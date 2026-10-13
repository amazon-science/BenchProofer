"""properties.py — G-PBT falsification battery for matplotlib__matplotlib-25479 (lean).

NOT a Lean file; a manifest the G-PBT gate executes. Each SPEC case is a full
``Solution.lean`` variant built by REGION SURGERY: only text strictly inside an
``-- impl-start`` / ``-- impl-end`` region — and, for a case that legitimately
re-proves, inside the matching ``-- proof-start`` / ``-- proof-end`` region — is
changed. So ``markers.same_spec`` holds by construction, both
``theorem correct_colormapEq`` and ``theorem correct_register`` STATEMENTS stay
byte-identical, and nothing is assumed (no ``sorry``/``admit``/
``native_decide``, no new ``axiom``/``theorem``/``lemma``). ``expect:"verify"``
passes iff the file elaborates with BOTH obligations closed; ``expect:"reject"``
passes iff it does NOT verify AND the case's refutation ``witness`` holds of the
rival while FAILING on the frozen solution.

PORT NOTE. This is a PORT of the nagini falsification battery
(``../nagini/properties.py``), which is the design document for the adversarial
reasoning below. The nagini sibling contracts its two behaviors over a heap
carrier with fractional read permissions and a mutable registry dictionary; this
bundle models the two purely functional cores over an immutable ``structure
Colormap`` and returns the STORED colormap as a value rather than mutating a
container. Every nagini case is accounted for at the bottom of this file:
ported, re-expressed, vacuous, or omitted with its reason.

DEFENDED SURFACE — TWO obligations, four independent top-level clauses.

  ``problem_spec_colormapEq (a b : Colormap) (result : Bool)``
    (E) ``result = ((a.flag == b.flag) && (a.table == b.table))``
    One equation, but with TWO independently attackable conjuncts on the right
    and one deliberate ABSENCE:
      (E-flag)  the auxiliary attribute must participate;
      (E-table) the lookup tables must agree AS TABLES — the carrier is
                ``List (List Int)``, so equality pins both the shape (row count
                and each row's width) and every entry;
      (E-nolabel) ``a.name`` / ``b.name`` do NOT appear. The absence is
                load-bearing: two colormaps differing only in display name are
                equal. A rival that consults the label is refutable precisely
                because the spec never mentions it.

  ``problem_spec_register (name : String) (cmap : Colormap) (result : Colormap)``
    (R1) ``result.name = name``   — the stored colormap reports the label it was
                                    stored under, whatever its own label was;
    (R2) ``result.flag = cmap.flag``   — the auxiliary attribute is carried over;
    (R3) ``result.table = cmap.table`` — the lookup table is carried over whole.
    R2/R3 are the frame half of a referentially transparent spec: everything the
    behavior does NOT change is pinned to its input value, so no output
    component is left free for a rival to fill arbitrarily.

BINDER STRUCTURE and POINT SPREAD. ``problem_spec_colormapEq`` has two input
binders (``a``, ``b``), each a three-field record; ``problem_spec_register`` has
two (``name``, ``cmap``). The seven reject witnesses probe SEVEN DISTINCT input
tuples and vary every field of every binder — see the point-spread table at the
bottom. In particular ``name`` is probed both DIFFERENT from and EQUAL to
``cmap.name`` (so the relabel decision is exercised in both directions rather
than only where it fires), and ``flag`` is probed at positive, zero and negative
codes.

ADVERSARIAL READ of the nagini case classes on this carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS. Three nagini cases (two on the
    comparison, one on the store) are rejected there for INSUFFICIENT
    PERMISSION: the inputs are held at ``Acc(...,1/2)`` and the rival writes to
    one. Lean is referentially transparent — ``a``, ``b`` and ``cmap`` are
    immutable values, there is no aliasing, no fractional permission, and no
    read-only cell to overwrite, so the rival cannot even be WRITTEN. No
    substitute probe is fabricated. The information those cases carried is not
    lost: the "cheapest cheat" they punished (relabel the supplied colormap in
    place and hand it back) is here a no-op on the caller's value, and the
    guarantee that nothing else moves is carried instead by clauses R2/R3, which
    ``r-reg-drop-flag`` and ``r-reg-truncate-table`` attack directly.

  * DIVERGENCE / NON-TERMINATION — the nagini sibling carries no such case, and
    this class is VACUOUS here, but NOT for the reason first recorded. The
    original claim — "these are total Lean ``def``s, so a diverging
    implementation cannot be written at all" — is FALSE as stated and was
    measured false: a ``while true do`` loop inside the impl region ELABORATES
    (exit 0), with no ``partial`` and no ``termination_by``, because this bundle
    sets no ``loom.semantics.termination`` and plain Lean's ``Id``-monad ``forIn``
    over ``Lean.Loop.mk`` is a well-founded definition whose *unfolding* is what
    fails to terminate, not its elaboration. So the rival is writable. What
    actually makes the class vacuous is a two-case split, both halves measured:

      - If the loop's result is UNUSED (``let mut i := 0; while true do i := i+1``
        before the real return), ``Id``'s bind beta-DROPS it: the impl is
        definitionally the frozen one (``rfl`` closes ``divEq a b =
        (a.table == b.table)``, exit 0) and ``decide`` still evaluates it (exit
        0). Nothing diverges and nothing is attacked — an observationally
        identical rival, vacuous by attack C.
      - If the loop's result IS the returned value (``while true do r := ...;
        return r``), the term genuinely does not reduce, and then NO witness can
        refute it: ``decide`` reports "its ``Decidable`` instance ... did not
        reduce to ``isTrue`` or ``isFalse``" (exit 1) — the gate's own
        ``witness-undecided`` screen, which would make the case INCONCLUSIVE
        rather than a pass. The frozen proof also fails to close it, so it would
        be recorded as ``rejected`` for a reason that attests to nothing.

    Both halves fail the shippability test for opposite reasons, so no diverging
    rival belongs in the reject lane HERE. This is a demonstrated vacuity, not an
    assumed one. (Contrast the velvet backend under partial termination
    semantics, where ``the corpus-wide termination-semantics finding`` records a KNOWN SPEC HOLE.)

  * UNGROUNDED-ORACLE ECHO — VACUOUS. The bundle declares no ``opaque`` callee
    and consumes no ``axiom``: both behaviors are modeled deeply, and each spec
    clause relates the result structurally to the input fields. There is no
    answer key to echo, so every reject witness is stated at CONCRETE record
    literals and closed by ``decide`` — no conditioning on the carrier is needed
    and no witness binds anything, so no witness has hypotheses whose joint
    satisfiability could be in question.

  * PARTIAL-DOMAIN / VALUE-DROP — APPLIES, and is the whole reject lane. Every
    rival below is correct on a large part of the domain and diverges exactly
    where the modeled behavior bites.

AUDIT PROBES (independent, beyond the shipped cases; none is a spec hole).
Five further WRONG impls were built against the frozen spec and all five were
REJECTED with a discriminating witness (rival 0 / gold 1): compare only the row
COUNT; compare row count AND flattened entries but leave per-row widths unpinned;
decide on the auxiliary attribute alone, ignoring the table; carry the table but
REVERSE its row order; and set the display name to the storage label with a
character appended. So (E-table)'s shape and entry halves and R1/R3 are each
pinned tightly enough to reject near-misses the shipped lane does not contain.
Three further CORRECT reshapes were built and all three VERIFY: the commuted
conjunction (now the shipped positive), an unconditional `{ cmap with name := name }`
store, and a `return decide (a.flag = b.flag ∧ a.table = b.table)` form closed by
case-splitting on both equalities. So the spec is not too strong on this surface.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen scripts are tuned to the frozen forms —
so a rejection alone attributes nothing to the spec. Every ``expect="reject"``
case therefore carries a Lean snippet that states the spec predicate's NEGATION
at one concrete input and closes by ``decide``. Each was checked with two real
``lake env lean`` builds: it ELABORATES against its rival, and on the frozen
solution ``decide`` instead proves the un-negated proposition and the build
FAILS. So each is a machine-checked discriminator, not a tautology.
"""
from pathlib import Path

