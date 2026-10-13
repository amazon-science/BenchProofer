# mapping.md — sympy__sympy-21612

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = b4777fdcef467b7132c055f8ac2c9a5059e6a145`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and gives
the provenance of the modeled observations.

Repo file under change: `sympy/printing/str.py` (the `StrPrinter`).

## 0. The one thing to read first — how a bracket request is LOCATED

The real function does not wrap a factor's text at the factor's own position. It
builds a list `pow_paren` of the reciprocal factors that need protective
brackets, and then, at `str.py:354-356`, satisfies each request with

```python
for item in pow_paren:
    if item.base in b:
        b_str[b.index(item.base)] = "(%s)" % b_str[b.index(item.base)]
```

`b.index(item.base)` is a VALUE-equality lookup returning the FIRST occurrence.
So a request names an *inner expression*, not a slot, and is satisfied at the
earliest slot of `b` holding that expression. Two denominator slots holding
EQUAL inner expressions therefore raise two requests that both resolve to the
earlier slot: that slot is wrapped TWICE and the later slot is left bare. The
loop is also cumulative — each iteration re-reads `b_str`, so a second request
naming an already-wrapped position wraps the wrapping.

`b` additionally holds slots that are NOT candidates at all: the `apow(item)`
results for factors whose exponent is not `-1` (`str.py:344`) and the
`Rational(item.q)` denominators (`str.py:349`). Those slots are never appended to
`pow_paren` and so never wrapped, but they DO occupy positions in `b` and can be
the value a request's `b.index` lookup lands on.

`Solution.lean` models exactly this: `bracketTargets` emits one request per
raising slot, each carrying the position `firstSlotWithKey f.innerKey all`, and
`applyWraps` folds those requests over the text list in order. `isReciprocal`
marks which slots can raise a request at all, and `innerKey` is the identity of
the slot's inner expression (equal keys ⟺ equal inner expressions), which is what
makes the lookup expressible.

None of this is changed by `patch.diff` — the patch touches only the gate at
`str.py:335-336` — so the base-commit function is authoritative about it and G-AX
grounds it there (§3).

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `bracketDenomFactors (slots : List DenomFactor)` | `StrPrinter._print_Mul` — `sympy/printing/str.py:249`; specifically the rendering of the denominator list `b`: the `pow_paren` gating at lines 335-338 and the request application at 354-356, feeding `b_str` / the `'%s/(%s)'` assembly at 358-363 | modeled changed function: produce the rendered text of every denominator slot, with the protective-bracket requests satisfied |
| `DenomFactor` (`rendered`, `shape`, `components`, `isReciprocal`, `innerKey`) | ONE ENTRY OF THE DENOMINATOR LIST `b` — any entry, not only the reciprocal ones: an `item.base` pushed at `str.py:342` (reciprocal), an `apow(item)` pushed at 344, or a `Rational(item.q)` pushed at 349 | the per-slot record of the five observations the rendering reads |
| `DenomFactor.rendered` | `self.parenthesize(b[k], prec, strict=False)` — the slot value's standard rendered text (`b_str[k]` before any request is satisfied), `str.py:351` | unchanged sub-render of the slot's inner expression |
| `DenomFactor.shape` | the *type* of the slot value: `product` ⟺ `isinstance(b[k], Mul)`, `power` ⟺ `isinstance(b[k], Pow)`, `simple` otherwise | the top-level shape of the inner expression |
| `DenomFactor.components` | `len(b[k].args)` — the number of top-level args of the inner expression (for a reciprocal slot this is `len(item.args[0].args)`, the quantity read at `str.py:335`) | the inner expression's top-level component count |
| `DenomFactor.isReciprocal` | whether this slot was pushed from the `item.exp is S.NegativeOne` branch (`str.py:342`), i.e. whether the slot is `item.base` for some reciprocal factor `item`. `True` there; `False` for an `apow(item)` slot (344) and for a `Rational(item.q)` slot (349) | only these slots can be appended to `pow_paren`, so only these can raise a request |
| `DenomFactor.innerKey` | an identity code for the slot value under `==`: `innerKey i == innerKey j` ⟺ `b[i] == b[j]`. This is precisely the equality `b.index(item.base)` / `item.base in b` use (`list.index` / `in` compare with `==`) | lets a request be located by the expression it names rather than by the slot that raised it |
| `firstSlotWithKey k slots` | `b.index(v)` for the slot value `v` with that key — the FIRST position of `b` holding an equal value; `b`'s length when `v not in b` (the `if item.base in b` guard at `str.py:355` skips the request, and `wrapAt` past the end wraps nothing) | resolve one request to a position |
| `bracketTargets all slots` | the list `[b.index(item.base) for item in pow_paren]` — one entry per raising slot, in slot order (`pow_paren` is appended to in the `args` loop, so its order is the slot order) | the requests, resolved to positions |
| `applyWraps` / `wrapAt` / `wrapText` | the `for item in pow_paren:` loop at `str.py:354-356` and its body `b_str[i] = "(%s)" % b_str[i]` | satisfy the requests in order, cumulatively over `b_str` |
| `slotTexts slots` | `b_str = [self.parenthesize(x, prec, strict=False) for x in b]` (`str.py:351`) | the slot texts before any request |
| `renderDenomFactors slots` | the value of `b_str` AFTER the `pow_paren` loop, i.e. the list consumed by the assembly at `str.py:358-363` | the modeled function's result |
| `needsBrackets`, `shapeIsCompound` (pure) | the post-patch gate at `str.py:335-336` under the `item.exp is S.NegativeOne` branch | pure spec: which slots raise a request |

The pre-patch repo behavior the change removes (refinement audit only, not in
the consumer spec view): the gate at `str.py:335-336` read
`isinstance(item.base, Mul)` — only a *product* inner expression raised a
request. The patch widens it to `isinstance(item.base, (Mul, Pow))` so a
reciprocal whose inner expression is itself a *power* (e.g. `1/y`, a
`Pow(y, -1)`) also raises one. The `len(item.base.args) != 1` conjunct is
unchanged by the patch and is preserved by `needsBrackets`'s `components != 1`;
the reciprocal branch it sits inside is preserved by `isReciprocal`; and the
request-resolution block at 354-356 is untouched, preserved by
`firstSlotWithKey` + `applyWraps`.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) and G-AX use to translate values between the
Lean value domain and the Python repo types. A wrong entry surfaces as spurious
G-CONF disagreements.

| repo reality | Lean carrier | bijection |
|---|---|---|
| the rendered denominator-slot text (a Python `str`) | `List Char` | `s` (Python str) ↔ `s.toList`-shaped `List Char`; `str` concat ↔ `List` `++`; the surrounding `'('`/`')'` ↔ `"(".toList`/`")".toList`; ASCII output is per-code-point exact |
| the denominator list `b`, in order | `List DenomFactor` | order-preserving; `len(b)` ↔ `slots.length`; `b[k]` ↔ `slots[k]` |
| `b_str`, in order | `List (List Char)` | order-preserving, same length as `b` |
| one denominator slot `b[k]` | `DenomFactor` | `rendered ↔ self.parenthesize(b[k], prec, strict=False)`; `shape ↔ type(b[k])`; `components ↔ len(b[k].args)`; `isReciprocal ↔ pushed from the exp==-1 branch`; `innerKey ↔ the ==-equivalence class of b[k]` |
| `isinstance(b[k], Mul)` | `shape = DenomShape.product` | the inner expression is a product |
| `isinstance(b[k], Pow)` | `shape = DenomShape.power` | the inner expression is a power (the NEW trigger) |
| neither (Symbol, Number, Function, …) | `shape = DenomShape.simple` | the inner expression is atomic / other |
| `len(b[k].args) != 1` | `components != 1` | inner expression has ≠ 1 top-level args |
| `item` appended to `pow_paren` (`str.py:337`) | `needsBrackets f = true` | this slot raises a protective-bracket request |
| `b.index(item.base)` (`str.py:355`) — first-occurrence VALUE lookup | `firstSlotWithKey f.innerKey all` | resolve the request to the position of the FIRST slot holding an equal inner expression. Equal-inner slots therefore co-target. |
| `item.base in b` false (`str.py:355`) | `firstSlotWithKey … = slots.length` (past the end) | no slot holds it; the request wraps nothing (`wrapAt` past the end is a no-op) |
| `for item in pow_paren: b_str[i] = "(%s)" % b_str[i]` (`str.py:354-356`) | `applyWraps (slotTexts slots) (bracketTargets slots slots)` | one wrap per raising slot, applied in slot order to the text produced so far; two requests naming the same position wrap that text twice |
| `"(%s)" % b_str[i]` | `wrapText` / `wrapAt … i` | wrap one slot's text in one bracket pair |

`Mul` and `Pow` are disjoint Python types, so `shape` is a faithful 3-way
classification of the slot value's top-level type. `innerKey` is a faithful model
of `==` on slot values in the only way the lookup uses it: as an equivalence whose
classes are the `==`-classes, which is exactly what `axiom_check.py` asserts
pairwise (`(codes[i] == codes[j]) == bool(b[i] == b[j])`). The carrier is
`List Char` because the operation assembles strings, and `List (List Char)`
because the operation's result is the whole `b_str` list.

The modeled function is the WHOLE denominator-slot rendering (`b_str` from `b`),
not just the gate: the request-resolution block is what makes the gate's decision
observable, and it is not expressible per-slot. The surrounding `_print_Mul`
machinery (numerator assembly, sign handling, the `'%s/(%s)'` join at 358-363,
and the `args`/`b` gathering loop) is unchanged by the patch and identical
pre/post, so it is out of the modeled altitude — common to both legs and
reproduced verbatim by the G-CONF oracle, which calls the real `_print_Mul`.

## 3. Observation provenance (kind-A-reference — checked by G-AX / axiom_check.py)

### 3.1 `DenomFactor` observations ↔ real denominator slots (A-reference)
`DenomFactor` is NOT a consumed axiom — no `axiom` about it is used by the proof;
it is a **structure** whose five fields are *observations* of a real SymPy
denominator slot. The spec borrows no soundness from an opaque contract:
`bracketDenomFactors` is proven purely structurally over whatever `DenomFactor`
values it is given. The A-reference obligations G-AX discharges are that these
observations, taken from the REAL slots inside `_print_Mul`, are well-defined, and
that the modeled rendering reproduces the real `_print_Mul`'s `b_str` wherever the
base-commit function is authoritative:

  * `rendered`     = `self.parenthesize(b[k], prec, strict=False)`;
  * `shape`        = `product` / `power` / `simple` by `type(b[k])`;
  * `components`   = `len(b[k].args)`;
  * `isReciprocal` = pushed from the `item.exp is S.NegativeOne` branch;
  * `innerKey`     = a code whose equality is exactly `==` on slot values;
  * the request trigger `needsBrackets = isReciprocal ∧ (components != 1) ∧
    shape∈{product,power}` matches the real patched gate, inside the reciprocal
    branch: `len(item.base.args) != 1 and isinstance(item.base, (Mul, Pow))`;
  * the request RESOLUTION `firstSlotWithKey` + cumulative `applyWraps` matches
    the real `b.index`-based loop at `str.py:354-356`, which the patch does not
    touch.

**Soundness check (G-AX):** `axiom_check.py` constructs a wide family of
unevaluated quotients over the real `StrPrinter` — whose denominator slots are
drawn from a small pool sampled WITH REPLACEMENT, so equal inner expressions
recur, and some of which are raised to an exponent other than `-1` so they are
non-reciprocal slots — reproduces `_print_Mul`'s unchanged gathering and assembly
scaffold, and asserts:

  * (observation soundness) for a reciprocal slot `item.base is item.args[0]` (so
    `len(item.args[0].args) == len(item.base.args)`); `shape ==
    isinstance(b[k], Mul/Pow/_)`; `components == len(b[k].args)`; `rendered ==
    self.parenthesize(b[k], prec, strict=False)` (the unchanged inner sub-render
    callee); and, pairwise over every pair of slots, `innerKey` equality ⟺ real
    `==` equality of the slot values — all read from the real objects;
  * (deep-model fidelity on unchanged-behaviour inputs) for every generated
    quotient in which NO slot's bracketing is changed by the patch (no reciprocal
    slot has a `power` inner with `components != 1`), the modeled
    `renderDenomFactors`, assembled through the unchanged scaffold, equals the
    string the REAL loaded base-commit `_print_Mul` produces. Because the family
    includes quotients whose slots hold EQUAL inner expressions, this grounds the
    request-RESOLUTION rule in the real function: the patch does not touch
    `str.py:354-356`, so base is authoritative there;
  * (non-vacuity of the widened gate) there exists a reciprocal `power` slot
    (`components != 1`) whose model gate (patched) raises a request but whose
    pre-patch gate (`Mul`-only) does not — so the modeled `power` trigger is the
    genuine behavioural change, not dead;
  * (non-vacuity of the resolution rule) among the inputs checked by the fidelity
    obligation there exists one with two raising slots sharing an `innerKey`, so
    the model wraps the earliest slot twice and leaves the later bare — otherwise
    the fidelity agreement would say nothing about the aliasing.

**Why G-AX does NOT assert the patched bracket against `_print_Mul`.** G-AX runs
against the UNPATCHED base_commit source (the harness applies patch.diff only for
G-CONF/G-RESOLVE, since axioms concern callees identical pre/post — gates.py
`gate_ax` calls the container WITHOUT `apply_gold`). Asserting the patched output
(`(1/y)`) against the base printer (which prints `1/y`) would be unsound; worse,
the bracketing GATE is the operation the patch CHANGES, and SPEC_GUIDE §0.7
forbids validating the changed op against the function under change. The fidelity
of the modeled gate against the **patched** `_print_Mul` is therefore G-CONF's
job (patch applied, ≥10⁵ inputs); G-AX validates the observation pipeline, the
unchanged-behaviour deep-model agreement (which DOES cover the unchanged
resolution rule), and the two non-vacuity witnesses. Imports only `sympy`. Sound
at base_commit (and also passes with the patch applied). Exit 0 iff sound.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`21612`** so the
consumer-side verdict (§11.3) is reproducible. The R/I shadow it builds
transliterates the whole pure surface of `bracketDenomFactors` — `needsBrackets`,
`firstSlotWithKey`, `wrapAt`, `bracketTargets`, `applyWraps`, `slotTexts`,
`renderDenomFactors`, one Python function per Lean `def` — reading
`rendered`/`shape`/`components`/`isReciprocal`/`innerKey` from the REAL slot
objects (the A-reference observations → taken from the real `StrPrinter`, not a
stand-in), and diffs the reassembled full `_print_Mul` output against the gold
patch's actual `_print_Mul`.

The shadow **does not reuse the real function's `pow_paren` list or its
`b.index(item.base)` lookup**. That lookup is precisely the behaviour the model
claims to reproduce, so borrowing it would make the check tautological: a model
with an idealized per-slot wrap would still agree, because the agreement would be
carried by the real code the shadow imported. The shadow instead builds its own
`isReciprocal` flags in the gathering loop and its own `innerKey` codes from the
slot values, and lets the transliterated model decide both WHICH slots raise a
request and WHERE each request lands. Measured: substituting the idealized
per-slot map back into this shadow produces immediate disagreements
(`x/(((y*z))*((y*z)))` vs the real `x/((((y*z)))*(y*z))`), so the check has teeth.

The fuzz family is correspondingly heavy on duplicate inner expressions: the
denominator slots of each generated quotient are drawn from a small pool sampled
WITH REPLACEMENT, and ~20% are raised to an exponent other than `-1` (the real
`apow` path, a non-reciprocal slot). Boundary cases include the F2P anchor
`x/(1/y)`, the #14160 anchor `-2*x/(y*y)`, both equal-inner witnesses
(`Mul(x, 1/(y*z), 1/(y*z))` → `x/((((y*z)))*(y*z))` and
`Mul(x, 1/(1/y), 1/(1/y))` → `x/(((1/y))*1/y)`), a three-fold co-targeted case, a
non-reciprocal slot aliasing a reciprocal one in both orderings, and equal-valued
inners written in different factor orders — over both `StrPrinter()` and
`StrPrinter({'order': 'none'})`.
