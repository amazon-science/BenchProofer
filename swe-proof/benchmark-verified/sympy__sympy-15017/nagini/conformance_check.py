#!/usr/bin/env python3
"""G-CONF differential conformance check for sympy__sympy-15017 (nagini).

Refutes (never proves) the R/I refinement leg that no other gate covers: does
the MODEL in `model.py` actually agree with the REAL patched repository code it
claims to model?  G-VERIFY says the impl meets the spec, G-PBT says no wrong
impl meets the spec; neither one ever looks at sympy.

SHADOW — the `# impl-start` / `# impl-end` region of `model.py`, copied
         VERBATIM (the model IS Python, so there is no transliteration step),
         with only the contract calls deleted: the `Invariant(...)` block
         between `# invariants-start` / `# invariants-end`, the two `Assert`
         lines, and — in the copied `@Pure` region — the `Requires`/`Ensures`
         lines and the `@Pure` decorator.  Nothing was renamed, reordered or
         "simplified": the loop still seeds `acc = 1`, still walks `i` upward,
         still multiplies `acc * shape[i]`.

         The copy is not merely asserted to be verbatim, it is MACHINE-CHECKED
         at run time: `_check_shadow_verbatim()` parses `/work/model.py` (the
         bundle dir is mounted at the script's own directory), strips docstrings
         and contract statements from the AST of `axis_count`,
         `lemma_axis_count_unfold` and `array_element_count`, and requires the
         resulting `ast.dump` to be byte-identical to the same-named functions
         in THIS file.  If the shadow ever drifts from the frozen model, the
         script fails before it reaches the differential — a paraphrased shadow
         cannot silently pass here.

         Nagini carrier shim: `PSeq` (immutable pure sequence: `len`, `[]`,
         `+`, `take`, `drop`, `==`) and `ToSeq(list)`.  There is no
         `@ContractOnly` callee to redirect — mapping.md §3 records that the
         changed operation is modeled DEEPLY, so the `axioms` region is empty
         and no axiom is assumed.

         Because the fold is modeled deeply, this check diffs BOTH sides of the
         model against the real code, not just the impl:
           * the impl region's loop result, and
           * the postcondition's own witness `axis_count(ToSeq(shape),
             len(shape))` — the `@Pure` deep model of the patched
             `functools.reduce(lambda x,y: x*y, shape, 1)` (mapping.md §2,
             row 3).
         Both must equal the real value on every input.  Diffing the spec
         witness is the leg a nonexistent `axiom_check.py` would otherwise
         leave unchecked.

ORACLE — the REAL patched repo function, CALLED, never transliterated:
         `ImmutableDenseNDimArray._new`'s `self._loop_size = ...` assignment,
         `sympy/tensor/array/dense_ndim_array.py:152` @ base_commit
         6810dee426943c1a2fe85b5002dd0d4cf2246a05 (mapping.md §1).  The gate
         applies the gold patch and sets PYTHONPATH=/testbed before this runs,
         so the patched function is imported and executed directly; there is no
         reimplementation of it anywhere in this file.  `_assert_patched()`
         inspects the LIVE source of `_new` and refuses to run unless the
         patched `reduce(..., shape, 1)` form is present and the pre-patch
         `if shape else 0` form is gone — a green run against unpatched code
         would certify nothing.

         The observable is read two independent ways that must agree with each
         other as well as with the shadow:
           (a) `arr._loop_size` — the value the patched assignment stores, and
           (b) `len(arr)` — how the repo reports it (`NDimArray.__len__`,
               ndim_array.py:164-178, is literally `return self._loop_size`),
               checked whenever CPython's `__len__` protocol permits it
               (0 <= n < 2**63; it raises for negative or non-index-sized n).
         Only the IMMUTABLE class is used: the gold patch changes
         `ImmutableDenseNDimArray._new` alone, mapping.md §1 binds the model to
         that path, and `MutableDenseNDimArray._new` (:177) still carries the
         pre-patch expression.  Diffing the Mutable path would report a
         disagreement that is outside the modeled unit, not a bundle finding.

BRIDGE — mapping.md §2, inverted.  Model side: `shape` is a `List[int]` of axis
         lengths (`PSeq[int]` inside the specification via `ToSeq`).  Repo side:
         `shape` is a `sympy.Tuple` of `_sympify`-ed `Integer` axis lengths.
         Forward: `ImmutableDenseNDimArray([], shape=tuple(shape))` — the empty
         iterable is deliberate, since `_loop_size` is a function of `shape`
         alone, so no input needs O(product) memory and the domain is not
         quietly narrowed to shapes that fit in RAM.  Backward:
         `int(arr._loop_size)`.  The bridge is VALIDATED on every single input
         rather than assumed: the script requires
         `tuple(int(d) for d in arr.shape) == tuple(shape)` and
         `arr._rank == len(shape)`, so an input that the constructor silently
         normalized could never be scored as agreement.

INPUTS — the model's `Requires` is only `Acc(list_pred(shape), 1/2)` plus
         `MustTerminate(2)`: it constrains the LIST, not the integers, so every
         `List[int]` of any length is in the domain and the check must not
         narrow it.  This domain is infinite, so it is not enumerated whole;
         instead:
           1. boundary cases, including the exact F2P shapes built through the
              F2P's own literal constructor calls (rank-0 scalar `Array(x)`,
              `([], shape=(0,))`, `([23])`, `(range(3**4), (3,3,3,3))`);
           2. an EXHAUSTIVE sweep of the finite sub-lattice rank 0..5 x axis
              lengths in {-2,-1,0,1,2,3} (9331 shapes) — every rank/sign/zero
              combination in that box, not a sample of it;
           3. seeded fuzz over the unrestricted domain — negative axis lengths
              and products up to ~1e480, which `len()` rejects but the model's
              `Requires` admits and `_loop_size` computes — to fill the count.
         Both impl branches are covered: zero loop iterations (rank 0, the
         empty product / the bug under specification) and >= 1 iteration, and
         both `axis_count` cases (`k == 0` base, recursive step).

Exit 0 iff zero disagreements.  stdlib + sympy only; seed pinned below and
recorded in mapping.md §"G-CONF".
"""
import ast
import itertools
import json
import os
import random
import sys
from typing import List

