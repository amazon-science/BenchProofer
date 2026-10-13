#!/usr/bin/env python3
"""G-CONF differential conformance check for sphinx-doc__sphinx-9461 (nagini).

SHADOW — the `# impl-start` / `# impl-end` regions of model.py, copied VERBATIM
below with only the contract calls removed (`Requires`, `Ensures`,
`MustTerminate`, `Acc`, `ToSeq`-in-Ensures). Five regions are copied:
`property_qualifier_prefix`, `qualifies_for_property_doc`,
`property_option_block`, `member_retained_in_class_walk`,
`class_walk_option_block`. No renaming, no restructuring, no "simplification":
the code below is byte-for-byte the impl statements, so what is tested is the
model's impl, not a paraphrase of it. The `@Pure` region (`word_*`, `space`,
`line_*`, `expected_prefix`, `expected_option_block`) is copied too, on top of a
`PSeq` tuple shim, because the model's `Ensures` are phrased over those deep
models — every tier therefore diffs BOTH the impl result and the pure spec the
Ensures pin it to against the real function.

The two `@ContractOnly` callees have no body to copy, so per the contract they
call the REAL repo step mapping.md §1 says they axiomatize, rather than being
assumed:

  * `establish_documented(member_id)` -> the real post-admission step
    `PropertyDocumenter.import_object()` (autodoc/__init__.py:2674+ post-patch),
    the step that actually makes the documenter proceed with the admitted member
    and sets `self.isclassmethod`. The capability is recorded only if the real
    step returns True.
  * `establish_retained(member_id)` -> the real walk keep-append,
    `Documenter.filter_members(...)` (autodoc/__init__.py:718 post-patch)
    returning the member in `ret`. The capability is recorded only if the real
    walk actually kept the member.

`property_option_block` / `class_walk_option_block` assert their `Requires`
capability before emitting, so the gating is exercised: an emission the real
pipeline never reaches cannot be produced by the shadow either.

ORACLE — the REAL, gold-patched repo functions, CALLED (no transliteration).
The gate applies patch.diff to /testbed before this script runs and
PYTHONPATH=/testbed makes the patched modules importable:

  * site 1: `sphinx.domains.python.PyProperty.get_signature_prefix`
    (domains/python.py:868 post-patch), invoked on a real `PyProperty` instance
    (`object.__new__(PyProperty)`) whose `options` mapping is populated through
    the real `PyProperty.option_spec['abstractmethod'/'classmethod']` converters
    — so gold hunk 1 (registering the `classmethod` flag) is exercised too: an
    unregistered flag is a KeyError, not a silent pass.
  * site 2 discovery: `sphinx.ext.autodoc.PropertyDocumenter.can_document_member`
    (autodoc/__init__.py:2661 post-patch), called with a real `ClassDocumenter`
    parent whose `.object` is a real class defined in a real importable module.
  * site 2/3 emission: the real `PropertyDocumenter.import_object()` +
    `add_directive_header('')` (autodoc/__init__.py:2674 / :2700 post-patch).
    The only shim is on the OBSERVER: `add_line` is rebound to append to a list
    (that is how the emission is read off; the emission logic itself is the real
    method). `autodoc_typehints='none'` keeps the unmodeled `:type:` line out;
    the projection drops only the two lines the model does not model (the
    `.. py:property::` header and `   :module:`) and requires EVERY remaining
    emitted line to equal the modeled block, so an unexpected extra line is a
    disagreement rather than something filtered away.
  * site 3 retention: the real `Documenter.filter_members(members, True)` keep
    decision on a real `ClassDocumenter` over the real class members — which
    runs the patched `getdoc(member, ..., self.object, membername)` and hence the
    patched `sphinx.util.inspect.getdoc`/`isclassmethod` `cls,name` branches.

TYPE BRIDGE (mapping.md §2, inverted). Model side: `str` is `List[int]` of
Unicode code points and `PSeq[int]` in specs; each `'<flag>' in self.options` /
`inspect.isproperty(...)` / `isabstractmethod(...)` / docstring-resolves
predicate is a `bool`; `member_id` is an abstract int identity. Real side:
`str`. So `[ord(c) for c in s]` maps oracle -> carrier and
`''.join(chr(cp) for cp in xs)` maps carrier -> oracle; each model bool is
realized by constructing a member/option-set that makes the corresponding real
predicate true, and the realization is cross-checked by calling that real
predicate (`isproperty`, `isabstractmethod`, the `classmethod`-wrapping-property
test) and asserting it equals the flag the shadow was fed — a wrong bridge is a
reported disagreement, not a green run. `member_id` is bound to a real
(class, attribute name) pair by a registry.

FINITE DOMAIN, ENUMERATED EXHAUSTIVELY. Every modeled input is a tuple of
booleans (plus an abstract identity), so the whole modeled input space is finite
and far smaller than 1e5: 4 combos for site 1, 4 for the discovery decision, 4
for the emission block, 4 for retention. Each tier therefore ENUMERATES its cube
exhaustively first (a complete proof of agreement over the modeled domain, i.e.
strictly stronger than sampling), and then seeded fuzz re-samples the same space
to reach the >= 1e5 budget the contract asks for. Every branch of every impl
region is taken: prefix with/without each qualifier word; discovery qualifying
via the `is_property` branch, via the new class-level branch, and not at all;
emission with each option line present and absent; retention kept and dropped.

The F2P shape (`test_pyproperty`: a class-level property renders
`'class property '`; `test_properties` / autodoc `:classmethod:` emission) is in
the boundary set explicitly.

The (is_property, is_classlevel_property) corner (True, True) has no single real
attribute (a member cannot be both a plain property and a classmethod wrapping
one), but the real `can_document_member(member, membername, ...)` reads `member`
and `membername` independently, so the corner is realized honestly with a real
plain-property `member` and a `membername` naming a real classmethod-property.
The one modeled-domain restriction: the real function's pre-existing, unchanged
`isinstance(parent, ClassDocumenter)` guard is held true, because the model's
site 2 is "a member OF A CLASS is examined" — the guard is not part of the
modeled decision. The gold patch's new branch is exercised, not routed around.

Pinned seed: 9461 (recorded in mapping.md, `## G-CONF`).
Exit 0 iff zero disagreements; on disagreement the input and both outputs are
printed and the exit status is 1. stdlib + the repo under test only.
"""
import json
import os
import random
import sys
import tempfile

