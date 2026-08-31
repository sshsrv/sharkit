from __future__ import annotations

import os
from typing import Any

from sharkit.tools.base import (
    ExecutionContext,
    OptionDefinition,
    Result,
    Tool,
    ToolMetadata,
)

VALID_SECTIONS = ("all", "gps", "camera", "timestamps")

GPS_TAGS = {
    "GPSLatitude",
    "GPSLatitudeRef",
    "GPSLongitude",
    "GPSLongitudeRef",
    "GPSAltitude",
    "GPSAltitudeRef",
    "GPSSpeed",
    "GPSSpeedRef",
    "GPSImgDirection",
    "GPSImgDirectionRef",
}

CAMERA_TAGS = {
    "Make",
    "Model",
    "LensModel",
    "LensMake",
    "FocalLength",
    "FNumber",
    "ExposureTime",
    "ISOSpeedRatings",
}

TIMESTAMP_TAGS = {
    "DateTime",
    "DateTimeOriginal",
    "DateTimeDigitized",
}

ALL_TAGS = GPS_TAGS | CAMERA_TAGS | TIMESTAMP_TAGS


def _dms_to_decimal(dms_tag: Any, ref_tag: Any) -> float | None:
    """Convert EXIF DMS (degrees/minutes/seconds) to decimal degrees."""
    try:
        values = getattr(dms_tag, "values", ())
        if not values or len(values) < 3:
            return None
        d = float(values[0].num) / float(values[0].den)
        m = float(values[1].num) / float(values[1].den)
        s = float(values[2].num) / float(values[2].den)
        decimal = d + m / 60.0 + s / 3600.0
        ref = str(ref_tag)
        if ref in ("S", "W"):
            decimal = -decimal
        return round(decimal, 6)
    except Exception:
        return None


class EXIFReaderTool(Tool):
    metadata = ToolMetadata(
        name="exif_reader",
        description="Read EXIF metadata from local image files",
        category="osint.util.image",
        author="sharkit",
        version="0.1.0",
        safety="safe",
        color="#27AE60",
    )

    def __init__(self) -> None:
        self._options: dict[str, OptionDefinition] = {
            "file": OptionDefinition(
                name="file",
                description="Path to the image file",
                required=True,
            ),
            "section": OptionDefinition(
                name="section",
                description="EXIF section to extract",
                required=True,
                default="all",
                choices=list(VALID_SECTIONS),
            ),
        }

    def get_options(self) -> dict[str, OptionDefinition]:
        return self._options

    def execute(self, context: ExecutionContext) -> Result:
        try:
            import exifread  # noqa: PLC0415
        except ImportError:
            return Result(
                success=False,
                error="exifread not installed. Run: pip install exifread",
            )

        file_path = context.options.get("file") or ""
        if not file_path:
            return Result(success=False, error="Option 'file' is required.")

        section = (context.options.get("section") or "all").strip().lower()
        if section not in VALID_SECTIONS:
            choices = ", ".join(sorted(VALID_SECTIONS))
            return Result(
                success=False,
                error=f"Invalid section '{section}'. Choose from: {choices}",
            )

        if not os.path.isfile(file_path):
            return Result(success=False, error=f"File not found: {file_path}")

        try:
            with open(file_path, "rb") as fh:  # noqa: PTH123
                tags = exifread.process_file(fh, details=False)
        except Exception as exc:
            return Result(success=False, error=f"Failed to read EXIF data: {exc}")

        if section == "all":
            target_tags = ALL_TAGS
        elif section == "gps":
            target_tags = GPS_TAGS
        elif section == "camera":
            target_tags = CAMERA_TAGS
        elif section == "timestamps":
            target_tags = TIMESTAMP_TAGS
        else:
            target_tags = ALL_TAGS

        filename = os.path.basename(file_path)
        lines: list[str] = [f"EXIF data for {filename} ({section}):"]

        for tag_name in sorted(target_tags):
            if tag_name in tags:
                tag_value = tags[tag_name]
                # Convert GPS coordinates to decimal
                if tag_name == "GPSLatitude" and "GPSLatitudeRef" in tags:
                    decimal = _dms_to_decimal(tag_value, tags["GPSLatitudeRef"])
                    if decimal is not None:
                        lines.append(f"  {tag_name}: {decimal}")
                        continue
                if tag_name == "GPSLongitude" and "GPSLongitudeRef" in tags:
                    decimal = _dms_to_decimal(tag_value, tags["GPSLongitudeRef"])
                    if decimal is not None:
                        lines.append(f"  {tag_name}: {decimal}")
                        continue
                lines.append(f"  {tag_name}: {tag_value.printable}")
            else:
                lines.append(f"  {tag_name}: N/A")

        result_text = "\n".join(lines)
        return Result(success=True, data={"result": result_text})
