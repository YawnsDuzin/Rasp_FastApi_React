# 배포 가이드

## 1. 사전 요구사항

### 1.1 하드웨어 요구사항

| 항목 | 최소 | 권장 |
|------|------|------|
| 라즈베리파이 | 3B | 4B / 5 |
| RAM | 1GB | 2GB+ |
| SD 카드 | 8GB | 16GB+ (Class 10) |
| 전원 | 5V 2.5A | 5V 3A (공식 어댑터) |

### 1.2 소프트웨어 요구사항

| 소프트웨어 | 최소 버전 | 확인 명령 |
|-----------|----------|----------|
| Raspberry Pi OS | Bullseye | `cat /etc/os-release` |
| Python | 3.9 | `python3 --version` |
| Node.js | 16 | `node --version` |
| npm | 8 | `npm --version` |
| Git | 2.0 | `git --version` |

---

## 2. 설치 단계

### 2.1 프로젝트 클론

```bash
cd ~
git clone <repository-url> Rasp_FastApi_React
cd Rasp_FastApi_React
```

### 2.2 설치 스크립트 실행

```bash
sudo chmod +x scripts/*.sh
sudo ./scripts/install.sh
```

**설치 스크립트가 수행하는 작업:**

1. 시스템 패키지 업데이트
2. I2C, SPI 인터페이스 활성화
3. Python 가상환경 생성
4. Python 의존성 설치
5. Node.js 의존성 설치
6. 프론트엔드 빌드
7. 환경 설정 파일 생성

### 2.3 수동 설치 (선택적)

#### Python 환경 설정

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

#### 라즈베리파이 전용 라이브러리

```bash
pip install RPi.GPIO gpiozero spidev smbus2
pip install adafruit-circuitpython-dht
pip install adafruit-circuitpython-bmp280
pip install adafruit-circuitpython-ads1x15
pip install adafruit-circuitpython-ssd1306
pip install adafruit-circuitpython-neopixel
pip install RPLCD
```

#### 프론트엔드 빌드

```bash
cd frontend
npm install
npm run build
cp -r dist/* ../backend/static/
```

---

## 3. 환경 설정

### 3.1 환경 변수 파일 (.env)

```bash
# backend/.env 파일 생성/편집
nano backend/.env
```

**설정 옵션:**

```ini
# 서버 설정
HOST=0.0.0.0
PORT=8000
DEBUG=false
LOG_LEVEL=INFO

# 하드웨어 설정
SIMULATION_MODE=false          # true = 시뮬레이션 모드
HARDWARE_UPDATE_INTERVAL=0.5   # 하드웨어 업데이트 주기 (초)
DATA_LOG_INTERVAL=5.0          # 데이터 로깅 주기 (초)
DATA_RETENTION_DAYS=30         # 데이터 보존 기간 (일)

# GPIO 핀 설정 (BCM 번호)
LED_PINS=17,27,22,23
BUTTON_PINS=5,6,13,19
RELAY_PINS=24,25
PWM_MOTOR_PIN=18
PWM_SERVO_PIN=12
DHT_PIN=4
DHT_TYPE=DHT22
NEOPIXEL_PIN=21
NEOPIXEL_COUNT=8

# I2C 설정
I2C_BUS=1
I2C_BMP280_ADDRESS=0x76
I2C_ADS1115_ADDRESS=0x48
I2C_OLED_ADDRESS=0x3C
I2C_LCD_ADDRESS=0x27

# SPI 설정
SPI_BUS=0
SPI_DEVICE=0
SPI_MAX_SPEED=1000000
```

### 3.2 인터페이스 활성화

```bash
sudo raspi-config
```

**Interface Options에서 활성화:**
- I2C
- SPI
- (필요시) Serial Port

또는 `/boot/config.txt` 직접 편집:

```ini
dtparam=i2c_arm=on
dtparam=spi=on
```

재부팅 후 적용:
```bash
sudo reboot
```

---

## 4. 실행 방법

### 4.1 개발 모드

```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 4.2 프로덕션 모드

```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1
```

### 4.3 시스템 서비스로 실행

```bash
sudo ./scripts/install-service.sh
```

**서비스 관리 명령:**

```bash
# 상태 확인
sudo systemctl status raspi-hmi

# 시작
sudo systemctl start raspi-hmi

# 중지
sudo systemctl stop raspi-hmi

# 재시작
sudo systemctl restart raspi-hmi

# 부팅 시 자동 시작 설정
sudo systemctl enable raspi-hmi

# 자동 시작 해제
sudo systemctl disable raspi-hmi

# 로그 확인
sudo journalctl -u raspi-hmi -f
```

---

## 5. Systemd 서비스 설정

### 5.1 서비스 파일 내용

`/etc/systemd/system/raspi-hmi.service`:

```ini
[Unit]
Description=Raspberry Pi HMI System
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/Rasp_FastApi_React/backend
Environment="PATH=/home/pi/Rasp_FastApi_React/backend/venv/bin"
ExecStart=/home/pi/Rasp_FastApi_React/backend/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=5

# 보안 설정
ProtectSystem=strict
ReadWritePaths=/home/pi/Rasp_FastApi_React/backend/data
ReadWritePaths=/home/pi/Rasp_FastApi_React/backend/logs

