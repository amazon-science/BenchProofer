"""properties.py — G-PBT falsification battery for django__django-15987 (lean).

NOT a Lean file; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region — and, for a case that legitimately re-proves, inside the
``-- proof-start`` / ``-- proof-end`` region — is changed, so
``markers.same_spec`` holds and the single ``theorem correct_<name>`` STATEMENT
stays byte-identical). ``expect:"verify"`` passes iff (in scope AND the file
elaborates with the obligation closed); ``expect:"reject"`` passes iff (in scope
AND it does NOT verify AND the case's refutation ``witness`` holds of the rival
while FAILING on the frozen solution).

PORT NOTE. This is a PORT of the nagini falsification battery (see
``../nagini/properties.py``) onto this backend's carrier. The nagini bundle
contracts a per-entry presence accumulator over two read-only parallel input
lists (``value_matches``, ``is_path_object``) with fractional-permission frame
clauses, and pins the boolean result to a front-recursive disjunction fold
``any_match``. This Lean bundle models the SAME modeled behavior at a slightly
higher altitude: ONE purely-functional core that, given the configured
directories and the installed components (each carrying its intrinsic default
directory), returns the FIRST component whose default directory collides with
some configured directory (by textual form, independent of how the configured
entry was supplied), or ``none``. Most nagini cases therefore carry over as
attacks on this single modeled obligation; the mapping of each nagini case to
its Lean counterpart (or its principled omission) is in the ``assessment``.

DEFENDED SURFACE (one modeled behavior). The postcondition pins ``result`` to a
single grounded computation over the inputs — the first-match scan over the
components using the textual-form membership test. Its independent facets,
selected by the input:

  * a collision is detected whenever a configured entry's textual form coincides
    with a component's default directory, REGARDLESS of the entry's supplied
    form (plain text vs structured location object) — this is the CHANGED
    behavioral discriminator: the type tag of the configured entry must NOT
    suppress a textual match;
  * the FIRST colliding component in iteration order is the one identified (not
    the last, not an arbitrary one);
  * EVERY configured entry participates in the membership test (not just the
    first, not just the tail);
  * ``none`` iff no component collides with any configured entry.

The BEHAVIORAL DISCRIMINATOR (the fix): a configured entry supplied as a
structured location object whose textual form equals a component's default
directory MUST count as a collision — the pre-fix behavior compared supplied
forms directly and let a structured-object entry escape the textual match. The
first uniqueness rival below IS that pre-fix behavior.

ADVERSARIAL READ of the case classes on this carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS. Lean is referentially transparent: an
    input list carries no heap permission, there is no read-only half-permission
    to overwrite and no aliasing to exploit. The two nagini frame-mutation
    rivals (write into ``value_matches`` / ``is_path_object``) have no
    expressible instance here — a Lean ``def`` argument cannot be mutated — so no
    substitute is fabricated. (nagini cases frame-mutation-write-value_matches,
    frame-mutation-write-is_path_object.)

  * DIVERGENCE / NON-TERMINATION — VACUOUS on lean. ``implementation_*`` is a
    total Lean ``def`` (a bounded ``for`` over a finite list); a diverging
    implementation cannot be written at all. (The nagini battery carries no
    ``diverge-*`` case here regardless.)

  * UNGROUNDED-ORACLE ECHO — VACUOUS. The postcondition is GROUNDED: ``result``
    is pinned equal to a first-match scan built only from the inputs, with the
    membership decided by concrete textual equality. There is no opaque answer
    key an implementation could echo (the carrier is FULLY transparent — no
    ``opaque`` callee, no ``axiom``). In its place the battery carries an honest
    cheapest-implementation POSITIVE CONTROL that must verify.

  * PARTIAL-DOMAIN / VALUE — APPLIES, and is the bulk of the port. Rivals correct
    on part of the domain but diverging where a facet bites: the pre-fix
    type-tag suppression; consulting only the first / only the tail of the
    configured entries; scanning the components in the wrong order; and the
    never-detect near-miss.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen proof script is tuned to the frozen
form — so a rejection alone attributes nothing to the spec. Every
``expect="reject"`` case therefore carries a Lean snippet stating the spec
predicate directly at one concrete input and refuting it by ``decide``. The
carrier computes: every input is small textual literals over ``String`` /
``Bool`` / ``List``, so the spec predicate is decidable at each probed point with
no conditioning needed. Each witness was checked to HOLD of its rival and to FAIL
on the frozen solution (``decide`` proves the spec DOES hold there), so it
discriminates rather than asserting a tautology.

BINDER / POINT SPREAD. The reject witnesses move every input binder of the spec
predicate rather than fixing them at one convenient point. The
structured-object tag (``ConfiguredDir.isObject``) is exercised at BOTH settings
— the pre-fix rival is refuted at a ``true`` (structured-object) entry, exactly
the sub-domain the fix repairs, while the other rivals probe ``false`` entries so
that tag is demonstrated live rather than pinned. The configured list ``dirs``
ranges over length 1 and length 2 with the matching entry at index 0 and at
index 1; the component list ``comps`` ranges over length 1 and length 2 with the
match at different positions; ``defaultDir`` / ``value`` / ``label`` take several
literals. No two rivals share a refutation point — the five reject witnesses
probe five distinct inputs.

AXIOM lane: EMPTY. The bundle consumes no ``axiom`` and declares no ``opaque``
callee (the modeled behavior is spelled out with concrete operations). The
nagini ``AXIOM_TESTS`` belong to G-AX, not this gate, and are dropped.
"""
from pathlib import Path

