/*

코드 분리이유

1. '하드웨어 드라이버'와 '비즈니스 로직'의 분리
이 프로젝트는 크게 두 덩어리로 나뉩니다.

비즈니스 로직 (main 역할): "거리가 100cm 이하면 주차된 걸로 쳐라", "LED를 켜라", "Modbus로 통신해라".

하드웨어 드라이버 (ultrasonic.cpp): "4번 핀에 전기를 10마이크로초 동안 쏴라", "3번 핀의 신호가 바뀌는 시간을 재라".

99_setup_loop.ino는 **사장님(관리자)**입니다. "거리 얼마야?"라고 물어보고 결과만 알면 되지, 초음파를 쏘는 복잡한 과정까지 알 필요가 없습니다. 
복잡하고 지저분한 하드웨어 제어 코드를 .cpp 뒤로 숨겨두어, 메인 코드를 깔끔하게 유지하려는 의도입니다.

2. 재사용성 (복사 & 붙여넣기 최적화)
초음파 센서를 사용하는 방식(인터럽트 방식, Non-blocking)은 꽤 고급 기술이라 코드가 복잡합니다. 이렇게 .cpp로 완벽하게 분리해 두면, 
나중에 다른 프로젝트를 할 때 이 파일(ultrasonic.cpp)만 쏙 빼서 가져가면 바로 쓸 수 있습니다.

만약 .ino 파일들에 코드가 섞여 있었다면, 초음파 센서 코드만 발라내기 위해 전체 코드를 다 뒤져야 했을 겁니다.

*/


#include <Arduino.h>

#define TRIG_PIN 4
#define ECHO_PIN 3
#define INTERVAL 100
#define MAX_DIST 400

// 초음파 센서 상태
enum UltrasonicState {
  IDLE,          // 대기 상태
  TRIGGER_SENT,  // 트리거 발사됨
  WAITING_ECHO   // ECHO 기다리는 중
};

static volatile UltrasonicState ultrasonic_state = IDLE;
static volatile unsigned long trigger_time = 0;
static volatile unsigned long echo_start_time = 0;
static volatile int16_t last_distance = 0;
static volatile bool echo_received = false;

static unsigned long ultrasonic_last_time = 0;

// 마지막으로 측정된 거리 반환
int16_t getLastDistance() { return last_distance; }

// ECHO 핀 인터럽트 처리
void echo_ISR() {
  if (digitalRead(ECHO_PIN) == HIGH) {
    // Rising edge: Echo pulse start
    echo_start_time = micros();
    echo_received = false;
  } else {
    // Falling edge: Echo pulse end
    if (echo_start_time > 0) {
      unsigned long duration = micros() - echo_start_time;

      // 거리(cm) = 시간(us) * 0.0343 / 2
      last_distance = min((int16_t)(duration * 0.01715), MAX_DIST);

      echo_received = true;
      ultrasonic_state = IDLE;
      echo_start_time = 0;
    }
  }
}

// 초음파 센서 초기화
void setupUltrasonic() {
  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);
  digitalWrite(TRIG_PIN, LOW);

  attachInterrupt(digitalPinToInterrupt(ECHO_PIN), echo_ISR, CHANGE);

  ultrasonic_state = IDLE;
  last_distance = 0;
  echo_received = false;
}

// 초음파 트리거 발생
void triggerUltrasonic() {
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(2);
  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);

  ultrasonic_state = TRIGGER_SENT;
  trigger_time = millis();
}

// Non-blocking 초음파 측정 주기 처리
bool updateUltrasonic() {
  bool ret = false;
  unsigned long now = millis();

  // INTERVAL 마다 측정 시작
  if (ultrasonic_state == IDLE && (now - ultrasonic_last_time >= INTERVAL)) {
    ultrasonic_last_time = now;
    triggerUltrasonic();
    ret = true;
  }

  // 타임아웃 처리 (echo 미수신)
  if (ultrasonic_state == TRIGGER_SENT && (now - trigger_time > 30)) {
    ultrasonic_state = IDLE;
    echo_start_time = 0;
    echo_received = false;
    last_distance = MAX_DIST;
  }

  return ret;
}
