############################################################
# Dockerfile to build Entu container images
# Based on Ubuntu
############################################################


FROM ubuntu:14.04

MAINTAINER Argo Roots <argo@roots.ee>


#################### BEGIN INSTALLATION ####################

# Update the repository & install necessary tools
RUN apt-get update
RUN apt-get install -y ufw nginx python-dev python-pip mysql-server mysql-client python-mysqldb python-imaging supervisor ntp
RUN pip install beautifulsoup4 chardet python-dateutil mistune ply PyYAML SimpleAES suds tornado torndb xmltodict

# Create Entu folders
RUN mkdir -p /entu/cert
RUN mkdir -p /entu/code
RUN mkdir -p /entu/conf
RUN mkdir -p /entu/files
RUN mkdir -p /entu/thumbs

# Copy a configuration files from the current directory
# ADD nginx.conf /entu/conf/

##################### INSTALLATION END #####################


EXPOSE 80
