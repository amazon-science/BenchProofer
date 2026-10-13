"""properties.py — G-PBT falsification battery for scikit-learn__scikit-learn-15100 (lean).

NOT a Lean file; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region — and, for a case that legitimately re-proves, inside the
``-- proof-start`` / ``-- proof-end`` region — is changed, so
``markers.same_spec`` holds and the single ``theorem correct_stripAccents``
STATEMENT stays byte-identical). ``expect:"verify"`` passes iff (in scope AND the
file elaborates with the obligation closed); ``expect:"reject"`` passes iff (in
scope AND it does NOT verify AND the case's refutation ``witness`` HOLDS of the
rival while FAILING on the frozen solution).

PORT NOTE. This is a PORT of the nagini falsification battery
(``../nagini/properties.py``) onto this backend's carrier. The two batteries
look different because the carriers do. The nagini bundle models the transform
imperatively over a permissioned ``List[int]`` (``strip_marks``): the input
carries only ``Acc(list_pred(s), 1/2)`` (read-only), the ASCII fast path is a
proven copy loop, and the general path is a backward fold with framing
Invariants/Asserts. Its defended surface is one LOAD-BEARING postcondition
``ToSeq(Result()) == strip_combining(nfkd(ToSeq(s)))`` plus the read-only frame
permission on ``s``.

This Lean bundle models the same single behavior purely functionally. A string
is ``List Char``; the decomposition and the combining-mark predicate are the two
UNCHANGED standard-library callees, entering the impl as ``opaque canonDecompose``
and ``opaque isCombiningMark`` (A-references, validated executably against the
real routines by the conformance gate — the proof consumes no property of
either). The whole observable behavior is ONE ``theorem correct_stripAccents``
over ONE binder ``s : List Char``, whose postcondition is a two-armed
if-then-else:

    if s.all isAscii then result = s
    else result = (canonDecompose s).filter (fun c => !isCombiningMark c)

DEFENDED SURFACE (one modeled behavior, one binder, two independent arms).

  * ASCII arm: an all-ASCII input is returned verbatim (the accent-free fast
    path). This is the analogue of the nagini fast-path copy loop.
  * non-ASCII arm: a string carrying any non-ASCII code point is canonically
    decomposed and every combining mark dropped — the LOAD-BEARING equality that
    nagini pins with ``strip_combining(nfkd(s))``. This arm is where the reported
    bug lives: an ALREADY-DECOMPOSED accented input (base + separate combining
    mark) is non-ASCII, so it must fall through to the decompose-and-drop path
    rather than being returned untouched.

ADVERSARIAL READ of the nagini case classes on this carrier:

  * FRAME / PERMISSION MUTATION (nagini frame-mut-store, frame-mut-append) —
    VACUOUS here, and DEMONSTRATED rather than asserted. Lean is referentially
    transparent: ``s : List Char`` carries no heap permission, there is no
    read-only half-permission to overwrite and no aliasing to exploit. The audit
    built the closest analogue of each nagini rival — take a ``let mut`` copy of
    the argument, write into it (``t.set``) or extend it (``t ++ [_]``), then run
    the gold body — and the append form VERIFIES (exit 0): the "mutation" is dead
    code the spec cannot observe, because nothing the impl does to a local can
    reach the caller's value. That is what makes these cases vacuous on this
    carrier rather than merely hard: there is no observable difference for a
    witness to discriminate. No substitute is fabricated.

  * DIVERGENCE / NON-TERMINATION — nothing to ship, but NOT for the reason "a
    diverging impl cannot be written". It can: ``partial def`` is accepted by the
    elaborator and is not barred by ``variant_scope``. The audit built two
    (``partial def`` self-call; a ``partial`` helper the impl returns), and both
    are REJECTED (exit 1) — vanilla Lean 4 has no partial-correctness escape
    hatch, so a non-terminating impl gets no free pass on the obligation. The
    divergence hole that DOES exist on the velvet carrier under
    ``loom.semantics.termination "partial"`` is a known, separately-escalated
    finding (``the corpus-wide termination-semantics finding``, scoped to velvet: lean and nagini
    unaffected); it is not re-reported here and this lane stays empty.
    RE-DERIVED by the independent audit, because "rejected" is not by itself a
    reason to ship nothing — a rejected rival is shippable if a WITNESS can
    refute it, and this one cannot. The frozen file sets no
    ``loom.semantics.termination`` option at all (that option is velvet's; this
    is vanilla Lean 4), so the disposition is neither of the two the audit rubric
    names. Measured: a ``partial def`` gets NO equation lemma, so ``unfold``
    fails (``failed to unfold implementation_stripAccents``), ``rw
    [implementation_stripAccents]`` reports ``Expected an equality or iff
    proof``, and ``simp [implementation_stripAccents]`` leaves the goal untouched
    — the impl's applied term is IRREDUCIBLE, so no witness can state what the
    rival returns. The one witness shape that does elaborate against it conditions
    on ``implementation_stripAccents [U+00F1] ≠ …``, i.e. it assumes the
    refutation; it builds against GOLD too (exit 0, so ``witness-vacuous`` — it
    discriminates nothing), and its consistency probe cannot refute the
    hypothesis either. So the class is genuinely unshippable HERE: the rival is
    rejected for a real reason (the obligation is not discharged) but no witness
    can attribute that rejection to the spec. Recorded as a carrier limit of
    ``partial def``, not as a spec hole and not as a hard case.

  * UNGROUNDED-ORACLE ECHO — VACUOUS. The postcondition is GROUNDED: ``result`` is
    pinned to a term built only from the input ``s`` (``s`` itself on the ASCII
    arm; ``(canonDecompose s).filter …`` on the other). ``canonDecompose`` /
    ``isCombiningMark`` are ``opaque`` carriers for UNCHANGED platform routines,
    NOT an answer key for the modeled decision — the impl must still compute the
    branch, apply the decomposition, and run the filter. In their place the
    battery carries honest cheapest-implementation POSITIVE CONTROLS.

  * PARTIAL-DOMAIN / CONTROL-FLOW / VALUE — APPLIES. These are the nagini
    uniqueness rivals (partial-no-filter, partial-inverted-filter,
    partial-skip-decompose, cf-always-return-input). Each ports directly: a wrong
    impl that is correct on part of the domain and wrong on the arm it mishandles.

CONDITIONING ON THE CARRIER. ``canonDecompose`` is ``opaque``, so on the
non-ASCII arm no literal input makes the spec ``decide``-able:
``canonDecompose [ñ]`` and ``[ñ].filter …`` are distinct terms with no computable
value. The five non-ASCII refutations are therefore stated at a point described by
hypothesis — a weak, satisfiable disequality asserting the rival's returned term
differs from the spec's pinned term at the concrete input — reading: whenever the
decomposition/filter distinguishes them, the rival's answer differs from the
spec's, exactly the sub-domain where the rival is wrong. Four of them carry a
SINGLE hypothesis; ``weak-guard-decomposed-fixpoint`` carries TWO (the input is
its own decomposition, AND its mark-filtered form differs from it), because a
guard rival has to describe both why the wrong branch FIRES and why firing is
wrong. In every case the assumptions are jointly satisfiable — no ``False`` is
derivable from a disequality between opaque terms, and the gate's consistency
probe confirms it per case. The ASCII-arm witness needs no hypothesis: the ASCII
branch is fully transparent (``decide``).

BINDER / POINT / CLAUSE SPREAD. The single spec binder ``s`` is moved across the
reject witnesses rather than fixed: it takes an all-ASCII value (``['a']``), a
bare-combining-mark value (``[U+0300]``), a precomposed-accent value
(``[U+00F1]``, "n with tilde"), an ALREADY-DECOMPOSED value (``['o', U+0308]``),
and a DOUBLY-MARKED value (``['o', U+0308, U+0304]``, the only 3-code-point
point). Two rivals share the ``[U+0300]`` point and two share the ``[U+00F1]``
point, but each pair attacks a DIFFERENT clause at it, so the sharing is not a
coverage gap; the spread that matters is over clauses, and all THREE are
attacked — the ASCII arm by ``ascii-arm-drop``, the non-ASCII arm by the four
partial-domain rivals plus ``weak-erase-first-mark-only`` (which alone probes
the filter's UNIVERSALITY, i.e. that EVERY mark is dropped and not just one),
and the BRANCH CONDITION that selects between them by
``weak-guard-decomposed-fixpoint`` — so no clause is left undefended.

AUDIT RECORD (independent adversarial re-derivation; every claim below is an
exit code observed on this carrier, not an argument).

  * Statement integrity: all ``theorem correct_stripAccents`` statements across
    every case are RAW BYTE-IDENTICAL to the frozen one, not merely
    whitespace-equal — no case reformats the obligation.
  * Witness discrimination re-derived for all reject cases: witness holds of the
    rival (0), fails on the frozen solution (1), consistency probe leaves
    ``False`` unproven (1, so the hypotheses are satisfiable). Each gold-side
    failure was READ, not just counted: the frozen file's spec equality is
    discharged by ``simp``, leaving the hypothesis at type ``True``, so the
    refutation fails because the claim is FALSE of gold — a semantic refutation,
    not a missing identifier, unfolding failure, or timeout.
  * A check the gate cannot perform: every witness was ALSO built against a
    CORRECT-but-reshaped impl of the same spec (this battery's own
    ``pos-negated-branch``). All fail there (1), which is what distinguishes a
    refutation of a WRONG impl from a tactic mismatch that any reshape triggers.
  * FORGERY test (the check that decides whether an
    ``Application type mismatch … has type True`` gold-side error carries any
    information about the CLAIM, rather than being the same error every claim
    gets). Run in both forms on all six conditioned witnesses. (a) Flip the
    claim — drop the ``¬`` and assert the spec HOLDS at that input — and the exit
    codes INVERT: gold 0, rival 1, with gold's build clean and the rival's
    reporting ``unsolved goals`` on the concrete equation. (b) Reveal the
    hypothesis's type by replacing the closing step with ``exact (heq : Nat)``:
    on gold ``heq has type True`` (so ``simp`` PROVED the spec equation there),
    on the rival it has the concrete unproven equation. Both forms show gold's
    exit code tracks the claim, so these are genuine refutations, not hollow.
  * SPEC-TOO-WEAK probe (13 NEW wrong impls the battery does not contain, aimed
    at the least-probed clause): guard on decomposed-ness; ``any`` for ``all`` in
    the guard; guard negated; guard ORed with the decomposed-ness test; guard on
    the decomposition's LENGTH; guard on the head code point only;
    filter-then-decompose (order swapped); decompose twice; filter the raw input
    AND the decomposition; keep only the ASCII code points on the non-ASCII arm;
    ``takeWhile`` for ``filter``; ASCII arm returns the reversed input; a
    wrong-only-at-the-empty-input edge rival. ALL THIRTEEN REJECTED — no spec
    hole. Two are now shipped, as ``weak-guard-decomposed-fixpoint`` and
    ``weak-erase-first-mark-only``.
  * SPEC-TOO-STRONG probe (10 NEW correct reshapes): plain ``if``-``then``-``else``
    with no ``Id.run do``; guard written ``= true``; prefix ``List.filter``;
    predicate as an ``if``-expression; ``match`` on the guard; a double-negated
    guard — all six VERIFY under the FROZEN tactic body, so the spec is not
    over-fit to the frozen spelling. Three more are correct but NOT definitionally
    the frozen impl, so the frozen tactic body does not close them; each was then
    PROVEN rather than recorded as a hole (a ``foldr`` for the filter, now shipped
    as ``pos-foldr-not-defeq``; an impl-region helper ``def``, closed by adding it
    to the ``unfold`` list; an ASCII arm returning ``s.filter isAscii``, closed by
    ``List.filter_eq_self`` + ``List.all_eq_true``). The tenth (apply the mark
    filter on the ASCII arm too) is rejected, and correctly so: the ASCII arm
    pins ``result = s`` exactly, and making that impl correct needs "no ASCII code
    point is a combining mark" — a property of the platform predicate that this
    bundle deliberately does NOT axiomatize (both callees are A-references with no
    consumed contract, validated executably by the conformance gate). Confirmed
    unavailable by building it: it does not follow from anything in scope. That is
    a modeling boundary of the opaque-callee choice, not a spec defect, and it
    costs nothing since the impl it forbids is one no faithful patch writes.

AXIOM lane: EMPTY here. The bundle declares two ``opaque`` leaves (the unchanged
platform decomposition and combining-mark predicate), both A-references validated
by the conformance/axiom gate, and consumes no ``axiom``. That lane belongs to
G-AX; this gate ignores it, and the nagini ``AXIOM_TESTS`` are dropped.
"""
from pathlib import Path

