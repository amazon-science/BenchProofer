#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-14752 (nagini).

SHADOW: the impl region of model.py, copied verbatim below with the contract
calls (Requires/Ensures/Invariant) stripped: the `build_results` loop, the
`default_record_entry` body, and the `Record`/`Entry` constructor assignments.
The bundle has no @Pure helper functions. The three @ContractOnly callees are
bridged to the REAL repo code:
  * `record_entry(view, rec, to_field_name)` — the responder's own late-bound
    conversion step — calls the REAL patched method on the REAL responder
    object bound to `view` (dynamic dispatch included), on the real record
    object bound to `rec`;
  * `lookup_text(rec, to_field_name)` / `display(rec)` — the unchanged
    builtin str-coercion chains — run the real `str(getattr(obj, name))` /
    `str(obj)` on the real record object.

ORACLE: the REAL patched repo functions the model models per mapping.md §1,
imported from the patched tree (the gate applies patch.diff to /testbed before
this script runs; PYTHONPATH=/testbed makes django importable):
  * `AutocompleteJsonView.serialize_result` — the default conversion step —
    called directly (it needs no view state);
  * the results-list construction inside `AutocompleteJsonView.get` — driven
    end-to-end through the real `get` body. `get`'s NON-modeled collaborators
    (request parsing, permission check, queryset construction, context
    assembly) are stubbed by an overriding harness subclass, exactly the
    boundary mapping.md §1 draws: only the results-list construction and the
    conversion step are under model. The real `get` returns a JsonResponse;
    the observed value is its decoded `results` list.

Type bridge (mapping.md §2):
  * a matched record `obj` <-> shadow `Record(id_text, display_text)` where
    `id_text = encode(str(getattr(obj, name)))` and
    `display_text = encode(str(obj))` with `encode(s) = tuple(ord(c))`
    (str <-> PSeq[int] of code points); the shadow Record additionally carries
    a reference to the real object so the bridged callees can run real code;
  * the attribute-name str <-> an int token, via the table `ATTR_NAMES`
    (only identity matters: the token is passed through unchanged);
  * one result dict <-> one `Entry`: `dict['id'] <-> Entry.id_val`,
    `dict['text'] <-> Entry.text_val`. The late-bound step's produced entry is
    opaque to the builder (it may carry further keys), so the `record_entry`
    bridge carries the real produced dict whole and the builder's output list
    is compared dict-for-dict, in order, against the real `results` list;
  * the iterated collection <-> List[Record], index order = iteration order.

Checked disagreement points, per generated input:
  1. shadow `build_results` output == real `get` `results` list (length,
     order, every entry by value), for the BASE responder AND for two
     overriding responders (one extending the default entry, one replacing it
     entirely) — the late-bound dispatch is part of the modeled behaviour;
  2. shadow `default_record_entry` == real `serialize_result` on the base
     responder: `id_val == encode(dict['id'])`, `text_val == encode(dict['text'])`,
     and the default entry carries exactly those two keys.

Input domain: `build_results` Requires only readable record fields (any
list); `default_record_entry` Requires only readable fields (any record).
Boundary cases cover the empty collection, a single record, empty strings,
unicode / HTML-ish / quote-heavy text, non-str attribute values (int, None,
negative int — the textual form is what the model carries), and several
distinct attribute-name tokens. Fuzz draws batch sizes 0..6, random texts
over a mixed alphabet, random attribute values and attribute names.

