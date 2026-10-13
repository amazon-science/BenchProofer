"""properties.py — G-PBT falsification battery for sphinx-doc__sphinx-11445 (lean).

NOT a Lean file; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region — and, for a case that legitimately re-proves or discharges
a ground instance, inside the ``-- proof-start`` / ``-- proof-end`` region — is
changed, so ``markers.same_spec`` holds and the ``theorem correct_<name>``
STATEMENT stays byte-identical). ``expect:"verify"`` passes iff (in scope AND the
file elaborates with the obligation closed); ``expect:"reject"`` passes iff (in
scope AND it does NOT verify AND the case's refutation ``witness`` holds of the
rival while FAILING on the frozen solution).

DEFENDED SURFACE (one total function over two list inputs):

  placePreamble (body preamble : List String) : List String
      result = placePreambleSpec body preamble
    where
      placePreambleSpec body preamble =
        if preamble = [] then body
        else let k := leadingFieldCount body
             body.take k ++ (if k > 0 then [""] else []) ++ preamble ++ [""]
                          ++ body.drop k

  A document body is a sequence of text lines; a preamble (itself a sequence of
  lines) is spliced in near the top. ``leadingFieldCount body`` is the length of
  the leading run of lines classified as bibliographic FIELD lines by the deeply
  modeled ``isFieldLine`` grammar (opens with a name enclosed in colons followed
  by a space or end of line; a line whose first colon-token is immediately
  followed by back-quoted text is NOT a field line). The preamble is placed
  immediately after those ``k`` lines, with a blank separator before it only when
  ``k > 0`` and a blank separator always after it; an empty preamble leaves the
  body unchanged.

  The single top-level clause (an equality against ``placePreambleSpec``) folds
  several inseparable sub-decisions, each pinned to a distinct binder / input:

    * WHETHER anything is spliced at all — the empty-preamble no-op. Pinned by
      ``preamble``; when ``preamble = []`` the result must equal ``body`` verbatim.
    * HOW MANY leading lines the splice lands after — ``leadingFieldCount body``,
      i.e. exactly the leading run classified by ``isFieldLine``. Pinned by
      ``body``. This subsumes both counting too many / too few field lines and
      classifying the wrong lines as fields (the load-bearing discriminator).
    * WHERE the blank separators and preamble land relative to that count — the
      splice arithmetic ``take k ++ sep ++ preamble ++ [""] ++ drop k``.

ADVERSARIAL READ of the nagini classes on this carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS. The nagini sibling holds ``content``
    at fractional (read-only) permission (a PSeq), so a rival that overwrites an
    input is rejected for insufficient permission. Lean is referentially
    transparent: ``body`` and ``preamble`` are plain immutable ``List String``
    values, there is no half-permission to violate and no aliasing to exploit, so
    this class has NO expressible instance here. No substitute is fabricated.

  * DIVERGENCE / NON-TERMINATION — a KNOWN HOLE, not a vacuous class. An earlier
    revision of this manifest recorded it as vacuous on the ground that "a
    non-terminating implementation cannot be written"; that is FALSE and was
    measured false. The frozen impl is a total ``def`` (a bounded ``for`` over
    ``body`` inside ``Id.run do``) and this backend sets no
    ``loom.semantics.termination`` option, but Lean's ``partial`` keyword opts
    out of the termination checker, so a diverging rival IS writable — a
    ``partial def`` counter that recurses on its argument UNCHANGED
    (``| (x :: xs) => if isFieldLine x.toList then spin (x :: xs) (acc+1) else acc``,
    which never terminates on a body opening with a field line) spliced in place
    of the loop. Built and measured: it is variant-scope admissible
    (``variant_problems`` empty — no new axiom/sorry/theorem, statement
    byte-identical) and the frozen script does NOT close it (exit 1).

    It is nevertheless UNSHIPPABLE as a reject case here, and the reason is the
    witness, not the rival. Both available witness routes were built and both
    fail, for reasons the gate itself screens:
      - stated by EVALUATION at a concrete input, the ``decide`` cannot reduce
        the ``partial`` term — the build fails on the RIVAL (the half that must
        succeed) with "reduction got stuck at the `Decidable` instance … did not
        reduce to `isTrue` or `isFalse`", i.e. the gate's ``witness-undecided``
        screen, so the exit code carries no information about the claim;
      - stated by HYPOTHESIS on the opaque counter's value, the witness must name
        ``spin``, a rival-only declaration, which
        ``pbt_witness.witness_scope_problems`` rejects outright ("declared by the
        variant but not by the frozen solution, so its failure on gold would be
        an unknown name rather than a satisfied spec") — correctly, since gold
        has no such name.
    And the class is a genuine SPEC hole rather than a mere tooling gap: the
    dual claim was built and VERIFIES (exit 0) — under the hypothesis that the
    diverging counter returns the true leading count, the diverging rival
    SATISFIES ``problem_spec_placePreamble`` at that input. So the frozen
    obligation constrains the impl only extensionally, at whatever value the
    opaque term takes, and no input refutes a pure-divergence rival. Recorded as
    a known hole in the SPEC's reach (a total-carrier obligation says nothing
    about a ``partial`` impl's termination), NOT as a vacuous class and NOT as a
    case the battery is missing.

  * UNGROUNDED-ORACLE ECHO — VACUOUS. The postcondition is GROUNDED: an equality
    against ``placePreambleSpec body preamble``, a term built only from the two
    inputs (a ``takeWhile``-based count, ``take``/``drop``, list concatenation and
    concrete blank separators), fully unfolded. The bundle declares no
    ``opaque``/``axiom`` (the ``axioms`` region is empty; the field-line grammar
    is modeled deeply, validated == the real reference matcher by G-CONF, not
    axiomatized), so there is no answer key an implementation could echo without
    doing the work. The honest analogue is the cheapest-correct POSITIVE CONTROL
    below.

  * PARTIAL-DOMAIN / WRONG-PREDICATE (the pre-patch bug) — APPLIES, and is the
    load-bearing rival. The pre-fix classifier accepted any line whose first
    colon-token is followed by ANYTHING (a loose ``:word:`` match), so a leading
    role-heading such as a cross-reference written as a colon-delimited token
    immediately followed by back-quoted text was wrongly counted as a field line,
    splicing the preamble AFTER it and destroying the heading. Refuted exactly on
    that discriminating line.

  * OFF-BY-ONE / CAP / CONSTANT / NO-GUARD — APPLY. Rivals that count one line too
    many past the run, cap the run at one line, never count, or splice even for an
    empty preamble each violate the one clause on a distinct sub-domain and are
    refuted with witnesses at distinct inputs.

  * SPLICE-ARITHMETIC-ONLY — APPLIES, and was MISSING from the first port. Every
    rival in the classes above changes the leading COUNT or whether a splice
    happens at all; none of them keeps the count correct and corrupts only the
    blank-separator layout. Two rivals now do
    (``weak-separator-always``, ``weak-no-trailing-separator``), so the third
    sub-decision is attacked on its own rather than only as a passenger of the
    count. ``weak-separator-always`` is additionally the only rival whose witness
    body has an EMPTY leading field run.

NAGINI CASES DROPPED BY THIS PORT, per-case disposition (re-derived, not
inherited):

  * ``pos-oracle-echo`` — INEXPRESSIBLE as a separate case, and it is the same
    case as this battery's ``pos-functional-splice``. The nagini spec is a
    conjunction whose clause 1 is ``Result() == leading_header_count(content)``
    against a @Pure oracle, so "return the oracle" is a distinct, cheaper impl
    than the gold loop. Here the whole postcondition IS one equality against
    ``placePreambleSpec``, so "echo the grounded oracle" and "spell the spec's
    right-hand side functionally" are the SAME Lean term — the carrier collapses
    the two nagini cases into one, and it is present.
  * ``pos-loop-reshape`` — EXPRESSIBLE, and it was missing. Landed as
    ``pos-loop-hoisted-guard``: the hoisted-guard ``for … if !cont then break``
    loop, whose elaborated ``forIn`` argument the frozen ``loop_helper`` does not
    cover, so the accumulator induction is genuinely re-run. This is the case that
    distinguishes "a different correct SHAPE verifies" from "a restatement of the
    spec's own right-hand side verifies"; without it the only positive closed by
    ``rfl``.
  * ``admiss-f2p-shaped`` — ported as ``admiss-role-heading-ground``, with the
    obligation discharged at the ground input rather than via a self-call (Lean
    has no precondition binder to admit; see that case's rationale).
  * ``reject-off-by-one-over`` / ``reject-cap-at-one`` / ``reject-prepatch-
    predicate`` / ``reject-constant-zero`` — all four ported, one-for-one.
  * ``ax-isheaderline-soundness`` (AXIOM_TESTS) — INEXPRESSIBLE in this lane. It
    is a runtime differential of the deep model against the real reference
    matcher, which on this backend is G-CONF's obligation (recorded pass: 0
    disagreements) and G-AX's skip, not something the spec lane re-runs.
  * The nagini sibling carries NO ``diverge-*`` / ``nonterm-*`` case, so nothing
    was dropped from that lane; its disposition here is nevertheless a known
    hole rather than a vacuous class — see the DIVERGENCE entry above, which an
    independent audit corrected after building the diverging rival.

INDEPENDENT AUDIT (adversarial re-derivation; every number below is an observed
exit code, not an expectation):

  * STATEMENT INTEGRITY — all 10 cases: the ``theorem correct_placePreamble``
    statement is byte-identical to the frozen one (raw slice compare, not just
    whitespace-normalized), and ``variant_problems`` is empty for each.
  * WITNESS DISCRIMINATION, re-derived for all 7 reject cases: rival build exit
    0, gold build exit 1 in every case, and every gold-side failure is the SAME
    plain-evaluation signature — ``Tactic `decide` proved that the proposition
    ¬(…) is false``, i.e. the kernel EVALUATED the concrete claim and found the
    frozen impl satisfies the spec there. No stuck reduction, no missing
    identifier, no type error, no timeout.
  * FORGERY TEST (attack B′) run anyway, on all 7: the claim was flipped (the
    leading ``¬`` dropped, asserting the frozen impl is WRONG at that input) and
    rebuilt against the frozen solution. 6 of 7 flip to exit 0 — the error
    disappears entirely when the claim changes — and the seventh
    (``weak-no-empty-preamble-guard``) flips to a DIFFERENT error at exit 1
    (``No goals to be solved``: ``simp`` alone closes the positive claim, leaving
    ``decide`` nothing to do). Either way gold's exit code tracks the claim, so
    none of these cases is hollow.
  * RIVALS ARE OBSERVABLY WRONG (attack C), by ``#eval`` of each rival's impl
    against ``placePreambleSpec`` over 9 input points: every one of the 7 rivals
    disagrees with the spec on at least one point, so no case is vacuous by
    definitional collapse. The two splice-arithmetic rivals were confirmed to
    agree with gold on the leading COUNT and differ only in separator placement,
    which is what their rationales claim.
  * SPEC-TOO-WEAK probe (attack D) — 6 NEW wrong impls this battery does not
    contain, aimed at the least-probed clauses: separator/preamble order swapped;
    count ALL field lines rather than the leading run; no-op guard weakened to
    ``preamble.length <= 1``; classifier accepting only ``:name:`` at end of line
    (rejecting ``:name: value``); the "first name char is not a space" guard
    dropped; ``drop (pos + 1)`` (loses a line). ALL SIX were rejected (exit 1).
    No spec hole found.
  * SPEC-TOO-STRONG probe (attack E) — 2 NEW correct reshapes: (a) the
    empty-preamble guard written as the Bool ``preamble.isEmpty`` instead of the
    decidable ``preamble = []`` — VERIFIES (exit 0); (b) the splice expressed as
    ``takeWhile``/``dropWhile`` instead of ``take k``/``drop k``, with the
    take/drop-equals-takeWhile/dropWhile bridge proved inline by induction —
    VERIFIES (exit 0). Both faithful correct reshapes are accepted, so no
    soundness hole in the spec was found in this direction.
  * The ``pos-loop-hoisted-guard`` proof burden is REAL, not decorative: that
    case's impl was rebuilt with the FROZEN tactic body left untouched and it
    FAILS (exit 1, ``rewrite failed: Did not find an occurrence of the pattern
    forIn … if isFieldLine … then ForInStep.yield``), confirming ``loop_helper``
    genuinely does not apply to the reshaped ``forIn`` argument.
  * The ``admiss-role-heading-ground`` ground instance DISCRIMINATES: the same
    ``simp``+``decide`` ground claim was built as a standalone ``example``
    against the frozen impl (exit 0) and against the pre-patch loose-classifier
    impl (exit 1). So it is a real evaluation of the F2P-shaped input, not a
    tautology that any impl would discharge.
  * PROSE SPOT-CHECK by evaluation: every concrete value asserted in every
    rationale was confirmed by ``#eval`` (the classifier's verdict on
    ``:mod:`foo``` = false, ``:a:``/``:b:``/``:a: x`` = true,
    ``hello``/``sub`` = false; the leading counts 0/1/2/0; and all seven
    spec-vs-rival result lists). The refinement claims about the real expected
    line sequences were checked against the actual test expectations at the base
    commit: the two F2P bodies do open with the role heading and expect the
    preamble BEFORE it, every expectation supplies a non-empty preamble (so the
    ``weak-no-empty-preamble-guard`` honest-scope note is accurate, including its
    explicit refusal to claim a does-not-resolve near-miss), and every
    expectation carries a blank line immediately after the preamble.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen script is tuned to the frozen form — so
a rejection alone attributes nothing to the spec. Every ``expect="reject"`` case
therefore carries a Lean snippet stating the spec predicate directly at a concrete
input; each was checked (with ``scripts/lean_verify.sh``, obligations removed) to
HOLD of its rival and to FAIL on the frozen solution (so it discriminates rather
than asserting a tautology). ``fieldMarkerScan`` uses well-founded recursion, so
``decide`` alone gets stuck on the ``String.toList``/``takeWhile`` reduction; the
witnesses ``simp`` with the classifier's equational lemmas and then close the
residual concrete-list inequality with ``decide``. All witness inputs are concrete
literals — no opaque terms, so no carrier-conditioning and no satisfiability
hazard.

BINDER / CLAUSE COVERAGE. Both input binders are varied across the reject
witnesses so the battery exercises the spec's dependence on each:
  * ``body`` — refuted at a leading role-heading line ``:mod:`foo``` (wrong
    predicate), at a single field line ``:a:`` (off-by-one, constant, no-guard,
    no-trailing-separator), at a two-field run ``[:a:, :b:]`` (cap-at-one), and at
    a body with NO leading field line at all, ``["hello"]``
    (separator-always) — so the zero-field-run, single-field-run and
    multi-field-run sub-domains are each probed. The ``["hello"]`` point matters
    beyond arity: it is the only witness input on which ``leadingFieldCount = 0``
    *and* the classifier is not the thing under attack, which is what isolates the
    ``if k > 0`` separator clause.
  * ``preamble`` — held at ``["P"]`` for six rivals and at ``[]`` (empty) for the
    no-guard rival, so the empty-preamble no-op clause is attacked and that binder
    is not pinned to one value across the lane.
  * CLAUSE coverage, which binder-arity alone does not show: of the three folded
    sub-decisions, WHETHER-to-splice is attacked by ``weak-no-empty-preamble-
    guard``, HOW-MANY by four rivals, and WHERE-the-separators-land by
    ``weak-separator-always`` + ``weak-no-trailing-separator``. Before those last
    two the third sub-decision had no rival that varied it alone.
The distinct input points are: ``[":mod:`foo`", "sub"]/["P"]``,
``[":a:", "x"]/["P"]`` (two rivals, different clauses),
``[":a:", ":b:", "y"]/["P"]``, ``[":a:", "y"]/["P"]``, ``[":a:", "y"]/[]``,
``["hello"]/["P"]`` — pts = 6.

AXIOM lane: EMPTY. The ``axioms`` region is empty and there are no ``opaque``
callees; the field-line grammar is modeled deeply and its equivalence to the real
reference matcher is a G-CONF (conformance) obligation, not an in-model
axiom-soundness one. That lane belongs to G-AX in any case. AXIOM_TESTS is empty.
"""
from pathlib import Path

