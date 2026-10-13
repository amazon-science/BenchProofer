"""properties.py — G-PBT falsification battery for django__django-13363 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the two ``-- impl-start`` /
``-- impl-end`` regions — the impl body is byte-identical in both modeled
methods, so it occurs twice — is changed; the consumer spec view elides those
regions, so ``markers.same_spec`` holds and every ``prove_correct`` obligation
survives with its header intact) and swaps in a candidate implementation; it is
checked by the real verifier. ``expect:"verify"`` passes iff (in scope AND
verifies); ``expect:"reject"`` passes iff (in scope AND does NOT verify AND its
refutation ``witness`` discriminates: the witness ELABORATES against the rival
and FAILS against the frozen solution).

DEFENDED SURFACE (two byte-identical contracted methods that select the
timezone name a datetime→date / datetime→time cast should apply):

  dateCastZoneName (tzAware : Bool) (explicitZone : Option String)
      (currentZone : String) return (out : Option String)
    ensures out = resolveZoneName tzAware explicitZone currentZone   -- only clause
  timeCastZoneName (tzAware) (explicitZone) (currentZone) return (out)
    ensures out = resolveZoneName tzAware explicitZone currentZone   -- same clause

where the TRANSPARENT ``def`` (directive 8; NOT an opaque answer-key) is

  resolveZoneName tzAware explicitZone currentZone =
    if tzAware then (match explicitZone with
                     | none   => some currentZone      -- ambient fallback
                     | some z => some z)               -- supplied zone HONOURED
    else none                                          -- no zone-awareness

The whole clause reduces, on concrete inputs, to a comparison of two
``Option String`` values that ``decide`` computes, so no rival can "echo an
opaque oracle": the only way to satisfy the clause is to compute exactly this
selection. The zone-name resolution this stands in for is validated equal to the
real (unchanged) callee by G-AX (an A-reference); this gate ignores that lane.

WHAT THE SPEC DEFENDS. The entire content of the modeled fix is that a
CALLER-SUPPLIED zone takes precedence over the ambient one when zone-awareness is
in effect — the supplied zone must be honoured, not silently dropped in favour of
the ambient name. That precedence lives in the ``some z => some z`` arm and is
pinned by the whole-Option equality, together with the ``none`` gate (no
zone-awareness ⇒ no zone name) and the ambient-fallback arm.

BINDER STRUCTURE (read before judging binder coverage). The postcondition
depends on all THREE inputs:

  * ``tzAware`` selects the outer gate. A rival wrong only when zone-awareness is
    OFF is refuted at ``tzAware = false``; a rival wrong only when it is ON is
    refuted at ``tzAware = true``. The battery carries both so ``tzAware`` is not
    pinned at one value.
  * ``explicitZone`` selects the inner arm. The load-bearing precedence rival is
    correct on ``explicitZone = none`` and wrong only on ``some z``, so it is
    refuted at ``some z`` with ``z`` distinct from ``currentZone`` (the point
    where the supplied/ambient distinction is observable). A separate rival is
    refuted on the ``none`` arm, so ``explicitZone`` is varied across ``some``/
    ``none``.
  * ``currentZone`` is the ambient name used on the ``none`` arm and the
    distractor the precedence rival wrongly returns; the witnesses vary it and at
    least one rival's refutation turns on it differing from the supplied zone.

ADVERSARIAL READ of the nagini classes on this carrier:
  * FRAME-MUTATION (nagini ``frame-mut-current_name`` / ``frame-mut-tzinfo``) —
    VACUOUS. The nagini sibling carries these because its two read-only list
    inputs are held at a fractional heap permission (``Acc(.,1/2)``) that an impl
    can illegally overwrite. Velvet is referentially transparent: every input
    here is an immutable value, there is no ``mut`` binder, no heap and no
    aliasing — there is no read-only input to mutate and no substitute probe to
    build. Not fabricated (porting map: vacuous here).
  * ADMISSIBILITY (nagini ``admiss-f2p-shaped``) — PORTED (``admiss-f2p-shaped``
    below). This bundle declares NO ``require`` clause, but that is NOT a reason to
    drop the lane: on a total carrier the analogue of PRECOND-TOO-STRONG is the
    obligation being unsatisfiable or DEGENERATE at an F2P-shaped input, which a
    ``have … := by decide`` discharging the post-image at concrete F2P-shaped
    points tests directly. It is not the trivial ``resolveZoneName … =
    resolveZoneName …``: each conjunct evaluates the selection against a
    LITERAL expected value, and one conjunct is a non-degeneracy INEQUALITY
    (supplied ≠ ambient at that point). Liveness confirmed by real builds —
    flipping either load-bearing conjunct fails.
  * UNGROUNDED-ORACLE ECHO — N/A: the post-image is a transparent ``def`` over
    the three method inputs, not an axiomatized oracle; the ``axioms`` region is
    empty. The echo positive below is therefore an honest cheapest-impl control.
  * DIVERGENCE / NON-TERMINATION - the class is INAPPLICABLE to this impl and
    CLOSED BY THE SEMANTICS against any rival that manufactures it. Every
    frozen impl region is LOOP-FREE (straight-line ``if`` over immutable
    values, no loop and no recursion), so there is no control flow here to make
    diverge: a diverging rival cannot be obtained by mutating this body, it has
    to bring a loop of its own. When it does, the semantics refuse it. This
    bundle sets ``loom.semantics.termination "total"`` AND carries
    ``open TotalCorrectness``, and the ``open`` is the line that actually
    selects the semantics: both namespaces define
    ``WPGen.forWithInvariantLoop``, the later ``open`` wins, and the
    ``PartialCorrectness`` version takes a loop measure and DISCARDS it, so the
    two lines have to move together and they do here. Under the total scope a
    postcondition is claimed of ALL runs and not only of terminating ones, so a
    spliced loop owes a descent obligation ``measure b' < measure b``.
    Re-measured on this bundle with a real build: a
    ``while spin > 0 do spin := spin`` prefix carrying ``decreasing spin`` is
    REJECTED on the measure's own goal (``case «decreasing_1: spin» ... ⊢ spin
    < spin``). Dropping the clause rather than faking it is refused even
    earlier, by the elaborator's own check (``Decreasing annotations are
    required in total correctness semantics``). So divergence neither applies
    to this impl nor discharges the ``ensures`` clauses vacuously if a rival
    introduces it.
  * AXIOM lane (nagini's 2 ``get_tzname`` A-reference probes) — DROPPED. The axiom
    lane is G-AX's job; this gate ignores ``AXIOM_TESTS`` regardless.

WITNESS MECHANICS. The spec is a ``method`` CONTRACT, not a bare predicate, so a
witness reaches it through Velvet's own tester machinery:
``dateCastZoneNameTester tzAware explicitZone currentZone = false`` says the
extracted program's result violates the postcondition at that concrete input. It
is checked in a file whose ``prove_correct`` block has been stripped (so no
tactic script can mask the verdict) and there are no ``require`` clauses, so
every input reaches the postcondition. The two methods are byte-identical, so one
method's tester suffices; ``String`` / ``Option String`` literals are fully
concrete, so ``decide`` settles the whole equality — no opaque term, no
conditioning, no head binders (hence no consistency obligation).
"""
from pathlib import Path

