Correct means what the benchmark means by correct: its own tests report the task resolved,
the PASS_TO_PASS tests included. The tests that say what the task is are fewer: the
FAIL_TO_PASS tests and the PASS_TO_PASS tests the test patch adds or edits. Of a parametrized
test the test patch only adds parametrized cases to, the cases it adds are the ones it edits.
A test the test patch adds or edits that the benchmark lists as neither judges no fix. Any
other PASS_TO_PASS test holds a specification to what it checks through the implementations
the specification accepts: one that breaks that test is wrong.
