# SPEC_GUIDE — binding rules for a Lean 4 + Velvet twin-artifact bundle

*Normative. Every construction agent follows every rule. The gates (docs/architecture.md §5)
enforce them; the agentic gates (G-EQ, G-AX, G-PANEL) are adversarial and will
actively try to break your bundle. This is the Lean+Velvet transliteration of
the Nagini SPEC_GUIDE.*

You are given one SWE-Bench-Verified instance: a repo worktree at `base_commit`,
the problem statement, the gold `patch`, the `test_patch`, and the FAIL_TO_PASS /
PASS_TO_PASS lists. You produce, in `<benchmark-root>/<id>/velvet/`: `Solution.lean`,
`Solution_prepatch.lean`, `patch.diff`, `refinement.md`, `mapping.md`,
`axiom_check.py`, `conformance_check.py`, `meta.json`.

The fully-green exemplar is `benchmark-verified/django__django-11276/velvet/` — mirror it.

## 0. Prime directives

1. **Never change the task.** Add files only; never edit `instance.json`, repo
   files (except via `patch.diff`, which equals/rephrases the gold), tests, or
   the problem statement. (G-INTEGRITY.)
2. **The guarantee is `verify ⟹ correct`.** "correct" = the official harness
   reports `resolved`. Your `Solution.lean` is the verifiable face of a real
   patch; your `patch.diff` is that real patch. They must be **equivalent** —
   related only by the type-only refinement you declare in `refinement.md`
   (R/A/I). If a verifying implementation of your spec could be refined to a
   patch that does NOT resolve, your spec/refinement is broken — fix it.
3. **`Solution.lean`'s `do` block is a faithful SKELETON of the fix.** Its
   control flow and data flow mirror `patch.diff` under the refinement. You may
   NOT model a different algorithm that happens to satisfy a weaker spec.
   (G-EQ checks this; G-DIFF checks the spec sees the bug; G-CONF mechanically
   differential-tests the R/I legs.)
4. **Spec strength: verified ⟹ correct, not just verified ⟹ plausible.** The
   `ensures` clauses must pin the behavior the issue + F2P tests demand, strong
   enough that NO wrong implementation of the modeled behavior can satisfy it
   (G-PANEL attacker 1 will try to find one). Ask: "could an impl satisfy this
   spec and still fail an F2P test?"
5. **Read-only inputs: `mut`-frame discipline.** Lean is functional — there is
   no aliasing and no fractional permission. The directive-5 obligation
   translates to: a parameter the operation does NOT mutate must NOT be declared
   `mut`; and if a `mut` parameter is conceptually unchanged, you must
   `ensures xOld = x` (state the post-state exactly). A postcondition that
   refers to a value the impl could have silently overwritten is the Lean
   analogue of the full-permission hole — pin the unchanged frame explicitly.
6. **No leakage.** The spec view (`Solution.lean` minus the `impl` `do` block
   and the `prove_correct` body — INCLUDING module docstring and all comments)
   is shown to consumers. It must not quote any gold-diff line, name the patched
   file/function/line (in identifiers OR comments), use an identifier echoing a
   patched repo symbol, or narrate the bug→fix MECHANISM. State the abstract
   desired behavior; never the edit or the diagnosis. **Leakage is judged
   against the solver-visible `problem_statement` ONLY — NOT `hints_text`.** A
   term that appears only in `hints_text` is not public; echoing it leaks.
   (Concrete case: an axiom comment naming `html.unescape` tripped G-LEAK —
   write "a standard-library HTML entity decoder," not the callee name.) **Exception —
   relaxed-leakage:** for a proven `problem_statement
   ↔ gold` mismatch where a faithful spec MUST name the discriminator, keep the
   instance with the leak allowed (`meta.json gates.G-LEAK.status = "relaxed"`).
   Do NOT relax to dodge ordinary de-narration.
7. **Axioms are liabilities — the #1 soundness defect is over-claiming.** Each
   `axiom` (or `:|`-stub Velvet method, §3) is (a) about a real callee the
   changed function CALLS but does NOT change, (b) the WEAKEST contract
   sufficient for the proof — never stronger than the real callee's observed
   behavior, (c) provenance-cited in mapping.md, (d) executable-checkable (G-AX
   runs the real callee against it). NEVER axiomatize the function under spec.
   **The operation the patch changes MAY be axiomatized as an oracle ONLY when it
   is a self-contained library routine the changed function delegates to** (e.g. a
   stdlib renderer, or a library call whose argument the patch alters) — provided
   the oracle is the weakest sufficient contract, its properties are validated
   executably by G-AX against the real callee (incl. that the prepatch genuinely
   fails), and the discriminating postcondition is grounded per directive 8. If
   the changed op is expressible in the fragment, model it deeply instead — only
   reach for the oracle when a deep model is genuinely impossible. Traps: do not assume a callee never raises
   unless verified; do not pin exact output values the callee only sometimes
   produces; fuzz sentinels/boundaries (NaN, ±inf, empty, max-size); in
   axiom_check.py, never double-mask (assert the equivalence at the level the
   axiom claims it).
