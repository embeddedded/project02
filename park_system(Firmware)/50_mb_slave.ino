#include <ModbusRTU.h>
//==================================
// [HOLDING REGISTER MAP]
#define HR_SETTING_GROUP_START     101

#define HR_SPACE_TYPE              101  // 주차면 type setting
#define HR_OCCUPIED_DELAY          102   // 주차 감지 시간 (1초 단위)
#define HR_AVAILABLE_DELAY         103   // 출차 감지 시간 (1초 단위)
#define HR_INSTALL_HEIGHT          104   // 설치 높이 (10~400 cm)
#define HR_OBJECT_HEIGHT           105   // 물체 높이 (10~400 cm)
#define HR_SETTING_GROUP_END       105   // 설정 그룹 종료 주소
#define N_SETTING_GROUP            \
    (HR_SETTING_GROUP_END - HR_SETTING_GROUP_START +1) 

// [INPUT REGISTER MAP]
#define IR_DISTANCE             0

// [DISCRETE INPUT MAP]
#define IN_AVAILABLE            0     // D2 핀 연결 스위치 입력
//==================================
uint16_t cbWritSetting(TRegister* reg, uint16_t val);

ModbusRTU slave;  //slave 객체생성

void setupModbus() {
  // 레지스터 등록
  slave.addHreg(HR_SETTING_GROUP_START, 0, N_SETTING_GROUP);
  slave.addIreg(IR_DISTANCE, 0);
    // 디지털 입력 등록 
  slave.addIsts(IN_AVAILABLE, 0);
  
  // 레지스터 초기값 설정
  slave.Hreg(HR_SPACE_TYPE, setting.spaceType); 
  slave.Hreg(HR_OCCUPIED_DELAY, setting.occupiedDelay); 
  slave.Hreg(HR_AVAILABLE_DELAY, setting.availableDelay); 
  slave.Hreg(HR_INSTALL_HEIGHT, setting.installHeight); 
  slave.Hreg(HR_OBJECT_HEIGHT, setting.objectHeight); 
  // 콜백 추가
  slave.onSetHreg( HR_SETTING_GROUP_START, cbWritSetting, N_SETTING_GROUP );
}

inline void findMode(bool v){
  led.isFindMode = v;
  digitalWrite(LED_BUILTIN, v);  
}

uint16_t cbWritSetting(TRegister* reg, uint16_t val) { 
  uint16_t addr = reg->address.address;
  uint16_t org = reg->value; //원래값  
  switch(addr){
    case HR_SPACE_TYPE:
      if (! isValidSpaceType(val)) 
        return org;
      setting.spaceType = val;
      break;

    case HR_OCCUPIED_DELAY:
      if (! IN_RANGE(val, DELAY_MIN, DELAY_MAX)) 
        return org;
      setting.occupiedDelay = val;
      break;

    case HR_AVAILABLE_DELAY:
      if (! IN_RANGE(val, DELAY_MIN, DELAY_MAX)) 
        return org;
      setting.availableDelay = val;
      break;

    case HR_INSTALL_HEIGHT:
      if (! IN_RANGE(val, HEIGHT_MIN, HEIGHT_MAX)) 
        return org;
      setting.installHeight = val;
      break;

    case HR_OBJECT_HEIGHT:
      if (! IN_RANGE(val, HEIGHT_MIN, HEIGHT_MAX)) 
        return org;
      setting.objectHeight = val;
      break;
  }
  // 유효성 검사 후 EEPROM 저장
  setting.save();

  return val;
}
