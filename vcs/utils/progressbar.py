# encoding: UTF-8
import sys
import datetime


class ProgressBarError(Exception):
    pass

class AlreadyFinishedError(ProgressBarError):
    pass


class ProgressBar(object):

    default_elements = ['percentage', 'bar', 'steps']

    def __init__(self, steps=100, stream=None, elements=None):
        self.step = 0
        self.steps = steps
        self.stream = stream or sys.stderr
        self.bar_char = '=' 
        self.width = 50
        self.separator = ' | '
        self.elements = elements or self.default_elements
        self.started = None
        self.finished = False
        self.steps_label = 'Step'
        self.time_label = 'Time'
        self.eta_label = 'ETA'

    def __str__(self):
        return self.get_line()

    def __iter__(self):
        start = self.step
        end = self.steps + 1
        for x in xrange(start, end):
            self.render(x)
            yield x

    def get_separator(self):
        return self.separator

    def get_bar_char(self):
        return self.bar_char

    def get_bar(self):
        char = self.get_bar_char()
        perc = self.get_percentage()
        length = int(self.width * perc / 100)
        bar = char * length
        bar = bar.ljust(self.width)
        return bar

    def get_elements(self):
        return self.elements

    def get_template(self):
        separator = self.get_separator()
        elements = self.get_elements()
        return separator.join((('{%s}' % e) for e in elements))

    def get_total_time(self, current_time=None):
        if current_time is None:
            current_time = datetime.datetime.now()
        if not self.started:
            return datetime.timedelta()
        return current_time - self.started

    def get_rendered_total_time(self):
        delta = self.get_total_time()
        if not delta:
            ttime = '-'
        else:
            ttime = str(delta)
        return '{}: {}'.format(self.time_label, ttime)

    def get_eta(self, current_time=None):
        if current_time is None:
            current_time = datetime.datetime.now()
        if self.step == 0:
            return datetime.timedelta()
        total_seconds = self.get_total_time().total_seconds()
        eta_seconds = total_seconds * self.steps / self.step - total_seconds
        return datetime.timedelta(seconds=int(eta_seconds))

    def get_rendered_eta(self):
        eta = self.get_eta()
        if not eta:
            eta = '--:--:--'
        else:
            eta = str(eta).rjust(8)
        return '{}: {}'.format(self.eta_label, eta)

    def get_percentage(self):
        return float(self.step) / self.steps * 100

    def get_rendered_percentage(self):
        perc = self.get_percentage()
        return '{val}%'.format(val=int(perc)).rjust(5)

    def get_rendered_steps(self):
        return '{}: {}/{}'.format(self.steps_label, self.step, self.steps)

    def get_context(self):
        return {
            'percentage': self.get_rendered_percentage(),
            'bar': self.get_bar(),
            'steps': self.get_rendered_steps(),
            'time': self.get_rendered_total_time(),
            'eta': self.get_rendered_eta(),
        }

    def get_line(self):
        template = self.get_template()
        context = self.get_context()
        return template.format(**context)

    def write(self, data):
        self.stream.write(data)

    def render(self, step):
        if not self.started:
            self.started = datetime.datetime.now()
        if self.finished:
            raise AlreadyFinishedError
        self.step = step
        self.write('\r%s' % self)
        if step == self.steps:
            self.finished = True
        if step == self.steps:
            self.write('\n')


"""
termcolors.py

Grabbed from Django (http://www.djangoproject.com)
"""

color_names = ('black', 'red', 'green', 'yellow', 'blue', 'magenta', 'cyan', 'white')
foreground = dict([(color_names[x], '3%s' % x) for x in range(8)])
background = dict([(color_names[x], '4%s' % x) for x in range(8)])

RESET = '0'
opt_dict = {'bold': '1', 'underscore': '4', 'blink': '5', 'reverse': '7', 'conceal': '8'}

