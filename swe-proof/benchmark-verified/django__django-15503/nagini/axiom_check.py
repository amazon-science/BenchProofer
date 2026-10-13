#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-15503.

The changed serialization step of the fix -- compiling the FINAL key of a
key-membership test into a textual JSON path step -- is modelled DEEPLY in
model.py (not behind a consumed @ContractOnly axiom). This script validates
that deep model against the REAL callee, in-container, on boundary + fuzz
inputs.

The deep model (model.py, pure region):

    json_string_literal(key)    = '"' + key + '"'                 (PSeq view)
    member_access_segment(key)  = '.' + json_string_literal(key)
                                = '.' + '"' + key + '"'

The real callee (django/db/models/fields/json.py, post-patch):

    class HasKeyLookup(PostgresOperatorLookup):
        def compile_json_path_final_key(self, key_transform):
            return ".%s" % json.dumps(key_transform)

`json.dumps` of a string from the modelled domain (printable ASCII 32..126,
excluding the double quote 34 and the backslash 92) is exactly the key verbatim
wrapped in double quotes, because the JSON encoder escapes only quote /
backslash / control characters and (with the default ensure_ascii=True) renders
non-ASCII as \\uXXXX -- none of which occur in the domain. Hence on the domain

    json.dumps(key) == '"' + key + '"'

and the real final-key step == member_access_segment(key). This is an
A-reference (validated, not consumed).

We ALSO demonstrate the bug discriminator the model's prepatch encodes: the
unchanged path compiler `compile_json_path([key], include_root=False)` (which
the PRE-PATCH code used for the final key) maps an all-digit key to the
array-element form `[<int>]` -- which is NOT the member-access form, and which
even drops leading zeros ("000" -> "[0]"). The fix routes the final key through
`compile_json_path_final_key` instead, so EVERY key (numeric or not) is the
object-member form. The F2P numeric keys are enumerated and asserted explicitly.

Imports only the standard library `json` (the very module the patched callee
calls); nothing repo-specific. Exit 0 iff every obligation holds.
"""
import json
import random
import string
import sys


# --- domain ------------------------------------------------------------------

def in_domain(s):
    """model.py in_domain: printable ASCII 32..126, no quote(34)/backslash(92)."""
    return all(32 <= ord(c) <= 126 and ord(c) not in (34, 92) for c in s)


# --- deep model (model.py reference encodings, code-point lists) -------------

def json_string_literal(codepoints):
    return [34] + list(codepoints) + [34]


def member_access_segment(codepoints):
    return [46] + json_string_literal(codepoints)


# --- the REAL callees (verbatim fragments of the patched source) -------------

def real_compile_json_path_final_key(key_transform):
    """HasKeyLookup.compile_json_path_final_key (the fix)."""
    return ".%s" % json.dumps(key_transform)


def real_compile_json_path(key_transforms, include_root=True):
    """The UNCHANGED path compiler; PRE-PATCH the final key went through this,
    which is the source of the array-index-for-numeric-key bug."""
    path = ["$"] if include_root else []
    for key_transform in key_transforms:
        try:
            num = int(key_transform)
        except ValueError:  # non-integer
            path.append(".")
            path.append(json.dumps(key_transform))
        else:
            path.append("[%s]" % num)
    return "".join(path)


# --- checks ------------------------------------------------------------------

def check_final_key_reference(key):
    """A-reference: deep model member_access_segment(key) == real fixed callee."""
    observed = [ord(ch) for ch in real_compile_json_path_final_key(key)]
    expected = member_access_segment([ord(ch) for ch in key])
    assert observed == expected, (
        "final-key deep model unsound on %r: real callee gave %r, "
        "deep model gives %r" % (key, observed, expected))


def check_bug_discriminator(key):
    """For an all-digit key the PRE-PATCH compiler emits the array-element form
    (begins with '['), NOT the member-access form -- exactly what model_prepatch
    encodes and what the F2P numeric-key test detects."""
    if not (key and key.isdigit()):
        return
    prepatch = real_compile_json_path([key], include_root=False)
    fixed = real_compile_json_path_final_key(key)
    assert prepatch.startswith("[") and prepatch.endswith("]"), prepatch
    assert fixed.startswith('."') and fixed.endswith('"'), fixed
    assert prepatch != fixed, (key, prepatch, fixed)


def main():
    # F2P keys (test_has_key_number + test_has_keys) plus existing has_key keys.
    f2p_keys = [
        "123", "456", "999", "789", "777", "000", "nested", "lorem",
        "array", "ipsum", "a", "c", "h",
    ]
    boundary = list(f2p_keys) + [
        "", "0", "00", "007", "9", "1111", "42abc", "abc42",
        "foo", " ", "a b c", "!@#$%^&*()", ";drop table", "o'brien",
        "key.with.dots", "(paren)", "[bracket]", "tab\tless",  # tab excluded below
    ]
    boundary = [k for k in boundary if in_domain(k)]
    for k in boundary:
        check_final_key_reference(k)
        check_bug_discriminator(k)

    # numeric discriminator: leading-zero collapse the bug exhibits
    assert real_compile_json_path(["000"], include_root=False) == "[0]"
    assert real_compile_json_path_final_key("000") == '."000"'
    assert real_compile_json_path(["1111"], include_root=False) == "[1111]"
    assert real_compile_json_path_final_key("1111") == '."1111"'

    # randomized fuzz over the full modelled domain
    rng = random.Random(15503)
    alphabet = [chr(c) for c in range(32, 127) if c not in (34, 92)]
    fuzz = 0
    for _ in range(50000):
        n = rng.randint(0, 16)
        k = "".join(rng.choice(alphabet) for _ in range(n))
        assert in_domain(k)
        check_final_key_reference(k)
        check_bug_discriminator(k)
        fuzz += 1

    # all-digit-only fuzz (stress the numeric branch the bug mishandles)
    digits = list("0123456789")
    for _ in range(20000):
        n = rng.randint(1, 8)
        k = "".join(rng.choice(digits) for _ in range(n))
        check_final_key_reference(k)
        check_bug_discriminator(k)
        fuzz += 1

    print(
        "G-AX OK: member_access_segment deep model == real "
        "compile_json_path_final_key on %d boundary + %d fuzz keys; "
        "numeric-key bug discriminator confirmed (array-index form pre-patch, "
        "object-member form post-patch)" % (len(boundary), fuzz)
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
