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
    def error(self, message: str) -> None:
        print(f"[오류] {message}")
        print(
            "[힌트] -help 옵션으로 사용 방법을 확인해주세요."
        )
        self.print_usage()
        raise SystemExit(2)


def add_help_option(
    parser: argparse.ArgumentParser
) -> None:

    parser.add_argument(
        "-help",
        action="help",
        help="사용 방법을 출력합니다.",
    )


def create_parser() -> argparse.ArgumentParser:

    parser = FriendlyArgumentParser(
        prog="budget_app",
        description="파일 기반 가계부 콘솔 프로그램",
        add_help=False,
    )

    add_help_option(parser)

    parser.add_argument(
        "-data-dir",
        default="data",
        help="데이터 저장 폴더 (기본값: data)",
    )

    subparsers = parser.add_subparsers(
        dest="command",
        help="사용할 명령어",
    )

    # --------------------------------------------------
    # add
    # --------------------------------------------------

    add_parser = subparsers.add_parser(
        "add",
        help="거래를 추가합니다.",
        add_help=False,
    )

    add_help_option(add_parser)

    # --------------------------------------------------
    # list
    # --------------------------------------------------

    list_parser = subparsers.add_parser(
        "list",
        help="거래 목록을 조회합니다.",
        add_help=False,
    )

    add_help_option(list_parser)

    list_parser.add_argument(
        "-limit",
        type=int,
        default=10,
        help="출력할 거래 개수",
    )

    # --------------------------------------------------
    # search
    # --------------------------------------------------

    search_parser = subparsers.add_parser(
        "search",
        help="거래를 검색합니다.",
        add_help=False,
    )

    add_help_option(search_parser)

    search_parser.add_argument(
        "-from",
        dest="date_from"
    )

    search_parser.add_argument(
        "-to",
        dest="date_to"
    )

    search_parser.add_argument(
        "-category"
    )

    search_parser.add_argument(
        "-type",
        dest="transaction_type"
    )

    search_parser.add_argument(
        "-q",
        dest="keyword"
    )

    search_parser.add_argument(
        "-tag"
    )

    # --------------------------------------------------
    # summary
    # --------------------------------------------------

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

    summary_parser.add_argument(
        "-month",
        required=True
    )

    summary_parser.add_argument(
        "-top",
        type=int,
        default=3
    )

    # --------------------------------------------------
    # budget
    # --------------------------------------------------

    budget_parser = subparsers.add_parser(
        "budget",
        help="예산을 관리합니다.",
        add_help=False,
    )

    add_help_option(
        budget_parser
    )

    budget_subparsers = (
        budget_parser.add_subparsers(
            dest="budget_command"
        )
    )

    budget_set = (
        budget_subparsers.add_parser(
            "set",
            add_help=False,
        )
    )

    add_help_option(
        budget_set
    )

    budget_set.add_argument(
        "-month",
        required=True
    )

    budget_set.add_argument(
        "-amount",
        required=True
    )

    # --------------------------------------------------
    # category
    # --------------------------------------------------

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

    category_subparsers = (
        category_parser.add_subparsers(
            dest="category_command"
        )
    )

    category_add = (
        category_subparsers.add_parser(
            "add",
            add_help=False
        )
    )

    add_help_option(
        category_add
    )

    category_list = (
        category_subparsers.add_parser(
            "list",
            add_help=False
        )
    )

    add_help_option(
        category_list
    )

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

    update_parser.add_argument(
        "-id",
        required=True
    )

    # --------------------------------------------------
    # delete
    # --------------------------------------------------

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

    delete_parser.add_argument(
        "-id",
        required=True
    )

    # --------------------------------------------------
    # import
    # --------------------------------------------------

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

    import_parser.add_argument(
        "-from",
        dest="input_file",
        required=True,
    )

    # --------------------------------------------------
    # export
    # --------------------------------------------------

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

    export_parser.add_argument(
        "-out",
        required=True
    )

    export_parser.add_argument(
        "-month"
    )

    export_parser.add_argument(
        "-from",
        dest="date_from"
    )

    export_parser.add_argument(
        "-to",
        dest="date_to"
    )

    return parser


