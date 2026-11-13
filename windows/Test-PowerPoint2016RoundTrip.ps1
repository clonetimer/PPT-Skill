#requires -Version 5.1
<#
.SYNOPSIS
  Perform a native Windows PowerPoint 2016 round-trip and object-count check.
.DESCRIPTION
  Open -> save a new PPTX -> export PDF/PNG -> reopen -> compare object/text
  snapshots. Does not claim that Office 365 is Office 2016 because both may
  report Version 16.0. A human must inspect exported PDF/PNG at final size.
.EXAMPLE
  powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\Test-PowerPoint2016RoundTrip.ps1 -InputDirectory C:\PPT-Figures -OutputDirectory C:\PPT-Figures\office2016_qa
#>
param(
    [Parameter(Mandatory=$true)][string]$InputDirectory,
    [Parameter(Mandatory=$true)][string]$OutputDirectory,
    [switch]$RequireOffice2016
)
$ErrorActionPreference = 'Stop'
$inputRoot = [IO.Path]::GetFullPath($InputDirectory)
$outputRoot = [IO.Path]::GetFullPath($OutputDirectory)
if (!(Test-Path -LiteralPath $inputRoot -PathType Container)) {
    throw "Input directory does not exist: $inputRoot"
}
New-Item -ItemType Directory -Force -Path $outputRoot | Out-Null

function Get-SlideSnapshot($deck) {
    $slides = @()
    foreach ($slide in $deck.Slides) {
        $texts = @()
        $fontNames = @()
        $types = @{}
        foreach ($shape in $slide.Shapes) {
            $kind = [string]$shape.Type
            if ($types.ContainsKey($kind)) { $types[$kind]++ }
            else { $types[$kind] = 1 }
            try {
                if ($shape.HasTextFrame -and $shape.TextFrame.HasText) {
                    $texts += [string]$shape.TextFrame.TextRange.Text
                    $fontNames += [string]$shape.TextFrame.TextRange.Font.Name
                }
            } catch {}
        }
        $slides += [pscustomobject]@{
            slide_number = [int]$slide.SlideIndex
            shape_count = [int]$slide.Shapes.Count
            text_count = [int]$texts.Count
            texts = @($texts | Sort-Object)
            font_families = @($fontNames | Sort-Object -Unique)
            type_counts = $types
        }
    }
    return ,$slides
}

$reports = @()
$app = $null
try {
    $app = New-Object -ComObject PowerPoint.Application
    $app.Visible = -1
    $version = [string]$app.Version
    $product = ''
    try {
        $reg = Get-ItemProperty 'HKLM:\SOFTWARE\Microsoft\Office\ClickToRun\Configuration' -ErrorAction Stop
        $product = [string]$reg.ProductReleaseIds
    } catch {}
    # Version 16.0 alone is not proof of a 2016 installation.
    $isOffice2016 = ($version -match '^16\.') -and ($product -match '2016')
    if ($RequireOffice2016 -and !$isOffice2016) {
        throw "Office 2016 not established (Version=$version; ProductReleaseIds=$product)"
    }
    $inputs = @(Get-ChildItem -LiteralPath $inputRoot -Filter '*.pptx' -File | Sort-Object Name)
    if ($inputs.Count -eq 0) { throw 'No *.pptx inputs found' }
    foreach ($source in $inputs) {
        $deck = $null
        $reopened = $null
        try {
            $pptx = Join-Path $outputRoot ($source.BaseName + '_office_roundtrip.pptx')
            $pdf = Join-Path $outputRoot ($source.BaseName + '_office_roundtrip.pdf')
            $preview = Join-Path $outputRoot ($source.BaseName + '_office_roundtrip.png')
            if ([IO.Path]::GetFullPath($source.FullName) -eq [IO.Path]::GetFullPath($pptx)) {
                throw 'Refusing to overwrite original'
            }
            $deck = $app.Presentations.Open($source.FullName, $false, $false, $false)
            $before = @(Get-SlideSnapshot $deck)
            $deck.SaveAs($pptx, 24) # ppSaveAsOpenXMLPresentation
            $deck.ExportAsFixedFormat($pdf, 2) # ppFixedFormatTypePDF
            if ($deck.Slides.Count -ge 1) {
                $w = 1600
                $h = [int][Math]::Round($w * $deck.PageSetup.SlideHeight / $deck.PageSetup.SlideWidth)
                $deck.Slides.Item(1).Export($preview, 'PNG', $w, $h)
            }
            $deck.Close(); $deck = $null
            $reopened = $app.Presentations.Open($pptx, $true, $false, $false)
            $after = @(Get-SlideSnapshot $reopened)
            $reopened.Close(); $reopened = $null
            $same = ($before.Count -eq $after.Count)
            if ($same) {
                for ($i=0; $i -lt $before.Count; $i++) {
                    if ($before[$i].shape_count -ne $after[$i].shape_count -or
                        $before[$i].text_count -ne $after[$i].text_count -or
                        (Compare-Object -ReferenceObject $before[$i].texts -DifferenceObject $after[$i].texts)) {
                        $same = $false; break
                    }
                }
            }
            $filesPresent = (Test-Path -LiteralPath $pptx) -and
                            (Test-Path -LiteralPath $pdf) -and
                            (Test-Path -LiteralPath $preview)
            $reports += [pscustomobject]@{
                input_file = $source.Name
                input_sha256 = (Get-FileHash -LiteralPath $source.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
                output_pptx = $pptx
                output_pdf = $pdf
                output_png = $preview
                output_sha256 = (Get-FileHash -LiteralPath $pptx -Algorithm SHA256).Hash.ToLowerInvariant()
                office_version = $version
                product_release_ids = $product
                identified_office2016 = $isOffice2016
                roundtrip_structure_same = $same
                all_output_files_exist = $filesPresent
                requires_manual_visual_check = $true
                status = $(if ($same -and $filesPresent) {'STRUCTURE_PASS'} else {'FAIL'})
                before = $before
                after = $after
            }
        } finally {
            if ($reopened) { try { $reopened.Close() } catch {} }
            if ($deck) { try { $deck.Close() } catch {} }
        }
    }
} finally {
    if ($app) {
        try { $app.Quit() } catch {}
        [void][Runtime.InteropServices.Marshal]::FinalReleaseComObject($app)
    }
}
$reportPath = Join-Path $outputRoot 'office2016_roundtrip_report.json'
$reports | ConvertTo-Json -Depth 9 | Set-Content -LiteralPath $reportPath -Encoding UTF8
Write-Host "Report: $reportPath"
if (@($reports | Where-Object {$_.status -ne 'STRUCTURE_PASS'}).Count -gt 0) { exit 1 }
