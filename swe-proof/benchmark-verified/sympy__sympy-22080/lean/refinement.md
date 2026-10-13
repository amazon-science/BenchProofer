# refinement.md — sympy__sympy-22080

Maps every operation in `implementation_renderProduct` to its `patch.diff`
counterpart. Tags: **R** (type refinement), **A-consumed** (proof uses an axiom's
property), **A-reference** (deep model validated == real callee by G-AX), **I**
(identical concrete op). Every step is R, A, or I.

## Modeled function: `renderProduct` (tail of `_print_Mul`)

Post-patch repo code (`patch.diff`, `sympy/printing/codeprinter.py`):
```python
        a = a or [S.One]

        if len(a) == 1 and sign == "-":
            # Unary minus does not have a SymPy class, and hence there's no
            # precedence weight associated with it, Python's unary minus has
            # an operator precedence between multiplication and exponentiation,
            # so we use this to compute a weight.
            a_str = [self.parenthesize(a[0], 0.5*(PRECEDENCE["Pow"]+PRECEDENCE["Mul"]))]
        else:
            a_str = [self.parenthesize(x, prec) for x in a]
        b_str = [self.parenthesize(x, prec) for x in b]

        # To parenthesize Pow with exp = -1 and having more than one Symbol
        for item in pow_paren:
            if item.base in b:
                b_str[b.index(item.base)] = "(%s)" % b_str[b.index(item.base)]

        if not b:
            return sign + '*'.join(a_str)
        elif len(b) == 1:
            return sign + '*'.join(a_str) + "/" + b_str[0]
        else:
            return sign + '*'.join(a_str) + "/(%s)" % '*'.join(b_str)
```
plus, in `sympy/printing/precedence.py`, `"Mod": PRECEDENCE["Mul"]` added to
`PRECEDENCE_VALUES` (surfaced as the strength *input* `50` for a `Mod` factor).

Lean impl (`implementation_renderProduct`):
```lean
def implementation_renderProduct
    (sign : String) (prec : Rat) (num : List Factor)
    (den : List String) : String := Id.run do
  let mut numStr : List String := []
  if num.length = 1 ∧ sign = "-" then
    numStr := num.map (parenFactor negSingleLevel)
  else
    numStr := num.map (parenFactor prec)
  let body := String.intercalate "*" numStr
  if den.isEmpty then return sign ++ body
  else if den.length = 1 then return sign ++ body ++ "/" ++ den.headI
  else return sign ++ body ++ "/(" ++ String.intercalate "*" den ++ ")"
```

