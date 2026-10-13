"""properties.py — G-PBT falsification battery for matplotlib__matplotlib-25122 (lean).

NOT a Lean file; a record of adversarially-reasoned cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside an ``-- impl-start`` /
``-- impl-end`` region — and, for a case that legitimately re-proves, inside
``-- proof-start`` / ``-- proof-end`` — is changed, so ``markers.same_spec`` holds
by construction and the ``theorem correct_windowCorrectionFactor`` STATEMENT stays
byte-identical). ``expect="verify"`` passes iff (in scope AND the file elaborates
with the obligation closed); ``expect="reject"`` passes iff (in scope AND it does
NOT verify AND the case's refutation ``witness`` holds of the rival while FAILING
on the frozen solution).

This battery is a PORT of the nagini sibling (``../nagini/properties.py``). It
carries that battery's adversarial ARGUMENT across to this backend's carrier; it
is not a translation of the nagini text. Case-count parity is not the target —
see WHAT THIS CARRIER COLLAPSES below for every nagini case's disposition.

DEFENDED SURFACE (one total function, three input binders)
----------------------------------------------------------
A single modeled function computes the correction factor that compensates a
windowed spectrum for what the analysis window scaled away:

  windowCorrectionFactor (window : List Rat) (mode : Mode) (scaleByFreq : Bool) : Rat

``problem_spec_windowCorrectionFactor`` is one equation whose right-hand side is a
five-way dispatch on ``mode``, with the ``psd`` arm further split on
``scaleByFreq``. Read as independent top-level clauses of the postcondition, one
per reachable branch — each pins a DIFFERENT reduction over the same samples, so
each is separately attackable:

  (AMP-M)  mode = magnitude                 → result = window.sum
  (AMP-C)  mode = complex                   → result = window.sum
  (SQ)     mode = psd, scaleByFreq = true   → result = (window.map (·*·)).sum
  (SQSUM)  mode = psd, scaleByFreq = false  → result = window.sum * window.sum
  (NONE)   mode = angle / mode = phase      → result = 1

WHAT DRIVES THE REJECTS. The spec docstring names the discriminating quantity
itself: the signed total is the ARITHMETIC sum of the samples, never the sum of
their sizes, and the two agree exactly while every sample is nonnegative. The
samples may be negative (a window whose side lobes dip below zero), and the
failing scenario is built on precisely such a window — so the signed-vs-magnitude
reading of the linear total is the load-bearing distinction on (AMP-M), (AMP-C)
and (SQSUM). Three further families are attacked because a factor built from the
right samples by the WRONG reduction, or delivered on the wrong branch, is just
as wrong:

  * (AMP-M)/(AMP-C)/(SQSUM) vs the magnitude reading — ``abs-amp`` and
    ``abs-psd-power``. Refuted on a window carrying a negative sample, where the
    two totals part company; both agree with gold on every all-nonnegative
    window, so these are genuine partial-domain rivals, not blanket wrongness.
  * (AMP-M) vs an off-by-one traversal — ``skip-head-amp`` drops the leading
    sample. A NEAR-MISS of ``abs-amp``: it is correct on some negative-sample
    windows (any whose leading sample is zero) and wrong on some all-nonnegative
    ones, so it gets its own witness at an ALL-POSITIVE window, an input where
    ``abs-amp`` agrees with gold. Sharing a witness would have let this rival
    claim a sub-domain the manifest never demonstrated.
  * (SQ) vs (SQSUM) — the two power-style arms are different reductions of the
    same samples and the ``scaleByFreq`` binder is what selects between them.
    ``linear-psd-density`` gives the density arm the linear total instead of the
    squared-sample total; ``flag-ignored-psd`` ignores the flag and hands the
    squared-sample total to BOTH arms. The latter is refuted at an ALL-POSITIVE
    window, so it cannot be mistaken for a sign defect: it is purely a
    flag-dispatch defect.
  * (NONE) — ``phase-corrected`` applies a correction on a branch the spec pins
    to no correction at all; ``phase-only-corrected`` does the same to the OTHER
    constructor of that clause; ``complex-uncorrected`` does the converse,
    applying no correction on a branch that requires the signed total. Together
    these pin that the identity factor belongs to exactly the phase-style
    constructors and to no other.
  * THE EMPTY WINDOW — ``empty-amp-one`` agrees with gold on every NONEMPTY
    window and returns the identity factor on the empty one. Every other rival
    here is refuted at a two-sample window, so each of them leaves the ``[]``
    corner of the ``window`` binder unattacked; without this case a rival that
    special-cased the empty window would verify. It is the narrowest
    partial-domain rival in the battery: its disagreement set is a single input.

BINDER COVERAGE. The witnesses probe nine DISTINCT input points and move every
input binder. ``mode`` takes ALL FIVE of its constructors across the rivals
(``magnitude``, ``complex``, ``psd``, ``angle``, ``phase``): (NONE) is a
two-constructor clause and a rival can be wrong on either constructor alone, so
``angle`` and ``phase`` are each attacked by their own rival rather than one
standing in for the other. ``scaleByFreq`` takes both values with the ``psd``
constructor held fixed, so the flag is discriminated on its own rather than
incidentally. ``window`` takes a negative-sample window ``[3, -1]``, an
all-positive one ``[3, 1]``, and the empty one ``[]``, and the choice is
load-bearing in every direction: the sign rivals are refutable only on the first,
the traversal and flag-dispatch rivals only on the second, and the empty-window
rival only on the third.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen script is tuned to the frozen impl's
exact elaboration — so a rejection alone attributes nothing to the spec. Each
``expect="reject"`` case therefore carries a Lean snippet proving its rival
CONTRADICTS the spec at one concrete input. The carrier is fully transparent
(``Rat`` literals over a ``List``, a ``Bool``, a ``deriving DecidableEq``
inductive), so no term needs conditioning and NO witness binds a hypothesis —
there is no consistency obligation to discharge on any case here.

  Tactic note, measured on this workspace: ``decide`` does NOT close these goals.
  It reduces the ``Decidable`` instance rather than computing the value and gets
  stuck at ``(Rat.add 3 (-1)).num`` / ``(Rat.mul _ _).num``. That is a property of
  ``Rat``'s decidable equality, not a sign that the input is undecidable. The
  witnesses instead unfold the traversal for ``simp only`` (``List.forIn_cons`` /
  ``List.forIn_nil`` to run the loop, ``Id.run``/``bind``/``pure`` to escape the
  monad, ``List.map_cons``/``List.sum_cons`` to run the spec's fold, plus
  ``List.tail_cons`` for the one rival that traverses a tail) and finish the
  rational arithmetic with ``norm_num``.

Every witness was checked with the two real builds the gate runs: it ELABORATES
against its own rival and FAILS against the frozen solution. No witness reaches
for ``sorry``/``admit``/``native_decide``, and none is stated over a name only the
variant declares.

WHAT THIS CARRIER COLLAPSES vs the nagini sibling
-------------------------------------------------
The nagini bundle contracts TWO functions (a linear-total divisor and a
squared-total divisor) as imperative backward loops over a ``List[int]`` held at a
FRACTIONAL permission, under an explicit total-correctness obligation. This lean
bundle models the same computation as ONE total ``def`` whose branch is selected
by the two dispatch inputs. Dispositions, nagini case by nagini case:

  * ``pos-control-amp`` / ``pos-control-pwr`` (structurally different but CORRECT
    accumulations, one per divisor) ↦ ``pos-fold-form`` and ``pos-reorder-arms``.
    This carrier fuses both divisors into one function, so a single reshape
    exercises both: ``pos-fold-form`` replaces every accumulator loop with the
    equivalent point-free fold (a genuinely different executable shape — no
    ``Id.run``, no ``let mut``) and ``pos-reorder-arms`` permutes the dispatch so
    the phase-style branch is tried first. Both re-prove the byte-identical
    obligation: ``pos-fold-form`` with a per-constructor ``rfl``, and
    ``pos-reorder-arms`` with the frozen tactic body verbatim. No helper lemma
    added, no assumption token, no axiom.
  * ``admiss-amp`` (the precondition ADMITS a normal in-domain input) ↦
    ``admiss-ground-instance``. The frozen obligation carries NO precondition
    hypothesis — the modeled behavior is total on every window — so there is no
    precondition binder to probe here. The honest analogue confirms the obligation
    is SATISFIABLE, not merely provable in the abstract: a ``have`` inside the
    existing tactic body discharges the spec predicate at a ground scenario-shaped
    input (a negative-sample window on the squared-signed-total branch) by
    evaluation, and then the frozen obligation closes verbatim.
  * ``frame-mutation-amp`` / ``frame-mutation-pwr`` (MANDATORY there: write to an
    input held at a fractional permission, expecting an insufficient-permission
    rejection) — VACUOUS here, and no substitute is fabricated. Lean is
    referentially transparent: ``window`` is an immutable ``List Rat`` passed by
    value, the function returns a single ``Rat``, and there is no heap, no
    aliasing, no permission to under-hold and no caller-shared array a rival could
    corrupt. The whole class is an artifact of nagini's fractional-permission
    carrier.
  * ``weak-magnitude-amp`` (the magnitude reading of the linear total) ↦
    ``abs-amp``, and additionally ``abs-psd-power`` — the nagini carrier attaches
    the linear total to ONE function, whereas here the same total is load-bearing
    on two independent clauses ((AMP-M)/(AMP-C) and (SQSUM)), and a rival can be
    wrong on either alone. Both are ported rather than merged, since a rival
    wrong only on the squared arm agrees with gold on the amplitude arms.
  * ``weak-skip-first-amp`` (loop bound short by one, skipping the leading
    sample) ↦ ``skip-head-amp``, re-expressed as a traversal of the tail.
  * ``weak-linear-pwr`` (the linear total where the squared-sample total is
    required) ↦ ``linear-psd-density``.
  * ``vacuous-nonterm-amp`` (an impl that never returns, satisfying every value
    clause vacuously; on nagini this is caught by the total-correctness
    obligation) — VACUOUS here, but NOT for the reason a reader would guess, and
    the guess is measurably wrong: a syntactically diverging body CAN be written
    in the impl region, and it elaborates. Three builds, on this workspace:

      (a) An unbounded ``while true do`` prefix spliced above the frozen body
          elaborates fine, and a variant carrying it VERIFIES (the frozen
          obligation closes once the proof routes through a ``show`` of the
          frozen body). So "a diverging implementation cannot be written at all"
          is false as stated.
      (b) But that prefix is not divergence — it is ERASED. The spliced impl is
          DEFINITIONALLY EQUAL to the frozen one: ``example : implSpin =
          implementation_windowCorrectionFactor := by rfl`` elaborates (exit 0),
          while the same ``rfl`` against a genuinely different function fails
          with ``is not definitionally equal``, so the ``rfl`` is discriminating
          and not vacuous. ``#eval`` on the spliced impl RETURNS (``mkRat 2 1``
          for ``[3, -1]``): the loop has no observable effect, so the compiler
          drops it. The variant that verifies is therefore not a diverging rival
          — it is gold, spelled with dead code. It is caught by attack C, not by
          a termination obligation.
      (c) The same prefix combined with a WRONG value (``return 0`` on the
          amplitude arm) does NOT verify. So the value clauses still bite through
          the dead loop; nothing is satisfied vacuously.

    The only way to write a genuinely non-returning impl of this signature is
    self-recursion under ``partial``, which makes the constant OPAQUE: the frozen
    proof's own ``unfold implementation_windowCorrectionFactor`` then fails
    (``Tactic `unfold` failed to unfold``), so it cannot verify either. Hence the
    class is vacuous on this carrier because the carrier admits no impl that both
    diverges and satisfies the spec — not because divergence is unwritable.
    (This is the lean disposition specifically. It is NOT the velvet-partial
    disposition, where the same rival is a known spec hole — see
    ``the corpus-wide termination-semantics finding`` — because there the spec would SATISFY it.)
  * ``AXIOM_TESTS`` — dropped. The axiom lane is G-AX's job and this gate ignores
    it. The list is empty in the nagini sibling anyway, and this bundle declares
    no ``opaque``/``axiom`` pair at all (the reductions are modeled deeply over
    transparent data), so there is no ungrounded oracle for a rival to echo: the
    postcondition is pinned to folds over the actual input samples.

NO SOUNDNESS POSITIVE WAS DROPPED. Both reshapes above re-prove cleanly; nothing
was omitted because a proof would not close.

NEITHER POSITIVE IS TRIVIALLY THE FROZEN IMPL. A reshape that is DEFINITIONALLY
equal to the frozen ``def`` would verify while testing nothing, so both were
measured rather than assumed: ``example : <reshape> =
implementation_windowCorrectionFactor := by rfl`` FAILS for each of them, with
``is not definitionally equal to``, so each really does present the elaborator a
different term and its ``verify`` is earned. (The same ``rfl`` DOES close against
a variant whose only change is dead code, which is what makes the failure here
informative rather than a limitation of ``rfl`` — see the divergence disposition
below.)

NEW ON THIS CARRIER (no nagini counterpart, and not parity-chasing). The nagini
sibling has no ``mode``/``scaleByFreq`` binder — it splits the two reductions
across two separately-contracted functions, so the DISPATCH itself is not part of
its defended surface. Here the dispatch is inside the modeled function and is
exactly the kind of independent binder a narrowed port must attack, so
``phase-corrected``, ``complex-uncorrected`` and ``flag-ignored-psd`` are added to
cover (NONE), the ``complex`` arm of the amplitude clause, and the
``scaleByFreq`` split. Without them, a rival that mishandled only the branch
selection would verify and the battery would never notice.
"""
from pathlib import Path

