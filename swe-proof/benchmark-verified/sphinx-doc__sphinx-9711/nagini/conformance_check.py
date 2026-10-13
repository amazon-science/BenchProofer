#!/usr/bin/env python3
"""G-CONF differential conformance check for sphinx-doc__sphinx-9711 (nagini).

SHADOW: the impl region of model.py, copied verbatim below with the contract
calls (Requires/Ensures) stripped. The @Pure helpers `seg` / `version_gt_from`
/ `version_gt` copy over as plain functions; PSeq[int] is realized as a plain
tuple (only len/indexing are used) and `ToSeq(list)` as `tuple(list)`. There
are no @ContractOnly callees in this bundle (the release-number ordering is a
deep model, not a consumed axiom).

ORACLE: the REAL patched repo function the model models per mapping.md —
`sphinx.extension.verify_needs_extensions(app, config)`, exercised one
extension at a time. The gate applies patch.diff to /testbed before this
script runs; PYTHONPATH=/testbed makes the patched module importable. The
oracle call is driven through minimal duck-typed carriers exposing exactly
the attributes the function reads: `config.needs_extensions` (a one-entry
name -> required-minimum mapping) and `app.extensions` (a one-entry name ->
extension mapping, using the repo's own Extension class so the loaded
version defaults exactly as it does in the repo when none is reported).

Type bridge (mapping.md section 2):
  - a release number `List[int]` of segments  <->  the dotted release string
    ".".join(str(seg) ...) on the repo side;
  - `ext_known=True`  <->  the extension was constructed with a reported
    version string; `ext_known=False`  <->  no version reported (the repo's
    Extension default sentinel), in which case the model's extversion
    segments are immaterial on both sides;
  - shadow outcome: normal `True` return  <->  oracle returns normally;
    shadow raises RequirementUnfulfilled  <->  oracle raises
    `sphinx.errors.VersionRequirementError` (the out-of-band abort).

Input domain: the modeled domain is valid dotted release numbers — non-empty
lists of non-negative integer segments (mapping.md section 3). Generation
draws 1..4 segments with values 0..99 plus a slice of larger values (up to
9999) and longer tails (up to 6 segments), all Requires-satisfying, plus the
ext_known flag. Boundary cases cover the segment-count/zero-padding edges and
the multi-digit-segment inputs where numeric and textual orderings disagree.

>= 1e5 Requires-satisfying inputs: boundary cases + 120000 fuzz triples.
Pinned fuzz seed: 97110.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outcomes and exits 1. stdlib only.
"""
import json
import random
import sys

SEED = 97110
N_FUZZ = 120_000


class RequirementUnfulfilled(Exception):
    """Shadow-side out-of-band failure signal (model.py's user-defined
    exception)."""
    pass


# --- PSeq / ToSeq shims: PSeq[int] is a plain tuple ---------------------------

def ToSeq(xs):
    return tuple(xs)


# --- pure helpers from model.py, verbatim, contracts stripped -----------------

def seg(s, i):
    if i < len(s):
        return s[i]
    return 0


def version_gt_from(a, b, i):
    if i >= len(a) and i >= len(b):
        return False
    if seg(a, i) > seg(b, i):
        return True
    if seg(a, i) < seg(b, i):
        return False
    return version_gt_from(a, b, i + 1)


def version_gt(a, b):
    return version_gt_from(a, b, 0)


# --- the impl region of model.py, verbatim, contract calls stripped -----------

def verify_requirement(reqversion, extversion, ext_known):
    fulfilled = True
    if not ext_known:
        fulfilled = False
    else:
        if version_gt(ToSeq(reqversion), ToSeq(extversion)):
            fulfilled = False
    if not fulfilled:
        raise RequirementUnfulfilled()
    return True


# --- bridge helpers ------------------------------------------------------------

def _vstr(segments):
    return ".".join(str(s) for s in segments)


def shadow_outcome(reqversion, extversion, ext_known):
    """Run the shadow; return 'ok' on normal return, 'reject' on the
    out-of-band signal."""
    try:
        result = verify_requirement(reqversion, extversion, ext_known)
    except RequirementUnfulfilled:
        return "reject"
    assert result is True
    return "ok"


