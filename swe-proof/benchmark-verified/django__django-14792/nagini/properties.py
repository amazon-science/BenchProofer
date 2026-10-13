"""PBT falsification battery for django__django-14792.

NOT a Nagini module: a manifest the runner (swebench_nagini.pbt) parses. Each
SPEC_TEST is a full model.py variant that shares the FROZEN spec byte-for-byte
(only the impl region between # impl-start / # impl-end is edited, guaranteed by
region-surgery via _swap) and is checked by Nagini verify + markers.same_spec.
Each AXIOM_TEST is a self-contained probe run in the instance Docker image
against the real callees.

Defended surface (read off model.py):

  resolve_timezone_name(tz: TimeZone) -> PSeq[int]
    Requires  Acc(tz.short_label, 1/2)   # READ-ONLY input field
    Requires  Acc(tz.full_name,   1/2)   # READ-ONLY input field
    Requires  MustTerminate(1)           # TOTAL correctness: no diverging impl
    Ensures   Acc(tz.short_label, 1/2)   # returned at half perm => still read-only
    Ensures   Acc(tz.full_name,   1/2)
    Ensures   Implies(present_and_nonempty(tz.short_label), Result()==tz.short_label)
    Ensures   Implies(not present_and_nonempty(tz.short_label), Result()==tz.full_name)

  present_and_nonempty(label) := label is not None and len(label) > 0   (@Pure)

The two postcondition clauses pin Result() to be EXACTLY one of the two carried
fields, selected by the present-and-non-empty predicate. The predicate is FULLY
GROUNDED in the input (a function of `label` itself, fully unfolded) — there is
no opaque answer-key oracle to echo, so the ungrounded-oracle-echo class does not
apply (see assessment). Both fields are read-only (half permission Required AND
Ensured) — so the FRAME-MUTATION probe is mandatory.
"""
from pathlib import Path

