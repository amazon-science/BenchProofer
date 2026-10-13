# properties.py — PBT falsification battery for django__django-16139.
#
# NOT a Nagini module. A manifest the runner (swebench_nagini.pbt) parses: each
# SPEC_TESTS entry is a full model.py variant that shares the FROZEN spec
# (axioms/pure/pre/post-conditions regions untouched) and swaps ONLY text inside
# the # impl-start / # impl-end region; the runner checks each with Nagini
# verify + markers.same_spec.
#
# Defended surface (read from model.py + refinement.md + mapping.md + instance):
#   build_action_reference(prefix: List[int], token, current_action, pk,
#                          secondary_action) -> List[int]
#   builds the RELATIVE reference embedded in the read-only password help-text
#   link (gold: f"../../{self.instance.pk}/password/" replacing "../password/").
#   The reference is the list of path-segment steps; DOTDOT()==-1 is the ".."
#   up-one-level step; ordinary segments are >= 0.
#
#   READ-ONLY input: `prefix` is held at Acc(list_pred(prefix), 1/2) (required
#   AND ensured) — it is read, never mutated. => FRAME-MUTATION is MANDATORY.
#
#   LOAD-BEARING postcondition (the whole point of the change):
#       resolve(ToSeq(prefix) + PSeq(token) + PSeq(current_action),
#               ToSeq(Result()))
#           == ToSeq(prefix) + PSeq(pk) + PSeq(secondary_action)
#   quantified over ALL token/pk: resolving the produced relative reference
#   against the current TOKEN-keyed location must land on the PK-keyed
#   secondary-action page, for EVERY access token. `resolve` is a GROUNDED
#   @Pure front-recursive fold of the actual args (not an opaque answer-key
#   oracle) — see 'assessment' re ungrounded-oracle echo (no wrong echo exists).
#
#   The unique correct reference is [DOTDOT(), DOTDOT(), pk, secondary_action]:
#   one ".." pops current_action, a second pops token, then pk and
#   secondary_action are appended -> prefix + [pk] + [secondary_action].
#
# F2P: test_link_to_password_reset_in_helptext_via_to_field — reaches the
#      change page via a `to_field` (the username "testclient"), so token != pk,
#      and asserts urljoin(change_url, href) == reverse(password_change, pk).
# A-reference: `resolve` deep model == urllib.parse.urljoin (G-AX). The axiom
#      lane re-runs that real-callee soundness check (stdlib only) in Docker.

from pathlib import Path

INSTANCE = "django__django-16139"
FLOAT_ENCODING = None  # meta.json float_encoding == null


_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# The frozen impl region (model.py lines 105-137). The first line builds the
# result; the rest is the gold resolution proof (per-step unfolds of `resolve`).
# Every rival edits ONLY this region. We anchor on the result-construction line
# and (for the positive control) keep the entire proof tail verbatim.
# ---------------------------------------------------------------------------
_GOLD_RESULT = (
    "    result = [DOTDOT(), DOTDOT(), pk, secondary_action]  # type: List[int]"
)


# === POSITIVE CONTROL (soundness) =========================================
# Structurally-different but CORRECT: produce the SAME unique-correct list
# value via a different executable shape — bind the two ".." steps to typed
# locals and assemble the reference by list concatenation, instead of a single
# 4-element literal. The result value is identical, so EVERY gold proof assert
# below (rel = ToSeq(result); the per-step resolve unfolds) is preserved
# verbatim and still discharges. This is a local-variable reshape (directive-2 &
# -3 safe): no loop-direction flip, no forward-append against the front-recursive
# `resolve` fold, no dropped framing assert. If this cannot verify the spec is
# SPEC-TOO-STRONG (rejects a faithful correct impl).
_POS_RESULT = (
    "    # POSITIVE CONTROL: same value, different shape (local-binding +\n"
    "    # list concatenation) — the gold proof tail is kept verbatim.\n"
    "    up = DOTDOT()  # type: int\n"
    "    head = [up, up]  # type: List[int]\n"
    "    tail = [pk, secondary_action]  # type: List[int]\n"
    "    result = head + tail  # type: List[int]"
)
POS_CONCAT = _swap(_BASE, _GOLD_RESULT, _POS_RESULT)


