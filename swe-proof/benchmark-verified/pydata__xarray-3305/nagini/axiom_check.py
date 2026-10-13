#!/usr/bin/env python3
"""G-AX soundness check for pydata__xarray-3305.

Validates the single consumed axiom `ambient_keep_default` against the REAL
callee it stands in for — xarray's ambient default-policy resolver
`xarray.core.options._get_keep_attrs` — and validates the deep metadata
selection model against the REAL `Variable.quantile` end-to-end behaviour.

Axiom under test (A-consumed), as encoded in model.py:

    ambient_keep_default()  ==  _get_keep_attrs(default=False)  ==  False

The axiom is sound only under the default ambient configuration
(OPTIONS["keep_attrs"] == "default"), which is the global state every F2P/P2P
test runs under (none of them mutates the global option). mapping.md records
this flag dependency; this check fuzzes the resolver under that configuration
AND under the non-default settings to document the exact boundary.

Also performs the end-to-end behavioural check that the metadata-selection
model (selected_attrs / resolve_keep) matches the real Variable.quantile:
keep_attrs=True copies the source attrs, keep_attrs in {False, None-default}
yields empty attrs.

Imports: stdlib + xarray/numpy (the very modules the patch touches).

Run mode (G-AX convention): the consumed-axiom check
(`check_ambient_default_axiom`) is patch-INDEPENDENT — it exercises the
unchanged `_get_keep_attrs` resolver and always runs. The end-to-end sections
validate POST-PATCH behaviour (the `keep_attrs` kwarg the patch adds), so they
must run against the gold-applied source; the orchestrator runs this script
with `apply_gold=True`. If the patched signature is absent (the script was run
in the base image without gold), the e2e sections cannot execute meaningfully:
the script exits 2 — a harness/config signal ("re-run with gold applied"),
DISTINCT from exit 1 (an actual axiom/model violation) and exit 0 (sound).

Exit codes: 0 = sound (axiom + e2e); 1 = a real axiom/model violation;
2 = run-mode error (patched signature missing — re-run with apply_gold=True).
"""
import sys
import inspect
import itertools

import numpy as np
import xarray as xr
from xarray.core.variable import Variable
from xarray.core.options import _get_keep_attrs, OPTIONS, set_options

failures = []


def quantile_supports_keep_attrs():
    """True iff the in-tree Variable.quantile accepts the keep_attrs kwarg —
    i.e. the gold patch (or an equivalent fix) is applied. Determines whether
    the post-patch e2e sections can run."""
    try:
        sig = inspect.signature(Variable.quantile)
    except (TypeError, ValueError):
        return False
    return "keep_attrs" in sig.parameters


def check_ambient_default_axiom():
    """ambient_keep_default() == _get_keep_attrs(default=False) == False under
    the default ambient configuration."""
    # Default global state (as every test runs): OPTIONS["keep_attrs"]=="default".
    assert OPTIONS["keep_attrs"] == "default", (
        "test harness baseline expects default keep_attrs option; got %r"
        % (OPTIONS["keep_attrs"],)
    )
    observed = _get_keep_attrs(default=False)
    if observed is not False:
        failures.append(
            "ambient_keep_default axiom violated: _get_keep_attrs(default=False) "
            "== %r under default config, axiom claims False" % (observed,)
        )
    # Document the boundary: under non-default global settings the resolver
    # returns the global choice, not the supplied default. The axiom is scoped
    # to the default config (recorded in mapping.md); confirm the boundary so a
    # future config change is caught loudly rather than silently unsound.
    with set_options(keep_attrs=True):
        if _get_keep_attrs(default=False) is not True:
            failures.append("resolver boundary: keep_attrs=True should force True")
    with set_options(keep_attrs=False):
        if _get_keep_attrs(default=False) is not False:
            failures.append("resolver boundary: keep_attrs=False should force False")
    # Restore is automatic via context manager; reassert default.
    if OPTIONS["keep_attrs"] != "default":
        failures.append("global option not restored to default after set_options")


def model_resolve_keep(keep):
    """Mirror of model.py resolve_keep under the default ambient config."""
    if keep is None:
        return False  # ambient_keep_default() under default config
    return bool(keep)


