"""properties.py — G-PBT falsification battery for django__django-13417 (lean).

NOT a Lean file; a record of adversarial cases the G-PBT gate executes. Each SPEC
case is a full ``Solution.lean`` variant sharing the FROZEN spec byte-for-byte
(region surgery: only text inside ``-- impl-start`` / ``-- impl-end`` — and, for a
case that legitimately re-proves, inside ``-- proof-start`` / ``-- proof-end`` — is
changed, so ``markers.same_spec`` holds and the ``theorem correct_querysetOrdered``
STATEMENT stays byte-identical). ``expect:"verify"`` passes iff (in scope AND the
file elaborates with the obligation closed, no ``sorry``/``admit``/
``native_decide``, no new ``axiom``/``theorem``); ``expect:"reject"`` passes iff
(in scope AND it does NOT verify AND the case's refutation ``witness`` holds of
the rival while FAILING on the frozen solution).

DEFENDED SURFACE (one modeled behavior, one obligation). Whether a result set will
carry a meaningful row ordering, pinned as a single total boolean equation over SIX
input binders:

  problem_spec_querysetOrdered
      (isEmpty : Bool) (extraOrderBy orderBy : List String)
      (defaultOrdering : Bool) (metaOrdering groupBy : List String)
      (result : Bool) : Prop :=
    result = (isEmpty || !extraOrderBy.isEmpty || !orderBy.isEmpty ||
              (defaultOrdering && !metaOrdering.isEmpty && groupBy.isEmpty))

The carrier is FULLY TRANSPARENT: no ``opaque`` callee, no axiom, every binder
observed only by its flag or its emptiness. So every refutation can be stated at
CONCRETE literal inputs and closed by ``decide`` — no conditioning on the carrier
is needed anywhere in this battery, and no witness binds anything (hence no
satisfiability question arises).

BINDER / CLAUSE STRUCTURE (read this before judging coverage). The right-hand side
is a four-way disjunction whose last disjunct is itself a three-way conjunction, so
there are SIX independently attackable positions, one per binder:

  D1  ``isEmpty``                     — unconditional: an empty result set is ordered
  D2  ``!extraOrderBy.isEmpty``       — an explicitly-requested extra ordering orders it
  D3  ``!orderBy.isEmpty``            — an explicitly-requested ordering orders it
  D4a ``defaultOrdering``             — the default-ordering mode must be in force
  D4b ``!metaOrdering.isEmpty``       — the model must actually carry a default ordering
  D4c ``groupBy.isEmpty``             — grouping SUPPRESSES the default ordering

Each of the six is attacked by its own rival (drop it, or invert its polarity), and
each rival is refuted at the input that isolates exactly that position. A NINTH
rival attacks the abstraction itself rather than a position: the spec observes each
sequence carrier only by its EMPTINESS, so an impl that keys on a carrier's CONTENTS
is wrong even though it drops no position and inverts no polarity
(``weak-meta-content-sensitive``). The nine witnesses therefore probe NINE DISTINCT
input points and vary all six binders: ``isEmpty`` at both values,
``defaultOrdering`` at both values, and each of the four sequence carriers both
empty and non-empty. No binder is held fixed across the battery, so a rival
mishandling any single one of them is caught.

ADVERSARIAL READ of the nagini classes on this carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS, and it was already N/A upstream. The
    sibling records that every one of its parameters is a by-value ``bool`` with no
    heap-carried read-only input, so there was no permission to violate there
    either. Lean is referentially transparent: the six binders are immutable values
    with no heap footprint and no aliasing, so there is no read-only field to
    overwrite and no substitute probe. Not fabricated.

  * DIVERGENCE / NON-TERMINATION — NOT SHIPPABLE as a witnessed rival, and absent
    upstream. The sibling carries no ``diverge-*``/``nonterm-*``/``weak-diverge``
    case. It is worth being precise about WHY there is none here, because the
    obvious reason is wrong: a diverging impl CAN be written on this carrier — the
    impl region may be replaced by a ``partial def`` that calls itself, which passes
    the admissible-variant scope check (``partial`` is not an assumption token, and
    the obligation statement is untouched). Measured with real builds: such a rival
    does not verify (the frozen script's ``unfold`` fails on the ``partial``
    definition, which has no equation lemmas), so it WOULD be "rejected" — but it
    cannot carry an honest refutation ``witness``, and that is what disqualifies it.
    A literal-input witness cannot be stated (``unfold`` fails on the rival for the
    same reason, so the witness does not hold of the rival), and the
    hypothesis-conditioned form — assuming the opaque value at a point and refuting
    there — was measured to ELABORATE against the frozen solution too (exit 0 on
    both sides), i.e. ``witness-vacuous``: because ``partial`` makes the impl
    irreducible rather than WRONG, the spec is not violated at any input one can
    exhibit. So the class is omitted for a demonstrated reason (no discriminating
    witness exists), not because it is inexpressible. This is NOT the
    ``partial``-semantics spec hole documented in ``the corpus-wide termination-semantics finding``
    (a velvet phenomenon under ``loom.semantics.termination``): here a diverging
    impl does not verify vacuously, it simply fails to verify.

  * UNGROUNDED-ORACLE ECHO — N/A. The sibling notes its ``@Pure`` oracle is grounded
    (a total boolean function of its arguments, fully unfolded in the contract), so
    echoing it is simply the CORRECT answer rather than a cheat. The same holds
    here: the spec's right-hand side is written out in terms of the input binders,
    so the direct-disjunction implementation is an honest cheapest-impl positive
    control (``pos-direct-disjunction``), not an answer-key echo.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen 64-way ``cases ... <;> simp_all <;> rfl``
script is tuned to the frozen guard cascade — so a rejection alone attributes
nothing to the spec. Every ``expect="reject"`` case therefore carries a Lean snippet
proving the rival CONTRADICTS the spec at one concrete input. Each was checked with
two real ``lake env lean`` builds: it ELABORATES against its rival, and it FAILS
against the frozen solution (there ``decide`` reports it proved the negation of the
witness's own claim — i.e. gold satisfies the spec at that point), so each is a real
discriminator and not a tautology. Re-derived independently at audit: all nine
witness pairs rebuilt, rival exit 0 / gold exit 1 in every case, and every gold-side
failure inspected to confirm it is that SEMANTIC ``decide`` refutation rather than an
unknown identifier, a type error, a failed unfold, or a stuck reduction.

AXIOM lane: EMPTY. The sibling's ``AXIOM_TESTS`` is already empty, and this bundle's
axioms region is empty too — every observation is reproduced concretely as a
flag/emptiness test rather than axiomatized, so there is nothing for this gate to
probe. ``AXIOM_TESTS = []``.
"""
from pathlib import Path

