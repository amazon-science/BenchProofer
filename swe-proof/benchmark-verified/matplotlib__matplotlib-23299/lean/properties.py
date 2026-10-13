"""properties.py — G-PBT falsification battery for matplotlib__matplotlib-23299 (lean).

NOT a Lean file; a manifest the G-PBT gate executes. Each SPEC case is a full
``Solution.lean`` variant that shares the FROZEN spec byte-for-byte (region
surgery: only text inside the ``-- impl-start`` / ``-- impl-end`` region — and,
for a case that legitimately re-proves, inside the ``-- proof-start`` /
``-- proof-end`` region — is changed, so ``markers.same_spec`` holds and the
single ``theorem correct_restoreSettings`` STATEMENT stays byte-identical).
``expect:"verify"`` passes iff (in scope AND the file elaborates with the
obligation closed, no ``sorry``/``admit``/``native_decide`` and no new
``axiom``/``theorem``); ``expect:"reject"`` passes iff (in scope AND it does NOT
verify AND the case's refutation ``witness`` holds of the rival while FAILING on
the frozen solution).

PORT NOTE. This is a PORT of the nagini falsification battery
(``../nagini/properties.py``) onto this backend's carrier. The nagini bundle
models the scoped-override save/body/revert lifecycle IMPERATIVELY over a live
``Dict[int, int]`` held at full permission, and pins FOUR postcondition clauses
(SURVIVE / REVERT / NO-SPURIOUS / FRAME-full-revert) over that mutated mapping.
This Lean bundle models the SAME purely-functional core — the net effect of the
scoped manager's restore on the settings mapping — as ONE pure function of two
observations (the entry snapshot ``orig`` and the post-body mapping ``final``),
and pins it with a SINGLE grounded equation:

    problem_spec_restoreSettings orig final result :=
        result = applyRestore orig final
    where  applyRestore orig final = dictUpdate final (assocErase orig "backend")

i.e. the restored mapping is the post-body mapping overlaid by the entry snapshot
with the distinguished rendering-backend entry removed first, so the value chosen
for that one distinguished key while the body ran SURVIVES and every other key
REVERTS to its entry value. Because the whole net effect is a single deep
equation over the two observable inputs (no opaque callee, no heap, no answer
key), nagini's four separate clauses collapse into ONE top-level clause here —
they are all consequences of this one equality — and each nagini rival ports to
an attack on that equation at the key its wrong impl mishandles.

DEFENDED SURFACE (one modeled behavior; ONE top-level clause, several observable
facets). ``applyRestore orig final`` simultaneously fixes, per key ``k``:
  * SURVIVE — the distinguished key keeps ``final``'s value (it is erased from the
    overlay snapshot, so ``final`` shows through);
  * REVERT  — every other key present in ``orig`` is overwritten back to its entry
    value by the overlay;
  * FRAME / NO-SPURIOUS — no key absent from ``orig``/``final`` is invented, and
    non-distinguished keys are not corrupted to arbitrary values.
The single equation ``result = applyRestore orig final`` pins all of these at
once; a rival mishandling any one of them makes ``result`` unequal to
``applyRestore orig final`` at a concrete input.

The BEHAVIOURAL DISCRIMINATOR (the fix): the distinguished key must be dropped
from the overlay snapshot so the body-chosen value survives. The pre-fix behavior
overlaid the FULL snapshot, reverting the distinguished key to its stale entry
value; the ``weak-revert-distinguished`` rival below IS that pre-fix behavior.

BINDER STRUCTURE. The spec predicate has TWO input binders: ``orig`` (the entry
snapshot) and ``final`` (the post-body mapping). Both are load-bearing and both
are varied across the reject witnesses (see the point-spread block at the
bottom): each witness supplies a distinct ``(orig, final)`` pair, exercising the
distinguished key alone and mixed two- and three-key mappings. The five reject
witnesses probe five DISTINCT input tuples (``pts=5``).

DOMAIN of the refutation points. The modeled mapping is a settings collection
that always carries the distinguished rendering-backend entry, and a scoped body
changes VALUES rather than the key set — so ``orig`` and ``final`` share their
keys. Every reject witness except the NO-SPURIOUS one therefore states its
refutation at a point where the distinguished key is present in BOTH observations
and the two mappings have the same key set, i.e. INSIDE that domain. (The frozen
equation is unconditional, so a witness at a mapping with no distinguished entry
would still build; it would just refute the rival at an input the real caller
cannot produce, which attests less. Two witnesses were re-pointed for exactly
this reason — see the audit note at the bottom.)

ADVERSARIAL READ of the case classes on this carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS as a *permission* class. The nagini
    sibling itself notes there is NO half-permission read-only input to overwrite;
    ``params`` is held at full permission because it is the thing the function
    mutates. On this referentially transparent carrier there is no ``mut`` input,
    no aliasing, no heap cell at all — ``orig``/``final`` are immutable values. So
    the half-permission frame-mutation reject is doubly vacuous here. The ANALOG
    the nagini bundle DOES probe — corrupting a third, non-distinguished key the
    restore must frame/revert — IS ported (``weak-corrupt-third-key`` below), as
    an attack on the FRAME facet of the single equation. No permission-mutation
    substitute is fabricated.

  * UNGROUNDED-ORACLE ECHO — VACUOUS. The postcondition pins ``result`` to
    ``applyRestore orig final`` — a structural function of the two inputs (overlay
    + key-erase), not an opaque answer key. Producing the restored mapping from
    the two observations IS doing the work; there is nothing to echo. In its place
    the battery carries honest structurally-different POSITIVE CONTROLS.

  * PARTIAL-DOMAIN / VALUE — APPLIES. Every rival is correct on part of the domain
    but diverges where its wrong per-key handling bites: reverting the
    distinguished key (the pre-fix bug); not reverting an ordinary key; reverting
    an ordinary key to a wrong constant value; corrupting a third key; and
    inventing a key that belongs to neither observation.

  * KEY-SET vs VALUE. The rivals split across the two ways the single equation can
    be violated: four differ from ``applyRestore orig final`` in a VALUE at a key
    both mappings share, and ``weak-invent-key`` differs in the KEY SET (its result
    is strictly longer). Both are attacks on the one equation, but a rival that
    only ever mis-values a shared key leaves membership untested, so the key-set
    facet carries its own rival rather than being folded into the frame one.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen ``rfl`` proof is tuned to the frozen
form — so a rejection alone attributes nothing to the spec (all five rivals below
fail with ``Tactic `rfl` failed``, exactly as a merely-RESHAPED-but-correct impl
would — and two correct reshapes that this battery does NOT ship were confirmed
to fail the frozen ``rfl`` for precisely that reason while being provable with a
two-line ``simp``, so the tuning is real, not hypothetical). Every
``expect="reject"`` case therefore carries a Lean snippet that
states the spec predicate NEGATED at one concrete ground input and closes by
``decide`` (all inputs are ground ``String``-keyed list literals, so the mapping
computes). Each witness binds NOTHING in its head — there are no hypotheses whose
consistency could be in question. Each was checked with two real ``lake env
lean`` builds to HOLD of its rival and to FAIL (``decide`` refutes the negation)
on the frozen solution, so it discriminates rather than asserting a tautology.

REFINEMENT (why a verifying rival would be a true verify-but-not-resolve break).
Each reject case's ``refinement`` argues that its faithful real counterpart
mishandles one key of the restore, so on exit a setting is left at the wrong
value — the distinguished key reverted (the reported defect, failing the F2P
that asserts the body-chosen backend outlives the scope), or an ordinary key not
restored / corrupted (failing the P2P that asserts the full ordinary set reverts)
— so the faithful patch would NOT resolve.

PROBES RUN BUT NOT SHIPPED (recorded so the next reader need not re-measure).
Four further WRONG impls were built against the frozen spec and all four were
REJECTED, so none is a spec hole: erasing the wrong (ordinary) key from the
overlay snapshot; swapping the overlay direction (snapshot as the overlaid map
instead of the base); using the snapshot as the base and overlaying the post-body
mapping; and a conditional near-miss that overlays the FULL snapshot exactly when
the body left the distinguished key unchanged. That last one is worth recording:
it is the pre-fix behavior guarded by a test that makes it agree with the fix on
the sub-domain where the body did not touch the distinguished key, and it was
confirmed to agree with the spec on the whole unique-key two-value grid — its only
disagreement is at a mapping with a DUPLICATE distinguished key, which the
documented domain excludes. It is therefore NOT shipped as a rival: on the real
domain it is definitionally equal to the frozen behavior, so a case built on it
would attest to a tactic mismatch rather than to the spec. Two further CORRECT
reshapes were also built and both were PROVEN (a double-erase of the
distinguished key, and the erase written as an explicit filter with a flipped
decidable test), each needing a two-line `simp` rather than the frozen `rfl`. They
are not shipped because the two positives already carry the soundness lane, but
they are the evidence that the spec is not too strong for shapes that are only
EXTENSIONALLY equal to the frozen body — the shipped positives are both
DEFINITIONALLY equal to it, which is a weaker demonstration.

AXIOM lane: EMPTY here. This bundle declares no ``opaque`` callee and consumes no
``axiom`` (the restore is modeled deeply as association-list operations); the
axiom lane belongs to G-AX. The nagini ``AXIOM_TESTS`` (an A-reference deep-model
probe validating its dict copy/del/update model against the real primitives) is a
nagini-carrier concern and is DROPPED — see ``assessment``.
"""
from pathlib import Path

