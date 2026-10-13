"""properties.py — G-PBT falsification battery for psf__requests-6028 (lean).

NOT a Lean file; a manifest the G-PBT gate executes. Each SPEC case is a full
``Solution.lean`` variant that shares the FROZEN spec byte-for-byte (region
surgery edits ONLY text inside an ``-- impl-start`` / ``-- impl-end`` region —
and, for a case that legitimately re-proves, inside the ``-- proof-start`` /
``-- proof-end`` region — so ``markers.same_spec`` holds and every
``theorem correct_prependScheme`` STATEMENT stays byte-identical).
``expect="verify"`` passes iff (in scope AND the file elaborates with the
obligation closed, no ``sorry``/``admit``/``axiom``/``native_decide``);
``expect="reject"`` passes iff (in scope AND it does NOT verify AND the case's
refutation ``witness`` holds of the rival while FAILING on the frozen solution).

DEFENDED SURFACE (one modeled behavior: reconstituting a URL string from the
components a parser hands back, supplying a default scheme when none was
parsed):

  prependScheme (scheme0 auth : Option String)
                (authority0 path query fragment : String) (newScheme : String)
                -> String
    result = reassemble scheme0 auth authority0 path query fragment newScheme

The sole spec clause is that equality: the result is EXACTLY the standard-syntax
round-trip that carries every parsed component into its slot. Under the modeled
domain (``authority0 ≠ ""``, ``newScheme ≠ ""``, a present scheme non-empty —
the three ``correct_prependScheme`` binders) ``reassemble`` reduces to
``assembleUrl scheme (eff-authority) path query fragment`` where the effective
authority re-attaches a present userinfo as ``userinfo@authority``. There are
SEVEN input binders; the reject witnesses vary scheme0, auth, path, query and
fragment across their probed points (see BINDER COVERAGE).

ADVERSARIAL READ of the nagini classes on this carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS. Lean is referentially transparent:
    the inputs are immutable ``String``/``Option String`` values, carry no heap
    permission, and there is no read-only half-permission to overwrite. The
    nagini frame-mutation rival (``authority.append(64)`` into a read-only input)
    has no expressible instance here and no discriminating witness; deliberately
    not ported, no substitute fabricated.

  * DIVERGENCE / NON-TERMINATION — VACUOUS. ``implementation_prependScheme`` is a
    total Lean ``def`` (``Id.run do`` over finite branch/append steps, no
    recursion, no loop); a diverging implementation cannot be written at all, so
    there is no partial-``semantics`` hole to record. (The nagini sibling carries
    no ``diverge-*`` case either.)

  * UNGROUNDED-ORACLE ECHO — VACUOUS. The postcondition is GROUNDED in the
    inputs: an equality against ``reassemble …``, itself built only from the
    seven binders and concrete ``String`` operations (fully transparent, no
    ``opaque``/``axiom`` — the bundle declares none). There is no answer-key an
    implementation could echo without doing the work; in its place the battery
    carries an honest branch-reorder POSITIVE CONTROL that must verify plus an
    ADMISSIBILITY control pinning satisfiability at the F2P/P2P inputs.

  * PARTIAL-DOMAIN / VALUE — APPLIES, and is the whole battery. The reported
    defect drops the parsed userinfo on re-assembly (a proxy URL with credentials
    loses ``user:pass@`` and 407s). The rivals below attack the single spec
    clause directly: they drop or mis-form the userinfo re-attachment (the
    reported bug and its value-class neighbours), or drop one of the other
    standard slots (query / fragment / path) or the scheme default, each on the
    exact sub-domain the F2P/P2P inputs occupy.

BINDER COVERAGE (against ``correct_prependScheme``'s seven inputs; the reject
witnesses move every binder the modeled clause reads):

  * ``auth`` (userinfo) — the load-bearing binder of the reported fix. Attacked
    by ``weak-drop-userinfo`` (drops the re-attach) and ``weak-userinfo-sep``
    (wrong separator ``:`` instead of ``@``), both at ``auth = some "user:pass"``
    where the spec re-attaches it.
  * ``scheme0`` / ``newScheme`` — the scheme-default clause. Attacked by
    ``weak-scheme-default`` at ``scheme0 = none``, where the result must fall back
    to ``newScheme`` (the schemeless P2P inputs) and the rival emits ``""``.
  * ``query`` — attacked by ``weak-drop-query`` at ``query = "query"`` (both F2P
    URLs carry ``?query``).
  * ``fragment`` — attacked by ``weak-drop-fragment`` at ``fragment = "frag"``.
  * ``path`` — attacked by ``weak-drop-path`` at ``path = "/path"``.
  * ``auth = none`` (userinfo ABSENT) — attacked by ``weak-uncond-userinfo-join``,
    which collapses the ``Option`` and joins an absent userinfo as the empty
    string, emitting a stray ``@``. This is the only case that moves ``auth`` to
    its ``none`` point while holding the rest of the slots correct, so without it
    a rival that mishandles only the no-userinfo sub-domain is invisible.
  * ``authority0`` — pinned non-empty by the ``authority0 ≠ ""`` precondition
    binder in every case; no admissible input moves it (the empty-authority swap
    is out of the modeled domain per mapping.md), so it is intentionally held
    fixed — the spec, not an under-attacked binder.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen script (``simp only [Id.run, …]`` then a
``cases``/``by_cases`` … ``rfl`` tuned to the frozen branch order) breaks on any
reshape — so a rejection alone attributes nothing to the spec. Every reject case
therefore carries a Lean snippet stating ``¬ problem_spec_prependScheme … (rival
…)`` at one CONCRETE all-literal input; the carrier is fully computable
``String``, so ``decide`` closes it with no conditioning (no opaque term, so no
hypothesis binders — the ``witness-inconsistent`` risk does not arise). Each was
built against its rival (must elaborate) and against the frozen solution (must
fail), so it discriminates rather than asserting a tautology.

AXIOM lane: EMPTY here. meta.json axioms == [] and the two deep-model references
(``reassemble`` / ``assembleUrl``, the A-reference validated == the real
``urlunparse`` / ``'@'.join`` by G-AX/G-CONF) belong to the axiom lane, not this
gate. nagini's AXIOM_TESTS are dropped by design.

PORTED FROM NAGINI. (1) pos-control-branch-reorder -> ``pos-branch-reorder``;
(2) admiss-f2p-shaped-selfcall -> ``admiss-f2p-p2p-instances``; (4)
partial-drop-credential-join -> ``weak-drop-userinfo``; (5)
partial-wrong-separator -> ``weak-userinfo-sep``; (6) partial-drop-query ->
``weak-drop-query``; (7) partial-drop-fragment -> ``weak-drop-fragment``.
nagini (3) frame-mutate-authority is VACUOUS here (see above) — not ported.
nagini (8) nearmiss-creds-unconditional IS ported, as
``weak-uncond-userinfo-join``. It required care about WHICH encoding of "drop the
guard" is faithful to the nagini original, and the first reading was wrong:

  * dropping only the inner ``a ≠ ""`` test while keeping the ``Option`` match
    diverges from the spec solely at ``auth = some ""``, an input the upstream
    parse never produces for a no-userinfo location (it yields ``none``). That
    rival IS rejected and a witness at ``auth = some ""`` does discriminate, but
    its faithful patch still resolves every F2P/P2P, so it carries no
    verify-does-not-resolve refinement and is not what nagini modeled.
  * nagini's rival drops the ``has_creds`` BOOLEAN test, i.e. it treats an ABSENT
    userinfo as empty and joins unconditionally. On this carrier that is
    ``auth.getD ""``, which collapses ``none`` and ``some ""`` to the same point
    and diverges from the spec at ``auth = none`` — exactly nagini's
    ``creds == [] ∧ has_creds = False`` point, and exactly the shape of all three
    schemeless P2P locations. Its faithful patch emits a stray ``@`` before the
    host and FAILS those P2P tests.

The second reading is the faithful port and is the one shipped; the ``auth =
none`` point it attacks was reachable all along, so recording (8) as
inexpressible would have been wrong. Added beyond nagini (still F2P/P2P-grounded):
``weak-scheme-default`` (attacks the scheme-default clause on the schemeless P2P
inputs) and ``weak-drop-path`` (attacks the path slot), to make the scheme and
path binders load-bearing. Also added: ``pos-nonmonadic-reshape``, a positive
control whose impl abandons the frozen impl's mutable-``do`` shape entirely (a
plain ``let``-chain) and re-proves the frozen obligation, so at least one
soundness case exercises a shape the frozen tactic script does NOT close.
See ``assessment`` in the submitted payload.
"""
from pathlib import Path

