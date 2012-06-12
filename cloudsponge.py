from bynd.handlers import BaseHandler
from google.appengine.api import urlfetch
from urlparse import urljoin
import logging

class CloudSpongeHandler(BaseHandler):
    
    base_url = 'https://api.cloudsponge.com/'
    
    @property
    def domain_key(self):
        return self.config["auth"]["local" if self.is_dev else "server"]["domain_key"]

    @property
    def domain_password(self):
        return self.config["auth"]["local" if self.is_dev else "server"]["domain_password"]
    
    def get_url_response(self,url):
        """Builds the URL to query CloudSponge. Concatenates the base URL,
        request URL and the credentials to make the request

        :param url:
            The API url to call (eg begin_import/user_conset)
            
        :returns:
            The content/text returned by the API        
        """
        
        credentials = 'domain_key=%s&domain_password=%s' % (self.domain_key,self.domain_password)
        
        url = self.base_url + url + credentials
        
        logging.info('Making CloudSponge API call to: ' + url)

        response = urlfetch.fetch(url) 
        
        return response.content

    def get(self,stage,param):
        """Routes all get requests to the CloudSponge handler.
        There are three stages of getting contacts, start, progress and final.
        The first request is always 'start', this provides the oAuth login URL and
        prepares an import_id. 'progress' may then be polled multiple times
        until the contacts are ready to be pulled in, 'final' is then called to
        retrieve the list of contacts.

        :param stage:
            The stage of the flow (start/progress/final)

        :param param:
            This can either be the service requested (YAHOO/WINDOWSLIVE/GMAIL)
            or the import_id provided by start.
            **A param named param may be a bit of a confusing name in fairness...
            
        :returns:
            returns the correct route to the browser     
        """                
        if (stage == 'start'):
            return self.start_import(param)
        if (stage == 'progress'):
            return self.progress(param)
        if (stage == 'final'):
            return self.final(param)
        
        return self.render_template('error/error.html')
        
        return self.redirect("/error/unknown-import")

    def post(self,stage,param):
        """Routes all post requests to the CloudSponge handler.
        Some email providers (PLAXO/AOL) require you to pass through the username
        and password straight to their API. Therefore these are handled in a
        slightly different way. This collects post data from a form containing
        username and password

        :param stage:
            The stage of the flow (start/progress/final)

        :param param:
            This can either be the service requested (AOL/PLAXO)
            **A param named param may be a bit of a confusing name in fairness...
            
        :returns:
            returns the correct route to the browser     
        """                
   
        return self.start_import(param,self.request.form.get('username'),self.request.form.get('password'))

    def start_import(self,service,username=None,password=None):
        """Initial request to the API, a service must be requested.

        :param service:
            This is the email supplier to use (YAHOO/WINDOWSLIVE/GMAIL)
            
        :returns:
            Renders out template to the browser   
        """
                
        #different request base depending on provider
        request_base = 'begin_import/import?username=%s&password=%s&' % (username,password);
        
        #If no username or password assume that it is doing an oAuth flow
        if (username == None and password == None):
            request_base = 'begin_import/user_consent?'
        
        logging.info('Request Base: ' + request_base)
        
        url = request_base+'service=%s&' % (service)

        response = self.get_url_response(url)
        
        return self.render_json(response)
        

    def progress(self,import_id):
        """Progress request to the API - this may be polled multiple times
        to get progress of the flow from CloudSponge. 

        :param import_id:
            This is the id supplied from self.start_import()'s initial request.
            
        :returns:
            Renders out template to the browser   
        """
                
        url = 'events/%s?' % (import_id)

        response = self.get_url_response(url)
        
        return self.render_json(response)
        
    def final(self,import_id):
        """Retrieve contacts from user after they have completed the flow and
        self.progress() has returned complete.

        :param import_id:
            This is the id supplied from self.start_import()'s initial request.
            
        :returns:
            Renders out template to the browser   
        """
                
        url = 'contacts/%s?' % (import_id)

        response = self.get_url_response(url)
        
        return self.render_json(response)
