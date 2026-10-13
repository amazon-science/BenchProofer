# properties.py — PBT falsification battery for sympy__sympy-21930.
#
# NOT a Nagini module. A manifest the runner (swebench_nagini.pbt) parses: each
# SPEC_TESTS case is a full model.py variant that shares the FROZEN spec
# (axioms/pure/pre/post-conditions + signatures) byte-for-byte and edits ONLY
# the impl regions (the text between # impl-start / # impl-end, which the
# spec_view elides — invariants are nested INSIDE impl, so they elide too). So
# same_spec is guaranteed by construction. Each case is checked by Nagini verify
# + markers.same_spec on the host.
#
# ---------------------------------------------------------------------------
# Defended surface (read from model.py / refinement.md / mapping.md / axiom_check.py):
#
#   render_token_a/b/c(body: List[int]) -> List[int]   (three byte-identical
#   renderers — AntiSymmetricTensor / CreateBoson / CreateFermion ._latex)
#
#   * `body` is READ-ONLY: Requires(Acc(list_pred(body), 1/2)) and
#     Ensures(Acc(list_pred(body), 1/2)).  => FRAME-MUTATION is MANDATORY.
#
#   * Each renderer carries Requires(MustTerminate(2)) — a total-correctness
#     obligation. A rival that diverges before returning (infinite loop) would
#     satisfy every value Ensures vacuously; the obligation system rejects any
#     loop lacking a decreasing termination measure. The gold copy loop
#     discharges it with Invariant(MustTerminate(len(body) - i + 1)).
#
#   * The LOAD-BEARING postcondition clause that pins the entire output:
#       Ensures(ToSeq(Result()) == grouped_token(ToSeq(body)))
#     where grouped_token is @Pure and FULLY GROUNDED in the arg:
#       grouped_token(body) = PSeq(LBRACE()) + body + PSeq(RBRACE())
#                           = PSeq(123) + body + PSeq(125)   ("{" + body + "}").
#     There is NO opaque answer-key / exact-marker oracle to echo wrong — the
#     oracle unfolds to a function of the input, so "ungrounded-oracle echo" is
#     N/A. The honest cheapest correct impl (build "{" + body + "}") is used as
#     the positive control instead (see 'assessment').
#
#   * Four redundant supporting clauses sharpen the shape: len == len(body)+2,
#     Result()[0] == LBRACE(), Result()[len-1] == RBRACE(), and
#     Forall e: appended_super_is_outer(Result(), e)  (Result() ends in "}").
#     The last is the POWER-SAFETY clause: the wrap exists so an appended
#     exponent superscript binds to the whole "{...}" group rather than
#     colliding with the body's interior "^" (issue 19661).
#
#   * The bug being fixed is the MISSING outer braces: prepatch returns the bare
#     body ("b^\dagger_{i}"), gold returns "{b^\dagger_{i}}". The F2P tests
#     (test_create/test_create_f/test_NO/test_commutation/test_Tensors/
#     test_issue_19661) assert the braced form. So any rival that drops a brace,
#     drops a body char, or wraps with a wrong delimiter renders a wrong LaTeX
#     string and FAILS those assertions — that is the refinement for each reject.
#
#   * No @ContractOnly axioms (axioms region empty). grouped_token and
#     appended_super_is_outer are DEEP A-reference models validated == the real
#     SymPy LaTeX printer out-of-band by axiom_check.py (G-AX). The axiom lane
#     re-runs that real-callee check as an axiom-soundness probe. There is no
#     axiom-containment case: no consumed axiom whose Requires domain could be
#     under-scoped (see the AXIOM LANE note).
# ---------------------------------------------------------------------------

from pathlib import Path

INSTANCE = "sympy__sympy-21930"
FLOAT_ENCODING = None  # meta.json float_encoding is null (unused)

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap_all(src, old, new):
    """Replace ALL occurrences of `old` (the three byte-identical impl regions)
    so the variant is uniform across render_token_a/b/c. Asserts exactly three
    sites exist (drift guard)."""
    n = src.count(old)
    if n != 3:
        raise AssertionError("expected 3 sites, found %d for %r" % (n, old))
    return src.replace(old, new)


