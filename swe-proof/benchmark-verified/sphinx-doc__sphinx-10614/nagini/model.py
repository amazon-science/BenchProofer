"""Twin-artifact model for sphinx-doc__sphinx-10614.

Behaviour under specification (stated as desired behaviour, not as an edit):

A clickable inheritance diagram is emitted in one of two image formats, and the
format decides what the links inside the image are resolved against:

  * a raster image with a clickable area map written into the page itself, so
    its links resolve relative to the document being rendered;
  * a vector image embedded into the page through an indirection, so its links
    resolve relative to the image's own location -- the image directory, one
    level below the document tree root.

The hyperlink target attached to each class node must be the link that resolves
correctly from whichever of those two embedding contexts applies, so the image
format is an input to the clauses below and each clause says what happens in
BOTH formats.

  (1) A cross-reference whose target is given by an explicit destination URI
      (a document-relative path, possibly with an anchor, or an absolute
      URL) maps to that destination URI itself, in EITHER image format: this
      link does not depend on the format. No extra leading path segment is
      added in either format -- the URI is already the correct target as seen
      from the image directory, and as seen from the document. In particular
      an absolute URL (containing a scheme separator "://") is preserved
      verbatim, beginning with its scheme; it is never turned into a relative
      path, in either format.

  (2) A cross-reference whose target is an anchor in the document currently
      being rendered maps, for a vector image, to that document's own output
      name followed by "#" and the anchor identifier -- naming the document is
      what makes the anchor reachable from the image directory. For a raster
      image, whose links already resolve against that same document, it maps
      to "#" and the anchor identifier alone. No extra leading path segment is
      added in either format.

  (3) A link of the shape <location>#<identifier> designates the class the
      identifier names. So where a class must be identified from an explicit
      destination URI alone, its identifier is the part of that URI after the
      final "#" (a URI with no "#" is its own identifier). Identification is a
      property of the link text, so it does not depend on the image format
      either.

Strings are modelled as `List[int]` of Unicode code points (Nagini bans `str`
indexing); the specification is carried by `PSeq[int]` via `ToSeq`. The image
format is modelled by the boolean `vector_format` (True for the vector image,
False for the raster one). There are no axiomatized callees: every modelled
operation is plain sequence arithmetic.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# axioms-end


# pure-start
@Pure
def is_scheme_sep_at(s: PSeq[int], i: int) -> bool:
    """True iff positions i, i+1, i+2 of s spell the scheme separator "://"
    (a colon U+003A followed by two slashes U+002F)."""
    return (0 <= i and i + 2 < len(s)
            and s[i] == 58 and s[i + 1] == 47 and s[i + 2] == 47)


@Pure
def has_scheme(s: PSeq[int]) -> bool:
    """True iff s contains an absolute-URL scheme separator "://" somewhere.
    Front-recursive so a single unfold is available per scanned position."""
    if len(s) == 0:
        return False
    if is_scheme_sep_at(s, 0):
        return True
    return has_scheme(s.drop(1))


@Pure
def after_last_hash(s: PSeq[int]) -> PSeq[int]:
    """The part of s after its final "#" (U+0023): the suffix that begins
    one past the final "#"; if s has no "#", it is s unchanged.
    Front-recursive (peels the leading element), so a single unfold is
    available per scanned position. Reading: the answer for s is the answer
    for s.drop(1) whenever that tail already contains a "#"; otherwise it is
    s itself when s[0] is not "#", or s.drop(1) when s[0] is "#"."""
    if len(s) == 0:
        return s
    tail = after_last_hash(s.drop(1))
    if len(tail) < len(s) - 1:
        # s.drop(1) contained a "#": the tail's answer dominates
        return tail
    if s[0] == 35:
        return s.drop(1)
    return s
# pure-end


def url_for_destination(dest_uri: List[int], vector_format: bool) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(dest_uri), 1 / 2))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(dest_uri), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The emitted link is the destination URI itself. Stated for an arbitrary
    # `vector_format`, so it holds for BOTH image formats: this link is the
    # same in both, and no extra leading path segment is added in either.
    Ensures(ToSeq(Result()) == ToSeq(dest_uri))
    # Hence an absolute URL keeps its scheme in both formats: the result
    # preserves the scheme separator membership of the input.
    Ensures(has_scheme(ToSeq(dest_uri)) == has_scheme(ToSeq(Result())))
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    i = 0
    while i < len(dest_uri):
        # invariants-start
        Invariant(Acc(list_pred(dest_uri), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(dest_uri))
        Invariant(ToSeq(result) == ToSeq(dest_uri).take(i))
        Invariant(MustTerminate(len(dest_uri) - i + 1))
        # invariants-end
        old_seq = ToSeq(result)
        result.append(dest_uri[i])
        Assert(ToSeq(result) == old_seq + PSeq(dest_uri[i]))
        Assert(ToSeq(dest_uri).take(i) + PSeq(ToSeq(dest_uri)[i]) == ToSeq(dest_uri).take(i + 1))
        i = i + 1
    Assert(ToSeq(dest_uri).take(len(dest_uri)) == ToSeq(dest_uri))
    return result
    # impl-end


def url_for_self_doc_anchor(current_doc_name: List[int], anchor_id: List[int],
                            vector_format: bool) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(current_doc_name), 1 / 2))
    Requires(Acc(list_pred(anchor_id), 1 / 2))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(current_doc_name), 1 / 2))
    Ensures(Acc(list_pred(anchor_id), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # For a vector image the link is this document's own output name, then "#",
    # then the anchor identifier. No extra leading path segment.
    Ensures(Implies(vector_format,
                    ToSeq(Result())
                    == ToSeq(current_doc_name) + PSeq(35) + ToSeq(anchor_id)))
    # The link therefore begins with the current document's name.
    Ensures(Implies(vector_format,
                    ToSeq(Result()).take(len(current_doc_name))
                    == ToSeq(current_doc_name)))
    # For a raster image the link is "#" and the anchor identifier alone: the
    # document's own name is NOT put in front of it, and neither is anything
    # else -- the anchor already resolves against that document.
    Ensures(Implies(not vector_format,
                    ToSeq(Result()) == PSeq(35) + ToSeq(anchor_id)))
    # post-conditions-end
    # impl-start
    if not vector_format:
        # Raster image: "#" then the anchor identifier.
        bare = [35]  # type: List[int]
        m = 0
        while m < len(anchor_id):
            # invariants-start
            Invariant(Acc(list_pred(anchor_id), 1 / 2))
            Invariant(Acc(list_pred(bare)))
            Invariant(0 <= m and m <= len(anchor_id))
            Invariant(ToSeq(bare) == PSeq(35) + ToSeq(anchor_id).take(m))
            Invariant(MustTerminate(len(anchor_id) - m + 1))
            # invariants-end
            old_bare = ToSeq(bare)
            bare.append(anchor_id[m])
            Assert(ToSeq(bare) == old_bare + PSeq(anchor_id[m]))
            Assert(ToSeq(anchor_id).take(m) + PSeq(ToSeq(anchor_id)[m]) == ToSeq(anchor_id).take(m + 1))
            m = m + 1
        Assert(ToSeq(anchor_id).take(len(anchor_id)) == ToSeq(anchor_id))
        Assert(ToSeq(bare) == PSeq(35) + ToSeq(anchor_id))
        return bare
    result = []  # type: List[int]
    i = 0
    while i < len(current_doc_name):
        # invariants-start
        Invariant(Acc(list_pred(current_doc_name), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(current_doc_name))
        Invariant(ToSeq(result) == ToSeq(current_doc_name).take(i))
        Invariant(MustTerminate(len(current_doc_name) - i + 1))
        # invariants-end
        old_seq = ToSeq(result)
        result.append(current_doc_name[i])
        Assert(ToSeq(result) == old_seq + PSeq(current_doc_name[i]))
        Assert(ToSeq(current_doc_name).take(i) + PSeq(ToSeq(current_doc_name)[i])
               == ToSeq(current_doc_name).take(i + 1))
        i = i + 1
    Assert(ToSeq(current_doc_name).take(len(current_doc_name)) == ToSeq(current_doc_name))
    cf_seq = ToSeq(current_doc_name)  # frozen carrier of the prefix
    Assert(ToSeq(result) == cf_seq)
    result.append(35)  # '#'
    Assert(ToSeq(result) == cf_seq + PSeq(35))
    j = 0
    while j < len(anchor_id):
        # invariants-start
        Invariant(Acc(list_pred(current_doc_name), 1 / 2))
        Invariant(Acc(list_pred(anchor_id), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= j and j <= len(anchor_id))
        Invariant(ToSeq(current_doc_name) == cf_seq)
        Invariant(ToSeq(result) == cf_seq + PSeq(35) + ToSeq(anchor_id).take(j))
        Invariant(MustTerminate(len(anchor_id) - j + 1))
        # invariants-end
        old_seq2 = ToSeq(result)
        result.append(anchor_id[j])
        Assert(ToSeq(result) == old_seq2 + PSeq(anchor_id[j]))
        Assert(ToSeq(anchor_id).take(j) + PSeq(ToSeq(anchor_id)[j]) == ToSeq(anchor_id).take(j + 1))
        j = j + 1
    Assert(ToSeq(anchor_id).take(len(anchor_id)) == ToSeq(anchor_id))
    Assert(ToSeq(result) == cf_seq + PSeq(35) + ToSeq(anchor_id))
    return result
    # impl-end


def trailing_name_for_destination(dest_uri: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(dest_uri), 1 / 2))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(dest_uri), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The identifier a destination URI names is the part of it after the
    # final "#". There is no image-format parameter: identification is the
    # same operation for either format.
    Ensures(ToSeq(Result()) == after_last_hash(ToSeq(dest_uri)))
    # post-conditions-end
    # impl-start
    # Scan backward for the last '#'. `start` indexes the beginning of the
    # trailing component; the invariant ties it to the front-recursive
    # `after_last_hash` via one unfold per step.
    start = len(dest_uri)
    i = len(dest_uri)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(dest_uri), 1 / 2))
        Invariant(0 <= i and i <= start and start <= len(dest_uri))
        Invariant(ToSeq(dest_uri).drop(start) == after_last_hash(ToSeq(dest_uri).drop(i)))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        # Unfold after_last_hash at index i-1: drop(i-1) == [dest_uri[i-1]] ++ drop(i)
        Assert(ToSeq(dest_uri).drop(i - 1) == PSeq(ToSeq(dest_uri)[i - 1]) + ToSeq(dest_uri).drop(i))
        Assert(ToSeq(dest_uri).drop(i - 1).drop(1) == ToSeq(dest_uri).drop(i))
        Assert(ToSeq(dest_uri).drop(i - 1)[0] == ToSeq(dest_uri)[i - 1])
        if dest_uri[i - 1] == 35 and start == i:
            # no '#' seen yet to the right, and this is one: trailing starts here
            start = i
        elif start == i and dest_uri[i - 1] != 35:
            # still no '#' to the right and this char is ordinary: extend left
            start = i - 1
        # else: a '#' already dominates to the right; `start` is unchanged
        i = i - 1
    Assert(ToSeq(dest_uri).drop(0) == ToSeq(dest_uri))
    Assert(ToSeq(dest_uri).drop(start) == after_last_hash(ToSeq(dest_uri)))
    result = []  # type: List[int]
    k = start
    while k < len(dest_uri):
        # invariants-start
        Invariant(Acc(list_pred(dest_uri), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= start and start <= k and k <= len(dest_uri))
        Invariant(ToSeq(dest_uri).drop(start) == after_last_hash(ToSeq(dest_uri)))
        Invariant(ToSeq(result) == ToSeq(dest_uri).drop(start).take(k - start))
        Invariant(MustTerminate(len(dest_uri) - k + 1))
        # invariants-end
        old_seq = ToSeq(result)
        result.append(dest_uri[k])
        Assert(ToSeq(result) == old_seq + PSeq(dest_uri[k]))
        Assert(ToSeq(dest_uri).drop(start)[k - start] == ToSeq(dest_uri)[k])
        Assert(ToSeq(dest_uri).drop(start).take(k - start) + PSeq(ToSeq(dest_uri).drop(start)[k - start])
               == ToSeq(dest_uri).drop(start).take(k - start + 1))
        k = k + 1
    Assert(ToSeq(result) == ToSeq(dest_uri).drop(start).take(len(dest_uri) - start))
    Assert(ToSeq(dest_uri).drop(start).take(len(dest_uri) - start) == ToSeq(dest_uri).drop(start))
    Assert(ToSeq(result) == ToSeq(dest_uri).drop(start))
    Assert(ToSeq(dest_uri).drop(start) == after_last_hash(ToSeq(dest_uri)))
    Assert(ToSeq(result) == after_last_hash(ToSeq(dest_uri)))
    return result
    # impl-end
