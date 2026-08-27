import argparse
import sys

from budget_app.decorators import (
    AppError,
    handle_errors,
)
from budget_app.repository import DataRepository
from budget_app.service import BudgetService


class FriendlyArgumentParser(
    argparse.ArgumentParser
):
    """
    argparse의 기본 오류 메시지를
    사용자가 이해하기 쉬운 한국어 형태로 변경한 Parser 클래스.
    """

    def error(self, message: str) -> None:
        # argparse에서 잘못된 옵션이나 명령어가 들어온 경우
        # 기본 에러 대신 직접 정의한 메시지 출력
        print(f"[오류] {message}")

        # 사용자가 도움말을 확인할 수 있도록 힌트 제공
        print(
            "[힌트] -help 옵션으로 사용 방법을 확인해주세요."
        )

        # 현재 명령어의 기본 사용 방법 출력
        self.print_usage()

        # 명령행 인자 오류이므로 종료 코드 2로 프로그램 종료
        raise SystemExit(2)


def add_help_option(
    parser: argparse.ArgumentParser
) -> None:
    """
    각 명령어 Parser에 -help 옵션을 추가한다.

    argparse 기본 옵션은 -h / --help이지만,
    과제에서 요구하는 -help 형태를 사용하기 위해
    직접 도움말 옵션을 등록한다.
    """

    parser.add_argument(
        "-help",
        action="help",
        help="사용 방법을 출력합니다.",
    )


