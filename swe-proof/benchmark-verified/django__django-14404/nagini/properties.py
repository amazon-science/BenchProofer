"""PBT manifest for django__django-14404 (NOT a Nagini module; a record of
adversarial cases the runner swebench_nagini.pbt executes + stamps RESULT).

Defended surface (frozen spec in model.py; see refinement.md / mapping.md):

  slash_redirect_target(full_path, app_relative_path, append_slash_enabled,
                        url_has_trailing_slash, slash_form_resolves,
                        target_view_opts_in) -> List[int]
    Requires: Acc(list_pred(full_path), 1/2)          -- READ-ONLY (1/2 perm)
    Requires: Acc(list_pred(app_relative_path), 1/2)  -- READ-ONLY (1/2 perm)
    Ensures (frame): Acc(list_pred(full_path), 1/2)
                     Acc(list_pred(app_relative_path), 1/2)
                     Acc(list_pred(Result()))
    Ensures (CONTROL FLOW): a value is returned on EXACTLY the four-guard
        conjunction  (append_slash_enabled AND not url_has_trailing_slash
        AND slash_form_resolves AND target_view_opts_in)
    Ensures (THE FIX, load-bearing):
        ToSeq(Result()) == with_trailing_slash(ToSeq(full_path))
        -- the redirect target is the FULL externally-visible path (with any
        deployment prefix) + a single trailing slash (code point 47), grounded
        STRUCTURALLY in full_path, never the prefix-stripped app_relative_path.
    Exsures(NotFound, <negation of the four-guard conjunction>)

  with_trailing_slash(p) = p + PSeq(47)   -- @Pure, GROUNDED in its argument.

This models the gold one-line fix to AdminSite.catch_all_view: the pre-patch
reused one local `path = '%s/' % request.path_info` BOTH as the resolve arg AND
as the redirect target; the fix rebuilds the redirect target from request.path
(`return HttpResponsePermanentRedirect('%s/' % request.path)`), which carries the
SCRIPT_NAME/FORCE_SCRIPT_NAME deployment prefix that request.path_info drops.
The two F2P tests set SCRIPT_NAME='/prefix/' (resp. FORCE_SCRIPT_NAME) and assert
the redirect goes to '/prefix' + known_url, i.e. the prefix is PRESENT in the
target -- only a target built from request.path (full_path) includes it.

GROUNDED-ORACLE NOTE: the postcondition oracle with_trailing_slash(ToSeq(full_path))
is GROUNDED in the argument -- a @Pure body `p + PSeq(47)`, fully unfolded, with
no opaque answer-key. So there is NO *wrong* echo a rival can return:
`result = list(full_path); result.append(47); return result` is the honest gold
construction and IS the correct impl; any other base (app_relative_path) or any
constant fails the postcondition. The uniqueness lane is therefore about (a) the
mandatory frame-mutation probe on the read-only inputs, (b) building the target
from the WRONG source (app_relative_path == the pre-patch bug == model_prepatch.py),
and (c) control-flow rivals that return/raise on the wrong guard sub-domain.

AXIOM LANE: there is NO @ContractOnly axiom in this bundle (axioms region empty)
and NO A-reference deep model consumed in the proof -- the one changed string op
(building the target from the full path) is modelled DEEPLY in the impl
(result.append(47)) and proven directly. The single load-bearing deep-modelling
PREMISE -- that request.path carries the deployment prefix while request.path_info
does not, so full_path is the correct base -- is validated by axiom_check.py
(G-AX) against the real WSGIRequest.__init__ path construction (stdlib-only,
reconstructed verbatim from django/core/handlers/wsgi.py:65-76). PBT re-runs that
premise check as an axiom-soundness probe: axiom_check.py's source is read on the
HOST at load time and embedded into the probe string (the runner mounts only the
probe at /work). It is stdlib-only (no django import needed), so it is robust to
the eval image; apply_gold is harmless.

REGION-SURGERY: every spec variant is built by _swap on _BASE editing ONLY text
inside # impl-start/# impl-end. The frozen spec (axioms/pure/pre/post-conditions/
signatures) is never touched, so same_spec holds for every spec case.
"""
from pathlib import Path

