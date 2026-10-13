"""properties.py — PBT falsification manifest for sphinx-doc__sphinx-9673.

NOT a Nagini module: a record of adversarial cases the runner
(`swebench_nagini.pbt`) executes. See the battery-authoring brief (esp. §2 "four
falsification checks" and §4a "Adversarial, NOT mechanical").

This battery is reasoned from THIS spec's defended surface, not stamped out by a
corruption template. Two functions are under spec:

    augment_return_typefield(field_kinds: List[int], return_annotated: bool) -> bool
        Requires(Acc(list_pred(field_kinds), 1/2))           # READ-ONLY input
        Requires(MustTerminate(2))                           # decision REACHED
        Ensures (Acc(list_pred(field_kinds), 1/2))
        Ensures (Result() == (return_annotated
                              and has_return_description(ToSeq(field_kinds))
                              and not has_return_type(ToSeq(field_kinds))))

    name_is_return_key(name, return_key_a, return_key_b) -> bool   # scalars only
        Requires(MustTerminate(6))                           # answer REACHED
        Ensures (Result() == (name == return_key_a or name == return_key_b))

What the spec actually defends, and the attacks it must survive:

  * The load-bearing pin for hunk 1 is the emission equality, in which EVERY
    field code classified as describing the return value counts:
    `has_return_description(kinds)` is a @Pure front-recursive fold returning
    True iff some field has code 2 OR code 3. The discriminating behaviour the
    F2P test observes is exactly that code 3 ALSO counts. A rival that
    recognises only code 2 is the prepatch twin's impl and must be REJECTED (it
    cannot maintain the loop invariant
    `described == has_return_description(ToSeq(field_kinds).drop(i))` when a
    code-3 field is read).

  * The oracle is GROUNDED, not an answer-key marker: `has_return_description` /
    `has_return_type` are @Pure folds OF `field_kinds`, fully unfolded by Viper.
    There is no opaque marker to echo and no executable materialisation of a
    @Pure bool that bypasses the per-field work — the only way to satisfy the
    postcondition is to compute the two predicates over the actual input. So
    there is no "wrong oracle echo that verifies"; instead the ungrounded-oracle
    lane is discharged by an honest cheapest-impl positive control
    (`echo-attempt-honest`) that asserts the built flags equal the @Pure folds.

  * The two equalities are claimed of EVERY run, not only of the runs that
    produce an answer: each routine's precondition demands it reach its decision
    in finitely many steps. This is a second load-bearing pin, and it is the one
    an equality on the answer cannot supply — an equality constrains a Result,
    and a run with no Result satisfies it on that input for free. Three reject
    cases hold it to account (`rival-stall-on-plural`,
    `rival-empty-never-decides`, `rival-name-never-decides`): each classifies
    exactly as the gold does and agrees with gold on every value it answers
    with, yet never reaches a decision on one sub-domain — the discriminating
    plural-spelling one, the empty collection, and one of the two return-name
    carriers respectively. `rival-name-never-decides` is why the obligation is
    stated of the ROUTINE rather than read off a loop: that routine's gold body
    is straight-line, so its control flow forces nothing about a rival's.

  * `field_kinds` is held READ-ONLY (Acc(list_pred(.),1/2), required AND
    ensured). The mandatory attack is FRAME MUTATION (`frame-mutate-kinds`): an
    impl that WRITES to `field_kinds` to satisfy the pin vacuously must fail for
    INSUFFICIENT PERMISSION (a store needs full permission). The gold
    invariants/asserts are kept verbatim so the rejection is attributable solely
    to the write.

  * Hunk 2 (`name_is_return_key`) is a separate defended surface: a name that
    stands for the return value must be skipped. A rival that recognises only
    one of the two return-name carriers (`return_key_a`) is the prepatch twin's
    hunk-2 impl and must be REJECTED by its byte-identical postcondition.

Authoring mechanics: every spec variant is built by REGION-SURGERY (`_swap`)
that edits ONLY inside an `# impl-start`/`# impl-end` region (the nested
invariants of `augment_return_typefield` live there too). `markers.same_spec`
elides every impl span (incl. nested invariants), so a rejection comes from the
POSTCONDITION catching wrong behaviour (or the permission system), never from a
tampered spec. Each `expect:"reject"` rival carries the refinement argument that
its faithful real patch would NOT resolve the F2P
(`test_autodoc_typehints_description_no_undoc`).

There are NO @ContractOnly axioms and NO A-reference deep models in this bundle
(meta.axioms == [], deep_model_references == []); the changed behaviour is pure
integer/sequence classification modelled deeply. AXIOM_TESTS is therefore [].
"""
from pathlib import Path

