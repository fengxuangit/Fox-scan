#!/usr/bin/env python
#!-*- coding:utf-8 -*-
import sys
import argparse
import logging
import atexit
import os
import time
import signal
import threading
from Queue import Queue

from mitmproxy import flow, proxy
from mitmproxy.proxy.server import ProxyServer

from action import ProxyHander

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
)


class BackProxyHandle(threading.Thread):
    def __init__(self, queue):
        threading.Thread.__init__(self)
        self.queue = queue

    def run(self):
        print "\n"
        while self.queue.empty() == False:
            print "[*] Waiting for Queue..."
            request = self.queue.get()
            if request['uri'].find('127.0.0.1')>=0:
                continue
            print request['uri']
            print "[*] Process Queue"
            ProxyHander(request)

save_content = False

http_mimes = ['text', 'image', 'application', 'video', 'message', 'audio']

# http static resource file extension
static_ext = []

# media resource files type
media_types = []

# http static resource files
static_files = [
    ]


# Core modules

class ResponseParser(object):
    """docstring for ResponseParser"""

    def __init__(self, f):
        super(ResponseParser, self).__init__()
        self.flow = f
        self.content_type = self.get_content_type()
        self.extension = self.get_extension()
        self.ispass = self.capture_pass()

    def parser_data(self):
        """parser the capture response & request"""

        result = {}
        result['content_type'] = self.content_type
        result['url'] = self.get_url()
        result['path'] = self.get_path()
        result['extension'] = self.get_extension()
        result['host'] = self.get_host()
        result['port'] = self.get_port()
        result['scheme'] = self.get_scheme()
        result['method'] = self.get_method()
        result['status_code'] = self.get_status_code()
        result['date_start'] = self.flow.response.timestamp_start
        result['date_end'] = self.flow.response.timestamp_end
        result['content_length'] = self.get_content_length()
        result['static_resource'] = self.ispass
        result['header'] = self.get_header()
        result['request_header'] = self.get_request_header()
        
        # request resource is media file & static file, so pass
        if self.ispass:
            result['content'] = None
            result['request_content'] = None
            return result

        result['content'] = self.get_content() if save_content else ''
        result['request_content'] = self.get_request_content() if save_content else ''
        return result

    def get_content_type(self):

        if not self.flow.response.headers.get('Content-Type'):
            return ''
        return self.flow.response.headers.get('Content-Type').split(';')[:1][0]

    def get_content_length(self):
        if self.flow.response.headers.get('Content-Length'):
            return int(self.flow.response.headers.get('Content-Length'))
        else:
            return 0

    def capture_pass(self):
        """if content_type is media_types or static_files, then pass captrue"""

        if self.extension in static_ext:
            return True

        # can't catch the content_type
        if not self.content_type:
            return False

        if self.content_type in static_files:
            return True

        http_mime_type = self.content_type.split('/')[:1]
        if http_mime_type:
            return True if http_mime_type[0] in media_types else False
        else:
            return False

    def get_header(self):
        return self.parser_header(self.flow.response.headers)

    def get_content(self):
        return self.flow.response.get_decoded_content()

    def get_request_header(self):
        return self.parser_header(self.flow.request.headers)

    def get_request_content(self):
        return self.flow.request.get_decoded_content()

    def get_url(self):
        return self.flow.request.url

    def get_path(self):
        return '/{}'.format('/'.join(self.flow.request.path_components))

    def get_extension(self):
        if not self.flow.request.path_components:
            return ''
        else:
            end_path = self.flow.request.path_components[-1:][0]
            split_ext = end_path.split('.')
            if not split_ext or len(split_ext) == 1:
                return ''
            else:
                return split_ext[-1:][0]

    def get_scheme(self):
        return self.flow.request.scheme

    def get_method(self):
        return self.flow.request.method

    def get_port(self):
        return self.flow.request.port

    def get_host(self):
        return self.flow.request.host

    def get_status_code(self):
        return self.flow.response.status_code

    @staticmethod
    def parser_header(header):
        headers = {}
        for key, value in header.iteritems():
            headers[key] = value
        return headers


