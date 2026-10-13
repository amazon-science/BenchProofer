"""properties.py — G-PBT falsification battery for django__django-14580 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed
— both regions the consumer spec view elides — so ``markers.same_spec`` holds
and the ``prove_correct renderTypeRef`` obligation survives with a
byte-identical statement) and swaps in a candidate implementation; it is checked
by the real verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness must ELABORATE against the rival and FAIL
against the frozen solution).

DEFENDED SURFACE (one contracted method over a pure type-dispatch classifier).
A runtime type is observed through a small record ``t : TypeInfo`` carrying only
the fields the rendering depends on — two identity flags (is the framework
base-model class; is the canonical none-valued type) and three name strings
(module name, qualified name, bare name). The operation renders the type as a
source reference paired with the import statements that reference requires:

  renderTypeRef (t : TypeInfo) return (out : String × List String)
    ensures out = typeRef t

``typeRef`` is a fully-unfolded ``def`` in the ``pure`` region — there is NO
opaque answer key to echo; pinning ``out = typeRef t`` IS the work. ``typeRef``
is a four-arm ordered ladder, and each arm is an INDEPENDENT sub-behaviour the
single ``ensures`` pins:

  (B1) base-model flag set  → reference is the literal base-model reference AND
       the imports are EXACTLY the one namespace import that makes that bare
       reference valid standalone source. This is the load-bearing fix: the
       import set is non-empty AND equal to the exact statement.
  (B2) none-type flag set   → reference is the built-in none expression AND the
       imports are EMPTY (a built-in expression needs no import).
  (B3) module name is the built-in namespace → reference is the bare name AND
       the imports are EMPTY.
  (B4) otherwise → reference is ``module.qualified_name`` AND the imports are
       exactly the single matching ``import module`` statement.

Every arm is attacked by a reject rival below, on BOTH components of the output
pair (the rendered string and the import set), and the reject witnesses vary
every field of the input record that any arm reads — the base-model flag, the
none-type flag, the built-in module name, a general module name, and a qualified
name distinct from the bare name — so no sub-behaviour is left pinned at one
point. The F2P test ``test_serialize_type_model`` asserts the base-model
reference serializes with EXACTLY the namespace import present (B1 is that
discriminator); the P2P ``test_serialize_type_none`` keeps the none row honest
with an empty import set (B2), and ``test_serialize_builtin_types`` /
``test_serialize_fields`` exercise B3/B4.

ADVERSARIAL READ of the nagini classes on THIS carrier:
  * FRAME / PERMISSION-MUTATION — VACUOUS here. The nagini sibling's
    ``READ-ONLY INPUT / FRAME-MUTATION`` note already records that there is NO
    read-only heap input to overwrite (the only parameter is a value, and its
    fractional-permission machinery is over loop LOCALS the impl constructs).
    Lean and Velvet are referentially transparent: the input is an immutable
    value, this bundle declares no ``mut`` parameter, there is no heap, no
    aliasing, and no mutable ``self``. So there is no read-only input to abuse
    and this whole class is structurally inapplicable. Not fabricated (per the
    porting map: vacuous on Lean/Velvet).
  * UNGROUNDED-ORACLE ECHO — N/A as a distinct class, exactly as the sibling
    records: ``typeRef`` is a concrete ``def`` in the ``pure`` region and the
    ``axioms`` region is empty, so there is no answer key to echo. The sibling's
    directive-2 substitute (the honest cheapest correct control) is carried here
    as the two soundness reshapes below (each does the real work of producing
    the right ``(string, imports)`` pair for its branch).
  * PARTIAL-DOMAIN / VALUE — the core attacks. Each rival is correct on part of
    the domain but diverges on one arm's sub-domain: drop / corrupt / truncate
    the base-model import, attach a spurious import to a no-import arm, or
    mis-render the module tail. The single whole-value equality is what rejects
    each divergence.
  * CONTROL-FLOW-EFFECT — N/A. ``renderTypeRef`` always returns the pair; there
    is no raise/side-effect path invisible to the value abstraction (the F2P
    observes exactly the returned (string, import-set) pair, which IS the value
    abstraction).

CARRIER NARROWING vs nagini. The nagini sibling models only the TWO
distinguished rows (base-model, none-type) as a two-row table scan; the velvet
carrier models the FULL four-arm classifier (base-model, none-type, builtins,
module-tail). So this port ATTACKS MORE surface than the sibling, not less: the
sibling's two-row rivals port to B1/B2 rivals, and the two arms the sibling does
not model (B3 builtins, B4 module-tail) get their own rivals with no nagini
counterpart. The sibling's ``weak-always-return-row0`` (a wrong-row TABLE scan)
has no *mechanism* counterpart — there is no runtime table to mis-index here,
the scan is unrolled into a static ``if/else`` ladder (mapping.md §2a) — but its
OBSERVABLE (an arm surfacing another arm's WHOLE output pair) is directly
expressible on the unrolled ladder and is carried literally by
``weak-none-returns-base-pair``, which returns the base-model arm's (reference,
imports) pair from the none-type arm. (An earlier revision of this manifest
claimed that observable had "no literal counterpart" and was only carried by
INTENT across the spurious-import and tail rivals; that claim was wrong — the
literal rival lands, with a discriminating witness, and is now present.)

WITNESS MECHANICS ON THIS BUNDLE. The frozen impl is a straight-line ``if/else``
ladder returning a pair, so its extracted program reduces under ``decide`` and a
reject rival written the same way does too. Each reject case is refuted by a
witness ``renderTypeRefTester t = false`` stated at a CONCRETE ``TypeInfo``
literal; it ELABORATES against the (reducible) rival and — because gold
satisfies the spec at every input — FAILS against the frozen solution under the
identical ``decide``. Both halves were checked out-of-band with
``scripts/lean_verify.sh`` (rival witness EXIT 0, gold witness EXIT 1) for every
reject case, and every rival's full variant was confirmed to FAIL verification
(EXIT 1) while both soundness reshapes and the admissibility variant VERIFY
(EXIT 0). No witness binds a hypothesis (every field is a concrete literal that
``decide`` reduces — the carrier is fully transparent), so there is no
carrier-conditioning and no consistency-probe obligation.

The gold-side failure is a SEMANTIC refutation, not a syntactic accident: on
every reject case the frozen-solution build fails with ``Tactic `decide` proved
that the proposition ... = false is false`` — the kernel EVALUATED the tester at
that literal input and got the opposite answer. It is not a stuck reduction
(``did not reduce to isTrue or isFalse``), not an unknown identifier, and not a
timeout, so each exit-1 carries real information about the spec. Independently
re-derived per case during audit.

The admissibility case's in-region ``assert`` was confirmed to carry a real VC
rather than being silently discharged: replacing its conjunction with a FALSE
claim about the same arm leaves the residual goal ``⊢ False`` and the build fails
(EXIT 1). So the assert's success is evidence about the post-image, not an
artifact of the assert being ignored.

AXIOM lane: EMPTY (``meta.json`` declares no ``axiom`` and no A-reference deep
model; the whole classifier is modeled DEEPLY as ``typeRef``, all I/R ops, not
axiomatized callees). There is no axiom-soundness / axiom-containment obligation
to probe here, and the gate ignores ``AXIOM_TESTS`` regardless. (The sibling's
``ax-ref-typeserializer-serialize-equals-real`` probe is a G-AX concern and is
dropped per the porting map; here G-AX is ``skip``.)
"""
from pathlib import Path

