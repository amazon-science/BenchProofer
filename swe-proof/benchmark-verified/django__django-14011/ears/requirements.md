# Requirements: Threaded live-test HTTP server must release database connections per request

## Introduction

Django's live-server test support (`django.test.LiveServerTestCase`, driven by
its live-server thread helper `LiveServerThread`) runs a real HTTP server in a
background thread so that a test client — or a browser — can make real requests
against the application under test. That server is `ThreadedWSGIServer`
(`django/core/servers/basehttp.py`), a `socketserver.ThreadingMixIn` subclass of
`WSGIServer` that dispatches **each incoming request to its own new thread**.

Because every request runs in a fresh thread, each request thread opens its own
database connections through `django.db.connections` (the `ConnectionHandler`
mapping a database alias to its connection object). Previously those per-request
connection threads were never told to release their database connections when
the request finished. Leftover open connections held by request threads mean
that at the end of the run, when the test framework tears down the test
database, the database can still be "in use" by those threads — a
non-deterministic teardown error ("database is being accessed by other users").
This is the resurfacing of a race that live-server support had earlier fixed for
the non-threaded server.

A second, related problem is that request threads must be able to *use* the
right database connections at all. For in-memory SQLite databases the test
database exists only inside a specific connection object and cannot be reopened
from another thread; the server thread must therefore be handed the parent
thread's connection objects and use those.

The change that resolves this is server-side: (a) let `ThreadedWSGIServer` be
given a set of database connections to use, (b) make each request thread adopt
those connections, and (c) make each request thread release all its database
connections once the request has been serviced. In addition, the `sqlite3`
database backend's declared set of tests that cannot run against an in-memory
database must continue to account for connection-closing behavior it cannot
exercise. The live-server harness that starts the server
(`LiveServerThread`/`LiveServerTestCase`) is the surrounding mechanism that
supplies the parent thread's connection objects to the server and marks them
shareable across threads for the duration of the run; this change relies on that
existing mechanism but does not itself alter it, and it must not regress any
existing live-server behavior.

## Requirement 1: The threaded test server can be handed a set of database connections to use

**User story:** As a test-infrastructure maintainer, I want to construct
`ThreadedWSGIServer` with an optional set of database connections supplied by the
thread that starts the server, so that request threads can be made to use those
exact connection objects instead of opening their own.

**Acceptance criteria**

1. The system SHALL allow `ThreadedWSGIServer` in
   `django/core/servers/basehttp.py` to be constructed with an optional
   keyword-only collection that maps each database alias to a connection object
   supplied by the parent thread.
2. WHEN `ThreadedWSGIServer` is constructed without such a collection (or with an
   empty/absent one), THEN the server SHALL behave exactly as before — it SHALL
   construct successfully and SHALL NOT override any request thread's database
   connections.
3. The system SHALL retain the supplied collection on the server instance so it
   is available to the code that services each request in a separate thread.
4. The system SHALL preserve every existing `ThreadedWSGIServer` /
   `WSGIServer` construction argument and behavior (address, request handler,
   `ipv6`, `allow_reuse_address`, daemon threads), accepting the new collection
   in addition to — not instead of — the existing arguments.

## Requirement 2: Each request thread adopts the supplied database connections

**User story:** As a developer testing a view that reads and writes the
database, I want the server's per-request thread to use the database connections
handed to the server, so that the view operates on the same (possibly in-memory)
test database as the test process.

**Acceptance criteria**

1. WHEN the threaded server begins servicing a request in its own new thread AND
   a set of connections was supplied to the server, THEN that thread SHALL
   install each supplied connection into the active `django.db.connections`
   registry under that connection's alias, so lookups by alias in that thread
   return the supplied connection object.
2. WHILE a set of connections was supplied, the request thread SHALL leave any
   alias that was not supplied untouched in its connection registry.
3. WHEN no set of connections was supplied to the server, THEN the request
   thread SHALL NOT replace any of its database connections and SHALL service
   the request as it did before.
4. WHEN the connections have been installed (or when there are none to install),
   THEN the thread SHALL proceed to service the HTTP request normally, producing
   the same response it otherwise would.

## Requirement 3: Each request thread releases its database connections when the request is done

**User story:** As a developer running a live-server test, I want each request
thread to close its database connections once the request has been serviced, so
that no request thread keeps a database connection open past the request and the
test database can be torn down cleanly at the end of the run.

**Acceptance criteria**

1. WHEN a request has been serviced and its per-request cleanup runs in the
   threaded server, THEN the server SHALL close every database connection held
   in that thread's `django.db.connections` registry before the request's normal
   cleanup (socket teardown) completes.
2. The system SHALL perform this connection-closing through a single overridable
   step so that the closing action can be observed or substituted by a subclass
   (for testability) without changing the request-cleanup control flow.
3. WHEN a database connection that was actually open is closed by this step,
   THEN that connection's underlying database link SHALL be torn down, such that
   afterwards the connection reports having no live underlying connection.
4. IF the underlying database backend's `close()` is a no-op for a given
   connection (as with an in-memory SQLite database), THEN this step SHALL still
   run without error and SHALL still perform the normal per-request cleanup.
5. The system SHALL still invoke the base server's normal per-request cleanup
   (socket shutdown/close) after closing the database connections, so request
   handling is otherwise unchanged.

## Requirement 4: The sqlite3 backend's in-memory skip set accounts for per-request connection closing

**User story:** As a maintainer of the `sqlite3` database backend, I want the
declared set of tests that cannot run against an in-memory database to include
the threaded server's per-request connection-closing check, so that this
behavior is not treated as exercisable under in-memory SQLite — where a
connection's `close()` is a no-op and the closing therefore cannot be observed.

**Acceptance criteria**

1. Because an in-memory SQLite connection's `close()` is a no-op, the `sqlite3`
   backend SHALL continue to declare, within its set of tests that cannot run
   against an in-memory database, that the threaded server's per-request
   connection-closing behavior is not exercised under an in-memory SQLite
   database.
2. WHEN the `sqlite3` backend reports the tests it skips for an in-memory
   database, THEN the newly declared per-request connection-closing entry SHALL
   appear grouped under the same "close() is a no-op for an in-memory database"
   explanation as the pre-existing connection-closing skip entry, and every
   previously declared skip SHALL be retained (additions only, no removal).

## Requirement 5: Existing live-server functionality is preserved (regression protection)

**User story:** As a maintainer, I want the live server to keep behaving exactly
as it did before, so that adding per-request connection management does not
change how requests are served or how views access the database.

**Acceptance criteria**

1. The system SHALL keep serving application views over the live server: a GET to
   a served view SHALL return that view's response, and a request to an
   unmapped path SHALL return an HTTP 404 status.
2. WHEN a view writes data to the database and a later request reads it back over
   the live server, THEN the read-back request SHALL observe the written data.
3. WHILE per-request connection closing is in effect, successive requests served
   by the live server SHALL each still be able to open and use their database
   connections normally, so that the per-request closing neither leaks nor
   exhausts database connections across requests and does not otherwise change
   any observable request-handling behavior from before the change.
