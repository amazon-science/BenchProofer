#!/usr/bin/env python3
"""G-CONF differential conformance check for psf__requests-5414 (nagini).

SHADOW: the impl region of model.py, copied VERBATIM below (all contract
calls live in the pre/post-condition regions, so nothing had to be stripped
inside the impl region), with the one @Pure helper (`is_invalid_leading`)
copied over as a plain function. The one @ContractOnly callee
(`encode_label`) is realized by calling the REAL unchanged repo callee it
abstracts — `PreparedRequest._get_idna_encoded_host` — on the concrete host
of the current input, mapping its rejection channel (UnicodeError) onto the
model's `InvalidLocator` (mapping.md sec. 3.1). The carriers are a List[int]
of code points plus two booleans; no PSeq shim is needed.

ORACLE: the REAL patched repo function the model models per mapping.md —
the host-validation slice of `requests.models.PreparedRequest.prepare_url`.
The gate applies patch.diff to /testbed before this script runs and sets
PYTHONPATH=/testbed, so the patched routine imports directly. Each input
host is wrapped into a URL and fed to `prepare_url`; the slice's verdict is
the observable the model pins: normal completion <-> accept, InvalidURL <->
reject.

Driving the slice: the URL scheme is chosen ('httpq') so that the whole
preparation path still runs (the routine only short-circuits schemes that do
not begin with 'http'), while the underlying URL parser treats the scheme as
unknown and therefore does NOT pre-normalize the host (no lowercasing, no
label encoding) — the slice receives the host byte-for-byte. Inputs are
admitted only when the parser round-trips the host exactly and the host is
non-empty, which guarantees (a) the slice is reached (the earlier empty-host
rejection cannot fire — matching the model precondition len(host) > 0) and
(b) no other rejection source is in play on the oracle path.

Type bridge (mapping.md sec. 2):
  * host: str <-> List[int] of Unicode code points via ord() per position.
  * host_is_ascii: the verdict of the real UNCHANGED predicate
    `requests._internal_utils.unicode_is_ascii(host)` (an R-refinement, so
    on the real side the bit is determined by the host, never free).
  * encodable: the observation of the real UNCHANGED encoder
    `PreparedRequest._get_idna_encoded_host(host)` — True iff it returns
    normally, False iff it signals UnicodeError. Only meaningful on the
    non-ASCII branch (the only branch that consults it); on the ASCII branch
    the shadow never reads it and it is fixed to True.
  * InvalidLocator <-> requests.exceptions.InvalidURL: only the
    raised/not-raised control flow is observed.

Input domain (Requires-satisfying): non-empty hosts that the URL parser
round-trips exactly. Boundary cases enumerate the leading-code-point
decision table (leading '*' / '.' / ordinary, ASCII and non-ASCII, encodable
and not) including the repo test-suite's internationalised fixtures; fuzz
draws random hosts over an ASCII pool weighted toward the two screened
leading code points plus a non-ASCII pool (~40% of draws contain a
non-ASCII code point, exercising the encoder-deferral branch).

>= 1e5 Requires-satisfying inputs: boundary cases + fuzz until 100000
checked inputs. Pinned fuzz seed: 5414.

Exit 0 iff zero disagreements; on disagreement prints the input and both
verdicts and exits 1. stdlib only.
"""
import json
import random
import sys

SEED = 5414
N_TARGET = 100_000


class InvalidLocator(Exception):
    """Stand-in rejection, as in model.py (only raise/no-raise observed)."""
    pass


# --- bridge state for the @ContractOnly callee --------------------------------

_REAL_ENCODE = None    # the real unchanged encoder callee (bound in main)
_CURRENT_HOST = None   # concrete host str of the input under check


def encode_label(encodable):
    """@ContractOnly callee realized by the REAL repo function: run the real
    unchanged encoder on the concrete host of the current input. Normal
    completion <-> the label encodes; the encoder's rejection channel
    (UnicodeError) maps onto InvalidLocator, exactly the axiom's two
    observable outcomes. `encodable` is the same observation lifted to a
    boolean by the driver, so it is not consulted here."""
    try:
        _REAL_ENCODE(_CURRENT_HOST)
    except UnicodeError:
        raise InvalidLocator()


# --- @Pure helper from model.py, decorator stripped ----------------------------

def is_invalid_leading(c):
    """A single leading code point cannot begin a valid label iff it is
    code point 42 or code point 46."""
    return c == 42 or c == 46


# --- the impl region of model.py, verbatim --------------------------------------

def screen_host(host, host_is_ascii, encodable):
    if not host_is_ascii:
        encode_label(encodable)
    elif is_invalid_leading(host[0]):
        raise InvalidLocator()
    # impl-end (verbatim copy ends here)


# --- driver ---------------------------------------------------------------------

# Scheme that keeps the parser from pre-normalizing the host while still
# running the full preparation path (see module docstring).
SCHEME = "httpq"
PATH = "/pq"


