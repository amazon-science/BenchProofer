"""properties.py — G-PBT falsification battery for scikit-learn__scikit-learn-14087 (lean).

NOT a Lean file; a manifest the G-PBT gate executes. Each SPEC case is a full
``Solution.lean`` variant that shares the FROZEN spec byte-for-byte (region
surgery: only text strictly inside a ``-- impl-start`` / ``-- impl-end`` region —
and, for a case that legitimately re-proves, inside a ``-- proof-start`` /
``-- proof-end`` region — is changed, so ``markers.same_spec`` holds by
construction and every ``theorem correct_*`` STATEMENT stays byte-identical).
``expect="verify"`` passes iff the variant elaborates with both obligations closed
(no ``sorry``/``admit``/``native_decide``, no new ``axiom``/``theorem``/``lemma``);
``expect="reject"`` passes iff the variant does NOT verify AND the case's
``witness`` holds of the rival while FAILING on the frozen solution.

DEFENDED SURFACE — TWO obligations over fully decidable finite/exact carriers:

  problem_spec_chooseLayout (req : ReqStrategy) (eff : EffStrategy)
                            (result : AggLayout) : Prop
    (eff = EffStrategy.perClass → result = AggLayout.perClassLayout)
  ∧ (eff = EffStrategy.joint    → result = AggLayout.jointLayout)

  problem_spec_ratioEntry (combinedPenalty : Bool) (ratio : ℚ)
                          (result : Option ℚ) : Prop
    (combinedPenalty = true  → result = some ratio)
  ∧ (combinedPenalty = false → result = none)

Neither obligation carries a precondition hypothesis: the ``∀`` in each
``theorem correct_*`` is unguarded, so every combination of the binders is
admissible. The ``axioms`` region is EMPTY — both post-images are constructors
determined by the obligation's own arguments, so there is no opaque answer key a
rival could ECHO (spec_guide directive 8 is satisfied structurally) and every
witness below computes under ``decide`` at literal inputs. No carrier
conditioning is needed anywhere, so no witness binds anything and no consistency
probe applies.

FOUR INDEPENDENT top-level clauses, and the independence is what a thin battery
would miss:

  * chooseLayout CLAUSE 1 — ``eff = perClass → result = perClassLayout``.
  * chooseLayout CLAUSE 2 — ``eff = joint → result = jointLayout``.
    Together they pin the selection to the EFFECTIVE strategy and to nothing
    else. ``req`` is deliberately absent from the relation: that absence is the
    load-bearing content (two runs at the same ``eff`` must select the same
    layout however the strategy was originally requested), so a rival that
    consults ``req`` is refuted even though it agrees with gold wherever the two
    operands happen to coincide.
  * ratioEntry CLAUSE 1 — ``combinedPenalty = true → result = some ratio``. Pins
    BOTH presence AND the value: the entry must be the PREPARED quantity, not
    merely some number of the right type.
  * ratioEntry CLAUSE 2 — ``combinedPenalty = false → result = none``. The entry
    is absent outside the regime; no value may be synthesized from a quantity
    that does not apply there.

The two obligations share no binder, and within ``ratioEntry`` clause 1's value
half is separable from its presence half. A battery attacking only presence would
leave a rival that always records a fixed number entirely undetected, which is why
``weak-ratio-wrong-quantity`` exists (see its refinement note — it is the one case
whose defect the listed tests do not observe, and that is stated rather than
papered over).

ADVERSARIAL READ of the nagini classes on this carrier (case-by-case ledger in the
footer):

  * PARTIAL-DOMAIN — the sibling's central class, heavily exercised. Each layout
    rival is correct on part of the domain and diverges exactly where the two
    strategy operands disagree, or on one layout only.
  * UNFORGEABLE-CAPABILITY / RANK FORGERY — NO COUNTERPART, and for a reason that
    strengthens rather than weakens this surface. The sibling models the ACCESS:
    its value clause is echoable by returning the value argument with no access
    performed, so it needs a rank-indexed capability token to pin the control-flow
    effect the value abstraction drops. This bundle models no access, no arity and
    no capability — it models the SELECTION BETWEEN two aggregation layouts that
    surrounding unchanged code prepares. The discriminating content is therefore a
    relation between the result and the obligation's own arguments, and every
    wrong-layout choice the three ``forge-rank`` rivals make is refuted directly
    by clause 1 or clause 2 with no token machinery. There is no rank argument to
    forge; inventing one would mean inventing a modeled quantity the spec does not
    have.
  * VALUE-SUBSTITUTION — ported (``weak-ratio-wrong-quantity``).
  * INVERTED-BRANCH — ported (``weak-ratio-inverted-guard``).
  * FRAME / PERMISSION MUTATION — VACUOUS, exactly as the sibling itself records
    it. The sibling states this class is inapplicable on its OWN carrier (every
    parameter is an immutable by-value scalar/option, with no reference held at
    partial permission to overwrite). Here a fortiori: Lean is referentially
    transparent, there is no heap, no aliasing, and no ``mut`` binder in any
    signature. No substitute probe is fabricated.
  * DIVERGENCE / NON-TERMINATION — GENUINELY VACUOUS on this backend, and this is
    the one disposition that differs from the velvet sibling of this same
    instance. The nagini battery carries ``rival-diverge-loop`` and closes the
    class with an explicit totality obligation, because under partial correctness
    a never-returning body discharges every postcondition vacuously. On velvet
    that survives as a real spec hole (``the corpus-wide termination-semantics finding``: under
    ``set_option loom.semantics.termination "partial"`` a diverging impl verifies,
    while its faithful counterpart hangs and resolves nothing — measured, 401
    ``partial`` bundles admit it and 99 ``total`` bundles reject it). On lean it
    does NOT — but NOT for the reason a first reading suggests, and the corrected
    reason was measured rather than argued. It is NOT true that a diverging
    implementation "cannot be written": rewriting the second impl as a
    self-recursive ``partial def`` COMPILES cleanly (``Option ℚ`` is inhabited, so
    Lean accepts the ``partial`` keyword), and only the OBLIGATION then fails,
    with ``unfold failed to unfold implementation_ratioEntry``. What closes the
    class here is that Lean's ``partial`` is implemented as an OPAQUE constant
    backed by an inhabitance witness, not as an assumption that the postcondition
    holds vacuously: the diverging body is rejected because nothing can be proven
    ABOUT it, whereas velvet's ``partial`` weakens the CLAIM to terminating runs
    and so discharges it. (The first impl does not even reach that point:
    ``AggLayout`` carries no ``Inhabited`` instance, so ``partial def`` is refused
    outright — "could not prove that the type ... is nonempty".) Either way there
    is no rival to ship, because a diverging impl is REJECTED on lean rather than
    accepted; the disposition is unchanged and only the stated mechanism is
    corrected. Vacuous here, a known hole there.

WITNESS MECHANICS. On a tactic-proof backend "did not verify" is the DEFAULT
outcome of reshaping an impl — the frozen ``refine ⟨…⟩ <;> subst he <;> rfl`` is
tuned to the frozen do-block's syntactic form — so a rejection alone attributes
nothing to the spec. Every ``expect="reject"`` case therefore carries a Lean
snippet proving the rival CONTRADICTS the spec at ONE concrete literal input,
checked in a file whose frozen ``proof`` regions the gate has emptied so no tactic
script can mask the verdict. All six were checked out-of-band with real
``scripts/lean_verify.sh`` builds: each ELABORATES against its own rival (exit 0)
and FAILS against the frozen solution (exit 1, ``decide`` reporting the negated
proposition false), so each discriminates rather than asserting a tautology. No
witness uses ``sorry``/``admit``/``native_decide``, and no obligation has a
precondition that could vacuously exclude a witness input.

Every witness point is also a REACHABLE configuration of the real routine, not
merely an admissible point of the model: ``(autoStrategy, perClass)`` is the
deferred-request-resolving-to-per-class configuration named in the public issue
reproduction, ``(perClass, perClass)`` and ``(joint, joint)`` are the two
concrete-request configurations, and both ``combinedPenalty`` values occur.

INDEPENDENT AUDIT (post-port, real builds). Every case was re-derived rather than
trusted. All six reject witnesses were rebuilt against their own rival and against
the frozen solution: rival exit 0 / gold exit 1 in all six, and each gold-side
failure is a SEMANTIC refutation (``Tactic `decide` proved that the proposition ...
is false``, reducing the frozen impl at the literal point) rather than a missing
identifier, a type error, or a stuck ``decide`` — so all six discriminate. The
admissibility asserts were confirmed LIVE by falsifying three of them
independently (each then fails with ``decide`` reporting the altered proposition
false). Four NEW wrong impls the battery did not contain were tried as
SPEC-TOO-WEAK probes — a layout keyed to the disjunction ``eff = perClass ∨ req =
perClass``, a layout keyed only to the deferred request, an entry recording
``some 0`` outside the regime, and an entry recording the negated quantity inside
it — and all four were REJECTED. Four NEW correct reshapes were tried as
SPEC-TOO-STRONG probes and all four VERIFY: ``bif`` over ``BEq`` plus
``List.head?``, an exhaustive 6-way ``match`` on BOTH binders, ``some (ratio * 1 +
0)``, and the raw ``Bool.rec`` eliminator. No spec hole in either direction was
found, which is what the ``have huniq`` in the admissibility case now explains
structurally: both relations are provably UNIQUE-VALUED at every input, so
SPEC-TOO-WEAK is closed by proof and not merely by the rival sample.

AXIOM lane: EMPTY. ``meta.json`` declares no axioms and no deep-model references
(both decisions consume only values that unchanged surrounding code prepares), so
there is nothing for an axiom probe to falsify — and this gate ignores
``AXIOM_TESTS`` regardless. The sibling's three axiom cases are dropped.
"""
from pathlib import Path