| # | Lean op | patch.diff / real-code counterpart | tag | justification |
|---|---|---|---|---|
| 1 | `sign : String` input | `sign` (`""`/`"-"` from `c < 0`) | **R** | the leading-sign decision is upstream of and unchanged by the fix; taken as a string input. |
| 2 | `prec : Rat` input | `prec = precedence(expr)` | **R** | the product's own precedence weight, produced by the unchanged `precedence`; taken as a numeric input. |
| 3 | `num : List Factor` (each `⟨strength, text⟩`) | `a` factor list, each factor's `(precedence(x), self._print(x))` | **R** | each numerator factor's rendered text and binding strength come from the unchanged recursive renderer / precedence lookup; taken as inputs. The `precedence.py` `"Mod"` edit changes only the *strength value* of a `Mod` factor (70→50), recorded in mapping.md as an input value — NOT a changed op in this function. |
| 4 | `den : List String` input | `b_str` AFTER the unchanged `b_str = [self.parenthesize(x, prec) for x in b]` rendering and the unchanged `pow_paren` group-wrapping loop (the #14160 guard) | **R** | the entire denominator pipeline is untouched by the patch and does not consume the fixed decision; its final texts (which may include pow_paren wrapping, e.g. `"(y*y)"` for `1/(y*y)`) are taken as inputs. `len(b_str) == len(b)` always, so `den.length` decides the tail branch exactly as `len(b)` does. |
| 5 | `parenFactor level f := if f.strength ≤ level then "(" ++ f.text ++ ")" else f.text` | `self.parenthesize(item, level)` (default `strict=False`): wrap iff `precedence(item) <= level` | **I** | byte-faithful model of the `parenthesize` branch with `strength = precedence(item)`, `text = self._print(item)`; applied only to numerator factors. The `parenthesize` body is unchanged by the patch. |
| 6 | `if num.length = 1 ∧ sign = "-" then num.map (parenFactor negSingleLevel) else num.map (parenFactor prec)` | `if len(a) == 1 and sign == "-": a_str = [self.parenthesize(a[0], 0.5*(PRECEDENCE["Pow"]+PRECEDENCE["Mul"]))] else: a_str = [self.parenthesize(x, prec) for x in a]` | **I** (the changed op) | **the fixed operation.** `negSingleLevel = 55 = 0.5*(60+50)`; the guard `num.length = 1 ∧ sign = "-"` ↔ `len(a) == 1 and sign == "-"`; the map over the (singleton-in-the-true-branch) numerator list ↔ the list comprehension. |
| 7 | `String.intercalate "*" numStr` | `'*'.join(a_str)` | **I** | join with `*`. |
| 8 | `if den.isEmpty then sign ++ body / else if den.length = 1 then sign ++ body ++ "/" ++ den.headI / else sign ++ body ++ "/(" ++ String.intercalate "*" den ++ ")"` | `if not b: … elif len(b) == 1: … else: … "/(%s)" % '*'.join(b_str)` | **I** | the three-way denominator tail, character-for-character, over the fully rendered `b_str` texts (`den`); `len(b) == len(b_str) == den.length`. |

All impl-region ops are **R/I** — there is NO A-tagged (axiom) content, so the
impl is NOT all-A-tagged: `conf_skip = false`, and `conformance_check.py`
mechanically differential-tests the R/I shadow against an in-process replica of
the post-patch `_print_Mul` tail over ≥10^5 fuzzed inputs.

## Modeling boundary note: the denominator is a rendered-text input

An earlier revision of this bundle modeled the denominator as `(strength, text)`
factors re-rendered inside the model with `parenFactor prec`. That was
UNFAITHFUL: the real tail also runs the `pow_paren` group-wrapping loop between
rendering and assembly, so e.g. `ccode` of `-2*x` times `1/(y*y)` (unevaluated
`Pow(Mul(y, y), -1)`) is `-2*x/(y*y)` — the denominator text arriving at the
return branches is `"(y*y)"`, not `"y*y"` (verified on the real repo at
base_commit + gold patch). Since neither `b_str` rendering nor the `pow_paren`
loop is changed by the patch, both belong upstream of the modeling boundary:
`den : List String` carries their combined output. This removes the divergence
without touching the modeled (changed) numerator decision.

## Modeling note: the two patched files are one modeled behavior

The gold patch touches two files but the observable behavior is a single
function's parenthesization decision:
- `codeprinter.py` adds the lone-negated-numerator special comparison level
  (`55`). This alone fixes `-x**4` → `-(x*x*x*x)` (the power product has strength
  `49.5 ≤ 55`).
- `precedence.py` adds `"Mod": Mul` (strength `70 → 50`). This alone fixes
  nothing observable; it only changes the strength *input* of a `Mod` factor so
  that, under the new `55` comparison level, `-Mod(x, y)` wraps (`50 ≤ 55`)
  giving `-(x % y)`.

Verified empirically at base_commit (each edit applied in isolation): the Mod
case needs BOTH edits; the power case needs only the codeprinter edit. The model
captures the `codeprinter.py` decision faithfully and carries the strength values
(incl. the `Mod` strength `50`) as R-abstracted inputs per mapping.md, so the
single `Solution_prepatch.lean` (which reverts the special comparison level)
exhibits the bug for every discriminating input — including the `Mod` factor at
strength `50` (pre-patch: compared against `prec = 40`, `50 > 40` → no wrap →
`-x % y`) and the power-product factor at strength `49.5` (pre-patch: `49.5 > 40`
→ no wrap → `-x*x*x*x`).

## Soundness check (verify ⟹ correct)

- `problem_spec_renderProduct sign prec num den result := result = renderProduct
  sign prec num den` pins the result by FULL string equality to an input-grounded
  expression — directive 5 (frame): every fragment of the output (the per-factor
  numerator parenthesization, the `*`-joined numerator, the `/`-denominator tail
  over the rendered texts) is determined by the inputs. No output component is
  unconstrained; no ungrounded oracle (directive 8) — the postcondition is
  dischargeable only by producing the actual assembled string via the modeled
  branch.
- The prepatch impl drops the lone-negated special case (uses `parenFactor prec`
  for the numerator unconditionally). On the discriminating input
  `sign = "-"`, `num = [⟨50, "x % y"⟩]`, `den = []`, `prec = 40` (the F2P
  `-(x % y)` case): the spec/post-patch requires comparison against `55`
  (`50 ≤ 55` → wrap → `-(x % y)`); the prepatch compares against `prec = 40`
  (`50 > 40` → no wrap → `-x % y`). Its carried gold proof (`split <;> rfl`)
  cannot close (G-DIFF/G-PANEL): the two assembled strings are not definitionally
  equal because the numerator-text branch differs.
- This discriminating behavior is exactly the FAIL_TO_PASS suite
  (`test_PythonCodePrinter`: `-Mod(x, y) → -(x % y)`;
  `test_create_expand_pow_optimization`: `-x**4 → -(x*x*x*x)`;
  `test_empty_modules`: `lambdify` of `-(x % y)` with `modules=[]`).
- G-CONF confirms the R/I shadow == an in-process replica of the post-patch
  `_print_Mul` tail over hand-picked edge cases (the issue's expressions,
  boundary strengths `55`/`56`, multi-factor numerators, all three denominator
  branches, a pow_paren-wrapped denominator text) plus ≥10^5 fuzzed inputs.
