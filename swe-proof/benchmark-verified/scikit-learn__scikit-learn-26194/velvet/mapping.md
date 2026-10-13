# mapping.md — scikit-learn__scikit-learn-26194

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = e886ce4e1444c61b865e7839c9cff5464ee20ace`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and gives
the provenance of the upstream callee.

Repo file under change: `sklearn/metrics/_ranking.py` (function `roc_curve`).

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `withLeadingSentinel (base : List Rat)` | the threshold-anchoring step of `roc_curve` — `sklearn/metrics/_ranking.py:1086` (`thresholds = np.r_[…, thresholds]`) | the modeled changed function: it prepends one extra leading position to the threshold vector |
| `base : List Rat` | the `thresholds` vector at line 1086 *before* the prepend (i.e. the post-`drop_intermediate` value returned by `_binary_clf_curve`) | the ordered finite thresholds the anchoring step receives |
| `out : List Threshold` | the `thresholds` vector *after* line 1086 | the anchored threshold vector returned by `roc_curve` |
| `Threshold.top` | `np.inf` (post-patch leading element) | the sentinel position classifying no instance positive |
| `Threshold.value r` | a finite element of the `thresholds` ndarray | an ordinary finite threshold |
| `finiteSeq` | identity on the `thresholds` content (each finite score lifted unchanged) | order/value-preserving lift |

The change is confined to one statement (line 1086): the leading element of the
returned `thresholds` array. The pre-patch repo expression the change removes
(refinement audit only, not in the consumer spec view) is `thresholds[0] + 1`.

### Upstream callee (NOT modeled; the input carrier — G-AX validated)
`_binary_clf_curve(y_true, y_score, …)` (`sklearn/metrics/_ranking.py:739`) and
the subsequent `drop_intermediate` masking (lines 1075–1083) together produce the
finite `thresholds` vector bound to `base`. This callee is **unchanged** by the
patch; the modeled function only consumes its output. We do not axiomatize it: it
is run as the **real callee** in both gate scripts. The two structural facts the
spec relies on — that `base` is **non-empty** (`require base ≠ []`) and contains
only **finite** scores — are guaranteed by the real callee and checked by G-AX
(see §3), never assumed via a Lean `axiom`.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) and G-AX use to translate values between the Lean
value domain and the Python repo types.

| repo reality | Lean carrier | bijection |
|---|---|---|
| a finite element of the `thresholds` ndarray (a real score, IEEE-754 double) | `Threshold.value (r : Rat)` | a finite float `x` ↔ `Threshold.value (Rat.ofScientific…)`; G-CONF compares **order and value** (the only properties the anchoring step and the F2P tests observe), so the exact rational image is irrelevant — only finiteness and the elementwise value/order matter. CLAUDE.md: model value/order with `Rat`, never `Float`. |
| the post-patch leading element `np.inf` | `Threshold.top` | `np.inf` ↔ `Threshold.top`; the sentinel is a distinct constructor, never a finite value. The F2P discriminator `np.isinf(thresholds[0])` ↔ `out.head? = some Threshold.top`. |
| the `thresholds` ndarray (1-D) | `List Threshold` | array ↔ list, same length, same order; `np.r_[a, xs]` ↔ `a :: xs`. |
| the pre-`prepend` finite vector | `List Rat` (`base`) | elementwise finite-float ↔ `Rat`, order preserved. |

**Why `Threshold` is an inductive, not `Float`.** The behavior the patch changes
is *which kind of value* leads the threshold vector: a finite number
(`max + 1`, pre-patch) versus the infinite sentinel (`np.inf`, post-patch). Lean
`Float` is FFI-opaque: `decide` cannot reduce `(1.0/0.0).isInf`, `native_decide`
is banned, and `loom_smt`/cvc5 cannot model IEEE infinities (measured — probe in
construction log). Modeling the sentinel as a **constructor** (`top`) makes the
discriminator a structural, decidable check that `loom_solve` discharges, and
makes "the sentinel is not a finite score" true *by construction* (`value _ ≠
top`) — which is exactly the property the issue demands and the prepatch violates.

## 3. Callee provenance (the input carrier — checked by G-AX / axiom_check.py)

There are **no Lean `axiom`s** and **no deep-model references** in this bundle:
the changed operation (the prepend) is modeled directly and concretely; the only
upstream dependency (`_binary_clf_curve` + drop) is the *input carrier*, run as
the real callee by both gate scripts rather than abstracted.

`axiom_check.py` (G-AX) nonetheless discharges the two structural facts the spec's
`require`/typing rely on, by executing the **real** `_binary_clf_curve` (+ the
real `drop_intermediate` mask) over boundary and fuzzed `(y_true, y_score)`
inputs and asserting, for the `thresholds` vector handed to the anchoring step:

1. it is **non-empty** (justifies `require base ≠ []`) — guaranteed because
   `threshold_idxs` always contains `y_true.size - 1` (`_ranking.py:786`), and
   the drop mask keeps the first and last index (`np.r_[True, …, True]`,
   `_ranking.py:1077`);
2. every element is **finite** (justifies the `Rat`/`Threshold.value` carrier and
   the claim that the new `np.inf` lead is categorically above all of them) —
   guaranteed because the thresholds are a subsequence of `y_score`, and
   `_binary_clf_curve` calls `assert_all_finite(y_score)` (`_ranking.py:773`).

Exit 0 iff both hold on every probed input. Imports only `numpy` + the repo
(`sklearn.metrics._ranking`), available in the instance image.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`26194`** so the
consumer-side verdict is reproducible. The R/I shadow it builds transliterates the
impl region (`Threshold.top :: finiteSeq base`) to Python as
`[np.inf, *base_thresholds]` and diffs it against the **real patched
`roc_curve`**'s returned `thresholds` over ≥10⁵ fuzzed `(y_true, y_score,
drop_intermediate)` inputs. There are no A-tagged callees inside the impl region,
so the shadow is pure R/I; `base` itself is obtained by calling the real
`_binary_clf_curve`/drop pipeline (the unchanged input carrier), so the only thing
under differential test is the prepend.
