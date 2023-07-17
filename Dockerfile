FROM selenium/standalone-chrome
RUN sudo apt-get update && sudo apt-get install -y \
  python3 \
  python3 python3-pip \
  git \
  vim
RUN pip3 install \
  instapy \
  awscli \
  boto3 \
  gspread \
  oauth2client \
  chromedriver-binary==91.0.4472.101.0
ADD Instagram_scripts/ /home/seluser/Instagram_scripts/
