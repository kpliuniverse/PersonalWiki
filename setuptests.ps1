# Remove the directory if it exists
Remove-Item -Recurse -Force testenv -ErrorAction SilentlyContinue

# Create the directory
New-Item -ItemType Directory -Path testenv | Out-Null

# Copy the contents of end-tests into testenv
Copy-Item -Path "end-tests\*" -Destination "testenv" -Recurse -Force