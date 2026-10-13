#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-12308.

There are NO consumed @ContractOnly axioms in model.py. The two callees the
rendered branch invokes are modelled DEEPLY and validated here against their
REAL callees as A-references, asserting THE SAME property model.py proves, on
THE SAME structured inputs model.py claims to cover:

  (A-reference 1) the canonical interchange encoder -- the real callee is
      CPython's `json.dumps(value)` (Django's `JSONField.get_prep_value(value)`
      with the default `encoder=None`). model.py models it DEEPLY as the
      single self-recursive STRUCTURAL serialiser `interchange_form`
      (`node_body` / `ser_list` over the `JNode` tree): a string token wraps in
      the double-quote delimiter U+0022 and, INSIDE that pair, is laid down in
      the interchange alphabet by `esc_seq` / `esc_char` rather than spliced in
      raw (U+0022 and U+005C each as U+005C followed by themselves; U+0008,
      U+0009, U+000A, U+000C, U+000D as U+005C + b/t/n/f/r; every other code
      point outside U+0020..U+007E as U+005C, U+0075 and four lowercase
      hexadecimal digits, one above U+FFFF as the two such forms of its
      surrogate halves); an array lays its elements between
      brackets, comma-and-space separated; an object lays its members between
      braces, each a double-quoted key laid down the same way, a colon-space,
      then the member value.
      This check reproduces that EXACT structural serialiser
      (`interchange_form_model`) and asserts, ON THE STRUCTURED VALUES, that it
      equals the real `json.dumps(value)` -- the very property model.py proves
      (`ToSeq(Result()) == interchange_form(value)`), not a parallel routing.

  (A-reference 2) the general-purpose display fallback -- the real callee is
      Django's `display_for_value(value, empty)`, which DISPATCHES on the
      value's own shape: a list/tuple takes the join arm
      `', '.join(str(v) for v in value)`, everything else the general arm
      `str(value)`. model.py therefore CARRIES that callee's own output in
      `content` and models the fallback as `fallback_form` == the identity: the
      text passed through unchanged, no delimiters added by the renderer. This
      check imports the REAL `display_for_value` and asserts the identity
      pass-through on it -- on the tuple-keyed F2P value, on list/tuple-rooted
      non-encodables where the join arm makes the real text DIFFER from
      `str(value)` (so modelling it as `str` would be caught here), and on the
      falsy stored values, which the renderer never offers to the encoder and
      which therefore take this arm rather than the placeholder. Also the
      single-vs-double-quote delimiter contrast against json.dumps' tokens.

The serialiser models the token form explicitly, so it is exact against
`json.dumps` under its default configuration (the field's `encoder` is None:
ASCII-only output, ', ' / ': ' separators, keys in insertion order) for EVERY
string token and key, not only for the ones that pass through unchanged. The
fuzz therefore draws tokens from the full code point range -- the delimiter, the
escape character, the control positions, the non-ASCII BMP band, the surrogate
range and the astral planes -- while ranging over the full STRUCTURED value
shapes (nested dicts / lists / strings), so the fuzz domain is a superset of the
four F2P value shapes and the property asserted == the property model.py
encodes, exercised on the declared input set.

