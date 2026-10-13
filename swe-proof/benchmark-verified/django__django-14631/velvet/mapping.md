# mapping.md — django__django-14631

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 84400d2e9db7c51fee4e9bb04c028f665b8e7624`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and
gives the provenance of each deep-model reference.

Repo files under change: `django/forms/forms.py`, `django/forms/boundfield.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `cleanFields (fields : List FieldSlot)` | `BaseForm._clean_fields` — `django/forms/forms.py:389` | the modeled changed function: the per-field value-resolution + clean loop |
| `FieldSlot` | one entry of `BaseForm.fields` together with its `BoundField` view (`form[name]`, `django/forms/forms.py:150`) | a single field slot the loop walks |
| `FieldSlot.readOnly` | `field.disabled` (`django/forms/fields.py` `Field.disabled`) tested in `_clean_fields` (`forms.py:391` pre / `forms.py:392` post) | whether the slot's value is fixed rather than taken from data |
| `FieldSlot.coarse` | `not bf.field.widget.supports_microseconds` (`django/forms/widgets.py:203` default `True`; `widgets.py:482` `DateTimeBaseInput` → `False`), consumed by `BoundField.initial` (`boundfield.py:213`) | whether the slot's presentation cannot carry the finer sub-count |
| `FieldSlot.stored` | the field's resolved initial — `get_initial_for_field(field, name)` (`forms.py:490`), evaluated once and cached on the `BoundField` (`boundfield.py:212`) | the slot's resolved stored value |
| `FieldSlot.given` | `bf.data` (`boundfield.py:117`) = `_widget_data_value(field.widget, html_name)` (`forms.py:194`) | the value supplied for the slot through ordinary data |
| `initialFor (f)` *(deep model — A-reference)* | `BoundField.initial` (`boundfield.py:212-220`): the microsecond-nixing of an auto-date when `not widget.supports_microseconds` (`#22502`) | the stored value as the slot exposes it |
| `slotValue (f)` | the value `_clean_fields` feeds to `field.clean` (`forms.py:392-393` post-patch: `bf.initial if field.disabled else bf.data`) | the value used to clean one slot |
| `cleanedSeq (fields)` | the sequence of values written to `self.cleaned_data` by the `_clean_fields` loop (`forms.py:389-406`) | the per-slot cleaned values across the field list |

The pre-patch repo path the change replaces (refinement audit only, not in the
consumer spec view): for a disabled field the old `_clean_fields` used
`self.get_initial_for_field(field, name)` **directly** (`forms.py:392` pre),
re-evaluating the callable initial and skipping the `BoundField.initial`
microsecond normalization; the post-patch code uses `bf.initial`
(cached + normalized). The companion refactors — `_bound_items`
(`forms.py` new), `BoundField._has_changed` / `changed_data`
(`forms.py:438`), the `data` property's `_field_data_value` → `_widget_data_value`
rename (`boundfield.py:121`) — are behaviour-preserving (refinement.md §B).

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) and G-AX use to translate values between the
Lean value domain and the Python repo types. A wrong entry surfaces as spurious
G-CONF disagreements (the falsifiability the plan §4 trust statement refers to).

| repo reality | Lean carrier | bijection |
|---|---|---|
| a resolved field value (here a `datetime`) | `Stamp` (`sec : Int`, `sub : Int`) | `datetime(2006,10,25,14,30, sec, sub)` ↔ `{ sec, sub }`; `sec ∈ [0,59]` ↔ the second field, `sub ∈ [0,999999]` ↔ the microsecond field. The two observable components the F2P tests compare (`replace(microsecond=0)`). |
| the ordered `BaseForm.fields` mapping + its `BoundField`s | `List FieldSlot` | dict-insertion order ↔ list order; `len(fields)` ↔ `fields.length`; per-field `BoundField` view ↔ one `FieldSlot` |
| `field.disabled` (bool) | `FieldSlot.readOnly` | identity on `Bool` |
| `not widget.supports_microseconds` (bool) | `FieldSlot.coarse` | identity on `Bool` |
| `BoundField.initial` value | `initialFor f` | `coarse` slot ⇒ `microsecond=0` (`{ stored with sub := 0 }`); else `stored` unchanged |
| `field.clean(value)` for the resolved datetime | identity (omitted) | `DateTimeField.clean(dt)` → `to_python(dt)` returns the `datetime` unchanged (tag I); the observable in `cleaned_data` is the resolved value itself |
| the list written to `self.cleaned_data` | `cleanedSeq fields` | element-wise via the rows above |

## 3. Deep-model reference (kind A-reference — checked by G-AX / axiom_check.py)

### 3.1 `initialFor` ↔ `BoundField.initial` (A-reference)
**Callee (unchanged):** `BoundField.initial` (`boundfield.py:212-220`). The
microsecond normalization it performs is modeled **deeply** by `initialFor`:
a slot whose widget cannot carry sub-second precision
(`not widget.supports_microseconds`, the `coarse` flag) has its stored value's
finer sub-count dropped to 0; any other slot's stored value passes through.
There is **no consumed axiom** — the changed value-resolution is spelled out in
the `pure` region. The patch routes the disabled-field branch through this
unchanged callee for the first time; that is the single behaviour the F2P tests
observe (`test_datetime_clean_disabled_callable_initial_microseconds`,
`..._bound_field`).

**Soundness check (G-AX, `axiom_check.py`):** constructs real Django forms with a
disabled `DateTimeField` and a callable initial bearing microseconds, over both
a coarse widget (default `DateTimeInput`, `supports_microseconds=False`) and a
microsecond-supporting widget (`TextInput`, `supports_microseconds=True`), plus
fuzzed second/microsecond components, and asserts (a) `BoundField.initial`
matches the `initialFor` deep model, and (b) `field.clean` is the identity on the
resolved datetime (tag I). Exit 0 iff sound.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`14631`** so the
consumer-side verdict (§11.3) is reproducible. The R/I shadow it builds
transliterates `slotValue`/`initialFor`/`cleanedSeq` (the R/I-tagged value
resolution) to Python and compares against the patched Django form's
`cleaned_data` (oracle = patch.diff at base_commit). The non-readOnly (enabled)
path supplies a value via form data; because the default `DateTimeField` input
format carries no microseconds, the enabled path is fuzzed with `sub = 0`
(coverage note logged by the script — the changed behaviour lives entirely in
the readOnly path, which is fuzzed over the full second/microsecond range).
