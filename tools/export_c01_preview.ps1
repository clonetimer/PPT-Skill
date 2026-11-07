param(
    [string]$RepositoryRoot = (Split-Path -Parent $PSScriptRoot)
)

$ErrorActionPreference = 'Stop'
$pptx = Join-Path $RepositoryRoot 'dist/C01_composite_defense_slide_v74.pptx'
$pdf = Join-Path $RepositoryRoot 'dist/C01_composite_defense_slide_v74_preview.pdf'
$png = Join-Path $RepositoryRoot 'dist/C01_composite_defense_slide_v74_preview.png'
$deckPptx = Join-Path $RepositoryRoot 'dist/DECK01_c01_defense.pptx'
$deckPdf = Join-Path $RepositoryRoot 'dist/DECK01_c01_defense.pdf'
if (-not (Test-Path -LiteralPath $pptx)) { throw "Missing $pptx" }
if (-not (Test-Path -LiteralPath $deckPptx)) { throw "Missing $deckPptx" }

$app = New-Object -ComObject PowerPoint.Application
try {
    $deck = $app.Presentations.Open($pptx, $true, $false, $false)
    try {
        $deck.SaveAs($pdf, 32)
        $deck.Slides.Item(1).Export($png, 'PNG', 1600, 900)
    } finally {
        $deck.Close()
    }
    $benchmark = $app.Presentations.Open($deckPptx, $true, $false, $false)
    try {
        $benchmark.SaveAs($deckPdf, 32)
        for ($page = 1; $page -le $benchmark.Slides.Count; $page++) {
            $slidePng = Join-Path $RepositoryRoot "dist/DECK01_c01_defense_slide_$page.png"
            $benchmark.Slides.Item($page).Export($slidePng, 'PNG', 1600, 900)
        }
    } finally {
        $benchmark.Close()
    }
    Write-Output "Exported C01 PDF/PNG and benchmark deck PDF with PowerPoint $($app.Version)"
} finally {
    $app.Quit()
}
