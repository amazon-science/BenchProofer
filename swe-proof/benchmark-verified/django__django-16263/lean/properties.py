"""properties.py — G-PBT falsification battery for django__django-16263 (lean).

NOT a Lean file. A record of adversarially-reasoned falsification cases the
G-PBT gate executes and stamps a verdict onto. Each SPEC case is a full
``Solution.lean`` variant that shares the FROZEN spec byte-for-byte (region
surgery: only text inside the ``-- impl-start`` / ``-- impl-end`` region — and,
for a positive that legitimately re-proves, inside ``-- proof-start`` /
``-- proof-end`` — is changed, so ``markers.same_spec`` holds by construction
and the single ``theorem correct_countPlan`` STATEMENT stays byte-identical).
``expect="verify"`` passes iff the variant is in scope AND the file elaborates
with the obligation closed; ``expect="reject"`` passes iff the variant is in
scope AND it does NOT verify AND the case's refutation ``witness`` holds of the
rival while FAILING on the frozen solution.

PORT NOTE
---------
This is a PORT of the nagini falsification battery (``../nagini/properties.py``)
onto this backend's carrier. The nagini bundle contracts TWO functions over
read-only sequence carriers, each carrying a fractional-permission
precondition and a termination obligation; this Lean bundle models the SINGLE
purely-functional core — one total function from the query state to the planning
outcome. Every nagini rival that attacked a *decision* carries over as an attack
on one clause of the one modeled obligation; the nagini rivals that attacked the
permission system or the termination obligation have no expressible counterpart
here. The per-case mapping (and every principled omission) is in ``assessment``.

DEFENDED SURFACE (one modeled obligation, ``correct_countPlan``)
---------------------------------------------------------------
``problem_spec_countPlan st result`` pins the whole planning outcome as two
independent top-level conjuncts:

  (C1) ``result.useSubquery = needsSubquery st``
       — the wrapping decision. It is a five-way disjunction over the query
       state: the grouping-tuple flag, the slicing flag, ``hasExistingAgg st``,
       the distinct flag, and the set-operation flag. ``hasExistingAgg`` is
       itself a disjunction of two independent terms: some MATERIALISED carried
       clause that is not one of the summary aggregates is an aggregate OR an
       OVER-style window, or the query carries post-grouping filters.

  (C2) ``result.keptExisting = if needsSubquery st then keptExisting st else []``
       — which carried clause aliases survive. Two arms, selected by the
       distinct flag: when distinct, exactly the materialised carried clauses;
       otherwise exactly the carried clauses whose alias appears in the mask the
       summary aggregates keep alive (each summary aggregate's own name together
       with the alias names it refers to). Note the non-distinct arm filters on
       "not a summary aggregate" and NOT on "materialised": a clause present
       only as a named alias but referred to by a summary aggregate IS kept.
       When no wrapping subquery is needed, nothing is kept at all.

Both conjuncts are GROUNDED in the input carrier: every helper
(``existingAnns`` / ``hasExistingAgg`` / ``needsSubquery`` / ``addedMask`` /
``keptExisting``) unfolds completely over ``st``, and the bundle declares no
``opaque`` callee and consumes no ``axiom``. So there is no answer-key oracle an
implementation could echo without doing the work, and — unlike the ports that
have to condition on an opaque term — every refutation here is stated at a fully
CONCRETE query state and closed by evaluation.

ADVERSARIAL READ of the nagini case classes on this carrier
-----------------------------------------------------------
  * FRAME / PERMISSION MUTATION — VACUOUS. Lean is referentially transparent: an
    input carries no heap permission, there is no read-only half-grant to
    overwrite and no aliasing to exploit. The nagini rivals that satisfied a
    postcondition by WRITING into a read-only input carrier have no expressible
    instance here, and no substitute is fabricated.

  * DIVERGENCE / NON-TERMINATION — VACUOUS. ``implementation_countPlan`` is a
    total Lean ``def``; a diverging body cannot be written at all, so the
    vacuous-satisfaction-by-divergence rival the nagini battery pins with a
    termination obligation is not expressible. (This is the lean disposition
    specifically: the class is collapsed by the carrier, not admitted by the
    spec.)

  * ADMISSIBILITY — APPLIES, and is carried. ``correct_countPlan`` is
    ``∀ (st : QState), ...`` with no hypothesis, so there is no precondition
    binder to show establishable — but "no precondition" is NOT a reason to drop
    this lane, and an earlier reading of this battery that said so was wrong. On
    a total carrier the analogue of PRECOND-TOO-STRONG is the obligation being
    UNSATISFIABLE at exactly an F2P-shaped input, which a positive that
    discharges the spec predicate at that concrete input — by evaluation, as a
    ``have``, before closing the frozen obligation verbatim — tests directly.
    ``admiss-ground-f2p-states`` does that at all three F2P-shaped states. This
    carrier is fully decidable, so the lane costs nothing and is not vacuous.

  * UNGROUNDED-ORACLE ECHO — VACUOUS, for the reason given above. In its place
    the battery carries honest structural-reshape POSITIVE CONTROLS that must
    verify with a proof that actually closes.

  * PARTIAL-DOMAIN / VALUE — APPLIES, and is the whole battery. Rivals correct
    over part of the carrier but diverging exactly where the modeled decision
    bites.

WITNESSES
---------
On a tactic-proof backend "did not verify" is the DEFAULT outcome of reshaping
an implementation — the frozen script is tuned to the frozen form — so a
rejection alone attributes nothing to the spec. Every ``expect="reject"`` case
therefore carries a Lean snippet stating ``problem_spec_countPlan`` directly at
one concrete query state and refuting it by evaluation. Each was checked to HOLD
of its rival and to FAIL on the frozen solution, so it discriminates rather than
asserting a tautology. No witness binds anything, so none can be inconsistent.

POINT SPREAD. The spec takes ONE input binder, ``st`` — but ``st`` is a record
whose fields are the real axes, and a field every witness holds at one value is
a field no rival was built to abuse. So the twelve reject witnesses probe twelve
DISTINCT query states and between them move EVERY field of the carrier:
``anns`` ranges over empty, one and two clauses; ``selected``,
``containsAggregate``, ``containsOverClause``, ``added``, ``distinct``,
``isSliced``, ``groupByTuple``, ``combinator`` and ``postGroupFilter`` each take
both settings; ``refs`` takes both empty and non-empty; ``aliasName`` varies.
Every disjunct of the wrapping decision and both arms of the keep-set are
independently pinned by a rival that drops exactly that disjunct/arm, and no two
rivals share a refutation point.

AXIOM lane: dropped. The bundle declares no ``opaque`` callee and consumes no
``axiom`` (its two non-``I`` legs are deep-model A-references validated
executably by G-CONF), so the nagini ``AXIOM_TESTS`` have no counterpart in this
gate, which ignores that lane in any case.
"""
from pathlib import Path

