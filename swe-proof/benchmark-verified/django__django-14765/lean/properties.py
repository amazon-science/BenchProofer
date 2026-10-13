"""properties.py — G-PBT falsification battery for django__django-14765 (lean).

NOT a Lean file; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region — and, for a case that legitimately re-proves, inside the
``-- proof-start`` / ``-- proof-end`` region — is changed, so
``markers.same_spec`` holds and the ``theorem correct_initRealApps`` STATEMENT
stays byte-identical). ``expect:"verify"`` passes iff (in scope AND the file
elaborates with the obligation closed, no ``sorry``/``admit``/``native_decide``
and no new ``axiom``/``theorem``); ``expect:"reject"`` passes iff (in scope AND
it does NOT verify AND the case's refutation ``witness`` holds of the rival while
FAILING on the frozen solution).

DEFENDED SURFACE (one modeled behavior; a single input binder ``arg``). The
argument describing a collection of application labels has three shapes, and the
produced collection is pinned case-by-case:

  initRealApps (arg : RealAppsArg) : Except Unit (List String)
    | absent   => Except.ok []      -- no value supplied → the empty collection
    | isSet xs => Except.ok xs       -- already a set → taken unchanged
    | nonSet _ => Except.error ()    -- any other collection → rejected, no value

The binder ``arg`` varies along TWO axes the rivals must exercise: its
constructor TAG (absent / isSet / nonSet), and the element list it CARRIES
(``elems`` — empty vs non-empty). Every top-level clause of the postcondition is
one match arm, and each is attacked by some rival; the witnesses probe all three
tags and both the empty and non-empty carried-list settings.

ADVERSARIAL READ of the nagini classes on this carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS, and DEMONSTRATED so rather than
    asserted. The nagini sibling holds the input at a half-permission
    (read-only) and makes its MANDATORY frame-mutation rival write to it. Lean is
    referentially transparent: the argument carries no heap permission, there is
    no read-only fraction to overwrite and no aliasing to exploit. The audit
    transliterated that rival anyway — a variant that binds a local copy of the
    argument, WRITES a corrupted value into it (``mutArg := .isSet (arg.elems ++
    ["injected"])``), and then computes the correct result from ``arg`` — and
    built it: it VERIFIES (exit 0) under the frozen tactic body. That is the
    demonstration, not an argument: the strongest available write to the argument
    is invisible to the obligation, so the class has no falsifying instance here
    and NO substitute is fabricated for it (see ``assessment``).

  * UNGROUNDED-ORACLE ECHO — VACUOUS. The postcondition is grounded in the
    argument (each arm equates the result to a term built only from ``arg``); the
    bundle declares no ``opaque``/``axiom``, so there is no answer key to echo.
    In its place the battery carries honest POSITIVE CONTROLS (``pos-*``) that
    must verify.

  * CONTROL-FLOW-EFFECT / PARTIAL-DOMAIN — APPLIES. The nagini rivals attack the
    discriminating "a present off-kind collection must be rejected, never coerced
    to a value" clause, the raise-for-EVERY-off-kind-collection (empty or not)
    clause, and the membership-preservation clause. Each maps to a match arm
    here: coercing ``nonSet`` to a value, rejecting only a NON-EMPTY ``nonSet``,
    and truncating the ``isSet`` membership. A fourth rival attacks the
    ``absent`` arm (which nagini pins as ``len(Result())==0`` and never attacks
    with a wrong-branch rival) so that arm is defended too.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen ``cases arg <;> rfl`` is tuned to the
frozen match — so a rejection alone attributes nothing to the spec. Every
``expect="reject"`` case therefore carries a Lean snippet proving the rival
CONTRADICTS the spec at one concrete input. Each was checked to hold of its rival
and to FAIL on the frozen solution (so it discriminates rather than asserting a
tautology).

That check alone is not sufficient, and an audit of this battery established why
with real builds. "Fails on gold" is evidence only if the failure TRACKS THE
CLAIM. Three witnesses here originally closed by ``unfold ... ; simp [Id.run]``,
and ``simp [Id.run]`` cannot discharge the ``pure X = X`` residue the frozen
``Id.run do`` carrier leaves: they failed on gold with ``unsolved goals ⊢ ¬pure
(Except.error ()) = Except.error ()`` — and a FORGERY differing only in dropping
the ``¬`` (i.e. claiming the spec HOLDS at that input, which of gold it does)
failed with the byte-identical stall. Confirmed independently: the spec instance
``problem_spec_initRealApps .absent (implementation_initRealApps .absent)``, which
is TRUE of gold, also fails on gold under that tactic. Gold's exit code carried
no information about the claim, so those three rejections attested to a tactic
gap, not to the spec.

Bare ``rfl`` DOES reduce this carrier (``implementation_initRealApps .absent =
Except.ok []`` closes by ``rfl``); what fails is ``decide`` (``Except Unit _`` has
no ``DecidableEq`` instance) and ``simp [Id.run]``. So every witness now pins the
rival's output with ``show <impl at the input> = <the rival's value> from rfl``
and refutes the resulting equality. Re-measured per case: rival exit 0, gold exit
1 with a ``Type mismatch rfl ... = <the rival's value>`` naming the concrete value
gold does NOT produce, and the flipped-claim forgery exit 0 on gold. The error
changes with the claim on both sides, which is what makes these discriminators.

SECOND (INDEPENDENT) AUDIT — what was re-derived from scratch, and what changed.
Every claim below is a build the auditor ran, not a reading of the record:

  * STATEMENT INTEGRITY. All cases' `theorem correct_initRealApps` statements are
    byte-identical to the frozen one, and the `axioms`/`pure`/`post-conditions`
    regions are byte-identical too; only `impl` (all 8 rivals/positives) and
    `proof` (`pos-append-nil-not-defeq`, `admiss-f2p-ground-instance`) differ.
    No reformatted hypothesis anywhere.

  * THE FOUR ORIGINAL WITNESSES RE-BUILT, plus the FORGERY PAIR for each (the
    gold signature is a `Type mismatch`, not a plain evaluation, so B′ is
    mandatory). Rival 0 / gold 1 on all four, matching the record. The forgery
    is decisive in BOTH available forms: flipping the claim (asserting the spec
    HOLDS at the witness input) builds on gold (exit 0) and FAILS on the rival
    (exit 1, `Tactic 'rfl' failed ... is not definitionally equal to ...`); and
    pinning GOLD's value at the same input by `rfl` likewise builds on gold (0)
    and fails on the rival (1). The exit code inverts with the claim on both
    sides, so these are refutations rather than tactic gaps.

  * THE PRIOR AUDIT'S HOLLOWNESS FINDING INDEPENDENTLY REPRODUCED. The pre-repair
    `simp [Id.run]` witness was rebuilt: on gold it fails `unsolved goals ⊢ ¬pure
    (Except.error ()) = Except.error ()`, and the flip (dropping the `¬`) fails
    with `⊢ pure (Except.error ()) = Except.error ()` — same tactic stall, so the
    old exit code indeed carried no information about the claim. The repair to
    `show ... from rfl` was necessary and is confirmed sufficient.

  * RIVALS ARE OBSERVABLY WRONG, not merely reshaped. Each rival differs from
    gold at a CONCRETE input in the produced value (`ok [...]` vs `error ()`, or
    a strictly shorter element list), which is what the witness builds pin. None
    is definitionally equal to gold on this carrier.

  * A FALSE RATIONALE CLAUSE WAS CORRECTED (not a build failure — a prose defect
    the gate cannot see). `weak-reject-nonempty-only` claimed "the coerce rival
    cannot be refuted here". Measured the cross-product: this case's empty-nonSet
    witness DOES refute the coerce rival (exit 0). The corrected text states the
    real relation, itself measured — the containment runs one way only (the
    coerce case's non-empty witness does NOT refute this rival, exit 1).

  * A COVERAGE GAP WAS CLOSED. The (tag × carried-list-emptiness) grid the
    docstring claims to span was missing the isSet arm's EMPTY setting; every
    shipped rival agrees with gold there. `weak-isSet-empty-rejects` was added
    for it, with its own forgery pair measured (see that case).

  * SPEC-TOO-WEAK PROBES (4 NEW wrong impls, none shipped as a case — all were
    correctly REJECTED, so none is a spec hole): permuting the stored membership
    (`xs.reverse`, residual goal `elems✝.reverse = elems✝`), deduplicating it
    (`xs.eraseDups`), rejecting the empty already-a-set argument, and returning a
    sentinel element for an absent argument (residual goal `False`). Each was
    given the frozen tactic plus `simp`/`unfold` fallbacks; every one left an
    unsolved goal naming exactly its deviation. Note the first two are rejected
    because the postcondition pins the element LIST, which is stricter than the
    set semantics `mapping.md` declares — this makes the spec strictly harder to
    satisfy, never easier, so it is not a hole (and G-CONF compares as sets).

  * SPEC-TOO-STRONG PROBES (3 NEW correct reshapes; the spec accepted every one
    it could express). Dispatching through the carrier's own projection
    (`| .nonSet _ => error | a => ok a.elems`) VERIFIES under the frozen tactic;
    rebuilding the membership with `List.foldr` — propositionally but NOT
    definitionally equal, so the frozen `rfl` genuinely fails — VERIFIES once the
    isSet arm goes through `simp`. A third reshape (a decidable guard over a
    `match ... => True/False` predicate) failed to elaborate for a reason that is
    not about the spec at all (`failed to synthesize Decidable (match arg with
    ...)`, cascading into `sorry () = Except.ok []`): a missing instance in the
    reshape as written, not a rejection of a faithful impl. Marked inconclusive
    rather than counted as a hole.

  * THE ADMISSIBILITY CASE IS DISCRIMINATING, checked by mutation rather than
    assumed: replacing its ground `have` with a FALSE instance at the same input
    (claiming the off-kind collection yields `ok ["contenttypes"]`) makes the file
    FAIL (exit 1, `rfl` failed, `Except.ok ["contenttypes"]` vs `Except.error ()`).
    So the `have` is really being checked. The same shape at a second point (an
    already-a-set argument carrying two labels) also discharges (exit 0).

  * `pos-append-nil-not-defeq` IS NON-TRIVIAL, checked directly: the same impl
    under the FROZEN tactic body fails (exit 1, `RealAppsArg.isSet elems✝ is not
    definitionally equal to ...`), so its re-proof is genuine work and not
    inherited definitional equality.

  * THE FRAME-MUTATION VACUITY CLAIM WAS RE-DERIVED, not taken on faith: the
    transliterated write-to-the-argument rival was rebuilt and it VERIFIES
    (exit 0). The class genuinely has no falsifying instance here.

AXIOM lane: EMPTY. meta.json axioms == [] and deep_model_references == []; the
modeled behavior is a total computation over the argument's own tag and elements,
so there is no axiom-soundness obligation to probe here (that lane is G-AX's).
AXIOM_TESTS is therefore omitted.
"""
from pathlib import Path

