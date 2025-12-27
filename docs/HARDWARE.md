# 하드웨어 가이드

## 1. 지원 하드웨어 목록

### 1.1 입출력 장치

| 장치 | 타입 | 인터페이스 | 수량 | 기본 핀 (BCM) |
|------|------|-----------|------|---------------|
| LED | RGB/일반 | GPIO (출력) | 4 | 17, 27, 22, 23 |
| 버튼 | 택트 스위치 | GPIO (입력) | 4 | 5, 6, 13, 19 |
| 릴레이 | 5V 모듈 | GPIO (출력) | 2 | 24, 25 |
| DC 모터 | 브러시 | PWM | 1 | 18 |
| 서보 모터 | SG90/MG996R | PWM | 1 | 12 |

### 1.2 센서

| 센서 | 모델 | 인터페이스 | 측정 값 | 기본 핀/주소 |
|------|------|-----------|--------|--------------|
| 온습도 | DHT11/DHT22 | GPIO (1-Wire) | 온도, 습도 | GPIO 4 |
| 기압계 | BMP280 | I2C | 온도, 기압, 고도 | 0x76 |
| ADC | ADS1115 | I2C | 전압 (4ch, 16bit) | 0x48 |
| ADC | MCP3008 | SPI | 전압 (8ch, 10bit) | CE0 |
| 거리 | HC-SR04 | GPIO | 거리 (cm) | Trig:23, Echo:24 |
| 모션 | HC-SR501 | GPIO (입력) | 움직임 감지 | GPIO 25 |
| 조도 | LDR | ADC 경유 | 빛 밝기 | ADC Ch0 |
| 토양수분 | Capacitive | ADC 경유 | 습도 레벨 | ADC Ch1 |

### 1.3 디스플레이

| 디스플레이 | 모델 | 인터페이스 | 해상도 | 기본 주소 |
|------------|------|-----------|--------|----------|
| OLED | SSD1306 | I2C | 128x64 | 0x3C |
| LCD | 1602/2004 | I2C | 16x2/20x4 | 0x27 |
| LED 스트립 | WS2812B | GPIO | 8 LED | GPIO 21 |

---

## 2. 핀 배치도

### 2.1 GPIO 헤더 (40핀)

```
                 3.3V (1)  (2)  5V
         I2C SDA (3)  (4)  5V
         I2C SCL (5)  (6)  GND
         DHT_PIN (7)  (8)  TX
                 GND (9)  (10) RX
        BUTTON_0 (11) (12) PWM_MOTOR [GPIO 18]
        BUTTON_1 (13) (14) GND
        BUTTON_2 (15) (16) BUTTON_3
            3.3V (17) (18) LED_0 [GPIO 17]
         SPI MOSI (19) (20) GND
         SPI MISO (21) (22) LED_1 [GPIO 27]
         SPI SCLK (23) (24) SPI CE0
                 GND (25) (26) SPI CE1
           Reserved (27) (28) Reserved
             LED_2 (29) (30) GND
             LED_3 (31) (32) PWM_SERVO [GPIO 12]
         ULTRASONIC_TRIG (33) (34) GND
         ULTRASONIC_ECHO (35) (36) RELAY_0
              PIR (37) (38) RELAY_1
                 GND (39) (40) NEOPIXEL
```

### 2.2 BCM 핀 번호 매핑

| 물리 핀 | BCM | 기능 | 장치 |
|--------|-----|------|------|
| 3 | GPIO 2 | I2C SDA | BMP280, ADS1115, OLED, LCD |
| 5 | GPIO 3 | I2C SCL | BMP280, ADS1115, OLED, LCD |
| 7 | GPIO 4 | 1-Wire | DHT11/DHT22 |
| 11 | GPIO 17 | Output | LED 0 |
| 13 | GPIO 27 | Output | LED 1 |
| 15 | GPIO 22 | Output | LED 2 |
| 16 | GPIO 23 | Output | LED 3 / Ultrasonic Trig |
| 12 | GPIO 18 | PWM0 | DC Motor |
| 32 | GPIO 12 | PWM1 | Servo |
| 29 | GPIO 5 | Input (Pull-up) | Button 0 |
| 31 | GPIO 6 | Input (Pull-up) | Button 1 |
| 33 | GPIO 13 | Input (Pull-up) | Button 2 |
| 35 | GPIO 19 | Input (Pull-up) | Button 3 |
| 18 | GPIO 24 | Output / Input | Relay 0 / Ultrasonic Echo |
| 22 | GPIO 25 | Output / Input | Relay 1 / PIR |
| 40 | GPIO 21 | Output | NeoPixel |
| 19 | GPIO 10 | SPI MOSI | MCP3008 |
| 21 | GPIO 9 | SPI MISO | MCP3008 |
| 23 | GPIO 11 | SPI SCLK | MCP3008 |
| 24 | GPIO 8 | SPI CE0 | MCP3008 |

---

## 3. 배선 가이드

### 3.1 LED 연결

