"""properties.py — G-PBT falsification battery for scikit-learn__scikit-learn-14141 (lean).

PORTED from the nagini sibling (../nagini/properties.py), re-expressed against
this bundle's carrier. NOT a Lean module: a manifest the G-PBT gate executes.

The modeled function builds a name→version overview: an ORDERED association list
covering a fixed roster of library import-names, each paired with the version it
resolves to (a null marker when unresolvable). On this backend the contract is a
single load-bearing clause, an EXACT ORDERED-LIST equality:

    problem_spec_dependencyVersions result :=
      result = expectedDeps.map (fun m => (m, lookupVersion m))

where `expectedDeps` is the nine-name roster (its ninth member being the
parallelism/serialization helper the fix adds) and `lookupVersion` is the
UNCHANGED per-module resolver, declared `opaque` and used identically on both
sides — the proof consumes no property of it.

CARRIER NARROWING vs nagini. The nagini sibling modeled the result as a Python
dict, so its checks were order-INDEPENDENT membership/value clauses spread over
nine per-name `Ensures`, a no-spurious-keys `Forall`, and a `MustTerminate`
termination obligation. Here the single equality subsumes ALL of those at once:
it pins, in one predicate,
  * the key-SET (upper + lower bound: exactly the nine roster names, nothing
    dropped, nothing added), and
  * the ORDER of the keys (a fact nagini's dict model could not even state), and
  * each VALUE to its grounded resolution `lookupVersion m`.
So the nagini cases do not map one-to-one; each nagini clause becomes an ATTACK
ANGLE on the one equality. The ports below cover every angle the equality
defends, and the reordering angle is NEW — it exists only because this carrier
is ordered.

What each nagini case became (full disposition in the submit assessment):
  * `rival-omit-joblib`       -> ported (attacks the roster's lower bound at the
                                  discriminating ninth member; the F2P asserts it).
  * `rival-omit-matplotlib`   -> ported (attacks the lower bound at a pre-existing
                                  member; a P2P-side assertion).
  * `rival-spurious-key`      -> ported (attacks the upper bound: a tenth,
                                  non-roster key).
  * `pos-control-reordered`   -> INVERTED. On a dict this was a VERIFY (order does
                                  not matter). On an ordered list it is genuinely
                                  wrong, so it ships as a REJECT rival that
                                  attacks the ordering angle.
  * `pos-control-cheapest`    -> ported as `pos-map` (the cheapest honest impl;
                                  see the note on its degeneracy below), with
                                  `pos-foldl`/`pos-zip` carrying the actual
                                  different-shape duty.
  * `admiss-roster-constructible` -> PORTED as `admiss-f2p-point` (see below).
                                  An earlier form of this manifest recorded the
                                  case as "subsumed: no precondition exists to be
                                  too strong", reasoning from `binders=0`. That
                                  reason is WRONG, and the second audit replaced
                                  it with a landed case: on a total carrier the
                                  PRECOND-TOO-STRONG analogue is not a
                                  precondition at all, it is the OBLIGATION being
                                  unsatisfiable at exactly an F2P-shaped input.
                                  That is directly testable — and testable here —
                                  by discharging the obligation at that concrete
                                  point BY EVALUATION, as a `have`, before closing
                                  the frozen obligation verbatim.
  * `rival-diverge`           -> DROPPED as unwitnessable on this carrier. The
                                  second audit re-derived this with real builds
                                  rather than accepting the argument, because
                                  "no witness can be built" is the reason that has
                                  been measured wrong most often. What was found:
                                  a diverging body IS writable and IS rejected —
                                  `partial def spin : Nat -> List (String × Option
                                  String) := fun n => spin (n+1)` with the impl
                                  bound to `spin 0` is inside variant scope and
                                  fails to verify (exit 1, `unsolved goals ⊢ spin 0
                                  = [...]`). But the blocker is on the RIVAL side,
                                  not the gold side, which is what makes it fatal:
                                  BOTH witness forms fail against the rival ITSELF.
                                  Stated in shared vocabulary (a membership
                                  `congrArg` over the result) the rival build fails
                                  with `hk : ∃ x, ("joblib", x) ∈ spin 0` and
                                  `⊢ False` unclosed — `spin 0` never reduces, so
                                  nothing can be derived from it. Stated over
                                  `spin` itself, the rival build likewise leaves
                                  `⊢ False` unclosed, and on gold it fails as
                                  `Unknown identifier `spin`` — the syntactic,
                                  non-discriminating failure the gate screens for.
                                  A `List.length` projection was also tried; same
                                  result. So the case can only ever land
                                  `witness-unproven` (the half that must SUCCEED),
                                  which is a genuine carrier limit and not a proof
                                  difficulty. Recorded as a KNOWN HOLE in the spec,
                                  not as a vacuous class: an impl that diverges
                                  here is not rejected for diverging, and this
                                  bundle sets no `loom.semantics.termination` line
                                  at all (the frozen solution has none), so nothing
                                  discharges a termination obligation. Note also
                                  that the recorded divergence finding
                                  (the corpus-wide termination-semantics finding) is scoped to
                                  velvet `partial` bundles; lean is unaffected.
  * frame-mutation            -> VACUOUS (no inputs; referentially transparent).
  * AXIOM_TESTS               -> dropped (G-AX's lane, not this gate's).

NEW work with no nagini counterpart:
  * `rival-wrong-value` — an angle nagini's grounded-oracle note said had "no
    wrong echo that verifies". True on a dict of independent per-key values; but
    the ordered-equality here still lets a rival drop the resolution and emit a
    constant. Its witness must CONDITION on the opaque carrier.
  * every reject `witness` (checked to discriminate: elaborates against the
    rival, FAILS against the frozen solution).

ADDED BY THE INDEPENDENT AUDIT of this port (all claims below re-derived with
real builds, not inherited from the port):
  * `rival-misbind-value` — a rival storing a REAL resolution at every position
    but always of the same library. `rival-wrong-value` is refutable from the
    value's shape (it is the null marker); only this one forces the spec to pin
    the resolver's ARGUMENT to the name being recorded.
  * `pos-zip` — a third correct shape. `pos-map` turned out to be the spec's own
    right-hand side transcribed verbatim, hence definitionally equal to the pinned
    value and near-vacuous as soundness evidence; that degeneracy is now admitted
    in its comment and rationale rather than claimed as different-shape evidence.
  * four witnesses re-stated to name the member they discriminate at. The
    membership and upper-bound rivals were previously refuted by `List.length`
    (or by a whole-key-list equality), which attests only to "the wrong number of
    entries" / "the key sequence differs somewhere" — true of several rivals at
    once, and in particular NOT the clause the discriminator's rationale names.
  * three `refinement` claims corrected. The port asserted that the reorder,
    spurious-key and wrong-value rivals' faithful patches would not resolve. The
    harness tests were replayed against each rival's reported mapping: all three
    PASS every test, because every assertion is membership-only on the keys and
    none reads a value or an order. Those three cases are fidelity-to-gold probes
    of clauses the suite does not exercise — which is why the spec must carry
    them — and only the two omission rivals are genuinely test-failing. The
    over-claim is removed in each.
  * `rival-diverge`'s omission reason replaced: a diverging impl IS writable here
    (via a `partial def` helper in the impl region), so "the carrier cannot express
    it" was wrong; what blocks the case is that its refutation is unstatable in
    vocabulary gold and the rival share. See the disposition list above.

ADDED BY THE SECOND (INDEPENDENT) AUDIT — every claim below re-derived with real
builds in a private /tmp dir, exit codes recorded:
  * `admiss-f2p-point` LANDED. The previous manifest dropped the whole
    admissibility lane, reasoning from `binders=0` that "no precondition exists to
    be too strong". That is the specific reason the audit protocol rules out: on a
    total carrier the analogue is the obligation being unsatisfiable at an
    F2P-shaped input, which a positive that discharges it at that concrete point by
    evaluation tests directly. Built and it verifies (exit 0), so the lane was
    expressible and its omission was a real gap, not a vacuous class.
  * The two `True.symm` gold signatures were subjected to the FORGERY test rather
    than read. Flipping the claim (asserting the spec HOLDS) against the frozen
    solution builds with exit 0, while the witnesses' own gold builds are exit 1 —
    so gold's exit code does track the claim and the cases are not hollow. The
    type-revealing probe (`exact (h0 : Nat)`) prints `h0 has type True` on gold
    (i.e. `simp` PROVED the equation there) against `none = lookupVersion "pip"`
    and `lookupVersion "sklearn" = lookupVersion "pip"` on the two rivals. That
    pair is a genuine refutation.
  * The four membership/ordering witnesses were checked for DISCRIMINATION
    SENSITIVITY, not just outcome: re-stating each at a member the rival actually
    carries (`"pip"`) makes the RIVAL build fail (exit 1), and the joblib witness
    does not refute the matplotlib rival (which carries joblib). So the member each
    witness names is load-bearing, not decorative.
  * Five NEW wrong impls the battery did not contain were tried against the frozen
    spec (adjacent-transposition of two roster members, a duplicated discriminating
    member, values shifted one position so each name carries its neighbour's
    resolution, a misspelled discriminating key, and the empty result). All five are
    REJECTED — no spec hole found. Four NEW correct reshapes (a fully unrolled
    nine-pair literal, `foldr`, reverse-of-reversed-cons, and a recursive helper
    with its own equations) were tried; all four VERIFY, so the equality is not
    over-fit to a shape.
  * The divergence lane's omission reason was re-measured and REWRITTEN; see the
    disposition list. The conclusion (unwitnessable) survived, but the previous
    reason located the blocker on the gold side when it is on the rival side, and
    the class is a known spec HOLE rather than vacuous.

Authoring mechanics (nagini convention preserved): every variant is built by
region-surgery (`_swap`) that edits ONLY inside the `-- impl-start`/`-- impl-end`
region (positives also touch the `-- proof-start`/`-- proof-end` body), so
`same_spec` holds by construction and any rejection is attributable to the
postcondition, never to a tampered spec.
"""
from pathlib import Path

