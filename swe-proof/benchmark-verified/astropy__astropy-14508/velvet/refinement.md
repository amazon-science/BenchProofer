# refinement.md — astropy__astropy-14508

Operation-by-operation correspondence between `Solution.lean`'s `formatFloatField`
impl region (plus the `eIndex` helper and the axiomatized renderer) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement), **A**
(axiomatized callee — **A-consumed** where the proof uses the axiom's `ensures`,
**A-reference** where a behavioural model is validated == the real callee by
axiom_check.py / G-AX), or **I** (identical concrete operation). The claim: *any
implementation that verifies against this frozen spec, refined per the map below,
is behaviourally equal to the gold patch on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the correctness oracle, G-RESOLVE).

**§0.7 library-routine oracle.** The operation the patch changes — the
float→text renderer `str(value)` — is modelled as the **A-consumed / A-reference**
axiom `shortestField` rather than deeply transliterated. This is permitted under
SPEC_GUIDE §0.7: it is a self-contained stdlib routine the changed function
delegates to, whose dtoa internals are inexpressible in Velvet. Its *properties*
(round-trip, minimal significant digits, short exponent suffix) are asserted and
validated == the real callee by G-AX. The row A2 below is that axiomatized op;
every other row is R or I.

## A. The renderer swap — `_format_float` (`astropy/io/fits/card.py:1300`)

Gold hunk (the load-bearing change):
```
-    value_str = f"{value:.16G}"
-    if "." not in value_str and "E" not in value_str:
-        value_str += ".0"
-    elif "E" in value_str:
-        ...normalize exponent to two digits...
+    value_str = str(value).replace("e", "E")
```
followed by the (unchanged) 20-character trim.

