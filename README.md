<!-- @format -->

# budget_project# 파일 기반 가계부 콘솔 프로그램

Python 표준 라이브러리만 사용하여 구현한 JSONL 기반 가계부 콘솔 프로그램입니다.

거래 추가, 조회, 검색, 수정, 삭제, 월별 요약, 예산 관리, 카테고리 관리, CSV 가져오기/내보내기 기능을 제공합니다.

또한 Generator, Decorator, Type Hint, dataclass, 모듈 분리 구조를 적용하여 유지보수성과 데이터 안정성을 고려했습니다.

---

## 1. 개발 환경

- Python 3.10 이상
- 테스트 환경: Python 3.13.2
- 외부 라이브러리 사용 없음
- Python 표준 라이브러리만 사용

---

## 2. 실행 방법

프로젝트 최상위 폴더에서 아래 명령어를 실행합니다.

```bash
python3 -m budget_app
```

도움말 확인:

```bash
python3 -m budget_app -help
```

각 명령어별 도움말도 확인할 수 있습니다.

```bash
python3 -m budget_app add -help
python3 -m budget_app list -help
python3 -m budget_app search -help
python3 -m budget_app summary -help
python3 -m budget_app budget -help
python3 -m budget_app category -help
python3 -m budget_app update -help
python3 -m budget_app delete -help
python3 -m budget_app import -help
python3 -m budget_app export -help
```

---

## 3. 프로젝트 구조

```text
budget_project/
├── budget_app/
│   ├── __init__.py
│   ├── __main__.py
│   ├── cli.py
│   ├── models.py
│   ├── repository.py
│   ├── service.py
│   └── decorators.py
├── data/
│   ├── transactions.jsonl
│   ├── categories.jsonl
│   └── budgets.jsonl
└── README.md
```

각 모듈의 역할은 다음과 같습니다.

- `models.py`

  - 거래 데이터 구조 정의
  - `Transaction` dataclass 사용

- `repository.py`

  - JSONL 파일 읽기/쓰기
  - 거래, 카테고리, 예산 데이터 저장
  - Generator 기반 데이터 읽기
  - update/delete 시 임시 파일을 이용한 안전한 파일 교체

- `service.py`

  - 거래 추가, 검색, 수정, 삭제
  - 입력값 검증
  - 월별 요약
  - 예산 계산
  - 카테고리 관리
  - CSV import/export

- `cli.py`

  - 명령어 처리
  - 사용자 입력 처리
  - 결과 출력

- `decorators.py`

  - 공통 예외 처리
  - 오류 메시지 출력

---

## 4. 데이터 저장 방식

본 프로그램은 JSONL 형식을 사용합니다.

기본 저장 위치는 다음과 같습니다.

```text
./data
```

저장 파일:

```text
data/transactions.jsonl
data/categories.jsonl
data/budgets.jsonl
```

프로그램 최초 실행 시 파일이 존재하지 않으면 자동으로 생성됩니다.

### transactions.jsonl

거래 데이터를 저장합니다.

예:

```json
{
  "id": "TX-AB12CD34",
  "type": "expense",
  "date": "2026-08-27",
  "amount": 15000,
  "category": "food",
  "memo": "점심",
  "tags": ["meal"]
}
```

### categories.jsonl

카테고리를 저장합니다.

예:

```json
{"name": "food"}
{"name": "transport"}
```

### budgets.jsonl

월별 예산을 저장합니다.

예:

```json
{ "month": "2026-08", "amount": 500000 }
```

---

## 5. 다른 데이터 폴더 사용

기본값은 `data` 폴더입니다.

다른 저장 폴더를 사용하려면 다음과 같이 실행합니다.

```bash
python3 -m budget_app -data-dir mydata list
```

---

# 주요 기능

## 6. 카테고리 관리

거래를 추가하기 전에 먼저 카테고리를 등록해야 합니다.

### 카테고리 추가

```bash
python3 -m budget_app category add
```

실행 예:

```text
카테고리명: food
[저장 완료] category=food
```

### 카테고리 목록 조회

```bash
python3 -m budget_app category list
```

출력 예:

```text
- food
- transport
- salary
```

### 카테고리 삭제

```bash
python3 -m budget_app category remove
```

실행 예:

```text
삭제할 카테고리명: transport
[삭제 완료] category=transport
```

