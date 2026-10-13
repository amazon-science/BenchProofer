# mapping.md — sympy__sympy-22080

## Instance
- repo: sympy/sympy
- base_commit: b506169ad727ee39cb3d60c8b3ff5e315d443d8e (the materialized worktree)
- modeled function: the product-expression renderer for code printers
  (`CodePrinter._print_Mul`), `sympy/printing/codeprinter.py`
- spec_provenance: cold

## Symbol binding (file:line @ base_commit)

| Lean symbol | Python | location @ base_commit |
|---|---|---|
| `implementation_renderProduct` | tail of `_print_Mul(self, expr)` (from the `a_str` computation through the three return branches), with the unchanged denominator pipeline (`b_str` rendering + `pow_paren` wrapping) R-abstracted into the `den` input | `sympy/printing/codeprinter.py:487`–`:507` |
| `sign` (input) | `sign = "-"` / `sign = ""` (set from `c < 0`) | `sympy/printing/codeprinter.py:456`–`:461` |
| `num` (input: rendered + strength) | `a` (numerator factor list) rendered by `self.parenthesize(x, …)` | `sympy/printing/codeprinter.py:487` |
| `den` (input: fully rendered texts) | `b_str` AFTER the unchanged `b_str = [self.parenthesize(x, prec) for x in b]` rendering AND the unchanged `pow_paren` group-wrapping loop (`for item in pow_paren: … b_str[b.index(item.base)] = "(%s)" % …`, the #14160 guard) | `sympy/printing/codeprinter.py:495`, `:497`–`:500` |
| `prec` (input) | `prec = precedence(expr)` | `sympy/printing/codeprinter.py:454` |
| numerator parenthesization (changed) | the `if len(a) == 1 and sign == "-": a_str = [self.parenthesize(a[0], 0.5*(PRECEDENCE["Pow"]+PRECEDENCE["Mul"]))] else: a_str = [self.parenthesize(x, prec) for x in a]` block (post-patch) | `sympy/printing/codeprinter.py:487`–`:494` |
| `negSingleLevel = 55` | `0.5*(PRECEDENCE["Pow"]+PRECEDENCE["Mul"]) = 0.5*(60+50)` | `sympy/printing/codeprinter.py:493`; `sympy/printing/precedence.py:6`–`:21` |
| denominator three-way tail | `if not b: … elif len(b) == 1: … else: …` (`len(b) == len(b_str)`, so the branch is decided by `den.length`) | `sympy/printing/codeprinter.py:502`–`:507` |

## `self.parenthesize` contract (the parenthesization rule, R-abstracted)

`StrPrinter.parenthesize(self, item, level, strict=False)` (`sympy/printing/str.py:33`):
```python
if (precedence(item) < level) or ((not strict) and precedence(item) <= level):
    return "(%s)" % self._print(item)
else:
    return self._print(item)
```
With the default `strict=False` this is exactly: **wrap iff `precedence(item) <= level`**.
The Lean `parenFactor level f := if f.strength ≤ level then "(" ++ f.text ++ ")" else f.text`
is a byte-faithful model of that branch, where `f.strength = precedence(item)` and
`f.text = self._print(item)` are the R-abstracted upstream results. `parenFactor`
is applied only to numerator factors: the fix changes only the numerator's
comparison level; the denominator rendering is unchanged (below).

## The denominator pipeline is R-abstracted (the modeling boundary)

Between the changed `a_str` block and the three return branches the source runs
an UNCHANGED denominator pipeline:

```python
b_str = [self.parenthesize(x, prec) for x in b]
# To parenthesize Pow with exp = -1 and having more than one Symbol
for item in pow_paren:                     # the #14160 guard
    if item.base in b:
        b_str[b.index(item.base)] = "(%s)" % b_str[b.index(item.base)]
```

Neither line is touched by the gold patch, and the numerator fix does not feed
into it. The model therefore takes the denominator as a list of FULLY RENDERED
texts (`den : List String` = the final `b_str`), exactly as the return branches
consume it. This matters for faithfulness: e.g. `ccode(Mul(-2, x,
Pow(Mul(y, y, evaluate=False), -1, evaluate=False), evaluate=False))` is
`-2*x/(y*y)` — the single denominator entry's text is `"(y*y)"` because the
`pow_paren` loop wrapped it; a model that re-rendered the denominator from
(strength, text) pairs with `parenFactor prec` would emit `-2*x/y*y` (verified
against the real repo at base_commit, patch applied). `len(b_str) == len(b)`
always (the loop rewrites entries in place), so the three-way tail branch is
decided by `den.length` exactly as by `len(b)`.

## The second patched site (`precedence.py`)

The gold patch also adds `"Mod": PRECEDENCE["Mul"]` to `PRECEDENCE_VALUES`
(`sympy/printing/precedence.py:43`). Empirically (verified at base vs patched):
this edit has **no standalone observable printer behavior** — with only this edit
applied, `_print_Mod`/`_print_Mul` output is unchanged for the issue's cases.
Its sole effect is to lower the binding strength reported by `precedence()` for a
`Mod` factor from `70` (the default `Func` strength) to `50` (`Mul`). That number
is consumed *as an input* by `_print_Mul`'s `parenthesize` comparison: it is the
`strength` of a `Mod` numerator factor. The two edits are coupled — both are
required to fix `-Mod(x, y)` → `-(x % y)`:

  - `-Mod(x, y)`: `sign = "-"`, `num = [Mod(x,y)]` (single factor). Post-patch the
    factor is compared against `negSingleLevel = 55`. Its strength must be `≤ 55`
    to be wrapped. With the OLD strength `70` it would NOT wrap (`70 > 55`); with
    the NEW strength `50` it wraps → `-(x % y)`. So the `_print_Mul` threshold
    change alone is insufficient for `Mod`; the precedence edit supplies the
    strength `50` that the threshold then captures.
  - `-x**4` (after pow-expansion → `-x*x*x*x`, a single factor of strength `49.5`):
    OLD code compared against `prec = precedence(-x*x*x*x) = 40`, so `49.5 > 40` →
    no wrap → `-x*x*x*x`. NEW code compares against `55`, so `49.5 ≤ 55` → wrap →
    `-(x*x*x*x)`. Fixed by the `_print_Mul` edit alone (no `Mod` involved).

Both behaviors are the SAME modeled function (`_print_Mul`'s numerator
parenthesization); the precedence-table edit only changes an *input strength
value*. Therefore the bundle models one function and carries the strength values
as R-abstracted inputs; mapping.md records that a `Mod` numerator factor has
post-patch strength `50` (and pre-patch `70`), and a pow-expanded power product
has strength `49.5`.

## Lean ↔ Python type bijection (used by G-CONF)

`_print_Mul`'s tail consumes: the leading `sign` string, the product's own
precedence `prec`, the numerator factor list (each factor contributes
`precedence(item)` — its strength — and `self._print(item)` — its text), and the
fully rendered denominator texts `b_str` (post `pow_paren`).

| Python value | Lean carrier |
|---|---|
| `sign : str` (`""` or `"-"`) | `sign : String` |
| `prec = precedence(expr) : number` | `prec : Rat` |
| numerator factor `x`: `(precedence(x), self._print(x))` | `Factor` `⟨strength, text⟩` in `num : List Factor` |
| denominator text `b_str[i]` (post `pow_paren`) | `String` in `den : List String` |
| `self.parenthesize(item, level)` (default `strict=False`) | `parenFactor level ⟨precedence item, _print item⟩` |
| `0.5*(PRECEDENCE["Pow"]+PRECEDENCE["Mul"])` = `55` | `negSingleLevel : Rat := 55` |
| `'*'.join(a_str)` | `String.intercalate "*" numStr` |
| `sign + '*'.join(a_str)` (no denom) | `sign ++ body` |
| `sign + '*'.join(a_str) + "/" + b_str[0]` (1 denom) | `sign ++ body ++ "/" ++ den.headI` |
| `sign + '*'.join(a_str) + "/(%s)" % '*'.join(b_str)` (≥2 denom) | `sign ++ body ++ "/(" ++ String.intercalate "*" den ++ ")"` |

Note: `a = a or [S.One]` guarantees `len(a) >= 1`, so the numerator list is never
empty. The `len(a) == 1` guard in the patched branch maps to `num.length = 1`.

## Callee provenance + flag deps
- `precedence(item)` / `self._print(item)` / `self.parenthesize` — UNCHANGED
  callees (the `parenthesize` body itself is unchanged; only the `level` argument
  passed for the lone-negated numerator case changed). The rendered text and the
  numeric strength are taken as INPUTS to the model (R-abstraction), exactly as
  caller-supplied values — NOT axiomatized. G-AX has nothing to validate →
  axiom_check.py is a skip stub.
- The denominator pipeline (`b_str` rendering + `pow_paren` loop) — UNCHANGED
  code upstream of the modeled decision; its output texts are the R-abstracted
  input `den : List String` (see "denominator pipeline" section). No
  `opaque`/`axiom` callee.
- The `precedence.py` `"Mod"` entry is an unchanged-callee *data* change surfaced
  as the strength input value `50` for a `Mod` factor (documented above); no
  `opaque`/`axiom` callee.
- No flag-dependent callees.

## G-CONF fuzz seed
- pinned seed: `22080`
- fuzz domain: `sign ∈ {"", "-"}`; `prec` drawn from the real precedence weights
  `{40, 49.5, 50, 55, 60, 70, 1000}` plus random rationals; `num` lists (incl.
  the `num.length == 1` case) of factors with strength drawn from the same
  weight set and random short rendered-text strings (incl. pre-parenthesized,
  with `*`, `/`, special chars); `den` lists of random rendered texts (incl.
  empty, single, multi, and pow_paren-style pre-wrapped `"(y*y)"`). ≥10^5
  samples. The R/I shadow of the impl is diffed against an in-process replica of
  the post-patch `_print_Mul` tail.
