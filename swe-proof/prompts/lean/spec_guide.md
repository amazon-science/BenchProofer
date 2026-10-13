# SPEC_GUIDE — binding rules for a vanilla Lean 4 + Mathlib twin-artifact bundle

*Normative. Every construction agent follows every rule. The gates (docs/architecture.md §5)
enforce them; the agentic gates (G-EQ, G-AX, G-PANEL) are adversarial and will
actively try to break your bundle. This is the vanilla-Lean-4 + Mathlib variant
(no Velvet); the spec/impl/proof shape is the CLEVER triple. The construction agent writes the **spec + impl**; the SEPARATE proof
agent (prompts/lean/proof_agent.md) closes the proof.*

You are given one SWE-Bench-Verified instance: a repo worktree at `base_commit`,
the problem statement, the gold `patch`, the `test_patch`, and the FAIL_TO_PASS /
PASS_TO_PASS lists. You produce, in `<benchmark-root>/<id>/lean/`: `Solution.lean`,
`Solution_prepatch.lean`, `patch.diff`, `refinement.md`, `mapping.md`,
`axiom_check.py`, `conformance_check.py`, `meta.json`.

The target shape is imperative `Id.run do … for … mut …` impls with every
`correct_*` closed and a clean `#print axioms`; `prompts/lean/proof_playbook.md`
works that shape end to end.

## 0. Prime directives

1. **Never change the task.** Add files only; never edit `instance.json`, repo
   files (except via `patch.diff`, which equals/rephrases the gold), tests, or
   the problem statement. (G-INTEGRITY.)
2. **The guarantee is `verify ⟹ correct`.** "verify" = `Solution.lean` compiles
   under the pin AND every `theorem correct_<name>` closes with no `sorry`/
   `admit` and a clean `#print axioms` (no `sorryAx`). "correct" = the official
   harness reports `resolved`. Your `Solution.lean` is the verifiable face of a
   real patch; your `patch.diff` is that real patch. They must be **equivalent**
   — related only by the type-only refinement you declare in `refinement.md`
   (R/A/I). If a verifying implementation of your spec could be refined to a
   patch that does NOT resolve, your spec/refinement is broken — fix it.
3. **`implementation_<name>` is a faithful SKELETON of the fix.** Its control
   flow and data flow mirror `patch.diff` under the refinement. Use the
   imperative idioms (§2) — `Id.run do` / `let mut` / `for … in` / early
   `return` — so the impl is a line-for-line skeleton of the imperative fix. You
   may NOT model a different algorithm that happens to satisfy a weaker spec.
   (G-EQ checks this; G-DIFF checks the spec sees the bug; G-CONF mechanically
   differential-tests the R/I legs.)
4. **Spec strength: verified ⟹ correct, not just verified ⟹ plausible.** The
   `problem_spec_<name>` predicate must pin the behavior the issue + F2P tests
   demand, strong enough that NO wrong implementation of the modeled behavior can
   satisfy it (G-PANEL attacker 1 will write a wrong impl + a fresh proof and try
   to verify it). Ask: "could an impl satisfy this spec and still fail an F2P
   test?"
5. **Read-only inputs: frame discipline.** Lean is referentially transparent —
   no aliasing, no fractional permission. The frame obligation translates to:
   when the spec relates a result to its inputs, pin the UNCHANGED parts
   explicitly (e.g. if only one field changes, the spec states the others equal
   their input value). A `problem_spec` that leaves an output component
   unconstrained is the analogue of the full-permission hole — a wrong impl can
   put anything there and still verify.
