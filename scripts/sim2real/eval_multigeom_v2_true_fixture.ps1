param(
    [string]$Profile = "hex_hex",
    [int[]]$Seeds = @(906500),
    [int]$Episodes = 1,
    [string]$Model = "",
    [string]$ResultDir = "results\sim2real_multigeom_v2_true_fixture"
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
    $Prefix = Join-Path $ResultDir ("eval_{0}_{1}ep_seed{2}" -f $Profile, $Episodes, $Seed)
    $PythonArgs = @(
        "scripts\eval_guarded_policy.py",
        "--config", "configs\sim2real\multigeom_v2_true_fixture_eval.yaml",
        "--model", $ResolvedModel,
        "--geometry-profile", $Profile,
        "--episodes", [string]$Episodes,
        "--seed", [string]$Seed,
        "--output-csv", "$Prefix.csv",
        "--output-md", "$Prefix.md",
        "--episode-output-csv", "${Prefix}_episodes.csv",
        "--step-output-csv", "${Prefix}_failure_steps.csv"
    )

    Write-Host "Running sim2real multigeom v2 true-fixture eval: profile=$Profile seed=$Seed episodes=$Episodes"
    & python @PythonArgs
}
