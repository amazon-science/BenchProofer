# refinement.md — operation correspondence (django__django-13346)

Maps every op in `implementation_inClauseSql` to its `patch.diff` counterpart.
Tags: **R** type refinement · **A-consumed** proof uses axiom property ·
**A-reference** deep model validated == real callee (G-AX) · **I** identical op.

The patched Python adds a membership-lookup RHS renderer registered on the key
transform. It (1) delegates to the base membership lookup to get the bare
placeholder fragment `(%s, …, %s)` and the bound params, then (2) on a backend
WITHOUT a native JSON column type, substitutes an `n`-tuple of the backend's
value-extraction template into that fragment via `rhs = rhs % func`. We model the
base placeholder and the substitution concretely and the per-vendor extraction
template deeply.

| # | Lean impl op | patch.diff counterpart | tag | justification |
|---|---|---|---|---|
| 1 | `vendor : Vendor` | `connection.vendor` + `connection.features.has_native_json_field` selecting a branch | R | the four modeled string-builder backends ↔ the vendor/native-flag dispatch (mapping.md); native-JSON-ness is `hasNativeJson` |
| 2 | `n : Nat` | `len(rhs_params)` (number of None-stripped `__in` values) | R | one value placeholder per element; `n ≥ 1` is the genuine precondition (empty list ⇒ `EmptyResultSet`, the renderer is never reached) |
| 3 | `let mut rhs := buildClause "%s".toList n` | `rhs, rhs_params = super().process_rhs(...)` building the base placeholder `'(' + ', '.join(['%s']*n) + ')'` | I | identical concrete op: the base membership lookup's bare placeholder is `(%s, …, %s)`, reproduced as `buildClause "%s" n` |
| 4 | `if !hasNativeJson vendor then` | `if not connection.features.has_native_json_field:` | I | identical guard: the native-JSON backend leaves the fragment bare, the others wrap |
| 5 | `rhs := buildClause (valueExtractor vendor) n` | `func = (<template>,)*len(rhs_params)` per vendor, then `rhs = rhs % func` | R+I | the **changed op**: `valueExtractor` is the per-vendor wrap template modeled deeply (sqlite/mysql `JSON_EXTRACT(%s, '$')`, mariadb `JSON_UNQUOTE(JSON_EXTRACT(%s, '$'))`). NOT axiomatized. The `rhs % func` single-pass substitution of the `n`-tuple is the identical-op rebuild `buildClause wrapper n` (the literal `%s` inside the template survives the one substitution pass — mapping.md) |
| 6 | `return rhs` | `return rhs, rhs_params` | I | the returned `rhs_params` is unchanged by the fix for every modeled vendor and is out of model scope (mapping.md frame discipline) |

No A-consumed rows: the proof discharges the concatenation directly; no UNCHANGED
callee property is assumed (axioms region empty, G-AX is a skip stub).
No A-reference rows: the only callees (the base placeholder build and the `%`
substitution) are reproduced concretely as I ops, not abstracted behind a model
that needs G-AX validation. No changed-inexpressible op WITHIN the modeled scope
(the Oracle JSON-serialization sub-behavior is out of scope, mapping.md).

The discriminating clause is rows 4–5: when `hasNativeJson vendor = false`
(sqlite / mysql / mariadb), each slot is the value-extraction wrapper, NOT the
bare `%s`. The prepatch impl keeps `buildClause "%s" n` for every vendor, so its
rendered clause is `(%s, …)` which differs from the frozen
`problem_spec_inClauseSql` (`buildClause (slotFor vendor) n` =
`buildClause (valueExtractor vendor) n` on those vendors) for all `n ≥ 1`. Hence
the prepatch `correct_inClauseSql` cannot close on the sqlite/mysql/mariadb cases
— the G-DIFF signal. (postgresql, native JSON, is unchanged: `slotFor = "%s"`.)
