"""Twin-artifact model for django__django-15127.

Behaviour under specification (an abstract behavioural contract over the
function's inputs, NOT an edit or a diagnosis):

  A per-level tag mapping assigns, to each integer message level, the tag token
  to display for that level. It is derived from two value sources: a constant
  family of DEFAULT tags (one per built-in level) overlaid with a configurable
  OVERRIDE mapping. The derived mapping is exactly the default family with the
  override mapping merged on top -- per level: the override's value where the
  override carries the level, otherwise the default's value, and a level
  neither carries is absent.

  The function takes an identifier selecting which setting's value this call
  concerns (``setting``), the current override mapping (``override``), the
  default family (``defaults``), and the mapping presently in force
  (``current``); it returns the per-level mapping that should be in force given
  that input. The contract on the returned mapping, per level:

    * if the identifier is the message-tags identifier, the result equals the
      override merged onto the defaults (override wins where it carries the
      level, else the default value; a level only the override provides is
      present with the override's token, including a custom level the defaults
      never had);
    * if the identifier is any other identifier, the result equals the
      mapping presently in force, level for level.

  The level-tag read of a level is the mapping's token for that level if
  present, otherwise the empty tag token. The behaviour the contract pins:
  under the message-tags identifier, reading a level the override provides
  returns the override's token (not a stale value, and not the empty token for
  a custom level the defaults never had).

Modelling choices (Nagini fragment):
  * A tags mapping is observed only by membership-and-value at the levels that
    discriminate the behaviour: a built-in level the override re-tags, a
    built-in level the override omits, and a custom level the defaults never
    had. It is carried as a small record of ``Optional[int]`` slots (one per
    representative level; ``None`` = the level is absent from the mapping, else
    the tag token). This is the faithful finite abstraction of the real
    ``Dict[int, str]`` keyed by level (mapping.md §2) -- the merge and the
    read are pinned pointwise on each slot, so only the intended mapping
    satisfies the contract.
  * The mapping merge ``{**defaults, **override}`` is modelled DEEPLY (the
    per-slot override-wins choice spelled out in ``merge_slot``); the real
    Python merge is validated against this model out-of-band (axiom_check.py,
    G-AX, A-reference). The per-level derivation under the message-tags
    identifier is the impl region.
  * The level-tag read ``mapping.get(level, '')`` is the unchanged pure helper
    ``read_slot`` (a present slot reads its tag, an absent slot the empty tag).

The function allocates a fresh merged record and never writes its inputs, so
the read-only mapping records are immutable value carriers (their slots are
plain integers, no heap permission needed). Markers (machine-parsed) delimit
the spec / proof / impl regions.
"""
from typing import Optional
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (No @ContractOnly axioms consumed: the merge primitive is modelled deeply as
#  the pure record-level merge below and validated against real Python by G-AX.)
# axioms-end


# pure-start
class Tags:
    """A tags mapping observed at the three discriminating levels. Each slot is
    ``Optional[int]``: ``None`` means the level is absent from the mapping,
    otherwise the slot holds the level's tag token. An immutable value carrier.
    """

    def __init__(self, a: Optional[int], b: Optional[int], c: Optional[int]) -> None:
        # Level 1: this constructor is loop-free and calls nothing obligated, so
        # it sits at the bottom of the obligation order. Every obligated caller
        # that allocates a result record must be at a strictly greater level.
        Requires(MustTerminate(1))
        Ensures(Acc(self.a) and self.a is a)  # type: ignore
        Ensures(Acc(self.b) and self.b is b)  # type: ignore
        Ensures(Acc(self.c) and self.c is c)  # type: ignore
        self.a = a  # built-in level the override re-tags
        self.b = b  # built-in level the override omits
        self.c = c  # custom level the defaults never had


@Pure
def setting_message_tags() -> int:
    # The token of the message-tags override setting (the one setting whose
    # change must re-derive the mapping). Any other token denotes a different
    # setting whose change leaves the mapping unchanged.
    return 1


@Pure
def empty_tag() -> int:
    # The empty tag token returned for a level the derived mapping lacks.
    return 0


@Pure
def slot_present(slot: Optional[int]) -> bool:
    # A slot denotes a present level iff it is not None.
    return slot is not None


@Pure
def read_slot(slot: Optional[int]) -> int:
    """The level-tag read of one slot (unchanged ``.get(level, '')``): the
    slot's tag token if the level is present, otherwise the empty tag token."""
    if slot is None:
        return empty_tag()
    return slot


@Pure
def merge_slot(d: Optional[int], o: Optional[int]) -> Optional[int]:
    """The per-level mapping merge ``{**defaults, **override}`` on one slot: the
    override's value wins where the override carries the level, otherwise the
    default's value. (Modelled deeply; validated == real Python by G-AX.)"""
    if o is not None:
        return o
    return d
# pure-end


def derive_tags_for_setting(setting: int, override: Tags,
                            defaults: Tags, current: Tags) -> Tags:
    # ``setting`` is an identifier selecting which setting's value this call
    # concerns (it equals ``setting_message_tags()`` when it concerns the
    # message-tags identifier, any other value otherwise).
    # pre-conditions-start
    # The three mapping records are read-only value carriers (immutable slots).
    Requires(Acc(override.a, 1 / 2) and Acc(override.b, 1 / 2) and Acc(override.c, 1 / 2))
    Requires(Acc(defaults.a, 1 / 2) and Acc(defaults.b, 1 / 2) and Acc(defaults.c, 1 / 2))
    Requires(Acc(current.a, 1 / 2) and Acc(current.b, 1 / 2) and Acc(current.c, 1 / 2))
    Requires(MustTerminate(6))
    # pre-conditions-end
    # post-conditions-start
    # Inputs returned untouched at the same half permission.
    Ensures(Acc(override.a, 1 / 2) and Acc(override.b, 1 / 2) and Acc(override.c, 1 / 2))
    Ensures(Acc(defaults.a, 1 / 2) and Acc(defaults.b, 1 / 2) and Acc(defaults.c, 1 / 2))
    Ensures(Acc(current.a, 1 / 2) and Acc(current.b, 1 / 2) and Acc(current.c, 1 / 2))
    # A fresh, full-permission result mapping (when derived from the merge) or
    # the unchanged in-force mapping; both yield full read access on the
    # result's slots.
    Ensures(Acc(Result().a) and Acc(Result().b) and Acc(Result().c))
    Ensures(Result() is not None)
    # Under the message-tags identifier the result equals the override merged
    # onto the defaults, pinned uniformly per level (override wins where it
    # carries the level, else the default value carries -- the merge_slot
    # primitive). This single clause per slot closes every merge case:
    #   * a built-in level the override re-tags -> the override's token;
    #   * a built-in level the override omits -> the default value survives;
    #   * a custom level only the override provides -> present with the
    #     override token (so the level-tag read is NOT the empty token).
    Ensures(Implies(setting == setting_message_tags(),
                    Result().a is merge_slot(defaults.a, override.a)))
    Ensures(Implies(setting == setting_message_tags(),
                    Result().b is merge_slot(defaults.b, override.b)))
    Ensures(Implies(setting == setting_message_tags(),
                    Result().c is merge_slot(defaults.c, override.c)))
    # The discriminating level-tag read (the unchanged ``.get(level, '')``): on
    # the result of the message-tags derivation, a level the override provides
    # reads the override's token, not the empty token.
    Ensures(Implies(setting == setting_message_tags() and slot_present(override.c),
                    read_slot(Result().c) == read_slot(override.c)))
    # Under any other identifier the result equals the in-force mapping, level
    # for level.
    Ensures(Implies(setting != setting_message_tags(),
                    Result().a is current.a
                    and Result().b is current.b
                    and Result().c is current.c))
    # post-conditions-end
    # impl-start
    if setting == setting_message_tags():
        return Tags(merge_slot(defaults.a, override.a),
                    merge_slot(defaults.b, override.b),
                    merge_slot(defaults.c, override.c))
    # Under any other identifier the result equals the in-force mapping: the
    # returned record holds the same level-for-level slot values as ``current``
    # (observationally the same mapping).
    return Tags(current.a, current.b, current.c)
    # impl-end