SEED = 15017
N_TARGET = 100_000          # >= 1e5 Requires-satisfying inputs
MAX_REPORTED = 5

# CPython's __len__ protocol only accepts 0 <= n < 2**63; outside that range the
# repo can only be observed through _loop_size (the patched assignment itself).
_LEN_MAX = 2 ** 63


# ===========================================================================
# Nagini carrier shim: PSeq / ToSeq (mapping.md §2, row 2).
# ===========================================================================

class PSeq:
    """Immutable pure sequence — nagini's `PSeq`."""

    def __init__(self, *items):
        self._t = tuple(items)

    def __class_getitem__(cls, item):     # so `PSeq[int]` annotations parse
        return cls

    @classmethod
    def _wrap(cls, t):
        s = cls()
        s._t = tuple(t)
        return s

    def take(self, n):
        return PSeq._wrap(self._t[:n])

    def drop(self, n):
        return PSeq._wrap(self._t[n:])

    def __len__(self):
        return len(self._t)

    def __getitem__(self, i):
        return self._t[i]

    def __add__(self, other):
        return PSeq._wrap(self._t + other._t)

    def __eq__(self, other):
        return isinstance(other, PSeq) and self._t == other._t

    def __hash__(self):
        return hash(self._t)


def ToSeq(lst):
    return PSeq._wrap(lst)


# ===========================================================================
# SHADOW.  model.py's `# pure-start`/`# pure-end` region and its
# `# impl-start`/`# impl-end` region, copied VERBATIM minus contract calls.
# Verbatim-ness is machine-checked by _check_shadow_verbatim() below.
# ===========================================================================

# --- pure region (dependencies of the impl / of the postcondition) ---------

def axis_count(shape: PSeq[int], k: int) -> int:
    if k == 0:
        return 1
    return axis_count(shape, k - 1) * shape[k - 1]


def lemma_axis_count_unfold(shape: PSeq[int], k: int) -> bool:
    return True


# --- impl region ----------------------------------------------------------

def array_element_count(shape: List[int]) -> int:
    acc = 1
    i = 0
    while i < len(shape):
        acc = acc * shape[i]
        i = i + 1
    return acc


# ===========================================================================
# Verbatim check: this file's shadow vs the frozen model.py.
# ===========================================================================

