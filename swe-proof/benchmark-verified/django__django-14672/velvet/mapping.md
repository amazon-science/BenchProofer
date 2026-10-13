# mapping.md — django__django-14672

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 00ea883ef56fb5e092cbe4a6f7ff2e7470886ac4`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and
gives the provenance of each axiom / deep-model reference.

Repo file under change: `django/db/models/fields/reverse_related.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `relationIdentity (rel : RelArgs)` | the `identity` cached-property of `ManyToManyRel` — `django/db/models/fields/reverse_related.py:310-315` | the modeled changed function (the identity tuple appended by `ManyToManyRel`) |
| `canonicalize (deep model — A-reference)` | `make_hashable` — `django/utils/hashable.py` (imported at `reverse_related.py:14`, called on `limit_choices_to` at `:126`, and post-patch on the sequence slot at `:313`) | unchanged stdlib-of-the-repo callee: turns an order-only sequence value into its canonical hashable (immutable) form, identity on already-hashable values; modeled DEEPLY, validated `canonicalize == make_hashable` by axiom_check.py (G-AX) |
| `Comp` / `RelArgs` / `Slot` | the elements of the identity tuple `ForeignObjectRel.identity + (through, through_fields, db_constraint)` (`reverse_related.py:120-131, 310-315`) | spec carrier: an identity-tuple component and the through-fields slot it carries |
| `Hashable (out : List Comp)` | the precondition `hash(self.identity)` (`__hash__`, `reverse_related.py:140`) requires: every tuple element is hashable | spec predicate: the produced identity tuple is hashable as a whole |

The pre-patch repo behaviour the change fixes (refinement audit only, not in the
consumer spec view): `reverse_related.py:313` placed `self.through_fields`
**raw** into the identity tuple; when `through_fields` is a Python `list`,
`hash(self.identity)` raises `TypeError: unhashable type: 'list'`.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) and G-AX use to translate values between the
Lean value domain and the Python repo types. A wrong entry surfaces as spurious
G-CONF disagreements (the falsifiability the plan §4 trust statement refers to).

The identity tuple mixes heterogeneous Python objects (a field object, a model,
strings, booleans, `on_delete`, and the through-fields slot). The behaviour
under change touches exactly ONE slot — `through_fields` — and the property it
must restore is *hashability of the whole tuple while preserving the
equality/ordering content of that slot*. So the carrier models each tuple
element by a `Comp` tagged with whether it is already hashable, and the
through-fields slot by its content + a hashable flag.

| repo reality | Lean carrier | bijection |
|---|---|---|
| the through-fields slot value: `None`, a `tuple[str,…]`, or a `list[str,…]` | `Slot` (an inductive: `none`, `seq (items : List String) (mutable : Bool)`) | `None` ↔ `Slot.none`; a Python `tuple` of names ↔ `Slot.seq names false` (already hashable); a Python `list` of names ↔ `Slot.seq names true` (order-only, NOT hashable until canonicalized). `make_hashable` maps both `tuple` and `list` to the same canonical `tuple`. |
| an already-hashable identity-tuple element (field, model, related_name, booleans, on_delete, through, db_constraint, limit_choices_to-after-its-own-make_hashable) | `Comp.opaque (h : Bool := true)` carrying a `hashable` flag | every such element is hashable; modeled as one opaque hashable component. Their concrete values are never relied on (only that they are hashable and unchanged), so a single opaque carrier per element is faithful. |
| the through-fields element of the tuple | `Comp.slot (s : Slot)` | the one component whose hashability depends on the modeled operation |
| `make_hashable(v)` (`django/utils/hashable.py`) | `canonicalize : Slot → Slot` | `make_hashable(None)=None` ↔ `canonicalize Slot.none = Slot.none`; `make_hashable(list_or_tuple of hashables)` = a `tuple` ↔ `canonicalize (Slot.seq xs _) = Slot.seq xs false` (same items, now immutable/hashable). The F2P inputs are name lists (`['event','invitee']`); `make_hashable` over a flat sequence of hashables is `tuple(...)`, preserving items and order. |
| `hash(self.identity)` succeeds (no `TypeError`) | `Hashable out` (every `Comp` in the produced list is hashable) | a Python tuple is hashable iff every element is; `Comp.opaque true` and `Comp.slot Slot.none`/`Comp.slot (Slot.seq _ false)` are hashable, `Comp.slot (Slot.seq _ true)` is not. |

