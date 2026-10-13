#!/usr/bin/env python3
"""G-AX executable soundness check for sympy__sympy-16886.

This bundle consumes NO `@ContractOnly` axiom: the only operation that changes
is a data table (the Morse representation of each symbol), which model.py models
DEEPLY as the pure function `morse_of` (with `dot`/`dash`). G-AX therefore
validates that deep model, and the two domain predicates that fence it, against
the REAL repository code:

  (A-reference 1) `morse_of` (model.py pure region) == the real per-symbol Morse
      representation the patched module uses, on EVERY key of the real table.
      In the repository the table lives in `sympy.crypto.crypto.char_morse`
      (the character -> Morse-code dict, inverted from `morse_char`,
      crypto.py:1536); the encoder maps each input symbol `letter` to
      `mapping[letter]` (crypto.py:1577). We assert, character by character,
      that the deep model's signal sequence equals the real code string, with
      dot = '.' (46) and dash = '-' (45).

  (A-reference 2) `morse_of` is TOTAL, and its value on a code point the table
      does NOT represent -- no signals at all -- is the real behaviour: such
      characters are DELETED before the per-word encoding step
      (`translate(msg, None, ''.join(chars - ok))`, crypto.py:1570), so they
      contribute nothing to the output. Checked both as a set identity
      (`represented` == the real key set, over the whole Unicode code space)
      and observationally (encoding a message with unrepresented characters
      equals encoding the message with them removed).

  (A-reference 3) `represented` / `sep_accepted` == the real separator guard.
      The encoder begins `assert sep not in mapping` (crypto.py:1560) and then
      does `mapping[" "] = word_sep` (crypto.py:1562) on the MODULE-LEVEL dict,
      so the steady-state reject set is the table's key set plus ' '. Checked as
      a set identity and observationally (the AssertionError is raised).

  (A-reference 4) the model's domain restriction is REAL: every character that
      reaches the per-word lookup `mapping[letter]` (crypto.py:1577) is a
      represented, non-whitespace single character. Proved MECHANICALLY by
      passing a recording `dict` subclass as the `mapping=` argument and
      inspecting every key the real encoder ever looks up, over a corpus that
      includes unrepresented characters, runs of whitespace, and the empty
      message.

Run in-container against the PATCHED source (the gold table), where
`char_morse['1'] == '.----'`. The check fails against the pre-patch table
(`'1' -> '----'`), which is exactly the bug this instance fixes -- so a sound
deep model is one that matches the patched table.

Imports nothing beyond the repository module under test. Exit 0 iff every
observation matches the deep model.
"""
import sys

# --- model.py deep-model reference (kept in lock-step with the pure region) ---
# dot = 46 ('.'), dash = 45 ('-').
DOT = 46
DASH = 45

# model.py's `represented` deep model: the sixteen punctuation code points it
# enumerates, besides 'A'..'Z' (65..90) and '0'..'9' (48..57).
_PUNCT = (33, 36, 39, 40, 41, 43, 44, 45, 46, 47, 58, 59, 61, 63, 64, 95)

