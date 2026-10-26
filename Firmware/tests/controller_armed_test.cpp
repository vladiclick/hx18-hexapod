#include <cassert>
#include <iostream>
#include "../build/calibrated-fixture/controller.cpp"
int main(){
 setup();loop();fakeMillis=1;loop();command("CAL_ACK",1);command("ARM",1);assert(state.mode==hx::Mode::Ramping);
 for(int t=20;t<=6000;t+=20){fakeMillis=t;if(t%200==0)command("PING",t);loop();assert(state.mode!=hx::Mode::Fault);}assert(state.mode==hx::Mode::Ready&&oeLevel==LOW);
 const auto stand=hx::standPose(config::geometry,config::gait).pose;assert(std::abs(axes[1].angle-stand.hip)<1e-5);assert(std::abs(axes[2].angle-stand.knee)<1e-5);
 command("WALK",6000);assert(state.mode==hx::Mode::Walking);
 for(int t=6020;t<=60000;t+=20){fakeMillis=t;if(t%200==0)command("PING",t);loop();if(state.mode!=hx::Mode::Walking){std::cerr<<"At t="<<t<<" "<<Serial.output;return 1;}unsigned lifted=0;for(int leg=0;leg<6;++leg){assert(hx::allowed(config::geometry,{axes[leg*3].angle,axes[leg*3+1].angle,axes[leg*3+2].angle}));lifted+=currentFoot(leg).z>config::gait.standZ+.25;}if(lifted>1){std::cerr<<"Support at t="<<t<<":";for(unsigned l=0;l<6;++l)std::cerr<<" "<<currentFoot(l).z-config::gait.standZ;std::cerr<<"\n";return 1;}}
 hx::Vec3 stopped[6];for(unsigned l=0;l<6;++l)stopped[l]=currentFoot(l);command("STOP",60000);assert(state.mode==hx::Mode::Ready);
 for(int t=60020;t<=65000;t+=20){fakeMillis=t;if(t%200==0)command("PING",t);loop();assert(state.mode==hx::Mode::Ready);}
 for(unsigned l=0;l<6;++l){auto f=currentFoot(l);assert(std::abs(f.x-stopped[l].x)<1e-5);assert(std::abs(f.y-stopped[l].y)<1e-5);assert(std::abs(f.z-config::gait.standZ)<1e-5);}
 command("WALK",65000);assert(state.mode==hx::Mode::Walking);for(int t=65020;t<=92000;t+=20){fakeMillis=t;if(t%200==0)command("PING",t);loop();assert(state.mode==hx::Mode::Walking);unsigned raised=0;for(unsigned l=0;l<6;++l)raised+=currentFoot(l).z>config::gait.standZ+.25;assert(raised<=1);}command("DISARM",92000);assert(oeLevel==HIGH&&state.mode==hx::Mode::Disabled);
 std::cout<<"Simulated E2E passed:5s ramp,54s WALK incl18s preposition,5s STOP with planted XY preserved,27s restart,DISARM. Physical validation not performed.\n";
}
