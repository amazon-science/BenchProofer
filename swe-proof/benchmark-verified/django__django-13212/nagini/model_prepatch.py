"""Twin-artifact model for django__django-13212.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When input validation rejects a value, it raises a structured validation
  error carrying a message template together with a mapping of interpolation
  parameters. A consumer may override the template with one that contains a
  named placeholder for the offending input -- the placeholder named ``value``
  -- and the rendered message then interpolates that placeholder against the
  parameter mapping. For the rejected input to be reportable this way, the
  parameter mapping the rejection produces MUST bind the ``value`` placeholder
  to the offending input itself, so that a template consisting of just the
  ``value`` placeholder renders to the string form of that input.

  Two shapes of rejection produce parameter mappings:

    (1) A bare rejection: the parameter mapping it produces binds the ``value``
        placeholder to the offending input, and binds nothing else.

    (2) A rejection that already publishes another named parameter (a numeric
        limit, bound here under the ``limit`` placeholder): the mapping it
        produces binds BOTH that pre-existing parameter to its value AND the
        ``value`` placeholder to the offending input -- the pre-existing binding
        is preserved, not dropped, while the value binding is added.

  In both shapes, rendering the ``value`` placeholder against the produced
  mapping yields the string form of the offending input; in shape (2),
  rendering the pre-existing ``limit`` placeholder still yields the string form
  of its value. This is what lets a custom ``%(value)s`` template surface the
  rejected input regardless of which rejection shape produced the error.

  A further consumer accompanies the offending input with a boolean
  classification bit, ``finite``, recording which of two classes the rejected
  candidate falls in. The behaviour under specification is that this consumer's
  rejection is UNIFORM in that bit: for EITHER value of ``finite`` the parameter
  mapping it produces is a bare rejection's mapping of shape (1) -- it binds the
  ``value`` placeholder to the offending input, and binds nothing else. So a
  custom ``%(value)s`` template surfaces the rejected input whichever class the
  candidate falls in, and neither class contributes a spurious extra binding.

Modelling choices (Nagini fragment):
  * The offending input and the numeric limit are strings, modelled as
    ``List[int]`` of Unicode code points (Nagini bans ``str`` indexing); their
    string form is the identity on code points and is carried by ``PSeq[int]``
    via ``ToSeq`` (mapping.md §2).
  * The parameter mapping is a ``Dict[int, PSeq[int]]`` from a placeholder-name
    token to the string that placeholder renders to. The two placeholder names
    are module-level constant tokens ``placeholder_value()`` and
    ``placeholder_limit()`` (mapping.md §1). Rendering a placeholder is the
    mapping lookup of its name token; membership of a name token models whether
    that placeholder can be rendered at all.

The produced mapping is a freshly built object held at full permission with its
exact membership and per-key contents stated; the read-only inputs are held at
fractional permission. The whole behaviour is modelled deeply (the parameter
mapping is constructed in the impl region); there is no axiomatised callee.
Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Dict, List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# No axioms: the parameter-mapping construction is the behaviour under
# specification and is spelled out deeply in the impl region. There is no
# unchanged opaque callee to axiomatise.
# axioms-end


# pure-start
@Pure
def placeholder_value() -> int:
    """Name token of the placeholder bound to the offending input."""
    return 0


@Pure
def placeholder_limit() -> int:
    """Name token of the placeholder bound to a numeric limit."""
    return 1
# pure-end


def build_invalid_params(value: List[int]) -> Dict[int, PSeq[int]]:
    # pre-conditions-start
    Requires(Acc(list_pred(value), 1 / 2))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(value), 1 / 2))
    Ensures(Acc(dict_pred(Result())))
    Ensures(Result() is not None)
    # The value placeholder is present and renders to the offending input.
    # A bare-rejection error must let a custom value template surface the input.
    Ensures(placeholder_value() in Result())
    Ensures(Result()[placeholder_value()] == ToSeq(value))
    # A bare rejection binds nothing other than the value placeholder.
    Ensures(Forall(int, lambda k: (
        Implies(k in Result(), k == placeholder_value()))))
    # post-conditions-end
    # impl-start
    # Pre-patch: a bare rejection produced no interpolation parameters at all,
    # so the value placeholder is never bound and cannot be rendered.
    params = {}  # type: Dict[int, PSeq[int]]
    return params
    # impl-end


def build_limit_params(value: List[int], limit: List[int]) -> Dict[int, PSeq[int]]:
    # pre-conditions-start
    Requires(Acc(list_pred(value), 1 / 2))
    Requires(Acc(list_pred(limit), 1 / 2))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(value), 1 / 2))
    Ensures(Acc(list_pred(limit), 1 / 2))
    Ensures(Acc(dict_pred(Result())))
    Ensures(Result() is not None)
    # The pre-existing limit binding is preserved: the limit placeholder is
    # still present and still renders to the limit.
    Ensures(placeholder_limit() in Result())
    Ensures(Result()[placeholder_limit()] == ToSeq(limit))
    # The value binding is added: the value placeholder is present and renders
    # to the offending input, so a custom value template surfaces the input
    # even for a bound-limit rejection.
    Ensures(placeholder_value() in Result())
    Ensures(Result()[placeholder_value()] == ToSeq(value))
    # A bound-limit rejection binds exactly the limit and the value
    # placeholders -- nothing spurious.
    Ensures(Forall(int, lambda k: (
        Implies(k in Result(),
                k == placeholder_limit() or k == placeholder_value()))))
    # post-conditions-end
    # impl-start
    params = {}  # type: Dict[int, PSeq[int]]
    params[placeholder_limit()] = ToSeq(limit)
    params[placeholder_value()] = ToSeq(value)
    return params
    # impl-end


def decimal_reject_params(finite: bool, value: List[int]) -> Dict[int, PSeq[int]]:
    # pre-conditions-start
    # `value` is the offending candidate (its string form); `finite` is the
    # boolean classification bit accompanying it. The candidate has already been
    # judged invalid -- this builds the parameter mapping its rejection
    # produces.
    Requires(Acc(list_pred(value), 1 / 2))
    Requires(MustTerminate(3))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(value), 1 / 2))
    Ensures(Acc(dict_pred(Result())))
    Ensures(Result() is not None)
    # The decisive guarantee: the rejection binds the value placeholder to the
    # offending input for EITHER value of `finite`, so a custom value template
    # surfaces the rejected input whichever class the candidate falls in.
    Ensures(placeholder_value() in Result())
    Ensures(Result()[placeholder_value()] == ToSeq(value))
    # The rejection binds nothing other than the value placeholder, again for
    # EITHER value of `finite`: the produced mapping is EXACTLY a bare
    # rejection's mapping in both classes, so neither class may contribute a
    # spurious extra binding.
    Ensures(Forall(int, lambda k: (
        Implies(k in Result(), k == placeholder_value()))))
    # post-conditions-end
    # impl-start
    # The not-finite screen that would intercept with a parameter-less rejection
    # is gone: a not-finite candidate flows through to the same bare rejection
    # as the finite-but-invalid one, so both produce the value-binding mapping.
    return build_invalid_params(value)
    # impl-end
