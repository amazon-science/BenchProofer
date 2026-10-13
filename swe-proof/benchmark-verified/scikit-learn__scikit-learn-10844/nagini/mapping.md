# mapping.md — scikit-learn__scikit-learn-10844

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 97523985b39ecde369d83352d7c3baf403b60a22`, states the type
abstraction, and gives the provenance of each axiom (callee + the exact
behaviour the axiom encodes).

Repo file under change: `sklearn/metrics/cluster/supervised.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `pair_similarity_index(tk, pk, qk, m)` | the score-assembly tail of `fowlkes_mallows_score(labels_true, labels_pred, sparse=False)` — `sklearn/metrics/cluster/supervised.py:856-859` (the `tk`/`pk`/`qk` computation + the `return tk / np.sqrt(pk * qk) if tk != 0. else 0.` line) | the modeled changed function (the index assembly that overflowed) |
| `ratio(a, b, m)` *(axiom — A-consumed)* | real division `/` (numpy/`__truediv__`), used at `:859` (`tk / np.sqrt(...)` pre-patch; `tk / pk` and `tk / qk` post-patch) | unchanged numeric division callee |
| `root(x, m)` *(axiom — A-consumed)* | `numpy.sqrt`, used at `:859` (`np.sqrt(...)`) | unchanged numeric square-root callee |
| `mul(x, y)` *(axiom — A-consumed)* | real multiplication `*`, used at `:859` (`np.sqrt(tk/pk) * np.sqrt(tk/qk)` post-patch) | unchanged numeric multiplication callee |
| `tk` | `tk = np.dot(c.data, c.data) - n_samples` (`:856`) | concordant-pair count |
| `pk` | `pk = np.sum(np.asarray(c.sum(axis=0)).ravel() ** 2) - n_samples` (`:857`) | first-clustering pair-count (marginal) |
| `qk` | `qk = np.sum(np.asarray(c.sum(axis=1)).ravel() ** 2) - n_samples` (`:858`) | second-clustering pair-count (marginal) |
| `m` | the maximum representable magnitude of the integer domain the marginals are widened into (the `np.int64` domain after `.astype(np.int64)`); `INT64_MAX` in axiom_check.py | the finite numeric domain bound (overflow threshold) |

The pre-patch repo line the change replaces (for the refinement audit, not
referenced from the consumer spec view):
`c = contingency_matrix(labels_true, labels_pred, sparse=True)` (`:855`, the
contingency matrix is NOT widened) and
`return tk / np.sqrt(pk * qk) if tk != 0. else 0.` (`:859`, the cross product
`pk * qk` is formed before the square root).

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `tk`, `pk`, `qk` — numpy integer scalars (widened to `np.int64` by the fix) | interpreted `float` (`--float-encoding=real`) | each non-negative integer count ↔ the equal real; the modeled behaviour (divide / sqrt / multiply, and the bounds the tests probe) is real-valued, so the carrier is the interpreted real |
| the int64 representable bound (`np.iinfo(np.int64).max`) | `float m` with `Requires(m >= 1.0)` and the per-marginal `Requires(pk <= m, qk <= m)` | the marginals are widened to a domain that holds each marginal but not necessarily their cross product; `m` is that domain's maximum magnitude |
| `n_samples` (the count subtracted to form `tk`/`pk`/`qk`) | folded into the carrier values | `tk`/`pk`/`qk` already denote the post-subtraction counts; the structural facts `0 <= tk <= pk`, `0 <= tk <= qk` are stated as preconditions (see §3) |
| `np.sqrt`, `/`, `*` on these scalars | `root`, `ratio`, `mul` axioms over reals | the three numeric operations are interpreted-real-uninterpreted in Nagini 1.2.0 for ordering/bounds, so each is modeled by the weakest sufficient real-arithmetic contract and validated against the real operation by axiom_check.py |

