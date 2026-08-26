import json
import os
import tempfile
from collections.abc import Iterator
from pathlib import Path

from budget_app.models import Transaction


class DataRepository:
    def __init__(self, data_dir: str = "data") -> None:
        self.data_dir = Path(data_dir)

        self.transactions_file = self.data_dir / "transactions.jsonl"
        self.categories_file = self.data_dir / "categories.jsonl"
        self.budgets_file = self.data_dir / "budgets.jsonl"

        self.initialize_files()

    # --------------------------------------------------
    # 초기화
    # --------------------------------------------------

    def initialize_files(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)

        files = [
            self.transactions_file,
            self.categories_file,
            self.budgets_file,
        ]

        for file_path in files:
            if not file_path.exists():
                file_path.touch()

    # --------------------------------------------------
    # Transaction
    # --------------------------------------------------

    def add_transaction(self, transaction: Transaction) -> None:
        with self.transactions_file.open(
            "a",
            encoding="utf-8"
        ) as file:
            json.dump(
                transaction.to_dict(),
                file,
                ensure_ascii=False
            )
            file.write("\n")

    def iter_transactions(self) -> Iterator[Transaction]:
        """
        전체 파일을 리스트로 읽지 않고
        한 줄씩 읽어서 Transaction을 반환한다.
        Generator 기반 스트리밍 처리.
        """

        with self.transactions_file.open(
            "r",
            encoding="utf-8"
        ) as file:

            for line in file:
                line = line.strip()

                if not line:
                    continue

                data = json.loads(line)

                yield Transaction.from_dict(data)

    def iter_transactions_latest(self) -> Iterator[Transaction]:
        """
        JSONL 파일을 뒤에서부터 읽는다.
        전체 거래를 메모리에 올리지 않고
        최신 거래부터 Generator로 반환한다.
        """

        for line in self._iter_lines_reverse(
            self.transactions_file
        ):
            data = json.loads(line)

            yield Transaction.from_dict(data)

    def _iter_lines_reverse(
        self,
        file_path: Path,
        chunk_size: int = 8192,
    ) -> Iterator[str]:

        with file_path.open("rb") as file:
            file.seek(0, os.SEEK_END)

            position = file.tell()
            buffer = b""

            while position > 0:

                read_size = min(chunk_size, position)
                position -= read_size

                file.seek(position)

                chunk = file.read(read_size)

                buffer = chunk + buffer

                lines = buffer.split(b"\n")
                buffer = lines[0]

                for line in reversed(lines[1:]):
                    if line.strip():
                        yield line.decode("utf-8")

            if buffer.strip():
                yield buffer.decode("utf-8")

    def find_transaction(
        self,
        transaction_id: str
    ) -> Transaction | None:

        for transaction in self.iter_transactions():

            if transaction.id == transaction_id:
                return transaction

        return None

    def replace_transaction(
        self,
        updated: Transaction
    ) -> bool:

        found = False

        temp_path: str | None = None

        try:
            with tempfile.NamedTemporaryFile(
                "w",
                delete=False,
                dir=self.data_dir,
                encoding="utf-8",
            ) as temp_file:

                temp_path = temp_file.name

                for transaction in self.iter_transactions():

                    if transaction.id == updated.id:
                        transaction = updated
                        found = True

                    json.dump(
                        transaction.to_dict(),
                        temp_file,
                        ensure_ascii=False,
                    )

                    temp_file.write("\n")

            if found:
                os.replace(
                    temp_path,
                    self.transactions_file
                )
            else:
                os.remove(temp_path)

            return found

        except Exception:
            if temp_path and os.path.exists(temp_path):
                os.remove(temp_path)

            raise

    def delete_transaction(
        self,
        transaction_id: str
    ) -> bool:

        found = False
        temp_path: str | None = None

        try:
            with tempfile.NamedTemporaryFile(
                "w",
                delete=False,
                dir=self.data_dir,
                encoding="utf-8",
            ) as temp_file:

                temp_path = temp_file.name

                for transaction in self.iter_transactions():

                    if transaction.id == transaction_id:
                        found = True
                        continue

                    json.dump(
                        transaction.to_dict(),
                        temp_file,
                        ensure_ascii=False,
                    )

                    temp_file.write("\n")

            if found:
                os.replace(
                    temp_path,
                    self.transactions_file
                )
            else:
                os.remove(temp_path)

            return found

        except Exception:
            if temp_path and os.path.exists(temp_path):
                os.remove(temp_path)

            raise

    # --------------------------------------------------
    # Category
    # --------------------------------------------------

    def get_categories(self) -> list[str]:

        categories: list[str] = []

        with self.categories_file.open(
            "r",
            encoding="utf-8"
        ) as file:

            for line in file:

                line = line.strip()

                if not line:
                    continue

                data = json.loads(line)

                categories.append(data["name"])

        return categories

    def category_exists(self, name: str) -> bool:
        return name in self.get_categories()

    def add_category(self, name: str) -> bool:

        if self.category_exists(name):
            return False

        with self.categories_file.open(
            "a",
            encoding="utf-8"
        ) as file:

            json.dump(
                {"name": name},
                file,
                ensure_ascii=False,
            )

            file.write("\n")

        return True

    def category_in_use(self, name: str) -> bool:

        for transaction in self.iter_transactions():

            if transaction.category == name:
                return True

        return False

    def remove_category(self, name: str) -> bool:

        categories = self.get_categories()

        if name not in categories:
            return False

        remaining = [
            category
            for category in categories
            if category != name
        ]

        temp_path: str | None = None

        try:
            with tempfile.NamedTemporaryFile(
                "w",
                delete=False,
                dir=self.data_dir,
                encoding="utf-8",
            ) as temp_file:

                temp_path = temp_file.name

                for category in remaining:

                    json.dump(
                        {"name": category},
                        temp_file,
                        ensure_ascii=False,
                    )

                    temp_file.write("\n")

            os.replace(
                temp_path,
                self.categories_file
            )

            return True

        except Exception:
            if temp_path and os.path.exists(temp_path):
                os.remove(temp_path)

            raise

    # --------------------------------------------------
    # Budget
    # --------------------------------------------------

    def get_budgets(self) -> dict[str, int]:

        budgets: dict[str, int] = {}

        with self.budgets_file.open(
            "r",
            encoding="utf-8"
        ) as file:

            for line in file:

                line = line.strip()

                if not line:
                    continue

                data = json.loads(line)

                budgets[str(data["month"])] = int(
                    data["amount"]
                )

        return budgets

    def get_budget(
        self,
        month: str
    ) -> int | None:

        return self.get_budgets().get(month)

    def set_budget(
        self,
        month: str,
        amount: int
    ) -> None:

        budgets = self.get_budgets()

        budgets[month] = amount

        temp_path: str | None = None

        try:
            with tempfile.NamedTemporaryFile(
                "w",
                delete=False,
                dir=self.data_dir,
                encoding="utf-8",
            ) as temp_file:

                temp_path = temp_file.name

                for budget_month in sorted(budgets):

                    json.dump(
                        {
                            "month": budget_month,
                            "amount": budgets[budget_month],
                        },
                        temp_file,
                        ensure_ascii=False,
                    )

                    temp_file.write("\n")

            os.replace(
                temp_path,
                self.budgets_file
            )

        except Exception:
            if temp_path and os.path.exists(temp_path):
                os.remove(temp_path)

            raise