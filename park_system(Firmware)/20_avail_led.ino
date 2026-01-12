#define LED_R A0
#define LED_G A1
#define LED_B A2

class AvailLed {
private:
  const uint8_t ledPins[3] = {LED_R, LED_G, LED_B};

  void control(SpaceType type) {
    for (uint8_t i = 0; i < 3; i++)
      digitalWrite(ledPins[i], LOW);
    
    switch (type) {
      case SpaceType::General:
        digitalWrite(LED_G, HIGH);
        break;

      case SpaceType::Disabled:
        digitalWrite(LED_B, HIGH);
        break;

      case SpaceType::Occupied:
        digitalWrite(LED_R, HIGH);
        break;

      case SpaceType::Find:
        for (uint8_t i = 0; i < 3; i++)
          digitalWrite(ledPins[i], HIGH);
        break;
    }
  }

public:
  bool isFindMode = false;

  AvailLed() {
    for (uint8_t i = 0; i < 3; i++)
      pinMode(ledPins[i], OUTPUT);
    control(SpaceType::Closed);
  }

  void updateLight(bool avail){
    if (isFindMode){
      control(SpaceType::Find);
      return;
    }
    if (setting.spaceType == SpaceType::Closed ||
        setting.spaceType == SpaceType::Occupied ) {   
        control(setting.spaceType);
        return; 
    }

    control(avail ? setting.spaceType : SpaceType::Occupied);
  }

};

AvailLed led;
