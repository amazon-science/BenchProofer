# refinement.md — django__django-11149

Operation-by-operation correspondence between `Solution.lean`'s impl regions
(the five methods `holdsAnyTargetPerm`, `addRelationAllowed`,
`changeRelationAllowed`, `deleteRelationAllowed`, `viewRelationAllowed`, plus the
pure `anyPerm` fold) and `patch.diff` (the gold patch). Each step is tagged
**R** (type refinement; state the bijection), **A-consumed** / **A-reference**
(none in this bundle), or **I** (identical concrete op). EVERY step is R or I.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the narrative is audited by **G-EQ**. Claim: any impl verifying against
this frozen spec, refined per the map below, is behaviourally equal to the gold
patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The shared probe — new helper `_has_any_perms_for_target_model`

Gold hunk (added method, decision line):
```
+        return any(
+            request.user.has_perm('%s.%s' % (opts.app_label, get_permission_codename(perm, opts)))
+            for perm in perms
+        )
```
(The preceding `opts = self.opts` + the `for field in opts.fields: … break`
target-model resolution is UNCHANGED logic relocated verbatim from the old
`has_view_permission`; it selects which model the per-codename test queries and
does not change the disjunctive decision — folded into `userHasPerm`, mapping.md
§3.)

| # | Solution.lean impl op (`holdsAnyTargetPerm` / `anyPerm`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | param `userHasPerm : Perm → Bool` | `request.user.has_perm('%s.%s' % (opts.app_label, get_permission_codename(perm, opts)))` as a function of `perm` on the resolved `opts` | R | the composite per-codename permission test ↔ a total `Perm → Bool` (mapping.md §2). Unchanged callee, abstracted as a free input (mapping.md §3). |
| A2 | param `perms : List Perm` | the `perms` argument (`['change']` or `['view','change']`) | R | codename-string list ↔ `List Perm` (mapping.md §2). |
| A3 | `result = anyPerm userHasPerm perms`, computed by the backward `while` fold | `any(userHasPerm(perm) for perm in perms)` | I | `anyPerm` IS the `any(... for perm in perms)` disjunction, modeled deeply; the fold ops (`userHasPerm p`, `||`, the loop) are concrete and transliterated by G-CONF. No axiom — the helper is the function under spec. |

## B. The four gates — `has_{add,change,delete,view}_permission`

Gold hunks (the auto-created branch of each gate):
```
 def has_add_permission(self, request, obj):
     if self.opts.auto_created:
-        return self.has_view_permission(request, obj)
+        return self._has_any_perms_for_target_model(request, ['change'])
     return super().has_add_permission(request)
```
(identically for `has_change_permission` and `has_delete_permission`); and
```
 def has_view_permission(self, request, obj=None):
     if self.opts.auto_created:
-        <inlined view-or-change probe>
+        return self._has_any_perms_for_target_model(request, ['view', 'change'])
     return super().has_view_permission(request)
```

| # | Solution.lean construct | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | `if autoCreated then … else pure superResult` (all four gates) | `if self.opts.auto_created: … ; return super().has_*_permission(...)` | R + I | `self.opts.auto_created ↔ autoCreated : Bool`; the non-auto branch returns the unchanged inherited decision `super().has_*` ↔ free input `superResult` (mapping.md §2/§3). |
| B2 | `addRelationAllowed` / `changeRelationAllowed` / `deleteRelationAllowed` auto branch `← holdsAnyTargetPerm userHasPerm [Perm.change]` | `return self._has_any_perms_for_target_model(request, ['change'])` | I | callee-under-spec: the gates call the modeled helper, whose `holdsAnyTargetPerm_correct` discharges the caller's proof (§3 multi-site). Requests exactly the CHANGE permission. |
| B3 | `viewRelationAllowed` auto branch `← holdsAnyTargetPerm userHasPerm [Perm.view, Perm.change]` | `return self._has_any_perms_for_target_model(request, ['view', 'change'])` | I | the VIEW gate requests VIEW-or-CHANGE (the decision the patch preserves for viewing). |