INSTANCE = "django__django-15987"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- region anchors (each unique inside Solution.lean; verified at load) ----
# Every anchor lies ENTIRELY inside the impl region (or, for the positive that
# re-proves, the impl+proof regions) so same_spec stays byte-identical.

# The load-bearing decision block: the per-component collision test + identify.
_I_DECISION = (
    "    if collides dirs c.defaultDir then\n"
    "      return some c"
)

# The iteration line of the impl (unique: only the impl scans `comps`).
_I_FORLINE = "  for c in comps do"

# The full impl body (header + loop) — for the branch-free positive control.
_I_BODY = (
    "def implementation_fixtureDirs (dirs : List ConfiguredDir) (comps : List Component) :\n"
    "    Option Component := Id.run do\n"
    "  for c in comps do\n"
    "    -- if app_dir in [str(d) for d in fixture_dirs]: raise (identify this component)\n"
    "    if collides dirs c.defaultDir then\n"
    "      return some c\n"
    "  return none"
)

# The frozen proof body (proof region).
_P_FROZEN = (
    "  intro dirs comps\n"
    "  unfold problem_spec_fixtureDirs implementation_fixtureDirs\n"
    "  induction comps with\n"
    "  | nil => rfl\n"
    "  | cons a as ih =>\n"
    "    rw [List.forIn_cons]\n"
    "    simp only [Id.run, bind] at ih ⊢\n"
    "    by_cases h : collides dirs a.defaultDir = true\n"
    "    · simp only [h, if_true, List.find?_cons]; rfl\n"
    "    · simp only [h, List.find?_cons, Bool.false_eq_true, if_false, ih]"
)


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROL (soundness) — a structurally different but CORRECT
    # implementation that MUST verify. If a faithful correct implementation
    # cannot satisfy the frozen obligation the spec is SPEC-TOO-STRONG. Keeps
    # the theorem STATEMENT byte-identical; re-proves inside the proof region
    # (no helper lemma, no axiom, no assumption token introduced).
    #
    # Ports nagini case pos-control-disjunctive-accumulator: the nagini positive
    # replaced the imperative branch with a branch-free disjunctive accumulator
    # and kept the framing. Here the analogous structural reshape drops the
    # imperative `Id.run do`/`for` skeleton entirely and states the core directly
    # as the pure first-match scan — the exact fold the postcondition names — so
    # the obligation closes definitionally.
    # =====================================================================
    {
        "id": "pos-direct-first-match-scan",
        "kind": "soundness",
        "expect": "verify",
        # Branch-free CORRECT impl: the pure first-match scan itself. Same result
        # on every input, so `result = comps.find? …` holds; after unfolding the
        # two definitions the goal is a reflexive equality.
        "module": _swap(
            _swap(
                _BASE, _I_BODY,
                "def implementation_fixtureDirs (dirs : List ConfiguredDir) (comps : List Component) :\n"
                "    Option Component :=\n"
                "  comps.find? (fun c => collides dirs c.defaultDir)",
            ),
            _P_FROZEN,
            "  intro dirs comps\n"
            "  unfold problem_spec_fixtureDirs implementation_fixtureDirs\n"
            "  rfl",
        ),
        "rationale": "a correct but structurally different impl (the pure "
                     "first-match scan, dropping the imperative loop skeleton) "
                     "must verify against `result = comps.find? (fun c => collides "
                     "dirs c.defaultDir)`, else SPEC-TOO-STRONG. Proof: after "
                     "`unfold` the two sides are syntactically equal, so `rfl` "
                     "closes; no lemma/axiom/assumption introduced. Ports nagini's "
                     "branch-free disjunctive-accumulator positive.",
    },

    # =====================================================================
    # ADMISSIBILITY — a positive control confirming the obligation is
    # SATISFIABLE (non-vacuous) at the normal, F2P-shaped input rather than only
    # in the abstract. The frozen theorem carries NO precondition hypothesis (the
    # modeled behavior is total, so `∀` is unguarded), so the nagini
    # precondition-admission probe (admiss-reachable-read) has no binder to attack
    # here; the honest analogue discharges the spec predicate by evaluation at a
    # ground collision input (the F2P scenario: a single configured entry
    # supplied as a structured location object whose textual form equals the one
    # component's default directory) alongside the frozen obligation.
    # Ports nagini case admiss-reachable-read.
    # =====================================================================
    {
        "id": "admiss-ground-collision-instance",
        "kind": "admissibility",
        "expect": "verify",
        # Discharge the obligation at the F2P-shaped collision input by `rfl`
        # (a `have`), then close the frozen obligation verbatim. Nothing is
        # assumed: no new declaration, the theorem statement is byte-identical,
        # the ground instance is a `have` inside the existing tactic body.
        "module": _swap(
            _BASE,
            "  intro dirs comps\n",
            "  have _ground : problem_spec_fixtureDirs "
            "[{value := \"/app/fixtures\", isObject := true}] "
            "[{label := \"a\", defaultDir := \"/app/fixtures\"}] "
            "(implementation_fixtureDirs "
            "[{value := \"/app/fixtures\", isObject := true}] "
            "[{label := \"a\", defaultDir := \"/app/fixtures\"}]) := by rfl\n"
            "  intro dirs comps\n",
        ),
        "rationale": "the obligation is discharged at a ground collision input "
                     "(the F2P scenario: one configured entry supplied as a "
                     "structured location object whose textual form equals the "
                     "one component's default directory → that component is "
                     "identified) by `rfl`, then the frozen obligation is closed "
                     "verbatim. Verifies (else the modeled behavior is "
                     "unsatisfiable at exactly the input the F2P exercises — the "
                     "analogue of PRECOND-TOO-STRONG). Nothing is assumed: no new "
                     "declaration, statement byte-identical, ground instance a "
                     "`have` inside the existing body. Ports nagini's "
                     "reachable-read admissibility probe.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong implementations sharing the
    # frozen spec that MUST be rejected. Each carries (a) the refinement argument
    # that its faithful real patch would NOT resolve the F2P, so a verifying rival
    # would be a true verify-does-not-imply-resolve break rather than an artifact,
    # and (b) a refutation witness pinning the violation at one concrete input.
    # =====================================================================

    # ---- the fix itself: let the structured-object tag suppress a match ----
    # Ports nagini case weak-prepatch-pathobject-suppression (the exact pre-patch
    # bug: a match is suppressed when the entry was supplied as a structured
    # object).
    {
        "id": "weak-prepatch-object-suppression",
        "kind": "uniqueness",
        "expect": "reject",
        # Pre-fix behavior: a configured entry counts as a collision only when it
        # was supplied as PLAIN TEXT — a structured-object entry with the same
        # textual form is ignored.
        "module": _swap(
            _BASE, _I_DECISION,
            "    if dirs.any (fun d => d.value == c.defaultDir && !d.isObject) then\n"
            "      return some c",
        ),
        "refinement": "this IS the pre-fix behavior: the membership test compares "
                      "the supplied form directly, so a configured entry given as "
                      "a structured location object never matches a component's "
                      "(plain-text) default directory even when their textual "
                      "forms coincide. The new F2P scenario supplies exactly such "
                      "a structured-object entry naming a component's default "
                      "directory and asserts the collision IS reported; the "
                      "pre-fix behavior fails to report it, so the faithful real "
                      "patch would NOT resolve.",
        "rationale": "REJECT from the CHANGED discriminator: the spec's membership "
                     "test ignores the supplied form (`d.value == target`) while "
                     "the rival additionally requires `!d.isObject`, so at a "
                     "structured-object entry whose textual form matches, the spec "
                     "identifies the component (`some c`) and the rival returns "
                     "`none`. Binder spread: this is the ONLY rival refuted at an "
                     "`isObject = true` entry — the sub-domain the fix repairs.",
        "witness": (
            "-- Refuted at the reported scenario: one configured entry supplied as\n"
            "-- a structured location object whose textual form equals the one\n"
            "-- component's default directory. Spec ⇒ `some`, rival ⇒ `none`.\n"
            "-- Fully concrete over String/Bool/List, so `decide` computes it.\n"
            "example : ¬ problem_spec_fixtureDirs [{value := \"/f\", isObject := true}] [{label := \"a\", defaultDir := \"/f\"}]\n"
            "    (implementation_fixtureDirs [{value := \"/f\", isObject := true}] [{label := \"a\", defaultDir := \"/f\"}]) := by\n"
            "  unfold problem_spec_fixtureDirs implementation_fixtureDirs\n"
            "  decide\n"
        ),
    },

    # ---- scan the components in the WRONG order (report the LAST match) ----
    # Ports nagini case partial-domain-only-last (report presence only from the
    # last entry): here the analogue mishandles first-match ORDERING over the
    # component list rather than over the configured list.
    {
        "id": "weak-last-match-not-first",
        "kind": "uniqueness",
        "expect": "reject",
        # Scan the components in reverse, so when several collide the LAST in
        # iteration order is identified instead of the FIRST.
        "module": _swap(
            _BASE, _I_FORLINE, "  for c in comps.reverse do",
        ),
        "refinement": "a faithful real patch that iterated the components in the "
                      "wrong order would identify (and raise for) a different "
                      "component than the first offending one; the reported "
                      "component's label is part of the observable outcome, so on "
                      "any configuration with two colliding components the "
                      "identified component — hence the raised message — differs "
                      "from the first-in-order one, and the faithful patch would "
                      "NOT resolve.",
        "rationale": "REJECT from the first-match clause: the spec pins `result = "
                     "comps.find? …` (FIRST in iteration order) while the rival "
                     "scans `comps.reverse` and returns the last, so on two "
                     "colliding components they differ. Binder spread: the only "
                     "rival moving `comps` to length 2 with distinct labels; "
                     "distinct point from every other witness.",
        "witness": (
            "example : ¬ problem_spec_fixtureDirs [{value := \"/f\", isObject := false}] [{label := \"a\", defaultDir := \"/f\"}, {label := \"b\", defaultDir := \"/f\"}]\n"
            "    (implementation_fixtureDirs [{value := \"/f\", isObject := false}] [{label := \"a\", defaultDir := \"/f\"}, {label := \"b\", defaultDir := \"/f\"}]) := by\n"
            "  unfold problem_spec_fixtureDirs implementation_fixtureDirs\n"
            "  decide\n"
        ),
    },

    # ---- consult only the FIRST configured entry (drop the tail) ----
    # Ports nagini case partial-domain-only-last, transposed onto the configured
    # list: a rival correct only when the matching configured entry is the first.
    {
        "id": "weak-only-first-configured",
        "kind": "uniqueness",
        "expect": "reject",
        # Partial domain: only the FIRST configured entry can produce a match; a
        # collision on any later configured entry goes undetected.
        "module": _swap(
            _BASE, _I_DECISION,
            "    if (dirs.take 1).any (fun d => d.value == c.defaultDir) then\n"
            "      return some c",
        ),
        "refinement": "a faithful real patch whose membership test consulted only "
                      "the first configured directory would miss a component whose "
                      "default directory collides with a LATER configured entry; a "
                      "configuration listing an unrelated directory first and the "
                      "colliding one second would fail to be reported, so the "
                      "faithful patch would NOT resolve.",
        "rationale": "REJECT from the every-entry-participates facet of the "
                     "membership test (`dirs.any`, over ALL entries): the spec "
                     "detects a collision at any configured entry while the rival "
                     "sees only `dirs.take 1`, so with the match at index 1 the "
                     "spec returns `some c` and the rival `none`. Binder spread: "
                     "moves `dirs` to length 2 with the match at index 1.",
        "witness": (
            "example : ¬ problem_spec_fixtureDirs [{value := \"/x\", isObject := false}, {value := \"/f\", isObject := false}] [{label := \"a\", defaultDir := \"/f\"}]\n"
            "    (implementation_fixtureDirs [{value := \"/x\", isObject := false}, {value := \"/f\", isObject := false}] [{label := \"a\", defaultDir := \"/f\"}]) := by\n"
            "  unfold problem_spec_fixtureDirs implementation_fixtureDirs\n"
            "  decide\n"
        ),
    },

    # ---- skip the FIRST configured entry (consult only the tail) ----
    # Ports nagini case partial-domain-skip-index-0 (ignore the first configured
    # entry): correct except when the ONLY match is at configured index 0 — the
    # shape of the F2P (a single configured entry at index 0).
    {
        "id": "weak-skip-first-configured",
        "kind": "uniqueness",
        "expect": "reject",
        # Partial domain: ignore the first configured entry (index 0); a
        # collision that exists only at that entry goes undetected.
        "module": _swap(
            _BASE, _I_DECISION,
            "    if (dirs.drop 1).any (fun d => d.value == c.defaultDir) then\n"
            "      return some c",
        ),
        "refinement": "a faithful real patch that skipped the first configured "
                      "directory of the membership test would miss a component "
                      "whose default directory is listed as that first entry; the "
                      "F2P uses a single configured entry (at index 0) naming a "
                      "component's default directory, so this would fail to report "
                      "the collision and would NOT resolve.",
        "rationale": "REJECT from the every-entry-participates facet: the spec "
                     "detects a collision at the first configured entry while the "
                     "rival sees only `dirs.drop 1`, so with the match at index 0 "
                     "the spec returns `some c` and the rival `none`. Binder "
                     "spread: moves `dirs` to length 2 with the match at index 0 "
                     "(distinct from the only-first rival, which matches at index "
                     "1).",
        "witness": (
            "example : ¬ problem_spec_fixtureDirs [{value := \"/f\", isObject := false}, {value := \"/x\", isObject := false}] [{label := \"a\", defaultDir := \"/f\"}]\n"
            "    (implementation_fixtureDirs [{value := \"/f\", isObject := false}, {value := \"/x\", isObject := false}] [{label := \"a\", defaultDir := \"/f\"}]) := by\n"
            "  unfold problem_spec_fixtureDirs implementation_fixtureDirs\n"
            "  decide\n"
        ),
    },

    # ---- never detect anything (the cheapest wrong impl) ----
    # Ports nagini case weak-constant-false.
    {
        "id": "weak-never-detect",
        "kind": "uniqueness",
        "expect": "reject",
        # Constant `none`: never identify a collision (always-miss). Correct only
        # on the no-collision sub-domain.
        "module": _swap(
            _BASE, _I_DECISION,
            "    if false then\n"
            "      return some c",
        ),
        "refinement": "a faithful real patch that never reported a collision would "
                      "never raise even when a component's default directory IS "
                      "among the configured directories; it fails the F2P (which "
                      "asserts the raise) and would NOT resolve.",
        "rationale": "REJECT from the collision-detection facet: on any "
                     "configuration with a match the spec returns `some c` while "
                     "the rival returns `none` unconditionally. Binder spread: "
                     "refuted at a plain-text (`isObject = false`) single-entry "
                     "single-component collision — a point distinct from every "
                     "other witness.",
        "witness": (
            "example : ¬ problem_spec_fixtureDirs [{value := \"/f\", isObject := false}] [{label := \"a\", defaultDir := \"/f\"}]\n"
            "    (implementation_fixtureDirs [{value := \"/f\", isObject := false}] [{label := \"a\", defaultDir := \"/f\"}]) := by\n"
            "  unfold problem_spec_fixtureDirs implementation_fixtureDirs\n"
            "  decide\n"
        ),
    },
]

# No AXIOM lane here: the bundle consumes no `axiom` and declares no `opaque`
# callee (the modeled behavior is spelled out with concrete operations). The
# nagini AXIOM_TESTS belong to G-AX; dropped.
AXIOM_TESTS = []
