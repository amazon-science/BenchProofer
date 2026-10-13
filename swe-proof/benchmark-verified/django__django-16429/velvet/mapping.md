# mapping.md — django__django-16429

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 6c86495bcee22eac19d7fb040b2988b830707cbd`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and records the
callee provenance.

Repo file under change: `django/utils/timesince.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `buildShiftedReference (base) (years) (months)` | the `pivot = datetime.datetime(...)` construction inside `timesince()` — `django/utils/timesince.py:87-102` (the `if years or months:` branch) | the modeled changed expression: build the shifted reference instant |
| `Instant` (structure) | `datetime.datetime` — the touched fields `(year, month, day, hour, minute, second, tzinfo)` | the carrier of an instant; `zone` ↔ `tzinfo` |
| `shiftReference` (pure deep model) | the body of the `datetime.datetime(pivot_year, pivot_month, min(MONTHS_DAYS[..], d.day), d.hour, d.minute, d.second, tzinfo=d.tzinfo)` constructor (post-patch) | pure spec: the reference instant produced from `d`, `years`, `months` |
| `monthLen` | `MONTHS_DAYS = (31,28,31,30,31,30,31,31,30,31,30,31)` — `django/utils/timesince.py:25` | the per-month day count consulted by `min(MONTHS_DAYS[pivot_month-1], d.day)` |

No symbol is axiomatized: the construction reads only the components of `d` and
the `years`/`months` offsets; `datetime.datetime(...)` is the language
constructor, not a foreign callee whose behavior the proof must assume
(refinement.md §C). `MONTHS_DAYS` is concrete repo data, transliterated into
`monthLen`.

The pre-patch repo expression the change fixes (refinement audit only, not in
the consumer spec view): the same `datetime.datetime(...)` call **without** the
`tzinfo=d.tzinfo` keyword (`timesince.py:93-100` @ base_commit), which produces
a tz-naive instant from a tz-aware `d`.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean value
domain and the Python repo types. A wrong entry surfaces as spurious G-CONF
disagreements.

| repo reality | Lean carrier | bijection |
|---|---|---|
| a `datetime.datetime` instance `d` | `Instant` | `d.year ↔ .y`, `d.month ↔ .mo`, `d.day ↔ .d`, `d.hour ↔ .h`, `d.minute ↔ .mi`, `d.second ↔ .s`; `d.tzinfo ↔ .zone` (see next row). Microseconds are not touched by the construction and are omitted. |
| `d.tzinfo` (a `tzinfo` object or `None`) | `Option Nat` | `None ↔ none` (a naive/floating instant); a non-`None` `tzinfo` ↔ `some k`, where `k` is a stable id for that designation. The construction never inspects the *internals* of `tzinfo` — it only either drops it (`none`) or carries the exact same object through (`some k` with the same `k`). The bijection therefore only needs to preserve **identity/`None`-ness**, which `Option Nat` captures: G-CONF maps each distinct `tzinfo` object to a distinct `k` and `None` to `none`. |
| `years`, `months` (the `divmod(total_months, 12)` results) | `Nat`, `Nat` | direct; `months = total_months % 12 ∈ 0..11` (the `require months ≤ 11`); this site (`if years or months:`) is only entered when `years or months` is truthy (the `require 0 < years ∨ 0 < months`). `d.month ∈ 1..12` (`require 1 ≤ base.mo ∧ base.mo ≤ 12`). |
| `MONTHS_DAYS[pivot_month - 1]` (0-indexed tuple lookup) | `monthLen pivot_month` (1-indexed function) | `MONTHS_DAYS[m-1] = monthLen m` for `m ∈ 1..12`; G-CONF checks the table transliteration directly. |
| `min(MONTHS_DAYS[pivot_month-1], d.day)` | `min (monthLen pm') base.d` | `min` over `Nat` ↔ Python `min` over the two non-negative ints. |
| month carry: `if pivot_month > 12: pivot_month -= 12; pivot_year += 1` | `pm' = if pm>12 then pm-12 else pm`, `py' = if pm>12 then py+1 else py` | identical arithmetic; `pm = d.month + months ≤ 12 + 11 = 23`, so a single `-12` normalizes into 1..12. |

The construction is per-field and total; no indexing-soundness workaround is
needed.

## 3. Callee provenance

**None.** There is no unchanged foreign callee in the modeled expression: the
shifted reference is built field-by-field from `d`, `years`, `months`, and the
concrete `MONTHS_DAYS` table. `datetime.datetime(...)` is the value constructor
(modeled by the `Instant` structure literal), not an axiomatized callee.
Therefore:

* `axioms` region empty; `meta.json axioms = []`, `deep_model_references = []`.
* **G-AX skips** (no `axiom_check.py`): there is no axiom or deep-model
  reference whose soundness must be checked against a real callee.

The whole mechanical burden falls on **G-CONF** (refinement fidelity of the R/I
legs) and **G-RESOLVE** (the gold patch resolves).

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`16429`** so the
consumer-side verdict is reproducible. The R/I shadow it builds transliterates
`shiftReference`/`monthLen` (R/I-tagged ops) to Python over real
`datetime.datetime` values and compares against `patch.diff`'s behaviour (the
patched construction read out of `timesince`), including tz-aware sources where
the pre-patch code raised `TypeError`.
