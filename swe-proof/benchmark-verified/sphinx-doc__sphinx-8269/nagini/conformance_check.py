#!/usr/bin/env python3
"""G-CONF differential conformance check for sphinx-doc__sphinx-8269 (nagini).

Refutes (never proves) the refinement leg: does the frozen MODEL agree with the
REAL patched repository code it claims to model?

SHADOW
------
The model IS Python, so the shadow is the `# impl-start` / `# impl-end` region
of `model.py` copied VERBATIM (there are no contract calls inside that region --
`Requires` lives in the pre-conditions region -- so nothing had to be stripped;
the `@Pure` code helpers it calls are copied below minus their decorators). No
restructuring, no renaming: `shadow_classify_fragment_link` below is a
byte-for-byte copy of the impl region, indentation aside.

The region's one `@ContractOnly` callee, `raise_on_error_status(status)`, has no
body to copy. Per the contract it is therefore wired to the REAL repo callee it
axiomatizes -- `requests.models.Response.raise_for_status()` (mapping.md §1/§3.1:
the bound method the gold patch ADDS a call to at
`sphinx/builders/linkcheck.py:169` post-patch) -- invoked on a genuine
`requests.models.Response` carrying the generated `status_code`, with the
library's `HTTPError` translated to the model's `TransportError`. So the axiom is
EXERCISED here rather than assumed: if `raise_for_status` did not partition on
[400,600) the shadow would diverge from the oracle at the boundary.

ORACLE -- the real patched function, CALLED, not transliterated
--------------------------------------------------------------
`CheckExternalLinksBuilder.check_thread.check_uri` (mapping.md §1;
`sphinx/builders/linkcheck.py:136` at base_commit, the
`if anchor and self.app.config.linkcheck_anchors:` fragment branch at :165-172
post-patch plus the shared `except HTTPError` / `except Exception` dispatch at
:186-199). The gate has already `git apply`-ed the gold patch to /testbed, so
the source on disk is the PATCHED source.

`check_uri` is a closure nested inside `check_thread`, so it is not importable by
name. Rather than transliterate it (which would test this file's reading of the
patch instead of the patch), this script EXTRACTS ITS REAL SOURCE TEXT from the
patched `sphinx/builders/linkcheck.py` on disk -- located structurally via `ast`
(ClassDef `CheckExternalLinksBuilder` -> FunctionDef `check_thread` -> nested
FunctionDef `check_uri`), `ast.get_source_segment`, no pattern text hard-coded --
and `exec`s that exact text with the closure variables (`self`, `uri`, `kwargs`,
`get_request_headers`, likewise extracted) bound to in-process stand-ins. Every
executed statement is the repository's own, including the real `check_anchor`
document scan, the real `raise Exception(__("Anchor '%s' not found"))`, the real
`raise_for_status` gate and the real three-arm `except HTTPError` dispatch.

The only stand-in is the network: the module-global `requests` name (i.e.
`sphinx.util.requests`, a thin wrapper over the `requests` package) is replaced
by an object whose `.get`/`.head` return a genuine `requests.models.Response`
with the generated `status_code`, `url == req_url` and a real HTML body that
either does or does not contain the `#anchor` id. That is the input bridge, not
a behavioural substitution -- nothing in the classification logic is replaced.
Startup assertions refuse to run unless the extracted text really contains the
patch's gate inside the fragment branch AND that gate precedes the
`check_anchor` call (so a mis-applied patch is an error, never a silent pass),
and unless no real network module leaked into the namespace.

TYPE BRIDGE (mapping.md §2, inverted)
-------------------------------------
Forward (model -> repo): `status: int` is the identity on `response.status_code`;
`fragment_present: bool` becomes a response BODY containing (True) or lacking
(False) a tag whose `id` equals the anchor, so the real `check_anchor` derives
the bit itself. Backward (repo -> model): the returned `(status, info, code)` is
abstracted to the model's `(status-class, datum-kind)` pair --
`'working'/'broken'/'ignored'` -> `WORKING/FAILED/IGNORED`, and `info` is
classified BY ORIGIN, comparing it for identity against the strings the two
sources would actually produce for this very response (the real
`str(HTTPError)` obtained from the real `raise_for_status`, and the real
`__("Anchor '%s' not found") % anchor`), with `''`/`' - unauthorized'` ->
`DATUM_NONE`. Any status class or info string not accounted for by that map is
reported as a disagreement, not silently bucketed.

`response.url` is held equal to `req_url` because the redirect sub-case is
governed by a dimension OUTSIDE the modeled input space `(status,
fragment_present)` (refinement.md A7); it is not reachable by any generated
input and so cannot hide a divergence in what IS modeled.

INPUT DOMAIN
------------
The model's only precondition is `MustTerminate(2)` -- a termination obligation
with no value content -- so EVERY `(status: int, fragment_present: bool)` pair
satisfies the Requires and the domain needs no narrowing. Boundary cases come
first: the exact F2P shape (500, fragment absent -> must report the transport
datum, not the fragment-absent one), its fragment-present twin, both edges of
the error window (399/400 and 599/600), the two specially-dispatched statuses
401/503, informational/success/redirect-range statuses, 429 (no rate-limit
branch exists at this commit), zero, negatives and extreme magnitudes -- each
crossed with both fragment bits, so all five impl arms (TransportError/401,
TransportError/503, TransportError/else, FragmentAbsent, fall-through) are
taken. Then seeded fuzz over a wide integer range, half of it drawn from a
boundary-biased pool, fills the count to >= 1e5.

Pinned seed: 8269 (recorded in mapping.md §G-CONF, and shared with the velvet /
lean siblings). Exit 0 iff zero disagreements. stdlib + the `requests` package
(a hard dependency of sphinx, and the very package the patch calls).
"""
import ast
import inspect
import json
import random
import sys
import textwrap

