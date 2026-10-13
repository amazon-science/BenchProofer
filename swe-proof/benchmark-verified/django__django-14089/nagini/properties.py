"""properties.py — PBT falsification manifest for django__django-14089.

NOT a Nagini module: a record of adversarial cases the runner
(`swebench_nagini.pbt`) executes. See the battery-authoring brief (esp. §2 "four
falsification checks" and §4a "Adversarial, NOT mechanical").

This battery is reasoned from THIS spec's defended surface, not stamped out by a
corruption template. The function under spec is

    reverse_order(elements: List[int]) -> List[int]   # the backward enumeration
                                                       # (new OrderedSet.__reversed__)

with the load-bearing contract

    Requires(Acc(list_pred(elements), 1/2))            # READ-ONLY input
    Ensures (Acc(list_pred(elements), 1/2))            # returned read-only
    Ensures (Acc(list_pred(Result())))                 # fresh, full-perm result
    Ensures (ToSeq(Result()) == rev(ToSeq(elements)))  # THE pin: result IS the reversal

What the spec actually defends, and the attacks it must survive:

  * The output pin `ToSeq(Result()) == rev(ToSeq(elements))` is GROUNDED in the
    input: `rev` is a @Pure front-recursive sequence-reversal (NOT @ContractOnly,
    NOT an opaque answer-key marker) applied to `ToSeq(elements)`. It is a
    function OF the argument, fully unfolded by Viper. There is no executable
    materialization of a @Pure PSeq into a list_pred list, so you cannot "echo the
    oracle" — the only way to make `ToSeq(result)` equal `rev(ToSeq(elements))` is
    to build the list element-by-element in reverse, which IS the real reversal
    work. So UNGROUNDED-ORACLE-ECHO does NOT apply here; the honest cheapest-impl
    positive control (`pos-assert-reversal`) stands in for it, and there is no
    *wrong* echo that verifies (else it would be a reject case).

  * `elements` is held READ-ONLY (1/2). The MANDATORY attack is FRAME MUTATION
    (`frame-mutate-elements`): an impl that WRITES to the read-only input must
    fail for INSUFFICIENT PERMISSION, not a value mismatch.

  * The discriminating content of the change is that the backward enumeration is
    the REVERSAL of the forward enumeration, not a copy of it, and visits EVERY
    element exactly once. Every uniqueness rival targets that: preserve order
    (the pre-gold behaviour), drop a boundary element, or return nothing.

  * There is NO control-flow / raise / side-effect difference invisible to the
    value abstraction at the SPEC lane: `reverse_order` is a total function with a
    single return path, no exceptions, returning a fresh list; the materialized-
    list value + the read-only frame capture everything the spec observes. The
    one real-world capability that is NOT a list value — that `reversed(self.dict)`
    yields a one-shot `collections.abc.Iterator` (the F2P type assertion) and is
    read-only — is a property of the REAL builtin callee, so it is discharged on
    the axiom lane (A-reference, ax-rev-ref-sound) exactly as axiom_check.py /
    G-AX checks it. CONTROL-FLOW-EFFECT is therefore N/A at the spec lane.

Authoring mechanics: every spec variant is built by REGION-SURGERY (`_swap`) that
edits ONLY inside `# impl-start`/`# impl-end` (the nested invariants region lives
there too and is elided by `markers.spec_view`), so `markers.same_spec` is
guaranteed and a rejection comes from the POSTCONDITION catching wrong behaviour
(or the permission system), never from a tampered spec. Each `expect:"reject"`
rival carries the refinement argument that its faithful real patch would NOT
resolve the F2P (`test_reversed`: `list(reversed(OrderedSet([1,2,3]))) == [3,2,1]`
and the result isinstance `collections.abc.Iterator`).

A note on the positive control / pilot pitfall #3: `rev` is FRONT-recursive
(`rev(s) = rev(s.drop(1)) + PSeq(s[0])`) and the gold impl is a BACKWARD loop that
APPENDS the head each step (`result = result + [e]`, `i` from len down to 1) with
two framing Asserts that unfold `rev` once per step. A forward-append / reversed-
loop-direction positive control would need an `f(a+b)==f(a)+f(b)` lemma the
verifier won't auto-discharge — that would be a PROOF gap, not a spec defect. So
the positive control keeps the gold loop shape and gold framing Asserts verbatim
and only REORDERS the two independent Asserts and rewrites the loop guard
(`while i > 0` -> `while 0 < i`) — a genuine structural change that preserves
every gold proof obligation.
"""
from pathlib import Path

