#!/usr/bin/env python3
"""G-CONF differential conformance check for psf__requests-1142 (nagini).

SHADOW: the impl region of model.py, copied VERBATIM below (the impl region
contains no Requires/Ensures/Invariant/Assert calls, so nothing had to be
stripped), with the three @Pure helpers (`size_header`, `method_get`,
`method_head`) copied over as plain functions. There are no @ContractOnly
callees and no PSeq usage in this bundle; the carriers are a plain
Dict[int, int] header map, an int method token, and four scalar body
observations, so no sequence shim is needed.

ORACLE: the REAL patched repo function the model models per mapping.md --
`requests.models.PreparedRequest.prepare_content_length(self, body)`. The
gate applies patch.diff to /testbed before this script runs and sets
PYTHONPATH=/testbed, so the patched function imports directly. Per the
velvet/lean siblings' driver shape, a fresh PreparedRequest is built per
input with `pr.headers = CaseInsensitiveDict()` (optionally pre-seeded with
unrelated entries to exercise the whole-map frame) and `pr.method` set to
the verb string, then `pr.prepare_content_length(body)` is called.

Type bridge (mapping.md section 2):
  * headers: the model's Dict[int, int] maps a header NAME to an int token
    and the announced size to the underlying int. Bridge: the size header's
    key token corresponds to the size header name in the real map; presence
    is compared via membership, and the value via int(real_value) ==
    shadow_value (str is injective on the announced non-negative ints).
    Pre-seeded unrelated headers get distinct tokens/names on both sides and
    must survive unchanged (the frame clause of the postcondition).
  * method: the int token maps method_get() <-> 'GET', method_head() <->
    'HEAD', and any other token <-> some other (upper-cased) verb.
  * body observations: `seekable`/`stream_len` are realized as an io.BytesIO
    of size stream_len (has seek+tell; tell after seek-to-end measures the
    size); `body_present`/`body_len` as a bytes object of length body_len
    (no seek/tell); the bodyless case as None. The model precondition
    `seekable => body_present` holds by construction (a BytesIO is not None).

Input domain (Requires-satisfying): the size header absent from the initial
map, seekable => body_present, arbitrary method token, non-negative sizes
(real sizes are lengths/positions, hence >= 0). Boundary cases enumerate the
full decision table over GET / HEAD / payload-carrying verbs x the three
body shapes (including empty bodies and the F2P's bodyless GET/HEAD rows);
fuzz draws random shapes, sizes, verbs, and pre-seeded unrelated headers.

>= 1e5 Requires-satisfying inputs: boundary cases + 100000 fuzz draws.
Pinned fuzz seed: 1142.

Exit 0 iff zero disagreements; on disagreement prints the input and both
post-states and exits 1. stdlib only.
"""
import io
import json
import random
import sys

SEED = 1142
N_FUZZ = 100_000


# --- pure helpers from model.py, @Pure decorators stripped ---------------------

def size_header():
    # The header-name token of the body-size header. Its presence as a key in
    # the header map models "the body-size header is announced".
    return 0


def method_get():
    # Identity token of the read-only retrieval method (a payload-less method).
    return 1


def method_head():
    # Identity token of the headers-only method (a payload-less method).
    return 2


# --- the impl region of model.py, verbatim (no contract calls inside) ----------

def announce_body_size(headers, method, seekable, stream_len,
                       body_present, body_len):
    if seekable:
        headers[size_header()] = stream_len
    elif body_present:
        headers[size_header()] = body_len
    elif method != method_get() and method != method_head():
        headers[size_header()] = 0
    # impl-end (verbatim copy ends here)


# --- bridge: model tokens <-> real repo values ----------------------------------

SIZE_HEADER_NAME = "Content-Length"

# method token <-> verb string; tokens other than 1/2 are payload-carrying.
TOKEN_TO_VERB = {
    1: "GET",
    2: "HEAD",
    3: "POST",
    4: "PUT",
    5: "DELETE",
    6: "PATCH",
    7: "OPTIONS",
}

# Unrelated pre-existing headers: token -> (name, value-int). Distinct from
# the size header's token/name; used to exercise the whole-map frame.
EXTRA_HEADERS = {
    10: ("Accept", 111),
    11: ("X-Custom", 222),
    12: ("User-Agent", 333),
}


def make_body(seekable, stream_len, body_present, body_len, rng):
    """Materialize the real body object matching the lifted observations."""
    if seekable:
        return io.BytesIO(bytes(rng.randrange(256) for _ in range(stream_len)))
    if body_present:
        return bytes(rng.randrange(256) for _ in range(body_len))
    return None


