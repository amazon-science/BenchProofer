# properties.py — PBT manifest for sphinx-doc__sphinx-10673. NOT a Nagini module;
# a record of adversarially-reasoned falsification cases. The runner
# (swebench_nagini.pbt) writes each SPEC_TESTS["module"] to a temp file, runs the
# Nagini verifier + markers.same_spec against the frozen model.py, and stamps a
# RESULT. Every spec variant is built by region-surgery (_swap) editing ONLY text
# inside # impl-start/# impl-end, so the frozen spec (axioms/pure/pre/post) is
# never touched and same_spec is guaranteed.
#
# Defended surface (read from model.py / meta.json / refinement.md):
#   select_toctree_entries(entries, found, generated): all three are List[int]
#   with Acc(list_pred(.),1/2) -> READ-ONLY inputs (frame-mutation MANDATORY).
#   Output is a fresh List[int]. Load-bearing postcondition:
#       Ensures(ToSeq(Result()) == kept(ToSeq(entries),ToSeq(found),ToSeq(generated)))
#   pinning the exact output sequence to the front-recursive `kept` fold, whose
#   head decision is known(x,found,gen) == mem(x,found) or mem(x,gen) (membership
#   in EITHER family). The discriminating behaviour: a target present in
#   `generated` but absent from `found` must be RETAINED (the genindex/modindex/
#   search bug fix). The oracle `kept` is GROUNDED in the inputs (a pure,
#   fully-unfolded function of the args) -> no wrong echo is possible; the
#   ungrounded-oracle lane is therefore N/A (see assessment) and we use an honest
#   structurally-different positive control instead. No raise/side-effect distinct
#   from the value abstraction -> control-flow-effect lane N/A.
#
# Axiom lane: meta.axioms == []; there is NO @ContractOnly consumed axiom. The
# single A-reference is the deep model `kept`, validated == real set-union
# membership by axiom_check.py (G-AX). We re-run that obligation as an
# axiom-containment/soundness probe (stdlib-only, runs in-container under
# apply_gold) so the deep model's fidelity is part of the persisted battery.
from pathlib import Path

INSTANCE = "sphinx-doc__sphinx-10673"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# 1. FRAME-MUTATION (MANDATORY — all three inputs are Acc(.,1/2) read-only).
#    A rival that WRITES to the read-only input `entries` to "satisfy" the
#    postcondition. The write `entries[i - 1] = x` requires FULL permission on
#    list_pred(entries); the precondition grants only Acc(list_pred(entries),1/2),
#    so the assignment cannot be framed and the function must be REJECTED for
#    insufficient permission. Gold invariants/asserts are kept verbatim so the
#    rejection is attributable solely to the write, not a proof gap.
_FRAME = _swap(
    _BASE,
    "        x = entries[i - 1]\n",
    "        x = entries[i - 1]\n"
    "        entries[i - 1] = x  # ATTACK: write to a 1/2-permission read-only input\n",
)

# ---------------------------------------------------------------------------
# 2. POSITIVE CONTROL (soundness). A structurally-DIFFERENT but CORRECT impl:
#    a local-variable reshape that hoists the classification into a boolean local
#    `is_known` and branches on it, and builds the prepend via a typed local
#    `head` instead of an inline `[x]`. Front-prepend ([x] + result) is kept (no
#    forward-append-against-front-recursive-fold lemma gap, per pilot bug #3);
#    every gold framing Assert is preserved verbatim (pilot bug #2). `known` is
#    @Pure so `is_known` is definitionally the same predicate the kept-fold
#    branches on -> the gold proof still discharges. Must VERIFY (else
#    SPEC-TOO-STRONG).
_POS = _swap(
    _BASE,
    "        if known(x, ToSeq(found), ToSeq(generated)):\n"
    "            # head is known: kept unfolds to PSeq(x) + kept(tail)",
    "        is_known = known(x, ToSeq(found), ToSeq(generated))\n"
    "        if is_known:\n"
    "            # head is known: kept unfolds to PSeq(x) + kept(tail)",
)
_POS = _swap(
    _POS,
    "            old_seq = ToSeq(result)\n"
    "            result = [x] + result\n"
    "            Assert(ToSeq(result) == PSeq(x) + old_seq)",
    "            old_seq = ToSeq(result)\n"
    "            head = [x]  # type: List[int]\n"
    "            result = head + result\n"
    "            Assert(ToSeq(result) == PSeq(x) + old_seq)",
)

