# properties.py — PBT falsification battery for sympy__sympy-18189.
#
# NOT a Nagini module; a manifest the runner (swebench_nagini.pbt) parses. Each
# SPEC_TESTS case is a full model.py variant built by REGION SURGERY: we _swap
# the SINGLE `# impl-start` .. `# impl-end` block of reorder_solution_family for
# a new body and leave the frozen spec (axioms / pure / pre / post-conditions /
# signatures) byte-identical. spec_view elides the entire impl region, so
# same_spec is GUARANTEED for every case regardless of impl shape.
#
# ---------------------------------------------------------------------------
# Defended surface (read from model.py / refinement.md / mapping.md / meta.json)
# ---------------------------------------------------------------------------
# reorder_solution_family(expand: bool) -> PSeq[int] models the gold diophantine
# `if syms != var:` re-ordering branch: when the caller's symbol ordering differs
# from the canonical ordering, re-derive the solution family under the caller's
# `permute` option and re-arrange every solution tuple's components into the
# caller's ordering. The single-token gold change is `permute=permute` replacing
# the dropped default on the recursive call (sympy/solvers/diophantine.py:185).
#
# Under the §2 bijection:
#   * `expand: bool`            <-> the `permute` keyword of diophantine
#   * `solve_family(expand)`    <-> diophantine(eq, param, permute=permute) — the
#       unchanged recursive solver, A-consumed axiom. KEYED on the option;
#       solve_family(True) and solve_family(False) are deliberately NOT asserted
#       equal (the option genuinely changes which family is enumerated). This is
#       the WEAKEST contract: the proof consumes only the ABSENCE of a
#       True==False equality.
#   * `relabel(token)`          <-> the per-tuple component re-arrangement
#       tuple([t[dict_sym_index[i]] for i in var]) — A-consumed axiom, an
#       injective coordinate permutation (bijection on solution identities).
#   * `relabel_family(s)`       <-> the set comprehension applying relabel to each
#       canonical solution; a @Pure front-recursive fold with
#       Ensures(len(Result()) == len(s)).
#
# LOAD-BEARING postcondition clauses (the things an impl must satisfy):
#   (P1) Result() == relabel_family(solve_family(expand))     [master pin]
#   (P2) len(Result()) == len(solve_family(expand))           [cardinality;
#                                                              follows from P1 +
#                                                              relabel_family len]
#
# ORACLE GROUNDING: the postcondition pins Result() to
# relabel_family(solve_family(expand)) — a function of the INPUT `expand`, NOT an
# opaque answer-key. The cheapest correct impl is literally
# `return relabel_family(solve_family(expand))`, which performs the real work
# (re-derive under the caller's option, then relabel). There is therefore NO
# "wrong ungrounded-oracle echo" to build: echoing the grounded oracle is the
# correct answer. (Directive 2.) We stand a grounded-oracle honest cheapest-impl
# positive control in its place, plus a structurally-different correct dispatch.
#
# READ-ONLY INPUT / FRAME-MUTATION: the ONLY input is `expand: bool`, a value
# type. Bools carry NO heap permission in Nagini (no Acc(...,1/2), no predicate),
# so there is NOTHING to overwrite — there is no read-only heap reference and no
# frame-mutation attack to mount. has_readonly_input is FALSE and the
# frame-mutation lane is N/A for this instance (justified in 'assessment').
#
# The DISCRIMINATING F2P behaviour (test_diophantine, the issue's
# y**4 + x**4 - 2**4 - 3**4 in a non-canonical symbol ordering): with permute=True
# the canonical-ordering recursive call returns the full 8-element sign/order
# family {(-3,-2),(-3,2),(-2,-3),(-2,3),(2,-3),(2,3),(3,-2),(3,2)}; with the
# dropped default (permute=False) it returns only {(2,3)}. The pre-patch
# (model_prepatch.py: canonical = solve_family(False)) re-derives under the
# default option and so the re-arranged answer COLLAPSES to the single base
# solution whenever the caller asked for the full family — the F2P mismatch. Any
# rival that re-derives under a CONSTANT option (not the caller's `expand`)
# reproduces this exact bug on the sub-domain where the constant disagrees with
# `expand`, and its faithful real patch would NOT resolve.
from pathlib import Path

