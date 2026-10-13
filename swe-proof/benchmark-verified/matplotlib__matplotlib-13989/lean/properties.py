"""properties.py — G-PBT falsification battery for matplotlib__matplotlib-13989 (lean).

NOT a Lean file; a record of adversarial cases the G-PBT gate executes. Each SPEC
case is a full ``Solution.lean`` variant that shares the FROZEN spec byte-for-byte
(region surgery: only text inside the ``-- impl-start`` / ``-- impl-end`` region —
and, for a case that legitimately re-proves, inside ``-- proof-start`` /
``-- proof-end`` — is changed, so ``markers.same_spec`` holds and the single
``theorem correct_<name>`` STATEMENT stays byte-identical). ``expect:"verify"``
passes iff (in scope AND the file elaborates with the obligation closed);
``expect:"reject"`` passes iff (in scope AND it does NOT verify AND the case's
refutation ``witness`` holds of the rival while FAILING on the frozen solution).

PORT NOTE. This is a PORT of the nagini falsification battery
(``../nagini/properties.py``) onto this backend's carrier. The nagini bundle
models the assembly as a mapping from integer key TOKENS to integer values
(``Dict[int, int]`` plus two nullary key-identity constants) and states six
postcondition clauses over it, two of which are about the mapping's *shape*
(wellformedness, key-set upper bound). This Lean bundle models the same assembly
as a two-field record of optionals, so those two shape clauses are discharged by
the TYPE rather than by the postcondition, and the nagini cases attacking them
have no expressible counterpart here. Every nagini case that attacks a *value* or
a *presence* decision does port; the per-case mapping (and each principled
omission) is in the module ``assessment``.

The one nagini REJECT case with no counterpart here is its stray-key rival
(nagini ``rival-stray-key``, attacking its ``C6`` key-set upper bound), and the
reason is mechanical rather than a proof difficulty. Writing a third entry
requires a third FIELD on ``HistKeywordArgs``, and that structure is declared in
the ``pure`` region, which is INSIDE the spec view: adding the field makes
``same_spec`` fail, so such a variant is out of scope as a spec change rather
than a rival (measured: ``variant_problems`` reports "spec view differs"). The
clause it attacked is instead discharged by the type, and that is checkable
rather than merely claimed — ``example (h : HistKeywordArgs) :
h = { range := h.range, density := h.density } := rfl`` elaborates, i.e. every
inhabitant of the carrier IS exactly its two components, so no stray entry is
representable for any implementation to place. A rival cannot be written and no
rival is needed.

DEFENDED SURFACE (one modeled behavior, one obligation). A small keyword mapping
is assembled from four already-resolved option values: a flag selecting the path
that requests explicit bounds, the bounds themselves, a normalise-to-density
request, and a stacking flag. The result carries two independent optional
entries, and the postcondition pins each of them to a grounded computation over
the inputs, giving two INDEPENDENT top-level clauses:

  * (C-range)   the bounds entry is present exactly when the bounds-requesting
                path was taken, and then equal to the bounds that were passed in;
  * (C-density) the density entry is present exactly when a density result was
                requested AND the datasets are not stacked, and then equal to
                that request.

The BEHAVIOURAL DISCRIMINATOR (what the fix is about): the two entries are
assembled INDEPENDENTLY — placing the density entry must leave an already-placed
bounds entry exactly as it was. C-range is therefore load-bearing on precisely
the sub-domain where both entries are wanted, which is the scenario the F2P test
pins (bounds requested, density requested, not stacked: the reported bin edges
must span the requested interval exactly).

The nagini clause numbering maps onto these two as follows:
``C1`` (mapping wellformed) → discharged by the record type; ``C2``/``C3``
(bounds present-and-pinned / bounds absent) → the two halves of C-range;
``C4``/``C5`` (density present-and-pinned / density absent) → the two halves of
C-density; ``C6`` (key-set upper bound) → discharged by the record type.

ADVERSARIAL READ of the case classes on this carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS, and the nagini sibling already
    records it as N/A for its own reasons (every input is a primitive passed by
    value, so there is no caller-owned container to overwrite). On this backend
    it is vacuous a second time over: Lean is referentially transparent, so there
    is no read-only half-permission to abuse and no aliasing to exploit. No
    substitute is fabricated.

  * DIVERGENCE / NON-TERMINATION — VACUOUS here, and there is nothing to port:
    the nagini sibling carries no ``diverge-*`` / ``nonterm-*`` case, and this
    bundle sets no ``loom.semantics.termination`` option at all — the modeled
    behavior is a plain total Lean ``def`` whose termination the kernel checks by
    structural recursion, so the verifier is on the "total" side of that
    distinction and a diverging rival is genuinely rejected rather than
    vacuously accepted. Demonstrated rather than asserted: a rival replacing the
    assembly with a ``partial def`` self-loop IS admissible scope (measured:
    ``variant_problems`` empty) and IS rejected. What it cannot carry is a
    DISCRIMINATING witness, and the reason is structural rather than tactical.
    The looping helper is a name only the rival declares, so a witness stated
    over it is refused by ``witness_scope_problems`` as out-of-vocabulary (gold's
    failure would be an unknown identifier, not a satisfied spec); and a witness
    stated over the shared implementation name has to CONDITION on a projection
    of it, at which point the hypothesis is satisfied by the frozen solution too
    and the witness elaborates against gold as well (measured: both builds exit
    0, so it discriminates nothing). The class is therefore a KNOWN GAP in the
    reject lane's coverage of this carrier rather than a vacuous class: a
    diverging rival is refutable by the verifier but not attributable by a
    witness, so it is not shippable under the witness requirement. It costs the
    battery nothing here, because a ``partial`` self-loop returns no assembled
    mapping on any input and so is strictly dominated by the forward-nothing
    rival, which IS shipped with a discriminating witness.

  * UNGROUNDED-ORACLE ECHO — VACUOUS, exactly as the nagini sibling records.
    Both clauses are GROUNDED: each entry is pinned either to an actual input
    (the bounds, the density request) or to absence. The bundle declares no
    ``opaque`` callee and consumes no ``axiom``, so the whole carrier is
    transparent and there is no answer key an implementation could echo without
    doing the assembly. In its place the battery carries honest structural
    POSITIVE CONTROLS that must verify.

  * UNIQUENESS / PARTIAL-DOMAIN / VALUE — APPLIES, and is where every ported
    nagini rival lands: dropping the bounds entry when the density entry is
    placed (the reported behavior), placing the bounds entry on the sub-domain
    that must not carry it, altering the recorded bounds, recording the wrong
    density value, ignoring the stacking flag, and forwarding nothing at all.
    Two rivals in this lane are NEW on this carrier and have no nagini
    counterpart, because both attack a distinction the nagini model does not
    have: nagini's mapping stores an opaque integer under each key, whereas here
    the bounds are an ORDERED PAIR (attackable by permutation, with presence
    untouched) and each entry is an ``Option`` whose ``none`` is a distinct
    inhabitant from ``some false`` (so "absent" is attackable by
    "present-carrying-false", which under a key-presence model is not
    expressible at all).

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen tactic script is tuned to the frozen
form — so a rejection alone attributes nothing to the spec. Every
``expect="reject"`` case therefore carries a Lean snippet stating the spec
predicate directly at one CONCRETE input and refuting it. Each was checked by
hand, with real builds, to HOLD of its rival and to FAIL on the frozen solution,
so it discriminates rather than asserting a tautology. Every witness states its
refutation at literal inputs; none conditions on a carrier term, so none carries
hypotheses that could be jointly unsatisfiable.

The gold-side failure is a plain EVALUATION in every case: all four inputs are
literals (``Bool`` constructors and rational numerals), so the whole term
computes, and on the frozen solution the goal ``simp`` is left holding is the
bare ``⊢ False`` — the spec predicate reduced to ``True`` and the negation could
not be closed. That gold-side exit code is not merely plausible-looking but
CLAIM-TRACKING, which is the property that makes it evidence: flipping each
witness's claim (dropping the ``¬``, so the snippet asserts the spec HOLDS at
that point) inverts both builds — the flipped claim elaborates against the frozen
solution and fails against the rival — so the exit codes carry information about
what is being claimed and not about the shape of the file. Nothing here is stated
over an ``opaque`` term or a ``Rat`` division, the two constructs that make a
kernel reduction stall on this carrier, so no witness needs a
``witness_reference`` or a ``decide +kernel`` rewrite.

BINDER / POINT SPREAD. The postcondition has four input binders and the reject
witnesses move all four rather than fixing them at one convenient point:

  * the bounds-requesting flag takes BOTH settings (false only in the
    bounds-on-the-wrong-subdomain rival, true elsewhere) — necessary, because a
    rival that mishandled only the not-requested sub-domain would otherwise
    verify;
  * the bounds themselves take six DISTINCT values across the seven witnesses,
    including an asymmetric pair whose component order is what one rival gets
    wrong — necessary, because a rival that recorded the bounds under a
    permutation agrees with any spec probe that only checked presence;
  * the density request takes BOTH settings (false in the three rivals whose
    defect is visible with no density entry wanted at all, true in the four that
    need the density branch to fire);
  * the stacking flag takes BOTH settings (true only in the ignore-stacking
    rival, which is the sub-domain that flag exists to carve out).

The seven reject witnesses probe seven DISTINCT input points. Where two rivals
overlap in behavior, the NEAR-MISS is refuted at the point that separates it:
the forward-nothing rival is refuted with no density entry wanted, where the
drop-the-bounds rival agrees with the frozen solution, so each rival's rationale
names a sub-domain the manifest actually demonstrates. That agreement is not
merely asserted: each rival was built against the spec predicate at the point
its rationale claims it AGREES with the frozen solution, and elaborated there,
so no two rivals in this battery claim the same sub-domain.

The ABSENCE halves of the two clauses are attacked in both of the ways this
carrier distinguishes. The stacking rival places the density entry on the
stacked sub-domain (the guard's second conjunct); the ``none``-vs-``some false``
rival places it on the ``densityFlag = false`` sub-domain (the guard's first
conjunct) carrying ``false``, which is where a spec that had pinned only
``result.density ≠ some true`` instead of ``= none`` would let a rival through.
Without the second, the first conjunct of the density guard is unprobed in the
reject lane and the ``Option`` carrier's own collapse trap goes untested.

AXIOM lane: DROPPED. The nagini sibling's two ``AXIOM_TESTS`` probes belong to
G-AX (this bundle declares no ``opaque`` callee and consumes no ``axiom``, so the
lane is a skip stub there); this gate ignores them.
"""
from pathlib import Path

