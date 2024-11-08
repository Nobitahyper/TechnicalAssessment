import subprocess
import sys
import time
import os

class DiskStatsTest:
    def __init__(self, disk="sda"):
        self.disk = disk
        self.status = 0

    def check_return_code(self, return_code, message, *output):
        """
        Check if the return code indicates an error, update status, and print the error message.
        """
        if return_code != 0:
            print(f"ERROR: {message}", file=sys.stderr)
            if self.status == 0:
                self.status = return_code
            for line in output:
                print(f"output: {line}", file=sys.stderr)

    def disk_check(self, command, message):
        """
        Check if a certain command related to the disk passes.
        """
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        self.check_return_code(result.returncode, message, result.stdout, result.stderr)
        return result.returncode == 0

    def capture_stats(self):
        """
        Capture the baseline stats for the disk from /proc/diskstats and /sys/block/<disk>/stat.
        """
        proc_stat = subprocess.run(
            f"grep -w -m 1 {self.disk} /proc/diskstats", 
            shell=True, capture_output=True, text=True
        ).stdout.strip()
        
        sys_stat = ""
        sys_stat_path = f"/sys/block/{self.disk}/stat"
        if os.path.exists(sys_stat_path):
            with open(sys_stat_path, 'r') as f:
                sys_stat = f.read().strip()
        
        return proc_stat, sys_stat

    def generate_disk_activity(self):
        """
        Generate disk activity using hdparm to measure disk read performance.
        """
        result = subprocess.run(f"hdparm -t /dev/{self.disk}", shell=True, capture_output=True, text=True)
        self.check_return_code(result.returncode, "Failed to generate disk activity", result.stdout, result.stderr)

    def test_disk_stats(self):
        """
        Perform the sequence of checks and validation to test the disk statistics.
        """
        # Check if the disk is an NVDIMM
        if "pmem" in self.disk:
            print(f"Disk {self.disk} appears to be an NVDIMM, skipping.")
            return self.status
        
        # Check if the disk exists in various system locations
        self.disk_check(f"grep -w -q {self.disk} /proc/partitions", 
                        f"Disk {self.disk} not found in /proc/partitions")
        
        self.disk_check(f"grep -w -q -m 1 {self.disk} /proc/diskstats", 
                        f"Disk {self.disk} not found in /proc/diskstats")
        
        self.disk_check(f"ls /sys/block/{self.disk}* > /dev/null 2>&1", 
                        f"Disk {self.disk} not found in /sys/block")
        
        sys_stat_path = f"/sys/block/{self.disk}/stat"
        if not os.path.exists(sys_stat_path) or os.stat(sys_stat_path).st_size == 0:
            self.check_return_code(1, f"stat is either empty or nonexistent in /sys/block/{self.disk}/")

        # Capture initial stats
        proc_stat_begin, sys_stat_begin = self.capture_stats()

        # Generate disk activity
        self.generate_disk_activity()

        # Wait 5 seconds to allow stat files to update
        time.sleep(5)

        # Capture stats again
        proc_stat_end, sys_stat_end = self.capture_stats()

        # Check if stats have changed
        if proc_stat_begin == proc_stat_end:
            self.check_return_code(1, "Stats in /proc/diskstats did not change", proc_stat_begin, proc_stat_end)

        if sys_stat_begin == sys_stat_end:
            self.check_return_code(1, f"Stats in /sys/block/{self.disk}/stat did not change", sys_stat_begin, sys_stat_end)

        # Final status message
        if self.status == 0:
            print(f"PASS: Finished testing stats for {self.disk}")
        
        return self.status

if __name__ == "__main__":
    disk = sys.argv[1] if len(sys.argv) > 1 else "sda"
    tester = DiskStatsTest(disk)
    exit_code = tester.test_disk_stats()
    sys.exit(exit_code)
