"""PBT manifest for django__django-10097 (NOT a Nagini module; a record of
adversarial cases the runner swebench_nagini.pbt executes + stamps RESULT).

Defended surface (frozen spec in model.py; see refinement.md / mapping.md):

  validate_authsegment(seg: List[int]) -> bool
    Requires: Acc(list_pred(seg), 1/2)            -- seg is READ-ONLY (1/2 perm)
    Ensures (frame): Acc(list_pred(seg), 1/2)     -- the 1/2 perm is returned
    Ensures (DECISION, load-bearing):
        Result() == accepts(ToSeq(seg))

  accepts(s) = len(s) > 0 AND body_ok(s) AND colons(s) <= 1 AND s[0] != 58
    body_ok(s): every code point is an authentication char (is_uchar: not
                whitespace AND not ':'(58)/'@'(64)/'/'(47)) or the one permitted
                separator ':' ; front-recursive @Pure fold.
    colons(s):  count of ':' ; front-recursive @Pure fold.

This models the gold one-line regex narrowing of URLValidator's userinfo group
  -  r'\\S+(?::\\S*)?'              (pre-patch: only whitespace excluded)
  +  r'[^\\s:@/]+(?::[^\\s:@/]*)?'  (post-patch: ':', '@', '/' also excluded)

GROUNDED-ORACLE NOTE: the postcondition oracle `accepts(ToSeq(seg))` is GROUNDED
in the argument -- it is a @Pure fold fully computable from `seg`, with no opaque
answer-key. So there is NO *wrong* echo a rival can return: `return
accepts(ToSeq(seg))` is the honest cheapest impl and is a CORRECT positive
control (included below), not an ungrounded-oracle attack. The uniqueness lane is
therefore about whether a rival can satisfy the decision on the F2P domain while
diverging on a discriminating sub-domain (extra colon / leading colon / a '/' or
'@' inside the segment) -- the exact behaviours the gold patch newly rejects.

AXIOM LANE: there is NO @ContractOnly axiom in this bundle (axioms region empty).
The changed matcher is modelled DEEPLY (pure region) and validated == the real
compiled userinfo group out-of-band by axiom_check.py (G-AX). PBT re-runs that
real-callee equivalence as an axiom-soundness probe (the deep model `accepts`
must equal `re.compile(r'[^\\s:@/]+(?::[^\\s:@/]*)?', re.IGNORECASE).fullmatch`
on the issue's discriminating segments + the full Unicode-\\s per-code-point
sweep + fuzz). axiom_check.py's logic is read on the HOST at load time and
embedded into the probe string (the runner mounts only the probe at /work).

REGION-SURGERY: every spec variant is built by _swap on _BASE editing ONLY text
inside # impl-start/# impl-end (the invariants are nested inside that region, so
editing them is still inside impl and preserves same_spec). The frozen spec
(axioms/pure/pre/post-conditions/signatures) is never touched.
"""
from pathlib import Path

INSTANCE = "django__django-10097"
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
_HEAD = "    n = len(seg)\n    if n == 0:"
_LEADING_GUARD = "    if seg[0] == 58:\n        return False\n"
_READ_C = "        c = seg[i - 1]\n"
_DISCR = ("        if c == 58:\n"
          "            ncolon = ncolon + 1\n"
          "        elif not is_uchar(c):\n"
          "            good = False\n")
_INV_GOOD = "        Invariant(good == body_ok(ToSeq(seg).drop(i)))\n"
_INV_LEAD = "        Invariant(seg[0] != 58)\n"
_ASSERT_GOOD = "    Assert(good == body_ok(ToSeq(seg)))\n"
_ASSERT_LEAD = "    Assert(ToSeq(seg)[0] != 58)\n"
_RETURN = "    return good and ncolon <= 1"

for _a in (_HEAD, _LEADING_GUARD, _READ_C, _DISCR, _INV_GOOD, _INV_LEAD,
           _ASSERT_GOOD, _ASSERT_LEAD, _RETURN):
    assert _BASE.count(_a) == 1, f"anchor drifted: {_a!r}"


# ===========================================================================
# POSITIVE CONTROLS / ADMISSIBILITY  (expect "verify")
# ===========================================================================

