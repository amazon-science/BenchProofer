r"""properties.py — G-PBT falsification battery for django__django-11099 (lean).

NOT a Lean file; a record of adversarial cases the G-PBT gate executes and
stamps a verdict onto. Each SPEC case is a full ``Solution.lean`` variant that
shares the FROZEN spec byte-for-byte (region surgery: only text inside a
``-- impl-start`` / ``-- impl-end`` region — and, for a case that legitimately
re-proves, inside the matching ``-- proof-start`` / ``-- proof-end`` region — is
changed, so ``markers.same_spec`` holds and each ``theorem correct_*`` STATEMENT
stays byte-identical). ``expect="verify"`` passes iff (in scope AND the file
elaborates with the obligation closed, no ``sorry``/``admit``/``native_decide``
and no new ``axiom``/``theorem``); ``expect="reject"`` passes iff (in scope AND
it does NOT verify AND the case's refutation ``witness`` holds of the rival while
FAILING on the frozen solution).

DEFENDED SURFACE (two modeled obligations, one input binder each). Two
admissibility checks are modeled, differing only in which single characters they
treat as allowed:

  validateAscii   (username : List Char) : Bool
  validateUnicode (username : List Char) : Bool

each pinned by the SAME shape of postcondition:

  result = (!username.isEmpty && username.all isAllowed*)

i.e. admissible exactly when the sequence is NON-EMPTY *and* EVERY one of its
characters — the very last included — belongs to the relevant allowed set. The
per-character membership test (``isAllowedAscii`` / ``isAllowedUnicode``) is an
unchanged building block and is left ABSTRACT (``opaque``); only the
whole-sequence rule is modeled.

ADVERSARIAL READ of the nagini classes on this carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS. The nagini sibling holds the input at
    a half-permission (read-only) and makes its MANDATORY frame-mutation rival
    write to it. Lean is referentially transparent: ``username`` carries no heap
    permission, there is no read-only fraction to overwrite and no aliasing to
    exploit. That class has no expressible instance here and NO substitute is
    fabricated for it (see ``assessment``).

  * MEMBERSHIP-CLASS / TERMINAL-LINE-BREAK ORACLE — FULLY EXPRESSIBLE. The
    nagini battery's sharpest rival is the pre-patch skeleton that tolerates one
    terminating line-break character; its refutation there is that the LAST code
    point is not permitted. It transfers to this carrier directly, and the
    ``terminal-break-tolerated`` cases below are it.

    The per-character predicate is ``opaque``, so ``isAllowedAscii '\n'`` does
    NOT evaluate and ``decide`` on it is stuck — but a witness never has to
    EVALUATE the guard. It states its refutation at a point described by
    HYPOTHESIS (``isAllowedAscii '\n' = false``, the real callee's own behavior,
    pinned outside Lean by G-AX / G-CONF), and the gate's consistency probe then
    confirms those hypotheses are jointly satisfiable — which an opaque term
    makes easy, since no tactic can derive ``False`` from an assumption about its
    value. So the LITERAL discriminating character can be named after all, at the
    literal two-element input, and the rival that is exactly the pre-patch shape
    is refutable rather than merely reshaped.

    The structural generalization is kept alongside it: ``weak-*-skip-last``
    exempts the final position for an ARBITRARY disallowed character, so the pair
    tests the clause both at the concrete character the behavior turns on and in
    the general last-position form.

  * NON-EMPTY GUARD and DECISION POLARITY — FULLY TRANSPARENT. ``!username.isEmpty``
    and the overall equality are stated over the input's own structure, so a rival
    that drops the emptiness guard is refuted at ``[]`` by pure computation, and a
    rival that inverts the decision is refuted at a singleton by ``!b ≠ b`` for the
    opaque ``b`` — neither needs the callee's value.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen loop-fold proof is tuned to the frozen
``Id.run do`` form — so a rejection alone attributes nothing to the spec. Every
``expect="reject"`` case therefore carries a Lean snippet proving the rival
CONTRADICTS the spec at one concrete (or one carrier-conditioned) input. Each was
built against its rival (must elaborate) and against the frozen solution (must
FAIL, i.e. gold satisfies the spec there, so the witness discriminates rather
than asserting a tautology). Every conditioned witness carries head hypotheses
about the opaque predicate; each one's consistency probe (``False`` from the
hypotheses alone) was checked to FAIL, so the refuting input genuinely exists.

Each conditioned witness was additionally FORGERY-tested: the same snippet with
its claim FLIPPED (the leading ``¬`` dropped, i.e. asserting the impl is CORRECT
at that input) was built on both sides. Every flip reversed both exit codes —
it ELABORATES against the frozen solution and FAILS against the rival, the exact
mirror of the witness. So the gold-side exit code tracks what is CLAIMED and is
not an artifact of an unfolding failure, a missing instance, or a stuck
reduction; each gold-side failure is a genuine ``⊢ False`` residual left after
the concrete equation was evaluated.

BINDER / CLAUSE COVERAGE. Each spec has the single input binder ``username``. The
reject witnesses probe it at DISTINCT points — ``[]`` (drop-guard), a singleton
(inverted polarity), a two-element list whose final character is an arbitrary
disallowed one (skip-last), and a two-element list whose final character is the
LITERAL terminating line-break character (terminal-break-tolerated) — so the
battery demonstrates the spec's dependence on the emptiness guard, on the
completeness of the traversal, and on the specific terminal position whose
treatment the modeled behavior turns on. Both obligations are defended (a
``pos-*`` soundness positive) and attacked by every reject class.

AXIOM lane: dropped. ``isAllowedAscii`` / ``isAllowedUnicode`` are the unchanged
per-character building block; their real-callee soundness (``[\w.@+-]`` under each
regex flag, line feed excluded) is G-AX's job (axiom_check.py / conformance_check.py),
not this gate's. AXIOM_TESTS is therefore omitted.

NAGINI CASE-BY-CASE ACCOUNTING (what transferred, what did not, and why):

  1  pos-control-ascii-conjunctive         -> pos-ascii-direct-expression, plus a
                                             mirror on the second obligation.
  2  admiss-ascii-read-input               -> RESHAPED, not dropped. The nagini
     probe asserts the read-only permission grant is held; this carrier has no
     permission to hold, so the transferable content is that the obligation is
     SATISFIABLE at the inputs that matter. Landed three ways: at the guard
     boundary ``[]``, and at the F2P shape (allowed run + disallowed terminal
     character) on BOTH obligations, each pinning the decided value there.
  3  frame-mutation-ascii-overwrite        -> INEXPRESSIBLE, and this one really
     is. The nagini rival's rejection comes from the PERMISSION SYSTEM: the input
     is held at ``Acc(...,1/2)`` and the rival writes to it. Lean's ``username :
     List Char`` is a value; there is no fraction to overwrite, no aliasing, and
     no permission judgment to violate. Any "mutation" a variant could write here
     would be a rebinding that produces a different value — which is just a wrong
     impl, already covered by the rivals below, not a frame violation. No
     substitute is fabricated.
  4  partial-domain-ascii-trailing-lf-tolerated
                                           -> weak-ascii-terminal-break-tolerated
  6  partial-domain-unicode-trailing-lf-tolerated
                                           -> weak-unicode-terminal-break-tolerated
     Both LANDED. See the terminal-break note above: the abstract per-character
     test does not block these, because the witness hypothesizes the terminal
     character's non-membership instead of evaluating it.
  5  partial-domain-ascii-skip-last        -> weak-*-skip-last-character (both
     obligations), the same clause in its general last-position form.
  7  support-ascii-inverted-decision       -> weak-ascii-inverted-decision.

  ADDED beyond the sibling: a drop-the-non-empty-guard rival on each obligation.
  Nagini has no counterpart (its `if n == 0` guard is not separately attacked);
  on this carrier the guard is a distinct conjunct of the postcondition and is
  refutable at ``[]`` by pure computation, so it is cheap to defend and would
  otherwise be the one clause with no rival aimed at it.
"""
from pathlib import Path

