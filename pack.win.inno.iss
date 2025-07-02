#include "src\fb_version.iss"

[Setup]
AppName=Birdland-Qt
AppVersion={#AppVersionFull}
DefaultDirName={commonpf}\Birdland-Qt
DefaultGroupName=Birdland-Qt
UninstallDisplayIcon={app}\birdland_qt.exe
OutputDir=C:\Users\wrw\Desktop\onedir
OutputBaseFilename="Birdland-Qt_win_installer_{#AppVersionFull}"
Compression=lzma
SolidCompression=yes
PrivilegesRequired=admin
DisableWelcomePage=no
DisableDirPage=no
DisableProgramGroupPage=no
CreateUninstallRegKey=yes
SetupIconFile=src\Icons\Saxophone_128.ico
WizardImageFile=src\Icons\Saxophone_128.bmp

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional icons:"

[Files]
; Install everything from the one-dir bundle located on the user's Desktop
Source: "C:\Users\wrw\Desktop\onedir\birdland_qt\*"; DestDir: "{app}"; Flags: recursesubdirs ignoreversion

; These files will be tracked and removed by the uninstaller

[Icons]
Name: "{group}\Birdland-Qt"; Filename: "{app}\birdland_qt.exe"
Name: "{userdesktop}\Birdland-Qt"; Filename: "{app}\birdland_qt.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\birdland_qt.exe"; Description: "Launch Birdland-Qt now"; Flags: nowait postinstall skipifsilent

