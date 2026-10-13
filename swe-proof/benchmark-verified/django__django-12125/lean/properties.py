"""properties.py — G-PBT falsification battery for django__django-12125 (lean).

NOT a Lean file; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region — and, where the case legitimately re-proves, inside the
``-- proof-start`` / ``-- proof-end`` region — is changed, so
``markers.same_spec`` holds and the ``theorem correct_serializeType`` STATEMENT
stays byte-identical). ``expect="verify"`` passes iff (in scope AND the file
elaborates with the obligation closed); ``expect="reject"`` passes iff (in scope
AND it does NOT verify AND the case's refutation ``witness`` holds of the rival
while FAILING on the frozen solution).

DEFENDED SURFACE (one modeled function, one obligation):

  serializeType (v) : Option (reference, imports)
    result = (special/base value  => a fixed constant literal, no import;
              null value           => a fixed constant literal, no import;
              value with a home module in the built-in namespace
                                   => its unqualified leaf name, no import;
              value with any other home module
                                   => the home module joined by a dot to the
                                      value's FULLY-QUALIFIED in-scope path,
                                      plus the single import of that module;
              value with no observable home module => no result)

  The load-bearing clause: in the general (non-built-in, has-module) arm the
  reference is keyed by the FULLY-QUALIFIED path (which threads through every
  enclosing scope), NOT the unqualified leaf name. The two coincide for a value
  declared at top level and DIFFER for a value nested inside another — that
  difference is exactly what the fix turns on. Every code point of the result is
  grounded in the fields of ``v`` and fixed character constants; there is no
  opaque answer key to echo.

ADVERSARIAL READ of the nagini case classes on this carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS. Lean is referentially transparent:
    ``v`` is passed by value, there is no read-only heap half-permission to
    overwrite and no aliasing to exploit. The nagini sibling made this class
    MANDATORY (all three text inputs were half-permission ``Acc(...,1/2)`` and it
    carried a frame-mutation rival that wrote to the read-only qualified-name
    input). That rival has no expressible instance here; no substitute is
    fabricated for it. DEMONSTRATED, not asserted: the closest expressible
    analogue — shadow ``v`` with a copy whose name fields are overwritten, then
    compute the result from the ORIGINAL fields — VERIFIES against the frozen
    spec, because the rebinding cannot be observed by the caller. So the class
    is genuinely vacuous rather than merely hard: the carrier has no
    permission the rival could lose, and a rival written for this class would
    be a positive control, not a refutation.

  * UNGROUNDED-ORACLE ECHO — VACUOUS. The postcondition is an equality against a
    term built ONLY from the fields of ``v`` and fixed character/string
    constants (a fully-unfolded computation, not an opaque oracle). The bundle
    declares no ``opaque``/``axiom`` callee — the whole assembly is modeled
    deeply — so there is nothing an implementation could echo without doing the
    work. The nagini sibling reached the same conclusion (its ``dotted_path`` /
    ``import_line`` were grounded @Pure helpers, not consumed axioms) and its
    empty ``AXIOM_TESTS`` lane is out of scope for G-PBT (that lane belongs to
    G-AX). In place of an echo attack the battery carries honest positive
    controls.

  * DIVERGENCE / NON-TERMINATION — VACUOUS on lean. ``implementation_*`` is a
    total Lean ``def``; a diverging implementation cannot be written at all, so
    there is no ``diverge-*`` rival to port (the nagini sibling carries none).

  * PARTIAL-DOMAIN / VALUE — the real attacks. The postcondition rejects any
    rival that renders even one arm wrongly on any point of the domain.

CASE-COUNT vs NAGINI. The nagini sibling contracted a single function with a
built-in vs non-built-in split over three read-only text inputs plus a mandatory
frame lane; this carrier models the SAME function but exposes the full branch
ladder the real code walks (two constant special cases, the built-in-namespace
arm, the general qualified arm, and the no-module ``none`` arm) as fields of one
descriptor ``v``. So: the nagini frame-mutation rival is DROPPED (vacuous — see
above); the nagini axiom-soundness lane is DROPPED (out of G-PBT scope); the
four nagini value/partial-domain rivals port directly (leaf-name pre-patch bug,
drop-the-dot, drop-the-import, always-qualified/built-in corruption); and four
further rivals attack the arms this carrier models that nagini's built-in flag
collapsed (the two constant special cases, the no-module ``none`` arm, and the
ORDER in which the two special cases are tried), so every arm of the
postcondition ladder — and the priority between the two leading arms — is
attacked by some rival. Two soundness
positives (a branch/condition reshape and a match-collapsed reassociated
reshape) and one admissibility positive (the frozen obligation discharged at a
ground F2P-shaped nested-value input) port from the nagini positive /
admissibility controls.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen ``simp only [Id.run, bind, pure]``
script is tuned to the frozen form — so a rejection alone attributes nothing to
the spec. Every ``expect="reject"`` case therefore carries a Lean snippet stating
the spec predicate at one concrete, ``decide``-able input; each was checked to
ELABORATE against its rival (the rival provably contradicts the spec there) and
to FAIL against the frozen solution (so it discriminates rather than asserting a
tautology). The single spec binder ``v`` is moved across every arm of the ladder:
each witness sets a DIFFERENT combination of the descriptor's flags and names, so
no arm and no field is pinned to one value across the battery.
"""
from pathlib import Path

