"""properties.py — G-PBT falsification battery for psf__requests-6028 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed
— both of which the consumer spec view elides, so ``markers.same_spec`` holds
and the ``prove_correct buildAuthority`` obligation survives with a
byte-identical statement) and swaps in a candidate implementation; it is checked
by the real verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness must ELABORATE against the rival and FAIL
against the frozen solution).

DEFENDED SURFACE (one contracted method):

  buildAuthority (userinfo : List Char) (authoritySlot : List Char)
      (fallbackSlot : List Char) return (out : List Char)
    ensures out = assembleAuthority userinfo
                    (authorityBase authoritySlot fallbackSlot)

The method reconstructs the authority section of a URL from the pieces a
splitter hands back. There is NO ``require`` clause (the operation is total on
its carrier) and NO permission surface. The single load-bearing ``ensures``
pins ``out`` to two fully-unfolded pure helpers (the ``axioms`` region is empty
— there is no opaque answer key to echo):

  * ``authorityBase authoritySlot fallbackSlot`` — resolves WHICH slot holds the
    host portion: the authority slot normally, but the fallback slot when the
    authority slot is empty (a parser-quirk resolution). ONE independent branch.
  * ``assembleAuthority userinfo base`` — folds the optional credentials back
    into that host portion: when credentials are present they precede the host
    portion joined by a single ``@``; when absent the host portion stands alone.
    TWO independent facets — which branch fires (credentials present vs absent)
    and the join separator value (``@``).

THREE INPUT BINDERS: ``userinfo`` (the optional credentials — selects the
``assembleAuthority`` branch and is emitted before the ``@``), ``authoritySlot``
(the primary host-portion slot — selects the ``authorityBase`` branch and is the
host portion when non-empty), and ``fallbackSlot`` (the alternate host-portion
slot — the host portion exactly when the authority slot is empty). All three are
load-bearing: the reject witnesses drive them to FOUR distinct input points so
the manifest demonstrates the post-image's dependence on which slot holds the
host, on whether credentials are present, on the separator value, and on the
fallback slot — not on a single pinned shape (pts = 4).

CARRIER NOTE — THE DECIDABLE BOUNDARY. A witness reaches the post-image through
Velvet's own tester machinery (``buildAuthorityTester userinfo authoritySlot
fallbackSlot = false`` says the extracted program's result violates the
postcondition at that concrete input) and closes by ``decide``, checked in a
file whose ``prove_correct`` block has been stripped so no tactic script can
mask the verdict. Every argument is a concrete ``"…".toList`` literal, so
``decide`` reduces the extracted rival program (a loop-free string computation)
without getting stuck. Both halves of every reject witness were confirmed
out-of-band with ``scripts/lean_verify.sh``: each ELABORATES green against its
rival (proof stripped) and FAILS against the frozen solution ("`decide` proved …
is false"), so it is a real discriminator, not a tautology.

ADVERSARIAL READ of the sibling's classes on this carrier:
  * SOUNDNESS / positive controls — APPLY. A structurally different but
    behaviourally identical impl (return the grounded model directly; and a
    branch-reordered form that keeps the frozen proof) must verify, else the
    spec is SPEC-TOO-STRONG on the shape of the impl.
  * ADMISSIBILITY — the sibling self-asserts an F2P-shaped input satisfies its
    fractional-permission precondition. This backend has NO ``require`` and no
    permission surface, so that probe is degenerate; the residual admissibility
    risk here is a DEGENERATE post-image. ``admiss-nondegenerate`` discharges an
    in-region ``assert`` pinning three genuinely distinct F2P-shaped outcomes
    (credentials folded in with the ``@`` join; bare host portion when no
    credentials; the parser-quirk fallback slot used when the authority slot is
    empty); the impl is kept verbatim so the method's own obligation still
    discharges.
  * FRAME-MUTATION — VACUOUS on this backend. The sibling carries a MANDATORY
    frame-mutation rival because a read-only component is held at a fractional
    heap permission (``Acc(.,1/2)``) an impl can illegally overwrite. Lean/Velvet
    are referentially transparent: ``userinfo`` / ``authoritySlot`` /
    ``fallbackSlot`` are immutable ``List Char`` values declared read-only (none
    ``mut``), there is no heap, no aliasing, no ``Old``, and no permission
    system. There is no read-only input to overwrite and no frame clause to
    violate, so the class has no carrier analogue; NOT ported (fabricating a
    substitute would test nothing).
  * DIVERGENCE / NON-TERMINATION: nothing to port (the sibling carries none) and
    no known hole, but the earlier reason is withdrawn. "A non-terminating impl
    cannot be written at all" is false: a rival rewrites the whole impl region and
    may splice a diverging loop, even though the frozen body is loop-free, which is
    why this bundle ships no divergence reject case. The class is closed by the
    verifier instead. Under this bundle's
    ``set_option loom.semantics.termination "total"`` a postcondition is claimed of
    ALL runs, not only terminating ones, so the verifier demands a decreasing
    measure on every loop AND discharges its descent; the option cannot drift from
    the file's ``open TotalCorrectness DemonicChoice``, because the ``set_option``
    elaborator itself runs ``openScope `TotalCorrectness``
    (``Loom/MonadAlgebras/WP/Options.lean:169-186``). Measured here with the proof
    reduced to a bare ``loom_solve``: a spliced
    ``while k > 0 / invariant k > 0 / done_with k = 0 / decreasing k`` with body
    ``k := k + 1`` is REJECTED on the measure's own goal,
    ``case «decreasing_1: k»``, residual ``⊢ k + 1 < k``.
  * UNGROUNDED-ORACLE ECHO — N/A. The post-image is pinned to two
    fully-unfolded ``def``s over the method's own arguments; there is no
    answer-key term a wrong impl could echo. The cheapest correct impl computes
    the helpers honestly, which the positive controls cover.
  * PARTIAL-DOMAIN / VALUE — carries the reject lane: each rival gets most of
    the domain right yet diverges on one sub-domain (credentials dropped; the
    wrong join separator; a stray join when no credentials; or the fallback slot
    ignored).
"""
from pathlib import Path

