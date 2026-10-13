"""properties.py — G-PBT falsification battery for django__django-13658 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed,
both of which the consumer spec view elides — so ``markers.same_spec`` holds and
the ``prove_correct usageProgName`` obligation survives with a byte-identical
statement) and swaps in a candidate implementation; it is checked by the real
verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: it must elaborate against the rival and FAIL against
the frozen solution).

DEFENDED SURFACE (one contracted method):

  usageProgName (argv processArgv : List String) return (out : List Char)
    require argv ≠ []
    ensures out = progNameOf argv

``progNameOf`` is a total, fully-unfolded pure function of an argument vector:
the final path component of the vector's first entry, except that a bare module
entry point is displayed under the package's friendly invocation name instead.
The single load-bearing ``ensures`` clause pins the result to
``progNameOf argv`` — grounded in the invocation's OWN vector (``argv``), NEVER
the process-global vector (``processArgv``). ``processArgv`` is a FREE input the
result must not depend on: the two vectors are allowed to disagree, and the
post-image must hold for every value ``processArgv`` takes.

ADVERSARIAL READ of the classes:
  * FRAME-MUTATION — VACUOUS on this backend. The sibling class exists because a
    read-only input may carry a fractional heap permission an impl can
    overwrite. Lean and Velvet are referentially transparent: every parameter is
    an immutable value (this bundle declares no ``mut`` binder), there is no heap
    and no aliasing, so there is no read-only input to mutate and no substitute
    probe to build. Not fabricated. (See footer.)
  * WRONG-SOURCE — APPLIES, and is the sibling's headline SPEC-TOO-WEAK probe:
    deriving the result from ``processArgv`` instead of ``argv``. It agrees with
    the post-image only where the two vectors coincide, so it is refutable at any
    input where they disagree — exactly the discriminator the failing test pins.
  * PARTIAL-DOMAIN / VALUE — APPLIES: a rival right on part of the argument-vector
    domain but diverging on a sub-domain (the module-entry-point special case; a
    one-shorter truncation of the derived name).
  * UNGROUNDED-ORACLE ECHO — N/A. ``progNameOf`` is a concrete ``def`` in the
    ``pure`` region (the ``axioms`` region is empty — no opaque answer key to
    echo); the cheapest correct impl simply evaluates it, which the positive
    controls cover honestly.

WITNESS PLACEMENT. Each reject rival carries a machine-checked refutation
``witness`` — a Velvet tester statement at ONE concrete input, checked in a file
whose obligation has been stripped so no tactic script can mask the verdict. The
three witnesses sit at three DISTINCT input points, and vary the binders:
``argv`` ranges over an ordinary name, the module-entry-point name, and a short
two-character name; and the wrong-source witness is the only one whose
``processArgv`` DIFFERS from ``argv`` — which is exactly the sub-domain on which a
result sourced from the wrong vector is observably wrong. A rival that read the
right vector would satisfy that witness, so the manifest genuinely demonstrates
the post-image's dependence on ``argv`` (and its independence from
``processArgv``), not merely its value at a single pinned point.
"""
from pathlib import Path

