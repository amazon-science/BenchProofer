"""PBT manifest for sphinx-doc__sphinx-7590 — adversarial falsification battery.

NOT a Nagini module; a record of adversarial cases the runner (swebench_nagini.pbt)
executes and stamps with RESULT. Spec cases are full model.py variants that share
the FROZEN spec byte-for-byte (region-surgery: only the text strictly inside the
`# impl-start` / `# impl-end` region is edited) and swap the implementation; they
are checked by Nagini verify + markers.same_spec. Axiom cases are real-callee
probes run in the instance Docker image.

Defended surface (read from model.py / refinement.md / mapping.md / instance.json):

  TWO modeled functions. (1) `number_literal_id(lit, ident, suffixed, ident_id)`
  decides the v3/v4 mangled id of a C++ numeric literal that may carry a trailing
  user-defined-literal (UDL) identifier. (2) `c_number_literal_id(lit, trail,
  valid)` decides the ordinary numeric-literal id of the parallel simpler dialect
  (no UDLs): a recognised numeric suffix run (`valid`) is folded into the literal
  text, a non-recognised trailing run is left unconsumed. Character data is
  `List[int]` of code points; the spec is carried by `PSeq[int]` via `ToSeq`; both
  share the `number_id_seq` deep model.

  READ-ONLY inputs (Acc(list_pred(x), 1/2)): `lit`, `ident`, `ident_id`. => the
  FRAME-MUTATION probe is MANDATORY (write a half-permission input to fake a
  postcondition match; must be REJECTED for INSUFFICIENT PERMISSION).

  Precondition (load-bearing):
    - len(lit) > 0
    - ToSeq(ident) != PSeq(115,116,100)            # exclude the reserved `std`
    - Implies(len(ToSeq(ident)) > 0,
              ToSeq(ident_id) == ident_mangle(ToSeq(ident)))   # ties the
      supplied precomputed identifier-id to the (axiomatized) length-prefixed
      identifier mangling whenever a trailing identifier is present. The UDL
      branch's proof SUBSTITUTES ident_id for ident_mangle(ident) via this tie.

  Postcondition (the two LOAD-BEARING value clauses, both pinned to GROUNDED
  @Pure helpers fully unfolded from the args — no opaque answer-key oracle):
    - UDL clause:  Implies(not suffixed and len(ident)>0 and ident != std,
                           ToSeq(Result()) == udl_id_seq(ToSeq(lit), ToSeq(ident)))
      where udl_id_seq = 'clL_Zli' + ident_mangle(ident) + 'E' + ('L'+lit+'E') + 'E'
    - ordinary clause: Implies(suffixed or len(ident)==0,
                               ToSeq(Result()) == number_id_seq(ToSeq(lit)))
      where number_id_seq = 'L' + lit + 'E'
    - Acc(list_pred(Result()))  (full permission on the produced list)
  The two clauses partition the whole precondition domain (the `ident==std` case
  is excluded by precondition), so every in-domain input is pinned.

  F2P (tests/test_domain_cpp.py::test_expressions) exercises the UDL matrix, e.g.
  `5_udl` -> `clL_Zli4_udlEL5EE`, the issue token `6.62607015e-34q_J` ->
  `clL_Zli3q_JEL6.62607015e-34EE`.

Axiom lane: ONE @ContractOnly axiom `ident_mangle` (A-consumed — the proof uses
its Ensures: len(Result())>len(ident) and the identifier text is a length-prefixed
suffix of its id, on the RESTRICTED domain nonempty & != std). The deep models
`udl_id_seq`/`number_id_seq` are @Pure A-reference (validated == the real callee by
axiom_check.py, not consumed as axioms). We probe (a) ident_mangle soundness on its
contracted domain + that the excluded `std` branch genuinely deviates (so the
restriction is load-bearing, not hidden over-claim), reusing axiom_check.py's
real-callee logic, and (b) containment: every identifier the MODEL can pass to
ident_mangle (nonempty and != std, threaded from number_literal_id's Requires)
lies inside the axiom's Requires domain.
"""
from pathlib import Path

INSTANCE = "sphinx-doc__sphinx-7590"
FLOAT_ENCODING = None  # meta.json float_encoding is null (pure code-point/int carrier)

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Region anchor — the ENTIRE impl body, strictly between # impl-start / # impl-end.
# Every variant _swaps THIS for new text, so edits are confined to the impl region
# and same_spec is guaranteed.
# ---------------------------------------------------------------------------

