# properties.py — PBT falsification battery for sphinx-doc__sphinx-7889.
#
# NOT a Nagini module. A manifest the runner (swebench_nagini.pbt) parses: each
# SPEC_TESTS entry is a full model.py variant that shares the FROZEN spec
# (axioms/pure/pre/post-conditions/invariants regions untouched) and swaps ONLY
# text inside the # impl-start / # impl-end region; the runner checks each with
# Nagini verify + markers.same_spec. AXIOM_TESTS are real-callee probes run in
# the instance Docker image.
#
# ---------------------------------------------------------------------------
# Defended surface (read from model.py + refinement.md + mapping.md + instance):
#
#   subscript_placeholder(key_is_text: bool, key_text: List[int],
#                         module: List[int]) -> List[int]
#
#   Models _MockObject.__getitem__: subscripting a mock placeholder by an
#   ARBITRARY index and naming the fresh placeholder `module + '.' + str(key)`.
#   The fix (gold) is `_make_subclass(str(key), ...)` instead of
#   `_make_subclass(key, ...)` — coerce the index to text BEFORE the
#   string-only fabricator.
#
#   READ-ONLY inputs (frame-mutation MANDATORY):
#     Requires(Acc(list_pred(key_text), 1/2))   <- half permission
#     Requires(Acc(list_pred(module),   1/2))   <- half permission
#   Precondition also: Requires(not (0 in ToSeq(key_text))) plus a Forall
#   excluding surrogate code points (scalar-only index rendering), and
#   Requires(MustTerminate(2)) — total-correctness obligation.
#
#   Load-bearing postcondition clauses:
#     (frame)  Ensures(Acc(list_pred(key_text), 1/2))   give back key_text perm
#     (frame)  Ensures(Acc(list_pred(module),   1/2))   give back module  perm
#     (own)    Ensures(Acc(list_pred(Result())))        own the result fully
#     (VALUE)  Ensures(ToSeq(Result())
#                == ToSeq(module) + PSeq(46) + render_text(ToSeq(key_text)))
#              i.e. result == module ++ "." ++ render_text(key_text).
#
#   render_text is GROUNDED: it is the IDENTITY (Ensures Result()==value_text,
#   body `return value_text`), fully unfolded @Pure. So the VALUE clause reduces
#   to `module ++ [46] ++ key_text` — there is no opaque answer-key to echo (see
#   'assessment' re ungrounded-oracle). The work the impl must actually do is
#   (a) discharge the fabricator axiom's Requires(name_is_text ...) by handing it
#   a TEXTUAL name (the fix), and (b) materialise the exact display content.
#
#   AXIOM (A-consumed): display_name ↔ _make_subclass (UNCHANGED callee).
#     Requires(name_is_text and not (0 in name)); Ensures(== module ++[46]++ name).
#     Consumed in impl: produced = display_name(name_is_text, name, ToSeq(module)).
#     The pre-patch fails this Requires (name_is_text=key_is_text false on a
#     non-text index) — that IS the modelled TypeError from _make_subclass(key).
#
# F2P: tests/test_ext_autodoc_mock.py::test_MockObject — the new sub-test builds
#      `class SubClass2(mock.SomeClass[T])` (T a TypeVar), i.e. a NON-textual
#      subscript index. Pre-patch raised TypeError; post-patch str(key) succeeds.
# P2P: test_MockModule / test_mock / test_abc_MockObject / test_mock_decorator
#      (exercise ordinary textual subscript/attribute access — must still work).

from pathlib import Path

INSTANCE = "sphinx-doc__sphinx-7889"
FLOAT_ENCODING = None  # meta.json float_encoding == null


