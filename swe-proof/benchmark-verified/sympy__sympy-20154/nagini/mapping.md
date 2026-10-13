# mapping.md — sympy__sympy-20154

Binds every `model.py` symbol to its repository counterpart at
`base_commit = bdb49c4abfb35554a3c8ce761696ffff3bb837fe`, states the type
abstraction, and gives the provenance of the (single, non-consumed) callee the
deep model is validated against.

Repo file under change: `sympy/utilities/iterables.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `gather_walk(steps)` | `list(partitions(...))` — the act of GATHERING the generator `partitions` (`sympy/utilities/iterables.py:1696`) into a list, as every F2P test does (`[p.copy() for p in partitions(...)]`, `list(uniq(... for p in partitions(...)))`) | the modeled behaviour: gathering the enumerator's per-step records into a list |
| `state_at(i)` | the working partition dictionary `ms`'s CONTENT at the i-th yield (`iterables.py:1798` initial, mutated through the `while` loop body `1809-1847`) | pure spec: the working state at step i, abstracted to a per-step strictly-increasing value |
| (the live integer `work` in the impl) | the single reused dict object `ms` (`iterables.py:1798`) that the generator mutates in place across yields | the live working record the enumerator advances in place |
| (each `snap` appended in the impl) | the object handed out by each `yield` — `ms.copy()` post-patch vs the live `ms` pre-patch (`iterables.py:1805/1807/1845/1847`) | the per-step record handed out (an independent snapshot post-patch) |

The pre-patch repo behaviour the change removes (for the refinement audit, not
referenced from the consumer spec view): the four `yield ms` / `yield
sum(ms.values()), ms` statements hand out the LIVE `ms` object
(`iterables.py:1805,1807,1845,1847`), so `list(partitions(...))` returns a list
whose entries all alias that one dict and read back as its final mutated state.
The accompanying docstring caveat ("the _same_ dictionary object is returned
each time", `iterables.py:1741-1754`) is also deleted by the gold patch.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| the working partition `dict` `ms : {int: int}` (a multiplicity mapping) | a single mutable working record advanced in place; abstracted to the integer `work` holding its per-step identity | the bug + the F2P tests never depend on the *internal structure* of `ms`, only on whether two gathered records are independent snapshots or the same evolving object; the abstraction keeps exactly the observable that the tests probe: gathered-record-i equals the state at step i (distinct per step) vs all-equal-to-final |
| `list(partitions(...))` / `[p.copy() for p in partitions(...)]` (gather a generator) | the impl loop that appends one record per step into `result : List[int]` | gathering n yields ↔ a length-n list; the k-th gathered record ↔ `result[k]` |
| `ms.copy()` (the added per-yield duplication) | recording `snap = work` BY VALUE before appending | `dict.copy()` produces a fresh, independent object equal in contents to `ms` at the moment of the yield; by-value capture of `work` is the same independence guarantee in the integer abstraction (a later mutation of `work`/`ms` does not reach the gathered record) |
| each yielded partition's per-step value (e.g. `{2: 3}`, `{1: 2, 2: 2}`, ... distinct across steps) | `state_at(i) == i + 1` (strictly increasing) | the genuine per-step difference of the partitions is abstracted to a strictly-increasing per-step value; this is what makes the alias defect observable (an aliasing gather collapses every record to a single value, so it cannot reproduce a strictly-increasing per-step list) |

`dict` indexing/iteration and `dict.copy()` are awkward to carry through
Nagini's quantified-permission fragment for a list of distinct dict objects
(the receivers `result[k].content` are not provably injective without a
quadratic pairwise-distinctness invariant that does not converge); the
behaviour the tests observe — per-step independence of gathered records — is
carried faithfully in the value domain instead. See §3.

**Termination (total correctness):** the real gather always answers —
`list(partitions(n, m, k))` walks a finite enumeration (the partition count of
a bounded `n` is finite and the generator's `while keys != [1]` loop strictly
decreases its multiset) and returns its gathered list. The spec carries
`Requires(MustTerminate(2))` on `gather_walk` (consumed in the impl loop by
`Invariant(MustTerminate(steps - i + 1))`). Nagini is a partial-correctness
verifier by default, so without the obligation a diverging implementation
would satisfy every `Ensures` vacuously while sharing the spec — the exact
spec-too-weak (vacuous-divergence) class G-PANEL-1 probes.

## 3. The duplication primitive (A-reference — checked by G-AX / axiom_check.py)

### 3.1 `snap = work` (by-value record) ↔ `ms.copy()` (`dict.copy`)
**Callee:** CPython `dict.copy()` (equivalently the `dict(...)` / `{**d}`
constructor) — returns a NEW dict object that is a shallow copy: a distinct
object (`copy is not d`) whose key/value pairs equal the source's at the moment
of the call, and which is thereafter unaffected by mutations of the source.
Docs: https://docs.python.org/3/library/stdtypes.html#dict.copy.

The changed operation (`yield ms` → `yield ms.copy()`) is modeled **deeply**:
the impl records an INDEPENDENT per-step value (`snap = work`, appended) rather
than a live alias. There is **no consumed `dict_copy` axiom** — the proof never
depends on one. Instead the deep model's independence guarantee is validated
**== the real `dict.copy()` semantics** out-of-band by `axiom_check.py` (G-AX):
it runs the real `partitions` generator (and a minimal `dict.copy()` probe) and
asserts that with `.copy()` the gathered list records the genuine per-step
history (gathered-record-i == the i-th partition, all distinct), whereas
without `.copy()` every gathered record aliases the single dict and reads back
as the final state — exactly the model's fix-vs-defect distinction.

**Soundness check (G-AX):** `axiom_check.py` imports only the standard library
(`sympy.utilities.iterables.partitions` is the repo function under test, run in
the harness container; the `dict.copy` semantics it relies on are pure stdlib).
It executes `partitions` on boundary + fuzz arguments and asserts:
(a) `[p.copy() for p in partitions(...)]` (independent snapshots) lists the
genuine, pairwise-distinct per-step partitions; (b) gathering WITHOUT copying
(`list(partitions(...))`) collapses every entry to the final state when more
than one partition is produced — confirming the modeled defect; and (c) a
direct `dict.copy()` probe satisfies the independence properties the deep model
encodes (distinct object, equal contents, source-mutation-isolated). Exit 0 iff
sound.

## G-CONF (differential conformance — `conformance_check.py`)

The refinement leg no other gate covers: does the MODEL agree with the REAL
patched repository function? G-VERIFY says the impl meets the spec, G-PBT says
no wrong impl meets it, G-AX validates the A-reference duplication primitive —
none of them diffs `gather_walk` against `partitions`.

**Shadow (provenance `direct`).** The model IS Python, so the shadow is the
`# impl-start` .. `# impl-end` region of `model.py` copied VERBATIM with only
the contract calls (`Requires`, `Ensures`, `Invariant`, `MustTerminate`) and the
`# invariants-start/-end` markers deleted, plus the `@Pure` helper `state_at`
minus its contracts. The nine executable statements of the region are
byte-identical to the frozen artifact — no paraphrase, no restructuring. No
`PSeq`/`ToSeq` shim is needed (the model carries plain `List[int]`/`append`),
and the `# axioms-start` region is empty with no `@ContractOnly` callee, so
there is no axiom stub to redirect at a repo function.

