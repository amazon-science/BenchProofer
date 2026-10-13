"""properties.py — G-PBT falsification battery for sympy__sympy-23950 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed
— both of which the consumer spec view elides, so ``markers.same_spec`` holds
and the ``prove_correct`` obligation survives) and swaps in a candidate
implementation. It is checked by the real verifier. ``expect:"verify"`` passes
iff (in scope AND verifies); ``expect:"reject"`` passes iff (in scope AND does
NOT verify AND its refutation ``witness`` discriminates: the witness must
elaborate against the rival and FAIL against the frozen solution).

DEFENDED SURFACE (one contracted method over one binder):

  asSet (a : MembershipAssertion)   ensures out = Except.ok a.container

An assertion "this element belongs to this collection", read as a set, IS that
collection: the conversion must SUCCEED (a normal ``Except.ok`` outcome, never
the decline arm) and hand back the assertion's SECOND stored component
(``a.container``) — never the element being tested (``a.elem``), never a
fabricated collection, never a decline. The single load-bearing clause
``out = Except.ok a.container`` pins all three at once: the success tag, the
value selected, and that the value is the container component specifically.

The two F2P-observable wrong behaviours the spec must reject:
  (a) returning the ELEMENT instead of the collection — the assertion read back
      as itself / the wrong operand; the discriminator is the value inside
      ``Except.ok`` being ``a.container``, and ``a.elem`` is a distinct
      component the spec does not accept.
  (b) DECLINING to produce the collection (the pre-image state) — the success
      arm is required, so a decline (``Except.error``) cannot satisfy the
      clause.

CARRIER NOTE — everything here is transparent. Both components are modeled as
distinct ``Nat`` identifiers (the weakest carrier that still discriminates
"returns the collection" from "returns the element" from "declines"); there is
no opaque callee. Every reject witness therefore lives on a concrete
``decide``-able point and needs no conditioning on the carrier.

ADVERSARIAL READ of the classes:
  * FRAME-SUBSTITUTE — LIVE, one arm of two. The nagini sibling writes back
    into a half-permission input to prove the read-only frame holds. There is no
    permission system here and ``asSet`` declares no ``mut`` binder, so the
    PERMISSION half of that attack is genuinely gone — but its BEHAVIOURAL half
    survives as a functional structure update: rebuild the assertion with one
    component displaced by the other, then read the component back. Overwriting
    the COLLECTION slot with the element is observably wrong and is shipped
    (``frame-substitute-displace-collection``). Overwriting the ELEMENT slot is
    the arm that really does collapse: the result is the untouched collection, so
    the impl is CORRECT here and verifies — measured, not assumed (see footer).
  * DIVERGENCE / NON-TERMINATION - CLOSED BY THE SEMANTICS, measured rather than
    argued, and this bullet RETRACTS the spec hole earlier revisions escalated
    here. The frozen file sets ``loom.semantics.termination "total"`` (line 4)
    AND opens ``TotalCorrectness DemonicChoice`` (line 7), so the verifier
    discharges a real termination obligation and BOTH shapes a diverging rival
    can take on this carrier are refused.

    Re-measured against the frozen file with real builds:

      - the measure-FREE diverging rival (``while True do pure ()`` prefix, in
        four forms: frozen proof, retuned proof, wrong return value, and a
        counter loop) -> REJECTED, exit 1, ``Decreasing annotations are required
        in total correctness semantics``, raised on the ``method`` itself. So the
        naive attack does not land.
      - the SHARPER rival, which cannot be dismissed as merely missing the
        annotation, CARRIES a measure that does not decrease. This cell's own
        claimed shape, ``while 0 <= i`` with ``done_with 0 > i``,
        ``decreasing (0 : Nat)``, ``i := i + 1``, is REJECTED TOO, at exit 1, on
        the MEASURE's own descent goal: ``unsolved goals case
        «decreasing_1: (0 : Nat)» ... ⊢ 0 < 0``. A constant measure over a
        counter loop and a strictly INCREASING ``decreasing k`` over
        ``k := k + 1`` fare the same way (``⊢ 0 < 0`` and ``⊢ k + 1 < k``).

    RETRACTION, stated plainly because a released artifact should not carry a
    stale finding. An earlier revision recorded the second shape as VERIFYING at
    exit 0, read the unreachable exit as discharging every ``ensures`` vacuously,
    and diagnosed a ROOT CAUSE that is also false: that the ``set_option`` does
    not select the semantics, that a later ``open PartialCorrectness`` wins over
    the namespace the option opens, and that "the cell reads ``total`` and is
    checked as ``partial``". Neither half survives contact with the sources.
    ``set_option loom.semantics.termination "total"`` ITSELF opens the
    ``TotalCorrectness`` scope (Loom, ``MonadAlgebras/WP/Options.lean``, the
    ``openScope `TotalCorrectness`` arm), and this file's ONLY ``open`` of a
    correctness namespace is ``TotalCorrectness`` on line 7, so there is no
    partial scope in play to shadow anything. ``TotalCorrectness.WPGen.
    forWithInvariantLoop`` takes the ``measure`` and emits ``⌜measure b' <
    measure b⌝`` as a goal the proof must discharge; only the
    ``PartialCorrectness`` twin takes a measure and drops it, which is why the two
    header lines have to move together and do here. No ``spec_holes`` entry is
    owed from this class and none is claimed.

    NOT shippable as a reject case here either, for a TOOLING reason rather than
    a judgement — measured three ways. A witness must first ELABORATE against the
    rival, and against ANY loop-bearing impl on this carrier the tester does not
    reduce: ``Tactic `decide` failed for proposition asSetTester { elem := 0,
    container := 1 } = false because its `Decidable` instance ... did not reduce
    to `isTrue` or `isFalse``` — the loop elaborates through ``Classical.choice``,
    which the kernel cannot unfold. That is the gate's own ``_STUCK_REDUCTION``
    class; it fires identically for the FLIPPED claim, and it fires even for a
    TERMINATING loop-bearing wrong rival, so it is the loop and not the
    divergence that blocks the witness. ``witness_reference`` cannot rescue it
    either: that option replaces the SECOND subject, and the failure is on the
    first (rival) half.
  * WRONG-COMPONENT / VALUE / DECLINE — the live class. Each rival either hands
    back the wrong component, a fabricated value, or a decline, refuted at a
    concrete decidable point.
  * PARTIAL-DOMAIN — also live, and initially unprobed: the three ported rivals
    are all TOTAL, so a spec pinned only where they differ would look identical
    to one pinned everywhere. ``partial-domain-elem-when-zero`` closes that by
    agreeing with the frozen impl on all but one guarded sub-domain.

WITNESS MECHANICS. The spec is a ``method`` CONTRACT, not a bare predicate, so a
witness reaches it through Velvet's own tester machinery
(``extract_program_for`` / ``derive_tester_for``): ``asSetTester a = false``
says the extracted program's result violates the postcondition at that concrete
input. It is checked in a file whose ``prove_correct`` block has been stripped,
so no tactic script can mask the verdict.
``prove_postcondition_decidable_for`` needs equality of the report carrier
``Except ConversionErr Nat`` to be decidable, so the preamble derives that
instance first — an instance, not an assumption (no ``axiom`` / ``sorry`` /
``native_decide``), and the frozen solution rejects every witness all the same
(on each witness point the frozen impl SATISFIES the postcondition, so its
tester returns ``true`` and ``= false`` FAILS against gold — the discriminator).

WITNESS PLACEMENT. The clause has a single input binder ``a`` with two fields.
The rival witnesses move BOTH fields across five distinct input points
— {(0,1), (2,3), (4,5), (8,9), (0,7)} for (elem, container) — so no field is
held constant by every witness. A rival that mishandled only a field every
witness pinned would slip through; varying both closes that hole. (``a.elem`` is
not consulted by the correct answer, but it IS the value the wrong-component
rivals abuse, so varying it is what demonstrates the spec rejects an elem-return
specifically.) The point (0,7) is deliberately NOT interchangeable with the
others: it is the only one inside the sub-domain
``pos-guarded-diagonal``/``partial-domain-elem-when-zero`` disagree on.

POSITIVE-CONTROL STRENGTH — the reason ``pos-guarded-diagonal`` exists. A
reshape that is DEFINITIONALLY EQUAL to the frozen impl cannot fail: the
elaborator sees the same term, so the case attests to region surgery working
rather than to the spec admitting a genuinely different program. Measured with
the real kernel: both ``let``-binding and ``match``-destructuring the container
close against the frozen body by bare ``rfl``, so on their own the soundness lane
was untestable. ``pos-guarded-diagonal`` is not defeq (``rfl`` fails on it with a
type mismatch); it BRANCHES, and on the diagonal it returns ``a.elem``, correct
only because the guard forces the two components equal. Discharging it therefore
requires the obligation to consume the guard hypothesis, which is a real
soundness question. The cheap reshapes are kept as controls, marked for what
they are.

AXIOM lane: EMPTY (the ``axioms`` region declares no ``axiom``; the conversion
reads the object's own stored components and calls nothing — there is no callee
to contract, and mapping.md records empty ``axioms`` / ``deep_model_references``,
so G-AX skips). The gate ignores ``AXIOM_TESTS``.
"""
from pathlib import Path

