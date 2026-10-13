# properties.py — G-PBT falsification battery for django__django-13807 (lean lane).
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
#   fkCheckQueries : List Char → List Char → List Char
#                    → (List Char × List Char × List Char)
#   From a (table, primaryKey, column) identifier triple it builds three SQL query
#   strings. The single postcondition pins each of the three results to the exact
#   ordered concatenation of fixed literal SQL text with the RENDERED identifiers,
#   where every substituted identifier passes through `quoteIdentifier` — the
#   double-quote-wrapping renderer that leaves an already-wrapped identifier
#   unchanged (idempotent). The load-bearing discriminator at every splice site is
#   that the RENDERED form is spliced, never the bare identifier: for a reserved
#   word the two differ. quoteIdentifier is GROUNDED in the input (a total function
#   of the input code points) — there is no opaque answer-key oracle to echo, so the
#   cheapest wrong impl is the pre-change one that splices the bare identifier.
#
# CARRIER NOTE: nagini modeled two assemblers (single-table + a three-id command)
# over List[int] code points behind fractional permissions. This backend collapses
# the modeled behaviour into ONE function returning the three query strings for a
# single table over a transparent `List Char` carrier, with `quoteIdentifier`
# modeled DEEPLY (an A-reference validated against the real callee by G-AX). Every
# splice site and the idempotence branch are therefore transparently attackable
# here.
#
# LANES THAT DO NOT PORT:
#   * FRAME-MUTATION (nagini's MANDATORY #1 class: the four identifier inputs were
#     read-only Acc(.,1/2), and rivals tried to WRITE the delimiter into the input
#     list in place). Lean is referentially transparent — no aliasing, no fractional
#     permissions — so a "write-back into a read-only input" rival is not
#     expressible and the whole lane is VACUOUS here. See 'assessment'.
#   * AXIOM_TESTS. The axiom lane (validating quoteIdentifier == the real callee) is
#     G-AX's job; this gate ignores them.
#
# ADMISSIBILITY: LANDED (see admiss-f2p-shaped below). An earlier revision of this
# file recorded the lane as N/A because "the frozen obligation carries no
# precondition hypothesis, so nothing can be PRECOND-TOO-STRONG". That reason is
# wrong, and a second audit removed it. The obligation IS an unconditional
# universal, so no HYPOTHESIS can be over-strong — but the analogue on a total
# carrier is the obligation being UNSATISFIABLE at an F2P-shaped input, which a
# positive that discharges the postcondition BY EVALUATION at that concrete input
# tests directly. It is expressible here and it verifies; see the case's rationale
# for the machine-checked informativeness control.
#
# INDEPENDENT AUDIT (post-port). Verified by rebuilding every case: statement
# integrity is exact (each variant's diff against the frozen file is confined to
# lines inside impl-start/impl-end, with the theorem statement byte-identical),
# and the six then-existing reject witnesses were rebuilt twice — each ELABORATES
# against its rival (exit 0) and FAILS on the frozen solution (exit 1) with
# `Tactic 'decide' proved that the proposition ¬(…)`, a SEMANTIC refutation of the
# concrete claim rather than an unknown identifier or an unfolding failure. Two
# defects were found and repaired here:
#   1. Both shipped positives were DEFINITIONALLY EQUAL to the frozen impl (Lean
#      collapses `let`-vs-`return` and a data-independent `let` reorder), so they
#      passed without probing SPEC-TOO-STRONG at all. Two non-defeq positives
#      (pos-append-reassoc, pos-flatten-segments) were added; both need a reproof
#      and both verify.
#   2. nagini's `partial-domain-constant-delim` had been dropped silently. It is
#      expressible here and attacks GROUNDEDNESS, which nothing else in the
#      battery attacked; re-derived as `constant-rendering-fkcheck`.
# Six further WRONG impls not in this battery were probed against the frozen spec
# (corrupted literal separator, swapped column identifiers, a single-quote
# delimiter, a half-guard renderer that checks only the leading quote, a
# tuple-slot swap, and a dropped close-paren). All six were REJECTED, so no
# SPEC-TOO-WEAK hole was found.
#
# SECOND INDEPENDENT AUDIT. Everything above was re-derived from scratch rather
# than trusted, and all 11 then-shipped cases were rebuilt:
#   * Statement integrity (attack A) re-checked mechanically on all 11 modules:
#     every `theorem correct_fkCheckQueries` statement is byte-identical to the
#     frozen one and every diff hunk falls inside impl-start/impl-end (lines
#     42-55), plus the proof BODY at line 63 for the two reproving positives.
#   * All 7 reject witnesses rebuilt twice: rival exit 0, gold exit 1, every gold
#     failure a `decide`-refutation of the concrete claim.
#   * FORGERY test (attack B') run on all 7 even though their gold signatures are
#     plain evaluations: flipping the witness's claim (dropping the `¬`) makes the
#     GOLD build succeed (exit 0, empty log — `decide` PROVES the spec holds
#     there) and the RIVAL build fail (exit 1). The exit codes therefore track the
#     CLAIM and not the file, so none of these cases is hollow.
#   * Five NEW wrong impls beyond the six above — a cross-binder splice (fkList
#     rendering `primaryKey` instead of `table`), a renderer guarding only the
#     TRAILING quote, a corrupted `rowid = 1` literal tail, a swapped PRAGMA
#     prefix, and a strip-then-wrap renderer that deletes interior quotes — were
#     all REJECTED, each with a rival-0/gold-1 witness. Still no SPEC-TOO-WEAK.
#   * Two NEW correct reshapes (attack E) beyond the shipped positives: an INLINED
#     renderer at the fkCheck site (verifies under the frozen proof body) and a
#     DOUBLE-rendered `quoteIdentifier (quoteIdentifier table)` (verifies once
#     reproven from an idempotence lemma). No SPEC-TOO-STRONG hole: the spec
#     constrains the rendered string, not the term that computes it.
# One defect was found and repaired: the ADMISSIBILITY lane had been dropped for
# an invalid reason. It is landed below as admiss-f2p-shaped.
from pathlib import Path

