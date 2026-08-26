<!-- @format -->

## 18. Generator

거래 목록과 검색 처리 시 파일 전체를 한 번에 메모리에 올리지 않도록 Generator를 사용했습니다.

예:

```python
def iter_transactions(self):
    for line in file:
        yield Transaction.from_dict(data)
```

`yield`를 사용하면 대용량 파일에서도 모든 데이터를 한 번에 메모리에 저장하지 않고 한 건씩 처리할 수 있습니다.

---

### 대용량 데이터 처리와 예상 병목 분석

본 프로그램은 `yield` 기반 Generator를 이용하여 거래 파일 전체를 한 번에 메모리에 올리지 않습니다.

따라서 거래가 100,000건 이상으로 증가하더라도 모든 `Transaction` 객체를 동시에 메모리에 생성하는 방식보다 메모리 사용량을 줄일 수 있습니다.

하지만 Generator를 사용하는 것만으로 모든 성능 문제가 해결되는 것은 아닙니다.

100,000건 이상의 거래가 저장되었을 경우 다음과 같은 병목이 예상됩니다.

#### 1. 디스크 I/O

`search`, `summary` 기능은 조건에 맞는 데이터를 찾기 위해 거래 파일의 많은 부분을 읽어야 합니다.

데이터가 많아질수록 디스크에서 읽어야 하는 데이터의 양도 증가하므로 실행 시간이 증가할 수 있습니다.

현재 구조에서 전체 검색의 시간 복잡도는 거래 건수를 `N`이라고 할 때 기본적으로 다음과 같습니다.

```text
O(N)
```

즉, 거래가 100,000건 존재한다면 조건에 따라 최대 100,000건의 거래를 확인해야 합니다.

#### 2. JSON 파싱 비용

JSONL 파일의 각 줄은 `json.loads()`를 이용하여 Python 데이터로 변환합니다.

거래 건수가 증가하면 파일 읽기뿐만 아니라 JSON 파싱 횟수도 증가합니다.

```text
파일 읽기
↓
json.loads()
↓
dictionary
↓
Transaction 객체 생성
```

따라서 대용량 데이터에서는 디스크 I/O와 JSON 파싱 비용이 함께 증가할 수 있습니다.

#### 3. 역순 조회 비용

`list`와 `search`의 최신순 처리를 위해 거래 파일을 뒤에서부터 읽는 방식을 사용합니다.

예:

```bash
python3 -m budget_app list -limit 10
```

최근 일부 거래만 조회하는 경우에는 필요한 거래를 찾은 뒤 처리를 종료할 수 있어 효율적입니다.

하지만 검색 조건에 따라 전체 거래를 확인해야 하는 경우에는 결국 많은 데이터를 읽어야 하므로 실행 시간이 증가할 수 있습니다.

#### 4. 월별 Summary 집계 비용

월별 요약에서는 거래 데이터를 순회하며 다음 내용을 계산합니다.

- 총 수입
- 총 지출
- 잔액
- 카테고리별 지출 합계
- 지출 TOP N

현재 구조에서는 `summary`를 실행할 때마다 거래 파일을 다시 읽어 계산합니다.

따라서 같은 월의 요약을 반복해서 실행하면 동일한 계산을 반복하는 문제가 발생할 수 있습니다.

---

### 대용량 데이터 개선 방법

데이터 규모가 더 커질 경우 다음과 같은 방법으로 개선할 수 있습니다.

#### 1. 인덱스 파일 추가

날짜, 월, 카테고리 등의 거래 위치를 별도의 인덱스 파일에 저장할 수 있습니다.

예:

```text
indexes/
├── month_index.json
├── category_index.json
└── date_index.json
```

예를 들어 `2026-08`에 해당하는 거래의 위치를 별도로 관리하면 월별 요약 시 전체 거래 파일을 순차적으로 확인하지 않고 필요한 범위만 조회할 수 있습니다.

#### 2. 월별 집계 캐시

월별 요약 결과를 별도의 파일로 저장할 수 있습니다.

예:

```text
summary_cache.json
```

거래가 추가, 수정, 삭제되었을 때 해당 월의 요약 데이터만 갱신하면 `summary` 실행 시 거래 전체를 다시 집계하는 비용을 줄일 수 있습니다.

#### 3. 배치 처리

