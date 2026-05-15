#!/usr/bin/env python3
"""One-shot loader: legge gli oggetti da ~scene/* e li pubblica nella
PlanningScene di MoveIt (geometria + colori), poi esce. Gli oggetti restano
nella scena finche' il move_group e' vivo."""

import sys
import rospy
from geometry_msgs.msg import PoseStamped
from std_msgs.msg import ColorRGBA
from moveit_msgs.msg import PlanningScene, ObjectColor, PlanningSceneComponents
from moveit_msgs.srv import (GetPlanningScene, GetPlanningSceneRequest,
                             ApplyPlanningScene, ApplyPlanningSceneRequest)
from moveit_commander import PlanningSceneInterface, roscpp_initialize, roscpp_shutdown


def make_pose(frame_id, xyz):
    p = PoseStamped()
    p.header.frame_id = frame_id
    p.pose.position.x = float(xyz[0])
    p.pose.position.y = float(xyz[1])
    p.pose.position.z = float(xyz[2])
    p.pose.orientation.w = 1.0
    return p


def make_color(name, rgba):
    oc = ObjectColor()
    oc.id = name
    oc.color = ColorRGBA(r=float(rgba[0]), g=float(rgba[1]),
                         b=float(rgba[2]),
                         a=float(rgba[3]) if len(rgba) > 3 else 1.0)
    return oc


def apply_allowed_collisions(pairs):
    """Aggiunge le coppie all'ACM via GET /get_planning_scene + ApplyPlanningScene.
    Idempotente: se la coppia gia' esiste, la rimette a True."""
    if not pairs:
        return
    try:
        rospy.wait_for_service("/get_planning_scene", timeout=5.0)
        rospy.wait_for_service("/apply_planning_scene", timeout=5.0)
    except rospy.ROSException as e:
        rospy.logerr("ACM: servizi non disponibili (%s), salto.", e)
        return

    get_scene = rospy.ServiceProxy("/get_planning_scene", GetPlanningScene)
    apply_scene = rospy.ServiceProxy("/apply_planning_scene", ApplyPlanningScene)

    req = GetPlanningSceneRequest()
    req.components.components = PlanningSceneComponents.ALLOWED_COLLISION_MATRIX
    acm = get_scene(req).scene.allowed_collision_matrix

    names = list(acm.entry_names)
    # matrice come lista di liste di bool
    values = [list(row.enabled) for row in acm.entry_values]

    def ensure_name(n):
        if n in names:
            return names.index(n)
        names.append(n)
        for row in values:
            row.append(False)
        values.append([False] * len(names))
        return len(names) - 1

    for a, b in pairs:
        i = ensure_name(a)
        j = ensure_name(b)
        values[i][j] = True
        values[j][i] = True

    # ribuilda i messaggi
    from moveit_msgs.msg import AllowedCollisionMatrix, AllowedCollisionEntry
    new_acm = AllowedCollisionMatrix()
    new_acm.entry_names = names
    new_acm.entry_values = [AllowedCollisionEntry(enabled=row) for row in values]
    new_acm.default_entry_names = list(acm.default_entry_names)
    new_acm.default_entry_values = list(acm.default_entry_values)

    ps = PlanningScene()
    ps.is_diff = True
    ps.allowed_collision_matrix = new_acm

    areq = ApplyPlanningSceneRequest()
    areq.scene = ps
    if apply_scene(areq).success:
        rospy.loginfo("ACM aggiornato: %d coppie consentite", len(pairs))
    else:
        rospy.logwarn("ApplyPlanningScene: success=false")


def wait_for_object(scene, name, timeout=2.0):
    end = rospy.Time.now() + rospy.Duration(timeout)
    while rospy.Time.now() < end and not rospy.is_shutdown():
        if name in scene.get_known_object_names():
            return True
        rospy.sleep(0.05)
    return False


def main():
    roscpp_initialize(sys.argv)
    rospy.init_node("franka_softhand_scene_loader", anonymous=False)

    frame_id = rospy.get_param("~scene/frame_id", "world")
    objects = rospy.get_param("~scene/objects", [])
    allowed_pairs = rospy.get_param("~scene/allowed_collisions", [])
    clear_first = rospy.get_param("~clear_first", True)

    try:
        rospy.wait_for_service("/get_planning_scene", timeout=30.0)
    except rospy.ROSException:
        rospy.logerr("franka_softhand_scene: /get_planning_scene non disponibile, esco.")
        roscpp_shutdown()
        return

    scene = PlanningSceneInterface(synchronous=True)
    # Publisher per i colori: PlanningScene diff su /planning_scene.
    scene_pub = rospy.Publisher("/planning_scene", PlanningScene,
                                queue_size=1, latch=True)
    rospy.sleep(0.5)  # tempo al monitor / publisher di agganciarsi

    if clear_first:
        for name in scene.get_known_object_names():
            scene.remove_world_object(name)

    if not objects:
        rospy.logwarn("franka_softhand_scene: nessun oggetto in ~scene/objects, esco.")
        roscpp_shutdown()
        return

    colors = []
    for obj in objects:
        name = obj["name"]
        otype = obj.get("type", "box")
        pose = make_pose(frame_id, obj["pose"])
        if otype == "box":
            scene.add_box(name, pose, size=tuple(obj["size"]))
        elif otype == "sphere":
            scene.add_sphere(name, pose, radius=float(obj["radius"]))
        elif otype == "cylinder":
            scene.add_cylinder(name, pose,
                               height=float(obj["height"]),
                               radius=float(obj["radius"]))
        else:
            rospy.logwarn("Tipo non supportato: %s (oggetto %s saltato)", otype, name)
            continue

        if wait_for_object(scene, name):
            rospy.loginfo("Aggiunto %s (%s) al frame %s", name, otype, frame_id)
            if "color" in obj:
                colors.append(make_color(name, obj["color"]))
        else:
            rospy.logwarn("Timeout su %s: non risulta nella scena.", name)

    if colors:
        ps = PlanningScene()
        ps.is_diff = True
        ps.object_colors = colors
        # Pubblica qualche volta: il topic e' latched ma alcuni subscriber
        # (rviz) si agganciano leggermente dopo.
        for _ in range(3):
            scene_pub.publish(ps)
            rospy.sleep(0.1)
        rospy.loginfo("Pubblicati colori per %d oggetti", len(colors))

    apply_allowed_collisions(allowed_pairs)

    roscpp_shutdown()


if __name__ == "__main__":
    main()
