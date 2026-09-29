; =====================================================================
; Inno Setup Script for Pravix Image Upscaler
; =====================================================================

#define MyAppName "Pravix Image Upscaler"
#define MyAppVersion "1.3.0"
#define MyAppPublisher "Pravix"
#define MyAppExeName "PravixUpscaler.exe"

[Setup]
AppId={{D548F09A-387E-4E61-9E9C-A8961726715F}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
ArchitecturesInstallIn64BitMode=x64compatible
DefaultDirName={autopf}\Pravix Upscaler
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
OutputDir=dist
OutputBaseFilename=PravixUpscaler_Setup
SetupIconFile=assets\icon.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"
Name: "contextmenu"; Description: "Add 'Upscale with Pravix' to Windows Explorer right-click menu"; GroupDescription: "Windows Explorer Integration:"

[Files]
Source: "dist\PravixUpscaler\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\PravixUpscaler\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Registry]
Root: HKCU; Subkey: "Software\Classes\SystemFileAssociations\image\shell\PravixUpscaler"; ValueType: string; ValueName: ""; ValueData: "Upscale with Pravix"; Tasks: contextmenu; Flags: uninsdeletekey
Root: HKCU; Subkey: "Software\Classes\SystemFileAssociations\image\shell\PravixUpscaler"; ValueType: string; ValueName: "Icon"; ValueData: """{app}\{#MyAppExeName}"",0"; Tasks: contextmenu; Flags: uninsdeletekey
Root: HKCU; Subkey: "Software\Classes\SystemFileAssociations\image\shell\PravixUpscaler\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" ""%1"""; Tasks: contextmenu; Flags: uninsdeletekey

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
