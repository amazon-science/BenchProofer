# mapping.md — sympy__sympy-12419

## Symbol binding (file:line @ base_commit 479939f8c65c8c2908bbedc959549a257a7c0b0b)

| Lean symbol | Python symbol | location |
|---|---|---|
| `implementation_identityElement` / `problem_spec_identityElement` / `correct_identityElement` | `Identity._entry(self, i, j)` | `sympy/matrices/expressions/matexpr.py:478-483` |
| `IdxCmp` (pure helper) | the three-valued result of comparing the two index expressions `i`, `j` | the `Eq(i, j)` object and its `is S.true` / `is S.false` tests | `matexpr.py:478-480` (post-patch) |
| `IndOutcome` (pure helper) | whether constructing the deferred indicator auto-evaluated it to a plain zero or left it symbolic | `KroneckerDelta(i, j) is S.Zero` vs not, decided inside `KroneckerDelta.eval` | `sympy/functions/special/tensor_functions.py:159-176` |
| `Elem α` (pure helper) | the symbolic value the method returns for one entry | `S.One` / `S.Zero` / `KroneckerDelta(i, j)` | `matexpr.py:479-482` |
| `elemOf` (pure helper) | the body of `_entry` mapping the two observations to the returned value | `matexpr.py:478-482` (post-patch) |

The modeled function is `Identity._entry`, the per-element accessor of the
symbolic identity matrix. It is the only behavior the patch changes and the only
behavior the FAIL_TO_PASS test (`test_Identity`) observes.

### What the function does (base_commit — the buggy version)

```python
def _entry(self, i, j):
    if i == j:            # Python structural equality: True / False only
        return S.One
    else:
        return S.Zero
```

`i == j` here is *Python* structural equality on the two (possibly symbolic)
index expressions: it returns the bool `True` only when the two expressions are
structurally identical, and `False` in EVERY other case — including when `i` and
`j` are distinct symbols whose numeric equality is not yet determined. So an
undetermined comparison is collapsed to `S.Zero`, as if the indices were known to
differ. Summing `e[i, j]` over a range that includes the diagonal therefore loses
the diagonal contribution and the total sum evaluates to `0` instead of `n`.

### What the function does (post-patch — the fix)

```python
def _entry(self, i, j):
    eq = Eq(i, j)            # symbolic equality: S.true / S.false / unevaluated
    if eq is S.true:
        return S.One
    elif eq is S.false:
        return S.Zero
    return KroneckerDelta(i, j)
```

`Eq(i, j)` is SymPy's *symbolic* equality. It evaluates to the singleton
`S.true` only when the indices are known equal, to `S.false` only when known
distinct, and otherwise stays an unevaluated `Equality` object (neither
singleton). The patch distinguishes all three: known-equal → `S.One`,
known-distinct → `S.Zero`, undetermined → `KroneckerDelta(i, j)`, so the diagonal
contribution survives aggregation.

### The second observation, and why the model needs it

`KroneckerDelta(i, j)` is NOT an inert wrapper: `KroneckerDelta.eval`
(`sympy/functions/special/tensor_functions.py:159-176`) runs its OWN settling
procedure and may auto-evaluate the constructor call to a singleton before
`_entry` ever returns it. That procedure is strictly RICHER than `Eq`'s:

```python
diff = i - j
if diff.is_zero:                    return S.One
elif fuzzy_not(diff.is_zero):       return S.Zero
if i.assumptions0.get("below_fermi") and j.assumptions0.get("above_fermi"):
    return S.Zero                   # <-- fermi-level branch; Eq has no analogue
if j.assumptions0.get("below_fermi") and i.assumptions0.get("above_fermi"):
    return S.Zero
```

The fermi-level branch decides pairs `Eq` leaves open. So there are index pairs on
which `Eq(i, j)` is an unevaluated `Equality` — the `undetermined` classification —
yet `_entry` returns a PLAIN `S.Zero`, because the indicator settled itself.
MEASURED against the real patched callee over 6970 index pairs (a 23-assumption
symbol pool plus randomized arithmetic; run in the instance container):