INSTANCE = "matplotlib__matplotlib-25479"
BACKEND = "lean"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


def _swaps(src, *pairs):
    for old, new in pairs:
        src = _swap(src, old, new)
    return src


# ---------------------------------------------------------------------------
# Region anchors, captured VERBATIM from the frozen Solution.lean and asserted
# unique at load, so this manifest breaks LOUDLY if the frozen solution drifts.
# Each anchor lies ENTIRELY inside the region it names.
# ---------------------------------------------------------------------------

# The whole body of the comparison implementation (inside its impl region).
_EQ_BODY = (
    "  if a.flag != b.flag then\n"
    "    return false\n"
    "  return a.table == b.table"
)

# The comparison proof's `intro` line (inside its proof region) — the hook the
# admissibility positive uses to prepend a ground `have` without touching the
# obligation STATEMENT.
_EQ_INTRO = "  intro a b\n"

# The comparison proof's tactic tail (inside its proof region) — replaced only by
# the positive control, whose commuted conjunction the frozen branch-split no
# longer closes.
_EQ_PROOF_TAIL = (
    "  simp only [Id.run, bind, bne]\n"
    "  by_cases h : a.flag == b.flag <;> simp [pure, h]"
)

# The whole body of the store implementation, comments included (inside its
# impl region).
_REG_BODY = (
    "  -- A duplicate of the colormap is what gets stored (structural copy).\n"
    "  let mut stored := cmap\n"
    "  -- The stored colormap should report the registration name, even when its own\n"
    "  -- display name differs.\n"
    "  if stored.name != name then\n"
    "    stored := { stored with name := name }\n"
    "  return stored"
)