INSTANCE = "sphinx-doc__sphinx-9673"
FLOAT_ENCODING = None  # meta.json float_encoding is null

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
# Region landmarks — all strictly INSIDE an impl region of model.py.
# ---------------------------------------------------------------------------

# The gold classification branch of augment_return_typefield (impl region).
# Order: return-description (codes 2/3) first, then return-type (code 4).
_GOLD_CLASSIFY = """        if c == 2 or c == 3:
            # a field classified as describing the return value
            described = True
        elif c == 4:
            # a field classified as declaring the return type
            typed = True"""

# The line that reads the (read-only) field code in augment_return_typefield.
_READ_CODE = "        c = field_kinds[i - 1]\n"

# The gold impl body of name_is_return_key (impl region of the 2nd function).
_NAME_IMPL = """    if name == return_key_a or name == return_key_b:
        return True
    return False"""


# ===========================================================================
# POSITIVE CONTROLS (soundness / admissibility) — expect "verify"
# ===========================================================================

# (S1) Structurally-different but CORRECT: the rtype branch (code 4) is checked
# FIRST and the return-description branch (codes 2/3) second. Same backward loop,
# same invariants, same Asserts; only the if/elif order changes. Codes 2/3/4 are
# mutually exclusive per field, so the decision is identical. If this fails to
# verify, the postcondition is over-fit to one branch order => SPEC-TOO-STRONG.
_CLASSIFY_RTYPE_FIRST = """        if c == 4:
            # a field classified as declaring the return type
            typed = True
        elif c == 2 or c == 3:
            # a field classified as describing the return value
            described = True"""
_POS_RTYPE_FIRST = _swap(_BASE, _GOLD_CLASSIFY, _CLASSIFY_RTYPE_FIRST)

# (S2) Structurally-different but CORRECT: the return-description disjunction is
# reordered to `c == 3 or c == 2` (plural spelling tested first). Semantically
# identical (set membership in {2,3}); confirms the spec is not over-fit to the
# literal disjunction order. Backward loop + invariants kept => gold proof holds.
_CLASSIFY_DISJ_SWAP = """        if c == 3 or c == 2:
            # a field classified as describing the return value
            described = True
        elif c == 4:
            # a field classified as declaring the return type
            typed = True"""
_POS_DISJ_SWAP = _swap(_BASE, _GOLD_CLASSIFY, _CLASSIFY_DISJ_SWAP)

# (S3) ECHO-ATTEMPT, HONEST. The oracle is grounded (the @Pure folds over the
# input), so the only way to satisfy the pin is to compute the two predicates.
# This control is the cheapest honest impl: right before the final return, it
# asserts the flags it built EQUAL the @Pure folds over the WHOLE input. That
# assertion is redundant with the gold loop proof and must verify. It
# demonstrates the spec is NOT echo-vulnerable: there is no wrong oracle echo
# that verifies (else this would be a reject case). The assert is placed after
# the loop, before `if return_annotated:`.
_LOOP_TAIL = "        i = i - 1\n    if return_annotated:"
_LOOP_TAIL_ECHO = (
    "        i = i - 1\n"
    "    Assert(described == has_return_description(ToSeq(field_kinds)))\n"
    "    Assert(typed == has_return_type(ToSeq(field_kinds)))\n"
    "    if return_annotated:"
)
_ECHO_HONEST = _swap(_BASE, _LOOP_TAIL, _LOOP_TAIL_ECHO)

