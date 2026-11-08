$FigureId = if ($args.Count -gt 0) { $args[0] } else { 'GR01_graphrag_flow' }
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$pptx = Join-Path $root "$FigureId.pptx"
$pdf = Join-Path $root "$FigureId.pdf"
$png = Join-Path $root "$FigureId.png"
$app = New-Object -ComObject PowerPoint.Application
try {
    $deck = $app.Presentations.Open($pptx, $true, $false, $false)
    try {
        $deck.SaveAs($pdf, 32)
        $deck.Slides.Item(1).Export($png, 'PNG', 1600, 900)
    } finally {
        $deck.Close()
    }
} finally {
    $app.Quit()
}
Write-Output "Exported $pdf and $png"