# ---------------------------------------------------------------------------
# 3. ADMISSIBILITY (precondition not too strong). The gold impl verbatim is the
#    witness that Acc(list_pred(entries/found/generated),1/2) admits a normal
#    F2P-shaped input and the loop body's reads (entries[i-1], the membership
#    folds) all frame. We mark a no-op-reshaped copy (a benign comment inside the
#    impl) so the case is a distinct module yet provably the same executable
#    behaviour. Must VERIFY (else PRECOND-TOO-STRONG).
_ADMISS = _swap(
    _BASE,
    "    result = []  # type: List[int]\n",
    "    result = []  # type: List[int]\n"
    "    # admissibility witness: precond admits an F2P-shaped in-domain input\n",
)

# ---------------------------------------------------------------------------
# 4. PARTIAL-DOMAIN (uniqueness / SPEC-TOO-WEAK probe). A rival that classifies
#    against the discovered-source family ALONE — `mem(x, ToSeq(found))` instead
#    of `known(x, found, gen)` — i.e. the PRE-PATCH behaviour. It is correct on
#    every input whose retained set is unaffected by the generated family, but
#    DROPS a target that is generated-only (genindex/modindex/search), diverging
#    exactly on the F2P sub-domain. The postcondition pins ToSeq(Result()) to
#    kept(...) whose head decision is known() (the union), so the if-branch's
#    gold unfold lemma (kept(cons) == PSeq(x) + kept(tail), valid only when
#    known(x)) cannot be discharged when the branch fires on mem(x,found) alone
#    for a generated-only x -> REJECTED at the postcondition's kept/known clause.
_PARTIAL_FOUND = _swap(
    _BASE,
    "        if known(x, ToSeq(found), ToSeq(generated)):\n"
    "            # head is known: kept unfolds to PSeq(x) + kept(tail)",
    "        if mem(x, ToSeq(found)):  # ATTACK: discovered-source family ALONE (pre-patch)\n"
    "            # head is known: kept unfolds to PSeq(x) + kept(tail)",
)

# ---------------------------------------------------------------------------
# 5. PARTIAL-DOMAIN (second variant): drop the FIRST listed target unconditionally
#    (skip the last loop step, i.e. stop at i == 1 instead of i == 0). Correct on
#    every input whose first entry is unknown (already dropped) or empty, but wrong
#    whenever the first entry is known. Its faithful real patch (a parse loop that
#    never classifies the first content line) would drop a leading retained target
#    and NOT resolve the F2P (the genindex/modindex/search toctree's first entry
#    must be retained). Must REJECT: the postcondition demands ToSeq(Result()) ==
#    kept over the WHOLE entries sequence (drop(0)); stopping at i==1 leaves
#    result == kept(drop(1)) != kept(drop(0)) when the head is known.
_PARTIAL_FIRST = _swap(
    _BASE,
    "    while i > 0:\n",
    "    while i > 1:  # ATTACK: never classify the first listed target\n",
)


