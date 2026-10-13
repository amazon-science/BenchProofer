# properties.py — G-PBT falsification battery for django__django-17087 (lean lane).
# PORTED from the nagini sibling's battery: the adversarial ARGUMENTS are carried
# over, the mechanics re-expressed against this backend's carrier. Each SPEC case is
# a FULL Solution.lean variant that shares the FROZEN spec byte-for-byte (only the
# impl region — and, where a positive reproves, the proof body — is edited), checked
# by variant_scope + the Lean verifier. Every expect="reject" case carries a
# refutation `witness`: a self-contained snippet that ELABORATES against the rival
# and FAILS on the frozen solution, so the rejection is attributable to the spec and
# not to a tactic script that merely stopped matching a reshaped impl.
#
# Defended surface (read from Solution.lean / mapping.md / instance.json):
#   classMethodRef : BoundClassMethod → DottedRef
#   A class-bound method is described by four char-list inputs: the defining
#   `module`, the owner's bare innermost name `ownerName`, the owner's
#   FULLY-QUALIFIED dotted name `ownerQualname` (== ownerName for a top-level
#   owner, strictly longer for an owner nested inside another class), and the
#   method's own `methodName`. The single postcondition
#   `problem_spec_classMethodRef` pins BOTH result components to the inputs:
#     (C1) TEXT: result.text is the dotted path
#          `module ++ "." ++ ownerQualname ++ "." ++ methodName`, qualified by the
#          owner's FULLY-qualified name. This is the DISCRIMINATING clause: it uses
#          `ownerQualname`, NOT `ownerName` — and note `ownerName` is a spec binder
#          that never appears in the postcondition, so a rival that keys the text on
#          `ownerName` agrees with gold on every top-level owner and diverges only on
#          a nested one (the F2P shape).
#     (C2) IMPORTS: result.imports is exactly the singleton `[importFor module]`
#          == `["import " ++ module]`. A rival that renders the right text but the
#          wrong import list fails C2.
#   importFor is a total, transparent fold over the input (no opaque callee, no
#   answer-key), so witnesses need no conditioning on the carrier — `decide` reduces
#   the whole predicate at any literal input after `unfold`.
#
# CARRIER NOTE / relation to the nagini sibling: nagini modeled the same rendering
# over PSeq[int] code-point lists with two @Pure postcondition clauses (member_path
# and import_line). Its four uniqueness rivals port ONE-TO-ONE onto this carrier:
#   nagini _WRONG_SIMPLE  -> weak-owner-bare-name  (attacks C1 via ownerName)
#   nagini _WRONG_IMPORT  -> weak-drop-import      (attacks C2)
#   nagini _PARTIAL_NODOT -> weak-missing-dot      (attacks C1: separator dropped)
#   nagini _PARTIAL_EXTRA -> weak-trailing-dot     (attacks C1: spurious suffix)
# Its two positive controls (direct-concat reorder; inner-to-outer tail build) port
# onto the two soundness cases below (statement reorder; pure record literal). Every
# reject witness probes a DISTINCT (module, ownerName, ownerQualname, methodName)
# point so both spec binders that appear in the postcondition (module,
# ownerQualname, methodName) are varied by the rivals, and the bare-name binder is
# exercised where it must differ from the qualname (the nested-owner shape).
#
# LANES THAT DO NOT PORT:
#   * FRAME-MUTATION (nagini's MANDATORY `_FRAME_MUT`: all four inputs were
#     Acc(list_pred(x),1/2) read-only and the rival wrote back into `module`).
#     Lean is referentially transparent — no aliasing, no fractional permission —
#     so a "store into a read-only input" rival is not expressible and the whole
#     lane is VACUOUS here. See 'assessment'.
#   * DIVERGENCE / NON-TERMINATION — KNOWN CARRIER LIMIT, measured, not assumed.
#     The nagini battery carries none. On this carrier the obligation is over a
#     Lean `def`, and three shapes were BUILT to check whether a diverging rival
#     is landable at all:
#       (a) `def f m := ... f m` (self-call, no decreasing measure) — the file
#           fails at the DEFINITION with "fail to show termination / no parameters
#           suitable for structural recursion", and the witness against it then
#           fails with "Tactic `unfold` failed to unfold" — i.e. the rival never
#           exists as a term, so the witness discriminates nothing;
#       (b) `partial def f m := ... f m` — fails earlier still: "failed to compile
#           'partial' definition ... could not prove that the type
#           BoundClassMethod → DottedRef is nonempty";
#       (c) (b) plus an `instance : Inhabited DottedRef` in the impl region, which
#           makes the `partial def` DECLARABLE (scope-clean) — but `partial` is
#           opaque to the kernel, so both the variant and its witness fail with
#           "Tactic `unfold` failed to unfold `implementation_classMethodRef`".
#     So a diverging impl is either unbuildable or irreducible, and in the
#     irreducible case gold's exit code carries no information about any claim.
#     This is a KNOWN HOLE in the reject lane (the spec cannot refute a diverging
#     impl here), NOT a vacuous class — recorded as a hole because that says the
#     spec is incomplete rather than that the battery is.
#     `Solution.lean` sets no `loom.semantics.termination` (vanilla Lean 4 +
#     Mathlib, no Velvet), so the "total"-semantics disposition does not apply.
#   * AXIOM_TESTS (nagini's `aref-render-soundness`). The axiom lane is G-AX's job;
#     this gate ignores it. importFor / the dotted join are modeled DEEPLY over
#     transparent carriers, so there is no consumed axiom here anyway.
from pathlib import Path