INSTANCE = "sphinx-doc__sphinx-11445"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- region anchors (each unique inside Solution.lean; verified at load) ----
# The FULL impl-region body, and the FULL frozen tactic body, so every
# replacement lands entirely inside the region it means to edit.
_IMPL_GOLD = (
    "def implementation_placePreamble\n"
    "    (body preamble : List String) : List String := Id.run do\n"
    "  if preamble = [] then\n"
    "    return body\n"
    "  -- count the consecutive leading field lines\n"
    "  let mut pos := 0\n"
    "  for line in body do\n"
    "    if isFieldLine line.toList then\n"
    "      pos := pos + 1\n"
    "    else\n"
    "      break\n"
    "  let head := body.take pos\n"
    "  let tail := body.drop pos\n"
    "  let sep := if pos > 0 then ([\"\"] : List String) else []\n"
    "  return head ++ sep ++ preamble ++ [\"\"] ++ tail"
)

_PROOF_BODY = (
    "  intro body preamble\n"
    "  unfold problem_spec_placePreamble implementation_placePreamble placePreambleSpec\n"
    "  by_cases hp : preamble = []\n"
    "  · simp only [hp, if_true, Id.run]; rfl\n"
    "  · have hloop : Id.run (forIn body 0 (fun line r =>\n"
    "        if isFieldLine line.toList = true then\n"
    "          (do pure PUnit.unit; pure (ForInStep.yield (r + 1)))\n"
    "        else pure (ForInStep.done r))) = leadingFieldCount body := by\n"
    "      rw [loop_helper, leadingFieldCount, Nat.zero_add]\n"
    "    simp only [hp, if_false, Id.run, bind, pure] at *\n"
    "    rw [hloop]"
)

