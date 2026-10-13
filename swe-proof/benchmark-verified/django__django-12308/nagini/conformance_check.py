#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-12308 (nagini).

SHADOW: the impl region of model.py (``serialize`` / ``serialize_list`` /
``append_all`` / ``append_escaped`` / ``append_esc_char`` /
``display_structured_value``), copied VERBATIM below with
only the contract calls (Requires / Ensures / Invariant / Assert / Fold /
Unfold) stripped. The pure region (``JNode``, ``node_body`` / ``ser_list`` /
``interchange_form`` / ``fallback_form`` / ``esc_seq`` / ``esc_char`` /
``hex_form`` / ``hex_digit``) copies over on top of a small
immutable tuple-backed PSeq shim (``Unfolding(acc, e)`` erases to ``e``) and
is kept as an internal cross-check of the executable shadow. There are no
@ContractOnly callees (mapping.md section 3: no consumed axioms; the two
A-references are deep models inside the pure region itself).

ORACLE: the REAL patched repo function the model models per mapping.md
section 1 -- ``django.contrib.admin.utils.display_for_field`` driven with a
``django.db.models.JSONField()`` (default encoder) as the field argument.
The gate applies patch.diff to /testbed and sets PYTHONPATH=/testbed before
this script runs, so the import resolves to the patched module.

TYPE BRIDGE (mapping.md section 2):
  * repo ``str`` <-> model ``List[int]`` of code points via ``ord``/``chr``;
  * the structured value (nested dict / list / str) <-> a recursive ``JNode``
    tree (0 STRING / 1 ARRAY / 2 OBJECT / 3 MEMBER, sibling/inner linked),
    built here by ``to_jnode``;
  * ``present == (value is not None)`` -- the repo renders the placeholder on
    the ``value is None`` arm and NOWHERE else. A falsy-but-stored value
    (``[]``, ``''``, ``{}``, ``0``, ``False``) is present and is probed
    through ``check_value``, not ``check_absent``;
  * ``encodable == (bool(value) and json.dumps(value) returns)`` -- BOTH
    conjuncts, because the repo only offers a truthy value to the encoder and
    only displays the encoder's output when it does not raise. A value that is
    not encodable has no JNode image needed, so the shadow receives a
    placeholder node there -- the modeled function consults only ``content``;
  * ``content`` == the code points of ``display_for_value(value,
    empty_value_display)``, i.e. the REAL fallback callee's own output -- not
    ``str(value)``. That callee dispatches on shape, so a list/tuple root takes
    its join arm and the two texts differ; probes therefore include
    sequence-rooted non-encodables (mapping.md section 3.2).

DOMAIN (mapping.md section 3.1): the deep structural serialiser models the
real interchange encoder under its DEFAULT configuration (the field's encoder is
None, so the encoder produces ASCII-only output with the standard ', ' / ': '
separators and no key reordering), and it models the TOKEN FORM explicitly, so
the domain is not restricted to tokens that pass through unchanged. Generation
therefore draws string tokens and keys from the FULL code point range: the
delimiter U+0022, the escape character U+005C, every control position, the
non-ASCII BMP band, the surrogate range and the astral planes are all in
domain, both as values and as object keys.

