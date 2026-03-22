#!/usr/bin/env python

from typing import Any

UNKNOWN_COMMAND_MSG = "Unknown command!"
NONPOSITIVE_VALUE_MSG = "Value must be grater than zero!"
INCORRECT_DATE_MSG = "Invalid date!"
NOT_EXISTS_CATEGORY = "Category not exists!"
OP_SUCCESS_MSG = "Added"
TYPE = "type"
AMOUNT = "amount"
DATE = "date"
CATEGORY = "category"
INCOME = "income"

DATE_PARTS = 3
DAY_LEN = 2
MONTH_LEN = 2
YEAR_LEN = 4
MONTHS_IN_YEAR = 12

INCOME_ARGUMENTS = 3
COST_ARGUMENTS = 4
STATS_ARGUMENTS = 2

EXPENSE_CATEGORIES = {
    "Food": ("Supermarket", "Restaurants", "FastFood", "Coffee", "Delivery"),
    "Transport": ("Taxi", "Public transport", "Gas", "Car service"),
    "Housing": ("Rent", "Utilities", "Repairs", "Furniture"),
    "Health": ("Pharmacy", "Doctors", "Dentist", "Lab tests"),
    "Entertainment": ("Movies", "Concerts", "Games", "Subscriptions"),
    "Clothing": ("Outerwear", "Casual", "Shoes", "Accessories"),
    "Education": ("Courses", "Books", "Tutors"),
    "Communications": ("Mobile", "Internet", "Subscriptions"),
    "Other": ("SomeCategory", "SomeOtherCategory"),
}

financial_transactions_storage: list[dict[str, Any]] = []


def is_leap_year(year: int) -> bool:
    if year % 400 == 0:
        return True
    if year % 100 == 0:
        return False
    return year % 4 == 0


def _valid_parts(parts: list[str]) -> bool:
    if len(parts) != DATE_PARTS:
        return False
    if not all(p.isdigit() for p in parts):
        return False
    lengths = [len(p) for p in parts]
    return lengths == [DAY_LEN, MONTH_LEN, YEAR_LEN]


def _valid_day(day: int, month: int, year: int) -> bool:
    days = [
        31,
        29 if is_leap_year(year) else 28,
        31,
        30,
        31,
        30,
        31,
        31,
        30,
        31,
        30,
        31,
    ]
    return 1 <= day <= days[month - 1]


def extract_date(maybe_dt: str) -> tuple[int, int, int] | None:
    parts = maybe_dt.split("-")

    if not _valid_parts(parts):
        return None

    day, month, year = map(int, parts)

    if not (1 <= month <= MONTHS_IN_YEAR):
        return None

    if not _valid_day(day, month, year):
        return None

    return day, month, year


def parse_amount(value: str) -> float | None:
    tmp = value.replace(",", ".", 1)

    if tmp.count(".") > 1:
        print(UNKNOWN_COMMAND_MSG)
        return None

    if tmp.startswith("-"):
        print(NONPOSITIVE_VALUE_MSG)
        return None

    check = tmp.replace(".", "", 1)
    if not check.isdigit():
        print(UNKNOWN_COMMAND_MSG)
        return None

    amount = float(tmp)
    if amount <= 0:
        print(NONPOSITIVE_VALUE_MSG)
        return None

    return amount


def validate_category(category: str) -> bool:
    if "::" not in category:
        return False

    main, sub = category.split("::", 1)
    return main in EXPENSE_CATEGORIES and sub in EXPENSE_CATEGORIES[main]


def income_handler(amount: float, income_date: str) -> str:
    if amount <= 0:
        return NONPOSITIVE_VALUE_MSG

    date_tuple = extract_date(income_date)
    if date_tuple is None:
        return INCORRECT_DATE_MSG

    financial_transactions_storage.append(
        {TYPE: INCOME, AMOUNT: amount, DATE: date_tuple}
    )
    return OP_SUCCESS_MSG


def cost_handler(category_name: str, amount: float, income_date: str) -> str:
    if amount <= 0:
        return NONPOSITIVE_VALUE_MSG

    if not validate_category(category_name):
        return NOT_EXISTS_CATEGORY

    date_tuple = extract_date(income_date)
    if date_tuple is None:
        return INCORRECT_DATE_MSG

    financial_transactions_storage.append(
        {
            TYPE: "cost",
            CATEGORY: category_name,
            AMOUNT: amount,
            DATE: date_tuple,
        }
    )
    return OP_SUCCESS_MSG