sys.path.insert(0, '/testbed')

SEED = 9461
N_FUZZ_PREFIX = 40_000
N_FUZZ_DISCOVERY = 20_000
N_FUZZ_EMISSION = 20_000
N_FUZZ_RETENTION = 10_000
N_FUZZ_WALK = 10_000


# ===========================================================================
# PSeq shim — Nagini's immutable pure sequence, the operations the pure region
# uses: construction from items, take, +, ==, len, [].
# ===========================================================================

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
        return "PSeq%r" % (self._t,)


def ToSeq(xs):
    """model.py's ToSeq(list) — materialize a List as a PSeq."""
    return PSeq._wrap(xs)


# ===========================================================================
# SHADOW — model.py's pure region, copied verbatim minus decorators.
# ===========================================================================

def word_abstract():
    # 'abstract'
    return PSeq(97, 98, 115, 116, 114, 97, 99, 116)


def word_class():
    # 'class'
    return PSeq(99, 108, 97, 115, 115)


def word_property():
    # 'property'
    return PSeq(112, 114, 111, 112, 101, 114, 116, 121)


def space():
    # ' '
    return PSeq(32)


def line_abstract():
    # '   :abstractmethod:'
    return PSeq(32, 32, 32, 58, 97, 98, 115, 116, 114, 97, 99, 116,
                109, 101, 116, 104, 111, 100, 58)


def line_class():
    # '   :classmethod:'
    return PSeq(32, 32, 32, 58, 99, 108, 97, 115, 115,
                109, 101, 116, 104, 111, 100, 58)


def expected_prefix(has_abstract, has_classlevel):
    result = space().take(0)  # type: PSeq[int]
    if has_abstract:
        result = result + word_abstract() + space()
    if has_classlevel:
        result = result + word_class() + space()
    return result + word_property() + space()


def expected_option_block(is_abstract, is_classlevel):
    result = space().take(0)  # type: PSeq[int]
    if is_abstract:
        result = result + line_abstract()
    if is_classlevel:
        result = result + line_class()
    return result


# ===========================================================================
# SHADOW — the @ContractOnly callees: they call the REAL repo step.
# ===========================================================================

_HELD_DOCUMENTED = set()
_HELD_RETAINED = set()
# member_id -> (real class, attribute name); populated by the driver.
_MEMBER_REGISTRY = {}


class ContractOnlyRefuted(Exception):
    """The real repo step the @ContractOnly callee axiomatizes did not happen,
    so the modeled capability could not be produced. This is a refutation of
    the axiomatization, reported as a disagreement."""


def establish_documented(member_id):
    """@ContractOnly in model.py (no body): the abstract 'register this member
    as documentable' effect. mapping.md §1 binds it to the documenter proceeding
    with the admitted member — the post-can_document_member-True step, i.e. the
    patched `PropertyDocumenter.import_object()`. Calling the real step here
    exercises the axiom instead of assuming it."""
    cls, name = _MEMBER_REGISTRY[member_id]
    doc = _make_property_documenter(cls, name)
    if not doc.import_object():
        raise ContractOnlyRefuted(
            "establish_documented(%r): the real PropertyDocumenter.import_object() "
            "refused the member %s.%s, so the real pipeline does NOT proceed to "
            "document it, yet the model's discovery decision qualified it."
            % (member_id, cls.__name__, name))
    _HELD_DOCUMENTED.add(member_id)


