#!/usr/bin/env python3
"""G-CONF differential conformance for django__django-16899 (plan §4.1).

Refutes (does not prove) the R/I refinement leg of the single modeled function
`readonlyItemCheck` (the per-item report of
`BaseModelAdminChecks._check_readonly_fields_item`). There are NO axioms in this
bundle: the four runtime observations and the four quoted strings are free
inputs (mapping.md §2/§3), so the whole impl region is R/I (conf_skip=false).

  * SHADOW  — Solution.lean's `readonlyItemReport`/`itemDiagnostic`,
              transliterated to Python over the mapping.md bijection
              (`Bool` ↔ the observation, `List Char` ↔ `str`,
              `none` ↔ `[]`, `some msg` ↔ the single `checks.Error` message).
  * ORACLE  — `patch.diff`'s behaviour: the GOLD-PATCHED message logic of
              `_check_readonly_fields_item`, transliterated VERBATIM:

                  if callable(field_name):                  return None
                  elif hasattr(obj, field_name):            return None
                  elif hasattr(obj.model, field_name):      return None
                  else:
                      try:
                          obj.model._meta.get_field(field_name)
                      except FieldDoesNotExist:             # fieldUnknown
                          return ("The value of '%s' refers to '%s', which is "
                                  "not a callable, an attribute of '%s', or an "
                                  "attribute of '%s'."
                                  % (label, field_name,
                                     obj.__class__.__name__,
                                     obj.model._meta.label))
                      else:                                 return None

ORACLE CHOICE — why we transliterate the patched message logic instead of
running the real `_check_readonly_fields_item`:
  The real method needs a configured ModelAdmin/Inline instance, an administered
  model class with migrated `Options`, and the app registry — essentially the
  F2P Django harness — purely to read back one message string. The four
  observations it performs (callable / hasattr / hasattr / get_field) are
  UNCHANGED by the patch; only how the resolved strings are arranged into the
  message changes. So, per the worker prompt and the django__django-11820
  precedent, the ORACLE is the patched message logic transliterated verbatim,
  and the unchanged observations + quoted strings are abstracted into the free
  inputs handed IDENTICALLY to SHADOW and ORACLE. The only thing under
  differential test is the message arrangement the patch actually edits.

We fuzz every combination of the four booleans crossed with random strings
(boundary combinations first, incl. the two F2P scenarios). Exit 0 iff zero
disagreements. stdlib only; fuzz seed pinned (mapping.md §4).
"""
import itertools
import random
import string
import sys

SEED = 16899
N_FUZZ = 100_000


# ---- SHADOW: Solution.lean transliterated ----------------------------------
def item_diagnostic(label, name, admin_name, model_label):
    """`itemDiagnostic` transliterated: the literal segments concatenated with
    the four free strings, in order label, name, admin_name, model_label."""
    return ("The value of '" + label
            + "' refers to '" + name
            + "', which is not a callable, an attribute of '" + admin_name
            + "', or an attribute of '" + model_label
            + "'.")


def shadow_report(is_callable, has_attr_admin, has_attr_model, field_unknown,
                  label, name, admin_name, model_label):
    """`readonlyItemReport` transliterated; None ↔ none, str ↔ some msg."""
    if is_callable:
        return None
    if has_attr_admin:
        return None
    if has_attr_model:
        return None
    if field_unknown:
        return item_diagnostic(label, name, admin_name, model_label)
    return None


# ---- ORACLE: gold-patched _check_readonly_fields_item message logic ---------
def oracle_report(is_callable, has_attr_admin, has_attr_model, field_unknown,
                  label, name, admin_name, model_label):
    if callable_obs(is_callable):
        return None
    elif has_attr_admin:
        return None
    elif has_attr_model:
        return None
    else:
        if field_unknown:                 # get_field raised FieldDoesNotExist
            # The patched format string, verbatim, with the patched arg tuple
            # (label, field_name, obj.__class__.__name__, obj.model._meta.label).
            return (
                "The value of '%s' refers to '%s', which is not a callable, "
                "an attribute of '%s', or an attribute of '%s'."
                % (label, name, admin_name, model_label)
            )
        else:                             # get_field resolved -> []
            return None


