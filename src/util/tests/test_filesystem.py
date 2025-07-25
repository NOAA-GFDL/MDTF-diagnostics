import json
import textwrap
import unittest
import unittest.mock as mock
from src.util import filesystem as util
from src.util import exceptions


class TestCheckDirs(unittest.TestCase):
    @mock.patch('os.path.isdir', return_value=True)
    @mock.patch('os.makedirs')
    def test_check_dirs_found(self, mock_makedirs, mock_isdir):
        # exit function normally if all directories found
        try:
            util.check_dir('DUMMY/PATH/NAME', create=False)
            util.check_dir('DUMMY/PATH/NAME', create=True)
        except (Exception, SystemExit):
            self.fail()
        mock_makedirs.assert_not_called()

    @mock.patch('os.path.isdir', return_value=False)
    @mock.patch('os.makedirs')
    def test_check_dirs_not_found(self, mock_makedirs, mock_isdir):
        # try to exit() if any directories not found
        with self.assertRaises(exceptions.MDTFFileNotFoundError):
            util.check_dir('DUMMY/PATH/NAME', create=False)
        mock_makedirs.assert_not_called()

    @mock.patch('os.path.isdir', return_value=False)
    @mock.patch('os.makedirs')
    def test_check_dirs_not_found_created(self, mock_makedirs, mock_isdir):
        # don't exit() and call os.makedirs if in create_if_nec
        try:
            util.check_dir('DUMMY/PATH/NAME', create=True)
        except (Exception, SystemExit):
            self.fail()
        mock_makedirs.assert_called_once_with('DUMMY/PATH/NAME', exist_ok=False)


class TestBumpVersion(unittest.TestCase):
    @mock.patch('os.path.exists', return_value=False)
    def test_bump_version_noexist(self, mock_exists):
        for f in [
            'AAA', 'AAA.v1', 'D/C/B/AAA', 'D/C/B/AAAA/', 'D/C/B/AAA.v23',
            'D/C/B/AAAA.v23/', 'A.foo', 'A.v23.foo', 'A.v23.bar.v45.foo',
            'D/C/A.foo', 'D/C/A.v23.foo', 'D/C/A.v23.bar.v45.foo'
        ]:
            f2, _ = util.bump_version(f)
            self.assertEqual(f, f2)

    @mock.patch('os.path.exists', return_value=False)
    def test_bump_version_getver(self, mock_exists):
        for f in [
            'AAA.v42', 'D/C/B/AAA.v42', 'D/C.v7/B/AAAA.v42/', 'A.v42.foo',
            'A.v23.bar.v42.foo', 'D/C/A.v42.foo', 'D/C/A.v23.bar.v42.foo'
        ]:
            _, ver = util.bump_version(f)
            self.assertEqual(ver, 42)

    @mock.patch('os.path.exists', return_value=False)
    def test_bump_version_delver(self, mock_exists):
        for f in [
            ('AAA', 'AAA'), ('AAA.v1', 'AAA'), ('D/C/B/AA', 'D/C/B/AA'),
            ('D/C.v1/B/AA/', 'D/C.v1/B/AA/'), ('D/C/B/AA.v23', 'D/C/B/AA'),
            ('D/C3/B.v8/AA.v23/', 'D/C3/B.v8/AA/'), ('A.foo', 'A.foo'),
            ('A.v23.foo', 'A.foo'), ('A.v23.bar.v45.foo', 'A.v23.bar.foo'),
            ('D/C/A.foo', 'D/C/A.foo'), ('D/C.v1/A234.v3.foo', 'D/C.v1/A234.foo'),
            ('D/C/A.v23.bar.v45.foo', 'D/C/A.v23.bar.foo')
        ]:
            f1, ver = util.bump_version(f[0], new_v=0)
            self.assertEqual(f1, f[1])
            self.assertEqual(ver, 0)

    @mock.patch('os.path.exists', return_value=False)
    def test_bump_version_setver(self, mock_exists):
        for f in [
            ('AAA', 'AAA.v42'), ('AAA.v1', 'AAA.v42'), ('D/C/B/AA', 'D/C/B/AA.v42'),
            ('D/C.v1/B/AA/', 'D/C.v1/B/AA.v42/'), ('D/C/B/AA.v23', 'D/C/B/AA.v42'),
            ('D/C3/B.v8/AA.v23/', 'D/C3/B.v8/AA.v42/'), ('A.foo', 'A.v42.foo'),
            ('A.v23.foo', 'A.v42.foo'), ('A.v23.bar.v45.foo', 'A.v23.bar.v42.foo'),
            ('D/C/A.foo', 'D/C/A.v42.foo'), ('D/C.v1/A.v23.foo', 'D/C.v1/A.v42.foo'),
            ('D/C/A.v23.bar.v45.foo', 'D/C/A.v23.bar.v42.foo')
        ]:
            f1, ver = util.bump_version(f[0], new_v=42)
            self.assertEqual(f1, f[1])
            self.assertEqual(ver, 42)

    # following tests both get caught in an infinite loop

    # @mock.patch('os.path.exists', side_effect=itertools.cycle([True,False]))
    # def test_bump_version_dirs(self, mock_exists):
    #     for f in [
    #         ('AAA','AAA.v1',1), ('AAA.v1','AAA.v2',2), ('D/C/B/AA','D/C/B/AA.v1',1),
    #         ('D/C.v1/B/AA/','D/C.v1/B/AA.v1/',1), ('D/C/B/AA.v23','D/C/B/AA.v24',24),
    #         ('D/C3/B.v8/AA.v9/','D/C3/B.v8/AA.v10/',10)
    #     ]:
    #         f1, ver = util.bump_version(f[0])
    #         self.assertEqual(f1, f[1])
    #         self.assertEqual(ver, f[2])

    # @mock.patch('os.path.exists', side_effect=itertools.cycle([True,False]))
    # def test_bump_version_files(self, mock_exists):
    #     for f in [
    #         ('A.foo','A.v1.foo',1), ('A.v23.foo','A.v24.foo',24),
    #         ('A.v23.bar.v45.foo','A.v23.bar.v46.foo',46),
    #         ('D/C/A.foo','D/C/A.v1.foo',1),
    #         ('D/C.v1/A.v99.foo','D/C.v1/A.v100.foo', 100),
    #         ('D/C/A.v23.bar.v78.foo','D/C/A.v23.bar.v79.foo', 79)
    #     ]:
    #         f1, ver = util.bump_version(f[0])
    #         self.assertEqual(f1, f[1])
    #         self.assertEqual(ver, f[2])


