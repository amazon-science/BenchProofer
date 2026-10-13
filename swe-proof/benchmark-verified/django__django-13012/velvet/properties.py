"""properties.py — G-PBT falsification battery for django__django-13012 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed,
both of which the consumer spec view elides — so ``markers.same_spec`` holds and
the ``prove_correct`` obligation survives with a byte-identical statement) and
swaps in a candidate implementation; it is checked by the real verifier.
``expect:"verify"`` passes iff (in scope AND verifies); ``expect:"reject"``
passes iff (in scope AND does NOT verify AND its refutation ``witness``
discriminates: the witness must ELABORATE against the rival and FAIL against the
frozen solution).

DEFENDED SURFACE (one contracted method over an identity-only column carrier,
``List GroupCol``). A transparent wrapping expression decides which columns it
contributes to a grouping clause:

  groupingColumns (selfCol : GroupCol) (innerHasAggregate : Bool)
      (innerCols : List GroupCol) (innerColsDefaultContext : List GroupCol)
      return (out : List GroupCol)
    ensures out = innerCols          -- THE load-bearing (and only) clause

There is NO opaque answer key to echo: ``out = innerCols`` grounds the result in
an actual method input (directive 8). The behaviour pinned is a property of the
CALLER — the transparent wrapper contributes EXACTLY the columns the wrapped
inner expression contributes for the requested grouping context, and NEVER
substitutes its own identity or drops the requested context.

BINDER STRUCTURE (read this before judging binder coverage). The postcondition
depends on EXACTLY ONE of the four inputs — ``innerCols``. The other three are
DELIBERATELY free and irrelevant to the modeled behaviour:

  * ``selfCol`` — the wrapping expression's own identity. It exists only so the
    rivals can state the WRONG answer (return the wrapper itself). The correct
    result never mentions it.
  * ``innerHasAggregate`` / ``innerColsDefaultContext`` — the two observations
    the INHERITED (pre-patch) rule branched on: a non-aggregating expression
    stood in for itself (``[selfCol]``), an aggregating one re-queried its
    sources WITHOUT forwarding the requested context (``innerColsDefaultContext``).
    They are present only so the pre-patch skeleton is expressible while the spec
    stays byte-identical. The whole POINT of the fix is that a transparent
    wrapper IGNORES both: it forwards regardless of aggregation and regardless of
    the default-context call.

So no rival can be wrong in a way DISTINGUISHED ONLY by ``innerHasAggregate`` or
``innerColsDefaultContext``: any impl that branches on them yet returns
``innerCols`` on every branch VERIFIES (correctly — the spec is independent of
them), and any impl that returns something ELSE is caught by the ``innerCols``
clause on whichever branch fires. These two binders are genuinely irrelevant to
the modeled behaviour (see ``assessment``). The reject witnesses below
nonetheless VARY all four binders across their concrete input points — varying
an irrelevant binder is free and keeps the coverage tool from flagging a binder
pinned at one value — while the DISCRIMINATION always comes from ``innerCols``
(and, for the wrong-answer rivals, from ``selfCol`` being substituted for it).

``innerCols`` is a SEQUENCE, so it is probed in three regimes, not two: the
constant arm (``[]``), the column-like arm (a singleton), and a length-2 point
where ORDER and MULTIPLICITY become observable at all. The last regime is what
``reorder-columns`` attacks; at lengths 0 and 1 a permutation is invisible, so a
battery refuted only at those lengths would not test the order half of
``out = innerCols`` that ``mapping.md`` declares load-bearing.

ADVERSARIAL READ of the nagini classes on this carrier:
  * FRAME-MUTATION — VACUOUS. The nagini sibling carries this MANDATORY because
    its inputs are held at a fractional heap permission (``Acc(.,1/2)``) an impl
    can illegally overwrite. Lean/Velvet are referentially transparent: every
    input here is an immutable value, there is no ``mut`` binder, no heap and no
    aliasing — so there is no read-only field to mutate and no substitute probe
    to build. Not fabricated (per the porting map: this class is vacuous here).
  * NAGINI's DEEP-MODEL cases (base_group_by_cols' constant/column-like
    dichotomy: DROP_CONSTANT, DROP_COLUMN, WRONG_IDENTITY, the branch-reorder
    positive) attacked a SEPARATE modeled function nagini spelled out. This
    bundle does NOT model that dichotomy: the wrapped node's own rule is folded
    into the FREE input ``innerCols`` (directive 7), so ``[]`` for a constant and
    ``[inner]`` for a column-like node are simply two VALUES of ``innerCols``.
    The dichotomy cases therefore re-express as value rivals over the single
    ``out = innerCols`` clause (see the accounting block at the bottom).
  * UNGROUNDED-ORACLE ECHO — N/A: the post-image is a method input, not an
    axiomatized oracle; the ``axioms`` region is empty.

WITNESS PLACEMENT. Each reject rival is refuted at a concrete input chosen so the
four points together move ``selfCol`` / ``innerCols`` (the load-bearing binders)
across the constant arm (``innerCols = []``) and the column-like arm
(``innerCols`` a non-empty singleton), and incidentally vary the two free
binders. No two rivals are refuted at the same input tuple.

AXIOM lane: EMPTY (``axioms`` region declares no ``axiom``; the delegated callee
is a free input, not an oracle). The gate ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "django__django-13012"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchor. Lies wholly inside the single impl region and is
# ---- unique in Solution.lean (both facts asserted at load by _swap). The two
# ---- comment lines above it are ALSO inside the impl region, so anchoring on
# ---- the two code lines keeps the surgery within the elided region. ----
_IMPL = (
    "    let result : List GroupCol := innerCols\n"
    "    return result"
)

def _with_impl(new_impl: str) -> str:
    """Solution.lean with ONLY the impl body replaced (spec view untouched).

    Every case in this battery keeps the frozen `prove_correct groupingColumns by
    loom_solve` script verbatim: the positive reshape collapses to `innerCols` so
    the frozen script still closes it, and each reject rival is judged by its
    witness, not by whether the frozen script happens to break on the reshape.
    """
    return _swap(_BASE, _IMPL, new_impl)


# ---- witness preamble. The spec is a `method` CONTRACT, not a bare predicate,
# ---- so a witness reaches it through Velvet's own tester machinery:
# ---- `groupingColumnsTester selfCol innerHasAggregate innerCols
# ---- innerColsDefaultContext = false` says the extracted program's result
# ---- violates the postcondition at that concrete input. Checked in a file whose
# ---- `prove_correct` block has been stripped, so no tactic script can mask the
# ---- verdict. There are no `require` clauses, so every input reaches the
# ---- postcondition (nothing is vacuously excluded). GroupCol is an identity-only
# ---- structure with a single `ref : Nat` field, so `⟨n⟩` is a concrete column
# ---- and `decide` settles every equality. ----
_TESTER = (
    "extract_program_for groupingColumns\n"
    "prove_precondition_decidable_for groupingColumns\n"
    "prove_postcondition_decidable_for groupingColumns\n"
    "derive_tester_for groupingColumns\n\n"
)


def _witness(call: str) -> str:
    return _TESTER + f"example : {call} = false := by\n  decide\n"


# ---- proof anchor. The frozen `prove_correct` script, used ONLY by the
# ---- admissibility case, which prepends `have`s to it. The obligation STATEMENT
# ---- is the `method` header (spec view, byte-identical under same_spec); only
# ---- the tactic body changes, which a variant may legitimately do. ----
_PROOF = "prove_correct groupingColumns by\n  loom_solve"


def _with_proof(new_proof: str) -> str:
    return _swap(_BASE, _PROOF, new_proof)


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROL (soundness) — a structurally different but CORRECT
    # impl that MUST verify, else SPEC-TOO-STRONG. It INSPECTS the aggregate
    # flag (a genuinely free input) yet returns the wrapped inner expression's
    # columns on BOTH branches, so `out = innerCols` still holds — a direct
    # demonstration that the spec is (correctly) independent of aggregation:
    # the transparent wrapper forwards regardless. The decision collapses to
    # `innerCols` on both arms, so the frozen tactic script (`loom_solve`) closes
    # the byte-identical obligation with no retune (verified out-of-band with two
    # real builds).
    # =====================================================================
    {
        "id": "pos-ignore-aggregate",
        "kind": "soundness",
        "expect": "verify",
        "module": _with_impl(
            "    let result : List GroupCol :=\n"
            "      if innerHasAggregate then\n"
            "        match innerCols with\n"
            "        | [] => []\n"
            "        | x :: xs => x :: xs\n"
            "      else innerCols\n"
            "    return result"),
        "rationale": "structurally different CORRECT reshape: it branches on the "
                     "free aggregate flag and, on the aggregate arm, REBUILDS the "
                     "wrapped inner expression's columns by a genuine "
                     "case-analysis (`match innerCols with [] / x :: xs`) rather "
                     "than echoing the binder — a term-shape the frozen impl does "
                     "not contain — yet both arms yield exactly `innerCols`, so "
                     "`out = innerCols` holds regardless of the flag. A faithful "
                     "reshape MUST verify, else SPEC-TOO-STRONG; it also witnesses "
                     "that the spec is correctly independent of `innerHasAggregate` "
                     "(the branches are NOT textually identical, so the positive "
                     "exercises the obligation on a non-trivially reshaped body).",
    },

    # =====================================================================
    # ADMISSIBILITY — the obligation is SATISFIABLE, and non-degenerately so,
    # at the two F2P-shaped input points. The method declares no `require`, so
    # the classic "does the precondition admit a normal input" probe has no
    # precondition to interrogate; the analogue on a total carrier is the
    # obligation being unsatisfiable at exactly an F2P-shaped input, which is
    # what this case tests directly. Two `have`s discharge, BY EVALUATION at
    # concrete points, that the post-image demanded at the constant arm
    # (`innerCols = []` -> no contributed columns) and at the column-like arm
    # (`innerCols = [⟨7⟩]` -> exactly that column) is inhabited AND distinct
    # from the two answers the inherited rule would give there (the wrapper's
    # own identity, and the default-context answer). Then the frozen obligation
    # is closed VERBATIM by the frozen `loom_solve`, so the method's own
    # obligation still discharges and the statement is byte-identical.
    #
    # The `have`s are LIVE, not decoration: measured with a real build, replacing
    # the constant arm's `out ≠ [⟨9⟩]` with the FALSE `out ≠ []` makes the file
    # fail to elaborate (exit 1), while the case as written elaborates (exit 0).
    # So a false claim about the same point leaves an unsolved goal rather than
    # passing quietly. If the post-image were unsatisfiable at an F2P-shaped
    # point => PRECOND-TOO-STRONG / SPEC-UNSATISFIABLE.
    # =====================================================================
    {
        "id": "admiss-f2p-arms-satisfiable",
        "kind": "admissibility",
        "expect": "verify",
        "module": _with_proof(
            "prove_correct groupingColumns by\n"
            "  have admissConstantArm :\n"
            "      ∃ out : List GroupCol,\n"
            "        out = ([] : List GroupCol) ∧ out ≠ [(⟨9⟩ : GroupCol)]\n"
            "          ∧ out ≠ [(⟨8⟩ : GroupCol)] :=\n"
            "    ⟨[], rfl, by decide, by decide⟩\n"
            "  have admissColumnArm :\n"
            "      ∃ out : List GroupCol,\n"
            "        out = [(⟨7⟩ : GroupCol)] ∧ out ≠ [(⟨9⟩ : GroupCol)]\n"
            "          ∧ out ≠ ([] : List GroupCol) :=\n"
            "    ⟨[(⟨7⟩ : GroupCol)], rfl, by decide, by decide⟩\n"
            "  loom_solve"),
        "rationale": "ADMISSIBILITY on a total carrier. The method declares no "
                     "`require`, so nothing can EXCLUDE a normal input; the "
                     "residual risk this case closes is the other direction — that "
                     "the obligation is unsatisfiable, or degenerate, at exactly an "
                     "F2P-shaped input. Two `have`s discharge by evaluation that "
                     "the post-image is inhabited at the constant arm (no "
                     "contributed columns) and at the column-like arm (exactly the "
                     "wrapped expression's own column), and that at each point the "
                     "demanded answer DIFFERS from both answers the inherited rule "
                     "produces there (the wrapper's own identity; the "
                     "default-context answer) — so the spec is non-degenerate at "
                     "the F2P points, not merely satisfiable. The frozen obligation "
                     "is then closed verbatim by the frozen `loom_solve`, and the "
                     "obligation STATEMENT (the `method` header) is byte-identical. "
                     "Measured live: substituting a FALSE claim at the same point "
                     "(`out ≠ []` on the constant arm) fails to elaborate, so these "
                     "`have`s carry information. Ports the nagini admiss-wrapper, "
                     "re-aimed: its precondition-admits-an-F2P-node half has no "
                     "precondition to attack here, but its satisfiable-at-an-F2P-"
                     "input half does. Must verify, else PRECOND-TOO-STRONG.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at
    # a concrete input and the refinement argument for why its faithful real
    # counterpart would NOT resolve the failing tests.
    # =====================================================================
    {
        "id": "return-self",
        "kind": "uniqueness",
        "expect": "reject",
        # The composite contributes ITSELF: return the wrapping expression's own
        # identity as a single grouping column (the inherited [self] rule for a
        # non-aggregating expression). Reads no input's structure — a constant
        # over selfCol.
        "module": _with_impl(
            "    let result : List GroupCol := [selfCol]\n    return result"),
        "refinement": "contributing the wrapping expression's own identity is the "
                      "inherited base rule for a non-aggregating expression "
                      "([self]) — the pre-patch behaviour. For a wrapped CONSTANT "
                      "the inner contributes no columns, so the transparent wrapper "
                      "must contribute none; this rival puts the wrapper itself "
                      "into the grouping clause instead — exactly the invalid "
                      "GROUP-BY the issue reports. The empty-grouping test asserts "
                      "no contributed columns and would FAIL — it would NOT resolve.",
        "rationale": "REJECT from `out = innerCols`: the rival returns `[selfCol]` "
                     "regardless of the input, which differs from `innerCols` "
                     "whenever they are unequal. Refuted at the constant arm "
                     "(innerCols = []): `[selfCol]` is non-empty, `innerCols` is "
                     "empty. Discrimination comes from selfCol vs innerCols.",
        "witness": _witness("groupingColumnsTester ⟨3⟩ false [] []"),
    },
    {
        "id": "drop-all-columns",
        "kind": "uniqueness",
        "expect": "reject",
        # Contribute NOTHING: always return the empty column list. Correct on the
        # constant arm, wrong on the column-like arm where the inner contributes a
        # real grouping column.
        "module": _with_impl(
            "    let result : List GroupCol := []\n    return result"),
        "refinement": "returning no columns for every wrapped expression DROPS a "
                      "real grouping column when the inner expression is "
                      "column-like: the query would group by fewer columns than "
                      "intended, changing its semantics. The non-empty-grouping "
                      "test asserts the wrapped column-like expression's own column "
                      "is contributed and would FAIL — it would NOT resolve.",
        "rationale": "REJECT from `out = innerCols`: the rival returns `[]` "
                     "regardless of the input, differing from `innerCols` whenever "
                     "the inner contributes ≥1 column. Refuted at the column-like "
                     "arm (innerCols a non-empty singleton), where the rival drops "
                     "it. Discrimination comes from innerCols being non-empty.",
        "witness": _witness("groupingColumnsTester ⟨0⟩ false [⟨5⟩] [⟨5⟩]"),
    },
    {
        "id": "wrong-identity",
        "kind": "uniqueness",
        "expect": "reject",
        # Right SHAPE, wrong identity: contribute one column per inner column but
        # each a DIFFERENT identity (a shifted ref). Correct length, wrong objects.
        "module": _with_impl(
            "    let result : List GroupCol := innerCols.map (fun c => ⟨c.ref + 1⟩)\n"
            "    return result"),
        "refinement": "contributing a DIFFERENT column object for each inner column "
                      "(the right count, wrong identity) groups by the wrong "
                      "columns; the non-empty-grouping test reads back the wrapped "
                      "expression's OWN column by identity and would get a different "
                      "object — it would NOT resolve.",
        "rationale": "REJECT from `out = innerCols`: the rival maps each column to a "
                     "distinct shifted identity, so it equals `innerCols` only when "
                     "`innerCols` is empty. Refuted at a non-empty singleton where "
                     "the identities differ. Discrimination comes from innerCols' "
                     "element identity — a near-miss the drop-all rival (wrong "
                     "LENGTH) does not subsume.",
        "witness": _witness("groupingColumnsTester ⟨0⟩ true [⟨1⟩] [⟨9⟩]"),
    },
    {
        "id": "inherited-base-rule",
        "kind": "uniqueness",
        "expect": "reject",
        # The full inherited (pre-patch) rule: a non-aggregating expression stands
        # in for itself; an aggregating one re-queries its sources WITHOUT
        # forwarding the requested context. This is the literal pre-patch skeleton
        # (identical to Solution_prepatch.lean's do-block).
        "module": _with_impl(
            "    let result : List GroupCol :=\n"
            "      if innerHasAggregate then innerColsDefaultContext\n"
            "      else [selfCol]\n"
            "    return result"),
        "refinement": "this IS the inherited pre-patch behaviour: a non-aggregating "
                      "wrapped expression is replaced by the wrapper itself and an "
                      "aggregating one re-queries its sources with the requested "
                      "context dropped. On a wrapped constant (non-aggregating) it "
                      "puts the wrapper into the grouping clause — the invalid "
                      "GROUP BY the issue reports; the empty-grouping test asserts "
                      "no contributed columns and would FAIL. It is the exact bug "
                      "the fix removes — it would NOT resolve.",
        "rationale": "REJECT from `out = innerCols`: on the non-aggregating arm the "
                     "rival returns `[selfCol]` where the spec demands `innerCols`. "
                     "Refuted at the constant arm (innerHasAggregate = false, "
                     "innerCols = []): the rival returns the non-empty `[selfCol]`. "
                     "This rival additionally exercises the free binders "
                     "`innerHasAggregate` and `innerColsDefaultContext` (present in "
                     "its body), which the value rivals do not touch.",
        "witness": _witness("groupingColumnsTester ⟨4⟩ false [] [⟨8⟩]"),
    },
    {
        "id": "reorder-columns",
        "kind": "uniqueness",
        "expect": "reject",
        # SET-equal, SEQUENCE-different: contribute exactly the inner expression's
        # columns but in reversed order. Every rival above is refuted at a point
        # where innerCols has length 0 or 1 — where order and multiplicity are
        # INVISIBLE — so none of them probes the sequence structure the mapping
        # declares load-bearing ("order and length preserved"). This one is
        # refuted at the first length-2 point in the battery.
        "module": _with_impl(
            "    let result : List GroupCol := innerCols.reverse\n"
            "    return result"),
        "refinement": "contributing the right SET of grouping columns in the wrong "
                      "ORDER is a faithful-looking near-miss: the wrapped "
                      "expression's columns all reach the grouping clause, but the "
                      "sequence the wrapper hands back is not the sequence the "
                      "wrapped expression produced. The contributed columns are "
                      "consumed positionally downstream, so a wrapper that permutes "
                      "them does not forward transparently; the non-empty-grouping "
                      "test reads the contributed columns back in the wrapped "
                      "expression's own order and would get a different sequence — "
                      "it would NOT resolve.",
        "rationale": "REJECT from `out = innerCols`: `List` equality is "
                     "order-sensitive, so `innerCols.reverse = innerCols` fails for "
                     "any innerCols whose first and last elements differ. Refuted at "
                     "the first LENGTH-2 point in the battery "
                     "(innerCols = [⟨6⟩, ⟨7⟩]), where the rival returns "
                     "[⟨7⟩, ⟨6⟩]. Discrimination comes from the ORDER of innerCols — "
                     "a dimension every other rival leaves unprobed, because each is "
                     "refuted where innerCols has length 0 or 1 and order and "
                     "multiplicity are invisible. Independently rebuilt: elaborates "
                     "against the rival (exit 0), fails against the frozen solution "
                     "(exit 1) with `decide` refuting the concrete claim, and the "
                     "flipped claim (`= true`) ELABORATES against the frozen "
                     "solution (exit 0) — so gold's exit code tracks the claim.",
        "witness": _witness("groupingColumnsTester ⟨2⟩ true [⟨6⟩, ⟨7⟩] []"),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 7 SPEC cases (1 soundness
# positive, 1 admissibility, 1 frame-mutation, 4 value/uniqueness rivals) plus a
# 2-case AXIOM lane. This bundle models a NARROWER surface: nagini contracts TWO
# functions (base_group_by_cols — the wrapped node's constant/column-like
# dichotomy — and wrapper_group_by_cols — the delegation), whereas velvet models
# only the delegation (`out = innerCols`) and folds the dichotomy into the free
# input `innerCols`. The accounting below records every sibling case.
#
#   sibling case                    -> here
#   ---------------------------------------------------------------------
#   pos-reorder (base dichotomy)    -> pos-ignore-aggregate       RE-EXPRESSED
#   admiss-wrapper                  -> admiss-f2p-arms-satisfiable RE-AIMED
#   frame-write-inner               -> (none)                     VACUOUS (no heap)
#   return-self                     -> return-self                PORTED
#   drop-constant (base const arm)  -> return-self / inherited    FOLDED
#   drop-column   (base col  arm)   -> drop-all-columns           PORTED
#   wrong-identity(base col  arm)   -> wrong-identity             PORTED
#   (no sibling)                    -> reorder-columns            ADDED (order)
#   AXIOM_TESTS (2)                 -> (none)                     DROPPED (G-AX)
#
# RE-EXPRESSED (positive control): the sibling reorders the two branches of the
#   base dichotomy. That dichotomy is not a separate function here — it is the
#   free input `innerCols` — so a branch reorder is not expressible. The ARGUMENT
#   ("a structurally different but faithful impl must verify") is carried by a
#   reshape that IS expressible on the delegation: inspect the free aggregate
#   flag but return `innerCols` on both arms. Verified to build (proof retuned to
#   close the collapsed conditional).
# RE-AIMED (admissibility): the sibling self-calls to prove the precondition admits
#   an F2P-shaped node. This bundle declares NO `require` clause (pre-conditions
#   region empty), so that HALF of the sibling case has no precondition to
#   interrogate. The other half — that the obligation is SATISFIABLE, and
#   non-degenerate, at an F2P-shaped input — is the analogue on a total carrier and
#   IS expressible: see `admiss-f2p-arms-satisfiable`, which discharges the
#   post-image at both F2P arms by evaluation, as `have`s, before closing the frozen
#   obligation verbatim. An earlier revision of this manifest recorded the whole
#   lane as vacuous on the grounds that an admissibility assert "would be the
#   trivial `innerCols = innerCols`". That reasoning was wrong: the assert is stated
#   at CONCRETE points (innerCols = [] and [⟨7⟩]), where the demanded answer is a
#   literal, and it is measurably live — substituting a false claim at the same
#   point fails to elaborate. Dropping the lane removed the only direction of this
#   gate that tests PRECOND-TOO-STRONG, so it is restored.
# VACUOUS (frame-mutation): the sibling carries this MANDATORY because its inputs
#   are held at Acc(.,1/2) an impl can illegally write. This backend is
#   referentially transparent and declares no `mut` binder — every input is an
#   immutable value with no heap footprint — so there is no read-only field to
#   overwrite and no substitute probe. Not fabricated (porting map: vacuous here).
# PORTED / FOLDED (value rivals): return-self ports directly ([node_id] ->
#   [selfCol]). drop-column ports as drop-all-columns ([] on a column-like inner).
#   wrong-identity ports as a shifted-identity map (right count, wrong objects).
#   drop-constant (base: always [node_id], wrong on the constant arm) is FOLDED:
#   on this carrier "always contribute the wrapper/self on a constant" is exactly
#   what return-self and inherited-base-rule do at innerCols = [], so it needs no
#   separate rival. The inherited (pre-patch) full rule is added as a further rival
#   so the two free binders (innerHasAggregate, innerColsDefaultContext) appear in
#   a rival body and vary across the witness set. Each rival carries a
#   machine-checked witness that ELABORATES against the rival and FAILS against
#   the frozen solution (two real builds per case).
#
#   ADDED (order): `reorder-columns`. Every ported rival above is refuted at a point
#   where innerCols has length 0 or 1, and at those lengths ORDER and MULTIPLICITY
#   are invisible — so the ported set left the sequence structure that mapping.md
#   declares load-bearing ("order and length preserved") entirely unprobed. The
#   reversal rival is set-equal to gold and sequence-different, refuted at the first
#   length-2 point in the battery. It has no sibling counterpart because nagini's
#   base dichotomy only ever produced lists of length 0 or 1; folding that dichotomy
#   into the free input `innerCols` is exactly what makes longer lists reachable
#   here, so this is a carrier-specific gap the port had no sibling case to catch.
#
#   The five witnesses probe five DISTINCT input tuples; across them selfCol takes
#   {3,0,0,4,2}, innerHasAggregate takes {false,true}, innerCols takes {[],[⟨5⟩],
#   [⟨1⟩],[],[⟨6⟩,⟨7⟩]}, innerColsDefaultContext takes {[],[⟨5⟩],[⟨9⟩],[⟨8⟩],[]}. The
#   load-bearing binder innerCols is varied across the constant arm ([]), the
#   column-like arm (non-empty singleton), and a length-2 point where order and
#   multiplicity become observable. The two aggregate-related binders are
#   varied too, though (see the DEFENDED-SURFACE note) the spec is genuinely
#   independent of them: no rival can be wrong in a way distinguished ONLY by
#   those binders, because any impl branching on them yet returning innerCols
#   VERIFIES. That is a property of the modeled behaviour (the transparent wrapper
#   ignores aggregation and default-context), not a gap in the battery.
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job; this bundle declares no
# axiom (the delegated callee is a directive-7 free input, not an oracle), so
# there is nothing to probe and the gate ignores AXIOM_TESTS regardless.
AXIOM_TESTS = []
