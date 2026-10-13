# refinement.md — django__django-16661

Maps every operation in `implementation_lookupAllowed` (Solution.lean) to its
`patch.diff` / base-source counterpart. Tags: **R** type refinement, **I**
identical concrete op, **A-consumed** proof uses an axiom's property,
**A-reference** deep model validated == real callee by G-AX. Every step is R, A,
or I. No changed op is inexpressible.

The gold patch's only behavioral change is the `relation_parts.append(part)`
GUARD (lines 461–469). The rest of `lookup_allowed` is unchanged; the impl
models the whole loop + final decision so the changed guard is observable.

| # | impl op (Solution.lean) | patch.diff / base-source counterpart | tag |
|---|---|---|---|
| 1 | `if fkeyAllowed then return true` | lines 446–452: `related_fkey_lookups` loop early `return True` | R — the FK raw-id popup allowance abstracted to one boolean (mapping.md) |
| 2 | `for step in steps do` | line 457 `for part in lookup.split(LOOKUP_SEP):` | R — chain of components → `List PathStep`, per-component metadata pre-resolved |
| 3 | `lastPart := step.part` | binds `part` each iteration (used at line 496) | I — running last-component identity |
| 4 | `if !step.exists_ then stopped := true` | lines 458–462: `get_field` raises `FieldDoesNotExist` ⇒ `break` | R — resolution success as `exists_ : Bool`; `break` as `stopped` |
| 5 | `appendIt` when `prev = none` ⇒ `true` | line 466 `if not prev_field or (...)` — the `not prev_field` disjunct | I — `Option.none` models `prev_field is None` |
| 6 | `appendIt` when `some pr` ⇒ `pr && !inParents && !isAutoField && (!modelHasAutoField || !partInPrevToFields)` | lines 467–469 (POST-patch guard): `prev_field.is_relation and field not in parents.values() and field is not auto_field and (auto_field is None or part not in to_fields)` | **R** — each conjunct is one abstracted metadata boolean; `continuesLocal` transcribes the added conjunction verbatim. THIS is the fixed op. |
| 7 | `if appendIt then relationParts := relationParts ++ [step.part]` | line 471 `relation_parts.append(part)` | I — list append |
| 8 | `if !step.hasPathInfos then stopped := true` | lines 472–474 `if not getattr(field,"path_infos",None): break` | R — `path_infos` truthiness as `hasPathInfos`; `break` as `stopped` |
| 9 | `else prev := some step.isRelation` | lines 476–477 `prev_field = field; model = field.path_infos[-1].to_opts.model` | R — only `prev_field.is_relation` (read next iter) is retained; `model` reassignment is folded into the pre-resolved `PathStep`s |
| 10 | `if relationParts.length ≤ 1 then return true` | lines 479–481 `if len(relation_parts) <= 1: return True` | I |
| 11 | `return validLookups.contains relationParts \|\| validLookups.contains (relationParts ++ [lastPart])` | lines 494–497 `return not {SEP.join(relation_parts), SEP.join(relation_parts+[part])}.isdisjoint(valid_lookups)` | R — `not {A,B}.isdisjoint(V)` ≡ `A ∈ V ∨ B ∈ V`; SEP-joined strings ↔ component-id lists |

`valid_lookups` construction (lines 482–492, `date_hierarchy` ∪ `list_filter`
entries) is pre-resolved into the input `validLookups : List (List Nat)`
(mapping.md) — R.

## A-legs

None. There is no `opaque`/`axiom` callee. The changed guard is modeled deeply
(rows 6, `continuesLocal`); the field-metadata reads are abstracted into the
`PathStep` inputs, not axiomatized. `axiom_check.py` is a skip stub.

## Prepatch (G-DIFF)

`Solution_prepatch.lean` differs ONLY in row 6's `appendIt` for `some pr`:
`pr && !step.inTargetFields` — the pre-patch guard
`prev_field.is_relation and field not in prev_field.path_infos[-1].target_fields`.
The `pure` region (incl. `continuesLocal`, which `problem_spec` consumes via
`lookupDecision`) is byte-identical, so the spec is unchanged and the carried
gold proof body cannot close against the buggy impl. On the F2P chain
`restaurant__place__country` the prepatch drops `place` (its
`inTargetFields = true`) ⇒ `relationParts = [restaurant, country]` ⇒ `False`,
whereas the post-patch spec value is `True` (mapping.md). Confirmed by
construction spec-probe.

## G-CONF (R/I legs)

All non-A rows above are R or I ⇒ `conf_skip = false`. `conformance_check.py`
differential-tests the Python shadow of `implementation_lookupAllowed` against an
oracle transcribing the post-patch loop over the same abstracted metadata, ≥10⁵
fuzzed inputs + edge cases (seed 16661).
