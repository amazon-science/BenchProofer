# properties.py — G-PBT falsification battery for django__django-15503 (lean lane).
# PORTED from the nagini sibling's battery: the adversarial ARGUMENTS are carried
# over, the mechanics re-expressed against this backend's carrier. Each SPEC case is
# a FULL Solution.lean variant that shares the FROZEN spec byte-for-byte (only the
# impl region is edited); scope is checked by variant_scope + the Lean verifier. Every
# expect="reject" case carries a refutation `witness`: a self-contained snippet that
# ELABORATES against the rival and FAILS on the frozen solution, so the rejection is
# attributable to the spec and not to a tactic script that merely stopped matching a
# reshaped impl.
#
# DEFENDED SURFACE (read from Solution.lean / mapping.md / instance.json):
#   keyLookupPath : Bool → String → List String → String  (precondition: keys ≠ [])
#   A key-location path is assembled from a path PREFIX (`lhsJsonPath`), a
#   non-empty list of key steps (`keys`), and a Bool `byName` carrying WHICH of the
#   two addressing forms the enquiry wants for the FINAL step. The single
#   postcondition `problem_spec_keyLookupPath` pins the WHOLE assembled string as
#       result = lhsJsonPath
#                  ++ (pathOfKeys keys.dropLast ++ finalSegment byName (keys.getLastD ""))
#   i.e. four independent, top-level-visible pieces:
#     (P) the PREFIX is reproduced verbatim at the front;
#     (I) the INTERMEDIATE steps (all keys but the last) are rendered by
#         `pathOfKeys` — each addressed by WHAT ITS TEXT DENOTES, where a text
#         reading as a base-10 integer becomes a bracketed positional step and
#         every other text a named member;
#     (F) the FINAL step is rendered by `finalSegment byName` — the NAMED-MEMBER
#         form (`"." ++ encodeKey k`) when the enquiry asks for a member of a given
#         name, REGARDLESS of whether the text reads as a number;
#     (M) and — the same clause read the other way — the DENOTED-LOCATION form
#         (`renderSegment k`, i.e. the bracketed positional step for a text that
#         reads as an integer) when THAT is what the enquiry asks for. Clause (M)
#         is what makes the final step's addressing form a DISPATCHABLE choice
#         rather than a constant: an assembly that hardwires either form satisfies
#         one half of the conjunction and violates the other.
#   The load-bearing content is the PAIR (F)+(M). (F) alone is what the pre-patch
#   code violates — it routed a digit-run final key through the positional
#   rendering it applied to every step. (M) alone is what an assembly violates if
#   it reaches the named-member form by INLINING that token at the assembly site,
#   which leaves no way for a caller that wants the denoted-location form to get
#   it. Both obligations are live and neither implies the other, so both are
#   attacked below.
#   `encodeKey` is an OPAQUE callee (a JSON string serializer whose exact escaping
#   is irrelevant), so witnesses cannot compute its value — but they never need to:
#   the two addressing forms differ in their FIRST glyph (`.` for named vs `[` for
#   positional), which is transparent and decides the disequality without any
#   property of `encodeKey` (see the witness note).
#
# CARRIER NOTE / relation to the nagini sibling. Nagini modeled a DIFFERENT,
# narrower slice: `compile_final_key_segment(key: List[int]) -> List[int]`, the
# per-CODE-POINT copy of ONE key between a fixed `."` prefix and `"` suffix, held
# under fractional read permission. This backend models the RICHER object — the
# whole RHS path assembly over `String`/`List String`, with the key serializer
# kept opaque rather than spelled out char-by-char, and with the final step's
# addressing form carried as an input rather than fixed. The porting map:
#   * nagini `prepatch-array-index` (emit the array-element step for an all-digit
#     key) -> R-prepatch-array-index here, attacking clause (F). This IS the
#     modeled bug and the F2P discriminator; it is the strongest near-miss.
#   * nagini `drop-last-char` / `skip-first-char` / `wrong-quote` were attacks on
#     the INTERNAL byte layout of the single key's segment (off-by-one on the
#     character copy loop; the open/close quote glyph). They DO port — see
#     R-truncate-final-key, R-skip-first-char and R-hand-quoted-final-key below.
#     Opacity of `encodeKey` does not block them, because neither the rival nor
#     the witness has to compute the serializer's value:
#       - the key TEXT is transparent `String` data, so an off-by-one is written
#         by handing the encoder a DIFFERENT key (`k.toList.dropLast` / `.tail`)
#         rather than by peering inside it;
#       - a wrong quote glyph is written by BYPASSING the encoder and hand-rolling
#         the token, which the spec's named-member form `"." ++ encodeKey k` pins
#         against directly;
#       - the refutation is then stated at a point described by HYPOTHESIS (the
#         serializer does not identify two distinct key texts, resp. does not
#         equal the hand-rolled token), which is precisely the technique an opaque
#         carrier admits: no tactic can derive `False` from `encodeKey a ≠
#         encodeKey b`, so the gate's consistency probe confirms satisfiability.
#     Each was BUILT both ways (elaborates against the rival, FAILS on the frozen
#     solution by a semantic refutation of the concrete claim, consistency probe
#     does not close) before being recorded here.
#   * the richer carrier additionally exposes STRUCTURAL rivals the nagini
#     single-key carrier had no counterpart for:
#       - R-drop-lhs-prefix attacks clause (P): the prefix binder `lhsJsonPath`.
#       - R-drop-intermediate attacks clause (I): the intermediate-steps portion
#         over a multi-key list (a `keys` shape nagini could not express).
#       - R-reverse-intermediate attacks clause (I) on the ORDER of the descent
#         rather than on its presence, at `keys` of LENGTH 3 — the shortest point
#         where reversal is observable, and the only case reaching that length.
#       - R-hardwire-named-final, R-swap-final-forms and
#         R-named-final-only-when-flat attack clause (M): the DISPATCH of the
#         final step's addressing form. These are the rivals that get clause (F)
#         right and are still wrong, so they are the ones a spec pinning only the
#         named form would admit. They live on the sub-domain `byName = false`
#         with a final key whose text reads as an integer — the ONLY region where
#         the two forms differ at all, hence the only region where the dispatch is
#         observable, and each probes a different point of it.
#   Every reject witness probes a DISTINCT (byName, lhsJsonPath, keys) point so all
#   four spec binders (the form selector, the prefix, the list, its final element)
#   are exercised by some rival.
#   * nagini `honest-cheapest` / `pos-prefix-reshape` (soundness positives) port to
#     pos-gold and pos-pure-reshape; the richer carrier also supports a genuinely
#     re-proven reshape (pos-foldl-reshape) whose proof does NOT reduce to `rfl`.
#   * nagini `admiss-numeric-key` (ADMISSIBILITY) ports to admiss-numeric-final-key,
#     which now pins BOTH addressing forms at the same numeric final key.
#
# LANES THAT DO NOT PORT:
#   * FRAME-MUTATION (nagini's MANDATORY `frame-mutate-key`: `key` was
#     Acc(list_pred(key),1/2) read-only and the rival wrote key[0]=34). Lean is
#     referentially transparent — no aliasing, no fractional permission — so a
#     "store through a read-only input" rival is not expressible and the whole
#     lane is VACUOUS here. See 'assessment'.
#     (ADMISSIBILITY does port — see admiss-numeric-final-key. The lean
#     precondition is only `keys ≠ []`, so the lane is cheap rather than absent:
#     it is still worth pinning that a digit-run FINAL key — the F2P shape — is
#     admitted with no extra hypothesis AND lands on the named-member form when
#     the enquiry asks for a member of that name, and on the positional form when
#     it asks about the denoted location, since a spec that quietly excluded
#     either would be PRECOND-TOO-STRONG on exactly the sub-domain the issue is
#     about.)
#   * DIVERGENCE / NON-TERMINATION. The frozen impl is a total Lean `def` and this
#     bundle sets no `loom.semantics.termination`, so the obligation is discharged
#     against a total carrier: a rival must be a `def` that elaborates, and one
#     that does terminates. A diverging rival is expressible only as `partial def`,
#     and that IS admissible to variant_scope (measured: scope-OK, and the variant
#     is REJECTED, exit 1) — but it is NOT shippable as a reject case, because a
#     `partial def` is opaque to the equation compiler: it has no unfolding
#     equations, so `unfold`/`simp` cannot reduce it and NO witness can hold of it.
#     Measured: the most permissive witness shape (literal input, refutation over
#     `String.data`) fails against the partial rival too (rival exit 1 =>
#     `witness-unproven`, an inconclusive outcome, not a rejection). So the class is
#     VACUOUS here for a demonstrated reason — every diverging rival is
#     witness-less by construction on this carrier — rather than because "a
#     non-terminating implementation cannot be written", which is false. This is
#     NOT the velvet-partial known-hole disposition: nothing verifies vacuously
#     here. See 'assessment'.
#   * AXIOM_TESTS. `encodeKey` is declared `opaque` with NO consumed `_prop` axiom
#     (the proof needs no property of it — only WHICH addressing form is applied).
#     The axiom lane is G-AX's job and is empty here regardless. See AXIOM_TESTS
#     below.
from pathlib import Path

