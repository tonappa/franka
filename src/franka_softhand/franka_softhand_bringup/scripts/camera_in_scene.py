#!/usr/bin/env python3
"""Aggiunge la RealSense alla scena MoveIt:
- pubblica la TF statica `world -> camera_link` con la posa da
  ~camera_pose (yaml)
- inserisce un collision box nella planning scene a `camera_link` con
  size/offset da ~camera_collision

Non avvia il nodo rs_camera (lo stream camera e' indipendente).
Resta vivo per mantenere la TF statica attiva.
"""

import sys
import rospy
import tf2_ros
from geometry_msgs.msg import TransformStamped, PoseStamped
from tf.transformations import quaternion_from_euler
from moveit_commander import PlanningSceneInterface, roscpp_initialize, roscpp_shutdown


def publish_static_tf(parent, child, xyz, quat):
    br = tf2_ros.StaticTransformBroadcaster()
    t = TransformStamped()
    t.header.stamp = rospy.Time.now()
    t.header.frame_id = parent
    t.child_frame_id = child
    t.transform.translation.x = float(xyz[0])
    t.transform.translation.y = float(xyz[1])
    t.transform.translation.z = float(xyz[2])
    t.transform.rotation.x = float(quat[0])
    t.transform.rotation.y = float(quat[1])
    t.transform.rotation.z = float(quat[2])
    t.transform.rotation.w = float(quat[3])
    br.sendTransform(t)
    return br  # tieni il broadcaster vivo


def quat_from_pose(pose):
    """Preferisce qx/qy/qz/qw nello yaml. Fallback su roll/pitch/yaw (URDF)."""
    if all(k in pose for k in ("qx", "qy", "qz", "qw")):
        return (pose["qx"], pose["qy"], pose["qz"], pose["qw"])
    if all(k in pose for k in ("roll", "pitch", "yaw")):
        q = quaternion_from_euler(float(pose["roll"]),
                                  float(pose["pitch"]),
                                  float(pose["yaw"]))
        return tuple(q)
    raise KeyError("camera_pose: serve (qx,qy,qz,qw) oppure (roll,pitch,yaw)")


def add_collision_box(frame_id, name, size, offset):
    psi = PlanningSceneInterface(synchronous=True)
    p = PoseStamped()
    p.header.frame_id = frame_id
    p.pose.position.x = float(offset[0])
    p.pose.position.y = float(offset[1])
    p.pose.position.z = float(offset[2])
    p.pose.orientation.w = 1.0
    psi.add_box(name, p, size=tuple(float(s) for s in size))


def main():
    rospy.init_node("camera_in_scene")
    roscpp_initialize(sys.argv)

    try:
        pose = rospy.get_param("~camera_pose")
        coll = rospy.get_param("~camera_collision")
    except KeyError as e:
        rospy.logfatal("Manca il parametro %s. Carica config/camera_pose.yaml.", e)
        return 1

    xyz = (pose["x"], pose["y"], pose["z"])
    quat = quat_from_pose(pose)
    rospy.loginfo("camera_in_scene: TF world->camera_link  xyz=%s quat(xyzw)=%s",
                  xyz, quat)
    br = publish_static_tf("world", "camera_link", xyz, quat)

    # Attendi che move_group sia pronto prima di pushare il box.
    rospy.loginfo("camera_in_scene: aspetto move_group per inserire il collision box...")
    rospy.sleep(2.0)
    try:
        add_collision_box("camera_link", "realsense_d435i",
                          coll["size"], coll.get("offset", [0.0, 0.0, 0.0]))
        rospy.loginfo("camera_in_scene: collision box 'realsense_d435i' aggiunto.")
    except Exception as e:
        rospy.logerr("camera_in_scene: impossibile aggiungere collision box: %s", e)

    rospy.spin()
    roscpp_shutdown()
    return 0


if __name__ == "__main__":
    sys.exit(main() or 0)