INSTANCE = "django__django-13807"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# impl-region anchors. Each lies ENTIRELY inside impl-start/impl-end and is unique
# in the file, so editing it cannot perturb the spec view.
# ---------------------------------------------------------------------------

# NOTE: the bare concatenation expressions (e.g. `"PRAGMA foreign_key_check("...`)
# each appear TWICE in the file — once in the spec clause, once in the impl `let`
# binding. So every anchor below includes its impl-only `let …` prefix, which makes
# it unique to the impl region and guarantees a swap cannot perturb the spec view.

# The full impl body (between `Id.run do` and `-- impl-end`), verbatim. Positive
# controls swap this whole block for a behaviourally-identical reshape.
_IMPL_BODY = (
    '  let fkCheck :=\n'
    '    "PRAGMA foreign_key_check(".toList ++ quoteIdentifier table ++ [\')\']\n'
    '  let fkList :=\n'
    '    "PRAGMA foreign_key_list(".toList ++ quoteIdentifier table ++ [\')\']\n'
    '  let selectRow :=\n'
    '    "SELECT ".toList ++ quoteIdentifier primaryKey ++ ", ".toList\n'
    '      ++ quoteIdentifier column ++ " FROM ".toList ++ quoteIdentifier table\n'
    '      ++ " WHERE rowid = %s".toList\n'
    '  return (fkCheck, fkList, selectRow)'
)
assert _BASE.count(_IMPL_BODY) == 1, "impl-body anchor drifted"

