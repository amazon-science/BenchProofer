# mapping.md — astropy__astropy-14508

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = a3f4ae6cd24d5ecdf49f213d77b3513dd509a06c`, states the type
abstraction, and gives the provenance of each axiom (callee source + the exact
behaviour the axiom encodes).

Repo file under change: `astropy/io/fits/card.py`.

**Policy note (§0.7 library-routine oracle).** The operation the patch changes —
the float→text renderer `str(value)` — is modelled as an axiomatized oracle
(`shortestField`), validated executably by G-AX, rather than deeply
transliterated. This is permitted under SPEC_GUIDE §0.7: the renderer is a
self-contained stdlib primitive (CPython shortest round-tripping repr / dtoa)
the changed function delegates to, whose IEEE-754 / dtoa internals are
inexpressible in Velvet's fragment, so a deep model is genuinely impossible.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `formatFloatField (value : Float)` | `_format_float(value)` — `astropy/io/fits/card.py:1300` | the modeled changed function: render a float to a ≤20-char FITS value field |
| `shortestField (value)` *(axiom — A-reference / waived changed op)* | `str(value).replace("e","E")` — the renderer the patch switches TO, `card.py:1302` post-patch | the stdlib float→str primitive (Python's shortest round-tripping repr) the fix newly invokes; modelled as an opaque oracle whose properties are validated == the real callee by G-AX |
| `paddedField (value)` *(axiom — pre-patch renderer)* | `f"{value:.16G}"` + exponent normalization — the renderer the patch switches FROM, `card.py:1302-1315` pre-patch | the OLD fixed-precision primitive; present so `Solution_prepatch.lean` has a faithful buggy renderer; validated well-formed + non-minimal by G-AX |
| `parseDec (field)` *(axiom)* | `float(field.replace("E","e"))` — CPython stdlib `float()` parser | the value-reconstruction theory the round-trip property is stated over (inverse of decimal rendering) |
| `sigCount (field)` *(axiom)* | number of significant digits in a decimal string | structural count over the significand's digit run |
| `minSig (value)` *(axiom)* | fewest significant digits a decimal needs to round-trip `value` | property of the number; `sigCount(str(value))` — the shortest repr, by construction (see axiom_check.py) |
| `eIndex (field)` / `eIndexFrom` | `value_str.find("E")` — `card.py:1321` | pure spec helper: first index of the exponent marker `E` (sentinel `length` for "absent", playing the role of Python's `-1`) |

## 2. Type abstraction (R-refinements)

| repo reality | Lean carrier | bijection |
|---|---|---|
| `str` (`value_str`, the function's return) | `List Char` | `s[k]` ↔ `field[k]`; `len(s)` ↔ `field.length`; `str` slicing/`+` ↔ `List.take`/`List.drop`/`++`; the marker `"E"` ↔ `'E'`. Lean `List`/`Char` indexing is total/sound — no `List[int]` code-point workaround is needed. |
| `float` (`value`) | Lean `Float` (IEEE-754) | identity; the behaviour IS about how a real number is rendered. The renderer's dtoa internals are opaque (axiomatized); only its *properties* are used. |
| `value_str.find("E")` (`card.py:1321`) | `eIndex field` over `List Char` | first-occurrence of `'E'`; Python's `-1` "absent" ↔ Lean sentinel `field.length`, so the over-cap branch keys on `idx < length` (present) vs `idx ≥ length` (absent), matching `idx < 0` vs `idx >= 0`. |
| `value_str[:20]` (`card.py:1324`) | `vs.take 20` | character-for-character prefix |
| `value_str[:20-(str_len-idx)] + value_str[idx:]` (`card.py:1326`) | `vs.take (20 - (n - idx)) ++ vs.drop idx` | significand prefix `take` ++ exponent suffix `drop`; `str` `+` ↔ `List` `++` |

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `shortestField` ↔ `str(value).replace("e","E")` (A-reference; waived changed op)
**Callee:** CPython `str(float)` / `repr(float)`. Since Python 3.1 these produce
the **shortest decimal string that round-trips to the same IEEE-754 double**
(David Gay / Grisu / Ryū-class dtoa); the patch upper-cases the exponent marker
with `.replace("e","E")`. Source: CPython `Objects/floatobject.c` `float_repr` →
`PyOS_double_to_string(..., 'r', 0, ...)`; docs:
https://docs.python.org/3/tutorial/floatingpoint.html (repr is the shortest
string that round-trips). The axioms encode exactly the properties the proof
consumes:

  * `shortestField_roundtrip`: `parseDec (shortestField v) = v` — it round-trips;
  * `shortestField_minimal`: `sigCount (shortestField v) = minSig v` — it spends
    the minimal number of significant digits (the whole point of the change);
  * `shortestField_nonempty`: `1 ≤ length`;
  * `shortestField_suffix_short`: if an exponent marker `'E'` is present at index
    `k`, the suffix `E±NNN` is ≤ 5 characters (a finite double's decimal exponent
    is at most three digits), so the significand-trim arithmetic
    `20 - (n - idx)` is always ≥ 0.

Validated **== the real callee** by axiom_check.py (G-AX): it runs
`str(value).replace("e","E")` on boundary + ~280 000 fuzz finite floats (two
seeds), exact powers of two over `2**[-1074,1023]`, and subnormals, asserting
every property above. **Minimality is checked WITHOUT the latent `%g` bug** (see
§3.4): minimality is taken as `sigCount(str(v))` (shortest by construction) AND
cross-checked structurally (no strictly-shorter rendering round-trips).

### 3.2 `paddedField` ↔ `f"{value:.16G}"` (pre-patch renderer)
**Callee:** the pre-patch `_format_float` body — `f"{value:.16G}"` with the
exponent zero-padded to two digits. This primitive renders to a FIXED 16
significant digits regardless of how few the number needs, which is precisely the
defect (e.g. `0.009125` → `"0.009124999999999999"`). The axioms for `paddedField`
are deliberately WEAK — `paddedField_nonempty`, `paddedField_suffix_short` — and
crucially do NOT claim minimal significant digits and do NOT equate it to
`shortestField`. axiom_check.py confirms it is well-formed AND that it spends MORE
than `minSig` digits on the regression values, so the discriminator the pre-patch
skeleton fails on is a real property of the old renderer. (`f"{value:.16G}"` does
not even always round-trip, so the axiom correctly does NOT claim round-trip.)

### 3.3 `parseDec` ↔ `float(str)` (A — value-reconstruction theory)
**Callee:** CPython `float()` on a decimal string (upper `E` mapped back to `e`).
The inverse of decimal rendering; the round-trip postcondition
`parseDec (shortestField v) = v` is its defining use. G-AX evaluates
`float(field.replace("E","e"))` on every observed field.

### 3.4 `sigCount` / `minSig` (A — significant-digit theory)
`sigCount(field)` counts the significant digits of a decimal string's significand
(leading zeros and integer-form trailing zeros dropped; zero counts as one).
`minSig(value)` is the fewest significant digits any decimal reading needs to
round-trip `value`. The proof uses `sigCount (shortestField v) = minSig v`. G-AX
implements both and asserts the equality over the full corpus.

**`minSig` avoids the latent `%g` bug.** A naive `min_sig` computed as
`min{k : float(f"{value:.{k}g}")==value}` rounds the k-th digit by a rule that
DIVERGES from dtoa on dyadic values (`2**-24`, `2**-44`, `2**122`, subnormals),
reporting a spurious 17 where `str(value)` spends 16 — a false-positive failure.
axiom_check.py defines `minSig(v) = sigCount(str(v))` (the shortest repr, minimal
by construction) and additionally cross-checks minimality structurally: for every
`k < sigCount(str(v))`, no `k`-significant-digit rendering round-trips to `v`.
This is sound on dyadic values; the fuzz corpus explicitly sweeps `2**[-1074,1023]`
and subnormals to cover the bug class.

## 4. Domain note (finite floats) and over-cap branch test relevance

`_format_float` is only reached for finite floats: `inf`/`nan` are rejected with
`ValueError` by `Header.set` before formatting (`test_assign_inf_nan`, a P2P). The
`Float` model and all axioms are stated over this finite domain; axiom_check.py and
conformance_check.py fuzz only finite floats (`math.isfinite`).

**The 20-character over-cap branch IS observed by PASS_TO_PASS tests** (verified
against instance.json). Both scientific-notation trim values flow through the
`idx < length` exponent-preserving path:

| test | list | what it exercises |
|---|---|---|
| `test_floating_point_string_representation_card` | **F2P** | the headline regression: `0.009125` must render `"0.009125"` (4 sig digits), not the 16-digit `"0.009124999999999999"` — the minimality content of the fits-branch |
| `test_floating_point_value_card` | **P2P** | `-467374636747637647347374734737437.0` → `str` ≈ `-4.673...E+32` (22 chars) → must trim to `-4.6737463674763E+32` (20 chars, exponent suffix `E+32` kept) — the `idx < length` over-cap path |
| `test_complex_value_card` | **P2P** | a complex card whose parts render in scientific notation and trim with the exponent kept — same over-cap path |
| `test_assign_inf_nan` | **P2P** | `inf`/`nan` rejected upstream, fixing the finite domain |

The post-condition pins the over-cap content STRUCTURALLY against the exact
rendering: with no exponent marker the field is `shortestField value |>.take 20`;
with a marker at `idx` it is
`(shortestField value).take (20 - (n - idx)) ++ (shortestField value).drop idx`
(significand shortened, full exponent suffix kept). A length-only `length = 20`
post-condition would be too weak (an impl dropping the exponent or emitting 20
arbitrary chars would pass it yet fail the P2P scientific-notation tests).

## 5. G-CONF / G-AX fuzz seeds (pinned)

- axiom_check.py: seeds `14508` and `0xC0FFEE` (two distinct seeds), plus the
  deterministic powers-of-two sweep `2**[-1074,1023]`, subnormal sweeps, and
  the integer sweep `[-2000,2000]`.
- conformance_check.py: seed `14508`, ~122k finite floats incl. powers of two.