# (S4) ADMISSIBILITY. A call on an F2P-shaped field-list — a plural
# return-description field (code 3) plus a param field (code 0), the exact shape
# the F2P test exercises — must establish EVERY precondition of the emission
# decision for that input: the read-only permission Acc(list_pred(.),1/2) AND
# the finiteness obligation, at a level strictly below the caller's. If either
# cannot be established for this normal input => PRECOND-TOO-STRONG.
#
# The call is placed in the OTHER spec-surface routine rather than as a
# self-call, and that placement is load-bearing rather than cosmetic. A routine
# that promises to reach its own answer in finitely many steps may not reach it
# by consulting ITSELF on the arguments it was handed: that is not a witness
# that a normal input is admissible, it is a request to assume the very
# finiteness being discharged. Calling ACROSS the two routines is the
# admissible direction and is what a real caller does.
#
# `Assert(_u)` is what makes the case load-bearing rather than a no-op: the
# F2P-shaped probe (a return documented under the plural spelling, annotated,
# with no declared type) must come back with the entry EMITTED. A reader can
# then tell admissibility from a call whose result says nothing.
#
# The `ToSeq`/`drop` Asserts before the call are proof plumbing only, not extra
# obligations: the classification predicates are front-recursive, so evaluating
# them on a two-element collection needs the two unfolds spelled out down to the
# empty tail. Each one is a fact about the literal `[0, 3]` alone; none mentions
# the routine under test.
_NAME_IMPL_ADMISS = (
    "    probe = [0, 3]  # type: List[int]\n"
    "    Assert(len(ToSeq(probe)) == 2)\n"
    "    Assert(ToSeq(probe)[0] == 0)\n"
    "    Assert(ToSeq(probe).drop(1)[0] == 3)\n"
    "    Assert(len(ToSeq(probe).drop(1).drop(1)) == 0)\n"
    "    Assert(not has_return_type(ToSeq(probe).drop(1).drop(1)))\n"
    "    Assert(has_return_description(ToSeq(probe).drop(1)))\n"
    "    Assert(not has_return_type(ToSeq(probe).drop(1)))\n"
    "    Assert(has_return_description(ToSeq(probe)))\n"
    "    Assert(not has_return_type(ToSeq(probe)))\n"
    "    _u = augment_return_typefield(probe, True)\n"
    "    Assert(_u)\n"
    "    if name == return_key_a or name == return_key_b:\n"
    "        return True\n"
    "    return False"
)
_ADMISS = _swap(_BASE, _NAME_IMPL, _NAME_IMPL_ADMISS)

# Landmarks the finiteness reject lane below splices on.
_IMPL_HEAD = "    described = False\n    typed = False\n    i = len(field_kinds)"
_LOOP_STEP = "        i = i - 1\n"


# ===========================================================================
# UNIQUENESS RIVALS (spec-too-weak probes) — expect "reject"
# ===========================================================================

# (U1) FRAME MUTATION — MANDATORY, the #1 weakness class. `field_kinds` is
# read-only (Acc(list_pred(.),1/2)). This rival WRITES `field_kinds[i-1] = 4`
# (forcing a code-4 "rtype already present" field) before reading it, to try to
# steer the decision on a self-mutated input. Under 1/2 permission a store
# requires FULL permission, so it MUST fail for INSUFFICIENT PERMISSION (not a
# value mismatch). The gold invariants/Asserts are kept verbatim around it, so
# the failure is attributable solely to the write. Rejection source: the
# PERMISSION SYSTEM (the store is unverifiable under 1/2 read-only access).
_FRAME_READ = "        field_kinds[i - 1] = 4\n        c = field_kinds[i - 1]\n"
_RIVAL_FRAME = _swap(_BASE, _READ_CODE, _FRAME_READ)