SEED = 8269
N_FUZZ = 100000

REQ_URL = "http://localhost:7777/"
URI = "http://localhost:7777/#anchor"
ANCHOR = "anchor"
REASON = "Internal Server Error"


# =============================================================================
# SHADOW -- model.py, contracts stripped.
# =============================================================================

# --- the two exception classes of model.py (mapping.md §2: user-defined
#     stand-ins for requests.exceptions.HTTPError and the builtin Exception) ---

class TransportError(Exception):
    pass


class FragmentAbsent(Exception):
    pass


# --- model.py `# pure-start` .. `# pure-end`, decorators dropped -------------

def is_error_status(status):
    """Copied for completeness; the impl region never calls it (it appears only
    inside `Ensures`), and the shadow must NOT use it in place of the real gate."""
    return 400 <= status and status < 600


def WORKING():
    return 0


def FAILED():
    return 1


def IGNORED():
    return 2


def DATUM_NONE():
    return 0


def DATUM_TRANSPORT():
    return 1


def DATUM_FRAGMENT_ABSENT():
    return 2


# --- the @ContractOnly callee: no body to copy, so call the REAL repo callee --

def raise_on_error_status(status):
    """model.py's `@ContractOnly def raise_on_error_status`. Axiomatizes
    `requests.models.Response.raise_for_status()` (mapping.md §3.1). Bodyless in
    the model, so here it CALLS that real method on a real Response carrying
    `status`, mapping the library's HTTPError onto the model's TransportError."""
    import requests
    from requests.exceptions import HTTPError
    response = requests.models.Response()
    response.status_code = status
    response.url = REQ_URL
    response.reason = REASON
    try:
        response.raise_for_status()          # REAL repo callee
    except HTTPError:
        raise TransportError()


# --- model.py `# impl-start` .. `# impl-end`, VERBATIM ------------------------