## C. The discriminating content — what the spec senses

The bug: pre-patch, `has_add/change/delete_permission` (auto-created branch) all
returned `has_view_permission`, i.e. the **VIEW-or-CHANGE** probe
(`anyPerm userHasPerm [view, change]`). A principal holding only the VIEW
permission therefore passed the add/change/delete gates and could edit the
inline. Post-patch they require the **CHANGE** permission alone
(`anyPerm userHasPerm [change]`).

The frozen spec pins the add/change/delete result to
`anyPerm userHasPerm [Perm.change]`. `Solution_prepatch.lean` reproduces the
pre-patch skeleton (those three gates delegate to the `[view, change]` probe) and
**fails** verification on exactly the clause
`x = anyPerm userHasPerm [Perm.view, Perm.change] ⊢ x = anyPerm userHasPerm
[Perm.change]` (G-DIFF, confirmed unsolved goal at `ensures_1` for each of the
three gates). The two states diverge precisely when `userHasPerm Perm.view = true`
and `userHasPerm Perm.change = false` — the view-only principal the F2P tests
exercise. The VIEW gate is unchanged and its prepatch clause verifies.

This is one independently-fixed behaviour observed at three call sites (add,
change, delete) sharing the identical corrected decision; a single
`Solution_prepatch.lean` carries all three failing gates plus the unchanged VIEW
gate, against the byte-identical frozen spec (G-DIFF requires `same_spec`).

**Termination semantics (spec-strengthening, audit repair).** The bundle uses
`loom.semantics.termination "total"` (`TotalCorrectness`), not `"partial"`. A
prior audit (G-PANEL-1) exhibited a same-spec counterexample under partial
correctness: an impl replacing the probe's fold with a non-terminating
`while true` loop verified vacuously, because partial correctness only
constrains terminating executions. The real repo helper always terminates (a
bounded `any(...)` over a finite list), so total correctness is the faithful
semantics: it demands the `decreasing i` measure on the fold loop (the counter
strictly decreases to 0) and rejects every non-terminating impl — a loop with
no `decreasing` annotation is an error under total semantics and its WP is
unprovable. The `decreasing` clause lives inside the impl region; the
`set_option`/`open` lines are part of the frozen spec view shared byte-identical
by both twins.

## D. No kind-3 (inexpressible-changed-op) steps

Every step is R or I. The operation that genuinely changed — which permission(s)
the auto-created branch demands — is modeled **deeply** (the `anyPerm` fold over
an explicit `[Perm.change]` vs `[Perm.view, Perm.change]` list, B2/B3), not
hidden behind an axiom about a function under change. There are **no consumed
axioms and no A-references**: the only callees (`has_perm`,
`get_permission_codename`, the field walk, `super().has_*`) are UNCHANGED by the
patch and are abstracted as free inputs with no relied-on property (mapping.md
§3), so nothing requires G-AX validation.

## E. verify(Solution) ⇒ resolved

Each gate verifies only if its result equals the exact modeled decision: the
add/change/delete gates `= (if autoCreated then anyPerm userHasPerm [Perm.change]
else superResult)` (B1/B2/A3) and the view gate `= (if autoCreated then anyPerm
userHasPerm [Perm.view, Perm.change] else superResult)` (B1/B3). By R (the bool /
`Perm → Bool` / list bijections, mapping.md §2) the verified gates equal the
gold-patched `has_*_permission` decisions on every input, and by G-CONF the R/I
transliteration of the fold + gates agrees with the patched `options.py` logic on
≥4·10⁵ checks (seed 11149, 0 disagreements). Therefore a model satisfying this
spec, refined by the map above, is the gold patch up to type refinement — and the
gold patch resolves (G-RESOLVE). The sole trust point is refinement fidelity
(this doc, G-EQ + G-CONF); there are no axioms (G-AX skips).