INSTANCE = "scikit-learn__scikit-learn-14087"
BACKEND = "lean"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Region anchors. Each lies ENTIRELY inside the region it names and is unique in
# the frozen file (asserted by `_swap` at import, so any drift in Solution.lean
# breaks this manifest loudly instead of silently mis-targeting a swap).
# ---------------------------------------------------------------------------

# The two impl bodies: a mutable do-block that picks the post-image by branching
# on the decision's own governing input.
_IMPL_LAYOUT = (
    "  let mut layout := AggLayout.jointLayout\n"
    "  if eff = EffStrategy.perClass then\n"
    "    layout := AggLayout.perClassLayout\n"
    "  else\n"
    "    layout := AggLayout.jointLayout\n"
    "  return layout")
_IMPL_RATIO = (
    "  let mut entry : Option ℚ := none\n"
    "  if combinedPenalty then\n"
    "    entry := some ratio\n"
    "  else\n"
    "    entry := none\n"
    "  return entry")

# The declaration heads, so a variant may drop the `Id.run do` shape entirely.
# Both sit inside their impl region together with the body above.
_DEF_LAYOUT = ("def implementation_chooseLayout\n"
               "    (req : ReqStrategy) (eff : EffStrategy) : AggLayout := "
               "Id.run do\n")