def shadow_classify_fragment_link(status, fragment_present):
    # impl-start
    try:
        # Read the whole document and obtain the fragment verdict.
        found = fragment_present
        # The transport-status gate is consulted BEFORE acting on the verdict.
        raise_on_error_status(status)
        if not found:
            raise FragmentAbsent()
    except TransportError:
        if status == 401:
            return (WORKING(), DATUM_NONE())
        elif status == 503:
            return (IGNORED(), DATUM_TRANSPORT())
        else:
            return (FAILED(), DATUM_TRANSPORT())
    except FragmentAbsent:
        return (FAILED(), DATUM_FRAGMENT_ABSENT())
    return (WORKING(), DATUM_NONE())
    # impl-end


# =============================================================================
# ORACLE -- the REAL patched check_uri, extracted from the patched source.
# =============================================================================

def _make_response(status, fragment_present):
    """Type bridge, forward direction: a genuine requests.models.Response
    carrying `status` and a real HTML body from which the REAL `check_anchor`
    derives the `fragment_present` bit itself."""
    import requests
    response = requests.models.Response()
    response.status_code = status
    response.url = REQ_URL
    response.reason = REASON
    if fragment_present:
        body = ("<html><body><h1 id=\"%s\">t</h1><p>body</p></body></html>"
                % ANCHOR)
    else:
        body = "<html><body><h1 id=\"other\">t</h1><p>body</p></body></html>"
    response._content = body.encode("utf-8")
    response._content_consumed = True
    response.encoding = "utf-8"
    response.history = []
    return response


class _NoNetwork(object):
    """Stands in for the module-global `requests` name inside check_uri (i.e.
    `sphinx.util.requests`). Returns the bridged Response instead of opening a
    socket; performs no classification of its own."""

    def __init__(self):
        self.status = 200
        self.fragment_present = True

    def get(self, url, **kwargs):
        return _make_response(self.status, self.fragment_present)

    def head(self, url, **kwargs):
        return _make_response(self.status, self.fragment_present)


class _Config(object):
    linkcheck_anchors = True          # the F2P test root sets this True
    linkcheck_request_headers = {}    # type: dict
    linkcheck_timeout = None
    linkcheck_retries = 1
    tls_verify = False
    user_agent = None


class _App(object):
    def __init__(self):
        self.config = _Config()


class _Builder(object):
    """The `self` closure variable check_uri reads: anchors_ignore / auth /
    config / app.config, exactly as the F2P test root configures them."""

    def __init__(self):
        self.app = _App()
        self.config = self.app.config
        self.anchors_ignore = []
        self.auth = []


def _extract_nested_source(module, class_name, outer, names):
    """Return {name: source text} for functions nested in
    `class_name.outer`, located structurally (no pattern text hard-coded)."""
    path = inspect.getsourcefile(module)
    with open(path, encoding="utf-8") as fh:
        source = fh.read()
    tree = ast.parse(source)
    cls = None
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            cls = node
            break
    if cls is None:
        raise RuntimeError("class %s not found in %s" % (class_name, path))
    fn = None
    for node in cls.body:
        if isinstance(node, ast.FunctionDef) and node.name == outer:
            fn = node
            break
    if fn is None:
        raise RuntimeError("%s.%s not found in %s" % (class_name, outer, path))
    out = {}
    for node in fn.body:
        if isinstance(node, ast.FunctionDef) and node.name in names:
            out[node.name] = textwrap.dedent(
                ast.get_source_segment(source, node))
    missing = set(names) - set(out)
    if missing:
        raise RuntimeError("nested defs %s not found in %s.%s"
                           % (sorted(missing), class_name, outer))
    return path, out


