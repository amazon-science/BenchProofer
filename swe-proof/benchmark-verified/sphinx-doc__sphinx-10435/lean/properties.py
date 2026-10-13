"""properties.py — G-PBT falsification battery for sphinx-doc__sphinx-10435 (lean).

NOT a Lean file; a record of adversarial cases the G-PBT gate executes against
the FROZEN spec in ``Solution.lean``. Each SPEC case is a full ``Solution.lean``
variant whose ONLY edits live inside the ``-- impl-start`` / ``-- impl-end``
region (and, for a case that legitimately re-proves, inside the
``-- proof-start`` / ``-- proof-end`` region), so ``markers.same_spec`` holds
byte-for-byte and every ``theorem correct_inlineCode`` STATEMENT stays
byte-identical. ``expect:"verify"`` passes iff (in scope AND the file elaborates
with the obligation closed); ``expect:"reject"`` passes iff (in scope AND it does
NOT verify AND the case's refutation ``witness`` holds of the rival while FAILING
on the frozen solution).

DEFENDED SURFACE (one modeled total function over a ``List Char`` carrier).
``inlineCode hlcode`` produces the exact character sequence emitted for an inline
highlighted code fragment given the highlighter output ``hlcode``. The
postcondition is a single rigid functional equality, fully GROUNDED in the input:

    result = dropLastN 15 (rstripWs (replaceAll verbOpen upquoteOpen hlcode))
             ++ closingTail

where ``verbOpen`` / ``upquoteOpen`` / ``closingTail`` are fixed literal
constants (fully transparent), ``replaceAll`` / ``rstripWs`` / ``dropLastN`` are
deep-modeled total helpers, and there is no opaque callee — the whole clause
computes on concrete inputs. There is thus NO ungrounded answer-key oracle to
echo; the honest analogues are the POSITIVE CONTROLS.

The equality has EIGHT independent, separately-attackable components, each
attacked by at least one rival below:

  * the OPENING rewrite carries a trailing comment marker (``upquoteOpen`` ends
    in ``%``), so the newline the highlighter emits after the opening delimiter
    is comment-suppressed rather than surviving as a leading inter-token space;
  * the OPENING rewrite happens AT ALL (``replaceAll`` is not the identity), so
    the highlighter's own opening delimiter does not survive into the output;
  * the OPENING rewrite fires at EVERY occurrence, not merely the leading one
    (``replaceAll``, not a first-occurrence substitution);
  * the TRAILER slice drops exactly fifteen trailing characters — not fourteen
    (which would leave the pre-delimiter newline in place) and not sixteen
    (which would eat the last retained body character);
  * the trailing-whitespace strip runs BEFORE the slice (``dropLastN 15
    (rstripWs hl)``, not ``dropLastN 15 hl`` and not ``rstripWs (dropLastN 15
    hl)``), so the fifteen-character run is counted from the last
    non-whitespace character;
  * the strip removes the WHOLE default whitespace set (``isTrailWs``: space,
    tab, newline, carriage return, vertical tab, form feed), not a proper subset
    of it;
  * the rewrite runs BEFORE the strip-and-slice, not after it (so a fragment too
    short to survive the slice intact is still rewritten);
  * the CLOSING tail begins with a comment marker (``closingTail`` starts with
    ``%``) before the newline and braces, so the trailing newline is likewise
    comment-suppressed.

ADVERSARIAL READ of the nagini classes on THIS carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS. The nagini bundle held ``content`` at
    a fractional (read-only) permission and its MANDATORY frame probe wrote
    through that half-permission (``content[0] = pct``) to fake a postcondition
    match, expecting rejection for INSUFFICIENT PERMISSION. Lean is referentially
    transparent: the input carries no heap permission, there is no read-only
    half to overwrite and no aliasing to exploit. The nagini ``frame-mut-write``
    case has no expressible instance here and no substitute is fabricated for it.

  * PARTIAL-DOMAIN / VALUE — APPLIES. Every nagini value rival (drop the trailing
    suppressor, drop the opening suppressor, the full pre-patch, off-by-one on
    the content copy) re-expresses as a component deviation in the functional
    equality and is carried over below. The nagini content off-by-one — which
    SHORTENS the emitted body by one character — maps to
    ``weak-trailer-off-by-one-long`` (``dropLastN 16``), which eats the last
    retained body character; ``weak-trailer-off-by-one`` (``dropLastN 14``) is the
    opposite direction and does NOT cover it, so both are carried.

  * UNGROUNDED-ORACLE ECHO — VACUOUS. The postcondition is grounded in the input
    (see above); there is no answer key to echo. The honest analogues are the
    positive controls (``pos-*``, ``admiss-*``) that must verify.

  * AXIOM lane — dropped (belongs to G-AX). meta.json declares no consumed
    ``axiom … _prop`` and no opaque callees, so there is no axiom-soundness
    obligation for this gate.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen ``simp only`` script is tuned to the
frozen impl's form — so a rejection alone attributes nothing to the spec. Every
``expect="reject"`` case therefore carries a Lean snippet proving the rival
CONTRADICTS the spec predicate at one CONCRETE input. Because ``replaceAll`` is
defined by well-founded recursion it does not reduce under ``decide`` directly;
each witness therefore first proves ``replaceAll`` at its concrete input equal to
a normal form via ``simp`` (the input is chosen so the rewrite either fires once
at the head or never), rewrites it in, and then ``decide``s the resulting ground
equality. For the suffix-only rivals (closing-tail deviation) the shared prefix
cancels via ``List.append_cancel_left_eq`` and the input can be empty. Each
witness was checked to ELABORATE against its rival and to FAIL on the frozen
solution (so it discriminates rather than asserting a tautology). The reject
rivals ship the FROZEN proof body verbatim (a ``sorry`` would violate the variant
scope), so their rejection is the frozen script failing to close against the
reshaped impl — which is exactly why the witness, not the rejection, attributes
the failure to the spec.

BINDER / POINT COVERAGE. The spec has the single input binder ``hlcode``. The
reject witnesses probe NINE distinct input points — the empty sequence, a
16-character run with no opening delimiter, a 17-character run, a 16-character
run followed by a trailing space, the same run followed by a trailing TAB, an
opening-delimiter run followed by filler, a BARE opening-delimiter run, the
opening delimiter TWICE, and an F2P-shaped
``verbOpen ++ "\\nCODE\\n\\end{Verbatim}"`` — so the battery demonstrates the
spec's dependence on ``hlcode`` at empty / no-match / single-match /
repeated-match / match-truncated-by-the-slice / two distinct trailing-whitespace
/ full-fragment shapes.

Every point above is load-bearing rather than a second spelling of another, and
each was chosen because the rival it serves is observably IDENTICAL to the frozen
impl everywhere else in the battery:

  * ``"abcdefghijklmnop "`` (trailing space) — every other point is
    ``rstripWs``-invariant, so on them the strip is the identity and both
    ``weak-no-rstrip`` and ``weak-rstrip-after-slice`` are indistinguishable from
    the frozen impl. Without it the strip and its ORDER relative to the slice are
    unprobed.
  * ``"abcdefghijklmnop\\t"`` (trailing tab) — the only point whose tail
    whitespace lies OUTSIDE the space/newline pair, so it is the only one that
    separates ``isTrailWs`` from a proper subset of it
    (``weak-narrow-whitespace-set``). A trailing space does not: any plausible
    narrower set still contains it.
  * ``verbOpen ++ verbOpen`` — the only point with more than one occurrence of
    the opening delimiter, so it is the only one on which all-occurrences and
    first-occurrence-only substitution differ
    (``weak-open-first-occurrence-only``).
  * ``verbOpen`` alone — the only point short enough that the fifteen-character
    slice truncates the delimiter itself, so it is the only one that separates
    rewrite-then-trim from trim-then-rewrite (``weak-rewrite-after-trim``).

Witnesses are written using only identifiers the FROZEN solution already
declares, even when the rival introduces a helper of its own. A witness naming a
rival-only constant fails on the frozen solution as an unknown identifier — a
syntactic accident that discriminates nothing — so ``weak-open-first-occurrence-\
only`` expresses its rival inline (``isPrefixOf`` / ``drop``) rather than via a
named helper for exactly that reason.
"""
from pathlib import Path

