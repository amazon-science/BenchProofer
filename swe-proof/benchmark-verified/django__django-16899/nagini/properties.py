"""properties.py — PBT falsification manifest for django__django-16899.

NOT a Nagini module: a record of adversarially-reasoned cases the runner
(`swebench_nagini.pbt`) executes and stamps with RESULT. See the battery-authoring brief
(esp. §2 "four falsification checks" and §4a "Adversarial, NOT mechanical").

DEFENDED SURFACE (frozen spec in model.py; see refinement.md / mapping.md):

    check_reference(label, value, cls, model_label: List[int], resolves: bool)
        -> List[int]                       # the diagnostic message, or [] if OK
    Requires(Acc(list_pred(label),       1/2))   # READ-ONLY input (1/2 perm)
    Requires(Acc(list_pred(value),       1/2))   # READ-ONLY input (1/2 perm)
    Requires(Acc(list_pred(cls),         1/2))   # READ-ONLY input (1/2 perm)
    Requires(Acc(list_pred(model_label), 1/2))   # READ-ONLY input (1/2 perm)
    Ensures(Acc(list_pred(label/value/cls/model_label), 1/2))  # frame returned
    Ensures(Acc(list_pred(Result())))            # result is a FRESH full-perm list
    Ensures(resolves == (len(Result()) == 0))    # CLAUSE-2: empty iff resolves
    Ensures(Implies(not resolves,
            ToSeq(Result()) == diagnostic_message(               # CLAUSE-3: WHOLE pin
                ToSeq(label), ToSeq(value), ToSeq(cls), ToSeq(model_label))))
    Ensures(Implies(not resolves,
            ToSeq(Result()).drop(len(seg_intro())+len(label)+len(seg_refers()))
                           .take(len(value)) == ToSeq(value)))   # CLAUSE-4: value-position

    diagnostic_message(label, value, cls, model_label)
      = seg_intro() + label + seg_refers() + value + seg_which_not()
        + cls + seg_or_attr() + model_label + seg_end()
    with seg_intro/refers/which_not/or_attr/end = PSeq(1..5): the five fixed
    prose pieces of the template, modelled by one-token markers (mapping.md §2).

WHAT THE GOLD FIX IS, AND WHAT THE SPEC MUST DEFEND
  The gold patch inserts a NEW `%s` (the offending reference VALUE) right after
  the label slot, changing the template from
    "The value of '%s' is not a callable, an attribute of '%s', or an attr of '%s'."
                                                                  % (label, cls, model_label)
  to
    "The value of '%s' refers to '%s', which is not a callable, an attribute of
     '%s', or an attribute of '%s'."          % (label, field_name, cls, model_label)
  So the entire content of the change is: the offending VALUE is now NAMED in
  the message, as its own quoted segment immediately after the label. The spec
  pins this three ways — CLAUSE-3 (the whole-message equality with `value`
  present), CLAUSE-4 (the value occupies its own contiguous slot at the offset
  after intro+label+refers), and CLAUSE-2 (empty result iff the reference
  resolves). Every uniqueness rival targets one of those.

GROUNDED-ORACLE NOTE (directive 2, ungrounded-oracle echo):
  `diagnostic_message` is a @Pure helper but it is GROUNDED in the inputs — it
  is a function OF `label/value/cls/model_label` (their carriers spliced between
  five constant markers), NOT an opaque answer-key marker. There is NO executable
  materialization of a @Pure PSeq into a list_pred list, so an impl CANNOT "echo"
  it; the only way to make `ToSeq(Result())` equal it is to build the list by
  concatenating the actual carriers — which IS the real work, and which IS
  correct. So there is no WRONG echo that could verify: UNGROUNDED-ORACLE-ECHO
  does NOT apply. The honest cheapest-impl positive control (`pos-master-assert`)
  stands in for it and confirms the grounded pin still does the work.

CONTROL-FLOW-EFFECT NOTE (directive 4): `check_reference` has one observable
  effect — the returned List[int] (empty vs the message). The resolve/error
  split is fully captured by CLAUSE-2 (empty iff resolves), so a wrong control-
  flow choice manifests as a value/emptiness difference the spec already pins;
  there is no raise / side-effect channel invisible to the value abstraction.
  The `discriminator-flip` rival below exercises exactly the control-flow split
  (emit a message on the resolve path), and it is caught as a value defect.

AUTHORING MECHANICS: every spec variant is built by REGION-SURGERY (`_swap`) that
  edits ONLY text strictly inside `# impl-start`/`# impl-end`. `spec_view` elides
  that whole region, so `markers.same_spec` is GUARANTEED and any rejection is
  attributable to the POSTCONDITION catching wrong behaviour (or the permission
  system), never to a tampered spec. Each expect="reject" rival carries the
  refinement argument that its faithful real patch would NOT resolve the F2P.

AXIOM LANE: there is NO @ContractOnly axiom CONSUMED (the axioms region is
  documentation-only). `diagnostic_message` is an A-REFERENCE deep model,
  validated == the REAL Python `%`-formatting of the gold post-patch template by
  axiom_check.py (G-AX). The probes below re-run that real-callee equivalence
  (the stdlib `%`-operator on the verbatim post-patch template) on the F2P
  witnesses + apostrophe/percent/non-ascii boundaries + heavy fuzz, plus the
  value-position guarantee and the differential against the pre-patch template.
"""
from pathlib import Path

