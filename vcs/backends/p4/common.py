import abc
import logging
import subprocess
import marshal

import re

import vcs.exceptions

logger = logging.getLogger(__name__)


class P4(object):
    __metaclass__ = abc.ABCMeta

    def __init__(self, user, passwd, port, client, env=None):
        self.user = user
        self.client = passwd
        self.port = port
        self.client = client
        self.env = env

    @abc.abstractmethod
    def run(self, args, input=None):
        """

        :param args:
        :param input:
        :return:
        """
        pass


class SubprocessP4(P4):
    """A command-line based P4 class.

    Based on using 'p4 -G ...', which returns marshaled
    python dictionaries as its output values, together with a 'code' key which may be 'stat', 'error', or 'info'.
    The normal return case is 'stat'. Some fixup is required for things like array value results.
    """
    ARRAY_KEY = re.compile(r'(\w+?)(\d+)$')
    INT = re.compile(r'\d+$')

    def run(self, args, input=None, env=None):
        logger.debug('Going to run p4 command %s', str(args))
        stdin_mode = subprocess.PIPE if input is not None else None

        p = subprocess.Popen(['p4', '-G'] + map(str, args), stdin=stdin_mode, stdout=subprocess.PIPE,
                             env=env or self.env)

        if input is not None:
            input = SubprocessP4.encode_arrays(input)
            marshal.dump(input, p.stdin, 0)  # must specify version 0; http://kb.perforce.com/article/585/using-p4-g
            p.stdin.close()

        result = []

        while True:
            try:
                h = marshal.load(p.stdout)
                if not isinstance(h, dict):
                    raise vcs.exceptions.CommandError('Command %r produced unmarshalled object of the wrong type: %r',
                                    (['p4', '-G'] + map(str, args), h))
                result.append(h)
            except EOFError:
                break

        return SubprocessP4.post_process(result, args)

    @staticmethod
    def post_process(result, args):
        def append(l, v):
            l.append(v)

        def process_dict(h):
            code = h.get('code', None)
            if code == 'error':
                name = 'Error' if h['severity'] == 3 else 'Warning'
                raise vcs.exceptions.CommandError('%ss during command execution( "p4 -G %s" )\n\n\t[%s]: %s\n' %
                                                  (name, ' '.join(map(str, args)), name, h['data']))
            elif code == 'info':
                return h['data'], append
            elif code == 'text':
                # Mimic behavior of 'diff',
                # e.g.: Result is a dict of clientFIle, depotFile, rev, text, then lines.
                return h['data'], lambda l, v: l.extend(v.splitlines())
            elif code and code != 'stat':
                raise vcs.exceptions.CommandError('ERROR: %r => %r' % (args, h))  # never happens
            if code:
                del h['code']

            SubprocessP4.decode_arrays(h)
            return h, append

        a = []
        for value, fn in map(process_dict, result):
            fn(a, value)
        return a

    @staticmethod
    def encode_arrays(h):
        if not isinstance(h, dict):
            return h
        keys_with_lists = [(key, value) for key, value in h.items()
                         if isinstance(value, (list, tuple))]
        if not keys_with_lists:
            return h
        for key, valueList in keys_with_lists:
            for i, value in enumerate(valueList):
                indexed_key = '%s%d' % (key, i)
                assert indexed_key not in h, 'Key %r already present in pre-marshaled dict: %r' % (indexed_key, h)
                h[indexed_key] = value
            del h[key]
        return h

    @staticmethod
    def decode_arrays(h):
        """If there is an array of values, e.g. the result of [ p4 -G describe CHANGELIST ], then they are returned
        as key0: value0, key1: value1, etc. Convert these to key: [value0, value1, ...]."""
        keys_and_indices = [(m.group(1), int(m.group(2))) for key, m in
                          [(key, SubprocessP4.ARRAY_KEY.match(key)) for key in h.keys()]
                          if m]
        if not keys_and_indices:
            return h
        key_range = {}
        for key, index in keys_and_indices:
            index_range = key_range.setdefault(key, [None, None])
            index_range[0] = index if index_range[0] is None else min(index_range[0], index)
            index_range[1] = index if index_range[1] is None else max(index_range[1], index)
        for key, index_range in key_range.items():
            # Handle otherOpen, otherChange, otherLock
            if re.match(r'other[A-Z][a-z]*[a-rt-z]$', key):
                plural_key = key + 's'
                # fix special case (fstat)
                # n.b.: sometimes the key value is '' instead of the array length (bug in p4???)
                if key in h and plural_key not in h and (SubprocessP4.INT.match(h[key]) or h[key] == ''):
                    h[plural_key] = h[key]
                    del h[key]
            assert key not in h, 'Key %r already present in unmarshaled dict: %r' % (key, h)
            a = []
            for i in range(index_range[1]+1):
                indexed_key = '%s%d' % (key, i)
                if indexed_key in h:
                    a.append(h[indexed_key])
                    del h[indexed_key]
                else:
                    a.append(None)  # n.b.: if zeroth entry is missing, p4 puts a None in
            h[key] = a
        return h
