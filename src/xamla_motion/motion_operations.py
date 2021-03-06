# motion_operations.py
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

# later replace with dataclass in python3.6 > available

import asyncio
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Callable, Union

import numpy as np

from .data_types import (CartesianPath, JointPath, JointTrajectory,
                         JointValues, PlanParameters, Pose)
from .motion_service import SteppedMotionClient
from .xamla_motion_exceptions import ServiceException

if TYPE_CHECKING:
    from xamla_motion.v2.motion_client import EndEffector, MoveGroup


class MoveArgs(object):
    """
    Base move data class to exchange between client and operation classes

    All properties are initialized with None
    """

    def __init__(self):
        self._move_group = None
        self._velocity_scaling = None
        self._acceleration_scaling = None
        self._collision_check = None
        self._sample_resolution = None
        self._max_deviation = None

    @property
    def move_group(self) -> 'xamla_motion.v2.MoveGroup':
        return self._move_group

    @move_group.setter
    def move_group(self, move_group: 'xamla_motion.v2.MoveGroup'):
        self._move_group = move_group

    @property
    def velocity_scaling(self) -> float:
        return self._velocity_scaling

    @velocity_scaling.setter
    def velocity_scaling(self, velocity_scaling: float):
        self._velocity_scaling = velocity_scaling

    @property
    def acceleration_scaling(self) -> float:
        return self._acceleration_scaling

    @acceleration_scaling.setter
    def acceleration_scaling(self, acceleration_scaling: float):
        self._acceleration_scaling = acceleration_scaling

    @property
    def collision_check(self) -> bool:
        return self._collision_check

    @collision_check.setter
    def collision_check(self, collision_check: bool):
        self._collision_check = collision_check

    @property
    def sample_resolution(self) -> float:
        return self._sample_resolution

    @sample_resolution.setter
    def sample_resolution(self, sample_resolution: float):
        self._sample_resolution = sample_resolution

    @property
    def max_deviation(self) -> float:
        return self._max_deviation

    @max_deviation.setter
    def max_deviation(self, max_deviation: float):
        self._max_deviation = max_deviation


class MoveJointsArgs(MoveArgs):
    """
    Move joints data class to exchange between client and operation classes

    All properties are initialized with None
    """

    def __init__(self):
        super(MoveJointsArgs, self).__init__()

        self._start = None
        self._target = None

    @property
    def start(self) -> Union[None, JointValues]:
        return self._start

    @start.setter
    def start(self, start: Union[None, JointValues]):
        self._start = start

    @property
    def target(self) -> Union[None, JointValues, JointPath]:
        return self._target

    @target.setter
    def target(self, target: Union[None, JointValues, JointPath]):
        self._target = target


class MoveCartesianArgs(MoveJointsArgs):
    """
    Move cartesian data class to exchange between client and operation classes

    All properties are initialized with None
    """

    def __init__(self):
        super(MoveCartesianArgs, self).__init__()

        self._end_effector = None
        self._seed = None
        self._ik_jump_threshold = None

    @property
    def end_effector(self) -> 'xamla_motion.v2.EndEffector':
        return self._end_effector

    @end_effector.setter
    def end_effector(self, end_effector: 'xamla_motion.v2.EndEffector'):
        self._end_effector = end_effector

    @property
    def start(self) -> Union[None, JointValues, Pose]:
        return self._start

    @start.setter
    def start(self, start: Union[None, JointValues, Pose]):
        self._start = start

    @property
    def target(self) -> Union[None, Pose, CartesianPath]:
        return self._target

    @target.setter
    def target(self, target: Union[None, JointValues, JointPath]):
        self._target = target

    @property
    def seed(self) -> JointValues:
        return self._seed

    @seed.setter
    def seed(self, seed: JointValues):
        self._seed = seed

    @property
    def ik_jump_threshold(self) -> float:
        return self._ik_jump_threshold

    @ik_jump_threshold.setter
    def ik_jump_threshold(self, ik_jump_threshold: float):
        self._ik_jump_threshold = ik_jump_threshold


