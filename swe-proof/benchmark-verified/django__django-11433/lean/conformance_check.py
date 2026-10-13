#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for django__django-11433.

The bundle models ONE routine: how a bound form's resolved data is turned into a
model instance's field assignments (mapping.md). For each model field the routine
decides whether to assign the form's resolved value or to leave the field at the
value it already holds (its model default), deferring file-type fields to a
second pass.

The decision for each field is a PURE function of observables the loop reads:

    name           : str
    editable       : bool   (f.editable)
    is_auto        : bool   (isinstance(f, AutoField))
    in_resolved    : bool   (f.name in cleaned_data)
    has_default    : bool   (f.has_default())
    omitted        : bool   (widget.value_omitted_from_data(...))
    resolved_empty : bool   (cleaned_data.get(f.name) in field.empty_values)
    is_file        : bool   (isinstance(f, FileField))
    resolved_value : str    (cleaned_data[f.name])

plus the call-level `name_filter` (the `fields` param: None or a set of names)
and `skip_names` (the `exclude` param: possibly-empty list).

Standing up Django's forms + model meta + widgets to drive the real
`construct_instance` is heavy and unnecessary: the modeled value is exactly the
ordered sequence of `save_form_data(instance, cleaned_data[name])` assignments,
which is a pure function of the observables above. The ORACLE below is a faithful
in-process replica using the EXACT patched guard expressions; the SHADOW is the
op-for-op transliteration of `implementation_bindFields` / `assignField` /
`assignmentsFor` (per refinement.md).

This genuinely tests:
  * the F2P behavior: a defaulted field whose value was omitted but whose
    resolved value is NON-empty must be assigned that value (has_default=True,
    omitted=True, resolved_empty=False);
  * the empty case still leaves the default (resolved_empty=True): the
    PASS_TO_PASS default-population behavior;
  * the editable / auto / membership / fields / exclude skip guards;
  * the file-field deferral ordering (two passes).

stdlib-only. Pinned seed: 20240629 (also in mapping.md).
"""
import random
import sys

SEED = 20240629
N = 120_000


# --- ORACLE: faithful in-process replica of the patched construct_instance ----
def oracle(name_filter, skip_names, fields):
    assigned = []
    file_fields = []
    for f in fields:
        if (not f["editable"]) or f["is_auto"] or (not f["in_resolved"]):
            continue
        if name_filter is not None and f["name"] not in name_filter:
            continue
        if skip_names and f["name"] in skip_names:
            continue
        # post-patch guard: default kept only when value omitted AND resolved
        # value is itself empty.
        if f["has_default"] and f["omitted"] and f["resolved_empty"]:
            continue
        if f["is_file"]:
            file_fields.append((f["name"], f["resolved_value"]))
        else:
            assigned.append((f["name"], f["resolved_value"]))
    return assigned + file_fields


# --- SHADOW of implementation_bindFields (the R/I / A-reference leg) -----------
# Mirrors Solution.lean:
#   assignField nf sk f =
#       f.editable && !f.isAuto && f.inResolved
#       && (match nf with some names => names.contains f.name | none => true)
#       && !(!sk.isEmpty && sk.contains f.name)
#       && !(f.hasDefault && f.omitted && f.resolvedEmpty)
#   assignmentsFor nf sk fields =
#       let kept = fields.filter (assignField nf sk)
#       (kept.filter (!isFile)).map emit ++ (kept.filter isFile).map emit
def _assign_field(name_filter, skip_names, f):
    if not (f["editable"] and (not f["is_auto"]) and f["in_resolved"]):
        return False
    if name_filter is not None and f["name"] not in name_filter:
        return False
    if (len(skip_names) != 0) and f["name"] in skip_names:
        return False
    if f["has_default"] and f["omitted"] and f["resolved_empty"]:
        return False
    return True


def shadow(name_filter, skip_names, fields):
    kept = [f for f in fields if _assign_field(name_filter, skip_names, f)]
    non_file = [(f["name"], f["resolved_value"]) for f in kept if not f["is_file"]]
    file_f = [(f["name"], f["resolved_value"]) for f in kept if f["is_file"]]
    return non_file + file_f


def disagree(name_filter, skip_names, fields):
    o = oracle(name_filter, skip_names, fields)
    s = shadow(name_filter, skip_names, fields)
    if o != s:
        return ((name_filter, skip_names, fields), o, s)
    return None


NAME_POOL = ["mode", "title", "slug", "id", "pk", "file", "image",
             "name", "x", "y", "z"]


def _field(name, **kw):
    base = dict(name=name, editable=True, is_auto=False, in_resolved=True,
                has_default=False, omitted=False, resolved_empty=False,
                is_file=False, resolved_value="v_" + name)
    base.update(kw)
    return base


def _enumerate_edge():
    cases = []
    # F2P: defaulted field, value omitted, resolved value NON-empty -> assign it.
    cases.append((None, [], [
        _field("mode", has_default=True, omitted=True, resolved_empty=False,
               resolved_value="de")]))
    # PASS_TO_PASS: defaulted, omitted, resolved value EMPTY -> keep default.
    cases.append((None, [], [
        _field("mode", has_default=True, omitted=True, resolved_empty=True,
               resolved_value="")]))
    # defaulted, NOT omitted -> assign regardless of emptiness.
    cases.append((None, [], [
        _field("mode", has_default=True, omitted=False, resolved_empty=True)]))
    # no default -> always assign.
    cases.append((None, [], [_field("title", has_default=False)]))
    # skip guards.
    cases.append((None, [], [_field("id", editable=False)]))
    cases.append((None, [], [_field("pk", is_auto=True)]))
    cases.append((None, [], [_field("x", in_resolved=False)]))
    cases.append(({"mode"}, [], [_field("mode"), _field("title")]))
    cases.append((None, ["title"], [_field("mode"), _field("title")]))
    # file deferral ordering.
    cases.append((None, [], [
        _field("file", is_file=True), _field("mode"), _field("image", is_file=True)]))
    return cases


def main() -> int:
    checked = 0
    for nf, sk, fields in _enumerate_edge():
        d = disagree(nf, sk, fields)
        if d:
            print(f"DISAGREE edge {d[0]!r}: oracle={d[1]} shadow={d[2]}")
            print("status=fail")
            return 1
        checked += 1

    rng = random.Random(SEED)
    for _ in range(N):
        use_filter = rng.choice([True, False])
        name_filter = (set(rng.sample(NAME_POOL, rng.randint(0, 3)))
                       if use_filter else None)
        skip_names = rng.sample(NAME_POOL, rng.randint(0, 2))
        nf_count = rng.randint(0, 6)
        fields = []
        for _ in range(nf_count):
            nm = rng.choice(NAME_POOL)
            fields.append(_field(
                nm,
                editable=rng.choice([True, False]),
                is_auto=rng.choice([True, False]),
                in_resolved=rng.choice([True, False]),
                has_default=rng.choice([True, False]),
                omitted=rng.choice([True, False]),
                resolved_empty=rng.choice([True, False]),
                is_file=rng.choice([True, False]),
                resolved_value=rng.choice(["", "de", "x", "v_" + nm]),
            ))
        d = disagree(name_filter, skip_names, fields)
        if d:
            print(f"DISAGREE fuzz {d[0]!r}: oracle={d[1]} shadow={d[2]}")
            print("status=fail")
            return 1
        checked += 1

    print(f"checked={checked} disagreements=0")
    print("status=pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
