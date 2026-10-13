"""PBT falsification battery for django__django-17087.

Instance under attack: `render_class_member_reference(module, class_simple_name,
class_qualified_name, method_name) -> Tuple[List[int], List[int]]` — the model of
`FunctionTypeSerializer.serialize()`'s class-bound-method branch. The gold one-line
change keys the rendered fragment on the owning class's FULLY-QUALIFIED name
(`klass.__qualname__`) instead of its bare leaf name (`klass.__name__`).

Defended surface (read from model.py):
  * ALL FOUR inputs are READ-ONLY: `Acc(list_pred(x), 1/2)` for module,
    class_simple_name, class_qualified_name, method_name. => FRAME-MUTATION is
    mandatory: any impl that WRITES to one to satisfy a postcondition vacuously
    must be rejected for INSUFFICIENT PERMISSION.
  * Two load-bearing postcondition clauses, both grounded as @Pure functions of
    the inputs (no opaque oracle to echo):
      - ToSeq(Result()[0]) == member_path(ToSeq(module), ToSeq(class_qualified_name),
        ToSeq(method_name))  == module ++ '.' ++ class_qualified_name ++ '.' ++ method_name
        The DISCRIMINATING clause: it uses class_qualified_name, NOT class_simple_name.
      - ToSeq(Result()[1]) == import_line(ToSeq(module)) == "import " ++ module.
  * No @ContractOnly consumed axiom (axioms region empty). member_path / import_line
    are A-reference deep models validated == the real post-patch format string by
    axiom_check.py (G-AX). We add one A-reference soundness probe that re-runs that
    deep-model equality against the reconstructed gold formatting (stdlib-only).

Region surgery: every variant is built by _swap on the frozen model.py, editing
ONLY text strictly inside # impl-start / # impl-end, so same_spec is guaranteed.
"""
from pathlib import Path

INSTANCE = "django__django-17087"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError("drift: %r" % (old,))
    if src.count(old) != 1:
        raise AssertionError("not unique: %r" % (old,))
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# The frozen impl region (verbatim from model.py) — every variant edits ONLY
# the text between these two markers.
# ---------------------------------------------------------------------------
_GOLD_IMPL = (
    '# impl-start\n'
    '    # frag = module + "." + class_qualified_name + "." + method_name\n'
    '    frag = []                                # type: List[int]\n'
    '    frag = frag + module\n'
    "    frag = frag + [46]                       # '.'\n"
    '    frag = frag + class_qualified_name\n'
    "    frag = frag + [46]                       # '.'\n"
    '    frag = frag + method_name\n'
    '    imp = [105, 109, 112, 111, 114, 116, 32] + module   # "import " + module\n'
    '    return (frag, imp)\n'
    '    # impl-end'
)

# sanity: the gold impl block must appear verbatim and uniquely in the base.
assert _BASE.count(_GOLD_IMPL) == 1, "gold impl region drifted from model.py"


def _impl(body_lines):
    """Wrap an impl body (lines already indented 4 spaces, no markers) into a
    full impl region between the frozen # impl-start / # impl-end markers."""
    return "# impl-start\n" + body_lines + "\n    # impl-end"


# ===========================================================================
# POSITIVE CONTROLS (soundness) — structurally-different CORRECT impls that
# MUST verify; else SPEC-TOO-STRONG.
# ===========================================================================

# (1) Single-expression direct concatenation, matching member_path's shape, and
#     imp computed BEFORE frag (branch/statement reorder). No framing asserts are
#     needed — each output is a single pinned concatenation, so the gold proof
#     stays valid. Keeps class_qualified_name (correct).
_POS_DIRECT = _impl(
    '    imp = [105, 109, 112, 111, 114, 116, 32] + module   # build import first\n'
    '    frag = module + [46] + class_qualified_name + [46] + method_name\n'
    '    return (frag, imp)'
)

# (2) Build frag right-to-left via prepending tails (different executable shape,
#     same value). Still a straight chain of concatenations equal to member_path;
#     no induction lemma needed because it is one composite '+' expression.
_POS_TAILBUILD = _impl(
    '    tail = [46] + method_name                # ".method"\n'
    '    mid = [46] + class_qualified_name + tail # ".Qual.method"\n'
    '    frag = module + mid                      # module.Qual.method\n'
    '    imp = [105, 109, 112, 111, 114, 116, 32] + module\n'
    '    return (frag, imp)'
)


