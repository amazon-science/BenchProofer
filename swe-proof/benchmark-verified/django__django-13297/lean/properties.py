# properties.py — G-PBT falsification battery for django__django-13297 (lean lane).
# PORTED from the nagini sibling's battery: the adversarial ARGUMENTS are carried
# over, the mechanics re-expressed against this backend's carrier. Each SPEC case is
# a FULL Solution.lean variant that shares the FROZEN spec byte-for-byte (only the
# impl region — and, where a positive reproves, the proof body — is edited), checked
# by variant_scope + the Lean verifier. Every expect="reject" case carries a
# refutation `witness`: a self-contained snippet that ELABORATES against the rival
# and FAILS on the frozen solution, so the rejection is attributable to the spec and
# not to a tactic script that merely stopped matching a reshaped impl.
#
# Defended surface (read from Solution.lean / mapping.md / instance.json):
#   wrapContextKwargs : List (String × UrlValue) → List (String × DeferredValue)
#   Each captured argument (a name paired with a value, the value carrying a type
#   identity `pytype` and content `data`) is turned into a deferred wrapper. The
#   single postcondition `problem_spec_wrapContextKwargs` is
#   `List.Forall₂ wrapsValue urlKwargs result`, which simultaneously pins:
#     (STRUCT) LENGTH + ORDER + positional pairing — the output has exactly one
#              wrapper per input, in the same order (Forall₂ over the two lists).
#     and, per matching position, `wrapsValue (inp) (out)` =
#       (C1) out.1 = inp.1               the pair's name is carried through
#       (C2) out.2.resolved = inp.2      the wrapper resolves to EXACTLY the value
#       (C3) out.2.noticeKey = inp.1     the notice is keyed to that same name
#       (C4) out.2.presentedType = inp.2.pytype   THE DISCRIMINATOR: the wrapper
#            presents the underlying value's OWN type identity, not a generic
#            placeholder type.
#   Every predicate here is a total, transparent structure/fold over the input:
#   no opaque callee, no answer-key oracle. Witnesses therefore need no
#   conditioning on the carrier — the loop reduces at any concrete literal input
#   and `simp` closes the disequality.
#
# CARRIER NOTE / relation to the nagini sibling: nagini modeled a SINGLE wrapping
# `wrap_kwarg_value(value) -> Wrapped` behind fractional read permission, whose
# postcondition split into P1 (fresh full-perm wrapper), P2 (`forced == value`,
# the SHARED value facet) and P3 (`binder_castable(Result(), value, type_of(value))`,
# the unforgeable directive-8 capability — the type-directed discriminator). This
# backend models the RICHER object directly and over a LIST: `DeferredValue` with
# `resolved`/`noticeKey`/`presentedType`, one per captured argument. The
# correspondence:
#   * nagini P2 (forces to `value`)              ↦ clause C2 (`resolved = inp.2`).
#   * nagini P3 (the type-directed capability)   ↦ clause C4 (`presentedType =
#     inp.2.pytype`) — the same "present the value's own type, not a generic
#     placeholder" facet, now modeled STRUCTURALLY instead of as an abstract
#     capability predicate. nagini's `weak-bare-wrapped` / `weak-opaque-wrapping`
#     (P1/P2 satisfied, P3 missing — the pre-patch generic-deferred-object) port
#     onto C4 as the `weak-generic-type` rival.
#   * nagini's `weak-launder-capability` (obtain P3 for a DIFFERENT wrapper/value
#     and launder it onto Result()) DOES port, as `weak-launder-type`. The
#     laundering does not need an abstract capability to be forgeable: over the
#     LIST carrier a wrapper can present a type identity that is genuinely
#     SOME captured argument's own type — just not its own. Reading one
#     argument's `pytype` and stamping it onto every wrapper is exactly the
#     cross-entry laundering nagini attacked, and it is a strict near-miss here
#     (indistinguishable from gold at length 1, refuted from length 2 on).
#   * nagini's `weak-partial-domain` (resolvable only on a sub-domain) ports onto
#     C4 as `weak-partial-type` (present the true type only when pytype matches a
#     fixed tag, else the generic placeholder).
#   * nagini's `weak-wrong-forced-value` (forces to value+1, breaks P2) ports onto
#     C2 as `weak-wrong-resolved`.
#   The LIST carrier ADDS surface nagini's single-value model had no counterpart
#   for: STRUCT (length/order/pairing) and the per-position name facets C1/C3.
#   These are attacked by `weak-drop-entries`, `weak-reverse-order`,
#   `weak-blank-pair-name`, and `weak-blank-noticekey`. The witnesses do NOT each
#   sit at a distinct input point, and they do not need to: what a witness must
#   do is refute ITS OWN rival at a point where that rival diverges from gold. The
#   single-argument point `[("k", ⟨1, "v"⟩)]` is where the four per-position facet
#   rivals (C1..C4) and the length rival all already diverge, so they share it.
#   The two rivals that are NOT refutable at length 1 — `weak-reverse-order` and
#   `weak-launder-type`, both of which agree with gold on every one-element input —
#   carry two-argument witnesses, and `weak-partial-type` carries a two-argument
#   witness spanning BOTH its handled and unhandled type sub-domains so the
#   near-miss is demonstrated rather than asserted.
#
# ADMISSIBILITY — nagini's `admiss-concrete-input`, ported as `admiss-ground-f2p-kwarg`.
#   An EARLIER pass recorded this lane N/A because the frozen obligation is an
#   unconditional `∀ (urlKwargs …), problem_spec … (implementation …)` with no
#   precondition hypothesis, so "nothing could be PRECOND-TOO-STRONG". That reason is
#   wrong, and it is the reason that removes one of the three directions this gate
#   exists to test. On a TOTAL carrier the analogue of PRECOND-TOO-STRONG is not a
#   rejected precondition: it is the obligation being UNSATISFIABLE at exactly an
#   F2P-shaped input — a spec provable only in the abstract, or vacuously, while
#   pinning nothing at the concrete point the failing test observes. That is directly
#   testable, and the case below tests it: it discharges the obligation BY EVALUATION
#   at a concrete F2P-shaped captured argument (a single route-captured slug whose
#   value carries its own type identity) as a `have`, and additionally EVALUATES the
#   modeled behaviour at that point down to the concrete wrapper it builds, before
#   closing the frozen obligation verbatim. MEASURED load-bearing rather than
#   decorative: the two `have`s verify against the frozen solution (exit 0) and FAIL
#   against all eight rivals in this battery (exit 1 each), so they pin the behaviour
#   at that input rather than restating something any impl satisfies.
#
# LANES THAT DO NOT PORT:
#   * FRAME / PERMISSION-MUTATION (nagini's fractional `Acc(...)` reasoning). Lean
#     is referentially transparent — no aliasing, no fractional permission — so a
#     "write back into a read-only input" rival is not expressible. nagini itself
#     already declared this class N/A on this instance (the `value: int` tag
#     carries no `Acc`), and it is doubly VACUOUS here.
#   * DIVERGENCE / NON-TERMINATION. On lean `implementation_wrapContextKwargs` is a
#     total Lean `def`; a non-terminating implementation cannot be written at all,
#     so the class is genuinely VACUOUS here (NOT the velvet-partial known-hole
#     disposition; the corpus-wide termination-semantics finding records that known velvet hole as
#     scoped to `partial` velvet bundles, with lean unaffected). The nagini
#     sibling carries no diverge case anyway.
#   * AXIOM_TESTS (nagini's `ax-sound-*` / `ax-contain-*`). The axiom lane is
#     G-AX's job; this gate ignores them. The wrapping is modeled DEEPLY (the
#     `DeferredValue` structure is built directly), so there is no consumed axiom
#     here anyway.
from pathlib import Path

