<!-- @format -->

# 파일 기반 가계부 콘솔 프로그램

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

## 4. 공통 관심사 분리

본 프로그램은 예외 처리, 로그 기록, 실행시간 측정을 핵심 비즈니스 로직과 분리하기 위해 데코레이터를 사용합니다.

이를 통해 동일한 기능이 여러 함수에 반복되는 것을 줄이고, 각 함수가 자신의 주요 역할에 집중할 수 있도록 구성했습니다.

### 예외 처리 데코레이터

`handle_errors` 데코레이터는 프로그램 실행 중 발생하는 오류를 공통으로 처리합니다.

Python 스택트레이스를 사용자에게 그대로 출력하지 않고 오류 원인과 해결 힌트를 제공합니다.

사용 예:

```python
@handle_errors
def run() -> int:
    ...
```

출력 예:

```text
[오류] 날짜 형식이 올바르지 않습니다.
[힌트] YYYY-MM-DD 형식으로 입력해주세요.
```

### 로그 기록 데코레이터

`log_execution` 데코레이터는 주요 기능의 실행 정보를 로그 파일에 기록합니다.

로그 저장 위치:

```text
logs/app.log
```

기록하는 정보는 다음과 같습니다.

- 실행 시각
- 실행 함수명
- 성공 또는 실패 여부

로그 예:

```text
2026-08-27T03:10:21.123456 | export_csv | SUCCESS
```

거래 금액, 메모, 태그 등의 실제 거래 내용은 로그에 저장하지 않습니다.

### 실행시간 측정 데코레이터

`measure_time` 데코레이터는 함수 실행 전후의 시간을 측정합니다.

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

이를 통해 import/export와 같은 파일 처리 기능의 실행 시간을 확인할 수 있습니다.

---

## 5. JSONL 저장 방식을 선택한 이유

본 프로그램의 내부 영구 저장 방식으로 JSONL을 선택했습니다.

JSONL과 CSV는 모두 한 행 단위로 데이터를 저장할 수 있지만 데이터 구조와 활용 목적에 차이가 있습니다.

| 구분             | JSONL                          | CSV                          |
| ---------------- | ------------------------------ | ---------------------------- |
| 데이터 구조      | JSON 객체 단위                 | 행과 열 구조                 |
| 레코드 추가      | 한 줄 단위 append가 쉬움       | 한 행 단위 추가 가능         |
| 숫자/문자 구분   | 자료형 표현이 비교적 명확함    | 주로 문자열 기반             |
| 리스트 데이터    | 배열 형태로 저장 가능          | 별도 문자열 변환 필요        |
| tags 표현        | JSON 배열 사용 가능            | 쉼표 문자열 등으로 변환 필요 |
| Python 객체 변환 | dict/dataclass와 변환하기 쉬움 | 컬럼별 변환 필요             |
| 스트리밍 처리    | 한 줄씩 처리 가능              | 한 행씩 처리 가능            |
| Excel 호환성     | 상대적으로 낮음                | 높음                         |

본 프로그램의 거래 데이터에는 `tags`와 같이 여러 값을 저장할 수 있는 필드가 존재합니다.

예:

```json
{
  "id": "TX-AB12CD34",
  "type": "expense",
  "date": "2026-08-27",
  "amount": 15000,
  "category": "food",
  "memo": "점심",
  "tags": ["meal", "food"]
}
```

JSONL에서는 `tags`를 리스트 형태로 자연스럽게 저장할 수 있습니다.

또한 `Transaction` dataclass를 dictionary로 변환한 뒤 JSON 객체로 바로 저장할 수 있어 데이터 모델과 저장 데이터 간 변환이 단순합니다.

거래 추가 시에도 기존 파일 전체를 다시 작성하지 않고 다음과 같이 한 줄을 추가할 수 있습니다.

```text
기존 데이터
기존 데이터
새로운 거래 ← append
```

Generator를 이용해 한 줄씩 읽을 수 있기 때문에 스트리밍 처리에도 적합합니다.

반면 CSV는 Excel 등의 외부 프로그램과 데이터 교환에 더 유리합니다.

따라서 본 프로그램에서는 다음과 같이 역할을 분리했습니다.

```text
JSONL
→ 프로그램 내부 영구 저장

CSV
→ 외부 데이터 import/export
```