# ===========================================================================
# UNIQUENESS / completeness (postcondition too weak) — WRONG impls sharing the
# spec exactly; any that VERIFIES is SPEC-TOO-WEAK.
# ===========================================================================

# (3) FRAME-MUTATION (MANDATORY — all inputs are read-only Acc(...,1/2)).
#     Mutate the read-only `module` list in place, then build the (correct) value.
#     The append needs WRITE permission to list_pred(module) but the precondition
#     grants only 1/2; Nagini must reject for INSUFFICIENT PERMISSION. The gold
#     value clauses are kept verbatim so the rejection is attributable to the write.
_FRAME_MUT = _impl(
    '    module.append(46)                        # WRITE to a read-only input\n'
    '    module.append(0)  # ILLEGAL write to a read-only input (needs full permission)\n'
    '    frag = module + [46] + class_qualified_name + [46] + method_name\n'
    '    imp = [105, 109, 112, 111, 114, 116, 32] + module\n'
    '    return (frag, imp)'
)

# (4) WRONG CARRIER — the prepatch bug verbatim in carrier terms: key the fragment
#     on class_simple_name (klass.__name__) instead of class_qualified_name
#     (klass.__qualname__). On a top-level owning class these coincide, but on a
#     nested owning class (the F2P case) they differ, so the result violates
#     ToSeq(Result()[0]) == member_path(..., class_qualified_name, ...).
_WRONG_SIMPLE = _impl(
    '    frag = module + [46] + class_simple_name + [46] + method_name\n'
    '    imp = [105, 109, 112, 111, 114, 116, 32] + module\n'
    '    return (frag, imp)'
)

# (5) DROP IMPORT PREFIX — return the module itself as the import rather than
#     "import " ++ module. Violates ToSeq(Result()[1]) == import_line(ToSeq(module)).
_WRONG_IMPORT = _impl(
    '    frag = module + [46] + class_qualified_name + [46] + method_name\n'
    '    imp = module                             # missing "import " prefix\n'
    '    return (frag, imp)'
)

# (6) PARTIAL-DOMAIN — correct EXCEPT it drops the separator dot before the method
#     name. Produces module.Qualmethod (no dot), so it diverges from member_path on
#     every input whose method_name is non-empty (the whole F2P domain) yet is a
#     near-miss a value-proxy that ignored separators might admit. Must be rejected.
_PARTIAL_NODOT = _impl(
    '    frag = module + [46] + class_qualified_name + method_name  # dropped the 2nd "."\n'
    '    imp = [105, 109, 112, 111, 114, 116, 32] + module\n'
    '    return (frag, imp)'
)

# (7) PARTIAL-DOMAIN (subtler) — uses class_qualified_name normally but appends an
#     extra trailing dot to the fragment. Right on prefix, wrong on suffix; pins the
#     "exact concatenation, no extra glyphs" guarantee. Must be rejected.
_PARTIAL_EXTRA = _impl(
    '    frag = module + [46] + class_qualified_name + [46] + method_name + [46]  # spurious trailing "."\n'
    '    imp = [105, 109, 112, 111, 114, 116, 32] + module\n'
    '    return (frag, imp)'
)


