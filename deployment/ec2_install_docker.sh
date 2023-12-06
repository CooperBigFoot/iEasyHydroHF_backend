sudo mkfs -t ext4 /dev/xvdh || echo 'filesystem /dev/svdh already created'
sudo mkdir /ebs_volume || echo '/ebs_volume already created'
sudo mount /dev/xvdh /ebs_volume/ || echo '/ebs_volume already mounted'

sudo chown -R $USER:$USER /ebs_volume
mkdir /ebs_volume/timescale_data || echo '/ebs_volume/timescale_data already created'
mkdir /ebs_volume/backups || echo '/ebs_volume/backups already created'

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


