# G-PBT spec-lane manifest authoring — {iid} ({backend_name})

The bundle at `{root}/{iid}/{backend_name}/` is already GREEN (spec + impl verify).
Your job: author `properties.py` in that bundle directory — a manifest of
adversarial SPEC variants that stress whether the spec is exactly as strong as it
must be: no weaker (admits wrong impls), no stronger (rejects correct impls).

This is the SPEC lane only. Contracts are not runtime-executable, so the oracle
is the verifier itself: each variant is re-run through the backend checker and its
accept/reject compared to your declared `expect`.
Do NOT author axiom-lane runtime probes here — that is G-AX's job (`axiom_check.py`).
Set `AXIOM_TESTS = []`.

## Read first
1. `prompts/{backend_name}/spec_guide.md` — the binding spec rules for this backend.
2. The bundle dir — the frozen solution file (note every modeled function, its
   precondition, and the LOAD-BEARING postcondition clause that pins the output),
   `refinement.md`, `mapping.md`, `meta.json`.
3. `{root}/{iid}/instance.json` — `problem_statement`, FAIL_TO_PASS, PASS_TO_PASS,
   and the gold `patch`. Use the gold patch + F2P tests to ground each rival's
   refinement argument.
4. Any `{root}/*/{backend_name}/properties.py` that already exists — a worked,
   validated reference battery in the house style. Match its structure and its
   level of argument, not its content.

## Deliverable: properties.py

Build every variant by region-surgery on the frozen source so the spec is
PROVABLY untouched — read the frozen solution into a `_BASE` string, then produce
each variant with a `_swap(_BASE, old, new)` helper that replaces exactly one
unique substring lying ENTIRELY inside an editable region. Reference pattern:

- `INSTANCE` — the instance id string.
- `FLOAT_ENCODING` — for nagini, the meta.json `float_encoding` value if set, else
  None; omit for the Lean backends.
- `_BASE` — the frozen solution text, read from the file next to properties.py.
- `_swap(src, old, new)` — assert `old` occurs exactly once, then replace it;
  raise on drift so an edited solution fails loudly at load.
- `SPEC_TESTS` — a list of dicts, each with keys: `id`; `kind` (one of
  `uniqueness`, `soundness`, `admissibility`); `expect` (`verify` or `reject`);
  `module` (the full variant source string built via `_swap`); for `reject` cases
  a `refinement` (why its faithful real patch would NOT resolve the F2P); and a
  `rationale` (where the verify/reject comes from — which clause, permission, or
  typing rule).