# The fkCheck `let` binding (impl-only; produces clause result.1's value).
_FKCHECK_LET = (
    '  let fkCheck :=\n'
    '    "PRAGMA foreign_key_check(".toList ++ quoteIdentifier table ++ [\')\']'
)
# The fkList `let` binding (impl-only; produces clause result.2.1's value).
_FKLIST_LET = (
    '  let fkList :=\n'
    '    "PRAGMA foreign_key_list(".toList ++ quoteIdentifier table ++ [\')\']'
)
# The selectRow `let` binding (impl-only; produces clause result.2.2's value). The
# three select-site rivals swap this whole block, changing exactly one splice.
_SELECT_LET = (
    '  let selectRow :=\n'
    '    "SELECT ".toList ++ quoteIdentifier primaryKey ++ ", ".toList\n'
    '      ++ quoteIdentifier column ++ " FROM ".toList ++ quoteIdentifier table\n'
    '      ++ " WHERE rowid = %s".toList'
)
for _a in (_FKCHECK_LET, _FKLIST_LET, _SELECT_LET):
    assert _BASE.count(_a) == 1, f"anchor drifted / not unique: {_a!r}"


# ---------------------------------------------------------------------------
# Witness helper. States `¬ problem_spec … (implementation …)` at one concrete
# (table, primaryKey, column) input, closed by `decide`. It ELABORATES against a
# rival whose result diverges from the spec at that point, and FAILS on the frozen
# solution (which satisfies the spec everywhere). All inputs are concrete literals
# — no opaque terms, no hypotheses — so the assumptions are trivially satisfiable.
# ---------------------------------------------------------------------------
def _wit(table, pk, col):
    args = f'"{table}".toList "{pk}".toList "{col}".toList'
    return (
        f"example : ¬ problem_spec_fkCheckQueries {args}\n"
        f"    (implementation_fkCheckQueries {args}) := by\n"
        f"  unfold problem_spec_fkCheckQueries implementation_fkCheckQueries\n"
        f"  decide"
    )


# An already-double-quoted identifier witness (exercises the idempotence branch).
def _wit_quoted():
    # table = `"o"` (already wrapped at both ends), pk/col plain.
    args = '"\\"o\\"".toList "p".toList "c".toList'
    return (
        f"example : ¬ problem_spec_fkCheckQueries {args}\n"
        f"    (implementation_fkCheckQueries {args}) := by\n"
        f"  unfold problem_spec_fkCheckQueries implementation_fkCheckQueries\n"
        f"  decide"
    )


# ---------------------------------------------------------------------------
# POSITIVE CONTROLS (soundness) — must VERIFY with the FROZEN proof body.
# ---------------------------------------------------------------------------

# pos-combined-return: build all three strings in ONE combined `return` tuple
# instead of three `let` bindings. Behaviourally identical; the frozen
# `refine ⟨?_, ?_, ?_⟩ <;> rfl` proof still closes because each component reduces
# definitionally to the same concatenation.
_POS_COMBINED = (
    '  return (\n'
    '    "PRAGMA foreign_key_check(".toList ++ quoteIdentifier table ++ [\')\'],\n'
    '    "PRAGMA foreign_key_list(".toList ++ quoteIdentifier table ++ [\')\'],\n'
    '    "SELECT ".toList ++ quoteIdentifier primaryKey ++ ", ".toList\n'
    '      ++ quoteIdentifier column ++ " FROM ".toList ++ quoteIdentifier table\n'
    '      ++ " WHERE rowid = %s".toList)'
)

# pos-reordered-lets: compute the three `let` bindings in REVERSE order (selectRow,
# then fkList, then fkCheck), assemble the tuple in the same final order. A
# data-independent reorder; the value is identical on every input and the frozen
# proof still closes.
_POS_REORDER = (
    '  let selectRow :=\n'
    '    "SELECT ".toList ++ quoteIdentifier primaryKey ++ ", ".toList\n'
    '      ++ quoteIdentifier column ++ " FROM ".toList ++ quoteIdentifier table\n'
    '      ++ " WHERE rowid = %s".toList\n'
    '  let fkList :=\n'
    '    "PRAGMA foreign_key_list(".toList ++ quoteIdentifier table ++ [\')\']\n'
    '  let fkCheck :=\n'
    '    "PRAGMA foreign_key_check(".toList ++ quoteIdentifier table ++ [\')\']\n'
    '  return (fkCheck, fkList, selectRow)'
)

