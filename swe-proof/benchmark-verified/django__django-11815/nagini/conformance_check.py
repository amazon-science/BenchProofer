#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-11815 (nagini).

SHADOW: the impl region of model.py `serialize_member`, copied verbatim below
with the contract calls (Requires/Ensures) stripped. The @Pure helpers
(`plain_token_char`, `quoted`, `rendered`, `import_line`) copy over as plain
functions on top of a small immutable-tuple PSeq shim; they are contract-side
but serve here as an internal cross-check of the shadow. There are no
@ContractOnly callees in this bundle.

ORACLE: the REAL patched repo method the model models per mapping.md —
``EnumSerializer.serialize`` from ``django.db.migrations.serializer``. The
gate applies patch.diff to /testbed before this script runs, so the imported
method is the patched one. The method reads three texts off the value it
serializes (the module path of the value's class, the class's simple name,
and the value's stable ``name`` attribute) and returns a rendered fragment
plus a set of import statements.

Type bridge (mapping.md section 2): every text is a ``str``; the model
carrier is ``List[int]`` of Unicode code points via ``ord`` (a bijection).
The method's return is a 2-tuple ``(string, imports)``; the model refines the
import set as its single member rendered to code points, so the oracle side
asserts the set is a singleton and compares that one element.

Input domain (the Requires): the four texts are arbitrary readable lists of
code points EXCEPT the stable identifier, whose every code point must be an
ASCII letter, digit, or underscore (`plain_token_char`). Generation respects
exactly that: identifiers are drawn from the 63-character token alphabet
(including empty and digit-leading shapes, which the precondition admits),
while module / class-name / payload texts range over broad Unicode. Real
enumeration members (including the shapes the target tests observe, and
``re.RegexFlag``) are exercised directly; the rest of the Requires domain is
reached through a minimal carrier object exposing the same three attributes
the real method reads (`__class__.__module__`, `__class__.__name__`, `name`),
so the oracle is always the real patched method.

>= 1e5 Requires-satisfying inputs: boundary cases + single/double-token
sweep + 100000 fuzz triples. Pinned fuzz seed: 118150.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only.
"""
import enum
import json
import random
import re
import sys

SEED = 118150
N_FUZZ = 100000


# --- PSeq shim: immutable sequence with the operations the pure region uses --

class PSeq(object):
    __slots__ = ("_t",)

    def __init__(self, *items):
        self._t = tuple(items)

    @classmethod
    def _wrap(cls, t):
        s = cls()
        s._t = tuple(t)
        return s

    def __add__(self, other):
        return PSeq._wrap(self._t + other._t)

    def __len__(self):
        return len(self._t)

    def __getitem__(self, i):
        return self._t[i]

    def __eq__(self, other):
        return isinstance(other, PSeq) and self._t == other._t

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self._t)


def ToSeq(lst):
    return PSeq._wrap(lst)


# --- pure helpers from model.py, contracts stripped ---------------------------

def plain_token_char(c):
    return (c == 95                                # '_'
            or (48 <= c and c <= 57)               # '0'..'9'
            or (65 <= c and c <= 90)               # 'A'..'Z'
            or (97 <= c and c <= 122))             # 'a'..'z'


def quoted(tok):
    return PSeq(39) + tok + PSeq(39)


def rendered(module, class_name, identifier):
    return (module + PSeq(46) + class_name + PSeq(91)
            + quoted(identifier) + PSeq(93))


def import_line(module):
    return PSeq(105, 109, 112, 111, 114, 116, 32) + module


# --- the impl region of model.py, verbatim, contract calls stripped -----------

def serialize_member(module, class_name, identifier, payload):
    # frag = module + "." + class_name + "[" + "'" + identifier + "'" + "]"
    frag = []  # type: List[int]
    frag = frag + module
    frag = frag + [46]                       # '.'
    frag = frag + class_name
    frag = frag + [91]                       # '['
    frag = frag + [39]                       # "'"
    frag = frag + identifier
    frag = frag + [39]                       # "'"
    frag = frag + [93]                       # ']'
    imp = [105, 109, 112, 111, 114, 116, 32] + module   # "import " + module
    return (frag, imp)


# --- bridge helpers ------------------------------------------------------------

def cps(s):
    return [ord(ch) for ch in s]


def requires_ok(identifier):
    """The Requires domain: every identifier code point is a plain token
    char (module / class_name / payload are unconstrained texts)."""
    return all(plain_token_char(ord(ch)) for ch in identifier)


class _Carrier(object):
    """Minimal object exposing the three attributes the real method reads:
    its class's __module__ and __name__, and a stable ``name``. Lets the
    differential run cover the whole Requires domain (module/class texts of
    any shape, identifiers the enumeration constructors would reject) while
    still calling the REAL patched method as the oracle."""
    pass


def make_value(module, class_name, name, payload):
    cls = type(_Carrier)(class_name, (_Carrier,), {})
    cls.__module__ = module
    obj = cls()
    obj.name = name
    obj.value = payload
    return obj


# --- differential driver --------------------------------------------------------

def check(serializer_cls, value, module, class_name, name, payload):
    """Run shadow and REAL patched serializer on one input; return an error
    string on disagreement, else None."""
    mod_l, cls_l, id_l, pay_l = cps(module), cps(class_name), cps(name), cps(payload)
    shadow_frag, shadow_imp = serialize_member(mod_l, cls_l, id_l, pay_l)

    real_string, real_imports = serializer_cls(value).serialize()

    if cps(real_string) != shadow_frag:
        return ("DISAGREEMENT (fragment) on module=%r class=%r name=%r payload=%r:\n"
                "  shadow (impl region) -> %r\n"
                "  real patched serializer -> %r (code points %r)"
                % (module, class_name, name, payload,
                   shadow_frag, real_string, cps(real_string)))
    if len(real_imports) != 1:
        return ("DISAGREEMENT (import set arity) on module=%r class=%r name=%r "
                "payload=%r:\n  shadow models a single import line -> %r\n"
                "  real patched serializer import set -> %r"
                % (module, class_name, name, payload, shadow_imp, real_imports))
    only = next(iter(real_imports))
    if cps(only) != shadow_imp:
        return ("DISAGREEMENT (import line) on module=%r class=%r name=%r "
                "payload=%r:\n  shadow (impl region) -> %r\n"
                "  real patched serializer -> %r (code points %r)"
                % (module, class_name, name, payload,
                   shadow_imp, only, cps(only)))
    # internal cross-check: the executable impl agrees with the pure spec view
    if (ToSeq(shadow_frag) != rendered(ToSeq(mod_l), ToSeq(cls_l), ToSeq(id_l))
            or ToSeq(shadow_imp) != import_line(ToSeq(mod_l))):
        return ("INTERNAL: impl region and pure functions disagree on "
                "module=%r class=%r name=%r" % (module, class_name, name))
    return None


TOKEN_ALPHABET = ("abcdefghijklmnopqrstuvwxyz"
                  "ABCDEFGHIJKLMNOPQRSTUVWXYZ_0123456789")

# broad text alphabet for the unconstrained module / class / payload inputs
TEXT_ALPHABET = (list(TOKEN_ALPHABET)
                 + list(".:/[]'\"\\%s%r{}() -\t\n")
                 + ['\u00e9', '\u2022', '\U0001F600', '\u00a0', '\u3000'])


def boundary_members():
    """Real enumeration members: the shapes the target tests observe plus a
    real stdlib flag enumeration routed through the same serializer."""
    class TextEnum(enum.Enum):
        A = 'a-value'
        B = 'value-b'

    class BinaryEnum(enum.Enum):
        A = b'a-value'
        B = b'value-b'

    class IntEnum(enum.IntEnum):
        A = 1
        B = 2

    members = list(TextEnum) + list(BinaryEnum) + list(IntEnum)
    members += list(re.RegexFlag)
    # synthesised enumerations over assorted member names/payloads
    E1 = enum.Enum("Choice", {"GOOD": "g", "BAD": "b", "UGLY": "u"})
    E2 = enum.IntEnum("Level", {"LOW": 1, "MID": 2, "HIGH": 3})
    members += list(E1) + list(E2)
    return members


def boundary_carriers():
    """Requires-boundary shapes reachable only through the carrier."""
    cases = []
    # identifier boundaries: empty, single chars at each class edge, digit-led
    idents = ["", "_", "a", "z", "A", "Z", "0", "9",
              "0abc", "9_9", "___", "a0Z_9", "class", "None", "True",
              "x" * 200]
    for nm in idents:
        cases.append(("m", "C", nm, "p"))
    # module / class / payload boundaries: empty, dots, brackets, quotes,
    # whitespace, non-ASCII — all unconstrained by the Requires
    texts = ["", ".", "a.b.c", "mod[x]", "we'ird", 'dq"uote', "back\\slash",
             "sp ace", "tab\there", "\u00e9\u2022", "\U0001F600",
             "import ", "os.path"]
    for t in texts:
        cases.append((t, "C", "NAME", "p"))
        cases.append(("m", t, "NAME", "p"))
        cases.append(("m", "C", "NAME", t))
    return cases


def main():
    from django.db.migrations.serializer import EnumSerializer

    checked = 0

    # boundary 1: real enumeration members through the real serializer
    for m in boundary_members():
        name = m.name
        if not requires_ok(name):
            continue
        module = m.__class__.__module__
        class_name = m.__class__.__name__
        payload = repr(m.value)
        err = check(EnumSerializer, m, module, class_name, name, payload)
        if err:
            print(err)
            return 1
        checked += 1

    # boundary 2: Requires-edge shapes via the carrier
    for module, class_name, name, payload in boundary_carriers():
        assert requires_ok(name)
        v = make_value(module, class_name, name, payload)
        err = check(EnumSerializer, v, module, class_name, name, payload)
        if err:
            print(err)
            return 1
        checked += 1

    # sweep: every single-token-char identifier, and a stride of pairs
    singles = list(TOKEN_ALPHABET)
    for nm in singles:
        v = make_value("mod.sub", "Kind", nm, "payload")
        err = check(EnumSerializer, v, "mod.sub", "Kind", nm, "payload")
        if err:
            print(err)
            return 1
        checked += 1
    for a in singles[::4]:
        for b in singles[::4]:
            nm = a + b
            v = make_value("m", "K", nm, "p")
            err = check(EnumSerializer, v, "m", "K", nm, "p")
            if err:
                print(err)
                return 1
            checked += 1

    # randomized fuzz over the full Requires domain (pinned seed)
    rng = random.Random(SEED)

    def rand_text(max_len):
        return "".join(rng.choice(TEXT_ALPHABET)
                       for _ in range(rng.randint(0, max_len)))

    def rand_ident(max_len):
        return "".join(rng.choice(TOKEN_ALPHABET)
                       for _ in range(rng.randint(0, max_len)))

    for _ in range(N_FUZZ):
        module = rand_text(16)
        class_name = rand_text(12)
        name = rand_ident(14)
        payload = rand_text(10)
        v = make_value(module, class_name, name, payload)
        err = check(EnumSerializer, v, module, class_name, name, payload)
        if err:
            print(err)
            return 1
        checked += 1

    print("G-CONF OK: shadow impl == real patched enum serializer on %d "
          "inputs (real members + Requires-edge carriers + token sweep + %d "
          "fuzz, seed %d); 0 disagreements." % (checked, N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
