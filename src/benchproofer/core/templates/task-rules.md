The specification states each behavior the FAIL_TO_PASS tests and the PASS_TO_PASS tests the
test patch adds or edits check, and each change the statement asks of the fix, even when none
of those tests checks it. A statement can ask for more than its fix does -- a restriction it
names that the fixed code never checks -- and a specification that leaves that out still
describes the task the benchmark poses. A behavior none of those tests checks and the statement
does not ask for -- a message's wording, a branch no test reaches -- is incidental: it may be
left out of the obligations, and a specification that pins it, so that a correct patch without
it is refused, demands more than the task does. A branch of a changed function that the golden
patch leaves as it was may be left out of the model as well, by an `Outside the bridge` entry
of the third kind, and only so. Where an incidental choice of the golden patch decides a
result, the specification states the set of results the statement allows, rather than nothing
or the golden patch's one result: it admits the golden patch's behavior there without demanding
it.
