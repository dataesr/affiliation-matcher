#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Fake Chrome browser using CEF for reading a webpage
from __future__ import print_function

import logging
import os
import sys
import threading
import time

import requests
import unidecode
from cefpython3 import cefpython as cef
from matcher.server.main.utils_swift import set_objects, exists_in_storage, get_hash

sys.excepthook = cef.ExceptHook # shutdown CEF processes on exception
logger = logging.getLogger('fc')

def get_ip():
    ip = requests.get('https://api.ipify.org').text
    return ip

class fakechromehandlers(object):
    '''
    Handler object
    '''
    __slots__ = ('chrome',)
    def __init__(self, fakechrome):
        self.chrome = fakechrome

    def GetViewRect(self, rect_out, **kwargs):
        "RenderHandler interface. CEF will call this to read what geometry should the browser be"
        logger.debug('Reset view rect')
        rect_out.extend([0, 0, self.chrome.width, self.chrome.height]) # [x, y, width, height]
        return True

    def OnConsoleMessage(self, browser, message, **kwargs):
        "DisplayHandler interface. Intercept all message printted to console"
        self.chrome.console.append(message)

    def OnLoadError(self, browser, frame, error_code, failed_url, **_):
        self.chrome.ready = error_code # like True
        logger.debug('Load Error')
        self.chrome._getReadyLock.acquire()
        self.chrome._getReadyLock.notify()
        self.chrome._getReadyLock.release()

    def OnLoadingStateChange(self, browser, is_loading, **kwargs):
        "LoadHandler interface. Browser will call when load state change"
        if not is_loading:
            # Loading is complete. DOM is ready.
            self.chrome.ready = True
            logger.debug('Loaded')
            self.chrome._getReadyLock.acquire()
            self.chrome._getReadyLock.notify()
            self.chrome._getReadyLock.release()
        else:
            logger.debug('Loading')
            self.chrome.ready = False

class fakechrome(object):
    # https://stackoverflow.com/questions/472000/usage-of-slots
    __slots__ = ('width','height','headless','browser','source','domArray'
                ,'windowParams','ready','_handler','__weakref__' # weakref for StringVisitor iface
                ,'console','_getSourceLock','_getDOMLock','_getReadyLock')

    def __init__(self, width=1920, height=1080, headless=False):
        self.width = width
        self.height = height
        self.headless = headless

        # pointer to reusable CEF objects
        self.console = []
        self.browser = None
        self.source = None
        self.domArray = None
        self.windowParams = None
        self.ready = True
        self._getSourceLock = threading.Condition()
        self._getDOMLock = threading.Condition()
        self._getReadyLock = threading.Condition()
        self._handler = fakechromehandlers(self)

        settings = {
            'user_agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) ' \
                         'AppleWebKit/537.36 (KHTML, like Gecko) ' \
                         'Chrome/64.0.3282.140 Safari/537.36'
        }
        if self.headless:
            settings['windowless_rendering_enabled'] = True
        settings['downloads_enabled'] = False
        cef.Initialize(settings=settings)

    def __getattr__(self, name):
        # all unknown attributes/methods will pass through to CEF browser
        return getattr(self.browser, name)

    def getBrowser(self):
        if self.browser:
            return self.browser
        # create browser instance
        if self.headless:
            parent_handle = 0
            winfo = cef.WindowInfo()
            winfo.SetAsOffscreen(parent_handle)
            self.browser = cef.CreateBrowserSync(window_info=winfo)
        else:
            self.browser = cef.CreateBrowserSync()
        # create bindings for DOM walker and handler for browser activities
        self.browser.SetClientHandler(self._handler) # use render handler to resize window
        self.browser.SendFocusEvent(True) # put browser in focus
        self.browser.WasResized() # need to call this at least once in headless mode
        bindings = cef.JavascriptBindings(bindToFrames=False, bindToPopups=True)
        bindings.SetFunction("get_attr_callback", self._domWalkerCallback)
        self.browser.SetJavascriptBindings(bindings)
        logger.debug('Browser created')
        return self

    def LoadUrl(self, url, synchronous=False):
        "Load a URL, pass-through to CEF browser"
        self.ready = False # safe-guard the wait below
        self.browser.LoadUrl(url)
        logger.debug('Waiting for %s to load' % url)
        if synchronous:
            self._getReadyLock.acquire()
            if not self.ready:
                self._getReadyLock.wait() # sleep until browser status update, no timeout
            self._getReadyLock.release()

    def getSource(self, synchronous=False):
        'Get HTML source code of the main frame asynchronously. Handled by self.Visit() when ready'
        self.source = None
        self.browser.GetMainFrame().GetSource(self)
        logger.debug('Waiting for HTML source ready')
        if synchronous:
            self._getSourceLock.acquire()
            if not self.source:
                self._getSourceLock.wait() # sleep until Visit() populated self.source, no timeout
            self._getSourceLock.release()
        return self.source

    def _domWalkerCallback(self, array, windowparams=None):
        "Bound to Javascript as callback function for DOM walker"
        logger.debug('DOM walker called back')
        self.domArray = array
        self.windowParams = windowparams
        self._getDOMLock.acquire()
        self._getDOMLock.notify()
        self._getDOMLock.release()

    def getDOMdata(self, synchronous=False):
        self.domArray = None
        # read JS code that to be executed
        js_path = os.path.join(os.path.abspath(os.path.dirname(__file__)),"cef_walkdom.js")
        js_code = open(js_path).read()
        # make sure the binding is there
        bindings = self.browser.GetJavascriptBindings()
        bindings.SetFunction("get_attr_callback", self._domWalkerCallback)
        bindings.Rebind()
        threading.Timer(1, self.browser.GetMainFrame().ExecuteJavascript, [js_code]).start()
        logger.debug('Waiting for DOM data ready')
        if synchronous:
            self._getDOMLock.acquire()
            if self.domArray is None:
                self._getDOMLock.wait() # sleep until JS code callback set self.domArray, no timeout
            self._getDOMLock.release()
        return self.domArray

    def Visit(self, value):
        "StringVisitor interface. GetSource() will call this function with browser's source HTML"
        self.source = value
        self._getSourceLock.acquire()
        self._getSourceLock.notify()
        self._getSourceLock.release()


