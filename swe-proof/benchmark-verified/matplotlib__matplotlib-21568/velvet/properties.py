"""properties.py — G-PBT falsification battery for matplotlib__matplotlib-21568 (velvet).

NOT a Velvet module; a manifest the G-PBT gate executes. Each SPEC case is a
full ``Solution.lean`` variant that shares the FROZEN spec byte-for-byte (region
surgery: only text inside the ``-- impl-start`` / ``-- impl-end`` region, or the
``prove_correct`` tactic body, is changed — both elided from the consumer spec
view, so ``markers.same_spec`` holds and the ``prove_correct renderTexLabel``
obligation survives with a byte-identical statement) and swaps in a candidate
implementation. ``expect="verify"`` passes iff (in scope AND verifies);
``expect="reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness must elaborate against the rival and FAIL
against the frozen solution, with jointly-satisfiable hypotheses).

DEFENDED SURFACE (one contracted method, one input binder ``text``):

  renderTexLabel (text : List Char) return (out : List Char)
    ensures out = removeEmpty
      ("$\\mathdefault{".toList ++ protectSeq (preprocess text) ++ "}$".toList)

  The single load-bearing clause pins the WHOLE output to a total function of the
  input: the input is first run through an unchanged pre-processor, then each
  code point of the result is math-protected by ``protectSeq`` — a grounded
  front-recursive fold whose per-code-point map wraps three code points and
  passes every other through unchanged:

      '-'  ->  "{-}"       ':'  ->  "{:}"       ' '  ->  "\\;"      else  [c]

  and the protected string is enclosed in the fixed math delimiters, the whole
  finally passed through an unchanged empty-group collapse. The three protected
  code points are the entire content of the modeled change.

CARRIER NOTE — why this port CONDITIONS on the carrier for every rival.

  The postcondition RHS is ``removeEmpty (prefix ++ protectSeq (preprocess text)
  ++ suffix)`` where BOTH the input pre-processor and the OUTERMOST operation
  (the empty-group collapse) are UNINTERPRETED total functions (axioms with no
  constraining ``ensures`` — mapping.md §3.2; they are unchanged context callees
  the change never touches). Two consequences drive every design choice:

   1. No literal input decides anything. The pre-processor sits between ``text``
      and the ``protectSeq`` fold, so ``renderTexLabel ['x']`` reduces only to
      ``removeEmpty (… protectSeq (preprocess ['x']) …)`` with ``preprocess
      ['x']`` opaque — nothing computes. So every reject ``witness`` states its
      refutation at a point described by HYPOTHESIS: it fixes ``preprocess t = v``
      for a concrete ``v`` (the sub-domain where the rival's per-code-point
      handling bites), and — because the whole result is then wrapped in the
      opaque collapse — assumes the collapse SEPARATES the rival's assembled
      string from gold's (``removeEmpty A ≠ removeEmpty B`` for the two distinct
      pre-collapse strings ``A`` (rival) and ``B`` (gold)). That assumption is
      exactly the sub-domain where the rival is observably wrong; the gate's
      consistency probe confirms both hypotheses can jointly hold (they are about
      DIFFERENT terms — one about the pre-processor, one about the collapse — and
      the two collapse arguments genuinely differ, so no contradiction).
   2. The witness reaches the method's Hoare triple DIRECTLY (``¬ triple True
      (renderTexLabel t) (fun out => out = …)``) reduced through ``triple_pure``
      for the straight-line rivals — the ``extract_program_for`` /
      ``derive_tester_for`` + ``decide`` tester route is UNAVAILABLE, because the
      postcondition depends on the noncomputable opaque callees and extraction
      cannot compile it. Checked in a file whose ``prove_correct`` block has been
      stripped, so no tactic script can mask the verdict.

ADVERSARIAL READ of the sibling weakness classes (see footer for the full
accounting; each omission is a stated carrier limit, never a hard-to-prove one):
  * FRAME-MUTATION — VACUOUS. The nagini sibling's mandatory frame rival writes
    into a read-only input held at a fractional heap permission and is rejected
    for INSUFFICIENT PERMISSION. This backend is referentially transparent:
    ``text`` is an immutable value (NOT a ``mut`` binder), there is no heap, no
    aliasing and no permission system to trip. No read-only input to overwrite
    and no substitute probe to build. Reported vacuous, not fabricated.
  * PARTIAL-DOMAIN / per-code-point — APPLIES, re-expressed by conditioning.
    Rivals right on every label without a given code point but diverging on it: a
    body that DROPS one of the three protections (dash / colon / space) and one
    that emits the space token with its two code points SWAPPED. Each is refuted
    at a concrete pre-processor image that varies the ``text`` binder, so no point
    is pinned across the battery.
  * UNGROUNDED-ORACLE ECHO — N/A as a wrong echo. The clause is grounded in
    ``protectSeq`` (a fold over the pre-processed input), not an opaque
    answer-key; any echo of that fold IS the correct answer. The only available
    "echo" is a wrong per-code-point emission, which is exactly the drop / swap
    rivals below.
  * ADMISSIBILITY — APPLIES, and is LANDED (``adm-indomain-label``). The method
    carries no ``require`` clause, but "no precondition" is NOT a reason to drop
    this lane: on a total carrier the analogue of PRECOND-TOO-STRONG is the
    OBLIGATION being unsatisfiable at exactly an F2P-shaped input. That is
    directly testable — discharge the obligation's computable part at a concrete
    in-domain label BY EVALUATION, as a ``have``, before closing the frozen
    obligation verbatim — so the lane is expressible here and is exercised.
"""
from pathlib import Path