_GOLD_IMPL = (
    "    if not suffixed and len(ident) > 0:\n"
    "        # user-defined literal: mangle as the call ident(literal),\n"
    "        # concatenating the prefix, the identifier id, the numeric id and the\n"
    "        # framing 'E's.\n"
    "        result = [99, 108, 76, 95, 90, 108, 105] + ident_id \\\n"
    "            + [69, 76] + lit + [69, 69]  # type: List[int]\n"
    "        return result\n"
    "    else:\n"
    "        # ordinary numeric literal: its id is 'L' + text + 'E'\n"
    "        out = [76] + lit + [69]  # type: List[int]\n"
    "        return out"
)

# sanity: the anchor is present and unique in _BASE (fail loud at import otherwise)
assert _BASE.count(_GOLD_IMPL) == 1, "gold impl anchor drifted from model.py"

# ---------------------------------------------------------------------------
# Region anchor for the SECOND modeled function, c_number_literal_id (the
# simpler-dialect suffix-vs-not decision). Its impl region is disjoint from the
# cpp one, so swapping THIS confines edits to c_number_literal_id and same_spec
# is preserved.
# ---------------------------------------------------------------------------

_C_GOLD_IMPL = (
    "    if valid:\n"
    "        # the recognised numeric suffix is consumed into the literal text\n"
    "        out = [76] + lit + trail + [69]  # type: List[int]\n"
    "        return out\n"
    "    else:\n"
    "        # the trailing run is not a valid suffix: the literal text is just `lit`\n"
    "        plain = [76] + lit + [69]  # type: List[int]\n"
    "        return plain"
)

assert _BASE.count(_C_GOLD_IMPL) == 1, "c_number_literal_id impl anchor drifted from model.py"


# ===========================================================================
# SPEC LANE
# ===========================================================================

