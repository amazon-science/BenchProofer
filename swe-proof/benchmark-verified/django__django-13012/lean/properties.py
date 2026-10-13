"""properties.py — G-PBT falsification battery for django__django-13012 (lean).

NOT a Lean file; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region — and, for a case that legitimately re-proves, inside the
``-- proof-start`` / ``-- proof-end`` region — is changed, so
``markers.same_spec`` holds and the ``theorem correct_wrapperGroupByCols``
STATEMENT stays byte-identical). ``expect:"verify"`` passes iff (in scope AND the
file elaborates with the obligation closed, no ``sorry``/``admit``/
``native_decide`` and no new ``axiom``/``theorem``); ``expect:"reject"`` passes
iff (in scope AND it does NOT verify AND the case's refutation ``witness`` holds
of the rival while FAILING on the frozen solution).

DEFENDED SURFACE (one modeled behavior; a single spec predicate over one input
binder that matters). A transparent wrapping expression decides which columns it
contributes to a query's grouping clause:

  wrapperGroupByCols (e : Expr) (result : List Col) : Prop
    result = e.innerCols          -- THE load-bearing (and only) clause

``e`` is an ``Expr`` with three observed fields — ``selfCol`` (the wrapper's own
identity as a single grouping column), ``innerContainsAggregate`` (whether the
wrapped expression contains an aggregate), and ``innerCols`` (the columns the
WRAPPED expression contributes). There is NO opaque answer key to echo:
``result = e.innerCols`` grounds the result in an actual input field
(spec_guide directive 8). The pinned behaviour is a property of the WRAPPER — it
contributes EXACTLY the columns the wrapped expression contributes, and NEVER
substitutes its own identity, drops columns, or perturbs their identities.

BINDER STRUCTURE (read this before judging binder coverage). The postcondition
depends on EXACTLY ONE field — ``innerCols``. The other two are DELIBERATELY free
and irrelevant to the modeled behaviour:

  * ``selfCol`` — the wrapper's own identity. It exists only so a rival can state
    the WRONG answer (contribute the wrapper itself). The correct result never
    mentions it.
  * ``innerContainsAggregate`` — the observation the INHERITED (pre-patch) rule
    branched on: a non-aggregating wrapper stood in for itself (``[selfCol]``).
    It is present only so the pre-patch skeleton is expressible while the spec
    stays byte-identical. The whole POINT of the fix is that a transparent
    wrapper IGNORES it and forwards regardless.

So no rival can be wrong in a way DISTINGUISHED ONLY by ``innerContainsAggregate``:
any impl that branches on it yet returns ``innerCols`` on every branch VERIFIES
(correctly — the spec is independent of it), and any impl returning something
ELSE is caught by the ``innerCols`` clause on whichever branch fires. That binder
is genuinely irrelevant to the modeled behaviour (see ``assessment``); the reject
witnesses nonetheless VARY it (``{false, true}``) so the coverage tool does not
flag it pinned, while the DISCRIMINATION always comes from ``innerCols`` (and,
for the wrong-answer rivals, from ``selfCol`` being substituted for it).

``innerCols`` itself is varied over three points that change what is OBSERVABLE,
not merely three spellings: ``[]`` (substituting the wrapper is visible; length
and order are not), a singleton (element identity is visible; order is not), and
a two-element list (order and multiplicity become visible — the only place a
reordering rival is refutable, since shorter lists are palindromes).

ADVERSARIAL READ of the nagini classes on this carrier:

  * ADMISSIBILITY — LANDED (``admiss-f2p-inputs``), not vacuous. The frozen
    obligation has no precondition hypothesis, but that is not a reason to drop
    the lane: on a total carrier the PRECOND-TOO-STRONG analogue is the obligation
    being unsatisfiable at exactly an F2P-shaped input, which a positive that
    discharges it BY EVALUATION at that concrete input — as a ``have``, before
    closing the frozen obligation verbatim — tests directly. See the accounting
    block for why this is not the trivial ``innerCols = innerCols``.

  * FRAME / PERMISSION MUTATION — VACUOUS. The nagini sibling holds the node at a
    half-permission (``Acc(.,1/2)``) and makes its MANDATORY frame-mutation rival
    WRITE to it (rebinding ``node.inner_id = node.node_id``). Lean is
    referentially transparent: ``e`` is an immutable value with no heap footprint,
    no ``mut`` binder and no aliasing — there is no read-only field to overwrite
    and no substitute probe. NOT fabricated (per the porting map, this class is
    vacuous here); see ``assessment``.

  * NAGINI's DEEP-MODEL cases (``base_group_by_cols``' constant/column-like
    dichotomy: DROP_CONSTANT, DROP_COLUMN, WRONG_IDENTITY, and the branch-reorder
    positive) attacked a SEPARATE modeled function nagini spelled out. This bundle
    does NOT model that dichotomy: the wrapped expression's own rule is folded
    into the FREE input ``innerCols`` (directive 7), so ``[]`` for a constant and
    ``[inner]`` for a column-like node are simply two VALUES of ``innerCols``. The
    dichotomy cases therefore re-express as value rivals over the single
    ``result = e.innerCols`` clause (see the accounting block at the bottom).

  * UNGROUNDED-ORACLE ECHO — N/A: the post-image is an input field, not an
    axiomatized oracle; the ``axioms`` region declares no ``opaque``/``axiom``.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen ``intro e; rfl`` is tuned to the frozen
``Id.run do; return e.innerCols`` — so a rejection alone attributes nothing to the
spec. Every ``expect="reject"`` case therefore carries a Lean snippet proving the
rival CONTRADICTS the spec at one concrete input. Each was checked (two real
``lake env lean`` builds) to ELABORATE against its rival and to FAIL against the
frozen solution (so it discriminates rather than asserting a tautology). ``Col``
derives ``DecidableEq`` and ``Expr`` literals are ground, so the snippets
``unfold`` the spec + impl and ``decide`` a concrete ``List Col`` (in)equality;
against gold the same ``decide`` faces ``e.innerCols = e.innerCols`` and fails.

AXIOM lane: EMPTY. meta.json ``axioms == []`` and ``deep_model_references == []``;
the modeled behavior is a total forwarding of an input field, so there is no
axiom-soundness obligation to probe here (that lane is G-AX's). ``AXIOM_TESTS`` is
therefore empty.
"""
from pathlib import Path

