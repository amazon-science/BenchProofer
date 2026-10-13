"""properties.py — G-PBT falsification battery for matplotlib__matplotlib-25332 (lean).

NOT a Lean file; a manifest the G-PBT gate parses and executes. Each SPEC_TESTS
entry is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte: region surgery touches only text inside an ``-- impl-start`` /
``-- impl-end`` region and, for a case that legitimately re-proves, inside a
``-- proof-start`` / ``-- proof-end`` region. So ``markers.same_spec`` holds by
construction and every ``theorem correct_<name>`` STATEMENT stays byte-identical
(only the tactic body may differ). No case introduces an ``axiom``, a helper
``theorem``/``lemma``, ``sorry``/``admit``, or ``native_decide``.

``expect="verify"`` passes iff the variant is in scope AND the file elaborates
with both obligations closed. ``expect="reject"`` passes iff the variant is in
scope AND it does NOT verify AND the case's refutation ``witness`` holds of the
rival while FAILING on the frozen solution.

DEFENDED SURFACE (read the frozen spec view). Two modeled behaviors over a
partition table that maps each member's *reference* to the list of references
making up its group (``m : List (Ref × List Ref)``), and over that table's
transferable form (``s : List (Int × List Int)``), in which every reference has
been replaced by the object it points at:

  serialize (m : List (Ref × List Ref)) : Except String (List (Int × List Int))
    problem_spec_serialize m result :=  result = Except.ok (toStrong m)
      where toStrong m = m.map (fun kv => (kv.1.val, kv.2.map (fun r => r.val)))

  deserialize (s : List (Int × List Int)) : List (Ref × List Ref)
    problem_spec_deserialize s result :=  result = toWeak s
      where toWeak s = s.map (fun kv => (Ref.mk kv.1, kv.2.map (fun n => Ref.mk n)))

Each clause is a single equality, but it is an equality against a term the spec
spells out completely, so it bundles several INDEPENDENT obligations. Every
reject rival below attacks exactly one of these faces:

  * SUCCEEDS — the transferable form must be produced at all (``Except.ok``),
    not declined. This is the face with no counterpart on the deserialize side.
  * ENTRY-COMPLETE — one output entry per input entry, in order; no entry may be
    dropped or added.
  * KEY REFERENT — each entry's recorded key is the referent of *that entry's
    key reference*, not of some member of its group.
  * MEMBER-COMPLETE — every member of the group is recorded, in order; none may
    be dropped and the group may not be left empty.
  * FAITHFUL REFERENT — the recorded (respectively re-wrapped) value IS the
    referent, not a transform of it. A rival that shifts every referent has the
    right shape and the right length and is still wrong.

ADVERSARIAL READ OF THE NAGINI CLASSES ON THIS CARRIER
(the nagini sibling contracts ``capture_state`` / ``restore_state`` /
``roundtrip_weakness`` over two parallel flag lists; this bundle models the
purely functional core as the two table transforms above, so the port is a
re-expression against a different carrier, not a translation):

  * FRAME / PERMISSION MUTATION (nagini cases 1 and 2, ``frame-mutation-*``) —
    VACUOUS here. Those rivals write into an input the nagini contract holds at a
    half permission, and the rejection comes from the permission system. Lean is
    referentially transparent: an input carries no heap permission, there is no
    read-only half to overwrite and no aliasing to exploit, so the class has no
    expressible instance. NO substitute is fabricated for it.

  * PARTIAL-DOMAIN (nagini cases 3, 4, 5, 10 — last slot, first slot, restore's
    last slot, short result) — PORTED, and re-expressed on the richer carrier.
    Nagini's carrier is a flat flag list, so "partial" can only mean *which index
    diverges*; here the table is nested, so the same argument splits into two
    genuinely different attacks per direction: drop an ENTRY (the outer level,
    nagini's short-result probe) and mutilate a GROUP (the inner level, which the
    flat carrier cannot express at all). Cases 5-6, 8-9 below.

  * WRONG-CONSTANT / SKIPPED STEP (nagini case 6, ``roundtrip-skip-restore``) —
    PORTED as the SUCCEEDS-face rival (case 4) and, on the reconstruct side, as
    the skipped member re-wrap (case 8). Nagini could state this as a composition
    that ends in the wrong global constant because it contracts a third
    composing function; this bundle models the two directions separately, so the
    same "a required step was skipped" argument attaches to each direction on its
    own.

  * POSITIVE CONTROLS (nagini cases 7 and 8, ``pos-control-*``) — PORTED as cases
    1-2. On this backend a positive control is real work rather than a reshape:
    the variant must close the frozen obligation for its NEW implementation shape
    with no new lemma and no weakened statement.

  * ADMISSIBILITY (nagini case 9) — PORTED as case 3, re-aimed. The nagini probe
    establishes a *precondition* at a representative input; the frozen
    obligations here carry NO precondition hypothesis (both transforms are total,
    so each ``∀`` is unguarded), so there is no precondition binder to admit.
    The honest analogue is to show the obligations are SATISFIABLE at the ground
    inputs the behavior is actually exercised on — including the composition of
    the two directions, which is the property the surface exists to provide.

  * DIVERGENCE / NON-TERMINATION — a KNOWN HOLE, not a vacuous class. The
    nagini sibling carries no such case to port (no ``diverge-*`` / ``nonterm-*``
    / ``weak-diverge`` id appears in it), so nothing was dropped; but the claim
    this file previously made — that "a diverging implementation cannot be
    written at all" — was measured FALSE and is corrected here.

    What was measured. A diverging rival IS writable, as
    ``partial def implementation_serialize ... := implementation_serialize m``.
    ``partial`` is not in ``variant_scope``'s assumption-token list, so
    ``variant_problems`` returns ``[]`` — the rival is IN SCOPE — and the variant
    does fail to verify (the frozen script cannot ``unfold`` an opaque `partial`
    constant). So the case would record as ``rejected``.

    It is nonetheless NOT shipped, because its rejection would not be
    attributable: a ``partial def`` is compiled to an OPAQUE constant with no
    equation lemmas, so no witness can reduce it. Measured directly — the
    ``toOption`` witness that discriminates for the declines-to-produce case
    fails against the diverging rival with ``Tactic `decide` failed ... because
    its `Decidable` instance``, i.e. the claim is never evaluated. The rejection
    would attest to `partial`'s opacity (the same reason a merely RESHAPED
    correct impl fails), not to the spec. Recording it as a hole rather than as
    vacuous is the honest disposition: the spec does not pin termination.

  * UNGROUNDED-ORACLE ECHO — VACUOUS. Each postcondition is GROUNDED in its own
    input: the right-hand side is built only from that input by a fully unfolded
    helper, and the bundle declares no ``opaque`` callee and no ``axiom``
    (``meta.json``: ``axioms == []``, ``deep_model_references == []``). There is
    no answer key to echo, so no echo rival exists. The positive controls and the
    admissibility case stand in its place.

  * AXIOM_TESTS (nagini A1, A2) — DROPPED, as required: the axiom lane belongs to
    G-AX, which this gate ignores. (It is a skip stub for this bundle anyway,
    since references are modeled deeply rather than axiomatized.)

BINDER COVERAGE. ``problem_spec_serialize`` binds ``m`` and ``result``;
``problem_spec_deserialize`` binds ``s`` and ``result``. Both input binders are
varied by the reject witnesses along every axis the carrier has, so no rival that
mishandled one axis could hide behind a value every witness holds fixed:

  * ENTRY COUNT — one-entry tables and two-entry tables both appear (a rival that
    only ever drops the last of several entries is invisible at a one-entry
    input, and a rival wrong on a singleton is invisible if every witness has
    two).
  * GROUP SIZE — singleton groups and two-member groups both appear (a rival that
    drops one member of a group agrees with the spec on a group it leaves empty
    only if the group had exactly one member; only a longer group separates
    "dropped a member" from "left the group empty").
  * KEY-VS-GROUP RELATION — witnesses include the normal shape, where the key's
    referent is itself the FIRST member of its group, and the discriminating
    shape, where it is NOT (``[(Ref.mk 9, [Ref.mk 2, Ref.mk 9])]``,
    ``[(20, [13, 20])]``). Held at the normal shape alone, a rival that reads
    each entry's key off the head of its own group agrees with the spec
    everywhere and the battery would never notice. This is the binder axis that
    two earlier ports missed, in the exact shape the porting brief describes.

  AUDIT PROBE (attack D/E, not shipped as cases — recorded so the next reader
  knows which unattacked faces were measured rather than assumed). Six NEW wrong
  impls aimed at faces no shipped rival covers were built against the frozen
  spec, and all six were REJECTED, so none is a spec hole: entry ORDER reversed,
  member order reversed within each group, entries de-duplicated
  (``eraseDups``), a decline confined to the empty table only, member order
  reversed on the reconstruct side, and a reconstruct that appends each key into
  its own group. Three NEW correct reshapes were also built: a ``foldr``-based
  serialize and a pattern-matching ``s.map (fun (k, vs) => ...)`` reconstruct
  both VERIFY, so the clauses are not too strong on those shapes. The third (an
  inner ``foldl (fun r v => r ++ [v.val])``) needs the append-accumulator lemma
  the frozen file already proves; with that argument supplied inline as a
  ``have`` it verifies too, so it is a proof-effort matter and NOT a soundness
  hole in the spec.

  The nine reject witnesses probe nine distinct input points, no two rivals
  sharing one: five on the ``m`` binder and four on ``s``, which
  ``scripts/pbt_coverage.py`` reports per obligation as ``pts=4-5``. The
  ``result`` binder is not independently varied and cannot be: it is always
  applied to ``implementation_<name>`` of the same input, which is exactly what
  makes each witness a statement about the rival rather than about an arbitrary
  value.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen script is tuned to the frozen form — so
a rejection alone attributes nothing to the spec. Every ``expect="reject"`` case
therefore carries a Lean snippet stating ``¬ problem_spec_<name>`` at ONE
CONCRETE input and closing by evaluation. Each was built twice by hand before
shipping (``scripts/lean_verify.sh`` against the rival and against the frozen
solution) and SEEN to hold of its rival and to FAIL on gold, so it discriminates
rather than asserting a tautology. Every witness is stated at literal inputs, so
none binds a hypothesis and none can be inconsistent.

  Mechanics note, recorded because it is not obvious and cost several rounds.
  ``Except String (List (Int × List Int))`` has no ``DecidableEq`` instance, so a
  serialize witness cannot close by ``decide`` on the equality itself
  (``failed to synthesize Decidable``), and ``simp``/``simp only`` alone leaves a
  residual ``pure`` around the loop result. Two different routes are needed
  depending on what the rival returns:

    * rival produces a value at the wrong content — strip the shared ``ok``
      constructor with ``Except.ok.inj`` and decide the resulting
      ``List (Int × List Int)`` equality, which IS decidable;
    * rival produces NO value — ``Except.ok.inj`` does not apply here at all
      (there is no shared ``ok`` to strip), so the refutation is stated over
      ``Except.toOption``, a computable projection whose image DOES carry a
      ``DecidableEq``. The tempting shortcut, constructor disjointness via
      ``Except.noConfusion``, was measured HOLLOW and must not be used: it fails
      on the frozen solution because `simp` leaves the accumulator loops
      unreduced, not because the frozen solution is correct, and it fails
      identically against a deliberately WRONG loop-keeping impl. See the audit
      note on ``_ser_wit_no_value`` for the build evidence.

  The deserialize witnesses return a bare list and close by ``decide`` directly.

AUDIT NOTE on the ``pos-control-serialize-direct-map`` proof body. That case
re-proves its obligation with ``rfl`` after unfolding, and the comment on it
originally said the frozen script's loop lemma "no longer applies". Measured
otherwise: the frozen tactic body, retained verbatim, ALSO closes that reshaped
impl (exit 0). Both scripts work, so the case is an honest positive control but
its reshape is absorbed by the frozen script rather than requiring a new proof;
the wording below was corrected to say so.
"""
from pathlib import Path