def _swap_first(src, old, new):
    """Replace only the FIRST occurrence (used to inject a single module-level
    admissibility caller into render_token_a's elided impl span)."""
    if old not in src:
        raise AssertionError("drift: %r" % (old,))
    return src.replace(old, new, 1)


# The gold impl region (appears 3x, one per renderer):
#     result = [LBRACE()]  # type: List[int]
#     i = 0
#     while i < len(body):
#         <invariants>
#         result.append(body[i])
#         i = i + 1
#     result.append(RBRACE())
#     return result
_GOLD_INIT = "    result = [LBRACE()]  # type: List[int]"
_GOLD_TAIL = "    result.append(RBRACE())\n    return result\n    # impl-end"
_GOLD_LOOPHEAD = "    while i < len(body):"
_GOLD_LOOPBODY = "        result.append(body[i])\n        i = i + 1"


# ===========================================================================
# 1. POSITIVE CONTROL (soundness) — structurally DIFFERENT but CORRECT.
# The gold seeds the open brace as a list literal `result = [LBRACE()]`. This
# variant instead starts from an EMPTY list and APPENDS the open brace as an
# explicit statement before the loop. Same forward copy loop, same gold
# invariants kept VERBATIM (so the proof obligations still discharge — pilot
# bug #2 avoided), same trailing `}` append. Produces the identical
# "{" + body + "}" for every body, so == grouped_token(ToSeq(body)) holds.
# A local-variable / statement reshape (NOT a loop-direction flip against the
# front-recursive `PSeq(LBRACE()) + take(i)` invariant — pilot bug #3 avoided).
# Must VERIFY (else SPEC-TOO-STRONG).
# ===========================================================================
_POS = _swap_all(
    _BASE,
    _GOLD_INIT + "\n    i = 0",
    "    result = []  # type: List[int]\n"
    "    result.append(LBRACE())\n"
    "    i = 0",
)


# ===========================================================================
# 2. ADMISSIBILITY — a fresh module-level caller injected into render_token_a's
# elided impl span (between `return result` and the terminal `# impl-end`, so
# spec_signature is untouched). It constructs an F2P-shaped body — the code
# points of `b^\dagger_{i}` = [98,94,...] carrying the interior `^` (94) — that
# the real CreateBoson._latex wraps, establishes the Requires (a fresh local
# list owns full list_pred, > 1/2), calls render_token_a, and asserts the
# output equals grouped_token(body) and ends in `}`. Must VERIFY (else
# PRECOND-TOO-STRONG: the precondition would be rejecting a legitimate input).
# ===========================================================================
_ADMISS = _swap_first(
    _BASE,
    "    result.append(RBRACE())\n    return result\n    # impl-end",
    "    result.append(RBRACE())\n"
    "    return result\n"
    "\n"
    "\n"
    "def _admiss_caller() -> None:\n"
    "    # F2P-shaped body: code points of `b^\\dagger_{i}` (carries the\n"
    "    # interior `^` = 94 that motivates the wrap).\n"
    "    body = [98, 94, 92, 100, 97, 103, 103, 101, 114, 95,\n"
    "            123, 105, 125]  # type: List[int]\n"
    "    out = render_token_a(body)\n"
    "    # the wrap is exactly the body as one group, and ends in `}`.\n"
    "    Assert(ToSeq(out) == grouped_token(ToSeq(body)))\n"
    "    Assert(len(out) == len(body) + 2)\n"
    "    Assert(ToSeq(out)[0] == LBRACE())\n"
    "    Assert(ToSeq(out)[len(out) - 1] == RBRACE())\n"
    "    Assert(appended_super_is_outer(ToSeq(out), ToSeq(body)))\n"
    "    # impl-end",
)


