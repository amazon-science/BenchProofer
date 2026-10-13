#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for sympy__sympy-13091.

The bundle models the rich-comparison OPERATORS `==` / `!=` for a symbolic left
operand (mapping.md). The gold patch changes two idioms, in ~30 classes:

  * `__eq__` returns `NotImplemented` (abstain) instead of `False` when it cannot
    interpret the operand, so the `==` operator delegates to the operand's
    reflected `__eq__` (symmetric equality);
  * `__ne__` negates the resolved `==` OPERATOR (`not self == other`) instead of
    the raw self-method verdict (`not self.__eq__(other)`).

Standing up the full sympy class hierarchy to drive every site is heavy and
unnecessary: the gated outcome is a PURE function of how the left method
classifies the operand (5 booleans) plus the operand's own reflected opinion.

  * ORACLE — a faithful in-process replica of the POST-PATCH semantics. The repo
    has TWO families of left method and the replica has one class for each: the
    classify-then-compare family (basic.py `Basic.__eq__`, numbers.py
    `Float`/`Rational`/`Integer`/`NumberSymbol.__eq__`), whose uninterpretable
    case the patch makes `NotImplemented` rather than `False`; and the
    identity-only family (`Infinity`/`NegativeInfinity`/`NaN.__eq__`, each of
    which is a bare `return other is <singleton>`), which never interprets the
    operand and therefore never abstains. The `==` operator then resolves the
    method's reply exactly the way CPython does (left method -> reflected method
    -> identity), with `!=` the negation of that resolved operator. Both replica
    classes are exercised through Python's real `==`/`!=` operators, so the
    reflected-dispatch and `not ==` semantics are the interpreter's, not ours.
  * SHADOW — the op-for-op transliteration of `implementation_richEq` /
    `implementation_richNe` (Solution.lean impl region), per refinement.md.

stdlib-only. Pinned seed: 13091 (also in mapping.md / meta.json).
"""
import random
import sys

SEED = 13091
N = 200_000

# `None` ↦ NotImplemented ; True/False ↦ definite verdict.  (mapping.md bijection)
THREE = (None, True, False)


# --- ORACLE: realize the POST-PATCH operator semantics via real Python ops ----
class _Left:
    """A symbolic left operand of the CLASSIFY-THEN-COMPARE family. Its __eq__
    reproduces the POST-PATCH left method: a definite verdict for an interpretable
    operand, ABSTENTION (NotImplemented) when the operand cannot be interpreted.
    __ne__ negates the resolved `==` operator (the fix: `not self == other`)."""
    def __init__(self, sameObj, interpretable, sameKind, contentEq):
        self.sameObj = sameObj
        self.interpretable = interpretable
        self.sameKind = sameKind
        self.contentEq = contentEq

    def __eq__(self, other):
        if self.sameObj:
            return True
        if not self.interpretable:
            return NotImplemented          # the fix (was: return False)
        if not self.sameKind:
            return False
        return self.contentEq

    def __ne__(self, other):
        return not self == other           # the fix (was: not self.__eq__(other))

    __hash__ = None


class _IdentityOnlyLeft:
    """A symbolic left operand of the IDENTITY-ONLY family: its whole __eq__ is
    `return other is <this singleton>`, i.e. the answer is the identity
    observation and nothing else. It has no notion of interpreting the operand,
    so it can never abstain — which is why the patch leaves these three methods
    untouched. Its __ne__ is the matching `return other is not <singleton>`."""
    def __init__(self, sameObj):
        self.sameObj = sameObj

    def __eq__(self, other):
        return self.sameObj                # stands for `other is <singleton>`

    def __ne__(self, other):
        return not self.sameObj            # `other is not <singleton>`

    __hash__ = None


class _Right:
    """The operand. Its reflected __eq__ returns the modeled three-valued opinion
    (NotImplemented ↦ abstain). This is arbitrary user code (mapping.md)."""
    def __init__(self, verdict):
        self.verdict = verdict             # None ↦ NotImplemented

    def __eq__(self, other):
        return NotImplemented if self.verdict is None else self.verdict

    __hash__ = None


def oracle(inp):
    if inp["identityOnly"]:
        left = _IdentityOnlyLeft(inp["sameObj"])
    else:
        left = _Left(inp["sameObj"], inp["interpretable"], inp["sameKind"],
                     inp["contentEq"])
    right = _Right(inp["otherVerdict"])
    # Use Python's REAL operators so reflected dispatch + `not ==` are authentic.
    eq = bool(left == right)
    ne = bool(left != right)
    return (eq, ne)


# --- SHADOW of the Solution.lean impl region (the R/I legs) -------------------
def self_eq_verdict(sameObj, identityOnly, interpretable, sameKind, contentEq):
    if sameObj:
        return True
    if identityOnly:
        return False
    if not interpretable:
        return None
    if not sameKind:
        return False
    return contentEq


def shadow_eq(inp):
    sv = self_eq_verdict(inp["sameObj"], inp["identityOnly"],
                         inp["interpretable"], inp["sameKind"], inp["contentEq"])
    if sv is not None:
        return sv
    ov = inp["otherVerdict"]
    if ov is not None:
        return ov
    return False


def shadow(inp):
    eq = shadow_eq(inp)
    return (eq, (not eq))


def disagree(inp):
    got = oracle(inp)
    want = shadow(inp)
    return None if got == want else (inp, got, want)


def _enumerate_all():
    cases = []
    for so in (False, True):
        for io in (False, True):
            for it in (False, True):
                for sk in (False, True):
                    for ce in (False, True):
                        for ov in THREE:
                            cases.append(dict(sameObj=so, identityOnly=io,
                                              interpretable=it, sameKind=sk,
                                              contentEq=ce, otherVerdict=ov))
    return cases


def main() -> int:
    checked = 0
    # The modeled input space is finite (2^5 * 3 = 96); enumerate it exhaustively
    # first, then fuzz to satisfy the volume requirement.
    for inp in _enumerate_all():
        d = disagree(inp)
        if d:
            print(f"DISAGREE exhaustive: oracle={d[1]} shadow={d[2]} inp={d[0]}")
            print("status=fail")
            return 1
        checked += 1

    rng = random.Random(SEED)
    for _ in range(N):
        inp = dict(
            sameObj=rng.random() < 0.5,
            identityOnly=rng.random() < 0.5,
            interpretable=rng.random() < 0.5,
            sameKind=rng.random() < 0.5,
            contentEq=rng.random() < 0.5,
            otherVerdict=rng.choice(THREE),
        )
        d = disagree(inp)
        if d:
            print(f"DISAGREE fuzz: oracle={d[1]} shadow={d[2]} inp={d[0]}")
            print("status=fail")
            return 1
        checked += 1

    print(f"checked={checked} disagreements=0")
    print("status=pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