INSTANCE = "django__django-11099"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Region anchors. Each is a contiguous slice living ENTIRELY inside one region
# (impl or proof), unique in the file. The two impl bodies are structurally
# identical, disambiguated by the `Ascii` / `Unicode` token in the def name.
# ---------------------------------------------------------------------------

# Full ASCII impl def (unique via `_validateAscii`); anchor for impl reshapes.
_ASCII_IMPL = (
    "def implementation_validateAscii (username : List Char) : Bool := Id.run do\n"
    "  if username.isEmpty then\n"
    "    return false\n"
    "  let mut ok := true\n"
    "  for c in username do\n"
    "    if !isAllowedAscii c then\n"
    "      ok := false\n"
    "  return ok\n"
)
# Full Unicode impl def (unique via `_validateUnicode`).
_UNI_IMPL = (
    "def implementation_validateUnicode (username : List Char) : Bool := Id.run do\n"
    "  if username.isEmpty then\n"
    "    return false\n"
    "  let mut ok := true\n"
    "  for c in username do\n"
    "    if !isAllowedUnicode c then\n"
    "      ok := false\n"
    "  return ok\n"
)
# Frozen ASCII proof body head (unique: only the ASCII proof opens this way).
_ASCII_PROOF_HEAD = (
    "  intro username\n"
    "  unfold problem_spec_validateAscii\n"
    "  by_cases h : username.isEmpty = true\n"
)
# Frozen Unicode proof body head (unique: only the Unicode proof opens with the
# `key` generalization). Anchor for the Unicode admissibility `have`.
_UNI_PROOF_HEAD = (
    "  intro username\n"
    "  have key :"
)
# Frozen ASCII proof body in full — for the soundness reshape that reproves.
_ASCII_PROOF_FULL = (
    "  intro username\n"
    "  unfold problem_spec_validateAscii\n"
    "  by_cases h : username.isEmpty = true\n"
    "  · obtain ⟨hl, hr⟩ := empty_branch username h\n"
    "    rw [hl, hr]\n"
    "  · unfold implementation_validateAscii\n"
    "    simp only [h, Bool.false_eq_true, if_false, Bool.not_false, Bool.true_and]\n"
    "    exact (loop_eq_fold true username).trans\n"
    "      ((fold_eq_all true username).trans (by simp))\n"
)
# Frozen Unicode proof body in full — for the soundness reshape that reproves.
_UNI_PROOF_FULL = (
    "  intro username\n"
    "  have key : ∀ (l : List Char) (r : Bool),\n"
    "      (forIn (m := Id) l r (fun c r =>\n"
    "        if !isAllowedUnicode c then pure (ForInStep.yield false)\n"
    "        else pure (ForInStep.yield r))) = (r && l.all isAllowedUnicode) := by\n"
    "    intro l\n"
    "    induction l with\n"
    "    | nil => intro r; simp only [List.forIn_nil, List.all_nil, Bool.and_true]; rfl\n"
    "    | cons a as ih =>\n"
    "      intro r\n"
    "      rw [List.forIn_cons]\n"
    "      by_cases h : isAllowedUnicode a\n"
    "      · simp only [h, Bool.not_true, Bool.false_eq_true, ↓reduceIte, ih, List.all_cons, Bool.true_and]\n"
    "        rfl\n"
    "      · simp only [h, Bool.not_false, ↓reduceIte, ih, List.all_cons, Bool.false_and, Bool.and_false]\n"
    "        rfl\n"
    "  unfold problem_spec_validateUnicode implementation_validateUnicode\n"
    "  cases username with\n"
    "  | nil => rfl\n"
    "  | cons a as =>\n"
    "    simp only [Id.run, List.isEmpty_cons, Bool.false_eq_true, ↓reduceIte, bind_pure_comp, map_pure]\n"
    "    rw [show (forIn (m := Id) (a::as) true (fun c r => if !isAllowedUnicode c then pure (ForInStep.yield false) else pure (ForInStep.yield r))) = _ from key (a::as) true]\n"
    "    simp\n"
)


