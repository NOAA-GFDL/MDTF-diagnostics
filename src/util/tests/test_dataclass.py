import unittest
import unittest.mock as mock
import dataclasses
import typing
import src.datelabel as dt # only used to construct one test instance
from src.util import basic
from src.util import dataclass as util


class TestRegexPattern(unittest.TestCase):

    # TODO: need many more tests for RegexPattern et al.

    def test_regex_dataclass(self):
        regex = r"/(?P<foo>\d+)/(?P<bar>\d+)/other_text"
        ppat = util.RegexPattern(regex)

        @util.regex_dataclass(ppat)
        @util.mdtf_dataclass()
        class A():
            foo: int
            bar: int

        ppat.match('/123/456/other_text')
        self.assertDictEqual(ppat.data, {'foo':123, 'bar': 456})
        a = A.from_string('/1/2/other_text')
        self.assertEqual(a.foo, 1)
        self.assertEqual(a.bar, 2)
        b = A.from_string('/3/4/other_text')
        self.assertEqual(a.foo, 1)
        self.assertEqual(a.bar, 2)
        self.assertEqual(b.foo, 3)
        self.assertEqual(b.bar, 4)

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
        FooEnum = basic.MDTFEnum('FooEnum', 'X Y Z')

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
        with self.assertRaises(TypeError):
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

if __name__ == '__main__':
    unittest.main()