| `Eq` classification | indicator | count | `_entry` returns |
|---|---|---|---|
| `known_equal` | left symbolic | 61 | `S.One` |
| `known_equal` | settled to zero | 3 | `S.One` |
| `known_distinct` | settled to zero | 682 | `S.Zero` |
| `known_distinct` | left symbolic | 750 | `S.Zero` |
| `undetermined` | left symbolic | 4525 | `KroneckerDelta(i, j)` |
| `undetermined` | **settled to zero** | **801** | **`S.Zero`** |

The last row is 15% of the undetermined pairs. A model over the `Eq`
classification ALONE therefore mispredicts there: it asserts a non-zero symbolic
indicator where the real method returns a plain zero. Witness (reproducible in the
container with the gold patch applied):

```python
p = Symbol('p', below_fermi=True); q = Symbol('q', above_fermi=True)
Eq(p, q)                    # Eq(p, q)  -- neither S.true nor S.false
Identity(n)._entry(p, q)    # 0         -- a PLAIN zero
```

The Lean model consequently carries BOTH observations, and the postcondition
states what the method GUARANTEES on each: the symbolic indicator on every
undetermined pair whose indicator survives (the class the defect and the graded
test are about), and a plain zero on the pairs where the indicator settled itself.
A search over 23403 further pairs found NO pair where `Eq` is undetermined and the
indicator resolves to a plain ONE, which is why `IndOutcome` has two constructors
rather than three.

### Lean modeling

- `IdxCmp` records the three-valued comparison status of the two indices — the
  observation the touched branch reads. The comparison itself (`Eq(i, j)` and
  its `is S.true` / `is S.false` tests) is an UNCHANGED upstream operation; its
  trichotomous outcome is carried as plain input data (SPEC_GUIDE §3
  carried-observation refinement):
  - `known_equal` ↔ `Eq(i, j) is S.true`,
  - `known_distinct` ↔ `Eq(i, j) is S.false`,
  - `undetermined` ↔ `Eq(i, j)` is an unevaluated `Equality` (neither singleton).
- `IndOutcome` records the SECOND carried observation — what constructing the
  deferred indicator delivered. `KroneckerDelta.eval` is likewise an UNCHANGED
  upstream operation (the patch imports it, it does not modify it), so its outcome
  enters as plain input data too:
  - `settled_zero` ↔ `KroneckerDelta(i, j) is S.Zero`,
  - `left_symbolic` ↔ `KroneckerDelta(i, j)` is anything else (a genuine
    `KroneckerDelta` term).
  It is read only under the `undetermined` classification, mirroring the real
  method: on the decided branches `_entry` returns its constant without ever
  constructing the indicator.
- `Elem α` is the returned symbolic value, restricted to the three shapes the
  method can produce: `one ↔ S.One`, `zero ↔ S.Zero`, `deferred i j ↔
  KroneckerDelta(i, j)`. `deferred` carries the two indices because the real
  indicator is a function of them; it is structurally distinct from `zero`,
  which is the soundness-critical property: an undetermined comparison whose
  indicator SURVIVES must NOT collapse to a plain zero.
- `elemOf` is the post-patch `_entry` body composed with the indicator's own
  settling; `implementation_identityElement` is its `Id.run do` skeleton (a
  `match` on the classification with a nested `match` on the indicator outcome
  under `undetermined`, mirroring the `if/elif/return` chain plus the
  auto-evaluation of the constructed indicator). The pre-patch impl folds
  `known_distinct` and BOTH undetermined sub-cases together into `zero` (the
  two-valued `if i == j` branch), so it violates the surviving-indicator arm.

## Lean ↔ Python type bijection (used by G-CONF / G-AX)