INSTANCE = "psf__requests-6028"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- region anchors (each unique inside Solution.lean; verified at load) ----
# The FULL body of the one impl region and the FULL body of the one proof region,
# so every replacement lands entirely inside the region it edits and the spec
# view (thus same_spec) is untouched.
_IMPL = (
    'def implementation_prependScheme (scheme0 auth : Option String)\n'
    '    (authority0 path0 query fragment : String) (newScheme : String) :\n'
    '    String := Id.run do\n'
    '  let mut authority := authority0\n'
    '  let mut path := path0\n'
    '  if authority = "" then\n'
    '    let saved := authority\n'
    '    authority := path\n'
    '    path := saved\n'
    '  match auth with\n'
    '  | some a => if a ≠ "" then\n'
    '                authority := a ++ "@" ++ authority\n'
    '  | none => pure ()\n'
    '  let scheme := match scheme0 with\n'
    '    | none => newScheme\n'
    '    | some s => s\n'
    '  return assembleUrl scheme authority path query fragment'
)

_PROOF = (
    'theorem correct_prependScheme :\n'
    '    ∀ (scheme0 auth : Option String)\n'
    '      (authority0 path query fragment : String) (newScheme : String),\n'
    '      authority0 ≠ "" → newScheme ≠ "" →\n'
    '      (∀ s, scheme0 = some s → s ≠ "") →\n'
    '      problem_spec_prependScheme scheme0 auth authority0 path query fragment newScheme\n'
    '        (implementation_prependScheme scheme0 auth authority0 path query fragment newScheme) := by\n'
    '  intro scheme0 auth authority0 path query fragment newScheme hauth hns hs\n'
    '  unfold problem_spec_prependScheme implementation_prependScheme reassemble\n'
    '  simp only [Id.run, if_neg hauth]\n'
    '  cases auth with\n'
    '  | none => rfl\n'
    '  | some a => by_cases h : a = "" <;> simp only [h, if_true, if_false, ne_eq, not_true, not_false_iff] <;> rfl'
)

