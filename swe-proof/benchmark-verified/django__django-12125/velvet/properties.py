"""properties.py — G-PBT falsification battery for django__django-12125 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed —
both of which the consumer spec view elides, so ``markers.same_spec`` holds and
the ``prove_correct typeReference`` obligation survives with a byte-identical
statement) and swaps in a candidate implementation; it is checked by the real
verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness must ELABORATE against the rival and FAIL
against the frozen solution).

DEFENDED SURFACE (one contracted method over a type-value carrier). The modeled
operation renders the source-text reference that names a type value, together
with the import line needed to make that reference resolve:

  typeReference (t : TypeValue) return (out : Rendered)
    ensures out = renderRef t                                    -- (C0) master
    ensures (¬ t.isSentinelBase ∧ ¬ t.isNoneType ∧ ¬ t.isBuiltin)
              → out = { expr := t.module ++ ['.'] ++ t.qualified,
                        imp := some ("import ".toList ++ t.module) }   -- (C1)
    ensures (¬ t.isSentinelBase ∧ ¬ t.isNoneType ∧ t.isBuiltin)
              → out = { expr := t.bare, imp := none }                   -- (C2)

``renderRef`` is a fully-grounded pure dispatch over the input fields (flat
string concatenation, no opaque oracle / answer-key), so pinning ``out =
renderRef t`` is grounded, not an echo (directive 8) — returning the
concatenation IS the correct work. The master clause (C0) pins the whole
per-kind behaviour; (C1) and (C2) restate the two branches the F2P/P2P tests
turn on so a rival that mishandles either is caught even by the weaker restated
form.

THE modeled change. In the GENERAL branch (a value that is neither of the two
sentinel kinds nor a built-in) the reference is keyed by the value's FULL
within-module location — the location that keeps every enclosing scope
(``qualified``) — NOT by the value's own bare name without enclosing scope
(``bare``). These two fields DIFFER exactly when the value is nested inside
another (an inner class): for a top-level value they coincide, so the
distinction is observable only on the nested case — which is precisely the F2P.
Any rival that, in the general branch, keys the reference on ``bare`` (or
otherwise drops the enclosing chain / the dot / the import) renders the wrong
reference and does NOT resolve the F2P.

BINDER STRUCTURE (read before judging binder coverage). The method has ONE input
binder ``t : TypeValue`` with SIX observed fields; the reject witnesses vary
every one that the modeled behaviour reacts to:

  * ``isSentinelBase`` / ``isNoneType`` / ``isBuiltin`` — the three priority
    flags selecting the branch. A rival that corrupts one branch is caught only
    at an input that ENTERS that branch, so the witness set moves each flag to
    ``true`` at least once (``weak-sentinel-branch`` / ``weak-none-branch`` /
    ``weak-builtin-always-qualified``) and holds them all ``false`` for the
    general-branch rivals.
  * ``module`` — the module prefix and the import body; attacked by
    ``weak-drop-dot`` (the dot between module and location) and
    ``weak-no-import`` (the import line built from it).
  * ``qualified`` — the FULL within-module location; attacked by
    ``weak-leaf-name`` at an input where ``qualified`` (``"A.B"``) differs from
    ``bare`` (``"B"``), the nested-value case the fix turns on.
  * ``bare`` — the own name without enclosing scope; read by the built-in
    branch (attacked by ``weak-builtin-always-qualified``) and by the
    ``weak-none-branch`` rival that renders it in place of the sentinel spelling.

ADVERSARIAL READ of the nagini classes on this carrier:
  * ADMISSIBILITY — RE-AIMED, not dropped. The method declares no ``require``, so
    there is no precondition to admit; that does NOT make the lane vacuous. The
    analogue on a total carrier is the OBLIGATION being unsatisfiable at exactly
    an F2P-shaped input, which ``admiss-obligation-satisfiable-at-nested`` tests
    directly by discharging the method's own triple at the concrete nested point
    (by evaluation, as a ``have``, before closing the frozen obligation verbatim).
  * FRAME-MUTATION (permission overwrite of a read-only input) — VACUOUS. The
    nagini sibling carries a mandatory frame-mutation probe because its three
    text inputs are held at a fractional heap permission (``Acc(.,1/2)``) an
    impl can illegally overwrite. Lean/Velvet are referentially transparent:
    ``t`` is an immutable value, there is no ``mut`` binder, no heap and no
    aliasing — so there is no read-only input to mutate and no substitute probe
    to build. Per the porting map this class is vacuous here; NOT fabricated.
  * UNGROUNDED-ORACLE ECHO — N/A. The ``axioms`` region is empty (no callee is
    axiomatized; the dispatch is modeled deeply), and every post-image is a flat
    function of the input fields, not an answer-key. There is nothing to echo;
    the positives are honest grounded reshapes. (The nagini sibling reached the
    same conclusion — its ``dotted_path`` / ``import_line`` helpers were grounded
    @Pure concatenations, so an echo of them was CORRECT work, not a wrong echo.)

DIVERGENCE LANE - the class is INAPPLICABLE to this impl and CLOSED BY THE
SEMANTICS against any rival that manufactures it. The frozen impl is LOOP-FREE
(straight-line ``if`` over immutable values, no loop and no recursion), so
there is no control flow here to make diverge: a diverging rival cannot be
obtained by mutating this body, it has to bring a loop of its own. When it
does, the semantics refuse it. This bundle sets
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

WITNESS PLACEMENT. Each reject rival is refuted at a concrete ``t`` reaching the
``method`` contract through Velvet's own tester machinery
(``typeReferenceTester t = false`` says the extracted program's result violates
the postcondition at that input). ``TypeValue`` / ``Rendered`` are concrete
records over ``Bool`` / ``List Char`` / ``Option (List Char)``, so ``decide``
settles every equality at a concrete input. There are NO ``require`` clauses, so
every input reaches the postcondition (the tester never short-circuits). Each
witness is checked in a file whose ``prove_correct`` block has been stripped, so
no tactic script can mask the verdict, and was verified out-of-band with two
real builds: it ELABORATES against the rival and FAILS against the frozen
solution. No two rivals are refuted at the same input (pts = 6).

AXIOM lane: EMPTY (the ``axioms`` region declares no ``axiom``; the dispatch is
modeled deeply, not delegated to an oracle). The gate ignores ``AXIOM_TESTS``
regardless. Nagini→velvet accounting is at the bottom of the file.
"""
from pathlib import Path

