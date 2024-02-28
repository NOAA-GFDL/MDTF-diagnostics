import unittest
from src.util import basic as util
from src.util import exceptions


class TestMDTFABCMeta(unittest.TestCase):
    def test_abstract_attribute(self):
        class Foo(metaclass=util.MDTFABCMeta):
            class_attr = util.abstract_attribute()

            def foo(self, x):
                return self.class_attr + x

        class GoodChildClass(Foo):
            class_attr = 5

        raised_exc = False
        try:
            b = GoodChildClass()
            test = b.foo(23)
        except Exception:
            raised_exc = True
        self.assertFalse(raised_exc)
        self.assertEqual(test, 28)

        class BadChildClass(Foo):
            pass

        with self.assertRaises(NotImplementedError):
            b = BadChildClass()


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
        temp = util.MultiMap({'a': 1, 'b': 2})
        temp_inv = temp.inverse()
        self.assertIn(1, temp_inv)
        self.assertEqual(temp_inv[2], set(['b']))

    def test_multimap_setitem(self):
        # test key addition and handling of duplicate values
        temp = util.MultiMap({'a': 1, 'b': 2})
        temp['c'] = 1
        temp_inv = temp.inverse()
        self.assertIn(1, temp_inv)
        self.assertCountEqual(temp_inv[1], set(['a', 'c']))
        temp['b'] = 3
        temp_inv = temp.inverse()
        self.assertNotIn(2, temp_inv)

    def test_multimap_delitem(self):
        # test item deletion
        temp = util.MultiMap({'a': 1, 'b': 2})
        del temp['b']
        temp_inv = temp.inverse()
        self.assertNotIn(2, temp_inv)

    def test_multimap_add(self):
        temp = util.MultiMap({'a': 1, 'b': 2, 'c': 1})
        temp['a'].add(3)
        temp_inv = temp.inverse()
        self.assertIn(3, temp_inv)
        self.assertCountEqual(temp_inv[3], set(['a']))
        temp['a'].add(2)
        temp_inv = temp.inverse()
        self.assertIn(2, temp_inv)
        self.assertCountEqual(temp_inv[2], set(['a', 'b']))

    def test_multimap_add_new(self):
        temp = util.MultiMap({'a': 1, 'b': 2, 'c': 1})
        temp['x'].add(2)
        temp_inv = temp.inverse()
        self.assertIn(2, temp_inv)
        self.assertCountEqual(temp_inv[2], set(['b', 'x']))

    def test_multimap_remove(self):
        temp = util.MultiMap({'a': 1, 'b': 2, 'c': 1})
        temp['c'].add(2)
        temp['c'].remove(1)
        temp_inv = temp.inverse()
        self.assertIn(2, temp_inv)
        self.assertCountEqual(temp_inv[2], set(['b', 'c']))
        self.assertIn(1, temp_inv)
        self.assertCountEqual(temp_inv[1], set(['a']))


