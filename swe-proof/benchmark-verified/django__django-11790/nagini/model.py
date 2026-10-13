"""Twin-artifact model for django__django-11790.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When the login form for a user model is prepared, the identifier-input field
  is configured with a length limit derived from the user model's identifier
  column: the model's declared maximum length when it declares a usable one,
  and a default limit of 254 when the model declares no maximum -- or declares
  one that conveys no usable length at all. That same resolved
  limit must be reflected in TWO places that downstream consumers read:

    (1) the field-level length limit used for server-side validation, and
    (2) the rendered input widget's length-limit attribute, under the
        dedicated attribute name a browser honours to cap typed input.

  Both must carry exactly the resolved limit. Any widget attributes already
  configured on the input (for example focus or autocomplete hints) are
  preserved unchanged; only the length-limit attribute is established.

  The attribute the limit is published under is what makes it effective: a
  renderer emits the browser-honoured cap by looking the limit up under that
  one dedicated attribute name and no other. Publishing the right number under
  some other attribute name leaves the rendered input with no cap at all, which
  is indistinguishable from never having published it.

  This configuration is UNCONDITIONAL: it happens the same way whatever the
  input widget already carries. If the widget already advertises a length limit
  of its own, the resolved limit replaces it, so the rendered cap and the
  server-side cap can never disagree; if the widget carries no other attributes
  at all, none are invented. No starting state is exempt, so the behaviour may
  not vary with what the widget happened to be configured with.

Modelling choices (Nagini fragment):
  * The model's declared maximum length is an ``Optional[int]``: ``None`` means
    "no declared maximum"; a declared maximum of zero likewise conveys no
    usable length. Both resolve to the default 254; any other declared maximum
    is used verbatim. The resolution mirrors the repo's
    "declared-maximum-or-default" expression, which selects the default for
    every unusable declared maximum alike (mapping.md §2).
  * The widget's attribute mapping is a ``Dict[str, object]`` from an
    attribute NAME to its value. Both of its domains are deliberately
    non-arithmetic, and for the same reason -- neither a name nor a stored
    value is a quantity in the repository:

      - An attribute NAME is TEXTUAL. It is carried as the text it actually is,
        so a name and a LENGTH inhabit disjoint domains and no length may ever
        be mistaken for, or arithmetically built into, an attribute name. A
        name may only be written down or compared for equality. This is what
        makes the carrier faithful on the name axis: were names carried as
        numbers, a number computed out of the length domain could coincide with
        the dedicated attribute name in the model while denoting a completely
        different attribute in the repository, and the model would then be
        unable to see the difference between publishing the limit under the
        attribute a browser honours and publishing it under an unrelated one
        (mapping.md §2).
      - An attribute VALUE is of MIXED kinds: a length limit is a number, but a
        focus or autocomplete hint is not, so the value domain is opaque.
        Nothing may be computed from a value read out of the mapping -- it may
        only be compared, or carried over verbatim (mapping.md §2). The length
        limit's own value is stated through ``limit_value``, the injection of a
        number into that opaque domain.

The widget attribute mapping is genuinely mutated in place (the length-limit
attribute is added to it), so it is held at full permission and its exact
post-state is stated. The field-level limit is returned.

No string indexing is used (Nagini bans it): attribute names are only written
down, compared, and used as keys. The behaviour is modelled deeply (the
resolution and the two writes are spelled out in the impl region); there is no
axiomatised callee. Markers (machine-parsed) delimit the spec / proof / impl
regions.
"""
from typing import Dict, Optional
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# No axioms: the field/widget configuration is the behaviour under
# specification and is spelled out deeply in the impl region. There is no
# unchanged opaque callee to axiomatise.
# axioms-end


# pure-start
@Pure
def default_limit() -> int:
    # The length limit used when the user model declares no maximum. A LENGTH,
    # i.e. a quantity -- never an attribute name.
    return 254


@Pure
def attr_maxlength() -> str:
    # The dedicated widget attribute NAME under which the rendered length limit
    # is published, and the only name a browser honours to cap typed input. A
    # name is textual, so it shares no domain with any length: it can be
    # written down and compared, and cannot be arrived at by computing with
    # numbers.
    return 'maxlength'