INSTANCE = "django__django-16263"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Region anchors. Each is a contiguous slice lying ENTIRELY inside the impl
# region, except _P_HASAGG_LEMMA / _P_MASK_LEMMA / _P_REWRITE which lie entirely
# inside the proof region (used only by the two positives that re-prove). Every
# anchor is unique in Solution.lean; _swap asserts both at import time, so the
# manifest breaks loudly if the frozen solution ever drifts.
# ---------------------------------------------------------------------------

# The materialised-carried-clause selection.
_I_EXISTING = "  let existing := st.anns.filter (fun a => !a.added && a.selected)\n"

# The whole accumulate loop that decides whether a materialised carried clause
# is an aggregate or an OVER-style window.
_I_HASAGG_LOOP = (
    "  let mut hasAgg := false\n"
    "  for a in existing do\n"
    "    if a.containsAggregate || a.containsOverClause then\n"
    "      hasAgg := true\n"
)

# Just the per-clause test inside that loop.
_I_AGG_TEST = (
    "    if a.containsAggregate || a.containsOverClause then\n"
    "      hasAgg := true"
)

# The wrapping decision itself.
_I_NEEDSSUB = (
    "  let needsSub :=\n"
    "    st.groupByTuple || st.isSliced || (hasAgg || st.postGroupFilter)\n"
    "      || st.distinct || st.combinator"
)

# The whole mask-building loop.
_I_MASK_LOOP = (
    "    let mut mask : List String := []\n"
    "    for a in st.anns do\n"
    "      if a.added then\n"
    "        mask := mask ++ (a.aliasName :: a.refs)\n"
)

# Just the mask contribution of one summary aggregate.
_I_MASK_ADD = "        mask := mask ++ (a.aliasName :: a.refs)"

# The whole keep-set, both arms.
_I_KEPT = (
    "    let kept :=\n"
    "      if st.distinct then\n"
    "        existing.map (fun a => a.aliasName)\n"
    "      else\n"
    "        (st.anns.filter (fun a => !a.added && mask.contains a.aliasName)).map\n"
    "          (fun a => a.aliasName)"
)

# Just the non-distinct arm's filter.
_I_KEPT_FILTER = (
    "        (st.anns.filter (fun a => !a.added && mask.contains a.aliasName)).map\n"
    "          (fun a => a.aliasName)"
)

# The no-wrapping branch's returned outcome.
_I_ELSE = "    return { useSubquery := false, keptExisting := [] }"

# --- proof region (only the two positives touch these) ---
_P_HASAGG_LEMMA = """  have hbool : ∀ (l : List Ann) (b0 : Bool),
      List.foldl (fun b a => if (a.containsAggregate || a.containsOverClause) = true then true else b) b0 l
        = (b0 || l.any (fun a => a.containsAggregate || a.containsOverClause)) := by
    intro l
    induction l with
    | nil => simp
    | cons x xs ih =>
      intro b0
      simp only [List.foldl_cons, List.any_cons]
      rw [ih]
      by_cases h : (x.containsAggregate || x.containsOverClause) = true <;> simp [h]
"""