# (U2) PARTIAL-DOMAIN / THE DISCRIMINATING BUG. This rival recognises only the
# SHORT spelling (code 2) as a return-description and DROPS the plural spelling
# (code 3) — exactly model_prepatch.py and the pre-gold real code
# (`elif parts[0] == 'return':`). On the whole sub-domain of field-lists with no
# code-3 field it agrees with gold; it diverges precisely on the plural-spelling
# input the F2P test feeds. Its faithful real patch is the pre-patch
# augment_descriptions_with_types, which FAILS
# test_autodoc_typehints_description_no_undoc (a function documented with
# `:returns:` must still emit a "Return type:" section) — it would NOT resolve.
# Rejection source: the loop invariant
# `described == has_return_description(ToSeq(field_kinds).drop(i))` cannot be
# maintained at an iteration reading a code-3 field (the fold counts 3, the
# impl does not).
_CLASSIFY_SHORT_ONLY = """        if c == 2:
            # a field classified as describing the return value
            described = True
        elif c == 4:
            # a field classified as declaring the return type
            typed = True"""
_RIVAL_SHORT_ONLY = _swap(_BASE, _GOLD_CLASSIFY, _CLASSIFY_SHORT_ONLY)

# (U3) PARTIAL-DOMAIN, SUB-DOMAIN. Recognises the plural spelling (code 3)
# EVERYWHERE except when it sits at the FIRST element of the field-list (i == 1):
# there the field is ignored. It pins only the sub-domain of field-lists whose
# leading field is not a plural return-description; every other input is handled
# exactly like gold. A faithful real patch of this shape (special-casing the
# first field) would still miss a leading `:returns:` field and so FAIL the F2P
# test — it would NOT resolve. Rejection source: the loop invariant on the FIRST
# (i == 1) iteration cannot close `described == has_return_description(...drop(0))`
# when field_kinds[0] == 3 but `described` is left False.
_CLASSIFY_DROP_FIRST_PLURAL = """        if c == 2 or (c == 3 and i != 1):
            # a field classified as describing the return value
            described = True
        elif c == 4:
            # a field classified as declaring the return type
            typed = True"""
_RIVAL_DROP_FIRST_PLURAL = _swap(_BASE, _GOLD_CLASSIFY, _CLASSIFY_DROP_FIRST_PLURAL)

# (U4) supporting near-miss: treat a return-TYPE field (code 4) as a description.
# A faithful patch doing this would set has_description on an rtype field and
# emit a spurious "Return type:" entry even when one already exists — failing the
# autodoc tests (P2P) that pin the rtype-emission decision. Rejection source: the
# postcondition (Result must follow has_return_description / has_return_type as
# defined; code 4 must set `typed`, not `described`).
_CLASSIFY_4_AS_DESC = """        if c == 2 or c == 3 or c == 4:
            # a field classified as describing the return value
            described = True
        elif c == 99:
            # a field classified as declaring the return type
            typed = True"""
_RIVAL_4_AS_DESC = _swap(_BASE, _GOLD_CLASSIFY, _CLASSIFY_4_AS_DESC)

# (U5) HUNK-2 BUG / control-flow surface of name_is_return_key. This rival
# recognises only ONE of the two return-name carriers (`return_key_a`) and drops
# the other (`return_key_b`) — exactly the prepatch twin's hunk-2 impl. Its
# faithful real patch is the pre-gold back-fill guard, which is the byte that
# model_prepatch.py reverts; it would NOT resolve the hunk-2 behaviour. Rejection
# source: the byte-identical postcondition
# `Result() == (name == return_key_a or name == return_key_b)` — when
# name == return_key_b the impl returns False but the postcondition demands True.
_NAME_SHORT_ONLY = """    if name == return_key_a:
        return True
    return False"""
_RIVAL_NAME_SHORT_ONLY = _swap(_BASE, _NAME_IMPL, _NAME_SHORT_ONLY)

# (U6) NEVER-REACHED DECISION, on the discriminating sub-domain. The
# classification is the gold one — both return-description spellings counted,
# the return-type spelling setting `typed` — and every value this rival DOES
# answer with agrees with gold. It simply does not advance past a field carrying
# the plural return-description spelling, so on precisely the collections the
# F2P test feeds it never reaches the emission decision at all.
#
# This is the counterexample class the emission equality alone cannot see: an
# equality on the answer constrains only the runs that produce one. Its faithful
# real patch classifies both spellings exactly as the gold does and still never
# appends the entry on a `:returns:`-documented function, because the routine
# does not come back — so it would NOT resolve
# test_autodoc_typehints_description_no_undoc, with the F2P failing for a
# missing "Return type:" section just as the pre-gold code does.
#
# Rejection source: the routine's obligation to reach its decision in finitely
# many steps. The per-step measure cannot be maintained across an iteration that
# leaves the counter where it was.
_CLASSIFY_STALL_ON_PLURAL = """        if c == 2 or c == 3:
            # a field classified as describing the return value
            described = True
        elif c == 4:
            # a field classified as declaring the return type
            typed = True
        if c != 3:
            i = i - 1"""