# AUDIT NOTE (positive-control strength). The two positives above are reshapes
# that Lean collapses by zeta/iota reduction: `let`-vs-`return` and a
# data-independent reorder of the `let` bindings both leave the impl
# DEFINITIONALLY EQUAL to the frozen one, which is why they close under the
# FROZEN `<;> rfl` body unchanged. They are honest but weak — a spec that
# accepted only terms defeq to gold would still pass them, so on their own they
# do not probe SPEC-TOO-STRONG. The two positives below are therefore NOT defeq
# to gold: they change the association / construction of the concatenation, so
# `rfl` no longer closes the third clause and the case must REPROVE it (which
# variant_scope permits: the `theorem correct_fkCheckQueries` STATEMENT stays
# byte-identical, only the tactic body differs). A spec pinned to gold's
# syntactic term shape rather than to its VALUE would reject these.

# The frozen proof body (inside proof-start/proof-end), verbatim. A positive that
# is not defeq to gold swaps this for a reproof of the same statement.
_PROOF_BODY = (
    '  intro table primaryKey column\n'
    '  refine ⟨?_, ?_, ?_⟩ <;> rfl'
)
assert _BASE.count(_PROOF_BODY) == 1, "proof-body anchor drifted"

# pos-append-reassoc: the selectRow concatenation is RIGHT-associated instead of
# left-associated. `List.append` is associative so the value is identical on every
# input, but the two terms are not definitionally equal, so the third clause needs
# `List.append_assoc`. If this FAILS => SPEC-TOO-STRONG (the spec would be pinning
# gold's bracketing rather than the string it denotes).
_POS_REASSOC = (
    '  let selectRow :=\n'
    '    "SELECT ".toList ++ (quoteIdentifier primaryKey ++ (", ".toList\n'
    '      ++ (quoteIdentifier column ++ (" FROM ".toList ++ (quoteIdentifier table\n'
    '      ++ " WHERE rowid = %s".toList)))))'
)
_POS_REASSOC_PROOF = (
    '  intro table primaryKey column\n'
    '  refine ⟨?_, ?_, ?_⟩\n'
    '  · rfl\n'
    '  · rfl\n'
    '  · simp [implementation_fkCheckQueries, problem_spec_fkCheckQueries,\n'
    '      List.append_assoc]'
)

# pos-flatten-segments: selectRow is built by listing its seven segments and
# FLATTENING them, rather than by an explicit chain of `++`. Same value on every
# input, a genuinely different construction (not defeq), reproven.
_POS_FLATTEN = (
    '  let selectRow :=\n'
    '    ["SELECT ".toList, quoteIdentifier primaryKey, ", ".toList,\n'
    '      quoteIdentifier column, " FROM ".toList, quoteIdentifier table,\n'
    '      " WHERE rowid = %s".toList].flatten'
)
_POS_FLATTEN_PROOF = (
    '  intro table primaryKey column\n'
    '  refine ⟨?_, ?_, ?_⟩\n'
    '  · rfl\n'
    '  · rfl\n'
    '  · simp [implementation_fkCheckQueries, problem_spec_fkCheckQueries,\n'
    '      List.flatten, List.append_assoc]'
)


# ---------------------------------------------------------------------------
# ADMISSIBILITY — the obligation must be SATISFIABLE at an F2P-shaped input.
#
# The frozen obligation is an unconditional `∀ …`, so there is no precondition
# HYPOTHESIS that could be over-strong. The analogue on this total carrier is the
# obligation being UNSATISFIABLE at exactly the input the reported failure is
# about, which this case tests directly: the postcondition is discharged BY
# EVALUATION (`decide`) at the F2P-shaped triple — a reserved-word table with
# reserved-word primary-key and foreign-key columns, the shape the reported
# failure drives — as a ground `have`; the `have` is then cleared and the FROZEN
# tactic body closes the obligation verbatim. Nothing is assumed: no new
# declaration, no axiom, the theorem statement is byte-identical, and the impl
# region is untouched.
# ---------------------------------------------------------------------------
_ADMISS_PROOF = (
    '  have _f2p : problem_spec_fkCheckQueries\n'
    '      "order".toList "select".toList "where".toList\n'
    '      (implementation_fkCheckQueries\n'
    '        "order".toList "select".toList "where".toList) := by\n'
    '    unfold problem_spec_fkCheckQueries implementation_fkCheckQueries\n'
    '    decide\n'
    '  clear _f2p\n'
    '  intro table primaryKey column\n'
    '  refine ⟨?_, ?_, ?_⟩ <;> rfl'
)


