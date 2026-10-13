# SPEC_GUIDE — binding rules for a twin-artifact verification bundle

*Normative. Every construction agent follows every rule. The gates
(docs/architecture.md §5) enforce them; the agentic gates (G-EQ, G-AX, G-PANEL) are
adversarial and will actively try to break your bundle.*

You are given one SWE-Bench-Verified instance: a repo worktree at
`base_commit`, the problem statement, the gold `patch`, the `test_patch`, and
the FAIL_TO_PASS / PASS_TO_PASS lists. You produce, in `<benchmark-root>/<id>/nagini/`:
`model.py`, `model_prepatch.py`, `patch.diff`, `refinement.md`, `mapping.md`,
`meta.json`.

## 0. Prime directives

1. **Never change the task.** Add files only; never edit `instance.json`,
   repo files (except via `patch.diff`, which equals/rephrases the gold),
   tests, or the problem statement. (G-INTEGRITY.)
2. **The guarantee is `verify ⟹ correct`.** "correct" = the official harness
   reports `resolved`. Your `model.py` is the verifiable face of a real patch;
   your `patch.diff` is that real patch. They must be **equivalent** — related
   only by the type-only refinement you declare in `refinement.md`. If a
   verifying implementation of your spec could be refined to a patch that does
   NOT resolve, your spec/refinement is broken — fix it, don't ship it.
3. **`model.py` is a faithful SKELETON of the fix, not a re-imagining.** Its
   control flow and data flow mirror `patch.diff` line-for-line under the
   refinement. You may NOT model a different algorithm that happens to satisfy
   a weaker spec. (G-EQ checks this; G-DIFF checks the spec sees the bug.)
4. **Spec strength: verified ⟹ correct, not just verified ⟹ plausible.** The
   `Ensures` must pin the behavior the issue + F2P tests demand, derived from
   the problem statement and tests — strong enough that NO wrong implementation
   of the modeled behavior can satisfy it (G-PANEL attacker 1 will try to find
   one). Ask: "could an impl satisfy this spec and still fail an F2P test?"
   **Termination is part of that strength:** Nagini proves only PARTIAL
   correctness unless the spec demands otherwise, so every method that owns a
   loop states `Requires(MustTerminate(n))` in its pre-conditions region (`n` is
   a LEVEL, not a measure — `2` unless the method calls another obligated
   method, whose level must be strictly lower) and closes that loop's invariants
   region with `Invariant(MustTerminate(e))`, `e` an upper bound on the
   REMAINING iterations that strictly decreases and stays positive (`n - i + 1`
   for `while i < n`) — without the obligation an implementation that never
   reaches the return satisfies every `Ensures` vacuously and VERIFIES, while
   its faithful patch hangs the test it was meant to fix.
5. **Read-only inputs get fractional permission.** Any parameter the operation
   does not mutate is required AND ensured at `Acc(list_pred(x), 1/2)` (full
   permission only for genuinely-mutated objects, with the post-state stated
   exactly). A full-permission read-only input referenced in a postcondition
   lets a wrong impl satisfy it vacuously by overwriting the input — it
   verifies but is wrong. (The most common spec-weakness mode.)
6. **No leakage.** The spec view (model.py minus impl + proof — INCLUDING the
   module docstring and all comments) is shown to consumers. It must not quote
   any gold-diff line, name the patched file/function/line (in identifiers OR
   docstrings/comments), use an identifier echoing a patched repo symbol, or
   narrate the bug→fix MECHANISM. State the abstract desired behavior the
   issue demands, never the edit or the diagnosis of how to fix it.
   **Leakage is judged against the solver-visible `problem_statement` ONLY —
   NOT `hints_text`** (which the consumer never sees). A term/symbol/diagnosis
   that appears only in `hints_text` is NOT public; echoing it in the spec view
   leaks. (The most common leakage failure: narrating the fix in the docstring
   using hints_text-only vocabulary.) The model docstring should read like a
   behavioral contract ("element i of the result is f(...)"),
   not "the bug was X; the fix fills Y instead of Z." (G-LEAK / G-PANEL
   attacker 3.) **Exception — relaxed-leakage:** a few
   instances are `problem_statement ↔ gold` MISMATCHES where the gold's tested
   discriminator exists only in `hints_text`/gold internals, so a *faithful*
   spec MUST name it. When independent adversarial analysis confirms faithful +
   non-leaking is impossible (not mere lazy de-narration) AND the core is sound
   + G-RESOLVE resolves, KEEP the instance with the leak allowed: ship
   `RELAXED_LEAKAGE.md` + set `meta.json gates.G-LEAK.status = "relaxed"`. Do NOT
   relax leakage to dodge ordinary de-narration work — only for a proven
   PS↔gold mismatch. (`verify ⟹ correct` is unaffected; only no-leakage relaxes.)
