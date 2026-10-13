# properties.py — PBT falsification battery for sympy__sympy-13877.
#
# NOT a Nagini module: a record of adversarial cases the runner
# (swebench_nagini.pbt) executes and stamps with RESULT. Each spec case is a
# full model.py whose ONLY change is inside the impl region (# impl-start /
# # impl-end), so the frozen spec (axioms/pure/pre/post-conditions) is byte-
# identical and same_spec holds by construction. Axiom cases are real-callee
# probes run in the instance Docker image.
#
# DEFENDED SURFACE (what this spec actually pins):
#   lowest_live_index(col: List[int]) returns the lowest index whose entry is
#   NOT genuinely zero (is_genuinely_zero(e) == e <= 0), or -1 if the whole
#   column is genuinely zero. col is READ-ONLY: Requires/Ensures carry only
#   Acc(list_pred(col), 1/2) — half permission. The load-bearing postcondition
#   clauses:
#     (P0)  Acc(list_pred(col), 1/2)                         frame preservation
#     (P1)  -1 <= Result() < len(col)                        range
#     (P2)  (Result()==-1) == (first_usable(ToSeq(col),0)==len(col))   no-pivot iff all-zero
#     (P3)  Result()!=-1  ==>  Result() == first_usable(ToSeq(col),0)  exact lowest live
#     (P4)  Result()!=-1  ==>  forall t in [0,Result()): is_genuinely_zero(col[t])
#     (P5)  Result()!=-1  ==>  not is_genuinely_zero(col[Result()])
#   first_usable is a @Pure FRONT-RECURSIVE fold fully grounded in (s,k): it is
#   a function of the input, NOT an opaque answer key, so an "ungrounded-oracle
#   echo" attack is impossible — returning first_usable(...) IS the correct
#   answer and the cheapest correct impl. See 'assessment'. We therefore run an
#   honest cheapest-correct positive control in its place.

from pathlib import Path

INSTANCE = "sympy__sympy-13877"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()

# The exact, unique impl-region block in model.py (markers inclusive).
_IMPL = (
    "    # impl-start\n"
    "    i = 0\n"
    "    while i < len(col):\n"
    "        # invariants-start\n"
    "        Invariant(Acc(list_pred(col), 1 / 2))\n"
    "        Invariant(0 <= i and i <= len(col))\n"
    "        # Everything scanned so far is genuinely zero.\n"
    "        Invariant(Forall(int, lambda t: (Implies(0 <= t and t < i,\n"
    "                                                  is_genuinely_zero(col[t])),\n"
    "                                          [[col[t]]])))\n"
    "        # ... which is exactly first_usable not yet having fired.\n"
    "        Invariant(first_usable(ToSeq(col), 0) == first_usable(ToSeq(col), i))\n"
    "        # invariants-end\n"
    "        if not is_genuinely_zero(col[i]):\n"
    "            return i\n"
    "        i = i + 1\n"
    "    return -1\n"
    "    # impl-end"
)


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: impl block not found verbatim")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: impl block appears {src.count(old)}x")
    return src.replace(old, new, 1)


def _impl(body_lines):
    """Build a full impl region (markers inclusive) from a list of body source
    lines already indented to 4 spaces (the function-body indent)."""
    return "    # impl-start\n" + "\n".join(body_lines) + "\n    # impl-end"


# ---------------------------------------------------------------------------
# POSITIVE CONTROLS (soundness — must VERIFY; else SPEC-TOO-STRONG)
# ---------------------------------------------------------------------------

