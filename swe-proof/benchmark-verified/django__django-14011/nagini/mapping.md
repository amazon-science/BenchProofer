# mapping.md — django__django-14011

Binds every `model.py` symbol to its repository counterpart at
`base_commit = e4430f22c8e3d29ce5d9d0263fba57121938d06d`, states the type
abstraction, and gives the provenance of each axiom / A-reference callee (source
+ the exact behaviour the deep model or capability is validated against by G-AX /
axiom_check.py).

Repo file under change (production code): `django/core/servers/basehttp.py`
(the `ThreadedWSGIServer` class, line 80). A second hunk adds one test name to a
backend test-skip set in `django/db/backends/sqlite3/features.py` (line 84) —
test-infrastructure only, no behavioural content, not modeled.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `serve_request_on_worker(server, tokens, has_override, override_tokens)` | `ThreadedWSGIServer.process_request_thread(self, request, client_address)` — **added** by the patch, run on each worker thread — together with the configuration accepted by the **added** `__init__(*, connections_override=None)` | modeled changed behaviour: the worker can operate on the parent-supplied connection set only because the server was configured to accept it; install the available set into this thread's registry |
| `teardown_request(closed, tokens, request)` | `ThreadedWSGIServer.close_request(self, request)` — **added** by the patch | modeled changed behaviour (secondary, non-F2P): close all DB connections then release the request |
| `connections_handed_off(server)` | the control-flow fact "the server was configured (via `__init__(*, connections_override=...)`) so the parent-supplied connection set is available to its worker threads" | abstract, unforgeable per-server capability (the discriminating effect) |
| `accept_connection_set(server, has_override, override_tokens)` | the **added** `ThreadedWSGIServer.__init__(*, connections_override=None)` ACCEPTING the supplied set and storing `self.connections_override = connections_override` | the configuration step that grants the capability (A-consumed axiom) |
| `tokens[i]` (an `int`) | the identity of the connection object bound to `connections[alias]` (the per-thread registry `django.db.connections`) | per-alias bound-connection identity |
| `has_override[i]` / `override_tokens[i]` | `self.connections_override` (a `{alias: conn}` dict, stored by the added `__init__`) — was alias *i* supplied a connection, and which | the parent-thread connection set |
| `closed[i]` (a `bool`) | "is alias *i*'s connection closed?" — the live/closed state of `connections[alias]` | per-alias connection state |
| `Request.released` | the request resource being released by the inherited request-cleanup primitive (`request.close()`) | request-resource lifecycle flag |

The patch adds four members to `ThreadedWSGIServer`: `__init__` (accept+store the
parent-supplied set), `process_request_thread` (install the stored set into the
worker registry, then handle the request), `_close_connections` (calls
`connections.close_all()`), and `close_request` (close connections then delegate
to the inherited cleanup). The **tested** discriminator is `__init__` accepting
the set: with the hidden `test_patch` applied, the harness calls
`_create_server(..., connections_override=connections_override)`, and the
pre-patch constructor (which has no such parameter) raises `TypeError` in
`setUpClass`, erroring all 17 F2P tests before any request runs. `model.py`
pins this as the capability `connections_handed_off(server)` produced by
`accept_connection_set`.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `django.db.connections` — a per-thread registry mapping `alias` → connection object | two index-aligned `List`s over the registry's aliases: `tokens: List[int]`, `closed: List[bool]` | alias ↔ position `i`; `connections[alias]` identity ↔ `tokens[i]`; `connections[alias]` open ↔ `closed[i] == False` |
| `self.connections_override` (a `{alias: conn}` dict, possibly `None`/empty) | `has_override: List[bool]` (membership) + `override_tokens: List[int]` (the supplied identity) index-aligned with the registry | `alias in connections_override` ↔ `has_override[i]`; `connections_override[alias]` identity ↔ `override_tokens[i]` |
| `connections[alias] = conn` (install) | `tokens[i] = override_tokens[i]` | rebinding alias *i* to the supplied connection |
| "the server was configured to accept the parent-supplied set" (a control-flow fact, no value witness) | the abstract capability `connections_handed_off(server)` | configure-succeeds ↔ capability held; configure-impossible (pre-patch) ↔ capability unobtainable |
| `connections.close_all()` (`django/db/utils.py:207`) | the loop `for i: closed[i] = True` | closing every alias's connection ↔ setting every `closed[i]` to `True` |
| the socket `request` cleaned up by the inherited primitive | `Request` object with a `released: bool` flag | `request.close()` having run ↔ `request.released == True` |

