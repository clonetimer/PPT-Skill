param(
    [string]$RepositoryRoot = (Split-Path -Parent $PSScriptRoot)
)

$ErrorActionPreference = 'Stop'
$ids = @('Q01_iris_scatter', 'Q02_iris_strip', 'Q03_iris_mean_ci', 'Q03_iris_mean_ci_nature', 'Q04_iris_confusion', 'Q05_iris_ablation', 'Q06_iris_trend_interval', 'Q07_wine_scatter', 'I01_cell_image_quant')
$dist = Join-Path $RepositoryRoot 'dist'
$app = New-Object -ComObject PowerPoint.Application
try {
    $powerPointVersion = $app.Version
    foreach ($id in $ids) {
        $pptx = Join-Path $dist "$id.pptx"
        $pdf = Join-Path $dist "$id.pdf"
        $png = Join-Path $dist "$id.preview.png"
        if (-not (Test-Path -LiteralPath $pptx)) { throw "Missing $pptx" }
        $deck = $app.Presentations.Open($pptx, $true, $false, $false)
        try {
            $deck.SaveAs($pdf, 32)
            if ($id -eq 'Q03_iris_mean_ci_nature') {
                $deck.Slides.Item(1).Export($png, 'PNG', 1830, 1000)
            } else {
                $deck.Slides.Item(1).Export($png, 'PNG', 1600, 900)
            }
            Write-Output "Exported $id"
        }
        finally {
            $deck.Close()
        }
    }
    $metadata = [ordered]@{
        exporter = 'Microsoft PowerPoint'
        version = $powerPointVersion
        export_method = 'Presentation.SaveAs PDF (32); Slide.Export PNG'
        figure_ids = $ids
    }
    $metadata | ConvertTo-Json -Depth 3 | Set-Content -LiteralPath (Join-Path $dist 'export_quantitative_metadata_v76.json') -Encoding utf8
}
finally {
    $app.Quit()
}