class TestJSONC(unittest.TestCase):
    def test_parse_json_basic(self):
        s = """{
            "a" : "test_string",
            "b" : 3,
            "c" : false,
            "d" : [1,2,3],
            "e" : {
                "aa" : [4,5,6],
                "bb" : true
            }
        }
        """
        d = util.parse_json(s)
        self.assertEqual(set(d.keys()), {'a', 'b', 'c', 'd', 'e'})
        self.assertEqual(d['a'], "test_string")
        self.assertEqual(d['b'], 3)
        self.assertEqual(d['c'], False)
        self.assertEqual(len(d['d']), 3)
        self.assertEqual(d['d'], [1, 2, 3])
        self.assertEqual(set(d['e'].keys()), {'aa', 'bb'})
        self.assertEqual(len(d['e']['aa']), 3)
        self.assertEqual(d['e']['aa'], [4, 5, 6])
        self.assertEqual(d['e']['bb'], True)

    def test_parse_json_comments(self):
        s = """
        // comment 1
        // comment 1.1 // comment 1.2 // comment 1.3

        { // comment 1.5
            // comment 2
            "a" : 1, // comment 3

            "b // c" : "// d x ////", // comment 4
            "e" : false,
            // comment 5 "quotes in a comment"
            "f": "ff" // comment 6 " unbalanced quote in a comment
        } // comment 7

        """
        d = util.parse_json(s)
        self.assertEqual(set(d.keys()), {'a', 'b // c', 'e', 'f'})
        self.assertEqual(d['a'], 1)
        self.assertEqual(d['b // c'], "// d x ////")
        self.assertEqual(d['e'], False)
        self.assertEqual(d['f'], "ff")

    def test_parse_json_syntax_lineno(self):
        s = 'SYNTAX_ERROR\n{"a": 1, "e": false}'
        try:
            flag = False
            _ = util.parse_json(textwrap.dedent(s))
        except json.JSONDecodeError as exc:
            flag = True
            self.assertEqual(exc.lineno, 1)
            self.assertEqual(exc.colno, 1)
        self.assertTrue(flag)

        s = '{"a"  :  1  "e"  : false  }'
        # missing ',' triggers on first " in "e"
        try:
            flag = False
            _ = util.parse_json(textwrap.dedent(s))
        except json.JSONDecodeError as exc:
            flag = True
            self.assertEqual(exc.lineno, 1)
            self.assertEqual(exc.colno, 13)
        self.assertTrue(flag)

        s = '//COMMENT\n{"a"  :  1  "e"  : false  }'
        # missing ',' triggers on first " in "e"
        try:
            flag = False
            _ = util.parse_json(textwrap.dedent(s))
        except json.JSONDecodeError as exc:
            flag = True
            self.assertEqual(exc.lineno, 2)
            self.assertEqual(exc.colno, 13)
        self.assertTrue(flag)

        s = """        // comment 1

        { // comment 1.5
            // comment 2
            "a" : 1, // comment 6 " unbalanced quote in a comment
            "e" : false
        } // comment 7

        SYNTAX_ERROR
        """
        try:
            flag = False
            _ = util.parse_json(textwrap.dedent(s))
        except json.JSONDecodeError as exc:
            flag = True
            self.assertEqual(exc.lineno, 9)
            self.assertEqual(exc.colno, 1)
        self.assertTrue(flag)

        s = """        // comment 1

        { // comment 1.5
            // comment 2
            "a" : 1 // comment 3
            "e" : false
        } // comment 7
        """
        # missing ',' triggers on first " in "e"
        try:
            flag = False
            _ = util.parse_json(textwrap.dedent(s))
        except json.JSONDecodeError as exc:
            flag = True
            self.assertEqual(exc.lineno, 6)
            self.assertEqual(exc.colno, 5)
        self.assertTrue(flag)

    def test_strip_comments_quote_escape(self):
        str_ = '"foo": "bar\\\"ba//z\\\""'
        self.assertEqual(
            util.strip_comments(str_, delimiter='//'),
            ('"foo": "bar\\"ba//z\\""', [0])
        )
        str_ = '"foo": "bar\\\"ba//z\\\"" //comment \\\" '
        self.assertEqual(
            util.strip_comments(str_, delimiter='//'),
            ('"foo": "bar\\"ba//z\\"" ', [0])
        )
        # old code breaks on this case - unbalanced
        str_ = '"foo": bar\\\"ba//z\\\""'
        self.assertEqual(
            util.strip_comments(str_, delimiter='//'),
            ('"foo": bar\\"ba', [0])
        )


