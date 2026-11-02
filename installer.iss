; Inno Setup script - builds YouTube-to-MP4-Setup.exe from the PyInstaller output.
[Setup]
AppName=YouTube to MP4
AppVersion=1.0.0
AppId={{6F2B3C1E-8A4D-4E57-9B0A-2D7C5E1F9A31}
DefaultDirName={autopf}\YouTube to MP4
DefaultGroupName=YouTube to MP4
OutputDir=dist
OutputBaseFilename=YouTube-to-MP4-Setup
Compression=lzma2
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequired=lowest
UninstallDisplayIcon={app}\YouTube to MP4.exe

[Files]
Source: "dist\YouTube to MP4\*"; DestDir: "{app}"; Flags: recursesubdirs ignoreversion

[Icons]
Name: "{group}\YouTube to MP4"; Filename: "{app}\YouTube to MP4.exe"
Name: "{autodesktop}\YouTube to MP4"; Filename: "{app}\YouTube to MP4.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; Flags: unchecked

[Run]
Filename: "{app}\YouTube to MP4.exe"; Description: "Launch YouTube to MP4"; Flags: nowait postinstall skipifsilent
