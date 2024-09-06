# Swap file location and size
SWAPFILE="/mnt/swapfile"

# Check if swap is already enabled
if swapon --show | grep -q "$SWAPFILE"; then
  echo "Swap is already enabled at $SWAPFILE. Continuing..."
else
  # Check if the swap file already exists
  if [ -f "$SWAPFILE" ]; then
    echo "Swap file already exists at $SWAPFILE."
  else
    # Create the swap file
    echo "Creating swap file at $SWAPFILE."
    sudo dd if=/dev/zero of="$SWAPFILE" bs=1G count=4  #4 GB swap file
    sudo chmod 600 "$SWAPFILE"
    sudo mkswap "$SWAPFILE"
  fi

  # Enable the swap file
  sudo swapon "$SWAPFILE"
fi

# Verify and display swap status
sudo swapon --show

# Mount EBS
sudo mkfs -t ext4 /dev/xvdh || echo 'filesystem /dev/svdh already created'
sudo mkdir /ebs_volume || echo '/ebs_volume already created'
sudo mount /dev/xvdh /ebs_volume/ || echo '/ebs_volume already mounted'
sudo mkdir /ebs_volume/imomo_ingestion_storage || echo '/ebs_volume/imomo_ingestion_storage already created'
sudo mkdir /ebs_volume/imomo_telegram_ingestion_storage || echo '/ebs_volume/imomo_telegram_ingestion_storage already created'

sudo chown -R $USER:$USER /ebs_volume
mkdir /ebs_volume/timescale_data || echo '/ebs_volume/timescale_data already created'
mkdir /ebs_volume/backups || echo '/ebs_volume/backups already created'
mkdir /ebs_volume/logs || echo '/ebs_volume/logs already created'
touch /ebs_volume/logs/cron-ingestion.log

sudo apt update
sudo apt install -y curl zip

curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

sudo groupadd docker
sudo usermod -aG docker $USER

sudo apt install -y docker-compose

mkdir /home/ubuntu/staging/dumps || echo '/home/ubuntu/staging/dumps already created'
# DB dump at 23:00 daily and make sure the /staging/dumps contains dumps not older than 6 months. Dumps are gzipped.
echo '0 23 * * * docker-compose -f /home/ubuntu/staging/backend-staging-compose.yml exec -T timescale pg_dump -U sapphire sapphire_backend | gzip > /home/ubuntu/staging/dumps/dump_sapphire_backend_$(date +\%Y\%m\%d).sql.gz && find /home/ubuntu/staging/dumps/ -type f -name '"'"'dump_sapphire_backend_*.sql.gz'"'"' -mtime +180 -exec rm {} \;' | crontab -
