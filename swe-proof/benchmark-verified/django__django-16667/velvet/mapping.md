# mapping.md — django__django-16667

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 02c356f2f3945b8075735d485c3cf48cad991011`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and gives
the provenance of the modeled callee.

Repo file under change: `django/forms/widgets.py`
(class `SelectDateWidget`, method `value_from_datadict`, lines 1149-1165).

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `method dateComponentsText (y m d : List Char) (outcome : ConstructOutcome) → Except DateErr (List Char)` | the all-three-present inner branch of `SelectDateWidget.value_from_datadict` — `django/forms/widgets.py:1158-1164` (the `try / except ValueError / return`-fallthrough block) | the **modeled changed routing**: given the three textual components and the outcome of handing them to the calendar machinery, produce the text this branch returns. This is the only place the patch edits. |
| `ConstructOutcome` (inductive: `rendered s` / `notCalendar` / `unrepresentable`) | the three observable results of `datetime.date(int(y),int(m),int(d))` then `date_value.strftime(input_format)` — `widgets.py:1159,1164` | a **free input** to the method: the three mutually-exclusive outcomes of the UNCHANGED construct-and-format callee. Modeled as an input rather than a contracted axiom (directive 7 — see §3). |
| `dateText (y m d : List Char) (o : ConstructOutcome) : Except DateErr (List Char)` (pure region) | the post-patch routing of those three outcomes to a return value — `widgets.py:1158-1164` post-patch | **deep model (I)** of the CHANGED op: maps each outcome to the returned text. The `unrepresentable → Except.ok allZeroTriple` leg is the single behavioural change. |
| `pseudoTriple (y m d : List Char)` (pure region) | `"%s-%s-%s" % (y or 0, m or 0, d or 0)` — `widgets.py:1163` | the ValueError fallback rendering, per-component empty→`'0'`. |
| `orZero (x : List Char)` (pure region) | the `x or 0` per-component coercion inside the `%`-format — `widgets.py:1163` | empty component shows as the single digit `0`; any other component verbatim. |
| `allZeroTriple` (pure region) | the constant string literal `"0-0-0"` — `widgets.py` post-patch (the `except OverflowError` leg) | the constant all-zero triple the OverflowError leg returns; the downstream `DateField.to_python`/`date_re` rejects it as a non-date. |
| `DateErr` (inductive: `valueEscaped`) | the absence of a return — an exception that escapes `value_from_datadict` uncaught | models the pre-patch crash: `Except.error .valueEscaped` ⇔ an `OverflowError` propagating out of the method. A correct result is always `Except.ok`. |

The outer framing of `value_from_datadict` the patch does NOT touch
(`y = data.get(self.year_field % name)` etc., the `y == m == d == ""` → `None`
short-circuit, the all-present `if y is not None and m is not None and d is not
None`, and the trailing `return data.get(name)`) is unchanged between pre- and
post-patch and is identical context, not modeled (refinement.md §B). The patch
hunk lives entirely inside the all-present try/except, which is exactly what
`dateComponentsText` models.

`input_format` (`get_format("DATE_INPUT_FORMATS")[0]` run through
`formats.sanitize_strftime_format`) affects only the `rendered` payload (the
`strftime` text). The changed behaviour does not touch it, and the F2P overflow
tests never reach it; it is folded into the opaque `rendered s` outcome.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

Table G-CONF (§4.1) and G-AX use to translate values between the Lean value
domain and the Python repo types.

| repo reality | Lean carrier | bijection |
|---|---|---|
| `y`, `m`, `d` — the raw `str` values pulled from the submitted data on the all-present branch (not `None`) | `List Char` (`y`, `m`, `d`) | Python `str` ↔ Lean `List Char`, code-point for code-point (`ch ↔ Char.ofNat (ord ch)`). Empty `str` ↔ `[]`. |
| the value the branch produces (a `str`: a `strftime` result, a pseudo-ISO triple, or `"0-0-0"`); or an exception escaping uncaught | `Except DateErr (List Char)` | a returned `str` `s` ↔ `Except.ok s.toList`; an `OverflowError` escaping the method uncaught ↔ `Except.error .valueEscaped`. |
| `datetime.date(int(y),int(m),int(d))` succeeds, then `.strftime(input_format)` | `ConstructOutcome.rendered s` | `s` ↔ the `str` `date_value.strftime(input_format)` returns. Opaque payload — its exact value is not pinned (it is the unchanged callee's job). |
| that construction raises `ValueError` (an `int()` parse failure on an empty/non-numeric component, OR an in-range `(y,m,d)` that is not a valid calendar date) | `ConstructOutcome.notCalendar` | carries no payload; the routing rebuilds the fallback from the supplied `y m d` via `pseudoTriple`. |
| that construction raises `OverflowError` (a parsed component outside the signed C-`long` range) | `ConstructOutcome.unrepresentable` | carries no payload; the routing supplies the constant `allZeroTriple`. |

The pre-/post-patch difference is entirely in `dateText`'s `unrepresentable`
leg: post-patch returns `Except.ok allZeroTriple`; pre-patch lets the
`OverflowError` escape — `Except.error .valueEscaped` (the crash). G-DIFF
confirms the prepatch fails exactly on `ensures outcome = .unrepresentable →
out = Except.ok allZeroTriple` and `ensures ∃ r, out = Except.ok r`.

## 3. Callee provenance — `ConstructOutcome` is a free input (A-reference), not a consumed axiom

The construct-and-format step — `datetime.date(int(y),int(m),int(d))` then, on
success, `date_value.strftime(input_format)` — is **unchanged** by the patch;
only the handling of its `OverflowError` outcome changes. Per directive 7 it is
the weakest possible modeling: instead of a module-level `axiom` pinning its
behaviour, the method takes the construction outcome as a **free input**
(`outcome : ConstructOutcome`). The postconditions hold for *every* value of
`outcome`, so the callee is owed no contract at all — strictly weaker than any
concrete implementation. There is no consumed axiom and no dead axiom; the
changed routing is modeled **deeply** in `dateText` (an A-reference + I).

What G-AX must still validate is that the three-way `ConstructOutcome` partition
is **exhaustive and well-defined** over the real callee — i.e. that the real
`datetime.date(int(y),int(m),int(d))` always lands in exactly one of the three
shapes the model enumerates, so no fourth outcome the routing fails to handle is
possible.

### 3.1 The three-way partition (the A-reference G-AX checks)

Verified empirically against the real CPython `datetime` (axiom_check.py;
300 000-triple fuzz, 0 mismatches against the predicate below):

- **`unrepresentable` (OverflowError)** ⇔ every component parses as an `int`
  AND at least one parsed value lies outside the signed C-`long` range
  `[-2^31, 2^31-1] = [-2147483648, 2147483647]`. The overflow is raised during
  `date()`'s C-level argument conversion, *after* the `int()` parse but *before*
  calendar validation. (Boundary: `int("2147483648")` → overflow;
  `int("2147483647")` → in range → ValueError as a calendar year; symmetrically
  `-2147483649` → overflow, `-2147483648` → ValueError.)
- **`notCalendar` (ValueError)** ⇔ NOT `unrepresentable` AND (`int()` rejects a
  component — empty or non-numeric — OR the in-range `(year, month, day)` is not
  a valid calendar date: `year ∉ 1..9999`, `month ∉ 1..12`, or `day` outside
  the month's length). The `int()` parse happens first and left-to-right, so a
  non-numeric component yields ValueError even if another component would
  overflow.
- **`rendered s` (constructed)** ⇔ otherwise: a valid calendar date, formatted
  by `strftime` to the `str` `s`.

**Soundness check (G-AX):** `axiom_check.py` runs the real
`datetime.date(int(y),int(m),int(d))` (matching the widget's exact call) on
boundary inputs (the C-`long` edges `±2^31`, `±sys.maxsize`, the
`year`/`month`/`day` calendar edges, empty/non-numeric strings, the F2P
`sys.maxsize+1` triple, the problem-statement `1234567821345678` triple) plus
≥200 000 randomized fuzz triples, and asserts the real outcome is **always**
exactly one of the three modeled shapes AND matches the documented predicate
(so the partition is total and `ConstructOutcome` admits no fourth case).
stdlib-only (`datetime` is the same module the gold patch's call uses). Exit 0
iff sound.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`16667`** so the
consumer-side verdict is reproducible. The R/I shadow it builds transliterates
`dateText` (the I-tagged changed routing) and `pseudoTriple`/`orZero`/
`allZeroTriple` to Python, and leaves the construct-and-format callee as the
**real** `datetime.date`/`int`/`strftime` computation (A-reference → run real
callee, not a re-implementation). It bridges I/O via the §2 bijection
(`str ↔ List Char`; widget field templates `%s_year`/`%s_month`/`%s_day`,
`widgets.py:1019-1021`) and diffs the shadow's `value_from_datadict` return
value against the **patched** `value_from_datadict`'s behaviour over ≥10⁵ fuzzed
`(y, m, d)` string triples (boundary + random). Exit 0 iff zero disagreements.
`conf_skip=false`: the impl region computes its result via I-tagged routing over
R-refined inputs, so the shadow is a genuine R/I differential, not all-A.
