"""properties.py — PBT falsification manifest for django__django-10999.

NOT a Nagini module: a record of adversarial cases the runner
(`swebench_nagini.pbt`) executes. See the battery-authoring brief (esp. §2 "four
falsification checks" and §4a "Adversarial, NOT mechanical").

This battery is reasoned from THIS spec's defended surface, not stamped out by a
corruption template. The function under spec is

    parse_clock_seconds(fields: List[int], leading_minus: bool,
                        inner_sign_seen: bool) -> Optional[int]

= the standard-duration colon-form branch of django.utils.dateparse.parse_duration
(driven by the gold-patch standard_duration_re), with the load-bearing contract

    Requires(Acc(list_pred(fields), 1/2))                    # read-only input
    Requires(1 <= len(fields) and len(fields) <= 3)
    Requires(Forall k: 0<=k<len(fields) ==> fields[k] >= 0)  # non-negative fields
    Ensures (Acc(list_pred(fields), 1/2))                    # returns the read perm
    Ensures (Implies(inner_sign_seen, Result() is None))     # inner-sign rejection
    Ensures (Implies(not inner_sign_seen,
                     Result() is not None and
                     Result() == signed_total(ToSeq(fields), leading_minus)))

What the spec actually defends, and the attacks it must survive:

  * The output pin `Result() == signed_total(ToSeq(fields), leading_minus)` is
    GROUNDED in the input: `signed_total`/`clock_value`/`pow60` are @Pure deep
    models (NOT @ContractOnly axioms), fully unfolded by Viper, equal to the real
    post-patch standard_duration_re + parse_duration sign logic (G-AX /
    axiom_check.py). The oracle is a function OF (`fields`, `leading_minus`), not
    an opaque answer-key marker — so there is no "echo a wrong oracle" shortcut.
    A direct `return signed_total(ToSeq(fields), leading_minus)` is simply the
    CORRECT cheapest honest impl (pos-control-direct-oracle): it does the real
    work because `signed_total` is the work. (Hence there is no SPEC-TOO-WEAK
    ungrounded-echo reject case for this instance — see 'assessment'.)

  * Two independent behaviours are pinned, exactly matching the two prepatches
    in meta.json:
      (1) whole-value sign distribution — the leading minus negates the WHOLE
          base-60 total, not just the leading field (clause:
          Result() == signed_total(...) which is -clock_value when leading_minus).
          model_prepatch.py reverts to per-field sign and FAILS this clause
          (e.g. -15:30 -> -930 vs pre-patch -870). Rival `partial-perfield-sign`
          reproduces exactly that bug.
      (2) inner-sign rejection — a sign after a separator yields no standard
          match (None). model_prepatch_2.py allows it and FAILS the
          Implies(inner_sign_seen, Result() is None) clause. Rival
          `partial-inner-sign-value` reproduces exactly that bug.

  * `fields` is held read-only (Acc(list_pred(fields), 1/2)). The MANDATORY
    attack is FRAME MUTATION (`frame-mutate-fields`): an impl that WRITES to
    `fields` to satisfy the pin vacuously must fail for INSUFFICIENT PERMISSION.

Authoring mechanics (preserved from the schema): every spec variant is built by
REGION-SURGERY (`_swap`) that edits ONLY inside `# impl-start`/`# impl-end` (the
nested invariants live there too), so `markers.same_spec` is GUARANTEED and a
rejection comes from the POSTCONDITION catching wrong behaviour (or the
permission system), never from a tampered spec. Each `expect:"reject"` rival
carries the refinement argument that its faithful real patch would NOT resolve
the F2P. The axiom lane re-runs the A-reference deep model == the REAL
post-patch standard_duration_re + parse_duration sign logic in Docker (a port of
axiom_check.py), and a caller-domain containment probe.
"""
from pathlib import Path

INSTANCE = "django__django-10999"
FLOAT_ENCODING = None

