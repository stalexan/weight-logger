#!/usr/bin/env python3
#
# Copyright 2022 Sean Alexandre
#
# This file is part of Weight Logger.
#
# Weight Logger is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option) any
# later version.
#
# Weight Logger is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# Weight Logger. If not, see <https://www.gnu.org/licenses/>.

""" weight-log administration """

# Standard library imports
import configparser
from getpass import getpass
import grp
import json
import math
import os
import re
import secrets
import shutil
import stat
import string
from subprocess import CompletedProcess, Popen, run
from subprocess import DEVNULL, PIPE
from subprocess import CalledProcessError, SubprocessError
from typing import Callable, List, Optional, Tuple
from argparse import Namespace

# 3rd-party imports
import validators

# Local imports
from .error import AdminError

DOCKER: str = '/usr/bin/docker'

# Number of bits to use for passwords and token.
PW_BIT_COUNT: int = 128
TOKEN_BIT_COUNT: int = 256

# Directories
CONFIG_DIR_NAME: str = 'config'
KEYS_DIR_NAME: str = 'keys'

# Config file.
CONFIG_MAIN_SECTION: str = 'main'
CONFIG_DEPL_KEY: str = 'deployment'

def create_run_command_error_message(
    args: list[str], ex: Optional[Exception], stderr: Optional[str]) -> str:
    """ Create error message for error running a command. """

    # Is there an stderr messag?
    stderr_message = f'\n{stderr.strip()}' if stderr else ''

    # Is this a Docker permission error?
    error: str = 'Got permission denied while trying to connect to the Docker daemon socket'
    if stderr_message.find(error) != -1:
        return 'Permission denied attempting to run Docker.\n' + \
            'Is the current user either root or in the docker group?'

    # What command was attempted?
    command: str = ' '.join(args)

    # Is there an exception message?
    ex_message = f'\n{str(ex).strip()}' if ex else ''

    return f'"{command}" failed{ex_message}{stderr_message}'

def run_command(
    args: list[str],
    print_command: bool = True,
    capture_output: bool = False) -> str:
    """ Run command and return stdout. """

    # Display command.
    if print_command:
        print(' '.join(args))

    # Run command.
    try:
        process: CompletedProcess = run(
            args, capture_output=capture_output, encoding='utf-8', check=True)
        return process.stdout
    except CalledProcessError as ex:
        raise AdminError(
            create_run_command_error_message(args, ex, ex.stderr)) from ex
    except (OSError, SubprocessError) as ex:
        raise AdminError(
            create_run_command_error_message(args, ex, None)) from ex

# pylint: disable=too-many-arguments
def run_command_in_container(
    container: str,
    depl_env: str,
    command: str,
    user: Optional[str] = None,
    stdout = None,
    interactive: bool = False) -> str:
    """ Run command in container.

    Parameters
    ----------
    container : str
        Which container to run the command in: proxy, frontend, backend, or db.

    depl_env : str
        Which deployement environment to use: dev or prod.

    command : str
        The command to run.

    stdout :
        The executed program's stdout. This is passed to Popen, as its stdout
        parameter.

        - If left set to None, the default, no redirection will occur, and the
          user will see stdout.
        - If set to a file or stream, stdout will be sent to the file or stream.
        - If set to PIPE, stdout will be returned as a string.
        - If set to DEVNULL, stdout will be discarded.

    interactive : bool
        Whether to run the command interactively, and allow user input. If
        True, output is displayed to the user and the stdout parameter is
        effectively None.

    Returns
    ----------
    str
        stdout if the stdout parameter was set to PIPE.
    """

    # Determine container name.
    container_name: str = f'wl-{container}-{depl_env}'

    # Prepare arg to run interactively.
    it_arg = ['-it'] if interactive else []

    # Prefix the command with su if the command should be run as another user.
    if not user is None:
        command = f'su {user} -c "{command}"'

    args: list[str] = [DOCKER, 'exec'] + it_arg + [container_name, 'sh', '-c', command]
    try:
        process = Popen(args, encoding='utf-8', stderr=PIPE, stdout=stdout)
        process.wait()
        if process.returncode != 0:
            # Create error message.
            stderr: str = process.stderr.read() if process.stderr else ''
            error_message: str
            if stderr.find("No such container") != -1:
                error_message = 'Unable to run backend command.\n' + \
                    f'Is {container_name} container running?'
            elif stderr:
                error_message = stderr.strip()
            else:
                # Error message has already been displayed on backend and not
                # available through process.stderr.  (This only happens with
                # the interactive "-it" flag. Without it, process.stderr has
                # the output from stderr.)
                error_message = ''

            # Raise error.
            raise AdminError(error_message)

        # Return stdout.
        if stdout == PIPE and not process.stdout is None:
            return process.stdout.read()
        return ''
    except OSError as ex:
        raise AdminError(
            create_run_command_error_message(args, ex, None)) from ex

