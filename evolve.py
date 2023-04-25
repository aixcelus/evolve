#!/usr/bin/env python3

################################################################################
#                          aiXcel.us API Integration License                   #
#                    Copyright (c) 2023, aiXcelus www.aixcel.us                #
#                                                                              #
# Permission is hereby granted, free of charge, to any person obtaining a copy #
# of this software and associated documentation files (the "Software"), to use,#
# copy, modify, and distribute the Software, subject to the following          #
# conditions:                                                                  #
#                                                                              #
# 1. The Software may only be used for the purpose of integrating the          #
#    aiXcel.us API into the licensee's products.                               #
# 2. The licensee is prohibited from modifying the Software to use an API or   #
#    service from a competing provider, whether commercial or non-commercial.  #
# 3. Redistributions of the Software must retain the above copyright notice    #
#    and this permission notice.                                               #
# 4. THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS   #
#    OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF                #
#    MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, NONINFRINGEMENT, AND  #
#    THE AVAILABILITY OR RELIABILITY OF THE API. IN NO EVENT SHALL THE AUTHORS #
#    OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, #
#    INCLUDING BUT NOT LIMITED TO DOWNTIME, ERRORS, OR INACCURACIES IN THE     #
#    API, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,   #
#    OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN #
#    THE SOFTWARE.                                                             #
# 5. The use of the aiXcel.us API is subject to the terms and conditions of    #
#    the licensee's account license with aiXcel.us, which can be found at      #
#    https://www.aixcel.us/tos.html.                                           #
#                                                                              #
# This license does not grant permission to use the trade names, trademarks,  #
# service marks, or product names of aiXcel.us, except as required for         #
# reasonable and customary use in describing the origin of the Software.       #
# By using the Software, the licensee agrees to be bound by the terms and      #
# conditions of this license.                                                  #
################################################################################

import os
import sys
import requests
import shutil
import re
import pty
import queue
import shutil
import mimetypes

# Define the endpoint URL
URL = "https://aixcel.us/api/v1/evolve"

mime_type_interpreter_map = {
    "text/x-python": "python3",
    "text/x-shellscript": "bash",
    "text/x-perl": "perl",
    "text/x-ruby": "ruby",
    "text/javascript": "node",
    "application/x-php": "php",
    "text/x-csrc": "gcc",
    "text/x-c++src": "g++",
    "text/x-java": "java",
    "text/x-csharp": "csc",
    "text/x-fortran": "gfortran",
    "text/x-go": "go",
    "text/x-rustsrc": "rustc",
    "text/x-scala": "scala",
    "text/x-swift": "swift",
    "text/x-d": "dmd",
    "text/x-dylan": "dylan-compiler",
    "text/x-erlang": "erlc",
    "text/x-haskell": "ghc",
    "text/x-lisp": "sbcl",
    "text/x-lua": "lua",
    "text/x-objectivec": "clang",
    "text/x-objectivec++": "clang++",
    "text/x-pascal": "fpc",
    "text/x-prolog": "swipl",
    "text/x-r": "Rscript",
    "text/x-scheme": "guile",
    "text/x-tcl": "tclsh",
    "text/x-vb": "vbc",
    "text/x-ada": "gnatmake",
    "text/x-asm": "nasm",
    "text/x-cobol": "cobc",
    "text/x-diff": "diff",
    "text/x-dockerfile": "docker",
    "text/x-elixir": "elixir",
    "text/x-elm": "elm",
    "text/x-erlang": "erlc",
    "text/x-fsharp": "fsharpc",
    "text/x-haskell": "ghc",
    "text/x-ini": "ini",
    "text/x-julia": "julia",
    "text/x-kotlin": "kotlinc",
    "text/x-lua": "lua",
    "text/x-matlab": "matlab",
    "text/x-ocaml": "ocaml",
    "text/x-pascal": "fpc",
    "text/x-powershell": "pwsh",
    "text/x-rustsrc": "rustc",
    "text/x-sass": "sass",
    "text/x-scss": "sass",
    "text/x-sql": "sqlite3",
    "text/x-toml": "toml",
    "text/x-vb": "vbc",
    "text/x-yaml": "yml"
}

