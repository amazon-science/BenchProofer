# properties.py — PBT manifest for pydata__xarray-2905. NOT a Nagini module; a
# record of adversarial falsification cases parsed by swebench_nagini.pbt.
#
# Defended surface (read from model.py / refinement.md / mapping.md):
#   normalize_self_describing(data: Incoming) -> int  models the ".values-unwrap"
#   normalization step of as_compatible_data after the gold patch.
#   * data's four fields are ALL read-only — Acc(data.X, 1/2) in BOTH the Requires
#     and the Ensures, plus four Ensures(data.X == Old(data.X)) pins. => the
#     FRAME-MUTATION attack is MANDATORY here.
#   * the precondition invariant Implies(is_recognized_container, exposes_values)
#     encodes the real-world fact that a recognized pandas container exposes .values.
#   * the LOAD-BEARING postcondition is the pair of total-by-cases clauses:
#       Implies(is_recognized_container,     Result() == values_identity)   # unwrap
#       Implies(not is_recognized_container, Result() == identity)          # passthrough
#     This is a FULLY-GROUNDED oracle: Result() is pinned to a field of the args on
#     BOTH branches (no @Pure answer-key, no opaque marker). There is therefore no
#     "wrong echo that still verifies" — see assessment. We instead carry an honest
#     cheapest-impl positive control and attack the two branch domains directly.
#   * NO @ContractOnly axioms, NO consumed deep model; the single A-reference
#     (is_recognized_container) is validated against the real as_compatible_data by
#     axiom_check.py / G-AX. => AXIOM_TESTS = [].
#
# Authoring discipline: every spec case is built by region-surgery (_swap) editing
# ONLY text strictly between "# impl-start" and "# impl-end" of model.py, so the
# frozen spec (signatures + axioms/pure/pre/post regions) is byte-identical and
# same_spec holds for every case. The verifier decides verify/reject.

from pathlib import Path

INSTANCE = "pydata__xarray-2905"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()

# The exact gold impl region body (between the markers, the markers excluded).
_GOLD_IMPL = """\
    if data.is_recognized_container:
        result = data.values_identity
    else:
        result = data.identity
    return result"""

assert _GOLD_IMPL in _BASE, "drift: gold impl body not found verbatim in model.py"


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


def _impl(new_body):
    """Return a full model.py with the gold impl body replaced by new_body.
    new_body is the text that sits between the impl markers (markers untouched),
    so the swap is confined to the impl region and same_spec is preserved."""
    return _swap(_BASE, _GOLD_IMPL, new_body)


