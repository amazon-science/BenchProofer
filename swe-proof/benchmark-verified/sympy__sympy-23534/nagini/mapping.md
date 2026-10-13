# mapping.md — sympy__sympy-23534

Binds every model.py symbol to the real repo symbol at `base_commit`
(`832c24fec1046eaa544a4cab4c69e3af3e651759`), records the type abstraction, and
documents the deep-model reference's provenance + executable evidence.

## 1. The modeled function

| model.py symbol | repo symbol | repo location (base_commit) | role |
|---|---|---|---|
| `symbols_on_sequence(names, cls)` | the *container* branch of `sympy.core.symbol.symbols` — the `else:` arm that iterates a sequence of names | `sympy/core/symbol.py:792-796` (the `else:` block; the patched line is `:794`) | modeled changed function: collects one sub-result per container entry, processing each entry under the requested output class |
| `expand_entry(cls)` | the *single-name* branch of `symbols` (the `isinstance(names, str)` arm that ultimately calls `cls(literal(name), **args)` / `cls(s, **args)`) reached via the recursive `symbols(name, ...)` call | `sympy/core/symbol.py:704-791` (constructors at `:744`, `:782`, `:784`) | deep model of the per-entry processing the container branch recurses into; this branch is NOT what changed, but its class handling is what the container branch must preserve |

`symbols` signature at base_commit: `def symbols(names, *, cls=Symbol, **args)`
(`sympy/core/symbol.py:586`). The container branch recurses:
`result.append(symbols(name, **args))` (`:794`) — and at base_commit it OMITS
`cls`, so each recursive call defaults `cls` back to `Symbol`
(`sympy/core/symbol.py:586` default), producing `Symbol` objects regardless of
the caller's requested `cls`. That is the bug.

## 2. Type abstraction

| repo reality | model as | justification |
|---|---|---|
| `names`: a container (`tuple`/`list`/`set`) of name strings | `List[int]`: each entry is an opaque token whose `int` value is its **expansion multiplicity** — the number of objects that entry produces (>= 0). Entry textual content is otherwise irrelevant to the tested behaviour. Read-only ⇒ `Acc(list_pred(names), 1/2)`; multiplicities non-negative ⇒ `all_nonneg(ToSeq(names))`. | The patch changes which class flows into each entry; the per-entry multiplicity and grouping are determined by the entry string (not by the impl), so they are an abstract property of the input the F2P test reads (`[0][0]`). |
| `cls`: the requested output class (a Python class / metaclass) | `int` *class tag*. The default class `Symbol` is the tag `DEFAULT_CLS() == 0`; any other requested class is a distinct tag. | An object's observable property in the F2P test is its class. The class produced by calling the requested `cls` is abstracted to its tag. |
| a produced symbol-like object | its `int` class tag (the only field the test touches is `type(obj)`) | The F2P test reads `type(symbols(('q:2','u:2'), cls=Function)[0][0])`. |
| the produced grouped structure `type(names)(result)` (a tuple/list/… of per-entry sub-results) | a sequence-of-sequences `PSeq[PSeq[int]]`: **one group per entry, in order**, group `k` holding the `names[k]` leaf class tags of entry `k`. Pinned by `len(Result()) == len(names)` (one group per entry) and `len(Result()[k]) == names[k]` (per-entry multiplicity). | The grouping `type(names)(result)` is **resolution-load-bearing**: the F2P test deconstructs it by indexing (`[0][0]`). A range entry's tuple of `m` objects ↔ a group of length `m`; a single-name scalar ↔ length 1; a null range `()` ↔ length 0. It is therefore modeled explicitly, NOT abstracted to a flat list. (Nagini note: quantified write-permission to nested *mutable* inner lists `List[List[int]]` is non-injective and infeasible; modeling the grouped result as the **pure** value `PSeq[PSeq[int]]` — built by functional concatenation, requiring no `list_pred` permission on inner groups — sidesteps that wall while keeping the grouping load-bearing.) |

Note (recorded for G-AX): the requested class may be a *metaclass*. For
`cls=Function`, `symbols('x', cls=Function)` produces an `UndefinedFunction`
instance — i.e. `type(cls('x'))`, not a `Function` instance. The class tag is
therefore the type of the object the requested class *produces*
(`type(cls(name))`), which is `Symbol` for `cls=Symbol` and `UndefinedFunction`
for `cls=Function`. `axiom_check.py` realises the tag as `type(cls("probe"))`.

Note (null ranges — recorded for G-AX, the soundness boundary): an entry may
expand to ZERO objects. `symbols('x:c', seq=True) == ()`,
`symbols('x:0', seq=True) == ()`; in a container,
`symbols(('q:2','x:0'), cls=Function) == ((q0, q1), ())`. The model's per-entry
multiplicity clause `len(Result()[k]) == names[k]` is sound here precisely
because it claims the EXACT multiplicity (0 for a null range), never `> 0`. The
earlier `len > 0` / `len(Result()) >= len(names)` over-claim (stronger than the
real callee on null ranges) is removed; `axiom_check.py` now exercises null
ranges as both single entries and container entries (and in the fuzzer) so the
clause is checked on the subdomain where the prior over-claim was unsound.

## 3. Deep-model reference (A-reference) provenance

There are NO consumed `@ContractOnly` axioms in this bundle. The per-entry
processing is modeled DEEPLY by `expand_entry` (model.py impl region) +
`all_tag` (pure region):

| name | kind | models | provenance | encoded property | checked by |
|---|---|---|---|---|---|
| `expand_entry` | A-reference | the single-name branch of `symbols` constructing objects via the requested class | `sympy/core/symbol.py:744` (`cls(literal(name), **args)`), `:782/:784` (`cls(...)` for ranges); the branch always constructs with the SAME `cls` it was called with | a single entry expands to EXACTLY its multiplicity many objects (≥ 0; a null range yields 0), EVERY one carrying the requested class tag (`len(Result())==n ∧ all_tag(Result(), cls)`) | `axiom_check.py` (G-AX): runs real `symbols(name, cls=X, seq=True)` and the real container `symbols(names, cls=X)` and asserts (a) one group per entry, (b) each group's multiplicity equals the entry's expansion (incl. 0 for null ranges), (c) every leaf has type `type(X(probe))`; 10 boundary + 300 fuzz (null ranges included); F2P witness reproduced; also confirmed to FAIL on the unpatched branch |

`expand_entry` is a *reference* validated against the real callee, NOT a
consumed axiom: the proof of `symbols_on_sequence` uses `expand_entry`'s
`Ensures` directly (it is the under-spec single-name path, modeled in-module),
and there is no `@ContractOnly` standing in for the function under change. The
changed operation (which class flows into the per-entry processing) is the
`cls` argument threaded through `symbols_on_sequence` into `expand_entry`,
modeled explicitly — not hidden behind an axiom.

## 4. Flag dependencies

None. No floats; `--float-encoding` not used. `axiom_check.py` imports only the
repo package `sympy` (and the stdlib `random`/`sys`) — the same module the gold
patch edits.
