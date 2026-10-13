# refinement.md — sympy__sympy-24443

The operation-by-operation correspondence between `model.py`'s implementation
(the `relator_image` impl region, the deep `image_fold` model, and the opaque
`gid`/`gmul`/`gpow` axioms) and `patch.diff` (the gold patch). Each step is
tagged **R** (type refinement), **A** (axiomatized callee — split into
**A-consumed**, where the proof uses the axiom, and **A-reference**, where a
deep model is validated == the real callee by axiom_check.py / G-AX), or **I**
(identical concrete operation). The claim: *any implementation that verifies
against this frozen spec, refined per the map below, is behaviourally equal to
the gold patch on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE; F2P `test_homomorphism` and P2P
`test_isomorphisms` both pass with it applied, confirmed locally).

## A. The image computation — `_image(r)` (`sympy/combinatorics/homomorphisms.py:318-346`)

Gold hunk (the buggy two-index walk is replaced by a direct block fold):
```
-    def _image(r):
-        if r.is_identity:
-            return identity
-        else:
-            w = identity
-            r_arr = r.array_form
-            i = 0
-            j = 0
-            while i < len(r):
-                power = r_arr[j][1]
-                if isinstance(domain, PermutationGroup) and r[i] in gens:
-                    s = domain.generators[gens.index(r[i])]
-                else:
-                    s = r[i]
-                if s in images:
-                    w = w*images[s]**power
-                elif s**-1 in images:
-                    w = w*images[s**-1]**power
-                i += abs(power)
-                j += 1
-            return w
+    def _image(r):
+        w = identity
+        for symbol, power in r.array_form:
+            g = symbols_to_domain_generators[symbol]
+            w *= images[g]**power
+        return w
```
plus the hoisting before `_image`:
```
+    symbols = [g.ext_rep[0] for g in gens]
+    symbols_to_domain_generators = dict(zip(symbols, domain.generators))
```

| # | model.py impl op (`relator_image`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameters `block_pows: List[int]` (one exponent per block) | the `power` field of each `(symbol, power)` block of `r.array_form` | R | `r.array_form` is a tuple of `(symbol, power)` blocks (`free_groups.py:372`); `block_pows[k]` ↔ block `k`'s `power`. mapping.md §2. |
| A2 | parameter `block_elems: List[int]` (the resolved codomain element per block) | `images[symbols_to_domain_generators[symbol]]` for each block | R | the symbol→domain-generator→codomain-image lookup is a TOTAL unchanged map; modeling its *result* per block (an opaque element handle) is sound — the lookup chain is not what changed, only the enumeration of blocks. mapping.md §1/§2. |
| A3 | `w = gid()` | `w = identity` (`= codomain.identity`) | A-consumed | `gid` is the opaque codomain identity, the initial accumulator. |
| A4 | the loop `for k: w = gmul(w, gpow(block_elems[k], block_pows[k]))`, whose verified result is `image_fold(gid(), block_elems, block_pows)` — the ordered product of EVERY block's factor | `for symbol, power in r.array_form: w *= images[g]**power` | A-reference | the changed image operation is modeled **deeply**: `image_fold` (the spelled-out left-to-right product in the `pure` region) and the verified loop in `relator_image` ARE the per-block product. There is no consumed `_image` value-axiom — the proof never depends on one. Instead the deep model is validated **== the real `_image`** out-of-band: G-AX (axiom_check.py) runs the real sympy groups and asserts `image_fold == real _image` on all relators incl. inverted generators. The `*` / `**` are the A-consumed opaque `gmul` / `gpow`. mapping.md §3.2. |
| A5 | `gmul(a, b)` (uninterpreted, non-commutative) | group element `*` (`__mul__`) | A-consumed | the codomain product; opaque so order is observable (no commutativity assumed). mapping.md §3.1. |
| A6 | `gpow(g, e)`, total over every integer `e` incl. negative | group element `**` (`__pow__`, `free_groups.py:488` handles `n<0`) | A-consumed | the codomain integer power; defined for negative exponents (inverted generators) — exactly the totality the bug ignored. mapping.md §3.1. |
| A7 | `return w` (a codomain element handle) | `return w` | I | identical control flow / return. |

The `r.is_identity` early-return of the old code (`homomorphisms.py:319-320`)
is subsumed: when the word is empty (`len(block_pows) == 0`) the fold returns
`gid()` = `identity`, matching the deleted special case. Tag **I** (the empty
loop reproduces it).

## B. The discriminating content — inverted generators (negative exponents)

The single behavioural change the F2P test observes: a relator block whose
generator is **inverted** (negative exponent — e.g. the `x_1**-1` block of D3's
relator `x_1*x_0*x_1**-1*x_0`) must still contribute its factor `images[g]**(-1)`
in its position. The pre-patch code took the `else: s = r[i]` branch for an
inverted letter (because `r[i] in gens` is False for an inverted generator),
then matched neither `s in images` nor `s**-1 in images` (images is keyed by the
*domain generators*, not free-group letters), so that block contributed
**nothing** — silently dropping the inverse factor and yielding a non-identity
image, hence a spurious `ValueError("The given images do not define a
homomorphism")`.

`model_prepatch.py` reproduces exactly this: its loop skips the multiplication
when `block_pows[i] >= 0` is **false** (the negative-exponent block), i.e. the
inverted-generator factor is dropped. It is byte-identical in spec to `model.py`
and **fails** the loop invariant
`image_fold(w, drop(i), drop(i)) == image_fold(gid(), block_elems, block_pows)`
— the spec sensing the dropped factor (G-DIFF), because the opaque `gmul`/`gpow`
make the shortened product provably unequal to the full one.

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A, or I. The operation that genuinely *changed* — how the
relator word is enumerated into its per-block factors and producted — is modeled
**deeply** (the spelled-out left-to-right fold `image_fold` consumed in
`relator_image`, step A4, an **A-reference**), not hidden behind an axiom about
the function under change: there is no consumed `_image` value-axiom. The only
consumed axioms, `gid`/`gmul`/`gpow` (**A-consumed**), cover **unchanged**
codomain group operations the new code invokes; the changed enumeration appears
only as the **A-reference** that G-AX validates the deep model against.

## D. verify(model) ⇒ resolved

`relator_image` verifies only if its output equals the exact left-to-right
product of every block's factor `gpow(block_elems[k], block_pows[k])` — every
block, including the negative-exponent (inverted-generator) ones (A4, B). By R
(`array_form` blocks ↔ `block_pows`; resolved per-block image ↔ `block_elems`)
and A (the opaque `gmul`/`gpow` ↔ real `*`/`**`, the deep fold ↔ real `_image`
validated by G-AX), the verified image equals the gold `_image(r)` for every
relator. The gold `_check_homomorphism` accepts iff every relator's image is the
identity, so a model satisfying this spec, refined by the map above, is the gold
patch up to type refinement and audited callees — and the gold patch resolves
(G-RESOLVE). The trust points are exactly the two of PLAN §1.1: axiom soundness
(G-AX) and refinement fidelity (this document, G-EQ).