# ===========================================================================
# 3a. FRAME-MUTATION (uniqueness, MANDATORY — body is Acc(list_pred(body),1/2)).
# A rival that WRITES the read-only `body` input via an indexed store inside the
# loop (a self-write body[i] = body[i]). Under only Acc(list_pred(body), 1/2)
# Nagini has INSUFFICIENT PERMISSION for a store, so it MUST reject. All gold
# invariants/appends are kept verbatim, so the rejection is attributable to the
# write, not a proof gap. A byte-fuzzer never constructs this — it is the
# project's #1 weakness class.
# ===========================================================================
_FRAME_STORE = _swap_all(
    _BASE,
    _GOLD_LOOPBODY,
    "        body[i] = body[i]  # frame violation: store into a 1/2-perm input\n"
    "        result.append(body[i])\n"
    "        i = i + 1",
)


# 3b. FRAME-MUTATION on the same read-only input via append. A rival that grows
# `body` (body.append(RBRACE())) before reading it — also requires full
# list_pred permission, which the 1/2 fraction does not grant. Same
# insufficient-permission rejection; a second, structurally-distinct frame
# attack (mutating method rather than indexed store).
_FRAME_APPEND = _swap_all(
    _BASE,
    _GOLD_INIT + "\n    i = 0",
    "    result = [LBRACE()]  # type: List[int]\n"
    "    body.append(RBRACE())  # frame violation: append onto a 1/2-perm input\n"
    "    i = 0",
)


# ===========================================================================
# 4. PARTIAL-DOMAIN (uniqueness) — DROP THE CLOSING BRACE. This is the literal
# bug the gold patch fixes (the body is emitted WITHOUT being closed into a
# group). The open brace and the whole body are still correct, so the impl is
# correct on the prefix; it diverges only at the final delimiter. Must REJECT.
# Rejection sources (multiple): ToSeq(Result()) == grouped_token(...) (missing
# the trailing `}`), len == len(body)+2 (off by one), Result()[len-1]==RBRACE()
# (last is the last body char, not `}`), and — critically — the power-safety
# clause Forall e: appended_super_is_outer(Result(), e) (Result() no longer
# ends in `}`, so an appended exponent would collide with the interior `^`).
# ===========================================================================
_PARTIAL_NO_CLOSE = _swap_all(
    _BASE,
    "    result.append(RBRACE())\n    return result\n    # impl-end",
    "    return result\n    # impl-end",
)


# 4b. PARTIAL-DOMAIN — DROP THE LAST BODY CHARACTER (loop stops one early). On an
# EMPTY body this yields the correct "{}" (so it is correct on the empty
# sub-domain), but on every non-empty body the last body char is missing, so the
# rendered token is e.g. "{b^\dagger_{i}}" -> "{b^\dagger_{i}" + "}" with the
# `}` of `_{i}` dropped — a wrong LaTeX string. Must REJECT on
# == grouped_token(...) and len == len(body)+2. (Length-class / last-element
# partial-domain — the class a byte-fuzzer cannot target by construction.)
_PARTIAL_DROP_LAST = _swap_all(
    _BASE,
    _GOLD_LOOPHEAD,
    "    while i < len(body) - 1:",
)


# 4c. PARTIAL-DOMAIN — WRONG OPENING DELIMITER. Open the group with `^` (CARET,
# already in the contract's vocabulary) instead of `{`. Body and closing `}` are
# correct, so it is a single-element divergence at index 0. Must REJECT on
# Result()[0] == LBRACE() and == grouped_token(...). Models a "fix" that emitted
# a stray superscript instead of a brace — which would render `^b^\dagger_{i}}`,
# failing every F2P latex assertion.
_PARTIAL_WRONG_OPEN = _swap_all(
    _BASE,
    "    result = [LBRACE()]  # type: List[int]",
    "    result = [CARET()]  # type: List[int]",
)


