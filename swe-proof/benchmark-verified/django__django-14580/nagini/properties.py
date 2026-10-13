# properties.py — PBT falsification battery for django__django-14580.
#
# NOT a Nagini module; a manifest the runner (swebench_nagini.pbt) parses. Each
# SPEC_TESTS case is a full model.py variant built by REGION SURGERY: we _swap
# the SINGLE `# impl-start` .. `# impl-end` block of serialize_type for a new
# body and leave the frozen spec (axioms / pure / pre / post-conditions /
# signatures / the Serialized constructor contract) byte-identical. The spec view
# elides the WHOLE impl region (the nested # invariants-start/-end included), so
# same_spec is GUARANTEED for every case regardless of the proof scaffolding
# inside the block.
#
# Defended surface (read from model.py / refinement.md / mapping.md / instance.json):
#   serialize_type(value_tag: int) -> Serialized
#     Requires: value_tag == base_ref_tag() or value_tag == other_ref_tag();
#               base_ref_tag() != other_ref_tag(). (value_tag is an int VALUE
#               parameter — there is NO heap reference passed in.)
#               MustTerminate(3) -- TOTAL correctness: the scan and the two
#               materialisation loops are bounded work, so serialize_type must
#               actually DELIVER the pair. Level 3 (not 2) because the body
#               calls Serialized(), whose own MustTerminate(2) — list.__init__
#               carries an obligation — needs room strictly below the caller's.
#               Every loop therefore carries Invariant(MustTerminate(e)) at the
#               end of its OWN invariants region: outer len(tags) - i + 1 (which
#               must NOT mention the inner counters j / m, reset each outer
#               pass), inner len(t) - j + 1 / len(d) - m + 1 (decreasing WITHIN
#               one outer pass, over the `is`-snapshot whose length is fixed).
#               A spliced variant whose loops count differently needs its own
#               measure, or Nagini reports "Obligation leak check failed. Loop
#               might not take all unsatisfied obligations from the context."
#     Ensures (load-bearing, the discriminating fix):
#       (E0) Acc(Result().text)/Acc(list_pred), Acc(Result().imports)/Acc(list_pred)
#       (E1) Implies(value_tag == base_ref_tag(),
#                    ToSeq(Result().text)    == base_ref_text()       AND
#                    ToSeq(Result().imports) == base_ref_directive())
#            -- serializing the base-class reference (models.Model) yields its
#               text AND EXACTLY the namespace-import directive
#               'from django.db import models'. THIS clause is the fix: the
#               import set is non-empty AND equal to the exact statement.
#       (E2) Implies(value_tag == other_ref_tag(),
#                    ToSeq(Result().text) == other_ref_text() AND
#                    len(Result().imports) == 0)
#            -- serializing the no-import reference (type(None)) yields its text
#               and an EMPTY directive set. (anti-"fix-the-wrong-row" guard.)
#
#   The F2P test test_serialize_type_model asserts
#     MigrationWriter.serialize(models.Model) == ("models.Model", {'from django.db import models'})
#   and the round-trip equality; the P2P test_serialize_type_none asserts
#   type(None) -> ("type(None)", set()). E1 is precisely the F2P discriminator;
#   E2 keeps the no-import row honest so a wrong impl cannot "fix the wrong row".
#
# READ-ONLY INPUT / FRAME-MUTATION: there is NO read-only heap input. The single
# parameter value_tag is an int VALUE (no Acc(value_tag,1/2)); the only Acc(...,1/2)
# in the module are loop invariants over LOCALS (tags/texts/directives) that the
# impl constructs itself, not inputs. So the #1 weakness class (overwrite a
# half-permission INPUT to satisfy the postcondition vacuously) is structurally
# inapplicable: there is no caller-owned heap to mutate. has_readonly_input=False.
# See 'assessment'. (We instead drive the uniqueness lane through the table-content
# / scan-fidelity attacks the postcondition actually defends.)
#
# UNGROUNDED-ORACLE ECHO: the postcondition's oracles (base_ref_text/_directive,
# other_ref_text) are @Pure CONSTANT sequences — fully grounded, no opaque
# answer-key. So there is no *wrong* echo to build: any impl whose result equals
# base_ref_directive() has actually carried the right directive (the real work).
# In place of an echo attack we include the honest cheapest correct impl as a
# POSITIVE CONTROL (build the right (text, directive) directly). A WRONG directive
# (attacks weak-wrong-directive / weak-truncated-directive) fails E1, confirming
# the clause pins EXACT content, not mere non-emptiness. See 'assessment'.
#
# CONTROL-FLOW-EFFECT: N/A. serialize_type always returns a Serialized object;
# there is no raise / side-effect path invisible to the value abstraction — the
# F2P observes exactly the returned (text, import-set) pair, which IS the value
# abstraction (text content + import-set content). No capability token is needed.
#
# AXIOM LANE: meta.axioms == [] — NO @ContractOnly axiom is consumed. The table
# scan and the set(imports) materialisation are modelled DEEPLY (impl region) and
# validated == the REAL post-patch django.db.migrations.serializer.TypeSerializer
# .serialize (and the set(imports) primitive) out-of-band by axiom_check.py (G-AX).
# We re-run that real-callee equivalence as a single axiom-soundness probe
# (axiom_check.py read on the HOST at load time and embedded verbatim — the runner
# mounts ONLY the probe at /work), grounding the A-reference deep model in the real
# Django callee, not a regex over source. A containment probe is N/A: there is no
# @ContractOnly axiom Requires domain to fall outside.
from pathlib import Path

