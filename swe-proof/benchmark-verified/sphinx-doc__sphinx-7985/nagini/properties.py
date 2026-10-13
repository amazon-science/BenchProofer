# properties.py — PBT manifest for sphinx-doc__sphinx-7985. NOT a Nagini module;
# a record of adversarial cases. The runner (swebench_nagini.pbt) executes each
# and stamps RESULT. Spec cases are full model.py variants (SAME frozen spec,
# swapped impl region only) checked by Nagini verify + same_spec; axiom cases
# are real-callee probes checked in Docker.
#
# Defended surface (read from model.py):
#   * starts_with(target, lit)   read-only Acc(list_pred(target),1/4),
#                                Acc(list_pred(lit),1/4); pins
#                                Result()==prefix_eq(ToSeq(target),ToSeq(lit)).
#   * scheme_present(target)     read-only Acc(list_pred(target),1/4); pins
#                                Result()==has_uri_scheme(ToSeq(target)).
#   * check(target, file_exists, ignore_match, remote)
#                                read-only Acc(list_pred(target),1/2); pins
#                                Result()==classify(ToSeq(target),file_exists,
#                                ignore_match,remote) PLUS three structural
#                                implications grounding MISSING/WORKING/IGNORED
#                                in witnessed input properties.
#
# Oracle-grounding note: classify / prefix_eq / has_uri_scheme are @Pure
# functions SPELLED OUT over the input args (code points + the three boolean/
# int env facts) — they are NOT opaque answer-keys. "Echoing classify(...)" IS
# performing the modeled decision, so there is no *wrong* echo to build; the
# UNGROUNDED-ORACLE-ECHO class does not apply. Instead we attack the real
# weakness surface: a frame mutation of the read-only target, and partial-domain
# rivals that diverge on exactly the sub-domains the gold patch fixes (the
# scheme branch, the IGNORED/MISSING split) — each carrying the refinement that
# its faithful real patch fails an F2P test.

from pathlib import Path

INSTANCE = "sphinx-doc__sphinx-7985"
FLOAT_ENCODING = None  # meta.json float_encoding is null (unused)

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Anchor blocks — every one lies STRICTLY inside an # impl-start/# impl-end
# region, so same_spec is guaranteed (the frozen spec is never touched).
# ---------------------------------------------------------------------------

# --- check() impl region -------------------------------------------------
_CHECK_TOP = """    h = []   # type: List[int]
    h = [35]
    m = [109, 97, 105, 108, 116, 111, 58]  # type: List[int]
    if len(target) == 0 or starts_with(target, h) or starts_with(target, m):
        return UNCHECKED()"""

_CHECK_BRANCH = """    hp = [104, 116, 116, 112, 58]  # type: List[int]
    hsp = [104, 116, 116, 112, 115, 58]  # type: List[int]
    if not (starts_with(target, hp) or starts_with(target, hsp)):
        if scheme_present(target):
            # recognised non-verifiable leading shape: nothing to verify
            return UNCHECKED()
        else:
            if file_exists:
                return WORKING()
            else:
                if ignore_match:
                    return IGNORED()
                else:
                    return MISSING()
    return remote"""

# --- scheme_present() impl region ----------------------------------------
_SCHEME_TAIL = """    if k < 1:
        return False
    if k + 3 > n:
        return False
    res = (target[k] == 58 and target[k + 1] == 47 and target[k + 2] == 47)
    return res"""


# ===========================================================================
# SPEC CASES
# ===========================================================================
SPEC_TESTS = []

# --- 1. FRAME-MUTATION (MANDATORY: target is read-only Acc(...,1/2)) -------
# A rival that WRITES the read-only `target` before classifying. The store
# `target[0] = 58` requires FULL list_pred permission but check() holds only
# Acc(list_pred(target), 1/2). The rest of the impl is the gold impl verbatim,
# so the rejection is attributable SOLELY to the illegal write (insufficient
# permission), not to a wrong value. expect=reject.
SPEC_TESTS.append({
    "id": "frame-mutation-check-target",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap(
        _BASE, _CHECK_TOP,
        """    if len(target) > 0:
        target[0] = 58      # ILLEGAL WRITE: only Acc(list_pred(target),1/2) held
""" + _CHECK_TOP,
    ),
    "refinement": (
        "A faithful real patch that mutated `uri` (e.g. uri = ':' + uri[1:]) "
        "before classifying would change the string fed to startswith / "
        "uri_re.match and to path.exists(join(srcdir, uri)); the F2P target "
        "'path/to/notfound' would no longer hit the missing-local-file branch, "
        "so '[broken] path/to/notfound' would not appear and test_defaults "
        "(splitlines()==6) would fail. The model must forbid the write."),
    "rationale": (
        "Precondition Requires(Acc(list_pred(target), 1/2)) grants only "
        "read permission; a store target[0]=58 needs full permission, so "
        "Nagini rejects for INSUFFICIENT PERMISSION. A byte-fuzzer never "
        "tries to mutate the input — this is the #1 weakness class."),
})

