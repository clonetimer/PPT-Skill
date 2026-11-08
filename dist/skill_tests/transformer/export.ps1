$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$pptx = Join-Path $root 'Transformer_original_explained.pptx'
$pdf = Join-Path $root 'Transformer_original_explained.pdf'
$app = New-Object -ComObject PowerPoint.Application
try {
    $deck = $app.Presentations.Open($pptx, $true, $false, $false)
    try {
        $deck.SaveAs($pdf, 32)
        $deck.Slides.Item(1).Export((Join-Path $root 'TR01_transformer_architecture.png'), 'PNG', 1600, 900)
        $deck.Slides.Item(2).Export((Join-Path $root 'TR02_transformer_attention.png'), 'PNG', 1600, 900)
    } finally {
        $deck.Close()
    }
} finally {
    $app.Quit()
}
Write-Output "Exported $pdf and two previews"
