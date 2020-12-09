import unittest
import unittest.mock as mock
from src.util import filesystem as util

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

if __name__ == '__main__':
    unittest.main()