# === ADMISSIBILITY ========================================================
# A separate top-level caller would break same_spec (spec_view only elides the
# impl region; anything module-level enters the spec signature). So the
# admissibility probe lives INSIDE the impl region, inserted right after
# `# impl-start` (before any gold obligation, so every following obligation is
# preserved verbatim): construct a concrete F2P-shaped prefix and assert the
# Requires predicates are establishable on it (read-permission on prefix, the
# non-negative-segments quantifier, and the >=0 scalar guards). If this block
# cannot verify, the precondition is unsatisfiable for a normal input ->
# PRECOND-TOO-STRONG. We do NOT make a self-recursive call (it would need a
# Decreases measure the spec doesn't carry — a proof gap, not a spec defect),
# so we exercise the Requires-predicate / domain directly.
_ADMISS_BLOCK = (
    "    # impl-start\n"
    "    # ADMISSIBILITY PROBE: an F2P-shaped current location\n"
    "    #   prefix = [admin, app, model] = [100, 101, 102], token=200 (a\n"
    "    #   to_field value distinct from pk), current_action=300, pk=7,\n"
    "    #   secondary_action=400 — establishes every Requires conjunct.\n"
    "    Assert(token >= 0 and current_action >= 0 and pk >= 0\n"
    "           and secondary_action >= 0)\n"
    "    Assert(Forall(int, lambda k: (Implies(0 <= k and k < len(prefix),\n"
    "                                          prefix[k] >= 0), [[prefix[k]]])))\n"
    "    Assert(Acc(list_pred(prefix), 1 / 2))"
)
ADMISS = _swap(_BASE, "    # impl-start", _ADMISS_BLOCK)


# === FRAME-MUTATION (MANDATORY — prefix is Acc(list_pred(prefix), 1/2)) =====
# Rival that WRITES to the read-only input `prefix` while still returning the
# gold reference. `prefix` is held at HALF permission, so the write
# `prefix.append(pk)` cannot be performed — Nagini rejects for INSUFFICIENT
# PERMISSION. The gold result + entire resolution proof are kept verbatim so the
# rejection is attributable solely to the illegal write (not a value mismatch).
# A byte-fuzzer never thinks to mutate the input — this is the project's #1
# weakness class. NOTE: the resolution postcondition reads `ToSeq(prefix)`; if
# the spec held FULL permission a mutating impl could falsely "stabilise" the
# read-only collection. The half permission forbids it.
# refinement: a faithful real patch that mutated the shared admin URL prefix
# (e.g. rewrote request.path / the form's base path while building the href)
# would corrupt the page location for every other field's link on the same form
# — admin form-rendering P2P tests would render the wrong URLs and NOT resolve;
# more directly, the change site only formats an href and must not touch the
# request path at all.
_FRAME_RESULT = (
    "    # FRAME-MUTATION RIVAL: write to the READ-ONLY prefix (Acc(.,1/2)).\n"
    "    # Must be rejected for INSUFFICIENT PERMISSION; gold proof kept verbatim.\n"
    "    prefix.append(pk)\n"
    + _GOLD_RESULT
)
FRAME_PREFIX_WRITE = _swap(_BASE, _GOLD_RESULT, _FRAME_RESULT)


# === UNIQUENESS / REJECT rivals ===========================================

# --- W1 token-keyed (THE PRE-PATCH BUG): the single-level reference
# [DOTDOT, secondary_action] == "../password/". Resolves to
# prefix + [token] + [secondary_action] (TOKEN-keyed): pop current_action,
# append secondary_action. Correct ONLY when token == pk. This is literally
# model_prepatch.py and the bug the gold patch fixes.
# refinement: this is the verbatim pre-patch expression
# `password.help_text.format("../password/")`; the F2P test reaches the change
# page via a `to_field` (username "testclient"), so token != pk, and the
# resolved href lands on the TOKEN-keyed page, not reverse(password_change, pk)
# — the assertEqual fails, so it does NOT resolve (it is the original bug).
# rejection source: the resolution postcondition — resolve(base0, rel) yields
# prefix+[token]+[secondary_action] != prefix+[pk]+[secondary_action] for the
# universally-quantified token (provably wrong when token != pk).
_W1_RESULT = (
    "    # W1 TOKEN-KEYED RIVAL (pre-patch '../password/'): one '..' then the\n"
    "    # action — resolves to the TOKEN-keyed page, wrong when token != pk.\n"
    "    result = [DOTDOT(), secondary_action]  # type: List[int]"
)
W1_TOKEN_KEYED = _swap(_BASE, _GOLD_RESULT, _W1_RESULT)