class Plan(object):
    """
    Plan holds a planned trajectory and offer methods for path execution
    """

    def __init__(self, move_group: 'xamla_motion.v2.MoveGroup',
                 trajectory: JointTrajectory,
                 parameters: PlanParameters):
        """
        Initialization of Plan

        Parameters
        ----------
        move_group : xamla_motion.v2.MoveGroup
            Move group which should execute the trajectory
        trajectory : JointTrajectory
            Planned trajectory which should be executed
        parameters : PlanParameters
            Defines properties and limits with which the
            trajectory is planned

        Returns
        -------
        Plan
            Instance of Plan
        """
        self._move_group = move_group
        self._trajectory = trajectory
        self._parameters = parameters

    @property
    def move_group(self):
        """
        move_group : xamla_motion.v2.MoveGroup (read only)
            Move group which executes the trajectory
        """
        return self._move_group

    @property
    def trajectory(self):
        """
        trajectory : JointTrajectory
            Trajectory which is the execution target
        """
        return self._trajectory

    @property
    def parameters(self):
        """
        parameters : PlanParameters
            PlanParameters with which the trajectory was planned
        """
        return self._parameters

    def execute_async(self) -> asyncio.Task:
        """
        Executes trajectory asynchronously

        Returns
        -------
        Task : asyncio.Task
            Task which asynchronously execute trajectory

        Raises
        ------
        TypeError
            If trajectory is not of type JointTrajectory
            or if collision_check is not convertable to bool
        ServiceException
            If execution ends not successful
        """
        services = self._move_group.motion_service
        return asyncio.ensure_future(services.execute_joint_trajectory(self._trajectory,
                                                                       self._parameters.collision_check))

    def execute_supervised(self):
        """
        Creates executor for supervised trajectory execution

        Returns
        -------
        SteppedMotionClient
            Executor client for supervised trajectory execution
        """
        services = self._move_group.motion_service
        return services.execute_joint_trajectory_supervised(self._trajectory,
                                                            1.0,
                                                            self._parameters.collision_check)


class MoveOperation(ABC):

    def __init__(self, args):
        """
        Initialize common move operation args
        """
        self._start = args.start
        self._target = args.target
        self._move_group = args.move_group
        self._velocity_scaling = args.velocity_scaling
        self._acceleration_scaling = args.acceleration_scaling
        p = self._move_group._build_plan_parameters(self._velocity_scaling,
                                                    args.collision_check,
                                                    args.max_deviation,
                                                    self._acceleration_scaling,
                                                    args.sample_resolution)
        self._plan_parameters = p

    @property
    def move_group(self) -> 'xamla_motion.v2.MoveGroup':
        """
        move_group : xamla_motion.v2.MoveGroup (read only)
            selected move group for move operation
        """
        return self._move_group

    @property
    def velocity_scaling(self) -> float:
        """
        velocity_scaling : float (read only)
            current velocity_scaling
        """
        return self._velocity_scaling

    @property
    def acceleration_scaling(self) -> float:
        """
        acceleration_scaling : float
            current acceleration scaling
        """
        return self._acceleration_scaling

    @property
    def plan_parameters(self) -> PlanParameters:
        """
        plan_parameters : PlanParameters
            current plan parameters
        """
        return self._plan_parameters

    @abstractmethod
    def plan(self):
        pass

    @abstractmethod
    def _build(self, args):
        pass

    @abstractmethod
    def _with_parameters(self, func):
        pass

    @abstractmethod
    def with_start(self, value):
        if value != self._start:
            def f(x):
                x.start = value
                return x
            return self._with_parameters(f)
        else:
            return self

    @abstractmethod
    def with_collision_check(self, value: bool=True):
        if value != self._plan_parameters.collision_check:
            def f(x):
                x.collision_check = value
                return x
            return self._with_parameters(f)

    @abstractmethod
    def with_velocity_scaling(self, value: float):
        if value != self._velocity_scaling:
            def f(x):
                x.velocity_scaling = value
                return x
            return self._with_parameters(f)
        else:
            return self

    @abstractmethod
    def with_acceleration_scaling(self, value: float):
        if value != self._acceleration_scaling:
            def f(x):
                x.acceleration_scaling = value
                return x
            return self._with_parameters(f)
        else:
            return self

    @abstractmethod
    def with_sample_resolution(self, value: float):
        if value != self._plan_parameters.sample_resolution:
            def f(x):
                x.sample_resolution = value
                return x
            return self._with_parameters(f)
        else:
            return self

    @abstractmethod
    def with_max_deviation(self, value: float):
        if value != self._plan_parameters.max_deviation:
            def f(x):
                x.max_deviation = value
                return x
            return self._with_parameters(f)
        else:
            return self

    @abstractmethod
    def with_args(self, **args):
        pass

    @abstractmethod
    def to_args(self):
        pass


