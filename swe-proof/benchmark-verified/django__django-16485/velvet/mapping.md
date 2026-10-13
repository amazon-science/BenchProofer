# mapping.md — django__django-16485

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 39f83765e12b0e5d260b7939fc3fe281d879b279`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and records the
provenance of each modeled construct.

Repo file under change: `django/template/defaultfilters.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `numericDisplay (isWhole, p, intView, fracView)` | `floatformat(text, arg=-1)` — `django/template/defaultfilters.py:96` (the guard + branch at body lines 171–206) | the modeled changed function (numeric display filter), reduced to its branch-selection decision |
| `isWhole : Bool` | `not m`, where `m = int(d) - d` (`defaultfilters.py:167`) | "the value has no fractional part" — read-only input (R) |
| `p : Int` | `p = int(arg)` (`defaultfilters.py:162`) | the requested fractional-digit count — read-only input (R) |
| `intView : List Char` | the integer-rendering branch result `mark_safe(formats.number_format("%d" % int(d), 0, …))` (`defaultfilters.py:172–179`) | UNCHANGED pre-computable rendering — read-only input (R) |
| `fracView : List Char` | the fractional-rendering branch result `mark_safe(formats.number_format(number, abs(p), …))` (`defaultfilters.py:199–206`, the tail starting at line 181) | UNCHANGED pre-computable rendering — read-only input (R) |

The patched line is the dispatch guard at `defaultfilters.py:171`:
`if not m and p < 0:` → `if not m and p <= 0:`. Nothing else in the function
body changes; the two branch bodies (`intView`, `fracView` computations) are
byte-identical before and after the patch.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean value
domain and the Python repo types.

| repo reality | Lean carrier | bijection |
|---|---|---|
| `not m` (Python bool: `int(d) == d`, the value is integral) | `isWhole : Bool` | `True ↔ true`, `False ↔ false`. `m = int(d) - d` is the (possibly-negative) fractional remainder; `not m` is `True` iff `m == 0` iff `d` is a whole number. |
| `p` (Python `int`, `= int(arg)`) | `p : Int` | identity on integers; `p` may be negative, zero, or positive. `p < 0 ↔ p < 0`, `p <= 0 ↔ p ≤ 0`. |
| the integer-branch return value (a `SafeString`) | `intView : List Char` | the rendered string's characters ↔ `List Char`; `mark_safe` only sets the `SafeString` flag and does not alter character content the F2P test observes (identity on content). |
| the fractional-branch return value (a `SafeString`) | `fracView : List Char` | same character-content bijection as `intView`. |
| selecting a branch result and returning it | `out : List Char` | the returned `SafeString`'s characters ↔ `out`. The model abstracts the routine to its branch SELECTION; the two branch bodies are unchanged and modeled as opaque pre-computed inputs (see §3). |

`intView` / `fracView` are NOT axioms: they are unchanged sub-results of the
surrounding code, taken as plain read-only method inputs (the
django-11951 / django-12276 "abstracted-input-not-axiom" pattern, LESSONS.md).
Nothing is asserted about their value, so there is no callee contract to
validate. The one changed op is the function-under-change's own guard (modeled
deeply, never axiomatized — directive 7), so the bundle ships no axiom_check.py
and G-AX is a **skip** (canonical no-axiom path).

## 3. Construct provenance — branch selection, not callee contracts

The single behavioural change is the **guard** deciding which of two unchanged
renderings is emitted. The fix is `p < 0` → `p <= 0` in
`if not m and p < 0:` (`defaultfilters.py:171`).

Why this is the whole bug (verified on the real repo, both with and without the
patch — see conformance_check.py, the G-CONF differential check):

- When the value is whole (`not m` true) and `p <= 0`, the integer-rendering
  branch (`intView`) is the correct output: it formats `"%d" % int(d)` with
  zero fractional positions, which never raises and yields the bare integer.
- The fractional-rendering branch (`fracView`, the tail from line 181) computes
  `prec = abs(p) + units + 1`. For a whole value with `p == 0` and `units == 1`
  (e.g. `Decimal("0.00")`, whose `as_tuple()` digits collapse to `(0,)`),
  `prec` computes to `0`, and `Context(prec=0)` raises
  `ValueError: valid range for prec is [1, MAX_PREC]` — the crash the issue
  reports for `floatformat("0.00", 0)` and `floatformat(Decimal("0.00"), 0)`.
- The pre-patch guard `p < 0` routed whole values at `p == 0` into the
  fractional branch, triggering the crash. Widening to `p <= 0` routes the
  `p == 0` whole-value case into the safe integer branch.

`intView` and `fracView` model the two branch bodies as their character
content. They are unchanged across the patch, so they are taken as read-only
inputs (R), not axioms — there is no callee whose contract the proof consumes.
G-CONF (§4) re-executes the REAL patched `floatformat` to confirm that the
modeled selection (`isWhole && p ≤ 0`) reproduces the real branch choice, with
`intView`/`fracView` resolved to the real branch outputs.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`16485`** so the
consumer-side verdict (§11.3) is reproducible. The shadow it builds is the R/I
transliteration of `numericDisplay`'s selection
(`out = intView if (isWhole and p <= 0) else fracView`); the oracle is the real
patched `floatformat` at base_commit, with `intView`/`fracView` resolved to the
two real branch outputs as observed on each fuzzed input. The G-CONF inputs are
`(text, arg)` pairs that drive `floatformat` across whole/fractional values and
negative/zero/positive `p`, plus the legacy suffix forms.
