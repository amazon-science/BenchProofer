# refinement.md — operation correspondence (django__django-11964)

Maps every op in `implementation_memberStr` to its `patch.diff` counterpart.
Tags: **R** type refinement · **A-consumed** proof uses axiom property ·
**A-reference** deep model validated == real callee (G-AX) · **I** identical op.

The post-patch Python is `def __str__(self): return str(self.value)` on
`Choices`. The single op is the textual conversion of the member's underlying
value; we model it deeply as `pyStr` applied to the member's `value` field.

| # | Lean impl op | patch.diff counterpart | tag | justification |
|---|---|---|---|---|
| 1 | `m : EnumMember` (uses `m.value`) | `self` (the bound member); `self.value` | R | member ↔ `EnumMember` bijection (mapping.md); `.value` ↔ `MemberValue` |
| 2 | `pyStr m.value` | `str(self.value)` | A-reference | the changed conversion modeled deeply; `pyStr` validated == real `str(value)` on int/str values by G-AX. NOT axiomatized. |
| 3 | `return …` | `return …` | I | the method returns its computed string |

No A-consumed rows: the proof discharges `pyStr` directly; no UNCHANGED callee
property is assumed. No changed-inexpressible op.

The discriminating clause is row 2: the result must equal `pyStr m.value`
(`str(self.value)`), NOT the owner-qualified member identifier
(`m.qualifiedName`, the inherited `Enum.__str__`). The prepatch impl returns
`m.qualifiedName`, so its `correct_memberStr` cannot close against the frozen
`problem_spec_memberStr` (which pins `pyStr m.value`). That is the G-DIFF
signal — and it is precisely the failure the issue reports
(`'MyChoice.FIRST_CHOICE' != 'first'`).
