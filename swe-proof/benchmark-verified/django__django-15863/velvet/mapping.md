# mapping.md — django__django-15863

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 37c5b8c07be104fd5288cd87f101e48cb7a40298`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and records the
modeled regime. This bundle is **axiom-free** — there is no callee provenance
section because no callee is axiomatized.

Repo file under change: `django/template/defaultfilters.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `floatFormat (intDigits fracDigits : List Char) (p : Nat)` | `floatformat(text, arg)` — `django/template/defaultfilters.py:96` (changed line 154) | the modeled changed function (the template `floatformat` filter) |
| `renderFixed (intDigits fracDigits : List Char) (p : Nat)` | the post-`d` rendering pipeline of `floatformat` (`defaultfilters.py:170-189` post-patch): `quantize`/`as_tuple`/zero-pad/`.`-insert/`number_format`, collapsed to identity in the modeled regime | pure spec: fixed-point render of a numeral to `p` places |
| `pad_tail_step` | the `while len(digits) <= abs(exponent): digits.append("0")` zero-pad loop (`defaultfilters.py:185-186`) | pure lemma: one tail zero-pad step |

The edit itself (`defaultfilters.py:154`) changes `input_val = repr(text)` to
`input_val = str(text)` — the seed of `Decimal(input_val)`. Its only observable
effect is whether the digits feeding the render are the numeral's exact digits
(str path) or a binary-float round-trip's truncated digits (repr path, via the
`InvalidOperation → Decimal(str(float(text)))` fallback). The model captures the
fixed behaviour: the fractional run is the numeral's verbatim `fracDigits`.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection + regime

This is the table G-CONF (§4.1) uses to translate values between the Lean value
domain and the Python repo types. A wrong entry surfaces as spurious G-CONF
disagreements.

| repo reality | Lean carrier | bijection |
|---|---|---|
| a non-negative decimal numeral `d = Decimal(str(text))` | `(intDigits, fracDigits) : List Char × List Char` | `str(d)` split at `.` → (integer-digit run, fractional-digit run); each digit char ↔ `Char`; empty fractional run ↔ `[]`. G-CONF bridges by `str(Decimal(...))`. |
| the precision `p = int(arg)` | `p : Nat` | identity on non-negative ints. |
| `number_format(number, abs(p), use_l10n=True, force_grouping=False)` (`defaultfilters.py:190`) | identity on character content (omitted) | under the default (en) locale with no grouping, `number_format` reproduces `number` verbatim — it neither regroups nor relocalizes the digit string. Identity on `List Char`. |
| `str(text)` / `Decimal(...)` parse | digit runs above | the *fix* makes this exact for `Decimal` inputs; modeled as the verbatim digits. |

**Modeled regime (the precondition envelope of `floatFormat`):** a non-negative
numeral (`intDigits ≠ []`, all digit chars), `p ≥ 1`, and `p ≥ |fracDigits|`
(the requested precision keeps or exceeds the numeral's own fractional length, so
`quantize`/`ROUND_HALF_UP` rounds nothing away), default locale, no grouping.
This is exactly the regime the FAIL_TO_PASS case
`floatformat(Decimal("123456.123456789012345678901"), 21)` and the issue MWE
`floatformat(Decimal("42.12345678901234567890"), 20)` occupy. Outside this regime
(rounding, negative `p` with integral value, scientific notation, grouping/`g`/`u`
suffixes, NaN/inf) the function does more than `renderFixed`; G-CONF restricts its
differential to the regime via `in_regime(...)` and counts the skips.

Lean `List Char` indexing is total and sound; the carrier is `List Char` because
the operation is per-digit.

## 3. No axioms / no callees modeled

There are no `axiom` declarations and no `:|` callee stubs in `Solution.lean`.
The changed behavior is the exact-digit identity, modeled directly by
`renderFixed`; the surrounding pipeline (`Decimal`, `quantize`, `number_format`)
is collapsed to identity *within the proven regime* and that collapse is checked
end-to-end against the real patched `floatformat` by G-CONF — not assumed by an
axiom. Hence `axiom_check.py` is absent and G-AX skips.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`15863`** so the
consumer-side verdict (§11.3) is reproducible. The R/I shadow transliterates
`renderFixed`/the `floatFormat` pad loop to Python and compares against the real
patched `floatformat` (the harness applies `patch.diff` first), over ≥10⁵
regime-restricted fuzzed numerals plus the F2P / MWE boundary cases.