# A smaller unique anchor inside the impl region for point edits.
_HEAD_ANCHOR = "  let head := body.take pos"

# The separator and the return line, each unique inside the impl region: the two
# point edits that keep the leading COUNT correct and change only the splice
# arithmetic, so the third sub-decision is attacked independently of the count.
_SEP_ANCHOR = '  let sep := if pos > 0 then ([""] : List String) else []'
_RET_ANCHOR = '  return head ++ sep ++ preamble ++ [""] ++ tail'

# sanity: the frozen anchors are present exactly once
assert _BASE.count(_IMPL_GOLD) == 1, "impl region drifted; update _IMPL_GOLD"
assert _BASE.count(_PROOF_BODY) == 1, "proof region drifted; update _PROOF_BODY"
assert _BASE.count(_HEAD_ANCHOR) == 1, "head anchor drifted; update _HEAD_ANCHOR"
assert _BASE.count(_SEP_ANCHOR) == 1, "sep anchor drifted; update _SEP_ANCHOR"
assert _BASE.count(_RET_ANCHOR) == 1, "return anchor drifted; update _RET_ANCHOR"


def _impl(body):
    """Build a full Solution.lean variant by replacing the gold impl body."""
    return _swap(_BASE, _IMPL_GOLD, body)


# The witness tactic prelude/closer shared by every reject case. `simp` with the
# classifier's equational lemmas reduces the deeply-recursive `fieldMarkerScan`
# and the `takeWhile`-based count on the concrete literal; `decide` then closes
# the residual concrete-list (in)equality. Stated directly on the spec predicate.
_WSIMP = ("simp [implementation_placePreamble, placePreambleSpec, leadingFieldCount, "
          "List.takeWhile, isFieldLine, fieldMarkerScan, Id.run, pure]")