INSTANCE = "django__django-16899"
FLOAT_ENCODING = None  # meta.json float_encoding is null


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
# Stable anchors strictly INSIDE the impl region of model.py.
# ---------------------------------------------------------------------------

# The resolve early-return (the no-diagnostic path). Insertion point for
# admissibility and the resolve-path discriminator flip.
_RESOLVE_BRANCH = (
    "    if resolves:\n"
    "        ok = []  # type: List[int]\n"
    "        return ok\n"
)

# Fresh-result initialisation on the error path (head of the build).
_INIT_RESULT = "    result = []  # type: List[int]\n"

# The value interpolation: the inserted `' refers to '` marker + the value
# carrier. This is the entire content of the gold change.
_VALUE_SPLICE = (
    "    result = result + [2]          # \"' refers to '\"  (added value interpolation)\n"
    "    result = result + value        # value  (the offending reference, named)\n"
)

# The closing return on the error path (the resolve path uses `return ok`).
_RETURN_RESULT = "    return result\n"

for _a in (_RESOLVE_BRANCH, _INIT_RESULT, _VALUE_SPLICE, _RETURN_RESULT):
    assert _BASE.count(_a) == 1, f"anchor drifted: {_a!r}"


# ===========================================================================
# POSITIVE CONTROLS / ADMISSIBILITY  (expect "verify")
# ===========================================================================

# (5a) STRUCTURALLY-DIFFERENT but CORRECT. The gold builds `result` by a chain of
# `result = result + <piece>`; this variant builds the SAME sequence in ONE
# combined expression (different source shape, identical value). `diagnostic_message`
# is a FLAT `+` chain (NOT a recursive fold), so the equality with the combined
# expression is a direct sequence identity the SMT backend discharges WITHOUT any
# `f(a+b)==f(a)+f(b)` induction lemma — this avoids the forward-append-vs-front-
# recursive-fold trap (directive 3). If it fails to verify, the postcondition is
# over-fit to one concatenation shape => SPEC-TOO-STRONG.
_POS_ONE_EXPR = _swap(
    _BASE,
    _INIT_RESULT
    + "    result = result + [1]          # \"The value of '\"\n"
      "    result = result + label        # label\n"
    + _VALUE_SPLICE
    + "    result = result + [3]          # \"', which is not a callable, an attribute of '\"\n"
      "    result = result + cls          # class name\n"
      "    result = result + [4]          # \"', or an attribute of '\"\n"
      "    result = result + model_label  # model label\n"
      "    result = result + [5]          # \"'.\"\n",
    "    result = ([1] + label + [2] + value + [3] + cls + [4] + model_label\n"
    "              + [5])  # type: List[int]\n",
)