CSV Import처럼 많은 데이터를 처리하는 기능은 일정 건수 단위로 나누어 처리할 수 있습니다.

예:

```text
1 ~ 1,000건
1,001 ~ 2,000건
2,001 ~ 3,000건
...
```

이를 통해 한 번에 처리하는 데이터의 크기를 제한하고 처리 상태도 단계별로 확인할 수 있습니다.

#### 4. chunk_size 조정

역순 파일 읽기에서는 일정 크기의 데이터를 블록 단위로 읽습니다.

현재 기본값:

```python
chunk_size = 8192
```

약 8KB씩 읽도록 설정되어 있습니다.

실제 데이터 규모에 따라 다음 크기를 비교할 수 있습니다.

```text
8KB
16KB
32KB
64KB
```

`chunk_size`가 너무 작으면 디스크 읽기 요청 횟수가 증가하고, 너무 크면 한 번에 사용하는 메모리가 증가합니다.

따라서 실제 실행 시간을 측정하여 적절한 값을 선택할 수 있습니다.

#### 5. 데이터베이스 전환

거래 데이터가 지속적으로 증가하고 검색 조건이 복잡해진다면 파일 기반 저장보다 SQLite와 같은 데이터베이스를 사용하는 것이 효율적일 수 있습니다.

예를 들어 다음 항목에 인덱스를 적용할 수 있습니다.

```text
date
category
type
```

이를 통해 모든 데이터를 순차적으로 확인하지 않고 필요한 거래를 빠르게 조회할 수 있습니다.

다만 이번 과제에서는 파일 기반 저장과 Generator 스트리밍 처리의 원리를 학습하는 것이 목적이므로 JSONL 구조를 유지했습니다.

---

### 메모리와 실행시간의 Trade-off

전체 거래를 한 번에 메모리에 저장하면 다음과 같은 특징이 있습니다.

```text
전체 거래 파일 읽기
↓
모든 데이터를 메모리에 저장
↓
메모리 사용량 증가
↓
이미 로딩된 데이터 검색은 빠름
```

현재 Generator 방식은 다음과 같습니다.

```text
파일에서 한 건씩 읽기
↓
필요한 데이터만 처리
↓
메모리 사용량 감소
↓
반복 검색 시 파일 I/O 증가
```

따라서 현재 프로그램은 모든 데이터를 메모리에 저장하는 방식보다 메모리 효율성을 우선하도록 설계했습니다.

데이터 규모가 매우 커질 경우 다음과 같은 순서로 개선할 수 있습니다.

```text
Generator 스트리밍
↓
인덱스 파일
↓
월별 집계 캐시
↓
배치 처리
↓
필요한 경우 데이터베이스 전환
```

---

## 19. Decorator

공통 관심사를 핵심 기능과 분리하기 위해 Decorator를 사용했습니다.

본 프로그램에서는 다음과 같은 Decorator를 사용합니다.

- 예외 처리 Decorator
- 로그 기록 Decorator
- 실행시간 측정 Decorator

---

### 예외 처리 Decorator

`handle_errors` Decorator를 이용하여 여러 기능에서 반복적으로 필요한 예외 처리를 분리했습니다.

사용 예:

```python
@handle_errors
def run() -> int:
    ...
```

사용자에게 Python 스택트레이스를 직접 노출하지 않고 오류 원인과 해결 방법을 안내합니다.

예:

```text
[오류] 날짜 형식이 올바르지 않습니다.
[힌트] YYYY-MM-DD 형식으로 입력해주세요.
```

---

### 로그 기록 Decorator

`log_execution` Decorator는 주요 기능의 실행 결과를 로그 파일에 기록합니다.

로그 파일:

```text
logs/app.log
```

기록 내용:

- 실행 시각
- 함수 이름
- 성공 또는 실패 여부

예:

```text
2026-08-27T03:10:21.123456 | export_csv | SUCCESS
```

거래 금액, 메모, 태그 등의 실제 거래 데이터는 로그에 기록하지 않습니다.

---

### 실행시간 측정 Decorator

`measure_time` Decorator는 함수 실행 전후 시간을 측정하여 처리 시간을 확인할 수 있도록 합니다.

사용 예:

```python
@log_execution
@measure_time
def export_csv(...):
    ...
```