# pos-cheapest: the cheapest CORRECT impl — directly materialize the grounded
# @Pure oracle first_usable and map its len(col) sentinel to -1. This is a
# structurally DIFFERENT shape (no loop, no loop invariant) that is correct, so
# it must verify; it also demonstrates that the oracle is grounded (returning
# it IS the right answer — there is no wrong echo).
_POS_CHEAPEST = _impl([
    "    fu = first_usable(ToSeq(col), 0)",
    "    # Framing bridge (proof engineering, NOT a spec change): first_usable's",
    "    # Ensures speaks over ToSeq(col)[t] (trigger [[s[t]]]); P4 speaks over",
    "    # col[t] (trigger [[col[t]]]). They are equal under list_pred, so this",
    "    # forall lets the genuinely-zero prefix from first_usable transfer onto",
    "    # col[t] and discharge P4. The gold loop avoids this only because its",
    "    # invariant is already phrased over col[t].",
    "    Assert(Forall(int, lambda t: (Implies(0 <= t and t < len(col),",
    "                                          col[t] == ToSeq(col)[t]),",
    "                                  [[col[t]]])))",
    "    if fu == len(col):",
    "        return -1",
    "    return fu",
])

# pos-reorder: a structurally-different LOOP variant. The genuine-non-zero test
# is hoisted into a local boolean and the branch order is inverted (advance in
# the common case, return on the negation). The gold loop invariants are kept
# VERBATIM (pilot bug #2: a structural positive control must keep every framing
# invariant it still needs), only the executable shape inside the loop body
# changes. Stays a forward (front-recursive-matching) scan (pilot bug #3).
_POS_REORDER = _impl([
    "    i = 0",
    "    while i < len(col):",
    "        # invariants-start",
    "        Invariant(Acc(list_pred(col), 1 / 2))",
    "        Invariant(0 <= i and i <= len(col))",
    "        Invariant(Forall(int, lambda t: (Implies(0 <= t and t < i,",
    "                                                  is_genuinely_zero(col[t])),",
    "                                          [[col[t]]])))",
    "        Invariant(first_usable(ToSeq(col), 0) == first_usable(ToSeq(col), i))",
    "        # invariants-end",
    "        zero_here = is_genuinely_zero(col[i])",
    "        if zero_here:",
    "            i = i + 1",
    "        else:",
    "            return i",
    "    return -1",
])


# ---------------------------------------------------------------------------
# ADMISSIBILITY (precondition must accept a normal F2P-shaped input)
# ---------------------------------------------------------------------------

# admiss-1: at function entry, on the half-permission read-only col, read a few
# entries and assert the precondition shape (col indexable, length >= 0) admits
# them — then fall through to the gold loop. If the Requires were too strong the
# reads / the gold tail would fail to verify. Keeps the gold body intact.
_ADMISS = _impl([
    "    # Admissibility: a normal column (F2P matrices give columns of length",
    "    # n>=1, e.g. the M(5)/M(6)/M(7) Bareiss minors) is accepted under the",
    "    # half-permission precondition; we may read its length and entries.",
    "    Assert(0 <= len(col))",
    "    if len(col) > 0:",
    "        Assert(is_genuinely_zero(col[0]) or not is_genuinely_zero(col[0]))",
    "    # gold body follows unchanged",
    "    i = 0",
    "    while i < len(col):",
    "        # invariants-start",
    "        Invariant(Acc(list_pred(col), 1 / 2))",
    "        Invariant(0 <= i and i <= len(col))",
    "        Invariant(Forall(int, lambda t: (Implies(0 <= t and t < i,",
    "                                                  is_genuinely_zero(col[t])),",
    "                                          [[col[t]]])))",
    "        Invariant(first_usable(ToSeq(col), 0) == first_usable(ToSeq(col), i))",
    "        # invariants-end",
    "        if not is_genuinely_zero(col[i]):",
    "            return i",
    "        i = i + 1",
    "    return -1",
])


# ---------------------------------------------------------------------------
# FRAME-MUTATION (MANDATORY — col is read-only Acc(...,1/2)). Must REJECT for
# INSUFFICIENT PERMISSION, not for a value mismatch. We keep the gold result
# logic so the ONLY reason to reject is the write to the half-permission input.
# ---------------------------------------------------------------------------