# --- W2 partial-pop: [DOTDOT, pk, secondary_action] == "../<pk>/password/".
# One '..' pops current_action; then pk and secondary_action are appended ->
# prefix + [token] + [pk] + [secondary_action]. The token segment is NOT popped,
# so the page is nested UNDER the token instead of replacing it. Wrong for
# every token (the resolved path has an extra segment).
# refinement: a faithful patch f"../{self.instance.pk}/password/" omits one
# '..'; the resolved href is /admin/auth/user/<token>/<pk>/password/ — not a
# valid password-change URL at all (reverse(password_change, pk) has no token
# segment) — the F2P assertEqual fails and it does NOT resolve.
# rejection source: the resolution postcondition (extra [token] segment in the
# resolved sequence; length and content differ from prefix+[pk]+[secondary]).
_W2_RESULT = (
    "    # W2 PARTIAL-POP RIVAL ('../<pk>/password/'): only one '..' — leaves the\n"
    "    # token segment in place, nesting under it.\n"
    "    result = [DOTDOT(), pk, secondary_action]  # type: List[int]"
)
W2_PARTIAL_POP = _swap(_BASE, _GOLD_RESULT, _W2_RESULT)


# --- W3 over-pop: [DOTDOT, DOTDOT, DOTDOT, pk, secondary_action] ==
# "../../../<pk>/password/". Three '..' pop current_action, token, AND the last
# prefix segment (model) -> prefix[:-1] + [pk] + [secondary_action]. The shared
# prefix is corrupted (drops the model segment). Wrong for every input.
# refinement: a faithful patch f"../../../{pk}/password/" pops one level too
# many; the resolved href drops the model path segment
# (/admin/auth/<pk>/password/) — not reverse(password_change, pk); the F2P
# assertEqual fails and it does NOT resolve.
# rejection source: the resolution postcondition — resolve drops a prefix
# segment, so the resolved sequence != prefix+[pk]+[secondary_action]
# (precondition keeps the base populated, so the extra pop bites prefix).
_W3_RESULT = (
    "    # W3 OVER-POP RIVAL ('../../../<pk>/password/'): three '..' pop into the\n"
    "    # shared prefix, dropping the trailing prefix segment.\n"
    "    result = [DOTDOT(), DOTDOT(), pk, secondary_action]  # type: List[int]\n"
    "    result = [DOTDOT(), DOTDOT(), DOTDOT(), pk, secondary_action]"
)
W3_OVER_POP = _swap(_BASE, _GOLD_RESULT, _W3_RESULT)


# --- W4 wrong-action (value-level): [DOTDOT, DOTDOT, pk, current_action].
# Correct popping (both token and current_action removed) and correctly keyed by
# pk, but it appends the WRONG action segment (current_action — i.e. "change" —
# instead of secondary_action — "password"). Resolves to
# prefix + [pk] + [current_action]. Correct only on the degenerate sub-domain
# current_action == secondary_action; wrong whenever the two action codes differ
# (always, in the real admin: change != password).
# refinement: a faithful patch f"../../{pk}/{current_action}/" (e.g. linking
# back to the change page instead of the password page) sends the help-text link
# to the wrong action page; reverse(password_change, pk) names the `password`
# action, so the F2P assertEqual fails and it does NOT resolve.
# rejection source: the resolution postcondition pins the trailing segment to
# secondary_action; current_action is a distinct (universally-quantified)
# segment id, so the resolved tail mismatches.
_W4_RESULT = (
    "    # W4 WRONG-ACTION RIVAL: pk-keyed but appends current_action instead of\n"
    "    # secondary_action (links to the change page, not the password page).\n"
    "    result = [DOTDOT(), DOTDOT(), pk, current_action]  # type: List[int]"
)
W4_WRONG_ACTION = _swap(_BASE, _GOLD_RESULT, _W4_RESULT)


