# 하드웨어 연결 가이드

## GPIO 핀 배치도

라즈베리파이 40핀 GPIO 헤더 기준입니다 (BCM 번호 사용).

```
                    3.3V  [1]  [2]  5V
                   GPIO2  [3]  [4]  5V           ← I2C SDA
                   GPIO3  [5]  [6]  GND          ← I2C SCL
                   GPIO4  [7]  [8]  GPIO14       ← DHT22
                     GND  [9]  [10] GPIO15
                  GPIO17 [11] [12] GPIO18       ← LED1, PWM (모터)
                  GPIO27 [13] [14] GND          ← LED2
                  GPIO22 [15] [16] GPIO23       ← LED3, LED4
                    3.3V [17] [18] GPIO24       ← Relay1
                  GPIO10 [19] [20] GND          ← SPI MOSI
                   GPIO9 [21] [22] GPIO25       ← SPI MISO, Relay2
                  GPIO11 [23] [24] GPIO8        ← SPI SCLK, SPI CE0
                     GND [25] [26] GPIO7
                   GPIO0 [27] [28] GPIO1
                   GPIO5 [29] [30] GND          ← Button1
                   GPIO6 [31] [32] GPIO12       ← Button2, Servo
                  GPIO13 [33] [34] GND          ← Button3
                  GPIO19 [35] [36] GPIO16       ← Button4
                  GPIO26 [37] [38] GPIO20
                     GND [39] [40] GPIO21       ← NeoPixel
```

## LED 연결

### 회로도

```
GPIO17 ──[330Ω]──LED(+)──GND
GPIO27 ──[330Ω]──LED(+)──GND
GPIO22 ──[330Ω]──LED(+)──GND
GPIO23 ──[330Ω]──LED(+)──GND
```

### 연결 방법

1. LED 긴 다리 (양극, +)를 저항에 연결
2. 저항의 다른 쪽을 GPIO 핀에 연결
3. LED 짧은 다리 (음극, -)를 GND에 연결
4. 저항 값: 220Ω ~ 470Ω (권장 330Ω)

## 버튼 연결

### 회로도 (내부 풀업 사용)

```
GPIO5 ────┬──Button──GND
          │
        (내부 풀업)

GPIO6 ────┬──Button──GND
GPIO13 ───┬──Button──GND
GPIO19 ───┬──Button──GND
```

### 연결 방법

1. 버튼의 한쪽을 GPIO 핀에 연결
2. 버튼의 다른 쪽을 GND에 연결
3. 소프트웨어에서 내부 풀업 저항 활성화 (이미 설정됨)

> 버튼을 누르지 않으면 HIGH (1), 누르면 LOW (0)

## 릴레이 모듈 연결

### 회로도

```
5V ────────── VCC (릴레이 모듈)
GND ───────── GND (릴레이 모듈)
GPIO24 ────── IN1 (릴레이 1)
GPIO25 ────── IN2 (릴레이 2)
```

### 주의사항

- 릴레이 모듈은 반드시 5V 전원 사용
- 고전압/고전류 장치 연결 시 안전 주의
- 신호 레벨은 3.3V 호환 모듈 사용

## DHT22 온습도 센서

### 회로도

```
3.3V ──────── VCC (1번 핀)
GPIO4 ─[10kΩ]─┬── DATA (2번 핀)
              │
           3.3V (풀업)
NC ─────────── NC (3번 핀)
GND ─────────── GND (4번 핀)
```

### 연결 방법

1. VCC를 3.3V에 연결 (5V도 가능하지만 3.3V 권장)
2. DATA 핀을 GPIO4에 연결
3. DATA와 VCC 사이에 10kΩ 풀업 저항 연결 (일부 모듈은 내장)
4. GND 연결

## BMP280 기압계 센서 (I2C)

### 회로도

```
3.3V ────── VCC
GND ─────── GND
GPIO2 ───── SDA
GPIO3 ───── SCL
GND ─────── SDO (0x76 주소 선택)
            또는
3.3V ────── SDO (0x77 주소 선택)
```

### I2C 주소 확인

```bash
i2cdetect -y 1
```

기본 주소: 0x76 (SDO = GND)

## ADS1115 ADC (I2C)

### 회로도

```
3.3V ────── VCC
GND ─────── GND
GPIO2 ───── SDA
GPIO3 ───── SCL
GND ─────── ADDR (0x48 주소)

A0 ──────── 아날로그 입력 1
A1 ──────── 아날로그 입력 2
A2 ──────── 아날로그 입력 3
A3 ──────── 아날로그 입력 4
```

### 전압 측정 범위

- 기본 게인: ±4.096V
- 분해능: 16비트 (65536 단계)