INSTANCE = "matplotlib__matplotlib-13989"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- region anchors (each unique inside Solution.lean; verified at load) ----
# Every anchor lies ENTIRELY inside the impl region, except _P_FROZEN which lies
# entirely inside the proof region, so same_spec stays byte-identical and the
# obligation statement is never touched.

# The whole assembly body of the impl.
_I_BODY = (
    "  let mut hk : HistKeywordArgs := { range := none, density := none }\n"
    "  if setRange then\n"
    "    hk := { hk with range := some binRange }\n"
    "  if densityFlag && !stacked then\n"
    "    hk := { hk with density := some densityFlag }\n"
    "  return hk"
)

# The guarded bounds-entry write.
_I_RANGE_WRITE = (
    "  if setRange then\n"
    "    hk := { hk with range := some binRange }\n"
)

# The guarded density-entry write (the site the reported behavior is about).
_I_DENSITY_WRITE = (
    "  if densityFlag && !stacked then\n"
    "    hk := { hk with density := some densityFlag }\n"
)

# The frozen proof body (proof region).
_P_FROZEN = (
    "  intro setRange binRange densityFlag stacked\n"
    "  unfold problem_spec_assembleHistKeywordArgs implementation_assembleHistKeywordArgs\n"
    "  cases setRange <;> cases densityFlag <;> cases stacked <;> exact ⟨rfl, rfl⟩"
)

