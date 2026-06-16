"""Build upip and mip artifacts from a selected pysm release."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import tempfile
from typing import Dict, Iterable, List, Optional
import urllib.request


PYPI_JSON_URL = "https://pypi.org/pypi/{project}/json"
PYPI_VERSION_JSON_URL = "https://pypi.org/pypi/{project}/{version}/json"
CORE_FILES = ("__init__.py", "pysm.py", "version.py")
MIP_DEPENDENCIES = (
    ("collections-deque", "latest"),
    ("collections-defaultdict", "latest"),
    ("logging", "latest"),
)
STAGING_FILES = (
    "LICENSE",
    "MANIFEST.in",
    "README.md",
    "pyproject.toml",
    "sdist_upip.py",
    "setup.py",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Fetch a selected pysm release and build the matching upysm "
            "MicroPython source distribution."
        )
    )
    parser.add_argument(
        "--pysm-version",
        default=os.environ.get("PYSM_VERSION", "latest"),
        help='pysm version to package, or "latest" (default: %(default)s)',
    )
    parser.add_argument(
        "--package-profile",
        choices=("core", "all"),
        default=os.environ.get("UPYSM_PACKAGE_PROFILE", "core"),
        help=(
            "core copies only the MicroPython runtime files; all copies every "
            "Python module from pysm (default: %(default)s)"
        ),
    )
    parser.add_argument(
        "--dist-dir",
        type=Path,
        default=Path("dist"),
        help="directory for built distributions (default: %(default)s)",
    )
    parser.add_argument(
        "--mip-dir",
        type=Path,
        default=Path("site"),
        help="directory for generated mip static files (default: %(default)s)",
    )
    parser.add_argument(
        "--no-mip",
        action="store_true",
        help="skip mip package layout generation",
    )
    parser.add_argument(
        "--work-dir",
        type=Path,
        default=Path("build/upysm"),
        help="scratch directory for downloads and staging (default: %(default)s)",
    )
    parser.add_argument(
        "--stage-dir",
        type=Path,
        help="explicit staging directory; implies a stable path for smoke tests",
    )
    parser.add_argument(
        "--keep-stage",
        action="store_true",
        help="leave the generated staging tree on disk",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="run twine check after building",
    )
    parser.add_argument(
        "--smoke",
        action="store_true",
        help="extract the built sdist and run the CPython smoke test",
    )
    parser.add_argument(
        "--upload",
        action="store_true",
        help="upload the resulting sdist with twine",
    )
    parser.add_argument(
        "--repository-url",
        help="optional twine repository URL for --upload",
    )
    parser.add_argument(
        "--metadata-file",
        type=Path,
        help="optional path for JSON metadata about the generated artifacts",
    )
    return parser.parse_args()


def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def read_json(url: str) -> Dict[str, object]:
    with urllib.request.urlopen(url, timeout=30) as response:
        return json.load(response)


def resolve_pysm_version(requested: str) -> str:
    requested = requested.strip()
    if not requested or requested == "latest":
        data = read_json(PYPI_JSON_URL.format(project="pysm"))
        return data["info"]["version"]
    if requested.startswith("v"):
        return requested[1:]
    return requested


def find_pysm_sdist(version: str) -> Dict[str, object]:
    data = read_json(PYPI_VERSION_JSON_URL.format(
        project="pysm",
        version=version,
    ))
    for item in data.get("urls", []):
        if item.get("packagetype") == "sdist":
            return item
    raise SystemExit("No source distribution found for pysm {0}".format(
        version
    ))


def download_file(
    url: str,
    destination: Path,
    expected_sha256: Optional[str],
) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256()
    with urllib.request.urlopen(url, timeout=60) as response:
        with destination.open("wb") as output:
            while True:
                chunk = response.read(1024 * 128)
                if not chunk:
                    break
                output.write(chunk)
                digest.update(chunk)

    if expected_sha256 and digest.hexdigest() != expected_sha256:
        raise SystemExit(
            "sha256 mismatch for {0}: expected {1}, got {2}".format(
                destination,
                expected_sha256,
                digest.hexdigest(),
            )
        )


def safe_extract_tar(archive: Path, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    root = destination.resolve()
    with tarfile.open(archive, "r:*") as tar:
        for member in tar.getmembers():
            target = (destination / member.name).resolve()
            try:
                target.relative_to(root)
            except ValueError:
                raise SystemExit(
                    "Refusing to extract path outside destination: {0}".format(
                        member.name
                    )
                )
        tar.extractall(destination)


def extracted_root(destination: Path) -> Path:
    roots = [path for path in destination.iterdir() if path.is_dir()]
    if len(roots) != 1:
        raise SystemExit(
            "Expected exactly one root directory in {0}, found {1}".format(
                destination,
                len(roots),
            )
        )
    return roots[0]


def read_version_from_source(source_root: Path) -> str:
    version_file = source_root / "pysm" / "version.py"
    namespace: Dict[str, object] = {}
    exec(version_file.read_text(encoding="utf-8"), namespace)
    version = namespace.get("__version__")
    if not isinstance(version, str):
        raise SystemExit("Could not read __version__ from {0}".format(
            version_file
        ))
    return version


def prepare_stage(
    root: Path,
    source_root: Path,
    stage_dir: Path,
    profile: str,
) -> None:
    if stage_dir.exists():
        shutil.rmtree(stage_dir)
    stage_dir.mkdir(parents=True)

    for filename in STAGING_FILES:
        shutil.copy2(root / filename, stage_dir / filename)

    source_package = source_root / "pysm"
    target_package = stage_dir / "pysm"
    target_package.mkdir()

    if profile == "core":
        filenames = [source_package / filename for filename in CORE_FILES]
    else:
        filenames = sorted(source_package.glob("*.py"))

    for source_file in filenames:
        if not source_file.exists():
            raise SystemExit("Missing expected pysm file: {0}".format(
                source_file
            ))
        shutil.copy2(source_file, target_package / source_file.name)


def package_file_names(stage_dir: Path) -> List[str]:
    package_dir = stage_dir / "pysm"
    return sorted(path.name for path in package_dir.glob("*.py"))


def copy_mip_package(stage_dir: Path, target_dir: Path) -> None:
    package_dir = target_dir / "pysm"
    package_dir.mkdir(parents=True, exist_ok=True)

    for filename in package_file_names(stage_dir):
        shutil.copy2(stage_dir / "pysm" / filename, package_dir / filename)


def mip_package_data(version: str, files: Iterable[str]) -> Dict[str, object]:
    return {
        "version": version,
        "urls": [
            ["pysm/{0}".format(filename), "pysm/{0}".format(filename)]
            for filename in files
        ],
        "deps": [list(item) for item in MIP_DEPENDENCIES],
    }


def write_json(path: Path, data: Dict[str, object]) -> None:
    path.write_text(
        json.dumps(data, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def write_index(mip_dir: Path, version: str) -> None:
    mip_dir.joinpath(".nojekyll").write_text("", encoding="utf-8")
    mip_dir.joinpath("index.html").write_text(
        """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>upysm MicroPython package</title>
