# mapping.md — django__django-15315

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 652c68ffeebd510a6f59e1b56b3e007d07683ad8`, states the type
abstraction, and gives the provenance of the single axiom.

Repo file under change: `django/db/models/fields/__init__.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `located_value(self)` | `Field.__hash__(self)` — `django/db/models/fields/__init__.py:544` (body lines 545-549) | the modeled changed function (the value used to locate a field in a hash container) |
| `Descriptor` | `Field` (the descriptor class) — `django/db/models/fields/__init__.py:103` (`class Field(RegisterLookupMixin)`) | minimal class carrying only the touched fields |
| `Descriptor.order` | `Field.creation_counter` — set once at construction (`__init__`, lines 164-168) and never mutated thereafter | the fixed creation-order identity |
| `Descriptor.has_owner` | `hasattr(self, 'model')` — the attachment flag tested at lines 547-548; `self.model` is set by `Field.contribute_to_class` (line 783, `self.model = cls`) when the field is assigned to a model class | whether the field has been attached to a model |
| `Descriptor.owner_label` | `self.model._meta.app_label` (line 547) | owner-derived attribute available only once attached |
| `Descriptor.owner_name` | `self.model._meta.model_name` (line 548) | owner-derived attribute available only once attached |

**Attribute-existence modeling (permission structure).** In the real program an
UNattached field simply lacks the `model` attribute: any read of
`self.model._meta.*` on an unattached field raises `AttributeError` (this is
observable — the F2P test `test_hash_immutability` hashes an unattached
`IntegerField` first, so a `__hash__` that reads `self.model` unconditionally
ERRORS there). The spec mirrors this existence condition with conditional
permissions: `Acc(self.owner_label, 1/2)` and `Acc(self.owner_name, 1/2)` are
granted only under `Implies(self.has_owner, ...)`. An implementation may
therefore read an owner-derived attribute only on a path where it has
established `self.has_owner` (the model analogue of a `hasattr(self, 'model')`
guard), exactly as the real code must. An unconditional owner-attribute read —
even one whose returned value is correct — is rejected by the verifier for
insufficient permission, matching the real `AttributeError`.

**Termination obligation (total correctness).** `located_value` carries
`Requires(MustTerminate(2))` (and the `Descriptor` constructor
`MustTerminate(1)`): the real hash-site method is a bounded straight-line
delegation to the hashing primitive and always returns. Without the obligation,
a non-returning implementation would verify vacuously while its real
counterpart hangs every hash-container lookup; with it, any loop needs a
decreasing measure and unbounded recursion is rejected. The gold body
discharges the obligation trivially.
| `hash_int(value)` *(axiom — A-consumed)* | the builtin `hash` applied to an `int`, `hash(self.creation_counter)` — the post-fix body at line 545 | unchanged standard hashing primitive on a single integer |

The pre-patch repo behaviour the change removes (for the refinement audit, not
referenced from the consumer spec view): the 3-tuple hash
`hash((self.creation_counter, self.model._meta.app_label if hasattr(self,
'model') else None, self.model._meta.model_name if hasattr(self, 'model') else
None))` (lines 545-549), whose value differs before vs. after attachment.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `Field.creation_counter` (`int`) | `Descriptor.order : int` | identity on `int` |
| `hasattr(self, 'model')` (presence of the `model` attribute) | `Descriptor.has_owner : bool` | the attribute is absent before `contribute_to_class`, present after → `has_owner` False/True |
| `self.model._meta.app_label` (a `str`) | `Descriptor.owner_label : int` | the concrete app-label value is immaterial to the tested behaviour (only whether it participates); modeled as an opaque `int` identity |
| `self.model._meta.model_name` (a `str`) | `Descriptor.owner_name : int` | likewise an opaque `int` identity |
| the returned hash (`int`) | `located_value` return (`int`) | identity on `int` |
| `hash(self.creation_counter)` builtin call | `hash_int(self.order)` axiom call | identity (same primitive, one-int argument) |

The owner-derived attributes are modeled as `int` identities (not strings)
because the tested behaviour is precision-/value-independent: the F2P test
observes only that the located-value does NOT change when the owner attributes
become available, never any particular owner-attribute value. Modeling them as
opaque ints is sound for that observation and avoids banned `str` handling.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `hash_int` ↔ builtin `hash` on an `int` (A-consumed)
**Callee:** the Python builtin `hash`, applied to a single `int`
(`hash(self.creation_counter)` in the post-fix body, line 545). It is unchanged
by the patch — the patch only changes WHAT is hashed (a lone int instead of a
3-tuple), not the hashing primitive itself.

**Axiom (weakest sufficient):** `hash_int` is a `@Pure @ContractOnly` function
of one `int` with NO `Ensures` clause. The only property the proof consumes is
that it is a deterministic function of its single argument — which `@Pure`
already grants in Nagini. The proof needs nothing about the concrete hash value
(the F2P test never inspects a particular value; it checks equality of two
hashes of the same field), so the axiom states nothing about the value. This is
strictly weaker than the real callee's behaviour, hence sound: `hash` on an int
is indeed a deterministic pure function of that int within a process.

**Conformance check (G-CONF):** `conformance_check.py` differentially tests
the contract-stripped impl region (shadow) against the real patched
`Field.__hash__` in-container over >= 1.2e5 (order, owner-state) probes plus
attachment-transition probes. Pinned fuzz seed: **15315** (the instance
number).

**Soundness check (G-AX):** `axiom_check.py` runs the real builtin `hash` on
20 boundary integers (0, ±1, ±2^31, ±2^63, ±2^64, large magnitudes, the NaT-ish
`-2**63`) and 20 000 randomized fuzz integers, asserting determinism (repeated
and equal-input calls agree). It additionally validates the A-reference oracle
the deep model encodes: that `hash(creation_order)` is invariant under owner
attachment, whereas the pre-fix `hash((creation_order, owner_label,
owner_name))` changes — the exact differential the F2P test
`test_hash_immutability` exercises. Stdlib-only (no Django import); exit 0 iff
sound.
