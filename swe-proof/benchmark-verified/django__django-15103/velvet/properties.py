"""properties.py — G-PBT falsification battery for django__django-15103 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed —
both of which the consumer spec view elides, so ``markers.same_spec`` holds and
the ``prove_correct jsonScriptTag`` obligation survives with a byte-identical
statement) and swaps in a candidate implementation; it is checked by the real
verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness must ELABORATE against the rival and FAIL
against the frozen solution).

DEFENDED SURFACE (one contracted method over two per-code-point string inputs):

  jsonScriptTag (identifier : List Char) (content : List Char)
      return (out : List Char)
    ensures identifier = [] → out = wrapNoId content       -- ABSENT clause (Q1)
    ensures identifier ≠ [] → out = wrapWithId identifier content  -- PRESENT clause (Q2)

with the two arms spelled out as TRANSPARENT ``def``s over the inputs (directive
8), NOT an opaque answer key:

  wrapNoId content            = openPlain ++ content ++ scriptClose
  wrapWithId identifier c     = openWithId identifier ++ c ++ scriptClose
  openPlain                   = "<script type=\\"application/json\\">".toList
  openWithId identifier       = "<script id=\\"".toList ++ identifier
                                  ++ "\\" type=\\"application/json\\">".toList

So each clause reduces to an ordered concatenation of the method inputs and the
fixed markup fragments — ``decide`` computes it and no rival can "echo an oracle";
the only way to satisfy a clause is to build the exact wrapping.

WHAT THE SPEC DEFENDS. The whole modeled change is: an ABSENT identifier (the
empty ``[]`` case) must produce the BARE element with NO ``id`` attribute
(``wrapNoId``), while a PRESENT (non-empty) identifier must carry it in an ``id``
attribute (``wrapWithId``). Q1 pins the absent arm, Q2 the present arm; the two
together pin the output on the WHOLE domain in both directions.

BINDER STRUCTURE (read before judging binder coverage). The postcondition
depends on BOTH inputs — ``identifier`` and ``content``:

  * ``identifier`` selects the arm (``= []`` vs ``≠ []``) AND is spliced into the
    ``id`` attribute on the present arm. The absent/present rivals are refuted at
    ``identifier = []`` and at a non-empty identifier respectively, so this binder
    is varied across its length-zero point and a non-empty value.
  * ``content`` is the payload spliced into BOTH arms. A rival that drops it from
    the wrapping is caught by the whole-string equality; that rival is what VARIES
    and DISCRIMINATES the ``content`` binder (the spec value depends on it).

ADVERSARIAL READ of the nagini classes on this carrier:
  * FRAME / PERMISSION-MUTATION — VACUOUS. The nagini sibling carries TWO
    MANDATORY rivals (write into ``payload`` / into ``element_id``, each held at a
    fractional heap permission ``Acc(.,1/2)`` a store can illegally overwrite).
    Lean/Velvet are referentially transparent: both inputs are immutable values,
    this bundle declares NO ``mut`` binder, and there is no heap and no aliasing —
    so there is no read-only input to overwrite and no substitute probe to build.
    Not fabricated (porting map: this class is vacuous here), and DEMONSTRATED
    rather than asserted: an impl-region variant that stores into either input
    (``identifier := identifier`` / ``content := []``) does not even parse as a
    program on this carrier — the elaborator refuses it with "`identifier` cannot
    be mutated, only variables declared using `let mut` can be mutated" (measured,
    exit 1 on both). So such a variant is a TOOLING rejection, not a spec
    refutation: it could never carry a witness attributable to the ``ensures``
    clauses, which is precisely why the class has no counterpart here.
  * ADMISSIBILITY (nagini's F2P-shaped self-call proving the precondition) —
    PORTED, as ``admiss-absent-arm-live``. This bundle declares no ``require``
    clause, but "no precondition" is NOT a reason to drop the lane: the analogue
    on a total carrier is the obligation being UNSATISFIABLE (or degenerate) at
    exactly the input shape the failing tests exercise. The positive discharges,
    by evaluation and inside the impl region, that at the absent-identifier point
    the two arms are genuinely DIFFERENT elements (and that the absent arm is the
    strictly shorter one, so the id-carrying segment is really absent from it)
    BEFORE closing the frozen obligation verbatim. That is a live claim, not a
    trivial ``wrap… = wrap…``: flipping its first conjunct to an equality makes
    the same file FAIL (measured, exit 1, "Tactic `decide` proved that the
    proposition … is false"), so the assert is load-bearing.
  * VACUOUS-NON-TERMINATION (nagini's ``vac-nonterm`` under ``MustTerminate(2)``) -
    NOT SHIPPABLE as a reject case, and CLOSED BY THE SEMANTICS rather than a hole.
    Three earlier statements of the reason were wrong; all three are corrected here
    from real builds, and the third is the one this revision withdraws.

    (i) The earliest revisions said this bundle sets
    ``loom.semantics.termination "partial"`` and dismissed the class by citing a
    corpus-wide ``partial``-semantics hole in an internal findings doc. The frozen
    ``Solution.lean`` sets ``"total"``, and its only correctness ``open`` is
    ``open TotalCorrectness DemonicChoice``. The two cannot disagree, because the
    ``set_option`` elaborator itself runs ``openScope `TotalCorrectness``
    (``Loom/MonadAlgebras/WP/Options.lean:169-186``). The cited cohort also no longer
    exists: all 500 velvet bundles set ``"total"``.

    (ii) Under ``"total"`` a postcondition is claimed of ALL runs, not only
    terminating ones, and the verifier demands a decreasing measure on every loop. A
    spinning prefix with NO loop annotation block (``while True do / pure ()``, the
    shape the corpus-wide divergence probe splices) is REJECTED - ``error: Decreasing
    annotations are required in total correctness semantics`` (measured, exit 1).
    That much the previous revision had right, including why it cannot be CARRIED as
    an ``expect="reject"`` case: the error makes the whole FILE uncompilable, so the
    witness build against the rival fails too (even ``example : True := trivial``
    appended to the stripped rival exits 1, measured), and the gate would record
    ``witness-unproven`` - an inconclusive outcome, i.e. a battery FAILURE - for a
    rival that is in fact rejected. Not shippable, and not for want of trying.

    (iii) The previous revision then claimed that the SAME spinning loop written in
    the carrier's real loop syntax with an explicit vacuous measure -

              let mut n : Nat := 0
              while true
                -- invariants-start
                decreasing none
                -- invariants-end
              do
                n := n + 1

    - is ACCEPTED, that spliced ahead of ``return []`` it VERIFIES at exit 0, and
    that this is a hole in the FROZEN spec which "plausibly reaches every ``total``
    bundle with a splice point". THAT IS FALSE, and it is the claim being retracted.
    Re-measured on this cell, that exact shape spliced at the impl-start anchor with
    the proof reduced to a bare ``loom_solve``: exit 1, ``unsolved goals``, and the
    failure is on the MEASURE's own case - ``case «decreasing_1: none»`` with the
    residual goal ``⊢ n + 1 < n``. So ``decreasing none`` does NOT discharge the
    obligation without supplying a measure; it names a measure and then owes the
    descent, exactly as any other expression does. Under ``TotalCorrectness`` the
    loop rule takes ``measure : β -> Nat`` and emits
    ``⌜with_name_prefix `decreasing (measure b' < measure b)⌝``
    (``Loom/MonadAlgebras/NonDetT/Basic.lean:544``); it is the ``PartialCorrectness``
    twin that takes an ``Option ℕ`` and DISCARDS it, and this file does not open that
    namespace. Nothing is escalated, no ``Solution.lean`` edit is owed, and the
    speculation that the hole reaches other ``total`` bundles is withdrawn rather
    than left on file: the same measure-carrying shape was rebuilt on further cells
    in this corpus and is rejected on its own descent goal there too.
    an EMPTY token as present, distinct from ``None``) — COLLAPSED on this carrier.
    mapping.md §2 maps BOTH a falsy ``None`` and an empty ``""`` element_id to the
    SAME Lean value ``identifier = []``; there is no residual empty-vs-None
    distinction for a rival to abuse, so this nagini case has no counterpart here.
  * FULL BRANCH INVERSION (nagini's ``weak-swap-branches``) — PORTED, as
    ``weak-swap-arms``. The port originally dropped it as "subsumed by the union
    of the two single-branch rivals", on the argument that no single input
    isolates it. That argument does not survive contact with the carrier: an
    inversion IS refutable at a single input, and its witness at a fresh present
    identifier was built and confirmed to discriminate (elaborates against the
    inversion, refuted against the frozen solution). "Behaviourally a union of
    two other rivals' failures" is not a reason to drop a rival — a wrong impl
    the battery does not contain is a rival the battery does not test — so it is
    landed rather than argued away, at a FOURTH distinct input point.
  * UNGROUNDED-ORACLE ECHO — N/A: both arms are transparent ``def``s over the
    method inputs, not an axiomatized oracle; the ``axioms`` region is empty.
  * AXIOM lane (nagini's 2 A-reference soundness/containment probes) — DROPPED.
    The axiom lane is G-AX's job (meta.json sets ``G-AX = skip`` for this bundle);
    this gate ignores ``AXIOM_TESTS`` regardless.

WITNESS MECHANICS. The spec is a ``method`` CONTRACT, not a bare predicate, so a
witness reaches it through Velvet's own tester machinery:
``jsonScriptTagTester identifier content = false`` says the extracted program's
result violates the postcondition at that concrete input. It is checked in a file
whose ``prove_correct`` block has been stripped (so no tactic script can mask the
verdict) and there are no ``require`` clauses, so every input reaches the
postcondition. ``List Char`` literals via ``"…".toList`` are fully concrete, so
``decide`` settles the whole equality — no opaque term, no conditioning, no head
binders (hence no consistency obligation). Every witness below was confirmed
out-of-band with two real builds: it ELABORATES against its rival (exit 0) and
FAILS against the frozen solution (exit nonzero).
"""
from pathlib import Path

