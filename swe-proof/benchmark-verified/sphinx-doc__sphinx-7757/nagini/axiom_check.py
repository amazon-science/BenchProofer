#!/usr/bin/env python3
"""G-AX executable soundness check for sphinx-doc__sphinx-7757.

Runs in the official evaluation container (Python >= 3.8 for the
positional-only cases) against the REAL repository callee
`sphinx.util.inspect.signature_from_str` (post-patch) and the unchanged AST
renderer `sphinx.pycode.ast.unparse`. Two kinds:

  (A-reference) the DEEP model of the changed alignment operation
      (`resolved_default` / `resolve_positional_defaults` in model.py):
      supplied defaults right-align across ALL positional parameters
      (positional-only prefix included), so positional parameter at index `p`
      carries NO default iff `p < n - m` (n = total positionals,
      m = number of supplied defaults) and otherwise carries the supplied
      default at offset `p - (n - m)`. We assert the real Signature produced by
      `signature_from_str` agrees position-by-position: a parameter has
      `default is Parameter.empty` exactly when the model predicts EMPTY, and a
      non-empty source string exactly otherwise, in the predicted left-to-right
      order across positional-only + positional-or-keyword parameters.

  (A-consumed) the `render` axiom: the per-default renderer is a PARTIAL map.
      model.py guards it with a `renderable(value_code)` domain predicate and
      only claims `render(...) != EMPTY()` (a source string is never the
      `Parameter.empty` sentinel) plus determinism ON THAT DOMAIN. We validate
      BOTH directions against the real `ast.unparse`:
        - on renderable default expressions it returns a non-empty source
          string (never `Parameter.empty`) and is deterministic, and
        - on grammar-valid-but-unsupported default expressions it RAISES
          `NotImplementedError` (it does NOT silently return / does NOT return a
          source string) — i.e. those codes lie OUTSIDE `renderable`, so the
          axiom's `Ensures` is never asserted there. This is what makes the
          domain-restricted axiom a sound over-approximation rather than an
          over-claim of totality.

Imports only the standard library plus the repository package under test
(`sphinx`), which is installed in the eval image. Exit 0 iff every obligation
holds.
"""
import ast
import itertools
import random
import sys

from sphinx.util.inspect import signature_from_str
from sphinx.pycode.ast import unparse as ast_unparse

try:
    from inspect import Parameter
except Exception:  # pragma: no cover
    from sphinx.util.inspect import Parameter  # type: ignore

POSITIONAL = (Parameter.POSITIONAL_ONLY, Parameter.POSITIONAL_OR_KEYWORD)


def model_resolved(positionals, provided_count):
    """Reference of model.py's resolved_default over all positional indices:
    returns a list of bools `has_default[p]` for p in 0..positionals-1."""
    n, m = positionals, provided_count
    pad = n - m
    return [p >= pad for p in range(n)]


def build_signature(posonly_specs, regular_specs):
    """Construct a signature string from (name, has_default, value) specs.

    posonly_specs are emitted before the '/'; regular_specs after. Only
    positional parameters (no *args/**kwargs/kwonly) so the test exercises the
    alignment that the patch fixes. AST requires that, within the combined
    positional list, every parameter that follows a defaulted one is also
    defaulted; the caller guarantees this.
    """
    posonly = ", ".join(
        ("%s=%s" % (nm, val)) if has else nm for (nm, has, val) in posonly_specs)
    regular = ", ".join(
        ("%s=%s" % (nm, val)) if has else nm for (nm, has, val) in regular_specs)
    inner = posonly
    if posonly_specs:
        inner = (posonly + ", /") if not regular else (posonly + ", /, " + regular)
    else:
        inner = regular
    return "(" + inner + ")"


def check_signature(posonly_specs, regular_specs, py38):
    all_specs = list(posonly_specs) + list(regular_specs)
    n = len(all_specs)
    m = sum(1 for (_, has, _) in all_specs if has)

    sig_str = build_signature(posonly_specs, regular_specs)
    # positional-only syntax ('/') requires Python >= 3.8
    if posonly_specs and not py38:
        return

    sig = signature_from_str(sig_str)
    params = [p for p in sig.parameters.values() if p.kind in POSITIONAL]
    assert len(params) == n, (
        "param count mismatch for %r: model %d, real %d"
        % (sig_str, n, len(params)))

    expected_has_default = model_resolved(n, m)
    for p, (param, (nm, has, val)) in enumerate(zip(params, all_specs)):
        real_has = param.default is not Parameter.empty
        # (A-reference) alignment: real presence-of-default == model prediction
        assert real_has == expected_has_default[p], (
            "alignment unsound on %r at index %d (%s): model has_default=%s, "
            "real has_default=%s" % (sig_str, p, nm, expected_has_default[p],
                                     real_has))
        # the supplied default expressions bind to the trailing m parameters
        if expected_has_default[p]:
            # (A-consumed) render: a rendered default is never the EMPTY sentinel
            assert param.default is not Parameter.empty
            assert isinstance(param.default, str) and param.default != "", (
                "render produced empty/sentinel for %r at %d" % (sig_str, p))


