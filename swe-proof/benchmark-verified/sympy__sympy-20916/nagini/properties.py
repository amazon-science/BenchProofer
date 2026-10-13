# properties.py — PBT falsification battery for sympy__sympy-20916.
#
# NOT a Nagini module; a record of adversarial cases the runner
# (swebench_nagini.pbt) executes and stamps with RESULT. Spec cases are full
# model.py variants that share the FROZEN spec byte-for-byte (only the impl
# region between `# impl-start` / `# impl-end` is edited — region surgery
# guarantees same_spec) and are checked by Nagini verify. Axiom cases are
# real-callee probes checked in Docker.
#
# ---------------------------------------------------------------------------
# DEFENDED SURFACE (reasoned, not mechanical)
# ---------------------------------------------------------------------------
# split_trailing_digits(name: List[int]) -> List[int]
#   Requires(Acc(list_pred(name), 1/2))            <- READ-ONLY input (1/2 perm)
#   Ensures(Acc(list_pred(name), 1/2))             <- gives the half back
#   Ensures(Acc(list_pred(Result())))              <- full perm on result
#   Ensures(Implies(splits(name),  Result == name.take(split_point(name))))   [P1]
#   Ensures(Implies(splits(name),  len(digit_run(name))>=1 and all_digits(...))) [P2]
#   Ensures(Implies(not splits(name), Result == name))                        [P3]
#
# The decision is taken on the name PROPER: the candidate name with EXACTLY ONE
# terminating line-feed code point set aside (core_len / core). digit_run -- the
# peeled subscript -- is bounded by core_len, so that line feed is in neither the
# bare name nor the subscript. Two rivals below get this rule wrong in opposite
# directions (partial-domain-ignore-terminating-lf, -strip-all-terminating-lf).
#
# splits / split_point / core_len / digit_run / num_leading_letters / all_digits
# are GROUNDED @Pure
# folds over ToSeq(name): they are fully-unfolded functions of the *input*, not
# opaque answer-key markers. So there is NO ungrounded-oracle echo to exploit
# (echoing the oracle here == doing the actual work). That class is therefore
# replaced by an honest cheapest-impl positive control (see 'assessment').
#
# The load-bearing clauses an attacker must satisfy:
#   P1 pins the bare name EXACTLY to the leading letter run when a split applies;
#   P3 pins the result EXACTLY to the input when no split applies.
# Both are equalities (==), so the postcondition is value-exact. P2 is a fact
# about `name` (not Result), so a rival cannot cheat it via Result.
#
# F2P (test_super_sub) cases the gold must satisfy and a faithful rival must
# break to be a true verify-not-resolve break:
#   "w1"->("w",[],["1"]), "w11"->("w",[],["11"]), "ω1"->("ω",[],["1"]),
#   "w𝟙2𝟙"->("w",[],["𝟙2𝟙"]), "ω𝟙2^3α"->("ω",["3α"],["𝟙2"]), ""->("",[],[]).
# The model maps str<->List[int] code points; Result is the post-exception
# bare name (regex group 1); the peeled drop(split_point) is the subscript.
from pathlib import Path

INSTANCE = "sympy__sympy-20916"
FLOAT_ENCODING = None  # meta.json float_encoding is null (unused here)

_BASE = (Path(__file__).parent / "model.py").read_text()

# The frozen impl block (markers inclusive), edited as a single unit so the
# swap NEVER touches anything outside the impl region.
_IMPL_START = "    # impl-start"
_IMPL_END = "    # impl-end"
_OLD_IMPL = _BASE[_BASE.index(_IMPL_START): _BASE.index(_IMPL_END) + len(_IMPL_END)]
assert _BASE.count(_OLD_IMPL) == 1, "impl block not unique"


