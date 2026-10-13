# refinement.md — django__django-13112

The operation-by-operation correspondence between `model.py`'s implementation
(the `normalize_reference` impl region plus the deep pure model `normalized` /
`normfold` / `keep_count` / `first_dot` / `lower_cp`) and `patch.diff` (the gold
patch). Each step is tagged **R** (type refinement — same operation, refined
carrier type), **A-consumed** (proof uses an axiom's `Ensures`), **A-reference**
(a deep model validated == the real callee by axiom_check.py / G-AX, NOT
consumed as an axiom), or **I** (identical concrete operation). The claim: any
implementation that verifies against this frozen spec, refined per the map
below, is behaviourally equal to the gold patch on the tested inputs, so it
resolves.

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## The change site — `ForeignObject.deconstruct` (`django/db/models/fields/related.py:582-589`)

Gold hunk (the branch taken when `self.remote_field.model` is a `str`):
```
- kwargs['to'] = self.remote_field.model.lower()
+ if '.' in self.remote_field.model:
+     app_label, model_name = self.remote_field.model.split('.')
+     kwargs['to'] = '%s.%s' % (app_label, model_name.lower())
+ else:
+     kwargs['to'] = self.remote_field.model.lower()
```

`model.py`'s `normalize_reference(text)` models exactly the value assigned to
`kwargs['to']` in this `str` branch: the normalized reference. Everything else
in `deconstruct` (the `kwargs` assembly, the swappable handling, the non-`str`
`label_lower` branch) is unchanged by the gold patch and is outside the modeled
behaviour.

| # | model.py impl op (`normalize_reference`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| 1 | parameter `text: List[int]` | `self.remote_field.model: str` (in the `isinstance(..., str)` branch) | R | `str` ↔ `List[int]` of Unicode code points (mapping.md §2). The `isinstance(..., str)` guard is the modeled-branch precondition; the non-`str` branch (`label_lower`) is unchanged and not modeled. |
| 2 | `keep_count(s)` — `first_dot(s) < len(s)` ? `first_dot(s)` : `0` | `'.' in self.remote_field.model` ? len of `app_label` : (no split) | R + I | `'.' in model` ↔ `first_dot(s) < len(s)` (membership of the dot code point 46); `app_label = model.split('.')[0]` is the prefix before the first dot, whose length is `first_dot(s)`. The integer/branch logic is identical (I) under the str↔List[int] refinement (R). |
| 3 | dot present: `result` = `s[:keep]` verbatim followed by `lower_cp` of every later code point (the verified backward loop; equivalently `normfold(s, first_dot(s))`) | `'%s.%s' % (app_label, model_name.lower())` | A-reference | the changed string operation is modeled **deeply**: `normfold` / `lower_cp` (spelled-out folds in the `pure` region) and the verified loop in `normalize_reference` ARE the transformation. There is no consumed `lower`/`split`/`format` axiom — the proof never depends on one. The deep model is validated **== the real transform** out-of-band by G-AX (`axiom_check.py` runs `str.split('.')` / `str.lower()` / `%`-format and asserts `normalized == gold_transform`). Note the dot at index `first_dot(s)` is reproduced because `lower_cp(46) == 46`; the `app_label` (indices `< first_dot`) is emitted verbatim; the `model_name` (indices `> first_dot`) is ASCII-lower-cased — exactly `'%s.%s' % (app_label, model_name.lower())`. |
| 4 | no dot: `result` = `lower_cp` of every code point (`normfold(s, 0)`) | `self.remote_field.model.lower()` | A-reference | bare-name lower-casing; the deep `normfold(s, 0)` == `str.lower()` on ASCII identifier text, checked by G-AX. |
| 5 | `result` returned (a `List[int]`) | the value assigned to `kwargs['to']` | R | `List[int]` ↔ `str` content; the F2P test observes the rendered reference string (the app registry resolves `kwargs['to']` against installed app labels, which are case-sensitive). |

The discriminating content of the change — the **application label keeps its
letter case** when the reference is qualified (`app_label.model_name`), rather
than the whole string being folded to lower case — lives in
`keep_count(s) == first_dot(s)` when a dot is present (model) ⇔ the new
`if '.' in ...: '%s.%s' % (app_label, model_name.lower())` branch (real). The
pre-patch code lowered the entire string (`model.lower()` for every shape);
`model_prepatch.py` reproduces that (`keep = 0`, loop lower-cases every code
point) and **fails** the postcondition `ToSeq(Result()) == normalized(ToSeq(text))`,
which is exactly the spec sensing the change (G-DIFF).

## No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The operation that genuinely *changed*
— folding only the model-name portion to lower case while preserving the
application label's case — is modeled **deeply** (the spelled-out folds
`normfold` / `lower_cp` and the verified backward loop, an **A-reference**),
not hidden behind an axiom about a function the patch changes. There is **no
consumed axiom**: `str.split`, `str.lower`, and `%`-formatting are unchanged
stdlib operations whose composition the gold patch performs and which the deep
model reproduces; G-AX validates that composition (`normalized ==
gold_transform`) on boundary + fuzz inputs.

## verify(model) ⇒ resolved

`normalize_reference` verifies only if its output equals `normalized(ToSeq(text))`
— the exact per-code-point transform with the application label preserved
(step 3) and a bare name fully lower-cased (step 4). By R (str ↔ List[int]) the
verified result equals the `str` value the gold patch assigns to `kwargs['to']`
on the tested references; by G-AX the deep model `normalized` equals the real
gold transformation (`str.split('.')` / `str.lower()` / `%`-format) over
boundary + 40000 fuzz inputs (A-reference). Therefore a model satisfying this
spec, refined by the map above, is the gold patch up to type refinement and the
G-AX-audited deep model — and the gold patch resolves (G-RESOLVE). The single
trust point is deep-model fidelity (this document + G-AX); there is no axiom to
trust.
