#ifndef SLAVE_SERIAL
  #define SLAVE_SERIAL Serial
#endif
#ifndef SLAVE_DERE_PIN
  #define SLAVE_DERE_PIN   2 // RS-485 DE/RE 제어 핀
#endif
#ifndef SLAVE_BAUD_RATE
  #define SLAVE_BAUD_RATE 115200
#endif 

//=====================================================
#define CL_GROUP_START       0 // 코일 시작 주소
#define CL_ID_SETTING_MODE   0 // ID 설정 모드
#define CL_FIND_MODE         1 // 노드 찾기 모드
#define CL_DEVICE_RESET      2 // 장치 리셋
#define CL_GROUP_END         2 // 코일 종료 주소
#define N_CL_GROUP   (CL_GROUP_END - CL_GROUP_START + 1)        

#define HR_SLAVE_ID          100 // 슬레이브 ID 설정
//=====================================================
uint16_t cbWriteCoil(TRegister* reg, uint16_t val);
uint16_t cbWriteSlaveId(TRegister* reg, uint16_t val);

void(* resetFunc) (void) = 0; // 리셋함수->리셋벡터 호출

void setupModbusBase() {
  pinMode(LED_BUILTIN, OUTPUT);
  digitalWrite(LED_BUILTIN, LOW);

  SLAVE_SERIAL.begin(SLAVE_BAUD_RATE);  
  slave.begin(&SLAVE_SERIAL,SLAVE_DERE_PIN);
  slave.slave(setting.slaveId);

  slave.addHreg(HR_SLAVE_ID, 0, 1);
  slave.addCoil(CL_GROUP_START, 0, N_CL_GROUP);  
  slave.Hreg(HR_SLAVE_ID, setting.slaveId); 

  slave.onSetHreg( HR_SLAVE_ID,cbWriteSlaveId);
  slave.onSetCoil( CL_GROUP_START, cbWriteCoil, N_CL_GROUP );
}

uint16_t cbWriteCoil(TRegister* reg, uint16_t val) {
  uint8_t addr = reg->address.address;
  switch(addr){
    case CL_FIND_MODE:    
      {
        bool b= COIL_BOOL(val);
        digitalWrite(LED_BUILTIN, b);
        findMode(b);
      }
      break; 
    case CL_DEVICE_RESET:
      resetFunc();
      break;  
  }
  return val;
}

uint16_t cbWriteSlaveId(TRegister* reg, uint16_t val) {   
  uint16_t org = reg->value; //원래값
  
  if (! slave.Coil(CL_ID_SETTING_MODE) 
      || val == org 
      || val < SLAVE_ID_RANGE_START || val > SLAVE_ID_RANGE_END) 
    return org; // 변경없음

  //EEPROM에 저장
  setting.slaveId= val;
  setting.save();
  return val;
}
