# mapping.md — django__django-16502

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 246eb4836a6fb967880f838aa0d22ecfdca8b6f1`, states the type
abstraction, and records the (stdlib) modeling assumptions the refinement
relies on.

Repo file under change: `django/core/servers/basehttp.py`. The changed class is
`ServerHandler(wsgiref.simple_server.ServerHandler)`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `prepare_response_headers(resp, head, keepalive)` | `ServerHandler.cleanup_headers` — `django/core/servers/basehttp.py:131` (changed hunk lines 131-144) | modeled changed method: the method-sensitive payload-size-header removal + close decision |
| `emit_response_body(result, head)` | `ServerHandler.finish_response` — `django/core/servers/basehttp.py` (new method added by the patch at lines 156+) | modeled changed method: the method-sensitive body emission |
| `Resp` (fields `has_size`, `conn_close`, `close_flag`) | the observable state touched by `cleanup_headers`: `self.headers` membership of `"Content-Length"` and `"Connection" == "close"`, and `self.request_handler.close_connection` | carrier for the three observable facts |
| `want_close(head, has_size_after, keepalive)` | the `if … / elif …` close decision inside `cleanup_headers` (lines 134-141 post-patch) | pure spec: the close predicate |

The pre-patch repo behaviour the change replaces (for the refinement audit,
not referenced from the consumer spec view): `cleanup_headers` (pre-#16502) had
no method-sensitive `Content-Length` removal and set `Connection: close`
whenever `"Content-Length" not in self.headers` regardless of method; there was
no `finish_response` override, so the base `wsgiref` `finish_response` always
wrote the application body.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `self.environ["REQUEST_METHOD"] == "HEAD"` (a `str` equality) | `head: bool` | `head == True` ⟺ `REQUEST_METHOD == "HEAD"`; `head == False` ⟺ any other method (the only F2P methods are `HEAD` and `GET`). The behaviour branches solely on this classification. |
| `"Content-Length" in self.headers` (Headers membership) | `resp.has_size: bool` | True ⟺ a `Content-Length` header is present. Entry value = the post-`super().cleanup_headers()` state. |
| `self.headers["Connection"] == "close"` | `resp.conn_close: bool` | True ⟺ the `Connection` header has been set to `close`. Entry value False (base step sets no `Connection`). |
| `self.request_handler.close_connection` | `resp.close_flag: bool` | True ⟺ the handler's connection-close flag is set. Entry value False. |
| `isinstance(self.request_handler.server, socketserver.ThreadingMixIn)` | `keepalive: bool` | `keepalive == True` ⟺ the server is a threading server able to keep a connection alive across requests; the close decision uses `not keepalive` exactly where the patch uses `not isinstance(..., ThreadingMixIn)`. |
| the application iterable `self.result` (bytes chunks) | `result: List[int]` of byte values | concatenation of the chunks' bytes; `len`/order carried by `PSeq[int]` via `ToSeq`. The emitted body is the bytes written via `self.write` (none for HEAD). |
| `self.headers["Connection"] = "close"` (a write) | `resp.conn_close = True` | setting the close header ⟺ setting the bool |
| dropping `Content-Length` for HEAD (`del self.headers["Content-Length"]`) | `resp.has_size = False` | removal of the header ⟺ clearing the presence bool (Nagini bans `del d[k]`; the presence bool carries header membership) |

`str` indexing and `del d[k]` are banned in Nagini, so request-method equality
is abstracted to a bool and header membership/removal is carried by bool fields.

## 3. Modeling assumptions (validated by axiom_check.py — stdlib `wsgiref`)

There is **no `@ContractOnly` axiom** and **no A-reference deep model standing
in for a real opaque callee**: every changed decision is the behaviour under
specification and is spelled out deeply in the impl regions. Consequently there
is no G-AX obligation against a *changed* callee. What the refinement relies on
instead is the behaviour of the **unchanged** `wsgiref` base handler the patch
builds on; `axiom_check.py` validates those assumptions against the real stdlib
`wsgiref.handlers` classes (the same module hierarchy the running handler
uses):

### 3.1 Base body emission writes the full application data
`wsgiref.handlers.BaseHandler.finish_response` iterates `self.result` and calls
`self.write(data)` for each chunk, then `finish_content`. So for a body-bearing
method the emitted body is exactly the application's data — which is why the
patch only needs to *bypass* this path for HEAD and keep it (`super().
finish_response()`) for every other method. Model: `emit_response_body(result,
head=False) == result`.
Source: CPython `Lib/wsgiref/handlers.py`, `BaseHandler.finish_response` /
`BaseHandler.write`. Docs: https://docs.python.org/3/library/wsgiref.html.

### 3.2 Why the patch must bypass `finish_content` for HEAD
`BaseHandler.finish_content` does `self.headers.setdefault('Content-Length',
"0")` when headers are unsent. If the HEAD path called it, a `Content-Length:
0` header would be (re)introduced — defeating the omission of the payload-size
header. So the HEAD path consumes the iterable, sends the headers directly if
unsent, and does NOT call `finish_content`. Model: `emit_response_body(result,
head=True)` is empty (no body written) — and the header model keeps
`has_size == False` for HEAD (no resurrected size header).
Source: CPython `Lib/wsgiref/handlers.py`, `BaseHandler.finish_content`.

### 3.3 The close decision is taken entirely in the changed method
`wsgiref`'s base `cleanup_headers` only sets `Content-Length` (via
`set_content_length`) and never sets `Connection`. So at entry to the changed
method the connection is not yet asked to close (`conn_close == False`,
`close_flag == False`), and the close decision is exactly `want_close`. Model:
the entry preconditions `conn_close == False`, `close_flag == False`.
Source: CPython `Lib/wsgiref/handlers.py`, `BaseHandler.cleanup_headers`.

**Soundness check (axiom_check.py):** drives the real `wsgiref.handlers`
`SimpleHandler` (stdlib only — no Django/repo import) with a known application
body, under both the HEAD-style and GET-style decisions the gold patch makes,
and asserts: (a) the base path writes the full body (3.1); (b) the base
`finish_content` would inject `Content-Length: 0` when headers are unsent (3.2,
the reason for the bypass); (c) the base `cleanup_headers` sets no `Connection`
(3.3); and (d) the modeled per-method decisions (`want_close`, the HEAD
size-drop, the empty HEAD body) reproduce the gold patch's branch outcomes on
the F2P scenarios (HEAD vs GET, with/without a payload-size header, threading
vs not). Exit 0 iff every assumption holds.
