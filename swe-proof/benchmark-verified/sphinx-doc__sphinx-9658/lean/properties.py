"""properties.py — G-PBT falsification battery for sphinx-doc__sphinx-9658 (lean).

NOT a Lean file; a manifest of adversarial cases the G-PBT gate executes. Each
SPEC_TESTS case is a complete ``Solution.lean`` variant produced by REGION
SURGERY: only text strictly inside the ``-- impl-start`` / ``-- impl-end`` region
(and, for a case that legitimately re-proves, inside ``-- proof-start`` /
``-- proof-end``) is changed. The frozen spec — docstring, ``axioms``, ``pure``,
``post-conditions`` — stays byte-identical, so ``markers.same_spec`` holds by
construction and the single ``theorem correct_mockQualifiedName`` STATEMENT is
preserved verbatim in every case (only tactic bodies differ). No case introduces
an ``axiom``, a helper ``theorem``/``lemma``, ``sorry``/``admit``, or
``native_decide``.

``expect:"verify"`` passes iff the variant is in scope AND the file elaborates
with the obligation closed. ``expect:"reject"`` passes iff the variant is in
scope AND it does NOT verify AND the case's refutation ``witness`` HOLDS of the
rival while FAILING on the frozen solution.

PORT NOTE — this is a PORT of the nagini battery (``../nagini/properties.py``)
onto this backend's carrier, not a fresh invention. The nagini sibling models
THREE functions with fractional-permission contracts over ``List[int]`` code
points — a short-identifier site, a display-identifier site, and a renderer that
joins a module path, a dot, and the display identifier. This Lean bundle models
the SINGLE purely-functional core those three sites exist to serve: one total
``String -> String`` function, the reported qualified name of a stand-in, with
one obligation and one input binder. Nagini's renderer clauses (Q1/Q2/Q3, the
dotted join and the anti-dangling-dot length bound) and its short-identifier
clause (S) have no separate obligation here — the module path is outside the
modeled output (see ``mapping.md``: the spec frames the result to the short name
only). So most nagini cases collapse onto attacks on the ONE clause of the ONE
modeled obligation, and the case count legitimately shrinks from nagini's 11 to
9-with-a-different-shape. Per-nagini-case disposition is in the module
``assessment``.

AUDIT TRAIL — an independent adversarial audit re-derived every case with real
builds (the port had recorded SOUND). Two defects were found and FIXED here, both
in the port's own reasoning; the frozen spec was NOT implicated.

  1. A FALSE PASS_TO_PASS claim in ``weak-separator-glued``'s ``refinement``: it
     asserted the PASS_TO_PASS reference-rendering tests would also fail under
     that rival. They would not. All 24 PASS_TO_PASS tests pin references for
     CONCRETE types, which never construct a stand-in at all, and the single
     PASS_TO_PASS test that does build one already passed at ``base_commit`` —
     where the reported qualified name was empty — so it demonstrably does not
     read the modeled output. Withdrawn in place; the FAIL_TO_PASS test alone
     carries the refinement argument, which is all it needs.
  2. A MISSING POSITIVE SHAPE — the coverage gap that mattered. Every positive
     the port shipped is STRAIGHT-LINE, closed either by the frozen ``rfl``'s
     definitional reduction or by a two-arm ``by_cases``. But BOTH nagini
     positive controls this lane claims to port were indexed LOOP rebuilds
     carrying loop invariants, and ``spec_guide.md`` §2 names ``Id.run do`` +
     ``let mut`` + ``for`` the PREFERRED impl shape on this backend. The shape a
     faithful solver is most likely to write was thus the one shape the positive
     lane never exercised, so "a correct loop rebuild is provable against this
     identity clause" was an assumption rather than a result.
     ``pos-loop-accumulate-characters`` (added) is that case: it needs a genuine
     induction, and it VERIFIES — so the clause is confirmed not to be
     SPEC-TOO-STRONG on iterative shape.

Attacks that found NOTHING, recorded so the next reader need not repeat them.
Five NEW wrong implementations aimed at sub-domains the shipped rivals leave
unprobed — a single-point deviation wrong at exactly ONE short name, a case-folded
name, a TRAILING separator, a name wrong only at the empty input, and a reversed
name — were each given a generous proof attempt and NONE verified, so there is no
hole on the weak side. Three further correct reshapes (a double-reversal round
trip, an empty suffix appended on the right, and the loop now shipped) were
provable. A full-length ``String.take`` reshape could NOT be closed by the audit
and is recorded as UNCERTAIN rather than as a hole: its blocker is a looping
``simp`` set around ``String.length`` (max recursion depth), a tactic-library
artifact that says nothing about the spec.

DEFENDED SURFACE (one modeled behavior, one clause, one binder).

    problem_spec_mockQualifiedName (name : String) (result : String) : Prop :=
      result = name

  The qualified name a stand-in reports equals the short name it was created
  with. There is exactly ONE independent top-level clause — a total value-level
  string identity — and exactly ONE input binder, ``name``. The obligation is
  unguarded (``∀ (name : String), …``), so there is no precondition to attack and
  no partial domain: the clause must hold at every string, the empty one
  included.

  The clause is GROUNDED and fully transparent: ``result`` is pinned to the input
  itself, not to an opaque answer key. ``meta.json`` records ``axioms: []`` and
  ``opaque_callees: []``, so there is no callee to echo and no term that blocks
  ``decide``; every refutation below is stated at a literal input and closed by
  plain evaluation. No witness needs to CONDITION on the carrier, so no witness
  binds a hypothesis and the gate's consistency probe has nothing to check
  (``consistency_probe`` is ``None`` for all four).

  BEHAVIORAL DISCRIMINATOR. A stand-in whose reported qualified name is anything
  other than the short name it was created with makes the downstream renderer —
  which joins the containing module path, a dot, and the reported qualified name
  — emit an incomplete or wrong reference. The FAIL_TO_PASS test asserts the
  complete joined reference verbatim for a stand-in reached by attribute access,
  so ANY deviation of the reported name from the created-with name is observable
  there. That is why the four rivals below are refutable on this carrier even
  though the module path itself is not modeled: they each corrupt the trailing
  component the renderer consumes.

ADVERSARIAL READ of the nagini case classes on this carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS. Lean is referentially transparent: an
    input carries no heap permission, there is no read-only half-permission to
    overwrite, and no aliasing to exploit. Nagini's three frame-mutation rivals
    (each clearing a read-only identifier input in place) have NO expressible
    instance here — the Lean input is an immutable ``String`` value and a
    variant that rebinds a local cannot be observed by anyone. No substitute is
    fabricated. (nagini cases ``frame-mutate-short-name``,
    ``frame-mutate-qref-module``, ``frame-mutate-qref-name``.)

  * DIVERGENCE / NON-TERMINATION — VACUOUS here, and vacuous for the RIGHT
    reason. ``implementation_mockQualifiedName`` is a total Lean ``def`` (no
    ``partial``, no ``termination_by`` escape), so a diverging implementation
    cannot be written at all and there is no vacuous-``ensures`` hole to probe.
    This is NOT the velvet situation documented in ``the corpus-wide termination-semantics finding``
    (where ``loom.semantics.termination "partial"`` lets a non-terminating rival
    satisfy every clause vacuously and verify while its faithful real patch hangs
    the F2P): that is a KNOWN SPEC HOLE on that backend, whereas on this backend
    the class genuinely does not exist. The nagini sibling carries no
    ``diverge-*``/``nonterm-*``/``weak-diverge`` case either, so nothing is
    dropped.

  * UNGROUNDED-ORACLE ECHO — VACUOUS. The postcondition equates the result to the
    INPUT, so there is no oracle to echo: an implementation satisfying the clause
    has actually reported the short name. As in nagini, the class is replaced by
    honest cheapest-implementation positive controls.

  * PARTIAL-DOMAIN / VALUE — APPLIES, and carries the whole reject lane. Nagini's
    value rivals port one-for-one onto the single modeled site: report nothing
    (its ``weak-display-empty`` / ``weak-short-empty``), report a truncated
    trailing component (its ``weak-truncated-display-tail``), and glue the
    separator onto the reported name (its ``weak-missing-dot`` / dangling-dot
    pair, re-expressed as a corruption of the component the renderer joins).

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen ``rfl`` is tuned to the frozen
definitional form, and every rival below does break it with
``Tactic `rfl` failed``, exactly as a merely-RESHAPED correct implementation
would. A rejection alone therefore attributes nothing to the spec. Every
``expect="reject"`` case accordingly carries a Lean snippet that states the spec
predicate directly at one concrete input and refutes it by evaluation. Each was
built against the rival and against the frozen solution before shipping: all four
ELABORATE against their rival and all four FAIL on gold (gold's failure is
``decide`` proving the NEGATION of the witness's claim — i.e. gold satisfies the
clause at that point), so each discriminates rather than asserting a tautology.

BINDER / POINT SPREAD. The spec has one input binder, ``name``, and the four
reject witnesses probe FOUR DISTINCT points of it rather than one convenient
value: ``"Class"``, ``"Module"``, ``"Kernel"`` and ``""``. The spread is chosen
so no two rivals share a refutation point, and each point is where its own rival
is maximally wrong: a multi-character name for the report-nothing rival; a name
whose last character is the one dropped for the truncation rival; a name whose
first character alone is not the name for the first-character rival; and the
EMPTY name for the separator-glued rival — the boundary case ``mapping.md``
singles out (a stand-in created with no name must report the empty name, so a
rival that unconditionally prefixes a separator is wrong there while agreeing
with gold nowhere else it could hide). Two rivals never share a witness.

AXIOM LANE — dropped, as instructed. The nagini sibling's single ``AXIOM_TESTS``
entry re-runs its host A-reference probe; this bundle declares no ``axiom`` and no
``opaque`` callee (``meta.json``: ``axioms: []``, ``opaque_callees: []``, G-AX
recorded ``skip`` — the behavior is modeled deeply and validated by G-CONF). The
axiom lane belongs to G-AX; this gate ignores it.
"""
from pathlib import Path