def cost_categories_handler() -> str:
    result: list[str] = []
    for main, subs in EXPENSE_CATEGORIES.items():
        result.extend(f"{main}::{sub}" for sub in subs)
    return "\n".join(result)


def _update_total(item: dict[str, Any], current: float, target: tuple[int, int, int]) -> float:
    d, m, y = item[DATE]
    y_t, m_t, d_t = target[2], target[1], target[0]

    if (y, m, d) <= (y_t, m_t, d_t):
        if item[TYPE] == INCOME:
            return current + item[AMOUNT]
        return current - item[AMOUNT]
    return current


def _update_month(
        item: dict[str, Any],
        income_m: float,
        cost_m: float,
        categories: dict[str, float],
        target: tuple[int, int, int],
) -> tuple[float, float]:
    d, m, y = item[DATE]
    d_t, m_t, y_t = target

    if y == y_t and m == m_t and d <= d_t:
        if item[TYPE] == INCOME:
            return income_m + item[AMOUNT], cost_m

        cost_m += item[AMOUNT]
        category = item[CATEGORY].split("::")[1]
        categories[category] = categories.get(category, 0) + item[AMOUNT]

    return income_m, cost_m


def stats_handler(report_date: str) -> str:
    date_tuple = extract_date(report_date)
    if date_tuple is None:
        return INCORRECT_DATE_MSG

    total = 0
    income_m = 0
    cost_m = 0
    categories: dict[str, float] = {}

    for item in financial_transactions_storage:
        total = _update_total(item, total, date_tuple)
        income_m, cost_m = _update_month(item, income_m, cost_m, categories, date_tuple)

    delta = income_m - cost_m
    status = "profit amounted to" if delta >= 0 else "loss amounted to"

    lines = [
        f"Your statistics as of {report_date}:",
        f"Total capital: {total:.2f} rubles",
        f"This month, the {status} {abs(delta):.2f} rubles.",
        f"Income: {income_m:.2f} rubles",
        f"Expenses: {cost_m:.2f} rubles",
        "",
        "Details (category: amount):",
    ]

    if categories:
        for i, category in enumerate(sorted(categories), 1):
            val = categories[category]
            val_str = int(val) if val.is_integer() else val
            lines.append(f"{i}. {category}: {val_str}")

    return "\n".join(lines)


def handle_income(parts: list[str]) -> None:
    if len(parts) != INCOME_ARGUMENTS:
        print(UNKNOWN_COMMAND_MSG)
        return

    amount = parse_amount(parts[1])
    if amount is None:
        return

    if extract_date(parts[2]) is None:
        print(INCORRECT_DATE_MSG)
        return

    print(income_handler(amount, parts[2]))


def handle_cost(parts: list[str]) -> None:
    if len(parts) == STATS_ARGUMENTS and parts[1] == "categories":
        print(cost_categories_handler())
        return

    if len(parts) != COST_ARGUMENTS:
        print(UNKNOWN_COMMAND_MSG)
        return

    if not validate_category(parts[1]):
        print(NOT_EXISTS_CATEGORY)
        print(cost_categories_handler())
        return

    amount = parse_amount(parts[2])
    if amount is None:
        return

    if extract_date(parts[3]) is None:
        print(INCORRECT_DATE_MSG)
        return

    print(cost_handler(parts[1], amount, parts[3]))


def handle_stats(parts: list[str]) -> None:
    if len(parts) != STATS_ARGUMENTS:
        print(UNKNOWN_COMMAND_MSG)
        return

    print(stats_handler(parts[1]))


def _dispatch(command: str, parts: list[str]) -> None:
    if command == INCOME:
        handle_income(parts)
    elif command == "cost":
        handle_cost(parts)
    elif command == "stats":
        handle_stats(parts)
    else:
        print(UNKNOWN_COMMAND_MSG)


def main() -> None:
    with open(0) as f:
        for line in f:
            parts = line.strip().split()
            if not parts:
                continue

            _dispatch(parts[0], parts)


if __name__ == "__main__":
    main()