INSTANCE = "django__django-13297"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# --- anchors -----------------------------------------------------------------------
# The full frozen impl body, lying ENTIRELY inside impl-start/impl-end and unique in
# the file. Every rival (and the positives) swap THIS block.
_IMPL = (
    "def implementation_wrapContextKwargs\n"
    "    (urlKwargs : List (String × UrlValue)) : List (String × DeferredValue) := Id.run do\n"
    "  let mut context := []\n"
    "  for (key, value) in urlKwargs do\n"
    "    -- Bind this argument into its own deferred wrapper. The wrapper exposes the\n"
    "    -- underlying value's own type identity, resolves to that value, and carries\n"
    "    -- the notice keyed to this argument's name.\n"
    "    let wrapper : DeferredValue := {\n"
    "      presentedType := value.pytype,\n"
    "      resolved := value,\n"
    "      noticeKey := key }\n"
    "    context := context ++ [(key, wrapper)]\n"
    "  return context"
)
assert _BASE.count(_IMPL) == 1, "impl anchor drifted from expected text"

# The frozen proof body (tactic lines inside proof-start/proof-end). Swapped only by
# the positives, whose different impl shapes need an (equally cheap, honest) reproof
# of the byte-identical theorem statement.
_PROOF = (
    "  intro urlKwargs\n"
    "  have helper : ∀ (xs : List (String × UrlValue)) (acc : List (String × DeferredValue)),\n"
    "      (forIn xs acc (fun x r => do\n"
    "          pure PUnit.unit\n"
    "          pure (ForInStep.yield (r ++ [(x.1, { presentedType := x.2.pytype, resolved := x.2, noticeKey := x.1 })]))) : Id _)\n"
    "        = acc ++ xs.map (fun x => (x.1, ({ presentedType := x.2.pytype, resolved := x.2, noticeKey := x.1 } : DeferredValue))) := by\n"
    "    intro xs\n"
    "    induction xs with\n"
    "    | nil => intro acc; simp; rfl\n"
    "    | cons a as ih =>\n"
    "      intro acc\n"
    "      rw [List.forIn_cons]\n"
    "      simp only [bind] at ih ⊢\n"
    "      simp [ih, List.append_assoc]\n"
    "  unfold implementation_wrapContextKwargs\n"
    "  simp only [Id.run]\n"
    "  rw [helper]\n"
    "  simp only [List.nil_append]\n"
    "  unfold problem_spec_wrapContextKwargs\n"
    "  induction urlKwargs with\n"
    "  | nil => simp\n"
    "  | cons a as ih =>\n"
    "    simp only [List.map_cons]\n"
    "    apply List.Forall₂.cons _ ih\n"
    "    refine ⟨rfl, rfl, rfl, rfl⟩"
)
assert _BASE.count(_PROOF) == 1, "proof anchor drifted from expected text"