INSTANCE = "django__django-14580"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchors. Each lies wholly inside the single impl region and
# ---- is unique in Solution.lean (both facts asserted at load by _swap). The
# ---- four `return (...)` lines are the four arms of the classifier; the bare
# ---- `return (...)` prefix distinguishes them from the identical tuple
# ---- literals in the pure `typeRef` def (which have no `return`). ----
_RET_BASE = '      return ("models.Model", ["from django.db import models"])'
_RET_NONE = '        return ("type(None)", [])'
_RET_BUILTIN = "          return (t.simpleName, [])"
_RET_TAIL = (
    '          return (t.moduleName ++ "." ++ t.qualName, '
    '["import " ++ t.moduleName])')
_IMPL_START = "    -- impl-start\n"

# ---- proof-body anchor. The `prove_correct` TACTIC BODY is elided from the
# ---- consumer spec view (only the header/statement survives). None of the
# ---- variants below need to retune it — every soundness reshape closes under
# ---- the frozen script — so it is left byte-identical; asserted present so the
# ---- manifest breaks loudly if the frozen solution ever changes. ----
_PROOF = "prove_correct renderTypeRef by\n  loom_solve <;> simp_all [typeRef]"
assert _BASE.count(_PROOF) == 1, "prove_correct body drifted from expected text"


# ---- witness preamble. The spec is a `method` CONTRACT, not a bare predicate,
# ---- so a witness reaches the post-image through Velvet's own tester
# ---- machinery: `renderTypeRefTester t = false` says the extracted program's
# ---- result violates the postcondition at that concrete input. Checked in a
# ---- file whose `prove_correct` block is stripped, so no tactic script can
# ---- mask the verdict. The method has no `require` clause, so every input
# ---- reaches the postcondition rather than vacuously passing.
_TESTER = (
    "extract_program_for renderTypeRef\n"
    "prove_precondition_decidable_for renderTypeRef\n"
    "prove_postcondition_decidable_for renderTypeRef\n"
    "derive_tester_for renderTypeRef\n\n"
)


