#!/usr/bin/env python3
"""G-CONF differential conformance check for sympy__sympy-21930 (nagini).

SHADOW: the impl regions of model.py's `render_token_a` / `render_token_b` /
`render_token_c`, copied VERBATIM below with the contract calls (Requires/
Ensures/Invariant) stripped. The @Pure helpers the impl consults (`LBRACE`,
`RBRACE`, `CARET`, and the spec-only `grouped_token` /
`appended_super_is_outer`) copy over as plain functions; `PSeq`/`ToSeq`
become immutable-tuple shims. There are no @ContractOnly callees.

ORACLE: the REAL patched repo renderers per mapping.md — the `_latex`
methods of the three second-quantization operator classes at
sympy/physics/secondquant.py (the gate applies patch.diff to /testbed before
this script runs; PYTHONPATH=/testbed). Each method is invoked directly with
a real LatexPrinter instance (the argument the methods ignore).

Type bridge (mapping.md section 2): the repo carrier is `str`; the model
carrier is `List[int]` of Unicode code points, `s[k] <-> body[k] == ord(s[k])`.
The model's `body` parameter is the operator's intrinsic rendering — the
UNCHANGED interpolation of the operator's own attributes (symbol / index
names / state name), which the modeled delta then wraps. For each generated
operator the script derives that intrinsic body from the constructed
object's attributes (matching mapping.md A1/A3: the body is carried as an
uninterpreted input; only the outer delimiters are the modeled operation),
converts it to code points for the shadow, and compares the shadow's output
code-point list against the real method's returned string, code point by
code point.

Input domain: the model Requires only a readable code-point list; the bridge
domain is every body realizable from the operators' attributes — arbitrary
Symbol labels (ASCII identifiers, digits, greek, unicode, punctuation,
multi-char) for the state/index slots, and 0..4 upper/lower indices
for the tensor renderer. Boundary cases enumerate short/degenerate labels
and index-count corners; randomized fuzz covers long/astral labels.

>= 1e5 Requires-satisfying inputs across the three modeled sites (boundary +
fuzz). Pinned fuzz seed: 219300. Exit 0 iff zero disagreements; on
disagreement prints the input and both outputs and exits 1. stdlib only.
"""
import json
import random
import sys
from typing import List


# --- shims for the sequence carrier -------------------------------------------

class _Seq(tuple):
    """Immutable code-point sequence with the tiny slice API the pure
    helpers use."""
    def take(self, n):
        return _Seq(self[:n])

    def drop(self, n):
        return _Seq(self[n:])

    def __add__(self, other):
        return _Seq(tuple(self) + tuple(other))


def PSeq(*items):
    """Immutable sequence literal."""
    return _Seq(items)


def ToSeq(lst):
    """Immutable snapshot of a list's contents."""
    return _Seq(lst)


# --- @Pure helpers from model.py, contracts stripped ---------------------------

def LBRACE():
    return 123        # '{'


def RBRACE():
    return 125        # '}'


def CARET():
    return 94         # '^'


def grouped_token(body):
    """The rendered token: the body wrapped as one group `{ body }`."""
    return PSeq(LBRACE()) + body + PSeq(RBRACE())


def appended_super_is_outer(token, exp):
    """True iff `token` is a self-delimited group (ends in `}`)."""
    if len(token) == 0:
        return False
    return token[len(token) - 1] == RBRACE()


# --- the impl regions of model.py, verbatim, contract calls stripped -----------

def render_token_a(body: List[int]) -> List[int]:
    result = [LBRACE()]  # type: List[int]
    i = 0
    while i < len(body):
        result.append(body[i])
        i = i + 1
    result.append(RBRACE())
    return result


def render_token_b(body: List[int]) -> List[int]:
    result = [LBRACE()]  # type: List[int]
    i = 0
    while i < len(body):
        result.append(body[i])
        i = i + 1
    result.append(RBRACE())
    return result


def render_token_c(body: List[int]) -> List[int]:
    result = [LBRACE()]  # type: List[int]
    i = 0
    while i < len(body):
        result.append(body[i])
        i = i + 1
    result.append(RBRACE())
    return result


# --- differential driver --------------------------------------------------------

SEED = 219300
N_TOTAL = 105_000


def encode(s):
    return [ord(ch) for ch in s]


def check_site(site_name, shadow_fn, body_str, real_out, desc):
    """Bridge one (site, body) pair: run the shadow on the body's code points
    and compare against the real method's returned string. Returns an error
    string on disagreement, else None."""
    shadow_out = shadow_fn(encode(body_str))
    real_pts = encode(real_out)
    if shadow_out != real_pts:
        return ("DISAGREEMENT at %s\n  input: %s\n  body: %r"
                "\n  shadow: %r\n  real:   %r (code points %r)"
                % (site_name, desc, body_str, shadow_out, real_out, real_pts))
    return None


def label_pool(rng, ws=False):
    """Boundary label set for the state/index/symbol slots."""
    base = ["i", "j", "k", "p", "q", "n", "m", "a", "b", "0", "1", "9",
            "alpha", "beta", "x1", "k_1", "state", "phi", "psi",
            "α", "ψ", "A", "Z", "long_state_name_0123456789",
            "s s", "s.t", "s-t", "s+t", "'", "~", "!", "#", "%", "&",
            "(", ")", "[", "]", "|", "<", ">", "=", "?", "@",
            "é", "中", "\U0001d49c"]
    return base


