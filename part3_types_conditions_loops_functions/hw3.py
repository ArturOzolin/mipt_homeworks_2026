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


def _is_same_month_and_past(
        date1: tuple[int, int, int],
        date2: tuple[int, int, int],
) -> bool:
    if date1[2] != date2[2]:
        return False
    if date1[1] != date2[1]:
        return False
    return date1[0] <= date2[0]


def _update_month_cost(
        item: dict[str, Any],
        stats: dict[str, Any],
) -> None:
    stats["cost_m"] += item[AMOUNT]
    category = item[CATEGORY].split("::")[1]
    categories = stats["categories"]
    categories[category] = categories.get(category, 0.0) + item[AMOUNT]


def _update_stats_for_item(
        item: dict[str, Any],
        stats: dict[str, Any],
        target: tuple[int, int, int],
) -> None:
    item_date = item[DATE]
    if item_date[::-1] <= target[::-1]:
        if item[TYPE] == INCOME:
            stats["total"] += item[AMOUNT]
        else:
            stats["total"] -= item[AMOUNT]

    if _is_same_month_and_past(item_date, target):
        if item[TYPE] == INCOME:
            stats["income_m"] += item[AMOUNT]
        else:
            _update_month_cost(item, stats)


def _calculate_stats(target: tuple[int, int, int]) -> dict[str, Any]:
    stats: dict[str, Any] = {
        "total": 0,
        "income_m": 0,
        "cost_m": 0,
        "categories": {},
    }
    for item in financial_transactions_storage:
        _update_stats_for_item(item, stats, target)
    return stats


def _format_categories(
        categories: dict[str, float],
) -> list[str]:
    lines = []
    for index, (category, amount) in enumerate(sorted(categories.items()), 1):
        lines.append(f"{index}. {category}: {int(amount) if amount.is_integer() else amount}")
    return lines


def _format_stats_output(
        report_date: str,
        stats: dict[str, Any],
) -> str:
    delta = stats["income_m"] - stats["cost_m"]
    status = f"profit amounted to {delta:.2f}" if delta >= 0 else f"loss amounted to {-delta:.2f}"

    lines = [
        f"Your statistics as of {report_date}:",
        f"Total capital: {stats['total']:.2f} rubles",
        f"This month, the {status} rubles.",
        f"Income: {stats['income_m']:.2f} rubles",
        f"Expenses: {stats['cost_m']:.2f} rubles",
        "",
        "Details (category: amount):",
    ]

    if stats["categories"]:
        lines.extend(_format_categories(stats["categories"]))

    return "\n".join(lines)


def stats_handler(report_date: str) -> str:
    date_tuple = extract_date(report_date)
    if date_tuple is None:
        return INCORRECT_DATE_MSG

    stats = _calculate_stats(date_tuple)
    return _format_stats_output(report_date, stats)


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
