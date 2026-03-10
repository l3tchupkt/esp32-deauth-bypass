# Sending Deauthentication Frames with ESP32 (Arduino IDE)

## Overview

Sending **WiFi deauthentication frames** with the ESP32 is normally blocked by limitations in **Espressif's ESP-IDF**. These restrictions prevent raw frame injection for certain packet types such as:

* Deauthentication frames
* Disassociation frames
* Authentication frames

However, a bypass exists that overrides the internal function responsible for validating raw frames:

```
ieee80211_raw_frame_sanity_check
```

By overriding this function to always return `0`, the ESP32 can send frames that are normally restricted.

This guide explains how to configure **Arduino IDE + Arduino-ESP32** and implement the bypass.

---

# ESP-IDF vs Arduino-ESP32

Understanding the difference is important.

| Framework     | Description                                          |
| ------------- | ---------------------------------------------------- |
| ESP-IDF       | Espressif’s official low-level development framework |
| Arduino-ESP32 | Arduino wrapper built on top of ESP-IDF              |

Arduino-ESP32 internally depends on a specific **ESP-IDF version**.

The original bypass was tested with:

```
ESP-IDF v4.1
commit: 5ef1b390026270503634ac3ec9f1ec2e364e23b2
```

However, no Arduino-ESP32 version ships with IDF 4.1.

The closest compatible version is:

```
Arduino-ESP32 2.0.0 RC1 (ESP-IDF v4.4)
```

Testing shows the same internal sanity check still exists, allowing the bypass to work.

---

# Bypassing `ieee80211_raw_frame_sanity_check`

Add the following function to your firmware:

```cpp
extern "C" int ieee80211_raw_frame_sanity_check(int32_t arg, int32_t arg2, int32_t arg3){
  return 0;
}
```

### What this does

This overrides the original ESP-IDF function and **forces the sanity check to always succeed**, enabling transmission of normally restricted WiFi frames.

---

# Required Linker Flag

The Arduino build system normally blocks duplicate function definitions.

To allow overriding the function, add the linker flag:

```
-zmuldefs
```

This allows multiple definitions of the same function during linking.

---

# Arduino IDE Setup

## Step 1 — Install Arduino IDE

Download and install the **latest Arduino IDE**.

---

## Step 2 — Add ESP32 Board Manager URLs

Open:

```
File → Preferences
```

Add the following URLs to **Additional Boards Manager URLs**:

```
https://dl.espressif.com/dl/package_esp32_index.json
https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_dev_index.json
```

---

## Step 3 — Install ESP32 Board Package

Open:

```
Tools → Board → Boards Manager
```

Search for:

```
esp32
```

Install:

```
esp32 by Espressif Systems
```

Recommended version:

```
2.0.10
```

---

## Step 4 — Install USB Drivers

Depending on your ESP32 board, install the required drivers.

### CP210X Driver

Used by many ESP32 development boards.

### CH340X Driver

Used by some clones.

Install both if unsure.

---

# (Optional) Build Configuration Changes

These steps are **only required if compiling the full ESP32 Marauder firmware from source**.

If you are just using the bypass in your own sketch, you can skip this section.

---

## Step 5 — Edit `platform.txt`

Open the following file:

```
C:\Users\<USERNAME>\AppData\Local\Arduino15\packages\esp32\hardware\esp32\2.0.10\platform.txt
```

---

## Step 6 — Add Compiler Warning Suppression

Add `-w` to these lines:

```
build.extra_flags.esp32
build.extra_flags.esp32s2
build.extra_flags.esp32s3
build.extra_flags.esp32c3
```

Example:

```
build.extra_flags.esp32=-w
```

---

## Step 7 — Add Linker Flag

Add the following flag to:

```
compiler.c.elf.libs.esp32
compiler.c.elf.libs.esp32s2
compiler.c.elf.libs.esp32s3
compiler.c.elf.libs.esp32c3
```

Add:

```
-zmuldefs
```

Example:

```
compiler.c.elf.libs.esp32=-zmuldefs
```

---

# Result

After applying the bypass and linker modification, the ESP32 can transmit **raw WiFi frames** including:

* Deauthentication frames
* Disassociation frames
* Authentication frames

This technique is used in tools such as **ESP32 Marauder firmware**.

---

---
![Author](https://img.shields.io/badge/Author-l3tchupkt-blue?style=for-the-badge&logo=github)
![Tech](https://img.shields.io/badge/Hardware-ESP32-orange?style=for-the-badge)