7. **Axioms are liabilities — and the #1 soundness defect is over-claiming.**
   Each `@ContractOnly` is (a) about a real callee the changed function CALLS
   but does NOT change, (b) **the WEAKEST contract sufficient for the proof —
   never stronger than the real callee's observed behavior**, (c)
   provenance-cited in mapping.md (callee file:line + doc/source evidence),
   (d) executable-checkable (G-AX runs the real callee against it). NEVER
   axiomatize the function under spec or the operation the patch changes.
   Specific over-claim traps, each of which has produced a real G-AX failure:
   - **Termination/no-raise:** do NOT `Ensures` (or rely on the absence of
     `Exsures` implying) the callee always returns normally unless you have
     verified it NEVER raises on any Requires-satisfying input. Real callees
     raise (e.g. `pkgutil.get_loader` raises `ImportError` on a bad dotted
     name). Either model the raise path (`Exsures` / a guarded `Requires` that
     excludes it) or weaken the contract.
   - **Exact values / sentinels:** do NOT `Ensures` exact output values the
     callee only sometimes produces, and do NOT forget in-domain sentinels
     (NaT `-2**63`, NaN, empty, boundary). Your `axiom_check.py` MUST fuzz the
     raise/exception behavior AND sentinels/boundaries, not just the happy
     path — that is exactly what G-AX will do independently.
   - **No double-mask in axiom_check.py.** If the A-reference asserts an
     INDEX-level (or structural) equivalence, the check must assert it at THAT
     level (`model_keeps(k) ⇔ k ∈ gold_index_set`) — NOT via a value-membership
     proxy. A check that filters BOTH sides by the same predicate the model is
     supposed to decide (e.g. comparing only `value(k) is real` on each side)
     silently drops any disagreeing index whose value is masked out, so an
     over-keep/under-keep passes spuriously. The predicate under test may not
     appear on both sides of the checked equality. Likewise, a skip-guard
     (`if cond: return`) that fires on an F2P input is a FALSE pass — enumerate
     F2P cases and fail loud if any is skipped. (Concrete case: in sympy-21596
     an `is_real` double-mask hid an index-3 over-keep; the gold yields EmptySet.)
8. **Ground the postcondition in the inputs — never pin it to an ungrounded
   oracle.** A postcondition must be dischargeable ONLY by the real
   computation. Do NOT write `Ensures` that equate `Result()` to an opaque
   "answer-key" — an `@Pure @ContractOnly` oracle or a pure fn with a hardcoded
   lookup table — because a wrong impl can simply ECHO it
   (`return materialize(oracle(x))`) and verify without doing the work. Same
   trap when an axiom pins a marker EXACTLY (`Ensures(Result()==2)`): the caller
   discharges `P ⇒ Result()==2` with a literal `return 2`, never invoking the
   helper. Instead pin behavior with **expressible structural predicates on the
   actual input carrier** (length / membership / order / element-wise /
   arithmetic relations), and tie any marker/code to a witnessed structural
   property of the input — so the result must be *produced by* the modeled
   branch, not merely *equal to* a constant or oracle value. (This is the #2
   spec-too-weak mode after directive 5, and it is how an over-eager
   strengthening re-opens the hole it was meant to close: a real clause gets
   swapped for an oracle. G-EQ / G-PANEL attacker 1 will hunt for an
   echo-the-oracle cheat.)

## 1. The twin: model.py, patch.diff, refinement.md

