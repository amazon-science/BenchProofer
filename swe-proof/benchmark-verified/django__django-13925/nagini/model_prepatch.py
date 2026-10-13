"""Twin-artifact model for django__django-13925.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A model's automatic-primary-key advisory is emitted for exactly those models
  whose primary key was created automatically (because no primary-key type was
  declared) AND for which neither the project-wide default-auto-field setting
  nor the owning application's default-auto-field attribute has been
  configured.

  A primary key that a model receives as the inherited stand-in for a concrete
  ancestor's already-declared key is NOT, for this advisory, an automatically
  created key of the model's own: the ancestor's key is the one being checked,
  and it is checked on the ancestor itself. So a key that re-uses such an
  ancestor's declared key does not warrant the advisory on this model.

The pieces of model state the check reads are modelled as a small record with
only the touched fields (whether the key was created automatically, plus the
two independent flags whose conjunction means the key re-uses a concrete
ancestor's already-declared key) together with the two configuration-override
flags. The check's only observable outcome is whether the single advisory is
emitted (modelled as an `int` count, 0 or 1).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


class PkField:
    """The touched fields of the model's primary-key field descriptor."""

    def __init__(self, auto: bool, reuses_ancestor_key_a: bool,
                 reuses_ancestor_key_b: bool) -> None:
        Requires(MustTerminate(1))
        self.auto = auto                                  # key was created automatically
        self.reuses_ancestor_key_a = reuses_ancestor_key_a  # ancestor-key reuse, part A
        self.reuses_ancestor_key_b = reuses_ancestor_key_b  # ancestor-key reuse, part B
        Ensures(Acc(self.auto) and self.auto == auto)
        Ensures(Acc(self.reuses_ancestor_key_a) and
                self.reuses_ancestor_key_a == reuses_ancestor_key_a)
        Ensures(Acc(self.reuses_ancestor_key_b) and
                self.reuses_ancestor_key_b == reuses_ancestor_key_b)


# axioms-start
# (no axiomatized callees: every operation the check performs is a boolean
# field read or a boolean connective, all expressible directly)
# axioms-end


# pure-start
@Pure
def reuses_ancestor_declared_key(auto: bool, reuses_ancestor_key_a: bool,
                                 reuses_ancestor_key_b: bool) -> bool:
    """The key re-uses a concrete ancestor's already-declared key: its value is
    the ancestor's declared key, which is checked on the ancestor itself."""
    return reuses_ancestor_key_a and reuses_ancestor_key_b


@Pure
def advisory_warranted(auto: bool, reuses_ancestor_key_a: bool,
                       reuses_ancestor_key_b: bool,
                       setting_overridden: bool, appconfig_overridden: bool) -> bool:
    """The advisory is warranted exactly for an automatically-created primary
    key that does NOT re-use a concrete ancestor's declared key, with neither
    override configured."""
    return (
        auto and
        not reuses_ancestor_declared_key(auto, reuses_ancestor_key_a,
                                         reuses_ancestor_key_b) and
        not setting_overridden and
        not appconfig_overridden
    )
# pure-end


def check_default_pk(pk: PkField, setting_overridden: bool,
                     appconfig_overridden: bool) -> int:
    # pre-conditions-start
    Requires(Acc(pk.auto, 1 / 2))
    Requires(Acc(pk.reuses_ancestor_key_a, 1 / 2))
    Requires(Acc(pk.reuses_ancestor_key_b, 1 / 2))
    Requires(MustTerminate(6))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(pk.auto, 1 / 2))
    Ensures(Acc(pk.reuses_ancestor_key_a, 1 / 2))
    Ensures(Acc(pk.reuses_ancestor_key_b, 1 / 2))
    # read-only inputs are unchanged
    Ensures(pk.auto == Old(pk.auto))
    Ensures(pk.reuses_ancestor_key_a == Old(pk.reuses_ancestor_key_a))
    Ensures(pk.reuses_ancestor_key_b == Old(pk.reuses_ancestor_key_b))
    # the count is 0 or 1
    Ensures(Result() == 0 or Result() == 1)
    # the advisory is emitted (count 1) iff it is warranted
    Ensures((Result() == 1) ==
            advisory_warranted(pk.auto, pk.reuses_ancestor_key_a,
                               pk.reuses_ancestor_key_b,
                               setting_overridden, appconfig_overridden))
    # post-conditions-end
    # impl-start
    if (
        pk.auto and
        not setting_overridden and
        not appconfig_overridden
    ):
        return 1
    return 0
    # impl-end
