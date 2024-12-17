if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Host "Docker not found, install Docker from https://desktop.docker.com/win/main/amd64/Docker%20Desktop%20Installer.exe"
}
else {
    docker compose build
    docker compose up
}