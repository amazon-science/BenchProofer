"""properties.py — G-PBT falsification battery for django__django-11490 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed —
both of which the consumer spec view elides, so ``markers.same_spec`` holds and
the ``prove_correct applyProjection`` obligation survives) and swaps in a
candidate implementation. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness must ELABORATE against the rival and FAIL
against the frozen solution).

DEFENDED SURFACE (one contracted method):

  applyProjection (mut persistent : Carrier) (mut recorded : Bool)
      (requested : List String) (projected : List String)
      return (working : Carrier)
    require shouldProject persistent requested = true ->
      answerable persistent projected = true
    ensures persistent = persistentOld                     -- (F) FRAME
    ensures shouldProject persistentOld requested = false
      -> recorded = recordedOld                             -- (R1) NO RECORD
    ensures shouldProject persistentOld requested = true
      -> recorded = true                                    -- (R2) DOES RECORD
    ensures working =
      workingCarrier persistentOld requested projected      -- (W) VALUE

One step of reconciling a single SHARED constituent carrier with the projection
an outer request wants every constituent to carry. A ``Carrier`` carries its
SELECTION in THREE parts that move together — ``columns`` (the explicit column
list it names of its own model), ``sideSelected`` (which of the side outputs
carried alongside its model are part of that selection) and ``auxSelected``
(which of the auxiliary outputs computed for it are part of that selection) —
plus two observations describing its MODEL, ``auxAvailable`` and ``ownFields``,
which reconciling a projection never alters. Recording a projection overwrites
ALL THREE selection parts at once, which is why restoring only some of them does
not put the carrier back as it was. The split reads the selection the carrier
ALREADY carries, not what its model is able to supply, so a non-column output
that is available but unselected is no part of it. It consults the two records
of selected non-column outputs IN ORDER, side outputs FIRST: a name carried in
BOTH records is kept only as a side output and is dropped from the auxiliary
record, so the two records cannot both retain it. Recording an EMPTY projection
is a separate leg, which leaves BOTH records alone and fills the explicit column
list with every column the carrier's own model defines.

FOUR INDEPENDENT TOP-LEVEL CONCERNS over four clauses, all load-bearing and all
attacked below:

  * (F) the FRAME. ``persistent`` is declared ``mut`` and pinned to its entry
    value — EVERY observation of it, all three parts of the selection and both
    parts of the model description, not the explicit column list alone. This is the
    clause that forbids reconciling the shared carrier in place, and it is what
    leaves a later assembly of the same compound request free to project a
    different column list. Because the frame pins the whole carrier, a rival
    that records onto the shared carrier and then writes back only PART of what
    recording moved is caught here (``weak-clobber-carrier-model``).
  * (R1)+(R2) the RECORDING ACCOUNTING. ``recorded`` says whether this step has
    recorded a pushed-down projection onto ANY constituent carrier. The two
    clauses pin the recording to happen EXACTLY on the push-down. This is the
    concern neither (F) nor (W) can express: a rival can satisfy the frame and
    the value on the WHOLE domain and still record where it must not, or
    nowhere at all (``weak-install-then-restore``, ``weak-never-record``). How
    MANY times it is recorded where the push-down applies is deliberately NOT
    pinned — recording once and twice are equally correct, so an exact-count
    clause would be over-fitting.
  * (W) the VALUE. ``working`` is pinned to the fully-unfolded pure model
    ``workingCarrier`` (the ``axioms`` region is empty — there is no opaque
    answer key to echo). It composes two sub-domains: PUSH-DOWN FIRES (carrier
    names no columns, ``requested`` non-empty) and DOES NOT FIRE. The two
    request observations are INDEPENDENT — the guard reads ``requested`` while
    the recorded selection reads ``projected`` — so a rival can get one right
    and the other wrong (``weak-guard-on-projected``). Within the firing
    branch the SELECTION SPLIT is pinned in shape, content and order
    (``weak-no-aux-split``, ``weak-swapped-aux-split``,
    ``weak-permute-projection``, ``weak-drop-last-column``), it is pinned to
    the OBSERVATION it reads — the selection the carrier already carries, not
    the non-column outputs its model could supply (``weak-key-on-available``) —
    BOTH records of selected non-column outputs are pinned rather than one
    (``weak-collapse-side-into-aux``) and so is the PRECEDENCE between them
    (``weak-ignore-record-precedence``), and BOTH legs are pinned, the empty
    projection as well as the general one (``weak-empty-projection-blanks``).
  * the ``require``. A carrier can only absorb a projection whose every name it
    can answer — a column its own model defines, or a non-column output either
    of its two selection records already carries — so the step is asked only
    about such a push-down. Both records count here on equal terms: the
    precedence decides only WHERE an answerable name is kept, never whether it
    can be answered. This bounds the claim to the domain where the real behaviour is
    total; it is not a dodge, and the reject lane drives ten distinct input
    points inside it.

THREE INPUT BINDERS beyond the ledger: ``persistent`` (a ``Carrier``),
``requested`` and ``projected``. All are load-bearing, and the reject witnesses
drive them to ten distinct points so no binder is pinned at one value across
the reject set: carriers that name no columns and carriers that already name
``["num"]``; carriers with and without an auxiliary output available;
``requested`` empty (the sub-domain where the push-down must NOT fire),
singleton and two-column, including a permutation point that holds length and
membership fixed so ORDER alone is at stake; carriers carrying a selected
non-column output in the side record only, in the auxiliary record only, and in
BOTH at once (the precedence point); and ``projected`` non-empty while
``requested`` is EMPTY, the point that separates the two request observations.

CARRIER NOTE — reaching the post-image. The spec is a ``method`` CONTRACT, so
each witness goes through Velvet's own tester machinery:
``applyProjectionTester persistent recorded requested projected = false`` says
the extracted program's observable result violates the method's postcondition
at that concrete input. It is checked in a file whose ``prove_correct`` block
has been stripped, so no tactic script can mask the verdict, and every argument
is a concrete literal so ``decide`` reduces the extracted program without
getting stuck — the carrier is fully transparent (a structure of plain string
lists with ``DecidableEq``, four pure ``def``s, no ``opaque`` term anywhere), so
no witness conditions on a hypothesis and none binds anything. All witness
halves were run with ``scripts/lean_verify.sh``: every witness elaborates green
against its rival and is REFUTED against the frozen solution (``Tactic `decide`
proved that the proposition ... is false``).
"""
from pathlib import Path