### 1.1 model.py skeleton
Imports limited to `typing` and `nagini_contracts.*` (`.contracts`, plus
`.obligations` for `MustTerminate`). Mandatory marker
regions (machine-parsed): `# axioms-start/end`, `# pure-start/end`,
`# pre-conditions-start/end`, `# post-conditions-start/end`,
`# invariants-start/end`, `# impl-start/end`.

```python
from typing import List, Optional
from nagini_contracts.contracts import *

# axioms-start
@Pure                 # MUST be @Pure if used inside an Ensures (measured)
@ContractOnly
def callee(x: List[int]) -> int:
    Requires(Acc(list_pred(x), 1/4))   # weakest precondition; fractional read
    Ensures(...)                        # exactly what the proof needs
# axioms-end

# pre-conditions / post-conditions / invariants / impl regions follow, and the
# impl is the SKELETON of patch.diff under refinement.
```

`model_prepatch.py`: byte-identical spec; impl is the pre-patch (buggy)
skeleton. MUST fail verification (G-DIFF). One `model_prepatch_<k>.py` per
independently-fixed behavior if the patch fixes several.

### 1.2 patch.diff
The equivalent real patch. For the shipped ground truth it is the gold patch
verbatim, OR a behavior-identical rephrasing if the gold uses a construct that
has no clean skeleton (rare; justify in refinement.md). It MUST apply at
`base_commit` and make the harness `resolved` (G-RESOLVE).

### 1.3 refinement.md — the operation correspondence (the heart of soundness)
A table mapping every operation in model.py's impl region to its counterpart
in patch.diff, each tagged:
- **R (type refinement):** same operation, refined carrier type. E.g.
  `self_row[j]` (List[int]) ↔ `self[i, j]` (Matrix); `len(other_row)` ↔
  `other.cols`. State the type bijection.
- **A (axiomatized callee):** model calls `@ContractOnly callee`; patch calls
  the real callee. Cite the axiom and its G-AX evidence.
- **I (identical):** literally the same concrete operation (ints, bools,
  control flow).
EVERY step must be R, A, or I. A step that is a *changed operation Nagini
cannot express* is FORBIDDEN here — model it deeply per §3 instead. G-EQ
reviewers reject any refinement.md with an unjustified or kind-3 step.

## 2. Type modeling

| repo reality | model as |
|---|---|
| `str` | `List[int]` of code points (str indexing crashes Nagini) |
| `float` where the bug is NOT about precision | `int` scaled — only if refinement.md shows the tested behavior is precision-independent; else use interpreted floats |
| `float` where precision IS the behavior | real Python `float` with `--float-encoding=real` (or `ieee32` for bit-level); record the flag in meta.json and set it in the verify invocation. Do NOT fake with int. |
| rich object (Matrix, QuerySet, AST, DataFrame) | minimal class with only the touched fields, or parallel `List`/`Dict`; refinement.md gives the field bijection |
| exception raised | user-defined exception class + `Exsures` (builtin-exception Exsures crashes the translator), or a no-Exsures spec that forbids the raise |
| unchanged library/utility callee | `@ContractOnly` axiom (kind A) |
| kwargs/defaults | explicit positional params |

Banned (verifier crash surface, measured on 1.2.0): `str` indexing/iteration;
`Exsures(<builtin exception>)`; imports beyond `typing`/`nagini_contracts`;
`Assume`/`Refute`; I/O. Dict/Set access guarded (`k in d` before `d[k]`);
permissions via `dict_pred`/`set_pred`/`list_pred`/`Acc`. Every `Forall`/`Exists`
body indexing a sequence carries explicit in-bounds guard conjuncts; loop-relied
bounds are loop invariants.

Nagini gotchas (measured on the pinned verifier; encode these):
- An axiomatized callee used inside an `Ensures` must be `@Pure @ContractOnly`
  (a non-`@Pure` callee in a postcondition is `purity.violated`).