def _ti(base, none, module, qual, simple):
    return ("{ isBaseModelType := %s, isNoneType := %s, moduleName := %r, "
            "qualName := %r, simpleName := %r }"
            % ("true" if base else "false", "true" if none else "false",
               module, qual, simple)).replace("'", '"')


def _witness(ti):
    return _TESTER + f"example : renderTypeRefTester {ti} = false := by\n  decide\n"


# Concrete TypeInfo inputs, one per attacked arm (fields varied across witnesses
# so no field is pinned at a single value).
_IN_BASE = _ti(True, False, "m", "q", "s")          # base-model arm (B1)
_IN_NONE = _ti(False, True, "m", "q", "s")           # none-type arm (B2)
_IN_BUILTIN = _ti(False, False, "builtins", "int", "int")  # builtins arm (B3)
_IN_TAIL = _ti(False, False, "datetime", "date", "date")   # module-tail arm (B4)
_IN_TAIL_NESTED = _ti(False, False, "mymod", "Outer.Inner", "Inner")  # qual≠simple
# builtins arm at a NESTED name (qual≠simple) — separates the two name fields on
# arm B3, the way _IN_TAIL_NESTED does on arm B4. _IN_BUILTIN cannot: it has
# qualName == simpleName == "int", so a B3 rival that reads the wrong name field
# is invisible there.
_IN_BUILTIN_NESTED = _ti(False, False, "builtins", "Outer.Inner", "Inner")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify. If a faithful correct reshape cannot verify the spec is
    # SPEC-TOO-STRONG. There is no opaque oracle to echo (`typeRef` is a concrete
    # def), so each control does the real work of producing the arm's exact
    # (string, imports) pair — the sibling's directive-2 substitute for the
    # (N/A) ungrounded-echo class.
    # =====================================================================
    {
        "id": "pos-reshape-base-arm",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _BASE, _RET_BASE,
            '      let ref := "models.Model"\n'
            '      let imp := ["from django.db import models"]\n'
            "      return (ref, imp)"),
        "rationale": "the base-model arm is reshaped to bind the reference and "
                     "the import list to `let`s before returning the pair; the "
                     "returned value is byte-identical, so `out = typeRef t` "
                     "still holds and the frozen `loom_solve <;> simp_all "
                     "[typeRef]` proof closes unchanged. A faithful correct "
                     "reshape that could NOT verify would mean SPEC-TOO-STRONG "
                     "(the postcondition over-fit to the gold return SHAPE).",
    },
    {
        "id": "pos-reshape-tail-arm",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _BASE, _RET_TAIL,
            "          let m := t.moduleName\n"
            '          return (m ++ "." ++ t.qualName, ["import " ++ m])'),
        "rationale": "the module-tail arm is reshaped to bind the module name "
                     "once and reuse it in both the reference and the import; "
                     "the returned value is identical for every input, so "
                     "`out = typeRef t` still holds and the frozen proof closes "
                     "unchanged. A different-shape CORRECT impl that could not "
                     "verify would mean SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-reshape-ladder-inverted",
        "kind": "soundness",
        "expect": "verify",
        # The ORDER of the ladder is inverted: the fall-through arm is tested
        # FIRST, under the explicit conjunction of the negated guards, and the
        # three special arms are tried after. This is a genuinely different
        # control shape (not a `let`-rebinding of the frozen one) that agrees
        # with `typeRef` at every input, because the guards are mutually
        # exclusive by construction. It is the strongest available
        # SPEC-TOO-STRONG probe: the frozen `ensures` pins a whole-value
        # equality, so a spec over-fit to the frozen ARM ORDER would reject it.
        "module": _swap(
            _BASE,
            "    if t.isBaseModelType then\n"
            '      return ("models.Model", ["from django.db import models"])\n'
            "    else\n"
            "      if t.isNoneType then\n"
            '        return ("type(None)", [])\n'
            "      else\n"
            '        if t.moduleName = "builtins" then\n'
            "          return (t.simpleName, [])\n"
            "        else\n"
            '          return (t.moduleName ++ "." ++ t.qualName, '
            '["import " ++ t.moduleName])',
            "    if !t.isBaseModelType && !t.isNoneType "
            '&& !(t.moduleName = "builtins") then\n'
            '      return (t.moduleName ++ "." ++ t.qualName, '
            '["import " ++ t.moduleName])\n'
            "    else\n"
            "      if t.isBaseModelType then\n"
            '        return ("models.Model", ["from django.db import models"])\n'
            "      else\n"
            "        if t.isNoneType then\n"
            '          return ("type(None)", [])\n'
            "        else\n"
            "          return (t.simpleName, [])"),
        "rationale": "the four-arm ladder is REORDERED, not merely rebound: the "
                     "fall-through arm is decided first under the explicit "
                     "conjunction of negated guards, and the three special arms "
                     "follow. Every input still lands on the same arm (the guards "
                     "are mutually exclusive), so `out = typeRef t` holds and the "
                     "frozen `loom_solve <;> simp_all [typeRef]` proof closes "
                     "unchanged. This is the ORDER-independence control: the "
                     "other two positives keep the frozen arm order and only "
                     "rebind within one arm, so neither would catch a "
                     "postcondition over-fit to the ladder's SHAPE. If a correct "
                     "reshape this far from the frozen control flow could not "
                     "verify => SPEC-TOO-STRONG.",
    },

    # =====================================================================
    # ADMISSIBILITY — the method carries NO `require` clause, so no input is
    # excluded and the sibling's "a normal F2P input satisfies the precondition"
    # probe is vacuous. The residual admissibility risk on a total domain is that
    # the post-image is DEGENERATE / unsatisfiable — a spec no impl can meet
    # reads exactly like a spec every impl meets. This case discharges an
    # in-region assert that the post-image is non-degenerate: the import set
    # genuinely tracks the arm (non-empty for the base-model arm, empty for the
    # none-type arm), and the module-tail reference genuinely tracks the module
    # and qualified names. The impl body is kept verbatim so the method's own
    # `ensures` still discharges; `loom_solve <;> simp_all [typeRef]` also clears
    # the assert VC, so NO proof retune is needed.
    # =====================================================================
    {
        "id": "admiss-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _IMPL_START,
            _IMPL_START +
            "    assert (with_name_prefix `admiss\n"
            "      ((typeRef " + _IN_BASE + ").2 = "
            '["from django.db import models"] ∧\n'
            "       (typeRef " + _IN_NONE + ").2 = ([] : List String) ∧\n"
            "       (typeRef " + _IN_TAIL + ") = "
            '("datetime.date", ["import datetime"])))\n'),
        "rationale": "the post-image is satisfiable AND non-degenerate: the "
                     "import set genuinely varies with the arm (the base-model "
                     "arm carries a non-empty namespace import, the none-type "
                     "arm carries the empty list — the import clause is not a "
                     "constant), and the module-tail arm genuinely renders "
                     "`module.qualified_name` with the matching `import module` "
                     "(the reference is not a constant either). The in-region "
                     "assert must discharge (else an unsatisfiable/degenerate "
                     "obligation would read as trivially met) and the impl body "
                     "is kept verbatim so `out = typeRef t` discharges too. "
                     "`loom_solve <;> simp_all [typeRef]` clears the assert, so "
                     "no proof retune is needed.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected. Each is a straight-line COMPUTABLE impl (so its
    # witness reduces under `decide`), refuted at a concrete TypeInfo input by a
    # witness that fails on the frozen solution, and each carries the refinement
    # argument that its faithful real counterpart would NOT resolve the F2P.
    # =====================================================================
    {
        "id": "weak-base-drops-import",
        "kind": "uniqueness",
        "expect": "reject",
        # THE bug-delta (= Solution_prepatch): the base-model arm renders the
        # reference with an EMPTY import list. Correct on every other arm, wrong
        # on the base-model arm.
        "module": _swap(_BASE, _RET_BASE,
                        '      return ("models.Model", [])'),
        "refinement": "this is the pre-patch behaviour: the base-model arm emits "
                      "its reference with NO accompanying import. A faithful "
                      "patch that kept it would render a bare base-model "
                      "reference into a generated migration with the namespace "
                      "import dropped, so executing that migration raises a name "
                      "error on the bare name. The F2P asserts the base-model "
                      "reference serializes with EXACTLY the namespace import "
                      "present, which an empty import set cannot satisfy, so the "
                      "faithful patch does NOT resolve.",
        "rationale": "REJECT from `out = typeRef t` on arm B1: `typeRef` pins "
                     "the base-model arm's imports to the singleton namespace "
                     "import; this rival returns the empty list, which cannot "
                     "equal it. Refuted at the base-model arm — the F2P "
                     "discriminator. If it verified => SPEC-TOO-WEAK.",
        "witness": _witness(_IN_BASE),
    },
    {
        "id": "weak-base-wrong-import",
        "kind": "uniqueness",
        "expect": "reject",
        # Base-model arm carries a NON-EMPTY but WRONG import (`import models`
        # instead of the namespace import). The import set is non-empty, so a
        # spec that only demanded "some import" would accept it — but the whole-
        # value equality pins the EXACT statement.
        "module": _swap(_BASE, _RET_BASE,
                        '      return ("models.Model", ["import models"])'),
        "refinement": "the base-model arm carries a non-empty but incorrect "
                      "import statement. A faithful patch emitting that import "
                      "does NOT bring the bare name the reference uses into "
                      "scope, so the rendered reference still raises a name "
                      "error at migration time, and the F2P's exact-import "
                      "assertion FAILS. The faithful patch does NOT resolve.",
        "rationale": "REJECT from `out = typeRef t` on arm B1: the postcondition "
                     "pins the EXACT import statement; a non-empty but different "
                     "singleton cannot equal it. Confirms B1 is exact-content, "
                     "not mere non-emptiness. Refuted at the base-model arm. If "
                     "it verified => SPEC-TOO-WEAK.",
        "witness": _witness(_IN_BASE),
    },
    {
        "id": "weak-base-truncated-import",
        "kind": "uniqueness",
        "expect": "reject",
        # Base-model arm carries a TRUNCATED import (drops the final char): a
        # near-miss that is non-empty and shares a long prefix with the correct
        # statement, distinguished only at the full-string level.
        "module": _swap(
            _BASE, _RET_BASE,
            '      return ("models.Model", ["from django.db import model"])'),
        "refinement": "the base-model arm's import is truncated by one character "
                      "('...models' -> '...model'). A faithful patch emitting "
                      "that statement imports nothing under the name the "
                      "reference uses, so the rendered reference still raises a "
                      "name error and the F2P's exact-import assertion FAILS. "
                      "The faithful patch does NOT resolve.",
        "rationale": "REJECT from `out = typeRef t` on arm B1: a strict-prefix "
                     "import string is not equal to the exact statement `typeRef` "
                     "pins. This is the near-miss the exact-content clause exists "
                     "to catch. Refuted at the base-model arm. If it verified => "
                     "SPEC-TOO-WEAK.",
        "witness": _witness(_IN_BASE),
    },
    {
        "id": "weak-none-spurious-import",
        "kind": "uniqueness",
        "expect": "reject",
        # Fix-the-wrong-row / anti-guard: the none-type arm (a no-import
        # built-in expression) is given the namespace import too. Correct on the
        # base-model arm, wrong on the none-type arm.
        "module": _swap(
            _BASE, _RET_NONE,
            '        return ("type(None)", ["from django.db import models"])'),
        "refinement": "the none-type arm surfaces a SPURIOUS namespace import "
                      "for an expression that needs none. A faithful patch doing "
                      "this attaches an unused import to every migration "
                      "referencing the none expression; the P2P "
                      "test_serialize_type_none asserts an EMPTY import set for "
                      "that arm (and 'django.db.models shouldn't be imported if "
                      "unused' would regress), so the faithful patch does NOT "
                      "resolve.",
        "rationale": "REJECT from `out = typeRef t` on arm B2: `typeRef` pins the "
                     "none-type arm's imports to the empty list; a non-empty set "
                     "cannot equal it. This is the anti-'fix the wrong row' guard "
                     "(dual to the base-drop attack). Refuted at the none-type "
                     "arm — a DIFFERENT input from the B1 rivals, exercising the "
                     "none-type flag. If it verified => SPEC-TOO-WEAK.",
        "witness": _witness(_IN_NONE),
    },
    {
        "id": "weak-tail-drops-import",
        "kind": "uniqueness",
        "expect": "reject",
        # Module-tail arm (B4, no nagini counterpart — the sibling models only
        # the two distinguished rows) renders the qualified reference with an
        # EMPTY import instead of the matching `import module`.
        "module": _swap(
            _BASE, _RET_TAIL,
            '          return (t.moduleName ++ "." ++ t.qualName, [])'),
        "refinement": "the module-tail arm renders a `module.qualified_name` "
                      "reference with NO `import module`. A faithful patch doing "
                      "this drops the import a non-special type's reference needs, "
                      "so a generated migration referencing such a type raises a "
                      "name error; the module-tail serialization tests assert the "
                      "matching import is present, so the faithful patch does NOT "
                      "resolve.",
        "rationale": "REJECT from `out = typeRef t` on arm B4: `typeRef` pins the "
                     "module-tail imports to the singleton `import module`; the "
                     "empty list cannot equal it. Refuted at the module-tail arm "
                     "— an arm with no nagini counterpart, exercising the general "
                     "module-name field. If it verified => SPEC-TOO-WEAK.",
        "witness": _witness(_IN_TAIL),
    },
    {
        "id": "weak-tail-wrong-reference",
        "kind": "uniqueness",
        "expect": "reject",
        # Module-tail arm renders the reference from the BARE name instead of the
        # qualified name. Correct whenever qualName == simpleName (the common
        # case), wrong precisely when they differ (a nested type). Attacks the
        # STRING component of the output, not the imports.
        "module": _swap(
            _BASE, _RET_TAIL,
            '          return (t.moduleName ++ "." ++ t.simpleName, '
            '["import " ++ t.moduleName])'),
        "refinement": "the module-tail arm builds the reference from the bare "
                      "name rather than the qualified (dotted) name. A faithful "
                      "patch doing this mis-renders any nested type "
                      "(module.Outer.Inner -> module.Inner), producing a "
                      "reference that does not resolve to the intended type; the "
                      "module-tail serialization tests assert the fully-qualified "
                      "reference, so the faithful patch does NOT resolve.",
        "rationale": "REJECT from `out = typeRef t` on arm B4's STRING component: "
                     "`typeRef` renders `module ++ '.' ++ qualName`; using "
                     "`simpleName` differs whenever the qualified name is not the "
                     "bare name. Refuted at a NESTED type (qualName='Outer.Inner', "
                     "simpleName='Inner') — the near-miss input that distinguishes "
                     "the two fields, and the only rival attacking the rendered "
                     "string rather than the imports. If it verified => "
                     "SPEC-TOO-WEAK.",
        "witness": _witness(_IN_TAIL_NESTED),
    },
    {
        "id": "weak-builtin-spurious-import",
        "kind": "uniqueness",
        "expect": "reject",
        # Builtins arm (B3, no nagini counterpart) attaches a spurious
        # `import builtins` to a bare built-in name that needs no import.
        "module": _swap(
            _BASE, _RET_BUILTIN,
            '          return (t.simpleName, ["import " ++ t.moduleName])'),
        "refinement": "the built-in-namespace arm attaches a spurious "
                      "`import builtins` to a bare built-in name. A faithful "
                      "patch doing this emits an unused/invalid import into every "
                      "migration referencing a built-in type; the built-in "
                      "serialization tests assert an EMPTY import set for that "
                      "arm, so the faithful patch does NOT resolve.",
        "rationale": "REJECT from `out = typeRef t` on arm B3: `typeRef` pins the "
                     "built-in arm's imports to the empty list; a non-empty set "
                     "cannot equal it. Refuted at a built-in type "
                     "(moduleName='builtins') — an arm with no nagini "
                     "counterpart, exercising the built-in module-name value. If "
                     "it verified => SPEC-TOO-WEAK.",
        "witness": _witness(_IN_BUILTIN),
    },
    {
        "id": "weak-none-returns-base-pair",
        "kind": "uniqueness",
        "expect": "reject",
        # The sibling's wrong-ROW observable, stated literally on the unrolled
        # ladder: the none-type arm returns the BASE-MODEL arm's whole pair —
        # both the rendered string AND the imports. Strictly stronger than
        # weak-none-spurious-import, which corrupts only the import component of
        # that arm and leaves the reference right; this rival also mis-renders
        # the reference, so it is the only rival that attacks BOTH components of
        # one arm at once.
        "module": _swap(
            _BASE, _RET_NONE,
            '        return ("models.Model", '
            '["from django.db import models"])'),
        "refinement": "the none-type arm surfaces the base-model arm's ENTIRE "
                      "result — the base-model reference together with the "
                      "namespace import — instead of its own. A faithful patch "
                      "doing this renders the wrong reference for the "
                      "none-valued type, so a migration that meant to name that "
                      "type names a different one (silently changing what the "
                      "migration declares) and carries an import it does not "
                      "need. The P2P test_serialize_type_none asserts the "
                      "none-valued type serializes to its own built-in "
                      "expression with an EMPTY import set; both halves fail, so "
                      "the faithful patch does NOT resolve.",
        "rationale": "REJECT from `out = typeRef t` on arm B2, on BOTH output "
                     "components at once: `typeRef` pins the none-type arm to "
                     "(the built-in none expression, []), and this rival returns "
                     "(the base-model reference, [the namespace import]). This is "
                     "the sibling's `weak-always-return-row0` observable — one "
                     "arm surfacing another arm's whole row — expressible here "
                     "even though the table scan is unrolled, because the "
                     "observable is about the RESULT, not the scan. Refuted at "
                     "the none-type arm. If it verified => SPEC-TOO-WEAK.",
        "witness": _witness(_IN_NONE),
    },
    {
        "id": "weak-builtin-wrong-name-field",
        "kind": "uniqueness",
        "expect": "reject",
        # Builtins arm reads the QUALIFIED name where the spec pins the BARE
        # name. Invisible at every input where the two coincide (which is every
        # other witness in this battery, including _IN_BUILTIN) — hence the
        # dedicated nested-name input. Attacks the STRING component of arm B3;
        # every other B3/B2 rival attacks only the import component.
        "module": _swap(_BASE, _RET_BUILTIN,
                        "          return (t.qualName, [])"),
        "refinement": "the built-in-namespace arm renders the type's qualified "
                      "(dotted) name where the source renders its bare name. A "
                      "faithful patch doing this emits a dotted reference for a "
                      "built-in that must be named bare, and since that arm "
                      "deliberately carries no import, the dotted prefix "
                      "resolves against nothing at migration time. The built-in "
                      "serialization tests assert the BARE name for that arm, so "
                      "the faithful patch does NOT resolve.",
        "rationale": "REJECT from `out = typeRef t` on arm B3's STRING component: "
                     "`typeRef` renders `simpleName` on the built-in arm, and "
                     "`qualName` differs from it whenever the type is nested. "
                     "Refuted at a NESTED built-in name (qualName='Outer.Inner', "
                     "simpleName='Inner'): this is the input the rest of the "
                     "battery lacked — every other B3 witness has "
                     "qualName == simpleName, so a wrong-name-field read on this "
                     "arm was previously unobservable. If it verified => "
                     "SPEC-TOO-WEAK.",
        "witness": _witness(_IN_BUILTIN_NESTED),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 8 SPEC cases (2 soundness
# positives, 1 admissibility, 5 uniqueness rivals) plus 1 AXIOM_TEST, and it
# explicitly records that the frame/permission-mutation class is inapplicable
# (no read-only heap input). This bundle models a WIDER classifier than the
# sibling: nagini models only the two distinguished rows (base-model, none-type)
# as a two-row table scan, whereas the velvet carrier models the full four-arm
# ordered ladder (base-model, none-type, builtins, module-tail). So the port
# ATTACKS MORE surface, not less.
#
#   sibling case                    -> here                          disposition
#   -----------------------------------------------------------------------------
#   pos-control-reorder-columns     -> pos-reshape-base-arm           RE-AIMED
#   pos-control-direct-branch       -> pos-reshape-tail-arm           RE-AIMED
#   admiss-base-and-other           -> admiss-nondegenerate           RE-AIMED
#   weak-empty-directive-prepatch   -> weak-base-drops-import         PORTED
#   weak-wrong-directive-content    -> weak-base-wrong-import         PORTED
#   weak-truncated-directive        -> weak-base-truncated-import     PORTED
#   weak-always-return-row0         -> weak-none-returns-base-pair     PORTED
#   weak-other-row-nonempty         -> weak-none-spurious-import       PORTED
#   (no sibling)                    -> weak-tail-drops-import          ADDED
#   (no sibling)                    -> weak-tail-wrong-reference       ADDED
#   (no sibling)                    -> weak-builtin-spurious-import    ADDED
#   (no sibling)                    -> weak-builtin-wrong-name-field   ADDED
#   (no sibling)                    -> pos-reshape-ladder-inverted     ADDED
#   ax-ref-typeserializer-...       -> (none)                         DROPPED
#
# RE-AIMED (positives): the sibling reshapes the gold table impl (reorder the
#   two copy loops; branch-and-materialise directly). This backend's impl is
#   already a direct branch ladder, so the reshape is applied per-arm: bind the
#   base-model arm's (reference, import) to `let`s (pos-reshape-base-arm) and
#   bind the module-tail arm's module name once (pos-reshape-tail-arm). Both
#   return byte-identical values, so `out = typeRef t` holds and the frozen
#   `loom_solve <;> simp_all [typeRef]` proof closes unchanged. Verified to build
#   (EXIT 0). pos-reshape-ladder-inverted was ADDED during audit as the
#   order-independence control the two `let`-rebinding positives could not
#   provide (both keep the frozen arm order); it also builds under the frozen
#   proof (EXIT 0).
#
# PROOF-SENSITIVITY of the positive lane (recorded so a future port does not
#   mistake it for a spec hole). The frozen script
#   `loom_solve <;> simp_all [typeRef]` is not shape-agnostic: a correct reshape
#   that computes the two output COMPONENTS separately and pairs them at the end
#   (`let ref := if ... ; let imps := if ... ; return (ref, imps)`) leaves
#   `simp_all` with an unsolved goal, because the residual obligation is a
#   pair-of-ifs vs if-of-pairs distribution that `simp_all [typeRef]` does not
#   perform. This is a TACTIC gap, not SPEC-TOO-STRONG: the same reshape verifies
#   (EXIT 0) once the proof body is retuned to `loom_solve <;> simp_all [typeRef]
#   <;> split_ifs <;> simp_all`, and also under
#   `loom_solve <;> (unfold typeRef; split_ifs <;> rfl)`. Both retunes are inside
#   the elided tactic body, so `same_spec` is untouched. It is not carried as a
#   case because a positive control whose proof had to be retuned attests to the
#   retune rather than to the spec; the order-inverted positive above is the
#   stronger control and needs no retune. The spec is NOT over-fit to the return
#   shape — it is a whole-value equality — but the shipped SCRIPT is tuned to the
#   frozen ladder, which is the ordinary condition of a tactic-proof backend and
#   exactly why every reject case here carries a witness.
# RE-AIMED (admissibility): the sibling self-calls on the F2P input to establish
#   the precondition. This backend has no `require` clause, so that probe is
#   vacuous; it is re-aimed at the residual total-domain risk — a
#   DEGENERATE/unsatisfiable post-image — via an in-region assert that the import
#   set genuinely varies with the arm (non-empty base-model, empty none-type) and
#   the module-tail reference genuinely tracks the module/qualified names. Impl
#   kept verbatim; `loom_solve <;> simp_all [typeRef]` clears the assert (no
#   retune). Verified to build (EXIT 0).
# PORTED (B1 trio + B2 guard): the empty/wrong/truncated-directive rivals become
#   weak-base-drops-import (the bug-delta = Solution_prepatch), weak-base-wrong-
#   import, weak-base-truncated-import; the fix-the-wrong-row rival becomes
#   weak-none-spurious-import. Each carries a machine-checked witness that
#   ELABORATES against its straight-line rival (EXIT 0) and FAILS against the
#   frozen solution (EXIT 1).
# PORTED (weak-always-return-row0): the sibling's wrong-ROW table scan has no
#   MECHANISM counterpart — there is no runtime table to mis-index; the two-row
#   scan is unrolled into a static `if/else` ladder (mapping.md §2a). But its
#   OBSERVABLE — one arm surfacing another arm's WHOLE (string, imports) row — is
#   about the RESULT, not the scan, so it is expressible verbatim on the ladder
#   and is now carried literally by weak-none-returns-base-pair (the none-type
#   arm returns the base-model arm's reference AND its import). Earlier this was
#   recorded as CARRIED-by-intent across weak-none-spurious-import and the tail
#   rivals; that under-ported the case, since those rivals each corrupt only ONE
#   output component of an arm and none surfaces another arm's full row.
# ADDED (B3, B4 — no sibling counterpart, from the WIDER carrier): the sibling
#   models neither the builtins arm nor the module-tail arm, so these four
#   rivals have no nagini sibling. weak-tail-drops-import (tail imports emptied),
#   weak-tail-wrong-reference (tail reference built from the bare name, attacking
#   the rendered STRING at a nested type), weak-builtin-spurious-import (builtins
#   arm given a spurious import), weak-builtin-wrong-name-field (builtins arm
#   renders the QUALIFIED name where the spec pins the bare one, attacking the
#   rendered STRING on arm B3 at a nested built-in name — the point the rest of
#   the battery could not observe, since every other B3 input has
#   qualName == simpleName). Each carries a discriminating witness.
# DROPPED (ax-ref-typeserializer-serialize-equals-real): the sibling's axiom lane
#   re-runs the real-callee equivalence. That is a G-AX concern; this bundle
#   declares no axiom and no A-reference deep model (the whole classifier is
#   modeled deeply as `typeRef`, all I/R ops — mapping.md §3, refinement.md §B),
#   so there is nothing for the axiom lane to probe and the gate ignores
#   AXIOM_TESTS regardless. G-AX is `skip` for this bundle.
# VACUOUS (frame/permission-mutation): the sibling records there is NO read-only
#   heap input to overwrite even on nagini. Lean and Velvet are referentially
#   transparent — the input is an immutable value, no `mut` parameter, no heap,
#   no aliasing, no mutable `self`. No substitute fabricated (per the porting
#   map: this class is vacuous here).
#
# BINDER / FIELD COVERAGE of the nine reject witnesses over the input record's
#   fields and the two output components:
#     isBaseModelType — true (weak-base-* trio), false (all others): varied.
#     isNoneType      — true (weak-none-spurious-import,
#                       weak-none-returns-base-pair), false (others): varied.
#     moduleName      — "builtins" (the two builtins rivals, driving arm B3),
#                       "datetime"/"mymod" (tail rivals, driving arm B4), "m"
#                       (base/none rivals where module is INNOCENT — proving the
#                       base/none arms do not secretly depend on the module name):
#                       varied.
#     qualName        — distinct from simpleName ("Outer.Inner" vs "Inner") in
#                       weak-tail-wrong-reference (arm B4) and
#                       weak-builtin-wrong-name-field (arm B3), equal elsewhere:
#                       varied, and now separated on BOTH arms that read a name
#                       field rather than only on B4.
#     simpleName      — "int" (builtins arm reads it), "Inner"/others: varied.
#   OUTPUT COMPONENTS: the import set is attacked on every arm (B1 drop/wrong/
#     trunc, B2 spurious, B3 spurious, B4 drop); the rendered STRING is attacked
#     on B2 (weak-none-returns-base-pair), B3 (weak-builtin-wrong-name-field) and
#     B4 (weak-tail-wrong-reference). So both projections of `out = typeRef t` are
#     defended, and on three of the four arms both projections are attacked
#     independently. The nine reject witnesses probe SIX DISTINCT input points
#     (base-model, none-type, builtins, nested-builtins, datetime-tail,
#     nested-tail; the three B1 rivals share the base-model input because they
#     fail there for the SAME reason — the base-model import is wrong — each a
#     distinct wrongness of the same clause at the same discriminating arm).
#     pts=6.
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job and this bundle declares no
# axiom and no A-reference deep model, so there is nothing there to probe.
AXIOM_TESTS = []