# The store proof's tactic tail (inside its proof region) — replaced only by the
# positive control that legitimately re-proves a reshaped implementation.
_REG_PROOF_TAIL = (
    "  simp only [Id.run, bind, bne]\n"
    "  by_cases h : cmap.name == name <;> simp [pure, h]\n"
    "  exact beq_iff_eq.mp h"
)

for _a in (_EQ_BODY, _EQ_INTRO, _EQ_PROOF_TAIL, _REG_BODY, _REG_PROOF_TAIL):
    if _BASE.count(_a) != 1:
        raise AssertionError(f"anchor drift / not unique: {_a[:48]!r}")


# ---------------------------------------------------------------------------
# Witness scaffolds. Both specs are decidable at concrete record literals, so a
# refutation is `¬ problem_spec_<name> <literals> (implementation_<name>
# <literals>)` closed by `decide` after unfolding the two definitions. Nothing
# is bound in the head, so there are no assumptions to be inconsistent.
# ---------------------------------------------------------------------------
def _w_eq(a, b):
    return (
        "example : ¬ problem_spec_colormapEq\n"
        f"    {a}\n"
        f"    {b}\n"
        "    (implementation_colormapEq\n"
        f"      {a}\n"
        f"      {b}) := by\n"
        "  unfold problem_spec_colormapEq implementation_colormapEq\n"
        "  decide\n"
    )


def _w_reg(name, cmap):
    return (
        f"example : ¬ problem_spec_register {name}\n"
        f"    {cmap}\n"
        f"    (implementation_register {name}\n"
        f"      {cmap}) := by\n"
        "  unfold problem_spec_register implementation_register\n"
        "  decide\n"
    )


