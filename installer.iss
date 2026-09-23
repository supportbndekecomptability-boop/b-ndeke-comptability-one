; ============================================================
;  B-NDEKE Comptability One - Script d'installation Inno Setup
; ============================================================

#define MyAppName "B-NDEKE Comptability One"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "B-NDEKE"
#define MyAppURL "https://bndeke.com"
#define MyAppExeName "B-NDEKE Comptability One.exe"

[Setup]
AppId={{BNDEKE-COMPTABILITY-ONE-2025-A1B2C3D4}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}

DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes

OutputDir=installer_output
OutputBaseFilename=B-NDEKE-Comptability-One-Setup-{#MyAppVersion}

Compression=lzma2/max
SolidCompression=yes

SetupIconFile=data\bndeke.ico

WizardStyle=modern
DisableProgramGroupPage=yes

PrivilegesRequired=admin
PrivilegesRequiredOverridesAllowed=dialog

ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

MinVersion=10.0

[Languages]
Name: "french"; MessagesFile: "compiler:Languages\French.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: checkedonce

[Files]
Source: "dist\B-NDEKE Comptability One\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\Desinstaller {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}\data\exports"
Type: filesandordirs; Name: "{app}\data\backups"