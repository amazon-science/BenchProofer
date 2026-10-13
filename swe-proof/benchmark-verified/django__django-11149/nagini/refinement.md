# refinement.md — django__django-11149

The operation-by-operation correspondence between `model.py`'s implementation
(the four `inline_*_decision` impls and the shared `target_decision` helper /
`holds_any` deep model) and `patch.diff` (the gold patch). Each step is tagged
**R** (type refinement), **A-consumed** (proof uses an axiom's `Ensures`),
**A-reference** (a deep model validated == a real callee by axiom_check.py /
G-AX), or **I** (identical concrete operation). The claim: *any implementation
that verifies against this frozen spec, refined per the map below, is
behaviourally equal to the gold patch on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The shared helper — `_has_any_perms_for_target_model` (new method)

Gold hunk (new method):
```python
def _has_any_perms_for_target_model(self, request, perms):
    opts = self.opts
    for field in opts.fields:
        if field.remote_field and field.remote_field.model != self.parent_model:
            opts = field.remote_field.model._meta
            break
    return any(
        request.user.has_perm('%s.%s' % (opts.app_label, get_permission_codename(perm, opts)))
        for perm in perms
    )
```

| # | model.py impl op (`target_decision` / `holds_any`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `held: PSet[int]` | the actor's permission grant queried by `request.user.has_perm` | R | each held permission string ↔ a distinct int code; `has_perm(p)` TRUE ↔ `code(p) in held` (mapping.md §2). Read-only ⇒ `Acc(set_pred(held), 1/2)` required AND ensured (directive 5). |
| A2 | parameter `required: PSeq[int]` | the `perms` list + the codename string built from each entry via `get_permission_codename` for the located target model | R | the locating loop over `opts.fields` (unchanged, moved verbatim into the helper) fixes the target model; each requested action ↔ its distinct code; `['change']` ↔ `PSeq(modify_code)`, `['view','change']` ↔ `PSeq(inspect_code, modify_code)` (mapping.md §2, §3). |
| A3 | `holds_any(held, required) == Exists j: 0<=j<len(required) and required[j] in held`; the impl loop returns True on the first held required code, else False | `any(request.user.has_perm('%s.%s' % (opts.app_label, get_permission_codename(perm, opts))) for perm in perms)` | R (deep model) + I | `any` over the requested list ↔ the existential of per-code membership. `has_perm`/`get_permission_codename` are unchanged callees refined to membership / distinct codes (mapping.md §3); the short-circuit loop is the identical control flow of `any`. No callee is axiomatized — the operation is modeled deeply, so this is a deep-model refinement, not a consumed axiom. |

## B. The four decisions — `has_add/change/delete/view_permission`

Gold hunks (auto_created branch of each):
```python
has_add_permission   : return self._has_any_perms_for_target_model(request, ['change'])
has_change_permission: return self._has_any_perms_for_target_model(request, ['change'])
has_delete_permission: return self._has_any_perms_for_target_model(request, ['change'])
has_view_permission  : return self._has_any_perms_for_target_model(request, ['view', 'change'])
```

| # | model.py construct | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | `inline_create_decision`: `target_decision(held, PSeq(modify_code))`; post `Result() == (modify_code in held)` | `has_add_permission` → `_has_any_perms_for_target_model(request, ['change'])` | R + I | `['change']` ↔ `PSeq(modify_code)` (A2); the helper's spec (A3) gives `Result() == (modify_code in held)`. Caller uses the helper's spec, not an axiom (multi-site rule). |
| B2 | `inline_modify_decision`: `target_decision(held, PSeq(modify_code))`; post `Result() == (modify_code in held)` | `has_change_permission` → `_has_any_perms_for_target_model(request, ['change'])` | R + I | identical to B1 for the change decision. |
| B3 | `inline_remove_decision`: `target_decision(held, PSeq(modify_code))`; post `Result() == (modify_code in held)` | `has_delete_permission` → `_has_any_perms_for_target_model(request, ['change'])` | R + I | identical to B1 for the delete decision. |
| B4 | `inline_inspect_decision`: `target_decision(held, PSeq(inspect_code, modify_code))`; post `Result() == ((inspect_code in held) or (modify_code in held))` | `has_view_permission` → `_has_any_perms_for_target_model(request, ['view', 'change'])` | R + I | `['view','change']` ↔ `PSeq(inspect_code, modify_code)`; the helper's spec (A3, `Exists` over the two codes) is provably the OR of the two memberships, which is the unchanged view rule. |

The discriminating content of the change — create/modify/remove must require the
**MODIFY** code, not the view rule {inspect, modify} — lives in steps B1–B3
(`required = PSeq(modify_code)`, post `Result() == (modify_code in held)`). The
pre-patch code returned `has_view_permission(...)` for all three, i.e.
`required = PSeq(inspect_code, modify_code)`; `model_prepatch.py` (and the
per-behaviour `model_prepatch_{create,modify,remove}.py`) reproduce that and
**fail** the postcondition `Result() == (modify_code in held)` — exactly the
spec sensing the change (G-DIFF). An actor holding only `inspect_code` (the
view-only permission of the F2P tests) then makes the helper return True under
the buggy rule but the spec demands False.

## C. No kind-3 (unexpressible-changed-op) steps; no consumed axiom

Every step above is R or I. The changed operation — *which set of required
permission codes each decision queries on the target model* — is modeled
**deeply**: the requested-code lists are explicit (`PSeq(modify_code)` vs
`PSeq(inspect_code, modify_code)`) and the "holds any" computation is the
spelled-out existential `holds_any` / short-circuit loop in `target_decision`.
The unchanged callees the helper invokes (`request.user.has_perm`,
`get_permission_codename`, the builtin `any`) are **R-refinements** to set
membership / distinct int codes / the existential — not axioms the proof
consumes. There is therefore **no `@ContractOnly` axiom** and no A-consumed /
A-reference row; `axiom_check.py` exists only to validate the two refinement
facts (codename distinctness; `any` == existential-membership) as an in-container
sanity oracle.

## D. verify(model) ⇒ resolved

`inline_create/modify/remove_decision` verify only if each returns
`modify_code in held` (B1–B3), i.e. only if create/modify/remove require the
MODIFY code and an inspect-only actor is denied; `inline_inspect_decision`
verifies only if it returns the {inspect, modify} OR (B4), the unchanged and
correct view rule. By R (held permissions ↔ `PSet[int]` membership; codename
strings ↔ distinct codes; `any` ↔ existential) the verified decisions equal the
gold helper-based decisions on the tested inputs: with only the target's `view`
permission, view = True and add/change/delete = False; with the `change`
permission, all four = True — exactly what the F2P tests
`test_inline_add_m2m_view_only_perm`, `test_inline_change_m2m_view_only_perm`
(and the strengthened `test_inline_change_m2m_change_perm`) assert. Therefore a
model satisfying this spec, refined by the map above, is the gold patch up to
type refinement, and the gold patch resolves (G-RESOLVE). The only trust point
is refinement fidelity (this document, G-EQ); there is no axiom-soundness trust
point because no axiom is consumed.

**Termination obligation.** Nagini's default judgement is partial correctness,
so a value-only spec would be discharged vacuously by an implementation that
never returns (e.g. a scan whose index does not advance, or one that re-enters
itself on the miss path) — and such an implementation, refined faithfully,
hangs the test suite instead of resolving. Every modeled function therefore
also `Requires(MustTerminate(...))`: the four decision wrappers carry measure 3
and the shared membership scan measure 2 (strictly smaller, so the delegation
is permitted), and the scan's loop consumes the obligation with the strictly
decreasing, bounded-below measure `len(required) - i`. With these obligations a
verified model both returns the correct decision AND returns at all, closing
the termination dimension of verify ⇒ resolved.
