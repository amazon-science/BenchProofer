# mapping.md — sympy__sympy-22080

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 3f8c8c2377cb8e0daaf8073e8d03ac7d87580813`, states the type
abstraction, and gives the provenance of each callee the deep model is validated
against (G-AX / axiom_check.py).

Repo files under change: `sympy/printing/precedence.py`,
`sympy/printing/codeprinter.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `remainder_operand_level()` | the precedence assigned to a `Mod` node by `precedence(item)` (`sympy/printing/precedence.py:118`) via the `PRECEDENCE_VALUES` table (`precedence.py:27-51`) | modeled changed site A: the new `"Mod": PRECEDENCE["Mul"]` entry (gold adds it at `precedence.py:42-43`) |
| `negated_single_operand_enclosed(factor_strength)` | the `len(a)==1 and sign=="-"` branch of `CodePrinter._print_Mul` building `a_str` (`sympy/printing/codeprinter.py:454-490`, gold edits the `a_str = [...]` line at `codeprinter.py:490`) | modeled changed site B: the single negated factor's parenthesization decision |
| `negated_remainder_is_enclosed()` | the composite rendering of `-Mod(x,y)` (e.g. `PythonCodePrinter.doprint(-Mod(x,y))`, `sympy/printing/pycode.py:235` `_print_Mod` + `_print_Mul`) | the F2P observation `-(x % y)` tying both sites |
| `encloses(operand_level, cutoff, strict)` | the `parenthesize(item, level, strict=False)` predicate (`sympy/printing/str.py:33-37`) | pure spec: the parenthesization rule |
| `leading_minus_cutoff()` | the level `0.5*(PRECEDENCE["Pow"]+PRECEDENCE["Mul"])` the gold passes to `parenthesize` (`codeprinter.py` new branch) | pure spec: the unary-minus binding strength (= 55) |
| `level_additive/level_multiplicative/level_power/level_function()` | `PRECEDENCE["Add"/"Mul"/"Pow"/"Func"]` (`precedence.py:6-21`) = 40/50/60/70 | pure spec: the named binding strengths |

Pre-patch repo facts the change relies on (for the refinement audit, not
referenced from the consumer spec view):
- pre-patch there is NO `"Mod"` key in `PRECEDENCE_VALUES`, so `precedence(item)`
  walks `Mod`'s MRO (`Mod` subclasses `Function`) and returns
  `PRECEDENCE["Func"]` = 70 (`precedence.py:129-135`).
- `precedence_Mul(item)` (`precedence.py:61-64`) returns `PRECEDENCE["Add"]` (40)
  when `_coeff_isneg(item)`, so for a leading-minus product the pre-patch level
  `prec = precedence(expr)` collapses to 40.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `PRECEDENCE` dict entries (int) | `level_*()` int constants | identical ints 40/50/60/70 |
| `0.5*(PRECEDENCE["Pow"]+PRECEDENCE["Mul"])` = `55.0` (float) | `leading_minus_cutoff()` = `(60+50)//2` = `55` (int) | exact: even sum ⇒ integer midpoint == float midpoint; only used in `precedence(item) <(=) level` comparisons against integer precedences, so every comparison outcome is identical. The tested behaviour is precision-independent — integer carrier is faithful, no `--float-encoding`. |
| `precedence(item)` dispatcher | the relevant `level_*()` constant / the `factor_strength` parameter | the dispatcher returns the `PRECEDENCE`/`PRECEDENCE_VALUES` entry; model names it directly |
| `parenthesize(item, level, strict=False)` returning `"(%s)" % ...` vs bare | `encloses(operand_level, cutoff, strict)` returning `bool` (paren present?) | the printed wrapping is observed structurally (paren presence); `encloses` is the boolean decision |
| a SymPy expression node | its integer binding strength only (the sole field the patch reads) | rich object → the one touched field (`precedence(item)`) |

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

