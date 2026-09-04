# -*- mode: python ; coding: utf-8 -*-


args = []

EXECUTABLES = ["main.py", "webserver_main.py"]

for exec in EXECUTABLES:
    a = Analysis(
        [exec],
        pathex=["."],
        binaries=[],
        datas=[
            ("resources", "resources"),
            ("src/ui/stylesheets/app_stylesheet.scss", "src/ui/stylesheets")
        ],
        hiddenimports=[],
        hookspath=[],
        hooksconfig={},
        runtime_hooks=[],
        excludes=[],
        noarchive=False,
        optimize=2,
    )
    pyz = PYZ(a.pure)

    exe = EXE(
        pyz,
        a.scripts,
        [],
        exclude_binaries=True,
        name=exec.rstrip(".py"),
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        console=True,
        disable_windowed_traceback=False,
        argv_emulation=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
    )

    args.extend([exe, a.binaries, a.datas])

coll = COLLECT(
    *args,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='main',
)