_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# The GOLD impl head (lines 96-106 of model.py): the fix lives here. Every rival
# edits ONLY inside the # impl-start / # impl-end region.
# ---------------------------------------------------------------------------
_GOLD_HEAD = """    # Reduce the index to its textual rendering FIRST, so the string-only
    # fabricator receives an honest string for EVERY index.  The rendering is
    # always textual, so the fabricator's textual precondition (name_is_text)
    # is met unconditionally -- independent of key_is_text.
    name_is_text = True
    name = render_text(ToSeq(key_text))
    # Hand the (now textual) name to the fabricator; its textual precondition
    # name_is_text is discharged here.  This call is the operation that fails
    # for a non-textual name argument.
    produced = display_name(name_is_text, name, ToSeq(module))
    Assert(produced == ToSeq(module) + PSeq(46) + name)"""


# === POSITIVE CONTROL (soundness) =========================================
# Structurally-different but CORRECT impl. The two leading statements
# `name_is_text = True` and `name = render_text(ToSeq(key_text))` are mutually
# independent, so they may be REORDERED; and `produced` is renamed `fab`. Every
# loop, invariant and load-bearing Assert is kept VERBATIM (directives 2 & 3:
# no framing assert dropped, no loop-direction flip, no auto-undischargeable
# lemma). The fix property (name_is_text = True, name = render_text(...)) is
# preserved, so the fabricator's Requires is still discharged. MUST verify; if it
# cannot, the spec rejects a faithful correct impl => SPEC-TOO-STRONG.
_POS_HEAD = """    # POSITIVE CONTROL: reorder the two independent leading statements and
    # rename the fabricator result; the fix (textual name) is unchanged.
    name = render_text(ToSeq(key_text))
    name_is_text = True
    fab = display_name(name_is_text, name, ToSeq(module))
    Assert(fab == ToSeq(module) + PSeq(46) + name)"""
POS_REORDER = _swap(_BASE, _GOLD_HEAD, _POS_HEAD)


# === ADMISSIBILITY ========================================================
# Insert a probe block right after `# impl-start`, BEFORE any gold obligation
# (so every following obligation is preserved verbatim). It constructs an
# F2P-shaped textual rendering -- the code points of "~T" ([126,84], the issue's
# `SubClass2(mock.SomeClass[T])` rendered index) -- and asserts the precondition
# predicates are establishable: list_pred ownership and the NUL-free clause
# `not (0 in ToSeq(probe))`. A self-call would need a permission split / framing
# the spec does not carry (proof gap, not a spec defect), so we exercise the
# Requires predicates directly. If this cannot verify, the precondition is
# unsatisfiable for a normal index => PRECOND-TOO-STRONG.
_ADMISS_BLOCK = """    # impl-start
    # ADMISSIBILITY PROBE: a representative F2P-shaped index rendering ("~T",
    # the parametrised-generic index in test_MockObject) establishes the
    # Requires predicates (list_pred ownership + NUL-free).
    probe = [126, 84]  # type: List[int]
    Assert(list_pred(probe))
    Assert(not (0 in ToSeq(probe)))
    Assert(len(probe) == 2)
    Assert(ToSeq(probe)[0] == 126)"""
ADMISS = _swap(_BASE, "    # impl-start", _ADMISS_BLOCK)


# === UNIQUENESS / REJECT rivals ===========================================

# --- W1 FRAME-MUTATION (MANDATORY: module is read-only Acc(list_pred,1/2)).
# A rival that WRITES to the read-only `module` input (appends a code point to
# it) to try to satisfy the postcondition. With only HALF permission the write
# CANNOT be performed -- the rival fails for INSUFFICIENT PERMISSION at the
# mutation, not for a value mismatch. Every gold invariant/assert is kept
# verbatim so the rejection is attributable to the write. A byte-fuzzer never
# constructs this.
# refinement: a faithful real patch that mutated self.__display_name__ (the
# `module` carrier) -- e.g. `self.__display_name__ += '.'` -- before fabricating
# would CORRUPT the placeholder's module name for every subsequent subscript /
# attribute access; test_MockObject reads `obj.__display_name__`-derived
# behaviour and the P2P test_mock / test_MockModule chained-access tests would
# observe the wrong display name -- it would NOT resolve.
# rejection source: PERMISSION SYSTEM -- writing `module` needs full permission
# but only Acc(list_pred(module),1/2) is held (and the frame Ensures must return
# that 1/2 intact).
_FRAME_HEAD = """    # FRAME-MUTATION RIVAL: write to the read-only `module` input. Only
    # Acc(list_pred(module),1/2) is held, so this append must be REJECTED for
    # insufficient permission.
    module.append(46)
    name_is_text = True
    name = render_text(ToSeq(key_text))
    produced = display_name(name_is_text, name, ToSeq(module))
    Assert(produced == ToSeq(module) + PSeq(46) + name)"""