A-reference 1 imports only the standard library: `json` is the very module
Django's `JSONField.get_prep_value` calls. A-reference 2 imports exactly one
repo function, `display_for_value` -- the callee it is a reference FOR, so it is
checked against the real thing rather than a reproduction of it. Exit 0 iff
sound.
"""
import json
import random
import sys


# --- model.py's deep model, reproduced char-for-char (kept in lock-step with
#     the pure region: node_body / ser_list / interchange_form). --------------
#
# A JSON value is mapped to the model's JNode tree as:
#   str  -> STRING(text)
#   list -> ARRAY(elements)
#   dict -> OBJECT(members), each member = (key, value)
# and serialised structurally. Code points are produced as a Python list[int]
# (the model's `List[int]` carrier); we compare via the rendered str.

def cps(s):
    return [ord(ch) for ch in s]


def hex_digit(d):
    """Reproduction of model.py `hex_digit`."""
    return 48 + d if d < 10 else 87 + d


def hex_form(c):
    """Reproduction of model.py `hex_form`: U+005C, U+0075 and four lowercase
    hexadecimal digits of one 16-bit unit, most significant first."""
    return ([92, 117] + [hex_digit(c // 4096)] + [hex_digit((c // 256) % 16)]
            + [hex_digit((c // 16) % 16)] + [hex_digit(c % 16)])


def esc_char(c):
    """Reproduction of model.py `esc_char`: the interchange form of ONE code
    point of a string token or of a key."""
    if c == 34:
        return [92, 34]
    if c == 92:
        return [92, 92]
    if c == 8:
        return [92, 98]
    if c == 9:
        return [92, 116]
    if c == 10:
        return [92, 110]
    if c == 12:
        return [92, 102]
    if c == 13:
        return [92, 114]
    if 32 <= c and c <= 126:
        return [c]
    if 0 <= c and c <= 65535:
        return hex_form(c)
    if 65536 <= c and c <= 1114111:
        return (hex_form(55296 + (c - 65536) // 1024)
                + hex_form(56320 + (c - 65536) % 1024))
    return [c]


def esc_seq(codepoints):
    """Reproduction of model.py `esc_seq`: each code point of the token replaced
    by that code point's own interchange form, in order."""
    out = []
    for c in codepoints:
        out += esc_char(c)
    return out


def node_body(value):
    """Reproduction of model.py `node_body` / `interchange_form` for a single
    value: the structural double-quote interchange serialisation."""
    if isinstance(value, str):                       # STRING: "text"
        return [34] + esc_seq(cps(value)) + [34]
    if isinstance(value, list):                      # ARRAY: [ elements ]
        return [91] + ser_list([("elem", v) for v in value]) + [93]
    if isinstance(value, dict):                      # OBJECT: { members }
        return [123] + ser_list([("member", (k, v)) for k, v in value.items()]) + [125]
    raise TypeError("unsupported value shape: %r" % (value,))


def ser_list(items):
    """Reproduction of model.py `ser_list`: each node's body, comma-and-space
    (44,32) separated, no trailing separator. `items` is a list of tagged
    siblings: ("elem", v) for array elements, ("member", (k, v)) for members."""
    out = []
    for i, (tag, payload) in enumerate(items):
        if i > 0:
            out += [44, 32]                          # ", "
        if tag == "elem":
            out += node_body(payload)
        else:                                        # MEMBER: "key": value
            k, v = payload
            out += [34] + esc_seq(cps(k)) + [34] + [58, 32] + node_body(v)
    return out


def interchange_form_model(value):
    """model.py `interchange_form(value)` as a rendered string."""
    return "".join(chr(c) for c in node_body(value))


def fallback_form_model(content):
    """model.py `fallback_form(content)`: the identity -- the general-purpose
    display text passed through unchanged (no delimiters added)."""
    return "".join(chr(c) for c in cps(content))


def real_display_for_value():
    """The REAL fallback callee (mapping.md section 3.2): Django's
    display_for_value. It dispatches on the value's shape -- a list/tuple takes
    the join arm ', '.join(str(v) for v in value), everything else str(value) --
    so `content` must carry ITS output, never str(value)."""
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(INSTALLED_APPS=["django.contrib.contenttypes",
                                           "django.contrib.auth"],
                           USE_TZ=False)
    django.setup()
    from django.contrib.admin.utils import display_for_value
    return display_for_value


# --- A-reference 1: interchange_form == real json.dumps on a STRUCTURED value -

def check_interchange_form(value):
    """Assert model.py's structural interchange_form(value) == real
    json.dumps(value) -- the EXACT property model.py proves, on the real
    structured value (string tokens / keys drawn from a non-escaping alphabet)."""
    observed = json.dumps(value)                     # real callee
    expected = interchange_form_model(value)         # deep model (structural)
    assert observed == expected, (
        "interchange_form deep model unsound on %r: json.dumps gave %r, deep "
        "model gives %r" % (value, observed, expected))


# --- random structured-value generator (nested dicts / lists / strings) ------

# the FULL code point range is in domain: one representative of every class the
# interchange alphabet treats specially, plus unrestricted draws below.
_ALPHABET = list("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
                 "0123456789 .;:!?-=+_()"
                 "\"\\/'<>&"
                 "\b\t\n\f\r\x00\x01\x1f\x7f"
                 "\u00e9\u00ff\u0416\u2022\u2028\uffff"
                 "\ud800\udfff"
                 "\U0001f600\U0010ffff")


