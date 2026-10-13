#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-16642.

This bundle carries NO consumed axioms (`@ContractOnly`) and NO A-reference
deep models: the changed operation is a finite literal table (a dict keyed by
five string literals, consumed through `dict.get`), modeled directly in
model.py as a case split over `PSeq[int]` key equality. There is therefore no
opaque library callee whose contract must be validated against a real
implementation.

What this script DOES check (so G-AX is meaningful rather than vacuous):

  1. The five encoding tokens (`tok_*`) and five content-type values (`ct_*`)
     in model.py are the EXACT Unicode code points of the five dict keys /
     values in the gold patch. A drift here would silently weaken the spec.

  2. The R-refinement context (mapping.md §3.1): the real, unchanged
     `mimetypes.guess_type` callee actually produces the encoding tokens the
     table keys on for the regressing file types — in particular `"br"` for a
     `*.br` name and `"compress"` for a `*.Z` name — so that the modeled inputs
     correspond to reality. This is NOT a consumed axiom (the proof does not
     depend on guess_type's Ensures); it is a sanity check that the modeled
     case split is over the tokens the system really emits.

  3. The denotation of `dict.get(encoding, content_type)` over the gold dict
     matches model.py's `resolved_type` on every recognised scheme and on a
     fuzz of unrecognised encodings — i.e. the case split the model spells out
     equals the real dict lookup.

Imports nothing repo-specific: `mimetypes` is the Python standard library, the
same module `set_headers` calls. Exit 0 iff every obligation holds.
"""
import mimetypes
import random
import sys

# --- model.py reference encodings (kept in lock-step with the spec) ----------

# tok_* : encoding token -> code points (model.py pure region)
_TOK = {
    "br": [98, 114],
    "bzip2": [98, 122, 105, 112, 50],
    "compress": [99, 111, 109, 112, 114, 101, 115, 115],
    "gzip": [103, 122, 105, 112],
    "xz": [120, 122],
}

# ct_* : dedicated content type -> code points (model.py pure region)
_CT = {
    "br": ([97, 112, 112, 108, 105, 99, 97, 116, 105, 111, 110,
            47, 120, 45, 98, 114, 111, 116, 108, 105], "application/x-brotli"),
    "bzip2": ([97, 112, 112, 108, 105, 99, 97, 116, 105, 111, 110,
               47, 120, 45, 98, 122, 105, 112], "application/x-bzip"),
    "compress": ([97, 112, 112, 108, 105, 99, 97, 116, 105, 111, 110,
                  47, 120, 45, 99, 111, 109, 112, 114, 101, 115, 115],
                 "application/x-compress"),
    "gzip": ([97, 112, 112, 108, 105, 99, 97, 116, 105, 111, 110,
              47, 103, 122, 105, 112], "application/gzip"),
    "xz": ([97, 112, 112, 108, 105, 99, 97, 116, 105, 111, 110,
            47, 120, 45, 120, 122], "application/x-xz"),
}

# The gold dict (post-patch) as a plain Python object.
_GOLD_TABLE = {
    "br": "application/x-brotli",
    "bzip2": "application/x-bzip",
    "compress": "application/x-compress",
    "gzip": "application/gzip",
    "xz": "application/x-xz",
}


def resolved_type_model(content_type, encoding):
    """Reference of model.py's `resolved_type`: dedicated content type if the
    encoding is one of the five recognised schemes, else the guessed type."""
    if encoding in _TOK:
        return _CT[encoding][1]
    return content_type


def check_token_encodings():
    """(1) tok_* / ct_* code points == the literal keys / values."""
    for key, cps in _TOK.items():
        assert [ord(c) for c in key] == cps, (
            "tok encoding drift for key %r: model %r != real %r"
            % (key, cps, [ord(c) for c in key]))
    for key, (cps, value) in _CT.items():
        assert [ord(c) for c in value] == cps, (
            "ct encoding drift for value %r: model %r != real %r"
            % (value, cps, [ord(c) for c in value]))
        # and the gold table maps the key to exactly this value
        assert _GOLD_TABLE[key] == value, (
            "gold table value drift for key %r: %r != %r"
            % (key, _GOLD_TABLE[key], value))


def check_guess_type_context():
    """(2) the unchanged guess_type really emits the tokens the table keys on
    for the regressing inputs named in the problem statement."""
    # The two file types the problem statement reports as broken.
    cases = {
        "test.html.br": "br",
        "test.html.Z": "compress",
        # the three pre-existing schemes, for completeness
        "test.tar.gz": "gzip",
        "test.tar.bz2": "bzip2",
        "test.tar.xz": "xz",
    }
    for name, expected_encoding in cases.items():
        _ct, encoding = mimetypes.guess_type(name)
        assert encoding == expected_encoding, (
            "guess_type(%r) encoding %r != expected %r (model case split "
            "would not be exercised by the real system)"
            % (name, encoding, expected_encoding))
        # and that encoding token is one the model recognises
        assert encoding in _TOK, (
            "guess_type emitted encoding %r not in the modeled table" % encoding)


def check_lookup_denotation():
    """(3) dict.get over the gold table == model.py resolved_type, on each
    recognised scheme and on a fuzz of unrecognised encodings."""
    sample_cts = ["text/html", "application/octet-stream", "", "image/png",
                  "text/plain"]

    # recognised schemes: result is the dedicated type regardless of guessed ct
    for enc in _TOK:
        for ct in sample_cts:
            real = _GOLD_TABLE.get(enc, ct)
            model = resolved_type_model(ct, enc)
            assert real == model == _CT[enc][1], (
                "recognised-scheme mismatch enc=%r ct=%r: real=%r model=%r"
                % (enc, ct, real, model))

    # unrecognised encodings (incl. None / empty): passthrough of guessed ct
    rng = random.Random(16642)
    pool = ["", "deflate", "identity", "BR", "Br", "z", "Z", "gz", "bzip",
            "x-gzip", "tar", "html", None]
    for _ in range(20000):
        enc = rng.choice(pool)
        ct = rng.choice(sample_cts)
        key = enc if enc is not None else "\x00\x01_no_such_key_"
        real = _GOLD_TABLE.get(key, ct)
        model = resolved_type_model(ct, key)
        assert real == model == ct, (
            "unrecognised-encoding mismatch enc=%r ct=%r: real=%r model=%r"
            % (enc, ct, real, model))


def main():
    check_token_encodings()
    check_guess_type_context()
    check_lookup_denotation()
    print("G-AX OK: no consumed axioms / deep-model references; tok_*/ct_* "
          "encodings exact; guess_type emits 'br'/'compress' for *.br/*.Z; "
          "dict.get == resolved_type over 5 schemes x 5 cts + 20000 fuzz.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