- A `@Pure` callee still needs its `Requires` permission satisfied at every
  call site, including inside other functions' postconditions — account for
  fractional permission carefully (a too-strong `Requires` on the callee makes
  the caller's postcondition unprovable).
- Interpreted floats are OFF by default ("Floating point operations are
  uninterpreted" warning) — naive float specs vacuously "fail"; pass the flag.

## 3. Multi-site changes and axioms (the hard cases)

- **Multiple changed functions:** model each as its own function in `model.py`
  with its own contract — the per-function marker regions (`pre-conditions`,
  `post-conditions`, `impl`, `invariants`) REPEAT, one set per implemented
  function (the `axioms` and `pure` regions stay single, module-level). The
  impl skeletons mirror each patched hunk. If the changed functions call each
  other, the caller's spec uses the callee's spec (not an axiom — it's under
  spec). refinement.md covers every hunk; G-DIFF needs one failing
  `model_prepatch_<k>` per independently-observable fixed behavior. (Prefer
  modeling each site as its own function over collapsing sites into one deep
  function + axiomatized callee — the latter is sound but yields fewer
  differential witnesses and a less faithful skeleton.)

- **Consumed axiom vs. deep-model reference (refinement.md MUST distinguish).**
  When a changed operation is modeled DEEPLY (spelled out, e.g. an escape fold
  over `List[int]`), the corresponding callee is NOT an axiom the proof
  consumes — it is a *reference the deep model is validated against by G-AX*.
  Do not ship a `@ContractOnly` axiom the proof never uses ("dead axiom") and
  claim in refinement.md that the proof depends on it. Tag each refinement.md
  row: **A-consumed** (the proof uses this axiom's Ensures) vs **A-reference**
  (the deep model is checked == this real callee by axiom_check.py / G-AX).
  A dead axiom is a hygiene defect; a mislabeled one is a refinement-audit
  failure (G-EQ).

- **Sequence folds: use front-recursion (measured).** Index-recursion over a
  sequence does NOT auto-unfold in Nagini 1.2.0; a fold spec like
  `escaped(s) == entity(s[0]) + escaped(s.drop(1))` (front-recursive `@Pure`
  over `PSeq`) gives one auto-unfold per loop step and verifies, paired with a
  matching loop in the impl. This is the canonical pattern for "result is the
  per-element expansion of the input."

- **`html.escape`-style axioms are sound only under their default flags.** The
  `html.escape` axiom is sound only for `quote=True` (Django's call + CPython's
  default); record such flag dependencies in mapping.md so G-AX fuzzes the
  right configuration.
- **Callees that must be axiomatized:** anything the changed code CALLS but
  does not change and Nagini can't express → `@ContractOnly` (kind A). The
  axiom is the weakest contract the proof needs. G-AX will execute the REAL
  callee on Requires-satisfying inputs (boundary + fuzz, in-container) and
  check every observation meets the Ensures. An axiom stronger than the real
  callee is unsound and will be caught.
- **The changed operation is inexpressible:** model it
  deeply — interpreted floats, strings as `List[int]` with the operation
  spelled out, a richer axiom that captures the *changed* property (not the
  unchanged callee). If genuinely impossible in 1.2.0, write
  `<benchmark-root>/<id>/nagini/BLOCKED.md` (what you tried, the exact wall, candidate modelings)
  and stop. A principled BLOCKED is a valid result; a weakened/faked spec
  is a benchmark-poisoning bug.

## 4. Workflow & self-check (budget verifier calls)

1. mapping.md first (forces reading the real code + callees), then axioms,
   contracts, skeleton impl, proof annotations.
2. `bash scripts/nagini_verify.sh <benchmark-root>/<id>/nagini/model.py [--float-encoding=...]`
   (G-VERIFY). Fix proof annotations on failure — never weaken a contract.
   The script enforces a hard timeout (exit 124 = "did not converge" → simplify
   the model; do not pile on annotations). ≤8 rounds.
3. `model_prepatch.py` must FAIL (G-DIFF). Write `patch.diff`; apply it in the
   container and confirm `resolved` (G-RESOLVE); confirm a gold-faithful impl
   verifies (G-GOLD). Write `refinement.md` and self-audit it against the R/A/I
   discipline before submitting to the panel.
4. `meta.json`: modeled functions, axiom inventory + provenance, float-encoding
   flag (if any), verify wall-times, frozen-spec region hashes, gate results.

A verification failure is information: read the assertion location; strengthen
invariants or fix the skeleton transcription. If a genuinely-required contract
is unprovable in Nagini's logic, that is BLOCKED, not a license to delete it.