INSTANCE = "django__django-17087"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# --- anchors -----------------------------------------------------------------------
# The full frozen impl body, lying ENTIRELY inside impl-start/impl-end and unique in
# the file. Every rival (and the reorder positive) swap THIS block.
_IMPL = (
    "def implementation_classMethodRef (m : BoundClassMethod) : DottedRef := Id.run do\n"
    "  let module := m.module\n"
    "  let text := module ++ \".\".toList ++ m.ownerQualname ++ \".\".toList ++ m.methodName\n"
    "  return { text := text, imports := [importFor module] }"
)
assert _BASE.count(_IMPL) == 1, "impl anchor drifted from expected text"

# The frozen proof body (tactic lines inside proof-start/proof-end). Swapped only by
# the pure-record positive, whose different impl shape needs an (equally cheap,
# honest) reproof of the byte-identical theorem statement.
_PROOF = (
    "  intro m\n"
    "  unfold problem_spec_classMethodRef implementation_classMethodRef\n"
    "  refine ⟨rfl, rfl⟩"
)
assert _BASE.count(_PROOF) == 1, "proof anchor drifted from expected text"


# ===========================================================================
# POSITIVE CONTROLS (soundness) — must VERIFY (else SPEC-TOO-STRONG).
# ===========================================================================

# pos-reorder-imports-first: structurally-DIFFERENT but behaviourally identical.
# The import component is bound to a local BEFORE the text (statement reorder,
# mirroring nagini's "build import first" positive), and the text is one composite
# concatenation. Output equals the frozen impl's on every input. The theorem
# statement is byte-identical AND the frozen proof body still closes (the extra
# `let` is definitionally transparent). No reproof, no new axiom/lemma/sorry. If it
# FAILS => SPEC-TOO-STRONG (postcondition over-fit to one syntactic impl shape).
_POS_REORDER = _swap(
    _BASE,
    _IMPL,
    "def implementation_classMethodRef (m : BoundClassMethod) : DottedRef := Id.run do\n"
    "  let imports := [importFor m.module]\n"
    "  let text := m.module ++ \".\".toList ++ m.ownerQualname ++ \".\".toList ++ m.methodName\n"
    "  return { text := text, imports := imports }",
)