실행 예:

```text
[실행 시간] export_csv: 0.001234초
[완료] export.csv (5 records)
```

이를 통해 대량의 데이터를 Import 또는 Export할 때 처리 시간을 확인할 수 있습니다.

---

## 20. 오류 처리

사용자에게 Python 스택트레이스를 직접 출력하지 않고 원인과 해결 방법을 안내하도록 구현했습니다.

예:

```text
[오류] 날짜 형식이 올바르지 않습니다.
[힌트] YYYY-MM-DD 형식으로 입력해주세요. 예: 2026-08-27
```

예상하지 못한 내부 오류가 발생한 경우에도 내부 파일 경로나 상세 스택트레이스를 사용자에게 노출하지 않습니다.

예:

```text
[오류] 프로그램 실행 중 예상하지 못한 문제가 발생했습니다.
[힌트] 입력값과 데이터 파일 상태를 확인해주세요.
```

---

### 종료 코드 정책

프로그램은 실행 결과에 따라 종료 코드를 반환합니다.

| 종료 코드 | 의미                              |
| --------- | --------------------------------- |
| 0         | 정상 종료                         |
| 1         | 입력 검증 또는 프로그램 실행 오류 |
| 2         | CLI 명령어나 옵션 사용 오류       |

정상적인 실행은 종료 코드 `0`을 사용합니다.

입력값 검증 실패나 실행 중 오류가 발생한 경우에는 `0`이 아닌 종료 코드를 사용합니다.

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

이를 통해 파일 수정 중 오류가 발생했을 때 원본 데이터가 손상될 가능성을 줄였습니다.

임시 파일 작성 중 오류가 발생하면 임시 파일을 삭제하고 기존 원본 파일을 유지합니다.

---

### 파일 교체 실패 시 개선 방안

현재는 임시 파일 작성과 `os.replace()`를 이용하여 데이터 안전성을 확보하고 있습니다.

향후에는 다음과 같은 백업 절차를 추가할 수 있습니다.

```text
transactions.jsonl
↓
transactions.backup.jsonl 생성
↓
임시 파일 작성
↓
os.replace()

성공
→ backup 삭제

실패
→ backup 파일 복구
```

이를 통해 디스크 공간 부족이나 파일 시스템 오류 등으로 파일 교체가 실패한 경우에도 데이터를 복구할 수 있도록 개선할 수 있습니다.

---

## 22. 카테고리 데이터 무결성

거래에서 사용 중인 카테고리는 바로 삭제할 수 없도록 구현했습니다.

예를 들어 `food` 카테고리를 사용하는 거래가 존재한다면 다음과 같이 처리합니다.

```text
[오류] 사용 중인 카테고리는 삭제할 수 없습니다: food
[힌트] 해당 카테고리를 사용하는 거래를 먼저 수정하거나 삭제해주세요.
```

이를 통해 기존 거래가 존재하지 않는 카테고리를 참조하게 되는 문제를 방지합니다.

현재는 사용 중인 카테고리의 삭제를 차단하는 정책을 사용합니다.

향후에는 사용자가 삭제할 카테고리 대신 대체 카테고리를 지정할 수 있도록 개선할 수 있습니다.

---

## 23. CSV 호환 및 Import 정책

CSV Import는 컬럼의 실제 위치가 아니라 헤더 이름을 기준으로 데이터를 읽습니다.

따라서 다음과 같이 컬럼 순서가 변경되어도 필수 헤더 이름이 존재하면 처리할 수 있습니다.

```csv
date,type,category,amount,memo,tags
```

다음 형식도 처리 가능합니다.

```csv
amount,category,type,date,memo,tags
```

필수 컬럼:

- `date`
- `type`
- `category`
- `amount`

선택 컬럼:

- `memo`
- `tags`

현재는 컬럼 이름의 별칭이나 여러 버전의 CSV 스키마를 자동 변환하는 기능은 제공하지 않습니다.

---

### Import 부분 적용 정책

현재 CSV Import는 부분 적용 방식으로 동작합니다.

```text
정상 행
→ 거래 저장

잘못된 행
→ skipped 처리
```

예:

```text
[완료] imported=5, skipped=2
```

즉, 일부 행에 오류가 있어도 정상적인 행은 저장됩니다.

