# refinement.md — django__django-14765

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`normalizeSetArg` `do` block, plus the deep `normalizeSpec` model) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A** (axiomatized callee — none here), or **I** (identical concrete op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the narrative is audited by **G-EQ**. Claim: any impl verifying against
this frozen spec, refined per the map below, is behaviourally equal to the gold
patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The normalization site — `ProjectState.__init__` (`state.py:94-97`)

Gold hunk:
```
- if real_apps:
-     self.real_apps = real_apps if isinstance(real_apps, set) else set(real_apps)
- else:
-     self.real_apps = set()
+ if real_apps is None:
+     real_apps = set()
+ else:
+     assert isinstance(real_apps, set)
+ self.real_apps = real_apps
```

| # | Solution.lean impl op (`normalizeSetArg`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `arg : SetArg` | the `real_apps` parameter + the two tests `real_apps is None`, `isinstance(real_apps, set)` | R | the argument's shape ↔ `SetArg` (mapping.md §2). The tests are UNCHANGED primitives, abstracted as the free input (directive 7); G-CONF runs them LIVE in its `classify`. |
| A2 | `.absent => Except.ok []` | `if real_apps is None: real_apps = set()` then `self.real_apps = real_apps` | R + I | absent argument stored as the empty collection. `set()` ↔ `[]` (mapping.md §2). The dispatch on the absent case is concrete/transliterated (I). |
| A3 | `.alreadySet xs => Except.ok xs` | `else: assert isinstance(real_apps, set)` (passes) then `self.real_apps = real_apps` | R + I | an argument that is already a set is stored AS-IS; the assert succeeds and the value is kept unchanged. `set` members ↔ `xs` as a Python set (mapping.md §2). |
| A4 | `.coercible _ => Except.error .rejected` | `else: assert isinstance(real_apps, set)` (fails → `AssertionError`) | R + I | an argument that is not a set is REJECTED; the assert fails and raises. `AssertionError` ↔ `Except.error .rejected` (mapping.md §2). This is the discriminating behaviour. |

Discriminating content of the change — a non-set `real_apps` is now REFUSED
(`assert` → raise) instead of silently coerced with `set(real_apps)` — lives in
`normalizeSpec (.coercible _) = Except.error .rejected` (model) ⇔ the
`assert isinstance(real_apps, set)` step (real). The pre-patch wrapped it with
`set(real_apps)` and stored the result; `Solution_prepatch.lean` reproduces that
(`.coercible ys => Except.ok ys`) and **fails** `out = normalizeSpec arg` on the
`coercible` branch (G-DIFF). The F2P test `test_real_apps_non_set`
(`ProjectState(real_apps=['contenttypes'])` must raise `AssertionError`) is
exactly the `coercible` case.

## B. The empty-set/falsy guard refinement (no separate prepatch)

The pre-patch guard `if real_apps:` (truthiness) and the post-patch guard
`if real_apps is None:` differ only for a genuine empty `set()`: pre-patch it
fell to the `else` and was replaced by a fresh `set()`; post-patch it is kept.
Both are observationally `set()` (mapping.md §2 note), so no observer of
`self.real_apps` can distinguish them and the F2P/P2P matrix never does. The
model collapses both to an empty stored collection (`absent`→`[]`,
`alreadySet []`→`[]`), agreeing with the gold patch. G-CONF fuzzes `set()`, `[]`,
and the omitted argument and finds zero disagreements, confirming the collapse is
sound. No separate failing prepatch is owed (a prepatch must keep the spec
byte-identical, G-DIFF; site A's prepatch already exercises the one
observable change).

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R or I. The one operation that genuinely *changed* — refusing a
non-set argument rather than coercing it — is modeled **deeply** (`normalizeSpec`
in the `pure` region, the `Except.error .rejected` branch), not hidden behind an
axiom about the function under change. There are no consumed axioms and no
deep-model references to library callees: the only sub-steps not pinned are the
two UNCHANGED primitive tests, modeled as the free input `SetArg` (directive 7).

## D. verify(Solution) ⇒ resolved

`normalizeSetArg` verifies only if its output equals `normalizeSpec arg`
exactly: empty on `absent`, the set as-is on `alreadySet`, and an error
(`rejected`) on `coercible` (A2/A3/A4). By R (`SetArg ↔ argument shape`,
`set ↔ List String` under set-equality, `AssertionError ↔ Except.error`) the
verified normalizer equals the gold patch's `__init__` body on every argument:
None/omitted → empty `self.real_apps`; a set → that set; a non-set →
`AssertionError`. By G-CONF the R/I transliteration agrees with `patch.diff`'s
behaviour through the real `ProjectState.__init__` on ≥10⁵ inputs (and
disagrees on the pre-patch source, confirming discrimination). Therefore a model
satisfying this spec, refined by the map above, is the gold patch up to type
refinement — and the gold patch resolves (G-RESOLVE). The sole trust point is
refinement fidelity (this doc, G-EQ + G-CONF); there is no axiom-soundness trust
point (no axioms).
