# properties.py — PBT manifest for sympy__sympy-22080. NOT a Nagini module; a
# record of adversarial falsification cases. The runner (swebench_nagini.pbt)
# executes each and stamps RESULT.
#
# Spec cases are full model.py variants built by region-surgery: every variant
# is produced by _swap()-ing text that lies ENTIRELY inside an impl region
# (between `# impl-start` / `# impl-end`). The frozen spec (axioms/pure/pre/
# post-conditions + signatures) is never touched, so same_spec holds by
# construction. Each is checked by Nagini verify + markers.same_spec on the host.
#
# ---------------------------------------------------------------------------
# Defended surface (what THIS spec actually pins):
#
#   The gold patch fixes how the code-printers parenthesize a single negated
#   operand so it re-parses to the same value. Two independent sites:
#     Site A (precedence.py): a "%"/Mod operand re-binds exactly as tightly as a
#       "*"/Mul operand (precedence == PRECEDENCE["Mul"] == 50), not at the
#       pre-patch MRO fall-through level PRECEDENCE["Func"] == 70.
#     Site B (codeprinter.py _print_Mul single-factor leading-minus branch): the
#       one operand is parenthesized against the cut-off 0.5*(Pow+Mul) == 55
#       (strictly between Mul=50 and Pow=60) under the default strict=False
#       parenthesize predicate (wrap iff precedence(item) <= cut-off), not the
#       pre-patch level precedence(neg Mul) == Add == 40.
#
#   model.py carriers (all PURE data — int/bool; NO mutable / read-only inputs):
#     remainder_operand_level() -> int            [site A]   Ensures == 50
#     negated_single_operand_enclosed(lvl) -> bool[site B]   Ensures ==
#         encloses(lvl, leading_minus_cutoff(), False), PLUS two consequence
#         clauses: (lvl<=50 => True) and (lvl>=60 => False).
#     negated_remainder_is_enclosed() -> bool      [composite, illustrative]
#         Ensures == True.
#
#   The load-bearing clause of site B is the FULL `Result() == encloses(lvl, 55,
#   False)` equality — it pins the output on EVERY in-domain level 40..70, not
#   just the two consequence sub-domains (40..50 and 60..70). The interesting
#   adversarial gap is the BAND 51..59 (between Mul and Pow) and the cut-off
#   value 55 itself: the consequence clauses say NOTHING there; only the main
#   equality does. A rival that is correct on 40..50 and 60..70 but wrong inside
#   the band is the sharpest partial-domain attack and is exactly the kind a
#   byte-fuzzer never constructs.
#
#   FRAME-MUTATION: N/A. Every modeled function takes an int-by-value or no
#   argument and returns a pure value; there is no Acc(x,1/2) read-only input to
#   overwrite. has_readonly_input == False. (Documented in 'assessment'.)
#
#   UNGROUNDED-ORACLE ECHO: the postcondition references @Pure helpers
#   (encloses / leading_minus_cutoff / level_*), but they are fully-unfolded
#   integer constants grounded in the input `operand_level` — there is no opaque
#   answer-key to echo. `return encloses(operand_level, leading_minus_cutoff(),
#   False)` IS the correct gold impl, not a wrong echo. So instead of a wrong
#   echo we ship an honest cheapest-impl positive control (pos-control-echo).
# ---------------------------------------------------------------------------
from pathlib import Path

