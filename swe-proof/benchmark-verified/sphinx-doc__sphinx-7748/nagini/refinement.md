# refinement.md — sphinx-doc__sphinx-7748

The operation-by-operation correspondence between `model.py`'s implementation
(the `gather_signatures` impl region and the deep folds `run_len` / `collected`)
and `patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A-consumed** (proof uses an axiom's `Ensures`), **A-reference** (a deep model
validated == the real behaviour by axiom_check.py / G-AX, NOT consumed), or
**I** (identical concrete operation). The claim:

*any implementation that verifies against this frozen spec, refined per the map
below, gathers the same ordered set of candidate signatures as the gold patch on
the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies cleanly at `base_commit`
and is the real correctness oracle, G-RESOLVE).

## A. The gathering site — `_find_signature` + `format_signature`

Gold hunk (essence): the per-block loop changes from "look only at the first
line, record one signature, break" to "walk the lines, record EVERY accepted
signature up to and including the first non-continued (`\`-terminated) line,
then join them":

```
- match = py_ext_sig_re.match(doclines[0])      # only the first line
- ... result = args, retann ; break              # at most one signature
+ for j, line in enumerate(doclines):
+     if not line: break
+     if line.endswith('\\'): multiline = True; line = line.rstrip('\\').rstrip()
+     else: multiline = False
+     match = py_ext_sig_re.match(line)
+     ... if result is None: result = args, retann
+         else: self._signatures.append("(%s) -> %s" % (args, retann))
+     if multiline: continue
+     else: break
- return super().format_signature(**kwargs)
+ sig = super().format_signature(**kwargs)
+ return "\n".join([sig] + self._signatures) if self._signatures else sig
```

| # | model.py impl op (`gather_signatures`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameters `cont: List[int]`, `val: List[int]` | the docstring block `doclines: List[str]` and its per-line `multiline` flags / recorded `(args, retann)` | R | each accepted signature line ↔ a pair `(cont[k], val[k])`: `cont[k] != 0 ⇔ doclines[k].endswith('\\')`; `val[k]` is the opaque token of the line's parsed signature (mapping.md §2). |
| A2 | the result is `collected(ToSeq(cont), ToSeq(val))` — the per-line values from the top up to and including the first terminating line, computed by the forward loop with the telescoping invariant | the post-patch loop's recorded `[result] + self._signatures`, joined by `format_signature` | A-reference | the changed gathering operation is modeled **deeply**: `run_len` / `collected` (the spelled-out front-recursive folds) and the verified loop in `gather_signatures` ARE the gathering. There is no consumed gathering axiom — the proof depends on none. The deep model is validated **== the real algorithm** out-of-band: G-AX (axiom_check.py) reimplements the post-patch loop + join with the verbatim `py_ext_sig_re` and asserts the model's count/order equals the real collected signatures on exhaustive clean runs + 20000 fuzz + the F2P fixtures (mapping.md §3.1). |
| A3 | `if c == 0 or i == n - 1: break` (stop at the first non-continued line, or at end-of-block) | `if multiline: continue else: break`, plus the `for` loop exhausting `doclines` | I + R | a non-continued line stops the run exactly as the `else: break` does (`c == 0 ⇔ not multiline`, R); running out of lines stops the run exactly as the `for` exhausting `doclines` does (`i == n-1`, I — same control-flow termination). |
| A4 | `result = result + [v]` (append the line's value, ordered) | recording `result`/`self._signatures.append(...)` then `"\n".join([sig] + self._signatures)` | R | the ordered append ↔ the first-then-rest recording followed by the order-preserving join; the result list's order is the source order of the lines (mapping.md §2). |

The discriminating content of the change — gathering MORE THAN ONE signature
when leading lines are continued — lives in `collected` recursing on a continued
line (`cont[0] != 0 ⇒ PSeq(val[0]) + collected(drop 1)`) ⇔ the post-patch
`if multiline: continue`. The pre-patch consulted only `doclines[0]` and
recorded a single signature; `model_prepatch.py` reproduces that (`result =
[val[0]]`) and **fails** the postcondition `ToSeq(Result()) == collected(...)`
(and `len(Result()) == run_len(...)`) whenever the leading line is continued
(run length ≥ 2) — exactly the spec sensing the change (G-DIFF). The F2P
`class E` fixture is precisely this case: two `__init__` signature lines, the
first continued, so the gold renders both and the pre-patch renders only one.

## B. Secondary hunks — outside the modeled (F2P-tested) behaviour

The gold patch also contains two incidental hunks (mapping.md §4). They are not
part of the gathered-signature count/order that `gather_signatures` pins and the
F2P tests do not discriminate them:

| # | patch.diff op | tag | justification |
|---|---|---|---|
| B1 | `get_doc`: `lines = getattr(...); if lines is not None: return lines` → `if self._new_docstrings is not None: return self._new_docstrings` (with the new class attr `_new_docstrings = None`) | I | observationally identical: both return the cached docstrings when present and otherwise fall through to `super().get_doc`. A pure refactor; no behaviour change the spec must see. |
| B2 | `SingledispatchFunctionDocumenter.format_signature`: add `documenter.objpath = [None]` | guard outside domain | a defensive guard so the new `_find_signature` (which reads `self.objpath[-1]` up front) does not `IndexError` on a synthesised singledispatch documenter. The F2P tests do not exercise singledispatch; this is outside the modeled domain and changes no gathered-signature count/order. |

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R, I, or A-reference. The one operation that genuinely
*changed* — gathering all continued signatures instead of just the first — is
modeled **deeply** (the spelled-out folds `run_len` / `collected` consumed in
`gather_signatures`, step A2, an **A-reference**), not hidden behind an axiom
about the function under change. There is **no consumed axiom**: the gathering is
structural logic over the abstract per-line flags/values, and the unchanged
regex parser appears only inside G-AX's reimplemented real algorithm that the
deep model is validated against.

## D. verify(model) ⇒ resolved

`gather_signatures` verifies only if its output equals the exact collected run —
every line's value from the top up to and including the first terminating line
(A2), with the run length pinned to `run_len` so a continued leading line yields
≥ 2 signatures (the discriminating clause). By R (str-block ↔ parallel
`List[int]` streams; continuation marker ↔ `cont != 0`; recorded-and-joined
signatures ↔ ordered result list) the verified gatherer renders the same ordered
signature sequence as the post-patch `_find_signature` + `format_signature` on
the tested inputs; by G-AX the deep model `run_len` / `collected` equals the real
gathering (A-reference) over exhaustive + fuzz inputs and the F2P fixtures.
Therefore a model satisfying this spec, refined by the map above, is the gold
patch up to type refinement and the audited deep model — and the gold patch
resolves (G-RESOLVE). The trust points are exactly the two of PLAN §1.1: the
A-reference soundness (G-AX) and refinement fidelity (this document, G-EQ).
