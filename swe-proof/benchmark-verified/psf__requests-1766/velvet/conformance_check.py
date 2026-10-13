#!/usr/bin/env python3
"""G-CONF differential conformance check for psf__requests-1766 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region
              (`appendQopDirective`) transliterated to Python over the *real*
              repo type (`str`), via the mapping.md bijection (`List Char` ↔
              `str`). The impl appends, to the prefix `base`, the constant
              directive head carrying the QUOTED value token `"auth"`, then the
              bare count value, then `, cnonce="`, the client-nonce, and a
              closing quote. There are no A-tagged callees, so the whole shadow
              is pure R/I.
  * ORACLE  — `patch.diff`'s behaviour: the patched
              `requests.auth.HTTPDigestAuth.build_digest_header` applied at
              base_commit (the harness applies patch.diff before this runs).
              We drive the real function with a synthetic Digest challenge and
              read back the produced `Authorization` credential; the
              count/client-nonce it chose internally are recovered from that
              credential so the shadow can reconstruct the exact directive
              segment the gold code emitted.

They must agree on the assembled qop directive segment for every challenge.
Exit 0 iff zero disagreements; any disagreement is a mechanical R/I-fidelity
counterexample.

Runs in-container (the prebuilt SWE-Bench instance image), stdlib + hypothesis
only. The fuzz seed is pinned for a deterministic verdict.
"""
import random
import re
import sys

SEED = 1766
N_FUZZ = 5000

# --- the R/I shadow: Solution.lean directiveHead/qopSegment, transliterated ----
QUOTED_VALUE_TOKEN = '"auth"'
DIRECTIVE_HEAD = ', qop=' + QUOTED_VALUE_TOKEN + ', nc='
DIRECTIVE_MID = ', cnonce="'
DIRECTIVE_TAIL = '"'


def shadow_qop_segment(ncvalue, cnonce):
    """qopSegment ncvalue cnonce transliterated to str: directiveHead (carrying
    the QUOTED value token) + count + directiveMid + client-nonce + tail."""
    return DIRECTIVE_HEAD + ncvalue + DIRECTIVE_MID + cnonce + DIRECTIVE_TAIL


# --- the oracle: patched build_digest_header behaviour -------------------------
def make_auth(qop_value):
    """Construct a patched HTTPDigestAuth primed with a synthetic challenge so a
    single build_digest_header call emits the qop branch (qop present)."""
    from requests.auth import HTTPDigestAuth
    auth = HTTPDigestAuth('user', 'pass')
    chal = {'realm': 'testrealm@host.com',
            'nonce': 'dcd98b7102dd2f0e8b11d0f600bfb0c093',
            'qop': qop_value}
    # The challenge lives either on the instance (older API) or on a per-thread
    # state object (newer API); set whichever the installed version uses.
    if hasattr(auth, 'init_per_thread_state'):
        auth.init_per_thread_state()
        auth._thread_local.chal = chal
        auth._thread_local.last_nonce = ''
        auth._thread_local.nonce_count = 0
    else:
        auth.chal = chal
        auth.last_nonce = ''
        auth.nonce_count = 0
    return auth


def oracle_segment(qop_value):
    """patch.diff's behaviour: build a real credential and recover the qop
    directive segment (from `, qop=` through the closing client-nonce quote),
    plus the count/client-nonce the gold code chose internally."""
    auth = make_auth(qop_value)
    cred = auth.build_digest_header('GET', 'http://example.com/dir/index.html')
    # cred == 'Digest username="...", ..., qop=..., nc=<nc>, cnonce="<cn>"'
    m = re.search(r', qop=.*?, nc=([0-9a-f]+), cnonce="([0-9a-f]+)"\Z', cred)
    if not m:
        raise AssertionError("unexpected credential layout: %r" % cred)
    ncvalue, cnonce = m.group(1), m.group(2)
    segment = cred[cred.index(', qop='):]
    return segment, ncvalue, cnonce


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    # The qop directive is emitted whenever a qop challenge is present; the F2P
    # test uses 'auth'. Comma-separated qop lists also trigger the branch.
    qop_values = ['auth', 'auth,auth-int', 'auth-int,auth']
    for _ in range(N_FUZZ):
        qv = rng.choice(qop_values)
        count += 1
        oracle_seg, ncvalue, cnonce = oracle_segment(qv)
        shadow_seg = shadow_qop_segment(ncvalue, cnonce)
        if shadow_seg != oracle_seg:
            disagreements.append((qv, shadow_seg, oracle_seg))
            if len(disagreements) >= 5:
                break
        # The decisive substring the F2P test inspects must be present.
        if QUOTED_VALUE_TOKEN not in oracle_seg:
            disagreements.append((qv, "missing '\"auth\"'", oracle_seg))
            break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for qv, sh, orc in disagreements:
            print("  qop=%r shadow=%r oracle=%r" % (qv, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of appendQopDirective agrees with patch.diff "
          "behaviour on %d challenges (seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
