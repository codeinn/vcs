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
from mercurial.util import matchdate, Abort

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
    mr = MercurialRepository('/home/marcink/python_workspace/lotto/')
    print mr.repo.changectx('tip')
    print mr.get_name()        
        
