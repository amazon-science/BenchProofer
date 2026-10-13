#!/usr/bin/env python3
"""G-CONF differential conformance check for sphinx-doc__sphinx-8035 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region transliterated
              to Python over the *real* repo types, via the mapping.md bijection
              (`List Member` ↔ list of synthetic members, `Sel` ↔
              `self.options.private_members ∈ {None, ALL, list[str]}`). No
              module-level axiom is consumed by the proof, so the shadow is pure
              R/I: it is `shownMembers`/`memberShown`/`selKeeps` transliterated.
  * ORACLE  — `patch.diff`'s behaviour: the REAL patched
              `Documenter.filter_members` keep-loop applied at base_commit (the
              real correctness oracle, G-RESOLVE), driven on the same synthetic
              members. The A-reference callees `getdoc` / `extract_metadata` /
              `members_option` are left as the real repo callees (members carry
              real `:meta private:` / `:meta public:` docstrings; the selection
              is parsed by the real `members_option`).

They must agree on every input in the modeled scenario (mapping.md §2: the
`want_all` case over function members, `objtype = module`, no exclude/special,
no skip-member listener). Exit 0 iff zero disagreements; any disagreement is a
mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image, gold patch applied),
stdlib + the repo's own sphinx only. The fuzz seed is pinned (mapping.md §5) for
a deterministic verdict.
"""
import random
import sys
import types
import warnings

warnings.simplefilter("ignore")

SEED = 8035
N_FUZZ = 100_000

from sphinx.ext.autodoc import Documenter, ALL, members_option  # noqa: E402
from sphinx.util.inspect import safe_getattr  # noqa: E402


# --- helpers to build synthetic members the real callees can classify --------

def make_member(doc):
    """A function object carrying `doc` as its docstring (so the real `getdoc`
    + `extract_metadata` classify it exactly as the repo would)."""
    def f(name):  # pragma: no cover - never called
        pass
    f.__doc__ = doc
    return f


class FakeOptions:
    def __init__(self, private_members, undoc_members):
        self.exclude_members = None        # no :exclude-members:
        self.special_members = None        # no :special-members:
        self.members = ALL                 # want_all path (bare :members:)
        self.private_members = private_members
        self.undoc_members = undoc_members
        self.inherited_members = None


class FakeEnv:
    app = None
    config = types.SimpleNamespace(autodoc_inherit_docstrings=False)


def make_documenter(private_members, undoc_members):
    self = types.SimpleNamespace()
    self.options = FakeOptions(private_members, undoc_members)
    self.env = FakeEnv()
    self.parent = None
    self.object_name = None
    self.object = types.ModuleType("m")    # module, not class -> no inherited filtering
    self.objpath = []
    self.analyzer = None                   # attr_docs = {} -> the function-member branches
    self.get_attr = safe_getattr
    self.objtype = "module"
    return self


def oracle_keep(members, private_members, undoc_members):
    """patch.diff behaviour: real patched filter_members, returns kept names."""
    self = make_documenter(private_members, undoc_members)
    ret = Documenter.filter_members(self, members, True)  # want_all=True
    return [name for (name, _member, _isattr) in ret]


# --- the R/I shadow: Solution.lean selectMembers / memberShown, transliterated

def shadow_keep(specs, sel, undoc_members):
    """shownMembers sel undoc (members) transliterated to Python.

    `specs` is a list of (name, is_restricted, has_doc) — the abstracted
    `Member` records (mapping.md §3). `sel` mirrors `Sel`:
      None        -> Sel.none
      ALL         -> Sel.all
      list[str]   -> Sel.only names
    """
    def sel_keeps(name):
        if sel is None:
            return False
        if sel is ALL:
            return True
        return name in sel          # list membership by value (List.contains)

    def member_shown(name, is_restricted, has_doc):
        if is_restricted:
            return (has_doc or undoc_members) and sel_keeps(name)
        return has_doc or undoc_members

    return [name for (name, is_restricted, has_doc) in specs
            if member_shown(name, is_restricted, has_doc)]


