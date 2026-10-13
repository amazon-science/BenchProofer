"""properties.py — G-PBT falsification battery for django__django-14580 (lean).

NOT a Lean file; a manifest the G-PBT gate executes. Each SPEC case is a full
``Solution.lean`` variant that shares the FROZEN spec byte-for-byte (region
surgery: only text inside the ``-- impl-start`` / ``-- impl-end`` region — and,
for a case that legitimately re-proves, inside the ``-- proof-start`` /
``-- proof-end`` region — is changed, so ``markers.same_spec`` holds and the
single ``theorem correct_serializeType`` STATEMENT stays byte-identical).
``expect:"verify"`` passes iff (in scope AND the file elaborates with the
obligation closed, no ``sorry``/``admit``/``native_decide`` and no new
``axiom``/``theorem``); ``expect:"reject"`` passes iff (in scope AND it does NOT
verify AND the case's refutation ``witness`` holds of the rival while FAILING on
the frozen solution).

PORT NOTE. This ports the nagini falsification battery
(``../nagini/properties.py``) onto this backend's carrier. The nagini bundle
contracts ONE function over an ``int`` value-tag parameter (`value_tag`) whose
precondition pins it to one of TWO distinguished tags — the base-class reference
row and the no-import reference row — and validates each row against a GROUNDED
@Pure deep model (nagini's ``base_ref_*`` / ``other_ref_*`` constants). This Lean
bundle models the SAME single purely-functional core — serializing a type object
to a pair ``(source text, import statements)`` — but over a RICHER carrier: an
inductive ``TypeVal`` with FOUR arms, not two. The nagini value_tag ∈ {base,
other} corresponds here to ``TypeVal.baseModel`` / ``TypeVal.noneType``; the two
extra arms (``TypeVal.builtin name`` / ``TypeVal.other module qualname``) are the
fully-general fallback the nagini precondition excluded, and this Lean spec pins
them too. So every nagini case ports, and this carrier ADMITS two extra rivals
(one per extra arm) that the narrower nagini carrier could not express.

DEFENDED SURFACE (one modeled behavior; a single grounded clause over four arms).
``problem_spec_serializeType v result`` pins EXACTLY ``result = serializeSpec v``,
where ``serializeSpec`` is a GROUNDED @Pure table:

  * (A0 base)     ``.baseModel  → ("models.Model", ["from django.db import models"])``
    — THE FIX: the base-class reference carries EXACTLY the namespace-import
    statement, non-empty and equal to that exact line. (nagini E1.)
  * (A1 none)     ``.noneType   → ("type(None)", [])``
    — the no-import reference: its own text and an EMPTY import set. The
    anti-"fix-the-wrong-row" guard. (nagini E2.)
  * (A2 builtin)  ``.builtin n  → (n, [])``
    — a built-in type is referenced by its bare name, no import.
  * (A3 other)    ``.other m q  → (m ++ "." ++ q, ["import " ++ m])``
    — any other type is referenced module-qualified, importing its module.

The F2P ``test_serialize_type_model`` asserts serializing the base-class
reference yields ``("models.Model", {'from django.db import models'})``; A0 is
precisely that discriminator. The P2P ``test_serialize_type_none`` keeps the
no-import row honest (A1), so a wrong impl cannot "fix the wrong row".

BINDER STRUCTURE. The spec predicate has ONE input binder, ``v : TypeVal`` — but
it is a SUM type whose four arms are four independent top-level clauses of
``serializeSpec``. Varying the binder means exercising each arm. The reject
witnesses probe FOUR DISTINCT ``TypeVal`` inputs — ``.baseModel``, ``.noneType``,
``.builtin "int"``, ``.other "mymod" "MyClass"`` — so no arm of the carrier is
left unattacked and the binder is discriminated across its whole shape. Each arm
maps to a PAIR (source text, import statements), and both components of every arm
are separately falsified: the import component by rivals (1)-(7) and the text
component by the three audit-added rivals (8)-(10).

ADVERSARIAL READ of the nagini case classes on this carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS. The nagini sibling already records
    this class as structurally inapplicable (its sole input is an ``int`` VALUE
    with no heap permission — ``has_readonly_input=False``). On this
    referentially transparent carrier it is doubly vacuous: ``v`` is an immutable
    value, no ``mut`` input binder, no aliasing, no read-only cell to overwrite.
    No substitute probe is fabricated.

  * UNGROUNDED-ORACLE ECHO — VACUOUS. The nagini oracles are @Pure CONSTANT
    sequences (grounded); ``serializeSpec`` is the same here — a concrete Lean
    ``def`` returning literal strings, no opaque answer key. There is no wrong
    echo to build: an impl whose output equals ``serializeSpec v`` has done the
    real work (materialised the exact text + import line). In its place the
    battery carries honest cheapest-impl POSITIVE CONTROLS that must verify.

  * DIVERGENCE / NON-TERMINATION — NOTHING TO SHIP, but not because it is
    unwritable. AUDIT CORRECTION: the original port note claimed "a diverging
    impl cannot be written at all", which is false — ``partial def loopForever
    (v : TypeVal) : String × List String := loopForever v`` delegated from the
    impl region is admissible variant scope (checked: ``variant_problems`` clean)
    and elaborates. It is nonetheless not a shippable rival, for the reason that
    actually holds: it is REJECTED (build exit 1, ``Tactic 'rfl' failed`` on all
    four arms, because a ``partial def`` is irreducible so no arm computes), and
    no witness can be landed for it — the refutation ``¬ problem_spec ... `` at
    ``.baseModel`` fails with ``Tactic 'decide' failed ... because its Decidable
    instance`` (exit 1 on the RIVAL side, the half that must succeed), since the
    opaque ``partial`` term blocks kernel reduction in BOTH directions rather
    than deciding against the rival. So the rejection is a reducibility artifact,
    not attributable to the spec, and shipping it would be a ``witness-unproven``
    inconclusive. Recorded here rather than dropped silently. (The nagini sibling
    carries no ``diverge-*`` case, so nothing to port regardless.) This lean
    bundle is NOT a velvet ``partial`` bundle: it sets no ``loom.semantics``
    option, so the vacuous-divergence spec hole recorded in
    ``the corpus-wide termination-semantics finding`` does not apply to it either way.

  * PARTIAL-DOMAIN / VALUE — APPLIES, and is the whole reject lane. Every nagini
    ``weak-*`` rival is correct on part of the domain and wrong where the fix
    bites; each ports as an attack on one arm of ``serializeSpec``.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an impl (the frozen ``cases v <;> rfl`` is tuned to the frozen loop
form), so a rejection alone attributes nothing to the spec. Every
``expect="reject"`` case therefore carries a Lean snippet that states the spec
predicate at ONE concrete ``TypeVal`` and refutes it: ``unfold`` the three defs
(``problem_spec_serializeType`` / ``implementation_serializeType`` /
``serializeSpec``) and ``decide``. The carrier is fully COMPUTABLE (finite
strings + lists, ``DecidableEq``), so ``decide`` closes without conditioning on
any opaque term — every witness head binds NOTHING (the input is a ground
constructor literal), so there are no hypotheses whose joint satisfiability could
be in question. Each was checked with two real ``lake env lean`` builds: it HOLDS
of its rival (exit 0) and FAILS on the frozen solution (exit 1), so it
discriminates rather than asserting a tautology.

REFINEMENT (why a verifying rival would be a true verify-but-not-resolve break).
Each reject case's ``refinement`` argues that its faithful real counterpart is a
serializer that emits the wrong ``(text, import-set)`` for one type kind, so on
the reported inputs a generated migration either omits the import that makes the
bare ``models.Model`` reference resolve (raising ``NameError``) or emits a
spurious import for a type that needs none — and the added F2P / existing P2P
assertions pin the exact pair, so the faithful patch would NOT resolve.

AXIOM lane: EMPTY here. The bundle declares no ``opaque`` callee and consumes no
``axiom`` (the serialization is modeled deeply as ``serializeSpec``); the axiom
lane belongs to G-AX, and the nagini ``AXIOM_TESTS`` (one A-reference soundness
probe, run by G-AX not this gate) are dropped.
"""
from pathlib import Path