def write_env_var(dest_file, name: str, value: str) -> None:
    """ Write line for environment variable. """
    if value is None:
        value = ""
    dest_file.write(f'{name}=\"{value}\"\n')

def open_deployment_file(filename: str, mode: str):
    """ Open deployment file for writing. """
    return open(filename, mode, encoding="utf-8")

def create_deployment_file(filename: str) -> None:
    """ Create deployment file and set permissions so that it can only be read
    and written by current user. """

    try:
        fd: int = os.open(filename, os.O_CREAT | os.O_WRONLY, mode=0o600)
        os.close(fd)
    except OSError as ex:
        raise AdminError(f'Could not create {filename}\n{str(ex)}') from ex

def lookup_entropy_avail() -> int:
    """ Lookup available entropy. """

    entry_avail_str: str = run_command(
        ["cat", "/proc/sys/kernel/random/entropy_avail"],
        print_command=False,
        capture_output=True)
    try:
        return int(entry_avail_str)
    except ValueError as ex:
        raise AdminError(f'Could not determine entropy available\n{str(ex)}') from ex

def generate_password() -> str:
    """ Generate password. """
    pw_len: int = 22 # For 128 bits at approx 5.9 bits per alphanumeric char.
    alphanum: str = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphanum) for ii in range(pw_len))