# pos-pure-record: a structurally different CORRECT impl written as a pure record
# literal (no `Id.run do` monad, no `let`, no early return), directly building the
# DottedRef — the analogue of nagini's inner-to-outer tail build (a different
# executable shape, same pinned value). The theorem STATEMENT is byte-identical; its
# proof is reproven honestly (`exact ⟨rfl, rfl⟩`) inside proof-start/proof-end — no
# new axiom/lemma/sorry, just the cheapest tactic for the new shape. If it FAILS =>
# SPEC-TOO-STRONG (the postcondition is bound to the monadic impl shape).
_POS_PURE = _swap(
    _swap(
        _BASE,
        _IMPL,
        "def implementation_classMethodRef (m : BoundClassMethod) : DottedRef :=\n"
        "  { text := m.module ++ \".\".toList ++ m.ownerQualname ++ \".\".toList ++ m.methodName,\n"
        "    imports := [importFor m.module] }",
    ),
    _PROOF,
    "  intro m\n"
    "  unfold problem_spec_classMethodRef implementation_classMethodRef\n"
    "  exact ⟨rfl, rfl⟩",
)

# adm-nested-owner-satisfiable: the ADMISSIBILITY lane. The frozen obligation
# carries no precondition hypothesis, so PRECOND-TOO-STRONG cannot arrive as an
# unprovable `Requires`; on a total carrier the analogue is the obligation being
# UNSATISFIABLE at an F2P-shaped concrete input — a spec that quantifies over all
# inputs but is contradictory at the one that matters would still let every rival
# be "rejected" while pinning nothing real. So this positive discharges the
# postcondition at exactly the discriminating shape (an owner nested inside
# another owner, ownerQualname strictly extending ownerName) BY KERNEL EVALUATION
# (`decide`), as a `have`, BEFORE closing the frozen obligation verbatim. The impl
# is the frozen one untouched and the theorem statement is byte-identical; the
# only edit is the added `have` ahead of the unchanged frozen tactic lines. If the
# `have` FAILED, the spec would be unsatisfiable at the F2P shape => the lane's
# finding. `clear` drops it so the frozen closing script runs in an unchanged
# context and the positive cannot pass BECAUSE of the added hypothesis.
_ADM_REC = (
    '{ module := "app.models".toList, ownerName := "Inner".toList, '
    'ownerQualname := "Outer.Inner".toList, methodName := "make".toList }'
)
_ADM_NESTED = _swap(
    _BASE,
    _PROOF,
    "  have admissible_at_nested_owner :\n"
    "      problem_spec_classMethodRef\n"
    f"        {_ADM_REC}\n"
    f"        (implementation_classMethodRef {_ADM_REC}) := by\n"
    "    unfold problem_spec_classMethodRef implementation_classMethodRef importFor\n"
    "    decide\n"
    "  clear admissible_at_nested_owner\n" + _PROOF,
)


# ===========================================================================
# UNIQUENESS RIVALS — must be REJECTED (else SPEC-TOO-WEAK). Each shares the
# frozen spec exactly and edits only the impl region; the frozen proof body is left
# in place (it will not close for the reshaped impl, but the gate reads the witness —
# checked in a file with the obligation removed — not the rival's own build).
# ===========================================================================

# weak-owner-bare-name: THE prepatch bug in carrier terms — keys the text on the
# owner's BARE name (`ownerName`) instead of its FULLY-qualified name
# (`ownerQualname`). On a top-level owner the two coincide, so this agrees with gold
# there; on an owner nested inside another class they differ, and the rendered
# reference is wrong. `ownerName` never appears in the frozen postcondition, so this
# rival is refutable only at a nested-owner input.
_RIV_BARE = _swap(
    _BASE,
    _IMPL,
    "def implementation_classMethodRef (m : BoundClassMethod) : DottedRef := Id.run do\n"
    "  let module := m.module\n"
    "  let text := module ++ \".\".toList ++ m.ownerName ++ \".\".toList ++ m.methodName\n"
    "  return { text := text, imports := [importFor module] }",
)

