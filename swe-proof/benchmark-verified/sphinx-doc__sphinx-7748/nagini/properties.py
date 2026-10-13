"""properties.py — PBT falsification manifest for sphinx-doc__sphinx-7748.

NOT a Nagini module: a record of adversarial cases the runner
(`swebench_nagini.pbt`) executes. See the battery-authoring brief (esp. §2 "four
falsification checks" and §4a "Adversarial, NOT mechanical").

This battery is reasoned from THIS spec's defended surface, not stamped out by a
corruption template.

THE DEFENDED SURFACE
--------------------
`gather_signatures(cont: List[int], val: List[int]) -> List[int]` models the
gold change to `DocstringSignatureMixin._find_signature` + `format_signature`:
gather the per-line signature values of EVERY line from the top of a
documentation block up to AND INCLUDING the first terminating (non-continued)
line, then render them in order. A line is *open* (carries over) iff its
continuation flag is non-zero (`cont[k] != 0`, the real `line.endswith('\\')`).

Both inputs are READ-ONLY: `Acc(list_pred(cont),1/2)` and
`Acc(list_pred(val),1/2)`, required AND ensured at fractional permission. The
gatherer mutates neither stream (the real loop only reads the doclines).

The LOAD-BEARING postcondition has three clauses, all GROUNDED in the input
args (no opaque oracle — `run_len`/`collected` are @Pure front-recursive folds
spelled out over `cont`/`val` and fully unfolded by Viper):

    Ensures(ToSeq(Result()) == collected(ToSeq(cont), ToSeq(val)))   # L103 whole seq
    Ensures(len(Result()) == run_len(ToSeq(cont)))                   # L106 count
    Ensures(len(val) > 0 and len(Result()) >= 1 and Result()[0] == val[0])  # L108 head

The discriminating behaviour: a run whose leading line is open (cont[0]!=0)
must yield >= 2 signatures (run_len >= 2), not just the first. The pre-patch
consulted only doclines[0] and recorded ONE signature; model_prepatch.py
reproduces that as `result = [val[0]]` and fails L103/L106 for any open leading
run. The F2P fixture (class E: two __init__ signature lines, the first
continued) is exactly this case (gold renders 2, pre-patch renders 1).

ATTACKS THIS SPEC MUST SURVIVE
------------------------------
  * FRAME-MUTATION (MANDATORY — BOTH inputs are Acc(...,1/2) read-only):
    `frame-mutate-cont` writes through `cont` before reading it;
    `frame-mutate-val` writes through `val`. Both must fail for INSUFFICIENT
    PERMISSION (gold invariants/asserts kept verbatim so the rejection is
    attributable to the write, not to a weakened spec). A byte-fuzzer never
    thinks to mutate the input — this is the project's #1 weakness class.

  * UNGROUNDED-ORACLE ECHO is N/A as a *wrong-echo* attack: the postcondition
    oracle (`collected`/`run_len`) is GROUNDED in the input args — it is a fully
    unfolded @Pure function of `cont`/`val`, not an opaque answer-key constant or
    a synthesisable marker. There is no value an impl can echo that satisfies
    L103 without actually producing `collected(cont,val)`; moreover a PSeq is not
    directly materialisable into the returned List, so the only way to satisfy
    `ToSeq(Result()) == collected(...)` is to build the list element-by-element
    matching the fold. We therefore include an HONEST cheapest-impl positive
    control (`honest-single-line`) on the sub-domain where the cheapest correct
    answer is a singleton, instead of a wrong-echo reject.

  * PARTIAL-DOMAIN: three rivals each correct on a sub-domain but diverging
    elsewhere — `first-only` (the pre-patch [val[0]]; correct only when the
    leading line terminates, run_len==1); `over-collect-all` (collect EVERY line
    regardless of the terminator; correct only when the whole block is one run);
    `drop-terminator` (stop one short, omit the terminating line's value;
    off-by-one on the suffix). All must reject.

  * POSITIVE CONTROL (soundness): a structurally-different but CORRECT impl that
    commutes the break disjunction (`i == n-1 or c == 0`) and reshapes the
    per-step locals, KEEPING every gold framing assert (directive-2: a forward
    telescoping fold needs the per-step `collected(drop i)` unfold asserts; the
    gold impl is itself a forward-append against the front-recursive fold, so a
    forward-append positive control is in-idiom and does NOT need an
    f(a+b)==f(a)+f(b) lemma — directive-3 — provided the gold asserts stay).
    MUST verify (else SPEC-TOO-STRONG).

  * ADMISSIBILITY: an in-region self-call on an F2P-shaped input (a 2-line run,
    leading line open: cont=[1,0], val=[10,20]) asserting the precondition is
    establishable and the run length is 2. MUST verify (else PRECOND-TOO-STRONG).

  CONTROL-FLOW-EFFECT is N/A: `gather_signatures` is a pure value computation
  with a single return and no raise / side-effect path invisible to the value
  abstraction — the entire observable effect is the returned List, fully pinned
  by L103. VALUE-DOUBLE-MASK is N/A: L103 pins the ENTIRE sequence
  (`ToSeq(Result()) == collected(...)`), not an index-via-value proxy that could
  drop disagreeing indices; L106 independently pins the count and L108 the head.

AXIOMS: none. meta.axioms == [] (no @ContractOnly axioms). The sole A-reference
deep model (`run_len`/`collected`) is validated == the real patched
`_find_signature`+`format_signature` by axiom_check.py (G-AX) out-of-band
(verbatim py_ext_sig_re; exhaustive clean runs len 1..6 x all continuation
patterns + 20000 fuzz + the F2P class E (2 sigs) / class D (1 sig) fixtures;
order-faithful, no count-only proxy). PBT's axiom lane covers only obligations
NOT already discharged by G-AX; there is none here, so AXIOM_TESTS == [].

Authoring mechanics: every spec variant is built by REGION-SURGERY (`_swap`)
that edits ONLY inside `# impl-start`/`# impl-end` (the invariants region is
NESTED inside impl, so editing it is still inside the elided span and preserves
`markers.same_spec`). A rejection therefore comes from the POSTCONDITION (or the
permission system), never from a tampered spec. Each `expect:"reject"` rival
carries the refinement argument that its faithful real patch would NOT resolve
the F2P (test_autoclass_content_and_docstring_signature_init/both, which render
the class E two-__init__-signature fixture whose leading line is continued).
"""
from pathlib import Path

