#!/usr/bin/env python3
"""G-CONF differential conformance check for sphinx-doc__sphinx-8593 (nagini).

SHADOW
------
The impl regions of `model.py`, copied VERBATIM with only the contract calls
(`Requires` / `Ensures` / `Acc` / `ToSeq`-as-contract markers) removed:

  * `member_effective_doc(attr_doc, value_doc)`  — modeled behaviour (1)
  * `keep_module_member(...)`                    — modeled behaviour (2)

plus the `@Pure` helpers the impl region calls, contracts stripped:
`is_private`, `in_private_selection` (and `effective_doc`, the pure spec
function, carried over unused-by-impl for completeness). `PSeq` is realized by
the immutable-tuple shim below and `ToSeq(list)` materializes one, exactly as in
the sibling nagini bundles.

`meta_class` is the bundle's single `@ContractOnly` axiom (mapping.md §3.1) and
therefore has NO body to copy: the shadow calls the REAL repo callee it
axiomatizes — `sphinx.util.docstrings.extract_metadata` followed by the
unchanged visibility branch of `filter_members`
(`sphinx/ext/autodoc/__init__.py:731-739`) — so the axiom is EXERCISED here
rather than assumed. Note the real branch tests `'private'` before `'public'`,
so a block carrying both markers classifies PRIVATE; that case is in the
boundary set.

ORACLE (called, never transliterated)
-------------------------------------
The REAL, gold-patched repository code, composed exactly as
`Documenter.document_members` composes it:

  1. `sphinx.ext.autodoc.ModuleDocumenter.get_module_members` — the method the
     gold patch ADDS (`sphinx/ext/autodoc/__init__.py`, new method at ~1046).
     This is the load-bearing edit: it attaches
     `docstring="\\n".join(attr_docs.get(('', name), []))` to each collected
     `ObjectMember`.
  2. `sphinx.ext.autodoc.Documenter.filter_members`
     (`sphinx/ext/autodoc/__init__.py:662`) — the unchanged consumer that
     prefers that attached docstring over the value's intrinsic `getdoc`
     (`:725-727` vs `:711`), derives `isprivate` from it (`:731-739`), and takes
     the retention decision (`:759-768`).

Both are driven on a duck-typed documenter exposing only what they read
(`self.object`, `self.analyzer.attr_docs` / `.find_attr_docs()`, `self.options`,
`self.objpath`, `self.get_attr`, `self.config.autodoc_inherit_docstrings`,
`self.parent`, `self.object_name`, `self.env.app is None`). No Sphinx app, no
build; the real functions run unmodified. `self.object` is a genuine
`types.ModuleType` carrying the case's member as a real attribute, so `dir` /
`safe_getattr` / `inspect.getannotations` behave as in production. The single
`ObjectMember` that step 1 collects for the case's member name is the list fed
to step 2 (`filter_members` decides members independently, one at a time), which
isolates the modeled per-member decision.

Behaviour (1) is observed by SPYING on the effective documentation the real
pipeline computes: `sphinx.ext.autodoc.extract_metadata` is temporarily
rebound to a recorder that forwards to the real callee and records its
argument — the exact `doc` the real patched code arrived at after the
attribute-doc-preferred-over-intrinsic-doc choice. Nothing is reimplemented;
the recorder only reads what the real function passes.

Behaviour (2) is observed as membership of the case's name in the list
`filter_members` returns (the `ret.append((membername, member, isattr))` at
`:807-808`, mapping.md §2's last row).

Type bridge (mapping.md §2, inverted)
-------------------------------------
The model carries documentation blocks as `List[int]` of Unicode code points
(Nagini bans `str` indexing) and specifications as `PSeq[int]`; the repo carries
`str`. Generation happens on the `str` side and each block is mapped to the
model side by `str_to_cps` / back by `cps_to_str`; a real `doc` of `None`
(no `__doc__`, or a non-`str` one the repo discards) bridges to `[]`. The
inline attribute documentation, which the repo stores as the LINE LIST
`attr_docs[('', name)]` and joins with `"\n"`, is fed as
`attr_doc_text.split("\n")` so the repo's join reproduces the model's
`attr_doc` byte-for-byte (including the trailing `""` line the real
`ModuleAnalyzer` appends, exercised via blocks ending in `"\n"`).
`private_mode` inverts to `self.options.private_members`: 0 -> `None`,
1 -> the repo's `ALL` sentinel, 2 -> an explicit name list (with
`name_selected` = name in that list). `name_underscored` is
`membername.startswith('_')` and `name_special` is pinned False (the model's
`Requires(not name_special)`) by never generating a reserved `__name__` form.

Input domain — every generated case satisfies the model's `Requires`
-------------------------------------------------------------------
`private_mode in {0,1,2}`; `len(attr_doc) > 0 or len(value_doc) > 0` (a
DOCUMENTED member — never both empty); `not name_special`. The domain is
INFINITE (documentation blocks are arbitrary text), so: 28 boundary cases
first — empty/absent attribute doc, absent vs present-but-empty `attr_docs`
key (the two distinct real keep branches, `:759` vs `:769`), each
`private_mode`, both `want_all` values, both markers, multi-line blocks,
indented blocks, the exact F2P shape (`_foo = None  #: :meta public:` under
`:members:` with no `:private-members:`, which must be RETAINED) and its
`:meta private:` mirror — then seeded fuzz to reach the count. Every impl
branch is taken: `member_effective_doc`'s two arms, `is_private`'s three arms,
`in_private_selection`'s three arms, and `keep_module_member`'s three arms.

>= 1e5 Requires-satisfying inputs. Pinned seed: 8593 (mapping.md, `## G-CONF`).

Exit 0 iff zero disagreements; a disagreement prints the input and both sides'
outputs and exits 1. stdlib + the in-image Sphinx only.
"""
import json
import random
import sys
import types

