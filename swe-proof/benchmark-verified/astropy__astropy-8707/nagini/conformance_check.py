#!/usr/bin/env python3
"""G-CONF differential conformance check for astropy__astropy-8707 (nagini).

SHADOW — the `# impl-start` / `# impl-end` region of model.py's
`build_record_image(raw, from_bytes)`, transcribed below with only the contract
calls removed (`Requires`, `Ensures`, `Invariant`, `Assert`, and the
`# invariants-start`/`-end` markers). Nothing is restructured or renamed: the
backward `while i > 0` loop that prepends `raw[i - 1]` onto `image` is the
value-preserving code-point correspondence as the model spells it out, then
`text = enter_text_form(image)` and `res = pad_runtime(text)` are left as the
two calls they are. Note the region does not branch on `from_bytes` at all — the
correspondence is applied unconditionally, which is precisely the model's claim
that both input forms are accepted; the parameter is kept in the signature (and
driven with both values) rather than dropped, and it is what the type bridge
below needs to name the concrete value the carrier stands for.

  * The `@Pure` helpers of the `pure` region (`reinterpret`, `all_bytes`) are
    copied over with their contracts stripped. `all_bytes` (a `Forall` over the
    element domain) is realized as a bounded loop and used ONLY to assert that
    every generated input satisfies the model's `Requires`. `reinterpret` — the
    A-reference deep model of the reinterpretation (mapping.md §3.1) — is copied
    and run over a sampled subset as a model-internal consistency check of the
    stripped `Assert(ToSeq(image) == reinterpret(ToSeq(raw)))`; it is NOT the
    oracle and never enters the differential comparison (a model-vs-model check
    would certify nothing).
  * `PSeq` / `ToSeq` are Nagini spec carriers, realized here by the immutable
    tuple shim used by the other nagini bundles in this corpus.

  * Both `@ContractOnly` callees have no body to copy, so each shim CALLS THE
    REAL REPO OPERATION it axiomatizes; the axioms are therefore exercised, not
    assumed:
      - `enter_text_form(v)` ↔ the guarded reinterpretation the gold hunk adds,
        `if isinstance(image, bytes): image = image.decode('latin1')`
        (`astropy/io/fits/card.py:557-562`, patched; mapping.md §1). The real
        step is called on the concrete value the carrier stands for.
      - `pad_runtime(text)` ↔ `astropy.io.fits.card._pad`
        (`astropy/io/fits/card.py:1269`, unchanged by the patch; mapping.md
        §3.2), so the shadow's padding is the real 80-column helper. Its
        `Requires(text_form(text))` — the modelled padding step is defined on
        textual content — is separately cross-checked against that real callee
        (see `check_text_only_axiom`): a value that is not textual content never
        comes back as textual content, at any length.

ORACLE — the REAL patched repo function, CALLED, not transliterated:
`Card.fromstring(image)` at `astropy/io/fits/card.py:548` (mapping.md §1); the
observable is the `card._image` it stores, which is exactly what the gold hunk
changes and what the F2P test (`test_card_from_bytes`) parses `keyword`/`value`
back out of. No transliteration was needed: the function is a classmethod over
a bare `str`/`bytes` argument with no Table/session/file context, so it is
driven directly in-container. The gate applies patch.diff to /testbed before
this script runs and sets PYTHONPATH=/testbed, so the import is the patched
module (asserted at start-up).

TYPE BRIDGE (mapping.md §2, inverted) — the model carries a `str`/`bytes` as
`List[int]` (element = byte value / code point) plus a `from_bytes` flag ↔
`isinstance(image, bytes)`. Inverting: a generated `List[int]` with every
element in 0..255 becomes `bytes(raw)` when `from_bytes` is true and
`''.join(chr(c) for c in raw)` when it is false; the oracle's `str` result comes
back as `[ord(ch) for ch in image]` for comparison against the shadow's
`List[int]`. The same bridge is applied at each `@ContractOnly` callee boundary
(`List[int]` → `bytes`/`str` → real operation → `List[int]`). The model's
`WIDTH = 4` is a spec-only constant (mapping.md §2: the refinement is
width-agnostic); the impl region never mentions it, and because the shadow calls
the REAL `_pad`, the executable diff runs at the real width 80 — the width
abstraction never enters the comparison.

INPUT DOMAIN — the model's `Requires` is `all_bytes(ToSeq(raw))`, i.e. every
element in 0..255, for EITHER value of `from_bytes` (a text-form input
additionally carries `text_form(raw)`, which the carrier cannot express and
which the concrete `str` has by virtue of its type); both flag values must
return normally (the "accept any form" guarantee is the absence of an Exsures).
The space is infinite (unbounded length), so: boundary cases first — the empty
input (the `while i > 0` false branch, and the `_pad`-adds-a-whole-record
corner), singletons, every single byte value 0..255 in both forms (the element
domain exhaustively), the exact F2P image `b"ABC     = 'abc'"` in both forms,
`bytes(range(256))`, the high-bit 0x80..0xFF range that only latin-1
round-trips, and lengths straddling both the real width 80 (79/80/81/159/160/
161) and the modeled WIDTH 4 (3/4/5/8) — then seeded fuzz to fill the count.
Every generated input is asserted `Requires`-satisfying before use, and the
byte and text forms of the same value-equal input are both driven, so the
branch the gold patch added (`isinstance(image, bytes)`) is taken on roughly
half of all inputs; the pre-patch function raises `TypeError` on every one of
them whose length is not a positive whole multiple of the width.

>= 1e5 inputs: 100000 fuzz draws plus the boundary block. Pinned seed 8707
(recorded in mapping.md § G-CONF).

Exit 0 iff zero disagreements; on a disagreement the input and both outputs are
printed and the exit status is 1. stdlib only (hypothesis not required).
"""
import json
import random
import sys
from typing import List  # only so the copied `# type: List[int]` comment resolves