def build_oracle():
    """Exec the REAL patched check_uri source with its closure bound to the
    in-process stand-ins. Returns (call, net, path, source)."""
    import sphinx.builders.linkcheck as linkcheck

    path, srcs = _extract_nested_source(
        linkcheck, "CheckExternalLinksBuilder", "check_thread",
        ("check_uri", "get_request_headers"))
    body = srcs["check_uri"]

    # --- refuse to run against anything but the patched fragment branch ------
    flag = "linkcheck_anchors"
    marker = body.find(flag)
    if marker < 0:
        raise RuntimeError("no linkcheck_anchors fragment branch in check_uri "
                           "source at %s" % path)
    # start past the flag name itself: `linkcheck_anchors` ends with the
    # substring `check_anchor`, which would otherwise match as the scan call.
    tail = body[marker + len(flag):]
    i_gate = tail.find("raise_for_status")
    i_scan = tail.find("check_anchor(")
    if i_scan < 0:
        raise RuntimeError("no check_anchor call in the fragment branch (%s)" % path)
    if i_gate < 0 or i_gate > i_scan:
        raise RuntimeError(
            "the patched transport-status gate is absent from (or follows the "
            "document scan in) the fragment branch of check_uri at %s -- the "
            "gold patch does not appear to be applied; refusing to compare "
            "against unpatched code" % path)

    net = _NoNetwork()
    ns = dict(linkcheck.__dict__)
    ns["requests"] = net                  # the ONLY substitution: the network
    ns["uri"] = URI
    ns["self"] = _Builder()
    ns["kwargs"] = {"allow_redirects": True}
    exec(srcs["get_request_headers"], ns)
    exec(body, ns)
    if getattr(ns["requests"], "__class__", None) is not _NoNetwork:
        raise RuntimeError("a real network module leaked into the oracle namespace")
    return ns["check_uri"], net, path, body


# --- type bridge, backward direction: (status, info, code) -> model codes -----

_CLASS_CODES = {"working": WORKING(), "broken": FAILED(), "ignored": IGNORED()}


def _real_http_error_text(status):
    """The exact `str(err)` the REAL raise_for_status produces for this response,
    or None when it does not raise. Not reimplemented -- observed."""
    import requests
    from requests.exceptions import HTTPError
    response = requests.models.Response()
    response.status_code = status
    response.url = REQ_URL
    response.reason = REASON
    try:
        response.raise_for_status()
    except HTTPError as err:
        return str(err)
    return None


def _real_anchor_absent_text():
    """The exact message the REAL patched fragment branch raises when the
    fragment is missing (read from the repo's own locale helper)."""
    from sphinx.locale import __
    return __("Anchor '%s' not found") % ANCHOR


def abstract_outcome(outcome, status):
    """Map the repo's (status, info, code) onto the model's (class, datum)
    codes. Returns (pair, None) or (None, reason) when the outcome falls
    outside the documented map -- never a silent bucket."""
    if not (isinstance(outcome, tuple) and len(outcome) == 3):
        return None, "outcome is not a 3-tuple: %r" % (outcome,)
    cls, info, code = outcome
    if cls not in _CLASS_CODES:
        return None, "unmapped status class %r (mapping.md §2 covers " \
                     "working/broken/ignored)" % (cls,)
    if code != 0:
        return None, "non-zero code %r (the modeled paths always return 0)" % (code,)
    if info == "" or info == " - unauthorized":
        datum = DATUM_NONE()
    elif info == _real_http_error_text(status):
        datum = DATUM_TRANSPORT()
    elif info == _real_anchor_absent_text():
        datum = DATUM_FRAGMENT_ABSENT()
    else:
        return None, "unmapped info string %r" % (info,)
    return (_CLASS_CODES[cls], datum), None


# =============================================================================
# INPUTS
# =============================================================================

BOUNDARY_STATUSES = [
    # the F2P shape and the error-window edges
    500, 399, 400, 401, 402, 403, 404, 410, 429, 451, 499,
    501, 502, 503, 504, 511, 598, 599, 600, 601,
    # non-error statuses: informational / success / redirect
    0, 1, 100, 101, 199, 200, 201, 204, 226, 300, 301, 302, 304, 307, 308,
    # far outside every range, and negatives (the model's carrier is `int`)
    699, 700, 999, 1000, 4000, -1, -400, -500,
    10 ** 6, -(10 ** 6), 10 ** 12,
]

