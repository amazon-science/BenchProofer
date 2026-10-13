# mapping.md — django__django-15315

## Symbol binding (file:line @ base_commit 652c68ffeebd510a6f59e1b56b3e007d07683ad8)

- Modeled function: `Field.__hash__`,
  `django/db/models/fields/__init__.py:544-549` @ base_commit.
- Lean name `object_hash` is a de-narrated alias for the per-instance hash of an
  identified object (it does NOT echo the patched repo symbol `Field` / `__hash__`).
- Supporting context read: `Field.__eq__` (lines 516-523) and `Field.__lt__`
  (525-542) — they establish that `creation_counter` is the construction-time
  identity token and that the model (`app_label`, `model_name`) only becomes
  available once the field is attached to a model class. Also
  `Field.__init__` / class attributes `creation_counter` and
  `auto_creation_counter`: ordinary fields receive non-negative serials
  (counting up from 0), while auto-created fields (e.g. every model's implicit
  auto pk, `auto_created=True`) draw from `auto_creation_counter`, which counts
  DOWN from `-1`. The serial domain is therefore ALL of `Int`.

## Lean ↔ Python type bijection (used by G-CONF; G-AX is a skip)

| Lean | Python |
|---|---|
| `IdObject` | a `Field` instance |
| `o.serial : Int` | `self.creation_counter` (an unbounded Python `int`; non-negative for ordinary fields, negative for auto-created ones) |
| `o.owner : Option (String × String)` | `(self.model._meta.app_label, self.model._meta.model_name)` if `hasattr(self,'model')`, else `None` |
| `implementation_object_hash o : Int` | `Field.__hash__(self)` return value |
| `result = int_hash o.serial` | `hash(self.creation_counter)` |

### The concrete model of `hash(int)` (`int_hash`)

The real fix returns `hash(self.creation_counter)`. CPython's `hash` on an
unbounded `int` is NOT the identity: the magnitude is reduced modulo the
Mersenne prime `M = sys.hash_info.modulus = 2**61 - 1`, the sign is
re-applied, and the reserved output `-1` is mapped to `-2` (so
`hash(-1) == -2`). The Lean `int_hash` mirrors this law exactly:

    int_hash n = let r := if 0 ≤ n then n % M else -((-n) % M)
                 if r = -1 then -2 else r

In particular `int_hash n = n` for `0 ≤ n < M`, `int_hash (-1) = -2`, and
`int_hash` never returns `-1`. There is no domain precondition on
`correct_object_hash`: the spec pins the result for EVERY serial, including
the negative `auto_creation_counter` serials of auto-created fields. G-CONF
differential-tests `int_hash` against the REAL patched `Field.__hash__` over
the full signed domain, probing every boundary (`0`, `±1`, `±(M−1)`, `±M`,
`±(M+1)`, multi-limb magnitudes).

## Callee provenance + flag deps

- No unchanged callee is consumed as an axiom. The built-in `hash` of an
  integer is modeled concretely as `int_hash` inside the pure region (a
  mechanically-refutable model, not an axiom); G-CONF differential-tests it
  against the real callee.
- Flag dependency: the presence/absence of `self.model` (i.e. whether the field
  has been attached to a model class) corresponds to `o.owner` being `some`/`none`.
  G-CONF fuzzes both states (and varies the owner label/name strings) to confirm
  the result is invariant under attachment.

## G-CONF fuzz seed

Pinned seed: `15315` (`random.Random(15315)`), N = 100000.