# (5b / 2) HONEST cheapest-impl / no-echo control. Assert, right before the error-
# path return (when `result` is the COMPLETE message), that what was built EQUALS
# the spec oracle `diagnostic_message(...)`. The oracle is GROUNDED in the args
# (no opaque marker, no executable materialization), so the cheapest impl that
# satisfies CLAUSE-3 still concatenates the real carriers — this assert is
# redundant with the gold proof and MUST verify. Its purpose: demonstrate there is
# no WRONG oracle-echo that verifies (else this would be a reject case). If it
# failed => SPEC-TOO-STRONG (the gold proof would not establish its own oracle).
_POS_MASTER = _swap(
    _BASE,
    _RETURN_RESULT,
    "    Assert(ToSeq(result) == diagnostic_message(\n"
    "        ToSeq(label), ToSeq(value), ToSeq(cls), ToSeq(model_label)))\n"
    + _RETURN_RESULT,
)

# (6) ADMISSIBILITY. A self-call on the exact F2P-shaped input — label=
# "readonly_fields[1]", value="nonexistent", cls="SongAdmin",
# model_label="admin_checks.Song", resolves=False (the F2P
# `test_nonexistent_field` shape) — must establish the four
# Acc(list_pred(.),1/2) preconditions for a normal input. The four call args
# are fresh locals (full perm, so 1/2 is trivially establishable); the probe
# discards the result and the gold body that follows is unchanged. If the call
# site fails to verify the precondition => PRECOND-TOO-STRONG.
_ADMISS = _swap(
    _BASE,
    _RESOLVE_BRANCH,
    "    plabel = [114, 102, 91, 49, 93]  # type: List[int]\n"        # "rf[1]" stand-in (any code points)
    "    pvalue = [110, 111, 110, 101]  # type: List[int]\n"          # "none"
    "    pcls = [83, 111, 110, 103]  # type: List[int]\n"             # "Song"
    "    pml = [97, 46, 83]  # type: List[int]\n"                     # "a.S"
    "    Assert(Acc(list_pred(plabel), 1 / 2))\n"
    "    Assert(Acc(list_pred(pvalue), 1 / 2))\n"
    "    Assert(Acc(list_pred(pcls), 1 / 2))\n"
    "    Assert(Acc(list_pred(pml), 1 / 2))\n"
    + _RESOLVE_BRANCH,
)


# ===========================================================================
# UNIQUENESS RIVALS (spec-too-weak probes) — expect "reject"
# ===========================================================================

# (1) FRAME MUTATION — MANDATORY, the #1 weakness class. `value` is read-only
# (held at 1/2 permission). This rival appends to `value` at the error-path head
# (a write through a 1/2 reference) BEFORE running the gold build verbatim. A
# store into the list_pred requires FULL permission, so it MUST fail for
# INSUFFICIENT PERMISSION — not a value mismatch. The gold body is kept verbatim
# after the write, so the rejection is attributable solely to the illegal store.
# Rejection source: the PERMISSION SYSTEM.
_RIVAL_FRAME = _swap(
    _BASE,
    _INIT_RESULT,
    "    value.append(120)\n" + _INIT_RESULT,
)

# (2, the discriminating BUG / partial-domain == the PRE-PATCH shape) DROP THE
# VALUE. Omit the inserted `' refers to '` marker AND the value carrier — exactly
# the pre-gold behaviour (model_prepatch.py: the message NEVER names the offending
# reference). Correct on... nothing in the error domain (every unresolved
# reference now lacks its value). Its faithful real patch is the pre-patch
# template `"The value of '%s' is not a callable, ..." % (label, cls, model_label)`,
# which renders "The value of 'readonly_fields[1]' is not a callable, ..." for the
# F2P `test_nonexistent_field`, MISSING the "refers to 'nonexistent'" the test now
# asserts — so test_nonexistent_field / test_nonexistent_field_on_inline FAIL; it
# would NOT resolve. Rejection source: CLAUSE-3 (ToSeq(Result()) ==
# diagnostic_message, whose seg_refers()+value term is absent here) AND CLAUSE-4
# (the value-position witness has no value to land at its slot).
_RIVAL_DROP_VALUE = _BASE.replace(_VALUE_SPLICE, "", 1)
assert _BASE.count(_VALUE_SPLICE) == 1, "drift: value splice not unique"

