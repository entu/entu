apt-get install ufw  
apt-get install nginx  
apt-get install python-dev  
apt-get install python-pip  
apt-get install mysql-server  
apt-get install mysql-client  
apt-get install python-mysqldb  
apt-get install python-imaging  
apt-get install supervisor  
apt-get install ntp  

pip install beautifulsoup4  
pip install chardet  
pip install python-dateutil  
pip install mistune  
pip install ply  
pip install PyYAML  
pip install SimpleAES  
pip install suds  
pip install tornado  
pip install torndb  
pip install xmltodict  
pip install boto  

PyZ3950 needs manual [installation](http://www.panix.com/~asl2/software/PyZ3950/) and [fix](http://bayo.opadeyi.net/2011/05/getting-pyz3950-to-play-nice-with.html). Change file /usr/local/lib/python2.7/dist-packages/PyZ3950/ccl.py:  
"import lex" -> "from ply import lex" (line 124)  
"import yacc" -> "from ply import yacc" (line 140)  
