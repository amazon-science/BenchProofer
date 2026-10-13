# refinement.md — sphinx-doc__sphinx-7757

The operation-by-operation correspondence between `model.py`'s implementation
(the `resolve_positional_defaults` impl region, the deep `resolved_default`
spec, and the `render` axiom) and `patch.diff` (the gold patch). Each step is
tagged **R** (type refinement), **A** (axiomatized callee — **A-consumed** when
the proof uses the axiom's `Ensures`, **A-reference** when a deep model is
validated == the real callee by axiom_check.py / G-AX), or **I** (identical
concrete operation). The claim: *any implementation that verifies against this
frozen spec, refined per the map below, is behaviourally equal to the gold
patch on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit`,
confirmed with `git apply --check`, and is the real correctness oracle,
G-RESOLVE).

## A. The alignment site — `signature_from_str` (`sphinx/util/inspect.py:514`)

Gold hunk (positional default alignment). Pre-patch: positional-only parameters
get no default at all, and ordinary parameters index `args.defaults` relative to
the ordinary-parameter count. Post-patch: a single combined `defaults` list is
left-padded with `Parameter.empty` to the total positional count, and each
positional parameter (positional-only and ordinary alike) reads its slot:

```
+ defaults = list(args.defaults)
+ if hasattr(args, "posonlyargs"):
+     posonlyargs = len(args.posonlyargs)
+     positionals = posonlyargs + len(args.args)
+ else:
+     posonlyargs = 0
+     positionals = len(args.args)
+ for _ in range(len(defaults), positionals):
+     defaults.insert(0, Parameter.empty)
  ...
+ for i, arg in enumerate(args.posonlyargs):
+     if defaults[i] is Parameter.empty: default = Parameter.empty
+     else:                              default = ast_unparse(defaults[i])
+     ... Parameter(arg.arg, POSITIONAL_ONLY, default=default, ...)
  for i, arg in enumerate(args.args):
+     if defaults[i + posonlyargs] is Parameter.empty: default = Parameter.empty
+     else:  default = ast_unparse(defaults[i + posonlyargs])
      ... Parameter(arg.arg, POSITIONAL_OR_KEYWORD, default=default, ...)