def real_post_state(make_request, body, verb, extra_tokens):
    """Run the REAL patched function; return the post-state as a token->int
    dict in the model's carrier (size header value parsed back to int,
    unrelated headers mapped back to their tokens)."""
    pr = make_request(verb, extra_tokens)
    pr.prepare_content_length(body)
    out = {}
    for tok in extra_tokens:
        name, val = EXTRA_HEADERS[tok]
        if name in pr.headers:
            out[tok] = int(pr.headers[name])
    if SIZE_HEADER_NAME in pr.headers:
        out[size_header()] = int(pr.headers[SIZE_HEADER_NAME])
    # Any header beyond the seeded ones + the size header would break the
    # frame: surface it as a disagreement via a sentinel token.
    known = {SIZE_HEADER_NAME.lower()} | {
        EXTRA_HEADERS[t][0].lower() for t in extra_tokens}
    for name in pr.headers:
        if name.lower() not in known:
            out[("unexpected", name)] = str(pr.headers[name])
    return out


def check_case(make_request, method_tok, seekable, stream_len,
               body_present, body_len, extra_tokens, rng):
    """One differential comparison; returns an error string or None."""
    # shadow side: the verbatim impl over the model carriers
    shadow_headers = {t: EXTRA_HEADERS[t][1] for t in extra_tokens}
    announce_body_size(shadow_headers, method_tok, seekable, stream_len,
                       body_present, body_len)
    # real side: the patched repo function over materialized values
    body = make_body(seekable, stream_len, body_present, body_len, rng)
    verb = TOKEN_TO_VERB[method_tok]
    real_headers = real_post_state(make_request, body, verb, extra_tokens)
    if shadow_headers != real_headers:
        return ("DISAGREEMENT\n"
                "  method=%r(%s) seekable=%r stream_len=%r body_present=%r "
                "body_len=%r extra=%r\n  shadow=%r\n  real=%r"
                % (method_tok, verb, seekable, stream_len, body_present,
                   body_len, sorted(extra_tokens), shadow_headers,
                   real_headers))
    return None


def boundary_cases():
    """(method_tok, seekable, stream_len, body_present, body_len, extras) --
    the full decision table, F2P rows first."""
    cases = []
    for tok in (1, 2, 3, 4, 5):
        for extras in ((), (10,), (10, 11, 12)):
            # bodyless (the discriminating rows)
            cases.append((tok, False, 0, False, 0, extras))
            # non-stream body present: empty and non-empty
            cases.append((tok, False, 0, True, 0, extras))
            cases.append((tok, False, 0, True, 7, extras))
            # seekable stream: empty and non-empty
            cases.append((tok, True, 0, True, 0, extras))
            cases.append((tok, True, 9, True, 4, extras))
    # one larger size on each present-body shape
    cases.append((3, False, 0, True, 1 << 16, ()))
    cases.append((3, True, 1 << 16, True, 0, ()))
    return cases


def rand_case(rng):
    tok = rng.choice(list(TOKEN_TO_VERB))
    shape = rng.random()
    if shape < 0.34:
        seekable, body_present = True, True
    elif shape < 0.67:
        seekable, body_present = False, True
    else:
        seekable, body_present = False, False
    stream_len = rng.randint(0, 512) if seekable else rng.randint(0, 8)
    body_len = rng.randint(0, 512) if (body_present and not seekable) \
        else rng.randint(0, 8)
    n_extra = rng.randint(0, 3)
    extras = tuple(rng.sample(sorted(EXTRA_HEADERS), n_extra))
    return (tok, seekable, stream_len, body_present, body_len, extras)


def main():
    # REAL patched callee (PYTHONPATH=/testbed, gold patch applied by the gate)
    from requests.models import PreparedRequest
    from requests.structures import CaseInsensitiveDict

    def make_request(verb, extra_tokens):
        pr = PreparedRequest()
        pr.headers = CaseInsensitiveDict()
        for tok in extra_tokens:
            name, val = EXTRA_HEADERS[tok]
            pr.headers[name] = str(val)
        pr.method = verb
        return pr

    rng = random.Random(SEED)
    checked = 0
    n_boundary = 0
    for case in boundary_cases():
        err = check_case(make_request, *case, rng=rng)
        if err:
            print(err)
            return 1
        checked += 1
        n_boundary += 1

    for _ in range(N_FUZZ):
        err = check_case(make_request, *rand_case(rng), rng=rng)
        if err:
            print(err)
            return 1
        checked += 1

    print("G-CONF OK: shadow impl (verbatim impl region) == real patched "
          "prepare_content_length on %d inputs (%d boundary + %d fuzz, "
          "seed %d), 0 disagreements." % (checked, n_boundary, N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