There is **no consumed `@ContractOnly` axiom** (the `axioms` region is empty).
Both changed operations are modelled **deeply** (A-references) and validated ==
the real callees out-of-band.

### 3.1 `remainder_operand_level` ↔ `precedence(Mod(...))` (A-reference)
**Callee:** `sympy.printing.precedence.precedence` on a `Mod` node, post-patch.
The gold adds `"Mod": PRECEDENCE["Mul"]` to `PRECEDENCE_VALUES`
(`precedence.py:42`), so `precedence(Mod(a,b)) == PRECEDENCE["Mul"] == 50`.
Source: `precedence.py` `PRECEDENCE = {... "Mul":50, "Pow":60, "Func":70 ...}`
and the dispatcher loop over `item.__class__.__mro__` consulting
`PRECEDENCE_VALUES`. G-AX runs the real `precedence(Mod(x,y))` and asserts it
equals `PRECEDENCE["Mul"]` (= `level_multiplicative()`); it FAILS pre-patch (returns 70).

### 3.2 `negated_single_operand_enclosed` / `leading_minus_cutoff` / `encloses` ↔ `_print_Mul` + `parenthesize` (A-reference)
**Callee:** `CodePrinter._print_Mul` single-factor leading-minus branch
(`codeprinter.py`, gold) calling `StrPrinter.parenthesize(item, level,
strict=False)` (`str.py:33-37`):
```python
def parenthesize(self, item, level, strict=False):
    if (precedence(item) < level) or ((not strict) and precedence(item) <= level):
        return "(%s)" % self._print(item)
    else:
        return self._print(item)
```
with `level = 0.5*(PRECEDENCE["Pow"]+PRECEDENCE["Mul"])` (= 55.0, strictly
between Mul=50 and Pow=60). So the factor is wrapped iff `precedence(item) <= 55`.
`encloses(s, 55, False)` is exactly this predicate; `leading_minus_cutoff()` is the
threshold. **Flag/configuration dependency:** the default `strict=False` (the
gold calls `parenthesize` with no `strict` argument); G-AX exercises that
configuration. G-AX renders one operand per strength class through the REAL
printer and asserts the wrap/bare decision (presence of wrapping parens) matches
the model decision computed from the operand's REAL `precedence`:
remainder (50)→wrap, product (50)→wrap, power (60)→bare, function (70)→bare.

**Soundness check (G-AX):** `axiom_check.py` imports only `sympy` (the project
under test, the very code the gold patch edits), runs in the patched / gold
container. It asserts: (a) the named `PRECEDENCE` constants are 40/50/60/70;
(b) `precedence(Mod(x,y)) == PRECEDENCE["Mul"]`; (c) the real threshold `55.0` is
strictly between Mul and Pow and equals the model midpoint; (d) the real
printer's wrap decision == the model decision on each strength class (structural
paren presence, no value-proxy double-mask); (e) all six FAIL_TO_PASS rendering
observations verbatim (`-(x % y)`, `(-x) % y`, `x % 2`, `-(x*x*x*x)`,
`-(x*x) + x*x*x*x`, `pow(x, i) - (x*x)`). Exit 0 iff sound; it FAILS on the
unpatched tree (precedence(Mod)=70), confirming it discriminates the fix.

## G-CONF (differential conformance)

`conformance_check.py` refutes the R/I refinement leg: the impl regions of
`model.py` copied **verbatim** (contracts stripped) vs the **REAL patched** repo
functions, **called** — never transliterated. Pinned fuzz seed: **`SEED = 22080`**.

**Oracle (all called, in the gold-patched container):**
- `sympy.printing.precedence.precedence` on a `Mod` node (§1 site A)
- `sympy.printing.codeprinter.CodePrinter._print_Mul` — the post-patch
  `len(a)==1 and sign=="-"` branch (§1 site B)
- `sympy.printing.str.StrPrinter.parenthesize` (`str.py:33-37`), the predicate
  the new branch consults (backs the `encloses` @Pure helper)
