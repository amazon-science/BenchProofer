# mapping.md — sympy__sympy-20154

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = bdb49c4abfb35554a3c8ce761696ffff3bb837fe`, states the type
abstraction (R-refinements), and gives the provenance of the single callee the
deep model is validated against (A-reference). No callee is consumed.

Repo file under change: `sympy/utilities/iterables.py`.

## 1. Symbol ↔ repo binding

| `Solution.lean` symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `gatherWalk (steps)` | the act of GATHERING the generator `partitions` (`sympy/utilities/iterables.py:1696`) into a list, exactly as every F2P test does (`[p for p in partitions(...)]`, `list(uniq(p for p in partitions(...)))`) | the modeled behaviour: collecting the enumerator's per-step records into a list |
| `stateAt (i)` | the content of the single working partition dictionary `ms` at the i-th yield (`iterables.py:1798` initial, mutated through the `while` loop body `1809-1847`) | pure spec: the working state at step i, abstracted to a strictly-increasing per-step value |
| `work` (the live integer in the impl) | the one reused dictionary object `ms` (`iterables.py:1798`) that the generator mutates in place across yields | the live working record the enumerator advances in place |
| `snap` (the value appended in the impl) | the object handed out by each `yield` — `ms.copy()` post-patch versus the live `ms` pre-patch (`iterables.py:1805/1807/1845/1847`) | the per-step record handed out (an independent snapshot post-patch) |

The pre-image repo behaviour the change removes (for the refinement audit, not
referenced from the consumer spec view): the four yield statements at
`iterables.py:1805,1807,1845,1847` hand out the LIVE `ms` object, so gathering
the generator returns a list whose entries all alias that one dictionary and
read back as its final mutated state. The accompanying docstring caveat at
`iterables.py:1741-1754` is also deleted by the gold patch.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| the working partition dict `ms : {int: int}` (a multiplicity mapping) | a single mutable working record advanced in place; abstracted to the integer `work` carrying its per-step identity | the change and the F2P tests never depend on the *internal structure* of the working dict, only on whether two gathered records are independent snapshots or the same evolving object; the abstraction keeps exactly the observable the tests probe — gathered-record-i equals the state at step i (distinct per step) versus all-equal-to-final |
| gathering the generator (`list(partitions(...))` / `[p for p in partitions(...)]`) | the `gatherWalk` loop that records one value per step into `out : List Int` | gathering n yields ↔ a length-n list; the k-th gathered record ↔ `out[k]` |
| the added per-yield duplication (`ms.copy()`) | recording `snap := stateAt (i-1)` BY VALUE before appending | duplicating the working record produces a fresh, independent object equal in contents to the working state at the moment of the yield; by-value capture of the integer abstraction carries the same independence guarantee (a later mutation of the working record never reaches the gathered record) |
| each yielded partition's distinct per-step value (`{2: 3}`, `{1: 2, 2: 2}`, ... pairwise different across steps) | `stateAt i = i + 1` (strictly increasing) | the genuine per-step difference of the partitions is abstracted to a strictly-increasing per-step value; this is what makes the alias defect observable (an aliasing gather collapses every record to a single value, so it cannot reproduce a strictly-increasing per-step list) |

Carrying a list of distinct dictionary objects through the verifier's
quantified fragment is awkward (the per-element receivers are not provably
injective without a non-converging quadratic distinctness invariant); the
observable the tests sense — per-step independence of gathered records — is
carried faithfully in the value domain instead. See §3.

## 3. The duplication primitive (A-reference — checked by axiom_check.py / G-AX)

### 3.1 `snap := stateAt (i-1)` (by-value record) ↔ `ms.copy()` (`dict.copy`)
**Callee:** CPython `dict.copy()` (equivalently `dict(...)` / `{**d}`) — returns
a NEW dict object that is a shallow copy: a distinct object (`copy is not d`)
whose key/value pairs equal the source's at the moment of the call, and which is
thereafter unaffected by mutations of the source.
Docs: https://docs.python.org/3/library/stdtypes.html#dict.copy.

The changed operation (`yield ms` → `yield ms.copy()`) is modeled **deeply**:
the impl records an INDEPENDENT per-step value (`snap := stateAt (i-1)`,
appended) rather than a live alias. There is **no consumed copy axiom** — the
proof never depends on one. Instead the deep model's independence guarantee is
validated **== the real `dict.copy()` semantics** out-of-band by
`axiom_check.py` (G-AX): it runs the real `partitions` generator (plus a minimal
`dict.copy()` probe) and asserts that with `.copy()` the gathered list records
the genuine per-step history (gathered-record-i == the i-th partition, all
distinct), whereas without `.copy()` every gathered record aliases the single
dict and reads back as the final state — exactly the model's fix-vs-defect
distinction.

## 4. Conformance seed

`conformance_check.py` pins seed `20154` and fuzzes `partitions` arguments
`(n, m, k, size)` over boundary + random cases (§ that file). The R/I shadow of
`gatherWalk` (a length-`steps` list whose element i is `stateAt i`) is compared
against the gathered post-patch generator, abstracted by the §2 bijection.

## 5. Imports

`Solution.lean` imports `Velvet.Std` only; the proof uses Lean/Mathlib `List`
lemmas (`List.range`, `List.range'`, `List.getElem_range`, `List.range'_succ`)
already available through the front door.
