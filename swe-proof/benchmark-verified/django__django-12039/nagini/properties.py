# properties.py — PBT falsification battery for django__django-12039.
#
# NOT a Nagini module; a record of adversarial cases the runner
# (swebench_nagini.pbt) executes and stamps RESULT onto. Each SPEC case is a
# full model.py variant that shares the FROZEN spec byte-for-byte (region-surgery
# edits ONLY inside the two `# impl-start`/`# impl-end` regions) and swaps the
# implementation; it is checked by Nagini verify + markers.same_spec on the host.
#
# DEFENDED SURFACE (read before reading the cases):
#   Two structurally-identical modeled functions, render_column (site 1) and
#   render_column_with_opclass (site 2). Each:
#     * has TWO read-only inputs: Acc(list_pred(base),1/2) and
#       Acc(list_pred(suffix),1/2)  -> FRAME-MUTATION is mandatory (x2).
#     * pins the output with the LOAD-BEARING clause
#         ToSeq(Result()) == joined(ToSeq(base), ToSeq(suffix))
#       where joined is a @Pure helper FULLY GROUNDED in the inputs (it unfolds
#       to `base` for an empty suffix, else `base + [32] + suffix`). There is NO
#       opaque answer-key oracle to echo, so the ungrounded-oracle-echo class is
#       N/A here (see 'assessment'); instead we carry an honest positive control.
#     * adds structural pins: empty suffix -> Result()==base (no trailing sep);
#       non-empty suffix -> base preserved as prefix, Result()[len(base)]==sep()
#       (a single U+0020 separator, no fusion), drop(len(base)+1)==suffix.
#   The single change the gold patch makes is: only space-join the suffix when
#   it is non-empty (the empty-string ascending suffix must contribute nothing).
#   The F2P discriminator is `"headline" DESC` (a space before DESC) vs the
#   pre-patch `"headline"DESC`; the opclass P2P discriminator is no trailing
#   space for an empty suffix.
#
#   No @ContractOnly axioms are consumed (meta.axioms == []). `joined` is an
#   A-reference deep model checked by axiom_check.py against the real gold
#   col_str join. We carry ONE axiom-soundness probe that re-runs that real
#   join (Python stdlib str.format/truthiness, the gold logic verbatim) and
#   asserts joined == real join on boundary + fuzz inputs; it is self-contained
#   (embeds the host axiom_check.py source) and needs no repo import.

from pathlib import Path

INSTANCE = "django__django-12039"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()
_AXIOM_CHECK_SRC = (Path(__file__).parent / "axiom_check.py").read_text()


def _swap(src, old, new):
    """Replace the UNIQUE occurrence of `old` with `new` (drift guard)."""
    if old not in src:
        raise AssertionError(f"drift: {old!r} not found")
    if src.count(old) != 1:
        raise AssertionError(f"not unique ({src.count(old)}x): {old!r}")
    return src.replace(old, new, 1)


def _swap_n(src, old, new, n):
    """Replace EXACTLY n occurrences of `old` (the two impl bodies are byte
    identical; an attack on the shared join logic edits both at once)."""
    if src.count(old) != n:
        raise AssertionError(f"expected {n}x, found {src.count(old)}x: {old!r}")
    return src.replace(old, new)


# The two impl bodies are byte-identical. Split _BASE at site 2's def so we can
# target site 1 vs site 2 independently when an attack is site-specific.
_SITE2_DEF = "def render_column_with_opclass(base: List[int], suffix: List[int]) -> List[int]:"
assert _BASE.count(_SITE2_DEF) == 1, "site-2 def not unique"
_HEAD, _TAIL = _BASE.split(_SITE2_DEF, 1)   # _HEAD = site 1 + helpers; _TAIL = site 2


def _site1_only(old, new):
    """Edit the impl of render_column (site 1) only."""
    return _swap(_HEAD, old, new) + _SITE2_DEF + _TAIL


def _site2_only(old, new):
    """Edit the impl of render_column_with_opclass (site 2) only."""
    return _HEAD + _SITE2_DEF + _swap(_TAIL, old, new)


# ---- shared anchors inside the impl region (present in BOTH bodies) ----

