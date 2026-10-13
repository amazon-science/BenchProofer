"""properties.py — G-PBT falsification battery for django__django-14855 (lean).

NOT a Lean file; a record of adversarial cases the G-PBT gate executes and
stamps a verdict onto. Each SPEC case is a full ``Solution.lean`` variant that
shares the FROZEN spec byte-for-byte (region surgery: only text inside the
``-- impl-start`` / ``-- impl-end`` region — and, for a positive that
legitimately re-proves, inside the ``-- proof-start`` / ``-- proof-end`` region —
is changed, so ``markers.same_spec`` holds and the
``theorem correct_getAdminUrl`` STATEMENT stays byte-identical).
``expect:"verify"`` passes iff (in scope AND the file elaborates with the
obligation closed, no ``sorry``/``admit``/``native_decide`` and no new
``axiom``/``theorem``); ``expect:"reject"`` passes iff (in scope AND it does NOT
verify AND the case's refutation ``witness`` holds of the rival while FAILING on
the frozen solution).

DEFENDED SURFACE (one modeled behavior; a single spec predicate, one top-level
equality clause). Producing the display markup for a reference to a related
record on an administrative detail page:

  problem_spec_getAdminUrl
    (resolveUrl : String → String → Option String → Option String)
    (formatLink : String → String → String)
    (appLabel modelName arg siteName remoteObjStr : String) (result : String)
    :=
    let urlName := "admin:" ++ appLabel ++ "_" ++ modelName ++ "_change"
    result = match resolveUrl urlName arg (some siteName) with
             | some url => formatLink url remoteObjStr
             | none     => remoteObjStr

The two downstream operations are UNIVERSALLY-QUANTIFIED function parameters —
``resolveUrl`` (the URL-resolution step; ``none`` models "no route produced")
and ``formatLink`` (the link-formatting step). The single equality clause pins
FOUR things to the inputs at once (spec_guide directive 5, the referential-
transparency analogue of frame discipline):

  * the route name is exactly ``"admin:" ++ appLabel ++ "_" ++ modelName ++
    "_change"`` — pinned to ``appLabel`` and ``modelName``;
  * the resolution step is invoked with that route name, ``arg``, and — the
    LOAD-BEARING fact the fix installs — the currently-effective deployment
    identifier ``some siteName``, NOT a missing one (``none``);
  * on a produced URL the result is ``formatLink url remoteObjStr`` (that
    argument order, that display text);
  * otherwise the result is exactly ``remoteObjStr``.

There is no opaque answer key to echo: the result is grounded entirely in the
inputs and the two quantified callees (directive 8). Because the callees are
quantified rather than ``opaque``, a witness can INSTANTIATE them with concrete
computable lambdas, so every refutation ``decide``s at literal inputs — no need
to condition on any carrier term.

BINDER STRUCTURE (read before judging binder coverage). The equality depends on
every input binder, and the reject witnesses move each one:

  * ``siteName`` — the deployment identifier. THE load-bearing binder: the fix
    is solely that ``some siteName`` reaches the resolver rather than ``none``.
    Attacked by ``omit-site`` (passes ``none``) and ``default-site`` (passes a
    constant deployment id), the two faithful ports of the nagini partial-domain
    rivals.
  * ``appLabel`` / ``modelName`` — the route-name components. Attacked by
    ``swap-route`` (transposes them, so the assembled name is wrong).
  * ``arg`` — the encoded identifier threaded to the resolver. Attacked by
    ``drop-arg`` (passes ``""``).
  * ``remoteObjStr`` — the record's display text. Attacked by ``drop-fallback``
    (the ``none`` arm returns ``""`` instead of it) and used by
    ``swap-link-args`` (which transposes the two ``formatLink`` arguments).
  * ``resolveUrl`` / ``formatLink`` — the two quantified callees; every witness
    instantiates them, and the instantiations vary across the reject set.

ADVERSARIAL READ of the nagini classes on this carrier:

  * ADMISSIBILITY — RE-EXPRESSED as ``admiss-ground-nondefault-deployment``. The
    frozen obligation is an unguarded ``∀`` with no precondition binder, but that
    does NOT make the lane vacuous: on a total carrier the analogue of
    PRECOND-TOO-STRONG is the obligation being UNSATISFIABLE at exactly an
    F2P-shaped input, and that case discharges the spec predicate by evaluation at
    such a point before closing the frozen obligation verbatim.

  * FRAME / PERMISSION MUTATION — VACUOUS. The nagini sibling holds ``names`` and
    ``prefixes`` at half-permission (``Acc(list_pred(.),1/2)``) and makes its two
    MANDATORY frame-mutation rivals WRITE back into them. Lean is referentially
    transparent: every input is an immutable ``String``/function value with no
    heap footprint, no ``mut`` binder and no aliasing — there is no read-only
    input to overwrite and no substitute probe. NOT fabricated (per the porting
    map, this class is vacuous here); see the accounting block.

  * PARTIAL-DOMAIN (the nagini central attack: the link points to the WRONG
    deployment) — PORTED as ``omit-site`` (the literal pre-patch: the resolver is
    not told the current deployment, i.e. ``none``) and ``default-site`` (the
    resolver is told a CONSTANT/default deployment id instead of the current
    one). Both make the resolution ignore ``siteName``.

  * UNGROUNDED-ORACLE ECHO — N/A: the result is grounded in the inputs and the
    two quantified callees, not in an axiomatized oracle; the ``axioms`` region
    declares no ``opaque``/``axiom``.

  * AXIOM lane — DROPPED. That lane is G-AX's job; this bundle declares no axiom
    (``meta.json`` ``axioms == []``; the resolver and formatter are quantified
    parameters, recorded only as A-references documenting the G-CONF binding to
    the real callees), so there is nothing to probe. ``AXIOM_TESTS`` is empty.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen proof (``cases … <;> rfl``) is tuned to
the frozen ``match … (some siteName)`` shape — so a rejection alone attributes
nothing to the spec. Every ``expect="reject"`` case therefore carries a Lean
snippet proving the rival CONTRADICTS the spec at one concrete input, with the
two callees instantiated as concrete lambdas. Each was checked with two real
``lake env lean`` builds to ELABORATE against its rival and to FAIL against the
frozen solution (so it discriminates rather than asserting a tautology). Across
the six reject witnesses ``appLabel``/``modelName``/``arg``/``siteName``/
``remoteObjStr`` and the two callee instantiations all take distinct values, so
the battery probes six DISTINCT input points (pts=6).
"""
from pathlib import Path

