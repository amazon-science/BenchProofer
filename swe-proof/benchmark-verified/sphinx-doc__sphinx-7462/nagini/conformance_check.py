#!/usr/bin/env python3
"""G-CONF differential conformance check for sphinx-doc__sphinx-7462 (nagini).

SHADOW: the impl regions of model.py (`tuple_tokens`, `tuple_text`), copied
verbatim below with the contract calls stripped and PSeq realized as an
immutable tuple shim. The @Pure helpers (`sep_token`, `open_paren`,
`close_paren`, `join_tokens`, `join_comma`) copy over as plain functions.
There are no @ContractOnly callees in this bundle.

ORACLES (the REAL patched repo functions the model models, per mapping.md;
the gate applies patch.diff to /testbed before this script runs and
PYTHONPATH=/testbed makes the patched modules importable):

  * site A (token surface): the `ast.Tuple` branch of the nested `unparse`
    inside `sphinx.domains.python._parse_annotation`. The branch is reached
    by handing `_parse_annotation` a bare tuple expression source ("()",
    "a,", "a, b", ...); the observation is the sequence of display-node
    texts (`node.astext()`), which is exactly the model's carrier.
  * site B (text surface): the `ast.Tuple` branch of the module-level
    `sphinx.pycode.ast.unparse`, called on a parsed `ast.Tuple` node; the
    observation is the returned string.

Type bridge (mapping.md section 2): a member's rendered text / a display
token's text maps to PSeq[int] of Unicode code points; the member list maps
to PSeq[PSeq[int]]. Member renderings are unchanged upstream computations
taken as already-rendered inputs, so the shadow's members come from the REAL
upstream renderers: site A members are rendered individually through
`_parse_annotation` (each chosen member form renders as exactly one display
node, asserted); site B members are rendered by the real `unparse(e)` on
each element.

Input domain: the model has no precondition — a group may have zero or more
members. Boundary cases cover the empty group (both surfaces, plus the empty
group nested as a subscript argument on the token surface), the one-member
group, and members containing the separator characters; fuzz draws 0-6
members per group (site A: identifiers / dotted names, the forms the token
renderer maps to a single display node; site B: identifiers, dotted names,
numeric and string literals, list displays and nested empty groups).

>= 1e5 Requires-satisfying inputs: boundary cases + 60000 fuzz groups per
surface (120000+ total). Pinned fuzz seed: 7462.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only.
"""
import ast as pyast
import json
import keyword
import random
import string
import sys

SEED = 7462
N_FUZZ_PER_SITE = 60_000


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

    def __repr__(self):
        return "PSeq%r" % (self._t,)


# --- pure helpers from model.py, contracts/decorators stripped ---------------

def sep_token():
    # the single separator token ', ' (code points 44, 32)
    return PSeq(44, 32)


def open_paren():
    # the opening round-bracket symbol '(' (code point 40)
    return PSeq(40)


def close_paren():
    # the closing round-bracket symbol ')' (code point 41)
    return PSeq(41)


def join_tokens(parts):
    if len(parts) == 0:
        return PSeq(open_paren()).take(0)
    if len(parts) == 1:
        return PSeq(parts[0])
    return (PSeq(parts[0]) + PSeq(sep_token())) + join_tokens(parts.drop(1))


def join_comma(parts):
    if len(parts) == 0:
        return PSeq(0).take(0)
    if len(parts) == 1:
        return parts[0]
    return (parts[0] + sep_token()) + join_comma(parts.drop(1))


# --- the impl regions of model.py, verbatim, contract calls stripped ---------

def tuple_tokens(elts):
    if len(elts) > 0:
        result = join_tokens(elts)  # type: PSeq
    else:
        result = PSeq(open_paren(), close_paren())
    return result


def tuple_text(elts):
    if len(elts) > 0:
        result = join_comma(elts)  # type: PSeq
    else:
        result = PSeq(40, 41)
    return result


# --- bridge: str <-> PSeq[int], member list <-> PSeq[PSeq[int]] --------------

def cps(s):
    return PSeq(*[ord(ch) for ch in s])


def pseq_str(p):
    return "".join(chr(p[i]) for i in range(len(p)))


def toks_strs(toks):
    return [pseq_str(toks[i]) for i in range(len(toks))]


def members_pseq(member_strs):
    return PSeq(*[cps(m) for m in member_strs])


# --- oracle drivers -----------------------------------------------------------

def tuple_source(member_srcs):
    """A source string whose top-level parse is a tuple display with exactly
    the given element sources (trailing comma for the 1-element form)."""
    if len(member_srcs) == 0:
        return "()"
    if len(member_srcs) == 1:
        return member_srcs[0] + ","
    return ", ".join(member_srcs)


def real_tokens_a(parse_annotation, src):
    """Site A oracle: the display-node texts _parse_annotation yields."""
    return [n.astext() for n in parse_annotation(src)]