# The gold non-empty branch: append a separator then a forward-copy of the suffix.
_GOLD_NONEMPTY_OPEN = (
    "    if len(suffix) > 0:\n"
    "        result.append(sep())\n"
    "        Assert(ToSeq(result) == ToSeq(base) + PSeq(sep()))\n"
)

# The WHOLE guarded join region of a gold body: the empty-suffix guard, both of
# its arms, and every framing assert/invariant either arm carries. Anchored as
# one unit because an attack on the GUARD has to remove the arm structure too:
# rewriting only the `if` line to a constant-true test leaves the `else` arm
# unreachable, and Nagini's mypy front-end refuses to translate dead code
# (`Type error: dead.code`) -- so the rival would never reach Viper and its
# "did not verify" would attribute nothing to the spec (see the
# partial-unconditional-join case below).
_GUARDED_JOIN = (
    "    # only append a separator + suffix when the suffix is non-empty\n"
    "    Assert(len(ToSeq(suffix)) == len(suffix))\n"
    "    if len(suffix) > 0:\n"
    "        result.append(sep())\n"
    "        Assert(ToSeq(result) == ToSeq(base) + PSeq(sep()))\n"
    "        k = 0\n"
    "        while k < len(suffix):\n"
    "            # invariants-start\n"
    "            Invariant(Acc(list_pred(base), 1 / 2))\n"
    "            Invariant(Acc(list_pred(suffix), 1 / 2))\n"
    "            Invariant(Acc(list_pred(result)))\n"
    "            Invariant(len(suffix) > 0)\n"
    "            Invariant(0 <= k and k <= len(suffix))\n"
    "            Invariant(ToSeq(result) == ToSeq(base) + PSeq(sep()) + ToSeq(suffix).take(k))\n"
    "            Invariant(MustTerminate(len(suffix) - k + 1))\n"
    "            # invariants-end\n"
    "            result.append(suffix[k])\n"
    "            k = k + 1\n"
    "        Assert(ToSeq(suffix).take(len(suffix)) == ToSeq(suffix))\n"
    "        Assert(ToSeq(result) == ToSeq(base) + PSeq(sep()) + ToSeq(suffix))\n"
    "        Assert(len(ToSeq(suffix)) == len(suffix))\n"
    "        Assert(joined(ToSeq(base), ToSeq(suffix)) == ToSeq(base) + PSeq(sep()) + ToSeq(suffix))\n"
    "        Assert(ToSeq(result) == joined(ToSeq(base), ToSeq(suffix)))\n"
    "    else:\n"
    "        Assert(len(ToSeq(suffix)) == 0)\n"
    "        Assert(ToSeq(result) == ToSeq(base))\n"
    "        Assert(joined(ToSeq(base), ToSeq(suffix)) == ToSeq(base))\n"
    "        Assert(ToSeq(result) == joined(ToSeq(base), ToSeq(suffix)))\n"
)
assert _BASE.count(_GUARDED_JOIN) == 2, "guarded join region not present 2x verbatim"

# The same region with the empty-suffix guard GONE: the separator append and the
# suffix-copy loop run on every input, dedented to the body's top level, and the
# arm structure is dropped rather than left dead. `if True: A else: B` is
# semantically just `A`, so this is the same behaviour the constant-true guard
# intended -- but it TRANSLATES, so Viper gets to judge it.
#
# The two joined()-equality asserts and the `Invariant(len(suffix) > 0)` are NOT
# carried over. They are proof hints for the guarded non-empty arm and are false
# / unprovable once the region runs unconditionally; keeping them would move the
# rejection onto an intermediate Assert, so Viper would turn the rival down for a
# broken proof hint instead of for the POSTCONDITION the case is about. The
# asserts that survive are the ones true on every input, so the only thing left
# for the verifier to object to is the spec's own clause.
_UNCONDITIONAL_JOIN = (
    "    # append the separator + suffix UNCONDITIONALLY: no empty-suffix guard\n"
    "    Assert(len(ToSeq(suffix)) == len(suffix))\n"
    "    result.append(sep())\n"
    "    Assert(ToSeq(result) == ToSeq(base) + PSeq(sep()))\n"
    "    k = 0\n"
    "    while k < len(suffix):\n"
    "        # invariants-start\n"
    "        Invariant(Acc(list_pred(base), 1 / 2))\n"
    "        Invariant(Acc(list_pred(suffix), 1 / 2))\n"
    "        Invariant(Acc(list_pred(result)))\n"
    "        Invariant(0 <= k and k <= len(suffix))\n"
    "        Invariant(ToSeq(result) == ToSeq(base) + PSeq(sep()) + ToSeq(suffix).take(k))\n"
    "        Invariant(MustTerminate(len(suffix) - k + 1))\n"
    "        # invariants-end\n"
    "        result.append(suffix[k])\n"
    "        k = k + 1\n"
    "    Assert(ToSeq(suffix).take(len(suffix)) == ToSeq(suffix))\n"
    "    Assert(ToSeq(result) == ToSeq(base) + PSeq(sep()) + ToSeq(suffix))\n"
    "    Assert(len(ToSeq(suffix)) == len(suffix))\n"
)

