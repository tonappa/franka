# recall arguments from docker-compose
ARG ROS_DISTRO
ARG ROS_VERSION

# image base  in base of the ARG
FROM ros:${ROS_DISTRO}-perception

# ================================== ARGS ================================== #
# do not touch these ARGS
ARG ROS_DISTRO
ARG ROS_VERSION
ARG MYUID=1000
ARG MYGID=1000
ARG USER=ros
ARG WORKSPACE_NAME=ros_ws

# ================================ ENV variables ================================ #
ENV DEBIAN_FRONTEND=noninteractive

# ============================ install dependencies =========================== #

# update and install common packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    sudo \
    git \
    bash-completion \
    build-essential \
    cmake \
    software-properties-common \
    libjsoncpp-dev \
    python3-pip \
    python3-rosdep \
    curl \
    wget \
    libgl1-mesa-glx \
    libsm6 \
    libxext6 \
    ros-${ROS_DISTRO}-realsense2-* && \
    rm -rf /var/lib/apt/lists/*

# Build system ROS1/ROS2 + optional packages (write)
RUN if [ "${ROS_VERSION}" = "1" ]; then \
    echo "configuring for ROS1..."; \
    apt-get update && apt-get install --no-install-recommends -y \
    python3-catkin-tools \
    python3-osrf-pycommon \
    ros-${ROS_DISTRO}-franka-ros \
    ros-${ROS_DISTRO}-libfranka \
    ros-${ROS_DISTRO}-panda-moveit-config \
    ros-${ROS_DISTRO}-moveit \
    ros-${ROS_DISTRO}-moveit-visual-tools \
    ros-${ROS_DISTRO}-ros-control \
    ros-${ROS_DISTRO}-ros-controllers \
    ros-${ROS_DISTRO}-combined-robot-hw \
    ros-${ROS_DISTRO}-joint-state-publisher \
    ros-${ROS_DISTRO}-joint-state-publisher-gui \
    ros-${ROS_DISTRO}-geometric-shapes \
    ros-${ROS_DISTRO}-rviz-visual-tools \
    ros-${ROS_DISTRO}-image-geometry \
    ros-${ROS_DISTRO}-rviz \
    ros-${ROS_DISTRO}-handeye \
    ros-${ROS_DISTRO}-criutils \
    ros-${ROS_DISTRO}-baldor; \
    else \
    echo "configuring for ROS2..."; \
    apt-get update && apt-get install --no-install-recommends -y \
    python3-colcon-common-extensions \
    ros-${ROS_DISTRO}-rviz2; \
    \
    # add repository OSRF for Gazebo/Ignition
    wget -qO - https://packages.osrfoundation.org/gazebo.key | sudo apt-key add - && \
    echo "deb [arch=$(dpkg --print-architecture)] http://packages.osrfoundation.org/gazebo/ubuntu-stable $(lsb_release -cs) main" \
    | sudo tee /etc/apt/sources.list.d/gazebo-stable.list; \
    \
    # installa Ignition (Fortress) + integration to ROS
    apt-get update && apt-get install --no-install-recommends -y \
    ros-${ROS_DISTRO}-ros-gz \
    ros-${ROS_DISTRO}-ros-gz-bridge \
    ros-${ROS_DISTRO}-ros-gz-sim; \
    fi && \
    rosdep update && \
    rm -rf /var/lib/apt/lists/*

# ========== Python packages ========== #
# Copy the requirements file into the container
COPY docker/requirements.txt /tmp/requirements.txt

# Install python packages from requirements.txt
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r /tmp/requirements.txt

# ============================= user creation (as ROOT) ============================ #

RUN OLD_USER=$(awk -v uid="$MYUID" -F ':' '$3==uid {print $1}' /etc/passwd) \
    && if [ -z "${OLD_USER}" ]; then \
    addgroup --gid ${MYGID} ${USER} \
    && adduser --gecos "ROS User" --disabled-password --uid ${MYUID} --gid ${MYGID} ${USER} \
    && usermod -a -G dialout,video,sudo ${USER} \
    && echo "${USER} ALL=(ALL) NOPASSWD: ALL" > /etc/sudoers.d/${USER} \
    && chmod 0440 /etc/sudoers.d/${USER}; \
    else \
    usermod -l ${USER} ${OLD_USER} \
    && usermod -d /home/${USER} -m ${USER} \
    && groupmod -g ${MYGID} ${USER} \
    && echo "${USER} ALL=(ALL) NOPASSWD: ALL" > /etc/sudoers.d/${USER} \
    && chmod 0440 /etc/sudoers.d/${USER}; \
    fi

# =============================== assing to ros user ============================== #

USER ${USER}
ENV HOME=/home/${USER}

# ================================  workspace config (as USER) ================================ #

WORKDIR /home/${USER}/${WORKSPACE_NAME}
RUN mkdir -p ./src

# ==================================== Entrypoint (as USER) ==================================== #

COPY docker/entrypoint.sh /usr/local/bin/entrypoint.sh
# note: the user ros has sudo privileges
RUN sudo chmod +x /usr/local/bin/entrypoint.sh

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["bash"]
