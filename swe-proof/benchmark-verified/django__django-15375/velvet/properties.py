"""properties.py — G-PBT falsification battery for django__django-15375 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the elided ``prove_correct`` tactic body, is
changed — both regions the consumer spec view elides, so ``markers.same_spec``
holds and the ``prove_correct prepareAggregate`` obligation survives with a
byte-identical statement) and swaps in a candidate implementation; it is checked
by the real verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness must ELABORATE against the rival and FAIL
against the frozen solution).

DEFENDED SURFACE (one contracted method):

  prepareAggregate (terminal : Bool) (defaultVal : Option Int)
      return (out : Resolved)
    ensures out = prepared terminal defaultVal
    ensures out.isTerminal = terminal
    ensures out.hasFallback = defaultVal.isSome

The method prepares an aggregation clause to be added to a query, returning a
fresh two-field description ``Resolved`` (``isTerminal`` — the terminal/outer
marker the query builder later dispatches on; ``hasFallback`` — whether the
clause is the fallback form that substitutes a supplied value for the empty-rows
case). The post-image is a total function of the method's own two inputs
(``prepared`` is a concrete ``def`` over the ``pure`` region — there is NO opaque
answer key to echo, directive 8). The lead ``ensures`` (``out = prepared
terminal defaultVal``) SUBSUMES the two field-level clauses; the three together
pin TWO independent top-level behaviours:

  * (T) the TERMINAL MARKER — ``out.isTerminal = terminal`` UNCONDITIONALLY, i.e.
        the fresh clause carries the requested terminal marker whether or not a
        fallback value is supplied. This is the FIX: the terminal status is a
        property of the aggregation itself and must NOT be dropped merely because
        the fallback form was produced.
  * (F) the FALLBACK FORM — ``out.hasFallback = defaultVal.isSome``, i.e. the
        clause is the fallback form EXACTLY when a fallback value is supplied.

Both INPUT binders are free (no ``require`` clause) and the post-image must hold
for EVERY value of each:
  * ``terminal``   — the requested terminal/top-level marker; drives (T).
  * ``defaultVal`` — the optional fallback value; drives (F), and (via the
                     always-preserve rule) is the branch under which (T) is
                     load-bearing.

REPO BINDING (mapping.md): ``terminal`` ↔ the ``summarize`` flag; ``defaultVal``
↔ the ``default`` keyword argument (``none`` = no fallback, ``some _`` = a
fallback supplied); ``isTerminal`` ↔ the prepared expression's terminal marker;
``hasFallback`` ↔ whether the prepared expression is the fallback wrapper vs the
bare aggregate. The F2P (a final aggregation with a default after an annotate)
is the cell ``terminal=true, defaultVal=some _``: the fallback form MUST carry
``isTerminal=true`` (T) so the query builder promotes it to the outer level;
pre-patch it stays ``false``, the clause is stranded in the inner subquery, and
the backend emits malformed output. The P2P (a non-terminal aggregate with a
default) is the cell ``terminal=false, defaultVal=some _``: the fallback form
MUST carry ``isTerminal=false`` (T again) — so a hard-coded ``true`` is ALSO
wrong (the bogus mailing-list "fix").

ADVERSARIAL READ of the nagini classes on this carrier:
  * FRAME/PERMISSION-MUTATION — VACUOUS on this backend. The nagini surface has
    no ``Requires`` and no ``Acc(x,1/2)`` input: all inputs are immutable flags
    passed by value and the routine owns/mutates only the fresh objects it
    builds, so the sibling itself already records the mandatory frame-mutation
    probe as N/A. Lean/Velvet are additionally referentially transparent: every
    parameter is an immutable value, this bundle declares no ``mut`` binder,
    there is no heap and no aliasing. There is no read-only input to overwrite
    and no permission system to trip, so the class is doubly vacuous. No
    substitute is fabricated.
  * TERMINATION — the frozen impl is STRAIGHT-LINE (a single branch, no loop),
    and although this bundle runs under ``termination "total"`` there is no loop
    to diverge; a diverging-reject rival has no counterpart. Not fabricated.
  * UNGROUNDED-ORACLE ECHO — N/A, exactly as the sibling records. The ``axioms``
    region is empty; the post-image is ``prepared terminal defaultVal``, a
    concrete ``def`` computing the outcome from the method's own arguments, plus
    the two field clauses pinned DIRECTLY to the inputs. There is no opaque
    answer key to echo; the honest controls are the cheapest faithful reshapes
    (the ``pos-*`` cases).
  * CONTROL-FLOW-EFFECT — captured by the value abstraction, not lost to it. The
    structural difference "returned the bare aggregate vs a distinct
    fallback-supplying clause" is exactly the ``hasFallback`` field, whose whole
    purpose is to make that fork visible to the postcondition (the
    ``weak-return-bare`` rival is precisely that discriminator, rejected on (F)).
  * PARTIAL-DOMAIN / VALUE — heavily exercised. ``weak-drop-marker`` is correct
    on every ``terminal=false`` cell but wrong on the F2P; ``weak-hardcode-true``
    is correct on ``terminal=true`` but wrong on the P2P; ``weak-negated-marker``
    uses ``terminal`` with the wrong sign (a "reads terminal somewhere" heuristic
    would miss it).

WITNESS MECHANICS. The frozen impl is straight-line: its extracted program
reduces fully under ``decide``. Each reject rival carries a machine-checked
refutation ``witness`` — a Velvet tester statement
``prepareAggregateTester <terminal> <defaultVal> = false`` at ONE concrete
input, checked in a file whose ``prove_correct`` block has been stripped so no
tactic script can mask the verdict. ``Resolved`` already ``deriving
DecidableEq`` in the frozen spec, so the tester derivation needs no added
instance and no ``axiom`` / ``sorry`` / ``native_decide``. Both halves were
checked out-of-band with ``scripts/lean_verify.sh``: every witness ELABORATES
against its rival (exit 0) and FAILS against the frozen solution (``decide``
proves the proposition false, exit 1), so each rejection is a genuine spec
refutation and not mechanical tactic breakage.

AXIOM lane: EMPTY. ``meta.json`` declares no consumed ``axiom`` and no
deep-model reference; the unchanged-callee facts the direct model rests on are
validated executably by ``axiom_check.py`` (G-AX), and this gate ignores
``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "django__django-15375"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# The frozen impl body, verbatim — the entire single branch strictly BETWEEN the
# method's `-- impl-start` / `-- impl-end`. Every rival and reshape edits ONLY
# this block (and, for the admissibility case, the elided `prove_correct` tactic
# body), so the spec view is untouched and same_spec holds by construction.
_IMPL = (
    "    if defaultVal.isSome then\n"
    "      return { isTerminal := terminal, hasFallback := true }\n"
    "    else\n"
    "      return { isTerminal := terminal, hasFallback := false }"
)

assert _BASE.count(_IMPL) == 1, "method impl region drifted from expected text"

# The frozen proof, verbatim. Rivals leave it as-is (the rejection is carried by
# the witness, not the tactic script); the admissibility case retunes it to also
# close its in-region assert VC.
_PROOF = (
    "prove_correct prepareAggregate by\n"
    "  loom_solve\n"
    "  all_goals (cases defaultVal <;> simp_all [prepared])"
)

assert _BASE.count(_PROOF) == 1, "proof region drifted from expected text"


def _impl(new_body):
    """Full Solution.lean variant with ONLY the impl body replaced."""
    return _swap(_BASE, _IMPL, new_body)


def _impl_reproved(new_body, new_proof):
    """Impl body replaced AND the proof retuned (admissibility case)."""
    return _swap(_impl(new_body), _PROOF, new_proof)


# ---- witness preamble. The spec is a `method` CONTRACT, not a bare predicate,
# ---- so a witness reaches it through Velvet's own tester machinery:
# ---- `prepareAggregateTester <terminal> <defaultVal> = false` says the
# ---- extracted program's result violates the postcondition at that concrete
# ---- input. Checked in a file whose `prove_correct` block is stripped, so no
# ---- tactic script can mask the verdict. There are no `require` clauses, so
# ---- every input reaches the postcondition. `Resolved` derives DecidableEq in
# ---- the frozen spec, so `decide` settles every equality — no added instance. -
_TESTER = (
    "extract_program_for prepareAggregate\n"
    "prove_precondition_decidable_for prepareAggregate\n"
    "prove_postcondition_decidable_for prepareAggregate\n"
    "derive_tester_for prepareAggregate\n\n"
)


def _witness(call):
    return _TESTER + f"example : {call} = false := by\n  decide\n"


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # impls that MUST verify, else SPEC-TOO-STRONG. Each keeps the observable
    # object identical and only reshapes the executable surface; both keep the
    # FROZEN proof script (verified out-of-band with a real build).
    # =====================================================================
    {
        "id": "pos-branchless-flag",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: compute the fallback-form flag directly from the input option
        # in the constructor (no branch), instead of a two-arm `if`. Same object
        # on every input — `isTerminal := terminal`, `hasFallback :=
        # defaultVal.isSome` — so all three ensures still hold. Porting the
        # nagini "stamp the flags at construction time" positive control.
        "module": _impl(
            "    return { isTerminal := terminal, hasFallback := defaultVal.isSome }"),
        "rationale": "a correct impl with a DIFFERENT executable shape — collapse "
                     "the two-arm branch into a single constructor that computes "
                     "`hasFallback` directly from `defaultVal.isSome` — must "
                     "verify: it satisfies (T) `out.isTerminal = terminal` and "
                     "(F) `out.hasFallback = defaultVal.isSome` (hence "
                     "`out = prepared terminal defaultVal`) on every input. Else "
                     "SPEC-TOO-STRONG on branch structure.",
    },
    {
        "id": "pos-intermediate-local",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: read the fallback-form flag through a named intermediate local
        # and bind the whole clause description to a typed local before returning
        # it. Same value flow; the cheapest honest impl that still does the work,
        # standing in for the nagini grounded-oracle positive control.
        "module": _impl(
            "    let fb : Bool := defaultVal.isSome\n"
            "    let r : Resolved := { isTerminal := terminal, hasFallback := fb }\n"
            "    return r"),
        "rationale": "grounded-oracle honest positive control: name the "
                     "fallback-form flag through an intermediate local and bind "
                     "the clause description to a typed local before returning. "
                     "The decision and both fields are identical, so "
                     "`out = prepared terminal defaultVal` (and both field "
                     "clauses) still hold. Must verify; else SPEC-TOO-STRONG on "
                     "flag naming / result binding.",
    },

    # =====================================================================
    # ADMISSIBILITY — the method carries NO precondition (the pre-conditions
    # region is empty), so the sibling's "a normal F2P input satisfies the
    # precondition" self-call is degenerate here (every input is in-domain). The
    # residual admissibility risk on a total-domain spec is that the decision is
    # DEGENERATE at the interesting point — a spec whose two clauses never fork
    # would read like a live one. This case discharges an in-region assert that
    # the post-image function genuinely forks on BOTH binders at the F2P-shaped
    # points: a fallback IS reported present when supplied and absent when not
    # (F non-degenerate), and the terminal marker really can be false on the
    # fallback branch (T non-degenerate, the P2P direction). The impl is kept
    # verbatim so the method's own obligation still discharges; the proof is
    # retuned to also close the assert VC.
    # =====================================================================
    {
        "id": "admiss-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl_reproved(
            "    assert (with_name_prefix `assert\n"
            "      ((prepared true (some 0)).hasFallback = true ∧\n"
            "       (prepared true none).hasFallback = false ∧\n"
            "       (prepared false (some 0)).isTerminal = false))\n"
            + _IMPL,
            "prove_correct prepareAggregate by\n"
            "  loom_solve\n"
            "  all_goals first\n"
            "    | (cases defaultVal <;> simp_all [prepared])\n"
            "    | decide"),
        "rationale": "the post-image is satisfiable AND non-degenerate at the "
                     "F2P-shaped points: `prepared` reports the fallback form "
                     "present when a value is supplied and absent when it is not "
                     "(F genuinely forks on `defaultVal`), and the terminal "
                     "marker is `false` on a non-terminal fallback clause "
                     "(T genuinely forks on `terminal`, the P2P direction). The "
                     "in-region assert must discharge (else the clauses would be "
                     "degenerate / the obligation vacuous); the impl is kept "
                     "verbatim so the ensures still discharges too.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # concrete input and the refinement argument for why its faithful real
    # counterpart would NOT resolve the failing tests.
    # =====================================================================
    {
        "id": "weak-drop-marker",
        "kind": "uniqueness",
        "expect": "reject",
        # ATTACK 1 (PARTIAL-DOMAIN, = pre-patch). On the fallback path build the
        # clause UNMARKED (terminal marker dropped, class default false) instead
        # of carrying over the requested marker. Correct on every terminal=false
        # cell; wrong exactly when terminal AND a fallback are both present — the
        # F2P cell. Rejected on (T).
        "module": _impl(
            "    if defaultVal.isSome then\n"
            "      return { isTerminal := false, hasFallback := true }\n"
            "    else\n"
            "      return { isTerminal := terminal, hasFallback := false }"),
        "refinement": "this IS the pre-patch tail: the freshly built fallback "
                      "form inherits the class-default terminal marker (false) "
                      "and the requested marker is never carried over. For a "
                      "top-level aggregation with a fallback after an annotate "
                      "(the F2P, terminal=true, fallback supplied) the clause "
                      "stays unmarked, so the query builder does NOT promote it "
                      "to the outer level; it is stranded in the inner subquery "
                      "and the backend emits the malformed output the issue "
                      "reports. The F2P test then crashes. The faithful real "
                      "patch (drop the propagation) does NOT resolve — the exact "
                      "bug the spec senses (G-DIFF; matches Solution_prepatch).",
        "rationale": "REJECT from (T) `out.isTerminal = terminal`: on the "
                     "fallback path the rival returns `isTerminal=false` while "
                     "`terminal=true`, so the equality fails (and "
                     "`out ≠ prepared terminal defaultVal`). Refuted at the F2P "
                     "cell `(true, some 0)`.",
        "witness": _witness("prepareAggregateTester true (some 0)"),
    },
    {
        "id": "weak-hardcode-true",
        "kind": "uniqueness",
        "expect": "reject",
        # ATTACK 2 (the bogus mailing-list "fix" — hard-code the marker true).
        # Correct only when terminal=true; wrong on a NON-terminal aggregate with
        # a fallback (terminal=false, fallback supplied) — the P2P cell. Rejected
        # on (T). A true partial-domain rival: it passes the headline F2P but
        # breaks an existing test.
        "module": _impl(
            "    if defaultVal.isSome then\n"
            "      return { isTerminal := true, hasFallback := true }\n"
            "    else\n"
            "      return { isTerminal := terminal, hasFallback := false }"),
        "refinement": "this is the INCORRECT mailing-list patch: hard-code the "
                      "terminal marker to a constant true on the fallback path "
                      "instead of carrying the requested marker. It marks EVERY "
                      "fallback clause as terminal, even a NON-terminal aggregate "
                      "with a default (the P2P: a non-summary annotation with a "
                      "fallback that must keep the marker false). Marking it true "
                      "wrongly promotes it to the outer level / changes the "
                      "emitted output, so the P2P test fails. The faithful real "
                      "patch (hard-code true) does NOT resolve the full F2P+P2P "
                      "set.",
        "rationale": "REJECT from (T): the spec pins `out.isTerminal = terminal` "
                     "UNCONDITIONALLY (both `terminal` values). When "
                     "`terminal=false` on the fallback path the hard-coded true "
                     "violates the equality. Refuted at the P2P cell "
                     "`(false, some 0)` — the sub-domain where this rival is "
                     "wrong and `weak-drop-marker` is CORRECT, so it carries its "
                     "own separating input.",
        "witness": _witness("prepareAggregateTester false (some 0)"),
    },
    {
        "id": "weak-return-bare",
        "kind": "uniqueness",
        "expect": "reject",
        # ATTACK 3 (OBJECT-IDENTITY / control-flow-effect). Return the BARE
        # aggregation on the fallback path (never produce the fallback form). The
        # terminal marker is still correct (T holds), so this would pass a
        # marker-only spec; it is rejected SOLELY by (F) because hasFallback is
        # false where a fallback WAS supplied. This is the rival the `hasFallback`
        # observable exists to kill.
        "module": _impl(
            "    return { isTerminal := terminal, hasFallback := false }"),
        "refinement": "returning the bare aggregation on the fallback path drops "
                      "the fallback form entirely, so the resolved expression no "
                      "longer substitutes the supplied value when the aggregation "
                      "has no rows. EVERY default-value test asserts the default "
                      "is returned on an empty/normal aggregate; without the "
                      "fallback form they get the bare result (no substitution) "
                      "and FAIL. The faithful real patch does NOT resolve.",
        "rationale": "REJECT from (F) `out.hasFallback = defaultVal.isSome`: on "
                     "the fallback path the rival returns `hasFallback=false` "
                     "while `defaultVal.isSome = true`, so the equality fails "
                     "(and `out ≠ prepared terminal defaultVal`). This is the "
                     "object-identity/control-flow rival; the `hasFallback` "
                     "observable is exactly what discriminates it. Refuted at "
                     "`(true, some 5)` — a fallback-present cell with a distinct "
                     "value, exercising `defaultVal` at a non-zero payload.",
        "witness": _witness("prepareAggregateTester true (some 5)"),
    },
    {
        "id": "weak-inverted-fallback",
        "kind": "uniqueness",
        "expect": "reject",
        # ATTACK 4 (PARTIAL-DOMAIN, INVERTED). Report the fallback form on the
        # NO-fallback path and the bare form on the fallback path — i.e. invert
        # `hasFallback` w.r.t. `defaultVal`. Wrong on (F) on BOTH paths; refuted
        # here on the NO-fallback side to move `defaultVal` onto `none`, the value
        # every other reject witness holds at `some`.
        "module": _impl(
            "    if defaultVal.isSome then\n"
            "      return { isTerminal := terminal, hasFallback := false }\n"
            "    else\n"
            "      return { isTerminal := terminal, hasFallback := true }"),
        "refinement": "this inverts the fallback decision: it reports the bare "
                      "aggregation when a fallback WAS supplied (dropping the "
                      "substitution, so the default is lost) and reports the "
                      "fallback form when NO fallback was supplied (wrapping an "
                      "aggregate that should be returned bare, changing the "
                      "emitted output). Both the default-value tests (default "
                      "lost) and the no-default aggregate tests (spurious "
                      "fallback form) FAIL. The faithful real patch does NOT "
                      "resolve.",
        "rationale": "REJECT from (F): `hasFallback` is set opposite to "
                     "`defaultVal.isSome` on both paths. Refuted at the "
                     "NO-fallback cell `(true, none)`: the rival reports "
                     "`hasFallback=true` while `defaultVal.isSome = false`. This "
                     "witness moves `defaultVal` onto `none` — the branch every "
                     "other reject witness holds at `some`, so the battery "
                     "demonstrates the spec's dependence on fallback ABSENCE too.",
        "witness": _witness("prepareAggregateTester true none"),
    },
    {
        "id": "weak-negated-marker",
        "kind": "uniqueness",
        "expect": "reject",
        # ATTACK 5 (PARTIAL-DOMAIN, NEGATED marker). Keep the correct fallback
        # structure (F holds) but propagate the NEGATION of the requested marker
        # onto the fallback form. Wrong on (T) on the fallback path. Distinct from
        # attack 1 (constant false) and attack 2 (constant true): here the marker
        # DEPENDS on the input but with the wrong SIGN — a "reads terminal
        # somewhere" heuristic would miss it.
        "module": _impl(
            "    if defaultVal.isSome then\n"
            "      return { isTerminal := !terminal, hasFallback := true }\n"
            "    else\n"
            "      return { isTerminal := terminal, hasFallback := false }"),
        "refinement": "this stamps the fallback form with the NEGATION of the "
                      "requested terminal marker. For a top-level aggregation "
                      "with a fallback (the F2P, terminal=true) the clause gets "
                      "marked false — the SAME stranding as the unpatched bug, so "
                      "the F2P still crashes; and for a non-terminal aggregate "
                      "with a fallback (terminal=false) it wrongly marks the "
                      "clause true (the P2P direction). The faithful real patch "
                      "(negated propagation) does NOT resolve.",
        "rationale": "REJECT from (T): `out.isTerminal = !terminal` differs from "
                     "the required `terminal` on the fallback path for BOTH "
                     "`terminal` values. Refuted at `(false, some 9)`: the rival "
                     "returns `isTerminal = !false = true` where the spec demands "
                     "false — a point distinct from the constant-marker rivals "
                     "(both wrong here in the SAME direction only for one sign), "
                     "and varying `defaultVal` onto yet another value.",
        "witness": _witness("prepareAggregateTester false (some 9)"),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 8 SPEC cases (2 soundness
# positives, 1 admissibility, 5 uniqueness) plus a 1-case AXIOM lane. This velvet
# bundle models the SAME purely-functional core the nagini sibling contracts for
# resolve_aggregation — a fresh clause carrying TWO observable fields (the
# terminal marker + whether it is the fallback form) — so parity is achievable
# and every SPEC case ports.
#
#   sibling case                  -> here                        disposition
#   -----------------------------------------------------------------------
#   pos-control-construct-marked  -> pos-branchless-flag          PORTED (reshaped)
#   pos-control-intermediate-local-> pos-intermediate-local       PORTED
#   admiss-self-call              -> admiss-nondegenerate          RE-AIMED
#   weak-drop-propagation         -> weak-drop-marker              PORTED
#   weak-hardcode-true            -> weak-hardcode-true            PORTED
#   weak-return-bare-aggregate    -> weak-return-bare              PORTED
#   weak-inverted-wrap-path       -> weak-inverted-fallback        PORTED
#   weak-negated-final-flag       -> weak-negated-marker           PORTED
#   AXIOM_TESTS (1)               -> (none)                        DROPPED (G-AX)
#
# 7 ported, 1 re-aimed; 0 vacuous SPEC cases (the frame-mutation class is
# vacuous here but the nagini sibling already recorded its mandatory frame probe
# as N/A — there was no frame-mutation SPEC case to port), 1 axiom case dropped.
#
# VACUOUS (frame-mutation): the nagini surface has no `Requires` / no
#   `Acc(x,1/2)` input — all inputs are immutable flags by value — so the sibling
#   itself recorded the mandatory frame-mutation probe as N/A (there was never a
#   frame-mutation rival to port). This backend is additionally referentially
#   transparent and declares no `mut` binder, so the class is doubly vacuous. Not
#   fabricated.
# RE-AIMED (admissibility): the sibling self-calls resolve_aggregation on the
#   F2P-shaped input to prove the (empty) precondition admits it. This backend's
#   method has NO `require` clause, so that probe is degenerate. It is re-aimed at
#   the residual total-domain risk — that the post-image function is DEGENERATE at
#   the interesting points — via an in-region assert that `prepared` genuinely
#   forks on BOTH binders (F on `defaultVal` present/absent; T on the P2P
#   `terminal=false` fallback direction). The impl is kept verbatim so the ensures
#   still discharges; proof retuned to also close the assert VC.
# PORTED (positives): both nagini positive controls re-express directly — stamp
#   the flags at construction (`pos-branchless-flag`, a branchless constructor)
#   and read the flag through a named intermediate local (`pos-intermediate-
#   local`). Both keep the FROZEN proof script (verified with a real build).
# PORTED (uniqueness): all five nagini rivals re-express against the frozen
#   `Resolved` carrier. drop-propagation -> drop the terminal marker on the
#   fallback path (constant false); hardcode-true -> constant true; return-bare
#   -> report the bare form (hasFallback dropped); inverted-wrap -> invert
#   hasFallback vs defaultVal; negated-final -> negate the marker. Each carries a
#   machine-checked witness that ELABORATES against the rival and FAILS against
#   the frozen solution (two real builds per case, confirmed out-of-band).
#
# BINDER / CLAUSE COVERAGE of the reject witnesses over the two input binders
#   (pts = 5 distinct input points):
#     terminal    — true  (drop, return-bare, inverted);
#                   false (hardcode, negated):  BOTH values exercised, never
#                   held fixed.
#     defaultVal  — some 0 (drop, hardcode); some 5 (return-bare);
#                   none (inverted); some 9 (negated): the PRESENCE bit is varied
#                   (none vs some — the inverted rival's witness DEPENDS on `none`,
#                   the branch every other witness holds at `some`), and the
#                   carried value is varied {0, 5, 9} so no rival is pinned to a
#                   single payload.
#   Both independent top-level behaviours are attacked: the terminal marker (T)
#   in both wrong directions and with the wrong sign (drop / hardcode / negated),
#   and the fallback form (F) by both dropping it and inverting it (return-bare /
#   inverted). The lead clause `out = prepared terminal defaultVal` subsumes both
#   field clauses and is violated by every rival.
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job; this bundle declares no
# consumed axiom and no deep-model reference (the unchanged-callee facts the
# direct model rests on are executably checked by axiom_check.py), and this gate
# ignores AXIOM_TESTS regardless.
AXIOM_TESTS = []