INSTANCE = "sympy__sympy-18189"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# The single whole-impl anchor: the entire `# impl-start` .. `# impl-end` block
# of reorder_solution_family (verified verbatim from model.py). Each variant
# re-emits `# impl-start` first and `# impl-end` last so the region boundary is
# preserved exactly — only the body between them changes, and spec_view elides
# all of it (same_spec guaranteed).
# ---------------------------------------------------------------------------
_S = _BASE.index("# impl-start")
_E = _BASE.index("# impl-end") + len("# impl-end")
_IMPL_BLOCK = _BASE[_S:_E]
assert _BASE.count(_IMPL_BLOCK) == 1


def _impl(body_lines: str) -> str:
    """Replace reorder_solution_family's whole impl block with a new body.
    `body_lines` is the source BETWEEN the markers (no markers); we wrap it back
    in the exact `# impl-start` / `# impl-end` markers so the region is intact.
    Indentation is 4 spaces (function body level)."""
    new_block = "# impl-start\n" + body_lines.rstrip("\n") + "\n    # impl-end"
    return _swap(_BASE, _IMPL_BLOCK, new_block)


SPEC_TESTS = [

    # ===================================================================
    # SOUNDNESS — positive controls (must VERIFY; else SPEC-TOO-STRONG)
    # ===================================================================

    # POS-CONTROL 1 (grounded-oracle honest cheapest impl). Because the
    # postcondition oracle relabel_family(solve_family(expand)) is GROUNDED in the
    # input `expand` (not an opaque answer-key), the cheapest correct impl is
    # literally `return relabel_family(solve_family(expand))` — which performs the
    # real work (re-derive under the caller's option, then relabel). This STANDS
    # IN PLACE of an ungrounded-oracle echo attack (there is no wrong echo to
    # build). P1 holds definitionally; it MUST verify, else SPEC-TOO-STRONG.
    {
        "id": "pos-control-grounded-oracle-cheapest",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(
            "    # Cheapest correct impl: return the grounded relabelled family\n"
            "    # directly. relabel_family(solve_family(expand)) re-derives under\n"
            "    # the caller's option and relabels — the real work, not a cheat.\n"
            "    # P1 holds definitionally.\n"
            "    return relabel_family(solve_family(expand))\n"
        ),
        "rationale": "grounded-oracle honest positive control: the postcondition "
                     "oracle relabel_family(solve_family(expand)) is a function of "
                     "the input `expand` (no answer-key), so the cheapest correct "
                     "impl returns it directly and MUST verify (P1 is a "
                     "definitional equality). No wrong echo exists. Else "
                     "SPEC-TOO-STRONG.",
    },

    # POS-CONTROL 2 (structurally-different correct dispatch). Instead of the
    # gold's single straight-line `canonical = solve_family(expand)`, this
    # branches on the bool and calls solve_family with the CONCRETE option in each
    # arm. On the True branch Nagini knows expand==True so solve_family(True) ==
    # solve_family(expand); on the False branch solve_family(False) ==
    # solve_family(expand). Same value on every input, different control shape, NO
    # loop / NO fold-direction flip / NO framing assert to drop (relabel_family is
    # applied whole, so no induction lemma is needed). Must verify; else
    # SPEC-TOO-STRONG.
    {
        "id": "pos-control-bool-dispatch",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(
            "    # Dispatch on the concrete option (different control shape, same\n"
            "    # value): each branch passes the option Nagini knows it is in.\n"
            "    if expand:\n"
            "        canonical = solve_family(True)  # type: PSeq[int]\n"
            "    else:\n"
            "        canonical = solve_family(False)\n"
            "    result = relabel_family(canonical)  # type: PSeq[int]\n"
            "    return result\n"
        ),
        "rationale": "a correct impl with DIFFERENT control flow (bool dispatch "
                     "calling solve_family with the concrete option in each arm vs "
                     "gold's single straight-line call) must verify: on the True "
                     "branch expand==True so solve_family(True)==solve_family("
                     "expand), likewise False. relabel_family is applied whole (no "
                     "fold-direction flip, no induction lemma, no framing assert "
                     "to drop). Else SPEC-TOO-STRONG.",
    },

    # ===================================================================
    # ADMISSIBILITY — the precondition admits a normal input (must VERIFY;
    # else PRECOND-TOO-STRONG)
    # ===================================================================

    # ADMISS: a self-call caller invokes reorder_solution_family on BOTH F2P-shaped
    # in-domain inputs (expand=True — the issue's full-family request — and
    # expand=False — the base case). The precondition is empty (trivially
    # establishable), so both calls must be admissible; the Assert pins each
    # returned family to the grounded oracle for its option. If the Requires could
    # not be established for these normal inputs the call sites would fail =>
    # PRECOND-TOO-STRONG. The caller runs BEFORE the body's own return so it is
    # verified, then the modeled body returns normally.
    {
        "id": "admiss-self-call-both-options",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl(
            "    # Admissibility self-calls: both F2P-shaped in-domain options.\n"
            "    out_true = reorder_solution_family(True)  # type: PSeq[int]\n"
            "    Assert(out_true == relabel_family(solve_family(True)))\n"
            "    out_false = reorder_solution_family(False)  # type: PSeq[int]\n"
            "    Assert(out_false == relabel_family(solve_family(False)))\n"
            "    # Then the gold body proper:\n"
            "    canonical = solve_family(expand)  # type: PSeq[int]\n"
            "    result = relabel_family(canonical)  # type: PSeq[int]\n"
            "    return result\n"
        ),
        "rationale": "the (empty) precondition must admit a normal F2P-shaped "
                     "input for BOTH options (expand=True, the issue's full-family "
                     "request, and expand=False). The self-calls establish the "
                     "Requires and each Assert pins the returned family to its "
                     "grounded oracle relabel_family(solve_family(<opt>)); else "
                     "PRECOND-TOO-STRONG.",
    },

    # ===================================================================
    # UNIQUENESS — partial-domain wrong impls (must REJECT; else SPEC-TOO-WEAK)
    # ===================================================================

    # ATTACK 1 (PARTIAL-DOMAIN — the bug-delta / prepatch, CONSTANT False). Re-derive
    # the canonical family under a fixed FALSE option (exactly model_prepatch.py:
    # `canonical = solve_family(False)`), then relabel. CORRECT only when the
    # caller asked for expand==False; WRONG whenever expand==True. Must reject:
    # the axiom does NOT grant solve_family(False) == solve_family(True), so the
    # verifier cannot prove P1 (Result() == relabel_family(solve_family(expand)))
    # for symbolic/True expand.
    {
        "id": "weak-prepatch-const-false",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    # PRE-PATCH body: re-derive under the DROPPED default option\n"
            "    # (constant False), ignoring the caller's `expand`.\n"
            "    canonical = solve_family(False)  # type: PSeq[int]\n"
            "    result = relabel_family(canonical)  # type: PSeq[int]\n"
            "    return result\n"
        ),
        "refinement": "this is the EXACT pre-patch re-ordering branch — the "
                      "recursive call diophantine(eq, param) drops the caller's "
                      "permute option, so the re-derivation runs with permute=False "
                      "(the default). For the F2P equation y**4 + x**4 - 2**4 - "
                      "3**4 in a non-canonical symbol ordering with permute=True, "
                      "the canonical recursive call then returns only the base "
                      "family {(2,3)} instead of the full 8-element sign/order "
                      "family, so the re-arranged answer COLLAPSES to a single "
                      "solution. test_diophantine demands the full permuted family, "
                      "so it MISMATCHES. The faithful real patch (= prepatch) does "
                      "NOT resolve the F2P. (This is model_prepatch.py / G-DIFF.)",
        "rationale": "rejected by POSTCONDITION P1: the impl proves "
                     "Result() == relabel_family(solve_family(False)) but the "
                     "Ensures demands relabel_family(solve_family(expand)); the "
                     "solve_family axiom deliberately does NOT assert "
                     "solve_family(False) == solve_family(True), so for "
                     "expand==True the equality is unprovable. Correct on the "
                     "expand==False sub-domain only.",
    },

    # ATTACK 2 (PARTIAL-DOMAIN — mirror, CONSTANT True). The symmetric error:
    # re-derive under a fixed TRUE option, ignoring the caller's `expand`. CORRECT
    # only when expand==True; WRONG whenever expand==False (over-enumerates the
    # full family when the caller asked for the base one). Must reject for the
    # same reason: no solve_family(True) == solve_family(False) equality is
    # granted, so P1 is unprovable for symbolic/False expand. (Guards against a
    # spec that pins only the True branch — the F2P direction — and leaves the
    # base direction free.)
    {
        "id": "weak-const-true",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    # WRONG: always re-derive the FULL family, ignoring `expand`.\n"
            "    canonical = solve_family(True)  # type: PSeq[int]\n"
            "    result = relabel_family(canonical)  # type: PSeq[int]\n"
            "    return result\n"
        ),
        "refinement": "this hard-codes diophantine(eq, param, permute=True) on the "
                      "recursive call regardless of the caller's option. When a "
                      "caller passes permute=False (the default, the common case "
                      "exercised across the P2P diophantine tests — most equations "
                      "are solved WITHOUT permutation), the re-ordering branch "
                      "would now return the full sign/order family instead of the "
                      "single base family the caller asked for. Every P2P "
                      "diophantine assertion of a base (un-permuted) family in a "
                      "non-canonical symbol ordering would then over-enumerate and "
                      "MISMATCH. The faithful real patch does NOT resolve.",
        "rationale": "rejected by POSTCONDITION P1: proves "
                     "Result() == relabel_family(solve_family(True)) but the "
                     "Ensures demands relabel_family(solve_family(expand)); no "
                     "solve_family(True) == solve_family(False) equality is "
                     "granted, so for expand==False the equality is unprovable. "
                     "Correct on the expand==True sub-domain only — guards against "
                     "a spec that pins only the F2P (True) direction.",
    },

    # ATTACK 3 (DROP-THE-RELABELLING — return the canonical family un-rearranged).
    # Re-derive under the caller's `expand` (correct option), but return the
    # canonical family DIRECTLY without applying relabel_family — i.e. omit the
    # per-tuple component re-arrangement (the gold's
    # `tuple([t[dict_sym_index[i]] for i in var])` comprehension). Must reject:
    # the relabel axiom is opaque (NOT asserted to be identity), so the verifier
    # cannot prove solve_family(expand) == relabel_family(solve_family(expand)).
    {
        "id": "weak-drop-relabel",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    # WRONG: skip the per-tuple component re-arrangement; return the\n"
            "    # canonical-ordering family as-is.\n"
            "    canonical = solve_family(expand)  # type: PSeq[int]\n"
            "    return canonical\n"
        ),
        "refinement": "this drops the component re-arrangement comprehension "
                      "{ tuple([t[dict_sym_index[i]] for i in var]) for t in ... } "
                      "and returns the inner recursive call's tuples in the "
                      "CANONICAL symbol ordering, not the caller's requested "
                      "ordering. The whole point of the `if syms != var:` branch "
                      "is that the caller asked for a DIFFERENT symbol order, so "
                      "every returned tuple would have its components in the wrong "
                      "positions. The diophantine tests that supply syms in a "
                      "non-canonical order and assert the re-arranged tuples would "
                      "MISMATCH. The faithful real patch does NOT resolve.",
        "rationale": "rejected by POSTCONDITION P1: proves "
                     "Result() == solve_family(expand) but the Ensures demands "
                     "relabel_family(solve_family(expand)); relabel is "
                     "@ContractOnly/opaque and NOT asserted to be the identity, so "
                     "solve_family(expand) == relabel_family(solve_family(expand)) "
                     "is unprovable in general.",
    },

    # ATTACK 4 (PARTIAL-DOMAIN — asymmetric dispatch, wrong only on True). A
    # subtler partial-domain rival that LOOKS option-aware: it dispatches on
    # `expand` but on the True branch re-derives under the WRONG (False) option,
    # while the False branch is correct. CORRECT on expand==False; WRONG on
    # expand==True (the F2P direction). Must reject: on the True branch it proves
    # Result()==relabel_family(solve_family(False)) but expand==True demands
    # relabel_family(solve_family(True)), and no True==False equality is granted.
    {
        "id": "weak-asymmetric-true-uses-false",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    # WRONG only on the True branch: it consults `expand` but then\n"
            "    # re-derives under False there, collapsing the full family.\n"
            "    if expand:\n"
            "        canonical = solve_family(False)  # type: PSeq[int]\n"
            "    else:\n"
            "        canonical = solve_family(False)\n"
            "    result = relabel_family(canonical)  # type: PSeq[int]\n"
            "    return result\n"
        ),
        "refinement": "this is observationally identical to the prepatch bug on "
                      "the discriminating input: the True branch (the caller asked "
                      "for the FULL permuted family) re-derives with permute=False "
                      "and collapses to the single base solution. The F2P "
                      "y**4 + x**4 - 2**4 - 3**4 with permute=True in a "
                      "non-canonical ordering would again return {(2,3)} relabelled "
                      "instead of the 8-element family, so test_diophantine "
                      "MISMATCHES. The faithful real patch does NOT resolve.",
        "rationale": "rejected by POSTCONDITION P1 on the True branch: it proves "
                     "Result()==relabel_family(solve_family(False)) there, but "
                     "Nagini knows expand==True so the Ensures demands "
                     "relabel_family(solve_family(True)); no solve_family(True) == "
                     "solve_family(False) equality is granted. Correct on the "
                     "expand==False sub-domain only.",
    },
]