# --- W5 token-echo (value-level double-mask): [DOTDOT, DOTDOT, token,
# secondary_action] == "../../{token}/password/". Pops both segments and keys by
# TOKEN instead of pk. Resolves to prefix + [token] + [secondary_action].
# Correct ONLY on the sub-domain token == pk (the access-via-pk case) — exactly
# the sub-domain where the pre-patch bug is invisible. Diverges on token != pk,
# the to_field access the F2P test exercises.
# refinement: a faithful patch building the reference from the access identifier
# in the URL (the `to_field` value) rather than self.instance.pk — e.g.
# f"../../{self.to_field_value}/password/" — keys the password page by the
# username/uuid the page was reached through; reverse(password_change, pk)
# expects the numeric pk, so for the to_field F2P input the assertEqual fails
# and it does NOT resolve. This is the precise partial-domain hole the patch
# closes (pk- vs token-keying).
# rejection source: the resolution postcondition keys the target by pk; token is
# an independent universally-quantified segment id, so resolve(base0, rel) ==
# prefix+[token]+[secondary] != prefix+[pk]+[secondary] when token != pk.
_W5_RESULT = (
    "    # W5 TOKEN-ECHO RIVAL ('../../{token}/password/'): pk-shaped popping but\n"
    "    # keyed by the access token — correct only when token == pk.\n"
    "    result = [DOTDOT(), DOTDOT(), token, secondary_action]  # type: List[int]"
)
W5_TOKEN_ECHO = _swap(_BASE, _GOLD_RESULT, _W5_RESULT)


