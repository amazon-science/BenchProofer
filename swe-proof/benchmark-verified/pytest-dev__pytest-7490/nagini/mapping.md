# mapping.md — pytest-dev__pytest-7490

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 7f7a36478abe7dd1fa993b115d22606aa0e35e88`, states the type
abstraction, and gives the provenance of the axiom (callee source + the exact
behaviour the axiom encodes).

Repo file under change: `src/_pytest/skipping.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `settle_saved_evaluation(slot, final_marker_state)` | the post-`yield` portion of `pytest_runtest_call` — `src/_pytest/skipping.py:248` (the gold patch's added block at the end of that hook-wrapper) | the modeled changed behaviour: settle the saved xfail evaluation against the final marks |
| `evaluate_marks(marker_state)` *(axiom — A-consumed)* | `evaluate_xfail_marks(item)` — `src/_pytest/skipping.py:200` | unchanged community callee: evaluates the item's xfail marks to an `Optional[Xfail]` |
| `SavedSlot` (`present`, `value`) | the per-item store slot under `xfailed_key` (`src/_pytest/skipping.py:228`), accessed via `item._store.get(xfailed_key, None)` / `item._store[xfailed_key] = …` | the saved evaluation the report step consumes |
| `Xfail` (`run`) | `class Xfail` — `src/_pytest/skipping.py:191` (an `attr.s` of `reason/run/strict/raises`) | the evaluated expected-failure descriptor; only the presence/non-presence is observed by the modeled behaviour |

The downstream consumer of the saved slot (not modeled, but the reason the
behaviour matters): `pytest_runtest_makereport` reads
`item._store.get(xfailed_key, None)` (`src/_pytest/skipping.py:264`) and uses it
to decide whether a failing run is an expected failure / a strict xpass is a
real failure.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| the item's set of marks (which can change while the body runs) | an opaque marker-state token `marker_state: int` | the body attaching a mark is a transition to a different token; `evaluate_xfail_marks(item)` ↔ `evaluate_marks(marker_state)` |
| `item._store.get(xfailed_key, None)` returning `None` because the key was never set | `SavedSlot.present == False` | "absent key" ↔ `present == False` |
| `item._store[xfailed_key]` holding `None` (an evaluation that produced no xfail) | `SavedSlot.present == True and SavedSlot.value is None` | "present, empty evaluation" ↔ `present == True, value is None` |
| `item._store[xfailed_key]` holding an `Xfail` | `SavedSlot.present == True and SavedSlot.value is not None` | "present, non-empty evaluation" ↔ `present == True, value is not None` |
| `item._store[xfailed_key] = xfailed = evaluate_xfail_marks(item)` (after the body) | `slot.value = evaluate_marks(final_marker_state); slot.present = True` | the store write ↔ the slot write |
| `Xfail` object | minimal class `Xfail(run)` | only object identity / non-`None`-ness is observed by the modeled refresh |

The model collapses the pre-`yield` setup (which the gold patch leaves
behaviour-equivalent for the F2P scenarios — see refinement.md) into the
slot's *pre-state* (`Old(slot.present)`, `Old(slot.value)`), and models only
the post-`yield` refresh block the patch adds, because that block is the entire
behavioural change the two F2P tests observe.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `evaluate_marks` ↔ `evaluate_xfail_marks` (A-consumed)
**Callee:** `_pytest.skipping.evaluate_xfail_marks(item)` (`skipping.py:200-222`).
It iterates `item.iter_markers(name="xfail")`, and returns an `Xfail(...)`
descriptor for the first applicable mark or `None`. It is a **deterministic
pure function of the item's current marker state**: called twice on the same
item it returns equal results; it reads marks but does not mutate them.

The patch does NOT change `evaluate_xfail_marks`; the patch only changes WHEN it
is (re-)invoked relative to the body running. The model therefore axiomatizes it
as a `@Pure @ContractOnly` function of an opaque marker-state token. The axiom's
Ensures is **empty** — the proof relies only on `evaluate_marks` being a
function (so the same token yields the same value, used in the
`slot.value is evaluate_marks(final_marker_state)` postcondition). This is
the **weakest** possible contract: it claims nothing about the returned value's
fields, never over-approximating the real callee (so it is trivially sound).

**Axiom domain note (directive 7 — acknowledged, inert over-claim).** The
`@Pure @ContractOnly evaluate_marks` has no `Exsures`, so as modeled it is a
TOTAL function (returns normally on every `int` token). The real
`evaluate_xfail_marks` is wider-behaviour: on some attainable marker states it
RAISES `Failed` rather than returning (e.g. an `xfail(condition)` whose
condition string fails to evaluate, or `xfail(strict=...)`-style misuse). The
axiom's no-raise domain is therefore strictly LARGER than the callee's
no-raise domain. This over-claim is INERT for this instance: (i) the proof
consumes only determinism (same token → same value), never the totality; (ii)
no F2P/P2P test exercises a raising-condition mark — the two scenarios use a
plain `xfail(reason=...)` and a `xfail(strict=True)`, both of which evaluate
without raising; and (iii) the dynamic-attach path the runner exercises catches
any such raise at the hook level even when one were attached. Hence
`verify ⟹ resolved` is unaffected. (The weaker, fully-faithful alternative —
adding an `Exsures` raise path — would only add an unreached branch; it is not
required and is omitted to keep the axiom at its weakest sufficient form.)

**Soundness check (G-AX):** `axiom_check.py` runs the REAL
`evaluate_xfail_marks` on a collected item twice and asserts the two
evaluations agree (determinism), asserts an item with no xfail mark evaluates to
`None`, then attaches `pytest.mark.xfail(...)` dynamically and asserts the
evaluation becomes non-`None` and is still deterministic on the new state — the
exact properties the axiom relies on. It imports only `pytest` / `_pytest`
(the package under test); nothing else. Exit 0 iff sound.

### 3.2 The refresh itself — deep model (A-reference)
The changed operation — repopulating the saved slot from the post-body
evaluation when nothing non-empty was saved before the body — is an ordinary
conditional store-write Nagini expresses directly, so it is modeled **deeply**
(the `if not slot.present … elif slot.value is None …` impl region literally is
the gold patch's added block), NOT hidden behind an axiom. There is therefore
no consumed axiom for the refresh; instead `axiom_check.py` validates the deep
model end-to-end by driving the REAL patched pytest on the two issue scenarios
(a dynamically-xfailed failing test → `1 xfailed`; a dynamically-strict-xfailed
passing test → `1 failed`) and reconstructing the pre-patch no-refresh flow
inline to witness that without the refresh the mark is ignored (G-DIFF).
