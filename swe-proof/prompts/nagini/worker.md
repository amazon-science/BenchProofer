# Construction worker prompt (canonical, v2 twin-artifact)

Quoted verbatim into each construction subagent's task (with `{iid}` filled).
Edit here; do not fork per instance.

---

You are constructing a TWIN-ARTIFACT verification bundle for SWE-Bench-Verified
instance **{iid}**. Project root: the repository root.

## Read first (binding)
1. `prompts/nagini/spec_guide.md` — every rule binds. Especially: §0 prime directives
   (verify⟹correct, skeleton-faithful, spec strength, **directive 5 fractional
   read-only permission**, **directive 6 no leakage**, directive 7 axioms);
   §1 the twin (model.py / patch.diff / refinement.md); §2 type modeling
   (str→List[int]/PSeq, floats via --float-encoding); §3 multi-site + axioms +
   the **A-consumed vs A-reference** distinction + the **front-recursive fold**
   pattern.
2. `docs/architecture.md` §5 (the gates that will judge you, incl. the agentic
   G-EQ / G-AX / G-PANEL — adversarial reviewers WILL try to break your bundle).
3. `{root}/{iid}/instance.json` → `problem_statement` and `patch` (the gold).
4. The real source at `base_commit` (materialize a worktree:
   `git -C repos/<repo>.git worktree add /tmp/{iid}_wt <base_commit>`; read the
   changed functions AND their callees; remove the worktree when done).
5. The reference exemplar `benchmark-verified/django__django-11276/nagini/` — a fully-green
   multi-site + axiom bundle. Mirror its structure.

## Produce in `{root}/{iid}/nagini/`
- `model.py` — spec (Requires/Ensures) + `@ContractOnly` axioms for UNCHANGED
  callees + a verified SKELETON-FAITHFUL impl. Multiple changed functions →
  multiple contracted functions (per-function pre/post/impl/invariants regions
  REPEAT; axioms/pure are single module-level regions). Marker regions
  mandatory.
- `model_prepatch.py` (+ `model_prepatch_<k>.py` per independently-fixed
  behavior) — byte-identical spec, pre-patch buggy skeleton; MUST fail G-VERIFY.
- `patch.diff` — the equivalent real patch (the gold patch verbatim is fine);
  MUST apply at base_commit and resolve the harness.
- `refinement.md` — every model-impl op ↔ patch.diff op, tagged R (type
  refinement) / A-consumed (proof uses this axiom) / A-reference (deep model
  validated == real callee by G-AX, NOT consumed) / I (identical). No kind-3
  (a changed inexpressible op) — model those deeply instead.
- `mapping.md` — model↔repo symbol binding (file:line at base_commit), type
  abstraction, callee provenance (file:line + doc/source evidence + any flag
  dependency like html.escape's quote=True).
- `axiom_check.py` — for G-AX: generates inputs satisfying each axiom's
  Requires (boundary + fuzz), runs the REAL callee in-container, asserts every
  observation meets the Ensures. Also validates any A-reference deep model ==
  its real callee. stdlib-only imports; exit 0 iff sound.
- `conformance_check.py` — for G-CONF: embeds the impl region of `model.py`
  with contracts stripped (the model IS Python — copy the impl verbatim, no
  transliteration; `@ContractOnly` callees call the REAL repo function),
  bridges any type simplifications from mapping.md, applies patch.diff, and
  diffs the shadow against the patched repo function over ≥10⁵
  Requires-satisfying inputs (boundary + fuzz, pinned seed recorded in
  mapping.md); exit 0 iff zero disagreements. stdlib + hypothesis only. If
  the impl region has no directly-executable content, set
  `meta.json conf_skip=true` and write a stub that exits with `status=skip`.
- `meta.json` — modeled_functions, axioms (A-consumed only), deep_model_
  references (A-reference), float_encoding (if any), conf_skip, region hashes,
  gate map.

## Hard rules (the ones that bite)
- **Verify⟹correct:** the spec must pin behavior so tightly that no wrong impl
  of the modeled behavior verifies. G-EQ will throw ≥8 wrong-impls at your
  frozen spec; the prepatch (the actual bug) must fail on the discriminating
  clause.
- **Directive 5:** read-only inputs at `Acc(list_pred(x), 1/2)` (Required AND
  Ensured). A full-permission read-only input referenced in a postcondition
  lets a wrong impl overwrite it and verify vacuously — G-EQ's mutation attack
  will find it.
- **No dead axioms:** if you model a changed op deeply, the callee is an
  A-reference (G-AX-checked), not a consumed axiom. Don't ship a `@ContractOnly`
  the proof never uses and claim it's load-bearing.
- **Front-recursive folds:** index-recursion doesn't auto-unfold in Nagini
  1.2.0; use `f(s) == g(s[0]) + f(s.drop(1))` style + a matching impl loop.
- **No leakage:** spec view names no patched path/symbol, no diff line, no
  bug/fix narration; identifiers describe behavior, not the edit.
- **Banned:** str indexing (List[int]/PSeq); builtin-exception Exsures;
  Assume/Refute; imports beyond typing+nagini_contracts; I/O. Axiomatized
  callee used inside an Ensures must be `@Pure @ContractOnly`.

## Self-check loop (≤8 verify rounds)
```
bash scripts/nagini_verify.sh {root}/{iid}/nagini/model.py [--float-encoding=real]   # G-VERIFY
bash scripts/nagini_verify.sh {root}/{iid}/nagini/model_prepatch.py                  # G-DIFF: must FAIL
swebench-unified gates --backend nagini {iid} --static-only
```
The verify script enforces a 300s timeout (exit 124 = simplify the model, don't
pile on annotations). NEVER weaken a contract to pass. If genuinely blocked by
Nagini's fragment, write `{root}/{iid}/nagini/BLOCKED.md` (what you tried, the wall,
candidate modelings) — a principled BLOCKED is valid; a weakened spec is not.
Do NOT run the Docker gates (G-RESOLVE/G-CONF/G-AX) yourself — the orchestrator
batches them; make patch.diff + axiom_check.py + conformance_check.py correct
by construction.

## Final message = structured report
status (green|blocked); static-gate outcomes + verify times; modeled functions;
axioms (A-consumed) + deep-model references (A-reference) + provenance; the
refinement.md tags; how you handled the hard subtlety; confirmation prepatch
fails on the right clause; whether patch.diff == gold; the meta.json gates
block. If blocked, the precise wall.
