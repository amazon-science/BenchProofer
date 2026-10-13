"""properties.py — G-PBT falsification battery for django__django-15161 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside a ``prove_correct`` tactic body, is changed —
both of which the consumer spec view elides — so ``markers.same_spec`` holds and
every ``prove_correct`` obligation survives) and swaps in a candidate
implementation; it is checked by the real verifier. ``expect:"verify"`` passes
iff (in scope AND verifies); ``expect:"reject"`` passes iff (in scope AND does
NOT verify AND its refutation ``witness`` discriminates: the witness must
elaborate against the rival and FAIL against the frozen solution).

DEFENDED SURFACE (one contracted method over a dotted import-path domain,
carriers ``List Char`` and ``Option (List Char)``). A node reports one of two
import paths for its type. The method ``deconstructPath`` takes four read-only
inputs — the node's defining module, its class name, an optional assigned
simplified public path, and a boolean flag saying whether the runtime type is
exactly the type that public path was assigned to — and pins the reported path
with two top-level clauses:

  ensures (publicPath ≠ none ∧ exactType = true) → out = publicPath.getD []
  ensures ¬(publicPath ≠ none ∧ exactType = true) →
    out = definingModule ++ ['.'] ++ className

There is no ``require`` clause: the admitted domain is total, so every value of
every carrier is in scope, and each free input must satisfy the post-image at
EVERY value it takes. That totality is what makes the partial-domain rivals
below refutable at a concrete point. The first clause is the SIMPLIFIED-PATH
arm; the second is the DEFINING-MODULE-QUALIFIED arm, which governs both an
un-assigned node (``publicPath = none``) and an assigned node whose runtime type
is NOT the exact assigned type (``exactType = false`` — the subtype case).

ADVERSARIAL READ of the nagini classes:
  * FRAME-MUTATION — VACUOUS on this backend. It exists on nagini because a
    read-only input may carry a fractional heap permission an impl can overwrite
    to build its answer. Lean and Velvet are referentially transparent: every
    parameter is an immutable value (this bundle declares NO ``mut`` binder),
    there is no heap and no aliasing, so there is no read-only input to mutate
    and no substitute probe to build. Not fabricated — reported as an omission.
  * BRANCH-MISSELECTION / prepatch echo — APPLIES to the first clause. A rival
    that always takes the qualified arm ignores the assigned simplified path and
    reports the long defining-module name where the short public path is due.
  * PARTIAL-DOMAIN / VALUE — APPLIES to both clauses: a rival right on part of
    the domain but diverging on a sub-domain (a truncated simplified path on the
    simplified arm; a missing separator on the qualified arm).
  * FLAG-SENSITIVITY — APPLIES to ``exactType``. A rival that consults only
    whether a public path is assigned, never whether the type is exact, gets the
    un-assigned case right and the subtype case wrong (reports the short path for
    a type the short path does not name).
  * UNGROUNDED-ORACLE ECHO — N/A. Both post-images are total functions of the
    method's own arguments (``publicPath.getD []`` and
    ``definingModule ++ ['.'] ++ className``); the ``axioms`` region is empty,
    so there is no opaque answer key to echo. Instead we carry honest
    cheapest-reshape POSITIVE CONTROLS (``pos-*``).

WITNESS PLACEMENT. Rivals do not share a refutation point unless they fail there
for the same reason. The four reject witnesses move all four binders:
``publicPath`` over ``some``/``none``, ``exactType`` over both booleans, and
``definingModule`` / ``className`` over distinct strings — so no binder is
pinned across the battery and each rival's sub-domain claim is machine-checked
rather than asserted. The truncated-path rival is refuted at a two-character
public path (a one-character path drops to ``[]`` and would coincide with the
un-set marker on other arms), and the missing-separator rival is refuted on the
qualified arm where the dot is load-bearing.

AXIOM lane: EMPTY (``axioms`` region declares no ``axiom``; the import-path
selection IS the function under specification, modeled deeply). There is no
axiom-soundness obligation to probe, and the gate ignores ``AXIOM_TESTS``.
"""
from pathlib import Path

