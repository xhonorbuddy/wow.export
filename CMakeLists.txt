cmake_minimum_required(VERSION 3.21)
project(wow_export LANGUAGES NONE)

# Keep the Bun/NW.js pipeline and expose it alongside Blender's C++ helper.
option(WOW_EXPORT_NATIVE_GEOMETRY "Build the Windows x64 Blender geometry parser" ${WIN32})
set(WOW_EXPORT_APP_BUILD "win-x64-debug" CACHE STRING "Build name from build.json")
find_program(BUN_EXECUTABLE NAMES bun HINTS "$ENV{USERPROFILE}/.bun/bin" "$ENV{HOME}/.bun/bin")

if(WOW_EXPORT_NATIVE_GEOMETRY)
    if(NOT WIN32)
        message(FATAL_ERROR "The optional native Blender parser requires Windows.")
    endif()
    enable_language(CXX)
    if(NOT CMAKE_SIZEOF_VOID_P EQUAL 8)
        message(FATAL_ERROR "The Blender geometry parser requires a 64-bit compiler.")
    endif()
    add_subdirectory(addons/blender/native)
endif()

add_custom_target(wow_export_app
    COMMAND "${CMAKE_COMMAND}"
        "-DBUN_EXECUTABLE=${BUN_EXECUTABLE}"
        "-DAPP_BUILD=${WOW_EXPORT_APP_BUILD}"
        "-DSOURCE_DIR=${CMAKE_CURRENT_SOURCE_DIR}"
        -P "${CMAKE_CURRENT_SOURCE_DIR}/cmake/BuildApp.cmake"
    WORKING_DIRECTORY "${CMAKE_CURRENT_SOURCE_DIR}"
    COMMENT "Building wow.export ${WOW_EXPORT_APP_BUILD} with Bun"
    USES_TERMINAL
    VERBATIM
)
if(TARGET native_geometry)
    add_dependencies(wow_export_app native_geometry)
endif()
