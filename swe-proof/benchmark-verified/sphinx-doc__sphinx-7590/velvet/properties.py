"""properties.py — G-PBT falsification battery for sphinx-doc__sphinx-7590 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text strictly inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the elided ``prove_correct`` tactic body, is
changed — both regions the consumer spec view elides, so ``markers.same_spec``
holds and the ``prove_correct literalIdAfterFloat`` obligation survives with a
byte-identical header) and swaps in a candidate implementation. It is checked by
the real verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness must ELABORATE against the rival and FAIL
against the frozen solution).

DEFENDED SURFACE (ONE contracted method over a ``List Char`` carrier):

  literalIdAfterFloat (floatText : List Char) (rest : List Char)
      return (out : List Char)
    ensures out = parsedFloatId floatText rest        -- THE load-bearing clause

Given a recognized floating-point token text and the characters that follow it,
the method produces the mangled id of the literal that token denotes. There is NO
``require`` clause: the domain is total, every ``(floatText, rest)`` pair is
in-domain, and no witness can be vacuously excluded by a false precondition.

``parsedFloatId`` is a total, fully-unfolded pure function of the method's own
two arguments (``pure`` region); the ``axioms`` region is EMPTY, so there is no
opaque answer key to echo (directive 8) and the whole carrier is transparent and
``decide``-able. The clause decomposes into THREE mutually-exclusive top-level
branches plus the two mangling shapes they select, each independently attackable:

  * TAG        — when the following characters begin with a single type-tag
                 character that is NOT itself continued by another word
                 character, that one character belongs to the NUMBER: the id is
                 the plain-literal shape over ``floatText`` extended by it. The
                 word-boundary side condition is the whole discrimination between
                 this branch and the next.
  * NAME       — otherwise, when the following characters begin with a
                 letter/underscore, the MAXIMAL leading word run is a trailing
                 suffix NAME and the id is the call-mangling shape: a fixed
                 prefix, the name's own id, a separator, the plain id of the
                 unextended ``floatText``, and a closing frame. This is the
                 branch the modeled behavior ADDS.
  * PLAIN      — otherwise the id is the plain-literal shape over ``floatText``
                 alone (the following characters are not part of the literal).
  * NAME-ID    — inside NAME, the name's own id is its decimal LENGTH PREFIX
                 followed by the name, except for one reserved name that
                 abbreviates. Both halves are separately attackable.
  * FRAMING    — the exact byte layout of both shapes (the leading/closing
                 single-character frames and the separator between the name id
                 and the embedded plain id).

TWO input binders, both free, and the post-image must hold at every value of
each. The reject witnesses below vary both: ``floatText`` over SEVEN distinct
texts (short/long, integer-like, leading-dot, trailing-dot, exponent-signed, the
token the issue reports) and ``rest`` over ELEVEN distinct tails (EMPTY, a bare
lower-case tag char, a bare upper-case tag char, a tag char continued by word
chars, an underscore-initial name, a letter-initial name, a DIGIT-initial word
run, the reserved name, a near-miss of the reserved name, and a name followed by
more of the surrounding expression). No two witnesses share an input point
(pts = 12 distinct pairs over 12 reject cases).

ADVERSARIAL READ of the nagini classes on THIS carrier:
  * FRAME/PERMISSION-MUTATION — VACUOUS. The sibling carries TWO MANDATORY
    permission rivals (``frame-mutate-ident_id``, ``frame-mutate-lit``, plus the
    C-domain ``c-frame-mutate-lit``) that write through a half-permission
    read-only input and must be rejected for INSUFFICIENT PERMISSION. Lean and
    Velvet are referentially transparent: both inputs are immutable values, this
    bundle declares no ``mut`` binder, and there is no heap, aliasing, or
    fractional-permission system to subvert. There is no read-only cell to
    overwrite, so the class is vacuous. Per the porting map, NO substitute probe
    is fabricated.
  * DIVERGENCE - the class is INAPPLICABLE to this impl and CLOSED BY THE
    SEMANTICS against any rival that manufactures it. The frozen impl is
    LOOP-FREE (straight-line ``match`` over immutable values, no loop and no
    recursion), so there is no control flow here to make diverge: a diverging
    rival cannot be obtained by mutating this body, it has to bring a loop of
    its own. When it does, the semantics refuse it. This bundle sets
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
    REJECTED on the measure's own goal
    (``case «decreasing_1: spin» ... ⊢ False``). Dropping the clause rather
    than faking it is refused even earlier, by the elaborator's own check
    (``Decreasing annotations are required in total correctness semantics``).
    So divergence neither applies to this impl nor discharges the ``ensures``
    clauses vacuously if a rival introduces it.
  * UNGROUNDED-ORACLE ECHO — N/A, as on the sibling. The post-image is pinned to
    ``parsedFloatId floatText rest``, a concrete ``def`` over the method's own
    arguments (empty ``axioms`` region, no opaque callee). The only satisfier is
    the grounded computation; there is nothing to echo. The cheapest CORRECT
    impl (``pure (parsedFloatId floatText rest)``) is carried as a POSITIVE
    control instead, which doubles as evidence the spec is not echo-vulnerable:
    every wrong branch selection below still fails it.
  * PARTIAL-DOMAIN / VALUE — the whole reject surface. Each rival gets one branch
    or one mangling component wrong and is correct on the rest of the domain.

WITNESS MECHANICS ON THIS BUNDLE. The spec is a ``method`` CONTRACT, not a bare
predicate, so each witness reaches the post-image through Velvet's own tester
machinery: ``literalIdAfterFloatTester floatText rest = false`` says the
extracted program's result violates the postcondition at that concrete input.
The frozen impl is LOOP-FREE (a single ``match`` over two total pure
recognizers), so its tester reduces fully under ``decide``; every rival below is
likewise loop-free, so every rival's tester also ``decide``s. NO witness binds a
hypothesis — every input is a concrete literal pair — so there is no consistency
obligation to discharge and no risk of an inconsistent-binder forgery. No banned
token (sorry/admit/native_decide/axiom/opaque) appears in any witness.

Both halves of every witness were checked out-of-band with
``scripts/lean_verify.sh``, in a file whose ``prove_correct`` block was stripped
so no tactic script could mask the verdict: each witness ELABORATES against its
rival (exit 0 — the rival's own output violates the post-image there) and FAILS
against the frozen solution. Critically, the gold-side failure is a SEMANTIC
verdict, not a stuck reduction: Lean reports ``decide proved that the
proposition literalIdAfterFloatTester … = false is false`` — i.e. gold's tester
evaluates to ``true`` at that input, so the witness asserts something true of the
WRONG impl and demonstrably FALSE of the right one. That rules out the tautology
reading (and the "gold merely failed to reduce" reading) for all nine rivals.

AXIOM lane: dropped. ``AXIOM_TESTS = []``. The sibling carries axiom-soundness
and axiom-containment probes for its one ``@ContractOnly`` identifier-mangling
axiom; this bundle consumes NO axiom (``meta.json`` ``axioms: []``) — the
recognizers and the mangling are deep-model A-references validated by
axiom_check.py — and the G-PBT gate ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "sphinx-doc__sphinx-7590"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Region anchors. `_IMPL` is the frozen impl body verbatim — everything strictly
# BETWEEN `-- impl-start` and `-- impl-end`, both of which live inside the elided
# impl region. `_PROOF` is the frozen obligation's tactic body. Every variant
# _swaps ONE of these, so edits are confined to the two regions the spec view
# elides and same_spec holds by construction. Both anchors are asserted unique at
# import time, so the manifest breaks loudly if the frozen solution ever drifts.
# ---------------------------------------------------------------------------

_IMPL = (
    "    match matchTypeTag rest, matchSuffixName rest with\n"
    "    | some c, _         => pure (numberLitId (floatText ++ [c]))\n"
    "    | none,   some ident => pure (suffixedLitId floatText ident)\n"
    "    | none,   none       => pure (numberLitId floatText)\n"
)

assert _BASE.count(_IMPL) == 1, "method impl region drifted from expected text"

_PROOF = ("prove_correct literalIdAfterFloat by\n"
          "  loom_solve <;> simp_all [parsedFloatId]")

assert _BASE.count(_PROOF) == 1, "proof region drifted from expected text"


def _impl(new_body):
    """Full Solution.lean variant with ONLY the impl body replaced."""
    return _swap(_BASE, _IMPL, new_body)


def _impl_reproved(new_body, new_proof):
    """Impl body replaced AND the proof retuned (correct reshapes only)."""
    return _swap(_impl(new_body), _PROOF, new_proof)


# ---- The three frozen branch arms, named so each rival can state exactly which
# ---- ONE it perturbs and leave the other two byte-identical to gold. That is
# ---- what makes each rejection attributable to a single clause component.
_HD = "    match matchTypeTag rest, matchSuffixName rest with\n"
_TAG = "    | some c, _         => pure (numberLitId (floatText ++ [c]))\n"
_NAME = "    | none,   some ident => pure (suffixedLitId floatText ident)\n"
_PLAIN = "    | none,   none       => pure (numberLitId floatText)\n"

assert _IMPL == _HD + _TAG + _NAME + _PLAIN, "branch decomposition drifted"


# ---- witness preamble + builder. The postcondition is fully transparent (empty
# ---- axioms region), so `prove_postcondition_decidable_for` yields a REAL
# ---- executable instance and `derive_tester_for` a computable tester — the
# ---- django-13012 path, not the stuck-`decide` path. A witness therefore states
# ---- `…Tester floatText rest = false`: the extracted program's output violates
# ---- the post-image at that concrete input. Checked in a file whose
# ---- `prove_correct` block has been stripped, so no tactic script can interfere.
_TESTER = ("extract_program_for literalIdAfterFloat\n"
           "prove_precondition_decidable_for literalIdAfterFloat\n"
           "prove_postcondition_decidable_for literalIdAfterFloat\n"
           "derive_tester_for literalIdAfterFloat\n\n")


def _witness(float_text, rest):
    return (_TESTER +
            f'example : literalIdAfterFloatTester "{float_text}".toList '
            f'"{rest}".toList = false := by\n  decide\n')


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROL 1 (soundness) — the cheapest CORRECT impl: return the
    # pure post-image directly instead of re-deriving it by cases. Structurally
    # different (no branching at all in the impl region), observationally
    # identical on the whole domain. MUST verify, else the postcondition would
    # reject the output of its own model (SPEC-TOO-STRONG). Also the standing
    # answer to the echo question: the post-image is grounded in the arguments,
    # so "just return the model" IS the correct computation, not a cheat.
    # Verified out-of-band with a real build (exit 0).
    # =====================================================================
    {
        "id": "pos-model-direct",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl("    pure (parsedFloatId floatText rest)\n"),
        "rationale": "structurally different CORRECT impl: it returns the pure "
                     "post-image directly rather than re-deriving it by cases on "
                     "the two recognizers. Observationally identical at every "
                     "input, so `out = parsedFloatId floatText rest` holds on the "
                     "whole (total, unconstrained) domain and the frozen tactic "
                     "body still closes the byte-identical obligation. A faithful "
                     "reshape MUST verify, else SPEC-TOO-STRONG.",
    },
    # =====================================================================
    # POSITIVE CONTROL 2 (soundness) — FRAMING INLINED. Keeps the frozen branch
    # structure but spells the plain-literal shape out in place (its leading and
    # closing single-character frames written literally) in the two branches that
    # use it, instead of calling the named pure helper. Definitionally equal but
    # not syntactically so, which is what makes this a real test of fit rather
    # than a re-spelling: the proof needs the helper's own unfolding, so the
    # tactic body is retuned (an elided region). Verified out-of-band (exit 0).
    # =====================================================================
    {
        "id": "pos-framing-inlined",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl_reproved(
            _HD +
            "    | some c, _         => pure (['L'] ++ (floatText ++ [c]) ++ ['E'])\n"
            + _NAME +
            "    | none,   none       => pure (['L'] ++ floatText ++ ['E'])\n",
            "prove_correct literalIdAfterFloat by\n"
            "  loom_solve <;> simp_all [parsedFloatId, numberLitId, suffixedLitId]"),
        "rationale": "behaviourally-identical reshape: the plain-literal shape is "
                     "written out in place (both single-character frames literal) "
                     "in the TAG and PLAIN branches instead of delegating to the "
                     "named pure helper. Same produced `List Char` at every input, "
                     "so the post-image is unchanged; only the syntactic form "
                     "differs, so the elided tactic body is retuned to unfold the "
                     "helper. Must verify, else SPEC-TOO-STRONG (the clause would "
                     "be pinning a spelling rather than a value).",
    },
    # =====================================================================
    # POSITIVE CONTROL 3 (soundness) — EXHAUSTIVE PATTERNS. Replaces the frozen
    # TAG arm's wildcard second component with the two explicit cases, so the
    # match is four-way instead of three-way. Same selection function; proves the
    # spec does not depend on how the don't-care component is written. Verified
    # out-of-band with a real build (exit 0).
    # =====================================================================
    {
        "id": "pos-explicit-patterns",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl_reproved(
            _HD +
            "    | some c, none      => pure (numberLitId (floatText ++ [c]))\n"
            "    | some c, some _    => pure (numberLitId (floatText ++ [c]))\n"
            + _NAME + _PLAIN,
            "prove_correct literalIdAfterFloat by\n"
            "  loom_solve <;> simp_all [parsedFloatId, numberLitId, suffixedLitId]"),
        "rationale": "the frozen TAG arm ignores the second recognizer's result "
                     "via a wildcard; this reshape splits it into the two explicit "
                     "cases, both returning the same value. A four-way match "
                     "computing the identical selection function, so the post-image "
                     "is unchanged and it must verify — evidence the clause pins "
                     "the SELECTION, not the pattern spelling.",
    },
    # =====================================================================
    # ADMISSIBILITY — the sibling's probe re-derives that the precondition is
    # internally consistent and admits a normal input of the failing test's
    # shape. This bundle has NO `require` clause, so unsatisfiability is not the
    # residual risk; the residual risk is that the post-image is DEGENERATE (a
    # constant, or collapsing the three branches together), which would make
    # every positive above pass for nothing. One in-region assert pins the
    # post-image at three concrete inputs that land in THREE DIFFERENT branches
    # and produce three structurally different ids: the token the issue reports
    # (NAME branch — the call-mangling shape with a length-prefixed name id), a
    # tag-suffixed token (TAG branch — the tag folded into the number), and a
    # bare token with nothing following (PLAIN branch). The impl is kept verbatim
    # so the method's own obligation still discharges; only the elided tactic
    # body is retuned to clear the extra goal. The assert is LIVE — checked
    # during authoring: with the gold tactic body alone the variant FAILS (the
    # assert leaves an unsolved goal), and perturbing any expected id by one
    # character makes `decide` report the proposition FALSE.
    # =====================================================================
    {
        "id": "admiss-three-branch-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl_reproved(
            "    assert (with_name_prefix `admiss\n"
            "      (parsedFloatId \"6.62607015e-34\".toList \"q_J\".toList\n"
            "         = \"clL_Zli3q_JEL6.62607015e-34EE\".toList ∧\n"
            "       parsedFloatId \"5e42\".toList \"f\".toList = \"L5e42fE\".toList ∧\n"
            "       parsedFloatId \"5.0\".toList [] = \"L5.0E\".toList))\n" + _IMPL,
            "prove_correct literalIdAfterFloat by\n"
            "  loom_solve <;> simp_all [parsedFloatId]\n"
            "  all_goals decide"),
        "rationale": "the domain is total (no `require`), so the admissibility "
                     "risk is DEGENERACY rather than unsatisfiability. The "
                     "in-region assert pins the post-image at three inputs that "
                     "select three DIFFERENT branches and yield three structurally "
                     "different ids — the call-mangling shape with a "
                     "length-prefixed trailing name (the shape the reported case "
                     "needs), the tag-folded plain shape, and the bare plain shape "
                     "with nothing following. All three discharge, so the "
                     "obligation is non-degenerate: the clause genuinely "
                     "distinguishes the branches instead of collapsing them or "
                     "returning a constant. The impl is kept verbatim so the "
                     "method's own `ensures` discharges too.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals. Each is a wrong impl sharing the frozen
    # spec byte-for-byte that MUST be rejected, carrying a machine-checked
    # refutation witness at a concrete input (elaborates against the rival, fails
    # SEMANTICALLY against gold) and the refinement argument that its faithful
    # real counterpart would NOT resolve the failing test. Every rival is
    # loop-free, so every tester `decide`s; the frozen spec is untouched.
    # =====================================================================
    {
        "id": "weak-prepatch-no-name-branch",
        "kind": "uniqueness",
        "expect": "reject",
        # THE pre-image behaviour: consume a maximal run of tag-ish characters
        # into the number text and never recognize a trailing suffix NAME at all.
        # Correct on part of the PLAIN domain; wrong on the entire NAME branch and
        # on any tail whose leading run is longer than one tag character.
        "module": _impl(
            "    let consumed := rest.takeWhile "
            "(fun c => isTypeTagChar c || c == 'u' || c == 'U')\n"
            "    pure (numberLitId (floatText ++ consumed))\n"),
        "refinement": "this IS the pre-image behaviour: the trailing characters "
                      "are swallowed by a maximal run over a fixed small character "
                      "class and the result is always the plain-literal shape — a "
                      "trailing suffix NAME is never recognized as such. On the "
                      "token the issue reports, the trailing name is not consumed "
                      "at all, so the surrounding definition fails to parse to the "
                      "end and the expected call-mangled id is never produced. The "
                      "failing test asserts that id for a whole matrix of "
                      "name-suffixed tokens, so this would NOT resolve.",
        "rationale": "REJECT from `out = parsedFloatId floatText rest` via the "
                     "NAME branch: whenever the tail begins a letter/underscore "
                     "word run, the post-image demands the call-mangling shape, "
                     "and the rival returns the plain shape instead. Verifying "
                     "would be SPEC-TOO-WEAK — the entire added branch would be "
                     "unpinned. Refuted at floatText=`6.62607015e-34`, "
                     "rest=`q_J`, the reported token: gold's tester is true, the "
                     "rival's false.",
        "witness": _witness("6.62607015e-34", "q_J"),
    },
    {
        "id": "weak-name-without-length-prefix",
        "kind": "uniqueness",
        "expect": "reject",
        # The sibling's strongest reasoned attack: use the RAW trailing name text
        # in the mangling instead of the name's own id (which prefixes its decimal
        # LENGTH). Selects the right branch and gets every frame right; only the
        # NAME-ID component is wrong.
        "module": _impl(
            _HD + _TAG +
            "    | none,   some ident => pure (\"clL_Zli\".toList ++ ident ++ ['E']\n"
            "                                   ++ numberLitId floatText ++ ['E'])\n"
            + _PLAIN),
        "refinement": "the faithful counterpart would embed the trailing name's "
                      "raw text where the mangling requires that name's own id — "
                      "which is the name preceded by its decimal LENGTH. Every "
                      "name-suffixed row of the failing test asserts an id "
                      "containing that length prefix, so dropping it makes every "
                      "one of those rows mismatch and it would NOT resolve.",
        "rationale": "REJECT from the NAME-ID component of the post-image: the "
                     "clause embeds the trailing name's id (decimal length prefix "
                     "then the name), the rival embeds the bare name. Correct "
                     "branch, correct framing, wrong component — a NEAR-MISS, so "
                     "it gets its own witness at a distinct input: "
                     "floatText=`5`, rest=`q_J` (a short integer-like text with a "
                     "three-character name, where the missing prefix is the only "
                     "difference). If it verified, the length-prefix component "
                     "would be unpinned (SPEC-TOO-WEAK).",
        "witness": _witness("5", "q_J"),
    },
    {
        "id": "weak-name-loses-reserved-abbrev",
        "kind": "uniqueness",
        "expect": "reject",
        # Finer near-miss than the previous rival: it DOES emit the decimal length
        # prefix, so it agrees with gold on every ordinary trailing name — but it
        # inlines the mangling and thereby drops the one reserved name that
        # abbreviates instead of being length-prefixed.
        "module": _impl(
            _HD + _TAG +
            "    | none,   some ident => pure (\"clL_Zli\".toList "
            "++ (toString ident.length).toList ++ ident\n"
            "                                   ++ ['E'] ++ numberLitId floatText "
            "++ ['E'])\n"
            + _PLAIN),
        "refinement": "a counterpart that hand-rolled the length-prefix rule "
                      "instead of delegating to the shared identifier-id routine "
                      "would lose that routine's special case for one reserved "
                      "name, which abbreviates rather than taking a length prefix. "
                      "The produced id for a token carrying that reserved name as "
                      "its trailing suffix would then be the length-prefixed form, "
                      "not the abbreviation the mangling scheme mandates — a "
                      "non-conformant id, and the identifier-id behaviour the test "
                      "matrix relies on throughout.",
        "rationale": "REJECT from the NAME-ID component's reserved-name case. This "
                     "rival is STRICTLY closer to gold than "
                     "`weak-name-without-length-prefix`: it agrees with the "
                     "post-image on every ordinary trailing name, so that rival's "
                     "witness does not refute it and it needs its own. Refuted at "
                     "the sub-domain it actually gets wrong — floatText=`5.`, "
                     "rest=`std`, the one reserved trailing name — where gold's "
                     "tester is true and the rival's false. If it verified, the "
                     "abbreviation case would be unpinned (SPEC-TOO-WEAK).",
        "witness": _witness("5.", "std"),
    },
    {
        "id": "weak-name-takes-whole-tail",
        "kind": "uniqueness",
        "expect": "reject",
        # Uses the ENTIRE remaining character stream as the trailing name instead
        # of the MAXIMAL leading WORD RUN. Agrees with gold whenever the tail is
        # nothing but a word run; diverges as soon as anything follows the name.
        "module": _impl(
            _HD + _TAG +
            "    | none,   some _     => pure (suffixedLitId floatText rest)\n"
            + _PLAIN),
        "refinement": "a counterpart that treated everything after the number as "
                      "the trailing name — rather than the maximal leading run of "
                      "word characters — would absorb the surrounding expression "
                      "into the name. In the very example the issue reports the "
                      "suffixed number is one FACTOR of a product, so the operator "
                      "and the second factor follow it directly; absorbing them "
                      "yields a garbage name, a wrong id, and an unparseable "
                      "remainder. It would NOT resolve.",
        "rationale": "REJECT from the MAXIMALITY of the NAME branch's recognizer: "
                     "the post-image takes the maximal leading word run as the "
                     "name, the rival takes the whole tail. A near-miss agreeing "
                     "with gold on every tail that is purely a word run, so it is "
                     "refuted where it actually differs — floatText="
                     "`6.62607015e-34`, rest=`q_J*1q_s`, the reported "
                     "expression's own continuation. If it verified, the name's "
                     "right boundary would be unpinned (SPEC-TOO-WEAK).",
        "witness": _witness("6.62607015e-34", "q_J*1q_s"),
    },
    {
        "id": "weak-name-drops-separator",
        "kind": "uniqueness",
        "expect": "reject",
        # Off-by-one FRAMING near-miss inside the NAME branch: omits the single
        # separator character between the trailing name's id and the embedded
        # plain id. Correct branch, correct name id, correct embedded id.
        "module": _impl(
            _HD + _TAG +
            "    | none,   some ident => pure (\"clL_Zli\".toList ++ identId ident\n"
            "                                   ++ numberLitId floatText ++ ['E'])\n"
            + _PLAIN),
        "refinement": "the mangling places a single separator character between "
                      "the trailing name's id and the embedded plain-literal id. A "
                      "counterpart that omitted it would emit a byte sequence that "
                      "is not a well-formed mangled name, and every "
                      "name-suffixed row of the failing test compares the id "
                      "string exactly, so it would NOT resolve.",
        "rationale": "REJECT from the FRAMING component of the NAME shape: the "
                     "post-image has an explicit separator between the name id and "
                     "the embedded plain id, absent here. Off-by-one byte layout. "
                     "Refuted at floatText=`.5`, rest=`_udl` — a leading-dot "
                     "number text with an UNDERSCORE-initial name, the "
                     "letter-vs-underscore start alternative no other witness "
                     "probes. If it verified, the exact byte layout would be "
                     "unpinned (SPEC-TOO-WEAK).",
        "witness": _witness(".5", "_udl"),
    },
    {
        "id": "weak-plain-drops-closing-frame",
        "kind": "uniqueness",
        "expect": "reject",
        # Attacks the PLAIN branch alone: emits the leading frame but not the
        # closing one. Correct on the whole TAG and NAME domains.
        "module": _impl(
            _HD + _TAG + _NAME +
            "    | none,   none       => pure (['L'] ++ floatText)\n"),
        "refinement": "the plain-literal id wraps the token in a leading and a "
                      "closing single-character frame. A counterpart that emitted "
                      "only the leading one would mismangle every plain number "
                      "token — and the plain id is also EMBEDDED inside every "
                      "name-suffixed id, so the damage is not confined to the plain "
                      "rows. The failing test compares both families of id string "
                      "exactly; it would NOT resolve.",
        "rationale": "REJECT from the FRAMING component of the PLAIN shape: the "
                     "post-image closes with a single frame character the rival "
                     "omits. Refuted at floatText=`5e-42`, rest=`` — the EMPTY "
                     "tail, the only witness that probes the `rest = []` boundary "
                     "of both recognizers, and the sole input point where nothing "
                     "at all follows the number. If it verified, the plain shape's "
                     "byte layout would be unpinned (SPEC-TOO-WEAK).",
        "witness": _witness("5e-42", ""),
    },
    {
        "id": "weak-tag-not-folded-into-number",
        "kind": "uniqueness",
        "expect": "reject",
        # Attacks the TAG branch's PAYLOAD: selects the branch correctly but drops
        # the recognized tag character instead of folding it into the number text.
        "module": _impl(
            _HD +
            "    | some _, _         => pure (numberLitId floatText)\n"
            + _NAME + _PLAIN),
        "refinement": "when a single type-tag character trails the number and is "
                      "not itself continued by a word character, that character is "
                      "PART OF THE NUMBER's text. A counterpart that recognized it "
                      "and then discarded it would emit the id of the untagged "
                      "number; the failing test asserts the id of the token "
                      "INCLUDING its tag for every tag character over its whole "
                      "float matrix, so it would NOT resolve.",
        "rationale": "REJECT from the TAG branch's payload: the post-image extends "
                     "`floatText` by the recognized tag character before framing "
                     "it, the rival frames `floatText` alone. Refuted at "
                     "floatText=`5.0`, rest=`L` — a bare tag character with "
                     "nothing after it, so the word boundary holds trivially and "
                     "the TAG branch is unambiguously selected. If it verified, "
                     "the tag would be recognized but never recorded "
                     "(SPEC-TOO-WEAK).",
        "witness": _witness("5.0", "L"),
    },
    {
        "id": "weak-tag-ignores-word-boundary",
        "kind": "uniqueness",
        "expect": "reject",
        # Attacks the TAG recognizer's SIDE CONDITION: treats any leading tag
        # character as a tag, dropping the requirement that it not be continued by
        # another word character. This is precisely the TAG-vs-NAME discrimination
        # — the rival is correct wherever the tag stands alone, and wrong exactly
        # where a name HAPPENS to begin with a tag character.
        "module": _impl(
            "    match rest.head?.filter isTypeTagChar, matchSuffixName rest with\n"
            + _TAG + _NAME + _PLAIN),
        "refinement": "a counterpart that treated any leading tag character as a "
                      "type tag, without checking that no word character continues "
                      "it, would misread a trailing NAME that merely begins with "
                      "one of those characters: it would fold the name's first "
                      "character into the number and drop the rest. The failing "
                      "test's matrix contains exactly such tokens — trailing names "
                      "whose first character is a tag character — and asserts the "
                      "call-mangled id for them, so it would NOT resolve.",
        "rationale": "REJECT from the TAG recognizer's word-boundary side "
                     "condition, the single load-bearing discriminator between the "
                     "TAG and NAME branches. The rival agrees with gold on every "
                     "isolated tag and on every name NOT starting with a tag "
                     "character, so it is refuted exactly in the overlap: "
                     "floatText=`5.0`, rest=`fudl` — a name whose first character "
                     "is a tag character. Gold takes the NAME branch (the "
                     "boundary fails), the rival takes TAG. If it verified, the "
                     "boundary condition would be unpinned (SPEC-TOO-WEAK) — the "
                     "subtlest hole in this spec.",
        "witness": _witness("5.0", "fudl"),
    },
    {
        "id": "weak-branch-precedence-inverted",
        "kind": "uniqueness",
        "expect": "reject",
        # Attacks the ORDER of the two branches: tries the NAME recognizer FIRST
        # and only falls back to TAG. Since a lone tag character is also a
        # letter, it is matched as a one-character NAME, so a plainly tag-suffixed
        # token gets the call-mangling instead of the plain shape.
        "module": _impl(
            "    match matchSuffixName rest, matchTypeTag rest with\n"
            "    | some ident, _      => pure (suffixedLitId floatText ident)\n"
            "    | none,   some c     => pure (numberLitId (floatText ++ [c]))\n"
            + _PLAIN),
        "refinement": "the two recognizers OVERLAP: a lone trailing tag character "
                      "is both a valid type tag and a valid one-character name, so "
                      "which one is tried first decides the token's meaning. A "
                      "counterpart that tried the name first would mangle every "
                      "ordinarily tag-suffixed number as a name-suffixed literal. "
                      "The failing test asserts the PLAIN id for its whole "
                      "tag-suffixed float matrix, so it would NOT resolve.",
        "rationale": "REJECT from the BRANCH PRECEDENCE of the post-image: it "
                     "consults the tag recognizer first and the name recognizer "
                     "only on its failure, the rival inverts that. Distinct from "
                     "`weak-tag-ignores-word-boundary`, which keeps the precedence "
                     "and weakens the side condition — this one keeps both "
                     "recognizers exact and only reorders them, so neither rival's "
                     "witness refutes the other. Refuted at floatText=`5e42`, "
                     "rest=`f`: gold folds the lone tag into the number, the rival "
                     "treats it as a one-character name. If it verified, the "
                     "branch order would be unpinned (SPEC-TOO-WEAK).",
        "witness": _witness("5e42", "f"),
    },
    {
        "id": "weak-tag-drops-closing-frame",
        "kind": "uniqueness",
        "expect": "reject",
        # Added by audit. The TAG branch's own FRAMING was the one component no
        # shipped rival attacked: `weak-plain-drops-closing-frame` drops the
        # closing frame in the PLAIN arm only, leaving the TAG arm byte-identical
        # to gold, so its witness (at the EMPTY tail) cannot reach this arm at all.
        # Here the closing frame is omitted in the TAG arm alone; the PLAIN and
        # NAME arms stay verbatim, so the rejection is attributable to exactly the
        # tagged-number byte layout.
        "module": _impl(
            _HD +
            "    | some c, _         => pure (['L'] ++ (floatText ++ [c]))\n"
            + _NAME + _PLAIN),
        "refinement": "a counterpart that emitted only the leading frame when a "
                      "type tag has been folded into the number would mismangle "
                      "every tag-suffixed token while leaving untagged ones "
                      "correct — a defect the plain-branch framing rival cannot "
                      "produce. The failing test asserts the exact id string for "
                      "its whole tag-suffixed float matrix, so it would NOT "
                      "resolve.",
        "rationale": "REJECT from the FRAMING component of the TAG branch, which "
                     "is REACHED ONLY when the tag recognizer succeeds. Refuted at "
                     "floatText=`5e42`, rest=`F` — the upper-case tag character, "
                     "an input point no other witness uses, where gold's tester is "
                     "true and the rival's false. Distinct from "
                     "`weak-plain-drops-closing-frame`, whose rival keeps this arm "
                     "verbatim and whose witness sits at the empty tail (the PLAIN "
                     "branch), so neither refutes the other. If it verified, the "
                     "tagged-number byte layout would be unpinned "
                     "(SPEC-TOO-WEAK).",
        "witness": _witness("5e42", "F"),
    },
    {
        "id": "weak-name-start-admits-any-word-char",
        "kind": "uniqueness",
        "expect": "reject",
        # Added by audit. The NAME recognizer's START condition — that a trailing
        # name must begin with a LETTER or UNDERSCORE, not merely with any word
        # character — was claimed as covered but never demonstrated: every shipped
        # rival keeps `matchSuffixName` exact on this point, so a spec that let a
        # DIGIT start a name would have passed the whole battery. This rival
        # weakens the start class to any word character and is otherwise gold.
        "module": _impl(
            "    match matchTypeTag rest, (match rest with\n"
            "                              | []      => none\n"
            "                              | c :: cs => if isWordChar c then\n"
            "                                             some (c :: cs.takeWhile "
            "(fun d => isWordChar d))\n"
            "                                           else none) with\n"
            + _TAG + _NAME + _PLAIN),
        "refinement": "a counterpart that accepted any word character as the start "
                      "of a trailing suffix name would treat a digit run following "
                      "the number as a name and emit the call-mangling shape for "
                      "it, where the number's own trailing digits are simply not "
                      "part of any suffix. That mangles tokens the test matrix "
                      "expects the plain shape for, so it would NOT resolve.",
        "rationale": "REJECT from the START CONDITION of the NAME recognizer: the "
                     "post-image admits a trailing name only when the tail begins "
                     "a letter or underscore, and the rival admits any word "
                     "character. Refuted at floatText=`5`, rest=`1abc` — a "
                     "DIGIT-initial tail, the alternative the other eight "
                     "witnesses never place at the start position, where gold "
                     "takes PLAIN and the rival takes NAME. If it verified, the "
                     "letter/underscore start class would be unpinned "
                     "(SPEC-TOO-WEAK).",
        "witness": _witness("5", "1abc"),
    },
    {
        "id": "weak-reserved-abbrev-over-applied",
        "kind": "uniqueness",
        "expect": "reject",
        # Added by audit, and the converse of `weak-name-loses-reserved-abbrev`.
        # That rival abbreviates NOTHING; this one abbreviates TOO MUCH, applying
        # the reserved name's abbreviation to every name merely PREFIXED by it.
        # Both directions of the same clause need attacking: a spec pinning only
        # "the reserved name abbreviates" without pinning "and nothing else does"
        # would reject the first rival and admit this one.
        "module": _impl(
            _HD + _TAG +
            "    | none,   some ident => pure (\"clL_Zli\".toList\n"
            "        ++ (if ident.take 3 = ['s','t','d'] then ['S','t']\n"
            "            else (toString ident.length).toList ++ ident)\n"
            "        ++ ['E'] ++ numberLitId floatText ++ ['E'])\n"
            + _PLAIN),
        "refinement": "a counterpart that tested the reserved name by PREFIX "
                      "rather than by equality would abbreviate every trailing "
                      "name that merely starts with those three characters, "
                      "emitting the reserved abbreviation where the "
                      "length-prefixed form is required — and losing the rest of "
                      "the name entirely. Those ids are compared exactly, so it "
                      "would NOT resolve.",
        "rationale": "REJECT from the EXACTNESS of the reserved-name case: the "
                     "post-image abbreviates only the reserved name itself, and "
                     "the rival abbreviates any name prefixed by it. Refuted at "
                     "floatText=`5`, rest=`stdx` — a NEAR-MISS of the reserved "
                     "name, one character longer, where gold emits the "
                     "length-prefixed form and the rival the abbreviation. The "
                     "converse of `weak-name-loses-reserved-abbrev` (which "
                     "abbreviates nothing and is refuted at the exact reserved "
                     "name), so neither rival's witness refutes the other and the "
                     "clause is pinned in BOTH directions. If it verified, the "
                     "abbreviation's domain would be unpinned (SPEC-TOO-WEAK).",
        "witness": _witness("5", "stdx"),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 15 SPEC cases over TWO
# contracted functions (`number_literal_id` for the dialect that carries trailing
# suffix names, and `c_number_literal_id` for the parallel simpler dialect), plus
# a TWO-case AXIOM lane. This bundle contracts ONE method, `literalIdAfterFloat`,
# and models a NARROWER slice: the floating-point branch, which is what the
# FAIL_TO_PASS test exercises. Case-count parity is therefore not the target;
# what is carried over is coverage of the surface THIS bundle models.
#
# Two structural differences drive most of the accounting:
#
#  (1) CARRIER NARROWING, both ways. The sibling takes the branch decision as
#      GIVEN — `suffixed` and `valid` are boolean INPUTS, and the precomputed
#      identifier id is a third input tied to the mangling by precondition. Here
#      the decision is COMPUTED inside the modeled function from the raw trailing
#      characters by two transparent recognizers, and the identifier id is
#      computed by a transparent pure helper. So the sibling's boolean-flag
#      rivals become rivals against the RECOGNIZERS (a strictly larger attack
#      surface: their side conditions and their precedence are now attackable,
#      which on the sibling they were not), and its `ident_id`-vs-`ident` rival
#      becomes a rival against the name-id helper.
#  (2) NO PRECONDITION. The sibling's three-clause `Requires` (nonempty text, the
#      reserved name excluded, the identifier-id tie) has NO counterpart: this
#      method is total. That REMOVES the sibling's excluded-`std` restriction, so
#      the reserved name is IN-DOMAIN here and becomes an attackable component
#      rather than a precondition exclusion — see
#      `weak-name-loses-reserved-abbrev`, which has no sibling counterpart
#      precisely because the sibling's precondition rules that input out.
#
#   sibling case                          -> here                                       disposition
#   ------------------------------------------------------------------------------------------------
#   pos-branch-reorder                    -> pos-explicit-patterns                      PORTED (re-aimed)
#   pos-local-reshape                     -> pos-framing-inlined                        PORTED
#   (no sibling)                          -> pos-model-direct                            ADDED
#   admiss-both-branches-reachable        -> admiss-three-branch-nondegenerate          PORTED (re-aimed)
#   partial-prepatch-no-udl               -> weak-prepatch-no-name-branch               PORTED
#   partial-raw-ident-no-length-prefix    -> weak-name-without-length-prefix            PORTED
#   partial-drop-mid-E                    -> weak-name-drops-separator                  PORTED
#   partial-ordinary-drop-E               -> weak-plain-drops-closing-frame             PORTED
#   partial-ignores-suffixed              -> weak-branch-precedence-inverted            PORTED (re-aimed)
#   c-partial-prepatch-always-fold        -> weak-tag-ignores-word-boundary             PORTED (re-aimed)
#   c-partial-never-fold                  -> weak-tag-not-folded-into-number            PORTED (re-aimed)
#   c-partial-drop-E                      -> (subsumed)                                 OMITTED
#   c-pos-local-reshape                   -> (subsumed)                                 OMITTED
#   frame-mutate-ident_id       [MANDATORY]-> (none)                                    VACUOUS
#   frame-mutate-lit                      -> (none)                                     VACUOUS
#   c-frame-mutate-lit          [MANDATORY]-> (none)                                    VACUOUS
#   (no sibling)                          -> weak-name-loses-reserved-abbrev            ADDED
#   (no sibling)                          -> weak-name-takes-whole-tail                 ADDED
#   (no sibling)                          -> weak-tag-drops-closing-frame               ADDED (audit)
#   (no sibling)                          -> weak-name-start-admits-any-word-char       ADDED (audit)
#   (no sibling)                          -> weak-reserved-abbrev-over-applied          ADDED (audit)
#   AXIOM_TESTS (2 cases)                 -> (none)                                     DROPPED (G-AX)
#
# Totals over the sibling's 15 SPEC cases: 10 ported (5 directly, 5 re-aimed onto
# the recognizers this bundle computes), 2 omitted as subsumed, 3 permission
# rivals vacuous — 10 + 2 + 3 = 15, the ledger rows above. Plus 6 cases with no
# sibling counterpart (3 from the port, 3 added by audit); the 2-case axiom lane
# dropped. Shipped: 16 cases = 3 soundness + 1 admissibility + 12 uniqueness.
# (The pre-audit manifest recorded "14 sibling cases / 11 ported / 13 shipped";
# the sibling list has 15 entries and 10 arrows land on a shipped case, so those
# three counts were simply wrong and are corrected here. No disposition changed.)
#
# PORTED-RE-AIMED, in detail (the arguments that changed shape, not substance):
#   * partial-ignores-suffixed attacked a boolean INPUT the sibling was handed:
#     build the name-suffixed form even when the flag says the number carries an
#     ordinary suffix. Here that flag is COMPUTED, so the same argument — "the
#     ordinary-suffix case must not be mangled as a name-suffixed literal" — is
#     expressed as inverting the two recognizers' PRECEDENCE
#     (weak-branch-precedence-inverted). Same defended clause, mechanics rebuilt
#     for a carrier that decides rather than receives.
#   * c-partial-prepatch-always-fold was the sibling's pre-image maximal-run
#     defect on the simpler dialect: fold the whole trailing run into the number
#     regardless of whether it is a recognized suffix. The counterpart here is
#     weak-tag-ignores-word-boundary — drop the recognizer's side condition so a
#     trailing NAME beginning with a tag character is misread as a tag. This is
#     the SAME "recognized-vs-not" confusion, and on this carrier it is the
#     subtlest hole in the spec, so it is one of the two cases whose witness was
#     chosen most carefully.
#   * c-partial-never-fold (never fold a recognized suffix into the text) ports
#     to weak-tag-not-folded-into-number: recognize the tag, then discard it.
#   * pos-branch-reorder negated the guard and swapped two branches. The frozen
#     impl here is a `match` on a PAIR of options, so the faithful analogue of
#     "same values, different control path" is splitting the wildcard arm into its
#     explicit cases (pos-explicit-patterns); a literal branch SWAP would change
#     the selection function, which is what weak-branch-precedence-inverted is.
#   * admiss-both-branches-reachable re-derived the `Requires` facts as asserts to
#     show the precondition admits a normal input. There is NO precondition here,
#     so that risk does not exist; the probe is re-aimed at the residual one —
#     that the post-image might be degenerate — by pinning it at three inputs in
#     three different branches producing three structurally different ids.
#
# OMITTED (2 cases, both subsumed — not dropped for difficulty):
#   * c-partial-drop-E and c-pos-local-reshape are the SECOND modeled function's
#     copies of arguments already made against the first. This bundle contracts
#     ONE method, and its plain-literal shape is the SAME pure helper the sibling's
#     two functions shared, so `weak-plain-drops-closing-frame` already attacks
#     exactly the byte layout c-partial-drop-E attacks and `pos-framing-inlined`
#     already is the framing reshape c-pos-local-reshape is. Adding them would be
#     the same rival twice at a second input, not new coverage. There is no
#     unmodeled behavior hiding here: the simpler dialect's suffix decision is
#     recorded in meta.json `additional_change_sites` as deliberately not modeled
#     (the FAIL_TO_PASS test observes the id this method produces), so a rival
#     against it would have no obligation to attack.
#
# VACUOUS (3 permission rivals, 2 of them MANDATORY on the sibling): the sibling's
#   read-only inputs are held at half permission and its mandatory probes write
#   through them, expecting INSUFFICIENT PERMISSION. Velvet is referentially
#   transparent: both inputs are immutable values, no `mut` binder is declared,
#   and there is no heap, aliasing, or fractional-permission system. Nothing to
#   overwrite and no substitute fabricated (porting map: vacuous here).
#   RE-DERIVED BY AUDIT with two real builds rather than argument, since "the
#   carrier makes this vacuous" is exactly the claim that has been measured wrong
#   elsewhere. (a) Assigning to an input from inside the impl region — the only
#   region a variant may touch — is rejected by the ELABORATOR, not by any
#   obligation: `rest cannot be mutated, only variables declared using
#   let mut can be mutated`. So the write is not expressible where a variant is
#   allowed to put it. (b) Making it expressible needs a `mut` binder, which
#   lives in the METHOD HEADER, i.e. the spec view: that variant is rejected by
#   the scope check as `spec view differs (same_spec failed)`, which is a
#   different case out of scope, not this spec tested. Both halves measured, so
#   the class is genuinely inexpressible on this carrier — not merely hard.
#
# DROPPED (AXIOM_TESTS, 2 cases): the sibling consumes one `@ContractOnly`
#   identifier-mangling axiom and probes its soundness and its containment. This
#   bundle consumes NO axiom (`meta.json` `axioms: []`); the recognizers and the
#   mangling are deep-model A-references validated against their real
#   counterparts by axiom_check.py. That is G-AX's lane and this gate ignores
#   AXIOM_TESTS regardless.
#
# NO SOUNDNESS POSITIVE WAS DROPPED for an unclosable proof. Two further reshapes
#   were attempted and abandoned for a TOOLING reason, not a proof-difficulty one,
#   and neither is claimed as a gap: nesting the two recognizer matches (a
#   `match` on the first option whose `none` arm matches the second) and
#   let-binding a recognizer's result before matching on it both fail to
#   ELABORATE at all, with `Failed to parse an assertion without names: WPGen`
#   from Velvet's own weakest-precondition generator — it does not accept a
#   nested/let-bound `match` in that position. That is a fragment limitation of
#   the backend, upstream of any obligation, so no case is written over it. The
#   three positives shipped cover the same reshape axes that ARE expressible
#   (delegate wholesale to the model, inline the framing, split the wildcard).
#   BOTH REPRODUCED BY AUDIT with real builds: the nested `match` and the
#   let-bound recognizer each fail with exactly the quoted `Failed to parse an
#   assertion without names: WPGen` and no obligation is ever reached, so this is
#   a backend-fragment wall and not a proof the port could not close. The audit
#   also landed a FOURTH reshape axis the port did not try and that IS expressible
#   — the two recognizer results swapped in the scrutinee pair, with the arm
#   guards rewritten so gold's precedence is preserved (`| _, some c` first) —
#   which VERIFIES (exit 0). That is the faithful correct counterpart of
#   `weak-branch-precedence-inverted`, and it verifying while that rival is
#   rejected is direct evidence the clause pins the SELECTION FUNCTION and not the
#   scrutinee order: SPEC-TOO-STRONG is refuted on the very axis most likely to
#   host it. It is not shipped as a case only because the three positives already
#   discharge the soundness lane; it is recorded here so the claim is not lost.
#
# BINDER / CLAUSE COVERAGE of the 12 reject witnesses (pts = 12 distinct points,
# no two rivals sharing an input):
#   floatText — `6.62607015e-34` (x2, the reported token), `5` (x4), `5.`, `.5`,
#               `5e-42`, `5.0` (x2), `5e42` (x2): long/short, integer-like,
#               leading-dot, trailing-dot, signed exponent. Varied.
#   rest      — `q_J`, `q_J`(short-text pairing), `std`, `stdx`, `q_J*1q_s`,
#               `_udl`, `1abc`, `` (EMPTY), `L`, `F`, `fudl`, `f`: empty tail,
#               bare lower-case tag char, bare UPPER-case tag char, tag char
#               continued by word chars, underscore-initial name, letter-initial
#               name, DIGIT-initial word run, the reserved name, a NEAR-MISS of
#               the reserved name, and a name followed by more of the surrounding
#               expression. Varied, and NOT held at one value by any rival — the
#               binder that decides the branch is probed at every shape that
#               selects a different branch.
#   Every top-level branch and component of `out = parsedFloatId floatText rest`
#   is attacked: TAG selection (weak-tag-ignores-word-boundary,
#   weak-branch-precedence-inverted), TAG payload
#   (weak-tag-not-folded-into-number), TAG framing
#   (weak-tag-drops-closing-frame), NAME selection
#   (weak-prepatch-no-name-branch), NAME start class
#   (weak-name-start-admits-any-word-char), NAME right boundary
#   (weak-name-takes-whole-tail), NAME-ID length prefix
#   (weak-name-without-length-prefix) and its reserved-name case in BOTH
#   directions — under-applied (weak-name-loses-reserved-abbrev) and
#   over-applied (weak-reserved-abbrev-over-applied) — NAME framing
#   (weak-name-drops-separator), PLAIN framing
#   (weak-plain-drops-closing-frame). The near-miss PAIRS
#   (without-length-prefix vs loses-reserved-abbrev; loses-reserved-abbrev vs
#   over-applied; ignores-word-boundary vs precedence-inverted; plain-framing vs
#   tag-framing) each get separate witnesses at the input that distinguishes
#   them, so no rival's rationale claims a sub-domain the manifest does not
#   demonstrate.
#
# The last three cases were ADDED BY AUDIT, each closing a component the prose
# above previously claimed while no shipped rival reached it: the TAG arm's own
# framing (the plain-branch framing rival leaves that arm byte-identical to gold,
# and its empty-tail witness cannot enter it), the NAME recognizer's START class
# (every other rival keeps `matchSuffixName`'s start test exact, so a spec letting
# a DIGIT open a name would have passed the whole battery), and the
# over-application of the reserved-name abbreviation (the existing rival only
# pins that the abbreviation is not LOST, never that it is not applied too
# widely). Each was machine-checked in both halves: the module fails to verify,
# and its witness elaborates against the rival (exit 0) while `decide` proves the
# same proposition FALSE against the frozen solution (exit 1) — a semantic
# refutation, not a stuck reduction.
AXIOM_TESTS = []
