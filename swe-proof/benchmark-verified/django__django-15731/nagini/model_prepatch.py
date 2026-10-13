"""Twin-artifact model for django__django-15731.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A proxy callable is built that forwards to a source callable. The proxy's
  observable metadata must agree with the source so that introspection of the
  proxy reports the SAME information introspection of the source would report.
  Two pieces of metadata are observed here:

    (1) the proxy's display name and documentation equal the source's, and

    (2) the parameter signature reported for the proxy equals the source's
        declared signature -- NOT the proxy's own forwarding signature (which
        merely captures arbitrary positional/keyword arguments and would
        otherwise be reported).

  Property (2) is what makes signature introspection report the source's true
  parameters. The standard signature resolver, when a callable records the
  ORIGINAL callable it stands in for, reports that original callable's
  signature instead of the forwarding one. So the proxy must record the source
  it stands in for; recording only name and documentation is insufficient,
  because the resolver then falls back to the proxy's own forwarding signature.

  The desired behaviour is pinned exactly, not merely up to the reported
  observable:

    (3) the proxy's OWN declared signature is the forwarding parameter list
        (the change does not touch the proxy's own parameter list), and

    (4) the proxy ALWAYS records the source it stands in for -- the recording
        is unconditional (not, e.g., applied only when the source's signature
        happens to differ from the forwarding one) -- and what it records is
        the source's own signature.

  Clauses (3)/(4) close the free fields a rival implementation could vary
  while still meeting (1)/(2): they pin every metadata field of the built
  proxy to the value the desired builder actually produces.

A callable's introspectable metadata is modelled as a minimal record exposing
only the touched fields: a display-name code, a documentation code, a flag
recording whether the callable stands in for an original callable, and the
recorded original's signature code. Names / docstrings / signatures are
modelled as integer codes (the tested behaviour observes only equality between
the proxy's reported metadata and the source's). The signature resolver
(`reported_signature`) is the unchanged standard introspection callee: it is
axiomatized and its `Ensures` is consumed by the proof; its soundness against
the real resolver is validated out-of-band (axiom_check.py / G-AX).

`SIG_FORWARDING` is the signature code of the proxy's own forwarding parameter
list; any genuine source whose own signature differs from it (every real
proxied method here) is reported wrongly unless the source is recorded.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# pure-start
@Pure
def SIG_FORWARDING() -> int:
    """The signature code of the proxy's own forwarding parameter list (the
    one that captures arbitrary positional and keyword arguments). Reported for
    a proxy that records no original callable to stand in for."""
    return 0
# pure-end


# axioms-start
@Pure
@ContractOnly
def reported_signature(wrapped: bool, target_sig: int) -> int:
    """The signature an introspection of a callable reports (the unchanged
    standard resolver). When the callable records an original callable it
    stands in for (`wrapped`), the recorded original's signature
    (`target_sig`) is reported; otherwise the callable's own forwarding
    signature is reported. Provenance + executable soundness validation:
    mapping.md / axiom_check.py."""
    Ensures(Implies(wrapped, Result() == target_sig))
    Ensures(Implies(not wrapped, Result() == SIG_FORWARDING()))
# axioms-end


class Func:
    def __init__(self) -> None:
        # Straight-line constructor: no loops, no calls. Level 1 sits strictly
        # below every builder that constructs a Func, so the caller has room to
        # discharge its own obligation across this call.
        Requires(MustTerminate(1))
        Ensures(Acc(self.name) and Acc(self.doc))  # type: ignore
        Ensures(Acc(self.wrapped) and Acc(self.target_sig))  # type: ignore
        Ensures(Acc(self.sig))  # type: ignore
        Ensures(self.name == 0 and self.doc == 0)  # type: ignore
        Ensures(self.wrapped == False and self.target_sig == 0)  # type: ignore
        Ensures(self.sig == SIG_FORWARDING())  # type: ignore
        # name / doc: introspectable identity strings (as integer codes)
        self.name = 0  # type: int
        self.doc = 0  # type: int
        # wrapped: whether this callable records an original it stands in for
        self.wrapped = False  # type: bool
        # target_sig: the recorded original's signature code (meaningful only
        # when `wrapped`)
        self.target_sig = 0  # type: int
        # sig: this callable's own declared signature code
        self.sig = SIG_FORWARDING()  # type: int


def build_proxy(source: Func) -> Func:
    # pre-conditions-start
    # The source callable is read-only: its metadata is required (and ensured)
    # only at fractional permission.
    Requires(Acc(source.name, 1 / 2) and Acc(source.doc, 1 / 2))
    Requires(Acc(source.sig, 1 / 2))
    Requires(MustTerminate(6))
    # pre-conditions-end
    # post-conditions-start
    # The source callable is left exactly as it was, untouched.
    Ensures(Acc(source.name, 1 / 2) and Acc(source.doc, 1 / 2))
    Ensures(Acc(source.sig, 1 / 2))
    Ensures(source.name == Old(source.name))
    Ensures(source.doc == Old(source.doc))
    Ensures(source.sig == Old(source.sig))

    # The proxy is a fully-owned, distinct object.
    Ensures(Acc(Result().name) and Acc(Result().doc))
    Ensures(Acc(Result().wrapped) and Acc(Result().target_sig))
    Ensures(Acc(Result().sig))
    Ensures(Result() is not source)

    # (1) The proxy's display name and documentation equal the source's.
    Ensures(Result().name == source.name)
    Ensures(Result().doc == source.doc)

    # (2) The signature reported for the proxy equals the source's declared
    # signature -- the discriminating guarantee. It holds because the proxy
    # records the source it stands in for, so the resolver reports the source's
    # signature rather than the proxy's own forwarding signature.
    Ensures(reported_signature(Result().wrapped, Result().target_sig)
            == source.sig)

    # (3) The proxy's OWN declared signature is the forwarding parameter list:
    # the change decorates the proxy, it does not alter the proxy's own
    # parameter list (def manager_method(self, *args, **kwargs) is unchanged).
    Ensures(Result().sig == SIG_FORWARDING())

    # (4) The recording of the original is UNCONDITIONAL, and what is recorded
    # is the source's own signature. The builder always records the source it
    # stands in for -- never only on a sub-domain of sources (e.g. only when
    # the source's signature differs from the forwarding one).
    Ensures(Result().wrapped)
    Ensures(Result().target_sig == source.sig)
    # post-conditions-end
    # impl-start
    proxy = Func()
    # proxy's own forwarding parameter list (def manager_method(self, *args,
    # **kwargs)) -- its own sig is the forwarding signature.
    proxy.sig = SIG_FORWARDING()
    # Pre-fix: only the display name and documentation are copied. The proxy
    # never records the original callable it stands in for, so the resolver
    # falls back to the proxy's own forwarding signature.
    proxy.name = source.name
    proxy.doc = source.doc
    return proxy
    # impl-end
