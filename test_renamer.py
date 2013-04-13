from datetime import datetime
import unittest

from renamer import proper_name


class TestRenaming(unittest.TestCase):
    timestamp = datetime.strptime("2012.03.27 10:23:17", "%Y.%m.%d %H:%M:%S")

    def test_renames_already_changed(self):
        modified = "D:\\vid\\Baby\\6m-9m\\2013.02.10_MOV03D.mp4"
        expected = "D:\\vid\\Baby\\6m-9m\\2012.03.27_10-23-17_MOV061.mp4"
        self.assertEqual(expected, proper_name(modified, self.timestamp))

    def test_renames_old(self):
        bad_name = "D:\\vid\\Baby\\6m-9m\\MOV03D.mp4"
        expected = "D:\\vid\\Baby\\6m-9m\\2012.03.27_10-23-17_MOV061.mp4"
        self.assertEqual(expected, proper_name(bad_name, self.timestamp))

    def test_deals_with_spaces(self):
        bad_name = "D:\\vid\\Baby\\6m-9m\\2012.10.19 1.mp4"
        expected = "D:\\vid\\Baby\\6m-9m\\2012.03.27_10-23-17_1.mp4"
        self.assertEqual(expected, proper_name(bad_name, self.timestamp))

if __name__ == '__main__':
    unittest.main()