INSTANCE = "django__django-14792"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()
_AXIOM_CHECK_SRC = (Path(__file__).parent / "axiom_check.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# The exact gold impl region (between # impl-start / # impl-end). Every variant
# is produced by editing ONLY this text, so spec_view (=> same_spec) is preserved.
_GOLD_IMPL = (
    "    label = tz.short_label  # type: Optional[PSeq[int]]   # timezone.tzname(None)\n"
    "    if label is not None and len(label) > 0:\n"
    "        return label\n"
    "    return tz.full_name                                   # str(timezone)\n"
)

# sanity: the gold impl text must appear verbatim in the frozen model
assert _GOLD_IMPL in _BASE, "gold impl region drifted from model.py"


# ---------------------------------------------------------------------------
# POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls.
# ---------------------------------------------------------------------------

# (1) Branch-reorder: handle the absent/empty case first, then the present case.
#     Same value mapping, inverted control flow. No loop/lemma involved, so no
#     proof-trigger risk (avoids pilot bug #2/#3).
_POS_REORDER = (
    "    label = tz.short_label  # type: Optional[PSeq[int]]\n"
    "    if label is None or len(label) == 0:\n"
    "        return tz.full_name\n"
    "    return label\n"
)

# (2) Use the @Pure predicate directly as the guard, with an explicit else.
#     This is the honest 'cheapest correct impl' positive control: echoing the
#     predicate IS doing the work (the oracle is grounded in the input).
_POS_PREDICATE = (
    "    if present_and_nonempty(tz.short_label):\n"
    "        return tz.short_label\n"
    "    else:\n"
    "        return tz.full_name\n"
)

# (3) Local-variable reshape: bind both fields to typed locals first, then
#     select. Different data shape, identical result; keeps every obligation.
_POS_LOCALS = (
    "    s = tz.short_label  # type: Optional[PSeq[int]]\n"
    "    f = tz.full_name    # type: PSeq[int]\n"
    "    if present_and_nonempty(s):\n"
    "        return s\n"
    "    return f\n"
)


# ---------------------------------------------------------------------------
# ADMISSIBILITY — the precondition must admit a normal F2P-shaped input.
# A self-call re-establishes the Requires (Acc(.,1/2) on both fields) from
# exactly the permission the caller holds, then the result is returned. If the
# precondition were too strong (e.g. it forbade a None / empty short_label) the
# self-call would fail to verify => PRECOND-TOO-STRONG.
# ---------------------------------------------------------------------------
_ADMISS = (
    "    # admissibility: the half-permission we hold is exactly what the\n"
    "    # precondition demands, so we may re-invoke on the same in-domain tz.\n"
    "    Assert(present_and_nonempty(tz.short_label) or not present_and_nonempty(tz.short_label))\n"
    "    label = tz.short_label  # type: Optional[PSeq[int]]\n"
    "    if label is not None and len(label) > 0:\n"
    "        return label\n"
    "    return tz.full_name\n"
)


# ---------------------------------------------------------------------------
# FRAME-MUTATION (MANDATORY: read-only inputs) — overwrite a half-permission
# field to satisfy the postcondition vacuously. Must REJECT for insufficient
# permission (write needs full Acc; only 1/2 is held). Gold selection kept
# verbatim so the rejection is attributable to the WRITE, not to a wrong value.
# ---------------------------------------------------------------------------

# (a) overwrite tz.short_label so that present_and_nonempty becomes true and
#     short_label == full_name, then return it: would make BOTH clauses hold
#     trivially if the write were permitted. It is NOT (only 1/2 perm).
_FRAME_SHORT = (
    "    tz.short_label = tz.full_name   # ILLEGAL write: only Acc(.,1/2) held\n"
    "    return tz.short_label\n"
)

# (b) overwrite tz.full_name to equal the short label, then return full_name.
#     Same vacuity attempt on the other read-only field.
_FRAME_FULL = (
    "    label = tz.short_label  # type: Optional[PSeq[int]]\n"
    "    if label is not None and len(label) > 0:\n"
    "        tz.full_name = label        # ILLEGAL write: only Acc(.,1/2) held\n"
    "    return tz.full_name\n"
)


# ---------------------------------------------------------------------------
# UNIQUENESS / PARTIAL-DOMAIN — same-spec WRONG impls that must REJECT.
# ---------------------------------------------------------------------------

# (i) always return full_name (the pre-patch bug). Fails the discriminating
#     clause Implies(present_and_nonempty(short), Result()==short) whenever the
#     short label is present, non-empty and differs from the full rendering.
_WRONG_ALWAYS_FULL = (
    "    return tz.full_name\n"
)

# (ii) always return short_label. Fails the fallback clause
#      Implies(not present_and_nonempty(short), Result()==full) whenever the
#      short label is absent (None) or empty.
_WRONG_ALWAYS_SHORT = (
    "    label = tz.short_label  # type: Optional[PSeq[int]]\n"
    "    return label\n"
)

# (iii) INVERTED selection: full when the short label is present, short when
#       absent/empty. Wrong on the entire domain that the spec discriminates.
_WRONG_SWAP = (
    "    label = tz.short_label  # type: Optional[PSeq[int]]\n"
    "    if label is not None and len(label) > 0:\n"
    "        return tz.full_name\n"
    "    return label\n"
)

# (iv) drop the emptiness guard: present (not-None) wins even when EMPTY.
#      Fails the fallback clause when short_label is the empty sequence ('' tz):
#      present_and_nonempty is False so Result must be full_name, but this
#      returns the empty short label.
_WRONG_DROP_EMPTY = (
    "    label = tz.short_label  # type: Optional[PSeq[int]]\n"
    "    if label is not None:\n"
    "        return label\n"
    "    return tz.full_name\n"
)

# (v) NON-TERMINATION: an infinite loop satisfies every value postcondition
#     vacuously under partial correctness. The MustTerminate(1) obligation in
#     the precondition makes the loop leak an unsatisfied obligation, so the
#     verifier must REJECT (obligation leak check). This is the P1 class the
#     audit found before the obligation was added.
_WRONG_NONTERM = (
    "    while True:\n"
    "        pass\n"
)


SPEC_TESTS = [
    # ---- positive controls (soundness) ------------------------------------
    {
        "id": "pos-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _GOLD_IMPL, _POS_REORDER),
        "rationale": "branch-reordered correct impl (absent/empty handled first); "
                     "same value mapping, no loop/lemma => must verify, else SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-predicate",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _GOLD_IMPL, _POS_PREDICATE),
        "rationale": "cheapest honest impl using the grounded @Pure predicate "
                     "directly as the guard with an explicit else; the oracle is "
                     "grounded in the input so this echo IS the work => must verify.",
    },
    {
        "id": "pos-locals",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _GOLD_IMPL, _POS_LOCALS),
        "rationale": "local-variable reshape (bind both fields, then select); "
                     "different data shape, identical result => must verify.",
    },
    # ---- admissibility ----------------------------------------------------
    {
        "id": "admiss-bothbranches",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _GOLD_IMPL, _ADMISS),
        "rationale": "the precondition (half perm on both fields, short_label "
                     "Optional incl. None/empty) must admit a normal F2P-shaped "
                     "input on BOTH the present and the absent branch; the "
                     "tautology assert proves the predicate is well-defined on the "
                     "input under the held permission. Else PRECOND-TOO-STRONG.",
    },
    # ---- frame mutation (MANDATORY: read-only inputs) ---------------------
    {
        "id": "frame-mut-short",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _FRAME_SHORT),
        "refinement": "A real patch that REASSIGNS the tzinfo object's short label "
                      "to its full rendering and returns that would mutate the "
                      "caller's tzinfo, changing tzname(None) globally; the F2P "
                      "expects pytz Etc/GMT-10 -> '+10' (short) but Europe/Madrid -> "
                      "'Europe/Madrid' (full). Overwriting short_label with full_name "
                      "yields 'Etc/GMT-10' for the fixed-offset zone — the exact "
                      "regression the bug report rejects — so it would NOT resolve.",
        "rationale": "REJECT for insufficient permission: writing tz.short_label "
                     "needs full Acc but only Acc(.,1/2) is held (Requires). The "
                     "permission system, not a value clause, kills this. #1 class.",
    },
    {
        "id": "frame-mut-full",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _FRAME_FULL),
        "refinement": "Reassigning tz.full_name to the short label and returning it "
                      "mutates the caller's tzinfo rendering; str(timezone) is an "
                      "unchanged observation in the gold patch (the right operand of "
                      "the new `or`). A faithful patch never writes the object, so "
                      "this is not the gold behaviour and would not resolve.",
        "rationale": "REJECT for insufficient permission: writing tz.full_name needs "
                     "full Acc but only Acc(.,1/2) is held. Permission system.",
    },
    # ---- partial-domain uniqueness ----------------------------------------
    {
        "id": "wrong-always-full",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _WRONG_ALWAYS_FULL),
        "refinement": "This is the PRE-PATCH body `return str(timezone)` exactly "
                      "(model_prepatch.py). The F2P test asserts "
                      "_get_timezone_name(pytz.timezone('Etc/GMT-10')) == '+10', but "
                      "str(timezone) is 'Etc/GMT-10' — the regression the issue "
                      "reports. It does NOT resolve.",
        "rationale": "REJECT by Implies(present_and_nonempty(short), Result()==short): "
                     "when the short label is present, non-empty and differs from the "
                     "full rendering, returning full_name violates the discriminating "
                     "postcondition clause.",
    },
    {
        "id": "wrong-always-short",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _WRONG_ALWAYS_SHORT),
        "refinement": "Returning tzname(None) unconditionally yields None for a "
                      "zoneinfo named zone (zoneinfo.ZoneInfo('Europe/Madrid') has "
                      "tzname(None) is None) — the F2P asserts that case must be "
                      "'Europe/Madrid' (the full name). Returning None (or '') is "
                      "wrong and would not resolve.",
        "rationale": "REJECT by Implies(not present_and_nonempty(short), "
                     "Result()==full): when the short label is absent/empty the "
                     "result must be the full rendering, not the short label.",
    },
    {
        "id": "wrong-swap",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _WRONG_SWAP),
        "refinement": "Inverted selection (full when present, short when absent) "
                      "returns 'Etc/GMT-10' for the fixed-offset zone (F2P wants "
                      "'+10') and None for the named zoneinfo zone (F2P wants the "
                      "full name). Wrong on both discriminating cases; not resolved.",
        "rationale": "REJECT by BOTH postcondition clauses simultaneously: the "
                     "present branch must return short (it returns full) and the "
                     "absent branch must return full (it returns short).",
    },
    {
        "id": "wrong-drop-empty",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _WRONG_DROP_EMPTY),
        "refinement": "Dropping the len>0 guard returns an EMPTY short label '' when "
                      "tzname(None)=='' (a real possibility for some tzinfo subclasses) "
                      "instead of falling back to str(timezone). Django's `or` treats "
                      "'' as falsy and falls back; this impl does not, so on an "
                      "empty-abbreviation zone it returns '' where gold returns the "
                      "full name — a behavioural divergence that does not resolve.",
        "rationale": "REJECT by Implies(not present_and_nonempty(short), "
                     "Result()==full): present_and_nonempty('') is False (len==0) so "
                     "the result must be full_name; returning the empty short label "
                     "violates the fallback clause.",
    },
    {
        "id": "wrong-nonterm",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _WRONG_NONTERM),
        "refinement": "A real patch whose _get_timezone_name loops forever hangs "
                      "every caller — get_current_timezone_name(), the template "
                      "context processor, and the F2P test itself — so it does NOT "
                      "resolve (the test run would time out, not pass).",
        "rationale": "REJECT by the MustTerminate(1) obligation: the infinite loop "
                     "cannot discharge the termination obligation (obligation leak "
                     "check), so the vacuous-under-partial-correctness attack from "
                     "the audit (P1) no longer verifies.",
    },
]