# ---------------------------------------------------------------------------
# AXIOM LANE
# ---------------------------------------------------------------------------
# This bundle consumes TWO @ContractOnly A-consumed axioms:
#   * solve_family(expand) — the unchanged recursive diophantine solver, keyed on
#     the option. The proof consumes only the ABSENCE of a True==False equality
#     (the option genuinely changes the family). SOUNDNESS obligation: the real
#     diophantine must, on at least one input in the axiom's domain (any bool),
#     give permute=True != permute=False — and must NOT collapse them (otherwise
#     the discriminating clause of the spec would be vacuous). CONTAINMENT: the
#     model only ever passes a `bool` to solve_family (the caller's `expand`, or
#     the constants True/False in dispatch); the real callee's permute keyword is
#     a bool — every reachable input is in domain. Covering more (it would also
#     accept any bool) is sound.
#   * relabel(token) — the per-tuple component re-arrangement, an injective
#     coordinate permutation. SOUNDNESS obligation: the re-indexing built from
#     dict_sym_index = dict(zip(syms, range(len(syms)))) is a bijection on
#     solution tuples (collision-free, invertible) for every caller symbol
#     ordering. CONTAINMENT: relabel is applied (via relabel_family) only to
#     tokens drawn from solve_family's output — integer solution identities; the
#     real re-indexing is total on any tuple of the right arity, so every
#     reachable token is in domain.
#
# axiom_check.py (G-AX) already validates BOTH obligations against the real sympy
# diophantine and the real component re-indexing in-container (the F2P exact
# families {(2,3)} vs the 8-element sign/order family; permute=True superset of
# permute=False; dict_sym_index a permutation of range(n) and the re-indexing a
# collision-free invertible bijection over every symbol ordering). We re-run that
# HOST-validated oracle IN-CONTAINER as the axiom-lane probe (apply_gold=True so
# the post-patch recursive call shape is present). It CALLS the real diophantine
# and the real tuple re-indexing — it does NOT regex-scrape source (avoids pilot
# bug 4). It reads no bundle files in-container (avoids pilot bug 6): axiom_check.py
# is read on the HOST at load time and embedded verbatim into the probe string. It
# opens no files (no utf-8 codec concern, pilot bug 5). Exit 0 iff every
# obligation holds.
_AXIOM_CHECK_SRC = (Path(__file__).parent / "axiom_check.py").read_text()

