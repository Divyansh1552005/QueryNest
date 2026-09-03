# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller build spec for QueryNest.

Produces a single-file `querynest` binary (onefile mode). Build with:

    uv run pyinstaller querynest.spec --clean --noconfirm

Entry point mirrors [project.scripts] in pyproject.toml
(querynest.cli.main:main) — that file's `if __name__ == "__main__"` guard
is what actually runs when PyInstaller executes this as a script.

--- Why collect_all() for some packages, collect_submodules()/explicit
    hidden-imports for others ---
Most of this project's real dependency risk isn't in querynest's own code,
it's in packages that load native extensions or data files dynamically
(via importlib/pkgutil) rather than through imports PyInstaller's static
analysis can see. `collect_all` pulls in a package's binaries + data files
+ submodules unconditionally — correct, but expensive, so it's reserved
below for packages that are either small or genuinely need everything.

For the two size culprits (litellm, langchain_community) we instead grep
the actual usage in src/querynest/ and hidden-import exactly the concrete
modules that dynamic dispatch would otherwise resolve to at runtime. See
the LITELLM_HIDDEN_IMPORTS / LANGCHAIN_COMMUNITY_HIDDEN_IMPORTS comments
below for how each entry was derived — this is not a guess, each one
traces to a specific runtime lookup found by reading litellm's and
langchain_community's source.

Trimming history: an earlier version of this spec used
collect_all("litellm"), collect_all("langchain_community"), and
collect_all("langchain") and produced a 156MB binary. Of those three,
collect_all("langchain") — the umbrella `langchain` package, distinct
from `langchain_core` — turned out to be pulling in ~150 vector-store
integrations (Pinecone, Milvus, Redis, etc.) despite nothing in this
codebase or its direct deps (litellm, langchain_litellm,
langchain_google_genai) ever importing bare `langchain`. It's dropped
entirely below.

--- KNOWN RISKS TO TEST AFTER BUILDING (not fixed by bundling) ---
1. faiss-cpu ships three SWIG extension variants (base/avx2/avx512) and
   picks one at import time based on CPU features (see faiss/loader.py).
   All three are bundled; if `querynest chat --pdf ...` crashes with an
   ImportError/SIGILL on a different machine, this is the first suspect.
2. RESOLVED — verified offline, no extra bundling needed here. tiktoken
   itself would download its BPE vocab from OpenAI's CDN on first use if
   left to its own devices, but querynest never calls tiktoken directly
   (the text splitter uses plain character length, not
   `from_tiktoken_encoder`). The only real caller is litellm, which
   already ships its own fix: litellm/litellm_core_utils/default_encoding.py
   points TIKTOKEN_CACHE_DIR at its own bundled
   litellm/litellm_core_utils/tokenizers/ directory and eagerly loads the
   cl100k_base encoding from it at import time — before tiktoken ever gets
   a chance to reach the network. That data directory is pulled in by the
   collect_data_files("litellm") call below. Verified by running the built
   binary in a --network none container: `querynest --help` (which
   imports the litellm chain, and thus triggers that eager encoding load,
   on every invocation) succeeded with zero network access. If you ever
   add a direct tiktoken call to this codebase, re-verify this — it stops
   being automatic.
3. litellm's provider surface is now trimmed to the 5 providers in the
   curated `config/setup.py` model menu (gemini, openai, anthropic, groq,
   mistral) plus vertex_ai (gemini's calls route through
   litellm/main.py's "vertex_ai_beta"/"gemini" shared code path — verified
   by reading litellm/main.py, not assumed). The menu also offers "enter
   a custom model string" for ANY litellm-supported provider — a custom
   string naming a provider outside this set (e.g. "cohere/command-r")
   will NOT work in this binary; its litellm.llms.<provider> submodule
   isn't bundled. If you want to support arbitrary custom providers, go
   back to collect_all("litellm").
4. grpc/grpc_status (pulled in transitively by google-generativeai) needs
   its bundled root CA file to make TLS calls to Google's API. collect_all
   should grab it, but if you see SSL "unable to get local issuer
   certificate" errors at runtime, that's this.
5. google-generativeai installs itself as a namespace package via a
   `.pth` file (google_generativeai-*-nspkg.pth). PyInstaller's static
   analysis doesn't follow namespace-package tricks, hence the explicit
   hidden-imports for `google.generativeai` / `google.ai.generativelanguage`
   below. If Gemini calls fail with ModuleNotFoundError at runtime, check
   this first.
6. readability-lxml's HTML cleaning depends on lxml_html_clean, which is
   a *separate* PyPI package (lxml.html.clean was split out of lxml).
   It's collected explicitly below — if web loading breaks, check this.
