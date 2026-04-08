!define APPNAME "WikiArchitect"
!define DESCRIPTION "Intelligent Knowledge Vault"
!define VERSION "0.2.0"

InstallDir "$PROGRAMFILES\${APPNAME}"
Name "${APPNAME}"
OutFile "WikiArchitect-Installer-v${VERSION}.exe"

Section "Install"
    SetOutPath $INSTDIR
    # Nuitka dist output is usually in dist/main.dist
    File /r "dist\main.dist\*"
    
    WriteUninstaller "$INSTDIR\uninstall.exe"
    
    CreateDirectory "$SMPROGRAMS\${APPNAME}"
    CreateShortCut "$SMPROGRAMS\${APPNAME}\${APPNAME}.lnk" "$INSTDIR\main.exe"
    CreateShortCut "$DESKTOP\${APPNAME}.lnk" "$INSTDIR\main.exe"
SectionEnd

Section "Uninstall"
    Delete "$DESKTOP\${APPNAME}.lnk"
    Delete "$SMPROGRAMS\${APPNAME}\${APPNAME}.lnk"
    RMDir /r "$SMPROGRAMS\${APPNAME}"
    RMDir /r "$INSTDIR"
SectionEnd
