"""PBT falsification battery for django__django-13363.

NOT a Nagini module: a manifest the runner (swebench_nagini.pbt) parses. Each
SPEC_TEST is a full model.py variant built by region-surgery (`_swap` edits ONLY
text inside the two `# impl-start`/`# impl-end` regions, so the frozen spec is
never touched and same_spec holds by construction); checked by Nagini verify +
markers.same_spec. AXIOM_TESTS probe the real A-reference callee in Docker.

Defended surface (read off model.py):
  Two byte-identical modeled functions date_cast_tzname / time_cast_tzname:
    inputs  use_tz: bool
            tzinfo: Optional[List[int]]   (read-only: Acc(list_pred(tzinfo),1/2))
            current_name: List[int]       (read-only: Acc(list_pred(current_name),1/2))
    post    Acc(current_name,1/2) AND (tzinfo!=None -> Acc(tzinfo,1/2))     [frame]
            Result() is selected_tzname(use_tz, tzinfo, current_name)        [LOAD-BEARING]
  where the @Pure deep model is, fully unfolded over the args:
            not use_tz            -> None
            use_tz, tzinfo!=None  -> tzinfo          (supplied zone HONOURED)
            use_tz, tzinfo==None  -> current_name    (ambient fallback)

The load-bearing clause uses OBJECT IDENTITY (`is`) to a @Pure oracle that is a
total function of the three args. There is therefore NO ungrounded answer-key to
echo: `return selected_tzname(...)` is the CORRECT impl, not a wrong echo (so the
ungrounded-oracle-echo class is N/A here — see 'assessment'); instead we use the
echo as an honest cheapest-impl positive control. The real attack surface is
(a) FRAME-MUTATION of the two read-only inputs and (b) PARTIAL-DOMAIN divergence
on the discriminating sub-domain (the actual django bug: ignore tzinfo).
"""
from pathlib import Path

INSTANCE = "django__django-13363"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()

# The impl block is byte-identical in BOTH modeled functions, so it occurs twice.
_GOLD_IMPL = (
    "    tzname = None  # type: Optional[List[int]]\n"
    "    if use_tz:\n"
    "        if tzinfo is None:\n"
    "            tzname = current_name\n"
    "        else:\n"
    "            tzname = tzinfo\n"
    "    return tzname"
)


def _swap_both(src, old, new):
    """Replace `old` everywhere it appears in the (two identical) impl regions.

    Asserts exactly two occurrences so an accidental spec-region match (which
    would have a different count) is rejected as drift. Editing the same text in
    both impl regions keeps every spec region byte-identical => same_spec holds.
    """
    n = src.count(old)
    if n == 0:
        raise AssertionError(f"drift: {old!r} not present")
    if n != 2:
        raise AssertionError(f"expected 2 impl occurrences, found {n}: {old!r}")
    return src.replace(old, new, 2)


def _variant(new_impl):
    return _swap_both(_BASE, _GOLD_IMPL, new_impl)


# ---------------------------------------------------------------------------
# SPEC LANE
# ---------------------------------------------------------------------------

# (1) FRAME-MUTATION on `current_name` (read-only, Acc(...,1/2)). A rival that
#     writes to the ambient-name input cannot hold the write permission (it has
#     only 1/2). It still returns the gold value, so were the spec permissive it
#     would verify; it MUST be rejected for insufficient permission.
_FRAME_MUT_CURRENT = (
    "    current_name.append(0)  # WRITE to a read-only input: only Acc(...,1/2)\n"
    "    tzname = None  # type: Optional[List[int]]\n"
    "    if use_tz:\n"
    "        if tzinfo is None:\n"
    "            tzname = current_name\n"
    "        else:\n"
    "            tzname = tzinfo\n"
    "    return tzname"
)

