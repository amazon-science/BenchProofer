# properties.py — PBT manifest for django__django-12143. NOT a Nagini module; a
# record of adversarial cases the runner (swebench_nagini.pbt) parses.
#
# INSTANCE SHAPE. One changed behaviour (django admin _get_edited_object_pks):
# the per-key acceptance test pk_pattern.match(key), where the gold fix wraps the
# group label in re.escape so the label is matched LITERALLY instead of as a
# regex. Modeled by `is_edited_pk_key(prefix, pkname, key)` whose load-bearing
# postcondition is
#
#     Ensures(Result() == recognises(ToSeq(prefix), ToSeq(pkname), ToSeq(key)))
#
# `recognises` is a @Pure structural decomposition  prefix · '-' · \d+ · '-' ·
# pkname  consuming the whole key, with `prefix` matched code-point-for-code-point
# (prefix_eq). Two verified helpers `match_literal` / `run_is_digits` compute the
# literal / digit-run sub-claims so the index-recursive predicate discharges.
#
# READ-ONLY INPUTS. is_edited_pk_key takes prefix, pkname, key all at
# Acc(list_pred(.), 1/2); match_literal/run_is_digits take their lists at 1/4.
# Every input is read-only => the frame-mutation probe is MANDATORY (a rival that
# WRITES the read-only input must reject for INSUFFICIENT PERMISSION).
#
# GROUNDED ORACLE (no ungrounded-echo class). `recognises` is NOT an opaque
# answer-key: it is fully unfolded as a pure function of (prefix, pkname, key)
# (the spelled-out decomposition with prefix_eq / all_digits). So `return
# recognises(ToSeq(prefix), ToSeq(pkname), ToSeq(key))` is a CORRECT impl, not a
# wrong echo — it is included as the honest cheapest-impl positive control
# (sc-echo). There is no value of the args on which an echo of `recognises`
# diverges from `recognises`, so there is no ungrounded-oracle-echo rival to
# build (stated in assessment). The wrong impls instead attack specific
# sub-domains of the recognition decision (incl. the exact pre-patch bug).
#
# A-REFERENCE (axiom lane). meta.axioms == [] (no @ContractOnly consumed axiom),
# but deep_model_references carries `recognises` as an A-reference: the deep model
# is validated == the REAL post-fix compiled-pattern match by axiom_check.py
# (G-AX). The axiom lane therefore re-runs the real CPython `re` callee in-Docker
# and re-asserts (1) recognises == real re.escape-fixed match over the scoped
# realistic-POST-key domain (axiom-soundness) and (2) that every callee-input the
# model can reach lies in that scoped domain (axiom-containment). Probes embed the
# host axiom_check.py oracle source (only stdlib `re` is needed in-container).
from pathlib import Path

INSTANCE = "django__django-12143"
FLOAT_ENCODING = None  # meta.json float_encoding is null and unused

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- exact impl-region bodies (verbatim from model.py, between the markers) ----
# Every variant is produced by _swap on one of these anchors; the markers
# themselves and everything outside the impl regions (signatures, @Pure helpers,
# pre/post-conditions) are NEVER touched => same_spec is guaranteed.

# --- the is_edited_pk_key impl body (the headline modeled function) ---
_IMPL3 = (
    "    np = len(prefix)\n"
    "    nk = len(pkname)\n"
    "    n = len(key)\n"
    "    d = n - np - nk - 2\n"
    "    if d < 1:\n"
    "        Assert(not recognises(ToSeq(prefix), ToSeq(pkname), ToSeq(key)))\n"
    "        return False\n"
    "    # d >= 1, and n == np + 2 + d + nk, so every index/slice below is in bounds.\n"
    "    Assert(n == np + 2 + d + nk)\n"
    "    Assert(0 <= np and np < n)\n"
    "    Assert(np + 1 + d <= n and np + 1 + d < n)\n"
    "    Assert(np + 2 + d + nk == n)\n"
    "    ok_label = match_literal(key, 0, prefix)\n"
    "    Assert(len(key) == n)\n"
    "    Assert(ToSeq(key).drop(0) == ToSeq(key))\n"
    "    Assert(ok_label == prefix_eq(ToSeq(key), ToSeq(prefix)))\n"
    "    Assert(0 <= np and np < len(key))\n"
    "    hyphen1 = (key[np] == 45)\n"
    "    ok_digits = run_is_digits(key, np + 1, np + 1 + d)\n"
    "    Assert(len(key) == n)\n"
    "    Assert(0 <= np + 1 + d and np + 1 + d < len(key))\n"
    "    hyphen2 = (key[np + 1 + d] == 45)\n"
    "    ok_name = match_literal(key, np + 2 + d, pkname)\n"
    "    Assert(recognises(ToSeq(prefix), ToSeq(pkname), ToSeq(key))\n"
    "           == (ok_label and hyphen1 and ok_digits and hyphen2 and ok_name))\n"
    "    return ok_label and hyphen1 and ok_digits and hyphen2 and ok_name\n"
)