_P_MASK_LEMMA = """  have hlist : ∀ (l : List Ann) (acc : List String),
      List.foldl (fun b a => if a.added = true then b ++ (a.aliasName :: a.refs) else b) acc l
        = acc ++ (l.filter (fun a => a.added)).flatMap (fun a => a.aliasName :: a.refs) := by
    intro l
    induction l with
    | nil => simp
    | cons x xs ih =>
      intro acc
      simp only [List.foldl_cons, List.filter_cons]
      by_cases h : x.added = true <;> simp [h, ih, List.append_assoc]
"""

_P_REWRITE = "  rw [hbool, hlist]"

# The `intro st` that opens the frozen tactic body. The admissibility positive
# inserts its grounding `have`s directly after it, so the frozen script below
# is retained verbatim as the closing step.
_P_INTRO = "  intro st\n"


# ---------------------------------------------------------------------------
# Witness construction. Every refutation is stated at a fully CONCRETE query
# state and closed by evaluation, so no witness binds a variable and none can
# carry inconsistent hypotheses.
# ---------------------------------------------------------------------------

def _ann(name, selected=False, agg=False, over=False, added=False, refs=()):
    def b(x):
        return "true" if x else "false"
    rl = ", ".join(f'"{r}"' for r in refs)
    return (f'{{ aliasName := "{name}", selected := {b(selected)}, '
            f'containsAggregate := {b(agg)},\n'
            f'                 containsOverClause := {b(over)}, added := {b(added)}, '
            f'refs := [{rl}] }}')


def _state(anns, groupByTuple=False, isSliced=False, distinct=False,
           combinator=False, postGroupFilter=False):
    def b(x):
        return "true" if x else "false"
    body = ",\n               ".join(anns)
    return (f'{{ anns := [{body}],\n'
            f'      groupByTuple := {b(groupByTuple)}, isSliced := {b(isSliced)}, '
            f'distinct := {b(distinct)},\n'
            f'      combinator := {b(combinator)}, '
            f'postGroupFilter := {b(postGroupFilter)} }}')


# ---------------------------------------------------------------------------
# ADMISSIBILITY grounding. Same carrier literals, but emitted on ONE line: these
# go inside the frozen tactic block, where Lean's whitespace sensitivity rejects
# the multi-line record layout `_state` uses at top level.
# ---------------------------------------------------------------------------

def _ann1(name, selected=False, agg=False, over=False, added=False, refs=()):
    def b(x):
        return "true" if x else "false"
    rl = ", ".join(f'"{r}"' for r in refs)
    return (f'{{ aliasName := "{name}", selected := {b(selected)}, '
            f'containsAggregate := {b(agg)}, containsOverClause := {b(over)}, '
            f'added := {b(added)}, refs := [{rl}] }}')


def _state1(anns, groupByTuple=False, isSliced=False, distinct=False,
            combinator=False, postGroupFilter=False):
    def b(x):
        return "true" if x else "false"
    return ('{ anns := [' + ', '.join(anns) + '], '
            f'groupByTuple := {b(groupByTuple)}, isSliced := {b(isSliced)}, '
            f'distinct := {b(distinct)}, combinator := {b(combinator)}, '
            f'postGroupFilter := {b(postGroupFilter)} }}')


def _ground_have(name, state):
    """`have <name> : problem_spec_countPlan ST (implementation_countPlan ST)`.

    Discharges the frozen obligation's own predicate BY EVALUATION at one
    concrete query state. Nothing is assumed and no declaration is added — it is
    a local `have` inside the frozen tactic body, closed by `decide`.
    """
    return (f"  have {name} : problem_spec_countPlan\n"
            f"      ({state})\n"
            f"      (implementation_countPlan\n"
            f"        ({state})) := by\n"
            f"    unfold problem_spec_countPlan\n"
            f"    decide\n")


# The three F2P-shaped query states: each carries the summary aggregate the row
# count injects (`added`), alongside one already-present clause of each shape the
# failing tests observe.
_A1 = _state1([_ann1("cnt", agg=True),
               _ann1("total", selected=True, agg=True, added=True)])
_A2 = _state1([_ann1("name_l", selected=True),
               _ann1("total", selected=True, agg=True, added=True)])
_A3 = _state1([_ann1("cnt", selected=True, agg=True),
               _ann1("total", selected=True, agg=True, added=True)])

_ADMISS_PROOF = (_P_INTRO
                 + _ground_have("_ground_alias_only", _A1)
                 + _ground_have("_ground_materialised_scalar", _A2)
                 + _ground_have("_ground_unreferenced_agg", _A3))


def _witness(comment, state):
    """`¬ problem_spec_countPlan ST (implementation_countPlan ST)`, by evaluation.

    States the frozen spec predicate directly at one concrete query state. It
    ELABORATES exactly when the outcome the variant computes at that state
    contradicts the spec, and FAILS on the frozen solution (which satisfies the
    spec everywhere) — the two halves that make it a discriminator rather than a
    tautology.
    """
    indented = "\n".join(
        ("    " + ln if i == 0 else "  " + ln)
        for i, ln in enumerate(state.splitlines()))
    reindented = "\n".join(
        ("      " + ln.strip() if i == 0 else "    " + ln)
        for i, ln in enumerate(state.splitlines()))
    return (f"{comment}\n"
            f"example : ¬ problem_spec_countPlan\n"
            f"{indented}\n"
            f"    (implementation_countPlan\n"
            f"{reindented}) := by\n"
            f"  unfold problem_spec_countPlan\n"
            f"  decide\n")


