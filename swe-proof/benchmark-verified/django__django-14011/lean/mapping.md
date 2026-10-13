# mapping.md — symbol binding & type bijection (django__django-14011)

base_commit: `e4430f22c8e3d29ce5d9d0263fba57121938d06d`

## Modeled behaviors

The fix augments the threaded test HTTP server (`ThreadedWSGIServer`) with two
new, independently-observable value-level effects on the per-thread **database
connection registry** (`django.db.connections`, a `ConnectionHandler` that maps a
string alias → a connection object):

1. **Bind a provided set of connections into the active registry.**
   New `ThreadedWSGIServer.process_request_thread` installs each connection from a
   provided collection into the active per-thread registry (`connections[alias] =
   conn`), so the request-handling thread uses exactly those connections; any
   alias not provided is left untouched.
   - Python: `django/core/servers/basehttp.py`
     `ThreadedWSGIServer.process_request_thread` (added lines 22–28 of patch.diff,
     i.e. `for alias, conn in self.connections_override.items(): connections[alias] = conn`)
     @ base_commit class `ThreadedWSGIServer` (file lines 80–82, body added by patch).
   - `connections[alias] = conn` ⇒ `BaseConnectionHandler.__setitem__`
     (`django/utils/connection.py:66`) — a registry insert/replace keyed by alias.
   - Lean: `implementation_bindConnections` / `problem_spec_bindConnections` /
     `correct_bindConnections`.

2. **Close every connection in the registry after a request.**
   New `ThreadedWSGIServer.close_request` calls `_close_connections`, which calls
   `connections.close_all()`; `close_all` iterates the registry and calls
   `connection.close()` on each.
   - Python: `django/core/servers/basehttp.py` `_close_connections` /
     `close_request` (added lines 30–36 of patch.diff).
   - `connections.close_all()` ⇒ `ConnectionHandler.close_all`
     (`django/db/utils.py:207-213`): `for alias in self: getattr(...).close()`.
   - `connection.close()` ⇒ tears down the underlying DBAPI connection; observable
     post-state is `conn.connection is None` (asserted by the F2P test
     `test_closes_connections`).
   - Lean: `implementation_closeConnections` / `problem_spec_closeConnections` /
     `correct_closeConnections`.

The `__init__` override (stores the provided collection) carries no value-level
output behavior and is not separately modeled; it is plumbing for behavior 1.
The `super().process_request_thread(...)` / `super().close_request(...)` calls
(actual request handling / socket teardown) are side effects outside the
connection-registry value kernel and are abstracted away — the F2P tests observe
the registry state, which is exactly what the two triples pin.

## Type bijection (used by G-CONF and G-AX)

| Python | Lean |
|---|---|
| a database connection object | `structure Conn` with `alias : String`, `isOpen : Bool` |
| `conn.alias` (the registry key) | `Conn.alias` |
| `conn.connection is not None` (underlying DBAPI conn established) | `Conn.isOpen = true` |
| `conn.close()` (post-state `conn.connection is None`) | `closeConn c = { c with isOpen := false }` |
| the connection registry `connections` (alias → conn) | `List Conn`, keyed by `.alias` (unique aliases) |
| `connections[alias] = conn` (`__setitem__`) | `setConn reg c` (replace entry with same alias, else append) |
| `connections.all()` / iterating the registry | iterating the `List Conn` |
| `connections.close_all()` | mapping `closeConn` over the `List Conn` |
| a provided collection of connections (`connections_override.values()`) | `provided : List Conn` |

A real registry holds at most one connection per alias; the fuzzers and the
`correct_*` preconditions assume aliases are distinct (`List.Pairwise (·.alias ≠
·.alias)`), matching the dict-keyed reality.

## Callee provenance & flag deps

- `BaseConnectionHandler.__setitem__` (`django/utils/connection.py:66`) — unchanged
  by the patch; a plain keyed insert/replace. Modeled as the pure refinement
  `setConn` (no axiom).
- `ConnectionHandler.close_all` (`django/db/utils.py:207`) — unchanged; iterates
  and calls `.close()` on each connection. Modeled as `List.map closeConn` (no
  axiom).
- `connection.close()` — unchanged; its only observed effect in scope is moving a
  connection to the closed state (`conn.connection is None`). Modeled as the pure
  field update `closeConn` (no axiom). No flag dependency.

No consumed `_prop` axiom and no A-reference deep model needs G-AX validation:
every callee is modeled as a type-only refinement applied identically on both
sides (G-AX is a skip stub; the R/I legs are covered by G-CONF).

## G-CONF fuzz seed

Pinned seed: **14011** (see `conformance_check.py`, `meta.json verifier_pins`).