# ===========================================================================
# 5. PREPATCH WITNESS (uniqueness, supporting) — the bare body, NO braces. This
# is exactly model_prepatch.py's impl (the pre-fix behaviour: return the body
# verbatim). It is correct on NO operator (every operator's token is missing
# both braces). Must REJECT on every value clause. Kept as the G-DIFF witness
# inside the PBT battery; its faithful real patch is the unpatched `_latex`
# (`"b^\dagger_{%s}"`), which FAILS all six F2P tests — so it cannot resolve.
# The gold invariant references PSeq(LBRACE())+take(i); with the open brace gone
# the invariant must be relaxed to take(i) to stay a PROOF-valid prepatch
# (matching model_prepatch.py), so this variant edits the invariant too — still
# inside the elided impl region, same_spec preserved. It fails on the SPEC, not
# a proof gap: there is no `{` or `}` anywhere in Result().
# ===========================================================================
_PREPATCH = _swap_all(
    _BASE,
    "    result = [LBRACE()]  # type: List[int]\n"
    "    i = 0\n"
    "    while i < len(body):\n"
    "        # invariants-start\n"
    "        Invariant(Acc(list_pred(body), 1 / 2))\n"
    "        Invariant(Acc(list_pred(result)))\n"
    "        Invariant(0 <= i and i <= len(body))\n"
    "        Invariant(ToSeq(result) == PSeq(LBRACE()) + ToSeq(body).take(i))\n"
    "        # the copy loop consumes the caller's termination obligation with a\n"
    "        # strictly decreasing measure (len(body) - i), discharging\n"
    "        # MustTerminate(2) from the precondition.\n"
    "        Invariant(MustTerminate(len(body) - i + 1))\n"
    "        # invariants-end\n"
    "        result.append(body[i])\n"
    "        i = i + 1\n"
    "    result.append(RBRACE())\n"
    "    return result",
    "    result = []  # type: List[int]\n"
    "    i = 0\n"
    "    while i < len(body):\n"
    "        # invariants-start\n"
    "        Invariant(Acc(list_pred(body), 1 / 2))\n"
    "        Invariant(Acc(list_pred(result)))\n"
    "        Invariant(0 <= i and i <= len(body))\n"
    "        Invariant(ToSeq(result) == ToSeq(body).take(i))\n"
    "        # discharge the termination obligation identically, so the reject\n"
    "        # stays on the SPEC (grouped_token), not an obligation leak.\n"
    "        Invariant(MustTerminate(len(body) - i + 1))\n"
    "        # invariants-end\n"
    "        result.append(body[i])\n"
    "        i = i + 1\n"
    "    return result",
)


# ===========================================================================
# 6. VACUOUS NON-TERMINATION (uniqueness) — an impl that never returns. It
# opens the brace and then spins forever (while 0 <= i with i increasing), so
# every value postcondition is satisfiable only vacuously: no execution
# reaches the return. This is the exact spec-too-weak class the G-PANEL-1
# auditor exploited before the MustTerminate obligation was added (atk_9: an
# infinite `while True` loop verified against the value-only spec). Under
# Requires(MustTerminate(2)) the loop takes no termination obligation and has
# no decreasing measure, so Nagini's obligation system MUST reject it
# ("Obligation leak check failed"). The invariants are relaxed to what the
# spinning loop maintains — the reject must come from the obligation system,
# not a broken proof of a correct impl.
# ===========================================================================
_NONTERM = _swap_all(
    _BASE,
    "    result = [LBRACE()]  # type: List[int]\n"
    "    i = 0\n"
    "    while i < len(body):\n"
    "        # invariants-start\n"
    "        Invariant(Acc(list_pred(body), 1 / 2))\n"
    "        Invariant(Acc(list_pred(result)))\n"
    "        Invariant(0 <= i and i <= len(body))\n"
    "        Invariant(ToSeq(result) == PSeq(LBRACE()) + ToSeq(body).take(i))\n"
    "        # the copy loop consumes the caller's termination obligation with a\n"
    "        # strictly decreasing measure (len(body) - i), discharging\n"
    "        # MustTerminate(2) from the precondition.\n"
    "        Invariant(MustTerminate(len(body) - i + 1))\n"
    "        # invariants-end\n"
    "        result.append(body[i])\n"
    "        i = i + 1\n"
    "    result.append(RBRACE())\n"
    "    return result",
    "    result = [LBRACE()]  # type: List[int]\n"
    "    i = 0\n"
    "    while 0 <= i:\n"
    "        # invariants-start\n"
    "        Invariant(Acc(list_pred(body), 1 / 2))\n"
    "        Invariant(Acc(list_pred(result)))\n"
    "        Invariant(0 <= i)\n"
    "        # invariants-end\n"
    "        i = i + 1\n"
    "    result.append(RBRACE())\n"
    "    return result",
)


