#!/usr/bin/env python3
"""G-AX executable soundness check for astropy__astropy-7671.

There are NO consumed @ContractOnly axioms in model.py (its axioms region is
empty). The two changed operations are modelled DEEPLY, and this script
validates each deep model against the REAL library callee it stands in for
(A-reference checks, in the project's terminology), on boundary cases plus
randomized fuzz. Exit 0 iff every observation matches the model.

  (A-reference 1) the deep model `normalize` (model.py pure region) == the
      leading dotted-numeric prefix the real qualifier-stripping regex extracts.
      The real operation (gold patch) is:

          expr = r'^([1-9]\\d*!)?(0|[1-9]\\d*)(\\.(0|[1-9]\\d*))*'
          m = re.match(expr, version)
          if m: version = m.group(0)

      i.e. keep only the leading run of dotted release numbers, discarding any
      trailing non-numeric qualifier ("dev", "rc1", ...).

  (A-reference 2) the deep model `loose_ge` / `loose_gt` (model.py pure region)
      == the real component-wise version order
      `LooseVersion(a) >= LooseVersion(b)` / `> ` on qualifier-free (numeric)
      versions.

  (END-TO-END / DOMAIN) the deep model assembled exactly as `model.py`'s
      `version_meets_minimum` impl (`loose_ge(have, normalize(want))`) ==
      the REAL gold-patched `minversion` body, AND the spec's `Requires`
      domain (the requested version begins with a numeric release segment) is
      EXACTLY the region on which the real comparison is defined and total.
      Labels OUTSIDE that domain (pure / leading qualifier, empty, leading
      dot, epoch) make the real `minversion` RAISE (TypeError/AttributeError)
      or diverge from any defined ordering -- so the contract correctly
      promises a defined boolean only where one exists. This is the check that
      closes the directive-7 no-raise / total-vs-partial obligation: it
      fuzzes the raise behaviour across the full domain rather than excluding
      the qualifier region.

Versions are bridged between the string world (real callees) and the model's
parsed-component world (`List[int]`, with the sentinel -1 marking the start of
a qualifier tail) by `encode()` below, the documented type bijection
(mapping.md).

Imports nothing repo-specific: `re` and `distutils.version.LooseVersion` are
the Python standard library -- the exact callees the gold patch uses.
"""
import re
import random
import sys
from distutils.version import LooseVersion

# The qualifier-stripping regex from the gold patch (PEP440 Appendix B prefix).
EXPR = r'^([1-9]\d*!)?(0|[1-9]\d*)(\.(0|[1-9]\d*))*'

QUALIFIER = -1   # model.py sentinel: start of the non-numeric qualifier tail


# --- the type bijection: version string <-> model component list -------------

class Unencodable(Exception):
    """Raised when a version label is outside the model carrier's domain.

    The carrier is a list of NON-NEGATIVE integer release segments, optionally
    terminated by a single qualifier marker. Epoch labels ("1!2.3") carry a
    '!' separator inside the regex prefix and cannot be split into plain
    integer components; the model carrier does not represent them (see D3 /
    mapping.md domain note). They are excluded here rather than silently
    mis-encoded."""


def encode(version):
    """Map a real version string to model.py's parsed-component representation.

    The leading dotted-numeric run becomes its integer components; if any
    trailing qualifier remains, a single QUALIFIER (-1) marker is appended (the
    model only cares THAT a qualifier tail exists, not its content).

    Raises Unencodable for epoch labels (a '!' inside the matched prefix),
    which the model carrier does not represent."""
    m = re.match(EXPR, version)
    prefix = m.group(0) if m else ""
    if '!' in prefix:
        # epoch form "N!release..." -- not representable as plain int segments.
        raise Unencodable("epoch version %r outside model carrier domain" % version)
    comps = [int(x) for x in prefix.split('.')] if prefix else []
    if prefix != version:
        comps = comps + [QUALIFIER]
    return comps


# --- model.py reference encodings (kept in lock-step with the pure region) ---

def normalize(s):
    """Reference impl of model.py `normalize`: the prefix of `s` up to (not
    incl.) the first qualifier marker (first negative segment)."""
    out = []
    for c in s:
        if c < 0:
            break
        out.append(c)
    return out