# ---------------------------------------------------------------------------
# AXIOM lane. There is NO @ContractOnly consumed axiom (meta.axioms == []).
# The single trust point is the A-reference deep selection model
# (resolve_timezone_name + present_and_nonempty) == the real gold expression
# `timezone.tzname(None) or str(timezone)`. axiom_check.py (G-AX) is the bundle
# oracle; we re-run its exact logic in the instance image against the REAL
# callees over the F2P zone families + boundary dial sweep + 5000 fuzz cases.
# This is an axiom-soundness check on the A-reference (PLAN §2.4 / §4 widened):
# any disagreement between the deep model and the real callee is AXIOM-UNSOUND.
# ---------------------------------------------------------------------------

# Embed axiom_check.py's source (host-read at load time; the runner mounts ONLY
# the probe at /work, so the oracle cannot be read in-container — pilot bug #6).
# Open with utf-8 already done at load; the probe re-executes the embedded source.
_AX_PROBE = (
    "# A-reference soundness probe for django__django-14792.\n"
    "# Re-runs the bundle's G-AX oracle (axiom_check.py) against the REAL\n"
    "# datetime.timezone / pytz / zoneinfo callees inside the instance image,\n"
    "# asserting the deep selection model equals `tzname(None) or str(tz)` over\n"
    "# every F2P family + boundary + 5000 fuzz cases. Exit 0 iff sound.\n"
    "import sys\n"
    "_SRC = " + repr(_AXIOM_CHECK_SRC) + "\n"
    "g = {'__name__': '__embedded_axiom_check__'}\n"
    "exec(compile(_SRC, 'axiom_check_embedded.py', 'exec'), g)\n"
    "try:\n"
    "    rc = g['main']()\n"
    "except AssertionError as e:\n"
    "    print('AXIOM-UNSOUND: deep selection disagrees with real callee:', e)\n"
    "    sys.exit(1)\n"
    "except ImportError as e:\n"
    "    # pytz/zoneinfo are dependencies of the F2P test; absence is a probe\n"
    "    # environment problem, not a soundness result.\n"
    "    print('PROBE-ENV: required tz module missing:', e)\n"
    "    sys.exit(1)\n"
    "print('A-reference deep selection SOUND vs real tzname(None) or str(tz).')\n"
    "sys.exit(0 if rc == 0 else 1)\n"
)

AXIOM_TESTS = [
    {
        "id": "aref-selection-sound",
        "axiom": "resolve_timezone_name-selection (A-reference deep model)",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _AX_PROBE,
        "rationale": "The deep selection model (present_and_nonempty(short) ? short "
                     ": full) is the bundle's only trust point; if the REAL "
                     "`tzname(None) or str(tz)` ever disagrees with it on a "
                     "caller-reachable tzinfo object, the A-reference is AXIOM-UNSOUND. "
                     "Probe executes the real callees (never scrapes source).",
    },
]