FRAME_MODULE_WRITE = _swap(_BASE, _GOLD_HEAD, _FRAME_HEAD)


# --- W2 FRAME-MUTATION on key_text (the OTHER read-only input).
# Same attack against `key_text` (also Acc(list_pred(key_text),1/2)): write to it
# before building the result. Must fail for insufficient permission.
# refinement: a faithful patch mutating the index carrier would alter the name
# handed to _make_subclass, naming the placeholder after a corrupted index; the
# F2P/P2P subscript tests observe the resulting class identity -- it would NOT
# resolve.
# rejection source: PERMISSION SYSTEM -- key_text held at 1/2 only.
_FRAME_KEY_HEAD = """    # FRAME-MUTATION RIVAL (key_text): write to the read-only index carrier.
    # Only Acc(list_pred(key_text),1/2) is held -> insufficient permission.
    key_text.append(120)
    name_is_text = True
    name = render_text(ToSeq(key_text))
    produced = display_name(name_is_text, name, ToSeq(module))
    Assert(produced == ToSeq(module) + PSeq(46) + name)"""
FRAME_KEY_WRITE = _swap(_BASE, _GOLD_HEAD, _FRAME_KEY_HEAD)


# --- W3 PRE-PATCH SHAPE: hand the RAW index to the fabricator (name_is_text =
# key_is_text), i.e. NO textual coercion. This is exactly model_prepatch.py: the
# fabricator's Requires(name_is_text) CANNOT be discharged when key_is_text is
# false, so the call is rejected. This is the modelled image of the real
# TypeError from _make_subclass(key) on a non-textual (TypeVar) index, and the
# load-bearing discriminator of the fix.
# refinement: this IS the pre-patch -- `_make_subclass(key, ...)` raises
# TypeError on a TypeVar index, so `class SubClass2(mock.SomeClass[T])` fails at
# class-creation time; F2P test_MockObject's parametrised-type block raises
# instead of building SubClass2 -- it does NOT resolve (it is the bug the patch
# fixes).
# rejection source: AXIOM display_name's Requires(name_is_text) -- undischarged
# on the non-text branch (control-flow-effect: the modelled raise path).
_RAW_HEAD = """    # PRE-PATCH RIVAL: hand the index on UNCHANGED (no str() coercion). The
    # name is textual only when the index already was, so the fabricator's
    # Requires(name_is_text) is undischarged for a non-textual index.
    name_is_text = key_is_text
    name = render_text(ToSeq(key_text))
    produced = display_name(name_is_text, name, ToSeq(module))
    Assert(produced == ToSeq(module) + PSeq(46) + name)"""
RAW_INDEX = _swap(_BASE, _GOLD_HEAD, _RAW_HEAD)


# --- W4 WRONG SEPARATOR (partial-domain on the produced value). Materialise the
# result with code point 47 ('/') instead of 46 ('.'). Correct length/shape and
# correct rendering of module/key, wrong ONLY on the one separator code point.
# refinement: a faithful patch building `module + '/' + str(key)` would give the
# placeholder a display name like `mod/~T` instead of `mod.~T`; while the F2P
# only checks construction succeeds, any consumer reading the display name (the
# whole point of __display_name__) would see the wrong dotted path -- the model
# pins the EXACT display content the fabricator's Ensures specifies, so a
# faithful '/' patch diverges from the gold display name.
# rejection source: VALUE Ensures `ToSeq(Result()) == module ++ PSeq(46) ++
# render_text(key)` -- the separator MUST be 46.
_SEP_TAIL = """    result = result + [46]
    j = 0"""
