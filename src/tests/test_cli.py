import os
import io
import unittest
import unittest.mock as mock
from src import cli

def _parser_from_dict(d, add_site=True):
    p = cli.MDTFArgParser()
    p_config = cli.CLIParser.from_dict(d)
    p_config.configure(p)
    if add_site:
        p.add_argument('--site', default='local')
    return p

class TestCanonicalArgName(unittest.TestCase):
    def test_canonical_arg_name(self):
        self.assertEqual(cli.canonical_arg_name('--flag '), 'flag')
        self.assertEqual(cli.canonical_arg_name('--flag-two '), 'flag_two')
        self.assertEqual(cli.canonical_arg_name('-flag-three_3'), 'flag_three_3')

class TestWordWrap(unittest.TestCase):
    def tearDown(self):
        # clear contents of Singleton
        try:
            c = cli.CLIConfigManager()
            c._reset()
        except:
            pass

    def test_word_wrap(self):
        str1 = """
            Here's a multiline test string; we'll test to see
            if the indentation is removed
            and if it
            gets word wrapped to 80 columns, etc.
        """
        str2 = ("Here's a multiline test string; we'll test to see if the "
            "indentation is removed\nand if it gets word wrapped to 80 columns, etc.")
        self.assertEqual(cli.word_wrap(str1), str2)

    def test_word_wrap_multipara(self):
        str1 = """
            Here's a multiline test string; we'll test to see
            if the indentation is removed
            and if it

            gets word wrapped to 80 columns, etc.
            \n\nExplicit para break
        """
        str2 = ("Here's a multiline test string; we'll test to see if the "
            "indentation is removed\nand if it\n\ngets word wrapped to 80 columns,"
            " etc.\n\nExplicit para break")
        self.assertEqual(cli.word_wrap(str1), str2)

class TestMDTFArgParserBasic(unittest.TestCase):
    def tearDown(self):
        # clear contents of Singleton
        try:
            c = cli.CLIConfigManager()
            c._reset()
        except:
            pass

    def test_flag_aliases(self):
        p = _parser_from_dict({
            "arguments": [{"name": "multi_word_flag", "short_name": "f"}]})
        x = p.parse_args('-f bar')
        self.assertEqual(x.multi_word_flag, "bar")
        x = p.parse_args('--multi_word_flag bar')
        self.assertEqual(x.multi_word_flag, "bar")
        x = p.parse_args('--multi-word-flag bar')
        self.assertEqual(x.multi_word_flag, "bar")

    def test_flag_synonyms(self):
        p = _parser_from_dict({
            "arguments": [{"name": ["flag", "multi_word_flag"], "short_name": "f"}]})
        x = p.parse_args('-f bar')
        self.assertEqual(x.flag, "bar")
        x = p.parse_args('--flag bar')
        self.assertEqual(x.flag, "bar")
        x = p.parse_args('--multi_word_flag bar')
        self.assertEqual(x.flag, "bar")
        x = p.parse_args('--multi-word-flag bar')
        self.assertEqual(x.flag, "bar")

    def test_iter_actions(self):
        p = _parser_from_dict({
            "arguments": [{"name": "foo"}, {"name": "foo_2"}]})
        dests = [a.dest for a in p.iter_actions()]
        self.assertCountEqual(dests, ['foo', 'foo_2', 'site'])


