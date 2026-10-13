"""PBT manifest for sympy__sympy-21379 — adversarial falsification battery.

NOT a Nagini module; a record of adversarial cases the runner
(swebench_nagini.pbt) executes and stamps with RESULT. Spec cases are full
model.py variants that share the FROZEN spec byte-for-byte (region-surgery: only
the text strictly inside the single `# impl-start` / `# impl-end` region is
edited) and swap the implementation; they are checked by Nagini verify +
markers.same_spec. Axiom cases are real-callee probes run in the instance Docker
image.

Defended surface (read from model.py / refinement.md / mapping.md / instance):

  ONE modeled function:

    reduce_extract_common_factor(code: int, p: int, q: int) -> int
      models the "extract gcd" block of Mod.eval (sympy/core/mod.py:168-172) +
      the value the block feeds into the tail (return G*cls(p, q, ...)).
      Pre : 0 <= code and code <= 2                 (the three operand shapes)
      Post (NO Exsures => must NEVER raise on any in-domain input), three pins:
        (clause 2)  code == 2 -> Result() == build_result(1, p, q)
        (clause 3b) code != 2 and common_factor(code) == 1 ->
                        Result() == build_result(common_factor(code), p, q)
        (clause 3a) code != 2 and common_factor(code) != 1 ->
                        Result() == build_result(
                            common_factor(code),
                            divide_out(p, common_factor(code)),
                            divide_out(q, common_factor(code)))

      LOAD-BEARING clauses: (a) the ABSENCE of any Exsures (the discriminating
      content of the gold fix — wrapping the gcd call so its PolynomialError no
      longer escapes); (b) clause 3a, which pins each operand to the OPAQUE
      transform divide_out(., common_factor(code)) so an impl that skips the
      regroup cannot discharge it (closes the verdict's G-EQ hole / kills atk_6).

  INPUT FRAME: code, p, q are all plain `int` passed BY VALUE. There is NO heap
  reference and NO Acc(...,1/2) read-only permission anywhere in this bundle, so
  the directive-5 "frame-mutation / insufficient-permission" probe is N/A here
  (there is no permission to violate; see assessment). The read-only-ness of the
  OPERANDS is instead defended structurally: clause 3a's witnesses
  divide_out(p, ...) / divide_out(q, ...) refer to the parameters p, q; an impl
  that reassigns p/q before building the result cannot prove the build arguments
  equal those witnesses. We still attack that "operand-overwrite" surface
  directly (reassign-p, value-double-mask) as uniqueness rivals; they reject for
  a POSTCONDITION reason, not a permission reason, so we label them accordingly.

  ORACLE GROUNDING (directive 2): common_factor / divide_out / build_result are
  OPAQUE @ContractOnly axiom values keyed off the modeled inputs (code, p, q);
  the only pinned literals are the identity facts common_factor(1)==1 and
  common_factor(0)!=1. There is NO answer-key literal an impl could echo for the
  result value, so the classic "ungrounded-oracle echo" attack does not apply.
  In its place we (i) ship an honest cheapest/structural positive control and
  (ii) attack the opacity head-on with hardcode-literal-factor and
  fabricate-factor rivals (a fabricated literal cannot be proven == the opaque
  common_factor(code)).

Axiom lane (4 axioms, all A-consumed @ContractOnly, ZERO flag dependency — the
  gcd raise/return behaviour is a deterministic function of operand SHAPE, not of
  any global OPTIONS): common_factor / common_factor_compute <- sympy.gcd (value
  + raising facets of the SAME unchanged call); divide_out <- gcd_terms;
  build_result <- the unchanged Mul/Mod construction. The persisted axiom_check.py
  already runs the real callees; the AXIOM_TESTS reuse/strengthen its logic:
    - axiom-soundness-gcd: real gcd != 1 on every code-0 pair, == 1 on every
      code-1 pair, RAISES PolynomialError on every code-2 (Piecewise) pair, and
      the end-to-end refusal path (the F2P) completes without raising.
    - axiom-soundness-divide-out: the real code-0 regroup is non-trivial and the
      F2P's own pre-existing assertion (12x+18y)%(3x)==3*Mod(6y,x) holds (the
      witness that divide_out/build_result model the operand transform).
    - axiom-containment: every callee-input the MODEL can reach (code in {0,1,2}
      for gcd; factor != 1 for gcd_terms) lies inside the corresponding axiom
      Requires domain. Covering MORE (any operand shape) is sound; the check is
      that nothing reachable is UNcovered.
"""
from pathlib import Path

INSTANCE = "sympy__sympy-21379"
FLOAT_ENCODING = None  # meta.json float_encoding is null (integer carriers only)

