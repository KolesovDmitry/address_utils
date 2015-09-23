#!/bin/env python
# -*- coding: utf-8 -*-

import sys

import re
from itertools import product
import numpy as np
from collections import OrderedDict

from address import Address


class SplitingStrategy(object):
    """Стратегия -- способ разбиения строки адреса на составные части.
    Класс предоставляет способ оценки качества разбиения (функция
    get_score).
    """
    def __init__(self,
                 address,
                 index_pos,
                 country_pos,
                 region_pos,
                 subregion_pos,
                 city_pos,
                 street_pos,
                 house_pos,
                 poi_pos):

        self.address = address
        self.index_pos = index_pos
        self.country_pos = country_pos
        self.region_pos = region_pos
        self.subregion_pos = subregion_pos
        self.city_pos = city_pos
        self.street_pos = street_pos
        self.house_pos = house_pos
        self.poi_pos = poi_pos

        # Penalties:
        self.overlap_penalty = 100  # penalty for overlapping parts of address
        self.blank_penalty = 10    # penalty for unused symbols in the address
        self.space_ratio = 1       # factor for space penalties

        # Create position matrix:
        self.names = OrderedDict(
            # Name: number of row, positions
            Index=(0, self.index_pos),
            Country=(1, self.country_pos),
            Region=(2, self.region_pos),
            Subregion=(3, self.subregion_pos),
            City=(4, self.city_pos),
            Street=(5, self.street_pos),
            House=(6, self.house_pos),
            Poi=(7, self.poi_pos)
        )

        # Penalties for absence of the address parts
        self.absences_penalty = OrderedDict(
            Index=(self.names['Index'][0], 1),
            Country=(self.names['Country'][0], 2),
            Region=(self.names['Region'][0], 3),
            Subregion=(self.names['Subregion'][0], 2),
            City=(self.names['City'][0], 13),
            Street=(self.names['Street'][0], 7),
            House=(self.names['House'][0], 5),
            Poi=(self.names['Poi'][0], 1)
        )

        # Create the score matrix: it is the matrix of ones and zeros.
        # self.names are mapped to rows of the matrix:
        # Index => the 0-th row of the matrix
        # Country => the 1st row ...

        rows = len(self.names)
        cols = len(self.address)
        m = np.zeros((rows, cols), dtype=np.byte)
        for name in self.names:
            row = self.names[name][0]
            begin, end = self.names[name][1] \
                if self.names[name][1] else (0, 0)

            if (not (0 <= begin < cols + 1)) or \
                    (not (begin <= end < cols + 1)):
                raise ValueError(u'Wrong input for "%s": the positions '
                                 u'doesn\'t match address string "%s"' %
                                 (name, self.address))

            m[row, begin:end] = 1
        self._score_matrix = m

    def __eq__(self, other):
        if self.address != other.address:
            return False
        if self.get_parsed_address() != other.get_parsed_address():
            return False
        return True

    def __ne__(self, other):
        return not self.__eq__(other)

    @property
    def index_name(self):
        return self.address[self.index_pos[0]:self.index_pos[1]] \
            if self.index_pos else None

    @property
    def country_name(self):
        return self.address[self.country_pos[0]:self.country_pos[1]] \
            if self.country_pos else None

    @property
    def region_name(self):
        return self.address[self.region_pos[0]:self.region_pos[1]] \
            if self.region_pos else None

    @property
    def subregion_name(self):
        return self.address[self.subregion_pos[0]:self.subregion_pos[1]] \
            if self.subregion_pos else None

    @property
    def city_name(self):
        return self.address[self.city_pos[0]:self.city_pos[1]] \
            if self.city_pos else None

    @property
    def street_name(self):
        return self.address[self.street_pos[0]:self.street_pos[1]] \
            if self.street_pos else None

    @property
    def house_num(self):
        return self.address[self.house_pos[0]:self.house_pos[1]] \
            if self.house_pos else None

    @property
    def poi_name(self):
        return self.address[self.poi_pos[0]:self.poi_pos[1]] \
            if self.poi_pos else None

    def get_parsed_address(self):
        address = Address(
            raw_address=self.address,
            index=self.index_name,
            country=self.country_name,
            region=self.region_name,
            subregion=self.subregion_name,
            settlement=self.city_name,
            street=self.street_name,
            house=self.house_num,
            poi=self.poi_name
        )

        return address

    def _get_space_penalty(self):
        """Penalty for spaces betweeen address parts.

        Resurns count of symbols between the first
        and the last parts of the address
        """
        sum_cols = self._score_matrix.sum(axis=0)
        nonzeros = np.where(sum_cols > 0)[0]     # Only one row is used
        if len(nonzeros) == 0:
            return 0
        left, right = nonzeros[0], nonzeros[-1]
        return right - left

    def get_score(self):
        """Return weight of strategy. (Small weight is better)

        Требования:
            Разные части адреса не должны пересекаться между собой
                (за каждое пересечение назначается штраф).
            Должно быть мало неиспользуемых символов в адресе
                (за каждый неиспользумый символ назначается штраф).
        """

        sum_cols = self._score_matrix.sum(axis=0)
        sum_rows = self._score_matrix.sum(axis=1)

        absence_p = 0
        for (idx, penalty) in self.absences_penalty.itervalues():
            if sum_rows[idx] == 0:
                absence_p += penalty

        overlapping = sum(sum_cols > 1)    # Count of overlapping symbols
        blank_count = sum(sum_cols == 0)   # Count of unused symbols

        return overlapping * self.overlap_penalty + \
            blank_count * self.blank_penalty + absence_p + \
            self.space_ratio * self._get_space_penalty()