def establish_retained(member_id):
    """@ContractOnly in model.py (no body): the abstract 'keep this walked
    member' effect. mapping.md §1 binds it to the walk appending the member to
    `ret` — the post-keep-True step of the patched
    `Documenter.filter_members`. Calling the real walk here exercises the axiom
    instead of assuming it."""
    cls, name = _MEMBER_REGISTRY[member_id]
    if not _real_walk_keeps(cls, name):
        raise ContractOnlyRefuted(
            "establish_retained(%r): the real Documenter.filter_members() dropped "
            "the member %s.%s, so the real walk does NOT keep it, yet the model's "
            "retention decision retained it." % (member_id, cls.__name__, name))
    _HELD_RETAINED.add(member_id)


def documented_as_property(member_id):
    """@ContractOnly @Predicate in model.py: the unforgeable capability. Here it
    is the executable read of the capability set — only establish_documented
    writes to it."""
    return member_id in _HELD_DOCUMENTED


def retained_in_class_walk(member_id):
    """@ContractOnly @Predicate in model.py: the unforgeable capability. Only
    establish_retained writes to it."""
    return member_id in _HELD_RETAINED


class RequiresViolated(Exception):
    """A Requires the shadow depends on did not hold — the shadow refuses to
    compute, exactly as the model's precondition demands."""


# ===========================================================================
# SHADOW — the five impl regions, copied VERBATIM from model.py with only the
# contract calls (Requires/Ensures/MustTerminate/Acc) deleted.
# ===========================================================================

def property_qualifier_prefix(has_abstract, has_classlevel):
    # impl-start
    result = []  # type: List[int]
    if has_abstract:
        result = result + [97, 98, 115, 116, 114, 97, 99, 116]
        result = result + [32]
    if has_classlevel:
        result = result + [99, 108, 97, 115, 115]
        result = result + [32]
    result = result + [112, 114, 111, 112, 101, 114, 116, 121]
    result = result + [32]
    return result
    # impl-end


def qualifies_for_property_doc(is_property, is_classlevel_property, member_id):
    # impl-start
    if is_property:
        establish_documented(member_id)
        return True
    if is_classlevel_property:
        establish_documented(member_id)
        return True
    return False
    # impl-end


def property_option_block(is_abstract, is_classlevel_property, member_id):
    # Requires(documented_as_property(member_id)) — enforced, not assumed.
    if not documented_as_property(member_id):
        raise RequiresViolated(
            "property_option_block(%r): the documented_as_property capability is "
            "not held; the model forbids emitting an option block for a member "
            "the discovery step never established as documentable." % (member_id,))
    # impl-start
    result = []  # type: List[int]
    if is_abstract:
        result = result + [32, 32, 32, 58, 97, 98, 115, 116, 114, 97, 99, 116,
                           109, 101, 116, 104, 111, 100, 58]
    if is_classlevel_property:
        result = result + [32, 32, 32, 58, 99, 108, 97, 115, 115,
                           109, 101, 116, 104, 111, 100, 58]
    return result
    # impl-end


def member_retained_in_class_walk(is_classlevel_property, has_descriptive_text,
                                  member_id):
    # impl-start
    text_resolves = has_descriptive_text
    if text_resolves:
        establish_retained(member_id)
        return True
    return False
    # impl-end


def class_walk_option_block(is_abstract, is_classlevel_property, member_id):
    # Requires(retained_in_class_walk(member_id)) — enforced, not assumed.
    if not retained_in_class_walk(member_id):
        raise RequiresViolated(
            "class_walk_option_block(%r): the retained_in_class_walk capability "
            "is not held; the model forbids emitting a walk option block for a "
            "member the walk never retained." % (member_id,))
    # impl-start
    result = []  # type: List[int]
    if is_abstract:
        result = result + [32, 32, 32, 58, 97, 98, 115, 116, 114, 97, 99, 116,
                           109, 101, 116, 104, 111, 100, 58]
    if is_classlevel_property:
        result = result + [32, 32, 32, 58, 99, 108, 97, 115, 115,
                           109, 101, 116, 104, 111, 100, 58]
    return result
    # impl-end


# ===========================================================================
# Type bridge
# ===========================================================================

def to_codepoints(s):
    """real str -> model carrier List[int]."""
    return [ord(ch) for ch in s]


def from_codepoints(xs):
    """model carrier List[int] -> real str."""
    return ''.join(chr(cp) for cp in xs)