# (5a) POSITIVE CONTROL -- branch reorder. The gold `if c==58 / elif not
# is_uchar(c)` is split into two INDEPENDENT guarded statements that are
# semantically identical (the second is guarded by `c != 58` so a ':' never
# clears `good`, matching body_ok which treats ':' as OK). All invariants and
# framing asserts are kept verbatim, so the gold proof stays valid. MUST verify;
# else the postcondition is over-fit to one branch FORM => SPEC-TOO-STRONG.
_POS_REORDER = _swap(
    _BASE, _DISCR,
    "        if c == 58:\n"
    "            ncolon = ncolon + 1\n"
    "        if c != 58 and not is_uchar(c):\n"
    "            good = False\n",
)

# (5b) POSITIVE CONTROL -- the cheapest HONEST impl. The oracle `accepts` is
# GROUNDED in the argument (a @Pure fold), so directly returning it is a correct,
# fully-grounded implementation, not an ungrounded-oracle echo. MUST verify (the
# postcondition is literally Result() == accepts(ToSeq(seg))); else SPEC-TOO-STRONG
# and it also demonstrates the spec is not echo-vulnerable (there is no WRONG echo
# to build -- a wrong constant would fail the postcondition).
_IMPL_BODY_START = "    n = len(seg)"
_POS_DIRECT = _swap(
    _BASE,
    _BASE[_BASE.index(_IMPL_BODY_START):_BASE.index("    # impl-end")],
    "    return accepts(ToSeq(seg))\n",
)

# (6) ADMISSIBILITY -- a self-call on a fresh, F2P-shaped input "foo"
# ([102,111,111], a normal valid user run) establishes Acc(list_pred(.),1/2);
# then the gold body runs on the actual `seg`. MUST verify; else the precondition
# rejects a normal input => PRECOND-TOO-STRONG.
_POS_ADMISS = _swap(
    _BASE, _HEAD,
    "    probe = [102, 111, 111]  # type: List[int]\n"
    "    Assert(Acc(list_pred(probe), 1 / 2))\n"
    "    n = len(seg)\n    if n == 0:",
)


# ===========================================================================
# UNIQUENESS RIVALS  (spec-too-weak probes -- expect "reject")
# ===========================================================================

# (1) FRAME MUTATION -- MANDATORY (#1 weakness class). seg is read-only at 1/2.
# This rival WRITES `seg[i - 1] = 102` ('f') before reading it, attempting to
# normalize the input so the decision is vacuously satisfiable. Under
# Acc(list_pred(seg),1/2) a store needs FULL permission, so it must be rejected
# for INSUFFICIENT PERMISSION (not a value mismatch). All gold invariants/asserts
# are kept verbatim, so the rejection is attributable solely to the write.
_RIVAL_FRAME = _swap(
    _BASE, _READ_C,
    "        seg[i - 1] = 102\n        c = seg[i - 1]\n",
)

# (3a) PARTIAL-DOMAIN -- drop the colon-count guard. Returns `good` only, so a
# segment with TWO OR MORE ':' (e.g. "foo:bar:baz") is accepted (good == body_ok
# is True; ':' is permitted by body_ok) even though accepts() rejects it
# (colons > 1). All invariants/asserts are kept verbatim, so good == body_ok and
# ncolon == colons are PROVEN at return; the postcondition Result()==accepts then
# requires body_ok == (body_ok AND colons<=1), i.e. colons<=1 ALWAYS -- false on
# any 2-colon input. Correct on every <=1-colon input, wrong on >=2-colon ones.
_RIVAL_DROP_COLON = _swap(_BASE, _RETURN, "    return good")

# (3b) PARTIAL-DOMAIN -- whitespace-only class (the EXACT pre-patch \\S behaviour
# this gold hunk replaces; == model_prepatch.py). The discriminating elif is
# changed to reject only WHITESPACE, so '/' and '@' inside the segment are
# treated as acceptable. body_ok still rejects '/'/'@', so the loop's `good ==
# body_ok` invariant and final assert are gutted to Invariant(True)/Assert(True)
# to make the rival internally consistent; the ONLY remaining discriminator is
# the postcondition Result()==accepts, which the verifier cannot close because
# the whitespace-only `good` disagrees with accepts on e.g. "foo/bar","foo@bar".
_RIVAL_WS = _swap(_BASE, _DISCR,
                  "        if c == 58:\n"
                  "            ncolon = ncolon + 1\n"
                  "        elif is_whitespace(c):\n"
                  "            good = False\n")