INSTANCE = "django__django-15103"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchor. The COMPLETE branch body of the method; lies wholly
# ---- inside the single `-- impl-start`/`-- impl-end` region and is unique in
# ---- Solution.lean (both facts asserted at load by _swap). Anchoring on the
# ---- whole body keeps every surgery inside the elided region — the frozen spec
# ---- (the `method` header, both `ensures`, and the `pure` region spelling the
# ---- markup fragments) is never touched. ----
_IMPL = (
    "    if identifier = [] then\n"
    "      return wrapNoId content\n"
    "    else\n"
    "      return wrapWithId identifier content"
)


def _with_impl(new_impl: str) -> str:
    """Solution.lean with ONLY the impl body replaced (spec view untouched)."""
    return _swap(_BASE, _IMPL, new_impl)


# ---- proof anchor. The frozen tactic body, which the consumer spec view also
# ---- elides. Rivals leave it alone (a wrong impl must leave the obligation
# ---- unclosed); a case that adds an in-region `assert` retunes it only enough
# ---- to discharge that extra goal. ----
_PROOF = "prove_correct jsonScriptTag by\n  loom_solve"


def _with_impl_reproved(new_impl: str, new_proof: str) -> str:
    """Impl body replaced AND the elided tactic body retuned."""
    return _swap(_with_impl(new_impl), _PROOF, new_proof)


