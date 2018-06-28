# joint_states.py
#
# Copyright (c) 2018, Xamla and/or its affiliates. All rights reserved.
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

#!/usr/bin/env python

from __future__ import (absolute_import, division,
                        print_function)
#from future.builtins import *
from future.utils import raise_from, raise_with_traceback

from data_types import JointValues


class JointStates(object):

    """
    Class which holds can hold a complete JointState (pos, vel, eff)

    The JointState class can hold the complete information about a
    the state of joints of a robot. For this purpose it holds an 
    instance of JointValues for positions, velocities, and efforts
    (velocities and efforts are optional)

    Attributes
    ----------
    joint_set : JointSet (read only)
        Set of joints for which it holds the values
    positions : JointValues (read only)
        Joint Values which defines the positions of the joints
    velocities : JointValues (read only)
        Joint Values which defines the velocities of the joints
    efforts : JointValues (read only)
        Joint Values which defines the efforts / acceleration of the joints
    """

    def __init__(self, positions, velocities=None, efforts=None):
        """
        Initialization of JointStates class

        Parameters
        ----------
        positions : Joint_Values
            A instance of JointValues which represent the positions
        velocities : Joint_Values or None (optional)
            A instance of JointValues which represent the velocities
        efforts : Joint_Values or None (optional)
            A instance of JointValues which represent the efforts


        Yields
        ------
        JointStates
            Creates an instance of JointStates

        Raises
        ------
        TypeError : type mismatch
            If arguments are not of type JointValues
        ValueError
            If instances of JointValues does not hold the
            same JointSets (joint names and order)
        """

        self.__positions = self._init_check(positions,
                                            'positions',
                                            False)

        self.__velocities = None
        self.__efforts = None

        if velocities != None:
            self.__velocities = self._init_check(velocities,
                                                 'velocities')

        if efforts != None:
            self.__efforts = self._init_check(efforts,
                                              'efforts')

    def _init_check(self, joint_values, name, check=True):
        if not isinstance(joint_values, JointValues):
            raise TypeError(name+' is not of expected type JointValues')

        if check == True:
            if joint_values.joint_set != self.joint_set:
                raise ValueError('joint names or order do not match.')

        return joint_values

    @property
    def joint_set(self):
        return self.__positions.joint_set

    @property
    def positions(self):
        """JointValues which defines the positions readonly"""
        return self.__positions

    @property
    def velocities(self):
        """JointValues which defines the velocities readonly"""
        return self.__velocities

    @property
    def efforts(self):
        """
        JointValues which defines the efforts/acceleration readonly
        if not available returns None
        """
        return self.__efforts

    def reorder(self, new_order):
        """
        Creates reordered instance of JointValue by the order of new_order

        Parameters
        ----------
        new_order : JointSet
            JointSet which defines the new order

        Yields
        ------
        JointStates
            A new Instance of JointStates containing the
            joints in the order definied by new_order
            (it is ok when new_order only holds a subset of joints)

        Raises
        ------
        TypeError : type mismatch
            If input parameter new_order is not of type JointSet
        ValueError :
            If joint name from new_order not exists
        """

        positions = self.__positions.reorder(new_order)
        velocities = self.__velocities.reorder(new_order)
        efforts = self.__efforts.reorder(new_order)

        return JointStates(positions, velocities, efforts)

    def select(self, names):
        """
        Creates a JointStates instance which only contains selected joints

        Parameters
        ----------
        names : str or list of str or JointSet
            Joint names which should be in the new JointValues instance


        Yields
        ------
        JointValues
            New instance of JointValues with selected joints

        Raises
        ------
        TypeError : type mismatch
            If names is not of type str or list of str
        ValueError :
            If name not exist in joint names
        """
        try:
            if isinstance(names, JointSet):
                return self.reorder(names)
            elif isinstance(names, str):
                positions = self.__positions[self.joint_set.get_index_of(
                    names)]
                velocities = self.__velocities[self.joint_set.get_index_of(
                    names)]
                efforts = self.__efforts[self.joint_set.get_index_of(names)]
            elif names and all(isinstance(s, str) for s in names):
                positions = np.zeros(len(names), self.__positions.dtype)
                velocities = np.zeros(len(names), self.__velocities.dtype)
                efforts = np.zeros(len(names), self.__efforts.dtype)
                for i, name in enumerate(names):
                    positions[i] = self.__positions[self.joint_set.get_index_of(
                        name)]
                    velocities[i] = self.__velocities[self.joint_set.get_index_of(
                        name)]
                    efforts[i] = self.__efforts[self.joint_set.get_index_of(
                        name)]
            else:
                raise TypeError('names is not one of the expected types'
                                ' str or list of strs or JointSet')
            return self.__class__(JointSet(names), positions, velocities,
                                  efforts)
        except ValueError as exc:
            raise_from(ValueError('name ' + name +
                                  ' not exist in joint names'), exc)

    def __len__(self):
        return len(self.__positions)

    def __str__(self):
        ss = '\n'.join([k+' = '+str(v) for k, v in self.__dict__.items()])
        ss = ss.replace('_'+self.__class__.__name__+'__', '')
        ss = ss.replace('\n', '\n  ')
        return 'JointStates\n'+ss

    def __repr__(self):
        return self.__str__()
