# properties.py — G-PBT falsification battery for django__django-13820 (lean lane).
# NOT a Lean module; a manifest of adversarial cases the gate elaborates against
# the frozen spec. Ported from the nagini sibling's properties.py, re-expressed
# against this backend's carrier.
#
# Defended surface (read from Solution.lean):
#   providesMigrations (hasFile : Bool) (path : ModulePath) : Bool
#   A single obligation, `theorem correct_providesMigrations`, over a single
#   top-level postcondition clause:
#     (C) result = (path.isPackage && (hasFile || path.isList))
#   The clause is one equality, but it decomposes into three INDEPENDENT
#   sub-claims that a rival can break separately, and every rival below is
#   labelled by which one it attacks:
#     (C-pkg)  a non-package is never a source of migrations
#              (path.isPackage = false => result = false);
#     (C-file) a package that exposes a file location IS a source, whatever its
#              package path (hasFile = true => result = path.isPackage);
#     (C-list) a package with NO file location is a source exactly when its
#              package path is an ordinary list (this is the sub-claim the
#              change makes definite, and the F2P-shaped row lives here).
#
# Carrier and the input space. Both binders are finite and fully transparent —
# `hasFile : Bool` and `path : ModulePath` (three constructors) — so the whole
# domain is SIX points and every witness below is a literal `decide`. No opaque
# callee appears anywhere in the spec (the axioms region is empty), so none of
# the carrier-conditioning machinery is needed here: the refutations are stated
# at concrete inputs and computed. The battery probes all six points, i.e. the
# ENTIRE domain of the modeled function:
#     (hasFile, path)          C requires   probed by
#     (false, noPath)          false        weak-always-provides,
#                                           weak-non-package-without-file
#     (false, listPath)        TRUE         weak-no-file-location-skips,
#                                           weak-list-polarity-flip
#     (false, customPath)      false        weak-provides-from-placeholder,
#                                           weak-list-polarity-flip
#     (true,  noPath)          false        weak-provides-from-non-package
#     (true,  listPath)        true         weak-never-provides,
#                                           weak-accept-guard-inverted
#     (true,  customPath)      true         weak-ignores-file-location
#
# Correspondence to the nagini sibling. The nagini model contracted the same
# decision over THREE independent booleans plus a precondition ruling out the two
# unreachable rows; this bundle folds the package-ness and the path-shape facts
# into one three-constructor `ModulePath`, which makes those rows unrepresentable
# rather than excluded. So the reachable domain is the same six rows, the nagini
# per-row rivals port one-for-one, and nagini's precondition-admissibility case
# becomes a claim about the modeled point rather than about an admitted input
# (see admiss-modeled-rows). Ported: all six nagini uniqueness rivals and all
# three positives. Three rivals with NO nagini counterpart are added so that each
# binder is varied within a fixed value of the other (see `assessment`).
#
# Vacuous / dropped classes (stated, not silently omitted):
#   * FRAME / PERMISSION-MUTATION lane — VACUOUS on lean, and already recorded
#     inapplicable by the nagini sibling itself (its three inputs are immutable
#     scalars passed by value, so there was no read-only heap input to overwrite
#     even there). Lean is referentially transparent: there is no aliasable input
#     to mutate at all. Nothing to port, and no substitute is fabricated.
#   * DIVERGENCE / NON-TERMINATION lane — VACUOUS on lean. The nagini sibling
#     carries no such case for this instance, and in any event
#     `implementation_providesMigrations` is a total Lean `def`: a diverging
#     implementation cannot be written, so the class does not exist on this
#     carrier. (Contrast velvet under `partial` termination semantics, where a
#     diverging rival satisfies every clause vacuously and the frozen spec ADMITS
#     it — a known spec hole, not a vacuous class; see
#     the corpus-wide termination-semantics finding. That disposition does not apply to lean.)
#   * UNGROUNDED-ORACLE ECHO — N/A, exactly as the nagini sibling records. The
#     spec's right-hand side is a transparent boolean function of the two binders
#     built from the two pure helpers; there is no opaque answer-key to echo, so
#     returning the spec's RHS is the CORRECT behaviour and not a cheat. Both
#     directions are shipped as positives instead: pos-spec-shaped-expression
#     returns that RHS verbatim, and pos-constructor-match never mentions either
#     helper (see its rationale).
#   * AXIOM lane — DROPPED. `meta.axioms == []` and no opaque callee exists on
#     this path; the introspection reads are modeled directly as the two binders.
#     The axiom lane is G-AX's job and this gate ignores it. AXIOM_TESTS = [].
#
# Independent-audit probes (run against the frozen spec, NOT shipped as cases —
# they are recorded here so a later reader knows the clause was attacked from
# outside the battery and where the attack stopped). Eleven impls the battery
# does not contain were built, each under three proof scripts (the frozen
# `cases … <;> rfl`, a `cases … <;> decide`, and a helper-unfolding `simp_all`):
#   WRONG (must be rejected; all six were, under all three scripts): the two
#   acceptance signals conjoined rather than disjoined; the two signals xor'd;
#   the disjunction with the package test dropped; the package test alone; the
#   file-location signal alone; and the path-shape test at inverted polarity
#   inside the disjunction. No wrong impl verified => no SPEC-TOO-WEAK hole
#   found beyond what the nine rivals below already pin.
#   CORRECT RESHAPES (must verify; all five did, under all three scripts): the
#   De Morgan dual of the frozen two-guard skip form; the re-associated
#   `(isPackage && hasFile) || isList` (equal because an ordinary-list path
#   entails package-ness); a six-row `match` on BOTH binders naming neither pure
#   helper; the guard sequence with the path-shape test hoisted FIRST; and the
#   `decide`-of-a-Prop encoding. No faithful correct reshape was rejected => no
#   SPEC-TOO-STRONG hole found. The clause is an equality to a total boolean
#   function of a six-point domain, which is why both probes come back clean:
#   there is no unconstrained output component and no sub-domain left free.

