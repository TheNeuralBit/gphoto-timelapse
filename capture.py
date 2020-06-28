import exifread  # type: ignore
import json
import os.path
import subprocess
from json_state import JsonState

BASE_DIR = os.path.expanduser("~/.timelapse")
os.mkdir(BASE_DIR)

STATE_FILE = os.path.join(BASE_DIR, "capture_state.json")
IMAGE_DIR = os.path.join(BASE_DIR, "images")
os.mkdir(IMAGE_DIR)


def get_exif(fname: str):
    with open(fname, "rb") as f:
        exif = exifread.process_file(f)
        return {
            key: str(value) for key, value in exif.items() if key.startswith("EXIF")
        }


def capture(out_file: str):
    subprocess.run(["gphoto2", "--capture-image-and-download", "--filename", out_file])


def main():
    capture_time = datetime.now()
    today_image_dir = os.path.join(IMAGE_DIR, capture_time.strftime("%Y%m%d"))
    output_file = os.path.join(
        today_image_dir, capture_time.strftime("%Y%m%d_%H%M%S.cr2")
    )

    with JsonState(STATE_FILE) as state:
        if "recent_metadata" not in state:
            state["recent_metadata"] = []

        capture(output_file)

        state["recent_metadata"].append(get_exif(output_file))
        state["recent_metadata"] = state["recent_metadata"][-5:]


if __name__ == "__main__":
    main()
