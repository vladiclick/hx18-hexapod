#pragma once
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <string>
#include <vector>
#include <type_traits>
constexpr int HIGH=1,LOW=0,OUTPUT=1;
inline uint32_t fakeMillis=0;inline int oeLevel=HIGH;
inline uint32_t millis(){return fakeMillis;}
inline void digitalWrite(int,int v){oeLevel=v;}
inline void pinMode(int,int){}
inline uint32_t analogReadMilliVolts(int){return 0;}
struct FakeSerial {std::string input,output;void begin(int){}int available(){return int(input.size());}int read(){int c=input[0];input.erase(0,1);return c;}template<class T>void print(T v){if constexpr(std::is_convertible_v<T,std::string>)output+=v;else output+=std::to_string(v);}template<class T>void println(T v){print(v);output+='\n';}};
inline FakeSerial Serial;