SPEC_TESTS = [

    # -- POSITIVE CONTROL (soundness): branch-reorder -------------------------
    # Structurally different (negated guard, branches physically swapped) but
    # behaviourally identical: the SAME two list expressions, just reached by the
    # opposite control path. No loop, no fold, no framing lemma to lose (rule 2/3
    # N/A — the proof obligation is a straight-line list equality the verifier
    # discharges from the @Pure unfoldings). MUST verify, else SPEC-TOO-STRONG.
    {
        "id": "pos-branch-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _BASE, _GOLD_IMPL,
            "    if suffixed or len(ident) == 0:\n"
            "        # ordinary numeric literal: its id is 'L' + text + 'E'\n"
            "        out = [76] + lit + [69]  # type: List[int]\n"
            "        return out\n"
            "    else:\n"
            "        # user-defined literal: mangle as the call ident(literal).\n"
            "        result = [99, 108, 76, 95, 90, 108, 105] + ident_id \\\n"
            "            + [69, 76] + lit + [69, 69]  # type: List[int]\n"
            "        return result"),
        "rationale": "a correct impl with the guard negated and the two branches "
                     "swapped must still verify against the frozen spec — both "
                     "value clauses are unchanged. If it failed, the postcondition "
                     "would reject a faithful correct impl (SPEC-TOO-STRONG).",
    },

    # -- POSITIVE CONTROL (soundness): local-variable reshape -----------------
    # Builds the UDL id from named local pieces (prefix / mid / tail) concatenated
    # in a different grouping that is still provably the same PSeq. Pure
    # reassociation of list `+`; keeps every concrete code point. MUST verify.
    {
        "id": "pos-local-reshape",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _BASE, _GOLD_IMPL,
            "    if not suffixed and len(ident) > 0:\n"
            "        prefix = [99, 108, 76, 95, 90, 108, 105]  # type: List[int]\n"
            "        mid = [69, 76]  # type: List[int]\n"
            "        tail = [69, 69]  # type: List[int]\n"
            "        result = prefix + ident_id + mid + lit + tail  # type: List[int]\n"
            "        return result\n"
            "    else:\n"
            "        numL = [76]  # type: List[int]\n"
            "        numE = [69]  # type: List[int]\n"
            "        out = numL + lit + numE  # type: List[int]\n"
            "        return out"),
        "rationale": "a behaviourally-identical reshape that names the constant "
                     "pieces as typed locals and reassociates the list `+` must "
                     "verify (the produced PSeq is unchanged). Else SPEC-TOO-STRONG.",
    },

    # -- ADMISSIBILITY: the precondition admits a normal F2P-shaped input -----
    # Prepends framing asserts that re-derive, from the Requires alone, that BOTH
    # branch guards are reachable (the UDL guard `not suffixed and len(ident)>0 and
    # ident != std` AND the ordinary guard `suffixed or len(ident)==0` are each
    # satisfiable consistent with the precondition), then runs the gold body. If
    # the precondition were contradictory or could not admit a UDL-shaped input
    # the asserts/branches would be unreachable-or-fail => PRECOND-TOO-STRONG.
    # The asserts are pure framing (Implies(False,..)-style and re-statements of
    # Requires facts); they touch no spec region.
    {
        "id": "admiss-both-branches-reachable",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _GOLD_IMPL,
            "    # admissibility witness: the precondition is internally consistent\n"
            "    # and admits both a UDL-shaped and an ordinary-shaped input.\n"
            "    Assert(len(lit) > 0)                         # from Requires\n"
            "    Assert(ToSeq(ident) != PSeq(115, 116, 100))  # from Requires\n"
            "    Assert(Implies(len(ToSeq(ident)) > 0,\n"
            "                   ToSeq(ident_id) == ident_mangle(ToSeq(ident))))\n"
            "    if not suffixed and len(ident) > 0:\n"
            "        result = [99, 108, 76, 95, 90, 108, 105] + ident_id \\\n"
            "            + [69, 76] + lit + [69, 69]  # type: List[int]\n"
            "        return result\n"
            "    else:\n"
            "        out = [76] + lit + [69]  # type: List[int]\n"
            "        return out"),
        "rationale": "the Requires facts (len(lit)>0, ident != std, and the "
                     "ident_id<->ident_mangle tie) are re-derived as asserts and the "
                     "gold body verifies, so the precondition admits a normal "
                     "F2P-shaped input (UDL or ordinary). Else PRECOND-TOO-STRONG.",
    },

    # -- FRAME-MUTATION (uniqueness) #1 [MANDATORY]: write read-only `ident_id` --
    # `ident_id` is held at Acc(list_pred(ident_id), 1/2). This rival appends a
    # code point to `ident_id` and uses the mutated list, faking the mangling by
    # side effect. It MUST be REJECTED for INSUFFICIENT PERMISSION (list.append
    # needs the FULL list_pred, only 1/2 is held). Gold value clauses untouched, so
    # the rejection is attributable to the WRITE, not a proof gap.
    {
        "id": "frame-mutate-ident_id",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _GOLD_IMPL,
            "    if not suffixed and len(ident) > 0:\n"
            "        ident_id.append(69)   # WRITE to a 1/2-permission read-only input\n"
            "        result = [99, 108, 76, 95, 90, 108, 105] + ident_id \\\n"
            "            + [76] + lit + [69, 69]  # type: List[int]\n"
            "        return result\n"
            "    else:\n"
            "        out = [76] + lit + [69]  # type: List[int]\n"
            "        return out"),
        "refinement": "the faithful real patch would mutate the caller's "
                      "ASTIdentifier id string (a shared, cached value reused across "
                      "the parse for str()/describe_signature and other lookups); "
                      "corrupting it produces a wrong mangled id (an extra trailing "
                      "'E') for `5_udl` and breaks str()-round-trip, so "
                      "test_expressions would NOT resolve.",
        "rationale": "rejected by the permission system: `ident_id` is held at "
                     "Acc(list_pred(ident_id), 1/2); `list.append` requires the FULL "
                     "predicate => INSUFFICIENT-PERMISSION. If it verified, the "
                     "read-only frame is unguarded (SPEC-TOO-WEAK / frame leak).",
    },

    # -- FRAME-MUTATION (uniqueness) #2 [supporting]: write read-only `lit` ----
    # `lit` is also Acc(list_pred(lit), 1/2). The ordinary branch appends to `lit`
    # before building the number id. Must be rejected for INSUFFICIENT PERMISSION.
    {
        "id": "frame-mutate-lit",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _GOLD_IMPL,
            "    if not suffixed and len(ident) > 0:\n"
            "        result = [99, 108, 76, 95, 90, 108, 105] + ident_id \\\n"
            "            + [69, 76] + lit + [69, 69]  # type: List[int]\n"
            "        return result\n"
            "    else:\n"
            "        lit.append(69)   # WRITE to a 1/2-permission read-only input\n"
            "        out = [76] + lit  # type: List[int]\n"
            "        return out"),
        "refinement": "mutating the numeric-literal text in place corrupts the "
                      "shared literal token (its str() and any later get_id), so the "
                      "produced id is not the gold `L<text>E` and the surrounding "
                      "declaration mangling diverges; test_expressions fails.",
        "rationale": "rejected for INSUFFICIENT PERMISSION on `lit` (held at 1/2): "
                     "`list.append` needs the full list_pred. Frame integrity of the "
                     "read-only numeric-literal text.",
    },

    # -- PARTIAL-DOMAIN (uniqueness) #1: the PRE-PATCH rival -------------------
    # Never builds a UDL: always returns the ordinary number id `L+lit+E`. Correct
    # on the ENTIRE ordinary subdomain (suffixed or no identifier) but diverges on
    # the UDL subdomain (unsuffixed + trailing identifier). This is exactly
    # model_prepatch.py's defect. Must be REJECTED by the UDL Ensures clause.
    {
        "id": "partial-prepatch-no-udl",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _GOLD_IMPL,
            "    # PRE-PATCH rival: never builds a UDL; always the ordinary number id.\n"
            "    out = [76] + lit + [69]  # type: List[int]\n"
            "    return out"),
        "refinement": "this IS the pre-patch behaviour: the suffix-consuming loop "
                      "`while self.current_char in 'uUlLfF'` never recognises a UDL, "
                      "so `6.62607015e-34q_J` leaves `q_J` unconsumed and the parse "
                      "fails (`Expected end of definition`); test_expressions does "
                      "NOT resolve.",
        "rationale": "rejected by `Implies(not suffixed and len(ident)>0 and "
                     "ident != std, ToSeq(Result()) == udl_id_seq(lit, ident))`: on "
                     "a UDL input the result must be the clL_Zli mangling, not "
                     "`L+lit+E`. If it verified, the discriminating fix is unpinned "
                     "(SPEC-TOO-WEAK).",
    },

    # -- PARTIAL-DOMAIN (uniqueness) #2: raw `ident` instead of `ident_id` -----
    # The strongest reasoned attack. Uses the raw identifier TEXT (`ident`) in the
    # mangling instead of the precomputed length-prefixed id (`ident_id`). On
    # `5_udl` gold gives `clL_Zli4_udlEL5EE` but this gives `clL_Zli_udlEL5EE`
    # (missing the `4` length prefix). Nagini CANNOT prove ToSeq(ident) ==
    # ident_mangle(ToSeq(ident)) (the precondition ties only ident_id to the
    # mangling), so udl_id_seq (which embeds ident_mangle) is not matched => reject.
    {
        "id": "partial-raw-ident-no-length-prefix",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _GOLD_IMPL,
            "    if not suffixed and len(ident) > 0:\n"
            "        # WRONG: raw identifier text, missing the length prefix that\n"
            "        # ident_mangle (== ident_id) supplies.\n"
            "        result = [99, 108, 76, 95, 90, 108, 105] + ident \\\n"
            "            + [69, 76] + lit + [69, 69]  # type: List[int]\n"
            "        return result\n"
            "    else:\n"
            "        out = [76] + lit + [69]  # type: List[int]\n"
            "        return out"),
        "refinement": "the real `ASTUserDefinedLiteral.get_id` calls "
                      "`self.ident.get_id(version)`, which is the length-prefixed "
                      "`str(len)+ident` (e.g. `4_udl`), NOT the raw `_udl`. Emitting "
                      "the raw identifier yields `clL_Zli_udlEL5EE` instead of the "
                      "expected `clL_Zli4_udlEL5EE`, so every UDL row of "
                      "test_expressions fails.",
        "rationale": "rejected by the UDL Ensures: udl_id_seq embeds "
                     "ident_mangle(ident); the proof can substitute only `ident_id` "
                     "(tied by precondition) for ident_mangle(ident), and "
                     "len(ident_mangle(ident)) > len(ident) by the axiom, so `ident` "
                     "is NOT provably equal to ident_mangle(ident). If it verified, "
                     "the length-prefix component is unpinned (SPEC-TOO-WEAK).",
    },

    # -- PARTIAL-DOMAIN (uniqueness) #3: ignore `suffixed` ---------------------
    # Builds a UDL whenever a trailing identifier is present, REGARDLESS of the
    # suffix flag. Correct on the unsuffixed-UDL and the no-identifier subdomains,
    # but diverges on the SUFFIXED + trailing-identifier subdomain (where the
    # ordinary clause demands `number_id_seq`, not the UDL mangling).
    {
        "id": "partial-ignores-suffixed",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _GOLD_IMPL,
            "    if len(ident) > 0:\n"
            "        # WRONG: builds a UDL even when a recognised numeric suffix is\n"
            "        # present (ignores `suffixed`).\n"
            "        result = [99, 108, 76, 95, 90, 108, 105] + ident_id \\\n"
            "            + [69, 76] + lit + [69, 69]  # type: List[int]\n"
            "        return result\n"
            "    else:\n"
            "        out = [76] + lit + [69]  # type: List[int]\n"
            "        return out"),
        "refinement": "in the real parser a recognised numeric suffix (e.g. the `u` "
                      "in an integer with `uludl`... — or any `*_literal_suffix_re` "
                      "match) consumes into the literal and `hasSuffix` returns the "
                      "plain ASTNumberLiteral; treating a suffixed literal as a UDL "
                      "would wrongly mangle e.g. a genuinely-suffixed token, "
                      "diverging from `L<text>E` on that subdomain.",
        "rationale": "rejected by `Implies(suffixed or len(ident)==0, "
                     "ToSeq(Result()) == number_id_seq(lit))`: on the "
                     "(suffixed AND len(ident)>0) subdomain the result must be the "
                     "ordinary `L+lit+E`, not the UDL mangling. If it verified, the "
                     "suffix discriminator is unpinned (SPEC-TOO-WEAK).",
    },

    # -- PARTIAL-DOMAIN (uniqueness) #4: drop one `E` frame --------------------
    # A near-miss off-by-one: omits the inter-part `E` (uses [76] instead of
    # [69,76]) so the UDL id is `clL_Zli<id>L<lit>EE` (missing the `E` after the
    # identifier id). Correct everywhere EXCEPT the exact byte layout of the UDL
    # id. Must be rejected by the exact-equality UDL clause.
    {
        "id": "partial-drop-mid-E",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _GOLD_IMPL,
            "    if not suffixed and len(ident) > 0:\n"
            "        # WRONG: omit the 'E' that frames the identifier id.\n"
            "        result = [99, 108, 76, 95, 90, 108, 105] + ident_id \\\n"
            "            + [76] + lit + [69, 69]  # type: List[int]\n"
            "        return result\n"
            "    else:\n"
            "        out = [76] + lit + [69]  # type: List[int]\n"
            "        return out"),
        "refinement": "the real mangling is `clL_Zli{id}E{L lit E}E`; dropping the "
                      "`E` after the identifier id gives `clL_Zli4_udlL5EE` instead "
                      "of `clL_Zli4_udlEL5EE`, a non-conformant Itanium mangling that "
                      "every UDL row of test_expressions rejects.",
        "rationale": "rejected by the exact `ToSeq(Result()) == udl_id_seq(...)` "
                     "clause: udl_id_seq has an explicit `+ PSeq(69)` between the "
                     "identifier id and the number id, absent here. Off-by-one byte "
                     "layout (SPEC-TOO-WEAK if admitted).",
    },

    # -- PARTIAL-DOMAIN (uniqueness) #5: wrong ordinary framing ----------------
    # Correct on the entire UDL subdomain, but the ordinary branch drops the
    # trailing `E` (returns `L+lit` instead of `L+lit+E`). Diverges on the ordinary
    # subdomain (suffixed or no identifier). Must be rejected by number_id_seq.
    {
        "id": "partial-ordinary-drop-E",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _GOLD_IMPL,
            "    if not suffixed and len(ident) > 0:\n"
            "        result = [99, 108, 76, 95, 90, 108, 105] + ident_id \\\n"
            "            + [69, 76] + lit + [69, 69]  # type: List[int]\n"
            "        return result\n"
            "    else:\n"
            "        # WRONG: ordinary number id missing the trailing 'E'.\n"
            "        out = [76] + lit  # type: List[int]\n"
            "        return out"),
        "refinement": "the real `ASTNumberLiteral.get_id` is `\"L%sE\" % data`; "
                      "returning `L<text>` (no trailing `E`) mismangles every plain "
                      "number literal and the embedded number id inside every UDL, so "
                      "the expected `...L5EE` / `...EL6.62607015e-34EE` strings fail.",
        "rationale": "rejected by `Implies(suffixed or len(ident)==0, "
                     "ToSeq(Result()) == number_id_seq(lit))` with number_id_seq = "
                     "`L + lit + E`; the missing `E` breaks the equality. Partial "
                     "(ordinary-subdomain) divergence.",
    },

    # =======================================================================
    # SECOND MODELED FUNCTION: c_number_literal_id (simpler-dialect suffix decision)
    # =======================================================================

    # -- POSITIVE CONTROL (soundness): C-domain local-variable reshape --------
    # Builds the two id forms from named local pieces, reassociating the list `+`,
    # still provably the same PSeq. Pure reshape; keeps every code point. MUST verify.
    {
        "id": "c-pos-local-reshape",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _BASE, _C_GOLD_IMPL,
            "    L = [76]  # type: List[int]\n"
            "    E = [69]  # type: List[int]\n"
            "    if valid:\n"
            "        body = lit + trail  # type: List[int]\n"
            "        out = L + body + E  # type: List[int]\n"
            "        return out\n"
            "    else:\n"
            "        plain = L + lit + E  # type: List[int]\n"
            "        return plain"),
        "rationale": "a behaviourally-identical reshape of c_number_literal_id that "
                     "names the 'L'/'E' frames as typed locals and reassociates the "
                     "list `+` must verify (the produced PSeq is unchanged). Else "
                     "SPEC-TOO-STRONG.",
    },

    # -- C-domain FRAME-MUTATION (uniqueness) [MANDATORY]: write read-only `lit` --
    # `lit` is held at Acc(list_pred(lit), 1/2). Appending to it before building the
    # id fakes the text by side effect; MUST be rejected for INSUFFICIENT PERMISSION.
    {
        "id": "c-frame-mutate-lit",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _C_GOLD_IMPL,
            "    if valid:\n"
            "        lit.append(69)   # WRITE to a 1/2-permission read-only input\n"
            "        out = [76] + lit + trail + [69]  # type: List[int]\n"
            "        return out\n"
            "    else:\n"
            "        plain = [76] + lit + [69]  # type: List[int]\n"
            "        return plain"),
        "refinement": "the faithful parser slices `self.definition[pos:self.pos]` "
                      "from the shared definition buffer; corrupting the literal text "
                      "in place would mismangle the number and break str()-round-trip.",
        "rationale": "rejected by the permission system: `lit` is held at "
                     "Acc(list_pred(lit), 1/2); `list.append` requires the FULL "
                     "predicate => INSUFFICIENT-PERMISSION. If it verified, the "
                     "read-only frame is unguarded (SPEC-TOO-WEAK / frame leak).",
    },

    # -- C-domain PARTIAL (uniqueness) #1: the PRE-PATCH always-fold rival ------
    # Always folds the whole trailing run into the text (the old maximal-run loop),
    # regardless of `valid`. Correct on the recognised-suffix subdomain but diverges
    # on the non-recognised subdomain. This IS model_prepatch's c-domain defect.
    {
        "id": "c-partial-prepatch-always-fold",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _C_GOLD_IMPL,
            "    # PRE-PATCH rival: fold the WHOLE trailing run unconditionally.\n"
            "    out = [76] + lit + trail + [69]  # type: List[int]\n"
            "    return out"),
        "refinement": "this IS the pre-patch maximal-run loop "
                      "`while self.current_char in 'uUlLfF': self.pos += 1`, which "
                      "folds any uUlLfF run into the literal text even when it is not "
                      "a recognised numeric suffix; e.g. float `5.0` + `u` would give "
                      "`L5.0uE` instead of the gold `L5.0E`.",
        "rationale": "rejected by `Implies(not valid, ToSeq(Result()) == "
                     "number_id_seq(ToSeq(lit)))`: on a non-recognised run the result "
                     "must be `L+lit+E`, not `L+lit+trail+E`. If it verified, the "
                     "discriminating fix is unpinned (SPEC-TOO-WEAK).",
    },

    # -- C-domain PARTIAL (uniqueness) #2: drop the trailing run even when valid --
    # Never folds the suffix (always returns L+lit+E). Correct on the non-recognised
    # subdomain, but diverges on the recognised-suffix subdomain (where the suffix
    # must be folded). Must be rejected by the `valid` clause.
    {
        "id": "c-partial-never-fold",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _C_GOLD_IMPL,
            "    # WRONG: never fold the suffix run, even when it is recognised.\n"
            "    plain = [76] + lit + [69]  # type: List[int]\n"
            "    return plain"),
        "refinement": "a recognised suffix (e.g. integer `5` + `ul`, float `5.0` + "
                      "`f`) is part of the literal text in the real parser "
                      "(`self.definition[pos:self.pos]` spans it); dropping it gives "
                      "`L5E`/`L5.0E` instead of the gold `L5ulE`/`L5.0fE`.",
        "rationale": "rejected by `Implies(valid, ToSeq(Result()) == "
                     "number_id_seq(ToSeq(lit) + ToSeq(trail)))`: on a recognised "
                     "suffix the result must include `trail`. If it verified, the "
                     "suffix-folding is unpinned (SPEC-TOO-WEAK).",
    },

    # -- C-domain PARTIAL (uniqueness) #3: drop the trailing `E` frame ----------
    # Off-by-one: returns L+lit(+trail) with no closing E. Must be rejected by the
    # exact number_id_seq equality (which ends in PSeq(69)).
    {
        "id": "c-partial-drop-E",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _C_GOLD_IMPL,
            "    if valid:\n"
            "        # WRONG: missing the closing 'E'.\n"
            "        out = [76] + lit + trail  # type: List[int]\n"
            "        return out\n"
            "    else:\n"
            "        plain = [76] + lit  # type: List[int]\n"
            "        return plain"),
        "refinement": "the real `ASTNumberLiteral.get_id` is `\"L%sE\" % data`; "
                      "dropping the trailing `E` mismangles every number literal in "
                      "this dialect too.",
        "rationale": "rejected by both clauses (number_id_seq = `L + text + E` ends "
                     "in PSeq(69)); the missing `E` breaks the equality. Off-by-one "
                     "byte layout (SPEC-TOO-WEAK if admitted).",
    },
]


