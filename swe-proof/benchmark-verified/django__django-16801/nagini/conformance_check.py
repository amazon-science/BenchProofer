#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-16801 (nagini).

SHADOW: the impl region of model.py, copied verbatim below with the contract
calls (Requires/Ensures) stripped. The @Pure helpers (`configured`,
`should_register`) copy over as plain functions; the `Optional[List[int]]`
name carriers work unchanged as plain Python lists (only `is not None` and
`len` are used). There are no @ContractOnly callees in this bundle.

ORACLE: the REAL patched repo function the model models per mapping.md —
`django.db.models.fields.files.ImageField.contribute_to_class`, driven the
only way it is driven in the repo: by real Django model-class creation with
an image field attached. The gate applies patch.diff to /testbed before this
script runs; PYTHONPATH=/testbed makes the patched module importable.

Type bridge (mapping.md section 2):
  * a companion-target name (str or None) <-> Optional[List[int]] of its
    code points (None <-> None; "" <-> []);
  * the owning class's abstract flag <-> bool, identical;
  * the owning class identity `id(cls)` <-> the int owner token;
  * the post-init notification list <-> the projection of
    `signals.post_init.receivers` to its per-entry sender-id, as a List[int]
    (exactly the membership view the bundle's tests observe);
  * the registration side effect (connecting the field's recalculation
    handler for this sender) <-> appending the owner token.

Each observation snapshots the projected notification list, creates one real
model class (which invokes the real patched `contribute_to_class`), snapshots
again, and compares against the shadow run on the pre-snapshot. The handler
is then disconnected and the class unregistered from the app registry so the
global receiver list and model registry stay O(1) across 1e5 iterations
(both would otherwise make the run quadratic).

Input domain: the Requires only demands write access to the notification
list and read access to the optional name lists, so every
(abstract-flag, optional name, optional name) triple is Requires-satisfying.
Names are drawn over {absent, empty, short, realistic, long, non-identifier}
shapes; the abstract flag uniformly. Boundary cases enumerate the full
{None, "", one-char, realistic, long} x same x {concrete, abstract} decision
table, including the concrete-no-target cell the failing test observes.

>= 1e5 Requires-satisfying inputs: boundary cases + 100000 fuzz triples.
Pinned fuzz seed: 16801.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only.
"""
import json
import random
import sys

SEED = 16801
N_FUZZ = 100_000


# --- pure helpers from model.py, decorators/contracts stripped ---------------

def configured(name):
    return name is not None and len(name) > 0


def should_register(is_abstract, width_target, height_target):
    return (not is_abstract) and (configured(width_target) or configured(height_target))


# --- the impl region of model.py, verbatim, contract calls stripped ----------

def attach_post_init_hook(receivers, owner_id, is_abstract,
                          width_target, height_target):
    if (not is_abstract) and (configured(width_target) or configured(height_target)):
        receivers.append(owner_id)


# --- bridge: optional str name <-> Optional[List[int]] of code points --------

def name_to_carrier(name):
    return None if name is None else [ord(ch) for ch in name]


def main():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(INSTALLED_APPS=[], USE_I18N=False)
    django.setup()

    from django.apps import apps
    from django.db import models
    from django.db.models import signals

    APP_LABEL = "conf16801"

    def receiver_senders():
        """Projection of the post_init notification list to its per-entry
        sender-id tokens (the membership view the bundle's tests observe)."""
        return [sender_id for (_, sender_id), *_ in signals.post_init.receivers]

    seq = [0]

    def check_case(width_name, height_name, abstract):
        """Run oracle (real model-class creation -> real patched
        contribute_to_class) and shadow on one input triple; return an error
        string on disagreement, else None."""
        seq[0] += 1
        before = receiver_senders()

        field = models.ImageField(width_field=width_name,
                                  height_field=height_name, upload_to="t")
        attrs = {
            "__module__": APP_LABEL + ".models",
            "Meta": type("Meta", (), {"app_label": APP_LABEL,
                                      "abstract": abstract}),
            "img": field,
        }
        cls = type("ConfModel%d" % seq[0], (models.Model,), attrs)
        after = receiver_senders()

        shadow = list(before)
        attach_post_init_hook(shadow, id(cls), abstract,
                              name_to_carrier(width_name),
                              name_to_carrier(height_name))

        err = None
        if shadow != after:
            err = ("DISAGREEMENT\n"
                   "  input: abstract=%r width=%r height=%r owner=%d\n"
                   "  notification list before: %r\n"
                   "  shadow after:             %r\n"
                   "  real after:               %r"
                   % (abstract, width_name, height_name, id(cls),
                      before, shadow, after))

        # Per-iteration cleanup: keep the global receiver list and the app
        # registry O(1) so 1e5 iterations stay linear.
        signals.post_init.disconnect(field.update_dimension_fields, sender=cls)
        apps.all_models[APP_LABEL].pop(cls._meta.model_name, None)
        return err

    # Boundary: the full decision table over name shapes x abstractness,
    # including the concrete-both-targets-absent cell.
    shapes = [None, "", "w", "img_width", "x" * 64]
    boundary = [(w, h, a)
                for a in (False, True)
                for w in shapes
                for h in shapes]
    # Non-identifier name content (only truthiness is observed).
    boundary += [("has space", None, False), (None, "é•", False),
                 ("0digits", "\t", True)]

    checked = 0
    for w, h, a in boundary:
        err = check_case(w, h, a)
        if err:
            print(err)
            return 1
        checked += 1

    rng = random.Random(SEED)
    alphabet = "abcxyz_09 \té你"

    def rand_name():
        r = rng.random()
        if r < 0.35:
            return None
        if r < 0.45:
            return ""
        return "".join(rng.choice(alphabet) for _ in range(rng.randint(1, 12)))

    for _ in range(N_FUZZ):
        err = check_case(rand_name(), rand_name(), rng.random() < 0.5)
        if err:
            print(err)
            return 1
        checked += 1

    print("G-CONF OK: shadow impl == real attach-time registration decision "
          "on %d inputs (%d boundary + %d fuzz, seed %d)."
          % (checked, len(boundary), N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
