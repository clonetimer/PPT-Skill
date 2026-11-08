$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$ids = @('TR03_transformer_architecture_source_matched', 'TR04_transformer_attention_source_matched')
$app = New-Object -ComObject PowerPoint.Application
try {
    foreach ($id in $ids) {
        $deck = $app.Presentations.Open((Join-Path $root "$id.pptx"), $true, $false, $false)
        try {
            $deck.SaveAs((Join-Path $root "$id.pdf"), 32)
            if ($id -like 'TR03*') { $width = 1200; $height = 1213 }
            else { $width = 1600; $height = 945 }
            $deck.Slides.Item(1).Export((Join-Path $root "$id.png"), 'PNG', $width, $height)
        } finally { $deck.Close() }
    }
} finally { $app.Quit() }
Write-Output 'Exported two source-matched PDFs and PNG previews'
