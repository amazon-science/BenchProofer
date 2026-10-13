#!/usr/bin/env python3
"""G-CONF differential conformance check for sympy__sympy-19954 (nagini).

SHADOW: the impl region of model.py (`prune_parallel`), copied VERBATIM below
with the contract statement lines (Requires/Ensures/Invariant/Assert) stripped
— the model IS Python, no transliteration. The impl region operates on plain
lists only; the @Pure helpers `kept` / `filtered` copy over as plain functions
on an immutable PSeq tuple shim and serve as a secondary cross-check (the
shadow's outputs must also equal the spec's own pure-region filter, exactly as
the postconditions state). There is NO @ContractOnly callee in this bundle
(mapping.md section 3), so nothing needs a real-callee bridge.

ORACLE: the REAL patched repo code the model models per mapping.md section 1 —
the pruning of the three parallel candidate lists inside
`PermutationGroup.minimal_blocks` (sympy/combinatorics/perm_groups.py). The
gate applies patch.diff to /testbed before this script runs (this script does
NOT apply it); PYTHONPATH=/testbed makes the patched module importable.
Because the modeled behaviour is an inline block of a larger method rather
than a standalone function, the oracle is obtained by locating that exact
block in the patched method's AST — the consecutive rebuild assignments that
filter each of the three parallel lists by one shared per-position boolean
mask — and executing the REAL statement objects (the repo's own code, byte
for byte, not a transliteration) over controlled bindings of the names they
read (the three parallel lists and the mask).

An end-to-end grounding leg additionally drives public entry points whose
computation runs the modeled prune with two or more flagged positions in one
scan, confirming the patched repo completes and returns a valid subgroup
(pre-patch this input class crashed inside the prune).

TYPE BRIDGE (mapping.md section 2): each candidate descriptor is an opaque
identity — the prune observes only identity and position, never content. The
shadow carries the identity directly as an int; the oracle side carries
REAL-shaped repo values (a list for a partition entry, a tuple for a
numbering entry, a set for a representative entry), each tagged with the same
identity, and oracle outputs are projected back to identities for comparison.
Distinct identity ranges per list make any cross-list mix-up or
desynchronisation visible. The removal decision is a plain list[bool], one
flag per position (the Requires: all four lists equal length).

INPUT DOMAIN: Requires demand only len(blocks) == len(nums) == len(reps)
== len(flag); every boolean assignment of the flag is admitted. Generation
covers the empty case, ALL masks exhaustively for lengths 0..11 (4095 cases
— includes every multi-flag pattern, the class the spec discriminates on),
and randomized lengths 0..16 with varying flag densities.

>= 1e5 Requires-satisfying inputs: 4096 exhaustive boundary + 100000 fuzz.
Pinned fuzz seed: 19954.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib + sympy (the repo under test) only.
"""
import ast
import inspect
import random
import sys
import textwrap

SEED = 19954
N_FUZZ = 100_000


# --- PSeq shim: immutable sequence, the operations the pure region uses ------

class PSeq:
    __slots__ = ("_t",)

    def __init__(self, *items):
        self._t = tuple(items)

    @classmethod
    def _wrap(cls, t):
        s = cls()
        s._t = tuple(t)
        return s

    def take(self, n):
        return PSeq._wrap(self._t[:n])

    def drop(self, n):
        return PSeq._wrap(self._t[n:])

    def __add__(self, other):
        return PSeq._wrap(self._t + other._t)

    def __len__(self):
        return len(self._t)

    def __getitem__(self, i):
        return self._t[i]

    def __eq__(self, other):
        return isinstance(other, PSeq) and self._t == other._t

    def __hash__(self):
        return hash(self._t)


def ToSeq(xs):
    return PSeq._wrap(xs)


# --- pure helpers from model.py, contracts stripped ---------------------------

def kept(flag):
    """Number of positions that SURVIVE pruning: the count of False flags.
    Front-recursive so one unfold is available per loop step."""
    if len(flag) == 0:
        return 0
    return (0 if flag[0] else 1) + kept(flag.drop(1))


