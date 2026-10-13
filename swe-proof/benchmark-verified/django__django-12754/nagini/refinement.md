# refinement.md — django__django-12754

The operation-by-operation correspondence between `model.py`'s implementation
(the `removed_base_field_prereqs` impl region and the deep `selected` /
`qualifies` model) and `patch.diff` (the gold patch). Each step is tagged **R**
(type refinement), **A** (axiomatized callee — **A-consumed** where the proof
uses the axiom's `Ensures`, **A-reference** where a deep model is validated ==
the real callee by axiom_check.py / G-AX), or **I** (identical concrete
operation). The claim: *any implementation that verifies against this frozen
spec, refined per the map below, is behaviourally equal to the gold patch on the
tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The added per-base block — `generate_created_models` (`autodetector.py:566-575` post-patch)

Gold hunk (added inside the `for base in model_state.bases:` loop, right after
the existing `dependencies.append((base_app_label, base_name, None, True))`):
```
+ old_base_model_state = self.from_state.models.get((base_app_label, base_name))
+ new_base_model_state = self.to_state.models.get((base_app_label, base_name))
+ if old_base_model_state and new_base_model_state:
+     removed_base_fields = set(old_base_model_state.fields).difference(
+         new_base_model_state.fields,
+     ).intersection(model_state.fields)
+     for removed_base_field in removed_base_fields:
+         dependencies.append((base_app_label, base_name, removed_base_field, False))
```

| # | model.py impl op (`removed_base_field_prereqs`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | param `candidates: PSeq[int]` | `set(old_base_model_state.fields)` (keys of the prior parent dict) | R | field-name `str` keys ↔ `int` ids; a `dict`'s key set ↔ a `PSeq` of those names (mapping.md §2). The `if old_base_model_state and new_base_model_state:` guard is the precondition that both states exist; the modeled function is entered exactly in that case. |
| A2 | param `parent_after: PSet[int]` | `new_base_model_state.fields` (keys) | R | `name in new_base_model_state.fields` ↔ `name in parent_after` (mapping.md §2). |
| A3 | param `child: PSet[int]` | `model_state.fields` (keys) | R | `name in model_state.fields` ↔ `name in child` (mapping.md §2). |
| A4 | `Result()` equals `selected(candidates, parent_after, child)`, i.e. the candidates for which `qualifies` holds (`c ∉ parent_after and c ∈ child`), computed by the backward fold over `candidates` | `set(old...).difference(new...).intersection(model...)` | A-reference | the changed set operation is modeled **deeply**: `selected` (the spelled-out front-recursive filter in the `pure` region) and the verified loop in `removed_base_field_prereqs` ARE the difference-then-intersection. There is no consumed `set_diff_intersect` axiom — the proof never depends on one. The deep model is validated **== the real built-in set algebra** out-of-band: G-AX (axiom_check.py) runs `set(old).difference(new).intersection(model)` on boundary+fuzz and asserts its membership equals `selected`'s. For `n ∈ old`: `n ∈ difference(new).intersection(model)` ⇔ `n ∉ new ∧ n ∈ model` ⇔ `qualifies(n)` (mapping.md §3.1). |
| A5 | each emitted element `f` of `Result()` | one `dependencies.append((base_app_label, base_name, removed_base_field, False))` | R | the base app-label / base name are loop-fixed and the boolean slot is the constant `False` (a "removed field" dependency, `check_dependency` autodetector.py:399-405); the only varying content is `removed_base_field`, so the `List[int]` of emitted field ids captures the appended-dependency set exactly (mapping.md §2). |
| A6 | the `for c in candidates` walk with the per-element `if (not (c in parent_after)) and (c in child)` filter | the `for removed_base_field in removed_base_fields:` append loop over the computed set | I | identical control flow: iterate the qualifying names, emit one dependency each. (The model folds front-to-back via the backward loop; order is immaterial — mapping.md §2, dependencies consumed as a membership set.) |

The discriminating content of the change — that a withdrawn-and-re-declared
parent field becomes an ordering prerequisite of the child's creation — lives in
`selected` keeping exactly the `qualifies` candidates (model) ⇔ the
`difference(...).intersection(...)` set being non-empty and producing
`(base, base, field, False)` dependencies (real). The pre-patch loop body
emitted only the parent-existence dependency and **nothing** for withdrawn
fields; `model_prepatch.py` reproduces that (the loop emits no elements) and
**fails** the postcondition / loop invariant
`ToSeq(result) == selected(candidates, parent_after, child)` whenever a
qualifying field exists — exactly the spec sensing the change (G-DIFF).

## B. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The one operation that genuinely
*changed* — the set difference-then-intersection that selects withdrawn-and-
clashing parent fields — is modeled **deeply** (the spelled-out front-recursive
filter `selected` consumed in `removed_base_field_prereqs`, step A4, an
**A-reference**), not hidden behind an axiom about the function under change:
there is no consumed `@ContractOnly` axiom in this bundle. The set primitives it
is built from (`in`, `set()`, `.difference()`, `.intersection()`) are language
built-ins refined to `PSet[int]` membership, modeled deeply and validated by
G-AX as the A-reference (§A4), not consumed as axioms.

## C. verify(model) ⇒ resolved

`removed_base_field_prereqs` verifies only if its output equals the exact
qualifying-name subsequence (A4) — i.e. it emits a "removed field" prerequisite
for precisely the base fields that were withdrawn AND re-declared by the child,
and for no others. By R (str-keys ↔ int-ids, dict-key-set ↔ PSeq/PSet, the
loop-fixed tuple slots) the verified output equals the appended
`(base, base, field, False)` dependencies the gold block produces. By G-AX the
deep model `selected` equals the real `set(...).difference(...).intersection(...)`
(the A-reference). These dependencies make the child's `CreateModel` depend on
the parent-field `RemoveField` (`check_dependency`, autodetector.py:399-405), so
the autodetector emits `RemoveField` before `CreateModel` — the order the F2P
test `test_add_model_with_field_removed_from_base_model` asserts. Therefore a
model satisfying this spec, refined by the map above, is the gold patch up to
type refinement and the audited A-reference — and the gold patch resolves
(G-RESOLVE). The trust points are exactly the two of PLAN §1.1: A-reference
soundness (G-AX) and refinement fidelity (this document, G-EQ).
