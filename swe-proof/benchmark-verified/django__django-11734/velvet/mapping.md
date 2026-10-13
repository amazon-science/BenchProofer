# mapping.md — django__django-11734

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 999891bd80b3d02dd916731a7a239e1036174885` (django/django, v3.0),
states the type abstraction (the bijection G-CONF and G-AX use to bridge
Lean↔Python), and gives the provenance of each modeled operation.

Repo files under change: `django/db/models/fields/related_lookups.py`,
`django/db/models/sql/query.py`, `django/db/models/fields/__init__.py`.

## 0. Scope of the modeled behavior

The desired behavior (problem_statement) is: a reference to the outer query,
used as a comparison target inside `exclude()` / `~Q()`, must continue to refer
to the *outer* query rather than being mis-resolved against the query under
construction (which raises `ValueError: This queryset contains a reference to an
outer query and may only be used in a subquery`).

The gold patch touches three call sites; the official `FAIL_TO_PASS` test
(`queries.tests.ExcludeTests.test_subquery_exclude_outerref`) is sensitive to
exactly two of them (verified empirically by running the F2P test against each
hunk subset in the instance image):

| repo hunk | needed for F2P? | modeled as |
|---|---|---|
| `related_lookups.py` `RelatedLookupMixin.get_prep_lookup` guard | **yes** | `comparisonNormalizesAsValue` (site 1) |
| `query.py` `split_exclude` outer-ref rebind | **yes** | `subqueryTargetResolution` (site 2) |
| `fields/__init__.py` `AutoField.get_prep_value` removal | no (redundant cleanup) | not modeled (see §5) |

Both modeled sites are *independently necessary* for the F2P test: dropping
either one re-introduces the failure (`AssertionError`/`ValueError`). Hence one
failing prepatch per site (`Solution_prepatch.lean` breaks site 1,
`Solution_prepatch_2.lean` breaks site 2; G-DIFF).

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `comparisonNormalizesAsValue (lhsSpansMultipleColumns) (t)` | `RelatedLookupMixin.get_prep_lookup` guard — `django/db/models/fields/related_lookups.py:104` | site-1 changed function: whether the rhs comparison target is treated as a direct value to normalize |
| `subqueryTargetResolution (t)` | `Query.split_exclude` rhs rebind — `django/db/models/sql/query.py:1705-1707` post-patch | site-2 changed function: how the rhs is rebound and then resolves inside the rebuilt subquery |
| `Target` (`outerRef`/`localRef`/`directValue`) | the runtime kind of `self.rhs` / `filter_rhs`: `OuterRef`, `F`, or a plain value | the comparison-target carrier (R) |
| `isExpression t` | `hasattr(rhs, 'resolve_expression')` — `related_lookups.py:104` post-patch (the changed predicate, replacing `rhs_is_direct_value()` = `not hasattr(rhs,'as_sql')`) | whether the target is a query expression (I — identical to the post-patch guard) |
| `normalizesAsValue lhsSpan t` | `not isinstance(self.lhs, MultiColSource) and not hasattr(self.rhs, 'resolve_expression')` — `related_lookups.py:104` | per-call "treat rhs as a direct value" predicate (I) |
| `rebind t` | the post-patch rhs rebind in `split_exclude` (`query.py:1705-1707`) | how the rhs is rebound for the nested subquery (I — identical to the post-patch dispatch) |
| `resolveInSubquery b` *(deep model — A-reference)* | `F.resolve_expression` / `OuterRef.resolve_expression` / `ResolvedOuterRef` — `django/db/models/expressions.py:529,565,546` | the UNCHANGED resolution semantics of the rebound target; deep model validated `== the real callee` by axiom_check.py (G-AX) |

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) and G-AX use to translate values between the
Lean value domain and the Python repo types. A wrong entry surfaces as spurious
G-CONF disagreements (the falsifiability the plan §4 trust statement refers to).

| repo reality | Lean carrier | bijection |
|---|---|---|
| `self.rhs` / `filter_rhs` runtime kind | `Target` | `OuterRef` instance ↔ `outerRef`; `F` instance (non-`OuterRef`) ↔ `localRef`; anything else (int, str, model instance — no `resolve_expression`) ↔ `directValue` |
| `isinstance(self.lhs, MultiColSource)` | `lhsSpansMultipleColumns : Bool` | `True` ↔ `true` (the relation spans multiple columns); `False` ↔ `false` (single-column) |
| `hasattr(rhs, 'resolve_expression')` | `isExpression t : Bool` | present ↔ `true`; absent ↔ `false`. (`OuterRef`/`F` have it; plain values don't.) |
| the rebound rhs object | `Rebound` | `OuterRef(outerRefObj)` ↔ `outerKeepingDepth`; `OuterRef(name : str)` ↔ `outerByName`; the unchanged plain value ↔ `unchanged` |
| `rebound.resolve_expression()` outcome | `Resolution` | result is an `OuterRef` (still deferred) ↔ `staysOuter`; result is a `ResolvedOuterRef` (resolved at this level) ↔ `resolvesLocally`; a plain value (no `resolve_expression`) ↔ `plainValue` |

`OuterRef.resolve_expression` (`expressions.py:566-570`): `return self.name if
isinstance(self.name, OuterRef) else ResolvedOuterRef(self.name)`. So an
`OuterRef` *wrapping another* `OuterRef` peels one layer and stays an `OuterRef`
(`staysOuter`); an `OuterRef` wrapping a *name* becomes a `ResolvedOuterRef`
(`resolvesLocally`). This is the fixed, unchanged semantics the patch relies on
— modeled deeply by `resolveInSubquery`, validated against the real callee by
G-AX.

## 3. Callee provenance

### 3.1 No consumed axioms (A-consumed)
There is **no module-level `axiom`** and **no consumed axiom**. The operations
the patch changes — the site-1 guard predicate and the site-2 rebind dispatch —
are modeled **identically** (`normalizesAsValue`/`isExpression`, `rebind`), and
are tagged **I** in refinement.md. Their cross-language soundness is checked
mechanically by G-CONF against the real patched code.

### 3.2 `resolveInSubquery` deep model ↔ `resolve_expression` (A-reference)
The single UNCHANGED downstream callee — how a rebound target resolves when
consulted from inside the subquery — is modeled deeply by `resolveInSubquery`
(`pure` region) rather than left opaque. It is an **A-reference**:
`axiom_check.py` (G-AX) constructs the real rebound objects
(`OuterRef(OuterRef(name))`, `OuterRef(name)`, a plain value), calls the REAL
`resolve_expression`, classifies the result, and asserts it equals
`resolveInSubquery` on every `Rebound` value. It is NOT a consumed axiom (the
proof does not assume its `ensures`; it is a concrete `def` whose equality to
the real callee is the validated trust point).

The `OuterRef.resolve_expression` / `OuterRef.__init__` / `ResolvedOuterRef`
behavior is unchanged by `patch.diff` (the diff touches only `split_exclude`,
`get_prep_lookup`, and `AutoField.get_prep_value`); G-AX uses the real classes.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`11734`** so the
consumer-side verdict (§11.3) is reproducible. The R/I shadow it builds
transliterates `normalizesAsValue`/`isExpression` (site 1, I) and `rebind`
(site 2, I) to Python and compares against the real patched guard / the real
rebind-then-`resolve_expression` over fuzzed `(lhsSpansMultipleColumns, Target)`
inputs built from REAL django `OuterRef`/`F`/plain-value objects. The
A-reference `resolveInSubquery` is left as the real `resolve_expression` callee
in the shadow (A-tagged → run real callee), isolating the R/I legs.

## 5. The third gold hunk (not modeled — refinement audit only)

`AutoField.get_prep_value` (`fields/__init__.py:2335-2337`) is *removed* by the
gold patch. At base_commit it reads
`return value if isinstance(value, OuterRef) else super().get_prep_value(value)`.
Empirically (F2P run against the `related_lookups.py` + `query.py` hunks alone)
this removal is **not** required for the F2P test: once site 1 stops coercing an
`OuterRef` into a value (so `get_prep_value` is never reached with an `OuterRef`),
this guard becomes dead code that the gold patch tidies up. It changes no
behavior the F2P/P2P suite observes, so it is carried in `patch.diff` (gold
verbatim, for G-RESOLVE / PASS_TO_PASS) but is not a modeled site and has no
spec clause. It is neither an axiom nor a refinement leg.