INSTANCE = "matplotlib__matplotlib-23299"
BACKEND = "lean"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- region anchors (each unique inside Solution.lean; verified at load) ----
# The gold impl body between `-- impl-start`/`-- impl-end` (markers excluded).
# Every impl reshape lands entirely inside this region -> same_spec holds.
_GOLD_IMPL = """  let mut snapshot := orig
  snapshot := assocErase snapshot "backend"
  return dictUpdate final snapshot"""

# The frozen proof body (inside `-- proof-start`/`-- proof-end`) — the
# admissibility positive prepends a ground `have` here without touching the
# `correct_restoreSettings` STATEMENT or the spec view.
_GOLD_PROOF = "  intro orig final\n  rfl"


# ---------------------------------------------------------------------------
# witness scaffold. States the spec predicate NEGATED at a concrete ground
# input, unfolds to the deep equation, and closes by `decide` (the mapping over
# String-keyed literals computes). Holds of a rival whose output differs from
# `applyRestore orig final`; FAILS on gold (where they are equal).
# ---------------------------------------------------------------------------
def _witness(orig, final):
    return (
        f"example : ¬ problem_spec_restoreSettings {orig} {final}\n"
        f"    (implementation_restoreSettings {orig} {final}) := by\n"
        "  unfold problem_spec_restoreSettings implementation_restoreSettings "
        "applyRestore\n"
        "  decide\n")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify, else SPEC-TOO-STRONG. Each keeps the
    # `theorem correct_restoreSettings` statement byte-identical and reuses the
    # frozen `rfl` proof (both reshapes are definitionally the frozen body).
    # =====================================================================
    {
        "id": "pos-pointfree",
        "kind": "soundness",
        "expect": "verify",
        # Structurally different CORRECT reshape: drop the imperative `Id.run do`
        # / `let mut` scaffold and return the pure overlay expression directly.
        # Definitionally identical to the frozen loop body, so the frozen proof
        # (`intro; rfl`) still closes — no proof authoring, no helper, no
        # assumption token. (Verified: real build.)
        "module": _swap(
            _BASE, _GOLD_IMPL,
            '  dictUpdate final (assocErase orig "backend")',
        ),
        "rationale": "correct reshape that returns the overlay expression "
                     "point-free instead of threading it through a mutable local; "
                     "it computes the SAME mapping on every input, so the single "
                     "equation still holds — else SPEC-TOO-STRONG. Definitionally "
                     "the frozen body, so the frozen `intro; rfl` proof still "
                     "closes; statement byte-identical, no new axiom/lemma. Ports "
                     "the nagini pos-reorder-writes positive (there: reorder the "
                     "two straight-line body writes; here the imperative scaffold "
                     "is removed with identical net effect).",
    },
    {
        "id": "pos-immutable-let",
        "kind": "soundness",
        "expect": "verify",
        # Local-variable RESHAPE positive control: bind the erased snapshot to a
        # single immutable `let` (no `let mut`, no re-assignment), then overlay.
        # Same data flow, different local structure; definitionally the frozen
        # body, so the frozen proof still closes. (Verified: real build.)
        "module": _swap(
            _BASE, _GOLD_IMPL,
            '  let snapshot := assocErase orig "backend"\n'
            "  return dictUpdate final snapshot",
        ),
        "rationale": "local-variable reshape: the erased snapshot is bound to one "
                     "immutable `let` before the overlay, rather than mutated in "
                     "place. Same data flow, different local structure; keeps the "
                     "net effect intact so the single equation still holds. Must "
                     "verify, else SPEC-TOO-STRONG. Definitionally the frozen body, "
                     "so the frozen `intro; rfl` proof still closes; statement "
                     "byte-identical, no new axiom/lemma. Ports nagini's "
                     "pos-local-rename.",
    },

    # =====================================================================
    # ADMISSIBILITY — confirm the modeled behavior is SATISFIABLE (non-vacuous)
    # at a normal, F2P-shaped input. The frozen theorem carries NO precondition
    # (the equality holds unconditionally), so the nagini precondition-admission
    # self-call re-expresses as: discharge the spec predicate by evaluation at a
    # concrete two-key mapping matching the F2P scenario (distinguished key
    # changed by the body from one value to another; one ordinary key) as a
    # `have`, then close the frozen obligation verbatim. Nothing is assumed: no
    # new declaration, statement byte-identical, ground instance is a `have`
    # prepended to the existing tactic body. (Verified: real build.)
    # =====================================================================
    {
        "id": "admiss-ground-f2p",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _GOLD_PROOF,
            '  have _ground : problem_spec_restoreSettings\n'
            '      [("backend", "agg"), ("mode", "M")] '
            '[("backend", "aardvark"), ("mode", "N")]\n'
            '      (implementation_restoreSettings\n'
            '        [("backend", "agg"), ("mode", "M")] '
            '[("backend", "aardvark"), ("mode", "N")]) := by\n'
            '    unfold problem_spec_restoreSettings implementation_restoreSettings '
            'applyRestore\n'
            '    decide\n'
            '  intro orig final\n'
            '  rfl',
        ),
        "rationale": "the modeled behavior is discharged at the smallest F2P-shaped "
                     "input (a two-key mapping whose distinguished key is changed by "
                     "the body from one value to another and one ordinary key "
                     "changed too) by evaluation as a `have` — the restored mapping "
                     "keeps the body-chosen distinguished value and reverts the "
                     "ordinary key — then the frozen obligation is closed verbatim. "
                     "Verifies (else the modeled behavior would be unsatisfiable at "
                     "exactly a normal F2P input — the analogue of "
                     "PRECOND-TOO-STRONG). Nothing is assumed: no new declaration, "
                     "statement byte-identical, ground instance is a `have` in the "
                     "existing tactic body. Ports nagini's admiss-requires-facts.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected. Each carries (a) the refinement argument that its
    # faithful real patch would NOT resolve the F2P/P2P, and (b) a witness pinning
    # the violation at one concrete input.
    # =====================================================================

    # ---- the fix itself: revert the distinguished key (the PRE-patch bug) ----
    {
        "id": "weak-revert-distinguished",
        "kind": "uniqueness",
        "expect": "reject",
        # Pre-fix behavior: overlay the FULL entry snapshot WITHOUT erasing the
        # distinguished key, so its body-chosen value is reverted to the stale
        # entry value.
        "module": _swap(
            _BASE, _GOLD_IMPL,
            "  let mut snapshot := orig\n"
            "  return dictUpdate final snapshot"),
        "refinement": "this IS the pre-fix behavior: the entry snapshot is overlaid "
                      "in full, so the distinguished key is reverted to its stale "
                      "entry value instead of keeping the value chosen while the "
                      "body ran. A faithful real patch that overlaid the full "
                      "snapshot (omitting the drop of the distinguished key) reverts "
                      "the body-chosen backend on scope exit — exactly the reported "
                      "defect. The F2P asserts the body-chosen backend outlives the "
                      "scope, so the faithful patch would NOT resolve.",
        "rationale": "REJECT from the SURVIVE facet of the single equation: the spec "
                      "pins `result = dictUpdate final (assocErase orig \"backend\")` "
                      "(distinguished key erased from the overlay so `final`'s value "
                      "shows through), but the rival overlays the full snapshot, "
                      "reverting that key to `orig`'s value; they differ whenever the "
                      "body changed the distinguished key. Refuted at orig backend "
                      "\"A\", final backend \"B\".",
        "witness": _witness('[("backend", "A")]', '[("backend", "B")]'),
    },

    # ---- invent a key the restore must not introduce (NO-SPURIOUS facet) ----
    {
        "id": "weak-invent-key",
        "kind": "uniqueness",
        "expect": "reject",
        # The gold restore PLUS an entry for a key that is in NEITHER observation.
        # The overlay therefore introduces a setting that did not exist at entry
        # and was not left by the body. This attacks the NO-SPURIOUS facet, which
        # is DISTINCT from weak-corrupt-third-key: that rival mis-values a key
        # already present in both mappings, whereas this one changes the KEY SET.
        "module": _swap(
            _BASE, _GOLD_IMPL,
            "  let mut snapshot := orig\n"
            '  snapshot := assocErase snapshot "backend"\n'
            '  snapshot := assocSet snapshot "extra" "junk"\n'
            "  return dictUpdate final snapshot"),
        "refinement": "the NO-SPURIOUS probe: the restore overlays an entry for a "
                      "key present in neither observation, so on scope exit the "
                      "mapping carries a setting that was never recorded at entry "
                      "and never set by the body. A faithful real patch whose "
                      "restore injected an unrecorded setting would leave the "
                      "settings mapping with a key the caller never established, "
                      "FAILING the P2P that asserts the scope exits with exactly "
                      "the entry key set (only values, never membership, are "
                      "affected by the restore). verify-but-not-resolve.",
        "rationale": "REJECT from the NO-SPURIOUS facet of the single equation: "
                      "`applyRestore orig final` overlays only entries drawn from "
                      "`orig`, so its key set is contained in that of `orig`/"
                      "`final`; the rival appends a key drawn from neither, so the "
                      "two mappings differ in LENGTH, not merely in a value. "
                      "Refuted at orig=[(backend,agg),(dpi,100)], "
                      "final=[(backend,aardvark),(dpi,100)], where the spec's "
                      "result has two entries and the rival's has three.",
        "witness": _witness('[("backend", "agg"), ("dpi", "100")]',
                            '[("backend", "aardvark"), ("dpi", "100")]'),
    },

    # ---- do not revert an ordinary key (keeps the body override) ----
    {
        "id": "weak-no-revert-ordinary",
        "kind": "uniqueness",
        "expect": "reject",
        # The overlay is dropped entirely: `final` is returned unchanged, so every
        # ordinary key keeps the body's temporary override instead of reverting.
        "module": _swap(
            _BASE, _GOLD_IMPL,
            "  let mut snapshot := orig\n"
            '  snapshot := assocErase snapshot "backend"\n'
            "  return final"),
        "refinement": "the entry snapshot is never overlaid — the post-body mapping "
                      "is returned as-is, so every ordinary key keeps the value the "
                      "body left it at instead of reverting. A faithful real patch "
                      "that omitted the restore overlay leaves every non-distinguished "
                      "setting permanently mutated by the scoped body, which FAILS "
                      "the P2P asserting the ordinary settings are restored to their "
                      "entry values on scope exit. verify-but-not-resolve.",
        "rationale": "REJECT from the REVERT facet: the spec pins the overlay of the "
                      "erased snapshot onto `final`, so an ordinary key ends at its "
                      "`orig` value; the rival returns `final`, ending at the body "
                      "value. These differ whenever the body changed an ordinary "
                      "key. Refuted at a mapping carrying BOTH the distinguished "
                      "key and an ordinary key (orig mode \"X\", final mode \"Y\"): "
                      "the spec's result reverts the ordinary key to \"X\" while "
                      "the rival leaves it at \"Y\".",
        # The refutation point carries the distinguished key in BOTH observations
        # and gives the two mappings a SHARED key set, so it lies inside the
        # documented domain of the modeled behavior (the settings mapping always
        # carries the rendering-backend entry, and a scoped body changes values,
        # not the key set). A point with no distinguished entry at all would
        # refute the rival only outside that domain.
        "witness": _witness('[("backend", "agg"), ("mode", "X")]',
                            '[("backend", "aardvark"), ("mode", "Y")]'),
    },

    # ---- revert an ordinary key to a WRONG value ----
    {
        "id": "weak-revert-wrong-value",
        "kind": "uniqueness",
        "expect": "reject",
        # A partial-domain rival: the overlay is applied, but every ordinary key
        # is reverted to a CONSTANT wrong value ("stale") rather than its entry
        # value. Correct only where the entry value happened to equal that
        # constant.
        "module": _swap(
            _BASE, _GOLD_IMPL,
            "  let mut snapshot := orig\n"
            '  snapshot := assocErase snapshot "backend"\n'
            '  snapshot := snapshot.map (fun kv => (kv.1, "stale"))\n'
            "  return dictUpdate final snapshot"),
        "refinement": "a PARTIAL-DOMAIN rival: the overlay reverts each ordinary key "
                      "to a fixed constant value rather than its snapshotted entry "
                      "value — correct only where the entry value equals that "
                      "constant. A faithful real patch that wrote a wrong saved value "
                      "into a non-distinguished setting on restore corrupts that "
                      "setting, FAILING the P2P asserting the ordinary settings "
                      "revert to their exact entry values whenever the body value "
                      "differed from the entry value. verify-but-not-resolve.",
        "rationale": "REJECT from the REVERT facet (exact value pinned): the spec "
                      "pins the ordinary key at its `orig` value, the rival at the "
                      "constant \"stale\"; these differ for any entry value != "
                      "\"stale\". The spec pins the EXACT reverted value, not merely "
                      "'some revert happened'. Refuted at a three-key mapping "
                      "carrying the distinguished key plus TWO ordinary keys "
                      "(mode \"M\"->\"N\", dpi \"100\"->\"200\"), both of which the "
                      "spec reverts to their entry values while the rival flattens "
                      "both to the constant \"stale\".",
        # In-domain refutation point (distinguished key present in both, shared key
        # set) and a SECOND ordinary key, so the constant-collapse is exhibited on
        # more than one entry at once.
        "witness": _witness('[("backend", "A"), ("mode", "M"), ("dpi", "100")]',
                            '[("backend", "B"), ("mode", "N"), ("dpi", "200")]'),
    },

    # ---- corrupt a third, non-distinguished key (the FRAME facet) ----
    {
        "id": "weak-corrupt-third-key",
        "kind": "uniqueness",
        "expect": "reject",
        # The gold impl PLUS a write to a third non-distinguished key in the
        # snapshot, so the overlay leaves that key at a garbage value. This is the
        # frame-condition analog the nagini bundle probes for its full-permission
        # mutated mapping.
        "module": _swap(
            _BASE, _GOLD_IMPL,
            "  let mut snapshot := orig\n"
            '  snapshot := assocErase snapshot "backend"\n'
            '  snapshot := assocSet snapshot "mode" "corrupt"\n'
            "  return dictUpdate final snapshot"),
        "refinement": "the FRAME-condition probe: the gold restore PLUS a write of a "
                      "garbage value to a third, non-distinguished key in the overlay "
                      "snapshot. A faithful real patch whose restore corrupts a "
                      "non-distinguished setting leaves that setting at a garbage "
                      "value after the scope exits, FAILING the P2P that asserts the "
                      "FULL set of ordinary settings is restored to its entry state, "
                      "not just some of them. verify-but-not-resolve.",
        "rationale": "REJECT from the FRAME facet: the spec pins that key at its "
                      "`orig` value via the overlay, but the rival overlays "
                      "\"corrupt\" there. These differ whenever the entry value != "
                      "\"corrupt\". Refuted at a two-key mapping "
                      "orig=[(backend,A),(mode,M)], final=[(backend,B),(mode,M)] "
                      "where the third key `mode` must frame to \"M\" but the rival "
                      "makes it \"corrupt\".",
        "witness": _witness('[("backend", "A"), ("mode", "M")]',
                            '[("backend", "B"), ("mode", "M")]'),
    },
]