SPEC_TESTS = [

    # ===================================================================
    # OBLIGATION 1 — the comparison (problem_spec_colormapEq / correct_colormapEq)
    # ===================================================================

    # --------------------------------------------------------- soundness
    {
        "id": "pos-eq-local-flag-bool",
        "kind": "soundness",
        "expect": "verify",
        # Structurally different but CORRECT: hoist BOTH comparisons into local
        # booleans and return their conjunction in the OPPOSITE order, so the
        # branch on the auxiliary attribute disappears entirely.
        #
        # AUDIT NOTE — why the conjunction is commuted. The obvious reshape here
        # (hoist only the flag comparison and branch on `!flagEq`) is what this
        # case originally shipped, and it is NOT load-bearing: `Id`'s bind is
        # definitionally transparent and `if !flagEq` beta-reduces back to the
        # frozen `if a.flag != b.flag`, so the two impls are DEFINITIONALLY
        # EQUAL. Measured: `example : ∀ a b, gold a b = posLetBool a b := by
        # intro a b; rfl` ELABORATES (exit 0). A positive whose impl is
        # definitionally the frozen term cannot detect SPEC-TOO-STRONG — the
        # frozen proof script closes it because it is re-proving the same term,
        # not because the spec tolerates a new shape. Commuting the `&&` breaks
        # definitional equality (`rfl` on the same pair FAILS, exit 1: "gold a b
        # is not definitionally equal to cand a b"), so the frozen tactic no
        # longer applies and the proof region is legitimately re-proved by
        # `Bool.and_comm`. The statement stays byte-identical.
        "module": _swaps(
            _BASE,
            (_EQ_BODY,
             "  let flagEq := a.flag == b.flag\n"
             "  let tableEq := a.table == b.table\n"
             "  return tableEq && flagEq"),
            (_EQ_PROOF_TAIL, "  simp [Id.run, pure, Bool.and_comm]"),
        ),
        "rationale": "POSITIVE CONTROL for clause (E). A correct implementation with a "
                     "DIFFERENT executable shape — both comparisons hoisted into local "
                     "booleans and combined in the OPPOSITE order, so the branch on the "
                     "auxiliary attribute vanishes — must verify. It agrees with the "
                     "frozen implementation at every input, so (E-flag), (E-table) and "
                     "(E-nolabel) all still hold; if it could not verify the spec would "
                     "be SPEC-TOO-STRONG (pinning a syntactic form rather than the "
                     "behavior). Ports the nagini pos-eq-localbool positive's "
                     "local-boolean hoist, STRENGTHENED: the commuted conjunction makes "
                     "the reshape observably non-definitional (see the audit note "
                     "above), which the bare hoist was not, so this case now actually "
                     "exercises the spec rather than re-proving the frozen term.",
    },

    # --------------------------------------------------------- admissibility
    {
        "id": "admiss-eq-relabelled-duplicate",
        "kind": "admissibility",
        "expect": "verify",
        # The obligation is discharged at the exact shape the modeled behavior
        # exists for: two colormaps that agree on ALL color-determining content
        # and differ ONLY in display name. Prepended as a ground `have` inside
        # the existing tactic body, then the frozen proof continues verbatim.
        # Nothing is assumed: no new declaration, statement byte-identical.
        "module": _swap(
            _BASE, _EQ_INTRO,
            '  have _ground : problem_spec_colormapEq\n'
            '      { name := "orig", flag := 5, table := [[1, 2], [3, 4]] }\n'
            '      { name := "relabelled", flag := 5, table := [[1, 2], [3, 4]] }\n'
            '      (implementation_colormapEq\n'
            '        { name := "orig", flag := 5, table := [[1, 2], [3, 4]] }\n'
            '        { name := "relabelled", flag := 5, table := [[1, 2], [3, 4]] }) := by\n'
            '    unfold problem_spec_colormapEq implementation_colormapEq\n'
            '    decide\n'
            + _EQ_INTRO),
        "rationale": "ADMISSIBILITY: the spec must be SATISFIABLE — non-vacuously — at "
                     "the very input the modeled behavior exists to get right, namely a "
                     "pair agreeing on all color-determining content and differing only "
                     "in display name. The ground instance is discharged by evaluation "
                     "as a `have`, then the frozen obligation is closed verbatim; if "
                     "that instance could not be discharged, the modeled behavior would "
                     "be unsatisfiable at a normal in-domain input (the analogue of "
                     "PRECOND-TOO-STRONG). Re-expresses the nagini admiss-eq-self-call "
                     "case: nagini's version exists to show the fractional-permission "
                     "precondition can be ESTABLISHED at a call site, and this "
                     "obligation carries no precondition at all, so the honest analogue "
                     "is to discharge the postcondition at that same in-domain input.",
    },

    # --------------------------------------------------------- uniqueness
    {
        "id": "weak-eq-label-consulted",
        "kind": "uniqueness",
        "expect": "reject",
        # The pre-fix behavior: consult the display name before deciding.
        "module": _swap(
            _BASE, _EQ_BODY,
            "  if a.name != b.name then\n"
            "    return false\n"
            "  if a.flag != b.flag then\n"
            "    return false\n"
            "  return a.table == b.table"),
        "refinement": "this rival reports two colormaps as different whenever their "
                      "display names differ, even when every piece of "
                      "color-determining content agrees. Its faithful real counterpart "
                      "is the pre-change comparison, which is exactly the behavior the "
                      "reported defect is about: a duplicate of a colormap that has "
                      "been given a new display name is then not recognised as the same "
                      "colormap. The FAIL_TO_PASS behavior asserts precisely that a "
                      "duplicate carrying a DIFFERENT display name compares EQUAL to "
                      "its original, and the companion behavior asserts that a colormap "
                      "looked up under a storage label compares equal to the one that "
                      "was stored under it — which can only hold if the display name is "
                      "not consulted. So the faithful patch would NOT resolve.",
        "rationale": "REJECT from (E-nolabel): the spec's right-hand side is exactly "
                      "`(a.flag == b.flag) && (a.table == b.table)` and mentions neither "
                      "`a.name` nor `b.name`. The rival returns `false` at a point where "
                      "that right-hand side is `true`. Refuted at "
                      "a = {name := \"p\", flag := 3, table := [[7, 8]]}, "
                      "b = {name := \"q\", flag := 3, table := [[7, 8]]} — names differ, "
                      "all content agrees. This is the only witness that moves the "
                      "`name` field of the comparison binders while holding flag and "
                      "table fixed, so it is what demonstrates the label's irrelevance. "
                      "Ports nagini weak-eq-label-reintroduced.",
        "witness": _w_eq('{ name := "p", flag := 3, table := [[7, 8]] }',
                         '{ name := "q", flag := 3, table := [[7, 8]] }'),
    },

    {
        "id": "weak-eq-ignore-flag",
        "kind": "uniqueness",
        "expect": "reject",
        # Drop the auxiliary-attribute guard; decide on table content alone.
        "module": _swap(_BASE, _EQ_BODY, "  return a.table == b.table"),
        "refinement": "this rival decides equality on the lookup table alone and "
                      "ignores the auxiliary attribute entirely. Its faithful real "
                      "counterpart drops one whole disjunct of the comparison rather "
                      "than the single one the change is about, so two colormaps that "
                      "share a lookup table but differ in that attribute are reported "
                      "equal. The FAIL_TO_PASS behavior asserts BOTH directions on a "
                      "duplicate — equal when only the display name was altered, and "
                      "NOT equal when that auxiliary attribute was altered — so the "
                      "faithful patch would NOT resolve.",
        "rationale": "REJECT from (E-flag): the spec pins the result to a CONJUNCTION "
                      "whose first conjunct is `a.flag == b.flag`; the rival returns the "
                      "second conjunct alone, so it answers `true` where the spec "
                      "demands `false`. Refuted at flag codes 1 vs 2 with identical "
                      "names and identical tables [[0], [5]] — the only witness that "
                      "moves ONLY the flag field, holding name and table fixed. Ports "
                      "nagini weak-eq-ignore-extend.",
        "witness": _w_eq('{ name := "u", flag := 1, table := [[0], [5]] }',
                         '{ name := "u", flag := 2, table := [[0], [5]] }'),
    },

    {
        "id": "weak-eq-drop-last-row",
        "kind": "uniqueness",
        "expect": "reject",
        # Off-by-one tail: compare the tables with their final rows removed, so
        # the last row is never examined.
        "module": _swap(
            _BASE, _EQ_BODY,
            "  if a.flag != b.flag then\n"
            "    return false\n"
            "  return a.table.dropLast == b.table.dropLast"),
        "refinement": "this rival never examines the FINAL row of either lookup table, "
                      "so two colormaps differing only in their last table row are "
                      "reported equal. Its faithful real counterpart compares a prefix "
                      "of the table instead of the whole of it, which makes colormaps "
                      "that genuinely produce different colors at the top of their range "
                      "indistinguishable. The FAIL_TO_PASS behavior compares duplicates "
                      "whose tables have been altered and requires the alteration to be "
                      "seen, so the faithful patch would NOT resolve.",
        "rationale": "REJECT from (E-table): the spec pins the second conjunct to "
                      "`a.table == b.table` over the WHOLE tables; the rival compares "
                      "`dropLast` of each, which agrees with the spec only when the "
                      "final rows happen to match. Refuted at tables [[1], [2]] vs "
                      "[[1], [9]] (agreeing on every row but the last) with flag 0 and "
                      "differing names — a distinct point from the other table attack, "
                      "and the one that exercises the ENTRY dimension of table equality. "
                      "Ports nagini weak-eq-truncate-tail (there the off-by-one is in "
                      "the element loop's bound; here the same partial-domain error is "
                      "expressed on the list carrier).",
        "witness": _w_eq('{ name := "v", flag := 0, table := [[1], [2]] }',
                         '{ name := "w", flag := 0, table := [[1], [9]] }'),
    },

    {
        "id": "weak-eq-shape-blind",
        "kind": "uniqueness",
        "expect": "reject",
        # Compare the tables FLATTENED, so their shape stops mattering and only
        # the entry sequence is checked.
        "module": _swap(
            _BASE, _EQ_BODY,
            "  if a.flag != b.flag then\n"
            "    return false\n"
            "  return a.table.flatten == b.table.flatten"),
        "refinement": "this rival compares the two lookup tables as flat entry "
                      "sequences, so it is blind to their SHAPE: two tables holding the "
                      "same entries in the same order but arranged differently are "
                      "reported equal. Its faithful real counterpart compares tables "
                      "entry-by-entry without first checking that they have the same "
                      "extent — which is the one thing the modeled comparison must do "
                      "before looking at entries at all. The PASS_TO_PASS behavior "
                      "compares duplicates whose tables have been reduced to a "
                      "differently-shaped slice and requires that comparison to report "
                      "NOT equal (and to do so without failing), so the faithful patch "
                      "would NOT resolve.",
        "rationale": "REJECT from (E-table), SHAPE dimension: the carrier is "
                      "`List (List Int)` precisely so that `a.table == b.table` pins the "
                      "row count and each row's width as well as the entries; a "
                      "shape-blind comparison satisfies neither. Refuted at "
                      "table [[4], [6]] vs [[4, 6]] — identical entry sequences, "
                      "different shapes — with flag -1 (the negative-code point) and "
                      "identical names. ADDED relative to nagini: its carrier flattens "
                      "the table to a single sequence, so the shape distinction does not "
                      "exist there and no sibling rival could attack it. Here it is a "
                      "load-bearing half of a real spec clause.",
        "witness": _w_eq('{ name := "s", flag := -1, table := [[4], [6]] }',
                         '{ name := "s", flag := -1, table := [[4, 6]] }'),
    },

    # ===================================================================
    # OBLIGATION 2 — the store (problem_spec_register / correct_register)
    # ===================================================================

    # --------------------------------------------------------- soundness
    {
        "id": "pos-reg-construct-directly",
        "kind": "soundness",
        "expect": "verify",
        # Structurally different but CORRECT: instead of duplicating and then
        # conditionally overwriting the display name, build the stored colormap
        # directly under the storage label. The conditional disappears entirely,
        # so the frozen branch-splitting proof no longer applies and the proof
        # region is legitimately RE-PROVED — the `correct_register` STATEMENT is
        # byte-identical, and no new axiom/lemma/assumption token appears.
        # (Checked with a real build.)
        "module": _swaps(
            _BASE,
            (_REG_BODY,
             "  return { name := name, flag := cmap.flag, table := cmap.table }"),
            (_REG_PROOF_TAIL, "  simp [Id.run, pure]"),
        ),
        "rationale": "POSITIVE CONTROL for clauses R1/R2/R3. A correct implementation "
                     "with a structurally DIFFERENT shape — the display name is fixed "
                     "at construction rather than duplicated and then conditionally "
                     "overwritten, so the conditional vanishes — must verify. It "
                     "produces the same colormap at every input, so R1, R2 and R3 all "
                     "hold; if it could not verify the spec would be SPEC-TOO-STRONG. "
                     "Re-proved inside the proof region only (the frozen script splits "
                     "on a branch this shape no longer has), statement byte-identical, "
                     "nothing assumed. Ports nagini pos-reg-construct-relabel, which "
                     "makes exactly this reshape (fold the relabel into construction).",
    },

    # --------------------------------------------------------- uniqueness
    {
        "id": "weak-reg-keep-own-label",
        "kind": "uniqueness",
        "expect": "reject",
        # The pre-fix behavior: store the duplicate as-is, keeping its own
        # display name instead of the storage label.
        "module": _swap(_BASE, _REG_BODY,
                        "  let stored := cmap\n"
                        "  return stored"),
        "refinement": "this rival stores a faithful duplicate that keeps its ORIGINAL "
                      "display name, so a later lookup by the storage label yields a "
                      "colormap reporting a different name. Its faithful real "
                      "counterpart is the pre-change store, and this is the reported "
                      "defect verbatim: the problem statement shows a colormap created "
                      "under one name, stored under another, and then failing to be "
                      "usable because the stored object still reports the first name. "
                      "The FAIL_TO_PASS behavior asserts that a lookup by the storage "
                      "label yields a colormap whose display name IS that label, so the "
                      "faithful patch would NOT resolve.",
        "rationale": "REJECT from R1: the spec pins `result.name = name`, but the rival "
                      "yields `result.name = cmap.name`, which is not provably equal to "
                      "`name` — they are independent String inputs. Refuted at "
                      "name = \"reg\" with cmap.name = \"orig\" (the labels DIFFER, which "
                      "is where the clause bites). Ports nagini weak-reg-drop-relabel.",
        "witness": _w_reg('"reg"',
                          '{ name := "orig", flag := 4, table := [[1, 2]] }'),
    },

    {
        "id": "weak-reg-drop-flag",
        "kind": "uniqueness",
        "expect": "reject",
        # Relabel correctly, but hardwire the auxiliary attribute to a constant
        # instead of carrying the input's.
        "module": _swap(
            _BASE, _REG_BODY,
            "  let mut stored := cmap\n"
            "  if stored.name != name then\n"
            "    stored := { stored with name := name }\n"
            "  stored := { stored with flag := 0 }\n"
            "  return stored"),
        "refinement": "this rival sets the display name correctly but resets the "
                      "auxiliary attribute to a fixed default instead of carrying over "
                      "the one the supplied colormap has. Its faithful real counterpart "
                      "stores a fresh colormap rather than a faithful duplicate, so a "
                      "colormap whose end-of-range behavior was customised before being "
                      "stored loses that customisation. The FAIL_TO_PASS behavior stores "
                      "exactly such a customised colormap and then asserts that the "
                      "looked-up colormap compares EQUAL to the one that was stored — "
                      "and that comparison consults this very attribute — so the "
                      "faithful patch would NOT resolve.",
        "rationale": "REJECT from R2: the spec pins `result.flag = cmap.flag`, but the "
                      "rival yields the constant 0, which agrees only when the input's "
                      "code happens to be 0. Refuted at cmap.flag = 7 (a distinct, "
                      "non-default code) with name = \"alpha\" and cmap.name = \"beta\". "
                      "Ports nagini weak-reg-drop-extend.",
        "witness": _w_reg('"alpha"',
                          '{ name := "beta", flag := 7, table := [[3]] }'),
    },

    {
        "id": "weak-reg-truncate-table",
        "kind": "uniqueness",
        "expect": "reject",
        # Relabel and carry the auxiliary attribute correctly, but store only
        # the first row of the lookup table.
        "module": _swap(
            _BASE, _REG_BODY,
            "  let mut stored := cmap\n"
            "  if stored.name != name then\n"
            "    stored := { stored with name := name }\n"
            "  stored := { stored with table := stored.table.take 1 }\n"
            "  return stored"),
        "refinement": "this rival gets the display name and the auxiliary attribute "
                      "right but keeps only the first row of the lookup table. Its "
                      "faithful real counterpart stores a partial copy of the table, so "
                      "the stored colormap produces the wrong colors and no longer "
                      "compares equal to the colormap that was stored. The FAIL_TO_PASS "
                      "behavior asserts that a lookup by the storage label yields a "
                      "colormap EQUAL to the one stored, and that comparison pins the "
                      "table's shape and entries, so the faithful patch would NOT "
                      "resolve.",
        "rationale": "REJECT from R3: the spec pins `result.table = cmap.table` — the "
                      "table is carried over WHOLE — but the rival yields "
                      "`cmap.table.take 1`, which agrees only for tables of at most one "
                      "row. Refuted at a two-row table [[1], [2]] with flag -2 and, "
                      "deliberately, name = cmap.name = \"k1\": this is the only reject "
                      "witness on this obligation where the storage label EQUALS the "
                      "supplied colormap's own label, so it exercises the branch on "
                      "which no relabel is needed and shows R3 is enforced there too. "
                      "ADDED relative to nagini, whose store rivals attack the label and "
                      "the auxiliary attribute but leave the table clause with no "
                      "dedicated rival.",
        "witness": _w_reg('"k1"',
                          '{ name := "k1", flag := -2, table := [[1], [2]] }'),
    },
]