SEED = 8707
N_FUZZ = 100_000
CARD_LENGTH = 80  # the REAL record width (astropy/io/fits/card.py); see docstring


# --- PSeq shim: immutable sequence, the operations the copied code uses -------

class PSeq:
    __slots__ = ("_t",)

    def __init__(self, *items):
        self._t = tuple(items)

    @classmethod
    def _wrap(cls, t):
        s = cls()
        s._t = tuple(t)
        return s

    def take(self, n):
        return PSeq._wrap(self._t[:n])

    def drop(self, n):
        return PSeq._wrap(self._t[n:])

    def __add__(self, other):
        return PSeq._wrap(self._t + other._t)

    def __len__(self):
        return len(self._t)

    def __getitem__(self, i):
        return self._t[i]

    def __eq__(self, other):
        return isinstance(other, PSeq) and self._t == other._t

    def __hash__(self):
        return hash(self._t)


def ToSeq(lst):
    return PSeq._wrap(lst)


# --- model.py `pure` region, verbatim, contracts stripped --------------------

def reinterpret(x):
    """model.py: the value-preserving byte -> code-point correspondence."""
    if len(x) == 0:
        return PSeq(0).take(0)
    return PSeq(x[0]) + reinterpret(x.drop(1))


def all_bytes(x):
    # model.py states this with a Forall quantifier; realized here as a bounded
    # loop (used only to check that generated inputs satisfy the Requires).
    return all(0 <= x[k] and x[k] <= 255 for k in range(len(x)))


# --- the @ContractOnly callees: CALL THE REAL REPO OPERATIONS ----------------

def enter_text_form(v, from_bytes):
    """model.py's `@ContractOnly` `enter_text_form`, realized by the REAL repo
    step it axiomatizes: the guarded reinterpretation the gold hunk adds at
    `astropy/io/fits/card.py:557-562` (patched).

    Type bridge (docstring, inverted): the carrier `List[int]` plus the form
    flag names the concrete value — `bytes` or `str` — and the real step is run
    on that, then the result comes back to the carrier. On a value already in
    text form the real step is the identity, exactly as the model's
    `Ensures(ToSeq(Result()) == ToSeq(v))` allows for either form.
    """
    concrete = bytes(v) if from_bytes else "".join(chr(c) for c in v)
    if isinstance(concrete, bytes):                # the guarded real step
        concrete = concrete.decode("latin1")
    return [ord(ch) for ch in concrete]


def pad_runtime(text):
    """model.py's `@ContractOnly` `pad_runtime`, realized by the REAL unchanged
    repo callee it axiomatizes: `astropy.io.fits.card._pad` (card.py:1269).

    Its `Requires(text_form(text))` is the model's statement that the padding
    step is defined on textual content; the bridge is `List[int]` -> `str` ->
    real `_pad` -> `List[int]`, so the argument handed to the real callee is
    textual content, as the precondition demands.
    """
    from astropy.io.fits.card import _pad          # REAL unchanged repo callee
    s = "".join(chr(c) for c in text)              # carrier -> real str
    return [ord(ch) for ch in _pad(s)]             # real str -> carrier


