# P2 adversarial audit — django__django-13820

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The audit re-ran 7 candidate wrong implementations against this specification, each changing the implementation and leaving the specification as this bundle ships it. None of them verified without also resolving the instance, which is what a counterexample to `verify => correct` would require. The positive control verifies, so the specification is satisfiable by a correct implementation and that outcome is not an artifact of a specification nothing can satisfy.

**How far this record can be re-checked.** The attack sources are not carried in this bundle. The count above and the positive-control outcome are what the harness recorded; the sources and their individual outcomes are not, so this role is the one part of the cell a reader cannot re-run from the bundle alone. The audit record states the same limitation.

_The attack bodies behind this role's verdict are not carried in this bundle. The count of attacks re-run and the positive-control outcome are recorded above; the sources themselves are not, so this role is the one part of the cell a reader cannot re-verify from the bundle alone._

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The audit re-ran 7 candidate wrong implementations against this specification, each changing the implementation and leaving the specification as this bundle ships it. None of them verified without also resolving the instance, which is what a counterexample to `verify => correct` would require. The positive control verifies, so the specification is satisfiable by a correct implementation and that outcome is not an artifact of a specification nothing can satisfy.

**How far this record can be re-checked.** The attack sources are not carried in this bundle. The count above and the positive-control outcome are what the harness recorded; the sources and their individual outcomes are not, so this role is the one part of the cell a reader cannot re-run from the bundle alone. The audit record states the same limitation.

_The attack bodies behind this role's verdict are not carried in this bundle. The count of attacks re-run and the positive-control outcome are recorded above; the sources themselves are not, so this role is the one part of the cell a reader cannot re-verify from the bundle alone._

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) attack: no divergence found. The modeled function is_source(is_package, file_is_set, path_is_ordinary_list) = is_package and (file_is_set or path_is_ordinary_list), realized by treat_as_migration_source, models the post-patch MigrationLoader.load_disk per-module classification (django/db/migrations/loader.py else-arm). Real gold-patched callee: not-a-package -> skip; package with __file__ None AND __path__ not a list -> skip (PEP-420 namespace); else -> migration source. Checks: (1) same-spec exit 0 (spec region byte-identical). (2) nagini_verify.sh: 'Verification successful' (11.3s) -- model verifies against the frozen spec. (3) axiom_check.py exit 0: builds real regular + PEP-420 namespace packages on disk, imports them, confirms isinstance(__path__, list) discriminates them incl. the __file__-deleted regular-package frozen case, and confirms is_source == transcribed gold load_disk classification on all 6 reachable (is_package,file_is_set,path_is_ordinary_list) combos. (4) Manual truth-table over all reachable inputs agrees on every row, including the discriminating frozen-environment row (True,False,True)->source (F2P test_loading_package_without__file__) and namespace (True,False,False)->skip. The precondition Implies(not is_package, not path_is_ordinary_list) only pins an input region that is unreachable in reality (a non-package has no __path__), so it removes no genuine callee behavior and does not make the spec too strong. Check-order difference between real code (path check first) and model is immaterial to the boolean outcome; unchanged reload() side effect is outside classification scope. No input exists where the modeled function disagrees with the real repo callee.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `axiom_check.py`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Leakage judged against the public problem_statement only (hints excluded). The problem_statement for django__django-13820 is maximally explicit about the gold edit: it names the file (django.db.migrations.loader.MigrationLoader.load_disk), states the current check ('skips a module m if getattr(m, "__file__", None) is false'), explains the namespace-package discrimination via __path__ not being an ordinary list, and literally states the fix verbatim: 'I propose to augment getattr(m, "__file__", None) with and isinstance(m.__path__, list).' The entire semantic content of the gold patch (the added isinstance(module.__path__, list) conjunct) is therefore already public.

The solver-facing spec view (model.py docstring + Pure is_source + pre/postconditions) encodes the decision is_package and (file_is_set or path_is_ordinary_list) over three abstracted bool carriers (is_package, file_is_set, path_is_ordinary_list). Every fact it discloses — the package/__path__ check, the __file__-is-None check, the __path__-is-a-list conjunct, and the discriminating regular-package-without-__file__ case — is already spelled out in the public statement. Nothing in the spec view reveals the gold edit BEYOND what problem_statement already discloses.

The auditor-side documents refinement.md and mapping.md do quote the verbatim gold hunk (pre/post-patch code), but these are provenance/audit artifacts, not part of the solver's spec view; and even so, the problem_statement already contains the fix, so there is no incremental leak. Verdict: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
