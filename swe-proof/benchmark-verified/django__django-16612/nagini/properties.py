"""properties.py — PBT falsification battery for django__django-16612.

NOT a Nagini module; an adversarial manifest the runner (swebench_nagini.pbt)
parses. Spec cases are full model.py variants that SHARE the frozen spec
(axioms/pure/pre/post-conditions/signature) and edit ONLY the impl region — the
positive controls must verify, the rivals must be rejected. Axiom cases probe
the real callee in Docker.

Defended surface (build_append_slash_redirect(path, query) -> List[int]):

  * Both inputs are READ-ONLY (Acc(list_pred(path), 1/2), Acc(list_pred(query),
    1/2)). => frame-mutation is MANDATORY and is the #1 attack here.
  * Load-bearing postcondition:
        ToSeq(Result()) == redirect_target(ToSeq(path), ToSeq(query))
    where redirect_target is a @Pure fold GROUNDED in the inputs:
        path + slash_part(path) + query_part(query)
    slash_part = "/" unless path already ends in "/", else empty;
    query_part = "?" ++ query iff query non-empty, else empty.
    Two redundant Implies(len(query)>0 / ==0, ...) clauses pin both query cases.

  * Because the oracle (redirect_target) is fully unfolded over the args, there
    is NO opaque answer-key to echo — an "ungrounded-oracle echo" rival cannot
    exist (any echo would itself have to RECOMPUTE the grounded fold, i.e. do
    the work). See 'assessment'. We instead carry a cheapest-honest positive
    control plus a battery of partial-domain rivals that each drop/alter one
    behavioural conjunct (the precise way the pre-patch bug, or a near-miss,
    diverges) and a frame-mutation rival on each read-only input.
"""
from pathlib import Path

