# refinement.md — django__django-14351

Maps every operation in `implementation_membershipGroupColumns` to its
`patch.diff` counterpart (the body of the added `In.get_group_by_cols`). Tags:
**R** type refinement · **A-consumed** proof uses an axiom's property ·
**A-reference** deep model validated == real callee by G-AX/G-CONF · **I**
identical concrete op.

| # | Lean op (`implementation_membershipGroupColumns`) | patch.diff op (`In.get_group_by_cols`) | tag |
|---|---|---|---|
| 1 | `let mut cols := lhsCols` | `cols = self.lhs.get_group_by_cols()` | R — `lhsCols : List Col` is the type-refinement of the lhs's column list (`Col := Nat` identity, mapping.md). I in structure. |
| 2 | `match rhs with \| none => return (cols, none)` | the `if hasattr(self.rhs, 'get_group_by_cols'):` guard failing (rhs is not a subquery) ⇒ `cols` returned unchanged | R — `Option RhsSubquery`; `none` ⟺ `not hasattr(rhs,'get_group_by_cols')`. The early return models the un-entered `if`. |
| 3 | `\| some q0 => let mut q := q0` | entering the `hasattr` branch with the subquery rhs | R — `some q` ⟺ rhs is a subquery. |
| 4 | `if !q.explicitlySelected then` | `if not getattr(self.rhs, 'has_select_fields', True):` | A-reference — `explicitlySelected` models `has_select_fields = bool(select or masks)` (query.py:243-245); `getattr(...,True)` default is irrelevant inside the `some` branch (rhs IS a Query). Validated by G-CONF. |
| 5 | `q := { q with selected := [], explicitlySelected := false }` | `self.rhs.clear_select_clause()` (query.py:1861 → `select=()`, masks cleared ⇒ `has_select_fields=False`) | A-reference — deep model of the real callee's state effect. G-CONF runs the REAL `clear_select_clause`. |
| 6 | `q := { q with selected := [q.identityColumn], explicitlySelected := true }` | `self.rhs.add_fields(['pk'])` (query.py:1893 → `set_select([pk])` ⇒ `select=[pk]`, `has_select_fields=True`) | A-reference — deep model of `add_fields(['pk'])`. G-CONF runs the REAL `add_fields`. |
| 7 | `cols := cols ++ q.groupKeys` | `cols.extend(self.rhs.get_group_by_cols())` | A-reference — `groupKeys` models the patch-INVARIANT result of `rhs.get_group_by_cols()` (returns `[self]` for a non-aggregate query, unchanged by the patch). G-CONF runs the REAL `get_group_by_cols`. I in structure (list append). |
| 8 | `return (cols, some q)` | `return cols` | R — the returned `cols` list embeds the (now-mutated) rhs; the Lean pair makes that mutated rhs state an explicit second component so the spec can pin it (frame discipline, §0.5). |

## No changed-inexpressible op
Every changed op is modeled deeply (ops 4–7). No op is axiomatized; there is no
consumed axiom (axiom_check.py is a skip stub). The only operation the patch
*adds* — normalizing an implicitly-selected nested rhs to its identity column
before it contributes its grouping columns — is op 5+6, spelled out concretely.

## Frame discipline (§0.5)
The collected `cols` list (`result.1`) is pinned to `lhsCols ++ q.groupKeys` in
every branch; the rhs state (`result.2`) is pinned to `some q`, `some
(normalizeRhs q)`, or `none` exactly. No output component is left unconstrained.
The discriminating clause is `result.2` for an implicitly-selected nested rhs:
the spec demands `some (normalizeRhs q)` (which flips `explicitlySelected` to
`true` and `selected` to `[identityColumn]`); the prepatch returns `some q`
unchanged, so it cannot satisfy the spec (G-DIFF / G-PANEL).

## G-CONF legs
All A-reference ops (4–7) are differential-tested in `conformance_check.py`
against the real patched `In.get_group_by_cols` over the faithful `Query`-state
collaborators. The R/structural ops (1–3, 8) are exercised in the same harness
(both observable outputs — `cols` and the rhs selection state — are compared).
`conf_skip = false`.
