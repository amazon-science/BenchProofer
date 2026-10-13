"""properties.py — G-PBT falsification battery for sympy__sympy-23950 (lean).

NOT a Lean file; a manifest the G-PBT gate parses. Each SPEC case is a full
``Solution.lean`` variant that shares the FROZEN spec byte-for-byte (region
surgery: only text inside ``-- impl-start`` / ``-- impl-end`` — and, for a case
that legitimately re-proves, inside ``-- proof-start`` / ``-- proof-end`` — is
changed, so ``markers.same_spec`` holds and the ``theorem correct_asSet``
STATEMENT stays byte-identical). ``expect="verify"`` passes iff (in scope AND
the file elaborates with the obligation closed); ``expect="reject"`` passes iff
(in scope AND it does NOT verify AND the case's refutation ``witness`` holds of
the rival while FAILING on the frozen solution).

DEFENDED SURFACE (one modeled total function):

  implementation_asSet (c : MembershipAssertion E S) : Option S

  A membership assertion is built from two operands: an ``element`` (type ``E``)
  and a set operand ``setArg`` (type ``S``). Converting it to a set must ALWAYS
  produce a value and that value must be EXACTLY the set operand, verbatim. The
  postcondition is the single load-bearing clause

    problem_spec_asSet c result := result = some c.setArg

  which fuses two obligations that the F2P observable pins jointly:
    * DEFINEDNESS — the result is ``some _``, never ``none`` (a value is always
      produced; the conversion does not decline).
    * SELECTION — that value is the ``setArg`` operand, taken verbatim (not the
      element, not any other set).

  Input binders of the spec predicate: ``c`` (which decomposes into
  ``c.element : E`` and ``c.setArg : S``) and ``result``.

CARRIER NARROWING — what the abstract carriers do and do NOT collapse.

  The two operands are modeled at DISTINCT abstract carrier types ``E`` (element)
  and ``S`` (set operand), and the result type is ``Option S``. Returning the
  element (``some c.element``) — the headline wrong behaviour — is therefore not a
  spec-sharing rival here, it is a TYPE ERROR, so it cannot even be written
  against the frozen spec, let alone verify. Machine-checked: that impl fails to
  elaborate with ``Application type mismatch: The argument c.element has type E
  but is expected to have type S``. That is the carrier doing the work the nagini
  object-identity postcondition did by hand, so the nagini wrong-component attack
  has no distinct instance to ship.

  What the carriers do NOT do is reduce the reject lane to one rival. An earlier
  revision of this manifest claimed that "by parametricity" a total
  ``∀ {E S}, MembershipAssertion E S → Option S`` has EXACTLY two inhabitants
  (``some c.setArg`` and ``none``), hence one expressible wrong function. That
  claim is FALSE and the audit refuted it with a build: the carrier types are
  ``Type``-indexed VALUES, so an impl may branch on a PROPOSITION about them —
  e.g. decline exactly when the two carriers coincide (``E = S``), via
  ``Classical.propDecidable`` — and return the correct operand everywhere else.
  Such an impl is well-typed, shares the frozen spec, introduces no axiom or
  ``sorry``, and is a genuine PARTIAL-DOMAIN rival: wrong on a sub-domain and
  right off it. It is now shipped as ``rival-declines-on-diagonal``.

  So the reject lane carries TWO rivals, attacking the load-bearing clause on
  different domains:
    * ``rival-produces-no-value`` — declines EVERYWHERE (the total failure of
      DEFINEDNESS; per mapping.md ``none`` models "produces no value").
    * ``rival-declines-on-diagonal`` — declines on a PROPER SUB-DOMAIN and is
      indistinguishable from gold off it, so a battery whose only probe point was
      one arbitrary literal input could miss it. This is the near-miss the
      one-rival reading of the carrier had argued away.

  Both are refuted by their own witness at a concrete input; neither verifies.

ADVERSARIAL READ of the nagini classes on THIS carrier:

  * POSITIVE CONTROL (soundness) — PORTED (nagini ``pos-control-typed-local``),
    and STRENGTHENED by the audit. Two positives now ship, because the ported one
    alone is weak by construction:

      - ``pos-let-binding`` binds the set operand to a local, then returns ``some``
        of it. The local ZETA-REDUCES, so this impl is DEFINITIONALLY EQUAL to the
        frozen one and the frozen ``rfl`` closes it unchanged. That makes it an
        honest but shallow positive: it re-checks that region surgery and the
        scope machinery work, and almost nothing about the spec's strength, since
        no reshape the kernel cannot see through is being asked for.
      - ``pos-guarded-reshape`` is the positive that actually probes
        SPEC-TOO-STRONG. It returns the correct operand from behind a
        classically-decided guard that is ALWAYS taken (the element operand
        witnesses that its carrier is nonempty), so the impl is observably
        correct but NOT definitionally equal to the frozen body: the audit built
        it with the frozen tactic body and the frozen ``rfl`` FAILS ("The
        left-hand side c is not definitionally equal to ... implementation_asSet
        c"). It therefore has to be REPROVEN — the case discharges the guard with
        ``rw [if_pos ⟨c.element⟩]`` and then closes the frozen obligation — which
        is what makes its verification evidence that the spec admits a genuinely
        differently-shaped faithful impl, rather than evidence that the kernel
        unfolded a synonym.

  * ADMISSIBILITY — PORTED (nagini ``admiss-read-both-fields``). The frozen
    theorem carries no precondition hypothesis (the behaviour is total), so the
    honest analogue of the nagini precondition-admission probe is a ground,
    F2P-shaped instance discharged as a ``have`` prepended to the frozen tactic
    body, after which the frozen obligation is closed verbatim. If that ground
    instance could not be discharged, the modeled behaviour would be
    unsatisfiable at exactly the shape the F2P exercises — the analogue of
    PRECOND-TOO-STRONG. Nothing is assumed: no new declaration, the
    ``correct_asSet`` statement is byte-identical.

  * WRONG-COMPONENT (nagini ``wrong-component-return-element``, behaviour (a)) —
    ABSORBED by the carrier into the DEFINEDNESS rival. Returning the element is a
    type error here (``E ≠ S``), so there is no distinct element-return rival to
    ship; the only way to violate SELECTION without a type error is to produce no
    value at all, which is the ``none`` rival. See CARRIER NARROWING; recorded in
    'assessment' as an absorbed (not omitted) case.

  * DEFERRAL / CONTROL-FLOW (nagini ``defer-raise-viewnotproduced`` /
    ``no-return-fallthrough``, behaviour (b)) — PORTED as the ``none`` rival.
    ``none`` is the carrier's model of "raises / produces no value" (mapping.md),
    exactly the pre-patch body. It violates DEFINEDNESS (``result = some _``).

  * FRAME / PERMISSION MUTATION (nagini ``frame-mut-overwrite-region`` /
    ``frame-mut-overwrite-element``) — VACUOUS. Those rivals overwrote a
    half-permission (read-only) input field to satisfy the postcondition
    trivially, rejected by the PERMISSION system. Lean is referentially
    transparent: the input carries no heap permission, there is no read-only
    half-permission to overwrite and no aliasing to exploit. These rivals have NO
    expressible instance here and no substitute is fabricated for them.

  * NON-TERMINATION (nagini ``nonterm-self-recursion`` /
    ``nonterm-infinite-loop``) — KNOWN HOLE, not vacuous. An earlier revision of
    this manifest recorded the class as VACUOUS on the ground that "a diverging
    implementation cannot be written at all". The audit measured that and it is
    wrong on both halves:

      (a) EXPRESSIBLE. ``partial def implementation_asSet ... :=
          implementation_asSet c`` elaborates — ``partial`` accepts the
          self-call without a decreasing measure — and it stays inside variant
          scope (no new axiom / ``sorry`` / theorem; the ``correct_asSet``
          statement is byte-identical). It is REJECTED, as the class wants.
      (b) But it is NOT SHIPPABLE, because it cannot be given a discriminating
          witness. A ``partial def`` is compiled to an opaque constant with no
          equation the kernel can unfold, so every refutation of it is stuck, not
          decided: ``decide`` reports its ``Decidable`` instance "did not reduce
          to `isTrue` or `isFalse`" and a ``simp`` form leaves the goal
          untouched. Conditioning on the value instead (``h : implementation_asSet
          … = none``) does elaborate against the rival — but the audit built the
          same file against the FROZEN solution and it elaborated too (exit 0),
          i.e. that witness is VACUOUS: the hypothesis is unfalsifiable for gold
          as well, so it discriminates nothing. There is no third impl to use as a
          ``witness_reference`` either, since the blocker is the rival's own
          opacity, not gold's reducibility.

    So the correct disposition is a KNOWN HOLE in this bundle's carrier: an impl
    that never produces a value is rejected here only by the frozen tactic
    failing, which is exactly the unattributable rejection the witness rule
    exists to refuse. No reject case is shipped, and this is recorded as a hole
    (the spec is not complete against divergence) rather than as vacuity (which
    would claim the battery is).

  * UNGROUNDED-ORACLE ECHO — N/A (as in nagini). The postcondition is grounded
    directly in the input (``result = some c.setArg``, a verbatim field
    selection, fully unfolded); there is no opaque answer-key to echo. The honest
    analogues are the POSITIVE CONTROL and ADMISSIBILITY cases.

WITNESS. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen ``rfl`` is tuned to the frozen form — so
a rejection alone attributes nothing to the spec. Each ``expect="reject"`` case
therefore carries a Lean snippet proving its rival CONTRADICTS the spec at one
concrete input, and each was machine-checked in BOTH directions (elaborates
against the rival, fails against the frozen solution):

  * ``rival-produces-no-value`` — instantiates the carriers to ``E := Unit``,
    ``S := Nat``, reduces the rival's ``implementation_asSet`` to ``none`` at a
    literal input, and shows ``none ≠ some setArg`` by ``decide``. Against the
    frozen solution the build fails with ``decide`` reporting that the negated
    proposition *is false* — the strongest possible gold-side signal, an outright
    evaluation of the claim rather than a stuck reduction or a missing name.
  * ``rival-declines-on-diagonal`` — probes ``E := Nat``, ``S := Nat``, ON the
    sub-domain where that rival declines; against the frozen solution the same
    statement fails with ``unsolved goals ⊢ False``, again an evaluation of the
    claim.

Both were additionally FORGERY-tested (the audit's attack B′): a second file
differing from each witness ONLY in asserting the OPPOSITE claim (the ``¬``
dropped, i.e. claiming the spec HOLDS at that input) builds with exit 0 against
the frozen solution and exit 1 against the rival — the exact mirror of the
witness. So the gold-side exit code tracks WHAT IS CLAIMED and carries real
information about the spec; neither rejection rests on a tactic mismatch.

Neither witness binds anything (both state their refutation at literal inputs),
so neither has hypotheses that could be jointly inconsistent.

AXIOM lane: DROPPED. The nagini ``AXIOM_TESTS`` (the ``as_set`` A-reference
deep-model soundness/containment probes against real ``sympy.Contains``) belong
to G-AX, which the G-PBT spec lane ignores. This carrier declares NO ``opaque``
callee and consumes NO ``axiom … _prop`` (``correct_asSet`` closes by ``rfl``),
so there is no axiom-soundness obligation for this gate.
"""
from pathlib import Path