INSTANCE = "matplotlib__matplotlib-25122"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Region anchors. Each lies ENTIRELY inside the region it names and is unique in
# Solution.lean (both asserted by _swap at import, so the manifest breaks loudly
# if the frozen solution ever drifts).
# ---------------------------------------------------------------------------

# --- impl region: one anchor per dispatch arm -------------------------------

_ARM_AMP = (
    "  | Mode.magnitude | Mode.complex =>\n"
    "      -- amplitude-style: divide by the signed total of the window samples\n"
    "      let mut s : Rat := 0\n"
    "      for w in window do\n"
    "        s := s + w\n"
    "      return s\n"
)

_ARM_SQ = (
    "        -- density per unit frequency: divide by the total of the squared samples\n"
    "        let mut sq : Rat := 0\n"
    "        for w in window do\n"
    "          sq := sq + w * w\n"
    "        return sq\n"
)

_ARM_SQSUM = (
    "        -- power preserved per segment: divide by the square of the signed total\n"
    "        let mut s : Rat := 0\n"
    "        for w in window do\n"
    "          s := s + w\n"
    "        return s * s\n"
)

_ARM_NONE = (
    "  | Mode.angle | Mode.phase =>\n"
    "      -- phase-style: no window correction\n"
    "      return 1\n"
)