INSTANCE = "sphinx-doc__sphinx-9658"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Region anchors, verbatim from the frozen Solution.lean and each unique in it
# (asserted at manifest load, so the manifest breaks LOUDLY if the frozen
# solution ever changes).
#
# _IMPL lies entirely between `-- impl-start` and `-- impl-end`; _PROOF lies
# entirely between `-- proof-start` and `-- proof-end`. Neither touches the
# spec view, so same_spec is guaranteed; _PROOF swaps keep the `theorem
# correct_mockQualifiedName` STATEMENT untouched (the anchor begins after the
# proof-introducing `:= by`), so the obligation survives byte-identically.
# ---------------------------------------------------------------------------
_IMPL = (
    "  -- the stand-in records the short name it was created with\n"
    "  let mut nameAttr := name\n"
    "  -- its qualified name is taken from that recorded short name\n"
    "  let mut qualname := nameAttr\n"
    "  return qualname\n"
)

_PROOF = (
    "  intro name\n"
    "  unfold problem_spec_mockQualifiedName implementation_mockQualifiedName\n"
    "  rfl\n"
)

assert _BASE.count(_IMPL) == 1, "impl anchor drift"
assert _BASE.count(_PROOF) == 1, "proof anchor drift"


def _impl(body):
    """The frozen solution with ONLY the impl region's body replaced."""
    return _swap(_BASE, _IMPL, body)