class MoveJointsOperation(MoveOperation):

    def __init__(self, args: MoveJointsArgs):
        """
        Initialization of MoveJointsOperation

        Parameters
        ----------
        args : MoveJointsArgs
            move joint args which define the move operation

        Returns
        -------
        MoveJointsOperation
            Instance of MoveJointsOperation
        """

        super(MoveJointsOperation, self).__init__(args)

    def plan(self):
        """
        Planes a trajectory with defined properties

        Returns
        -------
        Plan
            Instance of Plan which holds the planned
            trajectory and methods to creates executors for it

        Raises
        ------
        ServiceException
            If trajectory planning service is not available or finish
            unsuccessfully
        """

        start = self._start or self._move_group.get_current_joint_positions()
        try:
            path = self._target.prepend(start)
        except AttributeError:
            path = JointPath.from_start_stop_point(start, self._target)
        joint_path = JointPath(self._move_group.joint_set, path)
        t = self._move_group.motion_service.plan_move_joints(joint_path,
                                                             self._plan_parameters)

        return Plan(self._move_group, t, self._plan_parameters)

    def _build(self, args: MoveJointsArgs):
        """
        Build a new instance of MoveJointsOperations
        """
        return type(self)(args)

    def _with_parameters(self, func):
        return self._build(func(self.to_args()))

    def with_start(self, joint_value: Union[None, JointValues]):
        """
        Creates new instance of MoveJointsOperation with modified start joint value

        Parameters
        ----------
        joint_value : JointValues or None
            defines start joint configuration if non
            current robot state is used

        Returns
        -------
        MoveJointsOperations
            New instance with modified start value

        Raises
        ------
        TypeError
            If joint_value is not of expected type JointValue
        """
        if not isinstance(joint_value, (type(None), JointValues)):
            raise TypeError('value is not of expected type JointValues')

        return super(MoveJointsOperation, self).with_start(joint_value)

    def with_velocity_scaling(self, velocity_scaling: float):
        """
        Creates new instance of MoveJointsOperation with modified velocity limits

        Parameters
        ----------
        velocity_scaling : float convertable
            scale hard velocity limits by defined factor

        Returns
        -------
        MoveJointsOperations
            New instance with modified velocity limits

        Raises
        ------
        TypeError
            If velocity_scaling is not float convertable
        ValueError
            If velocity_scaling is not in range 0.0, 1.0
        """

        return super(MoveJointsOperation, self).with_velocity_scaling(velocity_scaling)

    def with_acceleration_scaling(self, acceleration_scaling: float):
        """
        Creates new instance of MoveJointsOperation with modified velocity limits

        Parameters
        ----------
        acceleration_scaling : float convertable
            scale hard acceleration limits by defined factor

        Returns
        -------
        MoveJointsOperations
            New instance with modified acceleration limits

        Raises
        ------
        TypeError
            If acceleration_scaling is not float convertable
        ValueError
            If acceleration_scaling is not in range 0.0, 1.0
        """

        return super(MoveJointsOperation, self).with_acceleration_scaling(acceleration_scaling)

    def with_collision_check(self, collision_check: bool=True):
        """
        Creates new instance of MoveJointsOperation with modified collision check flag

        Parameters
        ----------
        collision_check : bool (default True)
            If True collisions with collision objects in worldview are check
            in the planning stage

        Returns
        -------
        MoveJointsOperations
            New instance with modified collision check flag

        Raises
        ------
        TypeError
            If collision check is of expected type bool
        """

        return super(MoveJointsOperation, self).with_collision_check(collision_check)

    def with_sample_resolution(self, sample_resolution: float):
        """
        Creates new instance of MoveJointsOperation with modified sample resolution

        Parameters
        ----------
        sample_resolution : float convertable
            sampling resolution of trajectory in Hz

        Returns
        -------
        MoveJointsOperations
            New instance with modified sample resolution

        Raises
        ------
        TypeError
            If sample_resolution is not float convertable
        """

        return super(MoveJointsOperation, self).with_sample_resolution(sample_resolution)

    def with_max_deviation(self, max_deviation: float):
        """
        Creates new instance of MoveJointsOperation with modified max deviation

        Parameters
        ----------
        max_deviation : float convertable
            defines the maximal deviation from trajectory points
            when it is a fly-by-point in joint space

        Returns
        -------
        MoveJointsOperations
            New instance with modified max deviation

        Raises
        ------
        TypeError
            If max_deviation is not float convertable
        """

        return super(MoveJointsOperation, self).with_max_deviation(max_deviation)

    def with_args(self, velocity_scaling: Union[float, None]=None,
                  collision_check: Union[bool, None]=None,
                  max_deviation: Union[float, None]=None,
                  sample_resolution: Union[float, None]=None,
                  acceleration_scaling: Union[float, None]=None):
        """
        Creates new instance of MoveJointsOperations with multiple modified properties

        All None assigned arguments take the current property values

        Parameters
        ----------
        velocity_scaling : float convertable (default None)
            scale hard velocity limits by defined factor
        collision_check : bool (default None)
            If True collisions with collision objects in worldview are check
            in the planning stage
        max_deviation : float convertable
            defines the maximal deviation from trajectory points
            when it is a fly-by-point in joint space
        sample_resolution : float convertable
            sampling resolution of trajectory in Hz
        acceleration_scaling : float convertable
            scale hard acceleration limits by defined factor

        Returns
        -------
        MoveJointsOperations or child of it (MoveJointsCollisionFreeOperations)
            New instance with modified properties

        Raises
        ------
        TypeError
            If velocity_scaling, max_deviation, sample_resolution and
            acceleration_scaling are not None or not float convertable
        ValueError
            If velocity_scaling or acceleration scaling are not None
            and no lie in range 0.0 to 1.0
        """

        def f(x):
            if velocity_scaling is not None:
                x.velocity_scaling = velocity_scaling
            if collision_check is not None:
                x.collision_check = collision_check
            if max_deviation is not None:
                x.max_deviation = max_deviation
            if sample_resolution is not None:
                x.sample_resolution = sample_resolution
            if acceleration_scaling is not None:
                x.acceleration_scaling = acceleration_scaling

        return self._with_parameters(f)

    def to_args(self) -> MoveJointsArgs:
        """
        Creates an Instance of MoveJointsArgs from this MoveJointsOperation

        Returns
        -------
        MoveJointsArgs
            MoveJointsArgs which holds the properties of this MoveJointsOperation
        """

        args = MoveJointsArgs()
        args.move_group = self._move_group
        args.start = self._start
        args.target = self._target
        args.velocity_scaling = self._velocity_scaling
        args.acceleration_scaling = self._acceleration_scaling
        args.collision_check = self._plan_parameters.collision_check
        args.sample_resolution = self._plan_parameters.sample_resolution
        args.max_deviation = self._plan_parameters.max_deviation

        return args