---

## 6. 대용량 데이터 처리

본 프로그램은 거래 데이터를 읽을 때 `yield` 기반 Generator를 사용합니다.

일반적인 전체 로딩 방식에서는 다음과 같이 모든 거래 데이터를 메모리에 저장하게 됩니다.

```text
transactions.jsonl
↓
전체 파일 읽기
↓
list에 모든 Transaction 저장
↓
처리
```

데이터가 많아질수록 메모리 사용량도 증가합니다.

본 프로그램에서는 다음 방식으로 처리합니다.

```text
transactions.jsonl
↓
한 줄 읽기
↓
Transaction 생성
↓
처리
↓
다음 한 줄 읽기
```

즉 필요한 데이터를 한 건씩 처리하기 때문에 전체 파일을 한 번에 메모리에 저장하지 않습니다.

---

## 7. 100,000건 이상 데이터에서 예상되는 병목

Generator를 사용하면 메모리 사용량을 줄일 수 있지만 데이터가 매우 많아지면 다른 성능 문제가 발생할 수 있습니다.

### 디스크 I/O

`search` 또는 `summary`를 실행하면 조건에 맞는 데이터를 찾기 위해 거래 파일의 많은 부분을 읽어야 합니다.

현재 검색 구조는 거래 개수를 `N`이라고 하면 기본적으로 다음과 같은 시간 복잡도를 가집니다.

```text
O(N)
```

예를 들어 거래가 100,000건 존재한다면 조건에 따라 최대 100,000건을 확인해야 합니다.

데이터 규모가 증가할수록 디스크에서 읽어야 하는 데이터량도 증가하여 실행시간이 길어질 수 있습니다.

### JSON 파싱 비용

JSONL의 한 줄을 읽을 때마다 다음 처리가 이루어집니다.

```text
파일 읽기
↓
json.loads()
↓
dictionary
↓
Transaction 객체
```

따라서 거래 수가 많아질수록 JSON 파싱 작업도 증가합니다.

### 역순 파일 조회 비용

최신 거래를 빠르게 조회하기 위해 거래 파일을 뒤쪽부터 읽는 기능을 사용합니다.

예:

```bash
python3 -m budget_app list -limit 10
```

최근 10건만 조회하는 경우 파일 전체를 읽지 않아도 되므로 효율적입니다.

하지만 검색 조건에 따라 전체 거래를 확인해야 하는 경우에는 결국 많은 레코드를 처리해야 합니다.

### Summary 집계 비용

월별 요약에서는 거래를 읽으면서 다음 정보를 계산합니다.

```text
총 수입
총 지출
잔액
카테고리별 지출
지출 TOP N
```

현재 구조에서는 summary 명령을 실행할 때마다 거래 파일을 다시 순회합니다.

따라서 동일한 월의 summary를 반복 실행하면 동일한 계산이 반복됩니다.

---

## 8. 대용량 데이터 개선 방안

데이터가 100,000건 이상으로 증가할 경우 다음과 같은 개선 방법을 고려할 수 있습니다.

### 인덱스 파일 추가

날짜, 월, 카테고리 등의 위치 정보를 별도 파일로 관리할 수 있습니다.

예:

```text
indexes/
├── month_index.json
├── category_index.json
└── date_index.json
```

예를 들어 `2026-08`의 거래 위치를 별도 인덱스로 관리하면 summary 실행 시 전체 파일을 탐색하지 않고 필요한 데이터만 확인할 수 있습니다.

### 월별 집계 데이터 캐싱

월별 요약 결과를 별도 파일로 저장할 수 있습니다.

예:

```text
summary_cache.json
```

거래가 추가, 수정, 삭제되었을 때 해당 월의 데이터만 다시 계산합니다.

그러면 동일한 월의 summary를 반복 실행할 때 전체 거래를 다시 계산하지 않아도 됩니다.

### 배치 처리

CSV Import처럼 거래 데이터가 많은 경우 일정 개수 단위로 데이터를 나누어 처리할 수 있습니다.

예:

```text
1 ~ 1,000건
1,001 ~ 2,000건
2,001 ~ 3,000건
...
```

이를 통해 대량 작업의 진행 상태를 확인하기 쉽고 한 번에 처리하는 데이터 크기를 제한할 수 있습니다.

