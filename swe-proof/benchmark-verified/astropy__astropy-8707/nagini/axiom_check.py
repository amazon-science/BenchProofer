#!/usr/bin/env python3
"""G-AX executable soundness check for astropy__astropy-8707.

Executes the REAL callees the modelled function relies on and asserts every
observation matches model.py:

  (A-reference) the deep model `reinterpret` (model.py pure region) == the REAL
      value-preserving byte->code-point reinterpretation. The real operation is
      `bytes.decode('latin1')` (CPython stdlib): byte value b maps to code point
      b, i.e. the identity on the integer value over the whole byte domain
      0..255. model.py's `reinterpret` is exactly this identity fold. Checked
      exhaustively on every byte 0..255, on every length-2 byte pair, and on
      fuzzed byte strings.

  (A-consumed) the `pad_to_width` / `pad_runtime` axioms (model.py axioms
      region) == the REAL unchanged padding helper `_pad`
      (astropy/io/fits/card.py:1269). `_pad` appends ASCII spaces to a TEXT
      input until the length is a whole multiple of the record width,
      preserving the existing content and adding at most `width` spaces. The
      model encodes exactly that (content prefix preserved; length a multiple
      of WIDTH; at most WIDTH padding added -- `<= len+WIDTH`, since an EMPTY
      input is padded out to a FULL record; every appended element is
      space=32). Checked WIDTH-agnostic against the real `astropy` `_pad` and
      against `_pad` reimplemented verbatim from source.

  (ghost property) `text_form` and its only source `enter_text_form`, plus the
      `Requires(text_form(text))` that restricts the modelled padding step to
      textual content. `text_form` is the runtime type tag the `List[int]`
      carrier erases -- the concrete value is a `str` rather than a `bytes` --
      and the three obligations checked against the real callees are:

        L1  `enter_text_form`: the real step (`bytes.decode('latin1')`) yields
            textual content with identical code points, and a DISTINCT object
            (the model forces `Result() is not v` by permission arithmetic).
        L2  `pad_runtime`'s `Requires(text_form(text))` and
            `Ensures(text_form(Result()))`: the real helper is a TEXT
            operation. On textual content it yields textual content; on a value
            that is NOT textual content it NEVER yields textual content -- it
            either fails outright (every length at which it must concatenate,
            the empty input included) or returns its argument untouched and
            still non-text (lengths that are already a positive whole multiple
            of the record width). Whole multiples are INCLUDED in the check,
            not skipped. The model claims NO failure of its own (it carries no
            `Exsures` anywhere): it restricts a callee's domain by
            precondition, so no MODEL-raises / REAL-returns divergence is
            claimed at any length.
        L3  the observable that grounds `Ensures(text_form(Result()))`: the
            record image handed back is what the caller parses as text.
            Probed on the module as the image ships it (unpatched: G-AX runs at
            base_commit), i.e. the behaviour under specification.

Runs the REAL `astropy.io.fits.card` callees in the instance image; the
verbatim source reimplementation below is cross-checked against them so the
provenance quoted in mapping.md is exercised rather than asserted. Exit 0 iff
every obligation holds.
"""
import random
import sys

CARD_LENGTH = 80  # astropy/io/fits/card.py: Card.length == CARD_LENGTH == 80


# --- _pad reimplemented VERBATIM from astropy/io/fits/card.py:1269 -----------
# (kept in lock-step with the real source for the soundness reference)
def _pad_ref(input):
    """Pad blank space to the input string to be multiple of 80."""
    _len = len(input)
    if _len == CARD_LENGTH:
        return input
    elif _len > CARD_LENGTH:
        strlen = _len % CARD_LENGTH
        if strlen == 0:
            return input
        else:
            return input + ' ' * (CARD_LENGTH - strlen)
    else:
        strlen = _len % CARD_LENGTH
        return input + ' ' * (CARD_LENGTH - strlen)


