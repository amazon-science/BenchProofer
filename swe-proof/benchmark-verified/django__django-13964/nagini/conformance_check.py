#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-13964 (nagini).

SHADOW: the impl region of model.py, copied verbatim below with the contract
calls (Requires/Ensures/Invariant/Assert) stripped. The @Pure helpers
``is_empty_placeholder`` / ``stored_seq`` copy over as plain functions on top
of a small immutable-tuple PSeq shim (``stored_seq`` is contract-side but
serves here as an internal cross-check of the shadow). ``SaveTarget`` copies
over as a plain attribute holder. There are no @ContractOnly callees in this
bundle (the axioms region is empty).

ORACLE: the REAL patched repo method the model models per mapping.md —
``Model._prepare_related_fields_for_save`` (django/db/models/base.py). The
gate applies patch.diff to /testbed before this script runs, so the imported
method is the patched one. The script configures an in-memory sqlite database
and defines minimal models: a parent whose primary key is a textual field and
a child holding a foreign key to it (plus a numeric-primary-key pair for the
absent-marker supplement). For one input the oracle is: save the parent (so
it carries a real stored key), build a child that references it, force the
child's local stored-key attribute to the chosen value, run the real method,
and read the local attribute back.

Type bridge (mapping.md section 2): the local stored-key attribute value is
``None`` (absent marker) or a ``str``; the model carrier is
``Optional[List[int]]`` of Unicode code points via ``ord`` — ``None`` <-> None,
the empty string <-> [], a concrete textual key <-> a non-empty list. The
referenced object's stored key (a non-empty ``str``) lowers the same way. The
bridge is a bijection, so generation happens over ``str``/None and is lowered
per call; shadow outputs are raised back via ``chr`` before comparison. For
the numeric supplement the integer key is bridged through its decimal-digit
character sequence (also a bijection on positive integers).

Input domain (the Requires): the referenced key is non-empty
(len(related_key) > 0 — the branch runs only once the referenced object has
been saved and carries a real key), and the local attribute may hold anything
(None / empty / non-empty). Generation stresses the decision boundary: the
absent marker, the empty character sequence (the crux of the change),
whitespace-only values (non-empty, hence NOT placeholders), values equal to /
differing from the referenced key, and unicode content.