# NON-VACUITY CONTROL for the case above: the same unconditional-join rival with
# `Assert(False)` immediately before the now-unguarded separator append. The
# rejection of the rival is only evidence about the join if the join is REACHED,
# and an unreachable region verifies anything -- so this must be REJECTED too,
# naming the Assert itself. If it ever verified, the region would be dead (a
# contradictory precondition, or a guard the translator folded away) and the
# unconditional-join rejection would be vacuous rather than real.
_UNCONDITIONAL_JOIN_ASSERT_FALSE = _UNCONDITIONAL_JOIN.replace(
    "    result.append(sep())\n",
    "    Assert(False)\n"
    "    result.append(sep())\n",
    1,
)
assert _UNCONDITIONAL_JOIN_ASSERT_FALSE != _UNCONDITIONAL_JOIN, "control probe not installed"

# A whole gold impl body (shared), used to install a structural positive control.
_GOLD_BODY = """    result = []  # type: List[int]
    # base token
    j = 0
    while j < len(base):
        # invariants-start
        Invariant(Acc(list_pred(base), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= j and j <= len(base))
        Invariant(ToSeq(result) == ToSeq(base).take(j))
        Invariant(MustTerminate(len(base) - j + 1))
        # invariants-end
        result.append(base[j])
        j = j + 1
    Assert(ToSeq(result) == ToSeq(base))
    # only append a separator + suffix when the suffix is non-empty
    Assert(len(ToSeq(suffix)) == len(suffix))
    if len(suffix) > 0:
        result.append(sep())
        Assert(ToSeq(result) == ToSeq(base) + PSeq(sep()))
        k = 0
        while k < len(suffix):
            # invariants-start
            Invariant(Acc(list_pred(base), 1 / 2))
            Invariant(Acc(list_pred(suffix), 1 / 2))
            Invariant(Acc(list_pred(result)))
            Invariant(len(suffix) > 0)
            Invariant(0 <= k and k <= len(suffix))
            Invariant(ToSeq(result) == ToSeq(base) + PSeq(sep()) + ToSeq(suffix).take(k))
            Invariant(MustTerminate(len(suffix) - k + 1))
            # invariants-end
            result.append(suffix[k])
            k = k + 1
        Assert(ToSeq(suffix).take(len(suffix)) == ToSeq(suffix))
        Assert(ToSeq(result) == ToSeq(base) + PSeq(sep()) + ToSeq(suffix))
        Assert(len(ToSeq(suffix)) == len(suffix))
        Assert(joined(ToSeq(base), ToSeq(suffix)) == ToSeq(base) + PSeq(sep()) + ToSeq(suffix))
        Assert(ToSeq(result) == joined(ToSeq(base), ToSeq(suffix)))
    else:
        Assert(len(ToSeq(suffix)) == 0)
        Assert(ToSeq(result) == ToSeq(base))
        Assert(joined(ToSeq(base), ToSeq(suffix)) == ToSeq(base))
        Assert(ToSeq(result) == joined(ToSeq(base), ToSeq(suffix)))
    return result
"""
assert _BASE.count(_GOLD_BODY) == 2, "gold body not present 2x verbatim"