assert _IMPL in _BASE and _BASE.count(_IMPL) == 1, "impl anchor drift / not unique"
assert _PROOF in _BASE and _BASE.count(_PROOF) == 1, "proof anchor drift / not unique"


# ---------------------------------------------------------------------------
# POSITIVE CONTROL (soundness). A structurally-different but CORRECT impl:
# compute the defaulted scheme FIRST, then the empty-authority swap, then the
# userinfo re-attach. Same value at every step (the scheme computation is
# independent of the authority path), so the sole spec clause is unchanged. The
# frozen proof still closes because its `simp only [Id.run, if_neg hauth]` + the
# `cases auth` … `rfl` shape is insensitive to the order the independent scheme
# `let` is bound in; kept byte-identical. Ports nagini (1). MUST verify, else
# SPEC-TOO-STRONG.
# ---------------------------------------------------------------------------
_IMPL_POS = (
    'def implementation_prependScheme (scheme0 auth : Option String)\n'
    '    (authority0 path0 query fragment : String) (newScheme : String) :\n'
    '    String := Id.run do\n'
    '  let scheme := match scheme0 with\n'
    '    | none => newScheme\n'
    '    | some s => s\n'
    '  let mut authority := authority0\n'
    '  let mut path := path0\n'
    '  if authority = "" then\n'
    '    let saved := authority\n'
    '    authority := path\n'
    '    path := saved\n'
    '  match auth with\n'
    '  | some a => if a ≠ "" then\n'
    '                authority := a ++ "@" ++ authority\n'
    '  | none => pure ()\n'
    '  return assembleUrl scheme authority path query fragment'
)