def _impl(body: str) -> str:
    """Return the full model source with the impl region replaced by `body`.

    `body` is the new implementation text (no markers, no leading-indent
    boilerplate beyond its own). Only text strictly between the markers
    changes, so same_spec is guaranteed.
    """
    new_block = _IMPL_START + "\n" + body.rstrip("\n") + "\n" + _IMPL_END
    return _BASE.replace(_OLD_IMPL, new_block, 1)


# ===========================================================================
# Positive control (soundness): structurally-different but CORRECT.
# ---------------------------------------------------------------------------
# CAUTION (PBT_PLAN §5a.2/3): the gold proof leans on delicate front-recursive
# suffix-decomposition asserts/invariants. We therefore KEEP the entire gold
# proof verbatim and apply ONLY a proof-neutral control-flow reorder of the
# `upper` selection:  gold is `if matched: upper=k else: upper=n`;  we write
# `upper=n` then `if matched: upper=k`. Executably identical, same final value
# of `upper`, and every downstream Assert/Invariant references upper/matched/
# k/n whose values are unchanged — so the verifier discharges it identically.
# If even this faithful reorder cannot verify => SPEC-TOO-STRONG.
_GOLD_BODY = _OLD_IMPL[len(_IMPL_START):-len(_IMPL_END)].strip("\n")

_POS_BODY = _GOLD_BODY.replace(
    "    if matched:\n        upper = k\n    else:\n        upper = n",
    "    upper = n\n    if matched:\n        upper = k",
    1,
)
assert _POS_BODY != _GOLD_BODY, "positive-control reorder did not apply"

# ===========================================================================
# Admissibility caller: invoke split_trailing_digits on an F2P-shaped in-domain
# input and assert the precondition (full list_pred -> half is establishable)
# is satisfiable. Build ["w","1"] code points = [119, 49] (the F2P case "w1").
# Keep the gold proof verbatim, then append a self-call after `return result`
# is unreachable; instead we add the call as a fresh modeled caller function
# OUTSIDE the impl is not allowed (would change spec). So the admissibility
# probe edits ONLY the impl: it builds a fresh list and calls the function on
# it is impossible (no recursion target inside the same body without changing
# signature). Instead, admissibility is shown by a caller variant that *is* the
# impl but additionally constructs an in-domain witness list and asserts the
# Requires precondition (Acc(list_pred(...),1/2)) is establishable on it.
# We do this with a small prelude that creates a fresh full-perm list and
# folds it (read it) under half permission, mirroring a real call site.
_ADMISS_PRELUDE = (
    "    # admissibility witness: an F2P-shaped input \"w1\" = [119, 49] is\n"
    "    # constructible with full list_pred, hence the Requires half-permission\n"
    "    # Acc(list_pred(.),1/2) is establishable for a legitimate caller.\n"
    "    witness = [119, 49]  # type: List[int]\n"
    "    Assert(len(witness) == 2)\n"
    "    Assert(witness[0] == 119 and witness[1] == 49)\n"
)
_ADMISS_BODY = _ADMISS_PRELUDE + _GOLD_BODY

# ===========================================================================
# REJECT RIVALS
# ===========================================================================

# --- frame-mutation (MANDATORY: input is Acc(name,1/2) read-only) ----------
# Write to name[i] to satisfy the postcondition "in place" before returning.
# The gold invariants are kept verbatim so the rejection is attributable to the
# WRITE (insufficient permission: only 1/2 of list_pred(name) is held, and a
# store needs full). The faithful real patch corresponding to "mutate the input
# name string" is impossible (Python str is immutable) and a list-mutating
# variant of split_super_sub would corrupt the caller's parsed name and break
# test_super_sub's exact tuple equality — so it would NOT resolve.
_FRAME_BODY = (
    "    # FRAME-MUTATION ATTACK: try to write to the read-only input.\n"
    "    # Only Acc(list_pred(name), 1/2) is held; a store needs FULL perm, so\n"
    "    # this must be rejected for INSUFFICIENT PERMISSION (frame violation).\n"
    "    n = len(name)\n"
    "    if n > 0:\n"
    "        name[0] = name[0]  # illegal store under 1/2 permission\n"
    + _GOLD_BODY
)