# ===========================================================================
# POSITIVE CONTROLS (soundness) — must VERIFY (else SPEC-TOO-STRONG).
# Each is a structurally-DIFFERENT but behaviourally identical impl, with the
# theorem STATEMENT kept byte-identical and its proof reproven honestly inside
# proof-start/proof-end (no new axiom/lemma/sorry — just the cheapest tactic for
# the new shape).
# ===========================================================================

# pos-map-fold: replaces the imperative `Id.run do … for … mut` accumulator with a
# single pure `List.map` over the input. Semantics identical on every input (one
# wrapper per argument, same order, same fields). If it FAILS => SPEC-TOO-STRONG
# (the postcondition would be over-fit to the monadic accumulator shape rather than
# to the behaviour).
_POS_MAP = _swap(
    _swap(
        _BASE,
        _IMPL,
        "def implementation_wrapContextKwargs\n"
        "    (urlKwargs : List (String × UrlValue)) : List (String × DeferredValue) :=\n"
        "  urlKwargs.map (fun (key, value) =>\n"
        "    (key, { presentedType := value.pytype, resolved := value, noticeKey := key }))",
    ),
    _PROOF,
    "  intro urlKwargs\n"
    "  unfold problem_spec_wrapContextKwargs implementation_wrapContextKwargs\n"
    "  induction urlKwargs with\n"
    "  | nil => simp\n"
    "  | cons a as ih =>\n"
    "    simp only [List.map_cons]\n"
    "    apply List.Forall₂.cons _ ih\n"
    "    refine ⟨rfl, rfl, rfl, rfl⟩",
)

# pos-recursive-def: a structurally different CORRECT impl written as an explicit
# front-recursive `def` (pattern match on the list, no monad, no `mut`). Semantics
# identical. The theorem STATEMENT is byte-identical; its proof is reproven honestly
# by induction with `simp only [implementation_wrapContextKwargs]` unfolding the
# recursive equation. If it FAILS => SPEC-TOO-STRONG.
_POS_REC = _swap(
    _swap(
        _BASE,
        _IMPL,
        "def implementation_wrapContextKwargs :\n"
        "    List (String × UrlValue) → List (String × DeferredValue)\n"
        "  | [] => []\n"
        "  | (key, value) :: rest =>\n"
        "      (key, { presentedType := value.pytype, resolved := value, noticeKey := key })\n"
        "        :: implementation_wrapContextKwargs rest",
    ),
    _PROOF,
    "  intro urlKwargs\n"
    "  unfold problem_spec_wrapContextKwargs\n"
    "  induction urlKwargs with\n"
    "  | nil => simp [implementation_wrapContextKwargs]\n"
    "  | cons a as ih =>\n"
    "    obtain ⟨key, value⟩ := a\n"
    "    simp only [implementation_wrapContextKwargs]\n"
    "    apply List.Forall₂.cons _ ih\n"
    "    refine ⟨rfl, rfl, rfl, rfl⟩",
)


# ===========================================================================
# ADMISSIBILITY (PRECOND-TOO-STRONG direction) — must VERIFY.
# The obligation is unconditional, so the thing to test is that it is SATISFIABLE at a
# concrete F2P-shaped input, not merely provable in general. Both `have`s are added to
# the FRONT of the frozen tactic body, which is then retained verbatim as the closing
# step: the theorem STATEMENT is byte-identical, nothing new is declared, and no
# assumption token is used.
# ===========================================================================