def print_transaction(
    transaction
) -> None:

    tags = ",".join(
        transaction.tags
    )

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
    while True:
        value = input(prompt).strip()

        try:
            return validator(value)

        except AppError as error:
            print(
                f"[오류] {error.message}"
            )

            if error.hint:
                print(
                    f"[힌트] {error.hint}"
                )


@handle_errors
def run() -> int:

    parser = create_parser()

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        return 0

    repository = DataRepository(
        args.data_dir
    )

    service = BudgetService(
        repository
    )

    # --------------------------------------------------
    # add
    # --------------------------------------------------

    if args.command == "add":

        transaction_date = prompt_validated(
            "날짜(YYYY-MM-DD): ",
            service.validate_date,
        )

        transaction_type = (
            prompt_validated(
                "타입(income/expense): ",
                service.validate_type,
            )
        )

        while True:
            category = input(
                "카테고리: "
            ).strip()

            try:
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

        amount = prompt_validated(
            "금액(양수): ",
            service.validate_amount,
        )

        memo = input(
            "메모(선택): "
        )

        tags = input(
            "태그(쉼표 구분, 선택): "
        )

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

        print(
            f"[저장 완료] id={transaction.id}"
        )

    # --------------------------------------------------
    # list
    # --------------------------------------------------

    elif args.command == "list":

        transactions = (
            service.list_transactions(
                args.limit
            )
        )

        if not transactions:
            print(
                "[안내] 저장된 거래가 없습니다."
            )

        for transaction in transactions:
            print_transaction(
                transaction
            )

    # --------------------------------------------------
    # search
    # --------------------------------------------------

    elif args.command == "search":

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

        if not transactions:
            print(
                "[안내] 검색 결과가 없습니다."
            )

        for transaction in transactions:
            print_transaction(
                transaction
            )

    # --------------------------------------------------
    # summary
    # --------------------------------------------------

    elif args.command == "summary":

        result = service.summary(
            args.month,
            args.top,
        )

        if result is None:
            print(
                "[안내] 해당 월의 데이터가 없습니다."
            )
            return 0

        print(
            f"총 수입: {result['income']}원"
        )

        print(
            f"총 지출: {result['expense']}원"
        )

        print(
            f"잔액: {result['balance']}원"
        )

        if result["budget"] is not None:

            print(
                f"예산: {result['budget']}원 "
                f"(사용률 "
                f"{result['usage_rate']:.1f}%)"
            )

            if (
                result["expense"]
                > result["budget"]
            ):
                print(
                    "[경고] 예산을 초과했습니다."
                )

        print(
            f"지출 TOP {args.top}"
        )

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

        if args.budget_command != "set":
            print(
                "[안내] budget set 명령을 사용해주세요."
            )
            return 0

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

        if args.category_command == "add":

            name = input(
                "카테고리명: "
            )

            service.add_category(
                name
            )

            print(
                f"[저장 완료] "
                f"category={name.strip()}"
            )

        elif (
            args.category_command
            == "list"
        ):

            categories = (
                service.list_categories()
            )

            if not categories:
                print(
                    "[안내] 등록된 카테고리가 없습니다."
                )

            for category in categories:
                print(
                    f"- {category}"
                )

        elif (
            args.category_command
            == "remove"
        ):

            name = input(
                "삭제할 카테고리명: "
            ).strip()

            service.remove_category(
                name
            )

            print(
                f"[삭제 완료] "
                f"category={name}"
            )

        else:
            print(
                "[안내] category add/list/remove를 사용해주세요."
            )

    # --------------------------------------------------
    # update
    # --------------------------------------------------

    elif args.command == "update":

        old = service.get_transaction(
            args.id
        )

        print(
            "Enter를 누르면 기존 값을 유지합니다."
        )

        transaction_date = input(
            f"날짜 [{old.date}]: "
        ).strip()

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
            amount = str(
                old.amount
            )

        memo = input(
            f"메모 [{old.memo}]: "
        )

        if not memo:
            memo = old.memo

        old_tags = ",".join(
            old.tags
        )

        tags = input(
            f"태그 [{old_tags}]: "
        )

        if not tags:
            tags = old_tags

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

        count = service.export_csv(
            args.out,
            args.month,
            args.date_from,
            args.date_to,
        )

        print(
            f"[완료] {args.out} "
            f"({count} records)"
        )

    return 0


def main() -> None:
    sys.exit(
        run()
    )