@Pure
def attr_other() -> str:
    # A representative pre-existing, unrelated widget attribute NAME (e.g. a
    # focus or autocomplete hint already configured on the input widget). It
    # witnesses that the operation leaves other attributes untouched.
    return 'autofocus'


@Pure
def limit_value(limit: int) -> object:
    # The resolved length limit as it sits among the widget's attribute values.
    # The attribute mapping carries values of mixed kinds (a length limit is a
    # number, whereas a focus or autocomplete hint is not), so a value read out
    # of the mapping is only ever compared or carried over verbatim; this
    # injection is what lets the length limit's value be stated at all.
    return limit


@Pure
def resolve_limit(declared: Optional[int]) -> int:
    """The resolved length limit. A declared maximum that is absent -- and
    equally one that is zero, i.e. no usable length -- resolves to the default
    limit; any other declared maximum is used verbatim. Mirrors the repo's
    declared-or-default expression, which treats an unusable declared maximum
    exactly as it treats an absent one."""
    if declared is None:
        return default_limit()
    if declared == 0:
        return default_limit()
    return declared
# pure-end


def configure_username_field(declared_max_length: Optional[int],
                             widget_attrs: Dict[str, object]) -> int:
    # pre-conditions-start
    # The widget attribute mapping is mutated in place; full permission.
    Requires(dict_pred(widget_attrs))
    # NO restriction on what the widget already carries. The operation is TOTAL
    # over starting states: it is required to behave the same way whether or
    # not a length-limit attribute is already configured on the widget, and
    # whether or not any other attribute is. (A caller that prepares the input
    # widget differently -- with a length limit of its own, or with nothing at
    # all -- is served identically.)
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(dict_pred(widget_attrs))
    # (1) The returned field-level length limit is the resolved limit.
    Ensures(Result() == resolve_limit(declared_max_length))
    # (2) The widget now publishes the length limit UNDER THE DEDICATED
    #     ATTRIBUTE NAME a browser honours, and it holds exactly the same
    #     resolved limit as the field. This is the clause a renderer reads to
    #     emit the cap, and the name it is published under is part of the
    #     obligation: the limit has to be reachable under THAT name, not merely
    #     stored somewhere in the mapping. It is required in EVERY starting
    #     state: in particular, when the widget already advertised a length
    #     limit of its own, that stale limit is REPLACED by the resolved one
    #     rather than left standing, so the rendered cap and the returned
    #     server-side cap always agree.
    Ensures(attr_maxlength() in widget_attrs)
    Ensures(widget_attrs[attr_maxlength()] == limit_value(resolve_limit(declared_max_length)))
    Ensures(widget_attrs[attr_maxlength()] == limit_value(Result()))
    # Frame: NO widget attribute other than the length-limit attribute
    # changes, again in EVERY starting state. Every other attribute NAME keeps
    # exactly its previous membership (nothing else is added or dropped -- and
    # in particular nothing is invented on a widget that carried no other
    # attribute), and every attribute present before the operation keeps its
    # exact previous value. Together these pin a SINGLE-attribute update: an
    # implementation that publishes the limit under any additional or
    # different attribute name, drops one, or disturbs one is rejected. Since
    # no starting state is excluded, an implementation may not take a shortcut
    # on any of them.
    Ensures(Forall(str, lambda a: (Implies(
        a != attr_maxlength(),
        (a in widget_attrs) == Old(a in widget_attrs)))))
    Ensures(Forall(str, lambda a: (Implies(
        a != attr_maxlength() and Old(a in widget_attrs),
        widget_attrs[a] == Old(widget_attrs[a])))))
    # A representative unrelated attribute -- WHEN the widget already carried
    # one -- keeps its membership and its exact value (a concrete witness of
    # the quantified frame above). When the widget carried none, the
    # obligation is silent about it: the operation does not invent one.
    Ensures(Implies(Old(attr_other() in widget_attrs),
                    attr_other() in widget_attrs))
    Ensures(Implies(Old(attr_other() in widget_attrs),
                    widget_attrs[attr_other()] == Old(widget_attrs[attr_other()])))
    # post-conditions-end
    # impl-start
    username_max_length = resolve_limit(declared_max_length)
    field_max_length = username_max_length
    widget_attrs[attr_maxlength()] = username_max_length
    return field_max_length
    # impl-end
