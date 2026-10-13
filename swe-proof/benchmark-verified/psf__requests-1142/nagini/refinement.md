# refinement.md — psf__requests-1142

The operation-by-operation correspondence between `model.py`'s implementation
(the `prepare_content_length` impl region) and `patch.diff` (the gold patch).
Each step is tagged **R** (type refinement), **A** (axiomatized callee — split
into **A-consumed** / **A-reference**), or **I** (identical concrete operation).
The claim: *any implementation that verifies against this frozen spec, refined
per the map below, is behaviourally equal to the gold patch on the tested
inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## The change — `prepare_content_length` (`requests/models.py:388`)

Gold hunk:
```
 def prepare_content_length(self, body):
-    self.headers['Content-Length'] = '0'
     if hasattr(body, 'seek') and hasattr(body, 'tell'):
         body.seek(0, 2)
         self.headers['Content-Length'] = str(body.tell())
         body.seek(0, 0)
     elif body is not None:
         self.headers['Content-Length'] = str(len(body))
+    elif self.method not in ('GET', 'HEAD'):
+        self.headers['Content-Length'] = '0'
```

The fix removes the unconditional leading `Content-Length = '0'` and adds a
final `elif` so that the zero size is announced only for payload-carrying
methods. The bodyless `GET`/`HEAD` case now announces no size header.

| # | model.py impl op (`prepare_content_length`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| 1 | param `headers: Dict[int,int]`, mutated in place at full permission | `self.headers` (`CaseInsensitiveDict`) | R | header NAME ↔ int key token; presence + per-key value preserved (mapping.md §2). |
| 2 | `if seekable:` | `if hasattr(body,'seek') and hasattr(body,'tell'):` | R | the seekable-stream guard is lifted to the boolean `seekable` (mapping.md §2). |
| 3 | `headers[size_header()] = stream_len` | `body.seek(0,2); self.headers['Content-Length']=str(body.tell()); body.seek(0,0)` | R | `size_header()` ↔ `'Content-Length'`; the int `stream_len` ↔ `str(body.tell())` (injective formatting, mapping.md §2); the seek round-trip is the identity for this operation. |
| 4 | `elif body_present:` | `elif body is not None:` | R | the non-None-body guard is lifted to `body_present`. |
| 5 | `headers[size_header()] = body_len` | `self.headers['Content-Length'] = str(len(body))` | R | int `body_len` ↔ `str(len(body))` (mapping.md §2). |
| 6 | `elif method != method_get() and method != method_head():` | `elif self.method not in ('GET','HEAD'):` | R | `not in ('GET','HEAD')` over the verb ↔ the two token disequalities; `'GET'`↔`method_get()`, `'HEAD'`↔`method_head()` (mapping.md §2). This is the added branch. |
| 7 | `headers[size_header()] = 0` | `self.headers['Content-Length'] = '0'` | R | int `0` ↔ the string `'0'` (mapping.md §2). |
| 8 | (no leading unconditional write) | (removed line `self.headers['Content-Length'] = '0'`) | I | the deletion is reflected by the *absence* of any pre-branch write in the impl skeleton — the model's control flow has no unconditional announcement, exactly mirroring the post-patch body. `model_prepatch.py` restores that leading write and FAILS the discriminating postcondition (G-DIFF). |

In addition to the branch clauses, the postcondition carries a whole-map FRAME
(clause 4): for every key other than `size_header()`, membership and value are
unchanged (`Forall k != size_header(): (k in headers) == Old(k in headers)`,
and equal values for surviving keys). This pins the fact that the real
`prepare_content_length` writes AT MOST the `'Content-Length'` entry of
`self.headers` — it never adds, removes, or rewrites any other header. Without
the frame the spec admitted an implementation that also smuggles an unrelated
header into the map (the G-PANEL-1 extra-key attack), whose faithful real patch
would add a spurious header to every prepared request — observably different
wire behaviour from the gold patch.

The discriminating content of the change — a bodyless `GET`/`HEAD` request must
carry NO body-size header, while any other bodyless method announces zero —
lives in clause (3) of the postcondition:
`Implies(not seekable and not body_present,
         (size_header() in headers) == (method != method_get() and method != method_head()))`.
The pre-patch unconditionally set the header; `model_prepatch.py` reproduces
that (`headers[size_header()] = 0` first, no method guard) and **fails** exactly
this clause — the spec sensing the change (G-DIFF).

## No kind-3 (unexpressible-changed-op) steps

Every step above is R or I. The operation that genuinely *changed* — the guarded
body-size announcement with the new method condition — is modeled **deeply**
(the three branches plus the method guard are concrete impl control flow), not
hidden behind an axiom. There is therefore NO consumed axiom and NO
A-reference: `axiom_check.py` carries a deep-model self-consistency oracle
(the decision table re-derived and matched against the gold behaviour), so G-AX
has a concrete stdlib-only check to run, but the proof depends on no callee
contract.

## verify(model) ⇒ resolved

`prepare_content_length` verifies only if, in the bodyless case, the size header
is present **iff** the method is payload-carrying (clause 3), and equals the
correct length in the stream / non-stream cases (clauses 1–2). By R (the type
refinements of §1–7: header name/value, method token, body observations) the
verified skeleton equals the post-patch `prepare_content_length` on the tested
inputs:
  * `test_no_content_length` (F2P): a bodyless `GET` and a bodyless `HEAD`
    (`not seekable and not body_present`, `method ∈ {GET,HEAD}`) ⇒ clause 3 ⇒
    `'Content-Length' not in headers` — the test's exact assertion.
  * `test_basic_building` (P2P): a present form body `'life=42'`
    (`body_present`) ⇒ clause 2 ⇒ the size header is announced with the body's
    length, and `pr.body == 'life=42'` is unaffected.
Therefore a model satisfying this spec, refined by the map above, is the gold
patch up to type refinement — and the gold patch resolves (G-RESOLVE). The only
trust point is refinement fidelity (this document, G-EQ); there is no axiom, so
the axiom-soundness trust point of PLAN §1.1 is vacuous here.