# A structurally-DIFFERENT but CORRECT body: the branch order is swapped
# (handle the empty-suffix case FIRST via `if len(suffix) == 0`, then the
# non-empty case in the else). The base-copy loop, the separator append, the
# suffix-copy loop, and EVERY gold framing assert/invariant are kept verbatim,
# only relocated; nothing the verifier needs is dropped. This is a pure
# control-flow reshape, not a loop-direction flip (no f(a+b) lemma needed).
_POS_BODY = """    result = []  # type: List[int]
    # base token
    j = 0
    while j < len(base):
        # invariants-start
        Invariant(Acc(list_pred(base), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= j and j <= len(base))
        Invariant(ToSeq(result) == ToSeq(base).take(j))
        Invariant(MustTerminate(len(base) - j + 1))
        # invariants-end
        result.append(base[j])
        j = j + 1
    Assert(ToSeq(result) == ToSeq(base))
    # only append a separator + suffix when the suffix is non-empty
    Assert(len(ToSeq(suffix)) == len(suffix))
    if len(suffix) == 0:
        Assert(len(ToSeq(suffix)) == 0)
        Assert(ToSeq(result) == ToSeq(base))
        Assert(joined(ToSeq(base), ToSeq(suffix)) == ToSeq(base))
        Assert(ToSeq(result) == joined(ToSeq(base), ToSeq(suffix)))
    else:
        result.append(sep())
        Assert(ToSeq(result) == ToSeq(base) + PSeq(sep()))
        k = 0
        while k < len(suffix):
            # invariants-start
            Invariant(Acc(list_pred(base), 1 / 2))
            Invariant(Acc(list_pred(suffix), 1 / 2))
            Invariant(Acc(list_pred(result)))
            Invariant(len(suffix) > 0)
            Invariant(0 <= k and k <= len(suffix))
            Invariant(ToSeq(result) == ToSeq(base) + PSeq(sep()) + ToSeq(suffix).take(k))
            Invariant(MustTerminate(len(suffix) - k + 1))
            # invariants-end
            result.append(suffix[k])
            k = k + 1
        Assert(ToSeq(suffix).take(len(suffix)) == ToSeq(suffix))
        Assert(ToSeq(result) == ToSeq(base) + PSeq(sep()) + ToSeq(suffix))
        Assert(len(ToSeq(suffix)) == len(suffix))
        Assert(joined(ToSeq(base), ToSeq(suffix)) == ToSeq(base) + PSeq(sep()) + ToSeq(suffix))
        Assert(ToSeq(result) == joined(ToSeq(base), ToSeq(suffix)))
    return result
"""

# Admissibility: keep the gold body, prepend a benign assertion that is provable
# ONLY if the (half-permission) precondition actually admits reading a normal,
# F2P-shaped input (non-negative lengths of both inputs). If the Requires were
# unsatisfiable / too strong for a legitimate input, even this would not verify.
_ADMISS_BODY = _GOLD_BODY.replace(
    "    result = []  # type: List[int]\n",
    "    result = []  # type: List[int]\n"
    "    Assert(len(base) >= 0)\n"
    "    Assert(len(suffix) >= 0)\n",
    1,
)