_SEP_TAIL_BAD = """    result = result + [47]
    j = 0"""
WRONG_SEP = _swap(_BASE, _SEP_TAIL, _SEP_TAIL_BAD)


# --- W5 DROP THE SEPARATOR entirely (partial-domain / value double-mask). Build
# `module ++ key_text` with NO dot. Off by one element vs the pinned content.
# refinement: a faithful patch building `module + str(key)` (concatenation
# without the '.') would name the placeholder `mod~T` instead of `mod.~T`,
# losing the dotted module path the display-name contract requires -- it would
# produce the wrong __display_name__ for every subscript and NOT resolve.
# rejection source: VALUE Ensures -- the separator PSeq(46) is mandatory.
_DROPSEP = """    Assert(ToSeq(result) == ToSeq(module))
    result = result + [46]
    j = 0"""
_DROPSEP_BAD = """    Assert(ToSeq(result) == ToSeq(module))
    j = 0"""
DROP_SEP = _swap(_BASE, _DROPSEP, _DROPSEP_BAD)


# --- W6 OMIT THE KEY RENDERING (partial-domain: correct for empty key, wrong for
# any non-empty index). Return `module ++ [46]` and never append the key's code
# points -- i.e. skip the second loop. Correct on the (degenerate) empty-index
# sub-domain, diverges on every non-empty index (the whole F2P scenario).
# refinement: a faithful patch that fabricated `module + '.'` (dropping the
# index) would name EVERY placeholder `mod.` regardless of the subscript index;
# `SomeClass[T]` and `SomeClass[U]` would collide on `mod.` -- the F2P/P2P
# subscript tests build distinct subclasses and would get an indistinguishable
# (wrong) display name -- it would NOT resolve.
# rejection source: VALUE Ensures -- the `render_text(key_text)` tail is
# mandatory; dropping the key loop leaves result == module ++ [46] != the pin.
_OMITKEY = """    result = result + [46]
    j = 0
    while j < len(key_text):
        # invariants-start
        Invariant(Acc(list_pred(module), 1 / 2))
        Invariant(Acc(list_pred(key_text), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= j and j <= len(key_text))
        Invariant(ToSeq(result) == ToSeq(module) + PSeq(46) + ToSeq(key_text).take(j))
        # Bounded loop: measure len(key_text) - j, strictly decreasing and
        # bounded below, discharges the caller-held termination obligation.
        Invariant(MustTerminate(len(key_text) - j + 1))
        # invariants-end
        result = result + [key_text[j]]
        Assert(ToSeq(key_text).take(j) + PSeq(key_text[j]) == ToSeq(key_text).take(j + 1))
        j = j + 1
    Assert(ToSeq(result) == ToSeq(module) + PSeq(46) + ToSeq(key_text))
    return result"""
_OMITKEY_BAD = """    result = result + [46]
    # OMIT-KEY RIVAL: skip the index-rendering loop; return module ++ [46].
    return result"""
OMIT_KEY = _swap(_BASE, _OMITKEY, _OMITKEY_BAD)