INSTANCE = "django__django-15161"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchor. The two-arm choice `definingModule ++ ['.'] ++
# ---- className` also appears in the frozen `ensures` (the spec view), so it is
# ---- NOT unique on its own; the whole `let out … return out` block, however,
# ---- occurs only inside the impl region. Swapping the entire block keeps the
# ---- surgery strictly in-region (same_spec holds) and keeps the anchor unique
# ---- (both facts asserted at load by _swap).
_IMPL = (
    "    let out : List Char :=\n"
    "      if publicPath ≠ none ∧ exactType = true then\n"
    "        publicPath.getD []\n"
    "      else\n"
    "        definingModule ++ ['.'] ++ className\n"
    "    return out\n"
)


# ---- witness preamble. The spec here is a `method` CONTRACT, not a bare
# ---- predicate, so a witness reaches it through Velvet's own tester
# ---- machinery: `deconstructPathTester args = false` says the extracted
# ---- program's result violates the method's postcondition at that concrete
# ---- input. Checked in a file whose `prove_correct` block has been stripped,
# ---- so no tactic script can mask the verdict.
_TESTER = ("extract_program_for deconstructPath\n"
           "prove_precondition_decidable_for deconstructPath\n"
           "prove_postcondition_decidable_for deconstructPath\n"
           "derive_tester_for deconstructPath\n\n")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # impls that MUST verify. If a faithful correct impl cannot verify, the
    # spec is SPEC-TOO-STRONG. Each keeps both obligations and only reshapes
    # the executable surface; the contracts are point-wise over immutable
    # values, so `loom_solve` closes each reproof unchanged.
    # =====================================================================
    {
        "id": "pos-branch-reorder",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: negate the guard and swap the two arms. Same decision, same
        # value on each arm; the post pins the VALUE, not the branch order.
        "module": _swap(
            _BASE, _IMPL,
            "    let out : List Char :=\n"
            "      if ¬(publicPath ≠ none ∧ exactType = true) then\n"
            "        definingModule ++ ['.'] ++ className\n"
            "      else\n"
            "        publicPath.getD []\n"
            "    return out\n"),
        "rationale": "negating the guard and swapping the arms preserves the "
                     "same two-way choice, so both clauses "
                     "(`… → out = publicPath.getD []` and "
                     "`… → out = definingModule ++ ['.'] ++ className`) still "
                     "discharge; a correct reshape must verify (else "
                     "SPEC-TOO-STRONG on branch order).",
    },
    {
        "id": "pos-let-bindings",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: bind each arm's value to a typed local first, then select.
        # Same value flow, so both clauses still hold pointwise.
        "module": _swap(
            _BASE, _IMPL,
            "    let simplified : List Char := publicPath.getD []\n"
            "    let qualified : List Char := definingModule ++ ['.'] ++ className\n"
            "    let out : List Char :=\n"
            "      if publicPath ≠ none ∧ exactType = true then simplified\n"
            "      else qualified\n"
            "    return out\n"),
        "rationale": "binding each arm's value to a typed local before the "
                     "selection leaves the produced value on each arm "
                     "unchanged, so both clauses still discharge; a correct "
                     "reshape must verify.",
    },

    # =====================================================================
    # ADMISSIBILITY — re-aimed. The sibling's admissibility case re-establishes
    # a precondition for a normal input. No method here has a `require` clause,
    # so nothing could exclude a normal input and that probe is vacuous. The
    # residual admissibility risk on a total domain is that the post-image is
    # UNSATISFIABLE / DEGENERATE at the interesting point — a spec no impl can
    # meet reads exactly like a spec every impl meets. This case discharges an
    # in-region `assert` at the F2P-shaped point: for a concrete assigned public
    # path the post-image demands EXACTLY that path on the simplified arm, the
    # defining-module-qualified name on the other arm, and (non-degeneracy) that
    # the two differ — so the obligation is live, not trivially satisfiable. The
    # impl is kept verbatim so both ensures clauses still discharge; the assert
    # is live — replacing it with a false claim about the same point leaves an
    # unsolved goal.
    # =====================================================================
    {
        "id": "admiss-postimage-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _IMPL,
            "    assert (with_name_prefix `assert\n"
            "      ((((some ['V'] : Option (List Char)) ≠ none ∧ true = true) ∧\n"
            "        ((some ['V'] : Option (List Char)).getD [] = ['V'])) ∧\n"
            "       ((['e'] ++ ['.'] ++ ['V'] : List Char) ≠ ['V'])))\n"
            + _IMPL),
        "rationale": "the post-image is satisfiable AND non-degenerate at the "
                     "F2P-shaped point: for a concrete assigned public path it "
                     "demands exactly that path on the simplified arm and a "
                     "strictly LONGER defining-module-qualified name on the "
                     "other arm (the two provably differ). The in-region assert "
                     "must discharge (else an unsatisfiable / degenerate "
                     "obligation); the impl is kept verbatim so both ensures "
                     "clauses still discharge too.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at
    # a concrete input and the refinement argument that its faithful real
    # counterpart would NOT resolve the failing tests.
    # =====================================================================
    {
        "id": "weak-always-qualified",
        "kind": "uniqueness",
        "expect": "reject",
        # Prepatch echo: always report the defining-module-qualified name,
        # ignoring the assigned simplified public path entirely. This is
        # literally the pre-patch behaviour.
        "module": _swap(
            _BASE, _IMPL,
            "    let out : List Char := definingModule ++ ['.'] ++ className\n"
            "    return out\n"),
        "refinement": "a counterpart that always reports the long "
                      "defining-module-qualified name ignores the node's "
                      "assigned simplified public path, so the failing tests "
                      "that expect the short public path (and the writer test "
                      "that expects the short `models.X` forms) still observe "
                      "the long path and still fail. It would NOT resolve.",
        "rationale": "REJECT from clause 1 "
                     "(`(publicPath ≠ none ∧ exactType = true) → "
                     "out = publicPath.getD []`): with a public path assigned "
                     "and the type exact, the impl reports the qualified name "
                     "where the post-image demands the simplified path.",
        "witness": _TESTER +
                   "example : deconstructPathTester (\"m\".toList) (\"c\".toList) "
                   "(some \"A\".toList) true = false := by\n  decide\n",
    },
    {
        "id": "weak-truncate-simplified",
        "kind": "uniqueness",
        "expect": "reject",
        # Partial-domain: on the simplified arm, drop the last character of the
        # assigned public path. Correct on the qualified arm, wrong only on the
        # simplified arm — and only for a public path of length ≥ 2.
        "module": _swap(
            _BASE, _IMPL,
            "    let out : List Char :=\n"
            "      if publicPath ≠ none ∧ exactType = true then\n"
            "        (publicPath.getD []).dropLast\n"
            "      else\n"
            "        definingModule ++ ['.'] ++ className\n"
            "    return out\n"),
        "refinement": "a counterpart that drops the last character of the "
                      "reported public path emits a truncated import path, so "
                      "the failing tests that compare the reported path against "
                      "the exact expected string still fail. It would NOT "
                      "resolve.",
        "rationale": "REJECT from clause 1 "
                     "(`… → out = publicPath.getD []`): the impl returns the "
                     "public path minus its last character. Correct on the "
                     "qualified sub-domain, wrong on the simplified arm "
                     "(partial-domain). Refuted at a two-character public path, "
                     "since a one-character path would drop to `[]` and coincide "
                     "with degenerate values on the other arm.",
        "witness": _TESTER +
                   "example : deconstructPathTester (\"m\".toList) (\"c\".toList) "
                   "(some \"AB\".toList) true = false := by\n  decide\n",
    },
    {
        "id": "weak-drop-separator",
        "kind": "uniqueness",
        "expect": "reject",
        # Partial-domain on the QUALIFIED arm: concatenate module and name
        # WITHOUT the '.' separator. Correct on the simplified arm, wrong on the
        # qualified arm.
        "module": _swap(
            _BASE, _IMPL,
            "    let out : List Char :=\n"
            "      if publicPath ≠ none ∧ exactType = true then\n"
            "        publicPath.getD []\n"
            "      else\n"
            "        definingModule ++ className\n"
            "    return out\n"),
        "refinement": "a counterpart that joins the defining module and class "
                      "name without the separating dot emits a malformed import "
                      "path, so the failing tests that pin the qualified path "
                      "exactly (dot included) still fail. It would NOT resolve.",
        "rationale": "REJECT from clause 2 "
                     "(`¬(…) → out = definingModule ++ ['.'] ++ className`): the "
                     "impl omits the `['.']` separator the post-image pins in. "
                     "Correct on the simplified sub-domain, wrong on the "
                     "qualified arm (partial-domain). Refuted at "
                     "`publicPath = none` with distinct module/name strings, so "
                     "the missing dot is observable.",
        "witness": _TESTER +
                   "example : deconstructPathTester (\"x\".toList) (\"y\".toList) "
                   "none false = false := by\n  decide\n",
    },
    {
        "id": "weak-ignores-exacttype",
        "kind": "uniqueness",
        "expect": "reject",
        # Flag-sensitivity near-miss: consult only whether a public path is
        # assigned, never whether the runtime type is exact. Gets the un-set
        # case right; wrong on the SUBTYPE case (path assigned but the type is
        # not the exact one), where the long qualified path is due.
        "module": _swap(
            _BASE, _IMPL,
            "    let out : List Char :=\n"
            "      if publicPath ≠ none then\n"
            "        publicPath.getD []\n"
            "      else\n"
            "        definingModule ++ ['.'] ++ className\n"
            "    return out\n"),
        "refinement": "a counterpart that reports the simplified public path "
                      "whenever one is assigned — regardless of whether the "
                      "runtime type is the exact assigned type — reports the "
                      "short path for a subtype the short path does not name, so "
                      "the failing tests that require the long "
                      "defining-module-qualified path for such a type still "
                      "fail. It would NOT resolve.",
        "rationale": "REJECT from clause 2 "
                     "(`¬(publicPath ≠ none ∧ exactType = true) → "
                     "out = definingModule ++ ['.'] ++ className`): with a public "
                     "path assigned but `exactType = false`, the antecedent's "
                     "conjunction is false, so the post-image demands the "
                     "qualified name — but the impl reports the simplified path. "
                     "Refuted at `exactType = false` with a public path set, the "
                     "sub-domain no other rival on this obligation probes; this "
                     "is what varies `exactType` across the battery rather than "
                     "holding it fixed at true.",
        "witness": _TESTER +
                   "example : deconstructPathTester (\"p\".toList) (\"q\".toList) "
                   "(some \"Z\".toList) false = false := by\n  decide\n",
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 6 cases (1 soundness
# positive, 1 admissibility, 4 uniqueness rivals); every one is accounted for.
#
#   sibling case                  -> here
#   ---------------------------------------------------------------------
#   pos-control-branch-reorder    -> pos-branch-reorder             PORTED
#   admiss-precond-name-no-dot    -> admiss-postimage-nondegenerate RE-AIMED
#   wrong-branch-prepatch-echo    -> weak-always-qualified          PORTED
#   partial-truncate-configured   -> weak-truncate-simplified       PORTED
#   partial-drop-dot-fallback     -> weak-drop-separator            PORTED
#   frame-mutate-name             -> (none)                         VACUOUS
#
# 4 ported, 1 re-aimed, 1 vacuous = 6.
#
# RE-AIMED (admissibility): the sibling's case re-establishes a precondition for
#   a normal input. This method has NO `require` clause, so nothing could
#   exclude a normal input and that probe is vacuous. It is re-aimed at the
#   residual admissibility risk on a total domain — that the post-image is
#   UNSATISFIABLE / DEGENERATE at the interesting point — by discharging an
#   in-region assert that the post-image demands exactly the assigned public
#   path on one arm and a strictly longer qualified name on the other.
# VACUOUS (frame/permission-mutation): the sibling already flags this as the #1
#   weakness class because `name` carries a fractional heap permission a rival
#   can overwrite. This backend is referentially transparent and this bundle
#   declares NO `mut` binder, so there is no read-only input to overwrite and no
#   substitute probe. No case fabricated.
#
# ADDED (1, no sibling counterpart): weak-ignores-exacttype. The sibling's
#   configured/fallback choice hinges on a single derived boolean; here the
#   choice hinges on TWO inputs — `publicPath ≠ none` AND `exactType = true` —
#   and the second is the subtype discriminator the spec docstring calls out.
#   A battery whose rivals all hold `exactType = true` would never move that
#   binder, so a rival mishandling only the subtype case (short path reported
#   for a non-exact type) would go uncaught. This rival is that case, refuted at
#   `exactType = false` with a public path set. Not fabricated wrongness: it is
#   a real divergence from clause 2 with a machine-checked witness and the
#   refinement argument for why its faithful counterpart would still leave the
#   failing tests failing.
#
# BINDER COVERAGE. The four reject witnesses move all four binders:
#   definingModule ∈ {m, x, p}, className ∈ {c, y, q},
#   publicPath ∈ {some "A", some "AB", none, some "Z"},
#   exactType ∈ {true, false}. No binder is pinned across the battery, and each
#   rival is refuted at a distinct input point.
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job and this bundle declares no
# axiom, so there is nothing there to probe.
AXIOM_TESTS = []