## MCP3008 ADC (SPI)

### 회로도

```
3.3V ────── VDD
3.3V ────── VREF
GND ─────── AGND
GND ─────── DGND
GPIO11 ──── CLK
GPIO9 ───── DOUT
GPIO10 ──── DIN
GPIO8 ───── CS/SHDN

CH0 ─────── 아날로그 입력 0
CH1 ─────── 아날로그 입력 1
...
CH7 ─────── 아날로그 입력 7
```

### 주의사항

- 반드시 3.3V 전원 사용
- VREF는 기준 전압 (측정 범위)
- 채널당 10비트 분해능 (0-1023)

## HC-SR04 초음파 거리 센서

### 회로도

```
5V ───────── VCC
GND ────────GND
GPIO23 ──── TRIG
          ┌─ECHO
          ├─[1kΩ]──GPIO24
          └─[2kΩ]──GND
```

### 주의사항

- ECHO 핀은 5V 출력이므로 분압 필수!
- 분압 저항: 1kΩ + 2kΩ (3.3V로 변환)
- 또는 레벨 시프터 사용

## PIR 모션 센서 (HC-SR501)

### 회로도

```
5V ────── VCC
GND ───── GND
GPIO25 ── OUT
```

### 설정

- 감도: 트리머로 조절
- 지연 시간: 트리머로 조절
- 반복 트리거 모드 권장

## SSD1306 OLED 디스플레이 (I2C)

### 회로도

```
3.3V ───── VCC
GND ────── GND
GPIO2 ──── SDA
GPIO3 ──── SCL
```

### I2C 주소

기본 주소: 0x3C

## 1602/2004 LCD (I2C 백팩)

### 회로도

```
5V ────── VCC
GND ───── GND
GPIO2 ──── SDA
GPIO3 ──── SCL
```

### I2C 주소

기본 주소: 0x27 (또는 0x3F)

## WS2812B NeoPixel LED 스트립

### 회로도

```
5V ─────────────── VCC
GND ────────────── GND
GPIO21 ──[330Ω]──── DIN
```

### 주의사항

- 반드시 5V 전원 사용
- LED당 최대 60mA 소비 (8개 = 480mA)
- 데이터 핀에 330Ω 저항 권장
- 긴 스트립은 별도 전원 공급

## 전원 고려사항

### 3.3V 핀 최대 전류

- GPIO 헤더 3.3V: 최대 50mA (라즈베리파이 4)
- 센서 여러 개 연결 시 별도 3.3V 레귤레이터 사용

### 5V 핀

- USB 전원 공급기 용량에 따라 다름
- 릴레이, LED 스트립 등은 별도 전원 권장

### GPIO 핀 전류

- 개별 핀: 최대 16mA
- 전체 합계: 최대 50mA

## 전체 연결 예시

```
                    ┌─────────────────────────────────────┐
                    │          Raspberry Pi 4             │
                    │                                     │
   ┌─LED1───────────┤ GPIO17                  3.3V ├──────┬──BMP280
   ├─LED2───────────┤ GPIO27                  GPIO2 ├─────┼──(I2C SDA)
   ├─LED3───────────┤ GPIO22                  GPIO3 ├─────┼──(I2C SCL)
   └─LED4───────────┤ GPIO23                              │
                    │                                     │
   ┌─Button1────────┤ GPIO5                    5V ├───────┼──Relay Module
   ├─Button2────────┤ GPIO6                               │
   ├─Button3────────┤ GPIO13                              │
   └─Button4────────┤ GPIO19                              │
                    │                                     │
   ┌─Relay1─────────┤ GPIO24                              │
   └─Relay2─────────┤ GPIO25                              │
                    │                                     │
   ─Motor PWM───────┤ GPIO18                              │
   ─Servo PWM───────┤ GPIO12                              │
                    │                                     │
   ─DHT22───────────┤ GPIO4                               │
   ─NeoPixel────────┤ GPIO21                              │
                    │                                     │
   ┌─MCP3008────────┤ GPIO10 (MOSI)                       │
   │                ┤ GPIO9  (MISO)                       │
   │                ┤ GPIO11 (SCLK)                       │
   └────────────────┤ GPIO8  (CE0)                        │
                    │                                     │
                    └─────────────────────────────────────┘
```

## 테스트 방법

### LED 테스트

```bash
# GPIO 17 HIGH 설정
gpio -g mode 17 out
gpio -g write 17 1

# GPIO 17 LOW 설정
gpio -g write 17 0
```

### I2C 장치 스캔

```bash
sudo i2cdetect -y 1
```

### SPI 활성화 확인

```bash
ls /dev/spi*
```