# weak-drop-import: renders the correct text but returns the bare module as the
# single import rather than `importFor module` == `"import " ++ module`. Attacks
# clause C2 (the import payload).
_RIV_IMPORT = _swap(
    _BASE,
    _IMPL,
    "def implementation_classMethodRef (m : BoundClassMethod) : DottedRef := Id.run do\n"
    "  let module := m.module\n"
    "  let text := module ++ \".\".toList ++ m.ownerQualname ++ \".\".toList ++ m.methodName\n"
    "  return { text := text, imports := [module] }",
)

# weak-missing-dot: correct EXCEPT it drops the separator between the qualified name
# and the method name, gluing them together. Diverges from the spec text on every
# input whose methodName is non-empty (the whole tested domain). Attacks clause C1.
_RIV_NODOT = _swap(
    _BASE,
    _IMPL,
    "def implementation_classMethodRef (m : BoundClassMethod) : DottedRef := Id.run do\n"
    "  let module := m.module\n"
    "  let text := module ++ \".\".toList ++ m.ownerQualname ++ m.methodName\n"
    "  return { text := text, imports := [importFor module] }",
)

# weak-trailing-dot: uses the qualified name normally but appends a spurious trailing
# separator to the text. Right on the prefix, wrong on the suffix; pins the
# "exact join, no extra glyphs" guarantee. Attacks clause C1.
_RIV_TRAIL = _swap(
    _BASE,
    _IMPL,
    "def implementation_classMethodRef (m : BoundClassMethod) : DottedRef := Id.run do\n"
    "  let module := m.module\n"
    "  let text := module ++ \".\".toList ++ m.ownerQualname ++ \".\".toList ++ m.methodName ++ \".\".toList\n"
    "  return { text := text, imports := [importFor module] }",
)


# weak-swap-order: emits the three components in the WRONG ORDER — the owner's
# qualified name first and the defining module second — so the rendered reference
# is a permutation of the right glyphs rather than the pinned join. Attacks C1 at a
# point the four ported rivals leave unattacked: each of those keeps `module` in
# head position, so none of them pins the ORDER of the joined components (a rival
# could permute them and still contain every substring the ported rivals check).
_RIV_SWAP = _swap(
    _BASE,
    _IMPL,
    "def implementation_classMethodRef (m : BoundClassMethod) : DottedRef := Id.run do\n"
    "  let module := m.module\n"
    "  let text := m.ownerQualname ++ \".\".toList ++ module ++ \".\".toList ++ m.methodName\n"
    "  return { text := text, imports := [importFor module] }",
)

# weak-empty-imports: renders the correct text but emits NO import at all. Attacks
# C2 from the other side than weak-drop-import: that rival emits a singleton with
# the wrong payload, so it pins the payload but not the LENGTH — an impl returning
# the empty list has no wrong payload to compare and is refuted only because the
# spec fixes the list to exactly one element.
_RIV_NOIMPORT = _swap(
    _BASE,
    _IMPL,
    "def implementation_classMethodRef (m : BoundClassMethod) : DottedRef := Id.run do\n"
    "  let module := m.module\n"
    "  let text := module ++ \".\".toList ++ m.ownerQualname ++ \".\".toList ++ m.methodName\n"
    "  return { text := text, imports := [] }",
)