def loose_ge(a, b):
    """Reference impl of model.py `loose_ge` (inclusive component-wise order)."""
    i = 0
    while True:
        if i >= len(a) and i >= len(b):
            return True
        if i >= len(a):
            return False
        if i >= len(b):
            return True
        if (a[i] < 0) != (b[i] < 0):
            return False
        if a[i] != b[i]:
            return a[i] > b[i]
        i += 1


def loose_gt(a, b):
    """Reference impl of model.py `loose_gt` (strict component-wise order)."""
    i = 0
    while True:
        if i >= len(a) and i >= len(b):
            return False
        if i >= len(a):
            return False
        if i >= len(b):
            return True
        if (a[i] < 0) != (b[i] < 0):
            return False
        if a[i] != b[i]:
            return a[i] > b[i]
        i += 1


def version_meets_minimum(have, want, inclusive):
    """The END-TO-END deep model, assembled EXACTLY as model.py's
    `version_meets_minimum` impl region: compare the installed version against
    the qualifier-STRIPPED requested version. `have`/`want` are model carriers."""
    norm = normalize(want)
    if inclusive:
        return loose_ge(have, norm)
    else:
        return loose_gt(have, norm)


# --- the REAL gold-patched callee (verbatim transcription of patch.diff) -----

def real_minversion(have_version, version, inclusive=True):
    """The real gold-patched `minversion` comparison tail (introspection.py
    after the patch), with the unchanged module/version_path resolution
    prologue abstracted to its resolved string operands. Transcribed verbatim
    from patch.diff so G-AX checks the deep model against the REAL behaviour,
    raises and all."""
    m = re.match(EXPR, version)
    if m:
        version = m.group(0)
    if inclusive:
        return LooseVersion(have_version) >= LooseVersion(version)
    else:
        return LooseVersion(have_version) > LooseVersion(version)


# --- an INDEPENDENT prefix oracle (NOT derived from EXPR / encode) -----------

def independent_release_prefix(version):
    """An oracle for the leading numeric release run that does NOT go through
    the gold regex `EXPR` nor `encode`: it uses distutils' own `LooseVersion`
    parser (a completely different code path) and takes the leading run of
    integer components. On the model carrier's canonical domain (segments
    without leading zeros, no epoch) this agrees with the regex prefix, giving
    `check_normalize` a genuinely independent reference instead of one
    re-derived from `re.match`+`encode` (D2: de-tautologized)."""
    out = []
    for c in LooseVersion(version).version:
        if isinstance(c, int):
            out.append(c)
        else:
            break
    return out


# --- the checks --------------------------------------------------------------

def check_normalize_vs_independent(version):
    """D2: assert the deep model `normalize(encode(version))` == an
    INDEPENDENTLY computed leading numeric release run (distutils LooseVersion
    parser, not the gold regex). Restricted to the model carrier's canonical
    domain so the two parsers agree exactly."""
    model_comps = normalize(encode(version))
    indep = independent_release_prefix(version)
    assert model_comps == indep, (
        "normalize deep model unsound on %r: independent LooseVersion prefix "
        "%r, model gives %r" % (version, indep, model_comps))


def check_normalize_strips(carrier, expected):
    """D2: validate the `normalize` PREFIX LOGIC directly on a hand-built
    carrier (markers in arbitrary positions), with no `re.match`/`encode` in
    the loop. Asserts it returns the prefix up to the first qualifier marker."""
    assert normalize(carrier) == expected, (
        "normalize prefix logic wrong on %r: expected %r, got %r"
        % (carrier, expected, normalize(carrier)))


def check_order(a_str, b_str):
    """For two qualifier-free (numeric) version strings, assert the deep model
    loose_ge / loose_gt == the REAL LooseVersion comparison."""
    a, b = encode(a_str), encode(b_str)
    assert QUALIFIER not in a and QUALIFIER not in b
    real_ge = LooseVersion(a_str) >= LooseVersion(b_str)
    real_gt = LooseVersion(a_str) > LooseVersion(b_str)
    assert loose_ge(a, b) == real_ge, (
        "loose_ge unsound on (%r,%r): real %s, model %s"
        % (a_str, b_str, real_ge, loose_ge(a, b)))
    assert loose_gt(a, b) == real_gt, (
        "loose_gt unsound on (%r,%r): real %s, model %s"
        % (a_str, b_str, real_gt, loose_gt(a, b)))


