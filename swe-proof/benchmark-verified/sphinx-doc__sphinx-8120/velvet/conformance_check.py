#!/usr/bin/env python3
"""G-CONF differential conformance check for sphinx-doc__sphinx-8120 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region (`buildLocaleDirs`)
              transliterated to Python over the real repo types, via the
              mapping.md bijection (`List Dir` ↔ Python list; the `sysNone`
              sentinel ↔ Python `None`). The impl region is pure R/I list
              assembly — no A-tagged callee appears in the computed `out`
              (`resolve`/`sphinx.locale.init` is only in the spec lemmas and is
              validated separately by G-AX).
  * ORACLE  — `patch.diff`'s behaviour: the EXACT `locale_dirs` assembly
              statements of the patched `Sphinx._init_i18n`, read from the live
              (post-patch) source in-container via `inspect.getsource` and
              executed against the same mocked inputs. Reading the real patched
              source (not a hardcoded copy) keeps the oracle faithful to
              patch.diff under G-RESOLVE.

They must agree on every input. Exit 0 iff zero disagreements; any disagreement
is a mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image), stdlib only. The fuzz
seed is pinned (mapping.md §4) for a deterministic verdict.
"""
import ast
import inspect
import os
import random
import sys
import textwrap

SEED = 8120
N_FUZZ = 100_000


# --- the R/I shadow: Solution.lean buildLocaleDirs, transliterated -----------
def shadow_build(repo_dirs, sys_none, package_locale):
    """buildLocaleDirs (repoDirs) (sysNone) (packageLocale), transliterated:
        let mut localeDirs := [sysNone]
        localeDirs := localeDirs ++ repoDirs
        localeDirs := localeDirs ++ [packageLocale]
    i.e. ensures out = sysNone :: (repoDirs ++ [packageLocale]).
    Per mapping.md §2 the Lean `sysNone` sentinel ↔ Python `None`."""
    locale_dirs = [sys_none]
    locale_dirs = locale_dirs + list(repo_dirs)
    locale_dirs = locale_dirs + [package_locale]
    return locale_dirs


# --- the oracle: the patched _init_i18n's locale_dirs assembly ---------------
def _extract_assembly_stmts():
    """Pull the `locale_dirs` assembly statements out of the LIVE (post-patch)
    Sphinx._init_i18n source. Returns a list of compiled ast statements that,
    executed in a namespace defining `repo`, `path`, `package_dir`, produce
    `locale_dirs`. Raises if the patched assembly cannot be located."""
    from sphinx.application import Sphinx
    src = inspect.getsource(Sphinx._init_i18n)
    src = textwrap.dedent(src)
    tree = ast.parse(src)
    func = tree.body[0]
    stmts = []
    capturing = False
    for node in ast.walk(func):
        pass
    # Walk the top-level body of the function (including nested under else:).
    def collect(body):
        out = []
        for n in body:
            if isinstance(n, ast.If):
                out.extend(collect(n.body))
                out.extend(collect(n.orelse))
            else:
                out.append(n)
        return out

    flat = collect(func.body)
    started = False
    for n in flat:
        # the assembly statements assign or augment `locale_dirs`
        targets_locale = False
        if isinstance(n, ast.Assign):
            for t in n.targets:
                if isinstance(t, ast.Name) and t.id == "locale_dirs":
                    targets_locale = True
        elif isinstance(n, ast.AugAssign):
            if isinstance(n.target, ast.Name) and n.target.id == "locale_dirs":
                targets_locale = True
        if targets_locale:
            started = True
            stmts.append(n)
        elif started:
            # stop at the first statement after the assembly block
            break
    if not stmts:
        raise RuntimeError("could not locate locale_dirs assembly in _init_i18n")
    return stmts


class _FakeRepo:
    def __init__(self, dirs):
        self._dirs = list(dirs)

    @property
    def locale_dirs(self):
        for d in self._dirs:
            yield d


def _make_oracle():
    from os import path as _path
    stmts = _extract_assembly_stmts()
    mod = ast.Module(body=stmts, type_ignores=[])
    ast.fix_missing_locations(mod)
    code = compile(mod, "<assembly>", "exec")

    def oracle(repo_dirs, sys_none, package_dir_value):
        ns = {
            "path": _path,
            "package_dir": package_dir_value,
            "repo": _FakeRepo(repo_dirs),
            "List": list, "Optional": object,  # type-comment names harmless
        }
        exec(code, ns)
        return ns["locale_dirs"]

    return oracle


def fuzz_inputs(n, rng):
    pool = ["locale", "_locales", "src/locale", "/abs/locale", "a", "b", "c",
            "user_locale", "translations", "i18n", ".", "..", "x/y/z"]
    # boundary cases first
    yield []
    yield ["locale"]
    yield ["a", "b"]
    yield ["a", "b", "c", "d", "e"]
    yield ["dup", "dup"]
    for _ in range(n):
        k = rng.randint(0, 6)
        yield [rng.choice(pool) for _ in range(k)]


def main():
    rng = random.Random(SEED)
    package_dir = "/sphinx/pkg"            # stands in for sphinx.package_dir
    package_locale = os.path.join(package_dir, "locale")
    sys_none = None                         # mapping.md §2: sysNone ↔ None
    oracle = _make_oracle()

    disagreements = []
    count = 0
    for repo_dirs in fuzz_inputs(N_FUZZ, rng):
        count += 1
        shadow = shadow_build(repo_dirs, sys_none, package_locale)
        ref = oracle(repo_dirs, sys_none, package_dir)
        if shadow != ref:
            disagreements.append((repo_dirs, shadow, ref))
            if len(disagreements) >= 5:
                break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for inp, sh, orc in disagreements:
            print("  repo_dirs=%r shadow=%r oracle=%r" % (inp, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of buildLocaleDirs agrees with patch.diff "
          "behaviour (patched _init_i18n assembly) on %d inputs (seed=%d), "
          "0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