INSTANCE = "matplotlib__matplotlib-25332"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Region anchors. Each is the FULL body of one impl region or the FULL tactic
# body of one proof region — so every replacement lands entirely inside the
# region it means to edit, the spec view (hence same_spec) is untouched, and the
# theorem statements stay byte-identical. Uniqueness is asserted at import, so
# the manifest breaks loudly if the frozen solution ever drifts.
# ---------------------------------------------------------------------------

_IMPL_SER = (
    "def implementation_serialize (m : List (Ref × List Ref)) :\n"
    "    Except String (List (Int × List Int)) := Id.run do\n"
    "  let mut acc : List (Int × List Int) := []\n"
    "  for kv in m do\n"
    "    let key := kv.1\n"
    "    let members := kv.2\n"
    "    let mut derefMembers : List Int := []\n"
    "    for v in members do\n"
    "      derefMembers := derefMembers ++ [v.val]\n"
    "    acc := acc ++ [(key.val, derefMembers)]\n"
    "  return Except.ok acc"
)

_IMPL_DES = (
    "def implementation_deserialize (s : List (Int × List Int)) :\n"
    "    List (Ref × List Ref) := Id.run do\n"
    "  let mut acc : List (Ref × List Ref) := []\n"
    "  for kv in s do\n"
    "    let members := kv.2\n"
    "    let mut wrapMembers : List Ref := []\n"
    "    for v in members do\n"
    "      wrapMembers := wrapMembers ++ [Ref.mk v]\n"
    "    acc := acc ++ [(Ref.mk kv.1, wrapMembers)]\n"
    "  return acc"
)

