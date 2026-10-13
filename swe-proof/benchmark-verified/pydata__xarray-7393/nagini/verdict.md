# P2 adversarial audit — pydata__xarray-7393

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
- **machine verdict:** same-spec exit 0 (spec byte-identical). Element-type postcondition (the patch's discriminator) matches the real callee EXACTLY: np.asarray(x,dtype=d).dtype is always d, and after None→declared defaulting equals effective_type(requested,declared); with requested=None result carries declared, never storage_type — verified in-container that int64-storage cast back to int32/int16/int8/float32 recovers the declared dtype and values [0,1] on the real xarray stack path. Value-preservation postcondition ToSeq(values)==ToSeq(level_values) is unconditional and thus stronger than real numpy on lossy casts (int8 overflow, float→int truncation confirmed), but mapping.md §2 explicitly scopes the value bijection to widening casts, the F2P path is lossless-by-construction (cast back to the declared type the values were widened from), and G-AX only exercises lossless cases. Divergence is entirely outside the modeled/tested domain and is a documented, sound abstraction boundary — spec does not drift from real repo behavior on any relevant input.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `mapping.md`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view regenerated via markers.spec_view over the NaginiBackend; sha256 = d1df977af28209358059e7c0f33e2ec2ae29ece08703c0da83319cb60db6861d, byte-identical to meta.region_hashes.spec_view. Leakage judged against the PUBLIC problem_statement ONLY (hints_text excluded — note hints_text DOES disclose the exact source location and a code sketch, but that is out of scope for this gate).

Gold edit (xarray/core/indexing.py, PandasMultiIndexingAdapter.__array__): hoist `if dtype is None: dtype = self.dtype`, then `return np.asarray(self.array.get_level_values(self.level).values, dtype=dtype)` instead of returning the promoted storage values.

Public problem_statement discloses: 'stack casts int32 dtype coordinate to int64'; expectation that creating a MultiIndex must NOT change the coordinate dtype (i4 must stay i4, not promote to i8); MVCE `ds['a'].values.dtype == ds.stack(b=('a',))['a'].values.dtype` should be True — which directly surfaces the declared-vs-promoted `.values.dtype` distinction.

Findings:
1. The spec view is fully abstracted over opaque integer type codes and a generic `materialize_level(requested, declared, storage_type, level_values) -> DenseArray`. It contains NO repo-specific identifiers: no `indexing.py`, `PandasMultiIndexingAdapter`, `__array__`, `self.dtype`, `np.asarray`, `get_level_values`, `stack`, `MultiIndex`. The impl region is elided ('implementation elided — supplied by the consumer'). The edit site/mechanism mapping lives only in the private mapping.md / refinement.md. A solver reading the spec view alone cannot locate the change site or reproduce the literal patch.
2. The behavioral content encoded — result dtype = requested-if-given-else-declared, and the storage_type code MUST NOT influence the result, values carried through unchanged — is exactly the DESIRED behavior already derivable from the public problem_statement (dtype must not change on stack; declared i4 vs promoted-.values i8). The `storage_type MUST NOT influence` clause restates the problem's own observed symptom, not a hidden mechanism. Encoding desired behavior is the legitimate job of a spec.
3. The `effective_type` requested/None case split mirrors the standard, public numpy `__array__(dtype=None)` protocol contract, stated abstractly; it does not disclose the edit beyond the problem statement.

No spec-view line reveals the gold edit's location (which file/class/method) or mechanism (default-dtype hoist + np.asarray application) beyond what the public problem_statement already implies. Concurs with meta G-LEAK (pass) and the recorded G-PANEL-3 (NO-LEAKAGE).

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