class TestWormDict(unittest.TestCase):
    def test_worm_normal_operation(self):
        foo = util.WormDict(a=1, b=2)
        self.assertTrue(isinstance(foo, dict))  # should really be testing for MutableMapping
        self.assertEqual(foo['b'], 2)
        # all dicts are OrderedDicts starting with 3.7
        self.assertEqual(tuple(foo.keys()), ('a', 'b'))
        self.assertEqual(tuple(foo.values()), (1, 2))
        self.assertEqual(tuple(str(k) + str(v) for k, v in foo.items()), ('a1', 'b2'))
        foo.update({'c': 3, 'd': 4})
        self.assertEqual(foo['d'], 4)
        self.assertEqual(len(foo), 4)
        test = foo.setdefault('d', 5)
        self.assertEqual(test, 4)
        self.assertEqual(foo['d'], 4)

    def test_worm_overwrite(self):
        foo = util.WormDict(a=1, b=2)
        with self.assertRaises(exceptions.WormKeyError):
            foo['a'] = 3
        with self.assertRaises(exceptions.WormKeyError):
            foo.update({'c': 3, 'a': 4})

    def test_worm_delete(self):
        foo = util.WormDict(a=1, b=2)
        with self.assertRaises(exceptions.WormKeyError):
            del foo['a']
        with self.assertRaises(exceptions.WormKeyError):
            _ = foo.pop('a')
        with self.assertRaises(exceptions.WormKeyError):
            _ = foo.popitem()

    def test_consistentD_normal_operation(self):
        foo = util.ConsistentDict(a=1, b=2)
        self.assertTrue(isinstance(foo, dict))  # should really be testing for MutableMapping
        self.assertEqual(foo['b'], 2)
        # all dicts are OrderedDicts starting with 3.7
        self.assertEqual(tuple(foo.keys()), ('a', 'b'))
        self.assertEqual(tuple(foo.values()), (1, 2))
        self.assertEqual(tuple(str(k) + str(v) for k, v in foo.items()), ('a1', 'b2'))
        foo.update({'c': 3, 'd': 4})
        self.assertEqual(foo['d'], 4)
        self.assertEqual(len(foo), 4)
        test = foo.setdefault('d', 5)
        self.assertEqual(test, 4)
        self.assertEqual(foo['d'], 4)

    def test_consistentD_overwrite_different(self):
        foo = util.ConsistentDict(a=1, b=2)
        with self.assertRaises(exceptions.WormKeyError):
            foo['a'] = 3
        with self.assertRaises(exceptions.WormKeyError):
            foo.update({'c': 3, 'a': 4})

    def test_consistentD_overwrite_same(self):
        foo = util.ConsistentDict(a=1, b=2)
        raised_exc = False
        try:
            foo['b'] = 2
        except Exception:
            raised_exc = True
        self.assertFalse(raised_exc)
        raised_exc = False
        try:
            foo.update({'c': 3, 'a': 1})
        except Exception:
            raised_exc = True
        self.assertFalse(raised_exc)
        self.assertEqual(foo['a'], 1)
        self.assertEqual(foo['b'], 2)
        self.assertEqual(foo['c'], 3)

    def test_consistentD_delete(self):
        foo = util.ConsistentDict(a=1, b=2)
        del foo['a']
        self.assertEqual(foo['b'], 2)
        self.assertEqual(len(foo), 1)
        foo = util.ConsistentDict(a=1, b=2)
        bar = foo.pop('a')
        self.assertEqual(bar, 1)
        self.assertEqual(len(foo), 1)
        foo = util.ConsistentDict(a=1, b=2)
        bar, baz = foo.popitem()
        self.assertEqual(bar, 'a')
        self.assertEqual(baz, 1)
        self.assertEqual(len(foo), 1)


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
        Dummy = util.MDTFEnum('Dummy', 'VALUE ANOTHER_VALUE')
        self.assertEqual('value', str(Dummy.VALUE))
        self.assertEqual('another_value', str(Dummy.ANOTHER_VALUE))

    def test_from_string(self):
        Dummy = util.MDTFEnum('Dummy', 'VALUE ANOTHER_VALUE')
        self.assertEqual(Dummy.from_struct('value'), Dummy.VALUE)
        self.assertEqual(Dummy.from_struct('another_value'), Dummy.ANOTHER_VALUE)
        with self.assertRaises(ValueError):
            Dummy.from_struct('invalid_value')

    def test_eq_coercion(self):
        Dummy = util.MDTFEnum('Dummy', 'VALUE ANOTHER_VALUE')
        self.assertEqual(Dummy.VALUE, Dummy.VALUE)
        self.assertNotEqual(Dummy.ANOTHER_VALUE, Dummy.VALUE)
        # self.assertEqual(Dummy.VALUE, 'value')
        # self.assertEqual('value', Dummy.VALUE)
        # self.assertNotEqual('another_value', Dummy.VALUE)
        # self.assertNotEqual(Dummy.VALUE, 'another_value')


class TestSpliceIntoList(unittest.TestCase):
    def test_splice_into_list_start(self):
        list_ = ['a', 'b', 'c']
        ans = util.splice_into_list(list_, {'a': ['a1']})
        self.assertEqual(ans, ['a', 'a1', 'b', 'c'])

    def test_splice_into_list_middle(self):
        list_ = ['a', 'b', 'c']
        ans = util.splice_into_list(list_, {'b': ['b1']})
        self.assertEqual(ans, ['a', 'b', 'b1', 'c'])

    def test_splice_into_list_end(self):
        list_ = ['a', 'b', 'c']
        ans = util.splice_into_list(list_, {'c': ['c1']})
        self.assertEqual(ans, ['a', 'b', 'c', 'c1'])

    def test_splice_into_list_multi(self):
        list_ = ['a', 'b', 'a']
        ans = util.splice_into_list(list_, {'a': ['a1'], 'c': ['c1']})
        self.assertEqual(ans, ['a', 'a1', 'b', 'a', 'a1'])

    def test_splice_into_list_keyfn(self):
        list_ = ['aaa', 'bXX', 'bYY', 'c', 'dXX', 'bZZ']
        key_fn = (lambda s: s[0])
        splice_d = {'a': ['a1'], 'b': ['b1'], 'd': ['d1'], 'g': ['g1']}
        ans = util.splice_into_list(list_, splice_d, key_fn)
        self.assertEqual(ans,
                         ['aaa', 'a1', 'bXX', 'b1', 'bYY', 'b1', 'c', 'dXX', 'd1', 'bZZ', 'b1']
                         )

    def test_splice_into_list_general(self):
        list_ = ['a', 'b', 'b', 'c', 'd', 'b']
        splice_d = {'a': ['a1', 'a2'], 'b': ['b1'], 'd': ['d1'], 'g': ['g1']}
        ans = util.splice_into_list(list_, splice_d)
        self.assertEqual(ans,
                         ['a', 'a1', 'a2', 'b', 'b1', 'b', 'b1', 'c', 'd', 'd1', 'b', 'b1']
                         )


if __name__ == '__main__':
    unittest.main()