from pathlib import Path

INSTANCE = "django__django-13820"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# --- Frozen regions, extracted verbatim so the manifest breaks loudly on drift.
# The impl region body and the proof TACTIC body are the only regions a variant
# may edit. The spec view, the signatures, and the byte-identical
# `theorem correct_providesMigrations` STATEMENT are never touched, so same_spec
# and the surviving-obligation rule hold by construction.

_IMPL_OLD = """\
def implementation_providesMigrations
    (hasFile : Bool) (path : ModulePath) : Bool := Id.run do
  -- A module that is not a package cannot provide migrations.
  if !path.isPackage then
    return false
  -- A package with no file location whose path is a custom (non-list) iterable
  -- is an empty-directory placeholder, not a real migrations package.
  if !hasFile && !path.isList then
    return false
  return true"""

assert _BASE.count(_IMPL_OLD) == 1, "impl region drifted from expected text"

_PROOF_OLD = """\
  intro hasFile path
  unfold problem_spec_providesMigrations implementation_providesMigrations
  cases path <;> cases hasFile <;> rfl"""

assert _BASE.count(_PROOF_OLD) == 1, "proof region drifted from expected text"

# Every variant's impl keeps the frozen signature line; only the body differs.
_SIG = """\
def implementation_providesMigrations
    (hasFile : Bool) (path : ModulePath) : Bool := Id.run do
"""


def _impl(new_impl, new_proof=None):
    """Build a full Solution.lean variant."""
    out = _swap(_BASE, _IMPL_OLD, new_impl)
    if new_proof is not None:
        out = _swap(out, _PROOF_OLD, new_proof)
    return out


def _body(body):
    """A variant impl that keeps the frozen `Id.run do` signature."""
    return _SIG + body