_PROOF_SER = (
    "  intro m\n"
    "  unfold problem_spec_serialize implementation_serialize toStrong\n"
    "  simp only [Id.run, bind, forIn_app_pure, List.nil_append]\n"
    "  rfl"
)

_PROOF_DES = (
    "  intro s\n"
    "  unfold problem_spec_deserialize implementation_deserialize toWeak\n"
    "  simp only [Id.run, bind, forIn_app_pure, List.nil_append]\n"
    "  rfl"
)

for _a in (_IMPL_SER, _IMPL_DES, _PROOF_SER, _PROOF_DES):
    if _BASE.count(_a) != 1:
        raise AssertionError(f"anchor drift / not unique: {_a[:60]!r}")


_SER_HEAD = ("def implementation_serialize (m : List (Ref × List Ref)) :\n"
             "    Except String (List (Int × List Int)) := Id.run do\n")
_DES_HEAD = ("def implementation_deserialize (s : List (Int × List Int)) :\n"
             "    List (Ref × List Ref) := Id.run do\n")


def _ser(body):
    """A variant whose serialize implementation has `body`; spec untouched."""
    return _swap(_BASE, _IMPL_SER, _SER_HEAD + body)


def _des(body):
    """A variant whose deserialize implementation has `body`; spec untouched."""
    return _swap(_BASE, _IMPL_DES, _DES_HEAD + body)


def _ser_wit(inp):
    """`¬ problem_spec_serialize inp (implementation_serialize inp)`.

    The result type is an `Except`, which has no `DecidableEq`, so the
    constructor is stripped by `Except.ok.inj` first and the resulting list
    equality — which IS decidable — is refuted by `decide`.
    """
    return (f"example : ¬ problem_spec_serialize {inp}\n"
            f"    (implementation_serialize {inp}) := by\n"
            "  unfold problem_spec_serialize\n"
            "  intro h\n"
            "  exact absurd (Except.ok.inj h) (by decide)\n")