INSTANCE = "matplotlib__matplotlib-21568"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchor: the whole backward-loop body (text strictly between
# ---- -- impl-start and -- impl-end). Lies wholly inside the single impl region
# ---- and is unique in Solution.lean; both facts asserted at load by _swap. The
# ---- rivals abandon the loop for a straight-line pass so the witness reduces
# ---- through `triple_pure`.
_GOLD_IMPL = (
    "    let s := reSub text\n"
    "    let mut result : List Char := []\n"
    "    let mut i := s.length\n"
    "    while i > 0\n"
    "      invariant 0 ≤ i ∧ i ≤ s.length\n"
    "      invariant result = protectSeq (s.drop i)\n"
    "      done_with i = 0\n"
    "      decreasing i\n"
    "    do\n"
    "      let c := s[i - 1]!\n"
    "      result := mathProtect c ++ result\n"
    "      i := i - 1\n"
    '    let out := removeEmpty ("$\\\\mathdefault{".toList ++ result ++ "}$".toList)\n'
    "    return out"
)

# ---- proof-body anchor. The `prove_correct` tactic body is elided from the
# ---- consumer spec view, so the soundness positive may retune it for a reshaped
# ---- impl without touching the spec statement or dropping the obligation.
# ---- Unique in the file.
_GOLD_PROOF = (
    "prove_correct renderTexLabel by\n"
    "  loom_solve\n"
    "  rw [protectSeq_drop_step (reSub text) i (by omega) (by omega)]\n"
    "  simp_all"
)

assert _BASE.count(_GOLD_IMPL) == 1, "frozen impl region drifted; update _GOLD_IMPL"
assert _BASE.count(_GOLD_PROOF) == 1, "frozen proof body drifted; update _GOLD_PROOF"


def _impl(body):
    """Full Solution.lean variant with the gold impl block replaced. The frozen
    `prove_correct` body is kept (a reshaped rival that fails to build under it is
    the DEFAULT outcome — which is exactly why every reject case ships a
    witness)."""
    return _swap(_BASE, _GOLD_IMPL, body)


def _impl_proof(body, proof):
    """Reshape the impl block AND retune the `prove_correct` tactic body (for the
    soundness positive, whose new impl needs a proof that closes)."""
    return _swap(_swap(_BASE, _GOLD_IMPL, body), _GOLD_PROOF, proof)


# ---- straight-line rival body: replace the loop with a single `flatMap` whose
# ---- per-code-point map is the rival's (wrong) protection. Keeps the opaque
# ---- pre-processor `reSub` and the opaque collapse `removeEmpty` exactly as
# ---- gold, so the ONLY divergence is the per-code-point handling.
def _straight_line(per_char_map):
    return (
        "    let s := reSub text\n"
        f"    let bad := s.flatMap (fun c => {per_char_map})\n"
        '    let out := removeEmpty ("$\\\\mathdefault{".toList ++ bad ++ "}$".toList)\n'
        "    return out"
    )


# ---- witness builder. Reaches the method's Hoare triple directly and reduces it
# ---- through `triple_pure`; conditions on the opaque pre-processor image (`h1`)
# ---- and on the opaque collapse separating the rival's assembled string from
# ---- gold's (`h2`). Checked in a file whose `prove_correct` block is stripped.
def _witness(text_lit, resub_lit, rival_pre_collapse, gold_pre_collapse):
    return (
        "example\n"
        f"    (h1 : reSub {text_lit} = {resub_lit})\n"
        f'    (h2 : removeEmpty ("$\\\\mathdefault{{".toList ++ {rival_pre_collapse} ++ "}}$".toList)\n'
        f'        ≠ removeEmpty ("$\\\\mathdefault{{".toList ++ {gold_pre_collapse} ++ "}}$".toList)) :\n'
        f"    ¬ (triple (l := Prop) True (renderTexLabel {text_lit})\n"
        '        (fun out => out = removeEmpty ("$\\\\mathdefault{".toList\n'
        f'            ++ protectSeq (reSub {text_lit}) ++ "}}$".toList))) := by\n'
        "  unfold renderTexLabel\n"
        "  simp only [triple_pure, le_Prop_eq, true_implies]\n"
        "  intro hc\n"
        "  rw [h1] at hc\n"
        "  simp only [protectSeq, mathProtect, List.flatMap_cons, List.flatMap_nil,\n"
        "             List.append_nil, reduceIte] at hc\n"
        "  exact h2 hc\n"
    )


# per-code-point maps for the rivals (Lean lambda bodies). The space token is the
# two code points `\` `;` written as the string literal "\;".
_DROP_SPACE = ('if c = \'-\' then "{-}".toList '
               'else if c = \':\' then "{:}".toList else [c]')
_DROP_COLON = ('if c = \'-\' then "{-}".toList '
               'else if c = \' \' then "\\\\;".toList else [c]')
_DROP_DASH = ('if c = \':\' then "{:}".toList '
              'else if c = \' \' then "\\\\;".toList else [c]')
_WRONG_SPACE = ('if c = \'-\' then "{-}".toList '
                'else if c = \':\' then "{:}".toList '
                'else if c = \' \' then ";\\\\".toList else [c]')


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROL (soundness) — a structurally different but CORRECT impl
    # that MUST verify, else the clause is SPEC-TOO-STRONG. The backward
    # accumulating LOOP is replaced by a single straight-line `flatMap
    # mathProtect` over the pre-processed string. `flatMap mathProtect` equals
    # the front-recursive `protectSeq` (a one-line induction discharged by an
    # in-body `have`, no new top-level lemma), so the single load-bearing clause
    # still holds. The `prove_correct` body is retuned (the loop's drop-step
    # lemma no longer applies) while the obligation statement stays
    # byte-identical.
    # =====================================================================
    {
        "id": "pos-control-flatmap",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl_proof(
            "    let s := reSub text\n"
            "    let result := s.flatMap mathProtect\n"
            '    let out := removeEmpty ("$\\\\mathdefault{".toList ++ result ++ "}$".toList)\n'
            "    return out",
            "prove_correct renderTexLabel by\n"
            "  loom_solve\n"
            "  have hfm : ∀ l : List Char, l.flatMap mathProtect = protectSeq l := by\n"
            "    intro l\n"
            "    induction l with\n"
            "    | nil => rfl\n"
            "    | cons c cs ih => rw [List.flatMap_cons, protectSeq_cons, ih]\n"
            "  rw [hfm]"),
        "rationale": "a correct reshape — the backward accumulating loop replaced "
                     "by a single `flatMap mathProtect` over the pre-processed "
                     "string, which equals the front-recursive `protectSeq` (a "
                     "one-line induction closed by an in-body `have`, no new "
                     "top-level lemma). The load-bearing clause still holds and "
                     "the obligation statement is byte-identical; if it failed to "
                     "verify the clause would be SPEC-TOO-STRONG on impl shape.",
    },

    # =====================================================================
    # ADMISSIBILITY (PRECOND-TOO-STRONG lane). The obligation carries no
    # ``require``, but the lane is NOT vacuous: on a total carrier the analogue
    # of a too-strong precondition is the OBLIGATION being unsatisfiable at
    # exactly an F2P-shaped input. This case tests that directly. It keeps the
    # frozen impl and the frozen closing tactics VERBATIM, and prepends two
    # ``have``s that must be discharged BY EVALUATION at a concrete in-domain
    # label carrying all three protected code points plus ordinary digits:
    #   hadm     — the fold's image at that label is the expected protected
    #              string (computed, not assumed);
    #   hnondeg  — that image is NOT the bare input, so the obligation is
    #              non-degenerate there (a spec whose fold collapsed to the
    #              identity would satisfy hadm and fail hnondeg).
    # If either could not be established the obligation would be unsatisfiable
    # at a normal label => PRECOND-TOO-STRONG. Negative control (audited, not
    # shipped): the same case with a WRONG expected image fails at the `have`
    # with goal `False`, so the evaluation genuinely discriminates.
    # =====================================================================
    {
        "id": "adm-indomain-label",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl_proof(
            _GOLD_IMPL,
            "prove_correct renderTexLabel by\n"
            "  have hadm : protectSeq \"01-02 04:00\".toList\n"
            "      = \"01{-}02\\\\;04{:}00\".toList := by\n"
            "    simp [protectSeq, mathProtect]\n"
            "  have hnondeg : protectSeq \"01-02 04:00\".toList "
            "≠ \"01-02 04:00\".toList := by\n"
            "    rw [hadm]\n"
            "    simp\n"
            "  loom_solve\n"
            "  rw [protectSeq_drop_step (reSub text) i (by omega) (by omega)]\n"
            "  simp_all"),
        "rationale": "PRECOND-TOO-STRONG probe, re-expressed for a total "
                     "carrier with no `require`: the analogue is the obligation "
                     "being unsatisfiable at an F2P-shaped input. The case keeps "
                     "the frozen impl and closing tactics verbatim and adds two "
                     "in-body `have`s discharged BY EVALUATION at a concrete "
                     "in-domain label bearing all three protected code points "
                     "and ordinary digits: the fold's image there is the "
                     "expected protected string (`hadm`), and that image is not "
                     "the bare input (`hnondeg`, non-degeneracy). Both must "
                     "verify; if the obligation could not be discharged at such "
                     "a label the precondition surface would be too strong. The "
                     "`have`s are not vacuous — the same shape with a wrong "
                     "expected image fails at the `have` with goal `False`.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # concrete pre-processor image and the refinement argument that its faithful
    # real counterpart would NOT resolve the failing test. Every witness
    # conditions on the opaque carrier (the pre-processor image and the collapse
    # separating rival from gold); the gate's consistency probe confirms the two
    # hypotheses are jointly satisfiable. Witnesses vary the `text` binder over
    # four distinct points.
    # =====================================================================
    {
        "id": "weak-drop-space",
        "kind": "uniqueness",
        "expect": "reject",
        # Protects '-' and ':' but lets ' ' pass through bare. Correct on any
        # label without a space; diverges on the space code point.
        "module": _impl(_straight_line(_DROP_SPACE)),
        "refinement": "a faithful counterpart that omits the space substitution "
                      "leaves inter-number spacing bare in the math group, so a "
                      "label containing a space renders with the numbers run "
                      "together. The failing tests expect the thin-space control "
                      "sequence at exactly those positions and compare the "
                      "rendered label string, so the expected string differs and "
                      "the test still fails. It would NOT resolve.",
        "rationale": "REJECT from the load-bearing clause on the space code "
                     "point: the fold maps ' ' to the thin-space token while the "
                     "rival emits the bare space, so the assembled string before "
                     "the collapse differs and the collapse separates them (`h2`). "
                     "If this verified the clause would be SPEC-TOO-WEAK on the "
                     "space branch. Refuted at a multi-code-point pre-processor "
                     "image `['1', ' ', '2']` (space between numbers, where the "
                     "divergence is observable).",
        "witness": _witness(
            "['1', ' ', '2']", "['1', ' ', '2']",
            "['1', ' ', '2']", "protectSeq ['1', ' ', '2']"),
    },
    {
        "id": "weak-drop-colon",
        "kind": "uniqueness",
        "expect": "reject",
        # Protects '-' and ' ' but lets ':' pass through bare. This is the
        # prepatch-class defect extended to keep the space fix; still wrong on any
        # colon.
        "module": _impl(_straight_line(_DROP_COLON)),
        "refinement": "a faithful counterpart that omits the colon substitution "
                      "leaves the colon bare in the math group, where the "
                      "typesetter spaces it like a binary operator. The failing "
                      "tests expect the braced colon token and compare the "
                      "rendered label, so the expected string differs and the "
                      "test still fails. It would NOT resolve.",
        "rationale": "REJECT from the load-bearing clause on the colon code "
                     "point: the fold maps ':' to the braced token while the rival "
                     "emits the bare colon, so the pre-collapse strings differ and "
                     "the collapse separates them (`h2`). Verifying would be "
                     "SPEC-TOO-WEAK on the colon branch. Refuted at the "
                     "pre-processor image `[':']`.",
        "witness": _witness("[':']", "[':']", "[':']", '"{:}".toList'),
    },
    {
        "id": "weak-drop-dash",
        "kind": "uniqueness",
        "expect": "reject",
        # Protects ':' and ' ' but lets '-' pass through bare. The dash is the
        # single code point the pre-change behavior already handled, so this
        # isolates the dash branch on its own.
        "module": _impl(_straight_line(_DROP_DASH)),
        "refinement": "a faithful counterpart that omits the hyphen substitution "
                      "leaves the hyphen bare in the math group, where it is "
                      "typeset as a minus/binary operator with surrounding space. "
                      "The failing tests expect the braced hyphen token and "
                      "compare the rendered label, so the expected string differs "
                      "and the test still fails. It would NOT resolve.",
        "rationale": "REJECT from the load-bearing clause on the dash code point: "
                     "the fold maps '-' to the braced token while the rival emits "
                     "the bare dash, so the pre-collapse strings differ and the "
                     "collapse separates them (`h2`). Verifying would be "
                     "SPEC-TOO-WEAK on the dash branch. Refuted at the "
                     "pre-processor image `['-']`.",
        "witness": _witness("['-']", "['-']", "['-']", '"{-}".toList'),
    },
    {
        "id": "weak-wrong-space-token",
        "kind": "uniqueness",
        "expect": "reject",
        # Protects all three code points, but emits the space token with its two
        # code points SWAPPED: ";\\" instead of "\\;". Correct on labels without a
        # space; wrong ORDERING on any space. Attacks the space branch's VALUE
        # (not its presence), the sub-domain weak-drop-space does not reach.
        "module": _impl(_straight_line(_WRONG_SPACE)),
        "refinement": "a faithful counterpart that emits the two code points of "
                      "the thin-space token in the wrong order produces a "
                      "malformed control sequence where the tests expect the "
                      "thin-space command, so the rendered label differs and the "
                      "test still fails. It would NOT resolve.",
        "rationale": "REJECT from the load-bearing clause on the space code "
                     "point's VALUE: the fold maps ' ' to the thin-space token "
                     "while the rival emits the two code points swapped, so the "
                     "pre-collapse strings differ and the collapse separates them "
                     "(`h2`). This attacks the token VALUE, a sub-domain "
                     "weak-drop-space (which drops the token entirely) does not "
                     "reach. Refuted at the pre-processor image `[' ']`.",
        "witness": _witness("[' ']", "[' ']", '";\\\\".toList', '"\\\\;".toList'),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 7 SPEC cases (1 soundness
# positive, 1 admissibility, 5 uniqueness rivals) contracting one function
# `protect_codepoints(text)` over a permission-bearing `List[int]` with the same
# load-bearing per-code-point substitution. This bundle models the same operation
# as `renderTexLabel` over the referentially-transparent `List Char`, with the
# input pre-processor and the empty-group collapse as unchanged OPAQUE callees
# (mapping.md §3.2). Every sibling case is accounted for below.
#
#   sibling case                          -> here
#   ---------------------------------------------------------------------
#   pos-control-branch-reorder             -> pos-control-flatmap        PORTED
#                                             (loop -> flatMap; reshape kept
#                                              proof-closing on this carrier)
#   frame-mutation-write-input             -> (none)                     VACUOUS
#   partial-domain-drop-space              -> weak-drop-space            PORTED
#   partial-domain-drop-colon              -> weak-drop-colon            PORTED
#   partial-domain-wrong-space-token       -> weak-wrong-space-token     PORTED
#   partial-domain-last-element-identity   -> weak-drop-dash             RE-AIMED
#   admissibility-indomain-input           -> adm-indomain-label         PORTED
#                                             (re-expressed: obligation
#                                              satisfiable at an F2P-shaped
#                                              label, by evaluation)
#
# 5 ported (1 positive + 3 partial-domain + 1 admissibility), 1 re-aimed,
# 1 dropped (vacuous). No case was dropped because its proof was hard.
#
# VACUOUS (frame-mutation-write-input): the sibling's MANDATORY frame rival writes
#   through a 1/2 (read-only) permission and is rejected for insufficient
#   permission. This backend is referentially transparent: `text` is an immutable
#   value, NOT a `mut` binder; there is no heap, no aliasing and no permission
#   system to trip. No read-only input to overwrite and no substitute probe to
#   build. Not fabricated.
# PORTED (admissibility-indomain-input -> adm-indomain-label): the method carries
#   no `require`, and an earlier revision of this manifest recorded the lane as
#   N/A for that reason. That reasoning was WRONG and is corrected here: on a
#   total carrier the analogue of PRECOND-TOO-STRONG is the OBLIGATION being
#   unsatisfiable at exactly an F2P-shaped input, which a positive that
#   discharges the obligation at that concrete input — by evaluation, as a
#   `have`, before closing the frozen obligation verbatim — tests directly. So
#   the lane is expressible here, and it is now exercised rather than argued
#   away; all three directions this gate exists to test are present.
# RE-AIMED (partial-domain-last-element-identity -> weak-drop-dash): the sibling's
#   off-by-one skips the FIRST-PROCESSED (last-index) element of the backward
#   loop. On this carrier the correct impl is expressible straight-line (the
#   positive control proves it), and the loop's index geometry is not an
#   observable of the spec — the spec pins only the OUTPUT string. The
#   discriminable analogue that stays faithful to "a protected code point left
#   bare" is dropping the dash branch: it is the third per-code-point protection
#   (the other two are covered by weak-drop-space / weak-drop-colon) and the one
#   code point the pre-change behavior already handled, so isolating it completes
#   the attack on all three branches of the per-code-point map.
#
# BINDER / CLAUSE COVERAGE. The single load-bearing clause pins the whole output
#   to `protectSeq (preprocess text)`; its three protected code points are the
#   entire content of the change, and ALL THREE branches of the per-code-point
#   map are attacked: dash (weak-drop-dash), colon (weak-drop-colon), space
#   (weak-drop-space drops it, weak-wrong-space-token corrupts its value). The
#   clause is defended by the positive control. The lone input binder `text` is
#   varied across four DISTINCT pre-processor images (pts=4):
#     text -> ['1',' ','2']   weak-drop-space        (space between numbers)
#     text -> [':']           weak-drop-colon
#     text -> ['-']           weak-drop-dash
#     text -> [' ']           weak-wrong-space-token
#   No point is pinned across the battery; the space branch is probed at two
#   distinct points (a multi-code-point image and the bare space) attacking two
#   distinct sub-domains (token absence vs token value). The admissibility case
#   adds a fifth, longer in-domain point ("01-02 04:00") carrying all three
#   protected code points at once alongside ordinary digits, which is the only
#   place the fold's interaction across branches is evaluated rather than
#   assumed. All three kind lanes are populated (soundness / uniqueness /
#   admissibility).
#
# CARRIER NOTE (why every witness conditions). The postcondition RHS is
#   `removeEmpty (prefix ++ protectSeq (preprocess text) ++ suffix)` with BOTH the
#   pre-processor and the OUTERMOST collapse uninterpreted opaque axioms (no
#   constraining `ensures`; unchanged context callees, mapping.md §3.2). No
#   literal input computes — the pre-processor sits between `text` and the fold.
#   So each witness fixes the pre-processor image (`h1`, about the input callee)
#   and assumes the collapse separates the rival's assembled string from gold's
#   (`h2`, about the output callee). The two hypotheses are about DIFFERENT opaque
#   terms and the two collapse arguments genuinely differ, so they are jointly
#   satisfiable (the gate's consistency probe confirms it). This is the only route
#   to a refutation on a doubly-opaque carrier; a positives-only battery would be
#   NO-REJECT-LANE, which the gate refuses to spell SOUND.
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job; `reSub`/`removeEmpty`
#   (determinism only) and the `protectSeq` deep-model reference (== the real
#   chained substitution) are validated there (axiom_check.py). This gate ignores
#   AXIOM_TESTS.
AXIOM_TESTS = []