SPEC_TESTS = [
    {
        "id": "pos-control-empty-init-append-open",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS,
        "rationale": (
            "structurally-different CORRECT impl: starts from an empty list and "
            "APPENDS the open brace as an explicit statement before the loop "
            "(vs the gold list-literal seed `[LBRACE()]`), keeping the SAME "
            "forward copy loop and the SAME gold invariants verbatim. Produces "
            "the identical `{`+body+`}` so ToSeq(Result())==grouped_token(...) "
            "and every supporting clause still holds; the front-recursive "
            "invariant PSeq(LBRACE())+take(i) is preserved (no f(a+b) lemma "
            "needed — pilot bugs #2/#3 avoided). Must verify else SPEC-TOO-STRONG."
        ),
    },
    {
        "id": "admiss-f2p-bdagger-body",
        "kind": "admissibility",
        "expect": "verify",
        "module": _ADMISS,
        "rationale": (
            "a contract-free caller (_admiss_caller, injected into render_token_a's "
            "elided impl span so spec_signature is untouched) builds an F2P-shaped "
            "body — the code points of `b^\\dagger_{i}` carrying the interior `^` "
            "(94) — from a fresh local (full list_pred > 1/2 establishes the "
            "Requires), calls render_token_a, and asserts the output is "
            "grouped_token(body), length body+2, opens `{`, ends `}`, and is "
            "power-safe. If the precondition cannot be established for this normal "
            "input => PRECOND-TOO-STRONG."
        ),
    },
    {
        "id": "frame-mutation-store-body",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _FRAME_STORE,
        "refinement": (
            "the rival writes the read-only `body` (body[i]=body[i]) — a faithful "
            "real patch CANNOT mutate the operator's intrinsic rendering string in "
            "place to make the postcondition hold; the real `_latex` builds its "
            "return by `%`-formatting `self.state.name`/`self.symbol`, it does not "
            "rewrite the body buffer. A patch that did so would not produce the "
            "gold `{body}` token and would FAIL the six F2P latex assertions, so it "
            "does NOT resolve. A verifying rival here would be a true "
            "verify-without-resolve break."
        ),
        "rationale": (
            "MUST reject for INSUFFICIENT PERMISSION: Requires/Ensures/Invariant "
            "hold only Acc(list_pred(body), 1/2) (read-only), so the indexed store "
            "body[i]=... is not permitted. Rejection source: the fractional-"
            "permission system, NOT the value postcondition. (MANDATORY frame-"
            "mutation case — the read-only input is present; a byte-fuzzer never "
            "constructs it.)"
        ),
    },
    {
        "id": "frame-mutation-append-body",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _FRAME_APPEND,
        "refinement": (
            "the rival grows the read-only `body` (body.append(RBRACE())). A "
            "faithful real patch cannot append to the operator's intrinsic body "
            "buffer; doing so would lengthen the rendered token (an extra `}` "
            "inside the group), producing a wrong LaTeX string that fails the F2P "
            "assertions — so it does NOT resolve."
        ),
        "rationale": (
            "MUST reject for INSUFFICIENT PERMISSION: only Acc(list_pred(body), "
            "1/2) is held, so the mutating method append() is not permitted. "
            "Rejection source: the fractional-permission system. Second, "
            "structurally-distinct frame attack (mutating method vs indexed store)."
        ),
    },
    {
        "id": "partial-drop-closing-brace",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _PARTIAL_NO_CLOSE,
        "refinement": (
            "this is the EXACT bug the gold patch fixes: the body is emitted but "
            "never closed into a group, so the token is `{b^\\dagger_{i}` (missing "
            "the outer `}`). The faithful real patch is the unpatched (or "
            "half-patched) `_latex` that prepends `{` but not `}` — it renders a "
            "token that is NOT the gold `{b^\\dagger_{i}}`, failing test_create / "
            "test_create_f / test_Tensors AND breaking power-safety (issue 19661), "
            "so it does NOT resolve."
        ),
        "rationale": (
            "MUST reject on FOUR clauses: ToSeq(Result())==grouped_token(...) "
            "(missing trailing `}`), len==len(body)+2 (off by one), "
            "Result()[len-1]==RBRACE() (last is the last body char), and the "
            "power-safety Forall e: appended_super_is_outer(Result(), e) "
            "(Result() no longer ends in `}`, so an appended exponent collides "
            "with the interior `^`). Rejection source: the load-bearing postcond."
        ),
    },
    {
        "id": "partial-drop-last-body-char",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _PARTIAL_DROP_LAST,
        "refinement": (
            "the loop stops one element early (i < len(body)-1), so the last body "
            "character is dropped. On an EMPTY body it still yields `{}` (correct "
            "there), but on every non-empty operator body it renders e.g. "
            "`{b^\\dagger_{i}` minus the `}` of the subscript — a wrong LaTeX "
            "string that fails the F2P latex equality assertions; the faithful "
            "patch (a truncated body interpolation) does NOT resolve."
        ),
        "rationale": (
            "MUST reject on ToSeq(Result())==grouped_token(...) and "
            "len(Result())==len(body)+2: after the short loop the result holds "
            "len(body)-1+2 = len(body)+1 elements for any non-empty body. Last-"
            "element / length-class partial-domain — a byte-fuzzer cannot target "
            "this sub-domain split by construction."
        ),
    },
    {
        "id": "partial-wrong-opening-delimiter",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _PARTIAL_WRONG_OPEN,
        "refinement": (
            "opens the group with `^` (CARET) instead of `{`. A faithful patch "
            "that emitted a stray superscript marker instead of a brace would "
            "render `^b^\\dagger_{i}}`, which is not the gold `{b^\\dagger_{i}}` "
            "and fails every F2P latex assertion (and is itself a double-superscript "
            "malformation), so it does NOT resolve."
        ),
        "rationale": (
            "MUST reject on Result()[0]==LBRACE() (element 0 is CARET()=94, not "
            "LBRACE()=123) and ToSeq(Result())==grouped_token(...). Single-element "
            "divergence at index 0 — a value-level head-element partial-domain. "
            "Rejection source: the head-delimiter postcondition clause."
        ),
    },
    {
        "id": "vacuous-nonterminating-loop",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _NONTERM,
        "refinement": (
            "the rival never returns: it spins in an unbounded loop after "
            "opening the brace, so every value postcondition holds only "
            "vacuously and no rendered token is ever delivered. Its faithful "
            "real patch is a `_latex` that hangs — sympy.latex(op) would never "
            "return, every F2P test times out/fails, so it does NOT resolve. "
            "This is the exact attack class (G-PANEL-1 atk_9, an infinite "
            "`while True` loop) that motivated the MustTerminate obligation."
        ),
        "rationale": (
            "MUST reject via the OBLIGATION system: the renderer's "
            "Requires(MustTerminate(2)) forces every loop on the path to the "
            "return to carry a decreasing termination measure; the spinning "
            "loop has none, so Nagini reports 'Obligation leak check failed'. "
            "Rejection source: the termination obligation, not a value clause "
            "— demonstrating the spec no longer admits vacuous divergence."
        ),
    },
    {
        "id": "prepatch-bare-body-no-braces",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _PREPATCH,
        "refinement": (
            "the prepatch behaviour verbatim: return the bare body with NO outer "
            "braces (the pre-fix `_latex` returning `\"b^\\dagger_{%s}\"`). Its "
            "faithful real patch is the unpatched method, which FAILS all six F2P "
            "tests (every assertion expects the braced `{...}` form) — it cannot "
            "resolve. Supporting G-DIFF witness inside the PBT battery."
        ),
        "rationale": (
            "MUST reject on every value clause: there is no `{` or `}` in "
            "Result(), so ToSeq(Result())==grouped_token(...), len==len(body)+2, "
            "Result()[0]==LBRACE(), Result()[len-1]==RBRACE() and the power-safety "
            "Forall all fail. The invariant is relaxed to take(i) (matching "
            "model_prepatch.py) so the failure is on the SPEC, not a proof gap — "
            "edit confined to the elided impl region, same_spec preserved."
        ),
    },
]


