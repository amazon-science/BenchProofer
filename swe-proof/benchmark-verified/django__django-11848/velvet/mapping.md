# mapping.md — django__django-11848

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = f0adf3b9b7a19cdee05368ff0c0c2d087f011180`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and records
callee provenance. There are **no axioms and no A-references** in this bundle —
see §3.

Repo file under change: `django/utils/http.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `resolveAbbreviatedYear (yy : Int) (cur : Int)` | the abbreviated-year resolution block inside `parse_http_date` — `django/utils/http.py:178-185` (the `if year < 100:` body) | the modeled changed computation |
| `resolvedFullYear (yy cur : Int)` | the post-patch arithmetic that resolves a two-digit year relative to the current year (`django/utils/http.py:179-185` post-patch) | pure spec: the resolved full year |
| `cur` (the `cur : Int` parameter) | `datetime.datetime.utcnow().year` — read at `django/utils/http.py:179` post-patch | the current calendar year, read from the environment |
| `yy` (the `yy : Int` parameter) | `year = int(m.group('year'))` when `year < 100` — `django/utils/http.py:177-178` | the parsed two-digit year |

The modeled function is `parse_http_date` (`django/utils/http.py:158`), but the
ONLY behavior the gold patch changes is the abbreviated-year resolution; the
date-string parsing, month/day/time extraction, `datetime` construction, and
`calendar.timegm` epoch conversion are all unchanged and surround the modeled
block. The spec isolates the changed arithmetic. G-CONF (§4) drives the WHOLE
real `parse_http_date` end-to-end through an RFC850 date string so the modeled
arithmetic is exercised inside its true caller, with `utcnow()` mocked to pin
`cur` (exactly the gold test_patch's mechanism).

The pre-patch repo code the change removes (refinement audit only): the fixed
two-digit cutoff `if year < 70: year += 2000 else: year += 1900`
(`http.py:179-182` pre-patch).

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4) uses to translate values between the Lean value
domain and the Python repo types. A wrong entry surfaces as spurious G-CONF
disagreements.

| repo reality | Lean carrier | bijection |
|---|---|---|
| the parsed two-digit year `year` (an `int` in `0..99`) | `Int` (`yy`, with `require 0 ≤ yy ∧ yy ≤ 99`) | identity on integers; the RFC850 regex `(?P<year>\d{2})` guarantees `0..99` |
| `datetime.datetime.utcnow().year` (a positive `int`) | `Int` (`cur`, with `require 0 ≤ cur`) | identity on integers; a calendar year is non-negative |
| the resolved full year `year` (an `int`) | `Int` (`out`) | identity on integers |
| Python `//` / `%` on the non-negative operands here | Lean `Int` `/` / `%` | on the non-negative `cur` used here, Python and Lean `%`/`/` agree (both give the Euclidean residue `0 ≤ cur % 100 < 100`); `cur - cur % 100` is the hundreds floor in both |

Python integers are unbounded; Lean `Int` is unbounded — exact match, no
overflow concern. `Int` (not `Nat`) is the carrier because the patch's
intermediate `year - (current_year % 100)` and `current_century - 100` are
written as signed subtractions whose faithful model needs signed arithmetic
(e.g. `yy + century - 100` and the comparison `yy - cc > 50` must not truncate
at zero).

## 3. Callees / axioms / references — none

- **No consumed axioms.** The changed block calls no repo/stdlib function whose
  contract the proof must assume. `datetime.datetime.utcnow().year` is an
  environmental *read*, not a callee with a contract to axiomatize: it is
  modeled as the free input `cur`, about which the spec assumes **nothing**
  beyond `0 ≤ cur` (a calendar year is non-negative). The contract therefore
  holds for *every* reference year — no over-claim (SPEC_GUIDE §0.7/§0.8).
- **No A-references.** The changed arithmetic is modeled deeply by
  `resolvedFullYear`; there is no deep model standing in for a separate
  unchanged callee. Its fidelity to the real patched behavior is checked by
  **G-CONF** end-to-end against `parse_http_date`, not by G-AX.
- Consequently this bundle ships **no `axiom_check.py`**; G-AX is `skip`
  (gates.py `gate_ax`: "no axiom_check.py" → skip).

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`11848`** so the
consumer-side verdict is reproducible. It drives the REAL `parse_http_date`
(gold applied by the harness) through an RFC850 date string carrying the
two-digit year `yy`, with `datetime.datetime.utcnow` mocked to a controlled
reference year `cur` (the gold test_patch's exact mechanism), and compares the
resolved full year against the R/I shadow of `resolveAbbreviatedYear`. The
reference year is fuzzed over `cur ∈ [200, 9900]` so the resolved full year
stays a valid `datetime` year (`1..9999`) while both branches of the `>50` rule
are exercised at every two-digit residue; `yy ∈ [0, 99]`. Boundary cases (the
seven F2P matrix rows and the cutoff edges 49/50/51/52, 69/70/71) are checked
first.