INSTANCE = "django__django-15503"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# --- anchor ------------------------------------------------------------------------
# The full frozen impl body, lying ENTIRELY inside impl-start/impl-end and unique in
# the file. Every rival (and the positives) swap THIS block. The frozen proof body is
# left untouched by every case: for the reject rivals the gate reads the WITNESS (in a
# file with the obligation removed), not the rival's own build; the one reshaped
# positive is close enough that the frozen `rfl` still closes (verified).
_IMPL = (
    "def implementation_keyLookupPath\n"
    "    (byName : Bool) (lhsJsonPath : String) (keys : List String) : String := Id.run do\n"
    "  let intermediate := keys.dropLast\n"
    "  let finalKey := keys.getLastD \"\"\n"
    "  let mut rhsJsonPath := pathOfKeys intermediate\n"
    "  rhsJsonPath := rhsJsonPath ++ finalSegment byName finalKey\n"
    "  return lhsJsonPath ++ rhsJsonPath"
)
assert _BASE.count(_IMPL) == 1, "impl anchor drifted from expected text"

_PROOF = (
    "  intro byName lhsJsonPath keys _\n"
    "  unfold problem_spec_keyLookupPath implementation_keyLookupPath\n"
    "  rfl"
)
assert _BASE.count(_PROOF) == 1, "proof anchor drifted from expected text"

_SIG = (
    "def implementation_keyLookupPath\n"
    "    (byName : Bool) (lhsJsonPath : String) (keys : List String) : String := Id.run do\n"
)


# ===========================================================================
# POSITIVE CONTROLS (soundness) — must VERIFY (else SPEC-TOO-STRONG).
# ===========================================================================

# pos-gold: the frozen impl, unchanged (the honest cheapest control). Its faithful
# per-step assembly — intermediate keys addressed by what their text denotes, the final
# key addressed in the form the caller selects — satisfies the postcondition by the
# frozen proof. Must verify; if it does not, the spec is SPEC-TOO-STRONG (unsatisfiable
# by the very computation it describes).
_POS_GOLD = _BASE

# pos-pure-reshape: a structurally DIFFERENT but behaviourally identical CORRECT impl —
# a pure `let`-expression (no `Id.run do`, no `mut`, no early `return`) building the RHS
# in one binding and concatenating. Output equals the frozen impl's on every input. The
# `theorem correct_keyLookupPath` STATEMENT is byte-identical and the FROZEN proof body
# still closes (the reshape is definitionally equal, so `rfl` discharges it — verified),
# so no reproof, no new axiom/lemma/sorry. If it FAILS => SPEC-TOO-STRONG (postcondition
# over-fit to the monadic impl shape).
_POS_PURE = _swap(
    _BASE,
    _IMPL,
    "def implementation_keyLookupPath\n"
    "    (byName : Bool) (lhsJsonPath : String) (keys : List String) : String :=\n"
    "  let rhs := pathOfKeys keys.dropLast ++ finalSegment byName (keys.getLastD \"\")\n"
    "  lhsJsonPath ++ rhs",
)

# pos-foldl-reshape: a CORRECT impl whose shape is far enough from the frozen one
# that the frozen `rfl` does NOT close it — the intermediate steps are folded
# directly onto the prefix as an accumulator, so `pathOfKeys` never appears in the
# impl at all. Because the proof must be genuinely RE-DERIVED (an induction over
# the step list showing the accumulating fold equals `prefix ++ String.join`), this
# positive tests that the postcondition is satisfiable by the BEHAVIOUR rather than
# by a shape that happens to be definitionally equal. The theorem STATEMENT is
# byte-identical; only the tactic body differs (which variant_scope permits, and
# which is what "reprove" means). No new axiom/lemma/sorry: the induction lives in
# a `have` inside the existing proof body. Note the addressing-form selector is
# still threaded through untouched — a correct alternative shape must keep the
# dispatch, and this control confirms the spec does not demand any particular way
# of expressing it.
_POS_FOLDL = _swap(
    _swap(
        _BASE,
        _IMPL,
        "def implementation_keyLookupPath\n"
        "    (byName : Bool) (lhsJsonPath : String) (keys : List String) : String :=\n"
        "  (keys.dropLast.foldl (fun acc k => acc ++ renderSegment k) lhsJsonPath)\n"
        "    ++ finalSegment byName (keys.getLastD \"\")",
    ),
    _PROOF,
    "  intro byName lhsJsonPath keys _\n"
    "  unfold problem_spec_keyLookupPath implementation_keyLookupPath\n"
    "  have L : ∀ (l : List String) (s : String),\n"
    "      List.foldl (fun r x => r ++ x) s l\n"
    "        = s ++ List.foldl (fun r x => r ++ x) \"\" l := by\n"
    "    intro l\n"
    "    induction l with\n"
    "    | nil => intro s; simp\n"
    "    | cons a t ih =>\n"
    "      intro s\n"
    "      simp only [List.foldl_cons]\n"
    "      rw [ih (s ++ a), ih (\"\" ++ a)]\n"
    "      simp [String.append_assoc]\n"
    "  rw [← List.foldl_map (f := renderSegment) (g := fun r x => r ++ x)]\n"
    "  rw [L]\n"
    "  simp only [pathOfKeys, String.join, String.append_assoc]",
)