SPEC_TESTS = [

    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # implementations that MUST verify. If a faithful correct implementation
    # cannot satisfy the frozen obligation the spec is SPEC-TOO-STRONG. Each
    # keeps the `theorem correct_*` statement byte-identical and REPROVES the
    # reshaped impl inside the proof region; no helper lemma, axiom, or
    # assumption token is introduced.
    # =====================================================================
    {
        "id": "pos-ascii-direct-expression",
        "kind": "soundness",
        "expect": "verify",
        # Collapse the mutable-accumulator `for` loop into the direct boolean
        # expression the spec pins. Observationally identical on every input, so
        # the postcondition holds definitionally and the proof is `rfl`.
        "module": _swap(
            _swap(
                _BASE, _ASCII_IMPL,
                "def implementation_validateAscii (username : List Char) : Bool :=\n"
                "  !username.isEmpty && username.all isAllowedAscii\n",
            ),
            _ASCII_PROOF_FULL,
            "  intro username\n"
            "  rfl\n",
        ),
        "rationale": "a correct reshape of the accumulator loop into the direct "
                     "`!username.isEmpty && username.all isAllowedAscii` computes "
                     "the SAME value on every input, so it must satisfy the "
                     "postcondition; if it cannot, the spec is SPEC-TOO-STRONG. "
                     "The reshaped impl is definitionally the spec's right-hand "
                     "side, so the reproof is `rfl` (no lemma/axiom introduced).",
    },
    {
        "id": "pos-unicode-direct-expression",
        "kind": "soundness",
        "expect": "verify",
        # Same reshape on the international-letter obligation: the patch fixes
        # BOTH checks, so BOTH must be defended by a correct positive.
        "module": _swap(
            _swap(
                _BASE, _UNI_IMPL,
                "def implementation_validateUnicode (username : List Char) : Bool :=\n"
                "  !username.isEmpty && username.all isAllowedUnicode\n",
            ),
            _UNI_PROOF_FULL,
            "  intro username\n"
            "  rfl\n",
        ),
        "rationale": "the direct-expression reshape of the second obligation "
                     "computes the SAME value on every input and so must verify; "
                     "if it cannot, the spec is SPEC-TOO-STRONG. Reproof is `rfl` "
                     "(the impl is definitionally the spec RHS). Defends the "
                     "second modeled obligation, which the fix touches too.",
    },

    {
        # The two positives above collapse the impl into LITERALLY the spec's
        # right-hand side, so their reproof is `rfl` and they are definitionally
        # the frozen decision — honest, but they establish only that the spec is
        # satisfiable by its own transcription. This one is a reshape that is NOT
        # definitionally the spec RHS: it recurses on the list, splitting the
        # non-empty guard into the `match` and computing the head's membership
        # separately from the tail's. `rfl` does NOT close it; the reproof needs a
        # genuine case split. If a faithful correct impl of this shape could not
        # be proven, the spec would be SPEC-TOO-STRONG in a way the `rfl`
        # positives cannot detect.
        "id": "pos-ascii-match-recursive",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _swap(
                _BASE, _ASCII_IMPL,
                "def implementation_validateAscii (username : List Char) : Bool :=\n"
                "  match username with\n"
                "  | [] => false\n"
                "  | c :: cs => isAllowedAscii c && cs.all isAllowedAscii\n",
            ),
            _ASCII_PROOF_FULL,
            "  intro username\n"
            "  unfold problem_spec_validateAscii\n"
            "  cases username with\n"
            "  | nil => rfl\n"
            "  | cons c cs => simp [implementation_validateAscii]\n",
        ),
        "rationale": "a correct reshape that is NOT definitionally the spec's "
                     "right-hand side: the emptiness guard becomes the `match` "
                     "arm and the head's membership is computed separately from "
                     "the tail's. It agrees with the pinned decision on every "
                     "input (`all` over `c :: cs` is exactly `isAllowedAscii c && "
                     "cs.all isAllowedAscii`, and the empty case is `false` on "
                     "both sides), so it MUST verify; if it cannot, the spec is "
                     "SPEC-TOO-STRONG. Unlike the direct-expression positives its "
                     "reproof needs a real case split rather than `rfl`, so it "
                     "tests that the obligation is provable for a shape the frozen "
                     "proof script was not written against.",
    },

    # =====================================================================
    # ADMISSIBILITY — a positive control confirming the obligation is
    # SATISFIABLE (non-vacuous) at a boundary input rather than only provable in
    # the abstract. The frozen theorem carries NO precondition hypothesis (the
    # modeled behavior is total, so `∀` is unguarded), which leaves the nagini
    # precondition-admission probe no binder to attack; the honest analogue is to
    # discharge the spec predicate at a ground boundary input (the empty
    # sequence, the guard's own boundary) by `decide`, alongside the frozen
    # obligation. If that ground instance could not be discharged the modeled
    # behavior would be unsatisfiable at the boundary the spec pins.
    # =====================================================================
    {
        "id": "admiss-ascii-empty-ground-instance",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _ASCII_PROOF_HEAD,
            "  have _ground : problem_spec_validateAscii []\n"
            "      (implementation_validateAscii []) := by\n"
            "    unfold problem_spec_validateAscii implementation_validateAscii\n"
            "    decide\n"
            "  intro username\n"
            "  unfold problem_spec_validateAscii\n"
            "  by_cases h : username.isEmpty = true\n",
        ),
        "rationale": "the obligation is discharged at the ground boundary input "
                     "(the empty sequence, which the non-empty guard must reject) "
                     "by `decide`, then the frozen obligation is closed verbatim. "
                     "Verifies (else the spec is unsatisfiable at its own guard "
                     "boundary, the analogue of PRECOND-TOO-STRONG). Nothing is "
                     "assumed: no new declaration, the theorem statement is "
                     "byte-identical, the ground instance is a `have` inside the "
                     "existing tactic body.",
    },
    {
        # The `[]` ground instance above is a BOUNDARY input, but it is not the
        # shape the modeled behavior turns on. This one discharges the obligation
        # at the F2P shape itself: an allowed run followed by a DISALLOWED
        # terminal character. That input is where a satisfiable-looking spec would
        # be unsatisfiable if the postcondition over-constrained the terminal
        # position, so it is the direct analogue of PRECOND-TOO-STRONG on a total
        # carrier. It also pins the VERDICT there (`= false`), so the `have` is not
        # merely a restatement: it asserts what the spec decides at that input.
        "id": "admiss-ascii-f2p-shape-terminal-disallowed",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _ASCII_PROOF_HEAD,
            "  have _f2p : ∀ c : Char, isAllowedAscii 'a' = true →\n"
            "      isAllowedAscii c = false →\n"
            "      problem_spec_validateAscii ['a', c]\n"
            "        (implementation_validateAscii ['a', c])\n"
            "      ∧ implementation_validateAscii ['a', c] = false := by\n"
            "    intro c ha hc\n"
            "    unfold problem_spec_validateAscii implementation_validateAscii\n"
            "    simp [ha, hc]\n"
            + _ASCII_PROOF_HEAD,
        ),
        "rationale": "discharges the obligation at the F2P-shaped input — an "
                     "allowed character followed by a disallowed TERMINAL one — "
                     "and simultaneously pins the decision there to `false`, "
                     "before closing the frozen obligation verbatim. If that "
                     "instance could not be discharged the spec would be "
                     "unsatisfiable at exactly the input the modeled behavior "
                     "turns on (PRECOND-TOO-STRONG analogue on a total carrier). "
                     "Stated over an arbitrary disallowed `c` under hypotheses, "
                     "since the per-character test is abstract; no new "
                     "declaration, statement byte-identical.",
    },
    {
        "id": "admiss-unicode-f2p-shape-terminal-disallowed",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _UNI_PROOF_HEAD,
            "  have _f2p : ∀ c : Char, isAllowedUnicode 'a' = true →\n"
            "      isAllowedUnicode c = false →\n"
            "      problem_spec_validateUnicode ['a', c]\n"
            "        (implementation_validateUnicode ['a', c])\n"
            "      ∧ implementation_validateUnicode ['a', c] = false := by\n"
            "    intro c ha hc\n"
            "    unfold problem_spec_validateUnicode implementation_validateUnicode\n"
            "    simp [ha, hc]\n"
            + _UNI_PROOF_HEAD,
        ),
        "rationale": "the same F2P-shaped satisfiability check on the SECOND "
                     "modeled obligation, which the fix touches too: the "
                     "obligation is discharged at an allowed character followed "
                     "by a disallowed terminal one, with the decision pinned to "
                     "`false`, before the frozen obligation is closed verbatim. "
                     "Without this the admissibility lane would defend only one "
                     "of the two obligations.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong implementations sharing the
    # frozen spec that MUST be rejected. Each carries (a) the refinement
    # argument that its faithful real patch would NOT resolve, so a verifying
    # rival would be a true verify-does-not-imply-resolve break, and (b) a
    # refutation witness pinning the violation at one input. The witnesses spread
    # the single binder `username` across `[]`, a singleton, and a two-element
    # list with a disallowed final character.
    # =====================================================================
    {
        "id": "weak-ascii-drop-nonempty-guard",
        "kind": "uniqueness",
        "expect": "reject",
        # Drop the non-empty guard: return `username.all isAllowedAscii`, which is
        # `true` on the empty sequence (vacuous `all`). Attacks the emptiness
        # clause.
        "module": _swap(
            _BASE, _ASCII_IMPL,
            "def implementation_validateAscii (username : List Char) : Bool :=\n"
            "  username.all isAllowedAscii\n",
        ),
        "refinement": "dropping the non-empty requirement corresponds to a class "
                      "pattern without the one-or-more quantifier (matching the "
                      "empty string), so an EMPTY username is accepted. The "
                      "validators must reject a blank username (the `+` in the "
                      "pattern is one-or-more); a patch that admits it regresses "
                      "the validator's non-empty guarantee and is not the faithful "
                      "fix — it would not resolve.",
        "rationale": "REJECT from the `!username.isEmpty && ...` clause: on `[]` "
                     "the spec requires `false` (empty is rejected) but the rival "
                     "returns `true` (vacuous `all`). Refuted at the empty "
                     "sequence — the binder value no other rival probes.",
        "witness": (
            "example : ¬ problem_spec_validateAscii []\n"
            "    (implementation_validateAscii []) := by\n"
            "  unfold problem_spec_validateAscii implementation_validateAscii\n"
            "  simp\n"
        ),
    },
    {
        "id": "weak-ascii-skip-last-character",
        "kind": "uniqueness",
        "expect": "reject",
        # Check only `username.dropLast`: the FINAL character is never tested
        # against the allowed set. This is the `$`-tolerance clause generalized —
        # a string with one unchecked terminal position is admitted.
        "module": _swap(
            _BASE, _ASCII_IMPL,
            "def implementation_validateAscii (username : List Char) : Bool :=\n"
            "  !username.isEmpty && username.dropLast.all isAllowedAscii\n",
        ),
        "refinement": "exempting the final character from the class check is "
                      "exactly the tolerance the fix removes: a terminal character "
                      "outside the allowed set (a line feed being the case the "
                      "issue names) is admitted. Such a patch still accepts a "
                      "username with a disallowed trailing character, so it does "
                      "NOT resolve the added trailing-character test.",
        "rationale": "REJECT from the whole-sequence traversal clause (every "
                     "character through the last must be allowed): on a two-element "
                     "input whose final character is NOT allowed, the rival ignores "
                     "it and returns `true`, but the spec requires `false`. "
                     "Refuted by CONDITIONING on the opaque predicate (prefix "
                     "allowed, final disallowed) — a two-element input, the only "
                     "setting that exercises the last-position clause and one no "
                     "other rival probes.",
        "witness": (
            # `isAllowedAscii` is opaque, so no literal character decides; state
            # the refutation at a carrier point described by hypotheses. Its
            # consistency probe (`False` from h1,h2 alone) FAILS, so this input
            # genuinely exists. Holds of the rival; FAILS on gold (gold checks the
            # final character, so its result is `false = false`, satisfying spec).
            "example (h1 : isAllowedAscii 'a' = true) (h2 : isAllowedAscii 'b' = false) :\n"
            "    ¬ problem_spec_validateAscii ['a', 'b']\n"
            "    (implementation_validateAscii ['a', 'b']) := by\n"
            "  unfold problem_spec_validateAscii implementation_validateAscii\n"
            "  simp [h1, h2]\n"
        ),
    },
    {
        "id": "weak-ascii-inverted-decision",
        "kind": "uniqueness",
        "expect": "reject",
        # Return the negation of the pinned decision. Mechanical, but pins the
        # polarity of the result: it accepts exactly the invalid usernames and
        # rejects the valid ones.
        "module": _swap(
            _BASE, _ASCII_IMPL,
            "def implementation_validateAscii (username : List Char) : Bool :=\n"
            "  !(!username.isEmpty && username.all isAllowedAscii)\n",
        ),
        "refinement": "returning the inverse decision accepts every invalid "
                      "username and rejects every valid one, the opposite of the "
                      "validator — it resolves nothing and regresses every "
                      "accept/reject the validator makes.",
        "rationale": "REJECT from the result equality: `!x` contradicts the pinned "
                     "`x` on any input where the two differ. Refuted at a singleton "
                     "(non-empty, so the decision reduces to `isAllowedAscii 'a'`) "
                     "via `!b ≠ b`, holding for the opaque `b` regardless of its "
                     "value — the singleton binder value, a third distinct point.",
        "witness": (
            "example : ¬ problem_spec_validateAscii ['a']\n"
            "    (implementation_validateAscii ['a']) := by\n"
            "  unfold problem_spec_validateAscii implementation_validateAscii\n"
            "  cases h : isAllowedAscii 'a' <;> simp [h]\n"
        ),
    },
    {
        "id": "weak-unicode-drop-nonempty-guard",
        "kind": "uniqueness",
        "expect": "reject",
        # Mirror of the emptiness attack on the second obligation.
        "module": _swap(
            _BASE, _UNI_IMPL,
            "def implementation_validateUnicode (username : List Char) : Bool :=\n"
            "  username.all isAllowedUnicode\n",
        ),
        "refinement": "same as the ASCII drop-guard rival on the second modeled "
                      "check: a pattern without the one-or-more quantifier accepts "
                      "the empty username, which the validator must reject — not "
                      "the faithful fix, would not resolve.",
        "rationale": "REJECT from the `!username.isEmpty && ...` clause of the "
                     "SECOND obligation: on `[]` the spec requires `false`, the "
                     "rival returns `true`. Attacks the second obligation (which "
                     "the fix also touches) at the empty sequence.",
        "witness": (
            "example : ¬ problem_spec_validateUnicode []\n"
            "    (implementation_validateUnicode []) := by\n"
            "  unfold problem_spec_validateUnicode implementation_validateUnicode\n"
            "  simp\n"
        ),
    },
    {
        "id": "weak-unicode-skip-last-character",
        "kind": "uniqueness",
        "expect": "reject",
        # Mirror of the last-character attack on the second obligation, so a rival
        # that fixes only one check (leaving the other's terminal tolerance) is
        # caught.
        "module": _swap(
            _BASE, _UNI_IMPL,
            "def implementation_validateUnicode (username : List Char) : Bool :=\n"
            "  !username.isEmpty && username.dropLast.all isAllowedUnicode\n",
        ),
        "refinement": "the second check must ALSO test its terminal character (the "
                      "fix changes both patterns). A rival that exempts the final "
                      "character on this check still admits a username with a "
                      "disallowed trailing character, so it does NOT resolve the "
                      "second obligation's added trailing-character test.",
        "rationale": "REJECT from the whole-sequence traversal clause of the "
                     "SECOND obligation: on a two-element input whose final "
                     "character is not allowed, the rival returns `true`, the spec "
                     "`false`. Refuted by conditioning on the opaque predicate at a "
                     "two-element input.",
        "witness": (
            "example (h1 : isAllowedUnicode 'a' = true) (h2 : isAllowedUnicode 'b' = false) :\n"
            "    ¬ problem_spec_validateUnicode ['a', 'b']\n"
            "    (implementation_validateUnicode ['a', 'b']) := by\n"
            "  unfold problem_spec_validateUnicode implementation_validateUnicode\n"
            "  simp [h1, h2]\n"
        ),
    },

    # =====================================================================
    # THE PRE-PATCH SHAPE ITSELF — the rival whose faithful counterpart is the
    # UNCHANGED pre-fix behavior, i.e. the one rival that is guaranteed not to
    # resolve. It drops a single TERMINATING line-break character before running
    # the whole-sequence check, so an otherwise-allowed run followed by one such
    # character is still admitted.
    #
    # This is the class the port initially recorded as inexpressible on the
    # ground that `isAllowedAscii '\n'` cannot be EVALUATED (the predicate is
    # abstract, so `decide` is stuck). That reasoning conflates evaluating the
    # guard with stating a refutation at it: the witness assumes the terminal
    # character's non-membership as a HYPOTHESIS — the real callee's own behavior,
    # pinned outside Lean by G-AX / G-CONF — and the gate's consistency probe
    # confirms the hypotheses are jointly satisfiable (no tactic can derive
    # `False` from an assumption about an opaque term's value). So the literal
    # discriminating character IS namable here, and these two cases attack the
    # terminal position at that character rather than only in the general form.
    # =====================================================================
    {
        "id": "weak-ascii-terminal-break-tolerated",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _ASCII_IMPL,
            "def implementation_validateAscii (username : List Char) : Bool := Id.run do\n"
            "  let core := if username.getLast? = some '\\n' then username.dropLast\n"
            "              else username\n"
            "  if core.isEmpty then\n"
            "    return false\n"
            "  let mut ok := true\n"
            "  for c in core do\n"
            "    if !isAllowedAscii c then\n"
            "      ok := false\n"
            "  return ok\n",
        ),
        "refinement": "tolerating one terminating line-break character before the "
                      "whole-sequence check IS the pre-fix behavior: the faithful "
                      "counterpart of this rival is the code as it stands before "
                      "the change, which still admits an otherwise-allowed run "
                      "followed by such a character. That is precisely the input "
                      "the added test pins, so this rival resolves nothing — it is "
                      "the strongest available near-miss.",
        "rationale": "REJECT from the whole-sequence clause `result = "
                     "(!username.isEmpty && username.all isAllowedAscii)`: on an "
                     "allowed character followed by the terminating line-break "
                     "character, the rival drops that character and returns "
                     "`true`, while the spec requires `false` because the sequence "
                     "must consist of allowed characters through its very LAST "
                     "one, with no end-of-sequence tolerance. Refuted at the "
                     "literal input `['a', '\\n']`.",
        "witness": (
            # The terminal character is named LITERALLY; only its non-membership
            # is hypothesized, because the per-character test is abstract here.
            # Consistency probe (`False` from h1,h2 alone) FAILS, so the input
            # exists. Holds of the rival; FAILS on gold with a semantic `⊢ False`
            # residual, and the flipped claim reverses both exit codes.
            "example (h1 : isAllowedAscii 'a' = true) (h2 : isAllowedAscii '\\n' = false) :\n"
            "    ¬ problem_spec_validateAscii ['a', '\\n']\n"
            "    (implementation_validateAscii ['a', '\\n']) := by\n"
            "  unfold problem_spec_validateAscii implementation_validateAscii\n"
            "  simp [h1, h2]\n"
        ),
    },
    {
        "id": "weak-unicode-terminal-break-tolerated",
        "kind": "uniqueness",
        "expect": "reject",
        # Mirror on the second obligation: the change touches BOTH checks, so a
        # rival that leaves the second one's terminal tolerance must also fail.
        "module": _swap(
            _BASE, _UNI_IMPL,
            "def implementation_validateUnicode (username : List Char) : Bool := Id.run do\n"
            "  let core := if username.getLast? = some '\\n' then username.dropLast\n"
            "              else username\n"
            "  if core.isEmpty then\n"
            "    return false\n"
            "  let mut ok := true\n"
            "  for c in core do\n"
            "    if !isAllowedUnicode c then\n"
            "      ok := false\n"
            "  return ok\n",
        ),
        "refinement": "the second check must also reject a terminating line-break "
                      "character — the change alters both. A rival that keeps the "
                      "second check's terminal tolerance still admits an "
                      "otherwise-allowed run followed by such a character under "
                      "the wider allowed set, so it does not resolve the second "
                      "obligation's added test.",
        "rationale": "REJECT from the whole-sequence clause of the SECOND "
                     "obligation: on an allowed character followed by the "
                     "terminating line-break character the rival returns `true`, "
                     "the spec requires `false`. Refuted at the literal input "
                     "`['a', '\\n']`, so a rival fixing only the first check is "
                     "caught here.",
        "witness": (
            "example (h1 : isAllowedUnicode 'a' = true) (h2 : isAllowedUnicode '\\n' = false) :\n"
            "    ¬ problem_spec_validateUnicode ['a', '\\n']\n"
            "    (implementation_validateUnicode ['a', '\\n']) := by\n"
            "  unfold problem_spec_validateUnicode implementation_validateUnicode\n"
            "  simp [h1, h2]\n"
        ),
    },
]
