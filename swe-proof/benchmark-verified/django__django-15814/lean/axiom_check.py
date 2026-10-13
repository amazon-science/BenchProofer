#!/usr/bin/env python3
"""G-AX for django__django-15814 — skip stub.

The bundle consumes NO unchanged-callee axiom and declares NO A-reference: the
modeled decision (`relationModelKeys`) is all R/I (validated by G-CONF). The op the
patch introduces — normalizing a resolved relation-target model to its concrete
base model before using it as the key of the fields-to-load map — is modeled DEEPLY
over each step's base-model identity (`baseOf` ↔ `cur_model._meta.concrete_model`).
There is therefore no callee contract to validate against the real repo.
"""
import json
import sys

print(json.dumps({
    "status": "skip",
    "instance": "django__django-15814",
    "reason": "no consumed callee axiom and no A-reference; impl is all R/I "
              "(validated by G-CONF)",
}))
sys.exit(0)