FUZZ_POOL = [199, 200, 301, 399, 400, 401, 402, 429, 499, 500, 502, 503,
             504, 599, 600, 601, 0, -1]


def boundary_inputs():
    cases = []
    for status in BOUNDARY_STATUSES:
        for present in (False, True):
            cases.append((status, present))
    return cases


def fuzz_inputs(n, rng):
    for _ in range(n):
        r = rng.random()
        if r < 0.5:
            status = rng.choice(FUZZ_POOL)
        elif r < 0.9:
            status = rng.randint(90, 620)       # dense around the window
        else:
            status = rng.randint(-100000, 100000)
        yield (status, rng.choice((False, True)))


# =============================================================================

def main():
    call_oracle, net, path, _src = build_oracle()

    def oracle(status, fragment_present):
        net.status = status
        net.fragment_present = fragment_present
        return call_oracle()                    # the REAL patched check_uri

    arms = {}
    checked = 0

    def compare(status, fragment_present, phase):
        raw = oracle(status, fragment_present)
        got, reason = abstract_outcome(raw, status)
        if reason is not None:
            print("G-CONF FAIL (%s): input (status=%r, fragment_present=%r): "
                  "real check_uri returned %r which the mapping.md §2 bridge "
                  "does not cover: %s" % (phase, status, fragment_present, raw, reason))
            return False
        shadow = shadow_classify_fragment_link(status, fragment_present)
        arms[shadow] = arms.get(shadow, 0) + 1
        if shadow != got:
            print("G-CONF FAIL (%s): DISAGREEMENT" % phase)
            print("  input          : status=%r fragment_present=%r" % (status, fragment_present))
            print("  shadow (model) : %r" % (shadow,))
            print("  oracle (repo)  : %r  <- raw %r" % (got, raw))
            return False
        return True

    for status, present in boundary_inputs():
        if not compare(status, present, "boundary"):
            return 1
        checked += 1

    rng = random.Random(SEED)
    for status, present in fuzz_inputs(N_FUZZ, rng):
        if not compare(status, present, "fuzz"):
            return 1
        checked += 1

    # every impl arm must have fired, else the check certifies nothing
    expected_arms = {
        (WORKING(), DATUM_NONE()),               # 401 dispatch + fall-through
        (IGNORED(), DATUM_TRANSPORT()),          # 503 dispatch
        (FAILED(), DATUM_TRANSPORT()),           # other error statuses
        (FAILED(), DATUM_FRAGMENT_ABSENT()),     # fragment-absent path
    }
    unfired = expected_arms - set(arms)
    if unfired:
        print("G-CONF FAIL: impl outcomes never exercised: %r" % (sorted(unfired),))
        return 1

    print("G-CONF OK: verbatim shadow of model.py's impl region (its "
          "@ContractOnly gate wired to the real requests.Response."
          "raise_for_status) agrees with the REAL patched "
          "CheckExternalLinksBuilder.check_thread.check_uri extracted from %s "
          "on all %d inputs (%d boundary + %d fuzz, seed %d); 0 disagreements."
          % (path, checked, len(boundary_inputs()), N_FUZZ, SEED))
    print(json.dumps({
        "checked": checked,
        "boundary": len(boundary_inputs()),
        "fuzz": N_FUZZ,
        "disagreements": 0,
        "seed": SEED,
        "shadow": "direct (model.py impl region verbatim; @ContractOnly "
                  "raise_on_error_status -> real Response.raise_for_status)",
        "oracle": "real patched check_uri source exec'd from " + str(path),
        "outcome_histogram": {str(k): v for k, v in sorted(arms.items())},
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
