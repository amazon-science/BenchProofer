# refinement.md — sympy__sympy-12481

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`buildExplicitForm` `do` block + the deep `arrayForm` model) and `patch.diff` (the
gold patch). Each step is tagged **R** (type refinement), **A-consumed** (proof
uses an axiom's `ensures`), **A-reference** (deep model validated == real callee
by G-AX), or **I** (identical concrete op). EVERY step is R, A, or I.

The R/I legs are mechanically refuted by **G-CONF**; the A legs + this narrative
are audited by **G-EQ**. `patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The changed screen — `Permutation.__new__`, both readings

Gold hunk (`sympy/combinatorics/permutations.py:897–904` @ base_commit):
```
         temp = flatten(args)
-        if has_dups(temp):
-            if is_cycle:
-                raise ValueError('there were repeated elements; to resolve '
-                'cycles use Cycle%s.' % ''.join([str(tuple(c)) for c in args]))
-            else:
-                raise ValueError('there were repeated elements.')
+        if has_dups(temp) and not is_cycle:
+            raise ValueError('there were repeated elements.')
         temp = set(temp)
```
Downstream, unchanged: the coverage screen `if not is_cycle and any(i not in temp
for i in range(len(temp))): raise ValueError("Integers 0 through %s must be
present." % max(temp))` (`:906–909`), then the two answers — `c = Cycle(); for ci
in args: c = c(*ci); aform = c.list()` (`:911–917`) on the grouped reading and
`aform = list(args)` (`:919`) on the flat one.

| # | Solution.lean impl op (`buildExplicitForm`) | patch.diff / repo op | tag | justification |
|---|---|---|---|---|
| A1 | param `entries : List (List Nat)` | `args` after `args = list(args[0])` (`:884`) and the per-reading coercion (`:887–888` grouped, `:889–890` flat) | R | list-of-lists of `int ≥ 0` ↔ `List (List Nat)` on the grouped reading; on the flat reading the real argument is `entries.flatten` and every encoding in that fiber behaves identically (mapping.md §2). G-CONF bridges both. |
| A2 | param `grouped : Bool`, FREE (no `require` on it) | `is_cycle = args and is_sequence(args[0])` (`:886`) | R | flag bijection (mapping.md §2). `is_cycle` is COMPUTED from the argument shape, so both values are reachable and the model assumes neither. |
| A3 | `require grouped = true → eachValid entries` | the invariant holding before `:897` on the grouped reading: no group repeats a point internally (else `Cycle.__init__` raises, `:451`) and some point is named (else `Cycle.list` raises, `:371`) | R | frames ONLY the grouped reading, against callees the patch does not touch. The flat reading carries no frame, so every flat argument is specified. |
| A4 | `let temp := entries.flatten` | `temp = flatten(args)` (`:897`) | I | `flatten` of a list of lists is concatenation; `List.flatten` is the same op. Unchanged callee, transliterated. |
| A5 | `if !pointsDistinct temp && !grouped then return Except.error ()` | `if has_dups(temp) and not is_cycle: raise ValueError(...)` (post-patch `:898–899`) | I | THE changed screen, expressed concretely. `has_dups` ↔ `!pointsDistinct` (mapping.md §1); `raise ValueError` ↔ `Except.error ()` (R). This is the operation whose logic the patch rewrites; it is fully expressible, so modeled directly (no axiom). The `&& !grouped` conjunct is the patch's added `and not is_cycle`. |
| A6 | `if !grouped && !rangeCovered temp then return Except.error ()` | `if not is_cycle and any(i not in temp for i in range(len(temp))): raise ValueError("Integers 0 through %s must be present.")` over `temp = set(temp)` (`:904`, `:906–909`) | I | the UNCHANGED coverage screen, transliterated. `rangeCovered` uses `l.dedup.length` for `len(set(temp))` and `l.contains i` for `i in temp`, so the two agree pointwise; the `!grouped` conjunct is the repo's own `not is_cycle`. Carried into the model because the patch's delta is about WHICH reading a refusal belongs to, and a model that dropped this screen would admit an impl that accepts `[4, 5]` — an input the official test requires be refused. |
| A7 | `if grouped then return Except.ok (arrayForm entries)` | fall-through to `c = Cycle(); for ci in args: c = c(*ci); aform = c.list()` (`:911–917`) and the store/return at `:925–929` | A-reference + I | the composition is UNCHANGED by the patch and modeled **deeply** by `arrayForm` (`composePoint`/`cycleStep`); its equality to the real composition block is the A-reference G-AX validates. The branch and return control flow is I. |
| A8 | `else return Except.ok temp` | `aform = list(args)` (`:919`) and the store/return at `:925–929` | I | on the flat reading the answer is a copy of the already-flat argument. `temp` is `entries.flatten`, the same list, so this is the identity op — no callee, nothing to axiomatize (mapping.md §4.2). |

Discriminating content of the change — a point repeated across different groups
must, on the GROUPED reading, yield the composed array form rather than a
`ValueError`, while on the FLAT reading a repeat must still be refused. Both
directions are pinned:

* post-patch, `grouped = true` makes `!grouped` false, so A5 cannot fire and the
  result is `Except.ok (arrayForm entries)`. The pre-patch screen `if has_dups
  temp` fires on exactly those shared-point inputs and returns `.error`, so
  `Solution_prepatch.lean` FAILS with `case «ensures_3: grouped = true → result =
  Except.ok (arrayForm entries)»` (G-DIFF). The added assertion
  `Permutation([[0, 1], [0, 2]]) == Permutation(0, 1, 2)` is the canonical witness
  (`arrayForm [[0,1],[0,2]] = [1,2,0]`).
* post-patch, `grouped = false` leaves A5 and A6 live, so a repeated point or a
  gap below the count of distinct points is refused — which is what the RETAINED
  assertions `raises(ValueError, lambda: Permutation([1, 1, 0]))` and
  `raises(ValueError, lambda: Permutation([4, 5], size=10))` observe. An impl that
  keeps only the first bullet verifies against a spec that fences this reading
  off, and its refined patch fails the official F2P test; properties.py ships six
  such impls as reject cases with that failure MEASURED.

## B. No consumed axioms

There are **no** `axiom`s the proof consumes. The only kind-A construct is the
**A-reference** `arrayForm` (A7), a deep model of the unchanged composition
routine validated `== real` by G-AX. There is no dead axiom and no axiom about the
function under change.

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R, A-reference, or I. The one operation that genuinely *changed* —
the repeated-point screen — is modeled **directly and concretely** (A5, an I op),
not hidden behind an axiom. The unchanged coverage screen (A6) and the flat
answer (A8) are likewise concrete; the unchanged composition is the deep
A-reference (A7).

## D. verify(Solution) ⇒ resolved

`buildExplicitForm` verifies only if, for a free `grouped`:

* on the grouped reading (framed by `eachValid`) the result is the SUCCESS
  constructor carrying the left-to-right composite (A5's screen never fires, A7's
  value is exact); and
* on the flat reading the result is the argument itself exactly when the argument
  already is an explicit list form, and a refusal otherwise (A5 + A6 + A8).

By R (`List (List Nat) ↔ args` on both readings, `Bool ↔ is_cycle`,
`ValueError ↔ .error`, array form ↔ `_array_form`) the verified method equals the
post-patch body over its declared frame (mapping.md §3 — `size=` excepted, and
refused before `size` is consulted on the one assertion that passes it); by G-AX
the deep model `arrayForm` equals the real composition block (A-reference); by
G-CONF the R/I transliteration agrees with `patch.diff`'s behavior on 10⁵ inputs
spanning both readings. Therefore a model satisfying this spec, refined per the
map above, is the gold patch up to type refinement and the audited callee — and
the gold patch resolves (G-RESOLVE: F2P `test_args` passes, 7/7 P2P pass,
measured). Trust points: the single A-reference's soundness (G-AX) and refinement
fidelity (this doc, G-EQ + G-CONF).