# (3, value-position bug) KEEP the `' refers to '` prose marker but DROP the value
# carrier: the message reads "...refers to '', which is not...". The inserted
# prose appears (so the message is the right LENGTH-ish shape) but the value is
# NOT named. Its faithful real patch would interpolate an EMPTY string at the new
# slot (e.g. `% (label, "", cls, model_label)`), rendering "refers to ''" — still
# missing 'nonexistent' — so the F2P FAILS; it would NOT resolve. Rejection
# source: CLAUSE-4 (the value-position witness `drop(...).take(len(value)) ==
# ToSeq(value)` — with the value absent, the slot holds seg_which_not()'s first
# tokens, not the value) AND CLAUSE-3.
_RIVAL_OMIT_VALUE = _swap(
    _BASE,
    "    result = result + [2]          # \"' refers to '\"  (added value interpolation)\n"
    "    result = result + value        # value  (the offending reference, named)\n",
    "    result = result + [2]          # \"' refers to '\"  (prose kept, value DROPPED)\n",
)

# (4, ordering bug) SWAP the value and class slots: put `cls` where the value
# belongs and `value` where the class belongs. The message still NAMES the value
# (so a naive presence check passes) but at the WRONG interpolation point. Its
# faithful real patch (`% (label, cls_name, field_name, model_label)`) renders
# "refers to 'SongAdmin', ... an attribute of 'nonexistent'" — the value and class
# are transposed — so the F2P (which asserts "refers to 'nonexistent', ... an
# attribute of 'SongAdmin'") FAILS; it would NOT resolve. Rejection source:
# CLAUSE-4 (the value-position witness requires the VALUE — not cls — at the slot
# after intro+label+refers) AND CLAUSE-3 (the whole-message ordering differs).
_RIVAL_SWAP_VALUE_CLS = _swap(
    _BASE,
    "    result = result + value        # value  (the offending reference, named)\n"
    "    result = result + [3]          # \"', which is not a callable, an attribute of '\"\n"
    "    result = result + cls          # class name\n",
    "    result = result + cls          # WRONG: class where the value belongs\n"
    "    result = result + [3]          # \"', which is not a callable, an attribute of '\"\n"
    "    result = result + value        # WRONG: value where the class belongs\n",
)

# (5, control-flow / emptiness discriminator) On the RESOLVE path, return a
# NON-EMPTY list ([88]) instead of []. The reference resolves, so no diagnostic
# should be emitted; this rival emits a spurious one. Its faithful real patch
# would emit a `checks.Error` for a VALID readonly_fields entry — every P2P test
# with a well-formed admin config (e.g. test_readonly_methods, the many
# SystemChecksTestCase configs that expect zero errors) would then report a
# spurious E035 and FAIL; it would NOT resolve. Rejection source: CLAUSE-2
# (`resolves == (len(Result()) == 0)` — a non-empty result on the resolve path
# violates it directly).
_RIVAL_RESOLVE_NONEMPTY = _swap(
    _BASE,
    "        ok = []  # type: List[int]\n        return ok\n",
    "        ok = [88]  # type: List[int]\n        return ok\n",
)


