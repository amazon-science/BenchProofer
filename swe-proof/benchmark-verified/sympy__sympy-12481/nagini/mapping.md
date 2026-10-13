# mapping.md — sympy__sympy-12481

Binds every `model.py` symbol to its repository counterpart at
`base_commit = c807dfe7569692cad24f02a08477b70c1679a4dd`, states the type
abstraction, and gives the provenance of the deep-model reference (the real
cyclic-form construction the deep model is validated against by G-AX).

Repo file under change: `sympy/combinatorics/permutations.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `compose_cycles(n, a, b, c, d)` | `Permutation.__new__` cyclic-form branch — `sympy/combinatorics/permutations.py:801` (changed hunk at body lines 897-906) | the modeled changed behaviour: build the array form of a cyclic-form input, allowing non-disjoint cycles |
| `swap_val(x, a, b)` *(deep model — A-reference)* | the action of one cycle as a map, i.e. the `Cycle` dict built in `Cycle.__init__` / applied in `Cycle.__call__` (`permutations.py:316-342, 442-447`) | pure spec: image of a point under one two-element cycle |
| the two-swap composition in `compose_cycles` *(deep model — A-reference)* | `c = Cycle(); for ci in args: c = c(*ci); aform = c.list()` — `permutations.py:914-917` (the cyclic branch that runs once the duplicate guard is removed) | pure spec: left-to-right composition of the cycles into the array form |

The pre-patch repo lines the change removes (for the refinement audit, not
referenced from the consumer spec view): the cyclic-form arm of the duplicate
guard in `Permutation.__new__`,

```python
temp = flatten(args)
if has_dups(temp):
    if is_cycle:
        raise ValueError('there were repeated elements; to resolve '
        'cycles use Cycle%s.' % ''.join([str(tuple(c)) for c in args]))
    else:
        raise ValueError('there were repeated elements.')
```

becomes

```python
temp = flatten(args)
if has_dups(temp) and not is_cycle:
    raise ValueError('there were repeated elements.')
```

i.e. the `is_cycle` (cyclic-form) duplicate rejection is dropped, so
non-disjoint cycles fall through to the composition arm.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| cyclic-form input `args = [[...], [...], ...]` (a list of cycles, each a list of `int` points) | the two GENUINE two-element cycles `(a b)`, `(c d)` given as four `int` params, with `a != b` and `c != d` (model `Requires`) | the smallest non-trivial cycle is a two-element swap of two DISTINCT points; the model's domain `a != b ∧ c != d` is exactly the real callee's accepting set — the within-cycle uniqueness check (untouched by the change) rejects a repeated point inside one cycle (`[e, e]` raises "All elements must be unique in a cycle"), while only the CROSS-cycle (non-disjoint) rejection is removed. The two cycles MAY still share a point with each other (the non-disjoint case the change enables). The F2P/problem witnesses that are pairs of genuine two-element cycles are `[[0,1],[0,2]]` (share point 0) and `[[0,1],[0,1]]` (coincide) — encoded directly as `compose_cycles`. The remaining F2P-removed witness `[[1],[1,2]]` pairs a SINGLETON cycle `[1]` with the swap `(1 2)`; a singleton `[e]` is the IDENTITY on `e` (it is NOT the swap `(e e)`, which would raise the within-cycle uniqueness error), so it is OUTSIDE the two-genuine-swap domain and is handled in axiom_check.py by the faithful `single_then_swap` model (singleton = identity, then swap), not by `compose_cycles`. |
| array form `aform` (a `list` of `int`, the second line of the two-line form) | `List[int]` of length `n`; specification over `PSeq[int]` via `ToSeq` | `aform[i]` ↔ `ToSeq(Result())[i]`; `len(aform)` ↔ `n`; `Cycle.list()`/`size` extension to `n` ↔ the loop building `n` entries |
| `Cycle(*ci)` acting on a running permutation (`Cycle.__call__`) | applying `swap_val(·, a, b)` point-wise to the current array | the running `Cycle` dict maps each point; applying it to position `i`'s current value is `swap_val(cur[i], a, b)`; left-to-right composition is `swap_val(swap_val(i, a, b), c, d)` |
| `Permutation(0, 1, 2)` etc. (the RHS of the F2P equality) | the array form `[1, 2, 0]` it denotes | a single cycle `(0 1 2)` ↔ array `[1, 2, 0]`; equality of `Permutation`s is equality of array forms (`_hashable_content` = `tuple(array_form)`, `permutations.py:956`) |

`size` extension never truncates here: every point `a, b, c, d` is `< n`
(model `Requires`), so the natural array length `max(point)+1 ≤ n`, and
`Permutation(..., size=n)` extends to exactly length `n`.

## 3. Deep-model reference (kind A-reference — checked by G-AX / axiom_check.py)

### 3.1 `swap_val` composition ↔ the real `Cycle`/`Permutation` cyclic-form construction (A-reference)

**Callee (unchanged machinery the changed branch invokes):** the `Cycle` class
(`permutations.py:233-462`), specifically:

```python
def __call__(self, *other):           # left-to-right product of cycles
    rv = Cycle(*other)
    for k, v in zip(list(self.keys()), [rv[self[k]] for k in self.keys()]):
        rv[k] = v
    return rv
