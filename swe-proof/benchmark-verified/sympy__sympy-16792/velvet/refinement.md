# refinement.md — sympy__sympy-16792

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`buildArgList` `do` block plus the deep `argFor` / `argList` / `extentBounds`
model) and `patch.diff` (the gold patch). Each step is tagged **R** (type
refinement), **A** (axiomatized callee — **A-consumed** / **A-reference**), or
**I** (identical concrete op). EVERY step is R, A, or I.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the narrative is audited by **G-EQ**. Claim: any impl verifying against
this frozen spec, refined per the map below, is behaviourally equal to the gold
patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

**Termination semantics: total.** The obligation runs under
`loom.semantics.termination "total"` (`TotalCorrectness`), so the `while` fold
carries a `decreasing i` measure and a verifying impl must TERMINATE and
produce `argList requests`. (An earlier revision used partial correctness,
which a same-spec diverging impl — `while true` with a trivial invariant —
vacuously satisfied; the G-PANEL-1 audit found that counterexample, and total
semantics excludes the whole class. The real fall-through loop trivially
terminates: it is a bounded `for symbol in argument_sequence`.)

## A. The argument-list site — the `argument_sequence` fall-through (`codegen.py:738–743`)

This is the site the issue is about and the only behavioural change.

Gold hunk:
```
  for symbol in argument_sequence:
      try:
          new_args.append(name_arg_dict[symbol])
      except KeyError:
-         new_args.append(InputArgument(symbol))
+         if isinstance(symbol, (IndexedBase, MatrixSymbol)):
+             metadata = {'dimensions': dimensions(symbol)}
+         else:
+             metadata = {}
+         new_args.append(InputArgument(symbol, **metadata))
  arg_list = new_args
```

| # | Solution.lean impl op (`buildArgList` / `argFor`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `requests : List ArgSpec` | the `argument_sequence` being iterated | R | requested symbols ↔ `List ArgSpec` (mapping.md §2). G-CONF bridges via the per-symbol descriptor. |
| A2 | the backward `while` fold building `result = argList requests` | the `for symbol in argument_sequence:` loop building `new_args` | I | concrete order-preserving loop; the fold is the verified transliteration (`out = argList requests`, count + order preserved). |
| A3 | `if e.alreadyResolved then e.prior` | `try: new_args.append(name_arg_dict[symbol])` | I | a requested symbol already turned into an argument is reused verbatim. (mapping.md §2: the reused metadata equals `extentBounds` of its extents on both legs and cancels in G-CONF.) |
| A4 | else `{ bounds := if e.arrayLike then extentBounds e.extents else [] }` | the `except KeyError:` arm: `metadata = {'dimensions': dimensions(symbol)}` if `isinstance(symbol,(IndexedBase, MatrixSymbol))` else `{}`; `InputArgument(symbol, **metadata)` | R + I | the changed behaviour, modeled **deeply**: array-like ⇒ extent-derived bounds, scalar ⇒ none. `extentBounds extents = extents.map (d ↦ (0, d-1))` is exactly `dimensions(s) = [(S.Zero, dim-1) for dim in s.shape]`. The `dimensions`↔`bounds` bijection is mapping.md §2 (R); the branch + map ops are concrete (I). On the loop's reachable domain the guard's `IndexedBase` disjunct is dead: the sequence-normalization pass (`codegen.py:719–727`, unchanged) replaces every requested `IndexedBase` by its shapeless `.label` Symbol before this loop, so `arrayLike ⇔ isinstance(symbol, MatrixSymbol)` there and a fresh IndexedBase-originated request takes the scalar leg (`dimensions = None ↔ []`) — mapping.md §2 normalization note, witnessed by G-CONF. |
| A5 | result `out : List Arg` | `arg_list = new_args` | R | the produced positional argument list; `Arg.bounds` ↔ `Argument.dimensions` (mapping.md §2). |

Discriminating content of the change — a freshly-built **array-like** argument
receives its extent-derived dimension metadata (so it is later emitted by
reference, `double *x`) rather than empty metadata (`double x`) — lives in
`argFor e = { bounds := extentBounds e.extents }` for `e.arrayLike = true`
(model) ⇔ the `metadata = {'dimensions': dimensions(symbol)}` branch (real). The
pre-patch arm `InputArgument(symbol)` dropped all metadata;
`Solution_prepatch.lean` reproduces that (`{ bounds := [] }` for every fresh
request) and **fails** `out = argList requests` exactly when a request is
array-like (G-DIFF). G-CONF independently witnesses this: the buggy shadow
disagrees with the real patched `routine()` on the `MatrixSymbol('x',2,1)` case.

## B. The helper-extraction site — `dimensions(s)` (`codegen.py:695–714`)

Gold hunk: a local `def dimensions(s): return [(S.Zero, dim - 1) for dim in
s.shape]` is introduced and the pre-existing array-symbol arm's inline
`dims = []; for dim in array.shape: dims.append((S.Zero, dim - 1))` is replaced
by `metadata = {'dimensions': dimensions(array)}`.

| # | Solution.lean construct | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | `extentBounds (extents) = extents.map (d ↦ (0, d-1))` | the inline `dims` loop → the `dimensions(s)` helper | I | a **pure refactor**: the new helper computes the byte-identical list the inline loop did (`[(S.Zero, dim-1) for dim in s.shape]`). Behaviour-preserving extraction; the single `extentBounds` definition models both the array-symbol arm and the fall-through arm. No observable change. |

No separate failing prepatch for site B: extracting the helper changes no
behaviour (a prepatch must keep the spec byte-identical, G-DIFF, and there is no
behaviour to break). Its only role is to share `extentBounds` with site A; G-CONF
exercises `extentBounds` through the array-like fresh arm (site A4), which is
where the shared computation is observable.

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R or I. The one operation that genuinely *changed* — attaching
dimension metadata to a freshly-built array-like argument — is modeled
**deeply** (the spelled-out `extentBounds` map + the `argFor` branch, step A4),
not hidden behind an axiom about the function under change. There are no consumed
axioms and no A-reference callees: every observable (`alreadyResolved`,
`arrayLike`, `extents`, the produced `bounds`) is computed directly from the
inputs. Hence no `axiom_check.py` (mapping.md §3).

## D. verify(Solution) ⇒ resolved

`buildArgList` verifies only if its output equals `argList requests` — i.e. each
requested symbol is mapped by `argFor`: a fresh array-like symbol receives
`extentBounds` of its extents (A4), a fresh scalar receives none, and a resolved
symbol is reused (A3), in the requested order (A2). By R (`argument_sequence ↔
List ArgSpec`, `Argument.dimensions ↔ Arg.bounds` with `None ↔ []`, `dimensions(s)
↔ extentBounds`) the verified builder equals the patched fall-through arm on the
tested inputs; by G-CONF the R/I transliteration agrees with `patch.diff`'s real
`routine()` behaviour on ≥10⁵ inputs (0 disagreements), including the F2P
`MatrixSymbol('x',2,1)` case. Therefore a model satisfying this spec, refined by
the map above, is the gold patch up to type refinement — and the gold patch
resolves (G-RESOLVE: `test_ccode_unused_array_arg` then renders `double *x`).
The single trust point is refinement fidelity (this doc, G-EQ + G-CONF); there
is no axiom-soundness trust point (no consumed axioms).