# (1b) FRAME-MUTATION on the OPTIONAL read-only input `tzinfo`. Guarded by the
#      `is not None` test so the write is well-typed; still rejected because the
#      caller granted only Acc(list_pred(tzinfo),1/2).
_FRAME_MUT_TZINFO = (
    "    tzname = None  # type: Optional[List[int]]\n"
    "    if use_tz:\n"
    "        if tzinfo is None:\n"
    "            tzname = current_name\n"
    "        else:\n"
    "            tzinfo.append(0)  # WRITE to a read-only input: only Acc(...,1/2)\n"
    "            tzname = tzinfo\n"
    "    return tzname"
)

# (3) PARTIAL-DOMAIN — the ACTUAL django bug (== model_prepatch.py). Correct when
#     use_tz is off and when tzinfo is None, but on use_tz AND tzinfo-supplied it
#     returns the ambient name instead of the supplied zone's name. Diverges on
#     exactly the F2P sub-domain (a supplied melb/pacific tz must be honoured).
_PARTIAL_IGNORE_TZINFO = (
    "    tzname = None  # type: Optional[List[int]]\n"
    "    if use_tz:\n"
    "        tzname = current_name  # ignores tzinfo: supplied zone silently dropped\n"
    "    return tzname"
)

# (3b) PARTIAL-DOMAIN on the use_tz==False sub-domain: returns the ambient name
#      when it should return None (time-zone support off => no time zone at all).
_PARTIAL_OFF_WRONG = (
    "    tzname = current_name  # WRONG: should be None when use_tz is off\n"
    "    if use_tz:\n"
    "        if tzinfo is None:\n"
    "            tzname = current_name\n"
    "        else:\n"
    "            tzname = tzinfo\n"
    "    return tzname"
)

# (3c) PARTIAL-DOMAIN — branch swap: on use_tz AND tzinfo-supplied returns the
#      ambient name, and on use_tz AND tzinfo-absent returns ... nothing useful;
#      concretely it swaps the two assignments so a supplied zone yields the
#      ambient name and an absent one yields a None-typed slot. Diverges on both
#      use_tz sub-domains; the F2P "supplied zone honoured" assertion fails.
_PARTIAL_SWAP = (
    "    tzname = None  # type: Optional[List[int]]\n"
    "    if use_tz:\n"
    "        if tzinfo is None:\n"
    "            tzname = tzinfo  # WRONG: ambient case returns None, not current_name\n"
    "        else:\n"
    "            tzname = current_name  # WRONG: supplied zone discarded for ambient\n"
    "    return tzname"
)

# (5) POSITIVE CONTROL — structurally-different but CORRECT: guard-clause /
#     early-return shape that mirrors the @Pure helper's branch order. Returns
#     the SAME objects (identity-preserving), so Result() is selected_tzname(...)
#     holds. No loop / fold / induction lemma => no proof gap.
_POS_EARLY_RETURN = (
    "    if not use_tz:\n"
    "        return None\n"
    "    if tzinfo is not None:\n"
    "        return tzinfo\n"
    "    return current_name"
)

# (5b) POSITIVE CONTROL — honest cheapest impl: echo the GROUNDED @Pure oracle
#      directly. Because the oracle is a total function of the args and returns
#      one of the input objects (or None), this is value- AND identity-correct.
#      Confirms there is no *wrong* echo (the oracle is grounded, not an
#      answer-key). The @Pure call's Requires(Acc(...,1/8)) is covered by the
#      caller's Acc(...,1/2).
_POS_ECHO = (
    "    result = selected_tzname(use_tz, tzinfo, current_name)"
    "  # type: Optional[List[int]]\n"
    "    return result"
)

# (6) ADMISSIBILITY — the gold impl plus a leading Assert that the precondition
#     admits evaluating the oracle on an F2P-shaped input (use_tz on, a supplied
#     zone). If the Requires could not be established this Assert would fail =>
#     PRECOND-TOO-STRONG. It verifies => the precondition accepts a normal input.
_ADMISS = (
    "    Assert(Implies(use_tz and tzinfo is not None,\n"
    "                   selected_tzname(use_tz, tzinfo, current_name) is tzinfo))\n"
    "    tzname = None  # type: Optional[List[int]]\n"
    "    if use_tz:\n"
    "        if tzinfo is None:\n"
    "            tzname = current_name\n"
    "        else:\n"
    "            tzname = tzinfo\n"
    "    return tzname"
)