INSTANCE = "scikit-learn__scikit-learn-14141"
FLOAT_ENCODING = None

# --- base spec (frozen) ------------------------------------------------------
_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src: str, old: str, new: str) -> str:
    """Replace exactly one occurrence of an impl/proof-region substring; assert
    it matched so silent drift (Solution.lean edited) fails loudly at load."""
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Region landmarks — all strictly INSIDE the impl (or proof) region.
# ---------------------------------------------------------------------------

# The whole impl body (unique in the file).
_IMPL_BODY = """def implementation_dependencyVersions : List (String × Option String) := Id.run do
  let deps := expectedDeps
  let mut depsInfo : List (String × Option String) := []
  for modname in deps do
    depsInfo := depsInfo ++ [(modname, lookupVersion modname)]
  return depsInfo"""

# The roster-binding line (unique in the file; the loop iterates over `deps`).
_DEPS_BIND = "  let deps := expectedDeps"

# The per-name value expression (unique in the file).
_VALUE_EXPR = "[(modname, lookupVersion modname)]"

# The trailing return of the loop accumulator (unique in the impl region).
_RETURN = "  return depsInfo"

# The frozen proof body (unique in the file). Positives may edit inside the proof
# region; the theorem STATEMENT is never touched, so `same_spec` and the
# obligation-preservation rule both hold by construction.
_PROOF_BODY = """  unfold problem_spec_dependencyVersions implementation_dependencyVersions
  simp [expectedDeps]"""