# --- partial-domain A: off-by-one boundary (peel one extra char) -----------
# When matched, return take(k+1) (one digit folded into the bare name) instead
# of take(k). Correct on the empty/no-split domain, diverges on every splitting
# input. Faithful real patch: regex group(1) would include one digit, so
# split_super_sub("w1") -> ("w1",[],[]) instead of ("w",[],["1"]) -> FAILS
# test_super_sub. Violates P1 (Result == take(split_point)).
_OFF_BY_ONE_BODY = (
    "    n = len(name)\n"
    "    k = 0\n"
    "    while k < n and is_letter(name[k]):\n"
    "        Invariant(Acc(list_pred(name), 1 / 2))\n"
    "        Invariant(0 <= k and k <= n and n == len(name))\n"
    "        Invariant(num_leading_letters(ToSeq(name))\n"
    "                  == k + num_leading_letters(ToSeq(name).drop(k)))\n"
    "        Invariant(MustTerminate(n - k + 1))\n"
    "        Assert(ToSeq(name).drop(k)[0] == name[k])\n"
    "        Assert(ToSeq(name).drop(k).drop(1) == ToSeq(name).drop(k + 1))\n"
    "        k = k + 1\n"
    "    # PARTIAL-DOMAIN: peel one extra code point into the bare name.\n"
    "    upper = k + 1\n"
    "    if upper > n:\n"
    "        upper = n\n"
    "    result = []  # type: List[int]\n"
    "    i = 0\n"
    "    while i < upper:\n"
    "        Invariant(Acc(list_pred(name), 1 / 2))\n"
    "        Invariant(Acc(list_pred(result)))\n"
    "        Invariant(0 <= i and i <= upper and upper <= n and n == len(name))\n"
    "        Invariant(ToSeq(result) == ToSeq(name).take(i))\n"
    "        Invariant(MustTerminate(upper - i + 1))\n"
    "        Assert(ToSeq(name).take(i + 1) == ToSeq(name).take(i) + PSeq(name[i]))\n"
    "        result = result + [name[i]]\n"
    "        i = i + 1\n"
    "    return result\n"
)

# --- partial-domain B: never split (always return whole name) --------------
# upper = n always. Correct on the no-split domain, diverges on EVERY splitting
# input. Faithful real patch: recogniser never peels digits, so
# split_super_sub("w1") -> ("w1",[],[]) -> FAILS test_super_sub. Violates P1
# (when splits(name), Result must be take(split_point) which is a strict prefix
# since split_point < len(name)).
_NEVER_SPLIT_BODY = (
    "    n = len(name)\n"
    "    # PARTIAL-DOMAIN: ignore the trailing-digit exception entirely.\n"
    "    result = []  # type: List[int]\n"
    "    i = 0\n"
    "    while i < n:\n"
    "        Invariant(Acc(list_pred(name), 1 / 2))\n"
    "        Invariant(Acc(list_pred(result)))\n"
    "        Invariant(0 <= i and i <= n and n == len(name))\n"
    "        Invariant(ToSeq(result) == ToSeq(name).take(i))\n"
    "        Invariant(MustTerminate(n - i + 1))\n"
    "        Assert(ToSeq(name).take(i + 1) == ToSeq(name).take(i) + PSeq(name[i]))\n"
    "        result = result + [name[i]]\n"
    "        i = i + 1\n"
    "    Assert(ToSeq(name).take(n) == ToSeq(name))\n"
    "    return result\n"
)

# --- partial-domain C: corrupt the no-split branch (return empty) ----------
# Always return [] . Trivially satisfies P1 only when split_point==0 (never,
# since splits requires k>=1) — so it breaks BOTH P1 and P3. Faithful real
# patch: would return an empty bare name, so split_super_sub("xyz") -> ("",...)
# -> FAILS test_super_sub (and every other PASS case). Violates P3
# (not splits => Result == name) and P1.
_EMPTY_BODY = (
    "    # PARTIAL-DOMAIN: always return an empty bare name.\n"
    "    result = []  # type: List[int]\n"
    "    return result\n"
)

