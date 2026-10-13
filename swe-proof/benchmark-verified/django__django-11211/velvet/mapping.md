# mapping.md — django__django-11211

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = ba726067604ce5a8ca3919edf653496722b433ab`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and
gives the provenance of each axiom.

Repo file under change: `django/db/models/fields/__init__.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `preparedValue (value : Val)` | the value-preparation method added on the identifier field class (`django/db/models/fields/__init__.py:2309` class body) | the modeled changed function: prepare a field value for use as a relational lookup key |
| `preCoerce` *(axiom — A-consumed)* | base `Field.get_prep_value` — `django/db/models/fields/__init__.py:771` | unchanged base callee invoked via `super()`; generic representation-preserving housekeeping (identity on this domain) |
| `canonicalize` *(axiom — A-consumed)* | `to_python` of the identifier field — `django/db/models/fields/__init__.py:2338` | unchanged callee: normal-form conversion to the canonical representation |
| `Val` (inductive) | the value space of the field (`None` / a concrete identifier object / its textual transcription / its integer transcription) | carrier; per-case bijection in §2 |
| `WellFormed` *(axiom — predicate)* | "`to_python` accepts the value (does not raise `ValidationError`)" — `__init__.py:2338-2349` | domain restriction; the F2P inputs satisfy it |

The pre-patch behavior the change replaces (refinement audit only, not in the
consumer spec view): the field class defined **no** value-preparation method of
its own, so it inherited only `Field.get_prep_value` (`__init__.py:771`) — the
base preliminary coercion with no normal-form conversion.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-AX (§3) uses to translate values between the Lean value
domain and the Python repo types. A wrong entry surfaces as a spurious G-AX
disagreement.

| repo reality | Lean carrier | bijection |
|---|---|---|
| `None` | `Val.absent` | the absent value; both callees pass it through |
| a concrete identifier object (the canonical stored form) | `Val.concrete cs` | `cs : List Char` is the 32-hex-digit canonical transcription of the object; `str(obj)`'s hex ↔ `cs` |
| a textual transcription of the value (`str` form, e.g. a hyphenated or 32-char hex string) | `Val.textual s` | `s : List Char` ↔ the Python `str`; `len(s)` ↔ `s.length` |
| an integer transcription of the value (`int` form) | `Val.numeric n` | `n : Nat` ↔ the Python non-negative `int` |
| the canonical representation a value is stored and compared as | the fixed point of `canonicalize` | `canonicalize` ↔ `to_python` (returns a concrete identifier object); already-concrete ⇒ unchanged |

`Val` is opaque (no operations are performed on its payload in the impl); the
spec speaks only through the two callee axioms, so the modeling makes no claim
about the field's internal parse beyond the two facts in §3.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `preCoerce` ↔ `Field.get_prep_value` (A-consumed)
**Callee:** `django.db.models.fields.Field.get_prep_value` (`__init__.py:771`):

```python
def get_prep_value(self, value):
    """Perform preliminary non-db specific value checks and conversions."""
    if isinstance(value, Promise):
        value = value._proxy____cast()
    return value
```

For every value in the modeled domain (`None`, a concrete object, a `str`, an
`int` — none of which is a lazy `Promise`), this is the **identity**. The axiom
`preCoerce_id : preCoerce v = v` pins exactly that — the weakest sufficient
contract (directive 7). G-AX runs the real base method over the corpus and
asserts it returns its argument unchanged.

### 3.2 `canonicalize` ↔ `to_python` (A-consumed)
**Callee:** the identifier field's `to_python` (`__init__.py:2338`):

```python
def to_python(self, value):
    if value is not None and not isinstance(value, uuid.UUID):
        input_form = 'int' if isinstance(value, int) else 'hex'
        try:
            return uuid.UUID(**{input_form: value})
        except (AttributeError, ValueError):
            raise exceptions.ValidationError(...)
    return value
```

It maps any accepted transcription (`str` hex, `int`) to the single canonical
object (`uuid.UUID`); an already-canonical object is returned unchanged. The one
load-bearing property the proof consumes is **idempotence on well-formed input**:
`canonicalize (canonicalize v) = canonicalize v` (its output is already
canonical, so a second conversion is a no-op). The axiom pins only that — not the
exact bytes of any particular conversion (directive 7: do not over-claim).

**Soundness check (G-AX):** `axiom_check.py` constructs the real field, runs the
real `get_prep_value` (base) and `to_python` (conversion) over a corpus of
well-formed values — `None`, freshly generated identifiers, their 32-char and
hyphenated hex transcriptions, integer transcriptions, boundary identifiers
(all-zero, all-`f`) — plus randomized fuzz, asserting (a) the base method is the
identity (`preCoerce_id`) and (b) the conversion is idempotent
(`canonicalize_idem`) and a non-canonical transcription is brought to the SAME
canonical object as the concrete value it denotes (the property the prepared key
relies on). Imports only `django.db.models` (the repo's own field module,
in-container) and stdlib `uuid`. Exit 0 iff every obligation holds.

### 3.3 `WellFormed` (domain predicate)
Models "`to_python` accepts the value" — i.e. the conversion does not raise. The
F2P scenario only ever prepares values that are accepted transcriptions of a real
identifier, so the precondition is satisfied on the tested path. G-AX restricts
its corpus to well-formed values accordingly.

## 4. G-CONF disposition (conf_skip)

The impl region of `preparedValue` is **all-A-tagged**: both ops are the unchanged
callees `preCoerce` and `canonicalize` (`:|` choice stubs), with no R/I
computational content to transliterate and differentially test against
patch.diff. Per SPEC_GUIDE §4.1 / the worker rules, `meta.json conf_skip=true`
and `conformance_check.py` is a stub that exits with `status=skip`. The soundness
of the A legs is covered by G-AX (axiom_check.py, §3). No fuzz seed is required.
