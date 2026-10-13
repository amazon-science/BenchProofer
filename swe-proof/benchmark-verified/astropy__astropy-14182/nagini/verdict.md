# P2 adversarial audit — astropy__astropy-14182

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass

- **status (recorded):** `pass`
- **machine verdict:** eq: 10 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The audit re-ran 10 candidate wrong implementations against this specification, each changing the implementation and leaving the specification as this bundle ships it. None of them verified without also resolving the instance, which is what a counterexample to `verify => correct` would require. The positive control verifies, so the specification is satisfiable by a correct implementation and that outcome is not an artifact of a specification nothing can satisfy.

**How far this record can be re-checked.** The attack sources are not carried in this bundle. The count above and the positive-control outcome are what the harness recorded; the sources and their individual outcomes are not, so this role is the one part of the cell a reader cannot re-run from the bundle alone. The audit record states the same limitation.

_The attack bodies behind this role's verdict are not carried in this bundle. The count of attacks re-run and the positive-control outcome are recorded above; the sources themselves are not, so this role is the one part of the cell a reader cannot re-verify from the bundle alone._

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 10 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The audit re-ran 10 candidate wrong implementations against this specification, each changing the implementation and leaving the specification as this bundle ships it. None of them verified without also resolving the instance, which is what a counterexample to `verify => correct` would require. The positive control verifies, so the specification is satisfiable by a correct implementation and that outcome is not an artifact of a specification nothing can satisfy.

**How far this record can be re-checked.** The attack sources are not carried in this bundle. The count above and the positive-control outcome are what the harness recorded; the sources and their individual outcomes are not, so this role is the one part of the cell a reader cannot re-run from the bundle alone. The audit record states the same limitation.

_The attack bodies behind this role's verdict are not carried in this bundle. The count of attacks re-run and the positive-control outcome are recorded above; the sources themselves are not, so this role is the one part of the cell a reader cannot re-verify from the bundle alone._

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness attack (spec-too-strong / model-vs-real-callee divergence): NO divergence found. The bundle models two gold-patch behaviors of astropy/io/ascii/rst.py: frame_index(n)==n (WRITE index idx=len(self.header.header_rows)) and data_start_index(n)==n+2 (READ start_line=2+len(...)). Both are pure affine integer formulas that are LITERALLY the gold patch's computed indices.

Validation performed in /tmp (built astropy shadow):
 Copied the installed astropy 5.2.2 and swapped in the gold-patched rst.py (verified via patch.diff). Ran axiom_check.py against it via PYTHONPATH shadow -> 'G-AX OK ... 0 violations' over n=1,2,3, boundary + 400 fuzz shapes.

(2) Instrumented the REAL RST.write/RST.read and asserted at runtime that idx==n (write) and self.data.start_line==2+n==n+2 (read) for n=1,2,3 and several header_rows orderings ([name],[name,unit],[name,unit,dtype],[unit,name],[dtype,name,unit]) -> all pass; the repo computes exactly the model formulas.

(3) Inspected raw rendered layout for n=4 and n=5: block is [header_0..header_{n-1}, rule, data...], rule at offset n, framing lines equal block[n], data begins at processed offset n+2 -> affine formulas hold at every n, no boundary where they break.

(4) rst_frame_block postcondition ToSeq(Result())==PSeq(block[n])+block+PSeq(block[n]) is byte-for-byte the gold patch's [lines[idx]]+lines+[lines[idx]]; the block[k]!=rule / block[n]==rule Requires are DOMAIN restrictions on well-formed RST blocks (real output always satisfies them) — they narrow the input domain but never cause the modeled output to disagree with the real callee on any shared, well-formed input.

(5) Model verifies: nagini_verify.sh -> 'Verification successful' (10.68s).

No consumed axioms; the deep models are A-references validated == real astropy writer/reader. The modeled functions agree with the real callee on every tested input; the spec is not too strong and does not drift from repo behavior.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `axiom_check.py`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Compared the consumer spec view (spec_view over model.py, impl regions elided) against the public problem_statement and the gold patch (rst.py: __init__ header_rows plumbing; write lines[1]->lines[idx] with idx=len(self.header.header_rows); read start_line 3 -> 2+len(self.header.header_rows)).

The spec view discloses only ABSTRACT, format-derivable behaviour: the RST layout has the closing rule at block offset n (frame_index(n)==n) and the first data row at n+2 (data_start_index(n)==n+2), both affine in the header-row count n. These are necessary correctness properties of ANY correct simple-RST renderer/reader for the multi-header-row feature that the problem_statement itself requests and illustrates (it shows the header_rows=['name','unit'] output framed by '=' rules and the TypeError). Stating the desired observable offsets is legitimate behavioural specification, not gold reconstruction.

The spec view does NOT leak the repo-specific edit beyond the public statement: it contains no repo symbols (self.header.header_rows, RST.write/RST.read, SimpleRSTData.start_line), no file/line, no method names, and crucially never states the PRE-patch constants (lines[1], start_line=3) as values an implementer could copy. The line 'pinning either to a constant is correct only for the single-header-row case' is a generic behavioural statement, not the specific constants 1/3. Row tags are abstract List[int]/PSeq[int].

All concrete repo-binding (idx=len(self.header.header_rows), start_line=3, lines[1], file:line) lives only in mapping.md / refinement.md, which are auditor artifacts, NOT part of the consumer spec view. The elided impl regions (# impl-start ... elided) hide the actual implementations.

Same-spec byte-identity of the impl-only-differing attack is a G-EQ/weakness concern, out of scope for the leakage gate. Conclusion: the spec view does not reveal the gold edit beyond what problem_statement already makes public.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.