class Daemon(object):
    """
    A generic daemon class.

    Usage: subclass the Daemon class and override the run() method
    """
    def __init__(self, pidfile, stdin=os.devnull,
                 stdout=os.devnull, stderr=os.devnull,
                 home_dir='.', umask=022, verbose=1, use_gevent=False):
        self.stdin = stdin
        self.stdout = stdout
        self.stderr = stderr
        self.pidfile = pidfile
        self.home_dir = home_dir
        self.verbose = verbose
        self.umask = umask
        self.daemon_alive = True
        self.use_gevent = use_gevent

    def daemonize(self):
        """
        Do the UNIX double-fork magic, see Stevens' "Advanced
        Programming in the UNIX Environment" for details (ISBN 0201563177)
        http://www.erlenstar.demon.co.uk/unix/faq_2.html#SEC16
        """
        try:
            pid = os.fork()
            if pid > 0:
                # Exit first parent
                sys.exit(0)
        except OSError, e:
            sys.stderr.write(
                "fork #1 failed: %d (%s)\n" % (e.errno, e.strerror))
            sys.exit(1)

        # Decouple from parent environment
        os.chdir(self.home_dir)
        os.setsid()
        os.umask(self.umask)

        # Do second fork
        try:
            pid = os.fork()
            if pid > 0:
                # Exit from second parent
                sys.exit(0)
        except OSError, e:
            sys.stderr.write(
                "fork #2 failed: %d (%s)\n" % (e.errno, e.strerror))
            sys.exit(1)

        if sys.platform != 'darwin':  # This block breaks on OS X
            # Redirect standard file descriptors
            sys.stdout.flush()
            sys.stderr.flush()
            si = file(self.stdin, 'r')
            so = file(self.stdout, 'a+')
            if self.stderr:
                se = file(self.stderr, 'a+', 0)
            else:
                se = so
            os.dup2(si.fileno(), sys.stdin.fileno())
            os.dup2(so.fileno(), sys.stdout.fileno())
            os.dup2(se.fileno(), sys.stderr.fileno())

        def sigtermhandler(signum, frame):
            self.daemon_alive = False
            sys.exit()

        if self.use_gevent:
            import gevent
            gevent.reinit()
            gevent.signal(signal.SIGTERM, sigtermhandler, signal.SIGTERM, None)
            gevent.signal(signal.SIGINT, sigtermhandler, signal.SIGINT, None)
        else:
            signal.signal(signal.SIGTERM, sigtermhandler)
            signal.signal(signal.SIGINT, sigtermhandler)

        if self.verbose >= 1:
            print "wyProxy daemon started successfully "

        # Write pidfile
        atexit.register(
            self.delpid)  # Make sure pid file is removed if we quit
        pid = str(os.getpid())
        file(self.pidfile, 'w+').write("%s\n" % pid)

    def delpid(self):
        os.remove(self.pidfile)

    def start(self, *args, **kwargs):
        """
        Start the daemon
        """

        if self.verbose >= 1:
            print "wyproxy daemon starting..."

        # Check for a pidfile to see if the daemon already runs
        try:
            pf = file(self.pidfile, 'r')
            pid = int(pf.read().strip())
            pf.close()
        except IOError:
            pid = None
        except SystemExit:
            pid = None

        if pid:
            message = "pidfile %s already exists. Is it already running?\n"
            sys.stderr.write(message % self.pidfile)
            sys.exit(1)

        # Start the daemon
        self.daemonize()
        self.run(*args, **kwargs)

    def stop(self):
        """
        Stop the daemon
        """

        if self.verbose >= 1:
            print "wyproxy daemon stopping..."

        # Get the pid from the pidfile
        pid = self.get_pid()

        if not pid:
            message = "pidfile %s does not exist. Not running?\n"
            sys.stderr.write(message % self.pidfile)

            # Just to be sure. A ValueError might occur if the PID file is
            # empty but does actually exist
            if os.path.exists(self.pidfile):
                os.remove(self.pidfile)

            return  # Not an error in a restart

        # Try killing the daemon process
        try:
            i = 0
            while 1:
                os.kill(pid, signal.SIGTERM)
                time.sleep(0.1)
                i = i + 1
                if i % 10 == 0:
                    os.kill(pid, signal.SIGHUP)
        except OSError, err:
            err = str(err)
            if err.find("No such process") > 0:
                if os.path.exists(self.pidfile):
                    os.remove(self.pidfile)
            else:
                print str(err)
                sys.exit(1)

        if self.verbose >= 1:
            print "wyproxy daemon stopped successfully"

    def restart(self):
        """
        Restart the daemon
        """
        self.stop()
        self.start()

    def get_pid(self):
        try:
            pf = file(self.pidfile, 'r')
            pid = int(pf.read().strip())
            pf.close()
        except IOError:
            pid = None
        except SystemExit:
            pid = None
        return pid

    def is_running(self):
        pid = self.get_pid()

        if pid is None:
            print 'Process is stopped'
        elif os.path.exists('/proc/%d' % pid):
            print 'Process (pid %d) is running...' % pid
        else:
            print 'Process (pid %d) is killed' % pid

        return pid and os.path.exists('/proc/%d' % pid)

    def run(self):
        """
        You should override this method when you subclass Daemon.
        It will be called after the process has been
        daemonized by start() or restart().
        """
        raise NotImplementedError