# ===========================================================================
# AXIOM LANE  (one @ContractOnly axiom: ident_mangle, A-consumed)
# ===========================================================================
#
# The runner mounts ONLY the probe script at /work; axiom_check.py / model.py are
# NOT in-container, so the soundness probe EMBEDS axiom_check.py's source (read on
# the HOST at manifest-load time) and EXECUTES the REAL ASTIdentifier.get_id /
# ASTNumberLiteral.get_id / ASTUserDefinedLiteral.get_id / DefinitionParser — it
# never regex-scrapes source. All file reads are utf-8-safe (the probe reads no
# files; it imports the patched module that lives in-container after apply_gold).

_AXIOM_CHECK_SRC = (Path(__file__).parent / "axiom_check.py").read_text(encoding="utf-8")

# axiom-soundness: run the real callees (ident_mangle on its contracted domain +
# the excluded-branch deviation proof that the `std` restriction is load-bearing,
# plus the A-reference number_id_seq/udl_id_seq deep models and the end-to-end F2P
# parser decision) via the persisted, gold-grounded axiom_check.py. Exit 0 iff
# every obligation holds; the in-container patched `sphinx.domains.cpp` is the
# real oracle.
_AX_SOUND_PROBE = _AXIOM_CHECK_SRC + """

# ---- PBT axiom-soundness driver (appended) --------------------------------
import sys as _sys
print("PBT axiom-soundness: running real-callee soundness obligations "
      "(ident_mangle on the contracted domain + 5000 fuzz idents; excluded-branch "
      "deviation proof for std/~dtor/@anon; number_id_seq + udl_id_seq deep models "
      "vs real get_id; end-to-end F2P UDL-token parser decision)")
_rc = main()
_sys.exit(0 if _rc == 0 else 1)
"""