class TestDoubleBraceTemplate(unittest.TestCase):
    def sub(self, template_text, template_dict=dict()):
        tmp = util._DoubleBraceTemplate(template_text)
        return tmp.safe_substitute(template_dict)

    def test_escaped_brace_1(self):
        self.assertEqual(self.sub('{{{{'), '{{')

    def test_escaped_brace_2(self):
        self.assertEqual(self.sub("\nfoo\t bar{{{{baz\n\n"), "\nfoo\t bar{{baz\n\n")

    def test_replace_1(self):
        self.assertEqual(self.sub("{{foo}}", {'foo': 'bar'}), "bar")

    def test_replace_2(self):
        self.assertEqual(
            self.sub("asdf\t{{\t foo \n\t }}baz", {'foo': 'bar'}),
            "asdf\tbarbaz"
        )

    def test_replace_3(self):
        self.assertEqual(
            self.sub(
                "{{FOO}}\n{{  foo }}asdf\t{{\t FOO \n\t }}baz_{{foo}}",
                {'foo': 'bar', 'FOO': 'BAR'}
            ),
            "BAR\nbarasdf\tBARbaz_bar"
        )

    def test_replace_4(self):
        self.assertEqual(
            self.sub(
                "]{ {{_F00}}\n{{  f00 }}as{ { }\n.d'f\t{{\t _F00 \n\t }}ba} {[z_{{f00}}",
                {'f00': 'bar', '_F00': 'BAR'}
            ),
            "]{ BAR\nbaras{ { }\n.d'f\tBARba} {[z_bar"
        )

    def test_ignore_1(self):
        self.assertEqual(self.sub("{{goo}}", {'foo': 'bar'}), "{{goo}}")

    def test_ignore_2(self):
        self.assertEqual(
            self.sub("asdf\t{{\t goo \n\t }}baz", {'foo': 'bar'}),
            "asdf\t{{\t goo \n\t }}baz"
        )

    def test_ignore_3(self):
        self.assertEqual(
            self.sub(
                "{{FOO}}\n{{  goo }}asdf\t{{\t FOO \n\t }}baz_{{goo}}",
                {'foo': 'bar', 'FOO': 'BAR'}
            ),
            "BAR\n{{  goo }}asdf\tBARbaz_{{goo}}"
        )

    def test_nomatch_1(self):
        self.assertEqual(self.sub("{{foo", {'foo': 'bar'}), "{{foo")

    def test_nomatch_2(self):
        self.assertEqual(
            self.sub("asdf\t{{\t foo \n\t }baz", {'foo': 'bar'}),
            "asdf\t{{\t foo \n\t }baz"
        )

    def test_nomatch_3(self):
        self.assertEqual(
            self.sub(
                "{{FOO\n{{  foo }asdf}}\t{{\t FOO \n\t }}baz_{{foo}}",
                {'foo': 'bar', 'FOO': 'BAR'}
            ),
            "{{FOO\n{{  foo }asdf}}\tBARbaz_bar"
        )


# ---------------------------------------------------

if __name__ == '__main__':
    unittest.main()
