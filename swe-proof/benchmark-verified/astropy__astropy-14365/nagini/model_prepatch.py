"""Twin-artifact model for astropy__astropy-14365.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A plotting-table text format is parsed line by line. Two recognition
  decisions must treat the format's reserved words case-INsensitively, because
  the format itself is not case sensitive: a reserved word written in any
  mixture of upper- and lower-case denotes the same token.

  (1) COMMAND RECOGNITION.  An error-specification line begins with the
      reserved word ``READ`` followed by one of the two error kinds ``SERR`` or
      ``TERR`` and then a non-empty list of column numbers.  Whether a given
      line is such a command must depend only on the *case-folded* spelling of
      its leading two words: ``read serr 1 2``, ``READ SERR 1 2`` and
      ``Read Serr 1 2`` are all the same command.  A line whose first word
      case-folds to ``READ`` and whose second word case-folds to ``SERR`` or
      ``TERR``, with at least one trailing column number, is a command;
      otherwise it is not (and in particular must not be rejected merely for
      being written in lower case).

  (2) MISSING-VALUE RECOGNITION.  Inside a data row, a single field denotes a
      missing (masked) value exactly when that field, compared
      case-INsensitively, equals the reserved word ``NO``.  Thus ``NO``, ``no``,
      ``No`` and ``nO`` are all the masked sentinel, while any other field is an
      ordinary numeric value.

Both decisions reduce to: normalise the field/word to a single case and
compare the normalised result to a constant reserved word.  Deciding either by
a raw, case-distinguishing comparison is correct only for the all-upper-case
spelling and wrongly rejects the lower- and mixed-case spellings the format
permits.

Text is modelled as ``List[int]`` / ``PSeq[int]`` of code points (Nagini bans
``str`` indexing); the case normalisation is modelled DEEPLY as a per-code-point
upper-casing fold (``upseq``): the ASCII letters ``a``..``z`` fold to
``A``..``Z``, and the single further code point that case-insensitive text
matching identifies with one of the reserved-word letters — the historic long-s
letterform (383), identified with ``S`` — folds to that letter (83); every
other code point is unchanged. The fold is validated equal to the real case
normalisation by axiom_check.py (G-AX), not consumed as an axiom.  The unchanged
surrounding machinery (splitting a line into fields/words, the numeric column
list, the numeric data fields) is case-irrelevant and is handled by refinement,
not re-modelled here.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (none — the changed operation in both sites is the case normalisation
#  itself, modelled deeply below by `up`/`upseq`. The real case normalisation is
#  an A-reference validated by axiom_check.py / G-AX, not a consumed
#  @ContractOnly axiom. The unchanged surrounding machinery is handled by
#  composition in refinement.md and is not referenced from this spec.)
# axioms-end


# pure-start
@Pure
def up(c: int) -> int:
    """Case normalisation of a single code point: a lower-case ASCII letter
    (``a``..``z``, 97..122) maps to its upper-case form (subtract 32); the
    historic long-s letterform (383) — the one further code point that
    case-insensitive text matching identifies with a reserved-word letter —
    maps to ``S`` (83); every other code point is unchanged. This is the
    per-code-point action of the case fold the two recognition decisions rely
    on."""
    Ensures(Implies(97 <= c and c <= 122, Result() == c - 32))
    Ensures(Implies(c == 383, Result() == 83))
    Ensures(Implies(not (97 <= c and c <= 122) and not (c == 383),
                    Result() == c))
    if 97 <= c and c <= 122:
        return c - 32
    if c == 383:
        return 83
    return c


@Pure
def upseq(s: PSeq[int]) -> PSeq[int]:
    """Case fold of a whole field/word: the per-code-point upper-casing applied
    elementwise. Front-recursive so a single unfold is available per loop step.
    Equal in length to the input."""
    Ensures(len(Result()) == len(s))
    if len(s) == 0:
        return s
    return PSeq(up(s[0])) + upseq(s.drop(1))


@Pure
def kw_NO() -> PSeq[int]:
    # "NO"
    return PSeq(78, 79)


@Pure
def kw_READ() -> PSeq[int]:
    # "READ"
    return PSeq(82, 69, 65, 68)


@Pure
def kw_SERR() -> PSeq[int]:
    # "SERR"
    return PSeq(83, 69, 82, 82)


@Pure
def kw_TERR() -> PSeq[int]:
    # "TERR"
    return PSeq(84, 69, 82, 82)


@Pure
def kw_NAN() -> PSeq[int]:
    # "NAN"
    return PSeq(78, 65, 78)


@Pure
def is_masked_field(field: PSeq[int]) -> bool:
    """A data field denotes a missing/masked value iff its case fold equals the
    reserved word ``NO`` (case-insensitive)."""
    return upseq(field) == kw_NO()


@Pure
def is_reserved_data_token(field: PSeq[int]) -> bool:
    """A field is one of the format's RESERVED-WORD data tokens iff (case
    folded) it is the missing-value word ``NO`` or the not-a-number word ``NAN``
    (optionally preceded by a single ``+``/``-`` sign). These reserved words —
    unlike ordinary decimal numbers, which contain no letters — must be
    recognised case-INsensitively: ``no``, ``No``, ``nan``, ``NaN``, ``+nan``
    all denote the same reserved token as ``NO``/``NAN``. (Ordinary numeric
    fields are case-irrelevant and recognised by the unchanged numeric
    machinery, not by this predicate.)"""
    return (upseq(field) == kw_NO()
            or upseq(field) == kw_NAN()
            or (len(field) >= 1
                and (field[0] == 43 or field[0] == 45)   # '+' or '-'
                and upseq(field.drop(1)) == kw_NAN()))


@Pure
def is_command_tokens(tok0: PSeq[int], tok1: PSeq[int], ncols: int) -> bool:
    """The leading two words ``tok0``, ``tok1`` and the count ``ncols`` of
    trailing column numbers denote an error-specification command iff (case
    folded) ``tok0`` is ``READ``, ``tok1`` is ``SERR`` or ``TERR``, and there is
    at least one trailing column number. The case fold is applied to BOTH
    keyword words; the column count is case-irrelevant."""
    return (upseq(tok0) == kw_READ()
            and (upseq(tok1) == kw_SERR() or upseq(tok1) == kw_TERR())
            and ncols >= 1)
# pure-end


def masked_field(field: List[int]) -> bool:
    """Decide whether a single data field is the masked sentinel ``NO``,
    case-insensitively."""
    # pre-conditions-start
    Requires(Acc(list_pred(field), 1 / 2))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(field), 1 / 2))
    # The field is masked iff its case fold equals the reserved word ``NO``.
    Ensures(Result() == is_masked_field(ToSeq(field)))
    # Discriminating witnesses: both ``NO`` and ``no`` are masked; a length-2
    # field that is not a case variant of ``NO`` is not.
    Ensures(Implies(ToSeq(field) == PSeq(78, 79), Result()))   # "NO"
    Ensures(Implies(ToSeq(field) == PSeq(110, 111), Result()))  # "no"
    # post-conditions-end
    # impl-start
    # PRE-PATCH (buggy): raw, case-SENSITIVE comparison of the field against the
    # reserved word ``NO`` (the old ``v == "NO"`` test), with no case fold. A
    # lower-case ``no`` field is therefore NOT recognised as masked, violating
    # the case-insensitive postcondition (G-DIFF).
    return ToSeq(field) == kw_NO()
    # impl-end


def reserved_data_token(field: List[int]) -> bool:
    """Decide whether a single field of a data row is one of the format's
    RESERVED-WORD data tokens — the missing-value word ``NO`` or the
    not-a-number word ``NAN`` (with an optional leading sign) — recognised
    case-INsensitively. (Ordinary decimal-number fields are recognised by the
    unchanged numeric machinery and are out of scope of this decision; this
    decides only the reserved-word alternative that a case-distinguishing
    comparison would wrongly reject in lower case.)"""
    # pre-conditions-start
    Requires(Acc(list_pred(field), 1 / 2))
    Requires(MustTerminate(6))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(field), 1 / 2))
    # The field is a reserved data token iff (case folded) it is ``NO`` or
    # ``NAN`` or a signed ``NAN``.
    Ensures(Result() == is_reserved_data_token(ToSeq(field)))
    # Discriminating witnesses: the lower-case missing-value word ``no`` and the
    # upper-case ``NO`` are both recognised reserved data tokens.
    Ensures(Implies(ToSeq(field) == PSeq(110, 111), Result()))  # "no"
    Ensures(Implies(ToSeq(field) == PSeq(78, 79), Result()))    # "NO"
    # post-conditions-end
    # impl-start
    folded = []  # type: List[int]
    i = len(field)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(field), 1 / 2))
        Invariant(Acc(list_pred(folded)))
        Invariant(0 <= i and i <= len(field))
        Invariant(ToSeq(folded) == upseq(ToSeq(field).drop(i)))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        c = field[i - 1]
        Assert(ToSeq(field).drop(i - 1)[0] == c)
        Assert(ToSeq(field).drop(i - 1).drop(1) == ToSeq(field).drop(i))
        if 97 <= c and c <= 122:
            folded = [c - 32] + folded
        elif c == 383:
            folded = [83] + folded
        else:
            folded = [c] + folded
        i = i - 1
    Assert(ToSeq(field).drop(0) == ToSeq(field))
    # The whole field is now folded: ToSeq(folded) == upseq(ToSeq(field)).
    Assert(ToSeq(folded) == upseq(ToSeq(field)))
    # Witness lemmas: case fold of the two relevant concrete spellings of the
    # missing-value reserved word, proved by explicit front-recursion unfold.
    Assert(up(78) == 78 and up(79) == 79 and up(110) == 78 and up(111) == 79)
    Assert(PSeq(78, 79).drop(1) == PSeq(79) and PSeq(79).drop(1) == PSeq(0).take(0))
    Assert(PSeq(110, 111).drop(1) == PSeq(111) and PSeq(111).drop(1) == PSeq(0).take(0))
    Assert(upseq(PSeq(0).take(0)) == PSeq(0).take(0))
    Assert(upseq(PSeq(79)) == PSeq(79) and upseq(PSeq(111)) == PSeq(79))
    Assert(upseq(PSeq(78, 79)) == kw_NO())     # upseq("NO") == "NO"
    Assert(upseq(PSeq(110, 111)) == kw_NO())   # upseq("no") == "NO"
    # Sign-prefix lemma: the case fold commutes with dropping the leading sign
    # (an unfold of upseq), so the signed-NAN test can be read off `folded`.
    if len(field) >= 1:
        Assert(upseq(ToSeq(field)) == PSeq(up(ToSeq(field)[0]))
               + upseq(ToSeq(field).drop(1)))
        Assert(upseq(ToSeq(field)).drop(1) == upseq(ToSeq(field).drop(1)))
        Assert(Implies(ToSeq(field)[0] == 43 or ToSeq(field)[0] == 45,
                       up(ToSeq(field)[0]) == ToSeq(field)[0]))
    is_no = ToSeq(folded) == kw_NO()
    is_nan = ToSeq(folded) == kw_NAN()
    is_signed_nan = (len(field) >= 1
                     and (field[0] == 43 or field[0] == 45)
                     and ToSeq(folded).drop(1) == kw_NAN())
    return is_no or is_nan or is_signed_nan
    # impl-end


def command_line(tok0: List[int], tok1: List[int], ncols: int) -> bool:
    """Decide whether a line whose leading two whitespace-separated words are
    ``tok0`` and ``tok1`` and which carries ``ncols`` trailing column numbers is
    an error-specification command, case-insensitively."""
    # pre-conditions-start
    Requires(Acc(list_pred(tok0), 1 / 2))
    Requires(Acc(list_pred(tok1), 1 / 2))
    Requires(ncols >= 0)
    Requires(MustTerminate(10))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(tok0), 1 / 2))
    Ensures(Acc(list_pred(tok1), 1 / 2))
    # A command iff (case folded) the words are ``READ`` and ``SERR``/``TERR``
    # with at least one trailing column number.
    Ensures(Result() == is_command_tokens(ToSeq(tok0), ToSeq(tok1), ncols))
    # Discriminating witnesses: a lower-case ``read serr 1`` IS a command;
    # an upper-case ``READ SERR 1`` is too; an unknown error kind is not.
    Ensures(Implies(ToSeq(tok0) == PSeq(114, 101, 97, 100)        # "read"
                    and ToSeq(tok1) == PSeq(115, 101, 114, 114)   # "serr"
                    and ncols >= 1, Result()))
    Ensures(Implies(ToSeq(tok0) == PSeq(82, 69, 65, 68)           # "READ"
                    and ToSeq(tok1) == PSeq(83, 69, 82, 82)       # "SERR"
                    and ncols >= 1, Result()))
    # post-conditions-end
    # impl-start
    f0 = []  # type: List[int]
    i = len(tok0)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(tok0), 1 / 2))
        Invariant(Acc(list_pred(f0)))
        Invariant(0 <= i and i <= len(tok0))
        Invariant(ToSeq(f0) == upseq(ToSeq(tok0).drop(i)))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        c = tok0[i - 1]
        Assert(ToSeq(tok0).drop(i - 1)[0] == c)
        Assert(ToSeq(tok0).drop(i - 1).drop(1) == ToSeq(tok0).drop(i))
        if 97 <= c and c <= 122:
            f0 = [c - 32] + f0
        elif c == 383:
            f0 = [83] + f0
        else:
            f0 = [c] + f0
        i = i - 1
    Assert(ToSeq(tok0).drop(0) == ToSeq(tok0))

    f1 = []  # type: List[int]
    j = len(tok1)
    while j > 0:
        # invariants-start
        Invariant(Acc(list_pred(tok1), 1 / 2))
        Invariant(Acc(list_pred(f1)))
        Invariant(0 <= j and j <= len(tok1))
        Invariant(ToSeq(f1) == upseq(ToSeq(tok1).drop(j)))
        Invariant(MustTerminate(j + 1))
        # invariants-end
        d = tok1[j - 1]
        Assert(ToSeq(tok1).drop(j - 1)[0] == d)
        Assert(ToSeq(tok1).drop(j - 1).drop(1) == ToSeq(tok1).drop(j))
        if 97 <= d and d <= 122:
            f1 = [d - 32] + f1
        elif d == 383:
            f1 = [83] + f1
        else:
            f1 = [d] + f1
        j = j - 1
    Assert(ToSeq(tok1).drop(0) == ToSeq(tok1))

    # Witness lemmas: case fold of the lower- and upper-case spellings of the
    # two keyword words, proved by explicit front-recursion unfold.
    Assert(up(114) == 82 and up(101) == 69 and up(97) == 65 and up(100) == 68)
    Assert(up(115) == 83 and up(82) == 82 and up(69) == 69 and up(65) == 65)
    Assert(up(68) == 68 and up(83) == 83)
    # upseq("read") == "READ"
    Assert(PSeq(114, 101, 97, 100).drop(1) == PSeq(101, 97, 100))
    Assert(PSeq(101, 97, 100).drop(1) == PSeq(97, 100))
    Assert(PSeq(97, 100).drop(1) == PSeq(100))
    Assert(PSeq(100).drop(1) == PSeq(0).take(0))
    Assert(upseq(PSeq(0).take(0)) == PSeq(0).take(0))
    Assert(upseq(PSeq(100)) == PSeq(68))
    Assert(upseq(PSeq(97, 100)) == PSeq(65, 68))
    Assert(upseq(PSeq(101, 97, 100)) == PSeq(69, 65, 68))
    Assert(upseq(PSeq(114, 101, 97, 100)) == kw_READ())
    # upseq("serr") == "SERR"
    Assert(PSeq(115, 101, 114, 114).drop(1) == PSeq(101, 114, 114))
    Assert(PSeq(101, 114, 114).drop(1) == PSeq(114, 114))
    Assert(PSeq(114, 114).drop(1) == PSeq(114))
    Assert(PSeq(114).drop(1) == PSeq(0).take(0))
    Assert(upseq(PSeq(114)) == PSeq(82))
    Assert(upseq(PSeq(114, 114)) == PSeq(82, 82))
    Assert(upseq(PSeq(101, 114, 114)) == PSeq(69, 82, 82))
    Assert(upseq(PSeq(115, 101, 114, 114)) == kw_SERR())
    # upseq("READ") == "READ" (already upper)
    Assert(PSeq(82, 69, 65, 68).drop(1) == PSeq(69, 65, 68))
    Assert(PSeq(69, 65, 68).drop(1) == PSeq(65, 68))
    Assert(PSeq(65, 68).drop(1) == PSeq(68))
    Assert(PSeq(68).drop(1) == PSeq(0).take(0))
    Assert(upseq(PSeq(68)) == PSeq(68))
    Assert(upseq(PSeq(65, 68)) == PSeq(65, 68))
    Assert(upseq(PSeq(69, 65, 68)) == PSeq(69, 65, 68))
    Assert(upseq(PSeq(82, 69, 65, 68)) == kw_READ())
    # upseq("SERR") == "SERR" (already upper)
    Assert(PSeq(83, 69, 82, 82).drop(1) == PSeq(69, 82, 82))
    Assert(PSeq(69, 82, 82).drop(1) == PSeq(82, 82))
    Assert(PSeq(82, 82).drop(1) == PSeq(82) and PSeq(82).drop(1) == PSeq(0).take(0))
    Assert(upseq(PSeq(82)) == PSeq(82))
    Assert(upseq(PSeq(82, 82)) == PSeq(82, 82))
    Assert(upseq(PSeq(69, 82, 82)) == PSeq(69, 82, 82))
    Assert(upseq(PSeq(83, 69, 82, 82)) == kw_SERR())

    is_read = ToSeq(f0) == kw_READ()
    is_err = ToSeq(f1) == kw_SERR() or ToSeq(f1) == kw_TERR()
    return is_read and is_err and ncols >= 1
    # impl-end