# --- 2. PARTIAL-DOMAIN: collapse IGNORED into MISSING ----------------------
# Correct on every target EXCEPT the (non-web, non-scheme, absent, ignored)
# sub-domain, where it returns MISSING instead of IGNORED. Must reject on the
# IGNORED structural implication / the classify postcondition. expect=reject.
SPEC_TESTS.append({
    "id": "partial-domain-ignored-as-missing",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap(
        _BASE, _CHECK_BRANCH,
        """    hp = [104, 116, 116, 112, 58]  # type: List[int]
    hsp = [104, 116, 116, 112, 115, 58]  # type: List[int]
    if not (starts_with(target, hp) or starts_with(target, hsp)):
        if scheme_present(target):
            # recognised non-verifiable leading shape: nothing to verify
            return UNCHECKED()
        else:
            if file_exists:
                return WORKING()
            else:
                return MISSING()
    return remote""",
    ),
    "refinement": (
        "A faithful real patch that dropped the `for rex in self.to_ignore: "
        "if rex.match(uri): return 'ignored'` loop would render every absent "
        "local target 'broken' even when listed in linkcheck_ignore. "
        "test_anchors_ignored adds 'path/to/notfound' to linkcheck_ignore and "
        "expects it ignored (absent from output / status 'ignored'); a "
        "'broken' there fails that F2P test."),
    "rationale": (
        "The IGNORED implication Ensures(Implies(...and ignore_match, "
        "Result()==IGNORED())) and Result()==classify(...) both demand "
        "IGNORED on this sub-domain; returning MISSING(2) where IGNORED(3) is "
        "required => rejected. SPEC-TOO-WEAK if it verified."),
})

# --- 3. PARTIAL-DOMAIN: collapse MISSING into WORKING ----------------------
# Correct everywhere EXCEPT the (non-web, non-scheme, absent, non-ignored)
# sub-domain, where it returns WORKING instead of MISSING. This is exactly the
# F2P-discriminating case ('path/to/notfound' must be broken). expect=reject.
SPEC_TESTS.append({
    "id": "partial-domain-missing-as-working",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap(
        _BASE, _CHECK_BRANCH,
        """    hp = [104, 116, 116, 112, 58]  # type: List[int]
    hsp = [104, 116, 116, 112, 115, 58]  # type: List[int]
    if not (starts_with(target, hp) or starts_with(target, hsp)):
        if scheme_present(target):
            # recognised non-verifiable leading shape: nothing to verify
            return UNCHECKED()
        else:
            if file_exists:
                return WORKING()
            else:
                if ignore_match:
                    return IGNORED()
                else:
                    return WORKING()
    return remote""",
    ),
    "refinement": (
        "A faithful real patch returning 'working' for an absent, non-ignored "
        "local target would mark 'path/to/notfound' as working instead of "
        "broken: '[broken] path/to/notfound' would be absent and the line "
        "count would not rise to 6, so test_defaults fails. This is the exact "
        "behaviour the gold patch fixes (pre-patch returned the unclassified "
        "'local')."),
    "rationale": (
        "The MISSING implication Ensures(Implies(...and not file_exists and "
        "not ignore_match, Result()==MISSING())) and Result()==classify(...) "
        "demand MISSING(2); returning WORKING(1) => rejected."),
})

