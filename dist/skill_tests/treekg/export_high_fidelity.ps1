$ErrorActionPreference='Stop'
$root=Split-Path -Parent $MyInvocation.MyCommand.Path
$id='TK02_treekg_source_composition'
$app=New-Object -ComObject PowerPoint.Application
try {
  $deck=$app.Presentations.Open((Join-Path $root "$id.pptx"),$true,$false,$false)
  try {
    $deck.SaveAs((Join-Path $root "$id.pdf"),32)
    $deck.Slides.Item(1).Export((Join-Path $root "$id.png"),'PNG',2560,1640)
  } finally {$deck.Close()}
} finally {$app.Quit()}
Write-Output 'Exported high-fidelity Tree-KG PDF and PNG'