INSTANCE = "sympy__sympy-22080"
FLOAT_ENCODING = None  # meta.json float_encoding is null (int carrier is exact)

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- the three impl-region anchors (each unique, each strictly inside an
# ---- # impl-start / # impl-end block of model.py) -------------------------
_A_IMPL = "    return level_multiplicative()"                      # site A impl
_B_IMPL = "    return encloses(operand_level, leading_minus_cutoff(), False)"  # site B impl
_C_IMPL = ("    s = remainder_operand_level()\n"
           "    return negated_single_operand_enclosed(s)")        # composite impl


# ===========================================================================
# SPEC LANE
# ===========================================================================
SPEC_TESTS = [

    # -----------------------------------------------------------------------
    # POSITIVE CONTROL (soundness) — structurally-different but CORRECT site-B
    # impl. The gold writes `encloses(operand_level, leading_minus_cutoff(),
    # False)` directly. Here we instead inline the SAME boolean via the literal
    # @Pure helper bodies (encloses with non-strict: wrap iff operand_level <=
    # cutoff; cutoff is the midpoint), through a local variable rather than a
    # nested call. Same value on every in-domain input, different executable
    # shape. Must verify, else SPEC-TOO-STRONG. (No loop / no fold / no framing
    # assert is dropped — pitfalls #2/#3 do not apply: there is no loop here.)
    # -----------------------------------------------------------------------
    {
        "id": "pos-control-siteB-local",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _BASE, _B_IMPL,
            "    cut = leading_minus_cutoff()\n"
            "    res = operand_level <= cut  # non-strict encloses: wrap iff lvl <= cutoff\n"
            "    return res",
        ),
        "rationale": "a structurally-different but value-identical correct impl "
                     "(inlined non-strict encloses via a local) must verify; "
                     "else the postcondition is SPEC-TOO-STRONG. encloses(l,c,"
                     "False) == (l<=c) for all l,c, so this equals the gold value "
                     "on every input.",
    },

    # -----------------------------------------------------------------------
    # POSITIVE CONTROL (soundness, site A) — different executable shape that is
    # still exactly the Mul level. The gold returns level_multiplicative()
    # directly; here we bind it to a typed local first. Must verify.
    # -----------------------------------------------------------------------
    {
        "id": "pos-control-siteA-local",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _BASE, _A_IMPL,
            "    lvl = level_multiplicative()  # type: int\n"
            "    return lvl",
        ),
        "rationale": "site A reshaped through a typed local; same value (==50) so "
                     "Ensures(Result()==level_multiplicative()) and the strict "
                     "ordering still hold; must verify else SPEC-TOO-STRONG.",
    },

    # -----------------------------------------------------------------------
    # POSITIVE CONTROL / cheapest honest impl (the no-wrong-echo control demanded
    # by directive 2). Because the oracle is grounded, the cheapest impl that
    # satisfies the postcondition IS the correct one. We restate site B exactly
    # as the gold but using the explicit two-arg-strict spelling encloses(...,
    # False) -> via the equivalent `encloses` call with the cut-off recomputed
    # from the named levels. Must verify (positive control, not a defect).
    # -----------------------------------------------------------------------
    {
        "id": "pos-control-echo-grounded",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _BASE, _B_IMPL,
            "    return encloses(operand_level, (level_power() + level_multiplicative()) // 2, False)",
        ),
        "rationale": "the oracle is grounded in the input, so the cheapest impl "
                     "satisfying Ensures is the correct one; recomputing the "
                     "cut-off inline from the named levels (== leading_minus_"
                     "cutoff()) keeps the gold value. Must verify; documents that "
                     "there is no WRONG echo to build (no ungrounded answer-key).",
    },

    # -----------------------------------------------------------------------
    # ADMISSIBILITY — the precondition (40 <= operand_level <= 70) must accept a
    # normal F2P-shaped input. The composite calls negated_single_operand_
    # enclosed(remainder_operand_level()); remainder_operand_level() == 50 lies
    # in [40,70], so the precondition is established for the real F2P operand.
    # We make this explicit by asserting the level lies in-domain before the call
    # (keeps the gold composite value True). Must verify else PRECOND-TOO-STRONG.
    # -----------------------------------------------------------------------
    {
        "id": "admiss-composite-indomain",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _C_IMPL,
            "    s = remainder_operand_level()\n"
            "    Assert(level_additive() <= s and s <= level_function())  # F2P operand is in-domain\n"
            "    return negated_single_operand_enclosed(s)",
        ),
        "rationale": "the precondition of negated_single_operand_enclosed must "
                     "admit the real F2P operand (the remainder level 50). The "
                     "Assert discharges only because the spec proves 40<=50<=70; "
                     "if it could not, PRECOND-TOO-STRONG. Result stays True.",
    },

    # -----------------------------------------------------------------------
    # UNIQUENESS — PARTIAL-DOMAIN, the sharpest attack (the band 51..59). A rival
    # that is correct on the two pinned consequence sub-domains (lvl<=50 => True,
    # lvl>=60 => False) but DIVERGES inside the band against the load-bearing
    # equality. We compare against the additive level (40) instead of the cut-off
    # (55): for lvl in 51..55 the gold wraps (lvl<=55) but this leaves bare
    # (lvl>40 -> False) — WRONG. This is exactly model_prepatch.py's bug
    # (cut-off reverted to additive level), so its faithful real patch is the
    # PRE-PATCH printer that renders -(x % y) as '-x % y' and FAILS the F2P
    # test_PythonCodePrinter / test_create_expand_pow_optimization. Must REJECT
    # (fails the main Ensures equality); if it verified, SPEC-TOO-WEAK.
    # -----------------------------------------------------------------------
    {
        "id": "weak-siteB-cutoff-to-additive",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _B_IMPL,
            "    return encloses(operand_level, level_additive(), False)",
        ),
        "refinement": "this is the pre-patch behaviour (cut-off = additive level "
                      "40 = precedence(neg Mul)). Its faithful real patch leaves a "
                      "Mul/Mod-level negated operand bare, so pycode(-Mod(x,y)) == "
                      "'-x % y' and ccode(-x**4) == '-x*x*x*x' — it FAILS "
                      "test_PythonCodePrinter and test_create_expand_pow_"
                      "optimization. verify here would be a true verify-not-resolve.",
        "rationale": "rejected by the load-bearing Ensures(Result()==encloses("
                     "operand_level, leading_minus_cutoff(), False)): at "
                     "operand_level==50 the gold wraps (50<=55) but this leaves "
                     "bare (50>40 -> non-strict 50<=40 False), and the <=Mul=>True "
                     "consequence also fails. (= model_prepatch.py, G-DIFF.)",
    },

    # -----------------------------------------------------------------------
    # UNIQUENESS — PARTIAL-DOMAIN inside the band, the OTHER direction. A rival
    # that pushes the cut-off UP to the power level (60) instead of 55. It still
    # satisfies BOTH consequence clauses (lvl<=50 => 50<=60 True wrap; lvl>=60 =>
    # at 60 it now WRAPS, but the >=Pow=>False clause requires bare!). Actually
    # it already breaks the >=Pow clause at lvl==60; AND it breaks the main
    # equality at lvl in 56..60 (gold leaves bare, this wraps). So it is rejected
    # twice over. This catches a rival that "covers more" by over-wrapping power
    # operands — its faithful real patch would render -x**3 as '-(x**3)' (or
    # worse, -sin(x) wrapped) — a different rendering than the gold, and would
    # FAIL the regression P2P renderings (e.g. power/function operands must stay
    # bare). Must REJECT; if it verified, SPEC-TOO-WEAK.
    # -----------------------------------------------------------------------
    {
        "id": "weak-siteB-cutoff-to-power",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _B_IMPL,
            "    return encloses(operand_level, level_power(), False)",
        ),
        "refinement": "cut-off pushed to the power level (60). Its faithful real "
                      "patch wraps a power-level negated operand: -x**3 would "
                      "render '(-(x**3))'-style instead of staying bare, diverging "
                      "from the gold's intent that a power operand needs no parens; "
                      "the threshold must be strictly BELOW Pow. It also still "
                      "fails the precise -(x % y) / Mod re-parse boundary the gold "
                      "fixes only because 55<60, so a real patch with cut-off=60 "
                      "changes power-operand renderings and is NOT the gold; the "
                      "F2P/P2P printer tests pin power operands bare.",
        "rationale": "rejected by both the >=Pow=>False consequence (at "
                     "operand_level==60: 60<=60 non-strict wraps -> True, but "
                     "clause demands False) AND the main equality (gold encloses("
                     "l,55,False) is False for 56..60, this is True). Either kills "
                     "it.",
    },

    # -----------------------------------------------------------------------
    # UNIQUENESS — PARTIAL-DOMAIN, single-point divergence at the cut-off itself
    # (operand_level == 55, the most subtle band point). Use strict=True instead
    # of the default strict=False. encloses(l, 55, True) differs from encloses(l,
    # 55, False) ONLY at l == 55: non-strict wraps (55<=55 True), strict leaves
    # bare. Neither consequence clause touches l==55 (it is strictly between Mul
    # and Pow), so this rival passes BOTH consequences yet violates the main
    # equality at exactly one point. This is the value-proxy / single-point
    # partial-domain attack a fuzzer cannot target. Must REJECT.
    # -----------------------------------------------------------------------
    {
        "id": "weak-siteB-strict-flip",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _B_IMPL,
            "    return encloses(operand_level, leading_minus_cutoff(), True)",
        ),
        "refinement": "flips the default parenthesize mode to strict=True. The "
                      "real parenthesize is called with strict=False (the gold "
                      "passes no strict arg); a strict=True real patch would leave "
                      "an operand whose precedence EQUALS the cut-off bare, "
                      "changing the boundary rendering the gold fixes. It would "
                      "not reproduce the gold's exact '<=' boundary, so a real "
                      "patch using strict=True diverges on the equality case and "
                      "is not the gold fix.",
        "rationale": "rejected by the main Ensures(Result()==encloses(operand_"
                     "level, leading_minus_cutoff(), False)) at the single point "
                     "operand_level==55: encloses(55,55,True)==False but the spec "
                     "demands encloses(55,55,False)==True. Both consequence "
                     "clauses are silent at 55, so ONLY the load-bearing equality "
                     "catches it — the spec is tight precisely there.",
    },

    # -----------------------------------------------------------------------
    # UNIQUENESS — site A: remainder operand reverted to the function level (70),
    # i.e. the pre-patch MRO fall-through. This is model_prepatch_2.py. Must
    # REJECT (fails Ensures(Result()==level_multiplicative())).
    # -----------------------------------------------------------------------
    {
        "id": "weak-siteA-remainder-to-func",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _A_IMPL,
            "    return level_function()",
        ),
        "refinement": "= the pre-patch precedence (no 'Mod' entry -> MRO walks to "
                      "Function -> PRECEDENCE['Func']==70). Its faithful real "
                      "patch leaves precedence(Mod) at 70, so a leading-minus Mod "
                      "operand (70 > cut-off 55) stays BARE: pycode(-Mod(x,y)) == "
                      "'-x % y' — FAILS test_PythonCodePrinter. This is "
                      "model_prepatch_2.py (G-DIFF).",
        "rationale": "rejected by Ensures(Result()==level_multiplicative()): "
                     "70 != 50. Also breaks the strict-ordering Result()<"
                     "level_power() (70 < 60 is False).",
    },

    # -----------------------------------------------------------------------
    # UNIQUENESS — site A: remainder reverted to the ADDITIVE level (40). A
    # near-miss that still satisfies the strict-ordering lower bound's intent
    # superficially but is wrong: 40 != 50. SUPPORTING mechanical case, but it
    # carries a genuine refinement (a real patch assigning Mod precedence 40
    # would put Mod BELOW Mul, mis-rendering e.g. x*Mod(...) products). Must
    # REJECT.
    # -----------------------------------------------------------------------
    {
        "id": "weak-siteA-remainder-to-additive",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _A_IMPL,
            "    return level_additive()",
        ),
        "refinement": "a real patch assigning Mod precedence 40 (== Add) would "
                      "make a remainder operand bind LOOSER than multiplication, "
                      "mis-parenthesizing products of Mods and still over/under-"
                      "wrapping vs the gold's 'Mod binds like Mul'. It is not the "
                      "gold ('Mod': PRECEDENCE['Mul']==50) and would not reproduce "
                      "the gold renderings across the F2P/P2P printer suite.",
        "rationale": "rejected by Ensures(Result()==level_multiplicative()): "
                     "40 != 50. Also breaks the lower strict bound level_additive()"
                     " < Result() (40 < 40 is False).",
    },

    # -----------------------------------------------------------------------
    # UNIQUENESS — composite over-claim. Revert ONLY the composite impl so it
    # returns the OPPOSITE boolean (bare) while keeping both standalone functions
    # gold. Ensures(Result()==True) must catch it. This guards the F2P
    # observation -(x % y) (composite True == 'wrapped'). Must REJECT.
    # NOTE: the refinement is honest — the composite is illustrative, but a real
    # impl that left the negated remainder bare IS the bug under test.
    # -----------------------------------------------------------------------
    {
        "id": "weak-composite-bare",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _C_IMPL,
            "    s = remainder_operand_level()\n"
            "    return not negated_single_operand_enclosed(s)",
        ),
        "refinement": "returns 'bare' for the negated remainder operand — exactly "
                      "the pre-patch symptom pycode(-Mod(x,y)) == '-x % y' that "
                      "FAILS test_PythonCodePrinter (the F2P demands '-(x % y)', "
                      "i.e. enclosed == True).",
        "rationale": "rejected by Ensures(Result()==True): the composite must be "
                     "True (the F2P observation that the negated remainder is "
                     "enclosed); 'not ...' is False on the in-domain remainder "
                     "level.",
    },
]