def _rand_token(rng):
    n = rng.randint(0, 8)
    out = []
    for _ in range(n):
        if rng.random() < 0.1:
            out.append(chr(rng.randrange(0, 0x110000)))   # any code point
        else:
            out.append(rng.choice(_ALPHABET))
    return "".join(out)


def _rand_value(rng, depth):
    if depth <= 0:
        return _rand_token(rng)
    r = rng.random()
    if r < 0.5:
        return _rand_token(rng)
    if r < 0.75:                                     # list
        return [_rand_value(rng, depth - 1) for _ in range(rng.randint(0, 4))]
    # dict (string keys only -- valid JSON objects)
    d = {}
    for _ in range(rng.randint(0, 4)):
        d[_rand_token(rng) + str(len(d))] = _rand_value(rng, depth - 1)
    return d


def main():
    empty = '-'

    # ----- the four FAIL_TO_PASS test cases, verbatim -----------------------
    f2p = [
        ({'a': {'b': 'c'}}, '{"a": {"b": "c"}}'),     # dict -> json.dumps
        (['a', 'b'], '["a", "b"]'),                   # list -> json.dumps
        ('a', '"a"'),                                 # str  -> json.dumps
        ({('a', 'b'): 'c'}, "{('a', 'b'): 'c'}"),     # tuple-key -> str fallback
    ]

    # The three ENCODABLE F2P values: model's structural interchange_form MUST
    # equal the real json.dumps AND the test's expected display value.
    for value, expected in f2p[:3]:
        check_interchange_form(value)
        assert interchange_form_model(value) == expected, (
            "interchange_form_model(%r) = %r != F2P expected %r"
            % (value, interchange_form_model(value), expected))
        assert json.dumps(value) == expected

    # The NON-ENCODABLE F2P value (tuple key): json.dumps raises TypeError; the
    # real fallback callee reaches its general arm here, so its text coincides
    # with str(value) on THIS value; string tokens inside it carry the single
    # quote (vs json.dumps' double quote).
    tuple_key, tk_expected = f2p[3]
    raised = False
    try:
        json.dumps(tuple_key)
    except TypeError:
        raised = True
    assert raised, "tuple-keyed dict must raise TypeError under json.dumps"
    assert str(tuple_key) == tk_expected, (
        "str fallback mismatch: %r != %r" % (str(tuple_key), tk_expected))

    # A-reference 2: the model's fallback is the IDENTITY on the text the REAL
    # fallback callee produced: fallback_form(content) == content, where
    # content = display_for_value(value, empty). Checked against the real repo
    # callee, NOT against str(value) -- the two differ on every list/tuple root.
    dfv = real_display_for_value()
    assert fallback_form_model(dfv(tuple_key, empty)) == tk_expected, (
        "fallback_form must pass the real fallback text through unchanged: "
        "%r != %r" % (fallback_form_model(dfv(tuple_key, empty)), tk_expected))

    # The JOIN arm: on a list/tuple-rooted non-encodable the real callee lays the
    # elements out one by one, so its text is NOT str(value). This is exactly the
    # reason `content` carries the callee's output instead of being derived here.
    join_arm = [
        ([{('x', 'y'): 'z'}],       "{('x', 'y'): 'z'}"),
        (['a', {('x', 'y'): 'z'}],  "a, {('x', 'y'): 'z'}"),
        ([b'raw'],                  "b'raw'"),
        ((b'raw', 'a'),             "b'raw', a"),
    ]
    for value, expected in join_arm:
        real_txt = dfv(value, empty)
        assert real_txt == expected, (
            "real display_for_value(%r) = %r, expected %r"
            % (value, real_txt, expected))
        assert fallback_form_model(real_txt) == expected, (
            "fallback_form must be the identity on %r" % (real_txt,))
        assert real_txt != str(value), (
            "join-arm value %r must distinguish the real callee (%r) from "
            "str(value) (%r) -- else the reference is untested"
            % (value, real_txt, str(value)))

    # Falsy STORED values: json.dumps returns for these, but the renderer never
    # offers them to the encoder, so they take the fallback arm. The identity
    # pass-through must hold on the real callee's text for them too.
    for value, expected in [([], ''), ('', ''), ({}, '{}'),
                            (0, '0'), (False, 'False')]:
        real_txt = str(dfv(value, empty))
        assert real_txt == expected, (
            "real display_for_value(%r) = %r, expected %r"
            % (value, real_txt, expected))
        assert fallback_form_model(real_txt) == expected

    # delimiter contrast on the str-token level: the fallback text delimits its
    # string tokens with the single quote (repr, INSIDE that text),
    # json.dumps uses the double quote.
    assert fallback_form_model(repr("a")) == "'a'"
    assert json.dumps("a") == '"a"'
    assert fallback_form_model(repr("a")) != json.dumps("a")

    # null / absent -> placeholder (model's `not present` branch).
    assert empty == '-'

    # ----- discriminating delimiter contrast on the encodable values --------
    for value, _ in f2p[:3]:
        j = json.dumps(value)
        s = str(value)
        assert '"' in j and "'" not in j, (
            "json.dumps must delimit string tokens with the double quote: %r" % j)
        if isinstance(value, dict):
            assert "'" in s and '"' not in s, (
                "str() printout must delimit string tokens with the single "
                "quote: %r" % s)
        assert j != s, (
            "encodable value must render differently under json.dumps vs str: "
            "%r vs %r" % (j, s))

    # ----- boundary structured values ---------------------------------------
    boundary = [
        "", "a", "ab", "hello world", "JSON",
        [], ["x"], ["x", "y", "z"],
        {}, {"k": "v"}, {"k": {"n": "m"}},
        {"a": ["b", "c"]}, [{"k": "v"}, "tail"],
        {"a": {"b": {"c": "d"}}},                     # deep nesting
        ["a", ["b", ["c"]]],                          # nested arrays
        # --- the token form: every escape class, as a VALUE and as a KEY ------
        'a"b', '"', '\\', 'a\\b', '\\"', '"\\"',
        '\b', '\t', '\n', '\f', '\r', 'a\nb', '\t\n\r\b\f',
        '\x00', '\x01', '\x1f', '\x00\x1f', '\x7f', 'a\x7fb',
        '\u00e9', '\u00ff', '\u0416', '\u2022', '\u2028\u2029', '\uffff',
        '\ud800', '\udfff', '\ud800\udc00',
        '\U0001f600', '\U0010ffff', 'a\U0001f600b',
        '"' * 40, '\\' * 40, '\x00' * 40,
        ['a"b', 'c\\d'], ['\n', '\t'], [['\u00e9'], ['\U0001f600']],
        {'a"b': 'c\\d'}, {'\n': '\t'}, {'\u00e9': '\U0001f600'},
        {'"': {'\\': ['\x00', '\u2028']}},
        {'k': 'v"w', 'x\\y': ['\u00e9', {'\t': '\ud800'}]},
    ]
    for value in boundary:
        check_interchange_form(value)

    # ----- randomized fuzz over nested STRUCTURED values --------------------
    rng = random.Random(12308)
    for _ in range(20000):
        value = _rand_value(rng, rng.randint(0, 4))
        check_interchange_form(value)

    # ----- every single code point, as a token AND as a key -----------------
    for cp in range(0, 0x110000):
        ch = chr(cp)
        check_interchange_form(ch)
        if cp % 977 == 0:                             # sampled as a key
            check_interchange_form({ch: [ch, {ch: ch}]})

    print("G-AX OK: structural interchange_form == real json.dumps on the 3 "
          "encodable F2P values + %d boundary + 20000 fuzz STRUCTURED values "
          "(nested dicts/lists/strings, tokens drawn from the full code point "
          "range) + all 1114112 code points as a single-token value; the "
          "tuple-key F2P value raises and "
          "falls back to the REAL display_for_value text, passed through "
          "UNCHANGED (fallback_form = identity), as do the join-arm "
          "list/tuple-rooted non-encodables (where that text differs from "
          "str(value)) and the falsy stored values; delimiter contrast holds."
          % len(boundary))
    return 0


if __name__ == "__main__":
    sys.exit(main())