# --- the match_literal impl body (verified helper) ---
_IMPL1 = (
    "    m = len(lit)\n"
    "    ok = True\n"
    "    i = m\n"
    "    while i > 0:\n"
    "        # invariants-start\n"
    "        Invariant(Acc(list_pred(key), 1 / 4))\n"
    "        Invariant(Acc(list_pred(lit), 1 / 4))\n"
    "        Invariant(0 <= i and i <= m and m == len(lit))\n"
    "        Invariant(0 <= off and off + m <= len(key))\n"
    "        Invariant(len(ToSeq(lit).drop(i)) <= len(ToSeq(key).drop(off + i)))\n"
    "        Invariant(ok == prefix_eq(ToSeq(key).drop(off + i), ToSeq(lit).drop(i)))\n"
    "        Invariant(MustTerminate(i + 1))\n"
    "        # invariants-end\n"
    "        Assert(ToSeq(key).drop(off + i - 1)[0] == ToSeq(key)[off + i - 1])\n"
    "        Assert(ToSeq(lit).drop(i - 1)[0] == ToSeq(lit)[i - 1])\n"
    "        Assert(ToSeq(key).drop(off + i - 1).drop(1) == ToSeq(key).drop(off + i))\n"
    "        Assert(ToSeq(lit).drop(i - 1).drop(1) == ToSeq(lit).drop(i))\n"
    "        if key[off + i - 1] != lit[i - 1]:\n"
    "            ok = False\n"
    "        i = i - 1\n"
    "    Assert(ToSeq(key).drop(off + 0) == ToSeq(key).drop(off))\n"
    "    Assert(ToSeq(lit).drop(0) == ToSeq(lit))\n"
    "    return ok\n"
)

# sanity: the bodies appear verbatim & uniquely in the frozen model.
assert _BASE.count(_IMPL3) == 1, "IMPL3 anchor drift"
assert _BASE.count(_IMPL1) == 1, "IMPL1 anchor drift"


# ============================================================================
# is_edited_pk_key rivals (the changed behaviour)
# ============================================================================

# --- FRAME-MUTATION (MANDATORY: key is Acc(list_pred(key), 1/2) read-only) ---
# Rival WRITES to `key` (the submitted POST key list). A frame-mutation attacker
# could try to normalise the key in place before deciding. Writing to a
# half-permission list is forbidden, so this must REJECT for INSUFFICIENT
# PERMISSION — not for a value mismatch. The whole gold body (and its
# postcondition tie-up) is kept verbatim AFTER the write, so the rejection is
# attributable solely to the append.
_F3_FRAME_KEY = (
    "    key.append(45)\n"
) + _IMPL3

# --- FRAME-MUTATION on prefix (the read-only group label, Acc 1/2) ---
# A rival might try to "escape" the label by mutating prefix in place. prefix is
# read-only at 1/2 permission, so the write is rejected for insufficient
# permission. Supporting case; same permission-discipline point as F3_FRAME_KEY
# but on the input the gold fix actually re.escapes.
_F3_FRAME_PREFIX = (
    "    prefix.append(45)\n"
) + _IMPL3