class TestMDTFArgParserHelpFormat(unittest.TestCase):
    def tearDown(self):
        # clear contents of Singleton
        try:
            c = cli.CLIConfigManager()
            c._reset()
        except:
            pass

    def test_formatting(self):
        p = _parser_from_dict({
            "usage": 'foo',
            "description": """long multiline description text, although strictly
                speaking we covered this in TestWordWrap, but why not test it
                again
            """,
            "arguments": [{
                "name": "foo",
                "help": "foo help",
                "metavar": "<foo metavar>",
                "default": "bar"}],
            "epilog": 'baz'
        }, add_site=False)
        str2 = ('usage: foo\n\nlong multiline description text, although strictly speaking we '
            'covered this in\nTestWordWrap, but why not test it again\n\nCOMMAND OPTIONS:\n  -h,'
            ' --help\n      show this help message and exit\n  --foo <foo metavar>\n      foo '
            "help (default: 'bar')\n\nbaz\n")
        str_ = io.StringIO()
        p.print_help(str_)
        self.assertEqual(str_.getvalue(), str2)

    def test_formatting_groups(self):
        p = _parser_from_dict({
            "usage": 'foo',
            "description": "bar",
            "arguments": [{
                "name": "arg1", "help": "arg1 help", "metavar": "<arg1 metavar>",
            },{
                "name": "hidden arg", "help": "hidden help", "hidden": True
            }],
            "argument_groups": [{
                "title" : "GROUP1",
                "description" : "group1 desc",
                "arguments":[{
                    "name": "arg2", "help": "arg2 help", "metavar": "<arg2 metavar>",
                }]
            },{
                "title" : "GROUP2",
                "description" : "group2 desc",
                "arguments":[{
                    "name": "arg3", "help": "arg3 help", "metavar": "<arg3 metavar>",
                }]
            }],
            "epilog": 'baz'
        }, add_site=False)
        str2 = ('usage: foo\n\nbar\n\nCOMMAND OPTIONS:\n  -h, --help\n      show this'
            ' help message and exit\n  --arg1 <arg1 metavar>\n      arg1 help'
            '\n\nGROUP1:\n  group1 desc\n\n  --arg2 <arg2 metavar>\n      arg2 '
            'help\n\nGROUP2:\n  group2 desc\n\n  --arg3 <arg3 metavar>\n'
            '      arg3 help\n\nbaz\n')
        str_ = io.StringIO()
        p.print_help(str_)
        self.assertEqual(str_.getvalue(), str2)


class TestMDTFArgParserRecordDefaults(unittest.TestCase):
    def tearDown(self):
        # clear contents of Singleton
        try:
            c = cli.CLIConfigManager()
            c._reset()
        except:
            pass

    def test_string_defaults(self):
        p = _parser_from_dict({"arguments": [{"name": "foo", "default": "bar"}]})
        x = p.parse_args('')
        self.assertEqual(x.foo, "bar")
        self.assertTrue(p.is_default['foo'])
        x = p.parse_args('--foo bar')
        self.assertEqual(x.foo, "bar")
        self.assertFalse(p.is_default['foo'])
        x = p.parse_args('--foo baz')
        self.assertEqual(x.foo, "baz")
        self.assertFalse(p.is_default['foo'])

    def test_bool_defaults_true(self):
        p = _parser_from_dict({"arguments": [{"name": "foo", "default": True}]})
        x = p.parse_args('')
        self.assertTrue(x.foo)
        self.assertTrue(p.is_default['foo'])
        x = p.parse_args('--foo')
        self.assertFalse(x.foo)
        self.assertFalse(p.is_default['foo'])

    def test_bool_defaults_false(self):
        p = _parser_from_dict({"arguments": [{"name": "foo", "default": False}]})
        x = p.parse_args('')
        self.assertFalse(x.foo)
        self.assertTrue(p.is_default['foo'])
        x = p.parse_args('--foo')
        self.assertTrue(x.foo)
        self.assertFalse(p.is_default['foo'])


