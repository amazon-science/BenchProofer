"""Twin-artifact model for django__django-15503.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A membership test for a key inside a stored JSON document compiles a textual
  path that selects WHERE in the document to look. The path step that selects
  the *final* key of a key-membership test addresses that key by its exact
  characters, for EVERY key, including a key whose characters all happen to be
  decimal digits.

  Concretely the final path step is: a separator '.' followed by the JSON
  string literal of the key (the key surrounded by double quotes). The key's
  characters are reproduced verbatim, in order, so a key such as "1111" or
  "000" yields the step `."1111"` / `."000"` -- the exact characters between
  the quotes, with no change to a key that happens to look numeric.

Strings (the key and the produced path segment) are modelled as `List[int]` of
Unicode code points (Nagini bans `str` indexing); the specification is carried
over `PSeq[int]` via `ToSeq`. The key domain is restricted to characters whose
JSON string literal is the key verbatim between double quotes (no character
that the JSON encoder would escape), which covers the keys the behaviour is
exercised on.

The JSON string-literal encoder of the unchanged serialization callee is
modelled deeply (`json_string_literal`) as the quote-wrap on this domain; its
equality to the real callee is checked out-of-band by axiom_check.py (G-AX),
not consumed as an axiom.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (no consumed @ContractOnly axioms: the changed serialization step is modelled
#  deeply by json_string_literal in the pure region and validated against the
#  real callee by axiom_check.py / G-AX as an A-reference.)
# axioms-end


# pure-start
@Pure
def is_digit(c: int) -> bool:
    """A single Unicode code point is an ASCII decimal digit 0-9."""
    return 48 <= c and c <= 57


@Pure
def all_digits(s: PSeq[int]) -> bool:
    """Every code point of the (non-empty) sequence is a decimal digit; the
    empty sequence is not all-digits. Front-recursive so one unfold is
    available per loop step."""
    if len(s) == 0:
        return False
    if len(s) == 1:
        return is_digit(s[0])
    return is_digit(s[0]) and all_digits(s.drop(1))


@Pure
def json_string_literal(s: PSeq[int]) -> PSeq[int]:
    """The JSON string literal of a key drawn from the modelled domain (no
    character the JSON encoder escapes): the key verbatim wrapped in double
    quotes. Deep model of the unchanged serialization callee; validated equal
    to the real callee by axiom_check.py (G-AX)."""
    return PSeq(34) + s + PSeq(34)


@Pure
def member_access_segment(key: PSeq[int]) -> PSeq[int]:
    """The desired final path step for a key-membership test: the separator
    '.' (46) followed by the JSON string literal of the key. The same form for
    EVERY key, numeric or not."""
    return PSeq(46) + json_string_literal(key)


@Pure
def in_domain(s: PSeq[int]) -> bool:
    """Key domain: every code point is printable ASCII (32..126) and is neither
    a double quote (34) nor a backslash (92) -- exactly the characters the JSON
    string encoder leaves verbatim between the surrounding quotes (it escapes
    quote/backslash/controls and emits non-ASCII as \\uXXXX)."""
    return Forall(int, lambda i: (Implies(0 <= i and i < len(s),
                                          32 <= s[i] and s[i] <= 126
                                          and s[i] != 34 and s[i] != 92)))
# pure-end


def compile_final_key_segment(key: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(key), 1 / 2))
    Requires(in_domain(ToSeq(key)))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(key), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The final path step is the member-access form for EVERY key (numeric or
    # not): separator '.' then the key's JSON string literal ("key").
    Ensures(ToSeq(Result()) == member_access_segment(ToSeq(key)))
    # Structural consequences pinned explicitly:
    #   - the step begins with the separator '.' (46) then a quote '"' (34);
    #   - the key characters appear verbatim, in order, between the quotes,
    #     so the result reproduces the key's exact characters unchanged.
    Ensures(len(Result()) == len(key) + 3)
    Ensures(Result()[0] == 46)
    Ensures(Result()[1] == 34)
    Ensures(Result()[len(Result()) - 1] == 34)
    Ensures(Forall(int, lambda i: (Implies(0 <= i and i < len(key),
                                           Result()[i + 2] == key[i]))))
    # post-conditions-end
    # impl-start
    # Pre-patch skeleton: a key whose characters are all decimal digits is
    # emitted in the form '[' key ']' instead of the '.' + '"' key '"' form;
    # only a non-all-digit key takes the '.' + '"' key '"' form. This fails the
    # postcondition for an all-digit key (G-DIFF).
    if all_digits(ToSeq(key)):
        arr = [91]  # type: List[int]   # '['
        j = 0
        while j < len(key):
            # invariants-start
            Invariant(Acc(list_pred(key), 1 / 2))
            Invariant(Acc(list_pred(arr)))
            Invariant(0 <= j and j <= len(key))
            Invariant(ToSeq(arr) == PSeq(91) + ToSeq(key).take(j))
            Invariant(MustTerminate(len(key) - j + 1))
            # invariants-end
            arr = arr + [key[j]]
            j = j + 1
        arr = arr + [93]  # ']'  (this branch fails the postcondition: G-DIFF)
        return arr
    result = [46, 34]  # type: List[int]
    i = 0
    while i < len(key):
        # invariants-start
        Invariant(Acc(list_pred(key), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(key))
        Invariant(ToSeq(result) == PSeq(46, 34) + ToSeq(key).take(i))
        Invariant(MustTerminate(len(key) - i + 1))
        # invariants-end
        result = result + [key[i]]
        i = i + 1
    result = result + [34]
    return result
    # impl-end
