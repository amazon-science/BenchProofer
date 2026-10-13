# properties.py — PBT falsification battery for sphinx-doc__sphinx-9367.
#
# NOT a Nagini module: a record of adversarially-reasoned cases the runner
# (swebench_nagini.pbt) executes and stamps with RESULT. Spec cases are full
# model.py variants built by region-surgery (edits ONLY inside the
# # impl-start / # impl-end region, so the frozen spec — axioms/pure/pre/post —
# is byte-identical and same_spec holds). Each is checked by Nagini verify +
# markers.same_spec.
#
# Defended surface (from model.py + refinement.md + instance.json F2P):
#   render_tuple(elts: List[PSeq[int]]) -> PSeq[int]
#     renders a parenthesized tuple from the textual renderings of its members.
#     * elts is READ-ONLY: Requires AND Ensures Acc(list_pred(elts), 1/2).
#       => FRAME-MUTATION is mandatory (a rival that writes elts must be
#          rejected for insufficient permission).
#     * the postcondition pins the output EXACTLY to a deep model:
#         Ensures(Result() == render_seq(ToSeq(elts)))
#       where render_seq is a @Pure CLOSED-FORM that fully resolves the three
#       surface forms (all of empty/single/multi, fully unfolded over the
#       input elts):
#         n == 0 -> PSeq(40,41)               i.e. "()"
#         n == 1 -> PSeq(40)+es[0]+PSeq(44,41) i.e. "(e0,)"  <- THE CHANGE
#         n >= 2 -> PSeq(40)+join_sep(es)+PSeq(41) i.e. "(e0, e1, ...)"
#     * render_seq is GROUNDED in the input (a function of elts, fully unfolded
#       via render_seq/join_sep/sep/empty_seq) — it is NOT an opaque answer-key
#       marker. `return render_seq(ToSeq(elts))` is therefore a LEGITIMATE
#       correct impl, not a "wrong echo": there is no ungrounded-oracle echo to
#       build (see 'assessment'). Accordingly the ungrounded-oracle lane is
#       covered by an honest cheapest-impl positive control (expect=verify).
#     * there is no raise / side-effect channel invisible to the value
#       abstraction: render_tuple has a single value output and no exceptional
#       path (no exsures). The one control-flow-effect channel Nagini's default
#       partial-correctness semantics leaves open is DIVERGENCE (never reaching
#       the return, so every Ensures holds vacuously); the spec closes it with
#       Requires(MustTerminate(2)) (consumed in the multi-branch loop by
#       Invariant(MustTerminate(i))), and the w-diverge case below pins the
#       rejection.
#
# The discriminating F2P behaviour
# (tests/test_pycode_ast.py::test_unparse[(1,)-(1,)]): a ONE-member tuple must
# render with the trailing comma — "(1,)", not "(1)". This lives in the n==1
# branch (PSeq(40)+es[0]+PSeq(44,41)) of impl and the render_seq len==1 clause.
# The pre-patch code rendered every non-empty sequence with the join branch, so
# a one-member sequence collapsed to "(e0)" (model_prepatch.py reproduces this
# and fails the postcondition on n==1). The empty ("()") and multi ("(1, 2)",
# "(1, 2, 3)") forms are exercised by the P2P cases.
from pathlib import Path

INSTANCE = "sphinx-doc__sphinx-9367"
FLOAT_ENCODING = None  # meta.json float_encoding is null


