#!/usr/bin/python

# ------------------------------------------------------------------------------
# mURLin Exporter for Prometheus
# Exports URL monitoring metrics via HTTP for Prometheus consumption
# Author: Fabien Loudet
# Version : 0.1
# ------------------------------------------------------------------------------

import yaml
import pycurl
import cStringIO
import re
import cherrypy
from cherrypy.process.plugins import Daemonizer

class MurlinExporter(object):
  
  @cherrypy.expose 
  def index(self):
    # redirect index to /metrics
    raise cherrypy.HTTPRedirect('metrics/')

  @cherrypy.expose
  def metrics(self):
    # load configuration file
    with open('config.yml', 'r') as stream:
      try:
        config = yaml.safe_load(stream)
      except yaml.YAMLError as exc:
        print(exc)
    
    for host in config['hosts']:
    
      curl_info = {}
      
      curl = pycurl.Curl()
      buff = cStringIO.StringIO()
      curl.setopt(pycurl.WRITEFUNCTION, buff.write)
    
      curl.setopt(pycurl.URL, host['url'])
    
      # Set a sensible timeout
      curl.setopt(pycurl.CONNECTTIMEOUT, host['timeout'])
      curl.setopt(pycurl.TIMEOUT, host['timeout'] + 3)
    
      # Set redirect options
      curl.setopt(pycurl.FOLLOWLOCATION, True)
      curl.setopt(pycurl.MAXREDIRS, 10)
    
      # Set a proxy if required
      if host['proxyserver'] == 1:
        curl.setopt(pycurl.PROXY, host['proxyaddress'])
        if host['proxyusername'] != '':
          curl.setopt(pycurl.PROXYUSERPWD, "%s:%s" % (host['proxyusername'], host['proxypassword']))
    
      curl.perform()
    
      body = buff.getvalue()
    
      if body == "":
        print "ERROR - Nothing returned" 
    
      if re.search(host['text_match'], body):
        # Page Text matches
        curl_info['total_time'] = curl.getinfo(pycurl.TOTAL_TIME)
        curl_info['http_code'] = curl.getinfo(pycurl.HTTP_CODE)
        curl_info['size_download'] = curl.getinfo(pycurl.SIZE_DOWNLOAD)
        curl_info['redirect_count'] = curl.getinfo(pycurl.REDIRECT_COUNT)
    
        curl_info['availability'] = '100'
    
        curl_info['namelookup_time'] = curl.getinfo(pycurl.NAMELOOKUP_TIME)
        curl_info['connect_time'] = curl.getinfo(pycurl.CONNECT_TIME)
        curl_info['pretransfer_time'] = curl.getinfo(pycurl.PRETRANSFER_TIME)
        curl_info['starttransfer_time'] = curl.getinfo(pycurl.STARTTRANSFER_TIME)
        curl_info['redirect_time'] = curl.getinfo(pycurl.REDIRECT_TIME)
    
      else:
        # Page text doesn't match
        curl_info['total_time'] = '0'
        curl_info['http_code'] = curl.getinfo(pycurl.HTTP_CODE)
        curl_info['size_download'] = curl.getinfo(pycurl.SIZE_DOWNLOAD)
        curl_info['redirect_count'] = curl.getinfo(pycurl.REDIRECT_COUNT)
    
        curl_info['availability'] = '0'
    
        curl_info['namelookup_time'] = '0'
        curl_info['connect_time'] = '0'
        curl_info['pretransfer_time'] = '0'
        curl_info['starttransfer_time'] = '0'
        curl_info['redirect_time'] = '0'
    
      curl.close()

      # Numbers in scientific notation need to be converted to fixed point
      regex_scinot = re.compile(r"(\d+(\.\d+)?)[Ee](\+|-)(\d+)")
    
      for i, j in curl_info.items():
        if re.search(regex_scinot, str(j)):
          curl_info[i] = "%.8f" % float(j)

      host['curl_info'] = curl_info
    
    # Build Output
    stroutput = "# HELP total_time Total transaction time in seconds for last transfer\n"
    stroutput += "# TYPE total_time untyped\n"
    for host in config['hosts']:
      stroutput += "total_time{host=\"%s\"} %s\n" % (host['name'], host['curl_info']['total_time'])
    stroutput += "# HELP http_code The last response code\n"
    stroutput += "# TYPE http_code untyped\n"
    for host in config['hosts']:
      stroutput += "http_code{host=\"%s\"} %s\n" % (host['name'], host['curl_info']['http_code'])
    stroutput += "# HELP size_download Total number of bytes downloaded\n"
    stroutput += "# TYPE size_download untyped\n"
    for host in config['hosts']:
      stroutput += "size_download{host=\"%s\"} %s\n" % (host['name'], host['curl_info']['size_download'])
    stroutput += "# HELP redirect_count Number of redirects\n"
    stroutput += "# TYPE redirect_count untyped\n"
    for host in config['hosts']:
      stroutput += "redirect_count{host=\"%s\"} %s\n" % (host['name'], host['curl_info']['redirect_count'])
    stroutput += "# HELP availability Site availability\n"
    stroutput += "# TYPE availability untyped\n"
    for host in config['hosts']:
      stroutput += "availability{host=\"%s\"} %s\n" % (host['name'], host['curl_info']['availability'])
    stroutput += "# HELP namelookup_time Time in seconds until name resolving was complete\n"
    stroutput += "# TYPE namelookup_time untyped\n"
    for host in config['hosts']:
      stroutput += "namelookup_time{host=\"%s\"} %s\n" % (host['name'], host['curl_info']['namelookup_time'])
    stroutput += "# HELP connect_time Time in seconds it took to establish the connection\n"
    stroutput += "# TYPE connect_time untyped\n"
    for host in config['hosts']:
      stroutput += "connect_time{host=\"%s\"} %s\n" % (host['name'], host['curl_info']['connect_time'])
    stroutput += "# HELP pretransfer_time Time in seconds from start until just before file transfer begins\n"
    stroutput += "# TYPE pretransfer_time untyped\n"
    for host in config['hosts']:
      stroutput += "pretransfer_time{host=\"%s\"} %s\n" % (host['name'], host['curl_info']['pretransfer_time'])
    stroutput += "# HELP starttransfer_time Time in seconds until the first byte is about to be transferred\n"
    stroutput += "# TYPE starttransfer_time untyped\n"
    for host in config['hosts']:
      stroutput += "starttransfer_time{host=\"%s\"} %s\n" % (host['name'], host['curl_info']['starttransfer_time'])
    stroutput += "# HELP redirect_time Time in seconds of all redirection steps before final transaction was started\n"
    stroutput += "# TYPE redirect_time untyped\n"
    for host in config['hosts']:
      stroutput += "redirect_time{host=\"%s\"} %s\n" % (host['name'], host['curl_info']['redirect_time'])

    return stroutput
  
# Load Server Configuration
cherrypy.config.update("server.conf")
# Start as a daemon
d = Daemonizer(cherrypy.engine)
d.subscribe()

# Configure the app to send output as raw text
appconfig = {
  '/metrics': {
    'tools.response_headers.on': True,
    'tools.response_headers.headers': [('Content-Type', 'text/plain')],
  }
}

cherrypy.quickstart(MurlinExporter(), config=appconfig)
