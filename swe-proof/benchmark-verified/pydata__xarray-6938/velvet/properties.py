"""properties.py — G-PBT falsification battery for pydata__xarray-6938 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes and
stamps with a verdict. Each SPEC case is a full ``Solution.lean`` variant that
shares the FROZEN spec byte-for-byte (region surgery: only text inside the
``-- impl-start`` / ``-- impl-end`` region, or inside the ``prove_correct``
tactic body, is changed — both of which the consumer spec view elides, so
``markers.same_spec`` holds and the ``prove_correct reifyIndependent``
obligation survives with a byte-identical statement) and swaps in a candidate
implementation; it is checked by the real verifier. ``expect:"verify"`` passes
iff (in scope AND verifies); ``expect:"reject"`` passes iff (in scope AND does
NOT verify AND its refutation ``witness`` discriminates: the witness must
ELABORATE against the rival and FAIL against the frozen solution).

DEFENDED SURFACE. One contracted method, over an explicit object store and an
allocation frontier:

  reifyIndependent (self : Handle) (mut store : Store) (mut nextFresh : Handle)
      return (res : Handle)
    require self < nextFresh                              (P1)
    ensures res = nextFreshOld                            (C1)
    ensures nextFresh = nextFreshOld + 1                  (C2)
    ensures res ≠ self                                    (C3)
    ensures store res = storeOld self                     (C4)
    ensures store self = storeOld self                    (C5)
    ensures ∀ h, h ≠ res → store h = storeOld h           (C6)

The method re-presents the source object. ``Handle`` is an object's identity,
``Store = Handle → Payload`` the live map from each object to its mutable
per-object state, ``nextFresh`` the allocation frontier (``P1``: the source is a
live object, i.e. below the frontier). SIX independent top-level clauses, every
one load-bearing and every one pinned to the method's own inputs — there is no
opaque answer-key oracle anywhere in the contract (the ``axioms`` region declares
none), so C1–C6 are grounded, not echoes:

  (C1) FRESHNESS — the result's identity is the allocation frontier's value at
       call time, i.e. an identity no live object holds.
  (C2) FRONTIER — the frontier advances by exactly one: an allocation happened,
       and the identity just handed out will never be handed out again.
  (C3) DISTINCTNESS — the result is NOT the source. This is the reported defect:
       a re-presentation that hands back the source itself lets a caller's later
       write to the result reach the source.
  (C4) CONTENT — the result's state is the source's state AT CALL TIME: the
       re-presentation carries the source's per-object state forward.
  (C5) SOURCE FRAME — the source's own state is untouched by the operation.
  (C6) GLOBAL FRAME — no other live object's state changes.

C3 + C1/C2 + C6 together are what make "the result is independent": the result's
slot is disjoint from every live slot, so a later write through the result
cannot be observed through the source. That is exactly the guarantee the failing
test observes.

BINDER STRUCTURE (read before judging binder coverage). Three input binders:
``self`` (the source's identity), ``store`` (the live state map), ``nextFresh``
(the frontier). C1/C2 depend on ``nextFresh``; C3 on ``self`` and ``nextFresh``;
C4/C5 on ``self`` and ``store``; C6 on ``store`` and the result. The eight reject
witnesses sit at EIGHT DISTINCT input points and vary all three: ``self`` over
{0, 1, 2, 3}, ``nextFresh`` over {4, 5, 6, 7, 8, 9}, and ``store`` over four
distinct shapes (a two-valued map keyed at 0, a constant map, a two-valued map
keyed at 1, a two-valued map keyed at 2). No binder is pinned across the
battery, and P1 (``self < nextFresh``) holds at every one of the eight points —
a refutation at an inadmissible input would attribute nothing to the spec.

WITNESS FORM — why the tester route is unavailable here. The sibling velvet
``…Tester args = false`` route needs a DECIDABLE postcondition, and C6 quantifies
``∀ h : Handle`` over an infinite carrier: ``prove_postcondition_decidable_for``
leaves ``Decidable (∀ (h : Handle), h ≠ res → store h = storeOld h)`` unsolved
(measured). So each witness instead ``extract_program_for``s the rival — which
needs no decidability, it merely names ``reifyIndependentExec`` — and states, at
ONE concrete admissible input, that a DECIDABLE projection of the rival's own
result differs from what the postcondition demands:

    ((reifyIndependentExec <self> <store> <nextFresh>).run).1        -- res
    ((reifyIndependentExec <self> <store> <nextFresh>).run).2.1 <h>  -- store at h
    ((reifyIndependentExec <self> <store> <nextFresh>).run).2.2      -- frontier

each an ``Int``/``Payload`` equality that ``simp [NonDetT.run, DivM.run,
Function.update]`` decides. Against the FROZEN solution the same statement fails
(gold allocates a fresh identity and copies the slot, so every projection reads
the correct value and the goal reduces to ``False``) — the required
discrimination. Every witness binds NO hypotheses (all three inputs are concrete
literals / explicit ``fun h => if … then … else …`` maps), so the consistency
probe is trivially satisfiable and no opaque-term conditioning is needed. No
banned token (``sorry``/``admit``/``native_decide``/``axiom``/``opaque``).

ADVERSARIAL READ of the nagini classes on THIS carrier:

  * FRAME / PERMISSION-MUTATION (the sibling's two MANDATORY rivals) — VACUOUS
    AS A PERMISSION MECHANISM. The sibling holds the source at a fractional read
    permission and writes it (a field reassignment, and an in-place append to the
    read-only list) to trip INSUFFICIENT PERMISSION before any postcondition is
    considered. Lean and Velvet are referentially transparent: there is no heap,
    no aliasing and no fractional-permission arithmetic to trip, so the
    MECHANISM has no counterpart and none is fabricated. But the BEHAVIOUR those
    two rivals guarded — the operation must not perturb the source, nor anything
    else live — is NOT lost: it is stated at the value level as C5 (source frame)
    and C6 (global frame) on the ``mut store`` binder, and each is attacked by
    its own rival below (``weak-clobber-source`` for C5, ``weak-clobber-other``
    for C6). The two are NOT independently isolable, and only one direction is:
    the source is itself a live non-result object, so C5 and C6 overlap at
    ``h = self`` and any rival that perturbs the source breaks both —
    ``weak-clobber-source`` is C5-and-C6 by construction. The C6-ONLY direction
    is separable and is what ``weak-clobber-other`` delivers, by aiming at a
    bystander (``self - 1``) that P1 keeps strictly below the frontier and
    arithmetic keeps off the source, so C1/C2/C4/C5 hold on every admissible
    input. Mechanism vacuous; behaviour fully exercised.

  * DIVERGENCE / NON-TERMINATION — CLOSED BY THE SEMANTICS OPTION, so there is
    nothing left for a reject case to attack. The sibling carries the obligation
    as a total-correctness measure the copy loop must discharge. This bundle runs
    under ``set_option loom.semantics.termination "total"``, so the checker
    refuses a non-terminating implementation OUTRIGHT, before any postcondition is
    considered. Confirmed by direct build on THIS bundle (audit, re-measured): an
    impl whose body is a non-terminating ``while true`` loop followed by the
    aliasing ``return self`` is REJECTED (exit 1) with
    ``error: Decreasing annotations are required in total correctness semantics``,
    under a bare ``loom_solve``, under the frozen positional script, and under an
    order-insensitive finisher alike — the verdict is the ``set_option``, not the
    tactic. So the sibling's total-correctness obligation is PRESERVED here rather
    than dropped, and the class is not a spec hole on this bundle. (An earlier
    version of this bullet set the result against a corpus census of ``partial``
    bundles versus ``total`` ones, taken from an internal findings doc. That census
    is withdrawn: all 500 velvet bundles set ``"total"``, and the ``set_option``
    elaborator itself runs ``openScope `TotalCorrectness``
    (``Loom/MonadAlgebras/WP/Options.lean``, lines 169-186), so the option and the
    ``open`` cannot disagree and there is no split to be on a side of.) No reject
    case is shipped for it nonetheless, and the reason
    is a WITNESS-side one: the rejection needs a refutation witness, and a witness
    file splices the rival's ``method`` block in with the obligations stripped, so
    the same ``Decreasing annotations are required`` error fires in the witness
    file too and the rival-side build cannot succeed (measured: exit 1 on the
    rival half, which the gate reads as ``witness-unproven``). The class is
    therefore DEFENDED BY THE SEMANTICS and inexpressible as a witnessed reject
    case — not admitted, and not silently dropped.

  * UNGROUNDED-ORACLE ECHO — N/A. C1–C6 are pinned to the method's own inputs
    (``nextFreshOld``, ``self``, ``storeOld``); the ``axioms`` region declares no
    ``axiom`` (the re-presentation is modeled DEEPLY as a fresh allocation plus a
    slot copy — an A-reference validated against the real callee by G-AX, not a
    consumed contract). There is no answer key for a rival to echo.

AXIOM lane: dropped. ``AXIOM_TESTS = []``, as in the sibling: this bundle
consumes no ``axiom``, its one deep-model reference is G-AX's job
(``axiom_check.py`` / mapping.md §3.1), and the G-PBT gate ignores
``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "pydata__xarray-6938"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchor. The ENTIRE frozen impl body including its marker
# ---- lines; lies wholly inside the single `-- impl-start`/`-- impl-end` region
# ---- and is unique in Solution.lean (both asserted at load by _swap).
_GOLD_IMPL = (
    "    -- impl-start\n"
    "    let r := nextFresh\n"
    "    store := Function.update store r (store self)\n"
    "    nextFresh := nextFresh + 1\n"
    "    return r\n"
    "    -- impl-end"
)
assert _BASE.count(_GOLD_IMPL) == 1, "frozen impl region drifted from expected text"

# ---- proof-body anchor. A `prove_correct` tactic body is elided from the
# ---- consumer spec view (only the obligation header is kept), so a case may
# ---- retune the script without touching the spec or dropping the obligation.
# ---- Unique in the file.
_GOLD_PROOF = (
    "prove_correct reifyIndependent by\n"
    "  loom_solve\n"
    "  · intro h hne; exact Function.update_of_ne hne _ _\n"
    "  · exact Function.update_of_ne (ne_of_lt require_1) _ _\n"
    "  · exact Function.update_self _ _ _"
)
assert _BASE.count(_GOLD_PROOF) == 1, "frozen proof body drifted from expected text"

# The frozen script's three bullets are POSITIONAL. An in-region `assert` adds a
# goal, which shifts them; this order-insensitive form closes exactly the same
# three goals plus a decidable closed side-condition. Used only by the
# admissibility case (a variant may retune the tactic body; the obligation
# header is untouched, so `variant_scope` is satisfied).
_FLEX_PROOF = (
    "prove_correct reifyIndependent by\n"
    "  loom_solve <;>\n"
    "    first\n"
    "      | (intro h hne; exact Function.update_of_ne hne _ _)\n"
    "      | exact Function.update_of_ne (ne_of_lt require_1) _ _\n"
    "      | exact Function.update_self _ _ _\n"
    "      | decide"
)


def _impl(body):
    """Full Solution.lean variant with ONLY the impl body replaced (frozen proof
    kept — a rival's rejection is carried by its witness, not by the script)."""
    return _swap(_BASE, _GOLD_IMPL,
                 "    -- impl-start\n" + body + "\n    -- impl-end")


def _impl_reproved(body, new_proof):
    """Impl body replaced AND the tactic body retuned (the admissibility case,
    whose in-region assert adds a goal the positional bullets cannot absorb)."""
    return _swap(_impl(body), _GOLD_PROOF, new_proof)


# ---- witness preamble. `extract_program_for` needs no decidability instance
# ---- (it just names `reifyIndependentExec`), which is what makes this route
# ---- available where the tester route is not: C6's `∀ h : Handle` is
# ---- undecidable, so `prove_postcondition_decidable_for` cannot synthesise the
# ---- instance `derive_tester_for` requires (measured). Checked in a file whose
# ---- `prove_correct` block the gate has stripped, so no tactic script can mask
# ---- the verdict. No `axiom`/`sorry`/`native_decide`.
def _witness(claim):
    return (
        "extract_program_for reifyIndependent\n\n"
        f"example : {claim} := by\n"
        "  unfold reifyIndependentExec reifyIndependent\n"
        "  simp [NonDetT.run, DivM.run, Function.update]\n"
    )


# ---- the four store shapes the witnesses probe. Each is a total map; the
# ---- two-valued ones make the frame clauses observable (a clobbered slot reads
# ---- a value no admissible run could produce).
_S_AT0 = "(fun h => if h = 0 then [1] else [])"
_S_CONST = "(fun _ => [7])"
_S_AT1 = "(fun h => if h = 1 then [3, 4] else [5])"
_S_AT2 = "(fun h => if h = 2 then [1, 2] else [9])"


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally DIFFERENT but CORRECT impls
    # that MUST verify, else the spec is SPEC-TOO-STRONG on impl shape. Both keep
    # the fresh allocation and the slot copy (so C1–C6 all still discharge) and
    # reshape only the executable surface, so the frozen positional script still
    # closes. Both confirmed with real builds (exit 0).
    # =====================================================================
    {
        "id": "pos-control-bind-payload-bump-first",
        "kind": "soundness",
        "expect": "verify",
        # Reshape, mirroring the sibling's positive control (read the copied
        # content into a typed local before writing it): bind the source's state
        # to a local `payload`, ADVANCE THE FRONTIER FIRST, then write the
        # captured state into the already-reserved slot. The reserved identity
        # `r` is read before the bump, so the allocated identity, the frontier's
        # post-value and the written content are all unchanged on every input.
        "module": _impl(
            "    let r := nextFresh\n"
            "    let payload := store self\n"
            "    nextFresh := nextFresh + 1\n"
            "    store := Function.update store r payload\n"
            "    return r"),
        "rationale": "a correct reshape: capture the source's state in a typed "
                     "local, advance the frontier BEFORE writing the reserved "
                     "slot, then write the captured state. `r` is read from the "
                     "frontier before the bump, so the allocated identity (C1), "
                     "the frontier post-value (C2), the distinctness (C3), the "
                     "copied content (C4) and both frames (C5/C6) are identical to "
                     "gold on every admissible input — the two statements touch "
                     "independent binders. Must verify; if it did not, the spec "
                     "would be SPEC-TOO-STRONG on statement order and local "
                     "binding. (Sibling: pos-control-clone-reshape.)",
    },
    {
        "id": "pos-control-commuted-bump",
        "kind": "soundness",
        "expect": "verify",
        # Reshape the frontier advance into the commuted arithmetic form
        # `1 + nextFresh`. Equal to `nextFresh + 1` on `Int`, so C2 is unchanged;
        # every other clause is untouched. A local-shape reshape that a `let`
        # temporary would otherwise hide.
        "module": _impl(
            "    let r := nextFresh\n"
            "    store := Function.update store r (store self)\n"
            "    nextFresh := 1 + nextFresh\n"
            "    return r"),
        "rationale": "a correct reshape of the frontier advance into the commuted "
                     "arithmetic form `1 + nextFresh` (equal to `nextFresh + 1` on "
                     "`Int`), with the allocation and the slot copy unchanged. C2 "
                     "still holds and C1/C3–C6 are untouched, so a correct impl "
                     "must verify — else SPEC-TOO-STRONG on the arithmetic form of "
                     "the frontier clause, which is the clause `weak-no-bump` "
                     "attacks.",
    },

    # =====================================================================
    # ADMISSIBILITY — the sibling builds a fresh source object shaped like the
    # failing test's input and self-calls the operation on it, to show the
    # fractional-permission precondition is establishable for a legitimate input.
    # Here the precondition is the single scalar P1 (`self < nextFresh`), so the
    # "can a legitimate input satisfy it" reading needs no self-call — but the
    # residual admissibility risk does exist and is re-aimed at: that the admitted
    # domain is NON-DEGENERATE at the point that matters. This case discharges an
    # in-region assert pinning the failing test's shape — a live source strictly
    # below the frontier, a frontier value DISTINCT from that source (so the
    # allocated identity is a real second object, not the source again), and a
    # NON-EMPTY per-object state (so the copied content is observable at all).
    # If that corner were excluded, C3/C4 would be satisfiable only degenerately.
    # The first two conjuncts are stated over the METHOD'S BINDERS, so the probe
    # is about the ADMITTED DOMAIN and not about closed arithmetic: they are
    # dischargeable only from `require_1`, at whatever input the method is called
    # on. The impl is kept verbatim so C1–C6 still discharge; the tactic body is
    # retuned only because the assert adds a goal the positional bullets cannot
    # absorb. Every conjunct is LIVE — audit-measured, four flips, four failures:
    # negating either binder-level conjunct leaves the whole assert unprovable
    # (`Expected type must not contain free variables self < nextFreshOld ∧ …`),
    # and negating either literal one leaves `decide proved that the proposition
    # … is false`.
    # =====================================================================
    {
        "id": "admiss-live-source-below-frontier",
        "kind": "admissibility",
        "expect": "verify",
        # The assert has TWO halves, and the binder half is the load-bearing one.
        # A conjunct over closed literals alone (`0 < 5`) is discharged by
        # `decide` without ever consulting the precondition, so on its own it
        # would probe the arithmetic and not the admitted domain. The first two
        # conjuncts are therefore stated over the METHOD'S OWN BINDERS — `self <
        # nextFresh` is P1 itself, and `nextFresh ≠ self` is the fact that the
        # identity C1 hands out is a SECOND object — so they are dischargeable
        # only from `require_1`, at the arbitrary input the method is called on
        # rather than at one chosen point. The literal half is kept because it
        # pins the failing test's concrete shape.
        "module": _impl_reproved(
            "    assert (with_name_prefix `adm\n"
            "      (self < nextFresh ∧ nextFresh ≠ self ∧ (0 : Handle) < (5 : Handle) ∧\n"
            "       (5 : Handle) ≠ (0 : Handle) ∧ ([120] : Payload) ≠ []))\n"
            "    let r := nextFresh\n"
            "    store := Function.update store r (store self)\n"
            "    nextFresh := nextFresh + 1\n"
            "    return r",
            _FLEX_PROOF),
        "rationale": "the admitted domain is non-degenerate, and non-degenerate AT "
                     "AN ARBITRARY ADMISSIBLE INPUT rather than at one chosen "
                     "point: the assert's first two conjuncts are stated over the "
                     "method's own binders, so they are dischargeable ONLY from the "
                     "precondition. `self < nextFresh` is P1 itself — the admitted "
                     "domain is inhabited by a genuinely live source — and "
                     "`nextFresh ≠ self` is the fact that the identity C1 hands out "
                     "is a SECOND object, so C3's `res ≠ self` is a real transition "
                     "rather than vacuous; both follow from `require_1` and from "
                     "nothing else, which is what makes this a PRECOND probe and "
                     "not an arithmetic one. The remaining conjuncts pin the "
                     "failing test's concrete shape: a live source below the "
                     "frontier (`0 < 5`), a distinct frontier value (`5 ≠ 0`), and "
                     "a NON-EMPTY per-object state (`[120] ≠ []`, so C4's copied "
                     "content is observable). All five are LIVE — flipping any one "
                     "of them fails the build (four flips measured, each rejected "
                     "at the assert, the binder-level flips reported as an "
                     "unprovable `self < nextFreshOld ∧ …` and the literal ones as "
                     "`decide proved that the proposition … is false`). The "
                     "in-region assert must discharge "
                     "— if this corner were inadmissible the precondition would be "
                     "PRECOND-TOO-STRONG exactly where the behaviour matters — and "
                     "the impl is kept verbatim so C1–C6 discharge too. (Sibling: "
                     "admiss-fresh-coordvar, re-aimed: there is no fractional "
                     "permission to establish here, so the probe targets "
                     "non-degeneracy of the scalar domain instead of a self-call.)",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each carrying a machine-checked refutation witness at
    # its OWN concrete admissible input plus the refinement argument that its
    # faithful real counterpart would NOT resolve the failing test. Every one of
    # the six clauses is attacked, and the eight witnesses probe eight distinct
    # input points (see BINDER STRUCTURE above).
    # =====================================================================
    {
        "id": "weak-alias-return-source",
        "kind": "uniqueness",
        "expect": "reject",
        # THE reported defect, and the bundle's own prepatch: hand back the SOURCE
        # itself. No allocation, no copy — the result IS the source, so a caller's
        # later write through the result is observed through the source.
        "module": _impl("    return self"),
        "refinement": "this is the verbatim pre-change behaviour the issue reports: "
                      "the re-presentation hands back the source object rather than "
                      "an independent one, so a caller that re-presents an object "
                      "and then assigns to the result's state silently rewrites the "
                      "SOURCE's state. The failing test does exactly that — it "
                      "re-presents an object, asserts the result is not the source, "
                      "then writes the result's state and asserts the source's is "
                      "unchanged — and both assertions fail on the aliasing "
                      "behaviour. Its faithful real counterpart is the un-changed "
                      "function, which is precisely what does NOT resolve.",
        "rationale": "REJECT from C3 (`res ≠ self`), C1 (`res = nextFreshOld`) AND "
                     "C2 (`nextFresh = nextFreshOld + 1`): the body does nothing at "
                     "all, so the result is the source — neither distinct from it "
                     "nor the frontier's value, and P1 (`self < nextFresh`) makes "
                     "those two mutually exclusive, so no input can rescue it — and "
                     "the frontier never advances either. Confirmed by build: the "
                     "three unsolved obligations are exactly `res ≠ self`, "
                     "`res = nextFreshOld` and `nextFresh = nextFreshOld + 1`. This "
                     "rival is deliberately the BLUNTEST one and isolates nothing; "
                     "the near-misses that isolate single clauses are the rivals "
                     "below. If it verified the spec would admit the reported "
                     "defect outright => SPEC-TOO-WEAK. Refuted at self=0, "
                     "frontier=5 (admissible: 0 < 5), where C1 demands the result be "
                     "5 but the rival returns 0. (Sibling: weak-alias-return-self.)",
        "witness": _witness(
            f"((reifyIndependentExec 0 {_S_AT0} 5).run).1 = 0"),
    },
    {
        "id": "weak-stale-identity",
        "kind": "uniqueness",
        "expect": "reject",
        # NEAR-MISS of the alias rival, and the on-carrier form of the sibling's
        # shared-storage attack: hand out an identity that is DISTINCT from the
        # source (`self + 1`) but NOT drawn from the allocation frontier. C3 holds,
        # C4/C5 hold, the frontier still advances — but the identity handed out may
        # already belong to a live object, so the "copy" can overwrite that
        # object's state and a later write through the result is observed through
        # it. Agrees with gold over more of the domain than the alias rival, so it
        # gets its own input point.
        "module": _impl(
            "    let r := self + 1\n"
            "    store := Function.update store r (store self)\n"
            "    nextFresh := nextFresh + 1\n"
            "    return r"),
        "refinement": "a counterpart that re-presents the source under a "
                      "REUSED identity — one derived from the source rather than "
                      "obtained from a genuine allocation — yields an object that "
                      "is not the source (so a bare identity check passes) but that "
                      "shares its state slot with whatever live object already held "
                      "that identity. A caller that then writes the result's state "
                      "corrupts that object instead, which is the same class of "
                      "cross-object corruption the reported issue describes, merely "
                      "displaced onto a different victim. The failing test's "
                      "surrounding suite round-trips re-presented objects and "
                      "observes their state, so it would NOT resolve.",
        "rationale": "REJECT from C1 (`res = nextFreshOld`): the identity is derived "
                     "from the source, not drawn from the allocation frontier, so "
                     "it is not fresh — and C6's frame is violated too whenever the "
                     "reused identity is a live object other than the result. This "
                     "is the NEAR-MISS of the alias rival (C3 and both content "
                     "clauses still hold), so it is refuted at its OWN input, "
                     "self=1, frontier=9 (admissible: 1 < 9), where C1 demands the "
                     "result be 9 and the rival returns 2 — a point at which the "
                     "alias rival's witness says nothing. (Sibling: "
                     "weak-shared-storage-ctor, re-expressed: on this carrier "
                     "'shares the source's storage' is 'hands out an identity the "
                     "allocator never issued'.)",
        "witness": _witness(
            f"((reifyIndependentExec 1 {_S_CONST} 9).run).1 = 2"),
    },
    {
        "id": "weak-no-bump",
        "kind": "uniqueness",
        "expect": "reject",
        # Allocates and copies correctly but never ADVANCES the frontier, so the
        # identity just handed out is still the next one to be issued: the very
        # next re-presentation hands out the SAME identity and its copy overwrites
        # this result's state. Isolates C2 — every other clause holds.
        "module": _impl(
            "    let r := nextFresh\n"
            "    store := Function.update store r (store self)\n"
            "    return r"),
        "refinement": "a counterpart that produces the new object but does not "
                      "retire the identity it consumed leaves the allocator handing "
                      "the same identity out again, so two successive "
                      "re-presentations collide: the second's state write lands on "
                      "the first's object. The reported issue is precisely that a "
                      "re-presented object is not independent of another live one; "
                      "this reintroduces that non-independence one step later, and "
                      "the failing test's assertion that a written result leaves "
                      "the other object's state alone does not hold across the "
                      "second call. It would NOT resolve.",
        "rationale": "REJECT from C2 (`nextFresh = nextFreshOld + 1`): the frontier "
                     "is returned unchanged, so the allocation is not recorded and "
                     "the identity is not retired. C1, C3, C4, C5 and C6 are all "
                     "kept correct, so C2 is the ONLY failing clause — without this "
                     "rival a spec that dropped the frontier clause would look "
                     "fully defended. Refuted at self=3, frontier=6 (admissible: "
                     "3 < 6), where C2 demands the frontier come back 7 but the "
                     "rival returns 6.",
        "witness": _witness(
            f"((reifyIndependentExec 3 {_S_CONST} 6).run).2.2 = 6"),
    },
    {
        "id": "weak-no-content-copy",
        "kind": "uniqueness",
        "expect": "reject",
        # Allocates a genuinely fresh, distinct identity and advances the frontier
        # — but never copies the source's state into it, so the new object starts
        # from whatever the store's default at that identity is. Isolates C4.
        "module": _impl(
            "    let r := nextFresh\n"
            "    nextFresh := nextFresh + 1\n"
            "    return r"),
        "refinement": "a counterpart that allocates the new object but never "
                      "initialises it from the source produces an object with the "
                      "wrong per-object state — independent of the source, but no "
                      "longer a re-presentation OF it. The failing test reads the "
                      "re-presented object's state and requires it to match the "
                      "source's, and the surrounding suite round-trips that state "
                      "through the operation throughout, so it would NOT resolve.",
        "rationale": "REJECT from C4 (`store res = storeOld self`): nothing is "
                     "written at the allocated identity, so the result's state is "
                     "the store's incumbent value there, not the source's. C1, C2, "
                     "C3, C5 and C6 all hold, isolating the content clause. Refuted "
                     "at self=1, frontier=6, a store that maps 1 to [3, 4] and "
                     "everything else to [5] (admissible: 1 < 6): C4 demands the "
                     "result's state be [3, 4] but the rival's reads [5]. The "
                     "source's slot is chosen DISTINCT from the store's default so "
                     "the omission is observable — under a constant store this "
                     "rival would agree with gold.",
        "witness": _witness(
            f"((reifyIndependentExec 1 {_S_AT1} 6).run).2.1 6 = [5]"),
    },
    {
        "id": "weak-fabricated-content",
        "kind": "uniqueness",
        "expect": "reject",
        # The sibling's fabricate-names attack: allocate a fresh, distinct,
        # correctly-retired identity, then initialise it with a CONSTANT state
        # instead of the source's. Also attacks C4, but in the opposite direction
        # to `weak-no-content-copy`: that rival leaves the slot alone, this one
        # writes content that depends on nothing.
        "module": _impl(
            "    let r := nextFresh\n"
            "    store := Function.update store r [424242]\n"
            "    nextFresh := nextFresh + 1\n"
            "    return r"),
        "refinement": "a counterpart that builds the new object with fabricated "
                      "per-object state rather than the source's is not a "
                      "re-presentation of the source at all: callers depend on the "
                      "result carrying the source's state forward. The failing test "
                      "asserts the source's state is intact after writing the "
                      "result's, which presupposes the result started from the "
                      "source's state; the surrounding suite compares the "
                      "re-presented object's state to the original's directly. It "
                      "would NOT resolve.",
        "rationale": "REJECT from C4 (`store res = storeOld self`): the written "
                     "content is a constant, independent of both `self` and "
                     "`store`, so it differs from the source's state at every input "
                     "where the source does not happen to hold that constant. C1, "
                     "C2, C3, C5 and C6 hold, so the failure is purely the content "
                     "pin. Refuted at self=0, frontier=4 (admissible: 0 < 4), a "
                     "store mapping 0 to [1]: C4 demands the result's state be [1] "
                     "but the rival's is the fabricated constant. A DISTINCT input "
                     "point from the no-copy rival, whose witness turns on the "
                     "store's default rather than on the written value. (Sibling: "
                     "weak-fabricate-names.)",
        "witness": _witness(
            f"((reifyIndependentExec 0 {_S_AT0} 4).run).2.1 4 = [424242]"),
    },
    {
        "id": "weak-drop-first-of-content",
        "kind": "uniqueness",
        "expect": "reject",
        # The sibling's partial-domain rival, on this carrier: copy the source's
        # state MINUS its first element. Correct on the empty-state subdomain
        # (`[].tail = []`) and wrong on every non-empty one — a strictly closer
        # near-miss than the fabricating rival, so it earns its own input point at
        # a source whose state has length > 1 (where truncation is visible without
        # collapsing to the empty state).
        "module": _impl(
            "    let r := nextFresh\n"
            "    store := Function.update store r (store self).tail\n"
            "    nextFresh := nextFresh + 1\n"
            "    return r"),
        "refinement": "a counterpart that carries the source's per-object state "
                      "forward MINUS its leading component produces a re-presented "
                      "object whose state is a truncation of the original's. It "
                      "agrees with the source exactly when that state is empty, so "
                      "it would pass a smoke test on a degenerate object and fail "
                      "on every real one; the failing test starts from an object "
                      "with a one-component state and asserts the source's state "
                      "afterwards, and the surrounding suite compares full "
                      "re-presented state against the original throughout. It "
                      "would NOT resolve.",
        "rationale": "REJECT from C4 (`store res = storeOld self`): the copied "
                     "content drops the source's leading component, so it differs "
                     "from the source's state for every non-empty source — while "
                     "agreeing on the empty-state subdomain, which is what makes "
                     "this a partial-domain near-miss rather than a repeat of the "
                     "fabricating rival. Refuted at its own point, self=2, "
                     "frontier=8, a store mapping 2 to [1, 2] (admissible: 2 < 8): "
                     "C4 demands the result's state be [1, 2] but the rival's is "
                     "[2]. The two-component state is chosen so the truncation is "
                     "observable without collapsing to the empty state the rival "
                     "gets right. (Sibling: weak-drop-first-element.)",
        "witness": _witness(
            f"((reifyIndependentExec 2 {_S_AT2} 8).run).2.1 8 = [2]"),
    },
    {
        "id": "weak-clobber-source",
        "kind": "uniqueness",
        "expect": "reject",
        # The value-level counterpart of the sibling's MANDATORY frame-mutation
        # rivals (which trip a fractional-permission arithmetic that does not exist
        # here). Produces a perfectly good independent result — fresh identity,
        # frontier retired, source's state copied — but PERTURBS THE SOURCE's own
        # slot on the way. Isolates C5.
        "module": _impl(
            "    let r := nextFresh\n"
            "    store := Function.update (Function.update store self []) r (store self)\n"
            "    nextFresh := nextFresh + 1\n"
            "    return r"),
        "refinement": "a counterpart that clears the SOURCE's per-object state "
                      "while producing the re-presentation corrupts the source on "
                      "every call — the exact opposite of the change, which exists "
                      "so that re-presenting an object leaves the original "
                      "untouched. The failing test asserts the source's state is "
                      "still its original value after the operation, and this "
                      "counterpart empties it, so that assertion fails outright; "
                      "every test in the surrounding suite that reads a source's "
                      "state after re-presenting it breaks too. It would NOT "
                      "resolve.",
        "rationale": "REJECT from C5 (`store self = storeOld self`): the source's "
                     "own slot is overwritten before the result's is written, so "
                     "the source does not survive the operation unchanged. C1, C2 "
                     "and C4 are kept correct (the result is fresh, retired and "
                     "carries the source's call-time state — machine-checked at the "
                     "probed input: result 5, frontier back 6, result's state "
                     "[1, 2], three witness builds at exit 0), and C3's `res ≠ "
                     "self` holds too. C6 is collaterally broken and deliberately "
                     "so: the source is itself a live object other than the result, "
                     "so clobbering it violates the GLOBAL frame as well as the "
                     "source frame — the two clauses overlap at `h = self` by "
                     "construction, and no impl can perturb the source without "
                     "also perturbing a non-result slot. That is why C6 needs its "
                     "OWN rival at a bystander P1 keeps distinct from both the "
                     "source and the result (`weak-clobber-other`), and why the "
                     "pair is not redundant: this rival is the only one that "
                     "touches the source, that one the only one that leaves the "
                     "source alone. Value-level statement of the read-only-input "
                     "obligation the sibling enforces with fractional permissions. "
                     "Refuted at self=2, frontier=5, a "
                     "store mapping 2 to [1, 2] (admissible: 2 < 5): C5 demands the "
                     "source's state still be [1, 2] but the rival leaves it empty. "
                     "(Siblings: frame-mutate-receiver-field, "
                     "frame-mutate-receiver-list — one behavioural rival replaces "
                     "both, since this carrier has no field/contents distinction.)",
        "witness": _witness(
            f"((reifyIndependentExec 2 {_S_AT2} 5).run).2.1 2 = []"),
    },
    {
        "id": "weak-clobber-other",
        "kind": "uniqueness",
        "expect": "reject",
        # The OTHER half of the frame: leave the source alone but perturb a
        # THIRD live object's state. Isolates C6, the global frame — the clause
        # that makes "the result's slot is disjoint from every live slot" a
        # statement about the whole store rather than about the source alone.
        # Without this rival, an impl that scribbled on unrelated objects would
        # verify against a spec that only framed the source.
        #
        # The victim is ``self - 1``, NOT a hardcoded handle. A literal victim
        # does not isolate C6: at the input where the literal happens to BE the
        # source it violates C5 as well, and where it happens to be the frontier
        # it violates C4, so the rival's rejection could be attributed to a
        # clause other than the one it is here to attack. ``self - 1`` is
        # arithmetically distinct from the source on every input, and P1
        # (``self < nextFresh``) puts it strictly below the frontier, hence
        # distinct from ``res = nextFreshOld`` on every ADMISSIBLE input. So C4
        # and C5 hold throughout and C6 is the only clause this rival breaks.
        "module": _impl(
            "    let r := nextFresh\n"
            "    store := Function.update (Function.update store r (store self)) (self - 1) []\n"
            "    nextFresh := nextFresh + 1\n"
            "    return r"),
        "refinement": "a counterpart that re-presents the source correctly but "
                      "clears an UNRELATED live object's per-object state along the "
                      "way is the same cross-object corruption the reported issue "
                      "describes, aimed at a bystander instead of the source: the "
                      "operation is supposed to touch nothing but the object it "
                      "allocates. The suite around the failing test holds several "
                      "objects live and reads their state after re-presenting one "
                      "of them, so a bystander whose state is silently emptied "
                      "breaks those reads. It would NOT resolve.",
        "rationale": "REJECT from C6 (`∀ h, h ≠ res → store h = storeOld h`) and "
                     "from C6 ALONE: a live object other than the result has its "
                     "state overwritten, so the global frame fails while C5's "
                     "source frame still holds. The bystander is `self - 1`, which "
                     "is distinct from the source arithmetically and — because P1 "
                     "(`self < nextFresh`) puts it strictly below the frontier — "
                     "distinct from `res = nextFreshOld` on every admissible input, "
                     "so C1–C5 are kept correct at EVERY input rather than merely "
                     "at the probed one. This is the clause `weak-clobber-source` "
                     "does NOT attack, so without this rival a spec framing only "
                     "the source would look defended. Refuted at self=2, "
                     "frontier=7, a store mapping 2 to [1, 2] and everything else "
                     "to [9] (admissible: 2 < 7): the result is 7 and the bystander "
                     "is 1, so C6 demands 1 still read [9] but the rival empties "
                     "it. Machine-checked at that point that the OTHER clauses "
                     "hold: the result is 7 (C1), the frontier comes back 8 (C2), "
                     "the result's state is [1, 2] (C4) and the source's is still "
                     "[1, 2] (C5) — five separate witness builds, all exit 0.",
        "witness": _witness(
            f"((reifyIndependentExec 2 {_S_AT2} 7).run).2.1 1 = []"),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery ships 8 SPEC cases (1
# soundness positive, 1 admissibility, 6 uniqueness rivals — two of them the
# MANDATORY frame-mutation class) and an EMPTY axiom lane. It contracts THREE
# functions (`as_coordinate`, `independent_clone`, `as_plain`) over a
# permission-bearing heap object, and its whole defended surface is a
# permission/identity/value triple discharged by fractional-permission
# arithmetic. This bundle models the SAME behaviour on a value carrier: ONE
# method, `reifyIndependent`, over an explicit object store (`Store = Handle →
# Payload`) and an allocation frontier, with six explicit `ensures` clauses in
# place of the permission arithmetic. Carrier narrowing, not thinning: the
# sibling's three functions are one delegation chain around a single copy
# primitive, and this bundle contracts that primitive directly. Every sibling
# case is accounted for below.
#
#   sibling case (nagini)          -> here                          disposition
#   ------------------------------------------------------------------------
#   pos-control-clone-reshape      -> pos-control-bind-payload-      PORTED
#                                     bump-first
#   (no sibling counterpart)       -> pos-control-commuted-bump      ADDED (C2)
#   admiss-fresh-coordvar          -> admiss-live-source-below-      RE-AIMED
#                                     frontier
#   weak-alias-return-self         -> weak-alias-return-source       PORTED (central)
#   weak-shared-storage-ctor       -> weak-stale-identity            RE-EXPRESSED
#   weak-drop-first-element        -> weak-drop-first-of-content     PORTED
#   weak-fabricate-names           -> weak-fabricated-content        PORTED
#   frame-mutate-receiver-field    -> weak-clobber-source            RE-EXPRESSED
#   frame-mutate-receiver-list     -> (merged into weak-clobber-     MERGED
#                                      source)
#   (no sibling counterpart)       -> weak-no-bump                   ADDED (C2)
#   (no sibling counterpart)       -> weak-no-content-copy           ADDED (C4)
#   (no sibling counterpart)       -> weak-clobber-other             ADDED (C6)
#   sibling nontermination note    -> (none)                         SPEC-CLOSED
#   AXIOM_TESTS (empty there)      -> (none)                         DROPPED (G-AX)
#
# 4 ported, 2 re-expressed, 1 merged, 1 re-aimed, 4 added, 1 known hole.
#
# PORTED (pos-control-bind-payload-bump-first): the sibling's positive control
#   reads each copied element into a typed local before appending and reorders the
#   trailing framing asserts. The on-carrier analogue binds the source's state to
#   a local and reorders the two independent post-state writes (frontier advance
#   before slot write), reading the reserved identity before the bump. Verified
#   with a real build under the frozen script.
# ADDED (pos-control-commuted-bump): a second positive, so the frontier clause C2
#   — which has no sibling counterpart at all, the sibling having no allocation
#   frontier — is DEFENDED as well as attacked. Without it C2 would be attacked by
#   weak-no-bump and defended by nothing but gold's own shape.
# RE-AIMED (admissibility): the sibling allocates a test-shaped object inside the
#   impl region and self-calls the operation on it, to show the fractional
#   read-permission precondition is establishable. There is no permission to
#   establish here — the precondition is the scalar P1 `self < nextFresh` — so the
#   case is re-aimed at the residual risk that the admitted domain is DEGENERATE
#   where the behaviour matters: a live source strictly below the frontier, a
#   frontier value distinct from that source (so C3 is a real transition), and a
#   non-empty per-object state (so C4's copy is observable). The first two are
#   stated over the METHOD'S OWN BINDERS (`self < nextFresh`, `nextFresh ≠ self`),
#   so they are dischargeable only from `require_1` and the probe reaches the
#   admitted domain rather than closed arithmetic — a purely literal assert would
#   be closed by `decide` without consulting the precondition at all, which is the
#   form the audit strengthened away from. Every conjunct is LIVE (audit: four
#   flips, four failures — the binder-level ones leave the assert unprovable,
#   `Expected type must not contain free variables self < nextFreshOld ∧ …`; the
#   literal ones leave `decide proved that the proposition … is false`), and the
#   impl is kept verbatim so C1–C6 discharge too.
# RE-EXPRESSED (weak-stale-identity <- weak-shared-storage-ctor): the sibling's
#   rival returns a fresh OBJECT built directly over the receiver's storage, so
#   result and source share a slot. On this carrier the store is a total function,
#   so "shares the source's storage" has no direct form — the faithful analogue is
#   "hands out an identity the allocator never issued" (`self + 1`), which is
#   distinct from the source yet may collide with a live object, reproducing the
#   same shared-slot corruption. It is the alias rival's NEAR-MISS (C3, C4, C5 and
#   C2 all hold), so it carries its own input point.
# RE-EXPRESSED + MERGED (weak-clobber-source <- frame-mutate-receiver-field +
#   frame-mutate-receiver-list): both sibling rivals write the read-only receiver
#   to trip INSUFFICIENT PERMISSION — one reassigning the field, one appending to
#   the list it names. That MECHANISM is vacuous here (no heap, no aliasing, no
#   fractional permissions), and the porting map says not to fabricate a
#   substitute for a vacuous class. But the BEHAVIOUR the two rivals guarded is
#   NOT vacuous on this carrier: it is clause C5, stated at the value level over
#   the `mut store` binder, and it is attacked directly. The two collapse into ONE
#   rival because this carrier has no field-vs-contents distinction to split them
#   along: an object's mutable state is one store slot, and there is exactly one
#   way to perturb it. Reported as a merge, not as two cases. Note that this rival
#   breaks C6 as well as C5 and NECESSARILY so — the source is a live non-result
#   object, so C5 and C6 overlap at `h = self` and no rival can break C5 alone.
#   That is why the C6-only direction needs its own rival at a bystander P1 keeps
#   distinct from both source and result (weak-clobber-other), and why the pair is
#   not redundant.
# ADDED (weak-no-bump, weak-no-content-copy, weak-clobber-other): three clauses
#   have no sibling counterpart because the sibling's permission arithmetic
#   discharges them implicitly rather than stating them — C2 (the frontier
#   advance; the sibling has no allocator to model), C4 as an OMISSION rather than
#   a fabrication (the sibling's copy loop cannot be "skipped" while still
#   type-checking), and C6 (the global frame; the sibling's disjointness is a
#   consequence of permission accounting, not a clause). Each is an independent
#   top-level clause of THIS spec, so each gets its own rival — a spec that
#   dropped any one of them would otherwise pass this battery.
# CLOSED BY SEMANTICS (divergence / non-termination): the sibling carries the
#   obligation as a total-correctness measure (`MustTerminate`) that its copy loop
#   must discharge, and its audit's nontermination rival attacks it. That
#   obligation is PRESERVED here, by the semantics option rather than by a clause:
#   this bundle sets `loom.semantics.termination "total"`, so the checker refuses a
#   non-terminating implementation outright, before any `ensures` clause is
#   considered. Re-measured by the audit with three real builds on THIS bundle: an
#   impl whose body is a non-terminating `while true` loop followed by the aliasing
#   `return self` is REJECTED (exit 1) under a bare `loom_solve`, under the frozen
#   positional script, and under an order-insensitive finisher — always with
#   `error: Decreasing annotations are required in total correctness semantics`, so
#   the verdict comes from the `set_option` and not from a tactic mismatch. This
#   spec therefore REJECTS the diverging rival. (An earlier version of this entry
#   placed the bundle in a `total` cohort against a `partial` one, citing an
#   internal findings doc; that census is withdrawn, since all 500 velvet bundles
#   set "total" and the `set_option` elaborator itself runs
#   `openScope `TotalCorrectness`.) Nothing is escalated from here. No reject case
#   is
#   shipped anyway, for a WITNESS-side reason: a witness file splices the rival's
#   `method` block in with the obligations stripped, so the same `Decreasing
#   annotations are required` error fires in the witness file and the rival-side
#   build — the half that must SUCCEED — cannot (measured: exit 1, which the gate
#   reads as `witness-unproven`). Defended by the semantics, inexpressible as a
#   witnessed reject case: neither a spec hole nor a battery gap.
# DROPPED (AXIOM_TESTS): the axiom lane is G-AX's job and is empty on the sibling
#   too. This bundle ships no `axiom`; its one deep-model reference (fresh
#   allocation + slot copy) is validated against the real callee by
#   axiom_check.py / G-AX, per mapping.md §3.1. The gate ignores AXIOM_TESTS
#   regardless.
#
# CLAUSE / BINDER COVERAGE. All six independent top-level clauses are ATTACKED:
#   C1 by weak-alias-return-source AND weak-stale-identity (the aliasing and the
#   reused-identity directions of freshness); C2 by weak-no-bump; C3 by
#   weak-alias-return-source; C4 by weak-no-content-copy, weak-fabricated-content
#   AND weak-drop-first-of-content (omission, fabrication, and partial-domain
#   truncation — three genuinely different ways to get the content wrong, the last
#   a near-miss correct on the empty-state subdomain); C5 by weak-clobber-source;
#   C6 by weak-clobber-other. All six are DEFENDED by the two positive controls
#   and the admissibility case.
#
#   Which clause each rival ACTUALLY breaks is machine-checked, not asserted: the
#   audit rebuilt every rival under an order-insensitive finisher that closes
#   whatever is provable and leaves the rest NAMED in the `unsolved goals` error,
#   so the obligation names below are read off real build output.
#
#     rival                        clauses left unsolved
#     weak-alias-return-source     C3, C1, C2      (blunt: does nothing at all)
#     weak-stale-identity          C1              (isolates freshness)
#     weak-no-bump                 C2              (isolates the frontier)
#     weak-no-content-copy         C4              (isolates content, by omission)
#     weak-fabricated-content      C4              (isolates content, by fabrication)
#     weak-drop-first-of-content   C4              (isolates content, by truncation)
#     weak-clobber-source          C5, C6          (see below — overlap is inherent)
#     weak-clobber-other           C6, C5*, C4*    (*only via the finisher's shared
#                                                   goal shape; the CLAIM this rival
#                                                   makes is C6-only, see next para)
#
#   The two frame rivals overlap and cannot be separated the other way round.
#   C5 (`store self = storeOld self`) and C6 (`∀ h, h ≠ res → store h = storeOld h`)
#   both constrain `h = self`, because the source is itself a live non-result
#   object, so ANY impl that perturbs the source breaks both. weak-clobber-source
#   is therefore C5-and-C6 by construction and no rival can be C5-only. The
#   converse IS separable and is what weak-clobber-other must deliver: a bystander
#   distinct from both the source and the result, so C5 holds and only C6 fails.
#   That requires the victim to be a function of `self`, not a literal — with a
#   hardcoded victim the rival breaks C5 at the input where the literal is the
#   source and C4 where it is the frontier, which the audit measured directly on
#   the earlier form of this case (at self=3 a witness for `store 3 = []`
#   ELABORATED against it, i.e. it clobbered the source; at nextFresh=3 likewise
#   for the result's slot). Repaired to `self - 1`, which P1 keeps strictly below
#   the frontier and arithmetic keeps off the source, so C1/C2/C4/C5 hold on every
#   admissible input — each confirmed by its own witness build at the probed point.
#
#   The eight reject witnesses probe EIGHT DISTINCT input points (pts=8):
#     self  store                              nextFresh  case
#     0     h=0 -> [1], else []                5          weak-alias-return-source
#     1     const [7]                          9          weak-stale-identity
#     3     const [7]                          6          weak-no-bump
#     1     h=1 -> [3,4], else [5]             6          weak-no-content-copy
#     0     h=0 -> [1], else []                4          weak-fabricated-content
#     2     h=2 -> [1,2], else [9]             8          weak-drop-first-of-content
#     2     h=2 -> [1,2], else [9]             5          weak-clobber-source
#     2     h=2 -> [1,2], else [9]             7          weak-clobber-other
#   so `self` is varied over {0, 1, 2, 3}, `nextFresh` over {4, 5, 6, 7, 8, 9},
#   and `store` over four distinct shapes — no binder is pinned across the
#   battery, and P1 (`self < nextFresh`) holds at all eight, so no refutation is
#   stated at an inadmissible input. The store shapes are chosen so the content
#   and frame clauses are OBSERVABLE: weak-no-content-copy needs the source's slot
#   to differ from the store's default (under a constant store it would agree with
#   gold), and weak-drop-first-of-content needs a state of length > 1 (on the
#   empty state it is correct). No two rivals share an input point, so no
#   near-miss borrows another's demonstration.
#
# WITNESS FORM. The `…Tester args = false` route is UNAVAILABLE: C6 quantifies
#   `∀ h : Handle` over an infinite carrier, so `prove_postcondition_decidable_for
#   reifyIndependent` leaves `Decidable (∀ (h : Handle), h ≠ res → store h =
#   storeOld h)` unsolved and `derive_tester_for` cannot be reached (measured).
#   Each witness therefore `extract_program_for`s the rival — extraction needs no
#   decidability instance — and states, at one concrete admissible input, that a
#   decidable projection of the rival's own result (`.1` = the identity, `.2.1 h` =
#   the store at h, `.2.2` = the frontier) differs from what the postcondition
#   demands, closed by `simp [NonDetT.run, DivM.run, Function.update]`. No witness
#   binds a hypothesis (all inputs are literals / explicit maps), so the gate's
#   consistency probe is trivially satisfiable and no opaque-term conditioning is
#   needed. Confirmed empirically with scripts/lean_verify.sh: every witness
#   ELABORATES against its rival (exit 0) and FAILS against the frozen solution
#   (exit 1, `unsolved goals ⊢ False` — gold's fresh allocation and slot copy make
#   every probed projection read the correct value), and every rival module does
#   NOT verify. Both halves seen, per rival, with two real builds each.
AXIOM_TESTS = []
