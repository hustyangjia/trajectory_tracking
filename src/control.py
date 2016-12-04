#!/usr/bin/env python
from __future__ import print_function
import rospy
import time
import sys
from gazebo_msgs.msg import ModelStates
from geometry_msgs.msg import Twist

from constants import DELTA_T, STEPS
from controller import create_controller
from plotter.simulation_plotter import SimulationPlotter
from util.util import TrajectoryName, ControllerName


def get_pose(message):
    global current_pose, current_twist
    current_pose = message.pose[-1]
    current_twist = message.twist[-1]


def compute_control_actions():
    global i
    controller.compute_control_actions(current_pose, current_twist, i)
    plotter.add_point(current_pose)
    plotter.plot_data.theta.append(controller.theta_n)
    plotter.plot_data.theta_ref.append(controller.theta_ref_n)
    plotter.plot_data.v_c.append(controller.v_c_n)
    plotter.plot_data.w_c.append(controller.w_c_n)

    twist = Twist()
    twist.linear.x = controller.v_c_n
    twist.angular.z = controller.w_c_n
    twist_publisher.publish(twist)

    i += 1


if __name__ == '__main__':
    if len(sys.argv) != 4:
        print('Missing arguments!' if len(sys.argv) < 4 else 'Too much arguments!')
        print('Try: rosrun trajectory_tracking control.py <trajectory> <controller> <simulation-time>')
        sys.exit(-1)

    arguments = sys.argv[1:]

    if arguments[0] not in TrajectoryName.__members__:
        print('ERROR: Please enter a valid trajectory:')
        for trajectory in TrajectoryName.__members__:
            print('\t' + trajectory)
        sys.exit(-2)

    if arguments[1] not in ControllerName.__members__:
        print('ERROR: Please enter a valid controller:')
        for controller in ControllerName.__members__:
            print('\t' + controller)
        sys.exit(-3)

    try:
        if float(arguments[2]) <= 0.0:
            raise RuntimeError
    except:
        print('ERROR: Please enter a positive number for simulation time!')
        sys.exit(-4)

    rospy.init_node('control')
    current_pose = None
    current_twist = None
    subscriber = rospy.Subscriber('gazebo/model_states', ModelStates, get_pose)
    twist_publisher = rospy.Publisher('computed_control_actions', Twist, queue_size=1)

    while current_pose is None or current_twist is None:
        pass

    i = 0
    plotter = SimulationPlotter(STEPS)
    controller = create_controller()
    rate = rospy.Rate(int(1 / DELTA_T))
    while not rospy.is_shutdown() and i < STEPS:
        compute_control_actions()
        rate.sleep()

    print('Simulation was completed successfully!')

    # wait before plotting after simulation is completed
    time.sleep(2)

    plotter.plot_results()
    plotter.export_results()
    print('Data was exported successfully!')

    rospy.spin()
