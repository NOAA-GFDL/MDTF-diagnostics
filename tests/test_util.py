import os
import unittest
import mock # define mock os.environ so we don't mess up real env vars
import dataclasses
import typing
import src.util as util
import src.datelabel as dt # only used to construct one test instance

class TestSingleton(unittest.TestCase):
    def test_singleton(self):
        # Can only be instantiated once
        class Temp1(util.Singleton):
            def __init__(self):
                self.foo = 0
        temp1 = Temp1()
        temp2 = Temp1()
        temp1.foo = 5
        self.assertEqual(temp2.foo, 5)

    def test_singleton_reset(self):
        # Verify cleanup works
        class Temp2(util.Singleton):
            def __init__(self):
                self.foo = 0
        temp1 = Temp2()
        temp1.foo = 5
        temp1._reset()
        temp2 = Temp2()
        self.assertEqual(temp2.foo, 0)

class TestMultiMap(unittest.TestCase):
    def test_multimap_inverse(self):
        # test inverse map
        temp = util.MultiMap({'a':1, 'b':2})
        temp_inv = temp.inverse()
        self.assertIn(1, temp_inv)
        self.assertEqual(temp_inv[2], set(['b']))

    def test_multimap_setitem(self):
        # test key addition and handling of duplicate values
        temp = util.MultiMap({'a':1, 'b':2})
        temp['c'] = 1           
        temp_inv = temp.inverse()
        self.assertIn(1, temp_inv)
        self.assertCountEqual(temp_inv[1], set(['a','c']))
        temp['b'] = 3
        temp_inv = temp.inverse()
        self.assertNotIn(2, temp_inv)

    def test_multimap_delitem(self):
        # test item deletion
        temp = util.MultiMap({'a':1, 'b':2})
        del temp['b']
        temp_inv = temp.inverse()
        self.assertNotIn(2, temp_inv)

    def test_multimap_add(self):
        temp = util.MultiMap({'a':1, 'b':2, 'c':1})
        temp['a'].add(3)
        temp_inv = temp.inverse()
        self.assertIn(3, temp_inv)
        self.assertCountEqual(temp_inv[3], set(['a']))
        temp['a'].add(2)
        temp_inv = temp.inverse()
        self.assertIn(2, temp_inv)
        self.assertCountEqual(temp_inv[2], set(['a','b']))

    def test_multimap_add_new(self):
        temp = util.MultiMap({'a':1, 'b':2, 'c':1})
        temp['x'].add(2)
        temp_inv = temp.inverse()
        self.assertIn(2, temp_inv)
        self.assertCountEqual(temp_inv[2], set(['b','x']))

    def test_multimap_remove(self):
        temp = util.MultiMap({'a':1, 'b':2, 'c':1})
        temp['c'].add(2)
        temp['c'].remove(1)
        temp_inv = temp.inverse()
        self.assertIn(2, temp_inv)
        self.assertCountEqual(temp_inv[2], set(['b','c']))
        self.assertIn(1, temp_inv)
        self.assertCountEqual(temp_inv[1], set(['a']))

class TestNameSpace(unittest.TestCase):
    def test_namespace_basic(self):
        test = util.NameSpace(name='A', B='C')
        self.assertEqual(test.name, 'A')
        self.assertEqual(test.B, 'C')
        with self.assertRaises(AttributeError):
            _ = test.D
        test.B = 'D'
        self.assertEqual(test.B, 'D')

    def test_namespace_dict_ops(self):
        test = util.NameSpace(name='A', B='C')
        self.assertIn('B', test)
        self.assertNotIn('D', test)

    def test_namespace_tofrom_dict(self):
        test = util.NameSpace(name='A', B='C')
        test2 = test.toDict()
        self.assertEqual(test2['name'], 'A')
        self.assertEqual(test2['B'], 'C')
        test3 = util.NameSpace.fromDict(test2)
        self.assertEqual(test3.name, 'A')
        self.assertEqual(test3.B, 'C')

    def test_namespace_copy(self):
        test = util.NameSpace(name='A', B='C')
        test2 = test.copy()
        self.assertEqual(test2.name, 'A')
        self.assertEqual(test2.B, 'C')
        test2.B = 'D'
        self.assertEqual(test.B, 'C')
        self.assertEqual(test2.B, 'D')

    def test_namespace_hash(self):
        test = util.NameSpace(name='A', B='C')
        test2 = test
        test3 = test.copy()
        test4 = test.copy()
        test4.name = 'not_the_same'
        test5 = util.NameSpace(name='A', B='C')
        self.assertEqual(test, test2)
        self.assertEqual(test, test3)
        self.assertNotEqual(test, test4)
        self.assertEqual(test, test5)
        set_test = set([test, test2, test3, test4, test5])
        self.assertEqual(len(set_test), 2)
        self.assertIn(test, set_test)
        self.assertIn(test4, set_test)

