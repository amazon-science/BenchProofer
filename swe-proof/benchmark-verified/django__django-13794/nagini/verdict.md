# P2 adversarial audit — django__django-13794

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The audit re-ran 8 candidate wrong implementations against this specification, each changing the implementation and leaving the specification as this bundle ships it. None of them verified without also resolving the instance, which is what a counterexample to `verify => correct` would require. The positive control verifies, so the specification is satisfiable by a correct implementation and that outcome is not an artifact of a specification nothing can satisfy.

**How far this record can be re-checked.** The attack sources are not carried in this bundle. The count above and the positive-control outcome are what the harness recorded; the sources and their individual outcomes are not, so this role is the one part of the cell a reader cannot re-run from the bundle alone. The audit record states the same limitation.

_The attack bodies behind this role's verdict are not carried in this bundle. The count of attacks re-run and the positive-control outcome are recorded above; the sources themselves are not, so this role is the one part of the cell a reader cannot re-verify from the bundle alone._

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The audit re-ran 8 candidate wrong implementations against this specification, each changing the implementation and leaving the specification as this bundle ships it. None of them verified without also resolving the instance, which is what a counterexample to `verify => correct` would require. The positive control verifies, so the specification is satisfiable by a correct implementation and that outcome is not an artifact of a specification nothing can satisfy.

**How far this record can be re-checked.** The attack sources are not carried in this bundle. The count above and the positive-control outcome are what the harness recorded; the sources and their individual outcomes are not, so this role is the one part of the cell a reader cannot re-run from the bundle alone. The audit record states the same limitation.

_The attack bodies behind this role's verdict are not carried in this bundle. The count of attacks re-run and the positive-control outcome are recorded above; the sources themselves are not, so this role is the one part of the cell a reader cannot re-verify from the bundle alone._

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) check for django__django-13794 nagini bundle. Spec region confirmed byte-identical to bundle via same-spec (exit 0); model verifies under pinned Nagini (exit 0, 10.3s).

Gold patch is exactly: __add__(self, other)->self.__cast()+other ; __radd__(self, other)->other+self.__cast() (added to __proxy__ in django/utils/functional.py; __cast() UNCHANGED). The two modeled functions:
  forward_combine: Ensures ToSeq(Result()) == ToSeq(realized) + ToSeq(other)  (models __add__)
  reverse_combine: Ensures ToSeq(Result()) == ToSeq(other) + ToSeq(realized)  (models __radd__)
with realized = self.__cast() modeled as a read-only R-refinement input, and str<->List[int] code-point carrier, + as PSeq concatenation.

Empirical faithfulness evidence: applied the gold patch to a base_commit (fe886eee) worktree and ran axiom_check.py against the REAL patched methods on a live lazy() proxy: 10 text boundary + 20000 text fuzz + 5 int boundary + 5000 int fuzz inputs all match ordered concatenation (G-AX OK, exit 0). Independent probes (add08 str+lazy via __radd__, add09 lazy+lazy, lazy+str via __add__, empty/unicode/newline operands, int test_lazy_add lazy_4()+lazy_5()==9) found no divergence. The postcondition equals the real callee's result on the entire modeled str domain; operand order and content are exactly preserved.

The spec's restriction to str x str operands (List[int] carrier) is a sound refinement covering exactly the F2P tests (test_add08/add09, test_lazy_add); it does not overclaim about unmodeled operand types. No input found where the modeled function disagrees with the real __add__/__radd__ on the modeled domain. Spec is not too strong and does not drift.

Verdict: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `axiom_check.py`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Attacker (3): leakage / gold-reconstruction. Compared the consumer spec view (markers.spec_view over model.py, impl regions elided) against the public problem_statement.

Public problem_statement: the `add` template filter cannot concatenate a string with a lazy string; result is always the empty string because concatenation raises TypeError (can only concatenate str, not __proxy__, to str).

Gold edit (out of scope for the consumer, must NOT be recoverable from spec view): add __add__ (return self.__cast() + other) and __radd__ (return other + self.__cast()) to __proxy__ in django/utils/functional.py.

Spec-view content: a module docstring + two contracted functions forward_combine / reverse_combine with pre/post-conditions and ELIDED impl regions ('... implementation elided — supplied by the consumer'). It states only DESIRED BEHAVIOUR at the sequence-abstraction altitude: a deferred value must combine under binary + from either side using its realized value, producing ordered concatenation (realized ++ other on the left, other ++ realized on the right), so the add filter concatenates rather than collapsing to '' .

Leakage assessment — spec view does NOT reveal the gold edit beyond the public statement:
- No repo file named (functional.py absent); no method/symbol names (__add__, __radd__, __proxy__, __cast, lazy) present.
- The fix expression (self.__cast() + other) is nowhere present; impl is elided.
- The 'collapse to empty string' consequence is verbatim from the public problem_statement.
- The 'from EITHER side / two directions' framing is a direct behavioral consequence of 'concatenate a string WITH a lazy string' (requires both lazy+str and str+lazy), stated abstractly as desired behaviour, not as an edit and not naming the reflected-operator mechanism.
- 'realized (forced) value' / 'read-only input realized' is an abstraction of the operand, not the __cast() symbol; does not disclose the edit site or method structure.

Note on scope: mapping.md, refinement.md and meta.json DO name __add__/__radd__/__cast()/functional.py, but these are audit/refinement artifacts, NOT part of the consumer spec view (G-HYGIENE spec_view hash 9c82bd8...; G-LEAK pass, failures=[]). Only the spec view is the consumer-facing surface for this gate. The spec view stays at behavioral-specification altitude and hands over neither the edit location, the changed symbols, nor the approach. G-LEAK already recorded 'spec view clean'; independent re-derivation confirms it.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
