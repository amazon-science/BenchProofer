# refinement.md — operation correspondence (django__django-16493)

Maps every op in `implementation_recordedStorage` to its `patch.diff`
counterpart. Tags: **R** type refinement · **A-consumed** proof uses axiom
property · **A-reference** deep model validated == real callee (G-AX) · **I**
identical op.

The patched Python computes the original storage reference first, then records it
in `kwargs` only when it differs (by identity) from `default_storage`:

```python
storage = getattr(self, "_storage_callable", self.storage)
if storage is not default_storage:
    kwargs["storage"] = storage
```

| # | Lean impl op | patch.diff counterpart | tag | justification |
|---|---|---|---|---|
| 1 | `originalCallable : Option Nat` | `getattr(self, "_storage_callable", …)` presence | R | callable-reference presence ↔ `Option`; object identity ↔ `Nat` (mapping.md) |
| 2 | `evaluatedStorage : Nat` | `self.storage` (evaluated instance) | R | object identity ↔ `Nat` |
| 3 | `defaultStorage : Nat` | `default_storage` | R | object identity ↔ `Nat` |
| 4 | `let storage := originalCallable.getD evaluatedStorage` | `storage = getattr(self, "_storage_callable", self.storage)` | R | the **moved op**: compute the original reference (callable if present, else the evaluated instance) BEFORE the comparison. This hoist is the fix. |
| 5 | `let mut result := none; if storage ≠ defaultStorage then result := some storage` | `if storage is not default_storage: kwargs["storage"] = storage` (else key absent) | R | the **changed op**: the `is not default_storage` identity test now runs against `storage` (the original reference) rather than the evaluated instance. `is not` ↔ `≠` on `Nat` identities; "key recorded" ↔ `some`, "key absent" ↔ `none`. NOT axiomatized. |
| 6 | `return result` | the resulting `kwargs.get("storage")` | I | the recorded reference / its absence is the modeled output; the rest of the returned tuple is unaffected (mapping.md scope note) |

No A-consumed rows: the proof discharges the decision (a `getD` + an `if` on
`Nat` equality) directly; no UNCHANGED callee property is assumed (axioms region
empty, G-AX is a skip stub).
No A-reference rows: the only callees touched (`getattr`-with-default and the
`is` identity test) are reproduced concretely (`Option.getD`, `Nat` equality) as
R ops, not abstracted behind a model that needs G-AX validation. No
changed-inexpressible op.

## Discriminating clause (G-DIFF signal)
Rows 4–5 together. Patched: the comparison subject is
`storage = originalCallable.getD evaluatedStorage`. Pre-patch (Solution_prepatch):
the comparison subject is `evaluatedStorage`. When `originalCallable = some c`
with `c ≠ defaultStorage` but `evaluatedStorage = defaultStorage` (a callable
that returns the default storage — exactly the F2P case):

- spec / patched: `storage = c ≠ defaultStorage` ⇒ result = `some c`.
- prepatch impl: `evaluatedStorage = defaultStorage` ⇒ test false ⇒ result =
  `none`.

`some c ≠ none`, so the prepatch `correct_recordedStorage` cannot close against
the frozen `problem_spec_recordedStorage`. That is the G-DIFF signal.
