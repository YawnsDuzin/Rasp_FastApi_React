# Raspberry Pi HMI (Human-Machine Interface) 시스템

## 프로젝트 개요

라즈베리파이 기반의 실시간 웹 HMI(Human-Machine Interface) 시스템입니다.
FastAPI 백엔드와 React 프론트엔드를 사용하여 하드웨어 제어 및 모니터링을 제공합니다.

### 주요 기능

- **실시간 하드웨어 모니터링**: WebSocket을 통한 실시간 데이터 푸시
- **다양한 하드웨어 지원**: GPIO, PWM, I2C, SPI 인터페이스
- **시스템 리소스 모니터링**: CPU, 메모리, 디스크, 온도
- **데이터 로깅**: SQLite (WAL 모드) 기반 SD 카드 수명 보호
- **시뮬레이션 모드**: 실제 하드웨어 없이 개발 가능
- **반응형 UI**: 다크 모드 지원, 모바일/태블릿/데스크톱 대응

---

## 문서 구조

| 문서 | 설명 |
|------|------|
| [시스템 아키텍처](./ARCHITECTURE.md) | 3계층 아키텍처, 기술 스택, 설계 원칙 |
| [Frontend-Backend 연동](./INTEGRATION.md) | 프론트엔드-백엔드 통신 및 데이터 흐름 상세 |
| [백엔드 가이드](./BACKEND.md) | FastAPI 백엔드 개발 가이드 |
| [프론트엔드 가이드](./FRONTEND.md) | React 프론트엔드 개발 가이드 |
| [하드웨어 가이드](./HARDWARE.md) | 지원 하드웨어 및 배선 가이드 |
| [API 레퍼런스](./API.md) | REST API 및 WebSocket 엔드포인트 |
| [배포 가이드](./DEPLOYMENT.md) | 설치, 서비스 설정, 문제 해결 |

---

## 빠른 시작

### 1. 설치

```bash
# 프로젝트 클론
git clone <repository-url>
cd Rasp_FastApi_React

# 설치 스크립트 실행 (라즈베리파이에서)
sudo ./scripts/install.sh
```

### 2. 실행

```bash
# 개발 모드 실행
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 또는 서비스로 실행
sudo ./scripts/install-service.sh
```

### 3. 접속

브라우저에서 `http://<라즈베리파이-IP>:8000` 접속

---

## 시스템 요구사항

### 하드웨어
- Raspberry Pi 3B+ / 4B / 5 (권장)
- 마이크로SD 카드 16GB 이상
- 전원 공급 장치 (5V 3A 권장)

### 소프트웨어
- Raspberry Pi OS (Bookworm 이상 권장)
- Python 3.9+
- Node.js 18+
- npm 9+

---

## 프로젝트 구조

```
Rasp_FastApi_React/
├── backend/                 # FastAPI 백엔드
│   ├── app/
│   │   ├── api/            # API 라우트
│   │   ├── core/           # 설정, 로깅
│   │   ├── hardware/       # 하드웨어 컨트롤러
│   │   ├── models/         # 데이터베이스 모델
│   │   ├── services/       # 비즈니스 로직
│   │   └── main.py         # 애플리케이션 엔트리포인트
│   ├── data/               # SQLite 데이터베이스
│   ├── logs/               # 애플리케이션 로그
│   └── static/             # React 빌드 파일
├── frontend/               # React 프론트엔드
│   ├── src/
│   │   ├── components/     # UI 컴포넌트
│   │   ├── hooks/          # 커스텀 훅
│   │   ├── pages/          # 페이지 컴포넌트
│   │   ├── services/       # API/WebSocket 서비스
│   │   └── types/          # TypeScript 타입 정의
│   └── package.json
├── scripts/                # 배포 스크립트
│   ├── install.sh
│   ├── install-service.sh
│   └── setup-kiosk.sh
├── docs/                   # 문서
└── config/                 # 설정 파일
```

---

## 라이선스

MIT License

---

## 기여

이슈 및 풀 리퀘스트를 환영합니다.
