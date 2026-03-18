from Part_3_Types_Conditions_Loops_Functions import hw3
from Part_3_Types_Conditions_Loops_Functions.hw3 import (
    INCORRECT_DATE_MSG,
    NONPOSITIVE_VALUE_MSG,
    OP_SUCCESS_MSG,
    income_handler,
)
from Part_3_Types_Conditions_Loops_Functions.tests.conftest import Income, IncomeBuilder, parse_date


def test_income_success(valid_income: Income) -> None:
    result = income_handler(valid_income.amount, valid_income.date)
    income_data = hw3.financial_transactions_storage[-1]
    assert result == OP_SUCCESS_MSG
    assert income_data
    assert income_data["amount"] == valid_income.amount
    assert income_data["date"] == parse_date(valid_income.date)


def test_income_amount_less_than_zero(invalid_income_factory: IncomeBuilder[Income]) -> None:
    invalid_income = invalid_income_factory(amount=-1)
    result = income_handler(invalid_income.amount, invalid_income.date)
    income_data = hw3.financial_transactions_storage[-1]
    assert result == NONPOSITIVE_VALUE_MSG
    assert not income_data


def test_income_invalid_date(invalid_income_factory: IncomeBuilder[Income]) -> None:
    invalid_income = invalid_income_factory(date="invalid")
    result = income_handler(invalid_income.amount, invalid_income.date)
    income_data = hw3.financial_transactions_storage[-1]
    assert result == INCORRECT_DATE_MSG
    assert not income_data