INSTANCE = "sphinx-doc__sphinx-7748"
FLOAT_ENCODING = None  # meta.json float_encoding is null

# --- base spec (frozen) ------------------------------------------------------
_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src: str, old: str, new: str) -> str:
    """Replace exactly one occurrence of an impl-region substring; assert it
    actually matched so silent drift (model.py edited) fails loudly at load."""
    if old not in src:
        raise AssertionError("drift: %r not in model.py" % (old,))
    if src.count(old) != 1:
        raise AssertionError("not unique: %r (%d)" % (old, src.count(old)))
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Surgery anchors — verbatim slices of the gold impl region.
# ---------------------------------------------------------------------------
# The whole gold impl body (between `# impl-start` and `# impl-end`), used as the
# anchor for whole-body rewrites (positive control, partial-domain rivals).
_GOLD_BODY = (
    "    result = []  # type: List[int]\n"
    "    n = len(cont)\n"
    "    i = 0\n"
    "    while True:\n"
    "        # invariants-start\n"
    "        Invariant(Acc(list_pred(cont), 1 / 2))\n"
    "        Invariant(Acc(list_pred(val), 1 / 2))\n"
    "        Invariant(len(cont) == len(val))\n"
    "        Invariant(n == len(cont))\n"
    "        Invariant(0 <= i and i < n)\n"
    "        Invariant(Acc(list_pred(result)))\n"
    "        # telescoping fold: what is already collected, concatenated with the\n"
    "        # collected run of the remaining suffix, is the whole collected run.\n"
    "        Invariant(ToSeq(result) + collected(ToSeq(cont).drop(i), ToSeq(val).drop(i)) ==\n"
    "                  collected(ToSeq(cont), ToSeq(val)))\n"
    "        # The condition is the constant `True`, so the bound comes from what the\n"
    "        # break counts down: the loop leaves via `break` no later than the line\n"
    "        # index i reaching the last line n - 1, and i rises by exactly one per\n"
    "        # pass, so at most n - i + 1 passes remain. It strictly decreases because\n"
    "        # only i changes (n is a local fixed before the loop, pinned by\n"
    "        # Invariant(n == len(cont))), and it stays >= 2 because the invariant\n"
    "        # Invariant(0 <= i and i < n) holds on entry to every pass (so it never\n"
    "        # reaches the unsatisfiable 0).\n"
    "        Invariant(MustTerminate(n - i + 1))\n"
    "        # invariants-end\n"
    "        c = cont[i]\n"
    "        v = val[i]\n"
    "        # peel the head of the suffix drop(i): head is line i, tail is drop(i+1).\n"
    "        Assert(ToSeq(cont).drop(i)[0] == c)\n"
    "        Assert(ToSeq(val).drop(i)[0] == v)\n"
    "        result = result + [v]\n"
    "        if c == 0 or i == n - 1:\n"
    "            # the run ends here — either this line terminates it (not open) or\n"
    "            # it is the last line of the block (no further line to spill onto).\n"
    "            # One unfold of collected on drop(i): when the line is not open the\n"
    "            # suffix is PSeq(v); when it is the last line the tail drop(i+1) is\n"
    "            # empty so collected of it is empty, again leaving PSeq(v). Either\n"
    "            # way the suffix contributes exactly this value.\n"
    "            Assert(ToSeq(cont).drop(i).drop(1) == ToSeq(cont).drop(i + 1))\n"
    "            Assert(ToSeq(val).drop(i).drop(1) == ToSeq(val).drop(i + 1))\n"
    "            Assert(collected(ToSeq(cont).drop(i), ToSeq(val).drop(i)) == PSeq(v))\n"
    "            break\n"
    "        # open line that is not the last: one unfold of collected on drop(i)\n"
    "        # peels PSeq(v) and recurses on drop(i+1).\n"
    "        Assert(ToSeq(cont).drop(i).drop(1) == ToSeq(cont).drop(i + 1))\n"
    "        Assert(ToSeq(val).drop(i).drop(1) == ToSeq(val).drop(i + 1))\n"
    "        Assert(collected(ToSeq(cont).drop(i), ToSeq(val).drop(i)) ==\n"
    "               PSeq(v) + collected(ToSeq(cont).drop(i + 1), ToSeq(val).drop(i + 1)))\n"
    "        i = i + 1\n"
    "    return result\n"
)


