import argparse

class VCSArgumentParser(argparse.ArgumentParser):
    """
    VCS argument parser used by command line script.
    """

    def __init__(self, scm=None, repo_path=None, *args, **kwargs):
        self.scm = scm
        self.repo_path = repo_path
        return super(VCSArgumentParser, self).__init__(*args, **kwargs)

    def parse_args(self, *args, **kwargs):
        args = super(VCSArgumentParser, self).parse_args(*args, **kwargs)
        args.scm = self.scm
        args.repo_path = self.repo_path
        return args