SPEC_TESTS = [
    {
        "id": "pos-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": POS_REORDER,
        "rationale": "structurally-different CORRECT impl (the two independent "
        "leading statements reordered, fabricator result renamed) keeping every "
        "loop/invariant/Assert verbatim and the fix property (textual name) "
        "intact -- must verify, else SPEC-TOO-STRONG. Reorder/rename only "
        "(directives 2 & 3 safe: no dropped framing assert, no loop-direction flip).",
    },
    {
        "id": "admiss-tilde-T",
        "kind": "admissibility",
        "expect": "verify",
        "module": ADMISS,
        "rationale": "a positive-control block constructs the F2P-shaped index "
        "rendering '~T' ([126,84]) and asserts the Requires predicates "
        "(list_pred ownership + NUL-free `not (0 in ToSeq(probe))`) hold -- the "
        "precondition must admit the normal parametrised-generic index, else "
        "PRECOND-TOO-STRONG.",
    },
    {
        "id": "frame-module-write",
        "kind": "uniqueness",
        "expect": "reject",
        "module": FRAME_MODULE_WRITE,
        "refinement": "a faithful patch mutating self.__display_name__ (the "
        "`module` carrier) before fabricating would corrupt the placeholder's "
        "module name for every later subscript/attribute access; the chained-"
        "access P2P tests (test_mock / test_MockModule) and test_MockObject would "
        "observe the wrong display name -- it would NOT resolve.",
        "rationale": "rejected by the PERMISSION SYSTEM: writing `module` needs "
        "full permission but only Acc(list_pred(module),1/2) is held (and the "
        "frame Ensures must return that 1/2 intact). MANDATORY frame-mutation "
        "probe for a read-only input; a byte-fuzzer never constructs it.",
    },
    {
        "id": "frame-key-write",
        "kind": "uniqueness",
        "expect": "reject",
        "module": FRAME_KEY_WRITE,
        "refinement": "a faithful patch mutating the index carrier would alter "
        "the name handed to _make_subclass, naming the placeholder after a "
        "corrupted index; the F2P/P2P subscript tests observe the class identity "
        "-- it would NOT resolve.",
        "rationale": "rejected by the PERMISSION SYSTEM: key_text is held at "
        "Acc(list_pred(key_text),1/2) only, so the append is insufficient-"
        "permission. Second read-only input, same frame-mutation class.",
    },
    {
        "id": "raw-index-no-coercion",
        "kind": "uniqueness",
        "expect": "reject",
        "module": RAW_INDEX,
        "refinement": "this IS the pre-patch -- `_make_subclass(key, ...)` raises "
        "TypeError on a TypeVar index, so `class SubClass2(mock.SomeClass[T])` "
        "fails at class-creation time; F2P test_MockObject's parametrised-type "
        "block raises instead of building SubClass2 -- it does NOT resolve (it is "
        "the exact bug the patch fixes).",
        "rationale": "rejected by the AXIOM display_name's Requires(name_is_text) "
        "-- undischarged when key_is_text is false (the modelled raise path; "
        "control-flow-effect). This is the load-bearing discriminator of the fix, "
        "matching model_prepatch.py / G-DIFF.",
    },
    {
        "id": "wrong-separator",
        "kind": "uniqueness",
        "expect": "reject",
        "module": WRONG_SEP,
        "refinement": "a faithful patch building `module + '/' + str(key)` would "
        "name the placeholder `mod/~T` instead of `mod.~T`, giving a wrong dotted "
        "module path in __display_name__ that any display-name consumer reads; the "
        "model pins the exact fabricator display content -- it would NOT resolve.",
        "rationale": "rejected by the VALUE Ensures `ToSeq(Result()) == "
        "ToSeq(module) ++ PSeq(46) ++ render_text(ToSeq(key_text))` -- the "
        "separator MUST be code point 46. (partial-domain: one wrong code point.)",
    },
    {
        "id": "drop-separator",
        "kind": "uniqueness",
        "expect": "reject",
        "module": DROP_SEP,
        "refinement": "a faithful patch building `module + str(key)` (no '.') "
        "names the placeholder `mod~T`, losing the dotted module path the "
        "display-name contract requires -- it would NOT resolve.",
        "rationale": "rejected by the VALUE Ensures -- the PSeq(46) separator is "
        "mandatory; result would be off by one element (module ++ key, no dot).",
    },
    {
        "id": "omit-key-render",
        "kind": "uniqueness",
        "expect": "reject",
        "module": OMIT_KEY,
        "refinement": "a faithful patch fabricating `module + '.'` (dropping the "
        "index) would name EVERY placeholder `mod.` regardless of index; "
        "SomeClass[T] and SomeClass[U] would collide on `mod.` -- the F2P/P2P "
        "subscript tests build distinct subclasses and would get an "
        "indistinguishable (wrong) display name -- it would NOT resolve.",
        "rationale": "rejected by the VALUE Ensures -- the render_text(key_text) "
        "tail is mandatory; dropping the key loop leaves result == module ++ [46], "
        "which fails the pin for any non-empty index. (partial-domain: correct "
        "only on the degenerate empty index.)",
    },
]


