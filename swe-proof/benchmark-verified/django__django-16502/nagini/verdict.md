# P2 adversarial audit — django__django-16502

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
- **machine verdict:** Faithfulness-break attack: no drift found. Spec region byte-identical (same-spec exit 0); model verifies with pinned Nagini (exit 0, 10.1s).

Method: applied the gold patch.diff and drove the REAL patched Django callees (not axiom_check's re-implementations) against the modeled functions.

(1) Header path — drove the actual patched ServerHandler.cleanup_headers over the full cube head∈{T,F} × has_size∈{T,F} × keepalive∈{T,F}, extracting (Content-Length present, Connection==close, close_connection). All 8 cases match model.prepare_response_headers / want_terminate exactly. Notably the discriminating new behaviours are reproduced by both: HEAD drops Content-Length (head=T,size=T → has_size_after=False); HEAD keeping alive is NEVER closed for lacking size (head=T,size=F,keepalive=T → conn_close=False); GET with size on threading server not closed (F,T,T → False). No mismatch.

(2) Body path — drove the actual patched finish_response: HEAD consumes the iterable and writes nothing (empty body); GET writes the full application data in order. Both match emit_response_body(result, head): head → len 0, not head → == result. No mismatch.

(3) Modeling assumptions on the UNCHANGED wsgiref base callees validated against the real stdlib by axiom_check.py (exit 0): base finish_response writes full body (3.1), base finish_content would inject Content-Length:0 (3.2, the reason for the HEAD bypass), base cleanup_headers sets no Connection so entry conn_close/close_flag==False (3.3).

Abstraction adequacy: the real code branches solely on REQUEST_METHOD=='HEAD' (→head bool), Content-Length membership (→has_size bool), and isinstance(server, ThreadingMixIn) (→keepalive bool), with body as bytes chunks (→List[int] via ToSeq). The abstracted domain is exhaustively enumerated above; the modeled functions agree with the real callees on every point. The spec is neither too strong nor drifted — the entry preconditions (conn_close==False, close_flag==False) are exactly the post-base state guaranteed by the unchanged wsgiref base, so they do not over-constrain. FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `axiom_check.py`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Judged the canonical spec view produced by swebench_unified.markers.spec_view (NaginiBackend); its sha256 582c3ccd42db9a36c2e129a2ff7144c8efe7f04da7af86db6c72f253df4d022b matches meta.json region_hashes.spec_view, so the region under audit is authoritative. The impl regions of both prepare_response_headers and emit_response_body collapse to the elision placeholder, so no implementation mechanism is visible.

The public problem_statement (django#16502) already discloses: (1) HEAD responses must carry no message body (the core RFC-compliance requirement); (2) the Expected curl -iX HEAD output shows headers only and, notably, NO Content-Length line (i.e., the payload-size header is dropped for HEAD); (3) 'compliant user agents expect to be able to terminate the connection after the headers are sent' plus the Broken-pipe note (the connection-termination behaviour).

Every behavioural fact stated in the spec view maps to those public disclosures: empty body for the body-less method (=(1)); payload-size header dropped for the body-less method / left untouched for body-bearing (=(2)); a body-less method is never asked to terminate merely for lacking a payload-size header (=(3)). The 'keepalive'/ThreadingMixIn terminate branch is a pre-existing, UNCHANGED behaviour, not part of the gold edit, so restating it does not leak the edit.

The spec view is fully abstracted and contains NONE of the gold patch's identifying tokens: no basehttp.py, cleanup_headers, finish_response, REQUEST_METHOD, "HEAD", Content-Length, Connection/"close", deque, send_headers, or finish_content. The request method is abstracted to a bool 'head', header membership to bool fields, and the body to List[int]/PSeq. Nothing in the spec view reveals the patch's mechanism (iterator consumption via deque, header deletion, bypassing finish_content, the specific method overrides) beyond the behaviour the problem_statement already requires. A verification spec must state its postconditions; here those postconditions are all derivable from the public problem_statement. No spec-view line pins the gold edit beyond problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