# --- the bijection: a synthetic member <-> its abstracted Member record ------
# Each generated member is given a real docstring so the REAL callees
# (getdoc/extract_metadata) reproduce (is_restricted, has_doc); the shadow's
# (is_restricted, has_doc) is computed by the SAME rule the repo uses, and the
# A-reference soundness of that rule is what axiom_check.py (G-AX) checks.

_DOC_PRIVATE = "a docstring().\n\n:meta private:\n"
_DOC_PUBLIC = "a docstring().\n\n:meta public:\n"
_DOC_PLAIN = "a plain docstring()."
_DOC_NONE = None


def member_variants(name):
    """Yield (member_obj, is_restricted, has_doc) for the doc-shapes that drive
    the classification, given a name (underscore-prefix matters)."""
    underscored = name.startswith("_")
    out = []
    # :meta private: -> restricted regardless of name; documented
    out.append((make_member(_DOC_PRIVATE), True, True))
    # :meta public: -> not restricted regardless of name; documented
    out.append((make_member(_DOC_PUBLIC), False, True))
    # plain docstring -> restricted iff underscored; documented
    out.append((make_member(_DOC_PLAIN), underscored, True))
    # no docstring -> restricted iff underscored; undocumented
    out.append((make_member(_DOC_NONE), underscored, False))
    return out


def fuzz_cases(n, rng):
    names = ["_public_function", "private_function", "_x", "foo", "_bar",
             "baz", "__weird", "_a", "b", "_helper"]

    # --- boundary cases first (the F2P scenario + edges) ----------------------
    # F2P: bare :members:, private-members="_public_function"
    yield (["_public_function", "private_function"], members_option("_public_function"), False)
    yield (["_public_function", "private_function"], ALL, False)      # blanket
    yield (["_public_function", "private_function"], None, False)     # default
    yield (["_public_function", "private_function"], members_option("private_function"), False)
    yield ([], None, False)
    yield ([], ALL, True)
    yield (["foo", "bar"], members_option("foo,bar"), False)
    yield (["_a", "_b"], members_option(""), False)   # empty arg -> [] -> Sel.only []
    yield (["_a"], members_option("_a, _a"), True)    # dup / spaces

    # --- randomized fuzz ------------------------------------------------------
    sel_choices = ["none", "all", "list", "empty"]
    for _ in range(n):
        k = rng.randint(0, 6)
        chosen = [rng.choice(names) for _ in range(k)]
        kind = rng.choice(sel_choices)
        if kind == "none":
            sel = None
        elif kind == "all":
            sel = ALL
        elif kind == "empty":
            sel = members_option("")          # -> []
        else:
            j = rng.randint(0, k) if k else 0
            picked = [rng.choice(names) for _ in range(j)]
            sel = members_option(",".join(picked)) if picked else members_option("")
        undoc = rng.choice([True, False])
        yield (chosen, sel, undoc)


def build_members(names, rng):
    """For each name pick one doc-variant; return (member_objs, specs) where
    member_objs feed the oracle and specs (name,is_restricted,has_doc) feed the
    shadow — the two faces of the same synthetic member (the bijection)."""
    member_objs = []
    specs = []
    for name in names:
        variants = member_variants(name)
        obj, is_restricted, has_doc = rng.choice(variants)
        member_objs.append((name, obj))
        specs.append((name, is_restricted, has_doc))
    return member_objs, specs


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for names, sel, undoc in fuzz_cases(N_FUZZ, rng):
        count += 1
        member_objs, specs = build_members(names, rng)
        oracle = oracle_keep(member_objs, sel, undoc)
        # translate sel (repo value) -> shadow's Sel encoding (mapping.md §3)
        if sel is None:
            shadow_sel = None
        elif sel is ALL:
            shadow_sel = ALL
        else:
            shadow_sel = list(sel)
        shadow = shadow_keep(specs, shadow_sel, undoc)
        if shadow != oracle:
            disagreements.append((names, sel, undoc, shadow, oracle))
            if len(disagreements) >= 5:
                break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for names, sel, undoc, sh, orc in disagreements:
            print("  names=%r sel=%r undoc=%r shadow=%r oracle=%r"
                  % (names, sel, undoc, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of selectMembers agrees with patch.diff "
          "(real patched filter_members) on %d inputs (seed=%d), 0 "
          "disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