# --- the twelve refutation points, one per rival ---------------------------

# P1: one materialised carried clause that is a plain scalar expression.
_P1 = _state([_ann("name_l", selected=True)])
# P2: one carried clause present only as a named alias, itself an aggregate.
_P2 = _state([_ann("cnt", selected=False, agg=True)])
# P3: a materialised carried aggregate that no summary aggregate refers to.
_P3 = _state([_ann("cnt", selected=True, agg=True),
              _ann("total", selected=True, agg=True, added=True)])
# P4: the same, but the summary aggregate DOES refer to the carried clause.
_P4 = _state([_ann("cnt", selected=True, agg=True),
              _ann("total", selected=True, agg=True, added=True, refs=("cnt",))])
# P5: nothing present at all.
_P5 = _state([])
# P6: distinct, with a materialised scalar carried clause nothing refers to.
_P6 = _state([_ann("name_l", selected=True),
              _ann("total", selected=True, agg=True, added=True)],
             distinct=True)
# P7: sliced, with a NON-materialised carried clause the summary refers to.
_P7 = _state([_ann("cnt", selected=False),
              _ann("total", selected=True, agg=True, added=True, refs=("cnt",))],
             isSliced=True)
# P8: post-grouping filters present, nothing else.
_P8 = _state([], postGroupFilter=True)
# P9: one materialised carried clause that is an OVER-style window, not an
#     aggregate.
_P9 = _state([_ann("rk", selected=True, over=True)])
# P10: the grouping-tuple flag alone.
_P10 = _state([], groupByTuple=True)
# P11: the set-operation flag alone.
_P11 = _state([], combinator=True)
# P12: two materialised scalar carried clauses, no wrapping required.
_P12 = _state([_ann("p_l", selected=True), _ann("q_l", selected=True)])