def list(self, size=None):            # explicit array form 0..size-1
    ...
    return [self[i] for i in range(size)]
```

The changed `Permutation.__new__` branch composes the input cycles with exactly
this machinery (`c = Cycle(); for ci in args: c = c(*ci); aform = c.list()`).
The CHANGE itself — removing the `is_cycle` duplicate rejection — does not touch
`Cycle`; it merely lets non-disjoint cycles reach this composition. So the
composition is modelled **deeply** (`swap_val` + the verified loop), and that
deep model is validated **== the real callee** out-of-band by G-AX; nothing is
consumed as an axiom.

`Cycle.__call__` composes **left to right**: `self` (the cycles already
accumulated) acts first, then the new cycle `other`. Applied to the identity,
two cycles `(a b)` then `(c d)` send point `i` to `(c d)((a b)(i))`, i.e.
`swap_val(swap_val(i, a, b), c, d)` — which is what `compose_cycles` computes
and pins in its postcondition. The result is always a genuine rearrangement of
`0..n-1` (a bijection), so it is well defined for non-disjoint cycles too.

**Soundness check (G-AX):** `axiom_check.py` imports the repository `sympy`
(run in-container with the gold patch applied, where it is installed) and
asserts the deep model equals the real
`Permutation([[a, b], [c, d]], size=n).array_form` for **all** `(a,b,c,d)` with
`a != b ∧ c != d` (the model `Requires` domain) and `n ≤ 6` (exhaustive over
the touched points: 1484 cases), plus 20 000 randomized larger sizes of genuine
two-element cycles, plus the explicit problem-statement / FAIL_TO_PASS
witnesses (`[[0,1],[0,2]] == (0 1 2)`; `[[0,1],[0,1]]` = identity; `[[1],[1,2]]`
constructs without raising and yields `[0,2,1]`, checked against the faithful
singleton model `single_then_swap`). Every observation must match; exit 0 iff
sound. The guarded sweep covers every CROSS-cycle non-disjoint configuration
(the two cycles share a point with each other) — precisely the behaviour the
change enables — while excluding only the within-cycle-repeat inputs that the
real callee still rejects (so the swept domain is exactly the callee's
accepting set: a domain-congruence assertion in the harness confirms no
in-domain input raises).

## 4. No consumed axioms

There is **no `@ContractOnly` axiom** in this bundle. The only operation that
changed — admitting and composing non-disjoint cycles — is modelled deeply
(`swap_val` + the verified composition loop). The `Cycle` machinery the branch
calls is unchanged and is the A-reference validated by G-AX above; it is not a
contract the proof consumes.