# model.py's `morse_of` deep model, branch for branch (52 represented code
# points; every other code point yields `no_signals()`, i.e. []).
_MORSE_OF = {
    ord('A'): [DOT, DASH],
    ord('B'): [DASH, DOT, DOT, DOT],
    ord('C'): [DASH, DOT, DASH, DOT],
    ord('D'): [DASH, DOT, DOT],
    ord('E'): [DOT],
    ord('F'): [DOT, DOT, DASH, DOT],
    ord('G'): [DASH, DASH, DOT],
    ord('H'): [DOT, DOT, DOT, DOT],
    ord('I'): [DOT, DOT],
    ord('J'): [DOT, DASH, DASH, DASH],
    ord('K'): [DASH, DOT, DASH],
    ord('L'): [DOT, DASH, DOT, DOT],
    ord('M'): [DASH, DASH],
    ord('N'): [DASH, DOT],
    ord('O'): [DASH, DASH, DASH],
    ord('P'): [DOT, DASH, DASH, DOT],
    ord('Q'): [DASH, DASH, DOT, DASH],
    ord('R'): [DOT, DASH, DOT],
    ord('S'): [DOT, DOT, DOT],
    ord('T'): [DASH],
    ord('U'): [DOT, DOT, DASH],
    ord('V'): [DOT, DOT, DOT, DASH],
    ord('W'): [DOT, DASH, DASH],
    ord('X'): [DASH, DOT, DOT, DASH],
    ord('Y'): [DASH, DOT, DASH, DASH],
    ord('Z'): [DASH, DASH, DOT, DOT],
    ord('0'): [DASH, DASH, DASH, DASH, DASH],
    ord('1'): [DOT, DASH, DASH, DASH, DASH],   # the fixed mapping: '.----'
    ord('2'): [DOT, DOT, DASH, DASH, DASH],
    ord('3'): [DOT, DOT, DOT, DASH, DASH],
    ord('4'): [DOT, DOT, DOT, DOT, DASH],
    ord('5'): [DOT, DOT, DOT, DOT, DOT],
    ord('6'): [DASH, DOT, DOT, DOT, DOT],
    ord('7'): [DASH, DASH, DOT, DOT, DOT],
    ord('8'): [DASH, DASH, DASH, DOT, DOT],
    ord('9'): [DASH, DASH, DASH, DASH, DOT],
    ord('.'): [DOT, DASH, DOT, DASH, DOT, DASH],
    ord(','): [DASH, DASH, DOT, DOT, DASH, DASH],
    ord(':'): [DASH, DASH, DASH, DOT, DOT, DOT],
    ord(';'): [DASH, DOT, DASH, DOT, DASH, DOT],
    ord('?'): [DOT, DOT, DASH, DASH, DOT, DOT],
    ord('-'): [DASH, DOT, DOT, DOT, DOT, DASH],
    ord('_'): [DOT, DOT, DASH, DASH, DOT, DASH],
    ord('('): [DASH, DOT, DASH, DASH, DOT],
    ord(')'): [DASH, DOT, DASH, DASH, DOT, DASH],
    ord("'"): [DOT, DASH, DASH, DASH, DASH, DOT],
    ord('='): [DASH, DOT, DOT, DOT, DASH],
    ord('+'): [DOT, DASH, DOT, DASH, DOT],
    ord('/'): [DASH, DOT, DOT, DASH, DOT],
    ord('@'): [DOT, DASH, DASH, DOT, DASH, DOT],
    ord('$'): [DOT, DOT, DOT, DASH, DOT, DOT, DASH],
    ord('!'): [DASH, DOT, DASH, DOT, DASH, DASH],
}


def represented(c):
    """model.py's `represented` deep model (kept in lock-step): True iff the
    representation table gives the code point c a Morse representation."""
    return ((65 <= c <= 90) or (48 <= c <= 57) or c in _PUNCT)


def morse_of(c):
    """model.py's `morse_of` deep model (kept in lock-step), TOTAL on int: a
    code point the table does not represent contributes no signals."""
    return _MORSE_OF.get(c, [])


def sep_accepted(c):
    """model.py's `sep_accepted` deep model (kept in lock-step): True iff the
    real encoder ACCEPTS code point c as a separator (does not raise
    AssertionError at `assert sep not in mapping`). Rejected: space (32,
    added to the module-level mapping by `mapping[" "] = word_sep`) and every
    represented character."""
    return not (c == 32 or represented(c))


# The table's key set, snapshotted BEFORE any encode_morse call: the real
# encoder MUTATES the module-level dict (`mapping[" "] = word_sep`,
# crypto.py:1562), and the model's predicates describe the table proper.
def _table_snapshot():
    from sympy.crypto.crypto import char_morse
    return dict(char_morse)


# ---------------------------------------------------------------------------
# (A-reference 1) morse_of == the real char_morse, on every key.
# ---------------------------------------------------------------------------
def check_table(table):
    assert len(table) == 52, (
        "real char_morse has %d entries, the deep model spells out 52"
        % len(table))
    for ch, code in sorted(table.items()):
        assert len(ch) == 1, (
            "char_morse has a multi-character key %r, so the code-point model "
            "of the lookup would be ill-typed" % (ch,))
        observed = [ord(sig) for sig in code]      # real repo table
        expected = morse_of(ord(ch))               # deep model `morse_of`
        assert observed == expected, (
            "morse_of deep model unsound on %r (cp %d): real char_morse gives "
            "%r, deep model gives %r" % (ch, ord(ch), observed, expected))
        assert set(observed) <= {DOT, DASH}, (
            "real code for %r is not over {dot, dash}: %r" % (ch, code))


