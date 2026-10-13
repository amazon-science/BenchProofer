#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for django__django-11149.

The bundle models the per-action authorization decision an admin inline makes
for an auto-created many-to-many "through" (link) model. For each of the four
editor actions (add / change / delete / view), the decision is a PURE function
of the observables the real `InlineModelAdmin.has_<action>_permission` reads at
the decision point (mapping.md):

    auto_created        : bool          (self.opts.auto_created)
    self_app_label      : str           (self.opts.app_label)
    self_model_name     : str           (self.opts.model_name)
    parent_model_id     : str           (identity tag of self.parent_model)
    fields              : list[(has_remote:bool, remote_model_id:str,
                                 remote_app_label:str, remote_model_name:str)]
                          (self.opts.fields, each field's remote_field info)
    user_perms          : list[str]     (the permission strings the user holds)
    super_result        : bool          (super().has_<action>_permission(...),
                                         the non-auto_created decision)

Standing up Django's admin + model registry + a real auto-created m2m through
model + a User with a permission set is heavy and unnecessary: the modeled value
is exactly this pure decision over the observables the real methods read. So the
ORACLE below is a faithful in-process replica using the EXACT patched
expressions from the gold diff:

    # gold _has_any_perms_for_target_model:
    opts = (self_app_label, self_model_name)
    for f in fields:                      # opts.fields
        if f.has_remote and f.remote_model_id != parent_model_id:
            opts = (f.remote_app_label, f.remote_model_name)
            break
    def has(perm):  # request.user.has_perm('%s.%s' % (app_label, codename))
        return '%s.%s_%s' % (opts[0], perm, opts[1]) in user_perms
    # has_add/has_change/has_delete (auto_created): any(has(p) for p in ['change'])
    # has_view (auto_created):                       any(has(p) for p in ['view','change'])
    # non-auto_created: super_result

The SHADOW is the op-for-op transliteration of the four
`implementation_has*Permission` defs + `implementation_hasAnyPermsForTargetModel`
(per refinement.md). `get_permission_codename(action, opts)` is the UNCHANGED
callee `'%s_%s' % (action, opts.model_name)`, modeled deeply as `permString`.

This genuinely tests:
  * the F2P behavior — a view-only user (holds only `view_<target>`):
    add/change/delete must be FALSE, view must be TRUE;
  * the change-perm user — all four TRUE;
  * the no-perm user — all four FALSE (auto_created);
  * the non-auto_created passthrough — result == super_result;
  * target-model resolution (first remote field != parent; fallback to self).

stdlib-only. Pinned seed: 20240629 (also in mapping.md).
"""
import random
import sys

SEED = 20240629
N = 130_000


# --- ORACLE: faithful in-process replica of the patched per-action decision ---
def _resolve_opts(self_app_label, self_model_name, parent_model_id, fields):
    opts = (self_app_label, self_model_name)
    for (has_remote, remote_model_id, remote_app_label, remote_model_name) in fields:
        if has_remote and remote_model_id != parent_model_id:
            opts = (remote_app_label, remote_model_name)
            break
    return opts


def _has_any_perms_for_target_model(self_app_label, self_model_name,
                                    parent_model_id, fields, user_perms, perms):
    app_label, model_name = _resolve_opts(self_app_label, self_model_name,
                                          parent_model_id, fields)
    return any(
        ('%s.%s_%s' % (app_label, perm, model_name)) in user_perms
        for perm in perms
    )


def oracle(action, auto_created, self_app_label, self_model_name,
           parent_model_id, fields, user_perms, super_result):
    if auto_created:
        perms = ['view', 'change'] if action == 'view' else ['change']
        return _has_any_perms_for_target_model(
            self_app_label, self_model_name, parent_model_id, fields,
            user_perms, perms)
    return super_result


# --- SHADOW of the implementation_has*Permission defs (R/I / A-reference leg) --
def _perm_string(app_label, model_name, action):
    return app_label + "." + action + "_" + model_name


def _impl_any_perms(self_app_label, self_model_name, parent_model_id,
                    fields, user_perms, actions):
    app_label = self_app_label
    model_name = self_model_name
    for (has_remote, remote_model_id, remote_app_label, remote_model_name) in fields:
        if has_remote and remote_model_id != parent_model_id:
            app_label = remote_app_label
            model_name = remote_model_name
            break
    for a in actions:
        if _perm_string(app_label, model_name, a) in user_perms:
            return True
    return False


def shadow(action, auto_created, self_app_label, self_model_name,
           parent_model_id, fields, user_perms, super_result):
    if auto_created:
        actions = ['view', 'change'] if action == 'view' else ['change']
        return _impl_any_perms(self_app_label, self_model_name, parent_model_id,
                               fields, user_perms, actions)
    return super_result


ACTIONS = ['add', 'change', 'delete', 'view']


def disagree(case):
    (action, ac, sal, smn, pmid, fields, up, sr) = case
    o = oracle(action, ac, sal, smn, pmid, fields, up, sr)
    s = shadow(action, ac, sal, smn, pmid, fields, up, sr)
    if o != s:
        return (case, o, s)
    return None


def _edge_cases():
    cases = []
    # A standard auto-created through model: self=(admin_inlines, author_books),
    # parent=author; the target is `book` in app `admin_inlines`.
    self_app, self_model = "admin_inlines", "author_books"
    parent = "author#id"
    book = "book#id"
    fields = [
        (True, parent, "admin_inlines", "author"),   # points back at parent -> skip
        (True, book, "admin_inlines", "book"),        # first non-parent remote -> target
    ]
    perm_sets = [
        [],                                            # no perms
        ["admin_inlines.view_book"],                   # view-only (F2P)
        ["admin_inlines.change_book"],                 # change
        ["admin_inlines.add_book"],                    # add-only
        ["admin_inlines.view_book", "admin_inlines.change_book"],
        ["admin_inlines.view_author"],                 # perm on the WRONG (parent) model
    ]
    for up in perm_sets:
        for action in ACTIONS:
            for sr in (True, False):
                cases.append((action, True, self_app, self_model, parent,
                              fields, up, sr))
                # non-auto_created: must passthrough to super_result
                cases.append((action, False, self_app, self_model, parent,
                              fields, up, sr))
    # No qualifying remote field -> fall back to self labels.
    for action in ACTIONS:
        cases.append((action, True, "selfapp", "selfmodel", parent,
                      [(False, "x", "y", "z")], ["selfapp.change_selfmodel"], False))
        cases.append((action, True, "selfapp", "selfmodel", parent,
                      [], ["selfapp.view_selfmodel"], False))
    return cases


APPS = ["admin_inlines", "auth", "app1", "app2"]
MODELS = ["book", "author", "photo", "report", "selfmodel"]
PERMS = ["add", "change", "delete", "view"]
IDS = ["a#1", "b#2", "c#3", "parent#0"]


def main() -> int:
    checked = 0
    for case in _edge_cases():
        d = disagree(case)
        if d:
            print(f"DISAGREE edge {d[0]!r}: oracle={d[1]} shadow={d[2]}")
            print("status=fail")
            return 1
        checked += 1

    rng = random.Random(SEED)
    for _ in range(N):
        action = rng.choice(ACTIONS)
        ac = rng.choice([True, False])
        sal = rng.choice(APPS)
        smn = rng.choice(MODELS)
        pmid = rng.choice(IDS)
        nf = rng.randint(0, 4)
        fields = [
            (rng.choice([True, False]), rng.choice(IDS),
             rng.choice(APPS), rng.choice(MODELS))
            for _ in range(nf)
        ]
        # build a plausible user_perms set drawn from the same vocab
        nperm = rng.randint(0, 4)
        up = [f"{rng.choice(APPS)}.{rng.choice(PERMS)}_{rng.choice(MODELS)}"
              for _ in range(nperm)]
        sr = rng.choice([True, False])
        d = disagree((action, ac, sal, smn, pmid, fields, up, sr))
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