SPEC_TESTS = [
    {
        "id": "frame-mutation-write-entries",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _FRAME,
        "refinement": (
            "The real parse_content reads each listed target name; it never "
            "rewrites self.content / the iterated docname. A faithful patch that "
            "mutated the source content sequence in place would corrupt the very "
            "list the F2P test inspects (env.tocs['index'] entries) and would not "
            "produce entries=[(None,'genindex'),(None,'modindex'),(None,'search')] "
            "-> would NOT resolve. The only reason a verifier would accept the "
            "write is if the read-only contract were too weak."
        ),
        "rationale": (
            "Inputs carry only Acc(list_pred(entries),1/2); the assignment "
            "entries[i-1]=x needs full write permission on list_pred(entries), "
            "which the precondition does not grant. REJECT for insufficient "
            "permission (the frame/permission system), not for a value mismatch."
        ),
    },
    {
        "id": "pos-control-local-reshape",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS,
        "rationale": (
            "A structurally-different but behaviourally-identical impl (hoist the "
            "@Pure classification into a boolean local `is_known`; build the "
            "prepend via a typed local `head` keeping the front-prepend shape). "
            "All gold framing Asserts are preserved, so it MUST verify; if it did "
            "not, the spec would be SPEC-TOO-STRONG (rejecting a correct impl)."
        ),
    },
    {
        "id": "admiss-gold-shape",
        "kind": "admissibility",
        "expect": "verify",
        "module": _ADMISS,
        "rationale": (
            "Witness that the precondition Acc(list_pred(.),1/2) on all three "
            "inputs admits a normal F2P-shaped input and that every read in the "
            "loop body frames; the function verifies (else PRECOND-TOO-STRONG)."
        ),
    },
    {
        "id": "partial-domain-found-only",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _PARTIAL_FOUND,
        "refinement": (
            "This IS the pre-patch behaviour (docname not in self.env.found_docs "
            "alone). On the F2P toctree the three targets genindex/modindex/search "
            "are generated-only (present in generated_docnames, absent from "
            "found_docs), so this rival drops them and emits the 'nonexisting "
            "document' warning -> entries would be empty, NOT "
            "[(None,'genindex'),(None,'modindex'),(None,'search')] -> would NOT "
            "resolve. It matches model_prepatch.py (G-DIFF)."
        ),
        "rationale": (
            "The postcondition pins ToSeq(Result()) == kept(...), whose head "
            "decision is known() = membership in EITHER family. Branching on "
            "mem(x,found) alone diverges from kept's branch for a generated-only "
            "x, so the if-branch's gold unfold lemma kept(cons)==PSeq(x)+kept(tail) "
            "(provable only when known(x)) fails -> REJECT at the kept/known clause."
        ),
    },
    {
        "id": "partial-domain-drop-first",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _PARTIAL_FIRST,
        "refinement": (
            "A faithful real patch that never classified the first content line of "
            "a toctree would drop a leading retained target. On the F2P toctree the "
            "first listed target (genindex) must be retained; dropping it yields "
            "entries=[(None,'modindex'),(None,'search')] != the asserted "
            "[(None,'genindex'),(None,'modindex'),(None,'search')] -> would NOT "
            "resolve."
        ),
        "rationale": (
            "Stopping the backward loop at i==1 leaves result == kept(drop(1)); the "
            "postcondition demands ToSeq(Result()) == kept(drop(0)) over the WHOLE "
            "sequence. When entries[0] is known these differ, so the final "
            "postcondition equality cannot be established -> REJECT at the kept "
            "(full-sequence) clause."
        ),
    },
]


