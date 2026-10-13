"""properties.py — G-PBT falsification battery for django__django-16612 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed —
both of which the consumer spec view elides, so ``markers.same_spec`` holds and
the ``prove_correct appendSlashRedirect`` obligation survives with a
byte-identical statement) and swaps in a candidate implementation; it is checked
by the real verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness must ELABORATE against the rival and FAIL
against the frozen solution).

DEFENDED SURFACE (one contracted method over two code-point sequences):

  appendSlashRedirect (encodedPath : List Char) (encodedQuery : List Char)
      return (out : List Char)
    ensures out = redirectTarget encodedPath encodedQuery   -- the only clause

with ``redirectTarget`` a fully-unfolded ``def`` in the ``pure`` region:

  redirectTarget p q =
    p ++ (if p.getLast? = some '/' then [] else ['/'])
      ++ (if q = [] then [] else '?' :: q)

so the single clause pins THREE independent structural sub-behaviours of the
assembled redirect destination:

  * PATH-PREFIX: the encoded path is preserved verbatim as the prefix of the
    result;
  * TRAILING-SLASH: a single '/' is appended EXACTLY when the path does not
    already end in one (both sub-domains — path already slashed vs not);
  * QUERY-PRESERVED: when a query is present it is carried into the result
    VERBATIM behind a single '?' introducer, and when absent nothing is
    appended (this is the behaviour the change adds — the pre-change destination
    dropped the query entirely);
  * ASSEMBLY-ORDER: the three components are concatenated in exactly the
    sequence path ++ slash ++ query, so pinning their contents is not enough —
    the sequence is pinned too (attacked by weak-swap-slash-query-order, whose
    component VALUES are bit-identical to the frozen impl's).

``redirectTarget`` is GROUNDED in the inputs (a total fold over both arguments);
the ``axioms`` region is empty (``redirectTarget`` is a deep A-reference
validated == the real destination builder by axiom_check.py / G-AX, NOT a
consumed answer key), so there is no wrong echo to build — any echo would have to
RECOMPUTE the grounded fold, i.e. do the work — and the ungrounded-oracle probe
is replaced by three honest positive controls. The TWO INPUT BINDERS are
``encodedPath`` and ``encodedQuery``; both are load-bearing (path drives the
prefix and the trailing-slash decision; query drives the preserved-query branch).

THE CARRIER IS FULLY TRANSPARENT. ``redirectTarget`` computes on ``Char``
literals, so a witness reaches the impl through Velvet's extractor
(``extract_program_for appendSlashRedirect`` gives ``appendSlashRedirectExec p q
= NonDetT.run (appendSlashRedirect p q)``) and states ``appendSlashRedirectExec p
q ≠ DivM.res (redirectTarget p q)`` at concrete literals, with ``decide`` closing
the residual (no opaque leaf, no carrier conditioning, so no witness binds a
hypothesis and there is no joint-satisfiability obligation). Unlike a loop-based
solution, the FROZEN impl here is straight-line and equal to ``redirectTarget``
on the whole domain, so the discrimination comes from the INPUT POINT, not from a
stuck loop fixpoint: gold satisfies ``out = redirectTarget …`` at every input, so
any ``…Exec p q ≠ DivM.res (redirectTarget p q)`` FAILS against gold (``decide``
proves the negation false) while ELABORATING against a rival that diverges at
``(p, q)``. Both halves were checked out-of-band with ``scripts/lean_verify.sh``
(rival elaborates exit 0, gold fails exit 1) for every reject case.

ADVERSARIAL READ of the nagini classes on this carrier:
  * FRAME / PERMISSION-MUTATION — VACUOUS. The nagini sibling carries TWO
    MANDATORY rivals here (``fm-write-path`` stores ``path[m-1] := 47`` and
    ``fm-write-query`` does ``query.append(63)``, each through a reference held at
    ``Acc(list_pred(·), 1/2)``) because a store needs full permission. Lean and
    Velvet are referentially transparent: ``encodedPath`` / ``encodedQuery`` are
    immutable ``List Char`` values, this bundle declares NO ``mut`` binder over
    any input, and there is no heap and no aliasing — so there is no read-only
    input to overwrite and no substitute probe to build. Not fabricated (per the
    porting map: this class is vacuous on Lean/Velvet). AUDIT CONFIRMATION, built
    rather than argued: the sibling's store written directly
    (``encodedPath := encodedPath.dropLast ++ ['/']``) does not COMPILE —
    "``encodedPath`` cannot be mutated, only variables declared using
    ``let mut`` can be mutated" — so the class is blocked by the LANGUAGE, and a
    reject case over it would attribute its rejection to a parse error rather
    than to the contract. The nearest legal analogue (a local ``let mut`` shadow
    copy, mutated) VERIFIES, confirming no write is observable through an input
    binder.
  * DIVERGENCE / NON-TERMINATION: CLOSED BY THE SEMANTICS, so there is nothing to
    ship, and the class is neither vacuous nor a hole. TWO earlier reasons recorded
    here are both withdrawn. The original port said "a diverging impl cannot be
    written at all" because the frozen body is a straight-line assembly; that is
    false, since a rival may rewrite the whole impl region and splice a diverging
    prefix. A later revision then said that this bundle declares
    ``set_option loom.semantics.termination "total"`` and that under it a
    non-terminating impl satisfies every ``ensures`` clause VACUOUSLY and VERIFIES,
    a known spec hole affecting a cohort of 401 velvet bundles. That is exactly
    inverted: vacuous satisfaction is the ``partial`` disposition, no velvet bundle
    sets ``partial`` (all 500 set ``"total"`` and open ``TotalCorrectness``), and
    the ``set_option`` elaborator itself runs ``openScope `TotalCorrectness``
    (``Loom/MonadAlgebras/WP/Options.lean:169-186``), so the setting and the scope
    cannot disagree. Under ``total`` a postcondition is claimed of ALL runs, so the
    verifier demands a decreasing measure on every loop AND discharges its descent.
    Measured on this cell, with each proof reduced to a bare ``loom_solve``: a
    spliced loop that CARRIES a measure its body never changes
    (``let mut q : Nat := 1; while q > 0 / invariant 0 ≤ q / done_with q = 0 /
    decreasing q do q := q``) is REJECTED at exit 1 on the measure's own goal,
    ``case «decreasing_1: q»``, residual ``⊢ q < q``; a loop with no measure at all
    is refused earlier still by the elaborator (``Decreasing annotations are
    required in total correctness semantics``). The first of those is the decisive
    build, since the second alone could be dismissed as a linter. So no divergence
    rival verifies, nothing is escalated, and no reject case is shipped for a
    mechanical reason rather than a spec one: the refusal fires on the ``method``
    command, so the rival's module never compiles and the witness the gate derives
    from it cannot elaborate, which records ``witness-unproven`` (INCONCLUSIVE).
    The nagini sibling carries no ``diverge-*`` case to port regardless.
  * ADMISSIBILITY — APPLIES, and is now SHIPPED (``admiss-f2p-nondegenerate``).
    SECOND-AUDIT CORRECTION: the prior pass recorded this lane as vacuous
    because "this bundle declares NO ``require`` clause, so there is no
    precondition to admit". That reason is REJECTED. The absence of a
    precondition is not what makes the lane vacuous; the analogue of
    PRECOND-TOO-STRONG on a total carrier is the obligation being UNSATISFIABLE
    or DEGENERATE at exactly an F2P-shaped input, which no other lane tests: the
    positive controls all discharge the obligation UNIVERSALLY, which is a
    strictly weaker fact than that its post-image at the F2P-shaped point is the
    value the behaviour actually requires. A universally-quantified clause can be
    satisfiable everywhere while its image at the interesting point is a
    degenerate collapse, and nothing else in this battery would notice. So the
    shipped case discharges, BY EVALUATION and in-region before the frozen
    obligation closes verbatim, that at an F2P-shaped input (a path WITHOUT a
    trailing slash carrying a NON-EMPTY query) the post-image is (a) exactly the
    slash-terminated, query-preserving destination and (b) DISTINCT from the
    empty-query image at the same path — i.e. non-degenerate in the query
    component, which is the component this specification pins. The assert is
    load-bearing, not decoration: the same case with a FALSE claim about the same
    point (the destination written without its '/' separator) leaves
    ``⊢ False`` on the ``admiss_1`` goal and fails to build.
  * SPEC-TOO-WEAK PROBES beyond the shipped rivals (second audit, built): a
    query truncated at 3 characters (correct on EVERY query any shipped witness
    probes, since all are length <= 2) is REJECTED, exit 1 — so the spec pins the
    whole query, not a bounded prefix, and the shipped rivals' short queries are
    not hiding a length-threshold hole. A slash decision testing whether the path
    CONTAINS '/' anywhere rather than ending in one is REJECTED, exit 1. Feeding
    the assembled result back through the model with an empty query is REJECTED,
    exit 1. Nothing admitted a wrong impl, so no spec hole was found on this side.
  * SPEC-TOO-STRONG PROBES beyond the shipped controls (second audit, built): a
    correct impl that case-splits the EMPTY path explicitly before the
    trailing-slash test VERIFIES, exit 0 (proof `rcases encodedPath … <;> simp
    [redirectTarget]`); a correct impl whose guard is the BEq test
    `(p.getLast? == some '/') = true` rather than propositional equality VERIFIES,
    exit 0 (`simp [redirectTarget, beq_iff_eq]`). So the clause is over-fit
    neither to the empty-path edge nor to the spelling of the equality test.
  * PARTIAL-DOMAIN / VALUE — APPLIES; the heart of the port. All five nagini
    partial-domain rivals re-express directly onto the structural clauses of
    ``redirectTarget``, and the audit added two more (a PATH-PREFIX rival and an
    ASSEMBLY-ORDER rival) covering sub-behaviours the port left unattacked.
  * UNGROUNDED-ORACLE ECHO — N/A. ``redirectTarget`` is a total ``def`` over the
    method's own inputs; there is no answer key to echo. Replaced by the three
    honest positive controls (the direct grounded return, a branch reshape, and
    a slash test computed via a provably-but-not-definitionally-equal accessor).

AXIOM lane: EMPTY (``meta.json`` declares no consumed ``axiom``; ``redirectTarget``
is a deep A-reference validated == the real destination builder by axiom_check.py
— that is G-AX's job, and this gate ignores ``AXIOM_TESTS`` regardless).
"""
from pathlib import Path

