# mapping.md — django__django-14792

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = d89f976bddb49fb168334960acc8979c3de991fa`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and records
callee provenance.

Repo file under change: `django/utils/timezone.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `resolveZoneLabel (shortLabel : Option (List Char)) (fullLabel : List Char)` | `_get_timezone_name(timezone)` — `django/utils/timezone.py:74` | the modeled changed function: pick the public label for a time-zone object |
| `shortLabel : Option (List Char)` | `timezone.tzname(None)` (the short/abbreviation label of the tzinfo) | read-only input: the abbreviation label, which may be absent (`None`) or empty |
| `fullLabel : List Char` | `str(timezone)` (the full textual name/key of the tzinfo) | read-only input: the always-present full label |
| `out : List Char` | the `str` returned by `_get_timezone_name` | result: the selected public label |

The function under change takes one argument — a `tzinfo` object — and reads
two textual labels off it. Per the §2 bijection, that object is presented to
the Lean model as exactly those two observable labels (`shortLabel`,
`fullLabel`); the model then performs the *selection* (the changed logic). This
is the same shape as the exemplar django__django-14155 (a `ResolverMatch`
presented as its observable-field record): the observations form the input
bijection (R-refinement), they are **not** consumed axioms about a callee.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean value
domain and the real repo types. A wrong entry surfaces as spurious G-CONF
disagreements.

| repo reality | Lean carrier | bijection |
|---|---|---|
| a `tzinfo` object `tz` (the `timezone` argument) | the pair `(shortLabel, fullLabel)` | `tz` ↔ `(observe_short tz, observe_full tz)` where `observe_short tz = tz.tzname(None)` and `observe_full tz = str(tz)` |
| `tz.tzname(None)` — a `str` or `None` | `shortLabel : Option (List Char)` | `None` ↔ `none`; a `str s` ↔ `some s.toList`; empty `str ''` ↔ `some []` |
| `str(tz)` — always a `str` | `fullLabel : List Char` | `s` ↔ `s.toList`; `len(s)` ↔ `.length`; empty `str` ↔ `[]` |
| Python truthiness of a `str`/`None` (the `or` operator's test) | `s ≠ []` for `some s`; `none` and `some []` are falsy | a Python `str` is truthy iff non-empty; `None` is falsy. So `shortLabel` is "present and non-empty" iff it is `some s` with `s ≠ []`. |
| the returned `str` | `out : List Char` | `out` ↔ `"".join(out)` |

Lean `String`/`List Char` is total and sound; the carrier is `List Char`
because the only property the selection inspects is emptiness (Python
truthiness of a string) — character content passes through unchanged.

## 3. Callee provenance

**No consumed axioms; no deep-model references.** The two callees
`tz.tzname(None)` and `str(tz)` are *not* axiomatized: the proof relies on no
property of them beyond "they produce the two label values," which is precisely
the input bijection (§2, R-refinement). They are the observation functions that
present the `tzinfo` object to the model, exactly as `m._func_path`, `m.url_name`
etc. present a `ResolverMatch` in django__django-14155 (a zero-axiom bundle).

Consequently `meta.json` carries `axioms: []`, `deep_model_references: []`,
there is **no `axiom_check.py`**, and **G-AX skips** (no axioms to check). The
selection logic is the entire changed behavior and is fully transliterable
(R/I), so `conf_skip = false` and G-CONF is the meaningful differential gate.

### 3.1 Why `tzname(None)` is the discriminator (provenance of the corpus)
Observed in-container (the prebuilt instance image, Python 3.6 + pytz):

| `tz` | `tz.tzname(None)` | `str(tz)` | desired result |
|---|---|---|---|
| `datetime.timezone(timedelta(hours=10))` | `'UTC+10:00'` | `'UTC+10:00'` | `'UTC+10:00'` |
| `datetime.timezone(timedelta(hours=10), name='Etc/GMT-10')` | `'Etc/GMT-10'` | `'Etc/GMT-10'` | `'Etc/GMT-10'` |
| `pytz.timezone('Europe/Madrid')` | `'Europe/Madrid'` | `'Europe/Madrid'` | `'Europe/Madrid'` |
| `pytz.timezone('Etc/GMT-10')` | `'+10'` | `'Etc/GMT-10'` | `'+10'` |

The last row is the discriminating case: the short label (`'+10'`) differs from
the full label (`'Etc/GMT-10'`) and is non-empty, so the desired result is the
short label. The pre-patch behavior (always the full label) diverges here —
this is exactly what the F2P tests observe (`Solution_prepatch.lean` fails the
"short label wins when non-empty" clause). For `datetime.timezone` the two
labels always coincide, so only the pytz (and zoneinfo, when present) fixed-offset
zones exhibit the divergence; the G-CONF corpus includes them.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`14792`** so the
consumer-side verdict is reproducible. The R/I shadow transliterates the
`resolveZoneLabel` selection (`none → full`, `some s → if s≠[] then s else full`)
to Python and bridges the input `tzinfo` via the §2 observations
(`tz.tzname(None)`, `str(tz)`). There are no A-tagged callees to leave as real.
