"""Raspberry Pi Service and Hardware monitoring using Discord Webhooks"""

import os
import time
import socket
from datetime import datetime, timedelta
import psutil
import requests

# Configuration constants
TIMER = 5  # in minutes
WEBHOOK_URL = "https://discord.com/api/webhooks/YOUR_DISCORD/WEBHOOK_URL"
SERVICES = [
    'service1', 'service2', 'service3'
]

def main():
    """Main function to initialize and start the monitoring with status updates."""
    print("Starting after 30 seconds...", flush=True)
    time.sleep(30)
    first_run = True

    while True:
        try:
            # Create embed data for Discord webhook
            embed = {
                "title": "Raspberry Pi Status",
                "color": 0x00ff00,
                "fields": [
                    {"name": f"**Uptime** (Push interval: {TIMER} minutes)", "value": get_uptime()},
                    {"name": "**Local IP**", "value": get_local_ip()},
                    {"name": "**External IP**", "value": get_external_ip()},
                    {"name": "**Services**", "value": get_service_status()}
                ],
                "footer": {"text": get_footer_info()}
            }

            # Add description only on the first run
            if first_run:
                embed["description"] = "**RPi started!**"
                first_run = False

            # Build the payload for the POST request
            data = {
                "embeds": [embed]
            }
            
            # Send the webhook
            response = requests.post(WEBHOOK_URL, json=data)
            if response.status_code == 204:
                print(f"Sent webhook successfully, waiting {TIMER * 60} seconds...", flush=True)
            else:
                print(f"Error at sending webhook - Status code:", str(response.status_code), "\n" + response.text, flush=True)
            time.sleep(TIMER * 60)

        except Exception as e:
            print("Error:", str(e), flush=True)
            
def get_local_ip():
    """Fetch the local IP address of the RPi."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            return local_ip
    except Exception as e:
        print("Error:", str(e), flush=True)
        return "Not available"

def get_uptime():
    """Return system uptime as a formatted string."""
    try:
        with open('/proc/uptime', 'r', encoding="utf-8") as file:
            uptime_string = str(timedelta(seconds = float(file.readline().split()[0])))
            hours = uptime_string.split(":")[0]
            minutes = uptime_string.split(":")[1]
            seconds = uptime_string.split(":")[2]
            seconds = seconds.split(".")[0]
            return(hours + " h, " + minutes + " m, " + seconds + " s") 
    except Exception as e:
        print("Error:", str(e), flush=True)
        return "Not available"

def get_ram_info():
    """Return available RAM in MB."""
    ram = psutil.virtual_memory()
    return round(ram.available / 1_000_000, 1)

def get_cpu_temperature():
    """Return CPU temperature (only for Raspberry Pi)."""
    try:
        res = os.popen('vcgencmd measure_temp').readline()
        return res.replace("temp=", "").replace("'C\n", "")
    except Exception as e:
        print("Error:", str(e), flush=True)
        return "Not available"

def get_external_ip():
    """Return the external IP address of the internet, connected with the RPi."""
    try:
        response = requests.get("http://ident.me/", timeout=10)
        return response.text.strip()
    except Exception as e:
        print("Error:", str(e), flush=True)
        return "Not available"

def get_internet_usage():
    """Return daily internet usage from vnstat."""
    try:
        res = os.popen('vnstat -d -s').read()
        usage_today = res.split("today")[1].split("/")[2].strip()
        return usage_today.replace("KiB", "KB").replace("MiB", "MB").replace("GiB", "GB")
    except Exception as e:
        print("Error:", str(e), flush=True)
        return "Not available"

def get_service_status():
    """Check the status of specified services and return formatted string."""
    status_messages = []
    for service in SERVICES:
        result = os.popen(f"systemctl is-active {service}.service").read().strip()
        if "failed" in result:
            status_messages.append(f":red_circle: {service} (error!)")
        elif "active" in result and "inactive" not in result:
            status_messages.append(f":green_circle: {service}")
    return "\n".join(status_messages)

def get_footer_info():
    """Compile footer information including CPU, RAM, and internet usage stats."""
    cpu_usage = psutil.cpu_percent()
    cpu_temp = get_cpu_temperature()
    ram_free = get_ram_info()
    internet_usage = get_internet_usage()
    timestamp = datetime.now()
    return (f"CPU Temp: {cpu_temp}°C, CPU Usage: {cpu_usage}%, RAM: {ram_free}MB free, "
            f"Traffic today: {internet_usage}\n{timestamp}")

if __name__ == "__main__":
    main()
