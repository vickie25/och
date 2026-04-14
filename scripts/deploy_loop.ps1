# Deployment Watchdog Loop for Ongoza CyberHub

$max_attempts = 5
$attempt = 1
$success = $false

while (-not $success -and $attempt -le $max_attempts) {
    Write-Host "=== Deployment Attempt $attempt of $max_attempts ==="
    
    # Run the SSH deployment command provided by the user
    sshpass -p 'Ongoza@#1' ssh -tt -p 22 -o StrictHostKeyChecking=no administrator@69.30.235.220 "cd /var/www/och && git pull origin main && printf '%s\n' 'Ongoza@#1' | sudo -S -p '' docker-compose up -d --build && printf '%s\n' 'Ongoza@#1' | sudo -S -p '' docker-compose ps"
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Checking health status..."
        $ps_output = sshpass -p 'Ongoza@#1' ssh -tt -p 22 -o StrictHostKeyChecking=no administrator@69.30.235.220 "printf '%s\n' 'Ongoza@#1' | sudo -S -p '' docker-compose ps"
        
        if ($ps_output -match "Up" -or $ps_output -match "healthy") {
            Write-Host "DEPLOYMENT SUCCESSFUL AND VERIFIED"
            $success = $true
        } else {
            Write-Host "Containers are not healthy yet. Retrying..."
        }
    } else {
        Write-Host "Build failed (possibly OOM). Waiting 15s before retry..."
        Start-Sleep -Seconds 15
    }
    
    $attempt++
}

if (-not $success) {
    Write-Host "DEPLOYMENT FAILED AFTER $max_attempts ATTEMPTS"
    exit 1
}
