#!/usr/bin/env python3
"""G-CONF differential conformance check for sympy__sympy-23262 (nagini).

SHADOW: the impl region of model.py's `render_container`, copied verbatim
below with the contract calls (Requires/Ensures/Invariant/Assert) stripped and
PSeq realized as an immutable tuple shim. The @Pure helpers (lparen/rparen/
lbracket/rbracket/comma/sep and the spec-side left_delim/right_delim/joined/
rendered) copy over as plain functions. There are no @ContractOnly callees in
this bundle.

ORACLE: the REAL patched repo function the model models per mapping.md --
`sympy.utilities.lambdify._recursive_to_string`, exercised on its iterable
branch. The gate applies patch.diff to /testbed before this script runs;
PYTHONPATH=/testbed makes the patched module importable.

Type bridge (mapping.md section 2):
  * str <-> PSeq[int] of Unicode code points (ord/chr per position);
  * the element-fragment sequence <-> PSeq[PSeq[int]]. A plain `str` element
    passes through the real function's recursion unchanged (its non-container,
    non-symbolic passthrough), so calling the oracle on a flat container of
    strings makes the k-th already-rendered fragment exactly the k-th input
    string -- the model's "fragments taken as given" boundary, realized
    without touching the unchanged per-element machinery.
  * is_paren: bool <-> the container's dynamic kind: True <-> tuple
    (parenthesis kind), False <-> list (square-bracket kind). Other iterables
    raise in the repo and are outside the modeled domain, so none are
    generated.

Input domain: the Requires is only the termination obligation -- every finite
fragment sequence with either kind flag is in-domain. Generation covers the
0/1/2/n-element boundaries (the 1-element parenthesis case is the arity-
critical one) and fuzz over fragments of varied lengths and characters,
including empty fragments, separators/delimiters inside fragments, and
non-ASCII code points.

>= 1e5 Requires-satisfying inputs: boundary cases + 100000 fuzz containers
(each checked as both kinds where listed). Pinned fuzz seed: 23262.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only.
"""
import json
import random
import sys

SEED = 23262
N_FUZZ = 100_000


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


# --- pure helpers from model.py, contracts stripped ---------------------------

def lparen():
    return 40


def rparen():
    return 41


def lbracket():
    return 91


def rbracket():
    return 93


def comma():
    return 44


def sep():
    return PSeq(44, 32)


def left_delim(is_paren):
    if is_paren:
        return PSeq(lparen())
    return PSeq(lbracket())


def right_delim(is_paren):
    if is_paren:
        return PSeq(comma(), rparen())
    return PSeq(rbracket())


def joined(elems):
    if len(elems) == 0:
        return PSeq(0).take(0)
    if len(elems) == 1:
        return elems[0]
    return elems[0] + sep() + joined(elems.drop(1))


def rendered(elems, is_paren):
    return left_delim(is_paren) + joined(elems) + right_delim(is_paren)


# --- the impl region of model.py, verbatim, contract calls stripped -----------

def render_container(elems, is_paren):
    # left, right := the delimiter pair for the requested kind. The parenthesis
    # kind's closing delimiter carries the trailing comma.
    if is_paren:
        left = PSeq(lparen())  # type: PSeq
        right = PSeq(comma(), rparen())  # type: PSeq
    else:
        left = PSeq(lbracket())
        right = PSeq(rbracket())
    # body := the ", "-joined element list (front-recursive fold, built back to
    # front so each step unfolds `joined` once).
    body = PSeq(0).take(0)  # type: PSeq
    i = len(elems)
    while i > 0:
        if i == len(elems):
            # last element: a single-element tail, no trailing separator.
            body = elems[i - 1]
        else:
            # at least two elements remain, so `joined` unfolds once.
            body = elems[i - 1] + sep() + body
        i = i - 1
    result = left + body + right  # type: PSeq
    return result


# --- bridge: str <-> PSeq[int] of code points ---------------------------------

def to_pseq(s):
    return PSeq._wrap(ord(ch) for ch in s)

def elems_to_pseq(strs):
    return PSeq._wrap(to_pseq(s) for s in strs)

def pseq_to_str(m):
    return "".join(chr(m[i]) for i in range(len(m)))


def check_container(real_fn, element_strs, is_paren):
    """Run shadow and oracle on one fragment list + kind; return an error
    string on disagreement, else None."""
    shadow = pseq_to_str(render_container(elems_to_pseq(element_strs), is_paren))
    container = tuple(element_strs) if is_paren else list(element_strs)
    observed = real_fn(str, container)  # str: passthrough printer for str leaves
    if shadow != observed:
        return ("DISAGREEMENT\n  elements=%r\n  is_paren=%s\n  shadow=%r\n  real=%r"
                % (element_strs, is_paren, shadow, observed))
    return None


def boundary_lists():
    return [
        [],                    # empty container
        ["1"],                 # the arity-critical one-element case
        ["x"],
        [""],                  # a single empty fragment
        ["1", "2"],
        ["3", "2"],
        ["", ""],              # empty fragments still get the separator
        ["", "x", ""],
        ["a", "b", "c", "d", "e"],
        ["x + 1", "y - 2"],    # fragments containing spaces/operators
        ["(1, 2)", "[3]"],     # fragments that themselves look like literals
        [", ", ","],           # separator characters inside fragments
        ["α", "éz"],  # non-ASCII code points
    ]


def main():
    from sympy.utilities.lambdify import _recursive_to_string  # REAL patched callee

    checked = 0
    for strs in boundary_lists():
        for is_paren in (True, False):
            err = check_container(_recursive_to_string, strs, is_paren)
            if err:
                print(err)
                return 1
            checked += 1

    rng = random.Random(SEED)
    alphabet = "abcxyz0123456789 +-*/[](){}, "
    for k in range(N_FUZZ):
        n = rng.randint(0, 6)
        strs = []
        for _ in range(n):
            m = rng.randint(0, 8)
            if rng.random() < 0.03:
                # occasional non-ASCII fragment (code points up to 0x2FF)
                strs.append("".join(chr(rng.randint(33, 0x2FF)) for _ in range(m)))
            else:
                strs.append("".join(rng.choice(alphabet) for _ in range(m)))
        is_paren = bool(k % 2)
        err = check_container(_recursive_to_string, strs, is_paren)
        if err:
            print(err)
            return 1
        checked += 1

    print("G-CONF OK: shadow impl == real serialiser on %d inputs "
          "(%d boundary + %d fuzz, seed %d)."
          % (checked, 2 * len(boundary_lists()), N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
