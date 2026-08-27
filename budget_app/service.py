import csv
import re
import uuid
from collections import defaultdict
from datetime import date
from pathlib import Path

from budget_app.decorators import (
    AppError,
    log_execution,
    measure_time,
)
from budget_app.models import Transaction
from budget_app.repository import DataRepository


class BudgetService:
    """
    가계부의 주요 비즈니스 로직을 담당하는 Service 클래스.

    Repository가 실제 파일 저장/조회 역할을 담당한다면,
    Service는 입력값 검증, 거래 처리, 검색, 통계 등의
    프로그램 핵심 기능을 담당한다.
    """

    def __init__(
        self,
        repository: DataRepository
    ) -> None:
        # 실제 데이터 저장/조회 작업을 담당할 Repository 객체
        # 외부에서 전달받아 사용한다.
        self.repository = repository

    # --------------------------------------------------
    # Validation
    # --------------------------------------------------

    def validate_date(
        self,
        value: str
    ) -> str:
        """
        날짜가 YYYY-MM-DD 형식인지 확인하고,
        실제로 존재하는 날짜인지 검증한다.
        """

        # 정규표현식을 이용해 YYYY-MM-DD 형식인지 먼저 검사
        if not re.fullmatch(
            r"\d{4}-\d{2}-\d{2}",
            value
        ):
            raise AppError(
                "날짜 형식이 올바르지 않습니다.",
                "YYYY-MM-DD 형식으로 입력해주세요. 예: 2026-08-27"
            )

        try:
            # 형식뿐 아니라 실제 존재하는 날짜인지 확인
            # 예: 2026-02-31 같은 날짜는 ValueError 발생
            date.fromisoformat(value)

        except ValueError:
            raise AppError(
                "존재하지 않는 날짜입니다.",
                "올바른 날짜를 입력해주세요."
            )

        # 검증에 성공한 날짜 반환
        return value

    def validate_month(
        self,
        value: str
    ) -> str:
        """
        월 입력값이 YYYY-MM 형식인지 확인하고,
        실제 존재하는 월인지 검증한다.
        """

        # YYYY-MM 형식 검사
        if not re.fullmatch(
            r"\d{4}-\d{2}",
            value
        ):
            raise AppError(
                "월 형식이 올바르지 않습니다.",
                "YYYY-MM 형식으로 입력해주세요. 예: 2026-08"
            )

        try:
            # date.fromisoformat()은 YYYY-MM-DD 형식이 필요하므로
            # 임시로 01일을 붙여 해당 월이 유효한지 검사
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
        """
        거래 타입이 income 또는 expense인지 검증한다.
        """

        # 허용된 거래 타입은 수입(income), 지출(expense) 두 가지
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
        """
        입력받은 금액을 정수로 변환하고
        0보다 큰 양수인지 확인한다.
        """

        try:
            # CLI에서 입력받은 문자열도 처리할 수 있도록
            # int 타입으로 변환
            amount = int(value)

        except (ValueError, TypeError):
            raise AppError(
                "금액은 정수로 입력해야 합니다.",
                "예: 15000"
            )

        # 0원이나 음수 금액은 허용하지 않음
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
        """
        입력한 카테고리가 실제로 등록되어 있는지 확인한다.
        """

        # Repository를 통해 등록된 카테고리인지 검사
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
        """
        쉼표로 입력된 태그 문자열을 리스트로 변환한다.

        예:
        "meal, lunch, food"
        -> ["meal", "lunch", "food"]
        """

        # 빈 문자열이면 빈 태그 목록 반환
        if not value.strip():
            return []

        # 쉼표 기준으로 분리하고 각 태그의 앞뒤 공백 제거
        # 공백만 있는 값은 제외
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
        """
        새로운 카테고리를 등록한다.
        """

        # 입력값 앞뒤 공백 제거
        name = name.strip()

        # 빈 카테고리 이름 방지
        if not name:
            raise AppError(
                "카테고리 이름이 비어 있습니다.",
                "카테고리 이름을 입력해주세요."
            )

        # Repository에서 중복 여부 확인 후 추가
        # 이미 존재하면 add_category()가 False 반환
        if not self.repository.add_category(
            name
        ):
            raise AppError(
                f"이미 존재하는 카테고리입니다: {name}"
            )

    def list_categories(
        self
    ) -> list[str]:
        """
        현재 등록된 모든 카테고리를 반환한다.
        """

        return self.repository.get_categories()

    def remove_category(
        self,
        name: str
    ) -> None:
        """
        카테고리를 삭제한다.

        존재하지 않는 카테고리는 삭제할 수 없으며,
        거래에서 사용 중인 카테고리도 데이터 일관성을 위해
        삭제하지 못하도록 처리한다.
        """

        name = name.strip()

        # 카테고리 존재 여부 확인
        if not self.repository.category_exists(
            name
        ):
            raise AppError(
                f"존재하지 않는 카테고리입니다: {name}"
            )

        # 기존 거래가 해당 카테고리를 사용하고 있는지 확인
        if self.repository.category_in_use(
            name
        ):
            raise AppError(
                f"사용 중인 카테고리는 삭제할 수 없습니다: {name}",
                "해당 카테고리를 사용하는 거래를 먼저 수정하거나 삭제해주세요."
            )

        # 문제가 없다면 실제 카테고리 삭제
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
        """
        새로운 거래를 생성하고 저장한다.

        저장하기 전에 날짜, 타입, 금액, 카테고리를 검증한다.
        """

        # 날짜 검증
        self.validate_date(
            transaction_date
        )

        # income / expense 검증
        self.validate_type(
            transaction_type
        )

        # 금액을 검증하고 int로 변환
        valid_amount = self.validate_amount(
            amount
        )

        # 등록된 카테고리인지 확인
        self.validate_category(
            category
        )

        # 모든 검증이 완료되면 Transaction 객체 생성
        transaction = Transaction(
            # 각 거래를 구분하기 위한 고유 ID 생성
            id=self._create_id(),
            type=transaction_type,
            date=transaction_date,
            amount=valid_amount,
            category=category,
            memo=memo.strip(),
            # 문자열 태그를 리스트로 변환
            tags=self.parse_tags(tags),
        )

        # Repository를 통해 실제 파일에 저장
        self.repository.add_transaction(
            transaction
        )

        # 생성된 거래 객체 반환
        return transaction

    def _create_id(self) -> str:
        """
        거래마다 사용할 고유 ID를 생성한다.

        UUID에서 앞 8자리를 사용하고 대문자로 변환하여
        TX-XXXXXXXX 형식으로 만든다.

        예:
        TX-098CE71A
        """

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
        """
        최신 거래부터 지정한 개수만큼 반환한다.
        """

        # 최소 1건 이상 조회하도록 제한
        if limit <= 0:
            raise AppError(
                "limit은 1 이상이어야 합니다."
            )

        result: list[Transaction] = []

        # Repository의 Generator를 사용해
        # 최신 거래부터 하나씩 가져옴
        for transaction in (
            self.repository.iter_transactions_latest()
        ):

            result.append(transaction)

            # 필요한 개수를 모두 가져오면
            # 더 이상 파일을 읽지 않고 즉시 반복 종료
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
        """
        여러 검색 조건을 조합하여 거래를 검색한다.

        지원 조건:
        - 시작 날짜
        - 종료 날짜
        - 카테고리
        - 거래 타입
        - 메모 키워드
        - 태그
        """

        # 검색 조건이 입력된 경우에만 해당 값 검증
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

        # 최신 거래부터 하나씩 검사
        for transaction in (
            self.repository.iter_transactions_latest()
        ):

            # 시작 날짜보다 이전이면 제외
            # YYYY-MM-DD 형식은 문자열 비교로도 날짜 순서 비교 가능
            if (
                date_from
                and transaction.date < date_from
            ):
                continue

            # 종료 날짜보다 이후이면 제외
            if (
                date_to
                and transaction.date > date_to
            ):
                continue

            # 카테고리가 다르면 제외
            if (
                category
                and transaction.category
                != category
            ):
                continue

            # 거래 타입이 다르면 제외
            if (
                transaction_type
                and transaction.type
                != transaction_type
            ):
                continue

            # keyword가 메모에 포함되어 있지 않으면 제외
            # lower()를 사용해 영문 대소문자 차이를 무시
            if (
                keyword
                and keyword.lower()
                not in transaction.memo.lower()
            ):
                continue

            # 지정한 태그가 거래 태그 목록에 없으면 제외
            if (
                tag
                and tag not in transaction.tags
            ):
                continue

            # 모든 검색 조건을 통과한 거래만 결과에 추가
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
        """
        거래 ID를 이용하여 거래 한 건을 조회한다.

        존재하지 않는 거래라면 AppError를 발생시킨다.
        """

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
        """
        기존 거래 정보를 수정한다.

        거래가 실제로 존재하는지 확인한 후
        새로운 값들을 검증하고 수정된 Transaction 객체를 만든다.
        """

        # 수정 대상 거래가 존재하는지 먼저 확인
        self.get_transaction(
            transaction_id
        )

        # 새로운 날짜 검증
        self.validate_date(
            transaction_date
        )

        # 새로운 거래 타입 검증
        self.validate_type(
            transaction_type
        )

        # 새로운 카테고리 검증
        self.validate_category(
            category
        )

        # 새로운 금액 검증 및 정수 변환
        valid_amount = (
            self.validate_amount(amount)
        )

        # 기존 ID는 그대로 유지하고
        # 수정된 값을 사용하여 새로운 Transaction 객체 생성
        updated = Transaction(
            id=transaction_id,
            type=transaction_type,
            date=transaction_date,
            amount=valid_amount,
            category=category,
            memo=memo,
            tags=self.parse_tags(tags),
        )

        # Repository를 통해 기존 거래 데이터를 수정
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
        """
        거래 ID를 이용하여 거래를 삭제한다.
        """

        # Repository에서 삭제하지 못했다면
        # 해당 ID의 거래가 존재하지 않는 것으로 처리
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
        """
        특정 월의 예산을 설정한다.
        """

        # YYYY-MM 형식 및 실제 월인지 확인
        self.validate_month(month)

        # 예산 금액 검증
        valid_amount = (
            self.validate_amount(amount)
        )

        # Repository를 통해 예산 저장
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
        """
        특정 월의 수입/지출 요약 정보를 계산한다.

        계산 결과:
        - 총 수입
        - 총 지출
        - 잔액
        - 지출 상위 카테고리
        - 설정 예산
        - 예산 사용률
        """

        # 조회할 월 검증
        self.validate_month(month)

        # 상위 카테고리 개수는 1 이상이어야 함
        if top <= 0:
            raise AppError(
                "top 값은 1 이상이어야 합니다."
            )

        # 월 전체 수입
        total_income = 0

        # 월 전체 지출
        total_expense = 0

        # 카테고리별 지출 금액 저장
        #
        # defaultdict(int)를 사용하면
        # 존재하지 않는 key도 기본값 0부터 계산할 수 있다.
        category_expenses: dict[str, int] = (
            defaultdict(int)
        )

        # 해당 월에 거래가 존재하는지 확인하기 위한 개수
        count = 0

        # 전체 거래를 한 건씩 읽음
        for transaction in (
            self.repository.iter_transactions()
        ):

            # 지정한 월의 거래가 아니면 제외
            # 예: month="2026-08"이면
            # 2026-08로 시작하는 날짜만 처리
            if not transaction.date.startswith(
                month
            ):
                continue

            count += 1

            # 수입인 경우 총 수입에 추가
            if transaction.type == "income":
                total_income += (
                    transaction.amount
                )

            # 수입이 아니면 지출로 처리
            else:
                # 전체 지출 증가
                total_expense += (
                    transaction.amount
                )

                # 해당 카테고리의 지출도 함께 누적
                category_expenses[
                    transaction.category
                ] += transaction.amount

        # 해당 월에 거래가 하나도 없으면 요약 정보 없음
        if count == 0:
            return None

        # 카테고리별 지출을 금액이 큰 순서대로 정렬
        sorted_categories = sorted(
            category_expenses.items(),
            key=lambda item: item[1],
            reverse=True,
        )

        # 해당 월에 설정된 예산 조회
        budget = (
            self.repository.get_budget(
                month
            )
        )

        # 예산이 설정되지 않은 경우를 위해 None으로 초기화
        usage_rate: float | None = None

        if budget is not None:
            # 예산 사용률 계산
            #
            # 예:
            # 예산 500,000원
            # 지출 250,000원
            # -> 50%
            usage_rate = (
                total_expense
                / budget
                * 100
            )

        # 계산된 요약 정보를 dictionary 형태로 반환
        return {
            "income": total_income,
            "expense": total_expense,

            # 잔액 = 총 수입 - 총 지출
            "balance": (
                total_income
                - total_expense
            ),

            # 지출이 많은 카테고리 중 상위 top개만 반환
            "categories": (
                sorted_categories[:top]
            ),

            "budget": budget,
            "usage_rate": usage_rate,
        }

    # --------------------------------------------------
    # Import
    # --------------------------------------------------

    # 함수 실행 여부를 로그에 기록하는 Decorator
    @log_execution

    # 함수 실행 시간을 측정하는 Decorator
    @measure_time
    def import_csv(
        self,
        input_path: str
    ) -> tuple[int, int]:
        """
        CSV 파일에 저장된 거래 내역을 가져와
        가계부 거래 데이터로 등록한다.

        반환값:
        (성공한 거래 수, 건너뛴 거래 수)
        """

        # 문자열 경로를 Path 객체로 변환
        path = Path(input_path)

        # CSV 파일 존재 여부 확인
        if not path.exists():
            raise AppError(
                f"CSV 파일을 찾을 수 없습니다: {input_path}"
            )

        # 정상적으로 등록된 데이터 개수
        imported = 0

        # 검증 오류 등으로 건너뛴 데이터 개수
        skipped = 0

        # CSV 파일에 반드시 존재해야 하는 컬럼
        required_columns = {
            "date",
            "type",
            "category",
            "amount",
        }

        # utf-8-sig를 사용하면 UTF-8 BOM이 있는 CSV도 처리 가능
        # newline=""은 csv 모듈이 줄바꿈을 직접 처리하도록 하기 위함
        with path.open(
            "r",
            encoding="utf-8-sig",
            newline=""
        ) as file:

            # 첫 번째 행을 컬럼 이름으로 사용하여
            # 각 행을 dictionary 형태로 읽음
            reader = csv.DictReader(file)

            # 헤더 자체가 없는 경우
            if reader.fieldnames is None:
                raise AppError(
                    "CSV 헤더가 없습니다."
                )

            # CSV가 필수 컬럼을 모두 가지고 있는지 검사
            if not required_columns.issubset(
                set(reader.fieldnames)
            ):
                raise AppError(
                    "CSV 필수 컬럼이 부족합니다.",
                    "date,type,category,amount 컬럼을 확인해주세요."
                )

            # CSV 데이터를 한 행씩 처리
            for row in reader:

                try:
                    # 기존 add_transaction()을 재사용한다.
                    # 따라서 CSV 데이터에도 동일한 검증 규칙이 적용된다.
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

                        # memo와 tags는 선택 항목이므로
                        # 값이 없으면 빈 문자열 사용
                        memo=(
                            row.get("memo", "")
                            or ""
                        ),
                        tags=(
                            row.get("tags", "")
                            or ""
                        ),
                    )

                    # 정상적으로 저장되었다면 성공 개수 증가
                    imported += 1

                except AppError:
                    # 한 행의 데이터가 잘못되어도
                    # 전체 Import를 중단하지 않고 해당 행만 건너뜀
                    skipped += 1

        # 성공 건수와 실패/건너뜀 건수를 함께 반환
        return imported, skipped

    # --------------------------------------------------
    # Export
    # --------------------------------------------------

    # 함수 실행 여부를 로그에 기록
    @log_execution

    # 함수 실행 시간 측정
    @measure_time
    def export_csv(
        self,
        output_path: str,
        month: str | None,
        date_from: str | None,
        date_to: str | None,
    ) -> int:
        """
        거래 내역을 CSV 파일로 내보낸다.

        모든 데이터를 무조건 내보내는 것이 아니라
        month 또는 date_from/date_to 중
        최소 하나 이상의 검색 조건이 필요하다.

        반환값:
        CSV 파일에 저장한 거래 개수
        """

        # 아무 검색 조건도 입력하지 않았다면 오류 처리
        if not month and not (
            date_from or date_to
        ):
            raise AppError(
                "export에는 검색 조건이 필요합니다.",
                "-month 또는 -from/-to 조건을 입력해주세요."
            )

        # 입력된 검색 조건 각각 검증
        if month:
            self.validate_month(month)

        if date_from:
            self.validate_date(date_from)

        if date_to:
            self.validate_date(date_to)

        # 실제 CSV에 기록한 거래 개수
        count = 0

        # 출력 CSV 파일 생성
        with Path(output_path).open(
            "w",
            encoding="utf-8",
            newline=""
        ) as file:

            writer = csv.writer(file)

            # CSV의 첫 번째 행에 헤더 작성
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

            # 최신 거래부터 한 건씩 읽어서 조건 검사
            for transaction in (
                self.repository.iter_transactions_latest()
            ):

                # 특정 월을 지정했다면 해당 월이 아닌 거래 제외
                if (
                    month
                    and not transaction.date.startswith(
                        month
                    )
                ):
                    continue

                # 시작 날짜 이전의 거래 제외
                if (
                    date_from
                    and transaction.date < date_from
                ):
                    continue

                # 종료 날짜 이후의 거래 제외
                if (
                    date_to
                    and transaction.date > date_to
                ):
                    continue

                # 검색 조건을 모두 통과한 거래를 CSV에 기록
                writer.writerow(
                    [
                        transaction.date,
                        transaction.type,
                        transaction.category,
                        transaction.amount,
                        transaction.memo,

                        # 내부적으로 list[str] 형태인 tags를
                        # CSV에서는 쉼표로 연결된 문자열로 저장
                        ",".join(
                            transaction.tags
                        ),
                    ]
                )

                # 저장된 거래 개수 증가
                count += 1

        # 총 Export 건수 반환
        return count