8. **Ground the postcondition in the inputs — never pin it to an ungrounded
   oracle.** A postcondition must be dischargeable ONLY by the real computation.
   Do NOT write `ensures` that equate the result to an opaque answer-key (an
   axiomatized oracle or a hardcoded lookup) — a wrong impl can ECHO it and
   verify without doing the work. Pin behavior with structural predicates on the
   actual input carrier (length / membership / order / element-wise / arithmetic
   relations) so the result must be *produced by* the modeled branch.
9. **Irreversible side effects with no value footprint are out of fragment.**
   A fix whose discriminator is an IRREVERSIBLE side effect that leaves NO trace
   on any value the spec can force the impl to return (canonical: "test
   discovery must not import a package's `__init__.py`" — the import runs
   top-level code irreversibly, yet discovery returns the same gathered entries
   whether or not it fired) is NOT soundly specifiable in the current fragment.
   Velvet's final-state WP has no pre-state `Old`/framed-heap primitive, so any
   modeled counter/flag is a freely-written output: a wrong impl fires the
   effect in a throwaway local and returns the clean value, satisfying the spec
   (the directive-4 hole). An "instrumented sole-channel callee" does NOT rescue
   it: forcing the impl through the channel requires a downstream value
   obtainable ONLY via the effect, but for these cases the returned result is
   (by the nature of the fix) computable WITHOUT the effect — so the channel is
   unenforceable and inventing a synthetic effect-product to force it is
   laundering (specifies a different algorithm than gold, directive 3). Disposition:
   principled BLOCK with a `BLOCKED.md` naming the missing primitive (pre-state /
   framed-effect tracking). This is a genuine logic-fragment limit, not a
   modeling-effort gap; do not paper over it with a resettable counter.

## 1. The twin: Solution.lean, patch.diff, refinement.md