INSTANCE = "django__django-14580"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_DIR = Path(__file__).parent
_BASE = (_DIR / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# The single whole-impl anchor: the entire `# impl-start` .. `# impl-end` block
# of serialize_type (verified verbatim from model.py). Each variant re-emits
# `# impl-start` first and `# impl-end` last so the region boundary is preserved
# exactly — only the body between them changes, and the spec view elides all of
# it (including the nested # invariants-start/-end), so same_spec is guaranteed.
# ---------------------------------------------------------------------------
_S = _BASE.index("    # impl-start")
_E = _BASE.index("    # impl-end") + len("    # impl-end")
_IMPL_BLOCK = _BASE[_S:_E]
assert _BASE.count(_IMPL_BLOCK) == 1


def _impl(body_lines: str) -> str:
    """Replace serialize_type's whole impl block with a new body. `body_lines`
    is the source BETWEEN the markers (no markers); we wrap it back in the exact
    `    # impl-start` / `    # impl-end` markers so the region is intact."""
    new_block = "    # impl-start\n" + body_lines.rstrip("\n") + "\n    # impl-end"
    return _swap(_BASE, _IMPL_BLOCK, new_block)


# The GOLD impl body BETWEEN the markers, verbatim — reused as the basis for
# variants that change only a single line (table content / loop bound / scan).
_GOLD_BODY = _IMPL_BLOCK[len("    # impl-start\n"):-len("\n    # impl-end")]


# ---------------------------------------------------------------------------
# POSITIVE CONTROL A (structural reshape, low-risk). Keep the GOLD table correct
# and every gold loop invariant/assert VERBATIM, but change the executable SHAPE:
# build the matched row's import column (imports_out) BEFORE its text column
# (text_out). Each of the two inner copy loops is self-contained (its own snapshot
# `d is directives[i]` / `t is texts[i]` and its own ToSeq(...).take(j/m)
# invariant), so reordering them keeps every proof obligation closable — no
# framing assert is dropped (directive 2) and no append-direction lemma is
# introduced (directive 3). If this CORRECT-but-different impl cannot verify =>
# SPEC-TOO-STRONG (the postcondition would be over-fit to the gold COLUMN order).
# ---------------------------------------------------------------------------
_POS_REORDER = _impl(
    "    tags = [base_ref_tag(), other_ref_tag()]  # type: List[int]\n"
    "    texts = [base_ref_text(), other_ref_text()]  # type: List[PSeq[int]]\n"
    "    directives = [base_ref_directive(), other_ref_directive_empty()]  # type: List[PSeq[int]]\n"
    "\n"
    "    result = Serialized()\n"
    "    i = 0\n"
    "    while i < len(tags):\n"
    "        # invariants-start\n"
    "        Invariant(Acc(list_pred(tags), 1 / 2))\n"
    "        Invariant(Acc(list_pred(texts), 1 / 2))\n"
    "        Invariant(Acc(list_pred(directives), 1 / 2))\n"
    "        Invariant(len(tags) == 2 and len(texts) == 2 and len(directives) == 2)\n"
    "        Invariant(tags[0] == base_ref_tag() and tags[1] == other_ref_tag())\n"
    "        Invariant(texts[0] == base_ref_text() and texts[1] == other_ref_text())\n"
    "        Invariant(directives[0] == base_ref_directive())\n"
    "        Invariant(len(directives[1]) == 0)\n"
    "        Invariant(0 <= i and i <= len(tags))\n"
    "        Invariant(value_tag == base_ref_tag() or value_tag == other_ref_tag())\n"
    "        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,\n"
    "                                                 tags[k] != value_tag))))\n"
    "        Invariant(Acc(result.text) and Acc(list_pred(result.text)))\n"
    "        Invariant(Acc(result.imports) and Acc(list_pred(result.imports)))\n"
    "        # TERMINATION: same outer measure as gold — i grows by one per pass\n"
    "        # and len(tags) is invariantly 2, so it strictly decreases and the\n"
    "        # + 1 keeps it positive. Independent of the inner counters, so\n"
    "        # reordering the two inner loops cannot affect it.\n"
    "        Invariant(MustTerminate(len(tags) - i + 1))\n"
    "        # invariants-end\n"
    "        if tags[i] == value_tag:\n"
    "            t = texts[i]  # type: PSeq[int]\n"
    "            d = directives[i]  # type: PSeq[int]\n"
    "            # REORDERED: materialise the import column FIRST.\n"
    "            imports_out = []  # type: List[int]\n"
    "            m = 0\n"
    "            while m < len(d):\n"
    "                # invariants-start\n"
    "                Invariant(Acc(list_pred(directives), 1 / 2))\n"
    "                Invariant(len(directives) == 2)\n"
    "                Invariant(0 <= i and i < len(directives))\n"
    "                Invariant(d is directives[i])\n"
    "                Invariant(Acc(list_pred(imports_out)))\n"
    "                Invariant(0 <= m and m <= len(d))\n"
    "                Invariant(len(imports_out) == m)\n"
    "                Invariant(ToSeq(imports_out) == d.take(m))\n"
    "                # TERMINATION: d is the fixed `is`-snapshot of directives[i],\n"
    "                # so len(d) is constant across this inner run; m grows by one\n"
    "                # per pass with m <= len(d), so the bound strictly decreases\n"
    "                # and stays positive WITHIN this single outer pass.\n"
    "                Invariant(MustTerminate(len(d) - m + 1))\n"
    "                # invariants-end\n"
    "                imports_out.append(d[m])\n"
    "                m = m + 1\n"
    "            Assert(d.take(len(d)) == d)\n"
    "            Assert(ToSeq(imports_out) == d)\n"
    "            text_out = []  # type: List[int]\n"
    "            j = 0\n"
    "            while j < len(t):\n"
    "                # invariants-start\n"
    "                Invariant(Acc(list_pred(texts), 1 / 2))\n"
    "                Invariant(Acc(list_pred(directives), 1 / 2))\n"
    "                Invariant(len(texts) == 2 and len(directives) == 2)\n"
    "                Invariant(0 <= i and i < len(texts))\n"
    "                Invariant(t is texts[i])\n"
    "                Invariant(d is directives[i])\n"
    "                Invariant(Acc(list_pred(text_out)))\n"
    "                Invariant(0 <= j and j <= len(t))\n"
    "                Invariant(len(text_out) == j)\n"
    "                Invariant(ToSeq(text_out) == t.take(j))\n"
    "                # TERMINATION: t is the fixed `is`-snapshot of texts[i], so\n"
    "                # len(t) is constant across this inner run; j grows by one per\n"
    "                # pass with j <= len(t), so the bound strictly decreases and\n"
    "                # stays positive WITHIN this single outer pass.\n"
    "                Invariant(MustTerminate(len(t) - j + 1))\n"
    "                # invariants-end\n"
    "                text_out.append(t[j])\n"
    "                j = j + 1\n"
    "            Assert(t.take(len(t)) == t)\n"
    "            Assert(ToSeq(text_out) == t)\n"
    "            result.text = text_out\n"
    "            result.imports = imports_out\n"
    "            Assert(ToSeq(result.text) == texts[i])\n"
    "            Assert(ToSeq(result.imports) == directives[i])\n"
    "            return result\n"
    "        i = i + 1\n"
    "    Assert(False)\n"
    "    return result\n"
)


# ---------------------------------------------------------------------------
# POSITIVE CONTROL B (honest cheapest, GROUNDED oracle). The postcondition's
# oracles are @Pure CONSTANT sequences, so the cheapest correct impl simply
# branches on which distinguished tag was passed (the precondition guarantees one
# of the two) and materialises that row's text/directive directly — NO table, NO
# linear scan. It still does the real work (copy the right code-point sequence
# into result.text/result.imports). This stands IN PLACE of an ungrounded-oracle
# echo (there is no wrong echo: the oracles are grounded constants). If this
# structurally-different CORRECT impl cannot verify => SPEC-TOO-STRONG.
# ---------------------------------------------------------------------------
def _materialise(seq_expr: str, dst: str, ind: str) -> str:
    """Emit a per-element copy loop that materialises a PSeq[int] `seq_expr` into
    a fresh List[int] local `dst`, with the take-prefix invariant (the same proof
    obligation the gold impl discharges per column). Every line is prefixed with
    the base indent `ind` (the loop body adds 4 more spaces).

    Each emitted loop carries its OWN termination measure at the end of its own
    invariants region: `<dst>_src` is bound once from a @Pure CONSTANT sequence
    and never reassigned, so len(<dst>_src) is fixed; the counter grows by one
    per pass and stays <= that length, so len(<dst>_src) - <dst>_n + 1 strictly
    decreases and stays positive. These loops are SIBLINGS (sequential), not
    nested, so each measure is over its own counter alone."""
    i0 = ind
    i1 = ind + "    "
    return (
        i0 + "%s_src = %s  # type: PSeq[int]\n" % (dst, seq_expr) +
        i0 + "%s = []  # type: List[int]\n" % dst +
        i0 + "%s_n = 0\n" % dst +
        i0 + "while %s_n < len(%s_src):\n" % (dst, dst) +
        i1 + "# invariants-start\n" +
        i1 + "Invariant(Acc(list_pred(%s)))\n" % dst +
        i1 + "Invariant(0 <= %s_n and %s_n <= len(%s_src))\n" % (dst, dst, dst) +
        i1 + "Invariant(len(%s) == %s_n)\n" % (dst, dst) +
        i1 + "Invariant(ToSeq(%s) == %s_src.take(%s_n))\n" % (dst, dst, dst) +
        i1 + "Invariant(MustTerminate(len(%s_src) - %s_n + 1))\n" % (dst, dst) +
        i1 + "# invariants-end\n" +
        i1 + "%s.append(%s_src[%s_n])\n" % (dst, dst, dst) +
        i1 + "%s_n = %s_n + 1\n" % (dst, dst) +
        i0 + "Assert(%s_src.take(len(%s_src)) == %s_src)\n" % (dst, dst, dst) +
        i0 + "Assert(ToSeq(%s) == %s_src)\n" % (dst, dst)
    )


_POS_DIRECT = _impl(
    "    result = Serialized()\n"
    "    if value_tag == base_ref_tag():\n"
    + _materialise("base_ref_text()", "text_out", "        ")
    + _materialise("base_ref_directive()", "imports_out", "        ")
    + "        result.text = text_out\n"
    "        result.imports = imports_out\n"
    "        Assert(ToSeq(result.text) == base_ref_text())\n"
    "        Assert(ToSeq(result.imports) == base_ref_directive())\n"
    "        return result\n"
    "    else:\n"
    "        Assert(value_tag == other_ref_tag())\n"
    + _materialise("other_ref_text()", "text_out2", "        ")
    + _materialise("other_ref_directive_empty()", "imports_out2", "        ")
    + "        result.text = text_out2\n"
    "        result.imports = imports_out2\n"
    "        Assert(ToSeq(result.text) == other_ref_text())\n"
    "        Assert(len(result.imports) == 0)\n"
    "        return result\n"
)


# ---------------------------------------------------------------------------
# ADMISSIBILITY. The precondition must admit the F2P-shaped input (the base-class
# reference, value_tag == base_ref_tag() — exactly what test_serialize_type_model
# serializes) and the no-import input (type(None), the P2P). The probe ASSERTS,
# on those two concrete tags, that every Requires clause is establishable and
# that the grounded @Pure oracles carry the guarantee the postcondition demands
# (base -> a non-empty directive equal to the namespace import; other -> empty).
# If the precondition could not be met for these normal inputs the asserts would
# not verify => PRECOND-TOO-STRONG. The probe precedes the gold body verbatim, so
# the postcondition obligation is unchanged.
#
# A RECURSIVE self-call is no longer usable as the witness: MustTerminate(3) in
# the precondition correctly forbids a same-measure self-call, and Nagini reports
# `Obligation leak check failed. Callee serialize_type might not take all
# unsatisfied obligations from the caller.` — a termination fact, not a fact
# about the precondition's domain, so it would attribute nothing. (Measured: the
# old self-call probe now fails exactly that way.) Asserting the establishability
# of each Requires clause is the same substitution astropy__astropy-14309 and
# astropy__astropy-13579 use for this reason.
# ---------------------------------------------------------------------------
_POS_ADMISS = _impl(
    "    # ADMISSIBILITY: the two distinguished tags are exactly the F2P and P2P\n"
    "    # inputs (test_serialize_type_model / test_serialize_type_none). Assert\n"
    "    # each Requires clause is establishable for them, and that the grounded\n"
    "    # oracles carry the guarantee => the precondition admits a normal input.\n"
    "    f2p_tag = base_ref_tag()\n"
    "    p2p_tag = other_ref_tag()\n"
    "    # Requires clause 1 (the distinguished path) holds of both:\n"
    "    Assert(f2p_tag == base_ref_tag() or f2p_tag == other_ref_tag())\n"
    "    Assert(p2p_tag == base_ref_tag() or p2p_tag == other_ref_tag())\n"
    "    # Requires clause 2 (the two distinguished types are distinct):\n"
    "    Assert(base_ref_tag() != other_ref_tag())\n"
    "    # ...and the tags are genuinely different inputs, not one input twice.\n"
    "    Assert(f2p_tag != p2p_tag)\n"
    "    # The guarantee is non-vacuous for the F2P tag: its directive is NON-EMPTY\n"
    "    # and is the namespace import (so the rendered name would resolve).\n"
    "    Assert(len(base_ref_directive()) > 0)\n"
    "    Assert(base_ref_directive() != other_ref_directive_empty())\n"
    "    # ...and empty for the P2P tag (no spurious import).\n"
    "    Assert(len(other_ref_directive_empty()) == 0)\n"
    + _GOLD_BODY
)


# ===========================================================================
# UNIQUENESS RIVALS  (spec-too-weak probes — expect "reject")
# ===========================================================================

# (1) PARTIAL-DOMAIN / the bug-delta (= model_prepatch.py). Build the table with
# row 0's directive EMPTY (both rows carry the empty directive). CORRECT on the
# no-import row (other), WRONG on the base-class reference row: the surfaced import
# set is empty, so E1's ToSeq(Result().imports) == base_ref_directive() fails.
_RIVAL_EMPTY_DIRECTIVE = _swap(
    _BASE,
    "    directives = [base_ref_directive(), other_ref_directive_empty()]  # type: List[PSeq[int]]",
    "    directives = [other_ref_directive_empty(), other_ref_directive_empty()]  # type: List[PSeq[int]]",
)
# the gold invariant `directives[0] == base_ref_directive()` is now false, so we
# must also relax that loop invariant to keep the body type-checkable as a faithful
# pre-patch skeleton (this edit is INSIDE the impl region, so same_spec holds).
_RIVAL_EMPTY_DIRECTIVE = _swap(
    _RIVAL_EMPTY_DIRECTIVE,
    "        Invariant(directives[0] == base_ref_directive())\n",
    "        Invariant(len(directives[0]) == 0)\n",
)


# (2) PARTIAL-DOMAIN — WRONG directive content (non-empty but not the namespace
# import). Row 0 carries a non-empty directive that is NOT base_ref_directive()
# (we reuse other_ref_text() = 'type(None)' code points as a stand-in for a wrong
# import string). The import set is now NON-EMPTY, so a spec that only required
# "non-empty imports" would wrongly accept it — but E1 pins the EXACT content
# (== base_ref_directive()), so it must reject. Confirms E1 is exact-content, not
# mere non-emptiness.
_RIVAL_WRONG_DIRECTIVE = _swap(
    _BASE,
    "    directives = [base_ref_directive(), other_ref_directive_empty()]  # type: List[PSeq[int]]",
    "    directives = [other_ref_text(), other_ref_directive_empty()]  # type: List[PSeq[int]]",
)
_RIVAL_WRONG_DIRECTIVE = _swap(
    _RIVAL_WRONG_DIRECTIVE,
    "        Invariant(directives[0] == base_ref_directive())\n",
    "        Invariant(directives[0] == other_ref_text())\n",
)


# (3) PARTIAL-DOMAIN — TRUNCATED directive. Keep row 0's directive correct in the
# table, but the import-materialisation loop stops one code point early
# (m < len(d) - 1), so the surfaced import drops its last char ('...models' ->
# '...model'). CORRECT only on an empty directive (the no-import row, where
# len(d)==0 makes len(d)-1 < 0 a no-op); WRONG on the base row: the result's
# imports equal base_ref_directive().take(len-1) != base_ref_directive() => E1
# fails. The loop invariant ToSeq(imports_out) == d.take(m) still holds; the bug
# is the early STOP, surfacing a partial directive.
_RIVAL_TRUNC_DIRECTIVE = _swap(
    _BASE,
    "            while m < len(d):\n",
    "            while m < len(d) - 1:\n",
)


# (4) STRUCTURAL / wrong-row scan — always return ROW 0's columns regardless of
# which tag matched (ignore the per-row match, use index 0). CORRECT on the base
# row; WRONG on the no-import row (other): it returns base_ref_text() +
# base_ref_directive() instead of other_ref_text() + empty, so E2's
# ToSeq(Result().text) == other_ref_text() AND len(Result().imports) == 0 fail.
# This is the "first-match scan returns the wrong row" attack.
_RIVAL_ALWAYS_ROW0 = _swap(
    _BASE,
    "            t = texts[i]  # type: PSeq[int]\n"
    "            d = directives[i]  # type: PSeq[int]\n",
    "            t = texts[0]  # type: PSeq[int]\n"
    "            d = directives[0]  # type: PSeq[int]\n",
)
# the inner-loop framing invariants pin `t is texts[i]` / `d is directives[i]`;
# with t/d now bound to index 0 those become false, so relax them to index 0 to
# keep the rival a faithful (wrong) impl rather than a proof-gap artifact. (Still
# inside the impl region => same_spec holds.)
_RIVAL_ALWAYS_ROW0 = _swap(
    _RIVAL_ALWAYS_ROW0,
    "                Invariant(t is texts[i])\n",
    "                Invariant(t is texts[0])\n",
)
_RIVAL_ALWAYS_ROW0 = _swap(
    _RIVAL_ALWAYS_ROW0,
    "                Invariant(d is directives[i])\n",
    "                Invariant(d is directives[0])\n",
    # NB there are TWO `d is directives[i]` lines (text loop has none); guard below.
)


# (5) PARTIAL-DOMAIN / fix-the-wrong-row — the no-import row (other) is given a
# NON-EMPTY directive (the namespace import). CORRECT on the base row; WRONG on
# the no-import row: serializing type(None) now surfaces a spurious import, so
# E2's len(Result().imports) == 0 fails. Dual of attack (1): the anti-"fix the
# wrong row" guard E2 catches it.
_RIVAL_OTHER_NONEMPTY = _swap(
    _BASE,
    "    directives = [base_ref_directive(), other_ref_directive_empty()]  # type: List[PSeq[int]]",
    "    directives = [base_ref_directive(), base_ref_directive()]  # type: List[PSeq[int]]",
)
_RIVAL_OTHER_NONEMPTY = _swap(
    _RIVAL_OTHER_NONEMPTY,
    "        Invariant(len(directives[1]) == 0)\n",
    "        Invariant(directives[1] == base_ref_directive())\n",
)


SPEC_TESTS = [
    # ---- positive controls / admissibility (must VERIFY) ----
    {
        "id": "pos-control-reorder-columns",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_REORDER,
        "rationale": "structurally-different but CORRECT impl: the matched row's "
                     "import column is materialised BEFORE its text column (gold "
                     "does text first). Each inner copy loop is self-contained "
                     "(its own `is`-snapshot + ToSeq(...).take invariant), so the "
                     "reorder keeps every gold proof obligation closable — no "
                     "framing assert dropped, no append-direction lemma needed. "
                     "Each loop keeps its OWN termination measure (outer over i "
                     "alone, so the reorder cannot touch it; each inner over its "
                     "own snapshot's fixed length). Must verify; else the "
                     "postcondition is over-fit to the gold COLUMN order => "
                     "SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-control-direct-branch",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_DIRECT,
        "rationale": "honest cheapest CORRECT impl with a DIFFERENT shape: no table "
                     "and no linear scan — branch on the (precondition-guaranteed) "
                     "distinguished tag and materialise that row's text/directive "
                     "directly. The postcondition oracles are GROUNDED @Pure "
                     "constants, so this is the honest cheapest impl (it copies the "
                     "exact code-point sequences — the real work), not an ungrounded "
                     "echo. Its four copy loops are SIBLINGS (no nesting), each with "
                     "its own measure over its own counter and a constant-length "
                     "source. Must verify; else SPEC-TOO-STRONG.",
    },
    {
        "id": "admiss-base-and-other",
        "kind": "admissibility",
        "expect": "verify",
        "module": _POS_ADMISS,
        "rationale": "asserts that BOTH distinguished tags (the base-class "
                     "reference is the exact F2P input, test_serialize_type_model; "
                     "type(None) is the P2P) satisfy EVERY Requires clause — each "
                     "is one of the two distinguished tags, the tags are distinct — "
                     "and that the guarantee is non-vacuous for them (base -> a "
                     "NON-EMPTY directive != the empty one; other -> empty). If the "
                     "precondition could not be established for these normal inputs "
                     "the asserts would not verify => PRECOND-TOO-STRONG. A "
                     "recursive self-call is no longer the witness: MustTerminate(3) "
                     "correctly forbids a same-measure self-call, so its rejection "
                     "would be a termination fact and would attribute nothing about "
                     "the precondition's domain.",
    },

    # ---- uniqueness rivals (must be REJECTED) ----
    {
        "id": "weak-empty-directive-prepatch",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_EMPTY_DIRECTIVE,
        "refinement": "this is the PRE-PATCH table: row 0 is "
                      "(models.Model, 'models.Model', []) with an EMPTY import list "
                      "(= model_prepatch.py / G-DIFF). The real serializer then "
                      "surfaces set([]) == set() for models.Model, so a generated "
                      "migration whose bases reference the rendered `models.Model` "
                      "emits NO `from django.db import models` and raises "
                      "NameError: name 'models' is not defined. The F2P "
                      "test_serialize_type_model asserts the import set is exactly "
                      "{'from django.db import models'} — the faithful pre-patch "
                      "code FAILS it and does NOT resolve.",
        "rationale": "rejected by postcondition E1: "
                     "Implies(value_tag == base_ref_tag(), ... and "
                     "ToSeq(Result().imports) == base_ref_directive()). With row 0's "
                     "directive empty the result's imports are empty, which cannot "
                     "equal the non-empty namespace-import directive. (Exactly the "
                     "G-DIFF failure on model_prepatch.py.) If it verified => "
                     "SPEC-TOO-WEAK.",
    },
    {
        "id": "weak-wrong-directive-content",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_WRONG_DIRECTIVE,
        "refinement": "row 0 carries a NON-EMPTY but WRONG directive (here the "
                      "code points of 'type(None)' standing in for a wrong import "
                      "string, e.g. 'import models' or 'from django.db.models import "
                      "Model'). The real serializer would then surface that wrong "
                      "import; executing it does NOT bring the bare name `models` "
                      "into scope, so the rendered `models.Model` still raises "
                      "NameError, and the F2P assertion `== {'from django.db import "
                      "models'}` (exact set equality) FAILS. The faithful patch does "
                      "NOT resolve.",
        "rationale": "rejected by E1: ToSeq(Result().imports) == base_ref_directive() "
                     "pins the EXACT directive content; a non-empty but different "
                     "sequence (other_ref_text()) cannot equal it. Confirms E1 is "
                     "exact-content, not mere non-emptiness. If it verified => "
                     "SPEC-TOO-WEAK.",
    },
    {
        "id": "weak-truncated-directive",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_TRUNC_DIRECTIVE,
        "refinement": "the import-materialisation loop stops one code point early "
                      "(m < len(d) - 1), so the surfaced directive for models.Model "
                      "drops its final char: 'from django.db import models' -> "
                      "'from django.db import model'. Executing that imports nothing "
                      "named `models` (no such attribute), so the rendered "
                      "`models.Model` still raises NameError and the F2P's exact-set "
                      "assertion FAILS. The faithful patch does NOT resolve.",
        "rationale": "rejected by E1: the loop invariant ToSeq(imports_out) == "
                     "d.take(m) is honest, but the early STOP makes the result's "
                     "imports equal base_ref_directive().take(len-1), which is a "
                     "strict prefix != base_ref_directive(). If it verified => "
                     "SPEC-TOO-WEAK.",
    },
    {
        "id": "weak-always-return-row0",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_ALWAYS_ROW0,
        "refinement": "the scan matches the right tag but materialises ROW 0's "
                      "columns regardless (t/d bound to index 0). This mirrors a "
                      "real serializer whose first-match scan returns the WRONG "
                      "row's (string, set(imports)) — for type(None) it would return "
                      "('models.Model', {'from django.db import models'}) instead of "
                      "('type(None)', set()). The P2P test_serialize_type_none "
                      "asserts type(None) serializes to ('type(None)', set()); this "
                      "FAILS it. The faithful patch does NOT resolve.",
        "rationale": "rejected by E2: "
                     "Implies(value_tag == other_ref_tag(), "
                     "ToSeq(Result().text) == other_ref_text() and "
                     "len(Result().imports) == 0). Returning row 0 for the other tag "
                     "gives text == base_ref_text() != other_ref_text() and a "
                     "non-empty import set. If it verified => SPEC-TOO-WEAK.",
    },
    {
        "id": "weak-other-row-nonempty",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_OTHER_NONEMPTY,
        "refinement": "the no-import row (type(None)) is given the namespace-import "
                      "directive too — `(type(None), 'type(None)', ['from django.db "
                      "import models'])`. The real serializer would then surface a "
                      "SPURIOUS `from django.db import models` for type(None). "
                      "test_serialize_type_none (P2P) asserts type(None) -> "
                      "('type(None)', set()) (empty import set); a non-empty set "
                      "FAILS it. (Also: `django.db.models shouldn't be imported if "
                      "unused`, a P2P, would regress.) The faithful patch does NOT "
                      "resolve.",
        "rationale": "rejected by E2's len(Result().imports) == 0: the no-import row "
                     "must surface an empty directive set. This is the anti-'fix the "
                     "wrong row' guard (dual to the empty-directive prepatch attack). "
                     "If it verified => SPEC-TOO-WEAK.",
    },
]


# ===========================================================================
# AXIOM LANE — no @ContractOnly axiom is consumed (meta.axioms == []); the table
# scan and the set(imports) materialisation are an A-reference deep model validated
# == the REAL post-patch django TypeSerializer.serialize (and the set(imports)
# primitive). We re-run that real-callee equivalence (axiom_check.py's logic, read
# on the HOST at load time and embedded verbatim into a self-contained probe — the
# runner mounts ONLY the probe at /work, so model.py / axiom_check.py are NOT
# in-container) as an axiom-soundness check: if the deep model ever disagrees with
# the real serializer on the two distinguished rows, or set(imports) loses/adds a
# directive over 5000 randomised lists, the A-reference is UNSOUND. The probe
# self-applies the gold patch (apply_gold=True) so the real serializer carries the
# post-patch row-0 directive. A containment probe is N/A: there is no @ContractOnly
# axiom Requires domain to fall outside.
# ===========================================================================

_AXIOM_CHECK_SRC = (_DIR / "axiom_check.py").read_text(encoding="utf-8")

AXIOM_TESTS = [
    {
        "id": "ax-ref-typeserializer-serialize-equals-real",
        "axiom": "serialize_type table scan + set(imports) materialisation (A-reference deep model)",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _AXIOM_CHECK_SRC,
        "rationale": "the deep model (the distinguished-row table, the first-match "
                     "scan, and the per-element set(imports) materialisation) is an "
                     "A-reference: it must equal the REAL post-patch "
                     "django.db.migrations.serializer.TypeSerializer.serialize on "
                     "every input the model covers. This probe (axiom_check.py "
                     "verbatim, stdlib + Django only) drives the REAL "
                     "MigrationWriter.serialize on models.Model and type(None), "
                     "asserts the (text, import-set) pair matches the deep model "
                     "(models.Model -> ('models.Model', {'from django.db import "
                     "models'}); type(None) -> ('type(None)', set())), execs the "
                     "surfaced imports and evals the rendered text to confirm it "
                     "resolves to models.Model (the NameError consequence the issue "
                     "reports), and confirms set(imports) materialisation over 5000 "
                     "randomised directive lists. Exit 0 iff every observation "
                     "agrees; any disagreement => the A-reference is UNSOUND. "
                     "Containment is N/A (no @ContractOnly axiom domain).",
    },
]
