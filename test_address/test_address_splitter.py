#!/bin/env python
# -*- coding: utf-8 -*-


import sys

import re
import numpy as np
import unittest

from address_splitter import (
    AddressSplitter,
    SplitingStrategy
)

from address import Address

from testing import (
    COUNTRY_LIST,
    REGION_LIST,
    SUBREGION_LIST,
    CITY_LIST,
    STREET_LIST,
    HOUSE_LIST,
    POI_LIST
)


class TestSplittingStrategy(unittest.TestCase):
    def test_init(self):
        strategy = SplitingStrategy(
            address='0123456789',
            index_pos=(0, 10),
            country_pos=(0, 10),
            region_pos=(0, 10),
            subregion_pos=(0, 10),
            city_pos=(0, 10),
            street_pos=(0, 10),
            house_pos=(0, 10),
            poi_pos=(0, 10)
        )
        expected_matr = np.ones((8, 10), dtype=np.byte)
        np.testing.assert_array_equal(strategy._score_matrix, expected_matr)

        strategy = SplitingStrategy(
            address='0123456789',
            index_pos=None,
            country_pos=None,
            region_pos=None,
            subregion_pos=None,
            city_pos=None,
            street_pos=None,
            house_pos=None,
            poi_pos=None
        )
        expected_matr = np.zeros((8, 10), dtype=np.byte)
        np.testing.assert_array_equal(strategy._score_matrix, expected_matr)

        strategy = SplitingStrategy(
            address='0123456789',
            index_pos=None,
            country_pos=(0, 5),
            region_pos=(5, 10),
            subregion_pos=None,
            city_pos=None,
            street_pos=(0, 10),
            house_pos=(3, 5),
            poi_pos=None
        )
        expected_matr = np.array(
            [[0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
             [1, 1, 1, 1, 1, 0, 0, 0, 0, 0],
             [0, 0, 0, 0, 0, 1, 1, 1, 1, 1],
             [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
             [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
             [1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
             [0, 0, 0, 1, 1, 0, 0, 0, 0, 0],
             [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]], dtype=np.byte)
        np.testing.assert_array_equal(strategy._score_matrix, expected_matr)

        # Test for wrong position values
        try:
            strategy = SplitingStrategy(
                address='0123456789',
                index_pos=None,
                country_pos=(0, 11),
                region_pos=None,
                subregion_pos=None,
                city_pos=None,
                street_pos=None,
                house_pos=None,
                poi_pos=None
            )
            raise Exception
        except ValueError:
            pass

        try:
            _ = SplitingStrategy(
                address='0123456789',
                index_pos=None,
                country_pos=(-1, 10),
                region_pos=None,
                subregion_pos=None,
                city_pos=None,
                street_pos=None,
                house_pos=None,
                poi_pos=None
            )
            raise Exception
        except ValueError:
            pass

        try:
            _ = SplitingStrategy(
                address='0123456789',
                index_pos=None,
                country_pos=(5, 3),
                region_pos=None,
                subregion_pos=None,
                city_pos=None,
                street_pos=None,
                house_pos=None,
                poi_pos=None
            )
            raise Exception
        except ValueError:
            pass

    def test_get_space_penalty(self):

        strategy = SplitingStrategy(
            address='ывааааааываырпрарапрапрараорпопопропрпропоппропdddddddр',
            index_pos=None,
            country_pos=None,
            region_pos=None,
            subregion_pos=(15, 31),
            city_pos=(5, 13),
            street_pos=(50, 55),
            house_pos=None,
            poi_pos=None
        )
        self.assertEqual(strategy._get_space_penalty(), 54 - 5)

        strategy = SplitingStrategy(
            address='ывdddddddааааааываырпрапрарапрапрараорпопопропрпропоппр',
            index_pos=(1, 2),
            country_pos=(2, 3),
            region_pos=(3, 4),
            subregion_pos=(4, 5),
            city_pos=(5, 6),
            street_pos=(6, 10),
            house_pos=(10, 11),
            poi_pos=None
        )
        self.assertEqual(strategy._get_space_penalty(), 10 - 1)

        strategy = SplitingStrategy(
            address='ывааааааdddddddываырпрапрарапрапрараорпопопропрпропоппр',
            index_pos=None,
            country_pos=None,
            region_pos=None,
            subregion_pos=None,
            city_pos=None,
            street_pos=None,
            house_pos=None,
            poi_pos=None
        )
        self.assertEqual(strategy._get_space_penalty(), 0)

        strategy = SplitingStrategy(
            address='ываыааааываырпdddddddрапрарапрапрараорпопопропрпропоппр',
            index_pos=(1, 3),
            country_pos=(5, 10),
            region_pos=(20, 30),
            subregion_pos=None,
            city_pos=None,
            street_pos=(35, 40),
            house_pos=(42, 43),
            poi_pos=None
        )
        self.assertEqual(strategy._get_space_penalty(), 42 - 1)

    def test_get_score(self):

        strategy = SplitingStrategy(
            address='0123456789',
            index_pos=None,
            country_pos=None,
            region_pos=None,
            subregion_pos=None,
            city_pos=None,
            street_pos=None,
            house_pos=None,
            poi_pos=None
        )
        self.assertEqual(strategy.get_score(),
                         10 * strategy.blank_penalty +
                         strategy.absences_penalty['Index'][1] +
                         strategy.absences_penalty['Country'][1] +
                         strategy.absences_penalty['Region'][1] +
                         strategy.absences_penalty['Subregion'][1] +
                         strategy.absences_penalty['City'][1] +
                         strategy.absences_penalty['Street'][1] +
                         strategy.absences_penalty['House'][1] +
                         strategy.absences_penalty['Poi'][1])

        strategy = SplitingStrategy(
            address='0123456789',
            index_pos=None,
            country_pos=(0, 5),
            region_pos=(5, 10),
            subregion_pos=None,
            city_pos=None,
            street_pos=(0, 10),
            house_pos=None,
            poi_pos=None
        )
        # expected_matr = np.array(
        #    [[0, 0, 0, 0, 0, 0, 0, 0, 0, 0],   (Index)
        #     [1, 1, 1, 1, 1, 0, 0, 0, 0, 0],   (Country)
        #     [0, 0, 0, 0, 0, 1, 1, 1, 1, 1],   (Region)
        #     [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],   (Subregion)
        #     [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],   (City)
        #     [1, 1, 1, 1, 1, 1, 1, 1, 1, 1],   (Street)
        #     [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],   (House)
        #     [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]],  (Poi))
        # sum: 2  2  2  2  2  2  2  2  2  2
        self.assertEqual(strategy.get_score(),
                         10 * strategy.overlap_penalty +
                         strategy.absences_penalty['Index'][1] +
                         strategy.absences_penalty['Subregion'][1] +
                         strategy.absences_penalty['City'][1] +
                         strategy.absences_penalty['House'][1] +
                         strategy.absences_penalty['Poi'][1] +
                         strategy.space_ratio * 9)

        strategy = SplitingStrategy(
            address='0123456789',
            index_pos=None,
            country_pos=(2, 5),
            region_pos=(5, 8),
            subregion_pos=None,
            city_pos=None,
            street_pos=(3, 5),
            house_pos=(8, 9),
            poi_pos=None
        )
        # expected_matr = np.array(
        #    [[0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        #     [0, 0, 1, 1, 1, 0, 0, 0, 0, 0],
        #     [0, 0, 0, 0, 0, 1, 1, 1, 0, 0],
        #     [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        #     [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        #     [0, 0, 0, 1, 1, 0, 0, 0, 0, 0],
        #     [0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
        #     [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        #                                     ], dtype=np.byte)
        # sum: 0  0  1  2  2  1  1  1  1  0
        self.assertEqual(strategy.get_score(),
                         2 * strategy.overlap_penalty +
                         strategy.absences_penalty['Index'][1] +
                         strategy.absences_penalty['Subregion'][1] +
                         strategy.absences_penalty['City'][1] +
                         strategy.absences_penalty['Poi'][1] +
                         3 * strategy.blank_penalty +
                         strategy.space_ratio * 6)

        strategy = SplitingStrategy(
            address='0123456789',
            index_pos=None,
            country_pos=(2, 3),
            region_pos=(5, 8),
            subregion_pos=None,
            city_pos=None,
            street_pos=(9, 10),
            house_pos=None,
            poi_pos=None
        )
        self.assertEqual(strategy.get_score(),
                         strategy.absences_penalty['Index'][1] +
                         strategy.absences_penalty['Subregion'][1] +
                         strategy.absences_penalty['City'][1] +
                         strategy.absences_penalty['House'][1] +
                         strategy.absences_penalty['Poi'][1] +
                         5 * strategy.blank_penalty +
                         strategy.space_ratio * (9 - 2))

        strategy = SplitingStrategy(
            address='0123456789',
            index_pos=(0, 3),
            country_pos=(2, 3),
            region_pos=(5, 8),
            subregion_pos=None,
            city_pos=None,
            street_pos=(9, 10),
            house_pos=(9, 10),
            poi_pos=None
        )
        self.assertEqual(strategy.get_score(),
                         2 * strategy.overlap_penalty +
                         strategy.absences_penalty['Subregion'][1] +
                         strategy.absences_penalty['City'][1] +
                         strategy.absences_penalty['Poi'][1] +
                         3 * strategy.blank_penalty +
                         strategy.space_ratio * 9)


class TestAddressSplitter(unittest.TestCase):

    def setUp(self):
        splitter = AddressSplitter(
            country_list_file=COUNTRY_LIST,
            region_list_file=REGION_LIST,
            subregion_list_file=SUBREGION_LIST,
            city_list_file=CITY_LIST,
            street_list_file=STREET_LIST,
            house_list_file=HOUSE_LIST,
            poi_list_file=POI_LIST
        )
        self.splitter = splitter

    def test__init__(self):
        parts = [self.splitter.house_list,
                 self.splitter.street_list,
                 self.splitter.city_list,
                 self.splitter.subregion_list,
                 self.splitter.region_list,
                 self.splitter.country_list,
                 self.splitter.poi_list]
        for i in range(len(parts)):
            for j in range(i+1, len(parts)):
                self.assertNotEqual(parts[i], parts[j])

    def test__read_list_file(self):

        expected = [
            u'российская федерация',
            u'россия'
        ]
        found = self.splitter._read_list_file(COUNTRY_LIST)

        self.assertEquals(found, expected)

    def test__get_position(self):
        patterns = {u'qwerty': re.compile(ur'\bqwerty\b', re.IGNORECASE),
                    u'abcd': re.compile(ur'\babcd\b', re.IGNORECASE)}
        address = u'abcd qwerty Abcd abcdf'
        pos = self.splitter._get_positions(address, patterns)

        expected = {
            'qwerty': [(5, 11)],
            'abcd': [(0, 4), (12, 16)]
        }
        self.assertEqual(pos, expected)

    def test__init(self):
        cl = self.splitter.country_list
        self.assertEqual(len(cl), 2)
        expected_names = [
            u'российская федерация',
            u'россия'
        ]
        for name in expected_names:
            self.assertTrue(name in cl)
            s = '0123 ' + name + ' werwewt'
            pos = self.splitter._get_country_pos(s)
            self.assertEqual(pos,
                             {name: [(5, len(name) + 5)]})

    def test_get_XXXXXX_pos(self):
        address = ur"Москва, Россия"
        pos = self.splitter._get_country_pos(address)
        expected = {u'россия': [(8, 14)]}
        self.assertEqual(pos, expected)

        address = ur"Москва, Российская Федерация"
        pos = self.splitter._get_country_pos(address)
        expected = {u'российская федерация': [(8, 28)]}
        self.assertEqual(pos, expected)

        pos = self.splitter._get_index_pos(address)
        expected = {}
        self.assertEqual(pos, expected)

        address = \
            u"Российская федерация, московская область, Зеленоград, вавилова"
        pos = self.splitter._get_country_pos(address)
        expected = {u'российская федерация': [(0, 20)]}
        self.assertEqual(pos, expected)

        pos = self.splitter._get_region_pos(address)
        expected = {
            u'московская область': [(22, 40)],
            u'московская': [(22, 32)]
        }
        self.assertEqual(pos, expected)

        pos = self.splitter._get_city_pos(address)
        expected = {u'зеленоград': [(42, 52)]}
        self.assertEqual(pos, expected)

        pos = self.splitter._get_street_pos(address)
        expected = {
            u'вавилова': [(54, 62)],
            u'московская': [(22, 32)]
        }
        self.assertEqual(pos, expected)

        address = \
            u'243545, москва, красная площадь'
        pos = self.splitter._get_country_pos(address)
        expected = {}
        self.assertEqual(pos, expected)

        pos = self.splitter._get_region_pos(address)
        expected = {}
        self.assertEqual(pos, expected)

        pos = self.splitter._get_city_pos(address)
        expected = {u'москва': [(8, 14)]}
        self.assertEqual(pos, expected)

        pos = self.splitter._get_street_pos(address)
        expected = {u'красная площадь': [(16, 31)]}
        self.assertEqual(pos, expected)

        pos = self.splitter._get_index_pos(address)
        expected = {u'243545': [(0, 6)]}
        self.assertEqual(pos, expected)

        # RE tests
        address = u'sdffjj, рязанская область, пывфоаджо'
        pos = self.splitter._get_region_pos(address)
        expected = {u'рязанская область': [(8, 25)]}
        self.assertEqual(pos, expected)

        address = u'sdffjj, рязанская обл, пывфоаджо'
        pos = self.splitter._get_region_pos(address)
        expected = {u'рязанская обл': [(8, 21)]}
        self.assertEqual(pos, expected)

        address = u'sdffjj, рязанская область, моркинский р-н'
        pos = self.splitter._get_subregion_pos(address)
        expected = {u'моркинский р-н': [(27, 41)], u'моркинский': [(27, 37)]}
        self.assertEqual(pos, expected)

        address = u'sdffjj, рязанская область, моркинский район'
        pos = self.splitter._get_subregion_pos(address)
        expected = {u'моркинский район': [(27, 43)], u'моркинский': [(27, 37)]}
        self.assertEqual(pos, expected)

        address = u'sdffjj, рязанская область, моркинский'
        pos = self.splitter._get_subregion_pos(address)
        expected = {u'моркинский': [(27, 37)]}
        self.assertEqual(pos, expected)

        address = u'sdffjj, рязанская область, остановка солнышко'
        pos = self.splitter._get_poi_pos(address)
        expected = {u'остановка солнышко': [(27, 45)]}
        self.assertEqual(pos, expected)

    def test_get_strategies(self):
        address = u'Российская федерация, москва, улица россия'

        # There are many possible startegies. List them all:
        expected = [
            Address(
                raw_address=address,
                country=u'россия',
                settlement=u'москва',
                street=u'улица россия',
                ),
            Address(country=u'россия', raw_address=address),
            Address(
                raw_address=address,
                country=u'россия',
                street=u'улица россия'
                ),
            Address(
                raw_address=address,
                country=u'россия',
                settlement=u'москва'
                ),
            Address(
                raw_address=address,
                country=u'Российская федерация',
                settlement=u'москва',
                street=u'улица россия'
                ),
            Address(country=u'Российская федерация', raw_address=address,),
            Address(
                raw_address=address,
                country=u'Российская федерация',
                street=u'улица россия',
                ),
            Address(
                raw_address=address,
                country=u'Российская федерация',
                settlement=u'москва'
                ),
            Address(street=u'улица россия', raw_address=address),
            Address(settlement=u'москва', raw_address=address),
            Address(
                raw_address=address,
                settlement=u'москва',
                street=u'улица россия'
                ),
            Address(raw_address=address)
        ]
        for s in self.splitter._get_strategies(address):
            # if not s.get_parsed_address() in expected:
            #     a = s.get_parsed_address()
            #     print a.country, a.settlement, a.street, a.house
            self.assertTrue(s.get_parsed_address() in expected)

        self.assertEqual(len(self.splitter._get_strategies(address)),
                         len(expected))

    def test_get_best_strategy(self):
        address = u'Российская федерация, москва, улица россия, дом 3'
        got = self.splitter.get_best_strategy(address)
        # u',Российская федерация,,москва,улица россия'
        expected = SplitingStrategy(
            address=address,
            index_pos=None,
            country_pos=(0, 20),
            region_pos=None,
            subregion_pos=None,
            city_pos=(22, 28),
            street_pos=(30, 42),
            house_pos=(44, 49),
            poi_pos=None
        )
        self.assertEqual(got, expected)

        address = (
            u'Российская федерация, москва, улица россия, '
            u'остановка Солнышко'
        )
        got = self.splitter.get_best_strategy(address)
        # u',Российская федерация,,москва,улица россия'
        expected = SplitingStrategy(
            address=address,
            index_pos=None,
            country_pos=(0, 20),
            region_pos=None,
            subregion_pos=None,
            city_pos=(22, 28),
            street_pos=(30, 42),
            house_pos=None,
            poi_pos=(44, 62)
        )
        self.assertEqual(got, expected)

        # u',россия,,москва,улица россия'
        not_expected = SplitingStrategy(
            address=address,
            index_pos=None,
            country_pos=(36, 42),   # !!!! We do not exect it
            region_pos=None,
            subregion_pos=None,
            city_pos=(22, 28),
            street_pos=(30, 42),
            house_pos=(44, 49),
            poi_pos=None
        )
        self.assertFalse(got == not_expected)

        # Check that we do not calculate strategy second time
        dummy = 'A DUMMY VARIABLE'
        self.splitter._best_strat = dummy
        parts = self.splitter.get_best_strategy(address)
        self.assertEqual(parts, dummy)

    def test_get_house_num(self):
        address = u'москва, улица малая, дом 18'
        expected = {u'дом 18': [(21, 27)], u'18': [(25, 27)]}
        self.assertEqual(self.splitter._get_house_pos(address),
                         expected)
        address = u'москва, улица малая, дом 18/3'
        expected = {u'дом 18/3': [(21, 29)],
                    u'дом 18': [(21, 27)],
                    u'18/3': [(25, 29)],
                    u'18': [(25, 27)],
                    u'3': [(28, 29)]}
        self.assertEqual(self.splitter._get_house_pos(address),
                         expected)
        address = u'москва, улица малая, h'
        self.assertEqual(self.splitter._get_house_pos(address),
                         {})
        address = u'москва, улица малая, 18'
        expected = {u'18': [(21, 23)]}
        self.assertEqual(self.splitter._get_house_pos(address),
                         expected)

    def test_get_parsed_address(self):
        address = u'Российская федерация, москва, улица россия, дом 3'
        got = self.splitter.get_parsed_address(address)
        expected = Address(
            raw_address=address,
            country=u'Российская федерация',
            settlement=u'москва',
            street=u'улица россия',
            house=u'дом 3'
        )
        self.assertEqual(got, expected)

        self.assertEqual(self.splitter._parsed_address, expected)

        # Check that we do not calculate strategy second time
        dummy = 'A DUMMY VARIABLE'
        self.splitter._parsed_address = dummy
        parts = self.splitter.get_parsed_address(address)
        self.assertEqual(parts, dummy)


if __name__ == '__main__':

    suite = unittest.makeSuite(TestSplittingStrategy, 'test')
    runner = unittest.TextTestRunner()
    result = runner.run(suite)
    if not result.wasSuccessful():
        sys.exit(1)

    suite = unittest.makeSuite(TestAddressSplitter, 'test')
    runner = unittest.TextTestRunner()
    result = runner.run(suite)
    if not result.wasSuccessful():
        sys.exit(1)