| Python | Lean | bijection |
|---|---|---|
| `Eq(i, j) is S.true` | `IdxCmp.known_equal` | comparison known to hold |
| `Eq(i, j) is S.false` | `IdxCmp.known_distinct` | comparison known to fail |
| `Eq(i, j)` unevaluated (neither singleton) | `IdxCmp.undetermined` | comparison undetermined |
| `KroneckerDelta(i, j) is S.Zero` | `IndOutcome.settled_zero` | constructing the indicator settled the pair, delivering a plain zero |
| `KroneckerDelta(i, j)` not `S.Zero` | `IndOutcome.left_symbolic` | constructing the indicator left the comparison open |
| `S.One` | `Elem.one` | the constant one |
| `S.Zero` | `Elem.zero` | the constant zero |
| `KroneckerDelta(i, j)` (a genuine term) | `Elem.deferred i j` | deferred equality indicator of the two indices |

The function's observable result is the returned symbolic value; we model it as
`result : Elem α` where `α` is the (opaque) type of an index expression. Only the
two comparison observations of the index pair are observed, so `α` is a free type
parameter. `Elem.deferred` corresponds to the real indicator up to its argument
ORDER, which the real constructor canonicalizes and the inductive does not model
(see the residue note below).

## Callee provenance + flag dependencies

- **No consumed callee axiom.** The behavior the patch changes — which of the
  three symbolic values is returned — is modeled DEEPLY and structurally over the
  two carried comparison observations; SPEC_GUIDE §3 forbids axiomatizing a
  deeply-modeled changed decision. The `axioms` region is empty and **G-AX
  skips**.
- `Eq(i, j)` (the symbolic-equality constructor) and the `is S.true` / `is
  S.false` identity tests are UNCHANGED SymPy operations upstream of the touched
  decision; their net effect is the trichotomous `IdxCmp` carried as input. They
  constrain no output component the spec leaves free.
- `KroneckerDelta(i, j)` is the deferred indicator the fix newly returns in the
  undetermined case; it is modeled structurally as `Elem.deferred i j` (a value
  distinct from `Elem.zero`), not axiomatized. Its own settling procedure is NOT
  re-derived in the model either — it is the `IndOutcome` observation carried as
  input — so the model asserts the indicator is non-zero exactly on the pairs
  where the real constructor left it symbolic, and nowhere else.
- The real `KroneckerDelta` constructor canonicalizes argument ORDER (it sorts the
  two indices by `default_sort_key`), which `Elem.deferred` does not model. G-CONF
  compares the symbolic arm up to that symmetry; the residue is recorded in
  `properties.py` (the position-EXCHANGE rival is rejected by the Lean spec but
  resolves on the real carrier, so it is deliberately not shipped as a reject
  case).
- No flag dependency: `_entry` reads only the two indices.

## G-CONF fuzz seed

Pinned seed: **12419** (see `conformance_check.py` `SEED`). The oracle is the
**REAL** `Identity._entry` from the patched tree — not an in-process replica of
the modeled decision, which would test the model against itself and is exactly
how the earlier revision of this bundle drifted from the repo. The shadow of
`implementation_identityElement` is driven by the two observations read off the
same real SymPy objects (`Eq(i, j)`'s trichotomy and whether
`KroneckerDelta(i, j)` auto-evaluated to `S.Zero`) and diffed against the real
method's returned value over 120000 index pairs: a 22-assumption symbol pool
(including `below_fermi` / `above_fermi`) crossed both orders, constants including
`oo`/`zoo`/`nan`, randomized arithmetic expressions, plus hand-picked edge cases
pinning the discriminating clauses — notably the fermi-level pairs where `Eq` is
undetermined but the indicator settles to a plain zero. The script also FAILS if
any modeled cell goes unexercised, so a clean run cannot come from a corpus that
never reached an arm. Recorded run: `checked=120000 disagreements=0`, cells
`known_equal/left_symbolic=1023 known_equal/settled_zero=63
known_distinct/left_symbolic=18631 known_distinct/settled_zero=15875
undetermined/left_symbolic=73297 undetermined/settled_zero=11111`. As a
regression control the one-observation shadow was run against the same oracle and
is CAUGHT at the first fermi-level edge case
(`oracle=('zero',) shadow=('deferred', p_bf, q_af)`).
