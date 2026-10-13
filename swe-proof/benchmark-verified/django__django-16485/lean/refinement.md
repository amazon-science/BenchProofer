# refinement.md — django__django-16485

Maps every operation in `implementation_floatformat` to its `patch.diff`
counterpart. Tags: **R** (type refinement), **A-consumed** (proof uses an axiom's
property), **A-reference** (deep model validated == real callee by G-AX), **I**
(identical concrete op). Every step is R, A, or I.

## Modeled function: `floatformat` (`floatformat`)

The patch changes exactly one branch guard in `floatformat`:

```diff
-    if not m and p < 0:
+    if not m and p <= 0:
         return mark_safe(
             formats.number_format("%d" % (int(d)), 0, use_l10n=use_l10n,
                                   force_grouping=force_grouping))
```

Everything before this guard (suffix parsing, the `Decimal` coercion of `text`,
`p = int(arg)`, `m = int(d) - d`) is unchanged pre-processing that establishes
the state the guard branches on. The modeled function takes that post-parse state
(`d : DecVal`, `p : Int`) directly and reproduces the two-way rendering choice the
guard governs:

```python
# post-patch, at the fix point:
if not m and p <= 0:
    return mark_safe(formats.number_format("%d" % (int(d)), 0, …))   # integer branch
# ... else fall through to:
exp = Decimal(1).scaleb(-abs(p)); ... rounded_d = d.quantize(exp, ROUND_HALF_UP, Context(prec=prec))
... number = "".join(...)
return mark_safe(formats.number_format(number, abs(p), …))          # general branch
```

The general branch is PARTIAL even post-patch: for a whole ZERO `d` with
trailing zeros and a small positive `p` (e.g. `Decimal("0.000")`, `p = 1`),
`prec = abs(p) + units + 1 <= 0` and `Context(prec=prec)` raises `ValueError`,
which propagates out of `floatformat`. The modeled observable is therefore
`Option String` — `some s` for a returned string, `none` for the propagated
raise — and `decimalDigits : DecVal → Int → Option String` carries the digit
builder's partiality (`none` exactly where it raises; see mapping.md).

Lean impl (`implementation_floatformat`):
```lean
def implementation_floatformat (d : DecVal) (p : Int) : Option String := Id.run do
  if decIsWhole d && decide (p ≤ 0) then
    return some (numberFormat (toString (decIntPart d)) 0)
  return (decimalDigits d p).map (fun s => numberFormat s p.natAbs)
```

| # | Lean op | patch.diff / real-code counterpart | tag | justification |
|---|---|---|---|---|
| 1 | `decIsWhole d` | `not m` (`m = int(d) - d`) | **R** | the "value is a whole number" test. `decIsWhole : DecVal → Bool` is an OPAQUE unchanged sub-computation carried IDENTICALLY in spec and impl. No property of it is consumed by the proof (it cancels on both sides), so there is no axiom and no G-AX obligation — it is a pure type refinement of the Python `bool(not m)`. Unchanged by the patch. |
| 2 | `decide (p ≤ 0)` | `p <= 0` | **I** (the changed op, modeled concretely) | **the fixed operation.** The guard is changed from `p < 0` to `p <= 0`; the Lean impl uses `p ≤ 0` exactly. Modeled concretely (`Int` comparison), not axiomatized. The prepatch uses `p < 0` (the bug). |
| 3 | `decIsWhole d && decide (p ≤ 0)` | `not m and p <= 0` | **I** | the conjunction guarding the integer branch; `&&` ↔ `and` (short-circuit irrelevant — both operands are pure). |
| 4 | `return some (numberFormat (toString (decIntPart d)) 0)` | `return mark_safe(formats.number_format("%d" % (int(d)), 0, use_l10n=…, force_grouping=…))` | **R** | integer branch (total — always returns). `decIntPart d ↔ int(d)` and `numberFormat ↔ formats.number_format` are OPAQUE unchanged callees carried identically in spec and impl (no consumed property); `toString (decIntPart d) ↔ "%d" % int(d)` (integer→decimal string); the call's flag config is fixed/unchanged, folded into the opaque (mapping.md); `mark_safe` is an identity-on-content wrapper (dropped — the modeled observable is the string content); `some` wraps the normal return in the Option observable. |
| 5 | `return (decimalDigits d p).map (fun s => numberFormat s p.natAbs)` | `return mark_safe(formats.number_format(number, abs(p), …))` where `number` is built by lines 181–198, OR the `ValueError` that block raises propagating out | **R** | general branch (partial). `decimalDigits d p ↔` `some number` on success / `none` on the block's raise (the quantize+as_tuple+join digit-string builder with `Context(prec<=0)` partiality); `Option.map` applies the final formatting only on success — a raise short-circuits past `number_format`, exactly as in Python; `numberFormat ↔ formats.number_format`; `p.natAbs ↔ abs(p)` (`Int.natAbs ↔ Python abs`). This branch is taken in every case the integer branch is not. |