def _ser_wit_no_value(inp):
    """`¬ problem_spec_serialize inp (...)` for a rival that produces NO value.

    Stated over `Except.toOption`, a COMPUTABLE projection of the result type,
    for the reason recorded below. `Except String (List (Int × List Int))` has no
    `DecidableEq`, but `Option (List (Int × List Int))` does, so mapping both
    sides through `toOption` and deciding the image is a refutation the kernel
    actually EVALUATES on either subject.

    AUDIT NOTE — why this is not the obvious `Except.noConfusion` route.
    A witness that closes by constructor disjointness alone,

        unfold problem_spec_serialize implementation_serialize
        simp only [Id.run, pure]
        intro h
        exact Except.noConfusion h

    holds of this rival (exit 0) and fails on the frozen solution (exit 1), so it
    clears both halves of the gate's discrimination check — but its gold-side
    failure carries NO information about the claim, and the case was hollow. The
    measurement, with the real verifier:

      * `exact (h : Nat)` to reveal the hypothesis's real type prints, on gold, an
        UNREDUCED `do let r ← forIn ... Except.ok r = Except.ok (toStrong ...)`.
        `simp only [Id.run, pure]` never normalises the frozen accumulator loops,
        so `Except.noConfusion` cannot see two distinct constructors and fails on
        the SHAPE of the term rather than on its truth. On the rival the same
        probe prints the fully reduced `Except.error "..." = Except.ok (...)`.
      * The same shipped witness was then built against a WRONG loop-keeping
        rival (the drops-last-entry impl of the case below, which at this input
        returns `ok []` instead of `ok [(1, [1])]`): exit 1, with the
        byte-identical `Type mismatch / Except.noConfusion h` first error as gold.
        So that witness rejects a wrong impl and the correct one for one and the
        same reason — the presence of a `forIn` loop — which is a tactic mismatch,
        not a refutation.

    The `toOption` route is evaluated instead of unified: gold fails with
    ``Tactic `decide` proved that the proposition ¬(... ) = ... is false`` (an
    evaluation of the concrete claim), while the same witness on the wrong
    loop-keeping rival above ELABORATES (exit 0). The gold-side exit code now
    tracks what is claimed, which is what makes the rejection attributable.
    """
    return (f"example : ¬ problem_spec_serialize {inp}\n"
            f"    (implementation_serialize {inp}) := by\n"
            "  unfold problem_spec_serialize\n"
            "  intro h\n"
            "  have h2 := congrArg Except.toOption h\n"
            "  simp only [implementation_serialize, toStrong, Id.run] at h2\n"
            "  exact absurd h2 (by decide)\n")


def _des_wit(inp):
    """`¬ problem_spec_deserialize inp (implementation_deserialize inp)`."""
    return (f"example : ¬ problem_spec_deserialize {inp}\n"
            f"    (implementation_deserialize {inp}) := by\n"
            "  unfold problem_spec_deserialize implementation_deserialize toWeak\n"
            "  decide\n")


# The graded behavior, stated without naming anything the frozen spec does not.
# A figure whose labels have been aligned carries a grouping container recording
# which of its label-bearing components must be positioned together. The graded
# test converts that figure to a transferable form, reconstructs it, RENDERS the
# reconstruction, and compares the rendered image against a reference figure
# rendered directly. So a rival is non-resolving if it either fails to produce a
# transferable form at all (the reported crash), or produces one from which the
# partition is recovered incorrectly: at render time the recovered group decides
# which components' extents are combined to place the shared label, so any
# recovered group that differs from the original shifts the label and the image
# comparison fails.
_RENDER_ARG = (
    "at render time the recovered group decides which components' extents are "
    "combined to place their shared label, so a group that differs from the "
    "original one places the label differently and the graded rendered-image "
    "comparison fails")


