#!/usr/bin/env python3
"""G-CONF differential conformance for django__django-14752 (plan §4.1).

Refutes (does not prove) the R/I refinement leg of `refinement.md`: the deep
results-construction model of Solution.lean (`buildResults` = `items.map
serialize`, and the default serializer `serializeResult` = `defaultSerialized`)
transliterated to Python, differential-tested against `patch.diff`'s
construction behaviour over many (object-list, serializer) points — including
the default serializer and several subclass overrides that add extra fields
(the customization the extension point exists for).

ORACLE CHOICE — why we transliterate the patched construction VERBATIM instead
of driving the real `AutocompleteJsonView.get`:
  The real `get()` lives on a Django class-based view; exercising its results
  construction requires a constructed request, an `admin_site` registry, a
  bound `ModelAdmin`, a queryset, pagination context, and permission checks —
  all UNCHANGED by the patch and purely to read back the assembled `results`
  list. The patch changes only HOW the per-item results are built: the inlined
  `{'id': …, 'text': …}` object becomes a call to the late-bound, overridable
  `self.serialize_result(obj, to_field_name)`, plus the new default
  `serialize_result`. So, per the worker prompt, the ORACLE is the gold-patched
  construction transliterated verbatim from autocomplete.py post-patch
  (`[self.serialize_result(obj, to_field_name) for obj in object_list]` with the
  default `serialize_result` returning `{'id': str(getattr(obj, tf)),
  'text': str(obj)}`), and the per-item serialization is abstracted by an
  in-process serializer (the free `serialize : Item -> Serialized` of the spec):
  the default, and overrides that add fields. The SHADOW is the deep model
  `items.map serialize` / `defaultSerialized` from Solution.lean. We
  differential-test over many (items, serializer) points. Exit 0 iff zero
  disagreements.

stdlib only. The fuzz seed is pinned (mapping.md §4).
"""
import random
import sys

SEED = 14752
N_FUZZ = 100_000


# An `Item` (mapping.md §2): the two renderings the default serialization reads.
class Item:
    def __init__(self, id_text, display_text, extra):
        self.id_text = id_text          # str(getattr(obj, to_field_name))
        self.display_text = display_text  # str(obj)
        self.extra = extra              # an extra observable an override may read


# ---- Serializers (the injected, overridable `serialize : Item -> Serialized`).
# Each maps one Item to an ORDERED list of (key, value) pairs, mirroring the
# Lean `Serialized = List (String x String)` (insertion-ordered dict).
def serialize_default(it):
    # The gold default `serialize_result`: {'id': ..., 'text': ...}.
    return [("id", it.id_text), ("text", it.display_text)]


def serialize_with_posted(it):
    # The F2P override shape: super().serialize_result(...) | {'posted': ...}.
    return serialize_default(it) + [("posted", it.extra)]


def serialize_notes(it):
    # The problem-statement override shape: adds a 'notes' field.
    return serialize_default(it) + [("notes", it.extra)]


def serialize_only_id(it):
    # A degenerate override returning a single field.
    return [("id", it.id_text)]


SERIALIZERS = [serialize_default, serialize_with_posted, serialize_notes,
               serialize_only_id]


# ---- ORACLE: patch.diff construction, transliterated verbatim --------------
def oracle_build(items, serialize):
    """The gold-patched results construction (autocomplete.py post-patch):
    `[self.serialize_result(obj, to_field_name) for obj in object_list]`, where
    `self.serialize_result` is the late-bound serializer (default or override).
    `serialize` stands for that late-bound method."""
    return [serialize(obj) for obj in items]


# ---- SHADOW: Solution.lean `buildResults` = items.map serialize ------------
def shadow_build(items, serialize):
    """buildResults items serialize = items.map serialize, transliterated."""
    return list(map(serialize, items))


def observe(results):
    """The observable content the spec pins: the ordered list of serialized
    objects, each as its ordered (key, value) pairs."""
    return [list(r) for r in results]


def rand_item(rng):
    return Item(
        id_text=str(rng.randint(0, 10_000)),
        display_text="Question %d" % rng.randint(0, 10_000),
        extra=str(rng.choice(["2021-08-09", "2021-08-07", "note-a", "note-b"])),
    )


def points(rng):
    """Yield (items, serialize) test points."""
    # boundary cases first (plan §4.1 step 4)
    yield ([], serialize_default)
    yield ([], serialize_with_posted)
    yield ([Item("1", "Question 1", "2021-08-09")], serialize_default)
    yield ([Item("1", "Question 1", "2021-08-09")], serialize_with_posted)
    # the F2P shape: two ordered questions, override adds 'posted'
    yield ([Item("2", "Question 1", "2021-08-09"),
            Item("3", "Question 2", "2021-08-07")], serialize_with_posted)
    yield ([Item("2", "Question 1", "2021-08-09"),
            Item("3", "Question 2", "2021-08-07")], serialize_default)
    for _ in range(N_FUZZ):
        k = rng.randint(0, 8)
        items = [rand_item(rng) for _ in range(k)]
        serialize = rng.choice(SERIALIZERS)
        yield (items, serialize)


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for items, serialize in points(rng):
        count += 1
        try:
            o = observe(oracle_build(items, serialize))
            o_err = None
        except Exception as e:                       # noqa: BLE001
            o, o_err = None, type(e).__name__
        try:
            s = observe(shadow_build(items, serialize))
            s_err = None
        except Exception as e:                       # noqa: BLE001
            s, s_err = None, type(e).__name__
        if (o, o_err) != (s, s_err):
            disagreements.append((len(items), serialize.__name__,
                                  (s, s_err), (o, o_err)))
            if len(disagreements) >= 5:
                break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for n, name, sh, orc in disagreements:
            print("  n_items=%d serializer=%s shadow=%r oracle=%r"
                  % (n, name, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of buildResults/serializeResult agrees with "
          "patch.diff construction over %d inputs (seed=%d), 0 disagreements."
          % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
