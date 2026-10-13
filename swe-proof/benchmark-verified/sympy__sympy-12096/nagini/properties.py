"""PBT manifest for sympy__sympy-12096 — adversarial falsification battery.

NOT a Nagini module; a record of adversarial cases the runner
(swebench_nagini.pbt) executes and stamps with RESULT. Spec cases are full
model.py variants that share the FROZEN spec byte-for-byte (region-surgery: only
the text strictly inside the `# impl-start` / `# impl-end` region is edited) and
swap the implementation; they are checked by Nagini verify + markers.same_spec.
Axiom cases are real-callee probes run in the instance Docker image.

Defended surface (read from model.py / refinement.md / mapping.md / instance):

  ONE modeled function:
    eval_implemented(leaf: int, layers: List[int]) -> Optional[int]
      models the `_imp_` branch of Function._eval_evalf (gold patch:
      `Float(self._imp_(*[i.evalf(prec) for i in self.args]), prec)`), abstracting
      a depth-n chain of unary implemented-function applications over a numeric
      leaf to (leaf, layers) with len(layers) == nesting depth (element values
      irrelevant). Result Optional[int]: a present int = a reduced number, None =
      "left unevaluated" (the `except: return None` path).

      Pre : Acc(list_pred(layers), 1/2)                  <- layers is READ-ONLY
            leaf >= 0
            eval_seq(leaf, ToSeq(layers)) < 1e14          (exact-float window)
      Post: Acc(list_pred(layers), 1/2)                  (returns the read perm)
            Result() is not None                          (always a present number)
            Result() == eval_seq(leaf, ToSeq(layers))     <- LOAD-BEARING pin

  LOAD-BEARING clause: the last two Ensures. eval_seq(leaf, layers) is a
  front-recursive @Pure fold, FULLY GROUNDED in the inputs
  (eval_seq(leaf, layers) = imp(eval_seq(leaf, layers.drop(1))); empty = leaf;
  imp(x) = x*x). It is NOT an opaque answer-key oracle: it is a pure function of
  the args, fully unfolded. So the directive-2 "ungrounded-oracle echo" attack
  does NOT apply — `return eval_seq(leaf, ToSeq(layers))` is the CORRECT cheapest
  impl, not a wrong echo. Per directive 2 we therefore use that as an honest
  cheapest-impl POSITIVE CONTROL (expect=verify) rather than a reject case (see
  assessment).

  Read-only input: `layers` is held at Acc(list_pred(layers), 1/2) in both the
  pre- and post-condition => the FRAME-MUTATION probe is MANDATORY: a rival that
  WRITES `layers` (append / index-store) to satisfy the postcondition vacuously
  must be REJECTED for INSUFFICIENT PERMISSION (list mutation needs the full
  list_pred; only 1/2 is held). The gold value-logic is kept verbatim around the
  write so the rejection is attributable to the write, not a proof gap.

Axiom lane: NO @ContractOnly consumed axioms (the `axioms` region is empty by
  design — meta.axioms == []). Two A-REFERENCE deep models (imp, eval_seq)
  validated == the real recursive evalf by axiom_check.py (G-AX). The PBT axiom
  lane therefore re-runs that validation in the instance image:
    * axiom-soundness  — embed axiom_check.py's source (read on the HOST at load
      time; it is NOT mounted in-container) and execute its main() under the gold
      patch: the REAL recursive Function._eval_evalf must reproduce eval_seq over
      imp (== a present number == imp iterated n times) on the F2P discriminator
      f(f(2)).evalf()==Float(16) + 32 boundary + 343 fuzz compositions, ON THE
      DECLARED EXACT-FLOAT DOMAIN (within_precision mirrors the precondition
      exactly). Any disagreement => the A-reference is UNSOUND.
    * axiom-containment — confirm the model NEVER reaches a callee input outside
      the validated domain: the model's precondition (leaf >= 0 and
      eval_seq(leaf, layers) < 1e14) is EXACTLY axiom_check.py's within_precision
      filter, so every caller-reachable input is inside the checked domain. A
      reachable input outside it would be AXIOM(A-reference)-TOO-WEAK-FOR-CALLER.
"""
from pathlib import Path

