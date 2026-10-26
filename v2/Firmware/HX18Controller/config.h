#pragma once
#include "robot_core.h"
namespace config {
constexpr int sda=22,scl=20,oe=27; // Adafruit Feather ESP32 V2 ONLY.
constexpr uint8_t addresses[2]={0x40,0x41};
constexpr double oscillatorHz[2]={25000000,25000000};
constexpr bool oscillatorVerified[2]={false,false};
constexpr bool calibrationReviewed=false;
constexpr hx::Geometry geometry{};
constexpr hx::GaitConfig gait{};
// CAD L1 yaw,hip,knee ... L6. Every sign/zero/end-point requires physical measurement.
constexpr hx::Calibration servos[18]={
 {1500,10,0,1,1200,1800,false},{1500,10,0,1,1200,1800,false},{1500,10,0,1,1200,1800,false},
 {1500,10,0,1,1200,1800,false},{1500,10,0,1,1200,1800,false},{1500,10,0,1,1200,1800,false},
 {1500,10,0,1,1200,1800,false},{1500,10,0,1,1200,1800,false},{1500,10,0,1,1200,1800,false},
 {1500,10,0,1,1200,1800,false},{1500,10,0,1,1200,1800,false},{1500,10,0,1,1200,1800,false},
 {1500,10,0,1,1200,1800,false},{1500,10,0,1,1200,1800,false},{1500,10,0,1,1200,1800,false},
 {1500,10,0,1,1200,1800,false},{1500,10,0,1,1200,1800,false},{1500,10,0,1,1200,1800,false}
};
constexpr bool batteryEnabled=false;
constexpr int batteryPin=34; // A2 / ADC1 on FeatherV2.
constexpr double batteryDividerRatio=0,batteryMinimumVolts=0;
static_assert(!batteryEnabled||(batteryDividerRatio>1&&batteryMinimumVolts>0),"Validate divider and threshold before enabling ADC battery monitoring.");
}
