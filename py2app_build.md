# Troubleshooting py2app Build for Bilibili Downloader

This document summarizes the issues encountered and solutions applied while trying to build a macOS application bundle for the Bilibili Downloader using `py2app`.

## 1. Initial `OSError` Related to Carbon Framework

*   **Problem**: After the initial build with `python3 setup.py py2app`, launching the app from the terminal (`./dist/Bilibili Downloader.app/Contents/MacOS/Bilibili Downloader`) resulted in an `OSError: dlopen(/System/Library/Carbon.framework/Carbon, 0x0006): tried: '/System/Library/Carbon.framework/Carbon' (no such file), '/System/Library/Frameworks/Carbon.framework/Versions/A/Carbon' (no such file)`.
*   **Attempts**:
    *   Upgrading `py2app` and `PyQt5`.
    *   Setting `MACOSX_DEPLOYMENT_TARGET=10.15` during the build.
*   **Solution**: The issue was resolved by disabling `argv_emulation` in the `py2app` options in `setup.py`.
    ```python
    # setup.py
    OPTIONS = {
        'argv_emulation': False,
        # ... other options
    }
    ```

## 2. `ModuleNotFoundError: No module named 'bilibili_downloader'`

*   **Problem**: After fixing the Carbon issue, the app failed to launch with `ModuleNotFoundError: No module named 'bilibili_downloader'`. This occurred because the main application script (`src/main_app.py`) and the downloader logic (`src/bilibili_downloader.py`) are both within the `src` directory.
*   **Attempts**:
    *   Changing the import in `src/main_app.py` to a relative import: `from .bilibili_downloader import BilibiliDownloader`. This led to `py2app` reporting "Modules with invalid relative imports" because `py2app` treats the main script as a top-level module.
    *   Reverting to `from bilibili_downloader import BilibiliDownloader` (still resulted in `ModuleNotFoundError` at runtime).
*   **Solution**: The problem was solved by:
    1.  Ensuring the `src` directory was listed in the `packages` option in `setup.py`:
        ```python
        # setup.py
        OPTIONS = {
            'packages': ['requests', 'tqdm', 'PyQt5', 'src'],
            # ... other options
        }
        ```
    2.  Changing the import in `src/main_app.py` to treat `src` as a package:
        ```python
        # src/main_app.py
        from src.bilibili_downloader import BilibiliDownloader, extract_bvid
        ```

## 3. `ImportError: No module named 'charset-normalizer'` (Build Time)

*   **Problem**: The `py2app` build process itself started failing with `ImportError: No module named 'charset-normalizer'`, even though it was listed in `OPTIONS['packages']` in `setup.py` and installed in the virtual environment.
*   **Attempts**:
    *   Adding a dummy import `import charset_normalizer` at the top of `src/main_app.py`.
*   **Solution**: The issue was that `pip install charset-normalizer` installs a package whose importable name is `charset_normalizer` (with an underscore). The `packages` list in `setup.py` must use the importable name.
    ```python
    # setup.py
    OPTIONS = {
        'packages': ['requests', 'tqdm', 'PyQt5', 'src', 'charset_normalizer'], # Changed hyphen to underscore
        # ... other options
    }
    ```
    The dummy import in `src/main_app.py` was later confirmed to be unnecessary after this fix.

## 4. Icon File Error (Build Time)

*   **Problem**: A build error `error: icon file must exist: 'src/bilibili_downloader.icns'` occurred.
*   **Solution**: This was due to an incorrect path or missing icon file specified in `setup.py`'s `iconfile` option. The immediate fix was to comment out the `'iconfile'` line.
    ```python
    # setup.py
    OPTIONS = {
        # 'iconfile': 'src/bilibili_downloader.icns', # Commented out or path corrected
        # ... other options
    }
    ```
    To re-enable, ensure the icon file exists at the specified path relative to `setup.py`.

## 5. Runtime `ImportError` Dialog for `BilibiliDownloader`

*   **Problem**: Even after the app seemed to launch, a `QMessageBox` would pop up with "Failed to import BilibiliDownloader. Ensure bilibili_downloader.py is in the same directory as main_app.py or in the Python path."
*   **Cause**: This was traced to a redundant `try-except` block within the `main()` function of `src/main_app.py`. This block attempted to manipulate `sys.path` and perform a direct `from bilibili_downloader import ...`, which was unnecessary and incorrect for the bundled app structure where `src` is treated as a package. The top-level import `from src.bilibili_downloader import ...` was already succeeding.
*   **Solution**: Removed the entire `sys.path` manipulation and the subsequent `try-except ImportError` block from the `main()` function in `src/main_app.py`.

By addressing these issues sequentially, the application was successfully built and launched.