# ===========================================================================
# ORACLE plumbing — real patched repo objects.
# ===========================================================================

# A real, importable module holding real members of each shape the model's
# booleans denote. Written to a temp dir and imported for real; the real
# `import_object` path resolves `modname.Holder.<attr>` through it.
_MODULE_NAME = 'sbu_conf_9461_subject'
_MODULE_SRC = '''"""Subject module for the sphinx-doc__sphinx-9461 G-CONF check."""
import abc


class Holder(metaclass=abc.ABCMeta):
    """Holder of one member per modeled shape."""

    @property
    def p_plain(self):
        "descriptive text of p_plain"
        return 1

    @property
    def p_nodoc(self):
        return 1

    @property
    @abc.abstractmethod
    def p_abstract(self):
        "descriptive text of p_abstract"
        return 1

    @classmethod
    @property
    def c_plain(cls):
        "descriptive text of c_plain"
        return 2

    @classmethod
    @property
    def c_nodoc(cls):
        return 2

    @classmethod
    @property
    @abc.abstractmethod
    def c_abstract(cls):
        "descriptive text of c_abstract"
        return 2

    def plain_method(self):
        "descriptive text of plain_method"
        return 3

    def method_nodoc(self):
        return 3
'''


def _install_subject_module():
    d = tempfile.mkdtemp(prefix='sbu_conf_9461_')
    with open(os.path.join(d, _MODULE_NAME + '.py'), 'w') as fh:
        fh.write(_MODULE_SRC)
    sys.path.insert(0, d)
    mod = __import__(_MODULE_NAME)
    return mod


class _Registry:
    autodoc_attrgettrs = {}


class _App:
    registry = _Registry()

    def emit_firstresult(self, *a, **kw):
        return None

    def emit(self, *a, **kw):
        return []


class _Config:
    # The unmodeled `:type:` emission is off, so the observed line block is
    # exactly the modeled option block (mapping.md §1 models only the two
    # option lines).
    autodoc_typehints = 'none'
    autodoc_type_aliases = {}
    autodoc_mock_imports = []
    autodoc_warningiserror = False
    autodoc_inherit_docstrings = True
    autodoc_member_order = 'alphabetical'
    autodoc_class_signature = 'mixed'


class _Env:
    app = _App()
    config = _Config()

    def __init__(self):
        self.temp_data = {}

    def note_reread(self):
        pass


_ENV = _Env()
_MOD = None            # the real subject module
_PY_PROPERTY = None    # sphinx.domains.python.PyProperty
_AUTODOC = None        # sphinx.ext.autodoc
_SINSPECT = None       # sphinx.util.inspect


def _load_real():
    global _MOD, _PY_PROPERTY, _AUTODOC, _SINSPECT
    from sphinx.domains.python import PyProperty
    from sphinx.ext import autodoc as autodoc_mod
    from sphinx.util import inspect as sinspect
    _PY_PROPERTY = PyProperty
    _AUTODOC = autodoc_mod
    _SINSPECT = sinspect
    _MOD = _install_subject_module()


def _make_property_documenter(cls, name):
    """A real PropertyDocumenter positioned on the real member, with the real
    Documenter state `import_object`/`add_directive_header` read. Only `add_line`
    is rebound, to OBSERVE the emission."""
    doc = object.__new__(_AUTODOC.PropertyDocumenter)
    doc.env = _ENV
    doc.config = _ENV.config
    doc.options = _AUTODOC.Options(noindex=False)
    doc.directive = None
    doc.modname = _MODULE_NAME
    doc.objpath = [cls.__name__, name]
    doc.fullname = '%s.%s.%s' % (_MODULE_NAME, cls.__name__, name)
    doc.name = '%s::%s.%s' % (_MODULE_NAME, cls.__name__, name)
    doc.indent = ''
    doc.args = None
    doc.retann = None
    doc.object = None
    doc.object_name = None
    doc.parent = None
    doc.module = None
    doc.analyzer = None
    doc.emitted = []
    doc.add_line = lambda line, source, *lineno: doc.emitted.append(line)
    return doc


def _make_class_documenter(cls):
    """A real ClassDocumenter over the real class, with the real state
    `can_document_member` and `filter_members` read."""
    cd = object.__new__(_AUTODOC.ClassDocumenter)
    cd.env = _ENV
    cd.config = _ENV.config
    cd.options = _AUTODOC.Options(
        members=_AUTODOC.ALL, undoc_members=False, exclude_members=None,
        private_members=None, special_members=None, inherited_members=None,
        imported_members=False)
    cd.directive = None
    cd.modname = _MODULE_NAME
    cd.objpath = [cls.__name__]
    cd.fullname = '%s.%s' % (_MODULE_NAME, cls.__name__)
    cd.name = '%s::%s' % (_MODULE_NAME, cls.__name__)
    cd.indent = ''
    cd.object = cls
    cd.object_name = cls.__name__
    cd.parent = _MOD
    cd.module = _MOD
    cd.analyzer = None
    cd.doc_as_attr = False
    return cd


