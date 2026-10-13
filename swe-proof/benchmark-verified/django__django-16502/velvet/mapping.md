# mapping.md — django__django-16502

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 246eb4836a6fb967880f838aa0d22ecfdca8b6f1`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and
gives the provenance of each modeled/deep-modeled construct.

Repo file under change: `django/core/servers/basehttp.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `responseBody (isHead) (chunks)` | the response-finishing step of `ServerHandler` — `django/core/servers/basehttp.py` (the `finish_response` override added by the patch at line 156; the bodyless branch consumes the application iterator and emits no body, the body-bearing branch defers to the base `wsgiref.handlers.BaseHandler.finish_response`) | the modeled changed function: the body actually written to the client |
| `prepareMeta (isHead) (isThreadingServer) (m)` | `ServerHandler.cleanup_headers` — `django/core/servers/basehttp.py:131` | the modeled changed function: how the finishing step adjusts the length declaration, the close marking, and the close commitment |
| `bodyFor` *(deep model)* | the body the finishing step emits | pure spec of `responseBody` |
| `adjustMeta` *(deep model)* | the descriptor after `cleanup_headers` runs | pure spec of `prepareMeta` |
| `ResponseMeta.hasLength` *(A-reference)* | whether `'Content-Length' in self.headers` holds **after** `super().cleanup_headers()` — the unchanged base `wsgiref.handlers.BaseHandler.cleanup_headers` / `set_content_length` (`Lib/wsgiref/handlers.py`) | free-input abstraction of the unchanged length-declaration callee; validated by axiom_check.py (G-AX) |
| `chunks` *(A-reference)* | the application's returned output iterable `self.result`, whose body-bearing emission is the unchanged base `BaseHandler.finish_response` write loop (`Lib/wsgiref/handlers.py`) | free-input abstraction of the unchanged body-emission callee; validated by axiom_check.py (G-AX) |

The pre-patch repo behaviour the change introduces guards against (refinement
audit only, not in the consumer spec view):
* `ServerHandler` had **no** `finish_response` override, so the base
  `BaseHandler.finish_response` wrote the application body unconditionally,
  including for a bodyless (HEAD) request — the issue's symptom
  (`Solution_prepatch.lean`, `responseBody`).
* `cleanup_headers` did not special-case a bodyless request: it never cleared a
  present length declaration, and the close marking was driven by
  `"Content-Length" not in self.headers` alone, without the bodyless guard
  (`Solution_prepatch_2.lean`, `prepareMeta`).

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-AX (§3) and G-CONF (§4) use to translate values between the
Lean value domain and the Python repo types. A wrong entry surfaces as spurious
G-CONF / G-AX disagreements (the falsifiability the plan §4 trust statement
refers to).

| repo reality | Lean carrier | bijection |
|---|---|---|
| `environ["REQUEST_METHOD"] == "HEAD"` | `isHead : Bool` | `True` ↔ `isHead = true`; any other method (GET, POST, …) ↔ `isHead = false`. The fix branches only on HEAD vs not-HEAD. |
| `isinstance(self.request_handler.server, socketserver.ThreadingMixIn)` | `isThreadingServer : Bool` | `True` ↔ `isThreadingServer = true` |
| `'Content-Length' in self.headers` (after `super().cleanup_headers()`) | `m.hasLength : Bool` (entry) / `out.hasLength` (exit) | present ↔ `true` |
| `self.headers.get("Connection") == "close"` | `m.terminate` (entry) / `out.terminate` (exit) | equals `"close"` ↔ `true`; the app may have set `Connection` before the step (entry value) |
| `self.request_handler.close_connection` | `m.willTerminate` (entry) / `out.willTerminate` (exit) | truthy ↔ `true` |
| the application output iterable `self.result` (a sequence of `bytes` chunks) | `chunks : List (List Char)` | chunk `bytes` ↔ `List Char` of its byte values; `b"".join(chunks)` ↔ `chunks.flatten`; the emitted body is observed as the bytes after the `\r\n\r\n` header/body separator |
| the body written to the client | `out : List Char` | byte-for-byte equality of the emitted body |

The body is carried as `List (List Char)` (a list of chunks) rather than a
single string because the only operation on it is order-preserving
concatenation (`flatten`) vs. total suppression; modeling per byte keeps the
bijection total and exact.

## 3. Callee provenance (A-reference — checked by G-AX / axiom_check.py)

There are **no consumed axioms**. The two unchanged base callees the changed
functions sit on top of are abstracted as **free inputs**; their relied-on
reference behaviour is validated against the real `wsgiref` base handler.

### 3.1 `chunks` body emission ↔ base `BaseHandler.finish_response` (A-reference)
**Callee:** `wsgiref.handlers.BaseHandler.finish_response` (`Lib/wsgiref/handlers.py`),
reached for a body-bearing request via `super().finish_response()`. Its write
loop (`for data in self.result: self.write(data)`) emits the application's
output chunks **in order, verbatim**, so the body for a body-bearing request is
`b"".join(self.result)` — exactly `bodyFor false chunks = chunks.flatten`. The
changed bodyless branch instead consumes `self.result` (`deque(self.result,
maxlen=0)`) and writes **no** body — `bodyFor true chunks = []`.

**G-AX check:** run a real `wsgiref.simple_server`-style base handler over a fake
WSGI app returning fuzzed chunk lists and assert the emitted body equals the
in-order concatenation (the A-reference), plus the bodyless emission is empty.

### 3.2 `hasLength` ↔ base `BaseHandler.cleanup_headers` / `set_content_length` (A-reference)
**Callee:** `wsgiref.handlers.BaseHandler.cleanup_headers` (`Lib/wsgiref/handlers.py`),
reached via `super().cleanup_headers()` at the top of the Django override. It
declares a `Content-Length` iff one is computable (`len(self.result) == 1`);
otherwise it leaves the header absent. The Django override reads only **whether**
a length declaration is now present (`'Content-Length' in self.headers`) — the
single Boolean `m.hasLength` the model abstracts.

**G-AX check:** drive the real base `cleanup_headers` with a single-chunk result
(length known) and with an unsized result (length unknown) and assert the
`Content-Length`-present Boolean matches the abstraction in both cases.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`16502`** so the
consumer-side verdict (§11.3) is reproducible. The R/I shadows it builds
transliterate `bodyFor` and `adjustMeta` to Python and differential-test them
against the patched `ServerHandler.finish_response` / `cleanup_headers` driven
exactly as the F2P test drives them (a real handler over a fake WSGI app, with
`REQUEST_METHOD` ∈ {GET, HEAD}). Both impl regions are pure R/I (no axiom value
flows into the computed output), so `conf_skip = false`.