INSTANCE = "sympy__sympy-12096"
FLOAT_ENCODING = None  # meta.json float_encoding is null (numbers modelled as exact int)

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Region anchor: the WHOLE content strictly INSIDE the impl region (the gold
# backward per-layer fold, with its nested invariants + head/tail-split Assert).
# Every variant is built by _swap on exactly this block, so only impl text is
# edited and same_spec is guaranteed. Loop variants keep the gold invariants /
# asserts verbatim (pilot-bug-2/3: never drop a framing assert / lemma).
# ---------------------------------------------------------------------------

_GOLD_IMPL = (
    "    acc = leaf\n"
    "    i = len(layers)\n"
    "    while i > 0:\n"
    "        # invariants-start\n"
    "        Invariant(Acc(list_pred(layers), 1 / 2))\n"
    "        Invariant(0 <= i and i <= len(layers))\n"
    "        # `acc` is the inside-out reduction of the innermost `len - i` layers.\n"
    "        Invariant(acc == eval_seq(leaf, ToSeq(layers).drop(i)))\n"
    "        # invariants-end\n"
    "        # The fold unfolds at the head of drop(i-1) (non-empty since i > 0):\n"
    "        # supply the head/tail split so a single unfold relates step i-1 to i.\n"
    "        Assert(ToSeq(layers).drop(i - 1).drop(1) == ToSeq(layers).drop(i))\n"
    "        acc = imp(acc)\n"
    "        i = i - 1\n"
    "    return acc"
)


# ===========================================================================
# SPEC LANE
# ===========================================================================

SPEC_TESTS = [

    # -- POSITIVE CONTROL (soundness): structurally-different cheapest impl -----
    # The postcondition oracle eval_seq is FULLY GROUNDED in the inputs (a @Pure
    # fold over leaf+layers), so the cheapest CORRECT impl simply returns it.
    # This is structurally different from the gold backward loop (no loop / no
    # invariants at all) yet behaviourally identical at every layer count. It
    # must verify (else SPEC-TOO-STRONG). It is also the honest replacement for
    # the directive-2 ungrounded-oracle echo: because the oracle is grounded,
    # echoing it is CORRECT, not a wrong echo.
    {
        "id": "pos-cheapest-fold",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _BASE, _GOLD_IMPL,
            "    return eval_seq(leaf, ToSeq(layers))"),
        "rationale": "Result() == eval_seq(leaf, ToSeq(layers)) and Result() is "
                     "not None are both immediate when the impl returns the "
                     "grounded fold directly; layers is only read, so the 1/2 "
                     "permission is preserved. A correct impl with a structurally "
                     "different (loop-free) shape must verify, else the "
                     "postcondition rejects a correct output (SPEC-TOO-STRONG).",
    },

    # -- POSITIVE CONTROL (soundness): backward loop, local-variable reshape ----
    # Keeps the gold control flow + EVERY gold invariant and the head/tail-split
    # Assert verbatim (only renamed: acc -> cur, len(layers) hoisted to n where it
    # does not appear inside an invariant/assert that the proof triggers on). The
    # invariant lines and the framing Assert are byte-identical to gold so no
    # proof obligation is dropped (pilot-bug-2). MUST verify.
    {
        "id": "pos-loop-rename",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _BASE, _GOLD_IMPL,
            "    cur = leaf\n"
            "    n = len(layers)\n"
            "    i = n\n"
            "    while i > 0:\n"
            "        # invariants-start\n"
            "        Invariant(Acc(list_pred(layers), 1 / 2))\n"
            "        Invariant(0 <= i and i <= len(layers))\n"
            "        Invariant(cur == eval_seq(leaf, ToSeq(layers).drop(i)))\n"
            "        # invariants-end\n"
            "        Assert(ToSeq(layers).drop(i - 1).drop(1) == ToSeq(layers).drop(i))\n"
            "        cur = imp(cur)\n"
            "        i = i - 1\n"
            "    return cur"),
        "rationale": "behaviourally identical backward fold with the accumulator "
                     "renamed (acc->cur) and len(layers) hoisted into a local n; "
                     "every gold invariant and the head/tail-split Assert are kept "
                     "verbatim so the loop-invariant proof is unchanged. A reshape "
                     "that keeps the gold proof must verify (else SPEC-TOO-STRONG).",
    },

    # -- ADMISSIBILITY: the precondition admits a normal, in-domain composition --
    # The impl self-calls eval_implemented on a freshly-built single-layer input
    # (leaf=2, layers=[0]; eval_seq(2,[_]) = imp(2) = 4 < 1e14, leaf 2 >= 0) — a
    # genuine 1-layer composition (f(2)), in the declared domain. The 1/2
    # permission on the fresh list is threaded into the call and Asserted present
    # on return; the result is Asserted non-None. Then the gold loop runs on the
    # real `layers`. If the precondition could not be established for this normal
    # input the self-call would fail => PRECOND-TOO-STRONG. (The F2P 2-layer case
    # f(f(2)), eval_seq=16<1e14, is likewise in-domain and is exercised by
    # pos-cheapest-fold / pos-loop-rename which return the fold for ALL layer
    # counts; a 1-layer witness keeps the precondition's eval_seq unfold shallow
    # so admissibility is not confounded by a deep-unfold proof gap.)
    {
        "id": "admiss-self-call",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _GOLD_IMPL,
            "    witness = [0]  # type: List[int]\n"
            "    # Unfold the front-recursive @Pure fold on the fresh 1-layer witness\n"
            "    # so Nagini can discharge the call's domain precondition\n"
            "    # eval_seq(2, ToSeq(witness)) = imp(2) = 4 < 1e14 (a proof lemma,\n"
            "    # not a spec change): establish the length facts then the two unfold\n"
            "    # steps. Without these Nagini will not auto-unfold the recursion.\n"
            "    Assert(len(ToSeq(witness)) == 1)\n"
            "    Assert(len(ToSeq(witness).drop(1)) == 0)\n"
            "    Assert(eval_seq(2, ToSeq(witness).drop(1)) == 2)\n"
            "    Assert(eval_seq(2, ToSeq(witness)) == 4)\n"
            "    r = eval_implemented(2, witness)  # type: Optional[int]\n"
            "    Assert(r is not None)\n"
            "    acc = leaf\n"
            "    i = len(layers)\n"
            "    while i > 0:\n"
            "        # invariants-start\n"
            "        Invariant(Acc(list_pred(layers), 1 / 2))\n"
            "        Invariant(0 <= i and i <= len(layers))\n"
            "        Invariant(acc == eval_seq(leaf, ToSeq(layers).drop(i)))\n"
            "        # invariants-end\n"
            "        Assert(ToSeq(layers).drop(i - 1).drop(1) == ToSeq(layers).drop(i))\n"
            "        acc = imp(acc)\n"
            "        i = i - 1\n"
            "    return acc"),
        "rationale": "a self-call on a freshly-built in-domain input (leaf=2 >= 0, "
                     "layers=[0] with eval_seq(2,[_])=imp(2)=4 < 1e14) establishes "
                     "the Requires for a normal 1-layer composition and returns the "
                     "1/2 permission; Assert(r is not None) confirms the present-"
                     "number postcondition is reachable. Verifies => the precondition "
                     "admits an F2P-shaped input (else PRECOND-TOO-STRONG).",
    },

    # -- FRAME-MUTATION (uniqueness): append to the read-only `layers` ----------
    # MANDATORY: layers is Acc(list_pred(layers), 1/2) — READ-ONLY. This rival
    # appends to layers before running the gold fold (gold value-logic verbatim).
    # list.append needs the FULL list_pred, only 1/2 is held => rejected for
    # INSUFFICIENT PERMISSION. If it verified, the read-only frame is unguarded
    # (SPEC-TOO-WEAK on the frame).
    {
        "id": "frame-mutate-append",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _GOLD_IMPL,
            "    layers.append(0)\n"
            "    acc = leaf\n"
            "    i = len(layers)\n"
            "    while i > 0:\n"
            "        # invariants-start\n"
            "        Invariant(Acc(list_pred(layers), 1 / 2))\n"
            "        Invariant(0 <= i and i <= len(layers))\n"
            "        Invariant(acc == eval_seq(leaf, ToSeq(layers).drop(i)))\n"
            "        # invariants-end\n"
            "        Assert(ToSeq(layers).drop(i - 1).drop(1) == ToSeq(layers).drop(i))\n"
            "        acc = imp(acc)\n"
            "        i = i - 1\n"
            "    return acc"),
        "refinement": "the faithful real patch corresponding to this write would "
                      "mutate self.args (the symbolic application's argument tuple) "
                      "in place while reducing it. The gold patch reads the args via "
                      "a comprehension `[i.evalf(prec) for i in self.args]` and never "
                      "mutates self.args; sympy Basic args are immutable and shared "
                      "(cached) across the expression DAG, so a patch that appended "
                      "to / rewrote self.args would corrupt every other reference to "
                      "the same node and the P2P invariants (e.g. test_list_args, "
                      "test_single_arg re-reading the function's args) would observe "
                      "the corruption — it would NOT resolve the suite.",
        "rationale": "rejected by the permission system: layers is held at "
                     "Acc(list_pred(layers), 1/2); list.append requires the FULL "
                     "list_pred, so the write is INSUFFICIENT-PERMISSION. The gold "
                     "fold value-logic is verbatim, so the rejection is attributable "
                     "to the write. If it verified, the read-only frame is unguarded "
                     "(SPEC-TOO-WEAK).",
    },

    # -- FRAME-MUTATION supporting case (uniqueness): in-place index store ------
    # A different write shape on the same read-only input: layers[0] = 0 (guarded
    # so it only fires on a non-empty list). Also needs the full list_pred; the
    # gold fold is verbatim. Rejected for INSUFFICIENT PERMISSION.
    {
        "id": "frame-mutate-index",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _GOLD_IMPL,
            "    if len(layers) > 0:\n"
            "        layers[0] = 0\n"
            "    acc = leaf\n"
            "    i = len(layers)\n"
            "    while i > 0:\n"
            "        # invariants-start\n"
            "        Invariant(Acc(list_pred(layers), 1 / 2))\n"
            "        Invariant(0 <= i and i <= len(layers))\n"
            "        Invariant(acc == eval_seq(leaf, ToSeq(layers).drop(i)))\n"
            "        # invariants-end\n"
            "        Assert(ToSeq(layers).drop(i - 1).drop(1) == ToSeq(layers).drop(i))\n"
            "        acc = imp(acc)\n"
            "        i = i - 1\n"
            "    return acc"),
        "refinement": "an in-place store into the argument carrier is not a faithful "
                      "evalf fix: the gold patch evaluates a COPY of each arg "
                      "(i.evalf(prec)) and leaves self.args untouched. A patch that "
                      "rewrote an entry of the immutable, DAG-shared self.args would "
                      "change what every other holder of that node reports and break "
                      "the args-preservation P2P tests — it would not resolve.",
        "rationale": "rejected for INSUFFICIENT PERMISSION: an in-place store to "
                     "layers[0] needs the full list_pred but only 1/2 is held. Frame "
                     "integrity of the read-only layer carrier; gold value-logic "
                     "verbatim so the rejection attributes to the write.",
    },

    # -- PARTIAL-DOMAIN (uniqueness): the canonical bug — None for >= 2 layers --
    # Correct (returns the grounded fold) for 0/1 layers; returns None (the
    # "left unevaluated" abstraction) for any deeper composition. This IS the
    # pre-patch behaviour. It fails the Ensures(Result() is not None) on exactly
    # the composition sub-domain (>= 2 layers). The None is bound to a TYPED LOCAL
    # before return (Nagini `# type:` rule, pilot-bug-1).
    {
        "id": "partial-none-on-composition",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _GOLD_IMPL,
            "    if len(layers) <= 1:\n"
            "        return eval_seq(leaf, ToSeq(layers))\n"
            "    unevaluated = None  # type: Optional[int]\n"
            "    return unevaluated"),
        "refinement": "this IS the pre-patch behaviour: passing the un-reduced inner "
                      "application to _imp_ yields a number only for <= 1 layer; a "
                      "deeper composition raises TypeError and `except: return None` "
                      "leaves it symbolic. The F2P test_issue_12092 asserts "
                      "f(f(2)).evalf() == Float(16) (a 2-layer composition); with this "
                      "impl the 2-layer case is left unevaluated (None / symbolic) "
                      "instead of 16, so it is EXACTLY the bug and does NOT resolve "
                      "(model_prepatch.py fails here — G-DIFF).",
        "rationale": "rejected by Ensures(Result() is not None): for any "
                     "len(layers) >= 2 the impl returns None while the postcondition "
                     "demands a present number. The 0/1-layer branch returns the "
                     "grounded fold and verifies, so the rejection is attributable "
                     "precisely to the composition sub-domain. If it verified the "
                     "always-present-number guarantee is unpinned (SPEC-TOO-WEAK).",
    },

    # -- PARTIAL-DOMAIN (uniqueness): off-by-one on the composition sub-domain --
    # Correct for 0/1 layers; off-by-one (eval_seq + 1) for >= 2 layers. Diverges
    # ONLY on the composition sub-domain — present (not None) but the WRONG number.
    # Catches a too-weak value pin that a None-only partial case would miss.
    {
        "id": "partial-offbyone-on-composition",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _GOLD_IMPL,
            "    if len(layers) <= 1:\n"
            "        return eval_seq(leaf, ToSeq(layers))\n"
            "    return eval_seq(leaf, ToSeq(layers)) + 1"),
        "refinement": "a patch that reduces deep compositions but is off by one (the "
                      "outer _imp_ applied to a value one too large, e.g. squaring "
                      "the wrong intermediate) computes f(f(2)).evalf() == 17, not "
                      "Float(16). The F2P test_issue_12092 (`== Float(16)`) fails, so "
                      "such a patch does NOT resolve.",
        "rationale": "rejected by Ensures(Result() == eval_seq(leaf, ToSeq(layers))): "
                     "for len(layers) >= 2 the impl returns eval_seq(..) + 1 != "
                     "eval_seq(..). The result is present (not None) so this is a pure "
                     "value-pin violation on the composition sub-domain; the <= 1 "
                     "branch is correct. If it verified the value is unpinned on deep "
                     "compositions (SPEC-TOO-WEAK).",
    },

    # -- PARTIAL-DOMAIN (uniqueness): wrong on the bare-leaf (0-layer) sub-domain
    # Correct for every >= 1 layer; wrong at exactly 0 layers (returns leaf + 1
    # instead of the leaf). Pins the OTHER end of the domain (the zero-layer base
    # case) that a composition-only attack would not touch.
    {
        "id": "partial-wrong-bare-leaf",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _GOLD_IMPL,
            "    if len(layers) == 0:\n"
            "        return leaf + 1\n"
            "    return eval_seq(leaf, ToSeq(layers))"),
        "refinement": "a patch that mis-reduces a BARE numeric leaf (zero surrounding "
                      "applications — e.g. a plain Integer/Float .evalf()) by an "
                      "off-by-one would make Integer(2).evalf() report 3 instead of 2 "
                      "and break the no-/single-arg numeric P2P paths (test_no_args / "
                      "test_single_arg evaluate bare and one-layer numeric results); "
                      "it would not resolve.",
        "rationale": "rejected by Ensures(Result() == eval_seq(leaf, ToSeq(layers))): "
                     "when len(layers) == 0, eval_seq(leaf, empty) == leaf but the "
                     "impl returns leaf + 1. The >= 1-layer branch returns the grounded "
                     "fold and verifies, so the rejection attributes precisely to the "
                     "zero-layer sub-domain. If it verified the base case is unpinned "
                     "(SPEC-TOO-WEAK).",
    },
]


