if(NOT BUN_EXECUTABLE OR NOT EXISTS "${BUN_EXECUTABLE}")
    message(FATAL_ERROR "Bun was not found. Install Bun 1.2+ and reconfigure, or set BUN_EXECUTABLE to bun.exe.")
endif()
execute_process(
    COMMAND "${BUN_EXECUTABLE}" build.js "${APP_BUILD}" --local
    WORKING_DIRECTORY "${SOURCE_DIR}"
    RESULT_VARIABLE result
)
if(NOT result STREQUAL "0")
    message(FATAL_ERROR "wow.export app build failed: ${result}")
endif()
