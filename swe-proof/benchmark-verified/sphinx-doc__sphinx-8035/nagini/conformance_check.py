#!/usr/bin/env python3
"""G-CONF differential conformance check for sphinx-doc__sphinx-8035 (nagini).

SHADOW  — the two `# impl-start` / `# impl-end` regions of model.py, copied
          VERBATIM with only the contract statements removed (there are no
          `Requires`/`Ensures` inside the regions; the stripped lines are the
          `Invariant(...)` blocks between the `# invariants-start` /
          `# invariants-end` markers and the two `Assert(...)` steps of
          `merge_selector_names`). The model IS Python, so nothing is
          transliterated or restructured: `keep_private_member` and
          `merge_selector_names` below are character-for-character the model's
          impl bodies, including the duplicated copy loop in the
          `members_is_all` branch. The `@Pure` helper the pure region defines
          (`documentable`) is copied too, minus its decorator. `PSeq`/`ToSeq`
          are the usual nagini carrier shims (immutable sequence over a tuple).
          There is NO `@ContractOnly` callee in this bundle (mapping.md §3), so
          nothing is axiomatized away — the whole impl is executable.

ORACLE  — the REAL patched repo functions, CALLED (not transliterated), with
          the gold patch already applied to /testbed by the gate:

            * `sphinx.ext.autodoc.Documenter.filter_members`
              (`sphinx/ext/autodoc/__init__.py:604`, keep branch at :664-688
              post-patch) — the function `keep_private_member` models. It is
              driven as an unbound function over a `SimpleNamespace` stand-in
              exposing exactly the attributes it reads (options / env / object
              / analyzer / get_attr / objpath), with `want_all=True`, no
              `autodoc-skip-member` listener (`env.app = None`), no
              exclude/special members and no analyzer, so control reaches the
              modeled `elif want_all and isprivate:` arm. The observable is the
              list of kept member names it returns.
            * `sphinx.ext.autodoc.merge_members_option`
              (the helper the gold patch adds at `__init__.py:141`) — the
              function `merge_selector_names` models. Called directly on an
              options dict; the observable is `options['members']` afterwards.
            * `sphinx.ext.autodoc.members_option` builds the three option
              states, `sphinx.util.inspect.getdoc` +
              `sphinx.util.docstrings.extract_metadata` derive each generated
              member's `has_doc` / `isprivate` (the surrounding context the
              patch does not touch), so the bridge's boolean inputs come from
              the real code path rather than from a re-implementation of it.

          Nothing is transliterated: every leg calls repo code.

BRIDGE  — mapping.md §2 inverted.
            * a member name is an `int` identity token in the model; token `t`
              maps to the distinct real name `NAMES[t]` (identifier-shaped,
              leading underscore so the real `isprivate` rule puts the member
              in the modeled private branch; the two F2P names
              `_public_function` / `private_function` are tokens 2 / 3).
            * the option trichotomy `None` / `ALL` / `List[str]` maps to
              `mode` 0 / 1 / 2 with the `names: List[int]` token payload; the
              concrete value is built by the REAL `members_option` (bare form
              -> `ALL`, comma string -> list).
            * `has_doc` / `undoc_members` / `filtered_inherited`: `has_doc`
              comes from the docstring given to the generated member (read back
              through the real `getdoc`); `undoc_members` is
              `options.undoc_members`; `filtered_inherited` is realized through
              the real nested `is_filtered_inherited_member` by making
              `self.object` a class whose MRO contains the class named by
              `options.inherited_members` — a member name absent from the
              subclass `__dict__` is a filtered inherited member, one present
              is not. The module-object variant (the F2P shape, `objtype
              module`) pins `filtered_inherited` to False.
            * for `merge_selector_names`, `List[int]` token lists map to the
              real `str` name lists of `options['members']` and
              `options['private-members']`; only ONE supplementary selector is
              supplied (`private-members`), matching the model's single `extra`
              parameter and avoiding the real helper's set-iteration order over
              the two `*-members` keys. In the `members_is_all` case the real
              helper returns early leaving `options['members'] is ALL`; the
              bridge checks exactly that (no name was appended) and compares
              the model's no-op result against the unchanged member list.

INPUTS  — Requires-satisfying by construction (`0 <= mode <= 2`; the list
          arguments are real lists). The modeled space is infinite (name lists
          are unbounded), so: an EXHAUSTIVE grid first — every option state x
          member-name token x docstring shape x `undoc_members` x
          inherited-filter variant, which takes each branch of both impl
          regions at least once, including the two discriminating shapes:
            (a) the exact F2P case — `private_function` documented with
                `:meta private:`, `private-members="_public_function"`: the
                patched code DROPS it while the pre-patch bool-flag code kept
                every documentable private member (so a container running
                unpatched code makes this script FAIL, not pass);
            (b) mode 1 (`ALL`) together with a filtered inherited member, where
                the patched order keeps the member — the asymmetry mapping.md
                §3.1 flags.
          then seeded fuzz (batched into multi-member `filter_members` calls)
          until >= 100000 keep decisions have been compared, plus 20000
          randomized merge inputs. Pinned seed: 8035 (recorded in mapping.md
          under `## G-CONF`).

Exit 0 iff zero disagreements. stdlib + the repo's own sphinx only.
"""
import random
import sys
import types
import warnings

