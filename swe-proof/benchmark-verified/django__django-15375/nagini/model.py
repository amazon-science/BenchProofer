"""Twin-artifact model for django__django-15375.

Behaviour under specification (stated as desired behaviour):

  Resolving an aggregation against a query either produces a resolved
  expression or REJECTS the aggregation, producing no expression at all. It
  rejects exactly two kinds of input: one where a part the resolution has to
  resolve — an operand the aggregation aggregates over, the condition it is
  restricted by, a fallback value that is itself an expression, or whatever
  else building the fallback-supplying expression requires resolution to
  determine — cannot be resolved against the query at all; and one where the
  aggregation aggregates over another aggregation while a NON-final resolution
  is requested. On every other input it produces an expression.

  Everything resolution reports about the aggregation is read from the
  aggregation AS RESOLVED, never from the aggregation as it was written:
  resolution works on its own resolved form of the aggregation and reads from
  THAT form both whether a fallback value is requested and what that value is.
  An aggregation whose resolution yields a different fallback value than the one
  it was written with is therefore described here by the fallback its resolved
  form carries.

  A produced expression carries six observable attributes: a boolean
  final-flag; whether the expression itself supplies a fallback value for an
  aggregation that matches nothing; whether it still holds a fallback value of
  its own that nothing supplies yet; whether every part it is built from can be
  used as it stands; the fallback VALUE it supplies (or none at all); and, when
  it supplies a fallback, the aggregation it supplies that fallback for, which
  stays reachable from it.

  A fallback value carries two observable attributes of its own: whether it can
  be used as it stands, and which value — if any — it is the resolved form OF.
  Nothing is assumed about the value an aggregation is written with: it may be
  usable as it stands or not, whether or not it is itself an expression.

  An aggregation is built over an OPERAND it aggregates, and may in addition be
  RESTRICTED BY A CONDITION. Resolution puts both of those into resolved form as
  the parts it resolves — but putting the OPERAND into resolved form is a step
  this resolution hands off, dispatched on the operand itself, and it does not
  decide what that step comes back with. Usually the operand's resolved form can
  be used as it stands; for some operands the step hands back something that
  still cannot be. So WHETHER THE OPERAND'S RESOLVED FORM CAN BE USED AS IT
  STANDS is read here rather than asserted, for exactly the reason the outcome of
  resolving a fallback value that is itself an expression is read rather than
  asserted below: a different step decides it.

  The condition, in turn, is put into resolved form only when it actually
  restricts something: a condition that is present but restricts NOTHING AT ALL
  is left exactly as it was written. Being left as written is NOT by itself the
  same as being a part that is not in resolved form. Whether the aggregation then
  still carries such a part depends on THAT WRITTEN CONDITION: some conditions
  cannot be used as they stand until they are put into resolved form, and one of
  those, left as written, IS a part that is not in resolved form; but a condition
  can perfectly well be usable as it stands ALREADY AS WRITTEN, and leaving such a
  condition alone leaves the aggregation carrying nothing unresolved. So what is
  read here is not mere "restricts nothing" but the conjunction of the two: the
  aggregation is RESTRICTED BY A CONDITION THAT WAS LEFT AS WRITTEN AND CANNOT BE
  USED AS IT STANDS. When the condition DOES restrict something,
  putting IT into resolved form is a handed-off step in exactly the same way the
  operand's is — dispatched on the condition itself, and this resolution does not
  decide what that step comes back with either. Usually the condition's resolved
  form can be used as it stands; for some conditions the step hands back
  something that still cannot be. So WHETHER THE CONDITION'S RESOLVED FORM CAN BE
  USED AS IT STANDS is likewise read here rather than asserted, for the very same
  reason: a different step decides it. Where no such step runs at all — no
  condition, or a condition left as written — there
  is no outcome of it to hold against the aggregation.

  So the parts of the resolved aggregation can be used as they stand exactly when
  ALL THREE hold: the operand's resolved form can be used as it stands, the
  condition's resolved form can be used as it stands, and the aggregation is not
  restricted by a condition that was left as written and cannot be used as it
  stands. Any one failing alone leaves
  the aggregation NOT usable as it stands — a condition left as written that
  cannot be used as it stands is
  still carried unresolved however well the operand resolved; an operand whose
  resolved form cannot be used as it stands leaves the aggregation unusable
  however plainly the condition resolved; and a condition that DID restrict
  something but whose resolved form cannot be used as it stands leaves it
  unusable however plainly the operand resolved. Conversely a condition left as
  written that is ALREADY usable as it stands leaves nothing unresolved, and the
  aggregation is usable as it stands as soon as the other two hold. This is a
  property of the
  aggregation, not of the fallback: it holds the same way whether or not a
  fallback value is requested.

  When no fallback value is requested, resolution returns the resolved
  aggregation directly: it does not supply a fallback, it holds no fallback
  value of its own, it supplies no fallback value and no aggregation's fallback,
  its parts can be used as they stand on exactly the three-part condition just
  stated, and its final-flag equals the requested final-flag.

  When a fallback value IS requested, resolution returns a DISTINCT expression
  that supplies the fallback (not the bare aggregation). That returned
  expression's final-flag must equal the requested final-flag — the same value
  the aggregation itself carries. The aggregation whose fallback it supplies
  stays reachable from it and is left as resolution made it: carrying the
  requested final-flag, supplying no fallback of any aggregation itself,
  holding no fallback value of its own any more, supplying nothing for a
  further aggregation, and — this is the aggregation resolution DID resolve, not
  some other aggregation that merely carries the same final-flag — with its
  operand put through resolution and its parts usable as they stand on exactly
  the same three-part condition as above: usable exactly when the operand's
  resolved form can be used as it stands, the condition's resolved form can be
  used as it stands, and it is not restricted by a condition that restricts
  nothing.

  The returned expression's own parts are the aggregation it supplies the
  fallback for and the fallback value it supplies. An aggregation always stands
  as a part of the expression built over it — a part of its OWN that is not in
  resolved form, whether a condition left as written that cannot be used as it
  stands or an operand whose
  resolved form cannot be used as it stands, is a fact about the aggregation's own
  parts and not about its standing as one — so every part of the returned
  expression can be used as it stands exactly when the value it supplies can be.

  WHICH value the returned expression supplies is pinned to the value that was
  asked for, not merely described by a flag on the expression that supplies it:

    * a fallback value that is NOT itself an expression is supplied AS ASKED
      FOR — the returned expression supplies THAT VERY VALUE, left exactly as it
      was (as usable as it arrived, the resolved form of whatever it already
      was), and nothing else is derived from it in its place;

    * a fallback value that IS itself an expression is PUT THROUGH RESOLUTION,
      and what THAT yields is what gets supplied. Resolving such a value is a
      step this resolution hands off: it does not decide what comes back, so
      what comes back is read here rather than asserted. Resolution of a value
      may yield a DISTINCT value, or it may hand back the very value it was
      given — a value that is already in resolved form is its own resolved
      form. When a DISTINCT value comes back, THAT value is what the returned
      expression supplies, and it is recorded as the resolved form OF the value
      that was asked for; whether it can be used as it stands is whatever
      resolving yielded, which is not guaranteed — the value resolution arrives
      at may itself still need resolving before it can be used. When resolution
      hands back the value it was given, THAT VERY VALUE is what the returned
      expression supplies, exactly as in the case above, as usable as it
      arrived. Either way the value as written is left exactly as it was.

  A fallback value that cannot be resolved at all is one of the two rejection
  cases above. A rejected aggregation also leaves the fallback value it was
  written with exactly as it was.

  Concretely: resolution rejects exactly on the two kinds of input above;
  otherwise the returned expression supplies a fallback exactly when one was
  requested, its final-flag equals the requested final-flag in every case, the
  aggregation reachable from it carries that same final-flag, and the fallback
  value it supplies is the requested one itself or what resolving the requested
  one yielded.

The expressions are modelled as a minimal class carrying only the observed
fields: the final-flag (a ``bool``), whether the expression supplies a fallback
value (a ``bool``), whether it still holds a fallback value of its own (a
``bool``), whether every part it is built from can be used as it stands (a
``bool``), the fallback value it supplies (a ``FallbackValue``, or ``None`` when
it supplies none), and the aggregation whose fallback it supplies (an
``Expression``, or ``None`` when it supplies none). A fallback value is a second
minimal class carrying whether it can be used as it stands (a ``bool``) and the
value it is the resolved form of (a ``FallbackValue``, or ``None``). Whether the
aggregation is restricted by a condition that was left as written AND cannot be
used as it stands is an INPUT (a
``bool``): it is a property of the aggregation as written, not something
resolution decides. Whether the OPERAND's resolved form can be used as it stands
is likewise an INPUT (a ``bool``): putting the operand into resolved form is a
step dispatched on the operand and handed off, so what it comes back with is read
here, not decided. Whether the CONDITION's resolved form can be used as it stands
is an INPUT (a ``bool``) for exactly the same reason — putting a condition that
restricts something into resolved form is a step dispatched on the condition and
handed off too; where no such step runs it carries no outcome to hold against the
aggregation. What resolving a fallback value that is itself an expression
YIELDS is read as INPUT for the very same reason — whether it yields a
value distinct from the one it was given (a ``bool``), and whether the value it
yields can be used as it stands (a ``FallbackValue`` standing for the yielded
value, whose own usability that step determines). Resolving such a value is
a step this resolution delegates, so what it produces is not this resolution's
to assert. Rejection is a user-defined exception: a builtin exception in an
``Exsures`` crashes the Nagini translator.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Optional
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


class ResolutionRefused(Exception):
    """Signals a rejected aggregation: resolution yields no expression at all
    for it. Stands in for the error the desired behaviour raises."""


class FallbackValue:
    """A fallback value an aggregation can carry. Two observables: whether it
    can be used as it stands, and which value it is the resolved form OF."""

    def __init__(self, usable: bool) -> None:
        # Level 1: straight-line field initialisation, no loop and no call, so it
        # terminates outright, BELOW every obligated caller's level.
        Requires(MustTerminate(1))
        Ensures(Acc(self.usable) and  # type: ignore
                Acc(self.resolution_of) and  # type: ignore
                self.usable == usable and  # type: ignore
                self.resolution_of is None)  # type: ignore
        self.usable = usable
        # A freshly built value is not yet the resolved form of any other value.
        self.resolution_of = None  # type: Optional[FallbackValue]


class Expression:
    def __init__(self, is_final_aggregation: bool, supplies_fallback: bool) -> None:
        # Level 1: straight-line field initialisation, no loop and no call, so it
        # terminates outright. It sits BELOW every obligated caller's level, which
        # is what lets a caller discharge its obligation into this constructor.
        Requires(MustTerminate(1))
        Ensures(Acc(self.is_final_aggregation) and  # type: ignore
                Acc(self.supplies_fallback) and  # type: ignore
                Acc(self.holds_own_fallback) and  # type: ignore
                Acc(self.parts_usable) and  # type: ignore
                Acc(self.fallback) and  # type: ignore
                Acc(self.wrapped) and  # type: ignore
                self.is_final_aggregation == is_final_aggregation and  # type: ignore
                self.supplies_fallback == supplies_fallback and  # type: ignore
                not self.holds_own_fallback and  # type: ignore
                not self.parts_usable and  # type: ignore
                self.fallback is None and  # type: ignore
                self.wrapped is None)  # type: ignore
        self.is_final_aggregation = is_final_aggregation
        self.supplies_fallback = supplies_fallback
        # A freshly built expression holds no fallback value of its own, supplies
        # no fallback value, and supplies no aggregation's fallback until it is
        # given one to supply.
        self.holds_own_fallback = False
        # Merely BUILDING an expression establishes nothing about its parts: an
        # expression built out of parts that have not been resolved cannot be
        # used as it stands. Whoever builds it is answerable for its parts.
        self.parts_usable = False
        self.fallback = None  # type: Optional[FallbackValue]
        self.wrapped = None  # type: Optional[Expression]


# axioms-start
# (no @ContractOnly callee is consumed: the unchanged base resolution and the
#  resolution of a fallback value that is itself an expression are modelled
#  directly by their effect on the observed fields — see mapping.md /
#  refinement.md.)
# axioms-end


# pure-start
# (no auxiliary pure spec functions are required for this behaviour)
# pure-end


def resolve_aggregation(requested_final: bool,
                        fallback: Optional[FallbackValue],
                        fallback_is_expression: bool,
                        resolution_yields_distinct: bool,
                        resolution_yield: Optional[FallbackValue],
                        aggregating_operand: bool,
                        operand_resolution_usable: bool,
                        condition_resolution_usable: bool,
                        vacuous_condition: bool,
                        parts_resolve: bool) -> Expression:
    # pre-conditions-start
    # The fallback value the resolved aggregation carries is passed as the object
    # it is (``None`` when no fallback value is requested), so that what the
    # returned expression supplies can be pinned to THAT value rather than
    # described by a flag the returned expression carries about itself.
    # Every combination of inputs is admitted — the behaviour below is a TOTAL
    # claim over the whole domain, including the inputs on which resolution must
    # REJECT rather than produce an expression (the Exsures pins those, so they
    # are specified, not excluded). NO clause below restricts a value: the single
    # clause is the permission to read and write the passed fallback value's own
    # two fields, which is ownership, not a domain restriction — resolution is
    # handed the value and is answerable for what it does to it (the
    # postcondition and the Exsures both hand that permission back with the value
    # unchanged). A fallback value is admitted usable or not-usable as it stands,
    # and the resolved form of anything or of nothing, INDEPENDENTLY of whether it
    # is itself an expression: a value that is not an expression can still be one
    # that cannot stand as a fallback source as it is written.
    # ``vacuous_condition`` says the aggregation is restricted by a condition that
    # was LEFT AS WRITTEN — it restricts nothing at all, so no resolving step ran
    # on it — AND that written condition CANNOT BE USED AS IT STANDS, so leaving it
    # alone left the aggregation carrying a part that is not in resolved form. BOTH
    # halves are required: a condition left as written which is ALREADY usable as it
    # stands leaves nothing unresolved and does NOT make this true. A property of
    # the aggregation as written, read as
    # an input for the same reason the others are: resolution does not choose it.
    # It is admitted BOTH ways on every combination of the others; no clause below
    # restricts it.
    # ``operand_resolution_usable`` says WHAT PUTTING THE OPERAND INTO RESOLVED
    # FORM CAME BACK WITH: whether that resolved form can be used as it stands.
    # That step is dispatched on the operand and handed off, so like
    # ``resolution_yields_distinct`` / ``resolution_yield`` on the fallback-value
    # side its outcome is READ here, not decided — a step that succeeds without
    # rejecting can still come back with something that cannot be used as it
    # stands. It is admitted BOTH ways on every combination of the others; no
    # clause below restricts it. In particular ``False`` together with
    # ``parts_resolve`` is in-domain: coming back with something not usable as it
    # stands is not a failure to resolve.
    # ``condition_resolution_usable`` says the SAME THING FOR THE CONDITION: what
    # putting a condition that restricts something into resolved form came back
    # with, namely whether that resolved form can be used as it stands. That step
    # is dispatched on the condition and handed off just as the operand's is, so
    # its outcome is READ here, not decided — a condition can be put through
    # resolution without rejecting and still come back as something that cannot be
    # used as it stands. It is admitted BOTH ways on every combination of the
    # others, including together with ``parts_resolve`` and on the inputs where no
    # such step runs at all (no condition, or ``vacuous_condition``), where it is
    # simply immaterial: no clause below restricts it, and no clause below reads it
    # on an input where the step did not run.
    # ``resolution_yields_distinct`` and ``resolution_yield`` carry WHAT RESOLVING
    # a fallback value that is itself an expression produced. That resolving is a
    # step this resolution hands off rather than performs, so its outcome is read
    # here, not decided: it may yield a value DISTINCT from the one it was given,
    # or hand back that very value, and the value it yields may or may not be
    # usable as it stands. ``resolution_yield`` is the value that came back (the
    # object standing for it, so what is supplied can be pinned by identity);
    # ``resolution_yields_distinct`` says whether it is a different value from the
    # one handed in. BOTH are admitted on every combination of the others: the
    # clauses below restrict neither, and in particular a resolving step that
    # yields the very value it was given, or one whose yield is not usable as it
    # stands, are both in-domain.
    Requires(Implies(fallback is not None,
                     Acc(fallback.usable) and Acc(fallback.resolution_of)))
    # Ownership of the yielded value's own two fields, on the input where a
    # resolving step ran and handed back something DIFFERENT — the value the
    # returned expression is going to supply. Ownership, not a domain
    # restriction: the postcondition hands this permission back.
    Requires(Implies(fallback is not None and fallback_is_expression
                     and resolution_yields_distinct,
                     resolution_yield is not None
                     and resolution_yield is not fallback
                     and Acc(resolution_yield.usable)
                     and Acc(resolution_yield.resolution_of)))
    # When the resolving step hands back the very value it was given, the value
    # that came back IS that value — this says which object the yield is, not
    # that any input is excluded.
    Requires(Implies(fallback is not None and fallback_is_expression
                     and not resolution_yields_distinct,
                     resolution_yield is fallback))
    # TERMINATION. This body is loop-free straight-line code, so it terminates on
    # every input; the obligation is what makes that a PROVEN fact rather than an
    # assumption, turning the Ensures/Exsures below from partial into total
    # correctness: resolution must ANSWER, by producing an expression or by
    # rejecting. The level is 2, one above the constructors' level 1, leaving the
    # room a caller needs to discharge into those callees. It rises to 3 on the
    # no-fallback path purely so that a self-call made from THAT path onto a
    # with-fallback input strictly descends (3 > 2), keeping any such recursion
    # well-founded. This constrains no input: every combination is still
    # admitted.
    Requires(MustTerminate(2 if fallback is not None else 3))
    # pre-conditions-end
    # post-conditions-start
    # Resolution produces an expression only when neither rejection case applies:
    # every part it has to resolve resolves, and it is not asked for a non-final
    # resolution of an aggregation over another aggregation.
    Ensures(parts_resolve)
    Ensures(requested_final or not aggregating_operand)
    Ensures(Acc(Result().is_final_aggregation))
    Ensures(Acc(Result().supplies_fallback))
    Ensures(Acc(Result().holds_own_fallback))
    Ensures(Acc(Result().parts_usable))
    Ensures(Acc(Result().fallback))
    Ensures(Acc(Result().wrapped))
    # The returned expression supplies a fallback exactly when one was
    # requested: with a fallback, a distinct fallback-supplying expression is
    # returned (not the bare aggregation); without one, the aggregation itself.
    Ensures(Result().supplies_fallback == (fallback is not None))
    # The returned expression's final-flag equals the requested final-flag —
    # whether or not a fallback was supplied.
    Ensures(Result().is_final_aggregation == requested_final)
    # Whatever is returned holds no fallback value of its own left unsupplied:
    # a returned bare aggregation was asked for none, and a returned
    # fallback-supplying expression supplies the one that was asked for.
    Ensures(not Result().holds_own_fallback)
    # A fallback VALUE is supplied exactly when one was requested.
    Ensures((Result().fallback is not None) == (fallback is not None))
    # A returned bare aggregation is one resolution actually RESOLVED: its operand
    # has been PUT THROUGH resolution, and so has the condition restricting it
    # WHENEVER that condition restricts anything — so its parts can be used as
    # they stand exactly when the operand's resolved form can be used as it stands
    # AND the condition's resolved form can be used as it stands AND it is not
    # restricted by a condition that was left as written and cannot be used as it
    # stands. The equality is two-sided:
    # under-claiming would admit an aggregation whose parts were never resolved at
    # all, and over-claiming asserts a usable form that the resolution demonstrably
    # does not always produce — not the resolved condition it never builds for a
    # condition left as written that cannot be used as it stands, not a usable
    # operand form the handed-off
    # operand step did not come back with, and not a usable condition form the
    # equally handed-off condition step did not come back with either. Equally it
    # must not UNDER-claim where the written condition needed nothing done to it:
    # a condition left as written that is already usable as it stands leaves the
    # aggregation usable, and denying that is just as unfaithful.
    Ensures(Implies(fallback is None,
                    Result().parts_usable == (operand_resolution_usable
                                              and condition_resolution_usable
                                              and not vacuous_condition)))
    # The aggregation whose fallback is being supplied stays reachable from the
    # returned expression, and only a fallback-supplying expression has one.
    Ensures((Result().wrapped is not None) == (fallback is not None))
    # That reachable aggregation is left as resolution made it: it carries the
    # requested final-flag, it supplies no aggregation's fallback itself, it no
    # longer holds a fallback value of its own, and it supplies no fallback value
    # and no further aggregation's fallback. And it is the aggregation resolution
    # actually RESOLVED, not some other aggregation that merely carries the same
    # final-flag: its operand has been put through resolution, and so has the
    # condition restricting it whenever that condition restricts anything — so its
    # parts can be used as they stand on EXACTLY the same three-part condition as a
    # returned bare aggregation, by the SAME two-sided equality. An aggregation
    # that was merely BUILT has none of its parts resolved, so it cannot satisfy
    # this on the inputs where the equality demands usable parts, however correctly
    # flagged it is; an aggregation resolution left with an unresolved condition
    # cannot be claimed usable either; and neither may a usable form be claimed
    # where a handed-off step — the operand's or the condition's — did not come
    # back with one.
    Ensures(Implies(Result().wrapped is not None,
                    Acc(Result().wrapped.is_final_aggregation) and
                    Acc(Result().wrapped.supplies_fallback) and
                    Acc(Result().wrapped.holds_own_fallback) and
                    Acc(Result().wrapped.parts_usable) and
                    Acc(Result().wrapped.fallback) and
                    Acc(Result().wrapped.wrapped) and
                    Result().wrapped.is_final_aggregation == requested_final and
                    not Result().wrapped.supplies_fallback and
                    not Result().wrapped.holds_own_fallback and
                    Result().wrapped.parts_usable == (operand_resolution_usable
                                                      and condition_resolution_usable
                                                      and not vacuous_condition) and
                    Result().wrapped.fallback is None and
                    Result().wrapped.wrapped is None))
    # WHICH value is supplied, case (a): there is nothing about the requested
    # value left to resolve, so the returned expression supplies THAT VERY VALUE,
    # left exactly as it was — as usable as it arrived and the resolved form of
    # whatever it already was. Nothing is derived from it in its place, and
    # nothing about it is written over. Note what is NOT claimed: that the value
    # can be used as it stands. A value that is not itself an expression may still
    # be one that cannot stand as a fallback source as written, and passing such a
    # value straight through, unchanged, is exactly the behaviour.
    # The returned expression's own parts are the aggregation it supplies the
    # fallback for — usable as it stands, per the clause above — and the value it
    # supplies: so all of ITS parts are usable exactly when the value passed
    # straight through is. Passing a value straight through does not make it
    # usable, and the expression built over it inherits that.
    Ensures(Implies(fallback is not None and not fallback_is_expression,
                    Acc(fallback.usable) and Acc(fallback.resolution_of) and
                    Result().fallback is fallback and
                    Result().parts_usable == fallback.usable and
                    fallback.usable == Old(fallback.usable) and
                    fallback.resolution_of is Old(fallback.resolution_of)))
    # WHICH value is supplied, case (b): the requested value is itself an
    # expression, so it is PUT THROUGH RESOLUTION and what THAT yielded is what
    # gets supplied — pinned by IDENTITY to the yield, so the claim is data flow
    # and not a report. The returned expression supplies the value the resolving
    # step handed back, and nothing else: not the value as written when something
    # different came back, and not anything derived from elsewhere. What is NOT
    # claimed is what the resolving step is not this resolution's to decide:
    # whether the value that came back is usable as it stands. It is supplied
    # exactly as it came back — a yield that still cannot be used as it stands is
    # supplied that way, and the expression built over it inherits that, exactly
    # as in case (a). The value as written is left exactly as it was: as usable as
    # it arrived and the resolved form of whatever it already was. So a resolution
    # that supplied the value as written where a DIFFERENT value came back, or one
    # that supplied something other than the yield, or one that made the written
    # value usable in place, does not satisfy this.
    Ensures(Implies(fallback is not None and fallback_is_expression,
                    Acc(fallback.usable) and Acc(fallback.resolution_of) and
                    Result().fallback is resolution_yield and
                    fallback.usable == Old(fallback.usable) and
                    fallback.resolution_of is Old(fallback.resolution_of)))
    # Case (b), the arm where the resolving step yielded a DISTINCT value: that
    # value is the one supplied, it is recorded as the resolved form OF the value
    # that was asked for — being a resolution of SOMETHING is not enough, it must
    # be the resolution of THIS value — and the returned expression's own parts
    # are usable exactly when the supplied value is, by the SAME rule as case
    # (a): the aggregation always stands as a part, so the value it supplies is
    # what decides. Fresh permission to the supplied value's own fields is what
    # makes DISTINCTNESS enforceable rather than merely stated.
    Ensures(Implies(fallback is not None and fallback_is_expression
                    and resolution_yields_distinct,
                    Acc(Result().fallback.usable) and
                    Acc(Result().fallback.resolution_of) and
                    Result().fallback is not fallback and
                    Result().fallback.resolution_of is fallback and
                    Result().parts_usable == Result().fallback.usable and
                    # The FRAME on the yielded value: whether it can be used as it
                    # stands is what the resolving step arrived at, and this
                    # resolution does not touch it. So an implementation may not
                    # write over the yield's usability to make its own claim about
                    # the expression built over it come out easier.
                    resolution_yield.usable == Old(resolution_yield.usable)))
    # Case (b), the arm where the resolving step handed back the very value it
    # was given: that value is supplied AS IT ARRIVED, left exactly as it was,
    # and the returned expression's parts are usable exactly when it is — the
    # same two-sided rule again. A value already in resolved form is its own
    # resolved form, so no distinct value is produced for it and none may be
    # claimed.
    Ensures(Implies(fallback is not None and fallback_is_expression
                    and not resolution_yields_distinct,
                    Result().fallback is fallback and
                    Result().parts_usable == fallback.usable))
    # Rejection happens on exactly the two kinds of input named above, and on no
    # other: a part that cannot be resolved at all, or a non-final resolution of
    # an aggregation that aggregates over another aggregation. A rejecting
    # resolution leaves the fallback value it was written with exactly as it was,
    # and likewise the value a resolving step handed back: rejecting is not a
    # licence to have written over either of them.
    Exsures(ResolutionRefused,
            (not parts_resolve or (aggregating_operand and not requested_final))
            and Implies(fallback is not None,
                        Acc(fallback.usable) and Acc(fallback.resolution_of) and
                        fallback.usable == Old(fallback.usable) and
                        fallback.resolution_of is Old(fallback.resolution_of))
            and Implies(fallback is not None and fallback_is_expression
                        and resolution_yields_distinct,
                        Acc(resolution_yield.usable) and
                        Acc(resolution_yield.resolution_of) and
                        resolution_yield.usable == Old(resolution_yield.usable)))
    # post-conditions-end
    # impl-start
    if not parts_resolve:
        # A part this resolution has to resolve cannot be resolved against the
        # query at all, so no expression is produced for the aggregation.
        raise ResolutionRefused()
    # The unchanged base resolution stamps the requested final-flag onto the
    # resolved aggregation; the aggregation does not itself supply a fallback,
    # and it still holds the fallback value the caller asked for.
    c = Expression(requested_final, False)
    # Resolving the aggregation puts the parts it is built from through
    # resolution: the operand it aggregates over, and the condition restricting it
    # WHEN that condition restricts anything. Each of those is handed off, and what
    # each comes back with — usable as it stands or not — is READ here, not
    # decided. A condition that restricts nothing is left as written, which leaves
    # an unresolved part behind only when that written condition cannot be used as
    # it stands. So the
    # aggregation is usable as it stands exactly when all three came out that way.
    # This is the step whose omission leaves a correctly flagged aggregation that
    # was never actually resolved.
    c.parts_usable = (operand_resolution_usable and condition_resolution_usable
                      and not vacuous_condition)
    # MODELLED STATE, not a step of the work: a resolved aggregation for which a
    # fallback value was requested DOES still hold that value at this point —
    # resolution reads the value off the resolved aggregation and only clears it
    # below, before the returned expression takes over supplying it. A model that
    # drops this line claims the aggregation never holds a fallback of its own,
    # which is false of the real callee; and such a model can no longer describe
    # leaving the fallback in place while wrapping, which is the behaviour the
    # clearing exists to prevent.
    c.holds_own_fallback = fallback is not None
    if aggregating_operand and not requested_final:
        # The resolved aggregation aggregates over another aggregation and a
        # non-final resolution was requested: rejected, no expression produced.
        raise ResolutionRefused()
    if fallback is None:
        return c
    supplied = fallback
    if fallback_is_expression:
        # The requested fallback value is itself an expression, so it is put
        # through resolution and what THAT yielded is what gets supplied. This
        # resolution hands that step off and does not decide its outcome, so the
        # outcome is READ here: the value that came back is what the returned
        # expression goes on to supply, whether or not it is usable as it stands.
        # The value as written is left untouched either way.
        if resolution_yields_distinct:
            # A DISTINCT value came back. It is recorded as the resolved form OF
            # the requested one, and its usability is whatever resolving yielded
            # — not something this step may assert.
            resolution_yield.resolution_of = fallback
            supplied = resolution_yield
        else:
            # Resolution handed back the very value it was given: a value already
            # in resolved form is its own resolved form, so that value is what is
            # supplied, exactly as it arrived.
            supplied = fallback
    # A fallback is supplied: return a distinct expression that supplies it. It
    # is built unmarked.
    wrapper = Expression(False, True)
    # Pin the modelled fact (G-AX negative control (3)): a freshly constructed
    # fallback wrapper is UNMARKED — the real one inherits the class default
    # until assigned. A model whose wrapper is born marked is unfaithful to the
    # real callee and must not verify.
    Assert(not wrapper.is_final_aggregation)
    # Its parts are the resolved aggregation, which always stands as a part of the
    # expression built over it, and the value it supplies: so all of its parts are
    # usable exactly when that value is.
    wrapper.parts_usable = supplied.usable
    # The returned fallback-supplying expression must carry the same final-flag
    # as the aggregation it supplies the fallback for.
    wrapper.is_final_aggregation = c.is_final_aggregation
    # The aggregation itself no longer holds the fallback value — the returned
    # expression is what supplies it — and it stays reachable from that
    # expression, which is what supplies the fallback FOR it.
    c.holds_own_fallback = False
    wrapper.wrapped = c
    # The value the returned expression supplies is the one resolution arrived
    # at for the requested fallback.
    wrapper.fallback = supplied
    return wrapper
    # impl-end