INSTANCE = "django__django-11490"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Anchors. Each lies ENTIRELY inside a region the consumer spec view elides (the
# impl region, or the `prove_correct` tactic body) and is asserted unique in the
# frozen file at import time, so this manifest breaks loudly if the frozen
# solution ever drifts.
# ---------------------------------------------------------------------------

_IMPL_BODY = """    let mut working := persistent
    if shouldProject persistent requested then
      recorded := true
      working := recordOnto persistent projected
      return working
    else
      return working"""
assert _BASE.count(_IMPL_BODY) == 1, "impl-body anchor drift — re-sync _IMPL_BODY"

_IMPL_START = "    -- impl-start\n"
assert _BASE.count(_IMPL_START) == 1, "impl-start anchor drift"

_PROOF_GOLD = """prove_correct applyProjection by
  loom_solve
  all_goals simp_all [workingCarrier, shouldProject, recordOnto]"""
assert _BASE.count(_PROOF_GOLD) == 1, "proof anchor drift"

# A bare proof body. When the impl is a single expression there is no residual
# branch goal for the `simp_all` arm to close, and the frozen script then errors
# with `No goals to be solved` — a TACTIC artifact, not the spec speaking.
_PROOF_BARE = "prove_correct applyProjection by\n  loom_solve"

_PROOF_ALL = _PROOF_GOLD


def _impl(body, proof=_PROOF_BARE):
    """Full variant: the executable impl lines replaced, proof retuned."""
    return _swap(_swap(_BASE, _IMPL_BODY, body), _PROOF_GOLD, proof)


# ---------------------------------------------------------------------------
# Witnesses. `applyProjectionTester p rec req proj = false` says the extracted
# program's result violates the method's postcondition at that concrete input.
# The four tester directives are appended to BOTH the rival file and the frozen
# file, so every name the witness uses exists on both sides by construction.
# Arguments are in DECLARATION order: the shared carrier, the recording ledger,
# then the two request observations. `recorded` is passed as `false` at every
# point (a step asked about an assembly that has not yet recorded a projection
# onto any carrier), which is the entry state BOTH halves of the accounting are
# stated against: a rival that records where the push-down does not apply drives
# the ledger to `true` and is refuted by the first half, and a rival that records
# nowhere leaves it `false` where the push-down DOES apply and is refuted by the
# second.
# ---------------------------------------------------------------------------
def _witness(args):
    return ("\n"
            "extract_program_for applyProjection\n"
            "prove_precondition_decidable_for applyProjection\n"
            "prove_postcondition_decidable_for applyProjection\n"
            "derive_tester_for applyProjection\n\n"
            f"example : applyProjectionTester {args} = false := by\n"
            "  decide\n")


_ADMISS_ASSERT = """    assert (with_name_prefix `admiss (
      workingCarrier { columns := [], sideSelected := [], auxSelected := [], auxAvailable := [],
                       ownFields := ["order"] } ["order"] ["order"]
        = { columns := ["order"], sideSelected := [], auxSelected := [], auxAvailable := [],
            ownFields := ["order"] } ∧
      workingCarrier { columns := [], sideSelected := [], auxSelected := ["bar"],
                       auxAvailable := ["bar"], ownFields := ["name"] }
          ["name"] ["name", "bar"]
        = { columns := ["name"], sideSelected := [], auxSelected := ["bar"], auxAvailable := ["bar"],
            ownFields := ["name"] } ∧
      workingCarrier { columns := [], sideSelected := [], auxSelected := ["bar"],
                       auxAvailable := ["bar"], ownFields := ["name"] }
          ["name"] []
        = { columns := ["name"], sideSelected := [], auxSelected := ["bar"], auxAvailable := ["bar"],
            ownFields := ["name"] } ∧
      workingCarrier { columns := [], sideSelected := [], auxSelected := [], auxAvailable := [],
                       ownFields := ["order"] } [] ["order"]
        = { columns := [], sideSelected := [], auxSelected := [], auxAvailable := [],
            ownFields := ["order"] } ∧
      workingCarrier { columns := ["num"], sideSelected := [], auxSelected := [], auxAvailable := [],
                       ownFields := ["num"] } ["order"] ["order"]
        = { columns := ["num"], sideSelected := [], auxSelected := [], auxAvailable := [],
            ownFields := ["num"] } ∧
      workingCarrier { columns := [], sideSelected := ["bar"], auxSelected := [],
                       auxAvailable := ["bar"], ownFields := ["name"] }
          ["name"] ["name", "bar"]
        = { columns := ["name"], sideSelected := ["bar"], auxSelected := [],
            auxAvailable := ["bar"], ownFields := ["name"] } ∧
      workingCarrier { columns := [], sideSelected := ["bar"], auxSelected := ["bar"],
                       auxAvailable := ["bar"], ownFields := ["name"] }
          ["name"] ["name", "bar"]
        = { columns := ["name"], sideSelected := ["bar"], auxSelected := [],
            auxAvailable := ["bar"], ownFields := ["name"] }))"""


SPEC_TESTS = [
    # =====================================================================
    # SOUNDNESS — structurally different but CORRECT impls that MUST verify.
    # =====================================================================
    {
        "id": "pos-closed-form",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl("""    recorded := recorded || shouldProject persistent requested
    return workingCarrier persistent requested projected""", _PROOF_BARE),
        "rationale": (
            "returns the grounded model `workingCarrier persistent requested "
            "projected` in closed form: no working local, no assignment, and "
            "the shared carrier is never written, so the frame holds by "
            "construction. Maximally different executable shape from the frozen "
            "copy-then-reconcile body; the reproof is a bare `loom_solve` "
            "because a single expression leaves no residual branch goal. This "
            "is also the honest no-ungrounded-echo control — the pure model IS "
            "the real work here, so returning it is correct rather than a "
            "cheat."),
    },
    {
        "id": "pos-two-branches",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl("""    if shouldProject persistent requested then
      recorded := true
      return recordOnto persistent projected
    else
      return persistent""", _PROOF_ALL),
        "rationale": (
            "splits the reconciliation into two explicit branches, each with "
            "its own return, instead of assigning a conditional to a working "
            "local. Observationally identical on every input, and the shared "
            "carrier is never assigned. Defends the obligation against a "
            "CONTROL-FLOW reshape."),
    },
    {
        "id": "pos-inlined-guard",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl("""    let mut working := persistent
    recorded := recorded || (persistent.columns.isEmpty && !requested.isEmpty)
    working := if persistent.columns.isEmpty && !requested.isEmpty then
        (if projected.isEmpty then { persistent with columns := persistent.ownFields }
         else { persistent with
            columns := projected.filter (fun n =>
              !persistent.sideSelected.contains n && !persistent.auxSelected.contains n),
            sideSelected := persistent.sideSelected.filter (fun n => projected.contains n),
            auxSelected := persistent.auxSelected.filter (fun n =>
              projected.contains n && !persistent.sideSelected.contains n) })
      else working
    return working""", _PROOF_ALL),
        "rationale": (
            "keeps the frozen copy-then-reconcile shape but spells the push- "
            "down guard AND the selection split out inline instead of calling "
            "the pure helpers. Definitionally the same test and the same "
            "partition, so a failure would mean the spec is pinned to the "
            "helpers being reached by name rather than to the behaviour they "
            "describe."),
    },

    # =====================================================================
    # ADMISSIBILITY — the `require` admits the ordinary inputs, and the
    # post-image is NON-DEGENERATE: four corners of the pure model are pinned
    # in-region at concrete carriers, so the obligation cannot read as one
    # every impl meets. The frozen impl is kept verbatim so the method's own
    # obligation still has to discharge; the proof gains a `decide` arm.
    # =====================================================================
    {
        "id": "admiss-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _swap(_BASE, _IMPL_START, _IMPL_START + _ADMISS_ASSERT),
            _PROOF_GOLD,
            "prove_correct applyProjection by\n"
            "  loom_solve\n"
            "  all_goals first\n"
            "    | decide\n"
            "    | simp_all [workingCarrier, shouldProject, recordOnto]\n"),
        "rationale": (
            "the post-image is satisfiable AND non-degenerate at four concrete "
            "corners, asserted in-region: a carrier naming no columns with a "
            "one-column request must end up naming exactly that column; the "
            "same carrier whose own auxiliary output is among the pushed names "
            "must route that name into its SELECTED AUXILIARY OUTPUTS and the "
            "rest into its explicit columns (so the returned carrier tracks "
            "the split, not merely the pushed list); a request that names no "
            "explicit columns of its own must leave the carrier alone EVEN "
            "THOUGH the pushed projection is non-empty (so the guard is pinned "
            "to the right observation); and a carrier that already names a "
            "column must keep its own selection; a carrier carrying a SIDE "
            "output among the pushed names must keep it in its side record "
            "rather than in its explicit columns; and a carrier carrying the "
            "SAME name in both records must keep it as a side output ONLY, its "
            "auxiliary record losing it. Six genuinely distinct outcomes, so "
            "the model is not a constant and the obligation is not vacuous."),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at
    # a DISTINCT concrete input point.
    # =====================================================================
    {
        "id": "weak-reconcile-in-place",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl("""    if shouldProject persistent requested then
      recorded := true
      persistent := recordOnto persistent projected
      return persistent
    else
      return persistent"""),
        "rationale": (
            "reconciles the SHARED carrier itself and hands it back, exactly "
            "the long-standing shape: the projection it records stays on the "
            "carrier every later assembly of the same compound request will "
            "read, so a second assembly finds a carrier that already names "
            "columns, skips the push-down, and keeps the FIRST assembly's "
            "column list. Refuted at the empty carrier with a one-column "
            "request, where the frame clause is violated outright."),
        "witness": _witness(
            '{ columns := [], sideSelected := [], auxSelected := [], auxAvailable := [], ownFields := [\"order\", \"name\"] } false [\"order\"] [\"order\"]'),
    },
    {
        "id": "weak-install-then-restore",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl("""    let saved := persistent
    recorded := true
    persistent := recordOnto persistent projected
    let working := if shouldProject saved requested then persistent else saved
    persistent := saved
    return working"""),
        "rationale": (
            "records the projection onto the SHARED carrier unconditionally and "
            "then writes the carrier's whole selection back. The frame clause "
            "is satisfied — the carrier ends as it began — and the returned "
            "selection is right on the whole domain, so only the recording "
            "ACCOUNTING can refute it: a recording happened where the push-down "
            "does not apply. Refuted at a carrier that already names its own "
            "column, where no recording may occur anywhere."),
        "witness": _witness(
            '{ columns := [\"num\"], sideSelected := [], auxSelected := [], auxAvailable := [], ownFields := [\"num\", \"order\"] } false [\"order\"] [\"order\"]'),
    },
    {
        "id": "weak-never-record",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl("""    return workingCarrier persistent requested projected"""),
        "rationale": (
            "asserts the right selection of the result without ever recording a "
            "projection onto any carrier — the ledger never moves. The value "
            "clause and the frame clause both hold on the whole domain, so this "
            "is refutable only by the accounting: where the push-down applies a "
            "recording must really happen. Refuted at the empty carrier with a "
            "one-column request."),
        "witness": _witness(
            '{ columns := [], sideSelected := [], auxSelected := [], auxAvailable := [], ownFields := [\"order\", \"name\"] } false [\"order\"] [\"order\"]'),
    },
    {
        "id": "weak-project-unconditionally",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl("""    recorded := true
    return recordOnto persistent projected"""),
        "rationale": (
            "records the projection on every input, ignoring the guard "
            "entirely, so a carrier that already names its own columns has them "
            "replaced and a request that names no explicit columns of its own "
            "still forces a push-down. Refuted at a carrier naming its own "
            "column with an empty request, where the carrier's own selection "
            "must survive untouched."),
        "witness": _witness(
            '{ columns := [\"num\"], sideSelected := [], auxSelected := [], auxAvailable := [], ownFields := [\"num\", \"order\"] } false [] []'),
    },
    {
        "id": "weak-never-project",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl("""    recorded := recorded || shouldProject persistent requested
    return persistent"""),
        "rationale": (
            "moves the ledger correctly but never actually reshapes anything: "
            "it hands back the carrier as it stands even where the push-down "
            "applies, so the constituent selects its own default columns "
            "instead of the requested projection. Refuted at the empty carrier "
            "with a two-column request."),
        "witness": _witness(
            '{ columns := [], sideSelected := [], auxSelected := [], auxAvailable := [], ownFields := [\"order\", \"name\"] } false [\"name\", \"order\"] [\"name\", \"order\"]'),
    },
    {
        "id": "weak-no-aux-split",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl("""    let mut working := persistent
    if shouldProject persistent requested then
      recorded := true
      working := { persistent with columns := projected }
      return working
    else
      return working"""),
        "rationale": (
            "puts every pushed name into the carrier's explicit column list, "
            "never routing the names the carrier supplies itself into its "
            "selected auxiliary outputs. The two parts of the selection are "
            "what recording reshapes together, and this rival gets the split "
            "wrong, asserting a carrier's own auxiliary output as one of its "
            "explicit columns. Refuted at a carrier that supplies an auxiliary "
            "output which is among the pushed names."),
        "witness": _witness(
            '{ columns := [], sideSelected := [], auxSelected := [\"bar\"], auxAvailable := [\"bar\"], ownFields := [\"name\"] } false [\"name\"] [\"name\", \"bar\"]'),
    },
    {
        "id": "weak-swapped-aux-split",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl("""    let mut working := persistent
    if shouldProject persistent requested then
      recorded := true
      working := { persistent with
        columns := persistent.auxSelected.filter (fun n => projected.contains n),
        auxSelected := projected.filter (fun n => !persistent.auxSelected.contains n) }
      return working
    else
      return working"""),
        "rationale": (
            "routes each pushed name to the WRONG half of the selection: the "
            "names the carrier supplies itself become its explicit columns and "
            "the rest become its selected auxiliary outputs. Both halves are "
            "non-empty at the refuting point, so this is caught by the "
            "selection's shape rather than by its emptiness — the partition "
            "itself is pinned, not merely the set of names."),
        "witness": _witness(
            '{ columns := [], sideSelected := [], auxSelected := [\"bar\"], auxAvailable := [\"bar\"], ownFields := [\"name\"] } false [\"name\"] [\"name\", \"bar\"]'),
    },
    {
        "id": "weak-permute-projection",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl("""    let mut working := persistent
    if shouldProject persistent requested then
      recorded := true
      working := recordOnto persistent projected.reverse
      return working
    else
      return working"""),
        "rationale": (
            "records the pushed names in reverse order. Every constituent of a "
            "compound request must line its columns up in the SAME order, so a "
            "permuted projection pairs each column with the wrong one from its "
            "siblings. Refuted at a two-column request, a point that holds "
            "length and membership fixed so ORDER alone is at stake."),
        "witness": _witness(
            '{ columns := [], sideSelected := [], auxSelected := [], auxAvailable := [], ownFields := [\"order\", \"name\"] } false [\"order\", \"name\"] [\"order\", \"name\"]'),
    },
    {
        "id": "weak-guard-on-projected",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl("""    let mut working := persistent
    if persistent.columns.isEmpty && !projected.isEmpty then
      recorded := true
      working := recordOnto persistent projected
      return working
    else
      return working"""),
        "rationale": (
            "reads the guard off the full pushed projection instead of the "
            "outer request's OWN explicit column list, so it fires a push-down "
            "for a request that names no explicit columns of its own. Refuted "
            "at exactly that separating point: an empty request whose pushed "
            "projection is non-empty, where the carrier must be left alone."),
        "witness": _witness(
            '{ columns := [], sideSelected := [], auxSelected := [], auxAvailable := [], ownFields := [\"order\", \"name\"] } false [] [\"order\"]'),
    },
    {
        "id": "weak-discard-shared-list",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl("""    let mut working := persistent
    if shouldProject persistent requested then
      recorded := true
      working := recordOnto persistent projected
      return working
    else
      return { persistent with columns := [], sideSelected := [], auxSelected := [] }"""),
        "rationale": (
            "throws the carrier's own selection away where the push-down does "
            "NOT apply, handing back a carrier naming nothing instead of the "
            "one it was given. Refuted at a carrier that already names its own "
            "column with an empty request — the sub-domain the guard exists to "
            "protect."),
        "witness": _witness(
            '{ columns := [\"num\"], sideSelected := [], auxSelected := [], auxAvailable := [], ownFields := [\"num\", \"order\"] } false [] []'),
    },
    {
        "id": "weak-drop-last-column",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl("""    let mut working := persistent
    if shouldProject persistent requested then
      recorded := true
      working := recordOnto persistent projected.dropLast
      return working
    else
      return working"""),
        "rationale": (
            "records the pushed projection one name short. The selection is "
            "right in shape and order and wrong only in LENGTH, so it is caught "
            "by a multi-name point rather than by any emptiness boundary."),
        "witness": _witness(
            '{ columns := [], sideSelected := [], auxSelected := [], auxAvailable := [], ownFields := [\"order\", \"name\"] } false [\"order\", \"name\"] [\"order\", \"name\"]'),
    },
    {
        "id": "weak-clobber-carrier-model",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl("""    let mut working := persistent
    if shouldProject persistent requested then
      recorded := true
      working := recordOnto persistent projected
      persistent := { persistent with auxAvailable := [], ownFields := [] }
      return working
    else
      return working"""),
        "rationale": (
            "hands back the right working carrier but reaches into the SHARED "
            "carrier and erases the description of its model — which auxiliary "
            "outputs it can supply and which columns it defines. Those "
            "observations are not part of a selection and reconciling a "
            "projection never alters them, so a later assembly of the same "
            "compound request would find a carrier that can no longer answer "
            "the names it used to."),
        "witness": _witness(
            '{ columns := [], sideSelected := [], auxSelected := [], auxAvailable := [\"bar\"], ownFields := [\"name\"] } false [\"name\"] [\"name\"]'),
    },
    {
        "id": "weak-key-on-available",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl("""    let mut working := persistent
    if shouldProject persistent requested then
      recorded := true
      working := { persistent with
        columns := projected.filter (fun n => !persistent.auxAvailable.contains n),
        auxSelected := projected.filter (fun n => persistent.auxAvailable.contains n) }
      return working
    else
      return working"""),
        "rationale": (
            "splits the pushed names on the wrong OBSERVATION: it asks which "
            "auxiliary outputs the carrier's model is ABLE to supply instead of "
            "which ones its selection already carries. The two agree whenever "
            "every available auxiliary output is also selected, so this rival is "
            "right on the ordinary carrier and wrong exactly where the carrier "
            "supplies an auxiliary output its selection leaves out. Refuted at "
            "such a carrier with a pushed name that is BOTH an available-but- "
            "unselected auxiliary output and a column the carrier's own model "
            "defines: the name belongs in the explicit column list, and this "
            "rival routes it into the selected auxiliary outputs instead."),
        "witness": _witness(
            '{ columns := [], sideSelected := [], auxSelected := [\"bar\"], auxAvailable := [\"bar\", \"name\"], ownFields := [\"name\"] } false [\"name\"] [\"name\"]'),
    },
    {
        "id": "weak-empty-projection-blanks",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl("""    let mut working := persistent
    if shouldProject persistent requested then
      recorded := true
      working := { persistent with
        columns := projected.filter (fun n =>
          !persistent.sideSelected.contains n && !persistent.auxSelected.contains n),
        sideSelected := persistent.sideSelected.filter (fun n => projected.contains n),
        auxSelected := persistent.auxSelected.filter (fun n =>
          projected.contains n && !persistent.sideSelected.contains n) }
      return working
    else
      return working"""),
        "rationale": (
            "keeps only the general leg of the recording and drops the other "
            "one: it filters an EMPTY projection through the same split, so the "
            "carrier ends up naming nothing at all instead of every column its "
            "own model defines, and its selected auxiliary outputs are dropped "
            "rather than left alone. Identical to the frozen model on every "
            "non-empty projection, so it is refutable ONLY at the empty one — "
            "the leg a rival that reads the split as a single filter cannot "
            "have. Refuted at a carrier with a selected auxiliary output, an "
            "outer request that names a column of its own, and nothing pushed "
            "down."),
        "witness": _witness(
            '{ columns := [], sideSelected := [], auxSelected := [\"bar\"], auxAvailable := [\"bar\"], ownFields := [\"name\"] } false [\"name\"] []'),
    },
    # ---------------------------------------------------------------------
    # The two rivals below attack the legs the THREE-part selection adds. Each
    # is exactly right on every carrier whose two records of selected non-column
    # outputs cannot disagree, and wrong only where they can, so neither is
    # reachable by any carrier that carries side outputs in one record only.
    # ---------------------------------------------------------------------
    {
        "id": "weak-collapse-side-into-aux",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl("""    let mut working := persistent
    if shouldProject persistent requested then
      recorded := true
      working := if projected.isEmpty then
          { persistent with columns := persistent.ownFields }
        else
          { persistent with
            columns := projected.filter (fun n => !persistent.auxSelected.contains n),
            auxSelected := persistent.auxSelected.filter (fun n => projected.contains n) }
      return working
    else
      return working"""),
        "rationale": (
            "consults only ONE of the carrier's two records of selected non- "
            "column outputs. It keeps the auxiliary record correctly and never "
            "looks at the side record at all, so a projected name the carrier "
            "carries as a SIDE output is treated as an ordinary column: it is "
            "pushed into the explicit column list, and the side record is left "
            "holding a name the projection did not ask for. Identical to the "
            "frozen model on every carrier whose side record is empty — which is "
            "every carrier the ordinary case builds — and refuted only where the "
            "side record is populated. Refuted at a carrier carrying a side "
            "output that is among the pushed names."),
        "witness": _witness(
            '{ columns := [], sideSelected := [\"bar\"], auxSelected := [], auxAvailable := [\"bar\"], ownFields := [\"name\"] } false [\"name\"] [\"name\", \"bar\"]'),
    },
    {
        "id": "weak-ignore-record-precedence",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl("""    let mut working := persistent
    if shouldProject persistent requested then
      recorded := true
      working := if projected.isEmpty then
          { persistent with columns := persistent.ownFields }
        else
          { persistent with
            columns := projected.filter (fun n =>
              !persistent.sideSelected.contains n && !persistent.auxSelected.contains n),
            sideSelected := persistent.sideSelected.filter (fun n => projected.contains n),
            auxSelected := persistent.auxSelected.filter (fun n => projected.contains n) }
      return working
    else
      return working"""),
        "rationale": (
            "reads BOTH records but filters them INDEPENDENTLY, dropping the "
            "precedence between them. A projected name the carrier happens to "
            "carry in both records must be kept as a side output ONLY and "
            "dropped from the auxiliary record; this rival keeps it in both, so "
            "the constituent would emit that output twice over. The two filters "
            "agree with the frozen model on every carrier whose two records "
            "share no name — so this is refutable only where they overlap, a "
            "point no single-record carrier can reach. Refuted at a carrier that "
            "carries the same name in both records with that name pushed down."),
        "witness": _witness(
            '{ columns := [], sideSelected := [\"bar\"], auxSelected := [\"bar\"], auxAvailable := [\"bar\"], ownFields := [\"name\"] } false [\"name\"] [\"name\", \"bar\"]'),
    },
]


AXIOM_TESTS = []