INSTANCE = "sphinx-doc__sphinx-10435"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Anchors that live EXCLUSIVELY inside the impl region (and, for the reproven
# positive, the proof region). Each is asserted unique in _BASE so every _swap
# edits only the region it means to, and same_spec is preserved by construction.
# ---------------------------------------------------------------------------
_A_OPEN = "hl := replaceAll verbOpen upquoteOpen hl"          # the opening rewrite
_A_TRAILER = "hl := dropLastN 15 (rstripWs hl)"               # the trailer slice
_A_CLOSE = "  body := body ++ closingTail\n"                  # the closing append
_A_IMPL = (                                                   # the full impl body
    "def implementation_inlineCode (hlcode : List Char) : List Char := Id.run do\n"
    "  let mut hl := hlcode\n"
    "  hl := replaceAll verbOpen upquoteOpen hl\n"
    "  -- get consistent trailer\n"
    "  hl := dropLastN 15 (rstripWs hl)\n"
    "  let mut body : List Char := []\n"
    "  body := body ++ hl\n"
    "  body := body ++ closingTail\n"
    "  return body"
)
_P_GOLD = (                                                   # the full proof body
    "  intro hlcode\n"
    "  simp only [problem_spec_inlineCode, implementation_inlineCode, Id.run, "
    "List.nil_append, pure]\n"
)

for _a in (_A_OPEN, _A_TRAILER, _A_CLOSE, _A_IMPL, _P_GOLD):
    assert _BASE.count(_a) == 1, f"impl/proof anchor drifted: {_a!r}"


# ===========================================================================
# POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls that
# MUST verify, else SPEC-TOO-STRONG. Each keeps the `theorem correct_inlineCode`
# statement byte-identical; none introduces a helper lemma, axiom, or assumption.
# ===========================================================================

# -- reshape: split the single closing-tail append into two appends (the comment
# marker + newline, then the closing braces). Same concatenation reaches the
# result on every input, so `result = trimmed ++ closingTail` still holds. The
# frozen script is tuned to the single append, so the obligation is RE-PROVED
# (statement byte-identical) by unfolding the split with the append/cons lemmas.
_POS_IMPL = (
    "  body := body ++ ('%' :: CR :: [])\n"
    "  body := body ++ \"}}\".toList\n"
)
_POS_PROOF = (
    "  intro hlcode\n"
    "  simp only [problem_spec_inlineCode, implementation_inlineCode, Id.run, "
    "List.nil_append, pure,\n"
    "    closingTail, CR, List.append_assoc, List.cons_append, List.nil_append]\n"
)
SPEC_POS = _swap(_swap(_BASE, _A_CLOSE, _POS_IMPL), _P_GOLD, _POS_PROOF)


# ===========================================================================
# ADMISSIBILITY — a positive control that the obligation is SATISFIABLE at a
# normal, F2P-shaped input rather than only in the abstract. The frozen theorem
# carries no precondition hypothesis (the modeled behaviour is total), so the
# nagini precondition-admission probe has no binder to attack; the honest
# analogue COMPUTES the emitted sequence at a ground F2P-shaped input (an
# opening-delimiter run, a newline, code, a newline, and the closing delimiter —
# the invariant highlighter fragment shape) as a `have` INSIDE the existing
# tactic body, then closes the frozen obligation verbatim.
#
# The `have` pins the ground RESULT VALUE and closes it by `decide`, i.e. by
# kernel reduction of the concrete character sequence. A `have` that merely
# restated `problem_spec_inlineCode <input> (implementation_inlineCode <input>)`
# and discharged it with the frozen script would be a NON-TEST: it is a
# substitution instance of the very theorem being proved a line later, so it
# would pass by definitional unfolding without ever evaluating the emission, and
# an impl whose ground value was wrong at this input could not make it fail.
# Pinning the literal expected sequence is what makes it bite: the opening
# rewritten and comment-marked, the body, and the comment-terminated close, with
# BOTH framing newlines gone and no spurious whitespace at either end.
# ===========================================================================
_F2P_IN = (
    "(verbOpen ++ (CR :: \"CODE\".toList) ++ (CR :: r\"\\end{Verbatim}\".toList))"
)
_ADMISS_PROOF = (
    "  have _reachable : implementation_inlineCode\n"
    "      " + _F2P_IN + "\n"
    "      = r\"\\sphinxcode{\\sphinxupquote{%\".toList ++ (CR :: \"CODE\".toList)\n"
    "        ++ ('%' :: CR :: \"}}\".toList) := by\n"
    "    unfold implementation_inlineCode\n"
    "    simp only [Id.run, List.nil_append, pure]\n"
    "    have hg : replaceAll verbOpen upquoteOpen\n"
    "        " + _F2P_IN + "\n"
    "        = upquoteOpen ++ (CR :: \"CODE\".toList) ++ "
    "(CR :: r\"\\end{Verbatim}\".toList) := by\n"
    "      simp [replaceAll, verbOpen, upquoteOpen, CR, List.isPrefixOf]\n"
    "    rw [hg]\n"
    "    decide\n"
    "  intro hlcode\n"
    "  simp only [problem_spec_inlineCode, implementation_inlineCode, Id.run, "
    "List.nil_append, pure]\n"
)
SPEC_ADMISS = _swap(_BASE, _P_GOLD, _ADMISS_PROOF)


# ===========================================================================
# UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec that
# MUST be rejected. Each carries (a) the refinement argument that its faithful
# real patch would NOT resolve the F2P, and (b) a refutation witness pinning the
# violation at one concrete input, checked to hold of the rival and FAIL on gold.
# Each reject rival ships the FROZEN proof body verbatim.
# ===========================================================================

# -- REJECT #1: opening rewrite WITHOUT the trailing comment marker ------------
# Rewrites the opening delimiter to the upquote opening but omits the trailing
# `%`, so the newline the highlighter emits after the opening delimiter survives
# as a leading inter-token space. Correct on inputs with no opening delimiter,
# diverges the moment one is present. (nagini "drop the opening suppressor".)
SPEC_OPEN_NO_PCT = _swap(
    _BASE, _A_OPEN,
    "hl := replaceAll verbOpen (r\"\\sphinxcode{\\sphinxupquote{\".toList) hl")

# -- REJECT #2: trailer slice off-by-one -- drop 14 instead of 15 --------------
# Drops only the closing delimiter and leaves the newline that precedes it in
# place, so a trailing inter-token space survives. Correct on the length prefix,
# diverges on the last retained character. Mirrors the nagini content off-by-one
# on THIS carrier's trailer slice, and is the pre-patch trailer behaviour.
SPEC_TRAILER_14 = _swap(
    _BASE, _A_TRAILER, "hl := dropLastN 14 (rstripWs hl)")

# -- REJECT #3: closing tail WITHOUT the leading comment marker ----------------
# Appends the newline and braces with no leading `%`, so the trailing newline is
# not comment-suppressed and survives as a trailing inter-token space. This is
# the pre-patch CLOSING-side defect. (nagini "drop the trailing suppressor".)
SPEC_CLOSE_NO_PCT = _swap(
    _BASE, _A_CLOSE, "  body := body ++ (CR :: \"}}\".toList)\n")

# -- REJECT #1b: no opening rewrite at all -------------------------------------
# Leaves the highlighter's opening delimiter in place. The shipped
# `weak-open-no-comment-marker` rival still rewrites and only varies the TARGET,
# so on its own it never pins that a rewrite occurs at all.
SPEC_NO_REWRITE = _swap(_BASE, _A_OPEN, "hl := hl")

# -- REJECT #3b: trailer slice off-by-one the OTHER way -- drop 16 -------------
# Drops the closing delimiter, the newline before it, AND one further character
# of the retained body, so the last body character is eaten. The shipped
# trailer-14 rival only pins the slice from BELOW (a shorter drop is caught); on
# its own, a LONGER drop is unattacked, and "drops fifteen" is only half pinned.
SPEC_TRAILER_16 = _swap(
    _BASE, _A_TRAILER, "hl := dropLastN 16 (rstripWs hl)")

# -- REJECT #3c: no trailing-whitespace strip before the slice -----------------
# Slices fifteen characters off the RAW rewritten sequence without first removing
# trailing whitespace, so on any input whose tail carries whitespace the fifteen
# are counted from the wrong end and a body character survives that should not.
SPEC_NO_RSTRIP = _swap(
    _BASE, _A_TRAILER, "hl := dropLastN 15 hl")

# -- REJECT #3d: strip AFTER the slice instead of before -----------------------
# Applies the strip to the already-sliced sequence. Same components, wrong ORDER:
# the fifteen-character run is again counted from the raw tail, so the retained
# prefix is one character too long on a whitespace-bearing input. Observably
# identical to the frozen impl on whitespace-free inputs, which is exactly why it
# needs the whitespace-bearing witness point.
SPEC_RSTRIP_AFTER = _swap(
    _BASE, _A_TRAILER, "hl := rstripWs (dropLastN 15 hl)")

# -- REJECT #4: the full PRE-PATCH composite -----------------------------------
# All three components regressed at once (no opening `%`, trailer 14, no closing
# `%`) — exactly the Solution_prepatch skeleton. Both framing newlines survive as
# spurious leading/trailing spaces; this is the literal bug the fix repairs.
SPEC_PREPATCH = _swap(
    _BASE, _A_IMPL,
    "def implementation_inlineCode (hlcode : List Char) : List Char := Id.run do\n"
    "  let mut hl := hlcode\n"
    "  hl := replaceAll verbOpen (r\"\\sphinxcode{\\sphinxupquote{\".toList) hl\n"
    "  -- get consistent trailer\n"
    "  hl := dropLastN 14 (rstripWs hl)\n"
    "  let mut body : List Char := []\n"
    "  body := body ++ hl\n"
    "  body := body ++ \"}}\".toList\n"
    "  return body")

# -- REJECT #5: rewrite only the LEADING occurrence, not every one -------------
# `replaceAll` is all-occurrences; this rival substitutes at the head only and
# leaves any later occurrence of the opening delimiter in place. Observably
# IDENTICAL to the frozen impl on every input containing at most one occurrence
# — which is every other witness point in this battery — so only a
# two-occurrence input separates it. Written with the frozen file's own
# identifiers (`isPrefixOf` / `drop` / `verbOpen` / `upquoteOpen`) so its
# witness names no constant that is absent from the frozen solution: a witness
# mentioning a rival-only helper fails on gold as an UNKNOWN IDENTIFIER, which
# is a syntactic accident rather than a refutation and would attest to nothing.
SPEC_OPEN_FIRST_ONLY = _swap(
    _BASE, _A_OPEN,
    "hl := (if verbOpen.isPrefixOf hl then upquoteOpen ++ hl.drop verbOpen.length"
    " else hl)")

# -- REJECT #6: a NARROWER trailing-whitespace set -----------------------------
# Strips only spaces and newlines, not the full default set (tab, carriage
# return, vertical tab, form feed). `rstripWs` is pinned to the whole set, so a
# tail bearing any of the other four is stripped by the frozen impl and retained
# here. Observably identical to the frozen impl on every point the rest of the
# battery uses (their only trailing whitespace is a space), so without this case
# WHICH characters the strip removes is unpinned — only THAT it strips something.
SPEC_NARROW_WS = _swap(
    _BASE, _A_IMPL,
    "def isTrailWs2 (c : Char) : Bool := c == ' ' || c == '\\n'\n"
    "\n"
    "def rstripWs2 (s : List Char) : List Char :=\n"
    "  (s.reverse.dropWhile isTrailWs2).reverse\n"
    "\n"
    + _A_IMPL.replace("hl := dropLastN 15 (rstripWs hl)",
                      "hl := dropLastN 15 (rstripWs2 hl)"))

# -- REJECT #7: the opening rewrite AFTER the trim instead of before -----------
# Same three components, a third distinct ORDER: trim first, then rewrite what
# survives. The trim cuts fifteen characters off the tail, so an input whose
# opening delimiter is not followed by at least fifteen further characters has
# that delimiter truncated before the rewrite can fire, and the rewrite then
# misses entirely. Observably identical to the frozen impl whenever the delimiter
# survives the trim intact — including every point the rest of the battery uses.
SPEC_REWRITE_AFTER_TRIM = _swap(
    _BASE, _A_IMPL,
    _A_IMPL.replace(
        "  hl := replaceAll verbOpen upquoteOpen hl\n"
        "  -- get consistent trailer\n"
        "  hl := dropLastN 15 (rstripWs hl)\n",
        "  -- get consistent trailer\n"
        "  hl := dropLastN 15 (rstripWs hl)\n"
        "  hl := replaceAll verbOpen upquoteOpen hl\n"))


SPEC_TESTS = [
    {
        "id": "pos-split-closing-append",
        "kind": "soundness",
        "expect": "verify",
        "module": SPEC_POS,
        "rationale": (
            "structurally-different but CORRECT: the single closing-tail append is "
            "split into two appends (the comment marker plus newline, then the "
            "closing braces); the same concatenation reaches the result on every "
            "input, so `result = trimmed ++ closingTail` is unchanged. A faithful "
            "correct impl of a different append shape MUST verify, else "
            "SPEC-TOO-STRONG. Re-proved because the frozen script is tuned to the "
            "single append: unfolding the split with the append/cons lemmas closes "
            "the byte-identical obligation, using only core lemmas, no new "
            "declaration."),
    },
    {
        "id": "admiss-fshaped-reachable",
        "kind": "admissibility",
        "expect": "verify",
        "module": SPEC_ADMISS,
        "rationale": (
            "the obligation is discharged at a ground F2P-shaped input (an "
            "opening-delimiter run, a newline, code, a newline, and the closing "
            "delimiter — the invariant highlighter fragment shape) as a `have` "
            "inside the existing tactic body, then the frozen obligation is closed "
            "verbatim. Verifies (else the modeled behaviour is unsatisfiable at the "
            "normal input, the analogue of PRECOND-TOO-STRONG). Nothing is assumed: "
            "no new declaration, the theorem statement is byte-identical."),
    },
    {
        "id": "weak-open-no-comment-marker",
        "kind": "uniqueness",
        "expect": "reject",
        "module": SPEC_OPEN_NO_PCT,
        "refinement": (
            "this is the pre-patch OPENING-side defect: the opening rewrite omits "
            "the trailing comment marker, so the newline after the opening "
            "delimiter renders as a spurious leading space. The F2P expects the "
            "opening followed immediately by the comment marker; producing the "
            "opening without it fails the substring assertion => NOT resolve."),
        "rationale": (
            "REJECT from the equality's opening component: on any input containing "
            "the opening delimiter the rewrite target must carry the trailing "
            "comment marker, so `result` differs from the rival's. If it verified, "
            "the opening-suppression discriminator is unpinned (SPEC-TOO-WEAK)."),
        "witness": (
            "example : ¬ problem_spec_inlineCode (verbOpen ++ \"aaaaaaaaaaaaaaaa\".toList)\n"
            "    (implementation_inlineCode (verbOpen ++ \"aaaaaaaaaaaaaaaa\".toList)) := by\n"
            "  have hg : replaceAll verbOpen upquoteOpen (verbOpen ++ \"aaaaaaaaaaaaaaaa\".toList)\n"
            "      = upquoteOpen ++ \"aaaaaaaaaaaaaaaa\".toList := by\n"
            "    simp [replaceAll, verbOpen, upquoteOpen, List.isPrefixOf]\n"
            "  have hr : replaceAll verbOpen (r\"\\sphinxcode{\\sphinxupquote{\".toList) "
            "(verbOpen ++ \"aaaaaaaaaaaaaaaa\".toList)\n"
            "      = (r\"\\sphinxcode{\\sphinxupquote{\".toList) ++ \"aaaaaaaaaaaaaaaa\".toList := by\n"
            "    simp [replaceAll, verbOpen, List.isPrefixOf]\n"
            "  unfold problem_spec_inlineCode implementation_inlineCode\n"
            "  simp only [Id.run, List.nil_append, pure, hg, hr]\n"
            "  decide\n"
        ),
    },
    {
        "id": "weak-trailer-off-by-one",
        "kind": "uniqueness",
        "expect": "reject",
        "module": SPEC_TRAILER_14,
        "refinement": (
            "this is the pre-patch TRAILER defect: dropping fourteen trailing "
            "characters removes only the closing delimiter and leaves the newline "
            "that precedes it, which renders as a spurious trailing space. The F2P "
            "expects the body immediately followed by the comment-terminated close; "
            "leaving the newline in place fails the substring assertion => NOT "
            "resolve."),
        "rationale": (
            "REJECT from the equality's trailer component: the retained prefix must "
            "be the input minus fifteen trailing characters, not fourteen, so on any "
            "input longer than the dropped run `result` differs. Correct on the "
            "shared prefix, wrong on the last retained character (partial-domain). "
            "If it verified, the trailer length is unpinned (SPEC-TOO-WEAK)."),
        "witness": (
            "example : ¬ problem_spec_inlineCode \"abcdefghijklmnop\".toList\n"
            "    (implementation_inlineCode \"abcdefghijklmnop\".toList) := by\n"
            "  have h : replaceAll verbOpen upquoteOpen \"abcdefghijklmnop\".toList "
            "= \"abcdefghijklmnop\".toList := by\n"
            "    simp [replaceAll, verbOpen]\n"
            "  unfold problem_spec_inlineCode implementation_inlineCode\n"
            "  simp only [Id.run, List.nil_append, pure, h]\n"
            "  decide\n"
        ),
    },
    {
        "id": "weak-trailer-off-by-one-long",
        "kind": "uniqueness",
        "expect": "reject",
        "module": SPEC_TRAILER_16,
        "refinement": (
            "dropping sixteen trailing characters removes the closing delimiter, "
            "the newline before it, AND the final character of the highlighted "
            "body, so the rendered inline code loses its last character. The F2P "
            "matches the highlighted body VERBATIM as a substring; a body missing "
            "its last character fails that assertion => NOT resolve."),
        "rationale": (
            "REJECT pinning the trailer length from ABOVE. The shipped "
            "`weak-trailer-off-by-one` rival drops fourteen and so pins the slice "
            "only from below; without this case a LONGER drop is unattacked and "
            "'drops exactly fifteen' is half-specified. This is also the direct "
            "analogue of the nagini content off-by-one (drop the last code point "
            "of the copied body) on THIS carrier's trailer slice."),
        "witness": (
            "example : ¬ problem_spec_inlineCode \"abcdefghijklmnopq\".toList\n"
            "    (implementation_inlineCode \"abcdefghijklmnopq\".toList) := by\n"
            "  have h : replaceAll verbOpen upquoteOpen \"abcdefghijklmnopq\".toList "
            "= \"abcdefghijklmnopq\".toList := by\n"
            "    simp [replaceAll, verbOpen]\n"
            "  unfold problem_spec_inlineCode implementation_inlineCode\n"
            "  simp only [Id.run, List.nil_append, pure, h]\n"
            "  decide\n"
        ),
    },
    {
        "id": "weak-no-rstrip",
        "kind": "uniqueness",
        "expect": "reject",
        "module": SPEC_NO_RSTRIP,
        "refinement": (
            "slicing fifteen characters off the raw sequence without first "
            "removing trailing whitespace counts the run from the wrong end, so a "
            "body character survives that should have been dropped and the "
            "emitted fragment carries a stray character before the "
            "comment-terminated close. The F2P matches the body followed "
            "immediately by that close; a stray retained character fails the "
            "substring assertion => NOT resolve."),
        "rationale": (
            "REJECT pinning the trailing-whitespace strip itself. Every OTHER "
            "witness point in this battery is strip-invariant (no trailing "
            "whitespace), so on those points the strip is the identity and this "
            "deviation is invisible; the refutation is therefore stated at "
            "`\"abcdefghijklmnop \"`, whose tail whitespace makes the strip "
            "observable. Without this case the strip is entirely unprobed and "
            "an impl that omits it would satisfy the battery (SPEC-TOO-WEAK)."),
        "witness": (
            "example : ¬ problem_spec_inlineCode \"abcdefghijklmnop \".toList\n"
            "    (implementation_inlineCode \"abcdefghijklmnop \".toList) := by\n"
            "  have h : replaceAll verbOpen upquoteOpen \"abcdefghijklmnop \".toList "
            "= \"abcdefghijklmnop \".toList := by\n"
            "    simp [replaceAll, verbOpen]\n"
            "  unfold problem_spec_inlineCode implementation_inlineCode\n"
            "  simp only [Id.run, List.nil_append, pure, h]\n"
            "  decide\n"
        ),
    },
    {
        "id": "weak-rstrip-after-slice",
        "kind": "uniqueness",
        "expect": "reject",
        "module": SPEC_RSTRIP_AFTER,
        "refinement": (
            "the same three components in the wrong ORDER: stripping trailing "
            "whitespace only AFTER the fifteen-character slice again counts the "
            "run from the raw tail, leaving the retained prefix one character too "
            "long on a whitespace-bearing input. The emitted body therefore "
            "differs from the one the F2P matches verbatim => NOT resolve."),
        "rationale": (
            "REJECT pinning the ORDER of the strip and the slice, which no other "
            "case constrains. Note this rival is observably IDENTICAL to the "
            "frozen impl on every whitespace-free input — including the empty, "
            "16-char, 17-char and F2P-shaped points the other cases use — so it "
            "is a genuine near-miss that only the whitespace-bearing point "
            "separates. If it verified, the composition order would be unpinned."),
        "witness": (
            "example : ¬ problem_spec_inlineCode \"abcdefghijklmnop \".toList\n"
            "    (implementation_inlineCode \"abcdefghijklmnop \".toList) := by\n"
            "  have h : replaceAll verbOpen upquoteOpen \"abcdefghijklmnop \".toList "
            "= \"abcdefghijklmnop \".toList := by\n"
            "    simp [replaceAll, verbOpen]\n"
            "  unfold problem_spec_inlineCode implementation_inlineCode\n"
            "  simp only [Id.run, List.nil_append, pure, h]\n"
            "  decide\n"
        ),
    },
    {
        "id": "weak-no-opening-rewrite",
        "kind": "uniqueness",
        "expect": "reject",
        "module": SPEC_NO_REWRITE,
        "refinement": (
            "leaving the highlighter's opening delimiter untouched emits the "
            "Verbatim environment opening instead of the inline upquote opening, "
            "so the fragment is not inline code at all. The F2P expects the "
            "upquote opening followed by the comment marker; emitting the "
            "highlighter's own opening fails that assertion => NOT resolve."),
        "rationale": (
            "REJECT pinning that the opening rewrite HAPPENS. The shipped "
            "`weak-open-no-comment-marker` rival still performs a rewrite and only "
            "varies its target, so 'a rewrite occurs at all' is unattacked by it; "
            "this rival makes the rewrite the identity. If it verified, an impl "
            "that never substituted the opening would satisfy the spec."),
        "witness": (
            "example : ¬ problem_spec_inlineCode\n"
            "    (verbOpen ++ (CR :: \"CODE\".toList) ++ (CR :: r\"\\end{Verbatim}\".toList))\n"
            "    (implementation_inlineCode\n"
            "      (verbOpen ++ (CR :: \"CODE\".toList) ++ (CR :: r\"\\end{Verbatim}\".toList))) := by\n"
            "  have h : replaceAll verbOpen upquoteOpen\n"
            "      (verbOpen ++ (CR :: \"CODE\".toList) ++ (CR :: r\"\\end{Verbatim}\".toList))\n"
            "      = upquoteOpen ++ (CR :: \"CODE\".toList) ++ "
            "(CR :: r\"\\end{Verbatim}\".toList) := by\n"
            "    simp [replaceAll, verbOpen, upquoteOpen, CR, List.isPrefixOf]\n"
            "  unfold problem_spec_inlineCode implementation_inlineCode\n"
            "  simp only [Id.run, List.nil_append, pure, h]\n"
            "  decide\n"
        ),
    },
    {
        "id": "weak-close-no-comment-marker",
        "kind": "uniqueness",
        "expect": "reject",
        "module": SPEC_CLOSE_NO_PCT,
        "refinement": (
            "this is the pre-patch CLOSING-side defect: the closing tail omits the "
            "leading comment marker, so the trailing newline renders as a spurious "
            "trailing space. The F2P expects the body followed by the "
            "comment-terminated newline and braces; producing the newline without "
            "the marker fails the substring assertion => NOT resolve."),
        "rationale": (
            "REJECT from the equality's closing component: the appended tail must "
            "begin with the comment marker before the newline and braces, so "
            "`result` differs from the rival's on every input. The shared trimmed "
            "prefix cancels, isolating the closing-tail difference. If it verified, "
            "the closing-suppression discriminator is unpinned (SPEC-TOO-WEAK)."),
        "witness": (
            "example : ¬ problem_spec_inlineCode \"\".toList\n"
            "    (implementation_inlineCode \"\".toList) := by\n"
            "  unfold problem_spec_inlineCode implementation_inlineCode\n"
            "  simp only [Id.run, List.nil_append, pure, closingTail, CR, "
            "List.append_cancel_left_eq]\n"
            "  decide\n"
        ),
    },
    {
        "id": "weak-prepatch-composite",
        "kind": "uniqueness",
        "expect": "reject",
        "module": SPEC_PREPATCH,
        "refinement": (
            "the literal pre-patch behaviour: opening rewrite without the comment "
            "marker, trailer dropping fourteen not fifteen, and closing braces with "
            "no comment-terminated newline. Both framing newlines survive as "
            "spurious leading and trailing spaces — exactly the rendered defect the "
            "issue reports. Every component the F2P checks (opening + marker, "
            "body-then-comment-close) fails => NOT resolve."),
        "rationale": (
            "REJECT from the equality on all three components at once: on the "
            "F2P-shaped fragment the rival's opening lacks the marker, its trailer "
            "keeps a newline, and its tail lacks the marker, so `result` differs "
            "from the pinned closed form. This is the bug the fix repairs; if it "
            "verified the whole spec would be SPEC-TOO-WEAK."),
        "witness": (
            "example : ¬ problem_spec_inlineCode\n"
            "    (verbOpen ++ (CR :: \"CODE\".toList) ++ (CR :: r\"\\end{Verbatim}\".toList))\n"
            "    (implementation_inlineCode\n"
            "      (verbOpen ++ (CR :: \"CODE\".toList) ++ (CR :: r\"\\end{Verbatim}\".toList))) := by\n"
            "  have hg : replaceAll verbOpen upquoteOpen\n"
            "      (verbOpen ++ (CR :: \"CODE\".toList) ++ (CR :: r\"\\end{Verbatim}\".toList))\n"
            "      = upquoteOpen ++ (CR :: \"CODE\".toList) ++ (CR :: r\"\\end{Verbatim}\".toList) := by\n"
            "    simp [replaceAll, verbOpen, upquoteOpen, CR, List.isPrefixOf]\n"
            "  have hr : replaceAll verbOpen (r\"\\sphinxcode{\\sphinxupquote{\".toList)\n"
            "      (verbOpen ++ (CR :: \"CODE\".toList) ++ (CR :: r\"\\end{Verbatim}\".toList))\n"
            "      = (r\"\\sphinxcode{\\sphinxupquote{\".toList) ++ (CR :: \"CODE\".toList) "
            "++ (CR :: r\"\\end{Verbatim}\".toList) := by\n"
            "    simp [replaceAll, verbOpen, CR, List.isPrefixOf]\n"
            "  unfold problem_spec_inlineCode implementation_inlineCode\n"
            "  simp only [Id.run, List.nil_append, pure, hg, hr]\n"
            "  decide\n"
        ),
    },
    {
        "id": "weak-open-first-occurrence-only",
        "kind": "uniqueness",
        "expect": "reject",
        "module": SPEC_OPEN_FIRST_ONLY,
        "refinement": (
            "the rewrite is specified over ALL occurrences of the opening "
            "delimiter; substituting only the leading one leaves any later "
            "occurrence in the emitted fragment as a raw Verbatim environment "
            "opening. The F2P matches the emitted fragment verbatim, and a "
            "retained `\\begin{Verbatim}` inside it fails that assertion => NOT "
            "resolve."),
        "rationale": (
            "REJECT pinning the MULTIPLICITY of the opening rewrite, which no "
            "other case constrains: every other rival either changes the target, "
            "removes the rewrite entirely, or reorders it, and every other "
            "witness point in this battery contains at most ONE occurrence of the "
            "delimiter — on which this rival is observably IDENTICAL to the "
            "frozen impl. The refutation is therefore stated at `verbOpen ++ "
            "verbOpen`, the smallest point where all-occurrences and "
            "first-occurrence-only diverge. If it verified, `replaceAll` would be "
            "pinned no more tightly than `replaceFirst` (SPEC-TOO-WEAK)."),
        "witness": (
            "example : ¬ problem_spec_inlineCode (verbOpen ++ verbOpen)\n"
            "    (implementation_inlineCode (verbOpen ++ verbOpen)) := by\n"
            "  have hg : replaceAll verbOpen upquoteOpen (verbOpen ++ verbOpen)\n"
            "      = upquoteOpen ++ upquoteOpen := by\n"
            "    simp [replaceAll, verbOpen, upquoteOpen, List.isPrefixOf]\n"
            "  have hr : (if verbOpen.isPrefixOf (verbOpen ++ verbOpen) then\n"
            "      upquoteOpen ++ (verbOpen ++ verbOpen).drop verbOpen.length\n"
            "      else (verbOpen ++ verbOpen))\n"
            "      = upquoteOpen ++ verbOpen := by\n"
            "    simp [verbOpen, upquoteOpen, List.isPrefixOf]\n"
            "  unfold problem_spec_inlineCode implementation_inlineCode\n"
            "  simp only [Id.run, List.nil_append, pure, hg, hr]\n"
            "  decide\n"
        ),
    },
    {
        "id": "weak-narrow-whitespace-set",
        "kind": "uniqueness",
        "expect": "reject",
        "module": SPEC_NARROW_WS,
        "refinement": (
            "stripping only spaces and newlines leaves a tab (or carriage "
            "return, vertical tab, form feed) at the tail, so the "
            "fifteen-character run is counted from that retained character and a "
            "body character survives that should have been dropped. The emitted "
            "fragment then differs from the one the F2P matches verbatim => NOT "
            "resolve."),
        "rationale": (
            "REJECT pinning WHICH characters the trailing strip removes. "
            "`weak-no-rstrip` and `weak-rstrip-after-slice` pin only that a strip "
            "happens and where it sits in the composition; both are satisfied by a "
            "strip over any whitespace set, so the SET itself was unpinned and an "
            "impl stripping a proper subset satisfied every other case in this "
            "battery. The refutation is stated at `\"abcdefghijklmnop\\t\"`, whose "
            "tab is in the pinned set but not in the rival's."),
        "witness": (
            "example : ¬ problem_spec_inlineCode \"abcdefghijklmnop\\t\".toList\n"
            "    (implementation_inlineCode \"abcdefghijklmnop\\t\".toList) := by\n"
            "  have h : replaceAll verbOpen upquoteOpen \"abcdefghijklmnop\\t\".toList\n"
            "      = \"abcdefghijklmnop\\t\".toList := by\n"
            "    simp [replaceAll, verbOpen]\n"
            "  unfold problem_spec_inlineCode implementation_inlineCode\n"
            "  simp only [Id.run, List.nil_append, pure, h]\n"
            "  decide\n"
        ),
    },
    {
        "id": "weak-rewrite-after-trim",
        "kind": "uniqueness",
        "expect": "reject",
        "module": SPEC_REWRITE_AFTER_TRIM,
        "refinement": (
            "trimming before rewriting means a short fragment has its opening "
            "delimiter truncated by the fifteen-character slice before the "
            "rewrite can fire, so no substitution happens at all and the emitted "
            "fragment is a truncated Verbatim opening instead of the inline "
            "upquote opening. The F2P expects the upquote opening followed by the "
            "comment marker => NOT resolve."),
        "rationale": (
            "REJECT pinning the order of the REWRITE against the trim — a third "
            "distinct composition order that no other case constrains "
            "(`weak-rstrip-after-slice` swaps the strip and the slice, both of "
            "which sit downstream of the rewrite). Observably identical to the "
            "frozen impl whenever the delimiter survives the trim intact, which is "
            "true at every other witness point in this battery. The refutation is "
            "stated at `verbOpen` alone, the point where the trim eats into the "
            "delimiter and the rewrite consequently misses."),
        "witness": (
            "example : ¬ problem_spec_inlineCode verbOpen\n"
            "    (implementation_inlineCode verbOpen) := by\n"
            "  have ht : dropLastN 15 (rstripWs verbOpen)\n"
            "      = \"\\\\begin{Verbatim}[comma\".toList := by\n"
            "    decide\n"
            "  have hg : replaceAll verbOpen upquoteOpen verbOpen = upquoteOpen := by\n"
            "    simp [replaceAll, verbOpen, upquoteOpen, List.isPrefixOf]\n"
            "  have hn : replaceAll verbOpen upquoteOpen "
            "\"\\\\begin{Verbatim}[comma\".toList\n"
            "      = \"\\\\begin{Verbatim}[comma\".toList := by\n"
            "    simp [replaceAll, verbOpen]\n"
            "  unfold problem_spec_inlineCode implementation_inlineCode\n"
            "  simp only [Id.run, List.nil_append, pure, ht, hg, hn]\n"
            "  decide\n"
        ),
    },
]

AXIOM_TESTS = []  # axiom lane belongs to G-AX; meta.json declares no consumed
# axiom and no opaque callees, so there is nothing to probe here.
