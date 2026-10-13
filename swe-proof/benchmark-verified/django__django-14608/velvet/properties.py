"""properties.py — G-PBT falsification battery for django__django-14608 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes. Each
SPEC_TESTS case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed —
both of which the consumer spec view elides, so ``markers.same_spec`` holds and
the ``prove_correct buildNonFormErrors`` header survives) and swaps in a
candidate implementation; it is judged by the real verifier. ``expect:"verify"``
passes iff (in scope AND verifies); ``expect:"reject"`` passes iff (in scope AND
does NOT verify AND its refutation ``witness`` discriminates — the witness must
ELABORATE against the rival and FAIL against the frozen solution).

DEFENDED SURFACE (one contracted method, one input binder):

  buildNonFormErrors (errors : List (List Char)) return (out : ErrorBox)
    ensures out.data     = errors                                 -- CLAUSE 1
    ensures out.cssClass = cssClassFor (some "nonform".toList)     -- CLAUSE 2

over a two-field record ``ErrorBox { data, cssClass }`` and the pure

  cssClassFor none     = "errorlist".toList
  cssClassFor (some m) = "errorlist ".toList ++ m

so the two clauses pin two INDEPENDENT sub-behaviours of the modeled
construction:

  * CLAUSE 1 (MESSAGES): the collection holds exactly the supplied messages, in
    order, none added and none lost. Grounded in the input binder ``errors``.
  * CLAUSE 2 (RENDERED CLASS): the collection renders under the base class
    followed by a single space and the ``nonform`` modifier — i.e. the modifier
    is present, is the right one, and is separated as ``cssClassFor`` prescribes.
    This clause holds UNCONDITIONALLY, on every input, which is what closes the
    sub-domain attacks below.

``cssClassFor`` is a total ``def`` over ``Option (List Char)`` that unfolds to
character literals, and ``out.data = errors`` is stated over the method's own
argument, so BOTH clauses are GROUNDED: there is no opaque answer key for a wrong
impl to echo, and the cheapest impl satisfying the clauses is the honest one.
The ``axioms`` region is empty (``cssClassFor`` is a deep A-reference validated
== the real unchanged class-string computation by axiom_check.py, NOT a consumed
axiom), so the nagini sibling's ungrounded-oracle concern does not arise; it is
replaced here by honest positive controls.

THE CARRIER IS FULLY TRANSPARENT. Every leaf is a ``Char`` literal or a ``List``
of them, so a witness reaches the contract through Velvet's own tester machinery
(``extract_program_for`` / ``prove_precondition_decidable_for`` /
``prove_postcondition_decidable_for`` / ``derive_tester_for``):
``buildNonFormErrorsTester errors = false`` says the extracted program's result
violates the method's postcondition at that concrete input, and ``decide``
closes it outright. No witness needs to CONDITION on the carrier, so no witness
binds a hypothesis and there is no joint-satisfiability obligation for the gate's
consistency probe to discharge. Both halves of every witness were checked
out-of-band with ``scripts/lean_verify.sh`` before shipping (rival exit 0, gold
nonzero); see the accounting block at the bottom.

Because the frozen impl is a straight-line ``let``/``return`` (no loop), the
rivals here are rejected by the VALUE clause itself rather than by a tactic gap:
each reject variant's build fails with an explicit unsolved
``ensures_1``/``ensures_2`` goal naming the two sides that differ. The witness is
still what the gate scores, and is what makes the rejection attributable.

ADVERSARIAL READ of the nagini classes on this carrier:
  * FRAME / PERMISSION-MUTATION — VACUOUS. The sibling carries this as MANDATORY
    (two rivals that WRITE into a message list held read-only at half
    permission). Lean and Velvet are referentially transparent: ``errors`` is an
    immutable value, this bundle declares NO ``mut`` binder, and there is no heap
    and no aliasing — so there is no read-only input to overwrite and no
    substitute probe. Not fabricated.
  * PARTIAL-DOMAIN / VALUE — APPLIES, and is the heart of the port. Each sibling
    partial-domain rival re-expresses onto one of the two clauses above.
  * DIVERGENCE / NON-TERMINATION - the class is INAPPLICABLE to this impl and
    CLOSED BY THE SEMANTICS against any rival that manufactures it. The frozen
    impl is LOOP-FREE (straight-line ``let`` over immutable values, no loop and
    no recursion), so there is no control flow here to make diverge: a
    diverging rival cannot be obtained by mutating this body, it has to bring a
    loop of its own. When it does, the semantics refuse it. This bundle sets
    ``loom.semantics.termination "total"`` AND carries
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
  * AXIOM lane — dropped (G-AX's job; this gate ignores AXIOM_TESTS).
"""
from pathlib import Path

