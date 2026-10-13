#!/usr/bin/env python3
"""G-CONF differential conformance check for sympy__sympy-22456 (nagini).

Refutes (does not prove) the R/I refinement leg: does the MODEL in `model.py`
actually agree with the REAL patched repository function it claims to model?

SHADOW — the impl region of `model.py` (its impl-start .. impl-end span), copied
VERBATIM below with only the contract calls deleted (`Requires`, `Ensures`,
`Invariant`, `Assert`, and the invariants-start/-end markers). Nothing is
restructured, renamed or simplified: the rebuild is still the same
element-by-element `while i < n` copy loop building `rebuilt_text` by list
concatenation and handing it to `Atomic(...)`. The `@Pure` helper the spec
region uses, `arg_count`, is copied over the same way (contracts stripped), and
so is the modelled carrier class `Atomic.__init__`. There are NO `@ContractOnly`
axioms in this bundle (model.py's axioms region records that the changed
operation is modelled DEEPLY), so there is no axiomatized callee to redirect to —
the whole impl region is directly executable and is executed here.

The Nagini carriers appear in this bundle only inside the contracts, so the
stripped impl region needs no `PSeq` for its own computation; the shim is still
provided because the OBSERVABLE the model specifies is stated over `PSeq[int]`
(`ToSeq(Result().text) == ToSeq(s.text)`, mapping.md §2), and this check
compares exactly that observable rather than a hand-rolled proxy.

ORACLE — the REAL patched repo function, CALLED, not transliterated:

    sympy.codegen.ast.String.func(*String.args)          (mapping.md §1)
      * `String`      — sympy/codegen/ast.py:872 @ base_commit
      * `Basic.args`  — sympy/core/basic.py:720
      * `func`        — post-fix `String.func` (gold hunk 4:
                        `@property def func(self): return lambda: self`);
                        pre-fix the inherited `Basic.func` (basic.py:716)

A real `String(text)` instance is constructed, its real `.args` tuple is read
off it, and its real `.func` is applied to those args. No behaviour is
reimplemented: if the reconstruction raises (as the pre-fix generic positional
rebuild does — `Token.__new__` cannot source the `not_in_args` `text` slot from
the empty argument list, sympy/codegen/ast.py:235 `No value for 'text' given`),
that is recorded as the oracle outcome `None` and disagrees with the shadow.
That is the leg that makes this check CAPABLE OF FAILING: run against the
unpatched base commit it reports a disagreement on every non-empty text, and
the gate applies the gold patch before this script runs.

Two observables are diffed per input, both directions of the model's claims:

  (1) arg count — shadow `arg_count(s)` vs real `len(String(t).args)`.
  (2) reconstruction — shadow `ToSeq(rebuild_from_args(s).text)` vs the real
      `ToSeq(bridge(String(t).func(*String(t).args).text))`, plus the model's
      token-equality abstraction (mapping.md §2: single-slot `Token.__eq__` is
      text equality) cross-checked against the real `rebuilt == st`. A real
      reconstruction that raised, or returned a non-`String`, or an object the
      real `__eq__` calls unequal, is a disagreement.

TYPE BRIDGE (mapping.md §2, inverted) — the model's text carrier is
`List[int]` of Unicode code points because Nagini bans `str` indexing; the real
`String` wants a `str`. `to_model(t) = [ord(c) for c in t]` and
`from_model(cps) = ''.join(chr(c) for c in cps)` are mutually inverse on every
Python `str` (including astral and lone-surrogate code units), so generating
real `str` inputs and lifting them keeps every input inside the model's
`Requires` — which constrains only permissions (`Acc(...)`), never values, so
EVERY `List[int]` satisfies it and the input domain is not narrowed anywhere.
The `self.args` abstraction (length only) is inverted by comparing counts.

INPUTS — the modelled domain (all texts) is infinite, so: a boundary catalogue
first (empty text -> loop body executed zero times; single char; the F2P
literal `'foobar'`; whitespace/quote/control/non-ascii/astral/surrogate; a
200-char text -> long loop), each branch of the impl region taken at least once,
then seeded fuzz to fill the count. Total >= 1e5 Requires-satisfying inputs.
Pinned seed below, recorded in mapping.md §5 (`## G-CONF`).

Exit 0 iff zero disagreements; on a disagreement the input and both outputs are
printed and the exit status is 1. stdlib + sympy only.
"""
import json
import random
import sys
from typing import List  # noqa: F401  (the copied region keeps its type comments)

