"""properties.py — G-PBT falsification battery for django__django-11276 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the elided ``prove_correct`` tactic body, is
changed — both regions the consumer spec view elides, so ``markers.same_spec``
holds and the ``prove_correct escapeCodepoints`` obligation survives with a
byte-identical statement) and swaps in a candidate implementation; it is checked
by the real verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness must elaborate against the rival and FAIL
against the frozen solution).

DEFENDED SURFACE (one contracted method):

  escapeCodepoints (text : List Char) return (out : List Char)
    ensures out = escapedSeq text                       -- the WHOLE pin (C1)
    ensures entityDecode (entity '&')  = ['&']          -- round-trip const (C2)
    ensures entityDecode (entity '<')  = ['<']          --      "         (C3)
    ensures entityDecode (entity '>')  = ['>']          --      "         (C4)
    ensures entityDecode (entity '"')  = ['"']          --      "         (C5)
    ensures entityDecode (entity '\'') = ['\'']         --      "         (C6)

The method escapes a code-point sequence: each of the five significant chars
expands to its entity sequence, every other char passes through. The escape of
one code point is the pure ``def entity``; the escape of a whole sequence is the
pure front-recursive fold ``escapedSeq`` (``escapedSeq (c :: cs) = entity c ++
escapedSeq cs``). Both are TRANSPARENT ``def``s over the method's own input —
there is NO opaque answer-key oracle in the load-bearing clause, so pinning
``out = escapedSeq text`` is grounded, not an echo.

WHICH CLAUSE CONSTRAINS THE IMPL. C1 (``out = escapedSeq text``) is the only
impl-constraining clause: it is a function of ``text`` and every escaping
decision (which byte sequence each significant char maps to, and that every
other char passes through) is pinned by it, at every position. C2–C6 are
CONSTANTS — they mention neither ``text`` nor ``out``; they are round-trip facts
about the opaque ``entityDecode`` on the five fixed entity tokens, so they do not
constrain the implementation at all. Every uniqueness rival therefore targets C1.

ADVERSARIAL READ of the nagini classes on THIS carrier:
  * FRAME/PERMISSION-MUTATION — VACUOUS. The nagini sibling's mandatory
    ``frame-mutate-text`` rival writes through a read-only (``Acc(.,1/2)``)
    reference to ``text`` and is rejected for INSUFFICIENT PERMISSION. Lean and
    Velvet are referentially transparent: ``text`` is an immutable value, this
    bundle declares no ``mut`` parameter, and there is no heap, aliasing, or
    permission system to subvert. There is no read-only input to overwrite, so
    the class is vacuous. No substitute probe is fabricated (see footer).
  * UNGROUNDED-ORACLE ECHO — N/A as an attack. The post-image C1 is
    ``escapedSeq text``, a transparent fold over the method's own argument; there
    is no answer key to echo. The honest cheapest CORRECT impl (``return
    escapedSeq text``) is carried as a POSITIVE control instead — it doubles as
    proof the spec is not echo-vulnerable, since any WRONG per-char map fails
    ``out = escapedSeq text``.
  * PARTIAL-DOMAIN / VALUE — the whole reject surface, all against C1. A rival
    can escape every significant char correctly except one (drop the escape of a
    single significant char), or mis-escape one char only in a sub-domain (the
    apostrophe when it is the FIRST code point — the leading-vs-interior split).
  * DIVERGENCE - the class is CLOSED BY THE SEMANTICS here, and a diverging
    rival is REJECTED rather than admitted. This bundle sets
    ``loom.semantics.termination "total"`` AND carries
    ``open TotalCorrectness``, and the ``open`` is the line that actually
    selects the semantics: both namespaces define
    ``WPGen.forWithInvariantLoop``, the later ``open`` wins, and the
    ``PartialCorrectness`` version takes a loop measure and DISCARDS it. So the
    two lines have to move together, and they do here. Under the total scope a
    postcondition is claimed of ALL runs, not only of terminating ones, and the
    verifier emits a descent obligation ``measure b' < measure b`` for every
    loop in the impl (1 loop here, measure ``i``). A rival that loops without a
    measure is refused outright (``Decreasing annotations are required in total
    correctness semantics``), and a rival that supplies a CONSTANT measure to
    dodge that is refused on the measure's own goal (``case «decreasing_1:
    spin» ... ⊢ spin < spin``), re-measured on this bundle with a real build.
    Divergence therefore does not discharge the ``ensures`` clauses vacuously.
    It is still not shipped as a G-PBT reject case, and the reason is the
    witness contract rather than a spec weakness. A reject case must carry a
    witness that ELABORATES against the rival, and the rival's module does not
    compile at all: the descent obligation fails at the ``method`` itself,
    ahead of any appended tester. Measured through the gate's own
    ``_check_witness``, even ``example : True := trivial`` comes back
    ``witness-unproven`` on this rival, which is an INCONCLUSIVE outcome and
    would fail the whole battery rather than pass a case. That is the right
    behavior: a diverging impl has no output at any input, so there is no value
    for a witness to disagree with, and its rejection is a judgement of the
    termination obligation rather than a postcondition violation at a point.
    Recorded as REJECTED-BY-SPEC and not expressible as a witnessed case, which
    is neither a spec hole nor a battery gap.

WITNESS MECHANICS ON THIS BUNDLE. The sibling django bundles reach a contract
whose postcondition is decidable via the tester machinery
(``derive_tester_for`` → ``<name>Tester args = false := by decide``). THAT PATH
IS DEAD HERE: the round-trip clauses C2–C6 mention the opaque axiom
``entityDecode``, so ``prove_postcondition_decidable_for escapeCodepoints``
yields a ``Decidable`` instance that depends on ``entityDecode`` and has no
executable code — ``derive_tester_for`` emits ``escapeCodepointsTester`` as
noncomputable and ``decide`` gets stuck (measured: both a wrong rival and gold
fail the tester build identically, discriminating nothing).

But C1's carrier IS transparent. Each rival is written LOOP-FREE (a
``text.flatMap`` per-char map, or a ``match`` on the head), so its extracted
program ``escapeCodepointsExec`` — ``NonDetT``-run of the impl — REDUCES fully
under ``decide`` at a concrete input. Each witness states, at one concrete input,

    (match escapeCodepointsExec <input> with | DivM.res r => r | _ => [])
        ≠ escapedSeq <input>

i.e. the rival's own output DIFFERS from the transparent post-image C1 demands —
a direct C1 violation the elaborator can see. Against the FROZEN solution the
same statement fails: gold's body is the ``while`` loop, whose ``…Exec`` is
well-founded recursion the kernel does NOT reduce under ``decide`` (it stays
stuck at ``.hasDecEq``), so ``decide`` cannot close the ``≠`` and the witness
FAILS on gold — the discrimination the gate requires. No witness here binds any
hypothesis (every input is a concrete literal that decides C1), so no
consistency probe is needed. No banned token (sorry/admit/native_decide/axiom/
opaque). Each witness was checked out-of-band with ``scripts/lean_verify.sh``:
every one ELABORATES against its rival (exit 0) and FAILS against gold (a
``decide`` error).

HONEST LIMIT OF THE GOLD HALF (recorded by the audit, which re-ran all builds).
The gold-side failure is a STUCK ``decide`` ("reduction got stuck at
``.hasDecEq``"), NOT a semantic refutation of the rival's claim: it says the
kernel could not evaluate gold's well-founded ``…Exec``, not that gold satisfies
C1 at that input. So the gold half of each witness discriminates LOOP-FREE from
LOOPING impls, and only the RIVAL half is a positive semantic statement (the
rival's concrete output ≠ the concrete post-image). What rules out the tautology
reading is a third build the audit ran per witness: the SAME witness against a
CORRECT loop-free impl (``return text.flatMap entity``), where ``decide``
reduces fully and reports the proposition **false** (exit 1, "``decide`` proved
that the proposition … is false"). That is the check that shows each witness
asserts something true of the WRONG impl and false of a right one, rather than
merely true of anything the kernel cannot reduce. Measured for
rival-apos-decimal, rival-drop-quot, rival-drop-amp and rival-mangle-ordinary.

AXIOM lane: dropped. ``AXIOM_TESTS = []``. The nagini file carries axiom-
soundness / containment probes over the real stdlib callees (``html.escape`` /
``html.unescape``); that is G-AX's job (axiom_check.py / mapping.md) and the
G-PBT gate ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "django__django-11276"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchor: the WHOLE frozen impl body (backward `while` fold),
# ---- everything strictly BETWEEN the method's `-- impl-start` / `-- impl-end`.
# ---- Every variant replaces exactly this text, so each edit lies wholly inside
# ---- the one -- impl-start .. -- impl-end region and same_spec holds by
# ---- construction (both facts asserted at load by _swap).
_IMPL = (
    "    let mut result : List Char := []\n"
    "    let mut i := text.length\n"
    "    while i > 0\n"
    "      invariant 0 ≤ i ∧ i ≤ text.length\n"
    "      invariant result = escapedSeq (text.drop i)\n"
    "      done_with i = 0\n"
    "      decreasing i\n"
    "    do\n"
    "      let c := text[i - 1]!\n"
    "      result := entity c ++ result\n"
    "      i := i - 1\n"
    "    return result"
)

assert _BASE.count(_IMPL) == 1, "method impl region drifted from expected text"

# The frozen proof, verbatim. A loop-free reshape may retune THIS block (elided
# from the spec view); loop-keeping variants leave it as-is. Rivals leave it
# as-is too — the rejection is carried by the witness, not the tactic script.
_PROOF = (
    "prove_correct escapeCodepoints by\n"
    "  loom_solve\n"
    "  rw [escapedSeq_drop_step text i (by omega) (by omega)]\n"
    "  simp_all"
)

assert _BASE.count(_PROOF) == 1, "proof region drifted from expected text"


def _impl(new_body):
    """Full Solution.lean variant with ONLY the impl body replaced."""
    return _swap(_BASE, _IMPL, new_body)


def _impl_reproved(new_body, new_proof):
    """Impl body replaced AND the proof retuned (for loop-free correct reshapes,
    whose residual goal no longer needs the backward-fold step lemma)."""
    return _swap(_impl(new_body), _PROOF, new_proof)


# ---- The per-code-point chain written INLINE, in the REVERSE branch order of
# ---- the pure `def entity`. Used by pos-control-reordered: pointwise equal to
# ---- `entity` at every char (so C1 still holds) but not DEFINITIONALLY equal,
# ---- which is what makes the positive a real test of branch-order fit rather
# ---- than a re-spelling.
_REORDERED_CHAIN = (
    "(fun c => if c = '\\'' then \"&#x27;\".toList "
    "else if c = '\"' then \"&quot;\".toList "
    "else if c = '>' then \"&gt;\".toList "
    "else if c = '<' then \"&lt;\".toList "
    "else if c = '&' then \"&amp;\".toList else [c])"
)


# ---- A loop-free rival: escape each char with a custom per-char map. Being
# ---- loop-free (`text.flatMap`), its extracted `…Exec` reduces under `decide`
# ---- so its witness discriminates; gold's `while`-loop `…Exec` stays stuck.
def _flatmap(mapexpr):
    return _impl(f"    return (text.flatMap (fun c => {mapexpr}))")


# ---- witness preamble + builder. The spec's postcondition is NOT decidable
# ---- (C2–C6 mention the opaque `entityDecode`), so the tester+`decide` path is
# ---- dead; instead extract the executable program and refute C1 directly on
# ---- the TRANSPARENT `escapedSeq`. Checked in a file whose `prove_correct`
# ---- block is stripped, so no tactic script can mask the verdict.
_EXTRACT = "extract_program_for escapeCodepoints\n\n"


def _witness(inp):
    return (
        _EXTRACT +
        "example :\n"
        f"    (match escapeCodepointsExec ({inp}) with | DivM.res r => r | _ => [])"
        f" ≠ escapedSeq ({inp}) := by\n"
        "  decide\n"
    )


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify. If a faithful correct impl cannot verify, the spec is
    # SPEC-TOO-STRONG.
    # =====================================================================
    {
        "id": "pos-control-direct",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: report the escape of the whole sequence DIRECTLY via the
        # transparent fold, no per-character loop. C1 is literally
        # `out = escapedSeq text`, so this is the cheapest HONEST correct impl —
        # and, since `escapedSeq text` is GROUNDED in the argument (not an opaque
        # answer key), it doubles as proof the spec is not echo-vulnerable (any
        # WRONG per-char map fails `out = escapedSeq text`). The loop is gone, so
        # the frozen proof's backward-fold step is unneeded and the residual goal
        # closes under `loom_solve` alone.
        "module": _impl_reproved(
            "    return (escapedSeq text)",
            "prove_correct escapeCodepoints by\n  loom_solve"),
        "rationale": (
            "the post-image `escapedSeq text` is GROUNDED in the input (a total "
            "front-recursive fold, no opaque answer key), so `return escapedSeq "
            "text` is the honest cheapest CORRECT impl; C1 is literally `out = "
            "escapedSeq text`, so it MUST verify, else C1 is SPEC-TOO-STRONG. "
            "Ports the nagini echo-attempt-honest control: the cheapest impl "
            "satisfying the grounded pin, showing the spec is not echo-vulnerable "
            "(any wrong per-char map fails `out = escapedSeq text`)."
        ),
    },
    {
        "id": "pos-control-seg-local",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: keep the backward `while` fold but bind the per-code-point
        # entity sequence to a typed local `e` before prepending it. Same value
        # flow (`e = entity c`), different control shape; the frozen proof still
        # closes unchanged (the loop invariant and step lemma are untouched).
        "module": _impl(
            "    let mut result : List Char := []\n"
            "    let mut i := text.length\n"
            "    while i > 0\n"
            "      invariant 0 ≤ i ∧ i ≤ text.length\n"
            "      invariant result = escapedSeq (text.drop i)\n"
            "      done_with i = 0\n"
            "      decreasing i\n"
            "    do\n"
            "      let c := text[i - 1]!\n"
            "      let e := entity c\n"
            "      result := e ++ result\n"
            "      i := i - 1\n"
            "    return result"),
        "rationale": (
            "a correct impl with a DIFFERENT control shape (bind the per-code-"
            "point entity sequence to a typed local before prepending it) must "
            "verify; the value flow is unchanged (`e = entity c`) so C1 still "
            "discharges and the frozen loop proof closes as-is. Ports the nagini "
            "pos-control-seg-local: if it fails => SPEC-TOO-STRONG (over-fit to "
            "the inline-prepend code form)."
        ),
    },

    # =====================================================================
    # ADMISSIBILITY — RE-AIMED from nagini admiss-significant-input. That case
    # established the read-only precondition `Acc(list_pred(.),1/2)` on an
    # F2P-shaped significant-char input. This method carries NO `require` clause
    # (the pre-conditions region is empty), so nothing could exclude a normal
    # input and the classic "a normal input is admitted" probe is vacuous.
    # Re-aimed at the residual admissibility risk on a total domain: that the
    # six-clause post-image is jointly SATISFIABLE by a gold-shaped computation.
    # The frozen impl discharging all six ensures IS that witness. MUST verify,
    # else SPEC-UNSATISFIABLE.
    # =====================================================================
    {
        "id": "pos-control-reordered",
        "kind": "soundness",
        "expect": "verify",
        # ADDED BY AUDIT. The port recorded the nagini pos-control-reordered as
        # having "no impl-region counterpart" because the per-char mapping is the
        # pure `def entity` rather than an inline if/elif chain. That reasoning
        # is wrong: the impl region may write its OWN per-char chain inline, and
        # ordering its branches in the REVERSE order of `entity` (' " > < & else)
        # reproduces exactly the nagini case — a correct impl whose branch order
        # differs from the frozen one. It keeps the frozen backward loop, so the
        # only change is the per-code-point chain; the proof adds the pointwise
        # `pt : ∀ c, <chain> c = entity c` (by cases on the five guards) that the
        # reorder makes non-definitional. Audited: verifies (exit 0).
        "module": _impl_reproved(
            "    let mut result : List Char := []\n"
            "    let mut i := text.length\n"
            "    while i > 0\n"
            "      invariant 0 ≤ i ∧ i ≤ text.length\n"
            "      invariant result = escapedSeq (text.drop i)\n"
            "      done_with i = 0\n"
            "      decreasing i\n"
            "    do\n"
            "      let c := text[i - 1]!\n"
            f"      result := {_REORDERED_CHAIN} c ++ result\n"
            "      i := i - 1\n"
            "    return result",
            "prove_correct escapeCodepoints by\n"
            "  loom_solve\n"
            "  rw [escapedSeq_drop_step text i (by omega) (by omega)]\n"
            f"  have pt : ∀ c : Char, {_REORDERED_CHAIN} c = entity c := by\n"
            "    intro c; simp only [entity]\n"
            "    by_cases h1 : c = '&' <;> by_cases h2 : c = '<' <;>"
            " by_cases h3 : c = '>'\n"
            "      <;> by_cases h4 : c = '\"' <;> by_cases h5 : c = '\\'' <;>"
            " simp_all\n"
            "  simp_all [pt]"),
        "rationale": (
            "a correct impl whose per-code-point branch chain is written INLINE "
            "in the impl region in the REVERSE branch order of `entity` "
            "(apostrophe, double-quote, '>', '<', ampersand, else) must verify; "
            "the mapping is pointwise equal to `entity` at every char, so C1 "
            "still discharges. Ports the nagini pos-control-reordered, which an "
            "earlier pass wrongly recorded as having no impl-region counterpart. "
            "If it failed => SPEC-TOO-STRONG (over-fit to one branch order)."
        ),
    },
    {
        "id": "admiss-gold-total",
        "kind": "admissibility",
        "expect": "verify",
        "module": _BASE,  # frozen impl; same_spec trivially, must verify
        "rationale": (
            "the input carries no `require`, so the escaper is total over every "
            "code-point sequence; the gold impl discharging all six ensures is "
            "the admissibility witness that the post-image (C1 plus the five "
            "round-trip constants) is jointly satisfiable. Near-trivial precisely "
            "because the precondition is empty. Re-aimed from the nagini "
            "admiss-significant-input, whose read-only-precondition half has no "
            "counterpart on this referentially-transparent carrier. Else "
            "SPEC-UNSATISFIABLE."
        ),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # concrete input and the refinement argument that its faithful real
    # counterpart would NOT resolve the F2P. All attack C1 (`out = escapedSeq
    # text`); the input binder `text` is varied across the five significant
    # chars and a two-element input.
    # =====================================================================
    {
        "id": "rival-apos-decimal",
        "kind": "uniqueness",
        "expect": "reject",
        # The exact pre-change behaviour: the apostrophe maps to the legacy
        # decimal reference &#39; at EVERY position instead of the numeric hex
        # reference &#x27;. This is the single behavioural change the F2P observes.
        "module": _flatmap(
            "if c = '\\'' then \"&#39;\".toList else entity c"),
        "refinement": (
            "this is the pre-change escaper: the apostrophe is emitted as the "
            "legacy decimal reference at every position. Its faithful real patch "
            "is the unpatched repo, whose escaper emits the legacy reference for "
            "the apostrophe; the failing test asserts the apostrophe escapes to "
            "the numeric hex reference regardless of position, which the legacy "
            "reference does not produce, so it would NOT resolve. This is the "
            "exact defect the fix corrects."
        ),
        "rationale": (
            "REJECT from C1 (`out = escapedSeq text`): `escapedSeq` pins the "
            "apostrophe's entity sequence to the hex reference (`entity '\\'' = "
            "\"&#x27;\".toList`), so a rival emitting the decimal reference "
            "diverges from the post-image at every apostrophe. Refuted at input "
            "`['\\'']`. If it verified => SPEC-TOO-WEAK (admits the bug)."
        ),
        "witness": _witness("['\\'']"),
    },
    {
        "id": "rival-partial-apos-first",
        "kind": "uniqueness",
        "expect": "reject",
        # Partial-domain: escape the apostrophe correctly (hex reference)
        # EVERYWHERE except when it is the FIRST code point, where it emits the
        # legacy decimal reference. Every input whose first char is not an
        # apostrophe, and every apostrophe that is not leading, is escaped exactly
        # like gold; the divergence is confined to inputs of the shape "'…".
        "module": _impl(
            "    match text with\n"
            "    | [] => return []\n"
            "    | c :: rest =>\n"
            "      let head := if c = '\\'' then \"&#39;\".toList else entity c\n"
            "      return (head ++ rest.flatMap entity)"),
        "refinement": (
            "escapes the apostrophe correctly EVERYWHERE except when it is the "
            "FIRST code point of the input, where it emits the legacy decimal "
            "reference. A faithful real patch of this shape (special-casing the "
            "first position) would still emit the legacy reference for any input "
            "beginning with an apostrophe, and the failing test pins the hex "
            "reference at every position, so it would NOT resolve. A genuine "
            "partial-domain break — correct on every non-leading apostrophe."
        ),
        "rationale": (
            "REJECT from C1 (`out = escapedSeq text`): C1 pins the WHOLE sequence "
            "including index 0, so a rival that mis-escapes only the leading "
            "apostrophe still diverges from `escapedSeq text` on inputs of shape "
            "\"'…\". Refuted at input `['\\'', 'a']` — a DISTINCT point from "
            "rival-apos-decimal (a leading apostrophe followed by an ordinary "
            "char, where this rival diverges but on which rival-apos-decimal and "
            "gold would both mis-/correctly escape only the leading one), so the "
            "battery varies the `text` binder. Ports nagini "
            "partial-domain-apos-first. If it verified => SPEC-TOO-WEAK "
            "(domain-incomplete)."
        ),
        "witness": _witness("['\\'', 'a']"),
    },
    {
        "id": "rival-drop-quot",
        "kind": "uniqueness",
        "expect": "reject",
        # Drop the double-quote escape: the double-quote passes through unescaped.
        "module": _flatmap("if c = '\"' then [c] else entity c"),
        "refinement": (
            "lets the double-quote pass through unescaped; a real patch doing "
            "this would emit unsafe attribute markup, and the failing test pins "
            "the double-quote's escape to its entity token, so it would NOT "
            "resolve."
        ),
        "rationale": (
            "REJECT from C1 (`out = escapedSeq text`): `escapedSeq` pins the "
            "double-quote's entity sequence (`entity '\"' = \"&quot;\".toList`), "
            "so a rival passing it through diverges from the post-image at every "
            "double-quote. Refuted at input `['\"']`. Ports nagini "
            "rival-drop-quot. If it verified => SPEC-TOO-WEAK."
        ),
        "witness": _witness("['\"']"),
    },
    {
        "id": "rival-drop-amp",
        "kind": "uniqueness",
        "expect": "reject",
        # Drop the ampersand escape: the ampersand passes through unescaped.
        # ADDED (no direct nagini rival): covers the C1 branch for '&', the
        # must-be-done-first substitution whose failure re-opens the double-escape
        # hole the escaper guards against.
        "module": _flatmap("if c = '&' then [c] else entity c"),
        "refinement": (
            "lets the ampersand pass through unescaped; a real patch doing this "
            "would leave literal ampersands in HTML output (the substitution that "
            "must be done first, so emitted entities are never re-escaped), and "
            "the escape contract pins the ampersand's entity token, so it would "
            "NOT resolve."
        ),
        "rationale": (
            "REJECT from C1 (`out = escapedSeq text`): `escapedSeq` pins the "
            "ampersand's entity sequence (`entity '&' = \"&amp;\".toList`), so a "
            "rival passing it through diverges from the post-image at every "
            "ampersand. Refuted at input `['&']` — a distinct significant-char "
            "branch of C1 from the quote/apostrophe rivals, varying `text`. If it "
            "verified => SPEC-TOO-WEAK."
        ),
        "witness": _witness("['&']"),
    },
    {
        "id": "rival-drop-lt",
        "kind": "uniqueness",
        "expect": "reject",
        # Drop the less-than escape: '<' passes through unescaped. ADDED — covers
        # the C1 branch for '<', the canonical XSS-relevant character.
        "module": _flatmap("if c = '<' then [c] else entity c"),
        "refinement": (
            "lets the less-than sign pass through unescaped; a real patch doing "
            "this would leave literal tag-opening characters in HTML output (an "
            "injection hole), and the escape contract pins its entity token, so "
            "it would NOT resolve."
        ),
        "rationale": (
            "REJECT from C1 (`out = escapedSeq text`): `escapedSeq` pins the "
            "less-than sign's entity sequence (`entity '<' = \"&lt;\".toList`), "
            "so a rival passing it through diverges from the post-image at every "
            "'<'. Refuted at input `['<']` — a distinct significant-char branch "
            "of C1, varying `text`. If it verified => SPEC-TOO-WEAK."
        ),
        "witness": _witness("['<']"),
    },
    {
        "id": "rival-mangle-ordinary",
        "kind": "uniqueness",
        "expect": "reject",
        # ADDED BY AUDIT. Attacks the `else [c]` PASS-THROUGH arm of `entity` —
        # the one arm of the per-code-point map no other rival touches. The five
        # drop/decimal rivals all attack a SIGNIFICANT char's expansion; every
        # one of them leaves the identity arm intact, so before this case a
        # spec that pinned only the five significant chars and said nothing
        # about ordinary characters would have passed the whole battery. This
        # rival expands an ordinary char ('a') into an entity-shaped sequence
        # instead of passing it through.
        "module": _flatmap(
            "if c = 'a' then \"&#97;\".toList else entity c"),
        "refinement": (
            "expands an ordinary character into a numeric character reference "
            "instead of passing it through. A faithful real patch of this shape "
            "would rewrite ordinary text into escaped references, changing every "
            "string the escaper touches rather than only the five significant "
            "characters; the escape contract pins non-significant code points to "
            "themselves, so it would NOT resolve."
        ),
        "rationale": (
            "REJECT from C1 (`out = escapedSeq text`): `escapedSeq` pins the "
            "IDENTITY arm (`entity c = [c]` for every c outside the five "
            "significant chars), so a rival expanding an ordinary char diverges "
            "from the post-image at that char. Refuted at input `['a']` — a "
            "seventh distinct point, and the only one that exercises the "
            "pass-through arm rather than an expansion arm. Without it the five "
            "significant-char rivals leave `else [c]` wholly unattacked. If it "
            "verified => SPEC-TOO-WEAK (ordinary characters unconstrained)."
        ),
        "witness": _witness("['a']"),
    },
    {
        "id": "rival-drop-gt",
        "kind": "uniqueness",
        "expect": "reject",
        # Drop the greater-than escape: '>' passes through unescaped. ADDED —
        # covers the C1 branch for '>', the fifth and last significant char, so
        # every arm of `entity` is attacked by some rival.
        "module": _flatmap("if c = '>' then [c] else entity c"),
        "refinement": (
            "lets the greater-than sign pass through unescaped; a real patch "
            "doing this would leave literal tag-closing characters in HTML "
            "output, and the escape contract pins its entity token, so it would "
            "NOT resolve."
        ),
        "rationale": (
            "REJECT from C1 (`out = escapedSeq text`): `escapedSeq` pins the "
            "greater-than sign's entity sequence (`entity '>' = \"&gt;\".toList`), "
            "so a rival passing it through diverges from the post-image at every "
            "'>'. Refuted at input `['>']` — the fifth significant-char branch of "
            "C1, so every arm of `entity` (& < > \" ') is attacked by some rival. "
            "If it verified => SPEC-TOO-WEAK."
        ),
        "witness": _witness("['>']"),
    },
]


# ===========================================================================
# NAGINI → VELVET ACCOUNTING.
#
#   nagini case                -> here
#   -----------------------------------------------------------------------
#   pos-control-reordered      -> pos-control-reordered        PORTED (audit)
#   pos-control-seg-local      -> pos-control-seg-local        PORTED
#   echo-attempt-honest        -> pos-control-direct           RE-EXPRESSED
#   admiss-significant-input   -> admiss-gold-total            RE-AIMED
#   frame-mutate-text          -> (none)                       VACUOUS
#   partial-domain-apos-first  -> rival-partial-apos-first     PORTED
#   rival-apos-decimal         -> rival-apos-decimal           PORTED
#   rival-drop-quot            -> rival-drop-quot              PORTED
#   (no sibling)               -> rival-drop-amp               ADDED
#   (no sibling)               -> rival-drop-lt                ADDED
#   (no sibling)               -> rival-drop-gt                ADDED
#   (no sibling)               -> rival-mangle-ordinary         ADDED (audit)
#   AXIOM_TESTS (3)            -> (none)                       DROPPED (G-AX lane)
#
# 11 velvet SPEC cases: 3 soundness, 1 admissibility, 7 uniqueness. EVERY nagini
# uniqueness rival that attacks a modeled clause is ported; the added rivals
# complete C1's coverage of every arm of `entity` — the five significant-char
# expansions AND the `else [c]` pass-through.
#
# PORTED (pos-control-reordered): the nagini file carries TWO positives over the
#   same backward fold — one that REORDERS the if/elif significant-char chain,
#   one that stages the per-code-point bytes into a local. An earlier pass
#   recorded the reorder positive as having no impl-region counterpart, on the
#   grounds that the per-char mapping here is the pure `def entity` rather than
#   an inline chain. That was wrong, and the audit landed the case: the impl
#   region may write its OWN inline chain, and ordering its branches in reverse
#   (`_REORDERED_CHAIN`) is exactly the nagini reorder — correct, pointwise but
#   NOT definitionally equal to `entity`, so it genuinely tests branch-order fit.
#   Both positives are now carried separately rather than merged.
# RE-EXPRESSED (echo-attempt-honest -> pos-control-direct): the nagini honest-echo
#   control asserted, right before return, that the built list equals the @Pure
#   oracle applied to the whole input. On this carrier the oracle IS the
#   transparent `escapedSeq`, and C1 already IS `out = escapedSeq text`, so the
#   honest cheapest impl is simply `return escapedSeq text` — the same argument
#   (the grounded pin is satisfiable only by the real per-char work; no wrong
#   echo verifies) expressed as a loop-free correct impl rather than an inline
#   assert.
# RE-AIMED (admiss-significant-input -> admiss-gold-total): the nagini case
#   established the read-only fractional-permission precondition on an F2P-shaped
#   input. This method has no `require` and no heap permission, so that probe is
#   vacuous; re-aimed at the residual total-domain risk (post-image joint
#   satisfiability), witnessed by the frozen impl discharging all six ensures.
# PORTED (3): the DEFAULT-VALUE / drop rivals carry across intact — only the
#   carrier changes from a nagini `List[int]` fold to a Velvet `List Char` map.
#   rival-apos-decimal (the pre-patch legacy-reference apostrophe), rival-drop-quot
#   (double-quote pass-through), and partial-domain-apos-first (legacy reference
#   only at the leading apostrophe) each carry their nagini refinement argument
#   (unpatched-repo / unsafe-markup / position-0 special-case all fail the same
#   F2P assertion), now backed by a machine-checked witness.
# ADDED (4): rival-drop-amp, rival-drop-lt, rival-drop-gt drop the escape of the
#   remaining three significant chars. The nagini file leans on its @Pure
#   `escaped_seq` oracle to catch these implicitly; here each is a concrete
#   witnessable C1 divergence at a distinct input, completing coverage of every
#   EXPANSION arm of `entity` (& < > " ').
#   rival-mangle-ordinary (added by audit) attacks the remaining arm: the
#   `else [c]` PASS-THROUGH. Every other rival mis-handles a SIGNIFICANT char and
#   leaves the identity arm intact, so without it a spec constraining only the
#   five significant chars — and saying nothing about ordinary characters — would
#   have passed the entire battery. Real divergences with machine-checked
#   witnesses, not fabricated wrongness.
# FRAME-MUTATION (frame-mutate-text): VACUOUS. The nagini rival writes through a
#   read-only (1/2) reference to `text` and is rejected for insufficient
#   permission. Velvet is referentially transparent, `text` is an immutable value,
#   no `mut` binder, no heap, no aliasing, no permission system. There is no
#   read-only input to overwrite. No substitute fabricated.
# DIVERGENCE - the class is CLOSED BY THE SEMANTICS here, and a diverging rival
#   is REJECTED rather than admitted. This bundle sets
#   ``loom.semantics.termination "total"`` AND carries
#   ``open TotalCorrectness``, and the ``open`` is the line that actually
#   selects the semantics: both namespaces define
#   ``WPGen.forWithInvariantLoop``, the later ``open`` wins, and the
#   ``PartialCorrectness`` version takes a loop measure and DISCARDS it. So the
#   two lines have to move together, and they do here. Under the total scope a
#   postcondition is claimed of ALL runs, not only of terminating ones, and the
#   verifier emits a descent obligation ``measure b' < measure b`` for every
#   loop in the impl (1 loop here, measure ``i``). A rival that loops without a
#   measure is refused outright (``Decreasing annotations are required in total
#   correctness semantics``), and a rival that supplies a CONSTANT measure to
#   dodge that is refused on the measure's own goal (``case «decreasing_1:
#   spin» ... ⊢ spin < spin``), re-measured on this bundle with a real build.
#   Divergence therefore does not discharge the ``ensures`` clauses vacuously.
#   It is still not shipped as a G-PBT reject case, and the reason is the
#   witness contract rather than a spec weakness. A reject case must carry a
#   witness that ELABORATES against the rival, and the rival's module does not
#   compile at all: the descent obligation fails at the ``method`` itself,
#   ahead of any appended tester. Measured through the gate's own
#   ``_check_witness``, even ``example : True := trivial`` comes back
#   ``witness-unproven`` on this rival, which is an INCONCLUSIVE outcome and
#   would fail the whole battery rather than pass a case. That is the right
#   behavior: a diverging impl has no output at any input, so there is no value
#   for a witness to disagree with, and its rejection is a judgement of the
#   termination obligation rather than a postcondition violation at a point.
#   Recorded as REJECTED-BY-SPEC and not expressible as a witnessed case, which
#   is neither a spec hole nor a battery gap.
# DROPPED (AXIOM_TESTS): the nagini file's three axiom-soundness/containment
#   probes over the real stdlib callees are G-AX's job (axiom_check.py /
#   mapping.md); the G-PBT gate ignores AXIOM_TESTS regardless.
#
# CLAUSE / BINDER / POINT COVERAGE. The only impl-constraining clause is C1
#   (`out = escapedSeq text`); C2–C6 are input-independent round-trip constants
#   that constrain no impl, so they are DEFENDED by the positives and admissibility
#   (all six discharge on gold) but there is no impl a rival could write that
#   violates a constant while sharing the spec — attacking them is not possible
#   and not a gap. C1 is attacked on all five significant-char arms of `entity`
#   (rival-drop-amp '&', rival-drop-lt '<', rival-drop-gt '>', rival-drop-quot
#   '"', rival-apos-decimal '\'') PLUS the `else [c]` pass-through arm
#   (rival-mangle-ordinary), plus the leading-vs-interior partial domain
#   (rival-partial-apos-first). The sole input binder `text` is varied across
#   seven distinct points — `['&']`, `['<']`, `['>']`, `['"']`, `['\'']`, `['a']`,
#   and the two-element `['\'', 'a']` — so pts=7, and no binder is held fixed by
#   every witness. All three positives and the admissibility case defend C1 and
#   the round-trip constants.
#
# WITNESS MECHANICS: the tester+`decide` path is DEAD (C2–C6 mention the opaque
#   `entityDecode`, so the postcondition's Decidable instance is noncomputable and
#   `derive_tester_for` yields a stuck `escapeCodepointsTester`). Every witness
#   instead extracts the executable program and refutes C1 directly against the
#   TRANSPARENT `escapedSeq`: each rival is loop-free so its `…Exec` reduces under
#   `decide`, while gold's `while`-loop `…Exec` (well-founded recursion) stays
#   stuck — so the same witness elaborates against the rival and FAILS against
#   gold. No witness binds a hypothesis, so no consistency probe is needed. All
#   six checked with scripts/lean_verify.sh: rival exit 0, gold build fails.
AXIOM_TESTS = []