# ---------------------------------------------------------------------------
# NAGINI -> LEAN ACCOUNTING. The sibling battery ships 9 SPEC cases (2 soundness
# positives, 1 admissibility, 6 uniqueness rivals) plus a 1-entry AXIOM lane.
# This bundle models the SAME two behaviors, so the port is close to 1:1 rather
# than narrowed; it drops the three permission-mutation cases (vacuous on this
# carrier), drops one case whose clause this bundle does not model, and ADDS two
# rivals for clauses the sibling left without a dedicated attacker.
#
#   sibling case                    -> here
#   ------------------------------------------------------------------------
#   pos-eq-localbool                -> pos-eq-local-flag-bool         PORTED
#   admiss-eq-self-call             -> admiss-eq-relabelled-duplicate RE-EXPRESSED
#   frame-mutate-eq-self-name       -> (none)                         VACUOUS
#   frame-mutate-eq-self-lut        -> (none)                         VACUOUS
#   weak-eq-label-reintroduced      -> weak-eq-label-consulted        PORTED
#   weak-eq-ignore-extend           -> weak-eq-ignore-flag            PORTED
#   weak-eq-truncate-tail           -> weak-eq-drop-last-row          PORTED
#   pos-reg-construct-relabel       -> pos-reg-construct-directly     PORTED (re-proved)
#   frame-mutate-reg-cmap-name      -> (none)                         VACUOUS
#   weak-reg-drop-relabel           -> weak-reg-keep-own-label        PORTED
#   weak-reg-drop-extend            -> weak-reg-drop-flag             PORTED
#   weak-reg-side-write             -> (none)                         OMITTED (unmodeled)
#   (none)                          -> weak-eq-shape-blind            ADDED
#   (none)                          -> weak-reg-truncate-table        ADDED
#   AXIOM_TESTS (1)                 -> (none)                         DROPPED (G-AX)
#
# VACUOUS x3 (frame-mutate-eq-self-name, frame-mutate-eq-self-lut,
#   frame-mutate-reg-cmap-name): all three are rejected on the sibling for
#   INSUFFICIENT PERMISSION — the rival writes to an input held at a half
#   permission. This carrier is referentially transparent: the inputs are
#   immutable values, there is no aliasing and no permission to be insufficient,
#   so the rival cannot be expressed at all. No substitute probe is fabricated
#   (that is the porting map's instruction). What those cases protected is
#   covered here by the R2/R3 frame clauses, which weak-reg-drop-flag and
#   weak-reg-truncate-table attack head-on.
#
# OMITTED x1 (weak-reg-side-write): the sibling's rival performs a correct
#   registration AND ALSO binds the new value under a second, unrelated key, and
#   is rejected by the sibling's registry-FRAME clauses (for every other key,
#   membership and binding are preserved). This bundle does not model the
#   registry container: the modeled behavior maps a storage label and a colormap
#   to the colormap that gets stored, and returns it as a VALUE. There is no
#   container binder, no other key, and therefore no clause about unrelated keys
#   for the rival to violate — a rival with the side-write shape cannot even be
#   typed here, and one written anyway would be observationally identical to
#   gold, so no discriminating witness exists. This is carrier narrowing, not a
#   proof difficulty; it is a KNOWN GAP: an implementation that corrupts an
#   unrelated stored colormap while registering correctly is outside what this
#   bundle's spec can see. Closing it would need the registry itself in the
#   carrier.
#
# ADDED x2 — each attacks a load-bearing clause of the SAME modeled spec that
#   no sibling rival targets individually, which the per-clause coverage
#   requirement asks for. Neither is fabricated for an unmodeled behavior.
#   * weak-eq-shape-blind attacks the SHAPE half of (E-table). The sibling's
#     carrier represents the lookup table as one flat sequence, so shape is not
#     representable there; this bundle's `List (List Int)` makes it a real half
#     of a real clause (mapping.md records exactly this: differently-shaped
#     tables must compare unequal).
#   * weak-reg-truncate-table attacks R3, which the sibling's store rivals leave
#     unattacked (they target the label and the auxiliary attribute).
#
# DIVERGENCE LANE: the sibling carries NO diverge-*/nonterm-*/weak-diverge case,
#   and the class is vacuous here — but by MEASUREMENT, not because "a
#   non-terminating rival cannot be written". It can: a `while true do` body
#   elaborates inside the impl region with no `partial` and no `termination_by`
#   (exit 0), since this bundle sets no `loom.semantics.termination`. The two
#   writable shapes are vacuous for OPPOSITE reasons — an unused loop is
#   beta-dropped by `Id`'s bind and is definitionally the frozen impl, while a
#   load-bearing loop stops reducing so `decide` reports "did not reduce to
#   `isTrue` or `isFalse`" and any witness lands as the gate's own
#   `witness-undecided` (inconclusive), never a pass. See the DIVERGENCE bullet
#   in the module docstring for the exact builds. (On velvet under partial
#   termination semantics this is instead a KNOWN SPEC HOLE; see
#   the corpus-wide termination-semantics finding. It is not one here.)
#
# NO SOUNDNESS POSITIVE WAS DROPPED for a proof that would not close. Both
#   positives and the admissibility case were confirmed to elaborate with both
#   obligations closed, by real builds; the only proof authoring needed was the
#   store positive's, whose conditional-free shape is closed by
#   `simp [Id.run, pure]`.
#
# POINT SPREAD — the seven reject witnesses probe SEVEN DISTINCT input tuples
# (pts=7), and every field of every input binder is moved by some witness while
# the others are held:
#
#   obligation 1 (binders a, b):
#     ("p",3,[[7,8]])   vs ("q",3,[[7,8]])    weak-eq-label-consulted   (E-nolabel)
#     ("u",1,[[0],[5]]) vs ("u",2,[[0],[5]])  weak-eq-ignore-flag       (E-flag)
#     ("v",0,[[1],[2]]) vs ("w",0,[[1],[9]])  weak-eq-drop-last-row     (E-table entries)
#     ("s",-1,[[4],[6]]) vs ("s",-1,[[4,6]])  weak-eq-shape-blind       (E-table shape)
#   obligation 2 (binders name, cmap):
#     "reg"   / ("orig",4,[[1,2]])            weak-reg-keep-own-label   R1
#     "alpha" / ("beta",7,[[3]])              weak-reg-drop-flag        R2
#     "k1"    / ("k1",-2,[[1],[2]])           weak-reg-truncate-table   R3
#
#   Across them: the `name` field varies and is probed both EQUAL to and
#   DIFFERENT from the storage label (so the relabel decision is exercised in
#   both directions); `flag` takes 3, 1, 2, 0, -1, 4, 7, -2 (positive, zero and
#   negative codes); `table` takes one-row, two-row, one-wide and two-wide
#   shapes. No binder and no field is pinned across the lane.
#
# AXIOM_TESTS: dropped. The axiom lane belongs to G-AX and this gate ignores it.
# This bundle declares no `opaque` callee and consumes no `axiom` (both
# behaviors are modeled deeply), so there is nothing for a spec-lane probe to
# assume in the first place.
AXIOM_TESTS = []