# 리소스 제한
MemoryMax=512M
CPUQuota=80%

[Install]
WantedBy=multi-user.target
```

### 5.2 서비스 변경 적용

```bash
sudo systemctl daemon-reload
sudo systemctl restart raspi-hmi
```

---

## 6. 키오스크 모드 설정

터치스크린으로 독립 HMI를 구축하려면:

```bash
sudo ./scripts/setup-kiosk.sh
```

**설정 내용:**
- Chromium 브라우저 전체 화면 모드
- 화면 보호기 비활성화
- 마우스 커서 숨김
- 자동 로그인 설정

---

## 7. 네트워크 설정

### 7.1 고정 IP 설정

`/etc/dhcpcd.conf`:

```ini
interface eth0
static ip_address=192.168.1.100/24
static routers=192.168.1.1
static domain_name_servers=8.8.8.8 8.8.4.4

interface wlan0
static ip_address=192.168.1.101/24
static routers=192.168.1.1
static domain_name_servers=8.8.8.8 8.8.4.4
```

### 7.2 방화벽 설정 (UFW)

```bash
sudo apt install ufw
sudo ufw allow 8000/tcp
sudo ufw enable
```

### 7.3 원격 접속

```bash
# SSH (기본 22번 포트)
ssh pi@<raspberry-pi-ip>

# 웹 인터페이스
http://<raspberry-pi-ip>:8000
```

---

## 8. 백업 및 복원

### 8.1 데이터 백업

```bash
# 데이터베이스 백업
cp backend/data/hmi_data.db backup/hmi_data_$(date +%Y%m%d).db

# 설정 백업
cp backend/.env backup/.env_$(date +%Y%m%d)

# 로그 백업
tar -czf backup/logs_$(date +%Y%m%d).tar.gz backend/logs/
```

### 8.2 전체 SD 카드 백업 (Linux/Mac)

```bash
# SD 카드를 이미지로 백업
sudo dd if=/dev/sdX of=raspi_backup.img bs=4M status=progress

# 압축
gzip raspi_backup.img
```

### 8.3 복원

```bash
# 데이터베이스 복원
cp backup/hmi_data_20240101.db backend/data/hmi_data.db

# 서비스 재시작
sudo systemctl restart raspi-hmi
```

---

## 9. 업데이트

### 9.1 코드 업데이트

```bash
cd ~/Rasp_FastApi_React
git pull origin main

# 의존성 업데이트
cd backend
source venv/bin/activate
pip install -r requirements.txt

# 프론트엔드 재빌드
cd ../frontend
npm install
npm run build
cp -r dist/* ../backend/static/

# 서비스 재시작
sudo systemctl restart raspi-hmi
```

### 9.2 시스템 업데이트

```bash
sudo apt update
sudo apt upgrade -y
sudo reboot
```

---

## 10. 문제 해결

### 10.1 서비스가 시작되지 않음

```bash
# 로그 확인
sudo journalctl -u raspi-hmi -n 50

# 수동 실행 테스트
cd backend
source venv/bin/activate
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 10.2 하드웨어가 감지되지 않음

```bash
# I2C 확인
i2cdetect -y 1

# SPI 확인
ls /dev/spidev*

# GPIO 확인
gpio readall  # WiringPi 설치 필요
```

### 10.3 포트 충돌

```bash
# 8000번 포트 사용 중인 프로세스 확인
sudo lsof -i :8000

# 프로세스 종료
sudo kill -9 <PID>
```

### 10.4 메모리 부족

```bash
# 메모리 상태 확인
free -h

# 스왑 파일 크기 증가
sudo dphys-swapfile swapoff
sudo nano /etc/dphys-swapfile  # CONF_SWAPSIZE=1024
sudo dphys-swapfile setup
sudo dphys-swapfile swapon
```

### 10.5 로그 파일 정리

```bash
# 오래된 로그 삭제
find backend/logs/ -name "*.log" -mtime +30 -delete

# journald 로그 정리
sudo journalctl --vacuum-time=7d
```

---

## 11. 성능 최적화

### 11.1 메모리 최적화

`/boot/config.txt`:
```ini
# GPU 메모리 최소화 (헤드리스 서버)
gpu_mem=16
```

### 11.2 SD 카드 수명 연장

```bash
# 임시 파일을 RAM에 저장
echo "tmpfs /tmp tmpfs defaults,noatime,nosuid,size=100m 0 0" | sudo tee -a /etc/fstab
echo "tmpfs /var/log tmpfs defaults,noatime,nosuid,size=50m 0 0" | sudo tee -a /etc/fstab
```

### 11.3 불필요한 서비스 비활성화

```bash
sudo systemctl disable bluetooth
sudo systemctl disable avahi-daemon
sudo systemctl disable triggerhappy
```

---

## 12. 보안 권장사항

### 12.1 기본 보안

```bash
# 기본 비밀번호 변경
passwd

# SSH 루트 로그인 비활성화
sudo nano /etc/ssh/sshd_config
# PermitRootLogin no

# SSH 키 인증만 허용 (선택적)
# PasswordAuthentication no
```

### 12.2 방화벽

```bash
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 8000/tcp
sudo ufw enable
```

### 12.3 Fail2ban 설치

```bash
sudo apt install fail2ban
sudo systemctl enable fail2ban
```