- `CodePrinter.doprint` on `-Mod(a,b)` (§1 composite / F2P observation)

The single thing the shadow does not model — the rendering of the inner factor —
is taken from the real printer (`printer._print(factor)`), the unchanged A-tagged
context, so the diff stays pointed at the R/I leg.

**Type bridge (§2 inverted).** Abstract `int` binding strength → real operand:
natural operands (`Mod`, `Pow`, function applications, products, sums) have their
level *read back* through the real `precedence()` dispatcher; levels no natural
node exhibits are reached with a `Symbol` subclass carrying a `precedence`
attribute, which the real dispatcher honours via its `hasattr(item,"precedence")`
fast path (`precedence.py:114-115`) — and the level is still re-read through
`precedence()` before reaching the shadow. The shadow's `bool` is bridged back to
text the way the patched code assembles it (`"-(" + inner + ")"` vs `"-" + inner`)
and compared byte-wise against real `_print_Mul` output, so assembly is diffed too.

**Input domain — finite, enumerated exhaustively.** The `Requires` of
`negated_single_operand_enclosed` is `40 <= operand_level <= 70`: 31 integer
points. All 31 are enumerated (× 2 real printer subclasses = 62 cases), which
pins the real cut-off exactly — 40..55 must enclose, 56..70 must not — then fuzz
re-covers the same space to reach the count. `encloses` is additionally checked
against real `parenthesize` on the exhaustive 31×31×{False,True} grid (leg D,
1922 cases): leg B alone only ever passes `cutoff=55`/`strict=False`, so without
leg D the helper's other two parameters would go untested.
Boundary-first: the F2P shapes (`-Mod(x,y)`, `Mod(-x,y)`, `Mod(x,2)`, expand-pow
`-(x*x*x*x)`), atoms, and the cut-off neighbours 54/55/56. Every impl branch is
counted and the script self-fails if any branch is never taken or the count falls
short (no silent shortfall).

**Branch membership is never inferred from the oracle's output.**
`_negated_single_factor` mirrors the real `_print_Mul` prologue
(`codeprinter.py:456-488`) line for line via the repo's own helpers
(`as_coeff_Mul`, `_keep_coeff`, `as_ordered_factors`) — note `2*exp(x)` keeps its
numeric coefficient as a SEPARATE factor, so `len(a)==2` and the modeled branch
is correctly NOT taken there. For an input that IS in the branch, a rendering
matching neither modeled assembly is a FAILURE, not a skip, so a disagreement
cannot hide as an out-of-domain skip. The carrier is also re-read back through
the real `precedence()` before reaching the shadow, so a bridge that failed to
take effect cannot pass silently.

**Extended carrier (documented, counted separately).** The expand-pow F2P operand
`UnevaluatedExpr(x*x*x*x)` has real precedence `49.5` — non-integer, hence outside
the model's declared `int` carrier (§2). It is neither dropped nor rounded: the
real float is fed straight into the verbatim `encloses`, which is exactly the R
refinement §2 claims (only comparison outcomes against the threshold matter).
Reported as `extended_carrier_samples`, excluded from the in-Requires total (so
they cannot pad the count).

**Recorded result:** **100,000** in-Requires inputs (2,045 boundary; per leg
A=14,688 B_level=35,768 B_natural=18,246 C=29,376 D=1,922; all 31 levels
exercised) + 21,290 extended-carrier, **0 disagreements**, exit 0.

**Capable of failing — controls run.** Against the **unpatched** tree it FAILS as
it must (`precedence(Mod)` 70 vs the model's 50; `doprint(-Mod(x,y))` `'-x % y'`
vs `'-(x % y)'`). Six mutants of the shadow were each killed, confirming every
leg is load-bearing: remainder level 50→70 (the pre-patch value), 50→51, cut-off
55→60, `strict` False→True, and both comparison operators of `encloses` flipped.
The last three differ from the real code only AT the boundary level 55 and are
caught precisely because the finite domain is enumerated exhaustively rather
than sampled.
