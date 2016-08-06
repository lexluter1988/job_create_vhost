import yum
import os
from sys import argv

""" this is class Model for virtual host in apache """
rewite_ip = argv[1]


class VhostModel(object):

    def __init__(self, listen='_default_:80',
                 errorlog='logs/oaci_error_log', transferlog='logs/oaci_access_log', loglevel='debug',
                 directory='/var/www/oaci/',
                 options='Indexes FollowSymLinks +Includes',
                 allowoverride='All', order='allow,deny',
                 allowfrom='all', ssl=False):

        self.loglevel = loglevel
        self.directory = directory
        self.options = options
        self.allowoverride = allowoverride
        self.order = order
        self.allowfrom = allowfrom
        self.ssl = ssl

        if ssl:
            self.listen = '_default_:443'
            self.errorlog = 'logs/oaci_ssl_error_log'
            self.transferlog = 'logs/oaci_ssl_access_log'
        else:
            self.listen = listen
            self.errorlog = errorlog
            self.transferlog = transferlog


""" this is class View for virtual host in apache """


class VhostView(object):
    def __init__(self, instance=VhostModel()):

        self.instance = instance

    def get_listen(self):
        str_listen = "<VirtualHost %s" % \
            self.instance.listen \
            + ">"
        return str_listen

    def get_docroot(self):
        str_docroot = "\tDocumentRoot \"%s" % \
            self.instance.directory + "html\""

        return str_docroot

    def get_logs(self):
        str_logs = "\tErrorLog %s" % self.instance.errorlog \
            + "\n" + "\tTransferLog %s" % self.instance.transferlog \
            + "\n" + "\tLogLevel %s" % self.instance.loglevel

        return str_logs

    def get_directory(self):
        str_directory = "\t<Directory \"%s" % self.instance.directory \
            + "html\"" \
            + ">" \
            + "\n" + "\t\tAddType application/exe .run" \
            + "\n" + "\t\tOptions %s" % self.instance.options \
            + "\n" + "\t\tAllowOverride %s" % self.instance.allowoverride \
            + "\n" + "\t\tOrder %s" % self.instance.order \
            + "\n" + "\t\tAllow from %s" % self.instance.allowfrom \
            + "\n" + "\t</Directory>" \
            + "\n" \
            + "\n" + "\tScriptAlias /cgi-bin/ %s" % self.instance.directory \
            + "cgi-bin>" \
            + "\n" + "\t<Directory \"%s" % self.instance.directory \
            + "cgi-bin\">" \
            + "\n" + "\t\tAllowOverride None" \
            + "\n" + "\t\tOptions None" \
            + "\n" + "\t\tOrder allow,deny" \
            + "\n" + "\t\tAllow from all" \
            + "\n" + "\t</Directory>"

        return str_directory

    def get_ssl(self):
        if self.instance.ssl:
            str_ssl = "\t" + "SSLEngine on" \
                + "\n" + "\tSSLProtocol all -SSLv2" \
                + "\n" + "\tSSLCipherSuite ALL:!ADH:!EXPORT:!SSLv2:RC4+RSA:+HIGH:+MEDIUM:+LOW" \
                + "\n" + "\tSSLCertificateFile /etc/pki/tls/certs/localhost.crt" \
                + "\n" + "\tSSLCertificateKeyFile /etc/pki/tls/private/localhost.key" \
                + "\n" + "\t<Files ~ \"\.(cgi|shtml|phtml|php3?)$\">" \
                + "\n" + "\t\tSSLOptions +StdEnvVars" \
                + "\n" + "\t</Files>" \
                + "\n" + "\tSetEnvIf User-Agent \".*MSIE.*\" \\" \
                + "\n" + "\t\tnokeepalive ssl-unclean-shutdown \\" \
                + "\n" + "\t\tdowngrade-1.0 force-response-1.0"

            return str_ssl

    @staticmethod
    def get_proxy():

        str_proxy = "<Proxy *>" \
            + "\n" + "\tOrder allow,deny" \
            + "\n" + "\tAllow from all" \
            + "\n" + "</Proxy>" \
            + "\n" + "ProxyVia On" \
            + "\n" + "ProxyRequests On"

        return str_proxy

    @staticmethod
    def begin_config():

        str_begin_config = "AddOutputFilter INCLUDES .html"
        return str_begin_config

    @staticmethod
    def end_vhost():

        str_end_vhost = "</VirtualHost>"
        return str_end_vhost


""" this is class is taking VhostView and VhostView for virtual creation """


