#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-16801 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same inputs and comparing observable outputs:

  * SHADOW — the R/I-tagged ops of Solution.lean's impl regions
             (`registerInitHandler`/`shouldRegister` and
             `dimensionWrites`/`dimUpdate`) transliterated to Python, over the
             real repo types via the mapping.md §2 bijection (Python truthiness
             ↔ Bool). This bundle consumes no axiom, so the shadow is pure R/I.
  * ORACLE — `patch.diff`'s behaviour, driving the *real patched* Django code
             (the harness applies the gold patch before this runs, G-RESOLVE):
       site 1 — build a model class with an ImageField configured per the input
                and observe whether `signals.post_init` gains a receiver for that
                class (exactly the F2P `test_post_init_not_connected` predicate),
                via the patched `ImageField.contribute_to_class`;
       site 2 — call the patched `ImageField.update_dimension_fields` bound to a
                real ImageField against a fake instance, recording which
                companion dimension fields it writes back.

They must agree on every input. Exit 0 iff zero disagreements; any disagreement
is a mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image, gold patch applied).
stdlib + django only. The fuzz seed is pinned (mapping.md §4) for a
deterministic verdict. Site 1's input space is the finite Boolean cube {0,1}^3,
enumerated exhaustively (definitive); site 2's is {0,1}^7, enumerated
exhaustively plus a pinned random fuzz to satisfy the ≥10^5 convention.
"""
import random
import sys

SEED = 16801
N_FUZZ = 100_000


def _configure_django():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            DEBUG=True,
            ALLOWED_HOSTS=["*"],
            DATABASES={},
            INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
            DEFAULT_AUTO_FIELD="django.db.models.AutoField",
        )
    django.setup()


# --- the R/I shadow: Solution.lean shouldRegister / dimUpdate ---------------

def shadow_register(is_abstract, has_width, has_height):
    """shouldRegister isAbstract hasWidthField hasHeightField."""
    return (not is_abstract) and (has_width or has_height)


def shadow_dim(deferred, force, has_file, has_width, width_filled,
               has_height, height_filled):
    """dimUpdate ... -> (writeWidth, writeHeight)."""
    dim_filled = not ((has_width and not width_filled)
                      or (has_height and not height_filled))
    proceed = (not deferred) and (has_file or force) and ((not dim_filled) or force)
    return (has_width and proceed, has_height and proceed)


# --- the oracle, site 1: the patched ImageField.contribute_to_class ---------

_reg_counter = [0]


def oracle_register(is_abstract, has_width, has_height):
    """Build a model class with an ImageField configured per the input and
    report whether the patched contribute_to_class connected a post_init
    receiver for that class (exactly the F2P predicate). Each call uses a fresh
    uniquely-named class under an installed app label, and clears the global
    post_init receivers first so the membership test is unambiguous."""
    from django.db import models
    from django.db.models import signals

    signals.post_init.receivers = []
    signals.post_init.sender_receivers_cache.clear()

    _reg_counter[0] += 1
    name = "Conf16801M%d" % _reg_counter[0]
    attrs = {"__module__": "django.contrib.contenttypes.models"}
    if has_width:
        attrs["w"] = models.IntegerField(null=True)
    if has_height:
        attrs["h"] = models.IntegerField(null=True)
    attrs["img"] = models.ImageField(
        width_field="w" if has_width else None,
        height_field="h" if has_height else None,
    )
    meta_attrs = {"app_label": "contenttypes"}
    if is_abstract:
        meta_attrs["abstract"] = True
    attrs["Meta"] = type("Meta", (), meta_attrs)
    Model = type(name, (models.Model,), attrs)

    sender_ids = [sid for (_, sid), *_ in signals.post_init.receivers]
    return id(Model) in sender_ids


# --- the oracle, site 2: the patched ImageField.update_dimension_fields -----

class _FakeFile:
    def __init__(self, truthy):
        self._truthy = truthy
        self.width = 7
        self.height = 11

    def __bool__(self):
        return self._truthy


class _FakeInstance:
    """A minimal stand-in for a model instance: records which attributes the
    method writes via setattr, and answers the getattr / __dict__ membership
    queries the method makes."""

    def __init__(self, attname, attname_present, file_obj, width_filled,
                 height_filled):
        object.__setattr__(self, "_writes", set())
        d = object.__getattribute__(self, "__dict__")
        if attname_present:
            d[attname] = file_obj            # getattr(instance, attname) -> file
        d["w"] = "x" if width_filled else ""   # getattr(instance, "w")
        d["h"] = "y" if height_filled else ""  # getattr(instance, "h")

    def __setattr__(self, name, value):
        object.__getattribute__(self, "_writes").add(name)
        object.__getattribute__(self, "__dict__")[name] = value


def oracle_dim(deferred, force, has_file, has_width, width_filled,
               has_height, height_filled):
    """Drive the patched update_dimension_fields and report which companion
    fields it writes -> (writeWidth, writeHeight)."""
    from django.db.models.fields.files import ImageField

    f = ImageField(
        width_field="w" if has_width else None,
        height_field="h" if has_height else None,
    )
    f.attname = "img"

    attname_present = not deferred
    file_obj = _FakeFile(has_file) if attname_present else None
    inst = _FakeInstance("img", attname_present, file_obj,
                         width_filled, height_filled)

    f.update_dimension_fields(inst, force=force)
    writes = object.__getattribute__(inst, "_writes")
    return ("w" in writes, "h" in writes)


def main():
    _configure_django()
    rng = random.Random(SEED)
    disagreements = []
    count = 0

    bools = (False, True)

    # --- site 1: registration decision (exhaustive over {0,1}^3) -------------
    for is_abstract in bools:
        for has_width in bools:
            for has_height in bools:
                count += 1
                shadow = shadow_register(is_abstract, has_width, has_height)
                oracle = oracle_register(is_abstract, has_width, has_height)
                if shadow != oracle:
                    disagreements.append(
                        ("register", (is_abstract, has_width, has_height),
                         shadow, oracle))

    # --- site 2: synchronization writes (exhaustive {0,1}^7 + pinned fuzz) ---
    def check_dim(cfg):
        nonlocal count
        count += 1
        shadow = shadow_dim(*cfg)
        oracle = oracle_dim(*cfg)
        if shadow != oracle:
            disagreements.append(("dim", cfg, shadow, oracle))

    if not disagreements:
        # exhaustive cube
        for i in range(128):
            cfg = tuple(bool((i >> b) & 1) for b in range(7))
            check_dim(cfg)
            if len(disagreements) >= 5:
                break

    if not disagreements:
        # pinned random fuzz to satisfy the >=10^5 convention
        for _ in range(N_FUZZ):
            cfg = tuple(rng.random() < 0.5 for _ in range(7))
            check_dim(cfg)
            if len(disagreements) >= 5:
                break

    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for kind, inp, sh, orc in disagreements[:5]:
            print("  [%s] input=%r shadow=%r oracle=%r" % (kind, inp, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of registerInitHandler/dimensionWrites agrees "
          "with patch.diff behaviour on %d inputs (seed=%d): site 1 exhaustive "
          "({0,1}^3), site 2 exhaustive ({0,1}^7) + %d fuzz, 0 disagreements."
          % (count, SEED, N_FUZZ))
    return 0


if __name__ == "__main__":
    sys.exit(main())