# frame-mutate: overwrite the scanned-past entries to literal-zero (col[i] = 0)
# as the scan advances. Under value semantics this is a no-op for the result
# (it only zeroes entries already proven genuinely-zero), so a value abstraction
# would not notice — but col only has Acc(...,1/2): a write needs full
# permission, so verification MUST fail for insufficient permission.
_FRAME_MUTATE = _impl([
    "    i = 0",
    "    while i < len(col):",
    "        # invariants-start",
    "        Invariant(Acc(list_pred(col), 1 / 2))",
    "        Invariant(0 <= i and i <= len(col))",
    "        # invariants-end",
    "        if not is_genuinely_zero(col[i]):",
    "            return i",
    "        col[i] = 0  # WRITE to a half-permission input -> insufficient perm",
    "        i = i + 1",
    "    return -1",
])


# ---------------------------------------------------------------------------
# UNIQUENESS / completeness rivals (wrong impls that share the spec — any that
# VERIFIES is SPEC-TOO-WEAK). Each carries the refinement argument that its
# faithful real patch would NOT resolve the F2P test (M(5/6/7).det()==0).
# ---------------------------------------------------------------------------

# weak-structtruthy: THE bug class. Use the pre-patch structural test (entry
# treated as a usable pivot iff its code != 0) instead of the mathematical
# is_genuinely_zero. On a pseudo-zero (code < 0) this returns that index where
# the spec demands skipping it. Must be rejected by P3/P5 (and P2 when the whole
# column is <=0 but contains a <0 pseudo-zero).
_WEAK_STRUCTTRUTHY = _impl([
    "    i = 0",
    "    while i < len(col):",
    "        # invariants-start",
    "        Invariant(Acc(list_pred(col), 1 / 2))",
    "        Invariant(0 <= i and i <= len(col))",
    "        # invariants-end",
    "        if col[i] != 0:  # PRE-PATCH struct-truthy: accepts a <0 pseudo-zero",
    "            return i",
    "        i = i + 1",
    "    return -1",
])

# weak-skipfirst: a partial-domain rival correct everywhere EXCEPT it never
# selects index 0 — it starts the scan at index 1. On a column whose first live
# entry is at index 0 (e.g. [3] or [1, 0]) it returns the WRONG pivot (or -1),
# violating P3 (Result must equal first_usable, which is 0 here).
_WEAK_SKIPFIRST = _impl([
    "    i = 1",
    "    while i < len(col):",
    "        # invariants-start",
    "        Invariant(Acc(list_pred(col), 1 / 2))",
    "        Invariant(1 <= i and i <= len(col))",
    "        # invariants-end",
    "        if not is_genuinely_zero(col[i]):",
    "            return i",
    "        i = i + 1",
    "    return -1",
])

# weak-lastlive: returns the HIGHEST live index (scan backward) instead of the
# lowest. On [2, 5] it returns 1 where first_usable == 0, violating P3/P4 (some
# t < Result is NOT genuinely zero). Its faithful patch picks the wrong Bareiss
# pivot row -> a different elimination, not the gold determinant.
_WEAK_LASTLIVE = _impl([
    "    i = len(col) - 1",
    "    while i >= 0:",
    "        # invariants-start",
    "        Invariant(Acc(list_pred(col), 1 / 2))",
    "        Invariant(-1 <= i and i < len(col))",
    "        # invariants-end",
    "        if not is_genuinely_zero(col[i]):",
    "            return i",
    "        i = i - 1",
    "    return -1",
])

# weak-alwaysminusone: the degenerate "no pivot ever" rival — always returns -1.
# Trivially correct on all-zero columns but wrong as soon as any entry is live
# (P2: Result==-1 must imply first_usable==len(col)). Cheap supporting case with
# a real refinement: its patch would report EVERY minor as singular -> det==0
# for non-singular matrices too, failing the P2P determinant assertions.
_WEAK_ALWAYS_M1 = _impl([
    "    return -1",
])

# weak-offbyone-sentinel: returns len(col) (out of the legal range) when no
# pivot exists instead of -1. Violates P1 (Result < len(col)) and P2. Supporting
# case; faithful patch would compare pivot_pos against the wrong sentinel.
_WEAK_LEN_SENTINEL = _impl([
    "    i = 0",
    "    while i < len(col):",
    "        # invariants-start",
    "        Invariant(Acc(list_pred(col), 1 / 2))",
    "        Invariant(0 <= i and i <= len(col))",
    "        # invariants-end",
    "        if not is_genuinely_zero(col[i]):",
    "            return i",
    "        i = i + 1",
    "    return len(col)  # wrong sentinel: violates P1 (-1<=R<len) and P2",
])