# axiom-containment: the model calls ident_mangle ONLY where its arguments are
# provably in the axiom's Requires domain (len(ident)>0 and ident != std). The
# axiom appears inside udl_id_seq (which carries its own
# Requires(len(ident)>0); Requires(ident != PSeq(115,116,100))) and inside
# number_literal_id's precondition tie (guarded by len(ToSeq(ident))>0 and the
# function-level Requires ToSeq(ident) != PSeq(115,116,100)). This probe parses
# model.py statically (stdlib only, utf-8-safe), enumerates EVERY ident_mangle
# call site, and asserts each is inside a context that establishes both domain
# facts — i.e. every caller-reachable callee input lies inside the axiom domain.
_MODEL_SRC = (Path(__file__).parent / "model.py").read_text(encoding="utf-8")

_AX_COVER_PROBE = (
    "import sys, ast\n"
    "SRC = " + repr(_MODEL_SRC) + "\n"
    "tree = ast.parse(SRC)\n"
    "funcs = {n.name: n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)}\n"
    "# 1) enumerate every call to ident_mangle and its enclosing function.\n"
    "sites = []  # (enclosing_func_name, arg_src)\n"
    "for fname, fnode in funcs.items():\n"
    "    for sub in ast.walk(fnode):\n"
    "        if isinstance(sub, ast.Call) and getattr(sub.func, 'id', None) == 'ident_mangle':\n"
    "            if len(sub.args) != 1:\n"
    "                print('UNEXPECTED arity to ident_mangle:', len(sub.args)); sys.exit(1)\n"
    "            sites.append((fname, ast.dump(sub.args[0])))\n"
    "print('ident_mangle call sites (caller, arg):')\n"
    "for s in sites: print('  ', s)\n"
    "if not sites:\n"
    "    print('NO ident_mangle call sites found in model.py'); sys.exit(1)\n"
    "callers = set(f for f, _ in sites)\n"
    "# the model never imports ident_mangle outside its own bundle; it is the\n"
    "# @ContractOnly axiom, consumed only inside udl_id_seq (Ensures helper) and\n"
    "# the number_literal_id precondition tie. Any OTHER caller would need its own\n"
    "# domain proof, so flag it.\n"
    "EXPECTED_CALLERS = {'udl_id_seq', 'number_literal_id'}\n"
    "extra = callers - EXPECTED_CALLERS\n"
    "if extra:\n"
    "    print('UNEXPECTED caller of ident_mangle (needs its own domain proof):', extra)\n"
    "    sys.exit(1)\n"
    "# 2) udl_id_seq must carry Requires(len(ident)>0) and Requires(ident != std).\n"
    "def func_src(fn):\n"
    "    lines = SRC.splitlines()\n"
    "    return '\\n'.join(lines[fn.lineno-1: getattr(fn, 'end_lineno', fn.lineno)])\n"
    "udl = funcs.get('udl_id_seq')\n"
    "if udl is None:\n"
    "    print('udl_id_seq missing'); sys.exit(1)\n"
    "udl_src = func_src(udl)\n"
    "if 'Requires(len(ident) > 0)' not in udl_src:\n"
    "    print('udl_id_seq does NOT require len(ident)>0 before calling ident_mangle'); sys.exit(1)\n"
    "if 'Requires(ident != PSeq(115, 116, 100))' not in udl_src:\n"
    "    print('udl_id_seq does NOT exclude the reserved std before calling ident_mangle'); sys.exit(1)\n"
    "# 3) number_literal_id ties ident_id only under len(ToSeq(ident))>0, and the\n"
    "#    function-level Requires excludes std; both establish the axiom domain.\n"
    "nli = funcs.get('number_literal_id')\n"
    "if nli is None:\n"
    "    print('number_literal_id missing'); sys.exit(1)\n"
    "nli_src = func_src(nli)\n"
    "if 'ToSeq(ident) != PSeq(115, 116, 100)' not in nli_src:\n"
    "    print('number_literal_id does NOT exclude the reserved std (code points 115,116,100)'); sys.exit(1)\n"
    "if 'Implies(len(ToSeq(ident)) > 0' not in nli_src:\n"
    "    print('number_literal_id ident_id tie is NOT guarded by len(ToSeq(ident))>0'); sys.exit(1)\n"
    "print('AXIOM-CONTAINMENT OK: ident_mangle is called only inside udl_id_seq "
    "(which requires len(ident)>0 and ident != std) and the number_literal_id "
    "precondition tie (guarded by len(ToSeq(ident))>0 with the function excluding "
    "std). Every caller-reachable ident_mangle input is nonempty and != std, "
    "exactly the axiom Requires domain.')\n"
    "sys.exit(0)\n"
)

