from mercurial import ui, config

def make_ui(path='hgwebdir.config'):        
    """
    A funciotn that will read python rc files and make an ui from read options
    
    @param path: path to mercurial config file
    """
    #propagated from mercurial documentation
    sections = [
                'alias',
                'auth',
                'decode/encode',
                'defaults',
                'diff',
                'email',
                'extensions',
                'format',
                'merge-patterns',
                'merge-tools',
                'hooks',
                'http_proxy',
                'smtp',
                'patch',
                'paths',
                'profiling',
                'server',
                'trusted',
                'ui',
                'web',
                ]

    repos = path
    baseui = ui.ui()
    cfg = config.config()
    cfg.read(repos)
    paths = cfg.items('paths')

    for section in sections:
        for k, v in cfg.items(section):
            baseui.setconfig(section, k, v)
    
    return baseui