# --- THE REAL BUG (== model_prepatch.py): label '$' honoured as an anchor ---
# Verbatim pre-patch skeleton: when the label's final code point is U+0024 ('$'),
# the matching engine treats it as an end-of-text anchor instead of a literal, so
# a key that continues past it with the '-<digits>-<field name>' tail is wrongly
# REJECTED. This is EXACTLY the pre-fix `re.compile(r'{}-\d+-{}$'.format(prefix,
# ...))` behaviour the gold patch repairs with re.escape. On the F2P input
# prefix='form$', key='form$-0-uuid' recognises is True but this rival returns
# False -> the edited row is dropped (the data-loss bug) -> F2P
# test_get_list_editable_queryset_with_regex_chars_in_prefix fails (count 0 != 1).
# NOTE the gold tie-up Assert(recognises == conjunction) is removed (as in
# model_prepatch.py) precisely because the forced ok_label=False makes the
# conjunction diverge from recognises; the rejection then lands on the
# POSTCONDITION Result() == recognises, not on an internal assert.
_F3_REALBUG = (
    "    np = len(prefix)\n"
    "    nk = len(pkname)\n"
    "    n = len(key)\n"
    "    d = n - np - nk - 2\n"
    "    if d < 1:\n"
    "        Assert(not recognises(ToSeq(prefix), ToSeq(pkname), ToSeq(key)))\n"
    "        return False\n"
    "    Assert(n == np + 2 + d + nk)\n"
    "    Assert(0 <= np and np < n)\n"
    "    Assert(np + 1 + d <= n and np + 1 + d < n)\n"
    "    Assert(np + 2 + d + nk == n)\n"
    "    ok_label = match_literal(key, 0, prefix)\n"
    "    Assert(len(key) == n)\n"
    "    Assert(ToSeq(key).drop(0) == ToSeq(key))\n"
    "    Assert(ok_label == prefix_eq(ToSeq(key), ToSeq(prefix)))\n"
    "    label_ends_in_anchor = (np >= 1 and prefix[np - 1] == 36)\n"
    "    if label_ends_in_anchor:\n"
    "        ok_label = False\n"
    "    Assert(0 <= np and np < len(key))\n"
    "    hyphen1 = (key[np] == 45)\n"
    "    ok_digits = run_is_digits(key, np + 1, np + 1 + d)\n"
    "    Assert(len(key) == n)\n"
    "    Assert(0 <= np + 1 + d and np + 1 + d < len(key))\n"
    "    hyphen2 = (key[np + 1 + d] == 45)\n"
    "    ok_name = match_literal(key, np + 2 + d, pkname)\n"
    "    return ok_label and hyphen1 and ok_digits and hyphen2 and ok_name\n"
)

# --- PARTIAL-DOMAIN: drop the literal-label check (ignore ok_label) ---
# Returns the recognition decision WITHOUT requiring the leading label to match
# literally. Faithful real patch: a pattern that drops the leading group label
# entirely (e.g. r'-\d+-{}$'.format(pkname)) — it would accept keys belonging to a
# DIFFERENT formset prefix (any '...-\d+-pkname'), miscounting edited rows across
# inline formsets. Diverges from recognises on every key whose label is wrong but
# whose '-\d+-pkname' tail is right (e.g. prefix='form', key='xxxx-0-uuid':
# recognises=False, rival=True). The gold tie-up Assert(recognises == full
# conjunction) stays provable; the rejection lands on the POSTCONDITION because
# Result() drops the ok_label conjunct.
_F3_DROP_LABEL = _swap(
    _IMPL3,
    "    return ok_label and hyphen1 and ok_digits and hyphen2 and ok_name\n",
    "    return hyphen1 and ok_digits and hyphen2 and ok_name\n",
)

# --- PARTIAL-DOMAIN: drop the digit-run check (treat the middle as always OK) ---
# Skips run_is_digits and asserts the middle region is digits unconditionally.
# Faithful real patch: replacing the `\d+` sub-pattern with `.+` (or `[^-]+`) — it
# would accept a non-numeric middle segment, recognising keys that are not real
# `prefix-<int>-pkname` formset keys. Diverges from recognises on e.g.
# prefix='form', key='form-0a-uuid' (recognises=False, rival=True). Rejected by
# the POSTCONDITION: Result() omits the ok_digits conjunct while recognises
# requires all_digits.
_F3_DROP_DIGITS = (
    "    np = len(prefix)\n"
    "    nk = len(pkname)\n"
    "    n = len(key)\n"
    "    d = n - np - nk - 2\n"
    "    if d < 1:\n"
    "        Assert(not recognises(ToSeq(prefix), ToSeq(pkname), ToSeq(key)))\n"
    "        return False\n"
    "    Assert(n == np + 2 + d + nk)\n"
    "    Assert(0 <= np and np < n)\n"
    "    Assert(np + 1 + d <= n and np + 1 + d < n)\n"
    "    Assert(np + 2 + d + nk == n)\n"
    "    ok_label = match_literal(key, 0, prefix)\n"
    "    Assert(len(key) == n)\n"
    "    Assert(ToSeq(key).drop(0) == ToSeq(key))\n"
    "    Assert(ok_label == prefix_eq(ToSeq(key), ToSeq(prefix)))\n"
    "    Assert(0 <= np and np < len(key))\n"
    "    hyphen1 = (key[np] == 45)\n"
    "    ok_digits = True\n"
    "    Assert(len(key) == n)\n"
    "    Assert(0 <= np + 1 + d and np + 1 + d < len(key))\n"
    "    hyphen2 = (key[np + 1 + d] == 45)\n"
    "    ok_name = match_literal(key, np + 2 + d, pkname)\n"
    "    return ok_label and hyphen1 and ok_digits and hyphen2 and ok_name\n"
)