AXIOM_TESTS = [
    {
        "id": "ax-sound-ident_mangle",
        "axiom": "ident_mangle",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _AX_SOUND_PROBE,
        "rationale": "the proof consumes ident_mangle's Ensures (length-prefixed "
                     "suffix: len(Result())>len(ident) and Result endswith ident) on "
                     "the contracted domain (nonempty, != std). The real "
                     "ASTIdentifier.get_id must meet it on boundary + 5000 fuzz "
                     "idents, AND the excluded `std`/`~`/`@` branches must genuinely "
                     "deviate (so the restriction is load-bearing, the over-claim "
                     "caught not hidden). The A-reference number_id_seq/udl_id_seq "
                     "deep models and the end-to-end F2P parser decision are checked "
                     "too. A violation => AXIOM-UNSOUND. Runs the gold-grounded "
                     "axiom_check.py in the instance image.",
    },
    {
        "id": "ax-cover-ident_mangle",
        "axiom": "ident_mangle",
        "kind": "axiom-containment",
        "expect": "covered",
        "apply_gold": True,
        "probe": _AX_COVER_PROBE,
        "rationale": "ident_mangle's Requires is len(ident)>0 and ident != std. The "
                     "model calls it only inside udl_id_seq (which itself requires "
                     "both) and the number_literal_id precondition tie (guarded by "
                     "len(ToSeq(ident))>0 with the function-level std exclusion). "
                     "Every caller-reachable input is therefore inside the axiom "
                     "domain (containment holds). A reachable ident outside "
                     "(empty, or == std) would be AXIOM-TOO-WEAK-FOR-CALLER.",
    },
]
