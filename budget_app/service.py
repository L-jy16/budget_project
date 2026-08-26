import csv
import re
import uuid
from collections import defaultdict
from datetime import date
from pathlib import Path

from budget_app.decorators import AppError
from budget_app.models import Transaction
from budget_app.repository import DataRepository


class BudgetService:
    def __init__(
        self,
        repository: DataRepository
    ) -> None:
        self.repository = repository

    # --------------------------------------------------
    # Validation
    # --------------------------------------------------

    def validate_date(
        self,
        value: str
    ) -> str:

        if not re.fullmatch(
            r"\d{4}-\d{2}-\d{2}",
            value
        ):
            raise AppError(
                "날짜 형식이 올바르지 않습니다.",
                "YYYY-MM-DD 형식으로 입력해주세요. 예: 2026-08-27"
            )

        try:
            date.fromisoformat(value)

        except ValueError:
            raise AppError(
                "존재하지 않는 날짜입니다.",
                "올바른 날짜를 입력해주세요."
            )

        return value

    def validate_month(
        self,
        value: str
    ) -> str:

        if not re.fullmatch(
            r"\d{4}-\d{2}",
            value
        ):
            raise AppError(
                "월 형식이 올바르지 않습니다.",
                "YYYY-MM 형식으로 입력해주세요. 예: 2026-08"
            )

        try:
            date.fromisoformat(
                f"{value}-01"
            )

        except ValueError:
            raise AppError(
                "존재하지 않는 월입니다.",
                "01~12 사이의 월을 입력해주세요."
            )

        return value

    def validate_type(
        self,
        value: str
    ) -> str:

        if value not in (
            "income",
            "expense"
        ):
            raise AppError(
                "거래 타입이 올바르지 않습니다.",
                "income 또는 expense를 입력해주세요."
            )

        return value

    def validate_amount(
        self,
        value: str | int
    ) -> int:

        try:
            amount = int(value)

        except (ValueError, TypeError):
            raise AppError(
                "금액은 정수로 입력해야 합니다.",
                "예: 15000"
            )

        if amount <= 0:
            raise AppError(
                "금액은 0보다 커야 합니다.",
                "양수 금액을 입력해주세요."
            )

        return amount

    def validate_category(
        self,
        value: str
    ) -> str:

        if not self.repository.category_exists(
            value
        ):
            raise AppError(
                f"등록되지 않은 카테고리입니다: {value}",
                "category add 명령으로 카테고리를 먼저 추가해주세요."
            )

        return value

    def parse_tags(
        self,
        value: str
    ) -> list[str]:

        if not value.strip():
            return []

        return [
            tag.strip()
            for tag in value.split(",")
            if tag.strip()
        ]

    # --------------------------------------------------
    # Category
    # --------------------------------------------------

    def add_category(
        self,
        name: str
    ) -> None:

        name = name.strip()

        if not name:
            raise AppError(
                "카테고리 이름이 비어 있습니다.",
                "카테고리 이름을 입력해주세요."
            )

        if not self.repository.add_category(
            name
        ):
            raise AppError(
                f"이미 존재하는 카테고리입니다: {name}"
            )

    def list_categories(
        self
    ) -> list[str]:

        return self.repository.get_categories()

    def remove_category(
        self,
        name: str
    ) -> None:

        name = name.strip()

        if not self.repository.category_exists(
            name
        ):
            raise AppError(
                f"존재하지 않는 카테고리입니다: {name}"
            )

        if self.repository.category_in_use(
            name
        ):
            raise AppError(
                f"사용 중인 카테고리는 삭제할 수 없습니다: {name}",
                "해당 카테고리를 사용하는 거래를 먼저 수정하거나 삭제해주세요."
            )

        self.repository.remove_category(name)

    # --------------------------------------------------
    # Add
    # --------------------------------------------------

    def add_transaction(
        self,
        transaction_type: str,
        transaction_date: str,
        amount: str | int,
        category: str,
        memo: str = "",
        tags: str = "",
    ) -> Transaction:

        self.validate_date(
            transaction_date
        )

        self.validate_type(
            transaction_type
        )

        valid_amount = self.validate_amount(
            amount
        )

        self.validate_category(
            category
        )

        transaction = Transaction(
            id=self._create_id(),
            type=transaction_type,
            date=transaction_date,
            amount=valid_amount,
            category=category,
            memo=memo.strip(),
            tags=self.parse_tags(tags),
        )

        self.repository.add_transaction(
            transaction
        )

        return transaction

    def _create_id(self) -> str:

        return (
            "TX-"
            + uuid.uuid4().hex[:8].upper()
        )

    # --------------------------------------------------
    # List
    # --------------------------------------------------

    def list_transactions(
        self,
        limit: int
    ) -> list[Transaction]:

        if limit <= 0:
            raise AppError(
                "limit은 1 이상이어야 합니다."
            )

        result: list[Transaction] = []

        for transaction in (
            self.repository.iter_transactions_latest()
        ):

            result.append(transaction)

            if len(result) >= limit:
                break

        return result

    # --------------------------------------------------
    # Search
    # --------------------------------------------------

    def search_transactions(
        self,
        date_from: str | None = None,
        date_to: str | None = None,
        category: str | None = None,
        transaction_type: str | None = None,
        keyword: str | None = None,
        tag: str | None = None,
    ) -> list[Transaction]:

        if date_from:
            self.validate_date(date_from)

        if date_to:
            self.validate_date(date_to)

        if transaction_type:
            self.validate_type(
                transaction_type
            )

        if category:
            self.validate_category(
                category
            )

        result: list[Transaction] = []

        for transaction in (
            self.repository.iter_transactions_latest()
        ):

            if (
                date_from
                and transaction.date < date_from
            ):
                continue

            if (
                date_to
                and transaction.date > date_to
            ):
                continue

            if (
                category
                and transaction.category
                != category
            ):
                continue

            if (
                transaction_type
                and transaction.type
                != transaction_type
            ):
                continue

            if (
                keyword
                and keyword.lower()
                not in transaction.memo.lower()
            ):
                continue

            if (
                tag
                and tag not in transaction.tags
            ):
                continue

            result.append(
                transaction
            )

        return result

    # --------------------------------------------------
    # Update
    # --------------------------------------------------

    def get_transaction(
        self,
        transaction_id: str
    ) -> Transaction:

        transaction = (
            self.repository.find_transaction(
                transaction_id
            )
        )

        if transaction is None:
            raise AppError(
                f"존재하지 않는 거래입니다: {transaction_id}"
            )

        return transaction

    def update_transaction(
        self,
        transaction_id: str,
        transaction_date: str,
        transaction_type: str,
        category: str,
        amount: str | int,
        memo: str,
        tags: str,
    ) -> Transaction:

        self.get_transaction(
            transaction_id
        )

        self.validate_date(
            transaction_date
        )

        self.validate_type(
            transaction_type
        )

        self.validate_category(
            category
        )

        valid_amount = (
            self.validate_amount(amount)
        )

        updated = Transaction(
            id=transaction_id,
            type=transaction_type,
            date=transaction_date,
            amount=valid_amount,
            category=category,
            memo=memo,
            tags=self.parse_tags(tags),
        )

        if not self.repository.replace_transaction(
            updated
        ):
            raise AppError(
                "거래 수정에 실패했습니다."
            )

        return updated

    # --------------------------------------------------
    # Delete
    # --------------------------------------------------

    def delete_transaction(
        self,
        transaction_id: str
    ) -> None:

        if not self.repository.delete_transaction(
            transaction_id
        ):
            raise AppError(
                f"존재하지 않는 거래입니다: {transaction_id}"
            )

    # --------------------------------------------------
    # Budget
    # --------------------------------------------------

    def set_budget(
        self,
        month: str,
        amount: str | int
    ) -> int:

        self.validate_month(month)

        valid_amount = (
            self.validate_amount(amount)
        )

        self.repository.set_budget(
            month,
            valid_amount
        )

        return valid_amount

    # --------------------------------------------------
    # Summary
    # --------------------------------------------------

    def summary(
        self,
        month: str,
        top: int
    ) -> dict | None:

        self.validate_month(month)

        if top <= 0:
            raise AppError(
                "top 값은 1 이상이어야 합니다."
            )

        total_income = 0
        total_expense = 0

        category_expenses: dict[str, int] = (
            defaultdict(int)
        )

        count = 0

        for transaction in (
            self.repository.iter_transactions()
        ):

            if not transaction.date.startswith(
                month
            ):
                continue

            count += 1

            if transaction.type == "income":
                total_income += (
                    transaction.amount
                )

            else:
                total_expense += (
                    transaction.amount
                )

                category_expenses[
                    transaction.category
                ] += transaction.amount

        if count == 0:
            return None

        sorted_categories = sorted(
            category_expenses.items(),
            key=lambda item: item[1],
            reverse=True,
        )

        budget = (
            self.repository.get_budget(
                month
            )
        )

        usage_rate: float | None = None

        if budget is not None:
            usage_rate = (
                total_expense
                / budget
                * 100
            )

        return {
            "income": total_income,
            "expense": total_expense,
            "balance": (
                total_income
                - total_expense
            ),
            "categories": (
                sorted_categories[:top]
            ),
            "budget": budget,
            "usage_rate": usage_rate,
        }

    # --------------------------------------------------
    # Import
    # --------------------------------------------------

    def import_csv(
        self,
        input_path: str
    ) -> tuple[int, int]:

        path = Path(input_path)

        if not path.exists():
            raise AppError(
                f"CSV 파일을 찾을 수 없습니다: {input_path}"
            )

        imported = 0
        skipped = 0

        required_columns = {
            "date",
            "type",
            "category",
            "amount",
        }

        with path.open(
            "r",
            encoding="utf-8-sig",
            newline=""
        ) as file:

            reader = csv.DictReader(file)

            if reader.fieldnames is None:
                raise AppError(
                    "CSV 헤더가 없습니다."
                )

            if not required_columns.issubset(
                set(reader.fieldnames)
            ):
                raise AppError(
                    "CSV 필수 컬럼이 부족합니다.",
                    "date,type,category,amount 컬럼을 확인해주세요."
                )

            for row in reader:

                try:
                    self.add_transaction(
                        transaction_date=(
                            row.get("date", "")
                        ),
                        transaction_type=(
                            row.get("type", "")
                        ),
                        category=(
                            row.get("category", "")
                        ),
                        amount=(
                            row.get("amount", "")
                        ),
                        memo=(
                            row.get("memo", "")
                            or ""
                        ),
                        tags=(
                            row.get("tags", "")
                            or ""
                        ),
                    )

                    imported += 1

                except AppError:
                    skipped += 1

        return imported, skipped

    # --------------------------------------------------
    # Export
    # --------------------------------------------------

    def export_csv(
        self,
        output_path: str,
        month: str | None,
        date_from: str | None,
        date_to: str | None,
    ) -> int:

        if not month and not (
            date_from or date_to
        ):
            raise AppError(
                "export에는 검색 조건이 필요합니다.",
                "-month 또는 -from/-to 조건을 입력해주세요."
            )

        if month:
            self.validate_month(month)

        if date_from:
            self.validate_date(date_from)

        if date_to:
            self.validate_date(date_to)

        count = 0

        with Path(output_path).open(
            "w",
            encoding="utf-8",
            newline=""
        ) as file:

            writer = csv.writer(file)

            writer.writerow(
                [
                    "date",
                    "type",
                    "category",
                    "amount",
                    "memo",
                    "tags",
                ]
            )

            for transaction in (
                self.repository.iter_transactions_latest()
            ):

                if (
                    month
                    and not transaction.date.startswith(
                        month
                    )
                ):
                    continue

                if (
                    date_from
                    and transaction.date < date_from
                ):
                    continue

                if (
                    date_to
                    and transaction.date > date_to
                ):
                    continue

                writer.writerow(
                    [
                        transaction.date,
                        transaction.type,
                        transaction.category,
                        transaction.amount,
                        transaction.memo,
                        ",".join(
                            transaction.tags
                        ),
                    ]
                )

                count += 1

        return count