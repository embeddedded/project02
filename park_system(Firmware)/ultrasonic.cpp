
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