INSTANCE = "django__django-14855"
BACKEND = "lean"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- region anchors (each unique inside Solution.lean; verified at load) ----
# The full frozen impl def (lies wholly inside `-- impl-start`/`-- impl-end`).
# Every impl reshape lands entirely inside that region.
_IMPL = (
    "def implementation_getAdminUrl\n"
    "    (resolveUrl : String → String → Option String → Option String)\n"
    "    (formatLink : String → String → String)\n"
    "    (appLabel modelName arg siteName remoteObjStr : String) : String := Id.run do\n"
    "  -- Assemble the route name for the related model's change view.\n"
    '  let urlName := "admin:" ++ appLabel ++ "_" ++ modelName ++ "_change"\n'
    "  -- Resolve the URL, telling the resolver the currently-effective deployment\n"
    "  -- identifier; frame the outcome as a link, or fall back to plain display text.\n"
    "  match resolveUrl urlName arg (some siteName) with\n"
    "  | some url => return formatLink url remoteObjStr\n"
    "  | none => return remoteObjStr"
)

# The frozen tactic body (lies wholly inside `-- proof-start`/`-- proof-end`).
# Only a positive that legitimately re-proves touches this; the reject rivals
# leave it frozen (they are judged by their witness, not by whether this script
# happens to break).
_PROOF = (
    "  intro resolveUrl formatLink appLabel modelName arg siteName remoteObjStr\n"
    "  unfold problem_spec_getAdminUrl implementation_getAdminUrl\n"
    "  simp only [Id.run]\n"
    "  cases resolveUrl (\"admin:\" ++ appLabel ++ \"_\" ++ modelName ++ \"_change\") arg (some siteName) <;>\n"
    "    rfl"
)

assert _BASE.count(_IMPL) == 1, "impl region drifted from expected text"
assert _BASE.count(_PROOF) == 1, "proof region drifted from expected text"


def _with_impl(new_impl: str) -> str:
    """Solution.lean with ONLY the impl body replaced (spec + proof view intact)."""
    return _swap(_BASE, _IMPL, new_impl)


def _with_impl_proof(new_impl: str, new_proof: str) -> str:
    """Solution.lean with the impl AND the proof body replaced (spec view intact)."""
    return _swap(_with_impl(new_impl), _PROOF, new_proof)


