# mapping.md — django__django-14631

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 84400d2e9db7c51fee4e9bb04c028f665b8e7624`, states the type
abstraction, and gives the provenance of each modelled operation.

Repo files under change: `django/forms/forms.py`, `django/forms/boundfield.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `clean_bound_initial_field(fs)` | `BaseForm._clean_fields` — `django/forms/forms.py:389` (the disabled-field branch, line 391-392 pre-patch) | the modeled changed function: the per-field cleaned-value computation, in the case where the value is taken from the field's bound initial (the disabled-field path). |
| `bound_initial(fs)` | `BoundField.initial` — `django/forms/boundfield.py:212` (`@cached_property`) | pure spec: the value exposed as the field's bound initial — a single, cached evaluation of the initial source, microsecond-normalised. |
| `normalise(value)` | the microsecond strip inside `BoundField.initial` — `boundfield.py:217-219` (`data = data.replace(microsecond=0)` when the value is a date/time and `widget.supports_microseconds` is false) | pure spec: drop the sub-second component of a date/time value. |
| `FieldState.first_eval` | the value returned by the FIRST evaluation of the initial source — `BaseForm.get_initial_for_field` — `forms.py:490` (`value = self.initial.get(...); if callable(value): value = value()`), as cached by `BoundField.initial` | the single evaluation the bound initial caches. |
| `FieldState.fresh_eval` | the value a SECOND, independent evaluation of the same source would yield — i.e. what the pre-patch `_clean_fields` obtained by calling `get_initial_for_field(field, name)` again (`forms.py:392` pre-patch), un-normalised | the fresh re-evaluation the pre-patch path used (the bug). |
| `clean` (identity step in the impl) | `Field.clean(value)` for the disabled `DateTimeField` — `django/forms/fields.py:144` (`to_python` then validate); `DateTimeField.to_python(dt)` returns the `datetime` unchanged (`fields.py:457`, `from_current_timezone` is the identity with `USE_TZ=False`) | the identity on the value being cleaned (a date/time validates to itself). |

The pre-patch repo construct the change removes (for the refinement audit, not
referenced from the consumer spec view): the disabled-field branch
`value = self.get_initial_for_field(field, name)` (`forms.py:391-392`), replaced
by `value = bf.initial if field.disabled else bf.data`.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| a `datetime.datetime` / `datetime.time` value | `int` encoding `whole_seconds * 1_000_000 + sub_second_units`, `0 <= sub_second_units < 1_000_000` | `v ↔ datetime`; whole-second floor `(v // 1_000_000) * 1_000_000` ↔ `dt.replace(microsecond=0)`; `>= 0` by choosing a fixed epoch (axiom_check.py `_encode`). |
| the disabled-field cleaning step of `_clean_fields` is bounded, straight-line code (`value = bf.initial`, then the identity clean): it always terminates and produces the cleaned value | `Requires(MustTerminate(2))` | total-correctness obligation: forbids a same-spec impl that diverges (hangs) instead of producing the value — such an impl satisfies the value postconditions only vacuously, and its faithful patch hangs `form.is_valid()` and the F2P test (the partial-correctness gap the G-EQ audit demonstrated). |
| `BoundField.initial` (a `@cached_property`: one evaluation, microsecond-stripped) | `bound_initial(fs) == normalise(fs.first_eval)` | the cache ↔ "the single first evaluation"; the microsecond strip ↔ `normalise`. |
| `get_initial_for_field(field, name)` re-evaluating a callable initial | a SECOND read of the source, modelled as the distinct field `fs.fresh_eval` — to which the cleaning function is granted **NO permission at all** | a stateful callable (e.g. `FakeTime().now`) yields `fresh_eval != first_eval`; a microsecond-bearing source yields `fresh_eval` un-normalised. |
| evaluating the initial source is STATEFUL: every call to a callable initial advances its own state, so ANY extra evaluation inside `_clean_fields` — even a dead one whose result is discarded — shifts which value `BoundField.initial` caches (the cache captures the NEXT evaluation if the extra call happens before `bf.initial` is first read). The F2P `FakeTime().now` advances one second per call; a dead `get_initial_for_field` call before `value = bf.initial` makes `bf.initial` cache `...:47` instead of `...:46`, failing the hidden tests. | the precondition grants no `Acc(fs.fresh_eval)` — reading `fs.fresh_eval` (modelling a second evaluation of the source, dead or live) fails verification for INSUFFICIENT PERMISSION | permission-as-effect: the right to evaluate the source afresh is a capability the cleaning step does not have; the G-EQ audit's atk_8 (dead read of `fresh_eval`, then the correct value) is exactly the impl this pin rejects. |
| `field.disabled` is `True` (the modelled branch) | implicit (the function models exactly that branch) | the non-disabled branch reads `bf.data` instead; out of scope of this function. |
| `Field.clean(value)` on a disabled `DateTimeField` | identity (`cleaned = value`) | `to_python(datetime) == datetime` with `USE_TZ=False`; validators do not alter the value (mapping §1 last row). |
| the `(name, bf)` iteration refactor (`_bound_items`), the `data` property callee rename (`_field_data_value` → `_widget_data_value`), the `_html_output` / `changed_data` / `_has_changed` refactors | not modelled (no observable behaviour change) | pure refactors: `_field_data_value(field, n)` was defined as `self._widget_data_value(field.widget, n)` (`forms.py:200-201`), so the rename is an inline of the same call; `_bound_items` yields the same `(name, self[name])` pairs `self.fields.items()` + `self[name]` produced; `changed_data`/`_has_changed` recompute the identical per-field changed predicate via the BoundField. The only F2P-observable behaviour is the `_clean_fields` disabled-field value source (modelled here). |