class WYProxy(flow.FlowMaster):
    queue = Queue()
    def __init__(self, server, state, unsave_data):
        super(WYProxy, self).__init__(server, state)
        self.unsave_data = unsave_data

    def run(self):
        try:
            logging.info("wyproxy started successfully...")
            flow.FlowMaster.run(self)
        except KeyboardInterrupt:
            self.shutdown()
            logging.info("Ctrl C - stopping wyproxy server")

    def handle_request(self, f):
        f = flow.FlowMaster.handle_request(self, f)
        if f:
            f.request.anticache()
            f.reply()
        return f

    def handle_response(self, f):
        f = flow.FlowMaster.handle_response(self, f)
        if f:
            if not self.unsave_data:
                parser = ResponseParser(f)
                data = parser.parser_data()
                proxy_dict = {}
                proxy_dict['uri'] = data['url']
                proxy_dict['method'] = data['method']
                proxy_dict['request_header'] = data['request_header']
                self.queue.put(proxy_dict)
                BackProxyHandle(self.queue).start()
            f.reply()
        return f

def start_server(proxy_port, proxy_mode, unsave_data):
    port = int(proxy_port) if proxy_port else 8080
    mode = proxy_mode if proxy_mode else 'regular'

    if proxy_mode == 'http':
        mode = 'regular'

    config = proxy.ProxyConfig(
        port=port,
        mode=mode,
        cadir="./ssl/",
    )

    state = flow.State()
    server = ProxyServer(config)
    m = WYProxy(server, state, unsave_data)
    m.run()

class wyDaemon(Daemon):
    def __init__(self, pidfile, proxy_port=8080, proxy_mode='regular', unsave_data=False):
        super(wyDaemon, self).__init__(pidfile)
        self.proxy_port = proxy_port
        self.proxy_mode = proxy_mode
        self.unsave_data = unsave_data

    def run(self):
        logging.info("wyproxy is starting...")
        logging.info("Listening: 0.0.0.0:{} {}".format(
            self.proxy_port, self.proxy_mode))
        start_server(self.proxy_port, self.proxy_mode, self.unsave_data)

def run(args):

    if args.restart:
        args.port = read_cnf().get('port')
        args.mode = read_cnf().get('mode')
        args.unsave = read_cnf().get('unsave')

    if not args.pidfile:
        args.pidfile = '/tmp/wyproxy.pid'
        
    wyproxy = wyDaemon(
        pidfile = args.pidfile,
        proxy_port = args.port,
        proxy_mode = args.mode,
        unsave_data = args.unsave)

    if args.daemon:
        save_cnf(args)
        wyproxy.start()
    elif args.stop:
        wyproxy.stop()
    elif args.restart:
        wyproxy.restart()
    else:
        wyproxy.run()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="wyproxy v 1.0 ( Proxying And Recording HTTP/HTTPs and Socks5)")
    parser.add_argument("-d","--daemon",action="store_true",
        help="start wyproxy with daemond")
    parser.add_argument("-stop","--stop",action="store_true",required=False,
        help="stop wyproxy daemond")
    parser.add_argument("-restart","--restart",action="store_true",required=False,
        help="restart wyproxy daemond")
    parser.add_argument("-pid","--pidfile",metavar="",
        help="wyproxy daemond pidfile name")
    parser.add_argument("-p","--port",metavar="",default="8080",
        help="wyproxy bind port")
    parser.add_argument("-m","--mode",metavar="",choices=['http','socks5','transparent'],default="http",
        help="wyproxy mode (HTTP/HTTPS, Socks5, Transparent)")
    parser.add_argument("-us","--unsave",action="store_true",required=False,
        help="Do not save records to MySQL server")
    args = parser.parse_args()

    try:
        run(args)
    except KeyboardInterrupt:
        logging.info("Ctrl C - Stopping Client")
        sys.exit(1)
