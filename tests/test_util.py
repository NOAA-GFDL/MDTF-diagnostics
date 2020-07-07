import os
import unittest
import mock # define mock os.environ so we don't mess up real env vars
import src.util as util

class TestBasicClasses(unittest.TestCase):
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
        self.assertItemsEqual(temp_inv[1], set(['a','c']))
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
        self.assertItemsEqual(temp_inv[3], set(['a']))
        temp['a'].add(2)
        temp_inv = temp.inverse()
        self.assertIn(2, temp_inv)
        self.assertItemsEqual(temp_inv[2], set(['a','b']))

    def test_multimap_add_new(self):
        temp = util.MultiMap({'a':1, 'b':2, 'c':1})
        temp['x'].add(2)
        temp_inv = temp.inverse()
        self.assertIn(2, temp_inv)
        self.assertItemsEqual(temp_inv[2], set(['b','x']))

    def test_multimap_remove(self):
        temp = util.MultiMap({'a':1, 'b':2, 'c':1})
        temp['c'].add(2)
        temp['c'].remove(1)
        temp_inv = temp.inverse()
        self.assertIn(2, temp_inv)
        self.assertItemsEqual(temp_inv[2], set(['b','c']))
        self.assertIn(1, temp_inv)
        self.assertItemsEqual(temp_inv[1], set(['a']))

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

    def test_poll_command_shell_true(self):
        rc = util.poll_command('echo "foo"', shell=True)
        self.assertEqual(rc, 0)

    def test_poll_command_shell_false(self):
        rc = util.poll_command(['echo', 'foo'], shell=False)
        self.assertEqual(rc, 0)
    
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
