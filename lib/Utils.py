from json import dumps, loads
from os import chdir, getcwd, path, system
from subprocess import DEVNULL, PIPE, CalledProcessError, Popen, check_call, check_output
from time import sleep
from typing import Any
from psycopg2 import connect
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

from lib.Arguments import verbose, postgres_address, postgres_port, postgres_database, postgres_user, postgres_password

output = None if verbose else DEVNULL

connection = connect(database=postgres_database, user=postgres_user, password=postgres_password, host=postgres_address, port=postgres_port)

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
        ] + args + (["-o", "json"] if json else []), stderr=output).decode()
    except CalledProcessError:
        if verbose or not failable:
            print(f"Kubectl command failed: [{command=}, {args=}], continue? {failable}")
        if not failable:
            exit(1)
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
        print(f"Failed to apply: {dumps(data, indent=4)}")
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

def psql(sql: str, json = False):
    try:
        result = check_output([
            "/usr/bin/psql",
            "-h", postgres_address,
            "-p", str(postgres_port),
            "-U", postgres_user,
            postgres_database,
            "-c", sql
        ], env={"PGPASSWORD": postgres_password}, stderr=output)

        return loads(result) if json else result
    except CalledProcessError as e:
        print(f"psql call failed {e.returncode}")
        exit(1)

# use seperate of postgres instances and reinit connection
def reinit():
    global connection

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

    # reinit connection
    connection = connect(host=postgres_address, port=postgres_port, user=postgres_user, password=postgres_password, database=postgres_database)


def postgresql_execute(sql, params=[], returns=False):
    cursor = connection.cursor()
    if params:
        cursor.execute(sql, params)
    else:
        cursor.execute(sql)
    connection.commit()
    if returns:
        return cursor.fetchall()
    return []


def logged_delay(delay):
    print(f"Current thread is waiting for {delay} seconds")
    sleep(delay)
