# Franka Panda + qbSoftHand — ROS Noetic (Docker)

Workspace for controlling the Franka Panda robot with MoveIt and qbSoftHand as end effector, running on ROS Noetic inside Docker.

> **Note:** requires a PC with an NVIDIA GPU.

---

## Requirements

- Linux with NVIDIA drivers installed (`nvidia-smi` must work)
- Docker Engine and Docker Compose installed
- Active X11 graphical session on the host (`DISPLAY=:0`)
- User in the `audio` and `video` groups

---

## 1. Clone the repository

```bash
git clone --recurse-submodules -b softhand git@github.com:tonappa/franka.git
cd franka
```

The `--recurse-submodules` flag automatically downloads the external packages:
- `src/utils/qbdevice-ros` (including its nested submodules)
- `src/utils/qbhand-ros`

If you already cloned without `--recurse-submodules`, fetch the submodules with:

```bash
git submodule update --init --recursive
```

---

## 2. Build the Docker image

```bash
./run_docker.sh build
```

This installs ROS Noetic with Franka, MoveIt, and controller packages.

---

## 3. Run the container

```bash
./run_docker.sh run
```

The container mounts the workspace at `/home/ros/franka`, forwards the GUI via X11, and enables the NVIDIA GPU.

---

## 4. Build the catkin workspace

Inside the container:

```bash
catkin build
source devel/setup.bash
```

---

## 5. Stop the container

```bash
./run_docker.sh down
```

---

## Project structure

```
franka/
├── docker/
│   ├── Dockerfile          # ROS Noetic image with Franka + MoveIt
│   ├── entrypoint.sh       # Automatic ROS environment sourcing
│   └── requirements.txt    # Python dependencies (optional)
├── src/
│   └── utils/
│       ├── qbdevice-ros/   # qbrobotics driver (submodule)
│       └── qbhand-ros/     # qbSoftHand packages (submodule)
├── docker-compose.yaml
└── run_docker.sh
```

---

## Credits

- [Do Won Park](https://github.com/tonappa) — Istituto Italiano di Tecnologia