# --- site 1 oracle ---------------------------------------------------------

def oracle_signature_prefix(has_abstract, has_classlevel):
    """The REAL patched PyProperty.get_signature_prefix, on a real PyProperty
    instance whose `options` mapping is built through the real
    `PyProperty.option_spec` converters (so gold hunk 1's registration of the
    `classmethod` flag is exercised: an unregistered flag raises KeyError)."""
    options = {}
    if has_abstract:
        options['abstractmethod'] = _PY_PROPERTY.option_spec['abstractmethod'](None)
    if has_classlevel:
        options['classmethod'] = _PY_PROPERTY.option_spec['classmethod'](None)
    inst = object.__new__(_PY_PROPERTY)
    inst.options = options
    return _PY_PROPERTY.get_signature_prefix(inst, '')


# --- site 2 oracles --------------------------------------------------------

def oracle_can_document(cls, member, membername):
    """The REAL patched PropertyDocumenter.can_document_member, with a real
    ClassDocumenter parent (its unchanged `isinstance(parent, ClassDocumenter)`
    guard held true: the modeled domain is 'a member of a class')."""
    parent = _make_class_documenter(cls)
    return _AUTODOC.PropertyDocumenter.can_document_member(
        member, membername, False, parent)


_UNMODELED_LINE_PREFIXES = ('.. py:property:: ', '   :module: ')


def oracle_emitted_option_block(cls, name):
    """The REAL patched import_object() + add_directive_header('') option lines,
    projected to the modeled block: the directive header and `:module:` lines
    (not modeled by model.py) are dropped and EVERY other emitted line is kept,
    so an unexpected extra line disagrees rather than being filtered away.
    Returns (imported_ok, code points of the concatenated option lines)."""
    doc = _make_property_documenter(cls, name)
    if not doc.import_object():
        return False, None
    doc.add_directive_header('')
    lines = [ln for ln in doc.emitted
             if not ln.startswith(_UNMODELED_LINE_PREFIXES)]
    return True, to_codepoints(''.join(lines))


# --- site 3 oracle ---------------------------------------------------------

def _real_walk_keeps(cls, name):
    """The REAL patched Documenter.filter_members keep decision for one walked
    member (which runs the patched `getdoc(member, ..., self.object,
    membername)` and hence the patched isclassmethod/getdoc cls,name branches)."""
    cd = _make_class_documenter(cls)
    member = cls.__dict__[name]
    kept = cd.filter_members([(name, member)], True)
    return any(k[0] == name for k in kept)


# ===========================================================================
# The modeled member shapes and their real predicates (the bridge, checked)
# ===========================================================================
# (attribute name, is_property, is_classlevel_property, is_abstract,
#  has_descriptive_text) — the flags the shadow is fed. Each is cross-checked
# against the REAL predicate below, so a wrong bridge is reported, not hidden.
MEMBER_SHAPES = [
    ('p_plain',      True,  False, False, True),
    ('p_nodoc',      True,  False, False, False),
    ('p_abstract',   True,  False, True,  True),
    ('c_plain',      False, True,  False, True),
    ('c_nodoc',      False, True,  False, False),
    ('c_abstract',   False, True,  True,  True),
    ('plain_method', False, False, False, True),
    ('method_nodoc', False, False, False, False),
]


def _bridge_flags(cls, name):
    """Derive the model's booleans from the REAL predicates mapping.md §2 binds
    them to."""
    member = cls.__dict__[name]
    is_property = bool(_SINSPECT.isproperty(member))
    is_cls_prop = bool(isinstance(member, classmethod)
                       and _SINSPECT.isproperty(member.__func__))
    resolved = member.__func__ if is_cls_prop else member
    is_abstract = bool(_SINSPECT.isabstractmethod(resolved))
    doc = _SINSPECT.getdoc(member, allow_inherited=False, cls=cls, name=name)
    has_text = bool(isinstance(doc, str) and doc.strip())
    return is_property, is_cls_prop, is_abstract, has_text


# ===========================================================================
# Driver
# ===========================================================================

class Disagreements:
    def __init__(self, limit=8):
        self.items = []
        self.limit = limit
        self.n = 0

    def add(self, tier, inp, shadow, oracle, note=''):
        self.n += 1
        if len(self.items) < self.limit:
            self.items.append((tier, inp, shadow, oracle, note))

    def __bool__(self):
        return self.n > 0


def _reset_capabilities():
    _HELD_DOCUMENTED.clear()
    _HELD_RETAINED.clear()