def rand_label(rng):
    """Randomized label: identifier-ish, digit-heavy, punctuation, or
    high/astral code points (surrogates excluded)."""
    mode = rng.randrange(4)
    if mode == 0:
        alpha = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
        n = rng.randint(1, 10)
        return "".join(rng.choice(alpha + "0123456789_") for _ in range(n))
    if mode == 1:
        return str(rng.randint(0, 10 ** rng.randint(1, 6)))
    if mode == 2:
        pool = "!#%&'()*+,-./:;<=>?@[]|~ "
        n = rng.randint(1, 6)
        return "".join(rng.choice(pool) for _ in range(n))
    n = rng.randint(1, 4)
    out = ""
    while len(out) < n:
        c = rng.randint(0x21, 0x2FFFF)
        if 0xD800 <= c <= 0xDFFF:
            continue
        out += chr(c)
    return out


def main():
    # REAL patched repo classes (mapping.md section 1) — import from /testbed.
    import sympy as sp
    from sympy.physics.secondquant import (
        Bd, Fd, AntiSymmetricTensor as AT,
    )
    from sympy.printing.latex import LatexPrinter

    printer = LatexPrinter()
    rng = random.Random(SEED)
    checked = 0
    n_boundary = 0

    def check_creation(cls, shadow_fn, prefix, label):
        """One creation-operator case: build the operator on a state Symbol
        with the given label, derive the intrinsic body from the constructed
        object's own state attribute (the unchanged interpolation), and diff
        shadow vs the real method."""
        op = cls(sp.Symbol(label))
        body = prefix + op.state.name + "}"
        real = op._latex(printer)
        return check_site(cls.__name__, shadow_fn, body, real,
                          "state label %r" % label)

    def check_tensor(sym_label, upper_labels, lower_labels):
        """One tensor case: build the tensor, derive the intrinsic body from
        the constructed object's own symbol/index attributes (index order as
        canonicalized by the class itself), and diff shadow vs the real
        method. Returns (err, counted)."""
        ups = tuple(sp.Symbol(l) for l in upper_labels)
        lows = tuple(sp.Symbol(l) for l in lower_labels)
        try:
            op = AT(sp.Symbol(sym_label), ups, lows)
        except Exception:
            return None, False           # out of the constructor's domain
        if not isinstance(op, AT):
            op = -op                     # canonicalization sign, if any
            if not isinstance(op, AT):
                return None, False
        body = "%s^{%s}_{%s}" % (
            op.symbol,
            "".join(i.name for i in op.args[1]),
            "".join(i.name for i in op.args[2]))
        real = op._latex(printer)
        err = check_site("AntiSymmetricTensor", render_token_a, body, real,
                         "symbol %r upper %r lower %r"
                         % (sym_label, upper_labels, lower_labels))
        return err, True

    # --- boundary inputs -------------------------------------------------------
    labels = label_pool(rng)
    for lab in labels:
        for cls, fn, prefix in ((Bd, render_token_b, "b^\\dagger_{"),
                                (Fd, render_token_c, "a^\\dagger_{")):
            err = check_creation(cls, fn, prefix, lab)
            if err:
                print(err)
                return 1
            checked += 1
    # tensor corners: index counts 0..3 on each side, distinct short labels
    idx_names = ["a", "b", "c", "d", "i", "j", "k", "l"]
    for nu in range(0, 4):
        for nl in range(0, 4):
            for sym in ["t", "v", "T0", "gamma"]:
                err, counted = check_tensor(
                    sym, idx_names[:nu], idx_names[4:4 + nl])
                if err:
                    print(err)
                    return 1
                if counted:
                    checked += 1
    n_boundary = checked

    # --- randomized fuzz to >= N_TOTAL ------------------------------------------
    while checked < N_TOTAL:
        mode = checked % 3
        if mode == 0:
            err = check_creation(Bd, render_token_b, "b^\\dagger_{",
                                 rand_label(rng))
            counted = True
        elif mode == 1:
            err = check_creation(Fd, render_token_c, "a^\\dagger_{",
                                 rand_label(rng))
            counted = True
        else:
            nu = rng.randint(0, 4)
            nl = rng.randint(0, 4)
            # distinct index labels (a repeated index degenerates the tensor)
            seen = set()
            ups, lows = [], []
            while len(ups) < nu or len(lows) < nl:
                lab = rand_label(rng)
                if lab in seen:
                    continue
                seen.add(lab)
                (ups if len(ups) < nu else lows).append(lab)
            err, counted = check_tensor(rand_label(rng), ups, lows)
        if err:
            print(err)
            return 1
        if counted:
            checked += 1

    print("G-CONF OK: shadow impl == real patched renderers on %d "
          "(site, body) inputs across the 3 modeled sites "
          "(%d boundary + %d fuzz, seed %d)."
          % (checked, n_boundary, checked - n_boundary, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
