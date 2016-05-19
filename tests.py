#! /usr/bin/env python3

import unittest
import os
import sqlite3

import map_utils

class TestMBTiles (unittest.TestCase):

    def setUp (self):
        # the bbox is not really important
        self.backend= map_utils.MBTilesBackend ('TestMBTiles', [10, 20, 30, 40])
        session= sqlite3.connect ('TestMBTiles.mbt')
        self.session.set_trace_callback (print)
        self.db= session.cursor ()


    def test_single_tile (self):
        data= open ('sea.png', 'rb').read ()

        self.backend.store (0, 0, 0, data)
        self.backend.commit ()

        self.assertTrue (self.backend.exists (0, 0, 0))

    def test_two_seas_one_tile (self):
        data= open ('sea.png', 'rb').read ()

        self.backend.store (0, 0, 0, data)
        self.backend.store (1, 1, 1, data)
        self.backend.commit ()
        self.backend.close ()

        # test two seas
        seas= self.db.execute ('select * from map;').fetchall ()

        self.assertEqual (len (seas), 2)

        # test one id
        self.assertEqual (seas[0][3], seas[1][3])

        # test one tile
        tile= self.db.execute ('select * from images;').fetchall ()

        self.assertEqual (len (tile), 1)

        # test one id, again
        self.assertEqual (seas[0][3], tile[0][0])

        # test one view
        tiles= self.db.execute ('select * from tiles;').fetchall ()

        self.assertEqual (len (tiles), 2)

    def test_update (self):
        data1= open ('data1.png', 'rb').read ()
        data2= open ('data2.png', 'rb').read ()

        self.backend.store (0, 0, 0, data1)
        self.backend.commit ()
        self.backend.store (0, 0, 0, data2)
        self.backend.commit ()
        self.backend.close ()

        data3= self.db.execute ('SELECT tile_data FROM tiles;').fetchall ()
        self.assertEqual (data3[0][0], data2)

    def tearDown (self):
        self.backend.close ()
        os.unlink ('TestMBTiles.mbt')

if __name__ == '__main__':
    unittest.main(verbosity=2)
