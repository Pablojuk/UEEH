; Script de Inno Setup para generar el instalador de Windows del "Sistema Académico UEEH".
;
; Para compilar este script:
; 1. Asegúrese de haber compilado previamente la carpeta portable en dist\UEEH\
; 2. Abra Inno Setup y cargue este archivo setup_config.iss
; 3. Presione F9 o haga clic en "Build -> Compile"
;
; El instalador resultante quedará en la carpeta "output\" en la raíz del repositorio.

#define AppName "Sistema Académico UEEH"
#define AppVersion "4.0.1"
#define AppPublisher "Econ. Pablo Hernan Juca Farfan"
#define AppExeName "UEEH.exe"

[Setup]
; Metadatos de la aplicación
AppId={{E5D9FA11-88D8-4C82-9B7C-A5E8E8A5E81A}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
DefaultDirName={autopf}\UEEH
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes

; Configuración de salida del instalador
OutputDir=output
OutputBaseFilename=Instalador_UEEH_v4.0.1
Compression=lzma
SolidCompression=yes
WizardStyle=modern

; Requerimientos de arquitectura (64 bits recomendado para Windows 10/11 moderno)
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; Archivo ejecutable principal
Source: "dist\UEEH\{#AppExeName}"; DestDir: "{app}"; Flags: ignoreversion
; Carpeta interna y dependencias (DLLs, _internal, plantillas Jinja2, etc.)
Source: "dist\UEEH\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
; Acceso directo en el menú de inicio
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExeName}"
; Acceso directo opcional en el escritorio
Name: "{userdesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; Tasks: desktopicon

[Run]
; Casilla de verificación para ejecutar la aplicación inmediatamente tras finalizar la instalación
Filename: "{app}\{#AppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(AppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
