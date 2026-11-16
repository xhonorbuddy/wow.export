$ErrorActionPreference='Stop'
$vswhere="${env:ProgramFiles(x86)}\Microsoft Visual Studio\Installer\vswhere.exe"
$installation=& $vswhere -latest -products * -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath
if (!$installation) { throw 'Visual Studio C++ tools are required to build the optional native parser.' }
$version=& $vswhere -latest -products * -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationVersion
$toolset=if ([int]($version.Split('.')[0]) -ge 18) {'v145'} else {'v143'}
& "$installation\MSBuild\Current\Bin\MSBuild.exe" "$PSScriptRoot\geometry.vcxproj" /p:Configuration=Release /p:Platform=x64 "/p:PlatformToolset=$toolset" /v:minimal /nologo
if ($LASTEXITCODE) { throw 'Close Blender if it has loaded native_geometry.dll, then retry the build.' }