# ---------------------------------------------------------------------------
# (A-reference 2) morse_of is TOTAL and unrepresented code points contribute
# nothing; `represented` == the real key set over the whole code space.
# ---------------------------------------------------------------------------
def check_totality(table):
    real_keys = {ord(k) for k in table}
    model_keys = {cp for cp in range(0x110000) if represented(cp)}
    assert model_keys == real_keys, (
        "represented deep model unsound: only in model %r, only in real table "
        "%r" % (sorted(model_keys - real_keys)[:8],
                sorted(real_keys - model_keys)[:8]))
    assert set(_MORSE_OF) == real_keys, (
        "morse_of's pinned key set != the real table's key set: %r"
        % sorted(set(_MORSE_OF) ^ real_keys)[:8])
    # Totality: every other code point contributes no signals at all. Sweep the
    # whole space rather than a sample, so no unrepresented code point is
    # silently given a representation.
    for cp in range(0x110000):
        if cp not in real_keys:
            assert morse_of(cp) == [], (
                "morse_of gives the unrepresented code point %d a "
                "representation %r" % (cp, morse_of(cp)))


def check_deletion():
    """The real reason unrepresented characters contribute no signals: they are
    DELETED (crypto.py:1570) before the per-word encoding step, so the output
    is identical to the output for the message with them removed."""
    from sympy.crypto.crypto import encode_morse
    for msg in ('AB#C', 'a1b2', '12%345', 'HELLO, WORLD!', '~`^&*',
                '1\t2\n3', '   ', '', 'AB#', '#AB', 'A#B C%D'):
        # Only UNREPRESENTED, non-whitespace characters are deleted: whitespace
        # is never in the delete set (`chars` is built from `''.join(msg.split())`,
        # crypto.py:1568) and goes on to delimit words.
        kept = ''.join(ch for ch in msg
                       if ch.isspace() or represented(ord(ch)))
        assert encode_morse(msg) == encode_morse(kept), (
            "unrepresented characters are not deleted: encode_morse(%r) = %r "
            "but encode_morse(%r) = %r"
            % (msg, encode_morse(msg), kept, encode_morse(kept)))


# ---------------------------------------------------------------------------
# (A-reference 3) sep_accepted == the real separator guard.
# ---------------------------------------------------------------------------
def check_sep_accepted(table):
    """The real encoder asserts `sep not in mapping` with mapping ==
    char_morse (crypto.py:1559-1560), then adds `mapping[" "] = word_sep`
    (crypto.py:1562); because char_morse is module-level, ' ' is a mapping key
    from the second call on. So the steady-state reject set is char_morse's
    keys plus ' '. Compare the deep model against that set on every ASCII code
    point (all mapping keys are single ASCII characters)."""
    from sympy.crypto.crypto import encode_morse
    reject = set(table.keys()) | {" "}
    assert all(len(k) == 1 for k in reject), (
        "char_morse has a multi-character key: %r"
        % [k for k in reject if len(k) != 1])
    for cp in range(128):
        expected = chr(cp) not in reject
        assert sep_accepted(cp) == expected, (
            "sep_accepted deep model unsound on %r (cp %d): model %r, "
            "real guard accepts=%r" % (chr(cp), cp, sep_accepted(cp),
                                       expected))
    # The accepted default '|' returns normally -- and this successful call is
    # what installs " " as a mapping key (crypto.py:1562), putting the
    # module-level table in the steady state the reject set above describes.
    # (' ' is the one code point whose rejection is not immediate: on the very
    # FIRST call of a fresh process the space is not yet a key, so the model's
    # exclusion of 32 is a NARROWING of the accepted set, never a claim the
    # real code contradicts.)
    assert encode_morse('1', sep='|') == '.----'
    # the rejection is OBSERVABLE: a represented separator raises
    # AssertionError (the G-PANEL-2 witness encode_morse('1', sep='0')).
    for bad in ('0', 'A', '5', '.', '-', '!', '$', ' '):
        try:
            encode_morse('1', sep=bad)
        except AssertionError:
            pass
        else:
            raise AssertionError(
                "real encode_morse accepted rejected separator %r" % bad)


# ---------------------------------------------------------------------------
# (A-reference 4) the modelled domain is REAL: mechanically record every
# character the real encoder looks up in the table.
# ---------------------------------------------------------------------------
class Recorder(dict):
    """A `mapping=` argument that records every key the real encoder looks up.

    The lookup under observation is `morseletter = mapping[letter]`
    (crypto.py:1577), the per-symbol step model.py's `morse_list` stands for.
    `__setitem__` is left alone so `mapping[" "] = word_sep` (crypto.py:1562)
    behaves exactly as on the real dict."""

    def __init__(self, *a, **kw):
        dict.__init__(self, *a, **kw)
        self.looked_up = []

    def __getitem__(self, key):
        self.looked_up.append(key)
        return dict.__getitem__(self, key)


