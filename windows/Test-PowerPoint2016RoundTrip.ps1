#requires -Version 5.1
<#
.SYNOPSIS
  Run a real Windows PowerPoint open/save/export/reopen structural round trip.
.DESCRIPTION
  This script must run on the target Windows machine with desktop PowerPoint.
  It never overwrites an input. Version 16.0 alone does not distinguish Office
  2016 from Microsoft 365. Use -ConfirmOffice2016Installation only after
  checking File > Account/About PowerPoint on the target host.
#>
param(
    [Parameter(Mandatory=$true)][string]$InputDirectory,
    [Parameter(Mandatory=$true)][string]$OutputDirectory,
    [switch]$RequireOffice2016,
    [switch]$ConfirmOffice2016Installation
)
$ErrorActionPreference = 'Stop'
$inputRoot = [IO.Path]::GetFullPath($InputDirectory)
$outputRoot = [IO.Path]::GetFullPath($OutputDirectory)
if (!(Test-Path -LiteralPath $inputRoot -PathType Container)) {
    throw "Input directory does not exist: $inputRoot"
}
New-Item -ItemType Directory -Force -Path $outputRoot | Out-Null

function Get-Office2016Evidence {
    param($PowerPointApp, [bool]$ManualConfirmation)
    $version = [string]$PowerPointApp.Version
    $productReleaseIds = ''
    $displayNames = @()
    try {
        $c2r = Get-ItemProperty 'HKLM:\SOFTWARE\Microsoft\Office\ClickToRun\Configuration' -ErrorAction Stop
        $productReleaseIds = [string]$c2r.ProductReleaseIds
    } catch {}
    foreach ($key in @(
        'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\*',
        'HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*'
    )) {
        try {
            $displayNames += @(Get-ItemProperty $key -ErrorAction SilentlyContinue |
                Where-Object { $_.DisplayName -match 'Microsoft Office|Microsoft 365|Office 20\d\d' } |
                ForEach-Object { [string]$_.DisplayName })
        } catch {}
    }
    $displayNames = @($displayNames | Sort-Object -Unique)
    $matching2016 = @($displayNames | Where-Object {
        $_ -match '(?i)(Microsoft\s+)?Office.*2016|2016.*Office'
    })
    $releaseId2016 = $productReleaseIds -match '(?i)Office2016'
    $manual = $ManualConfirmation -and ($version -match '^16\.')
    $identified = ($version -match '^16\.') -and (
        $matching2016.Count -gt 0 -or $releaseId2016 -or $manual
    )
    $method = if ($matching2016.Count -gt 0) { 'Windows uninstall DisplayName' }
              elseif ($releaseId2016) { 'ClickToRun ProductReleaseIds' }
              elseif ($manual) { 'user-confirmed File > Account/About PowerPoint' }
              else { 'unconfirmed; version 16.0 is not sufficient' }
    return [pscustomobject]@{
        version = $version
        product_release_ids = $productReleaseIds
        office_display_names = $displayNames
        office2016_display_name_matches = $matching2016
        identified_office2016 = [bool]$identified
        identity_method = $method
    }
}

function Get-SlideSnapshot {
    param($Deck)
    $slides = @()
    foreach ($slide in $Deck.Slides) {
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
            slide_width_points = [double]$Deck.PageSetup.SlideWidth
            slide_height_points = [double]$Deck.PageSetup.SlideHeight
        }
    }
    return ,$slides
}

function Test-SequenceEqual($Left, $Right) {
    return (@(Compare-Object -ReferenceObject @($Left) -DifferenceObject @($Right)).Count -eq 0)
}

$reports = @()
$app = $null
try {
    $app = New-Object -ComObject PowerPoint.Application
    $app.Visible = -1
    $office = Get-Office2016Evidence -PowerPointApp $app -ManualConfirmation:$ConfirmOffice2016Installation.IsPresent
    if ($RequireOffice2016 -and !$office.identified_office2016) {
        throw "Office 2016 not established. Version=$($office.version); ProductReleaseIds=$($office.product_release_ids). Check File > Account/About PowerPoint, then rerun with -ConfirmOffice2016Installation."
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
            foreach ($existing in @($pptx,$pdf,$preview)) {
                if (Test-Path -LiteralPath $existing) { Remove-Item -LiteralPath $existing -Force }
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
            $differences = @()
            if ($same) {
                for ($i=0; $i -lt $before.Count; $i++) {
                    $b = $before[$i]; $a = $after[$i]
                    if ($b.shape_count -ne $a.shape_count) { $differences += "slide $($i+1): shape count" }
                    if ($b.text_count -ne $a.text_count) { $differences += "slide $($i+1): text count" }
                    if (!(Test-SequenceEqual $b.texts $a.texts)) { $differences += "slide $($i+1): text content" }
                    if (!(Test-SequenceEqual $b.font_families $a.font_families)) { $differences += "slide $($i+1): font families" }
                    if (($b.type_counts | ConvertTo-Json -Compress) -ne ($a.type_counts | ConvertTo-Json -Compress)) {
                        $differences += "slide $($i+1): shape-type counts"
                    }
                    if ($b.slide_width_points -ne $a.slide_width_points -or
                        $b.slide_height_points -ne $a.slide_height_points) {
                        $differences += "slide $($i+1): slide dimensions"
                    }
                }
            } else { $differences += 'slide count' }
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
                office = $office
                roundtrip_structure_same = [bool]($same -and $differences.Count -eq 0)
                roundtrip_differences = $differences
                all_output_files_exist = $filesPresent
                requires_manual_visual_check = $true
                status = $(if ($same -and $differences.Count -eq 0 -and $filesPresent) {'STRUCTURE_PASS'} else {'FAIL'})
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
$reports | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $reportPath -Encoding UTF8
Write-Host "Report: $reportPath"
if (@($reports | Where-Object {$_.status -ne 'STRUCTURE_PASS'}).Count -gt 0) { exit 1 }