**Oracle (CALLED, not transliterated).** `sympy.utilities.iterables.partitions`
(`sympy/utilities/iterables.py:1696` @ `base_commit`), gathered into a list —
§1's binding `list(partitions(...))`, which is what every F2P assertion does.
The gate applies `patch.diff` to `/testbed` and sets `PYTHONPATH` before the
script runs, so the imported generator is the patched (copy-on-yield) one. The
generator is never reimplemented: driving it in-container needs no context
beyond three integer arguments and a bool.

**Type bridge (§2, inverted).**

| concrete (repo) | abstract (model) | conversion |
|---|---|---|
| the argument tuple `(n, m, k, size)` + an `islice` bound `limit` | — | the generated input |
| the number of records the walk performs | `steps : int` | `steps = len(T)` where `T = [copy of y for y in islice(partitions(...), limit)]` — the per-step history snapshotted at consume time, the way the F2P tests take it (`[p.copy() for p in partitions(...)]`). `T` is **patch-independent** (the gold patch changes only what the yields hand out, never the enumeration), so it is a legitimate ruler for both sides. Deriving `steps` from `T` and not from `len(list(partitions(...)))` is what keeps the `len(Result()) == steps` postcondition leg under test rather than trivially true. |
| gathered record `G[k]` (a `dict`, or `(M, dict)` when `size=True`) | `Result()[k] : int` | `alpha(G)[k] = state_at(j) = j + 1` for the unique step `j` with `G[k] == T[j]`; a record matching no step abstracts to the sentinel `0`, outside `state_at`'s range so it always disagrees. `T`'s pairwise distinctness (which makes `j` unique) is asserted per input and reported as a BRIDGE VIOLATION rather than silently absorbed. |
| gathered records must be **fresh, independent objects** (the `ms.copy()` row of §2) | by-value `snap` capture | object-identity aliasing among the gathered records is itself a disagreement, so the independence leg is checked and not merely its value shadow. |

