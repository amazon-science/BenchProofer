# mapping.md — scikit-learn__scikit-learn-14496

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = d49a6f13af2f22228d430ac64ac2b518937800d0`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and
gives the provenance of each modeled callee.

Repo file under change: `sklearn/cluster/optics_.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `conditionSizeParameter (value, scaled, population)` | `compute_optics_graph(X, min_samples, …)` — `sklearn/cluster/optics_.py:331`; conditioning block body `optics_.py:439-440` | modeled changed function #1 (single sizing parameter conditioned to an absolute count) |
| `resolvePairedSizes (value, secondaryValue, scaledPrimary, scaledSecondary, secondaryGiven, population)` | `cluster_optics_xi(reachability, …, min_samples, min_cluster_size, …)` — `sklearn/cluster/optics_.py:569`; conditioning block body `optics_.py:619-627` | modeled changed function #2 (two sizing parameters conditioned; second defaults to first when absent) |
| `asAbsoluteCount (value, scaled)` *(pure spec, deep model)* | the conditioning expression `max(2, int(value * n_samples))` (post-patch `optics_.py:440, 622, 627`), with `scaled` standing for the sub-expression `value * n_samples` as the machine actually computes it | pure spec: reduce the ALREADY-SCALED value to a whole count and clamp ≥ 2 |
| `scaledFromPopulation (scaled, value, population)` *(pure spec)* | the admissible results of the IEEE double multiplication `min_samples * n_samples` (`optics_.py:440, 622, 627`) | precondition: `scaled` agrees with the ideal product to within one part in 2^53, the guarantee IEEE double multiplication honors |
| `value ≤ 1` guard | `if min_samples <= 1:` (`optics_.py:439, 621, 626`) | the branch selecting fraction-mode vs absolute-mode |
| `population` | `n_samples = X.shape[0]` (`optics_.py:437`) / `n_samples = len(reachability)` (`optics_.py:619`) | size of the sample population |

The `_validate_size(size, n_samples, param_name)` callee (`optics_.py:280`) runs
**before** the conditioning at each site and is **unchanged** by the fix. It
raises unless `0 < size` and, for non-integral `size`, `size ≤ 1`, and unless
`size ≤ n_samples`. The fix does not touch it; its guarantee on the surviving
(non-raising) path — `0 < value` and `1 ≤ population` — is encoded as the
`require` preconditions, not as an axiom (no dead axiom; SPEC_GUIDE §0
directive 7). `_xi_cluster`'s docstring-only hunk (`optics_.py:735`) changes no
code and is not modeled.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) and G-AX use to translate values. A wrong entry
surfaces as spurious G-CONF disagreements.

| repo reality | Lean carrier | bijection |
|---|---|---|
| `min_samples` / `min_cluster_size` argument (`int > 1` **or** `float ∈ (0,1]`) | `Rat` (`value`, `secondaryValue`) | a Python numeric `v` ↔ the rational `Fraction(v)`; comparisons (`<= 1`), multiplication (`* n_samples`) and `max` are order/ring operations preserved exactly by `Rat` |
| `n_samples` (a non-negative `int`, ≥ 1 on the surviving path) | `Nat` (`population`) | `n` ↔ `(n : Nat)`; `int(v) ↔ Rat.floor`, `len`/`.shape[0]` ↔ the `Nat` |
| the machine product `value * n_samples` (IEEE double) | `scaled : Rat`, constrained by `scaledFromPopulation` | **NOT** an exact rational function of the inputs. The multiplication rounds, and the rounding can move the product across an integer boundary in either direction, so no exact-rational surrogate is faithful (§2.1). It is modeled as an INPUT satisfying a relative-precision band of `2^-53` around the ideal product — the guarantee IEEE multiplication does honor. |
| `int(<the machine product>)` (truncation toward zero) | `Rat.floor scaled` | for a **non-negative** value, Python `int(x)` truncates toward zero, which equals `math.floor(x) = Rat.floor`. Exact once the scaled value is in hand (0 counterexamples over 500k non-negative doubles; see §3.1). |
| `max(2, …)` | `max 2 (… : Int)` then re-injected to `Rat` | `max` on the ordered integers; the result is an `Int` cast back into the `Rat` carrier so both branches of `asAbsoluteCount` share one type |
| `min_cluster_size is None` (the default sentinel) | `secondaryGiven : Bool` (`False` ⇔ `None`) | `cluster_optics_xi` sets `min_cluster_size = min_samples` when the argument is `None`; modeled by `secondaryGiven = false ⇒ secondary defaults to the conditioned primary` |