# admiss-numeric-final-key: the ADMISSIBILITY lane. Instantiates the frozen
# obligation at the F2P-shaped input — a SINGLETON list whose sole (= final) key is
# a digit run — and pins that (a) the precondition `keys ≠ []` is establishable
# there with no extra hypothesis, (b) when the enquiry asks about a member of that
# NAME the assembled path addresses it as a named member, and (c) when the enquiry
# asks about whatever the text denotes, the SAME assembly addresses it as the
# bracketed positional step. Stated as an anonymous `example` inside the impl
# region, so it declares no name (variant_scope admits it: no new
# theorem/lemma/axiom) and the frozen obligation and its proof are untouched. If
# this FAILS, the spec excludes the very sub-domain the issue is about =>
# PRECOND-TOO-STRONG.
_ADMISS = _swap(
    _BASE,
    _IMPL,
    _IMPL + "\n"
    "\n"
    "/-- The obligation is establishable at an F2P-shaped NUMERIC final key: a\n"
    "digit-run step satisfies the only precondition (a non-empty step list) with no\n"
    "extra hypothesis, and the SAME assembly addresses it as a named member when the\n"
    "enquiry asks for that name and as the positional step when the enquiry asks\n"
    "about the denoted location. -/\n"
    "example :\n"
    "    ([\"1111\"] : List String) ≠ [] ∧\n"
    "    problem_spec_keyLookupPath true \"$\" [\"1111\"]\n"
    "      (implementation_keyLookupPath true \"$\" [\"1111\"]) ∧\n"
    "    problem_spec_keyLookupPath false \"$\" [\"1111\"]\n"
    "      (implementation_keyLookupPath false \"$\" [\"1111\"]) ∧\n"
    "    implementation_keyLookupPath true \"$\" [\"1111\"]\n"
    "      = \"$\" ++ (\".\" ++ encodeKey \"1111\") ∧\n"
    "    implementation_keyLookupPath false \"$\" [\"1111\"] = \"$\" ++ \"[1111]\" := by\n"
    "  have hn : finalSegment true \"1111\" = \".\" ++ encodeKey \"1111\" := rfl\n"
    "  have hp : finalSegment false \"1111\" = \"[1111]\" := by decide\n"
    "  refine ⟨by simp, ?_, ?_, ?_, ?_⟩\n"
    "  · unfold problem_spec_keyLookupPath implementation_keyLookupPath\n"
    "    rfl\n"
    "  · unfold problem_spec_keyLookupPath implementation_keyLookupPath\n"
    "    rfl\n"
    "  · unfold implementation_keyLookupPath\n"
    "    simp only [Id.run, pure, List.dropLast, pathOfKeys, List.map_nil, String.join,\n"
    "               List.foldl_nil, List.getLastD_cons, List.getLastD_nil, hn,\n"
    "               String.empty_append]\n"
    "  · unfold implementation_keyLookupPath\n"
    "    simp only [Id.run, pure, List.dropLast, pathOfKeys, List.map_nil, String.join,\n"
    "               List.foldl_nil, List.getLastD_cons, List.getLastD_nil, hp,\n"
    "               String.empty_append]",
)


# ===========================================================================
# UNIQUENESS RIVALS — must be REJECTED (else SPEC-TOO-WEAK). Each shares the frozen
# spec exactly and edits only the impl region; the frozen proof body is left in place
# (it will not close for the reshaped impl, but the gate reads the witness — checked in
# a file with the obligation removed — not the rival's own build).
# ===========================================================================

# R-prepatch-array-index: the EXACT pre-patch behaviour — address EVERY step
# (including the final one) by what its text denotes, so a digit-run final key becomes
# the bracketed positional step even when the enquiry asked for a member of that name.
# This is the modeled bug; it attacks clause (F) and is correct on the whole
# `byName = false` half, which is precisely why it is the strongest near-miss.
_RIV_PREPATCH = _swap(
    _BASE,
    _IMPL,
    _SIG +
    "  let rhsJsonPath := pathOfKeys keys\n"
    "  return lhsJsonPath ++ rhsJsonPath",
)

# R-hardwire-named-final: the MIRROR near-miss, and the one a spec pinning only the
# named form would admit. It gets clause (F) exactly right — the final step is always
# addressed as a named member, so every enquiry about a member of a given name is
# assembled correctly — but it INLINES that decision at the assembly site and so
# never delivers the denoted-location form at all. Attacks clause (M).
_RIV_HARDNAME = _swap(
    _BASE,
    _IMPL,
    _SIG +
    "  let intermediate := keys.dropLast\n"
    "  let finalKey := keys.getLastD \"\"\n"
    "  let mut rhsJsonPath := pathOfKeys intermediate\n"
    "  rhsJsonPath := rhsJsonPath ++ (\".\" ++ encodeKey finalKey)\n"
    "  return lhsJsonPath ++ rhsJsonPath",
)

# R-swap-final-forms: the dispatch EXISTS but is wired backwards — the enquiry's
# selection is honoured inverted, so each of the two addressing forms is delivered on
# exactly the wrong half of the domain. Attacks clause (M) on the DIRECTION of the
# dispatch rather than on its presence: a spec that only required the assembly to
# depend on the selector somehow (rather than to deliver the named form for a
# name enquiry and the denoted form otherwise) would accept this.
_RIV_SWAPMODE = _swap(
    _BASE,
    _IMPL,
    _SIG +
    "  let intermediate := keys.dropLast\n"
    "  let finalKey := keys.getLastD \"\"\n"
    "  let mut rhsJsonPath := pathOfKeys intermediate\n"
    "  rhsJsonPath := rhsJsonPath ++ finalSegment (!byName) finalKey\n"
    "  return lhsJsonPath ++ rhsJsonPath",
)

# R-named-final-only-when-flat: the PARTIAL-DOMAIN attack on clause (M). The dispatch
# is honoured whenever the step list descends at all, and short-circuited to the
# named-member form on the single-step list — the commonest shape, and the one the
# F2P query has. Correct on every multi-step input, wrong on exactly the singleton
# denoted-location enquiry, so a spec checked only on nested lookups would admit it.
_RIV_FLATNAME = _swap(
    _BASE,
    _IMPL,
    _SIG +
    "  let intermediate := keys.dropLast\n"
    "  let finalKey := keys.getLastD \"\"\n"
    "  let mut rhsJsonPath := pathOfKeys intermediate\n"
    "  rhsJsonPath := rhsJsonPath ++\n"
    "    (if keys.length ≤ 1 then memberSegment finalKey else finalSegment byName finalKey)\n"
    "  return lhsJsonPath ++ rhsJsonPath",
)

