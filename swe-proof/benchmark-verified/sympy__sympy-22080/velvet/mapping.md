# mapping.md — sympy__sympy-22080

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 3f8c8c2377cb8e0daaf8073e8d03ac7d87580813`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and gives
the provenance of each modeled callee.

Repo files under change: `sympy/printing/codeprinter.py`,
`sympy/printing/precedence.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `printNegatedFactor (k : OperandKind) (inner : List Char)` | the single-negated-factor branch of `CodePrinter._print_Mul` — `sympy/printing/codeprinter.py:453` (body line ~489), which emits `sign + '*'.join(a_str)` with `sign == "-"` and one numerator factor | the modeled changed function: how a leading unary minus parenthesizes its single factor |
| `opWeight : OperandKind → Int` *(deep model of the CHANGED behaviour)* | `sympy.printing.precedence.precedence` — `sympy/printing/precedence.py:118`, evaluated on the factor expression *under the patch* (Site P sets `Mod ↦ 50`); carried at **twice** the native value | pure spec: the *post-fix* binding strength for each operand kind, validated `precedence(e)*2 == opWeight(kind)` against the PATCHED renderer by conformance_check.py (G-CONF) |
| `negLevel : Int := 110` | the parenthesization level the patched `_print_Mul` passes for a single negative factor: `0.5*(PRECEDENCE["Pow"]+PRECEDENCE["Mul"]) = 55`, carried at twice (110) | pure spec: the unary-minus binding threshold |
| `needsParen (k : OperandKind)` *(deep model of the CHANGED behaviour)* | `Printer.parenthesize(item, level)` — `sympy/printing/str.py:33`: wraps iff `precedence(item) <= level` | pure spec: the *post-fix* wrap decision under the unary minus, validated against the PATCHED renderer's wrap by conformance_check.py (G-CONF) |
| `renderNeg (k) (inner)` | `sign + '*'.join(a_str)` with `sign="-"`, one factor (`'-' + (the parenthesized factor)`) | pure spec: assembly of the negated single factor |
| `inner : List Char` *(input — A-tagged callee output)* | `self._print(item)` — the recursive printing of the factor (unchanged callee); consumed as the input, no contract owed | the factor's own printed form |

The two gold edits, by site:

* **Site C (`codeprinter.py`)** — `_print_Mul` gains, for `len(a) == 1 and sign
  == "-"`, the branch `a_str = [self.parenthesize(a[0],
  0.5*(PRECEDENCE["Pow"]+PRECEDENCE["Mul"]))]` (level 55) instead of the generic
  `parenthesize(x, prec)` (where `prec == precedence(expr) == 40` for a negated
  product). Modeled by `negLevel = 110`.
* **Site P (`precedence.py`)** — `PRECEDENCE_VALUES` gains `"Mod":
  PRECEDENCE["Mul"]` (50), so `precedence(Mod(...))` drops from the inherited
  `Func` weight 70 to 50. Modeled by `opWeight .modOp = 100 (= 2*50)`.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the
Lean value domain and the Python repo types.

| repo reality | Lean carrier | bijection |
|---|---|---|
| the printed source fragment (a Python `str`) | `List Char` | `s` (Python str) ↔ `s.toList`-shaped `List Char`; `str` concat ↔ `List` `++`; the leading `"-"` ↔ `'-' :: …`; `"(" + s + ")"` ↔ `('(' :: l) ++ [')']` |
| the single numerator factor expression `a[0]` | `OperandKind` | the factor is classified by the shape distinctions §1 names: a `Mod` instance ↔ `.modOp`; a `Pow` ↔ `.power`; a `Mul` product ↔ `.mulCluster`; a `Function` call ↔ `.funcCall`; an `Atom` ↔ `.atomic`. A single `UnevaluatedExpr` wrapper is **transparent**: `precedence(UnevaluatedExpr(e)) == precedence(e) - 0.5` (repo `precedence.py::precedence_UnevaluatedExpr`), and no modeled strength lies in `(55, 55.5]` (the nearest above the threshold is `Pow = 60`), so the −0.5 shift never crosses the wrap threshold — `UnevaluatedExpr(e)` classifies to the kind of its inner `e` (e.g. `UnevaluatedExpr(x**2) ↔ .power`, NOT wrapped: `-x**2`; `UnevaluatedExpr(x*y) ↔ .mulCluster`, wrapped: `-(x*y)`). Nested wrappers (depth ≥ 2) accumulate −0.5 per level and could eventually cross the threshold, so they are out of the modeled Requires (G-CONF skips them). The bijection abstracts the factor to **only** its binding strength (the sole thing the change reads). |
| `precedence(e)` (a renderer binding strength, possibly a half-integer like 49.5) | `opWeight kind : Int` | `precedence(e)` ↔ `opWeight(kind) / 2`; equivalently `opWeight(kind) == precedence(e) * 2`. Order-only scaling by 2 keeps every modeled value an integer (decidable in the Lean kernel) while preserving all `<=` relations exactly (DECISIONS.md float-order note). |
| the parenthesize level `0.5*(Pow+Mul)=55` | `negLevel : Int := 110` | `55 * 2`. |

