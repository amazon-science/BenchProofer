# mapping.md — sympy__sympy-16450

Binds every `model.py` symbol to its repository counterpart at
`base_commit = aefdd023dc4f73c441953ed51f5f05a076f0862f`, states the type
abstraction, and gives the provenance of the axiom (callee source + the exact
behaviour the axiom encodes).

Repo file under change: `sympy/simplify/simplify.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `positive_standin_properties(stated)` | the per-symbol replacement built in `posify(eq)` — `sympy/simplify/simplify.py:202` (the changed dict-comprehension value at line 254) | the modeled changed behaviour: the effective assumptions of the stand-in symbol that replaces a sign-undecided free symbol |
| `derived(base, add_positive)` *(axiom — A-consumed)* | the unchanged property-inference engine viewed as a pure function: `Dummy(name, **base[+positive]).assumptions0` (`sympy/core/symbol.py:332` → `StdFactKB`; read via `assumptions0` `sympy/core/symbol.py:260`) | the deterministic effective-property MAP of a declaration; the mathematical model that the result is pinned to (`Result() is derived(...)`) |
| `resolve(base, add_positive)` *(axiom — A-consumed)* | the unchanged property-inference engine: `Dummy.__new__` (`sympy/core/symbol.py:332`) → `Symbol._sanitize` + `StdFactKB` assumption resolution (`sympy/core/assumptions.py`), read back via `assumptions0` (`sympy/core/symbol.py:260`) | the effectful call returning the engine's actual output object; its result IS `derived(base, add_positive)` (totality), unchanged by the patch |
| `stated` | `s.assumptions0` for a free symbol `s` with `s.is_positive is None` (`sympy/core/symbol.py:260`; `posify` filter at `simplify.py:255`) | the original quantity's stated assumptions (always lacks `positive`, since `is_positive is None`) |
| `POSITIVE()` | the assumption key `'positive'` (the `positive=True` the construction adds) | token for the "greater than zero" declaration |
| `FINITE()` | the assumption key `'finite'` (the property the issue centres on) | token for the "bounded / not infinite" property |

The pre-patch repo expression the change replaces (for the refinement audit, not
referenced from the consumer spec view): the dict-comprehension value
`Dummy(s.name, positive=True)` at `simplify.py:254` — which builds the stand-in
from `positive=True` ALONE, discarding `s.assumptions0`.

The post-patch expression: `Dummy(s.name, positive=True, **s.assumptions0)` —
which builds the stand-in from `positive=True` together with the original
symbol's stated assumptions.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| a symbol's assumption mapping (`assumptions0`, a `dict` from assumption-name `str` to `bool`) | `Dict[int, bool]` from an assumption-name token to its truth value | each assumption name (`'positive'`, `'finite'`, `'integer'`, …) ↔ a distinct `int` token; `POSITIVE()==0` ↔ `'positive'`, `FINITE()==1` ↔ `'finite'`, every other name ↔ some other token; membership `k in d` ↔ "the symbol states assumption `k`"; `d[k]` ↔ the stated truth value |
| `Dummy(name, positive=True, **base)` constructor + `.assumptions0` read | the `resolve(base, add_positive=True)` callee | building a fresh stand-in from the declaration and reading its derived assumptions ↔ `resolve(base, True)` |
| `s.name` (the textual symbol name) | omitted | the name does not affect the assumptions the issue + test observe; the F2P test asserts on `assumptions0`, not the name. (Modeled away.) |
| the dict-unpacking `**s.assumptions0` | passing `base = stated` (vs an empty base in the buggy skeleton) | the changed dataflow: whether the original symbol's stated assumptions reach the engine |

Assumption-name `str` keys are modeled as `int` tokens because Nagini bans
`str` indexing/iteration; only membership and per-key truth value are observed,
so integer identity is the faithful carrier.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `derived` / `resolve` ↔ the sympy property-inference engine (A-consumed)
**Callee:** `Dummy(name, positive=True, **base).assumptions0` — the unchanged
SymPy assumption engine (`Dummy.__new__` → `Symbol.__xnew__` → `_sanitize` +
`StdFactKB`, `sympy/core/symbol.py:332`, `sympy/core/assumptions.py`), read back
through `assumptions0` (`sympy/core/symbol.py:260`, which returns the resolved
non-`None` facts).

The engine is modelled as a pair: `derived(base, add_positive)` is the **pure
mathematical map** of the declaration to its effective properties (a
deterministic value, referenceable inside an `Ensures`); `resolve` is the
**effectful call** whose result object IS that map. The axiom encodes the
obligations the proof needs, the **weakest** sufficient contract:

  * **totality / closure:** the engine's output IS exactly `derived(base,
    add_positive)` (`resolve`'s `Ensures(Result() is derived(...))`). The
    operation may not add, drop, or alter any derived property: the whole result
    — including engine-derived keys the quantity never stated (`real`,
    `nonnegative`, …) — is pinned to the engine's derivation. (This is the
    Defect-1 strengthening: a postcondition that constrained only the
    input-derived subset let an impl fabricate a spurious derived key, which a
    licensed refinement turns into a non-resolving patch. The F2P test asserts
    the WHOLE `assumptions0` dict by exact equality, so the spec must bind the
    whole result.)
  * **fact preservation:** every assumption explicitly present in `base` is
    derived with the same truth value in the result. (The property the fix
    relies on: carrying `**s.assumptions0` into the constructor means every
    stated fact, e.g. `finite=True`, survives into the stand-in.)
  * **added positivity:** when `add_positive` holds, the result derives
    `positive=True`.

`derived` is left **abstract on the concrete closure content** (it does NOT
enumerate which extra facts — `real`, `complex`, `nonnegative`, … — the engine
adds; those vary across SymPy releases and the spec does not need their
identities, only that the result equals the engine's map). It does NOT claim the
engine always returns: when `base` together with `positive=True` is an
**inconsistent** declaration the engine raises `InconsistentAssumptions`.

**Permission:** the engine output is **read-only** to the caller (the stand-in's
assumptions are consulted, never mutated — `posify` stores the `Dummy` and
substitutes), so `resolve` yields only `Acc(dict_pred(Result()), 1/2)` and
`positive_standin_properties` ensures the result at `1/2`. Fractional result
permission is load-bearing: it is what forbids a verifying impl from mutating
the engine output to inject a spurious key (full permission would let
`r[k]=v` defeat the totality clause despite `Result() is derived(...)`).

**Domain (the `Requires`):** `add_positive ⇒ positive ∉ base`. This is always
satisfied in `posify`: a symbol is replaced exactly when `s.is_positive is None`,
so `'positive'` is never one of its `assumptions0` keys. Inconsistent
declarations (where the engine raises) are **out of the modeled operation's
domain** — there the gold patch raises identically, so the model and the gold
remain equivalent.

**Flag dependency:** the construction is fixed at `positive=True` (SymPy's
`posify` call and the only positivity declaration the routine makes).

**Soundness check (G-AX):** `axiom_check.py` runs the REAL engine
`Dummy("x", positive=True, **base).assumptions0` on the issue's exact example,
15 single-fact bases, and ~16k randomized **consistent** symbols drawn from the
full set of SymPy assumption predicates (`_assume_rules.defined_facts`). For
every replaced-domain symbol it asserts (a) every stated fact is preserved and
(b) `positive` is derived `True`. The **totality** clause is validated by the
model-fidelity assertion `real == derived` (full dict equality, both
directions) — the real `posify(s)[0].assumptions0` equals the engine result
exactly, so the result carries no key the engine did not derive. The
**raise-path** (the no-`Exsures` totality region) is checked in **LOCK-STEP**,
not skipped: when `base + positive` is inconsistent the engine raises and
`axiom_check.py` ASSERTS the real `posify(s)` raises too (it does so on 115 of
the in-container fuzz symbols). The pre-patch `Dummy(s.name, positive=True)`
(empty base) is additionally checked detectably wrong whenever the base carries
a fact bare positivity does not imply (e.g. `finite=True`). Imports only `sympy`
(the repo whose engine IS the real callee) + stdlib. Exit 0 iff sound
(validated in the pinned eval container with the gold patch applied: RC 0,
10139 consistent bases + 115 inconsistent lock-step + 15914 fuzz symbols).