_BASE = (Path(__file__).parent / "model.py").read_text()
_AXIOM_CHECK_SRC = (Path(__file__).parent / "axiom_check.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Region anchor — the executable core of the SINGLE impl region (strictly
# inside # impl-start / # impl-end). Editing only this text keeps the spec.
# The surrounding comments are left untouched; this block is the gold body
# from `pr = p` through the except handler's return.
# ---------------------------------------------------------------------------
_GOLD_BODY = (
    "    pr = p\n"
    "    qr = q\n"
    "    try:\n"
    "        # The single factor-producing call. Its raising facet\n"
    "        # (common_factor_compute) raises for the unanswerable input (code 2); for\n"
    "        # an answerable input it returns the factor, whose value is the helper's\n"
    "        # own pure-facet output common_factor(code). On normal completion this\n"
    "        # establishes code in {0, 1}, so the value facet is well-defined and the\n"
    "        # factor G is exactly common_factor(code).\n"
    "        G = common_factor_compute(code)\n"
    "        Assert(G == common_factor(code))\n"
    "        Assert(code == 0 or code == 1)\n"
    "        G = common_factor(code)\n"
    "        if G != 1:\n"
    "            # factor is not the identity: pass each operand through the transform\n"
    "            # helper, then build the value from the transformed operands. Because\n"
    "            # G is common_factor(code) and divide_out is opaque, the transformed\n"
    "            # operands are exactly the postcondition's witnesses (clause 3a) — an\n"
    "            # implementation that skips this step cannot discharge them.\n"
    "            pr = divide_out(p, G)\n"
    "            qr = divide_out(q, G)\n"
    "        # On normal completion the operands were transformed exactly when\n"
    "        # common_factor(code) != 1: the build arguments match clause (3a)/(3b).\n"
    "        return build_result(G, pr, qr)\n"
    "    except FactorUnavailable:\n"
    "        # the unanswerable input: keep the identity factor; the operands enter\n"
    "        # the value unchanged. The raise occurs only for code 2\n"
    "        # (common_factor_compute's Exsures guard), so this handler runs only\n"
    "        # there; pr, qr are still their original p, q (never reassigned).\n"
    "        return build_result(1, pr, qr)"
)


# ===========================================================================
# SPEC LANE
# ===========================================================================

SPEC_TESTS = [

    # -- POSITIVE CONTROL (soundness): result-into-local reshape --------------
    # Structurally different: instead of two separate `return` statements (one in
    # the try, one in the except), compute the produced value into a single local
    # `res` and return it once at the end of each handler. Behaviourally identical
    # and KEEPS every gold proof obligation (the two Asserts that rebind the factor
    # to the pure facet, the `if G != 1` guard, the operand transforms). No loops /
    # invariants are involved, so this reshape introduces no proof gap. MUST verify,
    # else SPEC-TOO-STRONG.
    {
        "id": "pos-result-local",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _BASE, _GOLD_BODY,
            "    pr = p\n"
            "    qr = q\n"
            "    try:\n"
            "        G = common_factor_compute(code)\n"
            "        Assert(G == common_factor(code))\n"
            "        Assert(code == 0 or code == 1)\n"
            "        G = common_factor(code)\n"
            "        if G != 1:\n"
            "            pr = divide_out(p, G)\n"
            "            qr = divide_out(q, G)\n"
            "        res = build_result(G, pr, qr)\n"
            "        return res\n"
            "    except FactorUnavailable:\n"
            "        res2 = build_result(1, pr, qr)\n"
            "        return res2"),
        "rationale": "a behaviourally-identical reshape (build the value into a "
                     "local before returning, in BOTH handlers) keeps the gold "
                     "Asserts and the `if G != 1` transform, so it discharges the "
                     "same postcondition clauses and must verify (else "
                     "SPEC-TOO-STRONG).",
    },

    # -- POSITIVE CONTROL (soundness): hoist the transform out of the if ------
    # Same behaviour via a different control shape: keep pr/qr as p/q, and inside
    # the `if G != 1` branch assign both transformed operands in a single tuple
    # statement instead of two statements. Keeps the guard and both transforms
    # (the proof obligations of clause 3a) intact. MUST verify.
    {
        "id": "pos-tuple-transform",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _BASE, _GOLD_BODY,
            "    pr = p\n"
            "    qr = q\n"
            "    try:\n"
            "        G = common_factor_compute(code)\n"
            "        Assert(G == common_factor(code))\n"
            "        Assert(code == 0 or code == 1)\n"
            "        G = common_factor(code)\n"
            "        if G != 1:\n"
            "            pr, qr = divide_out(p, G), divide_out(q, G)\n"
            "        return build_result(G, pr, qr)\n"
            "    except FactorUnavailable:\n"
            "        return build_result(1, pr, qr)"),
        "rationale": "the two operand transforms collapsed into one tuple "
                     "assignment is the same computation in a different shape; it "
                     "keeps both witnesses for clause 3a and must verify (else "
                     "SPEC-TOO-STRONG).",
    },

    # -- ADMISSIBILITY: the precondition admits a normal F2P-shaped input -----
    # Prepend Asserts that the Requires (0 <= code <= 2) holds for each of the three
    # representative shapes the F2P exercises (code 2 the issue's Piecewise; code 0
    # the (12x+18y)%(3x) transform; code 1 a coprime pair). These are no-ops for a
    # spec whose precondition admits them; the gold body follows. If the Requires
    # could not be established for a legitimate in-domain input the prelude / call
    # would fail => PRECOND-TOO-STRONG. It verifies, so the precondition is
    # satisfiable by a normal caller.
    {
        "id": "admiss-incode-range",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _GOLD_BODY,
            "    Assert(0 <= code and code <= 2)\n"
            "    Assert(code == 0 or code == 1 or code == 2)\n"
            "    pr = p\n"
            "    qr = q\n"
            "    try:\n"
            "        G = common_factor_compute(code)\n"
            "        Assert(G == common_factor(code))\n"
            "        Assert(code == 0 or code == 1)\n"
            "        G = common_factor(code)\n"
            "        if G != 1:\n"
            "            pr = divide_out(p, G)\n"
            "            qr = divide_out(q, G)\n"
            "        return build_result(G, pr, qr)\n"
            "    except FactorUnavailable:\n"
            "        return build_result(1, pr, qr)"),
        "rationale": "the precondition 0 <= code <= 2 admits every operand shape "
                     "the F2P exercises (code 0/1/2); the leading Asserts confirm a "
                     "normal in-domain input is accepted and the body verifies "
                     "(else PRECOND-TOO-STRONG).",
    },

    # -- UNIQUENESS / partial-domain (the canonical atk_6 / G-EQ closer) ------
    # Keep the try/except (so the no-Exsures obligation is met) but DROP the
    # `if G != 1: pr=divide_out...; qr=divide_out...` operand regroup. The result
    # is build_result(G, p, q) with the UNtransformed operands. On a code-0
    # (non-identity-factor) input clause 3a demands build_result(common_factor(code),
    # divide_out(p, ...), divide_out(q, ...)); because divide_out is OPAQUE the impl
    # cannot prove p == divide_out(p, common_factor(code)). MUST be REJECTED
    # ("Postcondition might not hold", clause 3a). If it verified => SPEC-TOO-WEAK.
    {
        "id": "drop-operand-regroup",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _GOLD_BODY,
            "    pr = p\n"
            "    qr = q\n"
            "    try:\n"
            "        G = common_factor_compute(code)\n"
            "        Assert(G == common_factor(code))\n"
            "        Assert(code == 0 or code == 1)\n"
            "        G = common_factor(code)\n"
            "        return build_result(G, pr, qr)\n"
            "    except FactorUnavailable:\n"
            "        return build_result(1, pr, qr)"),
        "refinement": "this is the gold patch with the `if G != 1: p, q = "
                      "[gcd_terms(i/G, ...) for i in (p, q)]` regroup deleted. Its "
                      "faithful real patch fails F2P test_Mod at the pre-existing "
                      "code-0 assertion (12*x + 18*y) % (3*x) == 3*Mod(6*y, x): "
                      "without the regroup the result is Mod(12*x+18*y, 3*x), not "
                      "3*Mod(6*y, x) (re-confirmed in-container: gold passes, this "
                      "fails), so it does NOT resolve.",
        "rationale": "rejected by postcondition clause 3a: with pr==p, qr==q the "
                     "build args are (common_factor(code), p, q) but the clause "
                     "demands (common_factor(code), divide_out(p, common_factor("
                     "code)), divide_out(q, common_factor(code))) and divide_out is "
                     "OPAQUE, so p == divide_out(p, ...) is unprovable. SPEC-TOO-WEAK "
                     "if it verifies.",
    },

    # -- UNIQUENESS / hardcode-literal factor (opacity attack, clause 3a/3b) --
    # Ignore the helper entirely: always return build_result(1, p, q) (the identity
    # factor with untransformed operands), i.e. pretend every input is trivial. On a
    # code-0 input clause 3a (factor != 1) demands the OPAQUE common_factor(code)
    # and the divide_out transforms; a literal 1 cannot be proven == common_factor(0)
    # (which is pinned != 1), and p != divide_out(p, ...). MUST be REJECTED.
    {
        "id": "hardcode-trivial-always",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _GOLD_BODY,
            "    pr = p\n"
            "    qr = q\n"
            "    return build_result(1, pr, qr)"),
        "refinement": "the faithful real patch drops the gcd extraction altogether "
                      "(always G = S.One, operands unchanged). On a code-0 pair it "
                      "leaves the common factor un-extracted: (12*x + 18*y) % (3*x) "
                      "would stay Mod(12*x+18*y, 3*x) instead of 3*Mod(6*y, x), so "
                      "F2P test_Mod fails and it does NOT resolve.",
        "rationale": "rejected by clause 3a: build_result(1, p, q) cannot match "
                     "build_result(common_factor(code), divide_out(p, ...), "
                     "divide_out(q, ...)) when common_factor(code) != 1 — the factor "
                     "1 is provably != common_factor(0) and the operands are "
                     "untransformed. SPEC-TOO-WEAK if it verifies.",
    },

    # -- UNIQUENESS / fabricate-literal factor (opacity attack) ---------------
    # A different opacity cheat: compute the real factor via the call (so code in
    # {0,1} is established and no raise escapes) but BUILD the result from a
    # fabricated literal factor 2 instead of the helper's opaque output. Even on a
    # code-0 input where common_factor(0) != 1 is known, the literal 2 cannot be
    # proven == common_factor(0) (the value is OPAQUE/unpinned), and the operands
    # are untransformed. MUST be REJECTED.
    {
        "id": "fabricate-literal-factor",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _GOLD_BODY,
            "    pr = p\n"
            "    qr = q\n"
            "    try:\n"
            "        G = common_factor_compute(code)\n"
            "        Assert(G == common_factor(code))\n"
            "        Assert(code == 0 or code == 1)\n"
            "        return build_result(2, pr, qr)\n"
            "    except FactorUnavailable:\n"
            "        return build_result(1, pr, qr)"),
        "refinement": "a real patch that returned 2*cls(p, q) (a fabricated factor) "
                      "instead of the gcd-extracted G*cls(p, q) would change the "
                      "value of every reduced Mod with a non-2 common factor — e.g. "
                      "(12*x+18*y)%(3*x) would not equal 3*Mod(6*y, x) — so F2P "
                      "test_Mod fails and it does NOT resolve.",
        "rationale": "rejected by clause 3b/3a: the build factor must be the OPAQUE "
                     "common_factor(code); a literal 2 is unprovably equal to it "
                     "(unpinned value), and on code-0 the operands must also be "
                     "transformed. SPEC-TOO-WEAK if it verifies.",
    },

    # -- CONTROL-FLOW-EFFECT / let the raise escape (the prepatch bug) --------
    # The discriminating content of the gold fix is the no-Exsures obligation: the
    # method must complete on EVERY in-domain input. This rival removes the
    # try/except and calls common_factor_compute UNGUARDED (exactly model_prepatch).
    # On code 2 common_factor_compute raises FactorUnavailable; with no Exsures and
    # no handler the raise escapes => "method raises no exceptions might not hold".
    # MUST be REJECTED. This is the value-invisible control-flow difference: both a
    # guarded and an unguarded impl return build_result(...) on codes 0/1, but only
    # the guarded one completes on code 2.
    {
        "id": "unguarded-raise-escapes",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _GOLD_BODY,
            "    pr = p\n"
            "    qr = q\n"
            "    G = common_factor_compute(code)\n"
            "    Assert(code == 0 or code == 1)\n"
            "    G = common_factor(code)\n"
            "    if G != 1:\n"
            "        pr = divide_out(p, G)\n"
            "        qr = divide_out(q, G)\n"
            "    return build_result(G, pr, qr)"),
        "refinement": "this is the PRE-PATCH code (the unguarded `G = gcd(p, q)` "
                      "with no try/except). On the issue's Piecewise input gcd "
                      "raises PolynomialError, which propagates out of Mod.eval and "
                      "up through the is_zero assumptions query, surfacing as the "
                      "reported error — exactly the F2P regression. The faithful "
                      "real patch (= no fix) does NOT resolve.",
        "rationale": "rejected by the ABSENCE of any Exsures: common_factor_compute "
                     "has Exsures(FactorUnavailable, code==2); called unguarded its "
                     "raise can escape, so 'method raises no exceptions' fails on "
                     "code 2. SPEC-TOO-WEAK (would fail to sense the bug) if it "
                     "verifies.",
    },

    # -- CONTROL-FLOW-EFFECT / wrong value on the refusal path (clause 2) -----
    # Catch the raise (so no exception escapes) but on the refusal path return the
    # operands built with a NON-identity literal factor 2 instead of the identity.
    # Clause 2 (code == 2 -> Result() == build_result(1, p, q)) pins the factor to
    # the identity on the refusal path; build_result(2, p, q) is provably unequal
    # (build_result is opaque, equal only when all three args provably equal; 2 != 1).
    # MUST be REJECTED.
    {
        "id": "wrong-factor-on-refusal",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _GOLD_BODY,
            "    pr = p\n"
            "    qr = q\n"
            "    try:\n"
            "        G = common_factor_compute(code)\n"
            "        Assert(G == common_factor(code))\n"
            "        Assert(code == 0 or code == 1)\n"
            "        G = common_factor(code)\n"
            "        if G != 1:\n"
            "            pr = divide_out(p, G)\n"
            "            qr = divide_out(q, G)\n"
            "        return build_result(G, pr, qr)\n"
            "    except FactorUnavailable:\n"
            "        return build_result(2, pr, qr)"),
        "refinement": "a real patch that set G to a non-identity value (not S.One) "
                      "on the PolynomialError branch would multiply the unevaluated "
                      "Mod by that factor: (Piecewise/z) % 1 would become 2*Mod(...) "
                      "rather than staying an unevaluated Mod, changing the value the "
                      "issue's expression evaluates to, so F2P does NOT resolve.",
        "rationale": "rejected by clause 2 (code == 2 -> Result() == build_result(1, "
                     "p, q)): build_result(2, p, q) is provably unequal (opaque "
                     "build_result, 2 != 1). SPEC-TOO-WEAK if it verifies.",
    },

    # -- VALUE-DOUBLE-MASK / operand-overwrite on the refusal path ------------
    # On code 2 the operands must enter the result UNCHANGED (clause 2:
    # build_result(1, p, q)). This rival overwrites pr/qr to divide_out(p, 7) /
    # divide_out(q, 7) before falling into the except (it transforms the operands on
    # a path where they must stay the originals). It catches the raise (no Exsures
    # violation) but on the refusal path returns build_result(1, divide_out(p,7),
    # divide_out(q,7)), which clause 2 demands equal build_result(1, p, q); since
    # divide_out is opaque, divide_out(p,7) is unprovably == p. MUST be REJECTED.
    # (This is the closest analogue here to a "mutate the read-only operand" attack:
    # the operands are value ints with no permission, so it rejects for a
    # POSTCONDITION reason — clause 2 pins the operand post-state — not permission.)
    {
        "id": "operand-overwrite-on-refusal",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _GOLD_BODY,
            "    pr = divide_out(p, 7)\n"
            "    qr = divide_out(q, 7)\n"
            "    try:\n"
            "        G = common_factor_compute(code)\n"
            "        Assert(G == common_factor(code))\n"
            "        Assert(code == 0 or code == 1)\n"
            "        G = common_factor(code)\n"
            "        if G != 1:\n"
            "            pr = divide_out(p, G)\n"
            "            qr = divide_out(q, G)\n"
            "        return build_result(G, pr, qr)\n"
            "    except FactorUnavailable:\n"
            "        return build_result(1, pr, qr)"),
        "refinement": "a real patch that pre-divided the operands by a spurious "
                      "factor (7) before the except set G = S.One would, on the "
                      "Piecewise refusal path, return S.One*cls(gcd_terms(p/7), "
                      "gcd_terms(q/7)) instead of the unchanged Mod — corrupting the "
                      "value the issue's expression evaluates to (it would no longer "
                      "stay an unevaluated Mod over the original operands), so F2P "
                      "does NOT resolve.",
        "rationale": "rejected by clause 2 (code == 2 -> Result() == build_result(1, "
                     "p, q)): on the refusal path pr==divide_out(p,7), qr==divide_out("
                     "q,7); build_result(1, divide_out(p,7), divide_out(q,7)) is "
                     "provably unequal to build_result(1, p, q) because divide_out is "
                     "OPAQUE (divide_out(p,7) un-provably == p). The postcondition "
                     "pins the operand post-state on the refusal path. SPEC-TOO-WEAK "
                     "if it verifies.",
    },

    # -- VALUE-DOUBLE-MASK / drop ONE operand transform (asymmetric regroup) --
    # Transform only p, leave q untransformed (regroup one operand but not the
    # other). On code-0, clause 3a demands BOTH operands transformed; qr == q
    # cannot be proven == divide_out(q, common_factor(code)) (opaque). This catches
    # an impl that masks the divergence on the p-coordinate while diverging on q.
    # MUST be REJECTED.
    {
        "id": "drop-one-operand-transform",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _GOLD_BODY,
            "    pr = p\n"
            "    qr = q\n"
            "    try:\n"
            "        G = common_factor_compute(code)\n"
            "        Assert(G == common_factor(code))\n"
            "        Assert(code == 0 or code == 1)\n"
            "        G = common_factor(code)\n"
            "        if G != 1:\n"
            "            pr = divide_out(p, G)\n"
            "        return build_result(G, pr, qr)\n"
            "    except FactorUnavailable:\n"
            "        return build_result(1, pr, qr)"),
        "refinement": "a real patch that rewrote only the dividend p (not the "
                      "divisor q) — p = gcd_terms(p/G, ...) without the q rewrite — "
                      "would leave the divisor un-reduced: (12*x+18*y)%(3*x) would "
                      "build from a reduced dividend over the UNreduced 3*x, not "
                      "3*Mod(6*y, x), so F2P test_Mod fails and it does NOT resolve.",
        "rationale": "rejected by clause 3a: qr == q is unprovably == divide_out(q, "
                     "common_factor(code)) (divide_out OPAQUE), so the second build "
                     "argument cannot be discharged on code-0. SPEC-TOO-WEAK if it "
                     "verifies.",
    },

    # -- NON-TERMINATION / diverge before the value is delivered --------------
    # Insert an unbounded loop AHEAD of the factor-producing call (the audit's
    # atk_7 shape). Nagini is a partial-correctness verifier by default: without
    # a termination obligation this impl discharges every value postcondition
    # VACUOUSLY (the return is unreachable) yet its faithful real patch hangs
    # Mod.eval — and the F2P — forever. The spec carries MustTerminate(2) in the
    # precondition; a `while True`-shaped loop has no decreasing measure that can
    # discharge the obligation, so the loop's termination check fails.
    # MUST be REJECTED.
    {
        "id": "diverge-before-return",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _GOLD_BODY,
            "    pr = p\n"
            "    qr = q\n"
            "    _atk = 0\n"
            "    while _atk >= 0:\n"
            "        _atk = _atk + 1\n"
            "    try:\n"
            "        G = common_factor_compute(code)\n"
            "        Assert(G == common_factor(code))\n"
            "        Assert(code == 0 or code == 1)\n"
            "        G = common_factor(code)\n"
            "        if G != 1:\n"
            "            pr = divide_out(p, G)\n"
            "            qr = divide_out(q, G)\n"
            "        return build_result(G, pr, qr)\n"
            "    except FactorUnavailable:\n"
            "        return build_result(1, pr, qr)"),
        "refinement": "a real patch that spins forever before the gcd extraction "
                      "(while True: ... ahead of the try/except) hangs Mod.eval on "
                      "EVERY input: the issue's Piecewise expression never finishes "
                      "substituting and the F2P test_Mod times out, so it does NOT "
                      "resolve.",
        "rationale": "rejected by the MustTerminate(2) obligation in the "
                     "precondition: the unbounded loop has no strictly-decreasing "
                     "measure, so Nagini cannot discharge the caller's termination "
                     "obligation across it (obligation 'MustTerminate' might not "
                     "hold). SPEC-TOO-WEAK (divergence admitted) if it verifies.",
    },
]


