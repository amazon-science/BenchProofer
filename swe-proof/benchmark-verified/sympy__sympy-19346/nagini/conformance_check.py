#!/usr/bin/env python3
"""G-CONF differential conformance check for sympy__sympy-19346 (nagini).

SHADOW: the impl regions of model.py (`render_collection_codepoints`,
`render_mapping_codepoints`), copied verbatim below with the contract calls
(Requires/Ensures/Invariant/Assert) stripped and PSeq realized as an immutable
tuple shim (ToSeq becomes a list->PSeq lift). The only callee the impl invokes
is the @ContractOnly `doprint_elem`, which per the contract calls the REAL
repo routine: `ReprPrinter().doprint(elem)` on the real element bound to the
token (mapping.md section 3.1). The @Pure helpers (`joined_elems`,
`set_seq`, ...) appear only inside contracts, so nothing else needs a shim.

ORACLE: the REAL patched repo functions the model models per mapping.md —
`sympy.printing.repr.ReprPrinter._print_set` and `._print_dict`. The gate
applies the patch to /testbed before this script runs; PYTHONPATH=/testbed
makes the patched module importable. This script does NOT apply any patch.

Type bridge (mapping.md section 2):
  * a rendering `str` <-> List[int] of Unicode code points
    (out[k] == ord(s[k]); list `+` <-> str concatenation);
  * one `set` of elements <-> List[int] of element tokens. A Python set is
    unordered, so the bridge builds the real set first, reads its actual
    iteration order, and binds token j to the j-th member in that order (the
    same object the oracle will iterate — iteration order of an unmutated set
    object is stable within a process);
  * one `dict` <-> flat even-length List[int] of alternating key,value tokens
    in items() order (dicts preserve insertion order).
  Tokens are consecutive ints >= 0 indexing a per-call element table, which
  realizes the documented token <-> element bijection exactly.

Input domain: `render_collection_codepoints` Requires only a readable token
list; `render_mapping_codepoints` additionally Requires even length — both
hold by construction (the flat carrier gets one key token and one value token
per pair). Elements are drawn from a pool of real sympy objects spanning the
classes axiom_check.py exercises: symbols (incl. an empty-name and an
assumptions-carrying one), integers/rationals/floats, the constant/singleton/
boolean/None class, and composite hashables; dict values additionally include
unhashable containers (a plain dict/list) to exercise recursive dispatch.

>= 1e5 Requires-satisfying inputs: boundary cases + 50000 collection +
50000 mapping fuzz inputs. Pinned fuzz seed: 19346.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib + the repo's public API only.
"""
import json
import random
import sys

SEED = 19346
N_FUZZ_SET = 50_000
N_FUZZ_DICT = 50_000

# Literal punctuation code points (copied from model.py's module constants).
LBRACE = 123   # "{"
RBRACE = 125   # "}"
COMMA = 44     # ","
SPACE = 32     # " "
COLON = 58     # ":"


# --- PSeq shim: immutable sequence with the operations the impl uses ---------

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


def ToSeq(lst):
    return PSeq._wrap(lst)


# --- @ContractOnly callee: calls the REAL repo routine ------------------------
# Per-call element table: token t <-> _ELEMS[t] (real sympy object). The real
# recursive representation routine is ReprPrinter().doprint (the unchanged
# callee the modeled methods invoke per element); results for the fixed pool
# objects are memoized by identity — each distinct element still goes through
# the real routine.

_ELEMS = []          # set per check-call by the bridge
_PRINTER = None      # ReprPrinter instance, set in main()
_DOPRINT_CACHE = {}  # id(elem) -> code-point list


def doprint_elem(t):
    elem = _ELEMS[t]
    key = id(elem)
    got = _DOPRINT_CACHE.get(key)
    if got is None:
        got = [ord(ch) for ch in _PRINTER.doprint(elem)]
        _DOPRINT_CACHE[key] = got
    return list(got)


# --- the impl regions of model.py, verbatim, contract calls stripped ----------

def render_collection_codepoints(elems):
    # impl-start
    elems_s = ToSeq(elems)  # type: PSeq
    if len(elems) == 0:
        out_empty = [115, 101, 116, 40, 41]  # "set()"
        return out_empty
    inner = []
    i = len(elems)
    while i > 0:
        elt = elems[i - 1]
        piece = doprint_elem(elt)
        if i == len(elems):
            inner = piece
        else:
            inner = piece + [COMMA, SPACE] + inner
        i = i - 1
    result = [LBRACE] + inner + [RBRACE]
    return result
    # impl-end


def render_mapping_codepoints(flat):
    # impl-start
    flat_s = ToSeq(flat)  # type: PSeq
    if len(flat) == 0:
        out_empty = [LBRACE, RBRACE]  # "{}"
        return out_empty
    inner = []
    i = len(flat)
    while i > 0:
        key = flat[i - 2]
        val = flat[i - 1]
        piece = doprint_elem(key) + [COLON, SPACE] + doprint_elem(val)
        if i == len(flat):
            inner = piece
        else:
            inner = piece + [COMMA, SPACE] + inner
        i = i - 2
    result = [LBRACE] + inner + [RBRACE]
    return result
    # impl-end


