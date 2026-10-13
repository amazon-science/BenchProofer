# refinement.md — django__django-11999

Maps every operation in the `registerAccessor` `do` block to its `patch.diff`
counterpart. Tags: **R** (type refinement; state the bijection), **A-consumed**
(proof uses an axiom's `ensures`), **A-reference** (deep model validated == real
callee by G-AX), **I** (identical concrete op). Every step is R, A, or I.

## Modeled function: the registration step in `Field.contribute_to_class`

Post-patch repo code (`patch.diff`):
```python
if self.choices is not None:
    if not hasattr(cls, 'get_%s_display' % self.name):
        setattr(
            cls,
            'get_%s_display' % self.name,
            partialmethod(cls._get_FIELD_display, field=self),
        )
```

Lean `do` block (`registerAccessor`):
```lean
let mut result := lookup
if (lookup key).isNone then
  result := (fun n => if n = key then some gen else lookup n)
return result
```

| # | Lean op | patch.diff / real-code counterpart | tag | justification |
|---|---|---|---|---|
| 1 | `lookup : Namespace` (`String → Option Nat`) | the class attribute namespace `cls`, as queried by `hasattr`/`getattr` | **R** | namespace ↔ name→identity-kind partial map (mapping.md). Only the presence and identity-kind of the binding at a name are observable to this step. |
| 2 | `key : String` | `'get_%s_display' % self.name` | **R** | identity on names; the format string is computed upstream of the modeled step and supplied as the carrier `key`. |
| 3 | `gen : Nat` (`= 1` at the call site) | `partialmethod(cls._get_FIELD_display, field=self)` | **R** | the generated accessor ↔ the token `gen`; the step never inspects its value, only installs it. mapping.md fixes `gen = 1` (the auto kind) vs `0` (a user kind). |
| 4 | `if (lookup key).isNone then …` | `if not hasattr(cls, 'get_%s_display' % self.name):` | **I** | `hasattr(cls, key)` is true ⟺ `key` is bound in the namespace ⟺ `lookup key ≠ none`; so `not hasattr` ⟺ `(lookup key).isNone`. Identical guard. |
| 5 | `result := (fun n => if n = key then some gen else lookup n)` | `setattr(cls, key, partialmethod(...))` | **I** | single-name namespace update: bind `gen` at `key`, leave every other name unchanged. Models `setattr` of one attribute. |
| 6 | (else: `result := lookup` unchanged) | (no `setattr` — the existing binding is preserved) | **I** | when `key` is already bound the branch is skipped, so the namespace — and in particular the binding at `key` — is returned exactly as received. This is the fixed behavior: a pre-existing accessor at `key` survives. |

All impl-region ops are **R/I** — there is NO A-tagged (axiom) content, so the
impl is NOT all-A-tagged: `conf_skip = false`, and `conformance_check.py`
mechanically differential-tests the R/I shadow against the real registration
behavior of `Field.contribute_to_class`.

## Soundness check (verify ⟹ correct)

- `ensures out = registerDisplay lookup key gen` pins the result EXACTLY (full
  functional equality to the input-grounded set-if-absent update) — directive 5
  (frame): the post-state of every name is determined by the input namespace.
  No output component is left unconstrained; the `else` leg explicitly preserves
  the entire input `lookup`, so a pre-existing binding at `key` is pinned to its
  input value. No ungrounded oracle (directive 8) — the postcondition is
  dischargeable only by actually performing the conditional update.
- The prepatch impl (unconditional overwrite) violates the spec exactly on the
  discriminating clause `(lookup key) ≠ none` (any namespace already binding
  `key`): it returns `fun n => if n = key then some gen else lookup n`, which
  differs from `registerDisplay = lookup` at `key`. Its carried proof therefore
  cannot close (G-DIFF / G-PANEL). This is precisely the issue: a user-defined
  `get_<name>_display` (already present in the namespace) must not be displaced.
- G-CONF confirms the R/I shadow == the real registration behavior over ≥1.0e5
  fuzzed (model, field-name, choices, override-present?) cases.

## Non-modeled coupled change

None. The gold patch touches only the choices-branch of `contribute_to_class`;
there is no second site to carry.