# ===========================================================================
# AXIOM LANE.
# meta.axioms == [] — there are NO @ContractOnly axioms in this bundle. The
# changed operation (the brace-wrap) and its interaction with the power printer
# are DEEP A-reference models: grouped_token(body) = "{"+body+"}" and
# appended_super_is_outer(token) (token ends in "}"). They are validated ==
# the REAL SymPy LaTeX printer out-of-band by axiom_check.py (G-AX).
#
# We re-run that real-callee soundness obligation here as a single
# axiom-soundness probe: the deep models must equal the real
# sympy.physics.secondquant._latex printer on the three changed operators, 8
# index-label fuzz variants, the power composites, and the exact issue-19661
# witness. If the real printer disagrees on any => AXIOM-UNSOUND.
#
# There is NO axiom-containment case: there is no CONSUMED axiom whose Requires
# domain could be under-scoped for the caller. The A-reference covers exactly
# what the model can reach — every operator the three modeled renderers stand
# for (each with an interior `^`), which is precisely the caller-reachable set.
#
# axiom_check.py imports only `sympy` (the library under change) and runs
# entirely in-container against the PATCHED sympy (apply_gold=True; the deep
# model describes post-gold behaviour). The probe embeds the HOST copy of
# axiom_check.py's source (read at manifest-load time per pilot bug #6 — the
# runner mounts ONLY the probe at /work, so model.py/axiom_check.py are not
# in-container) and executes its main(), exiting 0 iff every real-callee
# obligation holds. The probe CALLS the real callee (sp.latex) rather than
# scraping source (pilot bug #4) and opens nothing on disk (no codec issue,
# pilot bug #5).
# ===========================================================================
_AXIOM_CHECK_SRC = (Path(__file__).parent / "axiom_check.py").read_text(encoding="utf-8")