INSTANCE = "psf__requests-6028"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- the WHOLE gold impl block (between and INCLUDING the markers): a single
# ---- anchor lying wholly inside the impl region and unique in the file (both
# ---- facts asserted at load). Every reject rival and the direct-model positive
# ---- swap on this block.
_IMPL = """    -- impl-start
    let base : List Char :=
      if authoritySlot = [] then fallbackSlot else authoritySlot
    let out : List Char :=
      if userinfo = [] then base
      else userinfo ++ ['@'] ++ base
    return out
    -- impl-end"""
assert _BASE.count(_IMPL) == 1, "impl-block anchor drift — re-sync _IMPL"

# ---- the impl-start marker line (unique); the admissibility case inserts an
# ---- in-region `assert` immediately after it, keeping the whole gold body.
_IMPL_START = "    -- impl-start\n"
assert _BASE.count(_IMPL_START) == 1, "impl-start anchor drift"

# ---- the frozen proof body (tactic script only; elided from the spec view).
_PROOF_GOLD = "prove_correct buildAuthority by\n  loom_solve"
assert _BASE.count(_PROOF_GOLD) == 1, "proof anchor drift"


def _rewrite_impl(new_block, proof=_PROOF_GOLD):
    """Full variant: whole impl block replaced; proof left as the frozen script
    (the reshaped impls below all discharge under `loom_solve`)."""
    return _swap(_swap(_BASE, _IMPL, new_block), _PROOF_GOLD, proof)