def _with_proof(new_proof: str) -> str:
    """Solution.lean with ONLY the proof body replaced (impl + spec view intact).

    For the admissibility positive: the impl stays the FROZEN one byte-for-byte,
    and the tactic body gains ground `have`s before closing the frozen obligation
    verbatim. The `theorem` STATEMENT is untouched, so `variant_scope` holds.
    """
    return _swap(_BASE, _PROOF, new_proof)


# ---- the admissibility ground instance. A concrete NAMESPACED resolver: told a
# ---- deployment identifier it mounts the route under THAT deployment's prefix,
# ---- told none it falls back to the default prefix. This is the shape under
# ---- which the two deployments are observably different, i.e. the F2P shape. ----
_ADM_RESOLVE = (
    "fun name a s => match s with\n"
    '          | some dep => some ("/" ++ dep ++ "/" ++ name ++ "/" ++ a)\n'
    '          | none => some ("/default/" ++ name ++ "/" ++ a)'
)
_ADM_FMT = 'fun u t => "<a href=\\"" ++ u ++ "\\">" ++ t ++ "</a>"'
_ADM_ARGS = '"grp" "rec" "7" "otherdep" "Display"'
# What that resolver + formatter must yield at those inputs: the markup whose
# href sits under the CURRENTLY-EFFECTIVE deployment's prefix (`/otherdep/...`),
# not the default one (`/default/...`).
_ADM_VALUE = '"<a href=\\"/otherdep/admin:grp_rec_change/7\\">Display</a>"'