```
라즈베리파이          LED
┌────────────┐      ┌────┐
│  GPIO 17   ├──────┤ +  │ (긴 다리, 양극)
│            │  R   │    │
│  GND       ├─[220]┤ -  │ (짧은 다리, 음극)
└────────────┘      └────┘
                    R = 220Ω ~ 330Ω 저항
```

**코드 예제:**
```python
await gpio_controller.write_pin(17, PinState.HIGH)  # LED ON
await gpio_controller.write_pin(17, PinState.LOW)   # LED OFF
```

### 3.2 버튼 연결 (내부 풀업 사용)

```
라즈베리파이          버튼
┌────────────┐      ┌────┐
│  GPIO 5    ├──────┤    │
│            │      │ SW │
│  GND       ├──────┤    │
└────────────┘      └────┘
```

**참고:** 내부 풀업 저항 사용 시 버튼 누름 = LOW, 떼면 = HIGH

**코드 예제:**
```python
state = await gpio_controller.read_pin(5)
if state == PinState.LOW:
    print("버튼 눌림!")
```

### 3.3 DHT11/DHT22 연결

```
라즈베리파이          DHT11/22
┌────────────┐      ┌────────┐
│  3.3V/5V   ├──────┤ VCC    │
│  GPIO 4    ├──────┤ DATA   │
│            │  R   │        │
│  (내부)    ├─[10k]┤ DATA   │ (풀업 저항, 선택적)
│  GND       ├──────┤ GND    │
└────────────┘      └────────┘
```

**코드 예제:**
```python
data = await sensor_controller.read_dht()
# {'temperature': 25.5, 'humidity': 60.0}
```

### 3.4 HC-SR04 초음파 센서

```
라즈베리파이          HC-SR04
┌────────────┐      ┌────────┐
│  5V        ├──────┤ VCC    │
│  GPIO 23   ├──────┤ TRIG   │
│            │      │        │
│  GPIO 24   ├──[R1]┤ ECHO   │ (분압 회로)
│            │  │   │        │
│  GND       ├──[R2]┤ GND    │
└────────────┘      └────────┘
         분압 회로: R1 = 1kΩ, R2 = 2kΩ
         (5V → 3.3V 변환)
```

**코드 예제:**
```python
distance = await sensor_controller.read_ultrasonic()
# 거리 (cm), 예: 45.2
```

### 3.5 I2C 장치 연결

```
라즈베리파이          I2C 장치 (BMP280, ADS1115, OLED)
┌────────────┐      ┌────────┐
│  3.3V      ├──────┤ VIN    │
│  GPIO 2    ├──────┤ SDA    │
│  GPIO 3    ├──────┤ SCL    │
│  GND       ├──────┤ GND    │
└────────────┘      └────────┘
```

**여러 I2C 장치 연결 (버스 공유):**
```
       GPIO 2 (SDA) ──────┬──────┬──────┬──────
                          │      │      │
                       BMP280  ADS1115 OLED  LCD
                       (0x76) (0x48) (0x3C) (0x27)
                          │      │      │
       GPIO 3 (SCL) ──────┴──────┴──────┴──────
```

**코드 예제:**
```python
# BMP280 읽기
data = await i2c_controller.read_bmp280()
# {'temperature': 25.5, 'pressure': 1013.25, 'altitude': 100.5}

# ADS1115 ADC 읽기
voltage = await i2c_controller.read_adc(channel=0)
# 전압 (V), 예: 2.5

# OLED에 텍스트 출력
await display_controller.oled_text("Hello", x=0, y=0)
```

### 3.6 MCP3008 SPI ADC

```
라즈베리파이          MCP3008
┌────────────┐      ┌────────┐
│  3.3V      ├──────┤ VDD    │
│  3.3V      ├──────┤ VREF   │
│  GND       ├──────┤ AGND   │
│  GPIO 8    ├──────┤ CS     │ (CE0)
│  GPIO 10   ├──────┤ DIN    │ (MOSI)
│  GPIO 9    ├──────┤ DOUT   │ (MISO)
│  GPIO 11   ├──────┤ CLK    │ (SCLK)
│  GND       ├──────┤ DGND   │
└────────────┘      └────────┘
```

**아날로그 센서 연결 (LDR 예제):**
```
3.3V ──┬── [LDR] ───┬── MCP3008 CH0
       │            │
       └── [10kΩ] ──┴── GND
```

**코드 예제:**
```python
# MCP3008 채널 읽기 (10bit: 0-1023)
raw = await spi_controller.read_mcp3008(channel=0)

# 전압으로 변환
voltage = await spi_controller.read_mcp3008_voltage(channel=0, vref=3.3)
```

### 3.7 WS2812B NeoPixel

```
라즈베리파이          NeoPixel 스트립
┌────────────┐      ┌────────────────────┐
│  5V        ├──────┤ VCC                │
│  GPIO 21   ├──────┤ DIN                │
│  GND       ├──────┤ GND                │
└────────────┘      └────────────────────┘
                    ↓
              LED 0 → LED 1 → LED 2 → ... → LED 7
```

