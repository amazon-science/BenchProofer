#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-15103 (nagini).

SHADOW: the impl region of model.py's ``build_json_script``, copied verbatim
below with the contract calls (Requires/Ensures/Invariant/Assert) stripped.
The @Pure helpers (``tag_open_with_id`` / ``attr_close_and_type`` /
``tag_open_no_id`` / ``tag_close`` / ``prefix_with_id``) copy over as plain
functions on top of a small immutable-tuple PSeq shim (the impl assigns
``prefix_a = prefix_with_id(element_id)`` and ``prefix_b = tag_open_no_id()``,
so the shim must support construction, concatenation and ToSeq). There are no
@ContractOnly callees in this bundle.

ORACLE: the REAL patched repo function the model models per mapping.md --
``django.utils.html.json_script(value, element_id)`` (the gate applies
patch.diff to /testbed before this script runs; this script does NOT apply
any patch itself).

Type bridge (mapping.md section 2):
  * the model's ``payload: List[int]`` is the code-point list of the
    ALREADY-serialized, script-escaped payload string; that producing step is
    an unchanged callee, so the bridge computes it with the same unchanged
    repo helpers (``json.dumps(value, cls=DjangoJSONEncoder)`` +
    ``str.translate`` over the repo's escape table) and hands the resulting
    code points to the shadow while handing the original ``value`` to the
    oracle.
  * ``element_id: Optional[List[int]]`` bridges ``None`` <-> absent, and a
    ``str`` <-> its code-point list. Per the documented refinement domain
    (mapping.md section 2, refinement.md), identifier tokens are restricted to
    HTML-special-free characters (letters, digits, ``-``, ``_``, ``.``,
    ``:``), where attribute interpolation is the identity on characters.
  * the oracle's SafeString return bridges to its code points via ``str``.

Input domain: the precondition demands only readable lists (plus the
termination obligation, vacuous at runtime), so every bridged (value, id)
pair is Requires-satisfying. Generation stresses the decision boundary --
absent id vs empty id vs present id -- and payload content exercising the
script-escape class (``<``, ``>``, ``&``), quotes, whitespace, unicode, and
assorted JSON value shapes.

>= 1e5 Requires-satisfying inputs: boundary grid + 100000 fuzz cases.
Pinned fuzz seed: 151030.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib + the repo under test only.
"""
import json
import random
import sys

SEED = 151030
N_FUZZ = 100000


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

    def __add__(self, other):
        return PSeq._wrap(self._t + other._t)

    def take(self, n):
        return PSeq._wrap(self._t[:n])

    def drop(self, n):
        return PSeq._wrap(self._t[n:])

    def __len__(self):
        return len(self._t)

    def __getitem__(self, i):
        return self._t[i]

    def __eq__(self, other):
        return isinstance(other, PSeq) and self._t == other._t

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self._t)


def ToSeq(lst):
    return PSeq._wrap(lst)


# --- pure helpers from model.py, contracts stripped ---------------------------

def tag_open_with_id():
    # '<script id="'
    return PSeq(60, 115, 99, 114, 105, 112, 116, 32, 105, 100, 61, 34)


def attr_close_and_type():
    # '" type="application/json">'
    return PSeq(34, 32, 116, 121, 112, 101, 61, 34, 97, 112, 112, 108,
                105, 99, 97, 116, 105, 111, 110, 47, 106, 115, 111, 110, 34, 62)


def tag_open_no_id():
    # '<script type="application/json">'
    return PSeq(60, 115, 99, 114, 105, 112, 116, 32, 116, 121, 112, 101,
                61, 34, 97, 112, 112, 108, 105, 99, 97, 116, 105, 111, 110,
                47, 106, 115, 111, 110, 34, 62)


def tag_close():
    # '</script>'
    return PSeq(60, 47, 115, 99, 114, 105, 112, 116, 62)


def prefix_with_id(ident):
    """The opening-tag prefix WHEN an identifier is present: the id-bearing
    opening tag carries the identifier as an id attribute, then the media-type
    attribute."""
    return tag_open_with_id() + ToSeq(ident) + attr_close_and_type()


# --- the impl region of model.py, verbatim, contract calls stripped -----------

def build_json_script(payload, element_id):
    if element_id is not None and len(element_id) > 0:
        # opening tag carrying the identifier, then the media-type attribute
        result = [60, 115, 99, 114, 105, 112, 116, 32, 105, 100, 61, 34]
        i = 0
        while i < len(element_id):
            result.append(element_id[i])
            i = i + 1
        result = result + [34, 32, 116, 121, 112, 101, 61, 34, 97, 112, 112,
                           108, 105, 99, 97, 116, 105, 111, 110, 47, 106, 115,
                           111, 110, 34, 62]
        prefix_a = prefix_with_id(element_id)
        # append the payload, then the closing tag
        j = 0
        while j < len(payload):
            result.append(payload[j])
            j = j + 1
        result = result + [60, 47, 115, 99, 114, 105, 112, 116, 62]
        return result
    # opening tag carrying ONLY the media-type attribute (no id attribute)
    result = [60, 115, 99, 114, 105, 112, 116, 32, 116, 121, 112, 101,
              61, 34, 97, 112, 112, 108, 105, 99, 97, 116, 105, 111, 110,
              47, 106, 115, 111, 110, 34, 62]
    prefix_b = tag_open_no_id()
    # append the payload, then the closing tag
    k = 0
    while k < len(payload):
        result.append(payload[k])
        k = k + 1
    result = result + [60, 47, 115, 99, 114, 105, 112, 116, 62]
    return result


# --- oracle setup: the real patched repo function ------------------------------

import django
from django.conf import settings

if not settings.configured:
    settings.configure(USE_I18N=False)
django.setup()

from django.core.serializers.json import DjangoJSONEncoder  # noqa: E402
from django.utils.html import _json_script_escapes, json_script  # noqa: E402


def real_payload(value):
    """The already-serialized, script-escaped payload string the wrapped
    element carries -- produced by the same UNCHANGED repo helpers the real
    function uses upstream of the modeled assembly (mapping.md section 2)."""
    return json.dumps(value, cls=DjangoJSONEncoder).translate(_json_script_escapes)


def check(value, element_id_str):
    """Run shadow and oracle on one (value, identifier) pair; return an error
    string on disagreement, else None."""
    payload = [ord(c) for c in real_payload(value)]
    eid = None if element_id_str is None else [ord(c) for c in element_id_str]
    shadow = build_json_script(payload, eid)
    if element_id_str is None:
        observed_str = json_script(value)
    else:
        observed_str = json_script(value, element_id_str)
    real = [ord(c) for c in str(observed_str)]
    if shadow != real:
        return ("DISAGREEMENT on value=%r element_id=%r:\n"
                "  shadow (impl region) = %r\n"
                "  real (patched repo function) = %r"
                % (value, element_id_str,
                   "".join(chr(c) for c in shadow), str(observed_str)))
    return None


# --- input generation -----------------------------------------------------------

# identifier alphabet: HTML-special-free tokens (the documented refinement
# domain, where attribute interpolation is the identity on characters)
ID_ALPHABET = ("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
               "0123456789-_.:")

# payload-content alphabet: exercises the script-escape class, quotes,
# whitespace/control, ordinary ASCII and non-ASCII text
STR_ALPHABET = list("<>&\"'\\/ \t\n\r={}[]:,ampscript0123456789") + \
    ["\u00e9", "\u2022", "\u00a0", "\U0001F600"]


def rand_string(rng, max_len=20):
    n = rng.randint(0, max_len)
    return "".join(rng.choice(STR_ALPHABET) for _ in range(n))


def rand_value(rng, depth=0):
    """A random JSON-serializable value."""
    kinds = ["str", "int", "float", "bool", "none"]
    if depth < 2:
        kinds += ["list", "dict"]
    kind = rng.choice(kinds)
    if kind == "str":
        return rand_string(rng)
    if kind == "int":
        return rng.randint(-10**6, 10**6)
    if kind == "float":
        return rng.randint(-10**6, 10**6) / 128.0
    if kind == "bool":
        return rng.random() < 0.5
    if kind == "none":
        return None
    if kind == "list":
        return [rand_value(rng, depth + 1) for _ in range(rng.randint(0, 4))]
    return {rand_string(rng, 8): rand_value(rng, depth + 1)
            for _ in range(rng.randint(0, 4))}


def rand_id(rng):
    """A random identifier from the bridged domain: absent, empty (treated as
    absent), or a present HTML-special-free token."""
    choice = rng.randint(0, 3)
    if choice == 0:
        return None
    if choice == 1:
        return ""
    m = rng.randint(1, 16)
    return "".join(rng.choice(ID_ALPHABET) for _ in range(m))


def boundary_grid():
    values = [
        {}, [], "", "x", 0, -1, 1, 2**53, True, False, None, 0.5, -0.0,
        {"key": "value"},
        {"a": "<script>test&ing</script>"},
        "&<>", "a<b>&", "</script>",
        {"a": "testing\r\njson 'string\" <b>escaping</b>"},
        ["<", ">", "&", "plain"],
        {"nested": {"deep": ["<", {"x": "&"}]}},
        "quotes \" and ' apostrophe",
        "unicode \u00e9\u2022\u00a0\U0001F600",
        "line\u2028sep\u2029para",
    ]
    ids = [None, "", "test_id", "x", "a", "ID-42", "_priv", "a.b:c",
           "0start", "-lead", "a" * 64]
    return [(v, e) for v in values for e in ids]


def main():
    checked = 0

    for value, eid in boundary_grid():
        err = check(value, eid)
        if err:
            print(err)
            return 1
        checked += 1

    rng = random.Random(SEED)
    for _ in range(N_FUZZ):
        err = check(rand_value(rng), rand_id(rng))
        if err:
            print(err)
            return 1
        checked += 1

    print("G-CONF OK: shadow impl == real patched repo function on %d inputs "
          "(boundary grid + %d fuzz, seed %d); 0 disagreements."
          % (checked, N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
