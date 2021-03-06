# joint_trajectory_points.py
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

#!/usr/bin/env python3

from datetime import timedelta
from typing import Iterable
import numpy as np
import rospy

from .joint_set import JointSet
from .joint_values import JointValues
import trajectory_msgs.msg


class JointTrajectoryPoint(object):
    """
    Class JointTrajectoryPoint

    Methods
    -------
    from_joint_trajectory_point_msg(joint_set, msg)
        Creates an instance of JointTrajectoryPoint from ros message
    add_time_offset(offset)
        Creates a new instance of this JointTrajectoryPoint with same
        position, vel, acc, eff but with a modified time_from_start
    merge(others)
        Creates a new instance of JointTrajectory as a result of the merge operation
    to_joint_trajectory_point_msg()
        Converts JointTrajectoryPoint to JointTrajectoryPoint ros message
    """

    def __init__(self, time_from_start, positions, velocities=None,
                 accelertations=None, efforts=None):
        """
        Initialize JointTrajectoryPoint class

        Parameters
        ----------
        time_from_start : datatime.timedelta
            duration between start of trajectory and this point
        positions : JointValues
            joint positions
        velocities : JointValues or None
            joint velocities
        accelerations : JointValues
            joint accelerations
        efforts : JointValues
            joint force for a prismatic joint or torque
            for a rotational joint

        Returns
        -------
        JointTrajectoryPoint
            Instance of JointTrajectoryPoint

        Raises
        ------
        TypeError : type mismatch
            If time_from_start is not of expected type datatime.timedelta
            or if positions is not of expected type JointValues
            or if velocities, accelerations or efforts ist not one
            of the expected types None or JointValues
        ValueError
            If the joint set of positions and if not None
            velocities, accelerations and efforts is not equal
        """

        if not isinstance(time_from_start, timedelta):
            raise TypeError('time_from_start is not of'
                            ' expected type timedelta')

        self.__time_from_start = time_from_start

        self.__positions = self._init_check(positions, 'positions', False)
        self.__velocities = self._init_check(velocities, 'velocities')
        self.__accelerations = self._init_check(accelertations,
                                                'accelerations')
        self.__efforts = self._init_check(efforts, 'efforts')

    def _init_check(self, joint_values, name, check=True):
        if not joint_values:
            return None

        if not isinstance(joint_values, JointValues):
            raise TypeError(name+' is not of expected type JointValues')

        if check == True:
            if joint_values.joint_set != self.joint_set:
                raise ValueError('joint names or order do not match.')

        return joint_values

    @classmethod
    def from_joint_trajectory_point_msg(cls, joint_set, msg):
        """
        Creates an instance of JointTrajectoryPoint from ros message

        Creates an instance of JointTrajectoryPoint from the ros message
        trajectory_msgs/JointTrajectoryPoint

        Parameters
        ----------
        joint_set : JointSet
            Set of joints for which the trajectroy point is defined
        msg : trajectory_msgs/JointTrajectoryPoint
            Instance of ros message that should be converted to
            JointTrajectoryPoint

        Returns
        -------
        JointTrajectoryPoint
            New instance of JointTrajectoryPoint with the values
            of the ros message

        Raises
        ------
        TypeError : type mismatch
            If values from msg are not convertable to numpy
            array of type floating or if joint_set is not of
            expected type JointSet
        """

        if not isinstance(joint_set, JointSet):
            raise TypeError('joint_set is not of expected type JointSet')

        j_positions = JointValues(joint_set, msg.positions)
        j_velocity = cls._init_from_msg_helper(joint_set, msg.velocities)
        j_accelerations = cls._init_from_msg_helper(joint_set,
                                                    msg.accelerations)
        j_effort = cls._init_from_msg_helper(joint_set, msg.effort)

        days = msg.time_from_start.secs // (24*3600)
        seconds = msg.time_from_start.secs % (24*3600)
        microseconds = msg.time_from_start.nsecs // 1000

        time_from_start = timedelta(days=days, seconds=seconds,
                                    microseconds=microseconds)

        return cls(time_from_start, j_positions, j_velocity,
                   j_accelerations, j_effort)

    @staticmethod
    def _init_from_msg_helper(joint_set, values):
        if values:
            return JointValues(joint_set, values)
        else:
            return None

    @property
    def joint_set(self):
        """
        joint_set : JointSet
            Set of joints for which the trajectory point contains values
        """
        return self.__positions.joint_set

    @property
    def time_from_start(self):
        """
        time_from_start : datetime.timedelta (readonly)
            Time span between trajectory start and this trajectory
            point as a instance of datetime.timedelta
        """
        return self.__time_from_start

    @property
    def positions(self):
        """
        positions : JointValues (readonly)
            Joint positions of this trajectory point
        """
        return self.__positions

    @property
    def velocities(self):
        """
        velocities : JointValues (readonly)
            If defined available joint velocites of this trajectory point
            else None
        """
        return self.__velocities

    @property
    def accelerations(self):
        """
        accelerations : JointValues (readonly)
            If defined available joint accelerations of this trajectory point
            else None
        """
        return self.__accelerations

    @property
    def efforts(self):
        """
        efforts : JointValues (readonly)
            If defined available joint efforts of this trajectory point
            else None
        """
        return self.__efforts

    def add_time_offset(self, offset):
        """
        Creates a new instance of JointTrajectoryPoint with applied time offset

        adds a time offset to time_from_start

        Parameters
        ----------
        offset : datatime.timedelta
            time offset as datatime timedelta

        Returns
        -------
            Instance of JointTrajectoryPoint with modified time_from_start

        Raises
        ------
        TypeError
            If offset ist not of expected type datatime.timedelta
        """
        if not isinstance(offset, timedelta):
            raise TypeError('offset is not of expected'
                            ' type datatime.timedelta')

        time_from_start = self.__time_from_start + offset

        return self.__class__(time_from_start,
                              self.__positions,
                              self.__velocities,
                              self.__accelerations,
                              self.__efforts)

    def with_time_from_start(self, time: timedelta):
        """
        Set time from start

        Parameters
        ----------
        time : timedelta
            time form start to set

        Returns
        -------
        JointTrajectoryPoint
        """

        return type(self)(time,
                          self.__positions,
                          self.__velocities,
                          self.__accelerations,
                          self.__efforts)

    def merge(self, others):
        """
        Creates a new instance of JointTrajectoryPoint as a result of the merge operation

        Parameters
        ----------
        others: JointTrajectoryPoint or Iterable[JointTrajectoryPoint]
            TrajectoryPoints to merge with the current TrajectoryPoint

        Returns
        -------
        JointTrajectoryPoint:
            New instance of JointTrajectoryPoint which contains the merged
            JointTrajectoryPoints

        Raises
        ------
        TypeError : type mismatch
            If other not one of excpeted types JointTrajectoryPoint or
            Iterable[JointTrajectoryPoint]
        ValueError
            If time_from_start in self and others dont match
            If JointSets of self and others are not mergeable
            If self and others define more or less properties
            of JointTrajectoryPoint
        """
        def check_values(a, b, name):
            if not a:
                if b:
                    raise ValueError('merge conflict, ' + name + ' are defined'
                                     ' in others but not in self')
                return False
            else:
                if not b:
                    raise ValueError('merge conflict, ' + name + ' are defined'
                                     'in self but not in others')
                return True

        velocites = None
        accelerations = None
        efforts = None

        if isinstance(others, JointTrajectoryPoint):
            if self.__time_from_start != others.time_from_start:
                raise ValueError('merge conflict, time_from_start in others'
                                 ' is not equal to self time_from_start')

            positions = self.__positions.merge(others.positions)

            if check_values(self.__velocities, others.velocities, 'velocities'):
                velocites = self.__velocities.merge(others.velocities)
            if check_values(self.__accelerations, others.accelerations, 'accelerations'):
                velocites = self.__accelerations.merge(others.accelerations)
            if check_values(self.__efforts, others.efforts, 'efforts'):
                velocites = self.efforts.merge(others.efforts)

        elif (isinstance(others, Iterable) and
              all(isinstance(v, JointTrajectoryPoint) for v in others)):
            time_not_equal = list(map(lambda x: x.time_from_start !=
                                      self.__time_from_start, others))
            if any(time_not_equal):
                raise ValueError('time_from_start of others: {} is not'
                                 ' equal to self '
                                 'time_from_start'.format(time_not_equal))

            positions = self.__positions.merge(
                list(map(lambda x: x.positions, others)))

            check_velocities = list(map(lambda x: check_values(
                self.__velocities, x.velocities, 'velocities'), others))
            if all(check_velocities):
                velocites = self.__velocities.merge(
                    list(map(lambda x: x.velocities, others)))

            check_accelerations = list(map(lambda x: check_values(
                self.__accelerations, x.accelerations, 'accelerations'), others))
            if all(check_accelerations):
                accelerations = self.__accelerations.merge(
                    list(map(lambda x: x.accelerations, others)))

            check_efforts = list(map(lambda x: check_values(
                self.__efforts, x.efforts, 'efforts'), others))
            if all(check_efforts):
                efforts = self.__efforts.merge(
                    list(map(lambda x: x.efforts, others)))

        else:
            raise TypeError('others is not one of expected types '
                            'JointTrajectoryPoint or '
                            'Iterable[JointTrajectoryPoint]')

        return self.__class__(self.__time_from_start, positions,
                              velocites, accelerations, efforts)

    def interpolate_cubic(self, other: 'JointTrajectoryPoint', time: timedelta):
        """
        Interpolate cubic between self and other trajectory point

        Parameters
        ----------
        other: JointTrajectoryPoint
            Second trajectory point for interpolation
        time: timedelta
            time for which interpolation is performed

        Returns
        -------
        JointTrajectoryPoint

        Raises
        ------
        ValueError
            If time from start of point is smaller than time from start of self
            If joint sets of point and self are not equal
        """
        if self.joint_set != other.joint_set:
            raise ValueError('joint set of self: {} and other: {}'
                             ' are not equal'.format(self.joint_set,
                                                     other.joint_set))

        t0 = self.time_from_start
        t1 = other.time_from_start

        if t1 <= t0:
            raise ValueError('interpolation error: other time from start {} is'
                             ' smaller than self time from start {}'.format(t1,
                                                                            t0))

        delta_t = t1 - t0

        if delta_t.total_seconds() < 1e-6:
            return type(self)(t0+delta_t,
                              other.positions,
                              other.velocities,
                              other.accelerations,
                              other.efforts)

        t = max((time - t0).total_seconds(), 0.0)
        t = min(delta_t.total_seconds(), t)

        if self.velocities is None or other.velocities is None:
            raise ValueError

        dt = delta_t.total_seconds()

        pos = np.zeros(len(self.positions), dtype=float)
        vel = np.zeros(len(self.velocities), dtype=float)

        zipped = zip(self.positions,
                     other.positions,
                     self.velocities,
                     other.velocities)
        for i, (p0, p1, v0, v1) in enumerate(zipped):
            c = (-3.0*p0 + 3.0*p1 - 2.0*dt*v0 - dt*v1) / dt**2.0
            d = (2.0*p0 - 2.0*p1 + dt*v0 + dt*v1) / dt**3.0
            pos[i] = p0 + v0*t + c*t**2.0 + d*t**3.0
            vel[i] = v0 + 2.0*c*t + 3.0*d*t**2.0

        return type(self)(time,
                          JointValues(self.joint_set, pos),
                          JointValues(self.joint_set, vel))

    def to_joint_trajectory_point_msg(self):
        """
        Converts JointTrajectoryPoint to JointTrajectoryPoint ros message

        trajectory_msgs/JointTrajectoryPoint.msg

        Returns
        -------
        JointTrajectoryPoint msg
            New instance of JointTrajectoryPoint with the values
            of the ros message

        """
        msg = trajectory_msgs.msg.JointTrajectoryPoint()

        msg.positions = list(self.__positions.values)
        if self.__velocities:
            msg.velocities = list(self.__velocities.values)
        if self.__accelerations:
            msg.accelerations = list(self.__accelerations.values)
        if self.__efforts:
            msg.effort = list(self.__efforts.values)

        secs = (self.__time_from_start.days * 24*3600 +
                self.__time_from_start.seconds)
        nsecs = self.__time_from_start.microseconds * 1000
        msg.time_from_start = rospy.Duration(secs, nsecs)

        return msg

    def __str__(self):
        s = '\n'.join(['  '+k+' = ' + str(v)
                       for k, v in self.__dict__.items()])
        s = s.replace('_'+self.__class__.__name__+'__', '')
        return self.__class__.__name__+'\n'+s

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False

        if id(other) == id(self):
            return True

        if other.time_from_start != self.__time_from_start:
            return False

        if other.positions != self.__positions:
            return False

        if other.velocites != self.__velocities:
            return False

        if other.accelerations != self.__accelerations:
            return False

        if other.efforts != self.__efforts:
            return False

        return True

    def __ne__(self, other):
        return not self.__eq__(other)