_DEF_RATIO = ("def implementation_ratioEntry\n"
              "    (combinedPenalty : Bool) (ratio : ℚ) : Option ℚ := "
              "Id.run do\n")

# The frozen tactic bodies (each wholly inside a `-- proof-start`/`-- proof-end`
# region). Only a positive that legitimately re-proves touches these; every
# reject rival leaves both frozen and is judged by its witness.
_PROOF_LAYOUT = (
    "  intro req eff\n"
    "  unfold problem_spec_chooseLayout implementation_chooseLayout\n"
    "  simp only [Id.run]\n"
    "  refine ⟨fun he => ?_, fun he => ?_⟩ <;> subst he <;> rfl")
_PROOF_RATIO = (
    "  intro combinedPenalty ratio\n"
    "  unfold problem_spec_ratioEntry implementation_ratioEntry\n"
    "  refine ⟨fun hc => ?_, fun hc => ?_⟩ <;>\n"
    "    simp only [hc] <;> rfl")


def _layout(body):
    """Reshape ONLY the first decision's impl; everything else stays frozen."""
    return _swap(_BASE, _IMPL_LAYOUT, body)


def _ratio(body):
    """Reshape ONLY the second decision's impl; everything else stays frozen."""
    return _swap(_BASE, _IMPL_RATIO, body)


# ---- witness scaffold -------------------------------------------------------
# Both carriers are decidable at literal inputs (two finite inductives; `Bool`
# and exact `ℚ`), so a witness states the spec predicate directly at one concrete
# point and closes by `decide` — no opaque term, hence no conditioning and no
# binders to be jointly satisfiable.

def _wit_layout(req, eff):
    args = f"ReqStrategy.{req} EffStrategy.{eff}"
    return (f"example : ¬ problem_spec_chooseLayout {args}\n"
            f"    (implementation_chooseLayout {args}) := by\n"
            f"  unfold problem_spec_chooseLayout implementation_chooseLayout\n"
            f"  decide\n")


def _wit_ratio(combined, ratio):
    args = f"{combined} ({ratio} : ℚ)"
    return (f"example : ¬ problem_spec_ratioEntry {args}\n"
            f"    (implementation_ratioEntry {args}) := by\n"
            f"  unfold problem_spec_ratioEntry implementation_ratioEntry\n"
            f"  decide\n")