No `str` indexing is used. The registry is modeled by parallel `List`s (not an
object-keyed dict) because the tested behaviour observes only WHICH aliases the
worker ends up bound to / closing, and a positional model keeps the per-element
permission accounting tractable in Nagini.

## 3. Axiom / capability provenance (checked by G-AX / axiom_check.py)

### 3.1 The configuration-acceptance capability (A-consumed: `accept_connection_set`)
**What it abstracts:** the added `ThreadedWSGIServer.__init__(self, *args,
connections_override=None, **kwargs)` which calls `super().__init__(*args,
**kwargs)` and stores `self.connections_override = connections_override`. The
underlying store is an unchanged Python operation; the patch adds the
`connections_override` parameter so the server CAN be configured with the
parent-supplied set. The capability `connections_handed_off(server)` certifies
that this configuration succeeded.

**Weakest contract:** `accept_connection_set` requires only fractional read
permission on the supplied-set lists and ensures `connections_handed_off(server)`
(plus length preservation, needed by the caller's loop). It says nothing about
HOW the set is stored — only that the configuration accepted it. This is the
weakest fact `serve_request_on_worker` needs to discharge its discriminating
postcondition.

**Soundness check (axiom_check.py R3, in-container):** the eval container is at
`base_commit` (unpatched). The script applies `patch.diff` into the Django source
tree, reloads `django.core.servers.basehttp`, and confirms the REAL fixed
`__init__` (a) has a `connections_override` parameter and (b) stores
`self.connections_override = connections_override`, and that the REAL
`process_request_thread` installs `connections[alias] = conn` from
`connections_override`. If the patch cannot be applied (unpatched, read-only), it
instead asserts the pre-patch branch: constructing `ThreadedWSGIServer(...,
connections_override=...)` raises `TypeError` — exactly the discriminator the
capability encodes. RC=0 confirmed in-container.

### 3.2 The inherited request-cleanup primitive (A-reference R1)
**Callee:** CPython `socketserver.TCPServer.close_request(self, request)` (and
the `shutdown_request` that calls it), invoked by `super().close_request(request)`
in the patched override. Source (CPython `Lib/socketserver.py`):

```python
def close_request(self, request):
    """Called to clean up an individual request."""
    request.close()
```

It releases the request resource ONLY and never touches the database-connection
registry. This is the pre-patch behaviour that left connections open. The deep
model encodes it as the single `request.released = True` write that follows the
`closed[i] = True` loop; `model_prepatch_2.py` drops the loop (inheriting only
this primitive) and fails the "every connection closed" postcondition.
axiom_check.py R1 drives the real CPython `TCPServer.close_request` on an
instrumented request + connection registry and asserts it releases the request
but closes none of the connections.

### 3.3 `connections.close_all` (A-reference R2)
**Callee:** Django `ConnectionHandler.close_all` (`django/db/utils.py:207`):

```python
def close_all(self):
    for alias in self:
        try:
            connection = getattr(self._connections, alias)
        except AttributeError:
            continue
        connection.close()
```

It closes EVERY connection currently bound in the registry. The deep model
encodes this as "every `closed[i]` becomes `True`". axiom_check.py R2 reproduces
`close_all`'s exact loop over an instrumented registry and asserts every
connection ends closed.

### 3.4 The inherited worker request handling (A-reference, refinement A4)
`process_request_thread`, after installing the available overrides, calls
`super().process_request_thread(request, client_address)` — CPython
`socketserver.ThreadingMixIn.process_request_thread`, which handles the request
and does not undo the installation. The model performs no registry operation
after the install loop, so the inherited handling is a registry no-op; G-AX
confirms the real method handles the request without altering the installed
registry.

## 4. G-CONF (conformance_check.py)

Differential gate: the contract-stripped impl regions of
`serve_request_on_worker` / `teardown_request` (shadow) against the real
patched `process_request_thread` / `close_request` driven over the real
per-thread `django.db.connections` registry, using the section-2 bridge
(aliases-as-positions, connection-object identity ↔ `tokens[i]`, closed
state ↔ `closed[i]`, request cleanup ↔ `released`). The @ContractOnly
callee `accept_connection_set` delegates to the REAL configuration
acceptance (constructing the patched server with the supplied set;
`bind_and_activate=False`, no network side effects). ≥1e5
Requires-satisfying inputs: exhaustive small-arity boundary cases + fuzz
over 0..8 aliases. **Pinned fuzz seed: 14011.**
