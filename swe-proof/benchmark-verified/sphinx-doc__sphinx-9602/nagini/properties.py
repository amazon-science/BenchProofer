# properties.py — PBT falsification battery for sphinx-doc__sphinx-9602.
#
# NOT a Nagini module: a record of adversarially-reasoned cases the runner
# (swebench_nagini.pbt) executes and stamps with RESULT. Spec cases are full
# model.py variants built by region-surgery (edits ONLY inside a
# # impl-start / # impl-end region, with the nested invariants region included,
# so the frozen spec — axioms/pure/pre/post-conditions + signatures — is
# byte-identical and markers.same_spec holds). Each is checked by Nagini
# verify + markers.same_spec.
#
# ---------------------------------------------------------------------------
# Defended surface (from model.py + refinement.md + mapping.md + instance.json):
#
# TWO modeled functions, BOTH with a READ-ONLY input (Acc(...,1/2)):
#
# (1) render_literal_value(value: List[int], is_str: bool) -> List[int]
#       Models hunk 1 (ast.Constant branch): nodes.Text(node.value) ->
#       nodes.Text(repr(node.value)). value is the constant's text content as
#       Unicode code points.
#     * Requires(Acc(list_pred(value), 1/2))  => value is READ-ONLY.
#       Ensures(Acc(list_pred(value), 1/2)) keeps it read-only across the call.
#       => FRAME-MUTATION is MANDATORY: a rival that WRITES value to satisfy the
#          postcondition vacuously must be rejected for INSUFFICIENT PERMISSION.
#     * The is_str case carries a domain Requires (printable ASCII 0x20..0x7e,
#       no apostrophe 39, no backslash 92) — exactly the domain on which
#       repr(s) == "'" + s + "'" (G-AX / axiom_check.py validates this against
#       the real repr).
#     * LOAD-BEARING clauses:
#         Implies(is_str,     ToSeq(Result()) == quote() + ToSeq(value) + quote())
#         Implies(not is_str, ToSeq(Result()) == ToSeq(value))
#       where quote() == PSeq(39) (the apostrophe). Both oracles are GROUNDED in
#       the input (a closed-form function of `value`, fully unfolded) — there is
#       NO opaque answer-key marker to echo (see 'assessment'); building the
#       result IS doing the work.
#
# (2) resolve_subscript(kinds: List[int], is_literal: bool) -> List[int]
#       Models hunks 2+3 (the Literal wrap then the final resolution loop) on
#       the subscript BODY. kinds is the body node-kind list (1 NAME, 2 PUNCT,
#       3 XREF, 4 LIT).
#     * Requires(Acc(list_pred(kinds), 1/2))  => kinds is READ-ONLY.
#       Ensures(Acc(list_pred(kinds), 1/2)).  => FRAME-MUTATION MANDATORY here too.
#     * LOAD-BEARING clause (the whole wrap-then-resolve pipeline, grounded):
#         len(Result()) == len(kinds)
#         ToSeq(Result()) == resolve_seq(wrap_seq(ToSeq(kinds), is_literal))
#       where wrap1: NAME(1)->LIT(4) iff is_literal; resolve1: LIT(4)->NAME(1),
#       NAME(1)->XREF(3), else identity. So for is_literal=True a body NAME is
#       wrapped(4) then unwrapped(1) — it stays PLAIN TEXT, never a XREF(3); for
#       is_literal=False a body NAME stays NAME and resolves to XREF(3).
#
# The discriminating F2P behaviour
# (tests/test_domain_py.py::test_parse_annotation_Literal):
#   - B1: a STRING Literal value renders WITH surrounding quotes: 'abc' renders
#         "'abc'" (not "abc"); a numeric/bool renders bare ("True","0","1").
#   - B2: an enumerated value inside Literal[...] stays plain text (NOT a
#         pending_xref), while the head ("Literal","typing.Literal") and the
#         arguments of an ordinary parametrised annotation still become xrefs.
# model_prepatch.py reverts hunk 2 (never wraps -> enumerated NAME -> XREF) and
# fails resolve_subscript's pipeline postcondition; model_prepatch_2.py reverts
# hunk 1 (unquoted string) and fails render_literal_value's is_str clause.
# ---------------------------------------------------------------------------
from pathlib import Path

