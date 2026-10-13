# refinement.md — sphinx-doc__sphinx-9698

The operation-by-operation correspondence between `model.py`'s implementation
(the `get_member_index_text` impl region plus the deep `index_label` model) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A** (axiomatized callee — split into **A-consumed**, where the proof uses the
axiom's `Ensures`, and **A-reference**, where a deep model is validated == the
real operation by `axiom_check.py` / G-AX), or **I** (identical concrete
operation). The claim: *any implementation that verifies against this frozen
spec, refined per the map below, is behaviourally equal to the gold patch on the
tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The member-label site — `PyMethod.get_index_text` (`sphinx/domains/python.py:784`)

Gold hunk (the property branch only):
```
- return _('%s() (%s property)') % (methname, clsname)
+ return _('%s (%s property)') % (methname, clsname)
```

The patch removes the `()` from the property role's index-label template. The
other three role branches (classmethod / staticmethod / plain method) are
unchanged and keep their `()`.

| # | model.py impl op (`get_member_index_text` / `index_label`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | params `methname: List[int]`, `clsname: List[int]` | the `methname`, `clsname` `str` locals (from `name.rsplit('.', 1)`) consumed by the role branch | R | `str` ↔ `List[int]` code points (mapping.md §2). The split itself is upstream/unchanged; the model takes the already-split names. |
| A2 | `option: int` selector (0..3) | the `if 'classmethod'… elif 'property'… elif 'staticmethod'… else` dispatch over `self.options` | R | the four mutually-exclusive role branches collapse to one integer (mapping.md §1); the directive sets at most one option key. |
| A3 | the member-name copy loop (`result == methname`) | the first `%s` placeholder filled by `methname` | R + I | identity splice of the first name into the template; `str` ↔ `List[int]`. |
| A4 | the empty-call marker: `if is_callable_role(option): append 40, 41` | the literal `()` present in the three callable templates and ABSENT in the patched property template | I | the discriminating change. `is_callable_role(option) == (option != 2)`; the marker is emitted for exactly the callable roles. In the gold, this is the textual difference between `'%s() (…'` (callable) and `'%s (…'` (property). |
| A5 | `append 32, 40` (the `' ('` group opening) | the constant `' ('` between the two placeholders in every template | I | identical literal in all four templates (`PSeq(32, 40)`). |
| A6 | the class-name copy loop (`result += clsname`) | the second `%s` placeholder filled by `clsname` | R + I | identity splice of the second name; `str` ↔ `List[int]`. |
| A7 | the per-role suffix concatenation (`role_suffix(option)`) | the trailing ` <role word>)` of each template | I | the constant role-word + `')'` literal, identical to the template tail for that role (mapping.md §1). |
| A9 | `Requires(MustTerminate(2))` + the per-loop `Invariant(MustTerminate(len(...) - idx + 1))` measures | the real `get_index_text` is a straight-line template splice: it ALWAYS returns | R | total-correctness obligation. Nagini verifies partial correctness by default, so without this obligation a non-terminating implementation (an endless loop before a wrong return) satisfies every value postcondition vacuously while hanging the index build and the F2P test (the G-EQ audit exhibited exactly this: an infinite-loop impl verified under the old spec and hung the harness). The obligation is discharged by the two copy loops' strictly decreasing, bounded-below measures; the real operation trivially terminates, so this adds no strength beyond the real behavior. |
| A8 | the result is `index_label(ToSeq(methname), ToSeq(clsname), option)` | `_(template) % (methname, clsname)` | A-reference | the changed string operation is modelled **deeply**: `index_label` (the spelled-out concatenation in the `pure` region) and the verified loops/branches in `get_member_index_text` ARE the label. There is no consumed `format_label` axiom — the proof never depends on one. The deep model is validated **== the real label** out-of-band: G-AX (`axiom_check.py`) substitutes the post-patch templates (the real oracle, since `_()` is the identity with no catalogue and `%` is the in-order splice) and the real `PyMethod.get_index_text` on boundary+fuzz names, asserting `index_label == real label`. |

The `_()` gettext lookup is the identity on the untranslated template (no `.mo`
catalogue is loaded in the test/build environment; the F2P test compares the
literal English label) — an R-refinement (mapping.md §2), captured by the deep
model directly emitting the English template literals. The `%`-substitution with
two positional `%s` is sequence concatenation (R + I, steps A3/A6).

The discriminating content of the change — the property role label has **no**
`()` after the member name — lives in `is_callable_role(2) == False` (model) ⇔
the property template losing its `()` (real). `model_prepatch.py` reproduces the
pre-patch behaviour (it emits `()` for the property role too) and **fails** the
postcondition `ToSeq(Result()) == index_label(ToSeq(methname), ToSeq(clsname),
option)` (and the discriminator `is_callable_role(option) == (…take(2) ==
call_marker())`), which is exactly the spec sensing the change (G-DIFF).

## B. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The one operation that genuinely
*changed* — whether the empty-call marker `()` is emitted for the property role
— is modelled **deeply** (the `is_callable_role` branch in
`get_member_index_text`, step A4, validated as part of the A-reference A8), not
hidden behind an axiom about the function under change: there is **no consumed
`@ContractOnly` axiom** in this bundle. The only kind-A artefact is the
A-reference (the deep `index_label` model G-AX validates against the real label).

## C. verify(model) ⇒ resolved

`get_member_index_text` verifies only if it TERMINATES (A9: the MustTerminate
obligation closes the vacuous-satisfaction gap a partial-correctness verifier
would otherwise leave for diverging implementations) and its output equals the
exact per-role label assembly with `()` present iff the role is callable
(A4, A8) — i.e. the property role's label has no `()`. By R (str ↔ List[int]; `_()` identity; `%`
splice ↔ concatenation) the verified label equals
`_(template[option]) % (methname, clsname)` on the tested names; by G-AX the
deep model `index_label` equals the real label produced by the patched
`PyMethod.get_index_text` (A-reference). Therefore a model satisfying this spec,
refined by the map above, is the gold patch up to type refinement and the
audited A-reference — and the gold patch resolves (G-RESOLVE). The one trust
point is refinement fidelity (this document, G-EQ) together with the A-reference
soundness check (G-AX); there is no consumed-axiom trust point.