The change reacts to **nothing but** the factor's binding strength (`precedence`)
and the fixed unary-minus level; abstracting the factor to its `OperandKind`
(its strength class) is therefore faithful. The five modeled kinds cover every
factor shape the F2P tests and fuzz exercise; any other shape is out of the
modeled Requires (G-CONF skips it).

## 3. Callee provenance

### 3.1 `opWeight` / `needsParen` deep model — the CHANGED operation (checked by G-CONF, **not** G-AX)
The wrap decision for a single factor under a leading unary minus is exactly what
the gold patch changes (Site C raises the threshold; Site P lowers the
modular-remainder strength). It is modeled **deeply** by
`opWeight`/`needsParen`/`renderNeg` in the `pure` region; there is **no consumed
axiom and no A-reference**. The patched `_print_Mul` computes, for a single
negative factor `a[0]`:

```python
a_str = [self.parenthesize(a[0], 0.5*(PRECEDENCE["Pow"]+PRECEDENCE["Mul"]))]
# parenthesize wraps iff precedence(a[0]) <= 55
return "-" + a_str[0]
```

`opWeight(kind) == precedence(rep)*2` and `negLevel == 55*2`, so
`needsParen(kind) == (precedence(rep) <= 55) ==` the patched `parenthesize` wrap
decision. Site P feeds this: post-patch `precedence(Mod(..)) == 50` so
`opWeight .modOp == 100 <= 110` ⇒ wrapped (`-(x % y)`), where pre-patch
`precedence(Mod(..)) == 70 ⇒ 140 > 110` ⇒ unwrapped (`-x % y`, the issue).

**Why this is NOT a G-AX A-reference (directive 7).** `precedence`/`parenthesize`
are precisely the callees the patch *edits* (the `Mod` strength entry and the
unary-minus threshold are introduced by the gold diff). An A-reference must be an
**unchanged** outside callee; deep-modeling the *changed* op and checking it
against a real callee is forbidden, and is in any case impossible here: G-AX runs
`axiom_check.py` against the **unpatched** repo (`gate_ax` does not apply the gold
patch), where `precedence(Mod) == 70` and the threshold branch does not exist —
so the post-fix model could never agree there. The bundle therefore declares no
axiom and ships a G-AX **skip stub** (exit 0; `meta.json gates.G-AX.status =
"skip"`), the same pattern as the green `astropy__astropy-13033` bundle.

**Soundness check (G-CONF):** the deep model's fidelity to the *patched* behaviour
is exercised mechanically by `conformance_check.py`, which `git apply`s the gold
patch (the harness runs G-CONF with `apply_gold=True`) and then diffs the R/I
transliteration of `opWeight`/`needsParen`/`renderNeg` against the REAL patched
`pycode(-e)` over ≥10⁵ fuzzed single-negated-factor inputs (plus the exact F2P
expressions): `-(x % y)` for `-Mod(x, y)`, `-(x*x*x*x)` for the expand-pow ccode
case, etc. Zero disagreements ⇒ the model equals the patched renderer on the
tested factors. G-CONF runs against the patched repo, so it CAN and does observe
`precedence(Mod) == 50`; that is why this is the right gate for the changed op.

### 3.2 the inner factor printing `self._print(item)` (A-tagged, no contract)
The recursive printing of the factor that produces `inner` is unchanged by this
edit and is consumed as the input `inner` (G-CONF supplies the REAL renderer's
`pycode(factor)`). No property of it is owed a contract; it appears identically
on the shadow and oracle sides, so it is not a consumed axiom and carries no
soundness obligation beyond being the real callee.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`22080`** so the
consumer-side verdict (§11.3) is reproducible. The R/I shadow transliterates
`opWeight`/`needsParen`/`renderNeg` (R/I-tagged ops) to Python and leaves the
inner-factor printing as the real `pycode` callee (A-tagged → run real callee).
Inputs whose negation is not a single negated factor, or whose factor shape is
outside the five modeled kinds, are out of the changed branch's Requires and
skipped.