SPEC_TESTS = [
    # ---- positive controls (must VERIFY) ----
    {"id": "pos-one-expr", "kind": "soundness", "expect": "verify",
     "module": _POS_ONE_EXPR,
     "rationale": "structurally-different but CORRECT: the gold's chain of `result = result + "
                  "<piece>` is rewritten as ONE combined expression building the identical "
                  "sequence. `diagnostic_message` is a flat `+` chain (not a recursive fold), so "
                  "the equality is a direct sequence identity the SMT backend discharges without "
                  "an induction lemma. If it fails to verify, the spec is over-fit to one "
                  "concatenation shape => SPEC-TOO-STRONG."},
    {"id": "pos-master-assert", "kind": "soundness", "expect": "verify",
     "module": _POS_MASTER,
     "rationale": "the cheapest impl satisfying the GROUNDED master pin (CLAUSE-3) still "
                  "concatenates the real carriers — there is no executable materialization of the "
                  "@Pure oracle `diagnostic_message` into a list_pred list. Asserting result == "
                  "diagnostic_message(...) right before the error-path return is redundant with the "
                  "gold proof and must verify. Demonstrates the spec is NOT echo-vulnerable: there "
                  "is no WRONG oracle-echo that verifies (else this would be a reject case)."},
    {"id": "admiss-fshape", "kind": "admissibility", "expect": "verify",
     "module": _ADMISS,
     "rationale": "a self-call on the exact F2P-shaped input (label/value/cls/model_label as "
                  "code-point lists, resolves=False — the test_nonexistent_field shape) must "
                  "establish the four Acc(list_pred(.),1/2) preconditions for a normal input. The "
                  "args are fresh full-perm locals so 1/2 is trivially establishable; if the call "
                  "site fails to verify the precondition => PRECOND-TOO-STRONG."},

    # ---- uniqueness rivals (must be REJECTED) ----
    {"id": "frame-mutate-value", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_FRAME,
     "refinement": "no faithful real patch corresponds to this: `_check_readonly_fields_item` "
                   "never mutates the offending reference name (`field_name`, a Python str — "
                   "immutable — passed in by the caller). The rival exists only to test whether "
                   "the read-only (1/2) precondition on `value` can be subverted by writing to it. "
                   "No resolving patch overwrites its reference-name input, so a verifying rival "
                   "here would be a pure verify⇏resolve artifact (vacuous satisfaction via "
                   "self-mutation of the very value the message is supposed to NAME).",
     "rationale": "MANDATORY frame-mutation probe. `value.append(120)` stores through a list held "
                  "at 1/2 (read-only) permission and MUST fail for INSUFFICIENT PERMISSION. "
                  "Rejection source: the PERMISSION SYSTEM (the append needs full perm), not a "
                  "value mismatch — the gold build is kept verbatim after the write. If it "
                  "verified => SPEC-TOO-WEAK (frame protection on the read-only inputs is hollow)."},
    {"id": "drop-value", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_DROP_VALUE,
     "refinement": "omits the offending VALUE entirely — exactly the pre-gold behaviour "
                   "(model_prepatch.py; the pre-patch template names only the position, not the "
                   "value). Its faithful real patch is the pre-patch `\"The value of '%s' is not a "
                   "callable, ...\" % (label, cls, model_label)`, which renders \"The value of "
                   "'readonly_fields[1]' is not a callable, ...\" — MISSING \"refers to "
                   "'nonexistent'\" — so the F2P test_nonexistent_field / "
                   "test_nonexistent_field_on_inline FAIL; it would NOT resolve. This is the bug "
                   "the gold patch fixes.",
     "rationale": "the discriminating bug. Rejection source: CLAUSE-3 (ToSeq(Result()) == "
                  "diagnostic_message — whose seg_refers()+value term is absent here) AND CLAUSE-4 "
                  "(no value to occupy its interpolation slot). If it verified => SPEC-TOO-WEAK "
                  "(the spec would admit the un-fixed message)."},
    {"id": "omit-value-keep-prose", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_OMIT_VALUE,
     "refinement": "keeps the inserted `' refers to '` prose but drops the value carrier, "
                   "rendering \"...refers to '', which is not...\". Its faithful real patch "
                   "interpolates an EMPTY string at the new slot (`% (label, \"\", cls, "
                   "model_label)`), still MISSING 'nonexistent' — so the F2P FAILS; it would NOT "
                   "resolve. Targets the value-position clause specifically (the prose is present "
                   "but the value is not named).",
     "rationale": "Rejection source: CLAUSE-4 (`drop(len(seg_intro)+len(label)+len(seg_refers))."
                  "take(len(value)) == ToSeq(value)` — with the value absent the slot holds "
                  "seg_which_not's tokens, not the value) AND CLAUSE-3. If it verified => "
                  "SPEC-TOO-WEAK (the value-position witness would be satisfiable without the "
                  "value present)."},
    {"id": "swap-value-cls", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_SWAP_VALUE_CLS,
     "refinement": "transposes the value and class slots: the value IS named, but at the class's "
                   "interpolation point and vice-versa. Its faithful real patch "
                   "(`% (label, cls_name, field_name, model_label)`) renders \"refers to "
                   "'SongAdmin', ... an attribute of 'nonexistent'\" — value and class swapped — so "
                   "the F2P (asserting \"refers to 'nonexistent', ... an attribute of 'SongAdmin'\") "
                   "FAILS; it would NOT resolve. Defeats a naive value-PRESENCE check by putting "
                   "the value somewhere wrong.",
     "rationale": "Rejection source: CLAUSE-4 (the value must occupy the slot AFTER "
                  "intro+label+refers — here that slot holds cls) AND CLAUSE-3 (the whole-message "
                  "ordering differs from diagnostic_message). If it verified => SPEC-TOO-WEAK (the "
                  "value-position would be unpinned)."},
    {"id": "discriminator-flip", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_RESOLVE_NONEMPTY,
     "refinement": "emits a NON-EMPTY message on the RESOLVE path (a spurious diagnostic for a "
                   "reference that resolves). Its faithful real patch would return a "
                   "`[checks.Error(...)]` for a VALID readonly_fields entry — every P2P config "
                   "that expects zero errors (the well-formed admin configs in "
                   "SystemChecksTestCase) would then report a spurious E035 and FAIL; it would NOT "
                   "resolve. Exercises the control-flow split, caught as a value defect.",
     "rationale": "Rejection source: CLAUSE-2 (`resolves == (len(Result()) == 0)` — a non-empty "
                  "result on the resolve path violates the emptiness discriminator directly). If "
                  "it verified => SPEC-TOO-WEAK (resolve-path emptiness unpinned)."},
]