def _witness(bodyv, prev):
    return (
        f"example : ¬ problem_spec_placePreamble {bodyv} {prev}\n"
        f"    (implementation_placePreamble {bodyv} {prev}) := by\n"
        f"  unfold problem_spec_placePreamble\n"
        f"  {_WSIMP}\n"
        f"  decide\n"
    )


# ---------------------------------------------------------------------------
# Rival impl bodies (each is a full impl region; only the impl changes, so the
# spec and the theorem STATEMENT stay byte-identical).
# ---------------------------------------------------------------------------

# WRONG-PREDICATE (= the pre-fix bug): classify a leading line with a LOOSE
# recogniser — a line is accepted iff it opens with a colon, its first name char
# is neither colon nor space, and it contains ANY later colon, REGARDLESS of what
# follows that colon. This wrongly accepts a colon-delimited role token followed
# by back-quoted text (`:mod:`foo``), which the field-marker grammar rejects.
_PREPATCH = (
    "def implementation_placePreamble\n"
    "    (body preamble : List String) : List String := Id.run do\n"
    "  if preamble = [] then\n"
    "    return body\n"
    "  let mut pos := 0\n"
    "  for line in body do\n"
    "    let accept :=\n"
    "      match line.toList with\n"
    "      | (':' :: d :: rest) =>\n"
    "        if d == ':' || d == ' ' then false else rest.any (· == ':')\n"
    "      | _ => false\n"
    "    if accept then\n"
    "      pos := pos + 1\n"
    "    else\n"
    "      break\n"
    "  let head := body.take pos\n"
    "  let tail := body.drop pos\n"
    "  let sep := if pos > 0 then ([\"\"] : List String) else []\n"
    "  return head ++ sep ++ preamble ++ [\"\"] ++ tail"
)

# OFF-BY-ONE-OVER: count one extra line past the leading field run whenever the
# body is longer than the run — splices the preamble one line PAST the true
# boundary.
_OVER = _IMPL_GOLD.replace(
    _HEAD_ANCHOR,
    "  if pos < body.length then\n    pos := pos + 1\n" + _HEAD_ANCHOR, 1)