# One captured route argument, whose value carries its own type identity — the shape
# the failing scenario reaches (a captured slug reused downstream by a type-directed
# consumer). Deliberately a NON-generic type tag (1, not the placeholder 0): at the
# placeholder tag the obligation would hold for a wrapper that presents the generic
# type too, so the ground point would not distinguish the behaviour under test.
_GROUND = '[("offer_slug", ⟨1, "offer-one"⟩)]'

# (a) the obligation itself, discharged by evaluation at that concrete point.
_ADMISS_GROUND = (
    f"  have _ground : problem_spec_wrapContextKwargs {_GROUND}\n"
    f"      (implementation_wrapContextKwargs {_GROUND}) := by\n"
    "    unfold problem_spec_wrapContextKwargs\n"
    "    simp only [implementation_wrapContextKwargs, Id.run, List.forIn_cons,\n"
    "      List.forIn_nil, bind, pure]\n"
    "    simp [List.forall₂_cons, wrapsValue]\n"
)

# (b) WHICH wrapper that input actually produces, pinned by evaluation. Without this
# the `have` in (a) could read the same way if the spec were satisfied for a reason
# unrelated to the type facet; here the presented type identity, the resolved value and
# the notice key are all evaluated to concrete literals.
_ADMISS_EVAL = (
    f"  have _eval : implementation_wrapContextKwargs {_GROUND}\n"
    "      = [(\"offer_slug\", (⟨1, ⟨1, \"offer-one\"⟩, \"offer_slug\"⟩ : DeferredValue))] := by\n"
    "    simp only [implementation_wrapContextKwargs, Id.run, List.forIn_cons,\n"
    "      List.forIn_nil, bind, pure, List.nil_append]\n"
)

_ADMISS = _swap(_BASE, _PROOF, _ADMISS_GROUND + _ADMISS_EVAL + _PROOF)


# ===========================================================================
# UNIQUENESS RIVALS — must be REJECTED (else SPEC-TOO-WEAK). Each shares the
# frozen spec exactly and edits only the impl region; the frozen proof body is left
# in place (it will not close for the reshaped impl, but the gate reads the witness —
# checked in a file with the obligation removed — not the rival's own build).
# ===========================================================================

# Helper building an impl whose per-argument wrapper uses the given field exprs.
def _riv_wrapper(ptype, resolved, notice):
    return _swap(
        _BASE,
        _IMPL,
        "def implementation_wrapContextKwargs\n"
        "    (urlKwargs : List (String × UrlValue)) : List (String × DeferredValue) := Id.run do\n"
        "  let mut context := []\n"
        "  for (key, value) in urlKwargs do\n"
        "    let wrapper : DeferredValue := {\n"
        f"      presentedType := {ptype},\n"
        f"      resolved := {resolved},\n"
        f"      noticeKey := {notice} }}\n"
        "    context := context ++ [(key, wrapper)]\n"
        "  return context",
    )


# weak-generic-type: THE central port of nagini's `weak-bare-wrapped` /
# `weak-opaque-wrapping`. Presents a fixed GENERIC placeholder type identity (0) for
# every argument instead of the value's own `pytype`. This is EXACTLY the pre-patch
# behaviour — a single generic deferred-object type shared by every wrapper.
# Attacks clause C4.
_RIV_GENERIC = _riv_wrapper("0", "value", "key")

# weak-partial-type: PARTIAL-DOMAIN port of nagini's `weak-partial-domain`. Presents
# the value's own type only when its type tag equals a fixed value (5), and the
# generic placeholder (0) otherwise. Correct on the pytype==5 sub-domain, WRONG on
# every other type. Attacks clause C4 on the sub-domain the fix must cover.
_RIV_PARTIAL = _riv_wrapper(
    "(if value.pytype = 5 then value.pytype else 0)", "value", "key")

# weak-wrong-resolved: port of nagini's `weak-wrong-forced-value`. Makes the RIGHT
# presented type (C4 holds) and right names, but the wrapper resolves to a FIXED
# default value ⟨0, ""⟩ instead of the captured value — so the value the consumer
# reads back is wrong. Attacks clause C2 (confirming the resolved-value facet is
# load-bearing, not just the type facet).
_RIV_WRONG_RESOLVED = _riv_wrapper("value.pytype", "⟨0, \"\"⟩", "key")

# weak-blank-noticekey: presents the right type and resolves correctly, but keys the
# emitted notice to the empty string instead of the argument's name. Attacks clause
# C3 (the notice-key facet — a per-position name binder the nagini single-value
# carrier had no counterpart for).
_RIV_BLANK_NOTICE = _riv_wrapper("value.pytype", "value", "\"\"")

