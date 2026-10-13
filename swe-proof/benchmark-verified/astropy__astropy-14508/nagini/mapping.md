# mapping.md — astropy__astropy-14508

Binds every `model.py` symbol to its repository counterpart at
`base_commit = a3f4ae6cd24d5ecdf49f213d77b3513dd509a06c`, states the type
abstraction, and gives the provenance of each axiom (callee source + the exact
behaviour the axiom encodes).

Repo file under change: `astropy/io/fits/card.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `format_float_field(value, neg)` | `_format_float(d)` — `astropy/io/fits/card.py:1300` | the modeled changed function: render a float to a ≤20-char FITS value field. The single repo argument `d` (a finite double) is carried by the PAIR `(value, neg)` — see §2 |
| `shortest_field(value, neg)` *(axiom — A-reference)* | `str(d)` (then `.replace("e","E")`) — the renderer the patch switches TO, `card.py:1302` post-patch | unchanged stdlib float→str primitive (Python's shortest round-tripping repr) the fix newly invokes, applied to the double the pair denotes; deep behavioural model validated == real callee by G-AX |
| `shortest_seq(value, neg)` *(axiom — A-reference)* | the **value** (sequence of code points) of `str(d).replace("e","E")` | the pure `PSeq[int]` content of `shortest_field(value, neg)`, so the bounded result can be pinned STRUCTURALLY (take/drop/concat) against the exact rendering in a post-condition; same callee + same provenance + same G-AX evidence as `shortest_field` (the impure renderer ensures `ToSeq(Result()) == shortest_seq(value, neg)`) |
| `padded_field(value, neg)` *(axiom — pre-image reference)* | `f"{d:.16G}"` + exponent normalization — the renderer the patch switches FROM, `card.py:1302-1315` pre-patch | the OLD fixed-precision primitive; present so the pre-patch skeleton has a faithful buggy renderer; validated well-formed + non-minimal by G-AX |
| `parse_dec(field)` *(axiom)* | `float(field.replace("E","e"))` — CPython stdlib `float()` parser | the value-reconstruction theory the round-trip property is stated over (inverse of decimal rendering) |
| `sig_count(field)` *(axiom)* | number of significant digits in a decimal string | structural count over the significand's digit run |
| `min_sig(value)` *(axiom)* | fewest significant digits a decimal needs to round-trip `value` | property of the number's digits; a sign costs no significant digits, so it takes no sign flag |
| `shortest_field_len(value, neg)` *(axiom)* | `len(str(d).replace("e","E"))` | the length of the minimal rendering; it takes the sign flag because a negative number's field is one character longer |
| `e_index(field)` / `e_index_from` | `value_str.find("E")` — `card.py:1321` | pure spec: first index of the exponent marker `E` |

The pre-patch repo construct the change removes (for the refinement audit, not
referenced from the consumer spec view): the `f"{value:.16G}"` format and the
exponent-zero-padding block (`card.py:1302-1315`).

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `str` (`value_str`, the function's return) | `List[int]` of code points | `s[k]` ↔ `field[k] == ord(s[k])`; `len(s)` ↔ `len(field)`; `str` slicing/`+` ↔ list slicing/`+`; the marker `"E"` ↔ code point `69` |
| `str` value inside a specification | `PSeq[int]` (pure Viper sequence) | `ToSeq(list)` materializes the list as a `PSeq`; `PSeq` `+`/`take`/`drop`/`len`/`[i]` mirror `str` `+`/slice/`len`/index |
| `float` (the repo argument `d`, a finite double) | the PAIR `(value: float, neg: bool)` — an interpreted Python `float` (`--float-encoding=real`) plus a sign flag | `d` ↦ `(d + 0.0, signbit(d))`; back: `d = copysign(value, -1 if neg else +1)`. See the note below: this is a **complete invariant** of `d`, and it is a pair rather than a bare real because the interpreted-real domain is a quotient of the doubles that the renderer does not respect |
| `value_str.find("E")` (`card.py:1321`) | `e_index(field)` over `List[int]`, comparing code point `69` | identity on first-occurrence semantics (-1 if absent) |
| `value_str[:20]` / `value_str[:20-(str_len-idx)] + value_str[idx:]` (`card.py:1324,1326`) | the two trimming loops in `format_float_field` | character-for-character copy of the same slices |

`str` indexing/iteration is banned in Nagini, so the field carrier is
`List[int]`; the specification is phrased over `PSeq[int]` via `ToSeq`. The
numeric input, by contrast, is interpreted because the rendered-precision
behaviour is genuinely about the real value.

**Why the input is a pair and not a bare interpreted real.** Under
`--float-encoding=real` the model's numbers are Viper reals, which have no signed
zero: `+0.0` and `-0.0` are the SAME abstract point (machine-checked — a probe
asserting `0.0 == -0.0` verifies under the flag and fails without it). The real
renderer does not identify them: it renders `0.0` as `"0.0"` and `-0.0` as
`"-0.0"`, three characters versus four. So `str(d)` is not a function of the real
value alone, and any spec whose symbols are functions of that value alone either
over-claims (forcing one field where the repo produces two) or leaves the sign
free. The pair closes this exactly:

* it is a **complete invariant** of a finite double. For nonzero `d`, `value`
  determines `d` (`d + 0.0` is bit-identical to `d` — verified over 300 000 random
  finite nonzero bit patterns, 0 mismatches); at zero, `neg` determines which zero.
  Hence `str(d)` genuinely IS a function of `(value, neg)`, which is what makes
  the axioms well-defined.
* it adds no states that denote no number: the pre-conditions
  `Implies(value > 0.0, not neg)` and `Implies(value < 0.0, neg)` pin the flag to
  the value's own sign away from zero, so the admissible pairs are exactly the
  finite signed numbers. The domain is not narrowed — every double still has a
  pair, `-0.0` included, which is precisely the input a value-only model could
  not describe.
* `-0.0` is reachable and in-domain: it passes `Header.set`'s type check and is
  not caught by the `inf`/`nan` guard (`card.py:330-351`), so it flows
  `_format_value` (`card.py:1287`) → `_format_float`. It is also already in this
  bundle's own conformance corpus.

Note this is not an artefact of the gold change: the pre-patch `f"{d:.16G}"`
renderer distinguishes the two zeros as well, so the sign sensitivity is a
property of the function's whole domain, before and after the fix.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `shortest_field` ↔ `str(value).replace("e","E")` (A-reference)
**Callee:** CPython `str(float)` / `repr(float)`. Since Python 3.1 these produce
the **shortest decimal string that round-trips to the same IEEE-754 double**
(David Gay / Grisu shortest-representation algorithm); the patch upper-cases the
exponent marker with `.replace("e","E")`. Source: CPython `Objects/floatobject.c`
`float_repr` → `PyOS_double_to_string(..., 'r', 0, ...)`; docs:
https://docs.python.org/3/tutorial/floatingpoint.html (repr is the shortest
string that round-trips). The axiom encodes exactly the properties the proof
consumes:

  * `parse_dec(shortest_field(value, neg)) == value` — it round-trips;
  * `sig_count(shortest_field(value, neg)) == min_sig(value)` — it spends the
    minimal number of significant digits (the whole point of the change);
  * `len == shortest_field_len(value, neg)`;
  * the field begins with `-` (code point 45) exactly when `neg` — the renderer
    reproduces the number's sign rather than inventing or discarding it, and a
    negative zero is a negative number; and
  * if an exponent marker is present, its suffix `E±NNN` is ≤ 5 characters
    (a finite double's decimal exponent is at most three digits, so the
    significand-trim arithmetic `20 - (str_len - idx)` is always ≥ 0).

This is the renderer the function newly invokes; it is modelled as an axiom and
validated **== the real callee** out-of-band by axiom_check.py (G-AX): for each
boundary + fuzz finite double `d` it forms the pair `(d + 0.0, signbit(d))`,
asserts the pair reconstructs `d`, and asserts `shortest_field(pair)` equals the
real `str(d).replace("e","E")` together with every property above (both zeros are
in the boundary list).

The companion `@Pure` axiom `shortest_seq(value, neg)` is the SAME callee viewed
as a value: it returns the `PSeq[int]` content of `str(d).replace("e","E")`, with
the identical round-trip / minimal-significant-digit / length / sign /
exponent-suffix properties (so G-AX validates it by the very same `shortest_field` checks). It
exists so the post-condition can pin the bounded result's CONTENT structurally —
`ToSeq(Result()) == shortest_seq(value, neg).take(...)`/`.drop(...)` — against the
exact rendering, not merely its length. The impure `shortest_field` axiom ties
the two together with `ToSeq(Result()) == shortest_seq(value, neg)`, so the impl's
materialized `vs` carries exactly that value.

### 3.2 `padded_field` ↔ `f"{value:.16G}"` (pre-patch renderer)
**Callee:** the pre-patch `_format_float` body — `f"{value:.16G}"` with the
exponent zero-padded to two digits. This primitive renders to a FIXED 16
significant digits regardless of how few the number needs, which is precisely
the defect (e.g. `0.009125` → `"0.009124999999999999"`). The axiom for
`padded_field` is therefore deliberately WEAK — non-empty, with a ≤5 exponent
suffix — and crucially does NOT claim minimal significant digits. axiom_check.py
(G-AX) confirms it is well-formed AND that it spends MORE than `min_sig` digits
on the regression values, so the discriminator the pre-patch skeleton fails on is
a real property of the old renderer, not an artefact. (`f"{value:.16G}"` does not
even always round-trip — 16 digits is sometimes insufficient for a double — so
the axiom correctly does NOT claim round-trip, which would be an over-claim.)

### 3.3 `parse_dec` ↔ `float(str)` (A — value-reconstruction theory)
**Callee:** CPython `float()` constructor on a decimal string (with the upper
`E` mapped back to `e`). It is the inverse of decimal rendering; the round-trip
postcondition `parse_dec(shortest_field(value, neg)) == value` is its defining use.
G-AX evaluates `float(field.replace("E","e"))` on every observed field.

### 3.4 `sig_count` / `min_sig` (A — significant-digit theory)
`sig_count(field)` counts the significant digits of a decimal string's
significand (leading zeros and integer-form trailing zeros dropped; zero counts
as one). `min_sig(value)` is the fewest significant digits any decimal reading
needs to round-trip `value` — equivalently `sig_count` of Python's shortest
round-tripping repr (`str`/`repr`), which is defined to emit the fewest such
digits. Note: it must NOT be computed as `min{k : float(f"{value:.{k}g}")==value}`
— `%g` rounds to NEAREST, so it can miss a k-digit rendering that round-trips via
a different last digit (e.g. for `2**-24`, `%.16g` → ...062 which does not
round-trip while `repr` → ...063 which does, so the `%g` scan over-reports 17
where 16 is truly minimal). The single fact the proof uses is
`sig_count(shortest_field(value, neg)) == min_sig(value)` (supplied by the
`shortest_field` axiom). G-AX implements both and asserts the equality over the
full fuzz corpus (0 violations on finite floats; the only mismatches are
`inf`/`-inf`, which are rejected upstream by io.fits — see §4).

## 4. Domain note (finite floats) and test relevance of the over-cap branch

`_format_float` is only reached for finite floats: `inf`/`nan` are rejected with
`ValueError` by `Header.set` before formatting (`test_assign_inf_nan`, a P2P).
The interpreted-float model and all axioms are stated over this finite domain,
and axiom_check.py fuzzes only finite floats (`math.isfinite`). This is recorded
so G-AX fuzzes the right configuration.

**The 20-character over-cap branch IS observed by PASS_TO_PASS tests** (verified
against instance.json; F2P/P2P membership below). Both scientific-notation
trim values flow through the `idx >= 0` exponent-preserving path:

| test | list | what it exercises |
|---|---|---|
| `test_floating_point_string_representation_card` | **F2P** | the headline regression: `0.009125` must render `"0.009125"` (4 sig digits), not the 16-digit `"0.009124999999999999"` — the minimality content of the fits-branch |
| `test_floating_point_value_card` | **P2P** | `-467374636747637647347374734737437.0` → `str` is `-4.673...e+32` (22 chars) → must trim to `-4.6737463674763E+32` (20 chars, exponent suffix `E+32` kept) — the `idx >= 0` over-cap path |
| `test_complex_value_card` | **P2P** | a complex card whose real/imag parts likewise render in scientific notation and trim with the exponent kept — same over-cap path |
| `test_assign_inf_nan` | **P2P** | `inf`/`nan` rejected upstream, fixing the finite domain |
| `test_update_numeric` | **P2P** | a zero float must render `"0.0"` (card image `TEST    =                  0.0`) — so a zero value is an OBSERVED input and cannot be excluded from the domain; it is the input whose sign the pair carrier makes expressible |

Because the over-cap branch's *content* (not merely its length) is observed by
these P2P tests, the post-condition pins that content STRUCTURALLY against the
exact rendering `shortest_seq(value, neg)`: when the rendering carries no exponent
marker the field is `shortest_seq(value, neg).take(20)`, and when it carries a
marker at index `idx` the field is
`shortest_seq(value, neg).take(20 - (len - idx)) + shortest_seq(value, neg).drop(idx)`
(significand shortened, full exponent suffix kept). A length-only `len == 20`
post-condition would be too weak — an impl that truncated to the first 20
characters (dropping the exponent) or emitted 20 arbitrary characters would
satisfy it yet fail `test_floating_point_value_card` / `test_complex_value_card`;
the structural form rejects both.