SEED = 22456          # pinned; recorded in mapping.md ## G-CONF
N_FUZZ = 100_000      # >= 1e5 with the boundary catalogue on top


# --- PSeq shim: the immutable Viper sequence carrier of the specification ----
# `ToSeq(list)` materialises a list as a PSeq; equality of PSeqs is elementwise.
# (take/drop/+ are provided for shape-parity with the model's contracts; the
# stripped impl region itself only needs construction and equality.)

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

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self._t)

    def __repr__(self):
        return "PSeq(%s)" % ", ".join(repr(x) for x in self._t)


def ToSeq(lst):
    return PSeq._wrap(tuple(lst))


# --- model.py's carrier class, contracts stripped ----------------------------

class Atomic:
    """An atomic string-valued token; only its defining `text` payload is
    modelled (the single quantity token equality depends on)."""

    def __init__(self, text):
        self.text = text


# --- model.py's `# pure-start` region, contracts stripped -------------------

def arg_count(s):
    """The number of positional arguments of the token. The defining text is
    held OFF the argument list, so an atomic string token has zero positional
    arguments."""
    return 0


# --- model.py's `# impl-start` .. `# impl-end` region, VERBATIM -------------
# Only the contract calls (Requires/Ensures/Invariant/Assert) and the
# `# invariants-start`/`-end` markers are deleted. No other edit.

def rebuild_from_args(s):
    # impl-start
    # The reconstruction operation yields the very same token (its result is the
    # original object), so it carries the original text regardless of how many
    # positional arguments there are. Materialise a fresh carrier holding
    # exactly the original text.
    n = len(s.text)
    rebuilt_text = []  # type: List[int]
    i = 0
    while i < n:
        c = s.text[i]
        rebuilt_text = rebuilt_text + [c]
        i = i + 1
    result = Atomic(rebuilt_text)  # type: Atomic
    return result
    # impl-end


# --- type bridge (mapping.md §2), both directions ---------------------------

def to_model(text):
    """real `str` -> the model's `List[int]` of Unicode code points."""
    return [ord(c) for c in text]


def from_model(code_points):
    """the model's `List[int]` of code points -> real `str` (inverse)."""
    return "".join(chr(c) for c in code_points)


# --- oracle: the REAL patched repo function, called ------------------------

def oracle(String, text):
    """Call the REAL `String.func(*String.args)` on a real instance.

    Returns (n_args, rebuilt_text_or_None, eq_or_None):
      * n_args             — real `len(st.args)`
      * rebuilt_text       — real `st.func(*st.args).text`, or None if the real
                             reconstruction raised or produced a non-String
      * eq                 — real `rebuilt == st` (`Token.__eq__`), or None
    Nothing here reimplements the patched code; every value is read off the
    real objects."""
    st = String(text)
    n_args = len(st.args)
    try:
        rebuilt = st.func(*st.args)
    except Exception:
        return (n_args, None, None)
    if not isinstance(rebuilt, String):
        return (n_args, None, None)
    return (n_args, rebuilt.text, bool(rebuilt == st))


