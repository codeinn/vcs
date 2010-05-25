import unittest

from vcs.backends.git import GitRepository, GitChangeset
from vcs.exceptions import ChangesetError, RepositoryError
from vcs.nodes import NodeKind, NodeState

from conf import TEST_GIT_REPO

class GitRepositoryTest(unittest.TestCase):

    def setUp(self):
        self.repo = GitRepository(TEST_GIT_REPO)

    def test_repo_create(self):
        wrong_repo_path = '/tmp/errorrepo'
        self.assertRaises(RepositoryError, GitRepository, wrong_repo_path)

    def test_revisions(self):
        # there are 112 revisions (by now)
        # so we can assume they would be available from now on
        subset = set([
            'c1214f7e79e02fc37156ff215cd71275450cffc3',
            '38b5fe81f109cb111f549bfe9bb6b267e10bc557',
            'fa6600f6848800641328adbf7811fd2372c02ab2',
            '102607b09cdd60e2793929c4f90478be29f85a17',
            '49d3fd156b6f7db46313fac355dca1a0b94a0017',
            '2d1028c054665b962fa3d307adfc923ddd528038',
            'd7e0d30fbcae12c90680eb095a4f5f02505ce501',
            'ff7ca51e58c505fec0dd2491de52c622bb7a806b',
            'dd80b0f6cf5052f17cc738c2951c4f2070200d7f',
            '8430a588b43b5d6da365400117c89400326e7992',
            'd955cd312c17b02143c04fa1099a352b04368118',
            'f67b87e5c629c2ee0ba58f85197e423ff28d735b',
            'add63e382e4aabc9e1afdc4bdc24506c269b7618',
            'f298fe1189f1b69779a4423f40b48edf92a703fc',
            'bd9b619eb41994cac43d67cf4ccc8399c1125808',
            '6e125e7c890379446e98980d8ed60fba87d0f6d1',
            'd4a54db9f745dfeba6933bf5b1e79e15d0af20bd',
            '0b05e4ed56c802098dfc813cbe779b2f49e92500',
            '191caa5b2c81ed17c0794bf7bb9958f4dcb0b87e',
            '45223f8f114c64bf4d6f853e3c35a369a6305520',
            'ca1eb7957a54bce53b12d1a51b13452f95bc7c7e',
            'f5ea29fc42ef67a2a5a7aecff10e1566699acd68',
            '27d48942240f5b91dfda77accd2caac94708cc7d',
            '622f0eb0bafd619d2560c26f80f09e3b0b0d78af',
            '6970b057cffe4aab0a792aa634c89f4bebf01441',
            '3effb567c46375ba5e79642b77597960cf14207a',
            'b8d04012574729d2c29886e53b1a43ef16dd00a1',
            'ee6e9e865abf98a211c18cdf0bc870e71561bd5e',
            '34f4dd6dd285b533e6af23f794d63603e862f613',
            'b24000830360dcc991c1c386746ea3d9502c8812',
            '3bf1c5868e570e39569d094f922d33ced2fa3b2b',
            '7cde603b3e25ab8aca02ce5a8c0e615a70ba2413',
            '16fba1ae9334d79b66d7afed2c2dfbfa2ae53647',
            '37ab4dcf7129f1fa42ad3cb8632ebde5c2f45512',
            '60d8fac3945431215c12eff9585e677c38aeaf0f',
            'b2a6fe970ba5a2a980002a767135e5f7221541e3',
            '4abd4511350ecba09ddfae62517f5e05c1eacf06',
            '992f38217b979d0b0987d0bae3cc26dac85d9b19',
            '54dc388e8894007281d69aca0a8636b6091eadb1',
            '9b92f28befbd812524916b80605648d693faff00',
            '0f44a27d74475289858f949f6707407924014215',
            '1a62d681f09adaa6eb749d160b6cea3573afa2e8',
            '09815fd7da7d9c6271ac324ab8386251acab64c4',
            '6bfb7f77815e33f7c5db056cbefe3e1c3e3632cd',
            'd98aad4eef5340f1eec9303d44b784a48700c4be',
            '78c3f0c23b7ee935ec276acb8b8212444c33c396',
            '2a13f185e4525f9d4b59882791a2d397b90d5ddc',
            '7cb3fd1b6d8c20ba89e2264f1c8baebc8a52d36e',
            '0115510b70c7229dbc5dc49036b32e7d91d23acd',
            '0d60560b5e2be9209a75d111392981e836e21609',
            '84dec09632a4458f79f50ddbbd155506c460b4f9',
            'f33df1642f3b47f3df231bd06248f76c0cf8e591',
            '5b1e247d27069756e9c6374f9cc957173e6d33cd',
            '2353f2c469a6e3f5e84e2983d91402782a280a5d',
            'd2c9e813d6ac53ab07cf5faf901142906c45aa98',
            '2a5a4ff2582b848b2524225be4060651321db859',
            'ea2b108b48aa8f8c9c4a941f66c1a03315ca1c3b',
            'e906ef056cf539a4e4e5fc8003eaf7cf14dd8ade',
            'f15c21f97864b4f071cddfbf2750ec2e23859414',
            'd7e390a45f6aa96f04f5e7f583ad4f867431aa25',
            'f50f42baeed5af6518ef4b0cb2f1423f3851a941',
            '5eab1222a7cd4bfcbabc218ca6d04276d4e27378',
            '00bed32e40694f7a11e0f9135257a0e18c05cd1b',
            '7a012af5c7db64becf660dd6769c58f3aa06a16d',
            '7606439c12098c548f6267d6f6a638080228afd7',
            '96dc0ccc685af658d103e2cffe2491cf638740d2',
            '4b211a7813e9d4e0d8ea8d78b605cb5ab72b8908',
            '5eff8174118fd00850128e06a1b11e28703adb29',
            'b147a51495f1ca1a74bdc8f10814d07d3290b176',
            '5e0eb4c47f56564395f76333f319d26c79e2fb09',
            '444859687dd8f0f122eb436ee12790b0f19fb908',
            '1206d0ca5ffd48a321e9827bcff2b8506e99d903',
            'becf684fc06890679f4c0cdfed1761962e16a343',
            '12f2f5e2b38e6ff3fbdb5d722efed9aa72ecb0d5',
            '1e878f0b4f51a1c538fe0ecd2bbfcc4eb324a5b8',
            'cbc77ef056ab3714d378726bebd4def0c5b53b3c',
            '5a0c84f3e6fe3473e4c8427199d5a6fc71a9b382',
            '998ed409c795fec2012b1c0ca054d99888b22090',
            'f5bcd209c6e48e48d910136c3ff1262ed866644a',
            '2c652d1d94e5b5d7dd8197e14f8b84d11f2ac004',
            'e47835a356f32de1b019c05143a7b51ae6ba1920',
            '12669288fd13adba2a9b7dd5b870cc23ffab92d2',
            'ac71e9503c2ca95542839af0ce7b64011b72ea7c',
            '15ca85941b8122bd81b38c129f33c71ace01a16e',
            '95c37bb6ce39db8dcfb07b856f4aac383e50c8a1',
            'e6ea6d16e2f26250124a1f4b4fe37a912f9d86a0',
            '97cb029936e3eedb603d129c5a7bc1941e2f8485',
            '7d5abb5c07f2e2772d8ad299d03c25597be36e0c',
            '221b29fb9d210748a72ab40ff00998817eaa1f68',
            '51d254f0ecf5df2ce50c0b115741f4cf13985dab',
            'c2c7e4f89961d275ec79db98b31f744b76e74e5e',
            '30c26513ff1eb8e5ce0e1c6b477ee5dc50e2f34b',
            '2a08b128c206db48c2f0b8f70df060e6db0ae4f8',
            '2d03ca750a44440fb5ea8b751176d1f36f8e8f46',
            '7bdb913b1fe04979acc3a0c817be749cb000c73b',
            '54f4f0e4f35988b369c1f191c64683b4b4beb508',
            'ca28fc8ac7b83c5e257a5a7bcf9a0d9ace715739',
            '2361d3e7895a3fe6ed2068ccf5fef8bab8165c11',
            'e518ec89dc4335eecbb3661c449f0b017236ee0c',
            '1c6b3677b37ea064cb4b51714d8f7498f93f4b2b',
            'd4a16d0ce723203e14d393dfda751ac00582b6d0',
            '54000345d2e78b03a99d561399e8e548de3f3203',
            '54386793436c938cff89326944d4c2702340037d',
            '110842664173a81fc26964f3a37fa8f7a7c6a007',
            '6c2303a793671e807d1cfc70134c9ca0767d98c2',
            '905ae5660afb289591ce5d7b0589246d030e35d2',
            'f11e3a503682d8fbebb6fc40c46e1b5dad94c777',
            '4313566d2e417cb382948f8d9d7c765330356054',
            'c877b68d18e792a66b7f4c529ea02c8f80801542',
            'ab5721ca0a081f26bf43d9051e615af2cc99952f',
            '5d866a766c146f45068688f8f72582285aebf38b',
            'e686b958768ee96af8029fe19c6050b1a8dd3b2b'])
        self.assertTrue(subset.issubset(set(self.repo.revisions)))

    def test_branches(self):
        hex = '998ed409c795fec2012b1c0ca054d99888b22090'
        chset = self.repo.get_changeset(hex)
        self.assertEqual(chset.branch, 'master')

        hex = 'e686b958768ee96af8029fe19c6050b1a8dd3b2b'
        chset = self.repo.get_changeset(hex)
        self.assertEqual(chset.branch, 'gittree')

    def test_tags(self):
        tip = self.repo.get_changeset()
        self.assertTrue(tip in self.repo.tags)

