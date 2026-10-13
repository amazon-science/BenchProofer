"""Twin-artifact model for django__django-16801.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When an image-bearing model field is attached to a concrete model class, a
  per-instance post-initialization recalculation hook is registered with that
  class's initialization-completed notification list ONLY when it can ever do
  observable work. The hook recomputes the field's two optional companion
  size-attributes (a width target and a height target) after each instance is
  built. If NEITHER companion target is configured, the hook is a no-op for
  every instance, so it must NOT be registered at all.

  Concretely, registration happens exactly when BOTH hold:
    (a) the owning class is concrete (not an abstract base), AND
    (b) at least one companion target is configured (a non-empty width target
        name OR a non-empty height target name).
  When either condition fails, the notification list is left exactly as it was.

A companion target is modelled as an optional name: absent (None) or a name
whose "configured" truthiness is "present and non-empty". The notification
list is modelled as a `List[int]` of the owning-class identity tokens already
registered; registering appends this class's identity token. The class-identity
token and the two optional target names are read-only inputs; only the
notification list is mutated, and only by the single conditional append.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List, Optional
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# No consumed axioms: the registration decision is pure boolean/structure logic
# over the abstract-flag and the two optional companion-target names, modelled
# deeply. Nothing the proof needs is an unchanged opaque callee.
# axioms-end


# pure-start
@Pure
def configured(name: Optional[List[int]]) -> bool:
    """A companion target is configured iff it is present and non-empty. This
    is the truthiness of an optional target name: an absent name (None) and a
    name with no characters are both unconfigured; any named target counts."""
    Requires(Implies(name is not None, Acc(list_pred(name), 1 / 4)))
    return name is not None and len(name) > 0


@Pure
def should_register(
    is_abstract: bool,
    width_target: Optional[List[int]],
    height_target: Optional[List[int]],
) -> bool:
    """The registration decision: register the recalculation hook exactly when
    the owning class is concrete AND at least one companion target is
    configured."""
    Requires(Implies(width_target is not None, Acc(list_pred(width_target), 1 / 4)))
    Requires(Implies(height_target is not None, Acc(list_pred(height_target), 1 / 4)))
    return (not is_abstract) and (configured(width_target) or configured(height_target))
# pure-end


def attach_post_init_hook(
    receivers: List[int],
    owner_id: int,
    is_abstract: bool,
    width_target: Optional[List[int]],
    height_target: Optional[List[int]],
) -> None:
    # pre-conditions-start
    # The notification list is the single mutated object (full permission).
    Requires(Acc(list_pred(receivers)))
    # The two companion-target names are read-only inputs (fractional read).
    Requires(Implies(width_target is not None, Acc(list_pred(width_target), 1 / 2)))
    Requires(Implies(height_target is not None, Acc(list_pred(height_target), 1 / 2)))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(receivers)))
    Ensures(Implies(width_target is not None, Acc(list_pred(width_target), 1 / 2)))
    Ensures(Implies(height_target is not None, Acc(list_pred(height_target), 1 / 2)))
    # The companion-target names are unchanged (read-only).
    Ensures(Implies(width_target is not None,
                    ToSeq(width_target) == Old(ToSeq(width_target))))
    Ensures(Implies(height_target is not None,
                    ToSeq(height_target) == Old(ToSeq(height_target))))
    # The hook is registered (this owner's identity token is appended to the
    # notification list) EXACTLY when it can ever do observable work: the owner
    # is concrete and at least one companion target is configured. Otherwise the
    # notification list is left exactly as it was.
    Ensures(should_register(is_abstract, width_target, height_target)
            == (ToSeq(receivers) == Old(ToSeq(receivers)) + PSeq(owner_id)))
    Ensures((not should_register(is_abstract, width_target, height_target))
            == (ToSeq(receivers) == Old(ToSeq(receivers))))
    # In particular: a no-op hook (no companion target on a concrete class, or
    # any abstract class) is never registered, so this owner's token is not
    # newly present.
    Ensures(Implies(not should_register(is_abstract, width_target, height_target),
                    len(receivers) == Old(len(receivers))))
    # post-conditions-end
    # impl-start
    if (not is_abstract) and (configured(width_target) or configured(height_target)):
        receivers.append(owner_id)
    # impl-end
