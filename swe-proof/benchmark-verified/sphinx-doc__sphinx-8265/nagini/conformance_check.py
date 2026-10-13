#!/usr/bin/env python3
"""G-CONF differential conformance check for sphinx-doc__sphinx-8265 (nagini).

SHADOW: the impl regions of model.py (`tuple_render`, `subscript_render`),
copied verbatim below with the contract calls stripped, plus the @Pure helper
`join_comma` copied as a plain function.  PSeq is realized as an immutable
tuple shim.  There are no @ContractOnly callees in this bundle.

ORACLE: the REAL patched repo renderers the model models per mapping.md —
the two source-rendering methods of the expression unparser in
`sphinx.pycode.ast` (the gate applies patch.diff to /testbed before this
script runs; PYTHONPATH=/testbed makes the patched module importable).

Type bridge (mapping.md section 2): every rendered fragment is a `str` in the
repo and a code-point sequence (`PSeq[int]`) in the model; a list of rendered
members is `PSeq[PSeq[int]]`.  The model takes the members / base / general
index body as ALREADY-RENDERED inputs because the per-node rendering
recursion is unchanged upstream of the modeled assembly — so the harness
derives those inputs by running the SAME upstream recursion (the real
visitor's dispatch on each child node) and lifting the resulting strings to
code points.  The boolean `index_is_member_group` flag bridges to the repo's
predicate on the index node: it is a non-empty tuple node none of whose
members is a spread/unpacking element.  (This runtime is Python 3.9, where
an index expression is attached to the subscript node directly; the
legacy wrapper node for indices cannot even be constructed here — its
constructor returns the wrapped value — so that historical variant collapses
into the direct case, exactly as the single flag abstracts.)

Input domain: expression nodes built from a pool of pre-parsed atomic
renderable expressions (names, numbers, strings, attributes, calls, lists,
nested groups, nested indexings).  Members containing spread/unpacking
elements and slice-colon syntax are excluded: the former makes the index
non-simple with an upstream rendering this cut-down unparser does not
support, and the latter is likewise unsupported upstream — in both cases the
already-rendered inputs the model Requires simply do not exist.  The one
precondition, `Implies(index_is_member_group, len(elts) > 0)`, holds by
construction (the flag is only set for a non-empty member group).

>= 1e5 Requires-satisfying inputs: boundary cases + 50000 fuzz tuples +
55000 fuzz subscripts.  Pinned fuzz seed: 8265.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1.  stdlib only.
"""
import json
import random
import sys

SEED = 8265
N_FUZZ_TUPLE = 50_000
N_FUZZ_SUBSCRIPT = 55_000


# --- PSeq shim: immutable sequence, the operations the impl region uses ------

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


# --- @Pure helper from model.py, contracts stripped ---------------------------

def join_comma(parts):
    if len(parts) == 0:
        return PSeq(0).take(0)
    if len(parts) == 1:
        return parts[0]
    return (parts[0] + PSeq(44, 32)) + join_comma(parts.drop(1))


# --- the impl regions of model.py, verbatim, contract calls stripped ----------

def tuple_render(elts):
    if len(elts) > 0:
        body = join_comma(elts)  # type: PSeq[int]
        result = (PSeq(40) + body) + PSeq(41)  # type: PSeq[int]
    else:
        result = PSeq(40, 41)
    return result


def subscript_render(value, elts, index_is_member_group, slice_rendered):
    if index_is_member_group:
        body = join_comma(elts)
    else:
        body = slice_rendered
    result = ((value + PSeq(91)) + body) + PSeq(93)  # type: PSeq[int]
    return result


# --- bridge: str <-> PSeq[int] of code points ---------------------------------

def cps(s):
    return PSeq._wrap(ord(ch) for ch in s)


def pseq_to_str(m):
    return "".join(chr(c) for c in m._t)