def callable_obs(is_callable):
    # `callable(field_name)` is a pure boolean observation; modeled as the input.
    return is_callable


# ---- fuzz inputs -----------------------------------------------------------
def rand_str(rng):
    """A random label/name/class/label-ish string, including the awkward chars
    a real config entry or class name might contain (quotes, %, brackets)."""
    n = rng.randint(0, 18)
    alphabet = string.ascii_letters + string.digits + "_.[]'\"%- "
    return "".join(rng.choice(alphabet) for _ in range(n))


def boundary_cases():
    """The two F2P scenarios + structural boundaries, asserted against BOTH
    shadow and oracle (and, for the F2P rows, against the literal expected
    message) so a transcription error in either side is caught up front."""
    out = []
    # (label, name, admin, model_label) and the four observations.
    # F2P 1: test_nonexistent_field — SongAdmin / 'nonexistent'.
    f1 = ("readonly_fields[1]", "nonexistent", "SongAdmin", "admin_checks.Song")
    out.append(("F2P:test_nonexistent_field",
                False, False, False, True, f1,
                "The value of 'readonly_fields[1]' refers to 'nonexistent', "
                "which is not a callable, an attribute of 'SongAdmin', or an "
                "attribute of 'admin_checks.Song'."))
    # F2P 2: test_nonexistent_field_on_inline — CityInline / 'i_dont_exist'.
    f2 = ("readonly_fields[0]", "i_dont_exist", "CityInline", "admin_checks.City")
    out.append(("F2P:test_nonexistent_field_on_inline",
                False, False, False, True, f2,
                "The value of 'readonly_fields[0]' refers to 'i_dont_exist', "
                "which is not a callable, an attribute of 'CityInline', or an "
                "attribute of 'admin_checks.City'."))
    # acceptable paths -> None (no Error)
    blank = ("readonly_fields[0]", "x", "A", "app.M")
    out.append(("callable",      True,  False, False, False, blank, None))
    out.append(("hasattr_admin", False, True,  False, False, blank, None))
    out.append(("hasattr_model", False, False, True,  False, blank, None))
    out.append(("field_known",   False, False, False, False, blank, None))
    return out


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0

    # Boundary: shadow == oracle AND (where given) both == the expected message.
    for case in boundary_cases():
        name_tag, ic, haa, ham, fu, strs, expected = case
        label, nm, admin, ml = strs
        count += 1
        s = shadow_report(ic, haa, ham, fu, label, nm, admin, ml)
        o = oracle_report(ic, haa, ham, fu, label, nm, admin, ml)
        if s != o:
            disagreements.append(("boundary:%s shadow!=oracle" % name_tag, s, o))
        elif expected is not None and s != expected:
            disagreements.append(("boundary:%s != expected message" % name_tag,
                                  s, expected))

    # Random sweep: every boolean combination crossed with random strings.
    bool_combos = list(itertools.product([False, True], repeat=4))
    for _ in range(N_FUZZ):
        ic, haa, ham, fu = rng.choice(bool_combos)
        label = rand_str(rng)
        nm = rand_str(rng)
        admin = rand_str(rng)
        ml = rand_str(rng)
        count += 1
        s = shadow_report(ic, haa, ham, fu, label, nm, admin, ml)
        o = oracle_report(ic, haa, ham, fu, label, nm, admin, ml)
        if s != o:
            disagreements.append(
                ("obs=%r strs=%r" % ((ic, haa, ham, fu), (label, nm, admin, ml)),
                 s, o))
        if len(disagreements) >= 8:
            break

    if disagreements:
        print("G-CONF FAIL: %d disagreement(s) over %d checks:"
              % (len(disagreements), count))
        for d in disagreements:
            print("  %r shadow=%r oracle/expected=%r" % d)
        return 1
    print("G-CONF OK: R/I shadow of readonlyItemCheck agrees with the "
          "gold-patched _check_readonly_fields_item message logic on %d checks "
          "(boundary F2P scenarios + fuzz, seed=%d), 0 disagreements."
          % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