warnings.simplefilter("ignore")

SEED = 8035
N_KEEP = 100_000          # keep-decision comparisons (>= 1e5)
N_MERGE = 20_000          # merge comparisons
BATCH = 8                 # members per filter_members call during fuzz

from sphinx.ext.autodoc import (ALL, Documenter,  # noqa: E402
                                members_option, merge_members_option)
from sphinx.util.docstrings import extract_metadata  # noqa: E402
from sphinx.util.inspect import getdoc, safe_getattr  # noqa: E402


# ---------------------------------------------------------------------------
# Nagini carrier shims: PSeq / ToSeq as plain executable Python.
# ---------------------------------------------------------------------------

class PSeq:
    """Immutable sequence shim for nagini's pure sequence type."""

    def __init__(self, *items):
        self._t = tuple(items)

    @classmethod
    def _wrap(cls, t):
        s = cls()
        s._t = tuple(t)
        return s

    def take(self, n):
        return PSeq._wrap(self._t[:n])

    def drop(self, n):
        return PSeq._wrap(self._t[n:])

    def __len__(self):
        return len(self._t)

    def __getitem__(self, i):
        return self._t[i]

    def __iter__(self):
        return iter(self._t)

    def __contains__(self, x):
        return x in self._t

    def __add__(self, other):
        return PSeq._wrap(self._t + other._t)

    def __eq__(self, other):
        return isinstance(other, PSeq) and self._t == other._t

    def __hash__(self):
        return hash(self._t)


def ToSeq(lst):
    return PSeq._wrap(lst)


# ---------------------------------------------------------------------------
# model.py pure region, copied over as plain functions (@Pure stripped).
# `keep_private` / `merged_at` are the spec-side pure functions and are not
# called from the impl regions; `documentable` is copied because the impl's
# guard is its body.
# ---------------------------------------------------------------------------

def documentable(has_doc, undoc_members):
    return has_doc or undoc_members


# ---------------------------------------------------------------------------
# SHADOW: model.py impl regions, VERBATIM (contract statements stripped).
# ---------------------------------------------------------------------------

def keep_private_member(mode, names, membername, has_doc, undoc_members,
                        filtered_inherited):
    # impl-start
    if not (has_doc or undoc_members):
        return False
    if mode == 0:
        return False
    if mode == 1:
        return True
    if filtered_inherited:
        return False
    return membername in ToSeq(names)
    # impl-end


def merge_selector_names(members_is_all, members, extra):
    # impl-start
    if members_is_all:
        result = []  # type: List[int]
        i = 0
        while i < len(members):
            result = result + [members[i]]
            i = i + 1
        return result
    result = []
    i = 0
    while i < len(members):
        result = result + [members[i]]
        i = i + 1
    j = 0
    while j < len(extra):
        m = extra[j]
        present = m in ToSeq(result)
        if not present:
            result = result + [m]
        j = j + 1
    return result
    # impl-end


# ---------------------------------------------------------------------------
# BRIDGE: name tokens <-> real member names (mapping.md §2).
# Token order is fixed; tokens 2/3 are the F2P names. Every name is
# identifier-shaped, single-underscore-prefixed (so the real isprivate rule
# classifies it private, i.e. inside the modeled branch) except token 3,
# `private_function`, which is private only via `:meta private:` metadata and
# is therefore only used as a membername together with that docstring.
# ---------------------------------------------------------------------------