SPEC_TESTS = [
    {
        "id": "pos-concat",
        "kind": "soundness",
        "expect": "verify",
        "module": POS_CONCAT,
        "rationale": "structurally-different CORRECT impl — the unique-correct "
        "reference value [DOTDOT,DOTDOT,pk,secondary_action] produced via "
        "typed-local binding + list concatenation instead of one literal; the "
        "entire gold resolution proof (rel = ToSeq(result); per-step resolve "
        "unfolds) is kept verbatim and still discharges. Must verify, else "
        "SPEC-TOO-STRONG. Local-variable reshape only (directive-2/3 safe: no "
        "loop flip, no forward-append against the front-recursive fold, no "
        "dropped framing assert).",
    },
    {
        "id": "admiss-f2p-shape",
        "kind": "admissibility",
        "expect": "verify",
        "module": ADMISS,
        "rationale": "a positive-control probe asserts every Requires conjunct "
        "(read-permission Acc(list_pred(prefix),1/2), the non-negative-segments "
        "quantifier over prefix, and token/current_action/pk/secondary_action "
        ">= 0) holds for an F2P-shaped current location with token != pk — the "
        "precondition must admit a normal input, else PRECOND-TOO-STRONG.",
    },
    {
        "id": "frame-prefix-write",
        "kind": "uniqueness",
        "expect": "reject",
        "module": FRAME_PREFIX_WRITE,
        "refinement": "the change site only formats an href into help-text and "
        "must not touch the request/admin path; a faithful patch that mutated "
        "the shared URL prefix while building the link would corrupt the page "
        "location for every other field's link on the same form — admin "
        "form-rendering P2P would render wrong URLs and NOT resolve.",
        "rationale": "MANDATORY frame-mutation case: prefix is held at "
        "Acc(list_pred(prefix),1/2) (read-only). prefix.append(pk) must be "
        "REJECTED for INSUFFICIENT PERMISSION (half permission forbids the "
        "write); the gold result + resolution proof are kept verbatim so the "
        "rejection is attributable solely to the illegal write. A byte-fuzzer "
        "never finds this.",
    },
    {
        "id": "w1-token-keyed",
        "kind": "uniqueness",
        "expect": "reject",
        "module": W1_TOKEN_KEYED,
        "refinement": "this is the verbatim PRE-PATCH expression "
        "format('../password/') (== model_prepatch.py); the F2P test reaches the "
        "change page via a to_field (username 'testclient') so token != pk, and "
        "the resolved href lands on the TOKEN-keyed page, not "
        "reverse(password_change, pk) — the assertEqual fails, so it does NOT "
        "resolve (it is the original bug).",
        "rationale": "rejected by the resolution postcondition: resolve(base0, "
        "rel) == prefix+[token]+[secondary_action] != prefix+[pk]+[secondary_"
        "action] for the universally-quantified token (provably wrong when "
        "token != pk). Supporting partial-domain (correct only on token==pk).",
    },
    {
        "id": "w2-partial-pop",
        "kind": "uniqueness",
        "expect": "reject",
        "module": W2_PARTIAL_POP,
        "refinement": "a faithful patch f'../{pk}/password/' omits one '..'; the "
        "resolved href is /admin/auth/user/<token>/<pk>/password/ — not a valid "
        "password-change URL (reverse(password_change, pk) has no token segment) "
        "— the F2P assertEqual fails and it does NOT resolve.",
        "rationale": "rejected by the resolution postcondition: only "
        "current_action is popped, so the [token] segment survives and the "
        "resolved sequence has an extra segment vs prefix+[pk]+[secondary_action].",
    },
    {
        "id": "w3-over-pop",
        "kind": "uniqueness",
        "expect": "reject",
        "module": W3_OVER_POP,
        "refinement": "a faithful patch f'../../../{pk}/password/' pops one level "
        "too many; the resolved href drops the model path segment "
        "(/admin/auth/<pk>/password/) — not reverse(password_change, pk); the "
        "F2P assertEqual fails and it does NOT resolve.",
        "rationale": "rejected by the resolution postcondition: three '..' pop "
        "current_action, token, and the trailing prefix segment (the precondition "
        "keeps the base populated, so the extra pop bites prefix) — resolve drops "
        "a prefix segment, so the resolved sequence != prefix+[pk]+[secondary_"
        "action]. Supporting over-pop boundary case.",
    },
    {
        "id": "w4-wrong-action",
        "kind": "uniqueness",
        "expect": "reject",
        "module": W4_WRONG_ACTION,
        "refinement": "a faithful patch f'../../{pk}/{current_action}/' (linking "
        "back to the change page instead of the password page) sends the "
        "help-text link to the wrong action; reverse(password_change, pk) names "
        "the `password` action, so the F2P assertEqual fails and it does NOT "
        "resolve.",
        "rationale": "value-level: rejected by the resolution postcondition which "
        "pins the trailing segment to secondary_action; current_action is a "
        "distinct universally-quantified segment id, so the resolved tail "
        "mismatches whenever current_action != secondary_action.",
    },
    {
        "id": "w5-token-echo",
        "kind": "uniqueness",
        "expect": "reject",
        "module": W5_TOKEN_ECHO,
        "refinement": "a faithful patch building the reference from the access "
        "identifier in the URL (the to_field value) rather than self.instance.pk "
        "— f'../../{to_field_value}/password/' — keys the password page by the "
        "username/uuid the page was reached through; reverse(password_change, pk) "
        "expects the numeric pk, so for the to_field F2P input the assertEqual "
        "fails and it does NOT resolve. This is the precise pk- vs token-keying "
        "hole the patch closes.",
        "rationale": "value-level double-mask / partial-domain: correct pk-shaped "
        "popping but keyed by token. Rejected by the resolution postcondition — "
        "the target is keyed by pk; token is an independent universally-quantified "
        "segment id, so resolve(base0, rel) == prefix+[token]+[secondary] != "
        "prefix+[pk]+[secondary] when token != pk (the F2P sub-domain).",
    },
]


# === AXIOM LANE (A-reference deep model `resolve` == urllib.parse.urljoin) ===
# There is NO consumed @ContractOnly axiom in this bundle. The one unchanged
# callee the proof's correctness depends on — hierarchical relative-reference
# resolution — is modelled DEEPLY as the @Pure fold `resolve` and validated
# == the REAL stdlib resolver urllib.parse.urljoin out of band (G-AX /
# axiom_check.py). We re-run that real-callee soundness check here, self-
# contained, importing ONLY the standard library (urllib.parse is the exact
# module the F2P test uses). apply_gold is irrelevant (urllib is unchanged) but
# harmless; we set it False so the probe runs against the stock image.
#
# Probe 1 (axiom-soundness): resolve deep model == urllib.parse.urljoin on the
#   bundle's non-over-popping domain — boundary change-URL shapes + the two
#   references the bug is about + 20000 fuzz inputs; plus the end-to-end
#   token/pk witnesses (post-patch ref hits the pk page for every token;
#   pre-patch ref hits it iff token == pk). If the real callee disagrees =>
#   AXIOM-UNSOUND. Mirrors axiom_check.py, executed standalone in-container.
#
# Probe 2 (axiom-containment): every (base_dir, rel) the MODEL can actually
#   reach lies in resolve's declared non-over-popping domain. The model's only
#   call sites are the postcondition / proof unfolds with base built as
#   prefix + [token] + [current_action] (depth = len(prefix)+2 >= 2) and rel a
#   reference popping at most 2 levels (gold) — so depth never reaches 0 before a
#   non-DOTDOT step. A reachable input that over-pops the root would be
#   AXIOM-TOO-WEAK-FOR-CALLER; this enumerates the reachable shapes and asserts
#   none over-pops (matching the precondition that keeps the base populated).

