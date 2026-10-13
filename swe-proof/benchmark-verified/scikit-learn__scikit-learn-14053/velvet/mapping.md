# mapping.md — scikit-learn__scikit-learn-14053

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 6ab8c86c383dd847a1be7103ad115f174fe23ffd`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and gives the
provenance of each callee.

Repo file under change: `sklearn/tree/export.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `buildLabels (names) (sentinel) (refs)` | the `feature_names_` list comprehension inside `export_text` — `sklearn/tree/export.py:893` (the `if feature_names:` branch) | the modeled changed code: build the per-node label list from the table of user-supplied names and the per-node reference list |
| `names : List Name` | `feature_names` — the user-supplied list of feature names (`export_text` argument), `sklearn/tree/export.py:806` | the name table |
| `refs : List Int` | `tree_.feature` — the per-node split-feature index array (`Tree.feature`, `sklearn/tree/_tree.pyx`), iterated at `export.py:893` | the per-node integer references |
| `sentinel : Int` | `_tree.TREE_UNDEFINED` — module constant `= -2`, `sklearn/tree/_tree.pyx:64` | the distinguished value marking a node that splits on no feature (a leaf) |
| `labelOne` / `labelsOf` | the (post-fix) per-element resolution of the comprehension | pure spec: resolve one reference / the whole list |

The result `feature_names_` is consumed downstream only at `export.py:931`
(`name = feature_names_[node]`), which is reached **only** inside the
`if tree_.feature[node] != _tree.TREE_UNDEFINED:` branch (`export.py:930`) — i.e.
a sentinel slot's label is never read. So mapping a sentinel reference to "no
label" (`none`) is observationally safe; the only requirement the downstream
read imposes is that non-sentinel slots carry the correct named entry. This is
exactly what `buildLabels`'s postcondition pins.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean value
domain and the Python repo types. A wrong entry surfaces as spurious G-CONF
disagreements (the falsifiability the plan §4 trust statement refers to).

| repo reality | Lean carrier | bijection |
|---|---|---|
| `feature_names` (a `list` of `str`, length `n_features`) | `names : List Name` (`Name := Nat`) | the `str` at position `k` ↔ the natural number `k` (its index identity). The comprehension's *result content* observed downstream (`feature_names_[node]`) is exactly "the `feature_names` entry at this slot"; the spelling is irrelevant to the modeled control decision, so each entry is carried by its own slot index. `len(feature_names)` ↔ `names.length`. |
| `tree_.feature` (a 1-D int array, one entry per node) | `refs : List Int` | `int` entry ↔ Lean `Int`; iteration order ↔ list order; `len` ↔ `.length` |
| `_tree.TREE_UNDEFINED` (`= -2`) | `sentinel : Int` (a free input, instantiated `-2`) | the constant `-2` ↔ `sentinel`. Modeled as a free parameter, not a literal, so the spec names no concrete sentinel magnitude (de-leak) and the proof holds for any sentinel. |
| `feature_names_` (the result list; entries are `str` or `None` post-fix) | `out : List (Option Name)` | a `str` entry at slot `k` ↔ `some k`; a `None` entry ↔ `none`. Pre-fix the result had no `None` entries (and could raise — see below). |
| `feature_names[i]` indexing (Python) | `names[i.toNat]?` | for a non-sentinel `i`, the precondition forces `0 ≤ i < len`, so Python `feature_names[i]` ↔ `names[i.toNat]? = some i`. The sentinel branch never indexes. |

### 2.1 The bug being fixed (refinement audit; not in the consumer spec view)
Pre-fix the comprehension was `[feature_names[i] for i in tree_.feature]`: it
indexed `feature_names` for **every** node, including leaf nodes whose reference
is `-2`. Python's `feature_names[-2]` is negative indexing: it raises
`IndexError` when `len(feature_names) < 2` (the single-feature case in the issue
and the F2P test), and silently returns the wrong (second-from-last) name when
`len ≥ 2`. The fix guards the sentinel:
`[feature_names[i] if i != _tree.TREE_UNDEFINED else None for i in tree_.feature]`.
Both failure modes (the raise and the silent-wrong-name) are eliminated because
a sentinel reference now yields `None` directly. The `buildLabels` precondition
(`require ∀ i ∈ refs, i ≠ sentinel → 0 ≤ i ∧ i.toNat < names.length`) captures
that real, non-sentinel references ARE valid indices (an invariant of a fitted
tree's `feature` array against a correctly-sized `feature_names`), while placing
NO index obligation on the sentinel — which is precisely why the fixed code must
not index it.

## 3. Callee provenance (kind-A) — none

This bundle declares **no axioms and no deep-model references**. The modeled
change is a self-contained list comprehension whose every operation is concrete
list arithmetic over its two inputs:
- per-reference resolution (`labelOne`): an equality test against `sentinel`
  and, in the non-sentinel case, a total list index (`names[·]?`);
- assembly of the result list (`labelsOf` / the backward `while` fold): `::`.

There is no unchanged repo callee inside the comprehension whose contract must
be assumed. (`feature_names[i]` is the language's list indexing, not a repo
function; `_tree.TREE_UNDEFINED` is a module constant, carried as the free
`sentinel`.) Hence **G-AX has nothing to falsify**: the bundle ships **no**
`axiom_check.py`, so G-AX correctly returns `skip` ("no axioms in bundle") — the
canonical verdict for a zero-axiom bundle. (G-AX runs against the *unpatched*
container, so any end-to-end witness against the changed `export_text` would
necessarily hit the very `IndexError` the patch fixes; the differential burden
belongs to G-CONF, which applies the gold patch.) All refinement.md rows are R
or I; `conf_skip = false` (the impl region carries no A-tagged op, so G-CONF
carries full weight, validating the deep model against the real patched
comprehension on ≥10⁵ inputs).

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`14053`** so the
consumer-side verdict (§11.3) is reproducible. The R/I shadow it builds
transliterates `labelOne`/`labelsOf` (R/I-tagged ops) to Python and compares
against the patched comprehension's behaviour (the real correctness oracle),
including the single-feature / leaf-node boundary the issue reports.