INSTANCE = "sympy__sympy-23950"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Region anchors. Each lies ENTIRELY inside the impl or proof region and is
# unique in the file, so every replacement preserves same_spec by construction.
# ---------------------------------------------------------------------------

# The impl-region body line (the whole conversion): inside -- impl-start/-- impl-end.
_IMPL = "  return some c.setArg"

# The WHOLE impl-region definition, for the cases that must change the def's
# binder shape (a `noncomputable` classical guard cannot be an `Id.run do` body).
# Still entirely inside -- impl-start / -- impl-end, so same_spec is preserved.
_IMPL_DEF = ("def implementation_asSet {E S : Type}\n"
             "    (c : MembershipAssertion E S) : Option S := Id.run do\n"
             "  return some c.setArg")

# The frozen proof body: inside -- proof-start/-- proof-end. The admissibility
# case prepends a `have` between `intro c` and the closing `rfl`.
_PROOF = "  intro c\n  rfl"

assert _BASE.count(_IMPL) == 1, "impl anchor drifted from Solution.lean"
assert _BASE.count(_IMPL_DEF) == 1, "impl-def anchor drifted from Solution.lean"
assert _BASE.count(_PROOF) == 1, "proof anchor drifted from Solution.lean"


# ---------------------------------------------------------------------------
# POSITIVE CONTROL (soundness) — a structurally different but CORRECT impl that
# MUST verify. If a faithful correct impl cannot satisfy the frozen obligation
# the spec is SPEC-TOO-STRONG. The `theorem correct_asSet` statement stays
# byte-identical and no helper lemma / axiom / assumption is introduced; the
# frozen `rfl` still closes because the local zeta-reduces to the frozen body.
# ---------------------------------------------------------------------------
_POS_LET = _swap(
    _BASE, _IMPL,
    "  let r := c.setArg\n"
    "  return some r",
)


