import pytest
from xamla_motion.data_types import Pose
from datetime import timedelta
import numpy as np
from pyquaternion import Quaternion


class TestPose(object):

    @classmethod
    def setup_class(cls):
        c30 = np.sqrt(3)/2.0
        s30 = -0.5

        c60 = -s30
        s60 = -c30

        # create pose1 from transformation matrix
        m1 = np.eye(4)
        m1[0:3, 3] = np.asarray([0.8660254037844386, 0.5, 0.0])
        m1[0:2, 0:2] = np.asarray([[c30, -s30], [s30, c30]])
        cls.pose1 = Pose.from_transformation_matrix(m1)

        # create pose2 from transformation matrix
        m2 = np.eye(4)
        m2[0:3, 3] = np.asarray([0.25, -0.43301270189221935, 0.0])
        m2[0:2, 0:2] = np.asarray([[c60, -s60], [s60, c60]])
        cls.pose2 = Pose.from_transformation_matrix(m2)

        # create pose3 from transformation matrix
        cls.m3 = np.eye(4)
        cls.m3[0:3, 3] = np.asarray([0.8660254037844386, 0.0, 0.0])
        cls.m3[0:2, 0:2] = np.asarray([[0.0, 1.0], [-1.0, 0.0]])
        cls.pose3 = Pose.from_transformation_matrix(cls.m3)

        # create pose4 from transformation matrix
        translation = np.asarray([0.22419, -0.78420, 0.945699])
        quaternion = Quaternion(x=0.6087561845779419,
                                y=0.7779673933982849,
                                z=0.047310106456279755,
                                w=0.1481364518404007)
        cls.pose4 = Pose(translation, quaternion)

    def test_pose_inverse(self):
        p_inv = self.pose1.inverse('new_frame')
        p_m = (self.pose1*p_inv).transformation_matrix()

        assert p_m == pytest.approx(np.eye(4))

    def test_translate(self):
        t_pose = self.pose3.translate([0.0, 1.0, 1.0])
        gt = self.m3.copy()
        gt[1, 3] = 1.0
        gt[2, 3] = 1.0
        assert t_pose.transformation_matrix() == pytest.approx(gt)

    def test_rotate(self):
        m = self.m3.copy()
        m[0:3, 0:3] = np.eye(3)
        p = Pose.from_transformation_matrix(m)
        r_pose = p.rotate(self.m3[0:3, 0:3])
        assert r_pose.transformation_matrix() == pytest.approx(self.m3)

    def test_pose_mul_pose(self):
        tri_pose = (self.pose1*self.pose2)*self.pose3.inverse('pose3')
        assert tri_pose.transformation_matrix() == pytest.approx(np.eye(4))

    def test_pose_mul_vect3(self):
        vec = np.asarray([1.23, 2.3, 1.2])
        new_p = self.pose3*vec
        gt = self.pose3.translation.copy()
        gt[0] += vec[1]
        gt[1] -= vec[0]
        gt[2] += vec[2]
        assert new_p == pytest.approx(gt)

    def test_pose_mul_vect3_1(self):
        vec = np.asarray([[1.23, 2.3, 1.2]])
        new_p = self.pose3*vec.T
        gt = np.expand_dims(self.pose3.translation.copy(), axis=1)
        gt[0] += vec[0][1]
        gt[1] -= vec[0][0]
        gt[2] += vec[0][2]
        assert new_p == pytest.approx(gt)

    def test_pose_mul_vect4(self):
        vec = np.asarray([1.23, 2.3, 1.2, 1.0])
        new_p = self.pose3*vec
        gt = np.ones((4,))
        gt[0:3] = self.pose3.translation.copy()
        gt[0] += vec[1]
        gt[1] -= vec[0]
        gt[2] += vec[2]
        assert new_p == pytest.approx(gt)

    def test_pose_mul_vect4_1(self):
        vec = np.asarray([[1.23, 2.3, 1.2, 1.0]])
        new_p = self.pose3*vec.T
        gt = np.ones((4, 1))
        gt[0:3] = np.expand_dims(self.pose3.translation.copy(), axis=1)
        gt[0] += vec[0][1]
        gt[1] -= vec[0][0]
        gt[2] += vec[0][2]
        assert new_p == pytest.approx(gt)

    def test_pose_mul_pose_2(self):
        pose = self.pose4 * self.pose2
        pose_m = np.matmul(self.pose4.transformation_matrix(),
                           self.pose2.transformation_matrix())

        print('Pose type mul: {}'.format(pose.transformation_matrix()))
        print('numpy mul: {}'.format(pose_m))
        assert pose.transformation_matrix() == pytest.approx(pose_m)

    def test_pose_mul2_pose(self):
        pose = self.pose4 * self.pose2 * self.pose1
        pose_m = np.matmul(self.pose4.transformation_matrix(),
                           np.matmul(self.pose2.transformation_matrix(),
                                     self.pose1.transformation_matrix()))

        print('Pose type mul: {}'.format(pose.transformation_matrix()))
        print('numpy mul: {}'.format(pose_m))
        assert pose.transformation_matrix() == pytest.approx(pose_m)