### 1.1 Solution.lean skeleton
Imports limited to `Velvet.Std` (the front door) and, if needed, specific
`Mathlib.*` subdirectories listed in mapping.md. Begin with:

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"   -- or "total" (+ decreasing)
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice
```

Mandatory marker regions (machine-parsed, `-- <name>-start` / `-- <name>-end`):
`axioms`, `pure`, `pre-conditions`, `post-conditions`, `invariants`, `impl`.
`axioms`/`pure` are single module-level regions; `pre-conditions`/
`post-conditions`/`invariants`/`impl` REPEAT once per modeled `method`.

The spec lives in the `method`'s `require`/`ensures`/`decreasing` clauses; the
`impl` markers wrap the `do` block; the proof is `prove_correct <name> by ...`.
Keep proof-helper lemmas (generic list/array math) BEFORE the `method` or after
`prove_correct` — they appear in the spec view, so they must be content-neutral
(no fix narration, no leaked symbols).

`Solution_prepatch.lean`: byte-identical spec (the gates enforce `same_spec`);
the `do` block is the pre-patch (buggy) skeleton; `prove_correct` MUST fail
(G-DIFF). One `Solution_prepatch_<k>.lean` per independently-fixed behavior.

### 1.2 patch.diff
The equivalent real patch (gold verbatim is fine, or a behavior-identical
rephrasing). Applies at `base_commit`, makes the harness `resolved` (G-RESOLVE).

### 1.3 refinement.md — the operation correspondence (heart of soundness)
A table mapping every op in the `do` block to its `patch.diff` counterpart,
tagged **R** (type refinement; state the bijection), **A-consumed** (proof uses
this axiom's `ensures`), **A-reference** (deep model validated == real callee by
G-AX), or **I** (identical concrete op). EVERY step is R, A, or I. A *changed op
Velvet cannot express* is FORBIDDEN here — model it deeply (§3). The R/I legs
are mechanically refuted by G-CONF; A legs + narrative by G-EQ.

## 2. Type modeling (the Nagini→Velvet cheatsheet)

| repo reality | model as |
|---|---|
| `str`, per-code-point op | `List Char` (Lean indexing is total/sound — no `List[int]` workaround) |
| `str` value-level | Lean `String` directly, or `List Char` |
| `list[int]` | `Array Int` or `List Int` (Mathlib `Vector`/`Multiset` as apt) |
| `dict[k,v]` | `Std.HashMap k v` or `List (k × v)` |
| `len(xs)` | `xs.size` (Array) / `xs.length` (List) |
| `float`, precision IS the behavior | Mathlib `Real` (exact) or Lean `Float` (IEEE-754, SMT-modeled via `loom_smt`) |
| rich object (Matrix/QuerySet/AST) | a Lean `structure` with only the touched fields; bijection in mapping.md |
| exception raised | `Except E` return, or a structure tagged with the exception kind |
| unchanged pure callee in `ensures` | `axiom callee : ...` (Lean defs are pure) |
| unchanged imperative callee | Velvet `method ... do let r :| <ensures>; return r` (§3) |
| `Requires`/`Ensures`/`Invariant` | `require` / `ensures` / `invariant` clauses |

Banned/unsupported (measured on the pinned Velvet): early return inside a loop;
`else if` (nest, or use a `let e := if … then … else …` ladder); `for` loops
(use `while`); side effects beyond `VelvetM` mutation.

## 3. Multi-site changes and axioms (the hard cases)

- **Multiple changed functions:** one `method` per changed function in the same
  `Solution.lean`; per-method regions repeat. If a changed function calls
  another that is ALSO on the fix list, call it via `let r ← calleeMethod args`
  — `prove_correct` generates `<callee>_correct` so the caller's proof applies
  it directly (callee-under-spec, better than an axiom). G-DIFF needs one
  failing prepatch per independently-observable fixed behavior.
- **Consumed axiom vs deep-model reference.** A changed op modeled DEEPLY
  (spelled out, e.g. the `escapedSeq` fold) makes its callee an **A-reference**
  (validated == real callee by G-AX), NOT a consumed axiom. Do not ship a dead
  `axiom` the proof never uses and claim it's load-bearing. Tag each row
  A-consumed vs A-reference in refinement.md.
- **Front-recursive folds (measured).** `loom_solve` does not auto-unfold an
  index-recursive fold; write `f : List T → U` front-recursively
  (`f (c :: cs) = g c ++ f cs`), pair it with a backward `while` loop that
  prepends, and supply ONE drop-step lemma (`List.drop_eq_getElem_cons`) so
  `prove_correct M by loom_solve; rw [step ...]; simp_all` closes.
- **Imperative-callee stub (`:|`).** For an unchanged imperative callee:
  ```lean
  method calleeStub (args) return (r : Ret)
    require ...
    ensures ...
    do let r :| <the ensures predicate>; return r
  ```
  Sound by construction; `prove_correct` is discharged by `loom_solve`.
- **Flag-dependent callees** (e.g. `html.escape` is the per-char map only under
  `quote=True`): record the flag dependency in mapping.md so G-AX fuzzes the
  right configuration.
- **Changed op inexpressible:** model it deeply (Mathlib `Real`, an inductive
  string predicate, a richer axiom capturing the CHANGED property). If genuinely
  impossible, write `<benchmark-root>/<id>/velvet/BLOCKED.md` (what you tried, the wall, candidate
  modelings) and stop. A principled BLOCKED is valid; a weakened/faked spec is
  benchmark poisoning.

## 4. Workflow & self-check (budget verifier calls)

1. mapping.md first (forces reading the real code + callees), then axioms,
   contracts, skeleton `do` block, `prove_correct` annotations.
2. `bash scripts/lean_verify.sh <benchmark-root>/<id>/velvet/Solution.lean` (G-VERIFY). Fix proof
   annotations on failure — never weaken a contract. The script enforces a 300s
   timeout (exit 124 = simplify the model / try `loom_smt` + `solverHint`, do
   not pile on tactics). ≤8 rounds.
3. `Solution_prepatch.lean` must FAIL (G-DIFF). Write `patch.diff`; confirm it
   resolves (G-RESOLVE) and a gold-faithful impl verifies (G-GOLD). Write
   `axiom_check.py` (G-AX) and `conformance_check.py` (G-CONF) — make them
   correct by construction; the orchestrator batches the Docker gates. Write
   `refinement.md` and self-audit against R/A/I before the panel.
4. `meta.json`: modeled_functions, axioms (A-consumed) + deep_model_references
   (A-reference), conf_skip (true iff impl region is all-A-tagged), verify
   wall-times, frozen-spec region hashes, gate results.

A verification failure is information: read the goal at the unsolved location;
strengthen invariants or fix the skeleton. If a genuinely-required contract is
unprovable in Velvet's logic, that is BLOCKED, not a license to delete it.