# ---- witness preamble. The spec is a `method` CONTRACT, not a bare predicate,
# ---- so a witness reaches the post-image through Velvet's own tester machinery:
# ---- `buildAuthorityTester userinfo authoritySlot fallbackSlot = false` says
# ---- the extracted program's result violates the method's postcondition at that
# ---- concrete input. Checked in a file whose `prove_correct` block is stripped.
# ---- Every argument is a concrete literal so `decide` reduces the (loop-free)
# ---- extracted rival program without getting stuck.
def _witness(call):
    return ("\n"
            "extract_program_for buildAuthority\n"
            "prove_precondition_decidable_for buildAuthority\n"
            "prove_postcondition_decidable_for buildAuthority\n"
            "derive_tester_for buildAuthority\n\n"
            f"example : {call} = false := by\n  decide\n")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify. If a faithful correct impl cannot verify, the spec is
    # SPEC-TOO-STRONG. Both confirmed with a real build against the frozen
    # `prove_correct … by loom_solve` script.
    # =====================================================================
    {
        "id": "pos-control-direct-model",
        "kind": "soundness",
        "expect": "verify",
        # Cheapest honest correct impl: return the grounded pure model directly,
        # no intermediate `let` bindings — maximally structurally different from
        # the gold two-step build. `out` IS `assembleAuthority userinfo
        # (authorityBase …)`, so the ensures holds trivially and the frozen
        # `loom_solve` still closes it.
        "module": _rewrite_impl(
            "    -- impl-start\n"
            "    return assembleAuthority userinfo "
            "(authorityBase authoritySlot fallbackSlot)\n"
            "    -- impl-end"),
        "rationale": (
            "the cheapest honest correct impl returns the grounded model "
            "`assembleAuthority userinfo (authorityBase authoritySlot "
            "fallbackSlot)` directly. `out` IS that model, so the ensures holds "
            "on the whole domain; the reproof is the frozen `loom_solve`. If this "
            "fails to verify the spec is over-fit to the two-step build shape "
            "(SPEC-TOO-STRONG). Also the honest no-ungrounded-echo control: the "
            "helpers are the real work, so a direct return is correct, not a "
            "cheat. (Sibling: pos-control-branch-reorder — a structurally "
            "different correct impl.)"),
    },
    {
        "id": "pos-control-branch-reorder",
        "kind": "soundness",
        "expect": "verify",
        # Both branch decisions are REORDERED (non-empty arm first via `≠ []`),
        # semantically identical, different source. Keeps the two-step build and
        # the frozen proof. Direct port of the sibling's branch-reorder positive.
        "module": _rewrite_impl(
            "    -- impl-start\n"
            "    let base : List Char :=\n"
            "      if authoritySlot ≠ [] then authoritySlot else fallbackSlot\n"
            "    let out : List Char :=\n"
            "      if userinfo ≠ [] then userinfo ++ ['@'] ++ base\n"
            "      else base\n"
            "    return out\n"
            "    -- impl-end"),
        "rationale": (
            "reordering both branches (test `≠ []` and put the non-empty arm "
            "first) computes the same authority for every input, so `out = "
            "assembleAuthority userinfo (authorityBase …)` still holds on the "
            "whole domain; the frozen `loom_solve` closes it. A correct reshape "
            "must verify, else the postcondition is SPEC-TOO-STRONG (rejects a "
            "faithful impl over the shape of the branch order). (Sibling: "
            "pos-control-branch-reorder.)"),
    },

    # =====================================================================
    # ADMISSIBILITY — the method has NO `require`, so the sibling's "a normal
    # input satisfies the precondition" probe is degenerate here. The residual
    # admissibility risk on this domain is that the post-image is DEGENERATE at
    # the interesting point — a spec no impl distinguishes reads exactly like one
    # every impl meets. This case discharges an in-region `assert`, at three
    # fully concrete F2P-shaped inputs, that the post-image is NON-DEGENERATE:
    # credentials present fold in with an `@` (`u@h`), no credentials leave the
    # host portion alone (`h`), and an empty authority slot falls back to the
    # path slot (`p`) — three genuinely distinct outcomes. The surrounding impl
    # is kept verbatim so the method's own obligation still discharges; the proof
    # gains a `decide` arm to clear the assert goal.
    # =====================================================================
    {
        "id": "admiss-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _swap(_BASE, _IMPL_START,
                  _IMPL_START +
                  "    assert (with_name_prefix `admiss (\n"
                  '      assembleAuthority "u".toList (authorityBase "h".toList []) '
                  '= "u@h".toList ∧\n'
                  '      assembleAuthority [] (authorityBase "h".toList []) '
                  '= "h".toList ∧\n'
                  '      assembleAuthority [] (authorityBase [] "p".toList) '
                  '= "p".toList))\n'),
            _PROOF_GOLD,
            "prove_correct buildAuthority by\n  loom_solve\n  all_goals decide"),
        "rationale": (
            "the post-image is satisfiable AND non-degenerate at the F2P-shaped "
            "inputs: credentials present must fold into the host portion joined "
            "by `@` (`u@h`), no credentials must leave the host portion alone "
            "(`h`), and an empty authority slot must fall back to the path slot "
            "(`p`) — three distinct outcomes exercising both helpers. The "
            "in-region assert must discharge (else the obligation is degenerate); "
            "the impl is kept verbatim so `out = assembleAuthority …` still "
            "verifies. (Sibling: admiss-f2p-shaped-selfcall, re-aimed from "
            "precondition admissibility to post-image non-degeneracy since this "
            "backend has no `require` and no permission surface.)"),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # DISTINCT concrete input and the refinement argument that its faithful real
    # counterpart would NOT resolve the failing test.
    # =====================================================================
    {
        "id": "weak-drop-credential-join",
        "kind": "uniqueness",
        "expect": "reject",
        # Port of sibling partial-drop-credential-join (the pre-patch shape):
        # return the bare host portion, never folding the credentials back in.
        # Correct on every no-credentials input; diverges on every credentials
        # input — the exact behaviour the fix repairs.
        "module": _rewrite_impl(
            "    -- impl-start\n"
            "    return (if authoritySlot = [] then fallbackSlot "
            "else authoritySlot)\n"
            "    -- impl-end"),
        "refinement": (
            "this is the pre-change behaviour: assemble from the bare host "
            "portion, never re-attaching the credentials the splitter exposed in "
            "a separate slot. On a credentials-bearing location the credentials "
            "are silently dropped, so the re-emitted URL loses its userinfo and "
            "the scenario that round-trips a credentials-bearing location back to "
            "itself gets the credentials-stripped URL instead — it does NOT "
            "resolve. Correct on every no-credentials input (a true "
            "partial-domain break)."),
        "rationale": (
            "REJECT from `out = assembleAuthority …` via the credentials-present "
            "branch: when credentials are present the spec requires `userinfo ++ "
            "['@'] ++ base`, but this returns the bare `base`. Verifying would be "
            "SPEC-TOO-WEAK (the credentials-preservation the fix adds left "
            "unpinned). Refuted at credentials present (`userinfo = \"u\"`, "
            "non-empty authority slot) — where the spec keeps them and the rival "
            "drops them."),
        "witness": _witness('buildAuthorityTester "u".toList "h".toList "".toList'),
    },
    {
        "id": "weak-wrong-separator",
        "kind": "uniqueness",
        "expect": "reject",
        # Port of sibling partial-wrong-separator: fold credentials in with ':'
        # instead of '@'. Correct on every no-credentials input; diverges on
        # every credentials input by the separator value.
        "module": _rewrite_impl(
            "    -- impl-start\n"
            "    let base : List Char :=\n"
            "      if authoritySlot = [] then fallbackSlot else authoritySlot\n"
            "    return (if userinfo = [] then base "
            "else userinfo ++ [':'] ++ base)\n"
            "    -- impl-end"),
        "refinement": (
            "joining credentials to the host portion with ':' instead of '@' "
            "emits credentials and host separated by a colon rather than the "
            "authority delimiter, so the re-emitted URL is malformed for a "
            "credentials-bearing location and the round-trip scenario gets the "
            "wrong-delimiter string, != the expected URL — it does NOT resolve. "
            "Correct on every no-credentials input (a separator-value-only "
            "break)."),
        "rationale": (
            "REJECT from `out = assembleAuthority …` via the join SEPARATOR: the "
            "spec pins the credentials join to `['@']`, this rival uses `[':']`, "
            "so for a credentials input `userinfo ++ [':'] ++ base != userinfo "
            "++ ['@'] ++ base`. Verifying would be SPEC-TOO-WEAK on the separator "
            "value. Refuted at credentials present (`userinfo = \"a\"`, authority "
            "slot `\"b\"`) — a distinct input point from the drop-join rival "
            "(different userinfo/authority literals), so the two do not collapse "
            "to one probed point."),
        "witness": _witness('buildAuthorityTester "a".toList "b".toList "".toList'),
    },
    {
        "id": "weak-join-unconditional",
        "kind": "uniqueness",
        "expect": "reject",
        # Port of sibling nearmiss-creds-unconditional: fold credentials in
        # ALWAYS, even when userinfo is empty, emitting a stray leading '@'.
        # Correct on every credentials input; diverges on the no-credentials
        # sub-domain.
        "module": _rewrite_impl(
            "    -- impl-start\n"
            "    let base : List Char :=\n"
            "      if authoritySlot = [] then fallbackSlot else authoritySlot\n"
            "    return (userinfo ++ ['@'] ++ base)\n"
            "    -- impl-end"),
        "refinement": (
            "dropping the `if credentials present` guard prepends a stray '@' on "
            "a no-credentials location: the host portion is emitted as '@host', "
            "so the re-emitted URL carries an empty-userinfo delimiter it should "
            "not, != the expected URL for a no-credentials location — it does NOT "
            "resolve. Correct on every credentials-bearing input."),
        "rationale": (
            "REJECT from `out = assembleAuthority …` via the credentials-ABSENT "
            "branch: when `userinfo = []` the spec requires the bare `base`, but "
            "this returns `[] ++ ['@'] ++ base = '@' :: base`. Verifying would be "
            "SPEC-TOO-WEAK on the no-credentials sub-domain. Refuted at `userinfo "
            "= []` (empty credentials, non-empty authority slot) — the sub-domain "
            "the drop-join and wrong-separator rivals agree with gold on, so it "
            "shares no witness with them, and it drives `userinfo` to the empty "
            "value the credentials rivals never take."),
        "witness": _witness('buildAuthorityTester "".toList "h".toList "".toList'),
    },
    {
        "id": "weak-ignore-fallback-slot",
        "kind": "uniqueness",
        "expect": "reject",
        # Attacks the `authorityBase` clause (the parser-quirk fallback the
        # sibling's model.py did not separate out): always use the authority
        # slot, never the fallback. Correct whenever the authority slot is
        # non-empty; diverges exactly when it is empty and the host portion lives
        # in the fallback slot.
        "module": _rewrite_impl(
            "    -- impl-start\n"
            "    let base : List Char := authoritySlot\n"
            "    let out : List Char :=\n"
            "      if userinfo = [] then base\n"
            "      else userinfo ++ ['@'] ++ base\n"
            "    return out\n"
            "    -- impl-end"),
        "refinement": (
            "ignoring the fallback slot means that when the splitter left the "
            "authority slot empty and stashed the host portion in the path slot, "
            "the rebuild sees an empty host portion instead of the real one; the "
            "re-emitted URL loses its host for exactly that parser-quirk input, "
            "so the scenario over such a location gets an empty-authority URL, != "
            "expected — it does NOT resolve. Correct whenever the authority slot "
            "is non-empty."),
        "rationale": (
            "REJECT from `out = assembleAuthority …` via the `authorityBase` "
            "clause: the spec resolves the host portion to `fallbackSlot` when "
            "`authoritySlot = []`, this rival always uses `authoritySlot`, so on "
            "an empty authority slot the two differ. Verifying would be "
            "SPEC-TOO-WEAK (the fallback resolution unpinned). This is the "
            "sub-domain that proves `fallbackSlot` is LOAD-BEARING: the witness "
            "fixes it non-empty (`\"p\"`) and empties the authority slot, the "
            "only probed point where the fallback slot determines the result — "
            "no other rival exercises it."),
        "witness": _witness('buildAuthorityTester "".toList "".toList "p".toList'),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery ships 8 SPEC cases (1
# soundness positive, 1 admissibility, 6 uniqueness rivals — one a MANDATORY
# frame-mutation rival) plus an EMPTY AXIOM lane (AXIOM_TESTS = []). The sibling
# contracts `normalize_location` over NINE inputs (scheme, creds, authority,
# path, query, frag as read-only `List[int]`, + has_creds/has_query/has_frag
# bools) and pins the WHOLE re-assembled URL over `effective_authority` +
# `assembled`. This backend narrows the modeled slice to the discriminating
# core — the AUTHORITY reconstruction only (`buildAuthority` / `assembleAuthority`
# / `authorityBase`) — since scheme/path/query/fragment assembly is delegated to
# an UNCHANGED downstream re-assembler that this bundle exercises live in G-CONF
# rather than models (mapping.md §3). That carrier narrowing removes the sibling
# cases attached to the query/fragment sub-domains outright (they are not
# modeled here), and makes the frame + divergence classes vacuous.
#
#   sibling case                    kind          -> here                         disposition
#   -----------------------------------------------------------------------------------------
#   pos-control-branch-reorder      soundness     -> pos-control-branch-reorder   PORTED
#                                                    (+ pos-control-direct-model  ADDED)
#   admiss-f2p-shaped-selfcall      admissibility -> admiss-nondegenerate         RE-AIMED
#   frame-mutate-authority          uniqueness    -> (none)                       VACUOUS
#   partial-drop-credential-join    uniqueness    -> weak-drop-credential-join    PORTED
#   partial-wrong-separator         uniqueness    -> weak-wrong-separator         PORTED
#   partial-drop-query              uniqueness    -> (none)                       NOT MODELED
#   partial-drop-fragment           uniqueness    -> (none)                       NOT MODELED
#   nearmiss-creds-unconditional    uniqueness    -> weak-join-unconditional      PORTED
#   (bundle-specific)               uniqueness    -> weak-ignore-fallback-slot    ADDED
#   AXIOM_TESTS (2 A-reference)     axiom         -> (none)                       N/A (G-AX)
#
# 3 uniqueness ported + 1 added, 1 admissibility re-aimed, 1 soundness ported + 1
# added; 1 uniqueness vacuous, 2 uniqueness not modeled; axiom lane out of scope.
#
# PORTED (the three authority-core rivals): partial-drop-credential-join ->
#   weak-drop-credential-join (the literal pre-patch shape: drop the credential
#   fold; refuted at credentials present — the F2P discriminator).
#   partial-wrong-separator -> weak-wrong-separator (join with ':' not '@';
#   refuted at credentials present, a distinct input point).
#   nearmiss-creds-unconditional -> weak-join-unconditional (drop the "if
#   credentials" guard -> stray '@'; refuted on the no-credentials sub-domain).
# ADDED (weak-ignore-fallback-slot): this bundle models the parser-quirk slot
#   resolution as a SEPARATE helper `authorityBase` (mapping.md §1) that the
#   sibling's model.py did not carry as an independent clause. A rival that
#   ignores the fallback slot attacks that clause; refuted at an empty authority
#   slot with a non-empty fallback slot — the only point where `fallbackSlot`
#   determines the result, so it is what makes that binder load-bearing.
# RE-AIMED (admiss-f2p-shaped-selfcall -> admiss-nondegenerate): the sibling
#   asserts an F2P-shaped input satisfies its half-permission Requires. This
#   backend has NO `require` (the operation is total on its carrier) and no
#   permission surface, so that probe is degenerate; the sharper residual risk is
#   a DEGENERATE post-image, so the case is re-aimed to a live in-region assert
#   pinning three distinct F2P-shaped outcomes (credentials folded in via '@';
#   bare host portion; parser-quirk fallback), exercising both helpers.
# VACUOUS (frame-mutate-authority): the sibling's MANDATORY frame-mutation rival
#   writes to the half-permission `authority` input (`authority.append(64)`) and
#   is rejected for INSUFFICIENT PERMISSION. This backend is referentially
#   transparent: `userinfo`/`authoritySlot`/`fallbackSlot` are immutable values
#   declared read-only (none `mut`), there is no heap, no aliasing, no `Old`, and
#   no permission system. There is no read-only input to overwrite and no frame
#   clause to violate, so the class has no carrier analogue. Omitted as a genuine
#   carrier fact, NOT fabricated (porting map: this class is vacuous on a
#   referentially-transparent backend).
# NOT MODELED (partial-drop-query, partial-drop-fragment): the sibling pins the
#   WHOLE re-assembled URL, so it can attack the query- and fragment-append
#   sub-domains. This bundle models ONLY the authority reconstruction — the
#   scheme/path/query/fragment assembly is delegated to an UNCHANGED downstream
#   re-assembler that mapping.md §3 exercises end-to-end in G-CONF rather than
#   modeling. There is no query/fragment append clause in this bundle's spec, so
#   these two rivals have no counterpart. This is carrier narrowing (the
#   Lean-family bundle models only the discriminating core), NOT an omission for
#   difficulty: the modeled slice is defended and attacked in full.
# DIVERGENCE / NON-TERMINATION: the sibling carries no such case, so nothing to
#   port, and no known hole. Reason corrected: a diverging impl CAN be written (a
#   rival rewrites the whole impl region), so the class is not vacuous by
#   inexpressibility; it is closed by the verifier. This bundle sets
#   `loom.semantics.termination "total"`, so a postcondition is claimed of ALL
#   runs and every loop owes a decreasing measure AND its descent. Measured with
#   the proof reduced to `loom_solve`: a spliced `decreasing k` loop whose body is
#   `k := k + 1` is refused on `case «decreasing_1: k»`, residual `k + 1 < k`.
#   No case is SHIPPED only because the frozen body is loop-free.
#
# BINDER / CLAUSE COVERAGE. The sole `ensures` clause `out = assembleAuthority
#   userinfo (authorityBase authoritySlot fallbackSlot)` has THREE binders —
#   `userinfo`, `authoritySlot`, `fallbackSlot` (all `List Char`) — over two
#   helpers with three independently-attackable facets (authorityBase's slot
#   choice; assembleAuthority's credentials-present branch incl. the '@'
#   separator value; assembleAuthority's credentials-absent branch). The four
#   reject witnesses probe four DISTINCT input points (pts=4):
#     * weak-drop-credential-join   "u" / "h" / ""    (credentials present)
#     * weak-wrong-separator        "a" / "b" / ""    (credentials present)
#     * weak-join-unconditional     ""  / "h" / ""    (credentials absent)
#     * weak-ignore-fallback-slot   ""  / ""  / "p"   (authority slot empty)
#   So `userinfo` ranges over {non-empty, empty} (drop/sep hold it non-empty;
#   uncond/fallback empty — and it is load-bearing: the sole binder distinguishing
#   the drop-join and unconditional rivals' branches). `authoritySlot` ranges
#   over {non-empty, empty} (empty only in the fallback rival, where it flips the
#   authorityBase branch). `fallbackSlot` ranges over {"", "p"} and is shown
#   load-bearing by weak-ignore-fallback-slot, the only point where it determines
#   the result. Both helpers are attacked: authorityBase (weak-ignore-fallback-
#   slot), assembleAuthority credentials-present branch + separator (weak-drop-
#   credential-join: which branch; weak-wrong-separator: the '@' value), and
#   assembleAuthority credentials-absent branch (weak-join-unconditional). No
#   binder is pinned at a single value across the reject set.
#
# AXIOM_TESTS: empty. mapping.md §3.1: the modeled authority rebuild calls NO
#   unchanged callee (axioms = [], deep_model_references = []); the two real
#   callees bracketing the slice are exercised live in G-CONF, not axiomatized.
#   G-AX is a skip. The sibling's AXIOM_TESTS carries A-reference deep-model
#   probes for its own carrier; this gate ignores AXIOM_TESTS regardless.
AXIOM_TESTS = []
