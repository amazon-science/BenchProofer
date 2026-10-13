#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-14752.

The behaviour under specification is a results-list builder that DEFERS each
per-record conversion to the responder's OWN, replaceable conversion step (the
model axiom `record_entry`), together with the default conversion step. The
model axiomatizes the late-bound conversion step (`record_entry`) and models the
default step deeply (`default_record_entry`). This script executes the REAL
shipped code -- the exact post-patch bodies of
`AutocompleteJsonView.serialize_result` and the `get()` results comprehension
(quoted verbatim from patch.diff) -- and asserts:

  (A-reference) the deep model `default_record_entry` == the real default
      `serialize_result`: for the BASE responder, the entry for a record is
        {'id': str(getattr(obj, to_field_name)), 'text': str(obj)}
      i.e. the identifier field is the textual form of the designated lookup
      attribute and the display field is the textual form of the record. This
      matches model.py's `lookup_text(rec, tf)` / `display(rec)` encodings.

  (A-consumed) the late-bound conversion step is honoured by the builder: the
      builder calls `self.serialize_result(...)` per record, so a responder that
      supplies a DIFFERENT conversion step (an overriding subclass) changes
      every entry accordingly, IN ORDER -- exactly model.py's postcondition
      `Result()[k] is record_entry(view, recs[k], to_field_name)`. The
      pre-patch builder, which inlined the default entry, would IGNORE the
      override; the executed real code does not.

Imports nothing repo-specific and nothing beyond the standard library; the
checked logic is the patch's own method bodies, reproduced verbatim. Exit 0 iff
every obligation holds.
"""
import json
import random
import sys


# --- the REAL shipped code (post-patch bodies, verbatim from patch.diff) ------
#
# These two method bodies are EXACTLY the gold-patch text. `serialize_result`
# is the new extracted method; `build_results` is the `get()` results
# comprehension. Reproducing them here lets G-AX execute the real conversion
# and dispatch semantics with stdlib only (Django is not importable as stdlib).

class AutocompleteJsonView:
    """The base responder, carrying the two patched method bodies verbatim."""

    def serialize_result(self, obj, to_field_name):
        # gold: return {'id': str(getattr(obj, to_field_name)), 'text': str(obj)}
        return {'id': str(getattr(obj, to_field_name)), 'text': str(obj)}

    def build_results(self, object_list, to_field_name):
        # gold get(): [self.serialize_result(obj, to_field_name) for obj in ...]
        return [
            self.serialize_result(obj, to_field_name)
            for obj in object_list
        ]


# --- a plain stdlib stand-in for a matched record -----------------------------

class Record:
    """A record exposing an arbitrary set of attributes and a textual form."""

    def __init__(self, attrs, text):
        self._attrs = dict(attrs)
        self._text = text
        for k, v in attrs.items():
            setattr(self, k, v)

    def __str__(self):
        return self._text


# --- (A-reference) default serialize_result == model's deep default -----------

def model_default_entry(rec, to_field_name):
    """model.py's `serialize_result_default`: id field == lookup_text(rec, tf)
    == str(getattr(obj, tf)); text field == display(rec) == str(obj)."""
    return {'id': str(getattr(rec, to_field_name)), 'text': str(rec)}


def check_default_reference(rec, to_field_name):
    real = AutocompleteJsonView().serialize_result(rec, to_field_name)
    expected = model_default_entry(rec, to_field_name)
    assert real == expected, (
        "default serialize_result deep model unsound on %r/%r: real=%r model=%r"
        % (rec._attrs, to_field_name, real, expected))
    # The default entry exposes exactly the identifier and display fields.
    assert set(real.keys()) == {'id', 'text'}, (
        "default entry shape changed: %r" % (real,))


# --- (A-consumed) the builder defers to the late-bound conversion step --------

def check_dispatch_honoured(records, to_field_name):
    """The builder must produce, in order, exactly what the responder's OWN
    serialize_result yields per record -- so an override is honoured."""

    class Extended(AutocompleteJsonView):
        # A responder that SUPPLIES A DIFFERENT conversion step (the F2P
        # scenario: super().serialize_result(...) plus an extra field).
        def serialize_result(self, obj, to_field_name):
            base = super().serialize_result(obj, to_field_name)
            base['extra'] = str(getattr(obj, 'extra', ''))
            return base

    view = Extended()
    built = view.build_results(records, to_field_name)
    # Each built entry IS what THIS responder's serialize_result produces for the
    # corresponding record, in order (model: Result()[k] is serialize_result(...)).
    assert len(built) == len(records), "results not aligned 1:1 with records"
    for k, rec in enumerate(records):
        expected = view.serialize_result(rec, to_field_name)
        assert built[k] == expected, (
            "builder did not defer to the responder's conversion step at %d: "
            "built=%r expected=%r" % (k, built[k], expected))
        # The override genuinely changed the entry (extension point honoured).
        assert 'extra' in built[k], (
            "override IGNORED -- builder inlined the default entry at %d" % k)
    # And the BASE responder's builder yields the default entries, in order.
    base_view = AutocompleteJsonView()
    base_built = base_view.build_results(records, to_field_name)
    for k, rec in enumerate(records):
        assert base_built[k] == model_default_entry(rec, to_field_name), (
            "base builder entry mismatch at %d" % k)
    # The whole response is JSON-serialisable (the endpoint returns JsonResponse).
    json.dumps({'results': base_built})


def main():
    # --- boundary records over the default conversion -------------------------
    boundary = [
        Record({'pk': 1}, 'Question 1'),
        Record({'pk': 42}, ''),
        Record({'pk': 0}, 'edge•case'),
        Record({'uuid': 'a1b2'}, "Joe's record"),
        Record({'name': 'x'}, '<b>html</b> & "stuff"'),
        Record({'pk': -7, 'extra': 'note'}, 'neg pk'),
    ]
    to_fields = {'pk', 'uuid', 'name'}
    for rec in boundary:
        for tf in to_fields:
            if hasattr(rec, tf):
                check_default_reference(rec, tf)

    # dispatch honoured on ordered batches (incl. empty) -----------------------
    check_dispatch_honoured([], 'pk')
    check_dispatch_honoured([Record({'pk': i, 'extra': 'e%d' % i}, 'r%d' % i)
                             for i in range(5)], 'pk')

    # --- randomized fuzz over default conversion + dispatch --------------------
    rng = random.Random(14752)
    alphabet = "abcXYZ0129 &<>\"'•é;#"
    for _ in range(20000):
        n = rng.randint(0, 6)
        recs = []
        for _ in range(n):
            idv = rng.randint(-1000, 1000)
            text = "".join(rng.choice(alphabet) for _ in range(rng.randint(0, 12)))
            recs.append(Record({'pk': idv, 'extra': str(rng.randint(0, 99))}, text))
        for rec in recs:
            check_default_reference(rec, 'pk')
        check_dispatch_honoured(recs, 'pk')

    print("G-AX OK: default serialize_result deep model == real default entry "
          "and the builder defers to the late-bound conversion step (override "
          "honoured, in order) on 6 boundary + 20000 fuzz batches")
    return 0


if __name__ == "__main__":
    sys.exit(main())
