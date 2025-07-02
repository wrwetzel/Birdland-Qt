:: # --------------------------------------------------------------------------------------------------
:: #   WRW 3-Apr-2025 - too much to remember, encpsulte in shell script

set start=%time%
pushd src
pyside6-rcc bl_resources.qrc -o bl_resources_rc.py
popd

pyinstaller pyi.win.onefile.spec ^
        --clean ^
        --distpath %USERPROFILE%\Desktop\onefile ^
        --workpath %USERPROFILE%\Desktop\onefile\Build

set end=%time%
echo Start: %start%
echo End: %end%

:: # --------------------------------------------------------------------------------------------------