INSTANCE = "django__django-13417"
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
# Solution.lean, so the manifest breaks loudly if the frozen file ever drifts.
# ---------------------------------------------------------------------------
_SIG = ("def implementation_querysetOrdered\n"
        "    (isEmpty : Bool) (extraOrderBy orderBy : List String)\n"
        "    (defaultOrdering : Bool) (metaOrdering groupBy : List String) :\n")
_DO = "    Bool := Id.run do\n"

# The gold guard cascade (the whole impl region body, signature included).
_IMPL_GOLD = _SIG + _DO + (
    "  if isEmpty then\n    return true\n"
    "  if !extraOrderBy.isEmpty || !orderBy.isEmpty then\n    return true\n"
    "  else if defaultOrdering && !metaOrdering.isEmpty && groupBy.isEmpty then\n"
    "    return true\n"
    "  else\n    return false\n")

# The frozen tactic body (wholly inside `-- proof-start`/`-- proof-end`). Only the
# cases that legitimately re-prove touch this; every reject rival leaves it frozen
# and is judged by its witness, not by whether this script happens to break.
_PROOF_GOLD = (
    "  intro isEmpty extraOrderBy orderBy defaultOrdering metaOrdering groupBy\n"
    "  unfold problem_spec_querysetOrdered implementation_querysetOrdered\n"
    "  simp only [Id.run]\n"
    "  cases isEmpty <;>\n"
    "    cases defaultOrdering <;>\n"
    "    cases he : extraOrderBy.isEmpty <;>\n"
    "    cases ho : orderBy.isEmpty <;>\n"
    "    cases hm : metaOrdering.isEmpty <;>\n"
    "    cases hg : groupBy.isEmpty <;>\n"
    "    simp_all <;> rfl\n")

# The two guard expressions the rivals perturb, spelled once.
_EXPLICIT = "!extraOrderBy.isEmpty || !orderBy.isEmpty"
_DEFAULTED = "defaultOrdering && !metaOrdering.isEmpty && groupBy.isEmpty"


def _variant(impl_src, proof_src=_PROOF_GOLD):
    """Solution.lean with the impl region (and optionally the proof body) swapped."""
    return _swap(_swap(_BASE, _IMPL_GOLD, impl_src), _PROOF_GOLD, proof_src)


def _cascade(explicit_guard, defaulted_guard):
    """The gold cascade shape with its two non-empty guards substituted."""
    return _SIG + _DO + (
        "  if isEmpty then\n    return true\n"
        f"  if {explicit_guard} then\n    return true\n"
        f"  else if {defaulted_guard} then\n    return true\n"
        "  else\n    return false\n")


