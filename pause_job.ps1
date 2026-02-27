param(
    [Parameter(Mandatory = $true)]
    [string]$JobId
)

$body = @{ status = "paused" } | ConvertTo-Json
Invoke-RestMethod -Uri "http://127.0.0.1:8000/jobs/$JobId" -Method Patch -Body $body -ContentType "application/json"