INPUT PLAN (>= 1e5 Requires-satisfying inputs): boundary structured values
(single tokens, empty inner tokens/arrays/objects, deep nesting, long
sibling chains, long tokens, every escape class as a token AND as a key, dict-rooted AND sequence-rooted non-encodable
shapes, the falsy stored values across every placeholder text, absent probes
across several placeholder texts) + 100000 randomized fuzz probes mixing
encodable / non-encodable / falsy-stored / absent cases. All three dispatch
outcomes -- placeholder, interchange, fallback -- are generated; nothing
forces the probed value truthy. Pinned fuzz seed: 12308 (recorded in
mapping.md). Exit 0 iff zero disagreements; on disagreement prints the input
and both outputs and exits 1.
"""
import json
import random
import sys

SEED = 12308
N_FUZZ = 100000
# the pure folds (`ser_list`, `esc_seq`) are copied VERBATIM from the spec's
# pure region, so they recurse once per sibling and once per token code point;
# the long-token / long-chain boundary probes need more than the interpreter's
# default 1000 frames.
sys.setrecursionlimit(100000)


# --- PSeq shim: immutable sequence with the operations the pure region uses --

class PSeq(object):
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

    def __eq__(self, other):
        return isinstance(other, PSeq) and self._t == other._t

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self._t)

    def __len__(self):
        return len(self._t)

    def __getitem__(self, i):
        return self._t[i]


def ToSeq(lst):
    return PSeq._wrap(lst)


# --- pure region of model.py, contracts stripped ------------------------------

class JNode(object):
    """One node in a structured-value tree, in sibling/inner linked form
    (kinds: 0 STRING, 1 ARRAY, 2 OBJECT, 3 MEMBER; see model.py)."""

    def __init__(self, kind, text, inner, nxt):
        self.kind = kind
        self.text = text
        self.inner = inner
        self.nxt = nxt


def empty_seq():
    return PSeq(0).take(0)


def hex_digit(d):
    return 48 + d if d < 10 else 87 + d


def hex_form(c):
    return (PSeq(92, 117) + PSeq(hex_digit(c // 4096))
            + PSeq(hex_digit((c // 256) % 16))
            + PSeq(hex_digit((c // 16) % 16)) + PSeq(hex_digit(c % 16)))


def esc_char(c):
    """The interchange form of ONE code point of a string token or of a key."""
    if c == 34:
        return PSeq(92, 34)
    if c == 92:
        return PSeq(92, 92)
    if c == 8:
        return PSeq(92, 98)
    if c == 9:
        return PSeq(92, 116)
    if c == 10:
        return PSeq(92, 110)
    if c == 12:
        return PSeq(92, 102)
    if c == 13:
        return PSeq(92, 114)
    if 32 <= c and c <= 126:
        return PSeq(c)
    if 0 <= c and c <= 65535:
        return hex_form(c)
    if 65536 <= c and c <= 1114111:
        return (hex_form(55296 + (c - 65536) // 1024)
                + hex_form(56320 + (c - 65536) % 1024))
    return PSeq(c)


def esc_seq(s):
    """The interchange form of a WHOLE token (or key)."""
    if len(s) == 0:
        return empty_seq()
    return esc_seq(s.take(len(s) - 1)) + esc_char(s[len(s) - 1])


def node_body(head):
    """Interchange serialisation of the SINGLE node `head` (no sibling
    separator); Unfolding erased."""
    return (
        # STRING: "text"
        PSeq(34) + esc_seq(ToSeq(head.text)) + PSeq(34) if head.kind == 0
        # ARRAY: [ elements ]
        else (PSeq(91) + ser_list(head.inner) + PSeq(93) if head.kind == 1
              # OBJECT: { members }
              else (PSeq(123) + ser_list(head.inner) + PSeq(125) if head.kind == 2
                    # MEMBER: "key": value
                    else PSeq(34) + esc_seq(ToSeq(head.text)) + PSeq(34)
                    + PSeq(58, 32) + ser_list(head.inner))))


def ser_list(head):
    """Interchange serialisation of the sibling list starting at `head`:
    each node's body, comma-and-space (44,32) separated; Unfolding erased."""
    if head is None:
        return empty_seq()
    return (
        (PSeq(34) + esc_seq(ToSeq(head.text)) + PSeq(34) if head.kind == 0
         else (PSeq(91) + ser_list(head.inner) + PSeq(93) if head.kind == 1
               else (PSeq(123) + ser_list(head.inner) + PSeq(125) if head.kind == 2
                     else PSeq(34) + esc_seq(ToSeq(head.text)) + PSeq(34)
                     + PSeq(58, 32) + ser_list(head.inner)))) +
        (empty_seq() if head.nxt is None
         else PSeq(44, 32) + ser_list(head.nxt)))


def interchange_form(node):
    if node is None:
        return empty_seq()
    return node_body(node)


def fallback_form(content):
    return content


# --- impl region of model.py, verbatim, contract calls stripped ---------------

