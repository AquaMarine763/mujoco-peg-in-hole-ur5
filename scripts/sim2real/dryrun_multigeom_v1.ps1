param(
    [string]$Config = "configs\sim2real\multigeom_v1_real_dryrun.yaml",
    [string]$Model = "",
    [int]$Seed = 130000,
    [int]$Episodes = 1,
    [int]$MaxSteps = 4,
    [string]$ResultDir = "results\sim2real_multigeom_v1",
    [switch]$ZeroPolicy
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

$Output = Join-Path $ResultDir ("real_dryrun_seed{0}.csv" -f $Seed)
$ResolvedModel = Resolve-PolicyModel $Model
$PythonArgs = @(
    "scripts\run_real_policy_dryrun.py",
    "--config", $Config,
    "--agent", "sac",
    "--device", "cpu",
    "--episodes", [string]$Episodes,
    "--seed", [string]$Seed,
    "--max-steps", [string]$MaxSteps,
    "--output", $Output,
    "--guarded-policy",
    "--guard-scenario-filter", "geometry",
    "--guard-scenario-level", "full_light_geometry",
    "--guard-blend", "0.75"
)

if ($ZeroPolicy) {
    $PythonArgs += "--zero-policy"
} else {
    $PythonArgs += @("--model", $ResolvedModel)
}

Write-Host "Running sim2real multigeom v1 real-interface dry-run: seed=$Seed max_steps=$MaxSteps zero_policy=$ZeroPolicy"
& python @PythonArgs