# ---------------------------------------------------------------------------
# ADMISSIBILITY — the obligation is discharged at a ground, F2P-shaped input as a
# `have` prepended to the frozen tactic body, then the frozen obligation is
# closed verbatim. The frozen theorem has no precondition hypothesis (total
# behaviour), so this ground-instance form is the honest analogue of the nagini
# precondition-admission probe. Nothing is assumed: no new declaration, the
# statement is byte-identical, the ground instance is proved by reducing the impl
# and the spec.
# ---------------------------------------------------------------------------
_ADMISS = _swap(
    _BASE, _PROOF,
    "  have _ground : problem_spec_asSet\n"
    "      (E := Unit) (S := Nat) { element := (), setArg := 5 }\n"
    "      (implementation_asSet (E := Unit) (S := Nat) { element := (), setArg := 5 }) := by\n"
    "    unfold problem_spec_asSet implementation_asSet\n"
    "    rfl\n"
    "  intro c\n"
    "  rfl",
)


# ---------------------------------------------------------------------------
# UNIQUENESS / SPEC-TOO-WEAK rival — the only expressible wrong total function on
# this carrier: produce no value. Ships the FROZEN proof body verbatim (a `sorry`
# would violate variant scope), so its rejection is the frozen `rfl` failing
# against the reshaped impl — which is exactly why the WITNESS, not the
# rejection, attributes the failure to the spec.
# ---------------------------------------------------------------------------
_RIVAL_NONE = _swap(_BASE, _IMPL, "  return none")


