"""properties.py — G-PBT falsification battery for django__django-14999 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed —
both of which the consumer spec view elides, so ``markers.same_spec`` holds and
the ``prove_correct renameSchedule`` obligation survives with a byte-identical
statement) and swaps in a candidate implementation.
``expect:"verify"`` passes iff (in scope AND verifies); ``expect:"reject"``
passes iff (in scope AND does NOT verify AND its refutation ``witness``
discriminates: the witness must elaborate against the rival and FAIL against the
frozen solution).

DEFENDED SURFACE. One contracted method modeling a schema-layer operation driven
by whether a stored table identifier actually changes across the operation:

  renameSchedule (beforeTable : Int) (afterTable : Int) (relations : List Int)
      return (out : List Int)
    ensures beforeTable = afterTable → out = []
    ensures beforeTable ≠ afterTable → out = mainMove :: relationOps relations

Two table identities are modeled as ``Int`` (only their equality is observable
to the schema layer); each dependent relation is one ``List Int`` slot; the
emitted schedule of schema operations is a ``List Int`` of per-group operation
codes. The two ensures clauses are INDEPENDENT top-level behaviours:

  * (1) the INERT clause — when the two identifiers are the SAME the schedule is
        EMPTY: NO schema work at all, neither the main-table move NOR any
        dependent-relation rewrite. This is the behavioural change the issue
        asks for (an unchanged table identity must issue zero work).
  * (2) the PROCEEDING clause — when the two identifiers DIFFER the schedule is
        EXACTLY ``mainMove :: relationOps relations``: the main-table move
        FIRST, then one rewrite entry PER dependent relation. This is pinned
        EXACTLY (not merely as "non-empty"): an impl that skips the main move,
        skips or duplicates a relation's entry, emits the wrong marker code, or
        reorders the main move after the relation entries violates it. What it
        does NOT pin is the relative order of the relation ENTRIES among
        themselves — they are all the same code, so permuting ``relations`` is
        unobservable here (demonstrated by a verifying ``.reverse`` reshape; see
        INPUT BINDERS).

INPUT BINDERS of the two predicates:
  * ``beforeTable`` / ``afterTable`` — the two table identities; their EQUALITY
    selects which clause fires (the fork the whole contract turns on).
  * ``relations`` — the dependent-relation collection; read-only (no ``mut``),
    and clause (2) pins one schedule entry per element, so the emitted schedule
    depends on its LENGTH. It does NOT depend on the relative order of the
    ELEMENTS: because every relation contributes the SAME marker code
    (``relationOps`` maps each slot to ``2`` regardless of its value),
    ``relationOps l`` is determined by ``l.length`` alone. Measured, not
    assumed: an impl returning ``mainMove :: relationOps relations.reverse``
    VERIFIES against the frozen spec (``lean_verify.sh`` exit 0, proof
    ``relationOps l = List.replicate l.length 2`` by induction). The per-element
    ORDER of the real dependent relations is therefore ABSTRACTED AWAY by this
    carrier's per-relation marker abstraction, not pinned by it — the only
    order clause (2) pins is the MAIN MOVE's position relative to the relation
    block (``mainMove`` first), which ``weak-reorder-move`` attacks.

ADVERSARIAL READ of the classes:
  * FRAME/PERMISSION-MUTATION — VACUOUS on this backend, and MEASURED so rather
    than argued. The sibling's MANDATORY frame-mutation rival keeps the gold body
    verbatim then WRITES back into a read-only sequence input carrying only a
    fractional heap permission (``Acc(list_pred(relations),1/2)``) and is
    rejected for INSUFFICIENT PERMISSION. Here the analogous rival is not merely
    unnecessary, it is NOT EXPRESSIBLE as a same-spec variant, which was checked
    three ways with the real verifier:
      - ``relations := relations ++ [9]`` inside the impl region does not
        elaborate at all: ``error: `relations` cannot be mutated, only variables
        declared using `let mut` can be mutated`` (exit 1). That is a PARSE/scope
        error in the executable surface, not a spec verdict, so it could never be
        a witness-bearing reject case — its rejection attributes nothing.
      - giving the binder ``mut`` to make the write legal edits the METHOD
        HEADER, which lives in the consumer spec view:
        ``variant_problems`` reports ``spec view differs (same_spec failed)`` —
        out of scope by construction.
      - mutating a LOCAL copy (``let mut rels := relations; rels := ...``) and
        returning the frozen schedule VERIFIES (exit 0), confirming the class has
        no observable content: a copy's mutation is invisible to the post-image.
    So there is no read-only input to overwrite, no permission system to trip,
    and no same-spec surface on which the write is even statable. The sibling's
    "the dependent-relation collection must not be mutated" obligation is
    structurally guaranteed by the ABSENCE of ``mut`` (directive 5), which the
    frozen spec already encodes. No substitute is fabricated (see footer).
  * DIVERGENCE / NON-TERMINATION — N/A: the sibling carries NO ``diverge-*`` /
    ``nonterm-*`` / ``weak-diverge`` case (its inert-vs-proceeding decision is
    value-observable, not termination-observable), so there is nothing in this
    class to port. Not written off as vacuous; simply absent upstream.
  * UNGROUNDED-ORACLE ECHO — N/A, as the sibling records. Both post-images are
    total functions of the method's own inputs (``relationOps`` / ``mainMove``
    are concrete ``def``s in the ``pure`` region; the ``axioms`` region declares
    nothing). There is no opaque answer key to echo — evaluating the pure
    schedule IS the correct answer — so there is no WRONG echo to build. The
    honest positive controls (``pos-*``) are the cheapest faithful reshapes.
  * INERT-VS-PROCEEDING DECISION — heavily exercised in BOTH directions: an impl
    that emits work on the inert branch violates clause (1)
    (``weak-always-emit``, ``weak-prepatch``); one that emits nothing on the
    proceeding branch violates clause (2) (``weak-always-empty``); one that
    treats one genuinely-changed identity pair as inert violates clause (2) on
    that slice (``weak-partial-domain``).
  * EXACT-SCHEDULE (clause 2) — this backend pins the proceeding schedule
    EXACTLY, an observable the sibling's weaker "len(Result())>0" clause does not
    have. Two rivals attack it that have no sibling: ``weak-skip-relations``
    (emits the main move but drops the per-relation entries) and
    ``weak-reorder-move`` (emits the relation entries then the main move,
    reversing the pinned order).

WITNESS MECHANICS on this carrier. Each reject rival is written STRAIGHT-LINE (it
names the pure ``relationOps`` / ``mainMove`` directly instead of rebuilding them
by loop), so ITS tester reduces and ``decide`` settles it; the witness states
``renameScheduleTester <before> <after> <relations> = false`` at a concrete point
where the rival's schedule violates a post-image while the correct schedule
satisfies it. No ``sorry`` / ``admit`` / ``native_decide`` / ``axiom``.

The frozen impl's proceeding branch is a ``while`` loop, which elaborates through
a fixpoint the kernel does not reduce, so the frozen tester is STUCK — not false
— at any input that reaches that branch. This splits the six witnesses into two
groups, and the distinction matters because a stuck build is a refutation that
was never performed (``pbt.py::_STUCK_REDUCTION``), not evidence:

  * INERT-branch witnesses (``weak-always-emit`` at ``(5,5,[])``,
    ``weak-prepatch`` at ``(5,5,[7])``) never enter the loop — the frozen impl
    returns ``[]`` by the guard — so the FROZEN SOLUTION itself decides them.
    Re-measured: gold exits 1 with ``Tactic `decide` proved that the proposition
    ... is false``, a genuine SEMANTIC refutation of the concrete claim.
  * PROCEEDING-branch witnesses (``weak-always-empty`` ``(0,1,[])``,
    ``weak-skip-relations`` ``(0,1,[7])``, ``weak-reorder-move`` ``(0,1,[7,8])``,
    ``weak-partial-domain`` ``(3,4,[7])``) do enter the loop, so the frozen
    tester reports ``did not reduce to `isTrue` or `isFalse` `` and gold's exit
    code carries no information. For these the gate falls back to a VERIFYING
    positive from this battery as the second subject; it checks that subject
    shares the frozen spec and verifies first. ``pos-schedule-direct`` is
    loop-free and serves: all four witnesses fail against it with ``Tactic
    `decide` proved that the proposition ... is false``, again a semantic
    refutation. (This is why ``pos-schedule-direct`` is load-bearing beyond its
    own soundness role, and must not be removed.) The recorded per-case
    ``witness_subject`` field states which subject each case was judged against.

All twelve builds were re-run out-of-band with ``scripts/lean_verify.sh``: every
witness ELABORATES against its rival (exit 0) and FAILS (exit 1) against the
subject the gate uses, in every case by a decided refutation rather than by a
stuck reduction, a missing identifier, or a type error.

AXIOM lane: EMPTY. ``meta.json`` declares no consumed ``axiom`` and no deep-model
reference; the schedule is modeled DEEPLY (the ``relationOps`` fold), refinement-
checked by the static + resolve gates, not axiomatized. Nothing in the proof
rests on an axiom, and this gate ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "django__django-14999"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchor. The whole executable body between the method's
# ---- `-- impl-start` / `-- impl-end` (marker lines included). Every rival and
# ---- reshape edits ONLY this block (and, where noted, the elided
# ---- `prove_correct` tactic body), so the spec view is untouched and same_spec
# ---- holds by construction. Uniqueness of this substring in the file is
# ---- asserted at load by `_swap`. ----
_IMPL = (
    "    -- impl-start\n"
    "    -- Don't proceed when the table identifier is not changed: inert ⇒ empty.\n"
    "    if beforeTable = afterTable then\n"
    "      return []\n"
    "    else\n"
    "      -- The rename proceeds: emit the main-table move, then one rewrite per\n"
    "      -- dependent relation (built back-to-front so a single fold unfold is\n"
    "      -- available per loop step).\n"
    "      let mut result : List Int := []\n"
    "      let mut i := relations.length\n"
    "      while i > 0\n"
    "        invariant 0 ≤ i ∧ i ≤ relations.length\n"
    "        invariant result = relationOps (relations.drop i)\n"
    "        done_with i = 0\n"
    "        decreasing i\n"
    "      do\n"
    "        result := (2 : Int) :: result\n"
    "        i := i - 1\n"
    "      return mainMove :: result\n"
    "    -- impl-end"
)

assert _BASE.count(_IMPL) == 1, "method impl region drifted from expected text"

# The `-- impl-start` marker line alone (unique). Anchor for the in-region
# admissibility assert, which is PREPENDED to the verbatim frozen body so the
# method's own obligation still discharges unchanged.
_IMPL_START = "    -- impl-start\n"

# ---- proof-body anchor. A `prove_correct` TACTIC BODY is elided from the
# ---- consumer spec view, so a reshape may retune its tactic script without
# ---- touching the spec or dropping the byte-identical obligation statement. ----
_PROOF = (
    "prove_correct renameSchedule by\n"
    "  loom_solve\n"
    "  rw [relationOps_drop_step relations i (by omega) (by omega)]\n"
    "  simp_all"
)

assert _BASE.count(_PROOF) == 1, "proof region drifted from expected text"


def _impl(new_body):
    """Full Solution.lean variant with ONLY the impl body replaced."""
    return _swap(_BASE, _IMPL,
                 "    -- impl-start\n" + new_body + "\n    -- impl-end")


def _reproof(src, new_proof):
    """Retune the elided `prove_correct` tactic body (statement unchanged)."""
    return _swap(src, _PROOF, new_proof)


# ---- witness preamble. The spec here is a `method` CONTRACT, not a bare
# ---- predicate, so a witness reaches it through Velvet's own tester machinery:
# ---- `renameScheduleTester <before> <after> <relations> = false` says the
# ---- extracted program's result violates the postcondition at that concrete
# ---- input. Checked in a file whose `prove_correct` block has been stripped, so
# ---- no tactic script can mask the verdict. There is no `require` clause, so the
# ---- precondition is `True` and decides trivially. The `List Int` return
# ---- carrier's DecidableEq is stdlib, so no `deriving` preamble is needed.
_TESTER = (
    "extract_program_for renameSchedule\n"
    "prove_precondition_decidable_for renameSchedule\n"
    "prove_postcondition_decidable_for renameSchedule\n"
    "derive_tester_for renameSchedule\n\n"
)


def _witness(before, after, relations):
    return _TESTER + (
        f"example : renameScheduleTester {before} {after} {relations} = false := by\n"
        "  decide\n")


# =====================================================================
# The admissibility assert proposition and its case tag (Velvet names the case
# after the asserted proposition text, so the tag must echo it verbatim).
# =====================================================================
_ADM_PROP = ("(([] : List Int) ≠ mainMove :: relationOps [7] ∧ "
             "mainMove :: relationOps [7] = [1, 2])")
_ADM_TAG = f"«assert_1: {_ADM_PROP}»"


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # impls that MUST verify. If a faithful correct impl cannot verify, the
    # spec is SPEC-TOO-STRONG. Each keeps both obligations and the identical
    # theorem statement; only the executable surface and (where needed) the
    # tactic script move.
    # =====================================================================
    {
        "id": "pos-branch-reorder",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: test the PROCEEDING (not-equal) branch first and the inert
        # branch second — the mirror of the frozen order. Same schedule on every
        # input (the loop that rebuilds `mainMove :: relationOps relations` is
        # kept verbatim, only the two arms are swapped), so both ensures clauses
        # still discharge with the frozen invariants; the reproof stays the
        # frozen `loom_solve; rw [...]; simp_all` (the loop-invariant goal is
        # unchanged).
        "module": _impl(
            "    if beforeTable ≠ afterTable then\n"
            "      let mut result : List Int := []\n"
            "      let mut i := relations.length\n"
            "      while i > 0\n"
            "        invariant 0 ≤ i ∧ i ≤ relations.length\n"
            "        invariant result = relationOps (relations.drop i)\n"
            "        done_with i = 0\n"
            "        decreasing i\n"
            "      do\n"
            "        result := (2 : Int) :: result\n"
            "        i := i - 1\n"
            "      return mainMove :: result\n"
            "    else\n"
            "      return []"),
        "rationale": "swapping the two mutually-exclusive branches (proceeding "
                     "arm first) computes the SAME schedule on every input — the "
                     "loop rebuilds `mainMove :: relationOps relations` verbatim "
                     "and the inert arm returns `[]` — so both "
                     "`beforeTable = afterTable → out = []` and "
                     "`beforeTable ≠ afterTable → out = mainMove :: relationOps "
                     "relations` still hold; a correct branch-order reshape must "
                     "verify, else SPEC-TOO-STRONG on branch order.",
    },
    {
        "id": "pos-schedule-direct",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: drop the loop entirely and return the modeled schedule
        # directly on the proceeding branch. Observationally identical (the
        # loop's post-state IS `relationOps relations`), so both clauses hold; the
        # tactic script is retuned to plain `loom_solve` because the no-loop body
        # leaves none of the loop-invariant goals the frozen script closes.
        "module": _reproof(
            _impl(
                "    if beforeTable = afterTable then\n"
                "      return []\n"
                "    else\n"
                "      return mainMove :: relationOps relations"),
            "prove_correct renameSchedule by\n  loom_solve"),
        "rationale": "returning `mainMove :: relationOps relations` directly on "
                     "the proceeding branch satisfies clause (2) definitionally "
                     "and clause (1) on the inert branch, so a correct loop-free "
                     "reshape must verify (else SPEC-TOO-STRONG on the loop form); "
                     "a second positive on a reshape axis distinct from "
                     "pos-branch-reorder (loop-elimination, not branch-order).",
    },

    # =====================================================================
    # ADMISSIBILITY. The method carries NO `require` clause, so there is no
    # precondition an input could fail; the sibling's "a normal F2P-shaped input
    # satisfies the precondition" probe is degenerate here (every input is
    # in-domain). The residual admissibility risk on a total domain is that the
    # post-image is DEGENERATE at the interesting point — a fork that never
    # separated the inert case from the proceeding one would read like a live one.
    # This case discharges an in-region `assert` pinning that the two clauses
    # genuinely FORK at the F2P shape (one dependent relation present): the inert
    # schedule (`[]`) is DISTINCT from the proceeding schedule, and the proceeding
    # schedule covers the main move AND that one relation (`= [1, 2]`). The
    # surrounding impl is kept verbatim so the method's own obligations still
    # discharge; the assert is live (a false claim leaves an unsolved goal).
    # =====================================================================
    {
        "id": "admiss-schedule-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _reproof(
            _swap(_BASE, _IMPL_START,
                  "    -- impl-start\n"
                  "    assert (with_name_prefix `assert\n"
                  f"      {_ADM_PROP})\n"),
            "prove_correct renameSchedule by\n"
            "  loom_solve\n"
            f"  case {_ADM_TAG} => decide\n"
            "  rw [relationOps_drop_step relations i (by omega) (by omega)]\n"
            "  simp_all"),
        "rationale": "the two clauses are satisfiable AND non-degenerate at the "
                     "F2P-shaped input (one dependent relation present): the inert "
                     "schedule `[]` is DISTINCT from the proceeding schedule, and "
                     "the proceeding schedule `mainMove :: relationOps [7]` is "
                     "`[1, 2]` — the main move followed by the one relation entry. "
                     "The in-region assert must discharge (else the fork is "
                     "degenerate / the obligation vacuous); the impl is kept "
                     "verbatim so both ensures clauses still discharge too.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # concrete input and the refinement argument that its faithful real
    # counterpart would NOT resolve the failing test. Each rival is written
    # straight-line (naming `relationOps` / `mainMove` directly) so its tester
    # reduces under `decide`.
    # =====================================================================
    {
        "id": "weak-always-emit",
        "kind": "uniqueness",
        "expect": "reject",
        # No inert guard at all: always emit the full proceeding schedule, even
        # when the two identifiers are equal.
        "module": _impl(
            "    return mainMove :: relationOps relations"),
        "refinement": "always emitting the full schedule is what a real "
                      "counterpart with NO top-level inert guard would do — it "
                      "issues the main-table move and every dependent-relation "
                      "rewrite even when the stored table identity is unchanged. "
                      "The failing test drives exactly that unchanged-identity "
                      "input and asserts ZERO schema work is issued, so this "
                      "counterpart fails it. It would NOT resolve.",
        "rationale": "REJECT from clause (1) `beforeTable = afterTable → "
                     "out = []`: with the two identifiers equal the post-image "
                     "demands `[]` but the rival emits `mainMove :: relationOps "
                     "relations`. Refuted on the inert branch with EMPTY relations "
                     "`(5, 5, [])`, where the rival still emits `[mainMove]` — the "
                     "point at which even an empty-relation inert input is wrong.",
        "witness": _witness(5, 5, "[]"),
    },
    {
        "id": "weak-prepatch",
        "kind": "uniqueness",
        "expect": "reject",
        # The pre-fix defect: rewrite the dependent relations UNCONDITIONALLY and
        # gate only the main move on identity equality. On an unchanged identity
        # WITH a dependent relation present it emits the relation entries — a
        # non-empty schedule where the inert clause demands emptiness.
        "module": _impl(
            "    if beforeTable = afterTable then\n"
            "      return relationOps relations\n"
            "    else\n"
            "      return mainMove :: relationOps relations"),
        "refinement": "this IS the pre-fix behaviour: the dependent-relation "
                      "rewrites run UNCONDITIONALLY and only the main move is "
                      "gated on identity equality. On an unchanged identity with a "
                      "dependent relation present it still issues that relation's "
                      "rewrite — precisely the constraint drop/recreate the issue "
                      "reports — so the failing test's zero-work assertion fails. "
                      "It would NOT resolve (the precise change the spec senses).",
        "rationale": "REJECT from clause (1): with the two identifiers equal the "
                     "post-image demands `[]` but the rival returns `relationOps "
                     "relations`, which is non-empty when a relation is present. "
                     "Refuted on the inert branch with ONE relation `(5, 5, [7])` "
                     "— the shape that makes clause (1)'s dependence on the "
                     "relation collection observable (the near-miss the empty-"
                     "relation always-emit witness does not reach).",
        "witness": _witness(5, 5, "[7]"),
    },
    {
        "id": "weak-always-empty",
        "kind": "uniqueness",
        "expect": "reject",
        # Never emits anything — the dual of always-emit. Satisfies clause (1)
        # but violates clause (2): a genuinely-changed identity issues NO schema
        # work, so the rename never reaches the backend.
        "module": _impl("    return []"),
        "refinement": "always emitting nothing is what a real counterpart that "
                      "returned early on every input would do — a genuine change "
                      "of the stored table identity would issue NO schema work at "
                      "all, so the table is never actually moved and its dependent "
                      "relations are never rewritten. The hidden proceeding-branch "
                      "tests (which observe that the move and the rewrites DO "
                      "happen) fail. It would NOT resolve.",
        "rationale": "REJECT from clause (2) `beforeTable ≠ afterTable → out = "
                     "mainMove :: relationOps relations`: with the two identifiers "
                     "distinct the post-image demands the non-empty schedule but "
                     "the rival returns `[]`. Refuted on the proceeding branch "
                     "`(0, 1, [])` — distinct identities, where the demanded "
                     "schedule is `[mainMove]` and the rival gives `[]`.",
        "witness": _witness(0, 1, "[]"),
    },
    {
        "id": "weak-skip-relations",
        "kind": "uniqueness",
        "expect": "reject",
        # EXACT-SCHEDULE rival: emits the main-table move on the proceeding
        # branch but DROPS the per-relation rewrite entries. Correct on the inert
        # branch and on the empty-relation proceeding case, wrong whenever a
        # relation is present.
        "module": _impl(
            "    if beforeTable = afterTable then\n"
            "      return []\n"
            "    else\n"
            "      return [mainMove]"),
        "refinement": "a counterpart that moves the main table but skips the "
                      "dependent-relation rewrites leaves every relation pointing "
                      "at the OLD table identity — the foreign keys and link "
                      "tables are never repointed. The hidden proceeding-branch "
                      "tests that observe those rewrites actually happen fail. It "
                      "would NOT resolve.",
        "rationale": "REJECT from clause (2): the proceeding schedule is pinned "
                     "EXACTLY as `mainMove :: relationOps relations` (one entry "
                     "per relation, in order), but the rival returns `[mainMove]` "
                     "— dropping every relation entry. Refuted on the proceeding "
                     "branch with ONE relation `(0, 1, [7])`, the shape that makes "
                     "the per-relation half of clause (2) observable (this rival "
                     "agrees with the frozen schedule on empty relations, so it "
                     "carries its own separating input).",
        "witness": _witness(0, 1, "[7]"),
    },
    {
        "id": "weak-reorder-move",
        "kind": "uniqueness",
        "expect": "reject",
        # EXACT-SCHEDULE / ORDER rival: emits the correct MULTISET of entries but
        # in the wrong order — the relation entries first, then the main-table
        # move last, reversing the pinned "main move FIRST" order.
        "module": _impl(
            "    if beforeTable = afterTable then\n"
            "      return []\n"
            "    else\n"
            "      return relationOps relations ++ [mainMove]"),
        "refinement": "a counterpart that issues the dependent-relation rewrites "
                      "BEFORE the main-table move rewrites relations that still "
                      "reference the pre-move table, so the rewrites target the "
                      "wrong table state — an ordering the operation forbids (the "
                      "main move must land first). The hidden proceeding-branch "
                      "tests observe the emitted order, so this fails. It would "
                      "NOT resolve.",
        "rationale": "REJECT from clause (2): the schedule is pinned as `mainMove "
                     ":: relationOps relations` (main move FIRST), but the rival "
                     "returns `relationOps relations ++ [mainMove]` (main move "
                     "LAST). Refuted on the proceeding branch with TWO relations "
                     "`(0, 1, [7, 8])`, where the reversed schedule `[2, 2, 1]` "
                     "differs from the pinned `[1, 2, 2]` — a length-2 relation "
                     "list so the order violation is unambiguous (not a singleton "
                     "coincidence). NOTE the violated ordering is the MAIN MOVE's "
                     "position relative to the relation block; the order of the "
                     "relation entries among themselves is not observable on this "
                     "carrier (all one marker code), so this rival is wrong for "
                     "the main-move displacement alone.",
        "witness": _witness(0, 1, "[7, 8]"),
    },
    {
        "id": "weak-relcount-slice",
        "kind": "uniqueness",
        "expect": "reject",
        # PARTIAL-DOMAIN on the OTHER binder. Every existing rival slices on the
        # identity pair (`weak-partial-domain`) or is wrong on the relation
        # collection UNIFORMLY (`weak-skip-relations` drops every entry at every
        # length). This one is correct on the inert branch, correct on the
        # proceeding branch at EVERY relation count except exactly 2, and at that
        # one count drops a single relation's entry — the near-miss shape a rival
        # that is uniformly wrong cannot reach, and the only rival whose defect is
        # invisible at both [] and [7].
        "module": _impl(
            "    if beforeTable = afterTable then\n"
            "      return []\n"
            "    else\n"
            "      if relations.length = 2 then\n"
            "        return mainMove :: relationOps (relations.drop 1)\n"
            "      else\n"
            "        return mainMove :: relationOps relations"),
        "refinement": "a counterpart whose dependent-relation walk skips one "
                      "relation at exactly one collection size — an off-by-one "
                      "that only bites when a model has that many dependents — "
                      "leaves one foreign key or link table still pointing at the "
                      "old table identity while every other configuration is "
                      "rewritten correctly. The hidden proceeding-branch tests "
                      "that exercise a model with two dependent relations observe "
                      "the missing rewrite; configurations with one dependent "
                      "still pass, which is what makes this the dangerous shape. "
                      "It would NOT resolve.",
        "rationale": "REJECT from clause (2): on `(2, 9, [7, 8])` the identifiers "
                     "differ so the post-image demands `mainMove :: relationOps "
                     "[7, 8]` = `[1, 2, 2]`, but the rival drops one relation "
                     "entry and returns `[1, 2]`. PARTIAL-DOMAIN on the "
                     "`relations` binder specifically: the rival is correct at "
                     "relation counts 0, 1, 3, 4, ... and wrong only at 2, so "
                     "neither the `[]` nor the `[7]` witnesses used elsewhere in "
                     "this battery reach it, and the identity pair `(2, 9)` is a "
                     "non-adjacent distinct pair no other witness probes.",
        "witness": _witness(2, 9, "[7, 8]"),
    },
    {
        "id": "weak-partial-domain",
        "kind": "uniqueness",
        "expect": "reject",
        # PARTIAL-DOMAIN: correct on the whole input domain EXCEPT one slice —
        # when the two identifiers are an adjacent pair (after == before + 1) it
        # mis-treats a genuinely-changed identity as inert and emits nothing.
        "module": _impl(
            "    if beforeTable = afterTable then\n"
            "      return []\n"
            "    else\n"
            "      if afterTable = beforeTable + 1 then\n"
            "        return []\n"
            "      else\n"
            "        return mainMove :: relationOps relations"),
        "refinement": "a guard that aliased one distinct pair of table identities "
                      "to 'unchanged' would skip the real rename for exactly that "
                      "pair — a genuinely-changed identity issuing no schema work "
                      "on that slice. The hidden proceeding-branch tests for a "
                      "genuine change on that pair fail. It would NOT resolve.",
        "rationale": "REJECT from clause (2): on `(3, 4, [7])` the two "
                     "identifiers DIFFER, so the post-image demands `mainMove :: "
                     "relationOps [7]` = `[1, 2]`, but the rival mis-classifies "
                     "the adjacent pair as inert and returns `[]`. PARTIAL-DOMAIN: "
                     "the rival is correct everywhere except this one slice. "
                     "Refuted at the adjacent-pair proceeding input `(3, 4, [7])` "
                     "— a distinct-identity point no other reject witness probes.",
        "witness": _witness(3, 4, "[7]"),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 8 SPEC cases (2 soundness
# positives, 1 admissibility, 5 uniqueness — one of which is the MANDATORY
# frame-mutation rival). Every one is accounted for below. The sibling contracts
# `rename_schema_schedule(before_table, after_table, relations)` over a read-only
# HALF-PERMISSION list and pins clause (2) only as `len(Result())>0`; this
# backend contracts the SAME operation but pins clause (2) EXACTLY as
# `mainMove :: relationOps relations` — a strictly RICHER observable (main move
# first, then exactly one entry per relation, so the entry COUNT and the main
# move's POSITION are both pinned; the relation entries' order among themselves
# is not, since they share one marker code). The decision surface carries across
# intact; the permission surface does not exist here; and the stronger clause (2)
# both INVALIDATES one sibling positive and AFFORDS three reject rivals with no
# sibling counterpart.
#
#   sibling case                  -> here                            disposition
#   -----------------------------------------------------------------------
#   pos-control-branch-reorder    -> pos-branch-reorder              PORTED
#   pos-control-different-witness -> (dropped) / pos-schedule-direct  RE-EXPRESSED
#   admiss-noop-fk-input          -> admiss-schedule-nondegenerate   RE-AIMED
#   weak-prepatch-bug             -> weak-prepatch                   PORTED
#   weak-always-emit              -> weak-always-emit                PORTED
#   weak-always-empty             -> weak-always-empty               PORTED
#   weak-partial-domain           -> weak-partial-domain             PORTED
#   frame-mutation-write-relations-> (none)                          VACUOUS
#   (no sibling)                  -> weak-skip-relations             ADDED (clause 2)
#   (no sibling)                  -> weak-reorder-move               ADDED (clause 2)
#   (no sibling)                  -> weak-relcount-slice             ADDED (audit)
#
# 4 uniqueness ported, 1 positive ported, 1 re-aimed admissibility, 1 vacuous;
# 1 sibling positive RE-EXPRESSED into a positive on a different axis + 3 reject
# rivals added (2 by the stronger clause (2), 1 by the independent audit below).
# Final battery: 2 soundness, 1 admissibility, 7 uniqueness = 10 cases.
#
# RE-EXPRESSED (pos-control-different-witness): the sibling's second positive
#   returns a DIFFERENT non-empty schedule on the proceeding branch (`[2]` not
#   `[1]`) to confirm its spec pins ONLY `len>0`, not a specific value. This
#   backend pins the proceeding schedule EXACTLY (`mainMove :: relationOps
#   relations`), so a "different non-empty witness" is now genuinely WRONG and
#   would (correctly) be REJECTED — it cannot be a verify positive here. The
#   sibling positive is therefore not portable as a positive (its premise, that
#   the value is unpinned, is FALSE on this carrier). The reshape SPIRIT — a
#   second structurally-different correct positive — is preserved as
#   pos-schedule-direct (loop-elimination), and the fact the sibling was probing
#   (that value is unpinned) is INVERTED into two reject rivals
#   (weak-skip-relations, weak-reorder-move) that demonstrate the value IS pinned.
# RE-AIMED (admissibility): the sibling's admissibility case self-calls on an
#   F2P-shaped input (equal identifiers + one dependent relation) to establish
#   the half-permission precondition and assert `len(out)==0`. There is no
#   permission surface here and NO `require` clause, so that probe is degenerate
#   (every input is in-domain). It is re-aimed at the residual total-domain risk
#   — that the fork is DEGENERATE at the interesting point — via an in-region
#   assert that the inert schedule (`[]`) is DISTINCT from the proceeding
#   schedule and the proceeding schedule at the F2P shape covers the main move
#   AND the one relation (`= [1, 2]`). This preserves the sibling's exact F2P
#   witness shape (unchanged identity + one dependent relation).
# VACUOUS (frame-mutation-write-relations): the sibling's MANDATORY probe writes
#   into `relations`, held at half heap permission, and is rejected for
#   INSUFFICIENT PERMISSION. This backend is referentially transparent: no heap,
#   no aliasing, and this bundle declares NO `mut` binder on `relations`. The
#   claim was re-derived with real builds rather than argued (see the
#   FRAME/PERMISSION-MUTATION note in the module docstring for the three
#   measurements): the write does not elaborate at all as a same-spec variant
#   (`relations` cannot be mutated), adding `mut` breaks same_spec because the
#   binder lives in the spec view, and mutating a local copy verifies because it
#   is unobservable. So the class has no expressible content here — the
#   sibling's "the dependent-relation collection must not be mutated" obligation
#   is structurally guaranteed by the ABSENCE of `mut` (directive 5), which the
#   frozen spec already encodes. Not fabricated.
# ADDED (weak-skip-relations, weak-reorder-move): the sibling's clause (2) is
#   only `len(Result())>0`, so a schedule that emits the main move but drops the
#   relation entries, or that displaces the main move to the end, VERIFIES there
#   — the sibling cannot express these rivals. This backend pins clause (2)
#   exactly, so both are genuine REJECTs and each attacks the per-relation /
#   main-move-position content of the schedule that the ported decision rivals
#   leave untested.
# ADDED (weak-relcount-slice): added by the independent audit. Every ported rival
#   slices on the IDENTITY pair or is wrong on the relation collection
#   UNIFORMLY; none was wrong at exactly one relation COUNT. This one drops a
#   single relation entry only when the collection has length 2, so it agrees
#   with the frozen schedule at the [] and [7] points every other witness in the
#   battery uses — the near-miss on the `relations` binder the battery otherwise
#   left unattacked.
#
# BINDER / CLAUSE COVERAGE of the reject witnesses (7 distinct input points):
#     beforeTable/afterTable — equal pairs (5,5) for the inert-clause rivals;
#       distinct pairs (0,1), the adjacent pair (3,4) and the far pair (2,9) for
#       the proceeding-clause rivals: the identity fork is varied across equal /
#       distinct / adjacent / far, never held fixed.
#     relations — [] (always-emit inert, always-empty proceeding), [7] (prepatch
#       inert, skip-relations proceeding, partial-domain proceeding), [7,8]
#       (reorder-move, relcount-slice): varied across empty / singleton /
#       length-2, so clause (1)'s and clause (2)'s dependence on the relation
#       collection (presence, length) is demonstrated. Note the variation that is
#       MEANINGFUL on this carrier is the collection's LENGTH, not the element
#       values or their permutation: `relationOps` maps every slot to the same
#       marker code, so [7] and [8] are the same point and a permuted list is the
#       same point (a `.reverse` reshape verifies). The element values above are
#       therefore chosen only for readability; the discriminating variation is
#       0 / 1 / 2 relations.
#   Both independent clauses are attacked: clause (1) in the presence AND absence
#   of relations (weak-prepatch / weak-always-emit), clause (2) in FIVE distinct
#   ways — emptiness (weak-always-empty), uniformly dropped per-relation entries
#   (weak-skip-relations), main-move displacement (weak-reorder-move), a
#   mis-classified identity sub-domain (weak-partial-domain), and a
#   mis-handled relation-COUNT sub-domain (weak-relcount-slice).
#
# SPEC-STRENGTH PROBES run by the independent audit and NOT shipped as cases
#   (recorded so the next reader need not re-run them). Wrong impls beyond the
#   battery's rivals, all correctly REJECTED by the frozen spec (exit 1, each on
#   the `ensures_1` goal): duplicated relation block; wrong main-move marker
#   code; main move emitted twice; the sibling's "different non-empty witness"
#   [2]; an extra trailing code; drop-first-relation; inert when the relation
#   collection is empty; inert on a negative identifier; echoing the relation
#   identifiers instead of the marker code. No spec hole was found in the
#   proceeding or inert clause. Correct reshapes, all ACCEPTED (exit 0): the
#   symmetric guard (`afterTable = beforeTable`), `List.replicate
#   relations.length 2`, `relations.map (fun _ => 2)`, and `relationOps
#   relations.reverse` — so the spec is not over-pinned on guard orientation or
#   on the fold's construction, and the shipped positives are not the only
#   admissible shapes.
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job; this bundle declares no
# axiom and no A-reference deep model (the schedule is modeled deeply in the pure
# region), so there is nothing there to probe, and this gate ignores AXIOM_TESTS
# regardless.
AXIOM_TESTS = []