`float` is the carrier because the tested behaviour is numeric finiteness and
floating value (the F2P test asserts the result is **finite**; the P2P tests
assert exact floating values). `--float-encoding=real` is therefore mandatory
and recorded in meta.json.

### Structural-fact provenance (the preconditions)

The preconditions `0 <= tk`, `tk <= pk`, `tk <= qk`, `pk <= m`, `qk <= m` are
genuine facts of the upstream computation, not assumptions that smuggle in the
answer:
- `tk = Σ c_ij² − n`, `pk = Σ (Σ_i c_ij)² − n`, `qk = Σ (Σ_j c_ij)² − n` with
  `Σ c_ij = n`. Since `Σ c_ij² ≥ Σ c_ij = n`, `tk ≥ 0`; likewise `pk, qk ≥ 0`.
- A concordant pair is also counted by each marginal: `Σ c_ij² ≤ Σ (Σ_i c_ij)²`
  and `Σ c_ij² ≤ Σ (Σ_j c_ij)²` (a sum of squares is ≤ the square of the sum
  over any partition refinement), hence `tk ≤ pk` and `tk ≤ qk`.
- Each marginal is `≤ n²` which fits the int64 domain the fix widens into
  (`n` ≤ ~7.5e4 in the failing test ⇒ marginal ≤ ~5.6e9 ≪ 9.2e18 = `m`), so
  `pk ≤ m`, `qk ≤ m`. Their cross product `pk·qk` (≈ 1.7e19) does NOT fit `m`.
  Verified numerically in axiom_check.py against the actual failing-test labels.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

All three axioms model **unchanged** numeric operations the score assembly uses
both before and after the fix (the fix changes only the *evaluation order* and
the integer *width*, not which arithmetic operations are invoked). Each is the
weakest sufficient contract the proof consumes, and each is gated by a
representability precondition (`<= m`) that models the finite numeric domain.

### 3.1 `ratio(a, b, m)` ↔ real division `a / b`
For `0 <= a <= b <= m` and `b > 0`, the quotient is a real in `[0, 1]` equal to
`a / b`. Used by the fix as `tk / pk` and `tk / qk` (each a unit-interval
conditional ratio). The axiom is the weakest fact the proof needs: the exact
quotient plus its unit-interval bound. G-AX runs real Python/`numpy` division on
boundary + 200 000 fuzz inputs satisfying the Requires and checks the bound.

### 3.2 `root(x, m)` ↔ `numpy.sqrt`
For `0 <= x <= m`, `np.sqrt(x) >= 0`, and `np.sqrt(x) <= 1` when `x <= 1`
(monotone, `sqrt(1) = 1`). The axiom carries ONLY these bounds — no exact value —
because that is all the proof consumes. Its `Requires(x <= m)` is the crux: a
value that has overflowed the domain (e.g. the cross product `pk * qk`) is NOT
admissible as a square-root argument, which is exactly why the pre-patch
evaluation order is rejected. Docs: numpy.org/doc/stable/reference/generated/numpy.sqrt.html.
G-AX runs `math.sqrt` on boundary + fuzz inputs and checks non-negativity and
unit-interval preservation.

### 3.3 `mul(x, y)` ↔ real multiplication `x * y`
For `x, y` in `[0, 1]`, the product is in `[0, 1]` and equals `x * y`. Used by the
fix as `np.sqrt(tk/pk) * np.sqrt(tk/qk)`. Weakest sufficient contract: the exact
product plus its unit-interval bound. G-AX runs real multiplication on boundary +
fuzz inputs and checks the bound.

**Soundness check (G-AX):** `axiom_check.py` runs the real `/`, `math.sqrt`, `*`
on boundary inputs (incl. the actual `tk`/`pk`/`qk` magnitudes of the failing
test) plus 600 000 randomized fuzz inputs, asserting every observation meets the
corresponding axiom's Ensures. It additionally confirms the overflow
discriminator the bundle turns on: with the real failing-test marginals,
`pk <= m` and `qk <= m` while `pk * qk > m`, and the divide-first order yields a
finite result in `[0, 1]` agreeing with the (Python-bignum-only) direct order.
Imports only the standard library (`math`, `random`). Exit 0 iff sound.