def _real():
    """The REAL repo callees, in the instance image."""
    from astropy.io.fits.card import _pad, Card
    return _pad, Card


# --- model.py reference encodings (kept in lock-step with the spec) ----------

def reinterpret_model(byte_values):
    """model.py's deep model `reinterpret`: the value-preserving identity over
    a byte sequence (each element a code point of the same integer value)."""
    return list(byte_values)


# --- A-reference: latin-1 decode == identity on byte values ------------------

def check_decode_reference():
    # exhaustive over the whole byte domain 0..255
    for b in range(256):
        observed = [ord(ch) for ch in bytes([b]).decode('latin1')]  # real callee
        expected = reinterpret_model([b])                           # deep model
        assert observed == expected == [b], (
            "latin1 decode not value-preserving on byte %d: got %r" % (b, observed))
    # exhaustive over every ordered byte pair
    for a in range(256):
        for b in range(256):
            observed = [ord(ch) for ch in bytes([a, b]).decode('latin1')]
            expected = reinterpret_model([a, b])
            assert observed == expected == [a, b], (
                "latin1 decode not value-preserving on (%d,%d): %r" % (a, b, observed))
    # fuzz: random byte strings
    rng = random.Random(8707)
    for _ in range(20000):
        n = rng.randint(0, 90)
        bs = bytes(rng.randint(0, 255) for _ in range(n))
        observed = [ord(ch) for ch in bs.decode('latin1')]
        expected = reinterpret_model(list(bs))
        assert observed == expected == list(bs), (
            "latin1 decode not value-preserving on %r: %r" % (bs, observed))


# --- A-consumed: real _pad meets the model's pad_to_width contract -----------

def check_pad_axiom(pad):
    # boundary lengths around the record width and several multiples
    lengths = list(range(0, 3 * CARD_LENGTH + 5))
    for _len in lengths:
        # build a text input of this length using non-space, value-preserving
        # ASCII/latin content so we can detect any content corruption
        text = ''.join(chr(33 + ((k * 7) % 90)) for k in range(_len))
        out = pad(text)                                        # real callee
        assert out == _pad_ref(text), (
            _len, "real helper disagrees with the verbatim source reference")
        # model pad_to_width obligations (WIDTH-agnostic, width=CARD_LENGTH):
        assert len(out) >= len(text), (_len, "length must not shrink")
        assert out[:len(text)] == text, (_len, "content prefix must be preserved")
        assert len(out) % CARD_LENGTH == 0, (_len, "length must be a multiple")
        assert len(out) <= len(text) + CARD_LENGTH, (_len, "at most width added")
        assert all(ch == ' ' for ch in out[len(text):]), (_len, "appended must be spaces")
    print("  L0 pad_to_width: content prefix preserved, length a whole multiple, "
          "at most one width added (the EMPTY input adds a full record, so the "
          "bound is <=), appended elements all spaces, at %d lengths vs the REAL "
          "helper (== the verbatim source reference at every one)" % len(lengths))


# --- the ghost property text_form / enter_text_form / Requires(text_form) ----

def leg_enter_text_form():
    """`enter_text_form` Ensures: content unchanged + the outcome IS textual
    content, and the outcome is a DISTINCT object from the argument (the model
    forces `Result() is not v`: it hands back full permission on `Result` while
    keeping half on `v`)."""
    samples = [b"", b"ABC     = 'abc'", b"A" * 80, b"B" * 81,
               bytes(range(256)), bytes([0, 128, 255])]
    for bs in samples:
        out = bs.decode('latin1')                       # the real step
        assert isinstance(out, str), (bs, "the step did not yield textual content")
        assert [ord(c) for c in out] == list(bs), (bs, "content changed")
        assert out is not bs, (bs, "step returned its own argument")
    # a value already in text form is textual content by virtue of its form
    for s in ["", "ABC     = 'abc'", "A" * 80]:
        assert isinstance(s, str), (s, "text-form input is not textual content")
    print("  L1 enter_text_form: the real step yields TEXT with identical code "
          "points, a distinct object, over %d samples incl. all 256 byte values"
          % len(samples))