class GitChangesetTest(unittest.TestCase):

    def setUp(self):
        self.repo = GitRepository(TEST_GIT_REPO)

    def _test_equality(self, changeset):
        revision = changeset.revision
        self.assertEqual(changeset, self.repo.changesets[revision])

    def test_equality(self):
        revs = self.repo.revisions
        changesets = [self.repo.get_changeset(rev) for rev in revs]
        for changeset in changesets:
            self._test_equality(changeset)

    def test_default_changeset(self):
        tip = self.repo.get_changeset()
        self.assertEqual(tip, self.repo.get_changeset(None))
        self.assertEqual(tip, self.repo.get_changeset('tip'))
        self.assertEqual(tip, list(self.repo.get_changesets(limit=1))[0])

    def test_root_node(self):
        tip = self.repo.get_changeset()
        self.assertTrue(tip.root is tip.get_node(''))

    def test_lazy_fetch(self):
        """
        Test if changeset's nodes expands and are cached as we walk through
        the revision. This test is somewhat hard to write as order of tests
        is a key here. Written by running command after command in a shell.
        """
        hex = '2a13f185e4525f9d4b59882791a2d397b90d5ddc'
        self.assertTrue(hex in self.repo.revisions)
        chset = self.repo.get_changeset(hex)
        self.assertTrue(len(chset.nodes) == 0)
        root = chset.root
        self.assertTrue(len(chset.nodes) == 1)
        self.assertTrue(len(root.nodes) == 8)
        # accessing root.nodes updates chset.nodes
        self.assertTrue(len(chset.nodes) == 9)

        docs = root.get_node('docs')
        # we haven't yet accessed anything new as docs dir was already cached
        self.assertTrue(len(chset.nodes) == 9)
        self.assertTrue(len(docs.nodes) == 8)
        # accessing docs.nodes updates chset.nodes
        self.assertTrue(len(chset.nodes) == 17)

        self.assertTrue(docs is chset.get_node('docs'))
        self.assertTrue(docs is root.nodes[0])
        self.assertTrue(docs is root.dirs[0])
        self.assertTrue(docs is chset.get_node('docs'))

    def test_nodes_with_changeset(self):
        hex = '2a13f185e4525f9d4b59882791a2d397b90d5ddc'
        chset = self.repo.get_changeset(hex)
        root = chset.root
        docs = root.get_node('docs')
        self.assertTrue(docs is chset.get_node('docs'))
        api = docs.get_node('api')
        self.assertTrue(api is chset.get_node('docs/api'))
        index = api.get_node('index.rst')
        self.assertTrue(index is chset.get_node('docs/api/index.rst'))
        self.assertTrue(index is chset.get_node('docs')\
            .get_node('api')\
            .get_node('index.rst'))

    def _test_file_size(self, revision, path, size):
        node = self.repo.request(path, revision)
        self.assertTrue(node.is_file())
        self.assertEqual(node.size, size)

    def test_file_size(self):
        to_check = (
            ('c1214f7e79e02fc37156ff215cd71275450cffc3',
                'vcs/backends/BaseRepository.py', 502),
            ('d7e0d30fbcae12c90680eb095a4f5f02505ce501',
                'vcs/backends/hg.py', 854),
            ('6e125e7c890379446e98980d8ed60fba87d0f6d1',
                'setup.py', 1068),

            ('d955cd312c17b02143c04fa1099a352b04368118',
                'vcs/backends/base.py', 2921),
            ('ca1eb7957a54bce53b12d1a51b13452f95bc7c7e',
                'vcs/backends/base.py', 3936),
            ('f50f42baeed5af6518ef4b0cb2f1423f3851a941',
                'vcs/backends/base.py', 6189),
        )
        for revision, path, size in to_check:
            self._test_file_size(revision, path, size)

if __name__ == '__main__':
    unittest.main()