def colorize(text='', opts=(), **kwargs):
    """
    Returns your text, enclosed in ANSI graphics codes.

    Depends on the keyword arguments 'fg' and 'bg', and the contents of
    the opts tuple/list.

    Returns the RESET code if no parameters are given.

    Valid colors:
        'black', 'red', 'green', 'yellow', 'blue', 'magenta', 'cyan', 'white'

    Valid options:
        'bold'
        'underscore'
        'blink'
        'reverse'
        'conceal'
        'noreset' - string will not be auto-terminated with the RESET code

    Examples:
        colorize('hello', fg='red', bg='blue', opts=('blink',))
        colorize()
        colorize('goodbye', opts=('underscore',))
        print colorize('first line', fg='red', opts=('noreset',))
        print 'this should be red too'
        print colorize('and so should this')
        print 'this should not be red'
    """
    code_list = []
    if text == '' and len(opts) == 1 and opts[0] == 'reset':
        return '\x1b[%sm' % RESET
    for k, v in kwargs.iteritems():
        if k == 'fg':
            code_list.append(foreground[v])
        elif k == 'bg':
            code_list.append(background[v])
    for o in opts:
        if o in opt_dict:
            code_list.append(opt_dict[o])
    if 'noreset' not in opts:
        text = text + '\x1b[%sm' % RESET
    return ('\x1b[%sm' % ';'.join(code_list)) + text

def make_style(opts=(), **kwargs):
    """
    Returns a function with default parameters for colorize()

    Example:
        bold_red = make_style(opts=('bold',), fg='red')
        print bold_red('hello')
        KEYWORD = make_style(fg='yellow')
        COMMENT = make_style(fg='blue', opts=('bold',))
    """
    return lambda text: colorize(text, opts, **kwargs)

NOCOLOR_PALETTE = 'nocolor'
DARK_PALETTE = 'dark'
LIGHT_PALETTE = 'light'

PALETTES = {
    NOCOLOR_PALETTE: {
        'ERROR':        {},
        'NOTICE':       {},
        'SQL_FIELD':    {},
        'SQL_COLTYPE':  {},
        'SQL_KEYWORD':  {},
        'SQL_TABLE':    {},
        'HTTP_INFO':         {},
        'HTTP_SUCCESS':      {},
        'HTTP_REDIRECT':     {},
        'HTTP_NOT_MODIFIED': {},
        'HTTP_BAD_REQUEST':  {},
        'HTTP_NOT_FOUND':    {},
        'HTTP_SERVER_ERROR': {},
    },
    DARK_PALETTE: {
        'ERROR':        { 'fg': 'red', 'opts': ('bold',) },
        'NOTICE':       { 'fg': 'red' },
        'SQL_FIELD':    { 'fg': 'green', 'opts': ('bold',) },
        'SQL_COLTYPE':  { 'fg': 'green' },
        'SQL_KEYWORD':  { 'fg': 'yellow' },
        'SQL_TABLE':    { 'opts': ('bold',) },
        'HTTP_INFO':         { 'opts': ('bold',) },
        'HTTP_SUCCESS':      { },
        'HTTP_REDIRECT':     { 'fg': 'green' },
        'HTTP_NOT_MODIFIED': { 'fg': 'cyan' },
        'HTTP_BAD_REQUEST':  { 'fg': 'red', 'opts': ('bold',) },
        'HTTP_NOT_FOUND':    { 'fg': 'yellow' },
        'HTTP_SERVER_ERROR': { 'fg': 'magenta', 'opts': ('bold',) },
    },
    LIGHT_PALETTE: {
        'ERROR':        { 'fg': 'red', 'opts': ('bold',) },
        'NOTICE':       { 'fg': 'red' },
        'SQL_FIELD':    { 'fg': 'green', 'opts': ('bold',) },
        'SQL_COLTYPE':  { 'fg': 'green' },
        'SQL_KEYWORD':  { 'fg': 'blue' },
        'SQL_TABLE':    { 'opts': ('bold',) },
        'HTTP_INFO':         { 'opts': ('bold',) },
        'HTTP_SUCCESS':      { },
        'HTTP_REDIRECT':     { 'fg': 'green', 'opts': ('bold',) },
        'HTTP_NOT_MODIFIED': { 'fg': 'green' },
        'HTTP_BAD_REQUEST':  { 'fg': 'red', 'opts': ('bold',) },
        'HTTP_NOT_FOUND':    { 'fg': 'red' },
        'HTTP_SERVER_ERROR': { 'fg': 'magenta', 'opts': ('bold',) },
    }
}
DEFAULT_PALETTE = DARK_PALETTE

