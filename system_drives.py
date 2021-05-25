import psutil
import shutil
import sys
from natsort import natsorted
import logging
from system_logging import setup_logging
from system_logging import read_config

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


def get_plot_drives(target_drive_pattern, plot_size_g):
    """

        """
    with open('offlined_drives', 'r') as offlined_drives_list:
        offlined_drives = [current_drives.rstrip()
                           for current_drives in offlined_drives_list.readlines()]
    available_drives = []
    for part in psutil.disk_partitions(all=False):
        log.debug(f'partition: {part}')
        drive_num_free_space = space_free_plots_by_mountpoint(part.mountpoint, plot_size_g)
        if part.device.startswith('/dev/sd') \
                and part.mountpoint.startswith(target_drive_pattern) \
                and drive_num_free_space >= 1 \
                and get_drive_by_mountpoint(part.mountpoint) not in offlined_drives:
            drive = get_drive_by_mountpoint(part.mountpoint)
            available_drives.append((part.mountpoint, part.device, drive))
            
    return available_drives
    # return (natsorted(available_drives)[0])