INSTANCE = "django__django-14404"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_DIR = Path(__file__).parent
_BASE = (_DIR / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Stable anchors inside the impl region (each present exactly once in _BASE).
# ---------------------------------------------------------------------------
# The full nested-if impl body (the gold construction).
_IMPL_BODY = (
    "    if append_slash_enabled and not url_has_trailing_slash:\n"
    "        if slash_form_resolves:\n"
    "            if target_view_opts_in:\n"
    "                result = list(full_path)  # type: List[int]\n"
    "                result.append(47)\n"
    "                return result\n"
    "    raise NotFound()\n"
)
# The exact gold construction lines (the FIX -- target grounded in full_path).
_CONSTRUCT = (
    "                result = list(full_path)  # type: List[int]\n"
    "                result.append(47)\n"
    "                return result\n"
)

for _a in (_IMPL_BODY, _CONSTRUCT):
    assert _BASE.count(_a) == 1, f"anchor drifted: {_a!r}"


# ===========================================================================
# POSITIVE CONTROLS / ADMISSIBILITY  (expect "verify")
# ===========================================================================

# (5a) POSITIVE CONTROL -- guard reorder / branch flatten. The three nested
# `if`s are flattened into one short-circuit conjunction; on the negation we
# fall through to `raise NotFound()`. Semantically identical to the gold nested
# ifs (the conjunction is exactly the four-guard return condition). The gold
# construction (result = list(full_path); result.append(47); return result) is
# kept VERBATIM so the postcondition proof obligation
# ToSeq(Result()) == with_trailing_slash(ToSeq(full_path)) is closed exactly as
# in model.py. MUST verify; else the postcondition is over-fit to the nested-if
# FORM => SPEC-TOO-STRONG.
_POS_FLATTEN = _swap(
    _BASE, _IMPL_BODY,
    "    if (append_slash_enabled and not url_has_trailing_slash\n"
    "            and slash_form_resolves and target_view_opts_in):\n"
    "        result = list(full_path)  # type: List[int]\n"
    "        result.append(47)\n"
    "        return result\n"
    "    raise NotFound()\n",
)

# (5b) POSITIVE CONTROL -- raise-early / guard-the-negation reshape. Each guard
# failure raises NotFound() immediately (matching the Exsures negation clause
# disjunct-by-disjunct), then the gold construction runs unconditionally. This
# is a structurally DIFFERENT control shape (early-exit vs nested-if) that is
# behaviourally identical, and it keeps the gold construction verbatim. MUST
# verify; else SPEC-TOO-STRONG.
_POS_EARLYEXIT = _swap(
    _BASE, _IMPL_BODY,
    "    if not append_slash_enabled:\n"
    "        raise NotFound()\n"
    "    if url_has_trailing_slash:\n"
    "        raise NotFound()\n"
    "    if not slash_form_resolves:\n"
    "        raise NotFound()\n"
    "    if not target_view_opts_in:\n"
    "        raise NotFound()\n"
    "    result = list(full_path)  # type: List[int]\n"
    "    result.append(47)\n"
    "    return result\n",
)

# (6) ADMISSIBILITY -- a self-call on a fresh, F2P-shaped input establishes the
# precondition Acc(list_pred(.),1/2) for BOTH read-only inputs, on a normal
# redirect-issuing case (all four guards True, full_path = "/prefix/admin/x"
# code points, app_relative_path = "/admin/x" code points). The Assert pins the
# returned target to with_trailing_slash(ToSeq(probe_full)) (full_path + '/'),
# i.e. the prefix-carrying redirect target the F2P tests observe. Then the gold
# body runs on the actual inputs. MUST verify; else the precondition rejects a
# normal F2P-shaped input => PRECOND-TOO-STRONG.
_POS_ADMISS = _swap(
    _BASE, _IMPL_BODY,
    # "/p/x" -> [47,112,47,120] (full, with prefix); "/x" -> [47,120] (relative)
    "    probe_full = [47, 112, 47, 120]  # type: List[int]\n"
    "    probe_rel = [47, 120]  # type: List[int]\n"
    "    Assert(Acc(list_pred(probe_full), 1 / 2))\n"
    "    Assert(Acc(list_pred(probe_rel), 1 / 2))\n"
    + _IMPL_BODY,
)


# ===========================================================================
# UNIQUENESS RIVALS  (spec-too-weak probes -- expect "reject")
# ===========================================================================

# (1) FRAME MUTATION -- MANDATORY (#1 weakness class). full_path is read-only at
# 1/2 permission. This rival WRITES through it via full_path.append(47) and
# returns full_path itself as the target. A store/append needs FULL
# Acc(list_pred(full_path)) permission, so under the 1/2 precondition it MUST be
# rejected for INSUFFICIENT PERMISSION (not a value mismatch). The gold guard
# structure is kept verbatim so the rejection is attributable solely to the
# mutating write. If it verified, the read-only frame protection would be hollow.
_RIVAL_FRAME = _swap(
    _BASE, _CONSTRUCT,
    "                full_path.append(47)\n"
    "                return full_path\n",
)

# (1b) FRAME MUTATION on the OTHER read-only input. A subtler vacuous-satisfaction
# attempt: mutate app_relative_path in place to equal full_path + [47] and return
# it, trying to satisfy ToSeq(Result()) == with_trailing_slash(ToSeq(full_path))
# while never touching full_path's construction. The write
# app_relative_path.append(47) needs FULL permission on app_relative_path, held
# only at 1/2 -> rejected for INSUFFICIENT PERMISSION. (It would also fail the
# value postcondition since app_relative_path != full_path in general, but the
# permission check fires first and is the load-bearing rejection.)
_RIVAL_FRAME2 = _swap(
    _BASE, _CONSTRUCT,
    "                app_relative_path.append(47)\n"
    "                return app_relative_path\n",
)

# (2) WRONG-SOURCE -- build the target from the prefix-stripped path
# (app_relative_path) instead of full_path. This is EXACTLY the pre-patch bug
# (== model_prepatch.py): result = list(app_relative_path); result.append(47).
# The postcondition ToSeq(Result()) == with_trailing_slash(ToSeq(full_path))
# pins the base to full_path, so a target built from app_relative_path cannot be
# proven equal (full_path and app_relative_path are independent inputs, not
# assumed equal -- a prefix makes them differ). MUST be rejected on the FIX
# postcondition clause. Rejection source: the load-bearing FIX postcondition.
_RIVAL_WRONGSRC = _swap(
    _BASE, _CONSTRUCT,
    "                result = list(app_relative_path)  # type: List[int]\n"
    "                result.append(47)\n"
    "                return result\n",
)

# (3a) CONTROL-FLOW -- drop the target_view_opts_in guard. The rival returns the
# (correct, full-path) target whenever the first two guards hold and the slash
# form resolves, IGNORING whether the resolved view opts in. On an input with
# target_view_opts_in == False it RETURNS instead of raising NotFound. That
# violates BOTH the return-conjunction Ensures (a value is returned but the
# conjunction is False because target_view_opts_in is False) and the Exsures
# (which requires NotFound on that negation disjunct). MUST be rejected.
# Rejection source: the return-conjunction Ensures + the Exsures negation clause.
_RIVAL_DROP_OPTIN = _swap(
    _BASE, _IMPL_BODY,
    "    if append_slash_enabled and not url_has_trailing_slash:\n"
    "        if slash_form_resolves:\n"
    "            result = list(full_path)  # type: List[int]\n"
    "            result.append(47)\n"
    "            return result\n"
    "    raise NotFound()\n",
)

# (3b) PARTIAL-DOMAIN / CONTROL-FLOW -- drop the not-url_has_trailing_slash guard.
# The rival returns the target whenever slash-appending is enabled and the slash
# form resolves and the view opts in, EVEN IF the URL already ends with a slash.
# On an input with url_has_trailing_slash == True it RETURNS instead of raising
# NotFound, violating the return-conjunction Ensures (the conjunction is False
# because url_has_trailing_slash is True) and the Exsures clause. Correct on every
# no-trailing-slash input, wrong on the trailing-slash sub-domain. MUST be
# rejected. Rejection source: the return-conjunction Ensures + Exsures.
_RIVAL_DROP_TRAILING = _swap(
    _BASE, _IMPL_BODY,
    "    if append_slash_enabled:\n"
    "        if slash_form_resolves:\n"
    "            if target_view_opts_in:\n"
    "                result = list(full_path)  # type: List[int]\n"
    "                result.append(47)\n"
    "                return result\n"
    "    raise NotFound()\n",
)

# (3c) PARTIAL-DOMAIN -- return on the FULL conjunction but WITHOUT the trailing
# slash (return the bare full_path, no append). This pins the control flow
# correctly (returns on exactly the four-guard conjunction) but the redirect
# target is full_path itself, not full_path + [47]. It satisfies the
# return-conjunction Ensures and the Exsures, but FAILS the FIX postcondition
# ToSeq(Result()) == with_trailing_slash(ToSeq(full_path)) (missing the trailing
# '/'). MUST be rejected. Rejection source: the FIX postcondition (the trailing
# slash is load-bearing -- the redirect goes to the slash-terminated form).
_RIVAL_NO_SLASH = _swap(
    _BASE, _CONSTRUCT,
    "                result = list(full_path)  # type: List[int]\n"
    "                return result\n",
)


SPEC_TESTS = [
    # ---- positive controls (must VERIFY) ----
    {"id": "pos-control-flatten", "kind": "soundness", "expect": "verify",
     "module": _POS_FLATTEN,
     "rationale": "structurally-different (the three nested ifs flattened into one "
                  "short-circuit conjunction with a fall-through raise) but behaviourally "
                  "identical CORRECT impl, keeping the gold construction "
                  "(result=list(full_path); result.append(47); return result) verbatim so "
                  "the FIX postcondition ToSeq(Result())==with_trailing_slash(ToSeq(full_path)) "
                  "closes exactly as in model.py. Must verify; else the postcondition is "
                  "over-fit to the nested-if FORM => SPEC-TOO-STRONG."},
    {"id": "pos-control-earlyexit", "kind": "soundness", "expect": "verify",
     "module": _POS_EARLYEXIT,
     "rationale": "structurally-different control shape: each guard failure raises "
                  "NotFound() early (mirroring the Exsures negation disjunct-by-disjunct), "
                  "then the gold construction runs unconditionally. Behaviourally identical, "
                  "keeps the gold construction verbatim. Must verify; else SPEC-TOO-STRONG. "
                  "Also confirms the Exsures admits the disjunctive early-raise shape."},
    {"id": "admiss-selfcall", "kind": "admissibility", "expect": "verify",
     "module": _POS_ADMISS,
     "rationale": "a self-call on a fresh F2P-shaped redirect-issuing input "
                  "(full_path='/p/x'=[47,112,47,120] with a prefix, app_relative_path='/x'="
                  "[47,120], all four guards True) must establish the precondition "
                  "Acc(list_pred(.),1/2) for BOTH read-only inputs and the result property "
                  "ToSeq(tgt)==with_trailing_slash(ToSeq(probe_full)) (the prefix-carrying "
                  "target the F2P tests observe). If the precondition rejects this normal "
                  "input => PRECOND-TOO-STRONG."},

    # ---- uniqueness rivals (must be REJECTED) ----
    {"id": "frame-mutate-fullpath", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_FRAME,
     "refinement": "no faithful real patch corresponds to this: catch_all_view never mutates "
                   "request.path (a read-only str on the request, immutable); it formats a NEW "
                   "string '%s/' % request.path. The rival exists solely to test whether the "
                   "read-only (1/2) precondition on full_path can be subverted by overwriting "
                   "the input in place. There is no resolving patch that rewrites request.path, "
                   "so a verifying rival here would be a pure verify-not-resolve artifact "
                   "(vacuous satisfaction via self-mutation of a read-only input).",
     "rationale": "MANDATORY frame-mutation probe. full_path.append(47) writes through a 1/2 "
                  "(read-only) reference and MUST fail for INSUFFICIENT PERMISSION (an append "
                  "needs full Acc(list_pred(full_path))), NOT a value mismatch; the gold guard "
                  "structure is kept verbatim so the rejection is attributable to the write. "
                  "Rejection source: the PERMISSION SYSTEM. If it verified => SPEC-TOO-WEAK "
                  "(frame protection on the redirect-base input hollow)."},
    {"id": "frame-mutate-relpath", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_FRAME2,
     "refinement": "no faithful real patch corresponds: request.path_info is also a read-only "
                   "str the view never mutates. This rival tries to satisfy the FIX "
                   "postcondition vacuously by writing a '/' onto app_relative_path and "
                   "returning it, dodging full_path entirely. There is no resolving patch that "
                   "rewrites request.path_info in place, so a verifying rival would be a pure "
                   "verify-not-resolve artifact.",
     "rationale": "frame-mutation probe on the SECOND read-only input. app_relative_path.append(47) "
                  "needs FULL permission on app_relative_path, held only at 1/2, so it MUST be "
                  "rejected for INSUFFICIENT PERMISSION (the permission check fires before any "
                  "value reasoning; the value postcondition would also fail since "
                  "app_relative_path != full_path in general). Rejection source: the PERMISSION "
                  "SYSTEM. If it verified => SPEC-TOO-WEAK."},
    {"id": "weak-wrong-source", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_WRONGSRC,
     "refinement": "this is EXACTLY the pre-patch bug (== model_prepatch.py): build the redirect "
                   "target from the prefix-stripped path. The faithful real patch keeping "
                   "'%s/' % request.path_info as the redirect target drops the SCRIPT_NAME/"
                   "FORCE_SCRIPT_NAME deployment prefix, so under SCRIPT_NAME='/prefix/' it "
                   "redirects to known_url (no prefix) instead of '/prefix'+known_url and FAILS "
                   "both F2P tests (test_missing_slash_append_slash_true_script_name / "
                   "_force_script_name) -- verify-not-resolve.",
     "rationale": "rejection source: the FIX postcondition "
                  "ToSeq(Result())==with_trailing_slash(ToSeq(full_path)). The target is built "
                  "from app_relative_path, which the verifier cannot prove equals full_path + "
                  "[47] (full_path and app_relative_path are independent 1/2-perm inputs, not "
                  "assumed equal; a prefix makes them differ). This is precisely what G-DIFF "
                  "senses on model_prepatch.py. If it verified => SPEC-TOO-WEAK."},
    {"id": "weak-drop-optin-guard", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_DROP_OPTIN,
     "refinement": "dropping the should_append_slash opt-in check makes the view redirect to "
                   "the slash form even when the resolved view opts OUT (@no_append_slash). The "
                   "faithful real patch removing `if getattr(match.func,'should_append_slash',True)` "
                   "redirects views that explicitly disabled slash-appending, breaking the P2P "
                   "behaviour those tests pin (a no_append_slash view must 404, not 301) -- "
                   "verify-not-resolve.",
     "rationale": "rejection source: the return-conjunction Ensures(append_slash_enabled and "
                  "not url_has_trailing_slash and slash_form_resolves and target_view_opts_in) "
                  "AND the Exsures negation clause. On an input with target_view_opts_in==False "
                  "the rival RETURNS, but the return-conjunction is then False (so the value "
                  "postcondition that a value is returned only on the conjunction fails) and the "
                  "Exsures requires NotFound on that disjunct. If it verified => SPEC-TOO-WEAK."},
    {"id": "weak-drop-trailing-guard", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_DROP_TRAILING,
     "refinement": "dropping the `not url.endswith('/')` guard makes the view redirect a URL "
                   "that ALREADY ends with a slash, producing a double-slash target and an "
                   "infinite/duplicate redirect. The faithful real patch removing the "
                   "`not url.endswith('/')` condition redirects already-slashed URLs, which the "
                   "P2P tests (and the surrounding catch-all behaviour) forbid -- "
                   "verify-not-resolve.",
     "rationale": "rejection source: the return-conjunction Ensures + the Exsures negation "
                  "clause. On an input with url_has_trailing_slash==True the rival RETURNS, but "
                  "the four-guard conjunction is then False and the Exsures requires NotFound on "
                  "the `url_has_trailing_slash is True` disjunct. Correct on every "
                  "no-trailing-slash input, wrong on the trailing-slash sub-domain. If it "
                  "verified => SPEC-TOO-WEAK (partial-domain)."},
    {"id": "weak-no-trailing-slash", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_NO_SLASH,
     "refinement": "returning request.path WITHOUT the appended '/' is not a slash-appending "
                   "redirect at all -- the whole point of catch_all_view's APPEND_SLASH branch "
                   "is to redirect the slash-LESS URL to its slash-terminated form. A faithful "
                   "patch returning HttpResponsePermanentRedirect(request.path) (no '%s/') "
                   "redirects to the same slash-less URL, an immediate redirect loop, and FAILS "
                   "every F2P/P2P slash-redirect assertion (assertRedirects expects known_url "
                   "WITH its trailing slash) -- verify-not-resolve.",
     "rationale": "rejection source: the FIX postcondition "
                  "ToSeq(Result())==with_trailing_slash(ToSeq(full_path)). The control flow is "
                  "pinned correctly (returns on exactly the four-guard conjunction, so the "
                  "return-conjunction Ensures and Exsures both hold), but Result()==full_path "
                  "(no trailing slash) != with_trailing_slash(ToSeq(full_path))==full_path+[47]. "
                  "The trailing slash (code point 47) is load-bearing. If it verified => "
                  "SPEC-TOO-WEAK."},
]


# ===========================================================================
# AXIOM LANE -- no @ContractOnly axiom is consumed and no A-reference deep model
# is consumed in the Nagini proof (the changed string op is modelled deeply in
# the impl and proven directly). The single load-bearing deep-modelling PREMISE
# is that request.path carries the SCRIPT_NAME/FORCE_SCRIPT_NAME deployment prefix
# while request.path_info does NOT, so the FIX postcondition's choice of full_path
# (== request.path) as the redirect base is what restores the prefix. We re-run
# axiom_check.py's premise check (read on the HOST and embedded into a
# self-contained, stdlib-only probe) as an axiom-soundness case: it reconstructs
# WSGIRequest.__init__'s path / path_info construction verbatim
# (django/core/handlers/wsgi.py:65-76) over 10 boundary + 20000 fuzz
# (SCRIPT_NAME, PATH_INFO) pairs and asserts the model's
# with_trailing_slash(request.path) == the gold '%s/' % request.path and that a
# non-empty prefix makes the gold target differ from the bug '%s/' %
# request.path_info (prefix present => gold != bug; absent => gold == bug).
# A containment probe is N/A (there is no axiom Requires domain for a model-
# reachable input to fall outside).
# ===========================================================================

_AXIOM_CHECK_SRC = (_DIR / "axiom_check.py").read_text()

AXIOM_TESTS = [
    {
        "id": "ax-premise-requestpath-carries-prefix",
        "axiom": "with_trailing_slash / request.path deep-model premise",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _AXIOM_CHECK_SRC,
        "rationale": "the FIX postcondition pins the redirect base to full_path (== "
                     "request.path). Its load-bearing deep-modelling premise -- that "
                     "request.path carries the SCRIPT_NAME/FORCE_SCRIPT_NAME prefix while "
                     "request.path_info does not -- is validated against the REAL "
                     "WSGIRequest.__init__ path construction (django/core/handlers/wsgi.py:"
                     "65-76, transcribed verbatim, stdlib-only). The probe (axiom_check.py "
                     "verbatim) asserts (1) model with_trailing_slash(request.path) == gold "
                     "'%s/' % request.path, (2) a non-empty prefix => gold target carries it "
                     "and gold != bug ('%s/' % request.path_info), (3) no prefix => gold == "
                     "bug, over 10 boundary + 20000 fuzz (SCRIPT_NAME, PATH_INFO) pairs. Exit "
                     "0 iff every obligation holds; any disagreement => the deep-modelling "
                     "premise (and thus the choice of full_path as the redirect base) is "
                     "unsound. It imports nothing repo-specific, so apply_gold is harmless.",
    },
]
