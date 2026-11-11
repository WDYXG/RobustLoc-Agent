param(
    [string]$Sdk = (Join-Path $PSScriptRoot "../.android-sdk"),
    [string]$Output = (Join-Path $PSScriptRoot "../artifacts/RobustLoc-Field.apk")
)
$ErrorActionPreference = "Stop"
function Invoke-Checked([string]$Program, [string[]]$Arguments) {
    & $Program @Arguments
    if ($LASTEXITCODE -ne 0) { throw "$Program failed with exit code $LASTEXITCODE" }
}
$sdkPath = (Resolve-Path -LiteralPath $Sdk).Path
$platform = @((Join-Path $sdkPath "platforms/android-35/android.jar"),
              (Join-Path $sdkPath "android-35/android.jar")) |
    Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
$toolDir = @((Join-Path $sdkPath "build-tools/35.0.0"), (Join-Path $sdkPath "android-15")) |
    Where-Object { Test-Path -LiteralPath (Join-Path $_ "aapt2.exe") } | Select-Object -First 1
if (!$platform -or !$toolDir) { throw "Install Android API 35 and Build Tools 35.0.0." }
$work = Join-Path $PSScriptRoot ("../.android-build/" + [Guid]::NewGuid().ToString())
$classes = Join-Path $work "classes"
$dex = Join-Path $work "dex"
New-Item -ItemType Directory -Path $classes,$dex -Force | Out-Null
$source = Join-Path $PSScriptRoot "src/org/robustloc/field/MainActivity.java"
$manifest = Join-Path $PSScriptRoot "AndroidManifest.xml"
$bytecode = Join-Path $work "code.jar"
$unsigned = Join-Path $work "unsigned.apk"
$aligned = Join-Path $work "aligned.apk"
$apk = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($Output)
if (Test-Path -LiteralPath $apk) { throw "APK output exists. Choose a new output path." }
New-Item -ItemType Directory -Path (Split-Path -Parent $apk) -Force | Out-Null
Invoke-Checked "javac" @("-encoding","UTF-8","--release","8","-classpath",$platform,"-d",$classes,$source)
Invoke-Checked "jar" @("cf",$bytecode,"-C",$classes,".")
Invoke-Checked (Join-Path $toolDir "d8.bat") @("--lib",$platform,"--min-api","26","--output",$dex,$bytecode)
Invoke-Checked (Join-Path $toolDir "aapt2.exe") @("link","-I",$platform,"--manifest",$manifest,"-o",$unsigned)
Invoke-Checked "jar" @("uf",$unsigned,"-C",$dex,"classes.dex")
Invoke-Checked (Join-Path $toolDir "zipalign.exe") @("-p","4",$unsigned,$aligned)
$key = Join-Path $PSScriptRoot "../.android-build/field-test.keystore"
if (!(Test-Path -LiteralPath $key)) {
    Invoke-Checked "keytool" @("-genkeypair","-storetype","JKS","-keystore",$key,"-storepass","android",
        "-keypass","android","-alias","field-test","-keyalg","RSA","-keysize","2048","-validity","10000",
        "-dname","CN=RobustLoc Field Test")
}
Invoke-Checked (Join-Path $toolDir "apksigner.bat") @("sign","--ks",$key,"--ks-pass","pass:android",
    "--key-pass","pass:android","--out",$apk,$aligned)
Invoke-Checked (Join-Path $toolDir "apksigner.bat") @("verify","--verbose",$apk)
Get-FileHash -Algorithm SHA256 -LiteralPath $apk