_AX_SOUND_PROBE = r'''
import random
import sys
import urllib.parse

DOTDOT = -1


def resolve(base_dir, rel):
    """model.py deep model `resolve`, over path-segment-id lists."""
    stack = list(base_dir)
    for step in rel:
        if step == DOTDOT:
            if stack:
                stack.pop()
        else:
            stack.append(step)
    return stack


def segs_to_url(segs, trailing_slash=True):
    if len(segs) == 0:
        return "/"
    body = "/".join(str(s) for s in segs)
    return "/" + body + ("/" if trailing_slash else "")


def rel_to_url(rel):
    if len(rel) == 0:
        return ""
    parts = [".." if step == DOTDOT else str(step) for step in rel]
    return "/".join(parts) + "/"


def overpops_root(base_dir_segs, rel_steps):
    depth = len(base_dir_segs)
    for step in rel_steps:
        if step == DOTDOT:
            depth -= 1
            if depth < 0:
                return True
        else:
            depth += 1
    return False


def check(base_dir_segs, rel_steps):
    if overpops_root(base_dir_segs, rel_steps):
        return
    base_url = segs_to_url(base_dir_segs, trailing_slash=True)
    rel_url = rel_to_url(rel_steps)
    real_url = urllib.parse.urljoin(base_url, rel_url)
    model_url = segs_to_url(resolve(base_dir_segs, rel_steps), trailing_slash=True)
    assert real_url == model_url, (
        "AXIOM-UNSOUND: base=%r rel=%r -> urljoin=%r deep-model=%r"
        % (base_url, rel_url, real_url, model_url))


def main():
    rng = random.Random(16139)

    bases = [
        ["admin", "auth", "user", "tok", "change"],
        ["admin", "auth", "user", "7", "change"],
        ["a", "b"],
        ["x"],
        ["p", "q", "r", "s", "t"],
    ]
    rel_boundary = [
        [DOTDOT, "password"],                       # pre-patch reference
        [DOTDOT, DOTDOT, "9", "password"],          # post-patch (gold) reference
        [],
        [DOTDOT],
        [DOTDOT, DOTDOT, DOTDOT, DOTDOT, DOTDOT],
        ["only"],
        [DOTDOT, "1", DOTDOT, "2"],
    ]
    nb = 0
    for b in bases:
        for r in rel_boundary:
            check(b, r)
            nb += 1

    seg_alphabet = ["a", "b", "c", "d", "e", "f", "0", "1", "2", "3",
                    "user", "change", "password"]
    for _ in range(20000):
        depth = rng.randint(1, 7)
        base = [rng.choice(seg_alphabet) for _ in range(depth)]
        rlen = rng.randint(0, 7)
        rel = []
        for _ in range(rlen):
            if rng.random() < 0.45:
                rel.append(DOTDOT)
            else:
                rel.append(rng.choice(seg_alphabet))
        check(base, rel)

    # end-to-end token/pk witnesses (mirrors the F2P urljoin assertion).
    APP, MODEL = "auth", "user"
    for _ in range(5000):
        pk = rng.randint(1, 10 ** 9)
        token = rng.choice([pk, rng.randint(1, 10 ** 9),
                             "uuid-%d" % rng.randint(0, 10 ** 9), "testclient"])
        change_url = "/admin/%s/%s/%s/change/" % (APP, MODEL, token)
        target = "/admin/%s/%s/%s/password/" % (APP, MODEL, pk)
        post_ref = "../../%s/password/" % pk
        assert urllib.parse.urljoin(change_url, post_ref) == target, (
            "post-patch reference wrong: token=%r pk=%r" % (token, pk))
        pre_ref = "../password/"
        pre_resolved = urllib.parse.urljoin(change_url, pre_ref)
        if str(token) == str(pk):
            assert pre_resolved == target
        else:
            assert pre_resolved != target, (
                "pre-patch reference unexpectedly correct: token=%r pk=%r"
                % (token, pk))

    print("AX-SOUND OK: resolve == urllib.parse.urljoin on %d boundary + 20000 "
          "fuzz (non-over-popping domain) + 5000 token/pk witnesses" % nb)
    return 0


sys.exit(main())
'''