# ---------------------------------------------------------------------------
# AXIOM LANE -- one A-consumed axiom (display_name <-> _make_subclass, the
# UNCHANGED callee) + one A-reference deep model (render_text <-> str(key)).
# Probes import the REAL sphinx.ext.autodoc.mock and EXECUTE the callees
# (directive 4: never scrape source). apply_gold=True is harmless: _make_subclass
# is unchanged by the patch, str() is a builtin. Self-contained, stdlib-only.
# ---------------------------------------------------------------------------

_AX_SOUND_PROBE = r'''
"""axiom-soundness for display_name <-> _make_subclass (UNCHANGED callee).

Ensures: for a TEXTUAL NUL-free name, _make_subclass(name, module).__display_name__
         == module + '.' + name  (model: == module ++ PSeq(46) ++ name).
Requires (no over-claim): the real callee RAISES for
  (a) a non-textual name (TypeError), and
  (b) a textual name carrying a NUL code point (ValueError) --
  so Requires(name_is_text and not (0 in name)) promises nothing the real
  callee cannot deliver. Boundary + fuzz + control-character sweep.
"""
import random
import sys
from typing import TypeVar

from sphinx.ext.autodoc.mock import _make_subclass, _MockObject

fail = []

# (Ensures) textual NUL-free names: boundary
modules = ["", "a", "mod", "pkg.sub", "a.b.c", "MyModule", "x9"]
text_names = ["", "A", "name", "SomeClass", "T", "x", "Foo.Bar", "a_b",
              "9", "~T", "list", "Dict"]
for module in modules:
    for name in text_names:
        cls = _make_subclass(name, module)
        observed = cls.__display_name__
        expected = module + "." + name
        if observed != expected:
            fail.append("Ensures: name=%r module=%r got %r want %r"
                        % (name, module, observed, expected))
        if not issubclass(cls, _MockObject):
            fail.append("Ensures: %r not a _MockObject subclass" % (cls,))

# (Ensures) fuzz textual NUL-free names
rng = random.Random(7889)
alphabet = list("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_.0123456789~")
for _ in range(5000):
    n = rng.randint(0, 16)
    name = "".join(rng.choice(alphabet) for _ in range(n))
    m = rng.randint(0, 12)
    module = "".join(rng.choice(alphabet) for _ in range(m))
    cls = _make_subclass(name, module)
    if cls.__display_name__ != module + "." + name:
        fail.append("Ensures(fuzz): name=%r module=%r got %r"
                    % (name, module, cls.__display_name__))

# (Requires) non-textual names MUST raise -> Requires(name_is_text) not over-claimed
T = TypeVar("T")
nontext = [T, TypeVar("S", covariant=True), object(), [1, 2], {"k": 1}, (1, 2)]
for module in modules:
    for nm in nontext:
        try:
            cls = _make_subclass(nm, module)
        except TypeError:
            continue
        fail.append("Requires over-claim: non-text name %r accepted -> %r"
                    % (nm, cls))

# (Requires) NUL-bearing textual names MUST raise -> not(0 in name) not over-claimed
nul_names = ["\x00", "T\x00", "\x00T", "a\x00b", "name\x00", "\x00\x00",
             "Foo\x00Bar"]
for module in modules:
    for nn in nul_names:
        try:
            cls = _make_subclass(nn, module)
        except (ValueError, TypeError):
            continue
        fail.append("Requires over-claim: NUL name %r accepted -> %r"
                    % (nn, cls))

if fail:
    print("AXIOM-UNSOUND display_name:")
    for f in fail[:20]:
        print("  " + f)
    sys.exit(1)
print("G-PBT axiom-soundness OK: _make_subclass Ensures (module + '.' + name) "
      "holds on boundary+5000 fuzz NUL-free textual names; Requires(name_is_text "
      "and not(0 in name)) genuinely required (TypeError on non-text names, "
      "ValueError/TypeError on NUL-bearing names) -- no over-claim.")
sys.exit(0)
'''