# --- tier A: site 1, the qualifier prefix ---------------------------------

def tier_prefix(dis, rng):
    checked = 0
    cube = [(False, False), (True, False), (False, True), (True, True)]
    # F2P-observed forms (test_pyproperty): the class-level property renders
    # 'class property '.
    f2p = {
        (False, False): 'property ',
        (True, False): 'abstract property ',
        (False, True): 'class property ',
        (True, True): 'abstract class property ',
    }
    cases = list(cube) + [rng.choice(cube) for _ in range(N_FUZZ_PREFIX)]
    for has_abstract, has_classlevel in cases:
        checked += 1
        shadow = property_qualifier_prefix(has_abstract, has_classlevel)
        try:
            oracle = oracle_signature_prefix(has_abstract, has_classlevel)
        except KeyError as exc:
            dis.add('prefix', (has_abstract, has_classlevel), from_codepoints(shadow),
                    None, 'real option_spec is missing the flag %r' % (exc.args[0],))
            continue
        if from_codepoints(shadow) != oracle:
            dis.add('prefix', (has_abstract, has_classlevel),
                    from_codepoints(shadow), oracle)
            continue
        # the Ensures' deep model must agree with the real function too
        if ToSeq(shadow) != expected_prefix(has_abstract, has_classlevel):
            dis.add('prefix/spec', (has_abstract, has_classlevel),
                    from_codepoints(shadow),
                    from_codepoints(list(expected_prefix(has_abstract,
                                                         has_classlevel)._t)),
                    'impl disagrees with its own Ensures deep model')
        want = f2p.get((has_abstract, has_classlevel))
        if want is not None and oracle != want:
            dis.add('prefix/f2p', (has_abstract, has_classlevel), want, oracle,
                    'real prefix differs from the F2P-observed form')
    return checked


# --- tier B: site 2, the discovery decision -------------------------------

def tier_discovery(dis, rng):
    """Diff `qualifies_for_property_doc` against the real
    can_document_member over the full (is_property, is_classlevel_property)
    cube. The (True, True) corner is realized with a real plain-property
    `member` plus a `membername` naming a real classmethod-property, because
    the real function reads the two independently."""
    cls = _MOD.Holder
    # (label, member attr supplying `member`, attr supplying `membername`,
    #  is_property, is_classlevel_property, aligned?)
    combos = [
        ('plain-property',   'p_plain',      'p_plain',      True,  False, True),
        ('classlevel-prop',  'c_plain',      'c_plain',      False, True,  True),
        ('neither',          'plain_method', 'plain_method', False, False, True),
        ('both-corner',      'p_plain',      'c_plain',      True,  True,  False),
    ]
    checked = 0
    cases = list(combos) + [rng.choice(combos) for _ in range(N_FUZZ_DISCOVERY)]
    for label, member_attr, name_attr, is_prop, is_cls_prop, aligned in cases:
        checked += 1
        member = cls.__dict__[member_attr]
        # bridge check: the flags the shadow is fed are the real predicates
        real_is_prop = bool(_SINSPECT.isproperty(member))
        name_obj = cls.__dict__[name_attr]
        real_is_cls_prop = bool(isinstance(name_obj, classmethod)
                                and _SINSPECT.isproperty(name_obj.__func__))
        if (real_is_prop, real_is_cls_prop) != (is_prop, is_cls_prop):
            dis.add('discovery/bridge', label, (is_prop, is_cls_prop),
                    (real_is_prop, real_is_cls_prop),
                    'type bridge: the model flags do not match the real predicates')
            continue
        _reset_capabilities()
        member_id = 1000 + hash(label) % 1000
        _MEMBER_REGISTRY[member_id] = (cls, member_attr if aligned else name_attr)
        try:
            shadow = qualifies_for_property_doc(is_prop, is_cls_prop, member_id)
        except ContractOnlyRefuted as exc:
            dis.add('discovery/contract-only', label, True, False, str(exc))
            continue
        oracle = oracle_can_document(cls, member, name_attr)
        if shadow != bool(oracle):
            dis.add('discovery', (label, is_prop, is_cls_prop), shadow, bool(oracle))
            continue
        # the capability must be held exactly when the member qualified
        if documented_as_property(member_id) != shadow:
            dis.add('discovery/capability', (label, is_prop, is_cls_prop),
                    documented_as_property(member_id), shadow,
                    'documented_as_property not granted exactly on the '
                    'qualifying branch')
    return checked


# --- tier C: site 2, discovery -> gated option-line emission --------------

