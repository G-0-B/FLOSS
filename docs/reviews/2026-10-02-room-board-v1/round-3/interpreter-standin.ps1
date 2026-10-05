$a=@($args)
$op=if($a -contains '--check-identity'){'CHECK'}elseif($a -contains '--reclaim-claim'){'RECLAIM'}elseif($a -contains '--reserve-slot'){'RESERVE'}elseif($a -contains '--record-identity'){'RECORD'}else{'UNEXPECTED'}
[IO.File]::AppendAllText($env:REVIEW_TRACE,($op+' '+($a -join ' ')+"`n"))
switch($op){
 'CHECK' {$env:REVIEW_VERDICT}
 'RECLAIM' {'RECLAIMED'}
 'RESERVE' {'RESERVED'}
 'RECORD' {'RECORDED'}
 default {throw 'unexpected interpreter call'}
}
