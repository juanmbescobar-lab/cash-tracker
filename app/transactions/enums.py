"""Enums for the transactions domain."""

import enum


class TransactionType(enum.StrEnum):
    """Type of cash transaction.

    Inherits from ``StrEnum`` so values serialize naturally in JSON and
    can be compared with plain strings in queries and tests.
    """

    INCOME = "income"
    EXPENSE = "expense"