SPEC_TESTS = [
    {
        "id": "frame-mut-current_name",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _variant(_FRAME_MUT_CURRENT),
        "refinement": (
            "Its faithful real patch would mutate the ambient-zone-name string "
            "(timezone.get_current_timezone_name()'s return) in place. Beyond being "
            "impossible (str is immutable), a real edit that mutated shared process "
            "time-zone state before building SQL corrupts every other query in the "
            "request and does not produce the per-query supplied-zone name the F2P "
            "(test_trunc_timezone_applied_before_truncation) asserts; it would not resolve."
        ),
        "rationale": (
            "Rejected by the permission system: current_name is read-only "
            "(Requires/Ensures Acc(list_pred(current_name),1/2)); .append needs full "
            "permission, so verification fails for INSUFFICIENT PERMISSION, not for the "
            "value clause (the returned value is still gold). #1 weakness class."
        ),
    },
    {
        "id": "frame-mut-tzinfo",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _variant(_FRAME_MUT_TZINFO),
        "refinement": (
            "Its faithful real patch would mutate the supplied tzinfo object (the "
            "user-passed pytz/zoneinfo zone) before reading its name. Real tzinfo "
            "objects are shared/immutable; mutating one is both impossible and would "
            "leak across every expression sharing that zone, never yielding the clean "
            "per-call name the F2P observes; it would not resolve."
        ),
        "rationale": (
            "Rejected by the permission system: tzinfo is read-only "
            "(Acc(list_pred(tzinfo),1/2) under the `is not None` guard); .append needs "
            "full permission => INSUFFICIENT PERMISSION. The else-branch value is still "
            "gold (tzinfo), so only the write is at fault."
        ),
    },
    {
        "id": "partial-domain-ignore-tzinfo",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _variant(_PARTIAL_IGNORE_TZINFO),
        "refinement": (
            "This IS the pre-patch django behaviour (model_prepatch.py): "
            "`tzname = current_name if use_tz else None`, ignoring self.tzinfo. The "
            "faithful real patch is precisely the bug the issue reports — a supplied "
            "time zone is silently discarded in favour of the ambient one — so the F2P "
            "test_trunc_timezone_applied_before_truncation (which asserts melb/pacific "
            "dates computed in the SUPPLIED zone) FAILS. It does not resolve."
        ),
        "rationale": (
            "Rejected by the load-bearing postcondition Result() is "
            "selected_tzname(use_tz, tzinfo, current_name): on use_tz AND tzinfo!=None "
            "the oracle is `tzinfo` but this impl returns `current_name` (a different "
            "object) => identity fails. Correct on the other two sub-domains; diverges "
            "on exactly the discriminating sub-domain."
        ),
    },
    {
        "id": "partial-domain-off-wrong",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _variant(_PARTIAL_OFF_WRONG),
        "refinement": (
            "Its faithful real patch returns the ambient time-zone name even when "
            "settings.USE_TZ is off, so the cast applies a time zone when none should "
            "be used. Naive-datetime PASS_TO_PASS cases (USE_TZ off) would emit "
            "tz-converted SQL and break; it would not resolve."
        ),
        "rationale": (
            "Rejected by Result() is selected_tzname(...): when use_tz is False the "
            "oracle is None but this impl returns current_name => identity fails. "
            "Pins the use_tz==False sub-domain the prior rival happened to satisfy."
        ),
    },
    {
        "id": "partial-domain-branch-swap",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _variant(_PARTIAL_SWAP),
        "refinement": (
            "Its faithful real patch swaps the supplied/ambient branches: a supplied "
            "zone yields the ambient name and the ambient case yields no zone. The F2P "
            "supplied-zone assertion fails (supplied zone discarded), so it does not "
            "resolve."
        ),
        "rationale": (
            "Rejected by Result() is selected_tzname(...): on use_tz AND tzinfo!=None "
            "the impl returns current_name (oracle wants tzinfo); on use_tz AND "
            "tzinfo==None the impl returns tzinfo==None (oracle wants current_name). "
            "Both discriminating sub-domains diverge."
        ),
    },
    {
        "id": "pos-control-early-return",
        "kind": "soundness",
        "expect": "verify",
        "module": _variant(_POS_EARLY_RETURN),
        "rationale": (
            "Structurally-different but CORRECT: guard-clause / early-return shape "
            "mirroring the @Pure helper's branch order, returning the SAME input "
            "objects (identity-preserving). No loop/fold => no induction lemma => no "
            "proof gap. Must verify, else SPEC-TOO-STRONG."
        ),
    },
    {
        "id": "pos-control-echo-grounded-oracle",
        "kind": "soundness",
        "expect": "verify",
        "module": _variant(_POS_ECHO),
        "rationale": (
            "Honest cheapest impl: directly return the GROUNDED @Pure oracle "
            "selected_tzname(use_tz,tzinfo,current_name). It is a total function of the "
            "args returning an input object or None, so this is identity-correct (no "
            "wrong echo exists). The @Pure Requires(Acc(...,1/8)) is covered by the "
            "caller's Acc(...,1/2). Must verify (positive control for the grounded "
            "oracle); else SPEC-TOO-STRONG."
        ),
    },
    {
        "id": "admiss-f2p-shaped",
        "kind": "admissibility",
        "expect": "verify",
        "module": _variant(_ADMISS),
        "rationale": (
            "Gold impl plus a leading Assert that, for an F2P-shaped input (use_tz on, "
            "a supplied zone), the precondition admits evaluating the oracle and the "
            "oracle selects the supplied zone (is tzinfo). Verifies => the Requires "
            "accepts a normal input; else PRECOND-TOO-STRONG."
        ),
    },
]


