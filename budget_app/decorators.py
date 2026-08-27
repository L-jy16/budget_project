from collections.abc import Callable
from functools import wraps
from pathlib import Path
from typing import Any
from datetime import datetime
import time


class AppError(Exception):
    """
    사용자에게 보여줄 수 있는 애플리케이션 전용 예외 클래스.

    Python 기본 예외 메시지를 그대로 보여주는 대신,
    사용자에게 이해하기 쉬운 오류 메시지와
    해결 방법에 대한 힌트를 함께 전달하기 위해 사용한다.
    """

    def __init__(
        self,
        message: str,
        hint: str = ""
    ) -> None:
        # Exception 부모 클래스에도 오류 메시지를 전달
        super().__init__(message)

        # 사용자에게 출력할 오류 메시지
        self.message = message

        # 오류 해결을 위한 추가 안내 문구
        # 힌트가 필요 없는 경우 기본값은 빈 문자열
        self.hint = hint


def handle_errors(
    func: Callable[..., Any]
) -> Callable[..., Any]:
    """
    프로그램에서 발생하는 예외를 공통적으로 처리하는 데코레이터.

    각 함수마다 try-except를 반복해서 작성하지 않고
    @handle_errors를 붙이는 것만으로
    동일한 오류 처리 방식을 적용할 수 있다.

    주요 역할:
    - AppError 처리
    - Ctrl+C 처리
    - 예상하지 못한 내부 오류 처리
    - 사용자에게 Python 스택트레이스를 직접 노출하지 않음
    """

    # 원래 함수의 이름, 설명 등을 유지하기 위해 @wraps 사용
    @wraps(func)
    def wrapper(
        *args: Any,
        **kwargs: Any
    ) -> Any:

        try:
            # 원래 함수 실행
            return func(*args, **kwargs)

        except AppError as error:
            # 프로그램에서 의도적으로 발생시킨
            # 사용자용 오류 처리

            print(
                f"[오류] {error.message}"
            )

            # hint가 존재하는 경우에만 출력
            if error.hint:
                print(
                    f"[힌트] {error.hint}"
                )

            # 오류가 발생했음을 의미하는 종료 코드 1 반환
            return 1

        except KeyboardInterrupt:
            # 사용자가 Ctrl+C를 눌러
            # 프로그램 실행을 직접 중단한 경우 처리

            print(
                "\n[오류] 사용자가 작업을 취소했습니다."
            )

            print(
                "[힌트] 명령어를 다시 실행해주세요."
            )

            return 1

        except Exception:
            # AppError가 아닌 예상하지 못한 예외 처리
            #
            # 실제 Python 예외 내용이나 스택트레이스를
            # 그대로 사용자에게 보여주지 않고
            # 일반적인 오류 메시지만 출력한다.
            #
            # 내부 구현 정보가 그대로 노출되는 것을 줄이고
            # 일반 사용자가 복잡한 오류 메시지를 보지 않도록 한다.

            print(
                "[오류] 프로그램 실행 중 예상하지 못한 문제가 발생했습니다."
            )

            print(
                "[힌트] 입력값과 데이터 파일 상태를 확인해주세요."
            )

            return 1

    # 데코레이터가 적용된 wrapper 함수 반환
    return wrapper


def log_execution(
    func: Callable[..., Any]
) -> Callable[..., Any]:
    """
    함수의 실행 결과를 로그 파일에 기록하는 데코레이터.

    로그 파일:
    logs/app.log

    기록 정보:
    - 실행 시각
    - 실행된 함수 이름
    - 실행 성공/실패 여부

    예:
    2026-08-27T12:30:10.123456 | import_csv | SUCCESS
    """

    @wraps(func)
    def wrapper(
        *args: Any,
        **kwargs: Any
    ) -> Any:

        # 로그 파일을 저장할 logs 디렉터리 지정
        log_dir = Path("logs")

        # logs 폴더가 없다면 자동 생성
        #
        # parents=True:
        # 필요한 상위 폴더까지 함께 생성
        #
        # exist_ok=True:
        # 이미 폴더가 있어도 오류를 발생시키지 않음
        log_dir.mkdir(
            parents=True,
            exist_ok=True
        )

        # 실제 로그가 저장될 파일
        log_file = log_dir / "app.log"

        # 함수 실행 시작 시각 기록
        start_time = datetime.now()

        try:
            # 실제 원래 함수 실행
            result = func(
                *args,
                **kwargs
            )

            # 예외 없이 실행이 끝났다면 성공으로 기록
            status = "SUCCESS"

            # 원래 함수의 반환값 그대로 반환
            return result

        except Exception:
            # 함수 실행 중 예외가 발생한 경우
            # 실패 상태로 기록
            status = "FAIL"

            # 여기서 예외를 처리해버리지 않고
            # 다시 상위 코드로 전달
            #
            # 따라서 handle_errors 같은
            # 다른 예외 처리 로직에서 처리할 수 있음
            raise

        finally:
            # 성공하든 실패하든 반드시 실행되는 영역

            # 함수 실행이 끝난 시각
            end_time = datetime.now()

            # 로그 파일을 append 모드로 열어
            # 기존 로그를 삭제하지 않고 뒤에 계속 추가
            with log_file.open(
                "a",
                encoding="utf-8"
            ) as file:

                # 실행 종료 시각 | 함수 이름 | 상태 형태로 기록
                file.write(
                    f"{end_time.isoformat()} | "
                    f"{func.__name__} | "
                    f"{status}\n"
                )

    return wrapper


def measure_time(
    func: Callable[..., Any]
) -> Callable[..., Any]:
    """
    함수 실행 시간을 측정하는 데코레이터.

    time.perf_counter()를 사용하여
    함수 실행 전후 시간을 측정하고
    실제 소요 시간을 초 단위로 출력한다.

    성능 확인이나 처리 속도 비교에 사용할 수 있다.
    """

    @wraps(func)
    def wrapper(
        *args: Any,
        **kwargs: Any
    ) -> Any:

        # 함수 실행 직전의 고해상도 시간 측정
        start = time.perf_counter()

        try:
            # 실제 함수 실행
            return func(
                *args,
                **kwargs
            )

        finally:
            # 함수가 성공하든 예외가 발생하든
            # 실행 시간은 반드시 측정

            # 함수 실행 종료 시각 측정
            end = time.perf_counter()

            # 총 실행 시간 계산
            elapsed = end - start

            # 함수 이름과 소요 시간을 출력
            # 소수점 아래 6자리까지 표시
            print(
                f"[실행 시간] "
                f"{func.__name__}: "
                f"{elapsed:.6f}초"
            )

    return wrapper