# --- PARTIAL-DOMAIN: drop the second-hyphen check (ignore hyphen2) ---
# Omits the `key[np+1+d] == 45` separator requirement. Faithful real patch: a
# pattern that uses `\d+.{}$` (any single char before the field name) instead of
# the literal '-'. Diverges from recognises on a key where the second separator is
# not '-' (e.g. prefix='form', key='form-0xuuid' decomposed with d=1: separator
# 'x' not '-'; recognises=False, rival=True). Rejected by the POSTCONDITION
# (Result() drops the hyphen2 conjunct).
_F3_DROP_HYPHEN2 = _swap(
    _IMPL3,
    "    hyphen2 = (key[np + 1 + d] == 45)\n",
    "    hyphen2 = True\n",
)

# --- POSITIVE CONTROL (soundness): structurally-different but CORRECT ---
# Branch-reshape: the five conjuncts are accumulated into a single boolean local
# `acc` with explicit short-circuit-free conjunction, and the result is returned
# from `acc`. Same content as the gold conjunction; KEEPS the gold tie-up
# Assert(recognises == (ok_label and ... )) verbatim so the postcondition still
# discharges. Different executable shape, identical value -> MUST verify (else
# SPEC-TOO-STRONG). No new loop/lemma is introduced, so there is no proof-gap
# risk (avoids pilot bug #2/#3).
_F3_POS = (
    "    np = len(prefix)\n"
    "    nk = len(pkname)\n"
    "    n = len(key)\n"
    "    d = n - np - nk - 2\n"
    "    if d < 1:\n"
    "        Assert(not recognises(ToSeq(prefix), ToSeq(pkname), ToSeq(key)))\n"
    "        return False\n"
    "    Assert(n == np + 2 + d + nk)\n"
    "    Assert(0 <= np and np < n)\n"
    "    Assert(np + 1 + d <= n and np + 1 + d < n)\n"
    "    Assert(np + 2 + d + nk == n)\n"
    "    ok_label = match_literal(key, 0, prefix)\n"
    "    Assert(len(key) == n)\n"
    "    Assert(ToSeq(key).drop(0) == ToSeq(key))\n"
    "    Assert(ok_label == prefix_eq(ToSeq(key), ToSeq(prefix)))\n"
    "    Assert(0 <= np and np < len(key))\n"
    "    hyphen1 = (key[np] == 45)\n"
    "    ok_digits = run_is_digits(key, np + 1, np + 1 + d)\n"
    "    Assert(len(key) == n)\n"
    "    Assert(0 <= np + 1 + d and np + 1 + d < len(key))\n"
    "    hyphen2 = (key[np + 1 + d] == 45)\n"
    "    ok_name = match_literal(key, np + 2 + d, pkname)\n"
    "    acc = ok_name\n"
    "    acc = hyphen2 and acc\n"
    "    acc = ok_digits and acc\n"
    "    acc = hyphen1 and acc\n"
    "    acc = ok_label and acc\n"
    "    Assert(acc == (ok_label and hyphen1 and ok_digits and hyphen2 and ok_name))\n"
    "    Assert(recognises(ToSeq(prefix), ToSeq(pkname), ToSeq(key))\n"
    "           == (ok_label and hyphen1 and ok_digits and hyphen2 and ok_name))\n"
    "    return acc\n"
)

# --- POSITIVE CONTROL (cheapest honest echo of the GROUNDED oracle) ---
# `recognises` is fully grounded (a pure function of the args), so directly
# returning it is the cheapest CORRECT impl, not a wrong echo. It trivially
# satisfies Result() == recognises(...) and keeps every input read-only. MUST
# verify; documents that the oracle is grounded (no ungrounded-echo rival exists).
_F3_ECHO = (
    "    return recognises(ToSeq(prefix), ToSeq(pkname), ToSeq(key))\n"
)

