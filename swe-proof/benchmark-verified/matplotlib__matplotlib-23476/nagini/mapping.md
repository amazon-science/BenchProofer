# mapping.md — matplotlib__matplotlib-23476

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 33a0599711d26dc2b79f851c6daed4947df7c167`, states the type
abstraction, and records that there is no axiomatized callee (the change is pure
mapping logic modeled deeply, so there is nothing for G-AX to check beyond the
deep-model fidelity validated by `axiom_check.py`).

Repo file under change: `lib/matplotlib/figure.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `normalize_state_dpi(state, reference_present, reference_value)` | the DPI-reconciliation step added inside `Figure.__getstate__` — `lib/matplotlib/figure.py:3015` (the added hunk between body lines 3024 and 3026) | the modeled changed behavior: the live-resolution entry of the serialisable state is set to the original-resolution record when present, else left at the recorded value |
| `key_dpi()` | the state key `"_dpi"` (the figure's live DPI; `Figure._dpi` / `Figure.dpi` property, `lib/matplotlib/figure.py:2090,2576-2597`) | pure spec: the dpi entry name (model vocabulary: the "dpi entry") |
| `key_reference()` | the state key `"_original_dpi"` (`Figure._original_dpi`, set by the canvas at `lib/matplotlib/backend_bases.py:1656`) | pure spec: the reference-dpi entry name (model vocabulary: the "reference entry") |
| `state` (`Dict[int, int]`) | the figure state mapping `state` — `super().__getstate__()` returns `self.__dict__.copy()` (`lib/matplotlib/artist.py:186-191`), a `dict` mutated in place by `__getstate__` | the serialisable state mapping |

The pre-patch repo behavior the change fixes (for the refinement audit, not
referenced from the consumer spec view): `__getstate__` returned `state` with
`state["_dpi"]` left at the *scaled* value `self._dpi`. After a pixel-ratio
scaling, `_dpi = ratio * _original_dpi` (`backend_bases.py:2104-2105`,
`_set_device_pixel_ratio`), so the serialized `_dpi` carried the scaled
resolution. On unpickle, a fresh canvas re-records `_original_dpi = self.dpi`
(the scaled value) and re-scales, compounding the factor on every cycle
(the doubling / `OverflowError` of the issue).

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| the state mapping `state: dict` (`str` keys → arbitrary pickled values) | `Dict[int, int]` from an entry-name token to a value token | only the two entry names `"_dpi"` / `"_original_dpi"` and their values are touched/observed; every other entry passes through untouched. `key_dpi() = 0 ↔ "_dpi"`, `key_reference() = 1 ↔ "_original_dpi"` (distinct tokens, as the two `str` keys are distinct). `k in state` ↔ `key in state`; `state[k]` ↔ `state[key]`; in-place reassignment `state[k] = v` ↔ `state["..."] = v`. |
| the DPI values (`float`, e.g. `42.0`, `294.0`) | `int` token | the modeled behavior SELECTS one of two stored DPI values by entry membership (`state.get('_original_dpi', state['_dpi'])`); it never computes on the value. The tested behavior (`fig2.dpi == 42`, i.e. the original value is the one recorded, not the scaled `42*7`) is an EQUALITY of the selected value, precision-independent. So an `int` token faithfully carries the selection; no real `float` is needed (SPEC_GUIDE §2 "float where the bug is NOT about precision → int"). |
| `state.get('_original_dpi', state['_dpi'])` (dict `.get` with default) | the deep `if key_reference() in state: ... else: state[key_dpi()] = state[key_dpi()]` | `dict.get(k, default)` returns `state[k]` when `k in state` else `default`; the assignment target is always `state["_dpi"]`. The `else` self-assignment `state[key_dpi()] = state[key_dpi()]` mirrors the `default = state['_dpi']` branch (a no-op on the value). Validated against real Python `dict.get` by `axiom_check.py`. |

`str` keys are modeled as distinct integer tokens because (a) Nagini bans `str`
indexing and (b) only key *identity* (membership + equality of the two relevant
keys) is observed, never key content.

## 3. Callee provenance

None. The change adds no library call: it is a `dict.get`-with-default selection
plus an in-place assignment — primitive mapping operations modeled deeply in the
impl region. There is therefore **no `@ContractOnly` axiom** (the `axioms`
region is empty). `axiom_check.py` instead validates the *deep model's*
selection semantics against real Python `dict` (the `.get(k, default)` /
membership / assignment behavior the model encodes) — an A-reference check, not
a consumed axiom (refinement.md).

## 4. The `reference_present` / `reference_value` entry-state parameters

`__getstate__` reads the entry membership/value of `"_original_dpi"` BEFORE
writing `"_dpi"`. The model binds those two pre-state facts as parameters
(`reference_present == (key_reference() in state)`,
`reference_value == state[key_reference()]` when present) so the selection
postcondition gates on the genuine entry record rather than on a membership
query against the mutated state — exactly the established
`component_present` idiom (cf. `tasks/django__django-12713`). This keeps the
postcondition grounded in the input (SPEC_GUIDE directive 8): an implementation
must *produce* the original value, it cannot discharge the clause vacuously.
Since `"_original_dpi"` is never written by `__getstate__`, its entry record at
exit equals its record at entry, so these parameters faithfully describe both
the pre- and the post-state of that key.

## 5. Conformance check (G-CONF)

`conformance_check.py` runs the impl region verbatim (contracts stripped)
against the real patched `Figure.__getstate__` in-container, lowering the
token state per §2 (`0 ↔ "_dpi"`, `1 ↔ "_original_dpi"`, other key tokens
`k ↔ "_conf_tok_<k>"` attribute entries; int value tokens ↔ exact `float`s).
Inputs: boundary cases + 100000 fuzz states, **pinned seed 23476**.

## 6. Termination obligation

The modeled operation is a single loop-free `dict.get`-with-default selection
plus one in-place assignment inside `__getstate__`: the real code always
returns. Nagini checks partial correctness by default, so without a
termination obligation a same-spec implementation that diverges (e.g.
`while True: pass`) satisfies every `Ensures` vacuously while its real
counterpart would hang serialisation (pickling) forever — the F2P round-trip
would never complete. `Requires(MustTerminate(2))` pins totality. It adds no
behaviour beyond what the real code already has (the real operation is
straight-line and total on the whole precondition domain), so it cannot
exclude a correct implementation.