_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Region anchors (all strictly INSIDE the # impl-start / # impl-end region).
# ---------------------------------------------------------------------------

# The single-member (n==1) branch body — the load-bearing trailing-comma form.
_SINGLE_BRANCH = "        return PSeq(40) + es[0] + PSeq(44, 41)\n"

# The empty (n==0) branch body.
_EMPTY_BRANCH = "        return PSeq(40, 41)\n"

# The per-step join update inside the backward multi-loop.
_JOIN_STEP = (
    "            if i == n:\n"
    "                joined = e\n"
    "            else:\n"
    "                joined = e + sep() + joined\n"
)

# The whole impl body (after the # impl-start marker) — used by the
# cheapest-honest positive control (direct deep-model materialization) and by
# the divergence rival (endless loop before the return).
_FULL_IMPL = (
    "    es = ToSeq(elts)  # type: PSeq[PSeq[int]]\n"
    "    n = len(elts)\n"
    "    if n == 0:\n"
    "        return PSeq(40, 41)\n"
    "    elif n == 1:\n"
    "        return PSeq(40) + es[0] + PSeq(44, 41)\n"
    "    else:\n"
    "        joined = empty_seq()  # type: PSeq[int]\n"
    "        i = n\n"
    "        while i > 0:\n"
    "            # invariants-start\n"
    "            Invariant(Acc(list_pred(elts), 1 / 2))\n"
    "            Invariant(es == ToSeq(elts))\n"
    "            Invariant(n == len(elts))\n"
    "            Invariant(n >= 2)\n"
    "            Invariant(0 <= i and i <= n)\n"
    "            Invariant(joined == join_sep(es.drop(i)))\n"
    "            # The loop consumes the termination obligation: i is the strictly\n"
    "            # decreasing, bounded-below measure.\n"
    "            Invariant(MustTerminate(i))\n"
    "            # invariants-end\n"
    "            e = es[i - 1]\n"
    "            Assert(es.drop(i - 1)[0] == e)\n"
    "            Assert(es.drop(i - 1).drop(1) == es.drop(i))\n"
    "            if i == n:\n"
    "                joined = e\n"
    "            else:\n"
    "                joined = e + sep() + joined\n"
    "            i = i - 1\n"
    "        return PSeq(40) + joined + PSeq(41)\n"
)


# ===========================================================================
# SPEC_TESTS
# ===========================================================================
SPEC_TESTS = [

    # --- POSITIVE CONTROL #1 (soundness): cheapest-honest direct materialize -
    # The whole impl is replaced by `return render_seq(es)` (es == ToSeq(elts)).
    # This is the honest cheapest impl: it does the WORK by invoking the deep
    # model directly (no loop). Because render_seq is GROUNDED in the input,
    # there is no "wrong echo" to build — this impl is genuinely correct and
    # MUST verify. If it could not, the spec would be unsatisfiable / too strong.
    {
        "id": "pos-control-direct-materialize",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _BASE, _FULL_IMPL,
            "    es = ToSeq(elts)  # type: PSeq[PSeq[int]]\n"
            "    return render_seq(es)\n",
        ),
        "rationale": "render_seq(ToSeq(elts)) is the grounded deep model the "
                     "postcondition pins to; a faithful impl that materializes "
                     "it directly must verify (Result()==render_seq(ToSeq(elts)) "
                     "discharges by es==ToSeq(elts)), else SPEC-TOO-STRONG. Also "
                     "the honest positive control for the ungrounded-oracle lane "
                     "(no wrong echo exists; the oracle is a function of elts).",
    },

    # --- POSITIVE CONTROL #2 (soundness): branch-reorder, gold loop verbatim --
    # Structurally different: the n==0 / n==1 branch ORDER is swapped (test
    # n==1 first via the elif chain rewritten so the empty case is the elif).
    # The else multi-branch (backward loop, all six Invariants, both framing
    # Asserts, the join step) is kept BYTE-IDENTICAL, so every gold proof
    # obligation it discharges is untouched — only the executable order of the
    # two short-circuit branches changes. Must verify; else SPEC-TOO-STRONG.
    {
        "id": "pos-control-branch-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _BASE,
            "    if n == 0:\n"
            "        return PSeq(40, 41)\n"
            "    elif n == 1:\n"
            "        return PSeq(40) + es[0] + PSeq(44, 41)\n"
            "    else:\n",
            "    if n == 1:\n"
            "        return PSeq(40) + es[0] + PSeq(44, 41)\n"
            "    elif n == 0:\n"
            "        return PSeq(40, 41)\n"
            "    else:\n",
        ),
        "rationale": "reordering the two short-circuit branches (n==1 tested "
                     "before n==0) while keeping the multi-loop+invariants+"
                     "asserts verbatim is a correct structural variant; it must "
                     "verify, else SPEC-TOO-STRONG.",
    },

    # --- ADMISSIBILITY ----------------------------------------------------
    # On the single-member path, Assert the postcondition's deep-model fact for
    # n==1: render_seq for a one-element sequence equals (e0,). This must
    # discharge from the spec for an F2P-shaped input ("(1,)"); if the
    # precondition / @Pure definitions were contradictory or unusable this would
    # fail => PRECOND-TOO-STRONG. Only an extra Assert is added inside impl; the
    # returned value is gold-verbatim.
    {
        "id": "admiss-single-member-form",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE,
            "    elif n == 1:\n"
            "        return PSeq(40) + es[0] + PSeq(44, 41)\n",
            "    elif n == 1:\n"
            "        Assert(render_seq(es) == PSeq(40) + es[0] + PSeq(44, 41))\n"
            "        return PSeq(40) + es[0] + PSeq(44, 41)\n",
        ),
        "rationale": "the precondition + @Pure render_seq must admit and pin a "
                     "normal one-member input to the trailing-comma form; if "
                     "this Assert cannot discharge the spec is contradictory/"
                     "unusable => PRECOND-TOO-STRONG.",
    },

    # --- FRAME-MUTATION (MANDATORY: elts is Acc(list_pred(elts),1/2) read-only)-
    # The rival WRITES to the read-only member-rendering list (elts[0] = es[0])
    # on the single-member path before returning the gold value. The write sets
    # the SAME value back, so functionally it still computes the gold output —
    # but the half-permission Requires/Ensures forbids ANY write to list_pred,
    # so the verifier must reject for INSUFFICIENT PERMISSION. The returned
    # expression is gold-verbatim so the rejection is attributable to the write,
    # not a logic change. A byte-fuzzer never thinks to mutate the input — this
    # is the project's #1 weakness class.
    {
        "id": "frame-mutation-write-elts",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE,
            "    elif n == 1:\n"
            "        return PSeq(40) + es[0] + PSeq(44, 41)\n",
            "    elif n == 1:\n"
            "        elts[0] = elts[0]\n"
            "        return PSeq(40) + es[0] + PSeq(44, 41)\n",
        ),
        "refinement": "visit_Tuple only READS node.elts (renders each via "
                      "self.visit and joins the strings); it never assigns into "
                      "node.elts. A faithful patch that mutated node.elts while "
                      "unparsing would corrupt the shared AST that the rest of "
                      "the unparse / autodoc pipeline reads, changing renderings "
                      "of sibling nodes and other test sources — it would not "
                      "produce the stable strings the F2P/P2P test_unparse cases "
                      "assert, so it would NOT resolve.",
        "rationale": "elts is held at Acc(list_pred(elts),1/2) (Requires AND "
                     "Ensures). Writing elts[0] needs full list_pred permission; "
                     "the permission system rejects it (insufficient permission),"
                     " regardless that the value is unchanged.",
    },

    # --- PARTIAL-DOMAIN #1: single-member drops the trailing comma --------
    # The n==1 branch returns "(e0)" (PSeq(40)+es[0]+PSeq(41)) instead of
    # "(e0,)". This is EXACTLY the pre-patch bug and the F2P failure: a
    # one-member tuple renders without the comma. Correct on empty and multi,
    # diverges only on the n==1 sub-domain. Violates the load-bearing clause
    # Result()==render_seq(ToSeq(elts)) at the render_seq len==1 branch.
    {
        "id": "partial-domain-single-no-comma",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _SINGLE_BRANCH,
            "        return PSeq(40) + es[0] + PSeq(41)\n",
        ),
        "refinement": "this is the gold pre-patch behaviour verbatim "
                      "(`return \"(\" + \", \".join(...) + \")\"` collapses a "
                      "one-member tuple to \"(1)\"). The F2P "
                      "test_unparse[(1,)-(1,)] asserts \"(1,)\"; rendering \"(1)\" "
                      "fails that assertion exactly — it does NOT resolve.",
        "rationale": "violates Ensures(Result()==render_seq(ToSeq(elts))) on the "
                     "n==1 sub-domain: render_seq len==1 demands "
                     "PSeq(40)+s[0]+PSeq(44,41) (with the comma).",
    },

    # --- PARTIAL-DOMAIN #2: empty tuple renders as "(,)" not "()" ----------
    # The n==0 branch returns PSeq(40,44,41) i.e. "(,)" instead of "()".
    # Correct on single and multi, diverges only on the empty sub-domain.
    # Violates render_seq len==0 (PSeq(40,41)). First-fails on the P2P "()"
    # case.
    {
        "id": "partial-domain-empty-stray-comma",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _EMPTY_BRANCH,
            "        return PSeq(40, 44, 41)\n",
        ),
        "refinement": "a patch that emitted \"(,)\" for the empty tuple (e.g. "
                      "an off-by-one that always appended a trailing comma) "
                      "would fail the P2P test_unparse[()-()] which asserts "
                      "\"()\" — it does NOT resolve.",
        "rationale": "violates Ensures(Result()==render_seq(ToSeq(elts))) on the "
                     "n==0 sub-domain: render_seq len==0 demands PSeq(40,41) "
                     "(\"()\"), not PSeq(40,44,41) (\"(,)\").",
    },

    # --- PARTIAL-DOMAIN #3: multi-branch drops the separator before the last
    #     adjacency (concatenates first two members with no ", ") ------------
    # On the LAST loop step (i==2, i.e. prepending the first member) the rival
    # concatenates with NO separator (joined = e + joined) instead of
    # e + sep() + joined, so "(1, 2, 3)" renders as "(12, 3)". The loop
    # invariant `joined == join_sep(es.drop(i))` then cannot hold on that step,
    # so the rejection comes from the multi-branch failing to establish the
    # postcondition join. Correct on empty/single; diverges on n>=2.
    {
        "id": "partial-domain-multi-missing-sep",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _JOIN_STEP,
            "            if i == n:\n"
            "                joined = e\n"
            "            elif i == 1:\n"
            "                joined = e + joined\n"
            "            else:\n"
            "                joined = e + sep() + joined\n",
        ),
        "refinement": "a join that omitted \", \" before the first member "
                      "(`\"\".join` rather than `\", \".join`, or a slice bug) "
                      "would render \"(1, 2, 3)\" as \"(12, 3)\"; the P2P "
                      "test_unparse[(1, 2, 3)-(1, 2, 3)] and [(1, 2)-(1, 2)] "
                      "assert the fully-separated form — it does NOT resolve.",
        "rationale": "violates Ensures(Result()==render_seq(ToSeq(elts))) on the "
                     "n>=2 sub-domain: the dropped sep makes "
                     "joined != join_sep(es) so PSeq(40)+joined+PSeq(41) != "
                     "render_seq(es) (the invariant joined==join_sep(es.drop(i)) "
                     "fails to re-establish on the last step).",
    },

    # --- UNIQUENESS (cheap supporting): single-member uses ", " not "," ----
    # The n==1 branch returns "(e0, )" (PSeq(40)+es[0]+PSeq(44,32,41)) — a
    # plausible "use the member separator" slip. The trailing form must be a
    # bare comma then ")", not "comma space )". Cheap near-miss but with a real
    # refinement.
    {
        "id": "uniqueness-single-comma-space",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _SINGLE_BRANCH,
            "        return PSeq(40) + es[0] + PSeq(44, 32, 41)\n",
        ),
        "refinement": "a patch like `\"(%s, )\" % self.visit(node.elts[0])` "
                      "would render \"(1, )\"; the F2P test_unparse[(1,)-(1,)] "
                      "asserts the exact string \"(1,)\" (no space) — it does "
                      "NOT resolve.",
        "rationale": "violates Ensures(Result()==render_seq(ToSeq(elts))) on "
                     "n==1: render_seq len==1 demands PSeq(44,41) (\",)\") after "
                     "the member, not PSeq(44,32,41) (\", )\").",
    },

    # --- CONTROL-FLOW-EFFECT (vacuity): DIVERGE instead of returning --------
    # The rival replaces the whole impl with an endless loop before the return:
    # no normal exit is ever reached, so every Ensures (including the exact
    # output pin) holds vacuously under partial-correctness semantics. This was
    # the audit P1 witness (atk_5-class vacuity hole): under the pre-fix
    # contract (no MustTerminate) it VERIFIED while sharing the spec.
    # rejection source: the MustTerminate(2) obligation in the pre-conditions —
    # the loop carries no termination measure, so Nagini reports an obligation
    # leak instead of accepting the vacuous proof.
    {
        "id": "w-diverge",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _FULL_IMPL,
            "    while True:\n"
            "        pass\n"
            "    return PSeq(40, 41)\n",
        ),
        "refinement": "a real patch whose visit_Tuple spins forever (e.g. an "
                      "accidental infinite loop while assembling the members) "
                      "never returns; unparsing any tuple default hangs, the "
                      "F2P test_unparse[(1,)-(1,)] and every tuple P2P case "
                      "time out — it does NOT resolve.",
        "rationale": "rejected by the MustTerminate(2) termination obligation "
                     "in the pre-conditions: the loop takes no termination "
                     "measure, so Nagini reports an obligation leak. Without "
                     "MustTerminate this rival VERIFIED (the pre-fix P1 hole): "
                     "with no reachable normal exit every Ensures holds "
                     "vacuously. Vacuity / control-flow-effect case.",
    },
]


# ===========================================================================
# AXIOM_TESTS — none.
# ===========================================================================
# meta.json axioms == [] and deep_model_references == []: the only callee
# (self.visit) is UNCHANGED by the patch and abstracted as the INPUT carrier
# elts[k], not modeled deeply nor axiomatized. The pure functions
# render_seq/join_sep/sep/empty_seq are closed-form spec definitions of the
# assembly under change, not contracts about an external callee. There is
# therefore nothing to validate against a real callee in Docker (G-AX is
# vacuous in meta.json).
AXIOM_TESTS = []