# --- SHADOW: the impl region of model.py, contract calls stripped ------------

def build_record_image(raw, from_bytes):
    image = []  # type: List[int]
    i = len(raw)
    while i > 0:
        c = raw[i - 1]
        # the code-point correspondence: byte value b -> code point b.
        image = [c] + image
        i = i - 1
    # the outcome is taken over into text form, and the padding step, defined
    # on textual content, then applies for either input form.
    text = enter_text_form(image, from_bytes)
    res = pad_runtime(text)
    return res


# --- ORACLE: the real patched Card.fromstring -------------------------------

def oracle_image(raw, from_bytes):
    """The patched `Card.fromstring` (card.py:548), called; the observable is
    the `card._image` it stores."""
    from astropy.io.fits.card import Card          # patched module (/testbed)
    concrete = bytes(raw) if from_bytes else "".join(chr(c) for c in raw)
    card = Card.fromstring(concrete)
    return [ord(ch) for ch in card._image]


# --- input generation -------------------------------------------------------

def boundary_raws():
    """Boundary code-point lists; each is driven in BOTH input forms."""
    out = []
    out.append([])                                     # empty: loop not taken
    out.append([0])
    out.append([32])
    out.append([255])
    out.append(list(b"ABC     = 'abc'"))               # the exact F2P image
    out.append(list(range(256)))                       # whole element domain
    out.append([0x80, 0x81, 0xfe, 0xff])               # high-bit: latin-1 only
    out.append([0xc3, 0xa9])                           # UTF-8 'e-acute' octets
    out.append(list(range(128, 256)))
    for n in (1, 2, 3, 4, 5, 8, 9, 79, 80, 81, 159, 160, 161, 240):
        out.append([ord("X")] * n)                     # real-width + WIDTH=4 edges
        out.append([33 + ((k * 7) % 90) for k in range(n)])
    for b in range(256):                               # every single byte value
        out.append([b])
    return out


def fuzz_raw(rng):
    """A Requires-satisfying code-point list (every element in 0..255).

    Lengths are drawn short-biased with a long tail so the boundary region
    around both widths stays well covered at 1e5 draws.
    """
    r = rng.random()
    if r < 0.55:
        n = rng.randint(0, 24)
    elif r < 0.85:
        n = rng.randint(70, 90)                        # straddles width 80
    elif r < 0.97:
        n = rng.randint(150, 170)                      # straddles width 160
    else:
        n = rng.randint(0, 200)
    if rng.random() < 0.5:
        return [rng.randint(32, 126) for _ in range(n)]     # ASCII text-ish
    return [rng.randint(0, 255) for _ in range(n)]          # full byte domain


# --- the text-only axiom, cross-checked against the real callee --------------

def check_text_only_axiom():
    """`pad_runtime`'s `Requires(text_form(text))` says the modelled padding
    step is defined on textual content. Exercise that against the real callee
    rather than assume it: at EVERY length (whole multiples of the width
    included, not skipped), a value that is not textual content must never come
    back from the real helper as textual content -- it either fails on the
    concatenation or is returned untouched and still not textual content -- and
    textual content must come back as textual content, padded and
    content-preserving.

    The model makes no failure claim of its own (there is no `Exsures` in the
    bundle): it restricts the callee's domain by precondition. So no
    MODEL-raises / REAL-returns divergence is claimed at any length, and the
    whole-multiple family is checked rather than excluded.
    """
    from astropy.io.fits.card import _pad
    problems = []
    passthrough = []
    for n in range(0, 4 * CARD_LENGTH + 1):
        bs = bytes((33 + (k * 7) % 90) for k in range(n))
        try:
            got = _pad(bs)
        except TypeError:
            pass                                       # concatenation branch
        else:
            passthrough.append(n)
            if not (got is bs and isinstance(got, bytes)):
                problems.append(
                    "real _pad turned a non-text argument of length %d into %r "
                    "(the Requires(text_form) of pad_runtime is unsound)"
                    % (n, type(got).__name__))
        text = bs.decode("latin1")
        out = _pad(text)
        if not isinstance(out, str):
            problems.append("real _pad on textual content of length %d did not "
                            "return textual content" % n)
        elif out[:len(text)] != text or len(out) % CARD_LENGTH != 0:
            problems.append("real _pad mis-padded textual content %r -> %r"
                            % (text, out))
    return problems, passthrough


