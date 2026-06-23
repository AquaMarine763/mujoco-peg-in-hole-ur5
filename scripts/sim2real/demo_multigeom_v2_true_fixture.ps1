param(
    [string]$Profile = "hex_hex",
    [int]$Seed = 906500,
    [int]$Episodes = 1,
    [string]$Model = "",
    [string]$Output = "",
    [string]$ResultDir = "results\sim2real_multigeom_v2_true_fixture",
    [switch]$NoPolicyObservationPanel
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

if ([string]::IsNullOrWhiteSpace($Output)) {
    $Output = Join-Path $ResultDir ("demo_{0}_seed{1}.gif" -f $Profile, $Seed)
}
$TraceOutput = [System.IO.Path]::ChangeExtension($Output, ".trace.csv")
$ResolvedModel = Resolve-PolicyModel $Model

$PythonArgs = @(
    "scripts\demo_policy.py",
    "--config", "configs\sim2real\multigeom_v2_true_fixture_demo.yaml",
    "--model", $ResolvedModel,
    "--guarded-policy",
    "--geometry-profile", $Profile,
    "--episodes", [string]$Episodes,
    "--seed", [string]$Seed,
    "--output", $Output,
    "--trajectory-output", $TraceOutput
)
if ($NoPolicyObservationPanel) {
    $PythonArgs += "--no-policy-observation-panel"
}

Write-Host "Rendering sim2real multigeom v2 true-fixture demo: profile=$Profile seed=$Seed episodes=$Episodes output=$Output"
& python @PythonArgs