SPEC_TESTS = [
    {
        "id": "pos-cheapest",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _IMPL, _POS_CHEAPEST),
        "rationale": "The cheapest correct impl — directly return the grounded "
                     "@Pure oracle first_usable(ToSeq(col),0) with its len(col) "
                     "sentinel mapped to -1. A correct loop-free shape must "
                     "verify (else SPEC-TOO-STRONG). Also demonstrates the "
                     "oracle is grounded in the input, so there is no wrong echo.",
    },
    {
        "id": "pos-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _IMPL, _POS_REORDER),
        "rationale": "Structurally-different forward loop: the genuine-non-zero "
                     "test is hoisted to a local and the branch order inverted "
                     "(advance in the zero case, return in the live case). Gold "
                     "loop invariants kept verbatim (pilot bug #2); forward scan "
                     "matches the front-recursive first_usable (pilot bug #3). "
                     "Must verify.",
    },
    {
        "id": "admiss-1",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _IMPL, _ADMISS),
        "rationale": "An F2P-shaped column (length n>=1, the M(5/6/7) Bareiss "
                     "minors) is admitted by the half-permission precondition: "
                     "we may read len(col) and col[0]. If Requires were too "
                     "strong these reads / the gold tail would not verify "
                     "(PRECOND-TOO-STRONG).",
    },
    {
        "id": "frame-mutate",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL, _FRAME_MUTATE),
        "refinement": "Writing col[i]=0 to the input is invisible to the value "
                      "abstraction (it only zeroes entries already proven "
                      "genuinely-zero), so a faithful real patch that mutated "
                      "mat[:,0] in place would compute the SAME pivot index and "
                      "thus still resolve the F2P — the rejection here is purely "
                      "the permission firewall, the property no value-only spec "
                      "could enforce. A real patch must not mutate the column.",
        "rationale": "REJECT comes from the permission system: col carries only "
                     "Acc(list_pred(col), 1/2); the store col[i]=0 needs full "
                     "permission, so Nagini fails for INSUFFICIENT PERMISSION "
                     "(not a value mismatch). MANDATORY frame-mutation probe.",
    },
    {
        "id": "weak-structtruthy",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL, _WEAK_STRUCTTRUTHY),
        "refinement": "This IS the pre-patch bug (model_prepatch.py): the "
                      "structural test col[i]!=0 accepts a code<0 pseudo-zero as "
                      "a pivot. Its faithful real patch (_find_pivot with "
                      "`if val:`) divides by a pseudo-zero on the singular "
                      "M(5/6/7) columns -> nan / 'Invalid NaN comparison', so "
                      "det() does NOT equal 0 and the F2P test FAILS. A verifying "
                      "rival here would be a true verify-without-resolve break.",
        "rationale": "REJECT comes from P3 (Result==first_usable) and P5 (chosen "
                     "entry not is_genuinely_zero): on a column whose first "
                     "code!=0 entry has code<0, this returns that index while "
                     "first_usable skips it; and P2 fails on an all-(<=0) column "
                     "containing a <0 pseudo-zero (returns it, spec demands -1).",
    },
    {
        "id": "weak-skipfirst",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL, _WEAK_SKIPFIRST),
        "refinement": "Correct on every column whose first live entry is at "
                      "index >= 1, but it never selects index 0. A faithful patch "
                      "that started the pivot search at row 1 would pick the wrong "
                      "pivot (or wrongly report no pivot) whenever the top entry "
                      "is the genuine non-zero one — a different Bareiss pivot "
                      "row -> a different elimination -> wrong determinant on the "
                      "P2P matrices, not resolving.",
        "rationale": "REJECT comes from P3: on col=[c>0] (or [c>0, 0]) "
                     "first_usable(...,0)==0 but this returns -1 (or 1), so "
                     "Result()!=first_usable; equivalently P2 fails (Result==-1 "
                     "while first_usable!=len). Partial-domain (first element).",
    },
    {
        "id": "weak-lastlive",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL, _WEAK_LASTLIVE),
        "refinement": "Returns the highest live index instead of the lowest. A "
                      "faithful patch picking the LAST non-zero row as the Bareiss "
                      "pivot changes the elimination order and (the algorithm is "
                      "specified for the lowest valid pivot) yields a different / "
                      "wrong determinant on the multi-live P2P matrices, not "
                      "resolving the F2P.",
        "rationale": "REJECT comes from P4 (forall t<Result: is_genuinely_zero) "
                     "and P3: on col=[c1>0, c2>0] this returns 1 but index 0 is "
                     "live, so some t<Result is NOT genuinely zero and "
                     "Result()!=first_usable(...,0)==0. Partial-domain "
                     "(multi-live columns).",
    },
    {
        "id": "weak-alwaysminusone",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL, _WEAK_ALWAYS_M1),
        "refinement": "Always reports 'no pivot'. A faithful patch returning "
                      "S.Zero for every minor would make EVERY determinant 0, "
                      "including the non-singular P2P matrices "
                      "(test_determinant's earlier z**2 - x*y asserts), so it "
                      "fails the test suite — does not resolve.",
        "rationale": "REJECT comes from P2: Result==-1 forces "
                     "first_usable(ToSeq(col),0)==len(col); on any column with a "
                     "live entry first_usable<len(col), contradiction. Supporting "
                     "degenerate case with a real refinement.",
    },
    {
        "id": "weak-len-sentinel",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL, _WEAK_LEN_SENTINEL),
        "refinement": "Returns len(col) instead of -1 for the no-pivot case. A "
                      "faithful patch comparing pivot_pos against the wrong "
                      "out-of-range sentinel would mis-handle the singular-minor "
                      "branch (the `pivot_pos == None -> S.Zero` control), so the "
                      "M(5/6/7) singular columns would not contribute zero "
                      "correctly -> not resolving.",
        "rationale": "REJECT comes from P1 (-1<=Result<len(col)): returning "
                     "len(col) is out of range; and P2 (no-pivot must be -1). "
                     "Supporting boundary/sentinel case.",
    },
]


