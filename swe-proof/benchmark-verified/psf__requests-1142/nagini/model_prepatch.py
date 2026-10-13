"""Twin-artifact model for psf__requests-1142.

Behaviour under specification (stated as desired behaviour, not as an edit):

  An outgoing HTTP request is being finalised, and a header that announces the
  size of the message body must be set on the request's header map. The size to
  announce depends on the body that will be sent:

    * If the body is a seekable stream (it can report its own position), the
      announced size is the stream's measured length.
    * Otherwise, if a body is actually present, the announced size is the
      length of that body.
    * Otherwise there is no body at all. A size MUST be announced only when the
      request method is one that carries a payload; for the payload-less
      methods that conventionally have no body (the read-only retrieval method
      and the headers-only method) NO size header is announced at all -- the
      header map is left without it. This is the behaviour that matters: a
      bodyless request using one of those two methods carries no body-size
      header, whereas a bodyless request using any other method announces a
      zero size.

  In every case the announced size, when present, equals the size determined
  above, and the request method itself is never altered by this operation.
  The operation writes AT MOST the body-size header: no other header of the
  map is added, removed, or changed.

Modelling choices (Nagini fragment):
  * The request's header map is a ``Dict[int, int]`` from a header-name token to
    the announced size. Membership of the body-size header's name token models
    "the size header is present"; its value models the announced size. Only
    presence and the per-name value are observed, so the integer carrier is
    faithful (mapping.md S2).
  * The HTTP method is a method-identity token (an ``int``); the two payload-
    less methods are the module constants ``method_get()`` and ``method_head()``
    and any other token is a payload-carrying method.
  * The body is described by the observations the operation makes on it: whether
    it is a seekable stream (``seekable``) and, if so, its measured length
    (``stream_len``); whether a non-stream body is present (``body_present``)
    and, if so, its length (``body_len``). ``not seekable and not body_present``
    is the bodyless case.

The header map is genuinely mutated in place, so it is held at full permission
and its exact post-state is stated; the read-only method token is not mutated.
The behaviour is modelled deeply (the guarded size announcement is spelled out
in the impl region); there is no axiomatised callee. Markers (machine-parsed)
delimit the spec / proof / impl regions.
"""
from typing import Dict
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# No axioms: the guarded body-size announcement is the behaviour under
# specification and is spelled out deeply in the impl region. There is no
# unchanged opaque callee to axiomatise.
# axioms-end


# pure-start
@Pure
def size_header() -> int:
    # The header-name token of the body-size header. Its presence as a key in
    # the header map models "the body-size header is announced".
    return 0


@Pure
def method_get() -> int:
    # Identity token of the read-only retrieval method (a payload-less method).
    return 1


@Pure
def method_head() -> int:
    # Identity token of the headers-only method (a payload-less method).
    return 2
# pure-end


def announce_body_size(headers: Dict[int, int], method: int,
                       seekable: bool, stream_len: int,
                       body_present: bool, body_len: int) -> None:
    # pre-conditions-start
    # The header map is mutated in place; full permission.
    Requires(dict_pred(headers))
    # The size header has not yet been announced when this operation runs: the
    # header map was just built fresh for this request and no body-size header
    # is present yet. The operation only ever announces the header, never
    # removes one, so for the bodyless payload-less case the header is absent
    # exactly because it was never announced.
    Requires(size_header() not in headers)
    # A seekable stream is always a present body (the non-bodyless case).
    Requires(Implies(seekable, body_present))
    # Termination is demanded of every call, so what the postconditions below
    # claim is TOTAL correctness: an implementation that never reaches the
    # return no longer satisfies them vacuously. The level is arg-dependent
    # rather than a bare constant because a callee must sit STRICTLY below its
    # caller, so no constant could ever admit a delegation to this same
    # operation against itself (it would need n > n). Announcing the size for a
    # body-present call is one level above the bodyless case, which leaves
    # exactly the room such a delegation needs. Both levels are finite, so
    # termination is demanded just as strongly on every input -- this orders the
    # obligation, it does not weaken it.
    Requires(MustTerminate(3 if body_present else 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(dict_pred(headers))
    # (1) Seekable stream: the size header is announced and equals the stream's
    #     measured length.
    Ensures(Implies(seekable,
                    size_header() in headers and
                    headers[size_header()] == stream_len))
    # (2) Non-stream body present: the size header is announced and equals the
    #     body's length.
    Ensures(Implies(not seekable and body_present,
                    size_header() in headers and
                    headers[size_header()] == body_len))
    # (3) Bodyless: a size header is announced (with zero size) for a payload-
    #     carrying method, and is NOT announced for either payload-less method.
    #     This is the discriminating clause: presence is conditioned on the
    #     method, so a bodyless retrieval/headers-only request carries no size
    #     header, while a bodyless request of any other method announces zero.
    Ensures(Implies(not seekable and not body_present,
                    (size_header() in headers) ==
                    (method != method_get() and method != method_head())))
    Ensures(Implies(not seekable and not body_present and
                    method != method_get() and method != method_head(),
                    headers[size_header()] == 0))
    # (4) Whole-map frame: the operation writes AT MOST the body-size header.
    #     Every OTHER header name keeps its membership, and every other header
    #     that was present keeps its exact value. Without this frame the spec
    #     would admit an implementation that smuggles an extra header into the
    #     request (e.g. a spurious probe header) — the operation under
    #     specification never touches any other entry of the header map.
    #     (Explicit triggers keep the quantifiers tractable for the verifier.)
    Ensures(Forall(int, lambda k: (Implies(k != size_header(),
                                           (k in headers) == Old(k in headers)),
                                   [[k in headers]])))
    Ensures(Forall(int, lambda k: (Implies(k != size_header() and
                                           k in headers and Old(k in headers),
                                           headers[k] == Old(headers[k])),
                                   [[headers[k]]])))
    # (5) The method token is never altered by this operation.
    Ensures(method == Old(method))
    # post-conditions-end
    # impl-start
    headers[size_header()] = 0
    if seekable:
        headers[size_header()] = stream_len
    elif body_present:
        headers[size_header()] = body_len
    # impl-end