NAMES = ["_a", "_b", "_public_function", "private_function",
         "_helper", "_x", "_secret", "_m0", "_m1", "_m2"]
TOKEN_OF = {n: t for t, n in enumerate(NAMES)}
# tokens usable as a membername with any docstring shape (underscore-private)
MEMBER_TOKENS = [0, 1, 2, 4, 5, 6, 7, 8, 9]

# docstring shapes: (label, doc) -> has_doc is read back from the real getdoc
DOC_PLAIN = "a plain docstring()."
DOC_META_PRIVATE = "private_function is a docstring().\n\n:meta private:\n"
DOC_SHAPES = [("none", None), ("plain", DOC_PLAIN), ("meta_private", DOC_META_PRIVATE)]

# option states: (mode, names_tokens, real_private_members)
def option_states():
    yield (0, [], None)                              # option absent -> None
    all_val = members_option(None)                   # bare form -> ALL
    assert all_val is ALL, "members_option(None) must be ALL"
    yield (1, [], all_val)
    for spec in ("", "_public_function", "_a,_b", "_public_function,_a",
                 "_secret", "_a,_b,_x,_helper"):
        lst = members_option(spec)                   # real converter
        assert isinstance(lst, list)
        yield (2, [TOKEN_OF[n] for n in lst], lst)


def make_member(doc):
    """A function object carrying `doc`, so the real getdoc/extract_metadata
    classify it exactly as the repo would."""
    def f(name):  # pragma: no cover - never called
        pass
    f.__doc__ = doc
    return f


def classify(name, member):
    """(has_doc, isprivate) computed by the REAL repo callees, mirroring the
    unchanged context of filter_members (getdoc + extract_metadata + the
    underscore rule). This is the bridge for the `has_doc` boolean and the
    in-domain guard for the modeled private branch."""
    doc = getdoc(member, safe_getattr, False, None, None)
    if not isinstance(doc, str):
        doc = None
    cls = safe_getattr(member, '__class__', None)
    if cls:
        if safe_getattr(cls, '__doc__', None) == doc:
            doc = None
    has_doc = bool(doc)
    metadata = extract_metadata(doc)
    if 'private' in metadata:
        isprivate = True
    elif 'public' in metadata:
        isprivate = False
    else:
        isprivate = name.startswith('_')
    return has_doc, isprivate


# ---------------------------------------------------------------------------
# ORACLE: the real patched Documenter.filter_members, driven directly.
# ---------------------------------------------------------------------------

class ConfBase:
    """Base class used to realize `is_filtered_inherited_member`: when
    `options.inherited_members == 'ConfBase'` and `self.object` is a subclass,
    a member name absent from the subclass `__dict__` is reported filtered."""


class FakeEnv:
    app = None                                  # no autodoc-skip-member listener
    config = types.SimpleNamespace(autodoc_inherit_docstrings=False)


def make_documenter(private_members, undoc_members, obj, inherited_members):
    self = types.SimpleNamespace()
    self.options = types.SimpleNamespace(
        exclude_members=None,                   # no :exclude-members:
        special_members=None,                   # no :special-members:
        members=ALL,                            # want_all path (bare :members:)
        private_members=private_members,
        undoc_members=undoc_members,
        inherited_members=inherited_members,
    )
    self.env = FakeEnv()
    self.parent = None
    self.object_name = None
    self.object = obj
    self.objpath = []
    self.analyzer = None                        # attr_docs = {}
    self.get_attr = safe_getattr
    self.objtype = "module"
    return self


_MODULE_OBJ = types.ModuleType("conf_target")


def oracle_kept(member_objs, private_members, undoc_members, variant, own_names):
    """Real patched filter_members -> the list of kept member names.

    variant 'module': self.object is a module -> is_filtered_inherited_member
    is always False (the F2P shape).
    variant 'class': self.object is a subclass of ConfBase and
    inherited_members == 'ConfBase' -> a member whose name is NOT in the
    subclass __dict__ is a filtered inherited member.
    """
    if variant == "module":
        obj = _MODULE_OBJ
        inherited = None
    else:
        ns = {n: make_member(DOC_PLAIN) for n in own_names}
        obj = type("ConfDerived", (ConfBase,), ns)
        inherited = "ConfBase"
    self = make_documenter(private_members, undoc_members, obj, inherited)
    ret = Documenter.filter_members(self, member_objs, True)   # want_all=True
    return [name for (name, _member, _isattr) in ret]