```

| # | model.py impl op (`resolve_positional_defaults`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameters `positionals`, `posonly` (ints) | `positionals = posonlyargs + len(args.args)`, `posonlyargs = len(args.posonlyargs)` | R | the positional parameter lists `args.posonlyargs ++ args.args` are abstracted to their counts and the prefix boundary (mapping.md §2); names/annotations are irrelevant to the alignment bug. |
| A2 | `provided: List[int]`, `m = len(provided)` | `defaults = list(args.defaults)` (before padding), `len(args.defaults)` | R | `args.defaults` (a single combined list binding the trailing positional parameters) ↔ `provided` of value codes (mapping.md §2). |
| A3 | `pad = positionals - m`; positions `p < pad` get `EMPTY()` | `for _ in range(len(defaults), positionals): defaults.insert(0, Parameter.empty)` — the leading `positionals - len(defaults)` slots become `Parameter.empty` | I (up to R on the carrier) | the left-pad inserts exactly `positionals - m` sentinels at the front; model.py emits `EMPTY()` for exactly those leading `pad` positions. `EMPTY()` ↔ `Parameter.empty` (mapping.md §2). |
| A4 | positions `p >= pad` get `render(provided[p - pad])` | positional-only loop `defaults[i]` and ordinary loop `defaults[i + posonlyargs]` read the padded list; non-sentinel slot ⇒ `ast_unparse(defaults[...])` | A-consumed + I | after padding, the padded index of positional parameter `p` is `p` itself (positional-only `i==p`; ordinary `i + posonlyargs == p`). The non-sentinel slots are exactly the trailing `m`, at padded positions `pad .. positionals-1`, holding `args.defaults[(p-pad)]`. So `Result()[p] == render(provided[p-pad])` ⇔ `default = ast_unparse(defaults[p])`. The `render` axiom (A-consumed) is **domain-restricted** (`Requires(renderable(value_code))`) because the real `ast_unparse` is **partial** — it raises `NotImplementedError` on unsupported default nodes; the spec only covers signatures whose supplied defaults are all `renderable` (the precondition `Forall j: renderable(provided[j])`), which the real callee returns on, and there it supplies `render(...) != EMPTY()`, discharging that a defaulted slot is not the sentinel. (The alignment property the spec pins is independent of which default expressions are renderable, so this restriction does not weaken the discriminator — see §C.) |
| A5 | uniform single loop over all `positionals` positions, no separate treatment of the positional-only prefix | post-patch: the positional-only loop AND the ordinary loop both read the same padded `defaults` by absolute index | I | the gold patch makes both loops share one padded `defaults` list indexed by absolute position; model.py's single loop is that shared indexing. The positional-only prefix is no longer exempt. |
| A6 | `result` returned (`List[int]`, one resolved default per positional parameter) | the per-parameter `default=` passed to each `Parameter(...)` | R | only the `default` slot is modeled; `kind`, `annotation`, name, and the unchanged `*args`/kwonly/`**kwargs` handling are identical pre/post patch and omitted (mapping.md §2). |

The discriminating content of the change — a defaulted positional-only
parameter (e.g. `b` in `(a, b=0, /, c=1)`) keeping its default — lives in
`resolved_default(p) != EMPTY()` for a positional-only `p` inside the trailing
default block (model) ⇔ the new positional-only loop reading a non-sentinel
padded slot and passing `default=ast_unparse(defaults[i])` (real). The pre-patch
code attached no default to positional-only parameters and mis-indexed ordinary
defaults; `model_prepatch.py` reproduces that (the positional-only pass always
appends `EMPTY()`, the ordinary pass aligns over `regular = positionals - posonly`
with `provided[m - regular + i]`) and **fails** the postcondition
`ToSeq(Result())[p] == resolved_default(p, …)` (and the positional-only
non-exempt clause), which is exactly the spec sensing the change (G-DIFF).

## B. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-consumed, or I. The operation that genuinely *changed*
— the default-to-position alignment across the WHOLE positional list — is
modeled **deeply** (the spelled-out `resolved_default` / the padded loop in
`resolve_positional_defaults`), not hidden behind an axiom about the function
under change. The only consumed axiom, `render` (**A-consumed**), covers the
**unchanged** callee `sphinx.pycode.ast.unparse` the patched code merely invokes
to render the selected default node; the proof consumes only its weakest
property (`render(...) != EMPTY()`, plus referential transparency) and only ON
its domain of definedness. Because the real `ast.unparse` is **partial** (it
raises `NotImplementedError` on unsupported default nodes), the axiom is
**domain-restricted** by the abstract predicate `renderable` (`render` carries
`Requires(renderable(value_code))`; the function-under-spec requires every
supplied default to be renderable). This avoids the directive-7 over-claim: the
contract never asserts a return value on inputs the callee does not handle.
`renderable` is an A-consumed domain predicate, validated non-vacuous by G-AX
(off-domain expressions are confirmed to raise). G-AX also validates the deep
alignment model itself against the real post-patch `signature_from_str`
position-by-position (an **A-reference**-style check of the deep model).

## C. verify(model) ⇒ resolved

`resolve_positional_defaults` verifies only if every positional parameter `p`
carries `EMPTY()` for `p < positionals - m` and the rendered supplied default
at offset `p - (positionals - m)` otherwise (A3-A4), uniformly over the
positional-only prefix and the ordinary parameters (A5). By R (parameter lists
↔ counts; `args.defaults` ↔ `provided`; `EMPTY()` ↔ `Parameter.empty`;
`render` ↔ `ast_unparse`) this is exactly the padded-`defaults` indexing the
gold patch performs; by the domain-restricted `render` axiom (A-consumed, sound
by G-AX) a defaulted slot is a real source string, not the sentinel; and by the
G-AX position-by-position check the deep alignment model equals the real
post-patch `signature_from_str`. Therefore a model satisfying this spec, refined
by the map above, is the gold patch up to type refinement and the one audited
callee — and the gold patch resolves (G-RESOLVE). The trust points are exactly
the two of PLAN §1.1: axiom soundness (G-AX) and refinement fidelity (this
document, G-EQ).

### C6 — the resolver must ANSWER (total, not partial, correctness)

`resolve_positional_defaults` carries `Requires(MustTerminate(2))` in its
pre-conditions region, and its loop carries the decreasing measure
`Invariant(MustTerminate(positionals - p + 1))` in the impl region.

*Why the clause belongs to the specification.* Nagini proves PARTIAL correctness
unless a method demands otherwise: without this obligation every `Ensures` above
is claimed only of runs that **reach the return**, so the cheapest rival of all —
one that never reaches one — satisfies C1–C5 while performing none of the work,
and `verify` stops implying `resolved`. Two shapes of that rival were measured
against the un-obligated spec: an unconditional self-delegation
(`return resolve_positional_defaults(positionals, posonly, provided)`) verified in
20.6 s, and a plain `while spin >= 0: spin = spin + 1` ahead of the return
verified in 17.3 s. Refined into the real `signature_from_str` the first
recurses (`RecursionError` on every call: F2P fails 1/1 and P2P 5/33, module still
importing) and the second hangs, so neither resolves anything.

*Why the clause is TRUE of the real patched implementation* (`sphinx/util/inspect.py`
at `base_commit` + gold patch):

| model.py | patched repo | why it terminates |
|---|---|---|
| `Invariant(MustTerminate(positionals - p + 1))` on the single `while p < positionals` loop | `for _ in range(len(defaults), positionals): defaults.insert(0, Parameter.empty)` (`:530-531`) | a `range` loop of exactly `max(0, positionals - len(args.defaults))` steps, fixed before the first iteration |
| same | `for i, arg in enumerate(args.posonlyargs)` (`:534-542`) | one pass over a finite AST list built by `ast.parse` at `:516` |
| same | `for i, arg in enumerate(args.args)` (`:544-552`) | one pass over a finite AST list |
| `Requires(MustTerminate(2))` on the method | `signature_from_str` (`:514`) | no recursive call anywhere in the function; the only callees on the modeled path are `ast_unparse` (`sphinx/pycode/ast.py`, a structural recursion over a finite AST — the same callee the `render` axiom abstracts) and the `Parameter(...)` constructor |

So the obligation states a property the gold patch has, over the whole admitted
domain, and it restricts no input value: it is not a precondition that narrows
the domain but a duty to answer on it. It costs the frozen implementation nothing
(`model.py` verifies in 31.6 s under it) and it costs a faithful RIVAL nothing but
a measure of its own — measured: the correct `resolved_default`-echo rival, given
`Invariant(MustTerminate(positionals - p + 1))` for its own loop, still verifies
(38.7 s), and `model_prepatch.py` still fails on the alignment clause C2 rather
than on the obligation, i.e. G-DIFF still senses the *bug* and not the annotation.

*The other non-returning exit.* Stopping without answering is also possible by
raising. The frozen contract declares no `Exsures` at all, so the post-conditions
region promises a `Result()` on every admitted input; an impl that computes the
gold answer and then leaves by `raise` is rejected with `Exhale might fail.
Assertion "method raises no exceptions" might not hold.` (`properties.py`
`r8-raise-exit`). Implicit exceptional exits — an out-of-range read of `provided`,
say — are refused by Nagini's own safety obligations. Together with C6 this makes
the return the only way out, which is what `verify ⟹ resolved` needs.

The three cases `r6-self-delegation`, `r7-decorative-measure` and `r8-raise-exit`
in `properties.py` hold this lane open mechanically, so a later weakening that
deleted the obligation would be caught by G-PBT and not only by an audit panel.
`r7` matters because the measure lives in the elided impl region, where a rival
writes its own: a CONSTANT `Invariant(MustTerminate(1))` on an unbounded loop is
rejected (`Loop might not keep promise to terminate`), so the level has to
strictly decrease rather than merely appear.

**The domain restriction does not weaken the discriminator.** The bug the spec
senses is a *position-selection* effect: pre-patch, a defaulted positional-only
parameter (e.g. `b` in `(a, b=0, /, c=1)`) loses its default — `Result()[p]`
comes out `EMPTY()` where the spec requires a rendered default. This holds for
ANY renderable default value (all the F2P/P2P signatures use renderable literal
defaults), so restricting `render`'s domain to `renderable` leaves the failing
postcondition `ToSeq(Result())[p] == resolved_default(...)` (and the
positional-only-not-exempt clause) fully active. `model_prepatch.py` carries the
identical (renderable-guarded) spec and still **fails** on exactly that clause
(G-DIFF), so `verify ⟹ resolved` is preserved: the only signatures the spec
declines to cover are those with a non-renderable default node, on which the
real post-patch callee itself raises rather than returning — i.e. outside the
behaviour the patch resolves.
