"""properties.py — G-PBT falsification battery for pydata__xarray-6461 (lean).

NOT a Lean file; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside an ``-- impl-start`` /
``-- impl-end`` region — and, for a case that legitimately re-proves, inside a
``-- proof-start`` / ``-- proof-end`` region — is changed, so
``markers.same_spec`` holds and every ``theorem correct_<name>`` STATEMENT stays
byte-identical). ``expect:"verify"`` passes iff (in scope AND the file
elaborates with the obligation closed, no ``sorry``/``admit``/``axiom``);
``expect:"reject"`` passes iff (in scope AND it does NOT verify AND the case's
refutation ``witness`` holds of the rival while FAILING on the frozen solution).

DEFENDED SURFACE (one modeled behavior over a three-argument conditional
selection; each argument is either a labelled array carrying its own attribute
dictionary or a bare scalar carrying none). The result is modeled as
``Except Unit (Option Attrs)``:

  whereAttrs (cond x y : Arg) : Except Unit (Option Attrs)
    let objs := the labelled-array arguments in positional order
    objs = [] → result = ok none         (nothing to merge)
    objs ≠ [] → result = ok (some (attrsOf x))   (the SECOND argument's dict)

The load-bearing clause is the second conjunct: whenever at least one argument
is a labelled array, the resolved dictionary must be the attribute dictionary of
the SECOND positional argument (its own dict if labelled, the empty dict if a
scalar) — never some other argument's, never an out-of-range lookup failure.

ADVERSARIAL READ of the classes on this carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS. Lean is referentially transparent:
    no input carries a heap permission, there is no read-only half-permission to
    overwrite and no aliasing to exploit. The nagini frame-mutation rival (write
    back into the read-only positional-list input) has no expressible instance
    here; no substitute is fabricated for it.

  * UNGROUNDED-ORACLE ECHO — VACUOUS. The postcondition is GROUNDED in the
    arguments (an equality against a term built only from the inputs, fully
    unfolded via ``attrsOf``); the bundle declares no ``opaque``/``axiom``, so
    there is no answer key an implementation could echo without doing the work.
    In its place the battery carries honest cheapest-implementation POSITIVE
    CONTROLS (``pos-*``) that must verify, plus an ADMISSIBILITY control pinning
    satisfiability at the normal inputs the behavior is exercised on.

  * CONTROL-FLOW-EFFECT + PARTIAL-DOMAIN / VALUE — APPLIES. The observable is
    the ok/error decision together with the resolved dictionary. A rival that
    reads the entry at a fixed positional offset (rather than the second
    argument) is correct EXACTLY on the sub-domain where that offset happens to
    coincide with the second argument, and diverges elsewhere: either an
    out-of-range failure (too few labelled arguments) or the wrong argument's
    dictionary (a different labelled argument sits at the offset). Both rivals
    attack the second conjunct.

WHAT EACH REJECT CASE ATTESTS TO, kept separate on purpose. Four of the five
rivals are refuted by the frozen spec at an input where a faithful patch of
their shape would ALSO fail the behavioral oracle, so for those the rejection is
a genuine verify-does-not-imply-resolve near-miss. Two are not near-misses and
their prose says so rather than claiming otherwise: ``weak-fixed-offset-wrong-
selection`` agrees with the required behavior on both configurations the
behavioral oracle exercises (its refinement note carries the machine-checked
scope), and ``weak-empty-dict-for-no-arrays`` attacks a configuration the oracle
never reaches. Those two attest to the frozen spec being STRICTLY STRONGER than
the oracle over the modeled domain — which is what the uniqueness lane is for —
and conflating the two claims is what this note exists to prevent.

CLAUSE COVERAGE. Both conjuncts carry a rival: the second is attacked by the
four positional-selection rivals, the first (the "nothing to merge"
short-circuit) by ``weak-empty-dict-for-no-arrays``, which is the only one whose
refutation does not go through the second conjunct.

BINDER COVERAGE. All three positional binders are varied across the reject
witnesses, in both of the shapes each can take:

  * ``x`` (the second argument, whose dictionary the rule selects) — a SCALAR in
    ``weak-fixed-offset-unguarded-raise`` and ``weak-fixed-offset-wrong-selection``
    (where its dictionary is forced empty), and a LABELLED ARRAY carrying its own
    non-empty dictionary in ``weak-first-labelled-selection`` and
    ``weak-last-labelled-selection``. Probing only the scalar shape would leave a
    whole class unattacked: a rival that resolves correctly whenever the second
    argument is the sole labelled argument but picks a DIFFERENT labelled
    argument otherwise never raises, so it is invisible on the
    scalar-second-argument sub-domain that motivated the report — the two
    positional-selection rivals below are refuted exactly there.
  * ``cond`` — a labelled array in three rivals, a scalar in
    ``weak-last-labelled-selection``.
  * ``y`` — a scalar in two rivals, a labelled array in two.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen script (``by_cases`` + ``rfl``) is tuned
to the frozen form — so a rejection alone attributes nothing to the spec. Every
``expect="reject"`` case therefore carries a Lean snippet proving the rival
CONTRADICTS the spec at one concrete input. Each reduces the rival's
implementation at that input by ``rfl`` and derives a contradiction from the
second conjunct; each was checked to hold of its rival and to FAIL on the frozen
solution (so it discriminates rather than asserting a tautology).

AXIOM lane: EMPTY. meta.json axioms == [] and deep_model_references == []; the
modeled behavior is a total computation over the arguments' own data, so there
is no axiom-soundness / axiom-containment obligation to probe here (that lane
belongs to G-AX in any case).
"""
from pathlib import Path