# --- bridge + differential checks ---------------------------------------------

def _decode(codepoints):
    return "".join(chr(c) for c in codepoints)


def check_set(rp, elems):
    """One collection input: bind tokens to the real set's members in its real
    iteration order, run shadow and oracle, return an error string on
    disagreement, else None."""
    global _ELEMS
    real_set = set(elems)
    _ELEMS = list(real_set)          # token j <-> j-th member, iteration order
    tokens = list(range(len(_ELEMS)))

    shadow = _decode(render_collection_codepoints(tokens))
    real = rp._print_set(real_set)   # REAL patched repo function

    if shadow != real:
        return ("DISAGREEMENT (collection)\n  members=%r\n  shadow=%r\n"
                "  real=%r" % (_ELEMS, shadow, real))
    return None


def check_dict(rp, pairs):
    """One mapping input: build the real dict, bind tokens to its items() keys
    and values (flat, alternating), run shadow and oracle, return an error
    string on disagreement, else None."""
    global _ELEMS
    d = dict(pairs)
    _ELEMS = []
    tokens = []
    for k, v in d.items():
        _ELEMS.append(k)
        tokens.append(len(_ELEMS) - 1)
        _ELEMS.append(v)
        tokens.append(len(_ELEMS) - 1)
    assert len(tokens) % 2 == 0      # Requires of the mapping renderer holds

    shadow = _decode(render_mapping_codepoints(tokens))
    real = rp._print_dict(d)         # REAL patched repo function

    if shadow != real:
        return ("DISAGREEMENT (mapping)\n  items=%r\n  shadow=%r\n  real=%r"
                % (list(d.items()), shadow, real))
    return None


def main():
    global _PRINTER
    from sympy import Symbol, Integer, Rational, Float, oo, zoo, nan, pi, E, I, S
    from sympy.printing.repr import ReprPrinter  # REAL patched repo class

    rp = ReprPrinter()
    if not (hasattr(rp, "_print_set") and hasattr(rp, "_print_dict")):
        print("oracle methods missing: the patched repo is not on PYTHONPATH")
        return 1
    _PRINTER = ReprPrinter()  # separate instance backs the callee shim

    x, y, z = Symbol('x'), Symbol('y'), Symbol('z')
    # hashable pool: usable as set members and dict keys
    hashable_pool = [
        x, y, z, Symbol('alpha'), Symbol(''), Symbol('x', positive=True),
        Integer(0), Integer(5), Integer(-3), Rational(1, 2), Rational(-7, 4),
        Float(1.5), oo, zoo, nan, pi, E, I, S.Infinity, S.NaN, S.EmptySet,
        True, False, None, x + y, x * y,
    ]
    # dict values may additionally be unhashable containers (recursive dispatch)
    value_pool = hashable_pool + [{x: y}, [x, Integer(1)], (y, z)]

    checked_set = checked_dict = 0

    # --- boundary cases -------------------------------------------------------
    set_boundaries = [
        [],                                  # empty collection
        [x], [Integer(5)], [Symbol('')],     # singletons
        [oo], [True], [None],                # constant/singleton class
        [x, y], [x, y, z],
        [Integer(1), Rational(1, 2), Symbol('w')],
        [oo, pi], [Symbol(''), x],
        hashable_pool,                       # the whole pool at once
    ]
    dict_boundaries = [
        [],                                  # empty mapping
        [(x, y)],
        [(x, y), (y, z)],
        [(x, {y: z})],                       # container value, recursive
        [(x, [y, Integer(2)])],
        [(Integer(1), x), (Integer(2), y)],
        [(oo, nan), (pi, E)],
        [(Symbol(''), x)],
        [(True, False), (None, oo)],
        list(zip(hashable_pool, reversed(hashable_pool))),
    ]
    for elems in set_boundaries:
        err = check_set(rp, elems)
        if err:
            print(err)
            return 1
        checked_set += 1
    for pairs in dict_boundaries:
        err = check_dict(rp, pairs)
        if err:
            print(err)
            return 1
        checked_dict += 1

    # --- randomized fuzz (pinned seed) ---------------------------------------
    rng = random.Random(SEED)
    for _ in range(N_FUZZ_SET):
        k = rng.randint(0, 6)
        elems = rng.sample(hashable_pool, min(k, len(hashable_pool)))
        err = check_set(rp, elems)
        if err:
            print(err)
            return 1
        checked_set += 1
    for _ in range(N_FUZZ_DICT):
        k = rng.randint(0, 6)
        keys = rng.sample(hashable_pool, min(k, len(hashable_pool)))
        vals = [rng.choice(value_pool) for _ in keys]
        err = check_dict(rp, list(zip(keys, vals)))
        if err:
            print(err)
            return 1
        checked_dict += 1

    total = checked_set + checked_dict
    print("G-CONF OK: shadow impl == real repo renderers on %d inputs "
          "(%d collection + %d mapping; boundary + fuzz, seed %d)."
          % (total, checked_set, checked_dict, SEED))
    print(json.dumps({"checked": total, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl regions; "
                                "doprint_elem calls the real doprint)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
