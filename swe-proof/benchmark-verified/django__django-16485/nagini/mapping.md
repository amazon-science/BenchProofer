# mapping.md — django__django-16485

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 39f83765e12b0e5d260b7939fc3fe281d879b279`, states the type
abstraction, and gives the provenance of the deep-model reference (the
unchanged localisation callee).

Repo file under change: `django/template/defaultfilters.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `format_value(int_value, frac_zero, p)` | `floatformat(text, arg=-1)` — `django/template/defaultfilters.py:96` (the branch at body line 171 and the early-return at 171-179 vs. the decimal path 181-206) | the modeled changed function (numeric display filter), restricted to the branch the patch touches |
| `int_render(n)` / `digits_acc(n, acc)` | `"%d" % (int(d))` (`defaultfilters.py:175`) — the bare integer string of the early-return | pure spec: bare integer rendering as decimal-digit code points |
| `rendered(int_value, frac_zero, p)` | the value handed to `formats.number_format` in each branch: the bare integer string (175) vs. the assembled `number = "".join(reversed(digits))` (198) | pure spec: the core display string selected by the branch |
| `zeros_seq(count)` | the fractional digit field of the decimal-path string (the `digits`/`.`-bearing assembly, 191-198) | pure spec: the `|p|`-wide fractional placeholder run (a faithful skeleton of the separator-bearing core) |
| `formats.number_format` *(A-reference, not consumed)* | `django.utils.formats.number_format` — `django/utils/formats.py:172` → `django.utils.numberformat.format` (`numberformat.py:7`) | unchanged localisation/grouping callee invoked in BOTH branches (175-179, 200-205); digit-content preserving on the bare integer string |

The bound variables of the real `floatformat`:
- `int_value` ↔ `int(d)` where `d = Decimal(str(text))` (`defaultfilters.py:154-155,175`).
- `frac_zero` ↔ `not m`, where `m = int(d) - d` (`defaultfilters.py:167`); `frac_zero == True` ⟺ the value is exactly integral.
- `p` ↔ `p = int(arg)` (`defaultfilters.py:162`), the requested decimal places.

The single changed token at `base_commit:171` is the comparison operator in the
early-return guard `if not m and p < 0:` (decimal path otherwise). The
specification phrases the desired branch outcome, not the operator edit.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| the display string `floatformat` builds (the bare integer string, or the `number` decimal string) | `List[int]` of Unicode code points; specification carried by `PSeq[int]` via `ToSeq` | character `c` ↔ code point `ord(c)`; `str` concatenation ↔ list `+`; the decimal point `'.'` ↔ code point 46; the minus `'-'` ↔ 45; digit `'0'+d` ↔ 48 + d |
| `int(d)` (the integer part of the parsed `Decimal`) | `int_value: int` | identity on the integer |
| `not m` (`m = int(d) - d`, zero ⟺ integral) | `frac_zero: bool` | `frac_zero == (m == 0)` |
| `int(arg)` (requested decimal places) | `p: int` | identity on the integer |
| `"%d" % int(d)` (early-return integer string) | `int_render(int_value)` | the decimal-digit rendering with a leading `'-'` for negatives, NO `'.'` |
| `mark_safe(...)` wrapper (175,199) | identity (omitted) | only sets the `SafeString` flag; does not change the character content the F2P/P2P tests compare |

`str` indexing/iteration is banned in Nagini, so the carrier is `List[int]`
throughout; the specification is phrased over `PSeq[int]` via `ToSeq`. The
integer rendering is built by a forward digit loop matched to the tail-shaped
front-recursive `digits_acc` (a single auto-unfold per step).

## 3. Deep-model reference provenance (A-reference — checked by G-AX)

### 3.1 `formats.number_format` (A-reference, NOT a consumed axiom)
**Callee:** `django.utils.formats.number_format` (`formats.py:172`), delegating to
`django.utils.numberformat.format` (`numberformat.py:7`). Invoked in BOTH
branches of `floatformat` to lay out the digit string for the active locale.

The change under spec is the BRANCH SELECTION feeding this callee, not the
callee itself; the callee is unchanged. For the early-return (bare-integer)
path the callee is invoked as `number_format("%d" % int(d), 0, ...)` with
`decimal_pos=0` and no forced grouping. Under the test configuration (no
`USE_THOUSAND_SEPARATOR`, `force_grouping=False`, `use_l10n=False`) it is
**digit-content preserving** on that integer string: `numberformat.format`
takes the `isinstance(number, int)`-free fast path / sign+integer assembly and
returns the same digit characters with no separator (`numberformat.py:33-40`).
This is the property `model.py` relies on so that the modeled core string
`int_render(int_value)` equals the end-to-end `floatformat` observable in the
bare-integer regime. `axiom_check.py` (G-AX) validates it by running the real
`number_format` on a range of integers and asserting digit-content preservation,
and by running the real `floatformat` end-to-end and asserting it equals
`int_render` for integral values at `p <= 0`.

**Flag dependency (recorded for G-AX):** the digit-content-preservation holds
under `decimal_pos=0`, `force_grouping=False`, and `USE_THOUSAND_SEPARATOR`
unset — the exact configuration of the early-return call site. G-AX fuzzes that
configuration.

### 3.2 The decimal-path core (separator-bearing regime)
The else branch's **core** string assembly (`defaultfilters.py:181-198`, the
`Decimal.quantize` + `as_tuple` digit construction inserting a `'.'`) is the
UNCHANGED path; `model.py` models it as a faithful skeleton `int_render +
PSeq(46) + zeros_seq(|p|)` whose load-bearing property is solely that the
**core** string (the digit string built BEFORE the localisation callee
`number_format` lays it out) CONTAINS the decimal separator (code point 46) —
that is what distinguishes it from the bare-integer regime and makes
`model_prepatch` fail. `axiom_check.py` confirms the real **core** string is
separator-bearing for every non-integral value or `p > 0`, and confirms the
post-patch and pre-patch filters AGREE on this regime (the fix is localised to
the bare-integer regime).

**Layer of the discriminator (core, not end-to-end).** The property "separator
present iff NOT (integral and `p<=0`)" holds at the **core** layer only. It is
FALSE end-to-end, because `number_format` at `decimal_pos=0` may strip a
trailing separator: the real `floatformat(-0.499, 0) == "0"` — a non-integral
value at `p<=0` whose core string `"0."` is laid out by `number_format` (which
drops the trailing `.`) to a bare integer with no separator. So every statement
of the discriminator is scoped to the **core** layer; the end-to-end pin is only
the bare-integer-regime equality `floatformat == int_render` (A-reference, §3.1).

**On the fractional digits.** The exact digits of the decimal path are not
pinned by the skeleton's all-zeros field. Those digits ARE observed by P2P/F2P
tests (`floatformat(0.000000000000000000015, 20) == "0.00000000000000000002"`;
`7.7,3 → "7.700"`; `5555.555,2 → "5555.56"`; `8.2798,3 → "8.280"`), so the
skeleton's all-zeros field would mispredict them as an end-to-end statement.
But every such input lies in the patch-UNCHANGED regime (pre == post): the
else-branch is tagged **A-reference** and refines to the real unchanged decimal
path, so the all-zeros field is discarded under refinement and is NOT the
resolving oracle. Its sole load-bearing role is **core-layer** separator-
presence. Pinning only that (not the exact digits) keeps the spec the weakest
faithful one while leaving verify ⇒ resolve intact (every spec/real mismatch
lies strictly outside the patch-changed class `{integral ∧ p == 0}`).