def create_parser() -> argparse.ArgumentParser:
    """
    가계부 CLI에서 사용할 모든 명령어와 옵션을 정의한다.

    지원 명령어:
    - add
    - list
    - search
    - summary
    - budget
    - category
    - update
    - delete
    - import
    - export
    """

    # 프로그램의 최상위 ArgumentParser 생성
    parser = FriendlyArgumentParser(
        # 도움말에서 표시되는 프로그램 이름
        prog="budget_app",

        # 프로그램 설명
        description="파일 기반 가계부 콘솔 프로그램",

        # argparse의 기본 -h 옵션을 사용하지 않고
        # 직접 정의한 -help 옵션을 사용하기 위해 False 설정
        add_help=False,
    )

    # 최상위 명령에서도 -help 사용 가능
    add_help_option(parser)

    # 데이터가 저장될 디렉터리를 사용자가 지정할 수 있는 옵션
    parser.add_argument(
        "-data-dir",
        default="data",
        help="데이터 저장 폴더 (기본값: data)",
    )

    # add, list, search 등의 하위 명령어를 등록하기 위한 Parser
    subparsers = parser.add_subparsers(
        # 선택한 명령어 이름이 args.command에 저장됨
        dest="command",
        help="사용할 명령어",
    )

    # --------------------------------------------------
    # add
    # --------------------------------------------------

    # 새로운 거래를 추가하는 명령어
    add_parser = subparsers.add_parser(
        "add",
        help="거래를 추가합니다.",
        add_help=False,
    )

    # budget_app add -help 지원
    add_help_option(add_parser)

    # add 명령은 날짜, 타입, 카테고리, 금액 등을
    # 실행 후 input()으로 직접 입력받으므로 추가 옵션이 없음

    # --------------------------------------------------
    # list
    # --------------------------------------------------

    # 최근 거래 목록 조회 명령어
    list_parser = subparsers.add_parser(
        "list",
        help="거래 목록을 조회합니다.",
        add_help=False,
    )

    add_help_option(list_parser)

    # 출력할 거래 개수를 지정
    list_parser.add_argument(
        "-limit",
        type=int,
        default=10,
        help="출력할 거래 개수",
    )

    # --------------------------------------------------
    # search
    # --------------------------------------------------

    # 조건에 맞는 거래를 검색하는 명령어
    search_parser = subparsers.add_parser(
        "search",
        help="거래를 검색합니다.",
        add_help=False,
    )

    add_help_option(search_parser)

    # 검색 시작 날짜
    # -from은 Python 예약어처럼 직접 속성명으로 쓰기 불편하므로
    # dest를 사용해 args.date_from으로 저장
    search_parser.add_argument(
        "-from",
        dest="date_from"
    )

    # 검색 종료 날짜
    search_parser.add_argument(
        "-to",
        dest="date_to"
    )

    # 특정 카테고리 검색
    search_parser.add_argument(
        "-category"
    )

    # income / expense 검색
    # 결과는 args.transaction_type으로 저장
    search_parser.add_argument(
        "-type",
        dest="transaction_type"
    )

    # 메모에 포함된 키워드 검색
    search_parser.add_argument(
        "-q",
        dest="keyword"
    )

    # 태그 검색
    search_parser.add_argument(
        "-tag"
    )

    # --------------------------------------------------
    # summary
    # --------------------------------------------------

    # 월별 수입/지출 요약 명령어
    summary_parser = (
        subparsers.add_parser(
            "summary",
            help="월별 요약을 출력합니다.",
            add_help=False,
        )
    )

    add_help_option(
        summary_parser
    )

    # 어떤 월의 통계를 조회할지 지정
    # required=True이므로 반드시 입력해야 함
    summary_parser.add_argument(
        "-month",
        required=True
    )

    # 지출 상위 카테고리를 몇 개 출력할지 지정
    # 기본값은 3개
    summary_parser.add_argument(
        "-top",
        type=int,
        default=3
    )

    # --------------------------------------------------
    # budget
    # --------------------------------------------------

    # 월별 예산 관리 명령어
    budget_parser = subparsers.add_parser(
        "budget",
        help="예산을 관리합니다.",
        add_help=False,
    )

    add_help_option(
        budget_parser
    )

    # budget 아래에 set과 같은 추가 하위 명령을 등록
    budget_subparsers = (
        budget_parser.add_subparsers(
            dest="budget_command"
        )
    )

    # budget set 명령어 생성
    budget_set = (
        budget_subparsers.add_parser(
            "set",
            add_help=False,
        )
    )

    add_help_option(
        budget_set
    )

    # 예산을 설정할 월
    budget_set.add_argument(
        "-month",
        required=True
    )

    # 해당 월에 설정할 예산
    budget_set.add_argument(
        "-amount",
        required=True
    )

    # --------------------------------------------------
    # category
    # --------------------------------------------------

    # 카테고리 관리 명령어
    category_parser = (
        subparsers.add_parser(
            "category",
            help="카테고리를 관리합니다.",
            add_help=False,
        )
    )

    add_help_option(
        category_parser
    )

    # category 아래에 add/list/remove 명령 추가
    category_subparsers = (
        category_parser.add_subparsers(
            dest="category_command"
        )
    )

    # category add
    category_add = (
        category_subparsers.add_parser(
            "add",
            add_help=False
        )
    )

    add_help_option(
        category_add
    )

    # category list
    category_list = (
        category_subparsers.add_parser(
            "list",
            add_help=False
        )
    )

    add_help_option(
        category_list
    )

    # category remove
    category_remove = (
        category_subparsers.add_parser(
            "remove",
            add_help=False
        )
    )

    add_help_option(
        category_remove
    )

    # --------------------------------------------------
    # update
    # --------------------------------------------------

    # 기존 거래 수정 명령어
    update_parser = (
        subparsers.add_parser(
            "update",
            help="거래를 수정합니다.",
            add_help=False,
        )
    )

    add_help_option(
        update_parser
    )

    # 어떤 거래를 수정할 것인지 ID로 지정
    update_parser.add_argument(
        "-id",
        required=True
    )

    # --------------------------------------------------
    # delete
    # --------------------------------------------------

    # 거래 삭제 명령어
    delete_parser = (
        subparsers.add_parser(
            "delete",
            help="거래를 삭제합니다.",
            add_help=False,
        )
    )

    add_help_option(
        delete_parser
    )

    # 삭제할 거래 ID
    delete_parser.add_argument(
        "-id",
        required=True
    )

    # --------------------------------------------------
    # import
    # --------------------------------------------------

    # CSV 파일에서 거래 데이터를 가져오는 명령어
    import_parser = (
        subparsers.add_parser(
            "import",
            help="CSV 거래를 가져옵니다.",
            add_help=False,
        )
    )

    add_help_option(
        import_parser
    )

    # 가져올 CSV 파일 경로
    # 사용 예: import -from sample.csv
    import_parser.add_argument(
        "-from",
        dest="input_file",
        required=True,
    )

    # --------------------------------------------------
    # export
    # --------------------------------------------------

    # 거래 데이터를 CSV 파일로 내보내는 명령어
    export_parser = (
        subparsers.add_parser(
            "export",
            help="CSV 파일로 내보냅니다.",
            add_help=False,
        )
    )

    add_help_option(
        export_parser
    )

    # 출력할 CSV 파일 경로
    export_parser.add_argument(
        "-out",
        required=True
    )

    # 특정 월의 거래만 Export할 경우 사용
    export_parser.add_argument(
        "-month"
    )

    # 시작 날짜 조건
    export_parser.add_argument(
        "-from",
        dest="date_from"
    )

    # 종료 날짜 조건
    export_parser.add_argument(
        "-to",
        dest="date_to"
    )

    # 완성된 Parser 반환
    return parser