# ---------------------------------------------------------------------------
SPEC_TESTS = [

    # ---- POSITIVE CONTROL (soundness): correct but reshaped impl must verify --
    {
        "id": "pos-control-branch-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap_n(_BASE, _GOLD_BODY, _POS_BODY, 2),
        "rationale": "A structurally-different but CORRECT impl: the empty-suffix "
                     "branch is handled first (if len(suffix)==0) and the non-empty "
                     "join in the else. Every gold invariant and framing assert is "
                     "kept verbatim (only relocated), no loop direction flipped, so "
                     "no f(a+b) lemma is needed. It computes joined() identically. "
                     "If it cannot verify, the postcondition is SPEC-TOO-STRONG.",
    },

    # ---- ADMISSIBILITY: precondition admits a normal F2P-shaped input ---------
    {
        "id": "admiss-readonly-inputs",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap_n(_BASE, _GOLD_BODY, _ADMISS_BODY, 2),
        "rationale": "Adds Assert(len(base)>=0) and Assert(len(suffix)>=0) at the "
                     "top of both gold impls. These are provable only if the "
                     "half-permission Requires actually grants read access to a "
                     "normal input (non-empty base, possibly-empty suffix). It must "
                     "verify; if not, PRECOND-TOO-STRONG.",
    },

    # ---- FRAME-MUTATION (MANDATORY: both inputs are Acc(...,1/2)) -------------
    # Site 1: write to the read-only `suffix` input. The only legitimate way to
    # satisfy the postcondition while doing this would require full permission;
    # the half-permission precondition must reject it for INSUFFICIENT PERMISSION.
    {
        "id": "frame-mut-suffix-site1",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _site1_only(
            "        result.append(sep())\n"
            "        Assert(ToSeq(result) == ToSeq(base) + PSeq(sep()))\n",
            "        result.append(sep())\n"
            "        suffix.append(sep())\n"   # <-- WRITE to read-only input
            "        Assert(ToSeq(result) == ToSeq(base) + PSeq(sep()))\n",
        ),
        "refinement": "A faithful real patch that mutated self.col_suffixes[idx] "
                      "(the suffix) in place while rendering would corrupt the "
                      "shared col_suffixes list across columns and produce wrong "
                      "DDL for every later column reference, so it would NOT resolve "
                      "test_descending_columns_list_sql / the P2P column tests.",
        "rationale": "render_column requires only Acc(list_pred(suffix),1/2); "
                     "suffix.append(...) needs write permission. Must be rejected "
                     "for insufficient permission (the #1 weakness class).",
    },
    # Site 2: write to the read-only `base` input.
    {
        "id": "frame-mut-base-site2",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _site2_only(
            "    result = []  # type: List[int]\n",
            "    result = []  # type: List[int]\n"
            "    base.append(sep())\n",        # <-- WRITE to read-only input
        ),
        "refinement": "A faithful real patch that appended to the base token's "
                      "backing list (the assembled column+opclass string) would "
                      "mutate caller-shared state and emit the wrong opclass text, "
                      "failing test_ops_class_columns_lists_sql; it would NOT resolve.",
        "rationale": "render_column_with_opclass requires only "
                     "Acc(list_pred(base),1/2); base.append(...) needs write "
                     "permission and must be rejected for insufficient permission.",
    },

    # ---- PARTIAL-DOMAIN: pre-patch site-1 bug (no separator, direct concat) ---
    # Correct ONLY for the empty-suffix domain; for a non-empty suffix it fuses
    # the keyword onto the base (the exact F2P bug). Applied to BOTH bodies.
    {
        "id": "partial-no-separator",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap_n(
            _BASE,
            "    if len(suffix) > 0:\n"
            "        result.append(sep())\n"
            "        Assert(ToSeq(result) == ToSeq(base) + PSeq(sep()))\n",
            "    if len(suffix) > 0:\n",   # drop the separator append entirely
            2,
        ),
        "refinement": "This is the literal pre-patch site-1 behaviour "
                      "(quote_name(column) + col_suffixes[idx], no space). It "
                      "renders \"headline\"DESC, so it FAILS the F2P "
                      "test_descending_columns_list_sql which asserts "
                      "'(\"headline\" DESC)'. It would NOT resolve.",
        "rationale": "Without the separator append, the non-empty-suffix clauses "
                     "Result()[len(base)]==sep() and ToSeq(Result())==joined(...) "
                     "are violated. Must be rejected (SPEC-TOO-WEAK if it verifies).",
    },

    # ---- PARTIAL-DOMAIN: pre-patch site-2 bug (unconditional join) ------------
    # Correct ONLY for non-empty suffix; for the empty suffix it appends a
    # trailing space (the opclass-without-order quirk). Applied to BOTH bodies by
    # removing the empty-suffix guard so the separator is appended unconditionally.
    {
        "id": "partial-unconditional-join",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap_n(_BASE, _GUARDED_JOIN, _UNCONDITIONAL_JOIN, 2),
        "refinement": "This is the pre-patch site-2 behaviour (unconditional "
                      "'{} {}'.format(col, suffix)). For an empty ascending suffix "
                      "it emits a trailing space -> '(\"headline\" text_pattern_ops )', "
                      "failing test_ops_class_columns_lists_sql which expects no "
                      "trailing space. It would NOT resolve.",
        "rationale": "With the guard removed the separator append runs even for an "
                     "empty suffix (the suffix-copy loop itself is then a no-op), so "
                     "the rendered text is base + [32] instead of base. For "
                     "len(suffix)==0 that violates ToSeq(Result())==joined(...) and "
                     "Implies(len(suffix)==0, Result()==base). Must be rejected; "
                     "Viper names the joined() equality at BOTH sites "
                     "('Postcondition of render_column might not hold. Assertion "
                     "(ToSeq(Result()) == joined(ToSeq(base), ToSeq(suffix))) might "
                     "not hold.'), i.e. the load-bearing clause, not a framing "
                     "assert. Reachability of the edited region is established "
                     "separately by nonvacuity-unconditional-join-reachable.",
    },

    # ---- NON-VACUITY CONTROL for partial-unconditional-join -------------------
    # The rival above is judged solely by "Viper turned it down", so that verdict
    # is worth nothing unless the region it edits is actually REACHED: an
    # unreachable region verifies any postcondition, and a rival that never
    # translates does not even reach Viper (the earlier constant-true-guard
    # spelling of this attack died in mypy with `Type error: dead.code` and was
    # recorded as a correct rejection). `Assert(False)` at the join site is the
    # control: it must be REJECTED, naming the Assert. Verifying would mean the
    # site is dead and the rejection above is vacuous.
    {
        "id": "nonvacuity-unconditional-join-reachable",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap_n(_BASE, _GUARDED_JOIN,
                          _UNCONDITIONAL_JOIN_ASSERT_FALSE, 2),
        "refinement": "Not a candidate patch at all: a reachability probe. An "
                      "implementation asserting False renders nothing and would NOT "
                      "resolve; it exists only to show the region the "
                      "unconditional-join rival edits is executed.",
        "rationale": "Non-vacuity control, not a spec attack. Viper must reject with "
                     "'Assert might fail. Assertion False might not hold.' at the "
                     "join site in BOTH bodies, which is what makes "
                     "partial-unconditional-join's rejection a real judgment about "
                     "the join rather than a statement about an unreachable region "
                     "(or a front-end crash). If this VERIFIES the region is dead "
                     "and the sibling case proves nothing -- a defective test, and "
                     "the reject lane loses the empty-suffix attack.",
    },

    # ---- PARTIAL-DOMAIN / separator-value attack: wrong separator code point --
    # Uses tab (9) instead of space (32). Correct length, correct prefix, correct
    # suffix-after-separator, but the separator VALUE is wrong -> the
    # Result()[len(base)]==sep() clause and the joined() equality fail.
    {
        "id": "wrong-separator-tab",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap_n(
            _BASE,
            "    if len(suffix) > 0:\n"
            "        result.append(sep())\n",
            "    if len(suffix) > 0:\n"
            "        result.append(9)\n",   # tab instead of the U+0020 separator
            2,
        ),
        "refinement": "A real patch that joined with a tab/other glyph instead of a "
                      "space would render '\"headline\"\\tDESC', not '\"headline\" "
                      "DESC'; the F2P assertIn('(\"headline\" DESC)') fails. It would "
                      "NOT resolve.",
        "rationale": "sep()==32 is pinned by Result()[len(base)]==sep() and by the "
                     "joined() equality (joined uses PSeq(32)). Appending 9 makes the "
                     "code point after the base a tab. Must be rejected; verifying "
                     "would be SPEC-TOO-WEAK on the separator value.",
    },

    # ---- VALUE-DOUBLE-MASK / last-element attack: drop the final suffix char --
    # Emits base + sep + suffix[:-1] for a non-empty suffix. Matches on prefix +
    # separator and on all-but-last suffix element; diverges only on the last
    # element and the total length. Targets the drop(len(base)+1)==suffix and the
    # joined() equality clauses on the input that fails LAST.
    {
        "id": "drop-last-suffix-char",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap_n(
            _BASE,
            "        while k < len(suffix):\n",
            "        while k < len(suffix) - 1:\n",   # stop one short
            2,
        ),
        "refinement": "Rendering 'DESC'[:-1] = 'DES' would emit '\"headline\" DES', "
                      "so the F2P assertIn('(\"headline\" DESC)') fails (and any "
                      "multi-char suffix is truncated). A real patch dropping the "
                      "last suffix character would NOT resolve.",
        "rationale": "Stopping the suffix copy one short makes "
                     "drop(len(base)+1)==suffix false (it equals suffix.take(len-1)) "
                     "and breaks ToSeq(Result())==joined(...). The loop-invariant "
                     "exit also fails to establish the post-loop assert. Must be "
                     "rejected; verifying would be SPEC-TOO-WEAK (drops the last "
                     "index, a value-proxy mask).",
    },
]