def serialize(node):
    if node.kind == 0:                          # STRING: "text"
        out = [34]  # type: List[int]
        append_escaped(out, node.text)
        out.append(34)
        return out
    if node.kind == 1:                          # ARRAY: [ elements ]
        body = serialize_list(node.inner)
        result = [91]  # type: List[int]
        append_all(result, body)
        result.append(93)
        return result
    if node.kind == 2:                          # OBJECT: { members }
        mbody = serialize_list(node.inner)
        result2 = [123]  # type: List[int]
        append_all(result2, mbody)
        result2.append(125)
        return result2
    # MEMBER: "key": value
    result3 = [34]  # type: List[int]
    append_escaped(result3, node.text)
    result3.append(34)
    result3.append(58)
    result3.append(32)
    vbody = serialize_list(node.inner)
    append_all(result3, vbody)
    return result3


def serialize_list(head):
    result = []  # type: List[int]
    if head is None:
        return result
    # head body, dispatched INLINE (mirrors ser_list / node_body), recursing
    # into serialize_list on the sub-nodes only -- all while `head` is unfolded.
    if head.kind == 0:                          # STRING: "text"
        result.append(34)
        append_escaped(result, head.text)
        result.append(34)
    elif head.kind == 1:                        # ARRAY: [ elements ]
        result.append(91)
        body = serialize_list(head.inner)
        append_all(result, body)
        result.append(93)
    elif head.kind == 2:                        # OBJECT: { members }
        result.append(123)
        mbody = serialize_list(head.inner)
        append_all(result, mbody)
        result.append(125)
    else:                                       # MEMBER: "key": value
        result.append(34)
        append_escaped(result, head.text)
        result.append(34)
        result.append(58)
        result.append(32)
        vbody = serialize_list(head.inner)
        append_all(result, vbody)
    # tail: the rest of the sibling list, comma-and-space separated.
    if head.nxt is not None:
        result.append(44)
        result.append(32)
        rest = serialize_list(head.nxt)
        append_all(result, rest)
    return result