>= 1e5 Requires-satisfying inputs: 13 boundary batches + 100000 fuzz batches
(each batch feeds check 1 three times and check 2 per record).
Pinned fuzz seed: 14752. stdlib only. Exit 0 iff zero disagreements; on
disagreement prints the input and both outputs and exits 1.
"""
import json
import random
import sys

SEED = 14752
N_FUZZ = 100_000

# --- import the REAL patched repo code (oracle) -------------------------------

import django
from django.conf import settings

if not settings.configured:
    settings.configure()  # defaults suffice: no ORM / apps are touched

from django.contrib.admin.views.autocomplete import AutocompleteJsonView


# --- real-record stand-in (the `obj` side of the bridge) ----------------------

class RealRecord:
    """A plain object exposing one named attribute and a textual form —
    the two things the modeled conversion reads from a matched record."""

    def __init__(self, attr_name, attr_value, text):
        setattr(self, attr_name, attr_value)
        self._text = text

    def __str__(self):
        return self._text


class FakePage:
    def has_next(self):
        return False


class HarnessView(AutocompleteJsonView):
    """Drives the REAL `get` body: only the NON-modeled collaborators
    (request parsing / permission / queryset / context assembly) are stubbed;
    the results-list construction and the conversion step run the real
    patched code (including dynamic dispatch on this responder's type)."""

    def __init__(self, object_list, to_field_name):
        self._objs = list(object_list)
        self._tfn = to_field_name

    def process_request(self, request):
        return "", None, None, self._tfn

    def has_perm(self, request, obj=None):
        return True

    def get_queryset(self):
        return self._objs

    def get_context_data(self, **kwargs):
        return {"object_list": self._objs, "page_obj": FakePage()}


class ExtendingView(HarnessView):
    """A responder supplying a DIFFERENT conversion step that extends the
    default entry with a further key (the documented extension pattern)."""

    def serialize_result(self, obj, to_field_name):
        base = super().serialize_result(obj, to_field_name)
        base["notes"] = str(getattr(obj, "notes", ""))
        return base


class ReplacingView(HarnessView):
    """A responder whose conversion step ignores the default entirely —
    the produced entry is fully opaque to the builder."""

    def serialize_result(self, obj, to_field_name):
        return {"key": str(getattr(obj, to_field_name)) + "!", "n": len(str(obj))}


def real_results(view_cls, objs, to_field_name):
    """Run the REAL patched `get` and decode the results list it built."""
    view = view_cls(objs, to_field_name)
    response = view.get(request=None)
    return json.loads(response.content)["results"]


# --- str <-> PSeq[int] bridge --------------------------------------------------

def encode(s):
    return tuple(ord(c) for c in s)


# --- attribute-name str <-> int token bridge -----------------------------------

ATTR_NAMES = ["pk", "uuid", "name", "code", "ident"]


# --- shadow: model.py impl regions, contracts stripped -------------------------

class Record:
    def __init__(self, id_text, display_text):
        # impl (verbatim)
        self.id_text = id_text            # type: PSeq[int]
        self.display_text = display_text  # type: PSeq[int]


class Entry:
    def __init__(self, id_val, text_val):
        # impl (verbatim)
        self.id_val = id_val      # type: PSeq[int]
        self.text_val = text_val  # type: PSeq[int]


def make_record(real_obj, attr_name):
    """Bridge a real record object to the shadow carrier: the two stored
    texts are the real textual forms; the real object rides along so the
    bridged @ContractOnly callees can run the real code."""
    rec = Record(encode(str(getattr(real_obj, attr_name))),
                 encode(str(real_obj)))
    rec._real = real_obj
    return rec


# @ContractOnly callees: bridged to the REAL repo code -------------------------

def lookup_text(rec, to_field_name):
    # the unchanged builtin chain, run on the real record object
    return encode(str(getattr(rec._real, ATTR_NAMES[to_field_name])))


def display(rec):
    # the unchanged builtin chain, run on the real record object
    return encode(str(rec._real))


def record_entry(view, rec, to_field_name):
    # the responder's OWN late-bound conversion step: the REAL patched
    # method, dynamically dispatched on the real responder bound to `view`.
    # The produced entry is carried whole (dict <-> Entry bridge; the entry
    # is opaque to the builder and may hold further keys).
    return view._real_view.serialize_result(rec._real, ATTR_NAMES[to_field_name])


class View:
    def __init__(self, real_view):
        self._real_view = real_view


def default_record_entry(view, rec, to_field_name):
    # impl (verbatim)
    return Entry(lookup_text(rec, to_field_name), display(rec))


def build_results(view, recs, to_field_name):
    # impl (verbatim, invariants stripped)
    result = []  # type: List[Entry]
    i = 0
    while i < len(recs):
        result.append(record_entry(view, recs[i], to_field_name))
        i = i + 1
    return result


# --- differential checks -------------------------------------------------------

fail_count = 0


def report(label, inputs, shadow_out, real_out):
    global fail_count
    fail_count += 1
    print("DISAGREEMENT (%s)" % label)
    print("  input : %r" % (inputs,))
    print("  shadow: %r" % (shadow_out,))
    print("  real  : %r" % (real_out,))


def describe(objs, attr_name):
    return [(attr_name, getattr(o, attr_name), str(o)) for o in objs]


def check_batch(objs, tf_token):
    attr_name = ATTR_NAMES[tf_token]
    recs = [make_record(o, attr_name) for o in objs]

    # (1) builder vs the real get() results list, for three responder types
    for view_cls in (HarnessView, ExtendingView, ReplacingView):
        real = real_results(view_cls, objs, attr_name)
        # bind the shadow's view to a responder of the SAME dynamic type
        shadow_view = View(view_cls(objs, attr_name))
        shadow = build_results(shadow_view, recs, tf_token)
        if shadow != real:
            report("build_results / %s" % view_cls.__name__,
                   describe(objs, attr_name), shadow, real)
            return

    # (2) default conversion step vs the real method on the base responder
    base = HarnessView(objs, attr_name)
    for o, rec in zip(objs, recs):
        d = base.serialize_result(o, attr_name)
        e = default_record_entry(View(base), rec, tf_token)
        if (set(d.keys()) != {"id", "text"}
                or e.id_val != encode(d["id"])
                or e.text_val != encode(d["text"])):
            report("default_record_entry",
                   describe([o], attr_name),
                   {"id_val": e.id_val, "text_val": e.text_val}, d)
            return


def main():
    # --- boundary batches ------------------------------------------------------
    boundary = [
        ([], 0),
        ([RealRecord("pk", 1, "Question 1")], 0),
        ([RealRecord("pk", 42, "")], 0),
        ([RealRecord("pk", 0, "edge•case")], 0),
        ([RealRecord("uuid", "a1b2-c3", "Joe's record")], 1),
        ([RealRecord("name", "x", '<b>html</b> & "stuff"')], 2),
        ([RealRecord("pk", -7, "neg pk")], 0),
        ([RealRecord("code", None, "none-valued attr")], 3),
        ([RealRecord("ident", "", "empty attr text")], 4),
        ([RealRecord("pk", i, "r%d" % i) for i in range(5)], 0),
        ([RealRecord("pk", i, "same text") for i in range(3)], 0),
        ([RealRecord("uuid", "u%d" % i, "éè%d" % i) for i in range(4)], 1),
        ([RealRecord("pk", 10**12, "big"), RealRecord("pk", -1, "small")], 0),
    ]
    for objs, tf in boundary:
        check_batch(objs, tf)
        if fail_count:
            return 1

    # --- randomized fuzz -------------------------------------------------------
    rng = random.Random(SEED)
    alphabet = "abcXYZ0129 &<>\"'•é;#{}[]:,"
    for it in range(N_FUZZ):
        tf = rng.randrange(len(ATTR_NAMES))
        attr_name = ATTR_NAMES[tf]
        n = rng.randint(0, 6)
        objs = []
        for _ in range(n):
            kind = rng.randrange(3)
            if kind == 0:
                val = rng.randint(-10**6, 10**6)
            elif kind == 1:
                val = "".join(rng.choice(alphabet)
                              for _ in range(rng.randint(0, 10)))
            else:
                val = None
            text = "".join(rng.choice(alphabet)
                           for _ in range(rng.randint(0, 12)))
            o = RealRecord(attr_name, val, text)
            if rng.randrange(2):
                o.notes = "n%d" % rng.randint(0, 99)
            objs.append(o)
        check_batch(objs, tf)
        if fail_count:
            return 1

    print("G-CONF OK: shadow build_results == real results construction "
          "(base + 2 overriding responders) and shadow default entry == real "
          "default conversion on %d boundary + %d fuzz batches (seed %d)"
          % (len(boundary), N_FUZZ, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