# ---------------------------------------------------------------------------
# One comparison step: a case = a batch of members + one option state.
# ---------------------------------------------------------------------------

def compare_case(case, disagreements):
    """`case` = (members, mode, names_tokens, private_members, undoc, variant,
    own_names) where `members` is a list of (token, doc). Returns the number of
    keep decisions compared (0 if a member fell outside the modeled private
    branch, which the generator never produces)."""
    (members, mode, names_tokens, private_members, undoc, variant,
     own_names) = case
    member_objs = []
    shadow_kept = []
    for (token, doc) in members:
        name = NAMES[token]
        obj = make_member(doc)
        has_doc, isprivate = classify(name, obj)
        if not isprivate:
            # outside the modeled decision (the model covers only the private
            # branch); the generator never emits these.
            raise AssertionError("non-private member generated: %r" % (name,))
        filtered_inherited = (variant == "class" and name not in own_names)
        member_objs.append((name, obj))
        if keep_private_member(mode, names_tokens, token, has_doc, undoc,
                               filtered_inherited):
            shadow_kept.append(name)
    kept = oracle_kept(member_objs, private_members, undoc, variant, own_names)
    if kept != shadow_kept:
        disagreements.append(
            ("keep", [NAMES[t] for (t, _d) in members],
             [d for (_t, d) in members], mode, names_tokens, undoc, variant,
             sorted(own_names), shadow_kept, kept))
    return len(members)


def keep_cases(rng):
    """Exhaustive grid first, then seeded fuzz batches."""
    states = list(option_states())

    # --- (a) the exact F2P shape: `private_function` (":meta private:") with
    # private-members="_public_function" must be DROPPED by the patched code.
    # Pre-patch (`keep = private_members and (has_doc or undoc)`) it was kept,
    # so this case alone refutes an unpatched container.
    f2p_pm = members_option("_public_function")
    yield ([(3, DOC_META_PRIVATE)], 2, [TOKEN_OF["_public_function"]], f2p_pm,
           False, "module", ())
    # ... and its positive counterpart: the named member IS kept.
    yield ([(2, DOC_PLAIN)], 2, [TOKEN_OF["_public_function"]], f2p_pm,
           False, "module", ())
    # --- (b) mode 1 (ALL) with a filtered inherited member: kept anyway.
    yield ([(0, DOC_PLAIN)], 1, [], ALL, False, "class", ())
    # the same member, mode 2 with its own name listed but filtered: dropped.
    yield ([(0, DOC_PLAIN)], 2, [TOKEN_OF["_a"]], members_option("_a"),
           False, "class", ())
    # ... and not filtered (name in the subclass __dict__): kept.
    yield ([(0, DOC_PLAIN)], 2, [TOKEN_OF["_a"]], members_option("_a"),
           False, "class", ("_a",))
    # --- empty member list, and an empty explicit selection list.
    yield ([], 2, [], members_option(""), False, "module", ())
    yield ([(0, DOC_PLAIN)], 2, [], members_option(""), False, "module", ())

    # --- exhaustive grid over the bounded projection of the modeled space ---
    for (mode, names_tokens, pm) in states:
        for token in MEMBER_TOKENS:
            for (_label, doc) in DOC_SHAPES:
                for undoc in (False, True):
                    for variant in ("module", "class"):
                        for own in ((), (NAMES[token],)):
                            if variant == "module" and own:
                                continue   # own_names is irrelevant there
                            yield ([(token, doc)], mode, names_tokens, pm,
                                   undoc, variant, own)
    # `private_function` (private via metadata) across every option state.
    for (mode, names_tokens, pm) in states:
        for undoc in (False, True):
            for variant in ("module", "class"):
                yield ([(3, DOC_META_PRIVATE)], mode, names_tokens, pm, undoc,
                       variant, ())

    # --- seeded fuzz: batched multi-member cases -----------------------------
    while True:
        mode, names_tokens, pm = states[rng.randrange(len(states))]
        undoc = rng.random() < 0.5
        variant = "module" if rng.random() < 0.5 else "class"
        k = rng.randint(0, BATCH)
        members = []
        for _ in range(k):
            token = rng.choice(MEMBER_TOKENS)
            doc = rng.choice(DOC_SHAPES)[1]
            members.append((token, doc))
        # a random subset of the batch's names sits in the subclass __dict__
        own = tuple({NAMES[t] for (t, _d) in members if rng.random() < 0.5})
        if variant == "module":
            own = ()
        yield (members, mode, names_tokens, pm, undoc, variant, own)