Under the patched generator each `G[k]` is an independent snapshot equal to
`T[k]`, so `alpha(G) == [1, .., steps]` and the shadow must match exactly.

**Input domain.** Every input satisfies `Requires(steps >= 0)` (`steps =
len(T) >= 0` by construction; `MustTerminate` is an obligation, not a value
constraint) and every argument tuple is one the real generator accepts. The
`islice` bound `limit` is what reaches `steps == 0` — the real generator always
yields at least once, so a zero-step gather of it is exactly `limit = 0` — and
it also exercises partial gathers; both impl branches are therefore covered
(loop body taken zero times and many times). Composition:

* **160 boundary** — every argument shape the F2P `test_partitions` asserts on
  (`partitions(0)`, `(1, 0)`, `(6, 2, 2)`, `(6, 2, 0)`, `(6, 2, None)`,
  `(6, k=2)`, `(6, k=3)`, `(8, k=4, m=3)`, `(S(3), m=2)`, `(4, k=3)`, `(4)`),
  each with `size` False and True and `limit` in {full, 0, 1, 3}, plus every
  branch of the real function (the degenerate `yield {}` early return, the first
  yield, the loop yield, the `if not keys: return` exhaustion path) and the
  exact F2P call with a sympy `Integer` argument.
* **5096 exhaustive** — the finite grid `n` in 0..12 x `m`, `k` in
  {None} u 0..12 x `size` in {False, True}, full gathers, enumerated
  exhaustively. The modeled input space itself is infinite (`steps` is
  unbounded), so this is a sub-block, not a completeness claim.
* **94744 seeded fuzz** — a wider grid (`n <= 24`, `m`/`k` in {None} u 0..9,
  random `limit`) filling the count.

**Total 100000 inputs. Pinned seed: `SEED = 20154`** (module constant). stdlib
only; ~11s wall.

**Refutability, controlled.** The check was negative-controlled against three
mutant generators before being accepted, so a green verdict is evidence and not
decoration:

1. the **pre-patch** generator (`yield ms`, live alias) — reported
   `gathered=[{}, {}, {}, {}]` non-independent at the first boundary input,
   exit 1;
2. a mutant handing out **distinct fresh objects but write-backing** every
   already-gathered record to the current state (`model_prepatch.py`'s exact
   defect, which defeats the object-identity heuristic) — reported
   `shadow=[1, 2, 3, 4]` vs `oracle=[4, 4, 4, 4]`, exit 1;
3. the **post-patch** generator — 0 disagreements, exit 0.

**Recorded verdict: `G-CONF = pass`** — exit 0, 0 disagreements over 100000
checked inputs (seed 20154). The shadow of `gather_walk`/`state_at` agrees with
the real patched `partitions` gather, so the theorem G-VERIFY proves is a
theorem about the behaviour the repository actually has.