# ---- witness scaffold. The spec is a bare predicate over two quantified
# ---- callees, so a witness instantiates them with concrete lambdas and states
# ---- `¬ problem_spec_getAdminUrl <resolve> <fmt> a m arg s r
# ---- (implementation_getAdminUrl <resolve> <fmt> a m arg s r)` at ground String
# ---- literals. Checked in a file whose frozen obligation is elided by the gate,
# ---- so no tactic script can mask the verdict; `decide` settles the String
# ---- (in)equality after unfolding. Against gold the same `decide` faces
# ---- `x = x` and fails, so the witness is a real discriminator. ----
def _witness(resolve: str, fmt: str, a: str, m: str, arg: str, s: str, r: str) -> str:
    return (
        "example : ¬ problem_spec_getAdminUrl\n"
        f"    ({resolve}) ({fmt})\n"
        f'    "{a}" "{m}" "{arg}" "{s}" "{r}"\n'
        "    (implementation_getAdminUrl\n"
        f"      ({resolve}) ({fmt})\n"
        f'      "{a}" "{m}" "{arg}" "{s}" "{r}") := by\n'
        "  unfold problem_spec_getAdminUrl implementation_getAdminUrl\n"
        "  decide\n"
    )


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # implementations that MUST verify, else SPEC-TOO-STRONG. Each keeps the
    # `theorem correct_getAdminUrl` statement byte-identical.
    # =====================================================================
    {
        "id": "pos-direct-forward",
        "kind": "soundness",
        "expect": "verify",
        # Functional reshape: drop the `Id.run do` scaffold and the intermediate
        # `return`s, forming the match expression directly. Definitionally
        # identical (still resolves with `some siteName`), so the proof is retuned
        # to the collapsed shape (`cases … <;> rfl`, no `simp only [Id.run]`);
        # verified with a real build. No new axiom/lemma; statement unchanged.
        "module": _with_impl_proof(
            "def implementation_getAdminUrl\n"
            "    (resolveUrl : String → String → Option String → Option String)\n"
            "    (formatLink : String → String → String)\n"
            "    (appLabel modelName arg siteName remoteObjStr : String) : String :=\n"
            '  let urlName := "admin:" ++ appLabel ++ "_" ++ modelName ++ "_change"\n'
            "  match resolveUrl urlName arg (some siteName) with\n"
            "  | some url => formatLink url remoteObjStr\n"
            "  | none => remoteObjStr",
            "  intro resolveUrl formatLink appLabel modelName arg siteName remoteObjStr\n"
            "  unfold problem_spec_getAdminUrl implementation_getAdminUrl\n"
            "  cases resolveUrl (\"admin:\" ++ appLabel ++ \"_\" ++ modelName ++ \"_change\") arg (some siteName) <;>\n"
            "    rfl"),
        "rationale": "correct reshape of the mutable-do implementation into a "
                     "direct match expression; it computes the same value on "
                     "every input (still passing `some siteName` to the resolver), "
                     "so it must satisfy the equality clause — else "
                     "SPEC-TOO-STRONG. Proof retuned to the collapsed shape "
                     "(cases <;> rfl); no new axiom/lemma, statement unchanged.",
    },
    {
        "id": "pos-let-scrutinee",
        "kind": "soundness",
        "expect": "verify",
        # Structurally different CORRECT reshape: bind the resolution result to a
        # local `let` and match on that local, rather than matching the call
        # in-place. Behaviourally identical (same `some siteName` resolution, same
        # link/fallback framing); the frozen proof still closes because the local
        # is definitionally the call. Only the impl region changes; the theorem
        # STATEMENT and the proof body are byte-identical to frozen.
        "module": _with_impl(
            "def implementation_getAdminUrl\n"
            "    (resolveUrl : String → String → Option String → Option String)\n"
            "    (formatLink : String → String → String)\n"
            "    (appLabel modelName arg siteName remoteObjStr : String) : String := Id.run do\n"
            '  let urlName := "admin:" ++ appLabel ++ "_" ++ modelName ++ "_change"\n'
            "  let resolved := resolveUrl urlName arg (some siteName)\n"
            "  match resolved with\n"
            "  | some url => return formatLink url remoteObjStr\n"
            "  | none => return remoteObjStr"),
        "rationale": "structurally different CORRECT reshape: the resolution "
                     "result is bound to an intermediate `let` and matched via "
                     "that local instead of in-place. The local is definitionally "
                     "the call, so the value (and the `some siteName` argument) is "
                     "unchanged and the equality clause holds — else "
                     "SPEC-TOO-STRONG. The frozen proof still closes (verified "
                     "with a real build); no proof authoring, no assumption.",
    },

    # =====================================================================
    # ADMISSIBILITY / PRECOND-TOO-STRONG — the modeled behavior must be
    # SATISFIABLE at an F2P-shaped input, not merely satisfiable in principle.
    # =====================================================================
    {
        "id": "admiss-ground-nondefault-deployment",
        "kind": "admissibility",
        "expect": "verify",
        # The frozen obligation is an unguarded `∀` (no precondition binder), so
        # the analogue of PRECOND-TOO-STRONG on this total carrier is the
        # obligation being UNSATISFIABLE at exactly an F2P-shaped input. This
        # case discharges it there BY EVALUATION (`decide`), as two `have`s, and
        # only then closes the frozen obligation verbatim. The impl region is the
        # FROZEN one byte-for-byte; nothing is assumed (no new declaration, no
        # axiom, statement byte-identical) — the `have`s live inside the existing
        # tactic body. Ports the nagini sibling's `admiss-reads`.
        "module": _with_proof(
            "  -- The modeled behavior is satisfiable at an F2P-shaped input: a\n"
            "  -- reference rendered while a NON-DEFAULT deployment is in effect,\n"
            "  -- against a resolver that mounts each deployment under its own\n"
            "  -- prefix (so the two deployments are observably different here).\n"
            "  have admissible_at_nondefault_deployment :\n"
            "      problem_spec_getAdminUrl\n"
            f"        ({_ADM_RESOLVE})\n"
            f"        ({_ADM_FMT})\n"
            f"        {_ADM_ARGS}\n"
            "        (implementation_getAdminUrl\n"
            f"          ({_ADM_RESOLVE})\n"
            f"          ({_ADM_FMT})\n"
            f"          {_ADM_ARGS}) := by\n"
            "    unfold problem_spec_getAdminUrl implementation_getAdminUrl\n"
            "    decide\n"
            "  -- and the admitted value is the markup whose href sits under the\n"
            "  -- CURRENTLY-EFFECTIVE deployment's prefix rather than the default\n"
            "  -- one. Evaluating it pins the admission to the intended outcome,\n"
            "  -- so the `have` above cannot be discharged by an unspecified\n"
            "  -- branch that happens to satisfy the equality.\n"
            "  have admitted_value :\n"
            "      implementation_getAdminUrl\n"
            f"        ({_ADM_RESOLVE})\n"
            f"        ({_ADM_FMT})\n"
            f"        {_ADM_ARGS}\n"
            f"        = {_ADM_VALUE} := by\n"
            "    unfold implementation_getAdminUrl\n"
            "    decide\n"
            + _PROOF),
        "rationale": "the frozen obligation carries NO precondition hypothesis "
                     "(the `∀` is unguarded), so the analogue of "
                     "PRECOND-TOO-STRONG on this total carrier is the obligation "
                     "being unsatisfiable at exactly an F2P-shaped input. This "
                     "case tests that directly: it discharges "
                     "`problem_spec_getAdminUrl` BY EVALUATION (`decide`) at a "
                     "ground point where a NON-DEFAULT deployment is in effect "
                     "and the resolver mounts each deployment under its own "
                     "prefix — the configuration under which the two deployments "
                     "are observably distinct — as a `have`, and a second `have` "
                     "EVALUATES the outcome to the concrete markup whose href "
                     "carries that non-default deployment's prefix. Only then is "
                     "the frozen obligation closed verbatim. So the equality "
                     "clause is shown SATISFIABLE, and satisfiable at the "
                     "intended outcome, at the very input shape the failing test "
                     "observes — not merely satisfiable somewhere. Must verify; "
                     "if it does not, the modeled behavior is contradictory at a "
                     "normal input. Nothing is assumed: the impl region is the "
                     "frozen one byte-for-byte, no new declaration, statement "
                     "byte-identical.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # concrete input and the refinement argument for why its faithful real
    # counterpart would NOT resolve the F2P. The six witnesses probe six DISTINCT
    # input points; across them every input binder is varied.
    # =====================================================================
    {
        "id": "omit-site",
        "kind": "uniqueness",
        "expect": "reject",
        # The literal pre-patch: the resolver is NOT told the currently-effective
        # deployment identifier (it receives `none`). This is the bug the fix
        # removes.
        "module": _with_impl(
            "def implementation_getAdminUrl\n"
            "    (resolveUrl : String → String → Option String → Option String)\n"
            "    (formatLink : String → String → String)\n"
            "    (appLabel modelName arg siteName remoteObjStr : String) : String := Id.run do\n"
            '  let urlName := "admin:" ++ appLabel ++ "_" ++ modelName ++ "_change"\n'
            "  match resolveUrl urlName arg none with\n"
            "  | some url => return formatLink url remoteObjStr\n"
            "  | none => return remoteObjStr"),
        "refinement": "this IS the pre-patch behaviour: the resolution step is "
                      "invoked WITHOUT the currently-effective deployment "
                      "identifier. Its faithful real counterpart is the unchanged "
                      "repo line that resolves the link without threading the "
                      "current deployment through, so on a non-default deployment "
                      "the link resolves under the DEFAULT prefix instead of the "
                      "current one — exactly the reported bug. It fails the "
                      "FAIL_TO_PASS test, which renders under a NON-default "
                      "deployment and asserts the href carries that deployment's "
                      "prefix. Does NOT resolve.",
        "rationale": "REJECT from the equality clause: with `none` the resolver "
                     "is a function of a DIFFERENT third argument than the spec's "
                     "`some siteName`, so the results differ whenever the resolver "
                     "distinguishes them. Witness instantiates `resolveUrl` to "
                     "return its deployment-identifier argument, so `some siteName` "
                     "yields the URL `siteName` while `none` yields the fallback — "
                     "the load-bearing `siteName` binder is what discriminates.",
        "witness": _witness("fun _ _ s => s", "fun u _ => u",
                            "a", "m", "1", "S", "R"),
    },
    {
        "id": "default-site",
        "kind": "uniqueness",
        "expect": "reject",
        # Near-miss of omit-site: the resolver IS given a deployment identifier,
        # but a CONSTANT/default one ("admin") instead of the currently-effective
        # `siteName`. Ports the nagini weak-default-selector / weak-return-default
        # rivals (resolve relative to the default deployment's name).
        "module": _with_impl(
            "def implementation_getAdminUrl\n"
            "    (resolveUrl : String → String → Option String → Option String)\n"
            "    (formatLink : String → String → String)\n"
            "    (appLabel modelName arg siteName remoteObjStr : String) : String := Id.run do\n"
            '  let urlName := "admin:" ++ appLabel ++ "_" ++ modelName ++ "_change"\n'
            '  match resolveUrl urlName arg (some "admin") with\n'
            "  | some url => return formatLink url remoteObjStr\n"
            "  | none => return remoteObjStr"),
        "refinement": "resolving relative to a CONSTANT default deployment "
                      "identifier is what a real patch that hard-coded the default "
                      "deployment's name (or threaded the wrong one) would do. The "
                      "produced link carries the DEFAULT prefix, not the current "
                      "deployment's, so under the FAIL_TO_PASS test's non-default "
                      "deployment the href is wrong. This probes that the spec "
                      "checks WHICH deployment identifier reaches the resolver, "
                      "not merely that SOME identifier does. Does NOT resolve.",
        "rationale": "REJECT from the equality clause: with the constant "
                     "`some \"admin\"` the resolver is a function of a different "
                     "third argument than the spec's `some siteName`, differing "
                     "whenever `siteName ≠ \"admin\"`. Witness instantiates "
                     "`resolveUrl` to return its identifier argument, so the rival "
                     "yields `\"admin\"` while the spec yields `siteName`. A "
                     "near-miss of omit-site (it does pass SOME identifier), so it "
                     "carries its own distinguishing input on the `siteName` "
                     "binder.",
        "witness": _witness("fun _ _ s => s", "fun u _ => u",
                            "b", "n", "2", "T", "Q"),
    },
    {
        "id": "swap-route",
        "kind": "uniqueness",
        "expect": "reject",
        # Attacks the route-name components: transpose appLabel and modelName in
        # the assembled route name. The resolver is then handed the WRONG route
        # name, so the pinned `"admin:" ++ appLabel ++ "_" ++ modelName ++
        # "_change"` clause is violated.
        "module": _with_impl(
            "def implementation_getAdminUrl\n"
            "    (resolveUrl : String → String → Option String → Option String)\n"
            "    (formatLink : String → String → String)\n"
            "    (appLabel modelName arg siteName remoteObjStr : String) : String := Id.run do\n"
            '  let urlName := "admin:" ++ modelName ++ "_" ++ appLabel ++ "_change"\n'
            "  match resolveUrl urlName arg (some siteName) with\n"
            "  | some url => return formatLink url remoteObjStr\n"
            "  | none => return remoteObjStr"),
        "refinement": "assembling the route name from the grouping label and "
                      "model name in the WRONG order yields a route the resolver "
                      "cannot match, so no link is produced and the readonly field "
                      "renders as plain text. The FAIL_TO_PASS test asserts the "
                      "`<a href=…>` link is present, so it would FAIL. Does NOT "
                      "resolve.",
        "rationale": "REJECT from the equality clause: the spec pins the route "
                     "name to `\"admin:\" ++ appLabel ++ \"_\" ++ modelName ++ "
                     "\"_change\"`, but the rival passes the transposed name to "
                     "the resolver. Witness instantiates `resolveUrl` to echo its "
                     "route-name argument, so the rival's URL differs from the "
                     "spec's whenever `appLabel ≠ modelName` — discrimination "
                     "comes from the `appLabel`/`modelName` binders.",
        "witness": _witness("fun url _ _ => some url", "fun u _ => u",
                            "a", "m", "3", "U", "V"),
    },
    {
        "id": "drop-fallback",
        "kind": "uniqueness",
        "expect": "reject",
        # Attacks the `none` (no-URL) branch: return the empty string instead of
        # the record's display text `remoteObjStr`. The pinned fallback clause is
        # violated.
        "module": _with_impl(
            "def implementation_getAdminUrl\n"
            "    (resolveUrl : String → String → Option String → Option String)\n"
            "    (formatLink : String → String → String)\n"
            "    (appLabel modelName arg siteName remoteObjStr : String) : String := Id.run do\n"
            '  let urlName := "admin:" ++ appLabel ++ "_" ++ modelName ++ "_change"\n'
            "  match resolveUrl urlName arg (some siteName) with\n"
            "  | some url => return formatLink url remoteObjStr\n"
            '  | none => return ""'),
        "refinement": "when the resolution step produces no URL, the correct "
                      "behaviour is to render the record's plain display text; "
                      "returning the empty string instead drops that text. A "
                      "readonly reference to a target that is not registered (no "
                      "route) must still show its display text — the passing "
                      "readonly-links test asserts exactly that plain-text render, "
                      "so it would FAIL. Does NOT resolve.",
        "rationale": "REJECT from the equality clause's `none` arm: the spec pins "
                     "the no-URL result to `remoteObjStr`, but the rival returns "
                     "`\"\"`. Witness instantiates `resolveUrl` to return `none` "
                     "(forcing the fallback arm) with a non-empty `remoteObjStr`, "
                     "so the rival yields `\"\"` while the spec yields "
                     "`remoteObjStr` — discrimination comes from the "
                     "`remoteObjStr` binder on the fallback branch.",
        "witness": _witness("fun _ _ _ => none", "fun u _ => u",
                            "c", "d", "4", "W", "X"),
    },
    {
        "id": "swap-link-args",
        "kind": "uniqueness",
        "expect": "reject",
        # Attacks the `some` (URL) branch: apply the link-formatting step with its
        # two arguments TRANSPOSED (display text and URL swapped). The pinned
        # `formatLink url remoteObjStr` clause is violated.
        "module": _with_impl(
            "def implementation_getAdminUrl\n"
            "    (resolveUrl : String → String → Option String → Option String)\n"
            "    (formatLink : String → String → String)\n"
            "    (appLabel modelName arg siteName remoteObjStr : String) : String := Id.run do\n"
            '  let urlName := "admin:" ++ appLabel ++ "_" ++ modelName ++ "_change"\n'
            "  match resolveUrl urlName arg (some siteName) with\n"
            "  | some url => return formatLink remoteObjStr url\n"
            "  | none => return remoteObjStr"),
        "refinement": "the link-formatting step takes the URL and the display "
                      "text in a fixed order (the URL becomes the href, the text "
                      "the link body); transposing them produces malformed markup "
                      "with the text and href swapped. The FAIL_TO_PASS test "
                      "asserts the exact `<a href=\"URL\">text</a>` markup, so it "
                      "would FAIL. Does NOT resolve.",
        "rationale": "REJECT from the equality clause's `some` arm: the spec pins "
                     "the result to `formatLink url remoteObjStr`, but the rival "
                     "computes `formatLink remoteObjStr url`. Witness instantiates "
                     "`formatLink` to a non-commutative concatenation and forces a "
                     "URL result, so the two orders differ — discrimination comes "
                     "from the argument order over `remoteObjStr` and the resolved "
                     "URL.",
        "witness": _witness('fun _ _ _ => some "U"', "fun a b => a ++ b",
                            "e", "f", "5", "Y", "Z"),
    },
    {
        "id": "drop-arg",
        "kind": "uniqueness",
        "expect": "reject",
        # Attacks the `arg` binder: pass the empty string to the resolver instead
        # of the encoded record identifier. The pinned second argument of the
        # resolution step is violated.
        "module": _with_impl(
            "def implementation_getAdminUrl\n"
            "    (resolveUrl : String → String → Option String → Option String)\n"
            "    (formatLink : String → String → String)\n"
            "    (appLabel modelName arg siteName remoteObjStr : String) : String := Id.run do\n"
            '  let urlName := "admin:" ++ appLabel ++ "_" ++ modelName ++ "_change"\n'
            '  match resolveUrl urlName "" (some siteName) with\n'
            "  | some url => return formatLink url remoteObjStr\n"
            "  | none => return remoteObjStr"),
        "refinement": "the encoded record identifier must be threaded to the "
                      "resolution step so the produced URL points at THIS record; "
                      "passing the empty string instead resolves the wrong (or no) "
                      "URL. The FAIL_TO_PASS test asserts the href carries the "
                      "record's encoded identifier, so it would FAIL. Does NOT "
                      "resolve.",
        "rationale": "REJECT from the equality clause: the spec pins the "
                     "resolver's second argument to `arg`, but the rival passes "
                     "`\"\"`. Witness instantiates `resolveUrl` to echo its "
                     "identifier argument, so the rival's URL differs from the "
                     "spec's whenever `arg ≠ \"\"` — discrimination comes from the "
                     "`arg` binder.",
        "witness": _witness("fun _ a _ => some a", "fun u _ => u",
                            "g", "h", "6", "P", "O"),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> lean accounting. The sibling battery has 7 SPEC cases (1 soundness
# positive, 1 admissibility, 2 frame-mutation, 3 partial-domain/uniqueness
# rivals) plus a 2-case AXIOM lane. This bundle models the SAME single behavior
# but over a DIFFERENT carrier: nagini abstracts only the returned URL prefix
# (`Result() == prefixes[current_idx]`), while lean models the WHOLE returned
# markup string (route-name assembly + resolution with the current deployment id
# + link/fallback framing), with the resolver and formatter as universally-
# quantified parameters. Every sibling case is recorded below.
#
#   sibling case                 -> here                       disposition
#   ---------------------------------------------------------------------
#   pos-inline-selector          -> pos-direct-forward          RE-EXPRESSED
#                                   (+ pos-let-scrutinee)        ADDED positive
#   admiss-reads                 -> admiss-ground-nondefault-    RE-EXPRESSED
#                                     deployment
#   frame-mut-names              -> (none)                      VACUOUS (no heap)
#   frame-mut-prefixes           -> (none)                      VACUOUS (no heap)
#   weak-no-selector             -> omit-site                   PORTED
#   weak-default-selector        -> default-site                PORTED
#   weak-return-default          -> default-site (folded)       FOLDED
#   (no sibling)                 -> swap-route                  ADDED (carrier)
#   (no sibling)                 -> drop-fallback               ADDED (carrier)
#   (no sibling)                 -> swap-link-args              ADDED (carrier)
#   (no sibling)                 -> drop-arg                    ADDED (carrier)
#   AXIOM_TESTS (2)              -> (none)                      DROPPED (G-AX)
#
# RE-EXPRESSED / ADDED (positives): the sibling's positive inlines the selector
#   local. Here the analogue is pos-direct-forward (drop the `Id.run do` scaffold
#   and form the match directly, proof retuned) and pos-let-scrutinee (bind the
#   resolution result to a local and match that; frozen proof still closes). Both
#   keep `some siteName` and the link/fallback framing — a faithful reshape MUST
#   verify, else SPEC-TOO-STRONG.
# RE-EXPRESSED (admissibility): the sibling self-calls to prove its six-clause
#   precondition admits an F2P-shaped registry. This bundle's `correct_getAdminUrl`
#   carries NO precondition hypothesis (the `∀` is unguarded — the behavior is
#   total over all strings and all resolvers/formatters), so there is no
#   precondition BINDER to admit. That does NOT make the lane vacuous: on a total
#   carrier the analogue of PRECOND-TOO-STRONG is the obligation being
#   UNSATISFIABLE at exactly an F2P-shaped input, which
#   admiss-ground-nondefault-deployment tests directly — it discharges the spec
#   predicate by evaluation at a ground point (non-default deployment in effect, a
#   resolver that mounts each deployment under its own prefix) and evaluates the
#   outcome to the markup carrying that deployment's prefix, before closing the
#   frozen obligation verbatim. Landed with a real build; an earlier revision of
#   this manifest recorded the lane as VACUOUS, which was wrong.
# VACUOUS (frame-mutation, x2): the sibling carries these MANDATORY because
#   `names`/`prefixes` are held at Acc(.,1/2) an impl can illegally write. This
#   backend is referentially transparent and declares no `mut` binder over its
#   inputs — every input is an immutable value with no heap footprint — so there
#   is no read-only input to overwrite and no substitute probe. Not fabricated
#   (porting map: vacuous here).
# PORTED / FOLDED (partial-domain): weak-no-selector ports directly as omit-site
#   (has_selector=False / current_app omitted -> `none`). weak-default-selector
#   ports as default-site (resolve relative to the default deployment id ->
#   constant `some "admin"`). weak-return-default (return the default's prefix
#   directly, no axiom) FOLDS into default-site: on this carrier "resolve against
#   a constant default identifier" and "return the default's result directly" are
#   the same observable wrong value (the resolver here IS the value producer), so
#   it needs no separate rival.
# ADDED (carrier): the lean spec pins THREE things the nagini carrier abstracted
#   away — the route-name assembly, the encoded identifier threaded to the
#   resolver, and the link/fallback framing (the try/except NoReverseMatch that
#   nagini's mapping.md explicitly dropped). swap-route, drop-arg, swap-link-args
#   and drop-fallback attack exactly those clauses, so every binder of the richer
#   spec is defended. These are coverage of the surface THIS bundle models, not
#   fabricated rivals for behaviors it does not model.
#
# The six reject witnesses probe six DISTINCT input tuples; across them
# appLabel/modelName/arg/siteName/remoteObjStr and the two callee instantiations
# all take distinct values (pts=6). The load-bearing `siteName` binder is
# attacked by two near-misses (omit-site `none`, default-site constant).
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job; this bundle declares no
# axiom (meta.json axioms == []; the resolver/formatter are directive-5
# quantified parameters, not oracles), so there is nothing to probe and the gate
# ignores AXIOM_TESTS regardless.
AXIOM_TESTS = []
