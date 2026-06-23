param(
    [string]$Profile = "square_square",
    [int[]]$Seeds = @(906500),
    [int]$Episodes = 5,
    [string]$Model = "",
    [string]$Config = "configs\sim2real\multigeom_v2_true_fixture_tight_yaw_visual_yaw_align_eval.yaml",
    [string]$ResultDir = "results\sim2real_multigeom_v2_true_fixture_tight_yaw_visual_yaw_align"
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

foreach ($Seed in $Seeds) {
    $Prefix = Join-Path $ResultDir ("visual_yaw_align_{0}_{1}ep_seed{2}" -f $Profile, $Episodes, $Seed)
    $PythonArgs = @(
        "scripts\eval_guarded_policy.py",
        "--config", $Config,
        "--model", $ResolvedModel,
        "--geometry-profile", $Profile,
        "--episodes", [string]$Episodes,
        "--seed", [string]$Seed,
        "--output-csv", "$Prefix.csv",
        "--output-md", "$Prefix.md",
        "--episode-output-csv", "${Prefix}_episodes.csv",
        "--step-output-csv", "${Prefix}_steps.csv",
        "--step-trace-outcome-filter", "any"
    )

    Write-Host "Running v2 tight-yaw visual yaw-align eval: profile=$Profile seed=$Seed episodes=$Episodes"
    & python @PythonArgs
}
