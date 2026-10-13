"""properties.py — G-PBT falsification battery for django__django-13658 (lean).

NOT a Lean file; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the single ``-- impl-start`` /
``-- impl-end`` region — and, for a case that legitimately re-proves, inside the
``-- proof-start`` / ``-- proof-end`` region — is changed, so
``markers.same_spec`` holds and the ``theorem correct_progName`` STATEMENT stays
byte-identical). ``expect:"verify"`` passes iff (in scope AND the file
elaborates with the obligation closed); ``expect:"reject"`` passes iff (in scope
AND it does NOT verify AND the case's refutation ``witness`` holds of the rival
while FAILING on the frozen solution).

DEFENDED SURFACE (one total behavior over an argument-vector carrier):

  progName (argv ambient : List String) : String
    result = computeProgName argv.headI

The presented program name is a function of the utility's OWN argument vector
alone (its first argument's final path component), with the module-execution
entry point remapped to a constant textual name. ``computeProgName`` has two
independent legs, both pinned by the single postcondition clause
``result = computeProgName argv.headI``:

  * SOURCE + PATH-COMPONENT — the result is the final path component of the
    utility's own first argument. It is grounded in ``argv``, never in the
    ambient vector; the two are allowed to disagree.
  * ENTRY-POINT REMAP — the special path component (the module-execution entry
    point) maps to a constant textual name rather than to itself.

ADVERSARIAL READ of the nagini classes on this carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS. Lean is referentially transparent:
    no input carries a heap permission, there is no read-only half-permission to
    overwrite and no aliasing to exploit. The nagini frame-mutation rival (write
    to the read-only ``argv0_basename``) has no expressible instance here and no
    substitute is fabricated for it.

  * UNGROUNDED-ORACLE ECHO — VACUOUS. The postcondition is GROUNDED in the
    argument vector (an equality against a term built only from ``argv``, fully
    unfolded through ``computeProgName``/``basename``); the bundle declares no
    ``opaque``/``axiom``, so there is no answer key an implementation could echo
    without doing the work. In its place the battery carries an honest
    cheapest-implementation POSITIVE CONTROL that must verify.

  * WRONG-SOURCE / SPEC-TOO-WEAK — APPLIES. The nagini wrong-source rival
    (derive the program name from the ambient vector) ports directly: the
    postcondition mentions only ``argv``, so a rival sourcing from ``ambient``
    verifies ONLY where the two coincide and is refuted where they disagree.

  * PARTIAL-DOMAIN / VALUE — APPLIES. The nagini no-bootstrap-remap rival and
    the off-by-one truncation rival port directly: each is correct on part of
    the input domain and diverges on a sub-domain (the entry-point input; every
    non-empty path component, respectively).

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen script is tuned to the frozen form — so
a rejection alone attributes nothing to the spec. Every ``expect="reject"`` case
therefore carries a Lean snippet proving the rival CONTRADICTS the spec at one
concrete input, stated directly against the spec predicate at ``decide``-able
literals. The path-component helper is defined by well-founded recursion over a
byte-position scan, so ``decide``/``rfl`` cannot reduce it on a literal; each
witness first rewrites it into its validated ``List Char`` characterisation (a
core library lemma, not a new declaration) and then ``decide``s. Each was
checked to hold of its rival and to FAIL on the frozen solution (so it
discriminates rather than asserting a tautology); ``native_decide`` is banned
and not used.

Witness inputs are spread across the modeled domain rather than fixed at one
convenient point, and the reject witnesses vary the ONE binder the spec predicate
depends on — the utility's own first argument (``argv.headI``): the wrong-source
rival is refuted at an ordinary name where the two vectors disagree, the
no-remap rival at the entry-point input (the only place its leg diverges), and
the truncation rival at a non-empty ordinary name. Both legs of
``computeProgName`` are attacked.

AXIOM lane: DROPPED. The nagini AXIOM_TESTS (soundness + containment of the
``program_name`` A-reference) belong to G-AX, not to this gate; they are omitted
here by design.
"""
from pathlib import Path

INSTANCE = "django__django-13658"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- region anchors (each unique inside Solution.lean; verified at load) ----
# The full body of the single impl region, and the full tactic body of the
# single proof region, so every replacement lands entirely inside the region it
# means to edit.
_I_IMPL = (
    "def implementation_progName (argv : List String) (_ambient : List String) : String :=\n"
    "  Id.run do\n"
    "    -- Derive the program name from the utility's OWN argument vector, applying\n"
    "    -- the module-execution special case. The ambient argument vector is not\n"
    "    -- consulted.\n"
    "    let mut progName := basename argv.headI\n"
    "    if progName = \"__main__.py\" then\n"
    "      progName := \"python -m django\"\n"
    "    return progName\n"
)
_P_PROOF = (
    "  intro argv ambient _\n"
    "  unfold problem_spec_progName implementation_progName computeProgName\n"
    "  by_cases h : basename argv.headI = \"__main__.py\" <;>\n"
    "    simp only [Id.run, bind, pure, h, if_true, if_false]\n"
)

