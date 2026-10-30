; ============================================================
;  Redaktor-M — Inno Setup скрипт установщика
; ============================================================

#define AppName "Redaktor-M"
#define AppVersion "1.2.0"
#define AppPublisher "Redaktor-M"
#define AppExeName "Redaktor-M.exe"
#define SourceDir "dist\Redaktor-M"

[Setup]
AppId={{8F1E3A2B-4C5D-6E7F-9A0B-1C2D3E4F5A6B}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
OutputDir=installer
OutputBaseFilename=Redaktor-M-Setup
SetupIconFile=app.ico
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
UninstallDisplayIcon={app}\{#AppExeName}
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Создать ярлык на рабочем столе"; GroupDescription: "Ярлыки:"
Name: "contextmenu"; Description: "Добавить «Открыть в Redaktor-M» в контекстное меню файлов"; GroupDescription: "Интеграция с Windows:"
Name: "assoc_txt";   Description: "Ассоциировать .txt файлы (по умолчанию не включать!)"; GroupDescription: "Ассоциации файлов:"; Flags: unchecked
Name: "assoc_py";    Description: "Ассоциировать .py файлы";  GroupDescription: "Ассоциации файлов:"; Flags: unchecked
Name: "assoc_md";    Description: "Ассоциировать .md файлы";  GroupDescription: "Ассоциации файлов:"; Flags: unchecked
Name: "assoc_log";   Description: "Ассоциировать .log файлы"; GroupDescription: "Ассоциации файлов:"; Flags: unchecked

[Files]
Source: "{#SourceDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExeName}"
Name: "{group}\Удалить {#AppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExeName}"; Description: "Запустить {#AppName}"; Flags: nowait postinstall skipifsilent

; ============================================================
;  РЕЕСТР — контекстное меню и ассоциации
; ============================================================
[Registry]
; --- Контекстное меню «Открыть в Redaktor-M» для ВСЕХ файлов ---
Root: HKCR; Subkey: "*\shell\OpenWithRedaktorM"; ValueType: string; ValueName: ""; ValueData: "Открыть в Redaktor-M"; Tasks: contextmenu; Flags: uninsdeletekey
Root: HKCR; Subkey: "*\shell\OpenWithRedaktorM"; ValueType: string; ValueName: "Icon"; ValueData: "{app}\{#AppExeName},0"; Tasks: contextmenu
Root: HKCR; Subkey: "*\shell\OpenWithRedaktorM\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#AppExeName}"" ""%1"""; Tasks: contextmenu

; --- Ассоциация .txt ---
Root: HKCR; Subkey: ".txt\OpenWithProgids"; ValueType: string; ValueName: "RedaktorM.txt"; ValueData: ""; Tasks: assoc_txt; Flags: uninsdeletevalue
Root: HKCR; Subkey: "RedaktorM.txt"; ValueType: string; ValueName: ""; ValueData: "Текстовый документ Redaktor-M"; Tasks: assoc_txt; Flags: uninsdeletekey
Root: HKCR; Subkey: "RedaktorM.txt\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: "{app}\{#AppExeName},0"; Tasks: assoc_txt
Root: HKCR; Subkey: "RedaktorM.txt\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#AppExeName}"" ""%1"""; Tasks: assoc_txt

; --- Ассоциация .py ---
Root: HKCR; Subkey: ".py\OpenWithProgids"; ValueType: string; ValueName: "RedaktorM.py"; ValueData: ""; Tasks: assoc_py; Flags: uninsdeletevalue
Root: HKCR; Subkey: "RedaktorM.py"; ValueType: string; ValueName: ""; ValueData: "Python файл Redaktor-M"; Tasks: assoc_py; Flags: uninsdeletekey
Root: HKCR; Subkey: "RedaktorM.py\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: "{app}\{#AppExeName},0"; Tasks: assoc_py
Root: HKCR; Subkey: "RedaktorM.py\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#AppExeName}"" ""%1"""; Tasks: assoc_py

; --- Ассоциация .md ---
Root: HKCR; Subkey: ".md\OpenWithProgids"; ValueType: string; ValueName: "RedaktorM.md"; ValueData: ""; Tasks: assoc_md; Flags: uninsdeletevalue
Root: HKCR; Subkey: "RedaktorM.md"; ValueType: string; ValueName: ""; ValueData: "Markdown документ Redaktor-M"; Tasks: assoc_md; Flags: uninsdeletekey
Root: HKCR; Subkey: "RedaktorM.md\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: "{app}\{#AppExeName},0"; Tasks: assoc_md
Root: HKCR; Subkey: "RedaktorM.md\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#AppExeName}"" ""%1"""; Tasks: assoc_md

; --- Ассоциация .log ---
Root: HKCR; Subkey: ".log\OpenWithProgids"; ValueType: string; ValueName: "RedaktorM.log"; ValueData: ""; Tasks: assoc_log; Flags: uninsdeletevalue
Root: HKCR; Subkey: "RedaktorM.log"; ValueType: string; ValueName: ""; ValueData: "Лог-файл Redaktor-M"; Tasks: assoc_log; Flags: uninsdeletekey
Root: HKCR; Subkey: "RedaktorM.log\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: "{app}\{#AppExeName},0"; Tasks: assoc_log
Root: HKCR; Subkey: "RedaktorM.log\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#AppExeName}"" ""%1"""; Tasks: assoc_log

; ============================================================
;  Чистка при удалении
; ============================================================
[UninstallDelete]
Type: filesandordirs; Name: "{app}"

[Code]
// Уведомляем Проводник об изменениях ассоциаций БЕЗ убийства рабочего стола
procedure RefreshExplorer();
var
  ResultCode: Integer;
begin
  // Используем более мягкий метод: SHChangeNotify через Rundll32
  // Это заставляет Проводник перечитать ассоциации, не убивая процесс
  Exec('rundll32.exe', 'shell32.dll,SHChangeNotify', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    if WizardIsTaskSelected('contextmenu') or
       WizardIsTaskSelected('assoc_txt') or
       WizardIsTaskSelected('assoc_py') or
       WizardIsTaskSelected('assoc_md') or
       WizardIsTaskSelected('assoc_log') then
      RefreshExplorer();
  end;
end;