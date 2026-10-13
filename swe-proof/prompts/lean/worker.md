# Construction worker prompt (canonical, vanilla Lean 4 + Mathlib)

Quoted verbatim into each construction subagent's task (with `{iid}` filled).
Edit here; do not fork per instance. **You write the spec + impl only — the
`correct_<name>` proof is closed by a SEPARATE proof agent (prompts/lean/proof_agent.md).**

---

You are constructing a TWIN-ARTIFACT verification bundle for SWE-Bench-Verified
instance **{iid}**. Project root: the repository root. Stack: vanilla
Lean 4 + Mathlib (NO Velvet). Shape: the CLEVER triple
`problem_spec_<name>` / `implementation_<name>` / `theorem correct_<name>`.

## COLD CONSTRUCTION (binding constraint — read before anything)
You derive the specification **from scratch** using ONLY: the
`problem_statement`, the gold `patch`, and the real repo source at
`base_commit`. You must NOT read, search for, copy, or consult any pre-existing
solution to this instance — in particular **do NOT look at any
other backend's bundle for this instance, nor at any pre-existing twin or spec
for it**. Porting an existing solution is forbidden; it confounds what the
dataset demonstrates. The only Lean you may study is the worked shape in
`prompts/lean/proof_playbook.md`, for STRUCTURE only. Record
`spec_provenance: "cold"` in meta.json.

## Read first (binding)
1. `prompts/lean/spec_guide.md` — every rule binds. Especially §0 prime directives
   (verify⟹correct, skeleton-faithful, spec strength, directive 5 frame,
   directive 6 no leakage, directive 7 axioms, directive 8 grounded
   postconditions), §2 type modeling + imperative idioms, §3 multi-site + axioms
   + front-recursive folds.
2. `docs/architecture.md` §5 (the gates that judge you, incl. the agentic G-EQ /
   G-AX / G-PANEL and the mechanical G-CONF cross-language differential test).
3. `{root}/{iid}/instance.json` → `problem_statement` and `patch` (gold).
4. The real source at `base_commit` (the worktree is already materialized for
   you under /tmp — read the changed functions AND their callees).
5. `prompts/lean/proof_playbook.md` — the worked shape (imperative
   `Id.run do … for … mut …` impls + closed `correct_*`). Mirror its structure.

## Produce in `{root}/{iid}/lean/`
- `Solution.lean` — `import Mathlib`, the `axioms` region (`opaque <callee>` decls
  for UNCHANGED callees the fix uses — signatures only; the proof agent adds any
  `_prop` axioms), `pure` helpers, and per changed function:
  `problem_spec_<name> : … → Prop` (post-conditions region), a skeleton-faithful
  `implementation_<name> := Id.run do …` (impl region), and a `theorem
  correct_<name> : ∀ args, <preconds> → problem_spec_<name> args
  (implementation_<name> args) := by sorry` (proof region — LEAVE the `sorry`,
  the proof agent closes it). All marker regions mandatory.
- `Solution_prepatch.lean` (+ `_<k>` per independently-fixed behavior) —
  byte-identical spec (identical outside impl+proof regions), pre-patch buggy
  `impl` skeleton, the gold proof body carried over (so it fails to typecheck);
  MUST fail G-VERIFY (G-DIFF).
- `patch.diff` — the equivalent real patch (gold verbatim is fine); applies at
  base_commit and resolves.
- `refinement.md` — every impl op ↔ patch.diff op, tagged
  R / A-consumed / A-reference / I. No changed-inexpressible op (model deeply).
- `mapping.md` — symbol binding (file:line @ base_commit), the Lean↔Python type
  bijection (G-CONF + G-AX use it), callee provenance + flag deps, and the
  pinned G-CONF fuzz seed.
- `axiom_check.py` (G-AX) — runs each REAL callee in-container on boundary +
  fuzz, asserts every observation meets the axiom's property. stdlib-only;
  exit 0 iff sound. (If the proof needs no callee axiom, this may be a skip stub.)
- `conformance_check.py` (G-CONF) — builds the R/I shadow of the impl in Python
  (A-tagged callees left as the real repo callee), bridges I/O via mapping.md,
  diffs against patch.diff behaviour over ≥10⁵ fuzzed inputs; exit 0 iff zero
  disagreements. If the impl region is all-A-tagged, set `meta.json conf_skip=true`
  and write a stub that exits with `status=skip`.
- `meta.json` — modeled_functions, axioms (A-consumed), deep_model_references
  (A-reference), conf_skip, region hashes, gate map, verifier pins.

## Hard rules (the ones that bite)
- **Write the HONEST theorem.** `correct_<name>` must state the real
  `problem_spec` of the real `implementation` (with the genuine preconditions as
  binders). The proof agent must be able to close EXACTLY what you wrote — do not
  weaken the statement to make the proof trivial, and do not strengthen it beyond
  the fix.
- **Verify⟹correct:** the spec pins behavior so tightly no wrong impl verifies.
  G-PANEL attacker (1) writes a wrong impl AND a fresh proof against your frozen
  spec; the prepatch (the actual bug) must be unprovable on the discriminating
  clause.
- **Directive 5 (frame):** pin every unchanged output component to its input in
  `problem_spec`; an unconstrained result component is a hole a wrong impl fills.
- **No dead axioms:** a deeply-modeled changed op's callee is an A-reference
  (G-AX-checked), not a consumed axiom.
- **Imperative skeleton:** use `Id.run do`/`let mut`/`for`/early-`return` — match
  the real fix's control flow, not a re-imagined functional algorithm.
- **No leakage:** spec view (impl + proof regions elided) names no patched
  path/symbol/diff line/narration; comments describe behavior, not the edit
  (the `html.unescape` lesson).
- **Banned:** imports beyond `Mathlib`/`Std`/Lean core; `admit`/`sorryAx`;
  `native_decide`/`unsafe`/`extern`. (A `:= by sorry` placeholder in the proof
  region is the ONE permitted sorry, and only until the proof agent runs.)

## Self-check loop (≤8 rounds)
```
bash scripts/lean_verify.sh {root}/{iid}/lean/Solution.lean         # expect exit 3 (sorry) — confirms spec+impl+stmt elaborate
swebench-unified gates --backend lean {iid} --gates G-INTEGRITY G-HYGIENE G-LEAK
```
At construction time the proof is `sorry`, so G-VERIFY/full static will not pass
yet — that is expected. What you confirm: no TYPE errors (only the sorry), and
markers/integrity/leak clean. NEVER weaken a contract. If genuinely blocked by
the type model, write `{root}/{iid}/lean/BLOCKED.md`. Do NOT run the Docker gates
yourself — the orchestrator batches them.

## Final message = structured report
status (green|blocked); spec/impl elaborate (only sorry remains); modeled
functions; opaque callees declared + intended A-consumed vs A-reference; the
refinement.md tags; how you handled the hard subtlety; confirmation the prepatch
impl is the real bug; whether patch.diff == gold; the meta.json gates block.
If blocked, the precise wall.
