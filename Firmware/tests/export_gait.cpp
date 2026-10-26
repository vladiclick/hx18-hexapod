#include "../HX18Controller/robot_core.h"
#include <iostream>
int main(int argc,char**){
 hx::Geometry g;hx::GaitConfig c;
 std::cout<<"seconds,leg,yaw_deg,hip_deg,knee_deg,x_mm,y_mm,z_mm,swinging\n";
 for(int frame=0;frame<=(argc>1?600:300);++frame){const double t=frame*c.period/300.;
  for(unsigned leg=0;leg<6;++leg){const auto s=argc>1&&t<c.period?hx::prepositionTarget(g,c,leg,t,hx::forward(g,hx::standPose(g,c).pose)):hx::crawlTarget(g,c,leg,argc>1?hx::startupClock(t-c.period):t);
   if(!s.ok)return 1;const auto f=hx::forward(g,s.pose);
   std::cout<<t<<','<<leg+1<<','<<s.pose.yaw<<','<<s.pose.hip<<','<<s.pose.knee<<','<<f.x<<','<<f.y<<','<<f.z<<','<<s.swinging<<'\n';
  }
 }
}