SPEC_TESTS = [
    # =======================================================================
    # POSITIVE CONTROLS — structurally different but CORRECT implementations
    # that MUST verify, else SPEC-TOO-STRONG. Each keeps both `theorem
    # correct_*` statements byte-identical and adds no axiom/lemma. Both
    # positives reshape BOTH impls, so both obligations are defended twice.
    # =======================================================================
    {
        "id": "pos-complement-test-and-guard-only",
        "kind": "soundness",
        "expect": "verify",
        # Decision 1: branch on the COMPLEMENTARY test (`= joint`) with the
        # per-class post-image as the default — provably the same function,
        # since the effective-strategy carrier has exactly two constructors.
        # Decision 2: initialise to the absent entry and override ONLY inside
        # the regime, dropping the else-arm. The frozen proofs still close both
        # (measured with a real build), so no proof authoring is involved and
        # the case cannot pass by a retuned tactic accident.
        "module": _swap(
            _swap(_BASE, _IMPL_LAYOUT,
                  "  let mut layout := AggLayout.perClassLayout\n"
                  "  if eff = EffStrategy.joint then\n"
                  "    layout := AggLayout.jointLayout\n"
                  "  else\n"
                  "    layout := AggLayout.perClassLayout\n"
                  "  return layout"),
            _IMPL_RATIO,
            "  let mut entry : Option ℚ := none\n"
            "  if combinedPenalty then\n"
            "    entry := some ratio\n"
            "  return entry"),
        "rationale": "structurally different CORRECT reshape of BOTH impls. "
                     "chooseLayout branches on the complementary test `eff = "
                     "EffStrategy.joint` with AggLayout.perClassLayout as the "
                     "default: EffStrategy has exactly two constructors, so this "
                     "is the same function of `eff` and both clauses (eff = "
                     "EffStrategy.perClass → result = AggLayout.perClassLayout, "
                     "eff = EffStrategy.joint → result = AggLayout.jointLayout) "
                     "still hold. ratioEntry initialises to the absent entry and "
                     "overrides only inside the regime, dropping the else-arm — "
                     "identical result on both Bool values. It MUST verify, else "
                     "SPEC-TOO-STRONG (the spec would be over-fit to one way of "
                     "writing each branch). The FROZEN proofs close it unchanged, "
                     "so the pass cannot come from a retuned tactic.",
    },
    {
        "id": "pos-total-functional-shape",
        "kind": "soundness",
        "expect": "verify",
        # A different KIND of reshape: abandon the imperative `Id.run do` shape
        # altogether. Decision 1 becomes an exhaustive `match` on the effective
        # strategy; decision 2 becomes a single `cond` application. Both proofs
        # are retuned inside the elided proof regions (the frozen `simp only
        # [Id.run]` no longer applies once there is no `Id.run`), with the
        # theorem STATEMENTS untouched and no new lemma. Verified by a real build.
        "module": _swap(
            _swap(
                _swap(
                    _swap(_BASE, _DEF_LAYOUT + _IMPL_LAYOUT,
                          "def implementation_chooseLayout\n"
                          "    (req : ReqStrategy) (eff : EffStrategy)"
                          " : AggLayout :=\n"
                          "  match eff with\n"
                          "  | EffStrategy.perClass => AggLayout.perClassLayout\n"
                          "  | EffStrategy.joint => AggLayout.jointLayout"),
                    _DEF_RATIO + _IMPL_RATIO,
                    "def implementation_ratioEntry\n"
                    "    (combinedPenalty : Bool) (ratio : ℚ) : Option ℚ :=\n"
                    "  cond combinedPenalty (some ratio) none"),
                _PROOF_LAYOUT,
                "  intro req eff\n"
                "  unfold problem_spec_chooseLayout implementation_chooseLayout\n"
                "  refine ⟨fun he => ?_, fun he => ?_⟩ <;> subst he <;> rfl"),
            _PROOF_RATIO,
            "  intro combinedPenalty ratio\n"
            "  unfold problem_spec_ratioEntry implementation_ratioEntry\n"
            "  refine ⟨fun hc => ?_, fun hc => ?_⟩ <;> subst hc <;> rfl"),
        "rationale": "a different KIND of correct reshape: both impls drop the "
                     "imperative mutable-slot shape entirely — chooseLayout "
                     "becomes an exhaustive match on `eff`, ratioEntry a single "
                     "`cond` on `combinedPenalty`. Extensionally identical on "
                     "every input, so all four clauses hold and it MUST verify, "
                     "else SPEC-TOO-STRONG (the spec would be pinned to the "
                     "imperative encoding rather than to the behaviour). Both "
                     "proofs are honestly retuned inside the proof regions "
                     "(`subst` + `rfl`, no new lemma, no assumption token); both "
                     "theorem statements are byte-identical.",
    },
    {
        "id": "admiss-both-decisions-reachable-and-separating",
        "kind": "admissibility",
        "expect": "verify",
        # Re-aimed from the sibling's arity-establishability assert. Neither
        # obligation here has a precondition, so "the precondition admits an
        # F2P-shaped input" is trivially true and the residual risk is instead
        # DEGENERACY: a relation whose two arms coincide, or which is satisfied
        # without the governing input mattering, would be hollow. Each `have`
        # is discharged by `decide` inside the proof region and each is LIVE:
        # falsifying any one of them fails the build (checked out-of-band —
        # `decide proved that the proposition ... is false`).
        "module": _swap(
            _swap(_BASE, _PROOF_LAYOUT,
                  "  -- STRONGEST form of the non-degeneracy claim, added by audit:\n"
                  "  -- the relation admits EXACTLY ONE result at EVERY input, so no\n"
                  "  -- rival can satisfy this obligation while differing from the\n"
                  "  -- frozen impl anywhere. This is a universal statement, not a\n"
                  "  -- per-point spot-check, and it is what rules out SPEC-TOO-WEAK\n"
                  "  -- for this obligation outright rather than one rival at a time.\n"
                  "  have huniq : ∀ (r : ReqStrategy) (e : EffStrategy)\n"
                  "      (out : AggLayout), problem_spec_chooseLayout r e out\n"
                  "      → out = implementation_chooseLayout r e := by\n"
                  "    intro r e out hout\n"
                  "    obtain ⟨h1, h2⟩ := hout\n"
                  "    cases e\n"
                  "    · simp [implementation_chooseLayout, h1 rfl]\n"
                  "    · simp [implementation_chooseLayout, h2 rfl]\n"
                  "  -- Both post-images are actually REACHED, they are DISTINCT,\n"
                  "  -- and the merely-requested operand does not move the\n"
                  "  -- decision at a fixed effective strategy.\n"
                  "  have hdistinct : AggLayout.perClassLayout"
                  " ≠ AggLayout.jointLayout := by decide\n"
                  "  have hdeferred : implementation_chooseLayout"
                  " ReqStrategy.autoStrategy\n"
                  "      EffStrategy.perClass = AggLayout.perClassLayout :="
                  " by decide\n"
                  "  have hjoint : implementation_chooseLayout"
                  " ReqStrategy.autoStrategy\n"
                  "      EffStrategy.joint = AggLayout.jointLayout := by decide\n"
                  "  have hreqfree : implementation_chooseLayout"
                  " ReqStrategy.joint\n"
                  "      EffStrategy.perClass\n"
                  "      = implementation_chooseLayout ReqStrategy.perClass\n"
                  "      EffStrategy.perClass := by decide\n"
                  + _PROOF_LAYOUT),
            _PROOF_RATIO,
            "  -- Same universal uniqueness for the second obligation, VALUE half\n"
            "  -- included: any satisfying entry equals the frozen one, so a\n"
            "  -- wrong-quantity rival cannot satisfy this relation at all.\n"
            "  have huniq : ∀ (c : Bool) (q : ℚ) (out : Option ℚ),\n"
            "      problem_spec_ratioEntry c q out\n"
            "      → out = implementation_ratioEntry c q := by\n"
            "    intro c q out hout\n"
            "    obtain ⟨h1, h2⟩ := hout\n"
            "    cases c\n"
            "    · simp [implementation_ratioEntry, h2 rfl]\n"
            "    · simp [implementation_ratioEntry, h1 rfl]\n"
            "  -- Both post-images are reached and are DISTINGUISHABLE at a\n"
            "  -- nonzero prepared quantity, so neither arm is degenerate.\n"
            "  have hoff : implementation_ratioEntry false (3 : ℚ) = none :="
            " by decide\n"
            "  have hon : implementation_ratioEntry true (3 : ℚ)"
            " = some (3 : ℚ) := by decide\n"
            "  have hsep : (some (3 : ℚ)) ≠ (none : Option ℚ) := by decide\n"
            + _PROOF_RATIO),
        "rationale": "re-aimed admissibility, STRENGTHENED by audit. Neither "
                     "`theorem correct_*` carries a precondition hypothesis (both "
                     "∀s are unguarded), so admission of an input is trivial and "
                     "the real risk is DEGENERACY of the relations. The leading "
                     "`have huniq` in each proof region now discharges the "
                     "strongest available form of that check: for EVERY input, any "
                     "result satisfying the relation EQUALS the one the frozen impl "
                     "produces (`problem_spec_* args out → out = implementation_* "
                     "args`). That is a universal uniqueness proof, so it settles "
                     "SPEC-TOO-WEAK for both obligations outright rather than one "
                     "rival at a time — no impl can satisfy either relation while "
                     "differing from gold at any input, value half of the "
                     "mixing-ratio clause included. Both are closed by `cases` on "
                     "the governing binder plus the relation's own two clauses, "
                     "with no new lemma and no axiom, and both theorem statements "
                     "stay byte-identical. The remaining `have`s pin, for both "
                     "obligations, that each arm's post-image is actually reached, "
                     "that the two post-images DIFFER (AggLayout.perClassLayout ≠ "
                     "AggLayout.jointLayout; some ratio ≠ none), and that at a "
                     "fixed effective strategy the merely-requested operand does "
                     "not move the result — including at the deferred request, the "
                     "configuration the public issue reproduction exercises. All "
                     "are discharged by `decide` alongside the frozen proofs. Each "
                     "is LIVE: falsifying any one fails the build, so this is not "
                     "a decorative assert. If they could not be discharged the "
                     "relations would be admitting nothing meaningful => "
                     "PRECOND-TOO-STRONG / degenerate spec.",
    },

    # =======================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected. Each carries a machine-checked refutation witness
    # at one concrete literal input, plus the refinement argument for its
    # faithful real counterpart. Three rivals per obligation.
    # =======================================================================
    {
        "id": "weak-layout-from-requested-operand",
        "kind": "uniqueness",
        "expect": "reject",
        # THE reported defect: drive the selection off the merely-REQUESTED
        # operand instead of the effective one. Correct wherever the two
        # coincide, wrong exactly where the request is the unresolved
        # placeholder and the effective strategy is the per-class one.
        "module": _layout(
            "  let mut layout := AggLayout.jointLayout\n"
            "  if req = ReqStrategy.perClass then\n"
            "    layout := AggLayout.perClassLayout\n"
            "  else\n"
            "    layout := AggLayout.jointLayout\n"
            "  return layout"),
        "refinement": "its faithful counterpart is the reported defect itself: the "
                      "selection consults the raw requested setting, so whenever "
                      "the request is the unresolved placeholder but the effective "
                      "strategy is the per-class one, the aggregation addresses the "
                      "prepared table with the wrong number of leading axes and "
                      "raises the indexing failure quoted in the public issue "
                      "reproduction — the reported defect is simply not fixed. "
                      "HONEST CAVEAT, stated rather than papered over: the three "
                      "listed newly-passing configurations all resolve the "
                      "deferred request to the JOINT strategy (they are "
                      "multi-class on a solver that resolves that way), and for a "
                      "concrete request the two operands coincide — so those three "
                      "configurations do NOT by themselves discriminate this rival, "
                      "and its counterpart would still pass them once the second "
                      "decision is fixed. What refutes it is the spec clause plus "
                      "the issue's own reproduction (a binary problem, or a solver "
                      "that forces the per-class strategy), which is the "
                      "configuration this rival breaks and the whole reason the "
                      "selection was moved onto the effective operand. Verified by "
                      "reading the resolution rule and the prepared-table ranks, "
                      "not assumed from the sibling battery, which asserts the "
                      "stronger F2P claim.",
        "rationale": "REJECT from clause 1 (eff = EffStrategy.perClass → result = "
                     "AggLayout.perClassLayout). `req` is deliberately absent from "
                     "the relation — the result must not depend on it — so a rival "
                     "keyed to `req` is refuted at any point where the two "
                     "operands disagree. Refuted at (req = ReqStrategy."
                     "autoStrategy, eff = EffStrategy.perClass): the spec demands "
                     "AggLayout.perClassLayout, the rival yields AggLayout."
                     "jointLayout. This is the only witness that moves `req` off a "
                     "value matching `eff`, so it is what makes the `req`-freedom "
                     "of the relation load-bearing. If it verified => "
                     "SPEC-TOO-WEAK (the relation would not actually pin the "
                     "selection to the effective operand).",
        "witness": _wit_layout("autoStrategy", "perClass"),
    },
    {
        "id": "weak-layout-always-joint",
        "kind": "uniqueness",
        "expect": "reject",
        # Hardcode the joint post-image for every input: internally consistent,
        # wrong on the per-class layout.
        "module": _layout(
            "  let mut layout := AggLayout.jointLayout\n"
            "  return layout"),
        "refinement": "its faithful counterpart unconditionally aggregates with "
                      "the extra leading axis. On the per-class configuration the "
                      "prepared per-class table has one axis fewer than the index "
                      "expression supplies, so the aggregation raises the same "
                      "indexing failure the issue reports and the per-class "
                      "newly-passing configuration FAILS outright. It does NOT "
                      "resolve.",
        "rationale": "REJECT from clause 1 (eff = EffStrategy.perClass → result = "
                     "AggLayout.perClassLayout): the rival returns AggLayout."
                     "jointLayout on every input, so clause 1 fails while clause 2 "
                     "holds — a partial-domain rival correct only on the joint "
                     "layout. Refuted at (req = ReqStrategy.perClass, eff = "
                     "EffStrategy.perClass), a point where the two operands AGREE, "
                     "so it isolates the wrong-post-image defect from the "
                     "wrong-operand defect that weak-layout-from-requested-operand "
                     "attacks. If it verified => SPEC-TOO-WEAK. Carries the "
                     "adversarial content of the sibling's joint-layout rank "
                     "forgery on a carrier with no rank to forge.",
        "witness": _wit_layout("perClass", "perClass"),
    },
    {
        "id": "weak-layout-always-per-class",
        "kind": "uniqueness",
        "expect": "reject",
        # The mirror hardcode: correct on the per-class layout, wrong on the
        # joint one. Attacks the OTHER clause.
        "module": _layout(
            "  let mut layout := AggLayout.perClassLayout\n"
            "  return layout"),
        "refinement": "its faithful counterpart always aggregates with the "
                      "per-class index expression. On the joint configuration that "
                      "under-addresses the prepared table (it drops the leading "
                      "axis), so the aggregate has the wrong rank and the "
                      "committed per-class output attribute comes out mis-shaped — "
                      "the joint newly-passing configuration asserts that "
                      "attribute's shape and FAILS. It does NOT resolve.",
        "rationale": "REJECT from clause 2 (eff = EffStrategy.joint → result = "
                     "AggLayout.jointLayout): the rival returns AggLayout."
                     "perClassLayout on every input, satisfying clause 1 and "
                     "violating clause 2. This is the case that attacks the SECOND "
                     "clause of chooseLayout — without it a rival that mishandled "
                     "only the joint strategy would go unnoticed. Refuted at (req "
                     "= ReqStrategy.joint, eff = EffStrategy.joint), which also "
                     "moves BOTH binders to their remaining values. If it verified "
                     "=> SPEC-TOO-WEAK. Carries the content of the sibling's "
                     "independent-layout rank forgery.",
        "witness": _wit_layout("joint", "joint"),
    },
    {
        "id": "weak-ratio-unconditional",
        "kind": "uniqueness",
        "expect": "reject",
        # The pre-patch shape of the second decision: record the prepared
        # quantity with no guard at all.
        "module": _ratio(
            "  let mut entry : Option ℚ := none\n"
            "  entry := some ratio\n"
            "  return entry"),
        "refinement": "its faithful counterpart records the aggregated quantity "
                      "unguarded. Outside the combined-penalty regime the "
                      "candidate table upstream is a degenerate one-element "
                      "placeholder carrying no real quantity, so the unguarded "
                      "aggregation is performed against that placeholder and the "
                      "summarisation raises before the per-class attribute is ever "
                      "built. This is precisely the pre-patch behaviour, and it is "
                      "what all three listed newly-passing configurations trip "
                      "over: they are the non-combined-penalty ones. It does NOT "
                      "resolve.",
        "rationale": "REJECT from clause 2 (combinedPenalty = false → result = "
                     "none): the rival returns `some ratio` on every input, so it "
                     "satisfies clause 1 and violates clause 2 — the absent-entry "
                     "arm is exactly what it drops. Refuted at (combinedPenalty = "
                     "false, ratio = 3): the spec demands `none`, the rival yields "
                     "`some 3`. If it verified => SPEC-TOO-WEAK (the "
                     "absent-entry clause would be hollow).",
        "witness": _wit_ratio("false", "3"),
    },
    {
        "id": "weak-ratio-wrong-quantity",
        "kind": "uniqueness",
        "expect": "reject",
        # Value-substitution: get the PRESENCE decision exactly right, but
        # record a fixed stand-in instead of the prepared quantity. This is the
        # only rival that makes the `ratio` binder load-bearing — the other two
        # ratio rivals are refuted for ANY value of it.
        "module": _ratio(
            "  let mut entry : Option ℚ := none\n"
            "  if combinedPenalty then\n"
            "    entry := some 0\n"
            "  else\n"
            "    entry := none\n"
            "  return entry"),
        "refinement": "its faithful counterpart gets the presence/absence decision "
                      "exactly right and records a fixed constant in place of the "
                      "aggregated quantity, so the per-class summary attribute "
                      "silently reports a hyper-parameter the search never chose. "
                      "HONEST ACCOUNTING, and this is the ONE case in this battery "
                      "for which the verify-does-not-imply-resolve claim is NOT "
                      "established: the listed configurations assert that "
                      "attribute's SHAPE and presence, and the one test that "
                      "compares its VALUE against an independent search runs in "
                      "the refit mode, which is a different code path from the "
                      "modelled one. A constant of the right type keeps every "
                      "listed assertion satisfied, so this rival's counterpart "
                      "would very likely still resolve. It is shipped anyway, and "
                      "labelled, because the spec's value half is CORRECTLY "
                      "stronger than the listed tests — the recorded entry is a "
                      "documented output attribute reporting the chosen mixing "
                      "quantity, and reporting a constant instead is a real defect "
                      "— and because without it no rival would exercise the `ratio` "
                      "binder at all (see the rationale).",
        "rationale": "REJECT from the VALUE half of clause 1 (combinedPenalty = "
                     "true → result = some ratio): the rival's entry is present "
                     "and well-typed but is not the prepared `ratio`. This is the "
                     "only case that makes `ratio` load-bearing — "
                     "weak-ratio-unconditional and weak-ratio-inverted-guard are "
                     "both refuted for EVERY value of `ratio`, so without this "
                     "rival a rewrite that ignored `ratio` entirely and always "
                     "recorded a fixed number would satisfy every other witness "
                     "and the battery would never notice. Refuted at "
                     "(combinedPenalty = true, ratio = 7), a point chosen away "
                     "from the stand-in constant so the two disagree: the spec "
                     "demands `some 7`, the rival yields `some 0`. If it verified "
                     "=> SPEC-TOO-WEAK (the value half would be ungrounded and "
                     "only presence would be pinned).",
        "witness": _wit_ratio("true", "7"),
    },
    {
        "id": "weak-ratio-inverted-guard",
        "kind": "uniqueness",
        "expect": "reject",
        # Both arms swapped: absent inside the regime, present outside it.
        # Wrong on every input; given its OWN witness on the regime-ON arm,
        # where weak-ratio-unconditional is correct, so its rationale does not
        # claim a sub-domain the manifest never demonstrates.
        "module": _ratio(
            "  let mut entry : Option ℚ := none\n"
            "  if combinedPenalty then\n"
            "    entry := none\n"
            "  else\n"
            "    entry := some ratio\n"
            "  return entry"),
        "refinement": "its faithful counterpart inverts the guard, leaving the "
                      "summary entry absent precisely in the regime where the "
                      "quantity is meaningful and computing it from the degenerate "
                      "placeholder table in every other regime. So BOTH regimes "
                      "record the wrong entry: outside the regime it reproduces "
                      "the pre-patch failure the listed newly-passing "
                      "configurations trip over, and inside it the attribute is "
                      "built from absent entries and mis-shapes the "
                      "already-passing combined-penalty configurations. It does "
                      "NOT resolve.",
        "rationale": "REJECT from BOTH ratioEntry clauses — `none` where `some "
                     "ratio` is required and conversely — so it disagrees with the "
                     "post-image at every input. Given its OWN witness rather than "
                     "sharing weak-ratio-unconditional's: on the regime-OFF arm it "
                     "fails for the same reason as that rival, but on the "
                     "regime-ON arm, where that rival is CORRECT, only this one is "
                     "wrong, so the witness is placed there (combinedPenalty = "
                     "true, ratio = 5: the spec demands `some 5`, the rival yields "
                     "`none`). If it verified => SPEC-TOO-WEAK.",
        "witness": _wit_ratio("true", "5"),
    },
]