Equality content note (why hashability alone is not the whole spec): `__eq__`
compares `self.identity == other.identity`, and `__hash__` must agree with
`__eq__`. `make_hashable` turns the `list` `['event','invitee']` and the `tuple`
`('event','invitee')` into the SAME value, so an inherited reverse relation
(whose `through_fields` is the same names) compares equal AND hashes equal
(F2P `test_reverse_inherited_m2m_with_through_fields_list_hashable` asserts
`hash(reverse_m2m) == hash(inherited_reverse_m2m)`). The spec therefore pins the
slot to `canonicalize`'s output (content + immutability), not merely "some
hashable value".

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `canonicalize` deep model ↔ `make_hashable` (A-reference)
**Callee:** `django.utils.hashable.make_hashable` (`django/utils/hashable.py`),
UNCHANGED by the patch (the patch only adds a *call* to it). Source at
base_commit:

```python
def make_hashable(value):
    if isinstance(value, dict):
        return tuple([(key, make_hashable(nested_value))
                      for key, nested_value in sorted(value.items())])
    try:
        hash(value)
    except TypeError:
        if is_iterable(value):
            return tuple(map(make_hashable, value))
        raise
    return value
```

The changed operation (applying `make_hashable` to the through-fields slot) is
modeled **deeply** by `canonicalize` in the `pure` region; there is **no
consumed `makeHashable` axiom**. The domain of the slot in this codepath is
exactly what `ManyToManyRel.__init__` stores into `self.through_fields`: `None`,
or a sequence (tuple/list) of field-name strings (each a hashable `str`). On
that domain:
- `make_hashable(None) = None` → `canonicalize Slot.none = Slot.none`;
- `make_hashable(seq of strs)` hits the `try: hash(value)` branch for a tuple
  (returns it unchanged) and the `except → is_iterable → tuple(map(...))` branch
  for a list (returns the equal tuple). Either way the result is the tuple of
  the same names → `canonicalize (Slot.seq xs _) = Slot.seq xs false`.

**Soundness check (G-AX):** `axiom_check.py` runs the REAL `make_hashable` on
boundary slots (`None`, `[]`, `()`, single-name, the F2P `['event','invitee']`
and its tuple form, longer name sequences) plus randomized fuzz, asserting (a)
the result is hashable, (b) `make_hashable(list) == make_hashable(tuple(list))`
(list and tuple canonicalize equal — the equality content), and (c) the
canonical form preserves the element sequence (order + items), i.e. matches the
`canonicalize` deep model. Imports only `django.utils.hashable` (no ORM, no DB).
Exit 0 iff sound.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`14672`** so the
consumer-side verdict (§11.3) is reproducible. The R/I shadow it builds
transliterates the identity-tuple assembly (R/I-tagged ops): the opaque prefix
components are represented by sentinel hashable placeholders, and the
through-fields slot is canonicalized by the **real** `make_hashable`
(A-reference → run real callee, not the deep model). The oracle is the patched
behaviour: the through-fields slot of the identity tuple equals
`make_hashable(through_fields)` and the whole tuple is hashable. Each fuzzed
input is a `through_fields` value (`None`, a list, or a tuple of names); the
shadow asserts (i) the slot value matches `make_hashable(through_fields)` and
(ii) the assembled tuple is hashable — exactly what the patch guarantees and the
prepatch (raw slot) violates for `list` inputs.
