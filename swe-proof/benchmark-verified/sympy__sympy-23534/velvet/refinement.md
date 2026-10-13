# refinement.md — sympy__sympy-23534

Operation-by-operation correspondence between `Solution.lean`'s impl region
(the `buildSeq` `do` block, the deep `expand` model, and the `buildName` /
`buildName_cls` axioms) and `patch.diff` (the gold patch). Each step is tagged
**R** (type refinement), **A** (axiomatized callee — **A-consumed** where the
proof uses the axiom's `ensures`, **A-reference** where a deep model is
validated == the real callee by G-AX), or **I** (identical concrete op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the A legs and this narrative are audited by **G-EQ**. Claim: any impl
verifying against this frozen spec, refined per the map below, is behaviourally
equal to the gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The sequence-builder site — `symbols(...)` else-branch (`sympy/core/symbol.py:793-796`)

Gold hunk:
```
     else:
         for name in names:
-            result.append(symbols(name, **args))
+            result.append(symbols(name, cls=cls, **args))

         return type(names)(result)
```

| # | Solution.lean impl op (`buildSeq`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `names : List String` | `names` (non-`str` sequence) arg of `symbols` | R | `tuple/list` of name strings ↔ `List String` (mapping.md §2); order preserved. G-CONF bridges element-wise. |
| A2 | parameter `cls : SymCls` | the keyword-only `cls` parameter (default `Symbol`) | R | class object `Symbol`/`Function`/`Wild` ↔ `.sym`/`.func`/`.wild` (mapping.md §2). |
| A3 | the backward `while` loop iterating `names` in order, prepending each `buildName n cls` | `for name in names: result.append(...)` | I | concrete loop transliterated by G-CONF; the backward fold computes exactly the left-to-right per-element list `expand names cls`. |
| A4 | `buildName n cls` (per element, requested class threaded in) | `symbols(name, cls=cls, **args)` | A-consumed | the per-element builder is the UNCHANGED `str`-input branch; the one relied-on fact is `buildName_cls`: it honours the requested `cls`. The **fix is exactly the threading of `cls`** — modeled by passing `cls` (not `.sym`) as `buildName`'s second argument. mapping.md §3.1. |
| A5 | `result` returned (`List (List SymCls)`) | `type(names)(result)` wrap | R | the `tuple`/`list` wrapper is identity on element content and order (mapping.md §2); the F2P test indexes into it (`[0][0]`), observing element class only. |

Discriminating content of the change — the requested class reaches each
per-element build — lives in `buildName n cls` (model, A4) ⇔
`symbols(name, cls=cls, **args)` (real). The pre-patch code called
`symbols(name, **args)` (dropping `cls`, so the keyword-only `cls` defaulted to
`Symbol`); `Solution_prepatch.lean` reproduces that by building with `.sym`
instead of `cls` and **fails** the postcondition `out = expand names cls`
(and `∀ x ∈ sub, x = cls`) whenever `cls ≠ .sym` (G-DIFF). The unsolved goal is
literally `buildName … .sym = buildName … cls`.

## B. The `expand` deep model and `buildName_cls` axiom

| # | Solution.lean construct | patch.diff / repo op | tag | justification |
|---|---|---|---|---|
| B1 | `expand names cls` (front-recursive fold: `buildName n cls :: expand ns cls`) | the accumulated `result` of the else-loop, post-fix | I | deep model of the loop's data flow; each step is the concrete per-element build. Validated against `patch.diff` behaviour by G-CONF (the R/I legs A1–A5). |
| B2 | `buildName_cls : ∀ s c, ∀ x ∈ buildName s c, x = c` | the class invariant of the unchanged `str`-branch (`cls(literal(name))` / `cls(s)`) | A-consumed | weakest contract sufficient for `expand_cls`; consumed by the postcondition `∀ sub ∈ out, ∀ x ∈ sub, x = cls`. G-AX confirms against the real single-name `symbols`. |

The postcondition `∀ sub ∈ out, ∀ x ∈ sub, x = cls` is the abstract statement of
the issue: every produced object carries the requested class, even through the
extra layer of parentheses (the sequence input). It is grounded in the input
carrier (`names`, `cls`) via `expand`, not pinned to an opaque oracle
(directive 8).

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R, A, or I. The operation that genuinely *changed* — propagating
`cls` into the per-element recursion — is modeled as a concrete data-flow edge
(passing `cls` to `buildName`, step A4/B1), an **I/A-consumed** combination, not
hidden behind an axiom about the function under change. The only consumed
axioms, `buildName`/`buildName_cls`, cover the **unchanged** single-name
`symbols` branch the loop recurses into.

## D. verify(Solution) ⇒ resolved

`buildSeq` verifies only if its output equals `expand names cls` — each element
group built with the REQUESTED `cls` (A4) — and every produced object carries
`cls` (B2). By R (`tuple/list ↔ List`, `Symbol/Function/Wild ↔ SymCls`,
`type(names)(...)` wrapper identity) the verified builder equals
`type(names)([symbols(name, cls=cls, **args) for name in names])` on the tested
sequence inputs; by G-AX the per-name builder honours `cls` (A-consumed); by
G-CONF the R/I transliteration of the loop agrees with `patch.diff`'s behaviour
(leaf-class observation) on ≥10⁵ inputs. Therefore a model satisfying this spec,
refined by the map above, is the gold patch up to type refinement and the
audited callee — and the gold patch resolves (G-RESOLVE). Trust points are
exactly the two of plan §1.1: axiom soundness (G-AX) and refinement fidelity
(this doc, G-EQ + G-CONF).
