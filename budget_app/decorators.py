from collections.abc import Callable
from functools import wraps
from typing import Any


class AppError(Exception):
    """사용자에게 보여줄 수 있는 애플리케이션 오류"""

    def __init__(self, message: str, hint: str = "") -> None:
        super().__init__(message)
        self.message = message
        self.hint = hint


def handle_errors(func: Callable[..., int]) -> Callable[..., int]:
    """
    CLI 공통 예외 처리 데코레이터.
    스택트레이스를 직접 출력하지 않고
    사용자에게 원인과 해결 힌트를 보여준다.
    """

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> int:
        try:
            return func(*args, **kwargs)

        except AppError as error:
            print(f"[오류] {error.message}")

            if error.hint:
                print(f"[힌트] {error.hint}")

            return 1

        except KeyboardInterrupt:
            print("\n[오류] 사용자가 작업을 취소했습니다.")
            print("[힌트] 명령어를 다시 실행해주세요.")
            return 1

        except Exception as error:
            print(f"[오류] 프로그램 실행 중 문제가 발생했습니다: {error}")
            print("[힌트] 입력값과 저장 파일을 확인해주세요.")
            return 1

    return wrapper