def print_transaction(
    transaction
) -> None:
    """
    Transaction 객체 하나를
    CLI에서 보기 좋은 한 줄 형태로 출력한다.
    """

    # Transaction의 tags는 리스트이므로
    # 쉼표로 연결한 문자열 형태로 변환
    tags = ",".join(
        transaction.tags
    )

    # 거래 정보를 | 기호로 구분하여 출력
    print(
        f"{transaction.id} | "
        f"{transaction.date} | "
        f"{transaction.type} | "
        f"{transaction.category} | "
        f"{transaction.amount} | "
        f"{transaction.memo} | "
        f"{tags}"
    )


def prompt_validated(
    prompt: str,
    validator
):
    """
    사용자 입력이 올바르게 들어올 때까지 반복한다.

    validator 함수에 입력값을 전달하여 검증하고,
    AppError가 발생하면 오류와 힌트를 출력한 후 다시 입력받는다.
    """

    while True:
        # 사용자로부터 입력받고 앞뒤 공백 제거
        value = input(prompt).strip()

        try:
            # 전달받은 검증 함수 실행
            # 검증 성공 시 변환된 값도 그대로 반환 가능
            return validator(value)

        except AppError as error:
            # 검증에 실패하면 프로그램을 종료하지 않고
            # 오류 내용을 보여준 뒤 다시 입력받음
            print(
                f"[오류] {error.message}"
            )

            # 힌트가 존재하는 경우만 출력
            if error.hint:
                print(
                    f"[힌트] {error.hint}"
                )


