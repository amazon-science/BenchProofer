#!/usr/bin/env python3
"""G-CONF differential conformance check for sphinx-doc__sphinx-7985 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region (`isUnchecked`,
              the nested-`if` control flow, the `working`/`ignored`/`broken`
              dispatch) transliterated to Python over the real repo types
              (`uri: str`, `fileExists: bool`, `anyIgnore: bool`), via the
              mapping.md bijection. The access-method test is the A-reference
              `hasUriScheme`; per plan §4.1 the A-tagged callee is left as the
              REAL repo callee here (`uri_re.match`), so the shadow's "explicit
              scheme?" test calls the genuine detector, not the model — that
              isolates the surrounding R/I control flow.

  * ORACLE  — patch.diff's behaviour: a faithful executable copy of the patched
              non-network arm of `check()` (the `elif not uri.startswith(...)`
              block), driven by the REAL `uri_re` and with `path.exists(...)` /
              the `self.to_ignore` match loop replaced by the supplied booleans
              `fileExists` / `anyIgnore` (the unchanged callees enter BOTH sides
              identically as inputs — they are method inputs, mapping.md §3.2).
              This is the gold control flow (G-RESOLVE confirms the shipped patch
              resolves).

They must agree on the observable status word for every Requires-satisfying
input (`uri` is non-network: it does not start with `http:`/`https:`). Exit 0 iff
zero disagreements; any disagreement is a mechanical R/I-fidelity counterexample.

Runs stdlib-only (`re` is the same module the patched module imports). Fuzz seed
pinned (mapping.md §4) for a deterministic verdict.
"""
import random
import re
import sys

SEED = 7985
N_FUZZ = 100_000

# The REAL callee, byte-for-byte as the gold patch constructs it.
URI_RE = re.compile('[a-z]+://')


# --- ORACLE: faithful copy of patch.diff's patched non-network arm -----------
# Mirrors sphinx/builders/linkcheck.py check() post-patch:
#     if len(uri) == 0 or uri.startswith(('#', 'mailto:')):
#         return 'unchecked', '', 0
#     elif not uri.startswith(('http:', 'https:')):
#         if uri_re.match(uri):
#             return 'unchecked', '', 0          # non supported URI schemes
#         else:
#             if path.exists(path.join(self.srcdir, uri)):   # -> fileExists
#                 return 'working', '', 0
#             else:
#                 for rex in self.to_ignore:                 # -> anyIgnore
#                     if rex.match(uri):
#                         return 'ignored', '', 0
#                 else:
#                     return 'broken', '', 0
# The returned (status, '', 0) tuple is abstracted to its status word
# (mapping.md §2). path.exists / the to_ignore loop are method inputs.
def oracle(uri, file_exists, any_ignore):
    if len(uri) == 0 or uri.startswith(('#', 'mailto:')):
        return 'unchecked'
    # precondition: caller guarantees uri is non-network (not http(s)).
    if URI_RE.match(uri):                       # REAL callee (A-reference)
        return 'unchecked'
    else:
        if file_exists:
            return 'working'
        else:
            if any_ignore:
                return 'ignored'
            else:
                return 'broken'


# --- SHADOW: Solution.lean impl region transliterated ------------------------
def shadow_is_unchecked(uri):
    # isUnchecked (model.py): empty / '#'-prefixed / 'mailto:'-prefixed
    return len(uri) == 0 or uri.startswith('#') or uri.startswith('mailto:')


def shadow(uri, file_exists, any_ignore):
    if shadow_is_unchecked(uri):
        return 'unchecked'
    else:
        if bool(URI_RE.match(uri)):             # REAL callee left in (A-reference leg)
            return 'unchecked'
        else:
            if file_exists:
                return 'working'
            else:
                if any_ignore:
                    return 'ignored'
                else:
                    return 'broken'


def fuzz_inputs(n, rng):
    # boundary link texts (non-network only — the modeled arm's domain)
    boundary_uris = [
        "", "#frag", "mailto:a@b.com",          # skip-without-resolution
        "ftp:server/file", "ftp://host/f",      # 'ftp:' dropped from skip guard
        "ftps://host", "gopher://x", "a://b",   # explicit unsupported schemes
        "conf.py", "path/to/notfound",          # the F2P local files
        "doesntexist", "./relative", "../up",
        "dir/sub/file.txt", "ABC://x", "a1b://x",
        "file:local", "data:base", "tel:123",
        "weird stuff", ":/x", "://x", "a:/b",
    ]
    bools = (True, False)
    for uri in boundary_uris:
        for fe in bools:
            for ai in bools:
                yield (uri, fe, ai)
    alphabet = list("abcxyz") + list("ABCZ") + list("0139") + \
        [":", "/", ".", "-", "_", " ", "#", "@"]
    prefixes = ["", "ftp", "ftps", "mailto:", "#", "conf", "path/to/x", "a"]
    for _ in range(n):
        if rng.random() < 0.3:
            uri = rng.choice(prefixes) + "".join(
                rng.choice(alphabet) for _ in range(rng.randint(0, 8)))
        else:
            uri = "".join(rng.choice(alphabet) for _ in range(rng.randint(0, 16)))
        # keep within the modeled (non-network) domain
        if uri.startswith(('http:', 'https:')):
            continue
        yield (uri, rng.choice((True, False)), rng.choice((True, False)))


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for uri, fe, ai in fuzz_inputs(N_FUZZ, rng):
        count += 1
        sh = shadow(uri, fe, ai)
        orc = oracle(uri, fe, ai)
        if sh != orc:
            disagreements.append(((uri, fe, ai), sh, orc))
            if len(disagreements) >= 5:
                break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for inp, sh, orc in disagreements:
            print("  input=%r shadow=%r oracle=%r" % (inp, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of classifyLocalLink agrees with patch.diff "
          "behaviour on %d inputs (seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