현재 거래에서 사용 중인 카테고리는 삭제할 수 없습니다.

예:

```text
[오류] 사용 중인 카테고리는 삭제할 수 없습니다: food
[힌트] 해당 카테고리를 사용하는 거래를 먼저 수정하거나 삭제해주세요.
```

---

## 7. 거래 추가

```bash
python3 -m budget_app add
```

대화형 방식으로 거래 정보를 입력합니다.

실행 예:

```text
날짜(YYYY-MM-DD): 2026-08-27
타입(income/expense): expense
카테고리: food
금액(양수): 15000
메모(선택): 점심
태그(쉼표 구분, 선택): meal

[저장 완료] id=TX-AB12CD34
```

거래 데이터는 `transactions.jsonl`에 영구 저장됩니다.

입력값 검증 항목:

- 날짜 형식
- 존재하지 않는 날짜
- `income` / `expense` 외 타입
- 0 이하의 금액
- 존재하지 않는 카테고리

---

## 8. 거래 목록 조회

```bash
python3 -m budget_app list
```

기본적으로 최근 거래 10개를 조회합니다.

조회 개수를 변경할 수 있습니다.

```bash
python3 -m budget_app list -limit 3
```

출력 예:

```text
TX-AB12CD34 | 2026-08-27 | expense | food | 15000 | 점심 | meal
TX-CD34EF56 | 2026-08-26 | income | salary | 3000000 | 월급 |
```

거래 목록은 최신순으로 출력됩니다.

파일 전체를 한 번에 메모리에 올리지 않고 Generator와 `yield`를 사용하여 스트리밍 방식으로 처리합니다.

---

## 9. 거래 검색

```bash
python3 -m budget_app search
```

다음 조건을 사용할 수 있습니다.

- `-from`
- `-to`
- `-category`
- `-type`
- `-q`
- `-tag`

기간 검색:

```bash
python3 -m budget_app search -from 2026-08-01 -to 2026-08-31
```

카테고리 검색:

```bash
python3 -m budget_app search -category food
```

타입 검색:

```bash
python3 -m budget_app search -type expense
```

메모 키워드 검색:

```bash
python3 -m budget_app search -q 점심
```

태그 검색:

```bash
python3 -m budget_app search -tag meal
```

여러 조건 검색:

```bash
python3 -m budget_app search -from 2026-08-01 -to 2026-08-31 -type expense -category food
```

검색 결과는 최신순으로 출력됩니다.

---

## 10. 거래 수정

본 프로그램은 대화형 수정 방식을 사용합니다.

```bash
python3 -m budget_app update -id TX-AB12CD34
```

실행 예:

```text
Enter를 누르면 기존 값을 유지합니다.

날짜 [2026-08-27]:
타입 [expense]:
카테고리 [food]:
금액 [15000]: 20000
메모 [점심]: 저녁
태그 [meal]:

[수정 완료] id=TX-AB12CD34
```

변경하지 않을 항목은 Enter를 누르면 기존 값이 유지됩니다.

존재하지 않는 ID를 입력하면 오류 메시지를 출력합니다.

```text
[오류] 존재하지 않는 거래입니다: TX-XXXXXXXX
```

---

## 11. 거래 삭제

```bash
python3 -m budget_app delete -id TX-AB12CD34
```

성공 예:

```text
[삭제 완료] id=TX-AB12CD34
```

존재하지 않는 ID를 삭제하면 오류를 출력합니다.

```text
[오류] 존재하지 않는 거래입니다: TX-XXXXXXXX
```

수정 및 삭제 시 원본 파일에 직접 덮어쓰지 않고 임시 파일에 먼저 저장한 뒤 `os.replace()`를 이용하여 원본 파일과 교체합니다.

이를 통해 파일 저장 과정에서 발생할 수 있는 데이터 손상 가능성을 줄였습니다.

---

## 12. 예산 설정

월별 예산을 설정할 수 있습니다.

```bash
python3 -m budget_app budget set -month 2026-08 -amount 500000
```

출력 예:

```text
[저장 완료] 2026-08 예산 500000원
```

예산 정보는 `budgets.jsonl` 파일에 영구 저장됩니다.

---

## 13. 월별 요약

```bash
python3 -m budget_app summary -month 2026-08
```

카테고리별 지출 상위 개수를 설정할 수 있습니다.

```bash
python3 -m budget_app summary -month 2026-08 -top 3
```

