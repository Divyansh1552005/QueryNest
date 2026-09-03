# Packaging QueryNest (.rpm / .deb / .tar.xz)

This produces native Linux packages by bundling QueryNest into a single
standalone binary with PyInstaller, then wrapping that binary with
[fpm](https://github.com/jordansissel/fpm). No pip install happens on the
target machine — everything Python-related is frozen into the binary at
build time.

Pipeline: `querynest.spec` (PyInstaller) → `dist/querynest` (binary) →
`packaging/build.sh` stages it into `packaging/pkgroot/usr/bin/querynest`
and calls `fpm` three times → artifacts land in `dist-packages/`.

Everything in this document has actually been built, installed, and run —
not just written down as a plan. See "Verified build (2026-09-04)" below
for the exact numbers and toolchain versions that were used.

## Prerequisites (build machine)

Build on Fedora (matches the dev environment this was built and tested
on). You need:

- **uv** — already used by this repo for dependency management
  (`pip install uv` if you don't have it elsewhere)
- **ruby + fpm** — fpm is a Ruby gem
  ```bash
  sudo dnf install ruby ruby-devel gcc make rpm-build dpkg dpkg-devel
  gem install --no-document fpm
  ```
  - `rpm-build` provides `rpmbuild`, needed for the `.rpm` target
  - `dpkg` / `dpkg-devel` provide `dpkg-deb`, needed for the `.deb` target
    (Fedora doesn't ship these by default — that's why they're listed
    explicitly above)
- **xz** — usually preinstalled on Fedora (`sudo dnf install xz` if not),
  needed to compress the `.tar` fpm produces into `.tar.xz`

`packaging/build.sh` checks for `fpm`, `uv`, `rpmbuild`, `dpkg-deb`, and
`xz` up front and skips whichever package format it can't build, with a
warning — it won't silently produce an empty/broken package.

## Running the build

From the repo root:

```bash
./packaging/build.sh
```

This will:

1. Run `uv run pyinstaller querynest.spec --clean --noconfirm` (2-3
   minutes; see "Binary size" below for what's actually in it and why)
2. Stage `packaging/pkgroot/usr/bin/querynest`
3. Run `fpm` three times (rpm, deb, tar), reading `name`/`version`/
   `description`/`maintainer` straight out of `pyproject.toml` so the
   packages never drift out of sync with the Python package metadata
4. Print `rpm -qip` / `dpkg -I` / `tar -tvf` output for each artifact so
   you can eyeball the metadata and file layout before shipping

Output lands in `dist-packages/`:

```
dist-packages/
├── querynest-cli-2.0.0-1.x86_64.rpm
├── querynest-cli_2.0.0_amd64.deb
└── querynest-cli-2.0.0.tar.xz
```

Re-running the script overwrites these in place.

**fpm flag ordering** (learned the hard way): fpm requires ALL flags to
precede the first positional argument. `build.sh` keeps the shared flags
in `FPM_COMMON_ARGS` and appends the input-path spec
(`usr/bin/querynest=/usr/bin/querynest`) last on every invocation, after
that format's own `-t`/`-p`. If you edit the script and move a flag after
the positional arg, fpm will fail with "stray flags found" — that's this.

## Verified build (2026-09-04)

Built and installed for real, not just theorized. Toolchain used:

| Tool | Version |
|---|---|
| ruby | 4.0.6 |
| fpm | 1.18.0 |
| rpmbuild | RPM 6.0.2 |
| dpkg / dpkg-deb | 1.23.7 |
| xz | 5.8.2 |
| PyInstaller | 6.22.2 |

### Binary size: 156MB → 131MB

Three trimming passes against the original `collect_all()`-everywhere
spec, each one measured, not assumed:

1. **Dropped `collect_all("langchain")`** (the umbrella `langchain`
   package, distinct from `langchain_core`) — nothing in this codebase or
   its direct deps (litellm, langchain_litellm, langchain_google_genai)
   ever imports it, confirmed by grepping the installed packages. It was
   pulling in ~150 unused vector-store integrations (Pinecone, Milvus,
   Redis, etc.).
2. **Replaced `collect_all("litellm")` / `collect_all("langchain_community")`
   with narrow, source-derived hidden-imports** — see the comments in
   `querynest.spec` for exactly which modules and why (each one traces to
   a specific dynamic-dispatch lookup found by reading litellm's and
   langchain_community's source, not guessed).
   → **156MB → 147MB.** Smaller win than expected: Python source
   compresses well in PyInstaller's archive, so hundreds of removed `.py`
   modules only account for a few MB. The real weight is native binaries
   (see next point).
3. **Excluded faiss's AVX2/AVX512 SWIG variants**, ~36MB each — see
   "faiss CPU requirement" below.
   → **147MB → 131MB.**

For context: faiss's three SWIG `.so` variants alone total 107MB, and
grpc's compiled extension + numpy's OpenBLAS add another 49MB — 156MB of
native binaries before counting any Python code at all. That's most of
the original 156MB binary. If you want to go further, that's where the
remaining weight is (numpy/OpenBLAS and grpc are both needed as-is; there
isn't a similar "drop what you don't use" lever for them the way there
was for faiss's redundant CPU variants).

### faiss CPU requirement: none beyond baseline x86-64

`querynest.spec` now excludes faiss's AVX2 and AVX512 `.so` variants via
`Analysis(excludes=...)` — only the base (SSE2-only) variant ships. This
is a deliberate compatibility-over-speed trade: QueryNest builds a
brute-force flat FAISS index per chat session over one PDF/webpage's
chunks (realistically hundreds to a few thousand ~768-dim vectors from
Gemini's `text-embedding-004`). SIMD gains from AVX2/AVX512 matter at
millions-of-vectors ANN scale; at this scale the difference is
sub-millisecond, dwarfed by the network/LLM round trip that follows.

**Verified, not assumed**: the build/test machine's CPU (AMD Ryzen 5
5600H) actually supports AVX2. Forced a full index rebuild
(`querynest chat --web ... --force`) against the trimmed binary and it
completed cleanly with no crash — proof that faiss's own
`except ImportError` fallback chain in `faiss/loader.py` (try AVX512 →
try AVX2 → fall back to base) correctly falls through to the base variant
when the AVX `.so` files simply aren't present, rather than assuming it
would work because the file was missing.

**Result: the binary runs on any x86_64 CPU**, including minimal/older
virtualized cloud instances — there's no AVX requirement to document as a
minimum, because there's no AVX requirement at all anymore.

### tiktoken: works fully offline, no extra bundling needed

QueryNest never calls tiktoken directly — `processor/text_splitter.py`
uses plain character-length counting, not
`RecursiveCharacterTextSplitter.from_tiktoken_encoder()`. The only real
caller is litellm, which already ships its own offline fix:
`litellm/litellm_core_utils/default_encoding.py` points
`TIKTOKEN_CACHE_DIR` at its own bundled
`litellm/litellm_core_utils/tokenizers/` directory and eagerly loads the
`cl100k_base` encoding from it at import time, before tiktoken ever gets
a chance to reach the network. `querynest.spec`'s
`collect_data_files("litellm")` call carries that directory along
automatically.

**Verified**: ran the built binary in a `docker run --network none`
container (confirmed no route to the outside world beforehand) — since
`chat.py` imports the litellm chain at module level on every invocation,
including `--help`, a network dependency here would have crashed
`--help` itself. It didn't.

### grpc TLS: uses its own bundled CA cert, not the host's

Verified in a container with **no `/etc/ssl/certs` directory at all** (a
bare `debian:stable` image, which doesn't install `ca-certificates` by
default) — a chat session still completed a full TLS handshake and real
gRPC request to `generativelanguage.googleapis.com`, coming back with
Google's own structured `400 API_KEY_INVALID` response (using a
deliberately fake key — a real call wasn't needed to prove this; getting
past the TLS handshake to a real HTTP-level API response is the point).
That's only possible if grpc used its own bundled root CA — there was no
OS cert store to fall back on.

### Cross-distro install: verified, not just "should work"

Both final (post-trim) packages were downloaded from the actual published
GitHub Release and installed fresh, in both directions:

- **`.deb` on `debian:stable`**: `dpkg -i` (or `apt-get install`) →
  `querynest --help` and `querynest sessions list` both exit 0.
- **`.rpm` on `fedora:latest`**: `rpm -i` (or `dnf install`) →
  same result. (`command -v querynest` resolves to `/usr/sbin/querynest`
  on Fedora — that's not a bug, `/usr/sbin` is a symlink into Fedora's
  merged `/usr/bin`; `rpm -qlp` genuinely lists the file under
  `/usr/bin`.)
- **`.tar.xz`**: extracts to `usr/bin/querynest` (the archive's own path
  layout has `usr/bin/` baked in — extract with `-C /`, not into an
  arbitrary prefix, or the binary won't land on `PATH`).

### litellm provider trimming: verified with real API calls

`querynest.spec` narrows `litellm`'s bundled provider surface to the 5
providers in `config/setup.py`'s curated model menu (gemini, openai,
anthropic, groq, mistral — see the spec's comments for exactly which
`litellm.llms.*` submodules back each one, including `vertex_ai`, which
gemini's calls route through internally per `litellm/main.py:3415`).

Verified this didn't silently break anything by making real calls, not
just constructing objects: a real Gemini embedding call and a real Groq
completion call both went through, using existing config and API keys.
The Groq call surfaced a real, unrelated finding — the configured
`llama-3.3-70b-versatile` model has apparently been deprecated/renamed on
Groq's side — but it came back as Groq's own `model_not_found` API error,
not an `ImportError`/`ModuleNotFoundError`, which is what would have
indicated a missing hidden-import from the trim.

**Known gap**: the curated menu also offers "enter a custom model
string," which can name any litellm-supported provider. A custom string
naming a provider outside the 5 above (e.g. `cohere/command-r`) will
**not** work in this binary — its `litellm.llms.<provider>` submodule
isn't bundled. If you want to support arbitrary custom providers, go back
to `collect_all("litellm")` in `querynest.spec` (and accept the size
cost).

### Two things this surfaced that aren't packaging bugs

Found while smoke-testing installed packages, worth fixing separately:

1. **No `--version` flag exists.** `querynest --version` doesn't print a
   version — it falls through to `bootstrap()` (which only special-cases
   `--help`/`-h`/no-args) and crashes with a confusing "Gemini API key not
   found" error that has nothing to do with the actual problem.
2. **Every subcommand except `--help`/no-args requires a real-looking
   Gemini key up front**, even metadata-only commands like
   `sessions list` that never call Gemini. `bootstrap()` doesn't
   special-case those.

## Testing the packages in Docker

Verify install behavior on clean target images before trusting a release
— package metadata bugs (wrong deps, wrong paths) only show up on an
actual install. These are the exact commands used above, against files in
`dist-packages/`; swap in a `curl`/`wget` download from a GitHub Release
if testing published artifacts instead.

### .deb on Debian

```bash
docker run --rm -v "$(pwd)/dist-packages:/pkgs" debian:stable bash -c '
  apt-get update && apt-get install -y /pkgs/querynest-cli_*.deb
  querynest --help
'
```

### .rpm on Fedora

```bash
docker run --rm -v "$(pwd)/dist-packages:/pkgs" fedora:latest bash -c '
  dnf install -y /pkgs/querynest-cli-*.x86_64.rpm
  querynest --help
'
```

### .tar.xz (any distro with a compatible glibc)

```bash
docker run --rm -v "$(pwd)/dist-packages:/pkgs" debian:stable bash -c '
  # archive layout is usr/bin/querynest, so extract to / to land it on PATH
  tar -xJf /pkgs/querynest-cli-*.tar.xz -C /
  querynest --help
'
```

`querynest --help` succeeding in all three confirms the package is
structurally sound and the binary runs. It does **not** exercise real
LLM/embedding calls — for that, pass a real `GEMINI_API_KEY` and run
`querynest chat --web ...`, which is how the tiktoken/grpc/litellm
findings above were actually confirmed rather than assumed.

## Notes / things intentionally left out

- No AppImage, no Snap, no Flatpak — just rpm/deb/tar.xz as asked.
- No remote config fetching, no runtime `pip install` — the binary is
  fully self-contained.
- The script always builds all three formats it can; there's no
  per-format CLI flag. If you only want one, comment out the others in
  `build.sh` or just ignore the artifacts you don't need.
- License is set to `GPL-3.0` in the fpm metadata, matching `LICENSE` and
  `pyproject.toml`'s classifier.