def crawlmain(browser, url, title):

    container = "landing-page-html"

    notice_id = url
    init = 'url'
    doi = None
    if 'doi.org' in url:
        doi = url.replace('http://', '').replace('https://', '').replace('dx.','').replace('doi.org/', '').strip()
        init = doi.split('/')[0]
        notice_id = "doi{}".format(doi)
    id_hash = get_hash(notice_id)
    filename = "{}/{}.json.gz".format(init, id_hash)

    if exists_in_storage(container, filename):
        print("{} already exists ({})".format(url, filename), flush=True)
        browser.CloseBrowser()
        return
    
    browser.LoadUrl(url, synchronous=True)
    browser.LoadUrl(url, True) # True = synchronous call
    for i in range(100):
        cef.MessageLoopWork()
        time.sleep(0.01)
    source = browser.getSource(True) # synchronous get
    
    source2 = source.replace("<html><head></head><body></body></html>","")
    print("len source = {}".format(len(source2)), flush=True)
    print("source = {}".format(source2), flush=True)
    
    wait_longer = False

    important_words = []
    if title:
        title_normalized = unidecode.unidecode(title).lower()
        title_words = [w for w in title_normalized.split(' ') if len(w)>4]
        important_words = sorted(title_words , key = len, reverse = True)
    
    if doi:
        if doi not in source.lower():
            wait_longer = True
    #if '10.1016' in url:
    #    wait_longer = True
    
    if wait_longer and len(source2)>0:
        print("wait longer for "+url, flush=True)
        for i in range(1000):
            cef.MessageLoopWork()
            time.sleep(0.01)

    source = browser.getSource(True) # synchronous get
    assert(source)
    source_normalized = unidecode.unidecode(source).lower()
    
    #count the number of important words present in source
    present = 0
    for w in important_words:
        if w in source_normalized:
            present += 1
    print("{} / {} words present from title in html".format(present, len(important_words)), flush=True)
    
    ok_doi = False
    if doi:
        ok_doi = (doi in source_normalized)
    
    ok_title = (present > len(important_words)/2)

    ok = ok_doi or ok_title or len(source2)==0
    print("ok_doi : {} ok_title : {}".format(ok_doi, ok_title), flush=True)
    if not ok:
        print("seems scraping failed for "+url, flush=True)

    else:
        ip = get_ip()
        answer_elt = {"id": notice_id, "notice":source, "url":url, "ip": ip}
        if doi:
            answer_elt['doi'] = doi
        notices = [answer_elt]
        set_objects(container, filename, notices)
    
    browser.CloseBrowser()


def crawl(url, title):
    print("start crawl for {} {}".format(url, title), flush=True)
    browser = fakechrome(width=640, height=480, headless=False).getBrowser()
    logger.info('Browser loaded')
    workthread = threading.Thread(target=crawlmain, args=(browser, url, title))
    workthread.start()
    logger.info('Running CEF message loop')
    cef.MessageLoop() # blocking until browser closed
    logger.info('Message loop end')
    workthread.join()
    cef.Shutdown()