INSTANCE = "django__django-12125"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchors. Each lies wholly inside the single
# ---- `-- impl-start`/`-- impl-end` region and is unique in Solution.lean (both
# ---- facts asserted at load by _swap), so a swap edits only the impl body and
# ---- `markers.same_spec` holds by construction.

# The full frozen impl body (everything strictly between the markers), used by
# the reshape positives that replace the entire dispatch.
_FULL = (
    "    -- Dispatch in priority order; build and return the reference for the first\n"
    "    -- matching kind. A general value is named by its module joined to its full\n"
    "    -- within-module location (the location that keeps every enclosing scope),\n"
    "    -- and imports that module.\n"
    "    if t.isSentinelBase then\n"
    '      return { expr := "models.Model".toList, imp := none }\n'
    "    else\n"
    "      if t.isNoneType then\n"
    '        return { expr := "type(None)".toList, imp := none }\n'
    "      else\n"
    "        if t.isBuiltin then\n"
    "          return { expr := t.bare, imp := none }\n"
    "        else\n"
    "          return { expr := t.module ++ ['.'] ++ t.qualified,\n"
    '                   imp := some ("import ".toList ++ t.module) }\n'
)

# The general-branch return (unique multi-line substring, wholly inside impl).
_GENERAL_RET = (
    "          return { expr := t.module ++ ['.'] ++ t.qualified,\n"
    '                   imp := some ("import ".toList ++ t.module) }'
)
# The built-in-branch return (unique).
_BUILTIN_RET = "          return { expr := t.bare, imp := none }"
# The sentinel-base-branch return (unique).
_SENTINEL_RET = '      return { expr := "models.Model".toList, imp := none }'
# The none-type-branch return (unique).
_NONE_RET = '        return { expr := "type(None)".toList, imp := none }'

assert _BASE.count(_FULL) == 1, "impl body drifted from expected text"


def _full(new_body: str) -> str:
    """Solution.lean with the ENTIRE impl body replaced (spec view untouched)."""
    return _swap(_BASE, _FULL, new_body)


