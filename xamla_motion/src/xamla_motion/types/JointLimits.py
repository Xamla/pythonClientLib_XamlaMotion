#!/usr/bin/env python

from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
from future.builtins import *

from copy import deepcopy
import numpy as np

from JointSet import JointSet


class JointLimits(object):
    """
    Manages the joint limits for a set of joints

    Attributes
    ----------
    joint_set : JointSet (readonly)
        A instance of JointSet managing joint names
    max_velocity : list of float or numpy.array(dtype=floating)
        One dimension array which defines the maximal
        velocity for each joint (readonly)
    max_acceleration : list of float or numpy.array(dtype=floating)
        One dimension array which defines the maximal
        acceleration for each joint (readonly)
    min_position : list of float or numpy.array(dtype=floating)
        One dimension array which defines the mininmal
        position for each joint (readonly)
    max_position : list of float or numpy.array(dtype=floating)
        One dimension array which defines the maximal
        position for each joint (readonly)

    Methods
    -------
    select(names)
        Creates a JointLimits instance which only contains selected joints
    """

    def __init__(self, joint_set, max_velocity, max_acceleration,
                 min_position, max_position):
        """
        Initialization of JointLimits class

        If a specific joint has no limits for velocity, acceleration or position
        than please set them to None (for list) or numpy.nan (for numpy.ndarray)
        the specific joint has than no contrain for this limit

        Parameters
        ----------
        joint_set : JointSet
            Set of joints for which joint limits are required
        max_velocity : list of float or numpy.array(dtype=floating)
            One dimension array which defines
            the maximal velocity for each joint
        max_acceleration : list of float or numpy.array(dtype=floating)
            One dimension array which defines
            the maximal acceleration for each joint
        min_position : list of float or numpy.array(dtype=floating)
            One dimension array which defines
            the mininmal position for each joint
        max_position : list of float or numpy.array(dtype=floating)
            One dimension array which defines
            the maximal position for each joint

        Yields
        ------
        JointLimits
            An instance of class JointLimits

        Raises
        ------
        TypeError : type mismatch
            If joint_set is not of type JointSet or
            max/min values are not of type list of float
            or numpy array of type floating
        ValueError : not same size
            If max/min values are list of float and not contains the same number
            of items as joint_set or numpy array that has not the correct size
        """
        if not isinstance(joint_set, JointSet):
            raise TypeError('joint_set is not of expected type JointSet')

        self.__joint_set = joint_set

        # max_velocity
        try:
            try:
                if len(max_velocity) <= 1:
                    raise ValueError('max one value is provided')
            except (TypeError, ValueError) as exc:
                if isinstance(exc, TypeError):
                    max_velocity = [max_velocity] * self.__joint_set.count()
                else:
                    max_velocity = max_velocity * self.__joint_set.count()

            if len(max_velocity) != joint_set.count():
                raise ValueError('joint set holds ' +
                                 str(self.__joint_set.count()) +
                                 ' joints but only ' + str(len(max_velocity)) +
                                 ' velocities are provided')
            self.__max_velocity = np.fromiter(max_velocity, float)
        except (TypeError, ValueError) as exc:
            raise exc

        # max_acceleration
        try:
            try:
                if len(max_acceleration) <= 1:
                    raise ValueError('max one value is provided')
            except (TypeError, ValueError) as exc:
                if isinstance(exc, TypeError):
                    max_acceleration = [max_acceleration] * \
                        self.__joint_set.count()
                else:
                    max_acceleration = max_acceleration*self.__joint_set.count()

            if len(max_acceleration) != joint_set.count():
                raise ValueError('joint set holds ' +
                                 str(self.__joint_set.count()) +
                                 ' joints but only '+str(len(max_acceleration)) +
                                 ' accelerations are provided')
            self.__max_acceleration = np.fromiter(max_acceleration, float)
        except (TypeError, ValueError) as exc:
            raise exc

        # min_position
        try:
            try:
                if len(min_position) <= 1:
                    raise ValueError('max one value is provided')
            except (TypeError, ValueError) as exc:
                if isinstance(exc, TypeError):
                    min_position = [min_position] * self.__joint_set.count()
                else:
                    min_position = min_position * self.__joint_set.count()

            if len(min_position) != joint_set.count():
                raise ValueError('joint set holds ' +
                                 str(self.__joint_set.count()) +
                                 ' joints but only ' + str(len(min_position)) +
                                 ' min positions are provided')
            self.__min_position = np.fromiter(min_position, float)
        except (TypeError, ValueError) as exc:
            raise exc

        # max_position
        try:
            try:
                if len(max_position) <= 1:
                    raise ValueError('max one value is provided')
            except (TypeError, ValueError) as exc:
                if isinstance(exc, TypeError):
                    max_position = [max_position] * self.__joint_set.count()
                else:
                    max_position = max_position * self.__joint_set.count()

            if len(max_position) != joint_set.count():
                raise ValueError('joint set holds ' +
                                 str(self.__joint_set.count()) +
                                 ' joints but only ' + str(len(max_position)) +
                                 ' max positions are provided')
            self.__max_position = np.fromiter(max_position, float)
        except (TypeError, ValueError) as exc:
            raise exc

        self.__max_velocity.flags.writeable = False
        self.__max_acceleration.flags.writeable = False
        self.__min_position.flags.writeable = False
        self.__max_position.flags.writeable = False

    @property
    def joint_set(self):
        """read only joint_set"""
        return self.__joint_set

    @property
    def max_velocity(self):
        """read only maxmimal velocity"""
        return self.__max_velocity

    @property
    def max_acceleration(self):
        """read only maximal acceleration"""
        return self.__max_acceleration

    @property
    def min_position(self):
        """read only min position"""
        return self.__min_position

    @property
    def max_position(self):
        """read only max position"""
        return self.__max_position

    def select(self, names):
        """
        Creates a JointLimits instance which only contains selected joints

        Parameters
        ----------
        names : str or list of str
            Joint names which from the new JointLimit instance


        Yields
        ------
        JointLimits
            New instance of JointLimits with selected joints

        Raises
        ------
        TypeError : type mismatch
            If names is not of type str or list of str
        ValueError :
            If name not exist in joint names
        """
        try:
            if isinstance(names, str):
                names = (names)

            if names and all(isinstance(s, str) for s in names):
                max_velocity = np.zeros(len(names), self.__max_velocity.dtype)
                max_acceleration = np.zeros(
                    len(names), self.__max_acceleration.dtype)
                min_position = np.zeros(len(names), self.__min_position.dtype)
                max_position = np.zeros(len(names), self.__max_position.dtype)
                for i, name in enumerate(names):
                    index = self.__joint_set.get_index_of(name)
                    max_velocity[i] = self.__max_velocity[index]
                    max_acceleration[i] = self.__max_acceleration[index]
                    min_position[i] = self.__min_position[index]
                    max_position[i] = self.__max_position[index]
            else:
                raise TypeError('names is not one of the expected types'
                                ' str or list of str')
            return self.__class__(JointSet(names), max_velocity, max_acceleration,
                                  min_position, max_position)
        except ValueError as exc:
            raise_from(ValueError('joint name ' + name +
                                  ' not exist in joint names'), exc)

    def __deepcopy__(self, memo):
        cls = self.__class__
        result = cls.__new__(cls)
        memo[id(self)] = result
        for k, v in self.__dict__.items():
            setattr(result, k, deepcopy(v, memo))
        for k, v in result.__dict__.items():
            if isinstance(v, np.ndarray):
                v.flags.writeable = False
        return result

    def __iter__(self):
        return (self.__max_velocity.__iter__(),
                self.__max_acceleration.__iter__(),
                self.__min_position.__iter__(),
                self.__max_position.__iter__())

    def __str__(self):
        j_str = '\n'.join([name + ' :  max velocity=' +
                           str(self.__max_velocity[i]) + ' max acceleration=' +
                           str(self.__max_acceleration[i]) + ' min position=' +
                           str(self.__min_position[i]) + ' max position=' +
                           str(self.__max_position[i])
                           for i, name in enumerate(self.__joint_set)])
        return 'JointLimits:\n' + j_str

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        r_tol = 1.0e-13
        a_tol = 1.0e-14

        if not isinstance(other, self.__class__):
            return False

        if id(other) == id(self):
            return True

        if other.join_set != self.__joint_set:
            return False

        if not np.allclose(self.__max_velocity, other.max_velocity,
                           rtol=r_tol, atol=a_tol):
            return False

        if not np.allclose(self.__max_acceleration, other.max_acceleration,
                           rtol=r_tol, atol=a_tol):
            return False

        if not np.allclose(self.__min_position, other.min_position,
                           rtol=r_tol, atol=a_tol):
            return False

        if not np.allclose(self.__max_position, other.max_position,
                           rtol=r_tol, atol=a_tol):
            return False
        return True

    def __ne__(self, other):
        return not self.__eq__(other)
