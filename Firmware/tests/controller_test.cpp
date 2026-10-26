#include <cassert>
#include <iostream>
#include "../HX18Controller/controller.cpp"
int main(){
 setup();assert(oeLevel==HIGH);loop();assert(initStage==1);fakeMillis=1;loop();assert(initStage==2&&oeLevel==HIGH);
 command("ARM",1);assert(state.mode==hx::Mode::Disabled);command("CAL_ACK",2);command("ARM",2);assert(state.mode==hx::Mode::Disabled);
 command("BENCH 0",2);assert(benchServo==-1);command("BENCH_ACK",2);command("BENCH 18",2);assert(benchServo==-1);command("BENCH 17",2);assert(benchServo==17&&oeLevel==HIGH);
 command("STEP 6",2);assert(benchTarget==0);command("STEP nan",2);assert(benchTarget==0);command("STEP 3",2);fakeMillis=20;loop();assert(oeLevel==LOW);
 const auto& p=Wire.writes[Wire.writes.size()-3];assert(p.size()==66);for(unsigned c=0;c<16;++c){if(c==8)assert((p[5+c*4]&0x10)==0);else assert(p[5+c*4]==0x10);}
 command("PING",1000);fakeMillis=1020;loop();assert(oeLevel==HIGH&&state.mode==hx::Mode::Fault);
 command("DISARM",1020);command("BENCH_ACK",1020);command("BENCH 0",1020);fakeMillis=1040;loop();assert(oeLevel==LOW);Wire.fail=true;fakeMillis=1060;loop();assert(oeLevel==HIGH&&state.mode==hx::Mode::Fault);
 Wire.fail=false;command("DISARM",1060);command("BENCH_ACK",1060);command("BENCH 0",1060);for(int i=1;i<=76;++i){fakeMillis=1060+i*20;loop();}assert(state.mode==hx::Mode::Fault&&oeLevel==HIGH);
 command("DISARM",fakeMillis);Serial.input=std::string(100,'A')+"\nBENCH_ACK\nBENCH 0\n";serialInput(fakeMillis);serialInput(fakeMillis);assert(benchServo==0);
 command("DISARM",fakeMillis);command("BENCH_ACK",fakeMillis);Serial.input=std::string("BENCH 0\0HIDDEN\n",15);serialInput(fakeMillis);assert(benchServo==-1);
 command("DISARM",fakeMillis);command("STATUS",fakeMillis);command("STOP",fakeMillis);command("WALK",fakeMillis);assert(state.mode==hx::Mode::Disabled);
 std::cout<<"Controller safety integration passed: disabled boot/ARM gate, channel17, I2C fault, stall, heartbeat, malformed/control-character commands.\n";
}