# ===========================================================================
# AXIOM LANE (Docker, real `%`-template substitution)
# ===========================================================================
# No @ContractOnly axiom is CONSUMED (the axioms region is documentation-only).
# `diagnostic_message` is an A-REFERENCE: validated equal to the REAL Python
# `%`-formatting of the gold post-patch template (axiom_check.py / G-AX). These
# probes re-run that real-callee equivalence, executing the stdlib `%`-operator
# on the verbatim post-patch template (never scraping source), and also confirm
# the value-position guarantee and the pre-patch differential. apply_gold=True
# because the equivalence describes the post-gold template; the operation is
# stdlib `%` so nothing repo-specific is imported, but apply_gold is kept for
# fidelity with the A-reference's post-patch scope.

# (1) axiom-soundness: deep model `diagnostic_message` (markers expanded to the
# five literal prose pieces per the mapping.md bijection) == real post-patch
# `%`-formatting, over the F2P witnesses + apostrophe/percent/non-ascii/empty
# boundaries + 20000 fuzz; the value occupies its own contiguous slot at offset
# len(SEG_INTRO)+len(label)+len(SEG_REFERS); and the PRE-patch template (the
# function under change before the fix) omits the value (the differential). Any
# mismatch => AXIOM-UNSOUND (deep model unsound).
_AX_DIAGNOSTIC_SOUND = r'''
import random, sys
# The five fixed prose pieces of the post-patch template (mapping.md §2), in the
# order: intro, [label], refers, [value], which_not, [cls], or_attr,
# [model_label], end.
SEG_INTRO     = "The value of '"
SEG_REFERS    = "' refers to '"
SEG_WHICH_NOT = "', which is not a callable, an attribute of '"
SEG_OR_ATTR   = "', or an attribute of '"
SEG_END       = "'."
# The REAL post-patch and pre-patch templates (verbatim from checks.py).
NEW_TEMPLATE = ("The value of '%s' refers to '%s', which is not a callable, "
                "an attribute of '%s', or an attribute of '%s'.")
OLD_TEMPLATE = ("The value of '%s' is not a callable, an attribute of "
                "'%s', or an attribute of '%s'.")

def deep_model(label, value, cls, ml):           # model.py `diagnostic_message`
    return (SEG_INTRO + label + SEG_REFERS + value + SEG_WHICH_NOT
            + cls + SEG_OR_ATTR + ml + SEG_END)
def real_new(label, value, cls, ml):             # the REAL post-patch %-formatting
    return NEW_TEMPLATE % (label, value, cls, ml)
def real_old(label, cls, ml):
    return OLD_TEMPLATE % (label, cls, ml)

def check(label, value, cls, ml):
    """A-reference equivalence + value-position witness (every input)."""
    dm = deep_model(label, value, cls, ml)
    rm = real_new(label, value, cls, ml)
    assert dm == rm, ("A-REFERENCE-UNSOUND diagnostic_message != template %% data on "
        "label=%r value=%r cls=%r ml=%r: model=%r real=%r" % (label, value, cls, ml, dm, rm))
    # value-position (CLAUSE-4): value occupies its own contiguous slot.
    start = len(SEG_INTRO) + len(label) + len(SEG_REFERS)
    assert rm[start:start + len(value)] == value, (
        "value not at its interpolation slot: %r at %d in %r" % (value, start, rm))

def check_differential(label, value, cls, ml):
    """The PRE-patch template must NOT name a DISTINCT value. Only meaningful for
    a value that is not already a substring of the old message's fixed prose OR of
    the other (still-present) dynamic parts — so restricted to curated tokens that
    avoid those coincidences (the random fuzz would otherwise hit short tokens like
    '.' that occur in the constant prose). This mirrors axiom_check.py, which runs
    the differential only on the curated boundary set, never on the fuzz."""
    old = real_old(label, cls, ml)
    assert value and value not in old, (
        "pre-patch message unexpectedly names value %r: %r" % (value, old))

boundary = [
    ("readonly_fields[1]", "nonexistent", "SongAdmin", "admin_checks.Song"),   # F2P
    ("readonly_fields[0]", "i_dont_exist", "CityInline", "admin_checks.City"),  # F2P
    ("readonly_fields[0]", "", "A", "app.M"),       # empty value
    ("", "x", "", ""),                              # empty others
    ("L", "V", "C", "ML"),                          # single chars
    ("l'abel", "va'lue", "C'ls", "m.L'b"),          # apostrophes
    ("a%sb", "c%sd", "e%sf", "g%sh"),               # percent in data
    (chr(233), chr(8226), chr(231), chr(241)),      # non-ascii e-acute, bullet, etc.
]
for (lab, val, cls, ml) in boundary:
    check(lab, val, cls, ml)
# The DIFFERENTIAL (pre-patch omits the value) is meaningful only for a DISTINCT
# multi-char value token that does NOT coincide with the old template's fixed
# prose or its other dynamic parts (mirrors axiom_check.py: the differential runs
# on curated tokens, never on the random fuzz — a short token like '.' occurs in
# the constant prose and would spuriously "appear" in the old message).
differential = [
    ("readonly_fields[1]", "nonexistent", "SongAdmin", "admin_checks.Song"),
    ("readonly_fields[0]", "i_dont_exist", "CityInline", "admin_checks.City"),
    ("readonly_fields[10]", "field_with_underscores", "X", "y.Z"),
    ("label", "UNIQUEVALUETOKEN", "ClassName", "appname.Model"),
]
for (lab, val, cls, ml) in differential:
    check_differential(lab, val, cls, ml)
rng = random.Random(16899)
alphabet = list("abcdefghij ABC_.[]0123456789'%" + chr(233) + chr(8226))
def tok():
    return "".join(rng.choice(alphabet) for _ in range(rng.randint(0, 16)))
for _ in range(20000):
    check(tok(), tok(), tok(), tok())
# The F2P witness must read "...refers to 'nonexistent', which is not...".
w = real_new("readonly_fields[1]", "nonexistent", "SongAdmin", "admin_checks.Song")
assert "refers to 'nonexistent', which is not a callable" in w, w
assert "nonexistent" not in real_old("readonly_fields[1]", "SongAdmin", "admin_checks.Song")
print("AXIOM-SOUND: diagnostic_message deep model == real post-patch %%-formatting on",
      len(boundary), "boundary +", len(differential), "differential + 20000 fuzz; value at its own "
      "slot; pre-patch omits the value.")
sys.exit(0)
'''