SPEC_TESTS = [
    # ---- 5. POSITIVE CONTROL (soundness) --------------------------------------
    # Structurally different but CORRECT: branch order inverted (test the
    # NOT-recognized case first) and written with early returns instead of a
    # result local. Keeps every clause's proof obligation trivially (each return
    # is reached exactly under its guard). MUST verify; else SPEC-TOO-STRONG.
    {
        "id": "pos-control-reordered-early-return",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(
            "    if not data.is_recognized_container:\n"
            "        return data.identity\n"
            "    return data.values_identity"
        ),
        "rationale": (
            "a correct impl with the branch order flipped + early returns "
            "(non-recognized first) satisfies both Implies clauses on exactly "
            "their guards; if it cannot verify the postcondition is TOO-STRONG. "
            "No framing asserts are needed — the impl has no loop and Result() is "
            "pinned per-branch, so the gold proof is preserved by construction."
        ),
    },
    # A second positive control: ternary / single-return reshape (no branch at
    # all in control flow, just a conditional expression). Also correct.
    {
        "id": "pos-control-conditional-expression",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(
            "    result = data.values_identity if data.is_recognized_container "
            "else data.identity\n"
            "    return result"
        ),
        "rationale": (
            "the same total-by-cases function written as one conditional "
            "expression — a faithful correct shape that must verify."
        ),
    },

    # ---- 6. ADMISSIBILITY -----------------------------------------------------
    # The precondition must accept a normal, F2P-shaped input. We discharge this
    # from WITHIN the impl region by a self-call on the same `data`: the call's
    # Requires (Acc(data.X,1/2) for each field + the invariant) is exactly what we
    # already hold here, so the call site verifies iff the precondition is
    # satisfiable for an in-domain value. If it fails, PRECOND-TOO-STRONG.
    {
        "id": "admiss-self-call-in-domain",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl(
            "    # admissibility: re-establish the precondition on the live input\n"
            "    # and consume it via a self-call (proves Requires is admissible).\n"
            "    echo = normalize_self_describing(data)\n"
            "    Assert(Implies(data.is_recognized_container, echo == data.values_identity))\n"
            "    Assert(Implies(not data.is_recognized_container, echo == data.identity))\n"
            "    if data.is_recognized_container:\n"
            "        result = data.values_identity\n"
            "    else:\n"
            "        result = data.identity\n"
            "    return result"
        ),
        "rationale": (
            "a self-call on the read-only `data` discharges the function's own "
            "Requires (the half-perms + the recognized=>exposes invariant), "
            "proving the precondition admits a normal input; the Assert lines "
            "confirm the returned tag matches the contract. If the call site "
            "cannot establish Requires for the live in-domain input => "
            "PRECOND-TOO-STRONG."
        ),
    },

    # ---- 1. FRAME-MUTATION (MANDATORY: data.* are Acc(...,1/2) read-only) ------
    # A rival that WRITES the read-only input to satisfy the postcondition
    # vacuously. It forces is_recognized_container=False then returns identity so
    # the (now-false) recognized branch obligation is trivially met. With only
    # half permission to data.is_recognized_container the WRITE is illegal: the
    # spec must reject for INSUFFICIENT PERMISSION (not for a wrong value).
    {
        "id": "frame-mutation-overwrite-predicate",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    data.is_recognized_container = False\n"
            "    return data.identity"
        ),
        "refinement": (
            "the gold patch only rebinds a LOCAL name (data = data.values); it "
            "never mutates the incoming object's class/attributes. A real patch "
            "that overwrote the recognized-ness of the live `data` would corrupt "
            "the object handed to the caller and would NOT resolve the F2P "
            "test_unsupported_type (the stored CustomWithValuesAttr object must be "
            "returned intact by ._data.item()); mutating it away is a different, "
            "wrong program."
        ),
        "rationale": (
            "rejection comes from the PERMISSION SYSTEM: data.is_recognized_"
            "container is held at Acc(...,1/2) (read-only) in the Requires, so the "
            "assignment lacks write permission and fails to verify. This is the "
            "#1 weakness class a byte-fuzzer never finds."
        ),
    },
    # Frame-mutation variant: overwrite identity to launder the passthrough
    # branch. Same permission rejection on a different read-only field.
    {
        "id": "frame-mutation-overwrite-identity",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    if data.is_recognized_container:\n"
            "        return data.values_identity\n"
            "    data.identity = data.values_identity\n"
            "    return data.identity"
        ),
        "refinement": (
            "rebinding the surviving identity by writing data.identity is not what "
            "the gold does and mutates the read-only carrier; a real analogue "
            "(reassigning the input object's stored value) would change what the "
            "caller stores and break the passthrough the F2P requires."
        ),
        "rationale": (
            "rejection from the PERMISSION SYSTEM: data.identity is Acc(...,1/2), "
            "so `data.identity = ...` lacks write permission. Even though the "
            "returned value would equal identity, the write itself is illegal."
        ),
    },

    # ---- 3. PARTIAL-DOMAIN / value-double-mask: the PRE-PATCH bug --------------
    # Key on exposes_values instead of is_recognized_container (== the pre-patch
    # getattr(data,'values',data)). Correct on every recognized container and on
    # every plain object WITHOUT .values; diverges ONLY on the discriminating
    # sub-domain (exposes_values=True, is_recognized_container=False). On that
    # witness it returns values_identity, violating
    # Implies(not is_recognized_container, Result()==identity). MUST reject.
    {
        "id": "partial-domain-prepatch-exposes-values",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    if data.exposes_values:\n"
            "        result = data.values_identity\n"
            "    else:\n"
            "        result = data.identity\n"
            "    return result"
        ),
        "refinement": (
            "this is EXACTLY the pre-patch behaviour data = getattr(data, "
            "'values', data) — model_prepatch.py reproduces it. Its faithful real "
            "patch keeps the v0.10.1 bug: a non-pandas object that merely exposes "
            ".values (the issue's HasValues / the F2P CustomWithValuesAttr) is "
            "coerced to its .values contents, so "
            "Variable(dims=(), data=obj)._data.item() is NOT obj and "
            "test_unsupported_type FAILS. verify+resolve break if it verified."
        ),
        "rationale": (
            "rejection from the postcondition clause "
            "Implies(not data.is_recognized_container, Result() == data.identity): "
            "on the witness is_recognized_container=False & exposes_values=True the "
            "impl returns values_identity != identity (the invariant only forces "
            "recognized=>exposes, NOT exposes=>recognized, so this witness is in "
            "the precondition domain)."
        ),
    },
    # ---- 3b. PARTIAL-DOMAIN: always-unwrap (drops the passthrough domain) ------
    # Returns values_identity unconditionally. Correct on the whole recognized
    # sub-domain; wrong on every non-recognized input. MUST reject.
    {
        "id": "partial-domain-always-unwrap",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl("    return data.values_identity"),
        "refinement": (
            "always unwrapping to .values is the unconditional version of the "
            "pre-patch bug; a real patch doing `data = data.values` for every "
            "value would coerce ALL non-pandas objects (and crash on objects "
            "lacking .values), failing test_unsupported_type and many P2P object-"
            "array tests."
        ),
        "rationale": (
            "rejection from Implies(not is_recognized_container, Result()==identity)"
            ": for a non-recognized input the impl yields values_identity, which is "
            "not provably == identity (distinct free tags)."
        ),
    },
    # ---- 3c. PARTIAL-DOMAIN: never-unwrap (drops the recognized domain) --------
    # Returns identity unconditionally. Correct on every passthrough input; wrong
    # on every recognized pandas container (which must unwrap). MUST reject.
    {
        "id": "partial-domain-never-unwrap",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl("    return data.identity"),
        "refinement": (
            "never unwrapping means a real patch that DELETED the unwrap entirely; "
            "pd.Series / pd.Index / pd.DataFrame would no longer be reduced to "
            "their .values, breaking the pandas-handling P2P tests "
            "(TestAsCompatibleData on pandas inputs) — a different, non-resolving "
            "program."
        ),
        "rationale": (
            "rejection from Implies(is_recognized_container, Result()==values_"
            "identity): for a recognized input the impl yields identity, not "
            "provably == values_identity."
        ),
    },
    # ---- 3d. PARTIAL-DOMAIN: value-double-mask via identity-tag confusion ------
    # Swap the two branch RESULTS: unwrap on the passthrough domain and pass
    # through on the recognized domain (both branches individually wrong). Wrong
    # on BOTH sub-domains; a cross-check that neither Implies clause can be
    # satisfied by the mirror assignment. MUST reject.
    {
        "id": "partial-domain-swapped-results",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    if data.is_recognized_container:\n"
            "        result = data.identity\n"
            "    else:\n"
            "        result = data.values_identity\n"
            "    return result"
        ),
        "refinement": (
            "this unwraps the WRONG cases (recognized containers pass through, "
            "plain .values-objects get unwrapped) — the opposite of the fix; it "
            "resolves neither the F2P nor the pandas P2P tests."
        ),
        "rationale": (
            "rejection from BOTH Implies clauses: on the recognized branch it "
            "returns identity (must be values_identity) and on the passthrough "
            "branch values_identity (must be identity); the two free tags are not "
            "provably equal."
        ),
    },
]

# No @ContractOnly axioms and no consumed deep model in this bundle: the sole
# A-reference (is_recognized_container) is validated against the real
# as_compatible_data by axiom_check.py / G-AX, which is the standing soundness
# check. There is no callee-domain containment obligation to probe here (the
# decision predicate is modelled deeply as a bool field, not a callee input).
AXIOM_TESTS = []
