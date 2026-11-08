param([Parameter(Mandatory=$true)][string]$Pptx)
$ErrorActionPreference='Stop'
$source=(Resolve-Path -LiteralPath $Pptx).Path
$stem=[System.IO.Path]::Combine([System.IO.Path]::GetDirectoryName($source),[System.IO.Path]::GetFileNameWithoutExtension($source))
$app=New-Object -ComObject PowerPoint.Application
try {
  $deck=$app.Presentations.Open($source,$true,$false,$false)
  try {
    $deck.SaveAs("$stem.pdf",32)
    $w=2400
    $h=[int][Math]::Round($w*$deck.PageSetup.SlideHeight/$deck.PageSetup.SlideWidth)
    $deck.Slides.Item(1).Export("$stem.png",'PNG',$w,$h)
  } finally {$deck.Close()}
} finally {$app.Quit()}
Write-Output "Exported $stem.pdf and .png"
