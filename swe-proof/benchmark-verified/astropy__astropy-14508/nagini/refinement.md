# refinement.md — astropy__astropy-14508

The operation-by-operation correspondence between `model.py`'s implementation
(the `format_float_field` impl region, the `e_index` helper, and the
axiomatized renderers) and `patch.diff` (the gold patch). Each step is tagged
**R** (type refinement), **A** (axiomatized callee — split into **A-consumed**,
where the proof uses the axiom's `Ensures`, and **A-reference**, where a deep
behavioural model is validated == the real callee by axiom_check.py / G-AX), or
**I** (identical concrete operation). The claim: *any implementation that
verifies against this frozen spec, refined per the map below, is behaviourally
equal to the gold patch on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

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

| # | model.py impl op (`format_float_field`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameters `value: float` (interpreted) **and** `neg: bool` | `value` (a Python `float`, i.e. a finite double) | R | a finite double `d` refines to the PAIR `(d + 0.0, signbit(d))`; back, `d = copysign(value, -1 if neg else +1)`. The behaviour is about real-number rendering, so the magnitude is interpreted rather than int-scaled — but an interpreted real is a QUOTIENT of the doubles that identifies `+0.0` with `-0.0`, and the renderer does not respect that quotient (`"0.0"` vs `"-0.0"`). The pair is a complete invariant of `d` (nonzero: `value` determines it, bit-exactly; at zero: `neg` does), so `str(d)` is a genuine function of the pair, which is what makes the A2 axiom well-defined. The two linkage pre-conditions `Implies(value > 0.0, not neg)` / `Implies(value < 0.0, neg)` exclude only pairs denoting no number, so the domain is the full set of finite doubles — `-0.0` included, and a zero float IS observed (P2P `test_update_numeric`). Full justification: mapping.md §2. |
| A2 | `vs = shortest_field(value, neg)` | `value_str = str(value).replace("e", "E")` | A-reference | the changed renderer is modelled as the axiom `shortest_field`, ensuring `ToSeq(Result()) == shortest_seq(value, neg)` where the `@Pure` companion `shortest_seq` carries the changed property (round-trip `parse_dec == value`, **minimal significant digits** `sig_count == min_sig`, `len == shortest_field_len`, suffix ≤ 5). There is no consumed axiom *about `_format_float` itself*. The deep behaviour is validated **== the real callee** by G-AX: axiom_check.py runs `str(value).replace("e","E")` over boundary + ~240k fuzz and asserts every clause. `str(float)` IS the minimal round-tripping decimal (CPython shortest-repr; mapping.md §3.1). |
| A3 | `n = len(vs)`; `if n <= 20: return vs` | `str_len = len(value_str)`; `if str_len > 20: ...` (else fall through, returning `value_str`) | R + I | `len` over `List[int]` ↔ `len` over `str` (R); the ≤20 / >20 branch is the identical control-flow guard (I). The returned `vs` satisfies the fits-branch post-condition `ToSeq(Result()) == shortest_seq(value, neg)` directly from A2. |
| A4 | `idx = e_index(ToSeq(vs))` | `idx = value_str.find("E")` | R | `find("E")` ↔ first index of code point 69 in the `List[int]`, with the same -1-if-absent contract (mapping.md §2). |
| A5 | `if idx < 0:` first-20 copy loop | `value_str = value_str[:20]` | R + I | the slice `[:20]` is the character-for-character copy the loop performs over `List[int]` (R on the carrier; I on the slice semantics). The loop's invariant `ToSeq(result) == ToSeq(vs).take(j)` discharges the over-cap content post-condition `ToSeq(Result()) == shortest_seq(value, neg).take(20)` (since `ToSeq(vs) == shortest_seq(value, neg)` by A2). |
| A6 | `else:` significand-trim + exponent-keep loops | `value_str = value_str[: 20 - (str_len - idx)] + value_str[idx:]` | R + I | the first loop copies `vs[: 20-(n-idx)]` (invariant `ToSeq(result) == ToSeq(vs).take(j)`, reaching `take(keep)`) and the second copies `vs[idx:]` (invariant `ToSeq(result) == ToSeq(vs).take(keep) + ToSeq(vs).drop(idx).take(k-idx)`, reaching `... + drop(idx)`); concatenation ↔ list `+`. This discharges the over-cap content post-condition `ToSeq(Result()) == shortest_seq(value, neg).take(20 - (len - idx)) + shortest_seq(value, neg).drop(idx)`. `keep = 20 - (n - idx) >= 0` is guaranteed by the suffix-≤5 clause on `shortest_seq` (a finite double's exponent suffix is short). |
| A7 | `return result` (a `List[int]`) | `return value_str` (a `str`) | R | identity on character content under the `str` ↔ `List[int]` bijection. |

The discriminating content of the change — rendering with the **minimal** number
of significant digits instead of a fixed 16 — lives in
`sig_count(shortest_seq(value, neg)) == min_sig(value)` (model, A2 via `shortest_seq`)
⇔ the swap from `f"{value:.16G}"` to `str(value)` (real). The pre-patch used the
fixed-precision renderer; `model_prepatch.py` reproduces that (`padded_field`,
which carries no minimality guarantee and no `shortest_seq` content tie) and
**fails** the fits-branch postcondition
`Implies(shortest_field_len(value, neg) <= 20, ToSeq(Result()) == shortest_seq(value, neg))`
— exactly the spec sensing the change (G-DIFF). The discriminator is
significant-digit minimality, not round-trip: both `str(0.009125)` and
`f"{0.009125:.16G}"` round-trip to the same double, but only `str` spends the
minimal 4 significant digits (`"0.009125"`), while `.16G` spends 16
(`"0.009124999999999999"`), which is what forces the comment-truncation the F2P
test forbids.

The over-cap branch's content is now pinned STRUCTURALLY (not by length alone):
the post-condition requires `ToSeq(Result())` to be a take/drop/concat of the
exact rendering `shortest_seq(value, neg)`, so the result must be *produced by*
trimming that rendering. An impl that truncated to the first 20 characters
(dropping the exponent on scientific notation) or emitted 20 arbitrary code
points satisfies `len == 20` but FAILS this content post-condition — confirmed by
re-running both as attackers (each fails to verify), and both are observed by the
P2P scientific-notation tests (mapping.md §4).

## B. The trim logic is unchanged (kind I)

The 20-character trim (`str_len > 20` guard, `find("E")`, `[:20]` /
`[:20-(str_len-idx)] + [idx:]`) is byte-for-byte identical pre- and post-patch.
It is modelled faithfully (A3–A7) so the scientific-notation P2P
(`test_floating_point_value_card`, whose value `-4.673...e+32` is 22 chars and
trims to `-4.6737463674763E+32`) keeps passing, but it carries none of the
behavioural change — hence no separate `model_prepatch_<k>` for it.

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A, or I. The one operation that genuinely *changed* — the
choice of float→string renderer — is captured by the `shortest_field`
**A-reference** axiom whose `Ensures` state the *changed property* (minimal
significant digits + round-trip), validated == the real `str(float)` callee by
G-AX; it is NOT hidden behind an axiom about `_format_float` itself. The
`padded_field` axiom is the faithful model of the pre-patch renderer (used only
by `model_prepatch.py`); `parse_dec` / `sig_count` / `min_sig` are the
supporting numeric theory the minimality clause is stated over, each
G-AX-checked against its real computation.

## D. verify(model) ⇒ resolved

`format_float_field` verifies only if, whenever the minimal rendering fits in 20
characters, its output round-trips to `value` AND spends the minimal significant
digits (A2), and otherwise applies the exact unchanged trim (A3–A7). By R
(`float` interpreted, `str` ↔ `List[int]`, `find` ↔ `e_index`, slices ↔ copy
loops) the verified function equals `_format_float` post-gold on every finite
float; by G-AX the deep model `shortest_field` equals the real
`str(value).replace("e","E")` (A-reference) and the supporting numeric callees
meet their contracts. Therefore a model satisfying this spec, refined by the map
above, is the gold patch up to type refinement and audited callees — and the
gold patch resolves (G-RESOLVE). The trust points are exactly the two of PLAN
§1.1: axiom soundness (G-AX) and refinement fidelity (this document, G-EQ).