def check_site_a(parse_annotation, member_srcs, rendered_cache):
    """One site-A group: shadow tuple_tokens on the already-rendered members
    vs the real token surface on the whole group source."""
    rendered = []
    for m in member_srcs:
        if m not in rendered_cache:
            toks = real_tokens_a(parse_annotation, m)
            # the chosen member forms each render as exactly one display node
            assert len(toks) == 1, (m, toks)
            rendered_cache[m] = toks[0]
        rendered.append(rendered_cache[m])

    shadow = toks_strs(tuple_tokens(members_pseq(rendered)))
    src = tuple_source(member_srcs)
    real = real_tokens_a(parse_annotation, src)
    if shadow != real:
        return ("DISAGREEMENT (token surface)\n  members=%r\n  src=%r\n"
                "  shadow=%r\n  real=%r" % (member_srcs, src, shadow, real))
    return None


def check_site_b(unparse, member_srcs):
    """One site-B group: shadow tuple_text on the already-rendered members vs
    the real text surface on the parsed tuple node."""
    src = tuple_source(member_srcs)
    node = pyast.parse(src, mode="eval").body
    assert isinstance(node, pyast.Tuple), (src, node)
    assert len(node.elts) == len(member_srcs)
    # members: unchanged upstream renderings by the REAL repo function
    rendered = [unparse(e) for e in node.elts]

    shadow = pseq_str(tuple_text(members_pseq(rendered)))
    real = unparse(node)
    if shadow != real:
        return ("DISAGREEMENT (text surface)\n  members=%r\n  src=%r\n"
                "  shadow=%r\n  real=%r" % (member_srcs, src, shadow, real))
    return None


# --- input generation -----------------------------------------------------------

IDENT_FIRST = string.ascii_letters + "_"
IDENT_REST = string.ascii_letters + string.digits + "_"


def rand_ident(rng):
    while True:
        s = rng.choice(IDENT_FIRST) + "".join(
            rng.choice(IDENT_REST) for _ in range(rng.randint(0, 6)))
        if not keyword.iskeyword(s):
            return s


def rand_member_a(rng):
    """Site-A member: identifier or dotted name (forms the token renderer
    maps to a single display node)."""
    return ".".join(rand_ident(rng) for _ in range(rng.randint(1, 3)))


def rand_member_b(rng):
    """Site-B member: any element form the text renderer supports."""
    k = rng.random()
    if k < 0.45:
        return rand_member_a(rng)
    if k < 0.65:
        return str(rng.randint(0, 10 ** rng.randint(1, 6)))
    if k < 0.80:
        inner = "".join(rng.choice("ab, ()[]xyZ0") for _ in range(rng.randint(0, 6)))
        return repr(inner)
    if k < 0.92:
        return "[" + ", ".join(rand_ident(rng)
                               for _ in range(rng.randint(1, 3))) + "]"
    return "()"   # a nested empty group as a member


def boundary_members_a():
    return [
        [],                                   # the empty group
        ["a"],                                # one member
        ["int", "int"],                       # two identical members
        ["a", "b", "c"],
        ["os.path", "x"],                     # dotted-name members
        ["a_b", "C0", "_z", "q.r.s"],
        ["x"] * 8,                            # many members
        ["A" * 30, "b"],                      # a long member
    ]


def boundary_members_b():
    return [
        [],                                   # the empty group
        ["a"],
        ["1", "2", "3"],
        ["int", "int"],
        ["''"],                               # an empty-string member
        ["'x, y'", "z"],                      # ', ' inside a member
        ["()", "a"],                          # nested empty group member
        ["[a, b]", "c"],
        ["os.path", "0"],
        ["x"] * 8,
    ]


def main():
    # REAL patched repo callees (mapping.md section 1)
    from sphinx.domains.python import _parse_annotation
    from sphinx.pycode.ast import unparse as pycode_unparse

    checked = 0
    rendered_cache = {}

    def run(err):
        nonlocal checked
        if err:
            print(err)
            sys.exit(1)
        checked += 1

    # --- boundary groups ---------------------------------------------------
    for ms in boundary_members_a():
        run(check_site_a(_parse_annotation, ms, rendered_cache))
    for ms in boundary_members_b():
        run(check_site_b(pycode_unparse, ms))

    # the empty group nested as a subscript argument (token surface): the
    # group's rendering embeds unchanged between the surrounding tokens
    real = real_tokens_a(_parse_annotation, "Tuple[()]")
    shadow_inner = toks_strs(tuple_tokens(members_pseq([])))
    if real != ["Tuple", "["] + shadow_inner + ["]"]:
        print("DISAGREEMENT (token surface, nested empty group)\n"
              "  src='Tuple[()]'\n  shadow inner=%r\n  real=%r"
              % (shadow_inner, real))
        return 1
    checked += 1

    # --- randomized fuzz, pinned seed ----------------------------------------
    rng = random.Random(SEED)
    for _ in range(N_FUZZ_PER_SITE):
        n = rng.randint(0, 6)
        run(check_site_a(_parse_annotation,
                         [rand_member_a(rng) for _ in range(n)],
                         rendered_cache))
    for _ in range(N_FUZZ_PER_SITE):
        n = rng.randint(0, 6)
        run(check_site_b(pycode_unparse,
                         [rand_member_b(rng) for _ in range(n)]))

    print("G-CONF OK: shadow impl == real renderers on %d groups "
          "(%d boundary + 2x%d fuzz, seed %d)."
          % (checked,
             len(boundary_members_a()) + len(boundary_members_b()) + 1,
             N_FUZZ_PER_SITE, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