INSTANCE = "django__django-14580"
BACKEND = "lean"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- region anchors (each unique inside Solution.lean; verified at load) ----
# All lie ENTIRELY inside the impl region. Note that `serializeSpec` (the frozen
# @Pure table in the pure region) uses the pattern-match arm form
# `| .baseModel => ("models.Model", [...])`, WITHOUT the `TypeVal.` prefix, the
# tuple-list comma, and the `return`, so none of these anchors can match there —
# each is unique to the impl's special-case table / fallback arms.
_I_BASE_ROW = ('(TypeVal.baseModel, "models.Model", '
               '["from django.db import models"]),')
_I_NONE_ROW = '(TypeVal.noneType, "type(None)", []) ]'
_I_BUILTIN = '  | .builtin name => return (name, [])'
_I_OTHER = ('  | .other module qualname => return '
            '(module ++ "." ++ qualname, ["import " ++ module])')

# The whole frozen impl body (Id.run do table-scan + fallback match) — used by
# the direct-match positive to reshape the executable form entirely while keeping
# every returned value identical.
_I_WHOLE = (
    'def implementation_serializeType (v : TypeVal) : String × List String := Id.run do\n'
    '  let specialCases : List (TypeVal × String × List String) :=\n'
    '    [ (TypeVal.baseModel, "models.Model", ["from django.db import models"]),\n'
    '      (TypeVal.noneType, "type(None)", []) ]\n'
    '  for entry in specialCases do\n'
    '    let (case, str, imports) := entry\n'
    '    if sameType case v then\n'
    '      return (str, imports)\n'
    '  match v with\n'
    '  | .builtin name => return (name, [])\n'
    '  | .other module qualname => return (module ++ "." ++ qualname, ["import " ++ module])\n'
    '  | _ => return ("", [])')