# ===========================================================================
# ADMISSIBILITY — a positive-control caller proving the precondition admits an
# F2P-shaped input (the NestedChoices.method shape). Adds a helper that
# constructs four lists and calls render_class_member_reference, asserting the
# returned fragment value. MUST verify; else PRECOND-TOO-STRONG. The added
# caller lives entirely inside the impl region (so same_spec holds) and the gold
# impl body is preserved verbatim above it.
# ===========================================================================
_ADMISS = _impl(
    '    # gold impl body (verbatim), kept so the function still satisfies its spec\n'
    '    frag = []                                # type: List[int]\n'
    '    frag = frag + module\n'
    '    frag = frag + [46]\n'
    '    frag = frag + class_qualified_name\n'
    '    frag = frag + [46]\n'
    '    frag = frag + method_name\n'
    '    imp = [105, 109, 112, 111, 114, 116, 32] + module\n'
    '    return (frag, imp)\n'
    '\n'
    '\n'
    'def _admissibility_caller() -> None:\n'
    '    # An F2P-shaped input: module="ab", simple="Cd", qualified="Cd.Ef",\n'
    '    # method="gh" (a method owned by a class NESTED in an enclosing class,\n'
    '    # mirroring WriterTests.NestedChoices.method). Build fresh full-permission\n'
    '    # lists and call the modeled function; the 1/2-permission precondition\n'
    '    # must be establishable from full permission on a freshly-built list.\n'
    '    module = [97, 98]                        # type: List[int]\n'
    '    simple = [67, 100]                       # type: List[int]\n'
    '    qualified = [67, 100, 46, 69, 102]       # type: List[int]\n'
    '    method = [103, 104]                      # type: List[int]\n'
    '    # Nagini auto-establishes list_pred over a freshly-built list literal;\n'
    '    # an explicit Fold of it is unnecessary (and mistranslates the\n'
    '    # predicate access), so we call directly on the full-permission lists.\n'
    '    out = render_class_member_reference(module, simple, qualified, method)\n'
    '    # The postcondition returns full permission to both result lists and our\n'
    '    # 1/2 of each input back. Establishing the call (hence its Requires\n'
    '    # Acc(...,1/2)) on this F2P-shaped input is the admissibility obligation;\n'
    '    # if it could not be established the call would not verify => PRECOND-TOO-STRONG.\n'
    '    Assert(Acc(list_pred(out[0])))\n'
    '    Assert(Acc(list_pred(out[1])))\n'
    '    Assert(Acc(list_pred(module), 1 / 2))\n'
    '    Assert(Acc(list_pred(qualified), 1 / 2))'
)