# --- 4. PARTIAL-DOMAIN: drop the scheme-shape branch -----------------------
# Treat a recognised [a-z]+:// scheme target (e.g. gopher://h) as a local
# file instead of UNCHECKED. This is the gold patch's introduced uri_re.match
# branch; dropping it diverges from classify on the scheme sub-domain.
# expect=reject.
SPEC_TESTS.append({
    "id": "partial-domain-drop-scheme-branch",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap(
        _BASE, _CHECK_BRANCH,
        """    hp = [104, 116, 116, 112, 58]  # type: List[int]
    hsp = [104, 116, 116, 112, 115, 58]  # type: List[int]
    if not (starts_with(target, hp) or starts_with(target, hsp)):
        if file_exists:
            return WORKING()
        else:
            if ignore_match:
                return IGNORED()
            else:
                return MISSING()
    return remote""",
    ),
    "refinement": (
        "A faithful real patch without the `if uri_re.match(uri): return "
        "'unchecked'` guard would treat an unsupported scheme like 'gopher://h' "
        "as a local file and report it broken/working rather than unchecked, "
        "diverging from the gold post-patch check() (G-AX confirms gopher:// is "
        "the discriminator vs the unclassified pre-patch outcome)."),
    "rationale": (
        "classify() returns UNCHECKED() when has_uri_scheme(ToSeq(target)); "
        "this rival returns WORKING/IGNORED/MISSING for such a target, so "
        "Result()==classify(...) fails => rejected."),
})

# --- 5. SUPPORTING near-miss: collapse the whole non-web branch (prepatch) -
# The pre-patch bug: the entire non-web branch returns a single unclassified
# outcome. Mirrors G-DIFF; a cheap supporting case with a real refinement.
SPEC_TESTS.append({
    "id": "collapse-nonweb-to-constant",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap(
        _BASE, _CHECK_BRANCH,
        """    hp = [104, 116, 116, 112, 58]  # type: List[int]
    hsp = [104, 116, 116, 112, 115, 58]  # type: List[int]
    if not (starts_with(target, hp) or starts_with(target, hsp)):
        return UNCHECKED()
    return remote""",
    ),
    "refinement": (
        "This is the pre-patch shape (non-web branch collapsed to one outcome). "
        "It marks every local target unchecked: 'path/to/notfound' never "
        "appears as broken, so test_defaults (splitlines()==6) fails — the "
        "exact non-resolution G-DIFF reproduces."),
    "rationale": (
        "Returning UNCHECKED(0) for an absent local file violates the MISSING "
        "implication and Result()==classify(...) (which demands MISSING(2)) "
        "=> rejected."),
})

# --- 6. PARTIAL-DOMAIN on scheme_present: off-by-one on the run length -----
# scheme_present must be has_uri_scheme: maximal [a-z] run k>=1 then '://'.
# This rival accepts k>=0 (allows an empty leading run, e.g. '://x'), which
# disagrees with has_uri_scheme on targets whose first char is not [a-z] but
# are followed by '://'. expect=reject.
SPEC_TESTS.append({
    "id": "partial-domain-scheme-empty-run",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap(
        _BASE, _SCHEME_TAIL,
        """    if k < 0:
        return False
    if k + 3 > n:
        return False
    res = (target[k] == 58 and target[k + 1] == 47 and target[k + 2] == 47)
    return res""",
    ),
    "refinement": (
        "re.compile('[a-z]+://').match requires ONE OR MORE lowercase letters; "
        "a faithful patch using '[a-z]*://' (zero-or-more) would match '://x' "
        "and mis-route a target with no scheme letters into the unchecked "
        "branch, diverging from uri_re.match (G-AX fuzzes '://x' explicitly)."),
    "rationale": (
        "has_uri_scheme demands k>=1 (lower_run>=1); accepting k==0 makes "
        "scheme_present return True where has_uri_scheme is False (e.g. '://x'), "
        "so Result()==has_uri_scheme(ToSeq(target)) fails => rejected."),
})

# --- 7. POSITIVE CONTROL (soundness): structurally-different CORRECT check -
# Reorder check()'s nested branch cascade into a flat early-return sequence
# with the IGNORED/MISSING test inverted (test the negation first). No loops
# in check()'s impl (the work is in verified helpers starts_with /
# scheme_present), so no loop invariant / lemma is at risk — this is a pure
# branch reshape that keeps the gold proof valid. MUST verify.
SPEC_TESTS.append({
    "id": "pos-control-check-flat-branches",
    "kind": "soundness",
    "expect": "verify",
    "module": _swap(
        _BASE, _CHECK_BRANCH,
        """    hp = [104, 116, 116, 112, 58]  # type: List[int]
    hsp = [104, 116, 116, 112, 115, 58]  # type: List[int]
    if starts_with(target, hp) or starts_with(target, hsp):
        return remote
    if scheme_present(target):
        # recognised non-verifiable leading shape: nothing to verify
        return UNCHECKED()
    if file_exists:
        return WORKING()
    if not ignore_match:
        return MISSING()
    return IGNORED()""",
    ),
    "rationale": (
        "Same decision cascade, branches reordered (web first via the positive "
        "guard) and the IGNORED/MISSING test inverted (not ignore_match -> "
        "MISSING first). Behaviourally identical to classify(...), so it must "
        "verify; if it could not, SPEC-TOO-STRONG."),
})

