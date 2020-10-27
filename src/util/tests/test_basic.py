import unittest
import unittest.mock as mock
from src.util import basic as util


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

class TestSpliceIntoList(unittest.TestCase):
    def test_splice_into_list_start(self):
        list_ = ['a','b','c']
        ans = util.splice_into_list(list_, {'a':['a1']})
        self.assertEqual(ans, ['a', 'a1', 'b', 'c'])

    def test_splice_into_list_middle(self):
        list_ = ['a','b','c']
        ans = util.splice_into_list(list_, {'b':['b1']})
        self.assertEqual(ans, ['a', 'b', 'b1', 'c'])
    
    def test_splice_into_list_end(self):
        list_ = ['a','b','c']
        ans = util.splice_into_list(list_, {'c':['c1']})
        self.assertEqual(ans, ['a', 'b', 'c', 'c1'])

    def test_splice_into_list_multi(self):
        list_ = ['a','b','a']
        ans = util.splice_into_list(list_, {'a':['a1'], 'c':['c1']})
        self.assertEqual(ans, ['a', 'a1', 'b', 'a', 'a1'])

    def test_splice_into_list_keyfn(self):
        list_ = ['aaa','bXX','bYY','c','dXX','bZZ']
        key_fn = (lambda s: s[0])
        splice_d = {'a':['a1'], 'b':['b1'], 'd':['d1'],'g':['g1']}
        ans = util.splice_into_list(list_, splice_d, key_fn)
        self.assertEqual(ans, 
            ['aaa', 'a1', 'bXX', 'b1', 'bYY', 'b1', 'c', 'dXX', 'd1', 'bZZ', 'b1']
        )

    def test_splice_into_list_general(self):
        list_ = ['a','b','b','c','d','b']
        splice_d = {'a':['a1','a2'], 'b':['b1'], 'd':['d1'],'g':['g1']}
        ans = util.splice_into_list(list_, splice_d)
        self.assertEqual(ans, 
            ['a', 'a1', 'a2', 'b', 'b1', 'b', 'b1', 'c', 'd', 'd1', 'b', 'b1']
        )

class TestSerializeClass(unittest.TestCase):
    def test_deserialize_builtin(self):
        cls_ = util.deserialize_class('list')
        self.assertEqual(cls_, list)
        cls_ = util.deserialize_class('str')
        self.assertEqual(cls_, str)
        cls_ = util.deserialize_class('int')
        self.assertEqual(cls_, int)

    def test_deserialize_user(self):
        class Dummy(object):
            pass
        cls_ = util.deserialize_class('Dummy')
        self.assertEqual(cls_, Dummy)
# ---------------------------------------------------

if __name__ == '__main__':
    unittest.main()