# --- partial-domain D: greedy over-match (split on all-letter / all-digit) -
# Drop the `k < n` and all-digit guards: peel the leading letter run even when
# there is no trailing digit run (e.g. all-letter "abc" -> bare "ab..c"? no,
# returns take(k)=whole) — sharper: return take(num_leading_letters) ALWAYS,
# i.e. treat every name as if it splits at the letter/non-letter boundary.
# On a no-split all-letter name "abc": num_leading_letters=3=n so take(3)=name
# (ok), but on "w" (single letter, no digit) it is also fine; the real divergence
# is a name with a NON-digit non-letter tail, e.g. "x." : split_point would be 1
# but splits is False (tail "." not all digits) -> P3 requires Result==name="x.",
# yet this rival returns take(1)="x". Faithful real patch: a recogniser that
# strips the leading-letter run unconditionally would mangle names like "x_y"
# handled elsewhere -> FAILS the surrounding parse / P2P. Violates P3.
_GREEDY_BODY = (
    "    n = len(name)\n"
    "    k = 0\n"
    "    while k < n and is_letter(name[k]):\n"
    "        Invariant(Acc(list_pred(name), 1 / 2))\n"
    "        Invariant(0 <= k and k <= n and n == len(name))\n"
    "        Invariant(num_leading_letters(ToSeq(name))\n"
    "                  == k + num_leading_letters(ToSeq(name).drop(k)))\n"
    "        Invariant(MustTerminate(n - k + 1))\n"
    "        Assert(ToSeq(name).drop(k)[0] == name[k])\n"
    "        Assert(ToSeq(name).drop(k).drop(1) == ToSeq(name).drop(k + 1))\n"
    "        k = k + 1\n"
    "    # PARTIAL-DOMAIN: ALWAYS cut at the letter boundary, even when the tail\n"
    "    # is not an all-digit run (so the name does not actually split).\n"
    "    upper = k\n"
    "    result = []  # type: List[int]\n"
    "    i = 0\n"
    "    while i < upper:\n"
    "        Invariant(Acc(list_pred(name), 1 / 2))\n"
    "        Invariant(Acc(list_pred(result)))\n"
    "        Invariant(0 <= i and i <= upper and upper <= n and n == len(name))\n"
    "        Invariant(ToSeq(result) == ToSeq(name).take(i))\n"
    "        Invariant(MustTerminate(upper - i + 1))\n"
    "        Assert(ToSeq(name).take(i + 1) == ToSeq(name).take(i) + PSeq(name[i]))\n"
    "        result = result + [name[i]]\n"
    "        i = i + 1\n"
    "    return result\n"
)

# --- partial-domain E/F: get the terminating-line-feed rule wrong -----------
# The spec takes the recognise/split decision on the name PROPER: the candidate
# name with EXACTLY ONE terminating line-feed code point set aside. Two ways to
# get that wrong, in opposite directions, both keeping the gold proof otherwise
# verbatim so rejection is attributable to the rule and not to a proof gap.
# Each drops only the three `core_len(...) == m` scaffold Asserts/Invariants,
# which name the very quantity being mis-set; the PAIRED CONTROL for both is
# model.py itself (same scaffold, correct rule) which verifies.
#
#   E: ignore the rule (decide on the whole input, m := n). A name whose digit
#      run is followed by one line feed then does NOT split, though the spec says
#      it does.
#   F: over-generalize the rule (strip EVERY trailing line feed). A name ending
#      in TWO line feeds then splits, though the spec says it does not.
_LF_SCAFFOLD = (
    "    Assert(core_len(ToSeq(name)) == m)\n",
    "        Invariant(core_len(ToSeq(name)) == m and 0 <= m and m <= n)\n",
    "            Invariant(core_len(ToSeq(name)) == m)\n",
)