# The frozen proof body (proof region) — used by the admissibility positive to
# prepend ground `have`s WITHOUT touching the theorem STATEMENT or the spec view.
_P_BODY = '  intro v\n  cases v <;> rfl'


# ---------------------------------------------------------------------------
# witness scaffold. State the spec predicate at one concrete `TypeVal` literal
# and refute it by computation. The carrier is fully decidable, so no
# conditioning on an opaque term is needed and the head binds nothing.
# ---------------------------------------------------------------------------
def _wit(v_lit: str) -> str:
    return (
        f"example : ¬ problem_spec_serializeType {v_lit}\n"
        f"    (implementation_serializeType {v_lit}) := by\n"
        "  unfold problem_spec_serializeType implementation_serializeType serializeSpec\n"
        "  decide\n")


# ---------------------------------------------------------------------------
# POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls that
# MUST verify, else SPEC-TOO-STRONG. Each keeps the `theorem correct_serializeType`
# statement byte-identical. (Both verified with a real `lake env lean` build.)
# ---------------------------------------------------------------------------

# DIRECT-MATCH positive: drop the table + linear scan entirely and branch on the
# constructor directly, materialising each arm's pair. Definitionally the same
# values, so the frozen proof (`cases v <;> rfl`) still closes for every arm — no
# proof authoring, no helper lemma, no assumption token. Ports nagini's
# pos-control-direct-branch (there: branch on the distinguished tag directly).
_POS_DIRECT = _swap(
    _BASE, _I_WHOLE,
    'def implementation_serializeType (v : TypeVal) : String × List String :=\n'
    '  match v with\n'
    '  | .baseModel => ("models.Model", ["from django.db import models"])\n'
    '  | .noneType => ("type(None)", [])\n'
    '  | .builtin name => (name, [])\n'
    '  | .other module qualname => (module ++ "." ++ qualname, ["import " ++ module])')

# REORDER positive: keep the table + scan, but list the no-import row BEFORE the
# base-class row. The scan matches by identity, so the row ORDER is irrelevant to
# the returned value — every arm is unchanged, the frozen proof still closes.
# Ports nagini's pos-control-reorder-columns (there: reorder the two materialised
# columns; here the column order is inlined, so the analogous structural reshape
# is the table ROW order, which the first-match scan is likewise robust to).
_POS_REORDER = _swap(
    _BASE,
    '    [ (TypeVal.baseModel, "models.Model", ["from django.db import models"]),\n'
    '      (TypeVal.noneType, "type(None)", []) ]',
    '    [ (TypeVal.noneType, "type(None)", []),\n'
    '      (TypeVal.baseModel, "models.Model", ["from django.db import models"]) ]')