# Every witness opens the same way: state the spec predicate at a literal input
# applied to the implementation's own result, then reduce. The inputs are Bool
# literals and rational literals, so the whole term computes and `simp` closes
# the negation by constructor clash / literal clash — no opaque term is involved
# anywhere in this carrier.
_W_HEAD = "  unfold problem_spec_assembleHistKeywordArgs implementation_assembleHistKeywordArgs\n"


def _witness(setRange, binRange, densityFlag, stacked, note, tactic="  simp\n"):
    args = f"{setRange} {binRange} {densityFlag} {stacked}"
    return (
        note
        + f"example : ¬ problem_spec_assembleHistKeywordArgs {args}\n"
        + f"    (implementation_assembleHistKeywordArgs {args}) := by\n"
        + _W_HEAD
        + tactic
    )


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # implementations that MUST verify. If a faithful correct implementation
    # cannot satisfy the frozen obligation, the spec is SPEC-TOO-STRONG. Each
    # keeps the theorem statement byte-identical and re-proves with the frozen
    # tactic body (the reshapes preserve the definitional form, so the
    # case-split-then-`rfl` script still closes): no helper lemma, no axiom, no
    # assumption token introduced.
    # =====================================================================
    {
        # Ports nagini case `pos-reorder-correct` (Pos-control 1).
        "id": "pos-reorder-correct",
        "kind": "soundness",
        "expect": "verify",
        # Place the density entry FIRST, then the bounds entry. Both writes are
        # independent single-field updates, so the bounds entry still survives
        # and the assembled record is identical on every input.
        "module": _swap(
            _BASE, _I_BODY,
            "  let mut hk : HistKeywordArgs := { range := none, density := none }\n"
            "  if densityFlag && !stacked then\n"
            "    hk := { hk with density := some densityFlag }\n"
            "  if setRange then\n"
            "    hk := { hk with range := some binRange }\n"
            "  return hk",
        ),
        "rationale": "a structurally-different CORRECT implementation: the two "
                     "entries are placed in the opposite order. Both are "
                     "independent single-field updates, so each clause still "
                     "holds on every input and BOTH C-range and C-density must "
                     "still be provable — else the independence the spec demands "
                     "is stated in an order-dependent way, i.e. SPEC-TOO-STRONG. "
                     "Ports nagini's branch-reorder positive control. Proof: the "
                     "frozen tactic body is retained; after the case split on the "
                     "three flags both components reduce by `rfl` exactly as "
                     "before.",
    },
    {
        # Ports nagini case `pos-locals-correct` (Pos-control 2).
        "id": "pos-locals-correct",
        "kind": "soundness",
        "expect": "verify",
        # Hoist both branch conditions into typed local booleans before the
        # writes. Same writes, different executable shape.
        "module": _swap(
            _BASE, _I_BODY,
            "  let recordRange : Bool := setRange\n"
            "  let recordDensity : Bool := densityFlag && !stacked\n"
            "  let mut hk : HistKeywordArgs := { range := none, density := none }\n"
            "  if recordRange then\n"
            "    hk := { hk with range := some binRange }\n"
            "  if recordDensity then\n"
            "    hk := { hk with density := some densityFlag }\n"
            "  return hk",
        ),
        "rationale": "honest cheapest/structural positive control: both branch "
                     "conditions are hoisted into typed local booleans (a "
                     "local-variable reshape, not a different algorithm). The "
                     "assembled record is identical on every input, so both "
                     "clauses must still be provable; must verify. Ports nagini's "
                     "hoisted-locals positive control, which doubles there as the "
                     "cheapest-implementation control since there is no "
                     "ungrounded oracle to echo — the same is true here. Proof: "
                     "the frozen tactic body is retained (the locals "
                     "zeta-reduce).",
    },

    # =====================================================================
    # ADMISSIBILITY — the frozen obligation carries NO precondition hypothesis
    # (the modeled behavior is total, so the `∀` is unguarded), so nagini's
    # precondition-admission probe has no binder to attack on this carrier. The
    # honest analogue is to show the obligation is SATISFIABLE at the concrete,
    # F2P-shaped input rather than only in the abstract: bounds requested,
    # density requested, not stacked — the reported scenario.
    # =====================================================================
    {
        # Ports nagini case `admiss-f2p-shaped`.
        "id": "admiss-f2p-shaped",
        "kind": "admissibility",
        "expect": "verify",
        # Discharge the spec predicate at the ground F2P-shaped input as a `have`
        # inside the existing tactic body, then close the frozen obligation
        # verbatim. Nothing is assumed: no new declaration, no new axiom, the
        # theorem statement is byte-identical.
        "module": _swap(
            _BASE, _P_FROZEN,
            "  have _ground : problem_spec_assembleHistKeywordArgs true (0, 1) true false\n"
            "      (implementation_assembleHistKeywordArgs true (0, 1) true false) :=\n"
            "    ⟨rfl, rfl⟩\n"
            + _P_FROZEN,
        ),
        "rationale": "the obligation is discharged at the ground F2P-shaped input "
                     "(bounds requested with the reported interval, a density "
                     "result requested, not stacked — the point where BOTH "
                     "entries are wanted and where the two clauses interact) and "
                     "then closed verbatim in the abstract. It verifies only if "
                     "the modeled behavior is satisfiable at exactly the input "
                     "the F2P test exercises; if it could not, the spec would be "
                     "unsatisfiable there — the analogue of nagini's "
                     "PRECOND-TOO-STRONG finding, which is what its self-call "
                     "admissibility probe tests. Nothing is assumed: the ground "
                     "instance is a `have` in the existing tactic body and the "
                     "statement is untouched.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong implementations sharing the
    # frozen spec that MUST be rejected. Each carries (a) the refinement
    # argument that its faithful real patch would NOT resolve the F2P, so a
    # verifying rival would be a true verify-does-not-imply-resolve break rather
    # than an artifact, and (b) a refutation witness pinning the violation at one
    # concrete input, seen to hold of the rival and fail on the frozen solution.
    # =====================================================================

    {
        # Ports nagini case `rival-rebind-drop` (Rival B) — the reported behavior.
        "id": "rival-rebind-drop",
        "kind": "uniqueness",
        "expect": "reject",
        # Placing the density entry REPLACES the whole mapping with a fresh one
        # carrying only that entry, discarding a bounds entry placed above.
        "module": _swap(
            _BASE, _I_DENSITY_WRITE,
            "  if densityFlag && !stacked then\n"
            "    hk := { range := none, density := some densityFlag }\n",
        ),
        "refinement": "this IS the reported behavior: on the sub-domain where a "
                      "density result is requested and the datasets are not "
                      "stacked, the whole keyword mapping is replaced rather than "
                      "extended, so explicit bounds requested by the caller never "
                      "reach the counting routine. Its faithful real patch is the "
                      "unfixed tree, and the F2P test asserts that with bounds "
                      "requested AND a density result requested the reported bin "
                      "edges span the requested interval exactly — which they do "
                      "not once the bounds entry is discarded. So the faithful "
                      "patch does NOT resolve.",
        "rationale": "REJECT from C-range on the sub-domain where both entries are "
                     "wanted: the spec pins the bounds entry to `some binRange` "
                     "whenever the bounds-requesting path was taken, regardless of "
                     "whether a density entry was also placed, and the rival "
                     "leaves it absent there. This is the discriminating clause. "
                     "Binder spread: bounds requested, bounds (0,1) (the reported "
                     "interval), density requested, not stacked.",
        "witness": _witness(
            "true", "(0, 1)", "true", "false",
            "-- Refuted at the reported scenario: bounds requested with the\n"
            "-- reported interval AND a density result requested, not stacked.\n"
            "-- The bounds entry is absent where the spec pins it present, which\n"
            "-- is a constructor clash on fully concrete inputs.\n",
        ),
    },
    {
        # Ports nagini case `rival-range-always` (Rival C).
        "id": "rival-range-always",
        "kind": "uniqueness",
        "expect": "reject",
        # Place the bounds entry UNCONDITIONALLY, including on the path that
        # must not carry it.
        "module": _swap(
            _BASE, _I_RANGE_WRITE,
            "  hk := { hk with range := some binRange }\n",
        ),
        "refinement": "a faithful real patch that placed the bounds entry on every "
                      "path would forward explicit bounds even on the path that "
                      "has already resolved the bin edges itself, where the "
                      "counting routine is handed an explicit edge sequence: the "
                      "bounds are then either rejected as conflicting or silently "
                      "ignored, mis-binning that path. It also does not deliver "
                      "the fix — the F2P scenario runs on the OTHER path, where "
                      "this rival still discards the bounds entry the moment the "
                      "density entry is placed. So the faithful patch does NOT "
                      "resolve, and it breaks a path that currently works.",
        "rationale": "REJECT from the other half of C-range: the spec pins the "
                     "bounds entry ABSENT when the bounds-requesting path was not "
                     "taken, and the rival records it anyway. Partial-domain "
                     "attack — the rival agrees with the frozen solution wherever "
                     "bounds were requested, so it is refutable ONLY at the "
                     "not-requested point, which is the only witness in the "
                     "battery that moves that binder to false. Ports nagini's "
                     "multi-dataset-sub-domain attack.",
        "witness": _witness(
            "false", "(1 / 2, 3 / 2)", "true", "false",
            "-- Refuted on the sub-domain the rival gets wrong: the\n"
            "-- bounds-requesting path was NOT taken, so the spec pins the bounds\n"
            "-- entry absent and the rival records it. Distinct bounds value from\n"
            "-- every other witness, and the only point with that flag false.\n",
        ),
    },
    {
        # Ports nagini case `rival-wrong-density-value` (Rival D).
        "id": "rival-wrong-density-value",
        "kind": "uniqueness",
        "expect": "reject",
        # Place the density entry, but carrying the negation of the request
        # instead of the request itself.
        "module": _swap(
            _BASE, _I_DENSITY_WRITE,
            "  if densityFlag && !stacked then\n"
            "    hk := { hk with density := some (!densityFlag) }\n",
        ),
        "refinement": "a faithful real patch that recorded the negation of the "
                      "request would hand the counting routine an explicit "
                      "instruction NOT to normalise, on exactly the path where "
                      "the caller asked for a normalised result: raw counts come "
                      "back and the requested normalisation is silently dropped. "
                      "The F2P scenario requests a density result, so the "
                      "faithful patch does NOT resolve, and the other "
                      "density-related behaviors break with it.",
        "rationale": "REJECT from the VALUE half of C-density: the spec pins the "
                     "density entry equal to the request itself on the "
                     "requested-and-not-stacked sub-domain, and the rival records "
                     "its negation. Attacks the value rather than the presence, so "
                     "it is a near-miss that any presence-only probe would miss. "
                     "Binder spread: bounds requested with a third distinct "
                     "interval, density requested, not stacked.",
        "witness": _witness(
            "true", "(-1, 2)", "true", "false",
            "-- Refuted where the density entry is wanted: the entry is PRESENT\n"
            "-- but carries the opposite value to the one the spec pins it to, so\n"
            "-- the clash is at the value, not the presence. Bounds value distinct\n"
            "-- from every other witness (and negative, exercising the sign).\n",
        ),
    },
    {
        # Ports nagini case `rival-ignore-stacked` (Rival E).
        "id": "rival-ignore-stacked",
        "kind": "uniqueness",
        "expect": "reject",
        # Place the density entry whenever a density result is requested,
        # ignoring the stacking flag entirely.
        "module": _swap(
            _BASE, _I_DENSITY_WRITE,
            "  if densityFlag then\n"
            "    hk := { hk with density := some densityFlag }\n",
        ),
        "refinement": "a faithful real patch that dropped the not-stacked "
                      "condition would forward the normalise-to-density request "
                      "even while the datasets are being stacked, so each dataset "
                      "is normalised on its own instead of the stack being "
                      "normalised as a whole: the stacked-density behavior is "
                      "wrong. It also does not deliver the fix (the F2P scenario "
                      "is not stacked, and on that path this rival still discards "
                      "the bounds entry). So the faithful patch does NOT resolve, "
                      "and it regresses the stacked path.",
        "rationale": "REJECT from the ABSENCE half of C-density: the spec pins the "
                     "density entry absent unless the request is made AND the "
                     "datasets are not stacked, and the rival records it on the "
                     "stacked sub-domain too. Partial-domain attack on exactly the "
                     "sub-domain the stacking flag exists to carve out; the only "
                     "witness in the battery that moves that binder to true, so "
                     "without it a rival mishandling only stacking would verify "
                     "unnoticed. Ports nagini's stacked-sub-domain attack.",
        "witness": _witness(
            "false", "(0, 10)", "true", "true",
            "-- Refuted on the stacked sub-domain: a density result is requested\n"
            "-- but the datasets ARE stacked, so the spec pins the density entry\n"
            "-- absent and the rival records it. The only witness with the\n"
            "-- stacking flag set, and a fourth distinct bounds value.\n",
        ),
    },
    {
        # NEW on this carrier (no nagini counterpart): nagini models presence as
        # key-membership in a dict, where "absent" has no near-miss — a key is in
        # or out. Here each entry is an `Option`, so `none` and `some false` are
        # DISTINCT inhabitants and "absent" can be attacked by
        # "present-carrying-false" without ever placing a `some true`.
        "id": "rival-density-present-false",
        "kind": "uniqueness",
        "expect": "reject",
        # Place the density entry UNCONDITIONALLY, carrying the request itself.
        # On the sub-domain where no density result is requested that records
        # `some false` where the spec pins `none`.
        "module": _swap(
            _BASE, _I_DENSITY_WRITE,
            "  hk := { hk with density := some densityFlag }\n",
        ),
        "refinement": "a faithful real patch that always placed the density "
                      "entry would forward an explicit normalise-to-density "
                      "instruction on every path, including the paths where the "
                      "caller asked for nothing of the kind. The counting "
                      "routine then receives an option it was never meant to "
                      "receive, so the plain-count behaviours are handed an "
                      "explicit setting instead of the default and the callers "
                      "that rely on the option being absent change shape. It "
                      "also does not deliver the fix: the F2P scenario requests "
                      "a density result, and on that path this rival still "
                      "discards the bounds entry exactly as the unfixed tree "
                      "does. So the faithful patch does NOT resolve, and it "
                      "perturbs every non-density path as well.",
        "rationale": "REJECT from the ABSENCE half of C-density, on the FIRST "
                     "conjunct of its guard: the spec pins the density entry to "
                     "`none` unless a density result is requested, and the rival "
                     "records it PRESENT carrying `false`. This is the one attack "
                     "the `Option` carrier makes possible and a key-presence "
                     "model cannot express, and it is the carrier's own collapse "
                     "trap: a spec that had pinned the entry merely to `≠ some "
                     "true` on this sub-domain would accept this rival, and only "
                     "a witness distinguishing `none` from `some false` catches "
                     "that. Distinct from the ignore-stacking rival, which "
                     "attacks the SECOND conjunct of the same guard and agrees "
                     "with the frozen solution wherever no density result is "
                     "requested. Sixth distinct bounds value; the bounds are "
                     "requested at the witness point, so C-range is satisfied "
                     "there and the refutation is attributable to C-density "
                     "alone.",
        "witness": _witness(
            "true", "(3, 4)", "false", "false",
            "-- Refuted where NO density result is requested: the spec pins the\n"
            "-- density entry ABSENT there, and the rival records it PRESENT\n"
            "-- carrying `false`. `none` and `some false` are distinct\n"
            "-- inhabitants of `Option Bool`, so this is the point that separates\n"
            "-- 'absent' from 'present and negative' — a distinction no other\n"
            "-- witness in the battery exercises. Bounds are requested here, so\n"
            "-- C-range holds at this point and only C-density can be at fault.\n",
        ),
    },
    {
        # NEW on this carrier (no nagini counterpart): nagini models the bounds
        # as a single opaque integer token, so its value pinning has no internal
        # structure to permute. Here the bounds are an ORDERED PAIR, so the
        # pinning can be attacked without changing presence at all.
        "id": "rival-bounds-order-swapped",
        "kind": "uniqueness",
        "expect": "reject",
        # Record the bounds with their two components exchanged.
        "module": _swap(
            _BASE, _I_RANGE_WRITE,
            "  if setRange then\n"
            "    hk := { hk with range := some (binRange.2, binRange.1) }\n",
        ),
        "refinement": "a faithful real patch that recorded the requested bounds "
                      "with lower and upper exchanged would hand the counting "
                      "routine an inverted interval, which it rejects outright "
                      "(the upper bound must exceed the lower). The F2P scenario "
                      "requests bounds, so the faithful patch raises instead of "
                      "reporting edges spanning the interval: it does NOT resolve "
                      "— and every other behavior that requests bounds breaks too.",
        "rationale": "REJECT from the VALUE half of C-range: the spec pins the "
                     "bounds entry equal to the bounds that were passed in, and "
                     "the rival records a permutation of them. This is the rival "
                     "that makes the bounds binder load-bearing: it is PRESENT "
                     "exactly where the spec says, so any probe checking only "
                     "presence — or checking a symmetric interval — would accept "
                     "it. Refuted at an asymmetric interval, with no density entry "
                     "wanted, so the refutation is attributable to the bounds "
                     "value alone.",
        "witness": _witness(
            "true", "(0, 1)", "false", "false",
            "-- Refuted at an ASYMMETRIC interval with no density result\n"
            "-- requested, so nothing but the recorded bounds value can be at\n"
            "-- fault. A symmetric interval would NOT discriminate here, which is\n"
            "-- why this witness pins an ordered pair with distinct components.\n",
            tactic="  simp\n",
        ),
    },
    {
        # Ports nagini case `rival-empty` (Rival F) — the cheap supporting
        # near-miss, refuted at the point that separates it from the rival above.
        "id": "rival-empty",
        "kind": "uniqueness",
        "expect": "reject",
        # Forward nothing at all: both entries always absent.
        "module": _swap(
            _BASE, _I_BODY,
            "  let hk : HistKeywordArgs := { range := none, density := none }\n"
            "  return hk",
        ),
        "refinement": "a faithful real patch that forwarded no options at all "
                      "would let neither the requested bounds nor the density "
                      "request reach the counting routine, so the F2P scenario "
                      "reports neither the requested interval nor a normalised "
                      "result, and every option-forwarding behavior of the "
                      "surrounding call regresses. It does NOT resolve.",
        "rationale": "REJECT from both clauses at once (bounds absent where "
                     "required, density absent where required). Cheap supporting "
                     "near-miss; it never substitutes for the reasoned attacks "
                     "above, and it is deliberately refuted at a point where the "
                     "drop-the-bounds rival AGREES with the frozen solution — "
                     "bounds requested but NO density result requested, so the "
                     "density branch never fires — so the two rivals do not share "
                     "a sub-domain claim. Fifth distinct bounds value; the second "
                     "witness with the density request unset.",
        "witness": _witness(
            "true", "(2, 5)", "false", "false",
            "-- Refuted where the density branch never fires: bounds are\n"
            "-- requested and no density result is. The drop-the-bounds rival is\n"
            "-- CORRECT at this point, so this witness demonstrates the strictly\n"
            "-- larger sub-domain on which forwarding nothing is wrong.\n",
        ),
    },
]