>= 1e5 Requires-satisfying inputs: boundary grid + 100000 fuzz pairs + the
numeric absent-marker supplement. Pinned fuzz seed: 13964.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only (no f-strings; the container Python may be
older).
"""
import json
import random
import sys

SEED = 13964
N_FUZZ = 100000


# --- PSeq shim: immutable sequence, the operations the pure region uses ------

class PSeq(object):
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

def is_empty_placeholder(value):
    if value is None:
        return True
    return len(value) == 0


def stored_seq(value):
    if value is None:
        return PSeq(0).take(0)
    return ToSeq(value)


# --- SaveTarget from model.py, contracts stripped ------------------------------

class SaveTarget(object):
    def __init__(self, fk):
        self.fk = fk


# --- the impl region of model.py, verbatim, contract calls stripped -----------

def adopt_referenced_key_if_unset(target, related_key):
    if is_empty_placeholder(target.fk):
        # Adopt the referenced object's stored key into the local attribute.
        adopted = []  # type: list
        i = 0
        while i < len(related_key):
            adopted.append(related_key[i])
            i = i + 1
        # (the stripped Assert line carried only a proof-side sequence fact)
        target.fk = adopted


# --- oracle: the real patched method on minimal in-memory models ---------------

def build_oracle():
    """Configure Django with an in-memory sqlite database and create the
    minimal model pairs the differential drive needs. Models declare an
    explicit app_label so no synthetic app has to be importable. Returns
    (ChildTextFK_factory, ChildAutoFK_factory)."""
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            INSTALLED_APPS=[],
            DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3",
                                   "NAME": ":memory:"}},
        )
    django.setup()

    from django.db import connection, models

    class ParentTextPK(models.Model):
        name = models.CharField(primary_key=True, max_length=64)

        class Meta:
            app_label = "confcheck"

    class ChildToTextPK(models.Model):
        parent = models.ForeignKey(ParentTextPK, on_delete=models.CASCADE)

        class Meta:
            app_label = "confcheck"

    class ParentAutoPK(models.Model):
        class Meta:
            app_label = "confcheck"

    class ChildToAutoPK(models.Model):
        parent = models.ForeignKey(ParentAutoPK, on_delete=models.CASCADE)

        class Meta:
            app_label = "confcheck"

    for m in (ParentTextPK, ChildToTextPK, ParentAutoPK, ChildToAutoPK):
        with connection.schema_editor() as editor:
            editor.create_model(m)

    return ParentTextPK, ChildToTextPK, ParentAutoPK, ChildToAutoPK


class TextOracle(object):
    """Drives the real patched method on the textual-primary-key pair.
    Saved parents are cached per key (the primary key must be unique), so a
    fresh in-memory child per query is the only per-input cost."""

    def __init__(self, ParentTextPK, ChildToTextPK):
        self.Parent = ParentTextPK
        self.Child = ChildToTextPK
        self._attname = ChildToTextPK._meta.get_field("parent").attname
        self._saved = {}

    def run(self, fk_value, key):
        """fk_value: None or str (the child's local stored-key attribute on
        entry). key: non-empty str (the referenced object's stored key).
        Returns the local attribute after the real method runs."""
        parent = self._saved.get(key)
        if parent is None:
            parent = self.Parent(name=key)
            parent.save()
            self._saved[key] = parent
        child = self.Child(parent=parent)
        # Force the local stored-key attribute to the chosen entry value.
        # Write the instance dict directly: assigning through the attribute
        # descriptor drops the cached related object when the value changes,
        # which would make the real method skip the modeled branch (the model
        # presupposes the reference is present — mapping.md section 1). The
        # branch under test reads exactly this stored slot.
        child.__dict__[self._attname] = fk_value
        child._prepare_related_fields_for_save(operation_name="save")
        return getattr(child, self._attname)


# --- differential driver --------------------------------------------------------

def lower(value):
    """Bridge str/None -> Optional[List[int]] (code points)."""
    if value is None:
        return None
    return [ord(ch) for ch in value]


def raise_back(carrier):
    """Bridge Optional[List[int]] -> str/None."""
    if carrier is None:
        return None
    return "".join(chr(c) for c in carrier)


def check_text(oracle, fk_value, key):
    """Run shadow and real method on one (local value, referenced key) pair;
    return an error string on disagreement, else None."""
    target = SaveTarget(lower(fk_value))
    related = lower(key)
    adopt_referenced_key_if_unset(target, related)
    shadow = raise_back(target.fk)
    real = oracle.run(fk_value, key)
    if shadow != real:
        return ("DISAGREEMENT on local value %r with referenced key %r:\n"
                "  shadow (impl region)      = %r\n"
                "  real (patched repo method) = %r"
                % (fk_value, key, shadow, real))
    # internal cross-check against the pure spec helpers
    if is_empty_placeholder(lower(fk_value)):
        if stored_seq(target.fk) != ToSeq(related):
            return ("INTERNAL: adopted sequence != referenced key sequence "
                    "for local value %r, key %r" % (fk_value, key))
    else:
        if stored_seq(target.fk) != stored_seq(lower(fk_value)):
            return ("INTERNAL: non-placeholder value not preserved for "
                    "local value %r" % (fk_value,))
    return None


def boundary_grid():
    """Boundary (local value, referenced key) pairs. Local values stress the
    placeholder frontier: the absent marker, the empty sequence, whitespace-only
    (non-empty!), single characters, values equal to the key, and unicode."""
    keys = ["a", "0", "k1", "some-key", "UPPER", "key key", "n\xe9e",
            "\u4e2d\u6587", "\U0001F600", " ", ":", "0000"]
    fk_values = [None, "", " ", "  ", "\t", "\xa0", "\u3000",
                 "0", "x", "a", "some-key", "some-key2", "some-ke",
                 "None", "[]", "-1", "\U0001F600", "n\xe9e", ":", "@",
                 "a" * 64]
    pairs = []
    for k in keys:
        for v in fk_values:
            pairs.append((v, k))
        pairs.append((k, k))          # local value == referenced key
        pairs.append((k + "z", k))    # local value != referenced key
    return pairs


def main():
    ParentTextPK, ChildToTextPK, ParentAutoPK, ChildToAutoPK = build_oracle()
    oracle = TextOracle(ParentTextPK, ChildToTextPK)

    checked = 0

    boundary = boundary_grid()
    for fk_value, key in boundary:
        err = check_text(oracle, fk_value, key)
        if err:
            print(err)
            return 1
        checked += 1

    # randomized fuzz over the bridged domain (pinned seed): keys drawn from a
    # pre-built pool (each parent saved once), local values weighted toward the
    # placeholder frontier (absent marker / empty / short strings).
    rng = random.Random(SEED)
    alphabet = (list("abcdefgh") + list("XYZ") + list("0123456789")
                + list("-._%:@/ ") + ["\t", "\xa0", "\u3000",
                                      "\xe9", "\u4e2d", "\U0001F600"])

    def rand_str(lo, hi):
        n = rng.randint(lo, hi)
        return "".join(rng.choice(alphabet) for _ in range(n))

    key_pool = []
    seen = set()
    while len(key_pool) < 300:
        k = rand_str(1, 12)
        if k not in seen:
            seen.add(k)
            key_pool.append(k)

    for _ in range(N_FUZZ):
        key = rng.choice(key_pool)
        roll = rng.random()
        if roll < 0.20:
            fk_value = None            # absent marker
        elif roll < 0.40:
            fk_value = ""              # empty character sequence (the crux)
        elif roll < 0.50:
            fk_value = key             # already holds the referenced key
        else:
            fk_value = rand_str(0, 10)  # arbitrary (length 0 hits '' again)
        err = check_text(oracle, fk_value, key)
        if err:
            print(err)
            return 1
        checked += 1

    # numeric absent-marker supplement: a foreign key to an auto (integer)
    # primary key starts as None; the real method adopts the integer key, the
    # shadow adopts its decimal-digit carrier (bijective on positive ints).
    for _ in range(10):
        parent = ParentAutoPK()
        child = ChildToAutoPK(parent=parent)
        parent.save()
        if child.parent_id is not None:
            print("SETUP: expected the absent marker for an unsaved-then-saved "
                  "numeric reference, got %r" % (child.parent_id,))
            return 1
        child._prepare_related_fields_for_save(operation_name="save")
        real = child.parent_id
        target = SaveTarget(None)
        adopt_referenced_key_if_unset(target, lower(str(parent.pk)))
        shadow = raise_back(target.fk)
        if shadow != str(real):
            print("DISAGREEMENT on numeric absent-marker case (pk %r):\n"
                  "  shadow (impl region, digit carrier) = %r\n"
                  "  real (patched repo method)          = %r"
                  % (parent.pk, shadow, real))
            return 1
        checked += 1

    print("G-CONF OK: shadow impl == real patched method on %d inputs "
          "(%d boundary + %d fuzz + numeric supplement, seed %d); "
          "0 disagreements." % (checked, len(boundary), N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
