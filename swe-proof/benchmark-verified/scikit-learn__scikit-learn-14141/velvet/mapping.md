# mapping.md — scikit-learn__scikit-learn-14141

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 3d997697fdd166eff428ea9fd35734b6a8ba113e`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and gives
the provenance of the one axiom.

Repo file under change: `sklearn/utils/_show_versions.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `collectDependencyVersions` | `_get_deps_info()` — `sklearn/utils/_show_versions.py:33` (the `deps` roster at lines 41-50, the build loop at lines 57-64) | the modeled changed function (builds the dependency→version report) |
| `dependencyNames` | the `deps` list literal — `sklearn/utils/_show_versions.py:41-50` (post-patch: includes `"joblib"`) | pure spec: the fixed roster of covered dependency names, in order |
| `depEntries (ns : List (List Char))` | the per-name body of the `for modname in deps` loop (`sklearn/utils/_show_versions.py:57-64`) building `deps_info[modname] = ver` | pure spec: the name→version report as the per-name expansion of the roster |
| `lookupVersion` *(axiom — A-consumed via the `:|` callee model)* | the loop body's version resolution: `sys.modules[modname]` / `importlib.import_module(modname)` then `get_version(mod)` (`module.__version__`), with `None` on `ImportError` (`sklearn/utils/_show_versions.py:52-64`) | unchanged per-name version query; modeled as an uninterpreted `List Char → Option (List Char)` (no behavioral claim — see §3) |

The pre-patch repo state the change edits (refinement audit only, not in the
consumer spec view): the same `deps` list **without** the `"joblib"` entry
(`_show_versions.py:41-49` pre-patch). The patch inserts one list element.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) and G-AX use to translate values between the
Lean value domain and the Python repo types.

| repo reality | Lean carrier | bijection |
|---|---|---|
| a dependency name `str` (e.g. `"joblib"`) | `List Char` | `s` (Python str) ↔ `s.toList`-shaped `List Char`; on the ASCII module names here this is total and exact |
| the `deps` list `list[str]` | `List (List Char)` | element-wise per the row above; list order preserved; `len(deps)` ↔ `.length` |
| `deps_info` `dict[str, str | None]` | `List (List Char × Option (List Char))` (an association list) | the loop **inserts keys in `deps` order** with no duplicate names, so the insertion-ordered dict ↔ the assoc-list is a bijection on (key-set, per-key value, order). `dict[k]` ↔ `List.lookup`; `k in dict` ↔ `k ∈ .map Prod.fst`; `dict.keys()` (insertion order) ↔ `.map Prod.fst` |
| a version `str` value, or `None` on `ImportError` | `Option (List Char)` | `m.__version__` ↔ `some v`; `None` ↔ `none` |

`deps` has no duplicate names (it is a literal of distinct module names), so the
assoc-list ↔ dict bijection is exact: the dict has exactly one entry per roster
name, and the F2P test observes membership (`'joblib' in deps_info`) — which the
spec pins as `"joblib".toList ∈ out.map Prod.fst`.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `lookupVersion` ↔ the per-name version resolution (A-consumed)
**Callee:** the loop's version resolution — `sys.modules[modname]` or
`importlib.import_module(modname)`, then `module.__version__`, returning `None`
on `ImportError`. This is **unchanged** by the patch (the patch only extends the
`deps` roster). It is modeled as an **uninterpreted** function
`lookupVersion : List Char → Option (List Char)` with **no `ensures` axioms**:
the result is environment dependent (which versions happen to be installed), and
the contract this report's fix demands does NOT pin any concrete version value —
it pins only *which* dependencies are covered. Modeling it uninterpreted is the
weakest possible contract (directive 7): the proof never assumes anything about
its result, so it cannot over-claim.

**Why no `ensures` axiom is load-bearing:** the postconditions
`out = depEntries dependencyNames` and `"joblib".toList ∈ out.map Prod.fst` hold
for *every* total function `lookupVersion`. `lookupVersion` appears in the impl
only via the `:|` choice `ver = lookupVersion n` (sound by construction) and in
`depEntries` structurally; the version *value* is never constrained.

**Soundness check (G-AX):** because the axiom is uninterpreted (no `ensures`),
its only behavioral commitments are those of any total `List Char → Option
(List Char)`: a `str`-or-`None` **codomain** and **totality** (never raises
beyond the handled `ImportError`). `axiom_check.py` validates exactly those
against the **real** unchanged callee, two ways: (1) it reads every version
value the real `_get_deps_info()` resolved and asserts each is `str`-or-`None`
(direct observations of `lookupVersion`); (2) it runs the resolution logic
transcribed verbatim from the unchanged loop body over installed names plus
boundary + 2000 fuzzed nonexistent names, asserting each returns `str`-or-`None`
and never raises.

**Directive-7 boundary (why G-AX must NOT check the roster):** the orchestrator
runs G-AX against the **unpatched** repo (`gate_ax` does not apply the gold
patch, unlike `gate_conf`). The `deps` roster — *which* names are covered,
including `joblib` — is precisely the **function under change**, not an axiom;
asserting `_get_deps_info().keys()` here would (a) check the changed behavior of
the unpatched repo (the pre-patch 8-name roster, guaranteeing a false failure)
and (b) violate directive 7 by axiom-checking the function under spec. The
roster's joblib membership is validated by **G-RESOLVE + G-CONF**, which apply
the patch. G-AX is scoped to the unchanged callee `lookupVersion` only. Imports
only the repo module + stdlib. Exit 0 iff sound.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`14141`** for a
reproducible verdict. The R/I shadow it builds transliterates `dependencyNames`
and the `depEntries` fold to Python (the R/I-tagged ops); the A-tagged callee
`lookupVersion` is left as the **real** per-name version resolution of the
patched repo (run real callee, not a model). It compares the shadow's
(key-set, order) against the real patched `_get_deps_info()`'s `.keys()`, and
checks `'joblib'` membership, over the fuzz budget. Because the report is a fixed
roster (no input), fuzzing repeats the idempotent comparison to honour the
≥10⁵-input contract.
