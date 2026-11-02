cmake_minimum_required(VERSION 3.22)
project(abs662_bridge C CXX ASM)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)
get_filename_component(ABS662_ROOT "${CMAKE_CURRENT_SOURCE_DIR}/.." ABSOLUTE)
add_compile_options("-ffile-prefix-map=${ABS662_ROOT}=." "-fdebug-prefix-map=${ABS662_ROOT}=.")

set(DYNARMIC_SRC "" CACHE PATH "dynarmic source tree")
set(ABSW_GEN_DIR "${CMAKE_CURRENT_SOURCE_DIR}/gen" CACHE PATH "generated sources")
option(ABSW_TRACE "Log every import call" OFF)

set(DYNARMIC_USE_BUNDLED_EXTERNALS ON CACHE BOOL "" FORCE)
set(DYNARMIC_TESTS OFF CACHE BOOL "" FORCE)
set(DYNARMIC_FRONTENDS "A32" CACHE STRING "" FORCE)
set(DYNARMIC_WARNINGS_AS_ERRORS OFF CACHE BOOL "" FORCE)
set(DYNARMIC_USE_PRECOMPILED_HEADERS OFF CACHE BOOL "" FORCE)
add_subdirectory(${DYNARMIC_SRC} dynarmic EXCLUDE_FROM_ALL)

add_library(AngryBirdsSeasonsFull SHARED
    ${ABSW_GEN_DIR}/engine_blob.S
    src/arena.cpp
    src/bridge.cpp
    src/cpu.cpp
    src/display.cpp
    src/elf32.cpp
    src/gheap.c
    src/hint.cpp
    src/hle.cpp
    src/hle_android.cpp
    src/hle_gles.cpp
    src/hle_libc.cpp
    src/hle_pthread.cpp
    src/hle_stdio.cpp
    src/jni_bridge.cpp
    src/perf.cpp
)
target_include_directories(AngryBirdsSeasonsFull PRIVATE src ${ABSW_GEN_DIR})
target_compile_definitions(AngryBirdsSeasonsFull PRIVATE ABSW_TRACE=$<BOOL:${ABSW_TRACE}>)
target_compile_options(AngryBirdsSeasonsFull PRIVATE -fvisibility=hidden $<$<COMPILE_LANGUAGE:C>:-w>)
target_link_libraries(AngryBirdsSeasonsFull PRIVATE dynarmic GLESv2 android log)
target_link_options(AngryBirdsSeasonsFull PRIVATE -Wl,--exclude-libs,ALL -Wl,--gc-sections)
