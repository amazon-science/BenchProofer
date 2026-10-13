# Proof-agent prompt (canonical, vanilla Lean 4 + Mathlib)

Quoted into each proof subagent's task (with `{iid}` filled). Your ONLY job: close every
`theorem correct_<name>` in `{root}/{iid}/lean/Solution.lean` with real Lean tactics —
no `sorry`, no `admit`, no `native_decide`.

---

You are closing the correctness proofs for SWE-Bench-Verified instance **{iid}**.
Project root: the repository root. The construction agent already wrote
the spec (`problem_spec_<name>`) and the imperative implementation
(`implementation_<name> := Id.run do …`), and left each `theorem correct_<name>
… := by sorry`. Replace every `sorry` with a genuine proof.

## Hard rules
- **Do NOT modify `problem_spec_<name>` or `implementation_<name>`** — only the
  `proof` region (the `correct_<name>` tactic body) and, when the
  axiom-propose loop authorizes it, the `axioms` region. If you believe the spec
  or impl is wrong (the theorem is FALSE), STOP and return `fail` with the reason
  — do not patch around it. The orchestrator bounces it back to construction.
- **No `sorry`/`admit`/`native_decide`.** The bundle is graded by `#print axioms
  correct_<name>`; a `sorryAx` is an automatic reject. Allowed axioms: `propext`,
  `Classical.choice`, `Quot.sound`, plus any bundle-declared `axiom <callee>_prop`.
- **Discover lemma names — never guess.** Use `exact?`, `apply?`, `simp?`,
  `rw?`, and `loogle`/Mathlib search. The PROOF_PLAYBOOK lists names that exist
  here and names that do NOT.

## Recipe (binding — full detail in the proof playbook, appended below)
For an `Id.run do let mut acc := init; for x in xs do acc := upd; return acc`:
- **Route A (plain accumulation, no branch in body):** `unfold
  implementation_<name>; simp [List.range_eq_range']` reduces the loop to a
  `List.foldl`/`Finset.range` fold; finish with the closed-form Mathlib lemma.
- **Route B (conditional body — the general case):**
  1. State a helper lemma about the CLEANED `forIn` form, **generalized over the
     accumulator**: `Id.run (forIn xs init (fun x r => if cond then .yield … else
     .yield …)) = <foldl spec>`.
  2. Prove by `induction xs generalizing init with | nil => rfl | cons a as ih =>
     rw [List.forIn_cons]; simp only [Id.run, bind] at ih ⊢; by_cases h : cond
     <;> simp only [h, …, ih]`.
  3. In `correct_<name>`, bridge the DESUGARED body (`do pure PUnit.unit; pure
     (ForInStep.yield …)`) to the helper's clean body via `have h2 : … = … :=
     rfl`, then `rw [h2, helper]`. Strip an early-`return` guard with `simp only
     [Id.run, h, if_false]`.
- Discovery: `simp only [Id.run]; trace_state` prints the exact desugared goal —
  use it to write the matching `rfl` bridge.

## When a proof will not close
1. Try harder first: more tactic effort (`omega`/`ring`/explicit `induction` +
   the fold lemmas), `exact?`/`simp?` to find the missing Mathlib lemma.
2. If the gap is a property of an UNCHANGED dependency callee, return `stuck`
   with the exact goal state + the property you need. The orchestrator runs the
   axiom-propose loop: it adds a minimal `opaque <callee>` + `axiom
   <callee>_prop` (validated against PASS_TO_PASS by G-AX) and re-invokes you.
   NEVER axiomatize the function being fixed.
3. If the theorem is genuinely FALSE (spec/impl bug), return `fail` (→ bounce to
   construction).
4. If genuinely unprovable in reasonable effort, the orchestrator marks the
   bundle BLOCKED. A hard proof is BLOCKED for that bundle, never a `sorry`.

## Self-check loop
```
bash scripts/lean_verify.sh {root}/{iid}/lean/Solution.lean        # exit 0 = compiles, no sorry
grep -nE '\bsorry\b|\badmit\b' {root}/{iid}/lean/Solution.lean      # expect nothing
# append `#print axioms correct_<name>` and confirm no sorryAx:
swebench-unified gates --backend lean {iid} --gates G-VERIFY
```

## Final message = structured report
status (`ok` | `stuck` | `fail` — `ok` = every correct_<name> closed); the
`correct_<name>` theorems you closed;
if stuck, the goal state + the needed callee property; notes on the proof
strategy used (Route A/B, key lemmas).

---
# PROOF_PLAYBOOK.md (binding recipe)

# PROOF_PLAYBOOK — proving vanilla-Lean imperative implementations correct

Binding reference for the **proof-writing agent**: the proof-generation step,
which runs separately from spec construction so a stuck proof can be retried
without disturbing a spec that already gates clean. Tactic advice below is for
Mathlib on the toolchain pinned in `lean_shared/PINS.md`. A finished imperative impl has
every `correct_*` closed and `#print axioms` showing only
`propext`/`Classical.choice`/`Quot.sound`, never `sorryAx`.

