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

    def test_extracts_existing_date_format1(self):
        start = "D:\\vid\\Baby\\6m-9m\\VID_20120307_193607.mp4"
        expected = "D:\\vid\\Baby\\6m-9m\\2012.03.07_19-36-07_VID.mp4"
        self.assertEqual(expected, proper_name(start, self.timestamp))

    def test_extracts_existing_date_format2(self):
        start = "D:\\vid\\Baby\\6m-9m\\video-2010-05-09-12-52-10.3gp"
        expected = "D:\\vid\\Baby\\6m-9m\\2010.05.09_12-52-10_video.3gp"
        self.assertEqual(expected, proper_name(start, self.timestamp))

    def test_does_not_rename_correct(self):
        start = "D:\\vid\\Baby\\6m-9m\\2013.02.13_20-47-44_MOV064.mp4"
        self.assertEqual(start, proper_name(start, self.timestamp, False))

    def test_does_not_append_underscore(self):
        start = "D:\\vid\\Baby\\6m-9m\\2012.12.15_162651.mp4"
        expected = "D:\\vid\\Baby\\6m-9m\\2012.12.15_16-26-51.mp4"
        self.assertEqual(expected, proper_name(start, self.timestamp))



if __name__ == '__main__':
    unittest.main()