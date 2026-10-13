# refinement.md — django__django-15128

Maps every operation in `implementation_renumberAliases` to its `patch.diff`
counterpart. Tags: **R** (type refinement), **A-consumed** (proof uses an axiom's
property), **A-reference** (deep model validated == real callee by G-AX), **I**
(identical concrete op). Every step is R, A, or I.

## Modeled function: `renumberAliases` — the change-map construction in `Query.bump_prefix`

Post-patch repo code (`patch.diff`, the changed comprehension in `bump_prefix`):
```python
def bump_prefix(self, other_query, exclude=None):
    ...
    if exclude is None:
        exclude = {}
    self.change_aliases({
        alias: '%s%d' % (self.alias_prefix, pos)
        for pos, alias in enumerate(self.alias_map)
        if alias not in exclude
    })
```

Lean impl (`implementation_renumberAliases`):
```lean
def implementation_renumberAliases
    (pfx : String) (reserved : List Nat) (aliases : List Nat) :
    List (Nat × String) := Id.run do
  let mut changeMap : List (Nat × String) := []
  for p in aliases.zipIdx do
    if isReserved reserved p.1 then continue
    changeMap := changeMap ++ [(p.1, freshName pfx p.2)]
  return changeMap
```
where `isReserved reserved a = reserved.contains a` and
`freshName pfx pos = pfx ++ toString pos`.

| # | Lean op | patch.diff / real-code counterpart | tag | justification |
|---|---|---|---|---|
| 1 | `changeMap : List (Nat × String) := []` | the dict comprehension result accumulator `{}` | **R** | the change-map dict ↔ insertion-ordered `(old, new)` association list; alias keys distinct ⇒ lossless (mapping.md). |
| 2 | `for p in aliases.zipIdx do` | `for pos, alias in enumerate(self.alias_map):` | **R** | `enumerate(self.alias_map)` over the alias keys in order ↔ `aliases.zipIdx`; `p.1` ↔ `alias`, `p.2` ↔ `pos`. The number comes from enumerating the FULL map, so a reserved alias still consumes its index — `zipIdx` matches `enumerate` exactly. |
| 3 | `if isReserved reserved p.1 then continue` | `if alias not in exclude` (comprehension filter) | **I** (deep model of the changed op) | **the fixed operation.** The post-fix filter omits an alias from the map iff it is in `exclude`; `isReserved reserved p.1` reproduces `alias in exclude` (membership), and `continue` reproduces "not emitted". `exclude=None`/`{}` ↔ `reserved=[]` ⇒ membership always false ⇒ nothing omitted (matches the pre-existing all-aliases behavior when nothing is reserved). |
| 4 | `changeMap := changeMap ++ [(p.1, freshName pfx p.2)]` | `alias: '%s%d' % (self.alias_prefix, pos)` | **R** | record the entry; key `p.1` ↔ `alias`; value `freshName pfx p.2` = `pfx ++ toString p.2` ↔ `'%s%d' % (self.alias_prefix, pos)` (prefix + decimal position). `pfx` ↔ the already-bumped `self.alias_prefix`. |
| 5 | `return changeMap` | the assembled dict handed to `self.change_aliases(...)` | **R** | the ordered association list ↔ the change-map dict. The downstream `change_aliases` application is NOT part of the modeled value (it is unchanged by the patch and consumes the map); the modeled value is precisely the change map the patch alters. |

All impl-region ops are **R/I** — there is NO A-tagged (axiom) content, so the
impl is NOT all-A-tagged: `conf_skip = false`, and `conformance_check.py`
mechanically differential-tests the R/I shadow against an in-process replica of
the post-patch change-map comprehension.

## Soundness check (verify ⟹ correct)

- `problem_spec_renumberAliases pfx reserved aliases result :=
  result = (aliases.zipIdx).filterMap (fun p => if isReserved reserved p.1 then
  none else some (p.1, freshName pfx p.2))` pins the result EXACTLY (full list
  equality to an input-grounded expression) — directive 5 (frame): the keys are
  precisely the non-reserved aliases in order, and each value is its positional
  fresh name. No output component is left unconstrained; no ungrounded oracle
  (directive 8) — the postcondition is dischargeable only by actually walking the
  indexed alias list, dropping reserved aliases, and projecting `(alias,
  freshName)`. The positional numbering (over the full enumeration, including
  reserved aliases) is fixed by `zipIdx`, so an impl cannot renumber the survivors
  contiguously and still verify.
- The prepatch impl reproduces the PRE-FIX construction: it builds an entry for
  EVERY alias regardless of the reserved set (`exclude` did not exist). It
  violates the spec on the discriminating clause `reserved` non-empty naming an
  alias present in `aliases`: the spec drops that alias's entry, but the prepatch
  still emits it. Its carried gold proof cannot close (G-DIFF/G-PANEL); the
  failing case is any `reserved` containing a present alias.
- This discriminating case is precisely what the FAIL_TO_PASS test exercises:
  combining two query sets that share an alias prefix requires the rhs's aliases
  to be renumbered EXCEPT the base/initial alias (which must stay identical on
  both sides). Renumbering the base alias too (the pre-fix behavior) makes the
  base table absent on one side and corrupts the merge (the downstream
  `change_aliases` disjointness assertion fires / the join's initial alias goes
  missing). Reserving the base alias (`exclude={initial_alias}`) is exactly
  `reserved = [base]`.
- G-CONF confirms the R/I shadow == an in-process replica of the patched
  comprehension over hand-picked edge cases (empty reserved, reserving the base
  alias, reserving a middle alias, reserving an absent alias) plus ≥1e5 fuzzed
  alias lists / reserved sets / prefixes.