class MoveJointsCollisionFreeOperation(MoveJointsOperation):

    def __init__(self, args: MoveJointsArgs):
        """
        Initialization of MoveJointsCollisionFreeOperation

        Parameters
        ----------
        args : MoveJointsArgs
            move joint args which define the move operation

        Returns
        -------
        MoveJointsCollisionFreeOperation
            Instance of MoveJointsCollisionFreeOperation
        """

        super(MoveJointsCollisionFreeOperation, self).__init__(args)

    def plan(self):
        """
        Planes a collision free trajectory with defined properties

        Returns
        -------
        Plan
            Instance of Plan which holds the planned
            trajectory and methods to creates executors for it

        Raises
        ------
        ServiceException
            If trajectory planning service is not available or finish
            unsuccessfully
        """

        start = self._start or self._move_group.get_current_joint_positions()
        try:
            path = self._target.prepend(start)
        except AttributeError:
            path = JointPath.from_start_stop_point(start, self._target)
        joint_path = JointPath(self._move_group.joint_set, path)
        p = self._move_group.motion_service.plan_collision_free_joint_path(joint_path,
                                                                           self._plan_parameters)
        t = self._move_group.motion_service.plan_move_joints(p,
                                                             self._plan_parameters)

        return Plan(self._move_group, t, self._plan_parameters)