def _witness(is_empty, extra, order, default, meta, group):
    """`the spec does NOT hold of the rival's answer at this literal point`.

    Every binder is a ground literal, so no hypothesis is needed and the whole
    claim is closed by `decide` — hence no satisfiability question arises (the
    witness head binds nothing).
    """
    args = f"{is_empty} {extra} {order} {default} {meta} {group}"
    return ("example : ¬ problem_spec_querysetOrdered " + args + "\n"
            "    (implementation_querysetOrdered " + args + ") := by\n"
            "  unfold problem_spec_querysetOrdered implementation_querysetOrdered\n"
            "  decide\n")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # implementations that MUST verify, else SPEC-TOO-STRONG. Each keeps the
    # `theorem correct_querysetOrdered` statement byte-identical, adds no axiom,
    # lemma or assumption token, and was confirmed to close with a real build.
    # =====================================================================
    {
        "id": "pos-direct-disjunction",
        "kind": "soundness",
        "expect": "verify",
        # The cheapest honest implementation: drop the `Id.run do` scaffold and the
        # guard cascade entirely, returning the boolean combination in one step.
        # Definitionally equal to the specified combination, so `rfl` closes it
        # after the unfold; the 64-way case split is no longer needed, so the proof
        # body is retuned to exactly that. Statement byte-identical.
        "module": _variant(
            _SIG + "    Bool :=\n"
            "  isEmpty || !extraOrderBy.isEmpty || !orderBy.isEmpty ||\n"
            "    (defaultOrdering && !metaOrdering.isEmpty && groupBy.isEmpty)\n",
            "  intro isEmpty extraOrderBy orderBy defaultOrdering metaOrdering groupBy\n"
            "  unfold problem_spec_querysetOrdered implementation_querysetOrdered\n"
            "  rfl\n"),
        "rationale": "the structurally minimal correct impl — the specified boolean "
                     "combination returned in a single step, with no mutable-do "
                     "scaffold and no branch cascade. It agrees with the cascade on "
                     "every one of the 2^2 x 2^4 flag/emptiness combinations, so it "
                     "satisfies `result = <the combination>`; a faithful minimal impl "
                     "failing here would be SPEC-TOO-STRONG. This is NOT an "
                     "answer-key echo: the spec's right-hand side is written out in "
                     "terms of the input binders (no opaque oracle), so returning it "
                     "is doing the work. Proof retuned to `rfl` (the case split is "
                     "vacuous without the cascade); statement unchanged.",
    },
    {
        "id": "pos-reorder-guards",
        "kind": "soundness",
        "expect": "verify",
        # Structurally different control flow: test the explicit-ordering guard
        # FIRST, then the empty-set guard, and split the defaulted conjunction into
        # a nested branch. Same truth table; the two reordered guards are
        # independent (both return true), so precedence is unobservable.
        "module": _variant(
            _SIG + _DO + (
                f"  if {_EXPLICIT} then\n    return true\n"
                "  if isEmpty then\n    return true\n"
                "  if defaultOrdering && !metaOrdering.isEmpty then\n"
                "    if groupBy.isEmpty then\n      return true\n"
                "    return false\n"
                "  return false\n")),
        "rationale": "structurally different control flow: the explicit-ordering "
                     "guard is tested before the empty-set guard, and the "
                     "defaulted-ordering conjunction is split into a nested "
                     "grouping branch. Both reordered guards return the same value, "
                     "so their precedence is unobservable and the truth table is "
                     "unchanged — it must satisfy `result = <the combination>`, else "
                     "SPEC-TOO-STRONG. Guards against a spec that only accepts the "
                     "exact frozen branch order. The frozen case-split script still "
                     "closes it; no new axiom or lemma.",
    },
    {
        "id": "pos-accumulator",
        "kind": "soundness",
        "expect": "verify",
        # Third shape: a mutable accumulator instead of early returns. Seeds the
        # result with the three unconditional disjuncts, then refines it by the
        # defaulted conjunction only if still false, and returns it once.
        "module": _variant(
            _SIG + _DO + (
                "  let mut res := isEmpty || !extraOrderBy.isEmpty || !orderBy.isEmpty\n"
                "  if !res then\n"
                "    res := defaultOrdering && !metaOrdering.isEmpty && groupBy.isEmpty\n"
                "  return res\n")),
        "rationale": "a third correct shape: one mutable accumulator and a single "
                     "exit instead of a cascade of early returns. Seeding with the "
                     "three unconditional disjuncts and refining only when still "
                     "false reproduces the disjunction exactly, so `result = <the "
                     "combination>` holds — else SPEC-TOO-STRONG. Confirms the spec "
                     "is not tied to the early-return idiom. Frozen script closes "
                     "it; no new axiom or lemma.",
    },

    # =====================================================================
    # ADMISSIBILITY — the obligation must admit the discriminating input, and
    # admit it NON-degenerately (exactly one of the two boolean answers).
    # =====================================================================
    {
        "id": "admiss-discriminating-input",
        "kind": "admissibility",
        "expect": "verify",
        # `correct_querysetOrdered` binds ∀ with NO precondition hypothesis, so
        # instead of showing a guard admits an input we show the spec is
        # non-degenerate AT the discriminating input: it holds of exactly one of the
        # two possible answers there, and holds of the opposite answer once the
        # grouping carrier is emptied. Impl stays gold; the frozen script is kept
        # verbatim after the three `have`s (no new top-level declaration).
        "module": _variant(
            _IMPL_GOLD,
            "  have hSuppressed :\n"
            "      problem_spec_querysetOrdered false [] [] true [\"pk\"] [\"kind\"] false := by\n"
            "    unfold problem_spec_querysetOrdered\n"
            "    decide\n"
            "  have hSuppressedOnly :\n"
            "      ¬ problem_spec_querysetOrdered false [] [] true [\"pk\"] [\"kind\"] true := by\n"
            "    unfold problem_spec_querysetOrdered\n"
            "    decide\n"
            "  have hHonoured :\n"
            "      problem_spec_querysetOrdered false [] [] true [\"pk\"] [] true := by\n"
            "    unfold problem_spec_querysetOrdered\n"
            "    decide\n"
            + _PROOF_GOLD),
        "rationale": "the obligation carries NO precondition hypothesis (the "
                     "behavior is total over the six binders), so admissibility is "
                     "carried as NON-DEGENERACY at the discriminating input: with a "
                     "non-empty result set, no explicit ordering, the default-"
                     "ordering mode in force, a model default ordering present, and "
                     "a NON-EMPTY grouping carrier, the spec admits `false` and "
                     "REFUTES `true`; with the grouping carrier emptied it admits "
                     "`true`. That input is in-domain and the spec pins a single "
                     "answer on it — if either `have` failed, the spec would be "
                     "unsatisfiable or blind exactly where the modeled behavior "
                     "changes. Statement byte-identical; the frozen script follows "
                     "verbatim.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected. One per attackable position of the specified
    # combination (D1..D4c above), each with a machine-checked discriminating
    # witness at the input that ISOLATES that position, and the refinement
    # argument for why its faithful real counterpart would not resolve.
    # =====================================================================
    {
        "id": "weak-drop-group-conjunct",
        "kind": "uniqueness",
        "expect": "reject",
        # D4c attack — the load-bearing one. Drop the grouping conjunct: the
        # defaulted branch fires whether or not the result is aggregated into
        # groups. Agrees with the spec on every input except a grouped,
        # default-ordered, explicitly-unordered non-empty set.
        "module": _variant(_cascade(_EXPLICIT,
                                    "defaultOrdering && !metaOrdering.isEmpty")),
        "refinement": "this is the pre-change behavior: the defaulted-ordering "
                      "branch ignores whether the result is aggregated into groups. "
                      "Its faithful real counterpart is the unfixed property, which "
                      "is exactly what FAILS the two F2P regression tests — they "
                      "assert that an aggregated result set over a model carrying a "
                      "default ordering reports NOT ordered, and this reports "
                      "ordered. So a verifying rival here would be a true "
                      "verify-does-not-imply-resolve break.",
        "rationale": "REJECT from the D4c position of `result = (... || "
                     "(defaultOrdering && !metaOrdering.isEmpty && groupBy.isEmpty))`: "
                     "with isEmpty=false, both explicit-ordering carriers empty, "
                     "defaultOrdering=true, metaOrdering non-empty and groupBy "
                     "NON-EMPTY the specified value is false and the rival answers "
                     "true. Witness isolates D4c: it is the only input point in this "
                     "battery with a non-empty grouping carrier reached through the "
                     "defaulted branch. SPEC-TOO-WEAK if it verified.",
        "witness": _witness("false", "[]", "[]", "true", '["pk"]', '["kind"]'),
    },
    {
        "id": "weak-flip-group-polarity",
        "kind": "uniqueness",
        "expect": "reject",
        # D4c attack, opposite sign — a NEAR-MISS of the previous rival that must
        # not share its witness: it is wrong on the COMPLEMENTARY sub-domain (it
        # requires grouping to be present rather than absent), so it is refuted at
        # the un-grouped point, where the previous rival agrees with the spec.
        "module": _variant(_cascade(
            _EXPLICIT, "defaultOrdering && !metaOrdering.isEmpty && !groupBy.isEmpty")),
        "refinement": "inverts the polarity of the grouping conjunct instead of "
                      "dropping it. Its faithful counterpart would report a "
                      "NON-aggregated result set that inherits the model's default "
                      "ordering as not ordered — failing the P2P assertions that "
                      "such a set IS ordered — while still reporting an aggregated "
                      "one as ordered, so it also fails the F2P assertions. It does "
                      "not resolve in either direction.",
        "rationale": "REJECT from the D4c position, at the COMPLEMENTARY sub-domain "
                     "to weak-drop-group-conjunct: with isEmpty=false, both explicit "
                     "carriers empty, defaultOrdering=true, metaOrdering non-empty "
                     "and groupBy EMPTY the specified value is true and the rival "
                     "answers false. Its own witness point (empty grouping carrier) "
                     "is where the drop-conjunct rival is CORRECT, so the two cannot "
                     "share a witness and each demonstrates the sub-domain it "
                     "claims. SPEC-TOO-WEAK if it verified.",
        "witness": _witness("false", "[]", "[]", "true", '["pk"]', "[]"),
    },
    {
        "id": "weak-empty-not-unconditional",
        "kind": "uniqueness",
        "expect": "reject",
        # D1 attack: make the empty-set disjunct CONDITIONAL on the absence of
        # grouping. Correct everywhere except an empty result set that is also
        # aggregated — the one place D1's unconditionality is load-bearing.
        "module": _variant(
            _SIG + _DO + (
                "  if isEmpty && groupBy.isEmpty then\n    return true\n"
                f"  if {_EXPLICIT} then\n    return true\n"
                f"  else if {_DEFAULTED} then\n    return true\n"
                "  else\n    return false\n")),
        "refinement": "makes the trivially-ordered empty result set conditional on "
                      "the absence of grouping, so it reports an empty result set "
                      "that is ALSO aggregated as not ordered. NOTE, honestly: "
                      "unlike every other rival here this one is NOT caught by any "
                      "assertion in the modeled behavior's own test class — the "
                      "existing empty-result-set assertion exercises an "
                      "un-aggregated empty set, where this rival agrees with the "
                      "spec. Its sub-domain is nonetheless REACHABLE (the "
                      "empty-marker and the grouping carrier are set by independent "
                      "operations and compose freely), so a faithful counterpart is "
                      "a real behavioral regression against the specified "
                      "unconditional guarantee — it is simply an UNTESTED one "
                      "upstream. Kept because the spec must pin the whole modeled "
                      "domain, not only the points the shipped tests sample; the "
                      "claim it earns is spec-uniqueness on D1, not "
                      "verify-does-not-imply-resolve.",
        "rationale": "REJECT from the D1 position (`isEmpty` is an UNCONDITIONAL "
                     "disjunct): with isEmpty=true and groupBy NON-EMPTY (everything "
                     "else off) the specified value is true and the rival answers "
                     "false. This is the only witness in the battery that varies the "
                     "`isEmpty` binder to true, which is what makes D1's "
                     "unconditionality observable. SPEC-TOO-WEAK if it verified.",
        "witness": _witness("true", "[]", "[]", "false", "[]", '["kind"]'),
    },
    {
        "id": "weak-drop-meta-conjunct",
        "kind": "uniqueness",
        "expect": "reject",
        # D4b attack: report ordered whenever the default-ordering mode is in force
        # and there is no grouping, even when the model carries NO default ordering
        # sequence — claiming an ordering where there is none to honour.
        "module": _variant(_cascade(_EXPLICIT, "defaultOrdering && groupBy.isEmpty")),
        "refinement": "reports ordered whenever the default-ordering mode is in "
                      "force, even when the model declares no default ordering at "
                      "all. Its faithful counterpart would report a result set with "
                      "no ordering whatsoever as ordered, failing the P2P assertions "
                      "for a model without a default ordering and for one whose "
                      "default ordering has been cleared. It does not resolve.",
        "rationale": "REJECT from the D4b position (`!metaOrdering.isEmpty`): with "
                     "isEmpty=false, both explicit carriers empty, "
                     "defaultOrdering=true, metaOrdering EMPTY and groupBy empty the "
                     "specified value is false and the rival answers true. The "
                     "witness varies `metaOrdering` to empty while keeping "
                     "`defaultOrdering` true — the only way to separate the two "
                     "conjuncts of the defaulted branch. SPEC-TOO-WEAK if it "
                     "verified.",
        "witness": _witness("false", "[]", "[]", "true", "[]", "[]"),
    },
    {
        "id": "weak-meta-content-sensitive",
        "kind": "uniqueness",
        "expect": "reject",
        # ADDED BY AUDIT. D4b attack from a direction no other rival takes: every
        # existing rival either DROPS a position or inverts its polarity, so all of
        # them observe the sequence carriers exactly as the spec does — by emptiness
        # alone. This one instead observes the CONTENT (here, the length) of the
        # model's default-ordering carrier, honouring it only when it names more
        # than one field. That is the defect class the emptiness abstraction exists
        # to rule out, and the battery did not probe it: a rival can be wrong by
        # looking at too MUCH of a carrier, not only by ignoring it.
        "module": _variant(_cascade(
            _EXPLICIT,
            "defaultOrdering && metaOrdering.length > 1 && groupBy.isEmpty")),
        "refinement": "honours the model's default ordering only when it names more "
                      "than one field, so a model whose default ordering names a "
                      "SINGLE field is reported as not ordered. Its faithful "
                      "counterpart fails the P2P assertion that a result set over a "
                      "model carrying a one-field default ordering IS ordered — the "
                      "single most common shape of that declaration. It does not "
                      "resolve.",
        "rationale": "REJECT from the D4b position, attacked by CONTENT rather than "
                     "by presence: with isEmpty=false, both explicit carriers empty, "
                     "defaultOrdering=true, groupBy empty and metaOrdering a "
                     "ONE-element sequence the specified value is true (the carrier "
                     "is non-empty) and the rival answers false. Every other rival "
                     "in this battery observes the sequence carriers only by "
                     "emptiness, exactly as the spec does, so none of them can "
                     "detect an impl that keys on a carrier's contents; the spec "
                     "must pin emptiness-ONLY observation, and this is the case that "
                     "demonstrates it does. SPEC-TOO-WEAK if it verified.",
        "witness": _witness("false", "[]", "[]", "true", '["name"]', "[]"),
    },
    {
        "id": "weak-drop-default-flag",
        "kind": "uniqueness",
        "expect": "reject",
        # D4a attack — the mirror of the previous rival, isolating the OTHER
        # conjunct of the defaulted branch: honour the model's default ordering even
        # when the default-ordering mode is NOT in force.
        "module": _variant(_cascade(_EXPLICIT,
                                    "!metaOrdering.isEmpty && groupBy.isEmpty")),
        "refinement": "honours the model's default ordering even when the "
                      "default-ordering mode has been switched off. Its faithful "
                      "counterpart would report a result set whose default ordering "
                      "was explicitly disabled as ordered, failing the P2P assertion "
                      "for a cleared default ordering. It does not resolve.",
        "rationale": "REJECT from the D4a position (`defaultOrdering`): with "
                     "isEmpty=false, both explicit carriers empty, "
                     "defaultOrdering=FALSE, metaOrdering non-empty and groupBy "
                     "empty the specified value is false and the rival answers true. "
                     "This witness is the mirror of weak-drop-meta-conjunct's — "
                     "flag off / sequence present, versus flag on / sequence absent "
                     "— so neither subsumes the other and each conjunct of the "
                     "defaulted branch is separately demonstrated. SPEC-TOO-WEAK if "
                     "it verified.",
        "witness": _witness("false", "[]", "[]", "false", '["pk"]', "[]"),
    },
    {
        "id": "weak-ignore-extra-order",
        "kind": "uniqueness",
        "expect": "reject",
        # D2 attack: consult only ONE of the two explicit-ordering carriers,
        # ignoring the supplementary one. Wrong exactly when the supplementary
        # carrier alone requests an ordering.
        "module": _variant(_cascade("!orderBy.isEmpty", _DEFAULTED)),
        "refinement": "consults only one of the two explicit-ordering carriers, "
                      "ignoring the supplementary one. Its faithful counterpart "
                      "would report a result set ordered solely through the "
                      "supplementary channel as not ordered, failing the P2P "
                      "assertion covering that channel. It does not resolve.",
        "rationale": "REJECT from the D2 position (`!extraOrderBy.isEmpty`): with "
                     "extraOrderBy NON-EMPTY and everything else off/empty the "
                     "specified value is true and the rival answers false. This is "
                     "the only witness that varies `extraOrderBy` to non-empty, so "
                     "without it a rival blind to that carrier alone would pass the "
                     "battery unnoticed. SPEC-TOO-WEAK if it verified.",
        "witness": _witness("false", '["-pk"]', "[]", "false", "[]", "[]"),
    },
    {
        "id": "weak-ignore-order-by",
        "kind": "uniqueness",
        "expect": "reject",
        # D3 attack — the mirror of the previous rival on the OTHER explicit
        # carrier, refuted at the point where that one is correct.
        "module": _variant(_cascade("!extraOrderBy.isEmpty", _DEFAULTED)),
        "refinement": "consults only the supplementary explicit-ordering carrier, "
                      "ignoring the primary one. Its faithful counterpart would "
                      "report a result set with an explicitly requested ordering as "
                      "not ordered, failing the P2P assertion for an explicit "
                      "ordering — and, since the F2P scenario's sibling test asserts "
                      "that adding an explicit ordering to an aggregated set makes "
                      "it ordered, that too. It does not resolve.",
        "rationale": "REJECT from the D3 position (`!orderBy.isEmpty`): with orderBy "
                     "NON-EMPTY and everything else off/empty the specified value is "
                     "true and the rival answers false. Its witness point is where "
                     "weak-ignore-extra-order is CORRECT and vice versa, so the two "
                     "explicit-ordering disjuncts are separately demonstrated rather "
                     "than lumped into one probe. SPEC-TOO-WEAK if it verified.",
        "witness": _witness("false", "[]", '["pk"]', "false", "[]", "[]"),
    },
    {
        "id": "weak-constant-true",
        "kind": "uniqueness",
        "expect": "reject",
        # Whole-equation attack: always report ordered, ignoring all six binders.
        # A cheap supporting near-miss, refuted at the all-off point that no other
        # witness occupies — the one input where every disjunct is false.
        "module": _variant(_SIG + _DO + "  return true\n"),
        "refinement": "always reports ordered, ignoring every input. Its faithful "
                      "counterpart makes every negative-ordering assertion fail — "
                      "the P2P tests for a model with no default ordering and for a "
                      "cleared default ordering, as well as both F2P tests, which "
                      "assert an aggregated result set is NOT ordered. It does not "
                      "resolve.",
        "rationale": "REJECT from the whole equation: at the all-off input "
                     "(isEmpty=false, both explicit carriers empty, "
                     "defaultOrdering=false, metaOrdering and groupBy empty) every "
                     "disjunct is false, so the specified value is false and the "
                     "rival answers true. It is the MINIMAL such point — every "
                     "binder off/empty — confirming the spec constrains the result "
                     "there at all rather than only distinguishing among the true "
                     "cases. (The all-disjuncts-false CORNER is not unique to this "
                     "witness: weak-drop-group-conjunct, weak-drop-meta-conjunct "
                     "and weak-drop-default-flag are each refuted at a point where "
                     "the specified value is also false. What is unique here is "
                     "that this one holds every binder at its off/empty value, so "
                     "it catches a rival that ignores all six.) SPEC-TOO-WEAK if it "
                     "verified.",
        "witness": _witness("false", "[]", "[]", "false", "[]", "[]"),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> lean accounting. The sibling ships 9 SPEC cases (3 soundness
# positives, 1 admissibility, 5 uniqueness rivals) and an EMPTY axiom lane, over
# a 5-argument all-boolean carrier. This bundle models the same single behavior,
# but its carrier SPLITS two of those booleans into sequence carriers observed by
# emptiness: the sibling's single `has_raw_order` becomes TWO independent
# explicit-ordering carriers (`extraOrderBy`, `orderBy`), and `model_has_order`
# becomes the emptiness of `metaOrdering`. So the port is not narrower here — it
# is one binder WIDER, and two rivals were added to cover the split.
#
#   sibling case                  -> here
#   ---------------------------------------------------------------------
#   pos-single-return             -> pos-direct-disjunction       RE-EXPRESSED
#   pos-reorder-branches          -> pos-reorder-guards           RE-EXPRESSED
#   pos-local-var                 -> pos-accumulator              RE-EXPRESSED
#   admiss-f2p-shaped             -> admiss-discriminating-input   RE-EXPRESSED
#   weak-prepatch-bug             -> weak-drop-group-conjunct      RE-EXPRESSED
#   weak-flip-grouped-polarity    -> weak-flip-group-polarity      RE-EXPRESSED
#   weak-empty-misses-grouped     -> weak-empty-not-unconditional  RE-EXPRESSED
#   weak-ignore-model-order       -> weak-drop-meta-conjunct       RE-EXPRESSED
#   weak-constant-true            -> weak-constant-true            RE-EXPRESSED
#   (frame-mutation)              -> (none)   VACUOUS — and already N/A upstream
#   (divergence / non-termination)-> (none)   VACUOUS — absent upstream, and a
#                                             total `def` cannot diverge here
#   AXIOM_TESTS ([] upstream)     -> []       N/A (axioms region is empty)
#   (added: weak-drop-default-flag, weak-ignore-extra-order,
#           weak-ignore-order-by — carrier WIDENING, see below)
#   (added by AUDIT: weak-meta-content-sensitive — emptiness-ONLY observation,
#           a defect class no ported rival could express; see below)
#
# EVERY sibling SPEC case is ported; nothing was dropped, and no rival was found
# to be non-wrong on this carrier. The three ADDED rivals exist because this
# carrier exposes positions the sibling's did not:
#   * `weak-ignore-extra-order` / `weak-ignore-order-by` — the sibling folds both
#     explicit-ordering channels into one boolean, so a rival blind to just one of
#     them is inexpressible there but is a real defect here. They are mutual
#     near-misses, so each is refuted at the point where the other is correct.
#   * `weak-drop-default-flag` — the sibling attacks only the model-default-ordering
#     conjunct; here the mode flag and the model's ordering sequence are separate
#     binders, so the mirror rival (flag ignored, sequence honoured) is a distinct
#     defect and gets the mirror-image witness.
#   * `weak-meta-content-sensitive` (ADDED BY AUDIT) — the sibling's carriers are
#     BOOLEANS, so "observes the carrier's contents rather than its truthiness" is
#     inexpressible upstream: there are no contents to observe. Here the carriers are
#     `List String` projected to emptiness by the type bijection, so an impl keying
#     on a carrier's length/elements is a real defect that leaves the spec's
#     emptiness-only abstraction untested. The other eight rivals cannot catch it:
#     every one of them observes the carriers exactly as the spec does. This is a
#     carrier-widening gap of the same kind as the two explicit-ordering rivals, but
#     on the ABSTRACTION rather than on a position.
#
# RE-EXPRESSED (positives): the sibling's three positives carry the argument that a
#   faithful correct impl must verify regardless of shape. Carried here by (a) the
#   scaffold-free single-expression form (proof retuned to `rfl`, since the 64-way
#   case split is vacuous without the cascade), (b) a reordered guard cascade with a
#   nested grouping branch, and (c) a mutable accumulator with a single exit. All
#   three keep the obligation statement byte-identical, add no axiom or lemma, and
#   were confirmed to close with real builds.
# RE-EXPRESSED (admissibility): the sibling self-calls the oracle on the
#   discriminating input to show the (trivially true) precondition admits it. This
#   obligation binds all six inputs with NO precondition hypothesis, so the argument
#   is carried as NON-DEGENERACY instead: at the discriminating input the spec admits
#   exactly one of the two answers (and the opposite one once the grouping carrier is
#   emptied). Same purpose — the spec must be satisfiable and decisive precisely
#   where the modeled behavior turns — without inventing a precondition.
# VACUOUS (frame-mutation): the sibling records this class as N/A on its own carrier
#   (every parameter a by-value bool, no heap-carried read-only input), and it is
#   vacuous here for the backend reason: referential transparency, immutable value
#   binders, no aliasing. Not fabricated, per the porting map.
# VACUOUS (divergence): the sibling carries no divergence rival, and this backend
#   could not host one — `implementation_querysetOrdered` is a total, non-recursive
#   Lean `def`, so a non-terminating implementation cannot be written. This is a
#   carrier fact, NOT the `partial`-semantics spec hole in
#   `the corpus-wide termination-semantics finding`, which is a velvet phenomenon.
#
#   BINDER COVERAGE. The nine reject witnesses probe nine DISTINCT input points
#   and move every one of the six binders: `isEmpty` true (weak-empty-not-
#   unconditional) and false (all others); `defaultOrdering` true (drop-group-
#   conjunct, flip-group-polarity, drop-meta-conjunct, meta-content-sensitive) and
#   false (the rest);
#   `extraOrderBy` non-empty (ignore-extra-order) and empty; `orderBy` non-empty
#   (ignore-order-by) and empty; `metaOrdering` non-empty (drop-group-conjunct,
#   flip-group-polarity, drop-default-flag, meta-content-sensitive) and empty;
#   `groupBy` non-empty
#   (drop-group-conjunct, empty-not-unconditional) and empty. All six attackable
#   positions of the specified combination (the four disjuncts plus the two
#   non-grouping conjuncts of the fourth) are attacked, the emptiness-only
#   ABSTRACTION over the sequence carriers is attacked, and the all-disjuncts-false
#   corner is probed too.
#
#   WHAT THIS BATTERY DOES NOT CLAIM (audited, stated so no reader over-reads it).
#   Eight of the nine rivals have a faithful counterpart that breaks at least one
#   assertion of the modeled behavior's own upstream test class, so for those the
#   refinement argument is a real verify-does-not-imply-resolve argument. ONE does
#   not: `weak-empty-not-unconditional` is wrong only on an empty result set that is
#   ALSO aggregated, a reachable configuration the shipped assertions never sample.
#   Its case note says so explicitly. It earns spec-uniqueness on the D1 position,
#   not a resolve claim.
#
# AXIOM_TESTS: empty, matching the sibling. This bundle's axioms region is empty —
# every observation is reproduced concretely as a flag or emptiness test rather than
# axiomatized — so there is no callee contract for this gate to probe.
AXIOM_TESTS = []