# ===========================================================================
# SPEC LANE
# ===========================================================================
SPEC_TESTS = [

    # -- 1. POSITIVE CONTROL (soundness) — clause C1's aggregate/window scan ---
    # Nagini's `pos-control-esfd-accumulate` ported: there the decision-#1
    # accumulate loop was reshaped from an if-branch to a boolean accumulate;
    # here the whole accumulate loop collapses to the closed-form existential
    # over the same per-clause test. Structurally different, observationally
    # identical. The proof re-closes honestly: the frozen script's induction
    # lemma over the loop's fold is no longer needed and is dropped, and the
    # surviving rewrite carries the rest. The `theorem correct_countPlan`
    # STATEMENT is byte-identical; nothing is assumed. MUST verify.
    {
        "id": "pos-control-hasagg-closed-form",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _swap(
                _swap(
                    _BASE, _I_HASAGG_LOOP,
                    "  let hasAgg := existing.any "
                    "(fun a => a.containsAggregate || a.containsOverClause)\n",
                ),
                _P_HASAGG_LEMMA, "",
            ),
            _P_REWRITE, "  rw [hlist]",
        ),
        "rationale": "a structurally-different but CORRECT implementation of "
                     "clause C1's materialised-clause scan (the accumulate loop "
                     "replaced by the closed-form existential over the same "
                     "per-clause aggregate-or-window test) MUST verify, with the "
                     "obligation statement unchanged and re-proved rather than "
                     "weakened. If it cannot, C1 is SPEC-TOO-STRONG: it would be "
                     "pinning the loop's syntactic shape rather than the wrapping "
                     "decision, and would reject a faithful patch that computed "
                     "the same answer.",
    },

    # -- 2. POSITIVE CONTROL (soundness) — clause C2's mask assembly ----------
    # Nagini's `pos-control-ick-accumulate` ported to the mask channel: the
    # append-accumulate loop that collects what the summary aggregates keep
    # alive collapses to the closed-form flatMap over the same per-clause
    # contribution. The frozen script's fold-induction lemma for that loop is
    # dropped and the surviving rewrite carries the rest. MUST verify.
    {
        "id": "pos-control-mask-closed-form",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _swap(
                _swap(
                    _BASE, _I_MASK_LOOP,
                    "    let mask : List String :=\n"
                    "      (st.anns.filter (fun a => a.added)).flatMap "
                    "(fun a => a.aliasName :: a.refs)\n",
                ),
                _P_MASK_LEMMA, "",
            ),
            _P_REWRITE, "  rw [hbool]",
        ),
        "rationale": "a structurally-different but CORRECT implementation of "
                     "clause C2's keep-alive mask (the append-accumulate loop "
                     "replaced by the closed-form flatMap over the same "
                     "per-clause contribution) MUST verify, obligation statement "
                     "unchanged and re-proved. If it cannot, C2 is "
                     "SPEC-TOO-STRONG on the mask channel.",
    },

    # -- 3. ADMISSIBILITY (non-vacuity at the F2P-shaped inputs) --------------
    # Nagini's `admiss-esfd-read-input` ported. There the precondition was a
    # fractional-permission grant plus an equal-length requirement, and the case
    # showed it establishable for a normal input. This carrier is total and the
    # obligation is an unconditional `∀ st`, so there is no permission grant to
    # establish — but the ANALOGUE on a total carrier is the obligation being
    # unsatisfiable at exactly an F2P-shaped input, and that is a real thing to
    # test rather than a vacuous one. This case discharges the spec predicate BY
    # EVALUATION at the three F2P-shaped query states as three `have`s, and only
    # then closes the frozen obligation with the frozen script verbatim.
    {
        "id": "admiss-ground-f2p-states",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _P_INTRO, _ADMISS_PROOF),
        "rationale": "the frozen obligation carries no hypothesis, so there is no "
                     "precondition binder to attack directly; on this total "
                     "carrier the analogue of PRECOND-TOO-STRONG is the obligation "
                     "being UNSATISFIABLE at exactly an F2P-shaped input. This "
                     "case tests that directly, at the three states the failing "
                     "tests observe, each carrying the summary aggregate the row "
                     "count injects: (a) an already-present clause that is an "
                     "aggregate but present only as a named alias — the spec must "
                     "admit useSubquery = false with an empty keep-set; (b) a "
                     "materialised plain scalar clause — again no wrapping and "
                     "nothing kept; (c) a materialised aggregate clause the "
                     "summary refers to nothing — wrapping IS required and the "
                     "keep-set must still come back empty, the clause pruned. "
                     "Each is discharged by `decide` as a `have` BEFORE the frozen "
                     "script closes the obligation verbatim, so the two conjuncts "
                     "are shown jointly satisfiable at those very inputs rather "
                     "than only provable in the abstract. If any `have` failed, "
                     "the modeled decision would be unsatisfiable at an F2P input "
                     "and every reject case's attribution would be worthless. "
                     "Nothing is assumed: no new declaration, no assumption token, "
                     "the theorem STATEMENT is byte-identical, and the frozen "
                     "tactic body is retained unchanged as the closing step.",
    },

    # -- 4. PARTIAL-DOMAIN — C1, the PREDICATE axis ---------------------------
    # Nagini's `partial-domain-esfd-presence-only` ported. There the rival forced
    # the derived form on the mere PRESENCE of a selected column, dropping the
    # is-a-summary conjunct; here it forces the wrapping subquery whenever ANY
    # materialised carried clause is present, ignoring whether that clause
    # aggregates or windows.
    {
        "id": "partial-domain-presence-forces-wrapping",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _I_AGG_TEST,
            "    let _ := a\n"
            "    hasAgg := true",
        ),
        "refinement": "the faithful real patch of this rival is the UNCHANGED "
                     "base behavior on this axis: the presence of a carried "
                     "clause, aggregate or not, forces the wrapping subquery. It "
                     "therefore still emits two SELECTs for a row count over a "
                     "query carrying one plain scalar named clause, where the "
                     "F2P expects exactly one and the clause's name absent — so "
                     "it does NOT resolve. A rival that VERIFIED here would be a "
                     "true verify-does-not-imply-resolve break.",
        "rationale": "REJECT from clause C1 (result.useSubquery = needsSubquery "
                     "st): at a query state whose only carried clause is "
                     "materialised but is a plain scalar expression, "
                     "hasExistingAgg is false and no other disjunct fires, so "
                     "the spec pins useSubquery = false; the rival returns true. "
                     "The witness varies `selected`=true with "
                     "`containsAggregate`/`containsOverClause`=false, which is "
                     "exactly the sub-domain the dropped conjunct governs.",
        "witness": _witness(
            "-- One materialised carried clause, a plain scalar expression, and "
            "no other\n-- reason to wrap: the spec pins no wrapping and an empty "
            "keep-set.", _P1),
    },

    # -- 4. PARTIAL-DOMAIN — C1, the MATERIALISATION axis ---------------------
    # Nagini's `partial-domain-esfd-source-all` ported. There the rival built the
    # decision from ALL carried clauses including alias-only ones, dropping the
    # is-selected conjunct; here it drops the `selected` guard from the
    # materialised-clause selection, so a clause present only as a named alias
    # counts toward the wrapping decision.
    {
        "id": "partial-domain-source-all-clauses",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _I_EXISTING,
            "  let existing := st.anns.filter (fun a => !a.added)\n",
        ),
        "refinement": "the faithful real patch of this rival reads the full "
                     "carried-clause collection rather than the materialised "
                     "one, so a clause introduced only as a named alias still "
                     "forces the wrapping subquery: two SELECTs for a row count "
                     "over a query carrying one aliased aggregate, where the F2P "
                     "expects exactly one and the alias absent. It does NOT "
                     "resolve.",
        "rationale": "REJECT from clause C1: at a query state whose only carried "
                     "clause is NOT materialised (present only as a named alias) "
                     "though itself an aggregate, existingAnns is empty, so "
                     "hasExistingAgg is false and the spec pins useSubquery = "
                     "false; the rival returns true. The witness holds "
                     "`selected`=false with `containsAggregate`=true — the exact "
                     "complement of the previous rival's point, so neither "
                     "witness refutes the other's rival.",
        "witness": _witness(
            "-- One carried clause present only as a named alias, itself an "
            "aggregate:\n-- it is not materialised, so it forces no wrapping.",
            _P2),
    },

    # -- 5. PARTIAL-DOMAIN — C1, the post-grouping-filter term ----------------
    # No nagini counterpart on this axis (its carrier folded the retained-filter
    # bit into a plain int the rivals never dropped). Ported forward as a real
    # independent term of hasExistingAgg on THIS carrier.
    {
        "id": "partial-domain-drop-postgroup-filter",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _I_NEEDSSUB,
            "  let needsSub :=\n"
            "    st.groupByTuple || st.isSliced || hasAgg\n"
            "      || st.distinct || st.combinator",
        ),
        "refinement": "the faithful real patch of this rival decides the "
                     "wrapping from the materialised carried clauses alone and "
                     "never consults the post-grouping filter state. A row count "
                     "over a query filtered against a named aggregate would then "
                     "be computed without the wrapping subquery, in a single "
                     "grouped statement — a wrong count, breaking the retained "
                     "P2P behavior for filtering against an aggregate. It "
                     "resolves nothing.",
        "rationale": "REJECT from clause C1: hasExistingAgg is a disjunction of "
                     "the materialised-clause scan AND the post-grouping-filter "
                     "term; at a query state with no carried clauses at all but "
                     "post-grouping filters present, the spec pins useSubquery = "
                     "true and the rival returns false. The witness is the only "
                     "one holding `postGroupFilter`=true, so this term is pinned "
                     "independently of the scan.",
        "witness": _witness(
            "-- No carried clauses, but post-grouping filters are present: the "
            "spec\n-- pins wrapping on that term alone.", _P8),
    },

    # -- 6. PARTIAL-DOMAIN — C1, the OVER-style-window term ------------------
    # The nagini carrier collapsed "aggregate" and "window" into one summary bit,
    # so it had no rival for this axis. On THIS carrier they are two separate
    # fields joined by a disjunction, and a rival reading only the aggregate
    # field is wrong on the window sub-domain. Without this case every witness
    # would hold `containsOverClause` at false and such a rival would verify.
    {
        "id": "partial-domain-drop-window-term",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _I_AGG_TEST,
            "    if a.containsAggregate then\n"
            "      hasAgg := true",
        ),
        "refinement": "the faithful real patch of this rival inspects only "
                     "whether a materialised carried clause aggregates, never "
                     "whether it is an OVER-style window. A row count over a "
                     "query carrying a materialised window clause would then skip "
                     "the wrapping subquery and be computed in a single grouped "
                     "statement, returning one row per group instead of one "
                     "total — a wrong count. It resolves nothing.",
        "rationale": "REJECT from clause C1: the per-clause test is a "
                     "disjunction of the aggregate field and the OVER-style "
                     "window field; at a query state whose only materialised "
                     "carried clause is a window and not an aggregate, the spec "
                     "pins useSubquery = true and the rival returns false. The "
                     "witness is the only one holding `containsOverClause`=true, "
                     "so that field is discriminated rather than held fixed.",
        "witness": _witness(
            "-- The one materialised carried clause is an OVER-style window, "
            "not an\n-- aggregate: the spec still pins wrapping.", _P9),
    },

    # -- 7. PARTIAL-DOMAIN — C1, the grouping-tuple disjunct -----------------
    # Mechanical clause-pin (nagini's `support-*` class): drops one unchanged but
    # load-bearing disjunct of the wrapping decision. Carries a real refinement.
    {
        "id": "support-drop-grouptuple-disjunct",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _I_NEEDSSUB,
            "  let needsSub :=\n"
            "    st.isSliced || (hasAgg || st.postGroupFilter)\n"
            "      || st.distinct || st.combinator",
        ),
        "refinement": "the faithful real patch of this rival stops wrapping for "
                     "an explicitly-grouped query, so the summary aggregate is "
                     "computed in the same grouped statement and yields one row "
                     "per group rather than one total — a wrong result for every "
                     "retained grouping behavior. It resolves nothing.",
        "rationale": "REJECT from clause C1: the wrapping decision is a "
                     "five-way disjunction and this rival drops the "
                     "grouping-tuple disjunct. At a query state with no carried "
                     "clauses whose only set flag is the grouping tuple, the "
                     "spec pins useSubquery = true and the rival returns false. "
                     "The witness is the only one holding `groupByTuple`=true, "
                     "so that disjunct is pinned independently.",
        "witness": _witness(
            "-- The grouping-tuple flag alone forces wrapping.", _P10),
    },

    # -- 8. PARTIAL-DOMAIN — C1, the set-operation disjunct ------------------
    # Same mechanical class on the remaining unattacked disjunct.
    {
        "id": "support-drop-combinator-disjunct",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _I_NEEDSSUB,
            "  let needsSub :=\n"
            "    st.groupByTuple || st.isSliced || (hasAgg || st.postGroupFilter)\n"
            "      || st.distinct",
        ),
        "refinement": "the faithful real patch of this rival stops wrapping for "
                     "a query built from a set operation, so the summary "
                     "aggregate is pushed into the combined statement where it "
                     "cannot be evaluated over the combined row set — a wrong "
                     "result for every retained set-operation behavior. It "
                     "resolves nothing.",
        "rationale": "REJECT from clause C1: this rival drops the set-operation "
                     "disjunct. At a query state with no carried clauses whose "
                     "only set flag is the set-operation flag, the spec pins "
                     "useSubquery = true and the rival returns false. The witness "
                     "is the only one holding `combinator`=true.",
        "witness": _witness(
            "-- The set-operation flag alone forces wrapping.", _P11),
    },

    # -- 9. PARTIAL-DOMAIN — C1's polarity -----------------------------------
    # Nagini's `support-esfd-inverted` ported: return the NEGATION of the
    # wrapping decision. Pins the polarity, and specifically the DEFAULT: a query
    # carrying nothing at all needs no wrapping.
    {
        "id": "support-inverted-decision",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _I_NEEDSSUB,
            "  let needsSub :=\n"
            "    !(st.groupByTuple || st.isSliced || (hasAgg || st.postGroupFilter)\n"
            "      || st.distinct || st.combinator)",
        ),
        "refinement": "inverting the decision wraps exactly the queries that "
                     "need no wrapping and leaves unwrapped exactly those that "
                     "do: an extra SELECT for a plain row count and a wrong "
                     "grouped result for a query carrying a materialised "
                     "aggregate. Its faithful real patch resolves nothing and "
                     "breaks the retained behavior wholesale.",
        "rationale": "REJECT from clause C1: `!(...)` contradicts the pinned "
                     "value at every state where the decision is determinate. "
                     "The witness takes the DEFAULT point — a query carrying no "
                     "clauses at all and no set flags — where the spec pins "
                     "useSubquery = false; it is the only witness probing the "
                     "empty carrier with every flag clear, so the default is "
                     "pinned rather than inferred.",
        "witness": _witness(
            "-- Nothing present at all: the spec pins no wrapping and an empty "
            "keep-set.", _P5),
    },

    # -- 10. PARTIAL-DOMAIN — C2, the reference-based pruning ------------------
    # Nagini's `partial-domain-ick-keep-all` ported. There the rival kept EVERY
    # carried clause regardless of references; here it applies the distinct arm
    # unconditionally, so every materialised carried clause survives and nothing
    # is pruned by what the summary aggregates refer to.
    {
        "id": "partial-domain-keep-all-materialised",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _I_KEPT,
            "    let kept := existing.map (fun a => a.aliasName)",
        ),
        "refinement": "the faithful real patch of this rival is the UNCHANGED "
                     "base masking behavior: the inner statement keeps the full "
                     "materialised carried-clause set with no pruning by what "
                     "the summary aggregates refer to. A row count over a query "
                     "carrying a materialised aggregate that nothing refers to "
                     "would then still emit that clause's name inside the "
                     "wrapped statement, where the F2P requires two SELECTs with "
                     "the name absent. It does NOT resolve.",
        "rationale": "REJECT from clause C2 (result.keptExisting = if "
                     "needsSubquery st then keptExisting st else []): at a "
                     "non-distinct state with a materialised carried aggregate "
                     "that the summary aggregate does not refer to, wrapping is "
                     "required and the spec's non-distinct arm keeps nothing; the "
                     "rival keeps that clause. The witness holds `distinct`=false "
                     "with a summary aggregate whose `refs` is empty — the exact "
                     "sub-domain the dropped reference filter governs.",
        "witness": _witness(
            "-- Wrapping is required and the summary aggregate refers to "
            "nothing, so\n-- the materialised carried aggregate is pruned.", _P3),
    },

    # -- 11. PARTIAL-DOMAIN — C2, the reference channel -----------------------
    # Nagini's `partial-domain-ick-drop-refs` ported: keep a clause only when it
    # is one of the pushed-out summary names, discarding the reference channel.
    {
        "id": "partial-domain-drop-reference-channel",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _I_MASK_ADD,
            "        mask := mask ++ [a.aliasName]",
        ),
        "refinement": "the faithful real patch of this rival builds the "
                     "surviving mask from the summary aggregates' own names only "
                     "and never unions in the alias names they refer to. A "
                     "carried clause a summary aggregate DOES refer to would then "
                     "be dropped from the wrapped statement, leaving the outer "
                     "reference resolving to nothing — the retained behavior "
                     "requires that clause's name to appear twice. It resolves "
                     "nothing.",
        "rationale": "REJECT from clause C2: the keep-alive mask is each summary "
                     "aggregate's own name TOGETHER WITH the alias names it "
                     "refers to, and this rival discards the second half. At a "
                     "non-distinct state where the summary aggregate refers to "
                     "the materialised carried clause, the spec keeps that "
                     "clause and the rival keeps nothing. The witness is the "
                     "previous point with `refs` moved from empty to non-empty, "
                     "so neither rival is refuted at the other's input.",
        "witness": _witness(
            "-- Wrapping is required and the summary aggregate DOES refer to the "
            "carried\n-- clause, so that clause survives.", _P4),
    },

    # -- 12. PARTIAL-DOMAIN — C2, the distinct arm ---------------------------
    # No nagini counterpart: its carrier does not model the distinct flag at all.
    # On THIS carrier C2 has two arms selected by that flag, and a rival applying
    # the reference-based rebuild unconditionally is wrong on the distinct
    # sub-domain. Without this case every witness would hold `distinct` at false.
    {
        "id": "partial-domain-drop-distinct-arm",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _I_KEPT,
            "    let kept :=\n"
            "      (st.anns.filter (fun a => !a.added && mask.contains a.aliasName)).map\n"
            "        (fun a => a.aliasName)",
        ),
        "refinement": "the faithful real patch of this rival re-masks the "
                     "wrapped statement from the summary aggregates' references "
                     "even for a distinct query, dropping a materialised carried "
                     "clause that nothing refers to. Re-masking a distinct query "
                     "alters the row set it distinguishes on, so the count comes "
                     "back wrong — it breaks the retained distinct-aggregation "
                     "behavior and resolves nothing.",
        "rationale": "REJECT from clause C2: the keep-set has TWO arms, and on "
                     "the distinct arm exactly the materialised carried clauses "
                     "survive. At a distinct state with a materialised scalar "
                     "carried clause that the summary aggregate does not refer "
                     "to, the spec keeps it and the rival keeps nothing. The "
                     "witness is the only one holding `distinct`=true, so the arm "
                     "selector is discriminated rather than held fixed.",
        "witness": _witness(
            "-- The query is distinct, so the materialised carried clause "
            "survives even\n-- though the summary aggregate refers to nothing.",
            _P6),
    },

    # -- 13. PARTIAL-DOMAIN — C2, the non-distinct arm's filter --------------
    # A NEAR-MISS with no nagini counterpart: it agrees with the frozen spec
    # wherever the referred-to clause happens to be materialised, and diverges
    # only for a clause present as a named alias. That distinction is the one the
    # non-distinct arm makes explicitly (it filters on "not a summary aggregate",
    # NOT on "materialised"), so it needs its own point.
    {
        "id": "near-miss-kept-filters-on-materialised",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _I_KEPT_FILTER,
            "        (st.anns.filter (fun a =>\n"
            "            !a.added && a.selected && mask.contains a.aliasName)).map\n"
            "          (fun a => a.aliasName)",
        ),
        "refinement": "the faithful real patch of this rival intersects the "
                     "surviving mask with the materialised clause set instead of "
                     "replacing the mask outright, so a clause carried only as a "
                     "named alias but referred to by a summary aggregate is "
                     "dropped from the wrapped statement. The outer reference "
                     "then resolves to nothing and the aggregation errors out or "
                     "returns a wrong value — it resolves nothing.",
        "rationale": "REJECT from clause C2: the non-distinct arm keeps every "
                     "carried clause in the keep-alive mask irrespective of "
                     "whether it is materialised, and this rival adds a "
                     "materialisation guard. At a sliced non-distinct state where "
                     "the summary aggregate refers to a NON-materialised carried "
                     "clause, the spec keeps it and the rival keeps nothing. The "
                     "witness is the only one holding `isSliced`=true, and the "
                     "only one where a referred-to clause has `selected`=false — "
                     "the sub-domain that separates this near-miss from the "
                     "frozen decision, which the reference-channel rival's point "
                     "does not reach.",
        "witness": _witness(
            "-- Wrapping is forced by slicing; the summary aggregate refers to a "
            "carried\n-- clause that is NOT materialised, and that clause still "
            "survives.", _P7),
    },

    # -- 14. PARTIAL-DOMAIN — C2, the no-wrapping arm ------------------------
    # The remaining independent arm of C2: when no wrapping subquery is needed,
    # NOTHING is kept. No nagini counterpart (its decision-#2 model had no
    # no-subquery regime).
    {
        "id": "partial-domain-nowrap-leaks-kept",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _I_ELSE,
            "    return { useSubquery := false,\n"
            "             keptExisting := existing.map (fun a => a.aliasName) }",
        ),
        "refinement": "the faithful real patch of this rival leaves the "
                     "materialised carried clauses in place when no wrapping "
                     "subquery is used, instead of inlining and masking them "
                     "away. A row count over a query carrying plain scalar named "
                     "clauses would then still emit those names in the single "
                     "statement, where the F2P requires exactly one SELECT with "
                     "the name absent. It does NOT resolve.",
        "rationale": "REJECT from clause C2's second arm (`else []`): when "
                     "needsSubquery st is false the spec pins keptExisting = [] "
                     "unconditionally, and this rival returns the materialised "
                     "carried clause names instead. Its clause-C1 answer is "
                     "correct at the witness point, so the rejection is "
                     "attributable to the no-wrapping arm alone. The witness is "
                     "the only one carrying TWO already-present (non-summary) "
                     "clauses — four others carry two `anns` in total, but each of "
                     "those has one of them `added` — so the keep-set is pinned as "
                     "empty rather than as a singleton.",
        "witness": _witness(
            "-- Two materialised plain scalar carried clauses: no wrapping is "
            "required\n-- and nothing at all is kept.", _P12),
    },
]