def check_one(String, text):
    """Diff shadow vs oracle on one input. Returns None on agreement, else a
    printable disagreement report."""
    # forward bridge: real str -> model carrier, then run the SHADOW
    cps = to_model(text)
    s = Atomic(cps)
    shadow_n_args = arg_count(s)
    shadow_result = rebuild_from_args(s)
    # the observable the model's postcondition states, over PSeq[int]
    shadow_seq = ToSeq(shadow_result.text)
    shadow_source_seq = ToSeq(s.text)
    # the model's token-equality abstraction: tokens equal iff texts equal
    shadow_eq = (shadow_seq == shadow_source_seq)

    orc_n_args, orc_text, orc_eq = oracle(String, text)

    # (1) arg count
    if shadow_n_args != orc_n_args:
        return ("G-CONF FAIL: arg-count disagreement\n"
                "  input text=%r\n  shadow arg_count=%r\n  oracle len(args)=%r"
                % (text, shadow_n_args, orc_n_args))

    # (2) reconstruction: the real rebuild must exist and carry the same text
    if orc_text is None:
        return ("G-CONF FAIL: reconstruction disagreement (real "
                "func(*args) failed or returned a non-String)\n"
                "  input text=%r\n  shadow rebuilt text=%r (as str %r)\n"
                "  oracle rebuilt text=None"
                % (text, shadow_seq, from_model(shadow_result.text)))
    orc_seq = ToSeq(to_model(orc_text))
    if shadow_seq != orc_seq:
        return ("G-CONF FAIL: rebuilt-text disagreement\n"
                "  input text=%r\n  shadow rebuilt text=%r (as str %r)\n"
                "  oracle rebuilt text=%r (as str %r)"
                % (text, shadow_seq, from_model(shadow_result.text),
                   orc_seq, orc_text))
    # (3) token equality under the model's abstraction vs the real __eq__
    if shadow_eq != orc_eq:
        return ("G-CONF FAIL: token-equality disagreement\n"
                "  input text=%r\n  shadow (text equality)=%r\n"
                "  oracle (Token.__eq__ rebuilt == original)=%r"
                % (text, shadow_eq, orc_eq))
    return None


# --- inputs -----------------------------------------------------------------

def boundary_texts():
    """Boundary catalogue: every branch of the impl region taken at least once
    (loop body zero times on the empty text, many times on the long one), plus
    the F2P literal and the awkward character classes."""
    return [
        "",              # empty: the while loop body executes ZERO times
        "a",             # singleton: loop body executes exactly once
        "foobar",        # the F2P literal (sympy/codegen/tests/test_ast.py:270)
        "foo",
        "foo bar",       # whitespace inside
        " ",             # whitespace only
        "\n\t",          # control characters
        "text",          # the slot name itself, as content
        "String('x')",   # repr-looking content
        "Joe's",         # apostrophe
        'a"b',           # double quote
        "<x>&amp;",      # markup-ish
        "café",          # non-ascii latin
        "Ω≈ç√∫",         # unicode
        "𝔘𝔫𝔦",           # astral plane (code points > 0xFFFF)
        "\ud800",        # lone surrogate code unit (still a valid Python str)
        "\x00",          # NUL
        "x" * 200,       # long: 200 loop iterations
    ]


def fuzz_texts(n, rng):
    alphabet = list("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
                    "0123456789 _-.,;:!?'\"<>&#=()[]{}\t\n"
                    "éàüΩπ•λ𝔘")
    for _ in range(n):
        k = rng.randint(0, 24)
        yield "".join(rng.choice(alphabet) for _ in range(k))


def main():
    from sympy.codegen.ast import String   # the REAL patched repo class

    checked = 0
    boundary = boundary_texts()
    for text in boundary:
        err = check_one(String, text)
        checked += 1
        if err:
            print(err)
            print(json.dumps({"checked": checked, "disagreements": 1,
                              "seed": SEED, "status": "fail"}))
            return 1

    rng = random.Random(SEED)
    for text in fuzz_texts(N_FUZZ, rng):
        err = check_one(String, text)
        checked += 1
        if err:
            print(err)
            print(json.dumps({"checked": checked, "disagreements": 1,
                              "seed": SEED, "status": "fail"}))
            return 1

    print("G-CONF OK: contract-stripped impl region of rebuild_from_args "
          "(+ arg_count) agrees with the REAL patched "
          "sympy.codegen.ast.String.func(*String.args) on %d inputs "
          "(%d boundary + %d fuzz, seed=%d): rebuilt text, arg count and token "
          "equality all match, 0 disagreements."
          % (checked, len(boundary), N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "boundary": len(boundary), "fuzz": N_FUZZ,
                      "shadow": "direct (contract-stripped impl region)",
                      "oracle": "sympy.codegen.ast.String.func(*String.args) "
                                "(called, patched)",
                      "status": "pass"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
