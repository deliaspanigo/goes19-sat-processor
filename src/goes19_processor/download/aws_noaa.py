# src/goes19_processor/download/aws_noaa.py

import fsspec
from pathlib import Path
import os
import shutil
from typing import Optional, List
import datetime


def download_goes_files(
    product: str,
    year: str,
    day_of_year: str,
    hour: str,
    band: Optional[str] = None,
    output_dir: str = "../../data/raw",
    satellite: str = "19",
    all_files: bool = False,
    file_name: Optional[str] = None,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    overwrite: bool = False
) -> List[Path]:
    """
    Download GOES-19/16 files from S3 public bucket.
    
    Supports:
    - Single file (default: first available)
    - All files in prefix (--all)
    - Specific file by name (--file-name)
    - Range of hours (--start-time to --end-time)
    - Overwrite existing files (--overwrite)
    """
    downloaded = []

    # Handle time range if provided
    if start_time and end_time:
        start_dt = datetime.datetime.strptime(start_time, "%Y-%m-%d_%H:%M")
        end_dt = datetime.datetime.strptime(end_time, "%Y-%m-%d_%H:%M")
        current_dt = start_dt
        while current_dt <= end_dt:
            y = current_dt.strftime("%Y")
            doy = current_dt.strftime("%j")
            h = current_dt.strftime("%H")
            downloaded.extend(
                _download_from_prefix(
                    product, y, doy, h, bucket_name=f"noaa-goes{satellite}",
                    output_dir=output_dir, all_files=all_files, file_name=file_name,
                    band=band, overwrite=overwrite
                )
            )
            current_dt += datetime.timedelta(hours=1)
    else:
        # Single hour
        downloaded = _download_from_prefix(
            product, year, day_of_year, hour, bucket_name=f"noaa-goes{satellite}",
            output_dir=output_dir, all_files=all_files, file_name=file_name,
            band=band, overwrite=overwrite
        )

    return downloaded


def _download_from_prefix(
    product: str,
    year: str,
    day_of_year: str,
    hour: str,
    bucket_name: str,
    output_dir: str,
    all_files: bool,
    file_name: Optional[str],
    band: Optional[str],
    overwrite: bool
) -> List[Path]:
    """Internal helper: download from a single prefix"""
    prefix = f"{product}/{year}/{day_of_year.zfill(3)}/{hour.zfill(2)}/"
    s3_path = f"s3://{bucket_name}/{prefix}"

    print(f"Searching in: {s3_path}")

    try:
        fs = fsspec.filesystem('s3', anon=True)
        files = fs.ls(s3_path)

        if not files:
            print(f"No files found in {s3_path}")
            return []

        # Filter by band if specified (for ABI-L1b)
        if band:
            files = [f for f in files if f"C{band.zfill(2)}" in f]
            if not files:
                print(f"No files found for band {band} in {s3_path}")
                return []

        # Filter by exact filename if specified
        if file_name:
            files = [f for f in files if os.path.basename(f) == file_name]
            if not files:
                print(f"No match for specific file: {file_name}")
                return []

        # If not --all, take only the first one
        if not all_files:
            files = files[:1]

        downloaded_paths = []
        for remote_file in files:
            filename = os.path.basename(remote_file)
            local_dir = Path(output_dir) / bucket_name / product / year / day_of_year.zfill(3) / hour.zfill(2)
            local_dir.mkdir(parents=True, exist_ok=True)
            local_path = local_dir / filename

            remote_size = fs.info(remote_file)["size"]

            # Skip if exists and matches size (unless --overwrite)
            if local_path.exists():
                local_size = local_path.stat().st_size
                if local_size == remote_size and not overwrite:
                    print(f"✓ Already exists and size matches: {local_path}")
                    downloaded_paths.append(local_path)
                    continue
                else:
                    if overwrite:
                        print(f"Overwriting existing file: {local_path}")
                    else:
                        print(f"Size mismatch - downloading again: {local_path}")
                    local_path.unlink(missing_ok=True)

            # Download
            print(f"Downloading {remote_file} → {local_path}")
            with fs.open(remote_file, 'rb') as remote_f:
                with open(local_path, 'wb') as local_f:
                    shutil.copyfileobj(remote_f, local_f)

            print(f"Downloaded: {local_path}")
            downloaded_paths.append(local_path)

        return downloaded_paths

    except Exception as e:
        print(f"Error: {e}")
        return []