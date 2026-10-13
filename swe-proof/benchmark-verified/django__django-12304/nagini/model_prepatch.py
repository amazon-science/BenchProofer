"""Twin-artifact model for django__django-12304.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A constructed enumeration grouping is a class object, and a class object is
  callable.  When such a grouping is referenced as a variable in a template,
  the template engine's variable-resolution rule must yield the grouping
  *itself* so that a subsequent member access (a named choice, then that
  choice's label or value) can proceed.  The obstacle is that the default
  resolution rule, on encountering a callable, invokes it with no arguments;
  invoking the grouping with no arguments cannot succeed (constructing a
  member requires a value), so the resolution would instead collapse to the
  engine's invalid-value sentinel and every following member access would fail.

  The desired guarantee is therefore: the grouping is built so that it is
  flagged to be PRESERVED rather than invoked when it is met as a callable
  during template variable resolution.  Consequently resolving the grouping in
  a template yields the grouping object itself (its identity), never the
  invalid-value sentinel — making the grouping usable in templates.

  Building a grouping is furthermore an operation that must COMPLETE: declaring
  an enumeration is bounded work over the members declared for it, and the
  declaration must hand the finished grouping back to whoever declared it.  A
  construction that never delivers a grouping leaves the enumeration
  undeclarable and every template that mentions it unusable, so the guarantees
  above are demanded of a construction that actually returns, not merely of the
  runs that happen to get there.

  The construction proceeds in THREE recorded steps, and EACH of them can refuse
  the declaration it is handed.  What the whole construction must do is therefore
  a complete, ORDERED case split over which step refuses first — no declaration
  is left to behave as it likes:

    1. The BASE construction step creates the class object, binds the declared
       choices under their own names, and records the derived per-choice tables.
       It refuses a declaration whose declared kind cannot carry the declared
       choice values at all, and one that names a choice after a table this step
       must itself bind.  Where it refuses it delivers no grouping and reports
       the refusal, and the construction must pass that report on unchanged
       rather than substitute one of its own.

    2. Recording the flag is a guarded binding, not a bare field write.  The flag
       is recorded on the grouping under a NAME, and the grouping's declared
       choices occupy names on it too; a constructed grouping refuses to have a
       name rebound once one of its own declared choices already occupies that
       name.  So a declaration that itself declares a choice under the very name
       the flag is recorded under makes the recording REFUSED: the construction
       delivers no grouping at all and reports that refusal instead.

    3. The construction finally hands the flagged grouping to a value-
       distinctness step and delivers whatever that step hands back.  That step
       refuses a declaration that gives two of its declared choices the same
       value, so such a declaration yields no grouping either — but note WHERE it
       is refused: it is refused only at the very end, AFTER the flag has already
       been recorded on the grouping, and by a step the construction reaches
       normally.  A declaration that repeats a choice value is therefore squarely
       inside the behaviour demanded here; it is not a region a construction may
       treat as its own, and the report it produces must be the value-
       distinctness report, distinguishable from step 2's.

  All four outcomes are demanded and they are ORDERED: the report of the earliest
  step that refuses is the one the construction makes, so step 2's report is what
  a declaration that both names a choice after the flag's name AND repeats a
  choice value produces.  Off every refusal the grouping is delivered, flagged,
  and usable in a template.

  A refusal, moreover, is not merely an outcome of the right SHAPE at the right
  point: it is the refusal a particular step MAKES, and a declarer observes its
  content, not just the fact that something was refused.  The refusing steps here
  are steps of the surrounding construction — the base construction step and the
  value-distinctness step — each of which decides the declarations it refuses and
  words its own report about the declaration it read.  What is demanded is that
  the report a declarer receives be the one that step produced: the construction
  RELAYS it rather than deciding for itself that the declaration is refusable and
  composing a substitute report of its own.  A construction that anticipated a
  step's refusal — reading off the declaration that the step would refuse, and
  reporting so without letting the step run — would be making its own report,
  worded and detailed by itself, in place of a report that names the offending
  choices as the step words it.  A declarer distinguishing those two receives
  different text; so the demand is that no refusal be anticipated, and that the
  step whose refusal it is be the step that made it.  Correspondingly, DELIVERY
  is a two-sided claim about the same steps: a grouping is delivered only once
  BOTH the base construction step has itself accepted the declaration AND the
  value-distinctness step has itself confirmed the declared choice values are
  distinct, on the very grouping being delivered.  Neither confirmation may be
  substituted by the construction's own inspection of the declaration.

  Relaying means the declarer receives THE REPORT OBJECT that step produced, not
  merely a report of the same kind raised at the same point.  A construction that
  lets the step run, catches the report it made, and hands on a fresh report of
  its own composition has substituted its own wording just as surely as one that
  never ran the step: the step's account of WHICH declared kind cannot carry the
  values, or WHICH two choices collide, is exactly what is lost, and a declarer
  reading the report's content sees different text.  Both are refused here.

  The spec carries this as an unforgeable REPORT token per refusing step, issued
  by that step, when it actually refuses, FOR THE REPORT OBJECT IT RAISES, plus a
  CONFIRMATION token the value-distinctness step issues for the grouping it hands
  back.  A construction must present the matching token for the report it makes
  and with the grouping it delivers, so it can neither short-circuit a step nor
  relabel what a step reported and still discharge the obligation.

  Finally, one declared enumeration yields ONE grouping, and the grouping
  delivered is the one the base construction step built.  The declaration a
  grouping is built from is consumed by the act of building: the members declared
  for it are read off once and cannot be drawn from a second time, so the base
  construction step runs at most once per declaration.  A construction that ran
  that step twice for a single declaration would therefore not obtain two
  interchangeable groupings — the second attempt has nothing left to build from.
  The spec carries this as a single-use resource the base construction step
  consumes, together with a provenance token that step issues for the grouping it
  produced and the value-distinctness step passes along; so an implementation
  must build exactly once and deliver THAT grouping, rather than any object that
  merely reports the requested identity.

The grouping is modelled as a minimal class carrying only the two facts the
behaviour touches: its object identity (a positive integer distinguishing it
from the invalid-value sentinel, modelled as 0) and the boolean flag that
governs whether a callable is preserved (left as-is) rather than invoked during
template variable resolution.  Three unchanged callees are axiomatized: the base
class-construction step (which builds a callable grouping class object, or
refuses; whether the object it builds ALREADY carries the preserve-when-callable
flag is deliberately left open — a grouping constructed under an already-flagged
base inherits the flag, so its initial value cannot be assumed), the
value-distinctness step the construction hands the finished grouping to, and the
template variable-resolution rule (specialised to a callable whose no-argument
invocation cannot succeed).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Optional
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


class BaseStepRefused(Exception):
    """Signals that the BASE construction step itself refused the declaration it
    was handed — the declared kind cannot carry the declared choice values, or a
    choice is named after a table that step must itself bind — so it delivered no
    class object and the construction has nothing to record a flag on.  Stands in
    for the report that step makes, which the construction passes on unchanged; a
    builtin exception in an `Exsures` crashes the Nagini translator."""


class PreserveFlagNameTaken(Exception):
    """Signals that the grouping already binds, as one of its own declared
    choices, the name under which the preserve-when-callable flag is recorded,
    so recording the flag is refused and no grouping is delivered.  Stands in
    for the refusal the construction reports in that case; a builtin exception
    in an `Exsures` crashes the Nagini translator."""


class RepeatedChoiceValue(Exception):
    """Signals that the value-distinctness step the construction hands the
    already-flagged grouping to refused it, because the declaration gives two of
    its declared choices the same value.  Distinct from `PreserveFlagNameTaken`:
    the two refusals are made by different steps, at different points, and the
    construction must report the one that actually occurred.  Stands in for the
    report that step makes; a builtin exception in an `Exsures` crashes the
    Nagini translator."""


# The invalid-value sentinel a template substitutes when a variable lookup
# fails to produce a usable object.  Grouping identities are positive, so a
# grouping is never confused with the sentinel.
INVALID_VALUE = 0


class EnumGrouping:
    def __init__(self, identity: int, preserve_when_callable: bool) -> None:
        # Terminates: field initialisation is straight-line work. Measure 1 lets
        # any body holding MustTerminate(2) construct a grouping without leaking
        # its own obligation.
        Requires(MustTerminate(1))
        Ensures(Acc(self.identity) and self.identity == identity)                      # type: ignore
        Ensures(Acc(self.preserve_when_callable) and self.preserve_when_callable == preserve_when_callable)  # type: ignore
        self.identity = identity
        self.preserve_when_callable = preserve_when_callable


# axioms-start
# Opaque, unforgeable resource witnessing ONE pending enumeration declaration
# for the given identity — the declared-members record a grouping is built
# from.  It is a `@ContractOnly @Predicate` with NO body, so nothing can `Fold`
# a second one into existence, and it carries no `Ensures`, so it asserts
# nothing about the callee's results: its sole content is MULTIPLICITY.  The
# base construction step below consumes it, so a body holding one declaration
# may run that step exactly once.
@ContractOnly
@Predicate
def declaration_available(identity: int) -> bool:
    pass


# Opaque, unforgeable PROVENANCE token: this grouping is the object the base
# construction step built for this declaration.  Also a body-less
# `@ContractOnly @Predicate`, so it cannot be `Fold`ed into existence — the only
# way to hold one is to have obtained it from the base construction step (which
# issues it for the object it produces) or from the value-distinctness step
# (which passes it along for the object it hands back).  This is what makes "the
# grouping the construction produced" observable rather than collapsed to "any
# object that reports the requested identity": a body that fabricates a grouping,
# or builds one and delivers a different object, cannot present the token for
# what it delivers.
@ContractOnly
@Predicate
def built_from_declaration(grouping: EnumGrouping, identity: int) -> bool:
    pass


# Opaque, unforgeable REPORT token for the BASE construction step's own refusal,
# held BY THE REPORT OBJECT the declarer receives.  A body-less
# `@ContractOnly @Predicate`, so it cannot be `Fold`ed into existence: the only
# issuer is that step's refusal leg, and it issues the token FOR THE VERY REPORT
# IT RAISED.  That is what makes the report a declarer receives observable as
# THAT step's report rather than collapsed to "some refusal of the right kind at
# the right point".  Two distinct bodies fail to present it: one that decides the
# declaration is refusable and reports so WITHOUT letting the step run, and one
# that lets the step run, catches its report and hands on a REPLACEMENT report of
# its own.  Both make a report the step did not word, so a declarer reading the
# report's content — which names the offending kind or choices as the step words
# it — sees different text; the token is what forbids both.
@ContractOnly
@Predicate
def base_step_report(report: BaseStepRefused, identity: int) -> bool:
    pass


# Opaque, unforgeable REPORT token for the VALUE-DISTINCTNESS step's own refusal,
# with the same content and for the same reason: body-less, issued by that step's
# refusal leg for THE REPORT IT RAISED.  So neither anticipating the
# repeated-value refusal off the declaration nor substituting a freshly composed
# report for the one that step made can present it.  The report a declarer
# receives for a declaration that repeats a choice value therefore has to be the
# object that step raised, naming the offending choices as that step names them.
@ContractOnly
@Predicate
def distinctness_step_report(report: RepeatedChoiceValue, identity: int) -> bool:
    pass


# Opaque, unforgeable CONFIRMATION token: the value-distinctness step has itself
# confirmed, for THIS grouping, that the declaration's choice values are
# distinct.  Body-less, so it cannot be `Fold`ed; the only issuer is that step's
# delivery leg, on the object it hands back.  Delivery of a grouping is
# conditioned on holding it, so a construction cannot inspect the declaration
# itself, conclude the values are distinct and deliver on its own authority: the
# step that decides value-distinctness must have run, on the grouping delivered,
# and confirmed it.
@ContractOnly
@Predicate
def distinctness_confirmed(grouping: EnumGrouping, identity: int) -> bool:
    pass


@ContractOnly
def base_class_creation(identity: int) -> EnumGrouping:
    """The unchanged base construction step the grouping defers to first: it
    creates the enumeration class object, binds the declared choices under their
    own names and records the derived per-choice tables.

    It is TOTAL over declarations: either it delivers a callable class object
    with the given identity — issuing the provenance token for it — or it REFUSES
    the declaration and reports `BaseStepRefused`, and it refuses exactly the
    declarations `base_step_refuses` holds of.  Nothing here is contracted away
    into an excluded domain: a body that wants to report a refusal for such a
    declaration must obtain the report from this step, because the predicate is
    opaque and cannot be decided before the step runs.

    Whether the just-constructed object already carries the preserve-when-callable
    flag is deliberately UNCONSTRAINED: a grouping constructed under an
    already-flagged base INHERITS the flag (initially truthy), while a grouping
    with no flagged ancestor carries none (initially falsy) — so no sound contract
    may pin the initial value, and a correct implementation must establish the
    flag unconditionally rather than rely on (or toggle) its initial state.
    It is bounded work over the members declared for the grouping and always
    either delivers the class object or reports the refusal, so it terminates
    (measure 1: callable from any body holding MustTerminate(2) without leaking
    the obligation).
    Provenance + executable soundness: mapping.md / axiom_check.py.
    """
    Requires(MustTerminate(1))
    Requires(identity > 0)
    # CONSUMES the pending declaration: the declared-members record is read off
    # once and is exhausted by this step, so it can run at most once per
    # declaration. Not returned, hence single-use.
    Requires(declaration_available(identity))
    # Delivery means this step did NOT refuse — so the ONLY way a body can learn
    # that it did not is to have run it.
    Ensures(not base_step_refuses(identity))
    Ensures(built_from_declaration(Result(), identity))
    Ensures(Acc(Result().identity) and Acc(Result().preserve_when_callable))
    Ensures(Result().identity == identity)
    # NOTE: no Ensures on Result().preserve_when_callable — its initial value
    # is havoced (see docstring: it may be inherited-truthy or absent-falsy).
    # And this step refuses exactly the declarations the predicate holds of.
    # Refusing ISSUES this step's own report token FOR THE REPORT IT RAISES: the
    # report a declarer gets in that case is the very object this step worded
    # about the declaration it read, so the token is obtainable only by having
    # run the step, been refused, and passed THAT object on.
    Exsures(BaseStepRefused,
            base_step_refuses(identity)
            and base_step_report(RaisedException(), identity))


@ContractOnly
def finalize_grouping(grouping: EnumGrouping, identity: int) -> EnumGrouping:
    """The unchanged value-distinctness step the construction hands the finished
    grouping to, and whose result the construction delivers.  It is reached
    normally, AFTER the flag has been recorded, so the declarations it refuses are
    inside the specified behaviour rather than outside it.

    It is TOTAL over declarations: either it hands BACK THE SAME grouping,
    unaltered in both modelled facts (identity and the flag as recorded), passing
    the provenance token along; or it REFUSES and reports `RepeatedChoiceValue`,
    and it refuses exactly the declarations `repeats_choice_value` holds of.
    Bounded work over the declared choices, so it terminates (measure 1).
    Provenance + executable soundness: mapping.md / axiom_check.py.
    """
    Requires(MustTerminate(1))
    Requires(built_from_declaration(grouping, identity))
    Requires(Acc(grouping.identity) and Acc(grouping.preserve_when_callable))
    Requires(grouping.identity == identity)
    Ensures(not repeats_choice_value(identity))
    Ensures(built_from_declaration(Result(), identity))
    Ensures(Acc(Result().identity) and Acc(Result().preserve_when_callable))
    # The SAME object comes back, with both modelled facts as they were handed
    # over: this step is a check, not a rebuild, so it cannot be used to launder
    # a flag that was never recorded.
    Ensures(Result() is grouping)
    Ensures(Result().identity == identity)
    Ensures(Result().preserve_when_callable == Old(grouping.preserve_when_callable))
    # Handing the grouping back ISSUES this step's CONFIRMATION token for that
    # object: this step, and only this step, decides value-distinctness, so the
    # token records that the decision was actually made here rather than
    # anticipated by the caller off the declaration.
    Ensures(distinctness_confirmed(Result(), identity))
    # Refusing ISSUES this step's own report token for THE REPORT IT RAISES, for
    # the same reason the base step's does: the report a declarer gets names the
    # offending choices as this step words it, so it must be the object this step
    # raised, not a replacement composed around it.
    Exsures(RepeatedChoiceValue,
            repeats_choice_value(identity)
            and distinctness_step_report(RaisedException(), identity))


@Pure
@ContractOnly
def base_step_refuses(identity: int) -> bool:
    """Whether the BASE construction step itself refuses this declaration: its
    declared kind cannot carry the declared choice values at all, or it names a
    choice after a table that step must itself bind.  Those refusals happen
    inside that step, before any flag can be recorded on anything, which is why
    they are the base step's own report to pass on rather than a region of
    behaviour to invent.  Note what is NOT here: a declaration that repeats a
    choice value is NOT refused by this step — it is refused at the very end, by
    the value-distinctness step, and `repeats_choice_value` carries that.  This
    is a property of the declaration alone, settled before the construction
    starts, and it is opaque here (both outcomes are realizable, neither is
    assumed).  Provenance + executable soundness: mapping.md / axiom_check.py.
    """


@Pure
@ContractOnly
def flag_name_taken_by_choice(identity: int) -> bool:
    """Whether the declaration this grouping is built from declares one of its
    own choices under the very name the preserve-when-callable flag is recorded
    under.  This is the table the recording step consults: a constructed
    grouping refuses to rebind a name its own declared choices already occupy.
    It is a property of the declaration, so it is settled before the
    construction starts and is opaque here (both outcomes are realizable,
    neither is assumed).  Provenance + executable soundness: mapping.md / axiom_check.py.
    """


@Pure
@ContractOnly
def repeats_choice_value(identity: int) -> bool:
    """Whether the declaration gives two of its declared choices the same value —
    the table the value-distinctness step consults at the very END of the
    construction, after the flag has been recorded.  It is a property of the
    declaration, so it is settled before the construction starts and is opaque
    here (both outcomes are realizable, neither is assumed).  It is INDEPENDENT
    of `base_step_refuses` and of `flag_name_taken_by_choice`: every combination
    is realizable, so no clause below may be discharged by assuming one of them
    settles another.  Provenance + executable soundness: mapping.md /
    axiom_check.py.
    """


@Pure
@ContractOnly
def resolved_in_template(grouping: EnumGrouping) -> int:
    """The unchanged template variable-resolution rule, specialised to a
    callable object whose no-argument invocation cannot succeed (which a class
    object representing the grouping is — constructing a member requires a
    value).  Such an object is preserved (its own identity is the resolution
    result) exactly when it is flagged to be preserved when callable; otherwise
    the rule invokes it, the invocation fails, and the result is the
    invalid-value sentinel.  Provenance + executable soundness: mapping.md /
    axiom_check.py.
    """
    Requires(Acc(grouping.identity, 1 / 8) and Acc(grouping.preserve_when_callable, 1 / 8))
    Ensures(Implies(grouping.preserve_when_callable, Result() == grouping.identity))
    Ensures(Implies(not grouping.preserve_when_callable, Result() == INVALID_VALUE))
# axioms-end


# pure-start
# (no auxiliary pure spec functions are required for this behaviour)
# pure-end


def build_template_usable_grouping(identity: int) -> EnumGrouping:
    # pre-conditions-start
    # TOTAL correctness: constructing a grouping must actually DELIVER one, or
    # make one of the three refusals the case split below demands.
    # Declaring an enumeration is bounded work over the members declared for it
    # and the declaration hands the finished grouping back to its declarer; a
    # construction that never returns leaves the enumeration undeclarable and
    # every template mentioning it unusable. Under partial-correctness semantics
    # a body that never reaches its return (an endless loop, or a construction
    # that re-enters itself) satisfies every Ensures below only vacuously while
    # delivering no grouping at all. Measure 2: the body may invoke the bounded
    # construction and value-distinctness steps and build groupings (measure 1)
    # but may NOT re-enter this construction itself.
    Requires(MustTerminate(2))
    Requires(identity > 0)
    # Exactly ONE pending declaration is available to build from, so the base
    # construction step may be run exactly once and the delivered grouping must
    # be the one THAT run produced.
    Requires(declaration_available(identity))
    # NOTE: there is deliberately NO precondition restricting WHICH declarations
    # are specified. Every declaration is in scope, and the Ensures/Exsures below
    # form a complete case split over the three refusals: a declaration the base
    # step refuses, one that names a choice after the flag's own name, one that
    # repeats a choice value, and everything else. A precondition excluding any
    # of them would hand an implementation a region it could behave arbitrarily
    # in while the declared enumerations that land there are ordinary, reachable
    # ones whose reported refusal is observable to their declarer.
    # pre-conditions-end
    # post-conditions-start
    # DELIVERY is mandatory off the three refusals, and only off them: each
    # clause here makes the corresponding refusal MANDATORY rather than optional
    # (the Exsures below only describe the state once a refusal has occurred;
    # these clauses force that the right one occurs).
    #
    # (a) The base construction step did not refuse. The only way to establish
    #     this is to have RUN that step and had it deliver, so a body cannot
    #     invent a refusal for a declaration that step accepts, nor deliver a
    #     grouping for one it rejects.
    Ensures(not base_step_refuses(identity))
    # (b) The name the flag is recorded under is not already taken by one of the
    #     grouping's own declared choices.
    Ensures(not flag_name_taken_by_choice(identity))
    # (c) The declaration does not repeat a choice value. Establishing this needs
    #     the value-distinctness step to have been run and to have handed the
    #     grouping back, which happens only AFTER the flag is recorded.
    Ensures(not repeats_choice_value(identity))
    # The delivered grouping is the one the base construction step built from
    # this declaration (the provenance token, passed along by the
    # value-distinctness step) — not merely some object reporting that identity.
    Ensures(built_from_declaration(Result(), identity))
    # ...and the value-distinctness step ITSELF confirmed, on that very grouping,
    # that the declared choice values are distinct. (c) above says the
    # declaration does not repeat a value; this says WHO established it. Without
    # it a construction could read the declaration, conclude the values are
    # distinct and deliver on its own authority, never reaching the step whose
    # decision that is — and would then have to word that step's refusal itself
    # on the declarations it does refuse.
    Ensures(distinctness_confirmed(Result(), identity))
    Ensures(Acc(Result().identity) and Acc(Result().preserve_when_callable))
    # The grouping keeps the identity it was created with.
    Ensures(Result().identity == identity)
    # The grouping is flagged to be preserved (left as-is) rather than invoked
    # when it is met as a callable during template variable resolution.
    Ensures(Result().preserve_when_callable == True)
    # The discriminating guarantee the behaviour demands: resolving the grouping
    # as a template variable yields the grouping object itself (so a following
    # member access can proceed), never the invalid-value sentinel.
    Ensures(resolved_in_template(Result()) == identity)
    Ensures(resolved_in_template(Result()) != INVALID_VALUE)
    # REFUSAL 1: the base construction step's own report, passed on UNCHANGED.
    # It may escape only for a declaration that step actually refuses, so a body
    # cannot report it for one that step accepts — AND the report the declarer
    # receives must BE that step's report, carrying the token that step issued
    # for it, so a construction can neither anticipate the refusal off the
    # declaration nor swap the step's report for one it composed itself.
    Exsures(BaseStepRefused,
            base_step_refuses(identity)
            and base_step_report(RaisedException(), identity))
    # REFUSAL 2: one of the grouping's own declared choices already occupies the
    # name the flag is recorded under, so the recording is refused and NO
    # grouping is delivered. Confined to declarations the base step accepted:
    # that step's refusal comes first and carries its own report.
    Exsures(PreserveFlagNameTaken,
            flag_name_taken_by_choice(identity) and not base_step_refuses(identity))
    # REFUSAL 3: the value-distinctness step at the END of the construction
    # refused, because the declaration repeats a choice value. Confined to
    # declarations that got that far: neither earlier step refused, and in
    # particular a declaration that ALSO names a choice after the flag's name
    # must report refusal 2, since the flag is recorded BEFORE this step runs.
    # This is the clause that denies a body the freedom to treat a repeated
    # choice value as an unspecified region and report whatever it likes there.
    # The report delivered must also BE that step's own report object (carrying
    # the token it issued for it), not one the construction worded itself after
    # reading the declaration, and not a replacement wrapped around the step's:
    # the declarer sees the report's content, which names the offending choices
    # as the step naming them does.
    Exsures(RepeatedChoiceValue,
            repeats_choice_value(identity) and not base_step_refuses(identity)
            and not flag_name_taken_by_choice(identity)
            and distinctness_step_report(RaisedException(), identity))
    # post-conditions-end
    # impl-start
    grouping = base_class_creation(identity)  # type: EnumGrouping
    delivered = finalize_grouping(grouping, identity)  # type: EnumGrouping
    return delivered
    # impl-end