def check_domain(table):
    """Every character reaching the per-word lookup is a represented,
    non-whitespace single character -- the model's precondition
    `Forall(k, represented(msg[k]))`, established by the real code's own
    guards: deletion of unmapped characters (crypto.py:1570) and the
    whitespace split (crypto.py:1573).

    The corpus deliberately includes unrepresented characters, lower case,
    runs of several whitespace kinds, leading/trailing whitespace, punctuation,
    a single-character word and the empty message."""
    from sympy.crypto.crypto import encode_morse
    corpus = ('ABC', 'SMS', '12345', '67890', '', 'A', '1',
              'ATTACK RIGHT FLANK', 'HELLO, WORLD!', '!@#$%^&*()_+',
              'ab#c 12%3', '  spaced \t out \n ', 'x', '~', '   ',
              'A' * 40, "IT'S 3:15 P.M. -- GO/NO-GO?")
    for msg in corpus:
        rec = Recorder(table)
        encode_morse(msg, mapping=rec)
        for letter in rec.looked_up:
            assert isinstance(letter, str) and len(letter) == 1, (
                "the per-word lookup was handed a non-character key %r on %r"
                % (letter, msg))
            cp = ord(letter)
            assert represented(cp), (
                "the per-word lookup was handed the UNREPRESENTED character "
                "%r (cp %d) on %r -- the model's precondition would be "
                "unsound" % (letter, cp, msg))
            assert not letter.isspace(), (
                "the per-word lookup was handed whitespace %r on %r" %
                (letter, msg))
        # and the recorded lookups are exactly the surviving characters, in
        # order: the model's per-symbol decomposition of the word.
        survivors = [ch for ch in msg if represented(ord(ch))]
        assert rec.looked_up == survivors, (
            "the encoder's per-symbol lookups %r are not the surviving "
            "characters %r of %r" % (rec.looked_up, survivors, msg))


# ---------------------------------------------------------------------------
def check_encode(msg, expected):
    """Cross-check the real encoder on a full message (the F2P witnesses)."""
    from sympy.crypto.crypto import encode_morse
    observed = encode_morse(msg)
    assert observed == expected, (
        "real encode_morse(%r) = %r, expected %r" % (msg, observed, expected))


def main():
    table = _table_snapshot()

    # (A-reference 1) deep model morse_of == real char_morse, every key.
    check_table(table)

    # (A-reference 2) morse_of is total; unrepresented code points contribute
    # no signals, which is what the deletion step really does.
    check_totality(table)

    # (A-reference 3) deep model sep_accepted == the real separator guard
    # (`assert sep not in mapping`), including the observable AssertionError
    # on rejected separators (the G-PANEL-2 witnesses).
    check_sep_accepted(table)

    # (A-reference 2, observational) and (A-reference 4): the deletion step and
    # the recorded per-symbol lookups. Both call the real encoder, which
    # mutates the module-level table, so they run after the set identities.
    check_deletion()
    check_domain(table)

    # Sanity: every digit's representation is exactly five signals (the
    # property the bug violated: the pre-patch '1' -> '----' was only four).
    for ch in '0123456789':
        sig = morse_of(ord(ch))
        assert len(sig) == 5, "digit %r is not five signals: %r" % (ch, sig)

    # The discriminating digit: '1' must be dot + four dashes ('.----'),
    # NOT four dashes ('----').
    assert morse_of(ord('1')) == [DOT, DASH, DASH, DASH, DASH]
    assert table['1'] == '.----', (
        "patched char_morse['1'] is %r, not '.----'" % (table['1'],))

    # The full F2P witnesses, exercised on the real encoder: the two digit
    # strings the patch fixes, plus a letter word, a punctuation word and the
    # empty message -- the other assertions the F2P test makes, which the
    # widened model also has to be right about.
    check_encode('12345', '.----|..---|...--|....-|.....')
    check_encode('67890', '-....|--...|---..|----.|-----')
    check_encode('ABC', '.-|-...|-.-.')
    check_encode('SMS', '...|--|...')
    check_encode('!@#$%^&*()_+',
                 '-.-.--|.--.-.|...-..-|-.--.|-.--.-|..--.-|.-.-.')
    check_encode('', '')

    print("G-AX OK: morse_of deep model (== real char_morse) sound on all 52 "
          "table keys and total (no signals) on every other code point; "
          "represented/sep_accepted == the real key set and separator guard; "
          "every character reaching the per-word lookup is represented and "
          "non-whitespace (recorded mapping, 17 messages); F2P witnesses "
          "'12345', '67890', 'ABC', 'SMS', '!@#$%^&*()_+' and '' match.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