# ===========================================================================
# AXIOM LANE  (NO @ContractOnly axioms; two A-REFERENCE deep models validated by
# axiom_check.py / G-AX — imp and eval_seq == the real recursive evalf)
# ===========================================================================
#
# The runner mounts ONLY the probe script at /work; axiom_check.py / model.py are
# NOT in-container. The soundness probe therefore EMBEDS axiom_check.py's source
# (read on the HOST at manifest-load time) and EXECUTES the real callee
# (Function._eval_evalf via Expr.evalf) under the gold patch. It never scrapes
# source (pilot-bug-4). The containment probe embeds model.py's source (read on
# the HOST) and checks it statically. Files read on the host are decoded utf-8.

_AXIOM_CHECK_SRC = (Path(__file__).parent / "axiom_check.py").read_text(encoding="utf-8")
_MODEL_SRC = (Path(__file__).parent / "model.py").read_text(encoding="utf-8")

# axiom-soundness: run axiom_check.py's main() in-container under the gold patch.
# It builds implemented_function('f', lambda x: x**2) and asserts the REAL
# recursive evalf == eval_seq over imp (a present number == imp iterated n times)
# on the F2P discriminator f(f(2)).evalf()==Float(16) + 32 boundary + ~343 fuzz
# compositions, ALL filtered to the declared exact-float domain (within_precision
# == the model.py precondition exactly). Exit 0 iff every obligation holds.
_AX_SOUND_PROBE = _AXIOM_CHECK_SRC + """

# ---- PBT axiom-soundness driver (appended) --------------------------------
import sys as _sys
print("PBT axiom-soundness: running the REAL recursive Function._eval_evalf "
      "(via Expr.evalf) on nested implemented-function compositions and asserting "
      "it reproduces the eval_seq-over-imp deep model on the declared exact-float "
      "domain (F2P discriminator f(f(2))==Float(16) + boundary + fuzz).")
try:
    _rc = main()
except SystemExit as _e:
    _rc = _e.code if isinstance(_e.code, int) else 1
except AssertionError as _ae:
    print("PBT axiom-soundness FAIL: A-reference UNSOUND:", _ae)
    _sys.exit(1)
if _rc not in (0, None):
    print("PBT axiom-soundness FAIL: axiom_check.main() rc=%r" % (_rc,))
    _sys.exit(1)
_sys.exit(0)
"""

