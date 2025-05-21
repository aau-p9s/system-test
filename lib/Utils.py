from json import dumps, loads
from os import chdir, getcwd, path, system
from subprocess import DEVNULL, PIPE, CalledProcessError, Popen, check_call, check_output
from time import sleep
from typing import Any
from lib.Arguments import verbose

output = None if verbose else DEVNULL

def curl(url:str, params:list[str] = [], json=True) -> Any:
    if verbose:
        print("sending curl request: {url}[{' '.join(params)}]")
    raw_response = check_output([
        "curl",
        url,
    ] + params, stderr=output)
    if verbose:
        print(f"curl raw response: {raw_response}")
    if json:
        return loads(raw_response)
    return raw_response

def clone_repository(url:str, target_directory:str, branch:str = "main"):
    if target_directory in ["/", ".", ""]:
        print("lol")
        exit(1)
    system(f"rm -rf {target_directory}")
    print(f"Cloning Repository: {url}[{branch}] -> {target_directory}")
    try:
        check_call([
            "git",
            "clone",
            url,
            "-b",
            branch,
            target_directory
        ], stdout=output, stderr=output)
    except CalledProcessError as e:
        print(f"Failed to clone repo [{e.returncode}]")
        exit(1)

def copy_directory(source_directory:str, target_directory:str):
    try:
        if path.exists(target_directory):
            check_call([
                "rm",
                "-rf",
                target_directory
            ], stderr=output, stdout=output)
        check_call([
            "cp",
            "-r",
            source_directory,
            target_directory
        ], stderr=output, stdout=output)
    except CalledProcessError:
        print(f"Failed to copy directory: {source_directory} -> {target_directory}")
        exit(1)


def kubectl(command, args, json=False, failable=False) -> Any:
    raw_response = ""
    try:
        raw_response = check_output([
            "kubectl",
            command,
        ] + args + (["-o", "json"] if json else []), stderr=output)
    except CalledProcessError:
        if verbose or not failable:
            print(f"Kubectl command failed: [{command=}, {args=}], continue? {failable}")
        if not failable:
            exit(1)
    if verbose:
        print(f"kubernetes raw response: {raw_response}")
    if json:
        return loads(raw_response)

def kubectl_apply(data:Any):
    try:
        data_pipe = Popen([
            "echo", 
            dumps(data)
        ], stdout=PIPE)
        check_call([
            "kubectl",
            "apply",
            "-f",
            "-"
        ], stderr=output, stdout=output, stdin=data_pipe.stdout)
    except CalledProcessError:
        print(f"Failed to apply patch: {dumps(data, indent=4)}")
        exit(1)

def nix(command, flake, working_directory=""):
    original_directory = getcwd()
    if working_directory:
        chdir(working_directory)
    try:
        
        check_call([
            "nix",
            command,
            flake
        ], stderr=output, stdout=output)
    except CalledProcessError as e:
        print(f"nix call failed {e.returncode}[{e.cmd}, {e.args}]")
        exit(1)
    if working_directory:
        chdir(original_directory)


def logged_delay(delay):
    print(f"Current thread is waiting for {delay} seconds")
    sleep(delay)