# ===========================================================================
# AXIOM LANE
# ===========================================================================
# No @ContractOnly axiom is consumed (the model's `axioms` region is empty).
# The two deep encodings are A-references validated == the real callees by
# axiom_check.py / G-AX. We DO carry axiom-lane probes here as a re-runnable
# soundness + caller-domain-containment battery, executing the REAL sympy
# callees in the post-gold instance container (apply_gold=True). The probes are
# self-contained (import only sympy + stdlib), open files (none here) UTF-8, and
# do NOT depend on any bundle file being mounted in-container — each embeds its
# own logic. They CALL the real callee (precedence / the real printer); they
# never regex-scrape source.
# ===========================================================================

# Embed the host-side axiom_check.py source so the soundness probe reuses the
# exact validated oracle logic (directive 6: read it on the HOST at load time).
_AXIOM_CHECK_SRC = (Path(__file__).parent / "axiom_check.py").read_text(encoding="utf-8")


_PROBE_SOUND = r'''
import sys
# --- A-reference soundness: run the REAL sympy callees and assert they match
# --- the model's two deep encodings, on the post-gold tree. This reuses the
# --- bundle's own validated G-AX oracle, embedded verbatim below.
''' + _AXIOM_CHECK_SRC.replace(
    'if __name__ == "__main__":\n    sys.exit(main())',
    '''_rc = main()
print("PROBE axiom-soundness rc=", _rc)
sys.exit(0 if _rc == 0 else 1)''')


