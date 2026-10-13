#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-12419 (nagini).

SHADOW: the impl region of model.py, copied verbatim below with the contract
calls stripped (Assert / Invariant lines removed; nothing else changed). The
HeaderSlot carrier is reproduced as a plain class. There are no @ContractOnly
callees in this bundle (the axioms region is empty); the @Pure helpers are
spec-only (never called from the impl region) so none need to be carried over.

ORACLE: the REAL patched repo behaviour the model models per mapping.md --
the referrer-policy branch of
`django.middleware.security.SecurityMiddleware.process_response`, driven by
the shipped default configuration (the gate applies patch.diff before this
script runs; PYTHONPATH=/testbed). `settings.configure()` with no overrides
picks up the shipped global defaults, so the middleware sees exactly the
baseline configured policy. Each case builds a fresh HttpResponse, optionally
pre-sets the Referrer-Policy header, runs process_response, and observes the
header slot.

Type bridge (mapping.md section 2): the model's HeaderSlot{present, value}
maps to the Referrer-Policy slot of the response's header mapping --
  slot.present  <->  'Referrer-Policy' in response
  slot.value    <->  [ord(c) for c in response['Referrer-Policy']]
Pre-existing header values are drawn from the code points the real header
store carries verbatim: latin-1 range (0..255) excluding CR and LF, which the
header setter rejects by design (those inputs are outside the bridgeable
domain -- the model's slot carries an already-stored value, and no stored
value can contain them).

Input domain: the model's Requires places only access permissions on the
slot, so every (present: bool, value: List[int]) pair whose value is
representable as a stored header value is Requires-satisfying. Boundary
cases: absent slot; present with empty value; present with the exact
baseline value; present with single-char, long, whitespace-padded,
comma-bearing, and full-latin-1 values. Fuzz alternates absent/present and
draws random storable values.

>= 1e5 Requires-satisfying inputs: boundary cases + 100000 fuzz.
Pinned fuzz seed: 12419.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outcomes and exits 1. stdlib only.
"""
import json
import random
import sys

SEED = 12419
N_FUZZ = 100_000

HEADER = 'Referrer-Policy'


# --- the model's carrier, as a plain class (contracts stripped) ---------------

class HeaderSlot:
    def __init__(self, present, value):
        self.present = present
        self.value = value


# --- the impl region of model.py, verbatim (contracts stripped) --------------

def apply_referrer_policy(slot):
    # The configured referrer policy supplied by the shipped baseline.
    policy = [115, 97, 109, 101, 45, 111, 114, 105, 103, 105, 110]  # type: List[int]
    if len(policy) > 0:
        if not slot.present:
            # Build the normalized value: trim each comma-separated token,
            # rejoin by commas. For the baseline (no comma, no whitespace) this
            # copies the token verbatim.
            value = []  # type: List[int]
            i = 0
            while i < len(policy):
                value = value + [policy[i]]
                i = i + 1
            slot.present = True
            slot.value = value


# --- shadow / oracle outcomes -------------------------------------------------

def shadow_outcome(present, value_cps):
    slot = HeaderSlot(present, list(value_cps))
    apply_referrer_policy(slot)
    return (slot.present, tuple(slot.value) if slot.present else None)


def make_real_runner():
    import django
    from django.conf import settings
    if not settings.configured:
        # No overrides: the middleware must see the shipped defaults.
        settings.configure()
        try:
            django.setup()
        except Exception:
            pass
    from django.http import HttpRequest, HttpResponse
    from django.middleware.security import SecurityMiddleware

    try:
        mw = SecurityMiddleware(lambda request: HttpResponse())
    except TypeError:
        mw = SecurityMiddleware()
    request = HttpRequest()

    def run(present, value_cps):
        response = HttpResponse()
        if present:
            response[HEADER] = ''.join(chr(c) for c in value_cps)
        out = mw.process_response(request, response)
        if HEADER in out:
            return (True, tuple(ord(c) for c in out[HEADER]))
        return (False, None)

    return run


def check_case(run_real, present, value_cps):
    s = shadow_outcome(present, value_cps)
    r = run_real(present, value_cps)
    if s != r:
        return ("DISAGREEMENT\n  input: present=%r value=%r\n"
                "  shadow=%r\n  real=%r" % (present, list(value_cps), s, r))
    return None


# --- input generation ---------------------------------------------------------

BASELINE = (115, 97, 109, 101, 45, 111, 114, 105, 103, 105, 110)

# Code points a stored header value can carry verbatim: latin-1 minus CR/LF
# (the header setter rejects CR/LF by design, so no stored value has them).
_STORABLE = [c for c in range(256) if c not in (10, 13)]


def boundary_cases():
    cases = [(False, ())]                       # absent slot
    values = [
        (),                                     # present, empty value
        BASELINE,                               # present, exactly the baseline
        (120,),                                 # single char
        tuple(ord(c) for c in 'no-referrer'),
        tuple(ord(c) for c in 'origin-when-cross-origin'),
        tuple(ord(c) for c in ' padded '),      # surrounding whitespace kept
        tuple(ord(c) for c in 'a, b ,c'),       # comma-bearing value kept
        tuple(ord(c) for c in 'unsafe-url') * 30,   # long value
        tuple(_STORABLE),                       # every storable code point
        (0,), (9,), (32,), (44,), (255,),
    ]
    cases += [(True, v) for v in values]
    return cases


def rand_case(rng):
    if rng.random() < 0.5:
        # Absent slot (the value field is ignored by both sides).
        return (False, ())
    n = rng.randint(0, 40)
    pick = rng.random()
    if pick < 0.5:
        # printable ascii
        value = tuple(rng.randint(32, 126) for _ in range(n))
    elif pick < 0.8:
        # full storable latin-1
        value = tuple(rng.choice(_STORABLE) for _ in range(n))
    else:
        # policy-shaped tokens with commas/spaces mixed in
        alpha = [ord(c) for c in 'abcdefghijklmnopqrstuvwxyz-'] + [44, 32]
        value = tuple(rng.choice(alpha) for _ in range(n))
    return (True, value)


def main():
    run_real = make_real_runner()

    checked = 0
    n_boundary = 0
    for present, value in boundary_cases():
        err = check_case(run_real, present, value)
        if err:
            print(err)
            return 1
        checked += 1
        n_boundary += 1

    rng = random.Random(SEED)
    for _ in range(N_FUZZ):
        present, value = rand_case(rng)
        err = check_case(run_real, present, value)
        if err:
            print(err)
            return 1
        checked += 1

    print("G-CONF OK: shadow impl == real response filter on %d inputs "
          "(%d boundary + %d fuzz, seed %d)." % (checked, n_boundary,
                                                 N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
