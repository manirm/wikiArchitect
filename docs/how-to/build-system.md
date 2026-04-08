# Building WikiArchitect for Distribution

WikiArchitect is powered by **Nuitka**, a high-performance Python compiler. Use this guide to generate standalone binaries for your team.

---

## 🛠️ Build Requirements
- **Python**: 3.12+
- **Nuitka**: Installed via `uv pip install nuitka` or `pip install nuitka`.
- **C Compiler**: `gcc` (Linux), `msvc` (Windows), or `clang` (macOS).

## 🚀 Running the Build
Execute the orchestrated build script from the project root:
```bash
python scripts/build.py
```

### 🧬 What the Build Does
1.  **Compiles**: Converts all `.py` files into a single machine-code binary.
2.  **Bundles**: Includes the `sqlite-vss` vector extension and your `vault/schema` assets.
3.  **Packages**:
    - **Windows**: Generates a professional `.exe` and an NSIS installer.
    - **macOS**: Creates an `.app` bundle and a DMG.
    - **Ubuntu**: Produces a standalone AppImage or a Zip.

---
**Troubleshooting:** See the [GitHub CI release workflow](../../.github/workflows/release.yml) for the exact build commands used for official releases.
