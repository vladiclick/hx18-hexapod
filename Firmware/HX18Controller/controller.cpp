#include <Arduino.h>
#include <Wire.h>
#include <esp_task_wdt.h>
#include "config.h"
namespace {
hx::State state{};hx::Slew axes[18]{};
hx::Vec3 startupFeet[6]{},holdFeet[6]{},settleStartFeet[6]{};
bool settling=false,busHealthy=false,outputs=false,benchAcknowledged=false;
int benchServo=-1;double benchTarget=0;
uint32_t benchCommand=0,initAt=0,lastTick=0,lastReport=0;
unsigned initStage=0,lineLength=0;char line[80]{};bool lineOverflow=false;
bool writeRegister(uint8_t address,uint8_t reg,uint8_t value){Wire.beginTransmission(address);Wire.write(reg);Wire.write(value);return Wire.endTransmission()==0;}
bool both(uint8_t reg,uint8_t value){const bool a=writeRegister(config::addresses[0],reg,value),b=writeRegister(config::addresses[1],reg,value);return a&&b;}
void disableOutputs(){digitalWrite(config::oe,HIGH);outputs=false;}
void fault(const char* message){disableOutputs();benchServo=-1;state={hx::Mode::Fault,false,millis(),millis()};Serial.print("FAULT: ");Serial.println(message);}
void initializeDrivers(uint32_t now){
 if(initStage==0){
  const bool ok=both(0xFD,0x10)&&both(0x00,0x30)&&both(0x01,0x04)&&both(0xFE,121)&&both(0x00,0x20);
  if(!ok){initStage=3;fault("PCA init ACK failure");return;}initAt=now;initStage=1;return;
 }
 if(initStage==1&&uint32_t(now-initAt)>=1){busHealthy=both(0x00,0xA0);initStage=busHealthy?2:3;if(!busHealthy)fault("PCA restart failed");else Serial.println("Drivers ready, OE high; read README before bench or ARM.");}
}
bool calibrated(){
 if(!config::calibrationReviewed)return false;
 for(unsigned i=0;i<2;++i)if(!hx::validOscillator(config::oscillatorHz[i],config::oscillatorVerified[i]))return false;
 for(const auto& c:config::servos)if(!hx::valid(c))return false;return true;
}
bool batteryHealthy(){if(!config::batteryEnabled)return true;const double v=analogReadMilliVolts(config::batteryPin)*.001*config::batteryDividerRatio;return std::isfinite(v)&&v>=config::batteryMinimumVolts;}
bool transmit(const uint16_t (&pulses)[18],int single=-1){
 for(unsigned board=0;board<2;++board){
  if(!hx::validOscillator(config::oscillatorHz[board],true))return false;
  Wire.beginTransmission(config::addresses[board]);Wire.write(uint8_t(0x06));
  for(unsigned channel=0;channel<16;++channel){
   const unsigned index=board*9+channel;const bool enabled=channel<9&&(single<0||int(index)==single);
   const uint16_t ticks=enabled?hx::pulseTicks(pulses[index],config::oscillatorHz[board]):0;
   Wire.write(uint8_t(0));Wire.write(uint8_t(0));Wire.write(uint8_t(ticks&0xFF));Wire.write(uint8_t(enabled?((ticks>>8)&0x0F):0x10));
  }if(Wire.endTransmission()!=0)return false;
 }return true;
}
void enableOutputs(){if(!both(0xFD,0)){fault("Output-enable I2C failure");return;}digitalWrite(config::oe,LOW);outputs=true;}
void status(){const char* names[]={"DISABLED","RAMPING","READY","WALKING","FAULT"};Serial.print("state=");Serial.print(names[unsigned(state.mode)]);Serial.print(" calibrated=");Serial.print(calibrated()?"YES":"NO");Serial.print(" OE=");Serial.print(outputs?"ENABLED":"DISABLED");Serial.print(" bench=");Serial.println(benchServo);}
hx::Vec3 currentFoot(unsigned leg){return hx::forward(config::geometry,{axes[leg*3].angle,axes[leg*3+1].angle,axes[leg*3+2].angle});}
void armCommand(uint32_t now){
 if(initStage!=2||benchServo>=0){Serial.println("ARM rejected: driver/bench state");return;}
 const auto t=hx::arm(state,now,calibrated());if(!t.accepted){Serial.println("ARM rejected: verify config and CAL_ACK first");return;}
 if(!batteryHealthy()){fault("Battery below limit");return;}
 for(auto& a:axes)a={};const auto stand=hx::standPose(config::geometry,config::gait);
 for(auto& foot:holdFeet)foot=hx::forward(config::geometry,stand.pose);
 settling=false;state=t.state;Serial.println("5s ramp; keep robot supported.");
}
void walkCommand(uint32_t now){
 if(settling&&uint32_t(now-state.since)<2500){Serial.println("WALK rejected: foot still settling");return;}
 const auto t=hx::startWalk(state,now);if(!t.accepted){Serial.println("WALK rejected: READY required");return;}
 for(unsigned leg=0;leg<6;++leg){startupFeet[leg]=currentFoot(leg);if(std::abs(startupFeet[leg].z-config::gait.standZ)>.1){Serial.println("WALK rejected: wait for all modeled feet to settle");return;}}
 state=t.state;Serial.println("18s one-foot preposition, then slow +Y wave gait.");
}
void stopCommand(uint32_t now){
 if(state.mode==hx::Mode::Walking){for(unsigned leg=0;leg<6;++leg){settleStartFeet[leg]=currentFoot(leg);holdFeet[leg]=settleStartFeet[leg];holdFeet[leg].z=config::gait.standZ;}settling=true;}
 state=hx::stopWalk(state,now);Serial.println("Holding planted XY, lowering swing foot.");
}
void command(const char* text,uint32_t now){
 if(!strcmp(text,"PING")){state=hx::heartbeat(state,now);benchCommand=now;return;}
 if(!strcmp(text,"STATUS")){status();return;}
 if(!strcmp(text,"DISARM")){disableOutputs();state=hx::disarm(state);benchServo=-1;benchAcknowledged=false;both(0xFD,0x10);Serial.println("Disabled, acknowledgement cleared.");return;}
 if(!strcmp(text,"CAL_ACK")){state=hx::acknowledge(state);Serial.println("Acknowledged; config verification still required.");return;}
 if(!strcmp(text,"ARM")){armCommand(now);return;}
 if(!strcmp(text,"WALK")){walkCommand(now);return;}
 if(!strcmp(text,"STOP")){stopCommand(now);return;}
 if(!strcmp(text,"BENCH_ACK")){if(state.mode!=hx::Mode::Disabled){Serial.println("BENCH rejected: DISARM first");return;}benchAcknowledged=true;Serial.println("Bench: support body, remove horn before first center pulse.");return;}
 int index=-1;double angle=0;char extra=0;
 if(sscanf(text,"BENCH %d %c",&index,&extra)==1){
  if(!benchAcknowledged||state.mode!=hx::Mode::Disabled||initStage!=2||index<0||index>=18){Serial.println("BENCH rejected");return;}
  disableOutputs();benchServo=index;benchTarget=0;benchCommand=now;for(auto& a:axes)a={};Serial.println("Single channel:1500us, STEP +/-5deg nominal.");return;
 }
 if(sscanf(text,"STEP %lf %c",&angle,&extra)==1){if(benchServo<0||!std::isfinite(angle)||std::abs(angle)>5){Serial.println("STEP rejected");return;}benchTarget=angle;benchCommand=now;return;}
 Serial.println("Commands: STATUS PING DISARM CAL_ACK ARM WALK STOP BENCH_ACK BENCH 0..17 STEP -5..5");
}
void serialInput(uint32_t now){
 for(unsigned count=0;count<128&&Serial.available();++count){const char c=char(Serial.read());
  if(c=='\n'){if(lineOverflow)Serial.println("Rejected invalid/overlong command");else{line[lineLength]=0;command(line,now);}lineLength=0;lineOverflow=false;}
  else if(c!='\r'){if(c<32||c>126){lineOverflow=true;continue;}if(lineLength<sizeof(line)-1)line[lineLength++]=c;else lineOverflow=true;}
 }
}
void moveBench(double dt,uint32_t now){
 if(uint32_t(now-benchCommand)>1500){fault("Bench heartbeat expired");return;}if(!batteryHealthy()){fault("Battery below limit");return;}
 uint16_t pulses[18]{};axes[benchServo]=hx::slew(axes[benchServo],benchTarget,dt,3,10);pulses[benchServo]=uint16_t(std::lround(1500+10*axes[benchServo].angle));
 if(!transmit(pulses,benchServo)){fault("Bench I2C failure");return;}if(!outputs)enableOutputs();
}
hx::Solve targetPose(unsigned leg,uint32_t now,hx::Pose stand){
 if(state.mode==hx::Mode::Walking){const double elapsed=uint32_t(now-state.since)*.001;
  const auto gait=elapsed<config::gait.period?hx::prepositionTarget(config::geometry,config::gait,leg,elapsed,startupFeet[leg]):hx::crawlTarget(config::geometry,config::gait,leg,hx::startupClock(elapsed-config::gait.period));return {gait.ok,gait.pose};
 }
 if(state.mode==hx::Mode::Ready){hx::Vec3 foot=holdFeet[leg];if(settling){const double u=hx::quintic(uint32_t(now-state.since)/2000.);foot.z=settleStartFeet[leg].z+u*(foot.z-settleStartFeet[leg].z);}return hx::inverse(config::geometry,foot);}
 const double u=hx::quintic(uint32_t(now-state.since)/5000.);return {true,{stand.yaw*u,stand.hip*u,stand.knee*u}};
}
void moveRobot(double dt,uint32_t now){
 state=hx::advance(state,now,busHealthy,batteryHealthy());if(state.mode==hx::Mode::Fault){disableOutputs();return;}if(state.mode==hx::Mode::Disabled)return;
 const auto stand=hx::standPose(config::geometry,config::gait);if(!stand.ok||!hx::allowed(config::geometry,stand.pose)){fault("Invalid stand");return;}
 uint16_t pulses[18]{};hx::Slew next[18]{};
 for(unsigned leg=0;leg<6;++leg){const auto target=targetPose(leg,now,stand.pose);if(!target.ok||!hx::allowed(config::geometry,target.pose)){fault("Target outside workspace");return;}
  const double desired[3]={target.pose.yaw,target.pose.hip,target.pose.knee};
  for(unsigned j=0;j<3;++j){const unsigned i=leg*3+j;next[i]=hx::slew(axes[i],desired[j],dt);const auto p=hx::pulse(config::servos[i],next[i].angle);if(!p.ok){fault("Invalid calibrated pulse");return;}pulses[i]=p.microseconds;}
  if(!hx::allowed(config::geometry,{next[leg*3].angle,next[leg*3+1].angle,next[leg*3+2].angle})){fault("Smoothed pose outside workspace");return;}
 }
 if(!transmit(pulses)){busHealthy=false;fault("Servo I2C failure");return;}for(unsigned i=0;i<18;++i)axes[i]=next[i];if(!outputs)enableOutputs();
}
} // namespace
void setup(){
 digitalWrite(config::oe,HIGH);pinMode(config::oe,OUTPUT);disableOutputs();Serial.begin(115200);Wire.setTimeOut(10);
 if(Wire.setBufferSize(128)<65||!Wire.begin(config::sda,config::scl,100000)){initStage=3;fault("ESP32 I2C init failed");}
 const esp_task_wdt_config_t wdtConfig{1000,0,true};esp_err_t result=esp_task_wdt_init(&wdtConfig);if(result==ESP_ERR_INVALID_STATE)result=esp_task_wdt_reconfigure(&wdtConfig);
 if(result!=ESP_OK||(esp_task_wdt_status(nullptr)!=ESP_OK&&esp_task_wdt_add(nullptr)!=ESP_OK)){initStage=3;fault("Task watchdog init failed");}
 lastTick=millis();Serial.println("HX18 boot: outputs disabled.");
}
void loop(){
 const uint32_t now=millis();if(esp_task_wdt_reset()!=ESP_OK){fault("Watchdog service failed");return;}serialInput(now);if(initStage<2)initializeDrivers(now);
 if(outputs&&uint32_t(now-lastTick)>100){fault("Loop stalled >100ms");lastTick=now;return;}
 const uint32_t elapsed=uint32_t(now-lastTick);if(elapsed<20)return;lastTick=now;
 if(benchServo>=0)moveBench(elapsed*.001,now);else moveRobot(elapsed*.001,now);
 if(state.mode==hx::Mode::Fault&&uint32_t(now-lastReport)>1000){lastReport=now;status();}
}
