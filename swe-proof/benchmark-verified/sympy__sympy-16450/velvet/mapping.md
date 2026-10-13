# mapping.md — sympy__sympy-16450

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = aefdd023dc4f73c441953ed51f5f05a076f0862f`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and
gives the provenance of each axiom / deep-model reference.

Repo file under change: `sympy/simplify/simplify.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `positivizeSymbols (symbols : List SymInfo)` | `posify(eq)` — `sympy/simplify/simplify.py:202` (changed body line 254) | the modeled changed function: replace under-determined free symbols with positive surrogates |
| `SymInfo` | a free `Symbol` of `eq`, reduced to the two observations the change reads: its known property set (`assum`) and its sign-determinacy (`isPositive`) | rich-object → structure abstraction (mapping.md §2) |
| `SymInfo.assum` | `s.assumptions0` — `sympy/core/symbol.py:260` (returns the non-`None` facts of `s._assumptions`) | a symbol's already-known assumption facts |
| `SymInfo.isPositive` | `s.is_positive` (read by the comprehension filter `if s.is_positive is None`, line 255) | sign determinacy: `none` ↔ `is_positive is None` |
| `replacement (s : SymInfo)` | the per-symbol replacement-construction the comprehension performs at line 254 (post-patch) | pure spec: the surrogate's resulting property set for one symbol |
| `closeAssumptions` *(deep-model reference — A-reference)* | the assumption-closure engine `StdFactKB.__init__` invoked inside `Dummy.__new__` (`sympy/core/assumptions.py:208`, via `sympy/core/symbol.py:235`); observed through `Dummy(...).assumptions0` | unchanged callee: closes a supplied fact-set to the full derived assumption set |
| `posifyAll (symbols : List SymInfo)` | the dict comprehension `{s: Dummy(...) for s in eq.free_symbols if s.is_positive is None}` mapped to each surrogate's `assumptions0`, then read back via `eq.subs(reps)` | pure spec: the per-symbol surrogate property sets, in symbol order |

Pre-patch repo state the change fixes (refinement audit only, not in the consumer
spec view): line 254 reads `Dummy(s.name, positive=True)` — i.e. the surrogate is
constructed from positivity *alone*, discarding `s.assumptions0`.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) and G-AX use to translate values between the
Lean value domain and the Python repo types.

| repo reality | Lean carrier | bijection |
|---|---|---|
| a `Symbol`'s `assumptions0` dict `{str: bool}` (only `True`/`False` values; `None` facts omitted) | `List (String × Bool)` | `d` (Python dict) ↔ `[(k, v), …]`; key order is irrelevant — both sides treat it as the *set* of facts. `k in d` ↔ `(k, d[k]) ∈ l`. |
| `s.is_positive` ∈ {`True`, `False`, `None`} | `Option Bool` | `True ↔ some true`, `False ↔ some false`, `None ↔ none` |
| one free `Symbol` `s` (only `assumptions0` + `is_positive` are read) | `SymInfo` structure | the two observed fields; the symbol's *name* and expression identity are unobserved by the changed line and dropped (the name only labels the surrogate; `assumptions0` is name-independent) |
| `eq.free_symbols` (a `set` of symbols) | `List SymInfo` | unordered set ↔ list; the modeled property is per-element, so any order is faithful. The comprehension's filter `is_positive is None` is modeled inside `replacement`'s `if`. |
| `Dummy(s.name, positive=True, **s.assumptions0).assumptions0` | `closeAssumptions (("positive", true) :: s.assum)` | the surrogate's resulting fact set; G-AX validates equality to the real construction |
| `eq.subs(reps)` then reading each surrogate's `assumptions0` | identity over the per-symbol `replacement` results | `subs` swaps symbol → surrogate; the observable (`assumptions0` of the surrogates) is exactly the list `posifyAll` produces. R-abstraction. |

`assumptions0` carries only resolved (`True`/`False`) facts, never `None`; so a
fact present in `s.assum` is a *known* property. The closure engine
(`closeAssumptions`) only ever **adds** derived facts to a consistent supplied
set — it never drops one (the StdFactKB invariant); G-AX checks this.

## 3. Callee provenance

### 3.1 `closeAssumptions` deep-model reference ↔ `StdFactKB` / `Dummy(...).assumptions0` (A-reference)
**Callee:** the assumption-closure engine. `Dummy(name, **facts)` builds
`StdFactKB(facts)` (`sympy/core/symbol.py:235`), which closes `facts` under the
assumption rule base; `.assumptions0` then reads back the resolved facts. This
callee is **unchanged** by the patch. It is modeled as the **uninterpreted**
function `closeAssumptions : List (String × Bool) → List (String × Bool)` (no
`ensures` consumed by the proof — it is NOT a consumed axiom; it is the deep-model
reference whose fidelity G-AX validates).

The *changed* operation is the **argument** handed to this engine: post-patch the
surrogate is closed from `{positive: True} ∪ s.assumptions0`; pre-patch from
`{positive: True}` alone. That argument construction is modeled **deeply** and
concretely (`("positive", true) :: s.assum`, an I/R op), not axiomatized.

**Why positivity alone loses properties (the bug):** the closure of
`{positive: True}` does **not** re-derive an arbitrary declared fact such as
`finite=True` — positivity does not imply finiteness (`oo` satisfies
`is_positive=True`, `is_finite=False`). So a symbol declared `finite=True` whose
sign is unknown loses `finite` under the pre-patch construction and retains it
under the post-patch one. This is the single behavioural change `test_posify`
(issue 16438) observes.

**Soundness check (G-AX):** `axiom_check.py` constructs real `Symbol(name,
**facts)` for boundary + 20 000 fuzzed *consistent* fact-sets with `is_positive`
unknown, then builds `Dummy(name, positive=True, **facts)` and asserts: (a) the
construction is deterministic; (b) every supplied fact appears in the surrogate's
`assumptions0` (the closure-never-drops invariant that makes the deep model
sound); (c) `positive: True` appears. Imports only `sympy`. Exit 0 iff sound.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1)

`conformance_check.py` seeds its `random.Random` with **`16450`**. The R/I shadow
it builds transliterates the fold (`free_symbols` filter by `is_positive is None`,
the `("positive", true) :: assum` argument construction) to Python and leaves
`closeAssumptions`'s callee as the **real** `Dummy(...).assumptions0`
(A-tagged → run real callee). It diffs the shadow's per-surrogate `assumptions0`
against the real `posify`'s surrogate `assumptions0` over ≥10⁵ fuzzed symbols;
exit 0 iff zero disagreements.