# CAP-AT-ONE: cap the leading count at one field line — on a run longer than one
# the preamble lands between the field lines.
_CAP1 = _IMPL_GOLD.replace(
    _HEAD_ANCHOR,
    "  if pos > 1 then\n    pos := 1\n" + _HEAD_ANCHOR, 1)

# CONSTANT-ZERO: never count any leading field line — the preamble is always
# spliced at the very top, before any leading field block.
_ZERO = (
    "def implementation_placePreamble\n"
    "    (body preamble : List String) : List String := Id.run do\n"
    "  if preamble = [] then\n"
    "    return body\n"
    "  let pos := 0\n"
    "  let head := body.take pos\n"
    "  let tail := body.drop pos\n"
    "  let sep := if pos > 0 then ([\"\"] : List String) else []\n"
    "  return head ++ sep ++ preamble ++ [\"\"] ++ tail"
)

# NO-GUARD: drop the empty-preamble short-circuit — splice (with trailing blank
# separator) even when the preamble is empty, mutating a body that must be left
# verbatim.
_NOGUARD = (
    "def implementation_placePreamble\n"
    "    (body preamble : List String) : List String := Id.run do\n"
    "  let mut pos := 0\n"
    "  for line in body do\n"
    "    if isFieldLine line.toList then\n"
    "      pos := pos + 1\n"
    "    else\n"
    "      break\n"
    "  let head := body.take pos\n"
    "  let tail := body.drop pos\n"
    "  let sep := if pos > 0 then ([\"\"] : List String) else []\n"
    "  return head ++ sep ++ preamble ++ [\"\"] ++ tail"
)

# SEPARATOR-ALWAYS: emit the leading blank separator unconditionally, i.e. even
# when the leading field run is EMPTY. The leading COUNT is exactly the frozen
# one, so this attacks the splice-arithmetic sub-decision (`if k > 0 then [""]
# else []`) on its own, at a body with no leading field line.
_SEP_ALWAYS = _IMPL_GOLD.replace(
    _SEP_ANCHOR, '  let sep := ([""] : List String)', 1)

# NO-TRAILING-BLANK: drop the blank separator that must always follow the
# preamble. Again the leading count is exactly the frozen one, so this isolates
# the other half of the splice arithmetic (the unconditional trailing `[""]`).
_NO_TRAIL = _IMPL_GOLD.replace(
    _RET_ANCHOR, "  return head ++ sep ++ preamble ++ tail", 1)

# POSITIVE CONTROL (soundness): a structurally different but CORRECT impl — a
# direct functional expression (no `Id.run do` / `let mut` / `for`), spelling the
# whole result as the spec's own `placePreambleSpec` body. Same value on every
# input; the frozen loop-based script (loop_helper, forIn) no longer applies to
# the new shape, so the obligation is re-proved (statement byte-identical, no new
# lemma / axiom / assumption token — after `unfold` both sides are the same term,
# closed by `rfl`).
_POS_FUNC = (
    "def implementation_placePreamble\n"
    "    (body preamble : List String) : List String :=\n"
    "  if preamble = [] then body\n"
    "  else\n"
    "    let k := leadingFieldCount body\n"
    "    body.take k ++ (if k > 0 then [\"\"] else []) ++ preamble ++ [\"\"] ++ body.drop k"
)
_POS_PROOF = (
    "  intro body preamble\n"
    "  unfold problem_spec_placePreamble implementation_placePreamble placePreambleSpec\n"
    "  rfl"
)

# POSITIVE CONTROL 2 (soundness): a RESHAPED LOOP that is still correct and still
# carries a real proof burden. `_POS_FUNC` above is the cheapest honest positive
# (after `unfold` it is syntactically the spec's own right-hand side, so `rfl`
# closes it and no induction is re-run); this one keeps the imperative
# `Id.run do … for … break` shape but HOISTS the per-line guard into a local
# boolean and breaks on its negation, so the elaborated `forIn` body is
# `if (!isFieldLine …) = true then ForInStep.done r else ForInStep.yield (r + 1)`
# — a different functional argument from the frozen one. The frozen `loop_helper`
# is stated over the frozen guard shape, so it NO LONGER APPLIES: the accumulator
# induction has to be redone for the reshaped loop, which is exactly the burden a
# spec-too-strong probe should have to discharge. This is the lean analogue of the
# nagini `pos-loop-reshape` case (its hoisted-guard `while True / if not cont:
# break`), which the port dropped without recording it.
_POS_LOOP = (
    "def implementation_placePreamble\n"
    "    (body preamble : List String) : List String := Id.run do\n"
    "  if preamble = [] then\n"
    "    return body\n"
    "  let mut pos := 0\n"
    "  for line in body do\n"
    "    let cont := isFieldLine line.toList\n"
    "    if !cont then\n"
    "      break\n"
    "    pos := pos + 1\n"
    "  let head := body.take pos\n"
    "  let tail := body.drop pos\n"
    "  let sep := if pos > 0 then ([\"\"] : List String) else []\n"
    "  return head ++ sep ++ preamble ++ [\"\"] ++ tail"
)
# Re-proved for the reshaped loop: the same Route-B accumulator induction as
# `loop_helper`, but stated over the hoisted-guard functional argument (note the
# `!` and the `ForInStep.done`/`yield` branches swapped relative to the frozen
# lemma). No new top-level declaration: the helper is a `have` inside the existing
# tactic body, the theorem STATEMENT is byte-identical, and there is no new
# axiom / `sorry` / assumption token.
_POS_LOOP_PROOF = (
    "  intro body preamble\n"
    "  unfold problem_spec_placePreamble implementation_placePreamble placePreambleSpec\n"
    "  by_cases hp : preamble = []\n"
    "  · simp only [hp, if_true, Id.run]; rfl\n"
    "  · simp only [hp, if_false, Id.run, bind, pure] at *\n"
    "    have hloop : ∀ (b : List String) (init : Nat),\n"
    "        (forIn b init (fun (line : String) (r : Nat) =>\n"
    "          if (!isFieldLine line.toList) = true then ForInStep.done r\n"
    "          else ForInStep.yield (r + 1)) : Id Nat)\n"
    "        = init + (b.takeWhile (fun l => isFieldLine l.toList)).length := by\n"
    "      intro b init\n"
    "      induction b generalizing init with\n"
    "      | nil => rfl\n"
    "      | cons a as ih =>\n"
    "        rw [List.forIn_cons]\n"
    "        simp only [bind, pure] at ih ⊢\n"
    "        by_cases h : isFieldLine a.toList = true\n"
    "        · simp only [h, Bool.not_true, Bool.false_eq_true, if_false,\n"
    "            List.takeWhile_cons, if_true]\n"
    "          rw [ih]\n"
    "          simp only [List.length_cons, Nat.add_assoc, Nat.add_comm]\n"
    "        · simp only [h, Bool.not_false, if_true, List.takeWhile_cons,\n"
    "            if_false, Bool.false_eq_true, List.length_nil, Nat.add_zero]\n"
    "    rw [hloop, leadingFieldCount, Nat.zero_add]"
)

