"""Twin-artifact model for astropy__astropy-14096.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A coordinate object has a *fallback* attribute resolver for a requested name.
  The resolver attempts an ordered sequence of candidate resolutions and yields
  the outcome of the FIRST one its guards select:

    1. a frame-name alias,
    2. a frame attribute,
    3. a passthrough to the underlying frame object,
    4. a transform target, and — when none of those guards selects —
    5. the residual resolution of that same name.

  Every one of these steps except the alias is PARTIAL: producing a frame
  attribute, a frame passthrough, a transform target, or a residual resolution can
  itself fail, in which case the resolver surfaces that step's own failure
  instead of a value. So the resolver does NOT guarantee that a selected step
  returns. What it guarantees is that it is a CONDUIT for the step its guards
  selected, on both of that step's paths:

    * if the resolver returns, the selected step succeeded and the value is that
      step's value; and
    * if the resolver fails, the selected step failed and the failure is that
      step's own.

  Neither outcome is the resolver's to invent, and the resolver may not convert
  one of a step's outcomes into the other (it may not swallow a step's failure
  and return a value of its own, nor fail where the step succeeded).

  On leg 5 the surfaced failure additionally carries an observable *subject*:
  the name that the residual resolution of `name` found missing. That subject is in
  general NOT the requested name — a computed accessor for the requested name
  may internally read a different, absent name — and the subject the resolver
  reports is the one the residual resolution found missing, not the requested name.

The requested name and the failure subject are modelled abstractly as integer
symbol ids (a stable id per distinct name); Nagini bans `str` indexing, and the
discriminating observable is *which name the surfaced failure blames*, not its
characters. Each step is an unchanged callee the resolver invokes; the steps are
axiomatised, and each `*_succeeds(name)` selector is that step's own path fact
for the call, not a choice the resolver makes. A surfaced failure is carried by a
user-defined exception (a builtin exception in an `Exsures` crashes the
translator).

The conduit discipline is not only WHICH outcome a leg carries but the
CONTROL-FLOW EFFECT behind it: the resolver must actually PERFORM the step its
guards selected and surface THAT step's outcome, rather than fabricate an
outcome that happens to agree with it. That effect is invisible to a plain value
abstraction, since a step's value and its failure subject are also readable from
the pure oracles. It is therefore pinned per step with an abstract, unforgeable
capability token — `frame_attr_step_performed(name)`,
`passthrough_step_performed(name)`, `transform_step_performed(name)`,
`residual_step_performed(name)` — each an opaque predicate with NO body whose
SOLE producers are that step's own two paths. Because nothing can `Fold` a
body-less predicate into existence, a leg can present the token its contract
demands only by ACTUALLY performing that leg's step (directive-8 / control-flow
grounding; the effect is tied to the effect-producing step, not to a copyable
value). The tokens force the work to be done; the oracles say WHICH value and
WHICH subject the leg must then surface.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Optional
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


class AttributeAccessError(Exception):
    """A surfaced attribute-resolution failure, carrying the symbol id of the
    name the failure blames. Stands in for the failure the desired behaviour
    surfaces (a builtin exception in an `Exsures` crashes the Nagini
    translator; mapping.md §2)."""

    def __init__(self, subject: int) -> None:
        Requires(MustTerminate(1))
        self.subject = subject  # type: int
        Ensures(Acc(self.subject) and self.subject == subject)


# axioms-start
# ================================================================ step 2 of 5
@Pure
@ContractOnly
def frame_attr_step_succeeds(name: int) -> bool:
    """Whether producing the frame-attribute candidate for `name` SUCCEEDS
    rather than failing. This is that step's own path fact for the call, not a
    choice the resolver makes. Unchanged callee; the weakest fact the proof
    needs is that it is a function of `name` in the calling context.
    Provenance + executable soundness check: mapping.md §3 / axiom_check.py."""
    Ensures(True)


@ContractOnly
@Predicate
def frame_attr_step_performed(name: int) -> bool:
    pass


@ContractOnly
def frame_attr_step(name: int, value: int) -> int:
    """Produce the frame-attribute candidate for `name`, whose value is `value`.
    It is PARTIAL and the contract states both paths: where
    `frame_attr_step_succeeds(name)` it returns `value`, otherwise it fails,
    surfacing an `AttributeAccessError`. Both paths grant
    `frame_attr_step_performed(name)`. Provenance: mapping.md §3."""
    Requires(MustTerminate(6))
    Ensures(frame_attr_step_succeeds(name)
            and Result() == value
            and frame_attr_step_performed(name))
    Exsures(AttributeAccessError,
            (not frame_attr_step_succeeds(name))
            and Acc(RaisedException().subject)
            and frame_attr_step_performed(name))


# ================================================================ step 3 of 5
@Pure
@ContractOnly
def passthrough_step_succeeds(name: int) -> bool:
    """Whether producing the frame-passthrough candidate for `name` SUCCEEDS
    rather than failing — that step's own path fact for the call. Unchanged
    callee; the weakest fact the proof needs is that it is a function of `name`
    in the calling context. Provenance + executable soundness check:
    mapping.md §3 / axiom_check.py."""
    Ensures(True)


@ContractOnly
@Predicate
def passthrough_step_performed(name: int) -> bool:
    pass


@ContractOnly
def passthrough_step(name: int, value: int) -> int:
    """Produce the frame-passthrough candidate for `name`, whose value is
    `value`. PARTIAL, both paths stated: where
    `passthrough_step_succeeds(name)` it returns `value`, otherwise it fails
    with an `AttributeAccessError`. Both paths grant
    `passthrough_step_performed(name)`. Provenance: mapping.md §3."""
    Requires(MustTerminate(6))
    Ensures(passthrough_step_succeeds(name)
            and Result() == value
            and passthrough_step_performed(name))
    Exsures(AttributeAccessError,
            (not passthrough_step_succeeds(name))
            and Acc(RaisedException().subject)
            and passthrough_step_performed(name))


# ================================================================ step 4 of 5
@Pure
@ContractOnly
def transform_step_succeeds(name: int) -> bool:
    """Whether producing the transform-target candidate for `name` SUCCEEDS
    rather than failing — that step's own path fact for the call. Unchanged
    callee; the weakest fact the proof needs is that it is a function of `name`
    in the calling context. Provenance + executable soundness check:
    mapping.md §3 / axiom_check.py."""
    Ensures(True)


@ContractOnly
@Predicate
def transform_step_performed(name: int) -> bool:
    pass


@ContractOnly
def transform_step(name: int, value: int) -> int:
    """Produce the transform-target candidate for `name`, whose value is
    `value`. PARTIAL, both paths stated: where
    `transform_step_succeeds(name)` it returns `value`, otherwise it fails with
    an `AttributeAccessError`. Both paths grant
    `transform_step_performed(name)`. Provenance: mapping.md §3."""
    Requires(MustTerminate(6))
    Ensures(transform_step_succeeds(name)
            and Result() == value
            and transform_step_performed(name))
    Exsures(AttributeAccessError,
            (not transform_step_succeeds(name))
            and Acc(RaisedException().subject)
            and transform_step_performed(name))


# ================================================================ step 5 of 5
@Pure
@ContractOnly
def residual_step_succeeds(name: int) -> bool:
    """Whether the residual resolution of `name` SUCCEEDS (yields a value) rather
    than failing — that step's own path fact for the call, so the resolver
    cannot return where the residual resolution failed, nor fail where it
    succeeded. Unchanged callee; the weakest fact the proof needs is that it is
    a function of `name` in the calling context. Provenance + executable
    soundness check: mapping.md §3 / axiom_check.py."""
    Ensures(True)


@Pure
@ContractOnly
def residual_step_value(name: int) -> int:
    """The value the residual resolution of `name` yields where it SUCCEEDS.
    Unchanged callee; the weakest fact the proof needs is that it is a function
    of `name` in the calling context, so a resolver cannot invent a value and
    call it the residual resolution's. Provenance + executable soundness check:
    mapping.md §3 / axiom_check.py."""
    Ensures(True)


@Pure
@ContractOnly
def residual_step_subject(name: int) -> int:
    """The symbol id the residual resolution of `name` blames when it FAILS: the
    name that resolution found missing, which is in general distinct from
    `name` itself (a computed accessor for `name` may internally read another,
    absent name). Unchanged callee; the weakest fact the proof needs about it is
    that it is a function of `name`. Provenance + executable soundness check:
    mapping.md §3 / axiom_check.py."""
    Ensures(True)


@ContractOnly
@Predicate
def residual_step_performed(name: int) -> bool:
    pass


@ContractOnly
def residual_step(name: int) -> int:
    """Produce the residual resolution of `name` (the candidate leg 5 selects).
    PARTIAL, both paths stated:

      * where `residual_step_succeeds(name)` it yields
        `residual_step_value(name)`; or
      * otherwise it fails, surfacing an `AttributeAccessError` whose blamed
        subject is `residual_step_subject(name)` — the name it found missing,
        NOT necessarily `name`.

    Which path it takes is that step's own fact, recorded by the
    `residual_step_succeeds(name)` selector; the contract deliberately does
    NOT claim the step always fails, so a consumer must be correct on both paths
    and cannot turn one into the other. Both paths grant
    `residual_step_performed(name)`. Provenance: mapping.md §3."""
    Requires(MustTerminate(6))
    Ensures(residual_step_succeeds(name)
            and Result() == residual_step_value(name)
            and residual_step_performed(name))
    Exsures(AttributeAccessError,
            (not residual_step_succeeds(name))
            and Acc(RaisedException().subject)
            and RaisedException().subject == residual_step_subject(name)
            and residual_step_performed(name))
# axioms-end


# pure-start
# (no module-level pure helpers required)
# pure-end


def resolve_missing(name: int,
                    is_alias: bool, alias_value: int,
                    is_frame_attr: bool, frame_attr_value: int,
                    is_frame_passthrough: bool, passthrough_value: int,
                    is_transform: bool, transform_value: int) -> int:
    # pre-conditions-start
    # All inputs are plain integers / booleans (no heap permission needed). The
    # four boolean flags model, in order, the guards that select among the first
    # four candidate resolutions; the paired *_value ints model the value each
    # selected step yields where it succeeds.
    Requires(MustTerminate(10))
    # pre-conditions-end
    # post-conditions-start
    # NORMAL-RETURN PATHS, one per leg, in guard priority order (alias, then
    # frame attribute, then frame passthrough, then transform, then the base
    # resolution). Each says the same three things about the leg the guards
    # selected: that step SUCCEEDED, the returned value is that step's value,
    # and the return carries that step's unforgeable capability token — so a
    # normal return is legal only as the selected step's own success passed
    # through. The value is not the resolver's to choose, the token cannot be
    # forged, and the `*_succeeds(name)` selector forbids returning where the
    # step FAILED, so a resolver that performs a step and then swallows its
    # failure to return a value of its own is rejected even though it can
    # present the token.
    #
    # Leg 1 (alias) is the one TOTAL step: it cannot fail, so it needs no
    # selector or token, and the matching `not is_alias` conjunct in the Exsures
    # below records that no failure may escape from it.
    Ensures(Implies(is_alias, Result() == alias_value))
    Ensures(Implies((not is_alias) and is_frame_attr,
                    frame_attr_step_succeeds(name)
                    and Result() == frame_attr_value
                    and frame_attr_step_performed(name)))
    Ensures(Implies((not is_alias) and (not is_frame_attr)
                    and is_frame_passthrough,
                    passthrough_step_succeeds(name)
                    and Result() == passthrough_value
                    and passthrough_step_performed(name)))
    Ensures(Implies((not is_alias) and (not is_frame_attr)
                    and (not is_frame_passthrough) and is_transform,
                    transform_step_succeeds(name)
                    and Result() == transform_value
                    and transform_step_performed(name)))
    Ensures(Implies((not is_alias) and (not is_frame_attr)
                    and (not is_frame_passthrough) and (not is_transform),
                    residual_step_succeeds(name)
                    and Result() == residual_step_value(name)
                    and residual_step_performed(name)))
    # FAILING PATHS. A surfaced failure is always the selected step's own: the
    # leg's `*_succeeds(name)` selector must say that step FAILED (so the
    # resolver may not fail where its step succeeded), and the failure must
    # carry that step's unforgeable token (so it may not be fabricated — a
    # resolver that never performs the step, or performs a DIFFERENT leg's step,
    # holds no token for this one). Leg 1 is total, hence the unconditional
    # `not is_alias`: no failure may escape the alias leg at all.
    #
    # On leg 5 the failure has one further observable, and it is the
    # discriminating one: the blamed subject is `residual_step_subject(name)`,
    # the name the residual resolution found missing — which the spec does NOT
    # assume equals `name`, so a resolver blaming the requested name instead
    # does not satisfy this clause.
    Exsures(AttributeAccessError,
            (not is_alias)
            and Acc(RaisedException().subject)
            and Implies(is_frame_attr,
                        (not frame_attr_step_succeeds(name))
                        and frame_attr_step_performed(name))
            and Implies((not is_frame_attr) and is_frame_passthrough,
                        (not passthrough_step_succeeds(name))
                        and passthrough_step_performed(name))
            and Implies((not is_frame_attr) and (not is_frame_passthrough)
                        and is_transform,
                        (not transform_step_succeeds(name))
                        and transform_step_performed(name))
            and Implies((not is_frame_attr) and (not is_frame_passthrough)
                        and (not is_transform),
                        (not residual_step_succeeds(name))
                        and RaisedException().subject == residual_step_subject(name)
                        and residual_step_performed(name)))
    # post-conditions-end
    # impl-start
    if is_alias:
        return alias_value
    if is_frame_attr:
        return frame_attr_step(name, frame_attr_value)
    if is_frame_passthrough:
        return passthrough_step(name, passthrough_value)
    if is_transform:
        return transform_step(name, transform_value)
    return residual_step(name)
    # impl-end
