#!/usr/bin/env pwsh
# Git Account Switcher Script
# Usage: .\switch-git-account.ps1 [personal|company]

param(
    [Parameter(Mandatory=$true)]
    [ValidateSet("personal", "company")]
    [string]$Account
)

Write-Host "Switching to $Account account..." -ForegroundColor Yellow

switch ($Account) {
    "personal" {
        Write-Host "Setting up personal account..." -ForegroundColor Green
        git config user.email "gabrieljerdhy.lapuz@gmail.com"
        git config user.name "Gabriel Jerdhy Lapuz"
        Write-Host "✅ Personal account configured:" -ForegroundColor Green
        Write-Host "   Email: gabrieljerdhy.lapuz@gmail.com" -ForegroundColor Cyan
        Write-Host "   Name: Gabriel Jerdhy Lapuz" -ForegroundColor Cyan
    }
    "company" {
        Write-Host "Setting up company account..." -ForegroundColor Green
        git config user.email "gabriel@support101.co"
        git config user.name "gabriel-lapuz"
        Write-Host "✅ Company account configured:" -ForegroundColor Green
        Write-Host "   Email: gabriel@support101.co" -ForegroundColor Cyan
        Write-Host "   Name: gabriel-lapuz" -ForegroundColor Cyan
    }
}

Write-Host ""
Write-Host "Current repository configuration:" -ForegroundColor Yellow
git config user.email
git config user.name

Write-Host ""
Write-Host "💡 Tip: This only affects the current repository." -ForegroundColor Blue
Write-Host "   To set globally, add --global flag to the commands." -ForegroundColor Blue