_PROBE_CONTAINMENT = r'''
import sys
# --- caller-domain containment: enumerate EXACTLY the operand precedences the
# --- model can feed to its site-B decision (negated_single_operand_enclosed)
# --- and assert each lies in the predicate's modeled domain [Add, Func] =
# --- [40,70], AND that the real printer is exercised across that full reachable
# --- band of strength classes so no reachable operand escapes the cut-off rule.
# ---
# --- The site-B predicate's Requires is level_additive() <= lvl <= level_
# --- function() (40..70). The model reaches site B only via the composite,
# --- which passes remainder_operand_level() == 50; the F2P/P2P renderings
# --- exercise operands at the real strength classes Add(40)/Mul=Mod(50)/
# --- Pow(60)/Func(70). We assert every such REAL precedence the caller can
# --- reach is inside [40,70] (containment) — a reachable operand outside would
# --- be AXIOM-TOO-WEAK-FOR-CALLER.
from sympy import Mod, symbols, sin, Symbol
from sympy.printing.precedence import PRECEDENCE, precedence

x, y = symbols('x y')

ADD, MUL, POW, FUNC = (PRECEDENCE["Add"], PRECEDENCE["Mul"],
                       PRECEDENCE["Pow"], PRECEDENCE["Func"])
assert (ADD, MUL, POW, FUNC) == (40, 50, 60, 70), (ADD, MUL, POW, FUNC)

LO, HI = ADD, FUNC  # the model's site-B Requires domain [40, 70]

# the operand precedences the caller (the real _print_Mul single-factor branch)
# can actually reach for the tested expressions: remainder, product, power,
# function operands. Read the REAL precedence for each (no scraping).
reachable = {
    "Mod(x,y)":  precedence(Mod(x, y)),     # site A operand, == Mul == 50 post-gold
    "x*y":       precedence(x * y),         # product operand, 50
    "x**3":      precedence(x ** 3),        # power operand, 60
    "sin(x)":    precedence(sin(x)),        # function operand, 70
}
bad = {k: v for k, v in reachable.items() if not (LO <= v <= HI)}
print("PROBE containment reachable operand precedences:", reachable)
if bad:
    print("AXIOM-TOO-WEAK-FOR-CALLER: reachable operands outside [%d,%d]: %r"
          % (LO, HI, bad))
    sys.exit(1)

# The remainder operand the composite actually passes is exactly 50, well inside
# the domain and at-or-below the cut-off 55 (so it wraps). Confirm.
assert reachable["Mod(x,y)"] == MUL, reachable["Mod(x,y)"]
assert reachable["Mod(x,y)"] <= (POW + MUL) // 2, "remainder must be <= cut-off 55"
print("PROBE containment OK: every caller-reachable operand precedence in [%d,%d]"
      % (LO, HI))
sys.exit(0)
'''


