#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-15127 (nagini).

SHADOW: the impl region of model.py, copied VERBATIM below with the contract
calls stripped (the impl region itself contains no Requires/Ensures lines),
plus the @Pure helpers (`setting_message_tags`, `empty_tag`, `slot_present`,
`read_slot`, `merge_slot`) and the `Tags` record copied over as plain Python
(the `Tags.__init__` Ensures lines dropped). No @ContractOnly callees and no
PSeq in this bundle, so no shim is needed.

ORACLE: the REAL patched repo function the model models per mapping.md —
`django.contrib.messages.apps.update_level_tags(setting, **kwargs)`. The gate
applies patch.diff to /testbed before this script runs; PYTHONPATH=/testbed
makes the patched module importable. The oracle drives the receiver exactly
at the modeling boundary stated in mapping.md/refinement.md:

  * the `defaults` input is the module-level default family the derivation
    reads (`constants.DEFAULT_TAGS`) — injected by rebinding that attribute
    per case (the derivation reads it via attribute lookup at call time);
  * the `override` input is the configurable override mapping the derivation
    reads from settings — injected by setting (or deleting, for the
    absent-override case) `settings.MESSAGE_TAGS` per case;
  * the `current` input is the mapping in force before the call — injected by
    rebinding `base.LEVEL_TAGS` per case;
  * the receiver's "result" is the value of `base.LEVEL_TAGS` after the call
    (the model's value-return is the abstraction of that rebind, per
    refinement.md A4/A5).

TYPE BRIDGE (mapping.md §2): each real Dict[int, str] level->tag mapping is
observed pointwise per level; a level's slot is None iff the level is absent,
else an int token for its tag. Per test case a fresh bijection encodes the
case's tag strings as tokens with '' <-> 0 (the model's empty_tag()) and every
other distinct string a distinct positive int. The setting-name string is
observed only by equality with the message-tags name, so it bridges to the
model's int token: the message-tags name -> setting_message_tags() (== 1),
any other name -> a different int. The 3-slot `Tags` record carries three
representative levels at a time; a case's full level set is covered by
chunking it into triples (the derivation is pointwise per level, and the
shadow is run once per triple), so every level of every case is compared.
The per-level read `.get(level, '')` is compared against `read_slot` on the
result slots as well.

Input domain: the model's Requires are only read-permission accs, so every
(setting, override, defaults, current) is Requires-satisfying. Boundary cases
cover: empty/absent override, override re-tagging a built-in level, override
re-tagging to the empty string, a custom level only the override carries,
override == defaults, non-message-tags settings (mapping must stay the
in-force one), and current dicts unrelated to the merge. Fuzz draws small
random dicts over a shared level/tag pool plus random setting names.

