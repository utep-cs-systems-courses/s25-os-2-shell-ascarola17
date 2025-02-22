import os, sys, re

while True:
    #Step 2 (Retrieve PS@)
    ps1 = os.getenv("PS1", "$ ")

    command = input(ps1)

    cmds = command.split(" ")

    print("did split work ",cmds )
    