class TestMDTFEnum(unittest.TestCase):
    def test_to_string(self):
        class Dummy(util.MDTFEnum):
            VALUE = ()
            ANOTHER_VALUE = ()
        self.assertEqual('value', str(Dummy.VALUE))
        self.assertEqual('another_value', str(Dummy.ANOTHER_VALUE))

    def test_from_string(self):
        class Dummy(util.MDTFEnum):
            VALUE = ()
            ANOTHER_VALUE = ()
        self.assertEqual(Dummy.from_struct('value'), Dummy.VALUE)
        self.assertEqual(Dummy.from_struct('another_value'), Dummy.ANOTHER_VALUE)

class TestMDTFDataclass(unittest.TestCase):
    def test_builtin_coerce(self):
        @util.mdtf_dataclass
        class Dummy(object):
            a: str = None
            b: int = None
            c: list = None

        dummy = Dummy(a="foo", b="5", c=(1,2,3))
        self.assertEqual(dummy.a, "foo")
        self.assertEqual(dummy.b, 5)
        self.assertEqual(dummy.c, [1,2,3])

    def test_decorator_args(self):
        @util.mdtf_dataclass(frozen=True)
        class Dummy(object):
            a: str = None
            b: int = None

        dummy = Dummy(a="foo", b=5)
        self.assertTrue(hasattr(dummy, '__hash__'))
        self.assertEqual(dummy.a, "foo")
        self.assertEqual(dummy.b, 5)
        with self.assertRaises(dataclasses.FrozenInstanceError):
            dummy.b = 7

    def test_mandatory_args(self):
        @util.mdtf_dataclass
        class Dummy(object):
            a: str = util.MANDATORY
            b: int = util.NOTSET
            c: list = dataclasses.field(default_factory=list)

        dummy = Dummy(a="foo")
        self.assertEqual(dummy.a, "foo")
        self.assertEqual(dummy.b, util.NOTSET)
        self.assertEqual(dummy.c, [])
        with self.assertRaises(ValueError):
            dummy = Dummy(b=5)

    def test_mandatory_arg_inheritance(self):
        @util.mdtf_dataclass
        class Dummy1(object):
            a: str = util.MANDATORY

        @util.mdtf_dataclass
        class Dummy2(object):    
            b: int = util.NOTSET

        @util.mdtf_dataclass
        class Dummy12(Dummy1, Dummy2): pass

        @util.mdtf_dataclass
        class Dummy21(Dummy2, Dummy1): pass

        dummy = Dummy12(a="foo")
        self.assertEqual(dummy.a, "foo")
        self.assertEqual(dummy.b, util.NOTSET)
        with self.assertRaises(ValueError):
            dummy = Dummy12(b=5)
        dummy = Dummy21(a="foo")
        self.assertEqual(dummy.a, "foo")
        self.assertEqual(dummy.b, util.NOTSET)
        with self.assertRaises(ValueError):
            dummy = Dummy21(b=5)

    def test_defaults_coerce(self):
        @util.mdtf_dataclass()
        class Dummy(object):
            a: int = 5
            b: int = None
            c: int = util.NOTSET
            d: int = "not_an_int_but_python_don't_care"
            e: int = dataclasses.field(default_factory=list)

        dummy = Dummy()
        self.assertEqual(dummy.a, 5)
        self.assertEqual(dummy.b, None)
        self.assertEqual(dummy.c, util.NOTSET)
        self.assertEqual(dummy.d, "not_an_int_but_python_don't_care")
        self.assertEqual(dummy.e, [])

    def test_ignore_noninit_values(self):
        @util.mdtf_dataclass
        class Dummy(object):
            a: int = 5
            b: int = 6
            c: int = dataclasses.field(init=False)
            d: dataclasses.InitVar[int] = None

            def __post_init__(self, d):
                self.c = "foo"
                self.d = d

        dummy = Dummy(a=None, b=util.NOTSET, d="bar")
        self.assertEqual(dummy.a, None)
        self.assertEqual(dummy.b, util.NOTSET)
        self.assertEqual(dummy.c, "foo")
        self.assertEqual(dummy.d, "bar")

    def test_from_struct(self):
        FooEnum = util.MDTFEnum('FooEnum', 'X Y Z')

        @util.mdtf_dataclass
        class Dummy(object):
            a: FooEnum = None
            b: dt.Date = None
            c: dt.DateFrequency = None

        dummy = Dummy(a="X", b="2010", c="6hr")
        self.assertEqual(dummy.a, FooEnum.X)
        self.assertEqual(dummy.b, dt.Date(2010))
        self.assertEqual(dummy.c, dt.DateFrequency(6, 'hr'))

    def test_typing_generics(self):
        @util.mdtf_dataclass
        class Dummy(object):
            a: typing.List = None
            b: typing.List[int] = None
            c: typing.Union[int, list] = 6
            d: typing.MutableSequence = dataclasses.field(default_factory=list)
            e: typing.Text = "foo"

        dummy = Dummy(a=(1,2), b=(1,2))
        self.assertEqual(dummy.a, [1,2])
        self.assertEqual(dummy.b, [1,2])
        self.assertEqual(dummy.c, 6)
        dummy = Dummy(a=(1,2), b=(1,2), c=[1,2])
        self.assertEqual(dummy.c, [1,2])
        dummy = Dummy(a=(1,2), b=(1,2), c=5)
        self.assertEqual(dummy.c, 5)
        dummy = Dummy(a=(1,2), b=(1,2), d=[1,2])
        self.assertEqual(dummy.d, [1,2])
        with self.assertRaises(ValueError):
            _ = Dummy(a=(1,2), b=(1,2), d=(1,2))

    def test_typing_generics_2(self):
        def dummy_f(x: str) -> int:
            return int(x)

        @util.mdtf_dataclass
        class Dummy(object):
            a: typing.Any = None
            b: typing.TypeVar('foo') = None
            c: typing.Callable[[int], str] = util.NOTSET
            d: typing.Generic[typing.TypeVar('X'), typing.TypeVar('X')] = None
            e: typing.Tuple[int, int] = (5,6)

        dummy = Dummy(a="a")
        self.assertEqual(dummy.a, "a")
        self.assertEqual(dummy.b, None)
        self.assertEqual(dummy.c, util.NOTSET)
        self.assertEqual(dummy.d, None)
        self.assertEqual(dummy.e, (5,6))
        dummy = Dummy(a="a", b="bar", c=dummy_f, d="also_ignored", e=[1,2])
        self.assertEqual(dummy.a, "a")
        self.assertEqual(dummy.b, "bar")
        self.assertEqual(dummy.c, dummy_f)
        self.assertEqual(dummy.d, "also_ignored")
        self.assertEqual(dummy.e, (1,2))