INSTANCE = "django__django-13658"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchor (lies wholly inside the single impl region and is
# ---- unique in Solution.lean; both facts asserted at load by _swap) --------
_A_IMPL = (
    "    -- Use the program name derived from the invocation's own argument vector.\n"
    "    let out : List Char := progNameOf argv\n"
    "    return out\n"
)

# ---- proof-body anchor. A `prove_correct` tactic body is elided from the
# ---- consumer spec view, so a case that introduces an in-region `assert` may
# ---- retune the tactic script without touching the spec or dropping the
# ---- obligation. Unique in the file.
_T_PROOF = "prove_correct usageProgName by\n  loom_solve\n"


def _swap2(a_old, a_new, t_old, t_new):
    """Reshape the impl region AND retune the tactic body."""
    return _swap(_swap(_BASE, a_old, a_new), t_old, t_new)


# ---- witness preamble. The spec is a `method` CONTRACT, not a bare predicate,
# ---- so a witness reaches it through Velvet's own tester machinery:
# ---- `usageProgNameTester argv processArgv = false` says the extracted
# ---- program's result violates the method's postcondition at that concrete
# ---- input. Checked in a file whose `prove_correct` block has been stripped.
def _tester(body):
    return ("extract_program_for usageProgName\n"
            "prove_precondition_decidable_for usageProgName\n"
            "prove_postcondition_decidable_for usageProgName\n"
            "derive_tester_for usageProgName\n\n" + body)


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # impls that MUST verify. If a faithful correct impl cannot verify, the
    # spec is SPEC-TOO-STRONG. Each keeps the obligation and only reshapes the
    # executable surface; the contract is point-wise, so the reproof stays a
    # `loom_solve` away from the frozen script.
    # =====================================================================
    {
        "id": "pos-control-inline-derivation",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: spell the derivation out inline (final path component of the
        # first entry, with the module-entry-point rename) instead of naming the
        # pure derivation directly. Observationally `progNameOf argv` for every
        # non-empty vector.
        "module": _swap(
            _BASE, _A_IMPL,
            "    let b : List Char := basename (argv.headD \"\").toList\n"
            "    let out : List Char :=\n"
            "      if b = \"__main__.py\".toList then \"python -m django\".toList else b\n"
            "    return out\n"),
        "rationale": "an inlined but observationally identical derivation must "
                     "satisfy `out = progNameOf argv` on the whole non-empty "
                     "domain; if it fails to verify the post-image is "
                     "SPEC-TOO-STRONG on the derivation's shape.",
    },
    {
        "id": "pos-control-negated-guard",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: negate the module-entry-point guard and swap the two arms
        # (the sibling's branch-reorder positive control). Same mapping on both
        # arms, so the post-image is unchanged.
        "module": _swap(
            _BASE, _A_IMPL,
            "    let b : List Char := basename (argv.headD \"\").toList\n"
            "    let out : List Char :=\n"
            "      if b ≠ \"__main__.py\".toList then b else \"python -m django\".toList\n"
            "    return out\n"),
        "rationale": "negating the guard and swapping the branches computes the "
                     "same result on both arms, so `out = progNameOf argv` still "
                     "holds; a correct reshape must verify (else SPEC-TOO-STRONG "
                     "on branch order).",
    },

    # =====================================================================
    # ADMISSIBILITY — the precondition `argv ≠ []` is trivially satisfiable for
    # any F2P-shaped invocation (a real vector always has a first entry), so the
    # "a normal input satisfies the precondition" probe is not where the risk
    # sits. The residual admissibility risk on this surface is that the
    # post-image is UNSATISFIABLE or DEGENERATE at the interesting point — a
    # spec no impl can meet reads exactly like one every impl meets. This case
    # discharges an in-region `assert` pinning the post-image's value at the two
    # F2P-shaped inputs: an ordinary program name is reported verbatim, and the
    # module-entry-point name is reported under the friendly invocation name.
    # The surrounding impl is kept verbatim so the method's own obligation still
    # discharges; the assert is live (a false claim about the same points leaves
    # an unsolved `False` goal — checked during authoring).
    # =====================================================================
    {
        "id": "admiss-progname-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap2(
            _A_IMPL,
            "    assert (with_name_prefix `assert\n"
            "      (progNameOf [\"django-admin\"] = \"django-admin\".toList ∧\n"
            "       progNameOf [\"__main__.py\"] = \"python -m django\".toList))\n"
            + _A_IMPL,
            _T_PROOF,
            "prove_correct usageProgName by\n  loom_solve <;> decide\n"),
        "rationale": "the post-image is satisfiable AND non-degenerate at the "
                     "F2P-shaped inputs: it demands an ordinary program name back "
                     "verbatim and remaps the module-entry-point name to the "
                     "friendly invocation name. The in-region assert must "
                     "discharge (else the obligation is unsatisfiable / "
                     "PRECOND-TOO-STRONG); the impl is kept verbatim so the "
                     "method's own `ensures` still discharges.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # concrete input and the refinement argument that its faithful real
    # counterpart would NOT resolve the failing test.
    # =====================================================================
    {
        "id": "weak-wrong-source",
        "kind": "uniqueness",
        "expect": "reject",
        # Derive the result from the process-global vector instead of the
        # invocation's own vector. Agrees with the post-image only when the two
        # vectors coincide.
        "module": _swap(_BASE, _A_IMPL,
                        "    let out : List Char := progNameOf processArgv\n"
                        "    return out\n"),
        "refinement": "a counterpart that names the program after the "
                      "process-global vector reports the wrong program name "
                      "whenever an invocation supplies its own vector that "
                      "differs from the global one — the precise scenario the "
                      "failing test constructs (own vector naming one program, "
                      "the global vector mocked to something unusable). It would "
                      "NOT resolve.",
        "rationale": "REJECT from `out = progNameOf argv`: with the two vectors "
                     "disagreeing the impl computes `progNameOf processArgv` "
                     "where the post-image demands `progNameOf argv`. If this "
                     "verified the spec would be SPEC-TOO-WEAK (it would admit "
                     "the wrong-source impl). Refuted at the sub-domain where "
                     "`processArgv` differs from `argv`, which is what makes the "
                     "post-image's independence from `processArgv` observable.",
        "witness": _tester(
            "example : usageProgNameTester [\"django-admin\"] [\"other\"] "
            "= false := by\n  decide\n"),
    },
    {
        "id": "weak-no-module-rename",
        "kind": "uniqueness",
        "expect": "reject",
        # Take the final path component of the first entry but OMIT the
        # module-entry-point rename. Correct on every vector except the one
        # whose first entry is that bare entry point.
        "module": _swap(_BASE, _A_IMPL,
                        "    let out : List Char := basename (argv.headD \"\").toList\n"
                        "    return out\n"),
        "refinement": "a counterpart that omits the module-entry-point rename "
                      "reports the bare entry-point token instead of the package's "
                      "friendly invocation name, diverging from the documented "
                      "program-name derivation on exactly that sub-domain; the "
                      "usage line a module invocation prints would carry the wrong "
                      "name. It would NOT resolve.",
        "rationale": "REJECT from `out = progNameOf argv`: `progNameOf` remaps the "
                     "module-entry-point first entry, so a plain final-component "
                     "impl yields that bare token where the post-image demands the "
                     "friendly name — failing on exactly the module-entry-point "
                     "sub-domain. Verifying would be SPEC-TOO-WEAK there. Refuted "
                     "at that sub-domain (which no other rival probes).",
        "witness": _tester(
            "example : usageProgNameTester [\"__main__.py\"] [\"__main__.py\"] "
            "= false := by\n  decide\n"),
    },
    {
        "id": "weak-truncate-last-char",
        "kind": "uniqueness",
        "expect": "reject",
        # Supporting near-miss: drop the last character of the derived name.
        # A strict prefix of the correct program name on every non-empty result.
        "module": _swap(_BASE, _A_IMPL,
                        "    let out : List Char := (progNameOf argv).dropLast\n"
                        "    return out\n"),
        "refinement": "a counterpart that drops the last character of the derived "
                      "name reports a truncated program name (e.g. a name one "
                      "character short), a broken usage token that fails the test "
                      "asserting the exact rendered name. It would NOT resolve.",
        "rationale": "REJECT from `out = progNameOf argv`: dropping the final "
                     "character makes the result a strict prefix of the required "
                     "program name on every non-empty derivation. Rejected by the "
                     "value post-image; verifying would be SPEC-TOO-WEAK on the "
                     "exact program-name value. Refuted at a short ordinary name "
                     "distinct from the other rivals' inputs.",
        "witness": _tester(
            "example : usageProgNameTester [\"ab\"] [\"ab\"] = false := by\n"
            "  decide\n"),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 6 SPEC cases (1 soundness
# positive, 1 admissibility, 4 uniqueness rivals). This bundle models only the
# purely-functional core — a single method `usageProgName` — where the sibling
# contracts one function `build_settings_parser` over a permission-bearing heap
# object. The value surface carries across intact; the permission surface does
# not exist here. Every sibling case is accounted for below.
#
#   sibling case                        -> here
#   ---------------------------------------------------------------------
#   pos-control-branch-reorder          -> pos-control-negated-guard      PORTED
#                                          (+ pos-control-inline-derivation ADDED)
#   admissibility-django-admin          -> admiss-progname-nondegenerate  RE-AIMED
#   frame-mut-argv0-write               -> (none)                         VACUOUS
#   wrong-source-ambient-prepatch       -> weak-wrong-source              PORTED
#   partial-domain-no-bootstrap-remap   -> weak-no-module-rename          PORTED
#   partial-domain-off-by-one-truncate  -> weak-truncate-last-char        PORTED
#
# 4 ported, 1 re-aimed, 1 vacuous; 1 positive control added.
#
# VACUOUS (frame-mut-argv0-write): the sibling's mandatory frame-mutation rival
#   writes to a read-only input that carries only a fractional heap permission,
#   and is rejected for INSUFFICIENT PERMISSION. This backend is referentially
#   transparent: every parameter is an immutable value, this bundle declares no
#   `mut` binder, there is no heap and no aliasing. There is no read-only input
#   to overwrite and no permission system to trip, so the class is vacuous. No
#   substitute is fabricated (per the porting map, this class is legitimately
#   dropped here rather than replaced).
# RE-AIMED (admissibility): the sibling's case constructs a normal input and
#   establishes the precondition for it. The precondition here (`argv ≠ []`) is
#   trivially satisfiable for every F2P-shaped invocation, so that probe is not
#   where the risk sits. It is re-aimed at the residual admissibility risk on
#   this surface: that the post-image is unsatisfiable or degenerate at the
#   interesting point. The case discharges an in-region assert pinning the
#   post-image's value at the two F2P-shaped inputs (an ordinary name reported
#   verbatim; the module-entry-point name remapped).
# ADDED (1): pos-control-inline-derivation — a second, structurally-different
#   correct impl (the derivation spelled out inline rather than named), so the
#   soundness surface is defended by two distinct reshapes rather than one.
#
# BINDER / CLAUSE COVERAGE. The single `ensures` clause `out = progNameOf argv`
#   is attacked by all three rivals across three distinct sub-domains — the
#   argv-vs-processArgv discriminator (the load-bearing behavior), the
#   module-entry-point rename branch, and the derived-name value — refuted at
#   three DISTINCT input points (pts=3). The binder `argv` is varied across the
#   three witnesses (an ordinary name, the module-entry-point name, a short
#   name); `processArgv` is varied by weak-wrong-source, the one witness whose
#   `processArgv` differs from `argv`, which is exactly the point that
#   demonstrates the post-image does NOT depend on `processArgv`.
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job; the two deep models
#   (`basename`, `progNameOf`) are A-references validated there, and this gate
#   ignores AXIOM_TESTS regardless.
AXIOM_TESTS = []