def parse_color_setting(config_string):
    """Parse a DJANGO_COLORS environment variable to produce the system palette

    The general form of a pallete definition is:

        "palette;role=fg;role=fg/bg;role=fg,option,option;role=fg/bg,option,option"

    where:
        palette is a named palette; one of 'light', 'dark', or 'nocolor'.
        role is a named style used by Django
        fg is a background color.
        bg is a background color.
        option is a display options.

    Specifying a named palette is the same as manually specifying the individual
    definitions for each role. Any individual definitions following the pallete
    definition will augment the base palette definition.

    Valid roles:
        'error', 'notice', 'sql_field', 'sql_coltype', 'sql_keyword', 'sql_table',
        'http_info', 'http_success', 'http_redirect', 'http_bad_request',
        'http_not_found', 'http_server_error'

    Valid colors:
        'black', 'red', 'green', 'yellow', 'blue', 'magenta', 'cyan', 'white'

    Valid options:
        'bold', 'underscore', 'blink', 'reverse', 'conceal'

    """
    if not config_string:
        return PALETTES[DEFAULT_PALETTE]

    # Split the color configuration into parts
    parts = config_string.lower().split(';')
    palette = PALETTES[NOCOLOR_PALETTE].copy()
    for part in parts:
        if part in PALETTES:
            # A default palette has been specified
            palette.update(PALETTES[part])
        elif '=' in part:
            # Process a palette defining string
            definition = {}

            # Break the definition into the role,
            # plus the list of specific instructions.
            # The role must be in upper case
            role, instructions = part.split('=')
            role = role.upper()

            styles = instructions.split(',')
            styles.reverse()

            # The first instruction can contain a slash
            # to break apart fg/bg.
            colors = styles.pop().split('/')
            colors.reverse()
            fg = colors.pop()
            if fg in color_names:
                definition['fg'] = fg
            if colors and colors[-1] in color_names:
                definition['bg'] = colors[-1]

            # All remaining instructions are options
            opts = tuple(s for s in styles if s in opt_dict.keys())
            if opts:
                definition['opts'] = opts

            # The nocolor palette has all available roles.
            # Use that palette as the basis for determining
            # if the role is valid.
            if role in PALETTES[NOCOLOR_PALETTE] and definition:
                palette[role] = definition

    # If there are no colors specified, return the empty palette.
    if palette == PALETTES[NOCOLOR_PALETTE]:
        return None
    return palette

# ---------------------------- #
# --- End of termcolors.py --- #
# ---------------------------- #


class ColoredProgressBar(ProgressBar):

    BAR_COLORS = (
        (10, 'red'),
        (30, 'magenta'),
        (50, 'yellow'),
        (99, 'green'),
        (100, 'blue'),
    )

    def get_line(self):
        line = super(ColoredProgressBar, self).get_line()
        perc = self.get_percentage()
        if perc > 100:
            color = 'blue'
        for max_perc, color in self.BAR_COLORS:
            if perc <= max_perc:
                break
        return colorize(line, fg=color)


class AnimatedProgressBar(ProgressBar):

    def get_bar_char(self):
        chars = '-/|\\'
        if self.step >= self.steps:
            return '='
        return chars[self.step % len(chars)]