# sanity: both anchors present exactly once in the frozen solution.
assert _BASE.count(_I_IMPL) == 1, "impl anchor drifted from Solution.lean"
assert _BASE.count(_P_PROOF) == 1, "proof anchor drifted from Solution.lean"


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROL (soundness) — a structurally different but CORRECT
    # implementation that MUST verify. If a faithful correct implementation
    # cannot satisfy the frozen obligation the spec is SPEC-TOO-STRONG. Keeps
    # the `theorem correct_progName` statement byte-identical and re-proves it
    # for the new shape where the frozen script no longer applies; introduces no
    # helper lemma, axiom, or assumption token.
    # =====================================================================
    {
        "id": "pos-negated-guard-early-return",
        "kind": "soundness",
        "expect": "verify",
        # Control-flow reshape: bind the path component, test the NEGATED
        # entry-point predicate and early-return the ordinary result, falling
        # through to the constant name. Same value on every input; the frozen
        # `by_cases … <;> simp` script is re-tuned to the reshaped branches.
        "module": _swap(
            _swap(
                _BASE, _I_IMPL,
                "def implementation_progName (argv : List String) (_ambient : List String) : String :=\n"
                "  Id.run do\n"
                "    let b := basename argv.headI\n"
                "    if b ≠ \"__main__.py\" then\n"
                "      return b\n"
                "    return \"python -m django\"\n",
            ),
            _P_PROOF,
            "  intro argv ambient _\n"
            "  unfold problem_spec_progName implementation_progName computeProgName\n"
            "  by_cases h : basename argv.headI = \"__main__.py\" <;>\n"
            "    simp only [Id.run, bind, pure, h, if_true, ne_eq, not_true, not_false_iff, if_neg]\n",
        ),
        "rationale": "reshaping the entry-point decision behind a negated guard "
                     "with an early return preserves the exact value flow, so "
                     "`result = computeProgName argv.headI` still holds; a correct "
                     "reshape must verify (else SPEC-TOO-STRONG). Re-proved because "
                     "the frozen script matches the frozen branch order: the new "
                     "shape needs the negated-guard simp lemmas (`ne_eq`, `if_neg`; "
                     "core lemmas, no new declaration) after the same `by_cases`.",
    },

    # =====================================================================
    # ADMISSIBILITY — a positive control confirming the obligation is
    # SATISFIABLE (non-vacuous) at the exact F2P-shaped input rather than only
    # provable in the abstract. The frozen theorem carries a precondition
    # hypothesis (`argv ≠ []`); the honest analogue of the nagini precondition-
    # admission probe is to discharge the spec predicate at the concrete F2P
    # input — the utility's own vector `['django-admin','help','shell']` with a
    # DISAGREEING ambient vector (first entry empty, mirroring the F2P's mocked
    # `sys.argv[0]`) — by evaluation, inside the proof region alongside the
    # frozen obligation. If that ground instance could not be discharged, the
    # modeled behavior would be unsatisfiable at exactly the input the F2P
    # exercises.
    # =====================================================================
    {
        "id": "admiss-f2p-ground-instance",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _P_PROOF,
            "  have _ground : problem_spec_progName [\"django-admin\", \"help\", \"shell\"]\n"
            "      (implementation_progName [\"django-admin\", \"help\", \"shell\"] [\"\", \"help\", \"shell\"]) := by\n"
            "    unfold problem_spec_progName implementation_progName computeProgName\n"
            "    simp only [List.headI, Id.run, basename]\n"
            "    rw [String.split_of_valid]\n"
            "    decide\n"
            + _P_PROOF,
        ),
        "rationale": "the progName obligation is discharged at the concrete F2P "
                     "input (own vector 'django-admin help shell' with a "
                     "disagreeing ambient vector) by evaluation, then the frozen "
                     "obligation is closed verbatim. Verifies (else the spec is "
                     "unsatisfiable at the normal input — the analogue of "
                     "PRECOND-TOO-STRONG). Nothing is assumed: no new declaration, "
                     "the theorem statement is byte-identical, and the ground "
                     "instance is a `have` inside the existing tactic body.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong implementations sharing the
    # frozen spec that MUST be rejected. Each carries (a) the refinement
    # argument that its faithful real patch would NOT resolve the graded suite,
    # so a verifying rival is a true verify-does-not-imply-resolve break rather
    # than an artifact, and (b) a refutation witness pinning the violation at one
    # concrete input.
    # =====================================================================
    {
        "id": "weak-wrong-source-ambient",
        "kind": "uniqueness",
        "expect": "reject",
        # Derive the program name from the AMBIENT vector instead of the
        # utility's own. This is the pre-fix behavior. Verifies only where the
        # two vectors coincide; the postcondition pins the result to
        # `computeProgName argv.headI`, so wherever they disagree it fails.
        "module": _swap(
            _BASE, _I_IMPL,
            "def implementation_progName (argv ambient : List String) : String :=\n"
            "  Id.run do\n"
            "    let mut progName := basename ambient.headI\n"
            "    if progName = \"__main__.py\" then\n"
            "      progName := \"python -m django\"\n"
            "    return progName\n",
        ),
        "refinement": "sourcing the program name from the ambient process vector "
                      "is exactly the pre-fix behavior (the option parser defaulting "
                      "to the ambient first argument's basename). In the F2P the "
                      "utility's own vector is ['django-admin', …] while the ambient "
                      "vector is mocked so its first entry is UNUSABLE (the basename "
                      "of a missing launch path); the faithful real patch (no change) "
                      "does not present 'django-admin' and does NOT resolve the F2P.",
        "rationale": "REJECT from `result = computeProgName argv.headI`: the rival "
                     "computes `computeProgName ambient.headI`, so on any input "
                     "where the two vectors' first arguments differ it disagrees "
                     "with the spec. If it verified the spec would be SPEC-TOO-WEAK "
                     "(admits the wrong-source / pre-fix impl). Refuted at an "
                     "ordinary own-name 'django-admin' with a disagreeing ambient "
                     "'other' — the F2P-shaped divergence.",
        "witness": (
            "-- The result must be the utility's OWN first-argument path component,\n"
            "-- independent of the ambient vector: at own = 'django-admin', ambient\n"
            "-- = 'other' the rival returns 'other' where the spec requires\n"
            "-- 'django-admin'. `basename` is a well-founded byte scan, opaque to\n"
            "-- `decide`; rewrite it to its validated List-Char form first.\n"
            "example : ¬ problem_spec_progName [\"django-admin\"]\n"
            "    (implementation_progName [\"django-admin\"] [\"other\"]) := by\n"
            "  unfold problem_spec_progName implementation_progName computeProgName\n"
            "  simp only [List.headI, Id.run, basename, String.split_of_valid]\n"
            "  decide\n"
        ),
    },
    {
        "id": "weak-no-entry-point-remap",
        "kind": "uniqueness",
        "expect": "reject",
        # Copy the path component verbatim, OMITTING the entry-point remap.
        # Correct on every input EXCEPT the module-execution entry point, where
        # the spec requires the constant name but this yields the raw component.
        "module": _swap(
            _BASE, _I_IMPL,
            "def implementation_progName (argv : List String) (_ambient : List String) : String :=\n"
            "  Id.run do\n"
            "    return basename argv.headI\n",
        ),
        "refinement": "omitting the entry-point remap reports the raw component "
                      "'__main__.py' where the documented behavior requires the "
                      "constant module-invocation name. The narrow F2P uses an "
                      "ordinary name and would pass, but the graded suite pins the "
                      "entry-point behavior in a separate program-name-in-help "
                      "regression test, which this breaks; it is not a faithful fix "
                      "and does NOT leave the suite resolved.",
        "rationale": "REJECT from `result = computeProgName argv.headI`: on the "
                     "entry-point input the spec's `computeProgName` returns the "
                     "constant name while the rival returns '__main__.py'. Attacks "
                     "the entry-point-remap leg specifically. If it verified the "
                     "spec would be SPEC-TOO-WEAK on the entry-point sub-domain.",
        "witness": (
            "-- On the module-execution entry point the spec requires the constant\n"
            "-- name; the verbatim copy yields '__main__.py'. This point is the only\n"
            "-- place this leg diverges, so the witness sits exactly there.\n"
            "example : ¬ problem_spec_progName [\"__main__.py\"]\n"
            "    (implementation_progName [\"__main__.py\"] []) := by\n"
            "  unfold problem_spec_progName implementation_progName computeProgName\n"
            "  simp only [List.headI, Id.run, basename]\n"
            "  rw [String.split_of_valid]\n"
            "  decide\n"
        ),
    },
    {
        "id": "weak-off-by-one-truncate",
        "kind": "uniqueness",
        "expect": "reject",
        # Supporting near-miss: drop the last character of the path component
        # (keeping the entry-point remap). Wrong on every non-empty ordinary
        # name, correct only on a name whose truncation is idempotent.
        "module": _swap(
            _BASE, _I_IMPL,
            "def implementation_progName (argv : List String) (_ambient : List String) : String :=\n"
            "  Id.run do\n"
            "    let mut progName := (basename argv.headI).dropRight 1\n"
            "    if progName = \"__main__.py\" then\n"
            "      progName := \"python -m django\"\n"
            "    return progName\n",
        ),
        "refinement": "truncating the final character of the path component "
                      "presents 'django-admi' instead of 'django-admin'; the F2P "
                      "asserts the exact rendered program name in the usage banner, "
                      "so the faithful real patch (a truncated program name) fails "
                      "that assertion and does NOT resolve the F2P.",
        "rationale": "REJECT from `result = computeProgName argv.headI`: dropping "
                     "the last character makes the result a strict prefix of the "
                     "path component on every non-empty ordinary name. Attacks the "
                     "path-component leg (value). Refuted at an ordinary name "
                     "'prog', distinct from the wrong-source point, so its divergent "
                     "input is its own.",
        "witness": (
            "example : ¬ problem_spec_progName [\"prog\"]\n"
            "    (implementation_progName [\"prog\"] []) := by\n"
            "  unfold problem_spec_progName implementation_progName computeProgName\n"
            "  simp only [List.headI, Id.run, basename]\n"
            "  rw [String.split_of_valid]\n"
            "  decide\n"
        ),
    },
]
