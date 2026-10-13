"""Twin-artifact model for django__django-14404.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A final fall-through view decides whether a request whose URL lacks a
  trailing slash should be permanently redirected to the slash-terminated
  form. The redirect is issued only when slash-appending is enabled, the
  requested URL does not already end with a slash, the slash-terminated form
  resolves to a routable view, and that view does not opt out of slash
  appending. In every other case the view signals "not found".

  When a redirect IS issued, its target must be the request's FULL externally
  visible path -- the one a client would type, INCLUDING any deployment path
  prefix under which the application is mounted -- with a single trailing
  slash appended. The prefix-stripped, application-relative form of the path
  must NOT be used as the redirect target: a deployment served under a path
  prefix would otherwise redirect clients to a location missing that prefix.

The externally visible path and the prefix-stripped path are both modelled as
read-only `List[int]` sequences of code points (Nagini bans `str` indexing);
the trailing slash is the code point 47. The control-flow guards that decide
whether to redirect (slash-appending enabled, the URL's trailing-slash state,
the resolve outcome, the view's opt-out flag) are modelled as booleans. The
"not found" signal is a user-defined exception.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


class NotFound(Exception):
    """The fall-through "no routable target" signal (a not-found result)."""


# axioms-start
# (no callee needs axiomatizing: the resolve outcome and the opt-out flag are
#  modelled as the booleans they reduce to at this site; the only changed
#  operation -- which path the redirect target is built from -- is modelled
#  deeply over the code-point sequences.)
# axioms-end


# pure-start
@Pure
def with_trailing_slash(p: PSeq[int]) -> PSeq[int]:
    """The slash-terminated form of a path: the path followed by code point 47
    ('/'). This is the redirect target's shape over a chosen base path."""
    return p + PSeq(47)
# pure-end


def slash_redirect_target(
        full_path: List[int],
        app_relative_path: List[int],
        append_slash_enabled: bool,
        url_has_trailing_slash: bool,
        slash_form_resolves: bool,
        target_view_opts_in: bool) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(full_path), 1 / 2))
    Requires(Acc(list_pred(app_relative_path), 1 / 2))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(full_path), 1 / 2))
    Ensures(Acc(list_pred(app_relative_path), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # A value is returned (a redirect is issued) on EXACTLY the conjunction of
    # the four guards; otherwise the not-found signal is raised.
    Ensures(append_slash_enabled and not url_has_trailing_slash
            and slash_form_resolves and target_view_opts_in)
    # The redirect target is the FULL externally visible path (with any
    # deployment prefix) plus a single trailing slash -- grounded structurally
    # in the full-path input, never the prefix-stripped path.
    Ensures(ToSeq(Result()) == with_trailing_slash(ToSeq(full_path)))
    # The not-found signal is raised on EXACTLY the negation of that conjunction
    # (slash-appending off, the URL already ends with a slash, the slash form
    # does not resolve, or the resolved view opts out).
    Exsures(NotFound, append_slash_enabled is False
            or url_has_trailing_slash is True
            or slash_form_resolves is False
            or target_view_opts_in is False)
    # post-conditions-end
    # impl-start
    if append_slash_enabled and not url_has_trailing_slash:
        if slash_form_resolves:
            if target_view_opts_in:
                result = list(full_path)  # type: List[int]
                result.append(47)
                return result
    raise NotFound()
    # impl-end
