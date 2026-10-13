# refinement.md — sphinx-doc__sphinx-7757

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`distributePositionalDefaults` `do` block and the deep `distributed` model) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A** (axiomatized callee — none here), or **I** (identical concrete op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the (empty) A legs and this narrative are audited by **G-EQ**. Claim: any
impl verifying against this frozen spec, refined per the map below, is
behaviourally equal to the gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

**Termination semantics: total.** The obligation runs under
`loom.semantics.termination "total"` (`TotalCorrectness`), so the backward
prepend `while` carries a `decreasing k` measure and a verifying impl must
TERMINATE and produce `distributed (p + q) defaults`. (An earlier revision used
partial correctness, which a same-spec diverging impl — a non-terminating loop
with a trivially-maintained invariant — vacuously satisfied; the G-PANEL-1
audit found that counterexample, and total semantics excludes the whole class.
The real patched loop trivially terminates: `for _ in range(len(defaults),
positionals)` is a bounded range.)

## A. The default-distribution site — `signature_from_str` (`sphinx/util/inspect.py:514`)

Gold hunk (paraphrased): compute `defaults = list(args.defaults)`; let
`posonlyargs = len(args.posonlyargs)` (0 if absent) and
`positionals = posonlyargs + len(args.args)`; then
`for _ in range(len(defaults), positionals): defaults.insert(0, Parameter.empty)`
— i.e. **left-pad** `defaults` with `Parameter.empty` up to `positionals` so that
`defaults[j]` is the default of the `j`-th positional parameter (positional-only
first, then ordinary), `Parameter.empty` where absent. The two parameter loops
then read `defaults[i]` (posonly) and `defaults[i + posonlyargs]` (ordinary).

Lean side: `p = posonlyargs`, `q = len(args.args)`, `n = p + q = positionals`,
`defaults : List Int` the supplied defaults. `distributed n defaults =
replicate (n - d) none ++ defaults.map some` is exactly "left-pad with `empty`
to width `n`, then the defaults verbatim" — the per-position default vector.

| # | Solution.lean impl op (`distributePositionalDefaults`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | params `p q : Nat` | `posonlyargs = len(args.posonlyargs)` (0 if no attr) and `len(args.args)` | R | counts ↔ `Nat` (mapping.md §2). |
| A2 | `defaults : List Int` | `defaults = list(args.defaults)` | R | each rendered default ↔ an injective `Int` tag; the logic never inspects the payload (mapping.md §2). |
| A3 | `require defaults.length ≤ p + q` | always-true parser invariant (`len(args.defaults) ≤ positionals`) | I | a signature has no more defaults than positional parameters. |
| A4 | result `out = distributed (p+q) defaults`: `replicate ((p+q)-d) none ++ defaults.map some`, computed by the backward `while` that prepends `none` | `for _ in range(len(defaults), positionals): defaults.insert(0, Parameter.empty)` then per-position read | I | the left-pad-with-empties-then-defaults is modeled **deeply** by `distributed`; the loop prepends one `none` per missing leading slot — exactly `positionals - len(defaults)` insertions of `Parameter.empty` at the front. Concrete, transliterated by G-CONF. |
| A5 | element `none` ↔ "no default"; `some v` ↔ default value `v` | `Parameter.empty` vs `ast_unparse(defaults[idx])` | R | `Option Int` ↔ `empty`/rendered-string (mapping.md §2). `ast_unparse` is the per-element identity carried by the tag bijection, applied identically pre/post-patch; not an axiom. |

Discriminating content of the change — **positional-only parameters participate
in the default alignment**, so `positionals = posonlyargs + len(args.args)`
rather than `len(args.args)` — lives in `distributed (p + q)` (model) using the
full width `p + q`. The pre-patch aligned defaults over the trailing group only
(width `q = len(args.args)`), dropping any default that belonged to a
positional-only parameter; `Solution_prepatch.lean` reproduces that (alignment
over `q`, keeping only `min q d` defaults) and **fails** `out = distributed (p+q)
defaults` (G-DIFF) precisely when a default spills into the leading group — e.g.
the F2P signature `(a, b=0, /, c=1)` (`p=2, q=1, d=2`): correct `[none, 0, 1]`,
buggy `[none, none, 1]` (`b`'s default vanished — the reported bug).

## B. No second site

The fix is a single localized behaviour (default distribution across positional
parameters). There is no independently-fixed second behaviour, so a single
`Solution_prepatch.lean` suffices for G-DIFF.

## C. No kind-A and no kind-3 steps

Every step is R or I. There is **no axiomatized callee**: the modeled behaviour is
pure positional data movement; `ast_unparse` is a per-element identity (R), not a
participant in the distribution. There is also no kind-3 (inexpressible-changed-op)
step — the changed operation (the alignment width) is modeled **deeply** by
`distributed` over `Nat`/`List`, not hidden behind an axiom.

## D. verify(Solution) ⇒ resolved

`distributePositionalDefaults` verifies only if its output equals the exact
right-alignment of the defaults across **all** `p + q` positional parameters
(A4, the corrected width). By R (counts ↔ `Nat`, defaults ↔ tagged `List Int`,
per-position default ↔ `Option Int`/`Parameter.empty`) the verified vector equals
the per-position `Parameter.default` sequence the patched `signature_from_str`
builds on the tested inputs; by G-CONF the R/I transliteration of `distributed`
agrees with `patch.diff`'s behaviour on ≥10⁵ fuzzed signatures. There are no
axioms, so trust point #1 of plan §1.1 (axiom soundness) is vacuous here; the
only residual trust is the type bijection (mapping.md §2), which G-CONF makes
falsifiable. Therefore a model satisfying this spec, refined by the map above, is
the gold patch up to type refinement — and the gold patch resolves (G-RESOLVE).