INSTANCE = "django__django-14765"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- region anchors (each unique inside Solution.lean; verified at load) ----
# The three-arm match is the load-bearing shape of the impl region; every impl
# reshape lands entirely inside `-- impl-start`/`-- impl-end`.
_MATCH = (
    "  match arg with\n"
    "  | .absent    => realApps := []          -- absent argument: start from the empty collection\n"
    "  | .isSet xs  => realApps := xs           -- already a set: keep it as-is\n"
    "  | .nonSet _  => return Except.error ()   -- any other collection: reject before assigning\n"
)
# Full impl def — anchor for the functional-reshape positive that drops the
# `Id.run do` scaffold entirely.
_FULL_IMPL = (
    "def implementation_initRealApps (arg : RealAppsArg) : Except Unit (List String) :=\n"
    "  Id.run do\n"
    "  let mut realApps : List String := arg.elems\n"
    + _MATCH
    + "  return Except.ok realApps\n"
)
# Frozen tactic body (only the proof region may also change).
_PROOF = "  intro arg\n  cases arg <;> rfl\n"


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # implementations that MUST verify. If a faithful correct implementation
    # cannot satisfy the frozen obligation the spec is SPEC-TOO-STRONG. Each
    # keeps the `theorem correct_initRealApps` statement byte-identical; the
    # frozen `cases arg <;> rfl` still closes both shapes (each arm is
    # definitionally the frozen result), so no proof authoring is needed and no
    # helper lemma, axiom, or assumption token is introduced.
    # =====================================================================
    {
        "id": "pos-direct-match",
        "kind": "soundness",
        "expect": "verify",
        # Functional reshape: drop the `Id.run do`/`let mut` scaffold and return
        # each arm's value directly. Observationally identical on every argument
        # shape, so the frozen `cases arg <;> rfl` still closes.
        "module": _swap(
            _BASE, _FULL_IMPL,
            "def implementation_initRealApps (arg : RealAppsArg) : Except Unit (List String) :=\n"
            "  match arg with\n"
            "  | .absent    => Except.ok []\n"
            "  | .isSet xs  => Except.ok xs\n"
            "  | .nonSet _  => Except.error ()\n",
        ),
        "rationale": "a correct reshape of the mutable-accumulator loop into a "
                     "direct per-arm return computes the same value on every "
                     "argument shape (absent → ok [], isSet xs → ok xs, nonSet → "
                     "error ()), so it must satisfy the postcondition; if it "
                     "cannot, the spec is SPEC-TOO-STRONG. Proof: the frozen "
                     "tactic body (`cases arg <;> rfl`) still closes — each arm is "
                     "now definitionally the frozen result.",
    },
    {
        "id": "pos-reorder-arms",
        "kind": "soundness",
        "expect": "verify",
        # Branch reorder: decide the reject case first, then the two value cases.
        # `match` is unordered over disjoint constructors, so the value flow into
        # each arm is unchanged.
        "module": _swap(
            _BASE, _MATCH,
            "  match arg with\n"
            "  | .nonSet _  => return Except.error ()   -- any other collection: reject before assigning\n"
            "  | .absent    => realApps := []          -- absent argument: start from the empty collection\n"
            "  | .isSet xs  => realApps := xs           -- already a set: keep it as-is\n",
        ),
        "rationale": "reordering the match arms over disjoint constructors "
                     "preserves the exact per-shape result, so the postcondition "
                     "still holds; must verify (else SPEC-TOO-STRONG). Proof: the "
                     "frozen tactic body (`cases arg <;> rfl`) closes all three "
                     "cases regardless of arm order.",
    },

    {
        "id": "pos-append-nil-not-defeq",
        "kind": "soundness",
        "expect": "verify",
        # AUDIT ADDITION. The two positives above are closed by the FROZEN
        # `cases arg <;> rfl`, i.e. each arm is DEFINITIONALLY the frozen result;
        # a positive that rides definitional equality passes honestly while
        # exercising nothing. This one does not: the `isSet` arm returns
        # `xs ++ []`, which is only PROPOSITIONALLY equal to `xs`, so the frozen
        # tactic body genuinely fails on it (measured: `Tactic 'rfl' failed ...
        # RealAppsArg.isSet elems✝ is not definitionally equal to ...`) and the
        # case has to re-prove the obligation through the spec predicate. That
        # makes it a real SPEC-TOO-STRONG probe rather than a restatement.
        "module": _swap(
            _swap(
                _BASE, _FULL_IMPL,
                "def implementation_initRealApps (arg : RealAppsArg) : Except Unit (List String) :=\n"
                "  match arg with\n"
                "  | .absent    => Except.ok ([] ++ [])\n"
                "  | .isSet xs  => Except.ok (xs ++ [])\n"
                "  | .nonSet _  => Except.error ()\n",
            ),
            _PROOF,
            "  intro arg\n"
            "  cases arg with\n"
            "  | absent => rfl\n"
            "  | isSet xs => simp [problem_spec_initRealApps, implementation_initRealApps]\n"
            "  | nonSet xs => rfl\n",
        ),
        "rationale": "appending the empty collection to the supplied elements "
                     "returns the same membership, so this is a faithful correct "
                     "impl and MUST verify (else SPEC-TOO-STRONG). Unlike the two "
                     "positives above it is NOT definitionally equal to the frozen "
                     "impl on the `isSet` arm — the frozen `rfl` fails on it — so "
                     "the obligation is genuinely re-discharged rather than "
                     "inherited: the `isSet` case is closed by `simp` through the "
                     "spec predicate. No new declaration, statement byte-identical.",
    },

    # =====================================================================
    # ADMISSIBILITY — a positive control confirming the obligation is
    # SATISFIABLE (non-vacuous) at the normal F2P-shaped input rather than only
    # provable in the abstract. The frozen theorem carries NO precondition
    # hypothesis (the modeled behavior is total, so `∀` is unguarded), which
    # means the nagini precondition-admission probe has no binder to attack; the
    # honest analogue is to discharge the spec predicate at a ground F2P input (a
    # present off-kind collection — the exact input the F2P test exercises) by
    # `rfl`, inside the proof region, alongside the frozen obligation. If that
    # ground instance could not be discharged the modeled behavior would be
    # unsatisfiable at the input the F2P asserts about (the analogue of
    # PRECOND-TOO-STRONG).
    # =====================================================================
    {
        "id": "admiss-f2p-ground-instance",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _PROOF,
            "  have _ground : problem_spec_initRealApps (.nonSet [\"contenttypes\"])\n"
            "      (implementation_initRealApps (.nonSet [\"contenttypes\"])) := by\n"
            "    unfold problem_spec_initRealApps\n"
            "    rfl\n"
            + _PROOF,
        ),
        "rationale": "the obligation is discharged at the ground F2P input (a "
                     "present off-kind collection, which must be rejected) by "
                     "`rfl`, then the frozen obligation is closed verbatim. "
                     "Verifies (else the spec is unsatisfiable at the normal "
                     "input, the analogue of PRECOND-TOO-STRONG). Nothing is "
                     "assumed: no new declaration, the theorem statement is "
                     "byte-identical, and the ground instance is a `have` inside "
                     "the existing tactic body.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong implementations sharing the
    # frozen spec that MUST be rejected. Each carries (a) the refinement
    # argument that its faithful real patch would NOT resolve the F2P, so a
    # verifying rival would be a true verify-does-not-imply-resolve break, and
    # (b) a refutation witness pinning the violation at one concrete input. The
    # four witnesses spread the binder across all three constructor tags and
    # both the empty and non-empty carried-list settings.
    # =====================================================================
    {
        "id": "weak-coerce-offkind",
        "kind": "uniqueness",
        "expect": "reject",
        # The pre-patch behavior: a present off-kind collection is silently
        # coerced to a value and returned, instead of being rejected.
        "module": _swap(
            _BASE, _MATCH,
            "  match arg with\n"
            "  | .absent    => realApps := []\n"
            "  | .isSet xs  => realApps := xs\n"
            "  | .nonSet xs => realApps := xs           -- coerce any other collection instead of rejecting\n",
        ),
        "refinement": "coercing a present off-kind collection to a value and "
                      "returning it normally is exactly the pre-patch behavior: "
                      "the F2P test constructs one from an off-kind collection and "
                      "asserts the construction ABORTS. A patch that returns "
                      "normally there leaves the F2P failing → would NOT resolve; "
                      "this is the leg's prepatch.",
        "rationale": "REJECT from the `nonSet _ => Except.error ()` arm: at a "
                     "present off-kind collection the spec requires `error ()` and "
                     "the rival returns `ok _`. Refuted at a NON-EMPTY off-kind "
                     "collection — the tag under attack with a populated carried "
                     "list.",
        # AUDIT REPAIR: the original witness closed by `simp [Id.run]`, which
        # cannot discharge the `pure X = X` residue the `Id.run do` carrier
        # leaves. Measured: it fails on gold with `unsolved goals ⊢ ¬pure
        # (Except.error ()) = Except.error ()` — and the FORGERY that drops the
        # `¬` (claiming the spec HOLDS here, which of gold it does) fails with
        # the same tactic stall, `⊢ pure (Except.error ()) = Except.error ()`.
        # Gold's exit code therefore carried no information about the claim.
        # Bare `rfl` DOES reduce this carrier, so the rival's value is pinned by
        # `show ... from rfl` and the equation refuted from there. Re-measured:
        # rival 0, gold 1 (`Type mismatch rfl ... = Except.ok ["contenttypes"]`),
        # flipped-claim forgery 0 on gold — the error now tracks the claim.
        "witness": (
            "example : ¬ problem_spec_initRealApps (.nonSet [\"contenttypes\"])\n"
            "    (implementation_initRealApps (.nonSet [\"contenttypes\"])) := by\n"
            "  intro h\n"
            "  rw [show implementation_initRealApps (RealAppsArg.nonSet [\"contenttypes\"])\n"
            "        = Except.ok [\"contenttypes\"] from rfl,\n"
            "     problem_spec_initRealApps] at h\n"
            "  simp at h\n"
        ),
    },
    {
        "id": "weak-reject-nonempty-only",
        "kind": "uniqueness",
        "expect": "reject",
        # Rejects a present off-kind collection ONLY when it is non-empty; an
        # empty off-kind collection falls through and returns a value. Mirrors
        # the real truthiness blind spot (`if real_apps:` is false for an empty
        # non-set, so it slips past the kind check).
        "module": _swap(
            _BASE, _MATCH,
            "  match arg with\n"
            "  | .absent    => realApps := []\n"
            "  | .isSet xs  => realApps := xs\n"
            "  | .nonSet xs => if xs.length > 0 then return Except.error ()   -- reject only a non-empty other collection\n",
        ),
        "refinement": "a patch that rejects a present off-kind collection only "
                      "when non-empty (a truthiness guard rather than an is-a-set "
                      "check) silently accepts an EMPTY off-kind collection, "
                      "diverging from the intended 'a present non-set ALWAYS "
                      "aborts' contract on that sub-domain → not the faithful fix, "
                      "would NOT resolve on the empty-off-kind case.",
        "rationale": "REJECT from the `nonSet _ => Except.error ()` arm on the "
                     "sub-domain nonSet with an EMPTY carried list: the rival "
                     "falls through and returns `ok []`, but the spec pins "
                     "`error ()` for EVERY off-kind collection. This probes the "
                     "same nonSet tag as `weak-coerce-offkind` but at the EMPTY "
                     "carried-list setting, so the carried-list binder is varied "
                     "across the two nonSet rivals. What separates the two rivals "
                     "is the DIRECTION of containment, not which witness refutes "
                     "which: measured, this case's empty-nonSet witness ALSO "
                     "refutes the coerce rival (exit 0 — the coerce rival returns "
                     "`ok []` there too), while the coerce case's NON-EMPTY witness "
                     "does NOT refute this rival (exit 1, `Type mismatch rfl ... = "
                     "Except.ok [\"contenttypes\"]` — this rival correctly returns "
                     "`error ()` on a non-empty off-kind collection). So this rival "
                     "is strictly WEAKER-DEVIATING than the coerce rival: it agrees "
                     "with the spec everywhere the coerce rival disagrees except on "
                     "the empty-off-kind sub-domain, which is precisely the "
                     "truthiness blind spot only this case pins.",
        # AUDIT REPAIR: same hollow shape as `weak-coerce-offkind` (the shipped
        # `simp [Id.run]` witness and its flipped-claim forgery BOTH failed on
        # gold with the identical `pure (Except.error ()) = Except.error ()`
        # stall). Repinned via `show ... from rfl`. Re-measured: rival 0, gold 1
        # (`Type mismatch rfl ... = Except.ok []`), forgery 0 on gold.
        "witness": (
            "example : ¬ problem_spec_initRealApps (.nonSet [])\n"
            "    (implementation_initRealApps (.nonSet [])) := by\n"
            "  intro h\n"
            "  rw [show implementation_initRealApps (RealAppsArg.nonSet [])\n"
            "        = Except.ok ([] : List String) from rfl,\n"
            "     problem_spec_initRealApps] at h\n"
            "  simp at h\n"
        ),
    },
    {
        "id": "weak-drop-last-membership",
        "kind": "uniqueness",
        "expect": "reject",
        # Truncates the stored membership of an already-a-set argument: drops its
        # final element. Correct on empty/absent/off-kind, wrong for any set with
        # >= 1 element.
        "module": _swap(
            _BASE, _MATCH,
            "  match arg with\n"
            "  | .absent    => realApps := []\n"
            "  | .isSet xs  => realApps := xs.dropLast  -- drops the final element of the set\n"
            "  | .nonSet _  => return Except.error ()\n",
        ),
        "refinement": "storing a strict subset of the supplied set (dropping one "
                      "label) means a downstream consumer that relies on the full "
                      "membership (equality / rendering of the state's real_apps) "
                      "sees a registered label missing; the P2P cases that build a "
                      "state from a non-trivial set and rely on its complete "
                      "membership FAIL → would NOT resolve.",
        "rationale": "REJECT from the `isSet xs => Except.ok xs` arm: for a set "
                     "with >= 1 element the rival stores a strict prefix, so "
                     "`result ≠ ok xs`. Refuted at the isSet tag with a non-empty "
                     "carried list — the only tag the membership clause "
                     "constrains, and a setting no other rival probes.",
        "witness": (
            # `Except Unit _` has no DecidableEq instance, so reduce the impl to
            # its concrete `ok`-value by `rfl` inside a `show`, then refute the
            # resulting `List String` equality by `decide`. The `show ... from
            # rfl` FAILS against gold (gold's impl returns `ok [\"a\", \"b\"]`,
            # not `ok [\"a\"]`), which is exactly what makes this discriminate.
            "example : ¬ problem_spec_initRealApps (.isSet [\"a\", \"b\"])\n"
            "    (implementation_initRealApps (.isSet [\"a\", \"b\"])) := by\n"
            "  intro h\n"
            "  rw [show implementation_initRealApps (RealAppsArg.isSet [\"a\", \"b\"]) = Except.ok [\"a\"] from rfl,\n"
            "     problem_spec_initRealApps, Except.ok.injEq] at h\n"
            "  exact absurd h (by decide)\n"
        ),
    },
    {
        # SECOND-AUDIT ADDITION. Coverage gap found by enumerating the (tag ×
        # carried-list-emptiness) grid the docstring claims the battery spans.
        # Before this case the grid was: nonSet non-empty (coerce), nonSet empty
        # (reject-nonempty-only), isSet NON-empty (drop-last), absent
        # (absent-rejects) — leaving the isSet arm's EMPTY carried-list setting
        # entirely unattacked. That corner is not cosmetic: an empty already-a-set
        # argument is exactly where a truthiness guard on the OTHER side of the
        # kind check misfires (an empty set is falsy too), so the arm that must
        # take a supplied set unchanged is untested precisely where the supplied
        # set is falsy. Every existing rival returns `ok []` there, agreeing with
        # gold, so none of them can reach it.
        "id": "weak-isSet-empty-rejects",
        "kind": "uniqueness",
        "expect": "reject",
        # Rejects an already-a-set argument when it carries NO elements, instead
        # of taking it unchanged as the empty collection.
        "module": _swap(
            _BASE, _MATCH,
            "  match arg with\n"
            "  | .absent    => realApps := []\n"
            "  | .isSet xs  => if xs.isEmpty then return Except.error () else realApps := xs   -- reject an EMPTY already-a-set argument\n"
            "  | .nonSet _  => return Except.error ()\n",
        ),
        "refinement": "a patch that guards the supplied-collection branch on "
                      "truthiness rather than on presence aborts when an EMPTY "
                      "collection of the expected kind is supplied — a construction "
                      "that must succeed and yield the empty collection. The P2P "
                      "paths that build a state from an expected-kind collection "
                      "which happens to carry no labels would abort instead of "
                      "constructing → would NOT resolve.",
        "rationale": "REJECT from the `isSet xs => Except.ok xs` arm at the EMPTY "
                     "carried-list setting: the spec pins `ok []` there (`xs` is "
                     "`[]`) and the rival returns `error ()`. This is the one "
                     "(tag × carried-list-emptiness) cell no other rival reaches — "
                     "`weak-drop-last-membership` attacks the same arm but only "
                     "with a NON-EMPTY list (its `dropLast` agrees with the spec on "
                     "`[]`), and both nonSet rivals plus `weak-absent-rejects` "
                     "leave the isSet arm's empty case correct. Measured: the "
                     "witness holds of this rival (exit 0) and fails on the frozen "
                     "solution (exit 1, `Type mismatch rfl ... = Except.error ()`), "
                     "and the flipped-claim forgery — asserting the spec HOLDS at "
                     "this input — builds on gold (exit 0) while FAILING on this "
                     "rival (exit 1), so the error tracks the claim on both sides.",
        "witness": (
            # Same pinning discipline as the other rejects: bare `rfl` reduces
            # this carrier, so pin the rival's value at the input with
            # `show ... from rfl` and refute the resulting equation. The `show`
            # is what fails on gold (gold returns `ok []`, not `error ()`).
            "example : ¬ problem_spec_initRealApps (.isSet ([] : List String))\n"
            "    (implementation_initRealApps (.isSet ([] : List String))) := by\n"
            "  intro h\n"
            "  rw [show implementation_initRealApps (RealAppsArg.isSet ([] : List String))\n"
            "        = Except.error () from rfl,\n"
            "     problem_spec_initRealApps] at h\n"
            "  simp at h\n"
        ),
    },
    {
        "id": "weak-absent-rejects",
        "kind": "uniqueness",
        "expect": "reject",
        # Rejects an ABSENT argument instead of producing the empty collection.
        # Defends the absent arm, which the nagini positives pin but no nagini
        # rival attacks with a wrong-branch impl.
        "module": _swap(
            _BASE, _MATCH,
            "  match arg with\n"
            "  | .absent    => return Except.error ()   -- reject when no value supplied\n"
            "  | .isSet xs  => realApps := xs\n"
            "  | .nonSet _  => return Except.error ()\n",
        ),
        "refinement": "rejecting an absent argument aborts the default "
                      "construction (no collection supplied), which every P2P "
                      "path that builds a state without an explicit collection "
                      "relies on — the overwhelming common case; the construction "
                      "would abort where it must yield the empty collection → "
                      "would NOT resolve.",
        "rationale": "REJECT from the `absent => Except.ok []` arm: at an absent "
                     "argument the spec requires `ok []` and the rival returns "
                     "`error ()`. Refuted at the absent tag (carried list is `[]` "
                     "by definition), the third constructor and the only one the "
                     "other rivals leave untouched.",
        # AUDIT REPAIR: same hollow shape again (shipped witness and its
        # flipped-claim forgery BOTH failed on gold with `pure (Except.ok []) =
        # Except.ok []`). Repinned via `show ... from rfl`. Re-measured: rival 0,
        # gold 1 (`Type mismatch rfl ... = Except.error ()`), forgery 0 on gold.
        "witness": (
            "example : ¬ problem_spec_initRealApps .absent\n"
            "    (implementation_initRealApps .absent) := by\n"
            "  intro h\n"
            "  rw [show implementation_initRealApps RealAppsArg.absent\n"
            "        = Except.error () from rfl,\n"
            "     problem_spec_initRealApps] at h\n"
            "  simp at h\n"
        ),
    },
]