# --- ADMISSIBILITY: self-call on the exact F2P-shaped input ---
# Builds the concrete F2P input as fresh code-point lists (prefix='form$' =
# [102,111,114,109,36]; pkname='uuid' = [117,117,105,100]; key='form$-0-uuid' =
# [102,111,114,109,36,45,48,45,117,117,105,100]), invokes is_edited_pk_key on it,
# and asserts the recognition is True (recognises('form$','uuid','form$-0-uuid')
# == True). If the Requires rejected this normal POST-key input the call site
# would fail -> PRECOND-TOO-STRONG. The gold body is kept afterwards.
_F3_ADMISS = (
    "    s_prefix = [102, 111, 114, 109, 36]  # type: List[int]\n"
    "    s_pkname = [117, 117, 105, 100]  # type: List[int]\n"
    "    s_key = [102, 111, 114, 109, 36, 45, 48, 45, 117, 117, 105, 100]  # type: List[int]\n"
    "    Assert(Acc(list_pred(s_prefix), 1 / 2))\n"
    "    Assert(Acc(list_pred(s_pkname), 1 / 2))\n"
    "    Assert(Acc(list_pred(s_key), 1 / 2))\n"
) + _IMPL3


# ============================================================================
# match_literal rival (supporting frame-mutation on the helper surface)
# ============================================================================

# --- FRAME-MUTATION on a 1/4-permission helper input ---
# match_literal takes key, lit at Acc(list_pred(.), 1/4). A rival that writes to
# `lit` (the literal sub-pattern carrier) must reject for INSUFFICIENT
# PERMISSION. Supporting case demonstrating the permission discipline holds on the
# verified-helper surface too (the helpers have no behavioural counterpart, so the
# refinement is that a mutating helper has no faithful repo realisation).
_F1_FRAME = (
    "    lit.append(45)\n"
) + _IMPL1