# ---------------------------------------------------------------------------
# PARTIAL-DOMAIN rival (added by the audit). Declines exactly on the sub-domain
# where the two carrier types coincide, and returns the correct operand
# everywhere else. This is the case the "one expressible wrong function"
# parametricity argument had ruled out; it is well-typed and spec-sharing, so the
# argument was wrong. Wrong on a PROPER sub-domain, so it is the near-miss a
# single arbitrary probe point could miss: at `E := Unit, S := Nat` this rival
# agrees with gold exactly, and only a probe ON the diagonal refutes it.
# ---------------------------------------------------------------------------
_RIVAL_DIAGONAL = _swap(
    _BASE, _IMPL_DEF,
    "noncomputable def implementation_asSet {E S : Type}\n"
    "    (c : MembershipAssertion E S) : Option S :=\n"
    "  @ite _ (E = S) (Classical.propDecidable (E = S)) none (some c.setArg)",
)

# ---- witness (machine-checked: rival exit 0, frozen solution exit 1) --------
# Probes ON the diagonal (`E := Nat`, `S := Nat`), where the rival takes its
# declining branch: the guard is discharged by `simp`, the result reduces to
# `none`, and `none = some 0` is false. Against the frozen solution the same
# statement leaves `⊢ False` unsolved — a plain evaluation of the claim, not a
# missing name or a stuck reduction. Binds nothing, so no consistency probe is
# needed. Note this witness's probe point is a point at which the OTHER rival
# would NOT be refuted by the other witness's point, which is the whole reason
# both cases ship.
_WIT_DIAGONAL = (
    "example : ¬ problem_spec_asSet\n"
    "    (E := Nat) (S := Nat) { element := 0, setArg := 0 }\n"
    "    (implementation_asSet (E := Nat) (S := Nat) { element := 0, setArg := 0 }) := by\n"
    "  unfold problem_spec_asSet implementation_asSet\n"
    "  simp\n"
)