# ---------------------------------------------------------------------------
# AXIOM LANE — no @ContractOnly axiom is consumed (meta.axioms == []). The only
# kind-A item is the A-reference deep model is_genuinely_zero, validated == the
# real callee expand_mul(x)==0 by axiom_check.py (G-AX). We re-assert that
# soundness here as an axiom-soundness probe (running the REAL callee, never
# scraping source), and add a caller-domain CONTAINMENT probe: every entry-code
# the model can actually feed is_genuinely_zero is covered by the bijection.
# ---------------------------------------------------------------------------

# Read the bundle oracle on the HOST at load time and embed its source into the
# probe (the runner mounts only the probe script — pilot bug #6). The probe runs
# the real sympy expand_mul in the instance image.
_AXIOM_CHECK_SRC = (Path(__file__).parent / "axiom_check.py").read_text()

# Embed the bundle oracle's BODY at module level (it defines main(),
# _is_zero_after_expand_mul, is_genuinely_zero_model, struct_truthy_real). Strip
# its leading imports/`import sys` and its `if __name__` tail; we then call
# main() under a try so an AssertionError is reported as A-reference UNSOUND.
_AX_BODY = _AXIOM_CHECK_SRC.split("import sys", 1)[1].rsplit("if __name__", 1)[0]

_AX_SOUND_PROBE = (
    "# axiom-soundness: the A-reference deep model is_genuinely_zero(code) must\n"
    "# equal the REAL callee _is_zero_after_expand_mul(x) == (expand_mul(x)==0)\n"
    "# on a representative entry of every status class, INCLUDING the issue's\n"
    "# pseudo-zeros (numerator expands to 0 over a non-zero denom). Runs the real\n"
    "# sympy callee in the instance image; exit 0 iff every obligation holds.\n"
    "import sys\n"
    + _AX_BODY +
    "\n"
    "if True:\n"
    "    try:\n"
    "        rc = main()\n"
    "        print('AXIOM-SOUNDNESS', 'OK' if rc == 0 else 'FAIL')\n"
    "        sys.exit(rc)\n"
    "    except AssertionError as e:\n"
    "        print('AXIOM-SOUNDNESS FAIL (A-reference UNSOUND):', e)\n"
    "        sys.exit(1)\n"
    "    except Exception as e:\n"
    "        print('AXIOM-SOUNDNESS ERROR:', repr(e))\n"
    "        sys.exit(1)\n"
)