# ---------------------------------------------------------------------------
# AXIOM LANE. meta.axioms == [] (no @ContractOnly consumed axiom). The single
# A-reference is the deep model `kept`; its fidelity obligation (kept ==
# real set-union membership) is exactly what axiom_check.py / G-AX validates.
# We re-run that obligation as a persisted probe so the deep model's soundness is
# part of the battery. The probe is stdlib-only (set union + membership are Python
# language primitives — no repo callee to import), opens nothing, and exits 0 iff
# the deep model agrees with the real semantics on the F2P scenario + boundaries +
# fuzz. This doubles as the axiom-containment check: the model's reachable callee
# inputs (any List[int] entries/found/generated) are precisely the inputs over
# which set-union membership is total, so every caller-reachable input is covered.
_AX_PROBE = r'''
import random, sys

def mem(x, s):
    for e in s:
        if e == x:
            return True
    return False

def known(x, found, gen):
    # deep model `known` (== model.py: mem(x,found) or mem(x,gen))
    return mem(x, found) or mem(x, gen)

def kept(entries, found, gen):
    # deep model `kept` (order-preserving retention filter, front-recursive in
    # model.py; reproduced iteratively here — same value)
    out = []
    for e in entries:
        if known(e, found, gen):
            out.append(e)
    return out

def real_select(entries, found, gen):
    # the real patched semantics: docname in self.env.found_docs | generated_docnames
    universe = set(found) | set(gen)
    return [e for e in entries if e in universe]

def check(entries, found, gen):
    m = kept(entries, found, gen)
    r = real_select(entries, found, gen)
    assert m == r, ("deep model `kept` != real set-union membership on "
                    "entries=%r found=%r gen=%r: model=%r real=%r"
                    % (entries, found, gen, m, r))

def run():
    # concrete F2P scenario: the three generated reference pages, present in
    # generated, absent from found, must all be retained in order.
    FOO, GENINDEX, MODINDEX, SEARCH = 1, 100, 101, 102
    found = [FOO]
    generated = [GENINDEX, MODINDEX, SEARCH]
    entries = [GENINDEX, MODINDEX, SEARCH]
    res = kept(entries, found, generated)
    assert res == [GENINDEX, MODINDEX, SEARCH], (
        "F2P scenario broken: the three generated reference pages must all be "
        "retained, in order; got %r" % (res,))
    check(entries, found, generated)
    check([FOO, GENINDEX, MODINDEX, SEARCH], found, generated)
    check([999, GENINDEX, 42, SEARCH], found, generated)

    boundary = [
        ([], [], []),
        ([1], [], []),
        ([1], [1], []),
        ([1], [], [1]),
        ([1, 1], [], [1]),
        ([1, 2, 3], [2], [3]),
        ([3, 2, 1], [2], [3]),
        ([5], [5], [5]),
        ([1, 2, 3, 4, 5], [1, 2], [3, 4]),
    ]
    for e, f, g in boundary:
        check(e, f, g)

    rng = random.Random(10673)
    for _ in range(50000):
        nf = rng.randint(0, 8)
        ng = rng.randint(0, 4)
        ne = rng.randint(0, 12)
        f = [rng.randint(0, 20) for _ in range(nf)]
        g = [rng.randint(0, 20) for _ in range(ng)]
        e = [rng.randint(0, 20) for _ in range(ne)]
        check(e, f, g)

    print("AX OK: deep model `kept` == real set-union membership over "
          "%d boundary + 50000 fuzz inputs; F2P scenario retains all three "
          "generated reference pages in order" % (len(boundary),))

try:
    run()
except AssertionError as exc:
    print("AX FAIL:", exc)
    sys.exit(1)
sys.exit(0)
'''


AXIOM_TESTS = [
    {
        "id": "ax-kept-deep-model-soundness",
        "axiom": "kept",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _AX_PROBE,
        "rationale": (
            "The deep model `kept` (the A-reference) must equal the real patched "
            "semantics `docname in self.env.found_docs | generated_docnames` on "
            "every caller-reachable input. Set union + membership are Python "
            "language primitives (no repo callee to import), so the probe is "
            "stdlib-only and reproduces axiom_check.py: it asserts kept == "
            "[e for e in entries if e in set(found)|set(generated)] over the F2P "
            "scenario + 9 boundary + 50000 fuzz inputs. Any disagreement => the "
            "A-reference is unsound (model.py's classification != the patch's)."
        ),
    },
    {
        "id": "ax-kept-caller-domain-containment",
        "axiom": "kept",
        "kind": "axiom-containment",
        "expect": "covered",
        "apply_gold": True,
        "probe": _AX_PROBE,
        "rationale": (
            "Containment: the inputs the modeled function can reach are arbitrary "
            "List[int] (entries/found/generated under Acc(.,1/2), no value "
            "restriction in Requires). Set-union membership is total over all such "
            "lists, so every caller-reachable input lies in the A-reference's "
            "domain — covered, never AXIOM-TOO-WEAK-FOR-CALLER. The same fuzz over "
            "the unrestricted int domain witnesses total coverage."
        ),
    },
]
