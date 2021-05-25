import shutil
import sys
from natsort import natsorted
import logging
from system_logging import setup_logging
from system_logging import read_config
import subprocess
import os

config_file_name = sys.argv[1:]
setup_logging(config_file_name)
level = 'DEBUG'
level = logging._checkLevel(level)
logging.basicConfig(format='%(asctime)s %(message)s')
log = logging.getLogger(__name__)
log.setLevel(level)


def bytesto(bytes, to, bsize=1024):
    a = {'k': 1, 'm': 2, 'g': 3, 't': 4, 'p': 5, 'e': 6}
    r = float(bytes)
    return bytes / (bsize ** a[to])


def space_free_plots_by_mountpoint(drive, plot_size_g):
    return int(bytesto(shutil.disk_usage(drive)[2], 'g') / plot_size_g)


def get_drive_by_mountpoint(mountpoint):
    """
    This accepts a mountpoint ('/mnt/enclosure0/rear/column2/drive32') and returns the drive:
    drive32
    """
    return (mountpoint.split("/")[2])


def get_all_mounting_points():
    mount = subprocess.getoutput('mount -v')
    mntlines = mount.split('\n')
    mntpoints= [mount.split()[2] for mount in mntlines]
    return mntpoints



def get_plot_drives(target_drive_pattern, plot_size_g):
    """

        """
    with open('offlined_drives', 'r') as offlined_drives_list:
        offlined_drives = [current_drives.rstrip()
                           for current_drives in offlined_drives_list.readlines()]
    available_drives = []
    for mountpoint in get_all_mounting_points():
        log.debug(f'partition: {mountpoint}')
        drive_num_free_space = space_free_plots_by_mountpoint(mountpoint, plot_size_g)
        if mountpoint.startswith(target_drive_pattern) \
                and os.path.ismount(mountpoint) \
                and drive_num_free_space >= 1 \
                and get_drive_by_mountpoint(mountpoint) not in offlined_drives:
            drive = get_drive_by_mountpoint(mountpoint)
            available_drives.append((mountpoint, drive))
            
    return available_drives
    # return (natsorted(available_drives)[0])
