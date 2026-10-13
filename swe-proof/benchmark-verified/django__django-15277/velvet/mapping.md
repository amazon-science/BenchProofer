# mapping.md — django__django-15277

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 30613d6a748fce18919ff8b0da166d9fda2ed9bc`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and records
callee/flag provenance. This bundle ships **no axioms**, so there is no G-AX
obligation (axiom_check.py is intentionally absent — gates.py treats a missing
axiom_check.py as G-AX skip).

Repo file under change: `django/db/models/fields/__init__.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `configureValidators (priorValidators) (lengthBound)` | the validator-list assembly performed during `CharField.__init__` — `django/db/models/fields/__init__.py:1010-1013` (the changed body line is `1013`) | the modeled changed initialization step |
| `Validator.lengthBound (lim : Option Int)` | `validators.MaxLengthValidator(self.max_length)` — `django/core/validators.py:383` (`BaseValidator.limit_value`, `:322`) | spec carrier: a length-bound check whose configured bound is `lim` |
| `Validator.existing (j : Nat)` | any validator already on the field before this step — `Field.validators` cached property = `[*default_validators, *self._validators]` (`fields/__init__.py:609-615`); for `CharField`, `default_validators == []` so this is the constructor's `validators=` kwarg (`Field.__init__`, `:170`, `:137`) | spec carrier: an opaque pre-existing validator (its kind is irrelevant) |
| `priorValidators : List Validator` | the field's validators list immediately before the length-bound decision | input |
| `lengthBound : Option Int` | `self.max_length` (`Field.__init__`, `:143`) — `None` when no length bound configured | input |
| `out : List Validator` | `self.validators` after `CharField.__init__` returns | output |

The pre-patch line the change guards (refinement audit only, not in the consumer
spec view): the unconditional `self.validators.append(validators.MaxLengthValidator(self.max_length))`
at `fields/__init__.py:1013`.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean value
domain and the Python repo types. A wrong entry surfaces as spurious G-CONF
disagreements.

| repo reality | Lean carrier | bijection |
|---|---|---|
| `self.max_length` (`int` or `None`) | `Option Int` | `None` ↔ `none`; an `int n` ↔ `some n`. `len`-of-bound never inspected; only `is None` is observed, so the abstraction needs only the `none`/`some` distinction (and, for `some`, the value, which the result re-carries). |
| a validator already on the field | `Validator.existing j` | each prior validator ↔ one opaque `existing` tag; `j` only keeps distinct entries distinct (the model never inspects a prior validator's kind). G-CONF abstracts every prior (non-MaxLength) validator to the same opaque tag `('E',)`. |
| `validators.MaxLengthValidator(self.max_length)` | `Validator.lengthBound lengthBound` | the appended length-bound check ↔ the `lengthBound` constructor carrying the same optional bound; G-CONF abstracts a real `MaxLengthValidator` to `('L', limit_value)`. |
| `self.validators` list | `List Validator` | Python list ↔ Lean `List`; `append(x)` of a single element ↔ `++ [x]`; order preserved; `[]` ↔ `[]`. |

`Field.validators` is a `@cached_property` returning `[*default_validators,
*self._validators]`; `CharField.default_validators == []`, so before the changed
line the validators list is exactly the `validators=` kwarg (stored as
`self._validators`). The change appends to that list. The bijection above is the
identity on list structure; the only behavior under spec is **whether** the
length-bound element is appended.

## 3. Callee / flag provenance

- **No axiomatized callees, no deep-model references.** The construction of
  `MaxLengthValidator` is modeled as the opaque tag `Validator.lengthBound`; the
  spec asserts nothing about the validator's internal behavior, only its presence
  and its configured bound. The pre-existing validators are likewise opaque. So
  there is no unchanged callee whose contract the proof consumes, and nothing for
  G-AX to validate against a real callee. (`meta.json axioms = []`,
  `deep_model_references = []`; G-AX skips.)
- **Flag/condition dependency (G-CONF coverage):** the decision branches solely
  on `self.max_length is None`. G-CONF therefore fuzzes `max_length ∈ {None, 0,
  1, 2, negative, typical, large}` crossed with a prior-validators list of length
  0–4 to exercise both branches and the append position. Note `max_length=0` and
  negatives are `not None`, so the check IS registered (the change keys on
  `is not None`, not on validity — validity is a separate system-check concern,
  `_check_max_length_attribute`, untouched here).

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`15277`** so the
consumer-side verdict is reproducible. The R/I shadow it builds transliterates
`configureValidators` (all-R/I, no A-tagged op) to Python and reads its inputs
from / compares its output against a real patched `CharField` (the
`MaxLengthValidator`-or-not abstraction). Boundary cases (no-bound F2P scenario,
zero/negative/typical bounds, prior validators present) precede the fuzz stream.
