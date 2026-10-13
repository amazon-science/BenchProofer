# mapping.md — scikit-learn__scikit-learn-14983

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 06632c0d185128a53c57ccc73b25b6408e90bb89`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and
gives the provenance of each modeled callee.

Repo file under change: `sklearn/model_selection/_split.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `buildReprValues (keys, attrs, fallback, hasFallback)` | the value-collection loop of `_build_repr(self)` — `sklearn/model_selection/_split.py:2138` (loop body lines 2152-2167) | the modeled changed function: how the displayed value of each sorted parameter name is obtained |
| `resolveOne (attrs fallback hasFallback key)` | the per-key value lookup inside `_build_repr`'s loop (`value = getattr(self, key, None)`, post-patch with the `cvargs` fallback) — `_split.py:2159-2162` | pure spec: resolve the value shown for one parameter name |
| `resolveAll (attrs fallback hasFallback keys)` | the full sweep over `args` (the sorted constructor parameter names) populating `params[key] = value` — `_split.py:2152-2167` | pure spec: resolve, in order, the value shown for every parameter name |

The constructor-introspection prelude of `_build_repr` (`signature(init)`,
`sorted([... p.name ...])`) produces the `keys` list; it is **unchanged** by the
patch and is supplied to the model as the input carrier `keys` (see §2). The
`__repr__` method newly added to the repeated-splits base class
(`_split.py:105-106` region of the patch) is a one-line delegation to
`_build_repr`; it introduces no new computation beyond invoking the modeled
function, so it is covered by the model of `_build_repr` (refinement.md §B).

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) and G-AX use to translate values between the
Lean value domain and the Python repo types. A wrong entry surfaces as spurious
G-CONF disagreements.

| repo reality | Lean carrier | bijection |
|---|---|---|
| `args` — the sorted list of constructor parameter names | `keys : List String` | Python list of `str` ↔ `List String`, order-preserving, element-wise string identity |
| `self.__dict__` restricted to the parameter names (what `getattr(self, key, None)` reads) | `attrs : List (String × Int)` | an association list: `key` present with value `v` ↔ `(key, v) ∈ attrs` (first match); `getattr(self, key, None) is None` ↔ `attrs.lookup key = none`. Parameter values are integers in the tested configuration (`n_splits`, `n_repeats`, `random_state`); modeled as `Int`, with `random_state=None` modeled as that key being **absent** from `attrs` (its display value is `none`). |
| `self.cvargs` — the secondary keyword-parameter store (`dict`) | `fallback : List (String × Int)` | same association-list bijection as `attrs`; `self.cvargs.get(key, None)` ↔ `fallback.lookup key` |
| `hasattr(self, 'cvargs')` | `hasFallback : Bool` | `true` ↔ the object exposes the secondary store; `false` ↔ it does not (then no fallback is consulted) |
| `value` shown for one key (`Optional[int]`) | `Option Int` | `None` ↔ `none`; integer `v` ↔ `some v` |
| `params` (the ordered key→value dict that feeds `_pprint`) | `out : List (Option Int)` | order-preserving; the i-th resolved value corresponds to `keys[i]` |

The model abstracts the value type to `Int`/`Option Int` because the F2P test
(`test_repeated_cv_repr`) exercises exactly the integer/None-valued parameters
`n_splits`, `n_repeats`, `random_state`. The fix is purely about **where** each
value is sourced (own attribute table vs. the secondary store), not about value
rendering; `Int` is a faithful, sufficient carrier for that behavior. The
`_pprint`/`'%s(%s)'` rendering that turns `params` into the final string is
**unchanged** by the patch and is identity-on-content w.r.t. the resolved value
map; it is out of scope of the modeled change (refinement.md §A4).

## 3. Callee provenance

There are **no consumed axioms** and **no deeply-modeled unchanged callees** in
this bundle. The changed behavior — value resolution with a secondary-store
fallback — is modeled **deeply and directly** by `resolveOne`/`resolveAll` in
the `pure` region; the verified `while` loop IS that resolution. The `axioms`
region is therefore empty.

The two primitive lookups (`getattr(self, key, None)` and
`self.cvargs.get(key, None)`) are total dictionary reads with no side effects;
they are modeled as `List.lookup` and need no axiom. `axiom_check.py` (G-AX)
nonetheless executes the **real** patched `_build_repr` value-resolution
(`getattr` + `cvargs.get` exactly as the patch composes them) against the
`resolveOne`/`resolveAll` deep model over boundary + fuzzed object states, to
confirm the deep model equals the real callee behavior (an A-reference-style
soundness check, even though no axiom is consumed). Exit 0 iff sound.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`14983`** so the
consumer-side verdict is reproducible. The R/I shadow it builds transliterates
`resolveOne`/`resolveAll` to Python and diffs against the **real** patched
`_build_repr` value map (the correctness oracle) over ≥10⁵ fuzzed object states
spanning: keys present only in `attrs`, only in `fallback`, in both, in neither;
`hasFallback ∈ {true,false}`; and `None`-valued / absent attributes.