The impl region is **R/I** only — there is NO A-tagged content. The opaque callees
(`decIsWhole`, `decIntPart`, `decimalDigits`, `numberFormat`) appear IDENTICALLY in
`problem_spec_floatformat` and `implementation_floatformat`; the proof consumes no
property of them (they cancel), so there is no consumed axiom (`A-consumed`) and no
deeply-modeled changed op (`A-reference`). The proof agent should close
`correct_floatformat` by `unfold`/`simp [Id.run]`, reducing the impl's
`Id.run do … if …` to the same `if-then-else` the spec states — no axiom needed.
Because there is no consumed callee axiom, **G-AX skips** (`axiom_check.py` is a
skip stub). The impl region is not all-A-tagged, so `conf_skip = false` and G-CONF
runs the R/I differential.

## Soundness check (verify ⟹ correct)

- `problem_spec_floatformat d p result := result = (if decIsWhole d && decide (p ≤ 0)
  then some (numberFormat (toString (decIntPart d)) 0) else (decimalDigits d p).map
  (fun s => numberFormat s p.natAbs))` pins the result EXACTLY (full `Option String`
  equality to an input-grounded expression) — directive 5 (frame): there is one
  output component (the outcome: rendered string or propagated failure), and it is
  fully determined by `d` and `p` through the branch. No component is left
  unconstrained.
- Directive 8 (grounded): the postcondition is NOT an opaque oracle for the whole
  function — it is a structural case split on `decIsWhole d` and `p ≤ 0` whose
  two arms are the two genuinely different sub-computations the real code runs.
  An impl can satisfy it only by selecting the SAME branch on every input, i.e.
  by getting the guard right.
- **The discriminating clause** is `decIsWhole d = true ∧ p = 0`: the spec selects
  the integer branch, the prepatch (`p < 0`) selects the general branch. The two
  branch outcomes are distinct opaque values (`some (numberFormat (toString
  (decIntPart d)) 0)` vs `(decimalDigits d 0).map (fun s => numberFormat s 0)`), so
  the prepatch's carried gold proof cannot close (G-DIFF / G-PANEL): no wrong guard
  verifies. This is exactly the FAIL_TO_PASS case — `floatformat("0.00", 0)` and
  `floatformat(Decimal("0.00"), 0)`: whole value, `p == 0`. Pre-fix this fell into
  the general branch and crashed (`Context(prec=0)` ValueError, i.e. `decimalDigits
  d 0 = none` there — the mapped outcome differs from `some …` concretely); post-fix
  it returns the integer `"0"`.
- Faithfulness of the `Option` observable (the former G-PANEL-2 defect, fixed):
  the real POST-patch `floatformat` still raises `ValueError` on e.g.
  `floatformat(Decimal("0.000"), 1)` and `floatformat("0E-10", 1)` (verified on a
  worktree at base_commit + patch.diff). The model now returns `none` exactly
  there (`decimalDigits` is `none` where the builder raises, and the general
  branch propagates it), instead of fabricating a total string. The raise points
  are P (unchanged partiality), not part of the fix, and no hidden test exercises
  them; but the observable now matches reality on them.
- PASS_TO_PASS preserved: for `p > 0`, or non-whole `d`, the guard `p ≤ 0` /
  `p < 0` agree on the false outcome (both take the general branch); for whole `d`
  with `p < 0` both take the integer branch. The two guards differ ONLY at the
  `p = 0, whole` point — exactly where the fix is needed and where no prior test
  exercised it.
- There is no consumed callee axiom, so G-AX skips. G-CONF differential-tests the
  R/I branch-selection shadow against an in-process replica of the patched guard
  (the opaque callees are modeled identically on both legs, isolating the branch
  selection — the only thing the impl owns).