class AddressSplitter(object):
    """Class for parse address line and split in address parts
    (Country, City, Region, etc)
    """

    def __init__(self,
                 country_list_file,
                 region_list_file,
                 subregion_list_file,
                 city_list_file,
                 street_list_file,
                 house_list_file,
                 poi_list_file):
        """
        :param country_list_file: file name for list of country names
        :param region_list_file:  file name for list of region names
        :param city_list_file:    file name for list of city names
        :param street_list_file:  file name for list of street names
        :param house_list_file:   file name for list of houses names
        :param poi_list_file:     file name for list of poi names

        The files must contain regular expressions for names. Check that
        the RE are:
            * lowercase
            * duplicates are removed
        """
        self.country_list = \
            {name: re.compile(r'\b' + name + r'\b', re.I | re.U)
             for name in self._read_list_file(country_list_file)}
        self.region_list = \
            {name: re.compile(r'\b' + name + r'\b', re.I | re.U)
             for name in self._read_list_file(region_list_file)}
        self.subregion_list = \
            {name: re.compile(r'\b' + name + r'\b', re.I | re.U)
             for name in self._read_list_file(subregion_list_file)}
        self.city_list = \
            {name: re.compile(r'\b' + name + r'\b', re.I | re.U)
             for name in self._read_list_file(city_list_file)}
        self.street_list = \
            {name: re.compile(r'\b' + name + r'\b', re.I | re.U)
             for name in self._read_list_file(street_list_file)}
        self.house_list = \
            {name: re.compile(r'\b' + name + r'\b', re.I | re.U)
             for name in self._read_list_file(house_list_file)}
        self.poi_list = \
            {name: re.compile(r'\b' + name + r'\b', re.I | re.U)
             for name in self._read_list_file(poi_list_file)}
        self.index = re.compile(r'\b' + '[0-9]{6}' + r'\b')

        self._address = ""   # caching variable
        self._parsed_address = None   # caching variable
        self._best_strat = None

    def _get_country_pos(self, address):
        """Return list of country positions in the address
        """
        return self._get_positions(address, self.country_list)

    def _get_region_pos(self, address):
        """Return list of region positions in the address
        """
        return self._get_positions(address, self.region_list)

    def _get_subregion_pos(self, address):
        """Return list of region positions in the address
        """
        return self._get_positions(address, self.subregion_list)

    def _get_city_pos(self, address):
        """Return list of city positions in the address
        """
        return self._get_positions(address, self.city_list)

    def _get_street_pos(self, address):
        """Return list of street positions in the address
        """
        return self._get_positions(address, self.street_list)

    def _get_house_pos(self, address):
        """Return list of house positions in the address
        """
        return self._get_positions(address, self.house_list)

    def _get_poi_pos(self, address):
        """Return list of house positions in the address
        """
        return self._get_positions(address, self.poi_list)

    def _get_index_pos(self, address):
        """Return list of index positions in the address
        """
        pos = {address[match.start(): match.end()]: [match.span()]
               for match in re.finditer(self.index, address)}
        return pos

    def _get_positions(self, address, patterns):
        """Return list of matching positions of patterns in string

        :param address:     Address string
        :param patterns:    List of patterns
        :return:
        """
        res = dict()
        address = address.lower()
        for name in patterns:
            positions = [{match.group(): match.span()}
                         for match in re.finditer(patterns[name], address)]
            for pos in positions:
                found_part = pos.keys()[0]    # Dict has one item only
                try:
                    res[found_part].append(pos[found_part])
                except KeyError:
                    res[found_part] = [pos[found_part]]

        return res

    def _read_list_file(self, filename):
        with open(filename) as f:
            names = [line.decode('utf-8').rstrip() for line in f]

        return names

    def _get_strategies(self, address):
        """Return list of splitting strategies:
        return list of all possible divisions of the address
        """

        # Find cross product of all possible positions of address parts
        # (add one 'None' position to all possible position: it allows
        # to elliminate dublicates of adress paerts)

        cntrs = self._get_country_pos(address)
        cntrs['None_position'] = [None]

        regns = self._get_region_pos(address)
        regns['None_position'] = [None]

        subregs = self._get_subregion_pos(address)
        subregs['None_position'] = [None]

        cities = self._get_city_pos(address)
        cities['None_position'] = [None]

        strts = self._get_street_pos(address)
        strts['None_position'] = [None]

        houses = self._get_house_pos(address)
        houses['None_position'] = [None]

        indxs = self._get_index_pos(address)
        indxs['None_position'] = [None]

        poi = self._get_poi_pos(address)
        poi['None_position'] = [None]

        parts = [p for p in [indxs, cntrs, regns,
                             subregs, cities, strts, houses, poi]]

        positions = [(indxs[s[0]] if s[0] else [None],
                      cntrs[s[1]] if s[1] else [None],
                      regns[s[2]] if s[2] else [None],
                      subregs[s[3]] if s[3] else [None],
                      cities[s[4]] if s[4] else [None],
                      strts[s[5]] if s[5] else [None],
                      houses[s[6]] if s[6] else [None],
                      poi[s[7]] if s[7] else [None])
                     for s in product(*tuple(parts))]

        strategies = []
        for pos in positions:
            s = [SplitingStrategy(
                address=address,
                index_pos=p[0],
                country_pos=p[1],
                region_pos=p[2],
                subregion_pos=p[3],
                city_pos=p[4],
                street_pos=p[5],
                house_pos=p[6],
                poi_pos=p[7])
                for p in product(*pos)
            ]
            strategies += s

        return strategies

    def get_best_strategy(self, address):
        """Return startegy with minimum weight
        """

        if self._address == address and self._best_strat:
            return self._best_strat

        strategies = self._get_strategies(address)
        w = [s.get_score() for s in strategies]
        best_ind = w.index(min(w))
        best = strategies[best_ind]

        self._address = address
        self._best_strat = best

        return best

    def get_parsed_address(self, address):
        """Parse address string and return an Address object.

        :param address:    Address string

        :returns:    Parsed address
        :rtype:      geocoder.algorithms.address.address.Address
        """
        # check the cache:
        if self._address == address and self._parsed_address:
            return self._parsed_address

        s = self.get_best_strategy(address)
        self._parsed_address = s.get_parsed_address()

        self._address = address

        return self._parsed_address

    def _drop_part(self, address, positions):
        """Change part of address: replace it by spaces
        """
        return address[:positions[0]] + \
            u' ' * (positions[1] - positions[0]) \
            + address[positions[1]:]

    def drop_index(self, address):
        s = self.get_best_strategy(address)
        if s.index_pos:
            return self._drop_part(address, s.index_pos)
        else:
            return address

    def _drop_parts(self, address):
        addr = address
        s = self.get_best_strategy(addr)
        addr = self.drop_index(addr)
        if s.country_pos:
            addr = self._drop_part(addr, s.country_pos)
        if s.region_pos:
            addr = self._drop_part(addr, s.region_pos)
        if s.subregion_pos:
            addr = self._drop_part(addr, s.subregion_pos)
        if s.city_pos:
            addr = self._drop_part(addr, s.city_pos)
        if s.street_pos:
            addr = self._drop_part(addr, s.street_pos)
        if s.house_pos:
            addr = self._drop_part(addr, s.house_pos)

        m = re.search('^[, ]+', addr)
        if m:
            addr = addr[: m.start()] + addr[m.end():]

        return addr