INSTANCE = "django__django-13363"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap_both(src, old, new):
    """Replace `old` in BOTH (byte-identical) impl regions.

    Asserts exactly two occurrences: the impl body is identical in the two
    modeled methods, so it appears twice and only inside the elided impl
    regions. A count other than two signals drift (or an accidental spec-region
    match) and is rejected. Editing the same text in both regions keeps every
    spec region byte-identical => same_spec holds.
    """
    n = src.count(old)
    if n == 0:
        raise AssertionError(f"drift: {old!r} not present")
    if n != 2:
        raise AssertionError(f"expected 2 impl occurrences, found {n}: {old!r}")
    return src.replace(old, new, 2)


# ---- impl-region anchor. The COMPLETE impl body shared by both methods; lies
# ---- wholly inside the `-- impl-start`/`-- impl-end` regions and occurs exactly
# ---- twice (asserted at load by _swap_both). Anchoring on the whole body keeps
# ---- every surgery inside the elided regions — the frozen spec (the two
# ---- `method` headers, the `ensures` clauses, and the `pure` region that also
# ---- spells out the selection) is never touched. ----
_IMPL = (
    "    if tzAware then\n"
    "      match explicitZone with\n"
    "      | none   => return some currentZone\n"
    "      | some z => return some z\n"
    "    else\n"
    "      return none"
)