# --- 8. POSITIVE CONTROL (soundness): scheme_present tail reshaped ----------
# Keep the forward loop + its invariants + the lemma asserts byte-identical
# (front-recursive helpers require the forward direction — do NOT touch them);
# only fold the post-loop guard chain into a single boolean expression. MUST
# verify. (Guards added so all index reads stay in bounds for Nagini.)
SPEC_TESTS.append({
    "id": "pos-control-scheme-tail-boolean",
    "kind": "soundness",
    "expect": "verify",
    "module": _swap(
        _BASE, _SCHEME_TAIL,
        """    res = False
    if k >= 1 and k + 3 <= n:
        res = (target[k] == 58 and target[k + 1] == 47 and target[k + 2] == 47)
    return res""",
    ),
    "rationale": (
        "Identical post-loop predicate (k>=1 and len>=k+3 and target[k:k+3]== "
        "'://') folded into one boolean instead of two early-return guards; the "
        "loop, its invariants, and the lemma_* asserts are untouched, so the "
        "gold proof carries. Must verify; else SPEC-TOO-STRONG."),
})

# --- 9. ADMISSIBILITY: the precondition admits a normal F2P-shaped input ----
# Inside check()'s impl, before classifying, ASSERT that the read permission
# the precondition grants is usable for a representative non-empty local
# target (read target[0]); a self-read under Acc(list_pred(target),1/2) must
# succeed. The body otherwise is the gold impl verbatim. expect=verify. If the
# precondition could not establish a usable read for a normal input =>
# PRECOND-TOO-STRONG.
SPEC_TESTS.append({
    "id": "admiss-check-readable-target",
    "kind": "admissibility",
    "expect": "verify",
    "module": _swap(
        _BASE, _CHECK_TOP,
        """    if len(target) > 0:
        Assert(target[0] == target[0])   # read OK under Acc(list_pred,1/2)
""" + _CHECK_TOP,
    ),
    "rationale": (
        "An F2P-shaped target ('path/to/notfound') is a non-empty List[int]; "
        "the precondition Acc(list_pred(target),1/2) must permit reading its "
        "elements. If this read could not be established the precondition would "
        "be too strong for a legitimate input (PRECOND-TOO-STRONG)."),
})


# ===========================================================================
# AXIOM CASES
# ===========================================================================
# meta.json axioms == []. There are NO consumed @ContractOnly axioms: the two
# changed string decisions (str.startswith, re.match('[a-z]+://')) and the whole
# branch (classify) are modeled DEEPLY as A-references and validated == their
# real stdlib callees by axiom_check.py / G-AX (which already runs in the eval
# image, RC=0, over 47 boundary + 80000 fuzz inputs).
#
# We add two host/stdlib axiom-lane probes that reuse axiom_check.py's logic so
# the soundness/containment obligations are re-runnable from this manifest. The
# callees are pure stdlib (`re`, str.startswith) — no repo import needed — so
# the probes are self-contained and import only stdlib (apply_gold irrelevant;
# kept True for consistency with §4 since classify describes post-gold
# behaviour).

# Reuse the bundle's own reference oracle (read on the HOST at load time and
# embed; the runner mounts ONLY the probe at /work).
_AXC = (Path(__file__).parent / "axiom_check.py").read_text()

AXIOM_TESTS = []