def boundary_hosts():
    """Leading-code-point decision table + repo internationalised fixtures."""
    ascii_hosts = [
        "example.com", ".example.com", "*.example.com", "*", ".",
        "*.", ".*", "..", "**", "a", "a.", "a*", "*a", ".a",
        "localhost", "1.2.3.4", "a..b", "xn--.de", "foo.", "-x.com",
        "a-b.c", "A.B", "0", "sub.domain.example.com",
    ]
    non_ascii_hosts = [
        # encodable internationalised fixtures (repo test-suite oracle set)
        "straße.de", "Königsgäßchen.de", "ジェーピーニック.jp",
        "ドメイン.テスト", "مثال.إختبار", "παράδειγμα.δοκιμή", "例え.テスト",
        # not-encodable shapes
        "☃.net", ".straße.de", "straße..de", "*ü.com", "xn--stra-yna..de",
        # leading screened code points on the non-ASCII branch (screen must
        # NOT apply there; verdict comes from the encoder)
        ".ü", "*ü", "ü", "aß.de", "ü.example.com",
        "a" * 80 + "ß.de",
    ]
    return ascii_hosts + non_ascii_hosts


ASCII_POOL = list("abcdefghijklmnopqrstuvwxyz"
                  "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
                  "0123456789-_.*")
LEADING_POOL = ["*", ".", "a", "z", "A", "0", "-", "_", "x", "9"]
NON_ASCII_POOL = list("àáâãäåçèéêëìíîïñòóôõöùúûüýÿ"
                      "αβγδεζηθικλμνξοπρστυφχψω"
                      "абвгдежзийклмнопрстуфхцч"
                      "ぁあぃいうえおかきくけこ"
                      "مثالدومين") + ["☃", "ß"]


def rand_host(rng):
    n = rng.randint(1, 18)
    non_ascii = rng.random() < 0.40
    chars = []
    # weight the first position toward the screened leading code points
    r = rng.random()
    if r < 0.25:
        chars.append("*")
    elif r < 0.50:
        chars.append(".")
    elif non_ascii and r < 0.62:
        chars.append(rng.choice(NON_ASCII_POOL))
    else:
        chars.append(rng.choice(LEADING_POOL))
    for _ in range(n - 1):
        if non_ascii and rng.random() < 0.30:
            chars.append(rng.choice(NON_ASCII_POOL))
        else:
            chars.append(rng.choice(ASCII_POOL))
    if non_ascii and all(ord(c) < 128 for c in chars):
        chars.append(rng.choice(NON_ASCII_POOL))
    return "".join(chars)


def main():
    global _REAL_ENCODE, _CURRENT_HOST
    # REAL patched repo (PYTHONPATH=/testbed, gold patch applied by the gate)
    from urllib3.util import parse_url
    from requests.models import PreparedRequest
    from requests.exceptions import InvalidURL
    from requests._internal_utils import unicode_is_ascii

    _REAL_ENCODE = PreparedRequest._get_idna_encoded_host

    def check_host(host):
        """Returns 'skip', 'ok', or an error string."""
        global _CURRENT_HOST
        url = SCHEME + "://" + host + PATH
        # admissibility: the parser must deliver this exact non-empty host to
        # the slice (otherwise the input is outside the modeled domain)
        try:
            parsed = parse_url(url)
        except Exception:
            return "skip"
        if not host or parsed.host != host:
            return "skip"
        # bridge: the two abstracted callee verdicts, from the real callees
        host_is_ascii = bool(unicode_is_ascii(host))
        if host_is_ascii:
            encodable = True   # not consulted on this branch
        else:
            try:
                _REAL_ENCODE(host)
                encodable = True
            except UnicodeError:
                encodable = False
        # shadow: verbatim impl region over the model carriers
        _CURRENT_HOST = host
        cps = [ord(c) for c in host]
        try:
            screen_host(cps, host_is_ascii, encodable)
            shadow = "accept"
        except InvalidLocator:
            shadow = "reject"
        # oracle: the real patched preparation routine
        pr = PreparedRequest()
        try:
            pr.prepare_url(url, None)
            real = "accept"
        except InvalidURL:
            real = "reject"
        except Exception as exc:
            real = "other:%s" % type(exc).__name__
        if shadow != real:
            return ("DISAGREEMENT\n"
                    "  host=%r host_is_ascii=%r encodable=%r\n"
                    "  shadow=%s\n  real=%s"
                    % (host, host_is_ascii, encodable, shadow, real))
        return "ok"

    checked = 0
    n_boundary = 0
    for host in boundary_hosts():
        res = check_host(host)
        if res == "skip":
            continue
        if res != "ok":
            print(res)
            return 1
        checked += 1
        n_boundary += 1

    rng = random.Random(SEED)
    draws = 0
    max_draws = 400_000
    while checked < N_TARGET + n_boundary and draws < max_draws:
        draws += 1
        res = check_host(rand_host(rng))
        if res == "skip":
            continue
        if res != "ok":
            print(res)
            return 1
        checked += 1

    if checked < N_TARGET:
        print("ERROR: only %d checked inputs after %d draws (target %d)"
              % (checked, draws, N_TARGET))
        return 1

    print("G-CONF OK: shadow (verbatim impl region) == real patched "
          "prepare_url host slice on %d inputs (%d boundary + %d fuzz, "
          "seed %d), 0 disagreements."
          % (checked, n_boundary, checked - n_boundary, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region; "
                                "@ContractOnly callee bound to the real "
                                "unchanged encoder)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
