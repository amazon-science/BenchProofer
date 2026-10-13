# benchproofer:begin helpers
from hypothesis import given, strategies as st

AMOUNTS = st.integers(min_value=0, max_value=10000)
# benchproofer:end helpers


# benchproofer:begin impl
def impl(cents):
    quarters = cents // 25
    remainder = cents - quarters * 25
    dimes = remainder // 10
    remainder = remainder - dimes * 10
    nickels = remainder // 5
    pennies = remainder - nickels * 5
    return (quarters, dimes, nickels, pennies)
# benchproofer:end impl


# benchproofer:begin spec
@given(AMOUNTS)
def property_change_sums_to_the_amount(cents):
    quarters, dimes, nickels, pennies = impl(cents)
    assert quarters * 25 + dimes * 10 + nickels * 5 + pennies == cents


@given(AMOUNTS)
def property_change_uses_no_negative_coin(cents):
    assert all(count >= 0 for count in impl(cents))


@given(AMOUNTS)
def property_change_is_the_fewest_coins(cents):
    _, dimes, nickels, pennies = impl(cents)
    assert dimes * 10 + nickels * 5 + pennies < 25
    assert nickels * 5 + pennies < 10
    assert pennies < 5
# benchproofer:end spec