SEED = 8593
N_FUZZ = 100_000
MAX_REPORT = 5


# --- PSeq shim: immutable sequence with the ops the copied region uses --------

class PSeq:
    __slots__ = ("_t",)

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

    def __add__(self, other):
        return PSeq._wrap(self._t + other._t)

    def __len__(self):
        return len(self._t)

    def __getitem__(self, i):
        return self._t[i]

    def __eq__(self, other):
        return isinstance(other, PSeq) and self._t == other._t

    def __hash__(self):
        return hash(self._t)

    def __repr__(self):
        return "PSeq(%r)" % (self._t,)


def ToSeq(lst):
    """model.py's ToSeq: materialize a PSeq from a list."""
    return PSeq._wrap(lst)


# --- the @ContractOnly axiom: call the REAL callee it axiomatizes -------------
# model.py axioms region: meta_class(doc) in {NONE, PUBLIC, PRIVATE}.
NONE = 0
PUBLIC = 1
PRIVATE = 2


def meta_class(doc):
    """`@Pure @ContractOnly` in model.py — no body to copy. The real callee is
    sphinx.util.docstrings.extract_metadata (sphinx/util/docstrings.py:23)
    followed by the unchanged visibility branch of filter_members
    (sphinx/ext/autodoc/__init__.py:731-739). `doc` is a PSeq[int] of code
    points; the real callee takes a str."""
    from sphinx.util.docstrings import extract_metadata
    metadata = extract_metadata(cps_to_str(doc))
    if 'private' in metadata:
        return PRIVATE
    elif 'public' in metadata:
        return PUBLIC
    else:
        return NONE


# --- model.py pure region, contracts stripped, otherwise verbatim ------------

def effective_doc(attr_doc, value_doc):
    if len(attr_doc) > 0:
        return attr_doc
    return value_doc


def is_private(name_underscored, doc):
    mc = meta_class(doc)
    if mc == PUBLIC:
        return False
    if mc == PRIVATE:
        return True
    return name_underscored


def in_private_selection(mode, selected):
    if mode == 0:
        return False
    if mode == 1:
        return True
    return selected


# --- model.py impl regions, VERBATIM (contract calls removed) -----------------

def member_effective_doc(attr_doc, value_doc):
    # impl-start
    if len(attr_doc) > 0:
        result = list(attr_doc)  # type: List[int]
    else:
        result = list(value_doc)
    return result
    # impl-end


def keep_module_member(name_underscored, name_special,
                       attr_doc, value_doc,
                       want_all, private_mode,
                       name_selected):
    # impl-start
    doc = member_effective_doc(attr_doc, value_doc)
    private = is_private(name_underscored, ToSeq(doc))
    if not want_all:
        keep = True
    elif not private:
        keep = True
    else:
        keep = in_private_selection(private_mode, name_selected)
    return keep
    # impl-end


