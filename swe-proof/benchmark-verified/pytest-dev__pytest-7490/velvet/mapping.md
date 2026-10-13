# mapping.md — pytest-dev__pytest-7490

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 7f7a36478abe7dd1fa993b115d22606aa0e35e88`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and gives
the provenance of the parametrically-modeled callee.

Repo file under change: `src/_pytest/skipping.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `resolveDynamicXfail (entry evalBefore evalAfter : Option Xfail)` | `pytest_runtest_call(item)` — `src/_pytest/skipping.py:248` (hookwrapper) | the modeled changed function: it resolves the stored xfail determination across one test body's execution |
| `Xfail` (structure: `reason`, `run`, `strict`) | `class Xfail` — `src/_pytest/skipping.py:189` (`@attr.s(slots=True, frozen=True)`) | the determination object; only the fields downstream reporting consults are modeled (mapping.md §2) |
| `Option Xfail` | the value stored under `xfailed_key` (`StoreKey[Optional[Xfail]]`, `src/_pytest/skipping.py:228`); `None` ↔ `none`, an `Xfail` ↔ `some _` | the xfail determination known at a given moment |
| `evalBefore` / `evalAfter` *(parametric callee inputs — A-reference)* | results of `evaluate_xfail_marks(item)` — `src/_pytest/skipping.py:200` | the UNCHANGED marker-evaluation callee, modeled parametrically as its `Option Xfail` result; validated against the real callee by axiom_check.py (G-AX) |
| `refresh` / `finalXfail` (pure region) | the "evaluate only if not already known" guard (`if xfailed is None: ... = evaluate_xfail_marks(item)`) applied across the body, as patched | pure spec: the determination handed to reporting |

The reporting consumer (`pytest_runtest_makereport`, `src/_pytest/skipping.py:261`)
is UNCHANGED by the patch; it simply reads `item._store.get(xfailed_key, None)`.
The patch's whole observable effect is which value is stored there by the time
`makereport` runs — exactly what `resolveDynamicXfail` returns.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) and G-AX use to translate values between the Lean
value domain and the Python repo types. A wrong entry surfaces as spurious G-CONF
disagreements.

| repo reality | Lean carrier | bijection |
|---|---|---|
| `item._store.get(xfailed_key, None)` ∈ `Optional[Xfail]` | `Option Xfail` | `None` ↔ `none`; an `Xfail(reason, run, strict, raises)` ↔ `some { reason, run, strict }` |
| `Xfail.reason : str` | `Xfail.reason : String` | identity on character content |
| `Xfail.run : bool`, `Xfail.strict : bool` | `Bool` | identity |
| `Xfail.raises : Optional[Tuple[...]]` | (omitted) | not observed by the storage behaviour the patch changes; `makereport`'s `raises` branch is unchanged and orthogonal to which determination is *stored* |
| the test body running between the hook's pre-yield and post-yield | the gap between the two `match`/`refresh` steps in the impl | the body may add a marker dynamically; modeled by `evalAfter` possibly being `some _` where `evalBefore` was `none` |

### Flag dependency (G-AX / G-CONF fuzz configuration)
The modeled passthrough behaviour is for determinations with **`run = True`**
(the default; the case the F2P tests exercise). When `run = False`, the hook's
pre-yield `xfail("[NOTRUN] " + reason)` raises and the post-body re-evaluation is
a no-op for storage — a pre-existing branch unchanged by this patch and not
exercised by the F2P tests. The fuzz domain therefore fixes `run = True` and
`config.option.runxfail = False` (the tested configuration); recorded here so
G-AX/G-CONF drive the right configuration.

## 3. Callee provenance (A-reference — checked by G-AX / axiom_check.py)

### 3.1 `evaluate_xfail_marks` modeled parametrically (A-reference)
**Callee:** `evaluate_xfail_marks(item)` — `src/_pytest/skipping.py:200`. UNCHANGED
by the patch. It is modeled **parametrically**: its result enters
`resolveDynamicXfail` as the abstract inputs `evalBefore` (evaluated before the
body) and `evalAfter` (evaluated after the body). There is **no consumed
`axiom`**; the spec is quantified over every possible `Option Xfail` result, so
it is sound for whatever the real callee returns.

The two properties the parametric model relies on, validated by G-AX against the
real `evaluate_xfail_marks`:
1. **Pure function of the item's markers** — calling it yields a determination
   computed solely from `item.iter_markers(name="xfail")` (+ `xfail_strict` ini);
   calling it twice with the same markers yields the same `Option Xfail`.
2. **Reflects markers present at call time** — a determination only becomes
   available once a matching marker is present. Evaluating on an item with no
   xfail marker yields `None`; evaluating the same item after an xfail marker has
   been added yields `Xfail(reason, run, strict, raises)` extracted from that
   marker. This is precisely what makes `evalAfter` able to be `some _` where
   `evalBefore` was `none` — the dynamic-add case the patch fixes.

**Soundness check (G-AX):** `axiom_check.py` imports the real
`_pytest.skipping.evaluate_xfail_marks`, drives it with fake items carrying
scripted marker sets (none; one unconditional xfail with reason/strict/run
variations; xfail added after an initial empty evaluation), and asserts both
properties hold on boundary + fuzz marker sets. stdlib + installed pytest only.
Exit 0 iff sound.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`7490`** so the
consumer-side verdict is reproducible. The R/I shadow transliterates
`refresh`/`finalXfail` to Python (R/I-tagged ops). The ORACLE drives the REAL
patched `pytest_runtest_call` generator in-container (the gold patch applied by
G-RESOLVE before this runs) with a fake item and a scripted
`evaluate_xfail_marks` (the parametric callee left as a controllable stub so the
`entry`/`evalBefore`/`evalAfter` triple is enumerable), observing the value stored
under `xfailed_key` after the hook completes. There are no A-tagged callees
*inside* the impl region (the callee results are inputs), so the shadow is pure
R/I and `conf_skip = false`.
