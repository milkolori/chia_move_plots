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
    config_file_name, 'env_params', 'source_dirs').split(',')
target_drive_patterns = read_config(
    config_file_name, 'env_params', 'target_drive_pattern').split(',')
plot_size = int(read_config(config_file_name, 'env_params', 'plot_size'))

setup_logging()
level = read_config(config_file_name, 'system_logging', 'log_level')
level = logging._checkLevel(level)
logging.basicConfig(format='%(asctime)s %(message)s')
log = logging.getLogger(__name__)
log.setLevel(level)


def get_status_file_name(prefix: str, plot_dir: str, plot_file: str):
    log.debug(f'plot_dir  {plot_dir} ')
    dir_name_index = len(plot_dir.split('/')) - 1
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
    log.debug(f'Removing progress file {status_file}')
    os.remove(status_file)


def is_receive_locked(dest_dir: str):
    # Only one file transfer per destination dir is allowed
    file_pattern = get_status_file_name(RECEIVE_FILE_PREFIX, dest_dir, "*")
    dest_locks = [lock for lock in pathlib.Path('./').glob(file_pattern)]
    is_locked = len(dest_locks) > 0
    log.debug(f'Receiving dir {dest_dir} locked status: {is_locked}')
    return is_locked


def create_receive_lock(dest_dir: str, plot_file):
    status_file = get_status_file_name(
        RECEIVE_FILE_PREFIX, dest_dir, plot_file)
    log.debug(f'Creating dest lock {status_file}')
    os.open(status_file, os.O_CREAT)


def remove_receive_lock(dest_dir: str, plot_file):
    status_file = get_status_file_name(
        RECEIVE_FILE_PREFIX, dest_dir, plot_file)
    log.debug(f'Removing dest lock {status_file}')
    os.remove(status_file)


def get_plot_to_move():
    for src_dir in source_dirs:
        try:
            plot_to_process = [plot for plot in pathlib.Path(src_dir).glob(
                "*.plot") if plot.stat().st_size > plot_size and not is_in_progress(src_dir, plot.name)]
            log.debug(f'{plot_to_process[0].name}')
            return (src_dir, plot_to_process[0].name)
        except IndexError:
            log.debug(f'{src_dir} is Empty: No Plots to Process.')

    log.debug(f'All plot directories are empty. Will check again soon!')
    return (False, False)


def get_dest_drive():
    try:
        dest_dirs_list = []
        for pattern in target_drive_patterns:
            dest_dirs_list =  dest_dirs_list + get_plot_drives(pattern, plot_size)

        log.debug(f'{dest_dirs_list}')
        if len(dest_dirs_list) == 0:
            log.debug(f'There are no drives matching {target_drive_patterns} with available space')
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

            log.debug(f'Moving file')
            plot_path = plot_dir + plot_name
            if read_config(config_file_name, 'env_params', 'simulate'):
                log.debug(
                    f'This is a simulation, nothing will be moved! for moving "{plot_path}" to "{dest_dir}"')
                log.debug(
                    f'Simulation for moving "{plot_path}" to "{dest_dir}"')
            else:
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