INSTANCE = "sphinx-doc__sphinx-9602"
FLOAT_ENCODING = None  # meta.json float_encoding is null


_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Region anchors — every one strictly INSIDE a # impl-start / # impl-end region
# (and inside the nested # invariants regions, which spec_view elides as part of
# the impl span, so same_spec is preserved).
# ---------------------------------------------------------------------------

# render_literal_value: the whole impl body (string branch + non-string copy
# loop). Used by the branch-reorder positive control.
_RLV_FULL = (
    "    if is_str:\n"
    "        result = [39] + value + [39]  # type: List[int]\n"
    "        return result\n"
    "    else:\n"
    "        out = []  # type: List[int]\n"
    "        i = len(value)\n"
    "        while i > 0:\n"
    "            # invariants-start\n"
    "            Invariant(Acc(list_pred(value), 1 / 2))\n"
    "            Invariant(Acc(list_pred(out)))\n"
    "            Invariant(0 <= i and i <= len(value))\n"
    "            Invariant(ToSeq(out) == ToSeq(value).drop(i))\n"
    "            # the loop consumes the caller's termination obligation with the\n"
    "            # strictly decreasing, bounded-below measure i.\n"
    "            Invariant(MustTerminate(i + 1))\n"
    "            # invariants-end\n"
    "            out = [value[i - 1]] + out\n"
    "            i = i - 1\n"
    "        return out\n"
)

# render_literal_value: the is_str branch body alone.
_RLV_STR_BRANCH = (
    "        result = [39] + value + [39]  # type: List[int]\n"
    "        return result\n"
)

# render_literal_value: the non-string copy-loop per-step (read of value[i-1]).
_RLV_LOOP_STEP = (
    "            out = [value[i - 1]] + out\n"
    "            i = i - 1\n"
)

# render_literal_value: the non-string branch return (drop the final `return out`
# off the copy loop so we can append the quotes onto it).
_RLV_NONSTR_RETURN = "        return out\n"

# resolve_subscript: the wrap-loop per-step decision.
_RS_WRAP_STEP = (
    "        if is_literal and k == 1:\n"
    "            wrapped = [4] + wrapped\n"
    "        else:\n"
    "            wrapped = [k] + wrapped\n"
)

# resolve_subscript: the wrap-loop read of kinds[i-1].
_RS_WRAP_KREAD = "        k = kinds[i - 1]\n"

# resolve_subscript: the resolve-loop per-step decision.
_RS_RESOLVE_STEP = (
    "        if w == 4:\n"
    "            out = [1] + out\n"
    "        elif w == 1:\n"
    "            out = [3] + out\n"
    "        else:\n"
    "            out = [w] + out\n"
)

# resolve_subscript: the closing assertion + return (admissibility hook).
_RS_FINAL = (
    "    Assert(ToSeq(wrapped).drop(0) == ToSeq(wrapped))\n"
    "    Assert(ToSeq(out) == resolve_seq(ToSeq(wrapped)))\n"
    "    return out\n"
)


