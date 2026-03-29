#include "version.iss"

[Setup]
AppId={{2F25C602-5F70-4D5E-BD1F-5EF0C1118101}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
OutputDir=Output
OutputBaseFilename=FeelIT_Setup_{#AppVersion}
Compression=lzma
SolidCompression=yes
WizardStyle=modern

[Files]
Source: "..\dist\FeelIT\*"; DestDir: "{app}"; Flags: recursesubdirs ignoreversion

[Icons]
Name: "{group}\FeelIT"; Filename: "{app}\{#AppExeName}"
Name: "{group}\Uninstall FeelIT"; Filename: "{uninstallexe}"

[Run]
Filename: "{app}\{#AppExeName}"; Description: "Launch FeelIT"; Flags: nowait postinstall skipifsilent