# ---------------------------------------------------------------------------
# ADMISSIBILITY. The frozen obligation carries the modeled-domain precondition
# (authority0 ≠ "", newScheme ≠ "", present scheme non-empty). This control
# discharges the spec predicate at three ground inputs the behavior MUST admit —
# both F2P shapes (credential-bearing URL with query: `user:pass@` and `user@`)
# and a P2P shape (schemeless -> default applied) — by evaluation, THEN closes
# the frozen obligation verbatim. Nothing is assumed: the ground facts are
# `have`s inside the tactic body and the theorem statement is byte-identical.
# If any ground instance could not be discharged, the behavior would be
# unsatisfiable at an input it must admit (analogue of PRECOND-TOO-STRONG).
# Ports nagini (2).
# ---------------------------------------------------------------------------
_PROOF_ADMISS = (
    'theorem correct_prependScheme :\n'
    '    ∀ (scheme0 auth : Option String)\n'
    '      (authority0 path query fragment : String) (newScheme : String),\n'
    '      authority0 ≠ "" → newScheme ≠ "" →\n'
    '      (∀ s, scheme0 = some s → s ≠ "") →\n'
    '      problem_spec_prependScheme scheme0 auth authority0 path query fragment newScheme\n'
    '        (implementation_prependScheme scheme0 auth authority0 path query fragment newScheme) := by\n'
    '  have _f2p1 : problem_spec_prependScheme (some "http") (some "user:pass") "example.com" "/path" "query" "" "http"\n'
    '      (implementation_prependScheme (some "http") (some "user:pass") "example.com" "/path" "query" "" "http") := by\n'
    '    unfold problem_spec_prependScheme implementation_prependScheme reassemble; decide\n'
    '  have _f2p2 : problem_spec_prependScheme (some "http") (some "user") "example.com" "/path" "query" "" "http"\n'
    '      (implementation_prependScheme (some "http") (some "user") "example.com" "/path" "query" "" "http") := by\n'
    '    unfold problem_spec_prependScheme implementation_prependScheme reassemble; decide\n'
    '  have _p2p : problem_spec_prependScheme none none "example.com" "/path" "" "" "http"\n'
    '      (implementation_prependScheme none none "example.com" "/path" "" "" "http") := by\n'
    '    unfold problem_spec_prependScheme implementation_prependScheme reassemble; decide\n'
    '  intro scheme0 auth authority0 path query fragment newScheme hauth hns hs\n'
    '  unfold problem_spec_prependScheme implementation_prependScheme reassemble\n'
    '  simp only [Id.run, if_neg hauth]\n'
    '  cases auth with\n'
    '  | none => rfl\n'
    '  | some a => by_cases h : a = "" <;> simp only [h, if_true, if_false, ne_eq, not_true, not_false_iff] <;> rfl'
)


# ---------------------------------------------------------------------------
# UNIQUENESS rivals. Each replaces ONLY the impl body; the frozen proof script
# is carried verbatim (it will not close for the reshaped impl, which is exactly
# why a witness is required). Each witness states `¬ problem_spec_prependScheme
# … (rival …)` at one concrete input and was checked to elaborate against the
# rival and FAIL on the frozen solution.
# ---------------------------------------------------------------------------

# (4) DROP THE USERINFO RE-ATTACH — the reported bug. Assemble from the bare
# authority, never re-attaching a present userinfo.
_IMPL_DROP_USERINFO = (
    'def implementation_prependScheme (scheme0 auth : Option String)\n'
    '    (authority0 path0 query fragment : String) (newScheme : String) :\n'
    '    String := Id.run do\n'
    '  let mut authority := authority0\n'
    '  let mut path := path0\n'
    '  if authority = "" then\n'
    '    let saved := authority\n'
    '    authority := path\n'
    '    path := saved\n'
    '  match auth with\n'
    '  | some _ => pure ()\n'
    '  | none => pure ()\n'
    '  let scheme := match scheme0 with\n'
    '    | none => newScheme\n'
    '    | some s => s\n'
    '  return assembleUrl scheme authority path query fragment'
)

# (5) WRONG USERINFO SEPARATOR — join with ':' instead of '@'.
_IMPL_USERINFO_SEP = (
    'def implementation_prependScheme (scheme0 auth : Option String)\n'
    '    (authority0 path0 query fragment : String) (newScheme : String) :\n'
    '    String := Id.run do\n'
    '  let mut authority := authority0\n'
    '  let mut path := path0\n'
    '  if authority = "" then\n'
    '    let saved := authority\n'
    '    authority := path\n'
    '    path := saved\n'
    '  match auth with\n'
    '  | some a => if a ≠ "" then\n'
    '                authority := a ++ ":" ++ authority\n'
    '  | none => pure ()\n'
    '  let scheme := match scheme0 with\n'
    '    | none => newScheme\n'
    '    | some s => s\n'
    '  return assembleUrl scheme authority path query fragment'
)

