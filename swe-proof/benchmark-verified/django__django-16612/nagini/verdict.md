# P2 adversarial audit — django__django-16612

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
- **machine verdict:** django__django-16612 nagini bundle. Spec region byte-identical (same-spec exit 0); model.py verifies (nagini exit 0, 14.2s). This is a DEEP-model bundle with NO consumed @ContractOnly axioms: build_append_slash_redirect(path,query) models the redirect target built in AdminSite.catch_all_view via request.get_full_path(force_append_slash=True) -> _get_full_path. The spec redirect_target = path ++ slash_part(path) ++ query_part(query), i.e. location, then '/' iff not already slash-ending, then '?'+query iff query non-empty.

Verified faithfulness against the REAL repo at base_commit 55bcbd8d (worktree), importing the ACTUAL django.utils.encoding.escape_uri_path / iri_to_uri (not just axiom_check's reproduction). Compared real _get_full_path(path, force_append_slash=True) to the deep model:
 - All F2P-tested inputs AGREE: ('/test_admin/admin/admin_views/article','id=1')->'.../?id=1'; prefixed SCRIPT_NAME case; empty-query -> slash-only; ('/a','')-> '/a/'.
 - 18,317 in-domain fuzz inputs (identity-transform class): 0 divergences.

Divergences from the real callee occur ONLY outside the declared R-refinement class (e.g. path '/adm in'-> real '/adm%20in/' vs model '/adm in/'; non-ASCII 'é'-> '%C3%A9'). The mapping.md/refinement.md explicitly scope the R-refinement to admin endpoint paths + ASCII query strings where escape_uri_path/iri_to_uri are the identity, and axiom_check.py enforces that scope with an identity guard (return early if quote != arg). The F2P tests (test_missing_slash_append_slash_true_query_string with '?id=1' and the SCRIPT_NAME variant) all lie strictly inside this class, so the modeled function agrees with the real callee on every tested input.

The spec is NOT too strong / does not drift: it agrees with real repo behavior everywhere within its honestly-declared and enforced domain, and that domain covers the fix-exercising inputs. No diverging input exists inside the claimed scope. Verdict FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `axiom_check.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view (impl elided to '...') hashes 1923f7b6… — byte-identical to meta.json G-HYGIENE spec_view hash; impl region not exposed. The public problem_statement already fully discloses the desired behaviour: it states the bug (APPEND_SLASH redirect drops query string), gives the exact expected redirect (.../admin/auth/foo/?id=123 with slash added AND query preserved), the buggy actual redirect (query dropped), quotes the offending line HttpResponsePermanentRedirect('%s/' % request.path), and even points at request.META['QUERY_STRING']. The spec view formalizes exactly this outcome (redirect_target = location ++ conditional slash ++ ('?'+query when non-empty)) as a black-box behavioural property. It describes WHAT (the I/O relation already public) not HOW. Crucially it never names the gold edit's mechanism — get_full_path / force_append_slash appear only in meta.json/mapping.md deep-model notes, NOT in the solver-facing spec view. No spec-view line reveals the gold edit beyond problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `mapping.md`, which ships in this bundle, so a reader can start there.