def _with_impl(new_impl: str) -> str:
    """Solution.lean with ONLY the (doubled) impl body replaced."""
    return _swap_both(_BASE, _IMPL, new_impl)


# ---- frozen tactic body, verbatim (occurs twice — once per method). It is
# ---- ELIDED from the consumer spec view, so a case may retune it: a correct
# ---- reshape legitimately reproves, and an admissibility case legitimately
# ---- adds a `have` in front of the frozen script. Rivals never touch it. ----
_PROOF_TAC = "  loom_solve\n  all_goals simp_all [resolveZoneName]"


def _retune(src: str, new_tac: str) -> str:
    """`src` with BOTH frozen tactic bodies replaced (asserted count == 2)."""
    return _swap_both(src, _PROOF_TAC, new_tac)


# ---- witness preamble: reach the contract through Velvet's tester machinery.
# ---- One method's tester suffices — the two methods are byte-identical. ----
_TESTER = (
    "extract_program_for dateCastZoneName\n"
    "prove_precondition_decidable_for dateCastZoneName\n"
    "prove_postcondition_decidable_for dateCastZoneName\n"
    "derive_tester_for dateCastZoneName\n\n"
)


def _witness(call: str) -> str:
    return _TESTER + f"example : {call} = false := by\n  decide\n"


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify, else SPEC-TOO-STRONG. Both verified out-of-band with a
    # real build against the frozen spec.
    # =====================================================================
    {
        "id": "pos-match-reorder",
        "kind": "soundness",
        "expect": "verify",
        # Structurally different: the inner `match` on `explicitZone` lists the
        # supplied-zone arm FIRST and the ambient-fallback arm second (the reverse
        # of the frozen order). Semantically identical branch selection, different
        # source. Ports the nagini branch-order positive (`pos-control-early-return`).
        "module": _with_impl(
            "    if tzAware then\n"
            "      match explicitZone with\n"
            "      | some z => return some z\n"
            "      | none   => return some currentZone\n"
            "    else\n"
            "      return none"),
        "rationale": "structurally-different (inner match arms reordered — supplied "
                     "zone first, ambient fallback second) but semantically identical "
                     "impl must verify against `out = resolveZoneName tzAware "
                     "explicitZone currentZone`. If it fails to verify, the spec is "
                     "over-fit to one branch order => SPEC-TOO-STRONG. Verified "
                     "out-of-band with a real build against the frozen proof script.",
    },
    {
        "id": "pos-cheapest-echo",
        "kind": "soundness",
        "expect": "verify",
        # The cheapest impl satisfying the clause: return the transparent selection
        # directly. Because `resolveZoneName` is a spelled-out `def` over the three
        # inputs (not an opaque oracle), this still performs the real selection —
        # there is no wrong echo that verifies. Re-expresses the nagini honest
        # cheapest-impl control (`pos-control-echo-grounded-oracle`).
        "module": _with_impl(
            "    return resolveZoneName tzAware explicitZone currentZone"),
        "rationale": "the cheapest impl satisfying the clause returns the transparent "
                     "selection directly. Because the post-image `resolveZoneName` is a "
                     "spelled-out function of the three inputs — not an axiomatized "
                     "answer key — this still does the real work; there is no wrong echo "
                     "that could verify (else this would be a reject case). Demonstrates "
                     "the spec is NOT echo-vulnerable. Must verify.",
    },

    {
        "id": "pos-flat-match",
        "kind": "soundness",
        "expect": "verify",
        # A correct impl whose CONTROL SHAPE differs from the frozen one, not just
        # its arm order: a single flat `match` on the PAIR `tzAware, explicitZone`
        # replaces the nested `if`/`match`, so the zone-awareness gate is no longer
        # a syntactic `if` at all and the three outcomes are selected in one step.
        # The frozen tactic body is kept verbatim (no retune), so this is a real
        # probe that the spec is not over-fit to the gated-if form.
        "module": _with_impl(
            "    match tzAware, explicitZone with\n"
            "    | false, _      => return none\n"
            "    | true,  none   => return some currentZone\n"
            "    | true,  some z => return some z"),
        "rationale": "structurally-different but semantically identical: the nested "
                     "`if tzAware then match explicitZone` is collapsed into ONE flat "
                     "`match` on the pair, so the zone-awareness gate is not a "
                     "syntactic `if` and all three outcomes are selected in a single "
                     "step. Same branch selection, materially different control shape "
                     "(a stronger reshape than reordering two arms). Must verify under "
                     "the UNCHANGED frozen tactic body, else the spec/proof is over-fit "
                     "to the gated-if FORM => SPEC-TOO-STRONG. Confirmed with a real "
                     "build: exit 0.",
    },

    # =====================================================================
    # ADMISSIBILITY (PRECOND-TOO-STRONG) — the third direction, which neither the
    # soundness nor the uniqueness lane can see. This bundle declares NO `require`
    # clause, so there is no precondition to admit; on a TOTAL carrier the
    # analogue is the obligation being UNSATISFIABLE — or degenerate — at an
    # F2P-shaped input, i.e. the post-image collapsing to a constant or failing to
    # distinguish the inputs the failing test varies. That is what this case tests
    # directly: a `have ... := by decide` discharges the post-image BY EVALUATION at
    # three concrete F2P-shaped points before the frozen obligation is closed
    # verbatim, pinning that the selection
    #   * yields the SUPPLIED zone at (zone-awareness on, a supplied zone) — and,
    #     as a separate conjunct, that this is NOT the ambient name, so the
    #     obligation is non-degenerate exactly where the failing test looks;
    #   * yields the AMBIENT name when no zone was supplied; and
    #   * yields NO zone when zone-awareness is off.
    # Both directions are what make it non-vacuous: a post-image that returned the
    # ambient name everywhere would fail conjuncts 1-2, and one that returned the
    # supplied zone everywhere would fail conjuncts 3-4. The impl is kept
    # BYTE-IDENTICAL and the frozen tactic body follows the `have` unchanged, so
    # the method's own obligation still discharges on its own terms; `hadmiss` is
    # `clear`ed so it cannot contribute to that proof.
    # LIVENESS was checked with real builds, not assumed: flipping the
    # non-degeneracy conjunct (to `= some "UTC"`) and, separately, the
    # zone-awareness-off conjunct (to `= some "UTC"`) each make the file FAIL
    # (`decide` proved the conjunction false, exit 1), so the `have` is a live
    # obligation rather than a decoration.
    # =====================================================================
    {
        "id": "admiss-f2p-shaped",
        "kind": "admissibility",
        "expect": "verify",
        "module": _retune(
            _BASE,
            '  have hadmiss :\n'
            '      resolveZoneName true (some "Australia/Melbourne") "UTC"\n'
            '          = some "Australia/Melbourne"\n'
            '      ∧ resolveZoneName true (some "Australia/Melbourne") "UTC" ≠ some "UTC"\n'
            '      ∧ resolveZoneName true none "UTC" = some "UTC"\n'
            '      ∧ resolveZoneName false (some "Australia/Melbourne") "UTC" = none := by\n'
            '    decide\n'
            '  clear hadmiss\n' + _PROOF_TAC),
        "rationale": "PRECOND-TOO-STRONG probe, aimed at what that direction IS on a "
                     "total carrier with no `require` clause: the obligation "
                     "`out = resolveZoneName …` is SATISFIABLE and non-degenerate at an "
                     "F2P-shaped input. The `have` discharges the post-image by "
                     "EVALUATION at three concrete points — zone-awareness on with a "
                     "supplied zone (which must yield that zone, and NOT the ambient "
                     "name — the separate inequality conjunct is what makes the point "
                     "non-degenerate at exactly the sub-domain the failing test "
                     "exercises), zone-awareness on with no supplied zone (the ambient "
                     "name), and zone-awareness off (no zone). If the post-image "
                     "collapsed to the ambient name the first two conjuncts would fail; "
                     "if it collapsed to the supplied zone the last two would. Impl is "
                     "byte-identical and `hadmiss` is cleared, so the frozen obligation "
                     "still discharges on its own terms. Real builds: verifies exit 0; "
                     "flipping the inequality conjunct, or the zone-awareness-off "
                     "conjunct, each fail exit 1 (`decide` proved the conjunction "
                     "false) — the `have` is live.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # concrete input (ELABORATES against the rival, FAILS against gold — both
    # halves confirmed out-of-band with real builds) and the refinement argument
    # for why its faithful real counterpart would NOT resolve the failing test.
    # =====================================================================
    {
        "id": "ignore-explicit-zone",
        "kind": "uniqueness",
        "expect": "reject",
        # THE modeled bug: when zone-awareness is in effect, always return the
        # ambient name, ignoring the caller-supplied zone. Correct on the
        # zone-awareness-off arm and on the ambient-fallback (no supplied zone)
        # case; wrong on exactly the discriminating sub-domain (a supplied zone
        # present) — the sub-domain the failing test exercises.
        "module": _with_impl(
            "    if tzAware then\n"
            "      return some currentZone\n"
            "    else\n"
            "      return none"),
        "refinement": "This IS the pre-fix behaviour: the ambient zone name is used "
                      "whenever zone-awareness is on, and the caller-supplied target "
                      "zone is silently discarded. Its faithful real counterpart is "
                      "precisely the reported bug — a supplied zone is dropped in favour "
                      "of the ambient one — so the failing test, which asserts dates "
                      "computed in the SUPPLIED zone, still fails; it would NOT resolve.",
        "rationale": "REJECT from `out = resolveZoneName …`: on `tzAware = true` with a "
                     "supplied zone the post-image is `some z` but this impl returns "
                     "`some currentZone` (a different name), so the two Options differ. "
                     "Correct on the `tzAware = false` and `explicitZone = none` "
                     "sub-domains, wrong on exactly the supplied-zone sub-domain. "
                     "Refuted at `tzAware = true`, `explicitZone = some \"A\"`, "
                     "`currentZone = \"B\"` — the point where supplied ≠ ambient.",
        "witness": _witness('dateCastZoneNameTester true (some "A") "B"'),
    },
    {
        "id": "aware-off-returns-ambient",
        "kind": "uniqueness",
        "expect": "reject",
        # When zone-awareness is OFF, returns the ambient name instead of no zone.
        # Correct on the entire zone-awareness-on arm; wrong only on the off arm —
        # the sub-domain the precedence rival happens to satisfy. Carries the
        # `tzAware = false` point so that binder is not pinned at `true`.
        "module": _with_impl(
            "    if tzAware then\n"
            "      match explicitZone with\n"
            "      | none   => return some currentZone\n"
            "      | some z => return some z\n"
            "    else\n"
            "      return some currentZone"),
        "refinement": "returns the ambient time-zone name even when zone-awareness is "
                      "off, so the cast applies a zone when none should be used. Its "
                      "faithful real counterpart emits zone-converted SQL for naive "
                      "(zone-awareness-off) reads, breaking those cases; it would NOT "
                      "resolve.",
        "rationale": "REJECT from `out = resolveZoneName …`: when `tzAware = false` the "
                     "post-image is `none` but this impl returns `some currentZone`, so "
                     "the two Options differ. Pins the `tzAware = false` sub-domain the "
                     "precedence rival satisfies. Refuted at `tzAware = false`, "
                     "`explicitZone = none`, `currentZone = \"C\"`.",
        "witness": _witness('dateCastZoneNameTester false none "C"'),
    },
    {
        "id": "branch-swap",
        "kind": "uniqueness",
        "expect": "reject",
        # Swaps the two inner arms: with a supplied zone it returns the AMBIENT
        # name, and with no supplied zone it returns NO zone at all. Wrong on both
        # inner arms of the zone-awareness-on branch; refuted here on the
        # ambient-fallback (`explicitZone = none`) arm — the point no other rival
        # probes (it pins `explicitZone = none` under `tzAware = true`).
        "module": _with_impl(
            "    if tzAware then\n"
            "      match explicitZone with\n"
            "      | none   => return none\n"
            "      | some _ => return some currentZone\n"
            "    else\n"
            "      return none"),
        "refinement": "swaps the supplied/ambient arms: a supplied zone yields the "
                      "ambient name and the no-supplied-zone case yields no zone at all. "
                      "Its faithful real counterpart both discards the supplied zone and "
                      "drops the ambient fallback, so the failing test still fails and "
                      "ambient reads lose their zone; it would NOT resolve.",
        "rationale": "REJECT from `out = resolveZoneName …`: on `tzAware = true`, "
                     "`explicitZone = none` the post-image is `some currentZone` but "
                     "this impl returns `none`; (independently, on `some z` it returns "
                     "`some currentZone` where the post-image wants `some z`). Refuted "
                     "on the ambient-fallback arm at `tzAware = true`, "
                     "`explicitZone = none`, `currentZone = \"E\"` — the "
                     "`explicitZone = none, tzAware = true` point unique to this rival.",
        "witness": _witness('dateCastZoneNameTester true none "E"'),
    },
    {
        "id": "supplied-zone-aliased-to-ambient",
        "kind": "uniqueness",
        "expect": "reject",
        # A NEAR-MISS the other three rivals leave unattacked. It honours the
        # supplied zone on the whole `some z` arm EXCEPT for one distinguished zone
        # name, where it silently substitutes the ambient name — i.e. it agrees with
        # the frozen selection at every input the other rivals' witnesses probe
        # (including `some "A"` with ambient `"B"`), and diverges only on the
        # narrow sub-domain `explicitZone = some "UTC"` with an ambient name that is
        # not `"UTC"`. This is the shape a partial fix takes: the precedence is
        # implemented but special-cased away for what looks like a harmless zone, so
        # the whole-Option equality must be strong enough to pin the precedence
        # UNIFORMLY over zone names, not merely on the one name a rival happens to
        # be tested at. Refuted at exactly that point.
        "module": _with_impl(
            "    if tzAware then\n"
            "      match explicitZone with\n"
            "      | none   => return some currentZone\n"
            "      | some z => return some (if z == \"UTC\" then currentZone else z)\n"
            "    else\n"
            "      return none"),
        "refinement": "honours a caller-supplied zone in general but substitutes the "
                      "ambient name for one distinguished zone name. Its faithful real "
                      "counterpart is a partial fix that still drops the supplied zone "
                      "for that zone, so any read requesting it is computed in the "
                      "ambient zone instead — the same class of wrong result the "
                      "failing test reports, on a narrower input set; it would NOT "
                      "resolve.",
        "rationale": "REJECT from `out = resolveZoneName …`: the post-image is `some z` "
                     "for EVERY `z` on the supplied-zone arm, but this impl returns "
                     "`some currentZone` when `z = \"UTC\"` and the ambient name differs. "
                     "The frozen proof leaves the residual goal `z = \"UTC\" → "
                     "currentZone = \"UTC\"`, which is not provable. Distinct from "
                     "ignore-explicit-zone, which is wrong on the WHOLE arm: this one "
                     "AGREES with the frozen selection at every point the other three "
                     "witnesses probe, so it tests that the clause pins the precedence "
                     "uniformly over zone names rather than at one sampled name. "
                     "Refuted at `tzAware = true`, `explicitZone = some \"UTC\"`, "
                     "`currentZone = \"B\"` — the aliased zone with a differing ambient "
                     "name. Adds a fourth distinct `currentZone`/`explicitZone` pairing "
                     "to the witness set.",
        "witness": _witness('dateCastZoneNameTester true (some "UTC") "B"'),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 8 SPEC cases (2 soundness
# positives, 1 admissibility, 2 frame-mutation, 3 uniqueness rivals) plus a
# 2-case AXIOM lane. This bundle models the SAME functional core (the timezone-
# name selection), so the SPEC uniqueness/soundness lanes port directly; the
# permission and precondition classes are vacuous on a referentially-transparent
# carrier with no `require` clause.
#
#   sibling case                     -> here
#   ---------------------------------------------------------------------
#   pos-control-early-return         -> pos-match-reorder          RE-EXPRESSED
#                                     + pos-flat-match             RE-EXPRESSED (stronger)
#   pos-control-echo-grounded-oracle -> pos-cheapest-echo          PORTED
#   admiss-f2p-shaped                -> admiss-f2p-shaped          PORTED (re-aimed)
#   frame-mut-current_name           -> (none)                     VACUOUS (no heap)
#   frame-mut-tzinfo                 -> (none)                     VACUOUS (no heap)
#   partial-domain-ignore-tzinfo     -> ignore-explicit-zone       PORTED (the bug)
#   partial-domain-off-wrong         -> aware-off-returns-ambient  PORTED
#   partial-domain-branch-swap       -> branch-swap                PORTED
#   (no sibling)                     -> supplied-zone-aliased-to-ambient  ADDED
#   AXIOM_TESTS (2)                  -> (none)                     DROPPED (G-AX lane)
#
# RE-EXPRESSED (pos-match-reorder): nagini's structural positive uses a guard-
#   clause / early-return shape mirroring the helper's branch order. Here the
#   equivalent structural difference reorders the inner `match explicitZone` arms
#   (supplied zone first, ambient fallback second) — a different source shape, same
#   branch selection. Verified out-of-band with a real build against the frozen
#   proof script.
# PORTED (pos-cheapest-echo): nagini returns the grounded @Pure oracle directly to
#   show no wrong echo exists. Here `resolveZoneName` is a transparent `def` (no
#   opaque answer-key), so returning it directly is the honest cheapest correct
#   impl and the same no-echo argument holds.
# PORTED, re-aimed (admiss-f2p-shaped): the absence of a `require` clause does not
#   make this lane vacuous — it changes what the lane MEASURES. On a total carrier
#   PRECOND-TOO-STRONG shows up as the obligation being unsatisfiable or degenerate
#   at an F2P-shaped input, so the case discharges the post-image BY EVALUATION at
#   three concrete F2P-shaped points (supplied zone honoured; supplied ≠ ambient
#   there; ambient fallback; no zone when zone-awareness is off) ahead of the frozen
#   obligation, kept verbatim with the `have` cleared. Both directions are pinned, so
#   a collapse to either the ambient name or the supplied zone would fail it.
# VACUOUS (frame-mutation x2): this backend is referentially transparent, declares
#   no `mut` binder, and has no heap — the two read-only inputs the nagini rivals
#   mutate are immutable Lean values here. No read-only field to overwrite and no
#   substitute probe. Not fabricated (porting map: vacuous here).
#
#   The four reject witnesses probe four DISTINCT input tuples:
#     ignore-explicit-zone               (true,  some "A",   "B")
#     aware-off-returns-ambient          (false, none,       "C")
#     branch-swap                        (true,  none,       "E")
#     supplied-zone-aliased-to-ambient   (true,  some "UTC", "B")
#   Across them tzAware takes {true, false}; explicitZone takes {some "A",
#   some "UTC", none}; currentZone takes {"B", "C", "E"}. Every top-level clause of
#   the postcondition is attacked (the zone-awareness gate by
#   aware-off-returns-ambient; the supplied-zone precedence arm by
#   ignore-explicit-zone on the WHOLE arm and by supplied-zone-aliased-to-ambient at
#   a single aliased zone name, which pins the precedence UNIFORMLY over zone names
#   rather than at one sampled name; the ambient-fallback arm by branch-swap), and
#   every input binder is varied across the witness set.
#   Every witness was confirmed with two real builds to ELABORATE against the
#   rival and FAIL against the frozen solution.
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job; the zone-name resolution is
# an A-reference validated there, and this gate ignores AXIOM_TESTS regardless.
AXIOM_TESTS = []