SPEC_TESTS = [
    # ---------------- is_edited_pk_key: the changed behaviour ----------------
    {
        "id": "frame-mutation-key",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL3, _F3_FRAME_KEY),
        "refinement": "Appends to `key`, the submitted POST key, held at "
                      "Acc(list_pred(key), 1/2). A real patch cannot mutate the "
                      "POST key (request key strings are immutable and shared); a "
                      "faithful realisation would corrupt request.POST rather than "
                      "implement the re.escape recognition fix, so it does not "
                      "resolve the F2P.",
        "rationale": "Must reject for INSUFFICIENT PERMISSION: key is "
                     "Acc(list_pred(key), 1/2); .append needs full permission. The "
                     "entire gold body + postcondition tie-up is kept verbatim "
                     "after the write, so the rejection is attributable to the "
                     "append, not a value mismatch.",
    },
    {
        "id": "frame-mutation-prefix",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL3, _F3_FRAME_PREFIX),
        "refinement": "Mutates `prefix` (the group label) in place at "
                      "Acc(list_pred(prefix), 1/2). The gold fix re.escapes prefix "
                      "into a NEW pattern string; it never writes the prefix back. "
                      "A label-mutating realisation has no faithful repo "
                      "counterpart and would not be the gold escape fix.",
        "rationale": "Must reject for INSUFFICIENT PERMISSION: prefix is read-only "
                     "at 1/2. Supporting frame-mutation case on the input the gold "
                     "fix actually escapes; rejection attributable to the write.",
    },
    {
        "id": "real-bug-dollar-anchor",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL3, _F3_REALBUG),
        "refinement": "This is the verbatim PRE-PATCH skeleton (== "
                      "model_prepatch.py): the label's trailing '$' (U+0024) is "
                      "honoured as a regex end-anchor instead of a literal — "
                      "exactly the pre-fix `re.compile(r'{}-\\d+-{}$'.format("
                      "prefix, ...))` behaviour. Its faithful real patch is the "
                      "UNFIXED code (no re.escape), which on the F2P input "
                      "prefix='form$', key='form$-0-uuid' drops the edited row "
                      "(queryset.count()==0 != 1) -> F2P "
                      "test_get_list_editable_queryset_with_regex_chars_in_prefix "
                      "fails. This is the headline weakness the spec must reject.",
        "rationale": "Rejected by the POSTCONDITION Result() == recognises(...): "
                     "with prefix ending in '$' and a literally-matching key, "
                     "recognises is True (literal label present) but this rival "
                     "forces ok_label=False, so Result() is False != recognises. "
                     "Rejection lands on the postcondition (the tie-up assert is "
                     "removed, as in the prepatch, so it is a value break not a "
                     "proof break).",
    },
    {
        "id": "partial-drop-label",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL3, _F3_DROP_LABEL),
        "refinement": "Drops the literal-label conjunct from the decision. "
                      "Faithful real patch: a pattern missing the leading group "
                      "label, e.g. r'-\\d+-{}$'.format(pkname) — it accepts keys "
                      "from a DIFFERENT inline formset prefix, miscounting edited "
                      "rows across formsets. Diverges from recognises on any key "
                      "with a wrong label but a right '-\\d+-pkname' tail (e.g. "
                      "prefix='form', key='xxxx-0-uuid').",
        "rationale": "Rejected by the POSTCONDITION Result() == recognises(...): "
                     "Result() omits the ok_label (prefix_eq) conjunct while "
                     "recognises requires the literal label, so they disagree "
                     "whenever the label fails to match but the rest holds. The "
                     "gold tie-up assert stays provable; the break is a value "
                     "mismatch.",
    },
    {
        "id": "partial-drop-digits",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL3, _F3_DROP_DIGITS),
        "refinement": "Treats the middle region as digits unconditionally "
                      "(ok_digits = True, run_is_digits skipped). Faithful real "
                      "patch: replacing the `\\d+` sub-pattern with `.+`/`[^-]+` — "
                      "it recognises keys with a non-numeric middle segment that "
                      "are not real `prefix-<int>-pkname` formset keys. Diverges "
                      "from recognises on e.g. prefix='form', key='form-0a-uuid' "
                      "(recognises=False, rival=True).",
        "rationale": "Rejected by the POSTCONDITION Result() == recognises(...): "
                     "Result() drops the all_digits conjunct, so on a key with a "
                     "non-digit in the middle region recognises is False but the "
                     "rival returns True.",
    },
    {
        "id": "partial-drop-hyphen2",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL3, _F3_DROP_HYPHEN2),
        "refinement": "Drops the second-hyphen separator requirement (hyphen2 = "
                      "True). Faithful real patch: a pattern using `\\d+.{}$` "
                      "(any single char before the field name) instead of the "
                      "literal '-'. Diverges from recognises on a key whose second "
                      "separator is not '-' (e.g. decomposing 'form-0xuuid' with "
                      "d=1: separator 'x'; recognises=False, rival=True).",
        "rationale": "Rejected by the POSTCONDITION Result() == recognises(...): "
                     "Result() omits the `key[np+1+d] == 45` conjunct while "
                     "recognises requires it; they disagree on any key with a "
                     "non-hyphen second separator.",
    },
    {
        "id": "pos-control-reshape",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _IMPL3, _F3_POS),
        "rationale": "A structurally-different but CORRECT impl: the five "
                     "conjuncts are folded into an explicit boolean accumulator "
                     "`acc` (reverse order) and returned from it; the value equals "
                     "the gold conjunction. KEEPS the gold tie-up Assert(recognises "
                     "== conjunction) verbatim so the postcondition still "
                     "discharges, and adds no loop/lemma (no proof-gap risk). Must "
                     "verify; a failure would be SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-control-echo-grounded",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _IMPL3, _F3_ECHO),
        "rationale": "`recognises` is a GROUNDED @Pure function of the args (fully "
                     "unfolded), so returning it directly is the cheapest CORRECT "
                     "impl, not a wrong echo. It satisfies Result() == "
                     "recognises(...) trivially and keeps all inputs read-only. "
                     "Must verify; documents that no ungrounded-oracle-echo rival "
                     "exists (any echo of a grounded oracle is correct).",
    },
    {
        "id": "admissibility-f2p",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _IMPL3, _F3_ADMISS),
        "rationale": "Self-call on the EXACT F2P input (prefix='form$', "
                     "pkname='uuid', key='form$-0-uuid' as fresh code-point lists) "
                     "verifies and asserts the decision equals recognises, "
                     "confirming the precondition (Acc 1/2 on each of the three "
                     "lists) admits a normal submitted POST key. A failure would be "
                     "PRECOND-TOO-STRONG.",
    },

    # ---------------- match_literal: verified-helper surface ----------------
    {
        "id": "helper-frame-mutation",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL1, _F1_FRAME),
        "refinement": "Appends to `lit`, a 1/4-permission read-only helper input. "
                      "match_literal/run_is_digits have NO behavioural repo "
                      "counterpart (proof scaffolding); a mutating helper has no "
                      "faithful real realisation. Supporting permission-discipline "
                      "case on the helper surface.",
        "rationale": "Must reject for INSUFFICIENT PERMISSION: lit is "
                     "Acc(list_pred(lit), 1/4); .append needs full permission. The "
                     "gold helper body + postcondition is kept verbatim after the "
                     "write, so the rejection is attributable to the append.",
    },
]