출력 예:

```text
총 수입: 3000000원
총 지출: 215000원
잔액: 2785000원
예산: 500000원 (사용률 43.0%)

지출 TOP 3
1) food 150000원
2) transport 45000원
3) hobby 20000원
```

예산을 초과한 경우 다음과 같은 경고를 출력합니다.

```text
[경고] 예산을 초과했습니다.
```

해당 월에 거래가 없는 경우:

```text
[안내] 해당 월의 데이터가 없습니다.
```

라고 출력합니다.

---

## 14. CSV Import

CSV 파일의 거래 데이터를 프로그램으로 가져올 수 있습니다.

```bash
python3 -m budget_app import -from import.csv
```

출력 예:

```text
[완료] imported=5, skipped=0
```

정상적인 데이터는 추가되고 잘못된 데이터는 `skipped`로 처리됩니다.

---

## 15. CSV Export

특정 월 데이터를 CSV 파일로 저장할 수 있습니다.

```bash
python3 -m budget_app export -out export.csv -month 2026-08
```

기간 조건으로도 저장할 수 있습니다.

```bash
python3 -m budget_app export -out export.csv -from 2026-08-01 -to 2026-08-31
```

출력 예:

```text
[완료] export.csv (12 records)
```

Export 시에는 `-month` 또는 `-from/-to` 조건 중 하나 이상을 입력해야 합니다.

---

# CSV 스키마

Import와 Export에서 사용하는 CSV는 UTF-8 및 헤더 포함 형식을 사용합니다.

| column   | required | 설명                |
| -------- | -------- | ------------------- |
| date     | Y        | YYYY-MM-DD          |
| type     | Y        | income / expense    |
| category | Y        | 등록된 카테고리     |
| amount   | Y        | 양수 정수           |
| memo     | N        | 문자열              |
| tags     | N        | 쉼표(,) 구분 문자열 |

예:

```csv
date,type,category,amount,memo,tags
2026-08-27,expense,food,15000,점심,meal
2026-08-27,income,salary,3000000,월급,income
```

---

# 주요 구현 특징

## 16. dataclass

거래 데이터는 `Transaction` dataclass로 정의했습니다.

거래 데이터에 필요한 필드는 다음과 같습니다.

- id
- type
- date
- amount
- category
- memo
- tags

이를 통해 거래 데이터의 구조를 명확하게 표현했습니다.

---

## 17. Type Hint

함수의 매개변수와 반환값에 Type Hint를 적용했습니다.

예:

```python
def get_budget(self, month: str) -> int | None:
```

이를 통해 함수가 어떤 데이터를 입력받고 어떤 값을 반환하는지 명확하게 표현했습니다.

---

## 18. Generator

거래 목록과 검색 처리 시 파일 전체를 한 번에 메모리에 올리지 않도록 Generator를 사용했습니다.

예:

```python
def iter_transactions(self):
    for line in file:
        yield Transaction.from_dict(data)
```

`yield`를 사용하면 대용량 파일에서도 한 번에 모든 데이터를 메모리에 저장하지 않고 한 건씩 처리할 수 있습니다.

---

## 19. Decorator

공통 예외 처리를 `handle_errors` 데코레이터로 분리했습니다.

이를 통해 각 기능에서 반복적으로 작성해야 하는 예외 처리 코드를 줄이고 핵심 기능과 오류 처리 로직을 분리했습니다.

사용 예:

```python
@handle_errors
def run() -> int:
    ...
```

---

## 20. 오류 처리

사용자에게 Python 스택트레이스를 직접 출력하지 않고 원인과 해결 방법을 안내하도록 구현했습니다.

예:

```text
[오류] 날짜 형식이 올바르지 않습니다.
[힌트] YYYY-MM-DD 형식으로 입력해주세요. 예: 2026-08-27
```

정상 종료 시 exit code는 `0`을 사용하고 오류 발생 시 `0`이 아닌 값을 반환합니다.

---

## 21. 데이터 안전성

거래 수정 및 삭제 시 원본 JSONL 파일을 바로 수정하지 않습니다.

다음 방식으로 처리합니다.

```text
원본 파일 읽기
↓
임시 파일 생성
↓
수정된 데이터 작성
↓
정상 저장 완료
↓
os.replace()로 원본 파일 교체
```