def _impl_proof(body, proof):
    """Replace the impl body and re-prove; the theorem statement is untouched."""
    return _swap(_swap(_BASE, _IMPL, body), _PROOF, proof)


def _witness(point):
    """State the spec predicate at one literal input and refute it there.

    Appended by the gate to a copy of the file whose proof region has been
    emptied, so no tactic script can interfere. Nothing is assumed: the goal is
    closed by evaluating a decidable string equality at a literal.
    """
    return (
        "-- Refutation at one concrete short name: the reported qualified name\n"
        "-- must BE that short name, and this implementation's is not.\n"
        f"example : ¬ problem_spec_mockQualifiedName {point}\n"
        f"    (implementation_mockQualifiedName {point}) := by\n"
        "  unfold problem_spec_mockQualifiedName implementation_mockQualifiedName\n"
        "  decide\n"
    )


SPEC_TESTS = [

    # =====================================================================
    # SOUNDNESS positives — structurally DIFFERENT but CORRECT implementations
    # that must verify. If a faithful correct implementation of the modeled
    # behavior cannot satisfy the frozen obligation, the spec is SPEC-TOO-STRONG.
    # Ports nagini's two positive controls (`pos-control-qref-reshape`,
    # `pos-control-short-reshape`), whose reshapes were a loop-index rename and a
    # folded pair of trailing concatenations; the analogues on this carrier are
    # reshapes of how the reported name is BUILT, since that is the whole of the
    # modeled computation here.
    # =====================================================================
    {
        "id": "pos-rebuild-from-characters",
        "kind": "soundness",
        "expect": "verify",
        # Take the short name apart into its characters and rebuild the reported
        # name from them. Same value at every input; the frozen tactic body still
        # closes (the round trip is definitional).
        "module": _impl(
            "  -- decompose the recorded short name and rebuild it character-wise\n"
            "  let mut chars := name.data\n"
            "  let mut qualname := String.mk chars\n"
            "  return qualname\n"
        ),
        "rationale": "a CORRECT implementation with a different executable shape: "
                     "the reported name is rebuilt from the short name's "
                     "characters instead of copied wholesale. The single clause "
                     "`result = name` still holds at every input, so it must "
                     "verify; else the identity clause is SPEC-TOO-STRONG. Proof: "
                     "the frozen tactic body is retained (the decompose/rebuild "
                     "round trip is definitional, so `rfl` closes) — no helper "
                     "lemma, no assumption token, statement byte-identical. Ports "
                     "nagini's carrier-copy positive control (`pos-control-short-"
                     "reshape`), whose loop rebuilt the identifier element-wise.",
    },
    {
        "id": "pos-forward-accumulate",
        "kind": "soundness",
        "expect": "verify",
        # Accumulate forward onto an initially-empty reported name instead of
        # binding it directly — the shape nagini's positive used for the renderer.
        "module": _impl(
            "  -- accumulate the reported name forward from an empty start\n"
            "  let mut qualname := \"\"\n"
            "  qualname := qualname ++ name\n"
            "  return qualname\n"
        ),
        "rationale": "a second CORRECT reshape on the same region, structurally "
                     "unlike the first: the reported name is accumulated forward "
                     "onto an empty start rather than bound directly. Identical "
                     "value at every input, so `result = name` holds and it must "
                     "verify. Proof: frozen tactic body retained (the empty "
                     "accumulator reduces away definitionally). Ports nagini's "
                     "`pos-control-qref-reshape`, whose reshape likewise folded "
                     "the build into a single forward concatenation.",
    },
    {
        "id": "pos-empty-case-split",
        "kind": "soundness",
        "expect": "verify",
        # A genuinely different CONTROL FLOW: split on whether the short name is
        # empty and report the right thing in each arm. Both arms agree with the
        # frozen behavior, so this is correct — but the frozen `rfl` no longer
        # closes, so the case RE-PROVES inside the proof region. This is the
        # honest way to show that a reshaped-but-correct implementation is
        # accepted for the right reason, and it is exactly the discrimination the
        # reject lane's witnesses exist to establish from the other side.
        "module": _impl_proof(
            "  -- report the recorded short name, treating the no-name stand-in\n"
            "  -- (the bare root case) as its own branch\n"
            "  let mut nameAttr := name\n"
            "  let mut qualname := \"\"\n"
            "  if nameAttr == \"\" then\n"
            "    qualname := \"\"\n"
            "  else\n"
            "    qualname := nameAttr\n"
            "  return qualname\n",
            "  intro name\n"
            "  unfold problem_spec_mockQualifiedName "
            "implementation_mockQualifiedName\n"
            "  by_cases h : name = \"\"\n"
            "  · simp [h]\n"
            "  · simp [h]\n",
        ),
        "rationale": "a CORRECT implementation with different CONTROL FLOW (a case "
                     "split on the no-name stand-in, whose arms both agree with "
                     "the frozen behavior) must verify. It is the strongest "
                     "positive in the battery because the frozen `rfl` does NOT "
                     "close for it: the obligation is genuinely re-proven by "
                     "`by_cases` on the branch condition, keeping the theorem "
                     "STATEMENT byte-identical and adding no lemma, axiom or "
                     "assumption token. If it could not be closed, the spec would "
                     "be SPEC-TOO-STRONG on implementation shape rather than on "
                     "behavior. It also demonstrates that a reject case's "
                     "rejection cannot be inferred from tactic breakage alone.",
    },

    {
        "id": "pos-loop-accumulate-characters",
        "kind": "soundness",
        "expect": "verify",
        # ADDED BY AUDIT. The three positives above are all STRAIGHT-LINE: each
        # binds the reported name with one expression the frozen `rfl` still
        # closes (or, for the case-split, with a two-arm `if` closed by
        # `by_cases`). None of them is a LOOP — yet both nagini positive controls
        # this lane ports (`pos-control-short-reshape`,
        # `pos-control-qref-reshape`) rebuilt the identifier with an indexed
        # `while` loop and carried loop invariants, and `spec_guide.md` §2 makes
        # `Id.run do` + `let mut` + `for` the PREFERRED impl shape on this
        # backend. So the shape most likely to be written by a faithful solver
        # was the one shape the positive lane never tried, and "a correct loop
        # rebuild can be proven against this identity clause" was an untested
        # assumption. It is now tested: this case accumulates the reported name
        # by pushing each character of the recorded short name in turn.
        "module": _impl_proof(
            "  -- rebuild the reported name by appending each character in turn\n"
            "  let mut nameAttr := name\n"
            "  let mut qualname := \"\"\n"
            "  for c in nameAttr.data do\n"
            "    qualname := qualname.push c\n"
            "  return qualname\n",
            "  intro name\n"
            "  unfold problem_spec_mockQualifiedName "
            "implementation_mockQualifiedName\n"
            "  have key : ∀ (l : List Char) (acc : String),\n"
            "      List.foldl (fun (b : String) (a : Char) => b.push a) acc l\n"
            "        = { data := acc.data ++ l } := by\n"
            "    intro l\n"
            "    induction l with\n"
            "    | nil => intro acc; simp\n"
            "    | cons hd tl ih =>\n"
            "      intro acc\n"
            "      rw [List.foldl_cons, ih]\n"
            "      simp [String.push]\n"
            "  simp [Id.run, key]\n"
            "  rfl\n",
        ),
        "rationale": "a CORRECT implementation in the ITERATIVE shape this "
                     "backend's guide prefers and the nagini sibling's own "
                     "positive controls used — the reported name is accumulated "
                     "character-by-character in a `for` loop over the recorded "
                     "short name — must verify. It is the only positive here "
                     "whose proof needs a genuine INDUCTION: the frozen `rfl` "
                     "cannot close a fold, so the obligation is re-proven by an "
                     "in-proof generalized accumulator identity (`have key`, "
                     "quantified over the accumulator so the induction goes "
                     "through) and then discharged. No new top-level "
                     "theorem/lemma, no axiom, no assumption token, theorem "
                     "STATEMENT byte-identical. If a loop-shaped faithful impl "
                     "could NOT be proven, the identity clause would be "
                     "SPEC-TOO-STRONG on implementation shape — the exact hole "
                     "the straight-line positives above cannot detect, since all "
                     "three are closed by definitional reduction.",
    },

    # =====================================================================
    # ADMISSIBILITY — the obligation is SATISFIABLE at the concrete input shape
    # the FAIL_TO_PASS test exercises, not merely in the abstract. The frozen
    # theorem carries NO precondition hypothesis (the modeled behavior is total,
    # so the ∀ is unguarded), so nagini's precondition-admission probe
    # (`admiss-self-call`, which established each modeled function's Requires for
    # a freshly-built F2P-shaped input) has no binder to attack here; the honest
    # analogue is to discharge the spec predicate by evaluation at that same
    # ground input alongside the frozen obligation.
    # =====================================================================
    {
        "id": "admiss-ground-f2p-instance",
        "kind": "admissibility",
        "expect": "verify",
        # Discharge the spec predicate at the F2P-shaped short name by `rfl` (a
        # `have` inside the existing tactic body), then close the frozen
        # obligation verbatim. Nothing is assumed and nothing is declared.
        "module": _impl_proof(
            _IMPL,
            "  have _ground : problem_spec_mockQualifiedName \"Class\"\n"
            "      (implementation_mockQualifiedName \"Class\") := rfl\n"
            + _PROOF,
        ),
        "rationale": "the obligation is discharged at the ground input shape the "
                     "FAIL_TO_PASS test exercises (the final dotted component of "
                     "the reference it asserts) by `rfl`, and then the frozen "
                     "obligation is closed verbatim. Must verify — else the "
                     "modeled behavior is unsatisfiable at exactly the input the "
                     "F2P observes, the analogue of PRECOND-TOO-STRONG on a "
                     "backend whose obligation has no precondition binder. "
                     "Nothing is assumed: no new declaration, the theorem "
                     "statement is byte-identical, and the impl region is the "
                     "frozen one. Ports nagini's `admiss-self-call`.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — WRONG implementations sharing the frozen
    # spec that must be rejected. Each carries (a) the refinement argument that
    # its faithful real patch would NOT resolve the FAIL_TO_PASS test, so a
    # VERIFYING rival would be a true verify-does-not-imply-resolve break rather
    # than an artifact, and (b) a refutation witness pinning the violation at one
    # concrete input — checked to hold of the rival and to FAIL on gold.
    # =====================================================================

    # ---- report nothing at all (nagini `weak-display-empty` + `weak-short-empty`)
    {
        "id": "weak-reports-nothing",
        "kind": "uniqueness",
        "expect": "reject",
        # The reported qualified name is hard-set to the empty string, ignoring
        # the short name the stand-in was created with entirely.
        "module": _impl(
            "  -- WRONG: report nothing, ignoring the recorded short name\n"
            "  let mut qualname := \"\"\n"
            "  return qualname\n"
        ),
        "refinement": "a stand-in that reports no qualified name makes the "
                      "downstream renderer join the containing module path, a "
                      "dot, and nothing — so the reference it emits ends at the "
                      "dot with its final component missing. That is precisely "
                      "the incomplete reference the issue reports ('Bases' shown "
                      "as a dotted path ending in a dot). The FAIL_TO_PASS test "
                      "asserts the COMPLETE reference, final component included, "
                      "so a faithful real patch with this behavior would NOT "
                      "resolve; a verifying rival here would therefore be a true "
                      "verify-does-not-imply-resolve break. (It is also the "
                      "behavior `Solution_prepatch.lean` carries, which G-DIFF "
                      "records as failing to verify.)",
        "rationale": "REJECT from the single clause `result = name`: the empty "
                     "string equals `name` only when `name` is itself empty, so "
                     "the clause is violated at every non-empty short name. "
                     "Witness point: the binder `name` at \"Class\" — a "
                     "multi-character name where the reported value is maximally "
                     "far from the required one (nothing versus everything). "
                     "Ports nagini's two empty-return rivals "
                     "(`weak-display-empty`, `weak-short-empty`), which attacked "
                     "the (D) and (S) clauses separately; both collapse onto this "
                     "single obligation here.",
        "witness": _witness('"Class"'),
    },

    # ---- truncated trailing component (nagini `weak-truncated-display-tail`)
    {
        "id": "weak-truncated-tail",
        "kind": "uniqueness",
        "expect": "reject",
        # The reported name drops the LAST character of the short name — correct
        # nowhere except the empty name, and a NEAR-MISS that agrees with gold on
        # every character but one, which is why it gets its own witness point.
        "module": _impl(
            "  -- WRONG: report the recorded short name with its last character\n"
            "  -- dropped\n"
            "  let mut nameAttr := name\n"
            "  let mut qualname := nameAttr.dropRight 1\n"
            "  return qualname\n"
        ),
        "refinement": "this drops the final character of the stand-in's short "
                      "name from the reported qualified name, so the renderer "
                      "emits a reference whose final component is one character "
                      "short of the symbol actually referenced. The FAIL_TO_PASS "
                      "test asserts the reference EXACTLY, character for "
                      "character, so a one-character-short final component fails "
                      "it just as an absent one does — a faithful real patch with "
                      "this behavior would NOT resolve. It is a strictly harder "
                      "rival than reporting nothing: the emitted reference is "
                      "well-formed and does not end at the dot, so nothing but "
                      "the exact-value assertion catches it.",
        "rationale": "REJECT from `result = name`: the reported name is `name` "
                     "with its last character removed, which equals `name` at no "
                     "non-empty input. NEAR-MISS relative to `weak-reports-"
                     "nothing` — it agrees with gold on every character but the "
                     "last — so it does NOT share that rival's witness; it is "
                     "refuted at its own point, the binder `name` at \"Module\", "
                     "where the dropped final character is the sole difference. "
                     "Ports nagini's `weak-truncated-display-tail`, which attacked "
                     "the exact-concatenation clause Q2 for the same reason its "
                     "length bound Q3 could not catch a one-character drop.",
        "witness": _witness('"Module"'),
    },

    # ---- only the first character (a second near-miss, from the other end)
    {
        "id": "weak-first-character-only",
        "kind": "uniqueness",
        "expect": "reject",
        # The reported name keeps only the FIRST character of the short name.
        "module": _impl(
            "  -- WRONG: report only the first character of the recorded short\n"
            "  -- name\n"
            "  let mut nameAttr := name\n"
            "  let mut qualname := nameAttr.take 1\n"
            "  return qualname\n"
        ),
        "refinement": "reporting only the leading character of the short name "
                      "makes the renderer emit a reference whose final component "
                      "is a single character rather than the symbol's name. The "
                      "FAIL_TO_PASS test asserts the full final component, so a "
                      "faithful real patch with this behavior would NOT resolve. "
                      "It is the mirror image of the truncation rival — wrong from "
                      "the tail end rather than the head — and it agrees with gold "
                      "on every one-character name, so it is a genuinely distinct "
                      "sub-domain rather than a restatement.",
        "rationale": "REJECT from `result = name`: keeping one leading character "
                     "equals `name` only when `name` has length at most one. "
                     "Refuted at its own point, the binder `name` at \"Kernel\" — "
                     "distinct from both other rivals' points, and chosen because "
                     "it is the sub-domain (length > 1) where this rival and only "
                     "this rival is wrong in this particular way. Attacks the same "
                     "single clause from the opposite end, so the battery "
                     "demonstrates the clause pins the WHOLE reported name, not "
                     "just its prefix or its suffix.",
        "witness": _witness('"Kernel"'),
    },

    # ---- separator glued onto the reported name (nagini `weak-missing-dot` /
    # ---- `weak-dangling-dot`, re-expressed on the modeled component)
    {
        "id": "weak-separator-glued",
        "kind": "uniqueness",
        "expect": "reject",
        # The reported name carries a leading separator, so the renderer's join
        # doubles it. Wrong at EVERY input, including the empty short name — the
        # boundary case where every other rival above agrees with gold.
        "module": _impl(
            "  -- WRONG: prefix the recorded short name with a separator, which\n"
            "  -- the downstream join then duplicates\n"
            "  let mut nameAttr := name\n"
            "  let mut qualname := \".\" ++ nameAttr\n"
            "  return qualname\n"
        ),
        "refinement": "the reported qualified name is the short name with a "
                      "leading separator glued on. The renderer joins the "
                      "containing module path, a separator, and the reported "
                      "name, so the emitted reference carries a DOUBLED separator "
                      "before its final component. The FAIL_TO_PASS test asserts "
                      "the reference exactly, so a faithful real patch with this "
                      "behavior would NOT resolve. (AUDIT CORRECTION: an earlier "
                      "revision of this note also claimed the PASS_TO_PASS "
                      "reference-rendering tests would fail. That is FALSE and is "
                      "withdrawn — all 24 PASS_TO_PASS tests pin references for "
                      "CONCRETE types, which never reach a stand-in's reported "
                      "qualified name, and the one PASS_TO_PASS test that does "
                      "build a stand-in already passed at base_commit, where the "
                      "reported name was empty; so it cannot read that name "
                      "either. The FAIL_TO_PASS test is the sole observer, which "
                      "is enough for the refinement argument and is all that is "
                      "claimed now.) This is nagini's separator pair "
                      "(`weak-missing-dot` / `weak-dangling-dot`) re-expressed on "
                      "the component this bundle actually models: the module path "
                      "and the join are outside the modeled output, so the only "
                      "way to attack the separator here is to corrupt the piece "
                      "the join consumes.",
        "rationale": "REJECT from `result = name`: a separator-prefixed name "
                     "differs from `name` at every input, since the two differ in "
                     "length. Refuted at the binder `name` at \"\" — the EMPTY "
                     "short name, the boundary `mapping.md` singles out (a "
                     "stand-in created with no name must report the empty name). "
                     "That point is deliberately NOT shared with any other rival: "
                     "the three rivals above all agree with gold at the empty "
                     "name, so this witness probes the one sub-domain they leave "
                     "undefended and proves the clause bites there too. Four "
                     "rivals, four distinct points of the single input binder.",
        "witness": _witness('""'),
    },
]