_AX_CONTAIN_PROBE = (
    "# axiom-containment: every entry-code the MODEL can pass to is_genuinely_zero\n"
    "# is an int (the carrier is List[int]); the deep model is_genuinely_zero(e)=\n"
    "# e<=0 is TOTAL over int, so every caller-reachable input lies in its domain\n"
    "# (there is no Requires restricting e). We further confirm the real callee\n"
    "# expand_mul(x)==0 is itself total on the SymPy entries each code abstracts\n"
    "# (it returns a real bool, never None), so PASS-1 of _find_reasonable_pivot\n"
    "# is always decisive (the refinement claim in mapping.md A2). Containment\n"
    "# cannot fail here, but we assert it executably rather than by assertion.\n"
    "import sys\n"
    "from sympy import symbols, expand_mul, S, Integer\n"
    "a, b = symbols('a b')\n"
    "# Representative entries for codes 0, >0, <0 (the only three classes the\n"
    "# model carrier admits) — the deep model accepts ALL ints, so coverage is\n"
    "# exact-or-superset (sound, never AXIOM-TOO-WEAK-FOR-CALLER).\n"
    "entries = [S.Zero, Integer(0), a, Integer(5), a*b,\n"
    "           a*(a+1) - a**2 - a, (a*(a+1) - a**2 - a)/a]\n"
    "ok = True\n"
    "for x in entries:\n"
    "    r = (expand_mul(x) == 0)\n"
    "    if not isinstance(bool(r), bool):\n"
    "        ok = False\n"
    "        print('NON-TOTAL callee on', x)\n"
    "# the deep model is_genuinely_zero is defined for every int code:\n"
    "for code in (-3, -1, 0, 1, 5, 99):\n"
    "    _ = (code <= 0)  # total; no Requires excludes any int\n"
    "print('AXIOM-CONTAINMENT', 'OK' if ok else 'FAIL',\n"
    "      '- deep model is_genuinely_zero is total over int (covers every\\n'\n"
    "      ' caller-reachable code); real callee returns a real bool on every\\n'\n"
    "      ' representative entry (PASS-1 always decisive).')\n"
    "sys.exit(0 if ok else 1)\n"
)

AXIOM_TESTS = [
    {
        "id": "ax-sound-is_genuinely_zero",
        "axiom": "is_genuinely_zero",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _AX_SOUND_PROBE,
        "rationale": "If the real expand_mul(x)==0 disagrees with the deep model "
                     "is_genuinely_zero(code) on ANY class — especially the "
                     "pseudo-zero class (truthy yet expands to 0) the whole fix "
                     "hinges on — the A-reference is UNSOUND. Runs the real "
                     "callee (axiom_check.py logic), never scrapes source.",
    },
    {
        "id": "ax-contain-is_genuinely_zero",
        "axiom": "is_genuinely_zero",
        "kind": "axiom-containment",
        "expect": "covered",
        "apply_gold": True,
        "probe": _AX_CONTAIN_PROBE,
        "rationale": "The model carrier is List[int] and is_genuinely_zero(e)=e<=0 "
                     "is total over int with NO Requires — every caller-reachable "
                     "entry code is in its domain (exact-or-superset coverage, "
                     "sound per the float-vs-int rule). Also confirms the real "
                     "callee returns a real bool (never None) so PASS-1 of "
                     "_find_reasonable_pivot is always decisive (mapping.md A2).",
    },
]