# run() 전체에서 발생하는 AppError 등을
# 공통적으로 처리하기 위한 Decorator
@handle_errors
def run() -> int:
    """
    CLI 프로그램의 실제 실행 흐름을 담당한다.

    1. 명령행 인자를 분석한다.
    2. Repository와 Service 객체를 생성한다.
    3. 선택한 명령에 따라 필요한 기능을 실행한다.
    """

    # 명령어와 옵션 정의
    parser = create_parser()

    # 터미널에서 입력한 명령행 옵션 분석
    args = parser.parse_args()

    # 아무 명령도 입력하지 않았다면 전체 도움말 출력
    if args.command is None:
        parser.print_help()
        return 0

    # 실제 JSONL 데이터를 담당하는 Repository 생성
    # 사용자가 -data-dir을 입력했다면 해당 폴더 사용
    repository = DataRepository(
        args.data_dir
    )

    # 비즈니스 로직을 담당하는 Service에
    # Repository를 전달
    service = BudgetService(
        repository
    )

    # --------------------------------------------------
    # add
    # --------------------------------------------------

    if args.command == "add":

        # 날짜가 올바르게 입력될 때까지 반복
        transaction_date = prompt_validated(
            "날짜(YYYY-MM-DD): ",
            service.validate_date,
        )

        # income 또는 expense가 올바르게 입력될 때까지 반복
        transaction_type = (
            prompt_validated(
                "타입(income/expense): ",
                service.validate_type,
            )
        )

        # 카테고리 역시 올바르게 입력될 때까지 반복
        while True:
            category = input(
                "카테고리: "
            ).strip()

            try:
                # 등록되어 있는 카테고리인지 확인
                service.validate_category(
                    category
                )
                break

            except AppError as error:
                print(
                    f"[오류] {error.message}"
                )
                print(
                    f"[힌트] {error.hint}"
                )

        # 금액이 양의 정수가 될 때까지 반복 입력
        amount = prompt_validated(
            "금액(양수): ",
            service.validate_amount,
        )

        # 메모는 선택 입력이므로 별도 검증하지 않음
        memo = input(
            "메모(선택): "
        )

        # 태그 역시 선택 입력
        # 쉼표로 여러 태그 입력 가능
        tags = input(
            "태그(쉼표 구분, 선택): "
        )

        # 모든 입력을 Service에 전달하여
        # Transaction 생성 및 저장
        transaction = (
            service.add_transaction(
                transaction_type,
                transaction_date,
                amount,
                category,
                memo,
                tags,
            )
        )

        # 새로 생성된 거래 ID 출력
        print(
            f"[저장 완료] id={transaction.id}"
        )

    # --------------------------------------------------
    # list
    # --------------------------------------------------

    elif args.command == "list":

        # 최신 거래부터 limit 개수만큼 조회
        transactions = (
            service.list_transactions(
                args.limit
            )
        )

        # 거래가 한 건도 없는 경우 안내 메시지 출력
        if not transactions:
            print(
                "[안내] 저장된 거래가 없습니다."
            )

        # 조회한 각 거래를 동일한 형식으로 출력
        for transaction in transactions:
            print_transaction(
                transaction
            )

    # --------------------------------------------------
    # search
    # --------------------------------------------------

    elif args.command == "search":

        # 입력된 검색 조건을 Service로 전달
        transactions = (
            service.search_transactions(
                date_from=args.date_from,
                date_to=args.date_to,
                category=args.category,
                transaction_type=(
                    args.transaction_type
                ),
                keyword=args.keyword,
                tag=args.tag,
            )
        )

        # 조건에 맞는 거래가 없는 경우
        if not transactions:
            print(
                "[안내] 검색 결과가 없습니다."
            )

        # 검색된 거래 출력
        for transaction in transactions:
            print_transaction(
                transaction
            )

    # --------------------------------------------------
    # summary
    # --------------------------------------------------

    elif args.command == "summary":

        # 특정 월에 대한 월별 요약 계산
        result = service.summary(
            args.month,
            args.top,
        )

        # 해당 월에 거래가 없다면 안내 후 정상 종료
        if result is None:
            print(
                "[안내] 해당 월의 데이터가 없습니다."
            )
            return 0

        # 총 수입 출력
        print(
            f"총 수입: {result['income']}원"
        )

        # 총 지출 출력
        print(
            f"총 지출: {result['expense']}원"
        )

        # 잔액 = 수입 - 지출
        print(
            f"잔액: {result['balance']}원"
        )

        # 해당 월의 예산이 설정된 경우에만 예산 정보 출력
        if result["budget"] is not None:

            print(
                f"예산: {result['budget']}원 "
                f"(사용률 "
                f"{result['usage_rate']:.1f}%)"
            )

            # 실제 지출이 예산보다 많으면 경고 출력
            if (
                result["expense"]
                > result["budget"]
            ):
                print(
                    "[경고] 예산을 초과했습니다."
                )

        # 지출이 많은 카테고리 순위 제목 출력
        print(
            f"지출 TOP {args.top}"
        )

        # enumerate를 사용하여 1부터 순위 번호를 함께 출력
        for index, (
            category,
            amount
        ) in enumerate(
            result["categories"],
            start=1,
        ):
            print(
                f"{index}) "
                f"{category} "
                f"{amount}원"
            )

    # --------------------------------------------------
    # budget
    # --------------------------------------------------

    elif args.command == "budget":

        # 현재 구현된 budget 하위 명령은 set뿐이므로
        # 다른 명령이 들어오면 사용 방법 안내
        if args.budget_command != "set":
            print(
                "[안내] budget set 명령을 사용해주세요."
            )
            return 0

        # Service에서 월과 금액을 검증한 뒤 예산 저장
        amount = service.set_budget(
            args.month,
            args.amount,
        )

        print(
            f"[저장 완료] "
            f"{args.month} 예산 "
            f"{amount}원"
        )

    # --------------------------------------------------
    # category
    # --------------------------------------------------

    elif args.command == "category":

        # category add
        if args.category_command == "add":

            # 추가할 카테고리 이름 입력
            name = input(
                "카테고리명: "
            )

            # Service를 통해 중복 여부 등을 확인한 뒤 저장
            service.add_category(
                name
            )

            print(
                f"[저장 완료] "
                f"category={name.strip()}"
            )

        # category list
        elif (
            args.category_command
            == "list"
        ):

            # 전체 카테고리 조회
            categories = (
                service.list_categories()
            )

            # 등록된 카테고리가 없는 경우
            if not categories:
                print(
                    "[안내] 등록된 카테고리가 없습니다."
                )

            # 카테고리를 한 줄씩 출력
            for category in categories:
                print(
                    f"- {category}"
                )

        # category remove
        elif (
            args.category_command
            == "remove"
        ):

            # 삭제할 카테고리 입력
            name = input(
                "삭제할 카테고리명: "
            ).strip()

            # 카테고리가 사용 중인지 등을 Service에서 검사
            service.remove_category(
                name
            )

            print(
                f"[삭제 완료] "
                f"category={name}"
            )

        # add/list/remove 중 아무것도 선택하지 않은 경우
        else:
            print(
                "[안내] category add/list/remove를 사용해주세요."
            )

    # --------------------------------------------------
    # update
    # --------------------------------------------------

    elif args.command == "update":

        # 먼저 수정하려는 기존 거래를 ID로 조회
        old = service.get_transaction(
            args.id
        )

        print(
            "Enter를 누르면 기존 값을 유지합니다."
        )

        # 기존 값을 [] 안에 보여주고 새 날짜 입력
        transaction_date = input(
            f"날짜 [{old.date}]: "
        ).strip()

        # 아무 값도 입력하지 않고 Enter를 누르면 기존 값 유지
        if not transaction_date:
            transaction_date = old.date

        transaction_type = input(
            f"타입 [{old.type}]: "
        ).strip()

        if not transaction_type:
            transaction_type = old.type

        category = input(
            f"카테고리 [{old.category}]: "
        ).strip()

        if not category:
            category = old.category

        amount = input(
            f"금액 [{old.amount}]: "
        ).strip()

        if not amount:
            # input 결과는 문자열이므로 기존 int 값을 문자열로 변환
            amount = str(
                old.amount
            )

        memo = input(
            f"메모 [{old.memo}]: "
        )

        if not memo:
            memo = old.memo

        # 기존 태그 리스트를 입력 화면에 보여주기 위해
        # 쉼표 문자열로 변환
        old_tags = ",".join(
            old.tags
        )

        tags = input(
            f"태그 [{old_tags}]: "
        )

        if not tags:
            tags = old_tags

        # 변경된 값을 Service로 전달하여 수정
        # Service에서 다시 유효성 검사를 수행함
        updated = (
            service.update_transaction(
                args.id,
                transaction_date,
                transaction_type,
                category,
                amount,
                memo,
                tags,
            )
        )

        print(
            f"[수정 완료] id={updated.id}"
        )

    # --------------------------------------------------
    # delete
    # --------------------------------------------------

    elif args.command == "delete":

        # 입력한 거래 ID를 이용하여 삭제
        service.delete_transaction(
            args.id
        )

        print(
            f"[삭제 완료] id={args.id}"
        )

    # --------------------------------------------------
    # import
    # --------------------------------------------------

    elif args.command == "import":

        # CSV 파일의 거래를 가져옴
        #
        # imported : 정상 등록된 행 수
        # skipped  : 잘못된 데이터로 건너뛴 행 수
        imported, skipped = (
            service.import_csv(
                args.input_file
            )
        )

        print(
            f"[완료] imported={imported}, "
            f"skipped={skipped}"
        )

    # --------------------------------------------------
    # export
    # --------------------------------------------------

    elif args.command == "export":

        # 조건에 맞는 거래를 CSV 파일로 내보냄
        count = service.export_csv(
            args.out,
            args.month,
            args.date_from,
            args.date_to,
        )

        # 생성된 파일명과 저장된 거래 개수 출력
        print(
            f"[완료] {args.out} "
            f"({count} records)"
        )

    # 프로그램 정상 종료
    return 0


def main() -> None:
    """
    프로그램의 최종 진입점.

    run()이 반환한 종료 코드를
    sys.exit()에 전달하여 프로그램을 종료한다.
    """

    sys.exit(
        run()
    )