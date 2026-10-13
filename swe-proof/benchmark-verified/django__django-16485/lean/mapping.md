# mapping.md — django__django-16485

## Symbol binding (file:line @ base_commit `39f83765e12b0e5d260b7939fc3fe281d879b279`)

| Lean symbol | Python symbol | location |
|---|---|---|
| `floatformat` (modeled fn) | `floatformat(text, arg=-1)` | `django/template/defaultfilters.py:96` |
| the changed branch guard | `if not m and p < 0:` → `if not m and p <= 0:` | `django/template/defaultfilters.py:171` |
| integer-format early return | `return mark_safe(formats.number_format("%d" % (int(d)), 0, …))` | `defaultfilters.py:171–179` |
| general decimal path (unchanged) | `exp = … ; rounded_d = d.quantize(…) ; … ; return mark_safe(formats.number_format(number, abs(p), …))` | `defaultfilters.py:181–206` |

## The modeled state (at the fix point)

`floatformat` first parses the `arg` suffixes (`g`/`u`), coerces `text` into a
`Decimal d`, computes `p = int(arg)` and `m = int(d) - d`. All of that is
pre-processing that the patch does NOT touch; it establishes the state the fix
branches on. The modeled function takes that post-parse state directly:

| Lean | Python value at the fix point | notes |
|---|---|---|
| `d : DecVal` (`{negative, digits, exponent}`) | `d : Decimal`, viewed via `d.as_tuple()` = `(sign, digits, exponent)` | the as_tuple bijection: `negative ↔ sign==1`, `digits ↔ tuple of significant digits, most-significant first`, `exponent ↔ tuple exponent`. A faithful proxy for the `Decimal` value. |
| `p : Int` | `p = int(arg)` | the (already-parsed) precision argument. |

### Lean ↔ Python type bijection (used by G-CONF and G-AX)

- `DecVal` ↔ `Decimal`, via `d.as_tuple()`. `decIntPart d ↔ int(d)`,
  `decIsWhole d ↔ (int(d) - d == 0)` (i.e. Python `not m`),
  `decimalDigits d p : Option String ↔` the general-branch digit builder
  (lines 181–198): `some number` when it produces the `number` string, `none`
  when it RAISES (see "Partiality" below), and `numberFormat s k ↔
  formats.number_format(s, k, use_l10n=…, force_grouping=…)`.
- `result : Option String` ↔ the call's outcome: `some s` ↔ the returned
  (mark_safe) string `s`; `none` ↔ the call raises (the general branch's
  `ValueError` propagating out of `floatformat`).

### Partiality of the general branch (post-patch reality)

The digit builder computes `prec = abs(p) + units + 1` where, for a WHOLE `d`
(`m == 0`), `units = len(digits) + exponent` of `d.as_tuple()`. For a whole
ZERO value with enough trailing zeros and a small positive `p` — e.g.
`floatformat(Decimal("0.000"), 1)`, `floatformat("0E-10", 1)` — `prec <= 0`
and `Context(prec=prec)` raises `ValueError: valid range for prec is
[1, MAX_PREC]`, which propagates to the caller EVEN POST-PATCH (verified on a
worktree at base_commit + patch.diff). The model represents that outcome
honestly: `decimalDigits d p = none` exactly there, and the modeled result is
`none` (call raises). The fix itself only reroutes the whole ∧ `p <= 0` inputs
to the total integer branch; it does not totalize the general branch.

## Callee provenance + flag deps (opaque, signature-only — §0.7)

These are UNCHANGED operations the fix's neighborhood calls. None is the changed
op (the changed op is the branch guard `p ≤ 0`, modeled concretely). They carry
NO consumed `_prop` axiom and NO G-AX obligation — the proof case-splits on the
guard, and the two branches use the SAME opaque callees in spec and impl, so the
callees cancel and no property of them is asserted or consumed. They are pure
type refinements (R) of the unchanged Python sub-computations. G-AX therefore
skips (`axiom_check.py` is a skip stub).

| opaque | real callee / block | provenance |
|---|---|---|
| `decIntPart : DecVal → Int` | `int(d)` | `defaultfilters.py:167,174` — Decimal→int truncation. Unchanged. |
| `decIsWhole : DecVal → Bool` | `not m` where `m = int(d) - d` | `defaultfilters.py:167,171` — "is the value an exact integer". Unchanged. |
| `decimalDigits : DecVal → Int → Option String` | the digit-string builder `number` (quantize + as_tuple + join), or its raise | `defaultfilters.py:181–198`. Unchanged. This block is PARTIAL — whenever `prec = abs(p) + units + 1 <= 0` (whole `d` with `p == 0` pre-patch; whole ZERO `d` with trailing zeros and small positive `p` even post-patch) it raises `ValueError` (`Context(prec<=0)`). The opaque models it as `Option String`: `some number` on success, `none` on the raise, which the modeled result propagates (see "Partiality" above). |
| `numberFormat : String → Nat → String` | `formats.number_format(s, k, use_l10n=use_l10n, force_grouping=force_grouping)` | `django/utils/formats.py`. Applied in BOTH branches. **Flag dependency:** behavior depends on `use_l10n`/`force_grouping`, which are fixed per call by the `arg` suffix parsing and are unchanged by the patch. The model folds the call's flag config into the opaque; the F2P inputs use the default config (no `g`/`u` suffix), where `number_format(int_str, 0)` returns the integer string. |

## G-CONF fuzz seed

Pinned seed: **16485** (also in `conformance_check.py`).