# (2) axiom-containment: every callee-input the MODEL can reach lies in the REAL
# operation's domain. The model reaches `NEW_TEMPLATE % (label, value, cls,
# model_label)` with EXACTLY four positional str arguments (the four code-point
# carriers, rendered as str). The post-patch template has EXACTLY four `%s`
# conversions and is total over ANY four str values. So the model's reachable
# inputs (four arbitrary strings) are a subset of the callee's domain — covering
# more (any str) is sound. The probe confirms: (a) the template has exactly four
# `%s` and no other conversion; (b) the substitution succeeds (no TypeError /
# not-enough-args / unsupported-format) for the F2P witnesses + a spread of
# arbitrary 4-tuples — i.e. each reachable callee-input is IN domain.
_AX_CONTAINMENT = r'''
import re, sys
NEW_TEMPLATE = ("The value of '%s' refers to '%s', which is not a callable, "
                "an attribute of '%s', or an attribute of '%s'.")
# (a) the template's conversion specifiers, in order: exactly four bare %s.
specs = re.findall(r"%[^%]?[a-zA-Z]", NEW_TEMPLATE)
assert specs == ["%s", "%s", "%s", "%s"], specs
assert NEW_TEMPLATE.count("%") == 4, ("unexpected %% literal in template", NEW_TEMPLATE)
# (b) the substitution succeeds for every reachable 4-tuple of strings.
probes = [
    ("readonly_fields[1]", "nonexistent", "SongAdmin", "admin_checks.Song"),
    ("readonly_fields[0]", "i_dont_exist", "CityInline", "admin_checks.City"),
    ("", "", "", ""),
    ("a", "b", "c", "d"),
    ("with 'quote'", "with %s percent", "x", "y.Z"),
    (chr(233), chr(8226), chr(231), chr(241)),
]
for t in probes:
    out = NEW_TEMPLATE % t            # raises if any reachable input is out of domain
    # the four args appear in order at their four slots.
    assert out.startswith("The value of '" + t[0] + "' refers to '" + t[1] + "'"), (out, t)
print("CONTAINMENT OK: template has exactly", specs,
      "; substitution total for every probed 4-tuple of strings; model-reachable (four str args) "
      "is a subset of the callee domain (any four str).")
sys.exit(0)
'''

