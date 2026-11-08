$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$id = 'SC01_spacecraft_bus_mechanism'
$app = New-Object -ComObject PowerPoint.Application
try {
    $deck = $app.Presentations.Open((Join-Path $root "$id.pptx"), $true, $false, $false)
    try {
        $deck.SaveAs((Join-Path $root "$id.pdf"), 32)
        $deck.Slides.Item(1).Export((Join-Path $root "$id.png"), 'PNG', 1920, 1098)
    } finally { $deck.Close() }
} finally { $app.Quit() }
Write-Output 'Exported spacecraft PDF and PNG preview'