# --- type bridge (mapping.md section 2) --------------------------------------

def str_to_cps(s):
    """str documentation block -> List[int] of Unicode code points. A real
    doc of None (absent/non-str __doc__, discarded by the repo) -> []."""
    if s is None:
        return []
    return [ord(c) for c in s]


def cps_to_str(cps):
    """List[int]/PSeq[int] of code points -> str."""
    return "".join(chr(cps[i]) for i in range(len(cps)))


# --- ORACLE: duck-typed carriers exposing only what the real code reads -------

class _Analyzer:
    """Stand-in for ModuleAnalyzer: get_module_members reads `.attr_docs`,
    filter_members calls `.find_attr_docs()`. Same dict, as in the real
    analyzer (sphinx/pycode/__init__.py:186-189)."""

    def __init__(self, attr_docs):
        self.attr_docs = attr_docs

    def find_attr_docs(self):
        return self.attr_docs


class _Config:
    def __init__(self):
        # the repo default; irrelevant here (doc is never None-and-inherited)
        self.autodoc_inherit_docstrings = True


class _Env:
    # filter_members guards its autodoc-skip-member hook with `if self.env.app`
    app = None


class _FakeDocumenter:
    """Exposes exactly the attributes the two real methods read."""

    def __init__(self, obj, analyzer, options, object_name):
        from sphinx.util.inspect import safe_getattr
        self.object = obj
        self.analyzer = analyzer
        self.options = options
        self.objpath = []            # module documenter -> namespace ''
        self.get_attr = safe_getattr
        self.config = _Config()
        self.parent = None
        self.object_name = object_name
        self.env = _Env()
        self.fullname = "target.fake_module"


def _make_module(name, value):
    mod = types.ModuleType("target.fake_module")
    setattr(mod, name, value)
    return mod


def _make_value(value_doc_text, doc_is_none):
    """A member value whose intrinsic documentation is `value_doc_text`.

    `doc_is_none` models the plain data constant whose `__doc__` the repo
    discards (`getdoc` -> None, or a non-str `__doc__`): both bridge to the
    model's empty `value_doc`."""
    def _member(name):
        pass
    _member.__doc__ = None if doc_is_none else value_doc_text
    return _member


def _make_options(want_all, private_mode, private_list):
    from sphinx.ext.autodoc import ALL, Options
    if private_mode == 0:
        priv = None
    elif private_mode == 1:
        priv = ALL
    else:
        priv = list(private_list)
    # Options is a dict/attribute hybrid: `options.private_members` reads the
    # 'private-members' key (sphinx/ext/autodoc/__init__.py:251-257).
    return Options({
        'members': ALL if want_all else [],
        'private-members': priv,
        'undoc-members': None,
        'exclude-members': None,
        'special-members': None,
        'inherited-members': None,
    })


def oracle(name, attr_docs, value, want_all, private_mode, private_list):
    """Run the REAL patched pipeline; return (kept, effective_doc_text)."""
    import sphinx.ext.autodoc as ad

    mod = _make_module(name, value)
    documenter = _FakeDocumenter(mod, _Analyzer(attr_docs),
                                _make_options(want_all, private_mode,
                                              private_list),
                                name)

    # step 1: the method the gold patch adds — attaches the attribute doc.
    members = ad.ModuleDocumenter.get_module_members(documenter)
    member = members[name]

    # step 2: the unchanged consumer, spied on to record the effective doc it
    # actually computed (the recorder forwards to the real callee).
    seen = []
    real_extract = ad.extract_metadata

    def _spy(doc):
        seen.append(doc)
        return real_extract(doc)

    ad.extract_metadata = _spy
    try:
        ret = ad.Documenter.filter_members(documenter, [member], want_all)
    finally:
        ad.extract_metadata = real_extract

    kept = any(entry[0] == name for entry in ret)
    eff = seen[-1] if seen else None
    return kept, eff


# --- one case -----------------------------------------------------------------

