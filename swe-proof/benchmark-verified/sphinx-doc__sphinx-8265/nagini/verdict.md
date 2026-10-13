# P2 adversarial audit — sphinx-doc__sphinx-8265

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
- **machine verdict:** Faithfulness attack (spec-too-strong / spec-drifts-from-repo) FAILED to break the bundle. The spec is a faithful, 1:1 abstraction of the gold-patched real callees.

### Checks run
- same-spec on the unmodified model: SAME (byte-identical spec region). 
- nagini_verify.sh model.py: Verification successful (11.44s, <300s, no flags).
- axiom_check.py (G-AX): OK, join_comma == real ', '.join on 9 boundary + 30000 fuzz inputs; twin discriminates both sites.

GOLD-PATCH CORRESPONDENCE. The gold patch edits two sibling methods in sphinx/pycode/ast.py:
  visit_Tuple: non-empty tuple -> '(' + ', '.join(...) + ')'; empty -> '()'.
  visit_Subscript: if is_simple_tuple(slice) (ast.Tuple, non-empty, no Starred) render body as bare ', '.join(members) inside [..]; ast.Index-wrapped variant same; else '%s[%s]' % (base, self.visit(slice)).
model.py tuple_render / subscript_render encode exactly these (str<->PSeq[int] code points; '('=40 ')'=41 '['=91 ']'=93; join modeled deeply by join_comma == ', '.join).

I simulated the gold-patched renderer directly and confirmed the model agrees on every edge case I could construct that would expose over-strength/drift:
  (1,) -> (1)   [model tuple_render(["1"]) = (1) too -- spec faithfully preserves the real (arguably-buggy) single-element behaviour rather than 'fixing' it]
  (1, 2, 3) -> (1, 2, 3)
  () -> ()
  x[1,] -> x[1]      (simple 1-tuple index drops brackets)
  x[1, 2] -> x[1, 2]
  x[(1, 2)] -> x[1, 2]
  x[()] -> x[()]     (empty tuple index NOT simple -> verbatim '()')  <- model: index_is_member_group=False, slice_rendered='()' -> x[()] MATCH
  x[1] -> x[1]       (non-group index verbatim)
  x[*a, b] -> x[(*a, b)]  (Starred member -> not simple -> verbatim slice render '(*a, b)') <- model: index_is_member_group=False MATCH
  Tuple[int, int] -> Tuple[int, int]  (the P2P coupling)

Key precondition Requires(Implies(index_is_member_group, len(elts) > 0)) mirrors is_simple_tuple's bool(value.elts): the empty-tuple index is precisely the non-simple case, so the spec never over-claims a bracket-drop on an empty group. No input was found where the modeled functions disagree with the real repo callees. Deep-model soundness confirmed by G-AX; refinement is R/A-reference/I only, no consumed axiom, no kind-3 op.

RELAXED-LEAKAGE note (not a G-PANEL-2 defect): meta.json relaxed_leakage:true + RELAXED_LEAKAGE.md dispose the disclosure of the coupled group-as-subscript-index facet as an unavoidable, genuine problem_statement<->gold mismatch; re-confirmed the spec view names no patched file/symbol (visit_Tuple/visit_Subscript/is_simple_tuple/Starred/ast.Index/ast.py all absent). Out of scope for faithfulness.

Conclusion: no over-strength and no drift; spec agrees with the real repo on all constructed inputs. FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Leakage/gold-reconstruction audit of the solver-visible spec view (model.py). INDEPENDENT RE-VERIFICATION (not a rubber-stamp):

1. Lexical screen: grep of model.py for visit_Tuple|visit_Subscript|is_simple_tuple|Starred|ast.Index|ast.py|sphinx/pycode|node.|self.visit|isinstance => NONE. No gold diff line is quoted, no patched file path, no patched function/symbol name appears. The spec is abstract behavioural prose over PSeq[int].

2. Spec-region byte-identity confirmed across model.py / model_prepatch.py / model_prepatch_2.py (only impl regions differ) — the prepatch variants share the exact spec, so the discriminators are genuine spec content, not impl smuggling.

3. Core soundness re-confirmed via meta.json gates: G-VERIFY/G-DIFF/G-AX/G-RESOLVE/G-EQ(refinement, no kind-3, no consumed @ContractOnly axiom)/G-MUT/G-PBT/G-GOLD/G-INTEGRITY/G-HYGIENE all pass; G-LEAK status=relaxed (relaxed_leakage:true).

4. Unavoidability argument re-derived independently and holds: problem_statement concerns ONLY a standalone tuple default arg (color=(1,1,1)) losing its round brackets; it never mentions subscript/index expressions (Tuple[int,int], base[...]) nor tokens {subscript,index,starred,unpack,slice,join,ast,simple}. The gold's second, coupled hunk (visit_Subscript: a simple tuple index renders its body as the BARE join WITHOUT inner brackets) is forced only by the hidden P2P test test_unparse[Tuple[int, int]-Tuple[int, int]]: once hunk 1 parenthesises every non-empty tuple, the pre-patch visit_Subscript would emit Tuple[(int, int)] and break that P2P. So a faithful spec that makes the prepatch fail (G-DIFF) and admits no wrong impl (G-EQ) MUST model both sites — the group-as-index facet is genuinely unavoidable from the PS surface. No PS-only derivation of the subscript no-inner-brackets behaviour exists.

5. Scoped to the disposition: the ONLY facet disclosed beyond problem_statement is exactly the dispositioned one — model.py docstring §(2), subscript_render's postconditions keyed on index_is_member_group, and its Requires(Implies(index_is_member_group, len(elts)>0)) precondition (the 'no spread/unpacking member' condition = the Starred exclusion, explicitly covered by the disposition). No NEW leak beyond it was found: no diff quote, no patched symbol, no path, and the disposition is not broken (core gates sound, unavoidability not refuted).

Per the in-bundle panel recording convention (RELAXED_LEAKAGE.md + gates/_audit.py: a relaxed-leakage panel records as pass/NO-LEAKAGE + note; there is no separate 'relaxed' status at the panel layer), the honest recording for this properly-dispositioned instance is NO-LEAKAGE. Submit LEAKAGE reserved for a defect the disposition does not cover — none present.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere. This cell separately records G-LEAK as `relaxed`, which is a disclosure a reviewer accepted rather than the absence of one.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `relaxed` (the mechanical leakage screen over the same spec view). The account names `model.py`, `RELAXED_LEAKAGE.md`, all of which ship in this bundle, so a reader can start there.