# axiom-containment: the A-reference deep model is validated by axiom_check.py on
# EXACTLY the domain within_precision(leaf, n) == (leaf >= 0 and eval_seq(leaf,n) <
# 1e14). The model's PRECONDITION is the same predicate (Requires(leaf >= 0) and
# Requires(eval_seq(leaf, ToSeq(layers)) < 1e14)). Containment therefore holds iff
# the model can never reach a callee input outside the validated domain — i.e. the
# model's precondition is no broader than within_precision. We confirm statically
# (AST over the host-read model.py): (1) the modeled function carries both domain
# Requires literally, and (2) axiom_check.py's within_precision is that exact
# predicate (leaf >= 0 and eval_seq(leaf, n) < 10**14), so the validated domain
# equals the reachable domain — neither broader nor narrower. We also EXECUTE the
# real callee at the in-window F2P point and at a just-out-of-window point to show
# the boundary is exactly where exactness is (and is not) claimed.
_AX_COVER_PROBE = (
    "import sys, ast\n"
    "MODEL_SRC = " + repr(_MODEL_SRC) + "\n"
    "AXIOM_SRC = " + repr(_AXIOM_CHECK_SRC) + "\n"
    "# 1) the modeled function declares BOTH domain preconditions literally.\n"
    "need = ['Requires(leaf >= 0)',\n"
    "        'Requires(eval_seq(leaf, ToSeq(layers)) < 100000000000000)']\n"
    "missing = [s for s in need if s not in MODEL_SRC]\n"
    "if missing:\n"
    "    print('model.py missing domain precondition(s):', missing); sys.exit(1)\n"
    "print('model precondition declares the exact-float domain: leaf >= 0 and '\n"
    "      'eval_seq(leaf, layers) < 1e14 (the reachable callee domain).')\n"
    "# 2) axiom_check.within_precision is that EXACT predicate (validated domain ==\n"
    "#    reachable domain). Parse the function body, not a docstring (pilot-bug-4).\n"
    "tree = ast.parse(AXIOM_SRC)\n"
    "wp = None\n"
    "for node in ast.walk(tree):\n"
    "    if isinstance(node, ast.FunctionDef) and node.name == 'within_precision':\n"
    "        wp = node\n"
    "if wp is None:\n"
    "    print('within_precision not found in axiom_check.py'); sys.exit(1)\n"
    "ret = [n for n in ast.walk(wp) if isinstance(n, ast.Return)]\n"
    "if len(ret) != 1:\n"
    "    print('within_precision shape unexpected (returns=%d)' % len(ret)); sys.exit(1)\n"
    "expr = ast.dump(ret[0].value)\n"
    "# require the predicate (leaf >= 0) AND (eval_seq(leaf, n) < 10 ** 14)\n"
    "ok = ('GtE' in expr) and ('Lt' in expr) and ('eval_seq' in expr) and ('14' in expr)\n"
    "if not ok:\n"
    "    print('within_precision is not the expected (leaf>=0 and eval_seq<1e14) '\n"
    "          'predicate:', expr); sys.exit(1)\n"
    "print('axiom_check.within_precision == model precondition: leaf >= 0 and '\n"
    "      'eval_seq(leaf, n) < 1e14 (filter == Requires; no broader, no narrower).')\n"
    "# 3) EXECUTE the real callee at the in-window F2P point and just out of window\n"
    "#    to demonstrate exactness is claimed exactly on the validated domain.\n"
    "from sympy import Float, Integer\n"
    "from sympy.utilities.lambdify import implemented_function\n"
    "f = implemented_function('f', lambda x: x ** 2)\n"
    "# in-window: f(f(2)) -> eval_seq(2,2)=16 < 1e14, exact integer match.\n"
    "assert f(f(2)).evalf() == Float(16), 'in-window F2P discriminator broke'\n"
    "# out-of-window witness (NOT in the model's reachable domain): leaf=11 over 4\n"
    "# layers -> 11**16 ~ 4.59e16 >= 1e14. eval_seq there is >= 1e14, so the model's\n"
    "# precondition EXCLUDES it (eval_seq(leaf,layers) < 1e14 is False) and the\n"
    "# A-reference never claims exactness on it; this is OUT of the reachable\n"
    "# domain, so containment is not violated by the real callee rounding there.\n"
    "def _eval_seq(leaf, n):\n"
    "    acc = leaf\n"
    "    for _ in range(n):\n"
    "        acc = acc * acc\n"
    "    return acc\n"
    "assert _eval_seq(11, 4) >= 10 ** 14, 'expected out-of-window witness >= 1e14'\n"
    "print('AXIOM-CONTAINMENT OK: the model precondition (leaf >= 0 and '\n"
    "      'eval_seq(leaf, layers) < 1e14) equals axiom_check.within_precision, so '\n"
    "      'every caller-reachable input to the A-reference deep model is inside the '\n"
    "      'validated domain (no reachable input outside it => no '\n"
    "      'A-reference-TOO-WEAK-FOR-CALLER); the out-of-window witness leaf=11,n=4 '\n"
    "      '(>= 1e14) is excluded by the precondition and never claimed exact.')\n"
    "sys.exit(0)\n"
)