INSTANCE = "django__django-12125"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique ({src.count(old)}x): {old!r}")
    return src.replace(old, new, 1)


# ---- region anchors (each the FULL body of a region, unique in Solution.lean;
# every replacement lands entirely inside the region it edits, so `same_spec`
# holds and the theorem STATEMENT is untouched). ----

# The whole `implementation_serializeType` def (impl region body).
_IMPL = (
    "def implementation_serializeType (v : TypeRef) :\n"
    "    Option (String × List String) := Id.run do\n"
    "  -- The constant special cases, checked in order before anything else.\n"
    "  if v.isModelBase then\n"
    "    return some (\"models.Model\", [])\n"
    "  if v.isNoneType then\n"
    "    return some (\"type(None)\", [])\n"
    "  -- A class with an observable home module.\n"
    "  if v.hasModule then\n"
    "    if v.module = builtinsModule then\n"
    "      -- Built-in namespace: the leaf name alone, no import.\n"
    "      return some (v.shortName, [])\n"
    "    else\n"
    "      -- Any other module: home module joined to the class's fully-qualified\n"
    "      -- in-module path, plus the import of that home module.\n"
    "      return some (v.module ++ \".\" ++ v.fullName, [\"import \" ++ v.module])\n"
    "  return none"
)

# The proof body (proof region tactic block).
_PROOF = (
    "  intro v\n"
    "  unfold problem_spec_serializeType implementation_serializeType\n"
    "  simp only [Id.run, bind, pure]"
)

assert _BASE.count(_IMPL) == 1, "impl-serializeType drifted"
assert _BASE.count(_PROOF) == 1, "proof-serializeType drifted"


