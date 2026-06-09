"""Export decompiled pseudo-C functions from the current Ghidra program.

This script runs inside Ghidra's Python environment, not normal CPython.
It writes raw extraction output only: no labels, cleaning, or classification.
"""

import csv
import os
import sys

from ghidra.app.decompiler import DecompInterface


def get_output_path():
    args = getScriptArgs()
    if len(args) < 1:
        raise ValueError("Missing output CSV path argument.")
    return args[0]


def decompile_function(decompiler, function):
    result = decompiler.decompileFunction(function, 60, monitor)
    if result.decompileCompleted():
        decompiled = result.getDecompiledFunction()
        if decompiled is None:
            return "", "failed: no decompiled function returned"
        return decompiled.getC(), "success"

    error_message = result.getErrorMessage()
    if not error_message:
        error_message = "unknown decompilation failure"
    return "", "failed: " + str(error_message)


def open_csv_for_write(output_path):
    if sys.version_info[0] >= 3:
        return open(output_path, "w", newline="", encoding="utf-8")
    return open(output_path, "wb")


def main():
    output_path = get_output_path()
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    binary_name = currentProgram.getName()
    function_manager = currentProgram.getFunctionManager()
    functions = function_manager.getFunctions(True)

    decompiler = DecompInterface()
    decompiler.openProgram(currentProgram)

    total_functions = 0
    successful_decompilations = 0
    failed_decompilations = 0

    with open_csv_for_write(output_path) as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(
            [
                "binary_name",
                "function_name",
                "function_address",
                "function_code",
                "decompile_status",
            ]
        )

        for function in functions:
            total_functions += 1

            function_name = function.getName()
            function_address = str(function.getEntryPoint())

            try:
                function_code, decompile_status = decompile_function(
                    decompiler, function
                )
            except Exception as error:
                function_code = ""
                decompile_status = "failed: " + str(error)

            if decompile_status == "success":
                successful_decompilations += 1
            else:
                failed_decompilations += 1

            writer.writerow(
                [
                    binary_name,
                    function_name,
                    function_address,
                    function_code,
                    decompile_status,
                ]
            )

    print("Ghidra function extraction complete.")
    print("Output CSV: " + output_path)
    print("Total functions: " + str(total_functions))
    print("Successful decompilations: " + str(successful_decompilations))
    print("Failed decompilations: " + str(failed_decompilations))

    decompiler.dispose()


main()