def main():
    import astropy.io.fits.card as cardmod
    if "image.decode('latin1')" not in open(cardmod.__file__).read():
        print("G-CONF FAIL: the oracle module is not the patched one")
        print(json.dumps({"checked": 0, "disagreements": 1, "seed": SEED,
                          "shadow": "direct", "note": "oracle not patched"}))
        return 1

    problems, passthrough = check_text_only_axiom()
    if problems:
        print("G-CONF FAIL: the @ContractOnly text-form axiom does not hold of "
              "the real callee:")
        for p in problems:
            print("  " + p)
        print(json.dumps({"checked": 0, "disagreements": len(problems),
                          "seed": SEED, "shadow": "direct",
                          "note": "text-form axiom refuted"}))
        return 1

    rng = random.Random(SEED)
    checked = 0
    n_boundary = 0
    internal_checked = 0
    disagreements = []

    def one(raw, from_bytes, sample_internal):
        """Drive shadow + oracle on one Requires-satisfying input."""
        nonlocal checked, internal_checked
        assert all_bytes(ToSeq(raw)), "generated input violates Requires"
        try:
            shadow = build_record_image(raw, from_bytes)
        except Exception as e:                          # noqa: BLE001
            shadow = ("EXC", type(e).__name__)
        try:
            oracle = oracle_image(raw, from_bytes)
        except Exception as e:                          # noqa: BLE001
            oracle = ("EXC", type(e).__name__)
        checked += 1
        if sample_internal and len(raw) <= 200:
            # the stripped `Assert(ToSeq(image) == reinterpret(ToSeq(raw)))`:
            # a model-internal consistency check, NOT the differential.
            internal_checked += 1
            rebuilt = []
            i = len(raw)
            while i > 0:
                rebuilt = [raw[i - 1]] + rebuilt
                i = i - 1
            if ToSeq(rebuilt) != reinterpret(ToSeq(raw)):
                disagreements.append((raw, from_bytes, "loop != reinterpret",
                                      rebuilt))
                return
        if shadow != oracle:
            disagreements.append((raw, from_bytes, shadow, oracle))

    for raw in boundary_raws():
        for from_bytes in (True, False):
            n_boundary += 1
            one(raw, from_bytes, sample_internal=True)
            if disagreements:
                break
        if disagreements:
            break

    if not disagreements:
        for k in range(N_FUZZ):
            raw = fuzz_raw(rng)
            from_bytes = rng.random() < 0.5
            one(raw, from_bytes, sample_internal=(k % 1000 == 0))
            if disagreements:
                break

    if disagreements:
        print("G-CONF FAIL: %d disagreement(s) over %d inputs (seed=%d):"
              % (len(disagreements), checked, SEED))
        for raw, fb, sh, orc in disagreements[:5]:
            print("  input: raw=%r from_bytes=%r  (concrete=%r)"
                  % (raw[:64], fb,
                     (bytes(raw) if fb else "".join(chr(c) for c in raw))[:64]))
            print("    shadow=%r" % (sh[:96] if isinstance(sh, list) else sh,))
            print("    oracle=%r" % (orc[:96] if isinstance(orc, list) else orc,))
        print(json.dumps({"checked": checked,
                          "disagreements": len(disagreements),
                          "seed": SEED, "shadow": "direct"}))
        return 1

    print("G-CONF OK: contract-stripped impl region of build_record_image "
          "(enter_text_form = the REAL guarded latin-1 step, pad_runtime = the "
          "REAL astropy.io.fits.card._pad) agrees with the REAL patched "
          "Card.fromstring(image)._image on %d inputs (%d boundary + %d fuzz, "
          "seed %d); %d model-internal loop==reinterpret checks; the padding "
          "step is text-only on the real callee at every length (non-text "
          "returned untouched-and-still-non-text at %s, never as text)."
          % (checked, n_boundary, N_FUZZ, SEED, internal_checked, passthrough))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region: copy "
                                "loop + enter_text_form + pad_runtime)",
                      "oracle": "astropy.io.fits.card.Card.fromstring (called, "
                                "patched)",
                      "contract_only_callees": [
                          "bytes.decode('latin1') via the guarded step at "
                          "astropy/io/fits/card.py:557-562 (called)",
                          "astropy.io.fits.card._pad (called)"]}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