def check_case(case):
    (name, attr_doc_text, attr_key_present, value_doc_text, doc_is_none,
     want_all, private_mode, private_list) = case

    # --- model side: the abstract carrier ---
    attr_doc = str_to_cps(attr_doc_text) if attr_key_present else []
    value_doc = [] if doc_is_none else str_to_cps(value_doc_text)
    name_underscored = name.startswith('_')
    name_special = False
    name_selected = name in private_list

    # Requires of keep_module_member (model.py:128-140) — never route around it.
    assert private_mode in (0, 1, 2)
    assert len(attr_doc) > 0 or len(value_doc) > 0, case
    assert not name_special

    shadow_doc = member_effective_doc(attr_doc, value_doc)
    shadow_keep = keep_module_member(name_underscored, name_special,
                                     attr_doc, value_doc, want_all,
                                     private_mode, name_selected)

    # --- repo side: the concrete values (bridge inverted) ---
    attr_docs = {}
    if attr_key_present:
        attr_docs[('', name)] = attr_doc_text.split("\n")
    value = _make_value(value_doc_text, doc_is_none)

    real_keep, real_doc = oracle(name, attr_docs, value, want_all,
                                 private_mode, private_list)

    if shadow_keep != real_keep:
        return ("retention decision differs", case,
                {"shadow_keep": shadow_keep}, {"real_keep": real_keep})
    if cps_to_str(shadow_doc) != (real_doc or ""):
        return ("effective documentation differs", case,
                {"shadow_doc": cps_to_str(shadow_doc)},
                {"real_doc": real_doc})
    return None


# --- inputs -------------------------------------------------------------------

PUB = ":meta public:"
PRIV = ":meta private:"

NAME_POOL = ["foo", "_foo", "_PUBLIC_CONSTANT", "PRIVATE_CONSTANT",
             "_public_function", "private_function", "value", "_x", "Helper"]

DOC_POOL = [
    "", PUB, PRIV, PUB + "\n", PRIV + "\n",
    "a docstring().",
    "public_function is a docstring().\n\n" + PUB,
    "private_function is a docstring().\n\n" + PRIV,
    "summary\n\n" + PUB + "\n" + PRIV,
    "  " + PUB,
    "\n" + PUB + "\n",
    ":meta something:",
    "prose then\n" + PUB,
    ":param x: y",
    "line one\nsecond line",
    "None",
    " ",
]


def boundary_cases():
    """(name, attr_doc_text, attr_key_present, value_doc_text, doc_is_none,
        want_all, private_mode, private_list)"""
    c = []
    # The reported bug, verbatim: `_foo = None  #: :meta public:` documented
    # with :members: and no :private-members:. Must be RETAINED post-patch.
    c.append(("_foo", PUB + "\n", True, "", True, True, 0, []))
    c.append(("_PUBLIC_CONSTANT", PUB + "\n", True, "", True, True, 0, []))
    # its mirror: a public-named member marked private -> dropped under mode 0
    c.append(("PRIVATE_CONSTANT", PRIV + "\n", True, "", True, True, 0, []))
    # F2P shape via the value's own docstring (a function, no attribute doc)
    c.append(("_public_function", "", False,
              "public_function is a docstring().\n\n" + PUB, False,
              True, 0, []))
    c.append(("private_function", "", False,
              "private_function is a docstring().\n\n" + PRIV, False,
              True, 0, []))
    c.append(("_public_function", "", False,
              "public_function is a docstring().\n\n" + PUB, False,
              True, 2, ["_public_function"]))
    # both markers: the real branch tests 'private' first -> PRIVATE
    c.append(("_foo", "summary\n\n" + PUB + "\n" + PRIV, True, "", True,
              True, 1, []))
    c.append(("foo", "summary\n\n" + PUB + "\n" + PRIV, True, "", True,
              True, 0, []))
    # no marker: leading-underscore convention decides, x each private_mode
    for mode, plist in ((0, []), (1, []), (2, ["_foo"]), (2, ["other"])):
        c.append(("_foo", "a docstring().", True, "", True, True, mode, plist))
        c.append(("foo", "a docstring().", True, "", True, True, mode, plist))
    # want_all False: retained regardless of visibility
    c.append(("_foo", PRIV, True, "", True, False, 0, []))
    c.append(("_foo", "a docstring().", True, "", True, False, 0, []))
    # attribute doc PRESENT but empty vs key ABSENT: the two distinct real keep
    # branches (:759 attr_docs vs :769 fallback); intrinsic doc supplies the
    # marker in both, so member_effective_doc's second arm is taken.
    c.append(("_foo", "", True, PUB, False, True, 0, []))
    c.append(("_foo", "", False, PUB, False, True, 0, []))
    c.append(("_foo", "", True, PRIV, False, True, 1, []))
    c.append(("_foo", "", False, PRIV, False, True, 1, []))
    c.append(("_foo", "", True, "a docstring().", False, True, 0, []))
    c.append(("_foo", "", False, "a docstring().", False, True, 0, []))
    # attribute doc OVERRIDES the intrinsic doc (the precedence under spec)
    c.append(("_foo", PUB, True, PRIV, False, True, 0, []))
    c.append(("foo", PRIV, True, PUB, False, True, 0, []))
    # multi-line / indented / whitespace-only blocks
    c.append(("_foo", "line one\nsecond line", True, "", True, True, 0, []))
    c.append(("_foo", "  " + PUB, True, "", True, True, 0, []))
    c.append(("_foo", " ", True, "", True, True, 0, []))
    c.append(("_foo", "\n" + PUB + "\n", True, "", True, True, 0, []))
    # non-ASCII code points (the List[int] carrier is Unicode-wide)
    c.append(("_foo", "résumé ✓\n\n" + PUB, True, "", True,
              True, 0, []))
    return c