현재는 하나의 행에서 오류가 발생하면 전체 Import를 취소하는 완전 롤백 방식은 사용하지 않습니다.

향후 다음과 같은 `-atomic` 옵션을 추가할 수 있습니다.

```bash
python3 -m budget_app import -from import.csv -atomic
```

Atomic 방식에서는:

```text
모든 데이터 정상
→ 전체 저장

하나 이상의 오류 발생
→ 전체 Import 취소
```

방식으로 개선할 수 있습니다.

---

## 24. 클래스별 책임

### Transaction

거래 한 건의 데이터 구조를 표현합니다.

관리하는 데이터는 다음과 같습니다.

- id
- type
- date
- amount
- category
- memo
- tags

`dataclass`를 사용하여 거래 데이터의 구조를 명확하게 정의했습니다.

또한 객체와 dictionary 간 변환을 담당합니다.

---

### DataRepository

JSONL 파일에 접근하는 저장소 역할을 담당합니다.

주요 역할:

- 데이터 폴더 생성
- 거래 파일 읽기/쓰기
- 카테고리 파일 읽기/쓰기
- 예산 파일 읽기/쓰기
- Generator 기반 스트리밍
- 최신순 거래 읽기
- 임시 파일 작성
- `os.replace()`를 이용한 안전한 파일 교체

비즈니스 로직이나 사용자 입력 처리는 담당하지 않습니다.

---

### BudgetService

가계부의 비즈니스 로직을 담당합니다.

주요 역할:

- 거래 추가
- 거래 검색
- 거래 수정
- 거래 삭제
- 날짜 검증
- 거래 타입 검증
- 금액 검증
- 카테고리 검증
- 카테고리 관리
- 예산 설정
- 월별 요약
- CSV Import
- CSV Export

---

### CLI

사용자가 입력한 명령어와 옵션을 처리합니다.

주요 역할:

- 명령어 분석
- 옵션 분석
- 대화형 사용자 입력
- BudgetService 호출
- 결과 출력
- 종료 코드 반환

---

## 25. 모듈 간 의존 관계

프로그램은 다음과 같은 계층 구조로 구성했습니다.

```text
사용자
  │
  ▼
cli.py
  │
  ▼
service.py
  │
  ▼
repository.py
  │
  ▼
JSONL 파일
```

데이터 모델은 다음과 같이 사용합니다.

```text
models.py
   ▲
   │
service.py
repository.py
```

공통 기능은 별도 Decorator 모듈에서 관리합니다.

```text
decorators.py
   ▲
   │
cli.py
service.py
```

전체적인 구조는 다음과 같습니다.

```text
CLI
↓
Service
↓
Repository
↓
File
```

이를 통해 사용자 인터페이스, 비즈니스 로직, 데이터 저장 로직의 책임을 분리했습니다.

---

# 테스트 예시

## 카테고리 생성

```bash
python3 -m budget_app category add
```

입력:

```text
카테고리명: food
```

다른 카테고리 추가:

```bash
python3 -m budget_app category add
```

입력:

```text
카테고리명: salary
```

---

## 지출 추가

```bash
python3 -m budget_app add
```

입력 예:

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

입력 예:

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

## 검색

```bash
python3 -m budget_app search -category food
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

## 로그 확인

로그 Decorator가 적용된 기능을 실행한 뒤 로그 파일을 확인합니다.

```bash
cat logs/app.log
```

출력 예:

```text
2026-08-27T03:10:21.123456 | export_csv | SUCCESS
```

---

# 실행 전 문법 검사

프로그램 실행 전에 전체 Python 파일의 문법 오류를 확인합니다.

```bash
python3 -m compileall budget_app
```

정상적으로 실행되면 다음과 비슷한 결과가 출력됩니다.

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

문법 검사가 끝난 뒤 프로그램을 실행합니다.

```bash
python3 -m budget_app
```

정상적으로 실행되면 사용할 수 있는 주요 명령어가 출력됩니다.

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

데이터 파일도 확인합니다.

```bash
ls data
```

정상적인 경우 다음 세 파일이 존재합니다.

```text
budgets.jsonl
categories.jsonl
transactions.jsonl
```

프로그램을 종료한 뒤 다시 실행했을 때 기존 거래, 카테고리, 예산 데이터가 유지되는지도 확인합니다.