# R-drop-lhs-prefix: renders both portions correctly but DROPS the path prefix, emitting
# only the RHS. Attacks clause (P) — the `lhsJsonPath` binder.
_RIV_NOPREFIX = _swap(
    _BASE,
    _IMPL,
    _SIG +
    "  let intermediate := keys.dropLast\n"
    "  let finalKey := keys.getLastD \"\"\n"
    "  let mut rhsJsonPath := pathOfKeys intermediate\n"
    "  rhsJsonPath := rhsJsonPath ++ finalSegment byName finalKey\n"
    "  return rhsJsonPath",
)

# R-drop-intermediate: renders the prefix and the final key correctly but OMITS the
# intermediate steps entirely (as if the list were always a singleton). Attacks clause
# (I) — the intermediate-steps portion over a multi-key list.
_RIV_NOMID = _swap(
    _BASE,
    _IMPL,
    _SIG +
    "  let finalKey := keys.getLastD \"\"\n"
    "  return lhsJsonPath ++ finalSegment byName finalKey",
)


# R-reverse-intermediate: renders every piece with the CORRECT renderer, keeps the
# prefix, keeps the final key and honours the selector — but emits the intermediate
# steps in REVERSE order. Attacks clause (I) on the ORDER of the descent rather than
# on its presence, which R-drop-intermediate (which omits the portion wholesale)
# cannot distinguish: a spec pinning only the SET of steps would accept this rival.
# Observable only at three or more keys — with a single intermediate step `reverse` is
# the identity — so this is the only case that varies `keys` to LENGTH 3.
_RIV_REVMID = _swap(
    _BASE,
    _IMPL,
    _SIG +
    "  let intermediate := keys.dropLast.reverse\n"
    "  let finalKey := keys.getLastD \"\"\n"
    "  let mut rhsJsonPath := pathOfKeys intermediate\n"
    "  rhsJsonPath := rhsJsonPath ++ finalSegment byName finalKey\n"
    "  return lhsJsonPath ++ rhsJsonPath",
)

# R-truncate-final-key: the port of nagini `drop-last-char`. The final key is
# TRUNCATED (its last character dropped) before being handed to the addressing form,
# so the path addresses a DIFFERENT member than the one requested. The dispatch itself
# is used correctly — the off-by-one is on the key TEXT, which is transparent `String`
# data, so no property of the opaque serializer is needed.
_RIV_TRUNC = _swap(
    _BASE,
    _IMPL,
    _SIG +
    "  let intermediate := keys.dropLast\n"
    "  let finalKey := keys.getLastD \"\"\n"
    "  let mut rhsJsonPath := pathOfKeys intermediate\n"
    "  rhsJsonPath := rhsJsonPath ++ finalSegment byName (String.mk finalKey.toList.dropLast)\n"
    "  return lhsJsonPath ++ rhsJsonPath",
)

# R-skip-first-char: the port of nagini `skip-first-char`, the symmetric off-by-one
# — the FIRST character of the final key is dropped instead of the last.
_RIV_SKIP = _swap(
    _BASE,
    _IMPL,
    _SIG +
    "  let intermediate := keys.dropLast\n"
    "  let finalKey := keys.getLastD \"\"\n"
    "  let mut rhsJsonPath := pathOfKeys intermediate\n"
    "  rhsJsonPath := rhsJsonPath ++ finalSegment byName (String.mk finalKey.toList.tail)\n"
    "  return lhsJsonPath ++ rhsJsonPath",
)

# R-hand-quoted-final-key: the port of nagini `wrong-quote`. Rather than peer inside
# the opaque serializer, the rival BYPASSES it — hand-rolling the quoted token with
# the wrong quote glyph. The spec pins the named-member token to `encodeKey k`
# exactly, so any hand-rolled substitute is refutable under the hypothesis that the
# real serializer does not coincide with it.
_RIV_QUOTE = _swap(
    _BASE,
    _IMPL,
    _SIG +
    "  let intermediate := keys.dropLast\n"
    "  let finalKey := keys.getLastD \"\"\n"
    "  let mut rhsJsonPath := pathOfKeys intermediate\n"
    "  rhsJsonPath := rhsJsonPath ++ (\".\" ++ (\"'\" ++ finalKey ++ \"'\"))\n"
    "  return lhsJsonPath ++ rhsJsonPath",
)


# --- witnesses ---------------------------------------------------------------------
# Each witness states `¬ problem_spec … (implementation …)` at ONE concrete literal
# (byName, lhsJsonPath, keys). It reduces the impl to a closed form with `simp only`
# over the transparent list/string machinery (`decide` only on a fully-concrete
# positional rendering), then refutes the string equality by `congrArg String.data` and
# `String.data_append`: the two sides differ in their leading glyph (`.` vs `[`, or a
# present-vs-absent prefix), which holds WITHOUT any property of the opaque `encodeKey`.
# The witness head binds NOTHING (literal inputs) except in the three key-TEXT cases,
# so there is no consistency obligation elsewhere.
# Each was built against the rival (elaborates) and against the frozen solution (FAILS)
# — SEEN to discriminate both ways.

_WIT_PREPATCH = (
    'example : ¬ problem_spec_keyLookupPath true "" ["1"]\n'
    '    (implementation_keyLookupPath true "" ["1"]) := by\n'
    '  have himpl : implementation_keyLookupPath true "" ["1"] = "[1]" := by\n'
    "    unfold implementation_keyLookupPath\n"
    "    simp only [Id.run, pure, pathOfKeys, List.map_cons, List.map_nil,\n"
    "               String.join, List.foldl_cons, List.foldl_nil, String.empty_append]\n"
    "    decide\n"
    '  have hfin : finalSegment true "1" = "." ++ encodeKey "1" := rfl\n'
    "  unfold problem_spec_keyLookupPath\n"
    "  rw [himpl]\n"
    "  simp only [List.dropLast, pathOfKeys, List.map_nil, String.join, List.foldl_nil,\n"
    "             List.getLastD_cons, List.getLastD_nil, hfin, String.empty_append]\n"
    "  intro h\n"
    "  have hd := congrArg String.data h\n"
    "  simp [String.data_append] at hd"
)

# The clause-(M) witnesses live on `byName = false` with a final key whose text reads
# as an integer — the only region where the two addressing forms differ, so the only
# region where a hardwired form is observable at all. Each of the three uses a
# DIFFERENT point of that region (a bare digit, a signed magnitude, a distinct digit
# run) so the three cases are not three spellings of one input.

_WIT_HARDNAME = (
    'example : ¬ problem_spec_keyLookupPath false "" ["1"]\n'
    '    (implementation_keyLookupPath false "" ["1"]) := by\n'
    '  have himpl : implementation_keyLookupPath false "" ["1"]\n'
    '      = "." ++ encodeKey "1" := by\n'
    "    unfold implementation_keyLookupPath\n"
    "    simp only [Id.run, pure, List.dropLast, pathOfKeys, List.map_nil, String.join,\n"
    "               List.foldl_nil, List.getLastD_cons, List.getLastD_nil,\n"
    "               String.empty_append]\n"
    '  have hfin : finalSegment false "1" = "[1]" := by decide\n'
    "  unfold problem_spec_keyLookupPath\n"
    "  rw [himpl]\n"
    "  simp only [List.dropLast, pathOfKeys, List.map_nil, String.join, List.foldl_nil,\n"
    "             List.getLastD_cons, List.getLastD_nil, hfin, String.empty_append]\n"
    "  intro h\n"
    "  have hd := congrArg String.data h\n"
    "  simp [String.data_append] at hd"
)

