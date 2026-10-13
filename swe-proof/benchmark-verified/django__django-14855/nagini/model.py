"""Twin-artifact model for django__django-14855.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A change-form (or edit) page rendered for one of several sibling
  administration deployments displays a read-only related object as a link.
  Several such deployments are registered under one shared application
  identifier; each deployment carries its own instance identifier (its name),
  its own URL prefix, and its own set of routes. They are distinguished only
  by that instance name.

  The link built for the related object must point INTO the very deployment
  that is currently rendering the page: the URL prefix of the produced link is
  the prefix registered for the current deployment's instance name, NOT the
  prefix of whichever deployment happens to be the registered default. When
  the current deployment is the default one the two coincide, but for any
  non-default current deployment the link must carry that deployment's own
  prefix. One deployment cannot be pointed into this way: a deployment whose
  instance identifier is EMPTY supplies nothing to resolve relative to, so the
  resolution callee cannot tell it from "no deployment named at all" and
  resolution for it lands on the default deployment's prefix.

  Resolution is PARTIAL, and the page states that too. The view identifier
  being resolved names a route that each deployment either carries or does
  not: `exposes[k]` is whether deployment k carries a route for the identifier
  and argument at hand. Resolution consults ONLY the deployment it lands in
  (the current one, or the default one for an empty instance identifier), so
  when that deployment carries no such route nothing resolves, the page shows
  the related object with NO link at all, and the produced value therefore
  carries no prefix -- modelled as the EMPTY sequence. A registered
  deployment's own prefix always carries at least the resolution root, so it
  is never empty and the empty result is unambiguous.

The instance-name selection performed when turning a view identifier into a
concrete URL (choosing which sibling deployment's prefix to use, given the
name of the deployment to resolve relative to, and looking the identifier up
inside that deployment) is an unchanged framework callee; it is axiomatized
here (`resolve_prefix`) as the WEAKEST contract the proof needs: a NON-EMPTY
registered instance name selects that instance, while an absent selector --
and equally an empty one, which the callee cannot tell apart from an absent
one -- selects the default instance; the selected instance's prefix is the
result when that instance carries the route, and nothing is produced when it
does not. Its soundness against the real callee is checked out-of-band by
axiom_check.py (G-AX).

Strings (instance names, URL prefixes) are modelled as `PSeq[int]` of Unicode
code points (Nagini bans `str` indexing). The registry of sibling deployments
is a triple of parallel pure sequences (instance name, URL prefix, carries the
route).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List, Optional
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
@Pure
@ContractOnly
def resolve_prefix(names: PSeq[PSeq[int]], prefixes: PSeq[PSeq[int]],
                   exposes: PSeq[bool], default_idx: int, selector: PSeq[int],
                   has_selector: bool) -> PSeq[int]:
    """Unchanged framework callee: turn a view identifier into a URL by
    choosing which sibling deployment's prefix to apply and looking the
    identifier up inside that deployment.

    `names`/`prefixes`/`exposes` are the parallel registry of the sibling
    deployments sharing one application identifier: instance name, URL prefix,
    and whether that deployment carries a route for the identifier and
    argument being resolved. `default_idx` is the registered default instance.
    `selector` (active only when `has_selector`) is the name of the deployment
    to resolve relative to.

    Contract (weakest the proof needs). Selection: a NON-EMPTY selector naming
    a registered instance selects that instance; no selector -- or an EMPTY
    one, which the callee cannot distinguish from no selector at all --
    selects the default instance. Production: the selected instance's prefix
    when that instance carries the route, and NOTHING (the empty sequence)
    when it does not.

    Partiality is a genuine part of the callee's behaviour, not a gap: the
    callee narrows to the selected instance FIRST and then looks the
    identifier up only there, so an identifier absent from that one instance
    yields no URL even when a sibling carries it. The callee signals that
    rather than returning, and the consumer's arm for the signal produces no
    link, so the composite produces no prefix; the empty sequence is that
    value. Since a registered deployment's prefix carries at least the
    resolution root (see the Requires below) it is never empty, so the empty
    result cannot be confused with any deployment's prefix.

    Emptiness of the SELECTOR is likewise behaviour, not a gap: the callee
    consults the selector only after testing it for emptiness, and an empty
    selector fails that test, so it never reaches the name matching and the
    default instance is selected. An empty selector is therefore IN this
    contract's domain and is governed by the no-selector clauses; it is not
    excluded.

    Domain restriction: the selector is matched only after the callee splits it
    on the U+003A (`:`) component separator and resolves component-wise, so the
    selector-naming clause holds only for separator-free selectors (a name that
    embeds the separator is split into components and is not matched whole). The
    consumer supplies a separator-free selector; selectors containing U+003A are
    outside this contract's domain.

    Domain restriction (the registry is a MAP, not an arbitrary pair of lists):
    the callee looks a deployment up BY its instance identifier, so a registry
    associates each identifier with at most one deployment and hence with at
    most one prefix. A registry that offered one identifier under two different
    prefixes describes no state this callee can be in -- it would demand two
    different results from one lookup -- so such registries are outside this
    contract's domain. Stating this is what keeps the clauses below jointly
    SATISFIABLE: with identifiers unique, a supplied selector matches at most
    one registered deployment, so at most one clause pins the result. Without
    it the contract would assert a single value equal to two distinct prefixes
    at once, which is a claim no total callee can meet -- an assumption strictly
    stronger than the callee, and one that would let anything at all be derived
    from it. The consumer resolves relative to a registry of distinguishable
    sibling deployments and so supplies an in-domain registry.

    Domain restriction (a registered deployment's prefix is non-empty): a URL
    the callee produces carries the resolution root before anything else, so
    the prefix a registered deployment contributes to it is at least that root
    and never the empty sequence. This is a fact about the callee's output, not
    an exclusion of any deployment: a deployment mounted at the root has the
    root itself as its prefix. It is what makes "produced nothing" (the empty
    sequence) distinguishable from every prefix the callee can produce.

    Provenance + executable soundness check: mapping.md / axiom_check.py.
    """
    Requires(len(names) == len(prefixes))
    Requires(len(exposes) == len(names))
    Requires(0 <= default_idx and default_idx < len(names))
    # Domain: instance identifiers are unique within the registry -- the callee
    # resolves a deployment BY identifier, so one identifier cannot stand for two
    # deployments with different prefixes. This is what makes the Ensures clauses
    # below jointly satisfiable (a selector matches at most one k), so the
    # contract stays a claim about a real lookup rather than an inconsistent one.
    Requires(Forall2(int, int, lambda a, b: (
        Implies(0 <= a and a < len(names) and 0 <= b and b < len(names)
                and names[a] == names[b], a == b),
        [[names[a], names[b]]])))
    # Domain: every registered deployment's prefix is non-empty -- a produced URL
    # carries the resolution root before anything else. This is what makes the
    # empty sequence (produced nothing) distinct from every producible prefix.
    Requires(Forall(int, lambda k: (
        Implies(0 <= k and k < len(prefixes), len(prefixes[k]) > 0),
        [[prefixes[k]]])))
    # Domain: the selector carries no U+003A (58) component separator (the
    # callee splits the selector on it before matching, so a separator-bearing
    # selector is not matched as a whole name -> outside this contract).
    Requires(Forall(int, lambda i: (
        Implies(0 <= i and i < len(selector), selector[i] != 58),
        [[selector[i]]])))
    # No selector -- or an EMPTY selector, which the callee tests for and cannot
    # tell from an absent one -> the registered default instance is selected, and
    # its prefix is the result exactly when it carries the route.
    Ensures(Implies((not has_selector or len(selector) == 0)
                    and exposes[default_idx],
                    Result() == prefixes[default_idx]))
    Ensures(Implies((not has_selector or len(selector) == 0)
                    and not exposes[default_idx],
                    len(Result()) == 0))
    # A NON-EMPTY selector naming a registered instance -> that instance is
    # selected, and its prefix is the result exactly when it carries the route;
    # the identifier is looked up in that instance ALONE, so an instance without
    # the route produces nothing even if a sibling has it. Emptiness is excluded
    # here because the callee never reaches the name matching for an empty
    # selector (see the docstring): claiming the instance's own prefix for it
    # would be stronger than the callee.
    Ensures(Forall(int, lambda k: (
        Implies(has_selector and len(selector) > 0
                and 0 <= k and k < len(names)
                and names[k] == selector and exposes[k],
                Result() == prefixes[k]),
        [[names[k]]])))
    Ensures(Forall(int, lambda k: (
        Implies(has_selector and len(selector) > 0
                and 0 <= k and k < len(names)
                and names[k] == selector and not exposes[k],
                len(Result()) == 0),
        [[names[k]]])))
# axioms-end


# pure-start
# (no auxiliary pure helpers needed)
# pure-end


def related_link_target(names: List[PSeq[int]], prefixes: List[PSeq[int]],
                        exposes: List[bool], default_idx: int,
                        current_idx: int) -> PSeq[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(names), 1 / 2))
    Requires(Acc(list_pred(prefixes), 1 / 2))
    Requires(Acc(list_pred(exposes), 1 / 2))
    Requires(len(names) == len(prefixes))
    Requires(len(exposes) == len(names))
    Requires(0 <= default_idx and default_idx < len(names))
    Requires(0 <= current_idx and current_idx < len(names))
    # Instance names are unique: siblings are distinguished by their name.
    Requires(Forall2(int, int, lambda a, b: (
        Implies(0 <= a and a < len(names) and 0 <= b and b < len(names)
                and ToSeq(names)[a] == ToSeq(names)[b], a == b),
        [[ToSeq(names)[a], ToSeq(names)[b]]])))
    # Every registered deployment's prefix is non-empty: a produced URL carries
    # the resolution root before anything else, so no deployment contributes the
    # empty sequence -- which is what a link-less page's value is.
    Requires(Forall(int, lambda k: (
        Implies(0 <= k and k < len(prefixes), len(ToSeq(prefixes)[k]) > 0),
        [[ToSeq(prefixes)[k]]])))
    # The current deployment's instance name carries no U+003A (58) component
    # separator: it is resolved as a whole instance name, not split into
    # components (the resolution callee splits its selector on this separator).
    Requires(Forall(int, lambda i: (
        Implies(0 <= i and i < len(ToSeq(names)[current_idx]),
                ToSeq(names)[current_idx][i] != 58),
        [[ToSeq(names)[current_idx][i]]])))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(names), 1 / 2))
    Ensures(Acc(list_pred(prefixes), 1 / 2))
    Ensures(Acc(list_pred(exposes), 1 / 2))
    Ensures(len(prefixes) == len(names))
    Ensures(len(exposes) == len(names))
    Ensures(0 <= current_idx and current_idx < len(prefixes))
    Ensures(0 <= default_idx and default_idx < len(prefixes))
    # The produced link carries the CURRENT deployment's prefix, whenever that
    # deployment has a non-empty instance identifier to be resolved relative to
    # AND carries a route for the identifier being resolved.
    Ensures(Implies(len(ToSeq(names)[current_idx]) > 0
                    and ToSeq(exposes)[current_idx],
                    Result() == ToSeq(prefixes)[current_idx]))
    # Resolution consults the current deployment ALONE, so a current deployment
    # that carries no such route produces no link and hence no prefix -- even
    # when a sibling deployment does carry one.
    Ensures(Implies(len(ToSeq(names)[current_idx]) > 0
                    and not ToSeq(exposes)[current_idx],
                    len(Result()) == 0))
    # A deployment with an EMPTY instance identifier supplies nothing to resolve
    # relative to, so resolution lands on the default deployment: its prefix
    # when that deployment carries the route, and no link otherwise. The four
    # guards are mutually exclusive and together total, so the returned value is
    # pinned on every admissible input.
    Ensures(Implies(len(ToSeq(names)[current_idx]) == 0
                    and ToSeq(exposes)[default_idx],
                    Result() == ToSeq(prefixes)[default_idx]))
    Ensures(Implies(len(ToSeq(names)[current_idx]) == 0
                    and not ToSeq(exposes)[default_idx],
                    len(Result()) == 0))
    # post-conditions-end
    # impl-start
    nm = ToSeq(names)
    pf = ToSeq(prefixes)
    ex = ToSeq(exposes)
    selector = nm[current_idx]  # type: PSeq[int]
    url = resolve_prefix(nm, pf, ex, default_idx, selector, True)
    # selector == names[current_idx] is a registered instance name (k=current);
    # uniqueness pins resolve_prefix's choice to prefixes[current_idx].
    Assert(nm[current_idx] == selector)
    return url
    # impl-end
