"""properties.py — G-PBT falsification battery for django__django-13820 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the elided ``prove_correct`` tactic body, is
changed — both regions the consumer spec view elides, so ``markers.same_spec``
holds and the ``prove_correct migrationsModuleLoadable`` obligation survives with
a byte-identical statement) and swaps in a candidate implementation; it is
checked by the real verifier. ``expect:"verify"`` passes iff (in scope AND
verifies); ``expect:"reject"`` passes iff (in scope AND does NOT verify AND its
refutation ``witness`` discriminates: the witness must elaborate against the
rival and FAIL against the frozen solution).

DEFENDED SURFACE (one contracted method, pure over three free boolean inputs):

  migrationsModuleLoadable (hasFile : Bool) (hasPath : Bool) (pathIsList : Bool)
      return (out : Bool)
    ensures out = loadable hasFile hasPath pathIsList

The method classifies an imported candidate module by three observations —
whether it advertises a concrete file location (``hasFile``), whether it is a
package exposing a search path (``hasPath``), and whether that search path is an
ordinary list (``pathIsList``) — into a single decision: is this module's
on-disk migrations directory scanned (``out = true``) or is the module skipped
(``out = false``). The sole ensures pins the whole outcome to the pure grounded
selector

  loadable hasFile hasPath pathIsList = hasPath && (hasFile || pathIsList)

which is a transparent boolean function of the method's own three arguments (the
``axioms`` region is empty; there is no opaque answer key to echo). So there is
one independent top-level clause, and it decides the outcome in BOTH directions
for every one of the eight input configurations — a rival that misclassifies ANY
configuration violates it. There is no slack.

The FAITHFUL input cube (the note in mapping.md §2 records that ``pathIsList`` is
unobservable when ``hasPath = false``, and the spec is total over the full
``Bool³`` cube, both legs ignoring ``pathIsList`` there):

  (hasFile, hasPath, pathIsList) -> loadable
  (F, F, *) -> F   not a package, skipped
  (T, F, *) -> F   not a package, skipped
  (F, T, F) -> F   package, no file location, non-list path => namespace, skip
  (F, T, T) -> T   package, no file location, list path      => the DISCRIMINATING
                                                                row (the F2P)
  (T, T, F) -> T   package with a file location, non-list path => scan
  (T, T, T) -> T   package with a file location, list path      => scan

All THREE input binders are free (no ``require`` clause) and the post-image must
hold for every value of each:
  * ``hasFile``    — module advertises a concrete file location;
  * ``hasPath``    — module is a package (exposes a search path);
  * ``pathIsList`` — that search path is an ordinary list.

ADVERSARIAL READ of the nagini classes on THIS carrier (the sibling has 9 SPEC
cases + an empty AXIOM lane; footer accounts for each one):
  * FRAME/PERMISSION-MUTATION — VACUOUS. The sibling notes all three inputs are
    immutable ``bool`` value parameters with no ``Acc(x,1/2)`` heap read, so the
    frame class is already N/A there. On this referentially-transparent carrier
    it is likewise vacuous: every parameter is an immutable value, the method
    declares no ``mut`` binder, there is no heap and no aliasing. No substitute
    probe is fabricated.
  * UNGROUNDED-ORACLE ECHO — N/A, exactly as the sibling records. ``loadable`` is
    a concrete ``def`` in the ``pure`` region computing the outcome from the
    method's own three arguments; the ``axioms`` region is empty, so there is no
    opaque answer key to echo. Echoing ``loadable`` IS the correct answer — the
    honest cheapest positive control (``pos-oracle``) does exactly that.
  * DIVERGENCE / NON-TERMINATION - the class is INAPPLICABLE to this impl and
    CLOSED BY THE SEMANTICS against any rival that manufactures it. The frozen
    impl is LOOP-FREE (straight-line ``let`` / ``if`` over immutable values, no
    loop and no recursion), so there is no control flow here to make diverge: a
    diverging rival cannot be obtained by mutating this body, it has to bring a
    loop of its own. When it does, the semantics refuse it. This bundle sets
    ``loom.semantics.termination "total"`` AND carries
    ``open TotalCorrectness``, and the ``open`` is the line that actually
    selects the semantics: both namespaces define
    ``WPGen.forWithInvariantLoop``, the later ``open`` wins, and the
    ``PartialCorrectness`` version takes a loop measure and DISCARDS it, so the
    two lines have to move together and they do here. Under the total scope a
    postcondition is claimed of ALL runs and not only of terminating ones, so a
    spliced loop owes a descent obligation ``measure b' < measure b``.
    Re-measured on this bundle with a real build: a
    ``while spin > 0 do spin := spin`` prefix carrying ``decreasing spin`` is
    REJECTED on the measure's own goal (``case «decreasing_1: spin» ... ⊢ spin
    < spin``). Dropping the clause rather than faking it is refused even
    earlier, by the elaborator's own check (``Decreasing annotations are
    required in total correctness semantics``). So divergence neither applies
    to this impl nor discharges the ``ensures`` clauses vacuously if a rival
    introduces it.
  * PARTIAL-DOMAIN / VALUE — the whole reject surface. The sibling's central
    leverage is a rival correct on most of the cube but wrong on ONE (or two)
    configurations, most importantly the discriminating frozen-package row
    (F, T, T) the whole gold change exists to fix. Each is ported: it corresponds
    to a faithful real patch that would NOT resolve the F2P, and the spec MUST
    reject it.

WITNESS MECHANICS ON THIS BUNDLE. The frozen impl is STRAIGHT-LINE (no loop) and
the return carrier is ``Bool``, whose postcondition is DECIDABLE with no opaque
callee, so the tester+``decide`` path is live and needs no ``deriving instance``.
Each reject rival carries a machine-checked refutation ``witness`` — one or more
Velvet tester statements ``migrationsModuleLoadableTester <hasFile> <hasPath>
<pathIsList> = false`` at concrete configurations, checked in a file whose
``prove_correct`` block has been stripped so no tactic script can mask the
verdict. The method carries NO ``require`` clause, so the witness omits
``prove_precondition_decidable_for``. Every argument is a concrete boolean
literal that ``decide`` reduces, so no witness binds a hypothesis and no
consistency probe is needed. Both halves were checked out-of-band with
``scripts/lean_verify.sh``: every witness ELABORATES against its rival (exit 0)
and FAILS against the frozen solution with ``decide`` PROVING the proposition
false (exit 1) — a semantic refutation of the concrete claim, not an unknown
identifier, a type error or a timeout — so each rejection is a genuine spec
refutation and not mechanical tactic breakage.

A rival wrong at more than one configuration is pinned at more than one point.
This is not decoration: the gate's discrimination test is rival-vs-gold, so a
witness at a point TWO rivals share passes it while attesting only to the shared
row. ``weak-list-polarity-flip`` therefore names its second, distinguishing row
as well (see that case).

AXIOM lane: EMPTY, exactly as the sibling. ``meta.json`` / mapping.md §3 declare
no consumed ``axiom`` and no deep-model reference; the three attribute
observations are concrete I-ops (language-level boolean primitives) modeled
directly and refinement-checked by ``conformance_check.py`` (G-CONF), not
axiomatized. Nothing in the proof rests on an axiom, and this gate ignores
``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "django__django-13820"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchor: the WHOLE frozen impl body, i.e. everything strictly
# ---- BETWEEN the method's `-- impl-start` / `-- impl-end` (marker lines
# ---- included). Every variant replaces exactly this block (and, for reshapes /
# ---- admissibility, the elided `prove_correct` tactic body), so each edit lies
# ---- wholly inside the impl / proof regions and same_spec holds by construction
# ---- (asserted by _swap: substring present AND unique in the file).
_IMPL = (
    "    -- impl-start\n"
    "    -- A module that is not a package contributes nothing; a package that\n"
    "    -- advertises no concrete file location and whose search path is not an\n"
    "    -- ordinary list is an implicit namespace package and is also skipped; every\n"
    "    -- other package is scanned.\n"
    "    let notPackage : Bool := !hasPath\n"
    "    let isNamespace : Bool := (!hasFile) && (!pathIsList)\n"
    "    let out : Bool :=\n"
    "      if notPackage then false\n"
    "      else\n"
    "        if isNamespace then false\n"
    "        else true\n"
    "    return out\n"
    "    -- impl-end"
)

assert _BASE.count(_IMPL) == 1, "method impl region drifted from expected text"

# The frozen proof, verbatim. A reshape that changes the impl's syntactic form
# may retune THIS block (elided from the spec view); rivals leave it as-is (the
# rejection is carried by the witness, not the tactic script).
_PROOF = "prove_correct migrationsModuleLoadable by\n  loom_solve"

assert _BASE.count(_PROOF) == 1, "proof region drifted from expected text"


def _impl(new_body):
    """Full Solution.lean variant with ONLY the impl body replaced."""
    return _swap(_BASE, _IMPL,
                 "    -- impl-start\n" + new_body + "\n    -- impl-end")


def _impl_reproved(new_body, new_proof):
    """Impl body replaced AND the proof retuned (for correct reshapes)."""
    return _swap(_impl(new_body), _PROOF, new_proof)


# ---- witness builder. The postcondition is decidable over a `Bool` return
# ---- carrier (no opaque callee), so the tester path is live: the tester
# ---- statement `migrationsModuleLoadableTester <hasFile> <hasPath> <pathIsList>
# ---- = false` says the extracted program's result violates the method's
# ---- postcondition at that concrete configuration. The method has NO `require`,
# ---- so `prove_precondition_decidable_for` is omitted. Checked in a file whose
# ---- `prove_correct` block is stripped, so no tactic script can mask the
# ---- verdict.
_TESTER = (
    "extract_program_for migrationsModuleLoadable\n"
    "prove_postcondition_decidable_for migrationsModuleLoadable\n"
    "derive_tester_for migrationsModuleLoadable\n\n"
)


def _witness(*calls):
    """Refutation witness at ONE OR MORE concrete configurations.

    A rival that is wrong at several points may be pinned at all of them. That
    matters for a rival whose wrongness at a SHARED point is indistinguishable
    from another rival's: a witness naming only the shared point discriminates
    against gold (the gate's requirement) but does not attest to what makes THIS
    rival distinct. Audit-measured: the `false true true` witness alone
    elaborates against BOTH weak-prepatch and weak-list-polarity-flip (exit 0
    each), so on its own it cannot tell them apart."""
    body = "\n\n".join(f"example : {c} = false := by\n  decide" for c in calls)
    return _TESTER + body + "\n"


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify. If a faithful correct impl cannot verify, the spec is
    # SPEC-TOO-STRONG. Each returns a value definitionally equal to the gold one,
    # so it closes under the frozen `loom_solve` (no reproof needed).
    # =====================================================================
    {
        "id": "pos-oracle",
        "kind": "soundness",
        "expect": "verify",
        # Cheapest honest impl: return the GROUNDED pure selector directly.
        # Because `loadable` is a transparent boolean function of the args (NOT an
        # opaque answer key), echoing it IS the correct behaviour, not an
        # ungrounded-oracle cheat. Ports the sibling's pos-control-oracle-echo.
        "module": _impl(
            "    let out : Bool := loadable hasFile hasPath pathIsList\n"
            "    return out"),
        "rationale": (
            "`loadable` is GROUNDED in the inputs "
            "(`hasPath && (hasFile || pathIsList)`); returning it is the correct "
            "answer, so this honest cheapest impl must verify against "
            "`out = loadable hasFile hasPath pathIsList`. There is no WRONG echo "
            "to build => UNGROUNDED-ORACLE N/A. If it fails => SPEC-TOO-STRONG. "
            "Ports the sibling pos-control-oracle-echo."),
    },
    {
        "id": "pos-expr",
        "kind": "soundness",
        "expect": "verify",
        # Reshape the gold two-guard nested `if` into a single boolean expression
        # written out inline. Same total function; the value flow is unchanged so
        # the frozen proof closes as-is. Ports the sibling pos-control-expr.
        "module": _impl(
            "    let out : Bool := hasPath && (hasFile || pathIsList)\n"
            "    return out"),
        "rationale": (
            "a correct impl written as one boolean expression (a different shape "
            "from the gold nested-guard form) must satisfy "
            "`out = loadable hasFile hasPath pathIsList`; the value is "
            "definitionally identical for every configuration. If it fails => "
            "SPEC-TOO-STRONG. Ports the sibling pos-control-expr."),
    },
    {
        "id": "pos-reorder",
        "kind": "soundness",
        "expect": "verify",
        # Branch-reorder: test the SCAN case first, then fall through to skip, in a
        # different order than the gold skip-first guards. Same total function.
        # Ports the sibling pos-control-reorder.
        "module": _impl(
            "    let out : Bool :=\n"
            "      if hasPath && (hasFile || pathIsList) then true\n"
            "      else false\n"
            "    return out"),
        "rationale": (
            "branch-reorder (SCAN case tested first) computing the same total "
            "function; a correct re-expression must verify against "
            "`out = loadable hasFile hasPath pathIsList`. If it fails => "
            "SPEC-TOO-STRONG on branch order. Ports the sibling pos-control-"
            "reorder."),
    },
    {
        "id": "pos-match-nested",
        "kind": "soundness",
        "expect": "verify",
        # Audit-added. The three ported positives all reduce to the gold value flow
        # by `rfl` — each is a boolean EXPRESSION over the same three atoms — so
        # none of them exercises a genuinely different program STRUCTURE. This one
        # does: it case-splits the carrier with nested `match` scrutinees instead of
        # computing a boolean, so the impl term is a matcher application rather than
        # an `&&`/`||` tree, and the ensures must be discharged through the
        # case-split rather than by conversion. It still closes under the FROZEN
        # `loom_solve` (no proof retuning), which is the strongest form this control
        # can take.
        "module": _impl(
            "    let out : Bool :=\n"
            "      match hasPath with\n"
            "      | false => false\n"
            "      | true  =>\n"
            "        match hasFile with\n"
            "        | true  => true\n"
            "        | false => pathIsList\n"
            "    return out"),
        "rationale": (
            "a correct impl that CASE-SPLITS on the inputs (nested `match`) rather "
            "than evaluating a boolean expression: the impl term is a matcher "
            "application, not definitionally an `&&`/`||` tree, so the obligation "
            "is discharged through the case analysis instead of by conversion. "
            "This is the positive control whose shape differs STRUCTURALLY and not "
            "just syntactically from the frozen impl — the other three positives "
            "are all expression reshapes that reduce to the gold value flow by "
            "`rfl`. It verifies under the frozen `loom_solve` unchanged. If it "
            "failed => SPEC-TOO-STRONG on program structure. Audit-added; no "
            "sibling counterpart."),
    },

    # =====================================================================
    # ADMISSIBILITY — RE-AIMED from the sibling admiss-f2p-discriminating-row.
    # That case asserted the F2P-shaped input (a regular package with no file
    # location and a list search path) satisfies the precondition and returns
    # True. This method carries NO `require` clause (total over the full Bool³
    # cube), so the classic "a normal input is admitted" probe is degenerate —
    # every configuration is in-domain. It is re-aimed at the residual
    # total-domain admissibility risk: that the decision is DEGENERATE at the
    # interesting point — a classifier that never separated the F2P scan-case from
    # the namespace skip-case would read like a live one. The in-region assert
    # pins that `loadable` genuinely forks between the two: it ranks the F2P
    # discriminating row (F, T, T) as SCAN (`= true`) yet ranks the namespace row
    # (F, T, F) as SKIP (`= false`). The rest of the impl is kept verbatim so the
    # ensures still discharges; the proof is retuned to also close the assert VC.
    # =====================================================================
    {
        "id": "admiss-decision-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl_reproved(
            "    assert (with_name_prefix `assert\n"
            "      (loadable false true true = true ∧ loadable false true false = false))\n"
            "    let notPackage : Bool := !hasPath\n"
            "    let isNamespace : Bool := (!hasFile) && (!pathIsList)\n"
            "    let out : Bool :=\n"
            "      if notPackage then false\n"
            "      else\n"
            "        if isNamespace then false\n"
            "        else true\n"
            "    return out",
            "prove_correct migrationsModuleLoadable by\n  loom_solve <;> decide"),
        "rationale": (
            "the decision is satisfiable AND non-degenerate at the F2P-shaped "
            "axis: `loadable` ranks the discriminating frozen-package row "
            "(no file location, list search path) as SCAN (`= true`) yet ranks "
            "the namespace row (no file location, non-list search path) as SKIP "
            "(`= false`), so the classifier really does fork between them. The "
            "in-region assert must discharge (else the decision would be "
            "degenerate / the obligation vacuous); the impl is kept verbatim so "
            "the ensures still discharges too. Re-aimed from the sibling "
            "admiss-f2p-discriminating-row, whose empty-precondition probe has no "
            "non-degenerate counterpart on this total-domain carrier."),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec that
    # MUST be rejected, each with a machine-checked refutation witness at a
    # concrete configuration and the refinement argument that its faithful real
    # patch would NOT resolve the F2P. The three input binders (hasFile, hasPath,
    # pathIsList) are varied across the witnesses.
    # =====================================================================
    {
        "id": "weak-prepatch-discriminating-row",
        "kind": "uniqueness",
        "expect": "reject",
        # THE discriminating-row rival = the pre-patch behaviour. Skips whenever
        # the module advertises no file location, ignoring whether its search path
        # is a list. Wrong on exactly (F, T, T): returns false (skip) where the
        # spec demands true (scan).
        "module": _impl(
            "    let out : Bool := if !hasPath then false else if !hasFile then false else true\n"
            "    return out"),
        "refinement": (
            "this is the pre-patch logic: skip whenever the module advertises no "
            "file location, regardless of whether its search path is an ordinary "
            "list. Its faithful real counterpart is the unchanged repo, which "
            "skips a regular package that omits a file location but keeps a list "
            "search path — exactly the frozen-environment package the F2P "
            "constructs (file location deleted, list search path retained). The "
            "F2P test then asserts that package's migrations DO load; the rival "
            "skips it, so the F2P STILL FAILS. It would NOT resolve — the precise "
            "change the spec senses."),
        "rationale": (
            "REJECT from `out = loadable hasFile hasPath pathIsList`: at "
            "(hasFile=F, hasPath=T, pathIsList=T) the spec demands true but the "
            "rival returns false. Refuted at the F2P discriminating configuration "
            "`false true true`. Supporting near-miss carrying the strongest "
            "refinement (it is the literal pre-patch; wrong on exactly this one "
            "row). If it verified => SPEC-TOO-WEAK. Ports the sibling "
            "weak-prepatch-discriminating-row."),
        "witness": _witness(
            "migrationsModuleLoadableTester false true true"),
    },
    {
        "id": "weak-loads-namespace-pkg",
        "kind": "uniqueness",
        "expect": "reject",
        # Namespace-package rival: loads EVERY package, dropping the namespace
        # skip. Wrong on exactly (F, T, F): returns true (scan) for a package with
        # no file location AND a non-list search path — i.e. it scans PEP-420
        # namespace packages.
        "module": _impl(
            "    let out : Bool := if !hasPath then false else true\n"
            "    return out"),
        "refinement": (
            "drops the namespace-package skip entirely: a faithful patch that "
            "scanned every package would scan implicit namespace packages (no "
            "file location, non-list search path), regressing the behaviour that "
            "keeps a namespace package unmigrated. The namespace PASS_TO_PASS "
            "assertions (a namespace package contributes no migrations) then fail. "
            "It would NOT resolve."),
        "rationale": (
            "REJECT from `out = loadable hasFile hasPath pathIsList`: at "
            "(hasFile=F, hasPath=T, pathIsList=F) the spec demands false but the "
            "rival returns true. Refuted at `false true false` — varies "
            "`pathIsList` to false against the prepatch witness. If it verified "
            "=> SPEC-TOO-WEAK. Ports the sibling weak-loads-namespace-pkg."),
        "witness": _witness(
            "migrationsModuleLoadableTester false true false"),
    },
    {
        "id": "weak-loads-non-package",
        "kind": "uniqueness",
        "expect": "reject",
        # Non-package rival: skips only the (no file location AND non-list path)
        # case, scanning everything else — including a plain module that is NOT a
        # package. Wrong on (T, F, F): returns true (scan) where the spec demands
        # false (a non-package has nothing to scan).
        "module": _impl(
            "    let out : Bool := if (!hasFile) && (!pathIsList) then false else true\n"
            "    return out"),
        "refinement": (
            "drops the not-a-package guard, so a plain module that is not a "
            "package (e.g. a migrations module that is a single file, not a "
            "directory) is treated as a scan target. A faithful patch of this "
            "shape would attempt to iterate a search path on an object that "
            "exposes none, crashing / mis-loading; the PASS_TO_PASS that keeps a "
            "non-package module unmigrated fails. It would NOT resolve."),
        "rationale": (
            "REJECT from `out = loadable hasFile hasPath pathIsList`: at "
            "(hasFile=T, hasPath=F, pathIsList=F) the spec demands false "
            "(`hasPath = false` => not loadable) but the rival returns true. "
            "Refuted at `true false false` — the only reject witness with "
            "hasPath=false, so that binder is varied; also varies `hasFile` to "
            "true. If it verified => SPEC-TOO-WEAK. Ports the sibling "
            "weak-loads-non-package."),
        "witness": _witness(
            "migrationsModuleLoadableTester true false false"),
    },
    {
        "id": "weak-always-true",
        "kind": "uniqueness",
        "expect": "reject",
        # Always-scan rival: returns true for EVERY configuration, including both
        # non-package rows and the namespace row. Wrong on 3 of the 6 faithful
        # rows. Supporting near-miss carrying a real refinement.
        "module": _impl(
            "    let out : Bool := true\n"
            "    return out"),
        "refinement": (
            "scans every module. A faithful patch that always fell through to the "
            "scan branch would scan non-packages and namespace packages alike, "
            "breaking the unmigrated-apps PASS_TO_PASS assertions and attempting "
            "to iterate a search path on a non-package. It would NOT resolve."),
        "rationale": (
            "REJECT from `out = loadable hasFile hasPath pathIsList` on every "
            "skip row. Refuted at (hasFile=F, hasPath=F, pathIsList=T) — a "
            "non-package row where the spec demands false but the constant rival "
            "returns true; this configuration also varies `pathIsList` to true "
            "against the two non-package/namespace witnesses. Supporting "
            "partial-domain. If it verified => SPEC-TOO-WEAK. Ports the sibling "
            "weak-always-true."),
        "witness": _witness(
            "migrationsModuleLoadableTester false false true"),
    },
    {
        "id": "weak-always-false",
        "kind": "uniqueness",
        "expect": "reject",
        # Always-skip rival: returns false for EVERY configuration, so it never
        # scans ANY module — including the F2P discriminating row and both normal
        # scan rows. Wrong on 3 of the 6 faithful rows. Supporting near-miss.
        "module": _impl(
            "    let out : Bool := false\n"
            "    return out"),
        "refinement": (
            "skips every module, so NO app has its migrations scanned — the F2P "
            "test (which asserts a regular frozen-environment package's "
            "migrations DO load) fails, as does every scan-path PASS_TO_PASS. It "
            "would NOT resolve."),
        "rationale": (
            "REJECT from `out = loadable hasFile hasPath pathIsList` on every scan "
            "row. Refuted at (hasFile=T, hasPath=T, pathIsList=T) — a normal "
            "scan row where the spec demands true but the constant rival returns "
            "false; this configuration holds all three binders true, the point no "
            "other reject witness probes. Supporting partial-domain. If it "
            "verified => SPEC-TOO-WEAK. Ports the sibling weak-always-false."),
        "witness": _witness(
            "migrationsModuleLoadableTester true true true"),
    },
    {
        "id": "weak-list-polarity-flip",
        "kind": "uniqueness",
        "expect": "reject",
        # Subtle partial-domain: uses `pathIsList` with the WRONG polarity in the
        # namespace guard — skips a package iff it has no file location AND its
        # path IS a list, the inverse of the correct qualification. Correct on the
        # file-location rows but DOUBLY wrong on the two no-file-location package
        # rows: it now SKIPS the frozen regular package (F, T, T)->false and SCANS
        # the namespace package (F, T, F)->true — exactly backwards.
        "module": _impl(
            "    let out : Bool := if !hasPath then false else if (!hasFile) && pathIsList then false else true\n"
            "    return out"),
        "refinement": (
            "inverts the list test: a faithful patch qualifying the namespace "
            "skip on the search path BEING a list (instead of NOT being one) would "
            "SKIP frozen regular packages (list search path, no file location) and "
            "SCAN namespace packages (non-list search path, no file location) — "
            "exactly backwards. The F2P fails (the frozen regular package is "
            "skipped) AND the namespace assertion regresses. It would NOT "
            "resolve."),
        "rationale": (
            "REJECT from `out = loadable hasFile hasPath pathIsList` on BOTH "
            "(hasFile=F, hasPath=T, pathIsList=T) (spec true, rival false) and "
            "(hasFile=F, hasPath=T, pathIsList=F) (spec false, rival true). "
            "Refuted at BOTH wrong rows, `false true true` AND `false true "
            "false`. The second point is what makes this a DISTINCT impl rather "
            "than a duplicate of weak-prepatch: weak-prepatch is CORRECT at "
            "(F, T, F) (it skips there, as the spec demands), whereas this rival "
            "wrongly scans. A witness naming only the shared `false true true` "
            "row elaborates against weak-prepatch too and so attests only to the "
            "row they share; pinning (F, T, F) as well is what attributes the "
            "`pathIsList`-polarity abuse to THIS rival. If it verified => "
            "SPEC-TOO-WEAK. Ports the sibling weak-list-polarity-flip."),
        # TWO points: the shared F2P row and the row that separates this rival
        # from weak-prepatch. Audit-measured: the (F, T, F) half FAILS against
        # weak-prepatch (exit 1, `decide` proved the proposition false), which is
        # what demonstrates the two rivals are genuinely different impls.
        "witness": _witness(
            "migrationsModuleLoadableTester false true true",
            "migrationsModuleLoadableTester false true false"),
    },
    {
        "id": "weak-requires-list-path",
        "kind": "uniqueness",
        "expect": "reject",
        # Audit-added. The pre-existing rivals leave the (T, T, F) row — a package
        # that DOES advertise a file location but whose search path is not an
        # ordinary list — attacked only by the blunt `weak-always-false` constant.
        # This rival is the targeted near-miss there: it qualifies the scan on the
        # search path being a list and drops the file-location disjunct entirely,
        # so it is correct on five of the six faithful rows (including the F2P row
        # (F, T, T)) and wrong on exactly (T, T, F).
        "module": _impl(
            "    let out : Bool := if !hasPath then false else if !pathIsList then false else true\n"
            "    return out"),
        "refinement": (
            "requires an ordinary-list search path of EVERY package, dropping the "
            "file-location disjunct. A faithful patch of this shape would skip a "
            "package that advertises a concrete file location but exposes a "
            "non-list search path — a module that both the pre- and post-change "
            "behaviour scan — so it regresses a scan-path assertion that passes "
            "before the change. It would NOT resolve: it converts the fix into a "
            "different, narrower rule rather than the intended widening."),
        "rationale": (
            "REJECT from `out = loadable hasFile hasPath pathIsList`: at "
            "(hasFile=T, hasPath=T, pathIsList=F) the spec demands true "
            "(`hasFile` alone satisfies the disjunct) but the rival returns false. "
            "Refuted at `true true false`, the cube row no other TARGETED rival "
            "probes — it is a genuine near-miss (correct on the F2P row and on "
            "both namespace/non-package rows), so unlike weak-always-false its "
            "rejection is attributable to the `hasFile` disjunct specifically. If "
            "it verified => SPEC-TOO-WEAK: the spec would not be sensing that a "
            "file-location package is scanned irrespective of its path shape. "
            "Audit-added; no sibling counterpart."),
        "witness": _witness(
            "migrationsModuleLoadableTester true true false"),
    },
]


# ===========================================================================
# NAGINI -> VELVET ACCOUNTING.
#
# The sibling battery has 9 SPEC cases + an empty AXIOM lane: 3 soundness
# positives, 1 admissibility, 5 uniqueness rivals. The sibling models the SAME
# boolean classifier (`treat_as_migration_source(is_package, file_is_set,
# path_is_ordinary_list)`), grounded in a transparent `@Pure is_source` helper,
# with a precondition `Implies(not is_package, not path_is_ordinary_list)`. This
# backend models the identical decision as the pure `loadable`, with NO
# precondition (total over the full Bool³ cube — see mapping.md §2, which pins
# totality over the cube), and the same three observations as free `Bool` inputs.
# The whole decision surface carries across intact; only the sibling's
# precondition (and the frame prose about immutable value scalars) has no
# counterpart, being degenerate here.
#
#   sibling case                       -> here                          disposition
#   -----------------------------------------------------------------------------
#   pos-control-expr                   -> pos-expr                       PORTED
#   pos-control-oracle-echo            -> pos-oracle                     PORTED
#   pos-control-reorder                -> pos-reorder                    PORTED
#   (no counterpart)                   -> pos-match-nested                AUDIT-ADDED
#   admiss-f2p-discriminating-row      -> admiss-decision-nondegenerate  RE-AIMED
#   weak-prepatch-discriminating-row   -> weak-prepatch-discriminating-row  PORTED
#   weak-loads-namespace-pkg           -> weak-loads-namespace-pkg       PORTED
#   weak-loads-non-package             -> weak-loads-non-package         PORTED
#   weak-always-true                   -> weak-always-true               PORTED
#   weak-always-false                  -> weak-always-false              PORTED
#   weak-list-polarity-flip            -> weak-list-polarity-flip        PORTED
#   (no counterpart)                   -> weak-requires-list-path        AUDIT-ADDED
#   AXIOM_TESTS ([])                   -> (none)                         DROPPED (empty)
#
# 12 velvet SPEC cases: 4 soundness, 1 admissibility, 7 uniqueness. 9 ported
# (5 rivals + 3 positives + the axiom-echo positive), 1 re-aimed (admissibility),
# 2 audit-added (weak-requires-list-path, pos-match-nested).
# NOTHING omitted: this is the rare port with full carrier parity, because the
# velvet spec IS the sibling's grounded `is_source` decision function — the
# Lean-family bundle models exactly the purely-functional core the sibling's spec
# pins, so every sibling SPEC case has a live counterpart.
#
# AUDIT-ADDED (weak-requires-list-path): the ported rivals left the (T, T, F) row
#   — a package with a file location but a non-list search path — attacked only by
#   the blunt `weak-always-false` constant, which is wrong on three rows at once
#   and so attributes nothing to the `hasFile` disjunct in particular. The added
#   rival is the targeted near-miss there: correct on five of the six faithful
#   rows, wrong on exactly (T, T, F). Audit-measured: rival build exit 1 against
#   the frozen proof, witness exit 0 on the rival and exit 1 on gold with `decide`
#   proving `migrationsModuleLoadableTester true true false = false` false.
#
# AUDIT-ADDED (pos-match-nested): the three ported positives are all boolean
#   EXPRESSION reshapes that reduce to the gold value flow by conversion, so none
#   of them shows the spec tolerates a different program STRUCTURE. The added
#   positive case-splits the carrier with nested `match` scrutinees instead, and
#   verifies under the FROZEN `loom_solve` unchanged (audit-measured exit 0).
#   Recorded limit found while landing it: a THREE-discriminant `match` with mixed
#   wildcard/literal Bool patterns (`| _, false, _ => ...`) does NOT close, failing
#   with a `(kernel) application type mismatch` on the generated
#   `<method>.match_1.splitter` under loom_solve, and identically under
#   `<;> simp_all`, `<;> decide`, `<;> grind` and an explicit `cases` split. It
#   reproduces on a 12-line standalone method with no repo content, and the
#   equivalent SINGLE-discriminant and nested forms both verify — so it is a
#   verifier/tactic limitation on multi-discriminant Bool matcher splitters, NOT a
#   spec-too-strong finding. The nested form above is the faithful structural
#   reshape that lands; see the audit notes.
#
# RE-AIMED (admissibility): the sibling asserts its precondition admits the
#   F2P-shaped input and the call returns True. This method has NO `require`
#   clause and no permission surface, so that probe is degenerate (every input is
#   in-domain). It is re-aimed at the residual total-domain risk — that the
#   decision is DEGENERATE at the interesting point — via an in-region assert that
#   `loadable` genuinely forks between the F2P scan-case (F, T, T)->true and the
#   namespace skip-case (F, T, F)->false.
#
# VACUOUS (frame/permission-mutation): the sibling already records this class as
#   N/A — all three inputs are immutable bool value scalars with no Acc(x,1/2)
#   heap read. On this referentially-transparent carrier it is likewise vacuous:
#   no `mut` binder, no heap, no aliasing. No substitute is fabricated.
# NONE (divergence): the sibling carries no diverge-*/nonterm-*/weak-diverge case,
#   so there is nothing to port. (Nor would the class be a spec hole here: this
#   bundle sets `set_option loom.semantics.termination "total"`, under which a
#   postcondition is claimed of ALL runs and every loop owes a strictly
#   decreasing measure, so a diverging rival is REJECTED rather than verifying
#   vacuously. An earlier version of this note called the bundle `partial` and
#   said such a rival would verify; that is withdrawn, all 500 velvet bundles set
#   `"total"`. What would still block a case is the witness path: a diverging
#   rival's module does not compile, so no witness can elaborate against it.)
#   None written, none claimed dropped.
# DROPPED (AXIOM_TESTS): the sibling's AXIOM_TESTS is already empty (no consumed
#   axiom, no deep-model reference — the three observations are I-ops checked by
#   G-CONF). The axiom lane is G-AX's job and this gate ignores AXIOM_TESTS
#   regardless.
#
# CLAUSE / BINDER / POINT COVERAGE of the reject witnesses.
#   * The sole ensures clause `out = loadable hasFile hasPath pathIsList` is
#     attacked in BOTH directions: rivals that wrongly SKIP a loadable module
#     (weak-prepatch, weak-always-false, weak-requires-list-path,
#     weak-list-polarity-flip at (F,T,T)) and rivals that wrongly SCAN a skip
#     module (weak-loads-namespace-pkg, weak-loads-non-package, weak-always-true,
#     weak-list-polarity-flip at (F,T,F)). And it is DEFENDED by the three
#     positives + the admissibility control.
#   * Both disjuncts of `hasFile || pathIsList` are separately load-bearing:
#     weak-requires-list-path drops the `hasFile` disjunct (refuted at
#     `true true false`) and weak-prepatch drops the `pathIsList` disjunct
#     (refuted at `false true true`), so neither can be removed from the spec
#     without a rival slipping through.
#   * All three input binders vary across the reject witnesses, and the variation
#     is MEANINGFUL — each listed point changes the spec's own verdict relative to
#     the rival that names it, so no two spellings stand for the same point:
#       hasFile     — false (prepatch, namespace, always-true, polarity-flip),
#                     true (non-package, always-false, requires-list);
#       hasPath     — true (prepatch, namespace, always-false, polarity-flip,
#                     requires-list), false (non-package, always-true);
#       pathIsList  — true (prepatch, always-true, always-false, polarity-flip),
#                     false (namespace, non-package, polarity-flip,
#                     requires-list).
#     No binder is held fixed by every witness.
#   * Reject witness points — ALL SIX faithful cube rows are now named, so the
#     ensures is refuted at every configuration on which some rival is wrong:
#       `false true true`   prepatch, polarity-flip  (spec T, rival F)
#       `false true false`  namespace, polarity-flip (spec F, rival T)
#       `true false false`  non-package              (spec F, rival T)
#       `false false true`  always-true              (spec F, rival T)
#       `true true true`    always-false             (spec T, rival F)
#       `true true false`   requires-list            (spec T, rival F)
#     `false true true` is shared by prepatch and polarity-flip, which fail
#     identically there. That shared point alone does NOT separate them — measured:
#     the `false true true` witness elaborates against BOTH rivals (exit 0 each).
#     Polarity-flip therefore names its SECOND row `false true false` too, where
#     prepatch is CORRECT: measured, that half FAILS against prepatch (exit 1,
#     `decide` proved the proposition false). So the pair is distinguished by
#     machine-checked evidence, not by prose.
#
# WITNESS MECHANICS: the postcondition is decidable over a `Bool` return carrier
#   (no opaque callee), so every witness uses the tester+`decide` path at concrete
#   boolean literals — no hypothesis bound, so no consistency probe is needed. All
#   seven re-checked with scripts/lean_verify.sh during the audit: rival build
#   exit 0, gold build exit 1 with `decide` PROVING the tester proposition false
#   (a semantic refutation, not a missing identifier / type error / timeout).
AXIOM_TESTS = []