# ===========================================================================
# POSITIVE CONTROLS (soundness) — expect "verify"
# ===========================================================================

# Replace the imperative `Id.run do`/`for` accumulator with a single `List.map`
# over the roster. Correct, and it must verify.
#
# ADMITTED DEGENERACY (audit note): this impl is the spec's own right-hand side
# transcribed verbatim, so its obligation closes by `rfl` after `unfold` and it is
# DEFINITIONALLY equal to the pinned value rather than merely observationally
# equal to it. It therefore tests the weakest thing a positive can test — that the
# spec admits its own literal witness — and would still verify against a spec
# arbitrarily over-fit to that one syntactic form. Kept because it is the honest
# cheapest impl (the role nagini's pos-control-cheapest played, whose point was
# that no answer-key echo is available), but it is NOT the different-shape
# soundness evidence; `pos-foldl` and `pos-zip` carry that, since each computes
# the ordered result by a genuinely different route and needs the spec to be
# insensitive to the shape.
_POS_MAP = _swap(
    _BASE, _IMPL_BODY,
    """def implementation_dependencyVersions : List (String × Option String) :=
  expectedDeps.map (fun m => (m, lookupVersion m))""")

# Structurally-different but CORRECT: pair the roster against the separately-mapped
# list of resolved versions with `List.zip`. Not definitionally the pinned
# `map`-of-pairs — the zip has to be computed down to it — so this is a real
# different-shape probe of the equality, added by the audit alongside `pos-foldl`
# because `pos-map` is definitionally degenerate (see above).
_POS_ZIP = _swap(
    _BASE, _IMPL_BODY,
    """def implementation_dependencyVersions : List (String × Option String) :=
  expectedDeps.zip (expectedDeps.map lookupVersion)""")