class BarOnlyProgressBar(ProgressBar):

    default_elements = ['bar', 'steps']

    def get_bar(self):
        bar = super(BarOnlyProgressBar, self).get_bar()
        perc = self.get_percentage()
        perc_text = '{}%'.format(int(perc))
        text = ' {}% '.format(perc_text).center(self.width, '=')
        L = text.find(' ')
        R = text.rfind(' ')
        bar = ' '.join((bar[:L], perc_text, bar[R:]))
        return bar


class AnimatedColoredProgressBar(AnimatedProgressBar,
                                 ColoredProgressBar):
    pass


class BarOnlyColoredProgressBar(ColoredProgressBar,
                                BarOnlyProgressBar):
    pass


import unittest


class TestProgressBar(unittest.TestCase):

    def test_default_get_separator(self):
        bar = ProgressBar()
        bar.separator = '\t'
        self.assertEquals(bar.get_separator(), '\t')

    def test_cast_to_str(self):
        bar = ProgressBar()
        self.assertEquals(str(bar), bar.get_line())

    def test_default_get_bar_char(self):
        bar = ProgressBar()
        bar.bar_char = '#'
        self.assertEquals(bar.get_bar_char(), '#')

    def test_default_get_elements(self):
        bar = ProgressBar(elements=['foo', 'bar'])
        self.assertItemsEqual(bar.get_elements(), ['foo', 'bar'])

    def test_get_template(self):
        bar = ProgressBar()
        bar.elements = ['foo', 'bar']
        bar.separator = ' '
        self.assertEquals(bar.get_template(), '{foo} {bar}')

    def test_default_stream_is_sys_stderr(self):
        bar = ProgressBar()
        self.assertEquals(bar.stream, sys.stderr)

    def test_get_percentage(self):
        bar = ProgressBar()
        bar.steps = 120
        bar.step = 60
        self.assertEquals(bar.get_percentage(), 50.0)
        bar.steps = 100
        bar.step = 9
        self.assertEquals(bar.get_percentage(), 9.0)

    def test_get_rendered_percentage(self):
        bar = ProgressBar()
        bar.steps = 100
        bar.step = 10.5
        self.assertEquals(bar.get_percentage(), 10.5)

    def test_bar_width(self):
        bar = ProgressBar()
        bar.width = 30
        self.assertEquals(len(bar.get_bar()), 30)

    def test_write(self):
        from StringIO import StringIO
        stream = StringIO()
        bar = ProgressBar()
        bar.stream = stream
        bar.write('foobar')
        self.assertEquals(stream.getvalue(), 'foobar')

    def test_change_stream(self):
        from StringIO import StringIO
        stream1 = StringIO()
        stream2 = StringIO()
        bar = ProgressBar()
        bar.stream = stream1
        bar.write('foo')
        bar.stream = stream2
        bar.write('bar')
        self.assertEquals(stream2.getvalue(), 'bar')

    def test_render_writes_new_line_at_last_step(self):
        from StringIO import StringIO
        bar = ProgressBar()
        bar.stream = StringIO()
        bar.steps = 5
        bar.render(5)
        self.assertEquals(bar.stream.getvalue()[-1], '\n')

    def test_initial_step_is_zero(self):
        bar = ProgressBar()
        self.assertEquals(bar.step, 0)

    def test_iter_starts_from_current_step(self):
        from StringIO import StringIO
        bar = ProgressBar()
        bar.stream = StringIO()
        bar.steps = 20
        bar.step = 5
        stepped = list(bar)
        self.assertEquals(stepped[0], 5)

    def test_iter_ends_at_last_step(self):
        from StringIO import StringIO
        bar = ProgressBar()
        bar.stream = StringIO()
        bar.steps = 20
        bar.step = 5
        stepped = list(bar)
        self.assertEquals(stepped[-1], 20)

    def test_get_total_time(self):
        bar = ProgressBar()
        now = datetime.datetime.now()
        bar.started = now - datetime.timedelta(days=1)
        self.assertEqual(bar.get_total_time(now), datetime.timedelta(days=1))

    def test_get_total_time_returns_empty_timedelta_if_not_yet_started(self):
        bar = ProgressBar()
        self.assertEquals(bar.get_total_time(), datetime.timedelta())

    def test_get_render_total_time(self):
        p = ProgressBar()
        p.time_label = 'FOOBAR'
        self.assertTrue(p.get_rendered_total_time().startswith('FOOBAR'))

    def test_get_eta(self):
        from StringIO import StringIO
        bar = ProgressBar(100)
        bar.stream = StringIO()

        bar.render(50)
        now = datetime.datetime.now()
        delta = now - bar.started
        self.assertEquals(bar.get_eta(now).total_seconds(),
            int(delta.total_seconds() * 0.5))

        bar.render(75)
        now = datetime.datetime.now()
        delta = now - bar.started
        self.assertEquals(bar.get_eta(now).total_seconds(),
            int(delta.total_seconds() * 0.25))

    def test_get_rendered_eta(self):
        bar = ProgressBar(100)
        bar.eta_label = 'foobar'
        self.assertTrue(bar.get_rendered_eta().startswith('foobar'))

    def test_get_rendered_steps(self):
        bar = ProgressBar(100)
        bar.steps_label = 'foobar'
        self.assertTrue(bar.get_rendered_steps().startswith('foobar'))

    def test_context(self):
        bar = ProgressBar()
        context = bar.get_context()
        self.assertItemsEqual(context, [
            'bar',
            'percentage',
            'time',
            'eta',
            'steps',
        ])

    def test_context_has_correct_bar(self):
        bar = ProgressBar()
        context = bar.get_context()
        self.assertEquals(context['bar'], bar.get_bar())

    def test_context_has_correct_percentage(self):
        bar = ProgressBar(100)
        bar.step = 50
        percentage = bar.get_context()['percentage']
        self.assertEquals(percentage, bar.get_rendered_percentage())

    def test_context_has_correct_total_time(self):
        bar = ProgressBar(100)
        time = bar.get_context()['time']
        self.assertEquals(time, bar.get_rendered_total_time())

    def test_context_has_correct_eta(self):
        bar = ProgressBar(100)
        eta = bar.get_context()['eta']
        self.assertEquals(eta, bar.get_rendered_eta())

    def test_context_has_correct_steps(self):
        bar = ProgressBar(100)
        steps = bar.get_context()['steps']
        self.assertEquals(steps, bar.get_rendered_steps())

    def test_render_raises_error_if_bar_already_finished(self):
        from StringIO import StringIO
        bar = ProgressBar(10)
        bar.stream = StringIO()
        bar.render(10)

        with self.assertRaises(AlreadyFinishedError):
            bar.render(0)

        
def main():
    import time

    print "Standard progress bar..."
    bar = ProgressBar(30)
    for x in xrange(1, 31):
            bar.render(x)
            time.sleep(0.02)
    bar.stream.write('\n')
    print

    print "Empty bar..."
    bar = ProgressBar(50)
    bar.render(0)
    print
    print

    print "Colored bar..."
    bar = ColoredProgressBar(20)
    for x in bar:
        time.sleep(0.01)
    print

    print "Animated char bar..."
    bar = AnimatedProgressBar(20)
    for x in bar:
        time.sleep(0.01)
    print

    print "Animated + colored char bar..."
    bar = AnimatedColoredProgressBar(20)
    for x in bar:
        time.sleep(0.01)
    print

    print "Bar only ..."
    bar = BarOnlyProgressBar(20)
    for x in bar:
        time.sleep(0.01)
    print

    print "Colored, longer bar-only, eta, total time, breaks in the middle ..."
    bar = BarOnlyColoredProgressBar(40)
    bar.width = 60
    bar.elements += ['time', 'eta']
    for x in bar:
        time.sleep(0.1)
    print
    print


if __name__ == '__main__':
    main()
    unittest.main()