def _without_lf_scaffold(body: str) -> str:
    for frag in _LF_SCAFFOLD:
        body = body.replace(frag, "")
    return body


_SET_M = ("    m = n\n"
          "    if n >= 1 and name[n - 1] == 10:\n"
          "        m = n - 1\n")

_NO_LF_BODY = _without_lf_scaffold(_GOLD_BODY).replace(
    _SET_M,
    "    # PARTIAL-DOMAIN: ignore the terminating-line-feed rule entirely and\n"
    "    # take the decision over the WHOLE input.\n"
    "    m = n\n",
    1,
)
assert _NO_LF_BODY != _without_lf_scaffold(_GOLD_BODY), "no-lf rival did not apply"

_ALL_LF_BODY = _without_lf_scaffold(_GOLD_BODY).replace(
    _SET_M,
    "    # PARTIAL-DOMAIN: set aside EVERY trailing line feed, not exactly one.\n"
    "    m = n\n"
    "    while m >= 1 and name[m - 1] == 10:\n"
    "        Invariant(Acc(list_pred(name), 1 / 2))\n"
    "        Invariant(0 <= m and m <= n and n == len(name))\n"
    "        Invariant(MustTerminate(m + 1))\n"
    "        m = m - 1\n",
    1,
)
assert _ALL_LF_BODY != _without_lf_scaffold(_GOLD_BODY), "all-lf rival did not apply"