# ============================================================================
# AXIOM LANE — A-reference deep model `recognises` (no @ContractOnly axiom)
# ============================================================================
# meta.axioms == [] (no consumed axiom); deep_model_references carries
# `recognises` as an A-reference validated == the REAL post-fix compiled-pattern
# match by axiom_check.py (G-AX). We re-run the real CPython `re` callee in the
# instance image and re-assert the equivalence (soundness) and its caller-domain
# containment. Only stdlib `re` is needed in-container; the host axiom_check.py
# oracle source is embedded at manifest-load time (the runner mounts ONLY the
# probe at /work, so the bundle file is NOT in-container — pilot bug #6).

_AXIOM_CHECK_SRC = (Path(__file__).parent / "axiom_check.py").read_text(encoding="utf-8")


# --- axiom-soundness probe: deep model `recognises` == real re.escape-fixed
#     match over the scoped realistic-POST-key domain (the full G-AX battery). ---
_AX_SOUND_PROBE = (
    "# -*- coding: utf-8 -*-\n"
    "import sys\n"
    "# Embedded host axiom_check.py (the G-AX oracle): runs the REAL CPython `re`\n"
    "# callee on boundary + 60000 randomized-fuzz inputs and asserts\n"
    "# recognises == real re.escape-fixed match over the scoped domain, plus that\n"
    "# the change is real (30000+ discriminating inputs incl. the F2P case).\n"
    "_SRC = " + repr(_AXIOM_CHECK_SRC) + "\n"
    "g = {'__name__': '_axcheck'}\n"
    "exec(compile(_SRC, 'axiom_check.py', 'exec'), g)\n"
    "rc = g['main']()\n"
    "print('axiom-soundness: recognises == real re.escape-fixed match (G-AX), rc=%r' % rc)\n"
    "sys.exit(0 if rc == 0 else 1)\n"
)


