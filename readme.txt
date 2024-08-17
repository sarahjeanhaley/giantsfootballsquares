1. Set up virtual environemnt
2. Install pips requests beautifulsoup4
3. Sel up sql tables
    a. games tables
        results of games
        webscraping to get this data
    b. users tables
        holds their square location, like coordinates
    c. weekly results
        need to store the location of the numbers, along the top and along the side, maybe in some lsit or something?
4. poolUserSetup.py - Sets up the User table and all users with random names and random locations on the baord, using x and y coordaintes, then stores in an SQL table
5. poolBoardSetup.py - Sets up the weekly game boards for the 18 weeks of the seasons and stores in an SQL table
6. pool2023GameResults.py - getting the results of the 2023 season for the Giants, and then storing these in a table.
    Will eventually update to store 2024 game data and upload when there is a new week of data



---- Steps for setting up on aWS--
1. Make an EC2 serverLaunch an EC2 Instance:

Go to the EC2 dashboard and click "Launch Instance."
Choose an Amazon Machine Image (AMI). The most common choice is Amazon Linux 2 AMI or Ubuntu Server.
Select an instance type (e.g., t2.micro for free tier).
Configure instance details (you can leave defaults unless you need specific network settings).
Add storage (default is usually fine).
Configure security groups to allow HTTP (port 80) and SSH (port 22) access.
--- Had to go to the securitt groups, did all traffic for my IP and the IP it told maybe
2. connect in the browser, ran these commands:
sudo yum update -y  
sudo yum install python3 git -y
sudo yum install python3-pip -y
pip3 install --user virtualenv

3. clone my github 
git clone https://github.com/your-repo/flask-app.git
cd <flask-app-name-here>


4. est up virtual environemnt
virtualenv venvaws
source venvaws/bin/activate
pip install -r requirements.txt

pip install gunicorn

gunicorn --bind 0.0.0.0:8000 app:app

5. cntrl c to cancel and then install nginx

sudo yum install nginx -y
sudo systemctl start nginx
sudo systemctl enable nginx

6. check status

sudo systemctl status nginx

5. Configure Nginx as a Reverse Proxy
Now, you can configure Nginx to forward requests to your Gunicorn server:

Open the Nginx Configuration File:

sudo nano /etc/nginx/nginx.conf



Modify the Configuration:
Replace the contents with the following (or modify the existing server block):

Inside this file, look for the http block. If there's no existing server block, add a new one:
/etc/nginx/nginx.conf.



server {
    listen 80;
    server_name http://52.90.88.166/;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}



Replace your-ec2-public-ip with your actual EC2 public IP address.

Save and exit using Ctrl + O, Enter, and Ctrl + X.

Restart Nginx:
After making changes, restart Nginx to apply the new configuration:


sudo systemctl restart nginx




