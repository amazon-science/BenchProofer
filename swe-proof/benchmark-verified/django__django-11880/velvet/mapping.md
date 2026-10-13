# mapping.md — django__django-11880

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 06909fe084f87a65459a83bd69d7cdbe4fce9a7c`, states the type
abstraction (the Lean↔Python bijection that G-CONF and G-AX use to bridge
values), and gives the provenance of each axiom / unchanged-callee contract.

## 0. What the change does (the one independently-observable behavior)

The clone routine of a form field copies the field object by first taking a
**shallow** copy of the whole object and then giving the clone its own copies of
a few specific attributes that would otherwise be shared by reference with the
source. At `base_commit` the routine copies the rendering widget (deep) and the
list of validators (slice), but it leaves one dictionary-valued attribute — the
per-field table of override messages — **shared by reference**: both the source
and the clone point at the *same* dictionary object. Consequently a later
mutation of that table through one field is observed through every other clone
of the same field.

The fix adds one line: the clone is given its **own** copy of that dictionary,
built from the source's table. After the fix, the clone's table is a *distinct
object* that *holds the same entries*. The observable that distinguishes the two
behaviors is **object identity**: post-fix, `clone.table is not source.table`
(while `clone.table == source.table` as a mapping); pre-fix, they are the same
object.

The F2P test `test_field_deep_copy_error_messages` constructs a field whose
table is non-default, clones it, and asserts (a) the clone is still an instance
of the field's subclass and (b) `field_copy.error_messages is not
field.error_messages`. The identity assertion is the discriminator.

The modeled function is the clone routine. The copy helpers it calls — the deep
copy of the widget, the **fresh copy of the table**, and the slice of the
validator list — are all **unchanged** library/builtin callees. Each produces a
*new object*; the value-typed ones (table, validators) additionally produce a
*content-equal* object, while the opaque widget produces only a distinct object
(a widget has no value equality). Each is modeled by taking THE OBJECT IT RETURNED as a parameter
of the routine, carrying that callee's weakest sufficient contract as a `require`
(§3): exactly "distinct identity, equal contents" (value-typed: `freshCopy`) and
"distinct identity" (widget: `freshDistinct`). Because each Python step is an
ASSIGNMENT of the callee's return value into a slot, the clone's slot is pinned to
that parameter (`ensures result.X = XCopy`) — for the opaque widget this is the
only observable the slot has, content-equality being unavailable. G-AX checks each
contract against its real callee.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `deepCopyField (source : FormField)` | `Field.__deepcopy__` — `django/forms/fields.py:198` (changed: new line 202) | the modeled changed function: clones a form field, giving the clone its own copies of the by-reference attributes |
| `FormField` (structure) | a `django.forms.fields.Field` instance, restricted to the identity-bearing attributes the clone routine touches | the rich object, modeled by only the touched fields (SPEC_GUIDE §2) |
| `Obj` (structure: `ref`, `payload`) | any Python object reachable as an attribute, observed through `id(o)` (identity) and its logical contents | the object-identity carrier |
| `freshCopy` *(parameter contract — A-consumed)* | `self.error_messages.copy()` — `dict.copy()`, CPython builtin; analogously `self.validators[:]` (`list[:]`) | unchanged callee on a VALUE-typed attribute: returns a NEW object (`id` differs) whose contents `==` the argument's |
| `freshDistinct` *(parameter contract — A-consumed)* | `copy.deepcopy(self.widget, memo)` — the widget copy | unchanged callee on an OPAQUE object (a widget has no value equality): returns a NEW object (`id` differs). Distinct identity is the only sound observable; content-equality is NOT claimed (would over-claim, SPEC_GUIDE §0.7) |

The shallow copy `copy.copy(self)` (`fields.py:199`) is an unchanged callee
whose only relevant effect is that the resulting object initially *shares every
attribute by reference* with the source (a shallow copy copies references, not
referents). It is modeled directly: the clone starts as a value-copy of
`source`, so every attribute `ref` initially equals the source's. This is the
faithful pre-state the patch then overrides for selected attributes. It is not
axiomatized — its behavior (reference-sharing) is exactly the Lean record copy,
and no obligation beyond that is placed on it.

`memo` (the deepcopy memo dict) and the recursion guard are bookkeeping that does
not affect the modeled observable (object identity of the clone's attributes) and
are not modeled.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-AX (§4) and G-CONF use to translate values between the Lean
value domain and the Python repo types.

| repo reality | Lean carrier | bijection |
|---|---|---|
| a Python object, observed through `id(o)` and its contents | `Obj := { ref : Nat, payload : Nat }` | `o` ↔ `⟨id(o), fingerprint(o)⟩`; `ref` is the CPython object identity (`id`); `payload` is an opaque content fingerprint such that two objects are content-equal iff their `payload`s are equal (G-AX uses `repr`/`==` as the concrete fingerprint). |
| `a is b` (object identity) | `a.ref = b.ref` | two attribute objects are the *same object* iff their `id`s are equal iff their `ref`s are equal. |
| `a == b` (mapping/content equality) | `a.payload = b.payload` | content equality is reflected by fingerprint equality. |
| `new = obj.copy()` / `obj[:]` (value-typed) | `freshCopy new obj` | the copy is a NEW object with equal contents: `new.ref ≠ obj.ref ∧ new.payload = obj.payload`. |
| `new = copy.deepcopy(widget,_)` (opaque) | `freshDistinct new obj` | the copy is a NEW object: `new.ref ≠ obj.ref` (no content claim — a widget has no value equality). |
| a `Field` instance (touched attributes + the rest as one aggregate) | `FormField := { widget, errorMessages, validators, carried : Obj }` | the three by-reference attributes the clone routine handles, plus `carried` — the field's class and every attribute the shallow duplication copies over and the routine never re-points, observed as ONE object because the routine never inspects any of it. `result.carried = source.carried` states IDENTITY (a shallow duplication hands over the source's own objects), which is what the F2P's `isinstance` assertion tests and what a fresh construction cannot satisfy. Verified on `Field.__deepcopy__` at `base_commit`: 14/14 field classes, all 8–14 untouched attributes per class are the SAME objects. |

The carrier `Obj.ref : Nat` abstracts CPython `id()` only as an *equality oracle*
(SPEC_GUIDE §8: structural, grounded in the actual objects — not an answer key):
the spec pins identity *relations* between the clone's and source's attributes,
never absolute id values. G-CONF/G-AX bridge `ref` via "are these two the same
object?" (`is`), never via a literal id.

## 3. The unchanged-callee contracts — provenance (G-AX)

The routine invokes three unchanged copy callees, modeled by TWO contracts
because the callees deliver different observables. Each is the WEAKEST contract
sound for its callee(s) (SPEC_GUIDE §0.7 — never claim more than the real callee),
carried as a `require` on the parameter standing for that callee's return value.

**`freshCopy (b a : Obj) : Prop := b.ref ≠ a.ref ∧ b.payload = a.payload`** —
models the VALUE-typed copies `dict.copy()` (the added line) and `list[:]`:
* **fresh identity**: `b.ref ≠ a.ref` — a *new* object (`new is not old`);
* **content preservation**: `b.payload = a.payload` — *same contents* (`new == old`).
Provenance: CPython `dict.copy()` returns a new dict (`Objects/dictobject.c
dict_copy`); `list[:]` returns a new list. Both guarantee `result is not source`
AND `result == source` for the mapping/list values these attributes hold.

**`freshDistinct (b a : Obj) : Prop := b.ref ≠ a.ref`** — models the OPAQUE
widget copy `copy.deepcopy(self.widget, memo)`:
* **fresh identity**: `b.ref ≠ a.ref` — a *new* object (`new is not old`).
A Django widget defines no value equality (default identity `__eq__`), so
`copy.deepcopy(w) == w` is **False**; content-equality is NOT observable and
claiming it would be an unsound over-claim. (An earlier draft of this bundle used
`freshCopy` for the widget and was correctly BLOCKED by G-AX: real
`copy.deepcopy(TextInput) != TextInput`. This split is the principled fix.)
Provenance: `copy.deepcopy` returns a new (memoized) object — `result is not
source` holds universally.

G-AX (`axiom_check.py`) constructs real `dict`/`list`/object instances (boundary:
empty, singleton, many-entry, nested) plus fuzz, calls each real callee, and
asserts exactly its stub's clauses — both `id≠` and `==` for `dict.copy()`/`list[:]`,
and only `id≠` for `copy.deepcopy` (no double-masking, SPEC_GUIDE §0.7).

Both are **A-consumed**: the proof of `deepCopyField` consumes each `require`
to discharge the postconditions that the clone's copied attributes are distinct
objects (with equal contents for the value-typed ones). The companion derivation
postconditions (`result.X = XCopy`) need no contract — they say the routine
installed what the callee handed back, which is what the Python assignment does.
They are what forbids installing some OTHER distinct object in the opaque widget
slot, the one slot no content clause can constrain (refinement.md §B measures the
two wrong implementations they exclude: 18 and 44 PASS_TO_PASS failures).

## 4. Fuzz seed (G-CONF)

The impl region of `deepCopyField` is **all-A-tagged** (its only non-trivial ops
are record updates that install the three A-consumed callee results; there is no
R/I computational content to differentially test). Per
SPEC_GUIDE §workflow, `meta.json conf_skip = true` and `conformance_check.py`
exits `status=skip`. Soundness of the A legs is covered by G-AX.

If a seed were needed it would be pinned here as `SEED = 11880`; the G-AX fuzz
uses `SEED = 11880`.
