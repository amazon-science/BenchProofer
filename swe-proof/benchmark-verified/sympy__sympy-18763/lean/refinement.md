# refinement.md — sympy__sympy-18763

Maps every operation in `implementation_renderRestriction` to its `patch.diff`
counterpart. Tags: **R** (type refinement), **A-consumed** (proof uses an axiom's
property), **A-reference** (deep model validated == real callee by G-AX), **I**
(identical concrete op). Every step is R, A, or I.

## Modeled function: `renderRestriction` (`_print_Subs`)

Post-patch repo code (`patch.diff`):
```python
def _print_Subs(self, subs):
    expr, old, new = subs.args
    latex_expr = self._print(expr)
    latex_old = (self._print(e) for e in old)
    latex_new = (self._print(e) for e in new)
    latex_subs = r'\\ '.join(
        e[0] + '=' + e[1] for e in zip(latex_old, latex_new))
    return r'\left. \left(%s\right) \right|_{\substack{ %s }}' % (latex_expr,
                                                     latex_subs)
```

Lean impl (`implementation_renderRestriction`):
```lean
def implementation_renderRestriction
    (inner : String) (lhs rhs : List String) : String := Id.run do
  let latexSubs := String.intercalate subsSep (subsEntries lhs rhs)
  return "\\left. \\left(" ++ inner ++ "\\right) \\right|_{\\substack{ "
    ++ latexSubs ++ " }}"
```

| # | Lean op | patch.diff / real-code counterpart | tag | justification |
|---|---|---|---|---|
| 1 | `inner : String` input | `latex_expr = self._print(expr)` | **R** | the recursive markup of the body is produced upstream by the unchanged renderer; the fix does NOT change it. It is taken verbatim as a string input (caller-supplied value), mapping.md bijection. |
| 2 | `lhs : List String`, `rhs : List String` inputs | `latex_old = (self._print(e) for e in old)`, `latex_new = (self._print(e) for e in new)` | **R** | the per-assignment rendered LHS/RHS token streams, again from the unchanged renderer, taken as string-list inputs. |
| 3 | `subsEntries lhs rhs = (lhs.zip rhs).map (fun p => p.1 ++ "=" ++ p.2)` | `(e[0] + '=' + e[1] for e in zip(latex_old, latex_new))` | **I** | `zip` truncates to the shorter operand exactly as `List.zip`; `e[0] + '=' + e[1]` ↔ `p.1 ++ "=" ++ p.2`. |
| 4 | `String.intercalate subsSep (...)` with `subsSep = "\\\\ "` | `r'\\ '.join(...)` | **I** | `str.join` with separator `\\ ` (two backslashes + space) ↔ `String.intercalate "\\\\ "`. (Lean `"\\\\ "` is the 3-character string backslash,backslash,space — the same bytes as the Python raw literal `r'\\ '`.) |
| 5 | `return "\\left. \\left(" ++ inner ++ "\\right) \\right|_{\\substack{ " ++ latexSubs ++ " }}"` | `return r'\left. \left(%s\right) \right|_{\substack{ %s }}' % (latex_expr, latex_subs)` | **I** (the changed op) | **the fixed operation.** The post-patch format string wraps the body `%s` in `\left(...\right)`; the Lean assembly appends the literal fragments `\left. \left(`, then `inner`, then `\right) \right|_{\substack{ `, then the joined assignments, then ` }}`. Character-for-character identical to the `%`-substitution of the post-patch template. |

All impl-region ops are **R/I** — there is NO A-tagged (axiom) content, so the
impl is NOT all-A-tagged: `conf_skip = false`, and `conformance_check.py`
mechanically differential-tests the R/I shadow against an in-process replica of
the post-patch `%`-format assembly over ≥1e5 fuzzed inputs.

## Soundness check (verify ⟹ correct)

- `problem_spec_renderRestriction inner lhs rhs result := result = "\left. \left("
  ++ inner ++ "\right) \right|_{\substack{ " ++ intercalate subsSep (subsEntries
  lhs rhs) ++ " }}"` pins the result by FULL string equality to an input-grounded
  expression — directive 5 (frame): every fragment of the output is determined by
  the inputs (`inner`, `lhs`, `rhs`). No output component is left unconstrained;
  no ungrounded oracle (directive 8) — the postcondition is dischargeable only by
  producing the actual assembled string.
- The prepatch impl emits `"\left. " ++ inner ++ " \right|_{\substack{ " ++ …`
  (the body placed directly, NOT inside its own `\left(...\right)` group). It
  violates the spec for EVERY input (the literal prefix differs: `\left. \left(`
  vs `\left. ` and the body is not closed by `\right)`), in particular on the
  F2P discriminating case `inner = "- x + y"`, where it yields
  `\left. - x + y \right|_{\substack{ x=1 }}` but the spec requires
  `\left. \left(- x + y\right) \right|_{\substack{ x=1 }}`. Its carried gold proof
  (`rfl`) cannot close (G-DIFF/G-PANEL): the two string literals are not
  definitionally equal.
- This discriminating case is exactly the FAIL_TO_PASS test (`test_latex_subs`):
  `latex(3*Subs(-x+y, (x,),(1,)))` must equal
  `r'3 \left. \left(- x + y\right) \right|_{\substack{ x=1 }}'` — the body must be
  parenthesized so the surrounding `3 *` does not bind to only the first term.
- G-CONF confirms the R/I shadow == an in-process replica of the post-patch
  `%`-format assembly over hand-picked edge cases (empty `inner`, unequal-length
  `lhs`/`rhs`, strings containing backslashes/braces) plus ≥1e5 fuzzed inputs.
