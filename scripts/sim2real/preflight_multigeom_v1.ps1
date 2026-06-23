param(
    [string]$Config = "configs\sim2real\multigeom_v1_real_preflight.yaml",
    [string]$Model = "",
    [string]$ResultDir = "results\sim2real_multigeom_v1",
    [switch]$Strict
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
Set-Location $Root
$env:PYTHONPATH = if ([string]::IsNullOrWhiteSpace($env:PYTHONPATH)) { $Root } else { "$Root;$env:PYTHONPATH" }
New-Item -ItemType Directory -Force -Path $ResultDir | Out-Null

function Resolve-PolicyModel {
    param([string]$Requested)
    if (-not [string]::IsNullOrWhiteSpace($Requested)) {
        return $Requested
    }
    $Relative = "checkpoints\ur5e_full\high_start\hard\correction\sac_image_bc_wrist_pose_control_state_insert_drift_2k_w10_e1.zip"
    if (Test-Path $Relative) {
        return $Relative
    }
    $Sibling = Join-Path (Split-Path -Parent $Root) ("mujoco_peg_in_hole\" + $Relative)
    if (Test-Path $Sibling) {
        return $Sibling
    }
    return $Relative
}

$ResolvedModel = Resolve-PolicyModel $Model

$PythonArgs = @(
    "scripts\check_real_deployment_config.py",
    "--config", $Config,
    "--model", $ResolvedModel,
    "--require-model",
    "--output-md", (Join-Path $ResultDir "real_preflight_check.md"),
    "--output-json", (Join-Path $ResultDir "real_preflight_check.json")
)

if ($Strict) {
    $PythonArgs += @("--require-camera-calibration", "--require-image-crop", "--fail-on-warn")
} else {
    $PythonArgs += "--allow-missing-target-calibration"
}

Write-Host "Checking sim2real multigeom v1 real preflight config: strict=$Strict"
& python @PythonArgs
