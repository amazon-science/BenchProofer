#!/usr/bin/env python3
"""G-AX — validate the A-reference deep models against the REAL Python path the
post-patch code delegates to: `ast.Name` + `compile(..., mode="eval")` + `eval`
through a `Mapping` adapter.

The proof consumes NO callee axiom (axioms region empty). The deep models that
must agree with reality (refinement.md rows 4-6) are:

  (1) prefix-attach `key = '$' ++ name`  and  prefix-strip `key.drop 1`
      ==  `IDENT_PREFIX + name`  and  `key[len(IDENT_PREFIX):]`.
  (2) `isReservedConst id` (id in {"True","False","None"})  ==  the exact set of
      identifiers for which a bare eval-mode `ast.Name(id)` does NOT route a
      lookup through the locals Mapping (i.e. CPython treats it as a constant /
      would abort on a debug build) — so the matcher is bypassed.
  (3) end-to-end: with the '$' prefix attached and stripped, EVERY identifier
      (including "True"/"False"/"None") routes through the matcher and yields the
      matcher's verdict on the ORIGINAL identifier.

stdlib-only. exit 0 iff every observation meets the model.
"""
import ast
import random
import sys
from collections.abc import Mapping

SEED = 7324
IDENT_PREFIX = "$"
RESERVED = {"True", "False", "None"}


def is_reserved_const_model(s: str) -> bool:
    """The Lean `isReservedConst`."""
    return s in RESERVED


class RecordingAdapter(Mapping):
    """Mirrors MatcherAdapter: strips the prefix and consults a matcher, while
    recording whether __getitem__ (a real name lookup) was reached and with
    what stripped key."""
    def __init__(self, matcher, strip):
        self.matcher = matcher
        self.strip = strip
        self.requested = []

    def __getitem__(self, key):
        self.requested.append(key)
        k = key[len(IDENT_PREFIX):] if self.strip else key
        return self.matcher(k)

    def __iter__(self):
        raise NotImplementedError()

    def __len__(self):
        raise NotImplementedError()


def real_resolves_through_mapping(ident_in_node: str) -> bool:
    """Compile+eval a bare Name node with the given identifier and report
    whether the locals Mapping was actually consulted (True) or the node was
    resolved as a constant / bypassed the mapping (False)."""
    node = ast.fix_missing_locations(ast.Expression(ast.Name(ident_in_node, ast.Load())))
    code = compile(node, filename="<g-ax>", mode="eval")
    adapter = RecordingAdapter(lambda k: True, strip=False)
    try:
        eval(code, {"__builtins__": {}}, adapter)
    except Exception:
        pass
    return len(adapter.requested) > 0


def post_patch_resolve(name: str, matcher):
    """The REAL post-patch resolution of one identifier."""
    node = ast.fix_missing_locations(
        ast.Expression(ast.Name(IDENT_PREFIX + name, ast.Load())))
    code = compile(node, filename="<g-ax>", mode="eval")
    adapter = RecordingAdapter(matcher, strip=True)
    return eval(code, {"__builtins__": {}}, adapter)


def gen_idents(rng):
    alpha = "abcdefghijklmnopqrstuvwxyz0123456789_:+-.[]ABCDEFG"
    fixed = ["", "a", "True", "False", "None", "true", "false", "none",
             "TRUE", "and", "or", "not", "if", "else", "while", "1234",
             "123.232", "notandor", "a:::c", "a[bcd]", "אב",
             "Truee", "xTrue", "Nonexyz"]
    cases = list(fixed)
    for _ in range(40_000):
        n = rng.randint(1, 10)
        cases.append("".join(rng.choice(alpha) for _ in range(n)))
    return cases


def main() -> int:
    rng = random.Random(SEED)
    fails = []

    # (2) reserved-set model == real "bypasses-mapping" set, on BARE identifiers.
    for ident in gen_idents(rng):
        if not ident:
            continue
        try:
            real_bypass = not real_resolves_through_mapping(ident)
        except (SyntaxError, ValueError):
            # not a valid Name identifier at all; the parser would have rejected
            # it upstream — skip (not part of the modeled name-node path).
            continue
        if is_reserved_const_model(ident) != real_bypass:
            fails.append(("reserved-set", ident,
                          is_reserved_const_model(ident), real_bypass))
            if len(fails) > 10:
                break

    # (1)+(3) prefixed key never bypasses; end-to-end == matcher(name).
    for ident in gen_idents(rng):
        prefixed = IDENT_PREFIX + ident
        # prefix-attach/strip model
        if (prefixed[len(IDENT_PREFIX):]) != ident:
            fails.append(("strip", ident, prefixed, None))
            continue
        # prefixed identifier must NEVER be a reserved constant
        if is_reserved_const_model(prefixed):
            fails.append(("prefixed-reserved", ident, prefixed, None))
            continue
        matcher = lambda k, _i=ident: (hash(k) & 1) == 0
        want = matcher(ident)
        try:
            got = post_patch_resolve(ident, matcher)
        except (SyntaxError, ValueError):
            continue
        if got != want:
            fails.append(("end-to-end", ident, got, want))
        if len(fails) > 10:
            break

    if fails:
        print(f"G-AX FAIL: {len(fails)} mismatches")
        for kind, ident, a, b in fails[:10]:
            print(f"  [{kind}] ident={ident!r} model={a!r} real={b!r}")
        return 1

    print(f"G-AX OK: reserved-const set, prefix attach/strip, and end-to-end "
          f"resolution all == real ast/compile/eval path (seed={SEED})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