- `AXIOM_TESTS` — ignored by this gate (the axiom lane is G-AX's); set it to an
  empty list or omit it.

**Editable regions by backend** — everything outside these is the frozen spec:
- **nagini**: only between `# impl-start` / `# impl-end`.
- **velvet**: between `-- impl-start` / `-- impl-end`, AND the `prove_correct <name> by`
  tactic BODY (velvet's spec view elides prove_correct bodies but keeps the header).
- **lean**: between `-- impl-start` / `-- impl-end`, AND the whole `-- proof-start` /
  `-- proof-end` region (lean's spec view elides both).

Editing the proof/tactic body is not just allowed for lean and velvet — it is
usually REQUIRED for a positive control (see "The one failure mode" below).

## Required spec-lane coverage (only the classes that APPLY; justify omissions in `assessment`)

Calibration from the 500-bundle verified corpus: ~6 spec cases per cell,
uniqueness-heavy (2887 uniqueness : 897 soundness : 513 admissibility).

1. **UNIQUENESS (spec-too-weak hunt)** — `expect="reject"`. A WRONG impl the spec
   must reject. Prefer reasoned attacks over mechanical near-misses:
   - **Frame/permission mutation (nagini only)**: if an input is read-only (a half
     permission `Acc(x, 1/2)`), a rival that WRITES it to satisfy the postcondition
     vacuously must fail for insufficient permission. MANDATORY whenever a
     read-only input exists. Keep the gold invariants verbatim so the rejection is
     attributable to the write. This class does NOT exist for lean/velvet — their
     inputs are immutable values, there is no frame and nothing to mutate. Do not
     invent a lean/velvet analogue; say so in `assessment`.
   - **Ungrounded-oracle echo**: if the postcondition pins the result to a local
     `@Pure`/`def` answer-key, build the impl that just echoes it. Then decide
     which of two things you have, because this is the single most misjudged class:
     * the oracle is **GROUNDED** — total, and bottoming out in concrete literals
       or operations an implementer must actually perform, and fully visible in the
       spec view (the `pure`/`axioms` regions ARE part of the spec view). Then the
       echo is a CORRECT implementation whose faithful real patch RESOLVES the F2P,
       so it cannot carry the refinement argument a rival requires. Ship it as a
       `soundness` positive control (`expect="verify"`) and record the adjudication
       in `assessment`.
     * the oracle **leaves the contested behaviour unpinned** — it recomputes the
       very semantics under test, so echoing it discharges the obligation without
       the spec ever constraining that semantics. Then it is a genuine
       `uniqueness` rival and, if it verifies, a real SPEC-TOO-WEAK.
     The discriminating question is NOT "does the postcondition mention a local
     def" but "would a faithful implementation of exactly that def resolve the F2P".
   - **Value-level double-mask**: an index/structural claim checked only through a
     value proxy that drops disagreeing indices.
   - **Control-flow-effect**: a raise/return/side-effect difference invisible to the
     value abstraction (needs a capability-token rival to discriminate).
   - **Partial-domain**: correct on most of the F2P/P2P domain but diverging on a
     sub-domain (first/last element, a length class, a specific value).
   - **Wrong-payload**: if the spec pins an error message / diagnostic / status
     value, a rival with the right control flow but the wrong payload.
2. **SOUNDNESS / positive control** — `expect="verify"`. A structurally DIFFERENT
   but CORRECT impl that MUST verify. If a faithful correct impl is rejected, that
   is SPEC-TOO-STRONG. Aim for two: one cheap reshape (reordered branches, a
   different loop/branch shape) and one that reaches the answer by a genuinely
   different route (search/table-lookup instead of a cascade, or the closest
   analogue of the REAL patched code).
3. **ADMISSIBILITY** — `expect="verify"`. Show the precondition admits a normal
   F2P-shaped input: for nagini, a self-call on a freshly built full-permission
   input, `Assert`ing the expected result. If the spec has NO precondition (common
   for lean/velvet — an unconditional `∀`, or an empty `pre-conditions` region),
   admissibility becomes the same question one level down: is the postcondition
   SATISFIABLE (non-contradictory) at the inputs the F2P tests exercise? Exhibit a
   witness result for two or three real inputs (lean: top-level `example`s inside
   the impl region; velvet: `have`s inside the method body, since a top-level decl
   there would be a syntax error). Leave the gold impl and gold proof running
   unchanged alongside, so a failure cannot be a proof-shape artifact.

Each `expect="reject"` rival MUST carry a `refinement` arg: the argument that its
faithful real patch would NOT resolve the F2P/P2P, so a verifying rival is a true
verify-does-not-imply-resolve break, not an artifact. A rival you cannot write
that argument for is not a rival — drop it or reclassify it.

**Never weaken the spec.** You are not authorised to edit the solution file. If a
case seems to prove the spec wrong, that is a finding to REPORT in `assessment`,
not a licence to change the artifact.

## The one failure mode that ruins this lane: a positive control that fails for a PROOF reason

In the 500-bundle verified round the first sweep flagged 85 cells and **81 were
test bugs, not artifact defects** — a 95% false-positive rate. In the pro Phase A
calibration, EVERY hand-authored positive control failed on first try, all for
proof-shape reasons. A positive control that fails reads as "verification failed"
and gets mislabeled SPEC-TOO-STRONG. Pre-empt the known classes:

1. **Malformed Nagini `# type:` comment.** A type comment attaches only to an
   assignment/with/for target — NEVER to a bare `return []`, and the text must be
   exactly `# type: T` with no trailing parenthetical. Bind a typed local first
   (`empty = []  # type: List[int]`, then `return empty`).
2. **Dropping a framing assert / invariant / lemma.** A structurally-different
   positive control must KEEP the proof obligations it still needs. Change the
   executable shape, not the invariants.
3. **A tactic body written against the OLD executable shape (lean/velvet).** This
   is the dominant one. `simp only [Id.run, ...]` makes no progress once you drop
   `Id.run do`; `loom_solve` alone may already close a delegating impl so a
   trailing `simp_all` errors with "No goals to be solved"; a `split` fires on a
   `match` before the key equality is decided and leaves opaque hypotheses. ADAPT
   the proof: discharge the SAME obligations by a different route. Routes that
   worked in calibration: `split <;> split <;> simp_all` after unfolding the pure
   definitions; `by_cases` on each key equality then `subst` on the positive
   branch; unfolding `List.find?` alongside the pure defs.
4. **Forward-append against a front-recursive `@Pure` fold.** Needs an
   `f(a+b)==f(a)+f(b)` lemma the verifier will not auto-discharge. Prefer a
   branch reorder or a local-variable reshape over flipping loop direction.
5. **A variant that times out.** A timeout is recorded as INCONCLUSIVE and forces
   MALFORMED-TESTS for the whole cell — it never counts as a rejection. Keep
   variants small.

## Self-validate — you MUST check every case before submitting

Two checks, both cheap. Do not skip them; an unchecked battery is worse than no
battery because it manufactures a false finding.

**1. same_spec.** Load the manifest and confirm every case shares the frozen spec:

    python -c "
    import sys; sys.path.insert(0,'src')
    from swebench_unified.backends import get_backend
    from swebench_unified.gates.base import Bundle
    from swebench_unified.gates.pbt import load_manifest
    from swebench_unified.markers import same_spec
    b = Bundle('{iid}', get_backend('{backend_name}'))
    frozen = b.solution_src()
    for c in load_manifest(b):
        print(c['id'], same_spec(frozen, c['module'], b.backend.language))
    "

Every case must print True. A False means your region surgery touched the spec.
`Bundle` resolves the benchmark from the environment, which already selects the
one you are authoring for — do not override `SBU_BENCHMARK`/`SBU_BENCHMARK_DIR`.

**2. verify/reject, per case, through the THROTTLED checker.** Write each case's
`module` to a temp file and run:

    python experiments/pro2026/pbt_verify.py {iid} {backend_name} <variant-file>

If that wrapper is absent, call the backend's own checker instead
(`scripts/nagini_verify.sh <file>`, `scripts/lean_verify.sh <file> 900`) and keep
your own concurrency low.

It prints `RESULT=VERIFIES|REJECTED|TIMEOUT` plus verifier diagnostics on
rejection. Use it freely — it holds a global semaphore, so you cannot overload the
host no matter how many authors run concurrently. Iterate until every case's
actual result matches its declared `expect`:

- a `soundness`/`admissibility` case that comes back REJECTED is almost always
  YOUR proof gap (classes 1-5 above). Read the diagnostics and fix the case. Only
  after you have genuinely failed to find any faithful in-region proof that admits
  a structurally different correct impl may you report a suspected
  SPEC-TOO-STRONG — and then say exactly what you tried in `assessment`.
- a `uniqueness` case that comes back VERIFIES is a candidate SPEC-TOO-WEAK. Before
  claiming it, re-check its `refinement` argument: would its faithful real patch
  really fail the F2P? If not, it is not a rival — reclassify or drop it. If the
  argument holds, KEEP the case (its `expect` stays `reject`) and report the
  finding in `assessment`. Do not silence it.

Then submit the `pbt_author` payload: `status`, `n_spec_cases`, `case_classes`,
`assessment` (which classes apply/omitted and why, plus every case you had to
re-tactic and any suspected finding), `notes`.