| # | Solution.lean impl op (`formatFloatField`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `value : Float` | `value` (a Python `float`/`np.floating`) | R | `float` ↔ Lean `Float` (IEEE-754); the behaviour is about real-number rendering. |
| A2 | `vs := shortestField value` | `value_str = str(value).replace("e", "E")` | **A-consumed (waived changed op) + A-reference** | the changed renderer is the axiom `shortestField`, whose `ensures` the proof CONSUMES: `shortestField_roundtrip` (`parseDec (shortestField v) = v`), `shortestField_minimal` (`sigCount (shortestField v) = minSig v` — **minimal significant digits**, the change), `shortestField_nonempty`, `shortestField_suffix_short`. Validated **== the real callee** by G-AX: axiom_check.py runs `str(value).replace("e","E")` over boundary + ~280k fuzz (2 seeds) + powers-of-two + subnormals and asserts every clause. `str(float)` IS the minimal round-tripping decimal (CPython shortest-repr; mapping.md §3.1). Per the §0.7 waiver, this — not a deep dtoa transliteration — is the model of the changed op. |
| A3 | `n := vs.length`; `if n ≤ 20 then return vs` | `str_len = len(value_str)`; `if str_len > 20: …` (else fall through, returning `value_str`) | R + I | `length` over `List Char` ↔ `len` over `str` (R); the ≤20 / >20 branch is the identical control-flow guard (I). The returned `vs` satisfies the fit-branch post-conditions `out = shortestField value`, `parseDec out = value`, `sigCount out = minSig value` directly from A2. |
| A4 | `idx := eIndex vs` | `idx = value_str.find("E")` | R | `find("E")` ↔ first index of `'E'` in the `List Char`; Python's `-1` "absent" ↔ Lean sentinel `vs.length`, so `idx ≥ n` ↔ `idx < 0` and `idx < n` ↔ `idx ≥ 0` (mapping.md §2). |
| A5 | `if idx ≥ n then return vs.take 20` | `if idx < 0: value_str = value_str[:20]` | R + I | the slice `[:20]` ↔ `List.take 20` (R on carrier, I on slice semantics). Discharges the over-cap content post-condition `out = (shortestField value).take 20`. |
| A6 | `else return vs.take (20 - (n - idx)) ++ vs.drop idx` | `else: value_str = value_str[: 20 - (str_len - idx)] + value_str[idx:]` | R + I | significand prefix `[:20-(n-idx)]` ↔ `List.take (20-(n-idx))`, exponent suffix `[idx:]` ↔ `List.drop idx`, `str` `+` ↔ `List` `++`. Discharges `out = (shortestField value).take (20 - (n - idx)) ++ (shortestField value).drop idx`. `20 - (n - idx) ≥ 0` is guaranteed by `shortestField_suffix_short` (a finite double's exponent suffix is ≤ 5), discharged in the proof via `eIndex_eq_E` + the suffix axiom. |
| A7 | `return …` (a `List Char`) | `return value_str` (a `str`) | R | identity on character content under the `str` ↔ `List Char` bijection. |

The discriminating content of the change — rendering with the **minimal** number
of significant digits instead of a fixed 16 — lives in
`sigCount (shortestField value) = minSig value` (A2) ⇔ the swap from
`f"{value:.16G}"` to `str(value)`. The pre-patch used the fixed-precision
renderer; `Solution_prepatch.lean` reproduces that (`paddedField`, which carries
no minimality guarantee and is not tied to `shortestField`) and **fails** the
fit-branch post-conditions
`(shortestField value).length ≤ 20 → out = shortestField value` /
`… → sigCount out = minSig value` / `… → parseDec out = value` — exactly the spec
sensing the change (G-DIFF). The discriminator is significant-digit minimality,
not round-trip alone: both `str(0.009125)` and `f"{0.009125:.16G}"` round-trip to
the same double, but only `str` spends the minimal 4 significant digits
(`"0.009125"`), while `.16G` spends 16 (`"0.009124999999999999"`), which forces
the comment-truncation the F2P test forbids.

## B. The trim logic is unchanged (kind I) — and G-CONF-tested

The 20-character trim (`str_len > 20` guard, `find("E")`, `[:20]` /
`[:20-(str_len-idx)] + [idx:]`) is byte-for-byte identical pre- and post-patch. It
is modelled faithfully (A3–A6) so the scientific-notation P2P
(`test_floating_point_value_card`, whose value trims to `-4.6737463674763E+32`)
keeps passing. Although it carries none of the behavioural change, it IS R/I
content, so conformance_check.py (G-CONF) transliterates the whole
`formatFloatField` do block back to Python (with the A-reference renderer supplied
by the real audited callee) and differential-tests it against the gold post-patch
`_format_float` over ~122k finite floats (incl. powers of two), 0 disagreements —
confirming the R/I transliteration is faithful. (No separate `Solution_prepatch_k`
for the trim: it has no independently-observable fixed behaviour.)

## C. No kind-3 (unexpressible-changed-op) steps under the waiver

The one operation that genuinely *changed* — the choice of float→string renderer
— is captured by the `shortestField` axiom whose `ensures` state the *changed
property* (minimal significant digits + round-trip), validated == the real
`str(float)` callee by G-AX. Under the §0.7 waiver this is a sanctioned A model of
the changed op (not a kind-3 BLOCKED, not a deep transliteration). `paddedField`
is the faithful model of the pre-patch renderer (used only by
`Solution_prepatch.lean`); `parseDec` / `sigCount` / `minSig` are the supporting
numeric theory the minimality clause is stated over, each G-AX-checked against its
real computation.

## D. verify(Solution) ⇒ resolved

`formatFloatField` verifies only if, whenever the minimal rendering fits in 20
characters, its output round-trips to `value` AND spends the minimal significant
digits (A2), and otherwise applies the exact unchanged trim (A3–A6). By R
(`Float` ↔ `float`, `str` ↔ `List Char`, `find` ↔ `eIndex`, slices ↔ `take`/`drop`)
the verified function equals `_format_float` post-gold on every finite float; by
G-AX the oracle `shortestField` equals the real `str(value).replace("e","E")` and
the supporting numeric callees meet their contracts; by G-CONF the R/I trim
transliteration matches gold on ~122k inputs. Therefore a model satisfying this
spec, refined by the map above, is the gold patch up to type refinement and
audited callees — and the gold patch resolves (G-RESOLVE). The trust points are
exactly: axiom soundness (G-AX) and refinement fidelity (this document, G-EQ).