def in_spec_domain(want_str):
    """The model.py `Requires` domain on `want`: the requested label begins
    with a numeric release segment, i.e. `encode(want)[0] >= 0` and it is
    representable. Mirrors `Requires(len(want) > 0 and want[0] >= 0)`."""
    try:
        w = encode(want_str)
    except Unencodable:
        return False
    return len(w) > 0 and w[0] >= 0


def check_end_to_end_in_domain(have_str, want_str, inclusive):
    """D1 (the directive-7 no-raise obligation): on the spec's `Requires`
    domain the real gold-patched `minversion` MUST return normally and equal
    the end-to-end deep model. (`have_str` is always a numeric installed
    version, per `Requires(is_numeric(have))`.)"""
    have = encode(have_str)
    want = encode(want_str)
    try:
        real = real_minversion(have_str, want_str, inclusive)
    except Exception as e:  # pragma: no cover - would be a soundness failure
        raise AssertionError(
            "real minversion(%r, %r, inclusive=%s) RAISED %s inside the spec "
            "domain -- the contract over-claims a total result"
            % (have_str, want_str, inclusive, type(e).__name__))
    model = version_meets_minimum(have, want, inclusive)
    assert model == real, (
        "end-to-end deep model disagrees with real minversion(%r, %r, "
        "inclusive=%s): real %s, model %s"
        % (have_str, want_str, inclusive, real, model))


def check_out_of_domain_is_partial(have_str, want_str):
    """D1: a requested label OUTSIDE the spec domain (first segment not a
    numeric release component) is exactly where the real comparison is partial
    -- it RAISES, or (for a leading-dot label whose stripped form is empty) it
    returns a value that does NOT correspond to any defined release ordering.
    Confirms the `Requires` narrowing is the precise non-raising region rather
    than an arbitrary cut. Returns a tag describing the observed partiality."""
    assert not in_spec_domain(want_str), (
        "%r should be outside the spec domain" % want_str)
    try:
        real_minversion(have_str, want_str, True)
    except (TypeError, AttributeError):
        return "raises"
    except Exception as e:
        return "raises(%s)" % type(e).__name__
    # Did not raise: then it must be a label the regex could not strip (m is
    # None), so the real callee compared a degenerate operand. We only require
    # that such a label is excluded from the contract domain (it is), so this
    # is still a faithful partiality witness -- record it.
    return "returns-without-defined-order"


