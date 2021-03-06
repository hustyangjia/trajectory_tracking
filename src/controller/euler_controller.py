#!/usr/bin/env python
from math import atan2, sin, pi
from math import cos

from orientation import get_angle_between_0_and_2_pi
from .controller import Controller


class EulerMethodController(Controller):
    def __init__(self, trajectory, simulation_data, control_constants):
        Controller.__init__(self, trajectory, simulation_data)
        self.K_X = control_constants['x']
        self.K_Y = control_constants['y']
        self.K_THETA = control_constants['theta']
        self.theta_ez_n_minus_1 = 0
        self.theta_n_minus_1 = 0

    def set_next_reference(self, reference):
        self.x_ref_n_plus_1 = reference.x
        self.y_ref_n_plus_1 = reference.y

    def get_delta_x_n(self):
        return self.x_ref_n_plus_1 - self.K_X * (self.x_ref_n - self.x_n) - self.x_n

    def get_delta_y_n(self):
        return self.y_ref_n_plus_1 - self.K_Y * (self.y_ref_n - self.y_n) - self.y_n

    def get_delta_theta_n(self):
        self.theta_ez_n = get_angle_between_0_and_2_pi(self.theta_ez_n)
        self.theta_n = get_angle_between_0_and_2_pi(self.theta_n)
        self.theta_ez_n_minus_1 = get_angle_between_0_and_2_pi(self.theta_ez_n_minus_1)

        epsilon = 4 * self.delta

        alpha = self.theta_ez_n - self.K_THETA * (self.theta_ez_n_minus_1 - self.theta_n) - self.theta_n

        if alpha == 2 * pi:
            alpha = 0

        if self.trajectory.get_name() == 'astroid' and (
                            abs(self.simulation_time / 4 - self.i * self.delta) < epsilon or \
                                abs(self.simulation_time / 2 - self.i * self.delta) < epsilon or \
                            abs(3 * self.simulation_time / 4 - self.i * self.delta) < epsilon):
            alpha = abs(alpha) * 2

        return alpha

    def compute_theta_ez_n(self):
         return atan2(self.get_delta_y_n(), self.get_delta_x_n())

    def compute_v_c_n(self):
        delta_x_n = self.get_delta_x_n()
        delta_y_n = self.get_delta_y_n()

        return (delta_x_n * cos(self.theta_ez_n) + delta_y_n * sin(self.theta_ez_n)) / self.delta

    def compute_w_c_n(self):
        w_n = self.get_delta_theta_n() / self.delta

        self.theta_ez_n_minus_1 = self.theta_ez_n
        self.theta_n_minus_1 = self.theta_n
        self.theta_ref_n = self.theta_ez_n

        if self.trajectory.get_name() in ('circular', 'squared', 'astroid'):
            if not 0 <= self.i * self.delta < self.simulation_time / 4 + 10 * self.delta:
                self.theta_ref_n = get_angle_between_0_and_2_pi(self.theta_ez_n)
                self.theta_n = get_angle_between_0_and_2_pi(self.theta_n)

        # limit angular velocity to be between -pi and pi rad/s
        return atan2(sin(w_n), cos(w_n))

    def compute_control_actions(self, pose, twist, i):
        self.i = i
        self.set_current_orientation(pose.orientation)
        self.set_current_position(pose.position)
        self.set_current_reference(self.trajectory.get_position_at(i * self.delta))
        self.set_next_reference(self.trajectory.get_position_at((i + 1) * self.delta))

        self.theta_ez_n = self.compute_theta_ez_n()
        self.v_c_n = self.compute_v_c_n()
        self.w_c_n =  self.compute_w_c_n()