def random_case(rng):
    name = rng.choice(NAME_POOL)
    # keep the Requires: never both docs empty
    while True:
        attr_key_present = rng.random() < 0.6
        attr_doc_text = rng.choice(DOC_POOL) if attr_key_present else ""
        doc_is_none = rng.random() < 0.35
        value_doc_text = "" if doc_is_none else rng.choice(DOC_POOL)
        attr_doc = attr_doc_text if attr_key_present else ""
        value_doc = "" if doc_is_none else value_doc_text
        if attr_doc or value_doc:
            break
    want_all = rng.random() < 0.75
    private_mode = rng.choice((0, 1, 2))
    if private_mode == 2:
        k = rng.randint(0, 3)
        private_list = rng.sample(NAME_POOL, k)
    else:
        private_list = []
    return (name, attr_doc_text, attr_key_present, value_doc_text,
            doc_is_none, want_all, private_mode, private_list)


def main():
    try:
        import sphinx.ext.autodoc as ad
        assert hasattr(ad.ModuleDocumenter, "get_module_members"), (
            "ModuleDocumenter.get_module_members absent: the gold patch that "
            "adds it was not applied")
    except Exception as exc:
        print("G-CONF ERROR: cannot load the patched oracle: %r" % (exc,))
        print(json.dumps({"status": "error", "reason": repr(exc)}))
        return 2

    bad = []
    checked = 0
    bnd = boundary_cases()
    for case in bnd:
        d = check_case(case)
        checked += 1
        if d:
            bad.append(d)
            if len(bad) >= MAX_REPORT:
                break

    if not bad:
        rng = random.Random(SEED)
        for _ in range(N_FUZZ):
            case = random_case(rng)
            d = check_case(case)
            checked += 1
            if d:
                bad.append(d)
                if len(bad) >= MAX_REPORT:
                    break

    if bad:
        print("G-CONF FAIL: %d disagreement(s) over %d inputs" %
              (len(bad), checked))
        for what, case, shadow, real in bad:
            print("  %s" % what)
            print("    input  = (name=%r attr_doc=%r attr_key_present=%r "
                  "value_doc=%r doc_is_none=%r want_all=%r private_mode=%r "
                  "private_list=%r)" % case)
            print("    shadow = %r" % (shadow,))
            print("    real   = %r" % (real,))
        print(json.dumps({"status": "fail", "checked": checked,
                          "disagreements": len(bad), "seed": SEED}))
        return 1

    print("G-CONF OK: contract-stripped impl region of model.py "
          "(member_effective_doc + keep_module_member) agrees with the real "
          "gold-patched ModuleDocumenter.get_module_members -> "
          "Documenter.filter_members on %d Requires-satisfying inputs "
          "(%d boundary + %d fuzz, seed=%d), 0 disagreements."
          % (checked, len(bnd), N_FUZZ, SEED))
    print(json.dumps({"status": "pass", "checked": checked,
                      "boundary": len(bnd), "fuzz": N_FUZZ,
                      "disagreements": 0, "seed": SEED,
                      "oracle": "sphinx.ext.autodoc.ModuleDocumenter."
                                "get_module_members + Documenter."
                                "filter_members (called, patched)",
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