# (6) DROP THE QUERY SLOT — pass "" for query into the assembler.
_IMPL_DROP_QUERY = (
    'def implementation_prependScheme (scheme0 auth : Option String)\n'
    '    (authority0 path0 query fragment : String) (newScheme : String) :\n'
    '    String := Id.run do\n'
    '  let mut authority := authority0\n'
    '  let mut path := path0\n'
    '  if authority = "" then\n'
    '    let saved := authority\n'
    '    authority := path\n'
    '    path := saved\n'
    '  match auth with\n'
    '  | some a => if a ≠ "" then\n'
    '                authority := a ++ "@" ++ authority\n'
    '  | none => pure ()\n'
    '  let scheme := match scheme0 with\n'
    '    | none => newScheme\n'
    '    | some s => s\n'
    '  return assembleUrl scheme authority path "" fragment'
)

# (7) DROP THE FRAGMENT SLOT — pass "" for fragment into the assembler.
_IMPL_DROP_FRAG = (
    'def implementation_prependScheme (scheme0 auth : Option String)\n'
    '    (authority0 path0 query fragment : String) (newScheme : String) :\n'
    '    String := Id.run do\n'
    '  let mut authority := authority0\n'
    '  let mut path := path0\n'
    '  if authority = "" then\n'
    '    let saved := authority\n'
    '    authority := path\n'
    '    path := saved\n'
    '  match auth with\n'
    '  | some a => if a ≠ "" then\n'
    '                authority := a ++ "@" ++ authority\n'
    '  | none => pure ()\n'
    '  let scheme := match scheme0 with\n'
    '    | none => newScheme\n'
    '    | some s => s\n'
    '  return assembleUrl scheme authority path query ""'
)

# (added) DROP THE PATH SLOT — pass "" for path into the assembler.
_IMPL_DROP_PATH = (
    'def implementation_prependScheme (scheme0 auth : Option String)\n'
    '    (authority0 path0 query fragment : String) (newScheme : String) :\n'
    '    String := Id.run do\n'
    '  let mut authority := authority0\n'
    '  let mut path := path0\n'
    '  if authority = "" then\n'
    '    let saved := authority\n'
    '    authority := path\n'
    '    path := saved\n'
    '  match auth with\n'
    '  | some a => if a ≠ "" then\n'
    '                authority := a ++ "@" ++ authority\n'
    '  | none => pure ()\n'
    '  let scheme := match scheme0 with\n'
    '    | none => newScheme\n'
    '    | some s => s\n'
    '  return assembleUrl scheme authority "" query fragment'
)

# (added) DROP THE SCHEME DEFAULT — emit "" when no scheme was parsed instead of
# the supplied default.
_IMPL_SCHEME_DEFAULT = (
    'def implementation_prependScheme (scheme0 auth : Option String)\n'
    '    (authority0 path0 query fragment : String) (newScheme : String) :\n'
    '    String := Id.run do\n'
    '  let mut authority := authority0\n'
    '  let mut path := path0\n'
    '  if authority = "" then\n'
    '    let saved := authority\n'
    '    authority := path\n'
    '    path := saved\n'
    '  match auth with\n'
    '  | some a => if a ≠ "" then\n'
    '                authority := a ++ "@" ++ authority\n'
    '  | none => pure ()\n'
    '  let scheme := match scheme0 with\n'
    '    | none => ""\n'
    '    | some s => s\n'
    '  return assembleUrl scheme authority path query fragment'
)


# (8) UNCONDITIONAL USERINFO JOIN — treat an ABSENT userinfo as the empty string
# and join it anyway, so a location with no userinfo gains a leading '@'. Ports
# nagini nearmiss-creds-unconditional: `auth.getD ""` collapses `none` and
# `some ""` to one point, which is nagini's `creds == [] ∧ has_creds = False`.
_IMPL_UNCOND_JOIN = (
    'def implementation_prependScheme (scheme0 auth : Option String)\n'
    '    (authority0 path0 query fragment : String) (newScheme : String) :\n'
    '    String := Id.run do\n'
    '  let mut authority := authority0\n'
    '  let mut path := path0\n'
    '  if authority = "" then\n'
    '    let saved := authority\n'
    '    authority := path\n'
    '    path := saved\n'
    '  authority := (auth.getD "") ++ "@" ++ authority\n'
    '  let scheme := match scheme0 with\n'
    '    | none => newScheme\n'
    '    | some s => s\n'
    '  return assembleUrl scheme authority path query fragment'
)