# --- A1. axiom-soundness: the deep models == the real stdlib callees --------
# Run the bundle's G-AX oracle verbatim: it executes the REAL str.startswith /
# re.match('[a-z]+://') / transcribed post-patch check() and asserts the deep
# models (prefix_eq / has_uri_scheme / classify) agree on boundary + 80000
# fuzz inputs, then confirms the 4 F2P discriminators. exit 0 iff all hold.
AXIOM_TESTS.append({
    "id": "ax-sound-deep-models",
    "axiom": "prefix_eq/has_uri_scheme/classify (A-reference deep models)",
    "kind": "axiom-soundness",
    "expect": "holds",
    "apply_gold": True,
    "probe": _AXC,
    "rationale": (
        "If the deep models disagreed with the real str.startswith / "
        "re.match('[a-z]+://') / post-patch check() on any input in their "
        "domain, the A-reference would be unsound (AXIOM-UNSOUND). The oracle "
        "fuzzes ASCII-case boundaries (no IGNORECASE), '://'-near-misses, and "
        "the F2P targets, then asserts the 4 F2P discriminators vs pre-patch."),
})

# --- A2. axiom-containment: every callee-input the model can reach is in -----
# the A-reference domain. The model passes ARBITRARY List[int] code points to
# str.startswith / re.match (no Requires narrows the alphabet beyond "valid
# Unicode code points"), so the A-reference domain must cover any string. This
# probe enumerates the boundary alphabet PLUS pathological inputs (non-ASCII,
# control chars, lone surrogate-free high code points encoded as text) the
# model could reach and asserts the deep model equals the real callee on each —
# i.e. the A-reference is not mis-scoped (no caller-reachable input is outside
# the covered domain).
_CONTAINMENT_PROBE = r'''
import re
import sys

URI_RE = re.compile('[a-z]+://')


def prefix_eq(s, lit):
    return s[:len(lit)] == lit


def lower_run(s):
    k = 0
    while k < len(s) and 'a' <= s[k] <= 'z':
        k += 1
    return k


def has_uri_scheme(s):
    k = lower_run(s)
    return (k >= 1 and len(s) >= k + 3 and s[k] == ':'
            and s[k + 1] == '/' and s[k + 2] == '/')


SCHEME_LITERALS = ['#', 'mailto:', 'http:', 'https:', 'ftp:']

# Inputs the MODEL can actually reach: target is any List[int] of Unicode code
# points (the only Requires is list_pred permission, no alphabet restriction).
# So the A-reference must cover ARBITRARY strings, incl. non-ASCII, control
# chars, embedded NULs, and code points around the BMP/astral boundary.
reachable = [
    "", "#", "#frag", "mailto:x", "http://a", "https://b", "ftp://c",
    "a://b", "://x", "A://b", "1://b", "scheme://h", "Scheme://h",
    # non-ASCII / control / boundary code points (model carries any int):
    "\x00://x", "\t\n://", "é://x", "café://h",
    "AB://", "￿", "a\U0001F600://", "\U0001F600://x",
    "://", "abc​://", "あ://",   # CJK lead -> not [a-z]
    "z" * 200 + "://" + "x" * 50,                 # long maximal run
]

mism = 0
for s in reachable:
    for lit in SCHEME_LITERALS:
        if prefix_eq(s, lit) != s.startswith(lit):
            print("CONTAINMENT FAIL startswith s=%r lit=%r" % (s, lit))
            mism += 1
    if has_uri_scheme(s) != (URI_RE.match(s) is not None):
        print("CONTAINMENT FAIL scheme s=%r model=%r real=%r"
              % (s, has_uri_scheme(s), URI_RE.match(s) is not None))
        mism += 1

if mism:
    print("CONTAINMENT: %d caller-reachable input(s) outside the covered "
          "A-reference domain (AXIOM-TOO-WEAK-FOR-CALLER)" % mism)
    sys.exit(1)
print("CONTAINMENT OK: %d caller-reachable inputs (incl. non-ASCII / control / "
      "astral / long-run) all match the real callees; A-reference covers the "
      "full reachable domain." % len(reachable))
sys.exit(0)
'''

AXIOM_TESTS.append({
    "id": "ax-cover-reachable-domain",
    "axiom": "prefix_eq/has_uri_scheme (A-reference deep models)",
    "kind": "axiom-containment",
    "expect": "covered",
    "apply_gold": True,
    "probe": _CONTAINMENT_PROBE,
    "rationale": (
        "The model's only Requires on target is list_pred permission — no "
        "alphabet restriction — so it can pass ANY Unicode code-point string to "
        "the A-reference callees. The probe checks the deep models equal the "
        "real str.startswith / re.match on non-ASCII, control, astral, and "
        "long-run inputs the model can reach; a reachable input where they "
        "disagree would be AXIOM-TOO-WEAK-FOR-CALLER."),
})