# Structurally-different but CORRECT: build the accumulator with an explicit
# `List.foldl` instead of a `for` loop. Same ordered result; must verify with
# the frozen proof body. A second independent correct shape defending the clause.
_POS_FOLDL = _swap(
    _BASE, _IMPL_BODY,
    """def implementation_dependencyVersions : List (String × Option String) :=
  expectedDeps.foldl (fun acc m => acc ++ [(m, lookupVersion m)]) []""")


# ===========================================================================
# ADMISSIBILITY (PRECOND-TOO-STRONG probe) — expect "verify"
# ===========================================================================

# The obligation here binds a single result and NO input, so there is no literal
# precondition to be too strong. The analogue on a TOTAL carrier is the obligation
# being UNSATISFIABLE at exactly an F2P-shaped input — which is a real failure mode
# and a testable one, so `binders=0` is not a licence to drop this lane.
#
# The probe: before closing the frozen obligation verbatim, discharge two `have`s
# BY EVALUATION at the F2P-shaped point — that the discriminating roster member is
# among the covered entries of the pinned mapping, and that the pinned mapping's
# key-sequence is exactly the nine-name roster in order. Both must reduce on their
# own, from `expectedDeps` alone, with no appeal to the impl. If the obligation
# were unsatisfiable at the very input the F2P asserts (an over-strong roster
# contract, a key-sequence the spec pins to something the fix cannot produce), the
# `have`s would not close and this case would fail => PRECOND-TOO-STRONG.
#
# Only the PROOF region is edited; the impl and the theorem statement are the
# frozen ones, so this case says something about the SPEC's satisfiability at that
# point rather than about any rival's shape.
_ADMISS_F2P = _swap(
    _BASE, _PROOF_BODY,
    """  have hf2p : ("joblib", lookupVersion "joblib") ∈
      expectedDeps.map (fun m => (m, lookupVersion m)) := by
    simp [expectedDeps]
  have hkeys : (expectedDeps.map (fun m => (m, lookupVersion m))).map Prod.fst
      = ["pip", "setuptools", "sklearn", "numpy", "scipy", "Cython", "pandas",
         "matplotlib", "joblib"] := by
    simp [expectedDeps]
  unfold problem_spec_dependencyVersions implementation_dependencyVersions
  simp [expectedDeps]""")


# ===========================================================================
# UNIQUENESS RIVALS (spec-too-weak probes) — expect "reject"
# ===========================================================================

# (DISCRIMINATOR — lower bound at the ninth member) Omit the parallelism helper:
# the eight-name pre-fix roster. The result is one element short, so the ordered
# equality cannot hold. Rejection source: the roster's lower bound at the
# discriminating member.
_RIVAL_OMIT_JOBLIB = _swap(
    _BASE, _DEPS_BIND,
    '  let deps := ["pip", "setuptools", "sklearn", "numpy", "scipy", "Cython",\n'
    '               "pandas", "matplotlib"]')