## The artifact shape (vanilla Lean 4, NO Velvet)

```lean
import Mathlib

def problem_spec_<name> (args...) (result : T) : Prop := <logical predicate>

def implementation_<name> (args...) : T := Id.run do      -- IMPERATIVE style
  let mut acc := <init>
  for x in xs do
    acc := <update acc x>            -- may contain if/conditionals
  return acc

theorem correct_<name> : ∀ args, problem_spec_<name> args (implementation_<name> args) := by
  ...                                 -- closed by the recipe below, NO sorry
```

Implementations SHOULD use the imperative monadic structures (`Id.run`, `do`,
`let mut`, `for … in`, `StateM`) — they desugar to `List.forIn`/`Std.Range.forIn`
and remain fully provable. This keeps the impl a faithful skeleton of the real
imperative Python fix.

## Recipe — converting `Id.run do let mut acc; for x in xs do …; return acc`

### Route A — plain accumulation (no conditional in the loop body)
`unfold implementation_<name>; simp [List.range_eq_range']` reduces the whole
`Id.run do for [0:n] …` directly to `List.foldl (·+·) 0 (List.range n)`. `simp`
already knows the `Std.Range.forIn` + `Id.run` + `mut` desugaring — do NOT cite
`Std.Range.forIn_eq_forIn_range'` etc. explicitly (triggers unused-simp-arg
linter). Then finish with the relevant closed-form lemma (e.g.
`Finset.sum_range_id_mul_two : (∑ i ∈ Finset.range n, i) * 2 = n * (n - 1)`).

### Route B — conditional loop body (`if`/branch update; the general playbook)
1. State a standalone helper lemma about the **cleaned** `forIn` form,
   **generalized over the accumulator**:
   `Id.run (forIn xs init (fun x r => (if cond then .yield … else .yield …))) = <foldl spec>`.
2. Prove it by `induction xs generalizing init with`
   `| nil => rfl`
   `| cons a as ih => rw [List.forIn_cons]; simp only [Id.run, bind] at ih ⊢; by_cases h : cond <;> simp only [h, if_true, if_false, ih]` (+ `List.foldl_cons`/`List.filter_cons` on the RHS).
3. In `correct_<name>`, bridge the *desugared* loop body (contains
   `do pure PUnit.unit; pure (ForInStep.yield …)`) to the helper's *clean* body
   via `have h2 : … = … := rfl` (definitionally equal), then `rw [h2, helper]`.
   For an early-`return` guard (`if xs = [] then return 0`), strip it with
   `simp only [Id.run, h, if_false]` given the hypothesis.

### Discovery aids
- `simp only [Id.run]; trace_state` prints the exact desugared `forIn` goal —
  use it to write the matching `rfl` bridge.
- Use `exact?`, `apply?`, `simp?` to find real lemma names. DON'T guess.

## Lemma names that ACTUALLY EXIST here (verified)
- `List.forIn_cons`, `List.forIn_nil` — the monadic loop unfolders (workhorses)
- `List.foldl_cons`, `List.filter_cons`, `List.range_succ`, `List.range_eq_range'`,
  `List.sum_append`, `List.sum_eq_foldl`, `List.length_cons`
- `Finset.sum_range_succ`, `Finset.sum_range_id_mul_two`
- `List.mem_cons`, `List.mem_cons_self`, `List.mem_cons_of_mem`, `List.not_mem_nil`

## Names that do NOT exist (do not use)
- `Finset.sum_range_id_eq_choose`, `Gauss_sum`, `List.foldl_eq_sum`,
  `List.forIn_eq_foldl`, `range'_eq_range`
- Deprecated: `List.forIn_yield_eq_foldl` (→ `List.idRun_forIn_yield_eq_foldl`),
  `Id.bind_eq`/`Id.pure_eq` (→ `Id.run_bind`/`Id.run_pure`; or just
  `simp only [Id.run, bind]`).

## When a proof genuinely won't close
Return `stuck` with the goal state + the needed property. Reporting the open goal
is strictly better than closing it unsoundly, because a `sorry` would make the
gate green while proving nothing.The orchestrator may then run an axiom-propose/validate loop
(assert a minimal property of an **unchanged dependency** callee, validated
against PASS_TO_PASS — never axiomatize the changed function). A `sorry` is never
acceptable. If the spec/impl is itself wrong, return `fail` for refinement.
