$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$id = 'TK01_treekg_technical_route'
$app = New-Object -ComObject PowerPoint.Application
try {
    $deck = $app.Presentations.Open((Join-Path $root "$id.pptx"), $true, $false, $false)
    try {
        $deck.SaveAs((Join-Path $root "$id.pdf"), 32)
        $deck.Slides.Item(1).Export((Join-Path $root "$id.png"), 'PNG', 2400, 1350)
    } finally { $deck.Close() }
} finally { $app.Quit() }
Write-Output 'Exported Tree-KG PDF and PNG preview'
