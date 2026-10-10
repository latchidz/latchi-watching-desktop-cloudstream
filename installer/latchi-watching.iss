#ifndef MyAppVersion
#define MyAppVersion "1.0.0"
#endif
[Setup]
AppId={{891B65A6-34A2-47B6-9B90-606390EA8FB7}
AppName=LATCHI WATCHING Windows
AppVersion={#MyAppVersion}
AppPublisher=LATCHI
AppPublisherURL=https://github.com/latchidz/latchi-watching-desktop-cloudstream
DefaultDirName={localappdata}\Programs\LATCHI WATCHING Windows
DefaultGroupName=LATCHI WATCHING Windows
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0
OutputDir=Output
OutputBaseFilename=LATCHI-WATCHING-{#MyAppVersion}-Windows-x64-Setup
SetupIconFile=..\assets\appicon.ico
UninstallDisplayIcon={app}\LATCHI-WATCHING.exe
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
CloseApplications=yes
RestartApplications=no
LicenseFile=..\LICENSE
[Files]
Source: "..\publish\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; Flags: unchecked
[Icons]
Name: "{group}\LATCHI WATCHING Windows"; Filename: "{app}\LATCHI-WATCHING.exe"
Name: "{userdesktop}\LATCHI WATCHING Windows"; Filename: "{app}\LATCHI-WATCHING.exe"; Tasks: desktopicon
[Run]
Filename: "{app}\LATCHI-WATCHING.exe"; Description: "Open LATCHI WATCHING"; Flags: nowait postinstall skipifsilent