"""

from PyInstaller.utils.hooks import collect_all, collect_data_files, collect_submodules

datas = []
binaries = []
hiddenimports = []

# Packages with native extensions or bundled data files that are either
# small or genuinely need everything collected.
COLLECT_ALL_PACKAGES = [
    "faiss",  # SWIG C-extension, see risk #1 above
    "grpc",  # C-extension used by google-generativeai
    "grpc_status",
    "google.generativeai",  # namespace package, see risk #5
    "google.ai.generativelanguage",
    "tiktoken",  # C-extension (tiktoken._tiktoken)
    "tiktoken_ext",  # plugin package, discovered via entry_points
    "langchain_core",
    "langchain_text_splitters",
    "langchain_google_genai",
    "langchain_litellm",
    "readability",  # readability-lxml
    "lxml_html_clean",  # see risk #6
    "pypdf",
]

for pkg in COLLECT_ALL_PACKAGES:
    pkg_datas, pkg_binaries, pkg_hiddenimports = collect_all(pkg)
    datas += pkg_datas
    binaries += pkg_binaries
    hiddenimports += pkg_hiddenimports

# faiss ships THREE ~36MB SWIG C-extension variants (base/avx2/avx512) and
# picks one at import time (see faiss/loader.py) based on the running
# CPU's feature set — with a graceful fallback chain already built in:
# try avx512 -> except ImportError -> try avx2 -> except ImportError ->
# fall back to the base variant, which only needs baseline x86-64 (SSE2),
# guaranteed present on every x86-64 CPU made this century.
#
# First attempt (kept as a lesson, not repeated): removing these two names
# from `hiddenimports` does NOT work, because that's not the only path
# that finds them. faiss/loader.py's own source has literal
# `from .swigfaiss_avx512 import *` / `from .swigfaiss_avx2 import *`
# statements at module level (inside try/except, but PyInstaller's static
# bytecode scanner doesn't understand try/except — it just sees "this
# module imports these names" and re-adds them during Analysis()
# regardless of what's in our hiddenimports list). Verified this the hard
# way: filtering hiddenimports alone produced an identically-sized binary
# with both .so files still present.
#
# The mechanism that actually overrides every discovery path (hooks,
# static scanning, hiddenimports) is Analysis(excludes=[...]), passed
# below. Once they're excluded there, `from .swigfaiss_avx512 import *`
# raises ModuleNotFoundError (a subclass of ImportError) at runtime, which
# loader.py's existing `except ImportError` already catches and falls
# through from — no extra runtime code needed on our side.
#
# This is a deliberate compatibility-over-speed trade for THIS app: faiss
# builds a brute-force flat index per chat session (FaissStore.build() ->
# FAISS.from_documents()) over one PDF/webpage's chunks — realistically
# hundreds to a few thousand ~768-dim vectors (Gemini's
# text-embedding-004). SIMD gains from AVX2/AVX512 matter at
# millions-of-vectors ANN scale; at this scale the difference versus the
# base variant is sub-millisecond, dwarfed by the network/LLM round trip
# that follows. In exchange we drop AVX512/AVX2 CPU requirements entirely
# and save ~72MB. If you ever move to a much larger corpus per session,
# re-examine this trade — see packaging/README.md for the measured
# before/after and how this was verified.
FAISS_AVX_VARIANTS_TO_DROP = [
    "faiss._swigfaiss_avx2",
    "faiss._swigfaiss_avx512",
    "faiss.swigfaiss_avx2",
    "faiss.swigfaiss_avx512",
]
# Passed to Analysis(excludes=...) below — that's the only place this
# actually takes effect (see comment above).

# litellm: keep its bundled JSON/YAML data (cost map backup etc., used as
# an offline fallback — confirmed working, see packaging/README.md) but
# DON'T collect_all its code — that pulls in every provider litellm knows
# about. Instead hidden-import only the litellm.llms.<provider> submodules
# for the 5 providers in config/setup.py's curated menu. litellm's own
# provider-name -> module dispatch (litellm/main.py) is what would import
# these dynamically at call time; PyInstaller can't see that, so they're
# named explicitly here instead of guessed.
datas += collect_data_files("litellm")
LITELLM_PROVIDER_PACKAGES = [
    "litellm.llms.gemini",
    "litellm.llms.vertex_ai",  # gemini calls share this code path — see litellm/main.py:3415
    "litellm.llms.openai",
    "litellm.llms.anthropic",
    "litellm.llms.groq",
    "litellm.llms.mistral",
]
for pkg in LITELLM_PROVIDER_PACKAGES:
    hiddenimports += collect_submodules(pkg)

# langchain_community: PyInstaller's static analysis sees
# `from langchain_community.document_loaders import DirectoryLoader,
# PyPDFLoader` (loaders/pdf_loader.py) and `from
# langchain_community.vectorstores import FAISS` (vector_store/faiss_store.py)
# fine — those top-level packages get bundled. What it can't see is that
# both packages resolve those names via a lazy `__getattr__` /
# importlib.import_module lookup table rather than a real import
# statement. Read straight out of langchain_community's source
# (document_loaders/__init__.py's _module_lookup dict, same for
# vectorstores/__init__.py), the concrete modules those three names
# resolve to are exactly these three — nothing else in
# langchain_community is reachable from this codebase.
hiddenimports += [
    "langchain_community.document_loaders.directory",  # backs DirectoryLoader
    "langchain_community.document_loaders.pdf",  # backs PyPDFLoader
    "langchain_community.vectorstores.faiss",  # backs FAISS
]

# Extra hidden-imports for things collect_all can miss (entry-point plugins,
# lazily-imported submodules).
hiddenimports += [
    "tiktoken_ext.openai_public",
    "google.ai.generativelanguage_v1beta",
    "pydantic.deprecated.decorator",
]

block_cipher = None

a = Analysis(
    ["src/querynest/cli/main.py"],
    pathex=["src"],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=FAISS_AVX_VARIANTS_TO_DROP,
    noarchive=False,
    cipher=block_cipher,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="querynest",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
)