def _body(new_body: str) -> str:
    return _swap(_BASE, _GOLD_BODY, new_body)


# ===========================================================================
# SPEC CASES
# ===========================================================================
SPEC_TESTS = [

    # -- POSITIVE CONTROL (soundness): structurally-different CORRECT impl ------
    #
    # Commute the break disjunction to `i == n - 1 or c == 0` and reshape the
    # per-step locals (bind the suffix-head value once into a fresh local `head`,
    # build the appended list via a pre-bound one-element local). KEEP every gold
    # framing assert verbatim (directive-2): the forward telescoping fold needs
    # the per-step `collected(drop i)` unfold asserts to discharge the loop
    # invariant. This is forward-append against a front-recursive fold, which is
    # exactly the gold idiom (directive-3 N/A: the gold impl itself appends
    # forward and the asserts make each unfold local, so no f(a+b)==f(a)+f(b)
    # lemma is needed). Must verify.
    {"id": "pos-commute-break", "kind": "soundness", "expect": "verify",
     "module": _body(
         "    result = []  # type: List[int]\n"
         "    n = len(cont)\n"
         "    i = 0\n"
         "    while True:\n"
         "        # invariants-start\n"
         "        Invariant(Acc(list_pred(cont), 1 / 2))\n"
         "        Invariant(Acc(list_pred(val), 1 / 2))\n"
         "        Invariant(len(cont) == len(val))\n"
         "        Invariant(n == len(cont))\n"
         "        Invariant(0 <= i and i < n)\n"
         "        Invariant(Acc(list_pred(result)))\n"
         "        Invariant(ToSeq(result) + collected(ToSeq(cont).drop(i), ToSeq(val).drop(i)) ==\n"
         "                  collected(ToSeq(cont), ToSeq(val)))\n"
         "        # The condition is the constant `True`, so the bound comes from what the\n"
         "        # break counts down: the loop leaves via `break` no later than the line\n"
         "        # index i reaching the last line n - 1, and i rises by exactly one per\n"
         "        # pass, so at most n - i + 1 passes remain. It strictly decreases because\n"
         "        # only i changes (n is a local fixed before the loop, pinned by\n"
         "        # Invariant(n == len(cont))), and it stays >= 2 because the invariant\n"
         "        # Invariant(0 <= i and i < n) holds on entry to every pass (so it never\n"
         "        # reaches the unsatisfiable 0).\n"
         "        Invariant(MustTerminate(n - i + 1))\n"
         "        # invariants-end\n"
         "        c = cont[i]\n"
         "        head = val[i]\n"                       # reshaped local name
         "        Assert(ToSeq(cont).drop(i)[0] == c)\n"
         "        Assert(ToSeq(val).drop(i)[0] == head)\n"
         "        one = [head]  # type: List[int]\n"     # pre-bound one-element list
         "        result = result + one\n"
         "        if i == n - 1 or c == 0:\n"            # commuted disjunction
         "            Assert(ToSeq(cont).drop(i).drop(1) == ToSeq(cont).drop(i + 1))\n"
         "            Assert(ToSeq(val).drop(i).drop(1) == ToSeq(val).drop(i + 1))\n"
         "            Assert(collected(ToSeq(cont).drop(i), ToSeq(val).drop(i)) == PSeq(head))\n"
         "            break\n"
         "        Assert(ToSeq(cont).drop(i).drop(1) == ToSeq(cont).drop(i + 1))\n"
         "        Assert(ToSeq(val).drop(i).drop(1) == ToSeq(val).drop(i + 1))\n"
         "        Assert(collected(ToSeq(cont).drop(i), ToSeq(val).drop(i)) ==\n"
         "               PSeq(head) + collected(ToSeq(cont).drop(i + 1), ToSeq(val).drop(i + 1)))\n"
         "        i = i + 1\n"
         "    return result\n"),
     "rationale": "structurally-different but CORRECT: commutes the break "
                  "disjunction (i==n-1 or c==0) and reshapes the per-step locals "
                  "(head, a pre-bound one-element list `one`). Keeps every gold "
                  "framing assert so the loop invariant still discharges. Must "
                  "verify (else SPEC-TOO-STRONG)."},

    # -- ADMISSIBILITY: precondition admits an F2P-shaped input ----------------
    #
    # The F2P (class E) is a 2-line run whose leading line is continued. Encode
    # it as cont=[1,0], val=[10,20] and self-call gather_signatures, asserting
    # the precondition (len==len, len>0) is establishable and the result has
    # length 2 (run_len). The caller is appended INSIDE the impl region (after
    # `return result`), so same_spec is preserved.
    {"id": "admiss-class-e", "kind": "admissibility", "expect": "verify",
     "module": _body(_GOLD_BODY +
                     "\n"
                     "\n"
                     "def _admiss_caller() -> None:\n"
                     "    # F2P class E shape: 2 lines, leading line open (continued),\n"
                     "    # second terminates. A normal input must establish Requires\n"
                     "    # (else PRECOND-TOO-STRONG); the run length is 2.\n"
                     "    cnt = [1, 0]  # type: List[int]\n"
                     "    vls = [10, 20]  # type: List[int]\n"
                     "    out = gather_signatures(cnt, vls)\n"
                     "    Assert(len(out) == 2)\n"
                     "    Assert(out[0] == 10)\n"),
     "rationale": "the precondition (len(cont)==len(val), len(cont)>0) must "
                  "accept the F2P-shaped 2-line open-leading run cont=[1,0]; the "
                  "result length must be run_len==2 and the head val[0]==10. If "
                  "the self-call cannot establish Requires => PRECOND-TOO-STRONG."},

    # -- FRAME-MUTATION (MANDATORY: BOTH inputs are Acc(...,1/2) read-only) -----
    #
    # WRITE through `cont` (held at 1/2) before reading it. `cont[0] = 0` would
    # force the first line to terminate the run (making run_len==1) so a wrong
    # singleton would satisfy the postcondition IF the write were permitted — but
    # a store through a 1/2 list_pred is INSUFFICIENT PERMISSION, so it must
    # reject. Gold invariants/asserts kept verbatim so the rejection is
    # attributable to the write, not to a weakened spec.
    {"id": "frame-mutate-cont", "kind": "uniqueness", "expect": "reject",
     "module": _body(
         "    cont[0] = 0\n"                       # <-- write through 1/2 permission
         + _GOLD_BODY),
     "refinement": "the real _find_signature reads `doclines` (the docstring "
                   "block) and the per-line continuation marker only; it never "
                   "writes back into the docstring lines. A patch that mutated "
                   "the continuation flag of the first line (forcing it to "
                   "terminate) would collect only one signature on the class E "
                   "fixture (leading line continued) — exactly the pre-patch bug "
                   "the F2P (test_..._init/both) catches — so it would NOT "
                   "resolve.",
     "rationale": "MANDATORY frame-mutation probe on the first read-only input. "
                  "`cont[0] = 0` writes through Acc(list_pred(cont),1/2); Nagini "
                  "requires FULL permission for a store, so with only 1/2 the "
                  "assignment fails for INSUFFICIENT PERMISSION. Rejection comes "
                  "from the permission system, not the postcondition."},

    # WRITE through `val` (held at 1/2). `val[0] = val[0]` is a no-op value but a
    # store still needs full permission; len>0 (Requires) so index 0 is in
    # bounds. Must reject for INSUFFICIENT PERMISSION.
    {"id": "frame-mutate-val", "kind": "uniqueness", "expect": "reject",
     "module": _body(
         "    val[0] = val[0]\n"                   # <-- write through 1/2 permission
         + _GOLD_BODY),
     "refinement": "the real loop records (args, retann) / appends to "
                   "self._signatures from the parsed line text; it never writes "
                   "into the docstring value stream. A patch that mutated the "
                   "per-line signature values would render corrupted signatures "
                   "and fail the F2P assertions on the exact rendered "
                   "'(...) -> ...' strings, so it would NOT resolve.",
     "rationale": "MANDATORY frame-mutation probe on the second read-only input. "
                  "`val[0] = val[0]` writes through Acc(list_pred(val),1/2); a "
                  "store needs full permission. With only 1/2 it rejects for "
                  "INSUFFICIENT PERMISSION (even though the stored value is "
                  "unchanged) — the permission system, not the postcondition."},

    # -- PARTIAL-DOMAIN: pin only a sub-domain of the run shape ----------------
    #
    # (1) FIRST-ONLY — the pre-patch behaviour: return [val[0]]. Correct only
    # when the leading line TERMINATES (run_len==1). For an OPEN leading line
    # (the F2P class E: cont[0]!=0, run_len>=2) len(Result())==1 != run_len and
    # ToSeq(Result()) == PSeq(val[0]) != collected(...). This IS model_prepatch.
    {"id": "first-only", "kind": "uniqueness", "expect": "reject",
     "module": _body(
         "    head = val[0]\n"
         "    result = [head]  # type: List[int]\n"
         "    return result\n"),
     "refinement": "this IS the pre-patch code path (match doclines[0], record "
                   "one signature, break). On the F2P class E fixture the leading "
                   "__init__ line is continued, so gold renders 2 signatures and "
                   "this renders 1 — test_autoclass_content_and_docstring_"
                   "signature_init/both assert the 2-line rendering, so it would "
                   "NOT resolve. (model_prepatch.py reproduces exactly this.)",
     "rationale": "PARTIAL-DOMAIN: pins only the run_len==1 sub-domain. For an "
                  "open leading line (cont[0]!=0) run_len>=2, so len(Result())==1 "
                  "violates L106 (len==run_len) and ToSeq(Result())==PSeq(val[0]) "
                  "!= collected(...) violates L103. Rejection from the gathering "
                  "postcondition."},

    # (2) OVER-COLLECT-ALL — collect EVERY line of the block regardless of the
    # terminator. Correct only when the WHOLE block is one open run (every
    # cont[k]!=0 for k<n-1). When some line k<n-1 has cont[k]==0, the run should
    # STOP there (run_len==k+1 < n) but this collects all n, so len(Result())==n
    # > run_len violates L106 and ToSeq(Result()) != collected(...) violates L103.
    {"id": "over-collect-all", "kind": "uniqueness", "expect": "reject",
     "module": _body(
         "    result = []  # type: List[int]\n"
         "    n = len(cont)\n"
         "    i = 0\n"
         "    while i < n:\n"
         "        # invariants-start\n"
         "        Invariant(Acc(list_pred(cont), 1 / 2))\n"
         "        Invariant(Acc(list_pred(val), 1 / 2))\n"
         "        Invariant(len(cont) == len(val))\n"
         "        Invariant(n == len(cont))\n"
         "        Invariant(0 <= i and i <= n)\n"
         "        Invariant(Acc(list_pred(result)))\n"
         "        # this variant counts differently from gold (a plain forward walk\n"
         "        # over every line), so it carries its own measure: at most n - i + 1\n"
         "        # passes remain, n is a local fixed before the loop, i rises by\n"
         "        # exactly one per pass, and the guard i < n keeps the bound >= 2 on\n"
         "        # entry to a pass.\n"
         "        Invariant(MustTerminate(n - i + 1))\n"
         "        # invariants-end\n"
         "        result = result + [val[i]]\n"
         "        i = i + 1\n"
         "    return result\n"),
     "refinement": "collecting every docstring line ignores the `break` at the "
                   "first non-continued line. The real loop stops at the first "
                   "line NOT ending in '\\\\'; collecting past it would gather "
                   "trailing prose / a second unrelated signature block as extra "
                   "signatures, producing a wrong rendered '\\n'.join — the F2P "
                   "fixtures (which expect exactly the run up to the first "
                   "terminator) would fail, so it would NOT resolve.",
     "rationale": "PARTIAL-DOMAIN: pins only the all-open sub-domain. When a line "
                  "k<n-1 terminates (cont[k]==0) the collected run is k+1 lines, "
                  "but this returns all n, so len(Result())==n != run_len(...) "
                  "violates L106 and ToSeq(Result()) != collected(...) violates "
                  "L103. Rejection from the gathering postcondition."},

    # (3) DROP-TERMINATOR — gather the open leading lines but OMIT the first
    # terminating line's value (stop one short). Off-by-one on the suffix: when
    # the leading line is open (cont[0]!=0) the gold run includes the terminator,
    # so dropping it gives run_len-1 elements. len(Result()) < run_len violates
    # L106; ToSeq(Result()) != collected(...) violates L103. (When run_len==1 it
    # would even return empty, violating L108 Result()[0]==val[0].)
    {"id": "drop-terminator", "kind": "uniqueness", "expect": "reject",
     "module": _body(
         "    result = []  # type: List[int]\n"
         "    n = len(cont)\n"
         "    i = 0\n"
         "    while i < n and cont[i] != 0:\n"
         "        # invariants-start\n"
         "        Invariant(Acc(list_pred(cont), 1 / 2))\n"
         "        Invariant(Acc(list_pred(val), 1 / 2))\n"
         "        Invariant(len(cont) == len(val))\n"
         "        Invariant(n == len(cont))\n"
         "        Invariant(0 <= i and i <= n)\n"
         "        Invariant(Acc(list_pred(result)))\n"
         "        # this variant counts differently from gold (a compound guard), so it\n"
         "        # carries its own measure: the counter part alone bounds the passes at\n"
         "        # n - i + 1 (the extra conjunct only makes the loop leave sooner), n is\n"
         "        # a local fixed before the loop, i rises by exactly one per pass, and\n"
         "        # the guard i < n keeps the bound >= 2 on entry to a pass.\n"
         "        Invariant(MustTerminate(n - i + 1))\n"
         "        # invariants-end\n"
         "        result = result + [val[i]]\n"
         "        i = i + 1\n"
         "    return result\n"),
     "refinement": "this collects the open leading lines but never records the "
                   "FIRST terminating line — the real loop records the signature "
                   "and THEN breaks, so the terminating line IS included. Omitting "
                   "it renders one too few signatures (and none at all for a "
                   "single terminating line), so the F2P rendering "
                   "('\\n'.join([sig] + self._signatures)) is short by the "
                   "terminating signature and the F2P assertions fail — it would "
                   "NOT resolve.",
     "rationale": "PARTIAL-DOMAIN / off-by-one: omits the terminating line's "
                  "value. run_len counts the terminating line (1 + ... for open "
                  "leads, else 1), so this returns run_len-1 elements: "
                  "len(Result()) != run_len violates L106 and ToSeq(Result()) != "
                  "collected(...) violates L103 (and an all-terminating leading "
                  "line yields empty, violating L108 Result()[0]==val[0])."},

    # -- HONEST CHEAPEST positive control (grounded oracle has no echo cheat) --
    #
    # On the run_len==1 sub-domain (a single terminating leading line) the
    # cheapest CORRECT answer is the singleton [val[0]]. But the spec is over the
    # WHOLE domain, so a `return [val[0]]` cannot verify in general (that is the
    # `first-only` reject above). The honest cheapest impl that DOES verify is
    # still the full gold loop — there is no shortcut because the oracle is
    # grounded. We therefore demonstrate the grounded-oracle positive with a
    # local-variable reshape of the gold body that aliases the suffix value once;
    # it does the real work and must verify.
    {"id": "honest-grounded", "kind": "soundness", "expect": "verify",
     "module": _body(
         "    result = []  # type: List[int]\n"
         "    n = len(cont)\n"
         "    i = 0\n"
         "    while True:\n"
         "        # invariants-start\n"
         "        Invariant(Acc(list_pred(cont), 1 / 2))\n"
         "        Invariant(Acc(list_pred(val), 1 / 2))\n"
         "        Invariant(len(cont) == len(val))\n"
         "        Invariant(n == len(cont))\n"
         "        Invariant(0 <= i and i < n)\n"
         "        Invariant(Acc(list_pred(result)))\n"
         "        Invariant(ToSeq(result) + collected(ToSeq(cont).drop(i), ToSeq(val).drop(i)) ==\n"
         "                  collected(ToSeq(cont), ToSeq(val)))\n"
         "        # The condition is the constant `True`, so the bound comes from what the\n"
         "        # break counts down: the loop leaves via `break` no later than the line\n"
         "        # index i reaching the last line n - 1, and i rises by exactly one per\n"
         "        # pass, so at most n - i + 1 passes remain. It strictly decreases because\n"
         "        # only i changes (n is a local fixed before the loop, pinned by\n"
         "        # Invariant(n == len(cont))), and it stays >= 2 because the invariant\n"
         "        # Invariant(0 <= i and i < n) holds on entry to every pass (so it never\n"
         "        # reaches the unsatisfiable 0).\n"
         "        Invariant(MustTerminate(n - i + 1))\n"
         "        # invariants-end\n"
         "        c = cont[i]\n"
         "        v = val[i]\n"
         "        Assert(ToSeq(cont).drop(i)[0] == c)\n"
         "        Assert(ToSeq(val).drop(i)[0] == v)\n"
         "        result = result + [v]\n"
         "        last = i == n - 1\n"                 # pre-bound boolean local
         "        terminates = c == 0\n"               # pre-bound boolean local
         "        if terminates or last:\n"
         "            Assert(ToSeq(cont).drop(i).drop(1) == ToSeq(cont).drop(i + 1))\n"
         "            Assert(ToSeq(val).drop(i).drop(1) == ToSeq(val).drop(i + 1))\n"
         "            Assert(collected(ToSeq(cont).drop(i), ToSeq(val).drop(i)) == PSeq(v))\n"
         "            break\n"
         "        Assert(ToSeq(cont).drop(i).drop(1) == ToSeq(cont).drop(i + 1))\n"
         "        Assert(ToSeq(val).drop(i).drop(1) == ToSeq(val).drop(i + 1))\n"
         "        Assert(collected(ToSeq(cont).drop(i), ToSeq(val).drop(i)) ==\n"
         "               PSeq(v) + collected(ToSeq(cont).drop(i + 1), ToSeq(val).drop(i + 1)))\n"
         "        i = i + 1\n"
         "    return result\n"),
     "rationale": "the grounded-oracle positive control: because the postcond "
                  "oracle (collected/run_len) is a fully-unfolded function of the "
                  "args, the cheapest faithful impl still walks the run and builds "
                  "the list element-by-element. This reshape pre-binds the "
                  "terminator booleans into locals (`terminates`, `last`) but does "
                  "the identical real work. Must verify, proving the spec is "
                  "satisfiable by honest work (no echo shortcut exists for a "
                  "grounded oracle)."},
]

# ===========================================================================
# AXIOM CASES — none.
# ===========================================================================
# meta.axioms == [] (no @ContractOnly axioms). The sole A-reference deep model
# (run_len / collected) is validated == the real patched _find_signature +
# format_signature by axiom_check.py (G-AX), which runs IN-CONTAINER: it
# reimplements the post-patch loop + join with the verbatim py_ext_sig_re
# (sphinx/ext/autodoc/__init__.py:55) and asserts the model's count AND
# per-position rendered string equal the real algorithm's over the exhaustive
# clean runs (lengths 1..6 x all continuation patterns) + 20000 fuzz + the F2P
# class E (2 sigs) / class D (1 sig) fixtures. PBT's axiom lane covers only
# obligations NOT already discharged by G-AX (consumed @ContractOnly axioms /
# A-reference containment the model can reach but G-AX does not exercise); here
# G-AX already executes the real callee and asserts the deep model over the full
# reachable clean-run domain, so there is no additional axiom obligation for
# this lane.
AXIOM_TESTS = []