6. **No leakage.** The spec view (`Solution.lean` minus the `impl` region AND the
   `proof` region — INCLUDING module docstring and all comments) is shown to
   consumers. It must not quote any gold-diff line, name the patched
   file/function/line (in identifiers OR comments), use an identifier echoing a
   patched repo symbol, or narrate the bug→fix MECHANISM. State the abstract
   desired behavior; never the edit or the diagnosis. **Leakage is judged against
   the solver-visible `problem_statement` ONLY — NOT `hints_text`.** A term that
   appears only in `hints_text` is not public; echoing it leaks. (Concrete case:
   an axiom comment naming `html.unescape` tripped G-LEAK — write "a
   standard-library HTML entity decoder," not the callee name.) **Exception — relaxed-leakage:** for a proven `problem_statement ↔ gold` mismatch
   where a faithful spec MUST name the discriminator, keep the instance with the
   leak allowed (`meta.json gates.G-LEAK.status = "relaxed"`). Do NOT relax to
   dodge ordinary de-narration.
7. **Axioms are liabilities — the #1 soundness defect is over-claiming.** Each
   `axiom <callee>_prop` is (a) about a real callee the changed function CALLS but
   does NOT change, (b) the WEAKEST contract sufficient for the proof — never
   stronger than the real callee's observed behavior, (c) provenance-cited in
   mapping.md, (d) executable-checkable (G-AX runs the real callee against it).
   NEVER axiomatize the function under spec or the operation the patch changes.
   Declare the callee `opaque <callee> : <type>` (so it can appear in the
   executable impl) and assert only the property the proof consumes via `axiom
   <callee>_prop`. The construction agent declares the `opaque` signature; the
   PROOF agent proposes the `_prop` axioms only when stuck (axiom-propose loop).
   Traps: do not assume a callee never raises unless verified; do not pin exact
   output values the callee only sometimes produces; fuzz sentinels/boundaries
   (NaN, ±inf, empty, max-size) in axiom_check.py.
8. **Ground the postcondition in the inputs — never pin it to an ungrounded
   oracle.** A `problem_spec` must be dischargeable ONLY by the real computation.
   Do NOT equate the result to an opaque answer-key (an axiomatized oracle or a
   hardcoded lookup) — a wrong impl can ECHO it and verify without doing the work.
   Pin behavior with structural predicates on the actual input carrier (length /
   membership / order / element-wise / arithmetic relations) so the result must
   be *produced by* the modeled branch.

## 1. The CLEVER triple: spec / impl / proof

Per modeled function:

```lean
import Mathlib            -- the only front-door import (+ no others; G-HYGIENE)
-- imports-end

-- axioms-start
-- opaque + minimal property for UNCHANGED callees the fix uses (§3, §0.7).
-- The construction agent declares `opaque`; `_prop` axioms come from the proof
-- agent's axiom-propose loop. Comments describe BEHAVIOR, never the callee name.
-- axioms-end

-- pure-start
-- plain functional helpers (front-recursive spec folds, etc.)
-- pure-end

-- post-conditions-start
def problem_spec_<name> (args…) (result : T) : Prop := <logical predicate>
-- post-conditions-end

-- impl-start
def implementation_<name> (args…) : T := Id.run do
  let mut acc := <init>
  for x in xs do
    acc := <update acc x>
  return acc
-- impl-end

-- proof-start
theorem correct_<name> : ∀ args, <preconds> →
    problem_spec_<name> args (implementation_<name> args) := by
  sorry   -- LEFT FOR THE PROOF AGENT — construction agent does NOT close this
-- proof-end
```

- **Preconditions are hypotheses in the `correct_<name>` binder** (`∀ args, P args
  → …`), NOT conjuncts in `problem_spec` — keep the spec a clean input→output
  relation. A `pre-conditions` region is optional (use it only for shared
  precondition `def`s).
- Mandatory marker regions: `axioms`, `pure` (single, module-level);
  `post-conditions`, `impl`, `proof` (repeat once per modeled function). The
  construction agent ships the `proof` region with `:= by sorry`; the proof agent
  replaces the body. (The bundle is NOT green until that sorry is gone —
  G-VERIFY/G-HYGIENE reject `sorry`/`sorryAx`.)
- Keep proof-helper lemmas (generic list/array math) in the `pure` region or
  inside the `proof` region — if they sit in the spec view they must be
  content-neutral (no fix narration, no leaked symbols).

`Solution_prepatch.lean`: byte-identical spec (the gates enforce `same_spec` —
i.e. identical outside the `impl`+`proof` regions); the `impl` body is the
pre-patch (buggy) skeleton, and its `correct_<name>` MUST be unclosable so
verification fails (G-DIFF). Ship the prepatch with the gold proof body carried
over (it will fail to typecheck against the buggy impl) — that is exactly the
signal G-DIFF wants. One `Solution_prepatch_<k>.lean` per independently-fixed
behavior.

### 1.2 patch.diff
The equivalent real patch (gold verbatim is fine, or a behavior-identical
rephrasing). Applies at `base_commit`, makes the harness `resolved` (G-RESOLVE).

### 1.3 refinement.md — the operation correspondence (heart of soundness)
A table mapping every op in `implementation_<name>` to its `patch.diff`
counterpart, tagged **R** (type refinement; state the bijection), **A-consumed**
(proof uses this axiom's property), **A-reference** (deep model validated == real
callee by G-AX), or **I** (identical concrete op). EVERY step is R, A, or I. A
*changed op that needs deep modeling* is modeled deeply (§3), not axiomatized.
The R/I legs are mechanically refuted by G-CONF; A legs + narrative by G-EQ.

## 2. Type modeling + imperative idioms (the cheatsheet)

| repo reality | model as |
|---|---|
| `str`, per-code-point op | `List Char` (Lean indexing is total/sound) |
| `str` value-level | Lean `String`, or `List Char` |
| `list[int]` | `List Int` or `Array Int` (Mathlib `Multiset`/`Finset` as apt) |
| `dict[k,v]` | `Std.HashMap k v` or `List (k × v)` |
| `len(xs)` | `xs.length` (List) / `xs.size` (Array) |
| `float`, order-only fix (sign/zero/tolerance) | exact `Rat`/`Int` — kernel `Float` order is opaque to tactics |
| `float`, genuinely real-valued | Mathlib `Real` (`noncomputable` — keep OUT of the impl; model in spec only) |
| rich object (Matrix/QuerySet/AST) | a Lean `structure` with only the touched fields; bijection in mapping.md |
| exception raised | `Except E` / `Option` return |
| unchanged pure callee | `opaque <callee>` + minimal `axiom <callee>_prop` (§3) |

| Python imperative construct | Lean implementation idiom |
|---|---|
| procedure with local mutable state | `def implementation_<name> … := Id.run do …` |
| `x = …; x = f(x)` | `let mut x := …; x := f x` |
| `for item in xs:` | `for item in xs do …` |
| `for i in range(n):` | `for i in [0:n] do …` |
| `while cond:` | recursive `def` with `termination_by`, or bounded `for` |
| early `return v` | `return v` inside the `do` |
| threaded state | `StateM σ` / `StateT σ Id`, run with `.run init` |

`Id.run do` + `let mut` + `for` is the **preferred** shape (it keeps the impl a
skeleton of the imperative fix, and the proof agent has a validated playbook for
it). Pure functional `def`s (pattern match + `termination_by`) are fine where the
real code is functional.

Banned (G-HYGIENE): imports beyond `Mathlib`/`Std`/Lean core; `sorry`/`admit`/
`sorryAx` in the SHIPPED bundle; `native_decide` in proofs; `unsafe`/`extern`.
(The construction agent's `:= by sorry` placeholder is replaced by the proof
agent BEFORE the bundle is graded — a shipped sorry is a hard fail.)

## 3. Multi-site changes and axioms (the hard cases)

- **Multiple changed functions:** one triple per changed function in the same
  `Solution.lean` (ordered callees-before-callers). If a changed function calls
  another that is ALSO on the fix list, call `implementation_<callee>` directly
  and use `correct_<callee>` in the caller's proof (callee-under-spec, *proved*
  not assumed). G-DIFF needs one failing prepatch per independently-observable
  fixed behavior.
