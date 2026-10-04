; Inno Setup script for the standalone DeepPlant Editor (Issue #85).
;
; This produces the Windows user artifact: a normal installer with a wizard,
; Start Menu entry and a working uninstaller.
;
; The Inno Setup compiler (ISCC.exe) is a build-time tool and is not distributed
; with DeepPlant. The setup executable this script produces does contain Inno
; Setup installer/runtime components, so the applicable Inno Setup terms
; (including retaining its copyright notices and web site addresses) apply to the
; generated installer.
;
; The packaging driver passes AppVersion, SourceDir, OutputDir,
; OutputBaseFilename and LicenseFile as /D defines, so this script contains no
; second copy of the application version.

#ifndef AppVersion
  #define AppVersion "0.0.0"
#endif
#ifndef SourceDir
  #error SourceDir must point at the frozen DeepPlant Editor application
#endif
#ifndef OutputDir
  #define OutputDir "."
#endif
#ifndef OutputBaseFilename
  #define OutputBaseFilename "deepplant-editor-setup"
#endif
#ifndef LicenseFile
  ; The packaging driver always passes an absolute path to the project LICENSE.
  #define LicenseFile "..\..\LICENSE"
#endif

[Setup]
; A stable application identity so upgrades/uninstalls are recognized as the
; same product. Do not change it for a release.
AppId={{6D1F4C2A-2F5B-4E1D-9C3A-7B8E5A9D4F21}
AppName=DeepPlant Editor
AppVersion={#AppVersion}
AppPublisher=DeepPlant contributors
AppPublisherURL=https://github.com/Semtexcz/DeepPlant
AppSupportURL=https://github.com/Semtexcz/DeepPlant/issues
DefaultDirName={autopf}\DeepPlant Editor
DefaultGroupName=DeepPlant
DisableProgramGroupPage=yes
; The editor is a per-user local application; no administrator rights are
; required to install or run it.
PrivilegesRequired=lowest
ArchitecturesAllowed=x64
OutputDir={#OutputDir}
OutputBaseFilename={#OutputBaseFilename}
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
UninstallDisplayName=DeepPlant Editor
LicenseFile={#LicenseFile}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Files]
; The frozen application is entirely self-contained: the interpreter, the
; Python dependencies, the DeepPlant package, the canonical symbols and the
; built SPA are all inside SourceDir.
Source: "{#SourceDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\DeepPlant Editor"; Filename: "{app}\deepplant-editor.exe"
Name: "{autodesktop}\DeepPlant Editor"; Filename: "{app}\deepplant-editor.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Shortcuts:"
