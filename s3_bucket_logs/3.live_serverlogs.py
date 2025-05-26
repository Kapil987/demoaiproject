import time
import os
import subprocess
from collections import deque # For efficient queue operations

# --- Configuration ---
LOG_FILE_PATH = "/var/log/nginx/flask_error.log"
KEYWORDS_TO_WATCH = [
    "emerg",           # Emergency errors (very high severity)
    "crit",            # Critical errors
    "error",           # General errors (added 'error' keyword)
    "failed to connect",
    "HTTP/1.1 404 Not Found", # Note: 404s are usually in access logs, but if Nginx logs proxy 404s here, it's fine.
    "Connection refused"
]

# --- AI Feature: Basic Anomaly Detection Configuration ---
# This will store timestamps of recent "critical" error occurrences
critical_error_timestamps = deque()
ANOMALY_WINDOW_SECONDS = 5 # Check for anomalies within the last 60 seconds
ANOMALY_THRESHOLD_COUNT = 1 # If more than 5 critical errors in 60s, trigger anomaly alert
LAST_ANOMALY_ALERT_TIME = 0 # Timestamp of the last time an anomaly alert was sent
ANOMALY_ALERT_COOLDOWN = 300 # Don't send anomaly alerts more often than every 5 minutes (300 seconds)

# --- Action Cooldown Configuration (to prevent excessive actions/restarts) ---
# This dictionary stores the cooldown period (in seconds) for performing an action
# related to a specific keyword.
KEYWORD_ACTION_COOLDOWNS = {
    "failed to connect": 300, # Only attempt Nginx restart for this specific keyword every 5 minutes
    "Connection refused": 300, # Same for connection refused
    "emerg": 600,             # Emergency alerts might warrant an action every 10 minutes
    "crit": 600,              # Critical alerts every 10 minutes
    # "error": 120,             # General errors, maybe print a warning every 2 minutes
    "error": 10,             # General errors, maybe print a warning every 2 minutes
    "HTTP/1.1 404 Not Found": 60 # 404s can be very frequent; act less often if needed
}
# This dictionary will store the last time an action was taken for each specific keyword
last_action_time = {} # Key: keyword, Value: timestamp of last action

# --- End Configuration ---

def trigger_anomaly_alert():
    """
    Function to perform action when an anomaly (e.g., too many errors) is detected.
    This is a higher-level alert indicating a potential systemic issue.
    """
    global LAST_ANOMALY_ALERT_TIME
    current_time = time.time()

    # Apply cooldown to the anomaly alert itself
    if current_time - LAST_ANOMALY_ALERT_TIME > ANOMALY_ALERT_COOLDOWN:
        print("\n!!! --- ANOMALY DETECTED --- !!!")
        print(f"!!! High rate of critical errors: >{ANOMALY_THRESHOLD_COUNT} in {ANOMALY_WINDOW_SECONDS}s !!!")
        print("!!! Consider deeper investigation or escalated alert !!!")
        # --- Add more sophisticated anomaly actions here ---
        # e.g., Send a separate, higher-priority alert to a different monitoring system
        # e.g., Trigger a diagnostic script or auto-scaling action
        LAST_ANOMALY_ALERT_TIME = current_time
    else:
        print(f"   (Anomaly alert on cooldown. Next alert in {int(ANOMALY_ALERT_COOLDOWN - (current_time - LAST_ANOMALY_ALERT_TIME))}s)")