class TestUtil(unittest.TestCase):
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
        self.assertEqual(set(d.keys()), set(['a','b','c','d','e']))
        self.assertEqual(d['a'], "test_string")
        self.assertEqual(d['b'], 3)
        self.assertEqual(d['c'], False)
        self.assertEqual(len(d['d']), 3)
        self.assertEqual(d['d'], [1,2,3])
        self.assertEqual(set(d['e'].keys()), set(['aa','bb']))
        self.assertEqual(len(d['e']['aa']), 3)
        self.assertEqual(d['e']['aa'], [4,5,6])
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
        self.assertEqual(set(d.keys()), set(['a','b // c','e','f']))
        self.assertEqual(d['a'], 1)
        self.assertEqual(d['b // c'], "// d x ////")
        self.assertEqual(d['e'], False)
        self.assertEqual(d['f'], "ff")

    def test_write_json(self):
        pass

# ---------------------------------------------------
class TestSubprocessInteraction(unittest.TestCase):
    def test_run_shell_commands_stdout1(self):
        input = 'echo "foo"'
        out = util.run_shell_command(input)
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0], 'foo')

    def test_run_shell_commands_stdout2(self):
        input = 'echo "foo" && echo "bar"'
        out = util.run_shell_command(input)
        self.assertEqual(len(out), 2)
        self.assertEqual(out[0], 'foo')
        self.assertEqual(out[1], 'bar')
        
    def test_run_shell_commands_exitcode(self):
        input = 'echo "foo"; false'
        with self.assertRaises(Exception):
            # I couldn't get this to catch CalledProcessError specifically,
            # maybe because it takes args?
            util.run_shell_command(input)

    def test_run_shell_commands_envvars(self):
        input = 'echo $FOO; export FOO="baz"; echo $FOO'
        out = util.run_shell_command(input, env={'FOO':'bar'})
        self.assertEqual(len(out), 2)
        self.assertEqual(out[0], 'bar')
        self.assertEqual(out[1], 'baz')

    @unittest.skip("Skipping poll_command tests")
    def test_poll_command_shell_true(self):
        rc = util.poll_command('echo "foo"', shell=True)
        self.assertEqual(rc, 0)

    @unittest.skip("Skipping poll_command tests")
    def test_poll_command_shell_false(self):
        rc = util.poll_command(['echo', 'foo'], shell=False)
        self.assertEqual(rc, 0)
    
    @unittest.skip("Skipping poll_command tests")
    def test_poll_command_error(self):
        rc = util.poll_command(['false'], shell=False)
        self.assertEqual(rc, 1)

    def test_run_command_stdout1(self):
        out = util.run_command(['echo', '"foo"'])
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0], '"foo"')

    def test_run_command_exitcode(self):
        input = ['exit', '1']
        with self.assertRaises(Exception):
            # I couldn't get this to catch CalledProcessError specifically,
            # maybe because it takes args?
            util.run_command(input)

# ---------------------------------------------------

if __name__ == '__main__':
    unittest.main()