AXIOM_TESTS = [
    {
        "id": "ax-sound-deep-encodings",
        "axiom": "remainder_operand_level / negated_single_operand_enclosed (A-references)",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _PROBE_SOUND,
        "rationale": "the two deep encodings are A-references, not consumed "
                     "axioms; this runs the REAL sympy precedence table and the "
                     "REAL code printer (post-gold) and asserts precedence(Mod)=="
                     "PRECEDENCE['Mul'], the real cut-off 0.5*(Pow+Mul)==55 lies "
                     "strictly between Mul and Pow and equals the model midpoint, "
                     "the real printer's wrap decision matches the model on each "
                     "strength class, and all 6 F2P renderings verbatim. Any "
                     "disagreement => AXIOM-UNSOUND. Reuses the validated G-AX "
                     "oracle embedded verbatim.",
    },
    {
        "id": "ax-cover-siteB-domain",
        "axiom": "negated_single_operand_enclosed Requires [Add,Func]=[40,70]",
        "kind": "axiom-containment",
        "expect": "covered",
        "apply_gold": True,
        "probe": _PROBE_CONTAINMENT,
        "rationale": "every operand precedence the caller (the real single-factor "
                     "leading-minus branch) can actually reach — remainder/product"
                     " (50), power (60), function (70) — lies inside the model's "
                     "site-B Requires domain [40,70], and the remainder operand "
                     "the composite passes is exactly 50 (<= cut-off 55, so it "
                     "wraps). A reachable operand outside [40,70] would be "
                     "AXIOM-TOO-WEAK-FOR-CALLER.",
    },
]
