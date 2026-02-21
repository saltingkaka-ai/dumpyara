#
# Copyright (C) 2022 Dumpyara Project
#
# SPDX-License-Identifier: GPL-3.0
#

from typing import Callable, Dict
from liblp.partition_tools.lpunpack import lpunpack as liblp_unpack
from pathlib import Path
from re import Pattern, compile
from sebaubuntu_libs.liblogging import LOGI
from shutil import move
from subprocess import STDOUT, check_output, run, CalledProcessError

from dumpyara.lib.libpayload import extract_android_ota_payload

def extract_payload(image: Path, output_dir: Path):
	extract_android_ota_payload(image, output_dir)

def extract_super(image: Path, output_dir: Path):
	unsparsed_super = output_dir / "super.unsparsed.img"

	# Unsparse jika perlu
	try:
		check_output(["simg2img", image, unsparsed_super], stderr=STDOUT)
	except Exception:
		LOGI(f"Failed to unsparse {image.name} or already raw")
	else:
		move(unsparsed_super, image)

	if unsparsed_super.is_file():
		unsparsed_super.unlink()

	# Coba lpunpack.py dulu (dari workflow)
	LOGI(f"Extracting {image.name} with lpunpack.py")
	try:
		result = run(
			["python3", "/usr/local/bin/lpunpack", str(image), str(output_dir)],
			capture_output=True,
			text=True,
			check=True
		)
		LOGI(f"Successfully extracted with lpunpack.py")
		return
	except (CalledProcessError, FileNotFoundError) as e:
		LOGI(f"lpunpack.py failed: {e}")
		if hasattr(e, 'stderr') and e.stderr:
			LOGI(f"Error output: {e.stderr}")

	# Fallback ke liblp (Python library)
	LOGI("Falling back to liblp...")
	try:
		liblp_unpack(image, output_dir)
	except Exception as e:
		LOGI(f"liblp failed: {e}")
		raise RuntimeError(f"Failed to extract {image.name}")

MULTIPARTITIONS: Dict[Pattern[str], Callable[[Path, Path], None]] = {
	compile(key): value
	for key, value in {
		"payload.bin": extract_payload,
		"super(?!.*(_empty)).*\\.img": extract_super,
	}.items()
}
