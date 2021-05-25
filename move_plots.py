import pathlib
import logging
from system_logging import setup_logging
from system_logging import read_config
import sys
import os
import time
import subprocess

from system_drives import get_plot_drives

__author__ = 'Milko Lorinkov'
VERSION = "0.1 (2021-05-24)"


TRANSFER_FILE_PREFIX = 'copyFrom'
RECEIVE_FILE_PREFIX = 'copyTo'


config_file_name = sys.argv[1:]
source_dirs = read_config(
    config_file_name, 'env_params', 'source_dirs')
target_drive_patterns = read_config(
    config_file_name, 'env_params', 'target_drive_pattern')
plot_size_gb = float(read_config(
    config_file_name, 'env_params', 'plot_size_gb'))
is_simulation = read_config(config_file_name, 'env_params', 'simulate')

setup_logging(config_file_name)
level = read_config(config_file_name, 'system_logging', 'log_level')
level = logging._checkLevel(level)
logging.basicConfig(format='%(asctime)s %(message)s')
log = logging.getLogger(__name__)
log.setLevel(level)


red = '\033[0;31m'
yellow = '\033[0;33m'
green = '\033[0;32m'
white = '\033[0;37m'
blue = '\033[0;34m'
nc = '\033[0m'


def get_status_file_name(prefix: str, plot_dir: str, plot_file: str):
    endsWithSlash = plot_dir.endswith('/')
    dir_name_index = len(plot_dir.split('/')) - (2 if endsWithSlash else 1)
    dir_name = plot_dir.split('/')[dir_name_index]
    file_name = 'locks/' + prefix + '-' + dir_name + '-' + plot_file
    return file_name


def is_in_progress(plot_dir: str, plot_file: str):
    is_in_progress = os.path.isfile(get_status_file_name(
        TRANSFER_FILE_PREFIX, plot_dir, plot_file))
    log.debug(f'Check file  {plot_file} in progress: {is_in_progress}')
    return is_in_progress


def create_progress_file(plot_dir: str, plot_file):
    status_file = get_status_file_name(
        TRANSFER_FILE_PREFIX, plot_dir, plot_file)
    log.debug(f'Creating progress file {status_file}')
    os.open(status_file, os.O_CREAT)


def remove_progress_file(plot_dir: str, plot_file):
    status_file = get_status_file_name(
        TRANSFER_FILE_PREFIX, plot_dir, plot_file)
    log.debug(f'remove_progress_file(): Removing progress file {status_file}')
    os.remove(status_file)


def is_receive_locked(dest_dir: str):
    # Only one file transfer per destination dir is allowed
    file_pattern = get_status_file_name(RECEIVE_FILE_PREFIX, dest_dir, "*")
    dest_locks = [lock for lock in pathlib.Path('./').glob(file_pattern)]
    is_locked = len(dest_locks) > 0
    log.debug(
        f'is_receive_locked(): Receiving dir {dest_dir} locked status: {is_locked}')
    return is_locked


def create_receive_lock(dest_dir: str, plot_file):
    status_file = get_status_file_name(
        RECEIVE_FILE_PREFIX, dest_dir, plot_file)
    log.debug(f'create_receive_lock(*): Creating dest lock {status_file}')
    os.open(status_file, os.O_CREAT)


def remove_receive_lock(dest_dir: str, plot_file):
    status_file = get_status_file_name(
        RECEIVE_FILE_PREFIX, dest_dir, plot_file)
    log.debug(f'remove_receive_lock(): Removing dest lock {status_file}')
    os.remove(status_file)


def get_plot_to_move():
    has_plot_dir = False
    for src_dir in source_dirs:
        try:
            if not os.path.isdir(src_dir):
                log.debug(
                    f'Source dir {src_dir} does not exists. It will be skipped.')
                continue
            plot_to_process = [plot for plot in pathlib.Path(src_dir).glob(
                "*.plot") if plot.stat().st_size > plot_size_gb and not is_in_progress(src_dir, plot.name)]
            log.debug(f'{plot_to_process[0].name}')
            return (src_dir, plot_to_process[0].name)
        except IndexError:
            log.debug(f'{src_dir} is Empty: No Plots to Process.')

    if has_plot_dir:
        log.debug(f'All plot directories are empty. Will check again soon!')
    else:
        log.debug(f'Source directories are not available')

    return (False, False)


def get_dest_drive():
    try:
        dest_dirs_list = []
        for pattern in target_drive_patterns:
            dest_dirs_list = dest_dirs_list + \
                get_plot_drives(pattern, plot_size_gb)

        log.debug(f'{dest_dirs_list}')
        if len(dest_dirs_list) == 0:
            log.debug(
                f'There are no drives matching {target_drive_patterns} with available space')
            return False

        dest_dirs = [
            dir for dir in dest_dirs_list if not is_receive_locked(dir)]
        return dest_dirs[0]
    except IndexError:
        log.debug(f'All destination drives are locked. Will check again soon!')
        return False


def move_plot():
    plot_dir, plot_name = get_plot_to_move()

    if plot_dir and plot_name:
        dest_dir = get_dest_drive()

        if dest_dir:
            log.debug(f'About to mode {plot_name} from {plot_dir} to ')
            create_progress_file(plot_dir, plot_name)
            create_receive_lock(dest_dir, plot_name)

            plot_path = plot_dir + plot_name
            if is_simulation:
                log.debug(
                    f'{yellow}This is a simulation, nothing will be moved!{nc}')
                log.debug(
                    f'{yellow}Simulation for moving {green}"{plot_path}"{nc} to {green}"{dest_dir}"{nc}')
            else:
                log.debug(
                    f'{blue}Moving{nc} {green}"{plot_path}"{nc} to {green}"{dest_dir}{nc}')
                subprocess.call(['./move_file.sh', plot_path, dest_dir])

            remove_progress_file(plot_dir, plot_name)
            remove_receive_lock(dest_dir, plot_name)


def main():
    log.debug('Start moving plots')
    move_plot()
    # if verify_glances_is_running():
    #     process_plot()
    # else:
    #     print('Glances is Required for this script!')
    #     print('Please install and restart this script.')
    #     exit()


if __name__ == '__main__':
    main()
