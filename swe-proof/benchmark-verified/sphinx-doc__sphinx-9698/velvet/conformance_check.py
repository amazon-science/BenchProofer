#!/usr/bin/env python3
"""G-CONF differential conformance check for sphinx-doc__sphinx-9698 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region
              (`indexEntryText` / `indexText` / `rsplitDot` / `shownOwner`)
              transliterated to Python over the *real* repo types (`str`, the
              boolean `add_module_names`, and a four-way category tag), via the
              mapping.md bijection (`List Char` ↔ `str`, `MethodKind` ↔ the
              resolved option among classmethod/property/staticmethod/method).
  * ORACLE  — `patch.diff`'s behaviour: the patched
              `sphinx.domains.python.PyMethod.get_index_text` applied at
              base_commit (the real correctness oracle, G-RESOLVE). It reads
              `self.options` (which category flags are set) and
              `self.env.config.add_module_names`, and returns the index label.

The impl region has NO A-tagged content (no axiomatized callees); the whole
label is a pure per-character string computation, so the shadow is pure R/I.
They must agree on every input. Exit 0 iff zero disagreements; any disagreement
is a mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image), stdlib + sphinx
(already installed). The fuzz seed is pinned (mapping.md §4) for a deterministic
verdict.

NOTE on the gettext wrapper `_`: `get_index_text` returns `_('...') % (...)`.
With no message catalog installed, `_` is the identity translation, so the
returned label is exactly the `%`-formatted string. The oracle invokes the real
function, so whatever `_` does is captured on the oracle side; the shadow
reproduces only the format substitution. To keep the comparison about the format
string (the thing the patch changes) and not about an ambient catalog, the
oracle is run under the same no-catalog default the test harness uses.
"""
import random
import sys

SEED = 9698
N_FUZZ = 100_000

KINDS = ['classmethod', 'property', 'staticmethod', 'method']


# ---- SHADOW: transliteration of Solution.lean's impl region ----------------

def shadow_rsplit_dot(name):
    """rsplitDot: split at the LAST '.'; None when there is no '.'.
    Mirrors Python `name.rsplit('.', 1)` returning a 2-tuple only when a
    separator exists (otherwise the single-element split == no owner)."""
    idx = name.rfind('.')
    if idx < 0:
        return None
    return (name[:idx], name[idx + 1:])


def shadow_shown_owner(modname, owner, add_module_names):
    if modname != '' and add_module_names:
        return modname + '.' + owner
    return owner


def shadow_index_text(name, modname, add_module_names, kind):
    split = shadow_rsplit_dot(name)
    if split is not None:
        owner, member = split
        shown = shadow_shown_owner(modname, owner, add_module_names)
        if kind == 'classmethod':
            return '%s() (%s class method)' % (member, shown)
        elif kind == 'property':
            return '%s (%s property)' % (member, shown)
        elif kind == 'staticmethod':
            return '%s() (%s static method)' % (member, shown)
        else:  # 'method' (plain bound member)
            return '%s() (%s method)' % (member, shown)
    else:
        if modname != '':
            return '%s() (in module %s)' % (name, modname)
        return '%s()' % name


# ---- ORACLE: the real patched PyMethod.get_index_text ----------------------