_RIVAL_WS = _swap(_RIVAL_WS, _INV_GOOD, "        Invariant(True)\n")
_RIVAL_WS = _swap(_RIVAL_WS, _ASSERT_GOOD, "    Assert(True)\n")

# (3c) PARTIAL-DOMAIN -- drop the leading-colon guard. The early `seg[0]==58 ->
# return False` is removed (and its supporting invariant/assert, both inside the
# impl region, so same_spec holds), so a segment that BEGINS with ':' (empty user
# run, e.g. ":pass" or ":") is accepted: body_ok([58,...]) is True and ncolon<=1,
# yet accepts() rejects it (s[0]==58). The postcondition Result()==accepts cannot
# be closed on leading-colon inputs. Correct on every non-leading-colon input.
_RIVAL_LEADCOLON = _swap(_BASE, _LEADING_GUARD, "")
_RIVAL_LEADCOLON = _swap(_RIVAL_LEADCOLON, _INV_LEAD, "")
_RIVAL_LEADCOLON = _swap(_RIVAL_LEADCOLON, _ASSERT_LEAD, "")


SPEC_TESTS = [
    # ---- positive controls (must VERIFY) ----
    {"id": "pos-control-reorder", "kind": "soundness", "expect": "verify",
     "module": _POS_REORDER,
     "rationale": "structurally-different (the colon-count and uchar checks split "
                  "into two independent guarded ifs, semantically identical to the "
                  "gold if/elif) but CORRECT impl, keeping every gold invariant and "
                  "framing assert. Must verify; else the postcondition is over-fit to "
                  "the if/elif FORM => SPEC-TOO-STRONG."},
    {"id": "pos-control-direct", "kind": "soundness", "expect": "verify",
     "module": _POS_DIRECT,
     "rationale": "the oracle accepts(ToSeq(seg)) is GROUNDED in the argument (a @Pure "
                  "fold), so `return accepts(ToSeq(seg))` is the honest cheapest CORRECT "
                  "impl, not an ungrounded echo. Must verify (postcondition is literally "
                  "Result()==accepts); else SPEC-TOO-STRONG. Also shows the spec is not "
                  "echo-vulnerable: any WRONG constant/echo fails the postcondition."},
    {"id": "admiss-selfcall", "kind": "admissibility", "expect": "verify",
     "module": _POS_ADMISS,
     "rationale": "a self-call on a fresh F2P-shaped valid user run \"foo\" "
                  "([102,111,111]) must establish the precondition Acc(list_pred(.),1/2) "
                  "and the result-property assert (Result()==accepts(ToSeq(probe))). If "
                  "the precondition rejects this normal input => PRECOND-TOO-STRONG."},

    # ---- uniqueness rivals (must be REJECTED) ----
    {"id": "frame-mutate-seg", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_FRAME,
     "refinement": "no faithful real patch corresponds to this: URLValidator never "
                   "mutates the URL string it inspects (a str, immutable), it only "
                   "matches against it. The rival exists solely to test whether the "
                   "read-only (1/2) precondition can be subverted by overwriting `seg`. "
                   "There is no resolving patch that rewrites its input segment, so a "
                   "verifying rival here would be a pure verify-not-resolve artifact "
                   "(vacuous satisfaction via self-normalization).",
     "rationale": "MANDATORY frame-mutation probe. `seg[i-1] = 102` writes through a 1/2 "
                  "(read-only) reference and MUST fail for INSUFFICIENT PERMISSION (a "
                  "store needs full Acc(list_pred(seg))), NOT a value mismatch; the gold "
                  "invariants/asserts are kept verbatim so the rejection is attributable "
                  "to the write. Rejection source: the PERMISSION SYSTEM. If it verified "
                  "=> SPEC-TOO-WEAK (frame protection hollow)."},
    {"id": "weak-drop-colon-guard", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_DROP_COLON,
     "refinement": "dropping the colons<=1 check is exactly the pre-patch \\S+(?::\\S*)? "
                   "behaviour for multiple colons: it accepts \"foo:bar:baz\" (two ':'), "
                   "which the gold-narrowed group [^\\s:@/]+(?::[^\\s:@/]*)? rejects (only "
                   "one optional ':' separator). A faithful patch doing this still accepts "
                   "http://foo:bar:baz@example.com and FAILS the F2P (invalid_urls.txt now "
                   "lists that URL as invalid) -- verify-not-resolve.",
     "rationale": "rejection source: the postcondition Result()==accepts(ToSeq(seg)). All "
                  "invariants/asserts are kept verbatim so good==body_ok and "
                  "ncolon==colons are PROVEN at return; with Result()==good the "
                  "postcondition reduces to requiring colons<=1 unconditionally, false on "
                  "any segment with >=2 colons. If it verified => SPEC-TOO-WEAK."},
    {"id": "weak-whitespace-only", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_WS,
     "refinement": "this is the EXACT pre-patch character class \\S (only whitespace "
                   "excluded): '/' and '@' are treated as acceptable inside the segment, "
                   "so it accepts \"foo/bar\" and \"foo@bar\" which the gold group "
                   "[^\\s:@/] rejects. A faithful patch keeping \\S (== model_prepatch.py) "
                   "still accepts http://foo/bar@example.com and http://foo@bar@example.com "
                   "and FAILS the F2P (both now in invalid_urls.txt) -- verify-not-resolve.",
     "rationale": "rejection source: the postcondition Result()==accepts(ToSeq(seg)). The "
                  "whitespace-only `good` disagrees with accepts on any segment containing "
                  "'/' or '@' (accepts requires every non-':' code point to be is_uchar, "
                  "which excludes '/'/'@'); the verifier cannot close Result()==accepts. If "
                  "it verified => SPEC-TOO-WEAK (the narrowing to [^\\s:@/] would be hollow)."},
    {"id": "weak-leading-colon", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_LEADCOLON,
     "refinement": "dropping the leading-':' guard accepts a segment with an EMPTY user "
                   "run, e.g. \":pass\" or \":\", which the gold group rejects (the leading "
                   "[^\\s:@/]+ user run is mandatory, '+' not '*'). A faithful patch "
                   "accepting a leading ':' would accept URLs like http://:pass@example.com "
                   "that the post-patch validator must reject -- verify-not-resolve "
                   "(it diverges from the gold matcher on the leading-colon sub-domain).",
     "rationale": "rejection source: the postcondition Result()==accepts(ToSeq(seg)). With "
                  "the leading-':' early return removed, a single-':' input (\":\" or "
                  "\":pass\") yields good==body_ok==True and ncolon<=1 so Result()==True, "
                  "but accepts is False (s[0]==58). The verifier cannot close "
                  "Result()==accepts on leading-colon inputs. If it verified => "
                  "SPEC-TOO-WEAK."},
]


