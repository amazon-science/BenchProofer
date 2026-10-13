# P2 adversarial audit — pytest-dev__pytest-8399

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
- **machine verdict:** Faithfulness-break attack: no divergence found. (1) generated_fixture_name models the changed op directly (prepend code point 95); the gold patch prepends literal '_' to five name f-strings. Under the R-refinement str<->List[int] the model op [95]+label equals real '_'+label on every input. (2) Precondition domain (len(label)>0, label[0]!=95) matches reality exactly: all five base_commit f-strings have LITERAL prefixes 'unittest_'/'xunit_' (non-empty, first char u/x, never _), so no real input is excluded by the precondition -- the spec does not over-constrain or shadow any real domain point. (3) The only callee-like element, the deep model `listed`, was validated against the real repo rule two ways: read _showfixtures_main (python.py:1511, `argname[0]=="_"`) and _show_fixtures_per_test (python.py:1429, `argname.startswith("_")`) at base_commit 6e7dc8ba -- both match `listed` verbatim; and ran axiom_check.py (G-AX) asserting listed==both real filter expressions over 17 boundary + 20000 fuzz names x 5 verbosity levels + fix effect over 20000 labels, exit 0. (4) model.py verifies under pinned Nagini (11.97s). Postconditions (len+1, ToSeq[0]==95, drop(1)==label, not listed(_,0), listed(_,1)) are exactly the F2P observation (test_fixtures_setup_setUpClass_issue8394: --fixtures omits 'no docstring available', --fixtures -v shows it). No input where the modeled function disagrees with the real repo callee/logic; spec is neither too strong nor drifted.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Question: does the SOLVER-FACING spec view (model.py spec regions: axioms/pure/pre/post) disclose the gold edit beyond what the public problem_statement already states? It does not.

What the public problem_statement ALREADY discloses (this is the leakage baseline, and it is generous): 'The expected (and previously implemented) behavior is that this fixture's name would start with an underscore, and would therefore only get printed if the additional -v flag was used.' So the public statement itself already reveals the entire modeled behavior: prepend '_' to the generated fixture name => omitted from the default `pytest --fixtures` listing, shown under `-v`.

What model.py's spec regions disclose: PRIVACY_MARKER=95 ('_'); the deep `listed` rule (omitted at default verbosity iff name begins with '_', always shown when verbose>0); and postconditions Result()[0]==95, drop(1)==label, not listed(Result(),0), listed(Result(),1). Every one of these is a restatement of the exact behavior already given in problem_statement (leading underscore -> hidden by default, shown with -v). Nothing here goes beyond the public statement.

Critically, the concrete gold-edit specifics that live ONLY in hints_text/patch are ABSENT from the spec view: the descriptive name is abstracted to an opaque input `label: List[int]` (label[0] != 95, len>0). grep of model.py for 'unittest|xunit|python.py|setup_|f"' returns nothing — none of the five gold f-strings (f"unittest_{...}_fixture_{...}", f"xunit_setup_*"), none of the repo filenames (_pytest/python.py, _pytest/unittest.py), and none of the name= sites appear in the spec a solver fills. A solver seeing only model.py could not reconstruct the five specific hunk locations/strings from the spec — only the abstract 'prepend the marker' behavior, which is public.

mapping.md and refinement.md DO reproduce the five gold f-strings and embed patch.diff verbatim, but those are auditor-facing provenance/refinement documents whose purpose is to bind the model to the gold patch (G-EQ); they are not the solver's spec view, and their disclosure of the patch is by design, not leakage. The gate here concerns the spec view (model.py), which leaks nothing beyond problem_statement.

Same-spec integrity of the spec regions was not the object of this gate, but no repo literals were found in model.py's spec, confirming the abstraction boundary is clean. Verdict: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