INSTANCE = "django__django-14608"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Anchors. Each lies wholly inside a region the consumer spec view elides (the
# body between -- impl-start / -- impl-end, or the prove_correct tactic body) and
# is unique in Solution.lean; _swap asserts both at load, so the manifest breaks
# loudly if the frozen solution ever changes. Editing only these keeps
# markers.same_spec True and the `prove_correct buildNonFormErrors` header
# byte-identical.
# ---------------------------------------------------------------------------

# The WHOLE executable body: bind the rendered class, then return the record.
# Note the `    let cls := ` prefix is what makes this unique — the modifier
# expression itself also occurs in the (frozen, untouched) ensures clause.
_IMPL = ('    let cls := cssClassFor (some "nonform".toList)\n'
         '    return { data := errors, cssClass := cls }')

# The frozen proof body. Elided from the spec view, so a positive control that
# reshapes the impl (or the admissibility case, which adds an in-region assert)
# may retune it; every reject rival keeps it verbatim.
_PROOF = "prove_correct buildNonFormErrors by\n  loom_solve"


def _impl(cls_expr, data_expr="errors"):
    """Solution.lean whose body binds `cls_expr` and returns `data_expr`."""
    return _swap(_BASE, _IMPL,
                 f"    let cls := {cls_expr}\n"
                 f"    return {{ data := {data_expr}, cssClass := cls }}")


# ---- witness preamble. The spec is a `method` CONTRACT, not a bare predicate,
# ---- so a witness reaches the post-image through Velvet's tester machinery:
# ---- `buildNonFormErrorsTester errors = false` says the extracted program's
# ---- result violates the postcondition at that concrete input. Checked in a
# ---- file whose `prove_correct` block has been stripped, so no tactic script
# ---- can mask the verdict. Every probed input is a small `List (List Char)`
# ---- literal, so `decide` reduces the whole tester to a Boolean — there is no
# ---- opaque leaf and no carrier conditioning is needed.
_TESTER = (
    "extract_program_for buildNonFormErrors\n"
    "prove_precondition_decidable_for buildNonFormErrors\n"
    "prove_postcondition_decidable_for buildNonFormErrors\n"
    "derive_tester_for buildNonFormErrors\n\n"
)


def _witness(inp):
    return _TESTER + (f"example : buildNonFormErrorsTester {inp} = false := by\n"
                      "  decide\n")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally DIFFERENT but CORRECT impls
    # that MUST verify. If a faithful correct impl cannot verify, the spec is
    # SPEC-TOO-STRONG. Both defend BOTH clauses (each returns the full message
    # list and the fully-modified class), which is what "every obligation is
    # defended" requires.
    # =====================================================================
    {
        "id": "pos-control-build-from-concat",
        "kind": "soundness",
        "expect": "verify",
        # Instead of calling the class-string model, build the rendered class
        # COMPOSITIONALLY: base characters, one separating space, modifier
        # characters. Extensionally the same list, so both clauses still hold.
        # The frozen proof leaves the residual `... = cssClassFor (some ...)`
        # goal, which needs the definitional unfold — hence the retune (the
        # tactic body is elided from the spec view, so this is in scope).
        "module": _swap(
            _impl('"errorlist".toList ++ [\' \'] ++ "nonform".toList'),
            _PROOF,
            "prove_correct buildNonFormErrors by\n  loom_solve\n"
            "  simp [cssClassFor]"),
        "rationale": "structurally-different CORRECT impl: assemble the rendered "
                     "class from the base characters, a single separating space "
                     "and the modifier characters rather than by applying the "
                     "class-string model to the modifier. The assembled list is "
                     "extensionally equal to `cssClassFor (some \"nonform\")`, so "
                     "CLAUSE 2 holds; the message list is returned unchanged, so "
                     "CLAUSE 1 holds. Defends both clauses. A faithful correct "
                     "impl that could not verify would mean the postcondition is "
                     "over-fit to one syntactic FORM of the class string => "
                     "SPEC-TOO-STRONG. (Ports the sibling's "
                     "pos-control-build-from-concat.)",
    },
    {
        "id": "pos-control-branch-on-messages",
        "kind": "soundness",
        "expect": "verify",
        # Split the single return into two branches on whether any message was
        # supplied, naming the modifier in a `let` shared by both arms. On the
        # empty branch the returned message list is spelled `[]` rather than
        # `errors`, which is the same value there. Behaviourally identical on
        # every input; the frozen proof closes it with no retune.
        "module": _swap(
            _BASE, _IMPL,
            '    let modifier := some "nonform".toList\n'
            '    if errors.isEmpty then\n'
            '      return { cssClass := cssClassFor modifier, data := [] }\n'
            '    else\n'
            '      return { cssClass := cssClassFor modifier, data := errors }'),
        "rationale": "branch-reshaped CORRECT impl: case-split on whether any "
                     "message was supplied, hoist the modifier into a shared "
                     "`let`, and spell the empty branch's message list as `[]` "
                     "(the same value there). Behaviourally identical on every "
                     "input — the modified class is attached on BOTH arms — so "
                     "both clauses discharge and the frozen proof needs no "
                     "retune. A faithful reshape MUST verify, else the clauses "
                     "are over-fit to the straight-line FORM => SPEC-TOO-STRONG. "
                     "(Ports the sibling's pos-control-reorder-rejected-first: "
                     "same idea — the control cases handled in separate branches "
                     "rather than in one flow.) It also fixes the reference point "
                     "for the sub-domain rivals below: a correct impl may branch, "
                     "but every branch must attach the modifier.",
    },

    # =====================================================================
    # ADMISSIBILITY — this method declares NO `require` clause (the
    # pre-conditions region is empty), so the sibling's "the precondition admits
    # an ordinary input" probe is vacuous: nothing could exclude any input. The
    # residual admissibility risk on a total domain is that the post-image is
    # UNSATISFIABLE or DEGENERATE at the interesting point — a spec no impl can
    # meet reads like a spec every impl meets, and a CLAUSE 2 that failed to
    # distinguish the modified class from the unmodified one would make every
    # rival below pass for free. This case discharges an in-region `assert`, at
    # fully concrete values, that the post-image is non-degenerate: the modified
    # class really is the base characters + one space + the modifier, and really
    # does DIFFER from the unmodified class. The surrounding impl is kept
    # verbatim so the method's own obligation still discharges; only the tactic
    # body is retuned, to clear the extra assert goal.
    #
    # The assert is LIVE, not decoration: substituting the FALSE claim at the
    # same point (`cssClassFor (some "nonform") = cssClassFor none`) leaves
    # `⊢ False` unsolved and the build fails — checked out-of-band.
    # =====================================================================
    {
        "id": "admiss-postimage-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _swap(_BASE, _IMPL,
                  '    assert (with_name_prefix `admiss\n'
                  '      (cssClassFor (some "nonform".toList)\n'
                  '          = "errorlist".toList ++ [\' \'] ++ "nonform".toList\n'
                  '        ∧ cssClassFor (some "nonform".toList) ≠ cssClassFor none))\n'
                  + _IMPL),
            _PROOF,
            "prove_correct buildNonFormErrors by\n  loom_solve\n"
            "  all_goals first\n    | decide\n    | simp [cssClassFor]"),
        "rationale": "no `require` clause exists, so precondition admissibility "
                     "is vacuous; what is probed instead is that the post-image "
                     "is SATISFIABLE and NON-DEGENERATE. The in-region assert "
                     "pins, at concrete values, that the modified class is the "
                     "base characters followed by exactly one space and the "
                     "modifier, AND that it differs from the unmodified class. "
                     "Both must discharge (else CLAUSE 2 is degenerate — it "
                     "would not distinguish the modified from the unmodified "
                     "rendering, and every uniqueness rival below would pass for "
                     "free). The impl is kept verbatim so both ensures clauses "
                     "discharge too. (Re-aims the sibling's "
                     "admiss-f2p-shaped-input, whose permission-establishment "
                     "content has no counterpart here.)",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected. Each carries a machine-checked refutation witness at
    # a DISTINCT concrete input and the refinement argument for why its faithful
    # real counterpart would NOT resolve the failing tests. Four attack CLAUSE 2
    # (the rendered class) from four different angles; two attack CLAUSE 1 (the
    # held messages).
    # =====================================================================

    # ---- CLAUSE 2: no modifier at all — the pre-image behaviour ----
    {
        "id": "uniq-no-modifier",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl("cssClassFor none"),
        "refinement": "this IS the pre-image behaviour: construct the collection "
                      "with no modifier label, so it renders under the bare base "
                      "class. All four failing tests pin the rendered class of "
                      "the non-form-error collection — three compare the rendered "
                      "markup against `<ul class=\"errorlist nonform\">...`, and "
                      "the fourth compares it against a collection built WITH the "
                      "modifier. With no modifier the rendered class is the bare "
                      "base class and every one of those comparisons fails, so "
                      "the faithful counterpart does NOT resolve. (It is the "
                      "bundle's own pre-image skeleton, which G-DIFF records as "
                      "failing.)",
        "rationale": "REJECT from CLAUSE 2 (`out.cssClass = cssClassFor (some "
                     "\"nonform\".toList)`): the impl supplies `none`, and "
                     "`cssClassFor none` is the base characters alone while the "
                     "post-image is the base characters + space + modifier — "
                     "provably unequal, on EVERY input. The build fails with "
                     "exactly that unsolved `ensures_1` goal, not a tactic gap. "
                     "Refuted at the one-message input `[['x']]`. (Ports the "
                     "sibling's uniq-no-marker-init / uniq-no-marker-rejected, "
                     "which are two separate rivals there because that carrier "
                     "models two construction sites; this carrier models the "
                     "single shared construction, so they collapse into one — see "
                     "uniq-modifier-on-empty-only for the site-partial attack "
                     "that keeps their disjointness alive.)",
        "witness": _witness("[['x']]"),
    },

    # ---- CLAUSE 2: the WRONG modifier ----
    {
        "id": "uniq-wrong-modifier",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl('cssClassFor (some "nonfield".toList)'),
        "refinement": "supplying the neighbouring modifier label that the same "
                      "rendering mechanism already uses elsewhere — the "
                      "by-analogy mistake the public statement's own cited "
                      "precedent invites — renders the collection under that "
                      "other label instead. The failing tests pin the exact "
                      "rendered class string, so a different modifier produces a "
                      "different class attribute and the assertions fail; the "
                      "faithful counterpart does NOT resolve.",
        "rationale": "REJECT from CLAUSE 2: `cssClassFor` is injective in its "
                     "modifier on distinct labels, and the post-image fixes the "
                     "label to `nonform`, so the rendered class provably differs "
                     "on every input. Refuted at the two-message input "
                     "`[['y'], ['z']]` — a different length and different "
                     "contents from every other witness. (Ports the sibling's "
                     "uniq-wrong-marker, same by-analogy label.)",
        "witness": _witness("[['y'], ['z']]"),
    },

    # ---- CLAUSE 2: right modifier, wrong SEPARATION ----
    {
        "id": "uniq-modifier-not-separated",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl('"errorlist".toList ++ "nonform".toList'),
        "refinement": "concatenating the modifier onto the base class without "
                      "the separating space yields a single fused token rather "
                      "than two class names. The failing tests pin the rendered "
                      "class string exactly, and markup consumers select on "
                      "whitespace-separated class names, so a fused token neither "
                      "matches the asserted string nor is selectable as either "
                      "name — the whole point of the requested distinction is "
                      "lost. The faithful counterpart does NOT resolve.",
        "rationale": "REJECT from CLAUSE 2: the post-image places exactly one "
                     "space between the base characters and the modifier "
                     "(`cssClassFor (some m) = \"errorlist \" ++ m`), and the "
                     "impl omits it, so the two character lists differ in length "
                     "and contents on every input. This is the near-miss that "
                     "gets the modifier RIGHT and the composition wrong, so it "
                     "needs its own witness rather than sharing "
                     "uniq-no-modifier's: it agrees with gold on which label is "
                     "used and disagrees only on the separation. Refuted at the "
                     "EMPTY message list `([] : List (List Char))` — the "
                     "length-zero input, which no other witness probes, and where "
                     "CLAUSE 1 is trivially satisfied so the rejection is "
                     "attributable to CLAUSE 2 alone.",
        "witness": _witness("([] : List (List Char))"),
    },

    # ---- CLAUSE 2: modifier attached on only PART of the domain ----
    {
        "id": "uniq-modifier-on-empty-only",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl('if errors.isEmpty then cssClassFor (some "nonform".toList) '
                        'else cssClassFor none'),
        "refinement": "attaching the modifier only where no message was supplied "
                      "is the HALF-DONE change: the collection renders correctly "
                      "while it holds nothing, and reverts to the bare base class "
                      "exactly once it holds the messages a reader would see. All "
                      "four failing tests observe the collection AFTER messages "
                      "have been recorded (each asserts a non-empty rendered "
                      "list), so all four still see the bare base class and still "
                      "fail; the faithful counterpart does NOT resolve. This is "
                      "the sub-domain analogue of the sibling's second "
                      "pre-image rival — the change applied at one construction "
                      "point and missed at the other.",
        "rationale": "REJECT from CLAUSE 2, which is UNCONDITIONAL: it must hold "
                     "on every input, so an impl whose class string depends on "
                     "the message list at all is refutable wherever its branch "
                     "picks the unmodified class. PARTIAL-DOMAIN attack: agrees "
                     "with gold on the empty list and diverges on every non-empty "
                     "one, so — unlike uniq-no-modifier, which is wrong "
                     "everywhere — it needs a witness in the non-empty "
                     "sub-domain. Refuted at the three-message input "
                     "`[['p'], ['q'], ['r']]`, the longest point any witness "
                     "probes. This rival is also what makes `errors` "
                     "load-bearing for CLAUSE 2: it is the only one whose "
                     "rendered class varies with the binder.",
        "witness": _witness("[['p'], ['q'], ['r']]"),
    },

    # ---- CLAUSE 1: the messages are dropped entirely ----
    {
        "id": "uniq-drops-messages",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl('cssClassFor (some "nonform".toList)', "[]"),
        "refinement": "attaching the modifier correctly but building the "
                      "collection EMPTY rather than from the supplied messages "
                      "loses the recorded non-form errors. Every failing test "
                      "asserts the collection's message content as well as its "
                      "rendered class — the message list equality, and the "
                      "rendered markup including the message items — so an empty "
                      "collection fails them even though its class string is "
                      "right. The faithful counterpart does NOT resolve.",
        "rationale": "REJECT from CLAUSE 1 (`out.data = errors`): the impl "
                     "returns the empty list, which differs from `errors` at "
                     "every non-empty input. Attacks the OTHER top-level clause, "
                     "which every CLAUSE 2 rival above leaves satisfied — without "
                     "it a rival that got the class right and threw the messages "
                     "away would go unnoticed. Refuted at the two-message input "
                     "`[['m'], ['n']]`. (Ports the sibling's "
                     "uniq-skip-rejected-rebuild, whose defect is likewise that "
                     "the collection is not populated from the supplied "
                     "messages.)",
        "witness": _witness("[['m'], ['n']]"),
    },

    # ---- CLAUSE 1: the messages are truncated (off-by-one) ----
    {
        "id": "uniq-truncates-messages",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl('cssClassFor (some "nonform".toList)', "errors.dropLast"),
        "refinement": "copying all supplied messages except the last is the "
                      "off-by-one when populating the collection: the recorded "
                      "list comes back missing its final message. Each failing "
                      "test pins the collection's messages exactly, and each "
                      "observes a single recorded message — which this drops "
                      "entirely, leaving an empty collection — so the message "
                      "equality and the rendered markup both fail. The faithful "
                      "counterpart does NOT resolve on any message list of length "
                      "one or more. It is a near-miss relative to "
                      "uniq-drops-messages: on any list of length two or more it "
                      "still returns the leading messages, where "
                      "uniq-drops-messages returns nothing at all, so its witness "
                      "is placed where dropping exactly one element — rather than "
                      "dropping everything — is what breaks it.",
        "rationale": "REJECT from CLAUSE 1: the impl returns `errors.dropLast`, "
                     "which differs from `errors` at every non-empty input. This "
                     "is the NEAR-MISS on CLAUSE 1 — it preserves order and the "
                     "leading contents and errs only by losing the final element. "
                     "Its witness must therefore sit where it is DISTINGUISHABLE "
                     "from uniq-drops-messages, which is at length two or more: at "
                     "the single-message input the two rivals return the SAME "
                     "value (`[['k']].dropLast = []`, machine-checked by `decide`), "
                     "so a length-one witness would attest to nothing this "
                     "battery's uniq-drops-messages witness does not already "
                     "attest to. Refuted at the two-message input "
                     "`[['k'], ['l']]`, where it returns `[['k']]` — the leading "
                     "message kept, the last lost — which is unequal both to "
                     "`errors` (so CLAUSE 1 fails) and to `[]` (so the near-miss "
                     "is genuinely separated from wholesale loss).",
        "witness": _witness("[['k'], ['l']]"),
    },
]