# --- base spec (frozen) ------------------------------------------------------
_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src: str, old: str, new: str) -> str:
    """Replace exactly one occurrence of an impl-region substring; assert it
    actually matched so silent drift (model.py edited) fails loudly at load."""
    if old not in src:
        raise AssertionError(f"properties.py drift: substring not found:\n{old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"properties.py: substring not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Region landmarks (all strictly INSIDE the impl region of model.py).
# ---------------------------------------------------------------------------

# The whole gold impl body (everything between # impl-start and # impl-end),
# used as a single replaceable block for structural rewrites.
_GOLD_BODY = """    if inner_sign_seen:
        return None
    # Accumulate the positional magnitude right-to-left (seconds, minutes,
    # hours) so the front-recursive clock_value unfolds one field per step.
    total = 0  # type: int
    weight = 1  # type: int
    i = len(fields)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(fields), 1 / 2))
        Invariant(0 <= i and i <= len(fields))
        Invariant(weight == pow60(len(fields) - i))
        Invariant(total == clock_value(ToSeq(fields).drop(i)))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        Assert(ToSeq(fields).drop(i - 1)[0] == fields[i - 1])
        Assert(ToSeq(fields).drop(i - 1).drop(1) == ToSeq(fields).drop(i))
        Assert(len(ToSeq(fields).drop(i - 1)) == len(fields) - (i - 1))
        total = fields[i - 1] * weight + total
        weight = weight * 60
        i = i - 1
    Assert(total == clock_value(ToSeq(fields)))
    if leading_minus:
        return -total
    return total"""

# landmark for the loop-body read of a field (used by frame-mutation)
_FIELD_READ = "        total = fields[i - 1] * weight + total\n"

# landmark for the final sign application (used by partial-domain rivals)
_FINAL_SIGN = """    if leading_minus:
        return -total
    return total"""

# landmark for the inner-sign short-circuit (used by partial-inner-sign rival)
_INNER_GUARD = """    if inner_sign_seen:
        return None
"""


# ===========================================================================
# POSITIVE CONTROLS (soundness / admissibility) — expect "verify"
# ===========================================================================

# (5a) Cheapest honest correct impl: return the GROUNDED oracle directly. No
# loop at all -- maximally structurally different from the gold right-to-left
# fold. The postcondition Result() == signed_total(ToSeq(fields), leading_minus)
# is satisfied trivially (Result() IS signed_total(...)), Result() is not None
# (signed_total returns int), and the read-only permission is never touched. If
# this fails to verify the spec is over-fit to the fold code shape =>
# SPEC-TOO-STRONG. Also doubles as the honest "no ungrounded echo" control: the
# oracle is the real work, so a direct return is correct, not a cheat.
_POS_DIRECT_ORACLE_BODY = """    if inner_sign_seen:
        return None
    return signed_total(ToSeq(fields), leading_minus)"""
_POS_DIRECT_ORACLE = _swap(_BASE, _GOLD_BODY, _POS_DIRECT_ORACLE_BODY)

# (5b) Structurally-different but CORRECT: SAME right-to-left fold and ALL gold
# invariants/asserts kept verbatim (pilot bug #2: never drop a framing assert),
# but the final sign application is reshaped into a local variable `signed`
# computed in a branch-reordered (non-minus-first) form, then returned once.
# A local-variable reshape, NOT a loop-direction flip (pilot bug #3). If this
# fails to verify the spec is over-fit to the inline two-return sign form =>
# SPEC-TOO-STRONG.
_POS_LOCAL_RESHAPE_BODY = _GOLD_BODY.replace(
    _FINAL_SIGN,
    """    signed = total  # type: int
    if leading_minus:
        signed = -total
    return signed""",
    1,
)
_POS_LOCAL_RESHAPE = _swap(_BASE, _GOLD_BODY, _POS_LOCAL_RESHAPE_BODY)

# (6) ADMISSIBILITY. A self-call on an F2P-shaped input ([15, 30], leading_minus,
# not inner-sign) -- the literal "-15:30" from test_negative -- must establish
# the precondition (Acc(list_pred(.),1/2); 1<=len<=3; non-negative fields). The
# fresh list literal [15, 30] carries full list_pred, the values are >= 0, len==2,
# so the Requires must be establishable for this normal input. If the self-call
# fails to verify the precondition => PRECOND-TOO-STRONG. Inserted at the head of
# the impl region; the gold body follows verbatim.
_ADMISS_HEAD = "    if inner_sign_seen:\n        return None\n"
_ADMISS_HEAD_NEW = (
    "    probe = [15, 30]  # type: List[int]\n"
    "    Assert(Acc(list_pred(probe), 1 / 2))\n"
    "    Assert(1 <= len(probe) and len(probe) <= 3)\n"
    "    Assert(Forall(int, lambda k: (Implies(0 <= k and k < len(probe),\n"
    "                                          probe[k] >= 0), [[probe[k]]])))\n"
    "    if inner_sign_seen:\n        return None\n"
)
_ADMISS = _swap(_BASE, _ADMISS_HEAD, _ADMISS_HEAD_NEW)


# ===========================================================================
# UNIQUENESS RIVALS (spec-too-weak probes) — expect "reject"
# ===========================================================================

# (1) FRAME MUTATION — MANDATORY, the #1 weakness class. `fields` is read-only
# (Acc(list_pred(fields), 1/2)). This rival WRITES `fields[i - 1] = 0` inside the
# loop before reading it. Under the 1/2 (read-only) permission a store to
# `fields` requires FULL permission, so it MUST fail for INSUFFICIENT PERMISSION
# (not for a wrong value). The gold invariants/asserts are kept verbatim around
# it so the failure is attributable solely to the write. Rejection source: the
# PERMISSION SYSTEM (the store is unverifiable under 1/2 read-only access).
_FRAME_BODY = _GOLD_BODY.replace(
    _FIELD_READ,
    "        fields[i - 1] = 0\n" + _FIELD_READ,
    1,
)
_RIVAL_FRAME = _swap(_BASE, _GOLD_BODY, _FRAME_BODY)

# (3a) PARTIAL-DOMAIN — per-field sign (the EXACT pre-patch bug, == model_prepatch.py).
# Correct on EVERY input EXCEPT leading-minus literals: instead of negating the
# WHOLE base-60 total, it negates only the LEADING field's positional contribution
# (total - 2*fields[0]*pow60(len-1)). For "-15:30": total=930, lead=15*60=900 ->
# 930-1800 = -870 (the pre-patch value) instead of -930. Diverges only on the
# leading_minus sub-domain (non-minus inputs are returned identically). Rejection
# source: the postcondition Result() == signed_total(ToSeq(fields), leading_minus)
# = -clock_value(fields) when leading_minus (whole-value sign).
_PERFIELD_SIGN_BODY = _GOLD_BODY.replace(
    _FINAL_SIGN,
    """    if leading_minus:
        return total - 2 * fields[0] * pow60(len(fields) - 1)
    return total""",
    1,
)
_RIVAL_PERFIELD = _swap(_BASE, _GOLD_BODY, _PERFIELD_SIGN_BODY)

# (3b) PARTIAL-DOMAIN — drop the sign entirely (leading minus ignored). Correct on
# every non-minus input; on leading-minus inputs returns +total instead of -total
# (e.g. "-15:30" -> 930). Diverges only on the leading_minus sub-domain. Rejection
# source: the same whole-value-sign postcondition clause.
_DROP_SIGN_BODY = _GOLD_BODY.replace(
    _FINAL_SIGN,
    "    return total",
    1,
)
_RIVAL_DROP_SIGN = _swap(_BASE, _GOLD_BODY, _DROP_SIGN_BODY)

# (3c) PARTIAL-DOMAIN — inner-sign accepted (the EXACT second pre-patch bug,
# == model_prepatch_2.py). Drops the `if inner_sign_seen: return None`
# short-circuit, so an inner-sign literal falls through to compute a value
# instead of None. Correct on every non-inner-sign input; diverges only on the
# inner_sign_seen sub-domain. Rejection source: the postcondition
# Implies(inner_sign_seen, Result() is None).
_RIVAL_INNER_VALUE = _swap(_BASE, _INNER_GUARD, "")


SPEC_TESTS = [
    # ---- positive controls (must VERIFY) ----
    {"id": "pos-control-direct-oracle", "kind": "soundness", "expect": "verify",
     "module": _POS_DIRECT_ORACLE,
     "rationale": "the cheapest honest correct impl returns the GROUNDED oracle "
                  "signed_total(ToSeq(fields), leading_minus) directly (no loop). "
                  "Result() IS signed_total(...) so the pin holds trivially, Result() "
                  "is not None (int), permission untouched. If this fails => the spec is "
                  "over-fit to the fold code shape (SPEC-TOO-STRONG). Also the honest "
                  "no-ungrounded-echo control: the oracle is the real work, so a direct "
                  "return is correct, not a cheat."},
    {"id": "pos-control-local-reshape", "kind": "soundness", "expect": "verify",
     "module": _POS_LOCAL_RESHAPE,
     "rationale": "structurally-different but correct: SAME right-to-left fold and ALL "
                  "gold invariants/asserts kept verbatim, only the final sign application "
                  "reshaped into a local `signed` (branch-reordered, single return). A "
                  "local-variable reshape, not a loop-direction flip. If it fails => the "
                  "spec is over-fit to the inline two-return form (SPEC-TOO-STRONG)."},
    {"id": "admiss-negative-clock", "kind": "admissibility", "expect": "verify",
     "module": _ADMISS,
     "rationale": "a self-call on the F2P-shaped input [15,30]/leading_minus/not-inner "
                  "(the literal -15:30 from test_negative) must establish the precondition "
                  "(Acc(list_pred(.),1/2); 1<=len<=3; fields>=0). The fresh list literal "
                  "carries full list_pred, values >=0, len==2. If the self-call cannot "
                  "establish the Requires for this normal input => PRECOND-TOO-STRONG."},

    # ---- uniqueness rivals (must be REJECTED) ----
    {"id": "frame-mutate-fields", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_FRAME,
     "refinement": "no faithful real patch corresponds to this: parse_duration's input is "
                   "an immutable str and the regex extraction never mutates the captured "
                   "field magnitudes. The rival exists only to test whether the read-only "
                   "(1/2) precondition on `fields` can be subverted by writing to it. There "
                   "is no resolving patch that overwrites its extracted fields, so a "
                   "verifying rival here would be a pure verify-not-resolve artifact "
                   "(vacuous satisfaction via self-mutation).",
     "rationale": "MANDATORY frame-mutation probe. `fields[i-1] = 0` writes through a 1/2 "
                  "(read-only) reference and MUST fail for insufficient permission. "
                  "Rejection source: the PERMISSION SYSTEM (store needs full perm), not a "
                  "value mismatch; the gold invariants/asserts are kept verbatim. If it "
                  "verified => SPEC-TOO-WEAK (frame protection hollow)."},
    {"id": "partial-perfield-sign", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_PERFIELD,
     "refinement": "this is the EXACT pre-patch behaviour (== model_prepatch.py): the "
                   "per-field optional signs (?P<hours>-?\\d+)... attached the minus to only "
                   "the leading field, so -15:30 -> -15*60+30 = -870 not -930 and -1:15:30 "
                   "-> -3600+15*60+30 = -2670 not -4530. Its faithful real patch is the "
                   "pre-patch regex, which FAILS the F2P test_negative (which now asserts "
                   "-15:30 == timedelta(minutes=-15, seconds=-30) = -930). So it would NOT "
                   "resolve.",
     "rationale": "partial-domain: correct on every non-minus input, diverges only on the "
                  "leading_minus sub-domain (negates only the leading field). Rejection "
                  "source: the whole-value-sign postcondition Result() == signed_total(...) "
                  "= -clock_value(fields) when leading_minus. If it verified => "
                  "SPEC-TOO-WEAK (admits the pre-patch per-field sign)."},
    {"id": "partial-drop-sign", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_DROP_SIGN,
     "refinement": "ignores the leading minus entirely (returns +total on leading-minus "
                   "literals: -15:30 -> 930). A faithful real patch that dropped the sign "
                   "application (sign always +1) would return positive durations for "
                   "negative literals and FAIL the F2P test_negative (-15:30 must be -930). "
                   "So it would NOT resolve.",
     "rationale": "partial-domain near-miss with a real refinement: correct on every "
                  "non-minus input, diverges on the leading_minus sub-domain. Rejection "
                  "source: the whole-value-sign postcondition clause. If it verified => "
                  "SPEC-TOO-WEAK."},
    {"id": "partial-inner-sign-value", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_INNER_VALUE,
     "refinement": "this is the EXACT second pre-patch behaviour (== model_prepatch_2.py): "
                   "the pre-patch per-field signs allowed a minus after a separator, so an "
                   "inner-sign literal like -01:-01 still matched and produced a value "
                   "instead of None. Its faithful real patch is the pre-patch regex, which "
                   "FAILS the F2P test_negative (which now asserts -01:-01 == None). So it "
                   "would NOT resolve.",
     "rationale": "partial-domain: correct on every non-inner-sign input, diverges only on "
                  "the inner_sign_seen sub-domain (returns a value instead of None). "
                  "Rejection source: the postcondition Implies(inner_sign_seen, Result() is "
                  "None). If it verified => SPEC-TOO-WEAK (admits inner-sign acceptance)."},
]

# ===========================================================================
# AXIOM LANE (Docker, real callee) — A-reference deep-model soundness + containment
# ===========================================================================
#
# This bundle has NO @ContractOnly axiom (meta.axioms == []). The changed
# behaviour is modeled DEEPLY (clock_value/signed_total/the inner_sign_seen rule),
# an A-reference validated == the real callee by axiom_check.py / G-AX. The axiom
# lane re-runs that soundness check in Docker (a faithful port of axiom_check.py:
# the gold-patch standard_duration_re + parse_duration sign logic, on boundary +
# fuzz colon-form literals), and a caller-domain containment probe.

# (A) A-reference SOUNDNESS: deep model (clock_value/signed_total/validity) ==
# real post-patch standard_duration_re + parse_duration sign logic. Port of
# axiom_check.py; stdlib-only (re/datetime/random), reads no bundle file, opens
# nothing. The `sign` group is `-?` (minus only) so a leading `+` is out of the
# modeled domain (matches the model's leading_minus-only carrier). apply_gold is
# irrelevant (the regex is reconstructed verbatim from the patch, not read from
# the repo), but we set it True for consistency with "post-gold behaviour".
_AX_REF_SOUND = r'''
import datetime, random, re, sys

# the gold-patch standard_duration_re VERBATIM (django/utils/dateparse.py:29).
standard_duration_re = re.compile(
    r'^'
    r'(?:(?P<days>-?\d+) (days?, )?)?'
    r'(?P<sign>-?)'
    r'((?:(?P<hours>\d+):)(?=\d+:\d+))?'
    r'(?:(?P<minutes>\d+):)?'
    r'(?P<seconds>\d+)'
    r'(?:\.(?P<microseconds>\d{1,6})\d{0,6})?'
    r'$'
)

def real_standard_seconds(value):
    """REAL post-patch standard-duration branch of parse_duration on a colon-form
    literal (no days, no fractional part) -> signed int total seconds, or None on
    no standard match. Mirrors parse_duration's sign handling exactly."""
    m = standard_duration_re.match(value)
    if not m:
        return None
    kw = m.groupdict()
    if kw.get('days') is not None:
        return None  # out of modeled (no-days) domain
    sign = -1 if kw.pop('sign', '+') == '-' else 1
    fields = {k: float(v) for k, v in kw.items()
              if k in ('hours', 'minutes', 'seconds') and v is not None}
    td = sign * datetime.timedelta(**fields)
    secs = td.total_seconds()
    if secs != int(secs):
        print("unexpected fractional total for %r" % value); sys.exit(1)
    return int(secs)

# the model deep model (clock_value/signed_total) reproduced as plain python.
def clock_value(fields):
    n = len(fields); total = 0
    for idx, f in enumerate(fields):
        total += f * (60 ** (n - 1 - idx))
    return total

def signed_total(fields, leading_minus):
    v = clock_value(fields)
    return -v if leading_minus else v

def model_parse(fields, leading_minus, inner_sign_seen):
    if inner_sign_seen:
        return None
    return signed_total(fields, leading_minus)

def abstract(value):
    """colon-form literal -> (fields, leading_minus, inner_sign_seen) or None when
    outside the model's colon-and-digits domain (so we only compare where defined).
    A leading '+' is out of domain (sign group is -? minus-only)."""
    if value.startswith('+'):
        return None
    leading_minus = value.startswith('-')
    body = value[1:] if (value and value[0] == '-') else value
    parts = body.split(':')
    if not (1 <= len(parts) <= 3):
        return None
    fields = []; inner_sign_seen = False
    for i, p in enumerate(parts):
        seg = p
        if i > 0 and seg[:1] in '+-':
            inner_sign_seen = True
            seg = seg[1:]
        if seg == '' or not seg.isdigit():
            return None
        fields.append(int(seg))
    return fields, leading_minus, inner_sign_seen

bad = []
def check(value):
    a = abstract(value)
    if a is None:
        return
    fields, leading_minus, inner = a
    real = real_standard_seconds(value)
    exp = model_parse(fields, leading_minus, inner)
    if inner:
        # model declares invalid -> real pipeline must not match as standard duration
        if real is not None:
            bad.append(("inner-sign-not-rejected", value, real))
        return
    if real != exp:
        bad.append(("unsound", value, real, exp, fields, leading_minus))

boundary = [
    '30', '-30', '+30',
    '15:30', '-15:30', '5:30', '-5:30',
    '10:15:30', '-10:15:30', '1:15:30', '-1:15:30',
    '00:01:01', '-00:01:01', '01:01', '-01:01',
    '0:00:00', '-0:00:00', '100:200:300', '-100:200:300',
    # inner-sign literals: the post-patch rule rejects these as standard
    '-01:-01', '01:-01', '-1:-15:30', '15:-30', '1:15:-30', '+15:30',
]
for v in boundary:
    check(v)

rng = random.Random(10999)
for _ in range(50000):
    nfields = rng.randint(1, 3)
    sgn = rng.choice(['', '-', '+'])
    segs = []
    for i in range(nfields):
        inner = rng.choice(['', '', '', '-', '+']) if i > 0 else ''
        digits = ''.join(rng.choice('0123456789') for _ in range(rng.randint(1, 3)))
        segs.append(inner + digits)
    v = sgn + ':'.join(segs)
    check(v)

if bad:
    print("A-REFERENCE-UNSOUND: deep model != real post-patch pipeline on", bad[:8])
    sys.exit(1)
print("A-REFERENCE SOUND: clock_value/signed_total/validity == real post-patch "
      "standard_duration_re + parse_duration sign logic on %d boundary + 50000 "
      "fuzz colon-form literals (0 mismatch)" % len(boundary))
sys.exit(0)
'''

# (B) CALLER-DOMAIN CONTAINMENT. The model's Requires is exactly: fields is a
# 1..3 list of NON-NEGATIVE ints, plus the two booleans. So every (fields,
# leading_minus, inner_sign_seen) the modeled function can reach has fields a
# non-negative magnitude list of length 1..3. The A-reference soundness check
# above (real_standard_seconds + abstract) is exactly defined on that domain (it
# returns None / skips anything outside it), so the deep model is validated == the
# real callee on EVERY caller-reachable input -- containment holds by construction.
# This probe confirms: (i) the abstract() decomposition accepts every in-domain
# carrier and rejects every out-of-domain literal (leading '+', non-digit, wrong
# arity), and (ii) the real pipeline is exercised on each reachable shape (1/2/3
# fields x sign x inner) so none is silently skipped. A reachable input the
# soundness check could NOT exercise would be AXIOM-TOO-WEAK-FOR-CALLER.
_AX_CONTAINMENT = r'''
import re, sys

standard_duration_re = re.compile(
    r'^'
    r'(?:(?P<days>-?\d+) (days?, )?)?'
    r'(?P<sign>-?)'
    r'((?:(?P<hours>\d+):)(?=\d+:\d+))?'
    r'(?:(?P<minutes>\d+):)?'
    r'(?P<seconds>\d+)'
    r'(?:\.(?P<microseconds>\d{1,6})\d{0,6})?'
    r'$'
)

def abstract(value):
    if value.startswith('+'):
        return None
    leading_minus = value.startswith('-')
    body = value[1:] if (value and value[0] == '-') else value
    parts = body.split(':')
    if not (1 <= len(parts) <= 3):
        return None
    fields = []; inner = False
    for i, p in enumerate(parts):
        seg = p
        if i > 0 and seg[:1] in '+-':
            inner = True; seg = seg[1:]
        if seg == '' or not seg.isdigit():
            return None
        fields.append(int(seg))
    return fields, leading_minus, inner

problems = []

# (i) every reachable carrier shape is accepted by abstract() and the model's
# Requires (1<=len(fields)<=3, fields>=0); the real regex is exercised on it.
# Enumerate the reachable SHAPE space: arity 1/2/3 x leading sign x inner sign.
covered_shapes = set()
for arity in (1, 2, 3):
    for sgn in ('', '-'):
        # inner sign only meaningful when arity >= 2
        inner_opts = ('', '-') if arity >= 2 else ('',)
        for innerpos in inner_opts:
            segs = []
            for i in range(arity):
                pre = innerpos if i == 1 else ''
                segs.append(pre + '7')
            v = sgn + ':'.join(segs)
            a = abstract(v)
            if a is None:
                problems.append(("reachable shape rejected by abstract", v))
                continue
            fields, lm, inner = a
            if not (1 <= len(fields) <= 3) or any(f < 0 for f in fields):
                problems.append(("reachable carrier outside model Requires", v, fields))
            # the real regex must be exercised (match or deliberate non-match);
            # for non-inner it should match, for inner it should not match.
            m = standard_duration_re.match(v)
            if inner and m is not None:
                # inner-sign literal must NOT be a standard match
                problems.append(("inner-sign reachable but real matched", v))
            if (not inner) and m is None:
                problems.append(("valid reachable shape not matched by real regex", v))
            covered_shapes.add((arity, sgn, innerpos))

# (ii) out-of-domain literals the model CANNOT reach must be rejected by abstract
# (so the soundness comparison never silently includes them as in-domain).
out_of_domain = ['+30', '+1:2', '1:2:3:4', '', ':30', '30:', 'ab', '1:x', '-']
for v in out_of_domain:
    if abstract(v) is not None:
        problems.append(("out-of-domain literal accepted as in-domain", v))

if problems:
    print("CONTAINMENT FAIL:", problems[:8]); sys.exit(1)
print("CONTAINMENT OK: every caller-reachable carrier (arity 1/2/3 x sign x "
      "inner-sign, %d shapes) lies in the model Requires AND is exercised by the "
      "real regex; out-of-domain literals are rejected (not silently compared)."
      % len(covered_shapes))
sys.exit(0)
'''

AXIOM_TESTS = [
    {"id": "ax-ref-sound", "axiom": "signed_total/clock_value/validity",
     "kind": "axiom-soundness", "expect": "holds", "apply_gold": True,
     "probe": _AX_REF_SOUND,
     "rationale": "the A-reference deep model (clock_value/signed_total + the "
                  "inner_sign_seen=>None rule) must equal the REAL post-patch "
                  "standard_duration_re + parse_duration sign logic on 25 boundary + 50000 "
                  "fuzz colon-form literals (whole-value sign; inner-sign rejected). Any "
                  "mismatch => the deep model is unsound (A-REFERENCE-UNSOUND). Port of "
                  "axiom_check.py; stdlib-only."},
    {"id": "ax-containment", "axiom": "signed_total/clock_value/validity",
     "kind": "axiom-containment", "expect": "covered", "apply_gold": True,
     "probe": _AX_CONTAINMENT,
     "rationale": "every input the modeled function can reach (fields a 1..3 non-negative "
                  "list, two booleans) lies in the domain the A-reference soundness check "
                  "exercises (the real regex is run on every reachable arity/sign/inner-sign "
                  "shape); out-of-domain literals (leading +, non-digit, wrong arity) are "
                  "rejected so they are never silently compared. A reachable shape the "
                  "soundness check could not exercise => AXIOM-TOO-WEAK-FOR-CALLER."},
]
