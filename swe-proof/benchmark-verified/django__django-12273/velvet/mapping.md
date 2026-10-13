# mapping.md — django__django-12273

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 927c903f3cd25c817c21738328b53991c035b415`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), gives the
provenance of the data-flow facts the direct model relies on, and pins the
G-CONF fuzz seed.

Repo file under change: `django/db/models/base.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `assignPrimaryIdentity (attrs, slots, value, pk)` | `Model._set_pk_val(self, value)` — `django/db/models/base.py:571` | the modeled changed function (the primary-identity setter) |
| `attrs : Store` (`Nat → Option Int`) | the record instance's attribute cells `self.__dict__` viewed by attribute-name | the mutable per-instance field store the setter writes into |
| `slots : List Slot` | `self._meta.parents.values()` — the ordered parent-link descriptors of the instance's model | read-only input: one entry per inherited-table identity the instance carries |
| `Slot.attr` | `parent_link.target_field.attname` — `django/db/models/base.py:573` (post-patch) | the attribute name on the instance that stores that inherited identity |
| `Slot.isPrimary` | the predicate `parent_link == self._meta.pk` (negated in the guard at `base.py:572`) | flags the parent link that *is* the instance's own primary key (the pk write covers it) |
| `value : Option Int` | the `value` argument of `_set_pk_val` | the new primary-identity value; `None` ↔ `none` (the issue's reset case) |
| `pk : Nat` | `self._meta.pk.attname` — `django/db/models/base.py:575` | the attribute name of the instance's own primary key cell |

The pre-patch repo symbol the change augments (refinement audit only, not in the
consumer spec view): the single statement `setattr(self, self._meta.pk.attname,
value)` (`base.py:572` pre-patch), which wrote ONLY the primary cell.

No foreign callee is axiomatized (`axioms` region is empty). `setattr`/`getattr`
are Python's builtin attribute store/load, modeled directly as cell update/read
on `Store`; `_meta.parents` / `target_field.attname` are read-only structural
descriptors of the model, modeled as the read-only input `slots`. The
distinguishing behaviour — *which* cells the setter writes — is computed entirely
from `slots` and `pk` (refinement.md §C); there is therefore no consumed axiom
and no deep-model reference to a foreign callee.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) and G-AX use to translate values between the
Lean value domain and the Python repo types. A wrong entry surfaces as spurious
G-CONF disagreements.

| repo reality | Lean carrier | bijection |
|---|---|---|
| the instance attribute store `self.__dict__` keyed by attribute name | `Store = Nat → Option Int` | each attribute name ↔ a distinct `Nat` identity (a stable enumeration fixed per test scenario in the checkers); a cell's content ↔ `Option Int` with Python `None` ↔ `none`, an int identity `n` ↔ `some n` |
| `self._meta.parents.values()` (ordered) | `slots : List Slot` | the i-th parent link ↔ `slots[i]`; order preserved (Python dict values are insertion-ordered, the loop iterates them in order) |
| `parent_link.target_field.attname` | `Slot.attr` (a `Nat`) | the attribute name string ↔ its `Nat` identity in the same enumeration as the store keys |
| `parent_link == self._meta.pk` | `Slot.isPrimary` | the parent link that coincides with the instance's own pk ↔ `isPrimary = true`; any other ↔ `false`. (`parent_link and ...` truthiness: a falsy/`None` link is never produced for these models — see §3 — so it maps to no slot.) |
| `self._meta.pk.attname` | `pk : Nat` | the instance's own primary-key attribute name ↔ its `Nat` identity |
| `setattr(self, name, value)` | cell update `fun k => if k = name then value else s k` | functional store update at one key |

`value` is `Option Int` because the only scalar identities Django primary keys
take in the F2P scenarios are integer auto-ids (or `None` on reset); the issue is
exactly about `value = None` (`none`).

## 3. Data-flow provenance (the facts the direct model encodes)

The model claims: assigning the primary identity sets the primary cell `pk` to
`value` AND sets every *non-primary* inherited-identity cell (`Slot.attr` for
`Slot.isPrimary = false`) to the same `value`; every other cell is unchanged.
This is the exact effect of the patched `_set_pk_val`:

```python
def _set_pk_val(self, value):
    for parent_link in self._meta.parents.values():
        if parent_link and parent_link != self._meta.pk:
            setattr(self, parent_link.target_field.attname, value)
    return setattr(self, self._meta.pk.attname, value)
```

Observed `parents` layouts at `base_commit` (introspected in-container; the F2P
models), as `(parent, link.attname, target_field.attname, link == pk)`:

* `Profile(User)`: pk attname `profile_id`; parents = {`User`: (`user_ptr`,
  `user_ptr_id`, target `id`, link≠pk)}. Non-primary slot writes `id`; pk write
  writes `profile_id`. ⇒ assigning resets both `profile_id` and `id`.
* `Congressman(Person, Politician)`: pk attname `person_ptr_id`; parents =
  {`Person`: (`person_ptr`, `person_ptr_id`, target `id`, **link == pk**),
  `Politician`: (`politician_ptr`, `politician_ptr_id`, target `politician_id`,
  link≠pk)}. The `Person` link *is* the pk (skipped by the guard); the
  `Politician` link is non-primary and writes `politician_id`; pk write writes
  `person_ptr_id`. ⇒ assigning resets both `person_ptr_id` and `politician_id`.
* `Person`, `User`, `Politician` (no concrete parents): `parents` empty ⇒
  `slots = []`; only the pk cell is written. (The bug is invisible here, which is
  why the F2P tests use the multi-level `Profile`/`Congressman` children.)

A falsy/`None` `parent_link` never arises for these concrete-inheritance models
(every parent link is a populated `OneToOneField`), so the `parent_link and`
short-circuit is a no-op on the tested inputs; it is modeled as "no such slot is
present", consistent with the bijection (§2). G-AX exercises the real models to
confirm this layout and the resulting write set.

**Soundness check (G-AX):** `axiom_check.py` builds the real F2P model instances
in-container, reads `_meta.parents` / `target_field.attname` / `_meta.pk.attname`,
and asserts (a) the set of attribute names the patched `_set_pk_val` writes
equals `{pk} ∪ {slot.attr : ¬slot.isPrimary}` of the model, and (b) running the
real patched setter with `value=None` clears exactly those cells (and leaves
others untouched). Imports only `django` + stdlib. Exit 0 iff sound.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`12273`** so the
consumer-side verdict is reproducible. The R/I shadow it builds transliterates
`writeSlot`/`writtenSlots` and the dedicated pk write (R/I-tagged ops) to a
Python dict update over the model's real `parents`/`pk` layout, and compares the
resulting written-cell set against `patch.diff`'s behaviour (the patched
`_set_pk_val` applied to a real instance). There is no A-tagged callee, so the
shadow is pure R/I.