# ADMISSIBILITY (positive control): discharge the spec predicate at the F2P
# ground input (a leading role-heading line that the grammar must NOT count, so
# the preamble lands BEFORE it) inside the proof region, alongside the frozen
# obligation. The frozen `theorem correct_placePreamble` carries no precondition
# hypothesis (the behavior is total), so nagini's precondition-admission probe has
# no binder to attack; the honest analogue is that the modeled behavior is
# satisfiable at exactly the input the F2P exercises. Nothing is assumed: the
# theorem STATEMENT is byte-identical, the ground instance is a `have` inside the
# existing tactic body, and no new declaration / axiom / `sorry` is introduced.
_ADMISS_GROUND = (
    "  have _ground : problem_spec_placePreamble [\":mod:`foo`\", \"sub\"] [\"P\"]\n"
    "      (implementation_placePreamble [\":mod:`foo`\", \"sub\"] [\"P\"]) := by\n"
    "    unfold problem_spec_placePreamble\n"
    "    simp [implementation_placePreamble, placePreambleSpec, leadingFieldCount,\n"
    "      List.takeWhile, isFieldLine, fieldMarkerScan, Id.run, pure]\n"
    "    decide\n"
)


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROL (soundness) — a structurally different but CORRECT impl
    # that MUST verify. If a faithful correct impl cannot satisfy the frozen
    # obligation the spec is SPEC-TOO-STRONG. The `theorem correct_placePreamble`
    # STATEMENT is byte-identical; the tactic body is re-proved for the new shape
    # (the frozen `loop_helper`/`forIn` script is tuned to the `Id.run do … for`
    # form). No helper lemma, axiom, or assumption token is introduced.
    # =====================================================================
    {
        "id": "pos-functional-splice",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_impl(_POS_FUNC), _PROOF_BODY, _POS_PROOF),
        "rationale": (
            "a correct reshape that drops the mutable-accumulator `Id.run do … "
            "for … break` loop and spells the whole result as one functional "
            "expression (`if preamble = [] then body else let k := "
            "leadingFieldCount body; body.take k ++ … ++ body.drop k`) must satisfy "
            "`result = placePreambleSpec body preamble`; if it cannot, the spec is "
            "SPEC-TOO-STRONG. Proof: after `unfold` both sides are the same "
            "let/if/concat term, so the goal closes by `rfl` — no new declaration, "
            "axiom, or assumption token, and the theorem statement is unchanged."
        ),
    },

    # =====================================================================
    # POSITIVE CONTROL 2 (soundness) — a correct RESHAPED LOOP whose proof burden
    # is real: the hoisted-guard `for … if !cont then break` elaborates to a
    # different `forIn` functional argument, so the frozen `loop_helper` no longer
    # applies and the accumulator induction is redone from scratch. Distinguishes
    # "the spec admits a genuinely different correct SHAPE" from
    # "the spec admits a restatement of its own right-hand side" — the first
    # positive closes by `rfl` and so cannot make that distinction on its own.
    # =====================================================================
    {
        "id": "pos-loop-hoisted-guard",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_impl(_POS_LOOP), _PROOF_BODY, _POS_LOOP_PROOF),
        "rationale": (
            "a correct reshape that KEEPS the imperative `Id.run do … for … break` "
            "shape but hoists the per-line test into a local boolean and breaks on "
            "its negation must still satisfy `result = placePreambleSpec body "
            "preamble`; if it cannot, the spec is SPEC-TOO-STRONG. Unlike "
            "`pos-functional-splice` (which after `unfold` IS the spec's own "
            "right-hand side and closes by `rfl`), the reshaped loop elaborates to "
            "`if (!isFieldLine line.toList) = true then ForInStep.done r else "
            "ForInStep.yield (r + 1)` — a functional argument the frozen "
            "`loop_helper` is not stated over — so the Route-B accumulator "
            "induction is re-run inside the proof body as a `have`. Statement "
            "byte-identical; no new declaration, axiom, or assumption token."
        ),
    },

    # =====================================================================
    # ADMISSIBILITY — a positive control confirming the obligation is SATISFIABLE
    # (non-vacuous) at the normal, F2P-shaped input rather than only provable in
    # the abstract. The frozen theorem carries NO precondition hypothesis, so
    # nagini's precondition-admission probe has no binder to attack here; the
    # honest analogue is to discharge the spec predicate at the F2P ground input
    # inside the proof region, alongside the frozen obligation.
    # =====================================================================
    {
        "id": "admiss-role-heading-ground",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _PROOF_BODY, _ADMISS_GROUND + _PROOF_BODY),
        "rationale": (
            "the obligation is discharged at the F2P ground input (a leading line "
            "`:mod:`foo`` that is a colon-delimited role token followed by "
            "back-quoted text — NOT a field line — so the leading field count is 0 "
            "and the preamble `[\"P\"]` must land BEFORE it, yielding `[\"P\", "
            "\"\", \":mod:`foo`\", \"sub\"]`), by `simp`+`decide`; then the frozen "
            "obligation is closed verbatim. Verifies (else the spec is unsatisfiable "
            "at the normal input, the analogue of PRECOND-TOO-STRONG). Nothing is "
            "assumed: the theorem STATEMENT is byte-identical, the ground instance "
            "is a `have` inside the existing tactic body, and no new "
            "declaration/axiom/`sorry` is introduced."
        ),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec that
    # MUST be rejected. Each carries (a) the refinement argument that its faithful
    # real patch would NOT resolve the F2P, so a verifying rival would be a true
    # verify-does-not-imply-resolve break rather than an artifact, and (b) a
    # refutation witness pinning the violation at one concrete input.
    # =====================================================================
    {
        "id": "weak-prepatch-loose-classifier",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_PREPATCH),
        "refinement": (
            "this IS the pre-fix behavior: a loose leading-line classifier that "
            "accepts a line as long as it opens with a colon-delimited token and "
            "contains any later colon, ignoring what follows the closing colon. Its "
            "faithful real patch is exactly the pre-patch matcher, which counts a "
            "leading role-heading (a colon-delimited role token immediately "
            "followed by back-quoted text) as a leading field line and splices the "
            "preamble AFTER it — destroying the heading. That is the ORIGINAL BUG, "
            "so the F2P observable (the role heading must survive, with the preamble "
            "before it) fails. It does NOT resolve — this is the load-bearing "
            "discriminator of the whole instance."
        ),
        "rationale": (
            "REJECT from the clause `result = placePreambleSpec body preamble` via "
            "the `leadingFieldCount` sub-decision: at `body = [\":mod:`foo`\", "
            "\"sub\"]`, `preamble = [\"P\"]`, the grammar classifies the role "
            "heading as NOT a field line (leading count 0), so the spec demands "
            "`[\"P\", \"\", \":mod:`foo`\", \"sub\"]`, but the loose classifier "
            "accepts it (count 1) and yields `[\":mod:`foo`\", \"\", \"P\", \"\", "
            "\"sub\"]`. Refuted on `body` at the role-heading line — the "
            "discriminating sub-domain."
        ),
        "witness": _witness('[":mod:`foo`", "sub"]', '["P"]'),
    },
    {
        "id": "weak-off-by-one-over",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_OVER),
        "refinement": (
            "counting one line past the leading field run whenever the body is "
            "longer than the run inserts the preamble one line PAST the true "
            "boundary — on any document it splits the first non-field line away "
            "from the header block, so the spliced layout the F2P asserts is wrong. "
            "It does NOT resolve."
        ),
        "rationale": (
            "REJECT from the clause `result = placePreambleSpec body preamble`: at "
            "`body = [\":a:\", \"x\"]`, `preamble = [\"P\"]` the true leading count "
            "is 1, so the spec demands `[\":a:\", \"\", \"P\", \"\", \"x\"]`, but "
            "the rival counts 2 and yields `[\":a:\", \"x\", \"\", \"P\", \"\"]`. "
            "Refuted on `body` at a single-field run (count > 0), the sub-domain "
            "where the off-by-one advances past a real boundary."
        ),
        "witness": _witness('[":a:", "x"]', '["P"]'),
    },
    {
        "id": "weak-cap-at-one",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_CAP1),
        "refinement": (
            "capping the leading field count at one line inserts the preamble "
            "BETWEEN the field lines of a multi-line leading header block — the "
            "spliced layout is wrong on any document opening with two or more field "
            "lines. It does NOT resolve."
        ),
        "rationale": (
            "REJECT from the clause `result = placePreambleSpec body preamble`: at "
            "`body = [\":a:\", \":b:\", \"y\"]`, `preamble = [\"P\"]` the true "
            "leading count is 2, so the spec demands `[\":a:\", \":b:\", \"\", "
            "\"P\", \"\", \"y\"]`, but the cap yields count 1 and `[\":a:\", \"\", "
            "\"P\", \"\", \":b:\", \"y\"]`. Refuted on `body` at a TWO-field run — a "
            "multi-field sub-domain distinct from the other rivals'."
        ),
        "witness": _witness('[":a:", ":b:", "y"]', '["P"]'),
    },
    {
        "id": "weak-constant-zero",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_ZERO),
        "refinement": (
            "never counting any leading field line always splices the preamble at "
            "the very top, before any leading header block — on a document opening "
            "with field lines the preamble lands before them rather than after, the "
            "wrong layout. It does NOT resolve. (Cheap supporting near-miss; correct "
            "only when there is no leading field run at all.)"
        ),
        "rationale": (
            "REJECT from the clause `result = placePreambleSpec body preamble` "
            "whenever the leading field run is non-empty: at `body = [\":a:\", "
            "\"y\"]`, `preamble = [\"P\"]` the true count is 1, so the spec demands "
            "`[\":a:\", \"\", \"P\", \"\", \"y\"]`, but the constant-zero rival "
            "yields `[\"P\", \"\", \":a:\", \"y\"]` (no separator, spliced at top). "
            "Refuted on `body` at a single-field run."
        ),
        "witness": _witness('[":a:", "y"]', '["P"]'),
    },
    {
        "id": "weak-no-empty-preamble-guard",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_NOGUARD),
        "refinement": (
            "dropping the empty-preamble short-circuit splices a trailing blank "
            "separator (and the leading separator, when there is a field run) into "
            "a body that must be returned verbatim when there is nothing to "
            "prepend — the document gains spurious blank lines on every "
            "empty-preamble call. HONEST SCOPE (re-derived by simulating this "
            "rival's counter + splice against the real expected line/offset "
            "sequences of the whole modeled test group): every one of those "
            "expectations supplies a NON-empty preamble, so none of them reaches "
            "the empty-preamble branch and this rival passes all of them. Its "
            "faithful real patch is therefore NOT distinguished by the observable "
            "the modeled tests assert; it is a genuine violation of the spec's "
            "empty-preamble no-op clause (the spec is total and quantifies over "
            "`preamble = []`, which the real routine does short-circuit) that the "
            "test group happens not to cover. Kept as a CLAUSE-COVERAGE rival — it "
            "is the only case pinning the `preamble` binder off `[\"P\"]` — and "
            "explicitly NOT claimed as a does-not-resolve near-miss, which is what "
            "an earlier revision of this manifest asserted without deriving it."
        ),
        "rationale": (
            "REJECT from the empty-preamble no-op clause `if preamble = [] then "
            "body`: at `body = [\":a:\", \"y\"]`, `preamble = []` the spec demands "
            "the body verbatim `[\":a:\", \"y\"]`, but the rival splices anyway and "
            "yields `[\":a:\", \"\", \"\", \"y\"]`. This is the only rival varying "
            "`preamble` off `[\"P\"]` (to `[]`), so that binder is exercised and not "
            "pinned to a single value across the lane."
        ),
        "witness": _witness('[":a:", "y"]', '[]'),
    },

    # ---- SPLICE ARITHMETIC, attacked independently of the leading count -------
    # Every rival above changes WHERE the boundary is (the `leadingFieldCount`
    # sub-decision) or WHETHER anything is spliced. These two keep the leading
    # count exactly right and corrupt only the third sub-decision — the separator
    # placement — so a spec that pinned the count but left the blank-line layout
    # loose would be caught here and nowhere else.
    {
        "id": "weak-separator-always",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_SEP_ALWAYS),
        "refinement": (
            "emitting the leading blank separator unconditionally adds a blank "
            "line at the very top of every document that does NOT open with a "
            "field line — the preamble is preceded by a spurious blank where the "
            "modeled behavior emits the separator only to detach the preamble from "
            "a header block that is actually there. Confirmed against the real "
            "expected line/offset sequences: the two no-leading-field expectations "
            "of the modeled group both begin with the preamble's first line, and "
            "this rival puts a blank there instead, so it does NOT resolve."
        ),
        "rationale": (
            "REJECT from the clause `result = placePreambleSpec body preamble` via "
            "the splice-arithmetic sub-decision `if k > 0 then [\"\"] else []`: at "
            "`body = [\"hello\"]`, `preamble = [\"P\"]` the leading field count is "
            "0 (no field line), so the spec demands `[\"P\", \"\", \"hello\"]`, but "
            "the rival yields `[\"\", \"P\", \"\", \"hello\"]`. The leading count "
            "it computes is exactly the frozen one, so this refutes the separator "
            "clause ALONE — and it is the only case whose `body` has an empty "
            "leading field run, a sub-domain no other rival's witness visits."
        ),
        "witness": _witness('["hello"]', '["P"]'),
    },
    {
        "id": "weak-no-trailing-separator",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_NO_TRAIL),
        "refinement": (
            "dropping the blank separator that must always follow the preamble "
            "runs the preamble's last line directly into the next body line, so "
            "the two are parsed as one block. Confirmed against the real expected "
            "line/offset sequences: every expectation in the modeled group carries "
            "a blank line immediately after the preamble, and this rival omits it "
            "in all of them, so it does NOT resolve."
        ),
        "rationale": (
            "REJECT from the clause `result = placePreambleSpec body preamble` via "
            "the splice-arithmetic sub-decision (the unconditional trailing "
            "`[\"\"]`): at `body = [\":a:\", \"x\"]`, `preamble = [\"P\"]` the spec "
            "demands `[\":a:\", \"\", \"P\", \"\", \"x\"]`, but the rival yields "
            "`[\":a:\", \"\", \"P\", \"x\"]`. The leading count and the leading "
            "separator are both exactly the frozen ones, so the refutation is "
            "attributable to the trailing-separator clause alone."
        ),
        "witness": _witness('[":a:", "x"]', '["P"]'),
    },
]


# No consumed axioms and no deep-model `opaque` references: the field-line grammar
# is modeled directly (its equivalence to the real reference matcher is a G-CONF
# obligation, not an in-model axiom-soundness one), so there is no in-model axiom
# obligation for the PBT axiom lane to re-discharge.
AXIOM_TESTS = []