def filtered(xs, flag):
    """Prune `xs` by the per-position flag: keep `xs[i]` iff `flag[i]` is False,
    survivors in original order. Front-recursive (single auto-unfold per step).
    The whole pruning behaviour is this function applied with ONE shared flag to
    every parallel list."""
    if len(xs) == 0:
        return PSeq(0).take(0)
    if flag[0]:
        return filtered(xs.drop(1), flag.drop(1))
    return PSeq(xs[0]) + filtered(xs.drop(1), flag.drop(1))


# --- the impl region of model.py, verbatim, contract calls stripped -----------

def prune_parallel(blocks, nums, reps, flag):
    out_blocks = []  # type: list
    out_nums = []  # type: list
    out_reps = []  # type: list
    i = len(flag)
    while i > 0:
        b = blocks[i - 1]
        n = nums[i - 1]
        r = reps[i - 1]
        f = flag[i - 1]
        # the (i-1)-th position is the head of the suffix beginning at i-1;
        # dropping it leaves the suffix beginning at i.
        if f:
            # flagged for removal at this position: drop it from every list.
            out_blocks = out_blocks
            out_nums = out_nums
            out_reps = out_reps
        else:
            out_blocks = [b] + out_blocks
            out_nums = [n] + out_nums
            out_reps = [r] + out_reps
        i = i - 1
    res = (out_blocks, out_nums, out_reps)
    return res


# --- oracle extraction: the real prune statements from the patched repo -------

def extract_prune_code():
    """Locate, inside the patched `PermutationGroup.minimal_blocks`, the run of
    three consecutive assignments that each rebuild one parallel list by
    filtering it with the SAME shared per-position boolean mask (an
    enumerate-driven comprehension guarded by the negated mask entry). Returns
    (compiled code object of the three REAL statements, [list names], mask
    name). Fails loudly if the patched method does not contain exactly one
    such three-statement block."""
    from sympy.combinatorics.perm_groups import PermutationGroup
    src = textwrap.dedent(inspect.getsource(PermutationGroup.minimal_blocks))
    tree = ast.parse(src)

    def mask_filter_assign(node):
        # <name> = [<v> for <i>, <v> in enumerate(<name>) if not <mask>[<i>]]
        if not (isinstance(node, ast.Assign) and len(node.targets) == 1
                and isinstance(node.targets[0], ast.Name)
                and isinstance(node.value, ast.ListComp)
                and len(node.value.generators) == 1):
            return None
        gen = node.value.generators[0]
        if not (isinstance(gen.iter, ast.Call)
                and isinstance(gen.iter.func, ast.Name)
                and gen.iter.func.id == "enumerate"
                and len(gen.iter.args) == 1
                and isinstance(gen.iter.args[0], ast.Name)
                and gen.iter.args[0].id == node.targets[0].id
                and len(gen.ifs) == 1):
            return None
        test = gen.ifs[0]
        if not (isinstance(test, ast.UnaryOp) and isinstance(test.op, ast.Not)
                and isinstance(test.operand, ast.Subscript)
                and isinstance(test.operand.value, ast.Name)):
            return None
        return (node.targets[0].id, test.operand.value.id)

    found = []
    for parent in ast.walk(tree):
        body = getattr(parent, "body", None)
        if not isinstance(body, list):
            continue
        for k in range(len(body) - 2):
            infos = [mask_filter_assign(body[k + j]) for j in range(3)]
            if all(infos) and len({m for _, m in infos}) == 1 \
                    and len({t for t, _ in infos}) == 3:
                found.append((body[k:k + 3], [t for t, _ in infos],
                              infos[0][1]))
    if len(found) != 1:
        raise RuntimeError(
            "expected exactly one shared-mask three-list rebuild block in the "
            "patched method, found %d" % len(found))
    stmts, list_names, mask_name = found[0]
    module = ast.Module(body=[ast.fix_missing_locations(s) for s in stmts],
                        type_ignores=[])
    code = compile(ast.fix_missing_locations(module), "<real-prune>", "exec")
    return code, list_names, mask_name


def oracle_prune(code, list_names, mask_name, blocks, nums, reps, mask):
    """Execute the REAL patched statements over controlled bindings and read
    back the three rebuilt lists."""
    ns = {"__builtins__": {"enumerate": enumerate},
          list_names[0]: list(blocks),
          list_names[1]: list(nums),
          list_names[2]: list(reps),
          mask_name: list(mask)}
    exec(code, ns)
    return ns[list_names[0]], ns[list_names[1]], ns[list_names[2]]