# ---------------------------------------------------------------------------
# ADMISSIBILITY — the obligation is SATISFIABLE (non-vacuous) at the normal
# F2P-shaped inputs. Nagini's admiss-base-and-other self-calls serialize_type on
# BOTH distinguished tags; here the honest analogue discharges the spec predicate
# by evaluation at BOTH special-case values (`.baseModel` is the exact F2P input
# of test_serialize_type_model; `.noneType` is the P2P input) as ground `have`s,
# then closes the frozen obligation verbatim. Nothing is assumed: no new
# declaration, statement byte-identical, the `have`s are prepended to the existing
# tactic body. (Verified with a real build.)
# ---------------------------------------------------------------------------
_POS_ADMISS = _swap(
    _BASE, _P_BODY,
    "  have _base : problem_spec_serializeType TypeVal.baseModel\n"
    "      (implementation_serializeType TypeVal.baseModel) := by\n"
    "    unfold problem_spec_serializeType implementation_serializeType serializeSpec\n"
    "    rfl\n"
    "  have _none : problem_spec_serializeType TypeVal.noneType\n"
    "      (implementation_serializeType TypeVal.noneType) := by\n"
    "    unfold problem_spec_serializeType implementation_serializeType serializeSpec\n"
    "    rfl\n"
    "  intro v\n"
    "  cases v <;> rfl")


# ===========================================================================
# UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec that
# MUST be rejected. Each carries (a) the refinement argument that its faithful
# real patch would NOT resolve, and (b) a witness pinning the violation at one
# concrete input. (Every witness verified: HOLDS of its rival, FAILS on gold.)
# ===========================================================================

# (1) THE BUG-DELTA / pre-patch: base-class row carries an EMPTY import set.
_RIVAL_EMPTY = _swap(
    _BASE, _I_BASE_ROW, '(TypeVal.baseModel, "models.Model", []),')

# (2) WRONG import content (non-empty but not the namespace import).
_RIVAL_WRONG = _swap(
    _BASE, _I_BASE_ROW,
    '(TypeVal.baseModel, "models.Model", ["import models"]),')

# (3) TRUNCATED import: the final char of the import line is dropped.
_RIVAL_TRUNC = _swap(
    _BASE, _I_BASE_ROW,
    '(TypeVal.baseModel, "models.Model", ["from django.db import model"]),')

# (4) WRONG-ROW / no-import row returns the base row's pair (text + import).
_RIVAL_NONE_TEXT = _swap(
    _BASE, _I_NONE_ROW,
    '(TypeVal.noneType, "models.Model", ["from django.db import models"]) ]')

# (5) FIX-THE-WRONG-ROW: no-import row given a spurious namespace import.
_RIVAL_NONE_NONEMPTY = _swap(
    _BASE, _I_NONE_ROW,
    '(TypeVal.noneType, "type(None)", ["from django.db import models"]) ]')

# (6) BUILT-IN arm: emit a spurious import for a built-in type (should be none).
_RIVAL_BUILTIN = _swap(
    _BASE, _I_BUILTIN,
    '  | .builtin name => return (name, ["import " ++ name])')

# (7) OTHER arm: import the QUALNAME instead of the MODULE (wrong import line).
_RIVAL_OTHER = _swap(
    _BASE, _I_OTHER,
    '  | .other module qualname => return '
    '(module ++ "." ++ qualname, ["import " ++ qualname])')

# ---------------------------------------------------------------------------
# AUDIT ADDITION (three rivals). Every rival above (1)-(7) attacks the IMPORT
# component of its clause, except (4) which happens to move the text and the
# import together. So the TEXT component of A0 / A2 / A3 was never attacked on
# its own: a spec that pinned only `(result.2 = (serializeSpec v).2)` — imports
# only, text unconstrained — would have rejected all seven shipped rivals and
# been recorded SOUND. These three close that hole, one per unattacked clause,
# each holding the import component CORRECT so the text is the sole difference.
# ---------------------------------------------------------------------------

# (8) A0 TEXT: the base-class row's source text is module-qualified instead of
# the bare attribute reference. Import line left CORRECT.
_RIVAL_BASE_TEXT = _swap(
    _BASE, _I_BASE_ROW,
    '(TypeVal.baseModel, "django.db.models.Model", '
    '["from django.db import models"]),')

# (9) A2 TEXT: a built-in type is referenced through a module prefix instead of
# its bare name. Import list left CORRECT (empty).
_RIVAL_BUILTIN_TEXT = _swap(
    _BASE, _I_BUILTIN,
    '  | .builtin name => return ("builtins." ++ name, [])')

# (10) A3 TEXT: the module-qualified reference is assembled in the WRONG order
# (qualname.module). Import line left CORRECT (`import module`).
_RIVAL_OTHER_TEXT = _swap(
    _BASE, _I_OTHER,
    '  | .other module qualname => return '
    '(qualname ++ "." ++ module, ["import " ++ module])')