# ---------------------------------------------------------------------------
# POSITIVE CONTROLS (soundness) — must VERIFY. Structurally different but
# behaviourally identical impls. Each ships with a proof that closes for its own
# shape; the theorem STATEMENT is byte-identical and no new lemma / axiom /
# sorry is introduced. Measured: all three close under the FROZEN tactic script
# (`cases path <;> cases hasFile <;> rfl`), because the exhaustive case split
# reduces each shape definitionally — so no proof authoring was needed and none
# was done.
# ---------------------------------------------------------------------------

# pos-spec-shaped-expression: the port of the nagini pos-control-expr /
# pos-control-oracle-echo pair, which collapse into one case on this carrier.
# Nagini's gold used two early-return guards and its controls reshaped that into
# a single boolean expression (and, separately, into a call to the grounded
# helper); here the single expression IS the spec's right-hand side, built from
# the same two pure helpers the spec names. Drops the `Id.run do` wrapper
# entirely, so it also shows the spec does not depend on the imperative encoding.
_POS_EXPR = """\
def implementation_providesMigrations
    (hasFile : Bool) (path : ModulePath) : Bool :=
  path.isPackage && (hasFile || path.isList)"""

# pos-constructor-match: the MIRROR of the case above, and the one that makes
# "the spec is pinned to a VALUE, not to a syntactic echo of its own helpers"
# a measured claim. It matches on the three `ModulePath` constructors directly
# and never mentions `isPackage` or `isList` at all — the two symbols the spec's
# right-hand side is written in terms of. If the clause were satisfiable only by
# re-spelling the spec's own helper applications, this shape would fail.
_POS_MATCH = """\
def implementation_providesMigrations
    (hasFile : Bool) (path : ModulePath) : Bool :=
  match path with
  | .noPath     => false
  | .listPath   => true
  | .customPath => hasFile"""

# pos-accept-first: the port of nagini pos-control-reorder. The frozen impl
# tests the two SKIP conditions first and falls through to acceptance; this
# tests the single ACCEPT condition first and falls through to skipping, i.e.
# the guard sequence run in the opposite direction. Same total function.
_POS_REORDER = _body("""\
  if path.isPackage && (hasFile || path.isList) then
    return true
  return false""")

# admiss-modeled-rows: the port of nagini admiss-f2p-discriminating-row. Nagini
# asserted, via a positive-control caller, that its PRECONDITION admits the
# F2P-shaped input and that the call returns True there. This carrier has no
# precondition to admit anything — `correct_providesMigrations` binds both inputs
# unconditionally and the folded `ModulePath` makes nagini's excluded rows
# unrepresentable — so the porting question is what the nagini case was really
# buying: that the spec, at the F2P-shaped point, demands acceptance rather than
# being vacuous or inverted there. That is asserted directly as in-body `have`s
# (nagini `Assert(...)` -> lean `have ... := by decide`) at BOTH decisive points
# of the sub-claim the change makes definite: the no-file-location package whose
# path is an ordinary list must be a source, and the no-file-location package
# whose path is a custom iterable must not. Impl body and frozen proof script are
# otherwise verbatim, so the only thing this case can fail on is a spec-shape
# regression at those two points.
#
# AUDIT REPAIR. The `have`s originally shipped here re-spelled the clause's
# RIGHT-HAND SIDE as a literal (`(ModulePath.listPath.isPackage && (false ||
# ModulePath.listPath.isList)) = true`) instead of naming
# `problem_spec_providesMigrations`. That is a restatement, not a reproof: the
# two `have`s were then closed tautologies about the two pure helpers and were
# entirely independent of the clause they claimed to pin, so the case verified
# for a reason that had nothing to do with the spec. MEASURED: with the clause
# regressed to the pre-change shape `result = (path.isPackage && hasFile)` —
# which inverts the very row this case names as decisive — the original `have`s
# still elaborated (exit 0), and with the clause weakened all the way to the
# vacuous `result = result` they still elaborated (exit 0). The rationale's
# claim that "the only thing this case can fail on is a spec-shape regression at
# those two points" was therefore false of the shipped case. The `have`s below
# apply `problem_spec_providesMigrations` at the two points instead, so the
# assertion is about the CLAUSE and not about a copy of its body: against the
# pre-change clause shape they fail (exit 1, `decide` proving `true =
# (ModulePath.listPath.isPackage && false)` false) and against the vacuous
# clause they fail (exit 1), while against the frozen clause they elaborate
# (exit 0). Note the second `have` is stated with `¬ ... true` rather than
# `... false`: it must pin that the clause FORBIDS acceptance at the
# placeholder point, which is the direction the nagini case was buying.
_ADMISS = _body("""\
  have _hProvides : problem_spec_providesMigrations
      false ModulePath.listPath true := by
    unfold problem_spec_providesMigrations; decide
  have _hSkips : ¬ problem_spec_providesMigrations
      false ModulePath.customPath true := by
    unfold problem_spec_providesMigrations; decide
  -- A module that is not a package cannot provide migrations.
  if !path.isPackage then
    return false
  -- A package with no file location whose path is a custom (non-list) iterable
  -- is an empty-directory placeholder, not a real migrations package.
  if !hasFile && !path.isList then
    return false
  return true""")