def _general(new_ret: str) -> str:
    """Solution.lean with only the general-branch return replaced."""
    return _swap(_BASE, _GENERAL_RET, new_ret)


def _builtin(new_ret: str) -> str:
    return _swap(_BASE, _BUILTIN_RET, new_ret)


def _sentinel(new_ret: str) -> str:
    return _swap(_BASE, _SENTINEL_RET, new_ret)


def _none(new_ret: str) -> str:
    return _swap(_BASE, _NONE_RET, new_ret)


# ---- witness preamble. The spec is a `method` CONTRACT, not a bare predicate,
# ---- so a witness reaches it through Velvet's tester machinery:
# ---- `typeReferenceTester t = false` says the extracted program's result
# ---- violates the postcondition at the concrete input `t`. Checked in a file
# ---- whose `prove_correct` block has been stripped.
_TESTER = (
    "extract_program_for typeReference\n"
    "prove_precondition_decidable_for typeReference\n"
    "prove_postcondition_decidable_for typeReference\n"
    "derive_tester_for typeReference\n\n"
)


def _tv(sb: str, nt: str, bi: str, mod: str, qual: str, bare: str) -> str:
    """A TypeValue record literal (booleans as Lean `true`/`false`; strings as
    `.toList` of a literal so `decide` computes the List Char)."""
    return (
        "{ isSentinelBase := " + sb
        + ", isNoneType := " + nt
        + ", isBuiltin := " + bi
        + ', module := "' + mod + '".toList'
        + ', qualified := "' + qual + '".toList'
        + ', bare := "' + bare + '".toList }'
    )


def _witness(tv_literal: str) -> str:
    return _TESTER + f"example : typeReferenceTester {tv_literal} = false := by\n  decide\n"


# ---- the frozen obligation's tactic body. It is elided from the consumer spec
# ---- view, so prepending a `have` to it keeps `markers.same_spec` and leaves the
# ---- `prove_correct typeReference` header (and the statement it discharges)
# ---- byte-identical — the admissibility case's only edit.
_PROOF = "prove_correct typeReference by\n  loom_solve <;> simp_all [renderRef]"
assert _BASE.count(_PROOF) == 1, "proof anchor drifted from expected text"

# The F2P-shaped input: a general value NESTED inside another, so its full
# within-module location ("A.B") differs from its own bare name ("B"). This is the
# exact point the modeled behaviour turns on.
_ADM_TV = _tv("false", "false", "false", "m", "A.B", "B")
# What the obligation demands there, written out as a ground literal rather than
# as a function of the input: module + '.' + FULL location, importing the module.
_ADM_OUT = '{ expr := "m.A.B".toList, imp := some ("import m".toList) }'