def tier_emission(dis, rng):
    """Diff the composed shadow (discovery decision, then the capability-gated
    `property_option_block`) against the composed real pipeline
    (can_document_member -> import_object -> add_directive_header)."""
    cls = _MOD.Holder
    checked = 0
    shapes = list(MEMBER_SHAPES)
    cases = shapes + [rng.choice(shapes) for _ in range(N_FUZZ_EMISSION)]
    for name, is_prop, is_cls_prop, is_abstract, _has_text in cases:
        checked += 1
        # bridge check against the real predicates
        r_prop, r_cls, r_abs, _r_text = _bridge_flags(cls, name)
        if (r_prop, r_cls, r_abs) != (is_prop, is_cls_prop, is_abstract):
            dis.add('emission/bridge', name, (is_prop, is_cls_prop, is_abstract),
                    (r_prop, r_cls, r_abs),
                    'type bridge: the model flags do not match the real predicates')
            continue
        _reset_capabilities()
        member_id = 2000 + shapes.index(
            (name, is_prop, is_cls_prop, is_abstract, _has_text))
        _MEMBER_REGISTRY[member_id] = (cls, name)
        try:
            qualified = qualifies_for_property_doc(is_prop, is_cls_prop, member_id)
        except ContractOnlyRefuted as exc:
            dis.add('emission/contract-only', name, True, False, str(exc))
            continue
        shadow_block = None
        if qualified:
            shadow_block = property_option_block(is_abstract, is_cls_prop, member_id)
        # oracle
        real_admits = bool(oracle_can_document(cls, cls.__dict__[name], name))
        if real_admits != qualified:
            dis.add('emission/discovery', name, qualified, real_admits)
            continue
        if not real_admits:
            # neither side emits anything; the shadow's Requires forbids it
            try:
                property_option_block(is_abstract, is_cls_prop, member_id)
            except RequiresViolated:
                continue
            dis.add('emission/gate', name, 'emitted without capability',
                    'real pipeline emits nothing',
                    'the shadow produced a block for a member never admitted')
            continue
        imported, oracle_block = oracle_emitted_option_block(cls, name)
        if not imported:
            dis.add('emission/import', name, qualified, False,
                    'real import_object() refused an admitted member')
            continue
        if shadow_block != oracle_block:
            dis.add('emission', (name, is_abstract, is_cls_prop),
                    from_codepoints(shadow_block), from_codepoints(oracle_block))
            continue
        if ToSeq(shadow_block) != expected_option_block(is_abstract, is_cls_prop):
            dis.add('emission/spec', (name, is_abstract, is_cls_prop),
                    from_codepoints(shadow_block),
                    from_codepoints(list(expected_option_block(
                        is_abstract, is_cls_prop)._t)),
                    'impl disagrees with its own Ensures deep model')
    return checked


# --- tier D: site 3, the walk retention decision --------------------------

def tier_retention(dis, rng):
    cls = _MOD.Holder
    checked = 0
    # the (is_classlevel_property, has_descriptive_text) cube, realized:
    shapes = [
        ('p_plain', False, True),
        ('p_nodoc', False, False),
        ('c_plain', True,  True),
        ('c_nodoc', True,  False),
    ]
    cases = list(shapes) + [rng.choice(shapes) for _ in range(N_FUZZ_RETENTION)]
    for name, is_cls_prop, has_text in cases:
        checked += 1
        r_prop, r_cls, _r_abs, r_text = _bridge_flags(cls, name)
        if (r_cls, r_text) != (is_cls_prop, has_text):
            dis.add('retention/bridge', name, (is_cls_prop, has_text),
                    (r_cls, r_text),
                    'type bridge: the model flags do not match the real '
                    'isclassmethod/getdoc predicates')
            continue
        _reset_capabilities()
        member_id = 3000 + shapes.index((name, is_cls_prop, has_text))
        _MEMBER_REGISTRY[member_id] = (cls, name)
        try:
            shadow = member_retained_in_class_walk(is_cls_prop, has_text, member_id)
        except ContractOnlyRefuted as exc:
            dis.add('retention/contract-only', name, True, False, str(exc))
            continue
        oracle = _real_walk_keeps(cls, name)
        if shadow != oracle:
            dis.add('retention', (name, is_cls_prop, has_text), shadow, oracle)
            continue
        if retained_in_class_walk(member_id) != shadow:
            dis.add('retention/capability', (name, is_cls_prop, has_text),
                    retained_in_class_walk(member_id), shadow,
                    'retained_in_class_walk not granted exactly on the retain '
                    'branch')
    return checked


# --- tier E: site 3, retention -> gated walk emission ---------------------

