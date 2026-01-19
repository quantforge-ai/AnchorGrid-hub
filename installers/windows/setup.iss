; ====================================================================
; QuantGrid Terminal Installer Configuration (Inno Setup)
; ====================================================================
; To build the installer:
; 1. Download and install Inno Setup (free): https://jrsoftware.org/isdl.php
; 2. Open this file in Inno Setup Compiler
; 3. Click "Compile" (or press Ctrl+F9)
; 4. Output: Output\QuantGrid_Setup_v1.0.exe
; ====================================================================

[Setup]
AppName=QuantGrid Terminal
AppVersion=1.0.0
AppPublisher=QuantGrid Team
AppPublisherURL=https://quantgrid.dev
AppSupportURL=https://github.com/quantgrid/quantgrid-core
DefaultDirName={autopf}\QuantGrid
DefaultGroupName=QuantGrid
OutputBaseFilename=QuantGrid_Setup_v1.0
SetupIconFile=assets\grid.ico
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Files]
; The frozen EXE built by PyInstaller
Source: "dist\GridBash.exe"; DestDir: "{app}"; Flags: ignoreversion

; Optional: Include assets
; Source: "assets\*"; DestDir: "{app}\assets"; Flags: ignoreversion recursesubdirs

[Registry]
; 1. Add GridBash.exe to System PATH
; This allows users to type 'gridbash' in any CMD/PowerShell window
Root: HKCU; Subkey: "Environment"; ValueType: expandsz; ValueName: "Path"; ValueData: "{olddata};{app}"; Check: NeedsAddPath('{app}')

; 2. Add "Open Grid Bash Here" to Right-Click Menu
Root: HKCR; Subkey: "Directory\Background\shell\QuantGrid"; ValueType: string; ValueData: "Open Grid Bash Here"; Flags: uninsdeletekey
Root: HKCR; Subkey: "Directory\Background\shell\QuantGrid"; ValueType: string; ValueName: "Icon"; ValueData: "{app}\GridBash.exe,0"
Root: HKCR; Subkey: "Directory\Background\shell\QuantGrid\command"; ValueType: string; ValueData: """{app}\GridBash.exe"""

[Icons]
; Desktop Shortcut
Name: "{userdesktop}\Grid Bash"; Filename: "{app}\GridBash.exe"; IconFilename: "{app}\GridBash.exe"

; Start Menu Entry
Name: "{group}\Grid Bash"; Filename: "{app}\GridBash.exe"
Name: "{group}\Uninstall Grid Bash"; Filename: "{uninstallexe}"

[Run]
; Launch Grid Bash after installation (optional)
Filename: "{app}\GridBash.exe"; Description: "Launch the Grid"; Flags: nowait postinstall skipifsilent

[Code]
// Check if directory is already in PATH
function NeedsAddPath(Param: string): boolean;
var
  OrigPath: string;
begin
  if not RegQueryStringValue(HKEY_CURRENT_USER, 'Environment', 'Path', OrigPath) then
  begin
    Result := True;
    exit;
  end;
  Result := Pos(';' + Param + ';', ';' + OrigPath + ';') = 0;
end;
