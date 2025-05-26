import time
import os
import subprocess # For executing commands

LOG_FILE_PATH = "/var/log/nginx/flask_error.log"
KEYWORDS_TO_WATCH = ["emerg",
                    "crit",
                    "failed to connect",
                    "HTTP/1.1 404 Not Found",
                    "Connection refused"
                    ]

def perform_action(keyword, log_line):
    """
    This function defines what action to take when a keyword is found.
    """
    print(f"!!! Keyword '{keyword}' detected in log line: {log_line.strip()}")
    
    # if "HTTP/1.1 404 Not Found" in keyword:
    if keyword in KEYWORDS_TO_WATCH:
        print("Attempting to restart Nginx...")
        try:
            # This requires appropriate sudo permissions for the user running the script
            # or configuring sudoers to allow this command without a password.
            subprocess.run(["sudo", "systemctl", "stop", "nginx"], check=True)
            time.sleep(2) # explicit sleep
            subprocess.run(["sudo", "systemctl", "start", "nginx"], check=True)
            print("Nginx restart command issued successfully.")
        except subprocess.CalledProcessError as e:
            print(f"Error restarting Nginx: {e}")
        except FileNotFoundError:
            print("Error: 'sudo' or 'systemctl' command not found. Is it in PATH?")
        except Exception as e:
            print(f"An unexpected error occurred during Nginx restart: {e}")

def monitor_log_file(log_file_path, keywords):
    """
    Monitors a log file for specified keywords and performs actions.
    """
    print(f"Monitoring log file: {log_file_path}")
    try:
        # Open the file in read mode
        with open(log_file_path, 'r') as f:
            # Go to the end of the file to only read new lines
            f.seek(0, os.SEEK_END)

            while True:
                line = f.readline()
                if not line:
                    # No new line, wait a bit and try again
                    time.sleep(1)
                    continue

                # Process the new line
                for keyword in keywords:
                    if keyword.lower() in line.lower(): # Case-insensitive search
                        perform_action(keyword, line)
                        # Break after first match to avoid multiple actions for one line
                        break

    except FileNotFoundError:
        print(f"Error: Log file not found at {log_file_path}")
    except PermissionError:
        print(f"Error: Permission denied to read {log_file_path}. Run with appropriate user/permissions.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    monitor_log_file(LOG_FILE_PATH, KEYWORDS_TO_WATCH)