_RIVAL_STALL_ON_PLURAL = _swap(
    _BASE,
    _GOLD_CLASSIFY + "\n" + _LOOP_STEP.rstrip("\n"),
    _CLASSIFY_STALL_ON_PLURAL)

# (U7) NEVER-REACHED DECISION, boundary sub-domain. Same class as U6 taken at
# the empty collection: every non-empty input is handled exactly like gold, and
# on the empty one the routine never reaches a decision. It exists because U6
# stalls INSIDE the fold while this one never enters it, so a spec that pinned
# only the fold's progress would still admit this.
#
# A faithful real patch of this shape hangs the build for any documented object
# whose rendered description carries no fields at all, so it would NOT resolve
# (it fails the F2P and would take the P2P suite with it).
#
# Rejection source: the routine's finiteness obligation, which the fresh loop on
# the empty-collection path cannot discharge.
_IMPL_HEAD_EMPTY_SPIN = """    if len(field_kinds) == 0:
        spin = 0
        while spin >= 0:
            # invariants-start
            Invariant(spin >= 0)
            # invariants-end
            spin = spin + 1
        return False
    described = False
    typed = False
    i = len(field_kinds)"""
_RIVAL_EMPTY_SPIN = _swap(_BASE, _IMPL_HEAD, _IMPL_HEAD_EMPTY_SPIN)

# (U8) NEVER-REACHED DECISION in the OTHER spec-surface routine, whose gold body
# is straight-line: it answers correctly for one return-name carrier and never
# answers at all for the other. Nothing about the gold's own control flow forces
# this closed, which is why the obligation has to be stated of the routine
# rather than read off a loop.
#
# A faithful real patch is the back-fill guard that never returns for one of the
# two names it must recognise, so the back-fill loop does not come back and the
# build produces nothing — it would NOT resolve.
#
# Rejection source: the routine's finiteness obligation.
_NAME_DIVERGE_ON_B = """    if name == return_key_a:
        return True
    if name == return_key_b:
        spin = 0
        while spin >= 0:
            # invariants-start
            Invariant(spin >= 0)
            # invariants-end
            spin = spin + 1
        return True
    return False"""
_RIVAL_NAME_DIVERGE_ON_B = _swap(_BASE, _NAME_IMPL, _NAME_DIVERGE_ON_B)