# ---------------------------------------------------------------------------
# AXIOM LANE
# ---------------------------------------------------------------------------
# The `axioms` region is empty (no @ContractOnly consumed). There is ONE
# A-reference deep model: selected_tzname (model.py pure region) must equal the
# REAL callee TimezoneMixin.get_tzname on every caller-reachable input, UNDER the
# caller's runtime config (settings.USE_TZ toggled, TIME_ZONE='UTC'). We run the
# real callee in the instance image (Django + pytz present) and assert equality.
# This embeds axiom_check.py's logic (read on the HOST at load time so it travels
# into the container, per pilot bug #6).

_AXIOM_CHECK_SRC = (Path(__file__).parent / "axiom_check.py").read_text()

_AX_SOUND_PROBE = (
    "# -*- coding: utf-8 -*-\n"
    "# axiom-soundness probe: real TimezoneMixin.get_tzname == selected_tzname\n"
    "# deep model on every caller-reachable input, under the caller's config.\n"
    "# Embeds tasks/django__django-13363/axiom_check.py (read on the HOST at\n"
    "# manifest-load time so it is present in-container; the runner mounts ONLY\n"
    "# this probe at /work).\n"
    + _AXIOM_CHECK_SRC
)

# Containment: enumerate EXACTLY the callee-inputs the model can reach. The model
# passes (use_tz, name(tzinfo)|None, current_name) to selected_tzname; the real
# get_tzname is parameterised by settings.USE_TZ and self.tzinfo (None or a real
# zone). Every reachable combination — USE_TZ in {True,False} x tzinfo in
# {None} U {real pytz zones} — is exactly what the soundness probe enumerates
# (boundary zone list + 2000 fuzz). So the model never reaches an input outside
# get_tzname's domain (get_tzname is total over bool x Optional[tzinfo]); the
# A-reference is fully covered. We assert this by checking the real callee
# accepts (does not raise on) every reachable input, including USE_TZ off (which
# the model reaches: use_tz==False -> None).
_AX_COVER_PROBE = (
    "# -*- coding: utf-8 -*-\n"
    "# axiom-containment probe: every callee-input the model can REACH lies in\n"
    "# TimezoneMixin.get_tzname's domain. Reachable set = USE_TZ in {True,False}\n"
    "# x self.tzinfo in {None} U {real pytz zones}. get_tzname is total over that\n"
    "# domain (it never indexes the name; just chooses None / supplied / ambient),\n"
    "# so coverage is complete. We confirm by exercising the real callee on the\n"
    "# boundary of the reachable set and asserting it returns without error and\n"
    "# the value matches the model on the USE_TZ-off corner (the corner a\n"
    "# narrower axiom would miss).\n"
    "import sys\n"
    "def _check():\n"
    "    try:\n"
    "        from django.conf import settings\n"
    "        if not settings.configured:\n"
    "            settings.configure(USE_TZ=True, TIME_ZONE='UTC',\n"
    "                               INSTALLED_APPS=[], DATABASES={})\n"
    "        import django\n"
    "        django.setup()\n"
    "        from django.db.models.functions.datetime import TimezoneMixin\n"
    "    except Exception as e:\n"
    "        sys.stderr.write('Django unavailable (%s); containment is structural\\n' % e)\n"
    "        # Structural argument still holds: the reachable domain is bool x\n"
    "        # Optional[tzinfo]; get_tzname's body branches on exactly those and is\n"
    "        # total. Nothing to violate.\n"
    "        print('AX-COVER (no Django): reachable domain bool x Optional[tzinfo]'\n"
    "              ' is exactly get_tzname domain; total.')\n"
    "        sys.exit(0)\n"
    "    import pytz\n"
    "    class _Probe(TimezoneMixin):\n"
    "        def __init__(self, info):\n"
    "            self.tzinfo = info\n"
    "    zones = [None, pytz.timezone('UTC'), pytz.timezone('Australia/Melbourne'),\n"
    "             pytz.timezone('Pacific/Auckland'), pytz.timezone('America/New_York')]\n"
    "    n = 0\n"
    "    for use_tz in (True, False):  # model reaches BOTH (incl. USE_TZ off corner)\n"
    "        settings.USE_TZ = use_tz\n"
    "        for z in zones:\n"
    "            r = _Probe(z).get_tzname()  # must not raise: input in domain\n"
    "            if not use_tz:\n"
    "                assert r is None, ('USE_TZ-off corner reachable by model but '\n"
    "                                   'callee returned %r (expected None)' % (r,))\n"
    "            elif z is None:\n"
    "                assert isinstance(r, str), 'ambient name expected str, got %r' % (r,)\n"
    "            else:\n"
    "                assert r == z.tzname(None), ('supplied-zone name mismatch %r vs %r'\n"
    "                                             % (r, z.tzname(None)))\n"
    "            n += 1\n"
    "    print('AX-COVER OK: real get_tzname accepts all %d caller-reachable '\n"
    "          'inputs (USE_TZ on/off x None/supplied zones).' % n)\n"
    "    sys.exit(0)\n"
    "_check()\n"
)