_CONTRACT_CALLS = frozenset((
    "Requires", "Ensures", "Invariant", "Assert", "Fold", "Unfold",
    "Acc", "MustTerminate", "Exhale", "Inhale",
))
_SHADOW_FUNCS = ("axis_count", "lemma_axis_count_unfold", "array_element_count")


def _is_strippable(stmt):
    """True for a statement that is contract-only or a docstring."""
    if not isinstance(stmt, ast.Expr):
        return False
    val = stmt.value
    if isinstance(val, ast.Constant) and isinstance(val.value, str):
        return True                                    # docstring
    if isinstance(val, ast.Call) and isinstance(val.func, ast.Name):
        return val.func.id in _CONTRACT_CALLS          # Requires/Ensures/...
    return False


def _strip(node):
    """Drop docstrings/contract statements everywhere in a statement tree."""
    for field, value in ast.iter_fields(node):
        if isinstance(value, list):
            kept = [v for v in value
                    if not (isinstance(v, ast.stmt) and _is_strippable(v))]
            for v in kept:
                if isinstance(v, ast.AST):
                    _strip(v)
            setattr(node, field, kept)
        elif isinstance(value, ast.AST):
            _strip(value)
    return node


def _normalized_defs(source, names):
    """{name: ast.dump of the contract-stripped FunctionDef} for `names`."""
    out = {}
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.FunctionDef) and node.name in names:
            node.decorator_list = []          # @Pure has no runtime meaning
            out[node.name] = ast.dump(_strip(node))
    return out


def _check_shadow_verbatim():
    """Require this file's shadow to be the contract-stripped model.py region.

    Returns (ok, note).  A drifted shadow is a hard failure: a paraphrase would
    test the paraphrase, not the model.
    """
    model_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              "model.py")
    if not os.path.exists(model_path):
        return None, ("model.py not present next to the script; the verbatim "
                      "AST check could not run (differential still ran)")
    with open(model_path) as fh:
        model_src = fh.read()
    with open(os.path.abspath(__file__)) as fh:
        self_src = fh.read()
    want = _normalized_defs(model_src, _SHADOW_FUNCS)
    got = _normalized_defs(self_src, _SHADOW_FUNCS)
    missing = [n for n in _SHADOW_FUNCS if n not in want or n not in got]
    if missing:
        return False, "functions not found on both sides: %r" % (missing,)
    drifted = [n for n in _SHADOW_FUNCS if want[n] != got[n]]
    if drifted:
        return False, ("shadow is NOT the verbatim contract-stripped model.py "
                       "region; drifted: %r" % (drifted,))
    return True, ("shadow == contract-stripped model.py impl+pure region "
                  "(AST-identical for %s)" % ", ".join(_SHADOW_FUNCS))


# ===========================================================================
# ORACLE: the real patched ImmutableDenseNDimArray._new, called.
# ===========================================================================

def _assert_patched():
    """Refuse to run unless the gold patch is live in the imported source."""
    import inspect
    from sympy.tensor.array.dense_ndim_array import ImmutableDenseNDimArray
    src = inspect.getsource(ImmutableDenseNDimArray._new)
    post = "functools.reduce(lambda x,y: x*y, shape, 1)"
    pre = "functools.reduce(lambda x,y: x*y, shape) if shape else 0"
    if post not in src or pre in src:
        raise SystemExit(
            "G-CONF ERROR: the imported ImmutableDenseNDimArray._new is not "
            "the patched function (patched form present=%r, pre-patch form "
            "present=%r); refusing to certify against unpatched code."
            % (post in src, pre in src))


def oracle(cls, shape):
    """Drive the REAL patched `_new` on `shape` and read the value back.

    Returns (loop_size, len_or_None).  Raises BridgeError if the constructed
    array's shape is not the shape we asked for (then the input was never
    really tested and must not be scored as agreement).
    """
    arr = cls([], shape=tuple(shape))
    # --- bridge validation, every input, no exceptions ---
    got_shape = tuple(int(d) for d in arr.shape)
    if got_shape != tuple(shape):
        raise BridgeError("shape round-trip failed: asked %r got %r"
                          % (tuple(shape), got_shape))
    if int(arr._rank) != len(shape):
        raise BridgeError("rank round-trip failed: asked %d got %r"
                          % (len(shape), arr._rank))
    loop_size = int(arr._loop_size)
    via_len = None
    if 0 <= loop_size < _LEN_MAX:
        via_len = len(arr)          # NDimArray.__len__ -> self._loop_size
    return loop_size, via_len


