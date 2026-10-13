# refinement.md — django__django-16502

Maps every op in `implementation_headerPolicy` / `implementation_bodyEmission`
to its `patch.diff` counterpart. Tags: **R** type refinement · **A-consumed**
proof uses callee axiom · **A-reference** deep model validated == real callee
(G-AX) · **I** identical op.

The fix has two independently-observable behaviors, modeled as two CLEVER
triples (callees-before-callers ordering is irrelevant here — the two methods do
not call each other).

## Behavior 1 — `implementation_headerPolicy` ↔ `ServerHandler.cleanup_headers`

Post-patch source (`basehttp.py:131-144`): after `super().cleanup_headers()`,
a metadata-only request drops the body-length header, and the non-reuse
connection signal is asserted for an ordinary request lacking a known body
length, OR a single-request (non-threading) server, OR an app-set non-reuse.

| # | Lean impl op | patch.diff / source counterpart | tag | justification |
|---|---|---|---|---|
| 1 | `c.contentLengthSet` / `c.appDisconnect` (initial reads) | the header dict state left by `super().cleanup_headers()`: `"Content-Length" in self.headers`, `self.headers.get("Connection")=="close"` | R | base-handler result taken as input; `str`-keyed header membership ↔ `Bool` (mapping.md). Not a callee axiom — it is the modeled INPUT. |
| 2 | `if c.isHead && clPresent then clPresent := false` | `if REQUEST_METHOD=="HEAD" and "Content-Length" in self.headers: del self.headers["Content-Length"]` (patch lines 16-20) | I | identical boolean condition + deletion of the length header |
| 3 | `if !c.isHead && !clPresent then disconnect := true` | `if REQUEST_METHOD!="HEAD" and "Content-Length" not in self.headers: self.headers["Connection"]="close"` (patch lines 24-29) | I | the **changed condition** — gated on `!isHead` post-patch; reproduced concretely |
| 4 | `else if !c.isThreading then disconnect := true` | `elif not isinstance(self.request_handler.server, socketserver.ThreadingMixIn): self.headers["Connection"]="close"` (basehttp.py:139-140) | I | identical |
| 5 | `return { contentLengthPresent := clPresent, connectionDisconnect := disconnect }` | final header dict: `"Content-Length" in headers` + (`Connection=="close"` ⟺ `close_connection=True`, set together at 143-144) | R | observable header state ↔ `HeaderResult` fields; the `close_connection` flag tracks `connectionDisconnect` (mapping.md) |

## Behavior 2 — `implementation_bodyEmission` ↔ `ServerHandler.finish_response`

Post-patch source (`basehttp.py:156-171`, the ADDED method): a metadata-only
request drains the WSGI result iterator without writing a body and ensures the
headers are sent; an ordinary request defers to the base writer (headers + body).

| # | Lean impl op | patch.diff / source counterpart | tag | justification |
|---|---|---|---|---|
| 6 | `if c.isHead then …` | `if self.environ["REQUEST_METHOD"]=="HEAD":` (patch line 37) | I | identical branch condition |
| 7 | `{ bodyEmitted := false, … }` (no body write) | `deque(self.result, maxlen=0)  # Consume iterator` — drains the result, never writes body bytes (patch line 39) | R | iterator drain ↔ "body bytes not written to stream" (`bodyEmitted=false`); the observable is body-absence (mapping.md) |
| 8 | `let mut sent := c.headersAlreadySent; if !sent then sent := true` | `if not self.headers_sent: self.send_headers()` (patch lines 45-46) | I | ensure-headers-sent: net effect `headers_sent=true` either way |
| 9 | `else return { bodyEmitted := true, headersSent := true }` | `else: super().finish_response()` (patch lines 49-50) — base writer emits headers then body | R | base writer's observable net effect: headers written then body written; not axiomatized |

## Tagging summary

Every op is **R** or **I** — no A-tagged content. Both behaviors are modeled
deeply over their observable booleans; no UNCHANGED callee's behavior is
abstracted behind an axiom (the base handler's header preparation and standard
writer are taken as modeled inputs / direct net effects, per mapping.md). Hence
`axioms` region is empty, `axiom_check.py` is a skip stub, and `conf_skip=false`
(G-CONF mechanically differential-tests both impls — see conformance_check.py,
240k cases, 0 disagreements).

No changed-inexpressible op.

## Prepatch variants (the real bugs)

Two independently-fixed behaviors → two prepatch files, each carrying the gold
proof body (which then fails to typecheck against the buggy impl — the G-DIFF
signal):

- **`Solution_prepatch.lean`** — the **headline issue**: pre-fix there was no
  `finish_response` override, so every response (including metadata-only ones)
  deferred to the base writer and emitted the body. Buggy
  `implementation_bodyEmission` always returns `bodyEmitted := true`. The
  discriminating clause `result.bodyEmitted = !c.isHead` of
  `problem_spec_bodyEmission` is violated for `isHead = true` (body returned for
  a HEAD request), so `correct_bodyEmission` cannot close. This is exactly the
  F2P `test_no_body_returned_for_head_requests` HEAD assertion
  (`body == b"\r\n"`).

- **`Solution_prepatch_2.lean`** — pre-fix `cleanup_headers` did not distinguish
  the metadata-only method: it never deleted the body-length header for HEAD and
  asserted the non-reuse signal whenever the length was unknown, regardless of
  method. Buggy `implementation_headerPolicy` keeps `clPresent := contentLengthSet`
  (no HEAD deletion) and gates `disconnect` on `!clPresent` (drops the `!isHead`
  guard). Both `problem_spec_headerPolicy` conjuncts are then violated: for
  `isHead && contentLengthSet` the spec demands `contentLengthPresent = false`
  (the F2P assertion that no `Content-Length:` line appears for HEAD), and the
  `connectionDisconnect` formula differs for HEAD inputs. So `correct_headerPolicy`
  cannot close.