if __name__ == '__main__':
    '''Main function is used as an example only.
    Import the necessary class to your project and use it in the project.
    '''

    from progressbar import ProgressBar, Bar, Counter, ETA

    datafile = sys.argv[1]
    delimiter = ","
    if len(sys.argv) >= 3:
        delimiter = sys.argv[2]

    path = 'csv_files/'
    splitter = AddressSplitter(
        country_list_file=path + 'countries.csv',
        region_list_file=path + 'regions.csv',
        subregion_list_file=path + 'subregions.csv',
        # city_list_file=path + 'cities_big.csv',
        city_list_file=path + 'cities.csv',
        street_list_file=path + 'streets.csv',
        house_list_file=path + 'houses.csv'
    )

    num_lines = sum(1 for line in open(datafile))
    pbar = ProgressBar(
        widgets=[
            Bar('=', '[', ']'), ' ', Counter(),
            " of " + str(num_lines), ' ', ETA()]
    ).start()
    pbar.maxval = num_lines

    with open(datafile) as data:
        for address in data:
            pbar.update(pbar.currval + 1)
            line_text = address.decode('utf-8')
            address = address.decode('utf-8')
            parced_address = splitter.get_parsed_address(address)
            if parced_address.index is None:
                parced_address.index = ""
            if parced_address.country is None:
                parced_address.country = ""
            if parced_address.region is None:
                parced_address.region = ""
            if parced_address.subregion is None:
                parced_address.subregion = ""
            if parced_address.settlement is None:
                parced_address.settlement = ""
            if parced_address.street is None:
                parced_address.street = ""
            if parced_address.house is None:
                parced_address.house = ""
            result = delimiter.join([line_text, parced_address.index,
                                     parced_address.country,
                                     parced_address.region,
                                     parced_address.subregion,
                                     parced_address.settlement,
                                     parced_address.street,
                                     parced_address.house])
            print result.encode('utf-8')
    pbar.finish()