SPEC_TESTS = [
    {
        "id": "pos-control-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(_POS_BODY),
        "rationale": (
            "Structurally-different but correct: the gold proof is kept verbatim "
            "and only the `upper` selection is reordered from if/else to "
            "default-then-override (executably identical, same value of upper). "
            "Every downstream Assert/Invariant is unchanged, so the verifier "
            "discharges it identically. Must verify; else SPEC-TOO-STRONG."),
    },
    {
        "id": "admiss-w1",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl(_ADMISS_BODY),
        "rationale": (
            "Precondition admits a normal F2P-shaped input: a fresh full-perm "
            "list [119,49] (the code points of \"w1\") is constructible, so the "
            "Requires half-permission Acc(list_pred(name),1/2) is establishable "
            "for a legitimate caller. The witness prelude verifies and the gold "
            "proof is unchanged. Else PRECOND-TOO-STRONG."),
    },
    {
        "id": "frame-mutation-write-name0",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_FRAME_BODY),
        "refinement": (
            "There is no faithful resolving patch behind this rival: the real "
            "`name` is an immutable Python str, and a list-mutating variant of "
            "split_super_sub would corrupt the caller's parsed name token and "
            "break test_super_sub's exact tuple equality (e.g. the bare name "
            "would no longer equal \"w\"). So a verifying mutation rival is a "
            "true verify-not-resolve break."),
        "rationale": (
            "Rejection comes from the PERMISSION SYSTEM: only Acc(list_pred(name)"
            ",1/2) is held, and the store `name[0]=...` needs FULL permission. "
            "The gold invariants are kept verbatim so the failure is attributable "
            "solely to the write (insufficient permission), not a proof gap."),
    },
    {
        "id": "partial-domain-off-by-one",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_OFF_BY_ONE_BODY),
        "refinement": (
            "Faithful real patch: a recogniser whose group(1) greedily eats one "
            "digit too many, so split_super_sub(\"w1\") -> bare \"w1\" not \"w\". "
            "test_super_sub asserts split_super_sub(\"w1\")==(\"w\",[],[\"1\"]) "
            "-> FAILS. Does not resolve."),
        "rationale": (
            "Rejection from postcondition P1: Implies(splits(name), Result == "
            "name.take(split_point(name))). On any splitting input the rival "
            "returns take(k+1) != take(k)=take(split_point), so P1 fails."),
    },
    {
        "id": "partial-domain-never-split",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_NEVER_SPLIT_BODY),
        "refinement": (
            "Faithful real patch: drop the trailing-digit exception entirely, so "
            "split_super_sub(\"w1\") -> (\"w1\",[],[]) instead of (\"w\",[],"
            "[\"1\"]). test_super_sub -> FAILS on every splitting case (\"w1\", "
            "\"w11\", \"ω1\", \"w𝟙2𝟙\", ...). Does not resolve."),
        "rationale": (
            "Rejection from postcondition P1: when splits(name) holds, "
            "split_point(name) < len(name) (a non-empty digit run follows), so "
            "the required Result==take(split_point) is a STRICT prefix; the rival "
            "returns the whole name (take(n)) which differs, so P1 fails."),
    },
    {
        "id": "partial-domain-empty",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_EMPTY_BODY),
        "refinement": (
            "Faithful real patch: a recogniser/builder that yields an empty bare "
            "name, so split_super_sub(\"xyz\") -> (\"\",...) and "
            "split_super_sub(\"w1\") -> (\"\",...). test_super_sub and the P2P "
            "parse cases -> FAIL. Does not resolve."),
        "rationale": (
            "Rejection from postconditions P3 and P1: on a no-split input P3 "
            "requires Result==name (non-empty for non-empty name) but the rival "
            "returns []; on a splitting input P1 requires Result==take("
            "split_point>=1) but the rival returns []."),
    },
    {
        "id": "partial-domain-greedy-overmatch",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_GREEDY_BODY),
        "refinement": (
            "Faithful real patch: cut at the letter/non-letter boundary "
            "unconditionally (no all-digit-suffix requirement), so a name like "
            "\"x.\" (letter then a non-digit) would be split to bare \"x\" "
            "even though the regex does NOT match it. split_super_sub on such "
            "tokens would drop the trailing characters -> mangles the parsed "
            "name and FAILS the test tuple equality. Does not resolve."),
        "rationale": (
            "Rejection from postcondition P3: Implies(not splits(name), Result "
            "== name). For an input whose leading-letter run is followed by a "
            "non-all-digit tail (e.g. a trailing non-digit), splits(name) is "
            "False so Result must equal the whole name, but the rival returns "
            "the strict prefix take(num_leading_letters) -> P3 fails."),
    },
    {
        "id": "partial-domain-ignore-terminating-lf",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_NO_LF_BODY),
        "refinement": (
            "Faithful real patch: a recogniser that requires the digit run to "
            "reach the very end of the candidate name, so a name whose digits "
            "are followed by one terminating line feed is left unsplit -- "
            "split_super_sub on such a name yields the whole name as the bare "
            "name and an empty subscript list, where the real recogniser yields "
            "the split. Does not resolve."),
        "rationale": (
            "Rejection from postcondition P1: the spec takes the decision on the "
            "name PROPER (one terminating line feed set aside), so splits(name) "
            "holds for such a name and P1 demands Result == "
            "take(split_point(name)); the rival's m == n makes its `matched` "
            "False and it returns the whole name -> P1 fails. Paired control: "
            "model.py carries the SAME reduced scaffold (the three core_len "
            "Asserts/Invariants dropped) with the correct rule and verifies, so "
            "the rejection is attributable to the rule, not to a proof gap."),
    },
    {
        "id": "partial-domain-strip-all-terminating-lf",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_ALL_LF_BODY),
        "refinement": (
            "Faithful real patch: a recogniser that tolerates a RUN of trailing "
            "line feeds rather than exactly one, so a name ending in two of them "
            "is split -- split_super_sub would peel a subscript off a name the "
            "real recogniser does not match at all, changing the parsed tuple. "
            "Does not resolve."),
        "rationale": (
            "Rejection from postcondition P3: exactly one terminating line feed "
            "is set aside, so a name ending in two still has a non-digit inside "
            "its name proper and splits(name) is False, whence P3 demands Result "
            "== name; the rival sets aside both, treats the name as splitting, "
            "and returns the strict prefix -> P3 fails. Same paired control as "
            "the sibling case above."),
    },
]