_AX_CONTAIN_PROBE = r'''
"""axiom-containment for display_name <-> _make_subclass.

The model passes the fabricator EXACTLY ONE class of name:
    name = render_text(ToSeq(key_text)),  name_is_text = True
where key_text are the code points of str(key) for an ARBITRARY index, and the
caller's precondition guarantees `not (0 in ToSeq(key_text))` (the index's
textual rendering carries no NUL). So every callee-input the MODEL can reach is
a TEXTUAL, NUL-FREE name -- which is EXACTLY the axiom's
Requires(name_is_text and not (0 in name)) domain.

This probe ENUMERATES the model-reachable callee inputs by replaying the fix's
deep model: for a representative spread of real index objects (the issue's
TypeVar, plus types/ints/strings/objects), compute str(key) -- the rendering the
model hands on -- and assert it is (a) a str (name_is_text True) and (b) NUL-free
(in the precondition's NUL-free domain) AND that the real _make_subclass accepts
it. A reachable input outside the axiom domain would be AXIOM-TOO-WEAK-FOR-CALLER;
covering MORE than the caller reaches is sound and not flagged.

NOTE: the model's precondition `not (0 in ToSeq(key_text))` already EXCLUDES any
index whose str() rendering contains a NUL, so such an index is NOT
caller-reachable -- there is nothing for the axiom to cover there. We assert the
representative indices the F2P/issue exercises all render NUL-free and in-domain.
"""
import sys
from typing import TypeVar

from sphinx.ext.autodoc.mock import _make_subclass

T = TypeVar("T")
S = TypeVar("S", covariant=True)


class _Custom:
    def __repr__(self):
        return "Custom()"


# Representative spread of indices the subscript operation must handle
# (issue: parametrised generic T; plus ordinary textual / numeric / type / object
# indices). These are precisely the `key` the post-patch hands str(key) of.
indices = [T, S, TypeVar("V"), "A", "name", "T", "Foo.Bar", "",
           0, 3, -7, 42, int, object, object(), _Custom(), (1, 2), [1], {"k": 1}]

module = "mod"
fail = []
for key in indices:
    rendered = str(key)                      # the model's render_text(key) image
    # (containment half 1) name_is_text == True: str() is total + text-valued
    if not isinstance(rendered, str):
        fail.append("reachable name not textual for key=%r" % (key,))
        continue
    # (containment half 2) the model only reaches NUL-free renderings (its
    # precondition `not (0 in ToSeq(key_text))`); confirm these representative
    # indices render NUL-free, i.e. lie in the axiom's not(0 in name) domain.
    if "\x00" in rendered:
        fail.append("reachable name carries NUL for key=%r -> %r (would be "
                    "excluded by the model's precondition, so not actually "
                    "reachable)" % (key, rendered))
        continue
    # the axiom domain (textual + NUL-free) must ACCEPT this reachable name:
    # the real callee succeeds and assigns module + '.' + rendered.
    try:
        cls = _make_subclass(rendered, module)
    except Exception as e:
        fail.append("axiom domain does NOT cover caller-reachable name %r "
                    "(from key=%r): real _make_subclass raised %r"
                    % (rendered, key, e))
        continue
    if cls.__display_name__ != module + "." + rendered:
        fail.append("display name mismatch for reachable name %r: %r"
                    % (rendered, cls.__display_name__))

if fail:
    print("AXIOM-TOO-WEAK-FOR-CALLER display_name:")
    for f in fail[:20]:
        print("  " + f)
    sys.exit(1)
print("G-PBT axiom-containment OK: every callee-input the model can reach "
      "(name = str(key) for arbitrary index, name_is_text=True, NUL-free by the "
      "caller precondition) lies INSIDE the axiom's Requires(name_is_text and "
      "not(0 in name)) domain; the real _make_subclass accepts each and assigns "
      "module + '.' + str(key). Checked %d representative indices incl. the "
      "issue's TypeVar." % (len(indices),))
sys.exit(0)
'''


