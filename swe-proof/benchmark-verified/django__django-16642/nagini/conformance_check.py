#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-16642 (nagini).

SHADOW: the impl region of model.py, copied verbatim below with the contract
calls (Requires/Ensures/Invariant/Assert) stripped. PSeq is realized as an
immutable tuple shim and ToSeq materializes a list as a PSeq. The @Pure token
helpers (tok_br .. tok_xz) copy over as plain functions. There are no
@ContractOnly callees in this bundle.

ORACLE: the REAL patched repo code the model models per mapping.md — the
compression-scheme -> content-type resolution inside
`django.http.response.FileResponse.set_headers`. The gate applies patch.diff
to /testbed before this script runs; PYTHONPATH=/testbed makes the patched
module importable. The modeled operation takes the already-guessed
(content_type, encoding) pair as its inputs; its producer,
`mimetypes.guess_type`, is unchanged and NOT part of the model (mapping.md
section 3 / refinement.md section B). To drive the real resolution over
arbitrary Requires-satisfying pairs, the producer is substituted with a
dispatcher returning the pair under test, the real `set_headers` runs, and
the resulting Content-Type header is read back. A batch of end-to-end
boundary cases additionally runs with the REAL producer on real file names,
so the substitution itself is cross-checked.

Type bridge (mapping.md section 2): a str value maps to the List[int] of its
Unicode code points; None (producer found nothing) and the empty str both map
to []. On the way out, `set_headers` stores `resolved or
"application/octet-stream"` into the header, so the expected header for a
shadow output S is `str(S) if S else "application/octet-stream"`; the shadow
output list maps back via chr per code point.

Input domain: the Requires only demand read access to the two lists, so any
pair of code-point lists is Requires-satisfying. Fuzz draws encodings from
the recognised scheme tokens, case/spelling near-misses, empty/None, and
random short tokens; content types are drawn from realistic media types plus
random printable-ASCII strings without CR/LF (header values reject control
characters, and the producer only ever emits ASCII tokens, so this subdomain
is where the header read-back bijection is exact).

>= 1e5 Requires-satisfying inputs: boundary cases + 100000 fuzz pairs.
Pinned fuzz seed: 16642.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only.
"""
import io
import json
import mimetypes
import random
import sys

SEED = 16642
N_FUZZ = 100_000


# --- PSeq shim: immutable sequence, the operations the impl region uses ------

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


# --- pure helpers from model.py used by the impl region, decorators stripped --

def tok_br():
    # "br"
    return PSeq(98, 114)


def tok_bzip2():
    # "bzip2"
    return PSeq(98, 122, 105, 112, 50)


def tok_compress():
    # "compress"
    return PSeq(99, 111, 109, 112, 114, 101, 115, 115)


def tok_gzip():
    # "gzip"
    return PSeq(103, 122, 105, 112)


def tok_xz():
    # "xz"
    return PSeq(120, 122)


# --- the impl region of model.py, verbatim, contract calls stripped -----------

def select_content_type(content_type, encoding):
    enc = ToSeq(encoding)
    if enc == tok_br():
        return [97, 112, 112, 108, 105, 99, 97, 116, 105, 111, 110,
                47, 120, 45, 98, 114, 111, 116, 108, 105]
    if enc == tok_bzip2():
        return [97, 112, 112, 108, 105, 99, 97, 116, 105, 111, 110,
                47, 120, 45, 98, 122, 105, 112]
    if enc == tok_compress():
        return [97, 112, 112, 108, 105, 99, 97, 116, 105, 111, 110,
                47, 120, 45, 99, 111, 109, 112, 114, 101, 115, 115]
    if enc == tok_gzip():
        return [97, 112, 112, 108, 105, 99, 97, 116, 105, 111, 110,
                47, 103, 122, 105, 112]
    if enc == tok_xz():
        return [97, 112, 112, 108, 105, 99, 97, 116, 105, 111, 110,
                47, 120, 45, 120, 122]
    result = []  # type: list
    i = 0
    while i < len(content_type):
        result = result + [content_type[i]]
        i = i + 1
    return result


# --- bridge: str/None <-> List[int] of code points -----------------------------

def to_codepoints(s):
    """str-or-None input carrier -> List[int]; None and '' both mean 'no
    value' and map to the empty list (mapping.md section 2)."""
    if s is None:
        return []
    return [ord(ch) for ch in s]


def cp_to_str(lst):
    return "".join(chr(c) for c in lst)


class _NamedStub:
    """Minimal filelike: only a name, no read/seek/tell, so set_headers goes
    straight to the content-type resolution branch."""

    def __init__(self, name):
        self.name = name


class _Dispatcher:
    """Stand-in for the unchanged producer: returns the pair under test."""

    def __init__(self):
        self.pair = (None, None)

    def __call__(self, _filename, strict=True):
        return self.pair