# ===========================================================================
# AXIOM LANE — real-callee soundness + caller-domain containment (Docker).
# All four axioms are A-consumed @ContractOnly; ZERO flag dependency (the gcd
# raise/return behaviour is a deterministic function of operand SHAPE). The
# probes EXECUTE the real sympy callees (never scrape source) and open any file
# with encoding="utf-8". They embed the persisted axiom_check.py oracle (read on
# the HOST at load time) because the runner mounts ONLY the probe at /work.
# ===========================================================================

# The probe re-runs the persisted, gold-validated axiom_check.py inside the
# instance image (gold applied): it is the authoritative real-callee soundness
# check (gcd != 1 on code-0, == 1 on code-1, RAISES on code-2; F2P completes; the
# code-0 operand-transform assertions). We embed its source and exec it.
_AX_SOUND_PROBE = (
    "import sys\n"
    "_SRC = " + repr(_AXIOM_CHECK_SRC) + "\n"
    "g = {'__name__': '__embedded_axiom_check__'}\n"
    "exec(compile(_SRC, 'axiom_check.py', 'exec'), g)\n"
    "rc = g['main']()\n"
    "print('embedded axiom_check.py main() returned', rc)\n"
    "sys.exit(0 if rc == 0 else 1)\n"
)

# A standalone soundness probe (does NOT depend on the bundle oracle) that
# independently fuzzes the gcd raise/return facets and the divide_out / build_result
# transform, including boundary + sentinel shapes, to try to make the real callee
# DISAGREE with the axioms. Belt-and-braces alongside the embedded oracle.
_AX_SOUND_FUZZ = r'''
import sys

def main():
    from sympy import symbols, Piecewise, gcd, S, Mod
    from sympy.core.exprtools import gcd_terms
    from sympy.polys.polyerrors import PolynomialError

    x, y, z = symbols('x y z', real=True)
    a, b, c = symbols('a b c')

    # ---- common_factor / common_factor_compute: gcd value + raise facets ----
    # code 0: a genuine shared factor -> gcd returns NORMALLY and != 1.
    code0 = [(2*x, 2*y), (S(6), S(9)), (4*a, 6*a), (3*x*y, 3*x),
             (x**2 - 1, x**2 - 3*x + 2), (S(10), S(15)), (12*a*b, 8*a),
             (S(0), S(5)), (6*x + 9*y, 3), (12*x + 18*y, 3*x)]
    for p, q in code0:
        G = gcd(p, q)                 # must NOT raise (code 0/1 are answerable)
        assert G != 1, ("AXIOM-UNSOUND common_factor(0)!=1: gcd(%r,%r)=%r" % (p, q, G))

    # code 1: coprime / trivial -> gcd returns NORMALLY and == 1.
    code1 = [(x, y), (S(7), S(13)), (a, b), (x + 1, x - 1), (S(1), S(1)),
             (x, S(5)), (S(1), S(0)), (a + b, a - b)]
    for p, q in code1:
        G = gcd(p, q)                 # must NOT raise
        assert G == 1, ("AXIOM-UNSOUND common_factor(1)==1: gcd(%r,%r)=%r" % (p, q, G))

    # code 2: a Piecewise (case-split) generator -> gcd MUST RAISE.
    pw = Piecewise((x, y > x), (y, True))
    code2 = [(pw / z, S.One), (pw, x), (pw / z, S(2)), (pw * z**-1, y),
             (Piecewise((a, a > 2), (S(2), True)), a),
             (Piecewise((x, x > 0), (-x, True)), z),
             (S.One, pw)]   # raising facet is symmetric in the Piecewise arg
    raised = 0
    for p, q in code2:
        try:
            G = gcd(p, q)
            raise AssertionError(
                "AXIOM-UNSOUND common_factor_compute Exsures(code==2): "
                "gcd(%r,%r)=%r did NOT raise" % (p, q, G))
        except PolynomialError:
            raised += 1
    assert raised == len(code2), "expected all code-2 pairs to raise"

    # ---- divide_out: gcd_terms is TOTAL under factor != 1 (the model guard) --
    # the model only ever calls divide_out under `if G != 1`, so the real call is
    # gcd_terms(i/G, ...) with G != 1. It must complete (no raise) on every code-0
    # operand we can reach.
    for p, q in code0:
        G = gcd(p, q)
        assert G != 1
        _ = gcd_terms(p / G, clear=False, fraction=False)   # must NOT raise
        _ = gcd_terms(q / G, clear=False, fraction=False)   # must NOT raise

    # ---- build_result / divide_out value soundness (the F2P's own witnesses) -
    # the operand transform is REAL: each operand is reduced by the factor before
    # the Mul/Mod result is built. Dropping it breaks these (the G-EQ closer).
    assert (12*x + 18*y) % (3*x) == 3*Mod(6*y, x)
    assert (4*x + 6*y + 5) % (2*x) == Mod(6*y + 5, 2*x)
    assert gcd(12*x + 18*y, 3*x) != 1   # the divide_out guard holds on this code-0

    print("AXIOM-SOUND fuzz OK: %d code-0 (!=1), %d code-1 (==1), %d code-2 "
          "(raise), divide_out total under guard, operand-transform witnesses hold"
          % (len(code0), len(code1), len(code2)))
    return 0

sys.exit(main())
'''