# ---- witness preamble: reach the contract through Velvet's tester machinery.
# ---- Appended to a file whose `prove_correct` block is stripped, so the tester
# ---- is the sole judge; the `_for` directives declare `jsonScriptTagTester` in
# ---- BOTH the rival and the gold build, so the witness is stated over shared
# ---- vocabulary. ----
_TESTER = (
    "extract_program_for jsonScriptTag\n"
    "prove_precondition_decidable_for jsonScriptTag\n"
    "prove_postcondition_decidable_for jsonScriptTag\n"
    "derive_tester_for jsonScriptTag\n\n"
)


def _witness(call: str) -> str:
    return _TESTER + f"example : {call} = false := by\n  decide\n"


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify, else SPEC-TOO-STRONG. Both keep the frozen
    # `prove_correct jsonScriptTag by loom_solve` script (loom_solve discharges
    # each reshaped-but-equivalent skeleton). Both verified out-of-band with a
    # real build.
    # =====================================================================
    {
        "id": "pos-branch-reorder",
        "kind": "soundness",
        "expect": "verify",
        # The branch decision is REORDERED so the PRESENT arm is tested first
        # (`if identifier ≠ [] then <wrapWithId> else <wrapNoId>`). Semantically
        # identical, different source. Ports the nagini branch-reorder positive.
        "module": _with_impl(
            "    if identifier ≠ [] then\n"
            "      return wrapWithId identifier content\n"
            "    else\n"
            "      return wrapNoId content"),
        "rationale": "structurally-different (the present arm tested first, "
                     "`if identifier ≠ [] then <wrapWithId> else <wrapNoId>`) but "
                     "semantically identical impl must verify against both `ensures` "
                     "clauses (the present entry condition holds by negation of the "
                     "reordered absent guard). If it fails to verify, the spec is "
                     "over-fit to one branch order => SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-let-ladder",
        "kind": "soundness",
        "expect": "verify",
        # The two arms are selected by a single let-bound conditional expression
        # and returned once, rather than by two `return`s. Semantically identical,
        # different source shape.
        "module": _with_impl(
            "    let out := if identifier = [] then wrapNoId content "
            "else wrapWithId identifier content\n"
            "    return out"),
        "rationale": "structurally-different (arm selection folded into one "
                     "let-bound `if … then … else …` expression, single `return`) "
                     "but semantically identical impl must verify against both "
                     "`ensures` clauses. A faithful reshape that could NOT verify "
                     "would mean the postcondition is over-fit to the two-`return` "
                     "FORM => SPEC-TOO-STRONG.",
    },

    # =====================================================================
    # ADMISSIBILITY — the analogue of the sibling's F2P-shaped precondition probe
    # on a carrier with no `require` clause: the residual risk is not that an
    # input is excluded, but that the obligation is DEGENERATE at exactly the
    # input shape the failing tests exercise (the absent-identifier point), i.e.
    # that both arms coincide there and the clause therefore forces nothing. One
    # in-region `assert`, discharged BY EVALUATION at that concrete point, pins
    # the opposite before the frozen obligation is closed verbatim below it. The
    # assert is live: flipping its first conjunct to an equality makes the same
    # file fail (measured out-of-band).
    # =====================================================================
    {
        "id": "admiss-absent-arm-live",
        "kind": "admissibility",
        "expect": "verify",
        "module": _with_impl_reproved(
            '    assert (with_name_prefix `admiss\n'
            '      (wrapNoId "D".toList ≠ wrapWithId [] "D".toList\n'
            '       ∧ (wrapNoId "D".toList).length < (wrapWithId [] "D".toList).length\n'
            '       ∧ wrapWithId "T".toList "D".toList ≠ wrapNoId "D".toList\n'
            '       ∧ (wrapNoId "D".toList).length > 1))\n'
            + _IMPL,
            "prove_correct jsonScriptTag by\n  loom_solve\n  all_goals decide"),
        "rationale": "ADMISSIBILITY on a carrier with no `require`: the obligation "
                     "must not be DEGENERATE at the absent-identifier point (an "
                     "empty identifier with a non-empty payload — the input shape "
                     "the newly-passing behaviour is about). The in-region assert "
                     "discharges, by evaluation at that concrete point, that (a) the "
                     "absent arm and the id-carrying arm are DIFFERENT elements "
                     "there, (b) the absent arm is STRICTLY SHORTER, so the "
                     "id-carrying attribute segment is genuinely absent from it and "
                     "not merely reordered, (c) a non-empty identifier's arm also "
                     "differs from the absent arm, and (d) the absent arm is not the "
                     "degenerate empty sequence. Then the frozen obligation is closed "
                     "with the impl VERBATIM, so the method's own `ensures` still "
                     "discharge. If this FAILED the obligation would be unsatisfiable "
                     "or vacuous at exactly the discriminating input => "
                     "PRECOND-TOO-STRONG / degenerate clause.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each a loop-free closed form with a machine-checked
    # refutation witness at a concrete input (ELABORATES against the rival, FAILS
    # against gold — both halves confirmed out-of-band with real builds) and the
    # refinement argument for why its faithful real counterpart would NOT resolve.
    # =====================================================================

    # ---- ABSENT clause (Q1): the modeled bug — always emit the id-bearing tag ----
    {
        "id": "weak-absent-emits-id",
        "kind": "uniqueness",
        "expect": "reject",
        # THE modeled bug (the pre-patch behaviour): the identifier is treated as
        # mandatory, so the result ALWAYS carries the `id` attribute — even for an
        # ABSENT (empty) identifier, where the spec demands the bare element.
        # Correct on the present arm, wrong on every absent input.
        "module": _with_impl("    return wrapWithId identifier content"),
        "refinement": "this is exactly the pre-patch behaviour: the no-id case still "
                      "emits the id-bearing tag with an empty id value "
                      "('<script id=\"\" type=\"application/json\">…</script>'). Its "
                      "faithful real counterpart is the UNCHANGED repo (always the "
                      "id-bearing template), which on the F2P no-id call renders "
                      "'<script id=\"\" …>' — not the bare element the F2P tests "
                      "assert. Does NOT resolve — the exact change the spec senses "
                      "(G-DIFF).",
        "rationale": "REJECT from the ABSENT clause (Q1: identifier = [] → "
                     "out = wrapNoId content): on an empty identifier the rival "
                     "returns wrapWithId [] content (still carries the ' id=\"\"' "
                     "segment) while wrapNoId content omits it, so the wrappings "
                     "differ. Correct on the present arm, wrong on the absent arm "
                     "(partial-domain). Refuted at identifier = [] (the length-zero "
                     "point) with non-empty content.",
        "witness": _witness('jsonScriptTagTester [] "K".toList'),
    },

    # ---- PRESENT clause (Q2): always emit the bare tag, dropping the id ----
    {
        "id": "weak-present-drops-id",
        "kind": "uniqueness",
        "expect": "reject",
        # The dual failure: always emit the BARE element, so a PRESENT identifier's
        # `id` attribute is dropped. Correct on the absent arm, wrong on every
        # present input.
        "module": _with_impl("    return wrapNoId content"),
        "refinement": "always emitting the bare element drops the identifier from a "
                      "present-id call. Its faithful real counterpart renders "
                      "'<script type=\"application/json\">…</script>' even when an "
                      "id was supplied, so the P2P test that calls the routine with "
                      "'test_id' and asserts '<script id=\"test_id\" …>' still fails "
                      "— it would NOT resolve.",
        "rationale": "REJECT from the PRESENT clause (Q2: identifier ≠ [] → "
                     "out = wrapWithId identifier content): on a non-empty identifier "
                     "the rival returns wrapNoId content (no id attribute) while "
                     "wrapWithId identifier content carries '<script id=\"…\" …>', so "
                     "the wrappings differ. Correct on the absent arm, wrong on the "
                     "present arm (partial-domain). Refuted at a non-empty identifier "
                     "— the witness that VARIES the identifier binder off its "
                     "length-zero point.",
        "witness": _witness('jsonScriptTagTester "id".toList "V".toList'),
    },

    # ---- content binder / whole-string placement: drop the payload ----
    {
        "id": "weak-drop-content",
        "kind": "uniqueness",
        "expect": "reject",
        # Whole-string / placement attack: omit the payload `content` from the
        # wrapping on BOTH arms, keeping the arm selection correct. Independent of
        # the identifier, so refutable on the present arm; this is what VARIES and
        # DISCRIMINATES the `content` binder.
        "module": _with_impl(
            "    if identifier = [] then\n"
            "      return wrapNoId []\n"
            "    else\n"
            "      return wrapWithId identifier []"),
        "refinement": "drops the encoded payload from the wrapping. Its faithful real "
                      "counterpart renders '<script …></script>' with EMPTY content — "
                      "a different element — so every test that reads back the "
                      "JSON-encoded payload (e.g. the F2P '<script …>{\"key\": "
                      "\"value\"}</script>' assertion) still fails; it would NOT "
                      "resolve.",
        "rationale": "REJECT from both `ensures` clauses, which place `content` "
                     "between the opening tag and scriptClose (wrapNoId content / "
                     "wrapWithId identifier content). The rival splices [] in place "
                     "of content, so the wrappings differ whenever content is "
                     "non-empty. Refuted at a non-empty content — the witness that "
                     "VARIES and DISCRIMINATES the `content` binder (a rival that "
                     "mishandled only content would otherwise slip through).",
        "witness": _witness('jsonScriptTagTester "z".toList "P".toList'),
    },

    # ---- both clauses at once: the arms are exchanged ----
    {
        "id": "weak-swap-arms",
        "kind": "uniqueness",
        "expect": "reject",
        # The two arms are EXCHANGED: an absent identifier gets the id-carrying
        # element and a present one gets the bare element. Ports the sibling's
        # full-inversion rival. Wrong on the WHOLE domain (both clauses), and — the
        # point the port's "subsumed" argument got wrong — refutable at a single
        # input, so it carries its own discriminating witness at a FOURTH input
        # point that no other rival probes.
        "module": _with_impl(
            "    if identifier = [] then\n"
            "      return wrapWithId identifier content\n"
            "    else\n"
            "      return wrapNoId content"),
        "refinement": "exchanging the two arms is the exact opposite selection: every "
                      "call that supplies an identifier renders the bare element "
                      "(dropping the identifier the P2P assertion reads back) and every "
                      "call that supplies none renders the id-carrying element with an "
                      "empty id value. Its faithful real counterpart fails BOTH the "
                      "newly-asserted no-identifier behaviour and the pre-existing "
                      "with-identifier behaviour, so it would NOT resolve.",
        "rationale": "REJECT from BOTH `ensures` clauses at once. On identifier = [] "
                     "the rival returns wrapWithId [] content where Q1 demands "
                     "wrapNoId content; on a non-empty identifier it returns "
                     "wrapNoId content where Q2 demands wrapWithId identifier content. "
                     "Refuted at a non-empty identifier with non-empty content — a "
                     "distinct input tuple from all three rivals above, so it adds a "
                     "fourth refutation point rather than restating one.",
        "witness": _witness('jsonScriptTagTester "q".toList "J".toList'),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 8 SPEC cases (1 soundness
# positive, 1 admissibility, 2 frame-mutation rivals, 4 uniqueness rivals —
# weak-absent-emits-id, weak-present-on-empty, vac-nonterm, weak-swap-branches)
# plus a 2-case AXIOM lane. This bundle models the SAME purely-functional core —
# the optional-id `<script …>` wrapping — over the SAME carrier shape
# (`List Char`, a straight branch on emptiness), so the value-level cases port;
# the permission/precondition/termination classes are vacuous on a
# referentially-transparent carrier, and one nagini rival collapses on this carrier.
#
#   sibling case                 -> here                      disposition
#   ---------------------------------------------------------------------------
#   pos-branch-reorder           -> pos-branch-reorder         PORTED
#   admiss-shape                 -> admiss-absent-arm-live     PORTED (re-derived)
#   (no sibling; second shape)   -> pos-let-ladder             ADDED (2nd positive)
#   frame-mut-payload            -> (none)                     VACUOUS (demonstrated)
#   frame-mut-element_id         -> (none)                     VACUOUS (demonstrated)
#   weak-absent-emits-id         -> weak-absent-emits-id       PORTED (the bug, Q1)
#   (no sibling; Q2 clause)      -> weak-present-drops-id      ADDED (attacks Q2)
#   weak-present-on-empty        -> (none)                     COLLAPSED on carrier
#   vac-nonterm                  -> (none)                     N/A (no loop; partial)
#   weak-swap-branches           -> weak-swap-arms             PORTED (both clauses)
#   (no sibling; content binder) -> weak-drop-content          ADDED (binder coverage)
#   AXIOM_TESTS (2)              -> (none)                     DROPPED (G-AX lane)
#
# 4 ported, 3 added, 3 vacuous/N-A/collapsed, 2 axiom dropped
#   = 7 SPEC cases (2 soundness, 1 admissibility, 4 uniqueness).
#
# PORTED (pos-branch-reorder): the sibling tests the ABSENT predicate first with an
#   explicit guard, then the present block; here the analogous reshape tests the
#   PRESENT predicate first (`if identifier ≠ [] then <wrapWithId> else <wrapNoId>`),
#   keeping both `ensures` clauses satisfied by construction. Verified to build under
#   the frozen `loom_solve` proof.
# ADDED (pos-let-ladder): a second structurally-different correct impl (arm selection
#   folded into one let-bound conditional, single `return`) so the obligation is
#   defended from two shapes, not one. Verified to build.
# PORTED (weak-absent-emits-id): the sibling's pre-patch rival (the no-id case still
#   emits the id-bearing empty-id tag) re-expresses directly onto Q1. It is the
#   modeled bug (Solution_prepatch.lean is exactly this impl). Refuted at
#   identifier = [].
# ADDED (weak-present-drops-id): the sibling has no standalone Q2 attack (its present
#   arm is attacked only via the full inversion weak-swap-branches). Here Q2 is a
#   separate top-level `ensures`, so a dedicated rival that drops the id on a present
#   identifier attacks Q2 cleanly and, crucially, VARIES the identifier binder off its
#   length-zero point (the absent rival pins it at []). Refuted at a non-empty id.
# ADDED (weak-drop-content): the sibling pins the whole output sequence, so the
#   placement of the payload was covered implicitly; here it is made an explicit rival
#   so the `content` binder is attacked and DISCRIMINATED (a rival mishandling only the
#   payload would otherwise slip through the two arm-selection rivals). Refuted at a
#   non-empty content.
# PORTED (admiss-absent-arm-live): "no `require` clause" is not a reason to drop the
#   admissibility lane — the analogue on a total carrier is the obligation being
#   unsatisfiable or DEGENERATE at the input shape the newly-asserted behaviour is
#   about. This positive discharges, by evaluation at that concrete absent-identifier
#   point and inside the elided impl region, that the two arms are genuinely different
#   elements there, that the absent arm is strictly shorter (the attribute segment is
#   really gone, not reordered), and that neither side is the degenerate empty
#   sequence — then closes the frozen obligation with the impl VERBATIM. Confirmed
#   live: the same file with that first conjunct flipped to an equality FAILS.
# VACUOUS (frame-mut-payload / frame-mut-element_id): this backend is referentially
#   transparent, declares no `mut` binder, and has no heap. Demonstrated, not merely
#   asserted: an impl-region variant that stores into either input is refused by the
#   ELABORATOR ("cannot be mutated, only variables declared using `let mut` can be
#   mutated"), so it is a tooling rejection with no witness attributable to the
#   `ensures` clauses — the class genuinely has no counterpart here.
# PORTED (weak-swap-arms): the sibling's full inversion. Landed rather than argued
#   away as "subsumed": an inversion IS refutable at a single input (a non-empty
#   identifier with non-empty content), its witness discriminates, and a wrong impl the
#   battery does not contain is one the battery does not test.
# COLLAPSED (weak-present-on-empty): the sibling misclassifies an EMPTY token as
#   present, distinct from None. mapping.md §2 maps BOTH None and empty "" to the same
#   Lean value `identifier = []`, so there is no residual empty-vs-None distinction for
#   a rival to abuse — this nagini case has no counterpart on this carrier.
# SPEC-CLOSED (vac-nonterm): the sibling exploits the MustTerminate(2) obligation
#   with a spinning `while` loop. On this bundle the class is closed by the
#   semantics, and the previous revision of this note recorded the opposite. It said
#   the annotation-free shape (`while True do / pure ()`) is rejected but unshippable,
#   which is right and still stands: the error makes the file uncompilable, so no
#   witness can elaborate against the rival (`True := trivial` also exits 1) and the
#   gate would score it `witness-unproven`. It then said the same loop written in the
#   real loop syntax with `decreasing none` and `return []` VERIFIES at exit 0, and
#   escalated that as a genuine FROZEN-SPEC hole in this audit's spec_holes. That is
#   FALSE and is retracted: re-measured, that shape exits 1 with `unsolved goals`,
#   failing on the measure's own case -- `case «decreasing_1: none»`, residual
#   `n + 1 < n`. `decreasing none` names a measure and then owes the descent like any
#   other expression; under TotalCorrectness the loop rule takes `measure : β -> Nat`
#   and emits `(measure b' < measure b)` (Loom/MonadAlgebras/NonDetT/Basic.lean:544),
#   while it is the PartialCorrectness twin that takes an `Option` and discards it --
#   and this file opens only TotalCorrectness. Disposition: CLOSED BY THE SEMANTICS,
#   no spec_holes entry, no frozen edit owed.
# BINDER / CLAUSE COVERAGE. The obligation has two input binders — `identifier` and
#   `content` — and two independent top-level clauses (Q1 absent, Q2 present). Q1 is
#   attacked by weak-absent-emits-id, Q2 by weak-present-drops-id, BOTH at once by
#   weak-swap-arms; both positives defend both clauses and the admissibility case pins
#   the absent arm as non-degenerate. The four reject witnesses probe FOUR DISTINCT
#   input tuples: ([], "K") [absent, identifier length 0], ("id", "V") [present
#   identifier], ("z", "P") [present identifier, payload dropped], ("q", "J") [present
#   identifier, arms exchanged]. Across them `identifier` takes {[], "id", "z", "q"}
#   (varied over its length-zero point AND three distinct non-empty values, including
#   two of different length) and `content` takes {"K", "V", "P", "J"} (varied and
#   DISCRIMINATED by weak-drop-content — the spec value provably depends on it). No two
#   rivals are refuted at the same input. pts = 4 distinct input points across 4
#   witnesses.
# ADVERSARIAL PROBES RUN AND SURVIVED (SPEC-TOO-WEAK / SPEC-TOO-STRONG, real builds).
#   Re-measured from scratch by the independent audit; every exit code below was
#   observed, not inferred.
#   SPEC-TOO-WEAK (6 wrong impls beyond the four rivals, all REJECTED exit 1, each
#   with an `unsolved goals` naming the clause it violates and showing the residual
#   equation):
#     - arguments to the id-carrying arm exchanged  (wrapWithId content identifier)
#     - payload placed AFTER the closing fragment on both arms
#     - identifier appended into the element BODY instead of carried as an attribute
#     - arm selected on `content = []` instead of identifier emptiness
#     - boundary off-by-one: `identifier.length <= 1` routed to the absent arm
#     - id attribute emitted but the identifier TRUNCATED to its head character
#   So the spec has no slack on argument order, payload placement, attribute-vs-body
#   position, WHICH binder selects the arm, the length-0/1 boundary, or identifier
#   completeness.
#   SPEC-TOO-STRONG (4 correct reshapes, all VERIFY exit 0): a `match` on the
#   identifier's shape; an `.isEmpty` guard; a negated guard with the arms in the
#   other order; and the arm bodies written out as explicit concatenations. The last
#   needs the frozen tactic body extended by one `simp_all` over the markup `def`s
#   (which the spec view elides) — confirmed load-bearing: under the frozen
#   `loom_solve` alone that reshape fails with `unsolved goals` (measured). So the
#   spec is not over-fit to the frozen form.
#   Vacuous non-termination via `decreasing none` was recorded here as the one class
#   that does not survive; it does survive. See the SPEC-CLOSED note above: that
#   shape is rejected on its own descent goal (`n + 1 < n`), so there is no
#   frozen-spec defect and nothing is escalated.
# WITNESS DISCRIMINATION (verified during authoring with two real builds per reject
#   case): each witness ELABORATES against its rival (`jsonScriptTagTester … = false`
#   is provable — the extracted program violates the postcondition at the probed input)
#   and FAILS against the frozen solution (gold satisfies the spec there, so the tester
#   is true and `= false` is unprovable). No witness binds a hypothesis (the carrier is
#   fully transparent), so there is no joint-satisfiability obligation. No
#   `sorry`/`admit`/`native_decide`/`axiom` appears.
AXIOM_TESTS = []
