# refinement.md — pytest-dev__pytest-5840

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`registerModule` `do` block + the `Key`/`KeyRepr`/`regLookup` deep model) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A-consumed** (proof uses an axiom's `ensures`), **A-reference** (a deep model
validated == the real callee/object by G-AX), or **I** (identical concrete op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`);
the A legs + this narrative are audited by **G-EQ**. Claim: any impl verifying
against this frozen spec, refined per the map below, is behaviourally equal to
the gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The cache-key site — `_importconftest()` (`src/_pytest/config/__init__.py:431`)

Gold hunk (the load-bearing change, F2P-decisive):
```
-        conftestpath = unique_path(conftestpath)        # key = py.path.local(normcase(realpath))
-        try:
-            return self._conftestpath2mod[conftestpath]
+        key = Path(str(conftestpath)).resolve()         # key = pathlib.Path, case-preserving
+        try:
+            return self._conftestpath2mod[key]
 ...
-            self._conftestpath2mod[conftestpath] = mod
+            self._conftestpath2mod[key] = mod
```

| # | Solution.lean impl op (`registerModule`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | param `registry : List (Key × Module)` | `self._conftestpath2mod : dict` | R | dict ↔ assoc list (mapping.md §2). G-CONF bridges. |
| A2 | param `loc : Nat`, `freshMod : Module` | the location of `conftestpath`; `conftestpath.pyimport()` result | R | location identity ↔ `Nat`; the import callee's module ↔ free input (mapping.md §2; this op is unchanged — §C). |
| A3 | `let k := probeKey loc` (`= ⟨loc, primary⟩`) | `key = Path(str(conftestpath)).resolve()` | A-reference + I | the changed key-construction is modeled **deeply** by `probeKey`/`KeyRepr.primary`; the equality "this is a key object distinct from the `unique_path` one yet denoting the same location" is the **A-reference** G-AX validates against the real objects (mapping.md §3.1). The `let`/lookup ops themselves are **I**. |
| A4 | `let cached := regLookup registry k` ; `if cached.isSome then return cached.getD _` | `try: return self._conftestpath2mod[key] except KeyError:` | I | dict-membership + read ↔ `regLookup … ≠ none` + value read (mapping.md §2). Cache-hit returns the stored module, cache unchanged. |
| A5 | `else registry := registry ++ [(k, freshMod)]; return freshMod` | `self._conftestpath2mod[key] = mod; ... return mod` | I + R | miss-branch inserts under the SAME `primary` key `k` and returns the fresh module. Insertion ↔ `++ [(k, freshMod)]` (R, mapping.md §2). |

Discriminating content of the change — entries are keyed under the **same
representation consumers probe with** (`primary`), not a same-location
alternative (`secondary`) — lives in `k = probeKey loc` (A3) and the post-state
clause `ensures regLookup registry (probeKey loc) = some out`. The pre-patch
keyed under `unique_path` (`secondary`); `Solution_prepatch.lean` reproduces that
(`k = ⟨loc, secondary⟩`) and **fails** that post-state clause (G-DIFF), exactly
as the real pre-patch failed the F2P lookup `key in conftest._conftestpath2mod`.

## B. The other gold sites (test-neutral for the F2P set)

The gold patch also (i) drops `unique_path` from `_set_initial_conftests`
(`:369`) and adds `.realpath()` in `_getconftestmodules` (`:408,411`), and (ii)
deletes the now-dead `unique_path` helper + `normcase` import from `pathlib.py`.

Measured (mapping.md §3.2 / report): applying **only** the `_importconftest`
site (A) already turns both F2P parametrizations green and leaves PASS_TO_PASS
green. Sites (i)/(ii) are refactors that remove the now-unused
case-folding key path; they introduce no behaviour the F2P/P2P tests observe.
They carry no Lean construct and no axiom — pure deletions / a `realpath`
normalization on the dirpath traversal that does not change which conftests are
found on the case-sensitive eval FS. No separate failing prepatch is needed for
them: the single observable fixed behaviour is the key-representation match at
site A, which `Solution_prepatch.lean` already discriminates.

## C. `freshMod` / the import callee — free input (R, no axiom)

`conftestpath.pyimport()` (the module actually loaded on a miss) is an UNCHANGED
callee. The patch never inspects its value — it changes only the KEY under which
that value is stored. So it is modeled as the free input `freshMod`, about which
the spec makes **no** behavioural claim (every postcondition holds for all
`freshMod`). This is an **R** refinement (a value abstraction), NOT a consumed
axiom and NOT a deep-model reference: there is no `ensures` about `freshMod`'s
content, hence nothing for G-AX to check about it. Listing it as an axiom would
be a dead-axiom over-claim (SPEC_GUIDE §0.7).

## D. No kind-3 (inexpressible-changed-op) steps

Every step is R, A-reference, or I. The one operation that genuinely *changed* —
which key object the cache is keyed under — is modeled **deeply** (`Key`/
`KeyRepr`/`probeKey`, step A3, an A-reference + I), not hidden behind an axiom
about the function under change. There are **no consumed axioms** in this bundle
(`axioms` region is empty); the only kind-A obligation is the A-reference of
§3.1, validated by G-AX.

## E. verify(Solution) ⇒ resolved

`registerModule` verifies only if (A3) the key it stores/reads under is
`probeKey loc` (the `primary` representation) and (A5) the post-state satisfies
`regLookup registry (probeKey loc) = some out` in every branch — i.e. a
subsequent consumer probe finds the returned module. By R (`dict ↔ assoc list`,
`location ↔ Nat`, `module ↔ Nat`, `freshMod` free) the verified routine equals
the patched `_importconftest` on the cache state the F2P test inspects; by G-AX
the deep model's distinct-dict-key fact matches the real `Path.resolve()` vs
`unique_path` objects (A-reference); by G-CONF the R/I transliteration agrees
with `patch.diff`'s cache behaviour on ≥10⁵ fuzzed import sequences. Therefore a
model satisfying this spec, refined by the map above, is the gold patch up to
type refinement and the single audited A-reference — and the gold patch resolves
(G-RESOLVE). Trust points are exactly the two of plan §1.1: A-reference soundness
(G-AX) and refinement fidelity (this doc, G-EQ + G-CONF).