class BridgeError(Exception):
    pass


# ===========================================================================
# Inputs.  Requires = Acc(list_pred(shape), 1/2) + MustTerminate(2): every
# List[int] qualifies, so nothing below is filtered out.
# ===========================================================================

def f2p_shapes(cls):
    """Shapes taken from the F2P test's own literal constructions.

    Built through the real constructor calls the test makes (mapping.md §1),
    then handed back as model-side shapes so the shadow is driven by exactly
    the inputs the FAIL_TO_PASS test exercises.
    """
    import sympy
    x = sympy.Symbol("x")
    reals = [
        cls(x),                                    # rank-0 scalar: the bug
        cls([], shape=(0,)),                       # genuine 0-element array
        cls([23]),                                 # -> 1
        cls(list(range(3 ** 4)), (3, 3, 3, 3)),    # -> 81
        cls(sympy.Integer(3)),                     # the issue's Array(3)
    ]
    return [[int(d) for d in a.shape] for a in reals]


def boundary_shapes():
    return [
        [],                       # rank 0: the empty product, the F2P case
        [0],                      # zero axis
        [1],                      # unit axis
        [2],
        [0, 0], [0, 1], [1, 0], [0, 5], [5, 0],
        [1, 1], [2, 3], [3, 2],
        [1, 1, 1], [2, 3, 4], [3, 3, 3, 3],
        [-1],                     # negative axis length: in Requires, no len()
        [-1, -1], [-1, 0], [0, -1], [-2, 3], [3, -2], [-1, -1, -1],
        [10 ** 6], [10 ** 6, 10 ** 6],       # product beyond any allocation
        [2 ** 62, 3],                        # beyond __len__'s index range
        [10 ** 18, -1],                      # huge and negative
        [1] * 30,                            # long shape, many iterations
        [2] * 20,
        [1] * 59,                            # near the recursion cap
    ]


_LATTICE_DIMS = (-2, -1, 0, 1, 2, 3)
_LATTICE_MAX_RANK = 5


def lattice_shapes():
    """EXHAUSTIVE over the finite sub-lattice rank 0..5 x {-2,-1,0,1,2,3}.

    9331 shapes: every rank, sign and zero-placement combination inside that
    box is checked, not sampled.  The full modeled domain (any List[int]) is
    infinite, so this is a complete sweep of a sub-box plus fuzz beyond it.
    """
    for rank in range(_LATTICE_MAX_RANK + 1):
        for shape in itertools.product(_LATTICE_DIMS, repeat=rank):
            yield list(shape)


# axis-length pools: small/unit/zero edges, negatives, and large magnitudes.
_SMALL = (0, 1, 1, 1, 2, 3, 4, 5, 7, 12, 64, 100)
_SIGNED = (-1, -1, -2, -3, -7, -100, 0, 1, 2, 3, 5)
_LARGE = (10 ** 6, 10 ** 9, 10 ** 12, 2 ** 40, 2 ** 62, 999983, -(10 ** 9))


def fuzz_shape(rng):
    """A random List[int]; every result satisfies the model's Requires."""
    klass = rng.random()
    if klass < 0.06:
        return []                                  # rank 0 stays well sampled
    if klass < 0.50:
        rank = rng.randint(1, 8)
        pool = _SMALL
    elif klass < 0.80:
        rank = rng.randint(1, 8)
        pool = _SIGNED                             # negative axis lengths
    elif klass < 0.92:
        rank = rng.randint(1, 4)                   # bounded: bigint products
        pool = _LARGE
    else:
        rank = rng.randint(9, 59)                  # long shapes, many steps
        pool = _SMALL
    return [rng.choice(pool) for _ in range(rank)]


# ===========================================================================