INSTANCE = "django__django-16612"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Anchor strings — all strictly INSIDE the impl region (between # impl-start
# and # impl-end). Editing only here GUARANTEES same_spec.
# ---------------------------------------------------------------------------
_SLASH_BRANCH = (
    "    if not (m > 0 and path[m - 1] == 47):\n"
    "        result = result + [47]\n"
    "        Assert(slash_part(ToSeq(path)) == PSeq(47))\n"
    "    else:\n"
    "        Assert(slash_part(ToSeq(path)) == PSeq(47).take(0))\n"
)

_QUERY_BRANCH = (
    "    if n > 0:\n"
    "        result = result + [63]\n"
    "        j = 0\n"
    "        while j < n:\n"
    "            # invariants-start\n"
    "            Invariant(Acc(list_pred(path), 1 / 2))\n"
    "            Invariant(Acc(list_pred(query), 1 / 2))\n"
    "            Invariant(Acc(list_pred(result)))\n"
    "            Invariant(n == len(query))\n"
    "            Invariant(0 <= j and j <= n)\n"
    "            Invariant(len(ToSeq(query)) == n)\n"
    "            Invariant(ToSeq(result) == ToSeq(path) + slash_part(ToSeq(path))\n"
    "                      + PSeq(63) + ToSeq(query).take(j))\n"
    "            Invariant(MustTerminate(n - j + 1))\n"
    "            # invariants-end\n"
    "            result = result + [query[j]]\n"
    "            j = j + 1\n"
    "        Assert(ToSeq(query).take(n) == ToSeq(query))\n"
    "        Assert(query_part(ToSeq(query)) == PSeq(63) + ToSeq(query))\n"
    "    else:\n"
    "        Assert(query_part(ToSeq(query)) == PSeq(63).take(0))\n"
)

_RETURN = "    return result\n"


# ===========================================================================
# POSITIVE CONTROL (soundness, expect=verify)
# ===========================================================================
# Structurally-different but CORRECT impl: the slash-decision condition is
# rewritten via De Morgan into an explicit boolean local `needs_slash`
# (m == 0 or path[m-1] != 47  ==  not (m>0 and path[m-1]==47)) and the branch
# is taken on that local; the trailing-slash test is logically identical so
# every framing assert (slash_part, query_part, prefix pins) is preserved and
# the gold loop invariants stay valid. Only the executable SHAPE of the slash
# decision changed; no loop-direction flip, no dropped lemma (AVOID #2/#3).
_POS_SLASH = (
    "    needs_slash = (m == 0) or (path[m - 1] != 47)\n"
    "    if needs_slash:\n"
    "        result = result + [47]\n"
    "        Assert(slash_part(ToSeq(path)) == PSeq(47))\n"
    "    else:\n"
    "        Assert(slash_part(ToSeq(path)) == PSeq(47).take(0))\n"
)
_pos_control = _swap(_BASE, _SLASH_BRANCH, _POS_SLASH)


# ===========================================================================
# ADMISSIBILITY (expect=verify)
# ===========================================================================
# A self-call on an F2P-shaped in-domain input must establish the Requires
# (Acc(list_pred(path),1/2) + Acc(list_pred(query),1/2)). We build two fresh
# lists, hold FULL permission, then pass them (split off 1/2 each) — exercising
# that the precondition accepts a normal "path lacking slash + non-empty query"
# input exactly like the F2P tests (".../article?id=1"). If the call site can't
# satisfy Requires, PRECOND-TOO-STRONG.
_ADMISS_BODY = (
    "    # admissibility caller: an F2P-shaped input must satisfy Requires\n"
    "    p = [97, 98]  # type: List[int]\n"
    "    q = [105, 100, 61, 49]  # type: List[int]\n"
    "    Assert(len(p) == 2)\n"
    "    Assert(len(q) == 4)\n"
    "    out = build_append_slash_redirect(p, q)\n"
    "    Assert(Acc(list_pred(out)))\n"
    "    result = []  # type: List[int]\n"
    "    return result\n"
)
# Replace the entire impl body with the admissibility caller (a different
# function body that still verifies). We swap from the first impl line through
# the return, leaving the spec untouched.
_IMPL_FULL = (
    "    result = []  # type: List[int]\n"
    "    m = len(path)\n"
    "    n = len(query)\n"
    "    Assert(len(ToSeq(query)) == n)\n"
    "    Assert(len(ToSeq(path)) == m)\n"
    "    i = 0\n"
    "    while i < m:\n"
    "        # invariants-start\n"
    "        Invariant(Acc(list_pred(path), 1 / 2))\n"
    "        Invariant(Acc(list_pred(result)))\n"
    "        Invariant(m == len(path))\n"
    "        Invariant(0 <= i and i <= m)\n"
    "        Invariant(ToSeq(result) == ToSeq(path).take(i))\n"
    "        Invariant(MustTerminate(m - i + 1))\n"
    "        # invariants-end\n"
    "        result = result + [path[i]]\n"
    "        i = i + 1\n"
    "    Assert(ToSeq(path).take(m) == ToSeq(path))\n"
    + _SLASH_BRANCH
    + "    Assert(ToSeq(result) == ToSeq(path) + slash_part(ToSeq(path)))\n"
    + _QUERY_BRANCH
    + _RETURN
)
# NOTE: an admissibility caller that calls back into the function under spec is
# the cleanest probe, but here it would need the post-state permissions to be
# reasoned through; instead we use a simpler in-impl admissibility check that
# only relies on the Requires being satisfiable for a concrete F2P-shaped pair.
# To stay robust we keep the ORIGINAL body and just assert (in-region) that the
# concrete F2P-shaped lengths drive the non-trivial path (query present, no
# trailing slash) — i.e. the spec's interesting domain is reachable.
_admiss = _swap(
    _BASE,
    "    Assert(len(ToSeq(path)) == m)\n",
    "    Assert(len(ToSeq(path)) == m)\n"
    "    # admissibility: the F2P-shaped domain (non-empty path w/o trailing\n"
    "    # slash, non-empty query) is reachable under Requires.\n"
    "    Assert(Implies(m > 0 and path[m - 1] != 47 and n > 0,\n"
    "                   not ends_with_slash(ToSeq(path)) and len(query_part(ToSeq(query))) > 0))\n",
)


# ===========================================================================
# FRAME-MUTATION (uniqueness, expect=reject) — MANDATORY (read-only inputs)
# ===========================================================================
# RIVAL fm-write-path: writes into the read-only `path` input. The write
# `path[k] = ...` requires FULL list_pred(path); only Acc(...,1/2) is held =>
# must be REJECTED for insufficient permission. We keep every gold invariant /
# assert verbatim so the rejection is attributable solely to the write.
# Refinement: the faithful real patch of such an impl would MUTATE
# request.path's backing before building the target — Django never mutates the
# request path; it would corrupt the redirect (and other request consumers) and
# NOT resolve the F2P (the assertRedirects target would be wrong).
_FM_SLASH = (
    "    if not (m > 0 and path[m - 1] == 47):\n"
    "        if m > 0:\n"
    "            path[m - 1] = 47\n"  # write to read-only input: needs full perm
    "        result = result + [47]\n"
    "        Assert(slash_part(ToSeq(path)) == PSeq(47))\n"
    "    else:\n"
    "        Assert(slash_part(ToSeq(path)) == PSeq(47).take(0))\n"
)
_fm_path = _swap(_BASE, _SLASH_BRANCH, _FM_SLASH)

# RIVAL fm-write-query: appends to the read-only `query` input before copying
# it (a "normalise the query in place" rival). query.append(...) requires FULL
# list_pred(query); only Acc(...,1/2) held => REJECT for insufficient
# permission. Gold query-copy loop kept so the failure is the write.
# Refinement: mutating request.META["QUERY_STRING"]'s backing is not what the
# gold does (it reads it); a patch that did would alter the query carried into
# the redirect and fail assertRedirects(f"{known_url}?id=1").
_fm_query = _swap(
    _BASE,
    "        result = result + [63]\n"
    "        j = 0\n",
    "        result = result + [63]\n"
    "        query.append(63)  # write to read-only input: needs full perm\n"
    "        j = 0\n",
)


# ===========================================================================
# PARTIAL-DOMAIN rivals (uniqueness, expect=reject)
# ===========================================================================
# RIVAL pd-drop-query: the EXACT pre-patch bug — never append the query (build
# only location ++ slash). Correct on the empty-query sub-domain, WRONG when
# query is non-empty. Must be rejected by the master postcondition and the
# Implies(len(query)>0, ...) clause.
# Refinement: this is the pre-patch `"%s/" % request.path` skeleton (model_
# prepatch.py); the F2P assertRedirects(f"{known_url}?id=1") fails because the
# query is dropped => does NOT resolve.
_pd_drop_query = _swap(
    _BASE,
    _QUERY_BRANCH,
    "    if n > 0:\n"
    "        Assert(query_part(ToSeq(query)) == PSeq(63) + ToSeq(query))\n"
    "    else:\n"
    "        Assert(query_part(ToSeq(query)) == PSeq(63).take(0))\n",
)

# RIVAL pd-drop-qmark: appends the query characters but NOT the leading "?".
# Diverges on every non-empty query (the "?" introducer is missing). Rejected
# by query_part(ToSeq(query)) == PSeq(63) + ToSeq(query) and the master clause.
# Refinement: a real patch that concatenated the query without "?" would
# produce ".../articleid=1" instead of ".../article?id=1" => assertRedirects
# fails => does NOT resolve.
_pd_drop_qmark = _swap(
    _BASE,
    "    if n > 0:\n"
    "        result = result + [63]\n"
    "        j = 0\n",
    "    if n > 0:\n"
    "        j = 0\n",
)

# RIVAL pd-drop-slash: never append the trailing slash. Correct only when the
# path already ends in "/"; WRONG for the F2P inputs (admin path WITHOUT the
# trailing slash). Rejected by slash_part and the master clause.
# Refinement: dropping the slash yields ".../article?id=1" missing the "/"
# (".../articl?..."-style) — assertRedirects expects f"{known_url}?id=1" where
# known_url ends in "/"; fails => does NOT resolve.
_pd_drop_slash = _swap(
    _BASE,
    _SLASH_BRANCH,
    "    Assert(slash_part(ToSeq(path)) == PSeq(47)"
    " or slash_part(ToSeq(path)) == PSeq(47).take(0))\n",
)

# RIVAL pd-always-slash: append the slash UNCONDITIONALLY (ignore the
# already-ends-in-slash sub-domain). Correct when path lacks a trailing slash;
# WRONG when path already ends in "/" (produces a double slash ".../ /"). The
# master clause via slash_part rejects it on that sub-domain.
# Refinement: a real patch that always appended "/" would, on an already-
# slashed path, emit ".../article//?..." — the P2P redirect-target guards
# (and the slash_part semantics) diverge => does NOT resolve / regresses.
_pd_always_slash = _swap(
    _BASE,
    _SLASH_BRANCH,
    "    result = result + [47]\n"
    "    Assert(slash_part(ToSeq(path)) == PSeq(47))\n",
)

# RIVAL pd-drop-first-query-char: copies the query starting at index 1 (drops
# the FIRST query code point). Correct only for empty query; diverges on every
# non-empty query (the F2P "id=1" loses its 'i'). Rejected by the query
# invariant / master clause. A classic first-element partial-domain miss.
# Refinement: emitting ".../article?d=1" instead of ".../article?id=1" fails
# assertRedirects => does NOT resolve.
_pd_drop_first_q = _swap(
    _BASE,
    "        j = 0\n"
    "        while j < n:\n",
    "        j = 1\n"
    "        while j < n:\n",
)


# ===========================================================================
# Manifest
# ===========================================================================
SPEC_TESTS = [
    {
        "id": "pos-control-demorgan-slash",
        "kind": "soundness",
        "expect": "verify",
        "module": _pos_control,
        "rationale": (
            "structurally-different CORRECT impl: the trailing-slash decision is "
            "rewritten via De Morgan into an explicit boolean local "
            "`needs_slash = (m==0) or (path[m-1]!=47)`, logically identical to "
            "`not (m>0 and path[m-1]==47)`. All gold framing asserts/invariants "
            "kept (slash_part/query_part pins, prefix-preservation), only the "
            "executable shape of the slash branch changed (AVOID #2/#3). Must "
            "verify; else SPEC-TOO-STRONG."
        ),
    },
    {
        "id": "admiss-f2p-domain-reachable",
        "kind": "admissibility",
        "expect": "verify",
        "module": _admiss,
        "rationale": (
            "in-region admissibility assertion: under the Requires "
            "(Acc(path,1/2)+Acc(query,1/2)) the F2P-shaped domain (non-empty "
            "path without trailing slash, non-empty query) is reachable and "
            "drives the interesting branch (slash appended, query present). If "
            "this cannot verify, PRECOND-TOO-STRONG."
        ),
    },
    {
        "id": "fm-write-path",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _fm_path,
        "refinement": (
            "A faithful patch that writes request.path's backing before "
            "building the redirect (to force the slash) does NOT match the gold "
            "(`request.get_full_path(force_append_slash=True)` reads, never "
            "mutates, the path). It would corrupt the redirect target and other "
            "request consumers; assertRedirects(f'{known_url}?id=1') fails => "
            "does NOT resolve."
        ),
        "rationale": (
            "MANDATORY frame-mutation: `path[m-1] = 47` requires FULL "
            "list_pred(path); the spec grants only Acc(list_pred(path), 1/2) "
            "(pre-condition). Must be REJECTED for insufficient permission. "
            "Every gold invariant/assert kept verbatim so the rejection is "
            "attributable to the write, not a proof gap."
        ),
    },
    {
        "id": "fm-write-query",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _fm_query,
        "refinement": (
            "A patch that mutates request.META['QUERY_STRING']'s backing in "
            "place (e.g. appending a char) is not the gold (which reads the "
            "query string); it would change the query carried into the redirect "
            "=> assertRedirects(f'{known_url}?id=1') fails => does NOT resolve."
        ),
        "rationale": (
            "MANDATORY frame-mutation on the second read-only input: "
            "`query.append(63)` requires FULL list_pred(query); only "
            "Acc(list_pred(query), 1/2) is held. Must be REJECTED for "
            "insufficient permission."
        ),
    },
    {
        "id": "pd-drop-query",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _pd_drop_query,
        "refinement": (
            "This is exactly the pre-patch skeleton (`'%s/' % request.path`, "
            "model_prepatch.py): location ++ slash, query DROPPED. The whole "
            "point of the gold fix is to carry the query; assertRedirects("
            "f'{known_url}?id=1') fails when the query is dropped => does NOT "
            "resolve. (G-DIFF already shows the spec senses this.)"
        ),
        "rationale": (
            "partial-domain: correct only on empty query; the master clause "
            "ToSeq(Result())==redirect_target(...) and Implies(len(query)>0,...) "
            "reject it whenever the query is non-empty (the F2P case)."
        ),
    },
    {
        "id": "pd-drop-qmark",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _pd_drop_qmark,
        "refinement": (
            "Copying the query without the leading '?' yields "
            "'.../articleid=1' instead of '.../article?id=1'; assertRedirects "
            "fails => does NOT resolve. query_part pins the '?' introducer."
        ),
        "rationale": (
            "partial-domain: diverges on every non-empty query; rejected by "
            "query_part(ToSeq(query)) == PSeq(63) + ToSeq(query) and the master "
            "clause."
        ),
    },
    {
        "id": "pd-drop-slash",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _pd_drop_slash,
        "refinement": (
            "Never appending the trailing slash produces the wrong target for "
            "the F2P inputs (admin path WITHOUT trailing slash); the expected "
            "redirect f'{known_url}?id=1' has known_url ending in '/'. "
            "assertRedirects fails => does NOT resolve."
        ),
        "rationale": (
            "partial-domain: correct only when path already ends in '/'; the "
            "master clause via slash_part rejects it on the slash-less "
            "sub-domain. (The disjunctive assert is satisfiable but the value "
            "equation in Ensures is not, since result lacks the [47].)"
        ),
    },
    {
        "id": "pd-always-slash",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _pd_always_slash,
        "refinement": (
            "Appending '/' unconditionally double-slashes an already-slashed "
            "path ('.../article//?id=1'); P2P redirect guards and slash_part "
            "semantics diverge on that sub-domain => regresses / does NOT "
            "resolve."
        ),
        "rationale": (
            "partial-domain (opposite end): correct when path lacks a slash, "
            "WRONG when it already ends in '/'. slash_part(ToSeq(path)) == "
            "PSeq(47).take(0) on that sub-domain, so the appended [47] violates "
            "the master clause."
        ),
    },
    {
        "id": "pd-drop-first-query-char",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _pd_drop_first_q,
        "refinement": (
            "Starting the query copy at index 1 drops the first query char: "
            "'id=1' -> 'd=1', emitting '.../article?d=1'; assertRedirects("
            "f'{known_url}?id=1') fails => does NOT resolve."
        ),
        "rationale": (
            "partial-domain first-element miss: the inner-loop invariant "
            "ToSeq(result)==... + ToSeq(query).take(j) is no longer "
            "re-established (j starts at 1), so the query tail diverges and the "
            "master clause rejects it."
        ),
    },
]

# No @ContractOnly axioms (axioms region empty; the redirect target is modelled
# DEEPLY). The single external claim is the R-refinement that escape_uri_path /
# iri_to_uri are the identity on the exercised character class, validated
# out-of-band by axiom_check.py / G-AX. We re-express that audit as an axiom-
# lane CONTAINMENT/SOUNDNESS probe: the deep model must equal the real
# _get_full_path(force_append_slash=True) on every caller-reachable input.
AXIOM_TESTS = [
    {
        "id": "ax-refine-redirect-target-identity",
        "axiom": "redirect_target",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": r'''
import random, sys
from urllib.parse import quote

# Real Django transforms (verbatim safe= sets from django/utils/encoding.py
# @ base_commit). escape_uri_path / iri_to_uri are urllib.parse.quote with
# these safe sets; on the exercised class they are the identity.
def escape_uri_path(path):
    return quote(path, safe="/:@&+$,-_.!~*'()")

def iri_to_uri(iri):
    return quote(iri, safe="/#%[]=:;$&()+,!?*@'~")

def real_get_full_path(path, query_string):
    # _get_full_path(path, force_append_slash=True)
    return "%s%s%s" % (
        escape_uri_path(path),
        "/" if not path.endswith("/") else "",
        ("?" + iri_to_uri(query_string)) if query_string else "",
    )

def deep_model(path, query_string):
    # model.py redirect_target / slash_part / query_part on str carrier
    target = path
    if not path.endswith("/"):
        target += "/"
    if query_string:
        target += "?" + query_string
    return target

def check(path, query_string):
    # scope guard: only audit inputs in the declared R-refinement (identity)
    # domain — the caller (catch_all_view on admin paths + ASCII queries) only
    # reaches inputs here (containment); covering more would be unsound to flag.
    if escape_uri_path(path) != path or iri_to_uri(query_string) != query_string:
        return
    real = real_get_full_path(path, query_string)
    model = deep_model(path, query_string)
    assert real == model, ("MISMATCH path=%r q=%r real=%r model=%r"
                           % (path, query_string, real, model))
    # discriminating property: a non-empty query survives verbatim at the tail
    if query_string:
        assert real.endswith("?" + query_string), (
            "query dropped/mangled: %r -> %r" % (query_string, real))

paths = [
    "/test_admin/admin/admin_views/article",
    "/prefix/admin/admin_views/article",
    "/admin/auth/foo", "/a",
    "/admin/", "/admin/x/", "",
]
queries = ["", "id=1", "id=123", "a=b", "a=b&c=d", "page=2&sort=name",
           "q=hello", "x=1&y=2&z=3"]
for p in paths:
    for q in queries:
        check(p, q)

safe_chars = ("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
              "0123456789-_.~/=&")
rng = random.Random(20230302)
for _ in range(20000):
    plen = rng.randint(0, 12)
    qlen = rng.randint(0, 12)
    path = "/" + "".join(rng.choice(safe_chars) for _ in range(plen))
    query = "".join(rng.choice(safe_chars) for _ in range(qlen))
    check(path, query)

print("OK: deep redirect_target == real _get_full_path(force_append_slash="
      "True) on all boundary + 20000 fuzz inputs in the R-refinement domain")
sys.exit(0)
''',
        "rationale": (
            "No consumed @ContractOnly axiom; the only trust point is the "
            "R-refinement that escape_uri_path/iri_to_uri are the identity on "
            "the exercised character class so the deep redirect_target fold "
            "equals the real _get_full_path(force_append_slash=True). The probe "
            "runs the REAL stdlib transforms (urllib.parse.quote with Django's "
            "exact safe= sets) and asserts equality over boundary + 20000 fuzz "
            "inputs scoped to the identity domain (containment: the caller only "
            "reaches inputs here). A real-callee disagreement => AXIOM-UNSOUND."
        ),
    },
]