def _wit(m, on, oq, me, note):
    """A refutation witness: `¬ problem_spec … (implementation …)` at a concrete
    literal BoundClassMethod. `unfold` exposes the record and `decide` reduces the
    fully-transparent predicate (the dotted join + importFor over char lists) to a
    decidable disequality. Elaborates against a rival that diverges from the spec at
    this point, and FAILS on gold (which satisfies the spec at every input) — SEEN to
    discriminate both ways with real builds. No head binders, so no conditioning and
    nothing for the consistency probe to reject."""
    rec = (f"{{ module := \"{m}\".toList, ownerName := \"{on}\".toList,\n"
           f"      ownerQualname := \"{oq}\".toList, methodName := \"{me}\".toList }}")
    rec2 = (f"{{ module := \"{m}\".toList, ownerName := \"{on}\".toList,\n"
            f"        ownerQualname := \"{oq}\".toList, methodName := \"{me}\".toList }}")
    return (
        f"-- {note}\n"
        f"example : ¬ problem_spec_classMethodRef\n"
        f"    {rec}\n"
        f"    (implementation_classMethodRef\n"
        f"      {rec2}) := by\n"
        f"  unfold problem_spec_classMethodRef implementation_classMethodRef importFor\n"
        f"  decide"
    )


SPEC_TESTS = [
    # ---- positive controls (must VERIFY) ----
    {
        "id": "pos-reorder-imports-first",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_REORDER,
        "rationale": (
            "structurally-different but CORRECT impl: the import component is bound to a "
            "local BEFORE the text (statement reorder, matching the nagini 'build import "
            "first' positive) and the text is one composite concatenation, so the output "
            "equals the frozen impl's on every input. The theorem statement is byte-identical "
            "and the FROZEN proof body still closes (the extra let is definitionally "
            "transparent) — a faithful restructure with no reproof and no new "
            "axiom/lemma/sorry. If it FAILS => SPEC-TOO-STRONG (postcondition over-fit to one "
            "syntactic impl shape). NOTE, measured rather than claimed: this reshape is "
            "definitionally CLOSE to the frozen impl (the frozen `rfl`-based body still "
            "closes it), so on its own it is a WEAK positive — it shows the spec is not "
            "over-fit to the frozen statement ORDER, not that it tolerates a genuinely "
            "different term. The load-bearing soundness evidence is pos-pure-record (which "
            "needs its own tactic) plus the re-association reshape recorded in 'assessment', "
            "whose text is NOT defeq to the frozen chain and which the spec still accepts."
        ),
    },
    {
        "id": "pos-pure-record",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_PURE,
        "rationale": (
            "a structurally different CORRECT impl written as a pure record literal (no "
            "`Id.run do`, no let, no early return), directly building the DottedRef — the "
            "analogue of nagini's inner-to-outer tail build. Semantics identical on every "
            "input. The theorem STATEMENT is byte-identical; its proof is reproven honestly "
            "with `exact ⟨rfl, rfl⟩` — no new axiom/lemma/sorry, just the cheapest "
            "tactic for the new shape. If it FAILS => SPEC-TOO-STRONG (the postcondition is "
            "bound to the monadic impl shape rather than the behaviour)."
        ),
    },

    {
        "id": "adm-nested-owner-satisfiable",
        "kind": "admissibility",
        "expect": "verify",
        "module": _ADM_NESTED,
        "rationale": (
            "the ADMISSIBILITY lane, in the form the analogue takes on a TOTAL carrier. "
            "The frozen obligation binds no precondition, so PRECOND-TOO-STRONG cannot "
            "arrive as an unprovable Requires (that is the nagini shape); the total-carrier "
            "analogue is the obligation being UNSATISFIABLE at an F2P-shaped concrete input, "
            "which this case tests directly: it discharges the postcondition at a NESTED-owner "
            "record (ownerQualname 'Outer.Inner' strictly extends ownerName 'Inner' — the "
            "shape the failing test pins) by KERNEL EVALUATION as a `have`, before closing the "
            "frozen obligation verbatim. The impl region is the frozen one untouched and the "
            "theorem statement is byte-identical, so nothing but the added evaluation is being "
            "asserted; the `have` is `clear`ed so the frozen closing script runs in an "
            "unchanged context and cannot pass BECAUSE of it. If the `have` FAILED => the spec "
            "is contradictory at exactly the input that matters (PRECOND-TOO-STRONG's "
            "total-carrier face) and every rival's 'rejection' would attest to nothing."
        ),
    },

    # ---- uniqueness rivals (must be REJECTED) ----
    {
        "id": "weak-owner-bare-name",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_BARE,
        "refinement": (
            "this IS the pre-patch behaviour: keying the rendered reference on the owner's "
            "BARE innermost name instead of its fully-qualified dotted name. On a top-level "
            "owner the two coincide, so it resolves correctly there; on an owner nested inside "
            "another class they differ, and the reference points at the wrong (unresolvable) "
            "location. The F2P test pins exactly a nested-owner method and asserts the "
            "fully-qualified reference, so a faithful patch of this shape does NOT resolve — a "
            "true verify-does-not-imply-resolve break if it verified."
        ),
        "rationale": (
            "REJECTED by clause C1 (text). The spec pins result.text to the ownerQUALNAME "
            "join; this rival uses ownerName, which never appears in the postcondition. "
            "Witness probes the NESTED-owner sub-domain (ownerName != ownerQualname), the only "
            "place the two differ — a top-level witness would not discriminate. If it VERIFIES "
            "=> SPEC-TOO-WEAK (the text is not actually pinned to the qualified name)."
        ),
        # nested owner: ownerName "B" != ownerQualname "A.B" -> gold renders
        # "m.A.B.f", rival renders "m.B.f"; they differ.
        "witness": _wit("m", "B", "A.B", "f",
                        "nested owner (ownerName != ownerQualname): gold uses the qualified "
                        "name, rival uses the bare name"),
    },
    {
        "id": "weak-drop-import",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_IMPORT,
        "refinement": (
            "returning the bare module as the import instead of `\"import \" ++ module` yields "
            "an import entry that is not a valid import statement; the F2P assertion compares "
            "the emitted import set exactly, so a faithful patch of this shape fails the test. "
            "Does NOT resolve — the import line is part of the contract."
        ),
        "rationale": (
            "REJECTED by clause C2 (imports). The spec pins result.imports to "
            "`[importFor module]` == `[\"import \" ++ module]`; this rival emits `[module]`, "
            "dropping the literal prefix. Witness varies the MODULE binder at a top-level "
            "owner (so the text clause holds for both and only C2 separates them). If it "
            "VERIFIES => SPEC-TOO-WEAK (the import payload is unpinned)."
        ),
        # top-level owner (ownerName == ownerQualname == "Q") so C1 holds for both;
        # gold import "import io", rival import "io" -> differ.
        "witness": _wit("io", "Q", "Q", "g",
                        "top-level owner, import payload only: gold prefixes \"import \", "
                        "rival drops it"),
    },
    {
        "id": "weak-missing-dot",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_NODOT,
        "refinement": (
            "dropping the separator between the qualified name and the method glues them "
            "into a single token (`...P.Cmm`), not a resolvable dotted path — different from "
            "the expected string on every input whose method name is non-empty (the entire "
            "tested domain). A faithful patch of this shape fails the F2P exact-equality "
            "assertion. Does NOT resolve."
        ),
        "rationale": (
            "REJECTED by clause C1 (text). The spec places a separator between ownerQualname "
            "and methodName; this rival omits it. Witness varies module/owner/method to a "
            "fresh point with a non-empty methodName (the whole tested domain). If it VERIFIES "
            "=> SPEC-TOO-WEAK (the separator is not enforced)."
        ),
        # nested owner too; gold "mod.P.C.mm", rival "mod.P.Cmm" -> differ.
        "witness": _wit("mod", "C", "P.C", "mm",
                        "non-empty method name: gold separates it from the owner, rival "
                        "glues them"),
    },
    {
        "id": "weak-trailing-dot",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_TRAIL,
        "refinement": (
            "appending a spurious trailing separator renders a different string (`...D.h.`) "
            "the F2P exact-equality assertion rejects. A real patch emitting a trailing "
            "separator would not resolve."
        ),
        "rationale": (
            "REJECTED by clause C1 (text). The spec join ends exactly at methodName with no "
            "trailing separator; this rival appends one. Witness varies the inputs to a fresh "
            "top-level point; the two strings differ in the suffix. If it VERIFIES => "
            "SPEC-TOO-WEAK (the 'no extra glyphs' guarantee is unpinned)."
        ),
        # top-level owner; gold "z.D.h", rival "z.D.h." -> differ in the suffix.
        "witness": _wit("z", "D", "D", "h",
                        "exact suffix: gold ends at the method name, rival appends a "
                        "spurious separator"),
    },
    {
        "id": "weak-swap-order",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_SWAP,
        "refinement": (
            "emitting the owner's qualified name ahead of the defining module renders a "
            "reference whose components are permuted (`Owner.pkg.method`); the module path no "
            "longer leads the dotted path, so the reference does not resolve at import time "
            "even though the accompanying import line is right. The F2P assertion compares the "
            "emitted string exactly, so a faithful patch of this shape does NOT resolve."
        ),
        "rationale": (
            "REJECTED by clause C1 (text). The spec pins the join to module FIRST, then "
            "ownerQualname, then methodName; this rival permutes the first two. Aimed at what "
            "the four ported rivals leave unattacked — each of them keeps module in head "
            "position, so none of them pins component ORDER as opposed to component PRESENCE. "
            "Witness probes a TOP-LEVEL owner (ownerName == ownerQualname) so the ownerName/"
            "ownerQualname distinction plays no part and only the ordering separates the two. "
            "If it VERIFIES => SPEC-TOO-WEAK (the join order is unpinned)."
        ),
        # top-level owner; gold "pkg.E.fn", rival "E.pkg.fn" -> differ.
        "witness": _wit("pkg", "E", "E", "fn",
                        "component order: gold leads with the module, rival leads with the "
                        "owner's qualified name"),
    },
    {
        "id": "weak-empty-imports",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_NOIMPORT,
        "refinement": (
            "emitting no import at all renders a correct reference string that nothing brings "
            "into scope, so the migration fails at import time; the F2P assertion compares the "
            "emitted import set exactly and an empty set is not the required singleton. A "
            "faithful patch of this shape does NOT resolve."
        ),
        "rationale": (
            "REJECTED by clause C2 (imports). Attacks C2 from the side weak-drop-import does "
            "not reach: that rival emits a singleton with the WRONG PAYLOAD, so it pins the "
            "payload while leaving the list's LENGTH untested. This one emits the empty list, "
            "which the spec refutes only because it fixes imports to exactly one element. "
            "Witness probes a NESTED owner with a fresh module so C1 holds for both impls and "
            "only the import list separates them. If it VERIFIES => SPEC-TOO-WEAK (the spec "
            "would admit an impl that emits no import)."
        ),
        # nested owner, fresh module; C1 holds for both, gold imports ["import sys"],
        # rival imports [] -> differ in length.
        "witness": _wit("sys", "R", "N.R", "k",
                        "import list length: gold emits exactly one import, rival emits none"),
    },
]