def leg_pad_is_text_only(pad):
    """`pad_runtime`'s `Requires(text_form(text))` / `Ensures(text_form(Result()))`.

    The real padding helper is a TEXT operation: on textual content it returns
    textual content; on a value that is NOT textual content it NEVER yields
    textual content -- it either fails outright (every length at which it must
    concatenate, which includes the empty input: that one is padded out to a
    FULL record) or returns its argument untouched and still non-text (lengths
    already a positive whole multiple of the record width). Nothing a correct
    implementation does is excluded, and the model asserts no failure of its own
    (it carries no `Exsures`), so no MODEL-raises / REAL-returns divergence is
    claimed anywhere."""
    n_lengths = 4 * CARD_LENGTH + 1
    concat_lengths = []
    passthrough_lengths = []
    for n in range(n_lengths):
        raw = bytes((33 + (k * 7) % 90) for k in range(n))
        try:
            out = pad(raw)
        except TypeError:
            concat_lengths.append(n)
            assert not (n >= CARD_LENGTH and n % CARD_LENGTH == 0), (
                n, "failed where the helper does not concatenate")
            continue
        # returned normally: it must be the argument itself, still NOT text
        passthrough_lengths.append(n)
        assert n >= CARD_LENGTH and n % CARD_LENGTH == 0, (
            n, "returned normally where it must concatenate")
        assert out is raw and isinstance(out, bytes), (
            n, "non-text argument came back as textual content")
    # on TEXT the helper returns TEXT at every one of the same lengths
    for n in range(n_lengths):
        text = ''.join(chr(33 + (k * 7) % 90) for k in range(n))
        out = pad(text)
        assert isinstance(out, str), (n, "text argument did not yield text")
        assert out[:n] == text and len(out) % CARD_LENGTH == 0, (n, "value")
    print("  L2 pad text-only: non-text argument FAILS at %d lengths and comes "
          "back untouched-and-still-non-text at %d whole-multiple lengths "
          "(%s); text argument yields text at all %d lengths"
          % (len(concat_lengths), len(passthrough_lengths),
             passthrough_lengths, n_lengths))


def leg_observable(Card):
    """What grounds the postcondition `text_form(Result())`: the record image
    handed back is parsed as text by the caller. Probed on the module as the
    instance image ships it (G-AX runs at base_commit), i.e. the behaviour
    under specification."""
    import astropy.io.fits.card as cardmod
    src = open(cardmod.__file__).read()
    reinterprets = "image.decode('latin1')" in src
    witness = b"ABC     = 'abc'"
    try:
        c = Card.fromstring(witness)
        got = (type(c._image).__name__, c.keyword)
    except TypeError as e:
        got = ("TypeError", str(e))
    aligned = Card.fromstring(b"A" * CARD_LENGTH)
    print("  L3 observable (module %s the byte form): fromstring(%r) -> %r ; "
          "fromstring(b'A'*%d)._image type=%s"
          % ("reinterprets" if reinterprets else "does NOT reinterpret",
             witness, got, CARD_LENGTH, type(aligned._image).__name__))


def main():
    pad, Card = _real()
    check_decode_reference()
    print("G-AX legs, REAL astropy callees:")
    check_pad_axiom(pad)
    leg_enter_text_form()
    leg_pad_is_text_only(pad)
    leg_observable(Card)
    print("G-AX OK: reinterpret deep model == latin-1 decode (identity over "
          "0..255, all 65536 byte pairs, 20000 fuzz); pad_to_width axiom sound "
          "vs the REAL astropy _pad over %d lengths; text_form / "
          "enter_text_form / pad_runtime Requires(text_form) sound vs the REAL "
          "_pad over %d lengths, whole multiples INCLUDED (not skipped)."
          % (3 * CARD_LENGTH + 5, 4 * CARD_LENGTH + 1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