# The whole impl body (for the point-free positive). Unique; inside impl-start /
# impl-end.
_IMPL_ALL = (
    "def implementation_windowCorrectionFactor\n"
    "    (window : List Rat) (mode : Mode) (scaleByFreq : Bool) : Rat := Id.run do\n"
    "  match mode with\n"
    + _ARM_AMP
    + "  | Mode.psd =>\n"
    "      if scaleByFreq then\n"
    + _ARM_SQ
    + "      else\n"
    + _ARM_SQSUM
    + _ARM_NONE
)

# --- proof region ------------------------------------------------------------

# The frozen obligation STATEMENT. Reproduced byte-identically in every
# replacement below; only the tactic body ever changes.
_OBLIGATION = (
    "theorem correct_windowCorrectionFactor :\n"
    "    ∀ (window : List Rat) (mode : Mode) (scaleByFreq : Bool),\n"
    "      problem_spec_windowCorrectionFactor window mode scaleByFreq\n"
    "        (implementation_windowCorrectionFactor window mode scaleByFreq) := by\n"
)

# The head of the frozen tactic body — the insertion point for the admissibility
# ground instance. Unique in the file.
_PROOF_HEAD = (
    "  intro window mode scaleByFreq\n"
    "  unfold problem_spec_windowCorrectionFactor implementation_windowCorrectionFactor\n"
)

