import exifread  # type: ignore
import os.path
import subprocess
from datetime import datetime
from json_state import JsonState

BASE_DIR = os.path.expanduser("~/.timelapse")
if not os.path.exists(BASE_DIR):
    os.mkdir(BASE_DIR)

STATE_FILE = os.path.join(BASE_DIR, "capture_state.json")
IMAGE_DIR = os.path.join(BASE_DIR, "images")
if not os.path.exists(IMAGE_DIR):
    os.mkdir(IMAGE_DIR)

# Aperture choices:
# TODO: Run this command and cache results
# ❯ gphoto2 --get-config /main/capturesettings/aperture
# Label: Aperture
# Readonly: 0
# Type: RADIO
# Current: 11
# Choice: 0 3.5
# Choice: 1 4
# Choice: 2 4.5
# Choice: 3 5
# Choice: 4 5.6
# Choice: 5 6.3
# Choice: 6 7.1
# Choice: 7 8
# Choice: 8 9
# Choice: 9 10
# Choice: 10 11
# Choice: 11 13
# Choice: 12 14
# Choice: 13 16
# Choice: 14 18
# Choice: 15 20
# Choice: 16 22
# END

MIN_APERTURE_INDEX = 0
MAX_APERTURE_INDEX = 16


def parse_num(num_str: str):
    if "/" in num_str:
        num, den = map(int, num_str.split("/", maxsplit=1))
        return num / den
    else:
        return int(num_str)


def get_exif(fname: str):
    with open(fname, "rb") as f:
        exif = exifread.process_file(f)
        return {
            key: str(value) for key, value in exif.items() if key.startswith("EXIF")
        }


def capture(out_file: str, aperture_index: int):
    subprocess.run(
        [
            "gphoto2",
            # "--debug",
            # "--debug-logfile=/tmp/%s-logfile.txt" % datetime.now().strftime("%Y%m%d_%H%M%S"),
            "--set-config-index",
            "/main/capturesettings/aperture=%d" % aperture_index,
            "--capture-image-and-download",
            "--filename",
            out_file,
        ]
    )


def get_aperture_index(state):
    if not len(state["recent_metadata"]) or "last_aperture_index" not in state:
        # No previous images, just default to f/11
        return 10

    aperture = state["last_aperture_index"]
    last_shutter = parse_num(state["recent_metadata"][-1]["EXIF ExposureTime"])
    last_iso = parse_num(state["recent_metadata"][-1]["EXIF ISOSpeedRatings"])

    MAX_SHUTTER = 1 / 2
    MAX_ISO = 1000

    MIN_SHUTTER = 1 / 100
    MIN_ISO = 200

    if last_shutter > MAX_SHUTTER or last_iso > MAX_ISO:
        print(
            "Previous shutter (%.2f) or ISO (%d) too high. Attempting decrease aperture index."
            % (last_shutter, last_iso)
        )
        if aperture <= MIN_APERTURE_INDEX:
            print("Aperture already at min.")
        else:
            aperture -= 1
            print("Decreasing aperture to %d" % aperture)
            return aperture
    elif last_shutter < MIN_SHUTTER or last_iso < MIN_ISO:
        print(
            "Previous shutter (%.2f) or ISO (%d) too low. Attempting to increase aperture index."
            % (last_shutter, last_iso)
        )
        if aperture >= MAX_APERTURE_INDEX:
            print("Aperture already at max.")
        else:
            aperture += 1
            print("Increasing aperture to %d" % aperture)

    return aperture


def main(state=None):
    state = state or {}

    capture_time = datetime.now()
    today_image_dir = os.path.join(IMAGE_DIR, capture_time.strftime("%Y%m%d"))
    output_file = os.path.join(
        today_image_dir, capture_time.strftime("%Y%m%d_%H%M%S.cr2")
    )

    if "recent_metadata" not in state:
        state["recent_metadata"] = []

    aperture_index = get_aperture_index(state)
    state["last_aperture_index"] = aperture_index

    capture(out_file=output_file, aperture_index=aperture_index)

    state["recent_metadata"].append(get_exif(output_file))
    state["recent_metadata"] = state["recent_metadata"][-5:]


if __name__ == "__main__":
    with JsonState(STATE_FILE) as state:
        main(state)
