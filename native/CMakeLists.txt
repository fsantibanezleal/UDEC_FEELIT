cmake_minimum_required(VERSION 3.21)

project(feelit_bridge_probe LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/out")

add_executable(feelit_bridge_probe
  src/feelit_bridge_probe.cpp
)

target_compile_definitions(feelit_bridge_probe PRIVATE
  FEELIT_BRIDGE_DEFAULT_BACKEND="${FEELIT_BRIDGE_DEFAULT_BACKEND}"
  FEELIT_VENDOR_SDK_ROOT="${FEELIT_VENDOR_SDK_ROOT}"
)

if (MSVC)
  target_compile_options(feelit_bridge_probe PRIVATE /W4)
else()
  target_compile_options(feelit_bridge_probe PRIVATE -Wall -Wextra -Wpedantic)
endif()
