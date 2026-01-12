#include <EEPROM.h>

// 주차공간 enum 정의
enum SpaceType {
  Closed= 0,  // 이용 불가(OFF)
  General=1,  // 일반 가용(GREEN)
  Disabled=2, // 장애인 가용(BLUE)
  Occupied=3,  // 사용중(RED)
  
  Find=100, // 찾기모드(White)
};

#define IN_RANGE(x, a, b)  ((x) >= (a) && (x) <= (b))

// 정상범위에 있는지 확인
bool isValidSpaceType(uint16_t v) {
  return IN_RANGE(v,Closed, Occupied);
}  

// 설정을 EEPROM에 저장하고 로드하는 Setting 클래스
class Setting {
private:
  uint8_t magic;

public:
  uint8_t  slaveId;    
  Setting() {load();}

public: 
  // 추가 변수
    SpaceType spaceType;
    uint16_t  occupiedDelay;
    uint16_t  availableDelay;
    uint16_t  installHeight;
    uint16_t  objectHeight;
  // 추가 변수 초기화
  void init(){
    spaceType = General;
    occupiedDelay = DELAY_DEFAULT;
    availableDelay = DELAY_DEFAULT;
    installHeight = INSTALL_HEIGHT_DEFAULT;
    objectHeight = OBJECT_HEIGHT_DEFAULT;
   }

  void save() {      
    const byte *ptr = (const byte*)this;  
    for (unsigned int i = 0; i < sizeof(*this); i++) 
      EEPROM.update(i, *(ptr + i));
  }

  void load() {
    EEPROM.get(0, *this);  
    // 로드 후 매직 넘버 검증
    if (magic != DEVICE_MAGIC_NUMBER) {            
      magic = DEVICE_MAGIC_NUMBER;
      slaveId = SLAVE_ID_RANGE_START;
      init();
      save();
    }
  }
};

Setting setting;  // 전역 객체 생성
