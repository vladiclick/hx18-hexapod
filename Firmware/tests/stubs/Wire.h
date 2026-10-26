#pragma once
#include <cstddef>
#include <cstdint>
#include <vector>
struct FakeWire {bool fail=false;std::vector<std::vector<uint8_t>> writes;std::vector<uint8_t> current;void setTimeOut(int){}size_t setBufferSize(size_t n){return n;}bool begin(int,int,int){return !fail;}void beginTransmission(uint8_t a){current={a};}size_t write(uint8_t v){current.push_back(v);return 1;}uint8_t endTransmission(){writes.push_back(current);return fail?4:0;}};
inline FakeWire Wire;