# ---------------------------------------------------------------------------
# AXIOM lane. meta.axioms == [] (no @ContractOnly axioms consumed). `joined` is
# an A-reference deep model. We carry ONE axiom-soundness probe re-establishing
# the G-AX obligation: the deep model `joined` equals the REAL gold col_str join
# on boundary + fuzz inputs. The real join is Python stdlib (str.format +
# truthiness, the gold logic verbatim, identical at both sites) so the probe is
# self-contained and needs no repo import; it embeds the host axiom_check.py
# source and runs its main(). apply_gold is irrelevant (no repo code touched),
# set True for harness uniformity. Files are opened with encoding="utf-8".
_AX_PROBE = (
    "import sys\n"
    "# Embedded host axiom_check.py (G-AX A-reference soundness oracle).\n"
    "# It defines joined() (the model.py deep model), real_join() (the gold\n"
    "# col_str join, stdlib only), check(), and main(); main() exits 0 iff the\n"
    "# deep model equals the real join on every boundary + fuzz input.\n"
    "_SRC = " + repr(_AXIOM_CHECK_SRC) + "\n"
    "g = {'__name__': '__pbt_axiom__'}\n"
    "exec(compile(_SRC, 'axiom_check.py', 'exec'), g)\n"
    "rc = g['main']()\n"
    "if rc != 0:\n"
    "    print('AXIOM-UNSOUND: deep model joined != real col_str join')\n"
    "    sys.exit(1)\n"
    "# Extra adversarial fuzz targeting the empty-suffix boundary specifically\n"
    "# (the site-2 regression) and a multi-codepoint suffix (the F2P).\n"
    "joined = g['joined']\n"
    "real_join = g['real_join']\n"
    "import random\n"
    "rng = random.Random(987654)\n"
    "ALPH = [chr(c) for c in range(32, 127)]\n"
    "for _ in range(50000):\n"
    "    b = ''.join(rng.choice(ALPH) for _ in range(rng.randint(0, 16)))\n"
    "    # bias heavily toward empty + short suffixes (the discriminating domain)\n"
    "    r = rng.random()\n"
    "    if r < 0.5:\n"
    "        s = ''\n"
    "    else:\n"
    "        s = ''.join(rng.choice(ALPH) for _ in range(rng.randint(1, 6)))\n"
    "    obs = [ord(ch) for ch in real_join(b, s)]\n"
    "    exp = joined([ord(ch) for ch in b], [ord(ch) for ch in s])\n"
    "    if obs != exp:\n"
    "        print('AXIOM-UNSOUND on base=%r suffix=%r: real=%r model=%r'\n"
    "              % (b, s, obs, exp))\n"
    "        sys.exit(1)\n"
    "    if s == '' and obs != [ord(ch) for ch in b]:\n"
    "        print('empty suffix produced trailing data: base=%r %r' % (b, obs))\n"
    "        sys.exit(1)\n"
    "    if s != '' and (len(obs) < len(b) + 1 or obs[len(b)] != 32):\n"
    "        print('non-empty suffix not space-separated: base=%r suffix=%r %r'\n"
    "              % (b, s, obs))\n"
    "        sys.exit(1)\n"
    "print('PBT axiom-soundness OK: deep model joined == real col_str join on '\n"
    "      'host boundary/fuzz + 50000 extra boundary-biased fuzz inputs.')\n"
    "sys.exit(0)\n"
)

AXIOM_TESTS = [
    {
        "id": "ax-soundness-joined",
        "axiom": "joined",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _AX_PROBE,
        "rationale": "joined is an A-reference deep model, not a consumed axiom. It "
                     "must equal the real gold col_str join (if suffix: '{} "
                     "{}'.format(col, suffix) else col) on every caller-reachable "
                     "(base, suffix). The probe re-runs the host G-AX oracle "
                     "(axiom_check.py) plus 50000 boundary-biased fuzz inputs; a "
                     "single disagreement would be AXIOM-UNSOUND. There is no "
                     "containment case to add: the modeled functions can pass ANY "
                     "code-point lists as (base, suffix), and joined / the real "
                     "join are total over all str pairs, so the caller-reachable "
                     "domain is fully covered.",
    },
]