# The frozen tactic body in FULL (statement + every arm), for the positive whose
# reshaped impl needs a genuinely new proof: the frozen arms rewrite with the loop
# lemmas, which no longer apply once the loops are gone, so the whole body is
# replaced rather than only its head.
_PROOF_ALL = (
    _OBLIGATION
    + _PROOF_HEAD
    + "  cases mode with\n"
      "  | magnitude =>\n"
      "      simp only [Id.run]\n"
      "      have h := sum_loop_windowCorrectionFactor window 0\n"
      "      simp only [Id.run] at h\n"
      "      rw [h]; simp\n"
      "  | complex =>\n"
      "      simp only [Id.run]\n"
      "      have h := sum_loop_windowCorrectionFactor window 0\n"
      "      simp only [Id.run] at h\n"
      "      rw [h]; simp\n"
      "  | psd =>\n"
      "      by_cases hs : scaleByFreq\n"
      "      · subst hs\n"
      "        simp only [Id.run, if_true]\n"
      "        have h := sumsq_loop_windowCorrectionFactor window 0\n"
      "        simp only [Id.run] at h\n"
      "        rw [h]; simp\n"
      "      · simp only [hs, Bool.false_eq_true, if_false, Id.run]\n"
      "        have h := sum_loop_windowCorrectionFactor window 0\n"
      "        simp only [Id.run] at h\n"
      "        rw [h]; simp only [zero_add]; rfl\n"
      "  | angle => rfl\n"
      "  | phase => rfl\n"
)


# ---------------------------------------------------------------------------
# Witness helper.
#
# A reject witness states the spec predicate directly at ONE concrete, fully
# transparent input and refutes it. No hypothesis is bound, so no witness here
# carries a consistency obligation.
#
# `decide` is deliberately NOT used: measured on this workspace it reduces the
# `Decidable` instance instead of computing the value and gets stuck at
# `(Rat.add 3 (-1)).num`. The traversal is therefore unfolded for `simp only`
# (`List.forIn_*` runs the loop, `Id.run`/`bind`/`pure` escape the monad,
# `List.map_cons`/`List.sum_*` run the spec's fold, `List.tail_cons` handles the
# one rival that traverses a tail) and the rational arithmetic is closed by
# `norm_num`.
# ---------------------------------------------------------------------------

_WIT_TACTIC = (
    "  simp only [List.forIn_cons, List.forIn_nil, Id.run, bind, pure,\n"
    "    List.map_cons, List.map_nil, List.sum_cons, List.sum_nil, List.tail_cons]\n"
    "  norm_num\n"
)


def _wit(window, mode, scale_by_freq):
    """`¬ spec w m s (impl w m s)` at one concrete point."""
    return (
        f"example : ¬ problem_spec_windowCorrectionFactor {window} {mode} "
        f"{scale_by_freq}\n"
        f"    (implementation_windowCorrectionFactor {window} {mode} "
        f"{scale_by_freq}) := by\n"
        f"  unfold problem_spec_windowCorrectionFactor "
        f"implementation_windowCorrectionFactor\n"
        + _WIT_TACTIC
    )


