import io
import unittest
import unittest.mock as mock
from framework import cli

class TestWordWrap(unittest.TestCase):
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
    def test_canonical_arg_name(self):
        self.assertEqual(cli.MDTFArgParser.canonical_arg_name('--flag '), 'flag')
        self.assertEqual(cli.MDTFArgParser.canonical_arg_name('--flag-two '), 'flag_two')
        self.assertEqual(cli.MDTFArgParser.canonical_arg_name('-flag-three_3'), 'flag_three_3')

    def test_flag_aliases(self):
        p = cli.MDTFArgParser()
        p.configure({"arguments": [{"name": "multi_word_flag", "short_name": "f"}]})
        x = p.parse_args('-f bar')
        self.assertEqual(x.multi_word_flag, "bar")
        x = p.parse_args('--multi_word_flag bar')
        self.assertEqual(x.multi_word_flag, "bar")
        x = p.parse_args('--multi-word-flag bar')
        self.assertEqual(x.multi_word_flag, "bar")

    def test_iter_actions(self):
        p = cli.MDTFArgParser()
        p.configure({"arguments": [{"name": "foo"}, {"name": "foo_2"}]})
        dests = [a.dest for a in p.iter_actions()]
        self.assertCountEqual(dests, ['foo', 'foo_2'])

    def test_iter_actions_group(self):
        p = cli.MDTFArgParser()
        p.configure({
            "arguments": [{"name": "foo"}, {"name": "foo_2"}],
            "argument_groups": [{
                "name" : "GROUP1",
                "arguments":[{"name": "arg2"}]
            },{
                "name" : "GROUP2",
                "arguments":[{"name": "arg3"}],
            }]
        })
        dests = [a.dest for a in p.iter_actions('GROUP1')]
        self.assertCountEqual(dests, ['arg2'])
        dests = [a.dest for a in p.iter_actions('parser')]
        self.assertCountEqual(dests, ['foo', 'foo_2'])


class TestMDTFArgParserHelpFormat(unittest.TestCase):
    def test_formatting(self):
        p = cli.MDTFArgParser()
        p.configure({
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
        })
        str2 = ('usage: foo\n\nlong multiline description text, although strictly speaking we '
            'covered this in\nTestWordWrap, but why not test it again\n\nCOMMAND OPTIONS:\n  -h,'
            ' --help\n      show this help message and exit\n  --foo <foo metavar>\n      foo '
            'help (default: bar)\n\nbaz\n')
        str_ = io.StringIO()
        p.print_help(str_)
        self.assertEqual(str_.getvalue(), str2)

    def test_formatting_groups(self):
        p = cli.MDTFArgParser()
        p.configure({
            "usage": 'foo',
            "description": "bar",
            "arguments": [{
                "name": "arg1", "help": "arg1 help", "metavar": "<arg1 metavar>",
            },{
                "name": "hidden arg", "help": "hidden help", "hidden": True
            }],
            "argument_groups": [{
                "name" : "GROUP1",
                "description" : "group1 desc",
                "arguments":[{
                    "name": "arg2", "help": "arg2 help", "metavar": "<arg2 metavar>",
                }]
            },{
                "name" : "GROUP2",
                "description" : "group2 desc",
                "arguments":[{
                    "name": "arg3", "help": "arg3 help", "metavar": "<arg3 metavar>",
                }]
            }],
            "epilog": 'baz'
        })
        str2 = ('usage: foo\n\nbar\n\nCOMMAND OPTIONS:\n  -h, --help\n      show this'
            ' help message and exit\n  --arg1 <arg1 metavar>\n      arg1 help (default:'
            ' None)\n\nGROUP1:\n  group1 desc\n\n  --arg2 <arg2 metavar>\n      arg2 '
            'help (default: None)\n\nGROUP2:\n  group2 desc\n\n  --arg3 <arg3 metavar>\n'
            '      arg3 help (default: None)\n\nbaz\n')
        str_ = io.StringIO()
        p.print_help(str_)
        self.assertEqual(str_.getvalue(), str2)


