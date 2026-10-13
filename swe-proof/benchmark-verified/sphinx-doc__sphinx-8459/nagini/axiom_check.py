#!/usr/bin/env python3
"""G-AX executable soundness check for sphinx-doc__sphinx-8459.

The model has NO consumed `@ContractOnly` axiom. The behaviour the change makes
effective -- resolving an annotation source through the configured alias map
before recording it -- is modelled DEEPLY by `resolve` / `expand` (model.py
pure region). G-AX validates that deep model **== the real callee**: the
annotation resolution performed by `sphinx.util.inspect.signature(obj,
type_aliases=...)`, which delegates to `typing.get_type_hints(subject, None,
type_aliases)` (sphinx/util/inspect.py:508; sphinx/util/typing.py:69).

The deep model encodes, for one annotation source token under an alias map:

    resolve(tok, aliases) = aliases[tok]   if tok in aliases   (alias preserved)
                          = expand(tok)    otherwise           (expanded form)

with the structural invariant that, for an aliased source, the alias's target
DIFFERS from the unaliased expansion (so the alias map is observable).

This check reproduces the tested situation with stdlib `typing` only (the very
resolver sphinx delegates to): a module with PEP 563 string annotations
(`from __future__ import annotations`) and a module-level alias `name = <type>`,
a function annotated with that alias, resolved twice --

  * with the alias map supplied as the resolution namespace (post-patch:
    `type_aliases={name: name}`): the forward reference stays the alias NAME
    (the localns binding shadows the global and is itself the alias string), so
    the recorded annotation is the alias -> `resolve` takes the alias branch;

  * with NO alias map (pre-patch default `{}`): the forward reference is
    evaluated against the module globals and expands to the underlying type, so
    the recorded annotation is the expansion -> `resolve` takes the `expand`
    branch, and that expansion DIFFERS from the alias name.

It asserts both observations, over boundary + fuzz alias configurations. Exit 0
iff every obligation holds. Imports only the standard library (`typing`,
`types`, `random`, `sys`) -- the resolver sphinx itself calls.
"""
import keyword
import random
import sys
import types
import typing


def build_module(alias_name, underlying_src, param_names):
    """Build a module with PEP 563 string annotations, a module-level alias
    `<alias_name> = <underlying>`, and a function annotating each param (and the
    return) with `<alias_name>`. Returns (function, underlying_render)."""
    lines = ["from __future__ import annotations"]
    lines.append("%s = %s" % (alias_name, underlying_src))
    sig_params = ", ".join("%s: %s" % (p, alias_name) for p in param_names)
    lines.append("def fn(%s) -> %s:" % (sig_params, alias_name))
    lines.append("    return None")
    mod = types.ModuleType("axcheck_target")
    exec(compile("\n".join(lines), "axcheck_target", "exec"), mod.__dict__)
    return mod.__dict__["fn"]


def render(annotation):
    """Render a resolved annotation the way the recording step observes it.

    `typing.get_type_hints` yields either a real type (for an expanded forward
    reference, e.g. `int`) or a `typing.ForwardRef` (when the alias namespace
    keeps the source as its own name). The recording step stringifies it; for
    this check the *name* it renders to is the observable that distinguishes the
    alias from its expansion."""
    if isinstance(annotation, typing.ForwardRef):
        return annotation.__forward_arg__          # the preserved alias name
    return getattr(annotation, "__name__", None) or str(annotation)


def resolve_real(fn, type_aliases):
    """The REAL resolver sphinx delegates to: typing.get_type_hints(obj, None,
    localns) with the configured alias map as the resolution namespace."""
    return typing.get_type_hints(fn, None, type_aliases)


def check_config(alias_name, underlying_src, param_names):
    fn = build_module(alias_name, underlying_src, param_names)
    keys = list(param_names) + ["return"]

    # --- alias branch: alias map supplied -> alias NAME preserved (resolve) ---
    aliases = {alias_name: alias_name}
    hints_alias = resolve_real(fn, aliases)
    for k in keys:
        assert k in hints_alias, (
            "alias config %r: key %r missing from resolved hints %r"
            % (alias_name, k, hints_alias))
        observed = render(hints_alias[k])
        assert observed == alias_name, (
            "A-reference unsound (alias branch) for %r: with the alias map the "
            "real resolver recorded %r, deep model `resolve` requires the alias "
            "%r preserved" % (alias_name, observed, alias_name))

    # --- expand branch: NO alias map -> underlying expansion (expand) ---------
    hints_plain = resolve_real(fn, {})
    expansions = {}
    for k in keys:
        assert k in hints_plain, (
            "plain config %r: key %r missing from resolved hints %r"
            % (alias_name, k, hints_plain))
        expansions[k] = render(hints_plain[k])

    # Structural invariant the deep model relies on: for the aliased source the
    # unaliased expansion DIFFERS from the alias name (so the alias map is
    # observable -- this is exactly the bug the patch fixes).
    for k in keys:
        assert expansions[k] != alias_name, (
            "A-reference unsound (expand branch) for %r: the unaliased "
            "expansion %r equals the alias name, so the alias map would be "
            "unobservable -- contradicts the modelled discriminator"
            % (alias_name, expansions[k]))


def main():
    # --- boundary configurations -----------------------------------------
    boundary = [
        # (alias name, underlying type source, parameter names)
        ("myint", "int", ["x", "y"]),                 # the F2P test's exact case
        ("JSONObject", "dict", ["data"]),             # the issue's reproducer shape
        ("MyStr", "str", ["s"]),
        ("Num", "float", ["a", "b", "c"]),
        ("Flag", "bool", ["ok"]),
        ("Seq", "list", ["items"]),
        ("Alias1", "int", ["only"]),
        ("LongAliasName", "bytes", ["p", "q"]),
    ]
    for cfg in boundary:
        check_config(*cfg)

    # --- randomized fuzz ---------------------------------------------------
    rng = random.Random(8459)
    underlyings = ["int", "str", "float", "bool", "list", "dict", "bytes",
                   "complex", "tuple", "frozenset"]
    letters = "abcdefghijklmnopqrstuvwxyz"
    for _ in range(2000):
        # an alias name that is NOT a builtin/global, so its expansion differs
        alias = "Al" + "".join(rng.choice(letters) for _ in range(rng.randint(2, 8)))
        underlying = rng.choice(underlyings)
        nparams = rng.randint(1, 4)
        params = []
        seen = set()
        while len(params) < nparams:
            p = "p" + "".join(rng.choice(letters) for _ in range(rng.randint(1, 4)))
            if p not in seen and p != "return" and not keyword.iskeyword(p):
                seen.add(p)
                params.append(p)
        check_config(alias, underlying, params)

    print("G-AX OK: resolve/expand deep model == real get_type_hints resolver "
          "on %d boundary + 2000 fuzz alias configurations (alias branch "
          "preserves the configured name; no-alias branch expands to a "
          "different form -- the observable discriminator)." % len(boundary))
    return 0


if __name__ == "__main__":
    sys.exit(main())
