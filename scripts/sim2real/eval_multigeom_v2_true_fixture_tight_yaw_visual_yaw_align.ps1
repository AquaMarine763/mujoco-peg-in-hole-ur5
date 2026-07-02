param(
    [string]$Profile = "square_square",
    [int[]]$Seeds = @(906500),
    [int]$Episodes = 5,
    [string]$Model = "",
    [string]$Config = "",
    [string]$ResultDir = "results\sim2real_multigeom_v2_true_fixture_tight_yaw_visual_yaw_align",
    [switch]$NoTriangleWristProtocol,
    [switch]$NoTriangleProtocolYawOverrides,
    [string[]]$ExtraArgs = @()
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

function Resolve-ProfileConfig {
    param(
        [string]$Requested,
        [string]$ProfileName
    )
    if (-not [string]::IsNullOrWhiteSpace($Requested)) {
        return $Requested
    }
    if ($ProfileName -eq "square_square") {
        return "configs\sim2real\multigeom_v1_eval.yaml"
    }
    if ($ProfileName -eq "triangle_triangle") {
        return "configs\sim2real\multigeom_v2_true_fixture_visual_yaw_align_triangle_wrist_safe_v3_early_approach_v1_eval.yaml"
    }
    if ($ProfileName -eq "hex_hex") {
        return "configs\sim2real\multigeom_v2_true_fixture_visual_yaw_align_triangle_v2_hex_failures_v1_hex_early_approach_descent_v1_eval.yaml"
    }
    if ($ProfileName -eq "rectangular_key") {
        return "configs\sim2real\multigeom_v2_true_fixture_tight_yaw_key_visible_brake_low_z_crop_high_centered_local_hold_stronger_brake_early_approach_post_yaw_reapproach_low_z_verifier_v3_estimator_v2_relaxed_rawnorm_v1_eval.yaml"
    }
    return "configs\sim2real\multigeom_v2_true_fixture_visual_yaw_align_multishape_eval.yaml"
}

function Get-TriangleWristProtocolArgs {
    $Args = @(
        "--guard-visual-yaw-align-absolute-shape-target",
        "--guard-visual-yaw-align-absolute-shape-target-profiles", "triangle_triangle",
        "--guard-visual-yaw-align-absolute-shape-target-max-abs-deg", "160",
        "--guard-visual-yaw-align-absolute-shape-target-max-delta-deg", "95",
        "--guard-visual-yaw-align-absolute-shape-target-max-target-jump-deg", "70",
        "--guard-visual-yaw-align-absolute-shape-target-max-rest-delta-deg", "130",
        "--ik-nearest-wrist-target-equivalent",
        "--ik-max-wrist-target-delta-deg", "8",
        "--initial-shape-yaw-max-wrist-rest-delta-deg", "130",
        "--initial-ik-max-attempts", "80",
        "--guard-visual-yaw-align-absolute-shape-target-descent-unlock",
        "--guard-visual-yaw-align-absolute-shape-target-descent-unlock-profiles", "triangle_triangle",
        "--guard-visual-yaw-align-absolute-shape-target-descent-unlock-stable-steps", "20",
        "--guard-visual-yaw-align-absolute-shape-target-descent-unlock-max-xy", "0.005",
        "--guard-visual-yaw-align-absolute-shape-target-descent-unlock-min-z", "0.010",
        "--guard-visual-yaw-align-absolute-shape-target-descent-unlock-max-z", "0.090",
        "--guard-visual-yaw-align-absolute-shape-target-descent-unlock-max-down-action", "0.003",
        "--guard-visual-yaw-align-absolute-shape-target-descent-unlock-max-xy-action", "0.004",
        "--guard-visual-yaw-align-min-raw-norm", "0.03",
        "--guard-visual-yaw-align-hold-xy-enabled",
        "--guard-visual-yaw-align-hold-xy-profiles", "triangle_triangle",
        "--guard-visual-yaw-align-hold-xy-tolerance", "0.0025",
        "--guard-visual-yaw-align-hold-max-xy-action", "0.006",
        "--guard-visual-yaw-align-hold-target-enabled",
        "--guard-visual-yaw-align-hold-target-profiles", "triangle_triangle",
        "--guard-visual-yaw-align-hold-target-steps", "120",
        "--guard-visual-yaw-align-hold-target-release-xy", "0.18",
        "--guard-visual-yaw-align-hold-target-min-z", "0.0",
        "--guard-visual-yaw-align-hold-target-max-z", "0.16",
        "--guard-visual-yaw-align-hold-target-block-descent",
        "--guard-visual-yaw-align-freeze-aligned-target-enabled",
        "--guard-visual-yaw-align-freeze-aligned-target-profiles", "triangle_triangle",
        "--guard-visual-yaw-align-freeze-aligned-target-steps", "260",
        "--guard-visual-yaw-align-freeze-aligned-target-required-steps", "2",
        "--guard-visual-yaw-align-freeze-aligned-target-source", "target",
        "--guard-visual-yaw-align-freeze-aligned-target-block-until-descent-xy",
        "--guard-visual-yaw-align-freeze-aligned-target-descent-xy", "0.020",
        "--guard-visual-yaw-align-freeze-aligned-target-release-xy", "0.18",
        "--guard-visual-yaw-align-freeze-aligned-target-min-z", "0.0",
        "--guard-visual-yaw-align-freeze-aligned-target-max-z", "0.18",
        "--guard-visual-yaw-align-aligned-descent-max-down-action", "0.003",
        "--guard-visual-yaw-align-aligned-descent-max-xy-action", "0.004"
    )
    if (-not $NoTriangleProtocolYawOverrides) {
        $Args += @(
            "--guard-visual-yaw-align-hold-target-arm-yaw-deg", "65.0",
            "--guard-visual-yaw-align-hold-target-release-yaw-deg", "65.0",
            "--guard-visual-yaw-align-freeze-aligned-target-yaw-deg", "8.0",
            "--guard-visual-yaw-align-freeze-aligned-target-release-yaw-deg", "65.0"
        )
    }
    return $Args
}

$ResolvedModel = Resolve-PolicyModel $Model
$ResolvedConfig = Resolve-ProfileConfig $Config $Profile
$ProtocolArgs = @()
if ($Profile -eq "triangle_triangle" -and -not $NoTriangleWristProtocol) {
    $ProtocolArgs = Get-TriangleWristProtocolArgs
}

foreach ($Seed in $Seeds) {
    $Prefix = Join-Path $ResultDir ("visual_yaw_align_{0}_{1}ep_seed{2}" -f $Profile, $Episodes, $Seed)
    $PythonArgs = @(
        "scripts\eval_guarded_policy.py",
        "--config", $ResolvedConfig,
        "--model", $ResolvedModel,
        "--geometry-profile", $Profile,
        "--episodes", [string]$Episodes,
        "--seed", [string]$Seed,
        "--deterministic-eval",
        "--deterministic-eval-torch-threads", "1",
        "--output-csv", "$Prefix.csv",
        "--output-md", "$Prefix.md",
        "--episode-output-csv", "${Prefix}_episodes.csv",
        "--step-output-csv", "${Prefix}_steps.csv",
        "--step-trace-outcome-filter", "any"
    )
    $PythonArgs += $ProtocolArgs
    $PythonArgs += $ExtraArgs

    Write-Host "Running v2 tight-yaw visual yaw-align eval: profile=$Profile seed=$Seed episodes=$Episodes config=$ResolvedConfig"
    & python @PythonArgs
}