AXIOM_TESTS = [
    {
        "id": "ax-solve-family-option-dependence",
        "axiom": "solve_family",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _AXIOM_CHECK_SRC,
        "rationale": "solve_family soundness: the real recursive diophantine must "
                     "genuinely depend on the permute option (permute=True != "
                     "permute=False on at least one input — the F2P equation — and "
                     "permute=True a SUPERSET of permute=False, never a collapse), "
                     "so the axiom's deliberate refusal to assert "
                     "solve_family(True)==solve_family(False) is sound and the "
                     "spec's discriminating clause is well-founded. The probe runs "
                     "the real diophantine on the issue's exact equation "
                     "(y**4 + x**4 - 2**4 - 3**4: permute=True -> the 8-element "
                     "sign/order family, permute=False -> {(2,3)}) plus a second "
                     "test-suite equation. Containment: the model only ever passes "
                     "a bool to solve_family; the real callee's permute keyword is "
                     "a bool, so every reachable input is in domain.",
    },
    {
        "id": "ax-relabel-bijection",
        "axiom": "relabel",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _AXIOM_CHECK_SRC,
        "rationale": "relabel soundness: the real per-tuple component "
                     "re-arrangement built from dict_sym_index = dict(zip(syms, "
                     "range(len(syms)))) must be an INJECTIVE coordinate "
                     "permutation (a bijection on solution tuples) for every "
                     "caller symbol ordering, so the relabelled family preserves "
                     "cardinality and the set image is faithful. The probe checks, "
                     "over EVERY permutation of the canonical symbols and a "
                     "synthetic family of distinct tuples, that dict_sym_index is a "
                     "permutation of range(n), the component map sigma is a "
                     "bijection, the re-indexed family is collision-free (same "
                     "cardinality), and the re-indexing is invertible. Containment: "
                     "relabel is applied only to tokens from solve_family's output "
                     "(integer solution identities); the real re-indexing is total "
                     "on any tuple of the right arity, so every reachable token is "
                     "in domain.",
    },
]