# ---------------------------------------------------------------------------
# The merge leg: shadow vs the REAL merge_members_option.
# ---------------------------------------------------------------------------

def compare_merge(members_is_all, members, extra, disagreements):
    shadow = merge_selector_names(members_is_all, list(members), list(extra))
    opts = {}
    if members_is_all:
        opts["members"] = ALL
    else:
        opts["members"] = [NAMES[t] for t in members]
    opts["private-members"] = [NAMES[t] for t in extra]
    merge_members_option(opts)
    if members_is_all:
        # the real helper returns early: nothing appended, members stays ALL.
        ok = opts["members"] is ALL
        real = list(members) if ok else None
    else:
        real = [TOKEN_OF[n] for n in opts["members"]]
    if shadow != real:
        disagreements.append(("merge", members_is_all, list(members),
                              list(extra), shadow, real))


def merge_cases(rng):
    pool = list(range(len(NAMES)))
    # boundary: no-op branch, empty members, empty extra, all-duplicate extra,
    # extra fully contained, extra fully new, repeated names inside extra.
    yield (True, [], [])
    yield (True, [0, 1], [2, 3])
    yield (False, [], [])
    yield (False, [], [0, 1])
    yield (False, [0, 1], [])
    yield (False, [0, 1], [0, 1])
    yield (False, [0, 1], [1, 2])
    yield (False, [0], [1, 1, 2, 2])
    yield (False, [0, 0], [0])
    for _ in range(N_MERGE):
        members_is_all = rng.random() < 0.34
        members = [rng.choice(pool) for _ in range(rng.randint(0, 4))]
        extra = [rng.choice(pool) for _ in range(rng.randint(0, 4))]
        yield (members_is_all, members, extra)


def main():
    rng = random.Random(SEED)
    disagreements = []

    n_keep = 0
    n_cases = 0
    for case in keep_cases(rng):
        n_keep += compare_case(case, disagreements)
        n_cases += 1
        if disagreements or n_keep >= N_KEEP:
            break

    n_merge = 0
    if not disagreements:
        for (mia, members, extra) in merge_cases(rng):
            compare_merge(mia, members, extra, disagreements)
            n_merge += 1
            if disagreements:
                break

    if disagreements:
        print("G-CONF FAIL: %d disagreement(s) after %d keep decisions / %d "
              "merge inputs (seed=%d):" % (len(disagreements), n_keep, n_merge,
                                           SEED))
        for d in disagreements:
            if d[0] == "keep":
                (_k, names, docs, mode, names_tokens, undoc, variant, own,
                 shadow, oracle) = d
                print("  keep: members=%r docs=%r mode=%r names=%r undoc=%r "
                      "variant=%r own=%r\n    shadow_kept=%r\n    oracle_kept=%r"
                      % (names, docs, mode, [NAMES[t] for t in names_tokens],
                         undoc, variant, own, shadow, oracle))
            else:
                (_k, mia, members, extra, shadow, real) = d
                print("  merge: members_is_all=%r members=%r extra=%r\n"
                      "    shadow=%r\n    real=%r"
                      % (mia, [NAMES[t] for t in members],
                         [NAMES[t] for t in extra], shadow, real))
        print('{"status": "fail", "keep_decisions": %d, "merge_inputs": %d, '
              '"disagreements": %d, "seed": %d}'
              % (n_keep, n_merge, len(disagreements), SEED))
        return 1

    print("G-CONF OK: model.py impl shadow (verbatim, contracts stripped) "
          "agrees with the REAL patched sphinx.ext.autodoc on %d "
          "filter_members keep decisions (%d driver calls) + %d "
          "merge_members_option inputs (seed=%d), 0 disagreements."
          % (n_keep, n_cases, n_merge, SEED))
    print('{"status": "pass", "keep_decisions": %d, "keep_cases": %d, '
          '"merge_inputs": %d, "disagreements": 0, "seed": %d, '
          '"oracle": "called: Documenter.filter_members + '
          'merge_members_option (patched sphinx.ext.autodoc)"}'
          % (n_keep, n_cases, n_merge, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