INSTANCE = "pydata__xarray-6461"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- region anchors (each unique inside Solution.lean; verified at load) ----
# The FULL body of the one impl region, and the FULL tactic body of the one
# proof region, so every replacement lands entirely inside the region it edits.
_IMPL = (
    "  let objs := [cond, x, y].filter (fun a => a.isDarray)\n"
    "  if objs = [] then\n"
    "    return Except.ok none\n"
    "  return Except.ok (some (attrsOf x))"
)
_PROOF = (
    "  intro cond x y\n"
    "  unfold problem_spec_whereAttrs implementation_whereAttrs\n"
    "  simp only [Id.run]\n"
    "  by_cases h : [cond, x, y].filter (fun a => a.isDarray) = []\n"
    "  · refine ⟨fun _ => ?_, fun hne => absurd h hne⟩\n"
    "    simp only [h, if_true]\n"
    "    rfl\n"
    "  · refine ⟨fun he => absurd he h, fun _ => ?_⟩\n"
    "    simp only [h, if_false]\n"
    "    rfl"
)

assert _IMPL in _BASE and _BASE.count(_IMPL) == 1, "impl anchor drift / not unique"
assert _PROOF in _BASE and _BASE.count(_PROOF) == 1, "proof anchor drift / not unique"


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # implementations that MUST verify. If a faithful correct implementation
    # cannot satisfy the frozen obligation the spec is SPEC-TOO-STRONG. Each
    # keeps the `theorem correct_whereAttrs` statement byte-identical; the first
    # retains the frozen tactic body (the reshape is definitional), the second
    # re-proves for the reordered shape where the frozen script no longer
    # applies. Neither introduces a helper lemma, an axiom, or an assumption
    # token. Ports nagini case (1) pos-control-branch-typed-local.
    # =====================================================================
    {
        "id": "pos-resolved-typed-local",
        "kind": "soundness",
        "expect": "verify",
        # Route the resolved dictionary through a typed local before wrapping it.
        # Same value flows into the non-empty branch, so the ok/error decision
        # and the resolved dictionary are unchanged; the frozen `rfl` (the local
        # is zeta-reduced) still closes.
        "module": _swap(
            _BASE, _IMPL,
            "  let objs := [cond, x, y].filter (fun a => a.isDarray)\n"
            "  if objs = [] then\n"
            "    return Except.ok none\n"
            "  let keep : Attrs := attrsOf x\n"
            "  return Except.ok (some keep)",
        ),
        "rationale": "binding the resolved dictionary (the second argument's "
                     "attrs) to a typed local before wrapping it keeps `objs ≠ "
                     "[] → result = ok (some (attrsOf x))` and the empty-objs "
                     "short-circuit unchanged; a correct reshape must verify, "
                     "else the second conjunct is SPEC-TOO-STRONG. Proof: frozen "
                     "tactic body retained (the local is zeta-reduced, so the "
                     "`by_cases … rfl` script still closes both branches).",
    },
    {
        "id": "pos-negated-guard-reorder",
        "kind": "soundness",
        "expect": "verify",
        # Branch reorder: handle the non-empty case in the guard and fall through
        # to the empty short-circuit. Same objs-empty vs objs-nonempty semantics,
        # same resolved dictionary. The frozen script keys on the `objs = []`
        # guard shape, so the obligation is re-proved for the negated guard —
        # statement byte-identical.
        "module": _swap(
            _swap(
                _BASE, _IMPL,
                "  let objs := [cond, x, y].filter (fun a => a.isDarray)\n"
                "  if objs ≠ [] then\n"
                "    return Except.ok (some (attrsOf x))\n"
                "  return Except.ok none",
            ),
            _PROOF,
            "  intro cond x y\n"
            "  unfold problem_spec_whereAttrs implementation_whereAttrs\n"
            "  simp only [Id.run]\n"
            "  by_cases h : [cond, x, y].filter (fun a => a.isDarray) = []\n"
            "  · refine ⟨fun _ => ?_, fun hne => absurd h hne⟩\n"
            "    simp only [h, ne_eq, not_true_eq_false, if_false]\n"
            "    rfl\n"
            "  · refine ⟨fun he => absurd he h, fun _ => ?_⟩\n"
            "    simp only [h, ne_eq, not_false_eq_true, if_true]\n"
            "    rfl",
        ),
        "rationale": "reordering the two exits behind a negated (`objs ≠ []`) "
                     "guard preserves the exact empty-vs-nonempty decision and "
                     "the resolved dictionary, so both conjuncts still hold; must "
                     "verify (else SPEC-TOO-STRONG). Re-proved because the frozen "
                     "`simp only [h, if_true/if_false]` is tuned to the frozen "
                     "guard: the negated guard needs `ne_eq` + the boolean-guard "
                     "simp lemmas (Mathlib/core, not new declarations).",
    },

    # =====================================================================
    # ADMISSIBILITY — a positive control confirming the obligation is
    # SATISFIABLE (non-vacuous) at the normal inputs the behavior is exercised
    # on, not only provable in the abstract. The frozen theorem carries NO
    # precondition hypothesis (the behavior is total, so `∀` is unguarded), which
    # means the nagini precondition-admission probe has no binder to attack here;
    # the honest analogue is to discharge the spec predicate at three ground
    # inputs — a labelled-array selection with a SCALAR second argument (empty
    # resolved dictionary), an all-labelled selection, and the no-labelled-array
    # short-circuit — by evaluation inside the proof region, alongside the frozen
    # obligation. If any ground instance could not be discharged, the behavior
    # would be unsatisfiable at exactly an input it must admit (the analogue of
    # PRECOND-TOO-STRONG). Ports nagini case (2)
    # admissibility-readonly-present-both-configs.
    # =====================================================================
    {
        "id": "admiss-ground-instances",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _PROOF,
            "  have _g_scalar : problem_spec_whereAttrs (Arg.darray []) Arg.scalar Arg.scalar\n"
            "      (implementation_whereAttrs (Arg.darray []) Arg.scalar Arg.scalar) := by\n"
            "    unfold problem_spec_whereAttrs implementation_whereAttrs\n"
            "    exact ⟨fun h => absurd h (by decide), fun _ => rfl⟩\n"
            "  have _g_darray : problem_spec_whereAttrs (Arg.darray []) (Arg.darray [(\"attr\", \"x\")]) (Arg.darray [])\n"
            "      (implementation_whereAttrs (Arg.darray []) (Arg.darray [(\"attr\", \"x\")]) (Arg.darray [])) := by\n"
            "    unfold problem_spec_whereAttrs implementation_whereAttrs\n"
            "    exact ⟨fun h => absurd h (by decide), fun _ => rfl⟩\n"
            "  have _g_none : problem_spec_whereAttrs Arg.scalar Arg.scalar Arg.scalar\n"
            "      (implementation_whereAttrs Arg.scalar Arg.scalar Arg.scalar) := by\n"
            "    unfold problem_spec_whereAttrs implementation_whereAttrs\n"
            "    exact ⟨fun _ => rfl, fun h => absurd rfl h⟩\n"
            + _PROOF,
        ),
        "rationale": "the obligation is discharged at three ground inputs by "
                     "evaluation — a labelled-array selection with a scalar "
                     "second argument (resolved to the empty dictionary), an "
                     "all-labelled selection, and the no-labelled-array "
                     "short-circuit — then the frozen obligation is closed "
                     "verbatim. Verifies (else the behavior is unsatisfiable at a "
                     "normal input it must admit). Nothing is assumed: no new "
                     "declaration, the theorem statement is byte-identical, and "
                     "the ground instances are `have`s inside the tactic body.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong implementations sharing the
    # frozen spec that MUST be rejected. Each carries (a) the refinement
    # argument that its faithful real patch would NOT resolve the F2P, so a
    # verifying rival would be a true verify-does-not-imply-resolve break rather
    # than an artifact, and (b) a refutation witness pinning the violation at one
    # concrete input. Both are the two semantic faces of the pre-fix behavior:
    # a read at a FIXED positional offset rather than the second argument.
    # =====================================================================
    {
        "id": "weak-fixed-offset-unguarded-raise",
        "kind": "uniqueness",
        "expect": "reject",
        # THE RAISE FACE (the literal pre-fix behavior): read the entry at the
        # fixed positional offset 1 of the labelled-array list; if the list is
        # too short the lookup fails (Except.error). When the second argument is
        # a scalar and only one argument is labelled, objs has length 1, so the
        # offset-1 lookup is out of range → error, where the spec requires
        # ok (some (attrsOf x)). Ports nagini case (5)
        # partial-domain-constant-offset-unguarded-raise.
        "module": _swap(
            _BASE, _IMPL,
            "  let objs := [cond, x, y].filter (fun a => a.isDarray)\n"
            "  if objs = [] then\n"
            "    return Except.ok none\n"
            "  match (objs.map attrsOf)[1]? with\n"
            "  | some d => return Except.ok (some d)\n"
            "  | none   => return Except.error ()",
        ),
        "refinement": "reading a fixed positional offset is the pre-fix "
                      "behavior: when the second argument is a scalar and only "
                      "one argument is a labelled array, the offset lookup is out "
                      "of range and the routine RAISES — the exact out-of-range "
                      "failure the issue reports. The F2P test exercises precisely "
                      "that scalar-second-argument configuration and asserts the "
                      "resolved dictionary is the (empty) one of the second "
                      "argument, so a faithful patch keeping the fixed-offset "
                      "read would still crash and NOT resolve.",
        "rationale": "REJECT from the second conjunct `objs ≠ [] → result = ok "
                     "(some (attrsOf x))`: at cond a labelled array, x and y "
                     "scalars, objs = [cond] and the offset-1 lookup is `none` → "
                     "the rival returns `error ()`, while the spec requires `ok "
                     "(some (attrsOf x)) = ok (some [])`.",
        "witness": (
            "example : ¬ problem_spec_whereAttrs (Arg.darray []) Arg.scalar Arg.scalar\n"
            "    (implementation_whereAttrs (Arg.darray []) Arg.scalar Arg.scalar) := by\n"
            "  rintro ⟨_, h2⟩\n"
            "  have hbad := h2 (by decide)\n"
            "  rw [show implementation_whereAttrs (Arg.darray []) Arg.scalar Arg.scalar\n"
            "        = Except.error () from rfl] at hbad\n"
            "  exact Except.noConfusion hbad\n"
        ),
    },
    {
        "id": "weak-fixed-offset-wrong-selection",
        "kind": "uniqueness",
        "expect": "reject",
        # THE WRONG-SELECTION FACE (the pre-fix behavior, made total by falling
        # back to the correct value when the offset is out of range): read the
        # entry at the fixed positional offset 1 when present, else the second
        # argument's dictionary. Correct exactly when the second argument sits at
        # offset 1 of the labelled-array list, but WRONG when a DIFFERENT labelled
        # argument occupies that offset — e.g. cond labelled, x scalar, y labelled:
        # objs = [cond, y], offset-1 is y's dictionary, not x's (empty) one.
        # Ports nagini case (4) partial-domain-constant-offset-guarded.
        "module": _swap(
            _BASE, _IMPL,
            "  let objs := [cond, x, y].filter (fun a => a.isDarray)\n"
            "  if objs = [] then\n"
            "    return Except.ok none\n"
            "  match (objs.map attrsOf)[1]? with\n"
            "  | some d => return Except.ok (some d)\n"
            "  | none   => return Except.ok (some (attrsOf x))",
        ),
        "refinement": "reading a fixed positional offset returns the SECOND "
                      "argument's dictionary only when the second argument happens "
                      "to sit at that offset of the labelled-array list; when the "
                      "second argument is a scalar but other arguments are "
                      "labelled arrays, the offset selects a DIFFERENT argument's "
                      "dictionary rather than the (empty) one the second argument "
                      "carries — e.g. cond and y labelled with x a scalar, where "
                      "the spec requires the empty dictionary and this rival "
                      "reports y's. HONEST SCOPE (machine-checked by reducing this "
                      "impl at each input): unlike the three other rivals here, "
                      "this one AGREES with the required behavior on both "
                      "configurations the F2P assertions exercise — an "
                      "all-labelled selection (the offset does coincide with the "
                      "second argument) and a selection whose second and third "
                      "arguments are both scalars (the offset is out of range, so "
                      "the fallback returns the second argument's own empty "
                      "dictionary). So the claim for this case is NOT that a "
                      "faithful patch of this shape would fail the F2P: it would "
                      "pass it. The claim is the weaker and still load-bearing "
                      "one that the frozen spec is STRICTLY STRONGER than the F2P "
                      "assertions — it pins the resolved dictionary over the whole "
                      "domain, so it rejects a fixed-offset read that the test "
                      "alone would let through. The sub-domain where the two part "
                      "company (a scalar second argument with a LATER labelled "
                      "argument) is exactly where the witness below refutes it.",
        "rationale": "REJECT from the second conjunct `objs ≠ [] → result = ok "
                     "(some (attrsOf x))`: at cond and y labelled with dictionary "
                     "[(\"k\",\"v\")] and x a scalar, objs = [cond, y] so offset-1 "
                     "is `some [(\"k\",\"v\")]` → the rival returns `ok (some "
                     "[(\"k\",\"v\")])`, while the spec requires `ok (some (attrsOf "
                     "x)) = ok (some [])`.",
        "witness": (
            "example : ¬ problem_spec_whereAttrs (Arg.darray [(\"k\", \"v\")]) Arg.scalar (Arg.darray [(\"k\", \"v\")])\n"
            "    (implementation_whereAttrs (Arg.darray [(\"k\", \"v\")]) Arg.scalar (Arg.darray [(\"k\", \"v\")])) := by\n"
            "  rintro ⟨_, h2⟩\n"
            "  have hbad := h2 (by decide)\n"
            "  rw [show implementation_whereAttrs (Arg.darray [(\"k\", \"v\")]) Arg.scalar (Arg.darray [(\"k\", \"v\")])\n"
            "        = Except.ok (some [(\"k\", \"v\")]) from rfl] at hbad\n"
            "  simp only [attrsOf, Except.ok.injEq, Option.some.injEq] at hbad\n"
            "  exact absurd hbad (by decide)\n"
        ),
    },
    # ---------------------------------------------------------------------
    # The two rivals above are both refuted with the SECOND argument a SCALAR,
    # which leaves the other half of that binder's domain — a second argument
    # that IS a labelled array carrying its own dictionary — unprobed: a rival
    # that resolved the dictionary correctly for a scalar second argument but
    # picked the WRONG labelled argument when the second one is itself labelled
    # would never be caught. The two rivals below close that: each is refuted at
    # a second argument that is a labelled array, one selecting the first
    # positional labelled argument and one the last, so the "which positional
    # argument's dictionary" question is attacked on BOTH sides of the second
    # argument rather than only where its dictionary is forced empty.
    # ---------------------------------------------------------------------
    {
        "id": "weak-first-labelled-selection",
        "kind": "uniqueness",
        "expect": "reject",
        # Resolve to the dictionary of the FIRST labelled argument (the
        # condition, when it is labelled) rather than the second positional
        # argument. Agrees with the spec exactly when the second argument happens
        # to be the first labelled one — which is the case for EVERY input the
        # two rivals above probe (there the second argument is a scalar, so this
        # rival is refuted nowhere they look). Diverges as soon as the condition
        # is labelled and the second argument is a labelled array with a
        # different dictionary.
        "module": _swap(
            _BASE, _IMPL,
            "  let objs := [cond, x, y].filter (fun a => a.isDarray)\n"
            "  if objs = [] then\n"
            "    return Except.ok none\n"
            "  match (objs.map attrsOf)[0]? with\n"
            "  | some d => return Except.ok (some d)\n"
            "  | none   => return Except.ok (some (attrsOf x))",
        ),
        "refinement": "keeping the attributes of the FIRST positional argument "
                      "(the condition) rather than the second is not the "
                      "documented rule and is directly observable: the F2P test "
                      "builds a selection whose condition and second argument are "
                      "both labelled arrays with DIFFERENT attribute "
                      "dictionaries, and asserts the result carries the SECOND "
                      "argument's dictionary. A faithful patch that resolved to "
                      "the condition's dictionary would report the condition's "
                      "attributes there and FAIL that assertion, so it would NOT "
                      "resolve — even though it never raises and is correct on the "
                      "whole scalar-second-argument sub-domain that motivated the "
                      "report.",
        "rationale": "REJECT from the second conjunct `objs ≠ [] → result = ok "
                     "(some (attrsOf x))`: at cond a labelled array with "
                     "dictionary [(\"k\",\"c\")], x a labelled array with "
                     "[(\"k\",\"x\")] and y a scalar, objs = [cond, x] so offset-0 "
                     "is `some [(\"k\",\"c\")]` → the rival returns `ok (some "
                     "[(\"k\",\"c\")])` while the spec requires `ok (some (attrsOf "
                     "x)) = ok (some [(\"k\",\"x\")])`. This is the first rival "
                     "refuted with a NON-scalar second argument, so it is what "
                     "makes the `x` binder load-bearing over its whole domain "
                     "rather than only at the empty-dictionary end.",
        "witness": (
            "example : ¬ problem_spec_whereAttrs (Arg.darray [(\"k\", \"c\")]) (Arg.darray [(\"k\", \"x\")]) Arg.scalar\n"
            "    (implementation_whereAttrs (Arg.darray [(\"k\", \"c\")]) (Arg.darray [(\"k\", \"x\")]) Arg.scalar) := by\n"
            "  rintro ⟨_, h2⟩\n"
            "  have hbad := h2 (by decide)\n"
            "  rw [show implementation_whereAttrs (Arg.darray [(\"k\", \"c\")]) (Arg.darray [(\"k\", \"x\")]) Arg.scalar\n"
            "        = Except.ok (some [(\"k\", \"c\")]) from rfl] at hbad\n"
            "  simp only [attrsOf, Except.ok.injEq, Option.some.injEq] at hbad\n"
            "  exact absurd hbad (by decide)\n"
        ),
    },
    {
        "id": "weak-last-labelled-selection",
        "kind": "uniqueness",
        "expect": "reject",
        # Resolve to the dictionary of the LAST labelled argument (the value
        # chosen where the condition fails, when it is labelled) rather than the
        # second positional argument. The mirror image of the rival above: it too
        # is correct on the whole sub-domain where the second argument is the only
        # labelled argument, and diverges when a LATER argument is labelled as
        # well. Refuted with a labelled second argument.
        "module": _swap(
            _BASE, _IMPL,
            "  let objs := [cond, x, y].filter (fun a => a.isDarray)\n"
            "  if objs = [] then\n"
            "    return Except.ok none\n"
            "  match objs.getLast? with\n"
            "  | some a => return Except.ok (some (attrsOf a))\n"
            "  | none   => return Except.ok (some (attrsOf x))",
        ),
        "refinement": "keeping the attributes of the LAST positional argument "
                      "(the value chosen where the condition does not hold) "
                      "rather than the second inverts the documented rule and is "
                      "directly observable: the F2P test builds a selection whose "
                      "second and third arguments are both labelled arrays with "
                      "DIFFERENT attribute dictionaries and asserts the result "
                      "carries the SECOND argument's. A faithful patch resolving "
                      "to the third argument's dictionary would report the wrong "
                      "one and FAIL, so it would NOT resolve; like the rival "
                      "above it never raises, so the scalar-second-argument "
                      "sub-domain alone cannot expose it.",
        "rationale": "REJECT from the second conjunct `objs ≠ [] → result = ok "
                     "(some (attrsOf x))`: at cond a scalar, x a labelled array "
                     "with [(\"k\",\"x\")] and y a labelled array with "
                     "[(\"k\",\"y\")], objs = [x, y] so the last entry is y → the "
                     "rival returns `ok (some [(\"k\",\"y\")])` while the spec "
                     "requires `ok (some (attrsOf x)) = ok (some [(\"k\",\"x\")])`. "
                     "Also the only reject case whose condition argument is a "
                     "scalar, so `cond` is varied across both of its shapes too.",
        "witness": (
            "example : ¬ problem_spec_whereAttrs Arg.scalar (Arg.darray [(\"k\", \"x\")]) (Arg.darray [(\"k\", \"y\")])\n"
            "    (implementation_whereAttrs Arg.scalar (Arg.darray [(\"k\", \"x\")]) (Arg.darray [(\"k\", \"y\")])) := by\n"
            "  rintro ⟨_, h2⟩\n"
            "  have hbad := h2 (by decide)\n"
            "  rw [show implementation_whereAttrs Arg.scalar (Arg.darray [(\"k\", \"x\")]) (Arg.darray [(\"k\", \"y\")])\n"
            "        = Except.ok (some [(\"k\", \"y\")]) from rfl] at hbad\n"
            "  simp only [attrsOf, Except.ok.injEq, Option.some.injEq] at hbad\n"
            "  exact absurd hbad (by decide)\n"
        ),
    },
    # ---------------------------------------------------------------------
    # All four rivals above are refuted from the SECOND conjunct, which leaves
    # the FIRST conjunct (`objs = [] → result = ok none`, the "nothing to merge"
    # short-circuit) with no rival attacking it at all: every one of them keeps
    # that branch byte-identical to the frozen impl, so a spec that had dropped
    # or weakened the first conjunct would have been refuted by none of them.
    # The rival below closes that: it collapses the two distinguishable
    # no-attributes outcomes — "there was nothing to merge" (`none`) and "the
    # merge resolved to an empty dictionary" (`some []`) — which is the one
    # distinction the first conjunct exists to make, and which the carrier keeps
    # observable (`Option Attrs`, so `none ≠ some []`).
    # ---------------------------------------------------------------------
    {
        "id": "weak-empty-dict-for-no-arrays",
        "kind": "uniqueness",
        "expect": "reject",
        # Return an empty resolved dictionary instead of "no attributes" when no
        # argument is a labelled array. Agrees with the frozen impl on every
        # input where ANY argument is labelled (so all four rivals above, and
        # both configurations the F2P assertions exercise, cannot see it), and
        # diverges exactly on the all-scalar input the first conjunct governs.
        "module": _swap(
            _BASE, _IMPL,
            "  let objs := [cond, x, y].filter (fun a => a.isDarray)\n"
            "  if objs = [] then\n"
            "    return Except.ok (some [])\n"
            "  return Except.ok (some (attrsOf x))",
        ),
        "refinement": "the two outcomes this rival collapses are distinct in the "
                      "modeled result type and distinct in the behavior being "
                      "defended: 'no labelled argument, so there was nothing to "
                      "merge and no attribute dictionary was produced at all' is "
                      "not the same observable as 'a dictionary was resolved and it "
                      "happens to be empty'. A faithful patch of this shape would "
                      "report an attribute dictionary for a selection built purely "
                      "from bare scalars, where the surrounding routine's "
                      "short-circuit yields no attributes without ever consulting "
                      "the preservation rule. HONEST SCOPE: this configuration is "
                      "not one the F2P assertions exercise (both of them keep at "
                      "least one labelled argument), so this rival is admitted for "
                      "CLAUSE COVERAGE of the first conjunct rather than as an F2P "
                      "near-miss — it is the only case in this battery whose "
                      "refutation does not go through the second conjunct.",
        "rationale": "REJECT from the FIRST conjunct `objs = [] → result = ok "
                     "none`: at all three arguments scalars, objs = [] so the spec "
                     "requires `ok none`, while the rival returns `ok (some [])`. "
                     "This is the only reject case that loads the first conjunct; "
                     "every other rival leaves the empty-objs branch identical to "
                     "the frozen one, so without this case a spec missing its "
                     "short-circuit clause would be refuted by nothing here.",
        "witness": (
            "example : ¬ problem_spec_whereAttrs Arg.scalar Arg.scalar Arg.scalar\n"
            "    (implementation_whereAttrs Arg.scalar Arg.scalar Arg.scalar) := by\n"
            "  rintro ⟨h1, _⟩\n"
            "  have hbad := h1 (by decide)\n"
            "  rw [show implementation_whereAttrs Arg.scalar Arg.scalar Arg.scalar\n"
            "        = Except.ok (some []) from rfl] at hbad\n"
            "  simp at hbad\n"
        ),
    },
]