**참고:** 전류가 많이 필요하므로 외부 5V 전원 권장 (LED 개당 ~60mA)

**코드 예제:**
```python
# 단일 픽셀 색상 설정
await neopixel_controller.set_pixel(0, RGBColor(255, 0, 0))  # 빨강

# 전체 색상 설정
await neopixel_controller.set_all(RGBColor(0, 255, 0))  # 초록

# 효과 시작
await neopixel_controller.start_effect(NeopixelEffect.RAINBOW)
```

### 3.8 서보 모터

```
라즈베리파이          서보 모터 (SG90)
┌────────────┐      ┌────────┐
│  5V (외부) ├──────┤ VCC    │ (빨강)
│  GPIO 12   ├──────┤ Signal │ (주황/노랑)
│  GND       ├──────┤ GND    │ (갈색/검정)
└────────────┘      └────────┘
```

**주의:** 서보 모터는 순간 전류가 높으므로 외부 전원 권장

**코드 예제:**
```python
await pwm_controller.set_servo_angle(90)  # 90도 위치
await pwm_controller.set_servo_angle(0)   # 0도 위치
await pwm_controller.set_servo_angle(180) # 180도 위치
```

---

## 4. I2C 주소 스캔

```bash
# I2C 장치 스캔
i2cdetect -y 1
```

**예상 출력:**
```
     0  1  2  3  4  5  6  7  8  9  a  b  c  d  e  f
00:          -- -- -- -- -- -- -- -- -- -- -- -- --
10: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
20: -- -- -- -- -- -- -- 27 -- -- -- -- -- -- -- --
30: -- -- -- -- -- -- -- -- -- -- -- -- 3c -- -- --
40: -- -- -- -- -- -- -- -- 48 -- -- -- -- -- -- --
50: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
60: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
70: -- -- -- -- -- -- 76 --
```

- 0x27: LCD (PCF8574 I/O 확장기)
- 0x3C: SSD1306 OLED
- 0x48: ADS1115 ADC
- 0x76: BMP280 기압계

---

## 5. 시뮬레이션 모드

### 5.1 시뮬레이션 모드란?

라즈베리파이가 아닌 환경(Windows, Mac, Linux PC)에서 하드웨어 없이 시스템을 테스트할 수 있습니다.

### 5.2 활성화 방법

```bash
# .env 파일에서 설정
SIMULATION_MODE=true
```

또는 라즈베리파이가 아니면 자동으로 활성화됩니다.

### 5.3 시뮬레이션 동작

| 기능 | 시뮬레이션 동작 |
|------|----------------|
| GPIO 출력 | 상태 저장만 (실제 출력 없음) |
| GPIO 입력 | 저장된 상태 반환 |
| 센서 읽기 | 노이즈가 추가된 가상 값 |
| PWM | 값 저장만 |
| I2C/SPI | 가상 데이터 반환 |

### 5.4 가상 값 설정

```python
# API를 통해 시뮬레이션 값 설정
POST /api/hardware/simulation/values
{
    "temperature": 30.0,
    "humidity": 70.0,
    "distance": 50.0
}
```

---

## 6. 문제 해결

### 6.1 I2C 장치가 감지되지 않음

1. I2C 활성화 확인: `sudo raspi-config` → Interface Options → I2C
2. 배선 확인 (SDA, SCL, VCC, GND)
3. 장치 주소 확인: `i2cdetect -y 1`

### 6.2 SPI 장치가 작동하지 않음

1. SPI 활성화 확인: `sudo raspi-config` → Interface Options → SPI
2. 배선 확인 (MOSI, MISO, SCLK, CE0)
3. 장치 파일 확인: `ls /dev/spidev*`

### 6.3 GPIO 권한 오류

```bash
# gpio 그룹에 사용자 추가
sudo usermod -aG gpio $USER

# 재로그인 후 확인
groups
```

### 6.4 NeoPixel이 작동하지 않음

1. PWM 사용 핀 확인 (GPIO 18, 21 권장)
2. 외부 전원 확인 (LED가 많으면 필수)
3. root 권한으로 실행 필요할 수 있음

---

## 7. 전원 고려사항

### 7.1 라즈베리파이 GPIO 전원 제한

| 항목 | 최대 값 |
|------|--------|
| 3.3V 핀 총 전류 | 50mA |
| 5V 핀 총 전류 | USB 전원에서 남는 전류 |
| 개별 GPIO 핀 | 16mA |
| 모든 GPIO 총합 | 50mA |

### 7.2 외부 전원 권장 장치

- 서보 모터 (SG90: 400mA, MG996R: 2.5A)
- NeoPixel LED 스트립 (LED당 60mA)
- 릴레이 모듈 (코일 전류)
- DC 모터

### 7.3 안전한 전원 구성

```
USB 전원 (5V 3A) ──► 라즈베리파이
                          │
외부 5V 전원 ──────────────┼──► 서보 모터
       │                   │
       └───────────────────┼──► NeoPixel
                           │
                           └──► 릴레이 모듈
```

**중요:** 외부 전원 사용 시 반드시 GND를 공유해야 합니다.
