; installer/installer.nsh
!macro customUnInstall
  ${ifNot} ${isUpdated}
    RMDir /r "$LOCALAPPDATA\Antigravity"
  ${endIf}
!macroend
