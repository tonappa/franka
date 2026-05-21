cmake_minimum_required(VERSION 3.0.2)
project(franka_softhand_bringup)

find_package(catkin REQUIRED)

catkin_package()

install(DIRECTORY launch config
  DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION}
)

catkin_install_python(PROGRAMS
  scripts/camera_in_scene.py
  DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION}
)
