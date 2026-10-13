# benchproofer:begin helpers
from hypothesis import given, strategies as st

AMOUNTS = st.integers(min_value=0, max_value=10000)
# benchproofer:end helpers


# benchproofer:begin impl
def impl(cents):
    quarters = cents // 25
    dimes = cents // 10
    pennies = cents - quarters * 25 - dimes * 10
    return (quarters, dimes, 0, pennies)
# benchproofer:end impl


# benchproofer:begin spec
@given(AMOUNTS)
def property_change_sums_to_the_amount(cents):
    quarters, dimes, nickels, pennies = impl(cents)
    assert quarters * 25 + dimes * 10 + nickels * 5 + pennies == cents
# benchproofer:end spec
