param(
    [string]$Profile = "square_square",
    [int[]]$Seeds = @(906500),
    [int]$Episodes = 5,
    [string]$Model = "",
    [string]$Config = "configs\sim2real\multigeom_v2_true_fixture_tight_yaw_visual_yaw_align_eval.yaml",
    [string]$ResultDir = "results\sim2real_multigeom_v2_visual_yaw_align"
)

& "$PSScriptRoot\eval_multigeom_v2_true_fixture_tight_yaw_visual_yaw_align.ps1" `
    -Profile $Profile `
    -Seeds $Seeds `
    -Episodes $Episodes `
    -Model $Model `
    -Config $Config `
    -ResultDir $ResultDir