# ADMISSIBILITY, discharged BY EVALUATION at that concrete input BEFORE the frozen
# obligation is closed verbatim. `hadm` proves the method's own Hoare triple is
# SATISFIABLE at the F2P-shaped point: the impl's guard ladder reduces there, the
# `wp` of the resulting `pure` is taken, and BOTH conjuncts close by `decide` — the
# master clause (C0) `out = renderRef t` and, independently, the ground post-image
# `_ADM_OUT`. If the obligation were unsatisfiable at exactly this input — a
# post-image no computation can hit, the total-carrier analogue of a `require` no
# legitimate input meets — this `have` could not be discharged and the case would
# FAIL, which is PRECOND-TOO-STRONG. The frozen `loom_solve <;> simp_all
# [renderRef]` still closes the real obligation afterwards, so nothing is weakened
# and no clause is restated: the `have` is an ADDITION whose failure is the finding.
_PROOF_ADMISS = f"""prove_correct typeReference by
  have hadm : triple True (typeReference {_ADM_TV})
      (fun out => out = renderRef {_ADM_TV} ∧ out = {_ADM_OUT}) := by
    simp only [typeReference, triple, Bool.false_eq_true, if_false]
    intro _
    rw [wp_pure]
    exact ⟨by decide, by decide⟩
  loom_solve <;> simp_all [renderRef]"""


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROL 1 (soundness) — a structurally different but CORRECT
    # impl that MUST verify, else SPEC-TOO-STRONG. Instead of the inlined
    # priority dispatch, return the pure model `renderRef t` directly. The
    # ensures IS `out = renderRef t`, so the body is definitionally the RHS and
    # the frozen `loom_solve <;> simp_all [renderRef]` script closes the
    # byte-identical obligation. Verified out-of-band with a real build.
    # =====================================================================
    {
        "id": "pos-render-direct",
        "kind": "soundness",
        "expect": "verify",
        "module": _full("    return renderRef t\n"),
        "rationale": (
            "structurally different CORRECT impl: it returns the grounded pure "
            "model `renderRef t` directly rather than re-inlining the priority "
            "dispatch. Observationally identical on every input, so (C0) "
            "`out = renderRef t` holds on the whole domain and (C1)/(C2) follow. "
            "A faithful reshape MUST verify, else the postcondition is "
            "SPEC-TOO-STRONG (it would reject its own model's output)."
        ),
    },
    # =====================================================================
    # POSITIVE CONTROL 2 (soundness) — local-variable reshape of the general
    # branch: stage the reference expression and the import body into typed
    # locals, then build the record from them. Same values, reshaped executable
    # form; every branch and both clauses are preserved. MUST verify. Verified
    # out-of-band with a real build.
    # =====================================================================
    {
        "id": "pos-general-locals",
        "kind": "soundness",
        "expect": "verify",
        "module": _general(
            "          let e : List Char := t.module ++ ['.'] ++ t.qualified\n"
            '          let i : List Char := "import ".toList ++ t.module\n'
            "          return { expr := e, imp := some i }"
        ),
        "rationale": (
            "local-variable reshape of the general branch (the reference "
            "expression and the import body bound to typed locals, then the "
            "record built from them). Changes only executable shape while "
            "keeping every branch and both (C1) components; MUST verify, else "
            "SPEC-TOO-STRONG (over-fit to the single-expression spelling)."
        ),
    },

    # =====================================================================
    # ADMISSIBILITY — RE-AIMED onto the total carrier (was previously dropped as
    # "vacuous because the method declares no `require`"; that reason is wrong,
    # see the accounting footer). The nagini sibling proves the PRECONDITION
    # admits an F2P-shaped nested input. With no `require` to admit, the analogue
    # here is the OBLIGATION being unsatisfiable at exactly that input, which a
    # positive discharging the triple at the concrete point tests directly.
    # =====================================================================
    {
        "id": "admiss-obligation-satisfiable-at-nested",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _PROOF, _PROOF_ADMISS),
        "rationale": (
            "PRECOND-TOO-STRONG probe re-aimed for a total, precondition-free "
            "carrier. The impl region is byte-identical to the frozen one; the "
            "ONLY change is a `have hadm` prepended to the (elided) tactic body, "
            "so the frozen obligation is still closed verbatim afterwards and no "
            "clause is weakened or restated. `hadm` discharges the method's own "
            "Hoare triple BY EVALUATION at the F2P-shaped input (a general value "
            "nested inside another, whose full within-module location 'A.B' "
            "differs from its bare name 'B'): the guard ladder reduces there, "
            "`wp_pure` takes the weakest precondition of the resulting `pure`, and "
            "both conjuncts close by `decide` — (C0) `out = renderRef t` AND, "
            "independently, the ground post-image module + '.' + FULL location "
            "with the module's import. If the obligation were UNSATISFIABLE at "
            "this legitimate input — a post-image no computation can reach, the "
            "total-carrier analogue of a precondition no in-domain input meets — "
            "the `have` could not be discharged and this case would FAIL, which is "
            "PRECOND-TOO-STRONG. Load-bearing, not decorative: the same `have` "
            "with the pre-change post-image ('m.B'), with the import dropped, or "
            "with the separator dropped ('mA.B') each FAILS by semantic evaluation "
            "(`decide` proved the equation false), so what it asserts is pinned to "
            "the demanded rendering and not merely to the shape of the tactic."
        ),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # DISTINCT concrete input and the refinement argument for why its faithful
    # real counterpart would NOT resolve the failing test.
    # =====================================================================
    {
        "id": "weak-leaf-name",
        "kind": "uniqueness",
        "expect": "reject",
        # THE discriminating rival: in the general branch, key the reference on
        # the value's OWN bare name (without enclosing scope) instead of its FULL
        # within-module location. This is exactly the pre-change behaviour.
        "module": _general(
            "          return { expr := t.module ++ ['.'] ++ t.bare,\n"
            '                   imp := some ("import ".toList ++ t.module) }'
        ),
        "refinement": (
            "this is the pre-change behaviour: the general-branch reference is "
            "keyed by the value's own name WITHOUT any enclosing scope. On the "
            "F2P a value nested inside another (whose full within-module location "
            "'A.B' differs from its bare name 'B') then renders module + '.' + "
            "'B' — a reference to a non-existent top-level module attribute — "
            "instead of the demanded module + '.' + 'A.B' (the enclosing-then-"
            "inner path). The generated migration references a symbol that does "
            "not exist and the F2P assertion FAILS, so it would NOT resolve. This "
            "is the exact defect the fix corrects."
        ),
        "rationale": (
            "REJECT from (C1)/(C0): keys the general reference on `bare` instead "
            "of `qualified`, two INDEPENDENT inputs that differ precisely in the "
            "nested case. Refuted at the nested input (qualified='A.B' != "
            "bare='B'), the only witness that moves those two fields apart. If it "
            "verified => SPEC-TOO-WEAK (the nested-value regression would go "
            "unnoticed)."
        ),
        "witness": _witness(_tv("false", "false", "false", "m", "A.B", "B")),
    },
    {
        "id": "weak-drop-dot",
        "kind": "uniqueness",
        "expect": "reject",
        # Omit the dot separator: build module ++ qualified with nothing between.
        "module": _general(
            "          return { expr := t.module ++ t.qualified,\n"
            '                   imp := some ("import ".toList ++ t.module) }'
        ),
        "refinement": (
            "omitting the separator yields module concatenated directly to the "
            "location (e.g. 'mQ' rather than 'm.Q') — not a valid dotted "
            "reference and not equal to the string the tests expect, so the "
            "generated migration is malformed and it would NOT resolve."
        ),
        "rationale": (
            "REJECT from (C1)/(C0): drops the '.' between module and location, so "
            "the reference expression differs from module ++ ['.'] ++ qualified "
            "whenever module is non-empty. Refuted at module='p', qualified='Q' — "
            "a distinct input point from the leaf-name rival. If it verified => "
            "SPEC-TOO-WEAK."
        ),
        "witness": _witness(_tv("false", "false", "false", "p", "Q", "Q")),
    },
    {
        "id": "weak-no-import",
        "kind": "uniqueness",
        "expect": "reject",
        # Build the correct reference expression but emit NO import.
        "module": _general(
            "          return { expr := t.module ++ ['.'] ++ t.qualified,\n"
            "                   imp := none }"
        ),
        "refinement": (
            "a general value renders correctly but carries no accompanying "
            "import; the generated migration then references an unimported module "
            "and the tests, which demand the import line for such a value, FAIL — "
            "it would NOT resolve. Passes the reference-expression pin but fails "
            "the import pin."
        ),
        "rationale": (
            "REJECT from (C1)/(C0) on the IMPORT component: returns `imp := none` "
            "in the general branch, differing from `some (\"import \" ++ module)` "
            "at every general input. Refuted at module='q' — a distinct input "
            "point, and the only rival attacking the import facet independently. "
            "If it verified => SPEC-TOO-WEAK."
        ),
        "witness": _witness(_tv("false", "false", "false", "q", "R", "R")),
    },
    {
        "id": "weak-builtin-always-qualified",
        "kind": "uniqueness",
        "expect": "reject",
        # Corrupt the BUILT-IN branch: render the general dotted path + import
        # even for a built-in (which must be its bare name with no import).
        "module": _builtin(
            "          return { expr := t.module ++ ['.'] ++ t.qualified,\n"
            '                   imp := some ("import ".toList ++ t.module) }'
        ),
        "refinement": (
            "rendering the qualified dotted path + import for a built-in makes a "
            "type like `int` serialize as 'builtins.int' with an 'import "
            "builtins'; the built-in-serialization P2P tests expect the bare "
            "'int' with NO import, so those tests FAIL and it would NOT resolve."
        ),
        "rationale": (
            "REJECT from (C2)/(C0): correct on the general domain but wrong in "
            "the BUILT-IN branch — always renders the dotted path + import. "
            "Violates (C2) `out = { expr := bare, imp := none }` at every "
            "built-in input. Refuted at isBuiltin=true (bare='int'), the only "
            "witness that moves isBuiltin to true. If it verified => "
            "SPEC-TOO-WEAK (the built-in branch would be unpinned)."
        ),
        "witness": _witness(_tv("false", "false", "true", "b", "Q", "int")),
    },
    {
        "id": "weak-sentinel-branch",
        "kind": "uniqueness",
        "expect": "reject",
        # Corrupt the base-model sentinel branch: render the ABSENT-value
        # spelling in place of the base model type's canonical spelling.
        "module": _sentinel('      return { expr := "type(None)".toList, imp := none }'),
        "refinement": (
            "rendering the framework base model type with the absent-value "
            "spelling produces a migration referencing the wrong symbol; the P2P "
            "tests that expect the base model type's canonical spelling (and its "
            "omitted import) FAIL, so it would NOT resolve."
        ),
        "rationale": (
            "REJECT from the master clause (C0) `out = renderRef t`: the "
            "base-model sentinel branch returns the absent-value spelling "
            "instead of the base model type's canonical one, so `out` differs "
            "from `renderRef t` at this input. Refuted at isSentinelBase=true, "
            "the only witness that moves that flag to true. This branch is "
            "pinned ONLY by (C0) (no restated clause covers it). If it verified "
            "=> SPEC-TOO-WEAK."
        ),
        "witness": _witness(_tv("true", "false", "false", "m", "Q", "B")),
    },
    {
        "id": "weak-none-branch",
        "kind": "uniqueness",
        "expect": "reject",
        # Corrupt the absent-value sentinel branch: render the value's bare name
        # in place of the absent-value type's canonical spelling.
        "module": _none("        return { expr := t.bare, imp := none }"),
        "refinement": (
            "rendering the absent-value type as some bare name instead of its one "
            "canonical spelling produces a migration referencing a wrong / "
            "non-existent symbol; the P2P test that expects the canonical "
            "absent-value spelling FAILS, so it would NOT resolve."
        ),
        "rationale": (
            "REJECT from the master clause (C0) `out = renderRef t`: the "
            "absent-value sentinel branch returns the bare name instead of the "
            "type's canonical spelling, so `out` differs from `renderRef t` at "
            "this input. Refuted at isNoneType=true (bare='NoneType'), the only "
            "witness that moves that flag to true. If it verified => "
            "SPEC-TOO-WEAK."
        ),
        "witness": _witness(_tv("false", "true", "false", "m", "Q", "NoneType")),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The nagini sibling has 8 SPEC cases (2 soundness
# positives, 1 admissibility, 1 mandatory frame-mutation reject, 4 partial-domain
# rejects; AXIOM_TESTS empty) over `serialize_type(module, simple_name,
# qualified_name, module_is_builtin)` — a TWO-branch function (built-in vs not)
# with two output lists. THIS bundle models a carrier that is if anything RICHER:
# `typeReference (t : TypeValue)` dispatches over FOUR kinds (base-model sentinel
# -> absent-value sentinel -> built-in -> general) selected by three flags, and
# the master postcondition `out = renderRef t` pins every branch. The nagini
# `simple_name`/`qualified_name`/`module_is_builtin` inputs map to the `bare` /
# `qualified` / `isBuiltin` fields; the two sentinel branches are NEW modeled
# surface with no nagini counterpart (nagini folded them elsewhere).
#
#   nagini case                              -> here
#   ---------------------------------------------------------------------
#   pos-branch-reorder                       -> pos-render-direct        RE-SHAPED
#   pos-concat-reshape                       -> pos-general-locals       RE-SHAPED
#   admiss-f2p-nested-class                  -> admiss-obligation-satisfiable-at-nested  RE-AIMED
#   frame-mutation-write-qualified-name      -> (none)                   VACUOUS (ref. transparent)
#   partial-domain-leaf-name-prepatch-bug    -> weak-leaf-name           PORTED
#   partial-domain-drop-dot                  -> weak-drop-dot            PORTED
#   partial-domain-no-import                 -> weak-no-import           PORTED
#   partial-domain-builtin-always-qualified  -> weak-builtin-always-qualified  PORTED
#   (no nagini counterpart)                  -> weak-sentinel-branch     NEW (C0, sentinel)
#   (no nagini counterpart)                  -> weak-none-branch         NEW (C0, none-type)
#   AXIOM_TESTS (empty)                      -> (none)                   N/A
#
# PORTED (4 rejects): the four partial-domain rivals carry across intact — only
#   the carrier changes from two returned `List[int]` outputs to a `Rendered`
#   record. leaf-name (key on the bare name, the pre-patch bug), drop-dot (omit
#   the separator), no-import (drop the import), and builtin-always-qualified
#   (render the dotted path for a built-in) each keep their nagini refinement
#   argument (a migration referencing a wrong / unimported / non-existent symbol
#   fails the same test). Each now carries a machine-checked witness — the new
#   work with no nagini counterpart (nagini relied on Viper to discharge the
#   contract; a tactic-proof backend cannot infer wrongness from a build failure).
# RE-SHAPED (2 positives): pos-branch-reorder inverted a 2-way guard on the
#   single built-in bool — SAFE there, but a raw reorder of this four-branch
#   PRIORITY dispatch is NOT semantics-preserving when the flags overlap, so the
#   cheapest structurally-different correct impl is `return renderRef t` (the
#   grounded pure model, definitionally the ensures RHS). pos-concat-reshape
#   reassociated the general-branch concatenation into named locals; here that is
#   pos-general-locals (the reference expression and import body staged into
#   typed locals). Both verify under the frozen `loom_solve <;> simp_all
#   [renderRef]` (two real builds).
# RE-AIMED admissibility (1 positive): the nagini case self-calls to prove the
#   PRECONDITION admits an F2P-shaped nested input. This method declares no
#   `require`, so there is no precondition to admit — but "no precondition" does
#   NOT make the lane vacuous, and an earlier revision of this file wrongly
#   dropped it on that reason. PRECOND-TOO-STRONG is one of the three directions
#   this gate exists to test, and its analogue on a total carrier is the
#   OBLIGATION being unsatisfiable at exactly an F2P-shaped input. That is what
#   admiss-obligation-satisfiable-at-nested tests: it discharges the method's own
#   triple at the concrete nested point (qualified 'A.B' != bare 'B') by
#   evaluation, as a `have`, before closing the frozen obligation verbatim. It is
#   demonstrated load-bearing — the same `have` asserting the pre-change
#   post-image, or a dropped import, or a dropped separator, each FAILS by
#   semantic evaluation — so the lane is now covered rather than assumed empty.
# VACUOUS frame-mutation: the nagini mandatory probe writes to a read-only input
#   held at Acc(.,1/2). Lean/Velvet are referentially transparent — `t` is
#   immutable, no `mut` binder, no heap, no aliasing, no permission system — so
#   there is no read-only input to overwrite and no substitute probe. Per the
#   porting map this class is vacuous here; NOT fabricated.
# NEW (2 rejects, no nagini counterpart): this carrier models the base-model and
#   absent-value SENTINEL branches explicitly (nagini did not), each pinned by the
#   master clause (C0) only. weak-sentinel-branch and weak-none-branch attack them
#   (render the wrong canonical spelling), so (C0) is exercised on the branches
#   (C1)/(C2) do not restate. Both break a P2P test in their faithful form and so
#   would not resolve; both carry a machine-checked witness. Real modeled surface,
#   not fabricated wrongness.
#
# CLAUSE COVERAGE: (C0) attacked by every reject (and by both sentinel rivals
#   uniquely); (C1) attacked by weak-leaf-name / weak-drop-dot / weak-no-import
#   (expression AND import components); (C2) attacked by
#   weak-builtin-always-qualified. Both positives defend (C0) directly.
# BINDER COVERAGE: the one input binder `t` is varied across all six fields —
#   isSentinelBase, isNoneType, isBuiltin each moved to true by a distinct rival,
#   and module / qualified / bare each read by a distinct rival — over six
#   DISTINCT reject witness points (pts=6). The load-bearing nested case
#   (qualified != bare) is the leaf-name witness.
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job; this bundle declares no
# axiom (the dispatch is modeled deeply, not delegated to an oracle), so there is
# nothing to probe and the gate ignores AXIOM_TESTS regardless.
AXIOM_TESTS = []
