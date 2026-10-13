"""Twin-artifact model for psf__requests-1724.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When a request is constructed from a caller-supplied method name, the method
  carried into the constructed request is the case-normalised form of that
  name, and it is carried as a NATIVE text token regardless of the textual
  flavour the caller supplied.

  Concretely:

    (1) Content: every character of the carried method equals the
        case-normalised (upper-cased) form of the corresponding character of
        the supplied name — ASCII lowercase letters map to their uppercase
        partner, every other code point passes through unchanged; the length
        is preserved.

    (2) Flavour: the carried method is a native text token (the flavour the
        downstream header assembly requires), even when the supplied name was
        of the non-native textual flavour. The carried flavour is the one the
        native-flavour text constructor yields for the supplied content — so
        it IS the native flavour, and it does not depend on the flavour the
        caller supplied.

A textual value is modelled as a minimal class carrying the touched aspects:
the sequence of Unicode code points (Nagini bans ``str`` indexing, so the
carrier is ``List[int]``) and a boolean recording whether the value is of the
native text flavour. The case-normalisation is modelled DEEPLY as a verified
per-code-point fold (``upper_seq``), validated == the real ``str.upper`` by
axiom_check.py (G-AX), not consumed as an axiom. One unchanged callee — the
native-flavour text constructor — is axiomatized, together with the opaque
property that names the flavour it yields: a flavour is native by virtue of
having been produced by that constructor, and no computation can conjure the
property, so the carried flavour has to come from the constructor rather than
be asserted of a value the implementation chose itself.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


class TextToken:
    def __init__(self, chars: List[int], native: bool) -> None:
        Requires(MustTerminate(1))
        Requires(Acc(list_pred(chars), 1 / 2))
        Ensures(Acc(self.chars) and self.chars is chars)        # type: ignore
        Ensures(Acc(self.native) and self.native == native)     # type: ignore
        Ensures(Acc(list_pred(chars), 1 / 2))
        self.chars = chars
        self.native = native


# axioms-start
@Pure
@ContractOnly
def native_form(flavour: bool) -> bool:
    """Holds of the flavour a text value carries once that value has been taken
    over into the NATIVE text flavour.

    Deliberately OPAQUE — it has no body. Nothing computes it, and no caller can
    assert it of a flavour of its own choosing: its only source is `to_native`,
    and the construction step demands it. That is what makes "the carried method
    really is of the native flavour" checkable rather than merely claimable,
    which matters precisely because the flavour of a text value leaves no trace
    in its code points. Provenance + executable soundness check: mapping.md /
    axiom_check.py.
    """


@Pure
@ContractOnly
def to_native(chars: PSeq[int]) -> bool:
    """Native-flavour text constructor (the unchanged callee the construction
    site invokes on the supplied method before any further processing), read as
    the FLAVOUR of the value it produces for the given content. It produces a
    value of the native text flavour, independent of the flavour of its
    argument, while leaving the character content unchanged. The property the
    proof consumes is that the flavour it yields is a native one; which flavour
    that is, is left uninterpreted, so no caller can name it without invoking
    the constructor.
    Provenance + executable soundness check: mapping.md / axiom_check.py.
    """
    Ensures(native_form(Result()))
# axioms-end


# pure-start
@Pure
def upper_cp(c: int) -> int:
    """Case-normalisation of a single code point: an ASCII lowercase letter
    maps to its uppercase partner; every other code point is unchanged."""
    if 97 <= c and c <= 122:   # 'a'..'z'  ->  'A'..'Z'
        return c - 32
    return c


@Pure
def upper_seq(s: PSeq[int]) -> PSeq[int]:
    """Case-normalisation of a whole sequence: the per-code-point upper map.
    Front-recursive so a single unfold is available to callers."""
    if len(s) == 0:
        return PSeq(0).take(0)
    return PSeq(upper_cp(s[0])) + upper_seq(s.drop(1))
# pure-end


def normalize_method(chars: List[int], native: bool) -> TextToken:
    # pre-conditions-start
    Requires(MustTerminate(3))
    Requires(Acc(list_pred(chars), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(chars), 1 / 2))
    Ensures(Acc(Result().chars) and Acc(list_pred(Result().chars)))
    Ensures(Acc(Result().native))
    # (1) content: the carried method is the case-normalised supplied name.
    Ensures(len(Result().chars) == len(chars))
    Ensures(ToSeq(Result().chars) == upper_seq(ToSeq(chars)))
    # (2) flavour: the carried method's flavour is the one the native-flavour
    #     constructor yields for the supplied content — hence a native flavour
    #     (`native_form`), and independent of the supplied `native`.
    Ensures(Result().native == to_native(ToSeq(chars)))
    Ensures(native_form(Result().native))
    # post-conditions-end
    # impl-start
    native_flavour = native
    out = []  # type: List[int]
    i = len(chars)
    while i > 0:
        # invariants-start
        Invariant(MustTerminate(i + 1))
        Invariant(Acc(list_pred(chars), 1 / 2))
        Invariant(Acc(list_pred(out)))
        Invariant(0 <= i and i <= len(chars))
        Invariant(len(out) == len(chars) - i)
        Invariant(ToSeq(out) == upper_seq(ToSeq(chars).drop(i)))
        # invariants-end
        c = chars[i - 1]
        Assert(ToSeq(chars).drop(i - 1)[0] == c)
        Assert(ToSeq(chars).drop(i - 1).drop(1) == ToSeq(chars).drop(i))
        out = [upper_cp(c)] + out
        i = i - 1
    return TextToken(out, native_flavour)
    # impl-end