# (PARTIAL-DOMAIN — lower bound at a pre-existing member) Drop a long-standing
# roster member while keeping the discriminating one. Correct on eight of nine
# names but the ordered key-sequence differs. Rejection source: the lower bound
# at a pre-existing member.
_RIVAL_OMIT_MPL = _swap(
    _BASE, _DEPS_BIND,
    '  let deps := ["pip", "setuptools", "sklearn", "numpy", "scipy", "Cython",\n'
    '               "pandas", "joblib"]')

# (ORDERING — carrier-specific, NO nagini counterpart) All nine names, all
# correct values, but emitted in REVERSED order. On nagini's dict this VERIFIED
# (a dict is order-independent); on this ordered-list carrier the key-sequence
# differs from the roster's, so the equality fails. Rejection source: the
# ordering component of the equality — an angle only this carrier can state.
_RIVAL_REORDER = _swap(
    _BASE, _DEPS_BIND,
    '  let deps := ["joblib", "matplotlib", "pandas", "Cython", "scipy", "numpy",\n'
    '               "sklearn", "setuptools", "pip"]')

# (UPPER BOUND — no-spurious-keys) Populate all nine roster keys correctly AND
# append a tenth pair whose key is NOT a roster member. The result is one element
# too long, so the equality fails. Rejection source: the upper bound on the
# key-set.
_RIVAL_SPURIOUS = _swap(
    _BASE, _RETURN,
    '  depsInfo := depsInfo ++ [("threadpoolctl", lookupVersion "threadpoolctl")]\n'
    "  return depsInfo")

# (VALUE — grounded resolution; carrier-conditioned) Keep the exact roster and
# order, but drop the resolution: store the null marker for every name instead of
# `lookupVersion m`. Whenever any roster member actually resolves to a version,
# the rival disagrees with the spec at that position. Rejection source: the value
# component of the equality. Its witness CONDITIONS on the opaque resolver (it
# cannot be computed), asserting only that the first member resolves to something
# non-null — a single, satisfiable hypothesis.
_RIVAL_WRONG_VALUE = _swap(
    _BASE, _VALUE_EXPR, "[(modname, none)]")

# (VALUE — MIS-BINDING; added by the audit) Keep the exact roster, the exact order,
# and a genuinely RESOLVED version at every position — but resolve the SAME library
# at every position instead of the one being recorded. This attacks the angle
# `rival-wrong-value` leaves open: that rival is refutable by noticing the value is
# the null marker, i.e. by the value's SHAPE, so a spec that merely required each
# value to be *some* resolution would still reject it. This rival's every value is
# a real resolution, so only the requirement that each name carry the resolution of
# THAT name (the argument-binding, not just the value's provenance) can reject it.
# Its witness likewise conditions on the opaque resolver, at the weakest hypothesis
# that separates the two positions.
_RIVAL_MISBIND = _swap(
    _BASE, _VALUE_EXPR, '[(modname, lookupVersion "sklearn")]')