def real_outcome(verify_needs_extensions, VersionRequirementError, Extension,
                 reqversion, extversion, ext_known):
    """Run the REAL patched repo function on the bridged input; return 'ok'
    if it returns normally, 'reject' if it aborts with the repo's
    version-requirement error."""
    import types
    extname = "conf.check.ext"
    if ext_known:
        extension = Extension(extname, None, version=_vstr(extversion))
    else:
        extension = Extension(extname, None)  # no reported version
    app = types.SimpleNamespace(extensions={extname: extension})
    config = types.SimpleNamespace(
        needs_extensions={extname: _vstr(reqversion)})
    try:
        verify_needs_extensions(app, config)
    except VersionRequirementError:
        return "reject"
    return "ok"


def check_triple(oracle_env, reqversion, extversion, ext_known):
    """Diff shadow vs oracle on one input triple; return an error string on
    disagreement, else None."""
    s = shadow_outcome(reqversion, extversion, ext_known)
    r = real_outcome(*oracle_env, reqversion, extversion, ext_known)
    if s != r:
        return ("DISAGREEMENT\n  reqversion=%r (%r)\n  extversion=%r (%r)\n"
                "  ext_known=%r\n  shadow=%s\n  real=%s"
                % (reqversion, _vstr(reqversion), extversion,
                   _vstr(extversion), ext_known, s, r))
    return None


def boundary_triples():
    pairs = [
        # numeric-vs-textual ordering disagreements (multi-digit segments)
        ([0, 6], [0, 10]),
        ([0, 10], [0, 6]),
        ([3, 9], [3, 10]),
        ([3, 10], [3, 9]),
        ([3, 11], [3, 10]),
        ([3, 10], [3, 10]),
        ([10], [9]),
        ([9], [10]),
        # zero-padding / prefix / equal-length edges
        ([3], [3, 0]),
        ([3, 0], [3]),
        ([3, 0, 0], [3]),
        ([1], [2]),
        ([2], [1]),
        ([1, 0], [1, 0, 0]),
        ([1, 2, 3], [1, 2, 3]),
        ([1, 2, 3], [1, 2, 4]),
        ([1, 2, 4], [1, 2, 3]),
        ([0], [0]),
        ([0, 0, 1], [0, 0, 0]),
        ([0, 6, 0], [0, 10, 0]),
        # single-segment and long-tail extremes
        ([1], [1]),
        ([99], [100]),
        ([100], [99]),
        ([1, 2, 3, 4, 5, 6], [1, 2, 3, 4, 5, 6]),
        ([1, 2, 3, 4, 5, 6], [1, 2, 3, 4, 5, 7]),
    ]
    triples = []
    for req, ext in pairs:
        triples.append((req, ext, True))
        triples.append((req, ext, False))  # unknown loaded version: always reject
    return triples


def rand_release(rng):
    if rng.random() < 0.10:
        # longer tails / larger segments (still valid release numbers)
        n = rng.randint(1, 6)
        return [rng.randint(0, 9999) for _ in range(n)]
    n = rng.randint(1, 4)
    return [rng.randint(0, 99) for _ in range(n)]


def main():
    # REAL patched repo symbols (the oracle)
    from sphinx.extension import Extension, verify_needs_extensions
    from sphinx.errors import VersionRequirementError

    oracle_env = (verify_needs_extensions, VersionRequirementError, Extension)

    checked = 0
    boundary = boundary_triples()
    for req, ext, known in boundary:
        err = check_triple(oracle_env, req, ext, known)
        if err:
            print(err)
            return 1
        checked += 1

    rng = random.Random(SEED)
    for _ in range(N_FUZZ):
        req = rand_release(rng)
        ext = rand_release(rng)
        known = rng.random() < 0.9  # mostly known versions; unknowns sampled too
        err = check_triple(oracle_env, req, ext, known)
        if err:
            print(err)
            return 1
        checked += 1

    print("G-CONF OK: shadow impl == real requirement check on %d inputs "
          "(%d boundary + %d fuzz, seed %d)."
          % (checked, len(boundary), N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