SPEC_TESTS = [
    {
        "id": "pos-direct-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _GOLD_IMPL, _POS_DIRECT),
        "rationale": "structurally-different CORRECT impl: import built before the "
                     "fragment, fragment as one composite concatenation matching "
                     "member_path's shape. Each output is a single pinned "
                     "concatenation so no extra framing/induction is needed; must "
                     "verify (else SPEC-TOO-STRONG).",
    },
    {
        "id": "pos-tailbuild",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _GOLD_IMPL, _POS_TAILBUILD),
        "rationale": "CORRECT impl assembled inner-to-outer (tail then mid then "
                     "front) as one '+' chain == member_path; different statement "
                     "shape, no front-recursive-fold lemma needed; must verify.",
    },
    {
        "id": "frame-mutation-module",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _FRAME_MUT),
        "refinement": "A faithful real patch that MUTATES klass.__module__'s backing "
                      "string (or the list carrying it) cannot resolve: __module__ is "
                      "a shared class attribute read by every other serialization and "
                      "by `import %s` itself; in-place mutation would corrupt the "
                      "import line and other migrations, so the F2P assertion "
                      "('migrations.test_writer.WriterTests.NestedChoices.method', "
                      "{'import migrations.test_writer'}) would not hold. The "
                      "rendering is a pure read of the inputs.",
        "rationale": "module is read-only (Requires Acc(list_pred(module), 1/2)); "
                     "module.append/pop need WRITE permission. Nagini rejects for "
                     "INSUFFICIENT PERMISSION — the value clauses are kept verbatim so "
                     "the rejection is attributable to the write, not a value mismatch.",
    },
    {
        "id": "wrong-carrier-simple-name",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _WRONG_SIMPLE),
        "refinement": "This IS the prepatch behaviour: keying on klass.__name__ "
                      "(class_simple_name) instead of klass.__qualname__ "
                      "(class_qualified_name). On the F2P input it renders "
                      "'migrations.test_writer.NestedChoices.method' instead of the "
                      "required 'migrations.test_writer.WriterTests.NestedChoices.method', "
                      "so test_serialize_nested_class_method FAILS — exactly what "
                      "model_prepatch.py demonstrates (G-DIFF).",
        "rationale": "violates the discriminating postcondition ToSeq(Result()[0]) == "
                     "member_path(ToSeq(module), ToSeq(class_qualified_name), "
                     "ToSeq(method_name)): class_simple_name != class_qualified_name "
                     "whenever the owning class is nested.",
    },
    {
        "id": "drop-import-prefix",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _WRONG_IMPORT),
        "refinement": "Returning the bare module as the import instead of "
                      "'import ' ++ module yields the import set {'migrations.test_writer'} "
                      "rather than {'import migrations.test_writer'}; the F2P "
                      "assertSerializedResultEqual compares the import set exactly, so "
                      "the test FAILS. The module-import line is part of the contract.",
        "rationale": "violates ToSeq(Result()[1]) == import_line(ToSeq(module)) == "
                     "'import ' ++ module (PSeq(105,109,112,111,114,116,32) + module).",
    },
    {
        "id": "partial-domain-missing-dot",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _PARTIAL_NODOT),
        "refinement": "Dropping the second '.' renders "
                      "'migrations.test_writer.WriterTests.NestedChoicesmethod' "
                      "(method name glued to the qualified name) — not importable / "
                      "not equal to the expected string, so the F2P fails on every "
                      "input whose method_name is non-empty (the entire tested domain).",
        "rationale": "violates ToSeq(Result()[0]) == member_path(...): member_path "
                     "places PSeq(46) between class_qualified_name and method_name; "
                     "this impl omits it.",
    },
    {
        "id": "partial-domain-trailing-dot",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _PARTIAL_EXTRA),
        "refinement": "Appending a spurious trailing '.' renders "
                      "'migrations.test_writer.WriterTests.NestedChoices.method.' — a "
                      "different string the F2P exact-equality assertion rejects. A "
                      "real patch emitting a trailing dot would not resolve.",
        "rationale": "violates ToSeq(Result()[0]) == member_path(...): member_path "
                     "ends exactly at method_name with no trailing separator.",
    },
    {
        "id": "admissibility-nested-shape",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _GOLD_IMPL, _ADMISS),
        "rationale": "a positive-control caller builds an F2P-shaped nested-class "
                     "input (qualified='Cd.Ef' distinct from simple='Cd') and calls "
                     "render_class_member_reference; the 1/2-permission precondition "
                     "must be establishable from fresh full-permission lists (else "
                     "PRECOND-TOO-STRONG). The gold impl body is preserved verbatim "
                     "so the function still meets its own spec.",
    },
]