# --- input generation ----------------------------------------------------------

def repo_shaped(n):
    """Real-shaped repo values tagged with disjoint identity ranges: partition
    entries as lists, numbering entries as tuples, representative entries as
    sets (the shapes the real method's locals carry)."""
    blocks_o = [[100 + k, -1] for k in range(n)]
    nums_o = [(200 + k,) for k in range(n)]
    reps_o = [{300 + k} for k in range(n)]
    return blocks_o, nums_o, reps_o


def project(blocks_o, nums_o, reps_o):
    """Bridge: repo-shaped tagged values -> the opaque int identities the
    shadow carries."""
    return ([b[0] for b in blocks_o], [t[0] for t in nums_o],
            [next(iter(s)) for s in reps_o])


def gen_cases(rng):
    # exhaustive over every mask of length 0..11 (all multi-flag patterns)
    for n in range(0, 12):
        for bits in range(1 << n):
            yield n, [bool((bits >> k) & 1) for k in range(n)]
    # randomized fuzz: lengths 0..16, varying flag densities
    for _ in range(N_FUZZ):
        n = rng.randint(0, 16)
        p = rng.choice((0.1, 0.3, 0.5, 0.8))
        yield n, [rng.random() < p for _ in range(n)]


def check_case(code, list_names, mask_name, n, mask):
    blocks_o, nums_o, reps_o = repo_shaped(n)
    blocks_i, nums_i, reps_i = project(blocks_o, nums_o, reps_o)

    shadow = prune_parallel(blocks_i, nums_i, reps_i, mask)

    rb, rn, rr = oracle_prune(code, list_names, mask_name,
                              blocks_o, nums_o, reps_o, mask)
    real = project(rb, rn, rr)

    if (shadow[0], shadow[1], shadow[2]) != real:
        return ("DISAGREEMENT\n  n=%d mask=%r\n  shadow=%r\n  real=%r"
                % (n, mask, shadow, real))
    # alignment observable: all three real outputs equal-length
    if not (len(rb) == len(rn) == len(rr)):
        return ("ALIGNMENT BROKEN\n  n=%d mask=%r\n  real lens=%d,%d,%d"
                % (n, mask, len(rb), len(rn), len(rr)))
    # secondary cross-check against the spec's own pure region
    if (ToSeq(shadow[0]) != filtered(ToSeq(blocks_i), ToSeq(mask))
            or ToSeq(shadow[1]) != filtered(ToSeq(nums_i), ToSeq(mask))
            or ToSeq(shadow[2]) != filtered(ToSeq(reps_i), ToSeq(mask))
            or len(shadow[0]) != kept(ToSeq(mask))):
        return ("PURE-REGION MISMATCH\n  n=%d mask=%r\n  shadow=%r"
                % (n, mask, shadow))
    return None


def grounding_leg():
    """Drive public entry points whose computation runs the modeled prune with
    >= 2 flagged positions in one scan; the patched repo must complete and
    return a valid subgroup of the right order."""
    from sympy.combinatorics.named_groups import DihedralGroup
    for deg in (18, 50):
        G = DihedralGroup(deg)
        S = G.sylow_subgroup(p=2)
        if S is None or not G.order() % S.order() == 0:
            return "grounding: DihedralGroup(%d).sylow_subgroup(p=2) invalid" % deg
        if G.order() // S.order() % 2 == 0:
            return ("grounding: DihedralGroup(%d) 2-subgroup index not odd "
                    "(order %d in %d)" % (deg, S.order(), G.order()))
    return None


def main():
    code, list_names, mask_name = extract_prune_code()

    rng = random.Random(SEED)
    count = 0
    for n, mask in gen_cases(rng):
        err = check_case(code, list_names, mask_name, n, mask)
        if err:
            print(err)
            print("status=fail")
            return 1
        count += 1

    err = grounding_leg()
    if err:
        print(err)
        print("status=fail")
        return 1

    print("G-CONF OK: shadow of prune_parallel == the real patched prune "
          "statements on %d inputs (seed=%d), 0 disagreements; outputs stay "
          "index-aligned and match the pure-region filter; grounding entry "
          "points complete." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