def perform_action(keyword, log_line):
    """
    This function defines what action to take when a keyword is found.
    It now includes action cooldown and contributes to anomaly detection.
    """
    current_time = time.time()
    
    # --- Action Cooldown Logic for individual keyword actions ---
    cooldown_period = KEYWORD_ACTION_COOLDOWNS.get(keyword, 0) # Get specific cooldown or 0 if not defined
    if keyword in last_action_time and \
       (current_time - last_action_time[keyword]) < cooldown_period:
        print(f"   (Action for '{keyword}' on cooldown. Skipping immediate action.)")
        return # Skip action if on cooldown

    print(f"!!! Keyword '{keyword}' detected in log line: {log_line.strip()}")
    last_action_time[keyword] = current_time # Update last action time for this keyword

    # --- Anomaly Detection Contribution ---
    # Only "severe" keywords contribute to the anomaly count for triggering a higher-level alert
    if keyword in ["error","emerg", "crit", "failed to connect", "Connection refused"]:
        print("in anomaly detection function",critical_error_timestamps)
        critical_error_timestamps.append(current_time)
        
        # Remove old timestamps outside the defined window
        while critical_error_timestamps and \
              (current_time - critical_error_timestamps[0]) > ANOMALY_WINDOW_SECONDS:
            print(f"in while loop current time: {current_time},critical_error_timestamps[0]: {critical_error_timestamps[0]} ANOMALY_WINDOW_SECONDS: {ANOMALY_WINDOW_SECONDS}, current - critical time{current_time - critical_error_timestamps[0]}")  
            critical_error_timestamps.popleft()

        # If the number of critical errors in the window exceeds the threshold, trigger anomaly
        if len(critical_error_timestamps) >= ANOMALY_THRESHOLD_COUNT:
            trigger_anomaly_alert()
    
    # --- Specific Actions based on Keywords (after cooldown and anomaly checks) ---
    # if keyword == "failed to connect" or keyword == "Connection refused":
    # if keyword == "failed to connect" or keyword == "Connection refused" or keyword == "error":
    if keyword == "failed to connect" or keyword == "Connection refused":
        print("Attempting to restart Nginx due to potential backend connection issues...")
        try:
            # Note: systemctl restart is often sufficient; stop+sleep+start is more forceful.
            # subprocess.run(["sudo", "systemctl", "restart", "nginx"], check=True)
            subprocess.run(["sudo", "systemctl", "stop", "nginx"], check=True)
            time.sleep(2) # Give it a moment to stop
            subprocess.run(["sudo", "systemctl", "start", "nginx"], check=True)
            print("Nginx restart command issued successfully.")
        except subprocess.CalledProcessError as e:
            print(f"Error restarting Nginx: {e}")
        except FileNotFoundError:
            print("Error: 'sudo' or 'systemctl' command not found. Is it in PATH?")
        except Exception as e:
            print(f"An unexpected error occurred during Nginx restart: {e}")
    elif keyword == "HTTP/1.1 404 Not Found":
        # For 404s, which are often just normal traffic or misconfigured URLs,
        # you might just want to print a notification or send a very low-priority alert.
        print("   (Note: 404 Not Found detected. This might be normal traffic or misconfigured URLs.)")
        # Example: send_low_priority_slack_message("Low priority: 404 detected in Nginx logs.")
    elif keyword in ["emerg", "crit", "error"]:
        print(f"   (General critical/error detected. Consider specific actions beyond restart.)")
        # Example: send_email("CRITICAL ALERT", f"Critical Nginx error: {log_line}")
    else:
        print("   (No specific action defined for this keyword yet.)")


def monitor_log_file(log_file_path, keywords):
    """
    Monitors a log file for specified keywords and performs actions.
    """
    print(f"Monitoring log file: {log_file_path}")
    print(f"Watching for keywords: {', '.join(keywords)}")
    print(f"Anomaly detection: {ANOMALY_THRESHOLD_COUNT} errors in {ANOMALY_WINDOW_SECONDS}s triggers alert.")
    print(f"Action cooldowns configured per keyword.")

    try:
        # Open the file in read mode
        with open(log_file_path, 'r') as f:
            f.seek(0, os.SEEK_END) # Go to the end of the file to only read new lines

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
                        break # Process only the first matching keyword per line

    except FileNotFoundError:
        print(f"Error: Log file not found at {log_file_path}")
    except PermissionError:
        print(f"Error: Permission denied to read {log_file_path}. Run with appropriate user/permissions.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    monitor_log_file(LOG_FILE_PATH, KEYWORDS_TO_WATCH)