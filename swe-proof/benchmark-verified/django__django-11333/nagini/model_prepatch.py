"""Twin-artifact model for django__django-11333.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A routing-table object is expensive to build, so the lookup that hands one
  out memoizes its results in a shared cache keyed by a configuration selector.
  The selector may be supplied explicitly, or omitted; when it is omitted the
  lookup substitutes the process-wide default selector before doing anything
  else. The behaviour pinned here is that the memoization key is the
  RESOLVED selector -- the one obtained after the omitted-means-default
  substitution -- not the raw argument:

    (1) Omitting the selector and supplying the default selector explicitly are
        the same request: both resolve to the default selector, so they hand
        back the very same cached object. A routing table already built for the
        default selector is reused when the selector is omitted, rather than a
        second one being built and cached separately.

    (2) Two requests whose resolved selectors differ hand back distinct objects:
        each resolved selector owns its own cache slot, so omitting the selector
        never collides with a genuinely different selector.

  The consequence that matters: callers that omit the selector (e.g. before the
  default has been established for the thread) and callers that pass the default
  selector explicitly (e.g. after it has been established) share one cached
  routing table instead of redundantly constructing and storing two.

Modelling choices (Nagini fragment):
  * A selector is an ``int`` token; the omitted selector is ``Optional[int]``
    with ``None`` meaning "not supplied" (resolve to the default). The
    resolution mirrors the repo's "argument-or-default" expression
    (mapping.md §2). The process-wide default selector is the module-level
    constant ``default_selector()``.
  * The shared cache is a ``Dict[int, int]`` from a RESOLVED selector token to
    the identity token of the routing table built for it. Object identity in
    the repo (``is`` / ``is not`` in the tests) is carried by integer-identity
    of these tokens: equal tokens model the same object, distinct tokens model
    distinct objects (mapping.md §2).
  * Whether the RESOLVED selector is ALREADY cached at entry is captured as a
    ``bool`` parameter ``cached`` pinned by a precondition to the entry
    membership of the resolved selector, and the object already cached for it
    (when present) as an ``int`` parameter ``existing`` pinned to its entry
    value. These pre-state scalars let the memoization guarantee be gated on a
    genuine entry fact about the cache rather than on a membership/value query
    against the (mutated-in-place) cache, which an implementation could perturb
    by writing the slot itself (the django-12713 pattern).
  * The freshly built routing-table identity for a not-yet-cached selector is a
    ``fresh: int`` parameter, distinct from the already-cached object, modelling
    "construct a new object".

The cache is genuinely mutated in place (a new slot is added on a miss), so it
is held at FULL permission and its exact post-state is stated. No string
indexing is used (Nagini bans it). The whole behaviour is modelled deeply (the
omitted-means-default resolution and the lookup-or-insert keyed on the resolved
selector are spelled out in the impl region); there is no axiomatised callee.
Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Dict, Optional
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# No axioms: the memoized-on-resolved-selector lookup is the behaviour under
# specification and is spelled out deeply in the impl region. There is no
# unchanged opaque callee to axiomatise.
# axioms-end


# pure-start
@Pure
def default_selector() -> int:
    """The process-wide default selector substituted when none is supplied."""
    return 0


@Pure
def resolve_selector(selector: Optional[int]) -> int:
    """The resolved selector: the supplied one when supplied, otherwise the
    default. Mirrors the repo's argument-or-default expression. The omitted
    selector and the default selector resolve to the SAME value, which is the
    key fact the cache is keyed on."""
    if selector is None:
        return default_selector()
    return selector
# pure-end


def get_resolver(cache: Dict[int, int], selector: Optional[int],
                 cached: bool, existing: int, fresh: int) -> int:
    # pre-conditions-start
    # The shared cache may gain a new slot; full permission.
    Requires(dict_pred(cache))
    # ``cached`` captures, AT ENTRY, whether the RESOLVED selector already has a
    # cached object; ``existing`` captures that object's identity when it does.
    # Both are pre-state facts, bound before any mutation, so the memoization
    # guarantee below gates on the genuine entry state of the cache rather than
    # on a query against the (possibly mutated) cache.
    Requires(cached == (resolve_selector(selector) in cache))
    Requires(Implies(cached, cache[resolve_selector(selector)] == existing))
    # A freshly-built routing-table identity is a not-yet-used token: it differs
    # from the object already cached for the resolved selector (so a rebuild
    # would be observably a DIFFERENT object).
    Requires(Implies(cached, existing != fresh))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(dict_pred(cache))
    # The handed-back object is the one cached under the RESOLVED selector. A
    # request whose selector resolves to the default therefore reuses the cache
    # slot of the default selector, regardless of whether the selector was
    # supplied explicitly or omitted: both share one cached object.
    Ensures(resolve_selector(selector) in cache)
    Ensures(Result() == cache[resolve_selector(selector)])
    # Memoization: when the resolved selector was ALREADY cached at entry, the
    # request hands back that very same object -- the slot is reused, never
    # rebuilt. (Gated on the entry scalar ``cached``/``existing``, so an impl
    # cannot dodge it by writing the slot itself.)
    Ensures(Implies(cached, Result() == existing))
    # When the resolved selector was NOT yet cached at entry, it is built fresh.
    Ensures(Implies(not cached, Result() == fresh))
    # Distinctness: every selector OTHER than the resolved one keeps its own
    # cached object untouched, so distinct resolved selectors never collide --
    # omitting the selector hands back the default's object, never a different
    # selector's object.
    Ensures(Forall(int, lambda k: (Implies(
        Old(k in cache) and k != resolve_selector(selector),
        (k in cache) and cache[k] == Old(cache[k])))))
    # No selector slot is dropped; the cache only ever grows.
    Ensures(Forall(int, lambda k: (Implies(Old(k in cache), k in cache))))
    # post-conditions-end
    # impl-start
    # PRE-PATCH (buggy): the cache is keyed on the RAW argument, and the
    # omitted-means-default substitution happens only AFTER the cache lookup --
    # so the substitution chooses what to BUILD but not what to KEY on. An
    # omitted selector therefore keys on a distinct "no-argument" slot
    # (modelled by the -1 sentinel, which is not the default selector 0)
    # instead of the default selector's slot, so a routing table already built
    # for the default selector is missed and rebuilt under that separate slot.
    if selector is None:
        raw_key = -1
    else:
        raw_key = selector
    if raw_key in cache:
        return cache[raw_key]
    key = resolve_selector(selector)
    cache[raw_key] = fresh
    return fresh
    # impl-end