_AX_RENDER_PROBE = r'''
"""A-reference soundness for render_text <-> str(key).

render_text is modelled as the IDENTITY whose essential property is TOTALITY +
TEXT-VALUEDNESS, which is what makes name_is_text unconditionally True (the fix).
This probe confirms the deep model against the real builtin: str(key) is total
(never raises) and always returns a str for every index class the subscript
operation must handle -- the exact behaviour the model relies on. It also runs
the END-TO-END fix scenario: _make_subclass(str(key), module) succeeds for a
non-textual index (TypeVar), whereas _make_subclass(key, module) raises -- the
issue's `mock.SomeClass[T]` failure.
"""
import sys
from typing import TypeVar

from sphinx.ext.autodoc.mock import _make_subclass, _MockObject

T = TypeVar("T")
fail = []

keys = [T, TypeVar("S", covariant=True), "A", "name", "T", 0, 3, -7, int,
        object, object(), (1, 2), [1], {"k": 1}]
for key in keys:
    try:
        r = str(key)                         # render_text deep model
    except Exception as e:
        fail.append("str(%r) RAISED %r -- render_text not total" % (key, e))
        continue
    if not isinstance(r, str):
        fail.append("str(%r) -> %r not a str -- render_text not text-valued"
                    % (key, r))

# end-to-end fix scenario (the issue): str(key) coercion succeeds for a TypeVar
# index; the raw key raises -- matching the modelled name_is_text=True vs the
# pre-patch's undischarged Requires.
module = "mod"
for key in [T, TypeVar("U"), object(), 0]:
    cls_post = _make_subclass(str(key), module)   # post-patch path
    if cls_post.__display_name__ != module + "." + str(key):
        fail.append("post-patch display name wrong for key=%r: %r"
                    % (key, cls_post.__display_name__))
    if not issubclass(cls_post, _MockObject):
        fail.append("post-patch result not a _MockObject subclass for key=%r" % (key,))
    try:
        _make_subclass(key, module)                # pre-patch path: must raise
    except TypeError:
        pass
    else:
        fail.append("pre-patch unexpectedly succeeded on non-textual key=%r" % (key,))

if fail:
    print("A-REFERENCE render_text mismatch:")
    for f in fail[:20]:
        print("  " + f)
    sys.exit(1)
print("G-PBT A-reference OK: str(key) is total + text-valued for every index "
      "class (render_text identity sound); end-to-end fix scenario matches "
      "(str(key) coercion builds the placeholder for TypeVar/object/int indices, "
      "raw key raises -- the issue's mock.SomeClass[T] case).")
sys.exit(0)
'''


AXIOM_TESTS = [
    {
        "id": "ax-sound-display_name",
        "axiom": "display_name",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _AX_SOUND_PROBE,
        "rationale": "the real _make_subclass (unchanged callee) must satisfy the "
        "axiom Ensures (module + '.' + name) on textual NUL-free names AND raise "
        "on every input the Requires excludes (non-text names + NUL-bearing "
        "textual names), so Requires(name_is_text and not(0 in name)) does not "
        "over-claim. Any violation => AXIOM-UNSOUND.",
    },
    {
        "id": "ax-contain-display_name",
        "axiom": "display_name",
        "kind": "axiom-containment",
        "expect": "covered",
        "apply_gold": True,
        "probe": _AX_CONTAIN_PROBE,
        "rationale": "every callee-input the model can reach (name = str(key) for "
        "an arbitrary index, name_is_text=True, NUL-free by the caller "
        "precondition) lies inside the axiom's Requires domain; a reachable input "
        "outside it would be AXIOM-TOO-WEAK-FOR-CALLER.",
    },
    {
        "id": "ax-ref-render_text",
        "axiom": "render_text",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _AX_RENDER_PROBE,
        "rationale": "the A-reference deep model render_text == str(key) must be "
        "total + text-valued for every index class (so name_is_text is "
        "unconditionally True) and the end-to-end fix scenario must match the real "
        "_make_subclass (str(key) builds the placeholder, raw key raises).",
    },
]