## 3. Deep-model references (kind A-reference — checked by G-AX / axiom_check.py)

There is **no consumed `@ContractOnly` axiom**: every operation the
cleaned-value computation performs is modelled deeply.

### 3.1 `bound_initial` / `normalise` ↔ `BoundField.initial` (A-reference)
**Callee:** `BoundField.initial` (`boundfield.py:212-220`). It is a
`@cached_property`, so the underlying initial source is evaluated **once** and
reused; and for an auto-generated date/time value whose widget does not support
microseconds it does `data = data.replace(microsecond=0)`. The model encodes
exactly this: the cached single evaluation is `fs.first_eval`; the microsecond
strip is `normalise`; hence `bound_initial(fs) == normalise(fs.first_eval)`.

**Soundness check (G-AX):** `axiom_check.py` constructs the exact F2P scenario —
a disabled `DateTimeField` with a STATEFUL, microsecond-bearing callable initial
(`FakeTime().now`) — and asserts against the REAL Django machinery that
(R1) `BoundField.initial` equals the normalised first evaluation,
(R2) the disabled field's cleaned value equals `BoundField.initial`, and
(R3) a fresh re-evaluation of the source (the pre-patch path) DISAGREES with it
(so the differential witness is non-vacuous). It also fuzzes `normalise` over
50 008 inputs (idempotence, floor-to-second, range). Exit 0 iff sound. Imports
only stdlib + Django.

### 3.2 `clean` identity ↔ `Field.clean` on a disabled `DateTimeField`
`Field.clean(value)` = `to_python(value)` then `validate`/`run_validators`
(`fields.py:144-151`). For a `datetime` value passed to a `DateTimeField`,
`to_python` returns it unchanged (`fields.py:457`, `from_current_timezone` is the
identity when `USE_TZ` is false, the test setting), and the validators do not
mutate it. So on the tested input `clean` is the identity — modelled as
`cleaned = value`. (This is the unchanged callee the modelled branch invokes; it
is the identity on the tested input, so no separate axiom is needed.)

## G-CONF (differential conformance)

`conformance_check.py` refutes (does not prove) the R/I refinement leg: does the
MODEL agree with the REAL patched repository function it claims to model?