INSTANCE = "sympy__sympy-23950"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- the frozen impl body, verbatim (the return line PLUS the `-- impl-end`
# ---- marker as the right anchor, so every edit is guaranteed to land wholly
# ---- inside -- impl-start / -- impl-end and `same_spec` is preserved).
# ---- Unique in the file (asserted at load). ----
_RET = "    return Except.ok a.container\n    -- impl-end"
assert _BASE.count(_RET) == 1, "gold impl body drifted from Solution.lean"

# ---- the frozen proof block. A tactic body is elided from the consumer spec
# ---- view, so a positive control could retune it without touching the spec or
# ---- dropping the obligation — though both positives here close with the
# ---- frozen `loom_solve` unchanged. Unique in the file. ----
_PROVE = "prove_correct asSet by\n  loom_solve\n"
assert _BASE.count(_PROVE) == 1, "frozen proof block drifted from Solution.lean"


def _impl(body):
    """Full Solution.lean whose impl-region body is `body` (statements already
    indented 4 spaces), keeping the `-- impl-end` marker."""
    return _swap(_BASE, _RET, body + "\n    -- impl-end")


# ---- witness preamble: reach the method contract through Velvet's tester.
# ---- Except-carrier equality is DERIVED as an instance (not assumed) so the
# ---- postcondition is decidable at a concrete input. ----
_PREAMBLE = (
    "deriving instance DecidableEq for Except\n\n"
    "extract_program_for asSet\n"
    "prove_precondition_decidable_for asSet\n"
    "prove_postcondition_decidable_for asSet\n"
    "derive_tester_for asSet\n\n"
)


def _wit(elem, container):
    return _PREAMBLE + (
        f"example : asSetTester {{ elem := {elem}, container := {container} }} "
        "= false := by\n  decide\n")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify. If a faithful correct impl cannot verify, the spec is
    # SPEC-TOO-STRONG. Each keeps the obligation; the frozen `loom_solve` still
    # closes for both reshapes.
    # =====================================================================
    {
        "id": "pos-bind-local",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(
            "    let c := a.container\n"
            "    return Except.ok c"),
        "rationale": "binding the collection component into a local first, then "
                     "returning it, produces the SAME success outcome with the "
                     "SAME value as gold, so `out = Except.ok a.container` still "
                     "holds and the frozen proof closes. A correct reshape must "
                     "verify, else SPEC-TOO-STRONG. WEAK BY CONSTRUCTION: a "
                     "`let`-bound projection is DEFINITIONALLY EQUAL to the "
                     "frozen body (measured: `rfl` closes the two bodies against "
                     "each other), so this case cannot fail and attests to the "
                     "region surgery, not to the spec. Kept as a control; the "
                     "load-bearing positive is `pos-guarded-diagonal`.",
    },
    {
        "id": "pos-destructure-match",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(
            "    match a with\n"
            "    | { elem := _, container := c } => return Except.ok c"),
        "rationale": "destructuring the assertion and returning its second "
                     "component by a bound name sends the input down the same "
                     "route with the same value as gold, so "
                     "`out = Except.ok a.container` holds; the reshaped body "
                     "still closes under `loom_solve`. A correct reshape must "
                     "verify. WEAK BY CONSTRUCTION, same as `pos-bind-local`: "
                     "single-constructor pattern matching is projection, so this "
                     "body too is DEFINITIONALLY EQUAL to the frozen one "
                     "(measured: `rfl` closes them against each other). Kept as "
                     "a control.",
    },
    {
        # The load-bearing positive: NOT definitionally equal to gold. It
        # BRANCHES, and on the diagonal it hands back the OTHER component,
        # which is correct only because the guard forces the two equal. So the
        # obligation has to consume the guard hypothesis rather than see the
        # frozen term again.
        "id": "pos-guarded-diagonal",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(
            "    if a.elem = a.container then\n"
            "      return Except.ok a.elem\n"
            "    else\n"
            "      return Except.ok a.container"),
        "rationale": "the one positive that is NOT definitionally gold "
                     "(measured: `rfl` FAILS between this body and the frozen "
                     "body, with a type mismatch on the `if`). It is still "
                     "CORRECT on every input: off the diagonal it returns the "
                     "container outright, and ON the diagonal it returns "
                     "`a.elem`, which the guard makes equal to `a.container` — "
                     "so `out = Except.ok a.container` holds either way. "
                     "Discharging it therefore requires the obligation to case "
                     "split and USE the guard, which is the soundness question "
                     "the two defeq reshapes cannot ask. If the spec rejected "
                     "this it would be SPEC-TOO-STRONG: it would be refusing a "
                     "faithful correct impl for its shape. Closes under the "
                     "frozen `loom_solve` unchanged.",
    },

    # =====================================================================
    # ADMISSIBILITY (re-aimed) — this method has NO `require` clause, so the
    # nagini "a normal F2P-shaped input satisfies the precondition" probe is
    # VACUOUS in its literal form: nothing could exclude an in-domain input.
    # "No precondition" is NOT a reason to drop the lane, though — the analogue
    # on a TOTAL carrier is the obligation being unsatisfiable or DEGENERATE at
    # an F2P-shaped input (a spec no impl can meet reads exactly like a spec
    # every impl meets), so the case discharges TWO live in-region asserts
    # before closing the frozen obligation verbatim:
    #   (i) the demanded outcome is DISTINCT from the decline arm — the success
    #       requirement is a real constraint, not one a refusal also meets;
    #  (ii) at a CONCRETE F2P-shaped assertion the demanded outcome EVALUATES to
    #       the container (`{elem := 3, container := 7}` -> `Except.ok 7`), so
    #       the obligation is satisfiable at exactly that input shape.
    # Both asserts are live: a false claim in either leaves an unsolved goal
    # (measured both ways). The impl is kept verbatim, so the method's own
    # obligation still discharges.
    # =====================================================================
    {
        "id": "admiss-outcome-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl(
            "    assert (with_name_prefix `assert\n"
            "      (Except.ok a.container ≠ "
            "(Except.error ConversionErr.unavailable : Except ConversionErr Nat)))\n"
            "    return Except.ok a.container"),
        "rationale": "the post-image is non-degenerate: the demanded outcome "
                     "`Except.ok a.container` is provably DISTINCT from the "
                     "decline arm `Except.error .unavailable`, so 'the "
                     "conversion succeeds and yields the container' is a real "
                     "constraint, not one every outcome (incl. a refusal) meets. "
                     "The in-region assert must discharge; the impl is kept "
                     "verbatim so `out = Except.ok a.container` discharges too. "
                     "Re-aimed from the nagini precondition-admits probe "
                     "(vacuous: no `require` clause).",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # decidable input and the argument that its faithful real counterpart would
    # NOT resolve the F2P.
    # =====================================================================
    {
        "id": "wrong-component-return-element",
        "kind": "uniqueness",
        "expect": "reject",
        # The bug in the issue: hand back the ELEMENT being tested instead of
        # the collection. elem and container are distinct components; the spec
        # accepts only the container.
        "module": _impl("    return Except.ok a.elem"),
        "refinement": "its faithful real patch returns the tested element (the "
                      "first stored operand) rather than the collection. The F2P "
                      "asserts the set form of a membership assertion EQUALS the "
                      "collection it ranges over, but the element is a distinct "
                      "object (a symbol), so the assertion equals the element "
                      "!= the collection: the F2P FAILS. It does NOT resolve.",
        "rationale": "REJECT from `out = Except.ok a.container`: the rival "
                     "returns `Except.ok a.elem`, and whenever `a.elem != "
                     "a.container` (elem 0, container 1) that is `Except.ok 0 != "
                     "Except.ok 1`. Refuted at (elem 0, container 1); this is the "
                     "witness that moves the `elem` field OFF the value it shares "
                     "with `container`, exercising the wrong-component distinction.",
        "witness": _wit(0, 1),
    },
    {
        "id": "decline-produce-collection",
        "kind": "uniqueness",
        "expect": "reject",
        # The pre-image state: decline to produce a collection at all. The
        # success arm is required, so a decline cannot satisfy the clause.
        "module": _impl("    return Except.error ConversionErr.unavailable"),
        "refinement": "its faithful real patch keeps the pre-patch body that "
                      "declines to produce a set (the exact state the gold "
                      "change removes). The F2P then hits the decline instead of "
                      "receiving the collection — the very pre-patch failure the "
                      "issue reports — so a faithful counterpart does NOT resolve.",
        "rationale": "REJECT from `out = Except.ok a.container`: the clause "
                     "demands the SUCCESS tag, but the rival returns "
                     "`Except.error .unavailable`, which is never `Except.ok _` "
                     "at any input. Refuted at (elem 2, container 3), a point "
                     "distinct from the other witnesses.",
        "witness": _wit(2, 3),
    },
    {
        "id": "fabricate-constant-collection",
        "kind": "uniqueness",
        "expect": "reject",
        # Value-clause near-miss: succeed, but return a fabricated collection
        # not tied to any stored component. Agrees with gold only when the
        # container happens to be that constant; wrong everywhere else.
        "module": _impl("    return Except.ok 0"),
        "refinement": "its faithful real patch returns a fixed, fabricated "
                      "collection rather than the assertion's stored collection. "
                      "The F2P asserts the set form EQUALS the specific "
                      "collection the membership ranges over; a constant "
                      "unrelated collection is not that object, so the equality "
                      "FAILS on every assertion whose collection is not that "
                      "constant. It does NOT resolve.",
        "rationale": "REJECT from `out = Except.ok a.container`: the rival "
                     "returns `Except.ok 0`, so whenever `a.container != 0` "
                     "(container 5) it is `Except.ok 0 != Except.ok 5`. Refuted "
                     "at (elem 4, container 5) — the witness that moves the "
                     "`container` field off the values the other rivals hold it "
                     "at, exercising the value clause's dependence on the "
                     "container component.",
        "witness": _wit(4, 5),
    },
    {
        # RECOVERED from the nagini frame-mutation lane, which the port had
        # written off as vacuous. The permission half of that attack is indeed
        # gone (no fractional permission, no `mut` binder), but its BEHAVIOURAL
        # half is expressible as a functional structure update: rebuild the
        # assertion with the collection slot displaced by the element, then read
        # that slot back. Observably wrong, and refuted at a concrete point.
        "id": "frame-substitute-displace-collection",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    let a' := { a with container := a.elem }\n"
            "    return Except.ok a'.container"),
        "refinement": "its faithful real patch displaces the stored collection "
                      "with the tested element before reading the collection "
                      "slot back, so the conversion yields the element. The F2P "
                      "asserts the set form EQUALS the collection the membership "
                      "ranges over, but it would receive the element (a distinct "
                      "object, not a collection at all), so the equality FAILS. "
                      "It does NOT resolve. This is also why the real object's "
                      "stored components are immutable: a counterpart that could "
                      "do this is not the gold behaviour.",
        "rationale": "REJECT from `out = Except.ok a.container`: reading the "
                     "collection slot of a REBUILT assertion is not reading it "
                     "on the INPUT assertion, and the rebuilt slot holds "
                     "`a.elem`, so the rival returns `Except.ok a.elem` — the "
                     "goal the verifier is left with is literally "
                     "`Except.ok a.elem = Except.ok a.container`. Refuted at "
                     "(elem 8, container 9), a fourth distinct input point. "
                     "Distinct from `wrong-component-return-element` as a TEST "
                     "even though it lands on the same value: that rival names "
                     "the wrong component directly, this one reaches the wrong "
                     "value through a structure update that LOOKS like it reads "
                     "the container, which is the shape the sibling's frame lane "
                     "was built to catch.",
        "witness": _wit(8, 9),
    },
    {
        # PARTIAL-DOMAIN near-miss. All three ported rivals are TOTAL — wrong at
        # (almost) every input. Nothing probed whether the clause is pinned on a
        # narrow SUB-DOMAIN, which is where a spec that holds "on the cases the
        # tests happen to use" hides. This rival is gold everywhere except when
        # the tested element is the zero identifier.
        "id": "partial-domain-elem-when-zero",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    if a.elem = 0 then\n"
            "      return Except.ok a.elem\n"
            "    else\n"
            "      return Except.ok a.container"),
        "refinement": "its faithful real patch returns the collection in "
                      "general but falls back to the tested element on one "
                      "distinguished element (a guard on the operand, e.g. a "
                      "sentinel-valued one). The F2P exercises the conversion on "
                      "assertions covering that operand, and there the set form "
                      "comes back as the element rather than the collection, so "
                      "the asserted equality FAILS. It does NOT resolve — and a "
                      "patch correct only OUTSIDE a sub-domain the tests reach is "
                      "exactly the near-miss this case exists to exclude.",
        "rationale": "REJECT from `out = Except.ok a.container`: the clause is "
                     "claimed at EVERY input, not merely at the ones where the "
                     "rival happens to agree, so a single point in the bad "
                     "sub-domain refutes it. Refuted at (elem 0, container 7): "
                     "the rival returns `Except.ok 0` where the container is 7. "
                     "Verified to be a genuine NEAR-MISS rather than another "
                     "total rival — the same tester returns `true` for this rival "
                     "at (3,7) and (6,7), i.e. it satisfies the postcondition "
                     "off the guarded sub-domain and is refuted only inside it. "
                     "That is the property the three total rivals cannot test.",
        "witness": _wit(0, 7),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 9 SPEC cases (1 soundness
# positive, 1 admissibility, 7 uniqueness rivals — 2 frame-mutation, 2
# divergence). This bundle models the SAME behaviour (read the assertion's two
# stored components and hand back the collection component) as ONE method with
# one obligation.
#
#   sibling case                       -> here
#   ---------------------------------------------------------------------
#   pos-control-typed-local            -> pos-bind-local                 PORTED
#                                         + pos-destructure-match        ADDED
#                                         + pos-guarded-diagonal         ADDED
#   admiss-read-both-fields            -> admiss-outcome-nondegenerate   RE-AIMED
#   frame-mut-overwrite-region         -> frame-substitute-displace-collection
#                                                                        RECOVERED
#   frame-mut-overwrite-element        -> (none)              COLLAPSES (measured)
#   wrong-component-return-element     -> wrong-component-return-element PORTED
#   defer-raise-viewnotproduced        -> decline-produce-collection     PORTED
#   no-return-fallthrough              -> (none)         INEXPRESSIBLE (measured)
#   nonterm-self-recursion             -> (none)                         SPEC-CLOSED
#   nonterm-infinite-loop              -> (none)                         SPEC-CLOSED
#   (added for value-binder coverage)  -> fabricate-constant-collection  ADDED
#   (added for sub-domain coverage)    -> partial-domain-elem-when-zero  ADDED
#
# PORTED (positive): the sibling ships ONE structurally-different correct impl
#   (bind the component into a typed local, then return it). Carried here by
#   pos-bind-local (the same reshape) plus pos-destructure-match (destructure
#   the structure and return the second component by name). Both are correct on
#   every input and both verify under the frozen `loom_solve` — but both are
#   DEFINITIONALLY EQUAL to the frozen body (measured: `rfl` closes each against
#   it), so neither could have failed and neither tests the spec. They are kept
#   as controls and labelled as such.
# ADDED (pos-guarded-diagonal): the load-bearing positive, added because the two
#   above are defeq. It BRANCHES and returns `a.elem` on the diagonal — correct
#   only because the guard forces the components equal — so it is NOT defeq
#   (`rfl` fails on it) and its discharge requires the obligation to consume the
#   guard hypothesis. This is the case that can actually detect SPEC-TOO-STRONG.
# RE-AIMED (admissibility): the sibling reads both half-permission components and
#   pins the returned-region identity to show the precondition is establishable.
#   This method has no `require` clause (nothing to admit), so the probe is
#   re-aimed at post-image non-degeneracy: the demanded success outcome is
#   provably distinct from the decline arm, so the obligation is a real
#   constraint. Impl kept verbatim; verifies.
# PORTED (rivals): wrong-component-return-element IS behaviour (a), the bug in
#   the issue (hand back the tested element, not the collection);
#   decline-produce-collection IS behaviour (b), the pre-patch decline (the
#   G-DIFF discriminator). Each refuted at the smallest decidable point.
# INEXPRESSIBLE (no-return-fallthrough) — demonstrated, not asserted. A body that
#   produces no report cannot be WRITTEN: ending the `do` block with `pure ()`
#   is rejected by the elaborator before any spec question is reached
#   (`the argument () has type Unit but is expected to have type
#   Except ConversionErr Nat`), and a build that fails on a type error is not a
#   rejection attributable to the spec. The sibling's "produces no Region result"
#   surrogate has no carrier here; the DECLINE outcome is the nearest expressible
#   thing and is already shipped as decline-produce-collection.
# ADDED (fabricate-constant-collection): a value-clause near-miss (succeed but
#   return a fixed collection unrelated to the stored one). Its separating input
#   moves the `container` field off the values the other rivals pin, exercising
#   the value clause's dependence on the container component.
# ADDED (partial-domain-elem-when-zero): all three ported rivals are TOTAL —
#   wrong at essentially every input — so none of them probes whether the clause
#   is pinned across the whole domain or only where the rival happens to differ.
#   This one agrees with gold everywhere except a single guarded sub-domain, and
#   is confirmed a genuine near-miss: its tester returns `true` at (3,7) and
#   (6,7) and is refuted only at (0,7).
# RECOVERED (frame-mut-overwrite-region -> frame-substitute-displace-collection):
#   the port recorded both frame cases as vacuous because the carrier has no
#   fractional permission and `asSet` declares no `mut` binder. That is true of
#   the PERMISSION half and false of the case as a whole: the behaviour the
#   sibling was catching — the collection slot ending up holding the element,
#   then being read back — is expressible as a functional structure update
#   (`{ a with container := a.elem }`), is observably wrong, and is refuted at a
#   concrete point. Now shipped.
# COLLAPSES (frame-mut-overwrite-element) — demonstrated, not asserted. The
#   element-slot arm displaces a component the answer never consults, so the
#   rebuilt assertion still carries the original collection and the impl
#   `let a' := { a with elem := a.container }; return Except.ok a'.container`
#   is CORRECT: it VERIFIES. On nagini the case rejected for insufficient
#   permission, never for behaviour, and it is exactly that permission
#   distinction the carrier does not have. Shipping it as a reject would be
#   fabricating a rival that is not wrong.
# KNOWN HOLE (divergence x2 — self-recursion, infinite-loop): the frozen file's
#   `set_option` reads "total", NOT "partial" — an earlier revision of this file
#   cited the partial-semantics vacuity argument, which misquoted the artifact;
#   corrected here. Re-measured: the measure-FREE diverging rival is properly
#   REJECTED (`Decreasing annotations are required in total correctness
#   semantics`, exit 1, in all four forms tried). And the sharper rival, which
#   CARRIES a measure (`while 0 <= i`, `done_with 0 > i`, `decreasing (0 : Nat)`,
#   `i := i + 1`) and returns the WRONG value, is REJECTED TOO, at exit 1, on the
#   measure's own descent goal:
#       unsolved goals
#       case «decreasing_1: (0 : Nat)» ... |- 0 < 0
#   so is `decreasing k` over an increasing `k := k + 1` (`|- k + 1 < k`).
#   RETRACTION: an earlier revision recorded that shape as VERIFYING (exit 0),
#   diagnosed the root cause as "the `open` line, not the `set_option`, selects
#   the semantics, and the partial `forWithInvariantLoop` discards the measure",
#   and filed "the cell reads total and is checked partial" in spec_holes. Both
#   halves are false: `set_option loom.semantics.termination "total"` itself opens
#   the `TotalCorrectness` scope (Loom, `MonadAlgebras/WP/Options.lean`,
#   `openScope `TotalCorrectness`), this file's only correctness `open` is
#   `TotalCorrectness` on line 7, and `TotalCorrectness.WPGen.
#   forWithInvariantLoop` emits `measure b' < measure b` as a real goal. The
#   spec_holes entry is withdrawn; nothing from this class is escalated.
#   NOT shippable as a reject for a
#   TOOLING reason: a witness must elaborate against the rival first, and against
#   any loop-bearing impl the tester is stuck (`... did not reduce to `isTrue` or
#   `isFalse``, the gate's _STUCK_REDUCTION class) — measured to fire identically
#   for the flipped claim AND for a terminating loop-bearing wrong rival, so the
#   loop, not the divergence, is what blocks it. `witness_reference` cannot fix
#   it: it replaces the second subject; the failure is on the first.
#
# WITNESS DISTINCTNESS. Five distinct input points:
#   (elem 0, container 1)   wrong-component-return-element  (returns the element)
#   (elem 2, container 3)   decline-produce-collection      (declines)
#   (elem 4, container 5)   fabricate-constant-collection   (wrong success value)
#   (elem 8, container 9)   frame-substitute-displace-collection
#                                                     (wrong value via a rebuild)
#   (elem 0, container 7)   partial-domain-elem-when-zero
#                                             (wrong on a guarded sub-domain only)
# The `elem` field ranges over {0,2,4,8} and `container` over {1,3,5,7,9}; neither
# is held constant by every witness. The five rivals fail for DIFFERENT reasons
# (wrong component / wrong tag / wrong value / wrong value reached through a
# structure update / correct except on a sub-domain), so they are distinct
# predicates, not one attack written five times. The last point is the only one
# NOT interchangeable with the others: it is the sole point inside the sub-domain
# its rival disagrees on, and the same rival's tester returns `true` at (3,7) and
# (6,7), which is what certifies the case as a near-miss rather than a fourth
# total rival.
#
# EVERY reject witness was rebuilt against BOTH subjects with the real verifier:
# rival exit 0, frozen-solution exit 1, and in each case the frozen-side failure
# is the SEMANTIC one — `Tactic decide proved that the proposition
# asSetTester {...} = false is false` — not a missing identifier, a type error, a
# stuck reduction, or a timeout. The reduction is confirmed live at every point
# by the complementary build: asserting the tester `= true` against the frozen
# solution SUCCEEDS at (0,1), (2,3), (4,5), (8,9) and (0,7), so the kernel really
# decides these claims rather than failing on them uniformly.
#
# AXIOM_TESTS: dropped. There are no axioms and no deep-model references in this
# bundle (the conversion calls nothing); the axiom lane is G-AX's job and G-AX
# skips here.
AXIOM_TESTS = []
