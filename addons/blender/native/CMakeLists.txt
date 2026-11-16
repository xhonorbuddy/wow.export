add_library(native_geometry SHARED geometry.cpp)
target_compile_features(native_geometry PRIVATE cxx_std_20)
set_target_properties(native_geometry PROPERTIES
    CXX_EXTENSIONS OFF
    MSVC_RUNTIME_LIBRARY "MultiThreaded$<$<CONFIG:Debug>:Debug>"
)
if(MSVC)
    target_compile_options(native_geometry PRIVATE /W4 /EHsc)
    target_compile_definitions(native_geometry PRIVATE _CRT_SECURE_NO_WARNINGS)
endif()

# The ctypes wrapper loads the helper from beside native_geometry.py.
add_custom_command(TARGET native_geometry POST_BUILD
    COMMAND "${CMAKE_COMMAND}" -E copy_if_different
        "$<TARGET_FILE:native_geometry>"
        "${CMAKE_CURRENT_SOURCE_DIR}/../io_scene_wowobj/$<TARGET_FILE_NAME:native_geometry>"
    COMMENT "Installing native_geometry.dll into the Blender addon"
    VERBATIM
)