def main():
    # REAL patched module: the expression unparser and the ast module it
    # itself resolved (the builtin one on this runtime).
    import sphinx.pycode.ast as spa
    ast = spa.ast
    visitor = spa._UnparseVisitor()

    # pre-parsed pool of atomic renderable expressions (parsed once, nodes
    # are read-only under the visitor so they are safely reused as children)
    atom_srcs = [
        "a", "b", "x_1", "int", "str", "None", "True", "...",
        "0", "1", "2", "3", "42", "'s'", "1.5",
        "a.b", "f(x)", "g(a, b)", "[1, 2]", "[]",
        "T[a]", "List[int]", "(1, 2)", "(a, b, c)", "- x",
    ]
    atoms = {src: ast.parse(src, mode="eval").body for src in atom_srcs}

    def group_node(member_srcs):
        return ast.Tuple(elts=[atoms[s] for s in member_srcs], ctx=ast.Load())

    counters = {"checked": 0}

    def check_tuple(member_srcs):
        """One group case: real rendering of the group node vs the shadow fed
        the SAME upstream member renderings."""
        node = group_node(member_srcs)
        rendered_members = PSeq._wrap(cps(visitor.visit(e)) for e in node.elts)
        shadow = pseq_to_str(tuple_render(rendered_members))
        real = visitor.visit(node)
        if shadow != real:
            print("DISAGREEMENT (group)\n  members=%r\n  shadow=%r\n  real=%r"
                  % (member_srcs, shadow, real))
            return False
        counters["checked"] += 1
        return True

    def is_member_group(index_node):
        # bridge of the flag: non-empty tuple node, no spread/unpacking member
        return (isinstance(index_node, ast.Tuple) and bool(index_node.elts)
                and not any(isinstance(e, ast.Starred) for e in index_node.elts))

    def check_subscript(base_src, index_member_srcs, index_atom_src):
        """One indexing case: index is either a group of members
        (index_member_srcs) or a single atomic expression (index_atom_src)."""
        base_node = atoms[base_src]
        if index_member_srcs is not None:
            index_node = group_node(index_member_srcs)
        else:
            index_node = atoms[index_atom_src]
        node = ast.Subscript(value=base_node, slice=index_node, ctx=ast.Load())

        flag = is_member_group(index_node)
        value = cps(visitor.visit(base_node))          # upstream base rendering
        if flag:
            elts = PSeq._wrap(cps(visitor.visit(e)) for e in index_node.elts)
            slice_rendered = PSeq()                    # unused in this branch
        else:
            elts = PSeq()
            slice_rendered = cps(visitor.visit(index_node))  # upstream rendering
        shadow = pseq_to_str(subscript_render(value, elts, flag, slice_rendered))
        real = visitor.visit(node)
        if shadow != real:
            print("DISAGREEMENT (indexing)\n  base=%r index_members=%r "
                  "index_atom=%r flag=%r\n  shadow=%r\n  real=%r"
                  % (base_src, index_member_srcs, index_atom_src, flag,
                     shadow, real))
            return False
        counters["checked"] += 1
        return True

    # --- boundary cases --------------------------------------------------
    tuple_boundaries = [
        [],                        # empty group
        ["1"],                     # single member
        ["1", "2", "3"],
        ["int", "int"],
        ["g(a, b)"],               # a ', ' inside a member's own rendering
        ["(1, 2)", "3"],           # nested group member
        ["'s'", "None", "..."],
        ["a"] * 8,                 # long group
    ]
    for members in tuple_boundaries:
        if not check_tuple(members):
            return 1

    subscript_boundaries = [
        ("a", ["int", "int"], None),      # two-member group index
        ("a", ["1"], None),               # one-member group index
        ("a", ["1", "2", "3"], None),
        ("List[int]", ["a", "b"], None),  # already-subscripted base
        ("a", ["(1, 2)", "3"], None),     # nested group inside the index group
        ("a", [], None),                  # EMPTY tuple index: not a member
                                          # group -> rendered verbatim
        ("a", None, "1"),                 # plain expression index
        ("a", None, "a.b"),
        ("a", None, "T[a]"),              # index that is itself an indexing
        ("a", None, "(1, 2)"),            # note: parsing folds this into a
                                          # tuple node, so it IS a member group
        ("f(x)", None, "'s'"),
    ]
    for base, members, atom in subscript_boundaries:
        if not check_subscript(base, members, atom):
            return 1

    # --- randomized fuzz (pinned seed) -------------------------------------
    rng = random.Random(SEED)

    for _ in range(N_FUZZ_TUPLE):
        n = rng.randint(0, 6)
        members = [rng.choice(atom_srcs) for _ in range(n)]
        if not check_tuple(members):
            return 1

    for _ in range(N_FUZZ_SUBSCRIPT):
        base = rng.choice(atom_srcs)
        if rng.random() < 0.6:
            n = rng.randint(0, 6)   # n == 0 => empty tuple index (verbatim)
            members = [rng.choice(atom_srcs) for _ in range(n)]
            ok = check_subscript(base, members, None)
        else:
            ok = check_subscript(base, None, rng.choice(atom_srcs))
        if not ok:
            return 1

    checked = counters["checked"]
    print("G-CONF OK: shadow impl == real renderers on %d inputs "
          "(%d boundary + %d fuzz, seed %d)."
          % (checked,
             len(tuple_boundaries) + len(subscript_boundaries),
             N_FUZZ_TUPLE + N_FUZZ_SUBSCRIPT, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
