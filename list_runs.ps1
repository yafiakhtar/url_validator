param(
    [Parameter(Mandatory = $true)]
    [string]$JobId
)

Invoke-RestMethod -Uri "http://127.0.0.1:8000/jobs/$JobId/runs" -Method Get
