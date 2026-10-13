# mapping.md — sympy__sympy-23262

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = fdc707f73a65a429935c01532cd3970d3355eab6`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and gives the
provenance of each modeled symbol. This bundle has **no axioms and no
A-references** (G-AX = skip; no `axiom_check.py`): the only changed op is the
function under spec itself, modeled deeply and validated by G-CONF.

Repo file under change: `sympy/utilities/lambdify.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `renderSequence (isList : Bool) (elems : List (List Char))` | the iterable branch of `_recursive_to_string(doprint, arg)` — `sympy/utilities/lambdify.py:948` (def), branch at lines 957-964 | the modeled changed function: render a sequence of already-rendered element texts into its delimited form |
| `renderSeq` *(deep model of the changed op)* | the body of that branch: `left + ', '.join(_recursive_to_string(doprint, e) for e in arg) + right` with the `(left, right)` delimiter selection (lines 958-964 post-patch) | pure spec: join element texts with comma-space and wrap in the kind's delimiters; deep CONCRETE model of the changed render step. NOT an axiom and NOT an A-reference — it models the function the patch changes (§0.7), so it is validated by G-CONF (patched tree), not G-AX |
| `joinComma` | `', '.join(...)` (line 964) | pure spec: the comma-space join, a sub-step of the render |

The element-rendering recursion (`_recursive_to_string` on `Basic`/
`MatrixOperations` via `doprint`, on `str` via passthrough, and on iterables
recursively) is UNCHANGED by the patch. It is the opaque input to the modeled
step: in `Solution.lean` the already-rendered element texts arrive as the
read-only `elems`; in the gate scripts the same recursion runs identically on
both sides (an R identity bridge), so it carries no soundness obligation.

The pre-patch repo code the change replaces (refinement audit only, not in the
consumer spec view): the tuple-unpacking assignments `left, right = "[]"` and
`left, right = "()"` (lines 958, 960), which split a two-character string into
its two characters — so the tuple closer was the bare `)` with no comma.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean value
domain and the Python repo types. A wrong entry surfaces as spurious G-CONF
disagreements (the falsifiability the plan §4 trust statement refers to).

| repo reality | Lean carrier | bijection |
|---|---|---|
| a rendered element text (a Python `str`, the return of `_recursive_to_string` on one element) | `List Char` | `s` (Python str) ↔ `s.toList`-shaped `List Char`; `len(s)` ↔ `l.length`; `str` concat ↔ `List` `++`; empty `str` ↔ `[]` |
| the ordered tuple/list of element texts (`[ _recursive_to_string(doprint, e) for e in arg ]`) | `List (List Char)` | positional: the `i`-th element text ↔ `elems[i]`; arity and order preserved |
| `isinstance(arg, list)` vs `isinstance(arg, tuple)` | `isList : Bool` | `True` ↔ `isList = true` (bracketed/list kind); `False` ↔ `isList = false` (parenthesized/tuple kind). The `else: raise NotImplementedError` arm is unreachable for `list`/`tuple` args and is out of the modeled domain (mapping.md §3). |
| the comma-space separator `', '` | `", ".toList` | the two code points `[',', ' ']`, inserted strictly between adjacent elements |
| list delimiters `('[', ']')` | `("[".toList, "]".toList)` | the bracket pair, unchanged by the patch |
| tuple delimiters `('(', ',)')` post-patch | `("(".toList, ",)".toList)` | the opening parenthesis and the closing delimiter `,)` — a comma BEFORE the closing parenthesis (the behavioural change) |

Lean `String`/`List Char` indexing is total and sound; the carrier is
`List Char` because the operation is per-code-point text concatenation.

## 3. Provenance of the modeled op — no axioms, no A-references (G-AX = skip)

### 3.1 `renderSeq` deep model ↔ the iterable branch of the changed function

**Symbol modeled:** `sympy.utilities.lambdify._recursive_to_string`, **the
function the gold patch changes**. The changed render step is modeled **deeply
and concretely** by `renderSeq` (with `joinComma`) in the `pure` region.
Post-patch body of the iterable branch:

```python
elif iterable(arg):
    if isinstance(arg, list):
        left, right = "[", "]"
    elif isinstance(arg, tuple):
        left, right = "(", ",)"
    else:
        raise NotImplementedError("unhandled type: %s, %s" % (type(arg), arg))
    return left + ', '.join(_recursive_to_string(doprint, e) for e in arg) + right
```

So for a `list` the result is `'[' + body + ']'` and for a `tuple` it is
`'(' + body + ',)'`, where `body` is the comma-space join of the element texts.
This is exactly `renderSeq isList elems` / `joinComma elems`. The trailing comma
in the tuple closer is the single behavioural change the F2P test observes:
a one-element tuple renders `'(t0,)'` (a tuple), not `'(t0)'` (a bare value).
Empirically confirmed against the patched tree: `(1,) -> '(1,)'`,
`(1, 2) -> '(1, 2,)'`, `() -> '(,)'`, `[1] -> '[1]'`, `((1,),) -> '((1,),)'`.

### 3.2 Why this is NOT an axiom and NOT an A-reference (§0.7)

SPEC_GUIDE §0.7: *"NEVER axiomatize the function under spec or the operation the
patch changes."* An **A-reference** is a deep model of an **unchanged** callee,
validated `model == real callee` by G-AX. But:

- `renderSeq` models the **iterable branch of `_recursive_to_string` itself**,
  which **is** the function/op the patch changes — not an unchanged callee.
- **G-AX runs the real callee on the UNPATCHED `base_commit` tree** (gates.py
  `gate_ax` calls `run_in_container` with the default `apply_gold=False`). At
  base_commit that branch is the *pre-patch* code: `left, right = "()"` unpacks
  to closer `)`, so a one-element tuple renders `'(1)'`. The fixed deep model
  renders `'(1,)'`. Asserting `renderSeq == real` is therefore **structurally
  impossible** — it can only ever fail (and it did: prior G-AX
  `AssertionError on (1,): real gave '(1)', model gives '(1,)'`).

The truly **unchanged** part — the per-element rendering recursion (`doprint`,
the `str` passthrough, the recursive descent) — is the opaque READ-ONLY input
`elems`; the proof assumes **nothing** about it (no `ensures` references how an
element renders), so it is not a consumed axiom either. It is run *identically*
on both sides of G-CONF as an R identity bridge.

**Conclusion:** there are **zero A-consumed axioms and zero A-references** in
this bundle. The changed op is validated *behaviourally* by **G-CONF**, which
runs `conformance_check.py` against the **gold-patched** tree (gates.py
`gate_conf`: `apply_gold=True`) and diffs the R/I shadow of `renderSequence`
against the patched `_recursive_to_string` over ≥10⁵ inputs. The bundle ships
**no `axiom_check.py`**, so G-AX correctly returns `skip` ("no axioms in
bundle").

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`23262`** so the
consumer-side verdict (§11.3) is reproducible. The R/I shadow transliterates
`renderSeq`/`joinComma` (R/I-tagged ops) to Python and shares the unchanged leaf
renderer `doprint` with the oracle (the R identity bridge), so the two sides
differ only in the modeled join-and-wrap step.