# ---------------------------------------------------------------------------
# SECOND POSITIVE CONTROL (soundness), stronger than pos-branch-reorder. That
# case keeps the frozen `Id.run do` skeleton, so the frozen tactic script closes
# it unchanged — which makes it a weak probe of SPEC-TOO-STRONG, since it never
# leaves the shape the script was tuned to. This one abandons the monadic shape
# altogether: no `Id.run`, no `mut`, just a `let`-chain computing the swap, the
# effective authority and the defaulted scheme (via `Option.getD`). The frozen
# script does NOT close it (no `Id.run` to `simp` away and the branch structure
# differs), so the case must RE-PROVE the frozen obligation — with a byte-
# identical STATEMENT, only the tactic body differing, which `variant_scope`
# permits. If a faithful correct impl in this shape could not be proven, the
# spec would be too strong for a re-shaped but correct implementation.
# ---------------------------------------------------------------------------
_IMPL_POS_PURE = (
    'def implementation_prependScheme (scheme0 auth : Option String)\n'
    '    (authority0 path0 query fragment : String) (newScheme : String) :\n'
    '    String :=\n'
    '  let authority0swapped := if authority0 = "" then path0 else authority0\n'
    '  let pathswapped := if authority0 = "" then authority0 else path0\n'
    '  let eff := match auth with\n'
    '    | none => authority0swapped\n'
    '    | some a => if a = "" then authority0swapped else a ++ "@" ++ authority0swapped\n'
    '  assembleUrl (scheme0.getD newScheme) eff pathswapped query fragment'
)

_PROOF_POS_PURE = (
    'theorem correct_prependScheme :\n'
    '    ∀ (scheme0 auth : Option String)\n'
    '      (authority0 path query fragment : String) (newScheme : String),\n'
    '      authority0 ≠ "" → newScheme ≠ "" →\n'
    '      (∀ s, scheme0 = some s → s ≠ "") →\n'
    '      problem_spec_prependScheme scheme0 auth authority0 path query fragment newScheme\n'
    '        (implementation_prependScheme scheme0 auth authority0 path query fragment newScheme) := by\n'
    '  intro scheme0 auth authority0 path query fragment newScheme hauth hns hs\n'
    '  unfold problem_spec_prependScheme implementation_prependScheme reassemble\n'
    '  cases scheme0 <;> cases auth <;>\n'
    '    simp_all [Option.getD, ne_eq, ite_not]'
)


def _wit(scheme0, auth, authority0, path, query, fragment, newScheme):
    """A reject witness: ¬ (spec holds of the impl) at one concrete input.

    Fully computable String carrier, so `decide` closes it; no opaque term, so
    the head binds nothing (no hypothesis => no witness-inconsistent risk)."""
    args = (f'{scheme0} {auth} {authority0} {path} {query} {fragment} {newScheme}')
    return (
        f'example : ¬ problem_spec_prependScheme {args}\n'
        f'    (implementation_prependScheme {args}) := by\n'
        f'  unfold problem_spec_prependScheme implementation_prependScheme reassemble\n'
        f'  decide\n'
    )