# ---------------------------------------------------------------------------
# Nagini -> lean accounting. The sibling battery has 7 SPEC cases (2 soundness
# positives, 1 admissibility, 4 uniqueness rivals) plus a 1-probe AXIOM lane.
# This bundle models the SAME purely-functional core (the scoped restore's net
# effect on the settings mapping) but as ONE pure equation over the two
# observable inputs rather than an imperative mutation of a live dict, so
# nagini's four separate postcondition clauses (survive/revert/no-spurious/frame)
# collapse into the single grounded equation `result = applyRestore orig final`.
# Every sibling case is re-expressed as an attack on / defense of that equation.
#
#   sibling case                 -> here
#   -----------------------------------------------------------------------
#   pos-reorder-writes           -> pos-pointfree             RE-EXPRESSED
#   pos-local-rename             -> pos-immutable-let         RE-EXPRESSED
#   admiss-requires-facts        -> admiss-ground-f2p         RE-EXPRESSED
#   weak-revert-distinguished    -> weak-revert-distinguished PORTED (the fix)
#   weak-no-revert-ordinary      -> weak-no-revert-ordinary   PORTED
#   weak-revert-wrong-value      -> weak-revert-wrong-value   PORTED
#   weak-corrupt-third-key       -> weak-corrupt-third-key    PORTED (frame facet)
#   (no sibling case)            -> weak-invent-key           ADDED (no-spurious)
#   AXIOM_TESTS (1, A-reference) -> (none)                    DROPPED (see below)
#
# ADDED (weak-invent-key): the sibling pins NO-SPURIOUS as its own postcondition
#   clause (3) `Forall k: k in params ==> Old(k in params)`, and its
#   corrupt-third-key rival attacks clauses (3)/(4) TOGETHER because on a mutable
#   dict a write to an absent key both invents membership and breaks the frame.
#   On this carrier the two come apart: overlaying a wrong VALUE at a shared key
#   and overlaying an entry at an ABSENT key are different edits to the equation's
#   right-hand side (one changes an entry, the other the list's length). The ported
#   corrupt-third-key rival only does the former, so the membership half of the
#   sibling's clause (3) was defended by the equation but never PROBED. This rival
#   closes that: its witness point gives orig and final an identical key set, so
#   the only difference between spec and rival is the invented entry.
#
# RE-EXPRESSED (pos-pointfree / pos-immutable-let): the sibling's two positives
#   reorder two straight-line dict writes and rename a local. This carrier's impl
#   is a two-line imperative scaffold with the same net effect; the analogous
#   "structurally different but correct" reshapes are (a) returning the overlay
#   expression point-free and (b) binding the erased snapshot to an immutable
#   `let`. Both are definitionally the frozen body, so the frozen `intro; rfl`
#   proof still closes (verified with real builds).
# RE-EXPRESSED (admiss-ground-f2p): the sibling asserts the Requires-derived facts
#   for a normal input. The frozen theorem here carries NO precondition (the
#   equality is unconditional), so the honest analogue is to discharge the
#   POSTCONDITION at the smallest F2P-shaped input (distinguished key changed by
#   the body, one ordinary key) as a `have`, proving the behavior is satisfiable
#   at a normal input, then close the frozen obligation verbatim.
# VACUOUS (frame/permission mutation): the sibling itself notes there is no
#   half-permission read-only input to overwrite (its mapping is full-permission
#   because it is the mutated object). On this referentially transparent carrier
#   it is doubly vacuous — no `mut` input binder, no aliasing, no heap cell. The
#   frame ANALOG the sibling DOES probe (corrupt a third framed key) IS ported as
#   weak-corrupt-third-key. No permission-mutation substitute is fabricated.
# DROPPED (AXIOM_TESTS): the sibling's single axiom-lane probe is an A-reference
#   deep-model check — it validates nagini's Python dict copy/del/update model
#   against the real CPython primitives. That is a nagini-carrier concern and
#   belongs to G-AX regardless. This Lean bundle declares no `opaque` callee and
#   consumes no `axiom` (the restore is modeled deeply as association-list ops
#   over the observable inputs), so there is nothing to probe and the gate
#   ignores AXIOM_TESTS.
#
# POINT SPREAD. The five reject witnesses probe five DISTINCT input tuples
# (pts=5):
#   (orig, final) =
#     ([(backend,A)],            [(backend,B)])              weak-revert-distinguished
#     ([(backend,agg),(mode,X)], [(backend,aardvark),(mode,Y)])
#                                                            weak-no-revert-ordinary
#     ([(backend,A),(mode,M),(dpi,100)],
#      [(backend,B),(mode,N),(dpi,200)])                     weak-revert-wrong-value
#     ([(backend,A),(mode,M)],   [(backend,B),(mode,M)])     weak-corrupt-third-key
#     ([(backend,agg),(dpi,100)],[(backend,aardvark),(dpi,100)])
#                                                            weak-invent-key
#   Both binders (orig, final) vary across them, and the variation is MEANINGFUL
#   rather than two spellings of one point: the mappings range over one, two and
#   three keys; the distinguished key is changed by the body in four of them and
#   held fixed in none; an ordinary key is changed by the body in three and held
#   FIXED in two (weak-corrupt-third-key and weak-invent-key), which is what makes
#   those two refute on the frame/membership facet rather than on the revert facet.
#   So neither binder is pinned, and no two witnesses differ only by renaming.
#
# AUDIT NOTE (independent re-derivation of the reject lane; every claim below is
# from a real build, not an argument):
#   * All five rivals were confirmed to differ from `applyRestore orig final`
#     OBSERVABLY, by evaluating both mappings at an in-domain point rather than by
#     inspecting their source — so none is a mere reshape that the frozen `rfl`
#     rejects for being differently spelled. The evaluation also shows HOW each
#     differs (wrong value at the distinguished key / at an ordinary key / a
#     constant-collapsed value / a corrupted value / an extra entry), which is the
#     facet its rationale claims.
#   * Every witness was rebuilt against its rival (must hold) and against the
#     frozen solution (must fail), and each gold-side failure was read: all five
#     are `decide` proving the negated equation FALSE, i.e. a SEMANTIC refutation
#     of the concrete claim. None fails on gold for a missing identifier, a type
#     error, an unfolding failure or a timeout, so each is a genuine discriminator.
#   * No witness binds anything in its head, so there are no hypotheses whose
#     satisfiability could be in question and the gate's consistency probe is not
#     reached. This is a property of the witnesses (all inputs are ground list
#     literals that compute), not an untested assumption.
#   * Two witnesses were RE-POINTED during the audit: they previously refuted at
#     mappings carrying no distinguished entry at all. Those builds discriminated
#     correctly, but at an input outside the modeled domain (the settings mapping
#     always carries that entry), so the refutation was weaker than the rationale
#     implied. Both now refute in-domain, and the re-pointed witnesses were
#     re-verified with the same two builds.
AXIOM_TESTS = []