이 방식을 통해 파일 수정 도중 오류가 발생했을 때 원본 데이터가 손상될 가능성을 줄였습니다.

---

## 22. 카테고리 데이터 무결성

거래에서 사용 중인 카테고리는 바로 삭제할 수 없도록 구현했습니다.

예를 들어 `food` 카테고리를 사용하는 거래가 존재한다면:

```text
[오류] 사용 중인 카테고리는 삭제할 수 없습니다: food
```

라고 출력하여 기존 거래가 존재하지 않는 카테고리를 참조하는 문제를 방지합니다.

---

# 테스트 예시

## 카테고리 생성

```bash
python3 -m budget_app category add
```

```text
카테고리명: food
```

```bash
python3 -m budget_app category add
```

```text
카테고리명: salary
```

---

## 지출 추가

```bash
python3 -m budget_app add
```

```text
날짜(YYYY-MM-DD): 2026-08-27
타입(income/expense): expense
카테고리: food
금액(양수): 15000
메모(선택): 점심
태그(쉼표 구분, 선택): meal
```

---

## 수입 추가

```bash
python3 -m budget_app add
```

```text
날짜(YYYY-MM-DD): 2026-08-27
타입(income/expense): income
카테고리: salary
금액(양수): 3000000
메모(선택): 월급
태그(쉼표 구분, 선택): income
```

---

## 목록 확인

```bash
python3 -m budget_app list -limit 10
```

---

## 예산 설정

```bash
python3 -m budget_app budget set -month 2026-08 -amount 500000
```

---

## 월별 요약

```bash
python3 -m budget_app summary -month 2026-08 -top 3
```

---

## 검색

```bash
python3 -m budget_app search -category food
```

---

## CSV Export

```bash
python3 -m budget_app export -out export.csv -month 2026-08
```

---

## CSV 확인

macOS/Linux:

```bash
cat export.csv
```

---

# 실행 전 문법 검사

프로그램을 실행하기 전에 전체 Python 파일의 문법 오류를 확인할 수 있습니다.

```bash
python3 -m compileall budget_app
```

정상적으로 컴파일되면 각 Python 파일에 대해 다음과 비슷한 결과가 출력됩니다.

```text
Listing 'budget_app'...
Compiling 'budget_app/__init__.py'...
Compiling 'budget_app/__main__.py'...
Compiling 'budget_app/cli.py'...
Compiling 'budget_app/decorators.py'...
Compiling 'budget_app/models.py'...
Compiling 'budget_app/repository.py'...
Compiling 'budget_app/service.py'...
```

오류 메시지가 출력되지 않으면 기본적인 Python 문법 검사가 정상적으로 완료된 것입니다.

문법 오류가 있다면 파일명과 오류가 발생한 줄 번호가 출력되므로 해당 부분을 수정한 뒤 다시 검사합니다.

---

# 최종 실행 확인

문법 검사가 끝난 뒤 다음 명령어로 프로그램이 정상 실행되는지 확인합니다.

```bash
python3 -m budget_app
```

정상적으로 실행되면 사용할 수 있는 명령어 목록이 출력됩니다.

```text
add
list
search
summary
budget
category
update
delete
import
export
```

데이터 저장 파일도 확인합니다.

```bash
ls data
```

정상적인 경우 다음 세 파일이 존재합니다.

```text
budgets.jsonl
categories.jsonl
transactions.jsonl
```

프로그램 종료 후 다시 실행했을 때에도 기존 데이터가 유지되는지 확인합니다.

---

# 최종 기능 확인 목록

제출 전 다음 기능을 확인합니다.

- 거래 추가 `add`
- 거래 목록 `list`
- 거래 검색 `search`
- 월별 요약 `summary`
- 월 예산 설정 `budget`
- 카테고리 추가/조회/삭제 `category`
- 거래 수정 `update`
- 거래 삭제 `delete`
- CSV 가져오기 `import`
- CSV 내보내기 `export`
- JSONL 파일 영구 저장
- Generator와 `yield` 적용
- Decorator 적용
- dataclass 적용
- Type Hint 적용
- 입력값 검증
- 오류 메시지 및 해결 힌트 출력
- 사용 중인 카테고리 삭제 방지
- update/delete 임시 파일 교체
- `-help` 도움말 제공
- 정상 종료 코드 0
- 오류 종료 코드 0이 아닌 값
- Python 표준 라이브러리만 사용

---
