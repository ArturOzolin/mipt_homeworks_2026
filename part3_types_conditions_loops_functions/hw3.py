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
COST = "cost"
STATS = "stats"
CATEGORY_SEP = "::"

STATS_TOTAL = "total"
STATS_INCOME = "income_m"
STATS_COST = "cost_m"
STATS_CATEGORIES = "categories"

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
    if not all(part.isdigit() for part in parts):
        return False
    lengths = [len(part) for part in parts]
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
    normalized_val = value.replace(",", ".", 1)

    if normalized_val.count(".") > 1:
        return None

    check = normalized_val.removeprefix("-").replace(".", "", 1)
    if not check or not check.isdigit():
        return None

    return float(normalized_val)


def validate_category(category: str) -> bool:
    if CATEGORY_SEP not in category:
        return False

    main_cat, sub_cat = category.split(CATEGORY_SEP, 1)
    return main_cat in EXPENSE_CATEGORIES and sub_cat in EXPENSE_CATEGORIES[main_cat]


def income_handler(amount: float, transaction_date: str) -> str:
    if amount <= 0:
        financial_transactions_storage.append({})
        return NONPOSITIVE_VALUE_MSG

    date_tuple = extract_date(transaction_date)
    if date_tuple is None:
        financial_transactions_storage.append({})
        return INCORRECT_DATE_MSG

    financial_transactions_storage.append(
        {TYPE: INCOME, AMOUNT: amount, DATE: date_tuple}
    )
    return OP_SUCCESS_MSG


def cost_handler(category_name: str, amount: float, transaction_date: str) -> str:
    if amount <= 0:
        financial_transactions_storage.append({})
        return NONPOSITIVE_VALUE_MSG

    if not validate_category(category_name):
        financial_transactions_storage.append({})
        return NOT_EXISTS_CATEGORY

    date_tuple = extract_date(transaction_date)
    if date_tuple is None:
        financial_transactions_storage.append({})
        return INCORRECT_DATE_MSG

    financial_transactions_storage.append(
        {
            TYPE: COST,
            CATEGORY: category_name,
            AMOUNT: amount,
            DATE: date_tuple,
        }
    )
    return OP_SUCCESS_MSG


def cost_categories_handler() -> str:
    result: list[str] = []
    for main_cat, subs in EXPENSE_CATEGORIES.items():
        result.extend(f"{main_cat}{CATEGORY_SEP}{sub}" for sub in subs)
    return "\n".join(result)


def _is_same_month_and_past(
    item_date: tuple[int, int, int],
    target_date: tuple[int, int, int],
) -> bool:
    if item_date[2] != target_date[2]:
        return False
    if item_date[1] != target_date[1]:
        return False
    return item_date[0] <= target_date[0]


def _is_past_or_present(
    item_date: tuple[int, int, int],
    target_date: tuple[int, int, int],
) -> bool:
    return tuple(reversed(item_date)) <= tuple(reversed(target_date))


def _update_month_cost(
    item: dict[str, Any],
    stats: dict[str, Any],
) -> None:
    stats[STATS_COST] += item[AMOUNT]
    category = item[CATEGORY].split(CATEGORY_SEP)[1]
    categories = stats[STATS_CATEGORIES]
    categories[category] = categories.get(category, 0) + item[AMOUNT]


def _update_stats_for_item(
    item: dict[str, Any],
    stats: dict[str, Any],
    target: tuple[int, int, int],
) -> None:
    item_date = item[DATE]
    if _is_past_or_present(item_date, target):
        if item[TYPE] == INCOME:
            stats[STATS_TOTAL] += item[AMOUNT]
        else:
            stats[STATS_TOTAL] -= item[AMOUNT]

    if _is_same_month_and_past(item_date, target):
        if item[TYPE] == INCOME:
            stats[STATS_INCOME] += item[AMOUNT]
        else:
            _update_month_cost(item, stats)


def _calculate_stats(target: tuple[int, int, int]) -> dict[str, Any]:
    stats: dict[str, Any] = {
        STATS_TOTAL: 0,
        STATS_INCOME: 0,
        STATS_COST: 0,
        STATS_CATEGORIES: {},
    }
    for item in financial_transactions_storage:
        if not item:
            continue
        _update_stats_for_item(item, stats, target)
    return stats


def _format_category_line(index: int, category: str, amount: float) -> str:
    if amount.is_integer():
        return f"{index}. {category}: {int(amount)}"
    return f"{index}. {category}: {amount}"


def _format_categories(
    categories_dict: dict[str, float],
) -> list[str]:
    return [
        _format_category_line(index, category, amount)
        for index, (category, amount) in enumerate(sorted(categories_dict.items()), 1)
    ]


def _get_status_message(delta: float) -> str:
    abs_delta = abs(delta)
    if delta >= 0:
        return f"profit amounted to {abs_delta:.2f}"
    return f"loss amounted to {abs_delta:.2f}"


def _format_stats_output(
    report_date: str,
    stats: dict[str, Any],
) -> str:
    delta = stats[STATS_INCOME] - stats[STATS_COST]
    status = _get_status_message(delta)

    lines = [
        f"Your statistics as of {report_date}:",
        f"Total capital: {stats[STATS_TOTAL]:.2f} rubles",
        f"This month, the {status} rubles.",
        f"Income: {stats[STATS_INCOME]:.2f} rubles",
        f"Expenses: {stats[STATS_COST]:.2f} rubles",
        "",
        "Details (category: amount):",
    ]

    if stats[STATS_CATEGORIES]:
        lines.extend(_format_categories(stats[STATS_CATEGORIES]))

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
        print(UNKNOWN_COMMAND_MSG)
        return

    print(income_handler(amount, parts[2]))


def handle_cost(parts: list[str]) -> None:
    if len(parts) == STATS_ARGUMENTS and parts[1] == STATS_CATEGORIES:
        print(cost_categories_handler())
        return

    if len(parts) != COST_ARGUMENTS:
        print(UNKNOWN_COMMAND_MSG)
        return

    amount = parse_amount(parts[2])
    if amount is None:
        print(UNKNOWN_COMMAND_MSG)
        return

    result = cost_handler(parts[1], amount, parts[3])
    print(result)

    if result == NOT_EXISTS_CATEGORY:
        print(cost_categories_handler())


def handle_stats(parts: list[str]) -> None:
    if len(parts) != STATS_ARGUMENTS:
        print(UNKNOWN_COMMAND_MSG)
        return

    print(stats_handler(parts[1]))


def _dispatch(command: str, parts: list[str]) -> None:
    if command == INCOME:
        handle_income(parts)
    elif command == COST:
        handle_cost(parts)
    elif command == STATS:
        handle_stats(parts)
    else:
        print(UNKNOWN_COMMAND_MSG)


def main() -> None:
    with open(0) as input_file:
        for line in input_file:
            parts = line.strip().split()
            if not parts:
                continue

            _dispatch(parts[0], parts)


if __name__ == "__main__":
    main()