# ---------------------------------------------------------------------------
# NAGINI -> VELVET ACCOUNTING. The sibling battery has 11 SPEC cases (2
# soundness positives, 1 admissibility, 2 frame-mutation rivals, 6 uniqueness
# rivals) plus a 2-case AXIOM lane. This bundle contracts ONE method whose
# post-image is two clauses over one input binder, where the sibling contracts a
# five-parameter mutating operation over a three-way control split, so several
# sibling cases are attached to behaviour this carrier does not model. 9 cases
# ship: 2 soundness, 1 admissibility, 6 uniqueness.
#
#   sibling case                    -> here                          disposition
#   ---------------------------------------------------------------------------
#   pos-control-build-from-concat   -> pos-control-build-from-concat  PORTED
#   pos-control-reorder-rejected-   -> pos-control-branch-on-messages PORTED
#     first                                                            (re-aimed)
#   admiss-f2p-shaped-input         -> admiss-postimage-nondegenerate  RE-AIMED
#   frame-mutate-append             -> (none)                          VACUOUS
#   frame-mutate-store              -> (none)                          VACUOUS
#   uniq-no-marker-init             -> uniq-no-modifier                PORTED
#   uniq-no-marker-rejected         -> uniq-no-modifier (merged) +     PORTED
#                                      uniq-modifier-on-empty-only      (re-aimed)
#   uniq-wrong-marker               -> uniq-wrong-modifier             PORTED
#   uniq-skip-rejected-rebuild      -> uniq-drops-messages             PORTED
#   uniq-rejected-copy-prefix       -> uniq-truncates-messages         PORTED
#   uniq-drop-group-append          -> (none)                          NOT MODELED
#   (no sibling)                    -> uniq-modifier-not-separated     ADDED
#   AXIOM_TESTS (2)                 -> (none)                          DROPPED
#
# 6 ported (one of them merged from two siblings), 1 re-aimed, 1 added,
# 2 vacuous, 1 not modeled, 2 dropped.
#
# PORTED — positive controls. The sibling builds the class string
#   compositionally at both of its construction points instead of as one
#   spelled-out literal; here the same argument becomes assembling the rendered
#   class from base characters + one space + modifier instead of applying the
#   class-string model. The sibling's branch-reorder handles its control cases in
#   separate branches; here the analogue case-splits on whether any message was
#   supplied and attaches the modifier on both arms. Both verified to build (the
#   concat control needs the definitional unfold in its retuned tactic body; the
#   branch control closes under the frozen proof unchanged).
# RE-AIMED — admissibility. The sibling establishes that a legitimate input
#   satisfies its precondition. This method has NO `require` clause, so that
#   probe is vacuous — nothing could exclude any input, and the post-image is a
#   total function of the argument, so it is satisfiable everywhere by
#   construction (the gold impl and both positive controls witness it). Rather
#   than omit the lane, the case is re-aimed at the residual total-domain risk:
#   that the post-image is DEGENERATE. It asserts in-region, at concrete values,
#   that the modified class is base + one space + modifier and that it DIFFERS
#   from the unmodified class. That is load-bearing rather than decorative: if
#   CLAUSE 2 could not tell the modified rendering from the unmodified one, every
#   uniqueness rival below would pass for free. Liveness confirmed out-of-band —
#   the FALSE claim at the same point leaves `⊢ False` unsolved and the build
#   fails.
# PORTED / MERGED — the two pre-image rivals. The sibling models TWO
#   construction points and so carries two disjoint pre-image rivals (no marker
#   at the first, no marker at the second). This bundle models the single shared
#   construction the change touches at both points with the same delta (meta.json
#   records the second point as `additional_change_sites`, same behavioral
#   delta), so a rival that omits the modifier omits it once —
#   uniq-no-modifier, which is also this bundle's own pre-image skeleton.
#   Their DISJOINTNESS is not lost, though: uniq-modifier-on-empty-only
#   re-expresses it as a sub-domain attack (modifier attached where the
#   collection is empty, missing where it holds messages), which is exactly "the
#   change applied at one point and missed at the other" as this carrier can see
#   it. That rival is what keeps the empty / non-empty split under attack.
# ADDED — uniq-modifier-not-separated. The sibling has no counterpart: its
#   carrier spells the class as one flat code-point literal, so "right label,
#   wrong separation" is not a distinct mistake there. Here `cssClassFor`
#   composes the class from base + space + modifier, which makes the separation
#   an independently attackable part of CLAUSE 2 — and a fused single token is a
#   real failure mode (markup consumers select on whitespace-separated names, so
#   neither name is selectable). It is also the only witness at the length-zero
#   input.
# NOT MODELED — uniq-drop-group-append. The sibling's third control case
#   (a single collection-wide message appended before the failure check, which
#   its spec pins with a dedicated implication arm) has no counterpart: this
#   bundle's method takes the message list as its argument and does not model
#   where the messages came from or the intermediate collection state, so there
#   is no append to drop and no clause it would violate. Omitted as carrier
#   narrowing, not as an effort gap: a rival for it would have to invent a
#   behaviour the frozen spec does not mention.
# VACUOUS — the two frame-mutation rivals. The sibling carries them as MANDATORY
#   because its message list is held read-only at half permission and a rival can
#   illegally write into it (append, or index-store). This backend is
#   referentially transparent: `errors` is an immutable value, the method
#   declares no `mut` binder, and there is no heap and no aliasing, so there is
#   no read-only input to overwrite and no substitute probe exists. Not
#   fabricated.
# DROPPED — AXIOM_TESTS (2 cases). The axiom lane is G-AX's job (axiom_check.py
#   validates the deep A-reference `cssClassFor` == the real unchanged
#   class-string computation; meta.json declares no consumed axiom). This gate
#   ignores AXIOM_TESTS regardless.
#
# DIVERGENCE LANE - the class is INAPPLICABLE to this impl and CLOSED BY THE
#   SEMANTICS against any rival that manufactures it. The frozen impl is
#   LOOP-FREE (straight-line ``let`` over immutable values, no loop and no
#   recursion), so there is no control flow here to make diverge: a diverging
#   rival cannot be obtained by mutating this body, it has to bring a loop of
#   its own. When it does, the semantics refuse it. This bundle sets
#   ``loom.semantics.termination "total"`` AND carries
#   ``open TotalCorrectness``, and the ``open`` is the line that actually
#   selects the semantics: both namespaces define
#   ``WPGen.forWithInvariantLoop``, the later ``open`` wins, and the
#   ``PartialCorrectness`` version takes a loop measure and DISCARDS it, so the
#   two lines have to move together and they do here. Under the total scope a
#   postcondition is claimed of ALL runs and not only of terminating ones, so a
#   spliced loop owes a descent obligation ``measure b' < measure b``.
#   Re-measured on this bundle with a real build: a
#   ``while spin > 0 do spin := spin`` prefix carrying ``decreasing spin`` is
#   REJECTED on the measure's own goal (``case «decreasing_1: spin» ... ⊢ spin
#   < spin``). Dropping the clause rather than faking it is refused even
#   earlier, by the elaborator's own check (``Decreasing annotations are
#   required in total correctness semantics``). So divergence neither applies
#   to this impl nor discharges the ``ensures`` clauses vacuously if a rival
#   introduces it.
#
# BINDER / CLAUSE COVERAGE. One obligation (`prove_correct buildNonFormErrors`),
#   one input binder (`errors : List (List Char)`), two independent top-level
#   clauses.
#     * DEFENDED: both positive controls satisfy both clauses; the admissibility
#       case additionally pins CLAUSE 2's post-image non-degenerate.
#     * ATTACKED: CLAUSE 2 by four rivals (modifier absent / wrong label /
#       unseparated / present on only part of the domain); CLAUSE 1 by two
#       (messages dropped / truncated). Neither clause is left unattacked.
#     * BINDER VARIED: the six reject witnesses probe six DISTINCT points —
#       `[]` (length 0), `[['x']]` (length 1), `[['y'],['z']]`, `[['m'],['n']]`,
#       `[['k'],['l']]` (length 2, pairwise different contents),
#       `[['p'],['q'],['r']]` (length 3) — so `errors` is moved in both length
#       (0,1,2,2,2,3) and contents, and no two rivals share an input. pts = 6.
#       The binder is load-bearing for BOTH clauses, not just for CLAUSE 1:
#       uniq-modifier-on-empty-only makes the rendered class depend on `errors`,
#       so the empty / non-empty split is probed on the class clause too — which
#       is precisely the "every witness held the binder at one value" failure
#       mode the port guidance warns about, and the reason the length-zero and
#       length-three points are both present.
#     * NEAR-MISSES SEPARATED: uniq-modifier-not-separated gets its own witness
#       rather than sharing uniq-no-modifier's (it agrees with gold on WHICH
#       label is used); uniq-truncates-messages gets its own rather than sharing
#       uniq-drops-messages'. Those two CLAUSE 1 rivals coincide on the empty
#       list AND at every length-one input (`[c].dropLast = []`), so the
#       truncation witness is placed at length TWO, the shortest input where the
#       off-by-one is distinguishable from wholesale loss: there dropLast returns
#       the leading message while the other rival returns nothing. (An earlier
#       revision of this battery witnessed the truncation rival at a length-one
#       input, where it is observationally identical to uniq-drops-messages —
#       both rejections were real, but the near-miss the case claims to probe was
#       not exercised. Corrected by audit.) No rival's rationale claims a
#       sub-domain the manifest does not demonstrate.
# WITNESS DISCRIMINATION — verified during authoring with two real builds per
#   reject case (scripts/lean_verify.sh): each witness ELABORATES against its
#   rival (exit 0) and FAILS against the frozen solution (nonzero, `decide`
#   reporting the tester is TRUE of gold at that input). Every reject variant was
#   also built on its own and fails with an explicit unsolved `ensures_1` /
#   `ensures_2` goal naming the two sides that differ — so these rejections are
#   attributable to the value clauses, not to a tactic script tuned to the frozen
#   body. No witness binds a hypothesis (the carrier is fully transparent and
#   `decide` closes every tester at a literal), so the gate's joint-satisfiability
#   probe has nothing to discharge and no witness can be a
#   contradiction-forgery. No `sorry` / `admit` / `native_decide` / new `axiom` /
#   new `theorem` appears in any variant or witness.
AXIOM_TESTS = []
