FROM ubuntu:14.04

MAINTAINER Argo Roots <argo@roots.ee>

RUN apt-get update
RUN apt-get install -y ufw
RUN apt-get install -y nginx
RUN apt-get install -y python-dev
RUN apt-get install -y python-pip
RUN apt-get install -y mysql-server
RUN apt-get install -y mysql-client
RUN apt-get install -y python-mysqldb
RUN apt-get install -y python-imaging
RUN apt-get install -y supervisor
RUN apt-get install -y ntp

RUN pip install beautifulsoup4
RUN pip install chardet
RUN pip install python-dateutil
RUN pip install mistune
RUN pip install ply
RUN pip install PyYAML
RUN pip install SimpleAES
RUN pip install suds
RUN pip install tornado
RUN pip install torndb
RUN pip install xmltodict