def model_selected_attrs(src_attrs, keep):
    """Mirror of model.py selected_attrs: keep -> copy of source; else empty."""
    if keep:
        return dict(src_attrs)
    return {}


def check_variable_quantile_end_to_end():
    """The deep metadata-selection model == real Variable.quantile attrs, over
    a fuzz of source-attr payloads, keep flags, q shapes and interpolations."""
    rng = np.random.RandomState(20193305)
    interps = ["linear", "lower", "higher", "midpoint", "nearest"]
    q_choices = [0.5, [0.25], [0.25, 0.75], 0.0, 1.0]
    attr_payloads = [
        {},
        {"units": "K"},
        {"units": "K", "long_name": "temperature"},
        {"a": 1, "b": 2.5, "c": "x"},
        {str(i): i for i in range(5)},
    ]
    keep_choices = [True, False, None]

    cases = 0
    for attrs, keep, q in itertools.product(attr_payloads, keep_choices, q_choices):
        for interp in interps:
            data = rng.rand(6)
            var = Variable(("x",), data.copy(), attrs=dict(attrs))
            out = var.quantile(q, dim="x", interpolation=interp,
                               keep_attrs=keep)
            expected = model_selected_attrs(attrs, model_resolve_keep(keep))
            if dict(out.attrs) != expected:
                failures.append(
                    "Variable.quantile attrs mismatch: attrs=%r keep=%r q=%r "
                    "interp=%r -> real %r, model %r"
                    % (attrs, keep, q, interp, dict(out.attrs), expected)
                )
            cases += 1
    return cases


def check_dataarray_quantile_forwarding():
    """Site 2 forwarding: DataArray.quantile (-> Dataset.quantile ->
    Variable.quantile) honours keep_attrs end-to-end. This is exactly the F2P
    behaviour. Fail loud if any keep value disagrees with the model.
    Returns the number of cases exercised."""
    attrs = {"units": "K"}
    cases = 0
    for keep in (True, False, None):
        da = xr.DataArray([0.0, 1.0, 2.0, 3.0], dims="x", attrs=dict(attrs))
        out = da.quantile(0.9, dim="x", keep_attrs=keep)
        expected = model_selected_attrs(attrs, model_resolve_keep(keep))
        if dict(out.attrs) != expected:
            failures.append(
                "DataArray.quantile forwarding mismatch: keep=%r -> real %r, "
                "model %r" % (keep, dict(out.attrs), expected)
            )
        cases += 1
    return cases


def main():
    # Patch-independent: always runs (the consumed axiom over the unchanged
    # _get_keep_attrs resolver). 2 boundary observations + the default-config
    # assertion.
    check_ambient_default_axiom()

    if not quantile_supports_keep_attrs():
        # The e2e sections validate the post-patch keep_attrs behaviour by
        # construction; they cannot run against the unpatched base source.
        # Signal a run-mode error (exit 2) so the harness re-runs with the gold
        # patch applied — this is NOT an axiom violation (exit 1).
        if failures:
            print("G-AX FAIL (%d):" % len(failures))
            for f in failures:
                print("  -", f)
            sys.exit(1)
        print("G-AX RUN-MODE: consumed axiom sound, but Variable.quantile lacks "
              "the keep_attrs kwarg (base source, no gold applied). The "
              "end-to-end sections require the gold-applied container; re-run "
              "with apply_gold=True.")
        sys.exit(2)

    n_var = check_variable_quantile_end_to_end()
    n_da = check_dataarray_quantile_forwarding()
    if failures:
        print("G-AX FAIL (%d):" % len(failures))
        for f in failures:
            print("  -", f)
        sys.exit(1)
    # Total observations: consumed-axiom boundary (2) + Variable e2e + DataArray
    # e2e. Reported transparently so the count is auditable.
    total = 2 + n_var + n_da
    print("G-AX OK: ambient_keep_default axiom sound under default config "
          "(2 boundary obs); metadata-selection model == real Variable.quantile "
          "over %d cases; DataArray.quantile forwarding honours keep_attrs "
          "(%d cases). Total observations: %d."
          % (n_var, n_da, total))
    sys.exit(0)


if __name__ == "__main__":
    main()