def main():
    verbatim_ok, verbatim_note = _check_shadow_verbatim()
    if verbatim_ok is False:
        print("G-CONF FAIL: %s" % verbatim_note)
        print(json.dumps({"status": "fail", "shadow_verbatim": False,
                          "detail": verbatim_note}))
        return 1
    if verbatim_ok is None:
        print("G-CONF NOTE: %s" % verbatim_note)
    else:
        print("G-CONF shadow provenance: %s" % verbatim_note)

    _assert_patched()
    from sympy.tensor.array.dense_ndim_array import ImmutableDenseNDimArray
    cls = ImmutableDenseNDimArray

    rng = random.Random(SEED)
    checked = 0
    branch_rank0 = 0            # while loop taken 0 times (the empty product)
    branch_loop = 0             # while loop taken >= 1 time
    len_crosschecks = 0
    disagreements = []

    def run(shape, tag):
        nonlocal checked, branch_rank0, branch_loop, len_crosschecks
        # --- shadow: the contract-stripped impl region, on the model carrier
        shadow_impl = array_element_count(list(shape))
        # --- shadow: the postcondition's own deep witness (mapping.md §2 r3)
        shadow_spec = axis_count(ToSeq(list(shape)), len(shape))
        # --- oracle: the real patched repo function, called
        try:
            real, real_len = oracle(cls, shape)
        except BridgeError as exc:
            disagreements.append((tag, list(shape), shadow_impl, shadow_spec,
                                  "BRIDGE: %s" % exc, None))
            return
        checked += 1
        if len(shape) == 0:
            branch_rank0 += 1
        else:
            branch_loop += 1
        if real_len is not None:
            len_crosschecks += 1
        bad = (shadow_impl != real or shadow_spec != real
               or (real_len is not None and real_len != real))
        if bad:
            disagreements.append((tag, list(shape), shadow_impl, shadow_spec,
                                  real, real_len))

    for shape in f2p_shapes(cls):
        run(shape, "f2p")
    for shape in boundary_shapes():
        run(shape, "boundary")
    lattice = 0
    for shape in lattice_shapes():
        run(shape, "lattice")
        lattice += 1
        if disagreements and len(disagreements) >= MAX_REPORTED:
            break
    fuzzed = 0
    while checked < N_TARGET and len(disagreements) < MAX_REPORTED:
        run(fuzz_shape(rng), "fuzz")
        fuzzed += 1

    if disagreements:
        print("G-CONF FAIL: %d disagreement(s) between the model.py impl "
              "shadow and the real patched ImmutableDenseNDimArray._new "
              "(dense_ndim_array.py:152) over %d inputs (seed=%d):"
              % (len(disagreements), checked, SEED))
        for tag, shape, s_impl, s_spec, real, real_len in disagreements:
            print("  [%s] shape=%r\n    shadow(impl region)=%r\n"
                  "    shadow(axis_count witness)=%r\n"
                  "    real(_loop_size)=%r\n    real(len)=%r"
                  % (tag, shape, s_impl, s_spec, real, real_len))
        print(json.dumps({"status": "fail", "checked": checked,
                          "disagreements": len(disagreements), "seed": SEED}))
        return 1

    print("G-CONF OK: the contract-stripped model.py impl region (and the "
          "postcondition's axis_count witness) agrees with the real patched "
          "ImmutableDenseNDimArray._new _loop_size on %d inputs "
          "(seed=%d): %d F2P/boundary, %d exhaustive lattice (rank<=%d x "
          "%r), %d fuzz; rank-0 branch %d, loop branch %d; %d len() "
          "cross-checks; 0 disagreements."
          % (checked, SEED, checked - lattice - fuzzed, lattice,
             _LATTICE_MAX_RANK, list(_LATTICE_DIMS), fuzzed,
             branch_rank0, branch_loop, len_crosschecks))
    print(json.dumps({
        "status": "pass",
        "checked": checked,
        "disagreements": 0,
        "seed": SEED,
        "shadow": "direct (contract-stripped impl region; AST-verified "
                  "verbatim against model.py)"
                  if verbatim_ok else
                  "direct (contract-stripped impl region; model.py absent, "
                  "AST verbatim check skipped)",
        "shadow_verbatim": bool(verbatim_ok),
        "oracle": "sympy.tensor.array.dense_ndim_array."
                  "ImmutableDenseNDimArray._new (called, patched)",
        "exhaustive_sublattice": lattice,
        "fuzz": fuzzed,
        "branch_rank0": branch_rank0,
        "branch_loop": branch_loop,
        "len_crosschecks": len_crosschecks,
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