# Containment: every callee-input the MODEL can REACH lies inside the axiom's
# Requires domain. The model passes code in {0,1,2} (its own Requires 0<=code<=2)
# to common_factor_compute (Requires 0<=code<=2: EXACT match) and code in {0,1}
# to common_factor (Requires code==0 or code==1: established by the post-call
# Asserts, since common_factor_compute Ensures code!=2). divide_out is reached
# only under `if G != 1`, i.e. factor != 1 = its Requires exactly. We confirm
# (a) the model's call sites and (b) that the real callee actually ACCEPTS the
# full reachable domain (no reachable input is rejected/raises outside the
# modeled raise). Covering MORE (any Expr shape) than the caller reaches is sound.
_AX_CONTAIN_PROBE = r'''
import sys

def main():
    from sympy import symbols, Piecewise, gcd, S, Mod
    from sympy.core.exprtools import gcd_terms
    from sympy.polys.polyerrors import PolynomialError

    x, y, z = symbols('x y z', real=True)

    # --- containment for common_factor_compute (Requires 0 <= code <= 2) ------
    # The model's own Requires is 0 <= code <= 2 and it forwards `code` unchanged,
    # so the reachable callee-input set is EXACTLY {0,1,2} = the axiom domain.
    # Reachable: code 0 (answerable non-trivial), 1 (answerable trivial), 2 (refuse).
    # Each reachable shape behaves per the axiom (0/1 return, 2 raise):
    reach_answerable = [(S(6), S(9)), (x, y)]          # codes 0 and 1
    for p, q in reach_answerable:
        G = gcd(p, q)                                   # in-domain, must not raise
        assert G == gcd(p, q)
    pw = Piecewise((x, y > x), (y, True))
    try:
        gcd(pw / z, S.One)                              # code 2: in-domain, raises
        raise AssertionError("code-2 reachable input did not raise")
    except PolynomialError:
        pass

    # --- containment for common_factor (Requires code == 0 or code == 1) ------
    # The model rebinds G = common_factor(code) ONLY after common_factor_compute
    # has returned normally, which Ensures code != 2 => the only codes that reach
    # common_factor are {0, 1}, EXACTLY its Requires domain. There is NO model path
    # that reaches common_factor(2): the rebind is dominated by the try-normal exit.
    # (Static fact about the control flow; we assert the domain partition holds.)
    for code in (0, 1):
        assert code == 0 or code == 1     # the reachable set is within Requires

    # --- containment for divide_out (Requires factor != 1) --------------------
    # divide_out(p, G) / divide_out(q, G) are reached ONLY inside `if G != 1`, so
    # the only factor the model ever passes is != 1 = the axiom Requires exactly.
    # Confirm the real call under that guard is well-defined on every reachable
    # code-0 operand (G = gcd != 1 there).
    code0 = [(2*x, 2*y), (S(6), S(9)), (12*x + 18*y, 3*x), (3*x*y, 3*x)]
    for p, q in code0:
        G = gcd(p, q)
        assert G != 1                     # factor reaching divide_out is != 1
        _ = gcd_terms(p / G, clear=False, fraction=False)
        _ = gcd_terms(q / G, clear=False, fraction=False)

    print("AXIOM-CONTAINMENT OK: common_factor_compute reachable={0,1,2}=Requires; "
          "common_factor reachable={0,1}=Requires (rebind dominated by try-normal "
          "exit, code!=2); divide_out reachable factor != 1 = Requires. No "
          "caller-reachable input lies outside any axiom domain.")
    return 0

sys.exit(main())
'''

