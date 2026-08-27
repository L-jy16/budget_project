from dataclasses import dataclass, field
from typing import Any


@dataclass
class Transaction:
    """
    가계부의 거래 한 건을 표현하는 데이터 모델.

    하나의 거래가 가지고 있어야 하는 정보를
    하나의 객체로 묶어서 관리하기 위해 사용한다.

    예:
    - 거래 ID
    - 수입/지출 타입
    - 날짜
    - 금액
    - 카테고리
    - 메모
    - 태그
    """

    # 거래를 구분하기 위한 고유 ID
    # 예: TX-098CE71A
    id: str

    # 거래 타입
    # income : 수입
    # expense : 지출
    type: str

    # 거래 날짜
    # YYYY-MM-DD 형식의 문자열로 저장
    # 예: 2026-08-27
    date: str

    # 거래 금액
    # 계산에 사용하기 쉽도록 int 타입으로 저장
    amount: int

    # 거래가 속한 카테고리
    # 예: food, transport, salary
    category: str

    # 거래에 대한 간단한 메모
    # 선택 항목이므로 기본값은 빈 문자열
    memo: str = ""

    # 거래에 연결된 태그 목록
    #
    # 예:
    # ["meal", "lunch"]
    #
    # list를 기본값으로 직접 지정하지 않고
    # field(default_factory=list)를 사용한다.
    #
    # 이렇게 해야 Transaction 객체마다
    # 서로 독립적인 새로운 리스트가 생성된다.
    tags: list[str] = field(
        default_factory=list
    )

    def to_dict(
        self
    ) -> dict[str, Any]:
        """
        Transaction 객체를 dictionary 형태로 변환한다.

        JSON 파일에 저장할 때
        Python 객체를 바로 저장할 수 없기 때문에
        먼저 dictionary로 변환하는 용도로 사용한다.

        예:

        Transaction(...)
        ↓

        {
            "id": "TX-12345678",
            "type": "expense",
            "date": "2026-08-27",
            "amount": 15000,
            "category": "food",
            "memo": "lunch",
            "tags": ["meal"]
        }
        """

        return {
            "id": self.id,
            "type": self.type,
            "date": self.date,
            "amount": self.amount,
            "category": self.category,
            "memo": self.memo,
            "tags": self.tags,
        }

    @classmethod
    def from_dict(
        cls,
        data: dict[str, Any]
    ) -> "Transaction":
        """
        dictionary 데이터를 Transaction 객체로 변환한다.

        JSONL 파일에서 데이터를 읽으면
        json.loads()의 결과가 dictionary이므로,
        이를 다시 Transaction 객체로 복원하기 위해 사용한다.

        @classmethod를 사용했기 때문에
        특정 객체가 없어도 클래스 자체에서 호출할 수 있다.

        예:

        Transaction.from_dict(data)
        """

        return cls(
            # 각 값을 필요한 타입으로 명확하게 변환
            id=str(
                data["id"]
            ),

            type=str(
                data["type"]
            ),

            date=str(
                data["date"]
            ),

            amount=int(
                data["amount"]
            ),

            category=str(
                data["category"]
            ),

            # memo는 과거 데이터 등에 값이 없을 수도 있으므로
            # get()을 사용하고 기본값으로 빈 문자열을 사용
            memo=str(
                data.get(
                    "memo",
                    ""
                )
            ),

            # tags가 없는 경우에도 오류가 발생하지 않도록
            # 빈 리스트를 기본값으로 사용
            tags=list(
                data.get(
                    "tags",
                    []
                )
            ),
        )