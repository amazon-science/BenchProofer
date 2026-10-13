"""properties.py — G-PBT falsification battery for pytest-dev__pytest-5840 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes and
stamps with a verdict. Each SPEC case is a full ``Solution.lean`` variant that
shares the FROZEN spec byte-for-byte (region surgery: only text inside the
``-- impl-start`` / ``-- impl-end`` region, or inside the ``prove_correct``
tactic body, is changed — both of which the consumer spec view elides, so
``markers.same_spec`` holds and the ``prove_correct registerModule`` obligation
survives with a byte-identical statement) and swaps in a candidate
implementation; it is checked by the real verifier. ``expect:"verify"`` passes
iff (in scope AND verifies); ``expect:"reject"`` passes iff (in scope AND does
NOT verify AND its refutation ``witness`` discriminates: the witness must
ELABORATE against the rival and FAIL against the frozen solution).

DEFENDED SURFACE. One contracted method — a memoizing importer over a mutable
association-list cache plus a read-only location identity and a free
freshly-produced value:

  registerModule (mut registry : List (Key × Module)) (loc : Nat) (freshMod : Module)
      return (out : Module)
    ensures ∀ m, regLookup registryOld (probeKey loc) = some m →
              (out = m ∧ registry = registryOld)            -- (C1) HIT branch
    ensures regLookup registryOld (probeKey loc) = none →
              (out = freshMod ∧
               registry = registryOld ++ [(probeKey loc, freshMod)])  -- (C2) MISS branch
    ensures regLookup registry (probeKey loc) = some out    -- (C3) post-probe

A ``Key`` is a location together with a REPRESENTATION tag (``primary`` /
``secondary``): two keys answer the same lookup iff BOTH match. Every consumer
probes the cache under the location's ``primary`` key (``probeKey loc``). The
carrier is fully transparent (``Key`` and ``KeyRepr`` derive ``DecidableEq``,
``regLookup`` is a plain front-recursive ``def``), so every witness below closes
by ``decide`` — no conditioning on an opaque callee is needed, and no witness
binds any hypothesis (so the consistency probe is vacuous by construction).

THREE independent top-level clauses, each load-bearing and each attacked:
  (C1) on a HIT the returned module is the one already stored AND the cache is
       left EXACTLY as it was (the import runs at most once per location);
  (C2) on a MISS the fresh module is returned AND registered under the
       location's ``primary`` key;
  (C3) after the call, a subsequent probe under ``probeKey loc`` finds the
       returned module — the entry MUST be stored under the representation
       lookups use, never under a merely same-location alternative.

C3 is the load-bearing clause of the modeled change: the entry must be reachable
by the SAME key representation a later, independent probe recomputes. Storing
under the alternative representation (``secondary``) leaves an entry that denotes
the identical location yet is never found by ``probeKey`` — the exact defect the
issue describes (a cache write keyed by an object that a recomputed lookup key
does not match). The location string is identical across representations, so no
value-level equality of the location distinguishes them; only which
representation the entry is filed under does. That is the discriminator these
rivals exercise.

ADVERSARIAL READ of the sibling classes on this carrier:
  * FRAME-MUTATION (sibling's MANDATORY read-only-input write) — VACUOUS here.
    The sibling holds its input at a fractional heap permission an impl can
    illegally overwrite. Lean/Velvet are referentially transparent: ``loc`` and
    ``freshMod`` are immutable values (NOT ``mut`` binders), there is no heap and
    no aliasing, so there is no read-only field to overwrite and no substitute
    probe to build. The one ``mut`` binder (``registry``) is exactly the state
    the operation is SUPPOSED to write, and C1 already pins that it is left
    untouched on a hit (the ``registry = registryOld`` conjunct) — attacked by
    the hit-mutates rival below. Not fabricated (porting map: this class is
    vacuous here).
  * VALUE-LAUNDER (sibling's "build the recognised key but return a value-equal
    unrecognised copy") — RE-EXPRESSED. On this carrier there is no separate
    "value" to launder off the key: the discriminator IS the representation tag
    on the stored key. The faithful re-expression is the prepatch rival, which
    files the entry under ``secondary`` (identical location, wrong
    representation). It is refuted by C3.

WITNESS PLACEMENT. The spec is a ``method`` CONTRACT, not a bare predicate, so
each reject rival reaches it through Velvet's own tester machinery:
``registerModuleTester registry loc freshMod = false`` says the extracted
program's observable (the returned module and the mutated cache) violates the
method's postcondition at that concrete input. Checked in a file whose
``prove_correct`` block has been stripped, so no tactic script can mask the
verdict. The full postcondition — including the ``∀ m, …`` HIT clause — is made
decidable by the tester machinery (``prove_postcondition_decidable_for``), which
was confirmed to derive and kernel-reduce under ``decide`` here. Every reject
witness below was run against BOTH the rival (exit 0) and the frozen solution
(exit 1) with two real builds.

AXIOM lane: EMPTY. The two ways a location is turned into a cache key are modeled
DEEPLY by ``Key`` / ``KeyRepr`` / ``probeKey`` (a deep-model A-reference validated
against the real path objects by axiom_check.py / G-AX, not a consumed contract),
and the freshly-produced module is a directive-7 free input. The ``axioms``
region declares no ``axiom``; the gate ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "pytest-dev__pytest-5840"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchor. Lies wholly inside the single impl region (the
# ---- probe/hit-return/miss-register block) and is unique in Solution.lean
# ---- (both facts asserted at load by _swap). Anchoring on the whole block
# ---- keeps the surgery within the elided region. ----
_GOLD_IMPL = (
    "    let k : Key := probeKey loc\n"
    "    let cached := regLookup registry k\n"
    "    if cached.isSome then\n"
    "      return cached.getD freshMod\n"
    "    else\n"
    "      registry := registry ++ [(k, freshMod)]\n"
    "      return freshMod"
)

assert _GOLD_IMPL in _BASE, "frozen impl region drifted; update _GOLD_IMPL"

# ---- proof-body anchor. A `prove_correct` tactic body is elided from the
# ---- consumer spec view, so a case that introduces an in-region `assert` may
# ---- retune the tactic script without touching the spec statement or dropping
# ---- the obligation. Unique in the file. ----
_GOLD_PROOF = (
    "prove_correct registerModule by\n"
    "  loom_solve\n"
    "  simp_all [probeKey, regLookup_append_fresh]"
)

assert _GOLD_PROOF in _BASE, "frozen proof body drifted; update _GOLD_PROOF"

# ---- impl-start anchor for the in-region admissibility assert. ----
_IMPL_START = "    -- impl-start\n"

assert _IMPL_START in _BASE, "impl-start marker drifted"


def _impl(body):
    """Build a full Solution.lean variant by replacing the gold impl block."""
    return _swap(_BASE, _GOLD_IMPL, body)


# ---- witness preamble. Reaches the method contract through Velvet's tester
# ---- machinery; checked in a file whose `prove_correct` block is stripped.
# ---- `Key`/`KeyRepr` already derive `DecidableEq` and the postcondition
# ---- (including the `∀ m, …` HIT clause) is made decidable by
# ---- `prove_postcondition_decidable_for`, so every witness closes by `decide`.
# ---- No `axiom`/`sorry`/`native_decide`; the frozen solution rejects these
# ---- witnesses all the same. ----
def _tester(body):
    return (
        "extract_program_for registerModule\n"
        "prove_precondition_decidable_for registerModule\n"
        "prove_postcondition_decidable_for registerModule\n"
        "derive_tester_for registerModule\n\n" + body
    )


def _witness(call):
    return _tester(f"example : {call} = false := by\n  decide\n")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # impls that MUST verify, else SPEC-TOO-STRONG. Each keeps the byte-identical
    # three-clause obligation and only reshapes the executable surface; both
    # verify under the FROZEN proof script (the reshapes leave the same goals),
    # confirmed with real builds.
    # =====================================================================
    {
        "id": "pos-inline-lookup",
        "kind": "soundness",
        "expect": "verify",
        # Drop both intermediate locals (`k`, `cached`) and inline the probe key
        # and the lookup directly into the branch and the registration. Same
        # probe representation, same hit/miss decision, same registered entry.
        "module": _impl(
            "    if (regLookup registry (probeKey loc)).isSome then\n"
            "      return (regLookup registry (probeKey loc)).getD freshMod\n"
            "    else\n"
            "      registry := registry ++ [(probeKey loc, freshMod)]\n"
            "      return freshMod"),
        "rationale": "REORDER/INLINE reshape: dropping the `k`/`cached` locals and "
                     "inlining `probeKey loc` and the lookup yields an identical "
                     "hit/miss decision and an identical registered entry, so all "
                     "three clauses (hit returns stored + cache unchanged, miss "
                     "returns fresh + registers under the probe key, post-probe "
                     "finds the result) still discharge under the frozen script. A "
                     "faithful correct impl MUST verify, else SPEC-TOO-STRONG. "
                     "(Sibling: pos-control-inline-recognised.)",
    },
    {
        "id": "pos-drop-cached-local",
        "kind": "soundness",
        "expect": "verify",
        # Keep the `k` local but drop the `cached` local, inlining the lookup at
        # both the branch test and the hit return. A minimal reshape that still
        # names the probe key once.
        "module": _impl(
            "    let k : Key := probeKey loc\n"
            "    if (regLookup registry k).isSome then\n"
            "      return (regLookup registry k).getD freshMod\n"
            "    else\n"
            "      registry := registry ++ [(k, freshMod)]\n"
            "      return freshMod"),
        "rationale": "structurally different CORRECT reshape: keep the probe-key "
                     "local `k` but drop the `cached` local, inlining the lookup at "
                     "the test and the hit return. Observationally identical on "
                     "every input, so all three clauses still discharge under the "
                     "frozen script. MUST verify (else the spec is over-fitted to "
                     "the two-local gold shape => SPEC-TOO-STRONG). "
                     "(Sibling: pos-control-branch-reshape.)",
    },

    # =====================================================================
    # ADMISSIBILITY — the method has no `require` clause, so the "a normal input
    # satisfies the precondition" reading is vacuous. Re-aimed at the residual
    # admissibility risk: that the post-image is DEGENERATE at the F2P-shaped
    # point where a location has not yet been cached. This case discharges an
    # in-region assert (checked out-of-band; the FALSE variant leaves an unsolved
    # `decide` goal, so the assert is live) that at a fresh cache the location's
    # probe key is absent (so the MISS branch is genuinely reached) AND the probe
    # (`primary`) key differs from the same location's `secondary` key — i.e. the
    # representation distinction that C3 hinges on is real at the F2P point. The
    # surrounding impl is kept verbatim; the proof is retuned only to discharge
    # the extra assert VC (`decide`), leaving the method's own obligation intact.
    # =====================================================================
    {
        "id": "admiss-fresh-miss-distinct-repr",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _swap(
                _BASE, _IMPL_START,
                _IMPL_START +
                "    assert (with_name_prefix `adm\n"
                "      (regLookup ([] : List (Key × Module)) (probeKey 116) = none ∧\n"
                "       probeKey 116 ≠ (⟨116, KeyRepr.secondary⟩ : Key)))\n"),
            _GOLD_PROOF,
            "prove_correct registerModule by\n"
            "  loom_solve\n"
            "  · decide\n"
            "  all_goals simp_all [probeKey, regLookup_append_fresh]"),
        "rationale": "the post-image is non-degenerate at the F2P corner: at a "
                     "fresh cache the location's probe key is ABSENT (the MISS "
                     "branch is genuinely reachable, so the register-and-find-again "
                     "behaviour is exercised, not vacuously skipped), and the probe "
                     "(`primary`) key DIFFERS from the same location's `secondary` "
                     "key (the representation distinction C3 hinges on is real "
                     "here). The in-region assert must discharge (else the "
                     "obligation would be degenerate at the point that matters / "
                     "PRECOND-TOO-STRONG); the impl is kept verbatim so the "
                     "method's own `ensures` still discharges. The FALSE variant of "
                     "the assert leaves an unsolved `decide` goal, so it is live. "
                     "(Sibling: admissibility-f2p-shaped.)",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # concrete input and the refinement argument that its faithful real
    # counterpart would NOT resolve the failing test. Witnesses probe four
    # DISTINCT input tuples, varying `loc` over {3, 7, 2, 0}, the initial
    # `registry` over {empty, a primary-keyed hit, another primary-keyed hit,
    # empty}, and `freshMod` over {5, 5, 8, 5}. Each rival is a straight-line
    # (loop-free) body whose extracted tester reduces under `decide`; the frozen
    # solution rejects each witness (exit 1), the required discriminator.
    # =====================================================================
    {
        "id": "weak-store-under-alt-repr",
        "kind": "uniqueness",
        "expect": "reject",
        # THE central attack (= prepatch): probe and register under the
        # ALTERNATIVE representation (`secondary`) instead of the probe
        # representation. The stored entry denotes the identical location yet is
        # never found by a subsequent `probeKey` probe.
        "module": _impl(
            "    let k : Key := ⟨loc, KeyRepr.secondary⟩\n"
            "    let cached := regLookup registry k\n"
            "    if cached.isSome then\n"
            "      return cached.getD freshMod\n"
            "    else\n"
            "      registry := registry ++ [(k, freshMod)]\n"
            "      return freshMod"),
        "refinement": "this is the pre-change behaviour: the cache entry is filed "
                      "under a key object built by the alternative path-object "
                      "convention (the removed helper's key), which denotes the "
                      "identical location string but is a DISTINCT dictionary key "
                      "from the one every later probe recomputes. The failing test "
                      "stores a conftest, then asserts membership under an "
                      "independently-recomputed probe key: the recomputed key "
                      "MISSES the alternatively-keyed entry despite the identical "
                      "location, so the assertion fails. It would NOT resolve.",
        "rationale": "REJECT from clause (C3) `regLookup registry (probeKey loc) = "
                     "some out`: the entry is stored under `⟨loc, secondary⟩`, so a "
                     "post-call probe under `probeKey loc = ⟨loc, primary⟩` finds "
                     "nothing (`none ≠ some out`). Location equality alone (both "
                     "keys denote `loc`) does NOT satisfy the spec; the "
                     "representation must match. If it verified the spec would "
                     "admit the pre-image bug => SPEC-TOO-WEAK. Refuted at "
                     "registry=[], loc=3, freshMod=5 (fresh cache, MISS branch, "
                     "wrong-representation store). (Sibling: "
                     "uniqueness-unrecognised-convention-echo.)",
        "witness": _witness("registerModuleTester [] 3 5"),
    },
    {
        "id": "weak-hit-returns-fresh",
        "kind": "uniqueness",
        "expect": "reject",
        # On a HIT, return the freshly-produced module instead of the one already
        # stored. Isolates clause (C1) `out = m`: the cache is left unchanged and
        # the MISS branch is untouched, only the hit's returned value is wrong.
        "module": _impl(
            "    let k : Key := probeKey loc\n"
            "    let cached := regLookup registry k\n"
            "    if cached.isSome then\n"
            "      return freshMod\n"
            "    else\n"
            "      registry := registry ++ [(k, freshMod)]\n"
            "      return freshMod"),
        "refinement": "a faithful counterpart that re-imports and returns a FRESH "
                      "module on every call, ignoring the cached entry, defeats the "
                      "'import at most once per location' guarantee: a later "
                      "consumer that expects the SAME module object for the same "
                      "location instead receives a distinct re-import, so shared "
                      "module state / identity checks the cache is meant to "
                      "preserve break. It would NOT resolve.",
        "rationale": "REJECT from clause (C1) `∀ m, … → out = m`: on a hit the spec "
                     "pins the result to the module already stored, but the rival "
                     "returns `freshMod`, which differs whenever the stored module "
                     "differs from the fresh one. The cache is left unchanged and "
                     "the MISS branch is untouched, so the ONLY failing clause is "
                     "the hit's returned value. Refuted at "
                     "registry=[(⟨7,primary⟩,9)], loc=7, freshMod=5 (a primary hit "
                     "where stored 9 ≠ fresh 5).",
        "witness": _witness("registerModuleTester [(⟨7, KeyRepr.primary⟩, 9)] 7 5"),
    },
    {
        "id": "weak-hit-mutates-cache",
        "kind": "uniqueness",
        "expect": "reject",
        # On a HIT, return the stored module correctly BUT also append a duplicate
        # entry to the cache. Isolates clause (C1) `registry = registryOld`: the
        # returned value and the MISS branch are correct, only the "cache left
        # exactly as it was" conjunct is violated.
        "module": _impl(
            "    let k : Key := probeKey loc\n"
            "    let cached := regLookup registry k\n"
            "    if cached.isSome then\n"
            "      registry := registry ++ [(k, freshMod)]\n"
            "      return cached.getD freshMod\n"
            "    else\n"
            "      registry := registry ++ [(k, freshMod)]\n"
            "      return freshMod"),
        "refinement": "a faithful counterpart that re-registers the location on "
                      "every hit (re-running the import side effect and rewriting "
                      "the cache entry) re-imports a conftest that was already "
                      "loaded — exactly the double-import the memoization exists to "
                      "prevent — so a conftest whose top-level code must run once "
                      "runs again, and the tests that assert a single cached entry "
                      "per location observe a grown cache. It would NOT resolve.",
        "rationale": "REJECT from clause (C1) `… → registry = registryOld`: on a "
                     "hit the spec pins the cache to be left EXACTLY as it was, but "
                     "the rival appends a duplicate entry, so `registry ≠ "
                     "registryOld`. The returned value and the MISS branch are "
                     "correct, so the ONLY failing clause is the read-only-on-hit "
                     "frame conjunct (the referentially-transparent analogue of the "
                     "sibling's read-only-input discipline). Refuted at "
                     "registry=[(⟨2,primary⟩,4)], loc=2, freshMod=8 — a DIFFERENT "
                     "input point from the returns-fresh rival, moving loc, the "
                     "stored module, and freshMod. (Sibling: "
                     "frame-mutation-write-readonly-loc, re-expressed as the "
                     "cache-frame conjunct.)",
        "witness": _witness("registerModuleTester [(⟨2, KeyRepr.primary⟩, 4)] 2 8"),
    },
    {
        "id": "weak-partial-domain-alt-repr",
        "kind": "uniqueness",
        "expect": "reject",
        # PARTIAL-DOMAIN: use the correct probe representation on every location
        # EXCEPT one sub-domain (loc = 0), which falls to the alternative
        # representation. Correct almost everywhere; diverges only on the
        # singled-out sub-domain, so a spec pinning C3 only on part of the domain
        # would miss it.
        "module": _impl(
            "    let k : Key := if loc = 0 then ⟨loc, KeyRepr.secondary⟩ else probeKey loc\n"
            "    let cached := regLookup registry k\n"
            "    if cached.isSome then\n"
            "      return cached.getD freshMod\n"
            "    else\n"
            "      registry := registry ++ [(k, freshMod)]\n"
            "      return freshMod"),
        "refinement": "a faithful counterpart that keys the cache correctly for "
                      "most locations but files one sub-domain of locations under "
                      "the alternative path-object convention re-introduces the "
                      "lookup miss on exactly that sub-domain: a recomputed probe "
                      "key MISSES the alternatively-keyed entry there, so a conftest "
                      "in that sub-domain is re-imported and the membership "
                      "assertion fails for it. It would NOT resolve.",
        "rationale": "REJECT from clause (C3): the spec demands `regLookup registry "
                     "(probeKey loc) = some out` for EVERY location the domain "
                     "admits, but on the `loc = 0` sub-domain the entry is filed "
                     "under `secondary`, so the post-call `primary` probe misses. A "
                     "spec pinning the post-probe only on part of the domain would "
                     "MISS this => SPEC-TOO-WEAK. Refuted at registry=[], loc=0, "
                     "freshMod=5 — the singled-out sub-domain, a distinct input "
                     "point from the always-secondary rival (which is wrong "
                     "everywhere). (Sibling: partial-domain-empty-location-"
                     "unrecognised.)",
        "witness": _witness("registerModuleTester [] 0 5"),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 7 SPEC cases (2 soundness
# positives, 1 admissibility, 1 frame-mutation, 3 uniqueness rivals) plus a
# 2-probe AXIOM lane, contracting a PURE key-CONSTRUCTOR `conftest_dedup_key(loc)
# -> key` whose load-bearing clause is an unforgeable capability token
# `lookup_recognised(Result())` granted only by the recognised construction. This
# bundle models a WIDER surface: the full memoizing importer `registerModule`
# over a mutable cache, with three clauses (hit-branch, miss-branch, post-probe).
# The sibling's abstract "recognition token" P4 is re-expressed CONCRETELY here as
# the `primary` vs `secondary` key REPRESENTATION: storing under the alternative
# representation leaves an entry a later `probeKey` probe never finds, refuted by
# the transparent post-probe clause (C3). Every sibling case is accounted for.
#
#   sibling case (nagini)                    -> here
#   ---------------------------------------------------------------------
#   uniqueness-unrecognised-convention-echo   -> weak-store-under-alt-repr   PORTED (central)
#   partial-domain-empty-location-unrecognised-> weak-partial-domain-alt-repr PORTED
#   control-flow-effect-value-launder         -> weak-store-under-alt-repr   SUBSUMED (see below)
#   frame-mutation-write-readonly-loc         -> weak-hit-mutates-cache      RE-EXPRESSED
#   pos-control-inline-recognised             -> pos-inline-lookup           PORTED
#   pos-control-branch-reshape                -> pos-drop-cached-local       RE-EXPRESSED
#   admissibility-f2p-shaped                  -> admiss-fresh-miss-distinct-repr RE-AIMED
#   (new, no sibling)                         -> weak-hit-returns-fresh      ADDED
#   AXIOM_TESTS (2 probes)                    -> (none)                      DROPPED (G-AX)
#
# PORTED (weak-store-under-alt-repr): the sibling's central prepatch echo builds
#   the key under the unrecognised convention (identical location string, no
#   token). Here that is filing the entry under `⟨loc, secondary⟩`: identical
#   location, wrong representation, so the post-probe clause C3 refutes it. This
#   is the concrete form of the sibling's capability-token discriminator on this
#   carrier.
# SUBSUMED (control-flow-effect-value-launder): the sibling's launder rival builds
#   the recognised key but RETURNS a value-equal copy stripped of the token. On
#   this carrier the discriminator IS the representation tag on the stored key;
#   there is no separate "value" that can be equal while the token differs — a key
#   that denotes `loc` under `secondary` is `⟨loc, secondary⟩`, exactly the
#   prepatch rival. The two nagini rivals collapse to one distinct wrong impl
#   here, so laundering is not a separately-witnessable rival (its abstraction
#   coincides with the prepatch store). Not fabricated as a duplicate; reported.
# RE-EXPRESSED (weak-hit-mutates-cache): the sibling's MANDATORY frame rival writes
#   to the read-only INPUT `loc` (held at Acc(.,1/2)) and is rejected for
#   insufficient permission. This backend is referentially transparent: `loc` and
#   `freshMod` are immutable values (not `mut`), so there is no read-only input to
#   overwrite. The frame discipline survives as the `registry = registryOld`
#   conjunct of C1 — the cache must be left untouched on a hit — and is attacked by
#   a hit that appends a duplicate entry. This is the faithful carrier-narrowed
#   image of the frame class, not a fabricated substitute.
# PORTED / RE-EXPRESSED positives: pos-inline-lookup drops both intermediate locals
#   and inlines the probe/lookup (the sibling's inline-recognised); pos-drop-cached-
#   local drops only the `cached` local (the sibling's branch-reshape argument: a
#   structurally different faithful impl must verify). Both verify under the FROZEN
#   proof (the reshapes leave the same goals), confirmed with real builds.
# RE-AIMED (admiss-fresh-miss-distinct-repr): the sibling self-calls the constructor
#   on an F2P-shaped input to show the precondition admits it. There is no `require`
#   clause here, so that reading is vacuous. Re-aimed at proving the post-image is
#   non-degenerate at the F2P corner: at a fresh cache the MISS branch is genuinely
#   reachable AND the `primary`/`secondary` representations differ (so C3's
#   distinction is real). loom_solve + `decide` discharge the in-region assert; the
#   impl is kept verbatim so the method's own `ensures` still discharges.
# ADDED (weak-hit-returns-fresh): the hit-branch VALUE clause `out = m` has no
#   direct sibling counterpart (the sibling modeled only key CONSTRUCTION, not the
#   memoized lookup that returns the stored module). It is the other half of the
#   'import at most once' guarantee — returning the already-loaded module — so it
#   is attacked directly by a hit that returns the fresh module instead.
#
# BINDER / CLAUSE COVERAGE. All three independent top-level clauses are attacked:
#   (C1) by weak-hit-returns-fresh (`out = m`) and weak-hit-mutates-cache
#   (`registry = registryOld`); (C2)/(C3) by weak-store-under-alt-repr and
#   weak-partial-domain-alt-repr; and all three are defended by the two positive
#   controls and the admissibility case. The four reject witnesses probe four
#   DISTINCT input tuples (pts=4):
#     registry=[],                loc=3, freshMod=5   weak-store-under-alt-repr
#     registry=[(⟨7,primary⟩,9)], loc=7, freshMod=5   weak-hit-returns-fresh
#     registry=[(⟨2,primary⟩,4)], loc=2, freshMod=8   weak-hit-mutates-cache
#     registry=[],                loc=0, freshMod=5   weak-partial-domain-alt-repr
#   so the input binder `loc` is varied over {3,7,2,0}, the mutable `registry`
#   over {empty, a primary hit at 7, a primary hit at 2, empty}, and `freshMod`
#   over {5,5,8,5}. No binder is pinned across the battery. Each witness was SEEN
#   to discriminate: it ELABORATES against the rival (straight-line tester reduces
#   under `decide`) and FAILS against the frozen solution, the required two-build
#   check. No witness binds a hypothesis (all inputs are concrete literals over a
#   transparent carrier), so the consistency probe is vacuous by construction.
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job; this bundle declares no
#   axiom (the two key representations are a deep model / A-reference validated by
#   axiom_check.py, and the fresh module is a directive-7 free input), so there is
#   nothing to probe and the gate ignores AXIOM_TESTS regardless.
AXIOM_TESTS = []
