#!/usr/bin/env python3
r"""G-CONF differential conformance check for django__django-13512 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region transliterated
              to Python over the *real* repo type (`str`), via the mapping.md
              bijection (`List Char` <-> `str`, `Char.ofNat (ord ch)` <-> ch).
              `serializeStringValue text = '"' + body + '"'` where `body` is the
              per-code-point fold `jsonEscapedSeq`. There are NO A-tagged ops in
              the computed output (no consumed axioms), so the shadow is pure
              R/I.
  * ORACLE  — `patch.diff`'s behaviour: the patched
              `django.forms.JSONField.prepare_value` applied at base_commit (the
              real correctness oracle, G-RESOLVE), for `str` leaf inputs.

They must agree on every input. In addition, we confirm that the modeled scope
is faithful end-to-end: for CONTAINER inputs (dict/list with str leaves) the
patched `prepare_value` equals the same container serialized with the shadow's
string-leaf rule (i.e. the only change vs pre-patch is the string-leaf
escaping the shadow models), so nothing outside the modeled string-leaf
renderer moved.

Exit 0 iff zero disagreements; any disagreement is a mechanical R/I-fidelity
counterexample.

Runs in-container (the prebuilt SWE-Bench instance image), stdlib + django.
The fuzz seed is pinned (mapping.md §4) for a deterministic verdict.
"""
import json
import os
import random
import sys

SEED = 13512
N_FUZZ = 100_000

_SHORT = {
    0x22: '\\"',
    0x5c: '\\\\',
    0x08: '\\b',
    0x09: '\\t',
    0x0a: '\\n',
    0x0c: '\\f',
    0x0d: '\\r',
}


# --- the R/I shadow: Solution.lean jsonChar/jsonEscapedSeq, transliterated ---
def json_char(c):
    v = ord(c)
    if v in _SHORT:
        return _SHORT[v]
    if v < 0x20:
        return '\\u%04x' % v
    return c


def shadow_serialize_str(text):
    """serializeStringValue (text.toList) transliterated to str: quote + the
    per-code-point fold body + quote. The backward `while` fold of
    serializeStringValue computes exactly this left-to-right concatenation."""
    return '"' + "".join(json_char(ch) for ch in text) + '"'


def _setup_django():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            DEBUG=True,
            USE_I18N=False,
            INSTALLED_APPS=[],
            DATABASES={},
        )
    django.setup()


def make_oracle():
    """patch.diff's behaviour: the patched JSONField.prepare_value() (uses
    json.dumps(value, ensure_ascii=False, cls=self.encoder))."""
    from django.forms import JSONField
    field = JSONField()
    return field.prepare_value


def fuzz_str_inputs(n, rng):
    specials = ['"', '\\', '/', '\b', '\t', '\n', '\f', '\r',
                '\x00', '\x01', '\x1f', '\x7f', '\x80', '\xa0']
    nonascii = ['中', '国', '你', '好', '，', '世', '界',
                '\U0001f600', '\U0001f431', 'jaźń', 'é', '•']
    ordinary = list("aZ0 ;#x39271{}[]:,") + ['~', '!', '@']
    alphabet = specials + nonascii + ordinary
    pool = list(range(0x00, 0x80)) + [0x7f, 0x80, 0xa0, 0x2022, 0x4e2d,
                                      0x4f60, 0xff0c, 0xd7ff, 0xe000,
                                      0xfffd, 0x10000, 0x1f600, 0x10ffff]
    # boundary cases first
    yield ""
    yield "foo"
    yield "你好，世界"
    yield "你好 世界"
    yield "😀🐱"
    yield "jaźń"
    yield "Joe's \"quoted\" path\\back"
    yield "line\nbreak\ttab"
    yield "mix 中a国b😀c"
    for c in specials + nonascii:
        yield c
        yield c + c
    yield "".join(chr(i) for i in range(0x20))
    for _ in range(n):
        k = rng.randint(0, 24)
        chars = []
        for _ in range(k):
            if rng.random() < 0.5:
                chars.append(rng.choice(alphabet))
            else:
                chars.append(chr(rng.choice(pool)))
        yield "".join(chars)


def main():
    rng = random.Random(SEED)
    try:
        _setup_django()
        oracle = make_oracle()
    except Exception as e:  # pragma: no cover - environment guard
        print("G-CONF ERROR: could not load patched django oracle: %r" % e)
        return 2

    disagreements = []
    count = 0
    for s in fuzz_str_inputs(N_FUZZ, rng):
        count += 1
        shadow = shadow_serialize_str(s)
        orc = oracle(s)
        if shadow != orc:
            disagreements.append((s, shadow, orc))
            if len(disagreements) >= 5:
                break

    # --- container-framing invariance: the only change vs the rest of the
    #     value is the string-leaf escaping the shadow models. Build each
    #     container with the shadow's string rule and compare to the patched
    #     oracle. ---------------------------------------------------------
    def shadow_value(v):
        if isinstance(v, str):
            return shadow_serialize_str(v)
        if isinstance(v, dict):
            items = ", ".join("%s: %s" % (shadow_value(str(k)) if isinstance(k, str)
                                          else json.dumps(k, ensure_ascii=False),
                                          shadow_value(val))
                              for k, val in v.items())
            return "{" + items + "}"
        if isinstance(v, list):
            return "[" + ", ".join(shadow_value(x) for x in v) + "]"
        return json.dumps(v, ensure_ascii=False)

    containers = [
        {'a': '你好 世界'},
        {'a': {'b': 'c'}},
        ['a', 'b'],
        ["你好，世界", "jaźń"],
        {'a': '😀🐱'},
        {'k': ['中', '国', 1, True, None]},
        [],
        {},
        {'x': 'plain', 'y': 'naïve'},
    ]
    for v in containers:
        count += 1
        shadow = shadow_value(v)
        orc = oracle(v)
        if shadow != orc:
            disagreements.append((v, shadow, orc))
            if len(disagreements) >= 5:
                break

    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for s, sh, orc in disagreements:
            print("  input=%r shadow=%r oracle=%r" % (s, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of serializeStringValue agrees with "
          "patch.diff (patched prepare_value) on %d inputs (seed=%d), "
          "0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
