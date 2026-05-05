# 2026-1 OSSPrac ROOT

26-1 오픈소스소프트웨어실습 레포지토리입니다.

## 프로젝트 구성

```text
.
├── Subject3_1/
│   ├── ex4.py
│   └── templates/
│       ├── input.html
│       └── result.html
└── Subject3_2/
    ├── team.py
    ├── requirements.txt
    ├── data/
    │   └── members.json
    ├── templates/
    └── static/
```

## Subject3_1

- 이름, 학번, 성별, 전공, 사용 언어 입력
- 결과 페이지에서 입력값 표 형태로 출력

### 실행 방법

```bash
cd Subject3_1
python ex4.py
```

접속 주소:

```text
http://127.0.0.1:5000
```

## Subject3_2

ROOT 팀 소개 및 팀 페이지 생성 웹 애플리케이션입니다.

### 주요 기능

- ROOT 팀 소개 페이지
- ROOT 팀원 상세 페이지
- 비상연락망 페이지
- 팀 페이지 생성 기능
    - 팀명, 팀 소개, 팀 이미지 입력
    - 최대 4명의 팀원 정보 입력
    - 프로필 이미지
    - 포트폴리오
    - 포트폴리오 링크 및 파일 첨부
    - 팀원 상세 페이지 PDF 저장

### 실행 방법

```bash
cd Subject3_2
pip install -r requirements.txt
python team.py
```

접속 주소:

```text
http://127.0.0.1:5000
```

## 주요 라우트

| Route | Description |
| --- | --- |
| `/` | ROOT 팀 소개 메인 페이지 |
| `/input` | 팀 페이지 생성 및 팀원 입력 페이지 |
| `/input?member_id=<id>` | 생성 팀원 수정 페이지 |
| `/member/update` | 팀/팀원 정보 저장 및 수정 처리 |
| `/result` | 생성한 팀 페이지 결과 |
| `/members/<id>` | ROOT 또는 생성 팀원 상세 페이지 |
| `/contact` | ROOT 팀원 연락처 페이지 |
| `/reset` | 생성 중인 팀 정보 초기화 |

## 데이터

ROOT 팀과 ROOT 팀원 정보는 아래 JSON 파일에서 관리합니다.

```text
Subject3_2/data/members.json
```

사용자가 생성한 팀 정보는 Flask session에 저장됩니다.

## 업로드 파일

업로드 파일은 `Subject3_2/static/uploads/` 하위에 저장됩니다.

- 프로필/팀 이미지: `static/uploads/`
- 포트폴리오 첨부 파일: `static/uploads/portfolio/`

지원하는 포트폴리오 첨부 파일 확장자:

```text
pdf, doc, docx, ppt, pptx, xls, xlsx, zip, png, jpg, jpeg, gif, webp
```

## 팀원

| 이름 | 학과 | 역할 |
| --- | --- | --- | 
| 오승현 | 교육학과 | 팀장, 프론트엔드 |
| 김유미 | 산업시스템공학과 | 백엔드 |
| 오지윤 | 경영정보학과 | 백엔드 |

## 기술 스택

- Python
- Flask
- Jinja2
- HTML
- CSS