SPEC_TESTS = [
    # ---- positive controls (must VERIFY) ----
    {"id": "pos-map", "kind": "soundness", "expect": "verify",
     "module": _POS_MAP,
     "rationale": "structurally-different but correct: the imperative accumulating "
                  "loop is replaced by a single `List.map` over the roster, which is "
                  "exactly the value the equality pins. The frozen proof body closes it. "
                  "If it failed => SPEC-TOO-STRONG (over-fit to the loop's syntactic shape). "
                  "Ports nagini's pos-control-cheapest soundness intent onto this carrier "
                  "(the cheapest honest impl). It does NOT port nagini's "
                  "pos-control-reordered: on this ordered carrier reordering is genuinely "
                  "wrong, so that case inverted into `rival-reorder` in the reject lane."},
    {"id": "pos-zip", "kind": "soundness", "expect": "verify",
     "module": _POS_ZIP,
     "rationale": "third correct shape, added by the audit: pair the roster against the "
                  "separately-mapped list of resolved versions with `List.zip`. Unlike "
                  "`pos-map` this is NOT the spec's right-hand side transcribed — the zip must "
                  "be computed down to the pinned map-of-pairs — so it is genuine "
                  "different-shape evidence that the equality is not over-fit to one syntactic "
                  "form. If it failed => SPEC-TOO-STRONG."},
    {"id": "pos-foldl", "kind": "soundness", "expect": "verify",
     "module": _POS_FOLDL,
     "rationale": "second independent correct shape: build the accumulator with an "
                  "explicit `List.foldl` rather than a `for` loop. Same ordered result; must "
                  "verify with the frozen proof body. Defends the equality against a second "
                  "algorithmic form so a single-shape over-fit would be caught."},

    # ---- admissibility (must VERIFY) ----
    {"id": "admiss-f2p-point", "kind": "admissibility", "expect": "verify",
     "module": _ADMISS_F2P,
     "rationale": "PRECOND-TOO-STRONG probe, ported from nagini's "
                  "admiss-roster-constructible. The obligation binds no input, so there is "
                  "no literal precondition; the analogue on this total carrier is the "
                  "obligation being UNSATISFIABLE at an F2P-shaped input. This case "
                  "discharges it at exactly that point by EVALUATION, as two `have`s proven "
                  "from `expectedDeps` alone before the frozen obligation is closed "
                  "verbatim: that the discriminating roster member is among the covered "
                  "entries of the pinned mapping, and that the pinned key-sequence is the "
                  "nine-name roster in order. Both reduce without reference to the impl, so "
                  "they attest to the SPEC's satisfiability rather than to a proof script. "
                  "If either failed => PRECOND-TOO-STRONG (the contract cannot be met at "
                  "the very input the FAIL_TO_PASS asserts). Note `binders=0` is NOT a "
                  "reason to omit this lane; that was the earlier port's error."},

    # ---- uniqueness rivals (must be REJECTED, each with a discriminating witness) ----
    {"id": "rival-omit-joblib", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_OMIT_JOBLIB,
     "rationale": "the discriminator. Rejection source: the roster's lower bound at the "
                  "ninth (parallelism-helper) member — an eight-name result is one element "
                  "short of the pinned nine-element map, so the ordered equality fails. If it "
                  "verified => SPEC-TOO-WEAK (the discriminating membership is hollow).",
     "refinement": "this is the exact pre-fix behaviour: the roster omits the parallelism "
                   "helper, so that name never becomes a covered key. The FAIL_TO_PASS "
                   "asserts that name IS among the covered dependencies; the faithful pre-fix "
                   "patch fails that assertion and does NOT resolve. A verifying rival here "
                   "would be a true verify-does-not-imply-resolve break.",
     # Names the DISCRIMINATING member. An earlier form of this witness refuted
     # only via `congrArg List.length` — true, but a length count is satisfied by
     # ANY eight-element rival, so it attested to "one element short" rather than
     # to "the parallelism helper is missing", which is the clause the rationale
     # and the F2P actually name. This form derives that `"joblib"` is a covered
     # key under the assumed equality and contradicts it against the rival's own
     # key list, so the refutation is about the member the discriminator is about.
     "witness": """example : ¬ problem_spec_dependencyVersions implementation_dependencyVersions := by
  unfold problem_spec_dependencyVersions implementation_dependencyVersions
  intro h
  have hk := congrArg (fun l => "joblib" ∈ l.map Prod.fst) h
  simp [expectedDeps] at hk"""},

    {"id": "rival-omit-matplotlib", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_OMIT_MPL,
     "rationale": "partial-domain: correct on eight of the nine members (including the "
                  "discriminating one) but drops a long-standing member, so the ordered "
                  "key-sequence differs from the roster. Rejection source: the lower bound at "
                  "a pre-existing member. If it verified => SPEC-TOO-WEAK (domain-incomplete "
                  "on the long-standing roster).",
     "refinement": "the faithful real patch is a roster that omits a pre-existing dependency, "
                   "so that name is not a covered key — and a pre-existing (PASS_TO_PASS-side) "
                   "assertion checks that name IS present. That patch fails the suite and does "
                   "NOT resolve.",
     # Names the dropped member specifically, for the same reason as above: a
     # whole-key-list `congrArg` refutes "the key sequence differs somewhere",
     # which is also true of the reorder rival; this pins the refutation to the
     # ABSENT pre-existing member that the P2P-side assertion names.
     "witness": """example : ¬ problem_spec_dependencyVersions implementation_dependencyVersions := by
  unfold problem_spec_dependencyVersions implementation_dependencyVersions
  intro h
  have hk := congrArg (fun l => "matplotlib" ∈ l.map Prod.fst) h
  simp [expectedDeps] at hk"""},

    {"id": "rival-reorder", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_REORDER,
     "rationale": "ordering angle — has NO nagini counterpart (on a dict, reordering "
                  "verifies; here it is wrong). All nine names, all correct values, emitted "
                  "in reversed order: the key-sequence differs from the roster's, so the "
                  "ordered equality fails. Rejection source: the ordering component of the "
                  "equality. If it verified => SPEC-TOO-WEAK (order unconstrained).",
     "refinement": "the modeled contract requires the covered names in the roster's declared "
                   "order (the returned mapping preserves insertion order, mirroring the real "
                   "mapping type). A faithful patch that built the mapping in a different order "
                   "produces an overview whose iteration order — and therefore whose printed "
                   "report order — diverges from gold's, so it is not behaviourally equal to the "
                   "gold patch. HONEST NUANCE, measured rather than assumed: the harness tests "
                   "were replayed against this rival's reported mapping and all three PASS "
                   "(the assertions are membership-only, and the reporting test checks only that "
                   "certain substrings appear in the output, not their order). So this case, like "
                   "`rival-spurious-key`, is a fidelity-to-gold probe of an angle the ordered "
                   "carrier makes expressible, NOT a test-failing discriminator. Retained "
                   "because the frozen spec does pin order and a rival attacking that clause "
                   "must exist; not claimed to fail the suite.",
     # The whole-key-list refutation is the RIGHT shape here (unlike the two
     # membership rivals): this rival's key SET is exactly the roster's, so no
     # single-member statement can refute it. The refutation is genuinely about
     # the sequence, which is the angle this case owns.
     "witness": """example : ¬ problem_spec_dependencyVersions implementation_dependencyVersions := by
  unfold problem_spec_dependencyVersions implementation_dependencyVersions
  intro h
  have hk := congrArg (List.map Prod.fst) h
  simp [expectedDeps] at hk"""},

    {"id": "rival-spurious-key", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_SPURIOUS,
     "rationale": "exercises the upper bound: all nine roster keys correct, plus a tenth pair "
                  "whose key is not a roster member. The result is one element too long, so the "
                  "ordered equality fails. Rejection source: the upper bound on the key-set. If "
                  "it verified, the no-spurious-keys guarantee would be hollow.",
     "refinement": "a faithful patch adding a non-roster name to the covered list produces an "
                   "extra key, diverging from the gold roster (which has exactly the nine "
                   "entries). HONEST NUANCE (carried from nagini): the membership-only F2P "
                   "checks presence, not exact key-set, so a lenient extra-key patch could pass "
                   "the test; this case therefore probes the clause's FIDELITY to the exact gold "
                   "roster (behavioural equality with gold), a stronger property than the lenient "
                   "test enforces. Supporting case for the upper-bound angle. Re-checked by "
                   "replaying the three harness tests against this rival's reported mapping: the "
                   "F2P and both P2P tests all PASS on it, so the nuance above is not a hedge — "
                   "this case is provably NOT test-failing and earns its keep only as a "
                   "fidelity-to-gold probe. It is deliberately not counted among the "
                   "discriminators; `rival-omit-joblib` and `rival-omit-matplotlib` are the two "
                   "rivals whose faithful patches actually fail the suite.",
     # Names the non-roster key, rather than counting to ten: a length refutation
     # would equally refute any ten-element rival, including one whose extra key
     # IS a roster name. This pins the refutation to the specific spurious key.
     "witness": """example : ¬ problem_spec_dependencyVersions implementation_dependencyVersions := by
  unfold problem_spec_dependencyVersions implementation_dependencyVersions
  intro h
  have hk := congrArg (fun l => "threadpoolctl" ∈ l.map Prod.fst) h
  simp [expectedDeps] at hk"""},

    {"id": "rival-wrong-value", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_WRONG_VALUE,
     "rationale": "value angle: exact roster and order, but every value is the null marker "
                  "instead of the resolved version. Whenever a member actually resolves, the "
                  "rival disagrees at that position. Rejection source: the value component of "
                  "the equality (each key must carry its grounded resolution). If it verified "
                  "=> SPEC-TOO-WEAK (values unconstrained; a wrong echo passes). This attacks "
                  "an angle nagini's grounded-oracle note held was not echo-vulnerable on a "
                  "dict; on the ordered equality a constant-value rival is refutable.",
     "refinement": "a faithful patch that recorded a null/placeholder for every dependency "
                   "instead of resolving its installed version would report a wrong version for "
                   "every installed library — behaviourally unequal to gold, and the diagnostics "
                   "output it produces is wrong for every present dependency. HONEST NUANCE, "
                   "measured by replaying the three harness tests against this rival's reported "
                   "mapping: all three PASS, because every assertion is membership-only on the "
                   "keys and none inspects a value. So this rival's faithful patch is NOT "
                   "test-failing; it is a fidelity-to-gold probe of the value clause, which the "
                   "suite does not exercise at all. That gap in the suite is the reason the clause "
                   "must be defended here: the spec pins every value to its grounded resolution "
                   "where the test pins none of them. The witness conditions on the opaque "
                   "resolver because the value cannot be computed literally.",
     "witness": """example (h : lookupVersion "pip" ≠ none) :
    ¬ problem_spec_dependencyVersions implementation_dependencyVersions := by
  unfold problem_spec_dependencyVersions implementation_dependencyVersions
  intro heq
  have h0 := congrArg List.head? heq
  simp [expectedDeps] at h0
  exact h h0.symm"""},

    {"id": "rival-misbind-value", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_MISBIND,
     "rationale": "value angle at the ARGUMENT BINDING — added by the audit to close what "
                  "`rival-wrong-value` leaves unattacked. That rival stores the null marker "
                  "everywhere, so it is refutable from the value's SHAPE: a spec requiring only "
                  "that each name carry *some* resolution would already reject it. This rival "
                  "stores a genuine resolution at every position, but always of the SAME library "
                  "rather than of the name being recorded. So it can be rejected only by the "
                  "requirement that each key carry the resolution of THAT key — the binding of "
                  "the resolver's argument to the loop variable, which is the substance of the "
                  "value clause. Rejection source: the value component of the equality, at the "
                  "argument rather than at the marker. If it verified => SPEC-TOO-WEAK (the "
                  "resolver's argument is unconstrained, so a spec could be satisfied by "
                  "resolving one library nine times).",
     "refinement": "a faithful patch that resolved a single fixed library for every rostered "
                   "name would report that one library's version under all nine names — the "
                   "overview would be wrong for eight of the nine dependencies it claims to "
                   "describe, and it is plainly not behaviourally equal to gold. HONEST NUANCE, "
                   "measured the same way as the two cases above by replaying the harness tests "
                   "against its reported mapping: all three PASS, since the assertions are "
                   "membership-only on the keys and none reads a value. Like `rival-wrong-value` "
                   "this is therefore a fidelity-to-gold probe of a clause the suite does not "
                   "exercise, not a test-failing discriminator — which is exactly why the spec "
                   "has to carry it.",
     # Conditions on the opaque resolver at the weakest hypothesis that separates
     # the two positions: the first roster member must resolve to something other
     # than the library the rival resolves everywhere. Satisfiable (the gate's
     # consistency probe confirms `False` does not follow: an opaque function is
     # free to differ at two distinct arguments), and it FAILS against the frozen
     # solution, where the hypothesis is left untouched and the equality holds.
     "witness": """example (h : lookupVersion "pip" ≠ lookupVersion "sklearn") :
    ¬ problem_spec_dependencyVersions implementation_dependencyVersions := by
  unfold problem_spec_dependencyVersions implementation_dependencyVersions
  intro heq
  have h0 := congrArg List.head? heq
  simp [expectedDeps] at h0
  exact h h0.symm"""},
]
