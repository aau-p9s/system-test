from json import dumps, loads
from os import chdir, getcwd, path, system
from subprocess import DEVNULL, PIPE, CalledProcessError, Popen, check_call, check_output
from time import sleep
from typing import Any
from psycopg2 import connect
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from lib.Arguments import verbose, postgres_address, postgres_port, postgres_database, postgres_user, postgres_password, deployment

output = None if verbose else DEVNULL

def curl(url:str, params:list[str] = [], json=True) -> Any:
    if verbose:
        print(f"sending curl request: {url}[{' '.join(params)}]")
    raw_response = check_output([
        "curl",
        url,
    ] + params, stderr=output).decode()
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
        raise RuntimeError(f"Failed to clone repo [{e.returncode}]")

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
        raise RuntimeError(f"Failed to copy directory: {source_directory} -> {target_directory}")


def kubectl(command, args, json=False, failable=False) -> Any:
    if deployment == "docker":
        return
    raw_response = ""
    try:
        raw_response = check_output([
            "kubectl",
            command,
        ] + args + (["-o", "json"] if json else []), stderr=output).decode()
    except CalledProcessError as e:
        if verbose or not failable:
            print(f"Kubectl command failed: [{command=}, {args=}], continue? {failable}")
        if not failable:
            raise RuntimeError(f"Error code: {e}")
    if verbose:
        print(f"kubernetes raw response: {raw_response}")
    if json:
        return loads(raw_response)
    return raw_response

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
        raise RuntimeError(f"Failed to apply: {dumps(data, indent=4)}")

def docker_compose(data:dict[str, Any]):
    print("Building dockerfiles")
    try:
        data_pipe = Popen([
            "echo",
            dumps(data)
        ], stdout=PIPE)
        check_call([
            "docker",
            "compose",
            "-f", "-",
            "up", "-d",
            "--build"
        ], stderr=output, stdout=output, stdin=data_pipe.stdout)
    except CalledProcessError:
        raise RuntimeError(f"Failed to apply {dumps(data, indent=4)}")

def docker_compose_down(data:dict[str, Any]):
    try:
        data_pipe = Popen([
            "echo",
            dumps(data)
        ], stdout=PIPE)
        check_call([
            "docker",
            "compose",
            "-f", "-",
            "down", "--remove-orphans"
        ], stderr=output, stdout=output, stdin=data_pipe.stdout)
    except CalledProcessError as e:
        print(f"Failed to clean up docker {e.stderr} {e.stdout} {e.output}")

def deploy(data:list[dict], exclusions: list[str] = []):
    match deployment:
        case "docker":
            filtered_data = {
                name: service
                for name, service in data[0].items()
                if not name in exclusions
            }
            docker_compose(filtered_data)
        case "kubernetes":
            for kubeconfig in data:
                if not kubeconfig["metadata"]["name"] in exclusions:
                    kubectl_apply(kubeconfig)
        case _:
            raise ValueError("Error, invalid deployment type")


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
        raise RuntimeError(f"nix call failed {e.returncode}[{e.cmd}, {e.args}]")
    if working_directory:
        chdir(original_directory)

# use seperate of postgres instances and reinit connection
def reinit():
    conn = connect(host=postgres_address, port=postgres_port, user=postgres_user, password=postgres_password, database="postgres")
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cursor = conn.cursor()
    cursor.execute(f"""
        SELECT pg_terminate_backend(pid)
        FROM pg_stat_activity
        WHERE datname = %s AND pid <> pg_backend_pid();
    """, [postgres_database])
    cursor.execute(f"DROP DATABASE IF EXISTS {postgres_database};")
    cursor.execute(f"CREATE DATABASE {postgres_database};")

    cursor.close()
    conn.close()

def postgresql_execute(sql, params=[]):

    connection = connect(database=postgres_database, user=postgres_user, password=postgres_password, host=postgres_address, port=postgres_port)
    cursor = connection.cursor()
    if params:
        cursor.execute(sql, params)
    else:
        cursor.execute(sql)
    connection.commit()

def postgresql_execute_get(sql, params=[]):

    connection = connect(database=postgres_database, user=postgres_user, password=postgres_password, host=postgres_address, port=postgres_port)
    cursor = connection.cursor()
    if params:
        cursor.execute(sql, params)
    else:
        cursor.execute(sql)
    connection.commit()
    return cursor.fetchall()


def logged_delay(delay):
    print(f"Current thread is waiting for {delay} seconds")
    sleep(delay)
