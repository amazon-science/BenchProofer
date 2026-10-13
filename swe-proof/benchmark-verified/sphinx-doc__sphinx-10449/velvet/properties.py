"""properties.py — G-PBT falsification battery for sphinx-doc__sphinx-10449 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside an ``-- impl-start`` /
``-- impl-end`` region, or inside a ``prove_correct`` tactic body, is changed —
both of which the consumer spec view elides, so ``markers.same_spec`` holds and
every ``prove_correct`` obligation survives) and swaps in a candidate
implementation. It is checked by the real verifier. ``expect:"verify"`` passes
iff (in scope AND verifies); ``expect:"reject"`` passes iff (in scope AND does
NOT verify AND its refutation ``witness`` discriminates: the witness must
elaborate against the rival and FAIL against the frozen solution).

DEFENDED SURFACE (two contracted methods; the axioms region is EMPTY):

  * ``emitReturnTypeEntry hasReturnAnno returnInArgs returnAnnotation
    omitNoneReturnType``
      ensures out = returnTypeEntry hasReturnAnno returnInArgs returnAnnotation
                                    omitNoneReturnType
    ONE load-bearing clause pinning the whole decision: an entry is produced
    (``some returnAnnotation``) exactly when the object carries a return
    annotation AND the description does not already declare one — with the SOLE
    exception that a ``None`` annotation is dropped to ``none`` when omission is
    requested. Otherwise ``none``.

  * ``emitReturnTypeForKind kind hasReturnAnno returnInArgs returnAnnotation``
      (1) ensures out = returnTypeEntryForKind kind hasReturnAnno returnInArgs
                                               returnAnnotation
            the whole kind-aware decision: for a class kind the entry is built
            with omission on; for every other kind, with omission off.
      (2) ensures (kind = class ∧ hasReturnAnno ∧ ¬returnInArgs ∧
                   returnAnnotation = "None") → out = none
            the discriminating clause: a class whose annotation is ``None`` must
            produce NO entry.
      (3) ensures (kind ≠ class ∧ hasReturnAnno ∧ ¬returnInArgs)
                   → out = some returnAnnotation
            the completeness clause: a non-class documented object that carries
            an as-yet-undeclared annotation must produce the entry carrying that
            annotation — a class-only omission may not strip it.

All inputs are FREE (no ``require`` clause on either method), which is what makes
the partial-domain rivals below refutable at a concrete point.

ADVERSARIAL READ of the nagini classes:
  * FRAME-MUTATION — VACUOUS on this backend. The nagini sibling rejects an impl
    that WRITES a read-only half-permission input to prove the read-only frame
    holds. Lean and Velvet are referentially transparent and neither method
    declares a ``mut`` binder, so there is no read-only input to overwrite and no
    substitute probe to build. Reported N/A in the footer, not fabricated.
  * UNGROUNDED-ORACLE ECHO — N/A. ``returnTypeEntry`` / ``returnTypeEntryForKind``
    are total, fully unfolded functions of each method's own arguments (concrete
    ``def``s in the ``pure`` region; the ``axioms`` region is EMPTY), so there is
    no opaque answer-key an impl could echo. The positive controls are honest
    cheapest-reshape variants.
  * PARTIAL-DOMAIN / VALUE — the main class. A rival correct on part of the input
    domain but diverging on a sub-domain: dropping the omission path, over-
    applying it, fabricating fixed text, ignoring one of the two guard inputs, or
    (on the dispatcher) mis-selecting the per-kind policy. Each attacks a specific
    clause and is refuted where it diverges.

WITNESS MECHANICS. Each spec is a ``method`` CONTRACT, not a bare predicate, so a
witness reaches it through Velvet's own tester machinery (``extract_program_for``
/ ``derive_tester_for``): ``<name>Tester args = false`` says the extracted
program's result violates the postcondition at that concrete input. Every input
here is a ``Bool`` / ``List Char`` literal and both impls are loop-free, so the
extracted program reduces under kernel ``decide`` — the witness ELABORATES
against the rival. The frozen impl SATISFIES the postcondition at each witness
point, so its tester returns ``true`` and ``= false`` FAILS against gold — the
discriminator. The witness file has its ``prove_correct`` blocks stripped, so no
tactic script can mask the verdict. No ``sorry`` / ``admit`` / ``native_decide``.

BINDER / CLAUSE COVERAGE. The nine reject witnesses probe nine distinct input
points and vary every INPUT binder of each obligation:
  * ``emitReturnTypeEntry`` (5 rivals): ``hasReturnAnno`` moves off ``true``
    (E-ignore-hasanno), ``returnInArgs`` off ``false`` (E-ignore-inargs),
    ``returnAnnotation`` off ``"None"`` (E-over-suppress / E-fixed-none /
    E-ignore-*), ``omitNoneReturnType`` off ``true`` (E-fixed-none / E-ignore-*).
  * ``emitReturnTypeForKind`` (4 rivals): ``kind`` moves off the class label
    (F-nonclass-suppress etc.), ``hasReturnAnno`` off ``true`` (F-always-emit),
    ``returnInArgs`` off ``false`` (F-ignore-inargs), ``returnAnnotation`` off
    ``"None"`` (F-always-emit / F-ignore-inargs).
Clause (2) is attacked by F-class-noomit, clause (3) by F-nonclass-suppress, and
clause (1) by the remaining dispatcher rivals.

AXIOM lane: EMPTY (the ``axioms`` region declares no ``axiom`` and there is no
deep-model reference; every sub-computation is a closed function of the free
inputs). The gate ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "sphinx-doc__sphinx-10449"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- Frozen impl-region anchors. Each lies wholly inside its method's
# ---- `-- impl-start` / `-- impl-end` region and is unique in the file (both
# ---- facts asserted at load by _swap). ----

# The whole entry-builder body (used by the entry rivals + the inner-guard
# positive reshapes it in place).
_ENTRY_IMPL = (
    "    if hasReturnAnno && !returnInArgs then\n"
    "      if (returnAnnotation == \"None\".toList) && omitNoneReturnType then\n"
    "        return none\n"
    "      else\n"
    "        return (some returnAnnotation)\n"
    "    else\n"
    "      return none"
)
assert _BASE.count(_ENTRY_IMPL) == 1, "entry impl anchor drifted"

# The inner omission guard, whose `&&` operands the positive control commutes.
_ENTRY_INNER = (
    "      if (returnAnnotation == \"None\".toList) && omitNoneReturnType then"
)
assert _BASE.count(_ENTRY_INNER) == 1, "entry inner-guard anchor not unique"

# The whole dispatcher body (used by the dispatcher rivals + the flag-hoist
# positive replaces it wholesale).
_KIND_IMPL = (
    "    if isClassKind kind then\n"
    "      let r ← emitReturnTypeEntry hasReturnAnno returnInArgs returnAnnotation true\n"
    "      return r\n"
    "    else\n"
    "      let r ← emitReturnTypeEntry hasReturnAnno returnInArgs returnAnnotation false\n"
    "      return r"
)
assert _BASE.count(_KIND_IMPL) == 1, "dispatcher impl anchor drifted"

# The dispatcher's declaration head, prepended-to by the admissibility assert.
_KIND_HEAD = (
    "    if isClassKind kind then\n"
    "      let r ← emitReturnTypeEntry hasReturnAnno returnInArgs returnAnnotation true"
)
assert _BASE.count(_KIND_HEAD) == 1, "dispatcher head anchor not unique"

# The dispatcher's frozen proof block — a tactic body is elided from the spec
# view, so the admissibility case may retune it without touching the spec.
_KIND_PROVE = "prove_correct emitReturnTypeForKind by\n  loom_solve\n"
assert _BASE.count(_KIND_PROVE) == 1, "dispatcher proof block drifted"


# ---- Witness preambles: reach each method contract through Velvet's tester.
# ---- The tester directives come from `Velvet.Std` (the frozen import); they are
# ---- appended to BOTH the rival file and the gold file, so `<name>Tester` /
# ---- `<name>Exec` exist on both sides by construction (no new declaration the
# ---- variant introduces is referenced). ----
_TE = (
    "extract_program_for emitReturnTypeEntry\n"
    "prove_precondition_decidable_for emitReturnTypeEntry\n"
    "prove_postcondition_decidable_for emitReturnTypeEntry\n"
    "derive_tester_for emitReturnTypeEntry\n\n"
)
_TK = (
    "extract_program_for emitReturnTypeForKind\n"
    "prove_precondition_decidable_for emitReturnTypeForKind\n"
    "prove_postcondition_decidable_for emitReturnTypeForKind\n"
    "derive_tester_for emitReturnTypeForKind\n\n"
)


# ---- Positive-control impl reshapes ----

# Commute the `&&` operands of the omission guard. Boolean `&&` is commutative,
# so the route choice and every produced value are unchanged; the frozen proof
# closes with `loom_solve` untouched.
_POS_ENTRY_INNER = (
    "      if omitNoneReturnType && (returnAnnotation == \"None\".toList) then"
)

# Hoist the per-kind omission flag into a boolean local and delegate ONCE,
# instead of branching first. `isClassKind kind` selects the same flag on every
# kind, so the delegated decision is identical on every input; the frozen proof
# closes with `loom_solve` untouched.
_POS_KIND = (
    "    let omitNone := isClassKind kind\n"
    "    let r ← emitReturnTypeEntry hasReturnAnno returnInArgs returnAnnotation omitNone\n"
    "    return r"
)


# ---- Admissibility (re-aimed) impl + proof ----

# Prepend a live in-region assert establishing the post-image is satisfiable AND
# non-degenerate at the discriminating points: a class with a `None` annotation
# produces NO entry, while a non-class object with the SAME annotation produces
# the entry carrying it. A false claim leaves an unsolved goal (verified during
# authoring). The dispatcher body is kept verbatim so the three ensures clauses
# still discharge.
_ADMISS_HEAD = (
    "    assert (with_name_prefix `assert\n"
    "      (returnTypeEntryForKind \"class\".toList true false \"None\".toList = none ∧\n"
    "       returnTypeEntryForKind \"function\".toList true false \"None\".toList\n"
    "         = some \"None\".toList))\n"
    + _KIND_HEAD
)
_ADMISS_PROVE = (
    "prove_correct emitReturnTypeForKind by\n"
    "  loom_solve\n"
    "  all_goals first\n"
    "    | exact ⟨rfl, rfl⟩\n"
    "    | rfl\n"
)


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # impls that MUST verify, one per obligation. If a faithful correct
    # reshape could not verify, the spec would be SPEC-TOO-STRONG.
    # =====================================================================
    {
        "id": "pos-commute-omission-guard",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _ENTRY_INNER, _POS_ENTRY_INNER),
        "rationale": "commuting the two `&&` operands of the omission guard "
                     "(`omitNoneReturnType && annotation-is-None` vs the reverse) "
                     "leaves the route choice and every produced value unchanged, "
                     "so `out = returnTypeEntry …` still holds on every input and "
                     "the frozen proof closes. A correct reshape must verify, else "
                     "SPEC-TOO-STRONG on operand order.",
    },
    {
        "id": "pos-hoist-omission-flag",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _KIND_IMPL, _POS_KIND),
        "rationale": "hoisting the per-kind omission flag into a boolean local and "
                     "delegating ONCE (instead of branching on the kind first) "
                     "selects the SAME flag on every kind, so the delegated "
                     "decision is identical; `out = returnTypeEntryForKind …` and "
                     "both implication clauses still discharge. A correct reshape "
                     "must verify.",
    },

    # =====================================================================
    # ADMISSIBILITY (re-aimed) — neither method has a `require` clause, so the
    # nagini "a normal F2P-shaped input satisfies the precondition" probe is
    # VACUOUS (nothing could exclude an in-domain input). Re-aimed at the
    # residual risk on a total domain: that the post-image is UNSATISFIABLE /
    # DEGENERATE at the interesting point (a spec no impl can meet reads exactly
    # like a spec every impl meets). The case discharges a live in-region assert
    # that the decision spec really does demand a class with a `None` annotation
    # produce NO entry while a non-class object with the SAME annotation produces
    # it — the impl kept verbatim so the method's own obligations discharge too.
    # =====================================================================
    {
        "id": "admiss-kind-policy-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_swap(_BASE, _KIND_HEAD, _ADMISS_HEAD),
                        _KIND_PROVE, _ADMISS_PROVE),
        "rationale": "the kind-aware decision is satisfiable AND non-degenerate at "
                     "the discriminating point: for a class kind carrying a `None` "
                     "annotation (not already declared) it demands NO entry "
                     "(`= none`), and for a non-class object carrying the SAME "
                     "annotation it demands the entry carrying it "
                     "(`= some returnAnnotation`). The in-region assert must "
                     "discharge (else the obligation is unsatisfiable at the point "
                     "the fix targets); the impl is kept verbatim so all three "
                     "ensures clauses discharge too. Re-aimed from the nagini "
                     "precondition-admits probe (vacuous: no `require` clause).",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals against emitReturnTypeEntry (clause
    # `out = returnTypeEntry …`). Each is loop-free (its extracted program
    # reduces under `decide`) with a machine-checked witness at a concrete input,
    # plus the argument that its faithful real counterpart would NOT resolve.
    # =====================================================================
    {
        "id": "weak-entry-drop-omission",
        "kind": "uniqueness",
        "expect": "reject",
        # THE pre-image behaviour: the entry is produced whenever the annotation
        # exists and is not already declared, with no omission path at all.
        "module": _swap(
            _BASE, _ENTRY_IMPL,
            "    if hasReturnAnno && !returnInArgs then\n"
            "      return (some returnAnnotation)\n"
            "    else\n"
            "      return none"),
        "refinement": "this is exactly the pre-image entry builder (no omission "
                      "path): for a documented object whose annotation is `None` "
                      "and for which omission is requested, it still produces the "
                      "`None` return-type entry — the spurious entry the failing "
                      "test asserts is GONE. So a faithful counterpart does NOT "
                      "resolve.",
        "rationale": "REJECT from `out = returnTypeEntry …`: on "
                     "(hasReturnAnno, ¬returnInArgs, annotation=`None`, omit) the "
                     "spec demands `none`, but dropping the omission branch "
                     "produces `some \"None\"`. Refuted at (true, false, \"None\", "
                     "true) — the omission sub-domain.",
        "witness": _TE +
                   'example : emitReturnTypeEntryTester true false "None".toList '
                   "true = false := by\n  decide\n",
    },
    {
        "id": "weak-entry-over-omit",
        "kind": "uniqueness",
        "expect": "reject",
        # Over-applies omission: drops the entry for ANY annotation when omission
        # is requested, not only for `None`. Correct on a `None` annotation,
        # wrong on a genuine (non-None) one.
        "module": _swap(
            _BASE, _ENTRY_IMPL,
            "    if hasReturnAnno && !returnInArgs then\n"
            "      if omitNoneReturnType then\n"
            "        return none\n"
            "      else\n"
            "        return (some returnAnnotation)\n"
            "    else\n"
            "      return none"),
        "refinement": "a counterpart that omitted the return-type entry for ANY "
                      "annotation of a class (not only `None`) would strip "
                      "legitimate return-type entries from documented objects that "
                      "carry a real annotation, regressing the passing suite that "
                      "pins those entries. So it does NOT resolve.",
        "rationale": "REJECT from `out = returnTypeEntry …`: on a genuine "
                     "(non-`None`) annotation with omission requested the spec "
                     "demands `some returnAnnotation`, but the rival returns "
                     "`none`. Refuted at (true, false, \"Xy\", true) — the "
                     "sub-domain where the annotation is NOT `None`, moving "
                     "returnAnnotation off `\"None\"`.",
        "witness": _TE +
                   'example : emitReturnTypeEntryTester true false "Xy".toList '
                   "true = false := by\n  decide\n",
    },
    {
        "id": "weak-entry-fixed-none-text",
        "kind": "uniqueness",
        "expect": "reject",
        # Right decision, wrong content: produces a fixed `"None"` text instead
        # of the object's OWN annotation. Attacks the VALUE the entry carries.
        "module": _swap(
            _BASE, _ENTRY_IMPL,
            "    if hasReturnAnno && !returnInArgs then\n"
            "      if (returnAnnotation == \"None\".toList) && omitNoneReturnType then\n"
            "        return none\n"
            "      else\n"
            "        return (some \"None\".toList)\n"
            "    else\n"
            "      return none"),
        "refinement": "a counterpart that produced a fixed `None` text instead of "
                      "the object's own annotation would render a documented "
                      "object returning a real type as if it returned `None`, "
                      "failing the tests that pin the rendered return-type text. "
                      "So it does NOT resolve.",
        "rationale": "REJECT from `out = returnTypeEntry …` on the VALUE the entry "
                     "carries: the spec pins `some returnAnnotation`, but the "
                     "rival pins `some \"None\"`; they diverge whenever the "
                     "annotation is not `None`. Refuted at (true, false, \"Xy\", "
                     "false) — omission off, so the entry IS produced and the "
                     "content is the observable.",
        "witness": _TE +
                   'example : emitReturnTypeEntryTester true false "Xy".toList '
                   "false = false := by\n  decide\n",
    },
    {
        "id": "weak-entry-ignore-already-declared",
        "kind": "uniqueness",
        "expect": "reject",
        # Ignores the returnInArgs guard: produces the entry even when the
        # description ALREADY declares a return type, duplicating it. Built to
        # move the returnInArgs binder off `false`.
        "module": _swap(
            _BASE, _ENTRY_IMPL,
            "    if hasReturnAnno then\n"
            "      if (returnAnnotation == \"None\".toList) && omitNoneReturnType then\n"
            "        return none\n"
            "      else\n"
            "        return (some returnAnnotation)\n"
            "    else\n"
            "      return none"),
        "refinement": "a counterpart that ignored whether the description already "
                      "declares a return type would append a SECOND, duplicate "
                      "return-type entry whenever one was already parsed, so the "
                      "tests that observe a single return-type entry would see two "
                      "and fail. So it does NOT resolve.",
        "rationale": "REJECT from `out = returnTypeEntry …`: when the return type "
                     "is already declared (`returnInArgs = true`) the spec demands "
                     "`none`, but dropping the `!returnInArgs` guard produces "
                     "`some returnAnnotation`. Refuted at (true, true, \"Xy\", "
                     "false) — the only entry witness that moves returnInArgs off "
                     "`false`.",
        "witness": _TE +
                   'example : emitReturnTypeEntryTester true true "Xy".toList '
                   "false = false := by\n  decide\n",
    },
    {
        "id": "weak-entry-ignore-annotation-present",
        "kind": "uniqueness",
        "expect": "reject",
        # Ignores the hasReturnAnno guard: produces the entry even when the
        # object carries NO return annotation. Built to move the hasReturnAnno
        # binder off `true`.
        "module": _swap(
            _BASE, _ENTRY_IMPL,
            "    if !returnInArgs then\n"
            "      if (returnAnnotation == \"None\".toList) && omitNoneReturnType then\n"
            "        return none\n"
            "      else\n"
            "        return (some returnAnnotation)\n"
            "    else\n"
            "      return none"),
        "refinement": "a counterpart that produced a return-type entry even for an "
                      "object with NO return annotation would fabricate return "
                      "types for undocumented-return objects, so the tests that "
                      "observe no return-type entry in that case would fail. So it "
                      "does NOT resolve.",
        "rationale": "REJECT from `out = returnTypeEntry …`: with no annotation "
                     "present (`hasReturnAnno = false`) the spec demands `none`, "
                     "but dropping the `hasReturnAnno` guard produces "
                     "`some returnAnnotation`. Refuted at (false, false, \"Xy\", "
                     "false) — the only entry witness that moves hasReturnAnno off "
                     "`true`.",
        "witness": _TE +
                   'example : emitReturnTypeEntryTester false false "Xy".toList '
                   "false = false := by\n  decide\n",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals against emitReturnTypeForKind (the
    # kind-aware dispatcher). Same witness mechanics; each attacks a specific
    # clause and moves a distinct binder.
    # =====================================================================
    {
        "id": "weak-kind-never-omit",
        "kind": "uniqueness",
        "expect": "reject",
        # THE pre-image dispatcher: the kind is ignored, EVERY kind is handled
        # with omission OFF. Attacks the class-omission clause (2).
        "module": _swap(
            _BASE, _KIND_IMPL,
            "    let r ← emitReturnTypeEntry hasReturnAnno returnInArgs "
            "returnAnnotation false\n"
            "    return r"),
        "refinement": "this is the pre-image dispatcher exactly: no kind is "
                      "singled out, so a class whose annotation is `None` keeps "
                      "the spurious `None` return-type entry the failing test "
                      "asserts is removed. So a faithful counterpart does NOT "
                      "resolve.",
        "rationale": "REJECT from clause (2) (and clause (1)): for a class kind "
                     "with a `None` annotation the spec demands `out = none`, but "
                     "delegating with omission OFF on every kind produces "
                     "`some \"None\"`. Refuted at (class, true, false, \"None\") — "
                     "the class-omission sub-domain.",
        "witness": _TK +
                   'example : emitReturnTypeForKindTester "class".toList true '
                   'false "None".toList = false := by\n  decide\n',
    },
    {
        "id": "weak-kind-nonclass-omit",
        "kind": "uniqueness",
        "expect": "reject",
        # Applies omission to a NON-class kind (delegates with omission ON
        # everywhere). Correct on a class, wrong on any other kind carrying a
        # `None` annotation. Attacks the completeness clause (3).
        "module": _swap(
            _BASE, _KIND_IMPL,
            "    let r ← emitReturnTypeEntry hasReturnAnno returnInArgs "
            "returnAnnotation true\n"
            "    return r"),
        "refinement": "a counterpart that applied the `None`-omission policy to "
                      "EVERY kind would strip the legitimate `None` return-type "
                      "entry from a documented function/method that genuinely "
                      "returns `None`, regressing the passing suite that keeps it. "
                      "So it does NOT resolve.",
        "rationale": "REJECT from clause (3) (and clause (1)): a non-class object "
                     "with an as-yet-undeclared annotation must produce "
                     "`some returnAnnotation`, but omitting on every kind drops a "
                     "`None` annotation to `none`. Refuted at (function, true, "
                     "false, \"None\") — the non-class sub-domain, moving the kind "
                     "binder off the class label.",
        "witness": _TK +
                   'example : emitReturnTypeForKindTester "function".toList true '
                   'false "None".toList = false := by\n  decide\n',
    },
    {
        "id": "weak-kind-always-emit",
        "kind": "uniqueness",
        "expect": "reject",
        # Bypasses the delegate entirely and always produces the annotation
        # entry — even with no annotation present. Attacks clause (1) and moves
        # the hasReturnAnno binder off `true`.
        "module": _swap(
            _BASE, _KIND_IMPL,
            "    return (some returnAnnotation)"),
        "refinement": "a counterpart that always produced a return-type entry, "
                      "regardless of whether the object even carries a return "
                      "annotation, would fabricate return types for objects that "
                      "have none, failing every test that observes their absence. "
                      "So it does NOT resolve.",
        "rationale": "REJECT from clause (1) (`out = returnTypeEntryForKind …`): "
                     "with no annotation present the spec demands `none`, but the "
                     "rival always returns `some returnAnnotation`. Refuted at "
                     "(function, false, false, \"Xy\") — moving hasReturnAnno off "
                     "`true` on the dispatcher.",
        "witness": _TK +
                   'example : emitReturnTypeForKindTester "function".toList false '
                   'false "Xy".toList = false := by\n  decide\n',
    },
    {
        "id": "weak-kind-ignore-already-declared",
        "kind": "uniqueness",
        "expect": "reject",
        # Passes a constant `false` for the already-declared guard to the
        # delegate, so an already-declared return type is duplicated. Attacks
        # clause (1) and moves the returnInArgs binder off `false`.
        "module": _swap(
            _BASE, _KIND_IMPL,
            "    let r ← emitReturnTypeEntry hasReturnAnno false "
            "returnAnnotation (isClassKind kind)\n"
            "    return r"),
        "refinement": "a counterpart that ignored whether a return type was "
                      "already declared would append a duplicate return-type entry "
                      "for a documented object that already has one, so the tests "
                      "observing a single entry would see two and fail. So it does "
                      "NOT resolve.",
        "rationale": "REJECT from clause (1): when the return type is already "
                     "declared (`returnInArgs = true`) the spec demands `none`, "
                     "but forcing the delegate's guard to `false` produces "
                     "`some returnAnnotation`. Refuted at (function, true, true, "
                     "\"Xy\") — the only dispatcher witness that moves returnInArgs "
                     "off `false`.",
        "witness": _TK +
                   'example : emitReturnTypeForKindTester "function".toList true '
                   'true "Xy".toList = false := by\n  decide\n',
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The nagini sibling has 6 SPEC cases (1 soundness
# positive, 1 admissibility, 4 uniqueness rivals — two of them frame-mutation).
# This bundle models the SAME changed behaviour, but the Lean-family model
# separates it into TWO contracted methods: the entry builder
# (`emitReturnTypeEntry`, = nagini's append_return_type entry logic) and the
# kind-aware dispatcher (`emitReturnTypeForKind`, = nagini's suppress_for_kind /
# merge dispatch). So the entry-builder rivals port near one-for-one, and the
# dispatcher gets its own defence + attack lane (which nagini's model split into
# a separate helper `suppress_for_kind`).
#
#   nagini case                         -> here
#   ---------------------------------------------------------------------
#   pos-control-reorder-guard           -> pos-commute-omission-guard
#                                          + pos-hoist-omission-flag       PORTED
#   admissibility-f2p-shape             -> admiss-kind-policy-nondegenerate RE-AIMED
#   frame-mutation-return-annotation    -> (none)                          VACUOUS
#   frame-mutation-fields-helper        -> (none)                          VACUOUS
#   partial-domain-no-suppression       -> weak-entry-drop-omission        PORTED
#   partial-domain-over-suppress        -> weak-entry-over-omit            PORTED
#   content-wrong-fixed-none            -> weak-entry-fixed-none-text      PORTED
#   control-flow-effect (§7, N/A)       -> (none)                          N/A
#   AXIOM_TESTS (empty)                 -> (none)                          N/A
#
# PORTED (positives): the nagini sibling ships ONE structurally-different correct
#   impl (reorder the short-circuit `and` operands). It is carried by TWO honest
#   reshape positives, one per obligation: pos-commute-omission-guard (commute the
#   omission guard's `&&`, the direct analogue) on the entry builder, and
#   pos-hoist-omission-flag (hoist the per-kind flag and delegate once) on the
#   dispatcher. Both are correct on every input and both verify with the frozen
#   `loom_solve`, so the structural-difference intent is preserved AND both
#   obligations get a dedicated soundness positive.
# RE-AIMED (admissibility): the nagini case witnesses that the fractional
#   precondition admits a normal F2P-shaped input. Neither method here has a
#   `require` clause, so that probe is vacuous. It is re-aimed at the residual
#   admissibility risk on a total domain — that the kind-aware decision is
#   unsatisfiable / degenerate at the discriminating point — via a live in-region
#   assert (class-`None` -> none AND non-class-`None` -> some).
# PORTED (entry rivals): weak-entry-drop-omission IS the pre-image entry builder
#   (Solution_prepatch_1) and the G-DIFF discriminator on the entry obligation;
#   weak-entry-over-omit drops the `None` guard (over-applies omission);
#   weak-entry-fixed-none-text is the nagini content-bug (fixed `None` text vs
#   the object's own annotation). Each refuted at the smallest decidable point.
# ADDED (5, binder/clause coverage). The nagini per-token functions do not have
#   the free kind / hasReturnAnno / returnInArgs structure these two methods
#   take, and a battery that never moves such an input says nothing about the
#   spec's dependence on it:
#     weak-entry-ignore-already-declared  — moves the returnInArgs binder off
#         `false` on the entry builder (drops the `!returnInArgs` guard).
#     weak-entry-ignore-annotation-present — moves the hasReturnAnno binder off
#         `true` on the entry builder (drops the `hasReturnAnno` guard).
#     weak-kind-never-omit    — the pre-image dispatcher (Solution_prepatch_2);
#         attacks class-omission clause (2) at (class, true, false, "None").
#     weak-kind-nonclass-omit — applies omission to a non-class kind; attacks
#         completeness clause (3) and moves the `kind` binder off the class label.
#     weak-kind-always-emit / weak-kind-ignore-already-declared — attack clause
#         (1) and move the hasReturnAnno / returnInArgs binders on the dispatcher.
# VACUOUS (frame-mutation x2): the nagini sibling rejects impls that WRITE a
#   read-only 1/2-permission input (return_annotation / fields). This backend is
#   referentially transparent and neither method declares a `mut` binder, so
#   there is no read-only input to overwrite and no substitute probe. Not
#   fabricated (per the porting map: this class is vacuous on Lean/Velvet).
# N/A (control-flow-effect): the nagini sibling documents this as inapplicable —
#   the only observable effect is the return value, which both methods already
#   pin. No separate capability channel exists here either.
#
# WITNESS DISCRIMINATION. The nine reject witnesses sit at nine DISTINCT input
#   points (five on emitReturnTypeEntry, four on emitReturnTypeForKind); none
#   shares a refutation point with another. Each elaborates against its loop-free
#   rival (whose extracted program reduces under `decide`) and FAILS against the
#   frozen solution (whose tester returns `true` at that point, so `= false` is
#   `decide`-refuted), so every rejection is attributed to the spec, not to a
#   tactic gap. Verified during authoring: rival build exit 0, gold build exit
#   != 0, for all nine.
#
# AXIOM_TESTS: dropped. The nagini bundle declares no axiom and no deep-model
#   reference (mapping.md §3; meta.json axioms == [], deep_model_references ==
#   []); the modeled decision is closed boolean/list logic over free inputs.
#   Nothing for the G-AX lane, which this gate ignores regardless.
AXIOM_TESTS = []
