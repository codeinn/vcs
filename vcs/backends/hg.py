#!/usr/bin/env python
# encoding: utf-8
#
# Copyright (c) 2010 Marcin Kuzminski,Lukasz Balcerzak.  All rights reserved.
#
"""
Created on Apr 8, 2010

@author: marcink,lukaszb
"""
from base import BaseRepository
from mercurial import ui
from mercurial.localrepo import localrepository
from mercurial.util import matchdate, Abort, makedate
import os
from mercurial import hg
from mercurial.error import RepoError
from mercurial.hgweb.hgwebdir_mod import findrepos 

def get_repositories(repos_prefix, repos_path):
    """
    Listing of repositories in given path. This path should not be a repository
    itself. Return a list of repository objects
    @param repos_path: path to directory it could take syntax with * or ** for
    deep recursive displaying repositories
    """
    if not repos_path.endswith('*') and not repos_path.endswith('*'):
        raise Exception('You need to specify * or ** for recursive scanning')
        
    check_repo_dir(repos_path)
    if is_mercurial_repo(repos_path):
        pass
    repos = findrepos([(repos_prefix, repos_path)])
    
    my_ui = ui.ui()
    my_ui.setconfig('ui', 'report_untrusted', 'off')
    my_ui.setconfig('ui', 'interactive', 'off')
            
    for name, path in repos:
        u = my_ui.copy()

        try:
            u.readconfig(os.path.join(path, '.hg', 'hgrc'))
        except Exception, e:
            u.warn('error reading %s/.hg/hgrc: %s\n') % (path, e)
            continue
                
        def get(section, name, default=None):
            return u.config(section, name, default, untrusted=True)
        
        def get_mtime(spath):
            cl_path = os.path.join(spath, "00changelog.i")
            if os.path.exists(cl_path):
                return os.stat(cl_path).st_mtime
            else:
                return os.stat(spath).st_mtime   
        
        #skip hidden repo    
        if u.configbool("web", "hidden", untrusted=True):
            continue
        
        #skip not allowed
#       if not self.read_allowed(u, req):
#           continue        
        
        try:
            r = localrepository(my_ui, path)
            last_change = (get_mtime(r.spath), makedate()[1])
        except OSError:
            continue            
     
        print 'name', name ,
        print 'desc', get('web', 'description', 'mercurial repo'),
        print 'time', last_change,
        tip = r.changectx('tip')
        print 'tip', tip,
        print '@rev', tip.rev()
        print 'last commit by', tip.user()
        print
    

def check_repo_dir(path):
    """
    Checks the repository
    @param path:
    """
    repos_path = path.split('/')
    if repos_path[-1] in ['*', '**']:
        repos_path = repos_path[:-1]
    if repos_path[0] != '/':
        repos_path[0] = '/'
    if not os.path.isdir(os.path.join(*repos_path)):
        raise Exception('Not a valid repository in %s' % path[0][1])

def is_mercurial_repo(path):
    path = path.replace('*', '')
    try:
        hg.repository(ui.ui(), path)
        return True
    except (RepoError):
        return False

class MercurialRepository(BaseRepository):
    """
    Mercurial repository backend
    """

    def __init__(self, repo_path, **kwargs):
        baseui = ui.ui()
        self.repo = localrepository(baseui, path=repo_path)
        """
        Constructor
        """
        
    def get_name(self):
        return self.repo.path.split('/')[-2]

#TEST
if __name__ == "__main__":
    
    get_repositories('/', '/home/marcink/python_workspace/*')        