### chunk_size 조절

파일을 역순으로 읽을 때 일정 크기의 데이터를 한 번에 읽습니다.

현재 기본값:

```python
chunk_size = 8192
```

즉 약 8KB 단위로 파일을 읽습니다.

성능 측정 시 다음과 같은 크기를 비교할 수 있습니다.

```text
8KB
16KB
32KB
64KB
```

chunk size가 작으면 파일 읽기 요청 횟수가 증가하고, 너무 크면 한 번에 사용하는 메모리가 증가합니다.

따라서 실제 데이터 규모와 환경에 따라 적절한 값을 선택할 수 있습니다.

### 데이터베이스 전환

거래 데이터가 계속 증가하고 복잡한 검색이 많아진다면 파일 기반 방식보다 SQLite와 같은 데이터베이스가 더 적합할 수 있습니다.

예를 들어 다음 컬럼에 인덱스를 적용할 수 있습니다.

```text
date
category
type
```

이렇게 하면 전체 데이터를 순차 탐색하지 않고 필요한 데이터를 빠르게 찾을 수 있습니다.

다만 이번 과제에서는 파일 기반 저장과 Generator 스트리밍 처리를 학습하는 것이 주요 목적이므로 JSONL 구조를 유지했습니다.

---

## 9. 메모리와 실행시간의 Trade-off

전체 데이터를 메모리에 불러오면 다음과 같은 특징이 있습니다.

```text
전체 파일 로딩
↓
메모리 사용량 증가
↓
메모리에 존재하는 데이터 검색은 빠름
```

현재 Generator 방식은 다음과 같습니다.

```text
파일에서 한 건씩 읽기
↓
메모리 사용량 감소
↓
반복 검색 시 파일 I/O 증가
```

즉 본 프로그램은 실행 속도만을 우선하기보다 메모리 효율성과 대용량 파일 처리 가능성을 고려한 구조입니다.

데이터 규모가 매우 커질 경우 다음 순서로 개선할 수 있습니다.

```text
Generator
↓
인덱스 파일
↓
Summary 캐시
↓
배치 처리
↓
데이터베이스 전환
```

---

## 10. CSV 호환 정책

CSV Import에서는 컬럼의 위치가 아니라 헤더 이름을 기준으로 데이터를 읽습니다.

따라서 다음과 같이 컬럼의 순서가 변경되어도 필수 헤더 이름이 존재하면 처리할 수 있습니다.

예:

```csv
date,type,category,amount,memo,tags
```

다음 구조도 처리 가능합니다.

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

현재는 컬럼의 별칭이나 여러 버전의 CSV 스키마를 자동 변환하는 기능은 제공하지 않습니다.

향후 CSV 구조가 변경될 경우 다음과 같은 매핑 기능을 추가할 수 있습니다.

```text
transaction_date → date
transaction_type → type
price → amount
```

---

## 11. CSV Import 처리 정책

현재 Import는 부분 적용 방식을 사용합니다.

CSV에 정상 데이터와 오류 데이터가 함께 존재하는 경우:

```text
정상 데이터
→ 저장

잘못된 데이터
→ skipped
```

처리가 완료되면 다음과 같이 결과를 출력합니다.

```text
[완료] imported=5, skipped=2
```

현재는 한 행에서 오류가 발생했을 때 모든 데이터를 되돌리는 완전 롤백 방식은 적용하지 않았습니다.

향후 다음과 같은 옵션을 추가할 수 있습니다.

```bash
python3 -m budget_app import -from import.csv -atomic
```

Atomic 방식에서는:

```text
모든 데이터 정상
→ 전체 저장

1개 이상의 오류 발생
→ 전체 작업 취소
```

방식으로 개선할 수 있습니다.

---

## 12. 파일 교체 실패 및 복구 정책

거래 수정과 삭제에서는 원본 파일에 직접 데이터를 작성하지 않습니다.

현재 동작 방식:

```text
transactions.jsonl
↓
기존 거래 읽기
↓
임시 파일 생성
↓
수정된 내용 작성
↓
정상적으로 저장 완료
↓
os.replace()
↓
원본 파일 교체
```

