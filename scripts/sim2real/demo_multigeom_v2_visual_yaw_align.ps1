param(
    [string]$Profile = "hex_hex",
    [int]$Seed = 906500,
    [int]$Episodes = 1,
    [string]$Model = "",
    [string]$Output = "",
    [string]$ResultDir = "results\sim2real_multigeom_v2_visual_yaw_align_demo",
    [switch]$NoPolicyObservationPanel
)

& "$PSScriptRoot\demo_multigeom_v2_true_fixture.ps1" `
    -Profile $Profile `
    -Seed $Seed `
    -Episodes $Episodes `
    -Model $Model `
    -Output $Output `
    -ResultDir $ResultDir `
    -NoPolicyObservationPanel:$NoPolicyObservationPanel