_WIT_SWAPMODE = (
    'example : ¬ problem_spec_keyLookupPath false "" ["+3"]\n'
    '    (implementation_keyLookupPath false "" ["+3"]) := by\n'
    '  have himpl : implementation_keyLookupPath false "" ["+3"]\n'
    '      = "." ++ encodeKey "+3" := by\n'
    "    unfold implementation_keyLookupPath\n"
    "    simp only [Id.run, pure, List.dropLast, pathOfKeys, List.map_nil, String.join,\n"
    "               List.foldl_nil, List.getLastD_cons, List.getLastD_nil,\n"
    "               String.empty_append]\n"
    "    rfl\n"
    '  have hfin : finalSegment false "+3" = "[3]" := by decide\n'
    "  unfold problem_spec_keyLookupPath\n"
    "  rw [himpl]\n"
    "  simp only [List.dropLast, pathOfKeys, List.map_nil, String.join, List.foldl_nil,\n"
    "             List.getLastD_cons, List.getLastD_nil, hfin, String.empty_append]\n"
    "  intro h\n"
    "  have hd := congrArg String.data h\n"
    "  simp [String.data_append] at hd"
)

_WIT_FLATNAME = (
    'example : ¬ problem_spec_keyLookupPath false "$" ["70"]\n'
    '    (implementation_keyLookupPath false "$" ["70"]) := by\n'
    '  have himpl : implementation_keyLookupPath false "$" ["70"]\n'
    '      = "$" ++ ("." ++ encodeKey "70") := by\n'
    "    unfold implementation_keyLookupPath\n"
    "    simp only [Id.run, pure, List.dropLast, pathOfKeys, List.map_nil, String.join,\n"
    "               List.foldl_nil, List.getLastD_cons, List.getLastD_nil, memberSegment,\n"
    "               String.empty_append]\n"
    "    rfl\n"
    '  have hfin : finalSegment false "70" = "[70]" := by decide\n'
    "  unfold problem_spec_keyLookupPath\n"
    "  rw [himpl]\n"
    "  simp only [List.dropLast, pathOfKeys, List.map_nil, String.join, List.foldl_nil,\n"
    "             List.getLastD_cons, List.getLastD_nil, hfin, String.empty_append]\n"
    "  intro h\n"
    "  have hd := congrArg String.data h\n"
    "  simp [String.data_append] at hd"
)

_WIT_NOPREFIX = (
    'example : ¬ problem_spec_keyLookupPath true "$" ["a"]\n'
    '    (implementation_keyLookupPath true "$" ["a"]) := by\n'
    '  have hfin : finalSegment true "a" = "." ++ encodeKey "a" := rfl\n'
    '  have himpl : implementation_keyLookupPath true "$" ["a"] = "." ++ encodeKey "a" := by\n'
    "    unfold implementation_keyLookupPath\n"
    "    simp only [Id.run, pure, List.dropLast, pathOfKeys, List.map_nil, String.join,\n"
    "               List.foldl_nil, List.getLastD_cons, List.getLastD_nil, hfin,\n"
    "               String.empty_append]\n"
    "  unfold problem_spec_keyLookupPath\n"
    "  rw [himpl]\n"
    "  simp only [List.dropLast, pathOfKeys, List.map_nil, String.join, List.foldl_nil,\n"
    "             List.getLastD_cons, List.getLastD_nil, hfin,\n"
    "             String.empty_append]\n"
    "  intro h\n"
    "  have hd := congrArg String.data h\n"
    "  simp [String.data_append] at hd"
)

_WIT_NOMID = (
    'example : ¬ problem_spec_keyLookupPath true "" ["0", "a"]\n'
    '    (implementation_keyLookupPath true "" ["0", "a"]) := by\n'
    '  have hfin : finalSegment true "a" = "." ++ encodeKey "a" := rfl\n'
    '  have himpl : implementation_keyLookupPath true "" ["0", "a"]\n'
    '      = "." ++ encodeKey "a" := by\n'
    "    unfold implementation_keyLookupPath\n"
    "    simp only [Id.run, pure, List.getLastD_cons, List.getLastD_nil, hfin,\n"
    "               String.empty_append]\n"
    "  unfold problem_spec_keyLookupPath\n"
    "  rw [himpl]\n"
    '  have hr : renderSegment "0" = "[0]" := by decide\n'
    "  simp only [List.dropLast, pathOfKeys, List.map_cons, List.map_nil, String.join,\n"
    "             List.foldl_cons, List.foldl_nil, List.getLastD_cons, List.getLastD_nil,\n"
    "             hfin, hr, String.empty_append]\n"
    "  intro h\n"
    "  have hd := congrArg String.data h\n"
    "  simp [String.data_append] at hd"
)


# _WIT_REVMID deliberately carries NO `have himpl` step. The first attempt did, and
# it was a NON-DISCRIMINATOR that the two-build check alone would have passed: gold
# failed with `rewrite failed: did not find an occurrence of the pattern
# pathOfKeys ["1", "0"]`, i.e. a SYNTACTIC miss inside the `have`, and the
# claim-flipped forgery failed with the byte-identical error — so gold's exit code
# carried nothing about the claim. Restated below by unfolding BOTH sides and
# pinning the two positional renderings as `decide` facts about literal lists
# (valid in either file), so the refutation is the last step. Measured: on gold
# `simp` closes the equation and the final step reports `h has type True`, while the
# flipped claim gets a DIFFERENT error (`No goals to be solved`) — the error tracks
# the claim, which is what makes it evidence.
_WIT_REVMID = (
    'example : ¬ problem_spec_keyLookupPath true "" ["0", "1", "a"]\n'
    '    (implementation_keyLookupPath true "" ["0", "1", "a"]) := by\n'
    "  unfold problem_spec_keyLookupPath implementation_keyLookupPath\n"
    '  have hfwd : pathOfKeys ["0", "1", "a"].dropLast = "[0][1]" := by decide\n'
    '  have hrev : pathOfKeys ["0", "1", "a"].dropLast.reverse = "[1][0]" := by decide\n'
    "  simp only [Id.run, pure, hfwd, hrev, List.getLastD_cons, List.getLastD_nil,\n"
    "             finalSegment, memberSegment, String.empty_append]\n"
    "  intro h\n"
    "  have hd := congrArg String.data h\n"
    "  simp [String.data_append] at hd"
)


