
"""
Patch ESP-IDF's libnet80211.a to allow raw TX of deauth/disassoc frames.

The closed-source WiFi blob's ieee80211_raw_frame_sanity_check() rejects
management frame subtypes 0xA0 (disassoc) and 0xC0 (deauth). This script
patches the function body in ieee80211_output.o to return 0 (ESP_OK)
immediately, then re-archives it.

Supported targets:
- Xtensa: replace the prologue with `movi.n a2, 0; retw.n`
- RISC-V: replace the prologue with `li a0, 0; ret`

Usage: patch.py <libnet80211.a> <objcopy> <ar> <output.a>
"""
import sys, subprocess, shutil, tempfile, os

FUNC_SECTION = ".text.ieee80211_raw_frame_sanity_check"
FUNC_NAME = "ieee80211_raw_frame_sanity_check"

PATCHES = {
    "xtensa": {
        "expected_prefix": bytes([0x36, 0x81, 0x00]),  # entry a1, 64
        "patch": bytes([0x36, 0x81, 0x00, 0x0c, 0x02, 0x1d, 0xf0]),
    },
    "riscv": {
        "expected_prefix": bytes([0x79, 0x71, 0x06, 0xd6]),  # addi sp,sp,-48 ; sw ra,44(sp)
        "patch": bytes([0x01, 0x45, 0x82, 0x80]),  # li a0, 0 ; ret
    },
}


def find_section_offset(objdump, obj_path, section_name):
    """Find file offset and size of a section in an ELF .o file."""
    out = subprocess.check_output(
        [objdump, "-h", obj_path], text=True
    )
    for line in out.splitlines():
        parts = line.split()
        if len(parts) >= 7 and parts[1] == section_name:
            size = int(parts[2], 16)
            file_off = int(parts[5], 16)
            return file_off, size
    return None, None


def find_func_offset_in_section(objdump, obj_path, section_name, func_name):
    """Find the function entry offset within its section."""
    out = subprocess.check_output(
        [objdump, "-d", "-j", section_name, obj_path], text=True
    )
    for line in out.splitlines():
        if f"<{func_name}>:" in line:
            # Format: "0000005c <ieee80211_raw_frame_sanity_check>:"
            addr_str = line.strip().split()[0].strip()
            return int(addr_str, 16)
    return None


def detect_architecture(objdump, obj_path):
    """Detect the architecture from objdump metadata."""
    out = subprocess.check_output([objdump, "-f", obj_path], text=True).lower()
    if "riscv" in out:
        return "riscv"
    if "xtensa" in out:
        return "xtensa"
    return None


def main():
    if len(sys.argv) != 5:
        print(f"Usage: {sys.argv[0]} <libnet80211.a> <objcopy> <ar> <output.a>")
        sys.exit(1)

    lib_in, objcopy, ar, lib_out = sys.argv[1:5]
    objdump = objcopy.replace("objcopy", "objdump")

    with tempfile.TemporaryDirectory() as tmpdir:
        # Copy archive and extract the target .o
        lib_work = os.path.join(tmpdir, "libnet80211.a")
        shutil.copy2(lib_in, lib_work)

        obj_name = "ieee80211_output.o"
        subprocess.check_call([ar, "x", lib_work, obj_name], cwd=tmpdir)
        obj_path = os.path.join(tmpdir, obj_name)

        # Find section file offset
        sec_off, sec_size = find_section_offset(objdump, obj_path, FUNC_SECTION)
        if sec_off is None:
            print(f"ERROR: section {FUNC_SECTION} not found")
            sys.exit(1)

        # Find function entry within section
        func_off = find_func_offset_in_section(objdump, obj_path, FUNC_SECTION, FUNC_NAME)
        if func_off is None:
            print(f"ERROR: function symbol {FUNC_NAME} not found in {FUNC_SECTION}")
            sys.exit(1)

        arch = detect_architecture(objdump, obj_path)
        if arch not in PATCHES:
            print(f"ERROR: unsupported architecture for {obj_path}: {arch}")
            sys.exit(1)

        patch_info = PATCHES[arch]
        patch = patch_info["patch"]
        file_off = sec_off + func_off
        expected_prefix = patch_info["expected_prefix"]

        # Check if already patched or needs patching
        with open(obj_path, "rb") as f:
            f.seek(file_off)
            existing = f.read(len(patch))

        if existing == patch:
            print(f"Already patched at 0x{file_off:x}, skipping")
            shutil.copy2(lib_work, lib_out)
            return

        if existing[:len(expected_prefix)] != expected_prefix:
            print(f"ERROR: expected prologue {expected_prefix.hex()} at offset "
                  f"0x{file_off:x}, got {existing[:len(expected_prefix)].hex()}")
            sys.exit(1)

        # Apply patch
        with open(obj_path, "r+b") as f:
            f.seek(file_off)
            f.write(patch)

        print(f"Patched {FUNC_SECTION} at file offset 0x{file_off:x} "
              f"(section 0x{sec_off:x} + 0x{func_off:x}): "
              f"{existing[:len(expected_prefix)].hex()}... -> {patch.hex()}")

        # Replace .o in archive
        subprocess.check_call([ar, "r", lib_work, obj_name], cwd=tmpdir)

        shutil.copy2(lib_work, lib_out)
        print(f"Written patched library to {lib_out}")


if __name__ == "__main__":
    main()