class MoveCartesianOperation(MoveOperation):

    def __init__(self, args: MoveCartesianArgs):
        """
        Initialization of MoveCartesianOperation

        Parameters
        ----------
        args : MoveCartesianArgs
            move cartesian args which define the move operation

        Returns
        -------
        MoveCartesianOperation
            Instance of MoveCartesianOperation
        """

        super(MoveCartesianOperation, self).__init__(args)

        self._end_effector = args.end_effector
        self._seed = args.seed
        self._ik_jump_threshold = args.ik_jump_threshold

        p = self._end_effector._build_task_space_plan_parameters(args.velocity_scaling,
                                                                 args.collision_check,
                                                                 args.max_deviation,
                                                                 args.acceleration_scaling,
                                                                 args.sample_resolution,
                                                                 args.ik_jump_threshold)

        self._task_space_plan_parameters = p

    def plan(self):
        """
        Planes a trajectory with defined properties

        Returns
        -------
        Plan
            Instance of Plan which holds the planned
            trajectory and methods to creates executors for it

        Raises
        ------
        ServiceException
            If trajectory planning service is not available or finish
            unsuccessfully
        """
        seed = self._seed or self._move_group.get_current_joint_positions()

        start = self._start or self._move_group.get_current_joint_positions()

        if isinstance(start, Pose):
            start = self._end_effector.inverse_kinematics(start,
                                                          self._plan_parameters.collision_check,
                                                          seed)

        path = self._end_effector.inverse_kinematics_many(self._target,
                                                          self._plan_parameters.collision_check,
                                                          seed).path

        path = path.prepend(start)

        ik_jump_threshold = self._task_space_plan_parameters.ik_jump_threshold
        p_p = path[0].values
        for i, p in enumerate(path[1:]):
            delta = np.max(np.abs(p.values - p_p))
            if delta > ik_jump_threshold:
                raise RuntimeError('The difference {} of two consecutive IK solutions'
                                   ' for the given cartesian path at index {} exceeds the'
                                   ' ik jump threshold {}'.format(delta,
                                                                  i,
                                                                  ik_jump_threshold))

        t = self._move_group.motion_service.plan_move_joints(path,
                                                             self._plan_parameters)

        return Plan(self._move_group, t, self._plan_parameters)

    def _build(self, args: MoveCartesianArgs):
        """
        Build a new instance of MoveCartesianOperations
        """
        return type(self)(args)

    def _with_parameters(self, func):
        return self._build(func(self.to_args()))

    def with_start(self, start: Union[None, JointValues, Pose]):
        """
        Creates new instance of MoveCartesianOperation with modified start values

        Parameters
        ----------
        start : JointValues, Pose or None
            defines trajectory start position if None
            current robot state is used

        Returns
        -------
        MoveCartesianOperations
            New instance with modified start value

        Raises
        ------
        TypeError
            If start is not one of expected types JointValue, Pose, None
        """
        if not isinstance(start, (type(None), JointValues, Pose)):
            raise TypeError('start is not one of expected types'
                            ' None, JointValues')

        return super(MoveCartesianOperation, self).with_start(start)

    def with_seed(self, joint_value: Union[None, JointValues]):
        """
        Creates new instance of MoveCartesianOperation with modified seed joint values

        Parameters
        ----------
        joint_value : JointValues or None
            defines start joint configuration if None
            current robot state is used

        Returns
        -------
        MoveCartesianOperations
            New instance with modified seed value

        Raises
        ------
        TypeError
            If joint_value is not one of expected types JointValue, Pose, None
        """
        if not isinstance(joint_value, (type(None), JointValues, Pose)):
            raise TypeError('value is not one of expected types Pose,'
                            ' None, JointValues')

        if joint_value != self._seed:
            def f(x):
                x.seed = joint_value
            return self._with_parameters(f)
        else:
            return self

    def with_velocity_scaling(self, velocity_scaling: float):
        """
        Creates new instance of MoveCartesianOperation with modified velocity limits

        Parameters
        ----------
        velocity_scaling : float convertable
            scale hard velocity limits by defined factor

        Returns
        -------
        MoveCartesianOperations
            New instance with modified velocity limits

        Raises
        ------
        TypeError
            If velocity_scaling is not float convertable
        ValueError
            If velocity_scaling is not in range 0.0, 1.0
        """

        return super(MoveCartesianOperation, self).with_acceleration_scaling(velocity_scaling)

    def with_acceleration_scaling(self, acceleration_scaling: float):
        """
        Creates new instance of MoveCartesianOperation with modified velocity limits

        Parameters
        ----------
        acceleration_scaling : float convertable
            scale hard acceleration limits by defined factor

        Returns
        -------
        MoveCartesianOperations
            New instance with modified acceleration limits

        Raises
        ------
        TypeError
            If acceleration_scaling is not float convertable
        ValueError
            If acceleration_scaling is not in range 0.0, 1.0
        """

        return super(MoveCartesianOperation, self).with_acceleration_scaling(acceleration_scaling)

    def with_collision_check(self, collision_check: bool=True):
        """
        Creates new instance of MoveCartesianOperation with modified collision check flag

        Parameters
        ----------
        collision_check : bool (default True)
            If True collisions with collision objects in worldview are check
            in the planning stage

        Returns
        -------
        MoveCartesianOperations
            New instance with modified collision check flag

        Raises
        ------
        TypeError
            If collision check is of expected type bool
        """

        return super(MoveCartesianOperation, self).with_collision_check(collision_check)

    def with_sample_resolution(self, sample_resolution: float):
        """
        Creates new instance of MoveCartesianOperation with modified sample resolution

        Parameters
        ----------
        sample_resolution : float convertable
            sampling resolution of trajectory in Hz

        Returns
        -------
        MoveCartesianOperations
            New instance with modified sample resolution

        Raises
        ------
        TypeError
            If sample_resolution is not float convertable
        """

        return super(MoveCartesianOperation, self).with_sample_resolution(sample_resolution)

    def with_max_deviation(self, max_deviation: float):
        """
        Creates new instance of MoveCartesianOperation with modified max deviation

        Parameters
        ----------
        max_deviation : float convertable
            defines the maximal deviation from trajectory points
            when it is a fly-by-point in joint space

        Returns
        -------
        MoveCartesianOperations
            New instance with modified max deviation

        Raises
        ------
        TypeError
            If max_deviation is not float convertable
        """

        return super(MoveCartesianOperation, self).with_max_deviation(max_deviation)

    def with_ik_jump_threshold(self, ik_jump_threshold: float):
        """
        Creates new instance of MoveCartesianOperation with modified ik jump threshold

        Parameters
        ----------
        ik_jump_threshold : float convertable
            Maximal joint value jump between two consecutively
            following trajectory points

        Returns
        -------
        MoveCartesianOperations
            New instance with modified ik jump threshold

        Raises
        ------
        TypeError
            If ik_jump_threshold is not float convertable
        """

        if ik_jump_threshold != self._task_space_plan_parameters.ik_jump_threshold:
            def f(x):
                x.ik_jump_threshold = ik_jump_threshold
            return self._with_parameters(f)
        else:
            return self

    def with_args(self, velocity_scaling: Union[float, None]=None,
                  collision_check: Union[bool, None]=None,
                  max_deviation: Union[float, None]=None,
                  sample_resolution: Union[float, None]=None,
                  ik_jump_threshold: Union[float, None]=None,
                  acceleration_scaling: Union[float, None]=None):
        """
        Creates new instance of MoveCartesianOperations with multiple modified properties

        All None assigned arguments take the current property values

        Parameters
        ----------
        velocity_scaling : float convertable (default None)
            scale hard velocity limits by defined factor
        collision_check : bool (default None)
            If True collisions with collision objects in worldview are check
            in the planning stage
        max_deviation : float convertable
            defines the maximal deviation from trajectory points
            when it is a fly-by-point in joint space
        sample_resolution : float convertable
            sampling resolution of trajectory in Hz
        ik_jump_threshold : None or float
            Maximal joint value jump between two consecutively
            following trajectory points
        acceleration_scaling : float convertable
            scale hard acceleration limits by defined factor

        Returns
        -------
        MoveJointsOperations
            New instance with modified properties

        Raises
        ------
        TypeError
            If velocity_scaling, max_deviation, sample_resolution and
            acceleration_scaling are not None or not float convertable
        ValueError
            If velocity_scaling or acceleration scaling are not None
            and no lie in range 0.0 to 1.0
        """

        def f(x):
            if velocity_scaling is not None:
                x.velocity_scaling = velocity_scaling
            if collision_check is not None:
                x.collision_check = collision_check
            if max_deviation is not None:
                x.max_deviation = max_deviation
            if sample_resolution is not None:
                x.sample_resolution = sample_resolution
            if ik_jump_threshold:
                x.ik_jump_threshold = ik_jump_threshold
            if acceleration_scaling is not None:
                x.acceleration_scaling = acceleration_scaling

        return self._with_parameters(f)

    def to_args(self) -> MoveCartesianArgs:
        """
        Creates an Instance of MoveCartesianArgs from this MoveCartesianOperation

        Returns
        -------
        MoveCartesianArgs
            MoveCartesianArgs which holds the properties of this MoveCartesianOperation
        """

        args = MoveCartesianArgs()
        args.move_group = self._move_group
        args.end_effector = self._end_effector
        args.seed = self._seed
        args.start = self._start
        args.target = self._target
        args.velocity_scaling = self._velocity_scaling
        args.acceleration_scaling = self._acceleration_scaling
        args.collision_check = self._plan_parameters.collision_check
        args.sample_resolution = self._plan_parameters.sample_resolution
        args.max_deviation = self._plan_parameters.max_deviation
        args.ik_jump_threshold = self._ik_jump_threshold

        return args