SPEC_TESTS = [
    # =======================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify, else the spec is over-fit to the frozen spelling
    # (SPEC-TOO-STRONG). Each keeps the `theorem correct_windowCorrectionFactor`
    # STATEMENT byte-identical, adds no helper lemma, no axiom and no assumption
    # token, and re-proves the obligation honestly.
    # =======================================================================
    {
        "id": "pos-fold-form",
        "kind": "soundness",
        "expect": "verify",
        # Every accumulator loop replaced by the equivalent point-free fold over
        # the same samples: a genuinely different executable shape (no `Id.run`,
        # no `let mut`, no `for`) computing the same factor on every input. The
        # frozen tactic body no longer applies (it rewrites with the loop lemmas),
        # so the obligation is re-proven from scratch — each dispatch arm closes
        # by `rfl` because impl and spec now reduce to the same fold.
        "module": _swap(
            _swap(
                _BASE, _IMPL_ALL,
                "def implementation_windowCorrectionFactor\n"
                "    (window : List Rat) (mode : Mode) (scaleByFreq : Bool) : Rat :=\n"
                "  match mode with\n"
                "  | Mode.magnitude | Mode.complex =>\n"
                "      -- amplitude-style: divide by the signed total of the window samples\n"
                "      window.sum\n"
                "  | Mode.psd =>\n"
                "      if scaleByFreq then\n"
                "        -- density per unit frequency: divide by the total of the squared samples\n"
                "        (window.map (fun w => w * w)).sum\n"
                "      else\n"
                "        -- power preserved per segment: divide by the square of the signed total\n"
                "        window.sum * window.sum\n"
                "  | Mode.angle | Mode.phase =>\n"
                "      -- phase-style: no window correction\n"
                "      1\n",
            ),
            _PROOF_ALL,
            _OBLIGATION
            + _PROOF_HEAD
            + "  cases mode with\n"
              "  | magnitude => rfl\n"
              "  | complex => rfl\n"
              "  | psd => rfl\n"
              "  | angle => rfl\n"
              "  | phase => rfl\n"
              "-- The frozen loop lemmas above are unused by this shape (the folds are\n"
              "-- already in the spec's form). They are left DECLARED and unchanged, so\n"
              "-- the variant adds no lemma and removes none.\n",
        ),
        "rationale": "a CORRECT point-free reshape — every accumulator loop written "
                     "as the equivalent fold over the same samples — must satisfy "
                     "every clause (AMP-M), (AMP-C), (SQ), (SQSUM) and (NONE) at once, "
                     "since it agrees with the frozen impl at every input. If it "
                     "cannot verify, the spec is over-fit to the imperative spelling "
                     "of the reductions rather than to the values they produce => "
                     "SPEC-TOO-STRONG. Re-proven honestly: the obligation statement is "
                     "byte-identical and each dispatch arm closes by `rfl` (impl and "
                     "spec reduce to the same fold); no lemma added, nothing assumed.",
    },
    {
        "id": "pos-reorder-arms",
        "kind": "soundness",
        "expect": "verify",
        # The dispatch permuted so the no-correction arm is tried FIRST and the
        # amplitude arm last. Same factor on every input; a different control-flow
        # shape. The frozen tactic body closes it verbatim (it case-splits on
        # `mode`, and each arm's loop is unchanged), so this positive isolates
        # branch ORDER from branch CONTENT.
        "module": _swap(
            _BASE, _IMPL_ALL,
            "def implementation_windowCorrectionFactor\n"
            "    (window : List Rat) (mode : Mode) (scaleByFreq : Bool) : Rat := Id.run do\n"
            "  match mode with\n"
            + _ARM_NONE
            + "  | Mode.psd =>\n"
            "      if scaleByFreq then\n"
            + _ARM_SQ
            + "      else\n"
            + _ARM_SQSUM
            + _ARM_AMP,
        ),
        "rationale": "a CORRECT reshape that permutes the dispatch (no-correction arm "
                     "first, amplitude arm last) while leaving every arm's reduction "
                     "untouched. It agrees with the frozen impl at every input, so it "
                     "must verify; if branch ORDER mattered to the spec the spec would "
                     "be pinning the impl's syntax rather than the input→factor "
                     "relation => SPEC-TOO-STRONG. The frozen tactic body closes it "
                     "verbatim (the `cases mode` split reaches the same arms).",
    },

    # =======================================================================
    # ADMISSIBILITY — the obligation is SATISFIABLE at a normal, scenario-shaped
    # input, not merely provable in the abstract. The frozen obligation carries
    # no precondition hypothesis (the behavior is total on every window), so the
    # nagini precondition-admission probe has no binder to attack; the honest
    # analogue discharges the spec predicate at a ground input by evaluation
    # inside the existing tactic body, then closes the frozen obligation
    # verbatim. Nothing is added or assumed: no new declaration, no axiom, no
    # assumption token, and the theorem statement is byte-identical.
    # =======================================================================
    {
        "id": "admiss-ground-instance",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _PROOF_HEAD,
            "  have _ground : problem_spec_windowCorrectionFactor [3, -1] "
            "Mode.psd false\n"
            "      (implementation_windowCorrectionFactor [3, -1] Mode.psd false) := by\n"
            "    unfold problem_spec_windowCorrectionFactor "
            "implementation_windowCorrectionFactor\n"
            "    simp only [List.forIn_cons, List.forIn_nil, Id.run, bind, pure,\n"
            "      List.map_cons, List.map_nil, List.sum_cons, List.sum_nil]\n"
            "    norm_num\n"
            + _PROOF_HEAD,
        ),
        "rationale": "the (SQSUM) clause is discharged BY EVALUATION at a ground, "
                     "scenario-shaped input — a window carrying a negative sample, on "
                     "the squared-signed-total branch, exactly the configuration where "
                     "the signed and magnitude readings part company — and then the "
                     "frozen obligation closes verbatim. This must verify: if the spec "
                     "predicate could not be discharged at that concrete point the "
                     "modeled behavior would be unsatisfiable at the very input shape "
                     "the failing scenario exercises (the analogue of "
                     "PRECOND-TOO-STRONG on a carrier with no precondition binder).",
    },

    # =======================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — WRONG impls sharing the frozen spec
    # that MUST be rejected. Each carries (a) the refinement argument that its
    # faithful real patch would NOT resolve, so a verifying rival is a true
    # verify-does-not-imply-resolve break rather than an artifact, and (b) a
    # refutation witness, checked with two real builds, that holds of the rival
    # and FAILS on the frozen solution.
    # =======================================================================
    {
        "id": "abs-amp",
        "kind": "uniqueness",
        "expect": "reject",
        # The amplitude arm totals the sample SIZES instead of the samples.
        "module": _swap(
            _BASE, _ARM_AMP,
            "  | Mode.magnitude | Mode.complex =>\n"
            "      -- amplitude-style: divide by the signed total of the window samples\n"
            "      let mut s : Rat := 0\n"
            "      for w in window do\n"
            "        s := s + (if w < 0 then -w else w)\n"
            "      return s\n",
        ),
        "refinement": "this is the defective reading the change repairs. A faithful "
                      "real patch that kept the amplitude-style factor as the total of "
                      "the sample SIZES leaves the amplitude and complex spectra "
                      "mis-normalized on exactly the windows the failing scenario "
                      "uses — one whose side lobes dip below zero, where the two "
                      "totals differ — so the scenario's normalization identity still "
                      "does not hold and the instance is NOT resolved. Note it agrees "
                      "with the fixed behavior on every all-nonnegative window, which "
                      "is why the historically-passing scenarios never caught it: a "
                      "rival that verified here would be a genuine "
                      "verify-does-not-imply-resolve break.",
        "rationale": "REJECT from (AMP-M)/(AMP-C) (result = window.sum): on a window "
                      "carrying a negative sample the rival returns the total of the "
                      "sample sizes while the spec requires the arithmetic total. "
                      "Partial-domain — the two coincide on every all-nonnegative "
                      "window, so the `window` binder is what discriminates. If it "
                      "verified => SPEC-TOO-WEAK (the spec would not be pinning the "
                      "sign handling its own statement calls load-bearing).",
        "witness": _wit("[3, -1]", "Mode.magnitude", "true"),
    },
    {
        "id": "abs-psd-power",
        "kind": "uniqueness",
        "expect": "reject",
        # The same magnitude reading, on the OTHER clause that consumes the
        # signed total: the power-preserving arm squares it.
        "module": _swap(
            _BASE, _ARM_SQSUM,
            "        -- power preserved per segment: divide by the square of the signed total\n"
            "        let mut s : Rat := 0\n"
            "        for w in window do\n"
            "          s := s + (if w < 0 then -w else w)\n"
            "        return s * s\n",
        ),
        "refinement": "the signed total is load-bearing on TWO independent clauses, "
                      "and a real patch can repair one and miss the other. A patch "
                      "that fixed the amplitude-style factor but left the "
                      "power-preserving factor as the SQUARE of the magnitude total "
                      "still fails the failing scenario, which is stated on the "
                      "power-style branch: it compares the power-preserved and "
                      "density spectra of the same negative-sample window, and that "
                      "identity holds only once the squared factor is built from the "
                      "arithmetic total. NOT resolved. Independent of `abs-amp`: this "
                      "rival agrees with the fixed behavior on the amplitude arms.",
        "rationale": "REJECT from (SQSUM) (result = window.sum * window.sum): on a "
                      "negative-sample window the rival returns the square of the "
                      "magnitude total. Attacks a DIFFERENT top-level clause from "
                      "`abs-amp` and probes a different (mode, scaleByFreq) point, so "
                      "the two are not the same rival — each is refuted at the input "
                      "its own clause is reached by. If it verified => SPEC-TOO-WEAK.",
        "witness": _wit("[3, -1]", "Mode.psd", "false"),
    },
    {
        "id": "linear-psd-density",
        "kind": "uniqueness",
        "expect": "reject",
        # The density arm totals the samples instead of their squares.
        "module": _swap(
            _BASE, _ARM_SQ,
            "        -- density per unit frequency: divide by the total of the squared samples\n"
            "        let mut sq : Rat := 0\n"
            "        for w in window do\n"
            "          sq := sq + w\n"
            "        return sq\n",
        ),
        "refinement": "a real patch that normalized the per-unit-frequency density by "
                      "the linear total of the samples rather than the total of their "
                      "squares is the wrong physical normalization: the two reductions "
                      "coincide only on trivial windows. The failing scenario asserts "
                      "an identity BETWEEN the power-preserved and density spectra, "
                      "each divided by its own factor, so getting the density factor "
                      "wrong breaks it just as surely as getting the other one wrong — "
                      "and every historically-passing density comparison would break "
                      "too. NOT resolved.",
        "rationale": "REJECT from (SQ) (result = (window.map (·*·)).sum): the rival "
                      "delivers the linear total where the spec requires the "
                      "squared-sample total. These are different reductions of the "
                      "same samples, so this rival is orthogonal to the sign family: "
                      "it is wrong on nearly every window, negative samples or not. If "
                      "it verified => SPEC-TOO-WEAK (the two power-style reductions "
                      "would be interchangeable under the spec).",
        "witness": _wit("[3, -1]", "Mode.psd", "true"),
    },
    {
        "id": "skip-head-amp",
        "kind": "uniqueness",
        "expect": "reject",
        # Off-by-one traversal: the leading sample is never accumulated.
        "module": _swap(
            _BASE, _ARM_AMP,
            "  | Mode.magnitude | Mode.complex =>\n"
            "      -- amplitude-style: divide by the signed total of the window samples\n"
            "      let mut s : Rat := 0\n"
            "      for w in window.tail do\n"
            "        s := s + w\n"
            "      return s\n",
        ),
        "refinement": "a real patch whose traversal dropped the leading sample would "
                      "build the amplitude-style factor from all-but-the-first sample. "
                      "The analysis windows in play have a large nonzero leading "
                      "sample, so the factor is simply the wrong number and the "
                      "amplitude/complex normalization is off by a constant on EVERY "
                      "window — the failing scenario does not resolve, and the "
                      "historically-passing amplitude comparisons regress as well.",
        "rationale": "REJECT from (AMP-M) (result = window.sum): the rival returns the "
                      "total of the tail, short by the leading sample, so it violates "
                      "the clause on every window whose leading sample is nonzero. "
                      "Deliberately given its OWN witness at an ALL-POSITIVE window "
                      "rather than sharing `abs-amp`'s: the two rivals fail on "
                      "different sub-domains (this one is correct on any window whose "
                      "leading sample is zero — including negative-sample ones — and "
                      "wrong on all-nonnegative ones, where `abs-amp` agrees with "
                      "gold). Sharing a witness would let this rival claim a "
                      "sub-domain the manifest never demonstrated. If it verified => "
                      "SPEC-TOO-WEAK (the spec would not pin WHICH samples the total "
                      "ranges over).",
        "witness": _wit("[3, 1]", "Mode.magnitude", "true"),
    },
    {
        "id": "flag-ignored-psd",
        "kind": "uniqueness",
        "expect": "reject",
        # The density flag is ignored: the squared-sample total is delivered on
        # BOTH power-style arms.
        "module": _swap(
            _BASE, _ARM_SQSUM,
            "        -- power preserved per segment: divide by the square of the signed total\n"
            "        let mut sq : Rat := 0\n"
            "        for w in window do\n"
            "          sq := sq + w * w\n"
            "        return sq\n",
        ),
        "refinement": "a real patch that collapsed the two power-style branches — "
                      "normalizing by the total of the squared samples whether or not "
                      "the spectrum is expressed per unit frequency — destroys exactly "
                      "the relationship the failing scenario asserts: that scenario "
                      "computes the SAME signal both ways and checks the two spectra "
                      "against each other through their two DIFFERENT factors. Make "
                      "the factors identical and the asserted identity becomes a "
                      "different (false) claim. NOT resolved, and every "
                      "historically-passing density-vs-power comparison breaks too.",
        "rationale": "REJECT from (SQSUM) (scaleByFreq = false → result = window.sum * "
                      "window.sum): the rival ignores the flag and returns the "
                      "squared-sample total on both arms. Refuted at an ALL-POSITIVE "
                      "window on purpose, so the refutation cannot be confused with a "
                      "sign defect — it is purely a flag-dispatch defect. Paired with "
                      "`linear-psd-density` (same `mode`, the OTHER value of "
                      "`scaleByFreq`), this discriminates the `scaleByFreq` binder in "
                      "both directions; a battery that only ever probed one value of "
                      "the flag would admit a rival that ignored it entirely. If it "
                      "verified => SPEC-TOO-WEAK.",
        "witness": _wit("[3, 1]", "Mode.psd", "false"),
    },
    {
        "id": "phase-corrected",
        "kind": "uniqueness",
        "expect": "reject",
        # A correction is applied on a branch the spec pins to none.
        "module": _swap(
            _BASE, _ARM_NONE,
            "  | Mode.angle =>\n"
            "      -- phase-style: no window correction\n"
            "      let mut s : Rat := 0\n"
            "      for w in window do\n"
            "        s := s + w\n"
            "      return s\n"
            "  | Mode.phase =>\n"
            "      -- phase-style: no window correction\n"
            "      return 1\n",
        ),
        "refinement": "a real patch that applied a window correction to a phase-style "
                      "spectrum would scale an ANGLE by the window total. Angles are "
                      "already scale-free — that is why the correct behavior applies no "
                      "correction there — so the phase-style outputs would come back "
                      "divided by an arbitrary factor and the many "
                      "historically-passing angle/phase comparisons would fail "
                      "outright. NOT resolved.",
        "rationale": "REJECT from (NONE) (mode = angle → result = 1): the rival returns "
                      "the signed total on a branch the spec pins to the identity "
                      "factor. Attacks the only clause that does NOT depend on the "
                      "window samples — without it a rival that mishandled only "
                      "the no-correction branch would verify. Refuted at the `angle` "
                      "constructor specifically; `phase-only-corrected` does the same "
                      "to `phase`, because (NONE) has TWO constructors and this rival "
                      "leaves `phase` correct. If it verified => SPEC-TOO-WEAK (the "
                      "spec would not pin which constructors get no correction).",
        "witness": _wit("[3, -1]", "Mode.angle", "true"),
    },
    {
        "id": "phase-only-corrected",
        "kind": "uniqueness",
        "expect": "reject",
        # The (NONE) clause has TWO constructors and `phase-corrected` attacks only
        # the first. This rival is its mirror: `angle` is left correct and the
        # correction is applied on `phase` alone.
        "module": _swap(
            _BASE, _ARM_NONE,
            "  | Mode.angle =>\n"
            "      -- phase-style: no window correction\n"
            "      return 1\n"
            "  | Mode.phase =>\n"
            "      -- phase-style: no window correction\n"
            "      let mut s : Rat := 0\n"
            "      for w in window do\n"
            "        s := s + w\n"
            "      return s\n",
        ),
        "refinement": "a real patch can repair one phase-style constructor and miss the "
                      "other: the two are separate branches of the dispatch even though "
                      "the spec assigns them the same factor. A patch that stopped "
                      "correcting angle spectra but kept scaling the phase spectrum by "
                      "the window total leaves that output divided by an arbitrary "
                      "factor, and phase is scale-free for the same reason angle is, so "
                      "the historically-passing phase comparisons still fail. NOT "
                      "resolved, and independent of `phase-corrected`: this rival agrees "
                      "with the fixed behavior at `angle`.",
        "rationale": "REJECT from (NONE) (mode = phase → result = 1). Deliberately given "
                      "its OWN witness at the `phase` constructor rather than sharing "
                      "`phase-corrected`'s at `angle`: the two rivals disagree with gold "
                      "on DISJOINT sub-domains (each is correct at the constructor the "
                      "other breaks), so one witness cannot refute both and sharing it "
                      "would let this rival claim a sub-domain the manifest never "
                      "demonstrates. Together they take `mode` to all five constructors. "
                      "If it verified => SPEC-TOO-WEAK (the spec would pin the identity "
                      "factor to only ONE of the two phase-style constructors).",
        "witness": _wit("[3, -1]", "Mode.phase", "true"),
    },
    {
        "id": "complex-uncorrected",
        "kind": "uniqueness",
        "expect": "reject",
        # The converse: no correction on a branch that requires the signed total.
        "module": _swap(
            _BASE, _ARM_AMP,
            "  | Mode.magnitude =>\n"
            "      -- amplitude-style: divide by the signed total of the window samples\n"
            "      let mut s : Rat := 0\n"
            "      for w in window do\n"
            "        s := s + w\n"
            "      return s\n"
            "  | Mode.complex =>\n"
            "      -- amplitude-style: divide by the signed total of the window samples\n"
            "      return 1\n",
        ),
        "refinement": "a real patch that dropped the window correction from the "
                      "complex-spectrum branch while keeping it on the magnitude "
                      "branch would leave complex spectra unnormalized: the two are "
                      "required to agree up to taking sizes, and the "
                      "historically-passing equivalence comparisons between them "
                      "compare exactly that. So the complex outputs would be wrong by "
                      "the window factor on every window, and the instance does NOT "
                      "resolve.",
        "rationale": "REJECT from (AMP-C) (mode = complex → result = window.sum): the "
                      "rival returns the identity factor where the signed total is "
                      "required — the exact converse of `phase-corrected`. Pins the "
                      "boundary between the two constant/non-constant clause families "
                      "from the other side, and probes the `complex` constructor that "
                      "`abs-amp` (which shares that arm in the frozen impl) does not "
                      "reach at its own witness point. If it verified => "
                      "SPEC-TOO-WEAK.",
        "witness": _wit("[3, -1]", "Mode.complex", "true"),
    },
    {
        "id": "empty-amp-one",
        "kind": "uniqueness",
        "expect": "reject",
        # The narrowest partial-domain rival here: correct on every NONEMPTY
        # window, wrong only at `[]`. Every other rival is refuted at a
        # two-sample window, so the empty corner of the `window` binder was
        # otherwise unprobed.
        "module": _swap(
            _BASE, _ARM_AMP,
            "  | Mode.magnitude | Mode.complex =>\n"
            "      -- amplitude-style: divide by the signed total of the window samples\n"
            "      if window.isEmpty then\n"
            "        return 1\n"
            "      else\n"
            "        let mut s : Rat := 0\n"
            "        for w in window do\n"
            "          s := s + w\n"
            "        return s\n",
        ),
        "refinement": "a real patch that guarded the amplitude-style factor against a "
                      "zero divisor — substituting the identity factor when the window "
                      "carries no samples — is the plausible defensive version of this "
                      "computation, and it is still wrong: the spec pins the factor to "
                      "the signed total, which is 0 on the empty window, not 1. A caller "
                      "that receives 1 where the modeled behavior says 0 gets a silently "
                      "unnormalized spectrum instead of a detectable degenerate case. It "
                      "agrees with the fixed behavior on every window that has samples, "
                      "so no scenario built on a real analysis window would notice — "
                      "which is exactly why a battery whose every witness sits at a "
                      "two-sample window cannot see it, and why a rival that verified "
                      "here would be a genuine verify-does-not-imply-resolve break.",
        "rationale": "REJECT from (AMP-M)/(AMP-C) (result = window.sum): at `[]` the "
                      "spec requires `List.sum [] = 0` and the rival returns 1. Its "
                      "disagreement set is a SINGLE input, so it needs its own witness "
                      "at `[]` — no other case's witness reaches it, and the empty list "
                      "is a distinct point of the `window` binder rather than a second "
                      "spelling of an existing one (the fold's base case is what is "
                      "under test, not its step). If it verified => SPEC-TOO-WEAK (the "
                      "spec would not pin the total at the empty window, leaving the "
                      "base case of the reduction unconstrained).",
        "witness": _wit("[]", "Mode.magnitude", "true"),
    },
]

# The nagini AXIOM_TESTS lane is empty in the sibling and is G-AX's job in any
# case; this gate ignores it. This bundle declares no `opaque`/`axiom` callee
# pair at all — the reductions are modeled deeply over transparent data — so
# there is no ungrounded oracle a rival could echo.
AXIOM_TESTS = []
