#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-13512.

This bundle consumes NO axiom. The changed serialisation operation is modelled
DEEPLY in model.py (the pure region: `json_char` / `json_string_body`, wrapped
by `json_render_text` as `'"' + body + '"'`). G-AX validates that deep model
against the REAL standard-library serialiser the gold patch calls:

    json.dumps(s, ensure_ascii=False)        # for a text scalar s

i.e. an A-reference, checked here, not a consumed axiom.

The deep model asserts, over the modelled domain (printable code points,
>= U+0020 — exactly the domain of every tested input):

    rendering(s) == '"' + concat(json_char(c) for c in s) + '"'
    json_char('"') == '\\"'        json_char('\\') == '\\\\'
    json_char(c)   == c            for every other code point, INCLUDING all
                                   non-ASCII code points (>= U+0080)

The discriminating property: every code point >= U+0080 is emitted literally
as itself, never transliterated into an ASCII-only "\\uXXXX" surrogate form.
This check asserts that index-level (per-code-point) equivalence directly and
also the whole-string equality, on boundary + adversarial fuzz inputs, and
loudly checks the F2P discriminator inputs. Imports only the standard library
(`json`), the same module the gold patch calls. Exit 0 iff every obligation
holds.
"""
import json
import random
import sys


def json_char(c):
    """Reference of model.py's deep model `json_char` (one printable code
    point, ensure_ascii=False rule), as a list of code points."""
    if c == 34:        # '"'
        return [92, 34]
    if c == 92:        # '\'
        return [92, 92]
    return [c]


def json_string_body(codepoints):
    """Reference of model.py's deep model `json_string_body`."""
    out = []
    for c in codepoints:
        out.extend(json_char(c))
    return out


def model_render(s):
    """The whole model rendering: '"' + body + '"', as code points."""
    return [34] + json_string_body([ord(ch) for ch in s]) + [34]


def real_render(s):
    """The REAL callee the gold patch uses for a text scalar."""
    return [ord(ch) for ch in json.dumps(s, ensure_ascii=False)]


def check_render(s):
    """Whole-string equivalence: deep model == real json.dumps(...,
    ensure_ascii=False)."""
    observed = real_render(s)
    expected = model_render(s)
    assert observed == expected, (
        "deep model unsound on %r: json.dumps(ensure_ascii=False) gave %r, "
        "model gives %r" % (s, observed, expected))


def check_char_index(c):
    """Index-level equivalence asserted at the per-code-point level (no double
    mask): the real serialiser's encoding of the single code point c, taken
    out of its surrounding quotes, equals json_char(c)."""
    s = chr(c)
    real = json.dumps(s, ensure_ascii=False)
    # strip the surrounding quotation marks the serialiser always adds
    assert real[0] == '"' and real[-1] == '"', real
    real_body = [ord(ch) for ch in real[1:-1]]
    expected = json_char(c)
    assert real_body == expected, (
        "json_char unsound at U+%04X: real body %r, model %r"
        % (c, real_body, expected))
    # the discriminating clause: non-ASCII code points are kept literal
    if c >= 128:
        assert expected == [c], (
            "discriminator violated: model escapes non-ASCII U+%04X as %r"
            % (c, expected))
        assert real_body == [c], (
            "real serialiser escaped non-ASCII U+%04X as %r under "
            "ensure_ascii=False" % (c, real_body))


def main():
    # --- the F2P discriminator inputs: must NOT be skipped, must match -------
    f2p = [
        "a",                 # admin_utils + forms: plain ASCII scalar
        "你好 世界",     # '你好 世界'  admin_utils
        "你好，世界",  # '你好，世界' forms_tests
        "\U0001f600\U0001f431",          # '😀🐱'   forms_tests (astral / emoji)
        "jaźń",                # 'jaźń'  forms_tests (Polish)
        "foo",
    ]
    for s in f2p:
        check_render(s)
        # spell out the exact F2P expectation for the headline case
    assert json.dumps("你好 世界", ensure_ascii=False) == '"你好 世界"'
    assert json.dumps("\U0001f600\U0001f431", ensure_ascii=False) == '"\U0001f600\U0001f431"'

    # --- index-level per-code-point sweep over the modelled domain ----------
    # full sweep of printable BMP + a sample of astral planes
    for c in range(0x20, 0x10000):
        check_char_index(c)
    for c in [0x1F600, 0x1F431, 0x1F4A9, 0x10000, 0x10FFFF, 0x20BB7, 0x1D11E]:
        check_char_index(c)

    # --- whole-string boundary cases ----------------------------------------
    boundary = [
        "", '"', "\\", '""', "\\\\", '"\\"', "a\"b\\c",
        "你好", "\U0001f600", "café", "naïve",
        "你好\"\\世界",  # non-ASCII mixed with the two escapes
        "{}", "[]", "abc 123 !@#",
    ]
    for s in boundary:
        check_render(s)

    # --- randomized fuzz over the modelled domain (>= U+0020) ---------------
    rng = random.Random(13512)
    pool = (
        [chr(c) for c in range(0x20, 0x7f)] +      # printable ASCII
        [chr(c) for c in [0x4f60, 0x597d, 0x4e16, 0x754c, 0xff0c]] +  # CJK
        [chr(c) for c in [0xe9, 0x17a, 0x144, 0xdf, 0x3b1]] +         # Latin/Greek
        [chr(c) for c in [0x1f600, 0x1f431, 0x1f4a9]] +              # astral
        ['"', '\\']                                  # the two escaped points
    )
    for _ in range(40000):
        n = rng.randint(0, 24)
        s = "".join(rng.choice(pool) for _ in range(n))
        check_render(s)

    print("G-AX OK: deep model json_string_body (== json.dumps(ensure_ascii="
          "=False)) sound on %d F2P + full 0x20-0xFFFF index sweep + astral + "
          "%d boundary + 40000 fuzz inputs; non-ASCII kept literal."
          % (len(f2p), len(boundary)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