- **Consumed axiom vs deep-model reference.** A changed op modeled DEEPLY
  (spelled out, e.g. an `escapedSeq` fold) makes its callee an **A-reference**
  (validated == real callee by G-AX), NOT a consumed axiom. Do not ship a dead
  `axiom` the proof never uses. Tag each row A-consumed vs A-reference in
  refinement.md.
- **Front-recursive folds.** Pair a front-recursive spec helper
  (`f (c :: cs) = g c ++ f cs`) with an accumulator `for` loop; the proof agent
  proves the loop equals the fold via the proof playbook (prompts/lean/proof_playbook.md) Route B induction
  (generalizing the accumulator, `List.forIn_cons`).
- **Flag-dependent callees** (e.g. `html.escape` is the per-char map only under
  `quote=True`): record the flag dependency in mapping.md so G-AX fuzzes the
  right configuration.
- **Changed op needs deep modeling:** model it deeply (Mathlib `Real`/exact
  `Rat`, an inductive string predicate, a richer captured property). NEVER
  axiomatize the thing that changed. If genuinely impossible, write
  `<benchmark-root>/<id>/lean/BLOCKED.md` (what you tried, the wall, candidate modelings) and
  stop. A principled BLOCKED is valid; a weakened/faked spec is benchmark
  poisoning.

## 4. Workflow & self-check (budget verifier calls)

The construction agent's deliverable is **spec + impl that compile** (proof left
as `sorry`); the proof agent closes it next.

1. `mapping.md` first (forces reading the real code + callees), then the `opaque`
   callee decls, `problem_spec_<name>`, then the skeleton-faithful
   `implementation_<name> := Id.run do …`. Leave `correct_<name> := by sorry`.
2. `bash scripts/lean_verify.sh <benchmark-root>/<id>/lean/Solution.lean` — at this stage it will
   report the `sorry` (exit 3); that is expected. What you confirm now is that
   the spec + impl + theorem STATEMENT elaborate (no type errors). Then run
   `swebench-unified gates --backend lean <id> --static-only` minus G-VERIFY to check
   markers/integrity/leak. ≤8 rounds.
3. Spec-validation: add throwaway `example`s pinning `problem_spec_<name>` to
   concrete F2P input/output values and check they elaborate (`decide`/`rfl`/
   `simp`). Delete them before shipping (they would sit in the spec view).
4. `Solution_prepatch.lean` (buggy impl + carried gold proof) must FAIL G-VERIFY.
   Write `patch.diff`; it must resolve (G-RESOLVE) and a gold-faithful impl
   verify (G-GOLD). Write `axiom_check.py` (G-AX) and `conformance_check.py`
   (G-CONF) correct-by-construction; the orchestrator batches the Docker gates.
   Write `refinement.md` and self-audit against R/A/I.
5. `meta.json`: modeled_functions, axioms (A-consumed) + deep_model_references
   (A-reference), conf_skip (true iff impl region is all-A-tagged), region
   hashes, gate results.

A compile failure is information: read the goal at the unsolved location; fix the
type model or the skeleton. The hard proof obligations are the PROOF agent's job
— do not pre-empt them, but DO make the theorem statement honest (the real
`problem_spec` of the real `implementation`), because the proof agent must close
exactly what you wrote.
