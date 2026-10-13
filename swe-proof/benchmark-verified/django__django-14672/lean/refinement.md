# refinement.md — operation correspondence (django__django-14672)

Maps every op in `implementation_m2mIdentity` to its `patch.diff` counterpart.
Tags: **R** type refinement · **A-consumed** proof uses axiom property ·
**A-reference** deep model validated == real callee (G-AX) · **I** identical op.

The post-patch Python is
`return super().identity + (self.through, make_hashable(self.through_fields), self.db_constraint)`.
The single changed token is the field-name-sequence component: it was placed
into the key raw, and is now passed through the standard-library hashable
canonicaliser. We model that canonicaliser deeply as `canonTF` and build the key
left-to-right with an accumulator.

| # | Lean impl op | patch.diff counterpart | tag | justification |
|---|---|---|---|---|
| 1 | `let mut acc := base` | `super().identity` (inherited prefix) prepended by tuple `+` | I | unchanged inherited components carried verbatim; opaque `base` prefix |
| 2 | `acc := acc ++ [through]` | `self.through` appended to the key tuple | I | unchanged component read verbatim, same position |
| 3 | `acc := acc ++ [canonTF throughFields]` | `make_hashable(self.through_fields)` appended | A-reference | the changed slot: the field-name sequence canonicalised to hashable form; `canonTF` validated == `make_hashable` over the `through_fields` domain by G-AX. NOT axiomatized. |
| 4 | `acc := acc ++ [dbConstraint]` | `self.db_constraint` appended | I | unchanged component read verbatim, same position |
| 5 | `return acc` | `return (...)` | I | the assembled key tuple is returned |

No A-consumed rows: the proof discharges `canonTF` directly (it is a total
definition, not an assumed property); no UNCHANGED callee property is consumed.
No changed-inexpressible op.

The discriminating clause is row 3. The prepatch impl uses `rawTF`, which leaves
a present sequence in its ORIGINAL container — a list stays a list
(`HVal.hlist`) instead of being canonicalised to a tuple (`HVal.htuple`). On the
`.aslist` input the prepatch result therefore differs from
`canonTF throughFields`, so its `correct_m2mIdentity` cannot close against the
frozen `problem_spec_m2mIdentity`. That is the G-DIFF signal, and it is exactly
the observable the F2P tests pin: equal relations differing only in
list-vs-tuple `through_fields` must produce equal (hashable) identity keys.