_AX_PROBE = (
    "import sys\n"
    "AXIOM_CHECK_SRC = " + repr(_AXIOM_CHECK_SRC) + "\n"
    "g = {'__name__': '__axiom_check__'}\n"
    "exec(compile(AXIOM_CHECK_SRC, 'axiom_check.py', 'exec'), g)\n"
    "rc = g['main']()\n"
    "print('axiom-soundness probe rc =', rc)\n"
    "sys.exit(0 if rc == 0 else 1)\n"
)

AXIOM_TESTS = [
    {
        "id": "ax-sound-grouped-token-and-power-safety-vs-real-printer",
        "axiom": "grouped_token / appended_super_is_outer (A-reference deep models)",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _AX_PROBE,
        "rationale": (
            "the deep models must equal the real SymPy LaTeX printer on the three "
            "changed operators (sp.latex(op) == grouped_token(intrinsic_body), "
            "interior `^` present, token opens `{`/ends `}`), on 8 index-label "
            "fuzz variants for the two creation operators, on the power composites "
            "(sp.latex(op**2) contains token+`^{2}` and NOT the malformed bare "
            "double-superscript body+`^{2}`), and on the exact issue-19661 witness "
            "sp.latex(Commutator(Bd(0)**2, B(0))) == "
            "r'- \\left[b_{0},{b^\\dagger_{0}}^{2}\\right]'. If the real callee "
            "disagrees on any => AXIOM-UNSOUND. Runs against patched sympy "
            "(apply_gold). Probe CALLS the real callee (pilot bug #4 avoided) and "
            "opens nothing on disk (pilot bug #5 avoided)."
        ),
    },
]