INSTANCE = "django__django-13012"
BACKEND = "lean"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- region anchors (each unique inside Solution.lean; verified at load) ----
# The two-line impl def is the load-bearing shape of the impl region; every impl
# reshape lands entirely inside `-- impl-start`/`-- impl-end`.
_IMPL = (
    "def implementation_wrapperGroupByCols (e : Expr) : List Col := Id.run do\n"
    "  return e.innerCols"
)
# Frozen tactic body (lies wholly inside `-- proof-start`/`-- proof-end`). Only a
# case that legitimately re-proves touches this; the reject rivals leave it frozen
# (they are judged by their witness, not by whether this script happens to break).
_PROOF = "  intro e\n  rfl"


def _with_impl(new_impl: str) -> str:
    """Solution.lean with ONLY the impl body replaced (spec + proof view intact)."""
    return _swap(_BASE, _IMPL, new_impl)


# ---- witness scaffold. The spec here is a bare predicate, so a witness states it
# ---- directly at a ground `Expr` literal: `¬ problem_spec_wrapperGroupByCols e
# ---- (implementation_wrapperGroupByCols e)`. Checked in a file whose frozen
# ---- obligation is elided by the gate, so no tactic script can mask the verdict.
# ---- `Col` derives DecidableEq and the literal is ground, so `decide` settles the
# ---- `List Col` (in)equality after unfolding. ----
def _witness(self_ref: int, agg: str, inner: str) -> str:
    e = ("{ selfCol := ⟨%d⟩, innerContainsAggregate := %s, innerCols := %s }"
         % (self_ref, agg, inner))
    return (
        "example : ¬ problem_spec_wrapperGroupByCols\n"
        f"    {e}\n"
        "    (implementation_wrapperGroupByCols\n"
        f"      {e}) := by\n"
        "  unfold problem_spec_wrapperGroupByCols implementation_wrapperGroupByCols\n"
        "  decide\n"
    )


