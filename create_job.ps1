param(
    [string]$Url = "https://www.galleryofguns.com/",
    [int]$IntervalSeconds = 86400,
    [string]$Mode = "static",
    [string]$WebhookUrl = "http://127.0.0.1:8001"
)

$body = @{
    url = $Url
    interval_seconds = $IntervalSeconds
    mode = $Mode
    webhook_url = $WebhookUrl
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://127.0.0.1:8000/jobs" -Method Post -Body $body -ContentType "application/json"
