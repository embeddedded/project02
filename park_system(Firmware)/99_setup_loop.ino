  // 초음파 센서 관련 함수(파일 확장자가 달라서 선언해줌)
void setupUltrasonic();
bool updateUltrasonic();
int16_t getLastDistance();
 
void setup() {        //초기화
  setupModbusBase();  //51
  setupModbus();      //50
  setupUltrasonic();  //ul
}

void loop() {
  static bool available = false; 
  static uint16_t occupiedDelay = 0;
  static uint16_t availableDelay = 0;

  // 초음파 센서 주기적 업데이트 
  if (updateUltrasonic()) {
    int16_t dist = getLastDistance();    
    int16_t dist_lim = min(setting.installHeight , dist ) ;
    int obj_h = setting.installHeight - dist_lim; // 객체높이 계산

    if (obj_h > setting.objectHeight ) {
      availableDelay = 0;
      if (available && ++occupiedDelay >= setting.occupiedDelay * 10 )
        available = false; // 주차됨
    }
    else {
      occupiedDelay = 0;
      if (!available && ++availableDelay >= setting.availableDelay * 10 )
        available = true;
    }
    
    led.updateLight(available);       

    slave.Ists(IN_AVAILABLE, (setting.spaceType == Closed) ? false : available);
    slave.Ireg(IR_DISTANCE, dist_lim);
  }
  slave.task();  // Modbus RTU 프레임 처리
}
