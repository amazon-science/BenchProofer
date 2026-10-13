# refinement.md — django__django-15315

Maps every op in `implementation_object_hash` (Solution.lean) to its
`patch.diff` counterpart. Tags: **R** type-refinement, **A-consumed** axiom used
by proof, **A-reference** deep model validated == real callee by G-AX, **I**
identical concrete op.

The modeled function is `Field.__hash__`. The patch replaces the 3-tuple hash
`hash((creation_counter, app_label_or_None, model_name_or_None))` with the
single-component `hash(creation_counter)`, making the result independent of the
owner identity (which only exists after the field is attached to a model class)
— i.e. the hash becomes immutable across attachment.

| # | Lean impl op | patch.diff / repo counterpart | tag | note |
|---|---|---|---|---|
| 1 | `return int_hash o.serial` | `return hash(self.creation_counter)` | I | `o.serial : Int` ↔ `self.creation_counter` (both unbounded signed integers — ordinary fields count up from 0, auto-created fields count DOWN from `-1` via `auto_creation_counter`, so negatives are real inputs). `int_hash` is a concrete transliteration of CPython's `hash(int)`: sign-preserving reduction of the magnitude modulo the Mersenne prime `M = 2^61 − 1` (`sys.hash_info.modulus`), then the reserved output `-1` mapped to `-2` (so `int_hash (-1) = -2 = hash(-1)`). The owner identity `o.owner` is deliberately NOT consulted — modeled by omission, matching the removal of the `app_label`/`model_name` tuple components. G-CONF differential-tests `int_hash` against the real `Field.__hash__` over the full signed domain, probing `0`, `±1`, `±(M−1)`, `±M`, `±(M+1)` and multi-limb magnitudes. |

There is no proof-region precondition: `correct_object_hash` quantifies over
every `IdObject`, so the spec pins the hash for the negative auto-created
serials as well (`hash(-1) == -2` is reproduced exactly). No changed op is
inexpressible. No row is A-tagged ⇒ `axiom_check.py` is a skip stub and
`meta.json axioms`/`deep_model_references` are empty. Row 1's `int_hash` model
is mechanically refuted by G-CONF (shadow vs real `Field.__hash__`).

## Prepatch correspondence (G-DIFF)

- `Solution_prepatch.lean` carries the **pre-#31750-revert bug**: the hash folds
  in the owner identity when present, exactly the defect the issue describes —
  the hash CHANGES when the field is attached to a model. For any `o` with
  `o.owner = some (label, name)` the impl returns `int_hash o.serial + d` with
  `d ≥ 1`, contradicting the postcondition `result = int_hash o.serial`. The
  carried gold proof body (`rfl` after unfolding) no longer typechecks ⇒ fails
  G-VERIFY. (Confirmed: prepatch verify exits 1.)

The prepatch's owner-folding is a faithful skeleton of the removed code: the
real pre-patch `__hash__` hashed the tuple `(creation_counter, app_label,
model_name)`, whose value depends on the owner components whenever the field has
a model. The Lean prepatch folds a value-dependent digest of the owner strings
(`d := 1 + Σ (c.toNat + 1)` over the label and name characters) into the result,
so the contribution actually distinguishes different `(label, name)` values and
is strictly positive for any attached object — exactly the owner-dependence the
real bug exhibited. For any `o` with `o.owner = some …` the impl returns
`int_hash o.serial + d ≠ int_hash o.serial`, contradicting the discriminating
clause `result = int_hash o.serial`.
