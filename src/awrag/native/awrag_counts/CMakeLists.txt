cmake_minimum_required(VERSION 3.24)

project(awrag_counts LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

add_executable(awrag-counts
    src/awrag_counts.cpp
)

if(MSVC)
    target_compile_options(awrag-counts PRIVATE /W4 /permissive-)
else()
    target_compile_options(awrag-counts PRIVATE -Wall -Wextra -Wpedantic)
endif()
