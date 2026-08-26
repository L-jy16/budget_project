from collections.abc import Callable
from functools import wraps
from pathlib import Path
from typing import Any
from datetime import datetime
import time


class AppError(Exception):
    """사용자에게 보여줄 수 있는 애플리케이션 오류"""

    def __init__(self, message: str, hint: str = "") -> None:
        super().__init__(message)
        self.message = message
        self.hint = hint


def handle_errors(func: Callable[..., Any]) -> Callable[..., Any]:
    """
    공통 예외 처리 데코레이터.

    Python 스택트레이스를 그대로 노출하지 않고
    사용자에게 오류 원인과 해결 힌트를 출력한다.
    """

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
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

        except Exception:
            # 예상하지 못한 내부 예외의 상세 내용은
            # 사용자 화면에 그대로 노출하지 않는다.
            print("[오류] 프로그램 실행 중 예상하지 못한 문제가 발생했습니다.")
            print("[힌트] 입력값과 데이터 파일 상태를 확인해주세요.")
            return 1

    return wrapper


def log_execution(func: Callable[..., Any]) -> Callable[..., Any]:
    """
    함수 실행 정보를 파일로 기록하는 로그 데코레이터.

    로그 파일:
    logs/app.log
    """

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        log_dir = Path("logs")
        log_dir.mkdir(parents=True, exist_ok=True)

        log_file = log_dir / "app.log"

        start_time = datetime.now()

        try:
            result = func(*args, **kwargs)

            status = "SUCCESS"

            return result

        except Exception:
            status = "FAIL"
            raise

        finally:
            end_time = datetime.now()

            with log_file.open(
                "a",
                encoding="utf-8"
            ) as file:

                file.write(
                    f"{end_time.isoformat()} | "
                    f"{func.__name__} | "
                    f"{status}\n"
                )

    return wrapper


def measure_time(func: Callable[..., Any]) -> Callable[..., Any]:
    """
    함수 실행 시간을 측정하는 데코레이터.
    """

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        start = time.perf_counter()

        try:
            return func(*args, **kwargs)

        finally:
            end = time.perf_counter()

            elapsed = end - start

            print(
                f"[실행 시간] "
                f"{func.__name__}: "
                f"{elapsed:.6f}초"
            )

    return wrapper