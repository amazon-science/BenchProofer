"""Twin-artifact model for sympy__sympy-16886.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A plaintext word is rendered into International Morse Code. Each symbol of
  the word is replaced by its standard Morse representation -- a finite
  sequence over the two Morse signals "dot" and "dash" -- and consecutive
  symbol representations are joined by a caller-chosen separator signal. The
  standard representations of the ten decimal digits are:

      0  dash  dash  dash  dash  dash
      1  dot   dash  dash  dash  dash
      2  dot   dot   dash  dash  dash
      3  dot   dot   dot   dash  dash
      4  dot   dot   dot   dot   dash
      5  dot   dot   dot   dot   dot
      6  dash  dot   dot   dot   dot
      7  dash  dash  dot   dot   dot
      8  dash  dash  dash  dot   dot
      9  dash  dash  dash  dash  dot

  In particular every digit's representation is exactly five signals long, and
  the representation of a digit d is d dots followed by (5 - d) dashes for d in
  0..5, and (d - 5) dashes followed by (10 - d) dots for d in 6..9. The
  twenty-six upper-case letters and the sixteen punctuation marks
  ! $ ' ( ) + , - . / : ; = ? @ _
  each carry their standard representation too (one to seven signals); the pure
  function `morse_of` spells the WHOLE table out, and a symbol the table does
  not represent contributes no signals at all.

  The encoded word is the per-symbol representation of its symbols with a
  single separator signal placed between adjacent symbols; the empty word
  encodes to no signals.

  The encoder only ACCEPTS a separator that is not itself an encodable
  plaintext symbol: it REJECTS (raises on) a separator that is a represented
  character -- an upper-case letter, a decimal digit, one of the represented
  punctuation marks -- or the space character. Only accepted separators
  (e.g. the default '|') are in the modelled domain; they are in particular
  distinct from the two Morse signals, so the join is unambiguous.

Modelled domain: ONE word, i.e. a possibly-empty `List[int]` of code points
that are all represented by the table. That is exactly the shape the per-word
encoding step is ever handed: the surrounding pass deletes every character the
table does not represent (`translate(msg, None, ''.join(chars - ok))`,
crypto.py:1570) and then splits on whitespace (`msg.split()`, crypto.py:1573),
and `str.split()` with no argument never yields a piece containing whitespace.
The word list may be empty and a word may be a single symbol, so no length
lower bound is assumed; every symbol of the word is represented, so the model
pins the table on the whole of its key set rather than on one class of symbol.

Signals are modelled as code points (`dot` = 46, `dash` = 45); a plaintext is a
`List[int]` of code points. The pure sequence theory `PSeq[int]` carries the
specification of the join. The per-symbol representation table is modelled
DEEPLY (`morse_of`), since it is the data the behaviour is about; there is no
axiomatized callee. `morse_of` is TOTAL on `int`: every code point, represented
or not, has a pinned per-symbol contribution, so no code point is left free.

The encoder must ANSWER: Nagini verifies partial correctness by default, so
without an explicit obligation a non-terminating implementation (an endless
loop, bare self-recursion) satisfies every `Ensures` vacuously while never
delivering the encoding. The real encoder is one bounded pass over the
plaintext that always completes; the obligation is carried as `MustTerminate`
in the preconditions and consumed by the encoding loop with the strictly
decreasing, bounded-below measure `i + 2`.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# axioms-end


# pure-start
@Pure
def dot() -> int:
    return 46


@Pure
def dash() -> int:
    return 45


@Pure
def no_signals() -> PSeq[int]:
    """The empty signal sequence -- the per-symbol contribution of a code point
    the representation table does not represent, which the encoder's input
    never contains (it is deleted before the per-word encoding step runs)."""
    return PSeq(dot()).drop(1)


@Pure
def represented(c: int) -> bool:
    """True iff the representation table gives the code point c a Morse
    representation: an upper-case letter ('A'..'Z' = 65..90), a decimal digit
    ('0'..'9' = 48..57), or one of the sixteen punctuation marks
    ! $ ' ( ) + , - . / : ; = ? @ _.
    These 52 code points are exactly the key set of the table the encoder looks
    each plaintext symbol up in (`char_morse`, crypto.py:1536)."""
    return ((65 <= c and c <= 90) or
            (48 <= c and c <= 57) or
            c == 33 or c == 36 or c == 39 or c == 40 or
            c == 41 or c == 43 or c == 44 or c == 45 or
            c == 46 or c == 47 or c == 58 or c == 59 or
            c == 61 or c == 63 or c == 64 or c == 95)


@Pure
def sep_accepted(c: int) -> bool:
    """True iff the code point c is a separator the real encoder ACCEPTS.

    The repository's encode_morse begins `assert sep not in mapping` with
    mapping == char_morse (crypto.py:1559-1560): it raises AssertionError
    whenever the separator is itself a represented plaintext symbol -- a
    decimal digit ('0'..'9' = 48..57), an upper-case letter
    ('A'..'Z' = 65..90), or a represented punctuation mark
    (! $ ' ( ) + , - . / : ; = ? @ _). The space
    character (32) is also excluded: `mapping[" "] = word_sep` mutates the
    module-level dict, so space is a mapping key from the second call on.
    Separators outside this set (e.g. the default '|' = 124) are accepted and
    the encoder returns normally."""
    return not (c == 32 or represented(c))


@Pure
def morse_of(c: int) -> PSeq[int]:
    """The standard Morse representation of one plaintext code point, as a
    sequence over {dot, dash}. TOTAL on `int`: a code point the table does not
    represent contributes `no_signals()`. Every digit's code is exactly five
    signals; letters run one to four signals and punctuation four to seven."""
    if c == 65:       # 'A'
        return PSeq(dot(), dash())
    if c == 66:       # 'B'
        return PSeq(dash(), dot(), dot(), dot())
    if c == 67:       # 'C'
        return PSeq(dash(), dot(), dash(), dot())
    if c == 68:       # 'D'
        return PSeq(dash(), dot(), dot())
    if c == 69:       # 'E'
        return PSeq(dot())
    if c == 70:       # 'F'
        return PSeq(dot(), dot(), dash(), dot())
    if c == 71:       # 'G'
        return PSeq(dash(), dash(), dot())
    if c == 72:       # 'H'
        return PSeq(dot(), dot(), dot(), dot())
    if c == 73:       # 'I'
        return PSeq(dot(), dot())
    if c == 74:       # 'J'
        return PSeq(dot(), dash(), dash(), dash())
    if c == 75:       # 'K'
        return PSeq(dash(), dot(), dash())
    if c == 76:       # 'L'
        return PSeq(dot(), dash(), dot(), dot())
    if c == 77:       # 'M'
        return PSeq(dash(), dash())
    if c == 78:       # 'N'
        return PSeq(dash(), dot())
    if c == 79:       # 'O'
        return PSeq(dash(), dash(), dash())
    if c == 80:       # 'P'
        return PSeq(dot(), dash(), dash(), dot())
    if c == 81:       # 'Q'
        return PSeq(dash(), dash(), dot(), dash())
    if c == 82:       # 'R'
        return PSeq(dot(), dash(), dot())
    if c == 83:       # 'S'
        return PSeq(dot(), dot(), dot())
    if c == 84:       # 'T'
        return PSeq(dash())
    if c == 85:       # 'U'
        return PSeq(dot(), dot(), dash())
    if c == 86:       # 'V'
        return PSeq(dot(), dot(), dot(), dash())
    if c == 87:       # 'W'
        return PSeq(dot(), dash(), dash())
    if c == 88:       # 'X'
        return PSeq(dash(), dot(), dot(), dash())
    if c == 89:       # 'Y'
        return PSeq(dash(), dot(), dash(), dash())
    if c == 90:       # 'Z'
        return PSeq(dash(), dash(), dot(), dot())
    if c == 48:       # '0'
        return PSeq(dash(), dash(), dash(), dash(), dash())
    if c == 49:       # '1'
        return PSeq(dot(), dash(), dash(), dash(), dash())
    if c == 50:       # '2'
        return PSeq(dot(), dot(), dash(), dash(), dash())
    if c == 51:       # '3'
        return PSeq(dot(), dot(), dot(), dash(), dash())
    if c == 52:       # '4'
        return PSeq(dot(), dot(), dot(), dot(), dash())
    if c == 53:       # '5'
        return PSeq(dot(), dot(), dot(), dot(), dot())
    if c == 54:       # '6'
        return PSeq(dash(), dot(), dot(), dot(), dot())
    if c == 55:       # '7'
        return PSeq(dash(), dash(), dot(), dot(), dot())
    if c == 56:       # '8'
        return PSeq(dash(), dash(), dash(), dot(), dot())
    if c == 57:       # '9'
        return PSeq(dash(), dash(), dash(), dash(), dot())
    if c == 46:       # '.'
        return PSeq(dot(), dash(), dot(), dash(), dot(), dash())
    if c == 44:       # ','
        return PSeq(dash(), dash(), dot(), dot(), dash(), dash())
    if c == 58:       # ':'
        return PSeq(dash(), dash(), dash(), dot(), dot(), dot())
    if c == 59:       # ';'
        return PSeq(dash(), dot(), dash(), dot(), dash(), dot())
    if c == 63:       # '?'
        return PSeq(dot(), dot(), dash(), dash(), dot(), dot())
    if c == 45:       # '-'
        return PSeq(dash(), dot(), dot(), dot(), dot(), dash())
    if c == 95:       # '_'
        return PSeq(dot(), dot(), dash(), dash(), dot(), dash())
    if c == 40:       # '('
        return PSeq(dash(), dot(), dash(), dash(), dot())
    if c == 41:       # ')'
        return PSeq(dash(), dot(), dash(), dash(), dot(), dash())
    if c == 39:       # "'"
        return PSeq(dot(), dash(), dash(), dash(), dash(), dot())
    if c == 61:       # '='
        return PSeq(dash(), dot(), dot(), dot(), dash())
    if c == 43:       # '+'
        return PSeq(dot(), dash(), dot(), dash(), dot())
    if c == 47:       # '/'
        return PSeq(dash(), dot(), dot(), dash(), dot())
    if c == 64:       # '@'
        return PSeq(dot(), dash(), dash(), dot(), dash(), dot())
    if c == 36:       # '$'
        return PSeq(dot(), dot(), dot(), dash(), dot(), dot(), dash())
    if c == 33:       # '!'
        return PSeq(dash(), dot(), dash(), dot(), dash(), dash())
    return no_signals()


@Pure
def encoded_seq(s: PSeq[int], sep: int) -> PSeq[int]:
    """The encoding of a whole word: the per-symbol representations joined by a
    single separator signal, and no signals for the empty word. Front-recursive
    so a single unfold is available to callers."""
    if len(s) == 0:
        return no_signals()
    if len(s) == 1:
        return morse_of(s[0])
    return morse_of(s[0]) + PSeq(sep) + encoded_seq(s.drop(1), sep)
# pure-end


def encode_morse(msg: List[int], sep: int) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(msg), 1 / 2))
    # The modelled domain is ONE word: a possibly-empty plaintext every symbol
    # of which the representation table represents. The per-word encoding step
    # is only ever handed such a word -- unrepresented characters are deleted
    # (`translate(msg, None, ''.join(chars - ok))`, crypto.py:1570) and the
    # remaining text is split on whitespace (`msg.split()`, crypto.py:1573),
    # which never leaves whitespace inside a piece.
    Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(msg),
                                            represented(msg[k])),
                                    [[msg[k]]])))
    # The separator is a single character (a Unicode code point) that the
    # real encoder ACCEPTS. The repository's encode_morse raises
    # AssertionError (`assert sep not in mapping`, crypto.py:1560) whenever
    # the separator is itself a represented plaintext symbol (a digit, a
    # letter, a represented punctuation mark) or -- from the second call on --
    # the space character; those rejected separators are OUTSIDE the modelled
    # domain (see sep_accepted). An accepted separator is in particular
    # distinct from the two Morse signals '.'/'-' (both are represented
    # punctuation), so the join is unambiguous and the discriminating symbol
    # lengths are observable.
    Requires(0 <= sep and sep <= 1114111)
    Requires(sep_accepted(sep))
    Requires(sep != dot() and sep != dash())
    # Total-correctness obligation: the encoder must ANSWER (return the
    # encoding). Without it a diverging impl satisfies the Ensures vacuously.
    # Measure 3: the impl may call morse_list (measure 2) but may NOT
    # re-invoke this routine itself.
    Requires(MustTerminate(3))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(msg), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The result is the per-symbol representation joined by the separator.
    Ensures(ToSeq(Result()) == encoded_seq(ToSeq(msg), sep))
    # post-conditions-end
    # impl-start
    n = len(msg)
    if n == 0:
        empty = []  # type: List[int]
        return empty
    result = morse_list(msg[n - 1])  # type: List[int]
    Assert(ToSeq(msg).drop(n - 1) == PSeq(msg[n - 1]))
    i = n - 1
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(msg), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(n == len(msg))
        Invariant(0 <= i and i <= n - 1)
        Invariant(sep != dot() and sep != dash())
        Invariant(len(ToSeq(msg).drop(i)) == n - i)
        Invariant(ToSeq(result) == encoded_seq(ToSeq(msg).drop(i), sep))
        # The loop consumes the caller's termination obligation with the
        # strictly decreasing, bounded-below measure i + 2 (headroom for the
        # morse_list call and the list constructions in the body), discharging
        # MustTerminate(3) from the precondition.
        Invariant(MustTerminate(i + 2))
        # invariants-end
        c = msg[i - 1]
        Assert(ToSeq(msg).drop(i - 1)[0] == c)
        Assert(ToSeq(msg).drop(i - 1).drop(1) == ToSeq(msg).drop(i))
        Assert(len(ToSeq(msg).drop(i - 1)) == n - i + 1)
        result = morse_list(c) + [sep] + result
        i = i - 1
    Assert(ToSeq(msg).drop(0) == ToSeq(msg))
    return result
    # impl-end


def morse_list(c: int) -> List[int]:
    # pre-conditions-start
    # No restriction on c: the table lookup is pinned on EVERY code point, so
    # the implementation has no unconstrained branch to hide behaviour in.
    # Total-correctness obligation (measure 2): a straight-line table lookup;
    # measure 2 leaves the headroom the list constructor in the body needs,
    # while any body holding MustTerminate(3) can call it without leaking the
    # obligation.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(Result())))
    Ensures(ToSeq(Result()) == morse_of(c))
    # post-conditions-end
    # impl-start
    if c == 65:
        return [dot(), dash()]
    if c == 66:
        return [dash(), dot(), dot(), dot()]
    if c == 67:
        return [dash(), dot(), dash(), dot()]
    if c == 68:
        return [dash(), dot(), dot()]
    if c == 69:
        return [dot()]
    if c == 70:
        return [dot(), dot(), dash(), dot()]
    if c == 71:
        return [dash(), dash(), dot()]
    if c == 72:
        return [dot(), dot(), dot(), dot()]
    if c == 73:
        return [dot(), dot()]
    if c == 74:
        return [dot(), dash(), dash(), dash()]
    if c == 75:
        return [dash(), dot(), dash()]
    if c == 76:
        return [dot(), dash(), dot(), dot()]
    if c == 77:
        return [dash(), dash()]
    if c == 78:
        return [dash(), dot()]
    if c == 79:
        return [dash(), dash(), dash()]
    if c == 80:
        return [dot(), dash(), dash(), dot()]
    if c == 81:
        return [dash(), dash(), dot(), dash()]
    if c == 82:
        return [dot(), dash(), dot()]
    if c == 83:
        return [dot(), dot(), dot()]
    if c == 84:
        return [dash()]
    if c == 85:
        return [dot(), dot(), dash()]
    if c == 86:
        return [dot(), dot(), dot(), dash()]
    if c == 87:
        return [dot(), dash(), dash()]
    if c == 88:
        return [dash(), dot(), dot(), dash()]
    if c == 89:
        return [dash(), dot(), dash(), dash()]
    if c == 90:
        return [dash(), dash(), dot(), dot()]
    if c == 48:
        return [dash(), dash(), dash(), dash(), dash()]
    if c == 49:
        return [dot(), dash(), dash(), dash(), dash()]
    if c == 50:
        return [dot(), dot(), dash(), dash(), dash()]
    if c == 51:
        return [dot(), dot(), dot(), dash(), dash()]
    if c == 52:
        return [dot(), dot(), dot(), dot(), dash()]
    if c == 53:
        return [dot(), dot(), dot(), dot(), dot()]
    if c == 54:
        return [dash(), dot(), dot(), dot(), dot()]
    if c == 55:
        return [dash(), dash(), dot(), dot(), dot()]
    if c == 56:
        return [dash(), dash(), dash(), dot(), dot()]
    if c == 57:
        return [dash(), dash(), dash(), dash(), dot()]
    if c == 46:
        return [dot(), dash(), dot(), dash(), dot(), dash()]
    if c == 44:
        return [dash(), dash(), dot(), dot(), dash(), dash()]
    if c == 58:
        return [dash(), dash(), dash(), dot(), dot(), dot()]
    if c == 59:
        return [dash(), dot(), dash(), dot(), dash(), dot()]
    if c == 63:
        return [dot(), dot(), dash(), dash(), dot(), dot()]
    if c == 45:
        return [dash(), dot(), dot(), dot(), dot(), dash()]
    if c == 95:
        return [dot(), dot(), dash(), dash(), dot(), dash()]
    if c == 40:
        return [dash(), dot(), dash(), dash(), dot()]
    if c == 41:
        return [dash(), dot(), dash(), dash(), dot(), dash()]
    if c == 39:
        return [dot(), dash(), dash(), dash(), dash(), dot()]
    if c == 61:
        return [dash(), dot(), dot(), dot(), dash()]
    if c == 43:
        return [dot(), dash(), dot(), dash(), dot()]
    if c == 47:
        return [dash(), dot(), dot(), dash(), dot()]
    if c == 64:
        return [dot(), dash(), dash(), dot(), dash(), dot()]
    if c == 36:
        return [dot(), dot(), dot(), dash(), dot(), dot(), dash()]
    if c == 33:
        return [dash(), dot(), dash(), dot(), dash(), dash()]
    unrepresented = []  # type: List[int]
    return unrepresented
    # impl-end
