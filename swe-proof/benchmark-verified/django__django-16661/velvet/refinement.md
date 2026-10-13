# refinement.md — django__django-16661

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`keptSegments` backward `while` fold, the deep decision model `keepSegment`, and
the per-segment expansion `keepMask`) and `patch.diff` (the gold patch). Each
step is tagged **R** (type refinement; state the bijection), **A-consumed**
(proof uses an axiom's `ensures`), **A-reference** (deep model validated == real
callee by G-AX), or **I** (identical concrete op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`); the
narrative is audited by **G-EQ**. Claim: any impl verifying against this frozen
spec, refined per the map below, is behaviourally equal to the gold patch on the
per-segment keep decision, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The changed site — the per-segment append guard in `lookup_allowed`

Gold hunk (`django/contrib/admin/options.py:461-471`):
```
-            # It is allowed to filter on values that would be found from local
-            # model anyways. For example, if you filter on employee__department__id,
-            # then the id value would be found already from employee__department_id.
             if not prev_field or (
                 prev_field.is_relation
-                and field not in prev_field.path_infos[-1].target_fields
+                and field not in model._meta.parents.values()
+                and field is not model._meta.auto_field
+                and (
+                    model._meta.auto_field is None
+                    or part not in getattr(prev_field, "to_fields", [])
+                )
             ):
                 relation_parts.append(part)
```

| # | Solution.lean impl op (`keptSegments`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `hops : List Hop` | the walked path `lookup.split(LOOKUP_SEP)` plus the per-iteration introspection state | R | each segment iteration ↔ one `Hop`; the 7 booleans are the UNCHANGED `_meta`/field facts read at that iteration (mapping.md §2). G-CONF bridges via the identity `bool↔Bool` map. |
| A2 | `h.isFirst` | `not prev_field` | R | first-segment flag; truthiness ↔ `true` (mapping.md §2). |
| A3 | `h.priorIsRelation` | `prev_field.is_relation` | R | UNCHANGED field introspection; read-only fact. |
| A4 | `!h.concreteParentLink` | `field not in model._meta.parents.values()` | I + R | the NEW guard clause; `concreteParentLink` ↔ membership in the concrete-parent link set. The boolean negation is the identical concrete op the patch adds. |
| A5 | `!h.redundantLocalValue` | `field is not model._meta.auto_field` | I + R | the NEW guard clause; identity test ↔ `redundantLocalValue` flag (spec-view name mechanism-free, mapping.md §2). |
| A6 | `(!h.hasRedundantLocalValue \|\| !h.priorAlreadyCovers)` | `(model._meta.auto_field is None or part not in getattr(prev_field, "to_fields", []))` | I + R | the NEW disjunctive guard clause; `auto_field is None` ↔ `!hasRedundantLocalValue`, `part not in to_fields` ↔ `!priorAlreadyCovers`. The boolean structure is the identical concrete op. |
| A7 | `keepSegment h := h.isFirst \|\| (h.priorIsRelation && A4 && A5 && A6)` | the whole `if not prev_field or (prev_field.is_relation and …)` guard | I | the deep model of the CHANGED decision: the Boolean combination is transliterated `or`↔`\|\|`, `and`↔`&&` exactly. This is the changed op, modeled DEEPLY (not axiomatized). |
| A8 | `result := keepSegment h :: result` over the backward `while i > 0` fold; `keepMask hops` is the front-recursive spec | `relation_parts.append(part)` guarded by A7, walked left-to-right over the path | I | the loop records the keep flag of each segment. The backward fold (prepend, decreasing `i`) computes the same per-segment stream `keepMask hops` as the forward append; G-CONF confirms order-faithfulness on ≥10⁵ paths. `relation_parts` is `keepMask`'s `filter (·=true)` projection (mapping.md §2). |
| A9 | `return result : List Bool` | `relation_parts` (the recorded subsequence) used downstream by `lookup_allowed`'s `len(relation_parts) <= 1` / `LOOKUP_SEP.join(...)` checks | R | the spec pins the full per-segment flag stream `keepMask hops` (strictly stronger than the projected list — it pins each segment's decision positionally), so no wrong per-segment rule satisfies it. The downstream `len`/join logic is UNCHANGED by the patch and is a faithful function of this stream. |

Discriminating content of the change — a FK-that-is-a-PK reached through a
relation (the F2P `test_lookup_allowed_foreign_primary` case
`restaurant__place__country`): such a `Hop` has `priorIsRelation = true`,
`concreteParentLink = false`, `redundantLocalValue = false`, and EITHER
`hasRedundantLocalValue = false` OR `priorAlreadyCovers = false`, so the patched
`keepSegment` records it. The PRE-patch rule recorded a segment only when
`field not in prev_field.path_infos[-1].target_fields`, i.e. `¬targetOfPrior`; on
this case `targetOfPrior = true` (the FK-PK targets the prior relation), so the
old rule DROPPED it — shortcutting `restaurant__place__country` to
`restaurant__country` and raising `DisallowedModelAdminLookup`. The prepatch
skeleton reproduces exactly `keep := isFirst || (priorIsRelation && !targetOfPrior)`
and **fails** `out = keepMask hops` (G-DIFF).

## B. No axioms (no consumed axiom, no A-reference)

Every field of `Hop` is a single boolean fact from UNCHANGED Django introspection
(`Field.is_relation`, `Options.parents`, `Options.auto_field`, `Field.to_fields`,
`PathInfo.target_fields`). The patch changes none of these facts — only the way
they are COMBINED. So they are read-only per-hop **R** inputs, not contracts the
proof consumes: there is no `axiom <callee>_prop` and no `axiom_check.py`
(G-AX skips, per gates.py `gate_ax`). The single changed thing — the combination
rule `keepSegment` — is modeled **deeply** (A7, an I op), never axiomatized.

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R or I. The one operation that genuinely *changed* — the
per-segment keep guard — is modeled deeply (the spelled-out Boolean
`keepSegment`, step A7), not hidden behind an axiom about the function under
change. There are no consumed axioms and no A-reference deep models.

## D. verify(Solution) ⇒ resolved

`keptSegments` verifies only if its output equals the exact per-segment expansion
`keepMask hops` (A8/A9), i.e. each segment's flag is `keepSegment h` — the patched
guard (A7) under the `bool↔Bool` refinement (A1-A6). By R the verified decision
stream equals the `relation_parts`-building behaviour of the patched
`lookup_allowed` loop on every walked path; by G-CONF the R/I transliteration of
`keepSegment` + the backward fold agrees with `patch.diff`'s append guard
(transcribed independently from the `+` lines) on all 128 single-`Hop`
configurations + ≥10⁵ fuzzed paths. Therefore a model satisfying this spec,
refined by the map above, is the gold patch up to type refinement — and the gold
patch resolves (G-RESOLVE). The sole trust point is refinement fidelity (this
doc, G-EQ + G-CONF); there are no axioms (G-AX has nothing to check).