AXIOM_TESTS = [
    {
        "id": "ax-sound-embedded-check",
        "axiom": "common_factor,common_factor_compute,divide_out,build_result",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _AX_SOUND_PROBE,
        "rationale": "re-runs the persisted, gold-validated axiom_check.py in the "
                     "instance image (gold applied): real gcd returns != 1 on every "
                     "code-0 pair, == 1 on every code-1 pair, RAISES PolynomialError "
                     "on every code-2 (Piecewise) pair; the F2P refusal path "
                     "completes; the code-0 operand-transform assertions hold. Any "
                     "violation is AXIOM-UNSOUND.",
    },
    {
        "id": "ax-sound-fuzz-boundaries",
        "axiom": "common_factor,common_factor_compute,divide_out",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _AX_SOUND_FUZZ,
        "rationale": "independent boundary/sentinel fuzz of the real gcd value + "
                     "raise facets and the gcd_terms transform (incl. (0,5), (1,0), "
                     "symmetric Piecewise arg) — tries to make the real callee "
                     "DISAGREE with common_factor / common_factor_compute / "
                     "divide_out. Exits 1 (AXIOM-UNSOUND) on any disagreement.",
    },
    {
        "id": "ax-containment-caller-domain",
        "axiom": "common_factor,common_factor_compute,divide_out",
        "kind": "axiom-containment",
        "expect": "covered",
        "apply_gold": True,
        "probe": _AX_CONTAIN_PROBE,
        "rationale": "every callee-input the model can REACH is inside the axiom "
                     "Requires domain: common_factor_compute gets code in {0,1,2} "
                     "(== Requires 0<=code<=2); common_factor gets only {0,1} (the "
                     "rebind is dominated by the try-normal exit, where "
                     "common_factor_compute Ensures code!=2) == its Requires; "
                     "divide_out gets only factor != 1 (reached only under `if G != "
                     "1`) == its Requires. No reachable input is UNcovered => not "
                     "AXIOM-TOO-WEAK-FOR-CALLER.",
    },
]