### 2.1 Why `Rat`, and why the scaled value is an INPUT

CLAUDE.md gotcha: *model order-only fixes with `Rat`, not `Float`/`Real`.* The
op the patch CHANGES is order/integer — reduce a value to a whole count and clamp
it at two — and `Rat` models that exactly. The defect is a *type* defect: a
non-integral residue is passed downstream where a whole count is required.

But the expression contains a second op the patch does NOT change: the scaling
`min_samples * n_samples`, performed in IEEE double. An earlier revision of this
bundle recomputed that product in exact rationals, and it was **unfaithful** —
the faithfulness panel's witness proves it:

```
value=0.7, n_samples=90   (ordinary in-domain input; _validate_size passes)
  real repo:  0.7*90 == 62.99999999999999 -> int(...) == 62  -> 62
  old model:  Fraction('0.7')*90 == 63 exactly -> floor == 63 -> 63
```

The rounding is in the PRODUCT, before the truncation, and it can push the
product across an integer boundary in **either** direction, so no exact-rational
surrogate for it is faithful:

```
value=0.7,  n=90    real 62,  exact-decimal model 63   (model too high)
value=0.03, n=100   real  3,  exact-double  model  2   (model too low)
```

Hence the scaled value is not recomputed: it is an **input** (`scaled`)
constrained by `scaledFromPopulation`, a `2^-53` relative band around the ideal
product. That is exactly the guarantee IEEE double multiplication honors
(0 violations over ~750k fuzzed inputs incl. subnormals, this repair), so the
contract applies to the real code; and what the postcondition pins EXACTLY is the
part that IS exact — `Rat.floor scaled`, clamped at two. This is the
"abstract the operation to a callee whose contract the real one honors" route:
the spec states what the callee guarantees, not an idealized product.

## 3. Callee / model provenance

### 3.1 `asAbsoluteCount` deep model ↔ `max(2, int(value * n_samples))`
The conditioning operation is modeled **deeply** (spelled out in the `pure`
region), so there is **no consumed axiom** for it — it is the operation under
spec, which directive 7 forbids axiomatizing. `axiom_check.py` (G-AX) validates
it against the real Python expression in two legs, over the documented fraction
domain `value ∈ (0, 1]` and a range of populations:

1. **The band is sound.** The real machine product `fl(value * n_samples)` always
   lies inside `scaledFromPopulation`'s `2^-53` relative band around the ideal
   product. Without this the contract would not apply to the real code at all.

2. **The truncation is exact.** With `scaled` set to that real machine product,

   ```
   max(2, int(value * n_samples)) == max(2, Rat.floor scaled)
   ```

   holds **exactly, with no tolerated divergences**, on every fuzzed input —
   including the faithfulness witness (`0.7 @ 90 → 62`), its whole class
   (`0.7 @ 170/180`, `0.29 @ 100`, `0.03 @ 100`, `0.6 @ 90`), and the F2P values
   (`0.1`, `0.08` @ `n=31`).

The previous revision of this check tolerated 26 "tie divergences" and rationalized
them as unreachable sub-ULP artifacts. They were reachable and in-domain: that is
precisely the defect the faithfulness panel found. There are now **zero** tolerated
divergences — the model either matches the real expression or G-AX fails.

G-AX also asserts the **pre-patch** expression (no `int()`) differs from the model
wherever the machine product is non-integral — the discriminator G-DIFF sees.

### 3.2 `_validate_size` — not modeled, captured as `require`
Unchanged callee; its non-raising guarantee (`0 < value`, and the population
bound) is the precondition domain, not an axiom. Recorded here for the
refinement audit only.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`14496`** so the
consumer-side verdict is reproducible. The R/I shadow it builds transliterates
`asAbsoluteCount` and the two `do`-block skeletons to Python over the real repo
numeric types and diffs against `patch.diff`'s behaviour (the patched
conditioning expression executed at `base_commit`). There is no A-tagged callee
inside the computed result, so the shadow is pure R/I; `conf_skip = false`.