# --- reusable witness maker -------------------------------------------------
def _witness(inp):
    return (
        f"example : ¬ problem_spec_serializeType\n"
        f"    {inp}\n"
        f"    (implementation_serializeType\n"
        f"      {inp}) := by\n"
        f"  unfold problem_spec_serializeType implementation_serializeType\n"
        f"  decide\n"
    )


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness / admissibility) — structurally different
    # but CORRECT implementations that MUST verify. If a faithful correct
    # implementation cannot satisfy the frozen obligation the spec is
    # SPEC-TOO-STRONG. Each keeps the theorem STATEMENT byte-identical and
    # introduces no helper lemma, axiom, or assumption token.
    # =====================================================================
    {
        "id": "pos-branch-condition-reshape",
        "kind": "soundness",
        "expect": "verify",
        # The general (has-module) arm is reshaped: the built-in test is inverted
        # (`≠ builtinsModule` tried first) with the arms swapped, and the
        # reference string is bound to a local before being returned. Every arm
        # computes the SAME value as the frozen body, so the postcondition holds
        # pointwise. The proof discharges the reshaped `if` ladder with the
        # frozen unfold + `simp`.
        "module": _swap(
            _swap(
                _BASE,
                _IMPL,
                "def implementation_serializeType (v : TypeRef) :\n"
                "    Option (String × List String) := Id.run do\n"
                "  if v.isModelBase then\n"
                "    return some (\"models.Model\", [])\n"
                "  if v.isNoneType then\n"
                "    return some (\"type(None)\", [])\n"
                "  if v.hasModule then\n"
                "    if v.module ≠ builtinsModule then\n"
                "      let ref := v.module ++ \".\" ++ v.fullName\n"
                "      return some (ref, [\"import \" ++ v.module])\n"
                "    else\n"
                "      return some (v.shortName, [])\n"
                "  return none",
            ),
            _PROOF,
            "  intro v\n"
            "  unfold problem_spec_serializeType implementation_serializeType\n"
            "  simp [Id.run, bind, pure]",
        ),
        "rationale": "A correct reshape: the built-in test is inverted "
                     "(`v.module ≠ builtinsModule` first, arms swapped) and the "
                     "general-arm reference is bound to a local. Every arm returns "
                     "the same value as the frozen body, so it equals the spec RHS "
                     "pointwise on every descriptor. If it cannot verify the "
                     "postcondition is SPEC-TOO-STRONG. Proof: the frozen unfold, "
                     "then `simp` on the reshaped `if` ladder.",
    },
    {
        "id": "pos-match-collapse-reassoc",
        "kind": "soundness",
        "expect": "verify",
        # The two constant special cases are collapsed into one `match` on the
        # pair of flags, and the general-arm reference is REASSOCIATED as
        # `module ++ ("." ++ fullName)` with the dot bound to a local. Same value
        # by associativity of string append; proof closes via `String.append_assoc`.
        "module": _swap(
            _swap(
                _BASE,
                _IMPL,
                "def implementation_serializeType (v : TypeRef) :\n"
                "    Option (String × List String) := Id.run do\n"
                "  match v.isModelBase, v.isNoneType with\n"
                "  | true, _ => return some (\"models.Model\", [])\n"
                "  | false, true => return some (\"type(None)\", [])\n"
                "  | false, false =>\n"
                "    if v.hasModule then\n"
                "      if v.module = builtinsModule then\n"
                "        return some (v.shortName, [])\n"
                "      else\n"
                "        let dot := \".\"\n"
                "        return some (v.module ++ (dot ++ v.fullName), [\"import \" ++ v.module])\n"
                "    else\n"
                "      return none",
            ),
            _PROOF,
            "  intro v\n"
            "  unfold problem_spec_serializeType implementation_serializeType\n"
            "  simp only [Id.run, pure]\n"
            "  cases v.isModelBase <;> cases v.isNoneType <;> simp [String.append_assoc]",
        ),
        "rationale": "A correct reshape: the two constant special cases are "
                     "collapsed into a single `match` on the flag pair and the "
                     "general-arm reference is reassociated as "
                     "`module ++ (\".\" ++ fullName)`. Equal to the frozen body by "
                     "associativity of `++`, so the postcondition holds pointwise. "
                     "If it cannot verify the spec is SPEC-TOO-STRONG. Proof: unfold, "
                     "case-split the two flags, close with `String.append_assoc`.",
    },
    {
        "id": "admiss-f2p-nested-value",
        "kind": "admissibility",
        "expect": "verify",
        # The frozen obligation is unconditional (no precondition binder); the
        # honest analogue of the nagini precondition-admission probe is to
        # discharge the spec at a ground, F2P-shaped nested-value input (a value
        # whose fully-qualified path threads through an enclosing scope, so it is
        # strictly longer than the leaf name — the exact discriminating regime the
        # issue is about) by evaluation, then close the frozen obligation verbatim.
        "module": _swap(
            _BASE,
            _PROOF,
            "  have _ground : problem_spec_serializeType\n"
            "      { isModelBase := false, isNoneType := false, hasModule := true,\n"
            "        module := \"migrations.test_writer\", shortName := \"NestedEnum\",\n"
            "        fullName := \"WriterTests.NestedEnum\" }\n"
            "      (implementation_serializeType\n"
            "        { isModelBase := false, isNoneType := false, hasModule := true,\n"
            "          module := \"migrations.test_writer\", shortName := \"NestedEnum\",\n"
            "          fullName := \"WriterTests.NestedEnum\" }) := by\n"
            "    unfold problem_spec_serializeType implementation_serializeType\n"
            "    decide\n" + _PROOF,
        ),
        "rationale": "The obligation is discharged at a ground F2P-shaped input — a "
                     "value with an observable non-built-in home module whose "
                     "fully-qualified path is strictly longer than its leaf name "
                     "(the nested-value regime the issue reports) — by `decide`, "
                     "then the frozen obligation is closed verbatim. Verifies (else "
                     "the spec is unsatisfiable at a normal input, the analogue of "
                     "PRECOND-TOO-STRONG). Nothing is assumed: no new declaration, "
                     "the theorem statement is byte-identical, the ground instance "
                     "is a `have` inside the existing tactic body.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong implementations sharing the
    # frozen spec that MUST be rejected. Each carries (a) the refinement
    # argument that its faithful real patch would NOT resolve the F2P, so a
    # verifying rival would be a true verify-does-not-imply-resolve break rather
    # than an artifact, and (b) a refutation witness pinning the violation at one
    # concrete input, checked to elaborate against the rival and fail on the
    # frozen solution.
    # =====================================================================
    {
        "id": "weak-leaf-name-prepatch-bug",
        "kind": "uniqueness",
        "expect": "reject",
        # THE bug: the general arm is keyed by the UNQUALIFIED leaf name instead
        # of the fully-qualified path. Correct on top-level values (where the two
        # coincide), WRONG on a nested value.
        "module": _swap(
            _BASE,
            _IMPL,
            "def implementation_serializeType (v : TypeRef) :\n"
            "    Option (String × List String) := Id.run do\n"
            "  if v.isModelBase then\n"
            "    return some (\"models.Model\", [])\n"
            "  if v.isNoneType then\n"
            "    return some (\"type(None)\", [])\n"
            "  if v.hasModule then\n"
            "    if v.module = builtinsModule then\n"
            "      return some (v.shortName, [])\n"
            "    else\n"
            "      return some (v.module ++ \".\" ++ v.shortName, [\"import \" ++ v.module])\n"
            "  return none",
        ),
        "refinement": "This is the pre-patch behavior: keying the general-arm "
                      "reference on the unqualified leaf name. On the F2P's nested "
                      "value (leaf name strictly shorter than the fully-qualified "
                      "path) it renders a reference that omits the enclosing scope, "
                      "which names a sibling top-level value that does not exist. "
                      "The F2P asserts the reference threads through the enclosing "
                      "scope, so it would NOT resolve.",
        "rationale": "REJECT from the general-arm clause: the reference must be "
                     "`module ++ \".\" ++ fullName`, but the rival substitutes "
                     "`shortName`. Since `fullName` and `shortName` are independent "
                     "fields that differ for a nested value, if this verifies the "
                     "spec is SPEC-TOO-WEAK. Refuted at a nested-value input "
                     "(`fullName = \"WriterTests.Inner\" ≠ shortName = \"Inner\"`).",
        "witness": _witness(
            '{ isModelBase := false, isNoneType := false, hasModule := true, '
            'module := "app.models", shortName := "Inner", '
            'fullName := "WriterTests.Inner" }'
        ),
    },
    {
        "id": "weak-drop-dot-separator",
        "kind": "uniqueness",
        "expect": "reject",
        # Omit the '.' between module and the qualified path.
        "module": _swap(
            _BASE,
            _IMPL,
            "def implementation_serializeType (v : TypeRef) :\n"
            "    Option (String × List String) := Id.run do\n"
            "  if v.isModelBase then\n"
            "    return some (\"models.Model\", [])\n"
            "  if v.isNoneType then\n"
            "    return some (\"type(None)\", [])\n"
            "  if v.hasModule then\n"
            "    if v.module = builtinsModule then\n"
            "      return some (v.shortName, [])\n"
            "    else\n"
            "      return some (v.module ++ v.fullName, [\"import \" ++ v.module])\n"
            "  return none",
        ),
        "refinement": "Fusing the module and the qualified path with no dot yields "
                      "a token that is not a valid dotted reference (`mig.testOuter"
                      ".Nested` rather than `mig.test.Outer.Nested`); the F2P "
                      "asserts the exact dotted reference, so it would NOT resolve.",
        "rationale": "REJECT from the general-arm clause: the reference must be "
                     "`module ++ \".\" ++ fullName`, but the rival drops the dot "
                     "literal. If it verifies the spec is SPEC-TOO-WEAK. Refuted at "
                     "a distinct non-built-in nested-value input.",
        "witness": _witness(
            '{ isModelBase := false, isNoneType := false, hasModule := true, '
            'module := "mig.test", shortName := "Nested", '
            'fullName := "Outer.Nested" }'
        ),
    },
    {
        "id": "weak-drop-import",
        "kind": "uniqueness",
        "expect": "reject",
        # Correct reference, but an EMPTY import list on the general arm.
        "module": _swap(
            _BASE,
            _IMPL,
            "def implementation_serializeType (v : TypeRef) :\n"
            "    Option (String × List String) := Id.run do\n"
            "  if v.isModelBase then\n"
            "    return some (\"models.Model\", [])\n"
            "  if v.isNoneType then\n"
            "    return some (\"type(None)\", [])\n"
            "  if v.hasModule then\n"
            "    if v.module = builtinsModule then\n"
            "      return some (v.shortName, [])\n"
            "    else\n"
            "      return some (v.module ++ \".\" ++ v.fullName, [])\n"
            "  return none",
        ),
        "refinement": "Emitting no import for a value with a non-built-in home "
                      "module produces regenerated source that references an "
                      "unimported module; the F2P demands the single import of the "
                      "home module, so it would NOT resolve. This rival passes the "
                      "reference clause but fails the import clause.",
        "rationale": "REJECT from the general-arm import clause: the import must be "
                     "`[\"import \" ++ module]`, but the rival returns `[]`. If it "
                     "verifies the spec is SPEC-TOO-WEAK — the import component "
                     "would be unconstrained. Refuted at a distinct non-built-in "
                     "nested-value input.",
        "witness": _witness(
            '{ isModelBase := false, isNoneType := false, hasModule := true, '
            'module := "pkg.mod", shortName := "Leaf", '
            'fullName := "Encl.Leaf" }'
        ),
    },
    {
        "id": "weak-builtin-always-qualified",
        "kind": "uniqueness",
        "expect": "reject",
        # Corrupts the built-in-namespace arm: renders the qualified dotted path +
        # import even when the home module IS the built-in namespace. Correct on
        # the non-built-in domain, WRONG for a built-in value.
        "module": _swap(
            _BASE,
            _IMPL,
            "def implementation_serializeType (v : TypeRef) :\n"
            "    Option (String × List String) := Id.run do\n"
            "  if v.isModelBase then\n"
            "    return some (\"models.Model\", [])\n"
            "  if v.isNoneType then\n"
            "    return some (\"type(None)\", [])\n"
            "  if v.hasModule then\n"
            "    return some (v.module ++ \".\" ++ v.fullName, [\"import \" ++ v.module])\n"
            "  return none",
        ),
        "refinement": "Rendering the qualified dotted path + import even for a "
                      "built-in value makes a built-in type serialize as "
                      "`builtins.<name>` with `import builtins`; the PASS-side tests "
                      "expect the bare leaf name with NO import there, so those "
                      "tests would fail; it would NOT resolve.",
        "rationale": "REJECT from the built-in-namespace clause: when the home "
                     "module is the built-in namespace the result must be the leaf "
                     "name with no import, but the rival always renders the "
                     "qualified path + import. If it verifies the spec is "
                     "SPEC-TOO-WEAK. Refuted at a built-in-module input "
                     "(`module = builtins`).",
        "witness": _witness(
            '{ isModelBase := false, isNoneType := false, hasModule := true, '
            'module := "builtins", shortName := "int", fullName := "int" }'
        ),
    },
    {
        "id": "weak-no-module-nonempty",
        "kind": "uniqueness",
        "expect": "reject",
        # Corrupts the no-module arm: returns a (spurious) `some` result for a
        # value with no observable home module, where the spec demands `none`.
        "module": _swap(
            _BASE,
            _IMPL,
            "def implementation_serializeType (v : TypeRef) :\n"
            "    Option (String × List String) := Id.run do\n"
            "  if v.isModelBase then\n"
            "    return some (\"models.Model\", [])\n"
            "  if v.isNoneType then\n"
            "    return some (\"type(None)\", [])\n"
            "  if v.hasModule then\n"
            "    if v.module = builtinsModule then\n"
            "      return some (v.shortName, [])\n"
            "    else\n"
            "      return some (v.module ++ \".\" ++ v.fullName, [\"import \" ++ v.module])\n"
            "  return some (\"\", [])",
        ),
        "refinement": "A value with no observable home module cannot be serialized "
                      "to any reference; the real code falls off the end and "
                      "produces no result. Fabricating a `some` there would emit a "
                      "reference for an unserializable value instead of the expected "
                      "failure, so it would NOT resolve.",
        "rationale": "REJECT from the no-module arm: the result must be `none` when "
                     "the value has no observable home module, but the rival returns "
                     "`some`. If it verifies the spec is SPEC-TOO-WEAK — the "
                     "no-result arm would be unconstrained. Refuted at a "
                     "`hasModule = false` input.",
        "witness": _witness(
            '{ isModelBase := false, isNoneType := false, hasModule := false, '
            'module := "local", shortName := "f", fullName := "g.f" }'
        ),
    },
    {
        "id": "weak-model-base-wrong-constant",
        "kind": "uniqueness",
        "expect": "reject",
        # Corrupts the first special case: the base-model value renders the WRONG
        # constant literal (the null-type literal).
        "module": _swap(
            _BASE,
            _IMPL,
            "def implementation_serializeType (v : TypeRef) :\n"
            "    Option (String × List String) := Id.run do\n"
            "  if v.isModelBase then\n"
            "    return some (\"type(None)\", [])\n"
            "  if v.isNoneType then\n"
            "    return some (\"type(None)\", [])\n"
            "  if v.hasModule then\n"
            "    if v.module = builtinsModule then\n"
            "      return some (v.shortName, [])\n"
            "    else\n"
            "      return some (v.module ++ \".\" ++ v.fullName, [\"import \" ++ v.module])\n"
            "  return none",
        ),
        "refinement": "The base-model value has a fixed reference literal that is "
                      "not the null-type literal; emitting the wrong constant there "
                      "produces regenerated source that names the wrong type, so it "
                      "would NOT resolve.",
        "rationale": "REJECT from the first special-case clause: the base-model "
                     "value must render its own fixed literal, but the rival emits "
                     "the null-type literal. If it verifies the spec is "
                     "SPEC-TOO-WEAK. Refuted at an `isModelBase = true` input.",
        "witness": _witness(
            '{ isModelBase := true, isNoneType := false, hasModule := true, '
            'module := "m", shortName := "S", fullName := "S" }'
        ),
    },
    {
        "id": "weak-none-type-wrong-constant",
        "kind": "uniqueness",
        "expect": "reject",
        # Corrupts the second special case: the null value renders the WRONG
        # constant literal (the base-model literal).
        "module": _swap(
            _BASE,
            _IMPL,
            "def implementation_serializeType (v : TypeRef) :\n"
            "    Option (String × List String) := Id.run do\n"
            "  if v.isModelBase then\n"
            "    return some (\"models.Model\", [])\n"
            "  if v.isNoneType then\n"
            "    return some (\"models.Model\", [])\n"
            "  if v.hasModule then\n"
            "    if v.module = builtinsModule then\n"
            "      return some (v.shortName, [])\n"
            "    else\n"
            "      return some (v.module ++ \".\" ++ v.fullName, [\"import \" ++ v.module])\n"
            "  return none",
        ),
        "refinement": "The null value has a fixed reference literal that is not the "
                      "base-model literal; emitting the wrong constant there names "
                      "the wrong type in regenerated source, so it would NOT "
                      "resolve.",
        "rationale": "REJECT from the second special-case clause: the null value "
                     "must render its own fixed literal, but the rival emits the "
                     "base-model literal. If it verifies the spec is SPEC-TOO-WEAK. "
                     "Refuted at an `isNoneType = true` (and `isModelBase = false`) "
                     "input.",
        "witness": _witness(
            '{ isModelBase := false, isNoneType := true, hasModule := true, '
            'module := "m", shortName := "S", fullName := "S" }'
        ),
    },
    {
        "id": "weak-special-case-order-swapped",
        "kind": "uniqueness",
        "expect": "reject",
        # Corrupts the ORDER of the two constant special cases: the null test is
        # tried FIRST. Observationally identical to the frozen impl on every
        # descriptor that sets at most one of the two flags — the whole rest of
        # the domain — and WRONG only at the single point where BOTH flags hold,
        # where the spec's `if isModelBase then _ else if isNoneType then _`
        # ladder pins the base-model literal. The other two special-case rivals
        # corrupt a literal WITHIN an arm and so are refuted at a one-flag point;
        # neither reaches the priority point, so this clause of the ladder was
        # otherwise unattacked.
        "module": _swap(
            _BASE,
            _IMPL,
            "def implementation_serializeType (v : TypeRef) :\n"
            "    Option (String × List String) := Id.run do\n"
            "  if v.isNoneType then\n"
            "    return some (\"type(None)\", [])\n"
            "  if v.isModelBase then\n"
            "    return some (\"models.Model\", [])\n"
            "  if v.hasModule then\n"
            "    if v.module = builtinsModule then\n"
            "      return some (v.shortName, [])\n"
            "    else\n"
            "      return some (v.module ++ \".\" ++ v.fullName, [\"import \" ++ v.module])\n"
            "  return none",
        ),
        "refinement": "The two constant special cases are tried in a FIXED order, "
                      "and the ordering is observable exactly for a value that "
                      "matches both: it must render the FIRST case's literal. A "
                      "faithful patch that tested them in the other order would "
                      "emit the second literal for such a value, naming the wrong "
                      "type in regenerated source, so it would NOT resolve. Every "
                      "other operation is the verbatim frozen body, so the "
                      "rejection is attributable solely to the swapped order.",
        "rationale": "REJECT from the ORDERING of the two special-case clauses: "
                     "the spec's ladder tries the base-model test before the null "
                     "test, so at a descriptor satisfying BOTH the result must be "
                     "the base-model literal; the rival returns the null literal "
                     "there. If it verifies the spec would leave the priority "
                     "between the two special cases unconstrained (SPEC-TOO-WEAK) "
                     "— a rival could then permute them freely. Refuted at the "
                     "both-flags-true point, which no other case in this battery "
                     "reaches: the two literal-corruption rivals are refuted at "
                     "`isModelBase = true, isNoneType = false` and at "
                     "`isModelBase = false, isNoneType = true` respectively.",
        "witness": _witness(
            '{ isModelBase := true, isNoneType := true, hasModule := true, '
            'module := "m", shortName := "S", fullName := "S" }'
        ),
    },
]

# AXIOM_TESTS: empty by construction. The bundle declares no `opaque`/`axiom`
# callee (the axioms region is empty); every operation is modeled deeply over the
# descriptor `v`, so there is no consumed axiom for a real callee to violate. The
# axiom lane is G-AX's job and is out of scope for this gate.
AXIOM_TESTS = []
