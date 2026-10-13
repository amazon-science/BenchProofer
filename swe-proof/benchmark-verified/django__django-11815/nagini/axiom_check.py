#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-11815.

There is NO consumed @ContractOnly axiom in this bundle: the rendering is
spelled out deeply in model.py. This script validates the two A-REFERENCE deep
models against the REAL behaviour they stand in for, on boundary + fuzz inputs:

  (A-reference 1) `quoted(tok)` (model.py pure region) == the real repr of a
      simple identifier token. model.py models the `%r` of an enum member's
      stable name as a wrap in single quotes:  tok -> "'" + tok + "'".
      For a plain identifier (the only thing an enum member name can be — a
      valid Python attribute name: letters/digits/underscore, never starting
      with a digit, no quote/backslash/control characters) CPython's repr is
      exactly the single-quoted form. We assert this over every enum member
      name we can reach plus an exhaustive identifier fuzz.

  (A-reference 2) `rendered(module, class_name, identifier)` and
      `import_line(module)` (model.py pure region) == the REAL output of the
      enumeration serializer the gold patch installs:
          string  == "%s.%s[%r]" % (module, class_name, member.name)
          imports == {"import %s" % module}
      We reconstruct the real serializer's post-patch formatting and assert the
      deep model reproduces both the string and the (single) import line, code
      point for code point.

Imports only the Python standard library (`enum`, `re`, `keyword`, `random`) —
nothing repo-specific; the formatting under test is the two stdlib f-strings
the gold patch uses. Exit 0 iff every obligation holds.
"""
import enum
import keyword
import random
import re
import sys


# --- model.py reference encodings (kept in lock-step with the pure region) ---

def quoted(tok_cps):
    """Reference impl of model.py `quoted`: wrap code points in U+0027."""
    return [39] + list(tok_cps) + [39]


def rendered(module_cps, class_cps, ident_cps):
    """Reference impl of model.py `rendered`:
    module ++ '.' ++ class ++ '[' ++ "'ident'" ++ ']'."""
    return (list(module_cps) + [46] + list(class_cps) + [91]
            + quoted(ident_cps) + [93])


def import_line(module_cps):
    """Reference impl of model.py `import_line`: "import " ++ module."""
    return [105, 109, 112, 111, 114, 116, 32] + list(module_cps)


def cps(s):
    return [ord(ch) for ch in s]


# --- A-reference 1: quoted == repr on a simple identifier ---------------------

def check_quoted_is_repr(name):
    """Assert model.py quoted(name) == the real `%r` of the identifier name."""
    real = cps("%r" % name)             # real CPython repr of the name string
    model = quoted(cps(name))           # deep model
    assert real == model, (
        "quoted deep model unsound on %r: real repr -> %r, deep model -> %r"
        % (name, real, model))


# --- A-reference 2: rendered/import_line == the real serializer ---------------

def real_serialize_enum_member(member):
    """The post-patch EnumSerializer.serialize() formatting, reconstructed from
    the gold patch:
        return (
            '%s.%s[%r]' % (module, enum_class.__name__, self.value.name),
            {'import %s' % module},
        )
    """
    enum_class = member.__class__
    module = enum_class.__module__
    string = '%s.%s[%r]' % (module, enum_class.__name__, member.name)
    imports = {'import %s' % module}
    return string, imports


def check_serializer_reference(member):
    string, imports = real_serialize_enum_member(member)
    enum_class = member.__class__
    module = enum_class.__module__
    # string: the deep model rendered() must reproduce it code point for cp.
    model_string = rendered(cps(module), cps(enum_class.__name__),
                            cps(member.name))
    assert cps(string) == model_string, (
        "rendered deep model unsound for %r: real %r -> %r, deep model -> %r"
        % (member, string, cps(string), model_string))
    # imports: exactly one line, equal to import_line(module).
    assert len(imports) == 1, (
        "expected exactly one import for %r, got %r" % (member, imports))
    only = next(iter(imports))
    model_imp = import_line(cps(module))
    assert cps(only) == model_imp, (
        "import_line deep model unsound for %r: real %r -> %r, model -> %r"
        % (member, only, cps(only), model_imp))


def main():
    # --- A-reference 1: quoted == repr on identifier names ----------------
    # All enum member names from representative enums (incl. the F2P shapes)
    # plus the real re.RegexFlag names (the second F2P case).
    class TextEnum(enum.Enum):
        A = 'a-value'
        B = 'value-b'

    class BinaryEnum(enum.Enum):
        A = b'a-value'
        B = b'value-b'

    class IntEnum(enum.IntEnum):
        A = 1
        B = 2

    members = (list(TextEnum) + list(BinaryEnum) + list(IntEnum)
               + list(re.RegexFlag))

    for m in members:
        check_quoted_is_repr(m.name)
        check_serializer_reference(m)

    # exhaustive-ish identifier fuzz: every name is a valid Python identifier
    # (letters/digits/underscore, not starting with a digit, not a keyword).
    rng = random.Random(11815)
    ident_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_0123456789"
    head_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_"
    names = set()
    while len(names) < 20000:
        n = rng.randint(1, 12)
        nm = rng.choice(head_chars) + "".join(
            rng.choice(ident_chars) for _ in range(n - 1))
        if nm.isidentifier() and not keyword.iskeyword(nm):
            names.add(nm)
    # always include the literal F2P names
    names.update({"A", "B", "DOTALL", "GOOD", "BAD"})
    for nm in names:
        check_quoted_is_repr(nm)

    # synthesise enums over the fuzz names and check the full serializer too,
    # over a handful of module/class shapes. Enum reserves _sunder_/__dunder__
    # member names, so restrict the synthesised members to names that neither
    # start nor end with an underscore (every real F2P member name qualifies).
    sample = [nm for nm in names
              if not nm.startswith("_") and not nm.endswith("_")]
    rng.shuffle(sample)
    for i in range(0, min(len(sample) - 1, 2000), 2):
        a = sample[i]
        b = sample[i + 1]
        if a == b:
            continue
        E = enum.Enum("E_%d" % i, {a: 1, b: 2})
        for m in E:
            check_serializer_reference(m)

    print("G-AX OK: quoted/rendered/import_line deep models (A-reference) == "
          "real repr + real post-patch enum serializer over %d member names "
          "(incl. F2P A/B/DOTALL) and synthesised enums" % len(names))
    return 0


if __name__ == "__main__":
    sys.exit(main())