def tier_walk_emission(dis, rng):
    """Diff the composed shadow (retention decision, then the capability-gated
    `class_walk_option_block`) against the composed real walk
    (filter_members keep -> can_document_member -> import_object ->
    add_directive_header)."""
    cls = _MOD.Holder
    checked = 0
    shapes = [
        ('p_plain',    False, False, True),
        ('p_nodoc',    False, False, False),
        ('p_abstract', True,  False, True),
        ('c_plain',    False, True,  True),
        ('c_nodoc',    False, True,  False),
        ('c_abstract', True,  True,  True),
    ]
    cases = list(shapes) + [rng.choice(shapes) for _ in range(N_FUZZ_WALK)]
    for name, is_abstract, is_cls_prop, has_text in cases:
        checked += 1
        _r_prop, r_cls, r_abs, r_text = _bridge_flags(cls, name)
        if (r_cls, r_abs, r_text) != (is_cls_prop, is_abstract, has_text):
            dis.add('walk/bridge', name, (is_cls_prop, is_abstract, has_text),
                    (r_cls, r_abs, r_text),
                    'type bridge: the model flags do not match the real predicates')
            continue
        _reset_capabilities()
        member_id = 4000 + shapes.index((name, is_abstract, is_cls_prop, has_text))
        _MEMBER_REGISTRY[member_id] = (cls, name)
        try:
            retained = member_retained_in_class_walk(is_cls_prop, has_text, member_id)
        except ContractOnlyRefuted as exc:
            dis.add('walk/contract-only', name, True, False, str(exc))
            continue
        shadow_block = None
        if retained:
            shadow_block = class_walk_option_block(is_abstract, is_cls_prop, member_id)
        real_kept = _real_walk_keeps(cls, name)
        if real_kept != retained:
            dis.add('walk/retention', name, retained, real_kept)
            continue
        if not real_kept:
            try:
                class_walk_option_block(is_abstract, is_cls_prop, member_id)
            except RequiresViolated:
                continue
            dis.add('walk/gate', name, 'emitted without capability',
                    'real walk emits nothing',
                    'the shadow produced a walk block for a dropped member')
            continue
        imported, oracle_block = oracle_emitted_option_block(cls, name)
        if not imported:
            dis.add('walk/import', name, retained, False,
                    'real import_object() refused a retained member')
            continue
        if shadow_block != oracle_block:
            dis.add('walk', (name, is_abstract, is_cls_prop),
                    from_codepoints(shadow_block), from_codepoints(oracle_block))
            continue
        if ToSeq(shadow_block) != expected_option_block(is_abstract, is_cls_prop):
            dis.add('walk/spec', (name, is_abstract, is_cls_prop),
                    from_codepoints(shadow_block),
                    from_codepoints(list(expected_option_block(
                        is_abstract, is_cls_prop)._t)),
                    'impl disagrees with its own Ensures deep model')
    return checked


def main():
    try:
        _load_real()
    except Exception as exc:
        print('G-CONF ERROR: could not load the patched repo modules: %r' % (exc,))
        print(json.dumps({'status': 'error', 'reason': repr(exc)}))
        return 2

    rng = random.Random(SEED)
    dis = Disagreements()
    counts = {}
    counts['prefix'] = tier_prefix(dis, rng)
    counts['discovery'] = tier_discovery(dis, rng)
    counts['emission'] = tier_emission(dis, rng)
    counts['retention'] = tier_retention(dis, rng)
    counts['walk_emission'] = tier_walk_emission(dis, rng)
    total = sum(counts.values())

    if dis:
        print('G-CONF FAIL: %d disagreement(s) over %d inputs (seed=%d)'
              % (dis.n, total, SEED))
        for tier, inp, shadow, oracle, note in dis.items:
            print('  [%s] input=%r shadow=%r oracle=%r%s'
                  % (tier, inp, shadow, oracle, (' -- ' + note) if note else ''))
        print(json.dumps({'status': 'fail', 'disagreements': dis.n,
                          'inputs': total, 'seed': SEED, 'tiers': counts}))
        return 1

    print('G-CONF pass: nagini impl-region shadow agrees with the real patched '
          'sphinx functions (get_signature_prefix / can_document_member + '
          'import_object + add_directive_header / filter_members) on %d inputs '
          '(finite modeled domain enumerated exhaustively, then fuzzed; '
          'seed=%d), 0 disagreements.' % (total, SEED))
    print(json.dumps({'status': 'pass', 'disagreements': 0, 'inputs': total,
                      'seed': SEED, 'tiers': counts,
                      'oracle': ['sphinx.domains.python.PyProperty.get_signature_prefix',
                                 'sphinx.ext.autodoc.PropertyDocumenter.can_document_member',
                                 'sphinx.ext.autodoc.PropertyDocumenter.import_object',
                                 'sphinx.ext.autodoc.PropertyDocumenter.add_directive_header',
                                 'sphinx.ext.autodoc.Documenter.filter_members'],
                      'exhaustive_domain': True}))
    return 0


if __name__ == '__main__':
    sys.exit(main())
