#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""hose: unix pipeline for python"""
import sys,os
import time

class Processor(object):
    """Base class for a segment in a pipeline.
    An instance takes a stream of data and produces a stream of data.
    Segments are chained by the right shift (>>) operator.
    A subclass defines the stream transformation as a reverge generator 
    by overriding rgen method.
    """

    def __init__(self, *args, **opts):
        # pipeline linkage
        self.next=None
        self.prev=None
        # generic args for subclass instance.
        self.args=args
        self.opts=opts

    def __repr__(self):
        return self.__class__.__name__

    def __rshift__(self, rhs):
        """simply link up"""
        #print >>sys.stderr, '__rshift__', self, '-->', rhs
        self.next=rhs
        rhs.prev=self
        return rhs

    def rgen(self, nxt=None):
        """subclass overrides this with a reverse generator.
        while True:
            input_data=(yield)
            # some processing
            yield output1
            yield ...
        """
        OVERRIDE_ME

    def flush(self):
        pass

    def output(self):
        """a terminal segment subclass can override this to return final output"""
        return None

    def run(self):
        """Invoked on the terminal segment to hook up the generators to 
        process the data.
        """
        lin=list(self.reverse_lineage())
        print >>sys.stderr, 'run:', self, lin
        # 
        # build a rgen chain
        # 
        rhs_rg=None
        for cur in lin:
            # instantiate the reverse generator
            cur_rg=cur.rgen(rhs_rg)
            cur_rg.next()
            rhs_rg=cur_rg
        # 
        # kick off
        # 
        send(cur_rg, None)
        #
        # finish 
        # 
        for p in reversed(lin):
            p.flush()

        return self.output()

    def reverse_lineage(self):
        """sequence of segments from end to start """
        cur=self
        while cur:
            yield cur
            cur=cur.prev

def send(nxt, data):
    """nxt.send that swallows StopIteration.
    It's like ignoring sigpip in unix pipeline..
    """
    if nxt:
        try:
            nxt.send(data)
        except StopIteration:
            pass

#### subclasses

import urllib2
import hashlib
import urlparse

class fetch(Processor):
    """url --> fetched-content
    http user-agent with crude caching.
    """

    def cache_key(self, url):
        u=urlparse.urlparse(url)
        # xx aggressive normalization for dev. take this in ctor.
        return u.netloc+u.path

    def rgen(self, nxt=None):
        """ url --> content
        """

        cache_root=self.opts.get('cache_dir')
        if cache_root and not os.path.exists(cache_root):
            print >>sys.stderr, 'need cache dir', cache_root
            sys.exit(1)
        niceness=float(self.opts.get('niceness', 10))

        last_fetched=None

        while True:
            url=(yield)
            data=None

            if cache_root:
                cache_entry=os.path.join(cache_root, 
                                         hashlib.md5(self.cache_key(url)).hexdigest())
                if os.path.exists(cache_entry):
                    data=file(cache_entry).read()
                    assert data
                    print >>sys.stderr, 'fetched-cached:', url

            if data is None:
                now=time.time()
                if last_fetched:
                    elapsed=now-last_fetched
                    short=niceness-elapsed
                    if short>0:
                        print >>sys.stderr, 'being nice', short
                        time.sleep(short)
                last_fetched=now

                try:
                    data=urllib2.urlopen(url).read()
                except (urllib2.HTTPError,urllib2.URLError), e:
                    print >>sys.stderr, 'fetch-error:', e, url
                    data=None
                    # xx do negative cache
                    #    in fact, save the entire http txn

                if data and cache_root:
                    file(cache_entry, 'w').write(data)
                    print >>sys.stderr, 'fetched:', url

            # xxx url should be sent to the next phase..
            send(nxt, data)

class vals(Processor):
    """initial segment that kicks off the processing with a list of data
    pipline=h.vals([url]) >> ...
    """

    def __init__(self, vs):
        self.vals=vs
        super(vals, self).__init__()

    def rgen(self, nxt=None):

        # just to make this a rgen.
        # I need a cue to get started.
        cue=(yield)

        for v in self.vals:
            send(nxt,v)

        # may be send a sentinel value to signal EOF

class jq(Processor):
    """call out to jq command for json processing.
    command line args to jq should be passed to the ctor.
    >> hose.jq('-M', '-r', '.users[] | .profile.url')
    This requires the 'sh' python module and command 'jq' to be in path.
    see http://stedolan.github.io/jq/download/
    """

    def rgen(self, nxt=None):
        """json --> jsons"""

        import sh

        while True:
            indata=(yield)
            if indata is None:
                continue
            print >>sys.stderr, 'jq:', self.args, indata[:10]
            output=sh.jq(*self.args,_in=indata)
            for line in output.split('\n'):
                if line:
                    send(nxt, line)

class fmt(Processor):
    """python string formatting segment
    """

    def rgen(self, nxt=None):
        while True:
            data=(yield)
            # dwimmy type-dispatch. xx may be this should be made explicit in ctor.
            if isinstance(data, (list,tuple)):
                outdata=self.args[0].format(*data)
            elif isinstance(data, dict):
                outdata=self.args[0].format(**data)
            else: # scalar assumed. format-str should just contain {0}
                outdata=self.args[0].format(data)
            #print >>sys.stderr, 'fmt:', self.args[0], [data]
            send(nxt, outdata)

def ints(n=0):
    while True:
        yield n
        n+=1

class head(Processor):
    """like head(1)"""
    def rgen(self, nxt=None):
        limit=self.args[0]
        for i in ints():
            if i>=limit:
                break
            data=(yield)
            send(nxt, data)

import collections

class hist(Processor):
    """histogram: sort | uniq -c | sort -nr"""
    # must suck in all data, sinc this is a reduce on unsorted input..
    # but how do i suck in all the data, then do something?
    # is there an end-of-input exception?
    def rgen(self, nxt=None):
        self.opts['histo']=collections.defaultdict(int)
        self.opts['nxt']=nxt
        while True:
            data=(yield)
            self.opts['histo'][data]+=1

    def flush(self):
        for item in sorted(self.opts['histo'].items(), 
                           key=lambda item_cnt: item_cnt[1], 
                           reverse=True):
            send(self.opts['nxt'], item)

class catch(Processor):
    """Segment that captures the stream into a list. Sort of like tee(1)

    * usage:

      output=(... >> h.catch()).run()

      or 

      bucket=[]
      ... >> h.catch(bucket) >> ...
      for caught in bucket:
          ...
    """

    def rgen(self, nxt=None):

        if not self.args:
            bucket=[]
            self.args=[bucket]

        while True:
            data=(yield)
            self.args[0].append(data)
            send(nxt, data)

    def output(self):
        return self.args[0]

class out(Processor):
    """terminal segment to print data stream to stdout"""

    def rgen(self, nxt=None):

        while True:
            data=(yield)
            if not data:
                continue
            print data
            if nxt:          # tee to another optional segment
                send(nxt,data)