def real_content_type_header(resp_mod, FileResponse, response, filelike):
    """Run the REAL patched set_headers and read back the Content-Type."""
    response.headers.pop("Content-Type", None)
    response._no_explicit_content_type = True
    response.filename = ""
    response.set_headers(filelike)
    return response.headers.get("Content-Type")


def expected_header_from_shadow(ct_list, enc_list):
    """Shadow result mapped to the header value set_headers would store:
    a falsy resolved type falls back to application/octet-stream."""
    out = cp_to_str(select_content_type(ct_list, enc_list))
    return out if out else "application/octet-stream"


def check_pair(resp_mod, FileResponse, response, dispatcher, ct, enc):
    """One injected (content_type, encoding) pair; error string or None."""
    dispatcher.pair = (ct, enc)
    real = real_content_type_header(resp_mod, FileResponse, response,
                                    _NamedStub("payload.bin"))
    shadow = expected_header_from_shadow(to_codepoints(ct), to_codepoints(enc))
    if real != shadow:
        return ("DISAGREEMENT (injected pair)\n  content_type=%r encoding=%r\n"
                "  shadow=%r\n  real=%r" % (ct, enc, shadow, real))
    return None


def check_filename(resp_mod, FileResponse, response, name):
    """One end-to-end case with the REAL producer on a real file name."""
    ct, enc = mimetypes.guess_type(name)
    real = real_content_type_header(resp_mod, FileResponse, response,
                                    _NamedStub(name))
    shadow = expected_header_from_shadow(to_codepoints(ct), to_codepoints(enc))
    if real != shadow:
        return ("DISAGREEMENT (real producer)\n  filename=%r -> "
                "content_type=%r encoding=%r\n  shadow=%r\n  real=%r"
                % (name, ct, enc, shadow, real))
    return None


ENC_POOL = [
    # the recognised schemes
    "br", "bzip2", "compress", "gzip", "xz",
    # near-misses: case, prefixes, related tokens
    "BR", "Br", "bR", "GZIP", "Gzip", "XZ", "Xz", "BZIP2", "COMPRESS",
    "gz", "bz2", "bzip", "brotli", "z", "Z", "x-gzip", "x-bzip2",
    "deflate", "identity", "zstd", "lzma", "tar", "compres", "compresss",
    "gzip ", " gzip", "br\x00",
    # empty / absent
    "", None,
]

CT_POOL = [
    "text/html", "text/plain", "application/octet-stream", "image/png",
    "application/json", "application/x-tar", "video/mp4",
    "text/html; charset=utf-8", "", None,
]

ASCII = ("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
         "/-.+;= _")


def rand_token(rng, alphabet, max_len):
    return "".join(rng.choice(alphabet) for _ in range(rng.randint(0, max_len)))


def main():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure()
        django.setup()
    from django.http import response as resp_mod
    from django.http import FileResponse

    # One response object, reused; set_headers is re-entered per case.
    response = FileResponse(io.BytesIO(b""))

    checked = 0

    # --- end-to-end boundary cases with the REAL producer ---------------------
    real_names = [
        "test.html.br", "test.html.Z", "test.tar.gz", "test.tar.bz2",
        "test.tar.xz", "test.tar.br", "test.tar.Z", "file.txt", "pic.png",
        "archive.tar", "noext", "data.json.gz", "a.css.br", "movie.mp4",
        "weird.unknownext",
    ]
    for name in real_names:
        err = check_filename(resp_mod, FileResponse, response, name)
        if err:
            print(err)
            return 1
        checked += 1

    # --- injected pairs: producer substituted by a dispatcher -----------------
    dispatcher = _Dispatcher()
    saved_guess = mimetypes.guess_type
    try:
        mimetypes.guess_type = dispatcher

        # boundary grid: every pool encoding x every pool content type
        for enc in ENC_POOL:
            for ct in CT_POOL:
                err = check_pair(resp_mod, FileResponse, response,
                                 dispatcher, ct, enc)
                if err:
                    print(err)
                    return 1
                checked += 1

        # fuzz: pinned seed
        rng = random.Random(SEED)
        enc_alpha = "brzipcomgxs25ZB "
        for _ in range(N_FUZZ):
            r = rng.random()
            if r < 0.35:
                enc = rng.choice(ENC_POOL)
            elif r < 0.7:
                enc = rand_token(rng, enc_alpha, 9)
            else:
                enc = rand_token(rng, ASCII, 12)
            r = rng.random()
            if r < 0.4:
                ct = rng.choice(CT_POOL)
            else:
                ct = rand_token(rng, ASCII, 24)
            err = check_pair(resp_mod, FileResponse, response,
                             dispatcher, ct, enc)
            if err:
                print(err)
                return 1
            checked += 1
    finally:
        mimetypes.guess_type = saved_guess

    print("G-CONF OK: shadow impl == real content-type resolution on %d "
          "inputs (%d real-producer + boundary grid + %d fuzz, seed %d)."
          % (checked, len(real_names), N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