# ===========================================================================
# AXIOM LANE -- no @ContractOnly axiom is consumed; the changed matcher is an
# A-reference deep model validated == the real compiled userinfo group. We re-run
# that real-callee equivalence (axiom_check.py's logic, read on the HOST and
# embedded into a self-contained probe) as an axiom-soundness check: if the deep
# model `accepts` ever disagrees with the real compiled group, the A-reference is
# unsound. A containment probe is N/A (no axiom Requires domain to fall outside).
# ===========================================================================

_AXIOM_CHECK_SRC = (_DIR / "axiom_check.py").read_text()

AXIOM_TESTS = [
    {
        "id": "ax-ref-accepts-equals-real-matcher",
        "axiom": "accepts",  # the A-reference deep model (not a consumed axiom)
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _AXIOM_CHECK_SRC,
        "rationale": "the deep model accepts (pure region) is an A-reference: it must "
                     "equal the REAL post-patch compiled userinfo group "
                     "re.compile(r'[^\\s:@/]+(?::[^\\s:@/]*)?', re.IGNORECASE).fullmatch "
                     "on every input. This probe (axiom_check.py verbatim, stdlib `re` "
                     "only) runs the real matcher on the issue's discriminating segments "
                     "(foo/bar, foo@bar, foo:bar:baz, leading ':'), a per-code-point sweep "
                     "over the full 29-code-point Unicode-\\s class, and 100000 fuzz "
                     "strings, asserting accepts == fullmatch. Exit 0 iff every "
                     "observation agrees; any disagreement => the A-reference is UNSOUND.",
    },
]
