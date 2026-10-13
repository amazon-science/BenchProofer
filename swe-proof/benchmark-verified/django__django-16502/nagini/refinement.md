# refinement.md — django__django-16502

The operation-by-operation correspondence between `model.py`'s implementation
(the `prepare_response_headers` and `emit_response_body` impl regions, plus the
pure `want_close`) and `patch.diff` (the gold patch). Each step is tagged
**R** (type refinement), **A** (axiomatized callee — **A-consumed** where the
proof uses an axiom's `Ensures`, **A-reference** where a deep model is validated
== a real callee by axiom_check.py / G-AX), or **I** (identical concrete
operation). The claim: *any implementation that verifies against this frozen
spec, refined per the map below, is behaviourally equal to the gold patch on the
tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

There are **no axioms** in this bundle (`# axioms-start/end` is empty) and **no
A-reference deep model standing in for a *changed* opaque callee**: every changed
decision is modeled deeply. The only callees involved are the **unchanged**
`wsgiref` base-handler methods the patch builds on (`super().cleanup_headers()`,
`super().finish_response()`, the base `finish_content`/`write`); their relevant
behaviour is recorded in mapping.md §3 and validated against the real stdlib by
axiom_check.py. They are tagged **R** below (a base-call whose effect is carried
by the model's entry/exit state), not A — the proof does not consume a contract
about them; their behaviour is a modeling assumption checked out-of-band.

## A. The header-preparation site — `cleanup_headers` (`django/core/servers/basehttp.py:131`)

Gold hunk:
```
 def cleanup_headers(self):
     super().cleanup_headers()
+    if (
+        self.environ["REQUEST_METHOD"] == "HEAD"
+        and "Content-Length" in self.headers
+    ):
+        del self.headers["Content-Length"]
     # … persistent-connection comment …
-    if "Content-Length" not in self.headers:
+    if (
+        self.environ["REQUEST_METHOD"] != "HEAD"
+        and "Content-Length" not in self.headers
+    ):
         self.headers["Connection"] = "close"
     elif not isinstance(self.request_handler.server, socketserver.ThreadingMixIn):
         self.headers["Connection"] = "close"
     if self.headers.get("Connection") == "close":
         self.request_handler.close_connection = True
```

| # | model.py impl op (`prepare_response_headers`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | entry `resp.has_size` (post-base state); `Requires(conn_close == False, close_flag == False)` | `super().cleanup_headers()` then read of `self.headers` / `self.request_handler.close_connection` | R | the base call only sets `Content-Length` and never sets `Connection`; its effect is the entry state of `resp` (mapping.md §3.3). Not an axiom — its behaviour is a modeling assumption checked by axiom_check.py. |
| A2 | `head: bool` | `self.environ["REQUEST_METHOD"] == "HEAD"` | R | `str` method equality ↔ bool classification (mapping.md §2); only HEAD vs body-bearing matters. |
| A3 | `if head and resp.has_size: resp.has_size = False` | `if REQUEST_METHOD == "HEAD" and "Content-Length" in self.headers: del self.headers["Content-Length"]` | R + I | identical control flow; header membership ↔ `has_size` bool, header removal ↔ clearing the bool (`del d[k]` is banned in Nagini, mapping.md §2). |
| A4 | `if (not head) and (not resp.has_size): resp.conn_close = True` | `if REQUEST_METHOD != "HEAD" and "Content-Length" not in self.headers: self.headers["Connection"] = "close"` | R + I | identical guard (`not head` ⟺ `!= "HEAD"`, `not has_size` ⟺ `"Content-Length" not in headers`); set-`Connection`-close ↔ `conn_close = True`. Note `has_size` here is the post-A3 value, matching the patch evaluating membership after the `del`. |
| A5 | `elif not keepalive: resp.conn_close = True` | `elif not isinstance(self.request_handler.server, socketserver.ThreadingMixIn): self.headers["Connection"] = "close"` | R + I | identical `elif`; `not keepalive` ⟺ `not isinstance(..., ThreadingMixIn)` (mapping.md §2). |
| A6 | `if resp.conn_close: resp.close_flag = True` | `if self.headers.get("Connection") == "close": self.request_handler.close_connection = True` | R + I | identical mirror; `Connection == "close"` ⟺ `conn_close`, the handler flag ↔ `close_flag`. |

The pure `want_close(head, has_size_after, keepalive)` is exactly the A4/A5
disjunction (`((not head) and (not has_size)) or (not keepalive)`); the
postcondition `resp.conn_close == want_close(...)` pins the close outcome, and
`Implies(head and keepalive, conn_close == False)` pins the discriminating new
behaviour: **a HEAD request is never closed merely for lacking a payload-size
header**. The pre-patch `cleanup_headers` closed it (no `!= "HEAD"` guard);
`model_prepatch.py` reproduces that (`if not has_size: conn_close = True`) and
**fails** `conn_close == want_close(...)` — the spec sensing the change (G-DIFF).
It also fails the `Implies(head, has_size == False)` clause (no size-drop).

## B. The body-emission site — new `finish_response` (`django/core/servers/basehttp.py:156+`)

Gold hunk:
```
+    def finish_response(self):
+        if self.environ["REQUEST_METHOD"] == "HEAD":
+            try:
+                deque(self.result, maxlen=0)  # Consume iterator.
+                if not self.headers_sent:
+                    self.send_headers()
+            finally:
+                self.close()
+        else:
+            super().finish_response()
```

| # | model.py impl op (`emit_response_body`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | `result: List[int]` at `Acc(list_pred(result), 1/2)` (read-only) | `self.result` (the application iterable) | R | bytes chunks ↔ `List[int]`; the body is consumed but not mutated, so fractional read-only permission (directive 5). |
| B2 | HEAD branch: loop over `result` writing nothing, return `out == []` | `deque(self.result, maxlen=0)` (consume, write nothing); body is empty | R + I | `deque(it, maxlen=0)` fully consumes the iterable while discarding every element — modeled as a consume loop that appends nothing. The emitted body is empty (`len(Result()) == 0`). |
| B3 | non-HEAD branch: copy `result` into `out`, return `out == result` | `super().finish_response()` which writes every chunk via `self.write` | R | the base `finish_response` writes the full application data (mapping.md §3.1, checked by axiom_check.py); modeled as the identity copy. |

The postconditions `Implies(head, len(Result()) == 0)` and
`Implies(not head, ToSeq(Result()) == ToSeq(result))` pin the body outcome. The
pre-patch had **no** `finish_response` override, so the base path always wrote
the body; `model_prepatch_2.py` reproduces that (always copy `result`) and
**fails** `Implies(head, ToSeq(Result()) == empty)` — the spec sensing the
change (G-DIFF). Two independently-fixed behaviours ⇒ two failing prepatches.

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R or I. The two operations that genuinely *changed* — the
method-sensitive size-header removal + close decision (site A) and the
method-sensitive body suppression (site B) — are modeled **deeply** (spelled out
in the impl regions and the pure `want_close`), not hidden behind an axiom about
a changed callee. There is **no consumed axiom** and **no A-reference deep model
of a changed callee**. The only callees are the unchanged `wsgiref` base methods
(tagged R), whose assumed behaviour mapping.md §3 records and axiom_check.py
validates against the real stdlib.

## D. verify(model) ⇒ resolved

`prepare_response_headers` verifies only if (a) a HEAD response carries no
payload-size header (`Implies(head, has_size == False)`), (b) the close decision
equals `want_close` — in particular a HEAD request keeping alive is never closed
(`Implies(head and keepalive, conn_close == False)`), and (c) the handler flag
mirrors it. `emit_response_body` verifies only if a HEAD response emits an empty
body and a body-bearing response emits exactly the application data. By R (the
`str`/Headers/iterable refinements and the unchanged-base-method assumptions of
mapping.md §3, validated by axiom_check.py) the verified model equals the gold
patch on the tested inputs: the F2P `test_no_body_returned_for_head_requests`
observes exactly (a)+(b)+(c)+body — GET returns the body, has `Content-Length`,
no `Connection: close`; HEAD returns no body, no `Content-Length`, no
`Connection: close`. Therefore a model satisfying this spec, refined by the map
above, is the gold patch up to type refinement — and the gold patch resolves
(G-RESOLVE). The single trust point is refinement fidelity (this document,
G-EQ) plus the stdlib-base modeling assumptions (axiom_check.py); there is no
axiom-soundness trust point because there is no axiom.
