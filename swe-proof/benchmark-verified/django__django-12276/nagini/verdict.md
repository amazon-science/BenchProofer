# P2 adversarial audit — django__django-12276

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass

- **status (recorded):** `pass`
- **machine verdict:** eq: 9 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The audit re-ran 9 candidate wrong implementations against this specification, each changing the implementation and leaving the specification as this bundle ships it. None of them verified without also resolving the instance, which is what a counterexample to `verify => correct` would require. The positive control verifies, so the specification is satisfiable by a correct implementation and that outcome is not an artifact of a specification nothing can satisfy.

**How far this record can be re-checked.** The attack sources are not carried in this bundle. The count above and the positive-control outcome are what the harness recorded; the sources and their individual outcomes are not, so this role is the one part of the cell a reader cannot re-run from the bundle alone. The audit record states the same limitation.

_The attack bodies behind this role's verdict are not carried in this bundle. The count of attacks re-run and the positive-control outcome are recorded above; the sources themselves are not, so this role is the one part of the cell a reader cannot re-verify from the bundle alone._

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 9 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The audit re-ran 9 candidate wrong implementations against this specification, each changing the implementation and leaving the specification as this bundle ships it. None of them verified without also resolving the instance, which is what a counterexample to `verify => correct` would require. The positive control verifies, so the specification is satisfiable by a correct implementation and that outcome is not an artifact of a specification nothing can satisfy.

**How far this record can be re-checked.** The attack sources are not carried in this bundle. The count above and the positive-control outcome are what the harness recorded; the sources and their individual outcomes are not, so this role is the one part of the cell a reader cannot re-run from the bundle alone. The audit record states the same limitation.

_The attack bodies behind this role's verdict are not carried in this bundle. The count of attacks re-run and the positive-control outcome are recorded above; the sources themselves are not, so this role is the one part of the cell a reader cannot re-verify from the bundle alone._

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness confirmed against the real repo at base_commit 53d8646 (django/forms/widgets.py). Modeled function requires_value(control, value_present) = generic_requires_value(control.hidden) and not value_present maps to gold FileInput.use_required_attribute(self, initial) = super().use_required_attribute(initial) and not initial.

Evidence: (1) Axiom generic_requires_value(hidden)==(not hidden): the REAL inherited Widget.use_required_attribute returns not self.is_hidden and ignores initial across all widget classes (FileInput/ClearableFileInput/Input/Widget/HiddenInput) and 13+ initial values — exact match, no over/under-approximation. (2) Full conjunction: real patched FileInput.use_required_attribute equals (not is_hidden) and (not initial) over the entire battery (None/''/0/[]/{}/False truthy=resume.txt/x/space/1/[0]/{a:1}/True) — all MATCH. (3) Abstraction initial(object)->value_present(bool) via truthiness is lossless because the method's ONLY observation of initial is `not initial` (never indexed/iterated); adversarial probe with custom __bool__ (falsy object), __len__==0, __len__==5, and bare object() all MATCH real behavior. 

The spec is neither too strong nor drifting: the decomposed postconditions (Implies(value_present, Result==False) and Implies(not value_present, Result==generic)) pin behavior exactly to the real callee on both branches. same-spec exit 0 (byte-identical spec region), nagini_verify exit 0 (verifies). No diverging input exists.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery).

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec-view verified byte-identical to the recorded frozen view: markers.spec_view(model.py,'nagini') sha256 = ef9163a2af43562d147b185dd4cf6ee2778ead4a7c22bf44a860bf6876bac55e, matching meta.region_hashes.spec_view exactly (impl region elided to '...'). Leakage baseline = PUBLIC problem_statement only (hints_text excluded per instruction). The public problem_statement is already maximally explicit about the gold edit: it names ClearableFileInput.use_required_attribute(), links the exact widgets.py#L454, states it 'should be moved to FileInput.use_required_attribute() so that required is not output ... when a file is already set.' Thus the full gold fix (method-move + base-decision AND not-already-set) is public. The spec-view only formalizes that same target behavior in ABSTRACT terms: requires_value == generic_requires_value(control.hidden) and not value_present, plus two decomposed Implies clauses. A spec necessarily specifies target behavior; that is not leakage. Critically the spec-view is STRICTLY LESS revealing of the edit's structure than the public statement: it uses UploadControl.hidden / value_present:bool abstractions and discloses NO class names, NO method-move, NO super()/MRO delegation, NO widgets.py line numbers. Those structural specifics live only in refinement.md / mapping.md / patch.diff, which are audit artifacts not shown to the solver. No spec-view line reveals gold-edit information beyond the public problem_statement. Agrees with recorded G-PANEL-3.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