AXIOM_TESTS = [
    {"id": "ax-diagnostic-ref-sound", "axiom": "diagnostic_message",
     "kind": "axiom-soundness", "expect": "holds", "apply_gold": True,
     "probe": _AX_DIAGNOSTIC_SOUND,
     "rationale": "the A-reference deep model `diagnostic_message` (markers expanded to the five "
                  "literal prose pieces per the mapping.md bijection) must equal the REAL "
                  "post-patch `%`-formatting (the stdlib %-operator on the verbatim post-patch "
                  "template) over the F2P witnesses + apostrophe/percent/non-ascii/empty "
                  "boundaries + 20000 fuzz; the value must occupy its own contiguous slot; and the "
                  "pre-patch template must omit the value. Any mismatch => AXIOM-UNSOUND. Executes "
                  "the real `%`-operation; never scrapes source."},
    {"id": "ax-containment", "axiom": "diagnostic_message",
     "kind": "axiom-containment", "expect": "covered", "apply_gold": True,
     "probe": _AX_CONTAINMENT,
     "rationale": "every callee-input the model can reach (the post-patch template applied to "
                  "EXACTLY four str arguments — the four code-point carriers) lies in the real "
                  "substitution's domain (the template has exactly four `%s` and is total over any "
                  "four str). A reachable input outside that domain => AXIOM-TOO-WEAK-FOR-CALLER; "
                  "covering more (any four str) is sound."},
]