# No @ContractOnly axioms and no opaque callees: the dotted join and the import
# formatting (importFor) are modeled DEEPLY over transparent char-list carriers, so
# the axiom lane is vacuous here and belongs to G-AX regardless.
AXIOM_TESTS = []


# ===========================================================================
# assessment — INDEPENDENT AUDIT of this battery, with the builds that back it.
# Every exit code below was observed with scripts/lean_verify.sh on files built
# by the gate's own witness_file()/variant surgery under /tmp. Nothing here is
# an expectation; the numbers are what the verifier printed.
#
# WITNESS DISCRIMINATION, re-derived (attack B) — all four ported rivals plus the
# two added here, each built twice (rival / frozen solution):
#   weak-owner-bare-name   rival 0, gold 1     weak-missing-dot   rival 0, gold 1
#   weak-drop-import       rival 0, gold 1     weak-trailing-dot  rival 0, gold 1
#   weak-swap-order        rival 0, gold 1     weak-empty-imports rival 0, gold 1
# Every gold-side failure is a PLAIN EVALUATION: "Tactic `decide` proved that the
# proposition ¬(... ) is false" — the kernel reduced the whole predicate and found
# gold satisfies the spec at that literal input. No stuck reduction, no missing
# instance, no unfolding failure, no unknown name.
#
# FORGERY TEST (attack B′), run on all six even though a plain evaluation does not
# require it: each witness was rebuilt with the `¬` DROPPED (asserting the frozen
# impl is CORRECT at that point) against both subjects. Exit codes INVERT —
# forged-on-gold 0, forged-on-rival 1, for all six — with the same
# "decide proved ... is false" shape on the failing side. So gold's exit code
# tracks the CLAIM, not the file: these are refutations, not tactic mismatches.
#
# OBSERVABLE-DIFFERENCE CHECK (attack C): each rival differs from gold at its own
# witness point by construction, and the witness point is chosen so exactly ONE
# clause separates them (nested owner for the qualname rivals; top-level owner for
# the import/order/suffix rivals). No rival is definitionally equal to gold — a
# `decide` that evaluates to `false` on gold and `true` on the rival is proof of
# that, not an argument about it.
#
# SPEC-TOO-WEAK probes (attack D) — five NEW wrong impls the battery did not
# contain, each built with a witness against rival and gold:
#   swap-order (module/owner permuted)        rival 0, gold 1  -> rejected
#   dup-import (import emitted twice)         rival 0, gold 1  -> rejected
#   empty-imports (no import at all)          rival 0, gold 1  -> rejected
#   import-wrong-arg (imports the owner name) rival 0, gold 1  -> rejected
#   drop-first-dot (module glued to owner)    rival 0, gold 1  -> rejected
# All five gold-side failures are plain evaluations. NONE verified against the
# frozen spec, so no spec hole was found. The two that probe genuinely new
# clauses — component ORDER and import-list LENGTH — are now shipped above as
# weak-swap-order and weak-empty-imports; the other three are refuted by clauses
# the existing rivals already pin.
#
# SPEC-TOO-STRONG probes (attack E) — three NEW correct reshapes, each with the
# cheapest honest proof for its shape; all three VERIFY (exit 0):
#   re-associated join `a ++ (b ++ (c ++ (d ++ e)))`   exit 0  (closed by `simp`)
#   `let mut text` imperative accumulation             exit 0
#   `List.flatten [module, ".", qual, ".", method]`     exit 0
# The re-association one is the informative result: rebuilt with the FROZEN
# `refine ⟨rfl, rfl⟩` body it FAILS ("Application type mismatch: rfl has type
# ?m = ?m but is expected to have type ..."), i.e. its text is NOT definitionally
# equal to the frozen chain, and the spec accepts it anyway. That is real evidence
# the postcondition pins BEHAVIOUR and not the frozen term. (The `let mut` reshape,
# by contrast, closes under the frozen `rfl` body — it is defeq, hence weak, which
# is the same caveat now recorded on pos-reorder-imports-first.)
#
# FRAME-MUTATION: agreed VACUOUS, and for the stated reason — Lean has no aliasing
# and no fractional permission, so nagini's "write into a read-only input" rival
# has no term-level analogue. Nothing to build.
#
# DIVERGENCE: a KNOWN HOLE, not a vacuous class; three shapes were built to
# establish it. See the header note for the exact errors.
#
# ADMISSIBILITY: the port dropped this lane on the ground that the frozen
# obligation binds no precondition. That reason is REJECTED here — the analogue on
# a total carrier is the obligation being unsatisfiable at an F2P-shaped input, and
# it is expressible: adm-nested-owner-satisfiable (added above) discharges the
# postcondition at a nested-owner record by `decide` and builds at exit 0, scope
# clean. Landed rather than argued.
# ===========================================================================
