#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-14580 (nagini).

SHADOW: the impl region of model.py, copied verbatim below with the contract
calls (Requires/Ensures/Invariant/Assert) stripped and PSeq realized as an
immutable tuple shim. The @Pure helpers (the identity tags, the two rendered
texts, the directive constants) copy over as plain functions. There are no
@ContractOnly callees in this bundle.

ORACLE: the REAL patched repo function the model models per mapping.md —
`django.db.migrations.serializer.TypeSerializer.serialize`, reached through
`MigrationWriter.serialize` (a pass-through dispatch wrapper, unchanged and
outside the modeled scope). The gate applies patch.diff to /testbed before this
script runs; PYTHONPATH=/testbed makes the patched package importable.

Type bridge (mapping.md section 2):
  * the type object being rendered <-> an integer identity tag: tag
    base_ref_tag() denotes the first distinguished type (the base-class
    reference) and other_ref_tag() the second (the no-import reference); only
    WHICH distinguished row matches is observable, so the bridge is a 2-entry
    tag->type table;
  * str <-> List[int] of Unicode code points: shadow text decodes via chr();
  * the directive set (at most one element per row) <-> the single directive's
    code points, empty list = empty set: shadow imports decode to set() when
    empty, else the singleton set of the decoded directive.

Input domain: Requires restricts value_tag to the two distinguished tags (the
non-distinguished path is unmodeled), so the Requires-satisfying domain is
exactly {base_ref_tag(), other_ref_tag()}. Coverage = both boundary values
enumerated explicitly, plus 100000 seeded fuzz draws over that domain (each
draw runs shadow AND oracle fresh, exercising determinism of both).

>= 1e5 Requires-satisfying inputs: 2 boundary + 100000 fuzz.
Pinned fuzz seed: 145801.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only.
"""
import json
import random
import sys

SEED = 145801
N_FUZZ = 100_000


# --- PSeq shim: immutable sequence, the operations the impl region uses ------

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


# --- pure helpers from model.py, contracts stripped ---------------------------

def base_ref_tag():
    return 1


def other_ref_tag():
    return 2


def base_ref_text():
    # 'models.Model'
    return PSeq(109, 111, 100, 101, 108, 115, 46, 77, 111, 100, 101, 108)


def other_ref_text():
    # 'type(None)'
    return PSeq(116, 121, 112, 101, 40, 78, 111, 110, 101, 41)


def base_ref_directive():
    # 'from django.db import models'
    return PSeq(102, 114, 111, 109, 32, 100, 106, 97, 110, 103, 111, 46, 100,
                98, 32, 105, 109, 112, 111, 114, 116, 32, 109, 111, 100, 101,
                108, 115)


def other_ref_directive_empty():
    return PSeq(0).take(0)


class Serialized:
    def __init__(self):
        self.text = []
        self.imports = []


# --- the impl region of model.py, verbatim, contract calls stripped -----------

def serialize_type(value_tag):
    # Build the table of distinguished types exactly as the serializer does:
    # row 0 is the base-class reference (text + its namespace-import directive),
    # row 1 is the no-import reference (text + empty directive set).
    tags = [base_ref_tag(), other_ref_tag()]
    texts = [base_ref_text(), other_ref_text()]
    directives = [base_ref_directive(), other_ref_directive_empty()]

    result = Serialized()
    i = 0
    while i < len(tags):
        if tags[i] == value_tag:
            t = texts[i]
            d = directives[i]
            text_out = []
            j = 0
            while j < len(t):
                text_out.append(t[j])
                j = j + 1
            d = directives[i]
            imports_out = []
            m = 0
            while m < len(d):
                imports_out.append(d[m])
                m = m + 1
            result.text = text_out
            result.imports = imports_out
            return result
        i = i + 1
    # Unreachable for Requires-satisfying inputs: value_tag is one of the two
    # table tags, so the scan above matches one row.
    return result


# --- bridge: tag <-> type object, code points <-> str / directive set ---------

def decode(code_points):
    return "".join(chr(c) for c in code_points)


def shadow_as_repo_pair(res):
    """Lift a shadow result to the oracle's carrier: (str, set-of-str)."""
    text = decode(res.text)
    imports = set() if len(res.imports) == 0 else {decode(res.imports)}
    return text, imports


def check_tag(oracle, tag_to_type, value_tag):
    """Run shadow and oracle on one Requires-satisfying tag; return an error
    string on disagreement, else None."""
    shadow_pair = shadow_as_repo_pair(serialize_type(value_tag))
    real_text, real_imports = oracle(tag_to_type[value_tag])
    real_pair = (real_text, set(real_imports))
    if shadow_pair != real_pair:
        return ("DISAGREEMENT\n  value_tag=%r (type %r)\n  shadow=%r\n  real=%r"
                % (value_tag, tag_to_type[value_tag], shadow_pair, real_pair))
    return None


def _configure_django():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
            USE_I18N=False,
            DATABASES={},
        )
    django.setup()


def main():
    _configure_django()
    from django.db import models
    from django.db.migrations.writer import MigrationWriter  # REAL patched callee path

    oracle = MigrationWriter.serialize
    tag_to_type = {
        base_ref_tag(): models.Model,   # the base-class reference type
        other_ref_tag(): type(None),    # the no-import reference type
    }

    domain = sorted(tag_to_type)
    checked = 0

    # boundary: the whole (two-element) Requires-satisfying domain, explicitly
    for value_tag in domain:
        err = check_tag(oracle, tag_to_type, value_tag)
        if err:
            print(err)
            return 1
        checked += 1

    # fuzz: seeded draws over the same domain (fresh shadow + oracle run each)
    rng = random.Random(SEED)
    for _ in range(N_FUZZ):
        err = check_tag(oracle, tag_to_type, rng.choice(domain))
        if err:
            print(err)
            return 1
        checked += 1

    print("G-CONF OK: shadow impl == real serializer on %d inputs "
          "(%d boundary + %d fuzz, seed %d)."
          % (checked, len(domain), N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
