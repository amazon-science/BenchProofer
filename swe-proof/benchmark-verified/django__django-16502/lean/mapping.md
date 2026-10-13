# mapping.md — django__django-16502

## Symbol binding (base_commit 246eb4836a6fb967880f838aa0d22ecfdca8b6f1)

| Lean symbol | Python symbol | location |
|---|---|---|
| `implementation_headerPolicy` / `problem_spec_headerPolicy` / `correct_headerPolicy` | `ServerHandler.cleanup_headers(self)` | `django/core/servers/basehttp.py:131-144 @ base_commit` (post-patch body) |
| `implementation_bodyEmission` / `problem_spec_bodyEmission` / `correct_bodyEmission` | `ServerHandler.finish_response(self)` (added method) | `django/core/servers/basehttp.py:156-171 @ post-patch` |
| `HeaderCtx.isHead` | `self.environ["REQUEST_METHOD"] == "HEAD"` | `basehttp.py` cleanup_headers |
| `HeaderCtx.contentLengthSet` | `"Content-Length" in self.headers` (after `super().cleanup_headers()`) | base `wsgiref.handlers.BaseHandler.cleanup_headers` may set it from a known body length |
| `HeaderCtx.isThreading` | `isinstance(self.request_handler.server, socketserver.ThreadingMixIn)` | `basehttp.py:139` |
| `HeaderCtx.appDisconnect` | `self.headers.get("Connection") == "close"` was already true on entry (WSGI app / upstream set the `Connection` response header) | `basehttp.py:143` |
| `HeaderResult.contentLengthPresent` | `"Content-Length" in self.headers` after the method returns | |
| `HeaderResult.connectionDisconnect` | final state of `self.headers["Connection"] == "close"` ⟺ `self.request_handler.close_connection` set | `basehttp.py:137-144`; the header value and the `close_connection` flag are set together and are equal on exit |
| `BodyResult.bodyEmitted` | whether the WSGI result iterator's bytes are written to the output stream as the response body | `finish_response` HEAD branch consumes the iterator with `deque(self.result, maxlen=0)` and never writes it; the non-HEAD branch defers to `super().finish_response()` which writes it |
| `BodyResult.headersSent` | `self.headers_sent` after the method returns | HEAD branch calls `self.send_headers()` if not yet sent; non-HEAD branch sends them inside `super().finish_response()` |
| (input) `bodyEmission.headersAlreadySent` | `self.headers_sent` on entry | `finish_response` HEAD branch: `if not self.headers_sent: self.send_headers()` |

## Type bijection (G-CONF / G-AX use this)

| Python | Lean | notes |
|---|---|---|
| `environ["REQUEST_METHOD"] == "HEAD"` | `isHead : Bool` | only the HEAD-vs-not distinction is observed |
| `"Content-Length" in self.headers` | `contentLengthSet`/`contentLengthPresent : Bool` | header-name membership ↔ Bool |
| `isinstance(server, ThreadingMixIn)` | `isThreading : Bool` | the development server is non-threading by default; the F2P test forces a threading server |
| `self.headers.get("Connection") == "close"` | `appDisconnect` (on entry) / `connectionDisconnect` (on exit) : Bool | the `Connection` response header carrying the non-reuse sentinel |
| `self.request_handler.close_connection` | tracked by `connectionDisconnect` | set `True` ⟺ the `Connection` header carries the sentinel; equal to it on exit |
| `self.headers_sent` | `headersAlreadySent` (entry) / `headersSent` (exit) : Bool | |
| WSGI result iterator written as body | `bodyEmitted : Bool` | observable: body bytes present (GET) vs absent (HEAD) |

## Callee provenance / flag deps

No UNCHANGED callee carries semantics the proof must assume:

- `super().cleanup_headers()` (base `wsgiref` handler) is what establishes
  whether a `Content-Length` header is present and any pre-existing `Connection`
  header. Its result is taken as the INPUT (`contentLengthSet`, `appDisconnect`)
  to `headerPolicy` — not modeled, not axiomatized.
- `super().finish_response()` (base handler) writes headers then body. Its
  observable effect is modeled deeply in the non-HEAD branch
  (`bodyEmitted = true`, `headersSent = true`) — not axiomatized.
- `deque(result, maxlen=0)` (iterator drain), `self.send_headers()`,
  `self.close()`, `self.headers_sent` are plumbing; their observable net effect
  (body not written, headers ensured sent) is modeled directly.

→ no `opaque`/`axiom` declarations; `axiom_check.py` is a skip stub.

No flag-dependent callees.

## G-CONF fuzz seed (pinned)

`seed = 16502` (used in `conformance_check.py`). Inputs fuzzed:

- `headerPolicy`: all 2^4 combinations of `(isHead, contentLengthSet,
  isThreading, appDisconnect)`, exhaustively, then random fill.
- `bodyEmission`: all 2^2 combinations of `(isHead, headersAlreadySent)`,
  exhaustively, then random fill.

Total ≥ 10^5 cases; zero disagreements required.