def check_for_errors(data_queue):
    error_patterns = [
        r'error',
        r'invalid',
    ]
    data = "".join(list(data_queue.queue))
    for pattern in error_patterns:
        if re.search(pattern, data, re.IGNORECASE):  # Use the re.IGNORECASE flag
            return True
    return False


def is_executable(script_path):
    return os.access(script_path, os.X_OK)

def wrap_script_in_markdown(script_content):
    return f"```\n{script_content}```"

def extract_script_from_markdown(markdown_content):
    match = re.search(r"```(?:[a-zA-Z0-9]+)?\n(.*?)```", markdown_content, re.DOTALL)
    if match:
        return match.group(1)
    return markdown_content

def get_shebang_for_mime_type(mime_type):
    interpreter = mime_type_interpreter_map.get(mime_type, None)
    if interpreter:
        interpreter_path = shutil.which(interpreter)
        if interpreter_path:
            return f"#!/usr/bin/env {interpreter}"
    return None

def ensure_shebang_for_mime_type(script_path):
    mime_type, _ = mimetypes.guess_type(script_path)
    shebang = get_shebang_for_mime_type(mime_type)
    if shebang:
        with open(script_path, "r") as script_file:
            script_content = script_file.read()
        if not script_content.startswith("#!"):
            with open(script_path, "w") as script_file:
                script_file.write(shebang + "\n" + script_content)

def run_script(runtime, script_path, script_args):
    fixed_attempt = 1  # Counter to track the number of attempts to fix the script
    backup_created = False  # Flag to indicate if the backup has been created

    while True:
        if is_executable(script_path):
            ensure_shebang_for_mime_type(script_path)  # Add this line to ensure the shebang
            command = [script_path] + script_args
        else:
            command = [runtime, script_path] + script_args

        # Use a pseudo-terminal to run the script and interact with it
        data_queue = queue.Queue()
        def read(fd):
            data = os.read(fd, 1024)
            data_queue.put(data.decode())  # Add data to the queue
            return data

        exit_status = pty.spawn(command, read)

        # Check if the script executed successfully, otherwise send the data to the evolve endpoint
        if exit_status == 0 and not check_for_errors(data_queue):
            break
        else:
            crash_log = f"Script exited with non-zero status: {exit_status}\n"
            crash_log += "".join(list(data_queue.queue))
            print(f"Error: Script crashed with the following error:\n{crash_log}")

            # Your original code for sending data to the evolve endpoint
            with open(script_path, 'r') as script_file:
                script_content = script_file.read()
                wrapped_script = wrap_script_in_markdown(script_content)
                json_data = {
                    "scriptFile": wrapped_script,
                    "crashLog": crash_log
                }
                print("Getting help...")
                response = requests.post(URL, json=json_data)
                if response.ok:
                    markdown_content = response.text
                    rewritten_script = extract_script_from_markdown(markdown_content)
                    print(f"Corrected Script:\n{rewritten_script}")

                    if not backup_created:
                        root, ext = os.path.splitext(script_path)
                        backup_script_path = os.path.abspath(f"{root}.backup{ext}")  # Get the absolute path
                        with open(backup_script_path, 'w') as backup_script_file:
                            backup_script_file.write(script_content)
                            print(f"Original script backed up as '{backup_script_path}'")
                            backup_created = True

                    with open(script_path, 'w') as script_file:
                        script_file.write(rewritten_script)
                        print(f"Corrected script saved as: {script_path}")

if __name__ == "__main__":
    print("evolve.py (v1.0) - aiXcelus Evolve Client Starting...")
    if len(sys.argv) < 2:
        print("Usage: evolve.py [runtime] <path_to_script> [args...]")
        sys.exit(1)

    if is_executable(sys.argv[1]):
        runtime = None
        script_path = sys.argv[1]
        script_args = sys.argv[2:]
    else:
        runtime = sys.argv[1]
        script_path = sys.argv[2]
        script_args = sys.argv[3:]

    if not os.path.isfile(script_path):
        print(f"Error: File '{script_path}' does not exist")
        sys.exit(1)

    run_script(runtime, script_path, script_args)