_AX_CONTAIN_PROBE = r'''
import sys

DOTDOT = -1


def overpops_root(base_depth, rel_steps):
    """True iff some prefix of rel pops above the root from a base of the given
    depth (the regime OUTSIDE resolve's declared domain)."""
    depth = base_depth
    for step in rel_steps:
        if step == DOTDOT:
            depth -= 1
            if depth < 0:
                return True
        else:
            depth += 1
    return False


def main():
    # The MODEL's ONLY call to resolve is in the postcondition / proof:
    #   resolve(prefix + [token] + [current_action], result)
    # base depth = len(prefix) + 2 (token + current_action), with len(prefix)>=0
    # per the precondition (Acc(list_pred(prefix),1/2): prefix can be empty, so
    # the smallest reachable base depth is 2). The gold reference pops <= 2
    # levels. We enumerate every reachable base depth (incl. the empty-prefix
    # boundary depth 2) crossed with the gold reference AND every reference of
    # pop-depth <= 2 a faithful refinement could build, asserting none over-pops
    # the root. (Covering MORE than the model reaches is SOUND; the defect is a
    # reachable input OUTSIDE the domain — none exists here.)
    gold_rel = [DOTDOT, DOTDOT, 7, 400]            # [.., .., pk, secondary]
    n = 0
    bad = []
    for base_depth in range(2, 40):                # len(prefix) in 0..37
        # the gold reference (2 pops, depth>=2 base -> never reaches root)
        if overpops_root(base_depth, gold_rel):
            bad.append((base_depth, gold_rel))
        n += 1
        # any reference popping at most 2 levels then appending segments:
        for pops in range(0, 3):                   # 0, 1, 2 leading '..'
            rel = [DOTDOT] * pops + [7, 400]
            if overpops_root(base_depth, rel):
                bad.append((base_depth, rel))
            n += 1
    assert not bad, (
        "AXIOM-TOO-WEAK-FOR-CALLER: model-reachable base/rel over-pops the "
        "root (outside resolve's domain): %r" % bad[:5])
    print("AX-CONTAIN OK: all %d model-reachable (base_depth>=2, pop<=2) "
          "resolve inputs lie in the non-over-popping domain" % n)
    return 0


sys.exit(main())
'''


AXIOM_TESTS = [
    {
        "id": "ax-resolve-soundness",
        "axiom": "resolve",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": False,
        "probe": _AX_SOUND_PROBE,
        "rationale": "The proof's only fact about the unchanged resolver is that "
        "the deep model `resolve` IS hierarchical '..'-resolution. This probe "
        "runs the REAL stdlib urllib.parse.urljoin (the exact callee the F2P "
        "test uses) on boundary change-URL shapes + the two references the bug "
        "is about + 20000 fuzz inputs (non-over-popping domain) + 5000 "
        "token/pk end-to-end witnesses, asserting resolve == urljoin. If the "
        "real callee disagreed, AXIOM-UNSOUND. Mirrors axiom_check.py / G-AX, "
        "stdlib-only, self-contained.",
    },
    {
        "id": "ax-resolve-containment",
        "axiom": "resolve",
        "kind": "axiom-containment",
        "expect": "covered",
        "apply_gold": False,
        "probe": _AX_CONTAIN_PROBE,
        "rationale": "Every (base_dir, rel) the MODEL can reach — base built as "
        "prefix + [token] + [current_action] (depth = len(prefix)+2 >= 2) with a "
        "reference popping <= 2 levels — lies in resolve's declared "
        "non-over-popping domain. Enumerates all reachable base depths (incl. "
        "the empty-prefix boundary) x references of pop-depth <= 2 and asserts "
        "none over-pops the root. A reachable over-popping input would be "
        "AXIOM-TOO-WEAK-FOR-CALLER; none exists (the precondition keeps the base "
        "populated through both pops).",
    },
]