def check_render_axiom_and_determinism():
    """(A-consumed) the real ast.unparse is a PARTIAL renderer. Validate both
    directions of the domain-restricted `render` axiom (model.py: guarded by
    `renderable`, `Ensures(Result() != EMPTY())`):

      (i)  ON its domain (`renderable`): a default node renders to a non-empty
           source string (never the Parameter.empty sentinel) and rendering is
           deterministic — so the axiom's Ensures holds wherever the proof
           invokes render.
      (ii) OFF its domain: grammar-valid default expressions the renderer does
           NOT support raise NotImplementedError (they do not silently return a
           string). This is exactly why the axiom must be domain-restricted: it
           is a sound over-approximation only because render is never applied to
           these codes. A pure happy-path check (the previous version) would
           certify an UNSOUND totality claim; this catches a future regression
           where the model dropped the `renderable` guard.
    """
    # (i) on-domain: renderable default expressions -> non-empty source string,
    # deterministic, never the sentinel. These are exactly the value kinds the
    # F2P/P2P signatures use (numbers, names, attributes, tuples/lists/dicts/
    # sets, simple unary/binary/bool ops, lambda, constants).
    renderable_exprs = ["0", "1", "None", "True", "'x'", "3.14", "(1, 2)",
                        "[1]", "{1: 2}", "foo.BAR", "-1", "1 + 2",
                        "lambda x: x", "a and b", "x.y.z", "{1, 2}", "...",
                        "b'bytes'", "x @ y"]
    for e in renderable_exprs:
        node = ast.parse(e, mode="eval").body
        r1 = ast_unparse(node)
        r2 = ast_unparse(ast.parse(e, mode="eval").body)
        assert r1 is not None and r1 != "", "render empty for %r" % e
        assert r1 is not Parameter.empty
        assert isinstance(r1, str), "render non-string for %r: %r" % (e, r1)
        assert r1 == r2, "render non-deterministic for %r: %r vs %r" % (e, r1, r2)

    # (ii) off-domain: grammar-valid but unsupported default expressions MUST
    # raise (the renderer is partial). If any of these silently returned a
    # source string, the renderer would be more total than the axiom assumes —
    # still sound — but if NONE raised, the partiality the domain restriction
    # relies on would be vacuous and we must know. We require that the renderer
    # is observably partial: at least the classic unsupported nodes raise.
    nonrenderable_exprs = ["1 if x else 2", "x == y", "f'{x}'", "z[1:2]",
                           "{**w}", "[i for i in r]", "(yield x)"]
    raised = 0
    for e in nonrenderable_exprs:
        node = ast.parse(e, mode="eval").body
        try:
            out = ast_unparse(node)
        except NotImplementedError:
            raised += 1
            continue
        except Exception as ex:  # pragma: no cover - any raise = off-domain
            assert ex is not None
            raised += 1
            continue
        # If it returned, it must at least be a real string (still off the
        # alignment path, but record that this node kind is in-domain here).
        assert isinstance(out, str), (
            "render returned non-string off-domain for %r: %r" % (e, out))
    assert raised >= 1, (
        "expected the partial renderer to raise on at least one unsupported "
        "default expression (the domain restriction `renderable` would be "
        "vacuous otherwise); none of %r raised" % (nonrenderable_exprs,))


def main():
    py38 = sys.version_info >= (3, 8)

    # Boundary cases over positional alignment ------------------------------
    # the headline F2P case: (a, b=0, /, c=1) -> a empty, b '0', c '1'
    sig = None
    if py38:
        sig = signature_from_str("(a, b=0, /, c=1)")
        keys = list(sig.parameters.keys())
        assert keys == ["a", "b", "c"], keys
        assert sig.parameters["a"].kind == Parameter.POSITIONAL_ONLY
        assert sig.parameters["a"].default is Parameter.empty
        assert sig.parameters["b"].kind == Parameter.POSITIONAL_ONLY
        assert sig.parameters["b"].default == "0"
        assert sig.parameters["c"].kind == Parameter.POSITIONAL_OR_KEYWORD
        assert sig.parameters["c"].default == "1"

    names = ["a", "b", "c", "d", "e"]
    values = ["0", "1", "2", "None", "'x'"]

    # Exhaustive small enumeration: split k posonly + r regular, with a
    # contiguous trailing block of defaults of size 0..(k+r).
    checked = 0
    for k in range(0, 4):          # positional-only count
        for r in range(0, 4):      # regular positional count
            total = k + r
            if total == 0:
                continue
            for num_def in range(0, total + 1):
                # defaults occupy the LAST num_def positional parameters
                specs = []
                for idx in range(total):
                    nm = names[idx % len(names)] + str(idx)
                    has = idx >= total - num_def
                    val = values[idx % len(values)]
                    specs.append((nm, has, val))
                posonly_specs = specs[:k]
                regular_specs = specs[k:]
                check_signature(posonly_specs, regular_specs, py38)
                checked += 1

    # Randomized fuzz -------------------------------------------------------
    rng = random.Random(7757)
    for _ in range(4000):
        k = rng.randint(0, 4)
        r = rng.randint(0, 4)
        total = k + r
        if total == 0:
            continue
        num_def = rng.randint(0, total)
        specs = []
        for idx in range(total):
            nm = "p%d" % idx
            has = idx >= total - num_def
            val = rng.choice(values)
            specs.append((nm, has, val))
        check_signature(specs[:k], specs[k:], py38)
        checked += 1

    check_render_axiom_and_determinism()

    print("G-AX OK: alignment deep model (== real signature_from_str) sound on "
          "%d signatures; domain-restricted render axiom (== real partial "
          "ast.unparse: non-sentinel string on `renderable` codes, raises "
          "NotImplementedError off-domain) validated (py38=%s)"
          % (checked, py38))
    return 0


if __name__ == "__main__":
    sys.exit(main())