SPEC_TESTS = [
    # =====================================================================
    # 1. SOUNDNESS positive control (ports nagini case 7,
    #    pos-control-capture-local-reshape). A structurally DIFFERENT but
    #    correct implementation of the forward direction that MUST verify; if a
    #    faithful correct implementation cannot close the frozen obligation the
    #    clause is SPEC-TOO-STRONG. On this backend the reshape is real work: the
    #    accumulator loops disappear entirely, so the frozen tactic body no
    #    longer applies and the obligation is RE-PROVEN for the new shape. The
    #    theorem statement is byte-identical; no lemma, axiom or assumption
    #    token is added, and the loop lemma the frozen proof uses is simply not
    #    needed by this shape.
    # =====================================================================
    {
        "id": "pos-control-serialize-direct-map",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _swap(
                _BASE, _IMPL_SER,
                _SER_HEAD
                + "  return Except.ok (m.map (fun kv =>"
                  " (kv.1.val, kv.2.map (fun r => r.val))))",
            ),
            _PROOF_SER,
            "  intro m\n"
            "  unfold problem_spec_serialize implementation_serialize toStrong\n"
            "  rfl",
        ),
        "rationale": (
            "Structurally different — both accumulator loops are replaced by a "
            "single traversal that builds each entry in one step, with no "
            "mutable state at all — but observably identical: it returns "
            "`Except.ok` of exactly the term the clause names, so "
            "`result = Except.ok (toStrong m)` holds for every input. A "
            "faithful correct implementation of the forward direction MUST "
            "verify, else the clause is SPEC-TOO-STRONG. Proof: after unfolding, "
            "the two sides are definitionally equal and `rfl` closes it; the "
            "frozen script's loop lemma is not NEEDED by this shape (though, "
            "measured, the frozen tactic body would also still close it — so "
            "this case's value is defending the clause against a loop-free "
            "shape, not exercising a new proof). Statement byte-identical; "
            "nothing new is declared or assumed."
        ),
    },

    # =====================================================================
    # 2. SOUNDNESS positive control on the OTHER obligation (ports nagini case
    #    8, pos-control-restore-local-reshape). Every obligation must be
    #    DEFENDED, not only attacked, so the reconstruct direction gets its own
    #    positive control rather than relying on case 1.
    # =====================================================================
    {
        "id": "pos-control-deserialize-inner-map",
        "kind": "soundness",
        "expect": "verify",
        "module": _des(
            "  let mut acc : List (Ref × List Ref) := []\n"
            "  for kv in s do\n"
            "    acc := acc ++ [(Ref.mk kv.1, kv.2.map (fun n => Ref.mk n))]\n"
            "  return acc"
        ),
        "rationale": (
            "A correct reconstruct that builds each entry's group in one "
            "traversal instead of accumulating it element by element: the outer "
            "shape is kept, the inner mutable accumulator is gone. Observably "
            "identical (each entry is still the key wrapped afresh paired with "
            "every member wrapped afresh, in order), so `result = toWeak s` "
            "holds and it MUST verify — else the reconstruct clause is "
            "SPEC-TOO-STRONG. Proof: the frozen tactic body is retained "
            "verbatim; the inner reshape is definitional, so the outer loop "
            "lemma still applies and the script still closes. Statement byte-"
            "identical; nothing new is declared or assumed."
        ),
    },

    # =====================================================================
    # 3. ADMISSIBILITY (ports nagini case 9,
    #    admissibility-restore-precondition, RE-AIMED). The nagini probe admits
    #    a PRECONDITION at a representative input; both frozen obligations here
    #    are unguarded `∀` (each transform is total), so no precondition binder
    #    exists to admit. The honest analogue is that the obligations are
    #    SATISFIABLE at the ground inputs the behavior is exercised on rather
    #    than only provable in the abstract — including the COMPOSITION of the
    #    two directions, which is the property the surface exists to provide and
    #    which neither clause states on its own. If any ground instance could
    #    not be discharged, the behavior would be unsatisfiable at an input it
    #    must admit (the analogue of PRECOND-TOO-STRONG).
    # =====================================================================
    {
        "id": "admiss-ground-instances-and-composition",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _PROOF_DES,
            "  have _g_empty : problem_spec_serialize []\n"
            "      (implementation_serialize []) := by rfl\n"
            "  have _g_two : problem_spec_serialize\n"
            "      [(Ref.mk 1, [Ref.mk 1, Ref.mk 2]), (Ref.mk 2, [Ref.mk 1, Ref.mk 2])]\n"
            "      (implementation_serialize\n"
            "        [(Ref.mk 1, [Ref.mk 1, Ref.mk 2]), (Ref.mk 2, [Ref.mk 1, Ref.mk 2])])"
            " := by rfl\n"
            "  have _g_des : problem_spec_deserialize [(1, [1, 2]), (2, [1, 2])]\n"
            "      (implementation_deserialize [(1, [1, 2]), (2, [1, 2])]) := by rfl\n"
            "  have _g_roundtrip :\n"
            "      implementation_deserialize\n"
            "        (toStrong [(Ref.mk 1, [Ref.mk 1, Ref.mk 2]),"
            " (Ref.mk 2, [Ref.mk 1, Ref.mk 2])])\n"
            "      = [(Ref.mk 1, [Ref.mk 1, Ref.mk 2]), (Ref.mk 2, [Ref.mk 1, Ref.mk 2])]"
            " := by decide\n"
            + _PROOF_DES,
        ),
        "rationale": (
            "Discharges both obligations at ground inputs by evaluation before "
            "closing the frozen obligation verbatim: the empty table (the "
            "boundary case), a two-entry table whose two members share one "
            "group (the shape the behavior is actually exercised on), the "
            "reconstruct clause at that table's transferable form, and — the "
            "part neither clause states alone — the COMPOSITION, that "
            "reconstructing the transferable form of that table returns the "
            "table itself. Verifies, so the surface is satisfiable and "
            "round-trips at a normal input; if it could not be discharged the "
            "behavior would be unsatisfiable exactly where it must hold. "
            "Nothing is assumed: no new declaration, the theorem statement is "
            "byte-identical, and every ground instance is a `have` inside the "
            "tactic body proved by evaluation."
        ),
    },

    # =====================================================================
    # 4-8. UNIQUENESS rivals against `problem_spec_serialize`, one per face of
    #      the clause. Each carries (a) the refinement argument that its
    #      faithful real patch would NOT resolve the graded test, so a verifying
    #      rival would be a true verify-does-not-imply-resolve break rather than
    #      an artifact, and (b) a witness pinning the violation at one concrete
    #      input, SEEN to hold of the rival and to fail on gold.
    # =====================================================================
    {
        "id": "serialize-declines-to-produce",
        "kind": "uniqueness",
        "expect": "reject",
        # THE SUCCEEDS FACE, and the literal pre-fix behavior: no transferable
        # form is produced at all. Wrong on EVERY input, the strongest single
        # rival against this clause. Ports the nagini wrong-constant/skipped-
        # step argument (case 6) onto the forward direction.
        "module": _ser(
            '  return Except.error "no transferable form"'
        ),
        "refinement": (
            "Declining to produce a transferable form is exactly the reported "
            "defect: the container holds references, which have no transferable "
            "form, so the attempt to convert the enclosing figure produces no "
            "value and raises instead. The graded test's very first step is that "
            "conversion, so a faithful patch that still declines fails there "
            "immediately and would NOT resolve."
        ),
        "rationale": (
            "REJECT from the SUCCEEDS face of `result = Except.ok (toStrong m)`: "
            "the rival returns `Except.error` on every input, and no `error` "
            "value equals an `ok` value, so the clause fails at the first "
            "non-trivial input. Binder: `m` (any table); the violation is "
            "independent of its contents, which is why this rival is refuted at "
            "the smallest one."
        ),
        "witness": _ser_wit_no_value("[(Ref.mk 1, [Ref.mk 1])]"),
    },
    {
        "id": "serialize-drops-last-entry",
        "kind": "uniqueness",
        "expect": "reject",
        # THE ENTRY-COMPLETE FACE at the OUTER level: every entry is converted
        # correctly, then the last one is discarded. Ports nagini cases 3 and 10
        # (last-slot divergence / short result), which on a flat flag carrier
        # were two separate probes and here coincide at the outer level.
        "module": _ser(
            "  let mut acc : List (Int × List Int) := []\n"
            "  for kv in m do\n"
            "    let key := kv.1\n"
            "    let members := kv.2\n"
            "    let mut derefMembers : List Int := []\n"
            "    for v in members do\n"
            "      derefMembers := derefMembers ++ [v.val]\n"
            "    acc := acc ++ [(key.val, derefMembers)]\n"
            "  return Except.ok acc.dropLast"
        ),
        "refinement": (
            "Dropping an entry loses a member of the partition: after "
            "reconstruction that object is no longer recorded as belonging to "
            "its group, so the group recovered for it is the singleton "
            "containing only itself. " + _RENDER_ARG + ". A faithful patch that "
            "converted all but the last entry would therefore NOT resolve."
        ),
        "rationale": (
            "REJECT from the ENTRY-COMPLETE face: the clause pins the result to "
            "`toStrong m`, a traversal producing exactly one entry per input "
            "entry, so a result one entry shorter cannot equal it. Binder: `m`, "
            "varied to a TWO-entry table — at a one-entry table this rival "
            "returns the empty result and would be caught by the entry face "
            "generically, but only a table with more than one entry shows it is "
            "correct on the entries it does keep, which is the near-miss "
            "claimed here."
        ),
        "witness": _ser_wit(
            "[(Ref.mk 3, [Ref.mk 3, Ref.mk 4]), (Ref.mk 4, [Ref.mk 3, Ref.mk 4])]"
        ),
    },
    {
        "id": "serialize-drops-first-group-member",
        "kind": "uniqueness",
        "expect": "reject",
        # THE MEMBER-COMPLETE FACE at the INNER level — an attack the nagini
        # flat flag carrier cannot express at all. Every entry is present and
        # correctly keyed; each group has lost its first member.
        "module": _ser(
            "  let mut acc : List (Int × List Int) := []\n"
            "  for kv in m do\n"
            "    let key := kv.1\n"
            "    let members := kv.2\n"
            "    let mut derefMembers : List Int := []\n"
            "    for v in members do\n"
            "      derefMembers := derefMembers ++ [v.val]\n"
            "    acc := acc ++ [(key.val, derefMembers.tail)]\n"
            "  return Except.ok acc"
        ),
        "refinement": (
            "Dropping a member from each recorded group makes the reconstructed "
            "partition smaller than the original: the group recovered for a "
            "member is missing one of the objects it must be positioned with. "
            + _RENDER_ARG + ". A faithful patch that recorded the referents of "
            "all but the first member of each group would NOT resolve."
        ),
        "rationale": (
            "REJECT from the MEMBER-COMPLETE face: the clause pins each entry's "
            "second component to `kv.2.map (fun r => r.val)` — every member's "
            "referent, in order — and `.tail` of that is shorter for any "
            "non-empty group. Binder: `m`, varied in GROUP SIZE to a two-member "
            "group; at a singleton group this rival empties the group, which the "
            "next rival's face already covers, so the longer group is what makes "
            "this a distinct dropped-member claim rather than the same one."
        ),
        "witness": _ser_wit("[(Ref.mk 7, [Ref.mk 7, Ref.mk 8])]"),
    },
    {
        "id": "serialize-keys-entry-on-first-member",
        "kind": "uniqueness",
        "expect": "reject",
        # THE KEY-REFERENT FACE. A near-miss that agrees with the spec on every
        # table whose each key's referent happens to be the FIRST member of its
        # own group — which is the normal shape — and diverges only where it is
        # not. This is the binder axis the porting brief flags as the one two
        # earlier ports left un-probed, so it gets its own witness at the
        # DISTINGUISHING input rather than sharing one.
        "module": _ser(
            "  let mut acc : List (Int × List Int) := []\n"
            "  for kv in m do\n"
            "    let key := kv.2.headD kv.1\n"
            "    let members := kv.2\n"
            "    let mut derefMembers : List Int := []\n"
            "    for v in members do\n"
            "      derefMembers := derefMembers ++ [v.val]\n"
            "    acc := acc ++ [(key.val, derefMembers)]\n"
            "  return Except.ok acc"
        ),
        "refinement": (
            "Reading each entry's key off the head of its own group instead of "
            "off that entry's key reference re-labels the partition: after "
            "reconstruction, several entries collapse onto one object as their "
            "key and the objects that were keys are absent from the table "
            "entirely, so looking a member up recovers no group (or another "
            "member's group). " + _RENDER_ARG + ". A faithful patch that "
            "recorded each group under its first member would NOT resolve. Note "
            "this patch is INDISTINGUISHABLE from a correct one on any table "
            "where each key's referent leads its own group, which is why it must "
            "be probed off that shape."
        ),
        "rationale": (
            "REJECT from the KEY-REFERENT face: the clause pins each entry's "
            "first component to `kv.1.val`, the referent of THAT entry's key "
            "reference, while the rival records the referent of its group's "
            "first member. Binder: `m`, varied along the KEY-VS-GROUP axis — the "
            "witness input `[(Ref.mk 9, [Ref.mk 2, Ref.mk 9])]` is a table whose "
            "key's referent is NOT its group's first member. It needs its own "
            "witness rather than sharing one, because at three of the four other "
            "serialize inputs — `[(Ref.mk 1, [Ref.mk 1])]`, `[(Ref.mk 7, "
            "[Ref.mk 7, Ref.mk 8])]` and `[(Ref.mk 30, [Ref.mk 30])]`, each of "
            "which holds this axis at the normal key-leads-group shape — this "
            "rival's output is IDENTICAL to the spec's, so none of those points "
            "refutes it. (Checked directly, not assumed. The remaining input, "
            "the two-entry table, does happen to separate it as well, since its "
            "second entry's key does not lead that entry's group; but a rival "
            "whose only wrongness is on this axis would still be invisible to a "
            "battery that probed only the normal shape, which is the gap this "
            "case exists to close.)"
        ),
        "witness": _ser_wit("[(Ref.mk 9, [Ref.mk 2, Ref.mk 9])]"),
    },
    {
        "id": "serialize-shifts-member-referent",
        "kind": "uniqueness",
        "expect": "reject",
        # THE FAITHFUL-REFERENT FACE. Structure, entry count, group size and
        # order are all exactly right; only the recorded referents are a
        # transform of the real ones. Nagini's flag carrier can only express this
        # as a wrong constant (its cases 3-6 all move a flag between 0 and 1);
        # here the recorded value is a referent, so "wrong value at the right
        # place" is its own face.
        "module": _ser(
            "  let mut acc : List (Int × List Int) := []\n"
            "  for kv in m do\n"
            "    let key := kv.1\n"
            "    let members := kv.2\n"
            "    let mut derefMembers : List Int := []\n"
            "    for v in members do\n"
            "      derefMembers := derefMembers ++ [v.val + 1]\n"
            "    acc := acc ++ [(key.val, derefMembers)]\n"
            "  return Except.ok acc"
        ),
        "refinement": (
            "Recording something other than the referent itself means the "
            "reconstructed group is populated with objects that were never in "
            "it, and the real members are absent. The recovered partition has "
            "the right SHAPE and entirely wrong contents, so " + _RENDER_ARG
            + ". A faithful patch that stored a transform of each referent "
            "rather than the referent would NOT resolve — and, unlike a dropped "
            "entry, it cannot be caught by any length or shape check, which is "
            "why this face needs its own rival."
        ),
        "rationale": (
            "REJECT from the FAITHFUL-REFERENT face: the clause pins each "
            "recorded member to `r.val`, the referent itself, so a shifted value "
            "falsifies the equality even though the result has the right entry "
            "count, the right keys and the right group lengths. Binder: `m`, "
            "varied to a SINGLETON group at a one-entry table — the minimal "
            "input at which no structural face is violated, so the rejection is "
            "attributable to the recorded value alone and to nothing else."
        ),
        "witness": _ser_wit("[(Ref.mk 30, [Ref.mk 30])]"),
    },

    # =====================================================================
    # 9-12. UNIQUENESS rivals against `problem_spec_deserialize`. The reconstruct
    #       obligation must be ATTACKED in its own right: a battery that only
    #       attacked the forward direction would leave a rival that reconstructs
    #       wrongly entirely uncaught, and the round trip is the whole point of
    #       the surface. Ports nagini case 5 (restore's partial domain) plus the
    #       reconstruct-side counterparts of the faces above.
    # =====================================================================
    {
        "id": "deserialize-skips-member-rewrap",
        "kind": "uniqueness",
        "expect": "reject",
        # THE MEMBER-COMPLETE FACE on the reconstruct side, in its strongest
        # form: the keys are rebuilt but every group is left empty, so the step
        # that rebuilds the groups is skipped outright. Ports nagini case 6's
        # skipped-step argument onto this direction.
        "module": _des(
            "  let mut acc : List (Ref × List Ref) := []\n"
            "  for kv in s do\n"
            "    acc := acc ++ [(Ref.mk kv.1, [])]\n"
            "  return acc"
        ),
        "refinement": (
            "Rebuilding the keys but not their groups reconstructs a table in "
            "which nothing is grouped with anything: every recovered group is "
            "empty, so no component is positioned with any other and the "
            "alignment the original figure carried is gone. " + _RENDER_ARG
            + ". A faithful patch that omitted the group rebuild would NOT "
            "resolve."
        ),
        "rationale": (
            "REJECT from the MEMBER-COMPLETE face of `result = toWeak s`: the "
            "clause pins each entry's second component to `kv.2.map (fun n => "
            "Ref.mk n)`, one fresh reference per recorded member, and the empty "
            "list differs from it for every non-empty group. Binder: `s`, at a "
            "two-member group so the failure is a lost group rather than merely "
            "a lost element."
        ),
        "witness": _des_wit("[(5, [5, 6])]"),
    },
    {
        "id": "deserialize-drops-last-entry",
        "kind": "uniqueness",
        "expect": "reject",
        # THE ENTRY-COMPLETE FACE on the reconstruct side. Ports nagini case 5
        # (restore leaves the last slot wrong) — its "last index diverges"
        # argument, re-expressed at the outer level of this carrier.
        "module": _des(
            "  let mut acc : List (Ref × List Ref) := []\n"
            "  for kv in s do\n"
            "    let members := kv.2\n"
            "    let mut wrapMembers : List Ref := []\n"
            "    for v in members do\n"
            "      wrapMembers := wrapMembers ++ [Ref.mk v]\n"
            "    acc := acc ++ [(Ref.mk kv.1, wrapMembers)]\n"
            "  return acc.dropLast"
        ),
        "refinement": (
            "Reconstructing all but the last entry loses one object from the "
            "table, so the group recovered for it is the singleton containing "
            "only itself even though the transferable form recorded it as "
            "grouped. " + _RENDER_ARG + ". A single dropped entry is enough: a "
            "faithful patch that rebuilt every entry but the last would NOT "
            "resolve."
        ),
        "rationale": (
            "REJECT from the ENTRY-COMPLETE face: `toWeak s` produces exactly "
            "one entry per recorded entry, so a result one entry shorter cannot "
            "equal it. Binder: `s`, varied in ENTRY COUNT to a two-entry table, "
            "which is what shows the rival is correct on the entries it keeps "
            "(the near-miss it claims) rather than trivially empty."
        ),
        "witness": _des_wit("[(11, [11, 12]), (12, [11, 12])]"),
    },
    {
        "id": "deserialize-keys-entry-on-first-member",
        "kind": "uniqueness",
        "expect": "reject",
        # THE KEY-REFERENT FACE on the reconstruct side. The mirror near-miss of
        # case 7: agrees with the spec wherever a recorded key leads its own
        # group, diverges only where it does not, so it gets its own witness at
        # the distinguishing input.
        "module": _des(
            "  let mut acc : List (Ref × List Ref) := []\n"
            "  for kv in s do\n"
            "    let members := kv.2\n"
            "    let mut wrapMembers : List Ref := []\n"
            "    for v in members do\n"
            "      wrapMembers := wrapMembers ++ [Ref.mk v]\n"
            "    acc := acc ++ [(Ref.mk (kv.2.headD kv.1), wrapMembers)]\n"
            "  return acc"
        ),
        "refinement": (
            "Keying each rebuilt entry on the first member of its group rather "
            "than on the entry's own recorded key re-labels the reconstructed "
            "partition: entries collapse onto a shared key and the objects that "
            "were keys have no entry, so looking one up recovers no group. "
            + _RENDER_ARG + ". A faithful patch that rebuilt each entry under "
            "its group's first member would NOT resolve. Like its forward-"
            "direction counterpart it is invisible on any table where each "
            "recorded key leads its own group."
        ),
        "rationale": (
            "REJECT from the KEY-REFERENT face of `result = toWeak s`: the clause "
            "pins each entry's first component to `Ref.mk kv.1`, a fresh "
            "reference to THAT entry's recorded key, while the rival wraps its "
            "group's first member instead. Binder: `s`, varied along the "
            "KEY-VS-GROUP axis — the witness `[(20, [13, 20])]` records a key "
            "that is not its group's first member. It needs its own witness: at "
            "`[(5, [5, 6])]` and `[(41, [41])]`, which hold this axis at the "
            "normal key-leads-group shape, this rival's output is IDENTICAL to "
            "the spec's, so neither point refutes it (checked directly). The "
            "two-entry input separates it incidentally as well, but a rival wrong "
            "only on this axis would be invisible to a battery probing only the "
            "normal shape — the gap this case closes."
        ),
        "witness": _des_wit("[(20, [13, 20])]"),
    },
    {
        "id": "deserialize-shifts-member-referent",
        "kind": "uniqueness",
        "expect": "reject",
        # THE FAITHFUL-REFERENT FACE on the reconstruct side: right structure,
        # right entry count, right group lengths, references built to the wrong
        # objects. The mirror of case 8.
        "module": _des(
            "  let mut acc : List (Ref × List Ref) := []\n"
            "  for kv in s do\n"
            "    let members := kv.2\n"
            "    let mut wrapMembers : List Ref := []\n"
            "    for v in members do\n"
            "      wrapMembers := wrapMembers ++ [Ref.mk (v + 1)]\n"
            "    acc := acc ++ [(Ref.mk kv.1, wrapMembers)]\n"
            "  return acc"
        ),
        "refinement": (
            "Rebuilding a reference to something other than the recorded "
            "referent populates each group with objects that were never in it "
            "while the real members are absent, so the recovered partition has "
            "the right shape and wrong contents. " + _RENDER_ARG + ". A faithful "
            "patch that rebuilt references to a transform of each recorded "
            "referent would NOT resolve, and no length or shape check would "
            "catch it."
        ),
        "rationale": (
            "REJECT from the FAITHFUL-REFERENT face: the clause pins each "
            "rebuilt member to `Ref.mk n` for the recorded `n`, and a reference "
            "to a shifted value is a different `Ref` (equality on `Ref` is "
            "equality of the referent), so the equality fails despite the right "
            "entry count, keys and group lengths. Binder: `s`, at a SINGLETON "
            "group in a one-entry table — the minimal input violating no "
            "structural face, so the rejection is attributable to the rebuilt "
            "value alone."
        ),
        "witness": _des_wit("[(41, [41])]"),
    },
]


# AXIOM lane: EMPTY, and deliberately so. `meta.json` records `axioms == []` and
# `deep_model_references == []` — references are modeled deeply as a structure
# rather than as an axiomatized callee — so there is no axiom-soundness or
# axiom-containment obligation attached to this bundle. The nagini sibling's two
# AXIOM_TESTS are dropped in any event: that lane is G-AX's, and this gate
# ignores it.
AXIOM_TESTS = []