## G-CONF (differential conformance — `conformance_check.py`)

The refinement leg no other gate covers: does the MODEL's impl region agree with
the REAL patched repo function? Refuted-or-not by execution, not proved.

| leg | realization |
|---|---|
| SHADOW | the `# impl-start`/`# impl-end` region of `model.py` copied **verbatim** (byte-identical; contracts live outside the markers, so nothing inside had to be stripped). No `@Pure` helpers exist (`pure` region is empty) and the region uses no `PSeq`/`ToSeq`, so no carrier shim is needed. |
| `@ContractOnly` callees | realized by the REAL operations they axiomatize (§3): `ratio` → `/`, `root` → `numpy.sqrt`, `mul` → `*`. Each realization asserts its own `Requires` at call time, so the representability gate `root: x <= m` is *executed*, not assumed. |
| ORACLE | **called**, not transliterated: `sklearn.metrics.cluster.supervised.fowlkes_mallows_score` (`supervised.py:852-859`), with the gold patch applied by the gate. The script re-reads `inspect.getsource` at startup and refuses to run unless both `astype(np.int64)` and `np.sqrt(tk / pk) * np.sqrt(tk / qk)` are present, so a patch-apply failure can never be scored as conformance. |
| TYPE BRIDGE (§2 inverted) | the model carrier is `(tk, pk, qk, m)` reals; the repo function's input is a label-array pair. The three aggregates are **observed out of the real function's own frame** (a `sys.settrace` hook scoped to `fowlkes_mallows_score.__code__`, read at its `return` event) rather than recomputed — recomputing `np.dot(c.data, c.data) - n_samples` here would test the reimplementation, not the repo. numpy int64 → `float` (exactness asserted: every observed count `< 2**53`); `m = float(np.iinfo(np.int64).max)` per §2. |
| comparison | **exact** float equality. The shadow performs the same three IEEE ops in the same order as the patched line, so any tolerance would mask exactly the reassociation the bundle is about. |
| `Requires` screen | every input is screened against the model's preconditions. A *reachable* repo input violating them would mean the precondition excludes real behaviour, so it is reported as a **disagreement**, never skipped. None occurs. |

**Inputs — 106 296 checked (>= 1e5), pinned seed `SEED = 10844`:**
- 14 boundary cases: empty, singleton, both impl branches (`tk == 0` / `tk != 0`), perfect agreement, relabelled perfect agreement, all-one-cluster, all-distinct, skew, and the exact F2P workload of `test_int_overflow_mutual_info_fowlkes_mallows_score` plus ×2/×3 tilings of it — the large-count regime where `pk, qk <= m` while `pk * qk > m` (3 inputs land in it).
- **exhaustive** enumeration of the label-pair space for every `n <= 4` with labels in `range(n)` — 66 282 pairs, the complete reachable input space at those sizes (stronger than sampling it).
- 40 000 seeded fuzz draws (`n` in `[2, 80]`, up to `n // 2` classes/clusters each side) to carry the count past 1e5.
- Branch coverage recorded in the structured report: `tk == 0` on 44 854 inputs, `tk != 0` on 61 442.

**Negative control (runs first; the script exits 1 if any wrong tail survives).**
Four plausible-but-wrong tails are diffed against the oracle on the boundary
catalogue and all four are refuted: the pre-patch cross-product-first order
`tk / np.sqrt(pk * qk)` in the int64 domain, the un-rooted squared index
`(tk/pk)*(tk/qk)`, the single-ratio `sqrt(tk/pk)` (drops `qk`), and a non-zero
`tk == 0` branch. A check that cannot refute anything is worse than no check.

**Recorded verdict:** exit 0, `status=pass`, 0 disagreements over 106 296 inputs.
stdlib + numpy + the patched repo only.