# ---------------------------------------------------------------------------
# POSITIVE CONTROL #2 (added by the audit) — a correct impl that is NOT
# definitionally equal to the frozen body, so the frozen `rfl` does not close it
# (measured) and it must be REPROVEN. The guard is always taken: the element
# operand itself witnesses that its carrier is nonempty. Reproving inside the
# proof region is admissible variant scope (the `correct_asSet` STATEMENT stays
# byte-identical; only the tactic body differs, which is what a variant that
# legitimately re-proves is allowed to do).
# ---------------------------------------------------------------------------
_POS_GUARD = _swap(
    _BASE, _IMPL_DEF,
    "noncomputable def implementation_asSet {E S : Type}\n"
    "    (c : MembershipAssertion E S) : Option S :=\n"
    "  @ite _ (Nonempty E) (Classical.propDecidable (Nonempty E))\n"
    "    (some c.setArg) none",
)
_POS_GUARD = _swap(
    _POS_GUARD, _PROOF,
    "  intro c\n"
    "  unfold problem_spec_asSet implementation_asSet\n"
    "  rw [if_pos ⟨c.element⟩]",
)


# ---- witness (machine-checked: elaborates vs rival, fails vs frozen) --------
# Instantiates the abstract carriers to concrete decidable types, reduces the
# rival's impl at a literal input to `none`, and shows `none ≠ some setArg` by
# `decide`. Binds nothing, so its hypotheses cannot be inconsistent.
_WIT_NONE = (
    "example : ¬ problem_spec_asSet\n"
    "    (E := Unit) (S := Nat) { element := (), setArg := 0 }\n"
    "    (implementation_asSet (E := Unit) (S := Nat) { element := (), setArg := 0 }) := by\n"
    "  unfold problem_spec_asSet implementation_asSet\n"
    "  decide\n"
)


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROL (soundness)
    # =====================================================================
    {
        "id": "pos-let-binding",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_LET,
        "rationale": "Structurally-different CORRECT impl: the set operand is "
                     "bound to a local before being wrapped in `some` and "
                     "returned (a data-flow reshape). The value returned is "
                     "unchanged, so the postcondition `result = some c.setArg` "
                     "still holds; must verify (else SPEC-TOO-STRONG — a faithful "
                     "correct impl rejected). The frozen `rfl` closes verbatim "
                     "(the local zeta-reduces to the frozen body).",
    },
    {
        "id": "pos-guarded-reshape",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_GUARD,
        "rationale": "The positive that actually probes SPEC-TOO-STRONG. A "
                     "CORRECT impl that is NOT definitionally equal to the frozen "
                     "body: it returns the set operand from behind a classically-"
                     "decided guard that is always taken (the element operand "
                     "witnesses its own carrier's nonemptiness), so the returned "
                     "value is `some c.setArg` at every input and the "
                     "postcondition holds. Measured: the frozen `rfl` FAILS on "
                     "this impl (`c is not definitionally equal to "
                     "implementation_asSet c`), so unlike the let-binding "
                     "positive — which zeta-reduces to the frozen body and is "
                     "closed by the frozen tactic unchanged — this one must be "
                     "REPROVEN (`rw [if_pos ⟨c.element⟩]`, then the frozen "
                     "obligation). Its verification is therefore evidence that "
                     "the spec admits a genuinely differently-shaped faithful "
                     "impl, not evidence that the kernel unfolded a synonym. The "
                     "`correct_asSet` statement stays byte-identical and no "
                     "axiom / `sorry` / helper theorem is introduced.",
    },
    # =====================================================================
    # ADMISSIBILITY
    # =====================================================================
    {
        "id": "admiss-ground-instance",
        "kind": "admissibility",
        "expect": "verify",
        "module": _ADMISS,
        "rationale": "The obligation is discharged at a ground F2P-shaped input "
                     "(a membership assertion over concrete carriers, one set "
                     "operand) as a `have` prepended to the frozen tactic body; "
                     "the frozen obligation is then closed verbatim. Verifies "
                     "(else the modeled behaviour would be unsatisfiable at the "
                     "shape the F2P exercises — the analogue of PRECOND-TOO-"
                     "STRONG). Nothing is assumed: no new declaration, the "
                     "`correct_asSet` statement is byte-identical, and the ground "
                     "instance is proved by reducing the impl and the spec.",
    },
    # =====================================================================
    # UNIQUENESS / REJECT rival
    # =====================================================================
    {
        "id": "rival-produces-no-value",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_NONE,
        "refinement": "This is the pre-patch behaviour: the conversion declines "
                      "to produce a value (`none` models raising / producing no "
                      "value — mapping.md). A faithful real patch that kept "
                      "declining to produce a set leaves the conversion returning "
                      "no set, so the F2P assertion (converting a membership "
                      "assertion yields exactly its set operand) FAILS — it raises "
                      "/ returns a non-set instead of the operand — so the "
                      "instance is NOT resolved. It is also the residue of the "
                      "wrong-component attack: returning the element operand is a "
                      "TYPE ERROR on this carrier (element and set operand have "
                      "distinct types), so the only expressible way to violate "
                      "the selection is to produce no value at all.",
        "rationale": "REJECT from the load-bearing clause `result = some "
                     "c.setArg`, on its DEFINEDNESS dimension: the spec demands "
                     "`some _`, but this rival returns `none`. Witness "
                     "instantiates the carriers to `Unit`/`Nat`, reduces the "
                     "rival's impl at a literal input to `none`, and derives "
                     "`none ≠ some setArg` by `decide`; it fails on gold, whose "
                     "result is `some c.setArg`. The rival ignores `c.setArg` "
                     "entirely, so one probed point refutes it over the whole "
                     "domain.",
        "witness": _WIT_NONE,
    },
    {
        "id": "rival-declines-on-diagonal",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_DIAGONAL,
        "refinement": "Its faithful real patch is the conversion returning the "
                      "stored set operand on most inputs but DECLINING on a "
                      "recognisable sub-family of them (a guard on the operands' "
                      "kinds that happens to hold for that family). The F2P "
                      "assertion pins the conversion on three different set "
                      "operands, so any patch that declines on a sub-family the "
                      "test exercises produces no set there and the assertion "
                      "FAILS on that line — the instance is NOT resolved even "
                      "though the other lines pass. A partial fix is still a "
                      "failing fix.",
        "rationale": "REJECT from the load-bearing clause `result = some "
                     "c.setArg` on a PROPER SUB-DOMAIN, which is what the "
                     "battery previously had no case for: the one-rival reading "
                     "of this carrier argued (wrongly) that `none` everywhere was "
                     "the only expressible wrong total function. This rival is "
                     "well-typed, shares the frozen spec, adds no axiom / "
                     "`sorry` / theorem, and is right wherever its guard is "
                     "false — including at the `Unit`/`Nat` point the other "
                     "witness probes, where it agrees with gold exactly. So its "
                     "witness must probe ON the diagonal (`Nat`/`Nat`), where the "
                     "impl reduces to `none` and `none = some 0` is false. "
                     "Machine-checked: witness elaborates against the rival, and "
                     "against the frozen solution the same statement fails with "
                     "`unsolved goals ⊢ False` — a plain evaluation of the claim.",
        "witness": _WIT_DIAGONAL,
    },
]