# weak-blank-pair-name: the wrapper fields are all correct, but the entry is stored
# under the WRONG pair name (empty string) instead of the argument's key. Attacks
# clause C1 (the pair-position name / output keying — order-and-name preservation).
_RIV_BLANK_PAIR = _swap(
    _BASE,
    _IMPL,
    "def implementation_wrapContextKwargs\n"
    "    (urlKwargs : List (String × UrlValue)) : List (String × DeferredValue) := Id.run do\n"
    "  let mut context := []\n"
    "  for (key, value) in urlKwargs do\n"
    "    let wrapper : DeferredValue := {\n"
    "      presentedType := value.pytype,\n"
    "      resolved := value,\n"
    "      noticeKey := key }\n"
    "    context := context ++ [(\"\", wrapper)]\n"
    "  return context",
)

# weak-drop-entries: STRUCTURAL. Returns the empty list regardless of input — the
# cheapest non-doing impl. Every wrapper field is vacuously irrelevant; the LENGTH
# clause of Forall₂ refutes it on any non-empty input. Attacks STRUCT (length).
_RIV_DROP = _swap(
    _BASE,
    _IMPL,
    "def implementation_wrapContextKwargs\n"
    "    (urlKwargs : List (String × UrlValue)) : List (String × DeferredValue) := Id.run do\n"
    "  let context := []\n"
    "  return context",
)

# weak-launder-type: port of nagini's `weak-launder-capability`. Every wrapper
# presents a type identity BORROWED from the first captured argument instead of its
# own value's. The presented tag is therefore a REAL captured type — just the wrong
# argument's — so this is not "a placeholder" but genuine cross-entry laundering.
# Strictly stronger a near-miss than `weak-generic-type`: at length 1 it agrees
# with gold exactly (MEASURED: the positive `problem_spec … [("a", ⟨1,"x"⟩)]`
# elaborates against this rival, exit 0), so it is refutable only from length 2 on,
# where the second wrapper presents tag 1 while its value's own tag is 2.
_RIV_LAUNDER = _swap(
    _BASE,
    _IMPL,
    "def implementation_wrapContextKwargs\n"
    "    (urlKwargs : List (String × UrlValue)) : List (String × DeferredValue) := Id.run do\n"
    "  let borrowed : Nat := (urlKwargs.head?.map (fun p => p.2.pytype)).getD 0\n"
    "  let mut context := []\n"
    "  for (key, value) in urlKwargs do\n"
    "    let wrapper : DeferredValue := {\n"
    "      presentedType := borrowed,\n"
    "      resolved := value,\n"
    "      noticeKey := key }\n"
    "    context := context ++ [(key, wrapper)]\n"
    "  return context",
)

# weak-reverse-order: STRUCTURAL. Builds each wrapper correctly (all four field
# clauses hold element-wise) but accumulates in REVERSE order (prepend rather than
# append), so the positional pairing of Forall₂ is broken on any input with ≥2
# distinct arguments. Attacks STRUCT (order) — the order-preservation the spec pins.
_RIV_REVERSE = _swap(
    _BASE,
    _IMPL,
    "def implementation_wrapContextKwargs\n"
    "    (urlKwargs : List (String × UrlValue)) : List (String × DeferredValue) := Id.run do\n"
    "  let mut context := []\n"
    "  for (key, value) in urlKwargs do\n"
    "    let wrapper : DeferredValue := {\n"
    "      presentedType := value.pytype,\n"
    "      resolved := value,\n"
    "      noticeKey := key }\n"
    "    context := [(key, wrapper)] ++ context\n"
    "  return context",
)


def _wit(inp, note):
    """A refutation witness: `¬ problem_spec … (implementation … inp)` at a concrete
    literal input list `inp`. The `simp only [implementation_…, Id.run,
    List.forIn_cons, List.forIn_nil, bind, pure]` block fully reduces the `for`-loop
    accumulator to a concrete result, then `simp [List.forall₂_cons, wrapsValue]`
    decides the (dis)equality against the spec. Elaborates against a rival whose
    result diverges from the spec at `inp`, and FAILS on gold (which satisfies the
    spec at every input) — SEEN to discriminate both ways. Binds nothing (no
    hypotheses), so it is trivially consistent."""
    return (
        f"-- {note}\n"
        f"example : ¬ problem_spec_wrapContextKwargs {inp}\n"
        f"    (implementation_wrapContextKwargs {inp}) := by\n"
        f"  unfold problem_spec_wrapContextKwargs\n"
        f"  simp only [implementation_wrapContextKwargs, Id.run, List.forIn_cons,\n"
        f"    List.forIn_nil, bind, pure]\n"
        f"  simp [List.forall₂_cons, wrapsValue]"
    )