# ---------------------------------------------------------------------------
# NAGINI -> LEAN ACCOUNTING
#
# The sibling battery has 12 SPEC cases (2 soundness, 1 admissibility, 9
# uniqueness) plus a 3-case AXIOM lane, over TWO contracted functions. This
# bundle also carries TWO obligations modelling the SAME two decisions — so the
# narrowing here is not in the number of behaviours but in their DEPTH: the
# sibling's first site models the ACCESS (an echoable value plus a rank-indexed
# read capability), whereas this bundle models the SELECTION between two
# aggregation layouts that unchanged surrounding code prepares. That dissolves
# the sibling's whole capability apparatus (4 cases) into two value-level
# clauses, which is why the port is 9 cases rather than 12 — carrier narrowing,
# not thinning.
#
#   sibling case                      -> here                            disposition
#   ------------------------------------------------------------------------------
#   pos-control-site1-branch-reshape  -> pos-complement-test-and-guard-only  PORTED (merged)
#   pos-control-site2-init-override   -> pos-complement-test-and-guard-only  PORTED (merged)
#   (no sibling)                      -> pos-total-functional-shape          ADDED
#   admiss-site1-arity-establishable  -> admiss-both-decisions-reachable-... PORTED (re-aimed)
#   rival-echo-no-read                -> weak-ratio-wrong-quantity           PORTED (re-expressed)
#   rival-unresolved-operand          -> weak-layout-from-requested-operand  PORTED (caveated)
#   rival-hardcode-independent        -> weak-layout-always-per-class        PORTED
#   rival-forge-rank-joint            -> weak-layout-always-joint            RE-EXPRESSED
#   rival-forge-rank-independent      -> (folded into always-per-class)      RE-EXPRESSED
#   rival-forge-rank-unresolved       -> (folded into from-requested-operand) RE-EXPRESSED
#   rival-diverge-loop                -> (none)                              VACUOUS (lean)
#   rival-site2-always-value          -> weak-ratio-unconditional            PORTED
#   rival-site2-wrong-value           -> weak-ratio-wrong-quantity           PORTED
#   rival-site2-inverted              -> weak-ratio-inverted-guard           PORTED
#   frame-mutation (sibling: N/A)     -> (none)                              VACUOUS
#   AXIOM_TESTS (3)                   -> (none)                              DROPPED (G-AX)
#
# PORTED (positives, MERGED): the sibling's two positives reshape one site each
#   (its first site's branch test rewritten as an equivalent comparison, its
#   second site's if/else rewritten as init-then-override). Both arguments apply
#   here, and pos-complement-test-and-guard-only carries both at once — the
#   FROZEN proofs close it unchanged, so it cannot pass by a tactic accident.
# ADDED (pos-total-functional-shape): the merge would otherwise leave a single
#   positive. This one is a different KIND of reshape (abandon the imperative
#   mutable-slot encoding for a `match` and a `cond`) and needs its proofs
#   honestly retuned; it defends both obligations against being over-fit to the
#   imperative form. Both positives confirmed by real builds.
# PORTED-RE-AIMED (admissibility): the sibling asserts its precondition admits an
#   F2P-shaped input and that the arity-matching access is establishable there.
#   Neither obligation here has a precondition, so admission is trivial; the
#   residual risk is DEGENERACY, and the re-aimed asserts pin that both arms of
#   both relations are reached, that the post-images differ, and that the
#   merely-requested operand does not move the selection. Liveness confirmed
#   out-of-band: falsifying any assert fails the build.
# PORTED-CAVEATED (rival-unresolved-operand): ported as the direct spec-level
#   rival, but its refinement argument is WEAKER than the sibling's and says so.
#   The sibling claims this rival's counterpart fails a listed newly-passing
#   configuration; re-deriving the resolution rule and the prepared-table ranks
#   shows the three listed configurations all resolve the deferred request to the
#   JOINT strategy, so the pre-patch selection happens to agree with gold on all
#   three and its counterpart would still pass them. The defect it reintroduces
#   is the one in the PUBLIC ISSUE REPRODUCTION (a deferred request resolving to
#   the per-class strategy). The rival is still refuted by the spec, and its
#   witness discriminates; only the F2P-grounding of the refinement is softer,
#   and that is stated in the case rather than inherited.
# RE-EXPRESSED (the three rival-forge-rank-* cases): NOT omitted, unlike on the
#   velvet sibling. Those rivals forge self-consistency between the access they
#   perform and the rank they claim to have checked it against; there is no rank
#   argument and no capability token on this carrier, so the FORGERY mechanism has
#   no counterpart. But their adversarial CONTENT — a rival picks the wrong layout
#   and looks internally consistent doing it — is exactly what the three layout
#   rivals here carry, one per wrong choice: always-joint, always-per-class, and
#   driven-by-the-requested-operand. Nothing was invented and nothing was lost.
# PORTED-RE-EXPRESSED (rival-echo-no-read -> weak-ratio-wrong-quantity): the
#   sibling's echo returns the value argument with no access performed and is
#   caught only by an unforgeable token, because its value clause is satisfiable
#   without doing the work. Here every post-image is a constructor over the
#   obligation's own arguments, so there is no oracle to echo; the strongest
#   echo-shaped attack available is a result that has the right TYPE and the right
#   presence but is not the prepared quantity, and the value half of clause 1
#   refutes it directly. Same argument, re-expressed on a carrier needing no token.
# VACUOUS (rival-diverge-loop): closed on lean, and deliberately NOT recorded the
#   way the velvet sibling of this instance records it. There it is a KNOWN SPEC
#   HOLE (under `partial` termination semantics a diverging impl satisfies every
#   ensures clause vacuously and VERIFIES while its counterpart hangs —
#   the corpus-wide termination-semantics finding, 401 `partial` bundles admit it, 99 `total`
#   bundles reject it). Here it is closed, but the mechanism was RE-MEASURED and
#   the earlier wording ("a diverging implementation cannot be written") was
#   wrong: `partial def implementation_ratioEntry ... := implementation_ratioEntry
#   combinedPenalty ratio` compiles fine, since `Option ℚ` is inhabited. It is
#   still REJECTED, because Lean compiles `partial` to an opaque constant rather
#   than weakening the obligation to terminating runs, so the proof cannot unfold
#   it (`unfold failed to unfold implementation_ratioEntry`) and nothing can be
#   proven about the diverging body. The first impl is refused even earlier —
#   `AggLayout` has no `Inhabited` instance. Rejected either way, so there is no
#   rival to ship and no hole to report; the class is closed by the carrier's
#   treatment of `partial`, not by the impls being un-writable.
# VACUOUS (frame mutation): the sibling records this class as inapplicable on its
#   own carrier — every parameter is an immutable by-value scalar/option with no
#   reference held at partial permission to overwrite. Here a fortiori:
#   referentially transparent, no heap, no aliasing, no `mut` binder in any
#   signature. No substitute probe fabricated.
# DROPPED (AXIOM_TESTS): the axiom lane is G-AX's job and this gate ignores it.
#   This bundle declares no axioms and no deep-model references (both decisions
#   consume only values unchanged surrounding code prepares), so there is nothing
#   to probe.
#
# OBLIGATION / CLAUSE / BINDER COVERAGE
#   Both obligations DEFENDED: all three positives reshape BOTH impls, so each
#     obligation carries three expect="verify" cases.
#   Both obligations ATTACKED: three reject rivals each.
#   All FOUR top-level clauses attacked: chooseLayout clause 1 by
#     weak-layout-from-requested-operand and weak-layout-always-joint, clause 2 by
#     weak-layout-always-per-class; ratioEntry clause 1 (presence AND value) by
#     weak-ratio-wrong-quantity and weak-ratio-inverted-guard, clause 2 by
#     weak-ratio-unconditional (and again by the inverted guard).
#   INPUT BINDERS, per obligation, across its three reject witnesses (3 distinct
#   input points each, no two witnesses sharing a tuple):
#     chooseLayout  req : autoStrategy, perClass, joint     (all three values)
#                   eff : perClass,     perClass, joint     (both values)
#       `req` is moved off `eff`'s value by exactly one witness, which is what
#       makes the relation's intentional independence from `req` load-bearing;
#       `eff` is moved so that each clause is refuted on its own arm.
#     ratioEntry    combinedPenalty : false, true, true     (both values)
#                   ratio           : 3,     7,    5        (three values)
#       `ratio` is not merely varied numerically: weak-ratio-wrong-quantity is
#       refuted BECAUSE its recorded value ignores `ratio`, at a point chosen away
#       from its stand-in constant. The other two ratio rivals are refuted for
#       every value of `ratio`, so without that case the binder would be varied on
#       paper and unattacked in substance — the exact masked-binder shape that has
#       sunk other ports.
#   All six witness points are REACHABLE configurations of the real routine, not
#   just admissible points of the model.
AXIOM_TESTS = []