</head>
<body>
  <h1>upysm</h1>
  <p>Latest version: {version}</p>
  <pre>mpremote mip install https://pgularski.github.io/upysm/</pre>
  <pre>mpremote mip install https://pgularski.github.io/upysm/{version}/</pre>
</body>
</html>
""".format(version=version),
        encoding="utf-8",
    )


def generate_mip_layout(stage_dir: Path, mip_dir: Path, version: str) -> None:
    if mip_dir.exists():
        shutil.rmtree(mip_dir)
    mip_dir.mkdir(parents=True)

    files = package_file_names(stage_dir)
    package_data = mip_package_data(version, files)

    for target in (mip_dir, mip_dir / "latest", mip_dir / version):
        target.mkdir(parents=True, exist_ok=True)
        copy_mip_package(stage_dir, target)
        write_json(target / "package.json", package_data)

    write_index(mip_dir, version)
    validate_mip_layout(mip_dir, version)


def validate_mip_layout(mip_dir: Path, version: str) -> None:
    for target in (mip_dir, mip_dir / "latest", mip_dir / version):
        package_json = target / "package.json"
        data = json.loads(package_json.read_text(encoding="utf-8"))

        if data.get("version") != version:
            raise SystemExit(
                "Unexpected mip version in {0}: {1}".format(
                    package_json,
                    data.get("version"),
                )
            )

        for destination, source in data.get("urls", []):
            if destination != source:
                raise SystemExit(
                    "Unexpected mip mapping in {0}: {1!r}".format(
                        package_json,
                        [destination, source],
                    )
                )
            if not (target / source).exists():
                raise SystemExit(
                    "Missing mip source file referenced by {0}: {1}".format(
                        package_json,
                        source,
                    )
                )


def has_distribution(name: str) -> bool:
    try:
        from importlib import metadata
    except ImportError:
        try:
            import pkg_resources
        except ImportError:
            return False
        try:
            pkg_resources.get_distribution(name)
        except pkg_resources.DistributionNotFound:
            return False
        return True

    try:
        metadata.version(name)
    except metadata.PackageNotFoundError:
        return False
    return True


def build_sdist(stage_dir: Path, dist_dir: Path, version: str) -> List[Path]:
    dist_dir.mkdir(parents=True, exist_ok=True)
    expected = dist_dir / "upysm-{0}.tar.gz".format(version)
    if expected.exists():
        expected.unlink()
    orig = dist_dir / "upysm-{0}.tar.gz.orig".format(version)
    if orig.exists():
        orig.unlink()

    if has_distribution("build"):
        command = [
            sys.executable,
            "-m",
            "build",
            "--sdist",
            "--outdir",
            str(dist_dir.resolve()),
        ]
    else:
        command = [
            sys.executable,
            "setup.py",
            "sdist",
            "--dist-dir",
            str(dist_dir.resolve()),
        ]

    subprocess.run(command, cwd=str(stage_dir), check=True)

    for orig in dist_dir.glob("*.orig"):
        orig.unlink()

    if not expected.exists():
        raise SystemExit("Build completed but no upysm sdist was found")
    return [expected]


def run_twine_check(distributions: List[Path]) -> None:
    if not has_distribution("twine"):
        raise SystemExit(
            "twine is required for --check. Install requirements.txt first."
        )
    subprocess.run(
        [sys.executable, "-m", "twine", "check"]
        + [str(path) for path in distributions],
        check=True,
    )


def run_smoke_test(root: Path, sdist: Path, work_dir: Path) -> None:
    smoke_dir = work_dir / "smoke"
    if smoke_dir.exists():
        shutil.rmtree(smoke_dir)
    safe_extract_tar(sdist, smoke_dir)
    package_root = extracted_root(smoke_dir)
    subprocess.run(
        [sys.executable, str(root / "test" / "upysm_smoke.py")],
        cwd=str(package_root),
        check=True,
    )


def upload(distributions: List[Path], repository_url: Optional[str]) -> None:
    if not has_distribution("twine"):
        raise SystemExit(
            "twine is required for --upload. Install requirements.txt first."
        )
    command = [sys.executable, "-m", "twine", "upload"]
    if repository_url:
        command.extend(["--repository-url", repository_url])
    command.extend(str(path) for path in distributions)
    subprocess.run(command, check=True)


def write_metadata(
    path: Path,
    version: str,
    distributions: List[Path],
    mip_dir: Optional[Path],
    package_profile: str,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    write_json(path, {
        "version": version,
        "package_profile": package_profile,
        "sdists": [str(item) for item in distributions],
        "mip_dir": str(mip_dir) if mip_dir else None,
    })


def main() -> None:
    args = parse_args()
    root = project_root()
    dist_dir = (root / args.dist_dir).resolve()
    mip_dir = None if args.no_mip else (root / args.mip_dir).resolve()
    work_dir = (root / args.work_dir).resolve()
    downloads_dir = work_dir / "downloads"
    extract_dir = work_dir / "source"

    pysm_version = resolve_pysm_version(args.pysm_version)
    sdist_info = find_pysm_sdist(pysm_version)
    sdist_path = downloads_dir / sdist_info["filename"]

    print("Packaging pysm {0} as upysm {0}".format(pysm_version), flush=True)
    download_file(
        sdist_info["url"],
        sdist_path,
        sdist_info.get("digests", {}).get("sha256"),
    )

    if extract_dir.exists():
        shutil.rmtree(extract_dir)
    safe_extract_tar(sdist_path, extract_dir)
    source_root = extracted_root(extract_dir)

    source_version = read_version_from_source(source_root)
    if source_version != pysm_version:
        raise SystemExit(
            "Downloaded pysm version {0}, expected {1}".format(
                source_version,
                pysm_version,
            )
        )

    stage_dir = (
        (root / args.stage_dir).resolve()
        if args.stage_dir
        else Path(tempfile.mkdtemp(prefix="upysm-stage-", dir=str(work_dir)))
    )
    prepare_stage(root, source_root, stage_dir, args.package_profile)

    distributions = build_sdist(stage_dir, dist_dir, pysm_version)
    if mip_dir:
        generate_mip_layout(stage_dir, mip_dir, pysm_version)
    if args.check:
        run_twine_check(distributions)
    if args.smoke:
        run_smoke_test(root, distributions[-1], work_dir)
    if args.upload:
        upload(distributions, args.repository_url)
    if args.metadata_file:
        write_metadata(
            (root / args.metadata_file).resolve(),
            pysm_version,
            distributions,
            mip_dir,
            args.package_profile,
        )

    print("Built:")
    for path in distributions:
        print("  {0}".format(path))
    if mip_dir:
        print("Mip: {0}".format(mip_dir))
    print("Stage: {0}".format(stage_dir))

    if not args.keep_stage and not args.stage_dir:
        shutil.rmtree(stage_dir)


if __name__ == "__main__":
    main()