임시 파일 작성 중 오류가 발생하면 임시 파일을 삭제하고 기존 원본 파일을 유지합니다.

하지만 디스크 공간 부족 또는 파일 시스템 문제로 `os.replace()`가 실패할 가능성도 있습니다.

향후 다음과 같이 백업 기능을 추가할 수 있습니다.

```text
transactions.jsonl
↓
transactions.backup.jsonl 생성
↓
임시 파일 생성
↓
새 데이터 작성
↓
os.replace()

성공
→ backup 삭제

실패
→ backup 파일 복원
```

이를 통해 파일 교체 과정에서 문제가 발생한 경우 복구 가능성을 높일 수 있습니다.

---

## 13. 종료 코드 정책

프로그램은 실행 결과에 따라 종료 코드를 반환합니다.

| 종료 코드 | 의미                              |
| --------- | --------------------------------- |
| 0         | 정상 종료                         |
| 1         | 입력 검증 또는 프로그램 실행 오류 |
| 2         | 잘못된 명령어나 옵션 사용         |

정상 실행 예:

```bash
python3 -m budget_app list
```

정상적으로 실행되면 종료 코드 `0`을 반환합니다.

입력값 검증에 실패하거나 프로그램 처리 중 오류가 발생하면 종료 코드 `1`을 반환합니다.

CLI 옵션을 잘못 입력한 경우에는 종료 코드 `2`를 사용합니다.

종료 코드를 통해 자동화 프로그램이나 쉘 스크립트에서도 실행 성공 여부를 확인할 수 있습니다.

---

## 14. 로그 및 민감정보 처리 정책

프로그램 내부에서 예상하지 못한 Exception이 발생하더라도 사용자 화면에는 상세 Python 스택트레이스를 출력하지 않습니다.

사용자에게는 다음과 같은 일반적인 오류 메시지를 제공합니다.

```text
[오류] 프로그램 실행 중 예상하지 못한 문제가 발생했습니다.
[힌트] 입력값과 데이터 파일 상태를 확인해주세요.
```

실행 로그에는 다음 정보만 기록합니다.

```text
실행 시각
함수 이름
성공/실패 여부
```

다음 정보는 로그에 기록하지 않습니다.

```text
거래 금액
메모 내용
태그 내용
CSV 원본 데이터
```

이를 통해 프로그램 상태 확인에 필요한 정보만 저장하도록 구성했습니다.

---

## 15. 클래스별 책임

### Transaction

거래 한 건의 데이터 구조를 표현하는 클래스입니다.

관리하는 데이터:

- id
- type
- date
- amount
- category
- memo
- tags

`dataclass`를 사용하여 거래 데이터의 구조를 명확하게 정의합니다.

또한 파일 저장을 위해 객체와 dictionary 사이의 변환을 담당합니다.

---

### DataRepository

JSONL 파일에 접근하는 저장소 클래스입니다.

주요 책임:

- 데이터 폴더 생성
- 거래 파일 읽기/쓰기
- 카테고리 파일 읽기/쓰기
- 예산 파일 읽기/쓰기
- Generator 기반 데이터 스트리밍
- 최신순 거래 읽기
- 임시 파일 작성
- `os.replace()`를 이용한 파일 교체

비즈니스 로직이나 사용자 입력 처리는 담당하지 않습니다.

---

### BudgetService

가계부의 비즈니스 로직을 담당하는 클래스입니다.

주요 책임:

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

사용자가 입력한 명령어를 처리합니다.

주요 책임:

- 명령어 분석
- 옵션 분석
- 대화형 사용자 입력
- BudgetService 호출
- 결과 출력
- 종료 코드 반환

파일 저장과 주요 비즈니스 계산은 직접 수행하지 않습니다.

---

## 16. 모듈 의존 관계

프로그램은 다음과 같은 계층 구조로 구성되어 있습니다.

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

데이터 모델은 다음 모듈에서 사용합니다.

```text
models.py
   ▲
   │
service.py
repository.py
```

공통 기능은 별도의 데코레이터 모듈로 분리했습니다.

```text
decorators.py
   ▲
   │
cli.py
service.py
```

전체적으로 다음 책임을 유지합니다.

```text
CLI
↓
Service
↓
Repository
↓
File
```

이를 통해 사용자 인터페이스, 비즈니스 로직, 저장 로직을 서로 분리했습니다.

