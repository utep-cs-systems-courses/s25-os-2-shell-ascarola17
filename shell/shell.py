import os
import sys

def get_input():
    try:
        return input().strip()
    except EOFError:
        sys.exit(0)

while True:
    ps1 = os.getenv("PS1", "$ ")
    if sys.stdin.isatty():  # Show prompt only in interactive mode
        print(ps1, end="", flush=True)

    command = get_input()
    if not command:
        continue  # Ignore empty input

    cmds = command.split()  # Split command into a list

    # Built-in command: exit
    if cmds[0] == "exit":
        break  

    # Built-in command: cd
    if cmds[0] == "cd":
        try:
            target_dir = cmds[1] if len(cmds) > 1 else os.getenv("HOME")
            os.chdir(target_dir)
        except FileNotFoundError:
            print(f"cd: no such file or directory: {target_dir}")
        continue  

    # Check for background task (`&`)
    run_in_background = False
    if cmds[-1] == "&":
        run_in_background = True
        cmds = cmds[:-1]  # Remove `&` from the command list

    # Check for multiple pipes (`| |`)
    if "|" in cmds:
        cmds = " ".join(cmds).split("|")  # Split commands at each pipe
        cmds = [cmd.strip().split() for cmd in cmds]  # Convert to list of lists
        num_pipes = len(cmds) - 1  # Number of pipes needed

        pipes = [os.pipe() for _ in range(num_pipes)]  # Create all pipes

        for i in range(len(cmds)):  # Loop through all commands in the pipeline
            pid = os.fork()

            if pid == 0:  # Child process
                if i > 0:  # Not the first command
                    os.dup2(pipes[i - 1][0], 0)  # Read from previous pipe
                if i < num_pipes:  # Not the last command
                    os.dup2(pipes[i][1], 1)  # Write to next pipe

                # Close all pipes in the child
                for r, w in pipes:
                    os.close(r)
                    os.close(w)

                # Execute command
                for path in os.getenv("PATH").split(":"):
                    full_path = os.path.join(path, cmds[i][0])
                    if os.path.exists(full_path):
                        os.execve(full_path, cmds[i], os.environ)

                print(f"{cmds[i][0]}: command not found")
                sys.exit(1)

        # Parent process: Close all pipes and wait
        for r, w in pipes:
            os.close(r)
            os.close(w)

        for _ in range(len(cmds)):
            os.wait()

        continue  # Skip the rest of the loop

    # Handle forking and execution
    pid = os.fork()

    if pid == 0:  # Child process
        output_redirect = None
        input_redirect = None

        # Check for output redirection (`>`)
        if ">" in cmds:
            idx = cmds.index(">")
            output_redirect = cmds[idx + 1]  # Get the filename
            cmds = cmds[:idx]  # Remove `>` and filename from command

        # Check for input redirection (`<`)
        if "<" in cmds:
            idx = cmds.index("<")
            input_redirect = cmds[idx + 1]  # Get the filename
            cmds = cmds[:idx]  # Remove `<` and filename from command

        # Apply output redirection (if any)
        if output_redirect:
            fd = os.open(output_redirect, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o644)
            os.dup2(fd, 1)  # Redirect stdout to the file
            os.close(fd)

        # Apply input redirection (if any)
        if input_redirect:
            try:
                fd = os.open(input_redirect, os.O_RDONLY)
                os.dup2(fd, 0)  # Redirect stdin from the file
                os.close(fd)
            except FileNotFoundError:
                print(f"Error: {input_redirect} not found")
                sys.exit(1)

        # Find command in $PATH and execute
        if "/" in cmds[0]:  # Absolute path
            try:
                os.execve(cmds[0], cmds, os.environ)
            except FileNotFoundError:
                print(f"{cmds[0]}: command not found")
                sys.exit(1)
        else:  # Search in $PATH
            paths = os.getenv("PATH").split(":")
            for path in paths:
                full_path = os.path.join(path, cmds[0])
                if os.path.exists(full_path):
                    os.execve(full_path, cmds, os.environ)

            print(f"{cmds[0]}: command not found")
            sys.exit(1)

    else:  # Parent process
        if not run_in_background:
            os.wait()  # Wait for child to finish
