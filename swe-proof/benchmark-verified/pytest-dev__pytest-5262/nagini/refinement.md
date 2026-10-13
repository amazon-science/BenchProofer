# refinement.md — pytest-dev__pytest-5262

The operation-by-operation correspondence between `model.py`'s implementation
(the `reported_mode` impl region and the deep `without_marker` model) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A-consumed** (the proof uses an axiom's `Ensures`), **A-reference** (a deep
model is validated == the real callee by axiom_check.py / G-AX), or **I**
(identical concrete operation). The claim: *any implementation that verifies
against this frozen spec, refined per the map below, is behaviourally equal to
the gold patch on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The mode site — the new `EncodedFile.mode` property (`src/_pytest/capture.py:445`)

Gold hunk:
```
+    @property
+    def mode(self):
+        return self.buffer.mode.replace("b", "")
```

| # | model.py impl op (`reported_mode`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `buffer_mode: List[int]` | the implicit input `self.buffer.mode` (a `str`) | R | `str` ↔ `List[int]` of code points (mapping.md §2). The property's only input is the underlying buffer's mode string; modeled as the read-only parameter `buffer_mode` (`Acc(list_pred(buffer_mode), 1/2)`, required AND ensured). |
| A2 | the result is `without_marker(ToSeq(buffer_mode))`, the per-code-point deletion of the binary marker (`kept(c)` = empty when `c==98`, else `PSeq(c)`), computed by the backward loop | `self.buffer.mode.replace("b", "")` | A-reference | the changed string operation is modeled **deeply**: `without_marker` (the spelled-out front-recursive fold in the `pure` region) and the verified loop in `reported_mode` ARE the deletion. There is **no consumed axiom** for `str.replace`. The deep model is validated **== the real callee** out-of-band: G-AX (axiom_check.py) runs `s.replace("b","")` on boundary+fuzz and asserts `s.replace("b","") == without_marker(s)`. For a single-character search and an empty replacement, `str.replace` is exactly the per-code-point deletion (mapping.md §3); model loop and real callee compute the same function. |
| A3 | `result` returned (a `List[int]`) | the property's returned `str` | R | `str` ↔ `List[int]` (mapping.md §2); the F2P test observes the returned string's characters (`"b" not in sys.stdout.mode`), which the refinement preserves. |

The discriminating content of the change — the binary marker `"b"` (U+0062 = 98)
is **deleted** from the reported mode rather than left in place — lives in
`kept(98) == empty` (model) ⇔ the `.replace("b", "")` deletion (real). The
pre-patch state had no `mode` property, so the mode fell through `__getattr__`
to the buffer's binary mode **unchanged** (the identity); `model_prepatch.py`
reproduces that identity skeleton and **fails** the postcondition
`ToSeq(Result()) == without_marker(ToSeq(buffer_mode))` (and `marker_free`),
which is exactly the spec sensing the change (G-DIFF).

## B. No consumed axiom

There is no `@ContractOnly` in this bundle. The modeled function reads only the
buffer's mode string (its parameter) and deletes a character — both expressible
in Nagini. The one kind-A item is the **A-reference** above (A2): the deep model
`without_marker` validated `==` the real `str.replace("b","")` by G-AX. No proof
clause depends on an axiom's `Ensures`, so there is no A-consumed row and no dead
axiom.

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R or A-reference. The one operation that genuinely *changed*
— the deletion of the binary marker from the advertised mode — is modeled
**deeply** (the spelled-out per-code-point fold `without_marker`, consumed in
`reported_mode`, step A2, an **A-reference**), not hidden behind an axiom about
the function under change.

## D. verify(model) ⇒ resolved

`reported_mode` verifies only if its output equals the exact per-code-point
deletion of the binary marker (A2: `ToSeq(Result()) == without_marker(...)`) and
contains no binary marker (`marker_free`). By R (`str` ↔ `List[int]`) the verified
result equals `self.buffer.mode.replace("b", "")` on the buffer-mode strings the
tests exercise; by G-AX the deep model `without_marker` equals the real
`str.replace("b","")` (A-reference). Therefore a model satisfying this spec,
refined by the map above, is the gold patch up to type refinement — and the gold
patch resolves (G-RESOLVE): under FD capture `sys.stdout` is an `EncodedFile`
whose buffer mode is `"rb+"`; the new property reports `"r+"`, so the F2P
`test_capfd_sys_stdout_mode` (`assert "b" not in sys.stdout.mode`) passes. The
single trust point is axiom soundness of the A-reference (G-AX); there is no
consumed axiom and no refinement step outside R/A-reference (G-EQ).
