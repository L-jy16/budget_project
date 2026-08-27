import json
import os
import tempfile
from collections.abc import Iterator
from pathlib import Path

from budget_app.models import Transaction


class DataRepository:
    """
    가계부 데이터를 파일에 저장하고 불러오는 Repository 클래스.

    데이터는 JSONL(JSON Lines) 형식으로 관리한다.
    JSONL은 한 줄에 하나의 JSON 객체를 저장하는 방식이다.

    관리하는 파일
    - transactions.jsonl : 거래 내역
    - categories.jsonl   : 카테고리
    - budgets.jsonl      : 월별 예산
    """

    def __init__(self, data_dir: str = "data") -> None:
        # 데이터가 저장될 디렉터리 경로
        # 기본값은 프로젝트의 data 폴더
        self.data_dir = Path(data_dir)

        # 각 데이터를 저장할 JSONL 파일 경로
        self.transactions_file = self.data_dir / "transactions.jsonl"
        self.categories_file = self.data_dir / "categories.jsonl"
        self.budgets_file = self.data_dir / "budgets.jsonl"

        # 프로그램 실행 시 필요한 폴더와 파일이 있는지 확인하고
        # 없다면 자동으로 생성
        self.initialize_files()

    # --------------------------------------------------
    # 초기화
    # --------------------------------------------------

    def initialize_files(self) -> None:
        """
        데이터 저장에 필요한 폴더와 JSONL 파일을 생성한다.

        이미 존재하는 경우에는 기존 파일을 그대로 사용한다.
        """

        # data 디렉터리가 없으면 생성
        # parents=True : 상위 폴더도 필요한 경우 함께 생성
        # exist_ok=True : 이미 존재해도 오류를 발생시키지 않음
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # 프로그램에서 사용하는 데이터 파일 목록
        files = [
            self.transactions_file,
            self.categories_file,
            self.budgets_file,
        ]

        # 존재하지 않는 파일만 새로 생성
        for file_path in files:
            if not file_path.exists():
                file_path.touch()

    # --------------------------------------------------
    # Transaction
    # --------------------------------------------------

    def add_transaction(self, transaction: Transaction) -> None:
        """
        새로운 거래 내역을 transactions.jsonl 마지막에 추가한다.

        기존 데이터를 다시 작성하지 않고 append 모드("a")를 사용하여
        새로운 거래 한 건만 파일 끝에 추가한다.
        """

        with self.transactions_file.open(
            "a",
            encoding="utf-8"
        ) as file:

            # Transaction 객체를 dictionary로 변환한 뒤 JSON으로 저장
            json.dump(
                transaction.to_dict(),
                file,
                ensure_ascii=False
            )

            # JSONL 형식이므로 하나의 데이터 저장 후 줄바꿈
            file.write("\n")

    def iter_transactions(self) -> Iterator[Transaction]:
        """
        저장된 거래 내역을 앞에서부터 한 줄씩 읽는다.

        전체 파일을 리스트로 한 번에 메모리에 올리지 않고
        yield를 사용하여 거래를 하나씩 반환한다.

        따라서 거래 데이터가 많아져도 메모리 사용량을
        줄일 수 있는 Generator 기반 스트리밍 방식이다.
        """

        with self.transactions_file.open(
            "r",
            encoding="utf-8"
        ) as file:

            # 파일을 한 줄씩 읽음
            for line in file:
                line = line.strip()

                # 빈 줄은 무시
                if not line:
                    continue

                # JSON 문자열을 Python dictionary로 변환
                data = json.loads(line)

                # dictionary를 Transaction 객체로 변환하여 하나씩 반환
                yield Transaction.from_dict(data)

    def iter_transactions_latest(self) -> Iterator[Transaction]:
        """
        거래 파일을 뒤에서부터 읽어 최신 거래부터 반환한다.

        전체 거래 내역을 메모리에 올린 후 reverse하는 것이 아니라,
        파일 자체를 뒤에서부터 읽는다.

        따라서 데이터가 많아져도 메모리를 효율적으로 사용할 수 있다.
        """

        # _iter_lines_reverse()가 파일의 마지막 줄부터 반환
        for line in self._iter_lines_reverse(
            self.transactions_file
        ):
            # JSON 문자열을 dictionary로 변환
            data = json.loads(line)

            # Transaction 객체로 변환하여 반환
            yield Transaction.from_dict(data)

    def _iter_lines_reverse(
        self,
        file_path: Path,
        chunk_size: int = 8192,
    ) -> Iterator[str]:
        """
        파일을 뒤에서부터 일정 크기(chunk) 단위로 읽어
        마지막 줄부터 반환하는 Generator.

        파일 전체를 메모리에 읽지 않기 때문에
        대용량 파일에서도 메모리를 효율적으로 사용할 수 있다.

        chunk_size 기본값은 8192 byte(8KB).
        """

        # 바이트 단위로 위치를 이동해야 하므로 binary 모드로 파일 열기
        with file_path.open("rb") as file:

            # 파일 포인터를 파일의 끝으로 이동
            file.seek(0, os.SEEK_END)

            # 현재 위치 = 파일 전체 크기
            position = file.tell()

            # chunk 경계에서 잘린 줄을 이어 붙이기 위한 버퍼
            buffer = b""

            # 파일 시작 위치에 도달할 때까지 반복
            while position > 0:

                # 남은 파일 크기와 chunk_size 중 작은 값만 읽음
                read_size = min(chunk_size, position)

                # 읽을 위치를 앞으로 이동
                position -= read_size

                # 해당 위치로 파일 포인터 이동
                file.seek(position)

                # chunk만큼 데이터 읽기
                chunk = file.read(read_size)

                # 이전에 남아 있던 데이터와 연결
                buffer = chunk + buffer

                # 줄바꿈 기준으로 데이터 분리
                lines = buffer.split(b"\n")

                # 첫 번째 데이터는 chunk 경계에서 잘린 줄일 수 있으므로
                # 다음 반복에서 사용할 buffer로 보관
                buffer = lines[0]

                # 완성된 줄들은 뒤에서부터 반환
                for line in reversed(lines[1:]):
                    if line.strip():
                        # binary 데이터를 UTF-8 문자열로 변환
                        yield line.decode("utf-8")

            # 파일의 가장 첫 번째 줄이 buffer에 남아 있다면 반환
            if buffer.strip():
                yield buffer.decode("utf-8")

    def find_transaction(
        self,
        transaction_id: str
    ) -> Transaction | None:
        """
        거래 ID를 이용하여 특정 거래를 찾는다.

        찾으면 Transaction 객체를 반환하고,
        존재하지 않으면 None을 반환한다.
        """

        # 거래 데이터를 한 건씩 확인
        for transaction in self.iter_transactions():

            if transaction.id == transaction_id:
                return transaction

        # 일치하는 거래가 없는 경우
        return None

    def replace_transaction(
        self,
        updated: Transaction
    ) -> bool:
        """
        기존 거래를 수정한다.

        JSONL 파일은 특정 줄만 직접 수정하기 어렵기 때문에
        임시 파일에 전체 데이터를 다시 작성한다.

        수정할 거래 ID를 만나면 기존 거래 대신
        updated 데이터를 기록한다.

        모든 작업이 성공하면 os.replace()를 사용하여
        기존 파일을 임시 파일로 교체한다.
        """

        # 수정 대상 거래를 찾았는지 확인하기 위한 변수
        found = False

        # 예외 발생 시 임시 파일을 삭제하기 위해 경로를 저장
        temp_path: str | None = None

        try:
            # 원본 파일과 같은 data 디렉터리에 임시 파일 생성
            with tempfile.NamedTemporaryFile(
                "w",
                delete=False,
                dir=self.data_dir,
                encoding="utf-8",
            ) as temp_file:

                temp_path = temp_file.name

                # 기존 거래를 한 건씩 읽음
                for transaction in self.iter_transactions():

                    # 수정하려는 거래 ID를 찾으면
                    # 기존 객체 대신 updated 객체 사용
                    if transaction.id == updated.id:
                        transaction = updated
                        found = True

                    # 거래 데이터를 임시 파일에 저장
                    json.dump(
                        transaction.to_dict(),
                        temp_file,
                        ensure_ascii=False,
                    )

                    temp_file.write("\n")

            # 수정 대상이 존재했다면
            if found:
                # 임시 파일을 기존 transactions 파일로 교체
                os.replace(
                    temp_path,
                    self.transactions_file
                )

            else:
                # 수정 대상이 없다면 임시 파일은 필요 없으므로 삭제
                os.remove(temp_path)

            return found

        except Exception:
            # 처리 중 오류가 발생한 경우
            # 남아 있는 임시 파일을 삭제하여 불필요한 파일이
            # 생성되지 않도록 처리
            if temp_path and os.path.exists(temp_path):
                os.remove(temp_path)

            # 발생한 예외를 다시 상위 코드로 전달
            raise

    def delete_transaction(
        self,
        transaction_id: str
    ) -> bool:
        """
        특정 거래를 삭제한다.

        삭제할 거래를 제외한 나머지 거래를 임시 파일에 저장한 후
        기존 transactions.jsonl 파일과 교체한다.
        """

        # 삭제 대상 거래가 존재하는지 확인
        found = False

        # 임시 파일 경로
        temp_path: str | None = None

        try:
            with tempfile.NamedTemporaryFile(
                "w",
                delete=False,
                dir=self.data_dir,
                encoding="utf-8",
            ) as temp_file:

                temp_path = temp_file.name

                # 기존 거래를 하나씩 확인
                for transaction in self.iter_transactions():

                    # 삭제할 거래 ID라면 파일에 기록하지 않고 건너뜀
                    if transaction.id == transaction_id:
                        found = True
                        continue

                    # 삭제 대상이 아닌 거래만 임시 파일에 저장
                    json.dump(
                        transaction.to_dict(),
                        temp_file,
                        ensure_ascii=False,
                    )

                    temp_file.write("\n")

            if found:
                # 삭제 대상이 존재하면
                # 새롭게 작성한 임시 파일로 원본 파일 교체
                os.replace(
                    temp_path,
                    self.transactions_file
                )

            else:
                # 삭제 대상이 없으면 원본 파일을 변경할 필요가 없으므로
                # 생성했던 임시 파일 삭제
                os.remove(temp_path)

            return found

        except Exception:
            # 오류 발생 시 임시 파일 정리
            if temp_path and os.path.exists(temp_path):
                os.remove(temp_path)

            raise

    # --------------------------------------------------
    # Category
    # --------------------------------------------------

    def get_categories(self) -> list[str]:
        """
        categories.jsonl에 저장된 모든 카테고리 이름을 읽어
        list 형태로 반환한다.
        """

        categories: list[str] = []

        with self.categories_file.open(
            "r",
            encoding="utf-8"
        ) as file:

            for line in file:

                line = line.strip()

                # 빈 줄 무시
                if not line:
                    continue

                # JSON 문자열을 dictionary로 변환
                data = json.loads(line)

                # name 값만 리스트에 추가
                categories.append(data["name"])

        return categories

    def category_exists(self, name: str) -> bool:
        """
        입력한 카테고리가 이미 존재하는지 확인한다.
        """

        # name이 카테고리 목록에 있으면 True
        return name in self.get_categories()

    def add_category(self, name: str) -> bool:
        """
        새로운 카테고리를 추가한다.

        이미 존재하는 카테고리라면 False를 반환하고,
        새 카테고리라면 파일에 추가한 후 True를 반환한다.
        """

        # 중복 카테고리 등록 방지
        if self.category_exists(name):
            return False

        # append 모드로 파일 끝에 새로운 카테고리 추가
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
        """
        특정 카테고리가 거래 내역에서 사용 중인지 확인한다.

        카테고리 삭제 전에 사용 여부를 확인하는 용도로 사용할 수 있다.
        """

        # 모든 거래를 하나씩 확인
        for transaction in self.iter_transactions():

            if transaction.category == name:
                return True

        return False

    def remove_category(self, name: str) -> bool:
        """
        카테고리를 삭제한다.

        삭제할 카테고리를 제외한 나머지 카테고리를
        임시 파일에 저장한 뒤 기존 파일과 교체한다.
        """

        # 현재 카테고리 목록 가져오기
        categories = self.get_categories()

        # 삭제할 카테고리가 존재하지 않으면 False
        if name not in categories:
            return False

        # 삭제 대상 카테고리를 제외한 새로운 목록 생성
        remaining = [
            category
            for category in categories
            if category != name
        ]

        temp_path: str | None = None

        try:
            # 새로운 카테고리 파일을 만들기 위한 임시 파일 생성
            with tempfile.NamedTemporaryFile(
                "w",
                delete=False,
                dir=self.data_dir,
                encoding="utf-8",
            ) as temp_file:

                temp_path = temp_file.name

                # 삭제 대상 이외의 카테고리만 기록
                for category in remaining:

                    json.dump(
                        {"name": category},
                        temp_file,
                        ensure_ascii=False,
                    )

                    temp_file.write("\n")

            # 임시 파일로 기존 categories 파일 교체
            os.replace(
                temp_path,
                self.categories_file
            )

            return True

        except Exception:
            # 오류 발생 시 임시 파일 정리
            if temp_path and os.path.exists(temp_path):
                os.remove(temp_path)

            raise

    # --------------------------------------------------
    # Budget
    # --------------------------------------------------

    def get_budgets(self) -> dict[str, int]:
        """
        저장된 모든 월별 예산을 읽는다.

        반환 예:
        {
            "2026-08": 500000,
            "2026-09": 600000
        }
        """

        budgets: dict[str, int] = {}

        with self.budgets_file.open(
            "r",
            encoding="utf-8"
        ) as file:

            for line in file:

                line = line.strip()

                # 빈 줄은 무시
                if not line:
                    continue

                # JSON 데이터를 dictionary로 변환
                data = json.loads(line)

                # month를 key, amount를 value로 저장
                budgets[str(data["month"])] = int(
                    data["amount"]
                )

        return budgets

    def get_budget(
        self,
        month: str
    ) -> int | None:
        """
        특정 월의 예산을 조회한다.

        예:
        get_budget("2026-08")

        해당 월의 예산이 존재하지 않으면 None을 반환한다.
        """

        return self.get_budgets().get(month)

    def set_budget(
        self,
        month: str,
        amount: int
    ) -> None:
        """
        특정 월의 예산을 새로 설정하거나 수정한다.

        기존 예산 정보를 dictionary로 읽은 후
        해당 월의 값을 변경하고 전체 예산 파일을 다시 작성한다.

        임시 파일을 먼저 만든 뒤 os.replace()로 교체하여
        파일 수정 도중 원본 데이터가 손상될 가능성을 줄인다.
        """

        # 현재 저장되어 있는 모든 예산 가져오기
        budgets = self.get_budgets()

        # 해당 월의 예산 추가 또는 수정
        # 이미 존재하면 값이 덮어써지고,
        # 존재하지 않으면 새로운 key가 생성됨
        budgets[month] = amount

        temp_path: str | None = None

        try:
            # 수정된 데이터를 기록할 임시 파일 생성
            with tempfile.NamedTemporaryFile(
                "w",
                delete=False,
                dir=self.data_dir,
                encoding="utf-8",
            ) as temp_file:

                temp_path = temp_file.name

                # 월 순서대로 정렬하여 저장
                # 파일을 직접 확인할 때도 순서를 보기 쉽게 하기 위함
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

            # 모든 저장 작업이 정상적으로 끝난 후
            # 임시 파일을 실제 budgets 파일로 교체
            os.replace(
                temp_path,
                self.budgets_file
            )

        except Exception:
            # 오류 발생 시 만들어진 임시 파일 삭제
            if temp_path and os.path.exists(temp_path):
                os.remove(temp_path)

            # 예외를 숨기지 않고 상위 코드로 전달
            raise