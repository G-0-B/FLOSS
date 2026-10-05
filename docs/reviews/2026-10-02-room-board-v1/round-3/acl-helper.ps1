param([string]$Path,[switch]$Restrict)
if($Restrict){
 $acl=Get-Acl -LiteralPath $Path
 $acl.SetAccessRuleProtection($true,$false)
 $sid=[Security.Principal.WindowsIdentity]::GetCurrent().User
 $rule=New-Object Security.AccessControl.FileSystemAccessRule($sid,'FullControl','Allow')
 $acl.AddAccessRule($rule)
 Set-Acl -LiteralPath $Path -AclObject $acl
}
$a=Get-Acl -LiteralPath $Path
[pscustomobject]@{protected=$a.AreAccessRulesProtected;sddl=$a.Sddl;rules=@($a.Access|ForEach-Object{[pscustomobject]@{identity=$_.IdentityReference.ToString();rights=$_.FileSystemRights.ToString();inherited=$_.IsInherited}})}|ConvertTo-Json -Depth 5
