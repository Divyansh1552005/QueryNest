#!/usr/bin/env bash
#
# Builds the querynest PyInstaller binary and packages it as .rpm, .deb,
# and .tar.xz using fpm. See packaging/README.md for prerequisites.
#
# Usage:
#   ./packaging/build.sh
#
# Output:
#   dist-packages/querynest-cli-<version>-1.<arch>.rpm
#   dist-packages/querynest-cli_<version>_<arch>.deb
#   dist-packages/querynest-cli-<version>.tar.xz

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

PKGROOT="${REPO_ROOT}/packaging/pkgroot"
OUT_DIR="${REPO_ROOT}/dist-packages"

# --- Metadata pulled from pyproject.toml (kept as the single source of truth) ---
PKG_NAME="$(grep -m1 '^name *= *' pyproject.toml | sed -E 's/name *= *"([^"]+)"/\1/')"
PKG_VERSION="$(grep -m1 '^version *= *' pyproject.toml | sed -E 's/version *= *"([^"]+)"/\1/')"
PKG_DESCRIPTION="$(grep -m1 '^description *= *' pyproject.toml | sed -E 's/description *= *"([^"]+)"/\1/')"
PKG_MAINTAINER="$(grep -m1 '{ name = "' pyproject.toml | sed -E 's/.*name *= *"([^"]+)".*/\1/')"
PKG_LICENSE="GPL-3.0"   # matches LICENSE / pyproject.toml classifier — do not set to MIT, this repo is GPL-3.0
PKG_URL="https://github.com/Divyansh1552005/QueryNest"  # from `git remote -v` (origin); edit if it changes

if [[ -z "${PKG_NAME}" || -z "${PKG_VERSION}" ]]; then
  echo "ERROR: could not read name/version from pyproject.toml" >&2
  exit 1
fi

echo "==> Packaging ${PKG_NAME} ${PKG_VERSION} (license: ${PKG_LICENSE})"

# --- Tool checks (fail fast with a clear message instead of a cryptic fpm error) ---
missing=()
command -v fpm >/dev/null 2>&1 || missing+=("fpm")
command -v uv >/dev/null 2>&1 || missing+=("uv")
if ((${#missing[@]} > 0)); then
  echo "ERROR: missing required tool(s): ${missing[*]}" >&2
  echo "See packaging/README.md for install instructions." >&2
  exit 1
fi

HAVE_RPMBUILD=0
command -v rpmbuild >/dev/null 2>&1 && HAVE_RPMBUILD=1
HAVE_DPKG_DEB=0
command -v dpkg-deb >/dev/null 2>&1 && HAVE_DPKG_DEB=1
HAVE_XZ=0
command -v xz >/dev/null 2>&1 && HAVE_XZ=1

if ((HAVE_RPMBUILD == 0)); then
  echo "WARNING: rpmbuild not found — .rpm build will be skipped (install rpm-build)." >&2
fi
if ((HAVE_DPKG_DEB == 0)); then
  echo "WARNING: dpkg-deb not found — .deb build will be skipped (install dpkg-dev / dpkg)." >&2
fi
if ((HAVE_XZ == 0)); then
  echo "WARNING: xz not found — .tar.xz build will be skipped (install xz)." >&2
fi

# --- 1. Build the standalone binary with PyInstaller ---
echo "==> Running PyInstaller (this pulls in the full langchain/litellm surface, expect a few minutes and a ~150MB+ binary)"
uv run pyinstaller querynest.spec --clean --noconfirm

BIN_PATH="${REPO_ROOT}/dist/querynest"
if [[ ! -f "${BIN_PATH}" ]]; then
  echo "ERROR: PyInstaller did not produce ${BIN_PATH}" >&2
  exit 1
fi

# --- 2. Stage the pkgroot (what actually gets tarred/packaged: usr/bin/querynest) ---
echo "==> Staging pkgroot"
rm -rf "${PKGROOT}"
mkdir -p "${PKGROOT}/usr/bin"
cp "${BIN_PATH}" "${PKGROOT}/usr/bin/querynest"
chmod 0755 "${PKGROOT}/usr/bin/querynest"

mkdir -p "${OUT_DIR}"

# NOTE: fpm requires ALL flags to precede the first positional argument
# (the "usr/bin/querynest=/usr/bin/querynest" input-path spec below). If any
# flag comes after it, fpm treats it as a stray positional and errors out.
# So FPM_COMMON_ARGS holds only flags — the positional spec is appended last
# on each individual invocation, after that format's own -t/-p flags.
FPM_COMMON_ARGS=(
  -s dir
  -n "${PKG_NAME}"
  -v "${PKG_VERSION}"
  --license "${PKG_LICENSE}"
  --url "${PKG_URL}"
  --description "${PKG_DESCRIPTION}"
  --maintainer "${PKG_MAINTAINER}"
  -a native
  -C "${PKGROOT}"
)
FPM_INPUT_SPEC="usr/bin/querynest=/usr/bin/querynest"

# --- 3. .rpm ---
if ((HAVE_RPMBUILD == 1)); then
  echo "==> Building .rpm"
  RPM_OUT="${OUT_DIR}/${PKG_NAME}-${PKG_VERSION}-1.$(uname -m).rpm"
  rm -f "${RPM_OUT}"
  fpm "${FPM_COMMON_ARGS[@]}" -t rpm -p "${RPM_OUT}" "${FPM_INPUT_SPEC}"

  echo "----- rpm -qip ${RPM_OUT} -----"
  rpm -qip "${RPM_OUT}"
  echo "----- rpm -qlp ${RPM_OUT} (file list) -----"
  rpm -qlp "${RPM_OUT}"
fi

# --- 4. .deb ---
if ((HAVE_DPKG_DEB == 1)); then
  echo "==> Building .deb"
  DEB_OUT="${OUT_DIR}/${PKG_NAME}_${PKG_VERSION}_amd64.deb"
  rm -f "${DEB_OUT}"
  fpm "${FPM_COMMON_ARGS[@]}" -t deb -p "${DEB_OUT}" "${FPM_INPUT_SPEC}"

  echo "----- dpkg -I ${DEB_OUT} -----"
  dpkg -I "${DEB_OUT}" || dpkg-deb -I "${DEB_OUT}"
  echo "----- dpkg -c ${DEB_OUT} (file list) -----"
  dpkg -c "${DEB_OUT}" || dpkg-deb -c "${DEB_OUT}"
fi

# --- 5. .tar.xz ---
if ((HAVE_XZ == 1)); then
  echo "==> Building .tar.xz"
  TAR_OUT="${OUT_DIR}/${PKG_NAME}-${PKG_VERSION}.tar"
  rm -f "${TAR_OUT}" "${TAR_OUT}.xz"
  fpm "${FPM_COMMON_ARGS[@]}" -t tar -p "${TAR_OUT}" "${FPM_INPUT_SPEC}"
  xz -f -9 "${TAR_OUT}"

  echo "----- tar -tvf ${TAR_OUT}.xz -----"
  tar -tvf "${TAR_OUT}.xz"
fi

echo "==> Done. Artifacts in ${OUT_DIR}:"
ls -lh "${OUT_DIR}"
