"""Twin-artifact model for django__django-15098.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When a request path is inspected for a leading locale prefix, the locale
  candidate is the run of characters that immediately follows the leading
  ``"/"`` and that is built only from "word" code points joined by the two
  permitted sub-tag separators ``"-"`` and ``"@"``. Following the language-tag
  grammar of RFC 5646, such a candidate is

      language ["-" script] ["-" region]

  i.e. a primary sub-tag optionally followed by up to TWO further sub-tags,
  each separator immediately followed by a non-empty word run (so a sub-tag is
  never empty and the candidate neither begins nor ends with a separator). The
  candidate is accepted as a locale prefix iff:

    * the path begins with ``"/"``;
    * the candidate run is a well-formed sequence of word sub-tags joined by
      single separators (non-empty; starts and ends with a word code point; no
      two adjacent separators);
    * it contains AT MOST TWO separators (a primary sub-tag plus at most a
      script and a region sub-tag); and
    * the character immediately after the candidate run is the path separator
      ``"/"``, the end of the path, or a newline that is the LAST character of
      the path (Python-``re`` ``$`` semantics: ``$`` matches at end-of-string
      and also immediately before a newline at the very end of the string).

  When accepted, the extracted locale candidate is exactly that run (its length
  is returned); otherwise there is no locale prefix (``-1`` is returned). In
  particular a candidate carrying both a script and a region sub-tag (three
  word sub-tags, two separators) IS a locale prefix, whereas a longer run with
  three or more separators is NOT.

Paths are modelled as ``List[int]`` of Unicode code points (Nagini bans ``str``
indexing); the specification is carried by ``PSeq[int]`` via ``ToSeq``. The
acceptance/extraction rule above is modelled DEEPLY as front-recursive ``@Pure``
sequence predicates over ONE axiomatized primitive: membership of a single code
point in the "word" character class. That membership test is an unchanged
callee, pinned exactly below code point 128 and left OPEN over the rest of
Unicode, so the extraction rule is claimed for EVERY class the axiom permits
and never for an ASCII-only reading of it. The rule's equality to the real
compiled prefix matcher is checked out-of-band by axiom_check.py (G-AX).

The downstream resolution of the extracted candidate against the configured
locales is an UNCHANGED callee and is documented in mapping.md / refinement.md;
it is not part of the modelled, changed operation (the extraction is).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
@Pure
@ContractOnly
def is_word(c: int) -> bool:
    """Membership of ONE code point in the "word" character class that a locale
    sub-tag's characters are drawn from. This per-code-point class test is an
    UNCHANGED community callee; its provenance and its executable soundness
    check live in mapping.md / axiom_check.py.

    The class is pinned EXACTLY below code point 128: there it is the decimal
    digits, the two cased Latin letter runs, and the low line — and NOTHING
    else below 128 belongs to it (not the space, not the path separator, not a
    sub-tag separator, not a newline, not any other punctuation mark). At and
    above 128 the class is deliberately left OPEN: the real class is evaluated
    over the whole of Unicode, so exactly which further letters and digits it
    admits is the callee's business and is NOT something this specification
    decides. An implementation must therefore agree with the extraction rule
    below for EVERY class this contract permits, rather than for one chosen
    reading of it."""
    Ensures(Implies(c < 128, Result() == ((48 <= c and c <= 57)      # 0-9
                                          or (65 <= c and c <= 90)   # A-Z
                                          or (97 <= c and c <= 122)  # a-z
                                          or c == 95)))              # _
# axioms-end


# pure-start
@Pure
def is_sep(c: int) -> bool:
    """A sub-tag separator: ``"-"`` (45) or ``"@"`` (64)."""
    return c == 45 or c == 64


@Pure
def is_tagchar(c: int) -> bool:
    """A character that may appear inside a locale candidate run: a word code
    point or a sub-tag separator."""
    return is_word(c) or is_sep(c)


@Pure
def run_len(s: PSeq[int]) -> int:
    """Length of the maximal leading run of candidate characters (word or
    separator). Front-recursive: one unfold per step. The candidate run starts
    at the front of ``s`` and stops at the first character that may not appear
    in a locale candidate (e.g. ``"/"`` or any other punctuation)."""
    Ensures(0 <= Result() and Result() <= len(s))
    if len(s) == 0:
        return 0
    if not is_tagchar(s[0]):
        return 0
    return 1 + run_len(s.drop(1))


@Pure
def nsep(s: PSeq[int]) -> int:
    """Number of sub-tag separators in ``s``. Front-recursive."""
    Ensures(Result() >= 0)
    if len(s) == 0:
        return 0
    return (1 if is_sep(s[0]) else 0) + nsep(s.drop(1))


@Pure
def no_adjacent_sep(s: PSeq[int]) -> bool:
    """No two adjacent separators in ``s`` (every separator is immediately
    followed by another character that is not a separator). Front-recursive."""
    if len(s) <= 1:
        return True
    return not (is_sep(s[0]) and is_sep(s[1])) and no_adjacent_sep(s.drop(1))


@Pure
def well_formed_tag(t: PSeq[int]) -> bool:
    """``t`` is a well-formed sequence of word sub-tags joined by single
    separators: non-empty, begins and ends with a word code point, and has no
    two adjacent separators. (``t`` is assumed to consist only of candidate
    characters; the caller guarantees this via ``run_len``.)"""
    return (len(t) > 0
            and is_word(t[0])
            and is_word(t[len(t) - 1])
            and no_adjacent_sep(t))


@Pure
def spec_unfold(path: PSeq[int], maxsep: int, r: int) -> int:
    """One-level body of the locale-prefix decision, with the candidate run
    length ``r`` supplied explicitly (``r == run_len(path.drop(1))``). Given the
    path begins with ``"/"``, the candidate of length ``r`` is accepted iff it
    is non-empty, a well-formed tag, within the separator budget, and terminated
    by ``"/"``, end-of-path, or a trailing FINAL newline (Python-``re`` ``$``);
    the accepted length is ``r`` else ``-1``."""
    Requires(0 <= r and r <= len(path) - 1 if len(path) >= 1 else True)
    Ensures(Result() == -1 or Result() == r)
    body = path.drop(1)
    if r == 0:
        return -1
    tag = body.take(r)
    if not well_formed_tag(tag):
        return -1
    if nsep(tag) > maxsep:
        return -1
    # termination: end of path, the next character is "/", or the next
    # character is a newline (10) that is the LAST character of the path
    # (Python-re `$` also matches just before a trailing final newline).
    if r == len(body):
        return r
    if body[r] == 47:
        return r
    if body[r] == 10 and r == len(body) - 1:
        return r
    return -1


@Pure
def prefix_len_spec(path: PSeq[int], maxsep: int) -> int:
    """Length of the accepted locale candidate at the front of ``path`` under a
    separator budget ``maxsep``, or ``-1`` when there is no acceptable locale
    prefix. The path must begin with ``"/"`` (47); the candidate is the maximal
    run after it (``run_len``); it must be a well-formed tag with at most
    ``maxsep`` separators; and the run must be terminated by ``"/"`` (47),
    end-of-path, or a newline (10) that is the path's final character
    (Python-``re`` ``$``)."""
    Ensures(Result() == -1 or Result() >= 1)
    if len(path) == 0 or path[0] != 47:
        return -1
    return spec_unfold(path, maxsep, run_len(path.drop(1)))
# pure-end


def language_prefix_len(path: List[int]) -> int:
    # pre-conditions-start
    Requires(Acc(list_pred(path), 1 / 2))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(path), 1 / 2))
    # The extracted locale-prefix length is exactly the deep structural parse
    # with a budget of TWO sub-tag separators (primary + script + region).
    Ensures(Result() == prefix_len_spec(ToSeq(path), 2))
    # Grounding: either no prefix (-1), or a positive length within the path.
    Ensures(Result() == -1 or (1 <= Result() and Result() <= len(path) - 1))
    # post-conditions-end
    # impl-start
    n = len(path)
    if n == 0:
        Assert(len(ToSeq(path)) == 0)
        return -1
    Assert(ToSeq(path)[0] == path[0])
    if path[0] != 47:
        return -1
    if n == 1:
        # body == path.drop(1) is empty: no candidate run.
        Assert(len(ToSeq(path).drop(1)) == 0)
        Assert(run_len(ToSeq(path).drop(1)) == 0)
        Assert(prefix_len_spec(ToSeq(path), 2) == -1)
        return -1
    # body == path.drop(1) has length n-1; scan it from the back,
    # reconstructing run_len(body.drop(i)) over each suffix.
    body_len = n - 1
    rlen = 0          # run_len(body.drop(i)); body.drop(body_len) is empty
    i = body_len      # index into body == path.drop(1)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(path), 1 / 2))
        Invariant(n == len(path))
        Invariant(n >= 2 and path[0] == 47)
        Invariant(body_len == n - 1)
        Invariant(0 <= i and i <= body_len)
        Invariant(rlen == run_len(ToSeq(path).drop(1).drop(i)))
        Invariant(0 <= rlen and rlen <= body_len - i)
        Invariant(MustTerminate(i + 1))
        # invariants-end
        # body[i-1] == path[1 + (i-1)] == path[i]
        c = path[i]
        Assert(ToSeq(path).drop(1).drop(i - 1)[0] == c)
        Assert(ToSeq(path).drop(1).drop(i - 1).drop(1)
               == ToSeq(path).drop(1).drop(i))
        if is_tagchar(c):
            rlen = rlen + 1
        else:
            rlen = 0
        i = i - 1
    Assert(ToSeq(path).drop(1).drop(0) == ToSeq(path).drop(1))
    Assert(rlen == run_len(ToSeq(path).drop(1)))
    if rlen == 0:
        Assert(prefix_len_spec(ToSeq(path), 2) == -1)
        return -1
    # tag == body.take(rlen); check well-formedness + separator budget by a
    # second backward pass over the tag.
    Assert(rlen <= body_len)
    Assert(ToSeq(path).drop(1).take(rlen)
           == ToSeq(path).drop(1).take(rlen))
    tseps = 0         # nsep over tag suffix
    adj_ok = True     # no_adjacent_sep over tag suffix
    j = rlen
    while j > 0:
        # invariants-start
        Invariant(Acc(list_pred(path), 1 / 2))
        Invariant(n == len(path))
        Invariant(n >= 2 and path[0] == 47)
        Invariant(rlen == run_len(ToSeq(path).drop(1)))
        Invariant(0 <= j and j <= rlen)
        Invariant(rlen <= n - 1)
        Invariant(tseps == nsep(ToSeq(path).drop(1).take(rlen).drop(j)))
        Invariant(adj_ok == no_adjacent_sep(ToSeq(path).drop(1).take(rlen).drop(j)))
        Invariant(MustTerminate(j + 1))
        # invariants-end
        # element body[j-1] == path[1 + (j-1)] == path[j]
        Assert(ToSeq(path).drop(1).take(rlen).drop(j - 1)[0] == path[j])
        Assert(ToSeq(path).drop(1).take(rlen).drop(j - 1).drop(1)
               == ToSeq(path).drop(1).take(rlen).drop(j))
        c2 = path[j]
        if is_sep(c2):
            tseps = tseps + 1
        # adjacency: body[j-1] and body[j] both seps?
        if j < rlen:
            if is_sep(c2) and is_sep(path[j + 1]):
                adj_ok = False
        j = j - 1
    Assert(ToSeq(path).drop(1).take(rlen).drop(0)
           == ToSeq(path).drop(1).take(rlen))
    Assert(tseps == nsep(ToSeq(path).drop(1).take(rlen)))
    Assert(adj_ok == no_adjacent_sep(ToSeq(path).drop(1).take(rlen)))
    # well-formedness: starts/ends with a word code point.
    Assert(ToSeq(path).drop(1).take(rlen)[0] == path[1])
    Assert(ToSeq(path).drop(1).take(rlen)[rlen - 1] == path[rlen])
    starts_word = is_word(path[1])
    ends_word = is_word(path[rlen])
    if not (starts_word and ends_word and adj_ok):
        Assert(not well_formed_tag(ToSeq(path).drop(1).take(rlen)))
        Assert(prefix_len_spec(ToSeq(path), 2) == -1)
        return -1
    Assert(well_formed_tag(ToSeq(path).drop(1).take(rlen)))
    # Bind the spec's internal facts: same body, same run length, well-formed,
    # and the separator budget.
    Assert(len(ToSeq(path).drop(1)) == body_len)
    Assert(run_len(ToSeq(path).drop(1)) == rlen)
    Assert(nsep(ToSeq(path).drop(1).take(rlen)) == tseps)
    if tseps > 2:
        Assert(prefix_len_spec(ToSeq(path), 2) == -1)
        return -1
    Assert(nsep(ToSeq(path).drop(1).take(rlen)) <= 2)
    # Definitional unfold of prefix_len_spec, with run_len(body) bound to rlen:
    # one level of the (non-recursive) spec body, expressed in the same
    # sub-calls the impl loops established.
    Assert(len(ToSeq(path)) > 0)
    Assert(ToSeq(path)[0] == path[0])
    Assert(ToSeq(path)[0] == 47)
    Assert(run_len(ToSeq(path).drop(1)) == rlen)
    Assert(0 <= rlen and rlen <= len(ToSeq(path)) - 1)
    spec_val = spec_unfold(ToSeq(path), 2, rlen)
    Assert(prefix_len_spec(ToSeq(path), 2) == spec_val)
    # termination: end-of-body, the next character is "/", or a newline (10)
    # that is the final character of the path (Python-re `$` semantics).
    if rlen == body_len:
        Assert(rlen == len(ToSeq(path).drop(1)))
        Assert(spec_val == rlen)
        return rlen
    Assert(rlen < len(ToSeq(path).drop(1)))
    Assert(ToSeq(path).drop(1)[rlen] == path[rlen + 1])
    if path[rlen + 1] == 47:
        Assert(ToSeq(path).drop(1)[rlen] == 47)
        Assert(spec_val == rlen)
        return rlen
    if path[rlen + 1] == 10 and rlen == body_len - 1:
        Assert(ToSeq(path).drop(1)[rlen] == 10)
        Assert(rlen == len(ToSeq(path).drop(1)) - 1)
        Assert(spec_val == rlen)
        return rlen
    Assert(ToSeq(path).drop(1)[rlen] != 47)
    Assert(not (ToSeq(path).drop(1)[rlen] == 10
                and rlen == len(ToSeq(path).drop(1)) - 1))
    Assert(spec_val == -1)
    return -1
    # impl-end