def _make_oracle():
    """Build the ORACLE around the patched PyMethod.get_index_text.

    `get_index_text(modname, name_cls)` reads only `self.options` (the category
    flag) and `self.env.config.add_module_names`. We attach a minimal fake env
    and toggle the option dict per call. Importing the module exercises the
    *patched* repo source (the harness has applied patch.diff at base_commit
    before this runs).

    NOTE: at this sphinx version a bare `from sphinx.domains.python import ...`
    trips a circular import (`sphinx.addnodes` is only partially initialized when
    `sphinx.util.nodes` reaches back into it). Priming `sphinx.util.nodes` before
    `sphinx.addnodes` — the order the normal application bootstrap establishes —
    breaks the cycle. This is an import-ordering quirk of the package, unrelated
    to the behaviour under test."""
    import sphinx.util.nodes  # noqa: F401  (prime to break the import cycle)
    import sphinx.addnodes  # noqa: F401
    from types import SimpleNamespace
    from sphinx.domains.python import PyMethod

    # `get_index_text` reads ONLY `self.options` (the category flag dict) and
    # `self.env.config.add_module_names`. `env` on the real class is a read-only
    # @property (resolves `self.state.document.settings.env`), so we cannot bind
    # it on a constructed instance. Instead we call the UNBOUND method against a
    # duck-typed `self` exposing exactly those two attributes — the same patched
    # function body runs, with no other instance machinery touched.
    get_index_text = PyMethod.get_index_text

    def oracle(name, modname, add_module_names, kind):
        # Only the resolved category flag is set; the precedence
        # classmethod > property > staticmethod > (plain) is fixed in the real
        # function's if/elif chain, so a single flag is the faithful input.
        opts = {}
        if kind != 'method':
            opts[kind] = True
        fake_self = SimpleNamespace(
            options=opts,
            env=SimpleNamespace(config=SimpleNamespace(add_module_names=add_module_names)),
        )
        return get_index_text(fake_self, modname, (name, ''))

    return oracle


# ---- fuzzing ---------------------------------------------------------------

def rand_ident(rng):
    alpha = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_0123456789'
    n = rng.randint(1, 8)
    s = ''.join(rng.choice(alpha) for _ in range(n))
    # ensure non-empty leading char that is not a digit-only edge for realism
    return s if s else 'x'


def rand_name(rng):
    # 0..3 dotted components, occasionally with empty components / trailing dot
    style = rng.random()
    if style < 0.15:
        return rand_ident(rng)                              # bare name, no dot
    parts = [rand_ident(rng) for _ in range(rng.randint(2, 4))]
    name = '.'.join(parts)
    if rng.random() < 0.05:
        name = name + '.'                                   # trailing dot
    if rng.random() < 0.05:
        name = '.' + name                                   # leading dot
    return name


def rand_modname(rng):
    if rng.random() < 0.3:
        return ''                                           # no module
    parts = [rand_ident(rng) for _ in range(rng.randint(1, 3))]
    return '.'.join(parts)


def fuzz_inputs(n, rng):
    # boundary cases first (plan §4.1 step 4): the issue's scenario and the
    # discriminating category, plus the bare-name / no-module / module legs.
    yield ('Class.meth5', '', True, 'property')      # the issue: NO parens
    yield ('Class.meth5', '', True, 'method')        # plain: parens
    yield ('Class.meth5', '', True, 'classmethod')   # parens
    yield ('Class.meth5', '', True, 'staticmethod')  # parens
    yield ('Class.bar', 'mod', True, 'property')     # module shown -> prefixed owner
    yield ('Class.bar', 'mod', False, 'property')    # module present, names off
    yield ('bar', 'mod', True, 'property')           # unqualified + module
    yield ('bar', '', True, 'property')              # unqualified, no module
    yield ('A.B.C.meth', 'm.n', True, 'property')    # deep dotted name
    yield ('Class.meth5', '', True, 'method')
    for _ in range(n):
        name = rand_name(rng)
        modname = rand_modname(rng)
        add_module_names = rng.random() < 0.6
        kind = rng.choice(KINDS)
        yield (name, modname, add_module_names, kind)


def main():
    rng = random.Random(SEED)
    oracle = _make_oracle()
    disagreements = []
    count = 0
    for name, modname, add_module_names, kind in fuzz_inputs(N_FUZZ, rng):
        count += 1
        shadow = shadow_index_text(name, modname, add_module_names, kind)
        orc = str(oracle(name, modname, add_module_names, kind))
        if shadow != orc:
            disagreements.append((name, modname, add_module_names, kind, shadow, orc))
            if len(disagreements) >= 5:
                break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for nm, md, am, k, sh, orc in disagreements:
            print("  name=%r modname=%r add_module_names=%r kind=%r shadow=%r oracle=%r"
                  % (nm, md, am, k, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of indexEntryText agrees with patch.diff "
          "behaviour on %d inputs (seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
