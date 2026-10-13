# refinement.md — sympy__sympy-16792

The operation-by-operation correspondence between `model.py`'s implementation
(the `pointer_flags` impl region and the deep `@Pure` model
`shape_is_intrinsic` / `array_resolved` / `arg_is_pointer` / `want_pointer`)
and `patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A** (axiomatized callee — split into **A-consumed**, where the proof uses an
axiom's `Ensures`, and **A-reference**, where a deep model is validated == the
real callee by axiom_check.py / G-AX), or **I** (identical concrete operation).

The claim: *any implementation that verifies against this frozen spec, refined
per the map below, is behaviourally equal to the gold patch on the tested
inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. What the gold patch changes

The gold patch touches `CodeGen.routine` in `sympy/utilities/codegen.py` in
three coupled hunks:

1. introduces a local helper
   `def dimensions(s): return [(S.Zero, dim - 1) for dim in s.shape]`
   (lines 698-700 post-patch);
2. rewrites the inlined dimension loop for the *expression-derived* arguments
   to call that helper (lines 706-712 → `metadata = {'dimensions': dimensions(array)}`);
3. the load-bearing fix: in the `argument_sequence` `KeyError` branch
   (lines 741-745 post-patch) a requested symbol that does NOT occur in the
   expression is now given array `dimensions` when it is an array-like symbol:
   ```
   - new_args.append(InputArgument(symbol))
   + if isinstance(symbol, (IndexedBase, MatrixSymbol)):
   +     metadata = {'dimensions': dimensions(symbol)}
   + else:
   +     metadata = {}
   + new_args.append(InputArgument(symbol, **metadata))
   ```

Hunks 1 and 2 are a pure refactor (factor the identical comprehension into a
helper) — behaviour-preserving. Hunk 3 is the only behavioural change, and is
what the F2P test observes through the generated C prototype.

## B. The observable that the spec pins

`CCodeGen.get_prototype` (`codegen.py:911-916`) renders each argument as
`*name` iff `arg.dimensions` is truthy (an `InputArgument` is never a
`ResultBase`). So the only thing the test sees about an argument is the boolean
"does it carry a non-empty dimension list" → "is it a pointer". The model
`pointer_flags` computes exactly that boolean per requested argument.

Crucial subtlety the model is faithful to: at the top of the
`argument_sequence` loop every user-supplied `IndexedBase` is first normalised
to its `.label`, a plain `Symbol` (`codegen.py:722-729`). So in the `KeyError`
branch `symbol` is a `MatrixSymbol` or a plain `Symbol`, never an
`IndexedBase`. Hence an *absent* indexed array is NOT promoted (its label is a
scalar Symbol — `isinstance(...,(IndexedBase,MatrixSymbol))` is False); only an
absent **matrix** is promoted. The model encodes this as the three kinds:
matrix → pointer always; indexed → pointer iff present; scalar → never.

## C. Operation correspondence

| # | model.py impl op (`pointer_flags`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| C1 | parameters `kinds: List[int]`, `present: List[bool]` (one entry per requested argument) | the `argument_sequence` of sympy symbols + the `name_arg_dict` membership test | R | `kinds[i]` ∈ {scalar=0, matrix=1, indexed=2} ↔ the type of `argument_sequence[i]`; `present[i]` ↔ `argument_sequence[i] in name_arg_dict` ↔ the symbol occurs in `expr` (mapping.md §2). |
| C2 | loop over each requested argument in order, appending one flag | `for symbol in argument_sequence: new_args.append(...)` (`codegen.py:740-746`) | I | same ordered one-arg-per-iteration construction. |
| C3 | branch `if is_present:` (arg taken from the pre-built list) → `has_dims = (matrix or indexed)` | the `try: name_arg_dict[symbol]` success path (the arg already carries its dimensions, attached at `codegen.py:698-714` via `dimensions(array)` / the matrix/indexed keys) | R + A-reference | a present array-like already has a non-empty dimension list ⇒ pointer; a present scalar has none. The dimension-attaching computation is the deep-model reference `dimensions` (C6). |
| C4 | branch `else:` (KeyError) → matrix ⇒ `has_dims=True`; indexed-label ⇒ scalar ⇒ `has_dims=False`; scalar ⇒ `has_dims=False` | the `except KeyError:` branch: `if isinstance(symbol,(IndexedBase,MatrixSymbol)): metadata={'dimensions':dimensions(symbol)} else: metadata={}` (`codegen.py:741-746`) | R + A-reference | THE FIX. An absent matrix matches the `isinstance` and is given dimensions (the comprehension over `shape` is non-empty ⇒ pointer); an absent indexed array reaches here as its scalar label, fails the `isinstance`, and stays scalar; an absent scalar stays scalar. The model's `else` branch (matrix→True, k==2→False, scalar→False) mirrors this exactly. |
| C5 | `flag = arg_is_pointer(has_dims)`; append | `InputArgument(symbol, **metadata)` then later `get_prototype` emits `*name` iff `arg.dimensions` (`codegen.py:913-914`) | R + A-reference | `arg_is_pointer(has_dims) == has_dims` is the C-prototype renderer's rule; validated == real `get_prototype` by G-AX (mapping.md §3.2). |
| C6 | `shape_is_intrinsic`, `array_resolved` (the per-kind array-ness), and the non-emptiness of an array's dimension list | the helper `dimensions(s) = [(S.Zero, dim-1) for dim in s.shape]` and the fact that a `MatrixSymbol`/`IndexedBase` has a non-empty `shape` | A-reference | the changed array-ness decision is modelled **deeply**: every matrix has an intrinsic non-empty shape so `dimensions(s)` is non-empty ⇒ the arg is an array ⇒ pointer. There is **no consumed axiom**; the deep model is validated == the real `dimensions`/`shape` computation and the real `get_prototype` out-of-band by axiom_check.py (G-AX). |

## D. Why no separate failing `model_prepatch` per refactor hunk

Hunks 1 and 2 (the `dimensions` helper extraction and its use for the
expression-derived args) are behaviour-preserving refactors — they produce the
identical dimension lists the old inlined loop did, so they have no
independently-observable fixed behaviour and need no `model_prepatch`. The one
behavioural change is hunk 3, captured by the single `model_prepatch.py`: it
reverts the `KeyError` branch to "no dimensions for any absent argument"
(`has_dims = False` in the `else` branch), and **fails** the loop invariant /
postcondition `Result()[i] == want_pointer(kinds[i], present[i])` on exactly an
absent matrix argument (`kind=1, present=False`: required pointer, the bug
yields scalar) — which is precisely the F2P `test_ccode_unused_array_arg`
scenario (G-DIFF).

## E. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The operation that genuinely changed
— giving an absent array-like argument its dimensions so the prototype renders
a pointer — is modelled **deeply** (`array_resolved` / `arg_is_pointer` plus
the verified loop), not hidden behind an axiom about the function under change.
There is **no consumed `@ContractOnly` axiom**. The only trust point is the
A-reference: that the deep model (matrix ⇒ pointer always; indexed ⇒ pointer
iff present; scalar ⇒ never) equals the real `CodeGen.routine` +
`CCodeGen.get_prototype`, which G-AX confirms by executing the real callees on
the F2P scenario + 13 boundary + 400 fuzz argument sequences (mapping.md §3).

## F. verify(model) ⇒ resolved

`pointer_flags` verifies only if every output flag equals
`want_pointer(kinds[i], present[i])` — in particular an absent matrix is a
pointer (the discriminating clause the prepatch fails). By R (the type
refinements of §C / mapping.md §2) the verified per-argument pointer decision
equals the dimension-presence the gold `routine` attaches; by the A-reference
(G-AX) that dimension-presence drives the real `get_prototype` to emit `*x`
exactly as the model says. Therefore an implementation satisfying this spec,
refined by the map above, is the gold patch up to type refinement and the
audited callee, and the gold patch resolves (G-RESOLVE). The single trust point
is the A-reference (G-AX); refinement fidelity is this document (G-EQ).