class TestMDTFArgParserRecordDefaults(unittest.TestCase):
    def test_string_defaults(self):
        p = cli.MDTFArgParser()
        p.configure({"arguments": [{"name": "foo", "default": "bar"}]})
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
        p = cli.MDTFArgParser()
        p.configure({"arguments": [{"name": "foo", "default": True}]})
        x = p.parse_args('')
        self.assertTrue(x.foo)
        self.assertTrue(p.is_default['foo'])
        x = p.parse_args('--foo')
        self.assertFalse(x.foo)
        self.assertFalse(p.is_default['foo'])

    def test_bool_defaults_false(self):
        p = cli.MDTFArgParser()
        p.configure({"arguments": [{"name": "foo", "default": False}]})
        x = p.parse_args('')
        self.assertFalse(x.foo)
        self.assertTrue(p.is_default['foo'])
        x = p.parse_args('--foo')
        self.assertTrue(x.foo)
        self.assertFalse(p.is_default['foo'])


class TestMDTFArgParserPositionals(unittest.TestCase):
    def test_dupe_dest(self):
        p = cli.MDTFArgParser()
        p.configure({
            "arguments": [{
                "name": "foo"
            },{
                "name": "CASE_ROOT_DIR", "is_positional": True, "nargs" : "?",
            },{
                "name": "CASE_ROOT_DIR", "type" : "str"
            }]
        })
        self.assertDictEqual(vars(p.parse_args('')), {'foo': None, 'CASE_ROOT_DIR': None})
        self.assertDictEqual(vars(p.parse_args('A')),
            {'foo': None, 'CASE_ROOT_DIR': 'A'})
        self.assertDictEqual(vars(p.parse_args('--foo X')),
            {'foo': 'X', 'CASE_ROOT_DIR': None})
        self.assertDictEqual(vars(p.parse_args('--foo X A')),
            {'foo': 'X', 'CASE_ROOT_DIR': 'A'})
        self.assertDictEqual(vars(p.parse_args('--CASE_ROOT_DIR B --foo X A')),
            {'foo': 'X', 'CASE_ROOT_DIR': 'A'})


class TestConfigManager(unittest.TestCase):
    def setUp(self):
        p = cli.MDTFArgParser()
        p.configure({
            "arguments": [
                {"name": "foo"},
                {"name": "foo2", "default": "bar"}
            ],
        })
        _ = cli.ConfigManager(parser=p)

    def tearDown(self):
        # clear contents of Singleton
        try:
            c = cli.ConfigManager()
            c._reset()
        except:
            pass

    def test_no_partial_def(self):
        c = cli.ConfigManager()
        c._p.parse_args('--foo baz')
        c.parse_with_defaults()
        self.assertDictEqual(c.config.toDict(), {'foo':'baz', 'foo2': 'bar'})
        c._p.parse_args('--foo2 baz')
        c.parse_with_defaults()
        self.assertDictEqual(c.config.toDict(), {'foo':None, 'foo2': 'baz'})

    def test_partial_def_1(self):
        c = cli.ConfigManager()
        c._p.parse_args('--foo baz')
        c._partial_defaults = {'foo': 'XX', 'foo2': 'YY'}
        c.parse_with_defaults()
        self.assertDictEqual(c.config.toDict(), {'foo':'baz', 'foo2': 'YY'})

        c._p.parse_args('--foo baz')
        c._partial_defaults = {'foo': 'XX'}
        c.parse_with_defaults()
        self.assertDictEqual(c.config.toDict(), {'foo':'baz', 'foo2': 'bar'})

        c._p.parse_args('--foo baz')
        c._partial_defaults = {'foo2': 'YY'}
        c.parse_with_defaults()
        self.assertDictEqual(c.config.toDict(), {'foo':'baz', 'foo2': 'YY'})

    def test_partial_def_2(self):
        c = cli.ConfigManager()
        c._p.parse_args('--foo2 baz')
        c._partial_defaults = {'foo': 'XX', 'foo2': 'YY'}
        c.parse_with_defaults()
        self.assertDictEqual(c.config.toDict(), {'foo':'XX', 'foo2': 'baz'})

        c._p.parse_args('--foo2 baz')
        c._partial_defaults = {'foo': 'XX'}
        c.parse_with_defaults()
        self.assertDictEqual(c.config.toDict(), {'foo':'XX', 'foo2': 'baz'})

        c._p.parse_args('--foo2 baz')
        c._partial_defaults = {'foo2': 'YY'}
        c.parse_with_defaults()
        self.assertDictEqual(c.config.toDict(), {'foo':None, 'foo2': 'baz'})