>= 1e5 Requires-satisfying inputs: every shadow invocation (one per level
triple) is a distinct Requires-satisfying input vector; the run asserts the
total is >= 100000. Pinned fuzz seed: 15127.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only.
"""
import json
import random
import sys

SEED = 15127
N_FUZZ_CASES = 45_000
MIN_INPUTS = 100_000


# --- pure helpers from model.py, decorators + contracts stripped -------------

class Tags:
    def __init__(self, a, b, c):
        self.a = a  # built-in level the override re-tags
        self.b = b  # built-in level the override omits
        self.c = c  # custom level the defaults never had


def setting_message_tags():
    return 1


def empty_tag():
    return 0


def slot_present(slot):
    return slot is not None


def read_slot(slot):
    if slot is None:
        return empty_tag()
    return slot


def merge_slot(d, o):
    if o is not None:
        return o
    return d


# --- the impl region of model.py, verbatim -----------------------------------

def derive_tags_for_setting(setting, override, defaults, current):
    if setting == setting_message_tags():
        return Tags(merge_slot(defaults.a, override.a),
                    merge_slot(defaults.b, override.b),
                    merge_slot(defaults.c, override.c))
    # Under any other identifier the result equals the in-force mapping: the
    # returned record holds the same level-for-level slot values as ``current``
    # (observationally the same mapping).
    return Tags(current.a, current.b, current.c)


# --- oracle: drive the REAL patched receiver ----------------------------------

MSG_SETTING = "MESSAGE_TAGS"


def real_result_mapping(setting_name, override, defaults, current):
    """Run the REAL patched receiver with the three mapping sources injected
    at the modeling boundary and return the mapping in force afterwards.
    `override is None` = the setting is absent entirely."""
    from django.conf import settings
    from django.contrib.messages import apps as msg_apps
    from django.contrib.messages import constants
    from django.contrib.messages.storage import base

    constants.DEFAULT_TAGS = dict(defaults)
    if override is None:
        try:
            delattr(settings, MSG_SETTING)
        except AttributeError:
            pass
    else:
        setattr(settings, MSG_SETTING, dict(override))
    base.LEVEL_TAGS = dict(current)

    msg_apps.update_level_tags(setting=setting_name)

    return base.LEVEL_TAGS


# --- bridge: Dict[int, str] <-> per-level Optional[int] slots ------------------

class TokenTable:
    """Per-case bijection between the case's tag strings and int tokens:
    '' <-> 0 (the model's empty_tag), other distinct strings <-> distinct
    positive ints. A result string outside the table (impossible for a
    faithful merge, which never invents values) encodes to a unique sentinel
    that can never equal a shadow token."""

    def __init__(self):
        self._enc = {"": 0}
        self._next = 1
        self._sentinel = -1

    def learn(self, mapping):
        for v in mapping.values():
            if v not in self._enc:
                self._enc[v] = self._next
                self._next += 1

    def slot(self, mapping, level):
        if level in mapping:
            return self._enc[mapping[level]]
        return None

    def result_slot(self, mapping, level):
        if level not in mapping:
            return None
        v = mapping[level]
        if v in self._enc:
            return self._enc[v]
        s = self._sentinel
        self._sentinel -= 1
        return s

    def enc_read(self, tag_string):
        # the '' default of the real .get(level, '') is the empty tag token
        if tag_string in self._enc:
            return self._enc[tag_string]
        s = self._sentinel
        self._sentinel -= 1
        return s


def setting_token(setting_name):
    # the setting name is observed only by equality with the message-tags name
    return setting_message_tags() if setting_name == MSG_SETTING else 2


FRESH_LEVEL_BASE = 10_000_000  # padding levels no case's dicts ever carry


def check_case(setting_name, override, defaults, current):
    """Compare shadow vs real pointwise at every level any source mentions
    (plus padding levels, absent everywhere). Returns (n_inputs, error)."""
    ov = {} if override is None else override
    table = TokenTable()
    table.learn(defaults)
    table.learn(ov)
    table.learn(current)

    real_out = real_result_mapping(setting_name, override, defaults, current)

    levels = sorted(set(defaults) | set(ov) | set(current))
    if not levels:
        levels = [FRESH_LEVEL_BASE]
    while len(levels) % 3 != 0:
        levels.append(FRESH_LEVEL_BASE + len(levels))

    s_tok = setting_token(setting_name)
    n = 0
    for i in range(0, len(levels), 3):
        tri = levels[i:i + 3]
        t_ov = Tags(*(table.slot(ov, L) for L in tri))
        t_df = Tags(*(table.slot(defaults, L) for L in tri))
        t_cu = Tags(*(table.slot(current, L) for L in tri))
        shadow_out = derive_tags_for_setting(s_tok, t_ov, t_df, t_cu)
        n += 1
        for L, s_slot in zip(tri, (shadow_out.a, shadow_out.b, shadow_out.c)):
            r_slot = table.result_slot(real_out, L)
            if s_slot != r_slot:
                return n, (
                    "DISAGREEMENT (mapping slot)\n"
                    "  setting=%r override=%r defaults=%r current=%r\n"
                    "  level=%r shadow_slot=%r real=%r (real mapping=%r)"
                    % (setting_name, override, defaults, current,
                       L, s_slot, real_out.get(L), real_out))
            # the per-level read: real .get(level, '') vs read_slot
            r_read = table.enc_read(real_out.get(L, ""))
            if read_slot(s_slot) != r_read:
                return n, (
                    "DISAGREEMENT (level read)\n"
                    "  setting=%r override=%r defaults=%r current=%r\n"
                    "  level=%r shadow_read=%r real_read=%r"
                    % (setting_name, override, defaults, current,
                       L, read_slot(s_slot), real_out.get(L, "")))
    return n, None


# --- input generation ----------------------------------------------------------

BUILTIN_DEFAULTS = {10: "debug", 20: "info", 25: "success",
                    30: "warning", 40: "error"}
OTHER_SETTINGS = ["DEBUG", "USE_TZ", "MESSAGE_LEVEL", "LANGUAGE_CODE", "X",
                  "message_tags", "MESSAGE_TAGS2"]


def boundary_cases():
    d = BUILTIN_DEFAULTS
    cur_stale = dict(d)  # in-force == defaults (never re-derived yet)
    cases = [
        (MSG_SETTING, None, d, cur_stale),            # setting absent entirely
        (MSG_SETTING, {}, d, cur_stale),              # empty override
        (MSG_SETTING, {20: "info-new"}, d, cur_stale),        # re-tag a built-in
        (MSG_SETTING, {30: ""}, d, cur_stale),                # re-tag to ''
        (MSG_SETTING, {12: "custom"}, d, cur_stale),          # custom-only level
        (MSG_SETTING, {10: "", 20: "info", 30: "", 40: "bad",
                       25: "", 12: "custom"}, d, cur_stale),  # full re-tag + custom
        (MSG_SETTING, {20: "x", 30: "y", 99: "z"}, d, cur_stale),
        (MSG_SETTING, dict(d), d, cur_stale),         # override == defaults
        (MSG_SETTING, {12: "custom"}, {}, {}),        # empty defaults/current
        (MSG_SETTING, {}, {}, {5: "left"}),           # everything from current only
    ]
    # non-message-tags settings: the in-force mapping must survive untouched
    for name in OTHER_SETTINGS:
        cases.append((name, {12: "custom"}, d, cur_stale))
        cases.append((name, {12: "custom"}, d, {12: "already", 20: "kept"}))
        cases.append((name, None, d, {}))
    return cases


def rand_case(rng):
    tag_pool = ["", "a", "info", "bad", "custom", "warning", "x", "y", "zz"]
    level_pool = [0, 5, 10, 12, 20, 25, 30, 40, 99] + list(range(50, 60))

    def rand_dict(max_len):
        return {rng.choice(level_pool): rng.choice(tag_pool)
                for _ in range(rng.randint(0, max_len))}

    r = rng.random()
    if r < 0.60:
        setting_name = MSG_SETTING
    else:
        setting_name = rng.choice(OTHER_SETTINGS)
    override = None if rng.random() < 0.05 else rand_dict(6)
    defaults = BUILTIN_DEFAULTS if rng.random() < 0.5 else rand_dict(6)
    current = rand_dict(6)
    return setting_name, override, defaults, current


def main():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(DEBUG=False)

    checked = 0
    for case in boundary_cases():
        n, err = check_case(*case)
        checked += n
        if err:
            print(err)
            return 1

    rng = random.Random(SEED)
    for _ in range(N_FUZZ_CASES):
        n, err = check_case(*rand_case(rng))
        checked += n
        if err:
            print(err)
            return 1

    if checked < MIN_INPUTS:
        print("input budget not met: only %d shadow inputs (< %d)"
              % (checked, MIN_INPUTS))
        return 1

    print("G-CONF OK: shadow impl == real patched receiver on %d input "
          "vectors (%d boundary + %d fuzz cases, seed %d)."
          % (checked, len(boundary_cases()), N_FUZZ_CASES, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
