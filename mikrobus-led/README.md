# mikroBUS LED click (printed)

AC164162 의 mikroBUS 소켓에 꽂아서 Seeed 104990014 RGB LED 띠(WS2812 계열, 60 LED/m, 5 V)를 연결하는 출력 받침. PCB 없음.

- 28.6 × 25.4 × 2.5 mm (Click S 크기), 0.12 mm 층: **12분 / 1.6 g** (`led_click.gcode.3mf`)
- 1×8 수 핀헤더 2개를 홈에 끼운다(플라스틱 몸통이 판 안, 긴 핀이 아래로 소켓에). 끝의 1×3 핀헤더에 LED 띠를 꽂는다.
- 위쪽 홈 3개에 짧은 전선을 납땜: **PWM → DI, 5V → 5V, GND → G** (모두 PWM 쪽 줄). 납땜 전에 베이스 보드 소켓 실크와 핀 이름을 맞춰 볼 것.
- 데이터선에 330 Ω, 띠 쪽 5 V–GND 에 470–1000 µF. 60개 전부 흰색이면 ~3.6 A — 베이스의 5 V 핀으로는 못 준다: 밝기를 낮추거나 띠 5 V 를 따로 준다.
- 소스: `led_click.py` (cadquery)
