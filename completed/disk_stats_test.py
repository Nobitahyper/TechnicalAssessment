#!/usr/bin/env python3

"""
Disk Stats Test Script

This script gathers data about a disk to verify it's recognized by the OS
and is properly represented.

Usage:
    disk_stats_test.py [options] [disk]

Parameters:
    disk                    Disk device name (e.g., sda). Defaults to 'sda'.

Options:
    -v, --verbose           Enable verbose output.
"""

import argparse
import logging
import os
import platform
import re
import shutil
import subprocess
import sys
import time


class DiskStatsTest:
    def __init__(self, disk="sda", verbose=False):
        self.disk = disk
        self.verbose = verbose
        self.logger = logging.getLogger(__name__)
        self.sys_stat_path = f"/sys/block/{self.disk}/stat"

    def validate_disk_name(self):
        """
        Validate the disk name to prevent injection attacks.
        """
        if not re.match(r'^[a-zA-Z0-9]+$', self.disk):
            self.logger.error(f"Invalid disk name '{self.disk}'.")
            sys.exit(1)

    def check_compatibility(self):
        """
        Ensure the script is running on a Linux system.
        """
        if platform.system() != "Linux":
            self.logger.error("This script is only compatible with Linux.")
            sys.exit(1)
    
    def check_permissions(self):
        """
        Ensure the script is run with root permissions.
        """
        if os.geteuid() != 0:
            self.logger.error("This script requires root privileges. Please run as root or use sudo.")
            sys.exit(1)

    def check_hdparm(self):
        """
        Verify that 'hdparm' is installed, as it is required for disk activity.
        """
        if shutil.which("hdparm") is None:
            self.logger.error("'hdparm' is not installed. Please install it using 'sudo apt-get install hdparm'.")
            sys.exit(1)

    def disk_check(self, command, message):
        """
        Check if a certain command related to the disk passes.
        
        Args:
            command (list): The command to execute as a list of arguments.
            message (str): The error message to display if the command fails.

        Returns:
            bool: True if the command succeeds, False otherwise.
        """
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode != 0:
            self.logger.error(message)
            if result.stdout:
                self.logger.debug(f"stdout: {result.stdout.strip()}")
            if result.stderr:
                self.logger.debug(f"stderr: {result.stderr.strip()}")
            return False
        return True

    def capture_stats(self):
        """
        Capture the baseline stats for the disk from /proc/diskstats and /sys/block/<disk>/stat.
        
        Returns:
            tuple: proc_stat (str), sys_stat (str)
        """
        # Capture /proc/diskstats
        result = subprocess.run(
            ["grep", "-w", "-m", "1", self.disk, "/proc/diskstats"],
            capture_output=True, text=True
        )
        proc_stat = result.stdout.strip()
        
        # Capture /sys/block/<disk>/stat
        sys_stat = ""
        if os.path.isfile(self.sys_stat_path):
            with open(self.sys_stat_path, 'r') as f:
                sys_stat = f.read().strip()
        
        return proc_stat, sys_stat

    def generate_disk_activity(self):
        """
        Generate disk activity using hdparm to measure disk read performance.
        """
        result = subprocess.run(["hdparm", "-t", f"/dev/{self.disk}"], capture_output=True, text=True)
        if result.returncode != 0:
            self.logger.error("Failed to generate disk activity")
            if result.stdout:
                self.logger.debug(f"stdout: {result.stdout.strip()}")
            if result.stderr:
                self.logger.debug(f"stderr: {result.stderr.strip()}")
            sys.exit(1)

    def test_disk_stats(self):
        """
        Perform the sequence of checks and validation to test the disk statistics.
        """
        # Check system compatibility and hdparm availability
        self.check_compatibility()
        self.check_permissions()
        self.validate_disk_name()
        self.check_hdparm()

        # Check if the disk is an NVDIMM
        if "pmem" in self.disk:
            self.logger.info(f"Disk {self.disk} appears to be an NVDIMM, skipping.")
            sys.exit(0)
        
        # Check if the disk exists in various system locations
        if not self.disk_check(["grep", "-w", self.disk, "/proc/partitions"],
                               f"Disk {self.disk} not found in /proc/partitions"):
            sys.exit(1)

        if not self.disk_check(["grep", "-w", "-m", "1", self.disk, "/proc/diskstats"],
                               f"Disk {self.disk} not found in /proc/diskstats"):
            sys.exit(1)

        if not os.path.exists(f"/sys/block/{self.disk}"):
            self.logger.error(f"Disk {self.disk} not found in /sys/block")
            sys.exit(1)

        if not os.path.isfile(self.sys_stat_path) or os.path.getsize(self.sys_stat_path) == 0:
            self.logger.error(f"stat is either empty or nonexistent in /sys/block/{self.disk}/")
            sys.exit(1)

        # Capture initial stats
        proc_stat_begin, sys_stat_begin = self.capture_stats()
        self.logger.debug(f"Initial /proc/diskstats: {proc_stat_begin}")
        self.logger.debug(f"Initial /sys/block/{self.disk}/stat: {sys_stat_begin}")

        # Generate disk activity
        self.generate_disk_activity()

        # Wait 5 seconds to allow stat files to update
        time.sleep(5)

        # Capture stats again
        proc_stat_end, sys_stat_end = self.capture_stats()
        self.logger.debug(f"Final /proc/diskstats: {proc_stat_end}")
        self.logger.debug(f"Final /sys/block/{self.disk}/stat: {sys_stat_end}")

        # Check if stats have changed
        if proc_stat_begin == proc_stat_end:
            self.logger.error("Stats in /proc/diskstats did not change")
            self.logger.debug(f"Before: {proc_stat_begin}")
            self.logger.debug(f"After: {proc_stat_end}")
            sys.exit(1)

        if sys_stat_begin == sys_stat_end:
            self.logger.error(f"Stats in /sys/block/{self.disk}/stat did not change")
            self.logger.debug(f"Before: {sys_stat_begin}")
            self.logger.debug(f"After: {sys_stat_end}")
            sys.exit(1)

        # Final status message
        self.logger.info(f"PASS: Finished testing stats for {self.disk}")
        sys.exit(0)
        

def main():
    parser = argparse.ArgumentParser(description="Disk stats test script")
    parser.add_argument("disk", nargs='?', default="sda", help="Disk device name (e.g., sda)")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose output")
    args = parser.parse_args()

    # Configure logging
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format='%(message)s'
    )

    tester = DiskStatsTest(disk=args.disk, verbose=args.verbose)
    tester.test_disk_stats()


if __name__ == "__main__":
    main()