SPEC_TESTS = [
    # ---- positive controls / admissibility (must VERIFY) ----
    {
        "id": "pos-control-direct-match",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_DIRECT,
        "rationale": "honest cheapest CORRECT impl with a DIFFERENT shape: no table "
                     "and no linear scan — branch on the constructor directly and "
                     "materialise that arm's (text, imports) pair. Same value on "
                     "every input, so the single grounded clause `result = "
                     "serializeSpec v` holds for all four arms; the frozen proof "
                     "`cases v <;> rfl` still closes (statement byte-identical, no "
                     "new axiom/lemma). Must verify, else the postcondition is "
                     "over-fit to the gold table/scan shape => SPEC-TOO-STRONG. "
                     "Ports nagini's pos-control-direct-branch.",
    },
    {
        "id": "pos-control-reorder-rows",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_REORDER,
        "rationale": "structurally-different but CORRECT impl: the special-case "
                     "table lists the no-import row BEFORE the base-class row. The "
                     "scan matches by identity, so row order does not change any "
                     "returned value; every arm is unchanged and the frozen proof "
                     "still closes. Must verify, else the postcondition is over-fit "
                     "to the gold table ROW order => SPEC-TOO-STRONG. Ports nagini's "
                     "pos-control-reorder-columns (column order there; row order in "
                     "the first-match scan here).",
    },
    {
        "id": "admiss-base-and-none",
        "kind": "admissibility",
        "expect": "verify",
        "module": _POS_ADMISS,
        "rationale": "the obligation is discharged at BOTH special-case inputs (the "
                     "base-class reference is the exact F2P input of "
                     "test_serialize_type_model; the no-import reference is the P2P "
                     "input) by evaluation as ground `have`s, then the frozen "
                     "obligation is closed verbatim. Verifies (else the modeled "
                     "behavior would be unsatisfiable at exactly a normal F2P input "
                     "— the analogue of PRECOND-TOO-STRONG). Nothing assumed: no new "
                     "declaration, statement byte-identical, `have`s prepended to "
                     "the existing tactic body. Ports nagini's admiss-base-and-other.",
    },

    # ---- uniqueness rivals (must be REJECTED) ----
    {
        "id": "weak-empty-import-prepatch",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_EMPTY,
        "refinement": "this is the PRE-PATCH table: the base-class reference row "
                      "carries an EMPTY import list. The real serializer then "
                      "surfaces the empty set for that reference, so a generated "
                      "migration whose bases reference the rendered bare name emits "
                      "NO import for it and raises NameError at import time. The F2P "
                      "test_serialize_type_model asserts the import set is exactly "
                      "the single namespace-import statement — the faithful pre-patch "
                      "code FAILS it and does NOT resolve.",
        "rationale": "rejected by clause A0: `serializeSpec .baseModel` pins the "
                     "non-empty exact import line, but the rival's result carries an "
                     "empty import list, which cannot equal it. Exactly the G-DIFF "
                     "bug-delta. If it verified => SPEC-TOO-WEAK.",
        "witness": _wit("TypeVal.baseModel"),
    },
    {
        "id": "weak-wrong-import-content",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_WRONG,
        "refinement": "the base-class row carries a NON-EMPTY but WRONG import line "
                      "(a plausible-but-different import). Executing it does NOT "
                      "bring the bare reference name into scope, so the rendered "
                      "reference still raises NameError, and the F2P's exact-set "
                      "assertion FAILS. The faithful patch does NOT resolve.",
        "rationale": "rejected by A0: the clause pins the EXACT import line; a "
                     "non-empty but different string cannot equal it. Confirms A0 is "
                     "exact-content, not mere non-emptiness. Refuted at .baseModel "
                     "(same arm as the prepatch rival, but a distinct wrong value: "
                     "this one is non-empty, so a spec requiring only non-emptiness "
                     "would wrongly accept it). If it verified => SPEC-TOO-WEAK.",
        "witness": _wit("TypeVal.baseModel"),
    },
    {
        "id": "weak-truncated-import",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_TRUNC,
        "refinement": "the base-class row's import line drops its final character. "
                      "Executing that imports nothing under the intended name, so "
                      "the rendered reference still raises NameError and the F2P's "
                      "exact-set assertion FAILS. The faithful patch does NOT "
                      "resolve.",
        "rationale": "rejected by A0: a strict prefix of the exact import line != "
                     "the exact import line. A near-miss of the wrong-content rival "
                     "(both wrong at .baseModel, both non-empty) but a genuinely "
                     "distinct value, so it needs its own witness at .baseModel. If "
                     "it verified => SPEC-TOO-WEAK.",
        "witness": _wit("TypeVal.baseModel"),
    },
    {
        "id": "weak-none-returns-base-row",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_NONE_TEXT,
        "refinement": "the no-import reference row returns the base-class row's pair "
                      "(both its text AND its import) — a first-match scan that "
                      "surfaces the WRONG row for the no-import reference. The P2P "
                      "test_serialize_type_none asserts the no-import reference "
                      "serializes to its own text and an empty import set; returning "
                      "the base row FAILS it. The faithful patch does NOT resolve.",
        "rationale": "rejected by clause A1: `serializeSpec .noneType` pins the "
                     "no-import reference's own text and empty imports, but the rival "
                     "emits the base row's text and non-empty import. Ports nagini's "
                     "weak-always-return-row0. Refuted at .noneType. If it verified "
                     "=> SPEC-TOO-WEAK.",
        "witness": _wit("TypeVal.noneType"),
    },
    {
        "id": "weak-none-spurious-import",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_NONE_NONEMPTY,
        "refinement": "the no-import reference row is given the namespace-import "
                      "directive too, so the real serializer would surface a SPURIOUS "
                      "import for a reference that needs none. test_serialize_type_none "
                      "(P2P) asserts the no-import reference -> empty import set; a "
                      "non-empty set FAILS it (and regresses the 'imported only if "
                      "used' invariant). The faithful patch does NOT resolve.",
        "rationale": "rejected by A1's empty-imports component: the no-import row must "
                     "surface an empty import set. The anti-'fix the wrong row' guard "
                     "(dual to the empty-import prepatch attack). Ports nagini's "
                     "weak-other-row-nonempty. Refuted at .noneType (a DISTINCT "
                     "wrong-value from weak-none-returns-base-row: here the text is "
                     "correct and only the import set is wrong). If it verified => "
                     "SPEC-TOO-WEAK.",
        "witness": _wit("TypeVal.noneType"),
    },
    {
        "id": "weak-builtin-spurious-import",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_BUILTIN,
        "refinement": "a built-in type is referenced by its bare name and needs NO "
                      "import; this rival emits a spurious `import <name>` for it. "
                      "The real serializer would then write an unresolvable import "
                      "line into the migration for every built-in-typed value, so "
                      "the P2P serialization round-trips that exercise built-in "
                      "types FAIL. This arm has no counterpart in the nagini bundle "
                      "(its precondition excluded all but the two special rows); "
                      "this carrier models and defends it. The faithful patch does "
                      "NOT resolve.",
        "rationale": "rejected by clause A2: `serializeSpec (.builtin n)` pins "
                     "`(n, [])` (empty imports), but the rival emits a non-empty "
                     "import list. Refuted at `.builtin \"int\"` — the only witness "
                     "exercising the built-in arm of the carrier. If it verified => "
                     "SPEC-TOO-WEAK.",
        "witness": _wit('(TypeVal.builtin "int")'),
    },
    {
        "id": "weak-other-wrong-import",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_OTHER,
        "refinement": "a module-qualified type must import its MODULE (`import "
                      "<module>`); this rival imports the QUALNAME instead. The real "
                      "serializer would then write an import that does not bring the "
                      "referenced module into scope, so the rendered `module.qualname` "
                      "reference raises NameError and P2P round-trips over "
                      "module-qualified types FAIL. Like the built-in arm, this is a "
                      "fallback the narrower nagini carrier could not express; this "
                      "carrier defends it. The faithful patch does NOT resolve.",
        "rationale": "rejected by clause A3: `serializeSpec (.other m q)` pins the "
                     "import line `\"import \" ++ m`, but the rival emits `\"import \" "
                     "++ q`; whenever module != qualname these differ. Refuted at "
                     "`.other \"mymod\" \"MyClass\"` — the only witness exercising "
                     "the module-qualified arm. If it verified => SPEC-TOO-WEAK.",
        "witness": _wit('(TypeVal.other "mymod" "MyClass")'),
    },

    # ---- AUDIT ADDITION: the TEXT component of A0 / A2 / A3 ----
    {
        "id": "weak-base-text-qualified",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_BASE_TEXT,
        "refinement": "the base-class row emits a module-qualified source text "
                      "instead of the bare attribute reference, while carrying the "
                      "CORRECT import statement. A generated migration then renders "
                      "a reference that the surfaced import does not bring into "
                      "scope under that spelling, so it does not resolve. The F2P "
                      "test_serialize_type_model asserts the exact PAIR — text AND "
                      "import set — so the text half alone failing makes it FAIL. "
                      "The faithful patch does NOT resolve.",
        "rationale": "rejected by clause A0's TEXT component: `serializeSpec "
                     ".baseModel` pins the source text exactly, and the rival's "
                     "differs while its import list is correct. This is the only "
                     "rival isolating A0's text: rivals 1-3 all vary the IMPORT and "
                     "leave the text correct, so a spec pinning only the import "
                     "component would accept this one. Refuted at .baseModel. If it "
                     "verified => SPEC-TOO-WEAK.",
        "witness": _wit("TypeVal.baseModel"),
    },
    {
        "id": "weak-builtin-text-qualified",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_BUILTIN_TEXT,
        "refinement": "a built-in type must be referenced by its BARE name; this "
                      "rival prefixes it with a module path while correctly emitting "
                      "no import. The rendered reference then does not resolve in a "
                      "generated migration (nothing brings that prefix into scope), "
                      "so P2P serialization round-trips over built-in types FAIL. "
                      "The faithful patch does NOT resolve.",
        "rationale": "rejected by clause A2's TEXT component: `serializeSpec "
                     "(.builtin n)` pins the text to exactly `n`, but the rival "
                     "returns a prefixed string. Complements "
                     "weak-builtin-spurious-import, which varies A2's IMPORT and "
                     "leaves its text correct — together they pin both components of "
                     "the arm. Refuted at `.builtin \"int\"`. If it verified => "
                     "SPEC-TOO-WEAK.",
        "witness": _wit('(TypeVal.builtin "int")'),
    },
    {
        "id": "weak-other-text-reversed",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_OTHER_TEXT,
        "refinement": "a module-qualified type's reference must be assembled "
                      "module-then-qualname; this rival reverses the two components "
                      "while emitting the CORRECT import. The migration then renders "
                      "a reference that does not name the imported module, so it "
                      "does not resolve and P2P round-trips over module-qualified "
                      "types FAIL. The faithful patch does NOT resolve.",
        "rationale": "rejected by clause A3's TEXT component: `serializeSpec (.other "
                     "m q)` pins the text `m ++ \".\" ++ q`, but the rival emits `q "
                     "++ \".\" ++ m`; whenever module != qualname these differ. "
                     "Complements weak-other-wrong-import, which varies A3's IMPORT "
                     "and leaves its text correct. Refuted at `.other \"mymod\" "
                     "\"MyClass\"`. If it verified => SPEC-TOO-WEAK.",
        "witness": _wit('(TypeVal.other "mymod" "MyClass")'),
    },
]