class WorkFlow(object):

    def __init__(self, vhostname='oaci'):
        self.vhostname = vhostname
        self.nosslvhost = VhostView(VhostModel(ssl=False))
        self.sslvhost = VhostView(VhostModel(ssl=True))

    @staticmethod
    def install_httpd_if_needed():
        yb = yum.YumBase()
        if yb.rpmdb.searchNevra(name='httpd'):
            print "Apache already installed, nothing to do"
            return True
        else:
            print "Installing stock apache"
            os.system("yum install -y httpd")
            return False

    @staticmethod
    def install_modproxyws_if_needed():
        yb = yum.YumBase()
        if yb.rpmdb.searchNevra(name='mod_proxy_wstunnel'):
            print "mod_proxy_wstunnel already installed, nothing to do"
            return True
        else:
            print "Installing mod_proxy_wstunnel"
            os.system("yum install -y mod_proxy_wstunnel")
            return False

    @staticmethod
    def install_modrewritews_if_needed():
        yb = yum.YumBase()
        if yb.rpmdb.searchNevra(name='mod_rewrite_ws'):
            print "mod_rewrite_ws already installed, nothing to do"
            return True
        else:
            print "Installing mod_rewrite_ws"
            os.system("yum install -y mod_rewrite_ws")
            return False

    @staticmethod
    def httpd_reload():
        os.system("service httpd reload")

    @staticmethod
    def httpd_restart():
        os.system("service httpd restart")

    @staticmethod
    def import_mod_rewrite_ws():
        os.system("cp /etc/httpd/conf/httpd.conf /etc/httpd/conf/httpd.conf.bak")
        with open('/etc/httpd/conf/httpd.conf', 'r') as origin:
            search_str = 'LoadModule rewrite_module modules/mod_rewrite.so'
            replace_str = 'LoadModule rewrite_module modules/mod_rewrite_ws/mod_rewrite_ws.so'
            input_str = origin.read()
            output_str = input_str.replace(search_str, replace_str)

        with open('/etc/httpd/conf/httpd.conf', 'w') as replaced:
            replaced.write(output_str)

    def generate_vhost_conf(self):
        vhost_conf = self.nosslvhost.begin_config() \
            + "\n" + self.nosslvhost.get_proxy() \
            + "\n" + self.nosslvhost.get_listen() \
            + "\n" + self.nosslvhost.get_docroot() \
            + "\n" + self.nosslvhost.get_logs() \
            + "\n" + self.nosslvhost.get_directory() \
            + "\n" + self.nosslvhost.end_vhost() \
            + "\n" + self.sslvhost.get_listen() \
            + "\n" + self.sslvhost.get_logs() \
            + "\n" + self.nosslvhost.get_docroot() \
            + "\n" + self.sslvhost.get_ssl() \
            + "\n" + self.sslvhost.get_directory() \
            + "\n" + self.sslvhost.end_vhost()

        return vhost_conf

    @staticmethod
    def write_config(config, text):
        os.system('mv /etc/httpd/conf.d/parallels.conf /etc/httpd/conf.d/parallels.conf.bak')
        os.system('mkdir /var/www/oaci')
        os.system('mkdir /var/www/oaci/html')
        os.system('mkdir /var/www/oaci/cgi-bin')

        with open(config, 'a') as vhostconf:
            vhostconf.write(text)

    @staticmethod
    def generate_rewrite():

        rewrite_str = "RewriteEngine on" \
            + "\n" + "RewriteRule ^websocket/([^/]+) wss://" + rewite_ip + ":$1/websockify [P]"\
            + "\n" + "RewriteRule ^oaciws/([^/]+)/([^/]+) ws://" + rewite_ip + ":$2/websockify [P]"

        with open('/var/www/oaci/html/.htaccess', 'a') as rewrite_conf:
            rewrite_conf.write(rewrite_str)

""" this is main pipeline of calls """
pipeline = WorkFlow()

print "stage #1: checking Apache"
pipeline.install_httpd_if_needed()

print "stage #2: checking mod_proxy and mod_wstunnel"
pipeline.install_modproxyws_if_needed()
pipeline.install_modrewritews_if_needed()

print "stage #3: importing modules and configurations"
pipeline.import_mod_rewrite_ws()

print "stage #4: creating OACI websockets vhost"
pipeline.write_config('/etc/httpd/conf.d/oaci.conf', pipeline.generate_vhost_conf())

print "stage #5: reloading and restarting Apache"
pipeline.httpd_restart()

print "stage #6: creating rewrite rules"
pipeline.generate_rewrite()

