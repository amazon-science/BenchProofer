#!/usr/bin/env python3
"""G-AX executable soundness check for sympy__sympy-14976.

Executes the REAL repo callee that `Solution.lean` models deeply and asserts
that every observation matches the model encoded in Solution.lean.

The kind-A obligations, all on the single A-reference — the (unchanged)
name-resolution helper `AbstractPythonCodePrinter._module_format`
(`sympy/printing/pycode.py:113`) at the one dotted name the modeled operation
resolves, `'mpmath.mpf'`:

  (A-ref/value) the deep model `mpfName : Bool -> String` (Solution.lean pure
      region, `if qualified then "mpmath.mpf" else "mpf"`) equals the real
      `_module_format('mpmath.mpf')` in BOTH configurations of the ambient
      name-spelling setting `fully_qualified_modules`:
        mpfName True  == _module_format('mpmath.mpf')  on a qualified printer
        mpfName False == _module_format('mpmath.mpf')  on an unqualified printer
      The resolver is settings-dependent (pycode.py:117-121), so a model that
      pinned ONE branch would be strictly stronger than the real helper on the
      other. Both branches are hard obligations here; neither is "recorded".

  (A-ref/binding) the model's Bool binder is the real setting: the printer's
      documented default (`pycode.py:95`) is `fully_qualified_modules=True`, so
      `MpmathPrinter()` corresponds to `qualified = True`, and the printer
      `lambdify` constructs (`sympy/utilities/lambdify.py:416`, which passes
      `fully_qualified_modules=False`) corresponds to `qualified = False`.
      Asserted, so the mapping.md §2 binding of the binder is executable rather
      than prose.

  (A-ref/effect) the deep model `mpfImport = [("mpmath", "mpf")]` equals the
      import the resolver RECORDS while resolving that name, and the recording
      law mapping.md §3.1 states — post-state = pre-state UNION the delta, in
      BOTH configurations and independent of the pre-state (set insertion, hence
      idempotent) — holds by execution from several pre-states.

Runs in-container (the prebuilt SWE-Bench instance image) at base_commit: the
helper is UNCHANGED by patch.diff, so the un-patched worktree is its reference
(`ax_apply_gold` is not set). Imports `sympy` (the repo under test) only.
Exit 0 iff every obligation holds.
"""
import sys

# --- Solution.lean reference encoding (kept in lock-step with the model) -----
# def mpfName (qualified : Bool) : String := if qualified then "mpmath.mpf" else "mpf"
def mpf_name(qualified):
    return "mpmath.mpf" if qualified else "mpf"


# def mpfImport : List (String × String) := [("mpmath", "mpf")]
MPF_IMPORT = [("mpmath", "mpf")]

FQN = "mpmath.mpf"


def _printer(qualified=None):
    """A real MpmathPrinter. `qualified=None` means "no settings override", i.e.
    the documented default configuration."""
    from sympy.printing.pycode import MpmathPrinter
    if qualified is None:
        return MpmathPrinter()
    return MpmathPrinter(settings={"fully_qualified_modules": qualified})


def _flat(module_imports):
    """The printer's `module_imports` (a defaultdict(set)) flattened to the set of
    (module, name) pairs the Lean carrier `List (String × String)` abstracts
    (mapping.md §2: order-insensitive, duplicate-free)."""
    return {(mod, nm) for mod, names in module_imports.items() for nm in names}


def check_binder_binding():
    """(A-ref/binding) the model's Bool binder IS the repo setting, and the
    default configuration is the qualified one."""
    p = _printer(None)
    assert p._settings.get("fully_qualified_modules") is True, (
        "expected default fully_qualified_modules=True, got %r"
        % p._settings.get("fully_qualified_modules"))
    for qualified in (True, False):
        p = _printer(qualified)
        assert p._settings.get("fully_qualified_modules") is qualified, (
            "settings override did not take: asked %r, printer has %r"
            % (qualified, p._settings.get("fully_qualified_modules")))


def check_module_format_value():
    """(A-ref/value) mpfName agrees with the real resolver in BOTH branches."""
    observed = {}
    for qualified in (True, False):
        p = _printer(qualified)
        observed[qualified] = p._module_format(FQN)   # real callee
        assert observed[qualified] == mpf_name(qualified), (
            "mpfName deep model unsound at qualified=%r: "
            "_module_format(%r) gave %r, model gives %r"
            % (qualified, FQN, observed[qualified], mpf_name(qualified)))
    # The two branches must actually DIFFER, else this check would pass for a
    # one-branch model too and prove nothing about the branch structure.
    assert observed[True] != observed[False], (
        "the resolver returned the same spelling %r in both configurations; the "
        "model's Bool branch would then be unobservable and this check vacuous"
        % (observed[True],))
    # The default-settings printer must resolve exactly as the qualified one.
    assert _printer(None)._module_format(FQN) == mpf_name(True), (
        "default-settings printer disagrees with mpfName True")
    return observed


def check_registration_effect():
    """(A-ref/effect) mpfImport is the delta the resolver records, in BOTH
    configurations, and the post = pre UNION delta law holds from any pre-state."""
    delta = set(MPF_IMPORT)
    pre_states = [
        {},                                        # fresh printer
        {"math": {"sin"}},                         # unrelated entries present
        {"mpmath": {"mpf"}},                       # the delta already recorded
        {"mpmath": {"sign"}},                      # same module, other name
        {"mpmath": {"mpf", "sign"}, "math": {"copysign"}},
    ]
    for qualified in (True, False):
        for pre in pre_states:
            p = _printer(qualified)
            for mod, names in pre.items():
                for nm in names:
                    p.module_imports[mod].add(nm)
            before = _flat(p.module_imports)
            p._module_format(FQN)                  # real callee, register=True
            after = _flat(p.module_imports)
            assert after == before | delta, (
                "registration effect unsound at qualified=%r, pre=%r: "
                "after=%r, model predicts %r"
                % (qualified, pre, sorted(after), sorted(before | delta)))
            # idempotent: resolving again records nothing further
            p._module_format(FQN)
            assert _flat(p.module_imports) == after, (
                "second resolution changed the recorded imports; the delta model "
                "assumes set insertion (idempotent)")
    # The delta is non-empty, so the effect clause is not vacuously satisfiable
    # by a model that recorded nothing.
    assert delta, "mpfImport is empty; the effect obligation would be vacuous"


def main():
    check_binder_binding()
    observed = check_module_format_value()
    check_registration_effect()
    print("G-AX OK: mpfName deep model sound in BOTH configurations "
          "(_module_format(%r) = %r under fully_qualified_modules=True, %r under "
          "False; default = the True branch), the Bool binder is that setting, "
          "and mpfImport = %r is exactly the import the resolver records "
          "(post = pre UNION delta verified from 5 pre-states x 2 "
          "configurations, idempotent)."
          % (FQN, observed[True], observed[False], MPF_IMPORT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
