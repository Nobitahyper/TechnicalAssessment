# Disk Stats Test and SSH Connectivity Test Case

This repository contains:
- A Python script (`disk_stats_test.py`) that verifies disk statistics on a Linux system.
- A test case document (`SSH_Test_Case.txt`) for testing SSH connectivity using both password-based and key-based authentication.

## Files

1. **disk_stats_test.py**
   - A PEP8-compliant Python script converted from a shell script to test disk statistics.
   - The script verifies if a disk (e.g., `/dev/sda`) is active and produces expected system statistics on a Linux system.
   - Includes compatibility checks for Linux OS, verbose output options, and error handling for permissions and dependencies (e.g., `hdparm`).

2. **SSH_Test_Case.txt**
   - A detailed test case for validating SSH connectivity with password and key-based authentication methods.
   - Includes setup, steps, expected results, and cleanup instructions.

## Requirements

- **disk_stats_test.py**:
  - Python 3.x
  - `hdparm` installed (for generating disk activity)
  - Root permissions to access `/dev/sda`

- **SSH_Test_Case.txt**:
  - Linux server with SSH configured for both password and key-based authentication.

## Usage

1. **disk_stats_test.py**:
   - Run on a Linux system with sudo privileges:
     ```bash
     sudo python3 disk_stats_test.py sda
     ```
   - To enable verbose output:
     ```bash
     sudo python3 disk_stats_test.py sda -v
     ```

2. **SSH Test Case**:
   - Follow the steps outlined in `SSH_Test_Case.txt` for validating SSH connectivity.

## Notes
- The `disk_stats_test.py` script is designed for Linux only and includes a compatibility check to prevent execution on non-Linux systems.
- The `SSH_Test_Case.txt` provides a comprehensive setup and testing guide but does not contain actual test code.