def _with_proof(new_proof: str) -> str:
    """Solution.lean with ONLY the proof body replaced (spec + impl intact)."""
    return _swap(_BASE, _PROOF, new_proof)


# The two F2P-shaped inputs, as ground `Expr` literals. `_E_CONST` is the
# discriminating shape — a wrapped expression that contributes NO columns, where
# the transparent wrapper must contribute none either; `_E_COL` is the
# column-like shape, where the wrapped expression contributes one real column.
# `selfCol` is held distinct from every element of `innerCols` (ref 9 vs 7) so
# "contribute the wrapper itself" is observably different from forwarding.
_E_CONST = "{ selfCol := ⟨9⟩, innerContainsAggregate := false, innerCols := [] }"
_E_COL = "{ selfCol := ⟨9⟩, innerContainsAggregate := false, innerCols := [⟨7⟩] }"


def _discharge(e: str, name: str) -> str:
    """`have <name> : <the frozen obligation, instantiated at `e`> := by decide`."""
    return (
        f"  have {name} : problem_spec_wrapperGroupByCols\n      {e}\n"
        f"      (implementation_wrapperGroupByCols\n        {e}) := by\n"
        "    unfold problem_spec_wrapperGroupByCols implementation_wrapperGroupByCols\n"
        "    decide\n")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # implementations that MUST verify, else SPEC-TOO-STRONG. Each keeps the
    # `theorem correct_wrapperGroupByCols` statement byte-identical.
    # =====================================================================
    {
        "id": "pos-direct-forward",
        "kind": "soundness",
        "expect": "verify",
        # Functional reshape: drop the `Id.run do` scaffold and forward the wrapped
        # expression's contribution directly. Definitionally identical, so the
        # frozen `intro e; rfl` still closes (verified with a real build); no proof
        # authoring, no helper lemma, no assumption token.
        "module": _with_impl(
            "def implementation_wrapperGroupByCols (e : Expr) : List Col :=\n"
            "  e.innerCols"),
        "rationale": "correct reshape of the mutable-do forwarding into a direct "
                     "return of `e.innerCols`; it computes the same value on every "
                     "input, so it must satisfy `result = e.innerCols` — else "
                     "SPEC-TOO-STRONG. Proof: the frozen `intro e; rfl` still "
                     "closes (the result is now definitionally `e.innerCols`).",
    },
    {
        "id": "pos-ignore-aggregate",
        "kind": "soundness",
        "expect": "verify",
        # Structurally different CORRECT reshape: INSPECT the (free) aggregate flag
        # yet forward `e.innerCols` on BOTH branches — a direct demonstration that
        # the spec is correctly independent of `innerContainsAggregate`. The
        # decision collapses to `e.innerCols` on both arms; the proof is retuned to
        # close the collapsed conditional (verified with a real build). Only the
        # impl and proof regions change; the theorem STATEMENT is byte-identical.
        "module": _swap(
            _with_impl(
                "def implementation_wrapperGroupByCols (e : Expr) : List Col := Id.run do\n"
                "  if e.innerContainsAggregate then\n"
                "    return e.innerCols\n"
                "  return e.innerCols"),
            _PROOF,
            "  intro e\n"
            "  unfold problem_spec_wrapperGroupByCols implementation_wrapperGroupByCols\n"
            "  simp only [Id.run]\n"
            "  split <;> rfl"),
        "rationale": "structurally different CORRECT reshape: it branches on the "
                     "free aggregate flag but forwards `e.innerCols` on both arms, "
                     "so `result = e.innerCols` holds regardless of the flag. A "
                     "faithful reshape MUST verify, else SPEC-TOO-STRONG; it also "
                     "witnesses that the spec is correctly independent of "
                     "`innerContainsAggregate`. Proof: `split <;> rfl` closes both "
                     "collapsed arms; no new axiom/lemma, statement unchanged.",
    },

    {
        "id": "admiss-f2p-inputs",
        "kind": "admissibility",
        "expect": "verify",
        # PRECOND-TOO-STRONG probe. The obligation carries no hypothesis to admit,
        # so the analogue on this total carrier is: is the obligation SATISFIABLE
        # at exactly an F2P-shaped input? This case discharges it BY EVALUATION at
        # both F2P shapes as `have`s — the wrapped-nothing shape (innerCols = [],
        # the discriminating one) and the column-like shape (innerCols = [⟨7⟩]) —
        # and only then closes the frozen obligation verbatim with the frozen
        # `rfl`. Impl untouched; only the proof region changes; the theorem
        # STATEMENT is byte-identical. If either `decide` could not close, the
        # obligation would be unsatisfiable exactly where the modeled behaviour is
        # exercised => PRECOND-TOO-STRONG.
        "module": _with_proof(
            _discharge(_E_CONST, "hWrappedNothing")
            + _discharge(_E_COL, "hWrappedColumn")
            + "  intro e\n  rfl"),
        "rationale": "admissibility (PRECOND-TOO-STRONG lane). The obligation is "
                     "unguarded (`∀ e`, total behaviour), so the analogue of "
                     "admitting a precondition is showing the obligation is "
                     "SATISFIABLE at an F2P-shaped input rather than only "
                     "vacuously provable in general. Both F2P shapes are "
                     "discharged by `decide` on ground literals as `have`s before "
                     "the frozen `intro e; rfl` closes the obligation verbatim: "
                     "the wrapped-nothing shape (innerCols = [], where the "
                     "wrapper must contribute nothing) and the column-like shape "
                     "(innerCols = [⟨7⟩], where it must contribute the wrapped "
                     "expression's own column). `selfCol` is ⟨9⟩, distinct from "
                     "every innerCols element, so neither `have` is satisfiable by "
                     "an impl that substitutes the wrapper for the wrapped "
                     "expression. Not a restatement of the obligation: the `have`s "
                     "are CLOSED by evaluation at concrete inputs, so an "
                     "obligation unsatisfiable at those points would fail here "
                     "while still elaborating in the abstract.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # concrete input and the refinement argument for why its faithful real
    # counterpart would NOT resolve the failing F2P tests. The four witnesses
    # spread `innerCols` across the constant arm (`[]`) and the column-like arm
    # (a non-empty singleton) and vary `selfCol` and the free aggregate flag.
    # =====================================================================
    {
        "id": "return-self",
        "kind": "uniqueness",
        "expect": "reject",
        # The pre-patch behaviour: the wrapper contributes ITSELF (its own identity
        # as a single grouping column) instead of forwarding — the inherited
        # BaseExpression `[self]` default for a non-aggregating expression.
        "module": _with_impl(
            "def implementation_wrapperGroupByCols (e : Expr) : List Col := Id.run do\n"
            "  return [e.selfCol]"),
        "refinement": "contributing the wrapper's own identity is the inherited base "
                      "rule for a non-aggregating expression ([self]) — the literal "
                      "pre-patch behaviour. For a wrapped CONSTANT the inner "
                      "contributes no columns, so the transparent wrapper must "
                      "contribute none; this rival puts the wrapper itself into the "
                      "grouping clause instead — exactly the invalid GROUP BY the "
                      "issue reports. The empty-group-by F2P test asserts no "
                      "contributed columns and would FAIL — it does NOT resolve.",
        "rationale": "REJECT from `result = e.innerCols`: the rival returns "
                     "`[e.selfCol]` regardless of the input, differing from "
                     "`e.innerCols` whenever they are unequal. Refuted at the "
                     "constant arm (innerCols = []): `[selfCol]` is non-empty, "
                     "`innerCols` is empty. Discrimination comes from selfCol vs "
                     "innerCols.",
        "witness": _witness(3, "false", "[]"),
    },
    {
        "id": "drop-all-columns",
        "kind": "uniqueness",
        "expect": "reject",
        # Contribute NOTHING: always return the empty column list. Correct on the
        # constant arm, wrong on the column-like arm where the inner contributes a
        # real grouping column. Ports the nagini DROP_COLUMN rival.
        "module": _with_impl(
            "def implementation_wrapperGroupByCols (e : Expr) : List Col := Id.run do\n"
            "  return []"),
        "refinement": "returning no columns for every wrapped expression DROPS a "
                      "real grouping column when the inner expression is "
                      "column-like: the query would group by fewer columns than "
                      "intended, changing its semantics. The non-empty-group-by F2P "
                      "test asserts the wrapped column-like expression's own column "
                      "is contributed and would FAIL — it does NOT resolve.",
        "rationale": "REJECT from `result = e.innerCols`: the rival returns `[]` "
                     "regardless of the input, differing from `e.innerCols` whenever "
                     "the inner contributes ≥1 column. Refuted at the column-like "
                     "arm (innerCols a non-empty singleton), where the rival drops "
                     "it. Discrimination comes from innerCols being non-empty.",
        "witness": _witness(0, "false", "[⟨5⟩]"),
    },
    {
        "id": "wrong-identity",
        "kind": "uniqueness",
        "expect": "reject",
        # Right SHAPE, wrong identity: contribute one column per inner column but
        # each a DIFFERENT identity (a shifted ref). Correct length, wrong objects.
        # Ports the nagini WRONG_IDENTITY rival (node_id + 1 -> ref + 1).
        "module": _with_impl(
            "def implementation_wrapperGroupByCols (e : Expr) : List Col := Id.run do\n"
            "  return e.innerCols.map (fun c => ⟨c.ref + 1⟩)"),
        "refinement": "contributing a DIFFERENT column object for each inner column "
                      "(right count, wrong identity) groups by the wrong columns; "
                      "the non-empty-group-by F2P test reads back the wrapped "
                      "expression's OWN column by identity and would get a different "
                      "object — it does NOT resolve.",
        "rationale": "REJECT from `result = e.innerCols`: the rival maps each column "
                     "to a distinct shifted identity, so it equals `e.innerCols` "
                     "only when `innerCols` is empty. Refuted at a non-empty "
                     "singleton where the identities differ. Discrimination comes "
                     "from innerCols' element identity — a near-miss the drop-all "
                     "rival (wrong LENGTH) does not subsume, so it carries its own "
                     "distinguishing input.",
        "witness": _witness(0, "true", "[⟨1⟩]"),
    },
    {
        "id": "inherited-base-rule",
        "kind": "uniqueness",
        "expect": "reject",
        # The full inherited (pre-patch) rule: a non-aggregating wrapper stands in
        # for itself (`[selfCol]`); an aggregating one forwards. This is the literal
        # pre-patch skeleton (Solution_prepatch.lean's do-block) and additionally
        # exercises the free `innerContainsAggregate` binder in a rival body.
        "module": _with_impl(
            "def implementation_wrapperGroupByCols (e : Expr) : List Col := Id.run do\n"
            "  if e.innerContainsAggregate then\n"
            "    return e.innerCols\n"
            "  return [e.selfCol]"),
        "refinement": "this IS the inherited pre-patch behaviour: a non-aggregating "
                      "wrapped expression is replaced by the wrapper itself while an "
                      "aggregating one forwards. On a wrapped constant "
                      "(non-aggregating) it puts the wrapper into the grouping "
                      "clause — the invalid GROUP BY the issue reports; the "
                      "empty-group-by F2P test asserts no contributed columns and "
                      "would FAIL. It is the exact bug the fix removes — it does NOT "
                      "resolve.",
        "rationale": "REJECT from `result = e.innerCols`: on the non-aggregating arm "
                     "the rival returns `[e.selfCol]` where the spec demands "
                     "`e.innerCols`. Refuted at the constant arm "
                     "(innerContainsAggregate = false, innerCols = []): the rival "
                     "returns the non-empty `[selfCol]`. This rival additionally "
                     "exercises the free `innerContainsAggregate` binder (present in "
                     "its body), which the value rivals do not branch on.",
        "witness": _witness(4, "false", "[]"),
    },
    {
        "id": "reorder-columns",
        "kind": "uniqueness",
        "expect": "reject",
        # ORDER rival: contribute exactly the right columns, each with the right
        # identity and the right multiplicity, but in the REVERSED order. Every
        # existing rival is caught by a SET-level defect (wrong element, missing
        # element, wrong identity); this one is set-equal to the required answer
        # and differs only in sequence, so it probes the part of
        # `result = e.innerCols` that list equality pins beyond membership. Needs
        # a ≥2-element innerCols to be observable at all — the first input in the
        # battery that is not empty-or-singleton.
        "module": _with_impl(
            "def implementation_wrapperGroupByCols (e : Expr) : List Col := Id.run do\n"
            "  return e.innerCols.reverse"),
        "refinement": "contributing the wrapped expression's columns in a different "
                      "ORDER is not a faithful forward: the wrapped expression's "
                      "contribution is a sequence, and a grouping clause built from "
                      "it is read back positionally. The non-empty-group-by F2P test "
                      "compares the contributed list against the wrapped "
                      "expression's own list, which is an ordered comparison, so a "
                      "reordering impl would FAIL it once the wrapped expression "
                      "contributes more than one column — it does NOT resolve. It "
                      "also does not even attempt the reported symptom: on a wrapped "
                      "constant it returns [] like gold, so it is wrong ONLY in the "
                      "sequencing the spec pins.",
        "rationale": "REJECT from `result = e.innerCols`: list equality in Lean is "
                     "positional, so `e.innerCols.reverse = e.innerCols` fails for "
                     "any innerCols that is not a palindrome. Refuted at a "
                     "two-element innerCols ([⟨2⟩, ⟨6⟩]) where the rival returns "
                     "[⟨6⟩, ⟨2⟩] — the same COLUMNS with the same multiplicities, "
                     "in the wrong sequence. Discrimination comes from innerCols' "
                     "ORDER, which no other rival probes: return-self and "
                     "inherited-base-rule substitute a different element, "
                     "drop-all-columns changes the length, and wrong-identity "
                     "changes the identities. Both builds re-run: the witness "
                     "elaborates against the rival and its `decide` on gold reports "
                     "the proposition false (a plain evaluation, not a stuck "
                     "reduction).",
        "witness": _witness(0, "true", "[⟨2⟩, ⟨6⟩]"),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> lean accounting. The sibling battery has 7 SPEC cases (1 soundness
# positive, 1 admissibility, 1 frame-mutation, 4 value/uniqueness rivals) plus a
# 2-case AXIOM lane. This bundle models a NARROWER surface: nagini contracts TWO
# functions (base_group_by_cols — the wrapped node's constant/column-like
# dichotomy — and wrapper_group_by_cols — the delegation), whereas lean models
# only the delegation (`result = e.innerCols`) and folds the dichotomy into the
# free input field `innerCols`. Every sibling case is recorded below.
#
#   sibling case                    -> here
#   ---------------------------------------------------------------------
#   pos-reorder (base dichotomy)    -> pos-ignore-aggregate       RE-EXPRESSED
#                                      (+ pos-direct-forward)      ADDED positive
#   admiss-wrapper                  -> admiss-f2p-inputs          PORTED (re-shaped)
#   frame-write-inner               -> (none)                     VACUOUS (no heap)
#   return-self                     -> return-self                PORTED
#   drop-constant (base const arm)  -> return-self / inherited    FOLDED
#   drop-column   (base col  arm)   -> drop-all-columns           PORTED
#   wrong-identity(base col  arm)   -> wrong-identity             PORTED
#   AXIOM_TESTS (2)                 -> (none)                     DROPPED (G-AX)
#
# RE-EXPRESSED (positive control): the sibling reorders the two branches of the
#   base dichotomy. That dichotomy is not a separate function here — it is the
#   free input `innerCols` — so a branch reorder of it is not expressible. The
#   ARGUMENT ("a structurally different but faithful impl must verify") is carried
#   by a reshape that IS expressible on the delegation: inspect the free aggregate
#   flag but forward `innerCols` on both arms (pos-ignore-aggregate, proof retuned
#   to close the collapsed conditional). A second positive (pos-direct-forward)
#   drops the `Id.run do` scaffold entirely; the frozen `rfl` still closes it.
# PORTED, RE-SHAPED (admissibility): the sibling self-calls to prove the
#   precondition admits an F2P-shaped node. This bundle's obligation carries NO
#   precondition hypothesis (the `∀ e` is unguarded — the behavior is total), so
#   there is nothing to ADMIT; but that does NOT make the lane vacuous. The
#   analogue on a total carrier is the obligation being SATISFIABLE at exactly an
#   F2P-shaped input, which admiss-f2p-inputs tests directly: it discharges the
#   obligation by EVALUATION (`decide` on ground literals) at both F2P shapes as
#   `have`s before closing the frozen obligation verbatim. Nor is it the trivial
#   `innerCols = innerCols`: the `have`s are closed by computing the IMPL at a
#   concrete input and comparing to that input's field, so an obligation
#   unsatisfiable at those points fails there while still elaborating abstractly.
#   (An earlier revision of this file recorded the lane as VACUOUS for the
#   "no precondition" reason; that reason was wrong and the case is now landed.)
# VACUOUS (frame-mutation): the sibling carries this MANDATORY because its inputs
#   are held at Acc(.,1/2) an impl can illegally write (rebinding inner_id to
#   node_id). This backend is referentially transparent and declares no `mut`
#   binder — every input is an immutable value with no heap footprint — so there is
#   no read-only field to overwrite and no substitute probe. Not fabricated
#   (porting map: vacuous here).
# PORTED / FOLDED (value rivals): return-self ports directly ([node_id] ->
#   [selfCol]). drop-column ports as drop-all-columns ([] on a column-like inner).
#   wrong-identity ports as a shifted-identity map (right count, wrong objects).
#   reorder-columns is ADDED (no sibling analogue): the sibling's post-image is a
#   PSeq over a one-element dichotomy, so order is never observable there, while
#   here `result = e.innerCols` is positional List equality — a defect class the
#   ported rivals all miss, since each is already caught at the set level.
#   drop-constant (base: always [node_id], wrong on the constant arm) is FOLDED:
#   on this carrier "always contribute the wrapper/self on a constant" is exactly
#   what return-self and inherited-base-rule do at innerCols = [], so it needs no
#   separate rival. The inherited (pre-patch) full rule is added as a fourth rival
#   so the free `innerContainsAggregate` binder appears in a rival body and varies
#   across the witness set. Each rival carries a machine-checked witness that
#   ELABORATES against the rival and FAILS against the frozen solution.
#
#   The five witnesses probe five DISTINCT input tuples; across them selfCol takes
#   {3,0,0,4,0}, innerContainsAggregate takes {false,true}, innerCols takes
#   {[],[⟨5⟩],[⟨1⟩],[],[⟨2⟩,⟨6⟩]}. The load-bearing binder innerCols is varied
#   across three MEANINGFUL points, not three spellings of one: the empty
#   contribution ([], where substituting the wrapper is observable and length is
#   not), a singleton (where identity is observable and order is not), and a
#   TWO-element list (where ORDER and multiplicity become observable at all —
#   reorder-columns is refutable only here, since every 0/1-element list is a
#   palindrome). The
#   aggregate flag is varied too, though (see the DEFENDED-SURFACE note) the spec
#   is genuinely independent of it: no rival can be wrong in a way distinguished
#   ONLY by that binder, because any impl branching on it yet forwarding innerCols
#   VERIFIES. That is a property of the modeled behaviour (the transparent wrapper
#   ignores aggregation), not a gap in the battery.
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job; this bundle declares no axiom
# (the delegated callee is a directive-7 free input, not an oracle), so there is
# nothing to probe and the gate ignores AXIOM_TESTS regardless.
AXIOM_TESTS = []