# ---------------------------------------------------------------------------
# UNIQUENESS RIVALS — must be REJECTED (else SPEC-TOO-WEAK). Each edits ONLY the
# impl region. Every one ships a `witness` that was SEEN to discriminate: built
# against the rival (elaborates) and against the frozen solution (fails, with
# `decide` reporting the negation false — i.e. gold satisfies the clause there).
# ---------------------------------------------------------------------------

# weak-no-file-location-skips: THE discriminating rival — the pre-change
# behaviour. Skips any package with no file location, whatever its package path.
# Wrong on exactly one row, (false, listPath). (Ports nagini
# weak-prepatch-discriminating-row.)
_WEAK_PREPATCH = _body("""\
  if !path.isPackage then
    return false
  if !hasFile then
    return false
  return true""")

# weak-provides-from-placeholder: drops the placeholder guard entirely, so every
# package is a source of migrations. Wrong on exactly (false, customPath).
# (Ports nagini weak-loads-namespace-pkg.)
_WEAK_PLACEHOLDER = _body("""\
  if !path.isPackage then
    return false
  return true""")

# weak-provides-from-non-package: drops the not-a-package guard, keeping only the
# placeholder guard. Wrong on exactly (true, noPath). (Ports nagini
# weak-loads-non-package.)
_WEAK_NONPKG = _body("""\
  if !hasFile && !path.isList then
    return false
  return true""")

# weak-always-provides: every module is a source. Wrong on three of six rows.
# (Ports nagini weak-always-true.)
_WEAK_ALWAYS = _body("  return true")

# weak-never-provides: no module is ever a source. Wrong on three of six rows.
# (Ports nagini weak-always-false.)
_WEAK_NEVER = _body("  return false")

# weak-list-polarity-flip: the path-shape test used with the WRONG polarity —
# a package with no file location is a source exactly when its path is NOT an
# ordinary list. Doubly wrong: it flips BOTH no-file-location package rows.
# (Ports nagini weak-list-polarity-flip.)
_WEAK_POLARITY = _body("""\
  if !path.isPackage then
    return false
  if !hasFile && path.isList then
    return false
  return true""")

# weak-ignores-file-location: NO nagini counterpart. Every ported rival above
# either honours the file-location signal or discards the path-shape signal;
# none keeps the path-shape test while dropping the file-location signal
# ENTIRELY. This one is a source exactly when the path is an ordinary list, so
# it is correct on all four rows a nagini rival probes and wrong only at
# (true, customPath) — a package that DOES expose a file location but whose path
# is a custom iterable. Isolates (C-file) on the one row where it is the only
# reason for acceptance.
_WEAK_IGNORE_FILE = _body("""\
  if !path.isList then
    return false
  return true""")