SPEC_TESTS = [
    # ---- positive controls (must VERIFY) ----
    {
        "id": "pos-map-fold",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_MAP,
        "rationale": (
            "structurally-different but CORRECT impl: the imperative `Id.run do … for "
            "… mut` accumulator is replaced by a single pure `List.map` over the input, "
            "producing one wrapper per argument in the same order with the same fields, "
            "so the output equals the frozen impl's on every input. The theorem "
            "STATEMENT is byte-identical and its proof is reproven honestly by induction "
            "(`List.map_cons` + `List.Forall₂.cons`) — no new axiom/lemma/sorry. If it "
            "FAILS => SPEC-TOO-STRONG (postcondition over-fit to the monadic impl shape)."
        ),
    },
    {
        "id": "pos-recursive-def",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_REC,
        "rationale": (
            "a structurally different CORRECT impl written as an explicit front-recursive "
            "`def` (pattern match on the list; no monad, no `mut`, no early return). "
            "Semantics identical on every input. The theorem STATEMENT is byte-identical; "
            "its proof is reproven honestly by induction unfolding the recursive equation "
            "— no new axiom/lemma/sorry, just the cheapest tactic for the new shape. If it "
            "FAILS => SPEC-TOO-STRONG (the postcondition would be bound to a particular "
            "executable shape rather than the behaviour)."
        ),
    },

    # ---- admissibility (must VERIFY) ----
    {
        "id": "admiss-ground-f2p-kwarg",
        "kind": "admissibility",
        "expect": "verify",
        "module": _ADMISS,
        "rationale": (
            "the frozen obligation is an unconditional `∀ urlKwargs`, so there is no "
            "precondition binder to attack directly; on a total carrier the analogue of "
            "PRECOND-TOO-STRONG is the obligation being UNSATISFIABLE at exactly an "
            "F2P-shaped input. This case tests that directly: it discharges "
            "`problem_spec_wrapContextKwargs` BY EVALUATION at a concrete F2P-shaped "
            "captured argument — one route-captured name whose value carries its own "
            "(non-generic) type identity — as a `have`, and a second `have` EVALUATES "
            "the modeled behaviour at that same point down to the concrete wrapper it "
            "builds, so the admission is pinned to the presented type identity, the "
            "resolved value and the notice key rather than holding for an unrelated "
            "reason. Only then is the frozen obligation closed verbatim. Must VERIFY; a "
            "failure of either `have` would mean the modeled behaviour is unsatisfiable "
            "at the very input the failing scenario observes. MEASURED load-bearing, not "
            "decorative: the identical pair of `have`s FAILS (exit 1) against every one "
            "of the eight rivals in this battery, so it is not a restatement any impl "
            "would satisfy. Nothing is assumed: no new declaration, no `sorry`/axiom, "
            "the theorem statement is byte-identical, and the frozen tactic body is "
            "retained unchanged as the closing step."
        ),
    },

    # ---- uniqueness rivals (must be REJECTED) ----
    {
        "id": "weak-generic-type",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_GENERIC,
        "refinement": (
            "presenting a single fixed generic placeholder type for every wrapper is "
            "EXACTLY the pre-patch behaviour — the wrapper exposes only a generic "
            "deferred-object type, not the underlying value's own type. Its faithful real "
            "patch is the UNCHANGED (buggy) repo. A type-directed downstream consumer "
            "(the DB parameter bind that inspects the value's type) is then handed "
            "something it cannot use and the filtering F2P test crashes with the "
            "regression error — a faithful patch of this shape does NOT resolve, so a "
            "verifying rival is a true verify-does-not-imply-resolve break."
        ),
        "rationale": (
            "REJECTED by clause C4 (`presentedType = inp.2.pytype`). The wrapper presents "
            "the generic tag 0 while the value's own type tag is 1, so the per-position "
            "`wrapsValue` fails. Witness probes an argument whose type tag (1) differs "
            "from the generic placeholder (0). If it VERIFIES => SPEC-TOO-WEAK (the "
            "type-facet the fix introduces is unpinned — the exact pre-patch bug)."
        ),
        # pytype 1 != generic 0: gold presents 1 (satisfies C4), rival presents 0.
        "witness": _wit('[("k", ⟨1, "v"⟩)]',
                        "argument with a concrete (non-generic) type tag: gold presents "
                        "the value's own type, generic-type rival presents the placeholder"),
    },
    {
        "id": "weak-partial-type",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_PARTIAL,
        "refinement": (
            "presenting the true type only for values whose type matches one fixed tag "
            "(and the generic placeholder for the rest) is what a patch that fixed only a "
            "sub-domain would do — e.g. handling one runtime type specially while leaving "
            "the others generically wrapped. The F2P value (a captured slug/string, not "
            "the specially-handled tag) is left with the generic type, the type-directed "
            "bind still crashes, and the test does NOT resolve. A genuine PARTIAL-DOMAIN "
            "break."
        ),
        "rationale": (
            "REJECTED by clause C4 on the off-sub-domain. For an argument whose type tag "
            "is not the fixed one (5) the rival presents 0 but the spec demands the value's "
            "own tag. Witness probes a type tag (1) OUTSIDE the handled sub-domain — a "
            "different input point from `weak-generic-type` (which is refuted everywhere, "
            "whereas this near-miss is correct at tag 5). If it VERIFIES => SPEC-TOO-WEAK "
            "on the unhandled type sub-domain."
        ),
        # Two arguments SPANNING the sub-domain boundary: tag 5 is the handled one
        # (rival is correct there) and tag 1 is not (rival falls to the generic 0).
        # The witness therefore DEMONSTRATES the partiality the rationale claims
        # rather than only refuting off-domain: gold satisfies the spec at both,
        # the rival only at the first.
        "witness": _wit('[("h", ⟨5, "x"⟩), ("m", ⟨1, "y"⟩)]',
                        "two arguments spanning the sub-domain boundary: the rival is "
                        "correct at the handled type tag and falls back to the "
                        "placeholder at the unhandled one; gold presents both own types"),
    },
    {
        "id": "weak-wrong-resolved",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_WRONG_RESOLVED,
        "refinement": (
            "a wrapper that resolves to a FIXED default value instead of the captured one "
            "does not faithfully stand in for the original URL kwarg — a consumer reading "
            "the value back through the context gets the wrong content, and the lookup "
            "keyed on the original value fails. A faithful patch of this shape does NOT "
            "resolve the F2P (the wrong value is fetched)."
        ),
        "rationale": (
            "REJECTED by clause C2 (`resolved = inp.2`). The wrapper presents the right "
            "type (C4 holds) and right names, but resolves to ⟨0, \"\"⟩ instead of the "
            "captured ⟨1, \"v\"⟩, so `wrapsValue` fails on the resolved facet. Supporting "
            "near-miss confirming C2 is load-bearing independently of C4. Witness probes "
            "a value distinct from the default. If it VERIFIES => SPEC-TOO-WEAK (the "
            "resolved-value clause is unpinned)."
        ),
        # value ⟨1,"v"⟩ != default ⟨0,"":  gold resolves to ⟨1,"v"⟩, rival to ⟨0,"⟩.
        "witness": _wit('[("k", ⟨1, "v"⟩)]',
                        "argument whose value differs from the fixed default: gold resolves "
                        "to the captured value, wrong-resolved rival to the default"),
    },
    {
        "id": "weak-blank-noticekey",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_BLANK_NOTICE,
        "refinement": (
            "keying the emitted deprecation notice to the empty string rather than the "
            "argument's name is what a patch that dropped the `key=key` binding would do — "
            "the one-time notice is no longer keyed to the argument it concerns. A "
            "faithful patch of this shape mis-attributes (or fails to key) the notice, so "
            "behaviour keyed on the argument name diverges. Does NOT resolve."
        ),
        "rationale": (
            "REJECTED by clause C3 (`noticeKey = inp.1`). The wrapper is otherwise correct "
            "but keys the notice to \"\" while the argument name is \"k\", so `wrapsValue` "
            "fails on the notice-key facet. Witness varies the KEY binder (non-empty name). "
            "If it VERIFIES => SPEC-TOO-WEAK (the notice-key facet is unpinned)."
        ),
        # key "k" != "": gold keys the notice to "k", rival to "".
        "witness": _wit('[("k", ⟨1, "v"⟩)]',
                        "argument with a non-empty name: gold keys the notice to that name, "
                        "blank-noticekey rival keys it to the empty string"),
    },
    {
        "id": "weak-blank-pair-name",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_BLANK_PAIR,
        "refinement": (
            "storing every wrapper under the empty pair name rather than the argument's "
            "key is what a patch that mislabelled the output entries would do — the "
            "context maps the wrong name to each deferred value, so a consumer looking up "
            "by the captured argument name finds nothing. Does NOT resolve."
        ),
        "rationale": (
            "REJECTED by clause C1 (`out.1 = inp.1`). Every wrapper field is correct but "
            "the entry is stored under \"\" instead of the argument's name \"k\", so the "
            "positional `wrapsValue` fails on the pair-name facet. Witness varies the KEY "
            "binder (non-empty name). If it VERIFIES => SPEC-TOO-WEAK (the output keying / "
            "name-preservation is unpinned)."
        ),
        # key "k" != "": gold stores under "k", rival under "".
        "witness": _wit('[("k", ⟨1, "v"⟩)]',
                        "argument with a non-empty name: gold stores the entry under that "
                        "name, blank-pair-name rival under the empty string"),
    },
    {
        "id": "weak-drop-entries",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_DROP,
        "refinement": (
            "returning no entries at all is what a patch that skipped the wrapping loop "
            "would do — the URL kwargs never reach the template context. Every context "
            "lookup on a captured argument then fails, so the F2P test (which fetches by a "
            "captured argument) does NOT resolve."
        ),
        "rationale": (
            "REJECTED by the STRUCT (length) clause of `List.Forall₂`. The output is empty "
            "while the input has one argument, so the two lists cannot be related "
            "positionally regardless of any per-wrapper field. Witness probes a single "
            "non-empty input (length 1 vs 0). If it VERIFIES => SPEC-TOO-WEAK (the "
            "one-wrapper-per-argument length guarantee is unpinned)."
        ),
        # length 1 input vs empty output: gold has length 1, rival length 0.
        "witness": _wit('[("k", ⟨1, "v"⟩)]',
                        "non-empty input: gold emits one wrapper per argument, "
                        "drop-entries rival emits none"),
    },
    {
        "id": "weak-launder-type",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_LAUNDER,
        "refinement": (
            "presenting every wrapper with a type identity borrowed from the FIRST "
            "captured argument is what a patch that hoisted the type lookup out of the "
            "per-argument loop would do — one type is computed once and reused for every "
            "wrapper. Whenever the captured arguments are not all of the same type (the "
            "F2P route captures a value whose type differs from a sibling argument's), a "
            "type-directed consumer is handed a wrapper advertising a type the underlying "
            "value does not have, and the operation fails just as it does pre-patch. Does "
            "NOT resolve for inputs with ≥2 differently-typed arguments."
        ),
        "rationale": (
            "REJECTED by clause C4 at the SECOND position: the rival presents the borrowed "
            "tag 1 while that value's own tag is 2. Distinct from `weak-generic-type` in "
            "the way that matters — the presented tag is a genuine captured type rather "
            "than a placeholder, so the rival is INDISTINGUISHABLE from gold on every "
            "one-element input (measured: the spec's positive elaborates against it at "
            "length 1) and is refutable only from length 2 on. That makes it the strictly "
            "tighter near-miss on C4, and it is the lane nagini attacked as capability "
            "laundering. If it VERIFIES => SPEC-TOO-WEAK (C4 would pin only that the "
            "presented type is SOME captured argument's type, not this one's)."
        ),
        # two differently-typed args: gold presents 1 then 2; rival presents 1 twice.
        "witness": _wit('[("a", ⟨1, "x"⟩), ("b", ⟨2, "y"⟩)]',
                        "two arguments of different types: gold presents each value's own "
                        "type, launder rival reuses the first argument's type for both"),
    },
    {
        "id": "weak-reverse-order",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_REVERSE,
        "refinement": (
            "building each wrapper correctly but emitting them in reverse order is what a "
            "patch that prepended (rather than appended) to the accumulator would do. The "
            "captured-argument order — which the spec preserves exactly — is inverted, so "
            "a consumer relying on positional/ordered context sees the arguments "
            "mismatched. Does NOT resolve for inputs with ≥2 distinct arguments."
        ),
        "rationale": (
            "REJECTED by the STRUCT (order/pairing) clause of `List.Forall₂`. Each element "
            "satisfies `wrapsValue`, but at position 0 the rival pairs the SECOND input's "
            "wrapper against the FIRST input, so the positional relation fails. Witness "
            "probes a TWO-argument input with distinct names/types/values — a distinct, "
            "longer input point from every other rival (which are refuted at length 1), "
            "exercising the list-shape binder. If it VERIFIES => SPEC-TOO-WEAK (order "
            "preservation is unpinned)."
        ),
        # two distinct args: gold keeps [a,b] order, reverse rival yields [b,a].
        "witness": _wit('[("a", ⟨1, "x"⟩), ("b", ⟨2, "y"⟩)]',
                        "two distinct arguments: gold preserves their order, "
                        "reverse-order rival inverts it"),
    },
]


# No @ContractOnly axioms and no opaque callees: the deferred-wrapping behaviour
# (the DeferredValue structure, its resolved value, notice key, and presented type)
# is modeled DEEPLY over transparent carriers, so the axiom lane is vacuous here and
# belongs to G-AX regardless.
AXIOM_TESTS = []