SPEC_TESTS = [
    {
        "id": "pos-branch-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _IMPL, _IMPL_POS),
        "rationale": (
            "A structurally-different but CORRECT impl: compute the defaulted "
            "scheme FIRST, then the empty-authority swap and the userinfo "
            "re-attach. The scheme computation is independent of the authority "
            "steps, so the result equals `reassemble …` at every input — the sole "
            "spec clause is unchanged. The frozen proof closes unchanged because "
            "its `simp only [Id.run, if_neg hauth]` + `cases auth … rfl` shape is "
            "insensitive to the order the independent scheme `let` binds in. Must "
            "verify, else SPEC-TOO-STRONG. Ports nagini pos-control-branch-reorder."),
    },
    {
        "id": "pos-nonmonadic-reshape",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_swap(_BASE, _IMPL, _IMPL_POS_PURE),
                        _PROOF, _PROOF_POS_PURE),
        "rationale": (
            "A CORRECT impl that abandons the frozen impl's shape entirely: no "
            "`Id.run`, no `mut`, just a `let`-chain computing the swap, the "
            "effective authority and the defaulted scheme (`Option.getD`). It "
            "computes `reassemble …` at every input, so the sole spec clause "
            "holds, but the frozen tactic script does NOT close it — so the case "
            "must RE-PROVE the obligation, with a byte-identical STATEMENT and "
            "only the tactic body differing (permitted by variant_scope). This is "
            "a strictly stronger SPEC-TOO-STRONG probe than pos-branch-reorder, "
            "which stays inside the shape the frozen script was tuned to and so "
            "verifies without the spec ever being re-discharged for a new shape. "
            "If a faithful correct impl in this shape could not be proven, the "
            "spec would reject a correct implementation."),
    },
    {
        "id": "admiss-f2p-p2p-instances",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _PROOF, _PROOF_ADMISS),
        "rationale": (
            "The obligation is discharged at three ground inputs it MUST admit — "
            "both F2P shapes (credential-bearing URL with query, `user:pass@` and "
            "`user@`) and a schemeless P2P shape (default scheme applied) — by "
            "evaluation, then the frozen obligation is closed verbatim. Verifies, "
            "else the behavior is unsatisfiable at a normal input it must admit "
            "(analogue of PRECOND-TOO-STRONG). Nothing is assumed: the ground "
            "instances are `have`s inside the tactic body and the theorem "
            "statement is byte-identical. Ports nagini admiss-f2p-shaped-selfcall."),
    },
    {
        "id": "weak-drop-userinfo",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL, _IMPL_DROP_USERINFO),
        "refinement": (
            "This is the pre-fix behavior: assemble from the bare authority, "
            "never re-attaching a present userinfo. On the F2P URL "
            "'http://user:pass@example.com/path?query' the credentials are "
            "dropped, so the reconstruction returns "
            "'http://example.com/path?query' != expected. F2P FAIL => a faithful "
            "patch shaped this way does NOT resolve."),
        "rationale": (
            "REJECT from the sole clause `result = reassemble …`: for a present "
            "userinfo the spec re-attaches it as `userinfo@authority`, but the "
            "rival emits the bare authority; the two differ for any non-empty "
            "userinfo. Attacks the `auth` binder. If it verified => SPEC-TOO-WEAK "
            "on the userinfo clause — the very behavior the fix adds. Ports nagini "
            "partial-drop-credential-join."),
        "witness": _wit('(some "http")', '(some "user:pass")', '"example.com"',
                        '"/path"', '"query"', '""', '"http"'),
    },
    {
        "id": "weak-userinfo-sep",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL, _IMPL_USERINFO_SEP),
        "refinement": (
            "Joining the userinfo to the authority with ':' instead of '@' emits "
            "'http://user:pass:example.com/path?query' for the F2P URL != expected "
            "'...@...'. F2P FAIL => does NOT resolve."),
        "rationale": (
            "REJECT from `result = reassemble …`: the spec pins the userinfo join "
            "to '@', so `userinfo:authority` != `userinfo@authority` for a "
            "non-empty userinfo. Attacks the `auth` binder on the separator value. "
            "If it verified => SPEC-TOO-WEAK on the join character. Ports nagini "
            "partial-wrong-separator."),
        "witness": _wit('(some "https")', '(some "user:pass")', '"host.io"',
                        '"/p"', '"query"', '""', '"https"'),
    },
    {
        "id": "weak-drop-query",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL, _IMPL_DROP_QUERY),
        "refinement": (
            "Dropping the query slot emits "
            "'http://user:pass@example.com/path' (no '?query') for both F2P URLs "
            "(each carries '?query') != expected. F2P FAIL => does NOT resolve."),
        "rationale": (
            "REJECT from `result = reassemble …`: the round-trip appends '?query' "
            "for a non-empty query, so omitting it breaks the equality on every "
            "has-query input (including both F2P URLs). Attacks the `query` "
            "binder. If it verified => SPEC-TOO-WEAK on the query slot. Ports "
            "nagini partial-drop-query."),
        "witness": _wit('(some "http")', '(some "user:pass")', '"proxy.net"',
                        '"/a/b"', '"query"', '""', '"http"'),
    },
    {
        "id": "weak-drop-fragment",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL, _IMPL_DROP_FRAG),
        "refinement": (
            "Dropping the fragment slot strips '#frag' from any fragment-bearing "
            "location. The round-trip preserves the fragment, so the output "
            "diverges from the real post-patch behavior on every fragment-carrying "
            "input => does NOT faithfully implement the modeled function."),
        "rationale": (
            "REJECT from `result = reassemble …`: the round-trip appends '#frag' "
            "for a non-empty fragment, so omitting it breaks the equality on every "
            "has-fragment input. Attacks the `fragment` binder. If it verified => "
            "SPEC-TOO-WEAK on the fragment slot. Ports nagini partial-drop-fragment."),
        "witness": _wit('(some "http")', '(some "user:pass")', '"h.example"',
                        '"/x"', '"query"', '"frag"', '"http"'),
    },
    {
        "id": "weak-drop-path",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL, _IMPL_DROP_PATH),
        "refinement": (
            "Dropping the path slot strips '/path' from a location that carries "
            "one, so the F2P URL 'http://user:pass@example.com/path?query' loses "
            "its path and returns 'http://user:pass@example.com?query' != "
            "expected. F2P FAIL => does NOT resolve."),
        "rationale": (
            "REJECT from `result = reassemble …`: the round-trip carries the path "
            "into its slot, so emitting '' for a non-empty path breaks the "
            "equality on every has-path input. Attacks the `path` binder — a slot "
            "nagini modeled but no ported case moved, so a rival mishandling only "
            "the path would otherwise be invisible. If it verified => "
            "SPEC-TOO-WEAK on the path slot."),
        "witness": _wit('(some "ftp")', '(some "user:pass")', '"site.org"',
                        '"/path"', '"query"', '""', '"ftp"'),
    },
    {
        "id": "weak-uncond-userinfo-join",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL, _IMPL_UNCOND_JOIN),
        "refinement": (
            "Treating an ABSENT userinfo as the empty string and joining it "
            "anyway prepends a stray '@' to the authority on every location that "
            "carries no userinfo: 'example.com/path' reconstructs as "
            "'http://@example.com/path' rather than 'http://example.com/path', "
            "and likewise '//example.com/path' and 'example.com:80' (all three "
            "schemeless no-userinfo P2P locations). P2P FAIL => a faithful patch "
            "shaped this way does NOT resolve. Note it AGREES with the spec on "
            "both credential-bearing F2P inputs, so only the no-userinfo "
            "sub-domain exposes it — which is why the case is needed."),
        "rationale": (
            "REJECT from the sole clause `result = reassemble …`: for an absent "
            "userinfo the spec leaves the authority bare, but the rival emits "
            "'@' ++ authority. Attacks the `auth` binder at its `none` point — "
            "the sub-domain every other case holds fixed at `some \"user:pass\"`, "
            "so a rival mishandling only the no-userinfo case would otherwise be "
            "invisible. `auth.getD \"\"` is the faithful port of nagini's rival: "
            "it collapses `none` and `some \"\"` to one point, matching nagini's "
            "`creds == [] ∧ has_creds = False`. If it verified => SPEC-TOO-WEAK on "
            "the userinfo-absent sub-domain. Ports nagini "
            "nearmiss-creds-unconditional."),
        "witness": _wit('none', 'none', '"example.com"',
                        '"/path"', '""', '""', '"http"'),
    },
    {
        "id": "weak-scheme-default",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL, _IMPL_SCHEME_DEFAULT),
        "refinement": (
            "Emitting '' when no scheme was parsed instead of the supplied "
            "default drops the scheme on the schemeless P2P inputs: "
            "'example.com/path' would reconstruct as '://example.com/path' rather "
            "than 'http://example.com/path' != expected. P2P FAIL => does NOT "
            "resolve."),
        "rationale": (
            "REJECT from `result = reassemble …`: when scheme0 is absent the "
            "round-trip uses `newScheme`, but the rival uses '', which differ "
            "whenever `newScheme ≠ ''` (guaranteed by the precondition). Attacks "
            "the `scheme0`/`newScheme` binders — the scheme-default clause no "
            "other case reaches. If it verified => SPEC-TOO-WEAK on the scheme "
            "default."),
        "witness": _wit('none', 'none', '"example.com"',
                        '"/root"', '""', '""', '"http"'),
    },
]

AXIOM_TESTS = []