class MoveCartesianCollisionFreeOperation(MoveCartesianOperation):

    def __init__(self, args: MoveCartesianArgs):
        """
        Initialization of MoveCartesianCollisionFreeOperation

        Parameters
        ----------
        args : MoveCartesianArgs
            move joint args which define the move operation

        Returns
        -------
        MoveCartesianCollisionFreeOperation
            Instance of MoveCartesianCollisionFreeOperation
        """

        super(MoveCartesianCollisionFreeOperation, self).__init__(args)

    def plan(self):
        """
        Planes a collision free trajectory with defined properties

        Returns
        -------
        Plan
            Instance of Plan which holds the planned
            trajectory and methods to creates executors for it

        Raises
        ------
        ServiceException
            If trajectory planning service is not available or finish
            unsuccessfully
        """
        seed = self._seed or self._move_group.get_current_joint_positions()

        start = self._start or self._move_group.get_current_joint_positions()

        if isinstance(start, Pose):
            start = self._end_effector.inverse_kinematics(start,
                                                          self._plan_parameters.collision_check,
                                                          seed)

        path = self._end_effector.inverse_kinematics_many(self._target,
                                                          self._plan_parameters.collision_check,
                                                          seed).path

        path = path.prepend(start)

        ik_jump_threshold = self._task_space_plan_parameters.ik_jump_threshold
        p_p = path[0].values
        for i, p in enumerate(path[1:]):
            delta = np.max(np.abs(p.values - p_p))
            if delta > ik_jump_threshold:
                raise RuntimeError('The difference {} of two consecutive IK solutions'
                                   ' for the given cartesian path at index {} exceeds the'
                                   ' ik jump threshold {}'.format(delta,
                                                                  i,
                                                                  ik_jump_threshold))

        p = self._move_group.motion_service.plan_collision_free_joint_path(path,
                                                                           self._plan_parameters)

        t = self._move_group.motion_service.plan_move_joints(p,
                                                             self._plan_parameters)

        return Plan(self._move_group, t, self._plan_parameters)


class MoveCartesianLinearOperation(MoveCartesianOperation):

    def __init__(self, args: MoveCartesianArgs):
        """
        Initialization of MoveCartesianLinearOperation

        Parameters
        ----------
        args : MoveCartesianArgs
            move cartesian args which define the move operation

        Returns
        -------
        MoveCartesianLinearOperation
            Instance of MoveCartesianLinearOperation
        """

        super(MoveCartesianLinearOperation, self).__init__(args)

    def plan(self):
        """
        Planes a linear trajectory with defined properties

        Returns
        -------
        Plan
            Instance of Plan which holds the planned
            trajectory and methods to creates executors for it

        Raises
        ------
        ServiceException
            If trajectory planning service is not available or finish
            unsuccessfully
        """
        seed = self._seed or self._move_group.get_current_joint_positions()

        start = self._start or self._end_effector.get_current_pose()

        path = self._target

        path = path.prepend(start)

        t = self._move_group.motion_service.plan_move_pose_linear(path, seed,
                                                                  self._task_space_plan_parameters)

        return Plan(self._move_group, t, self._plan_parameters)
