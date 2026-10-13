# mapping.md — astropy__astropy-12907

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = d16bfe05a744909de4b27f5875fe0d4ed41ce607`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and
records callee provenance / flag dependencies.

Repo file under change: `astropy/modeling/separable.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `combineParallel (left right : List (List Int)) (lc rc : Nat)` | `_cstack(left, right)` — `astropy/modeling/separable.py:219` (changed hunk at body lines 242-245) | the modeled changed function, **array/array branch only** (the branch the gold hunk edits) |
| `blockDiag (left right : List (List Int)) (lc rc : Nat)` | the block-diagonal result `np.hstack([cleft, cright])` builds in the array/array branch — `separable.py:239-247` post-patch | pure spec: block-diagonal dependency matrix of the parallel composition; concrete (R/I), NOT an axiom/A-reference |
| `widenRight (rc : Nat) (row : List Int)` | `cleft = np.zeros((noutp, left.shape[1])); cleft[:lr,:lc] = left` then the right-half of the `hstack` — i.e. each left row followed by `rc` zero columns | pure spec: zero-pad a left-block row on the right |
| `widenLeft (lc : Nat) (row : List Int)` | `cright = np.zeros((noutp, right.shape[1])); cright[-rr:,-rc:] = right` then the left-half of the `hstack` — i.e. `lc` zero columns followed by each right row | pure spec: zero-pad a right-block row on the left |

### 1.1 Scope: which branch of `_cstack` is modeled, and why it suffices

`_cstack(left, right)` (`separable.py:219-247`) has four sub-cases by whether
each operand is a `Model` or an ndarray (a `coord_matrix`). The gold patch
edits **only** the `else` branch where `right` is an ndarray
(`separable.py:244-245`): `cright[-rr:,-rc:] = 1` → `= right`. The symmetric
`left`-is-ndarray branch (`separable.py:239-240`) was already correct
(`cleft[:lr,:lc] = left`). `combineParallel` models the fully-array branch
(both operands are matrices) because that is the branch on which the bug is
observable and the F2P tests trigger it:

- A **nested** CompoundModel like `m.Pix2Sky_TAN() & cm` (where `cm` is itself
  `Linear1D & Linear1D`) recurses in `_separable`: the inner `&` yields a
  coord-matrix ndarray for the right operand, so the outer `_cstack` takes the
  array/array branch. With the pre-patch `= 1`, the right operand's internal
  diagonal structure is overwritten by all-ones, producing the spurious
  off-diagonal `True`s in the issue. The patch restores `= right`, preserving
  the block's own dependency structure.
- FAIL_TO_PASS `cm8 = rot & (sh1 & sh2)`, `cm9 = rot & sh1 & sh2`, and the new
  `cm11 = rot & sh1 & (scl1 & scl2)` all force this branch.

The left operand here is also an ndarray; its handling
(`cleft[:lr,:lc] = left`) is the already-correct mirror of the fix, and is
modeled by `widenRight` (concrete, I-tagged). Modeling both halves as the
single block-diagonal assembly is faithful: it is exactly what
`np.hstack([cleft, cright])` produces once both blocks carry their own rows.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

The table G-CONF (§4.1) and G-AX use to translate values between the Lean
value domain and the Python repo types. A wrong entry surfaces as spurious
G-CONF disagreements (the falsifiability the plan §4 trust statement refers to).

| repo reality | Lean carrier | bijection |
|---|---|---|
| a 2-D `coord_matrix` ndarray of 0/1 (`np.ndarray`, dtype float, shape (rows × cols)) | `List (List Int)` | `M` (ndarray) ↔ `M.tolist()`-shaped `List (List Int)`; `M.shape[0]` ↔ outer `.length`; `M.shape[1]` ↔ each inner row `.length`; the matrix entries 0.0/1.0 ↔ `Int` 0/1 |
| `left.shape[1]` (left input width) | `lc : Nat` | column count of every `left` row; the `require ∀ r ∈ left, r.length = lc` pins rectangularity (a real ndarray is always rectangular) |
| `right.shape[1]` (right input width) | `rc : Nat` | column count of every `right` row; pinned by `require ∀ r ∈ right, r.length = rc` |
| `np.zeros((·,·))` + slice-assignment + `np.hstack` row-wise concat | `List.map` (zero-pad each row) + `++` (row concatenation) | row r of `hstack([cleft,cright])` ↔ `(widenRight rc lrow)` for left rows / `(widenLeft lc rrow)` for right rows; outer `++` = vertical stack of the two blocks |

Observable-equality predicate (plan §10 Q5b): exact integer equality on every
matrix entry AND identical shape. No float tolerance is needed — the matrices
are 0/1 and the downstream `separability_matrix` only tests `!= 0`.

The `require` rectangularity preconditions are sound abstractions of reality:
every numpy `coord_matrix` is rectangular by construction, so the modeled
`mut`-free inputs `left`/`right` always satisfy them. No parameter is `mut`
(directive 5: nothing is mutated; `combineParallel` is a pure assembly).

## 3. Callee provenance — NONE (no axioms, no A-references)

The modeled array/array branch of `_cstack` calls only numpy primitives in the
fixed path: `np.zeros`, ndarray slice-assignment, and `np.hstack`. There is **no
unchanged repo callee** whose contract the proof must assume, so:

- **0 consumed axioms.** The `axioms` region of `Solution.lean` is empty.
- **0 A-references.** `blockDiag`/`widenRight`/`widenLeft` are concrete list
  arithmetic transliterating the numpy block assembly (R/I legs), NOT deep
  models of an opaque callee. G-CONF mechanically refutes them; `axiom_check.py`
  additionally re-confirms `blockDiag == real _cstack` as a non-vacuous witness
  that no axiom is hiding (it is not a load-bearing axiom check).

The sibling functions `_coord_matrix`, `_compute_n_outputs`, `_cdot`,
`_separable` are NOT on the fixed path of the array/array branch and are not
called by the modeled assembly, so they need no axiomatization. (`noutp` from
`_compute_n_outputs` equals `left.shape[0] + right.shape[0]`; in the model the
combined row count is just `left.length + right.length` by the `++`, so `noutp`
is implicit and needs no callee.)

No flag-dependent callees.

## 4. G-CONF / G-AX fuzz seed (pinned for deterministic eval — §4.1, §11.3)

`conformance_check.py` and `axiom_check.py` both seed `random.Random` with
**`12907`** so the consumer-side verdict (§11.3) is reproducible. The R/I shadow
transliterates `widenRight`/`widenLeft`/`blockDiag` (all R/I-tagged) to numpy
and compares against the real patched `_cstack` array/array branch; there is no
A-tagged callee to leave as the real repo callee (§3).