SPEC_TESTS = [
    # ---- positive controls (must VERIFY) ----
    {"id": "pos-control-rtype-first", "kind": "soundness", "expect": "verify",
     "module": _POS_RTYPE_FIRST,
     "rationale": "structurally-different (rtype branch checked first) but correct "
                  "backward-fold impl; codes 2/3/4 are mutually exclusive per field so the "
                  "decision is identical. Same invariants/Asserts => gold proof holds. If it "
                  "fails to verify, the postcondition is over-fit to one branch order => "
                  "SPEC-TOO-STRONG."},
    {"id": "pos-control-disj-swapped", "kind": "soundness", "expect": "verify",
     "module": _POS_DISJ_SWAP,
     "rationale": "the return-description disjunction reordered to `c == 3 or c == 2` "
                  "(plural tested first) is semantically identical (membership in {2,3}). "
                  "Backward loop + invariants kept verbatim => gold proof valid. If it fails "
                  "=> SPEC-TOO-STRONG (over-fit to literal disjunction order)."},
    {"id": "echo-attempt-honest", "kind": "soundness", "expect": "verify",
     "module": _ECHO_HONEST,
     "rationale": "the oracle is GROUNDED (the @Pure folds over field_kinds), so the only "
                  "way to satisfy the pin is to compute both predicates; there is no "
                  "executable materialisation of a @Pure bool to echo. Asserting the built "
                  "flags equal has_return_description/has_return_type over the whole input is "
                  "redundant with the gold loop proof and must verify. Demonstrates the spec "
                  "is NOT echo-vulnerable (else this would be a reject case)."},
    {"id": "admiss-f2p-shaped", "kind": "admissibility", "expect": "verify",
     "module": _ADMISS,
     "rationale": "a self-call on an F2P-shaped field-list [param=0, plural-return=3] with a "
                  "return annotation must establish the precondition Acc(list_pred(.),1/2) "
                  "(a pure read-only list_pred, no value restriction). If the Requires cannot "
                  "be established for this normal input => PRECOND-TOO-STRONG."},

    # ---- uniqueness rivals (must be REJECTED) ----
    {"id": "frame-mutate-kinds", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_FRAME,
     "refinement": "no faithful real patch corresponds to this: "
                   "augment_descriptions_with_types only READS its field_list to classify "
                   "leading tokens; it never rewrites a field's leading token. The rival "
                   "exists solely to test whether the read-only (1/2) precondition can be "
                   "subverted by writing to field_kinds. There is no resolving patch that "
                   "overwrites its input field codes, so a verifying rival here would be a "
                   "pure verify⇏resolve artifact (vacuous satisfaction via self-mutation).",
     "rationale": "MANDATORY frame-mutation probe. `field_kinds[i-1] = 4` writes through a "
                  "1/2 (read-only) reference and MUST fail for insufficient permission. "
                  "Rejection source: the PERMISSION SYSTEM (a store needs full perm), not a "
                  "value mismatch; the gold invariants/Asserts are kept verbatim. If it "
                  "verified => SPEC-TOO-WEAK (frame protection hollow)."},
    {"id": "rival-short-spelling-only", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_SHORT_ONLY,
     "refinement": "recognises only the SHORT return-description spelling (code 2) and "
                   "ignores the plural (code 3) — exactly the pre-gold real code "
                   "`elif parts[0] == 'return':` and model_prepatch.py. Its faithful real "
                   "patch is the pre-patch augment_descriptions_with_types, which FAILS the "
                   "F2P test_autodoc_typehints_description_no_undoc (a `:returns:`-documented "
                   "function must still emit a 'Return type:' section) — it would NOT resolve.",
     "rationale": "the discriminating bug + partial-domain. Rejection source: the loop "
                  "invariant `described == has_return_description(ToSeq(field_kinds).drop(i))` "
                  "cannot be maintained at an iteration reading a code-3 field (the @Pure fold "
                  "counts 3, the impl does not). If it verified => SPEC-TOO-WEAK (admits the "
                  "synonym bug)."},
    {"id": "rival-drop-first-plural", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_DROP_FIRST_PLURAL,
     "refinement": "recognises the plural spelling (code 3) EVERYWHERE except at the first "
                   "field (i == 1), which it ignores. A faithful real patch special-casing the "
                   "first field would still miss a LEADING `:returns:` field and so FAIL the "
                   "F2P test (which pins the synonym regardless of field position) — it would "
                   "NOT resolve.",
     "rationale": "partial-domain (leading-field sub-domain). Rejection source: on the FIRST "
                  "iteration (i == 1) the invariant `described == "
                  "has_return_description(ToSeq(field_kinds).drop(0))` cannot close when "
                  "field_kinds[0] == 3 but `described` is left False. If it verified => "
                  "SPEC-TOO-WEAK (domain-incomplete)."},
    {"id": "rival-rtype-as-description", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_4_AS_DESC,
     "refinement": "treats a return-TYPE field (code 4) as a return-description and never "
                   "sets `typed`. A faithful real patch doing this would add a spurious "
                   "'Return type:' entry even when an rtype field already exists, failing the "
                   "autodoc P2P tests that pin the rtype-emission decision — it would NOT "
                   "resolve.",
     "rationale": "supporting near-miss with a real refinement: misclassifies code 4. "
                  "Rejection source: the postcondition (code 4 must drive has_return_type, not "
                  "has_return_description); the loop invariants on `described`/`typed` both "
                  "break. If it verified => SPEC-TOO-WEAK."},
    {"id": "rival-name-short-only", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_NAME_SHORT_ONLY,
     "refinement": "name_is_return_key recognising only ONE of the two return-name "
                   "carriers (`return_key_a`) is exactly the pre-gold hunk-2 guard that "
                   "model_prepatch.py reverts; it would NOT resolve the hunk-2 behaviour "
                   "(skip any name that stands for the return value).",
     "rationale": "hunk-2 control-flow surface. Rejection source: the byte-identical "
                  "postcondition `Result() == (name == return_key_a or name == "
                  "return_key_b)` — when name == return_key_b the impl returns False while "
                  "the postcondition demands True. If it verified => SPEC-TOO-WEAK (admits the "
                  "hunk-2 bug)."},
    {"id": "rival-stall-on-plural", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_STALL_ON_PLURAL,
     "refinement": "classifies BOTH return-description spellings exactly as the gold does "
                   "and agrees with gold on every value it answers with, but does not "
                   "advance past a field carrying the plural spelling, so on precisely the "
                   "collections the F2P test feeds it never reaches the emission decision. "
                   "Its faithful real patch appends no 'Return type:' section for a "
                   "`:returns:`-documented function because the routine does not come back, "
                   "so it FAILS test_autodoc_typehints_description_no_undoc exactly as the "
                   "pre-gold code does — it would NOT resolve.",
     "rationale": "the class the emission equality alone cannot see: an equality on the "
                  "answer constrains only the runs that produce one. Rejection source: the "
                  "routine's obligation to reach its decision in finitely many steps — the "
                  "per-step measure cannot be maintained across an iteration that leaves the "
                  "counter where it was. If it verified => SPEC-TOO-WEAK (the emission "
                  "decision would be claimed only of the runs that happen to reach it)."},
    {"id": "rival-empty-never-decides", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_EMPTY_SPIN,
     "refinement": "handles every non-empty collection exactly like gold and never reaches a "
                   "decision on the empty one. A faithful real patch of this shape hangs the "
                   "build for any documented object whose rendered description carries no "
                   "fields at all, so it would NOT resolve (it fails the F2P and takes the "
                   "P2P suite with it).",
     "rationale": "same never-reached-decision class as rival-stall-on-plural taken at the "
                  "BOUNDARY: that one stalls inside the fold, this one never enters it, so a "
                  "spec pinning only the fold's progress would still admit this. Rejection "
                  "source: the routine's finiteness obligation, which the fresh loop on the "
                  "empty-collection path cannot discharge. If it verified => SPEC-TOO-WEAK."},
    {"id": "rival-name-never-decides", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_NAME_DIVERGE_ON_B,
     "refinement": "answers correctly for one return-name carrier and never answers at all "
                   "for the other. A faithful real patch is the back-fill guard that does not "
                   "return for one of the two names it must recognise, so the back-fill loop "
                   "does not come back and the build produces nothing — it would NOT resolve.",
     "rationale": "the never-reached-decision class in the routine whose GOLD body is "
                  "straight-line and loop-free. Nothing about the gold's own control flow "
                  "forces this closed, which is why the obligation has to be stated of the "
                  "routine rather than read off a loop; this case is what holds that "
                  "statement to account. Rejection source: that routine's finiteness "
                  "obligation. If it verified => SPEC-TOO-WEAK (a spec-surface routine whose "
                  "answer is claimed only of the runs that produce one)."},
]

# ===========================================================================
# AXIOM LANE — none. meta.axioms == [], deep_model_references == []. The entire
# changed behaviour is pure integer/sequence classification modelled deeply
# (has_return_description / has_return_type front-recursive folds); no
# @ContractOnly axiom is consumed and no A-reference deep model is validated
# against a real library callee. axiom_check.py is a self-contained structural
# cross-check (stdlib-only), not an in-container callee execution. So there is no
# axiom-soundness / axiom-containment obligation to probe.
# ===========================================================================
AXIOM_TESTS = []