# ===========================================================================
# SPEC_TESTS
# ===========================================================================
SPEC_TESTS = [

    # -- POSITIVE CONTROL #1 (soundness): render_literal_value branch reorder --
    # Test `not is_str` FIRST. The string branch and the non-string copy loop
    # (with all four Invariants verbatim) are kept identical — only the order of
    # the two top-level branches changes. The is_str postcondition is discharged
    # in the `else` (where is_str holds), the not-is_str clause in the `if`.
    # A correct structural variant MUST verify, else SPEC-TOO-STRONG. This is
    # also the honest cheapest positive control for the (grounded) oracle lane.
    {
        "id": "pos-control-rlv-branch-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _BASE, _RLV_FULL,
            "    if not is_str:\n"
            "        out = []  # type: List[int]\n"
            "        i = len(value)\n"
            "        while i > 0:\n"
            "            # invariants-start\n"
            "            Invariant(Acc(list_pred(value), 1 / 2))\n"
            "            Invariant(Acc(list_pred(out)))\n"
            "            Invariant(0 <= i and i <= len(value))\n"
            "            Invariant(ToSeq(out) == ToSeq(value).drop(i))\n"
            "            # the loop consumes the caller's termination obligation with the\n"
            "            # strictly decreasing, bounded-below measure i.\n"
            "            Invariant(MustTerminate(i + 1))\n"
            "            # invariants-end\n"
            "            out = [value[i - 1]] + out\n"
            "            i = i - 1\n"
            "        return out\n"
            "    else:\n"
            "        result = [39] + value + [39]  # type: List[int]\n"
            "        return result\n",
        ),
        "rationale": "reordering the two branches (not-is_str tested first) while "
                     "keeping each branch's body + the copy-loop invariants "
                     "verbatim is a correct structural variant; it must verify, "
                     "else SPEC-TOO-STRONG. Also the honest positive control for "
                     "the ungrounded-oracle lane (the oracle is grounded in "
                     "`value`; there is no wrong echo to build).",
    },

    # -- POSITIVE CONTROL #2 (soundness): resolve_subscript resolve-branch reorder
    # In the SECOND (resolve) loop, test the NAME case (w==1) BEFORE the LIT case
    # (w==4). w==1 and w==4 are disjoint, so the per-element decision is
    # unchanged; the loop invariant ToSeq(out)==resolve_seq(ToSeq(wrapped).drop(j))
    # still holds. All Invariants + framing Asserts are kept verbatim. Must
    # verify, else SPEC-TOO-STRONG.
    {
        "id": "pos-control-rs-resolve-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _BASE, _RS_RESOLVE_STEP,
            "        if w == 1:\n"
            "            out = [3] + out\n"
            "        elif w == 4:\n"
            "            out = [1] + out\n"
            "        else:\n"
            "            out = [w] + out\n",
        ),
        "rationale": "the resolve decision for disjoint w==1 / w==4 is order-"
                     "independent; reordering the two arms keeps resolve1's "
                     "per-element result and the loop invariant intact, so it must "
                     "verify, else SPEC-TOO-STRONG.",
    },

    # -- ADMISSIBILITY #1: render_literal_value pins an F2P-shaped string -------
    # On the is_str path, Assert the postcondition's own deep-model fact
    # (ToSeq(result)==quote()+ToSeq(value)+quote()) BEFORE returning the gold
    # value. The Assert must discharge from quote()==PSeq(39) and the [39]+v+[39]
    # construction for ANY admitted string (incl. the F2P 'abc' = [97,98,99]); if
    # it could not, the precondition + @Pure quote() would be unusable =>
    # PRECOND-TOO-STRONG. The returned value is gold-verbatim.
    {
        "id": "admiss-rlv-quote-fact",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _RLV_STR_BRANCH,
            "        result = [39] + value + [39]  # type: List[int]\n"
            "        Assert(ToSeq(result) == quote() + ToSeq(value) + quote())\n"
            "        return result\n",
        ),
        "rationale": "the precondition + @Pure quote() must admit a normal string "
                     "input and pin it to the quoted form; if this Assert cannot "
                     "discharge, the spec is unusable => PRECOND-TOO-STRONG.",
    },

    # -- ADMISSIBILITY #2: resolve_subscript pins the full pipeline -------------
    # Before the gold `return out`, Assert the EXACT postcondition fact
    # ToSeq(out)==resolve_seq(wrap_seq(ToSeq(kinds), is_literal)) (composing the
    # two loop facts already asserted). If the spec admits a normal node list and
    # this composed fact discharges, the precondition is usable; if not =>
    # PRECOND-TOO-STRONG. Returned value gold-verbatim.
    {
        "id": "admiss-rs-pipeline-fact",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _RS_FINAL,
            "    Assert(ToSeq(wrapped).drop(0) == ToSeq(wrapped))\n"
            "    Assert(ToSeq(out) == resolve_seq(ToSeq(wrapped)))\n"
            "    Assert(ToSeq(out) == resolve_seq(wrap_seq(ToSeq(kinds), is_literal)))\n"
            "    return out\n",
        ),
        "rationale": "the precondition must admit a normal body node list and the "
                     "composed wrap-then-resolve fact (the postcondition itself) "
                     "must discharge; else PRECOND-TOO-STRONG.",
    },

    # -- FRAME-MUTATION #1 (MANDATORY: value is Acc(list_pred(value),1/2)) -------
    # In the non-string copy loop the rival WRITES value[i-1] = value[i-1] — the
    # SAME value back, so the computed output is byte-identical to gold — but the
    # index is provably valid (loop guard i>0, invariant i<=len(value)) so the
    # ONLY obstacle is permission: value is held at 1/2, a list_pred write needs
    # full permission, so the verifier MUST reject for INSUFFICIENT PERMISSION.
    # The returned value is gold-verbatim, so the rejection is attributable to
    # the write, not a logic change. A byte-fuzzer never thinks to mutate the
    # read-only input — the project's #1 weakness class.
    {
        "id": "frame-mutation-write-value",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _RLV_LOOP_STEP,
            "            value[i - 1] = value[i - 1]\n"
            "            out = [value[i - 1]] + out\n"
            "            i = i - 1\n",
        ),
        "refinement": "hunk 1 only READS node.value (it computes repr(node.value) "
                      "and constructs a NEW nodes.Text); it never assigns into the "
                      "AST node's value. A faithful patch that mutated node.value "
                      "while unparsing would corrupt the shared ast.Constant the "
                      "rest of the autodoc pipeline reads, perturbing every other "
                      "annotation rendered from the same module — it would not "
                      "produce the stable doctree the F2P/P2P assert, so it would "
                      "NOT resolve.",
        "rationale": "value is held at Acc(list_pred(value),1/2) (Requires AND "
                     "Ensures). Writing value[i-1] needs full list_pred "
                     "permission; the permission system rejects it (insufficient "
                     "permission) even though the value is unchanged.",
    },

    # -- FRAME-MUTATION #2 (MANDATORY: kinds is Acc(list_pred(kinds),1/2)) -------
    # In the wrap loop the rival WRITES kinds[i-1] = kinds[i-1] (same value back)
    # right after reading it. Index provably valid (i>0, invariant i<=len(kinds)).
    # kinds is at 1/2 permission, so the write needs full permission and the
    # verifier MUST reject for INSUFFICIENT PERMISSION. Output unchanged from gold,
    # so the rejection is attributable to the write alone.
    {
        "id": "frame-mutation-write-kinds",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _RS_WRAP_KREAD,
            "        k = kinds[i - 1]\n"
            "        kinds[i - 1] = kinds[i - 1]\n",
        ),
        "refinement": "hunks 2+3 mutate the LOCAL `result` list of rendered nodes, "
                      "never the input node list / AST. A faithful patch that "
                      "wrote back into the source node sequence would corrupt the "
                      "shared docutils/AST structures the surrounding "
                      "_parse_annotation and the rest of the test suite read, so "
                      "the doctree the F2P/P2P assert would not be produced — it "
                      "would NOT resolve.",
        "rationale": "kinds is held at Acc(list_pred(kinds),1/2) (Requires AND "
                     "Ensures). Writing kinds[i-1] needs full list_pred "
                     "permission; the permission system rejects it (insufficient "
                     "permission) regardless that the value is unchanged.",
    },

    # -- PARTIAL-DOMAIN #1 (the prepatch B2 bug): never wrap in a Literal --------
    # The wrap step prepends `k` unconditionally (drops the `is_literal and k==1`
    # special case), so a body NAME inside a Literal subscript is NOT wrapped and
    # the resolve loop turns it into a XREF(3). Correct for is_literal=False;
    # diverges on is_literal=True with a NAME body node. This is exactly
    # model_prepatch.py / the nitpick bug. The gold wrap invariant
    # ToSeq(wrapped)==wrap_seq(ToSeq(kinds),is_literal) cannot hold (wrap_seq
    # demands LIT(4) for that node), so it is rejected.
    {
        "id": "partial-domain-never-wrap",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _RS_WRAP_STEP,
            "        wrapped = [k] + wrapped\n",
        ),
        "refinement": "this reverts hunk 2 (no `if result[0] in ('Literal', "
                      "'typing.Literal'): ... nodes.literal` wrap). An enumerated "
                      "value then hits the `elif isinstance(node, nodes.Text)` arm "
                      "and is converted to type_to_xref -> a pending_xref. The F2P "
                      "test_parse_annotation_Literal asserts 'True'/'False'/'0'/"
                      "'1'/\"'abc'\" are PLAIN strings (not pending_xref) — a "
                      "non-wrapping patch fails those assertions, so it does NOT "
                      "resolve.",
        "rationale": "violates the wrap-loop invariant ToSeq(wrapped)=="
                     "wrap_seq(ToSeq(kinds),is_literal) (hence the postcondition "
                     "pipeline) on the is_literal=True, k==NAME sub-domain: "
                     "wrap_seq sends NAME(1)->LIT(4) there, but this impl keeps it "
                     "NAME(1).",
    },

    # -- PARTIAL-DOMAIN #2: a Literal value resolves to a XREF, not plain text ---
    # The resolve step unwraps LIT(4) to XREF(3) instead of NAME(1) (plain text).
    # So an enumerated value (wrapped to LIT) becomes a cross-reference — the
    # SAME observable bug as never-wrapping, but introduced at the resolve stage.
    # Correct on PUNCT/XREF/NAME nodes; diverges on LIT. resolve_seq demands
    # LIT->NAME(1), so the resolve invariant fails -> reject.
    {
        "id": "partial-domain-lit-to-xref",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _RS_RESOLVE_STEP,
            "        if w == 4:\n"
            "            out = [3] + out\n"
            "        elif w == 1:\n"
            "            out = [3] + out\n"
            "        else:\n"
            "            out = [w] + out\n",
        ),
        "refinement": "this corresponds to a hunk-3 that resolved the wrapped "
                      "nodes.literal to type_to_xref instead of unwrapping it to "
                      "its plain-text child (node[0]). The F2P asserts enumerated "
                      "values are plain strings, not pending_xref; resolving the "
                      "wrapped node to a xref fails those assertions exactly, so "
                      "it does NOT resolve.",
        "rationale": "violates the resolve-loop invariant ToSeq(out)=="
                     "resolve_seq(ToSeq(wrapped).drop(j)) on the LIT sub-domain: "
                     "resolve_seq (via resolve1) sends LIT(4)->NAME(1), but this "
                     "impl sends it to XREF(3).",
    },

    # -- PARTIAL-DOMAIN #3: a NAME never cross-references (ordinary subscript bug)
    # The resolve step keeps NAME(1) as NAME(1) instead of XREF(3). An ordinary
    # (non-Literal) parametrised annotation argument (a NAME body node that was
    # NOT wrapped) then stays plain text rather than becoming a cross-reference —
    # breaking the still-required behaviour that ordinary type args ARE xrefs.
    # Correct on LIT/PUNCT/XREF; diverges on a non-wrapped NAME.
    {
        "id": "partial-domain-name-not-xref",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _RS_RESOLVE_STEP,
            "        if w == 4:\n"
            "            out = [1] + out\n"
            "        elif w == 1:\n"
            "            out = [1] + out\n"
            "        else:\n"
            "            out = [w] + out\n",
        ),
        "refinement": "this drops the `type_to_xref` call for a non-blank Text "
                      "node (hunk-3's surviving elif). An ordinary parametrised "
                      "annotation argument (e.g. the `int` in `List[int]`) would "
                      "then render as plain text instead of a pending_xref, "
                      "breaking the P2P annotation tests that assert ordinary type "
                      "args are cross-references — it does NOT resolve.",
        "rationale": "violates the resolve-loop invariant on the NAME(1) "
                     "sub-domain: resolve_seq (via resolve1) sends NAME(1)->"
                     "XREF(3) (a non-wrapped body NAME becomes a cross-reference), "
                     "but this impl keeps it NAME(1).",
    },

    # -- PARTIAL-DOMAIN #4: render_literal_value drops the trailing quote --------
    # The is_str branch returns [39] + value (leading quote only). Correct on
    # non-strings; diverges on every string. Violates the load-bearing is_str
    # clause ToSeq(Result())==quote()+ToSeq(value)+quote() (the closing quote is
    # missing).
    {
        "id": "partial-domain-rlv-one-sided-quote",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _RLV_STR_BRANCH,
            "        result = [39] + value  # type: List[int]\n"
            "        return result\n",
        ),
        "refinement": "repr('abc') is \"'abc'\" with BOTH apostrophes; a patch that "
                      "produced only a leading quote (\"'abc\") fails the F2P "
                      "assertion that the rendered text equals \"'abc'\" exactly — "
                      "it does NOT resolve.",
        "rationale": "violates Ensures(Implies(is_str, ToSeq(Result())==quote()+"
                     "ToSeq(value)+quote())): the trailing quote() is absent.",
    },

    # -- PARTIAL-DOMAIN #5: render_literal_value quotes a NON-string value -------
    # The non-string branch wraps the value in quotes too ([39]+...+[39]). This
    # is the canonical over-application of repr's quoting: it would render a bool
    # or int as a quoted string. Correct on strings; diverges on every
    # non-string. Violates the not-is_str clause ToSeq(Result())==ToSeq(value).
    {
        "id": "partial-domain-rlv-quote-nonstring",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _RLV_NONSTR_RETURN,
            "        quoted = [39] + out + [39]  # type: List[int]\n"
            "        return quoted\n",
        ),
        "refinement": "repr(True) is 'True' and repr(0) is '0' — NO surrounding "
                      "quotes for bool/int. A patch that quoted non-string "
                      "constants would render them \"'True'\"/\"'0'\", failing the "
                      "F2P assertions that the bool/int Literal members are the "
                      "bare strings 'True','False','0','1' — it does NOT resolve.",
        "rationale": "violates Ensures(Implies(not is_str, ToSeq(Result())=="
                     "ToSeq(value))): the result carries extra apostrophes around "
                     "the value.",
    },

    # -- UNIQUENESS (cheap supporting): wrong quote glyph (double-quote 34) -------
    # The is_str branch frames value with the double-quote code point 34 instead
    # of the apostrophe 39. A plausible "use quotes" slip with the wrong glyph.
    # Carries a real refinement.
    {
        "id": "uniqueness-rlv-wrong-quote-glyph",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _RLV_STR_BRANCH,
            "        result = [34] + value + [34]  # type: List[int]\n"
            "        return result\n",
        ),
        "refinement": "repr of a short printable-ASCII string uses the SINGLE "
                      "quote (apostrophe, U+0027): repr('abc') == \"'abc'\", not "
                      "'\"abc\"'. A patch framing the value in double quotes fails "
                      "the F2P assertion of the exact string \"'abc'\" — it does "
                      "NOT resolve.",
        "rationale": "violates Ensures(Implies(is_str, ToSeq(Result())==quote()+"
                     "ToSeq(value)+quote())): quote()==PSeq(39) (apostrophe), so a "
                     "PSeq(34) (double-quote) frame is not equal.",
    },
]


# ===========================================================================
# AXIOM_TESTS — none (no @ContractOnly axiom in this bundle).
# ===========================================================================
# meta.json axioms == [] : both changed operations are modeled DEEPLY (the
# quoting in render_literal_value; the wrap_seq/resolve_seq folds + the two
# verified loops in resolve_subscript), with NO consumed @ContractOnly axiom.
# The only callees (the built-in repr and the unchanged type_to_xref) appear as
# A-references, already validated == the real callees out-of-band by
# axiom_check.py (G-AX: render_literal_value == real repr on 25 boundary +
# 25000 fuzz values drawn from EXACTLY the spec Requires domain, with a negative
# control just outside it; wrap1/resolve1 == the gold loop bodies exhaustively +
# 20000 fuzz node lists; gold end-to-end node-kinds match the two F2P
# annotations). There is no @ContractOnly obligation for the PBT axiom lane to
# re-discharge, so AXIOM_TESTS is empty.
AXIOM_TESTS = []
