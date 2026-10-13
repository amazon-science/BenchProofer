"""Twin-artifact model for sympy__sympy-20916.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When a symbol name ends in a run of digits, those trailing digits are peeled
  off and treated as a subscript, the remaining leading run of letters becoming
  the bare name. This trailing-digit exception is purely script-agnostic: a
  code point counts as a "letter" if it is a letter in ANY script (Latin,
  Greek, ...), and as a "digit" if it is a decimal digit in ANY script. So a
  leading run of letters in any script followed by a run of decimal digits is
  recognised and split, and a Greek-letter name with trailing digits is treated
  exactly like a Latin-letter one.

  A single line-feed code point sitting at the very END of a candidate name is
  not part of the name proper: it is set aside before the recognise/split
  decision is taken, and when the split applies it joins neither the bare name
  nor the peeled digit run. Exactly one terminating line feed is set aside, so a
  name ending in two of them still has a non-digit tail and is not split, and no
  code point other than a single terminating line feed is ever set aside.

  Concretely, for a candidate name s (the part of a symbol left of any explicit
  sub/superscript markers), write c for the name proper — s with one terminating
  line feed set aside as above. The split applies iff c is a NON-EMPTY run of
  letters immediately followed by a NON-EMPTY run of decimal digits, with
  nothing else: every code point of c before the first digit is a letter and
  every code point of c from the first digit onward is a digit. When it applies,
  the bare name becomes that leading letter run and the trailing digit run of c
  becomes a subscript; otherwise the name is left unchanged — terminating line
  feed included — and no subscript is produced.

  The discriminating cases the contract pins:
    * a Latin-letter name with trailing digits splits, e.g. "w1" -> name "w",
      subscript "1";
    * a Greek-letter (or any other non-Latin script) name with trailing digits
      ALSO splits, e.g. a Greek omega followed by "1" -> name omega, subscript
      "1" — letters are recognised regardless of script;
    * trailing digits are recognised whatever script the digits come from;
    * a name with no trailing digit run, or with a non-letter before the
      digits, or all-digit, or all-letter, is NOT split;
    * one terminating line feed disturbs none of the above: "w1" and "w1"
      followed by a line feed both give name "w", subscript "1".

Strings are modelled as `List[int]` of Unicode code points (Nagini bans `str`
indexing); the specification is carried by the pure sequence theory `PSeq[int]`.
The two per-code-point classifications (letter, decimal digit) are the UNCHANGED
primitives the operation rests on; they are `@Pure @ContractOnly` axioms
validated == the language runtime's full (any-script) letter/decimal-digit
classes by axiom_check.py (G-AX), NOT consumed beyond what the proof needs. The
recognise/split decision itself — the behaviour under specification — is
modelled DEEPLY as verified front-recursive folds over the code points.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
@Pure
@ContractOnly
def is_letter(c: int) -> bool:
    """True iff code point `c` is a LETTER in any script (the language's
    name-letter notion: a word character that is neither a decimal digit nor
    the underscore). Provenance + executable soundness check: mapping.md /
    axiom_check.py (validated against the runtime's any-script letter class,
    A-reference)."""
    Ensures(Implies(Result(), not is_digit(c)))   # letters and digits disjoint


@Pure
@ContractOnly
def is_digit(c: int) -> bool:
    """True iff code point `c` is a DECIMAL DIGIT in any script (the language's
    decimal-digit class). Provenance + executable soundness check: mapping.md /
    axiom_check.py (validated against the runtime's any-script decimal-digit
    class, A-reference)."""
# axioms-end


# pure-start
@Pure
def core_len(s: PSeq[int]) -> int:
    """Length of the name PROPER of `s`: `s` with a single terminating line-feed
    code point (10) set aside. Exactly one trailing line feed is set aside;
    every other code point — a second line feed included — belongs to the name
    proper, so the name proper is `s.take(core_len(s))`."""
    Ensures(0 <= Result() and Result() <= len(s))
    if len(s) >= 1 and s[len(s) - 1] == 10:
        return len(s) - 1
    return len(s)


@Pure
def num_leading_letters(s: PSeq[int]) -> int:
    """Length of the maximal prefix of `s` whose every code point is a letter.
    Front-recursive so a single unfold is available per proof step."""
    Ensures(0 <= Result() and Result() <= len(s))
    # Everything strictly before the returned index is a letter; the code point
    # AT the index (when there is one) is not a letter.
    Ensures(Implies(Result() < len(s), not is_letter(s[Result()])))
    # The count of the whole sequence is its first letter plus the count of the
    # tail (front-recursive decomposition the loop relies on).
    if len(s) == 0:
        return 0
    if not is_letter(s[0]):
        return 0
    return 1 + num_leading_letters(s.drop(1))


@Pure
def all_digits(s: PSeq[int]) -> bool:
    """True iff every code point of `s` is a decimal digit. Front-recursive."""
    Ensures(Result() == Forall(int, lambda k: (Implies(0 <= k and k < len(s),
                                                        is_digit(s[k])),
                                                [[s[k]]])))
    if len(s) == 0:
        return True
    if not is_digit(s[0]):
        # s[0] is a non-digit at index 0: witnesses the Forall failing.
        return False
    # is_digit(s[0]) holds. Every tail position s.drop(1)[t] equals s[t+1], so
    # the tail's Forall (the recursive postcondition) transfers to the full
    # Forall over s (index 0 is the digit s[0]).
    Assert(Forall(int, lambda t: (Implies(0 <= t and t < len(s) - 1,
                                          s.drop(1)[t] == s[t + 1]),
                                  [[s.drop(1)[t]]])))
    Assert(Forall(int, lambda k: (Implies(1 <= k and k < len(s),
                                          s[k] == s.drop(1)[k - 1]),
                                  [[s[k]]])))
    return all_digits(s.drop(1))


@Pure
def splits(s: PSeq[int]) -> bool:
    """The trailing-digit exception applies to `s` iff the name proper
    `s.take(core_len(s))` is a non-empty run of letters immediately followed by
    a non-empty run of decimal digits, with nothing else. Because letters and
    digits are disjoint, the boundary is the end of the leading letter run: the
    split applies iff that run is non-empty, stops strictly inside the name
    proper, and the rest of the name proper is all digits."""
    return (num_leading_letters(s) >= 1
            and num_leading_letters(s) < core_len(s)
            and all_digits(s.take(core_len(s))
                           .drop(num_leading_letters(s))))


@Pure
def split_point(s: PSeq[int]) -> int:
    """The code-point index at which `s` is split when the exception applies:
    the length of the leading letter run (= the start of the trailing digit run
    inside the name proper). Only meaningful when `splits(s)`."""
    return num_leading_letters(s)


@Pure
def digit_run(s: PSeq[int]) -> PSeq[int]:
    """The peeled trailing digit run — the part of the name PROPER from the
    split point onward, so the set-aside terminating line feed is not part of
    it. Only meaningful when `splits(s)`."""
    return s.take(core_len(s)).drop(split_point(s))
# pure-end


def split_trailing_digits(name: List[int]) -> List[int]:
    # pre-conditions-start
    # `name` is the candidate symbol name (code points), read-only: the
    # operation derives a new bare name and never mutates the input.
    Requires(Acc(list_pred(name), 1 / 2))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(name), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # When the trailing-digit exception applies, the bare name is exactly the
    # leading letter run; the peeled trailing digit run (the new subscript) is
    # `digit_run` and is non-empty and all digits.
    Ensures(Implies(splits(ToSeq(name)),
                    ToSeq(Result())
                    == ToSeq(name).take(split_point(ToSeq(name)))))
    Ensures(Implies(splits(ToSeq(name)),
                    len(digit_run(ToSeq(name))) >= 1
                    and all_digits(digit_run(ToSeq(name)))))
    # When it does not apply, the name is returned unchanged.
    Ensures(Implies(not splits(ToSeq(name)), ToSeq(Result()) == ToSeq(name)))
    # post-conditions-end

    # impl-start
    # PRE-PATCH skeleton: the leading-letter and trailing-digit runs are
    # recognised with an ASCII-only test (code points 'A'-'Z'/'a'-'z' for the
    # letter run, '0'-'9' for the digit run) instead of the language's full
    # Unicode word/decimal-digit notion. This disagrees with the spec's
    # `is_letter` / `is_digit` on any non-ASCII letter or non-ASCII digit, so
    # the splits-keyed postconditions cannot hold (e.g. a Greek-letter name
    # with a trailing digit is left unsplit although `splits` is True).
    n = len(name)
    # The name proper ends at `m`: one terminating line-feed code point is set
    # aside (unchanged by the behaviour under specification).
    m = n
    if n >= 1 and name[n - 1] == 10:
        m = n - 1
    # Count the leading run of ASCII letters.
    k = 0
    while k < n and ((65 <= name[k] and name[k] <= 90)
                     or (97 <= name[k] and name[k] <= 122)):
        # invariants-start
        Invariant(Acc(list_pred(name), 1 / 2))
        Invariant(0 <= k and k <= n and n == len(name))
        Invariant(MustTerminate(n - k + 1))
        # invariants-end
        k = k + 1
    # Decide whether the name proper's remainder [k, m) is a non-empty run of
    # ASCII digits.
    matched = False
    if k >= 1 and k < m:
        j = k
        bad = False
        while j < m and not bad:
            # invariants-start
            Invariant(Acc(list_pred(name), 1 / 2))
            Invariant(k <= j and j <= m and m <= n and n == len(name))
            Invariant(MustTerminate(m - j + 1))
            # invariants-end
            if not (48 <= name[j] and name[j] <= 57):
                bad = True
            else:
                j = j + 1
        matched = not bad
    # Build the result list: the leading ASCII-letter run when matched, else
    # the whole name unchanged.
    if matched:
        upper = k
    else:
        upper = n
    result = []  # type: List[int]
    i = 0
    while i < upper:
        # invariants-start
        Invariant(Acc(list_pred(name), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= upper and upper <= n and n == len(name))
        Invariant(ToSeq(result) == ToSeq(name).take(i))
        Invariant(MustTerminate(upper - i + 1))
        # invariants-end
        Assert(ToSeq(name).take(i + 1) == ToSeq(name).take(i) + PSeq(name[i]))
        result = result + [name[i]]
        i = i + 1
    return result
    # impl-end