# The three key-TEXT witnesses below CONDITION on the carrier instead of computing
# it, which is the technique an opaque callee admits (and the only one it admits):
# each states its refutation at a point described by a HYPOTHESIS saying the
# serializer does not identify the two distinct texts at issue. That is sound
# because the hypothesis is satisfiable — no tactic can derive `False` from
# `encodeKey a ≠ encodeKey b` for an opaque `encodeKey` — and the gate's consistency
# probe is run against each of them to confirm exactly that (probe must NOT close).
# Each was also built against the frozen solution and SEEN to fail by a semantic
# refutation of the concrete claim (the residual disequality was separately proven
# FALSE-under-hypothesis), not by an unknown identifier, type error or timeout.

_WIT_TRUNC = (
    'example (hk : encodeKey "1" ≠ encodeKey "12") :\n'
    '    ¬ problem_spec_keyLookupPath true "" ["12"]\n'
    '      (implementation_keyLookupPath true "" ["12"]) := by\n'
    '  have himpl : implementation_keyLookupPath true "" ["12"]\n'
    '      = "." ++ encodeKey "1" := by\n'
    "    unfold implementation_keyLookupPath\n"
    "    simp only [Id.run, pure, List.dropLast, pathOfKeys, List.map_nil, String.join,\n"
    "               List.foldl_nil, List.getLastD_cons, List.getLastD_nil, finalSegment,\n"
    "               memberSegment, String.empty_append]\n"
    "    rfl\n"
    "  unfold problem_spec_keyLookupPath\n"
    "  rw [himpl]\n"
    "  simp only [List.dropLast, pathOfKeys, List.map_nil, String.join, List.foldl_nil,\n"
    "             List.getLastD_cons, List.getLastD_nil, finalSegment, memberSegment,\n"
    "             String.empty_append]\n"
    "  intro h\n"
    "  have hd := congrArg String.data h\n"
    "  simp [String.data_append] at hd\n"
    "  exact hk (String.ext hd)"
)

_WIT_SKIP = (
    'example (hk : encodeKey "2" ≠ encodeKey "12") :\n'
    '    ¬ problem_spec_keyLookupPath true "" ["12"]\n'
    '      (implementation_keyLookupPath true "" ["12"]) := by\n'
    '  have himpl : implementation_keyLookupPath true "" ["12"]\n'
    '      = "." ++ encodeKey "2" := by\n'
    "    unfold implementation_keyLookupPath\n"
    "    simp only [Id.run, pure, List.dropLast, pathOfKeys, List.map_nil, String.join,\n"
    "               List.foldl_nil, List.getLastD_cons, List.getLastD_nil, finalSegment,\n"
    "               memberSegment, String.empty_append]\n"
    "    rfl\n"
    "  unfold problem_spec_keyLookupPath\n"
    "  rw [himpl]\n"
    "  simp only [List.dropLast, pathOfKeys, List.map_nil, String.join, List.foldl_nil,\n"
    "             List.getLastD_cons, List.getLastD_nil, finalSegment, memberSegment,\n"
    "             String.empty_append]\n"
    "  intro h\n"
    "  have hd := congrArg String.data h\n"
    "  simp [String.data_append] at hd\n"
    "  exact hk (String.ext hd)"
)

_WIT_QUOTE = (
    'example (hk : encodeKey "a" ≠ "\'a\'") :\n'
    '    ¬ problem_spec_keyLookupPath true "" ["a"]\n'
    '      (implementation_keyLookupPath true "" ["a"]) := by\n'
    '  have himpl : implementation_keyLookupPath true "" ["a"] = "." ++ "\'a\'" := by\n'
    "    unfold implementation_keyLookupPath\n"
    "    simp only [Id.run, pure, List.dropLast, pathOfKeys, List.map_nil, String.join,\n"
    "               List.foldl_nil, List.getLastD_cons, List.getLastD_nil,\n"
    "               String.empty_append]\n"
    "    rfl\n"
    "  unfold problem_spec_keyLookupPath\n"
    "  rw [himpl]\n"
    "  simp only [List.dropLast, pathOfKeys, List.map_nil, String.join, List.foldl_nil,\n"
    "             List.getLastD_cons, List.getLastD_nil, finalSegment, memberSegment,\n"
    "             String.empty_append]\n"
    "  intro h\n"
    "  have hd := congrArg String.data h\n"
    "  simp [String.data_append] at hd\n"
    "  exact hk (String.ext hd.symm)"
)


