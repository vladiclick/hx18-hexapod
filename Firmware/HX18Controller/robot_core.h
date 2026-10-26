#pragma once
#include <algorithm>
#include <cmath>
#include <cstdint>
namespace hx {
constexpr double pi=3.14159265358979323846;
inline double rad(double d){return d*pi/180.;}
inline double deg(double r){return r*180./pi;}
struct Geometry {double coxa=30,femur=42,tibia=80,lateral=13.5,hipNeutral=-25,kneeNeutral=-70,maxYaw=25,maxHip=15,maxKnee=15,maxLever=35;};
struct Vec3 {double x=0,y=0,z=0;};
struct Pose {double yaw=0,hip=0,knee=0;}; // CAD offsets; knee neutral is RELATIVE -70deg.
struct Solve {bool ok=false;Pose pose{};};
inline bool finite(Vec3 p){return std::isfinite(p.x)&&std::isfinite(p.y)&&std::isfinite(p.z);}
inline bool finite(Pose p){return std::isfinite(p.yaw)&&std::isfinite(p.hip)&&std::isfinite(p.knee);}
inline Vec3 forward(const Geometry& g,Pose p){
 const double a=rad(-p.yaw),h=rad(g.hipNeutral+p.hip),k=rad(g.kneeNeutral+p.knee);
 const double r=g.coxa+g.femur*std::cos(h)+g.tibia*std::cos(h+k);
 return {r*std::cos(a)-g.lateral*std::sin(a),r*std::sin(a)+g.lateral*std::cos(a),g.femur*std::sin(h)+g.tibia*std::sin(h+k)};
}
inline Solve inverse(const Geometry& g,Vec3 p){
 if(!finite(p)||g.femur<=0||g.tibia<=0||g.coxa<=0)return {};
 const double rr=p.x*p.x+p.y*p.y-g.lateral*g.lateral;if(rr<=0)return {};
 const double r=std::sqrt(rr),x=r-g.coxa;
 const double cosine=(x*x+p.z*p.z-g.femur*g.femur-g.tibia*g.tibia)/(2*g.femur*g.tibia);
 if(cosine < -1 || cosine > 1)return {};
 const double k=-std::acos(std::clamp(cosine,-1.,1.));
 const double h=std::atan2(p.z,x)-std::atan2(g.tibia*std::sin(k),g.femur+g.tibia*std::cos(k));
 return {true,{-deg(std::atan2(p.y,p.x)-std::atan2(g.lateral,r)),deg(h)-g.hipNeutral,deg(k)-g.kneeNeutral}};
}
inline bool allowed(const Geometry& g,Pose p){
 if(!finite(p)||std::abs(p.yaw)>g.maxYaw||std::abs(p.hip)>g.maxHip||std::abs(p.knee)>g.maxKnee)return false;
 const double h=rad(g.hipNeutral+p.hip),k=rad(g.kneeNeutral+p.knee);
 return std::hypot(g.femur*std::cos(h)+g.tibia*std::cos(h+k),g.lateral)<=g.maxLever;
}
inline double quintic(double u){u=std::clamp(u,0.,1.);return u*u*u*(10+u*(-15+6*u));}
struct GaitConfig {double strideHalf=6,lift=6,period=18,standHipX=25,standZ=-97.44554284044901;};
struct GaitTarget {bool ok=false;bool swinging=false;Pose pose{};};
inline Solve standPose(const Geometry& g,const GaitConfig& c){return inverse(g,{g.coxa+c.standHipX,g.lateral,c.standZ});}
inline GaitTarget crawlTarget(const Geometry& g,const GaitConfig& c,unsigned leg,double seconds){
 if(leg>=6||!std::isfinite(seconds)||seconds<0||c.period<=0||c.strideHalf<0||c.lift<0)return {};
 constexpr unsigned slot[6]={0,2,4,1,3,5}; // L1,L4,L2,L5,L3,L6.
 const double slots=std::fmod(seconds/c.period,1.)*6;
 const unsigned activeSlot=std::min(5U,static_cast<unsigned>(slots));
 double position=slots-slot[leg];if(position<0)position+=6;
 const double phase=position/6.;const bool swinging=slot[leg]==activeSlot;
 double shift=0,lift=0;
 if(swinging){const double u=phase*6;const double q=1.2*quintic(u)-.2*u;shift=-c.strideHalf+2*c.strideHalf*q;lift=c.lift*64*u*u*u*(1-u)*(1-u)*(1-u);}
 else {const double u=(phase-1./6.)*6./5.;shift=c.strideHalf-2*c.strideHalf*u;}
 const double root=rad(leg*60.);
 const auto s=inverse(g,{g.coxa+c.standHipX+shift*std::sin(root),g.lateral+shift*std::cos(root),c.standZ+lift});
 return {s.ok&&allowed(g,s.pose),swinging,s.pose};
}
inline double startupClock(double seconds){
 const double u=std::clamp(seconds/3.,0.,1.);
 return seconds<=3 ? 3*(2.5*u*u*u*u-3*u*u*u*u*u+u*u*u*u*u*u) : seconds-1.5;
}
inline GaitTarget prepositionTarget(const Geometry& g,const GaitConfig& c,unsigned leg,double seconds,Vec3 initial){
 if(leg>=6||!std::isfinite(seconds)||seconds<0||!finite(initial)||c.period<=0)return {};
 constexpr unsigned slot[6]={0,2,4,1,3,5};
 const auto goal=crawlTarget(g,c,leg,0);if(!goal.ok)return {};
 const auto end=forward(g,goal.pose);const double u=std::clamp(seconds/(c.period/6)-slot[leg],0.,1.);
 const double q=quintic(u),lift=c.lift*64*u*u*u*(1-u)*(1-u)*(1-u);
 const auto s=inverse(g,{initial.x+q*(end.x-initial.x),initial.y+q*(end.y-initial.y),initial.z+q*(c.standZ-initial.z)+lift});
 return {s.ok&&allowed(g,s.pose),u>0&&u<1,s.pose};
}
struct Calibration {double centerUs=1500,usPerDegree=10,offsetDegrees=0;int sign=1;double minimumUs=1200,maximumUs=1800;bool verified=false;};
inline bool valid(const Calibration& c){return c.verified&&std::isfinite(c.centerUs)&&std::isfinite(c.usPerDegree)&&std::isfinite(c.offsetDegrees)&&(c.sign==1||c.sign==-1)&&c.usPerDegree>0&&c.minimumUs>=1000&&c.maximumUs<=2000&&c.minimumUs<c.centerUs&&c.centerUs<c.maximumUs;}
struct Pulse {bool ok=false;uint16_t microseconds=0;};
inline Pulse pulse(const Calibration& c,double delta){
 if(!valid(c)||!std::isfinite(delta))return {};
 const double us=c.centerUs+c.sign*c.usPerDegree*(delta+c.offsetDegrees);
 if(us<c.minimumUs||us>c.maximumUs)return {};
 return {true,static_cast<uint16_t>(std::lround(us))};
}
inline bool validOscillator(double hz,bool verified){return verified&&std::isfinite(hz)&&hz>=20000000&&hz<=30000000;}
inline uint16_t pulseTicks(double microseconds,double hz){
 if(!validOscillator(hz,true)||!std::isfinite(microseconds)||microseconds<0||microseconds>20000)return 0;
 return static_cast<uint16_t>(std::clamp(std::lround(microseconds*hz/(122.*1e6)),0L,4095L));
}
struct Slew {double angle=0,velocity=0;};
inline Slew slew(Slew previous,double target,double dt,double maxSpeed=12,double maxAcceleration=30){
 if(!std::isfinite(target)||dt<=0||dt>.1)return previous;
 const double error=target-previous.angle;
 if(std::abs(error)<1e-8&&std::abs(previous.velocity)<=maxAcceleration*dt)return {target,0};
 const double direction=error>0?1.:-1.,braking=maxAcceleration*dt;
 const double desired=direction*std::min(maxSpeed,std::sqrt(braking*braking+2*maxAcceleration*std::abs(error))-braking);
 const double v=std::clamp(desired,previous.velocity-maxAcceleration*dt,previous.velocity+maxAcceleration*dt),step=v*dt;
 if(step*direction>=std::abs(error)&&std::abs(previous.velocity)<=maxAcceleration*dt)return {target,0};
 return {previous.angle+step,v};
}
enum class Mode {Disabled,Ramping,Ready,Walking,Fault};
struct State {Mode mode=Mode::Disabled;bool acknowledged=false;uint32_t since=0,lastCommand=0;};
struct Transition {bool accepted=false;State state{};};
inline State acknowledge(State s){if(s.mode==Mode::Disabled)s.acknowledged=true;return s;}
inline Transition arm(State s,uint32_t now,bool calibrated){if(s.mode!=Mode::Disabled||!s.acknowledged||!calibrated)return {false,s};return {true,{Mode::Ramping,true,now,now}};}
inline State heartbeat(State s,uint32_t now){s.lastCommand=now;return s;}
inline State disarm(State){return {};}
inline State advance(State s,uint32_t now,bool bus,bool battery){
 if(s.mode==Mode::Disabled||s.mode==Mode::Fault)return s;
 if(!bus||!battery||uint32_t(now-s.lastCommand)>1500)return {Mode::Fault,false,now,now};
 if(s.mode==Mode::Ramping&&uint32_t(now-s.since)>=5000)s.mode=Mode::Ready;return s;
}
inline Transition startWalk(State s,uint32_t now){if(s.mode!=Mode::Ready)return {false,s};return {true,{Mode::Walking,s.acknowledged,now,now}};}
inline State stopWalk(State s,uint32_t now){if(s.mode==Mode::Walking)return {Mode::Ready,s.acknowledged,now,now};return s;}
struct Channel {bool ok=true;uint8_t board=0,channel=0;};
inline Channel channel(unsigned servo){if(servo>=18)return {false,0,0};return {true,static_cast<uint8_t>(servo/9),static_cast<uint8_t>(servo%9)};}
} // namespace hx
