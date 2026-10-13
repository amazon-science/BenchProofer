#!/usr/bin/env python3
"""G-CONF for django__django-16333 — skip stub (conf_skip=true).

`implementation_persistForm` is composed ENTIRELY of A-reference ops
(refinement.md): each step forwards to a deeply-modeled, UNCHANGED persistence
sub-operation of a model-backed form's `save`:

  * `buildInstance` / `hasRelatedWriter`  <-  `super().save(commit=False)`
    (builds the instance from cleaned data and installs the deferred m2m writer);
  * `passwordSet := true`                 <-  `user.set_password(...)`;
  * `instanceSaved := commit`             <-  `if commit: user.save()`;
  * `relatedSaved := f.m2m` (the change)  <-  `self.save_m2m()` (writes the form's
    collected multi-valued related selections to the relation).

These mirror live-ORM persistence: building a model instance, writing its row, and
writing m2m relations through a relation/through table. They cannot be
transliterated to a stdlib-only Python shadow without re-implementing the Django
ORM, model forms, an m2m relation, and a database. There is no standalone R/I data
transformation whose Python shadow could be built independently, so there is
nothing for a cross-language differential test to exercise.

Per the worker spec, an all-A-tagged impl sets meta.json conf_skip=true and ships
this skip stub.
"""
import json
import sys

print(json.dumps({
    "status": "skip",
    "instance": "django__django-16333",
    "reason": "impl is all A-reference ORM-persistence ops (build instance / save "
              "row / save_m2m relation writes); no standalone R/I op transliterable "
              "to a stdlib-only shadow for a differential test",
}))
sys.exit(0)
