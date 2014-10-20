### 1. Upgrade Debian
apt-get update  
apt-get upgrade  
  
### 2. Install software
apt-get install ufw  
apt-get install nginx  
apt-get install python-dev  
apt-get install mysql-server mysql-client  
apt-get install python-mysqldb  
apt-get install python-imaging
apt-get install supervisor  
apt-get install ntp  

### 3. Install Python libraries
pip install beautifulsoup4  
pip install chardet  
pip install mistune  
pip install ply  
pip install PyYAML  
pip install SimpleAES  
pip install suds  
pip install tornado  
pip install torndb  
pip install xmltodict  
[PyZ3950](http://www.panix.com/~asl2/software/PyZ3950/)

#### 3.1 Fix PyZ3950 (if needed)
Change file /usr/local/lib/python2.7/dist-packages/PyZ3950/ccl.py:  
"import lex" -> "from ply import lex" (line 124)  
"import yacc" -> "from ply import yacc" (line 140)  
  
[More info abaut this fix...](http://bayo.opadeyi.net/2011/05/getting-pyz3950-to-play-nice-with.html)