INSTANCE = "scikit-learn__scikit-learn-15100"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- region anchors (each unique inside Solution.lean; verified at load) ----
# The whole gold impl def, strictly INSIDE the impl region.
_GOLD_IMPL = (
    "def implementation_stripAccents (s : List Char) : List Char := Id.run do\n"
    "  if s.all isAscii then\n"
    "    return s\n"
    "  let normalized := canonDecompose s\n"
    "  return normalized.filter (fun c => !isCombiningMark c)"
)

# The first tactic line of the frozen proof body (inside the proof region).
_P_INTRO = "  intro s\n"

# The WHOLE frozen tactic body (inside the proof region). Needed by the one
# positive whose impl is not definitionally the frozen one: it must both add an
# inline `have` AND feed that `have` to the closing `simp`, and inserting before
# `intro s` alone leaves the closing tactic unchanged, so the new hypothesis
# never reaches the goal. (Measured: that mistake makes the case fail as
# SPEC-TOO-STRONG on an impl that is provably correct — a false finding.)
_P_BODY = (
    "  intro s\n"
    "  unfold problem_spec_stripAccents implementation_stripAccents\n"
    "  by_cases h : s.all isAscii <;> simp [h, Id.run, pure, bind]"
)


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # implementations that MUST verify. If a faithful correct implementation
    # cannot satisfy the frozen obligation the spec is SPEC-TOO-STRONG. Each
    # keeps the theorem STATEMENT byte-identical; the reshapes preserve the
    # definitional form so the frozen `by_cases … <;> simp` proof still closes —
    # no helper lemma, no axiom, no assumption token.
    #
    # Ports nagini's soundness positive (pos-control-reorder): a control-flow
    # reshape of the two-arm branch that keeps the modeled behavior.
    # =====================================================================
    {
        "id": "pos-negated-branch",
        "kind": "soundness",
        "expect": "verify",
        # Structurally-different but CORRECT: test the NEGATED condition first,
        # returning the decompose-and-filter result on the non-ASCII arm, and
        # fall through to the verbatim-return on the ASCII arm — the mirror image
        # of the frozen branch order. Same value flows out on every input.
        "module": _swap(
            _BASE, _GOLD_IMPL,
            "def implementation_stripAccents (s : List Char) : List Char := Id.run do\n"
            "  if !s.all isAscii then\n"
            "    return (canonDecompose s).filter (fun c => !isCombiningMark c)\n"
            "  return s",
        ),
        "rationale": "the two-arm postcondition is reshaped by testing the "
                     "NEGATED ASCII condition first (non-ASCII arm returns "
                     "decompose-and-filter; ASCII arm falls through to the "
                     "verbatim return), the mirror of the frozen branch order. "
                     "The same value flows out on every input, so both arms of "
                     "`if s.all isAscii then result = s else result = "
                     "(canonDecompose s).filter …` still hold. Must verify, else "
                     "the spec is over-fit to the frozen branch order => "
                     "SPEC-TOO-STRONG. Proof: frozen tactic body retained "
                     "(`by_cases h : s.all isAscii <;> simp`). Ports nagini's "
                     "control-flow reorder positive.",
    },
    {
        "id": "pos-filter-staged-in-local",
        "kind": "soundness",
        "expect": "verify",
        # Structurally-different but CORRECT: stage the decomposition AND the
        # filtered result through immutable locals before returning, rather than
        # returning the filter application directly. Same behaviour; the locals
        # zeta-reduce so the frozen proof still closes.
        "module": _swap(
            _BASE, _GOLD_IMPL,
            "def implementation_stripAccents (s : List Char) : List Char := Id.run do\n"
            "  if s.all isAscii then\n"
            "    return s\n"
            "  let normalized := canonDecompose s\n"
            "  let stripped := normalized.filter (fun c => !isCombiningMark c)\n"
            "  return stripped",
        ),
        "rationale": "a correct impl that stages the decomposition and the "
                     "filtered result through immutable locals before returning "
                     "(local-variable reshape) must verify; if not, the spec is "
                     "over-fit to the direct-return spelling => SPEC-TOO-STRONG. "
                     "Doubles as the cheapest-honest control: the spec is GROUNDED "
                     "(no answer key to echo), so this honest impl IS a cheapest "
                     "verifier. Proof: frozen tactic body retained (the locals "
                     "zeta-reduce, each `by_cases` arm closes by `simp`).",
    },
    # AUDIT ADDITION (soundness). Both positives above are reshapes that the
    # FROZEN tactic body still closes — which is exactly what makes them weak
    # evidence against SPEC-TOO-STRONG. A branch-order swap and a `let` staging
    # are DEFINITIONALLY the frozen impl (they differ by iota/zeta reduction
    # only), so `by_cases h <;> simp` closes them for the same reason it closes
    # gold, and neither one probes whether the spec can accept a correct impl
    # that computes the mark-dropping step by a genuinely different ALGORITHM.
    # Measured while auditing: a `foldr` impl — observationally equal to the
    # frozen `filter` but NOT definitionally equal — is REJECTED by the frozen
    # tactic body (exit 1, `unsolved goals: List.foldr … = List.filter …`). That
    # rejection is a tactic artifact, not a spec verdict, and telling the two
    # apart is the whole point of the soundness lane; so the reshape is landed
    # here WITH the inline induction that discharges it, proving the spec itself
    # accepts the different algorithm. If this could NOT be proven, the spec
    # would be pinned to `List.filter` as a SPELLING rather than to the
    # mark-dropping BEHAVIOR => SPEC-TOO-STRONG.
    {
        "id": "pos-foldr-not-defeq",
        "kind": "soundness",
        "expect": "verify",
        # Structurally-different AND not definitionally equal: drop the combining
        # marks with a right fold that conses non-marks onto the accumulator,
        # instead of `List.filter`. Same value on every input, but the equality
        # needs an INDUCTION on the decomposed list — no `simp` normal form
        # relates the two terms. The induction is an inline `have` inside the
        # existing tactic body: no new top-level declaration, no axiom, no
        # assumption token, and the theorem statement stays byte-identical.
        "module": _swap(
            _swap(
                _BASE, _GOLD_IMPL,
                "def implementation_stripAccents (s : List Char) : List Char := Id.run do\n"
                "  if s.all isAscii then\n"
                "    return s\n"
                "  let normalized := canonDecompose s\n"
                "  return normalized.foldr\n"
                "    (fun c acc => if isCombiningMark c then acc else c :: acc) []",
            ),
            _P_BODY,
            "  intro s\n"
            "  have key : ∀ t : List Char,\n"
            "      t.foldr (fun c acc => if isCombiningMark c then acc else c :: acc) []\n"
            "        = t.filter (fun c => !isCombiningMark c) := by\n"
            "    intro t\n"
            "    induction t with\n"
            "    | nil => simp\n"
            "    | cons c u ih =>\n"
            "      by_cases hc : isCombiningMark c <;> simp [List.filter, hc, ih]\n"
            "  unfold problem_spec_stripAccents implementation_stripAccents\n"
            "  by_cases h : s.all isAscii <;> simp [h, Id.run, pure, bind, key]",
        ),
        "rationale": "the mark-dropping step is recomputed by a RIGHT FOLD "
                     "(cons the non-marks onto the accumulator) instead of "
                     "`List.filter`. Unlike the other two positives this is NOT "
                     "definitionally the frozen impl — no `simp` normal form "
                     "relates `List.foldr …` to `List.filter …`, so the frozen "
                     "tactic body alone does NOT close it, and the case supplies "
                     "the missing induction as an inline `have` (no new top-level "
                     "declaration, statement byte-identical). Must verify, else "
                     "the spec pins the mark-dropping step to the `List.filter` "
                     "SPELLING rather than to its BEHAVIOR => SPEC-TOO-STRONG. "
                     "This is the positive that makes the soundness lane "
                     "load-bearing: the branch-order and `let`-staging reshapes "
                     "verify by iota/zeta reduction, so they cannot distinguish a "
                     "spec that accepts a different algorithm from one that "
                     "merely accepts a different spelling of the same term.",
    },

    # =====================================================================
    # ADMISSIBILITY — a positive control confirming the obligation is
    # SATISFIABLE (non-vacuous) at the F2P discriminator input rather than only
    # in the abstract. The frozen theorem carries NO precondition hypothesis (the
    # modeled behavior is total, so `∀` is unguarded), so nagini's
    # precondition-admission probe (admiss-f2p-input) has no binder to attack
    # here; the honest analogue discharges the spec predicate at the exact F2P
    # input in a `have` alongside the frozen obligation. Ports nagini's
    # admissibility case.
    # =====================================================================
    {
        "id": "admiss-f2p-decomposed",
        "kind": "admissibility",
        "expect": "verify",
        # Discharge the obligation at the F2P discriminator ['o', U+0308]
        # ("o" + combining diaeresis, the already-decomposed accented input the
        # test observes) in a `have`, then close the frozen obligation verbatim.
        # Nothing is assumed: no new declaration, statement byte-identical, the
        # ground instance is a `have` inside the existing tactic body.
        "module": _swap(
            _BASE, _P_INTRO,
            "  have _ground : problem_spec_stripAccents [Char.ofNat 111, Char.ofNat 0x308]\n"
            "      (implementation_stripAccents [Char.ofNat 111, Char.ofNat 0x308]) := by\n"
            "    unfold problem_spec_stripAccents implementation_stripAccents\n"
            "    have hasc : ([Char.ofNat 111, Char.ofNat 0x308] : List Char).all isAscii = false := by decide\n"
            "    simp only [Id.run, pure, bind, Id.run_bind, hasc, if_false, Bool.false_eq_true]\n"
            "  intro s\n",
        ),
        "rationale": "the obligation is discharged at the F2P discriminator "
                     "['o', U+0308] (a base letter followed by a separate "
                     "combining diaeresis — the already-decomposed accented input "
                     "the test observes), whose effective behavior is the "
                     "non-ASCII decompose-and-drop arm, then the frozen obligation "
                     "is closed verbatim. Verifies (else the modeled behavior is "
                     "unsatisfiable at exactly the input the F2P exercises — the "
                     "analogue of PRECOND-TOO-STRONG). Nothing is assumed: no new "
                     "declaration, the theorem statement is byte-identical, and the "
                     "ground instance is a `have` inside the existing tactic body. "
                     "Ports nagini's admissibility probe.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong implementations sharing the
    # frozen spec that MUST be rejected. Each carries (a) the refinement argument
    # that its faithful real patch would NOT resolve the F2P, so a verifying rival
    # would be a true verify-does-not-imply-resolve break, and (b) a refutation
    # witness (conditioning on the opaque callees where the arm is opaque, or by
    # `decide` where transparent).
    # =====================================================================

    # ---- non-ASCII arm: keep every code point (drop the mark filter) ----
    {
        "id": "weak-no-filter",
        "kind": "uniqueness",
        "expect": "reject",
        # Decompose then keep EVERY code point (never test the combining-mark
        # predicate): returns the decomposition with combining marks intact.
        "module": _swap(
            _BASE, _GOLD_IMPL,
            "def implementation_stripAccents (s : List Char) : List Char := Id.run do\n"
            "  if s.all isAscii then\n"
            "    return s\n"
            "  let normalized := canonDecompose s\n"
            "  return normalized",
        ),
        "refinement": "the faithful real patch — decompose then keep every code "
                      "point without the combining-mark filter — returns the "
                      "decomposition with its combining marks still attached. On "
                      "the F2P inputs (a base letter plus a separate combining "
                      "mark, or bare combining marks) the marks survive instead of "
                      "being dropped, so the observed result differs from the "
                      "expected base-only string; that patch would NOT resolve.",
        "rationale": "REJECT from the non-ASCII arm: with a non-ASCII input the "
                     "spec pins `result = (canonDecompose s).filter (fun c => "
                     "!isCombiningMark c)` (marks DROPPED) while the rival returns "
                     "`canonDecompose s` (marks KEPT), distinct terms wherever the "
                     "decomposition carries a combining mark. Binder spread: "
                     "s = [U+0300] (a bare combining mark). If it verified => "
                     "SPEC-TOO-WEAK (the filter clause is not pinned). Ports nagini "
                     "partial-no-filter.",
        "witness": (
            "-- Refuted on the non-ASCII arm. `canonDecompose`/`isCombiningMark`\n"
            "-- are opaque, so no literal decides the goal; condition on them.\n"
            "-- The single hypothesis is satisfiable (the decomposition of a bare\n"
            "-- combining mark may differ from its combining-mark-filtered form)\n"
            "-- and states exactly the sub-domain where the rival is wrong.\n"
            "example (h : (canonDecompose [Char.ofNat 0x300])\n"
            "      ≠ (canonDecompose [Char.ofNat 0x300]).filter (fun c => !isCombiningMark c)) :\n"
            "    ¬ problem_spec_stripAccents [Char.ofNat 0x300]\n"
            "        (implementation_stripAccents [Char.ofNat 0x300]) := by\n"
            "  unfold problem_spec_stripAccents implementation_stripAccents\n"
            "  have hasc : ([Char.ofNat 0x300] : List Char).all isAscii = false := by decide\n"
            "  simp only [Id.run, pure, bind, Id.run_bind, hasc, if_false, Bool.false_eq_true]\n"
            "  intro heq\n"
            "  exact h heq\n"
        ),
    },

    # ---- non-ASCII arm: invert the filter (keep marks, drop bases) ----
    {
        "id": "weak-inverted-filter",
        "kind": "uniqueness",
        "expect": "reject",
        # Filter with the WRONG predicate: keep combining marks, drop the
        # non-combining base characters — returns the marks-only subsequence.
        "module": _swap(
            _BASE, _GOLD_IMPL,
            "def implementation_stripAccents (s : List Char) : List Char := Id.run do\n"
            "  if s.all isAscii then\n"
            "    return s\n"
            "  let normalized := canonDecompose s\n"
            "  return normalized.filter (fun c => isCombiningMark c)",
        ),
        "refinement": "inverting the predicate keeps the combining marks and drops "
                      "the base characters, returning the marks-only subsequence. "
                      "On the F2P inputs the expected base-only string is replaced "
                      "by the discarded marks (or by the empty string on a base "
                      "letter that had no attached mark), so the observed result "
                      "differs from the expected one; that patch would NOT resolve.",
        "rationale": "REJECT from the non-ASCII arm: the spec KEEPS non-combining "
                     "code points and DROPS combining ones; the rival keeps the "
                     "complement, so `result` is the marks-only subsequence, "
                     "contradicting the pinned filter. Binder spread: s = [U+0300]. "
                     "If it verified => SPEC-TOO-WEAK (the filter POLARITY is not "
                     "pinned). Ports nagini partial-inverted-filter.",
        "witness": (
            "-- Refuted on the non-ASCII arm. Single satisfiable hypothesis over\n"
            "-- the opaque callees: the marks-only subsequence differs from the\n"
            "-- bases-only subsequence of the decomposition.\n"
            "example (h : (canonDecompose [Char.ofNat 0x300]).filter (fun c => isCombiningMark c)\n"
            "      ≠ (canonDecompose [Char.ofNat 0x300]).filter (fun c => !isCombiningMark c)) :\n"
            "    ¬ problem_spec_stripAccents [Char.ofNat 0x300]\n"
            "        (implementation_stripAccents [Char.ofNat 0x300]) := by\n"
            "  unfold problem_spec_stripAccents implementation_stripAccents\n"
            "  have hasc : ([Char.ofNat 0x300] : List Char).all isAscii = false := by decide\n"
            "  simp only [Id.run, pure, bind, Id.run_bind, hasc, if_false, Bool.false_eq_true]\n"
            "  intro heq\n"
            "  exact h heq\n"
        ),
    },

    # ---- non-ASCII arm: skip the decomposition (filter the RAW input) ----
    {
        "id": "weak-skip-decompose",
        "kind": "uniqueness",
        "expect": "reject",
        # Omit the decomposition and filter the RAW input: correct wherever the
        # decomposition equals the input, WRONG on a precomposed accented glyph
        # (a single non-combining code point that is never split, so its accent
        # is never separated and dropped).
        "module": _swap(
            _BASE, _GOLD_IMPL,
            "def implementation_stripAccents (s : List Char) : List Char := Id.run do\n"
            "  if s.all isAscii then\n"
            "    return s\n"
            "  return s.filter (fun c => !isCombiningMark c)",
        ),
        "refinement": "omitting the decomposition and filtering the RAW input "
                      "leaves a PRECOMPOSED accented glyph (a single non-combining "
                      "code point, e.g. 'n with tilde') untouched, because it is "
                      "never split into base + mark. The test expects such a glyph "
                      "reduced to its base letter, so the observed result still "
                      "carries the accent and differs from the expected base "
                      "letter; that patch would NOT resolve.",
        "rationale": "REJECT from the non-ASCII arm: the spec pins the result to "
                     "the filter of `canonDecompose s`; the rival filters `s` "
                     "directly, dropping the decomposition, so the two diverge "
                     "wherever `canonDecompose s ≠ s` (precomposed glyphs). Binder "
                     "spread: s = [U+00F1] (precomposed 'n with tilde'), a point "
                     "distinct from the bare-combining-mark and "
                     "already-decomposed points (though SHARED with "
                     "`weak-always-return-input`, which refutes at the same "
                     "input on a different clause). If it verified => "
                     "SPEC-TOO-WEAK (the decomposition step is not pinned — the "
                     "exact reported bug). Ports nagini partial-skip-decompose.",
        "witness": (
            "-- Refuted on a precomposed glyph. Single satisfiable hypothesis:\n"
            "-- filtering the raw glyph differs from filtering its decomposition\n"
            "-- (the decomposition splits off the accent the raw filter cannot).\n"
            "example (h : ([Char.ofNat 0x00F1] : List Char).filter (fun c => !isCombiningMark c)\n"
            "      ≠ (canonDecompose [Char.ofNat 0x00F1]).filter (fun c => !isCombiningMark c)) :\n"
            "    ¬ problem_spec_stripAccents [Char.ofNat 0x00F1]\n"
            "        (implementation_stripAccents [Char.ofNat 0x00F1]) := by\n"
            "  unfold problem_spec_stripAccents implementation_stripAccents\n"
            "  have hasc : ([Char.ofNat 0x00F1] : List Char).all isAscii = false := by decide\n"
            "  simp only [Id.run, pure, bind, Id.run_bind, hasc, if_false, Bool.false_eq_true]\n"
            "  intro heq\n"
            "  exact h heq\n"
        ),
    },

    # ---- non-ASCII arm: return the input unchanged unconditionally ----
    {
        "id": "weak-always-return-input",
        "kind": "uniqueness",
        "expect": "reject",
        # Return the input verbatim on EVERY input (no decomposition, no filter):
        # the reported bug generalised. Correct only when the input is already
        # mark-free in decomposed form, wrong on every accented/combining input.
        "module": _swap(
            _BASE, _GOLD_IMPL,
            "def implementation_stripAccents (s : List Char) : List Char := Id.run do\n"
            "  return s",
        ),
        "refinement": "returning the input unchanged on every input (no "
                      "decomposition, no filter) is the reported bug generalised. "
                      "On a precomposed accented input the accent is never "
                      "stripped, so the observed result equals the accented input "
                      "instead of the expected base letter; that patch would NOT "
                      "resolve.",
        "rationale": "REJECT from the non-ASCII arm: returning `s` gives "
                     "`result = s`, which equals `(canonDecompose s).filter …` "
                     "only when `s` is already mark-free in decomposed form — "
                     "false on a precomposed accented input. Binder spread: "
                     "s = [U+00F1] (precomposed 'n with tilde'). If it verified => "
                     "SPEC-TOO-WEAK (the non-ASCII arm is not pinned to the "
                     "transform). Ports nagini cf-always-return-input.",
        "witness": (
            "-- Refuted on a precomposed glyph. Single satisfiable hypothesis:\n"
            "-- the raw glyph differs from its decompose-and-filter transform\n"
            "-- (the accent that the transform strips).\n"
            "example (h : ([Char.ofNat 0x00F1] : List Char)\n"
            "      ≠ (canonDecompose [Char.ofNat 0x00F1]).filter (fun c => !isCombiningMark c)) :\n"
            "    ¬ problem_spec_stripAccents [Char.ofNat 0x00F1]\n"
            "        (implementation_stripAccents [Char.ofNat 0x00F1]) := by\n"
            "  unfold problem_spec_stripAccents implementation_stripAccents\n"
            "  have hasc : ([Char.ofNat 0x00F1] : List Char).all isAscii = false := by decide\n"
            "  simp only [Id.run, pure, bind, Id.run_bind, hasc, if_false, Bool.false_eq_true]\n"
            "  intro heq\n"
            "  exact h heq\n"
        ),
    },

    # ---- the BRANCH CONDITION itself: guard on decomposed-ness, not ASCII ----
    # AUDIT ADDITION. Every other rival in this battery keeps the frozen guard
    # `s.all isAscii` BYTE-VERBATIM and attacks only the arm BODIES, so the
    # branch CONDITION — the clause that decides which arm runs, and the clause
    # whose mis-statement is the whole reported defect — had no rival, and the
    # already-decomposed discriminator input appeared only in the admissibility
    # POSITIVE (where it is asserted to hold, never used as a refutation point).
    # This case pins the condition.
    {
        "id": "weak-guard-decomposed-fixpoint",
        "kind": "uniqueness",
        "expect": "reject",
        # Take the verbatim-return fast path when the input EQUALS its own
        # canonical decomposition, instead of when it is plain ASCII. Correct on
        # every precomposed glyph (whose decomposition differs from it) and on
        # every all-ASCII input, WRONG on exactly the inputs that are already
        # supplied in decomposed form: they are their own decomposition, so they
        # are returned untouched and their combining marks are never dropped.
        "module": _swap(
            _BASE, _GOLD_IMPL,
            "def implementation_stripAccents (s : List Char) : List Char := Id.run do\n"
            "  let normalized := canonDecompose s\n"
            "  if normalized = s then\n"
            "    return s\n"
            "  return normalized.filter (fun c => !isCombiningMark c)",
        ),
        "refinement": "a faithful patch whose fast-path guard tests whether the "
                      "text already equals its own canonical decomposition, "
                      "rather than whether it is plain ASCII, returns an "
                      "already-decomposed accented string untouched. On the "
                      "discriminator inputs a base letter plus a separate "
                      "combining mark, and a run of bare combining marks, the "
                      "observed result keeps the marks while the expected result "
                      "is the base-only string (respectively the empty string); "
                      "3 of the 7 assertions the accent-stripping test makes "
                      "would fail, so that patch would NOT resolve.",
        "rationale": "REJECT from the BRANCH CONDITION (the clause every other "
                     "rival here leaves verbatim): the spec pins the "
                     "verbatim-return arm to `s.all isAscii`, so on a non-ASCII "
                     "input it demands `result = (canonDecompose s).filter (fun c "
                     "=> !isCombiningMark c)` REGARDLESS of whether `s` happens "
                     "to equal its own decomposition. The rival returns `s` on "
                     "that sub-domain. Binder spread: s = ['o', U+0308] (an "
                     "already-decomposed accented input — a THIRD point, distinct "
                     "from the bare-mark and precomposed points the other rivals "
                     "use, and the one the arm-body rivals all leave at its "
                     "correct value). If it verified => SPEC-TOO-WEAK (the guard "
                     "would be free to key on decomposed-ness, the precise "
                     "distinction this spec exists to draw).",
        "witness": (
            "-- Refuted at ['o', U+0308] (a base letter followed by a separate\n"
            "-- combining mark). `canonDecompose`/`isCombiningMark` are opaque, so\n"
            "-- the point is described by HYPOTHESIS: h1 says this input is already\n"
            "-- in decomposed form (it IS its own decomposition, which is what\n"
            "-- makes the rival's guard fire), h2 says its mark-filtered form\n"
            "-- differs from it (which is what makes firing WRONG). Both hold of\n"
            "-- the real routines and are jointly satisfiable — no tactic derives\n"
            "-- `False` from an opaque term — and together they are exactly the\n"
            "-- sub-domain where a guard keyed on decomposed-ness is wrong.\n"
            "-- h1 rewrites the opaque application to the literal everywhere it\n"
            "-- occurs, INCLUDING inside the spec's pinned term, so h2 is stated in\n"
            "-- that post-rewrite form.\n"
            "example (h1 : canonDecompose [Char.ofNat 111, Char.ofNat 0x308]\n"
            "      = [Char.ofNat 111, Char.ofNat 0x308])\n"
            "    (h2 : ([Char.ofNat 111, Char.ofNat 0x308] : List Char)\n"
            "      ≠ ([Char.ofNat 111, Char.ofNat 0x308] : List Char).filter\n"
            "          (fun c => !isCombiningMark c)) :\n"
            "    ¬ problem_spec_stripAccents [Char.ofNat 111, Char.ofNat 0x308]\n"
            "        (implementation_stripAccents [Char.ofNat 111, Char.ofNat 0x308]) := by\n"
            "  unfold problem_spec_stripAccents implementation_stripAccents\n"
            "  have hasc : ([Char.ofNat 111, Char.ofNat 0x308] : List Char).all isAscii\n"
            "      = false := by decide\n"
            "  simp only [Id.run, pure, bind, hasc, if_false, Bool.false_eq_true, h1,\n"
            "    if_pos]\n"
            "  intro heq\n"
            "  exact h2 heq\n"
        ),
    },

    # ---- non-ASCII arm: drop only the FIRST combining mark ----
    # AUDIT ADDITION. Every non-ASCII rival above gets the mark-dropping step
    # either wholly right or wholly wrong (no filter, inverted filter, no
    # decomposition, no transform at all), so each is refuted at an input
    # carrying a SINGLE mark and none of them probes the filter's UNIVERSALITY:
    # the spec drops EVERY mark, and a rival that drops one is wrong only on
    # inputs where a base character carries more than one. Checked against the
    # real routines while auditing: such a rival still satisfies the accented
    # inputs the other rivals fail, but not a base letter with two stacked
    # marks. That is a genuine sub-domain of the load-bearing clause that the
    # battery left undefended, and it is a THIRD non-ASCII refutation point
    # (a 3-code-point input), which no other case uses.
    {
        "id": "weak-erase-first-mark-only",
        "kind": "uniqueness",
        "expect": "reject",
        # Decompose, then remove only the FIRST combining mark (`List.eraseP`
        # stops after one hit) instead of every one. Correct on every input whose
        # decomposition carries at most one mark — which includes all the
        # single-accent glyphs the other rivals are refuted at — and WRONG on a
        # base character carrying two or more stacked marks.
        "module": _swap(
            _BASE, _GOLD_IMPL,
            "def implementation_stripAccents (s : List Char) : List Char := Id.run do\n"
            "  if s.all isAscii then\n"
            "    return s\n"
            "  let normalized := canonDecompose s\n"
            "  return normalized.eraseP (fun c => isCombiningMark c)",
        ),
        "refinement": "a faithful patch that removes only the FIRST combining "
                      "mark it finds rather than every one leaves the second and "
                      "later marks attached. It survives every single-accent "
                      "input, but on a base letter carrying two stacked marks the "
                      "observed result keeps the surplus mark while the expected "
                      "result is the bare base letter, and on a run of several "
                      "bare marks all but the first survive where the empty "
                      "string is expected. Checked against the real routines: 4 "
                      "of the 7 assertions the accent-stripping test makes would "
                      "fail, so that patch would NOT resolve.",
        "rationale": "REJECT from the UNIVERSALITY of the filter clause: the spec "
                     "pins `result = (canonDecompose s).filter (fun c => "
                     "!isCombiningMark c)`, which drops EVERY combining mark, "
                     "while the rival drops exactly one. The other non-ASCII "
                     "rivals get this step wholly right or wholly wrong, so all "
                     "of them are refutable at a single-mark input and none "
                     "distinguishes 'drops marks' from 'drops all marks'. Binder "
                     "spread: s = ['o', U+0308, U+0304] (a base letter with two "
                     "stacked marks — a FOURTH point, and the only 3-code-point "
                     "input in the battery). If it verified => SPEC-TOO-WEAK (the "
                     "filter would be free to drop just one mark).",
        "witness": (
            "-- Refuted at ['o', U+0308, U+0304] (a base letter carrying two\n"
            "-- stacked combining marks). `canonDecompose`/`isCombiningMark` are\n"
            "-- opaque, so the point is described by HYPOTHESIS: erasing the first\n"
            "-- mark of the decomposition differs from filtering all of them.\n"
            "-- Satisfiable (no tactic derives `False` from a disequality between\n"
            "-- opaque terms; the gate's consistency probe confirms it), and it\n"
            "-- states exactly the sub-domain where dropping one mark is wrong.\n"
            "example (h : (canonDecompose [Char.ofNat 111, Char.ofNat 0x308, Char.ofNat 0x304]).eraseP\n"
            "        (fun c => isCombiningMark c)\n"
            "      ≠ (canonDecompose [Char.ofNat 111, Char.ofNat 0x308, Char.ofNat 0x304]).filter\n"
            "          (fun c => !isCombiningMark c)) :\n"
            "    ¬ problem_spec_stripAccents [Char.ofNat 111, Char.ofNat 0x308, Char.ofNat 0x304]\n"
            "        (implementation_stripAccents\n"
            "          [Char.ofNat 111, Char.ofNat 0x308, Char.ofNat 0x304]) := by\n"
            "  unfold problem_spec_stripAccents implementation_stripAccents\n"
            "  have hasc : ([Char.ofNat 111, Char.ofNat 0x308, Char.ofNat 0x304] : List Char).all isAscii\n"
            "      = false := by decide\n"
            "  simp only [Id.run, pure, bind, hasc, if_false, Bool.false_eq_true]\n"
            "  intro heq\n"
            "  exact h heq\n"
        ),
    },

    # ---- ASCII arm: mishandle the verbatim fast path ----
    {
        "id": "ascii-arm-drop",
        "kind": "uniqueness",
        "expect": "reject",
        # Attacks the OTHER independent arm: on the all-ASCII fast path return the
        # empty list instead of the input verbatim. Correct on the empty-string
        # edge, wrong on every non-empty ASCII input. Fully transparent, so the
        # witness needs no hypothesis (`decide`).
        "module": _swap(
            _BASE, _GOLD_IMPL,
            "def implementation_stripAccents (s : List Char) : List Char := Id.run do\n"
            "  if s.all isAscii then\n"
            "    return []\n"
            "  let normalized := canonDecompose s\n"
            "  return normalized.filter (fun c => !isCombiningMark c)",
        ),
        # AUDIT CORRECTION. The previous text here claimed the accent-stripping
        # test asserts an all-ASCII sentence is returned unchanged. It does not:
        # every one of that test's inputs carries a non-ASCII code point, so this
        # rival passes all 7 of its assertions (checked by running the rival
        # against the real assertion list). The refutation is real but it lives in
        # the REGRESSION suite, not in the discriminating test, and the refinement
        # must say which — a refinement that names the wrong test is exactly the
        # unchecked prose an audit exists to catch.
        "refinement": "a faithful real patch that returned an empty string on the "
                      "ASCII fast path would map every accent-free ASCII input to "
                      "the empty string. It survives the accent-stripping test "
                      "itself, whose inputs all carry a non-ASCII code point, but "
                      "the accent-stripping option is also exercised by the "
                      "regression suite's tokenizer/n-gram tests, which feed it "
                      "pure-ASCII text and assert the resulting tokens: with the "
                      "text collapsed to the empty string those assertions get an "
                      "empty token list instead of the expected one. So the patch "
                      "breaks a previously-passing test and would NOT resolve "
                      "(resolution requires the regression set to keep passing, "
                      "not merely the discriminating test to pass).",
        "rationale": "REJECT from the ASCII arm (the OTHER independent top-level "
                     "arm): with an all-ASCII input the spec pins `result = s` "
                     "while the rival returns `[]`, distinct on any non-empty ASCII "
                     "input. Binder spread: s = ['a'] (an all-ASCII input — the "
                     "ASCII arm, which every non-ASCII rival leaves at its correct "
                     "verbatim value). If it verified => SPEC-TOO-WEAK (the "
                     "verbatim-return arm is not pinned).",
        "witness": (
            "-- Refuted on the ASCII arm, which is fully transparent — no opaque\n"
            "-- term, so `decide` closes it without any hypothesis.\n"
            "example : ¬ problem_spec_stripAccents ['a']\n"
            "    (implementation_stripAccents ['a']) := by\n"
            "  unfold problem_spec_stripAccents implementation_stripAccents\n"
            "  simp only [Id.run, pure, bind, Id.run_bind]\n"
            "  decide\n"
        ),
    },
]

# No AXIOM lane here: the bundle consumes no `axiom` (two `opaque` leaves — the
# unchanged platform decomposition and combining-mark predicate — are
# A-references validated by G-AX, not consumed contracts). The nagini
# AXIOM_TESTS belong to the axiom lane; dropped.
AXIOM_TESTS = []