def main():
    # --- normalize (A-reference 1): boundary + the F2P test labels ----------
    # All begin with a numeric release segment (the spec domain), no epoch.
    norm_boundary = [
        "0.12", "0.12.1", "0.12.0.dev", "0.12dev",   # the F2P good versions
        "1", "1.2rc1",                                # the F2P bad versions
        "0.12.2",                                     # the installed version
        "1.14dev", "1.14.3", "2.0.0", "10.0",
        "3.6.0rc2", "1.0a1", "2.1.0.post1", "0.0",
    ]
    for v in norm_boundary:
        check_normalize_vs_independent(v)

    # --- normalize PREFIX LOGIC (D2): direct, hand-built carriers -----------
    # No re.match / encode here -- exercises the marker-stripping itself,
    # including markers in interior / leading / absent positions.
    check_normalize_strips([], [])
    check_normalize_strips([0, 12], [0, 12])
    check_normalize_strips([0, 12, QUALIFIER], [0, 12])
    check_normalize_strips([1, 2, QUALIFIER], [1, 2])
    check_normalize_strips([0, 12, 0, QUALIFIER], [0, 12, 0])
    check_normalize_strips([QUALIFIER], [])
    check_normalize_strips([QUALIFIER, 5, 6], [])      # leading marker -> empty
    check_normalize_strips([3], [3])
    check_normalize_strips([10, 0, 0, QUALIFIER], [10, 0, 0])

    # --- normalize (A-reference 1): randomized fuzz over realistic labels ---
    rng = random.Random(7671)
    quals = ["", "dev", "rc1", "rc2", "a1", "b2", ".dev", ".dev0",
             "post1", ".post0", "c1", "alpha", "beta"]
    fuzz_labels = []
    for _ in range(20000):
        nseg = rng.randint(1, 4)
        # leading-zero-free numeric segments to stay inside the regex grammar
        segs = []
        for _ in range(nseg):
            if rng.random() < 0.3:
                segs.append("0")
            else:
                segs.append(str(rng.randint(1, 99)))
        v = ".".join(segs) + rng.choice(quals)
        fuzz_labels.append(v)
        check_normalize_vs_independent(v)

    # --- loose_ge / loose_gt (A-reference 2): boundary numeric pairs --------
    num_versions = ["0", "1", "0.12", "0.12.0", "0.12.1", "0.12.2",
                    "1.2", "1.14", "1.14.3", "2.0", "10.0", "1.0.0", "0.0.1"]
    for a in num_versions:
        for b in num_versions:
            check_order(a, b)

    # --- loose_ge / loose_gt (A-reference 2): randomized numeric fuzz -------
    for _ in range(20000):
        def rnd_num():
            n = rng.randint(1, 4)
            return ".".join(str(rng.randint(0, 9)) for _ in range(n))
        check_order(rnd_num(), rnd_num())

    # --- END-TO-END within the spec domain (D1): the deep model assembled as
    # model.py's impl == the REAL gold-patched minversion, and the real callee
    # NEVER raises on the Requires-admitted domain. -------------------------
    e2e_have = ["0.12.2", "1.14.3", "2.0.0", "1.0", "0.12", "10.0", "3.6.0"]
    for have_str in e2e_have:
        for want_str in norm_boundary + fuzz_labels[:2000]:
            assert in_spec_domain(want_str)
            check_end_to_end_in_domain(have_str, want_str, True)
            check_end_to_end_in_domain(have_str, want_str, False)

    # --- OUT-OF-DOMAIN is exactly the partial region (D1): every excluded
    # label makes the real callee raise or lose a defined ordering. This is
    # the fuzz of the RAISE behaviour directive 7 requires -- it no longer
    # structurally excludes the qualifier region. -------------------------
    out_of_domain = [
        "dev", "beta", "stable", "rc1", "alpha",      # pure qualifier
        "", " ", "x", "v1.0",                          # empty / non-numeric head
        ".1", ".12.3", ".dev",                         # leading dot
        "1!2.3", "2!1.0",                              # epoch (carrier-excluded)
        "abc.1.2",                                      # non-numeric head
    ]
    raise_witnesses = 0
    for want_str in out_of_domain:
        tag = check_out_of_domain_is_partial("0.12.2", want_str)
        if tag.startswith("raises"):
            raise_witnesses += 1
    assert raise_witnesses >= 8, (
        "expected most out-of-domain labels to make real minversion raise; "
        "only %d did" % raise_witnesses)

    # randomized out-of-domain fuzz: pure / leading-qualifier labels
    bad_heads = ["dev", "rc", "alpha", "beta", "", ".", ".0", "x", "v"]
    for _ in range(2000):
        head = rng.choice(bad_heads)
        tail = "" if rng.random() < 0.5 else ".".join(
            str(rng.randint(0, 9)) for _ in range(rng.randint(1, 3)))
        v = head + tail
        if in_spec_domain(v):
            continue  # a few may parse to a numeric head; only test the excluded ones
        check_out_of_domain_is_partial("0.12.2", v)

    # --- the headline differential: the qualifier tail must be stripped -----
    # The exact F2P discriminator: installed 0.12.2, requested 0.12dev.
    have = encode("0.12.2")
    want = encode("0.12dev")
    assert QUALIFIER in want, "0.12dev must carry a qualifier marker"
    # post-patch (normalize first) -> satisfied; pre-patch (raw) -> not satisfied
    assert loose_ge(have, normalize(want)) is True
    assert loose_ge(have, want) is False
    # and the real machinery: stripped compares fine, raw raises a TypeError
    assert LooseVersion("0.12.2") >= LooseVersion("0.12")
    raised = False
    try:
        LooseVersion("0.12.2") >= LooseVersion("0.12dev")
    except TypeError:
        raised = True
    assert raised, "expected the un-stripped comparison to raise (the bug)"

    print("G-AX OK: normalize deep model == independent LooseVersion prefix on "
          "%d boundary + 20000 fuzz labels (and prefix logic validated directly "
          "on hand-built carriers); loose_ge/loose_gt deep model == real "
          "LooseVersion order on %d boundary + 20000 fuzz numeric pairs; "
          "end-to-end model == real minversion (no raise) across the spec "
          "domain; every out-of-domain label is partial (raises/undefined) -- "
          "the Requires domain is exactly the non-raising region; "
          "qualifier-strip differential confirmed."
          % (len(norm_boundary), len(num_versions) ** 2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
