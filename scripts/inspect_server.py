import paramiko

hostname = "31.29.151.54"
username = "root"
password = "8gl87z5nc1MD"

try:
    print(f"Connecting to {hostname}...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname, username=username, password=password, timeout=10)
    print("Connected successfully!")
    
    commands = [
        "ls -la /etc/nginx/sites-enabled/",
        "cat /etc/nginx/sites-enabled/* 2>/dev/null || true",
        "ls -la /var/www/anton_website /var/www/anton-tsoy /var/www/html 2>/dev/null || true"
    ]
    
    for cmd in commands:
        print(f"\n--- Running: {cmd} ---")
        stdin, stdout, stderr = ssh.exec_command(cmd)
        out = stdout.read().decode('utf-8').strip()
        err = stderr.read().decode('utf-8').strip()
        if out:
            print(out)
        if err:
            print(f"ERROR: {err}")
            
    ssh.close()
except Exception as e:
    print(f"Error connecting: {e}")