**Shadow (provenance `direct`).** The impl region of
`clean_bound_initial_field` copied VERBATIM with only the contract calls
stripped, plus its `@Pure` dependencies `bound_initial` / `normalise` and the
`FieldState` carrier. No Nagini carrier shim is needed (the region is over plain
`int`s — no `PSeq`/`ToSeq`), and there is no `@ContractOnly` callee to redirect
to a real function (§3: the bundle consumes no axioms, so it is exactly the deep
model that this gate puts at risk).

**Oracle (called, not transliterated).** `BaseForm._clean_fields`
(`django/forms/forms.py:389` @ base_commit; §1), driven the only way it is
reachable — a real bound Django form with one disabled temporal field, then
`form.cleaned_data[name]`. The gate applies `patch.diff` to /testbed first, so
the patched `value = bf.initial if field.disabled else bf.data` and the real
`BoundField.initial` `@cached_property` (`boundfield.py:212`) execute unmodified.
Nothing is stubbed or replicated; the only instrumentation wraps the field's
initial *source* (an input to the modeled function) to record its evaluations.

**Type bridge (§2, inverted).** `encode_datetime` maps a `datetime` to the model
int `whole_seconds * 1_000_000 + sub_second_units` from the fixed epoch
`datetime.datetime.min` (`encode_time` from midnight) — the same bijection
`axiom_check.py` pins, with a lower epoch so that every representable datetime
encodes `>= 0` and every generated input satisfies `Requires(first_eval >= 0)`.
Both epochs have `microsecond == 0`, so the model's `normalise` (floor to a
multiple of 1_000_000) is exactly the repo's `data.replace(microsecond=0)`.
Generation runs in the repo direction, so the domain is inside Requires by
construction.

**Modeled branch.** `field.disabled is True` with a widget that does NOT carry
sub-second precision (`DateTimeInput`/`TimeInput`, `supports_microseconds =
False`, `widgets.py:482`). A micro-supporting widget is a different branch of
`BoundField.initial` that this model does not claim to cover, so it is
deliberately excluded rather than silently avoided.

**Three independent failure legs**, each verified to discriminate the patched
from the unpatched repo (negative controls run at construction time):
1. *value* — cleaned == `normalise(first evaluation)`; the pre-patch fresh,
   un-normalised `get_initial_for_field` call disagrees.
2. *bound initial* — cleaned == the real `BoundField.initial`
   (`Ensures(Result() == bound_initial(fs))`, §1's binding; the F2P test's own
   `cleaned == bf.initial`).
3. *effect / exactly-once* — the source is evaluated EXACTLY ONCE across the
   whole "clean, then read the bound initial" window. This is the
   `@cached_property` the model encodes as "the single first evaluation", and the
   reason the impl is granted NO permission to `fs.fresh_eval` (§2,
   permission-as-effect). Pre-patch evaluates it twice; leg 3 fires even on
   inputs where leg 1 agrees (stateless, sub-second-0 source).

**Inputs.** 100 000 Requires-satisfying inputs: 36 boundary cases first (the
exact F2P shape with its expected `datetime(2006, 10, 25, 14, 30, 46)` and
`cleaned == bf.initial` assertions; sub-second 0 / 1 / 123456 / 500000 / 999999;
stateful, stateless and non-callable sources; `TimeField`; the `datetime.min` /
`datetime.max` and `time.min` / `time.max` extremes; a large state step), then
seeded fuzz over the full datetime range x sub-second range x {DateTimeField,
TimeField} x {form-`initial`, field-`initial`} x {stateful, stateless,
non-callable}. The impl region is straight-line, so branch coverage is over
`normalise`'s two regimes (sub-second == 0 identity, sub-second > 0 strict
floor); both appear in the boundary set and their counts are reported in the
summary. The modeled input space is INFINITE, so this is sampling, not
exhaustive enumeration.

**Pinned seed: `SEED = 14631`** (module constant in `conformance_check.py`).
Exit 0 iff zero disagreements; a disagreement prints the input and both sides.