# weak-non-package-without-file: NO nagini counterpart. A tight near-miss that
# makes the not-a-package verdict depend on the file location: a non-package is
# a source exactly when it exposes NO file location. Wrong on exactly one row,
# (false, noPath) — the noPath constructor at the OTHER value of `hasFile` from
# weak-provides-from-non-package's (true, noPath), so it varies `hasFile` within
# a fixed `path`. Isolates (C-pkg) at a point weak-always-provides only reaches
# by being wrong everywhere.
_WEAK_NONPKG_NOFILE = _body("""\
  if !path.isPackage then
    return !hasFile
  if !hasFile && !path.isList then
    return false
  return true""")

# weak-accept-guard-inverted: NO nagini counterpart. A tight near-miss wrong on
# exactly (true, listPath) — the row where BOTH acceptance signals are present
# and so the only row on which they overlap. It rejects precisely that
# co-occurrence and is otherwise the frozen decision. Every other rival that is
# wrong there (weak-never-provides) is wrong on two further rows as well, so
# without this case the both-signals-present row is pinned only by a rival that
# breaks the clause wholesale.
_WEAK_ACCEPT_INV = _body("""\
  if hasFile && path.isList then
    return false
  if !path.isPackage then
    return false
  if !hasFile && !path.isList then
    return false
  return true""")


# --- Witness helper. Each reject case states the spec predicate directly at a
# concrete point of the six-point domain; the negation elaborates iff the rival's
# output contradicts the clause there. Both binders are finite and transparent,
# so `decide` computes both sides — no hypothesis is bound, hence no consistency
# question arises (there is nothing for the gate's `False`-probe to derive from).
# Checked in a file with the frozen obligations removed, so no tactic script can
# interfere.
def _witness(pt):
    return f"""\
example : ¬ problem_spec_providesMigrations {pt}
    (implementation_providesMigrations {pt}) := by
  unfold problem_spec_providesMigrations implementation_providesMigrations
  decide"""


# The doubly-wrong polarity rival is refuted at BOTH rows it inverts, in one
# statement: refuting it at only one would let its rationale claim an inversion
# the manifest never demonstrates.
_WITNESS_POLARITY = """\
example :
    (¬ problem_spec_providesMigrations false ModulePath.listPath
        (implementation_providesMigrations false ModulePath.listPath))
    ∧ (¬ problem_spec_providesMigrations false ModulePath.customPath
        (implementation_providesMigrations false ModulePath.customPath)) := by
  unfold problem_spec_providesMigrations implementation_providesMigrations
  decide"""