INSTANCE = "django__django-16612"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Anchors. Each lies wholly inside a region the spec view elides (the impl body
# between -- impl-start / -- impl-end, or the prove_correct tactic body) and is
# unique in Solution.lean (both facts asserted at load by _swap). The `let slash`
# / `let query` prefixes distinguish the impl-region conditionals from the same
# arithmetic inside the `redirectTarget` pure def, so each anchor is unique.
# Editing only these keeps markers.same_spec True and the prove_correct
# appendSlashRedirect statement byte-identical.
# ---------------------------------------------------------------------------

# The trailing-slash decision (impl region only — the `let slash` prefix makes it
# unique w.r.t. the identical arithmetic in the pure def).
_SLASH = (
    "    let slash : List Char :=\n"
    "      if encodedPath.getLast? = some '/' then ([] : List Char) else ['/']\n"
)

# The query-preservation decision (impl region only).
_QUERY = (
    "    let query : List Char :=\n"
    "      if encodedQuery = [] then ([] : List Char) else '?' :: encodedQuery\n"
)

# The final ASSEMBLY line (impl region only): how the three components are
# ordered and concatenated. Distinct from _SLASH / _QUERY, which decide the
# component VALUES — this anchor is what the PATH-PREFIX and component-ORDER
# rivals need, since a rival that mangles the prefix or reorders the
# concatenation leaves both component decisions untouched.
_ASSEMBLE = "    let result := encodedPath ++ slash ++ query\n"

# The impl-region OPENING marker. The admissibility case splices an in-region
# `assert` immediately after it, ahead of the frozen assembly, so the method's
# own obligation still discharges over the untouched body.
_IMPL_START = "    -- impl-start\n"

# The WHOLE executable body (between and including the markers). The direct
# positive control replaces it with a bare grounded return.
_IMPL = (
    "    -- impl-start\n"
    "    let slash : List Char :=\n"
    "      if encodedPath.getLast? = some '/' then ([] : List Char) else ['/']\n"
    "    let query : List Char :=\n"
    "      if encodedQuery = [] then ([] : List Char) else '?' :: encodedQuery\n"
    "    let result := encodedPath ++ slash ++ query\n"
    "    return result\n"
    "    -- impl-end"
)
assert _BASE.count(_IMPL) == 1, "impl-block anchor drift — re-sync _IMPL"

# The frozen proof body (tactic script only; elided from the spec view). When the
# impl returns the model directly there is nothing left for the trailing
# `simp [redirectTarget]` to do ("No goals"), so the direct control retunes the
# proof to a bare `loom_solve`.
_PROOF = (
    "prove_correct appendSlashRedirect by\n"
    "  loom_solve\n"
    "  simp [redirectTarget]"
)
assert _BASE.count(_PROOF) == 1, "proof anchor drift"
_PROOF_BARE = "prove_correct appendSlashRedirect by\n  loom_solve"


# ---- witness preamble. The spec is a `method` CONTRACT over a fully-transparent
# ---- carrier, so a witness reaches the impl through Velvet's extractor:
# ---- `appendSlashRedirectExec p q` is `NonDetT.run (appendSlashRedirect p q)`;
# ---- `≠ DivM.res (redirectTarget p q)` says the impl's output contradicts the
# ---- postcondition at that concrete input. Checked in a file whose
# ---- `prove_correct` block is stripped, so no tactic script can mask the
# ---- verdict. Every argument is a concrete literal so `decide` reduces the
# ---- extracted program; gold equals `redirectTarget` at every input, so the
# ---- same witness fails on gold — the required discrimination.
_EXTRACT = "extract_program_for appendSlashRedirect\n\n"


def _witness(p: str, q: str) -> str:
    return _EXTRACT + (
        f"example : appendSlashRedirectExec {p} {q} ≠ "
        f"DivM.res (redirectTarget {p} {q}) := by\n"
        "  unfold appendSlashRedirectExec appendSlashRedirect\n"
        "  simp [NonDetT.run, pure]\n"
        "  decide\n"
    )


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify (else the single clause is SPEC-TOO-STRONG).
    # =====================================================================
    {
        "id": "pos-control-direct-model",
        "kind": "soundness",
        "expect": "verify",
        # Cheapest honest correct impl: return the grounded pure model directly,
        # no branch splitting. `out` IS `redirectTarget encodedPath encodedQuery`,
        # so the ensures holds on the whole domain; the loop-of-branches is gone,
        # so the trailing `simp [redirectTarget]` has no goal and the reproof is a
        # bare `loom_solve`.
        "module": _swap(
            _swap(_BASE, _IMPL,
                  "    -- impl-start\n"
                  "    let result := redirectTarget encodedPath encodedQuery\n"
                  "    return result\n"
                  "    -- impl-end"),
            _PROOF, _PROOF_BARE),
        "rationale": (
            "the post-image `redirectTarget encodedPath encodedQuery` is GROUNDED "
            "in the inputs (a total fold, no opaque answer key), so returning it "
            "directly is the honest cheapest CORRECT impl. `out` IS that model, so "
            "the sole clause `out = redirectTarget …` holds on the whole domain; "
            "the reproof is `loom_solve`. If this fails to verify the clause is "
            "SPEC-TOO-STRONG (over-fit to the branch-assembly shape). Also shows "
            "the spec is not echo-vulnerable: any wrong constant/echo would fail "
            "`out = redirectTarget …`. (Sibling: pos-control-demorgan-slash — a "
            "structurally-different correct impl.)"),
    },
    {
        "id": "pos-control-reshape-branches",
        "kind": "soundness",
        "expect": "verify",
        # Structurally different but behaviourally identical: both conditionals are
        # rewritten with the guards NEGATED and the arms swapped
        # (`if p = s then [] else ['/']`  ==  `if p ≠ s then ['/'] else []`), the
        # De-Morgan-style reshape of the sibling's `needs_slash` control. The
        # assembled result is identical for every input, so `out = redirectTarget …`
        # still discharges under the FROZEN proof script with no retune.
        "module": _swap(
            _swap(
                _BASE, _SLASH,
                "    let slash : List Char :=\n"
                "      if encodedPath.getLast? ≠ some '/' then ['/'] else ([] : List Char)\n"),
            _QUERY,
            "    let query : List Char :=\n"
            "      if encodedQuery ≠ [] then '?' :: encodedQuery else ([] : List Char)\n"),
        "rationale": (
            "structurally different CORRECT reshape: both conditionals are "
            "rewritten with the guard NEGATED and the arms swapped (`if p = s then "
            "[] else ['/']` == `if p ≠ s then ['/'] else []`), logically identical "
            "to the frozen decision — the De-Morgan-style reshape of the sibling's "
            "`needs_slash` local. The assembled result is byte-identical for every "
            "input, so `out = redirectTarget …` still discharges under the frozen "
            "proof. A faithful reshape MUST verify, else the clause is over-fit to "
            "the branch FORM => SPEC-TOO-STRONG. (Sibling: pos-control-demorgan-"
            "slash.)"),
    },

    # =====================================================================
    # ADMISSIBILITY — SECOND-AUDIT ADDED. The port shipped no case in this lane
    # and justified the omission with "no `require` clause, so no precondition to
    # admit". That is the disallowed reason: on a TOTAL carrier the analogue of
    # PRECOND-TOO-STRONG is the obligation being unsatisfiable or DEGENERATE at
    # exactly an F2P-shaped input. The three positive controls discharge the
    # clause UNIVERSALLY, which does not establish that its post-image at the
    # F2P-shaped point is the value the behaviour requires rather than a
    # collapse — so this lane tests something no other case here does.
    #
    # The in-region `assert` is discharged BY EVALUATION (`decide`) at a fully
    # concrete F2P-shaped input — a path that does NOT already end in '/' and a
    # NON-EMPTY query — and it claims two things:
    #   (a) the post-image is exactly the slash-terminated, query-preserving
    #       destination (satisfiable, and satisfiable at the RIGHT value); and
    #   (b) it is DISTINCT from the empty-query image at the same path, i.e. the
    #       obligation is non-degenerate in the query component — the component
    #       this specification pins. Without (b), (a) alone would be consistent
    #       with a post-image that ignores the query.
    # The frozen assembly is kept verbatim underneath so the method's own
    # `ensures` still discharges; the proof is retuned only to clear the extra
    # assert goal, which the spec view elides. The assert is LIVE: the same case
    # with a false claim about the same point (destination written without its
    # '/' separator) leaves `⊢ False` on the `admiss_1` goal, exit 1.
    # =====================================================================
    {
        "id": "admiss-f2p-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _swap(_BASE, _IMPL_START,
                  _IMPL_START
                  + "    assert (with_name_prefix `admiss\n"
                    "      (redirectTarget ['a'] ['i', 'd'] = ['a', '/', '?', 'i', 'd'] ∧\n"
                    "       redirectTarget ['a'] ['i', 'd'] ≠ redirectTarget ['a'] ([] : List Char)))\n"),
            _PROOF,
            "prove_correct appendSlashRedirect by\n"
            "  loom_solve\n"
            "  all_goals first\n"
            "    | decide\n"
            "    | simp [redirectTarget]"),
        "rationale": (
            "the obligation is SATISFIABLE and NON-DEGENERATE at an F2P-shaped "
            "input — a path that does not already end in '/' carrying a "
            "non-empty query. Discharged by evaluation in-region, ahead of the "
            "frozen assembly: the post-image is exactly the slash-terminated "
            "destination with the query preserved behind its '?' introducer, AND "
            "it is DISTINCT from the empty-query image at the same path, so the "
            "clause genuinely discriminates the query-carrying case rather than "
            "collapsing to a query-independent value. This is the total-carrier "
            "analogue of PRECOND-TOO-STRONG: the positive controls discharge the "
            "clause universally, which is strictly weaker than pinning its image "
            "at the point the behaviour cares about. If this cannot verify the "
            "obligation is unsatisfiable exactly where it matters. The impl is "
            "kept verbatim so the method's own `ensures` discharges too; the "
            "assert is live (the same claim written with the '/' separator "
            "omitted leaves `⊢ False` and fails). (Sibling: "
            "admiss-f2p-domain-reachable, re-aimed from fractional-permission "
            "satisfiability onto post-image non-degeneracy.)"),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec that
    # MUST be rejected, each with a machine-checked refutation witness at a DISTINCT
    # concrete input and the refinement argument for why its faithful real
    # counterpart would NOT resolve the failing test. Each rival edits only the
    # `let slash` / `let query` binding, keeping the straight-line assembly so its
    # extracted program `decide`s over the concrete literal.
    # =====================================================================

    # ---- QUERY-PRESERVED clause: drop the query entirely (the pre-change bug) ----
    {
        "id": "weak-drop-query",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _QUERY,
                        "    let query : List Char := ([] : List Char)\n"),
        "refinement": (
            "this is the pre-change shape: the destination is assembled from the "
            "path and trailing slash only, and the query is DROPPED. The whole "
            "point of the fix is to preserve the query in the redirect; the failing "
            "scenario that redirects a slash-less path carrying a query and asserts "
            "the query survives in the destination would instead get a "
            "query-stripped destination — so it would NOT resolve. Correct on the "
            "empty-query sub-domain."),
        "rationale": (
            "REJECT from `out = redirectTarget …` via the QUERY-PRESERVED clause: "
            "with the query never appended, a non-empty query satisfies the rival "
            "but not `redirectTarget` (which appends `'?' :: q`). Refuted at "
            "`encodedPath=['a']`, `encodedQuery=['b']` — a non-empty query the "
            "rival strips. Varies `encodedQuery` to a non-empty run."),
        "witness": _witness("['a']", "['b']"),
    },

    # ---- QUERY-PRESERVED clause: append the query without the '?' introducer ----
    {
        "id": "weak-drop-qmark",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _QUERY,
                        "    let query : List Char :=\n"
                        "      if encodedQuery = [] then ([] : List Char) else encodedQuery\n"),
        "refinement": (
            "a faithful counterpart that concatenated the query WITHOUT the '?' "
            "separator would run the path, slash and query together into one token; "
            "the redirect destination would be malformed (the query would not be "
            "parsed as a query string) and the failing scenario asserting the exact "
            "destination string would get the wrong string — so it would NOT "
            "resolve. Correct on the empty-query sub-domain."),
        "rationale": (
            "REJECT from `out = redirectTarget …` via the QUERY-PRESERVED clause: "
            "`redirectTarget` pins the query behind a single '?' introducer "
            "(`'?' :: q`); this rival omits it. Refuted at `encodedPath=['a']`, "
            "`encodedQuery=['x', 'y']` — a length-2 query so the missing introducer "
            "is unambiguous. Varies `encodedQuery` to a multi-char run."),
        "witness": _witness("['a']", "['x', 'y']"),
    },

    # ---- TRAILING-SLASH clause: never append the slash ----
    {
        "id": "weak-drop-slash",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _SLASH,
                        "    let slash : List Char := ([] : List Char)\n"),
        "refinement": (
            "never appending the trailing slash produces the wrong destination for "
            "a path that does not already end in one — exactly the F2P inputs, an "
            "admin path WITHOUT the trailing slash. The failing scenario asserts a "
            "redirect to the slash-terminated URL; a slash-less destination would "
            "NOT resolve. Correct only when the path already ends in '/'."),
        "rationale": (
            "REJECT from `out = redirectTarget …` via the TRAILING-SLASH clause: "
            "`redirectTarget` appends `['/']` when the path does not end in '/'; "
            "this rival never appends it. Refuted at `encodedPath=['a']` (does not "
            "end in '/'), `encodedQuery=[]` — isolating the slash decision on the "
            "empty-query sub-domain the query rivals never probe."),
        "witness": _witness("['a']", "([] : List Char)"),
    },

    # ---- TRAILING-SLASH clause: append the slash unconditionally ----
    {
        "id": "weak-always-slash",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _SLASH,
                        "    let slash : List Char := ['/']\n"),
        "refinement": (
            "appending '/' unconditionally double-slashes a path that ALREADY ends "
            "in one, emitting a destination with a trailing '//'. A faithful "
            "counterpart would issue a redirect to a doubly-slashed URL, which "
            "regresses the already-slashed sub-domain the existing tests pin — so "
            "it would NOT resolve. Correct only when the path lacks a trailing "
            "slash."),
        "rationale": (
            "REJECT from `out = redirectTarget …` via the TRAILING-SLASH clause "
            "(opposite sub-domain): `redirectTarget` appends `[]` when the path "
            "already ends in '/'; this rival still appends `['/']`. Refuted at "
            "`encodedPath=['a', '/']` (ends in '/'), `encodedQuery=[]` — the "
            "already-slashed sub-domain no other rival drives, so `encodedPath`'s "
            "trailing character is demonstrated load-bearing on both sides."),
        "witness": _witness("['a', '/']", "([] : List Char)"),
    },

    # ---- QUERY-PRESERVED clause: drop the FIRST query character ----
    {
        "id": "weak-drop-first-query-char",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _QUERY,
                        "    let query : List Char :=\n"
                        "      if encodedQuery = [] then ([] : List Char) else '?' :: encodedQuery.drop 1\n"),
        "refinement": (
            "dropping the first query code point mangles every non-empty query "
            "(e.g. a query beginning with a key loses its leading character), so "
            "the preserved query in the destination is corrupt. The failing "
            "scenario asserting the exact query survives would get a truncated "
            "query — so it would NOT resolve. Correct on the empty-query "
            "sub-domain."),
        "rationale": (
            "REJECT from `out = redirectTarget …` via the QUERY-PRESERVED clause: "
            "`redirectTarget` preserves the query verbatim (`'?' :: q`); this rival "
            "emits `'?' :: q.drop 1`, losing the first character. Refuted at "
            "`encodedPath=['p']`, `encodedQuery=['i', 'd']` — a length-2 query so "
            "the dropped first char is observable (gold keeps `id`, the rival keeps "
            "`d`). A distinct multi-char query point from weak-drop-qmark."),
        "witness": _witness("['p']", "['i', 'd']"),
    },

    # ---- PATH-PREFIX clause: the encoded path is NOT preserved verbatim ----
    # AUDIT-ADDED. The battery as ported attacked only TRAILING-SLASH and
    # QUERY-PRESERVED; the third declared sub-behaviour (PATH-PREFIX) had no
    # rival at all and was defended only by the positive controls, i.e. only
    # from the SPEC-TOO-STRONG side. A spec that pinned the slash and query
    # components but let the prefix drift would have passed the battery
    # unchanged. This rival edits the ASSEMBLY rather than either component
    # decision, so it is reachable only through the _ASSEMBLE anchor.
    {
        "id": "weak-mangle-path-prefix",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _ASSEMBLE,
                        "    let result := encodedPath.dropLast ++ ['/'] ++ slash ++ query\n"),
        "refinement": (
            "this rival OVERWRITES the last code point of the encoded path with "
            "'/' instead of appending after it, so the destination addresses a "
            "different resource than the one requested — the final path segment "
            "is truncated by one character. A faithful counterpart would redirect "
            "to a neighbouring (usually nonexistent) URL, so the scenario "
            "asserting the destination is the requested path plus a trailing "
            "slash would get a corrupted path and would NOT resolve. Correct only "
            "on the empty path and on paths whose last two code points are both "
            "'/'."),
        "rationale": (
            "REJECT from `out = redirectTarget …` via the PATH-PREFIX clause, "
            "which no other rival attacks: `redirectTarget` carries "
            "`encodedPath` into the result VERBATIM as the prefix; this rival "
            "emits `encodedPath.dropLast ++ ['/']`, losing the final code point. "
            "Refuted at `encodedPath=['a', 'b']` (length 2, so the dropped last "
            "char is observable and the path does not already end in '/'), "
            "`encodedQuery=['z']`. A distinct input point from every other "
            "reject case, and the only one whose path is length 2 without a "
            "trailing slash."),
        "witness": _witness("['a', 'b']", "['z']"),
    },

    # ---- ASSEMBLY ORDER: right components, wrong sequence ----
    # AUDIT-ADDED. Every ported rival alters a component's VALUE; none altered
    # the ORDER in which the three are concatenated. A spec that pinned each
    # component's contents as a multiset but not their sequence would have
    # passed the battery unchanged, so the ordering was an untested claim.
    {
        "id": "weak-swap-slash-query-order",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _ASSEMBLE,
                        "    let result := encodedPath ++ query ++ slash\n"),
        "refinement": (
            "both components are computed EXACTLY as the frozen impl computes "
            "them — the defect is purely the order they are concatenated in, so "
            "the trailing slash lands after the query instead of before the '?'. "
            "A faithful counterpart would emit a destination whose slash is "
            "inside the query string rather than terminating the path, so the "
            "path is still slash-less and the query carries a spurious trailing "
            "character; the scenario asserting the exact destination would NOT "
            "resolve. Correct on the empty-query sub-domain and on already-"
            "slashed paths."),
        "rationale": (
            "REJECT from `out = redirectTarget …` via the component ORDER, which "
            "no other rival attacks: `redirectTarget` fixes the sequence "
            "path ++ slash ++ query, and this rival permutes the last two while "
            "leaving both component VALUES bit-identical to gold. That isolates "
            "ordering from content — the five ported rivals all alter a "
            "component's value, so none of them would fail if the spec pinned "
            "only the multiset of components. Refuted at `encodedPath=['q', 'x']` "
            "(slash-less, so `slash` is non-empty and the swap is observable), "
            "`encodedQuery=['k']` (non-empty, so `query` is non-empty too — both "
            "must be non-empty for a permutation to be visible)."),
        "witness": _witness("['q', 'x']", "['k']"),
    },

    # ---- AUDIT-ADDED positive: a slash test that is NOT definitionally equal ----
    {
        "id": "pos-control-slash-via-reverse-head",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _swap(_BASE, _SLASH,
                  "    let slash : List Char :=\n"
                  "      if encodedPath.reverse.head? = some '/' then ([] : List Char) else ['/']\n"),
            _PROOF,
            "prove_correct appendSlashRedirect by\n"
            "  loom_solve\n"
            "  simp [redirectTarget, List.head?_reverse]"),
        "rationale": (
            "AUDIT-ADDED third positive control, strictly stronger than "
            "pos-control-reshape-branches: that reshape only negates a guard and "
            "swaps the arms, which `simp` normalises, so it is close to "
            "definitionally equal to the frozen decision and demonstrates little. "
            "This one decides the trailing slash by a DIFFERENT COMPUTATION — "
            "`encodedPath.reverse.head?` instead of `encodedPath.getLast?` — "
            "which is provably but NOT definitionally equal (the proof needs the "
            "`List.head?_reverse` bridge lemma, so `simp [redirectTarget]` alone "
            "does not close it). A faithful correct impl that reaches the last "
            "element the other way round MUST still verify; if it could not, the "
            "clause would be over-fit to the frozen accessor => SPEC-TOO-STRONG. "
            "Together with the reshape and the direct-model control this defends "
            "soundness at three distinct distances from the frozen shape."),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery ships 9 SPEC cases (1
# soundness positive, 1 admissibility, 2 MANDATORY frame-mutation rivals, 5
# partial-domain rivals) plus a 1-case AXIOM lane. The sibling contracts
# `build_append_slash_redirect(path, query) -> List[int]` over two read-only
# `List[int]` code-point sequences held at fractional permission, with a fold
# oracle `redirect_target` grounded in the inputs. This bundle models the SAME
# purely-functional destination assembly DEEPLY (`redirectTarget` over the
# `List Char` carrier) with a single grounded `ensures out = redirectTarget …`,
# so the positive control and all five partial-domain rivals port near 1:1; the
# two frame cases are genuinely vacuous, and the admissibility case is vacuous.
#
#   sibling case                  kind          -> here                         disposition
#   -----------------------------------------------------------------------------------------
#   pos-control-demorgan-slash    soundness     -> pos-control-direct-model     RE-SHAPED
#                                                  (+ pos-control-reshape-branches ADDED)
#   admiss-f2p-domain-reachable   admissibility -> admiss-f2p-nondegenerate     RE-AIMED
#   fm-write-path                 uniqueness    -> (none)                       VACUOUS
#   fm-write-query                uniqueness    -> (none)                       VACUOUS
#   pd-drop-query                 uniqueness    -> weak-drop-query              PORTED
#   pd-drop-qmark                 uniqueness    -> weak-drop-qmark              PORTED
#   pd-drop-slash                 uniqueness    -> weak-drop-slash              PORTED
#   pd-always-slash               uniqueness    -> weak-always-slash            PORTED
#   pd-drop-first-query-char      uniqueness    -> weak-drop-first-query-char   PORTED
#   AXIOM_TESTS (1)               axiom         -> (none)                       DROPPED (G-AX)
#
# 5 uniqueness ported, 1 soundness re-shaped + 1 added; 2 frame vacuous; axiom
# lane dropped. A first independent AUDIT added 2 further uniqueness rivals
# (weak-mangle-path-prefix, weak-swap-slash-query-order) and a third soundness
# control (pos-control-slash-via-reverse-head) — see AUDIT NOTE under BINDER /
# CLAUSE COVERAGE. A SECOND independent audit then re-derived every case from
# scratch and landed the missing ADMISSIBILITY case (admiss-f2p-nondegenerate),
# which the port had dropped for a reason that does not hold — for 11 SPEC cases
# (3 soundness, 1 admissibility, 7 uniqueness), i.e. all three of the directions
# this gate exists to test: SPEC-TOO-STRONG (soundness), SPEC-TOO-WEAK
# (uniqueness), and PRECOND-TOO-STRONG / degenerate-at-F2P (admissibility).
#
# SECOND-AUDIT REBUILDS (every number below is an observed exit code, not an
# expectation). All 10 pre-existing variants rebuilt standalone: the 3 positives
# exit 0, all 7 rivals exit 1 — and each rival's exit 1 is a SEMANTIC residual
# (an unsolved `ensures_1` goal stating the concrete equation that fails), not a
# tactic-shape breakage. All 7 witnesses rebuilt on both sides: rival exit 0,
# gold exit 1, every gold-side error a plain `decide` evaluation of the concrete
# claim. FORGERY test (mandatory claim-flip) run on all 7: asserting the OPPOSITE
# of each witness inverts BOTH exit codes exactly (flipped-on-gold exit 0,
# flipped-on-rival exit 1, the latter erroring `decide proved that the
# proposition <gold value> = redirectTarget … is false`). So each gold-side exit
# code TRACKS THE CLAIM rather than being a fixed artefact of the file, which is
# what makes it admissible evidence — no case here is hollow.
#
# RE-SHAPED (pos-control-demorgan-slash -> pos-control-direct-model): the sibling's
#   positive rewrites the slash decision via De Morgan into an explicit
#   `needs_slash` local. On this carrier the maximally-different correct impl is a
#   loop-free direct return of the grounded model `redirectTarget …` (proof
#   retuned to bare `loom_solve`); a second, branch-PRESERVING correct reshape
#   (pos-control-reshape-branches) is ADDED — it negates BOTH conditional guards
#   and swaps the arms (the direct De-Morgan analogue of the sibling), which keeps
#   the assembled value byte-identical and discharges under the FROZEN proof with
#   no retune. So the soundness surface is defended both from a completely
#   different shape AND from a minimal in-body edit. Both verified to build.
# PORTED (the five partial-domain rivals): each re-expresses DIRECTLY onto a
#   structural sub-clause of `redirectTarget`. pd-drop-query -> weak-drop-query
#   (the exact pre-change bug: query dropped; refuted on a non-empty query).
#   pd-drop-qmark -> weak-drop-qmark (query concatenated without the '?'
#   introducer). pd-drop-slash -> weak-drop-slash (trailing slash never appended;
#   refuted on a slash-less path). pd-always-slash -> weak-always-slash (slash
#   appended unconditionally; refuted on an already-slashed path). pd-drop-first-
#   query-char -> weak-drop-first-query-char (first query char dropped). Each
#   refinement argument carries over verbatim: a faithful counterpart with that
#   defect emits a destination the failing scenarios reject, so it would NOT
#   resolve.
# RE-AIMED (admiss-f2p-domain-reachable -> admiss-f2p-nondegenerate): the sibling
#   asserts an F2P-shaped input satisfies its half-permission Requires. This
#   bundle declares no `require` clause, so the permission reading does not port
#   — but the LANE does. SECOND-AUDIT CORRECTION: the prior pass concluded from
#   the missing precondition that the lane was vacuous and shipped nothing, while
#   noting that a probe of this shape does elaborate. Both halves of that are
#   wrong as a disposition. "No precondition" is not the test; the total-carrier
#   analogue of PRECOND-TOO-STRONG is the obligation being unsatisfiable or
#   DEGENERATE at exactly an F2P-shaped input, and the fact that a probe
#   elaborates is a reason to SHIP it, not to drop it. Nor is it a tautology
#   about the pure def: the claim is checked as an in-region `assert` that the
#   method's own proof must discharge alongside its `ensures`, and it is live —
#   the same claim with the '/' separator omitted leaves `⊢ False` on the
#   `admiss_1` goal and the build fails (exit 1, re-derived). What the shipped
#   case adds over the three positive controls is direction: they discharge the
#   clause UNIVERSALLY, which does not pin the post-image at the F2P-shaped point
#   to the value the behaviour requires, nor rule out a post-image that ignores
#   the query component entirely. Non-degeneracy against the empty-query image at
#   the same path is exactly that missing claim.
# VACUOUS (fm-write-path, fm-write-query): the sibling carries these MANDATORY
#   because `path` / `query` are held at Acc(list_pred(·), 1/2) and a rival can
#   illegally store into them (`path[m-1] := 47`, `query.append(63)`). This
#   backend is referentially transparent and declares no `mut` binder —
#   `encodedPath` / `encodedQuery` are immutable values with no heap footprint —
#   so there is no read-only input to overwrite and no substitute probe. Not
#   fabricated (porting map: this class is vacuous on Lean/Velvet).
#   AUDIT CONFIRMATION (built, not argued): a rival attempting the sibling's
#   store directly — `encodedPath := encodedPath.dropLast ++ ['/']` in the impl
#   region — does not merely fail the spec, it fails to COMPILE:
#   "error: `encodedPath` cannot be mutated, only variables declared using
#   `let mut` can be mutated". So the class is blocked at the language level, not
#   by the spec, and a reject case over it would attribute its rejection to a
#   parse error rather than to the contract. The nearest legal analogue — a local
#   `let mut p := encodedPath; p := p ++ ['X']` shadow copy — VERIFIES (exit 0),
#   confirming a write that cannot be observed through any input binder. Note the
#   frozen signature declares no `mut` binder at all, so the spec_guide's
#   `mut`-frame obligation (pin an unchanged `mut` parameter with
#   `ensures xOld = x`) has no unframed parameter to bite on here.
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job (axiom_check.py validates the
#   deep A-reference `redirectTarget` == the real destination builder composed
#   with the two real percent-encoders); this bundle consumes no axiom `ensures`,
#   and the gate ignores AXIOM_TESTS regardless.
#
# DIVERGENCE / NON-TERMINATION: the sibling carries no such case to port. AUDIT
#   CORRECTION — the original port justified the omission by "a diverging impl
#   cannot be written" (the frozen body is straight-line). That is wrong: a rival
#   owns the whole impl region and can splice a diverging prefix. A later revision
#   then gave a second wrong reason: that this bundle is `partial`, so a diverging
#   impl VERIFIES vacuously and could not be declared `expect="reject"` at all,
#   citing a cohort of 401 `partial` bundles. Line 4 reads `"total"`, as it does in
#   all 500 velvet bundles, so no such cohort exists. The correct reason is that the
#   spec REJECTS every diverging rival (see the docstring bullet for the two
#   builds, including one that supplies a constant measure and is refused on the
#   descent goal itself), and the class is unshippable only because that refusal
#   fires at the `method`, so no witness can elaborate against the rival.
#   Disposition unchanged (nothing to ship), reason corrected, no hole open.
#
# BINDER / CLAUSE COVERAGE. The sole `ensures` clause `out = redirectTarget
#   encodedPath encodedQuery` has TWO input binders and THREE independent
#   structural sub-behaviours (path-prefix / trailing-slash / query-preserved),
#   plus the ASSEMBLY ORDER of the three components. The seven reject witnesses
#   probe seven DISTINCT input points (pts=7):
#     * weak-drop-query            ['a']       ['b']        (query non-empty)
#     * weak-drop-qmark            ['a']       ['x','y']    (query, no introducer)
#     * weak-drop-slash            ['a']       []           (path not slashed, q empty)
#     * weak-always-slash          ['a','/']   []           (path slashed, q empty)
#     * weak-drop-first-query-char ['p']       ['i','d']    (query content)
#     * weak-mangle-path-prefix    ['a','b']   ['z']        (prefix not verbatim)
#     * weak-swap-slash-query-order ['q','x']  ['k']        (component order)
#   So `encodedQuery` ranges over {[], ['b'], ['z'], ['k'], ['x','y'], ['i','d']}
#   — both the empty and non-empty sub-domains — and `encodedPath` ranges over
#   {['a'], ['p'], ['a','/'], ['a','b'], ['q','x']}, exercising BOTH branches of
#   the trailing-slash decision (a path ending in '/' at weak-always-slash, one
#   not at every other point) at both length 1 and length 2. The TRAILING-SLASH
#   clause is attacked on both sub-domains (weak-drop-slash: not appended when
#   required; weak-always-slash: appended when forbidden); the QUERY-PRESERVED
#   clause three ways (dropped, no introducer, first char lost); the PATH-PREFIX
#   clause by weak-mangle-path-prefix (last code point overwritten); and the
#   component ORDER by weak-swap-slash-query-order, which leaves both component
#   VALUES bit-identical to gold and permutes only their sequence. No binder is
#   pinned at a single value across the reject set; both are varied.
#
#   AUDIT NOTE (why the last two exist). As first ported this battery carried
#   five rivals, all of them altering a COMPONENT VALUE (`let slash` or `let
#   query`); none touched the final assembly. The PATH-PREFIX sub-behaviour the
#   docstring declares was therefore attacked by no rival at all — defended only
#   by the positive controls, i.e. only from the SPEC-TOO-STRONG side — and the
#   ordering of the three components was an entirely untested claim. A spec that
#   pinned the two component decisions but let the prefix drift, or that pinned
#   the components as a multiset without their sequence, would have passed the
#   ported battery unchanged. Both gaps are now closed by rivals whose witnesses
#   were rebuilt against rival AND gold; the third positive control
#   (pos-control-slash-via-reverse-head) was added for the same reason on the
#   soundness side, since the pre-existing reshape control is close to
#   definitionally equal to the frozen decision and a `simp`-normalised guard
#   flip demonstrates little about over-fitting.
# WITNESS DISCRIMINATION (verified during authoring with two real builds per
#   reject case): each witness ELABORATES against its rival (the extracted program
#   reduces to a literal that provably differs from `redirectTarget` at the probed
#   input) and FAILS against the frozen solution (`decide` proves the negation
#   false, since gold equals `redirectTarget` everywhere). No witness binds a
#   hypothesis (the carrier is fully transparent), so there is no
#   joint-satisfiability obligation. No `sorry`/`admit`/`native_decide`/`axiom`
#   appears.
AXIOM_TESTS = []