# ---------------------------------------------------------------------------
# Nagini -> lean accounting. The sibling battery has 6 SPEC cases (2 soundness
# positives, 1 admissibility, 3 uniqueness rivals + 2 more = actually 3 positives
# + 5 rivals) plus one AXIOM-lane probe. This bundle models the SAME single
# purely-functional core (serialize a type to text + imports) over a RICHER
# four-arm carrier, re-expresses every sibling case, and ADDS two rivals for the
# two carrier arms the narrower nagini precondition excluded.
#
#   sibling case                    -> here
#   -----------------------------------------------------------------------
#   pos-control-reorder-columns     -> pos-control-reorder-rows      RE-EXPRESSED
#   pos-control-direct-branch       -> pos-control-direct-match      PORTED
#   admiss-base-and-other           -> admiss-base-and-none          PORTED
#   weak-empty-directive-prepatch   -> weak-empty-import-prepatch    PORTED (A0)
#   weak-wrong-directive-content    -> weak-wrong-import-content     PORTED (A0)
#   weak-truncated-directive        -> weak-truncated-import         PORTED (A0)
#   weak-always-return-row0         -> weak-none-returns-base-row    PORTED (A1)
#   weak-other-row-nonempty         -> weak-none-spurious-import     PORTED (A1)
#   (none)                          -> weak-builtin-spurious-import  ADDED  (A2)
#   (none)                          -> weak-other-wrong-import       ADDED  (A3)
#   (none)                          -> weak-base-text-qualified      AUDIT  (A0 text)
#   (none)                          -> weak-builtin-text-qualified   AUDIT  (A2 text)
#   (none)                          -> weak-other-text-reversed      AUDIT  (A3 text)
#   AXIOM_TESTS (1, G-AX)           -> (none)                        DROPPED
#
# RE-EXPRESSED (pos-control-reorder-rows): the nagini positive materialises the
#   matched row's two COLUMNS in reversed order (import column before text
#   column). This carrier inlines the column placement into a single returned
#   tuple, so there is no column order to reverse; the analogous
#   structurally-different-but-correct reshape reverses the two TABLE ROWS, which
#   the first-match identity scan is equally robust to. Verified with a real build.
# ADDED (weak-builtin-spurious-import, weak-other-wrong-import): the nagini
#   contract's precondition pins value_tag to one of the two special rows, so its
#   carrier has only those two rows and no rival can attack a general fallback.
#   This Lean carrier models the full `hasattr(self.value, "__module__")` fallback
#   as two extra `TypeVal` arms (`.builtin` / `.other`), which are load-bearing
#   top-level clauses of `serializeSpec` (A2/A3). The coverage requirement — every
#   independent clause attacked, every arm of the binder varied — is met by adding
#   one rival per extra arm. These are NOT fabricated for an unmodeled behavior:
#   they attack real, defended clauses of the SAME modeled spec that the narrower
#   nagini carrier simply could not reach.
# VACUOUS (frame/permission mutation): the nagini sibling already records this as
#   structurally inapplicable (has_readonly_input=False; the sole input is an int
#   VALUE). On this referentially transparent carrier it is doubly vacuous. No
#   substitute probe fabricated.
# VACUOUS (divergence/non-termination): the nagini sibling carries no diverge-*
#   case, and on lean `implementation_serializeType` is a total `def` so a
#   diverging impl cannot be written at all. Nothing to port.
# VACUOUS (ungrounded-oracle echo): `serializeSpec` is a grounded @Pure table of
#   literal strings — no opaque answer key to echo. Replaced by the positive
#   controls.
#
# AUDIT ADDITION (weak-base-text-qualified, weak-builtin-text-qualified,
#   weak-other-text-reversed): an independent audit found that rivals (1)-(7) all
#   attack the IMPORT component of their clause — the sole exception, (4), moves
#   text and import together, so its rejection is already explained by the import
#   half. Consequence: the TEXT component of A0, A2 and A3 was pinned by the spec
#   but never falsified by the battery, so a hypothetical spec constraining only
#   `result.2` would have rejected all seven and still recorded SOUND. Each added
#   rival changes ONLY the text of one clause and keeps that clause's import
#   component correct, so its rejection is attributable to the text component
#   alone. All three were checked with real builds: module rejected (exit 1),
#   witness holds of the rival (exit 0) and fails on gold by SEMANTIC refutation
#   (exit 1, `Tactic 'decide' proved that the proposition ... is false` — the
#   kernel evaluated and found gold satisfies the spec at that input).
#
# POINT SPREAD. The ten reject witnesses probe FOUR DISTINCT input points
# (pts=4), one per arm of the `TypeVal` carrier, and now BOTH components (text,
# imports) of every arm:
#   TypeVal.baseModel                 weak-empty-import-prepatch     A0
#   TypeVal.baseModel                 weak-wrong-import-content      A0
#   TypeVal.baseModel                 weak-truncated-import          A0
#   TypeVal.noneType                  weak-none-returns-base-row     A1
#   TypeVal.noneType                  weak-none-spurious-import      A1
#   (TypeVal.builtin "int")           weak-builtin-spurious-import   A2
#   (TypeVal.other "mymod" "MyClass") weak-other-wrong-import        A3
#   TypeVal.baseModel                 weak-base-text-qualified       A0 text
#   (TypeVal.builtin "int")           weak-builtin-text-qualified    A2 text
#   (TypeVal.other "mymod" "MyClass") weak-other-text-reversed       A3 text
#   The A0 rivals and the two A1 rivals share an input ARM but each carries
#   its OWN witness pinning its OWN distinct wrong value (empty vs. wrong-content
#   vs. truncated import; wrong-text-and-import vs. correct-text-spurious-import),
#   so no rival rides another's discriminator. All four arms of the sole binder
#   `v : TypeVal` are exercised, so no arm of the carrier is left unattacked.
#
# AXIOM_TESTS: dropped. The nagini bundle's single axiom-soundness probe is
# G-AX's job; this bundle declares no axiom (the serialization is modeled deeply
# as `serializeSpec`), so there is nothing to probe and the gate ignores
# AXIOM_TESTS regardless.
AXIOM_TESTS = []