INSTANCE = "django__django-14089"
FLOAT_ENCODING = None   # meta.json float_encoding is null

# --- base spec (frozen) ------------------------------------------------------
_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src: str, old: str, new: str) -> str:
    """Replace exactly one occurrence of an impl-region substring; assert it
    actually matched so silent drift (model.py edited) fails loudly at load."""
    if old not in src:
        raise AssertionError(f"properties.py drift: substring not found:\n{old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"properties.py: substring not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Region landmarks (all strictly INSIDE the impl region of model.py).
# ---------------------------------------------------------------------------

# The impl head: result init + loop counter. Insertion point for the
# admissibility self-call and the frame-mutation write.
_HEAD = "    result = []  # type: List[int]\n    i = len(elements)\n"

# The two INDEPENDENT framing Asserts as written in gold (read input only / pin
# the head). Reordering them is the structural change for the positive control.
_ASSERTS = (
    "        Assert(ToSeq(elements).drop(i - 1)[0] == e)\n"
    "        Assert(ToSeq(elements).drop(i - 1).drop(1) == ToSeq(elements).drop(i))\n"
)
_ASSERTS_REORDERED = (
    "        Assert(ToSeq(elements).drop(i - 1).drop(1) == ToSeq(elements).drop(i))\n"
    "        Assert(ToSeq(elements).drop(i - 1)[0] == e)\n"
)

# The loop guard.
_GUARD = "    while i > 0:\n"

# The reversing append (build reverse order). The forward-order rival prepends.
_APPEND = "        result = result + [e]\n"

# The gold loop body (counter init through the loop) — replaced wholesale for the
# always-empty rival so the rejection lands on the postcondition cleanly.
_LOOP_BLOCK = (
    "    result = []  # type: List[int]\n"
    "    i = len(elements)\n"
    "    while i > 0:\n"
    "        # invariants-start\n"
    "        Invariant(Acc(list_pred(elements), 1 / 2))\n"
    "        Invariant(Acc(list_pred(result)))\n"
    "        Invariant(0 <= i and i <= len(elements))\n"
    "        Invariant(ToSeq(result) == rev(ToSeq(elements).drop(i)))\n"
    "        Invariant(MustTerminate(i + 1))\n"
    "        # invariants-end\n"
    "        e = elements[i - 1]\n"
    "        Assert(ToSeq(elements).drop(i - 1)[0] == e)\n"
    "        Assert(ToSeq(elements).drop(i - 1).drop(1) == ToSeq(elements).drop(i))\n"
    "        result = result + [e]\n"
    "        i = i - 1\n"
)


# ===========================================================================
# POSITIVE CONTROLS (soundness / admissibility) — expect "verify"
# ===========================================================================

# (5) Structurally-different but CORRECT. Keeps the gold backward-loop shape and
# both gold framing Asserts VERBATIM (pitfall #2/#3: a forward-append variant
# would need a fold-homomorphism lemma; a dropped Assert fails the loop invariant
# for a proof reason). Only the two INDEPENDENT Asserts are reordered and the
# loop guard is rewritten `while i > 0` -> `while 0 < i` (semantically identical).
# If this fails to verify, the postcondition is over-fit to one source shape =>
# SPEC-TOO-STRONG.
_POS_REORDER = _swap(_swap(_BASE, _ASSERTS, _ASSERTS_REORDERED), _GUARD, "    while 0 < i:\n")

# (2/5b) HONEST cheapest impl / no-echo demonstration. The most direct "echo the
# @Pure oracle" attack would be `result = <materialize rev(ToSeq(elements))>`.
# There is NO executable materialization of a @Pure PSeq into a list_pred list, so
# the cheapest impl satisfying the GROUNDED pin still builds the list element-by-
# element in reverse (the real work). This control asserts, right before the
# return (when `result` is the COMPLETE reversal), that what it built EQUALS the
# spec oracle `rev(ToSeq(elements))`. It is CORRECT (expect="verify"); its purpose
# is to show there is no wrong echo that verifies — the oracle is grounded in the
# arg, not an opaque marker. (If a wrong echo could verify, this would instead be
# a SPEC-TOO-WEAK reject; none exists.)
_POS_ASSERT = _swap(
    _BASE, "    return result\n",
    "    Assert(ToSeq(result) == rev(ToSeq(elements)))\n"
    "    return result\n",
)

# (6) ADMISSIBILITY. A self-call on the exact F2P-shaped input [1, 2, 3] must
# establish the precondition `Acc(list_pred(elements), 1/2)` (a pure read-only
# list_pred, no value restriction) for a normal collection. A fresh list grants
# full permission, so passing 1/2 is admissible; the result is discarded and the
# gold body that follows is unchanged. If the self-call fails to establish the
# precondition for a normal input => PRECOND-TOO-STRONG.
_ADMISS = _swap(
    _BASE, _HEAD,
    "    probe = [1, 2, 3]  # type: List[int]\n"
    "    Assert(Acc(list_pred(probe), 1 / 2))\n"
    + _HEAD,
)


# ===========================================================================
# UNIQUENESS RIVALS (spec-too-weak probes) — expect "reject"
# ===========================================================================

# (1) FRAME MUTATION — MANDATORY, the #1 weakness class. `elements` is read-only
# (1/2). This rival appends to `elements` at the impl head (a write through a 1/2
# reference) before doing the gold reversal. Under Acc(list_pred(elements),1/2) a
# mutation of the list_pred requires FULL permission, so it MUST fail for
# INSUFFICIENT PERMISSION (not a value mismatch). The gold body is kept verbatim
# after the write, so the rejection is attributable solely to the illegal store.
# Rejection source: the PERMISSION SYSTEM.
_RIVAL_FRAME = _swap(
    _BASE, _HEAD,
    "    elements.append(0)\n" + _HEAD,
)

# (3, primary partial-domain == the pre-gold BUG) FORWARD ORDER. Prepend each
# element instead of appending (`result = [e] + result`), reproducing the
# insertion order — i.e. the pre-patch behaviour where OrderedSet had no
# __reversed__ and a traversal handed back forward order (this is exactly
# model_prepatch.py's impl, invariant included). Correct ONLY for the symmetric/
# empty/singleton sub-domain; wrong for every collection whose reversal differs
# from itself. Its faithful real patch is
# `def __reversed__(self): return iter(self.dict)`, making
# `list(reversed(OrderedSet([1,2,3]))) == [1,2,3] != [3,2,1]` — the F2P
# `test_reversed` FAILS; it would NOT resolve.
#
# WELL-FORMEDNESS (why the invariant is swapped too): if the prepend is combined
# with the GOLD invariant `ToSeq(result) == rev(ToSeq(elements).drop(i))`, the
# invariant-preservation obligation (prepend vs. the front-recursive `rev`) sends
# Z3 into unbounded `rev`-unfold divergence — the verifier TIMES OUT with no
# verdict instead of rejecting (observed: >=1200s inconclusive => MALFORMED-TESTS
# at G-PBT). The invariants region is elided by markers.spec_view (same_spec
# holds), so the rival carries the invariant that MATCHES its own loop
# (`ToSeq(result) == ToSeq(elements).drop(i)`, exactly model_prepatch.py's): the
# loop body then verifies and the rejection lands DETERMINISTICALLY (~13s) on the
# postcondition — the actual discriminating pin — not on a diverging proof search.
# Rejection source: the postcondition `ToSeq(Result()) == rev(ToSeq(elements))`
# (forward order is not the reversal of any collection with >= 2 elements).
_RIVAL_FORWARD = _swap(
    _swap(_BASE, _APPEND, "        result = [e] + result\n"),
    "        Invariant(ToSeq(result) == rev(ToSeq(elements).drop(i)))\n",
    "        Invariant(ToSeq(result) == ToSeq(elements).drop(i))\n",
)

# (3, partial-domain boundary divergence) DROP THE FIRST INSERTED ELEMENT.
# `while i > 0` -> `while i > 1`: the loop stops at i==1, so elements[0] (the
# first inserted key) is never appended. The output is rev(drop(1)) — the
# reversal of all-but-the-first — correct length-minus-one. Correct on the empty
# sub-domain only; wrong (too short, missing the last reversed element) on every
# non-empty collection. Its faithful real patch is a __reversed__ that omits the
# first inserted element, making `list(reversed(OrderedSet([1,2,3]))) == [3,2]
# != [3,2,1]` — the F2P FAILS; it would NOT resolve. Rejection source: on loop
# exit i==1 so the invariant gives result == rev(drop(1)), and the postcondition
# requires rev(drop(0)) == rev(full) — they differ on any non-empty input.
_RIVAL_DROP_FIRST = _swap(_BASE, _GUARD, "    while i > 1:\n")

# (3b, supporting partial-domain) ALWAYS EMPTY. Replace the whole loop block with
# a no-op that leaves `result == []` (set the counter to 0 so the loop never runs;
# weaken the now-unreached invariant to drop the rev-pin so the empty `result`
# does not have to satisfy it before the loop). Correct ONLY on the empty
# collection; wrong on every non-empty one. Its faithful real patch is a
# __reversed__ returning an empty iterator, making
# `list(reversed(OrderedSet([1,2,3]))) == [] != [3,2,1]` — the F2P FAILS; it would
# NOT resolve. Rejection source: the postcondition
# `ToSeq(Result()) == rev(ToSeq(elements))` (empty != reversal of a non-empty
# collection). Supporting case (a coarser corruption than the reasoned attacks).
_RIVAL_EMPTY = _swap(
    _BASE, _LOOP_BLOCK,
    "    result = []  # type: List[int]\n"
    "    i = 0\n"
    "    while i > 0:\n"
    "        # invariants-start\n"
    "        Invariant(Acc(list_pred(elements), 1 / 2))\n"
    "        Invariant(Acc(list_pred(result)))\n"
    "        Invariant(0 <= i and i <= len(elements))\n"
    "        # invariants-end\n"
    "        i = i - 1\n",
)


SPEC_TESTS = [
    # ---- positive controls (must VERIFY) ----
    {"id": "pos-assert-reorder", "kind": "soundness", "expect": "verify",
     "module": _POS_REORDER,
     "rationale": "structurally-different (the two INDEPENDENT framing Asserts are reordered and "
                  "the loop guard rewritten `while i > 0` -> `while 0 < i`) but behaviourally "
                  "identical impl; keeps the gold backward-loop shape and both gold Asserts "
                  "verbatim so the front-recursive `rev` unfold still discharges. If it fails to "
                  "verify, the spec is over-fit to one source shape => SPEC-TOO-STRONG."},
    {"id": "pos-assert-reversal", "kind": "soundness", "expect": "verify",
     "module": _POS_ASSERT,
     "rationale": "the cheapest impl satisfying the GROUNDED pin still does the real reversal work "
                  "(no executable materialization of the @Pure oracle `rev` into a list_pred list "
                  "exists). Asserting result == rev(ToSeq(elements)) right before return is "
                  "redundant with the gold proof and must verify. Demonstrates the spec is NOT "
                  "echo-vulnerable: there is no wrong oracle-echo that verifies (else this would "
                  "be a reject case). Stands in for the N/A ungrounded-oracle-echo class."},
    {"id": "admiss-f2p-shape", "kind": "admissibility", "expect": "verify",
     "module": _ADMISS,
     "rationale": "a self-call on the exact F2P-shaped input [1,2,3] must establish the "
                  "precondition Acc(list_pred(elements),1/2) for a normal collection (a fresh "
                  "list grants full perm, so 1/2 is admissible); if not, PRECOND-TOO-STRONG."},

    # ---- uniqueness rivals (must be REJECTED) ----
    {"id": "frame-mutate-elements", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_FRAME,
     "refinement": "no faithful resolving patch corresponds to this: the real "
                   "`__reversed__(self): return reversed(self.dict)` does NOT mutate self.dict "
                   "(reversed yields a fresh read-only iterator; G-AX confirms materializing it "
                   "leaves the forward enumeration unchanged). This rival exists only to test "
                   "whether the read-only (1/2) precondition can be subverted by writing to "
                   "`elements`. A verifying rival here would be a pure verify⇏resolve artifact "
                   "(vacuous satisfaction via self-mutation); no resolving patch overwrites the "
                   "collection it is asked to reverse.",
     "rationale": "MANDATORY frame-mutation probe. `elements.append(0)` mutates a list held at "
                  "1/2 (read-only) permission and MUST fail for insufficient permission. "
                  "Rejection source: the PERMISSION SYSTEM (the append needs full perm on "
                  "list_pred(elements), only 1/2 is held), not a value mismatch; the gold body is "
                  "kept verbatim after the write. If it verified => SPEC-TOO-WEAK (frame "
                  "protection hollow)."},
    {"id": "forward-order", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_FORWARD,
     "refinement": "prepends instead of appends, reproducing forward (insertion) order — exactly "
                   "the pre-gold behaviour (model_prepatch.py, invariant included). Its faithful "
                   "real patch is `def __reversed__(self): return iter(self.dict)`, making "
                   "`list(reversed(OrderedSet([1,2,3]))) == [1,2,3] != [3,2,1]` — the F2P "
                   "`test_reversed` FAILS; it would NOT resolve. This is the behaviour class the "
                   "gold patch fixes (a backward enumeration that PRESERVES rather than REVERSES "
                   "the order).",
     "rationale": "the named adversary of the postcondition comment ('a traversal that preserves "
                  "rather than reverses the order'). The rival carries the invariant matching its "
                  "own loop (`ToSeq(result) == ToSeq(elements).drop(i)`, model_prepatch.py's; the "
                  "invariants region is spec_view-elided so same_spec holds) so Z3 does not "
                  "diverge unfolding `rev` against a prepend and the verdict is deterministic. "
                  "Rejection source: the postcondition `ToSeq(Result()) == rev(ToSeq(elements))` "
                  "(forward order is not the reversal of any collection with >= 2 elements). If "
                  "it verified => SPEC-TOO-WEAK (admits forward order as a 'reversal')."},
    {"id": "drop-first-element", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_DROP_FIRST,
     "refinement": "`while i > 1` stops one short, never appending elements[0]; the output is the "
                   "reversal of all-but-the-first inserted key. Its faithful real patch is a "
                   "__reversed__ that omits the first inserted element, making "
                   "`list(reversed(OrderedSet([1,2,3]))) == [3,2] != [3,2,1]` — the F2P FAILS; it "
                   "would NOT resolve.",
     "rationale": "partial-domain boundary divergence (correct on the empty sub-domain only; "
                  "too-short on every non-empty collection). Rejection source: on loop exit i==1, "
                  "so the invariant gives result == rev(drop(1)), but the postcondition requires "
                  "rev(drop(0)) == rev(full); they differ on any non-empty input. If it verified "
                  "=> SPEC-TOO-WEAK (the reversal need not visit every element)."},
    {"id": "always-empty", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_EMPTY,
     "refinement": "returns the empty list for every input (loop never runs). Its faithful real "
                   "patch is a __reversed__ returning an empty iterator, making "
                   "`list(reversed(OrderedSet([1,2,3]))) == [] != [3,2,1]` — the F2P FAILS; it "
                   "would NOT resolve.",
     "rationale": "supporting partial-domain (correct on the empty collection only). Rejection "
                  "source: the postcondition `ToSeq(Result()) == rev(ToSeq(elements))` — an empty "
                  "result is not the reversal of any non-empty collection. If it verified => "
                  "SPEC-TOO-WEAK."},
]

# ===========================================================================
# AXIOM LANE (Docker, real `reversed(dict)` builtin)
# ===========================================================================
# No @ContractOnly axiom is CONSUMED (model.py's axioms region is empty). The
# deep model `rev` is an A-REFERENCE: validated equal to the REAL callee the gold
# patch invokes — the CPython builtin `reversed` over a `dict`
# (`reversed(self.dict)`). These probes reuse axiom_check.py's logic, EXECUTING
# the real callee (never scraping source) and reading its observed values, in the
# instance image where the real Python (>=3.8, dict reverse-iteration) lives.

# (1) A-reference soundness: the deep model `rev` must equal the REAL
# `reversed(dict.fromkeys(items))` over boundary + heavy fuzz; the backward
# traversal must be a one-shot `collections.abc.Iterator` (the F2P type
# obligation); and materializing it must leave the forward enumeration unchanged
# (read-only). This is exactly axiom_check.py's logic, run in-container against
# the real builtin. apply_gold=True (post-gold behaviour; builtins are stdlib so
# the repo is not strictly required, but we keep it for fidelity).
_AX_REV_SOUND = r'''
import collections.abc
import random
import sys

# The image must support dict reverse-iteration (Python >= 3.8); the instance
# runs Python 3.9.
assert sys.version_info >= (3, 8), ("dict reverse-iteration needs Python >= 3.8; "
                                    "got %r" % (sys.version_info,))

def rev(seq):
    # model.py deep model `rev`: the element-wise reversal (rev(s) = rev(s.drop(1)) + [s[0]]).
    out = []
    for i in range(len(seq) - 1, -1, -1):
        out.append(seq[i])
    return out

def build_collection(items):
    # OrderedSet carrier: distinct keys in insertion order (dict.fromkeys, as in
    # OrderedSet.__init__: self.dict = dict.fromkeys(iterable or ())).
    return dict.fromkeys(items)

def check(items):
    d = build_collection(items)
    forward = list(iter(d))                 # real forward enumeration (== model `elements`)
    backward_iter = reversed(d)             # the REAL callee the gold patch invokes
    # F2P type obligation: reversed(...) is a one-shot iterator.
    assert isinstance(backward_iter, collections.abc.Iterator), (
        "A-REF-UNSOUND: backward enumeration of %r is not an Iterator (got %r)"
        % (items, type(backward_iter)))
    backward = list(backward_iter)          # materialize the real callee
    expected = rev(forward)                 # deep model `rev`
    assert backward == expected, (
        "A-REF-UNSOUND: rev deep model != reversed(dict) on %r: real=%r model=%r"
        % (items, backward, expected))
    # Read-only: materializing the backward iterator leaves forward order intact.
    assert list(iter(d)) == forward, (
        "A-REF-UNSOUND: backward enumeration mutated the collection on %r" % (items,))
    # Distinct-key carrier: element k of backward == element (n-1-k) of forward.
    n = len(forward)
    for k in range(n):
        assert backward[k] == forward[n - 1 - k], (
            "A-REF-UNSOUND: element %d of backward != element %d of forward on %r"
            % (k, n - 1 - k, items))

boundary = [
    [], [1], [1, 2, 3], [3, 2, 1], [0], [-1, 0, 1],
    list(range(10)), list(range(50)), [5, 4, 3, 2, 1],
    [1, 1, 2, 2, 3, 3],            # duplicates collapse to distinct keys
    [2, 1, 2, 3, 1],
    ["a", "b", "c"], ["c", "b", "a"],   # OrderedSet is generic over hashables
    [None], [True, False],
]
for items in boundary:
    check(items)

rng = random.Random(14089)
for _ in range(20000):
    n = rng.randint(0, 24)
    items = [rng.randint(-8, 8) for _ in range(n)]   # small pool -> duplicates exercised
    check(items)

# The F2P witness must read [3, 2, 1], and the iterator must be one-shot.
w_iter = reversed(dict.fromkeys([1, 2, 3]))
assert isinstance(w_iter, collections.abc.Iterator), type(w_iter)
assert list(w_iter) == [3, 2, 1], "F2P witness wrong"
assert list(w_iter) == [], "iterator is not one-shot (exhausted after first list())"

print("AXIOM-SOUND: deep model `rev` == real reversed(dict) on", len(boundary),
      "boundary + 20000 fuzz inputs; backward traversal is a one-shot Iterator and read-only.")
sys.exit(0)
'''

# (2) A-reference containment: every callee-input the MODEL can reach lies in the
# REAL callee's domain. The model reaches `reversed(d)` where d = dict.fromkeys(
# elements) and `elements` is an arbitrary List[int] of distinct keys (the
# model's only Requires is Acc(list_pred(elements),1/2) — a pure read-only
# list_pred, NO value/length restriction). The real callee `reversed(dict)` is
# TOTAL over any dict on Python >= 3.8 (the image is 3.9), so every reachable
# shape — empty, singleton, large, duplicate-collapsing, any int/hashable keys —
# is in domain. Covering MORE (any hashable) than the model reaches (ints) is
# SOUND (the float-vs-int rule). The probe confirms reversed succeeds (no
# TypeError / not-reversible) for the full spread of reachable shapes.
_AX_REV_CONTAINMENT = r'''
import collections.abc
import sys

assert sys.version_info >= (3, 8), ("reversed(dict) needs Python >= 3.8; got %r"
                                    % (sys.version_info,))

# Shapes the model can reach: the model's Requires places NO value/length bound on
# `elements`, so the reachable dicts are dict.fromkeys(<any list of keys>): empty,
# singleton, large, duplicate-collapsing, mixed hashables.
reachable = [
    [],                              # empty collection
    [1],                             # singleton
    [1, 2, 3],                       # the F2P witness
    list(range(100)),                # large
    [1, 1, 2, 2, 3, 3],             # duplicates collapse to distinct keys
    [-5, -1, 0, 7, 7, 3],           # negatives + duplicates
    ["a", "b", "c"], [None], [True, False],   # generic hashables
]
for items in reachable:
    d = dict.fromkeys(items)
    # reversed(dict) must be DEFINED for every reachable input (else it is outside
    # the callee's domain => AXIOM-TOO-WEAK-FOR-CALLER). On a dict it never raises.
    it = reversed(d)
    assert isinstance(it, collections.abc.Iterator), (items, type(it))
    materialized = list(it)
    # length must match the distinct-key count (in-domain, well-defined output).
    assert len(materialized) == len(d), (items, materialized)

# Confirm a plain dict is reversible at all on this image (the carrier type).
assert hasattr(dict, "__reversed__") or list(reversed({1: 0})) == [1], \
    "dict is not reverse-iterable on this image"

print("CONTAINMENT OK: reversed(dict.fromkeys(...)) is total over every model-reachable shape "
      "(empty / singleton / large / duplicate-collapsing / mixed hashables); "
      "model-reachable inputs (List[int] distinct keys) are a subset of the callee domain (any dict).")
sys.exit(0)
'''

AXIOM_TESTS = [
    {"id": "ax-rev-ref-sound", "axiom": "rev", "kind": "axiom-soundness",
     "expect": "holds", "apply_gold": True, "probe": _AX_REV_SOUND,
     "rationale": "the A-reference deep model `rev` must equal the REAL callee the gold patch "
                  "invokes — `reversed(self.dict)`, the CPython builtin over a dict built with "
                  "dict.fromkeys — on boundary + 20000 fuzz inputs (incl. empty, duplicate-"
                  "collapsing keys, the F2P witness [1,2,3]->[3,2,1]); the backward traversal "
                  "must be a one-shot collections.abc.Iterator (the F2P type obligation) and "
                  "read-only. Any mismatch => deep-model UNSOUND. Executes the real builtin in "
                  "the instance image; never scrapes source. Mirrors axiom_check.py / G-AX."},
    {"id": "ax-rev-containment", "axiom": "rev", "kind": "axiom-containment",
     "expect": "covered", "apply_gold": True, "probe": _AX_REV_CONTAINMENT,
     "rationale": "every callee-input the model can reach — reversed(dict.fromkeys(elements)) for "
                  "an arbitrary List[int] of distinct keys (the model's Requires places no "
                  "value/length bound) — lies in the real callee's domain: reversed(dict) is "
                  "total over any dict on Python >= 3.8 (the image is 3.9). A reachable shape "
                  "outside that domain => AXIOM-TOO-WEAK-FOR-CALLER; covering more (any hashable) "
                  "is sound (float-vs-int rule)."},
]
