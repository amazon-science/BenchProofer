"""Twin-artifact model for django__django-16899.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A configuration option lists candidate field references by name. Each
  reference is validated: it is acceptable when it resolves (it is callable, or
  names an attribute on the administered configuration object, or names an
  attribute or declared field on the underlying model). When a reference does
  NOT resolve, the validator emits exactly one diagnostic; when it does
  resolve, it emits nothing.

  The diagnostic message must let the reader locate the offending reference
  precisely. It therefore reports BOTH:

    * the positional label of the entry (e.g. the indexed option slot), AND
    * the offending reference VALUE ITSELF,

  before explaining the three places that were searched (the configuration
  object's class, the model, the model's declared fields). Concretely the
  message is the constant prose with four interpolation points filled, in order,
  by: the label, then the offending reference value, then the configuration
  class name, then the model label. The reference value appears as its own
  interpolated segment -- quoted, immediately after the label -- so the message
  names the value at fault rather than only its position.

Strings are modelled as `List[int]` of Unicode code points (Nagini bans `str`
indexing); the message specification is carried by `PSeq[int]`. The four constant
prose segments of the template are modelled by distinct one-token markers
(`seg_*`); the four dynamic parts are the input carriers spliced in at their
interpolation points. The behaviour the issue and tests pin is the SHAPE of the
message -- which dynamic parts appear, in what order, with the offending value
present as its own segment after the label -- not the exact prose wording, so
the prose is abstracted to constant markers (refinement.md gives the segment <->
literal-text bijection). Whether a reference resolves is an UNCHANGED, opaque
set of attribute/field lookups, abstracted by a single boolean guard
(`resolves`); it is the only thing under change that the message names the
value. No callee is consumed as an axiom: the construction is modelled deeply
(concrete sequence concatenation).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# No consumed axioms. The validated behaviour (the shape of the diagnostic
# message) is modelled deeply as concrete code-point-sequence concatenation.
# The opaque resolution lookups the validator performs are UNCHANGED by this
# behaviour and are abstracted by the boolean guard `resolves`; they are not
# consumed as an Ensures-bearing contract.
# axioms-end


# pure-start
@Pure
def seg_intro() -> PSeq[int]:
    # constant prose: "The value of '"
    return PSeq(1)


@Pure
def seg_refers() -> PSeq[int]:
    # constant prose: "' refers to '"  -- introduces the offending reference VALUE
    return PSeq(2)


@Pure
def seg_which_not() -> PSeq[int]:
    # constant prose: "', which is not a callable, an attribute of '"
    return PSeq(3)


@Pure
def seg_or_attr() -> PSeq[int]:
    # constant prose: "', or an attribute of '"
    return PSeq(4)


@Pure
def seg_end() -> PSeq[int]:
    # constant prose: "'."
    return PSeq(5)


@Pure
def diagnostic_message(label: PSeq[int], value: PSeq[int],
                       cls: PSeq[int], model_label: PSeq[int]) -> PSeq[int]:
    """The diagnostic message for a reference that does not resolve: the constant
    prose with the four interpolation points filled, in order, by the label,
    the offending reference value, the configuration class name, and the model
    label. The value is spliced in as its own quoted segment immediately after
    the label."""
    return (seg_intro() + label + seg_refers() + value + seg_which_not()
            + cls + seg_or_attr() + model_label + seg_end())
# pure-end


def check_reference(label: List[int], value: List[int],
                    cls: List[int], model_label: List[int],
                    resolves: bool) -> List[int]:
    # pre-conditions-start
    # All four message components are read-only inputs (fractional permission).
    Requires(Acc(list_pred(label), 1 / 2))
    Requires(Acc(list_pred(value), 1 / 2))
    Requires(Acc(list_pred(cls), 1 / 2))
    Requires(Acc(list_pred(model_label), 1 / 2))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(label), 1 / 2))
    Ensures(Acc(list_pred(value), 1 / 2))
    Ensures(Acc(list_pred(cls), 1 / 2))
    Ensures(Acc(list_pred(model_label), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # A resolving reference yields no diagnostic; a failing one yields exactly
    # one (the empty/non-empty result discriminates the two; the message always
    # begins with non-empty prose).
    Ensures(resolves == (len(Result()) == 0))
    # When a diagnostic is emitted it is exactly the constant prose with the four
    # dynamic parts spliced in at their interpolation points, IN ORDER:
    # label, then the offending reference value, then class, then model label.
    Ensures(Implies(not resolves,
                    ToSeq(Result()) == diagnostic_message(
                        ToSeq(label), ToSeq(value),
                        ToSeq(cls), ToSeq(model_label))))
    # Discriminating structural consequence: the offending reference VALUE
    # occurs in the message as a contiguous segment, at the offset that follows
    # the intro prose and the label (its own interpolated slot) -- the value is
    # named, not merely its position. A message that omits the value (placing
    # the class where the value belongs) cannot satisfy this.
    Ensures(Implies(not resolves,
                    ToSeq(Result()).drop(len(seg_intro()) + len(label)
                                         + len(seg_refers()))
                    .take(len(value)) == ToSeq(value)))
    # post-conditions-end
    # impl-start
    if resolves:
        ok = []  # type: List[int]
        return ok
    # Build the pre-change message "The value of '%s' is not a callable, an
    # attribute of '%s', or an attribute of '%s'." % (label, cls, model_label):
    # the offending reference value is NOT interpolated (constant prose markers).
    result = []  # type: List[int]
    result = result + [1]          # "The value of '"
    result = result + label        # label
    result = result + [6]          # "' is not a callable, an attribute of '"  (no value)
    result = result + cls          # class name
    result = result + [4]          # "', or an attribute of '"
    result = result + model_label  # model label
    result = result + [5]          # "'."
    return result
    # impl-end