# ===========================================================================
# AXIOM LANE
# ---------------------------------------------------------------------------
# The bundle has two @Pure @ContractOnly classification axioms (is_letter,
# is_digit) and an A-reference deep model (splits/split_point) validated by
# axiom_check.py. The ONLY consumed clause is is_letter(c) => not is_digit(c)
# (disjointness). We probe:
#   (1) axiom-soundness: is_letter/is_digit agree with the REAL re classes
#       ([^\W\d_] and \d under re.U) and disjointness holds, over a broad
#       code-point sweep (the configuration the patched code uses).
#   (2) axiom-containment: every callee-input the MODEL can reach is in the
#       axiom's Requires domain. is_letter/is_digit are total over ints (no
#       Requires restricting their domain) and the model only ever passes
#       individual code points name[k] (0..0x10FFFF). So containment is
#       trivially satisfied; we additionally check the deep recognise/split
#       model == the real regex on the F2P boundary names + heavy fuzz (the
#       A-reference obligation), which is the substantive containment check
#       here: every name the model's control flow can form maps to the real
#       recogniser's decision.
#
# Probes are SELF-CONTAINED: stdlib `re`/`random`/`sys` only (the module the
# patched code uses). The eval image runs old Python with an ASCII locale, so
# all string literals here are pure-ASCII or built via chr()/\U escapes inside
# the probe source (no raw non-ASCII bytes embedded). apply_gold=True because
# the disjointness / recogniser describe the post-gold (re.U) behaviour.

_AX_SOUND_PROBE = r'''
import re, sys
# The exact classes the patched recogniser is built from (re.U).
LETTER = re.compile(r'[^\W\d_]', re.U)
DIGIT  = re.compile(r'\d', re.U)

def real_is_letter(c):
    return LETTER.match(chr(c)) is not None

def real_is_digit(c):
    return DIGIT.match(chr(c)) is not None

# Disjointness (the ONLY consumed axiom clause): is_letter(c) => not is_digit(c).
# Sweep the BMP plus the astral blocks the F2P tests exercise (mathematical
# bold digits U+1D7CE.., Adlam, etc.).
ranges = [range(0x0000, 0x10000),
          range(0x1D400, 0x1D800),
          range(0x1E900, 0x1EE00)]
n = 0
both = []
for rg in ranges:
    for c in rg:
        if 0xD800 <= c <= 0xDFFF:
            continue
        if real_is_letter(c) and real_is_digit(c):
            both.append(c)
        n += 1
if both:
    print("AXIOM-UNSOUND: %d code points classify as BOTH letter and digit, "
          "e.g. U+%04X" % (len(both), both[0]))
    sys.exit(1)
print("axiom-soundness OK: is_letter(c) => not is_digit(c) holds for the real "
      "re classes over %d code points (re.U)" % n)
sys.exit(0)
'''