# ===========================================================================
# AXIOM lane — there is NO consumed @ContractOnly axiom (meta.axioms == []).
# member_path / import_line are A-reference deep models validated == the real
# post-patch FunctionTypeSerializer formatting by axiom_check.py (G-AX). We add
# ONE A-reference soundness probe that re-runs the deep-model equality against
# the reconstructed gold format string on boundary + fuzz class-bound methods,
# stdlib-only (Python on the eval image is old / ASCII locale; we read no files
# and use only builtins/enum/random/string/types). Exit 0 iff the deep models
# reproduce the real rendering code-point-for-code-point.
# ===========================================================================
_AX_PROBE = r'''
import enum, random, string, sys, types

def member_path(module_cps, qualified_cps, method_cps):
    return list(module_cps) + [46] + list(qualified_cps) + [46] + list(method_cps)

def import_line(module_cps):
    return [105, 109, 112, 111, 114, 116, 32] + list(module_cps)

def cps(s):
    return [ord(ch) for ch in s]

def real_serialize_class_method(value):
    # post-patch FunctionTypeSerializer.serialize() class-bound-method branch
    klass = value.__self__
    module = klass.__module__
    return "%s.%s.%s" % (module, klass.__qualname__, value.__name__), {
        "import %s" % module
    }

def check(value):
    assert getattr(value, "__self__", None) is not None and isinstance(
        value.__self__, type), "input %r not a class-bound callable" % (value,)
    string_out, imports = real_serialize_class_method(value)
    klass = value.__self__
    module = klass.__module__
    # A-reference 1: member_path == the real rendered fragment
    model_string = member_path(cps(module), cps(klass.__qualname__), cps(value.__name__))
    assert cps(string_out) == model_string, (
        "member_path unsound for %r: real %r -> %r vs model %r"
        % (value, string_out, cps(string_out), model_string))
    # A-reference 2: import_line == the single member of the import set
    assert len(imports) == 1, "expected one import for %r got %r" % (value, imports)
    only = next(iter(imports))
    assert cps(only) == import_line(cps(module)), (
        "import_line unsound for %r: real %r vs model %r"
        % (value, only, import_line(cps(module))))
    # discriminating fact: a NESTED owning class renders with its FULL qualified
    # chain, strictly different from the buggy bare-leaf form.
    if klass.__qualname__ != klass.__name__:
        assert string_out.endswith(".%s.%s" % (klass.__qualname__, value.__name__)), (
            "nested-class method %r not rendered with full qualified name: %r"
            % (value, string_out))
        buggy = "%s.%s.%s" % (module, klass.__name__, value.__name__)
        assert string_out != buggy, (
            "post-patch must differ from buggy bare-leaf form for %r: %r"
            % (value, string_out))

class TopLevelCls:
    @classmethod
    def cm(cls): return cls

class Outer:
    class Inner:
        @classmethod
        def method(cls): return cls
    class Middle:
        class Deep:
            @classmethod
            def go(cls): return cls

class Host:
    class NestedChoices(enum.Enum):
        X = "X"; Y = "Y"
        @classmethod
        def method(cls): return cls.X

class DeepTop:
    @classmethod
    def cm(cls): return cls
    class NestedA:
        @classmethod
        def cm(cls): return cls
        class NestedB:
            @classmethod
            def cm(cls): return cls

def main():
    targets = [TopLevelCls.cm, Outer.Inner.method, Outer.Middle.Deep.go,
               Host.NestedChoices.method, DeepTop.cm, DeepTop.NestedA.cm,
               DeepTop.NestedA.NestedB.cm]
    # sanity that we really exercise the qualname != name distinction
    assert TopLevelCls.__qualname__ == TopLevelCls.__name__
    assert Outer.Inner.__qualname__ != Outer.Inner.__name__
    assert Host.NestedChoices.__qualname__ != Host.NestedChoices.__name__
    for v in targets:
        check(v)

    rng = random.Random(17087)
    head = string.ascii_letters + "_"
    tail = string.ascii_letters + string.digits + "_"
    def ident():
        n = rng.randint(1, 10)
        return rng.choice(head) + "".join(rng.choice(tail) for _ in range(n - 1))
    def module_name():
        return ".".join(ident() for _ in range(rng.randint(1, 4)))
    for _ in range(20000):
        leaf = ident(); mname = ident()
        cls = types.new_class(leaf)
        cls.__module__ = module_name()
        cls.__name__ = leaf
        if rng.random() < 0.5:
            prefix = ".".join(ident() for _ in range(rng.randint(1, 3)))
            cls.__qualname__ = prefix + "." + leaf
        else:
            cls.__qualname__ = leaf
        def _fn(c): return c
        _fn.__name__ = mname
        check(types.MethodType(_fn, cls))
    print("A-ref OK: member_path/import_line == real post-patch formatting over "
          "%d explicit + 20000 fuzz class-bound methods" % len(targets))
    return 0

sys.exit(main())
'''

AXIOM_TESTS = [
    {
        "id": "aref-render-soundness",
        "axiom": "member_path/import_line (A-reference deep models)",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _AX_PROBE,
        "rationale": "No consumed @ContractOnly axiom exists; member_path / "
                     "import_line are A-reference deep models. This probe reconstructs "
                     "the gold post-patch \"%s.%s.%s\" %% (module, klass.__qualname__, "
                     "value.__name__) + {'import %s' %% module} and asserts the deep "
                     "models reproduce it code-point-for-code-point over boundary "
                     "(top-level / nested / nested-enum / deep-nested) + 20000 fuzz "
                     "class-bound methods, under the real runtime (the format is a "
                     "stdlib f-string with no flag dependency). Any disagreement => "
                     "A-reference UNSOUND. Containment is trivial: member_path/"
                     "import_line are total over all PSeq[int] the model can pass, so "
                     "there is no caller-reachable input outside their domain.",
    },
]