class Admin:
    """ For command-line administration of Weight Log app. """

    # Directories.
    config_dir: str
    keys_dir: str

    # File names.
    config_filename: str
    keys_database_filename: str
    keys_backend_filename: str

    # Deployment environment.
    depl_env: str

    def __init__(self):
        # Find root dir for Weight Log, one up from admin dir.
        weight_log_root_dir: str = os.path.realpath(
            os.path.dirname(os.path.realpath(__file__)) + '/..')

        # Config dir is in root dir.
        self.config_dir: str = f'{weight_log_root_dir}/{CONFIG_DIR_NAME}'

        # Keys dir is in config dir.
        self.keys_dir: str = f'{self.config_dir}/{KEYS_DIR_NAME}'

        # Create file names.
        self.config_filename = f'{self.config_dir}/config.ini'
        self.keys_database_filename = f'{self.keys_dir}/keys-database.env'
        self.keys_backend_filename = f'{self.keys_dir}/keys-backend.env'

        # Read config file.
        self.depl_env = ""
        if os.path.exists(self.config_filename):
            try:
                config = configparser.ConfigParser()
                config.read(self.config_filename)
                self.depl_env = config[CONFIG_MAIN_SECTION][CONFIG_DEPL_KEY]
                if not self.depl_env in { 'dev', 'prod' }:
                    raise AdminError(f'Expected dev or prod for {CONFIG_DEPL_KEY} ' + \
                        f'in {self.config_filename} but found {self.depl_env}')
            except OSError as ex:
                raise AdminError(f'Count not open {self.config_filename}.\n' + \
                    f'{str(ex)}') from ex
            except (KeyError, configparser.Error) as ex:
                raise AdminError(f'"{CONFIG_DEPL_KEY}" not found in section' + \
                    f' "{CONFIG_MAIN_SECTION}" of {self.config_filename}') from ex

    def __check_depl_env(self) -> None:
        """ Check that depl_env is set. """
        if len(self.depl_env) == 0:
            if self.__deployment_artifacts_exist():
                raise AdminError(f'No deployment setting found in {self.config_filename}')
            raise AdminError('No deployment found. To deploy run:\nwl-admin init ')

    def __deployment_artifacts_exist(self) -> bool:
        """ Returns true if there's already a deployment. """

        # Check for deployment files
        if os.path.isdir(self.config_dir):
            return True

        # Check for images and containers.
        if len(Admin.__create_docker_list()) > 0:
            return True

        return False

    def __check_state_for_init(self, homepage: str) -> None:
        """ Checks that a deployment can be initialized. """

        # Verify that homepage is a valid URL.
        if not validators.url(homepage):
            raise AdminError("--homepage needs to be a URL")

        # Check that there's not already a deployment.
        if self.__deployment_artifacts_exist():
            raise AdminError('An existing deployment was found. ' + \
                'To remove it run:\nwl-admin docker rm')

        # Check that there's enough entropy to generate passwords and keys.
        entropy_bytes_needed: int = math.ceil((TOKEN_BIT_COUNT + (2 * PW_BIT_COUNT)) / 8)
        entropy_bytes_needed = entropy_bytes_needed * 2 # Fudge factor for safety.
        if lookup_entropy_avail() < entropy_bytes_needed:
            raise AdminError('Not enough entropy to create passwords and keys')

    def __init_create_passwords_and_keys(self) -> None:
        """ Create password and key files. """

        # Create passwords and keys.
        postgres_password: str = generate_password()
        db_password: str = generate_password()
        token_key: str = secrets.token_hex(math.ceil(TOKEN_BIT_COUNT / 8))

        # Create files. Do this before writing to set ownership and permissions first.
        create_deployment_file(self.config_filename)
        create_deployment_file(self.keys_database_filename)
        create_deployment_file(self.keys_backend_filename)

        # Create database keys file.
        try:
            with open_deployment_file(self.keys_database_filename, "w") as file:
                write_env_var(file, 'POSTGRES_PASSWORD', postgres_password)
        except OSError as ex:
            raise AdminError(f'Could not create {self.keys_database_filename}.\n' + \
                f'{str(ex)}') from ex

        # Create backend keys file.
        try:
            with open_deployment_file(self.keys_backend_filename, "w") as file:
                write_env_var(file, 'DB_PASSWORD', db_password)
                write_env_var(file, 'TOKEN_KEY', token_key)
        except OSError as ex:
            raise AdminError(f'Could not open {self.keys_backend_filename}.\n' +
                f'{str(ex)}') from ex

    @staticmethod
    def __create_compose_paths(filename: str) -> Tuple[str, str]:
        """ Create paths from compose filename, for source template file and
        dest compose file. """

        return (f'admin/{filename}.tmpl', f'{CONFIG_DIR_NAME}/{filename}')

    @staticmethod
    def __copy_compose_file(filename: str) -> None:
        """ Copy compose file template to config dir. """
        try:
            (template_path, dest_path) = Admin.__create_compose_paths(filename)
            shutil.copy(template_path, dest_path)
        except OSError as ex:
            raise AdminError(
                f'Count not create docker file {filename}.\n{str(ex)}') from ex

    @staticmethod
    def __create_deployment_compose_file(filename: str, http_host_port: Optional[int]) -> None:
        """ Create deployment specific compose file. """

        # Create docker-network.yml.
        try:
            # Read template contents.
            (template_path, dest_path) = Admin.__create_compose_paths(filename)
            content: str
            with open(template_path) as template_file:
                content = template_file.read()

            # Configure ports section.
            pat = re.compile(r'\s*HOST-PORT')
            replacement: str = "" if http_host_port is None else \
                f'\n    ports:\n      - "{http_host_port}:80"'
            content = pat.sub(replacement, content)

            # Save results.
            with open(dest_path, 'a') as compose_file:
                compose_file.write(content)
        except OSError as ex:
            print(f'Unable to create {filename}\n{str(ex)}')

    @staticmethod
    def __init_create_docker_compose_files(network: str, http_host_port: Optional[int]) -> None:
        """ Create docker compose files. """

        # Create docker-compose.yml.
        Admin.__copy_compose_file("docker-compose.yml")

        # Create deployment specific compose files.
        Admin.__create_deployment_compose_file("docker-compose.dev.yml", http_host_port)
        Admin.__create_deployment_compose_file("docker-compose.prod.yml", http_host_port)

        # Create docker-network.yml.
        network_filename: str = 'docker-network.yml'
        try:
            # Use external network?
            is_external: str = "true"
            if network is None:
                is_external = "false"
                network = "wl-network"

            # Generate file content.
            content: str
            with open(f'admin/{network_filename}.tmpl') as networks_file:
                content = networks_file.read()
            content = content.replace('NETWORK', network)
            content = content.replace('IS_EXTERNAL', is_external)

            # Save file.
            with open(f'config/{network_filename}', 'a') as compose_file:
                compose_file.write(content)
        except OSError as ex:
            print(f'Unable to create {network_filename}\n{str(ex)}')

    @staticmethod
    def __save_homepage(homepage: str) -> None:
        """ Save homepage value to config files. """

        # Save homepage to 'frontend/.env'
        env_filename: str = 'frontend/.env'
        try:
            with open_deployment_file(env_filename, "w") as env_file:
                write_env_var(env_file, 'REACT_APP_WL_HOMEPAGE', homepage)
        except OSError as ex:
            raise AdminError(f'Count not write to {env_filename}.\n{str(ex)}') from ex

        # Save homepage to 'frontend/package.json'
        json_filename: str = 'frontend/package.json'
        try:
            with open(json_filename, 'r+') as json_file:
                # Load json and update.
                json_data = json.load(json_file)
                json_data['homepage'] = homepage

                # Write json back out.
                json_file.seek(0)
                json.dump(json_data, json_file, indent=2)
                json_file.truncate()
        except OSError as ex:
            raise AdminError(f'Count not update {json_filename}.\n{str(ex)}') from ex

    def do_init(self, args: Namespace):
        """ Initialize deployment. """

        # Verify application and system state.
        self.__check_state_for_init(args.homepage)

        # Create dirs.
        try:
            os.mkdir(self.config_dir, mode=0o700)
            os.mkdir(self.keys_dir, mode=0o700)
        except OSError as ex:
            raise AdminError(
                f'Count not create config directory.\n{str(ex)}') from ex

        # Write out homepage.
        self.__save_homepage(args.homepage)

        # Create password and key files.
        self.__init_create_passwords_and_keys()

        # Create config file.
        try:
            config = configparser.ConfigParser()
            config[CONFIG_MAIN_SECTION] = { CONFIG_DEPL_KEY: args.env }
            with open_deployment_file(self.config_filename, "w") as config_file:
                config.write(config_file)
        except OSError as ex:
            raise AdminError(f'Count not open {self.config_filename}.\n{str(ex)}') from ex

        # Create Docker compose files.
        Admin.__init_create_docker_compose_files(args.network, args.http_host_port)

    def __assemble_compose_files_list(self, depl_env: Optional[str] = None) -> list[str]:
        """ Assemble list of files used to invoke docker compose.

        Parameters
        ----------
        depl_env : str
            Which deployment environment the compose files should be created
            for, "dev" or "prod". Defaults to self.depl_env if set to None.

        Returns
        -------
        list[str]
            List of deployment files.
        """

        # Which deployment environment is this for?
        if depl_env is None:
            depl_env = self.depl_env

        # Assemble list.
        return [
            f'{self.config_dir}/docker-compose.yml',
            f'{self.config_dir}/docker-compose.{depl_env}.yml',
            f'{self.config_dir}/docker-network.yml',
        ]

    def __assemble_compose_file_args(self, depl_env: Optional[str] = None) -> list[str]:
        """ Assemble file command line arguments used to invoke docker compose. """

        args: list[str] = []
        for filename in self.__assemble_compose_files_list(depl_env):
            args = args + ['--file', filename]
        return args

    def __compose_files_exist(self) -> bool:
        """ Returns true if compose files exist. """

        # Assemble list of files to check for.
        files: list[str] = \
            self.__assemble_compose_files_list("dev") + \
            self.__assemble_compose_files_list("prod")
        files = list(set(files)) # Remove duplicates.

        # Check whether files exist.
        for filename in files:
            if not os.path.exists(filename):
                return False
        return True

    def do_docker_build(self, args: Namespace):
        """ Build docker images. """

        # Check that there's a deployment.
        self.__check_depl_env()

        # Create argument list
        command_args: list[str] = [ DOCKER, 'compose' ] + \
            self.__assemble_compose_file_args() + \
            [ 'build', '--build-arg', f'ENV={self.depl_env}' ]
        if args.pull:
            command_args = command_args + ["--pull", "--no-cache"]
        #command_args = command_args + ["--progress=plain"]

        # Build images.
        run_command(command_args)

    @staticmethod
    def __run_docker_list_command(args: list[str], title: str) -> str:
        """ Run a docker list command and display output. """

        # Run command
        stdout: str = run_command(args, print_command=False, capture_output=True)

        # Generate list.
        stdout = stdout.strip()
        lines: list[str] = stdout.split('\n')
        if len(lines) > 1:
            return title + '\n' + stdout
        return ''

    @staticmethod
    def __create_docker_list() -> str:
        """ Create string that lists docker images and containers. """

        # List images.
        results: list[str] = [Admin.__run_docker_list_command(
            [DOCKER, 'images', 'wl-*'],
            "=== IMAGES ===")]

        # List containers.
        results.append(Admin.__run_docker_list_command(
            [DOCKER, 'ps', '-a', '--filter', 'name=wl-*'],
            "=== CONTAINERS ==="))

        # List volumes .
        results.append(Admin.__run_docker_list_command(
            [DOCKER, 'volume', 'ls', '--filter', 'name=wl-*'],
            "=== VOLUMES ==="))

        # List networks.
        results.append(Admin.__run_docker_list_command(
            [DOCKER, 'network', 'ls', '--filter', 'name=wl-*'],
            "=== NETWORKS ==="))

        # Assemble lists.
        return '\n'.join([result for result in results if len(result) > 0])

    # pylint: disable=unused-argument
    @staticmethod
    def do_docker_list(args) -> None:
        """ List docker images and containers. """
        docker_list: str = Admin.__create_docker_list()
        if len(docker_list) > 0:
            print(docker_list)

    def do_docker_down(self, args) -> None:
        """ Bring containers down. """
        self.__check_depl_env()
        run_command([DOCKER, 'compose'] + self.__assemble_compose_file_args() + ['down'])

    def do_docker_up(self, args):
        """ Bring containers up. """
        self.__check_depl_env()
        run_command([DOCKER, 'compose'] + self.__assemble_compose_file_args() + ['up', '--detach'])

    def __delete_docker_content(self, depl_env: str):
        """ Delete docker content.

        Parameters
        ----------
        depl_env: str
            Which deployment to delete content for: dev or prod.

        Returns
        -------
        bool
            True if docker compose file was found and delete could be done,
            else false.

        """

        if not self.__compose_files_exist():
            return False

        # Delete containers.
        run_command([DOCKER, 'compose'] + self.__assemble_compose_file_args(depl_env) + \
            ['rm', '--force', '--stop', '--volumes'])

        # Delete volumes.
        run_command([DOCKER, 'volume', 'rm', 'wl-db-vol-dev', '--force'])
        run_command([DOCKER, 'volume', 'rm', 'wl-db-vol-prod', '--force'])

        # Delete images.
        run_command([DOCKER, 'compose'] + self.__assemble_compose_file_args(depl_env) + \
            ['down', '--rmi', 'all'])

        return True

    @staticmethod
    def __lookup_docker_ids(command: List[str]) -> List[str]:
        """ Lookup docker IDs. """
        ids_str: str = run_command(
            [DOCKER] + command + ['--quiet'],
            print_command = False,
            capture_output = True)
        ids: List[str] = ids_str.strip().split('\n')
        return [an_id.strip() for an_id in ids if len(an_id.strip()) > 0]

    @staticmethod
    def __delete_docker_content_manually():
        """ Delete docker content manually, by using "wl-" prefix. """

        # Delete containers.
        ids: [str] = Admin.__lookup_docker_ids(['ps', '--all', '--filter', 'name=wl-*'])
        if len(ids) > 0:
            run_command([DOCKER, 'rm', '--force'] + ids)

        # Delete volumes.
        ids = Admin.__lookup_docker_ids(['volume', 'ls', '--filter', 'name=wl-*'])
        if len(ids) > 0:
            run_command([DOCKER, 'volume', 'rm', '--force'] + ids)

        # Delete networks.
        ids = Admin.__lookup_docker_ids(['network', 'ls', '--filter', 'name=wl-*'])
        if len(ids) > 0:
            run_command([DOCKER, 'network', 'rm'] + ids)

        # Delete images.
        ids = Admin.__lookup_docker_ids(['images', 'wl-*'])
        if len(ids) > 0:
            run_command([DOCKER, 'rmi', '--force'] + ids)

    def do_docker_rm(self, args):
        """ Delete Weight Log deployment and its docker images, containers,
        volumes, and networks. """

        # Confirm delete.
        response: str = input(
            'Delete all Weight Log docker containers, volumes, and images? (y/N) ')
        if response.lower() != 'y':
            return

        # Delete docker content.
        compose_delete_worked: bool = self.__delete_docker_content("dev")
        compose_delete_worked = compose_delete_worked and self.__delete_docker_content("prod")
        if not compose_delete_worked:
            Admin.__delete_docker_content_manually()

        # Delete deployment files.
        try:
            if os.path.exists(self.config_dir):
                shutil.rmtree(self.config_dir)
        except OSError as ex:
            raise AdminError(f'Unable to delete {self.config_dir}.\n{str(ex)}') from ex

    def do_user_list(self, args):
        """ List users. """
        self.__check_depl_env()
        run_command_in_container("backend", self.depl_env, './wl-list-users', user='wls')

    def do_user_add(self, args):
        """ Add user. """

        # Check that there's a deployment.
        self.__check_depl_env()

        # Create command.
        english_opt: str = '--english' if args.english else ''
        command: str = f'./wl-add-user {english_opt} --goal {args.goal} {args.username}'

        # Run command.
        run_command_in_container("backend", self.depl_env, command, interactive=True, user='wls')

    def do_user_delete(self, args):
        """ Delete user. """
        self.__check_depl_env()
        run_command_in_container(
            "backend",
            self.depl_env,
            f'./wl-delete-user {args.username}',
            user='wls')

    def do_user_chpasswd(self, args):
        """ Change user password. """
        self.__check_depl_env()
        run_command_in_container(
            "backend",
            self.depl_env,
            f'./wl-edit-user-passwd {args.username}',
            interactive=True,
            user='wls')

    def do_db_backup(self, args):
        """ Backup database. """
        self.__check_depl_env()
        try:
            with open(args.file, "w", encoding="utf-8") as backup_file:
                run_command_in_container(
                    "db",
                    self.depl_env,
                    'pg_dump -t schema -t users -t entries --data-only --column-inserts ' + \
                        '-U postgres weight_log',
                    stdout=backup_file)
        except OSError as ex:
            raise AdminError(f'Could not write to {args.file}.\n{str(ex)}') from ex

    def do_db_restore(self, args):
        """ Restore database. """

        # Check that there's a deployment.
        self.__check_depl_env()

        try:
            # Create temp dir in container.
            temp_dir_name: str = run_command_in_container(
                'backend',
                self.depl_env,
                '/bin/mktemp --directory',
                user = 'wls',
                stdout = PIPE)
            temp_dir_name = temp_dir_name.strip()

            # Copy restore file to container.
            if not os.path.exists(args.file):
                raise AdminError(f'Could not find {args.file}')
            dest_path: str = f'wl-backend-{self.depl_env}:{temp_dir_name}'
            run_command(
                [DOCKER, 'cp', args.file, dest_path],
                print_command = False,
                capture_output = True)

            # Restore.
            filename: str = f'{temp_dir_name}/{os.path.basename(args.file)}'
            run_command_in_container(
                'backend',
                self.depl_env,
                f'./wl-db-restore {filename}',
                user = 'wls',
                interactive=True)

        finally:
            # Delete the restore file copy.
            run_command_in_container(
                'backend',
                self.depl_env,
                f'/bin/rm -rf {temp_dir_name}',
                stdout=DEVNULL)
