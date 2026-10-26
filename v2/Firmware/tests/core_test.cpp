#include "../HX18Controller/robot_core.h"
#include <cassert>
#include <iostream>
using namespace hx;
static bool near(double a,double b,double e=1e-6){return std::abs(a-b)<e;}
int main(){
 Geometry g;Pose neutral{};const auto foot=forward(g,neutral);
 assert(near(foot.x,61.09246763572664));assert(near(foot.y,13.5));assert(near(foot.z,-97.44554284044901));
 for(double y:{-25.,0.,25.})for(double h:{-15.,0.,15.})for(double k:{-15.,0.,15.}){Pose p{y,h,k};auto v=inverse(g,forward(g,p));assert(v.ok);assert(near(v.pose.yaw,y));assert(near(v.pose.hip,h));assert(near(v.pose.knee,k));}
 for(Vec3 p: {Vec3{1000,0,0},Vec3{0,0,0},Vec3{NAN,0,0}})assert(!inverse(g,p).ok);
 for(int kind=0;kind<3;++kind){Geometry b=g;if(kind==0)b.femur=0;if(kind==1)b.tibia=0;if(kind==2)b.coxa=0;assert(!inverse(b,foot).ok);}
 assert(allowed(g,neutral));for(Pose p:{Pose{26,0,0},Pose{0,16,0},Pose{0,0,16},Pose{0,0,15},Pose{NAN,0,0},Pose{0,NAN,0},Pose{0,0,NAN}})assert(!allowed(g,p));
 assert(near(quintic(0),0));assert(near(quintic(1),1));assert(near(quintic(.5),.5));
 GaitConfig gc;assert(standPose(g,gc).ok);
 for(int t=0;t<60000;++t){unsigned active=0;for(unsigned leg=0;leg<6;++leg){auto v=crawlTarget(g,gc,leg,t*.001);assert(v.ok&&allowed(g,v.pose));active+=v.swinging;}assert(active==1);}
 for(double t:{.7,3.1,7.3,11.7})for(unsigned leg=0;leg<6;++leg){auto a=crawlTarget(g,gc,leg,t),b=crawlTarget(g,gc,leg,t+.0001);if(!a.swinging&&!b.swinging){auto fa=forward(g,a.pose),fb=forward(g,b.pose);double root=rad(leg*60.);assert(near(((fb.x-fa.x)*std::sin(root)+(fb.y-fa.y)*std::cos(root))/.0001,-2*gc.strideHalf/(gc.period*5./6),1e-5));}}
 for(int frame=0;frame<=18000;++frame){unsigned active=0;for(unsigned leg=0;leg<6;++leg){auto v=prepositionTarget(g,gc,leg,frame*.001,forward(g,standPose(g,gc).pose));assert(v.ok);active+=v.swinging;}assert(active<=1);}
 assert(near(startupClock(0),0));assert(near(startupClock(3),1.5));assert(near(startupClock(4),2.5));
 assert(!crawlTarget(g,gc,6,0).ok);assert(!crawlTarget(g,gc,0,NAN).ok);assert(!crawlTarget(g,gc,0,-1).ok);
 for(int kind=0;kind<5;++kind){GaitConfig b;if(kind==0)b.period=0;if(kind==1)b.strideHalf=-1;if(kind==2)b.lift=-1;if(kind==3)b.strideHalf=100;if(kind==4)b.standZ=-1000;assert(!crawlTarget(g,b,0,.1).ok);}
 assert(!prepositionTarget(g,gc,6,0,foot).ok);assert(!prepositionTarget(g,gc,0,-1,foot).ok);assert(!prepositionTarget(g,gc,0,NAN,foot).ok);assert(!prepositionTarget(g,gc,0,0,{NAN,0,0}).ok);GaitConfig bad=gc;bad.period=0;assert(!prepositionTarget(g,bad,0,0,foot).ok);bad=gc;bad.standZ=-1000;assert(!prepositionTarget(g,bad,0,0,foot).ok);
 Calibration c;assert(!valid(c));c.verified=true;assert(valid(c));assert(pulse(c,0).microseconds==1500);assert(pulse(c,5).microseconds==1550);c.sign=-1;assert(pulse(c,5).microseconds==1450);c.offsetDegrees=2;assert(pulse(c,5).microseconds==1430);assert(!pulse(c,40).ok);assert(!pulse(c,-40).ok);assert(!pulse(c,NAN).ok);
 for(int k=0;k<10;++k){Calibration b;b.verified=true;if(k==0)b.centerUs=NAN;if(k==1)b.usPerDegree=NAN;if(k==2)b.offsetDegrees=NAN;if(k==3)b.usPerDegree=0;if(k==4)b.minimumUs=900;if(k==5)b.maximumUs=2100;if(k==6)b.minimumUs=1500;if(k==7)b.maximumUs=1500;if(k==8)b.sign=2;if(k==9)b.sign=0;assert(!valid(b));assert(!pulse(b,0).ok);}
 assert(validOscillator(25000000,true));assert(!validOscillator(25000000,false));for(double f:{0.,-1.,double(NAN),19000000.,31000000.}){assert(!validOscillator(f,true));assert(pulseTicks(1500,f)==0);}
 assert(pulseTicks(NAN,25000000)==0);assert(pulseTicks(-1,25000000)==0);assert(pulseTicks(20001,25000000)==0);assert(pulseTicks(1500,25000000)==307);assert(pulseTicks(0,25000000)==0);assert(pulseTicks(20000,25000000)==4095);
 Slew s{};auto n=slew(s,10,.02);assert(n.angle>0&&n.angle<=.012001);assert(n.velocity<=.600001);
 for(int i=0;i<1000;++i){auto next=slew(s,10,.02);assert(std::abs(next.velocity-s.velocity)<=.600001);assert(std::abs(next.velocity)<=12.000001);s=next;}assert(near(s.angle,10));assert(near(s.velocity,0));assert(slew(s,NAN,.02).angle==s.angle);assert(slew(s,20,-1).angle==s.angle);assert(slew(s,20,.3).angle==s.angle);
 State st;assert(st.mode==Mode::Disabled);assert(!arm(st,0,false).accepted);assert(!arm(st,0,true).accepted);st=acknowledge(st);auto ar=arm(st,0,true);assert(ar.accepted);st=ar.state;assert(!startWalk(st,100).accepted);st=heartbeat(st,2000);st=advance(st,3000,true,true);assert(st.mode==Mode::Ramping);st=heartbeat(st,4000);st=advance(st,5000,true,true);assert(st.mode==Mode::Ready);auto w=startWalk(st,5000);assert(w.accepted);auto hold=stopWalk(w.state,5001);assert(hold.mode==Mode::Ready);assert(disarm(hold).mode==Mode::Disabled);
 assert(advance(w.state,6600,true,true).mode==Mode::Fault);assert(advance(hold,5002,false,true).mode==Mode::Fault);assert(advance(hold,5002,true,false).mode==Mode::Fault);assert(!arm(advance(hold,5002,false,true),5003,true).accepted);assert(advance(State{},50000,false,false).mode==Mode::Disabled);assert(advance(advance(hold,5002,false,true),8000,true,true).mode==Mode::Fault);assert(stopWalk(State{},42).mode==Mode::Disabled);assert(acknowledge(hold).acknowledged);
 st=arm(acknowledge(State{}),0xFFFFFF00U,true).state;st=heartbeat(st,100);assert(advance(st,200,true,true).mode==Mode::Ramping);
 assert(channel(0).board==0&&channel(0).channel==0);assert(channel(17).board==1&&channel(17).channel==8);assert(!channel(18).ok);
 std::cout<<"Core passed: FK/IK,360000 gait targets,108006 preposition targets, common stance velocity, slew acceleration, calibration/safety.\n";
}
