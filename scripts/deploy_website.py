import paramiko
import tarfile
import os

hostname = "31.29.151.54"
username = "root"
password = "8gl87z5nc1MD"

local_website_dir = "/Users/anton_tsoy/Desktop/Обсидиан/website"
archive_name = "website.tar.gz"
remote_archive_path = f"/tmp/{archive_name}"

# 1. Create a tarball of the website directory locally
print("Creating local archive of website files...")
with tarfile.open(archive_name, "w:gz") as tar:
    # Change directory to website folder so files are at root of archive
    tar.add(local_website_dir, arcname=".")
print("Archive created successfully.")

try:
    # 2. Connect to the VPS via SFTP/SSH
    print(f"Connecting to {hostname} via SSH...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname, username=username, password=password, timeout=15)
    print("SSH connection established.")
    
    # 3. Upload the archive using SFTP
    print("Uploading archive to VPS...")
    sftp = ssh.open_sftp()
    sftp.put(archive_name, remote_archive_path)
    sftp.close()
    print(f"Archive uploaded to {remote_archive_path}.")
    
    # 4. Extract the archive to the remote directories
    # We will extract to /var/www/anton-tsoy and /var/www/anton_website to be safe and ensure coverage.
    target_dirs = ["/var/www/anton-tsoy", "/var/www/anton_website"]
    
    for target in target_dirs:
        print(f"Deploying to {target}...")
        # Create target dir if it doesn't exist
        ssh.exec_command(f"mkdir -p {target}")
        
        # Extract archive contents into target directory
        cmd = f"tar -xzf {remote_archive_path} -C {target}"
        stdin, stdout, stderr = ssh.exec_command(cmd)
        err = stderr.read().decode('utf-8').strip()
        if err:
            print(f"Error extracting to {target}: {err}")
        else:
            print(f"Successfully extracted to {target}")
            
        # Ensure permissions are correct
        ssh.exec_command(f"chown -R root:root {target}")
        ssh.exec_command(f"chmod -R 755 {target}")
        
    # 5. Clean up remote and local archives
    print("Cleaning up archives...")
    ssh.exec_command(f"rm {remote_archive_path}")
    ssh.close()
    
    if os.path.exists(archive_name):
        os.remove(archive_name)
    print("Deployment finished successfully!")
    
except Exception as e:
    print(f"Deployment failed: {e}")
    if os.path.exists(archive_name):
        os.remove(archive_name)