def append_esc_char(result, c):
    if c == 34:
        result.append(92)
        result.append(34)
    elif c == 92:
        result.append(92)
        result.append(92)
    elif c == 8:
        result.append(92)
        result.append(98)
    elif c == 9:
        result.append(92)
        result.append(116)
    elif c == 10:
        result.append(92)
        result.append(110)
    elif c == 12:
        result.append(92)
        result.append(102)
    elif c == 13:
        result.append(92)
        result.append(114)
    elif 32 <= c and c <= 126:
        result.append(c)
    elif 0 <= c and c <= 65535:
        result.append(92)
        result.append(117)
        result.append(hex_digit(c // 4096))
        result.append(hex_digit((c // 256) % 16))
        result.append(hex_digit((c // 16) % 16))
        result.append(hex_digit(c % 16))
    elif 65536 <= c and c <= 1114111:
        hi = 55296 + (c - 65536) // 1024
        lo = 56320 + (c - 65536) % 1024
        result.append(92)
        result.append(117)
        result.append(hex_digit(hi // 4096))
        result.append(hex_digit((hi // 256) % 16))
        result.append(hex_digit((hi // 16) % 16))
        result.append(hex_digit(hi % 16))
        result.append(92)
        result.append(117)
        result.append(hex_digit(lo // 4096))
        result.append(hex_digit((lo // 256) % 16))
        result.append(hex_digit((lo // 16) % 16))
        result.append(hex_digit(lo % 16))
    else:
        result.append(c)


def append_escaped(result, src):
    i = 0
    while i < len(src):
        append_esc_char(result, src[i])
        i = i + 1


def append_all(result, src):
    i = 0
    while i < len(src):
        result.append(src[i])
        i = i + 1


def display_structured_value(value, empty, content, present, encodable):
    if not present:
        result = []  # type: List[int]
        j = 0
        while j < len(empty):
            result.append(empty[j])
            j = j + 1
        return result

    if encodable:
        # the interchange encoding: the structural serialisation of the tree.
        return serialize(value)

    # fallback: the general-purpose display text for this value, returned
    # unchanged (a fresh owned copy of it; no delimiters are added).
    out2 = []  # type: List[int]
    m = 0
    while m < len(content):
        out2.append(content[m])
        m = m + 1
    return out2


# --- bridge: repo value <-> JNode tree / code points ---------------------------

def cps(s):
    return [ord(ch) for ch in s]


def to_str(codepoints):
    return "".join(chr(c) for c in codepoints)


def to_jnode(value):
    """Lower a nested dict/list/str value to the model's JNode tree
    (mapping.md section 2 bijection)."""
    if isinstance(value, str):
        return JNode(0, cps(value), None, None)
    if isinstance(value, (list, tuple)):
        # the encoder serialises a tuple as an array too, so both map to ARRAY
        head = None
        for v in reversed(list(value)):
            n = to_jnode(v)
            n.nxt = head
            head = n
        return JNode(1, [], head, None)
    if isinstance(value, dict):
        head = None
        for k, v in reversed(list(value.items())):
            vn = to_jnode(v)                    # member value: no siblings
            m = JNode(3, cps(k), vn, None)
            m.nxt = head
            head = m
        return JNode(2, [], head, None)
    raise TypeError("value shape outside the JNode bridge: %r" % (value,))


def placeholder_node():
    """Requires-satisfying stand-in node for the paths that never consult the
    value tree (absent / non-encodable): any well-formed JNode."""
    return JNode(0, [], None, None)


# --- oracle: the real patched repo function ------------------------------------

def make_oracle():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            INSTALLED_APPS=["django.contrib.contenttypes",
                            "django.contrib.auth"],
            USE_TZ=False)
    django.setup()
    from django.contrib.admin.utils import display_for_field, display_for_value
    from django.db import models
    return display_for_field, display_for_value, models.JSONField()


# --- differential driver --------------------------------------------------------

class Driver(object):
    def __init__(self):
        self.display_for_field, self.display_for_value, self.field = make_oracle()
        self.checked = 0

    def _fail(self, desc, shadow, real):
        print("DISAGREEMENT on %s:\n  shadow (impl region)       = %r\n"
              "  real (patched repo render) = %r" % (desc, shadow, real))
        return False

    def check_absent(self, empty_s):
        """present=False <-> NOTHING STORED, i.e. the repo value None -- the
        only value on which the repo renders the placeholder (mapping.md
        section 2). A falsy-but-stored value is NOT this case; it goes through
        check_value, which is what makes the three-outcome dispatch visible."""
        self.checked += 1
        shadow_cps = display_structured_value(
            placeholder_node(), cps(empty_s), [], False, True)
        shadow = to_str(shadow_cps)
        real = self.display_for_field(None, self.field, empty_s)
        if shadow != str(real):
            return self._fail("absent value, placeholder=%r" % empty_s,
                              shadow, str(real))
        return True

    def check_value(self, value, empty_s):
        """present=True (anything STORED, falsy included). `encodable` is the
        conjunction the repo actually applies: the value must be truthy (only
        then is it offered to the encoder) AND the encoder must express it."""
        self.checked += 1
        try:
            json.dumps(value)
            dumps_ok = True
        except TypeError:
            dumps_ok = False
        encodable = bool(value) and dumps_ok
        # `content` carries the REAL fallback callee's own output, not str(value):
        # display_for_value has a join arm for list/tuple roots, so the two differ
        # on every sequence-rooted value (mapping.md section 3.2).
        content_s = str(self.display_for_value(value, empty_s))
        if encodable:
            node = to_jnode(value)
            shadow_cps = display_structured_value(
                node, cps(empty_s), cps(content_s), True, True)
            # internal cross-check: the impl region agrees with the pure fold
            if ToSeq(shadow_cps) != interchange_form(node):
                print("INTERNAL: impl region and pure fold disagree on %r"
                      % (value,))
                return False
        else:
            shadow_cps = display_structured_value(
                placeholder_node(), cps(empty_s), cps(content_s), True, False)
            # internal cross-check: the fallback is the identity pass-through
            if ToSeq(shadow_cps) != fallback_form(ToSeq(cps(content_s))):
                print("INTERNAL: impl region and fallback_form disagree on %r"
                      % (value,))
                return False
        shadow = to_str(shadow_cps)
        real = self.display_for_field(value, self.field, empty_s)
        if shadow != str(real):
            return self._fail(
                "value=%r (encodable=%r, placeholder=%r)"
                % (value, encodable, empty_s), shadow, str(real))
        return True


# --- input generation -----------------------------------------------------------

PLACEHOLDERS = ["-", "", "(none)", "EMPTY", "\u00e9\u2022 placeholder",
                "-" * 40]

# string tokens / keys are drawn from the FULL code point range: the token form
# is modelled explicitly (esc_seq / esc_char), so nothing here has to steer
# clear of the escape classes. The alphabet mixes the printable band with one
# representative of every class the interchange alphabet treats specially, and
# rand_token also draws unrestricted code points.
ALPHABET = ("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
            "0123456789 .;:!?-=+_()"
            "\"\\/'<>&"                              # delimiter, escape char
            "\b\t\n\f\r\x00\x01\x1f\x7f"           # two-code-point forms + controls
            "\u00e9\u00ff\u0416\u2022\u2028\uffff"    # non-ASCII BMP
            "\ud800\udfff"                          # lone surrogates
            "\U0001f600\U0010ffff")                 # astral planes


def rand_token(rng):
    n = rng.randint(0, 8)
    out = []
    for _ in range(n):
        if rng.random() < 0.1:
            out.append(chr(rng.randrange(0, 0x110000)))   # any code point
        else:
            out.append(rng.choice(ALPHABET))
    return "".join(out)


def rand_value(rng, depth):
    if depth <= 0:
        return rand_token(rng)
    r = rng.random()
    if r < 0.5:
        return rand_token(rng)
    if r < 0.75:                                 # list
        return [rand_value(rng, depth - 1) for _ in range(rng.randint(0, 4))]
    d = {}                                       # dict (string keys)
    for _ in range(rng.randint(0, 4)):
        d[rand_token(rng) + str(len(d))] = rand_value(rng, depth - 1)
    return d


def rand_nonencodable(rng):
    """A truthy value the real encoder cannot express. Rooted at a dict OR at a
    list/tuple: the sequence roots take the fallback callee's JOIN arm, whose
    text differs from str(value), so they must be generated or the bridge's
    `content` binding is never exercised where it matters."""
    d = {}
    for _ in range(rng.randint(0, 3)):
        d[rand_token(rng) + str(len(d))] = rand_value(rng, rng.randint(0, 2))
    r = rng.random()
    if r < 0.5:
        d[(rand_token(rng), rand_token(rng))] = rand_token(rng)  # tuple key
    elif r < 0.8:
        d["b" + str(len(d))] = b"\x00bytes"      # bytes value
    else:
        d["s" + str(len(d))] = {rng.randint(0, 9)}  # singleton set value
    shape = rng.random()
    if shape < 0.45:
        return d                                  # dict root -> general arm
    payload = [rand_value(rng, rng.randint(0, 2)) for _ in range(rng.randint(0, 2))]
    payload.append(d)
    if shape < 0.55:
        payload.append(b"raw")
    seq = payload if shape < 0.85 else tuple(payload)
    return seq                                    # sequence root -> JOIN arm


def falsy_stored():
    """Values that ARE stored but are themselves falsy. The renderer never
    offers these to the encoder, so they take the fallback arm -- NOT the
    placeholder. Excluding them is what let a three-outcome dispatch pass as a
    two-outcome one, so they are boundary cases here, not out-of-domain."""
    return ["", [], {}, (), 0, 0.0, False]


def boundary_encodable():
    return [
        "a", "ab", "hello world", "JSON", " ", ".", "(x)",
        "a" * 500,                               # long token
        ["x"], ["x", "y", "z"], [""], ["", "a", ""],
        [[]], [{}], [["a"], []],
        {"k": "v"}, {"": ""}, {"k": ""}, {"k": []}, {"k": {}},
        {"a": {"b": "c"}},                       # nested object
        ["a", "b"],                              # flat array
        {"a": ["b", "c"]}, [{"k": "v"}, "tail"],
        {"a": {"b": {"c": {"d": {"e": "f"}}}}},  # deep nesting
        ["a", ["b", ["c", ["d", ["e"]]]]],
        dict(("k%d" % i, str(i)) for i in range(30)),  # many members
        [str(i) for i in range(200)],            # long sibling chain
        {"m": [{"a": ["b", {"c": "d"}]}, "", ["x", {}]]},
        # --- the token form: every escape class, as a VALUE and as a KEY ------
        'a"b', '"', '\\', 'a\\b', '\\"', '"\\"',
        '\b', '\t', '\n', '\f', '\r', 'a\nb', '\t\n\r\b\f',
        '\x00', '\x01', '\x1f', '\x00\x1f', '\x7f', 'a\x7fb',
        '\u00e9', '\u00ff', '\u0416', '\u2022', '\u2028\u2029', '\uffff',
        '\ud800', '\udfff', '\ud800\udc00',           # lone surrogates
        '\U0001f600', '\U0010ffff', 'a\U0001f600b',      # astral planes
        '"' * 40, '\\' * 40, '\x00' * 40,             # long escaping tokens
        ['a"b', 'c\\d'], ['\n', '\t'], [['\u00e9'], ['\U0001f600']],
        {'a"b': 'c\\d'}, {'\n': '\t'}, {'\u00e9': '\U0001f600'},
        {'"': {'\\': ['\x00', '\u2028']}},              # escapes at every depth
        {'k': 'v"w', 'x\\y': ['\u00e9', {'\t': '\ud800'}]},
    ]


def boundary_nonencodable():
    return [
        {("a", "b"): "c"},                       # tuple key -> general arm
        {("a", "b"): "c", "d": "e"},             # tuple key + ordinary member
        {"k": b"raw"},                           # bytes value
        {"k": {7}},                              # singleton set value
        {"outer": {("x",): "y"}},                # nested tuple key
        {'a"b': b"raw"},                         # escaping key, fallback arm
        ['a"b', {("x",): "y"}],                  # escaping token, JOIN arm
        # SEQUENCE-rooted non-encodables: the fallback callee's JOIN arm, whose
        # text is NOT str(value). A dict-rooted-only generator never reaches it.
        [{("x", "y"): "z"}],                     # single element, joined
        ["a", {("x", "y"): "z"}],                # two elements, ", " joined
        [b"raw"],                                # bytes element
        (b"raw", "a"),                           # tuple root
        [{"ok": "v"}, {("x",): "y"}, "tail"],    # mixed, joined
        [[{("x",): "y"}]],                       # nested sequence root
    ]


def main():
    drv = Driver()
    ok = True

    # absent probes across placeholder texts
    for empty_s in PLACEHOLDERS:
        ok = drv.check_absent(empty_s) and ok

    for value in boundary_encodable():
        ok = drv.check_value(value, "-") and ok
    for value in boundary_nonencodable():
        ok = drv.check_value(value, "-") and ok
    # falsy STORED values across every placeholder text: these are present and
    # must render as the fallback text, never as the placeholder.
    for value in falsy_stored():
        for empty_s in PLACEHOLDERS:
            ok = drv.check_value(value, empty_s) and ok

    n_boundary = drv.checked

    # randomized fuzz over the full nested value shapes (pinned seed):
    # ~2% absent probes, ~8% non-encodable, rest structured values -- INCLUDING
    # falsy top-level ones, which are in-domain (present) and exercise the
    # fallback arm. Nothing here forces the top level truthy: doing so would
    # hide the very dispatch outcome the three postconditions distinguish.
    rng = random.Random(SEED)
    for _ in range(N_FUZZ):
        p = rng.random()
        if p < 0.02:
            ok = drv.check_absent(rng.choice(PLACEHOLDERS)) and ok
        elif p < 0.10:
            ok = drv.check_value(rand_nonencodable(rng),
                                 rng.choice(PLACEHOLDERS)) and ok
        elif p < 0.14:
            ok = drv.check_value(rng.choice(falsy_stored()),
                                 rng.choice(PLACEHOLDERS)) and ok
        else:
            value = rand_value(rng, rng.randint(0, 4))
            ok = drv.check_value(value, rng.choice(PLACEHOLDERS)) and ok
        if not ok:
            break

    if not ok:
        print("FAIL after %d inputs" % drv.checked)
        print(json.dumps({"status": "fail", "checked": drv.checked,
                          "seed": SEED}))
        return 1

    print("G-CONF OK: shadow impl == real patched repo rendering on %d inputs"
          " (%d boundary + %d fuzz, seed %d); internal pure-fold cross-checks"
          " hold; 0 disagreements." % (drv.checked, n_boundary, N_FUZZ, SEED))
    print(json.dumps({"status": "pass", "checked": drv.checked,
                      "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