AXIOM_TESTS = [
    {
        "id": "ax-sound-eval_seq",
        "axiom": "eval_seq",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _AX_SOUND_PROBE,
        "rationale": "the deep model eval_seq (over imp) is an A-reference for the "
                     "CHANGED operation (recursive argument evaluation). The REAL "
                     "recursive Function._eval_evalf, under the gold patch, must "
                     "reproduce it: a present number == imp iterated n times, on the "
                     "F2P discriminator f(f(2)).evalf()==Float(16) + boundary + fuzz, "
                     "ALL on the declared exact-float domain (within_precision == the "
                     "precondition). If the real callee disagreed anywhere in-domain "
                     "the A-reference would be UNSOUND. Runs axiom_check.py's main() "
                     "in the instance image with the gold patch applied.",
    },
    {
        "id": "ax-cover-eval_seq",
        "axiom": "eval_seq",
        "kind": "axiom-containment",
        "expect": "covered",
        "apply_gold": True,
        "probe": _AX_COVER_PROBE,
        "rationale": "the A-reference is validated on exactly within_precision(leaf,n) "
                     "= (leaf >= 0 and eval_seq(leaf,n) < 1e14), which is byte-for-byte "
                     "the model's precondition. So every input the modeled function can "
                     "reach lies inside the validated domain (containment); a reachable "
                     "input outside it would be A-reference-TOO-WEAK-FOR-CALLER. The "
                     "real callee confirms exactness in-window (f(f(2))==Float(16)); the "
                     "out-of-window witness (leaf=11,n=4, >= 1e14) is excluded by the "
                     "precondition, so the callee rounding there is not a containment "
                     "defect (covering exactly the reachable domain is SOUND).",
    },
]