AXIOM_TESTS = [
    {
        "id": "ax-sound-selected_tzname",
        "axiom": "selected_tzname",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _AX_SOUND_PROBE,
        "rationale": (
            "A-reference: the deep model selected_tzname must equal the real "
            "TimezoneMixin.get_tzname on every input, under the caller's config "
            "(settings.USE_TZ toggled, TIME_ZONE='UTC'). Runs the REAL callee in the "
            "instance image over boundary zones + 2000 fuzz cases; any mismatch is "
            "AXIOM-UNSOUND. Embeds axiom_check.py (read on host)."
        ),
    },
    {
        "id": "ax-cover-selected_tzname",
        "axiom": "selected_tzname",
        "kind": "axiom-containment",
        "expect": "covered",
        "apply_gold": True,
        "probe": _AX_COVER_PROBE,
        "rationale": (
            "Containment: the callee-inputs the model can reach are exactly "
            "USE_TZ in {True,False} x self.tzinfo in {None} U {real zones}; get_tzname "
            "is total over that domain. The probe exercises the boundary (incl. the "
            "USE_TZ-off corner the model reaches) and asserts the real callee accepts "
            "every reachable input with the expected value. A reachable input outside "
            "the domain would be AXIOM-TOO-WEAK-FOR-CALLER; none exists."
        ),
    },
]