SPEC_TESTS = [
    # ---- positive controls (must VERIFY) ----
    {
        "id": "pos-gold",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_GOLD,
        "rationale": (
            "honest cheapest positive control: the faithful per-step assembly — "
            "intermediate keys addressed by what their text denotes, the final key "
            "addressed in the form the enquiry selects, prefixed by lhsJsonPath — "
            "satisfies the postcondition by the frozen proof. There is no answer-key to "
            "echo (the spec is grounded in `pathOfKeys`/`finalSegment` of the actual "
            "inputs). Must verify; if it FAILS => SPEC-TOO-STRONG (unsatisfiable by the "
            "computation it describes)."
        ),
    },
    {
        "id": "pos-pure-reshape",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_PURE,
        "rationale": (
            "structurally different but CORRECT impl written as a pure `let`-expression "
            "(no `Id.run do`, no `mut`, no early return), building the RHS in one binding "
            "and concatenating. Output equals the frozen impl's on every input, both "
            "addressing forms included. The theorem STATEMENT is byte-identical and the "
            "FROZEN proof body still closes (the reshape is definitionally equal, so "
            "`rfl` discharges it) — no reproof, no new axiom/lemma/sorry. If it FAILS => "
            "SPEC-TOO-STRONG (postcondition bound to the monadic impl shape rather than "
            "the behaviour)."
        ),
    },

    # ---- uniqueness rivals (must be REJECTED) ----
    {
        "id": "R-prepatch-array-index",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_PREPATCH,
        "refinement": (
            "this IS the pre-patch behaviour: address EVERY step (including the final "
            "one) by what its text denotes, so a digit-run final key is emitted as a "
            "bracketed positional step even for an enquiry about a member of that name. "
            "Its faithful real patch is the UNCHANGED repo, which routes a numeric final "
            "key to the array-index form (and even drops leading zeros). It is the exact "
            "F2P discriminator: the FAIL_TO_PASS tests assert a numeric object key "
            '("123"/"000"/"456"/…) is found as a NAMED member, not an array index. A patch '
            "keeping the pre-patch rendering does NOT resolve — a verifying rival would be "
            "a true verify-does-not-imply-resolve break."
        ),
        "rationale": (
            "REJECTED by clause (F): for a digit-run final key under a by-name enquiry the "
            "spec demands the named-member form (leading `.`) but the rival emits the "
            "positional step (leading `[`). Witness probes byName=true at a SINGLETON list "
            "whose sole (= final) key is the digit \"1\", the minimal point where the two "
            "forms diverge; the leading-glyph clash refutes the equality with no property "
            "of the opaque serializer. If it VERIFIES => SPEC-TOO-WEAK (the named-member "
            "obligation is unpinned)."
        ),
        # byName=true, keys=["1"]: gold ".<enc 1>" (leading '.'), rival "[1]" (leading '[').
        "witness": _WIT_PREPATCH,
    },
    {
        "id": "R-hardwire-named-final",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_HARDNAME,
        "refinement": (
            "the MIRROR of the pre-patch rival, and the harder one. It satisfies the "
            "named-member obligation on the nose — the final step is ALWAYS addressed by "
            "member name — so both FAIL_TO_PASS assertions about a numeric object key "
            "pass. But it reaches that by inlining the named-member token at the assembly "
            "site, so the assembly can no longer produce the denoted-location form at "
            "all. Its faithful real patch therefore breaks every enquiry that asks about "
            "whatever the final step's text denotes rather than about a member of that "
            "name: a query on an array element addressed by a numeric last step is "
            "assembled as an object-member reference and matches nothing. Measured "
            "against the instance's own suite, that patch keeps FAIL_TO_PASS green and "
            "REGRESSES six PASS_TO_PASS tests, so it does NOT resolve."
        ),
        "rationale": (
            "REJECTED by clause (M): the postcondition demands the assembled path deliver "
            "`finalSegment byName k`, which on byName=false is the denoted-location form, "
            "so an assembly that emits the named-member token unconditionally violates it "
            "on the whole byName=false, integer-reading-final-key sub-domain. This is the "
            "case that distinguishes a spec pinning only the named form (which admits the "
            "rival) from one pinning the DISPATCH. Witness probes byName=false at the "
            "singleton digit \"1\": the spec's positional \"[1]\" against the rival's "
            "leading `.`. If it VERIFIES => SPEC-TOO-WEAK (the final step's addressing "
            "form is a constant, not a caller-selected choice)."
        ),
        # byName=false, keys=["1"]: gold "[1]", rival ".<enc 1>".
        "witness": _WIT_HARDNAME,
    },
    {
        "id": "R-swap-final-forms",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_SWAPMODE,
        "refinement": (
            "the dispatch is present and the assembly genuinely depends on the enquiry's "
            "selection — but inverted, so each addressing form is delivered on exactly the "
            "wrong half of the domain. Its faithful real patch swaps the two families of "
            "query: a by-name enquiry on a numeric key is assembled positionally (the "
            "pre-patch failure, so FAIL_TO_PASS does not go green) and a denoted-location "
            "enquiry is assembled as an object member (the six-test regression). It "
            "resolves nothing and breaks more than the pre-patch code did."
        ),
        "rationale": (
            "REJECTED by clause (M) on the DIRECTION of the dispatch rather than on its "
            "presence: a spec that merely required the result to DEPEND on the selector "
            "would accept this, so the case pins that the named-member form is what a "
            "by-name enquiry gets and the denoted-location form is what the other gets. "
            "Witness probes byName=false at a SIGNED magnitude \"-3\" — a different point "
            "of the observable region than the other two dispatch rivals, and one that "
            "additionally exercises the sign in the integer reading. If it VERIFIES => "
            "SPEC-TOO-WEAK."
        ),
        # byName=false, keys=["-3"]: gold "[-3]", rival ".<enc -3>".
        "witness": _WIT_SWAPMODE,
    },
    {
        "id": "R-named-final-only-when-flat",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_FLATNAME,
        "refinement": (
            "the PARTIAL-DOMAIN attack on the dispatch: the enquiry's selection is "
            "honoured whenever the step list actually descends, and short-circuited to the "
            "named-member form on the single-step list. Its faithful real patch is correct "
            "for every nested lookup and wrong for the commonest shape there is — a "
            "top-level key — so a denoted-location enquiry with one numeric step is "
            "assembled as an object member and matches nothing. Does NOT resolve: it keeps "
            "the FAIL_TO_PASS assertions (whose enquiries are by-name) green while "
            "breaking the single-step denoted-location queries."
        ),
        "rationale": (
            "REJECTED by clause (M) on the sub-domain a battery checked only on nested "
            "lookups would miss: the postcondition is quantified over ALL non-empty step "
            "lists, singletons included, so the dispatch may not be short-circuited by the "
            "list's length. Witness probes byName=false at the singleton \"70\" with a "
            "non-empty prefix \"$\" — a third, distinct point of the observable region, and "
            "the only dispatch witness that also varies the prefix binder. If it VERIFIES "
            "=> SPEC-TOO-WEAK (the dispatch would be pinned only on nested inputs)."
        ),
        # byName=false, keys=["70"], prefix "$": gold "$[70]", rival "$.<enc 70>".
        "witness": _WIT_FLATNAME,
    },
    {
        "id": "R-drop-lhs-prefix",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_NOPREFIX,
        "refinement": (
            "renders both the intermediate and final portions correctly, dispatch "
            "included, but DROPS the path prefix, returning only the RHS. Its faithful "
            "real patch would emit a path missing its left-hand root/prefix, so the "
            "assembled membership expression addresses the wrong location and the F2P "
            "query does not match. Does NOT resolve — a rendering-correct impl that still "
            "breaks the prefix."
        ),
        "rationale": (
            "REJECTED by clause (P): the spec pins `result` to begin with `lhsJsonPath` "
            "verbatim, but the rival omits it. Witness VARIES the prefix binder to a "
            "non-empty \"$\" (with a named single key \"a\" and byName=true, so clauses "
            "(I)/(F)/(M) all hold) so the two results differ exactly by the dropped "
            "prefix. This binder had no counterpart in the nagini single-key carrier. If "
            "it VERIFIES => SPEC-TOO-WEAK (the prefix is unpinned)."
        ),
        # lhsJsonPath="$", keys=["a"]: gold "$.<enc a>", rival ".<enc a>" — differ by "$".
        "witness": _WIT_NOPREFIX,
    },
    {
        "id": "R-drop-intermediate",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_NOMID,
        "refinement": (
            "renders the prefix and the final key correctly, dispatch included, but OMITS "
            "the intermediate steps, as if the key list were always a singleton. Its "
            "faithful real patch would emit a path that skips the nesting steps of a "
            "nested key lookup (`value__nested__has_key`, `value__array__0__has_key`), so "
            "the membership query descends to the wrong node. Does NOT resolve — a rival "
            "correct only on the single-key sub-domain."
        ),
        "rationale": (
            "REJECTED by clause (I): the spec renders `keys.dropLast` via `pathOfKeys` "
            "before the final segment, but the rival drops that portion. Witness VARIES "
            "the list to LENGTH 2 (`[\"0\", \"a\"]`) — a shape the nagini single-key "
            "carrier could not express — where the intermediate step \"0\" renders to the "
            "positional \"[0]\" the rival omits, so the results differ at the front of the "
            "RHS. If it VERIFIES => SPEC-TOO-WEAK (the intermediate steps are unpinned)."
        ),
        # keys=["0","a"]: gold "[0].<enc a>", rival ".<enc a>" — differ by dropped "[0]".
        "witness": _WIT_NOMID,
    },
    {
        "id": "R-reverse-intermediate",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_REVMID,
        "refinement": (
            "every piece is rendered by the correct addressing form and none is dropped — "
            "the intermediate steps are simply emitted in REVERSE order. Its faithful real "
            "patch would descend a nested lookup through the right steps in the wrong "
            "sequence, so the path addresses a node that is generally absent (and, where "
            "the document happens to nest symmetrically, the WRONG one). Does NOT "
            "resolve: a nested key query would locate nothing. Correct only where at "
            "most one intermediate step exists, i.e. on lists of length ≤ 2."
        ),
        "rationale": (
            "REJECTED by clause (I) on ORDER rather than on presence: the spec renders "
            "`keys.dropLast` in list order via `pathOfKeys`, and a spec pinning only "
            "WHICH steps appear would accept this rival. R-drop-intermediate cannot "
            "distinguish it — that rival omits the portion wholesale — so this is the "
            "case that pins the sequence. Witness VARIES `keys` to LENGTH 3 "
            "(`[\"0\", \"1\", \"a\"]`), the shortest list where `reverse` is observable at "
            "all, and the two renderings differ as \"[0][1]\" vs \"[1][0]\" before the "
            "shared final member. If it VERIFIES => SPEC-TOO-WEAK (the descent order is "
            "unpinned)."
        ),
        # keys=["0","1","a"]: gold "[0][1].<enc a>", rival "[1][0].<enc a>".
        "witness": _WIT_REVMID,
    },
    {
        "id": "R-truncate-final-key",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_TRUNC,
        "refinement": (
            "the final step is rendered by the correct addressing form, but from a "
            "TRUNCATED copy of the key text — its last character is dropped. Its "
            "faithful real patch would emit a membership expression addressing a "
            "different, shorter member name than the one queried, so a lookup for a key "
            "would silently test a prefix of it. Does NOT resolve: the F2P asserts the "
            "queried key itself is found, and a truncated key matches a different member "
            "(or none). Correct only on the empty-key sub-domain."
        ),
        "rationale": (
            "REJECTED by clause (F): the spec pins the named-member token to `encodeKey k` "
            "for the ACTUAL final key `k`, but the rival passes a different text. Witness "
            "VARIES the final key to the two-character digit run \"12\" (so truncation is "
            "observable at all) and refutes at that point under the hypothesis that the "
            "serializer does not identify \"1\" with \"12\" — the conditioning technique an "
            "opaque callee admits, whose satisfiability the gate's consistency probe "
            "confirms. If it VERIFIES => SPEC-TOO-WEAK (the final token is pinned only up "
            "to the key's prefix)."
        ),
        "witness": _WIT_TRUNC,
    },
    {
        "id": "R-skip-first-char",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_SKIP,
        "refinement": (
            "the symmetric off-by-one: the FIRST character of the final key is dropped "
            "before it is rendered. Its faithful real patch addresses a member named by "
            "the key's tail, so the same F2P assertion fails for the same reason as the "
            "truncating variant, on a disjoint set of inputs (a leading-digit key such as "
            "\"000\" would be looked up as \"00\")."
        ),
        "rationale": (
            "REJECTED by clause (F), from the other end of the key: the rival hands the "
            "addressing form the key's TAIL. Witness refutes at final key \"12\" under the "
            "hypothesis that the serializer does not identify \"2\" with \"12\", a "
            "DIFFERENT discriminating pair than the truncating rival's, so the two cases "
            "are not two spellings of one point. If it VERIFIES => SPEC-TOO-WEAK."
        ),
        "witness": _WIT_SKIP,
    },
    {
        "id": "R-hand-quoted-final-key",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_QUOTE,
        "refinement": (
            "renders the final step by HAND-ROLLING the quoted token with the wrong quote "
            "glyph instead of calling the standard serializer. Its faithful real patch "
            "would emit a path token that is not the serializer's output — wrong quoting, "
            "and no escaping of characters that need it — so the assembled expression is "
            "not the well-formed path the database matches against, and the F2P key is not "
            "found. Does NOT resolve."
        ),
        "rationale": (
            "REJECTED by clause (F): the spec pins the named-member token to the "
            "SERIALIZER's output `encodeKey k`, not to any string that merely looks "
            "quoted; this is what stops an impl from open-coding the token. Witness "
            "refutes at a NAMED (non-digit) key \"a\" — the sub-domain the other rivals do "
            "not discriminate on — under the hypothesis that the serializer's output is "
            "not the hand-rolled single-quoted text. Note this attacks the spec from "
            "OUTSIDE the opaque callee (bypassing it), so no property of it is assumed. If "
            "it VERIFIES => SPEC-TOO-WEAK (the token would be pinned only in shape)."
        ),
        "witness": _WIT_QUOTE,
    },

    # ---- extra soundness positive (must VERIFY) ----
    {
        "id": "pos-foldl-reshape",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_FOLDL,
        "rationale": (
            "the strongest soundness control here: a CORRECT impl whose shape is far "
            "enough from the frozen one that the frozen `rfl` does NOT close it — the "
            "intermediate steps are folded directly onto the prefix as an accumulator, so "
            "the intermediate-path helper never appears in the impl. The proof is "
            "therefore genuinely RE-DERIVED (an induction showing the accumulating fold "
            "equals prefix ++ join), not discharged by definitional equality, which is "
            "what makes this positive test the postcondition against BEHAVIOUR rather than "
            "against a shape. It also confirms the dispatch clause is not over-fit: this "
            "impl threads the addressing-form selector through a completely different "
            "assembly and is still accepted. Theorem STATEMENT byte-identical; only the "
            "tactic body differs; no new axiom/lemma/sorry. If it FAILS => "
            "SPEC-TOO-STRONG (the postcondition is over-fit to the frozen assembly order)."
        ),
    },

    # ---- admissibility (must VERIFY) ----
    {
        "id": "admiss-numeric-final-key",
        "kind": "admissibility",
        "expect": "verify",
        "module": _ADMISS,
        "rationale": (
            "ADMISSIBILITY on the sub-domain the issue is actually about. The only "
            "precondition is that the step list is non-empty, so a digit-run FINAL key is "
            "admitted with NO extra hypothesis; the case pins that, and additionally that "
            "the SAME assembly routes that numeric key to the NAMED-member form when the "
            "enquiry asks about a member of that name and to the POSITIONAL form when it "
            "asks about the denoted location. Pinning both halves at one input is what "
            "shows the two obligations are jointly satisfiable — i.e. that the dispatch "
            "clause is not a hidden contradiction. Stated as an anonymous `example` in the "
            "impl region, so it adds no name and leaves the frozen obligation and proof "
            "untouched. If it FAILS, the spec excludes the very inputs the F2P exercises "
            "=> PRECOND-TOO-STRONG."
        ),
    },
]


# ===========================================================================
# AXIOM CASES — none.
# ===========================================================================
# `encodeKey` is declared `opaque` (signature only) with NO consumed `_prop` axiom: the
# proof needs no property of the key serializer, only WHICH addressing form (positional
# vs named) the final step gets. There are no @ContractOnly axioms and no deep-model
# reference the PBT lane must additionally discharge; G-AX owns the axiom lane
# regardless. So this list is empty.
AXIOM_TESTS = []
