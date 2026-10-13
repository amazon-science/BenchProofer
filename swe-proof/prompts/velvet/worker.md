# Construction worker prompt (canonical, Lean 4 + Velvet twin-artifact)

Quoted verbatim into each construction subagent's task (with `{iid}` filled).
Edit here; do not fork per instance.

---

You are constructing a TWIN-ARTIFACT verification bundle for SWE-Bench-Verified
instance **{iid}**. Project root: the repository root.

## COLD CONSTRUCTION (binding constraint — read before anything)
You derive the specification **from scratch** using ONLY: the
`problem_statement`, the gold `patch`, and the real repo source at
`base_commit`. You must NOT read, search for, copy, or consult any pre-existing
solution to this instance — in particular **do NOT look at any
other backend's bundle for this instance, nor at any pre-existing twin or spec
for it**. Porting an existing solution is forbidden; it confounds what the
dataset demonstrates. The only Lean bundle you may study is the in-repo style
exemplar (item 5 below), for STRUCTURE only. Record `spec_provenance: "cold"`
in meta.json.

## Read first (binding)
1. `prompts/velvet/spec_guide.md` — every rule binds. Especially §0 prime directives
   (verify⟹correct, skeleton-faithful, spec strength, directive 5 `mut`-frame,
   directive 6 no leakage, directive 7 axioms), §2 type modeling (the
   Nagini→Velvet cheatsheet), §3 multi-site + axioms + front-recursive folds +
   the `:|` imperative-callee stub + A-consumed vs A-reference.
2. `docs/architecture.md` §5 (the gates that judge you, incl. the agentic G-EQ /
   G-AX / G-PANEL and the mechanical G-CONF cross-language differential test).
3. `{root}/{iid}/instance.json` → `problem_statement` and `patch` (gold).
4. The real source at `base_commit` (worktree:
   `git -C repos/<repo>.git worktree add /tmp/{iid}_wt <base_commit>`; read the
   changed functions AND their callees; remove the worktree when done).
5. The reference exemplar `benchmark-verified/django__django-11276/velvet/` — a fully-green
   multi-site + axiom + front-recursive-fold bundle. Mirror its structure.

## Produce in `{root}/{iid}/velvet/`
- `Solution.lean` — `import Velvet.Std`, the semantics `set_option`s, axioms for
  UNCHANGED callees, `pure` helpers, one `method` per changed function with
  `require`/`ensures`/`invariant`/`decreasing` + a skeleton-faithful `do` block,
  and `prove_correct <name> by loom_solve [...]`. Marker regions mandatory.
- `Solution_prepatch.lean` (+ `_<k>` per independently-fixed behavior) —
  byte-identical spec, pre-patch buggy skeleton; MUST fail G-VERIFY.
- `patch.diff` — the equivalent real patch (gold verbatim is fine); applies at
  base_commit and resolves.
- `refinement.md` — every `do`-block op ↔ patch.diff op, tagged
  R / A-consumed / A-reference / I. No kind-3 (changed inexpressible op).
- `mapping.md` — symbol binding (file:line @ base_commit), the Lean↔Python type
  bijection (G-CONF + G-AX use it), callee provenance + flag deps, and the
  pinned G-CONF fuzz seed.
- `axiom_check.py` (G-AX) — runs each REAL callee in-container on boundary +
  fuzz, asserts every observation meets the axiom's `ensures` (and any
  A-reference deep model == its real callee). stdlib-only; exit 0 iff sound.
- `conformance_check.py` (G-CONF) — builds the R/I shadow of the `do` block in
  Python (A-tagged callees left as the real repo callee), bridges I/O via
  mapping.md, diffs against patch.diff behaviour over ≥10⁵ fuzzed inputs; exit 0
  iff zero disagreements. If the impl region is all-A-tagged, set
  `meta.json conf_skip=true` and write a stub that exits with `status=skip`.
- `meta.json` — modeled_functions, axioms (A-consumed), deep_model_references
  (A-reference), conf_skip, region hashes, gate map, verifier pins.

## Hard rules (the ones that bite)
- **Verify⟹correct:** the spec pins behavior so tightly no wrong impl verifies.
  G-EQ throws wrong-impls at your frozen spec; the prepatch (the actual bug)
  must fail on the discriminating clause.
- **Directive 5 (`mut`-frame):** don't mark a read-only param `mut`; if a `mut`
  param is unchanged, `ensures xOld = x`. Lean has no aliasing, but an
  unconstrained `mut` is the analogue of the full-permission hole.
- **No dead axioms:** a deeply-modeled changed op's callee is an A-reference
  (G-AX-checked), not a consumed axiom.
- **Front-recursive folds + one drop-step lemma** for
  "result is the per-element expansion of the input."
- **No leakage:** spec view names no patched path/symbol/diff line/narration;
  comments describe behavior, not the edit (the `html.unescape` lesson).
- **Banned:** early return inside a loop; `else if` (nest / `let … := if …`);
  `for` loops; `sorry`/`admit`/`Classical.choice`/`native_decide`; imports
  beyond `Velvet.Std` + listed `Mathlib.*`.

## Self-check loop (≤8 verify rounds)
```
bash scripts/lean_verify.sh {root}/{iid}/velvet/Solution.lean            # G-VERIFY (exit 0)
bash scripts/lean_verify.sh {root}/{iid}/velvet/Solution_prepatch.lean   # G-DIFF: must be non-zero
swebench-unified gates --backend velvet {iid} --static-only
```
The verify script enforces a 300s timeout (exit 124 = simplify / switch to
`loom_smt [hints]`, don't pile on tactics). NEVER weaken a contract. If
genuinely blocked by Velvet's fragment, write `{root}/{iid}/velvet/BLOCKED.md`. Do NOT
run the Docker gates (G-RESOLVE/G-CONF/G-AX) yourself — the orchestrator batches
them; make patch.diff + axiom_check.py + conformance_check.py correct by
construction.

## Final message = structured report
status (green|blocked); static-gate outcomes + verify times; modeled functions;
axioms (A-consumed) + deep-model references (A-reference) + provenance; the
refinement.md tags; how you handled the hard subtlety; confirmation the prepatch
fails on the right clause; whether patch.diff == gold; the meta.json gates block.
If blocked, the precise wall.