# ---------------------------------------------------------------------------
# UNIQUENESS RIVALS — must be REJECTED (else SPEC-TOO-WEAK). Each shares the frozen
# spec exactly, edits only the impl region, and carries a discriminating witness.
# ---------------------------------------------------------------------------

SPEC_TESTS = [
    # ---- positive controls -------------------------------------------------
    {
        "id": "pos-combined-return",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _IMPL_BODY, _POS_COMBINED),
        "rationale": (
            "structurally-different but CORRECT impl: the three query strings are "
            "produced in a single combined `return` tuple rather than three "
            "intermediate `let` bindings. The result is identical on every input; "
            "the frozen `theorem correct_fkCheckQueries` statement is kept byte-"
            "identical and its `refine ⟨?_, ?_, ?_⟩ <;> rfl` proof still closes "
            "because each component reduces definitionally to the same "
            "concatenation. If it FAILS => SPEC-TOO-STRONG."
        ),
    },
    {
        "id": "pos-reordered-lets",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _IMPL_BODY, _POS_REORDER),
        "rationale": (
            "structurally-different but CORRECT impl: the three `let` bindings are "
            "computed in reverse order (a data-independent reorder) and assembled in "
            "the same final tuple order. Value identical on every input; the frozen "
            "proof still closes. If it FAILS => SPEC-TOO-STRONG. NOTE: like "
            "pos-combined-return this reshape is DEFINITIONALLY EQUAL to the frozen "
            "impl (Lean collapses the `let` order by zeta reduction), so it is a "
            "weak positive — see pos-append-reassoc / pos-flatten-segments for the "
            "non-defeq ones that actually probe SPEC-TOO-STRONG."
        ),
    },
    {
        "id": "pos-append-reassoc",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _swap(_BASE, _SELECT_LET, _POS_REASSOC),
            _PROOF_BODY, _POS_REASSOC_PROOF),
        "rationale": (
            "structurally-different but CORRECT impl that is NOT definitionally "
            "equal to the frozen one: the SELECT concatenation is right-associated "
            "instead of left-associated. `List.append` is associative, so the string "
            "produced is identical on every input, but `rfl` no longer closes the "
            "third clause — the case reproves it with `List.append_assoc`, keeping "
            "the frozen `theorem correct_fkCheckQueries` STATEMENT byte-identical. "
            "This is the positive that actually tests SPEC-TOO-STRONG: it verifies "
            "only because the postcondition pins the VALUE of each query string, "
            "not gold's bracketing of the appends. If it FAILS => SPEC-TOO-STRONG."
        ),
    },
    {
        "id": "pos-flatten-segments",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _swap(_BASE, _SELECT_LET, _POS_FLATTEN),
            _PROOF_BODY, _POS_FLATTEN_PROOF),
        "rationale": (
            "structurally-different but CORRECT impl, again NOT defeq to gold: the "
            "SELECT is assembled by listing its seven segments and FLATTENING, "
            "rather than by an explicit `++` chain. A different construction with "
            "the same value on every input, reproven via `List.flatten` + "
            "`List.append_assoc`; the frozen theorem statement is unchanged. "
            "Together with pos-append-reassoc this shows the spec constrains the "
            "rendered string and not the term that builds it. If it FAILS => "
            "SPEC-TOO-STRONG."
        ),
    },
    # ---- admissibility -----------------------------------------------------
    {
        "id": "admiss-f2p-shaped",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _PROOF_BODY, _ADMISS_PROOF),
        "rationale": (
            "LANDED BY AUDIT; the lane had been dropped for an invalid reason (\"the "
            "frozen obligation has no precondition, so nothing can be PRECOND-TOO-"
            "STRONG\"). The obligation is indeed an unconditional universal, so no "
            "HYPOTHESIS can be over-strong — but the analogue on a total carrier is "
            "the obligation being UNSATISFIABLE at an F2P-shaped input, and this "
            "case tests that directly. The postcondition is discharged BY EVALUATION "
            "(`decide`) at the F2P-shaped identifier triple — table, primary-key "
            "column and foreign-key column all reserved words, the shape the "
            "reported failure drives, and the one input where the rendered and bare "
            "forms differ at every one of the five splice sites — as a ground "
            "`have`; the `have` is then CLEARED and the frozen tactic body closes "
            "the obligation verbatim, so the case cannot pass on the strength of the "
            "added step. Nothing is assumed: no new declaration, no axiom, the "
            "`theorem correct_fkCheckQueries` statement is byte-identical and the "
            "impl region is untouched. INFORMATIVENESS CONTROL (machine-checked "
            "during the audit, not shipped): the same shape asserting the "
            "postcondition of the WRONG result at that input — the three query "
            "strings built by splicing the BARE identifiers — does NOT close; "
            "`decide` reports the proposition `is false` (exit 1). So the `decide` "
            "here is really evaluating the claim rather than closing anything put in "
            "front of it. If this case FAILS, the obligation is unsatisfiable at "
            "exactly the input the fix is for => PRECOND-TOO-STRONG."
        ),
    },
    # ---- bare-identifier rivals (the pre-change behaviour) -----------------
    {
        "id": "bare-table-fkcheck",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _FKCHECK_LET,
            '  let fkCheck :=\n'
            '    "PRAGMA foreign_key_check(".toList ++ table ++ [\')\']'),
        "refinement": (
            "this IS the pre-change behaviour for the first query: the bare table "
            "identifier is interpolated into the foreign-key-check PRAGMA with no "
            "rendering. Its faithful real counterpart is the unchanged repo line, "
            "which for the FAIL_TO_PASS table name (a SQL reserved word) emits a "
            "PRAGMA whose argument the database parses as syntax, not as a name, "
            "raising a syntax error before any integrity check runs. So it does NOT "
            "resolve test_check_constraints_sql_keywords, and a verifying rival here "
            "would be a true verify-does-not-imply-resolve break."
        ),
        "rationale": (
            "REJECTED by the postcondition's FIRST clause (result.1), which pins the "
            "first query to the fixed prefix ++ quoteIdentifier table ++ close-paren. "
            "The rival splices the bare `table`, and quoteIdentifier table ≠ table "
            "for a non-wrapped identifier, so the clause equality fails. Attacks the "
            "`table` binder in clause result.1. If it VERIFIES => SPEC-TOO-WEAK."
        ),
        # table = "order" (a reserved word, not already-quoted): gold wraps it, rival
        # leaves it bare. pk/col irrelevant to clause result.1 but concrete.
        "witness": _wit("order", "id", "fk"),
    },
    {
        "id": "bare-table-fklist",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _FKLIST_LET,
            '  let fkList :=\n'
            '    "PRAGMA foreign_key_list(".toList ++ table ++ [\')\']'),
        "refinement": (
            "the pre-change behaviour for the second query: the bare table "
            "identifier is interpolated into the foreign-key-list PRAGMA. Its "
            "faithful real counterpart raises a syntax error on a reserved-word "
            "table name (parsed as syntax), so the row that the check needs is never "
            "retrieved and the F2P is not resolved."
        ),
        "rationale": (
            "REJECTED by the postcondition's SECOND clause (result.2.1), which pins "
            "the second query to the fixed prefix ++ quoteIdentifier table ++ "
            "close-paren; the rival splices the bare `table`. Attacks the `table` "
            "binder in clause result.2.1 — an independent clause from result.1. If "
            "it VERIFIES => SPEC-TOO-WEAK."
        ),
        # distinct point from bare-table-fkcheck: a different reserved word.
        "witness": _wit("group", "id", "fk"),
    },
    {
        "id": "bare-primarykey-select",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _SELECT_LET,
            '  let selectRow :=\n'
            '    "SELECT ".toList ++ primaryKey ++ ", ".toList\n'
            '      ++ quoteIdentifier column ++ " FROM ".toList ++ quoteIdentifier table\n'
            '      ++ " WHERE rowid = %s".toList'),
        "refinement": (
            "the pre-change behaviour for the primary-key column of the SELECT: the "
            "bare column identifier is interpolated. A faithful real patch that "
            "quoted the other identifiers but left the primary-key column bare would "
            "still fail on a reserved-word column name (the SELECT is a syntax "
            "error), so the value lookup the check depends on never returns and the "
            "F2P is not resolved."
        ),
        "rationale": (
            "REJECTED by the postcondition's THIRD clause (result.2.2), which pins "
            "the SELECT to a concatenation whose primary-key segment is "
            "quoteIdentifier primaryKey; the rival splices the bare `primaryKey`, and "
            "quoteIdentifier primaryKey ≠ primaryKey for a non-wrapped identifier. "
            "Attacks the `primaryKey` binder in clause result.2.2. If it VERIFIES => "
            "SPEC-TOO-WEAK."
        ),
        # primaryKey = "select" (reserved word) is the abused binder here.
        "witness": _wit("t", "select", "fk"),
    },
    {
        "id": "bare-column-select",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _SELECT_LET,
            '  let selectRow :=\n'
            '    "SELECT ".toList ++ quoteIdentifier primaryKey ++ ", ".toList\n'
            '      ++ column ++ " FROM ".toList ++ quoteIdentifier table\n'
            '      ++ " WHERE rowid = %s".toList'),
        "refinement": (
            "the pre-change behaviour for the foreign-key column of the SELECT: the "
            "bare column identifier is interpolated. A faithful real patch that left "
            "the foreign-key column bare would fail on a reserved-word column name "
            "(the SELECT is a syntax error) and would not resolve the F2P, which "
            "drives exactly such a column name."
        ),
        "rationale": (
            "REJECTED by the postcondition's THIRD clause (result.2.2), whose "
            "foreign-key-column segment is quoteIdentifier column; the rival splices "
            "the bare `column`. Attacks the `column` binder in clause result.2.2 — a "
            "binder no other rival abuses. If it VERIFIES => SPEC-TOO-WEAK."
        ),
        # column = "where" (reserved word) is the abused binder here.
        "witness": _wit("t", "id", "where"),
    },
    {
        "id": "bare-table-select",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _SELECT_LET,
            '  let selectRow :=\n'
            '    "SELECT ".toList ++ quoteIdentifier primaryKey ++ ", ".toList\n'
            '      ++ quoteIdentifier column ++ " FROM ".toList ++ table\n'
            '      ++ " WHERE rowid = %s".toList'),
        "refinement": (
            "the pre-change behaviour for the FROM-clause table of the SELECT: the "
            "bare table identifier is interpolated. A faithful real patch that quoted "
            "the two columns but left the FROM table bare would still fail on a "
            "reserved-word table name (SELECT … FROM order is a syntax error), so the "
            "lookup never returns and the F2P is not resolved."
        ),
        "rationale": (
            "REJECTED by the postcondition's THIRD clause (result.2.2), whose "
            "FROM-table segment is quoteIdentifier table; the rival splices the bare "
            "`table` at THIS site (the other two `table` splices remain rendered), so "
            "the SELECT clause diverges. Attacks the `table` binder within clause "
            "result.2.2, distinct from the fkCheck/fkList sites. If it VERIFIES => "
            "SPEC-TOO-WEAK."
        ),
        # table = "join" reserved word; distinct point again.
        "witness": _wit("join", "id", "fk"),
    },
    # ---- partial-domain rival (idempotence sub-domain) ---------------------
    {
        "id": "partial-domain-unconditional-wrap",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _FKCHECK_LET,
            '  let fkCheck :=\n'
            '    "PRAGMA foreign_key_check(".toList ++ ([\'"\'] ++ table ++ [\'"\']) ++ [\')\']'),
        "refinement": (
            "wrapping the table in double-quotes UNCONDITIONALLY (dropping the "
            "already-wrapped guard) is correct on every plain identifier but "
            "double-wraps an identifier that is already double-quoted. The modeled "
            "renderer is idempotent precisely so that a name arriving already quoted "
            "is not wrapped twice; a faithful real patch that wrapped unconditionally "
            "would emit a doubly-quoted identifier for such an input, diverging from "
            "the required rendering. Correct only on the non-already-quoted "
            "sub-domain."
        ),
        "rationale": (
            "REJECTED by the postcondition's FIRST clause (result.1): quoteIdentifier "
            "leaves an already-double-quoted identifier UNCHANGED, but the rival adds "
            "another pair of quotes, so the clause equality fails on the "
            "already-quoted sub-domain. Attacks the idempotence branch of "
            "quoteIdentifier over the `table` binder — a sub-domain the bare-splice "
            "rivals never reach. If it VERIFIES => SPEC-TOO-WEAK on the idempotence "
            "sub-domain."
        ),
        # table already double-quoted (`"o"`): gold leaves it unchanged, rival
        # double-wraps it. This is the only witness that exercises the quoted branch.
        "witness": _wit_quoted(),
    },
    # ---- constant-rendering rival (nagini's partial-domain-constant-delim) --
    # AUDIT NOTE: the port dropped nagini's `partial-domain-constant-delim`
    # without recording it as inexpressible. It IS expressible on this carrier
    # and it attacks something no other rival here does — GROUNDEDNESS, i.e.
    # that the spliced text is a function of the identifier at all, rather than
    # merely being wrapped in the right delimiters. Re-derived below.
    {
        "id": "constant-rendering-fkcheck",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _FKCHECK_LET,
            '  let fkCheck :=\n'
            '    "PRAGMA foreign_key_check(".toList ++ [\'"\', \'"\'] ++ [\')\']'),
        "refinement": (
            "emitting a CONSTANT delimiter pair discards the identifier entirely: "
            "the rendered argument is the same two characters whatever table was "
            "asked about. A faithful real counterpart would ask the database about "
            "an empty-named table rather than the one under check, so the violating "
            "row is never returned and the integrity error the F2P expects is never "
            "raised — it does not resolve the F2P. Correct only on the empty-"
            "identifier sub-domain (where the wrapped form is exactly those two "
            "characters), which is why it is a partial-domain rival and not simply "
            "a wrong constant."
        ),
        "rationale": (
            "REJECTED by the postcondition's FIRST clause (result.1): the required "
            "argument is quoteIdentifier table, which DEPENDS on `table`, whereas "
            "the rival's is a fixed two-character string, so the equality holds "
            "only when table is empty. This is the one rival that attacks "
            "GROUNDEDNESS rather than the choice of rendering — the bare-splice "
            "rivals all still emit a table-dependent string, and the "
            "unconditional-wrap rival emits the right characters in the wrong "
            "number. If it VERIFIES => SPEC-TOO-WEAK: the spec would be pinning "
            "the delimiters without pinning the name between them."
        ),
        # table = "order" (non-empty, so outside the sub-domain where the rival is
        # correct); gold renders the name, the rival renders nothing.
        "witness": _wit("order", "id", "fk"),
    },
]


# No @ContractOnly axioms and no opaque callees: the identifier renderer is modeled
# DEEPLY as `quoteIdentifier` over the transparent `List Char` carrier, so the axiom
# lane is vacuous here and belongs to G-AX regardless.
AXIOM_TESTS = []