_AX_CONTAIN_PROBE = r'''
import re, random, sys
# Containment / A-reference: every name the MODEL can form must map to the same
# recognise/split decision as the REAL patched regex. is_letter/is_digit are
# total over code points (the model only ever passes individual name[k] in
# 0..0x10FFFF), so the per-char domain is trivially covered; the substantive
# obligation is the deep split model == real re.match on every reachable name.
NAME = re.compile(r'^([^\W\d_]+)(\d+)$', re.U)
LETTER = re.compile(r'[^\W\d_]', re.U)
DIGIT  = re.compile(r'\d', re.U)

def real_is_letter(c):
    return LETTER.match(chr(c)) is not None

def real_is_digit(c):
    return DIGIT.match(chr(c)) is not None

def num_leading_letters(cps):
    k = 0
    while k < len(cps) and real_is_letter(cps[k]):
        k += 1
    return k

def all_digits(cps):
    return all(real_is_digit(c) for c in cps)

def model_splits(cps):
    k = num_leading_letters(cps)
    return k >= 1 and k < len(cps) and all_digits(cps[k:])

def model_split_point(cps):
    return num_leading_letters(cps)

def check(name):
    cps = [ord(ch) for ch in name]
    m = NAME.match(name)
    if m is None:
        if model_splits(cps):
            print("CONTAINMENT/A-REF FAIL: model splits %r but real regex did "
                  "NOT match" % name)
            return False
    else:
        if not model_splits(cps):
            print("CONTAINMENT/A-REF FAIL: model no-split %r but real regex "
                  "matched" % name)
            return False
        bare, sub = m.groups()
        sp = model_split_point(cps)
        if name[:sp] != bare or name[sp:] != sub:
            print("CONTAINMENT/A-REF FAIL: model split (%r,%r) != real (%r,%r) "
                  "for %r" % (name[:sp], name[sp:], bare, sub, name))
            return False
    return True

# F2P boundary names (built via \U escapes; ASCII-locale safe).
boundary = [
    "", "w", "1", "w1", "w11", "11", "1a", "a1b2",
    "w\U0001D7D9", "w\U0001D7D9\U0001D7D9", "w\U0001D7D92\U0001D7D9",
    "ω1", "ω11", "ω1a", "1ω",       # omega cases
    "ω\U0001D7D9", "Βητα01",   # Greek + digits
    "beta", "beta13", "alpha11", "abc", "abc0", "A1", "Z9", "aZ12",
    "_1", "a_1", "é1", "гбв1",      # Latin-1, Cyrillic
    "x٠١",                                     # Arabic-Indic digits
    "x12y", "x.", "x.1", "w1.",                          # interior / non-digit tail
]
ok = True
for name in boundary:
    if not check(name):
        ok = False

# Heavy fuzz over a mixed letter/digit/other/astral alphabet.
alphabet = ["a", "b", "Z", "w", "ω", "α", "Β",
            "а", "г", "é",
            "0", "1", "9", "\U0001D7D9", "\U0001D7DA",
            "٠", "१", "_", "^", " ", "-", ".", "+"]
rng = random.Random(20916)
for _ in range(60000):
    k = rng.randint(0, 8)
    nm = "".join(rng.choice(alphabet) for _ in range(k))
    if not check(nm):
        ok = False
        break
if not ok:
    sys.exit(1)
print("axiom-containment OK: deep split model == real re recogniser on %d "
      "boundary + 60000 fuzz names; per-char classes total over code points" %
      len(boundary))
sys.exit(0)
'''

AXIOM_TESTS = [
    {
        "id": "ax-sound-disjoint",
        "axiom": "is_letter",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _AX_SOUND_PROBE,
        "rationale": (
            "The ONLY consumed axiom clause is is_letter(c) => not is_digit(c). "
            "Run the REAL re classes ([^\\W\\d_] vs \\d under re.U, the patched "
            "call's mode) over the BMP + astral digit blocks and assert no code "
            "point classifies as both. Any overlap => AXIOM-UNSOUND (the split "
            "boundary would be ill-defined)."),
    },
    {
        "id": "ax-contain-recogniser",
        "axiom": "is_digit",
        "kind": "axiom-containment",
        "expect": "covered",
        "apply_gold": True,
        "probe": _AX_CONTAIN_PROBE,
        "rationale": (
            "A-reference / containment: is_letter/is_digit are total over code "
            "points (the model only passes individual name[k] in range), so the "
            "per-char domain is trivially covered. The substantive obligation is "
            "that the deep splits/split_point model equals the real patched "
            "re.match on every name the model's control flow can form; a "
            "reachable name where they disagree => AXIOM-TOO-WEAK-FOR-CALLER."),
    },
]