SPEC_TESTS = [
    # ------------------------------------------------------------- POSITIVES
    {
        "id": "pos-spec-shaped-expression",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(_POS_EXPR),
        "rationale": (
            "Ports nagini pos-control-expr and pos-control-oracle-echo, which "
            "collapse into one case on this carrier. A correct impl written as "
            "a single boolean expression — the clause's own right-hand side — "
            "dropping the imperative `Id.run do` wrapper the frozen impl uses. "
            "Because the clause is built from transparent helpers of the two "
            "binders rather than from an opaque answer-key, returning that "
            "expression is the CORRECT behaviour and not an ungrounded echo, "
            "which is why nagini shipped this shape as an honest positive too. "
            "Closes under the frozen tactic script (the exhaustive case split "
            "reduces it definitionally). If it fails => SPEC-TOO-STRONG."
        ),
    },
    {
        "id": "pos-constructor-match",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(_POS_MATCH),
        "rationale": (
            "The MIRROR of pos-spec-shaped-expression, and the control that "
            "makes 'the clause is pinned to a VALUE' a measured claim rather "
            "than an assertion. It decides by matching the three package-path "
            "constructors directly and never mentions either of the two pure "
            "helpers the clause's right-hand side is written in terms of. If "
            "the clause were satisfiable only by re-spelling its own helper "
            "applications, this shape would be rejected while "
            "pos-spec-shaped-expression passed. If it fails => SPEC-TOO-STRONG."
        ),
    },
    {
        "id": "pos-accept-first",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(_POS_REORDER),
        "rationale": (
            "Ports nagini pos-control-reorder. The frozen impl tests the two "
            "SKIP conditions first and falls through to acceptance; this tests "
            "the single ACCEPT condition first and falls through to skipping — "
            "the guard sequence run in the opposite direction, computing the "
            "same total function. Confirms the clause stays satisfiable under "
            "reordering. If it fails => SPEC-TOO-STRONG."
        ),
    },
    {
        "id": "admiss-modeled-rows",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl(_ADMISS),
        "rationale": (
            "Ports nagini admiss-f2p-discriminating-row. Nagini asserted that "
            "its precondition ADMITS the F2P-shaped input and that the call "
            "returns True there; this carrier has no precondition (the "
            "obligation binds both inputs unconditionally, and the folded "
            "package-path type makes nagini's excluded rows unrepresentable "
            "rather than excluded), so what ports is the underlying claim: at "
            "the F2P-shaped point the clause demands acceptance, and at its "
            "neighbour it demands skipping. Both are asserted in-body (nagini "
            "`Assert(...)` -> lean `have ... := by decide`) with the impl body "
            "and frozen proof script otherwise verbatim. The two `have`s APPLY "
            "`problem_spec_providesMigrations` at those points rather than "
            "re-spelling its right-hand side, so they are sensitive to the "
            "clause itself: measured to FAIL against the pre-change clause "
            "shape and against a vacuous clause, and to hold against the frozen "
            "one. That sensitivity is the case's whole content, so it is stated "
            "as a measurement and not as an expectation. If it fails => "
            "PRECOND-TOO-STRONG / spec-shape regression."
        ),
    },

    # ------------------------------------------------------------ UNIQUENESS
    {
        "id": "weak-no-file-location-skips",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_PREPATCH),
        "witness": _witness("false ModulePath.listPath"),
        "refinement": (
            "This IS the pre-change behaviour: skip whenever the module exposes "
            "no file location, without ever consulting the shape of its package "
            "path. Its faithful real patch is the unpatched repo, so the F2P "
            "test — which asserts that a regular package deprived of its file "
            "location still yields its two migrations — finds none of them and "
            "FAILS. A rival that verified here would be a true "
            "verify-does-not-imply-resolve break, since the spec would have "
            "failed to sense the very change the patch makes. Does NOT resolve."
        ),
        "rationale": (
            "Rejected by (C-list) at (hasFile = false, path = listPath): the "
            "clause demands true (a package with no file location whose path is "
            "an ordinary list IS a source), the rival returns false. This is "
            "the single row the change turns over, and the rival is wrong on "
            "that row ALONE. Witness at (false, listPath). If it verifies => "
            "SPEC-TOO-WEAK."
        ),
    },
    {
        "id": "weak-provides-from-placeholder",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_PLACEHOLDER),
        "witness": _witness("false ModulePath.customPath"),
        "refinement": (
            "Drops the placeholder guard entirely, so every package counts as a "
            "source. A faithful patch removing that guard would accept the "
            "empty-directory placeholder case — a package with no file location "
            "whose package path is a custom iterable — regressing the P2P tests "
            "that assert such a module stays unmigrated and that no migrations "
            "are discovered under it. Does NOT resolve."
        ),
        "rationale": (
            "Rejected by (C-list) at (hasFile = false, path = customPath): the "
            "clause demands false, the rival returns true. The exact opposite "
            "row from weak-no-file-location-skips, so the two together pin both "
            "directions of the sub-claim the change makes definite. Witness at "
            "(false, customPath). If it verifies => SPEC-TOO-WEAK."
        ),
    },
    {
        "id": "weak-provides-from-non-package",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_NONPKG),
        "witness": _witness("true ModulePath.noPath"),
        "refinement": (
            "Drops the not-a-package guard, keeping only the placeholder guard. "
            "A faithful patch without that guard treats a plain module — one "
            "that is not a package at all and so exposes no package path — as a "
            "source of migrations, and the subsequent traversal then has no "
            "package path to traverse. The P2P test that asserts an app whose "
            "migrations module is a plain file stays unmigrated FAILS. Does NOT "
            "resolve."
        ),
        "rationale": (
            "Rejected by (C-pkg) at (hasFile = true, path = noPath): the clause "
            "demands false for a non-package whatever its file location, the "
            "rival returns true. Witness at (true, noPath). If it verifies => "
            "SPEC-TOO-WEAK on the not-a-package sub-claim."
        ),
    },
    {
        "id": "weak-always-provides",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_ALWAYS),
        "witness": _witness("false ModulePath.noPath"),
        "refinement": (
            "Treats every module as a source. A faithful patch that always "
            "falls through to the migrated set would accept non-packages and "
            "empty-directory placeholders alike, breaking the P2P "
            "stays-unmigrated assertions and leaving the traversal with no "
            "package path on the non-package rows. Does NOT resolve."
        ),
        "rationale": (
            "Rejected by (C-pkg) at (hasFile = false, path = noPath), and wrong "
            "on three of the six rows. Supporting whole-clause attack: it "
            "establishes that the clause constrains the result at all on the "
            "skip rows, which the tighter single-row rivals then localize. "
            "Witness at (false, noPath). If it verifies => SPEC-TOO-WEAK."
        ),
    },
    {
        "id": "weak-never-provides",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_NEVER),
        "witness": _witness("true ModulePath.listPath"),
        "refinement": (
            "Treats no module as a source, so no app ever has migrations "
            "discovered. A faithful patch that always skips fails the F2P test "
            "and every migrations-loading P2P test in the suite. Does NOT "
            "resolve."
        ),
        "rationale": (
            "Rejected by (C-file) at (hasFile = true, path = listPath) — the "
            "ordinary regular-package row — and wrong on all three acceptance "
            "rows. The dual of weak-always-provides: together they show the "
            "clause constrains the result in both directions. Witness at "
            "(true, listPath). If it verifies => SPEC-TOO-WEAK."
        ),
    },
    {
        "id": "weak-list-polarity-flip",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_POLARITY),
        "witness": _WITNESS_POLARITY,
        "refinement": (
            "Inverts the path-shape test: among packages with no file location "
            "it accepts exactly those whose package path is NOT an ordinary "
            "list. A faithful patch with the path-shape test written at the "
            "wrong polarity would skip regular packages that merely lack a file "
            "location and accept the empty-directory placeholders — exactly "
            "backwards. The F2P test fails AND the placeholder P2P tests "
            "regress. Does NOT resolve."
        ),
        "rationale": (
            "Rejected by (C-list) on BOTH no-file-location package rows: at "
            "(false, listPath) the clause demands true and the rival returns "
            "false, and at (false, customPath) the clause demands false and the "
            "rival returns true. The witness asserts BOTH refutations in one "
            "statement — refuting only one would let this rationale claim an "
            "inversion the manifest never demonstrates. If it verifies => "
            "SPEC-TOO-WEAK."
        ),
    },
    {
        "id": "weak-ignores-file-location",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_IGNORE_FILE),
        "witness": _witness("true ModulePath.customPath"),
        "refinement": (
            "NO nagini counterpart. Keeps the path-shape test but discards the "
            "file-location signal entirely, accepting exactly the packages "
            "whose package path is an ordinary list. A faithful patch that "
            "dropped the file-location disjunct would change the verdict for a "
            "package that DOES expose a file location but whose package path is "
            "a custom iterable from source to skipped. The pre-change code "
            "accepted that module (it has a file location and is a package), so "
            "this is a regression of behavior that predates the change — and "
            "the problem statement's explicit promise is that the change does "
            "not alter behavior for ordinary environments at all. A verifying "
            "rival here would mean the spec permits silently narrowing the "
            "accepted set. Does NOT resolve."
        ),
        "rationale": (
            "Rejected by (C-file) at (hasFile = true, path = customPath): the "
            "clause demands true — a package that exposes a file location is a "
            "source whatever its path shape — and the rival returns false. This "
            "is the ONLY row on which the file-location signal is the sole "
            "reason for acceptance, so it is the only row that can isolate "
            "(C-file); every ported nagini rival either honours that signal or "
            "is wrong on the path-shape rows too, which is why this case has no "
            "counterpart there. It also varies `path` to customPath at "
            "hasFile = true, a combination no ported witness reaches. If it "
            "verifies => SPEC-TOO-WEAK on the file-location disjunct."
        ),
    },
    {
        "id": "weak-non-package-without-file",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_NONPKG_NOFILE),
        "witness": _witness("false ModulePath.noPath"),
        "refinement": (
            "NO nagini counterpart. A tight near-miss that makes the "
            "not-a-package verdict depend on the file location: a module that "
            "is not a package is accepted exactly when it exposes NO file "
            "location. A faithful patch of this shape does not implement the "
            "guard, whose whole point is that package-ness alone decides that "
            "row; it is unfaithful in precisely the direction the change is "
            "about, since it is the frozen-environment module — the one with no "
            "file location — that gets mis-accepted, and the traversal then has "
            "no package path to walk. Being wrong only on that row, it is not "
            "pinned by any currently-asserted test row (the suite's "
            "not-a-package fixture is an ordinary file and so exposes a file "
            "location), so this is a PARTIAL-DOMAIN attack on faithfulness "
            "rather than a claim about an existing assertion — stated plainly "
            "rather than overclaimed."
        ),
        "rationale": (
            "Rejected by (C-pkg) at (hasFile = false, path = noPath): the "
            "clause demands false for a non-package regardless of its file "
            "location, the rival returns true. Wrong on that row ALONE. It "
            "probes noPath at the OTHER value of `hasFile` from "
            "weak-provides-from-non-package's (true, noPath), so it varies "
            "`hasFile` within a fixed `path` — the binder-variation the "
            "coverage invariant asks for. It shares its input point with "
            "weak-always-provides and for the same reason (both return true "
            "where the clause demands false), but weak-always-provides reaches "
            "it only by being wrong on three rows; this rival demonstrates that "
            "(C-pkg) is pinned at that row on its own. If it verifies => "
            "SPEC-TOO-WEAK."
        ),
    },
    {
        "id": "weak-accept-guard-inverted",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_ACCEPT_INV),
        "witness": _witness("true ModulePath.listPath"),
        "refinement": (
            "NO nagini counterpart. A tight near-miss that rejects precisely "
            "the co-occurrence of the two acceptance signals — a package that "
            "exposes a file location AND whose package path is an ordinary list "
            "— and is otherwise the frozen decision. That is the ordinary "
            "regular-package configuration in every non-frozen environment, so "
            "a faithful patch of this shape skips the normal case: the F2P test "
            "and every migrations-loading P2P test fail. Does NOT resolve."
        ),
        "rationale": (
            "Rejected by (C-file) at (hasFile = true, path = listPath), the one "
            "row on which the two acceptance signals OVERLAP, and wrong on that "
            "row alone. Shares its input point with weak-never-provides and for "
            "the same reason (both return false where the clause demands true), "
            "but weak-never-provides is wrong on two further rows and so could "
            "be rejected anywhere; this rival shows the overlap row is pinned "
            "by itself, rather than only by a rival that breaks the clause "
            "wholesale. If it verifies => SPEC-TOO-WEAK on the both-signals "
            "row."
        ),
    },
]

# No opaque callee and no @ContractOnly-style axiom on this path
# (meta.axioms == [], no deep-model references): the introspection reads are
# modeled directly as the two binders. Nothing for the axiom lane to execute,
# and the axiom lane is G-AX's job regardless.
AXIOM_TESTS = []
