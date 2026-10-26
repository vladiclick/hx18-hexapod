#!/bin/sh
set -eu
cd "$(dirname "$0")"
mkdir -p build/calibrated-fixture
clang++ -std=c++17 -Wall -Wextra -Werror -fsanitize=address,undefined tests/core_test.cpp -o build/core-test
./build/core-test
clang++ -std=c++17 -Wall -Wextra -Werror -fsanitize=address,undefined -Itests/stubs tests/controller_test.cpp -o build/controller-test
./build/controller-test
cp HX18Controller/controller.cpp HX18Controller/robot_core.h build/calibrated-fixture/
sed 's/calibrationReviewed=false/calibrationReviewed=true/;s/oscillatorVerified\[2\]={false,false}/oscillatorVerified[2]={true,true}/;s/,false}/,true}/g' HX18Controller/config.h > build/calibrated-fixture/config.h
clang++ -std=c++17 -Wall -Wextra -Werror -fsanitize=address,undefined -Itests/stubs tests/controller_armed_test.cpp -o build/controller-armed-test
./build/controller-armed-test
if command -v xcrun >/dev/null 2>&1;then
 clang++ -std=c++17 -fprofile-instr-generate -fcoverage-mapping tests/core_test.cpp -o build/core-coverage
 LLVM_PROFILE_FILE=build/core.profraw ./build/core-coverage
 xcrun llvm-profdata merge -sparse build/core.profraw -o build/core.profdata
 xcrun llvm-cov report build/core-coverage -instr-profile=build/core.profdata HX18Controller/robot_core.h | tee build/coverage.txt
fi
if [ -n "${HX18_ARDUINO_CLI:-}" ];then
 if [ -n "${HX18_ARDUINO_CONFIG:-}" ];then "$HX18_ARDUINO_CLI" compile --config-file "$HX18_ARDUINO_CONFIG" --fqbn esp32:esp32:adafruit_feather_esp32_v2 --build-path build/esp32 HX18Controller
 else "$HX18_ARDUINO_CLI" compile --fqbn esp32:esp32:adafruit_feather_esp32_v2 --build-path build/esp32 HX18Controller;fi
fi
