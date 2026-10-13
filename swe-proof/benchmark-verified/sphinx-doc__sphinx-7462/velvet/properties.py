"""properties.py — G-PBT falsification battery for sphinx-doc__sphinx-7462 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside a ``-- impl-start`` /
``-- impl-end`` region, or inside a ``prove_correct`` tactic body, is changed —
both of which the consumer spec view elides, so ``markers.same_spec`` holds and
each ``prove_correct <name>`` obligation survives with a byte-identical
statement) and swaps in a candidate implementation, checked by the real
verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: it must ELABORATE against the rival and FAIL against
the frozen solution).

DEFENDED SURFACE (TWO contracted rendering operations over the member-count
domain):

  renderSequenceTokens (elts : List (List (List Char)))
      return (out : List (List Char))    ensures out = seqTokens elts
  renderSequenceText   (elts : List (List Char))
      return (out : List Char)           ensures out = seqText elts

Both assemble a comma-separated member group from its ALREADY-RENDERED member
images: the token-list surface (#1) and the source-text surface (#2). Neither
has a precondition (a group may carry zero or more members). Each ``ensures``
pins the result to a fully-unfolded, computable ``def`` over the input carrier
(``seqTokens`` / ``seqText``) — NOT an opaque answer-key oracle (the ``axioms``
region is empty, mapping.md §3), so pinning ``out = seq… elts`` is grounded, not
an echo. Each ``def`` has TWO independent top-level outcomes as a function of
the member count:

  EMPTY  (elts = [])   ↦  the punctuation pair — two tokens ``(`` then ``)`` (#1),
                          the two chars ``()`` (#2).  This is the DISCRIMINATING
                          fix: the empty group that previously crashed / rendered
                          empty.
  NON-EMPTY (elts ≠ []) ↦  the members' images concatenated with a single
                          comma-space separator BETWEEN adjacent members and none
                          at the ends (``List.intercalate``).

SINGLE INPUT BINDER per operation: ``elts`` (the ordered member images). It is
load-bearing on both facets — its EMPTINESS selects the branch, and on the
non-empty branch its length, order and per-member content determine the
interleaving. The reject witnesses drive it across member counts {0, 1, 2}: on
the empty sub-domain they attack the punctuation pair's cardinality and order; at
one member they attack the members being carried through at all; and at TWO
members (w9/w10) they attack the separator and the member ordering, which are
refutable at no smaller input. So the manifest demonstrates the post-image's
dependence on the branch, on the empty rendering's exact token/char sequence, and
on the exact interleaving of the non-empty branch — not on a single pinned shape.

CARRIER NOTE — THE DECIDABLE BOUNDARY. Both ``seqTokens`` and ``seqText`` are
fully-unfolded ``def``s (a two-arm ``match`` over ``List.intercalate``); the
member images are the arbitrary inputs ``elts`` and the spec assumes nothing
about them. So a witness at a CONCRETE literal input reduces by kernel
computation and closes by ``decide`` — no opaque callee blocks it and no
conditioning on the carrier is needed. A witness reaches the post-image through
Velvet's own tester machinery (``renderSequence…Tester elts = false`` says the
extracted program's result violates the postcondition at that concrete input),
checked in a file whose ``prove_correct`` block has been stripped so no tactic
script can mask the verdict. Every witness below was run both ways with
``scripts/lean_verify.sh``: it elaborates green against its rival and
``decide``-refutes (fails) against the frozen solution.

ADVERSARIAL READ of the sibling's classes on this carrier:
  * SOUNDNESS / positive controls — APPLY. A structurally different but
    behaviourally identical impl (return the grounded model directly; reorder the
    branches non-empty-first) must verify, else the spec is SPEC-TOO-STRONG on
    the shape of the impl. Both are supplied, each editing BOTH sites; the proof
    is retuned to ``loom_solve`` (the frozen ``loom_solve; rfl`` over-solves once
    the impl reduces definitionally, so the trailing ``rfl`` becomes "no goals").
  * ADMISSIBILITY — no precondition is declared, so the sibling's "a normal input
    satisfies the ``Requires``" probe is degenerate here (no ``require`` clause,
    no permission surface). The residual risk on a total domain is a DEGENERATE
    post-image, so the case is re-aimed at an in-region ``assert`` pinning BOTH
    outcomes at F2P-shaped inputs (empty group, one-member group, two-member
    group) so the post-image is demonstrably non-degenerate; the impl is kept
    verbatim so the method's own obligation still discharges.
  * FRAME-MUTATION — VACUOUS on this backend. The sibling records this class as
    inapplicable already (``elts`` is a plain immutable sequence VALUE carrying no
    heap permission). Lean/Velvet are referentially transparent: ``elts`` is an
    immutable ``List`` declared read-only (not ``mut``), there is no heap, no
    aliasing, no fractional permission. No read-only input to overwrite, no frame
    clause to violate; the class has no carrier analogue and no substitute is
    fabricated.
  * UNGROUNDED-ORACLE ECHO — N/A. The post-image is pinned to ``seqTokens elts`` /
    ``seqText elts``, fully-unfolded ``def``s over the method's own argument;
    there is no answer-key term a wrong impl could echo (the sibling reached the
    same conclusion — its ``join_tokens`` / ``join_comma`` were grounded folds,
    not oracles). The cheapest correct impl computes the rendering honestly, which
    the positives cover.
  * PARTIAL-DOMAIN / VALUE — carries the reject lane: each rival gets most of the
    domain right yet diverges on one sub-domain (the empty group rendered as no
    tokens / the empty string — the pre-patch regression; the empty pair rendered
    with the wrong cardinality, the wrong order, a missing bracket; or the empty
    rendering forced onto EVERY group, dropping the members).

DIVERGENCE LANE. The sibling's re-expressed pre-patch rivals are partial-domain
VALUE breaks (empty token sequence / empty string on the empty group), not
``diverge-*`` / ``nonterm-*`` / ``weak-diverge`` cases, so there is no divergence
class to port, and nothing ships in this lane. The REASON is now two facts, and
an earlier revision of this note had the first of them exactly backwards: it
said this bundle sets ``loom.semantics.termination "partial"`` and that a
non-terminating impl therefore satisfies every ``ensures`` on an unreachable
exit and VERIFIES. Both halves are false. The bundle sets
``set_option loom.semantics.termination "total"``, and in Loom that option is
itself what opens ``TotalCorrectness`` scope, so the option and the ``open``
cannot disagree. Under ``total`` a postcondition is claimed of ALL runs, not
only terminating ones, and Loom's total loop generator emits a per-iteration
side condition that the loop's measure STRICTLY DECREASES. A diverging prefix is
consequently REJECTED, in both of its shapes: with no ``decreasing`` clause the
elaborator refuses outright (``Decreasing annotations are required in total
correctness semantics``), and with the clause present but its measure constant
the descent goal ITSELF fails, under the clause's own name
(``case «decreasing_1: q» ... q < q``). So there is no vacuous satisfaction left
to exploit and no spec hole to escalate. The second fact is why no case ships
anyway: this impl is LOOP-FREE, so there is no loop for a divergence rival to
attack in the first place. Even where a loop exists the class stays
documentation rather than a case, because an ``expect="reject"`` case needs a
witness that ELABORATES against the rival, and a diverging rival's module does
not compile at all (the descent obligation fails at the ``method``, upstream of
any appended tester), so the case would score MALFORMED rather than rejecting.

AXIOM lane: EMPTY. The bundle declares no ``axiom`` (mapping.md §3: the changed
ops are modeled deeply and concretely, validated by G-CONF), and the sibling's
``AXIOM_TESTS`` is likewise empty. Nothing for the axiom lane to probe; this gate
ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "sphinx-doc__sphinx-7462"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# The two frozen impl blocks. Each anchor lies WHOLLY inside one
# `-- impl-start`/`-- impl-end` region and is unique in Solution.lean (both
# facts asserted at load by _swap): the token surface (#1) is typed
# `List (List Char)` and renders the empty pair as two tokens; the text surface
# (#2) is typed `List Char` and renders it as the two chars "()". Every rival
# edits ONLY one of these, in isolation.
# ---------------------------------------------------------------------------
_IMPL_A = """    let result : List (List Char) := match elts with
      | []  => ["(".toList, ")".toList]
      | _   => List.intercalate [", ".toList] elts
    return result"""

_IMPL_B = """    let result : List Char := match elts with
      | []  => "()".toList
      | _   => List.intercalate ", ".toList elts
    return result"""

assert _BASE.count(_IMPL_A) == 1, "impl-A anchor drift — re-sync _IMPL_A"
assert _BASE.count(_IMPL_B) == 1, "impl-B anchor drift — re-sync _IMPL_B"

# ---- frozen proof bodies (tactic scripts only; elided from the spec view). The
# ---- positives retune these to a bare `loom_solve`: once the impl returns a
# ---- value that reduces definitionally to `seq… elts`, `loom_solve` closes the
# ---- equality and the frozen trailing `rfl` becomes an over-solve ("no goals").
_PROOF_A = "prove_correct renderSequenceTokens by\n  loom_solve\n  rfl"
_PROOF_B = "prove_correct renderSequenceText by\n  loom_solve\n  rfl"
assert _BASE.count(_PROOF_A) == 1, "proof-A anchor drift"
assert _BASE.count(_PROOF_B) == 1, "proof-B anchor drift"
_PROOF_A_FLAT = "prove_correct renderSequenceTokens by\n  loom_solve"
_PROOF_B_FLAT = "prove_correct renderSequenceText by\n  loom_solve"

# ---- site-A impl-start anchor (the marker plus the token-typed `let` line — the
# ---- `-- impl-start` marker itself repeats once per method, so it is qualified
# ---- by the following line to stay unique). The admissibility case inserts an
# ---- in-region `assert` immediately after the marker, keeping the whole gold
# ---- body of site A.
_IMPL_START_A = "    -- impl-start\n    let result : List (List Char) := match elts with"
assert _BASE.count(_IMPL_START_A) == 1, "impl-start-A anchor drift"


# ---- witness preambles. The spec is a `method` CONTRACT, not a bare predicate,
# ---- so a witness reaches the post-image through Velvet's tester machinery:
# ---- `renderSequence…Tester elts = false` says the extracted program's result
# ---- violates the method's postcondition at that concrete input. Checked in a
# ---- file whose `prove_correct` block has been stripped. Every argument is a
# ---- concrete literal so `decide` reduces the extracted program directly (both
# ---- `def`s are fully unfolded — no opaque callee gets stuck).
def _witA(inp):
    return ("extract_program_for renderSequenceTokens\n"
            "prove_precondition_decidable_for renderSequenceTokens\n"
            "prove_postcondition_decidable_for renderSequenceTokens\n"
            "derive_tester_for renderSequenceTokens\n\n"
            f"example : renderSequenceTokensTester {inp} = false := by\n  decide\n")


def _witB(inp):
    return ("extract_program_for renderSequenceText\n"
            "prove_precondition_decidable_for renderSequenceText\n"
            "prove_postcondition_decidable_for renderSequenceText\n"
            "derive_tester_for renderSequenceText\n\n"
            f"example : renderSequenceTextTester {inp} = false := by\n  decide\n")


# === POSITIVE CONTROLS (soundness) ========================================
# Direct-model: return the grounded pure model at BOTH sites. Maximally
# structurally different from the frozen two-arm match; `out` IS `seq… elts`, so
# the ensures holds on the whole domain and `loom_solve` closes.
POS_DIRECT = _swap(
    _swap(
        _swap(_swap(_BASE, _IMPL_A, "    return seqTokens elts"),
              _IMPL_B, "    return seqText elts"),
        _PROOF_A, _PROOF_A_FLAT),
    _PROOF_B, _PROOF_B_FLAT)

# Branch-reorder: handle the NON-EMPTY case first (cons pattern), fall through to
# the empty end case. Same executable meaning at both sites; a faithful reshape.
_REORDER_A = """    let result : List (List Char) := match elts with
      | a :: rest => List.intercalate [", ".toList] (a :: rest)
      | []        => ["(".toList, ")".toList]
    return result"""
_REORDER_B = """    let result : List Char := match elts with
      | a :: rest => List.intercalate ", ".toList (a :: rest)
      | []        => "()".toList
    return result"""
POS_REORDER = _swap(
    _swap(
        _swap(_swap(_BASE, _IMPL_A, _REORDER_A), _IMPL_B, _REORDER_B),
        _PROOF_A, _PROOF_A_FLAT),
    _PROOF_B, _PROOF_B_FLAT)


# === ADMISSIBILITY ========================================================
# No precondition is declared, so the sibling's "a normal input satisfies the
# Requires" probe is degenerate. Re-aimed at post-image non-degeneracy: an
# in-region assert (site A) pins BOTH outcomes at three F2P-shaped inputs — the
# empty group renders as the two-token pair, a one-member group as that member's
# image, a two-member group as the images comma-separated — three genuinely
# distinct post-images. The impl is kept verbatim so `out = seqTokens elts` still
# discharges; the proof gains a `decide` arm to clear the assert goal.
_ADMISS_A = ("""    -- impl-start
    assert (with_name_prefix `admiss (
      seqTokens [] = ["(".toList, ")".toList] ∧
      seqTokens [["i".toList]] = ["i".toList] ∧
      seqTokens [["i".toList], ["j".toList]]
        = ["i".toList, ", ".toList, "j".toList]))
    let result : List (List Char) := match elts with""")
ADMISS = _swap(
    _swap(_BASE, _IMPL_START_A, _ADMISS_A),
    _PROOF_A,
    "prove_correct renderSequenceTokens by\n  loom_solve\n  all_goals first | rfl | decide")


# === UNIQUENESS / REJECT rivals ===========================================

# --- W1 (site A) PRE-PATCH regression: drop the empty special-case and assemble
# unconditionally. Correct on every NON-EMPTY group; wrong only on the empty
# sub-domain, where `List.intercalate [", "] []` is the EMPTY token sequence (the
# abstract image of the `.pop()`-on-[] crash), not the two-token pair.
W1_PREPATCH_TOK = _swap(_BASE, _IMPL_A, "    return List.intercalate [\", \".toList] elts")

# --- W2 (site B) PRE-PATCH regression: drop the empty special-case and join
# unconditionally. Correct on every NON-EMPTY group; wrong only on empty, where
# `List.intercalate ", " []` is the EMPTY string, not "()".
W2_PREPATCH_TXT = _swap(_BASE, _IMPL_B, "    return List.intercalate \", \".toList elts")

# --- W3 (site A) WRONG empty rendering, ONE token: render the empty group as a
# SINGLE token whose text is "()" rather than the TWO separate tokens ( and ).
_W3_A = """    let result : List (List Char) := match elts with
      | []  => ["()".toList]
      | _   => List.intercalate [", ".toList] elts
    return result"""
W3_WRONGTOK = _swap(_BASE, _IMPL_A, _W3_A)

# --- W4 (site A) SWAPPED-order empty rendering: render the empty group as the
# two tokens ) ( (close then open) instead of ( ).
_W4_A = """    let result : List (List Char) := match elts with
      | []  => [")".toList, "(".toList]
      | _   => List.intercalate [", ".toList] elts
    return result"""
W4_SWAPTOK = _swap(_BASE, _IMPL_A, _W4_A)

# --- W5 (site B) WRONG empty rendering, ONE char: render the empty group as the
# single character "(" instead of "()" (missing the close bracket).
_W5_B = """    let result : List Char := match elts with
      | []  => "(".toList
      | _   => List.intercalate ", ".toList elts
    return result"""
W5_WRONGTXT = _swap(_BASE, _IMPL_B, _W5_B)

# --- W6 (site B) SWAPPED-char empty rendering: render the empty group as ")("
# instead of "()".
_W6_B = """    let result : List Char := match elts with
      | []  => ")(".toList
      | _   => List.intercalate ", ".toList elts
    return result"""
W6_SWAPTXT = _swap(_BASE, _IMPL_B, _W6_B)

# --- W7 (site A) UNIVERSAL empty rendering: always emit the two tokens ( )
# regardless of members. Correct on the empty sub-domain; wrong on every
# NON-EMPTY group (drops the members). Attacks the NON-EMPTY clause.
W7_ALWAYSEMPTY_TOK = _swap(_BASE, _IMPL_A, "    return [\"(\".toList, \")\".toList]")

# --- W8 (site B) UNIVERSAL empty rendering: always return "()" regardless of
# members. Correct on empty; wrong on every NON-EMPTY group. The site-B analogue
# of W7 (attacks the text surface's NON-EMPTY clause).
W8_ALWAYSEMPTY_TXT = _swap(_BASE, _IMPL_B, "    return \"()\".toList")

# --- W9 (site A) SEPARATOR DROPPED: keep the empty pair and keep every member's
# image in order, but concatenate the members with NO separator token between
# them. Correct on the empty group AND on every ONE-member group (with one member
# there is no adjacent pair, so intercalate inserts nothing and `flatten` agrees);
# wrong from TWO members up, where the comma-space token is missing. This is the
# only rival that needs a 2-member input to refute, which is exactly the point:
# w1–w8 all refute at member count 0 or 1, so without this case the SEPARATOR
# half of the non-empty clause is never attacked and a spec pinning only "the
# members' images in order" would pass the whole battery.
_W9_A = """    let result : List (List Char) := match elts with
      | []  => ["(".toList, ")".toList]
      | _   => elts.flatten
    return result"""
W9_NOSEP_TOK = _swap(_BASE, _IMPL_A, _W9_A)

# --- W10 (site B) MEMBER ORDER reversed: keep the empty pair, keep the
# comma-space separator, keep the member count — but emit the members in reverse.
# Correct on the empty group and on every one-member group; wrong from TWO
# distinct members up. Attacks the ORDER half of the non-empty clause on the text
# surface (w9 attacks the separator half on the token surface); nothing else in
# the reject lane pins that the members are carried through in their input order.
_W10_B = """    let result : List Char := match elts with
      | []  => "()".toList
      | _   => List.intercalate ", ".toList elts.reverse
    return result"""
W10_REVORDER_TXT = _swap(_BASE, _IMPL_B, _W10_B)


SPEC_TESTS = [
    # ---- POSITIVE CONTROLS -------------------------------------------------
    {
        "id": "pos-direct-model",
        "kind": "soundness",
        "expect": "verify",
        "module": POS_DIRECT,
        "rationale": (
            "cheapest honest correct impl at BOTH sites: return the grounded "
            "models `seqTokens elts` / `seqText elts` directly (no match). `out` IS "
            "the pinned model, so both ensures hold on the whole domain and the "
            "reproof is a bare `loom_solve` (the frozen trailing `rfl` would "
            "over-solve). If this fails to verify the spec is over-fit to the "
            "match-expression shape (SPEC-TOO-STRONG). Also the no-ungrounded-echo "
            "control: the models ARE the real work, so a direct return is correct, "
            "not a cheat. (Sibling: pos-reorder — a structurally-different correct "
            "impl.)"),
    },
    {
        "id": "pos-branch-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": POS_REORDER,
        "rationale": (
            "branch reorder at both sites: handle the NON-EMPTY case first (cons "
            "pattern), fall through to the empty end case — the sibling's positive "
            "shape, carried over. Same executable meaning, so `out = seq… elts` "
            "still holds on the whole domain; the reproof is `loom_solve`. A correct "
            "reshape must verify, else SPEC-TOO-STRONG (over-fit to the "
            "empty-branch-first ordering). (Sibling: pos-reorder.)"),
    },

    # ---- ADMISSIBILITY -----------------------------------------------------
    {
        "id": "admiss-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": ADMISS,
        "rationale": (
            "no precondition is declared, so the sibling's precondition-admissibility "
            "probe is degenerate here; re-aimed at post-image non-degeneracy. An "
            "in-region assert pins BOTH outcomes at three F2P-shaped inputs: the "
            "empty group renders as the two-token punctuation pair, a one-member "
            "group as that member's image, a two-member group as the images with one "
            "comma-space separator between them — three distinct outcomes. The assert "
            "must discharge (else the obligation is degenerate / the precondition too "
            "strong); the impl is kept verbatim so `out = seqTokens elts` still "
            "verifies. (Sibling: admiss-shapes, re-aimed from precondition "
            "admissibility to post-image non-degeneracy — this backend has no "
            "`require` and no permission surface.)"),
    },

    # ---- UNIQUENESS / SPEC-TOO-WEAK rivals ---------------------------------
    {
        "id": "w1-prepatch-tok",
        "kind": "uniqueness",
        "expect": "reject",
        "module": W1_PREPATCH_TOK,
        "refinement": (
            "the faithful real patch is the literal pre-patch token loop with NO "
            "empty-group guard: it assembles the members and trims the trailing "
            "separator, and on the empty group that trailing-trim step operates on an "
            "empty accumulator and raises the IndexError in the bug report. The "
            "failing scenario that adds an empty-group annotation would error instead "
            "of emitting the punctuation pair — it does NOT resolve. Correct on every "
            "non-empty group (a true partial-domain break)."),
        "rationale": (
            "REJECT from `out = seqTokens elts` via the EMPTY outcome: on `elts = []` "
            "the spec pins the two-token pair `[\"(\", \")\"]`, but "
            "`List.intercalate [\", \"] []` is the EMPTY token sequence. Verifying "
            "would be SPEC-TOO-WEAK (the empty-group regression unpinned). Refuted on "
            "the empty sub-domain. (Sibling: w1-prepatch-tok, re-expressed in the "
            "impl region.)"),
        "witness": _witA("[]"),
    },
    {
        "id": "w2-prepatch-txt",
        "kind": "uniqueness",
        "expect": "reject",
        "module": W2_PREPATCH_TXT,
        "refinement": (
            "the faithful real patch is the literal pre-patch join with NO empty-group "
            "guard: joining the member images with the comma-space separator. On the "
            "empty group it produces the EMPTY string, not the empty pair. The failing "
            "scenario that renders an empty group asserts \"()\" and gets \"\" — it "
            "does NOT resolve. Correct on every non-empty group (a partial-domain "
            "break)."),
        "rationale": (
            "REJECT from `out = seqText elts` via the EMPTY outcome: on `elts = []` "
            "the spec pins the two chars `\"()\"`, but `List.intercalate \", \" []` is "
            "the empty char list. Verifying would be SPEC-TOO-WEAK (the empty-group "
            "regression unpinned). Refuted on the empty sub-domain. (Sibling: "
            "w2-prepatch-txt.)"),
        "witness": _witB("[]"),
    },
    {
        "id": "w3-wrongtok-one-node",
        "kind": "uniqueness",
        "expect": "reject",
        "module": W3_WRONGTOK,
        "refinement": (
            "a real patch emitting the empty pair as ONE punctuation node carrying "
            "the text \"()\" instead of two separate ( and ) nodes. The failing "
            "scenario expects exactly TWO punctuation nodes ( then ) positionally; one "
            "combined node fails the node-shape assertion — it does NOT resolve. "
            "Correct on every non-empty group."),
        "rationale": (
            "REJECT from `out = seqTokens elts` via the EMPTY outcome: a length-1 "
            "token sequence `[\"()\"]` != the length-2 pair `[\"(\", \")\"]` the spec "
            "pins. Defends the token COUNT/identity on the empty sub-domain. Verifying "
            "would be SPEC-TOO-WEAK. (Sibling: w3-wrongtok-one-node.)"),
        "witness": _witA("[]"),
    },
    {
        "id": "w4-swaptok-order",
        "kind": "uniqueness",
        "expect": "reject",
        "module": W4_SWAPTOK,
        "refinement": (
            "a real patch emitting the bracket nodes reversed ( ) node then ( node ). "
            "The failing scenario asserts ( BEFORE ) positionally; reversed order "
            "fails the node-shape assertion — it does NOT resolve. Correct on every "
            "non-empty group."),
        "rationale": (
            "REJECT from `out = seqTokens elts` via the EMPTY outcome: "
            "`[\")\", \"(\"]` is element-wise reversed and != the pinned "
            "`[\"(\", \")\"]`. Value-level ORDER defense on the empty sub-domain "
            "(distinct from w3, which attacks the count). Verifying would be "
            "SPEC-TOO-WEAK. (Sibling: w4-swaptok-order.)"),
        "witness": _witA("[]"),
    },
    {
        "id": "w5-wrongtxt-one-char",
        "kind": "uniqueness",
        "expect": "reject",
        "module": W5_WRONGTXT,
        "refinement": (
            "a real patch rendering the empty group as \"(\" (missing the close "
            "bracket). The failing scenario asserts exactly \"()\" — it gets \"(\" and "
            "does NOT resolve. Correct on every non-empty group."),
        "rationale": (
            "REJECT from `out = seqText elts` via the EMPTY outcome: `\"(\"` (length "
            "1) != the pinned `\"()\"`. Partial-domain break on the empty sub-domain, "
            "missing the close bracket. Verifying would be SPEC-TOO-WEAK. (Sibling: "
            "w5-wrongtxt-one-char.)"),
        "witness": _witB("[]"),
    },
    {
        "id": "w6-swaptxt-order",
        "kind": "uniqueness",
        "expect": "reject",
        "module": W6_SWAPTXT,
        "refinement": (
            "a real patch rendering the empty group as \")(\" (reversed bracket "
            "pair). The failing scenario asserts \"()\" exactly — it gets \")(\" and "
            "does NOT resolve. Correct on every non-empty group."),
        "rationale": (
            "REJECT from `out = seqText elts` via the EMPTY outcome: `\")(\"` is "
            "char-reversed and != the pinned `\"()\"`. Value-level char-ORDER defense "
            "on the empty sub-domain (distinct from w5, which drops a char). Verifying "
            "would be SPEC-TOO-WEAK. (Sibling: w6-swaptxt-order.)"),
        "witness": _witB("[]"),
    },
    {
        "id": "w7-always-empty-tok",
        "kind": "uniqueness",
        "expect": "reject",
        "module": W7_ALWAYSEMPTY_TOK,
        "refinement": (
            "a real patch unconditionally emitting the bare pair ( ) with no member "
            "loop renders EVERY group as an empty pair, dropping all members. The "
            "existing non-empty-group scenarios that assert the member tokens would "
            "lose them — it does NOT resolve. Correct only on the empty group."),
        "rationale": (
            "REJECT from `out = seqTokens elts` via the NON-EMPTY outcome: a fixed "
            "2-token output != the member interleaving for any non-empty group. "
            "Attacks the NON-EMPTY clause (the opposite side from the prepatch "
            "rivals), so the reject set exercises `elts ≠ []` too. Refuted at a "
            "one-member group. Verifying would be SPEC-TOO-WEAK. (Sibling: "
            "w7-always-empty-tok.)"),
        "witness": _witA("[[\"a\".toList]]"),
    },
    {
        "id": "w8-always-empty-txt",
        "kind": "uniqueness",
        "expect": "reject",
        "module": W8_ALWAYSEMPTY_TXT,
        "refinement": (
            "a real patch unconditionally returning \"()\" renders every group as the "
            "empty pair, dropping the members' text. The existing non-empty-group "
            "scenarios that assert the joined member text would lose it — it does NOT "
            "resolve. Correct only on the empty group."),
        "rationale": (
            "REJECT from `out = seqText elts` via the NON-EMPTY outcome: the fixed "
            "\"()\" != the members joined by comma-space for any non-empty group. The "
            "site-B analogue of w7 — attacks the text surface's NON-EMPTY clause, so "
            "BOTH modeled functions have their non-empty clause attacked. Refuted at a "
            "one-member group. Verifying would be SPEC-TOO-WEAK. (No direct sibling "
            "case — the sibling only carried the site-A always-empty rival; ADDED to "
            "defend the modeled text surface symmetrically.)"),
        "witness": _witB("[\"a\".toList]"),
    },
    {
        "id": "w9-nosep-tok",
        "kind": "uniqueness",
        "expect": "reject",
        "module": W9_NOSEP_TOK,
        "refinement": (
            "a real patch that keeps the empty-group guard and appends each "
            "member's rendered nodes in order but never emits the comma-space "
            "punctuation node between them. Every member node survives, in order, "
            "so a one-member group is indistinguishable from correct; a "
            "two-member group renders them abutted with no separator. The "
            "existing multi-member scenarios assert the separator node between "
            "adjacent members — it does NOT resolve. Correct on the empty group "
            "and on every one-member group."),
        "rationale": (
            "REJECT from `out = seqTokens elts` via the SEPARATOR half of the "
            "NON-EMPTY outcome: `elts.flatten` agrees with "
            "`List.intercalate [\", \"] elts` at member counts 0 and 1 and "
            "diverges from 2 up, where the spec pins one comma-space token "
            "between adjacent members. Refuted at a TWO-member group — the only "
            "case in this battery whose witness needs member count 2, so it is "
            "what makes `elts.length` load-bearing beyond the empty/non-empty "
            "split. Verifying would be SPEC-TOO-WEAK (the separator unpinned). "
            "(No sibling counterpart; ADDED by audit — w1–w8 all refute at member "
            "count 0 or 1, leaving the separator clause unattacked.)"),
        "witness": _witA("[[\"a\".toList], [\"b\".toList]]"),
    },
    {
        "id": "w10-revorder-txt",
        "kind": "uniqueness",
        "expect": "reject",
        "module": W10_REVORDER_TXT,
        "refinement": (
            "a real patch that keeps the empty-group guard and the comma-space "
            "separator but joins the member images in reverse order. Member count "
            "and separators are right; only the ordering is wrong, so it is "
            "indistinguishable from correct on any group of fewer than two "
            "members. The existing multi-member scenarios assert the members in "
            "source order — it does NOT resolve. Correct on the empty group and "
            "on every one-member group."),
        "rationale": (
            "REJECT from `out = seqText elts` via the ORDER half of the NON-EMPTY "
            "outcome: joining `elts.reverse` agrees with joining `elts` at member "
            "counts 0 and 1 and diverges from 2 distinct members up. Pins that "
            "the members are carried through in their INPUT order, which no other "
            "reject case does (w7/w8 drop the members entirely; w4/w6 attack "
            "order only inside the empty group's punctuation). Refuted at a "
            "TWO-member group. Verifying would be SPEC-TOO-WEAK. (No sibling "
            "counterpart; ADDED by audit alongside w9 to attack the non-empty "
            "clause's interleaving on BOTH surfaces at member count 2.)"),
        "witness": _witB("[\"a\".toList, \"b\".toList]"),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery ships 9 SPEC cases (1
# soundness positive, 1 admissibility, 7 uniqueness rivals) plus an EMPTY AXIOM
# lane (AXIOM_TESTS = []). This bundle models the SAME two rendering surfaces
# concretely: `renderSequenceTokens`/`seqTokens` (site A, the token list) and
# `renderSequenceText`/`seqText` (site B, the source text). Every sibling case is
# accounted for below.
#
#   sibling case            kind          -> here                      disposition
#   ----------------------------------------------------------------------------------
#   pos-reorder             soundness     -> pos-branch-reorder        PORTED
#                                            (+ pos-direct-model       ADDED)
#   admiss-shapes           admissibility -> admiss-nondegenerate      RE-AIMED
#   w1-prepatch-tok         uniqueness    -> w1-prepatch-tok           PORTED
#   w2-prepatch-txt         uniqueness    -> w2-prepatch-txt           PORTED
#   w3-wrongtok-one-node    uniqueness    -> w3-wrongtok-one-node      PORTED
#   w4-swaptok-order        uniqueness    -> w4-swaptok-order          PORTED
#   w5-wrongtxt-one-char    uniqueness    -> w5-wrongtxt-one-char      PORTED
#   w6-swaptxt-order        uniqueness    -> w6-swaptxt-order          PORTED
#   w7-always-empty-tok     uniqueness    -> w7-always-empty-tok       PORTED
#                                            (+ w8-always-empty-txt    ADDED)
#                                            (+ w9-nosep-tok           ADDED/audit)
#                                            (+ w10-revorder-txt       ADDED/audit)
#   AXIOM_TESTS (none)      axiom         -> (none)                    N/A (G-AX)
#
# 7 uniqueness ported verbatim in argument (carrier re-expressed), 1 admissibility
# re-aimed, 1 soundness ported (+ 1 soundness and 3 uniqueness ADDED: one for
# symmetric coverage of the second modeled surface, two by audit for the
# separator/order halves of the non-empty clause); axiom lane empty.
#
# ADDED (2, no sibling counterpart, both machine-checked real cases):
#   * pos-direct-model — the sibling's single positive is a branch reorder; on this
#     carrier a second, maximally-different correct shape (direct return of the
#     grounded model at both sites) is cheap and defends the soundness surface from
#     a completely different impl shape as well as from a minimal branch reorder.
#   * w8-always-empty-txt — the sibling carried the always-empty rival only for the
#     token surface (w7). This bundle models the text surface as an independent
#     `method`/`ensures` too, so its NON-EMPTY clause needs its own attacker; w8 is
#     the site-B analogue of w7 (a real divergence with a machine-checked witness).
#
# ADDED BY AUDIT (2 more, both machine-checked; the gap they close was measured):
#   * w9-nosep-tok / w10-revorder-txt — before these, EVERY reject case refuted at
#     member count 0 or 1, so the non-empty clause was pinned only up to "the
#     members are present". Two NEW wrong impls that agree with the frozen one at
#     counts 0 and 1 (drop the separator; reverse the members) were built during the
#     audit and both are rejected, refuted at count 2 — so they are shipped as
#     cases rather than merely reported. They are the reason `elts.length` is now
#     load-bearing past the empty/non-empty split.
#
# FRAME-MUTATION: VACUOUS. Referentially-transparent backend; `elts` is an
#   immutable read-only value (not `mut`), no heap, no aliasing, no permission
#   system. The sibling ALSO records this class inapplicable (a plain PSeq value
#   carries no heap permission). No substitute fabricated.
# DIVERGENCE - the class is INAPPLICABLE to this impl and CLOSED BY THE
#   SEMANTICS against any rival that manufactures it. Every frozen impl region
#   is LOOP-FREE (straight-line ``let`` over immutable values, no loop and no
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
# BINDER / CLAUSE / POINT COVERAGE. Each `ensures` has ONE binder, `elts`, and TWO
#   independent outcomes (EMPTY / NON-EMPTY). Both are attacked on BOTH functions:
#     * site A EMPTY   — w1 (empty-token-seq), w3 (wrong count), w4 (wrong order)
#     * site A NON-EMPTY — w7 (members dropped), w9 (separator dropped)
#     * site B EMPTY   — w2 (empty string), w5 (missing char), w6 (wrong order)
#     * site B NON-EMPTY — w8 (members dropped), w10 (member order reversed)
#   The reject witnesses drive `elts` across member counts {0, 1, 2}: the empty
#   sub-domain (w1–w6, `elts = []`), a one-member group (w7 `[["a"]]`, w8
#   `["a"]`), and a TWO-member group (w9 `[["a"],["b"]]`, w10 `["a","b"]`). The
#   two-member points are load-bearing and not decorative: w9 and w10 are each
#   OBSERVATIONALLY CORRECT at member counts 0 and 1, so they are refutable only
#   at count 2 — which is what separates "the members appear" (w7/w8 already pin
#   that) from "the members appear IN ORDER, separated by exactly one comma-space"
#   (w10 / w9). Both positives and the admissibility assert exercise 0/1/2-member
#   inputs. Within the empty sub-domain the punctuation pair's cardinality (w3/w5)
#   and order (w4/w6) are independently pinned. No binder is held at a single
#   value across the reject set.
#
# AXIOM_TESTS: empty. The bundle declares no axiom (mapping.md §3: the ops are
#   modeled deeply and concretely, validated by G-CONF); the sibling's AXIOM_TESTS
#   is likewise empty. This gate ignores AXIOM_TESTS regardless.
AXIOM_TESTS = []