# --- axiom-containment probe: every callee-input the MODEL can reach lies inside
#     the scoped domain the equivalence is asserted over. ---
# The model reaches `recognises(prefix, pkname, key)` for the SAME (prefix, pkname,
# key) triples the real callee `fixed_match` is applied to (the per-key decision is
# 1:1 with the regex match). The scoped domain (mapping.md / axiom_check.py) is:
#   (a) digit run is ASCII U+0030..U+0039 — the model's all_digits IS that ASCII
#       class, so the model never reaches a non-ASCII-digit acceptance;
#   (b) key does not end in a bare U+000A newline — recognises requires the key to
#       END exactly at pkname (no trailing-newline tolerance), so the model never
#       reaches the only inputs on which the real `$` anchor differs.
# Containment holds iff: on EVERY input where recognises(...) is True (an accepted
# key, the only inputs whose decision the model pins as a match), the key is in
# scope (no trailing newline) AND its digit run is ASCII. We enumerate accepted
# keys exhaustively over small lengths and assert each is in-scope; we also confirm
# that for any in-scope key the real fixed match agrees (so no reachable input lies
# outside the equivalence domain). Covering MORE than the caller reaches (e.g.
# unicode \d or trailing-\n keys, which only the real callee accepts) is SOUND, not
# a defect (the float-vs-int containment rule).
_AX_CONTAIN_PROBE = (
    "# -*- coding: utf-8 -*-\n"
    "import sys, itertools, re\n"
    "_SRC = " + repr(_AXIOM_CHECK_SRC) + "\n"
    "g = {'__name__': '_axcheck'}\n"
    "exec(compile(_SRC, 'axiom_check.py', 'exec'), g)\n"
    "recognises = g['recognises']\n"
    "fixed_match = g['fixed_match']\n"
    "in_scope = g['in_scope']\n"
    "\n"
    "# Enumerate every short candidate key over a small alphabet that INCLUDES the\n"
    "# boundary code points the model's recognition can depend on: ASCII digits,\n"
    "# the hyphen, label/field letters, a regex metachar '$', a non-ASCII unicode\n"
    "# decimal digit U+0660 (Arabic-Indic zero), and a trailing newline. The\n"
    "# label/field letters used by `prefixes`/`pknames` ('a','f','$') are all in\n"
    "# `alpha` so an accepted key (label-'-'-digits-'-'-name) is actually reachable\n"
    "# in the enumeration (reachable > 0 is asserted below).\n"
    "alpha = ['0', '1', '9', '-', 'a', 'f', '$', '\\u0660', '\\n']\n"
    "prefixes = ['', 'f', 'a$', 'fa']\n"
    "pknames = ['a', 'fa', 'aaf']\n"
    "reachable = 0\n"
    "checked = 0\n"
    "out_of_scope_reached = []\n"
    "for prefix in prefixes:\n"
    "    for pkname in pknames:\n"
    "        for L in range(0, 7):\n"
    "            for tup in itertools.product(alpha, repeat=L):\n"
    "                key = ''.join(tup)\n"
    "                checked += 1\n"
    "                # The model's recognition decision; True = a key the model\n"
    "                # pins as a MATCH (the inputs whose acceptance the model can\n"
    "                # actually reach as 'recognised').\n"
    "                m = recognises(prefix, pkname, key)\n"
    "                if not m:\n"
    "                    continue\n"
    "                reachable += 1\n"
    "                # Containment obligation 1: an accepted key is in scope\n"
    "                # (no trailing bare newline). recognises ends exactly at\n"
    "                # pkname so it can never accept a trailing-\\n key.\n"
    "                if not in_scope(key):\n"
    "                    out_of_scope_reached.append(('newline', prefix, pkname, key))\n"
    "                    continue\n"
    "                # Containment obligation 2: the digit run is ASCII 0-9, so\n"
    "                # the model never reaches a unicode-\\d acceptance. Check the\n"
    "                # decomposed digit region holds only ASCII digits.\n"
    "                np_, nk, n = len(prefix), len(pkname), len(key)\n"
    "                d = n - np_ - nk - 2\n"
    "                digit_region = key[np_ + 1:np_ + 1 + d]\n"
    "                if not all('0' <= c <= '9' for c in digit_region):\n"
    "                    out_of_scope_reached.append(('unicode-digit', prefix, pkname, key))\n"
    "                    continue\n"
    "                # In-scope: the real callee must AGREE (equivalence holds on\n"
    "                # every input the model reaches).\n"
    "                if fixed_match(prefix, pkname, key) is not True:\n"
    "                    out_of_scope_reached.append(('disagree', prefix, pkname, key))\n"
    "if out_of_scope_reached:\n"
    "    print('AXIOM-TOO-WEAK-FOR-CALLER: model reaches inputs outside the scoped '\n"
    "          'equivalence domain: %r' % out_of_scope_reached[:10])\n"
    "    sys.exit(1)\n"
    "if reachable == 0:\n"
    "    print('containment probe vacuous: no accepted key reached in the '\n"
    "          'enumeration (alphabet/prefix/pkname mismatch) — test bug, not a '\n"
    "          'spec verdict.')\n"
    "    sys.exit(1)\n"
    "print('axiom-containment OK: %d candidate keys, %d reachable matches, all '\n"
    "      'in-scope (ASCII digit run, no trailing newline) and agreeing with the '\n"
    "      'real re.escape-fixed match.' % (checked, reachable))\n"
    "sys.exit(0)\n"
)


AXIOM_TESTS = [
    {
        "id": "ax-sound-recognises",
        "axiom": "recognises",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _AX_SOUND_PROBE,
        "rationale": "The A-reference deep model `recognises` must equal the REAL "
                     "post-fix compiled-pattern match re.compile(r'{}-\\d+-{}$'."
                     "format(re.escape(prefix), pkname)).match(key) over the scoped "
                     "realistic-POST-key domain. The probe re-runs the G-AX "
                     "oracle (real CPython `re`) on the boundary + 60000-fuzz "
                     "battery and asserts 0 mismatch + a real discrimination. If "
                     "the real callee disagrees, AXIOM-UNSOUND.",
    },
    {
        "id": "ax-contain-recognises",
        "axiom": "recognises",
        "kind": "axiom-containment",
        "expect": "covered",
        "apply_gold": True,
        "probe": _AX_CONTAIN_PROBE,
        "rationale": "Every callee-input the MODEL can reach as a recognised key "
                     "must lie inside the scoped equivalence domain (ASCII digit "
                     "run; no trailing bare newline). The probe enumerates short "
                     "candidate keys over an alphabet that includes a unicode digit "
                     "(U+0660) and a trailing newline, and asserts every key the "
                     "model ACCEPTS is in-scope and agrees with the real fixed "
                     "match. A reachable accepted key outside the scoped domain "
                     "would be AXIOM-TOO-WEAK-FOR-CALLER; covering MORE than the "
                     "caller reaches (unicode-\\d / trailing-\\n keys only the real "
                     "callee accepts) is sound, not a defect.",
    },
]
