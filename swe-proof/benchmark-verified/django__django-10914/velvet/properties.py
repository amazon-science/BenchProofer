"""properties.py — G-PBT falsification battery for django__django-10914 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed
— both of which the consumer spec view elides, so ``markers.same_spec`` holds
and the ``prove_correct defaultFileMode`` obligation survives with a
byte-identical statement) and swaps in a candidate implementation, checked by
the real verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: it must elaborate against the rival and FAIL against
the frozen solution).

DEFENDED SURFACE (one contracted query over the empty input domain):

  defaultFileMode return (mode : Nat)   ensures mode = 420

The modeled behaviour is the framework's DEFAULT numeric mode handed to newly
stored files (the value passed straight to the OS chmod call): a definite,
owner-read/write plus group/other-read mode (decimal 420, i.e. rw-r--r--),
supplied out of the box in place of the unset/absent sentinel (modeled as 0)
that would leave the mode indefinite. The query takes NO input and mutates
nothing (directive 5).

  Load-bearing clause (the whole postcondition is a single top-level equality):
    (C1) mode = 420   — the EXACT default numeric mode. This one predicate pins
                        two distinguishable obligations:
                        * the mode is DEFINITE (equal to a concrete value, not
                          the unset/absent sentinel 0);
                        * the definite value is the SPECIFIC one 420 (0o644),
                          not some other numeric mode.

  There is no opaque answer-key oracle: the ``axioms`` region is empty and 420
  is a concrete literal, so pinning ``mode = 420`` is grounded, not an echo.

CARRIER NARROWING (this bundle vs the nagini sibling). The nagini sibling
contracts a RICHER function ``resolve_storage_mode(override: Optional[int])``:
a per-store override passes through verbatim (its C1 passthrough clause), and
only when NO override is configured is the project-wide default returned (its
C2/C3/C4 definite-default clauses). This bundle models ONLY the purely
functional core the fix actually turns on — WHAT the project-wide default value
IS — as a zero-argument constant provider. The gold patch's sole change is
exactly that default value (an unset/absent sentinel → the definite 0o644), and
that is the entire modeled surface here.

Consequently the nagini rivals attached to the OVERRIDE input (the passthrough
clause C1 and the partial-domain attacks on it) have NO counterpart on this
carrier: there is no ``override`` binder to abuse, no branch to swap, and no
sub-domain of a present override to special-case. Those are all downstream
resolver behaviour the fix does not touch and this bundle does not model
(mapping.md). Carrier narrowing, not a gap in coverage of what IS modeled — the
footer accounts for every nagini case.

ADVERSARIAL READ of the nagini classes on THIS carrier:
  * FRAME-MUTATION — VACUOUS. Lean and Velvet are referentially transparent:
    there is no heap, no aliasing, no fractional permission. This bundle's query
    takes no parameters and declares no ``mut`` binder, so there is no read-only
    input to overwrite. The nagini sibling ALSO records this class as
    inapplicable (its only input is an immutable scalar, no heap permission). No
    substitute probe is fabricated.
  * OVERRIDE-PASSTHROUGH (nagini C1) and its PARTIAL-DOMAIN attacks — NO
    COUNTERPART. The override input is not modeled here (see CARRIER NARROWING),
    so the passthrough clause and every rival that abuses a present override
    (always-return-default, swap-the-arms, special-case override == 0) has
    nothing to land on. Reported as omissions in the footer, not faked.
  * UNGROUNDED-ORACLE ECHO — N/A. 420 is a concrete literal, the ``axioms``
    region is empty, and the post-image is a total function of no input. There
    is no answer-key to echo; the positives are honest cheapest-reshape
    controls. (The nagini sibling reached the same conclusion: its
    ``default_mode()`` reference was a grounded ``@Pure`` constant == 420, so an
    echo of it was CORRECT, not a wrong echo.)
  * WRONG-VALUE — APPLIES to C1, and is the whole reject surface: a rival
    attaching a DIFFERENT definite value (the community-rejected 0o600, or a
    decimal/octal confusion), and a rival yielding the absent sentinel 0 (the
    pre-fix unset value).

DIVERGENCE LANE - the class is INAPPLICABLE to this impl and CLOSED BY THE
SEMANTICS against any rival that manufactures it. The frozen impl is LOOP-FREE
(straight-line a single ``return`` over immutable values, no loop and no
recursion), so there is no control flow here to make diverge: a diverging rival
cannot be obtained by mutating this body, it has to bring a loop of its own.
When it does, the semantics refuse it. This bundle sets
``loom.semantics.termination "total"`` AND carries ``open TotalCorrectness``,
and the ``open`` is the line that actually selects the semantics: both
namespaces define ``WPGen.forWithInvariantLoop``, the later ``open`` wins, and
the ``PartialCorrectness`` version takes a loop measure and DISCARDS it, so the
two lines have to move together and they do here. Under the total scope a
postcondition is claimed of ALL runs and not only of terminating ones, so a
spliced loop owes a descent obligation ``measure b' < measure b``. Re-measured
on this bundle with a real build: a ``while spin > 0 do spin := spin`` prefix
carrying ``decreasing spin`` is REJECTED on the measure's own goal (``case
«decreasing_1: spin» ... ⊢ spin < spin``). Dropping the clause rather than
faking it is refused even earlier, by the elaborator's own check (``Decreasing
annotations are required in total correctness semantics``). So divergence
neither applies to this impl nor discharges the ``ensures`` clauses vacuously
if a rival introduces it.

WITNESS PLACEMENT. The query takes NO argument, so its extracted tester is a
single ``Bool`` (``defaultFileModeTester : Bool``) — there is exactly ONE input
point (the empty tuple) at which any rival can be refuted, and ``pts=1`` is
therefore STRUCTURAL, not a coverage gap: there is no binder to vary because
there is no binder. Each reject case's witness asserts
``defaultFileModeTester = false`` — the extracted program violates the
postcondition. The three rivals fail at that single point for THREE DISTINCT
reasons (the absent sentinel 0 / the community-rejected 0o600 = 384 / a
decimal/octal-confused 644), each an independent divergence from the exact
pinned value. The witness snippet text coincides only because the carrier admits
a single input; it is elaborated against each rival's own impl and each FAILS
against the frozen solution (machine-checked both halves).

AXIOM lane: EMPTY (the ``axioms`` region declares no ``axiom``; the default mode
is a value supplied directly, modeled deeply as its concrete numeric value).
There is no axiom-soundness obligation to probe, and the gate ignores
``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "django__django-10914"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchor: the entire frozen constant-return body plus the
# ---- closing marker, so the swap lies wholly inside the single
# ---- `-- impl-start`/`-- impl-end` region and is unique in Solution.lean
# ---- (both facts asserted at load by _swap). No case here retunes the proof
# ---- body: the frozen tactic (`loom_solve`) closes each reshape below
# ---- unchanged, since every variant returns a value definitionally equal to
# ---- 420.
_IMPL = "    return 420\n    -- impl-end"

assert _BASE.count(_IMPL) == 1, "function impl region drifted from expected text"


def _impl(new_body):
    """Full Solution.lean variant with ONLY the impl region body replaced (the
    closing `-- impl-end` marker is re-appended)."""
    return _swap(_BASE, _IMPL, new_body + "\n    -- impl-end")


# ---- witness preamble. The spec is a `method` CONTRACT, not a bare predicate,
# ---- so a witness reaches it through Velvet's own tester machinery:
# ---- `defaultFileModeTester = false` says the extracted program's result
# ---- violates the method's postcondition. The query takes no argument, so the
# ---- tester is a nullary `Bool`. Checked in a file whose `prove_correct` block
# ---- has been stripped, so no tactic script can mask the verdict.
_WITNESS = (
    "extract_program_for defaultFileMode\n"
    "prove_precondition_decidable_for defaultFileMode\n"
    "prove_postcondition_decidable_for defaultFileMode\n"
    "derive_tester_for defaultFileMode\n\n"
    "example : defaultFileModeTester = false := by\n  decide\n"
)


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # impls that MUST verify. If a faithful correct impl cannot verify, the
    # spec is SPEC-TOO-STRONG. The post-image is point-wise over a zero-argument
    # value, so no induction is needed and each reproof stays within the frozen
    # `loom_solve` script (every reshape returns a value definitionally equal to
    # 420).
    # =====================================================================
    {
        "id": "pos-named-local",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: bind the default mode to a typed local, then return it. Same
        # value flow; the frozen proof still closes.
        "module": _impl("    let m : Nat := 420\n    return m"),
        "rationale": (
            "binding the default mode to a typed local before returning it "
            "leaves the returned value unchanged, so C1 (mode = 420) still "
            "discharges; a structurally-different but correct reshape must "
            "verify. If it fails => SPEC-TOO-STRONG (over-fit to the "
            "single-literal spelling)."
        ),
    },
    {
        "id": "pos-arith-form",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: return the default mode as its positional expansion
        # (6*64 + 4*8 + 4 = 420), i.e. the same numeric value spelled as the
        # arithmetic of its octal digits rather than as the decimal literal.
        # This is the honest grounded-value control: the value is computed, not
        # echoed from an oracle, and reduces definitionally to 420.
        "module": _impl("    return (6 * 64 + 4 * 8 + 4)"),
        "rationale": (
            "the default mode spelled as the arithmetic of its octal digits "
            "(6*64 + 4*8 + 4) is definitionally 420, so C1 holds; a "
            "structurally-different correct reshape defends the soundness "
            "surface. The nagini sibling's grounded-oracle positive returned the "
            "@Pure default_mode() (== 420); on this carrier there is no such "
            "helper, so the grounded-value analogue is the computed octal "
            "expansion. If it fails => SPEC-TOO-STRONG."
        ),
    },

    # =====================================================================
    # ADMISSIBILITY — the query has no `require` clause, so there is no
    # precondition that could exclude a normal input; the usual "a normal input
    # satisfies the precondition" probe is vacuously satisfied (the domain is
    # the empty tuple). The residual admissibility risk on a total domain is
    # that the post-image is UNSATISFIABLE / DEGENERATE — a spec no impl can
    # meet reads exactly like a spec every impl meets. This case discharges an
    # in-region `assert` that the default mode really is a definite value equal
    # to its octal expansion AND non-zero (not the absent sentinel): it
    # establishes the post-image is jointly satisfiable and non-degenerate. The
    # impl is kept returning 420 so the method's own obligation still discharges,
    # and the assert is live.
    # =====================================================================
    {
        "id": "admiss-mode-definite-nonzero",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl(
            "    assert (with_name_prefix `assert\n"
            "      ((420 : Nat) = 6 * 64 + 4 * 8 + 4 ∧ (420 : Nat) ≠ 0))\n"
            "    return 420"),
        "rationale": (
            "the post-image is satisfiable AND non-degenerate: the default mode "
            "is a definite value equal to its octal expansion and is non-zero "
            "(not the absent/unset sentinel). The in-region assert must discharge "
            "(else an unsatisfiable obligation would read as trivially met); the "
            "impl is kept returning 420 so C1 still discharges too. The nagini "
            "sibling's admissibility control asserted the same shape (default "
            "== 420 and default is not None) over its absent-override case."
        ),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at
    # the single input point and the refinement argument that its faithful real
    # counterpart would NOT resolve the failing test.
    # =====================================================================
    {
        "id": "weak-absent-sentinel",
        "kind": "uniqueness",
        "expect": "reject",
        # The exact pre-fix behaviour: yield the unset/absent sentinel (modeled
        # as 0, mapping.md §2) instead of the definite default mode. Violates C1
        # on the "definite value" facet.
        "module": _impl("    return 0"),
        "refinement": (
            "this is the pre-change behaviour: the default mode is left as the "
            "unset/absent sentinel. Its faithful real patch is the unpatched "
            "repo, under which the downstream store hands the OS no definite mode "
            "and the observed permission depends on how the upload was buffered. "
            "The failing test asserts the stored file's permission mode equals "
            "0o644, which the absent sentinel does not produce, so it would NOT "
            "resolve. This is the exact defect the fix corrects."
        ),
        "rationale": (
            "REJECT from C1 (mode = 420): the unset sentinel 0 is not the "
            "definite default the post-image pins. This is the only rival "
            "attacking the DEFINITE-value facet independently. If it verified => "
            "SPEC-TOO-WEAK (the absent-default regression would go unnoticed)."
        ),
        "witness": _WITNESS,
    },
    {
        "id": "weak-rejected-0o600",
        "kind": "uniqueness",
        "expect": "reject",
        # A definite but WRONG mode: 0o600 == 384 — the value the issue thread
        # first floated and the community explicitly REJECTED in favour of
        # 0o644. Non-zero (a definite policy), so it clears the sentinel facet,
        # but the specific value is wrong — C1 fails.
        "module": _impl("    return 384"),
        "refinement": (
            "0o600 == 384 is the default the issue discussion first proposed and "
            "then explicitly rejected in favour of 0o644. A real patch shipping "
            "that value would hand the store a definite but different mode; the "
            "failing test asserts the stored file's mode equals exactly 0o644, so "
            "0o600 would NOT resolve. A definite-but-wrong near-miss — the "
            "sub-domain a tight post-image must defend and a plausible half-fix "
            "only misses by the specific value."
        ),
        "rationale": (
            "REJECT from C1 (mode = 420): 384 is a definite non-zero value (it "
            "clears the sentinel facet) but is not the SPECIFIC default 0o644 "
            "the post-image pins. If it verified => SPEC-TOO-WEAK (the exact "
            "default value would be unpinned, only its definiteness enforced)."
        ),
        "witness": _WITNESS,
    },
    {
        "id": "weak-decimal-octal-confusion",
        "kind": "uniqueness",
        "expect": "reject",
        # A definite but WRONG mode: the decimal literal 644 — the classic
        # decimal/octal confusion for this exact fix (a patch author writing
        # `644` rather than `0o644 == 420`). Non-zero, so it clears the sentinel
        # facet, but the numeric value is wrong — C1 fails.
        "module": _impl("    return 644"),
        "refinement": (
            "the intended mode is the OCTAL 0o644 == decimal 420; the decimal "
            "literal 644 is the octal 0o1204 — a different, nonsensical chmod "
            "mode. A real patch that wrote the digits 644 without the octal "
            "prefix would hand the store 644 as the numeric mode, and the failing "
            "test asserts the mode equals 0o644 == 420, so 644 would NOT resolve. "
            "A distinct wrong definite value from the 0o600 rival, catching the "
            "decimal/octal-confusion failure mode specifically."
        ),
        "rationale": (
            "REJECT from C1 (mode = 420): 644 is a definite non-zero value but "
            "is not the pinned default 420 (0o644); it is the decimal-vs-octal "
            "confusion. A distinct wrong-value point from weak-rejected-0o600, "
            "so the exact-value clause is attacked from two independent "
            "directions. If it verified => SPEC-TOO-WEAK."
        ),
        "witness": _WITNESS,
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The nagini sibling has 8 SPEC cases (2 soundness
# positives, 1 admissibility, 5 uniqueness rivals; AXIOM_TESTS empty) over the
# resolver `resolve_storage_mode(override: Optional[int])`, whose postcondition
# has FOUR clauses: C1 override-passthrough, and C2/C3/C4 the
# definite-default-on-absent-override clauses (Result is not None / ==
# default_mode() / == 420). THIS bundle models only the purely-functional core
# the fix turns on — a single zero-argument constant provider `defaultFileMode :
# () -> Nat` whose only postcondition is `mode = 420` (the nagini C4, with C2/C3
# folded into the same equality). The override input, and therefore the
# passthrough clause C1 and every rival that abuses a present override, do not
# exist on this carrier (the resolver's override-handling is downstream behaviour
# the gold patch does not touch — the patch changes ONLY the default value).
# Every nagini case is accounted for below.
#
#   nagini case            -> here
#   -----------------------------------------------------------------------
#   pos-branch-reorder     -> pos-named-local                RE-SHAPED
#   pos-grounded-oracle    -> pos-arith-form                 RE-EXPRESSED
#   admiss-roundtrip       -> admiss-mode-definite-nonzero   RE-AIMED
#   weak-default-none      -> weak-absent-sentinel           PORTED
#   weak-wrong-default     -> weak-rejected-0o600            PORTED
#   weak-always-default    -> (none)                         NO COUNTERPART
#   weak-swap-branches     -> (none)                         NO COUNTERPART
#   weak-partial-zero      -> (none)                         NO COUNTERPART
#                             (+ weak-decimal-octal-confusion ADDED)
#
# 2 ported, 1 re-expressed, 1 re-aimed, 2 re-shaped positives, 3 no-counterpart;
# 1 rival added for exact-value coverage.
#
# PORTED (2): the DEFAULT-VALUE rivals carry across intact — only the carrier
#   changes from a returned Optional[int] on the absent-override branch to a
#   returned Nat over the empty domain. weak-default-none (the pre-patch absent
#   default) becomes weak-absent-sentinel (return 0, the unset sentinel per
#   mapping.md §2), rejected by C1 on the definiteness facet. weak-wrong-default
#   (0o600 == 384, the community-rejected proposal) becomes weak-rejected-0o600,
#   rejected by C1 on the exact-value facet. Both carry their nagini refinement
#   argument (unpatched-repo / rejected-proposal fails the same F2P assertion).
# RE-EXPRESSED (pos-grounded-oracle -> pos-arith-form): the nagini grounded-oracle
#   returned the @Pure default_mode() (a constant == 420) on the absent branch.
#   This carrier has no pure helper to reference; the grounded-value analogue is
#   the computed octal expansion 6*64+4*8+4 (== 420, definitionally), which is
#   likewise a value PRODUCED rather than echoed from an oracle.
# RE-SHAPED (pos-branch-reorder -> pos-named-local): the nagini positive inverted
#   the resolver's guard (present-branch first). There is no branch to reorder on
#   this constant carrier, so the cheapest structurally-different correct impl is
#   the typed-local staging (bind 420, then return it).
# RE-AIMED (admiss-roundtrip -> admiss-mode-definite-nonzero): the nagini
#   admissibility control asserted the post shape over its two F2P/P2P-shaped
#   inputs (None -> 420; a concrete override -> passthrough). This query has no
#   precondition and no input, so that probe is vacuous; it is re-aimed at the
#   residual total-domain risk — an UNSATISFIABLE/degenerate post-image — by a
#   live in-region assert that 420 is a definite value equal to its octal
#   expansion and non-zero (its P2P/passthrough half has no counterpart, the
#   override input being unmodeled).
# NO COUNTERPART (3): weak-always-default, weak-swap-branches, and
#   weak-partial-zero all attack the nagini OVERRIDE-PASSTHROUGH clause C1 —
#   respectively by ignoring a present override, swapping the two return arms,
#   and special-casing the boundary override == 0. This carrier has NO override
#   input (mapping.md: the fix changes only the default value; the resolver's
#   override handling is unchanged and unmodeled), so there is no passthrough
#   clause to violate, no arms to swap, and no override sub-domain to
#   special-case. Omitted because the modeled surface does not include that
#   behaviour, NOT because it was hard to prove.
# ADDED (1, no nagini counterpart): weak-decimal-octal-confusion returns the
#   decimal literal 644 — the classic decimal/octal confusion for this exact fix
#   (writing `644` rather than `0o644 == 420`). A distinct definite-but-wrong
#   value from weak-rejected-0o600, so the exact-value clause C1 is attacked from
#   two independent directions. A real divergence with a machine-checked witness,
#   not fabricated wrongness.
# FRAME-MUTATION: VACUOUS. Referentially-transparent backend, no `mut` binder, no
#   heap, no aliasing, no permission system, and no input at all. The nagini
#   sibling itself records this class as inapplicable (its only input is an
#   immutable scalar with no heap permission). No substitute fabricated.
# DIVERGENCE - the class is INAPPLICABLE to this impl and CLOSED BY THE
#   SEMANTICS against any rival that manufactures it. The frozen impl is
#   LOOP-FREE (straight-line a single ``return`` over immutable values, no loop
#   and no recursion), so there is no control flow here to make diverge: a
#   diverging rival cannot be obtained by mutating this body, it has to bring a
#   loop of its own. When it does, the semantics refuse it. This bundle sets
#   ``loom.semantics.termination "total"`` AND carries
#   ``open TotalCorrectness``, and the ``open`` is the line that actually
#   selects the semantics: both namespaces define
#   ``WPGen.forWithInvariantLoop``, the later ``open`` wins, and the
#   ``PartialCorrectness`` version takes a loop measure and DISCARDS it, so the
#   two lines have to move together and they do here. Under the total scope a
#   postcondition is claimed of ALL runs and not only of terminating ones, so a
#   spliced loop owes a descent obligation ``measure b' < measure b``.
#   Re-measured on this bundle with a real build: a
#   ``while spin > 0 do spin := spin`` prefix carrying ``decreasing spin`` is
#   REJECTED on the measure's own goal (``case «decreasing_1: spin» ... ⊢ spin
#   < spin``). Dropping the clause rather than faking it is refused even
#   earlier, by the elaborator's own check (``Decreasing annotations are
#   required in total correctness semantics``). So divergence neither applies
#   to this impl nor discharges the ``ensures`` clauses vacuously if a rival
#   introduces it.
#
# BINDER / CLAUSE / POINT COVERAGE. The modeled query takes NO argument, so there
#   is no input binder to vary and the extracted tester is a nullary `Bool`.
#   There is exactly ONE input point (the empty tuple); `pts=1` is therefore
#   STRUCTURAL, not a coverage defect — the coverage tool's "move the witness to
#   a distinguishing input" finding is N/A because no distinct input exists. What
#   coverage the battery CAN carry is over the independent FACETS of the single
#   clause C1, and it does: the DEFINITE-value facet (mode is not the absent
#   sentinel) is attacked by weak-absent-sentinel, and the EXACT-value facet
#   (mode is specifically 0o644, not merely definite) is attacked by
#   weak-rejected-0o600 and weak-decimal-octal-confusion from two independent
#   directions. Both positives and the admissibility assert defend the clause.
#   The three reject witnesses share the same snippet text ONLY because the
#   carrier admits a single input; each is elaborated against its own rival impl
#   (three distinct divergences) and each FAILS against the frozen solution.
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job; this bundle declares no
# axiom (the default mode is a value modeled deeply as its concrete numeric
# value), so there is nothing there to probe.
AXIOM_TESTS = []