class TestCLIConfigManager(unittest.TestCase):
    def setUp(self):
        _ = cli.CLIConfigManager('dummy/test/path', skip_defaults=True)

    def tearDown(self):
        # clear contents of Singleton
        try:
            c = cli.CLIConfigManager()
            c._reset()
        except:
            pass

    def _setup_parser(self):
        return _parser_from_dict({
            "arguments": [
                {"name": "foo"},
                {"name": "foo2", "default": "bar"}
            ],
        })
    def test_no_partial_def(self):
        c = cli.CLIConfigManager()
        p = self._setup_parser()
        config = vars(p.parse_args('--foo baz'))
        self.assertDictEqual(config, {'foo':'baz', 'foo2': 'bar', 'site': 'local'})
        config = vars(p.parse_args('--foo2 baz'))
        self.assertDictEqual(config, {'foo':None, 'foo2': 'baz','site':'local'})

    def test_partial_def_1(self):
        c = cli.CLIConfigManager()

        c.user_defaults = {'foo': 'XX', 'foo2': 'YY'}
        p = self._setup_parser()
        config = vars(p.parse_args('--foo baz'))
        self.assertDictEqual(config, {'foo':'baz', 'foo2': 'YY','site':'local'})

        c.user_defaults = {'foo': 'XX'}
        p = self._setup_parser()
        config = vars(p.parse_args('--foo baz'))
        self.assertDictEqual(config, {'foo':'baz', 'foo2': 'bar','site':'local'})

        c.user_defaults = {'foo2': 'YY'}
        p = self._setup_parser()
        config = vars(p.parse_args('--foo baz'))
        self.assertDictEqual(config, {'foo':'baz', 'foo2': 'YY','site':'local'})

    def test_partial_def_2(self):
        c = cli.CLIConfigManager()

        c.site_defaults = {'foo': 'XX'}
        p = self._setup_parser()
        config = vars(p.parse_args('--foo baz'))
        self.assertDictEqual(config, {'foo':'baz', 'foo2': 'bar','site':'local'})

        c.site_defaults = {'foo': 'XX', 'foo2': 'YY'}
        p = self._setup_parser()
        config = vars(p.parse_args('--foo2 baz'))
        self.assertDictEqual(config, {'foo':'XX', 'foo2': 'baz','site':'local'})

        c.site_defaults = {'foo': 'XX'}
        p = self._setup_parser()
        config = vars(p.parse_args('--foo2 baz'))
        self.assertDictEqual(config, {'foo':'XX', 'foo2': 'baz','site':'local'})

        c.site_defaults = {'foo2': 'YY'}
        p = self._setup_parser()
        config = vars(p.parse_args('--foo2 baz'))
        self.assertDictEqual(config, {'foo':None, 'foo2': 'baz','site':'local'})

    def test_partial_def_3(self):
        c = cli.CLIConfigManager()

        c.user_defaults = {'foo': 'XX', 'foo2': 'YY'}
        c.site_defaults = {'foo': 'XXQ', 'foo2': 'YYQ'}
        p = self._setup_parser()
        config = vars(p.parse_args('--foo baz'))
        self.assertDictEqual(config, {'foo':'baz', 'foo2': 'YY','site':'local'})

        c.user_defaults = {'foo': 'XX', 'foo2': 'YY'}
        c.site_defaults = {'foo': 'XXQ', 'foo2': 'YYQ'}
        p = self._setup_parser()
        config = vars(p.parse_args('--foo2 baz'))
        self.assertDictEqual(config, {'foo':'XX', 'foo2': 'baz','site':'local'})

        c.user_defaults = {'foo': 'XX'}
        c.site_defaults = {'foo': 'XXQ', 'foo2': 'YYQ'}
        p = self._setup_parser()
        config = vars(p.parse_args('--foo baz'))
        self.assertDictEqual(config, {'foo':'baz', 'foo2': 'YYQ','site':'local'})

        c.user_defaults = {'foo2': 'YY'}
        c.site_defaults = {'foo': 'XXQ', 'foo2': 'YYQ'}
        p = self._setup_parser()
        config = vars(p.parse_args('--foo2 baz'))
        self.assertDictEqual(config, {'foo':'XXQ', 'foo2': 'baz','site':'local'})

class TestParseDummyInput(unittest.TestCase):
    def tearDown(self):
        try:
            temp = cli.CLIConfigManager()
            temp._reset()
        except Exception:
            pass

    def test_parse_dummy_input(self):
        # get dir of currently executing script:
        cwd = os.path.dirname(os.path.realpath(__file__))
        code_root = os.path.dirname(os.path.dirname(cwd))
        cli_obj = cli.MDTFTopLevelArgParser(
            code_root,
            skip_defaults=True,
            argv= f"-f {os.path.join(cwd, 'dummy_config.json')}"
        )
        config = vars(cli_obj.parse_args())
        self.assertEqual(config["OBS_DATA_ROOT"], "/DUMMY/PATH/OBS_DATA_ROOT")
        self.assertEqual(config["MODEL_DATA_ROOT"], "/DUMMY/PATH/MODEL_DATA_ROOT")
        self.assertEqual(config["WORKING_DIR"], "/DUMMY/PATH/WORKING_DIR")
        self.assertEqual(config["OUTPUT_DIR"], "/DUMMY/PATH/OUTPUT_DIR")