---

## 17. 대용량 데이터 성능 측정 계획

향후 실제 성능을 검증할 경우 다음 규모의 테스트 데이터를 사용할 수 있습니다.

```text
1,000건
10,000건
100,000건
```

측정할 항목은 다음과 같습니다.

| 측정 항목  | 내용                              |
| ---------- | --------------------------------- |
| list       | 최신 N건 조회 시간                |
| search     | 조건 검색 실행시간                |
| summary    | 월별 집계 실행시간                |
| import     | CSV 대량 등록 시간                |
| export     | CSV 생성 시간                     |
| 메모리     | 대량 데이터 처리 중 메모리 사용량 |
| chunk_size | 파일 블록 크기에 따른 성능 차이   |

실행시간 측정 데코레이터를 이용하면 각 기능의 처리시간을 기록하여 비교할 수 있습니다.

---

## 18. 실행 로그 확인

로그 데코레이터가 적용된 기능을 실행합니다.

예:

```bash
python3 -m budget_app export -out export.csv -month 2026-08
```

실행 결과 예:

```text
[실행 시간] export_csv: 0.001234초
[완료] export.csv (5 records)
```

로그 확인:

```bash
cat logs/app.log
```

예:

```text
2026-08-27T03:10:21.123456 | export_csv | SUCCESS
```

---

## 19. 실행 전 문법 검사

프로그램을 실행하기 전에 전체 Python 파일에 문법 오류가 없는지 검사합니다.

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

문법 오류가 없으면 컴파일 오류 메시지가 출력되지 않습니다.

오류가 발생하면 오류가 발생한 파일명과 줄 번호를 확인하여 수정한 뒤 다시 실행합니다.

---

## 20. 최종 실행 확인

프로그램을 실행합니다.

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

정상적인 경우:

```text
budgets.jsonl
categories.jsonl
transactions.jsonl
```

카테고리 목록 확인:

```bash
python3 -m budget_app category list
```

거래 목록 확인:

```bash
python3 -m budget_app list -limit 10
```

예산 설정:

```bash
python3 -m budget_app budget set -month 2026-08 -amount 500000
```

월별 요약:

```bash
python3 -m budget_app summary -month 2026-08 -top 3
```

CSV Export:

```bash
python3 -m budget_app export -out export.csv -month 2026-08
```

로그 확인:

```bash
cat logs/app.log
```

---

## 21. Generator

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

## 22. Decorator

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

## 23. 오류 처리

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

## 24. 데이터 안전성

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

## 25. 카테고리 데이터 무결성

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

## 26. CSV 호환 및 Import 정책

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

## 27. 클래스별 책임

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

## 28. 모듈 간 의존 관계

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

## JSONL vs CSV 비교 및 선택 이유

본 프로그램은 내부 데이터 저장 형식으로 JSONL을 사용하고, CSV는 데이터 Import/Export 용도로 사용했습니다.

| 구분          | JSONL                       | CSV                      |
| ------------- | --------------------------- | ------------------------ |
| 데이터 구조   | JSON 객체 단위              | 행/열 형태               |
| 리스트 저장   | 배열 형태로 저장 가능       | 문자열 변환 필요         |
| 데이터 추가   | 한 줄씩 추가하기 편리       | 행 단위 추가 가능        |
| 스트리밍 처리 | 한 줄씩 읽기 편리           | 한 행씩 읽기 가능        |
| Python 연동   | dict, dataclass 변환이 편리 | 컬럼별 변환 필요         |
| 외부 호환성   | 상대적으로 낮음             | Excel 등과 호환성이 높음 |

### JSONL을 선택한 이유

거래 데이터에는 `tags`와 같은 리스트가 포함되어 있어 JSONL이 데이터 구조를 표현하기 편리합니다.

또한 거래 한 건을 한 줄씩 저장하기 때문에 Generator와 `yield`를 이용한 스트리밍 처리에 적합하며, 파일 전체를 메모리에 올리지 않고 데이터를 순차적으로 조회할 수 있습니다.

따라서 **내부 영구 저장은 JSONL**, Excel 등 외부 프로그램과 데이터를 주고받는 **Import/Export는 CSV**를 사용하도록 구성했습니다.
