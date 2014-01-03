### 1. Upgrade Debian
apt-get update  
apt-get upgrade  

### 2. Install software
apt-get install ufw
apt-get install nginx  
apt-get install python-dev  
apt-get install python-mysqldb  
apt-get install python-pip  
apt-get install supervisor  

### 3. Install Python libraries
pip install beautifulsoup4  
pip install boto  
pip install chardet  
pip install croniter  
pip install markdown2  
pip install ply  
pip install python-magic  
pip install PyYAML  
pip install PyZ3950  
pip install SimpleAES  
pip install suds  
pip install tornado  
pip install tornadomail  
pip install torndb  
pip install xmltodict  

### 4. Fix PyZ3950 (if needed)
Change file /usr/local/lib/python2.7/dist-packages/PyZ3950/ccl.py:   
"import lex" -> "from ply import lex" (line 124)   
"import yacc" -> "from ply import yacc" (line 140)

[More info abaut this fix...](http://bayo.opadeyi.net/2011/05/getting-pyz3950-to-play-nice-with.html)

### 5. Make Entu folders
mkdir -p /entu/conf  
mkdir -p /entu/log  
mkdir -p /entu/backup  
mkdir -p /entu/code/develop  
