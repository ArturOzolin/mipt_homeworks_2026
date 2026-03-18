from Part_3_Types_Conditions_Loops_Functions import hw3
from Part_3_Types_Conditions_Loops_Functions.hw3 import (
    INCORRECT_DATE_MSG,
    NONPOSITIVE_VALUE_MSG,
    NOT_EXISTS_CATEGORY,
    OP_SUCCESS_MSG,
    cost_categories_handler,
    cost_handler,
)
from Part_3_Types_Conditions_Loops_Functions.tests.conftest import Cost, CostBuilder, parse_date


def test_cost_success(valid_cost: Cost) -> None:
    result = cost_handler(valid_cost.category, valid_cost.amount, valid_cost.date)
    cost_data = hw3.financial_transactions_storage[-1]
    assert result == OP_SUCCESS_MSG
    assert cost_data
    assert cost_data["amount"] == valid_cost.amount
    assert cost_data["date"] == parse_date(valid_cost.date)
    common_category, direct_category = valid_cost.category.split("::")
    assert common_category in hw3.EXPENSE_CATEGORIES
    assert direct_category in hw3.EXPENSE_CATEGORIES[common_category]


def test_cost_amount_less_than_zero(invalid_cost_factory: CostBuilder[Cost]) -> None:
    invalid_income = invalid_cost_factory(amount=-1)
    result = cost_handler(invalid_income.category, invalid_income.amount, invalid_income.date)
    income_data = hw3.financial_transactions_storage[-1]
    assert result == NONPOSITIVE_VALUE_MSG
    assert not income_data


def test_cost_invalid_date(invalid_cost_factory: CostBuilder[Cost]) -> None:
    invalid_income = invalid_cost_factory(date="invalid")
    result = cost_handler(invalid_income.category, invalid_income.amount, invalid_income.date)
    income_data = hw3.financial_transactions_storage[-1]
    assert result == INCORRECT_DATE_MSG
    assert not income_data


def test_cost_invalid_category(invalid_cost_factory: CostBuilder[Cost]) -> None:
    invalid_income = invalid_cost_factory(category="NotExistCategory")
    result = cost_handler(invalid_income.category, invalid_income.amount, invalid_income.date)
    income_data = hw3.financial_transactions_storage[-1]
    assert result == NOT_EXISTS_CATEGORY
    assert not income_data


def test_cost_categories_info() -> None:
    result = cost_categories_handler()
    assert result == "\n".join(f"{k}::{v}" for k, kv in hw3.EXPENSE_CATEGORIES.items() for v in kv)
