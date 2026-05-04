from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

import numpy as np

try:
    import gymnasium as gym
    from gymnasium import spaces
except ImportError as exc:  # pragma: no cover - exercised before dependencies are installed.
    raise ImportError(
        "gymnasium is required. Install project dependencies with "
        "`python -m pip install -r requirements.txt`."
    ) from exc

try:
    import mujoco
except ImportError as exc:  # pragma: no cover - exercised before dependencies are installed.
    raise ImportError(
        "mujoco is required. Install project dependencies with "
        "`python -m pip install -r requirements.txt`."
    ) from exc


ObservationMode = Literal["image", "state"]
DomainRandomizationLevel = Literal[
    "none",
    "visual",
    "visual_camera",
    "visual_camera_control",
    "full",
]


@dataclass(frozen=True)
class RewardTerms:
    reward: float
    dist_xy: float
    dist_z: float
    shaped_distance: float
    desired_z: float
    inserted: bool
    collision: bool


class PegInHoleMujocoEnv(gym.Env):
    """MuJoCo reproduction of the DRL_Peg-in-Hole_UR5 task.

    The default mode mirrors the original repository: the policy observes a
    100x100 grayscale eye-in-hand camera image and controls small Cartesian
    displacements of the tool center point.
    """

    metadata = {"render_modes": ["rgb_array"], "render_fps": 50}

    ARM_JOINT_NAMES = (
        "shoulder_pan",
        "shoulder_lift",
        "elbow",
        "wrist_1",
        "wrist_2",
        "wrist_3",
    )
    IK_JOINT_COUNT = 3
    ROBOT_GEOMS = {
        "base_geom",
        "shoulder_geom",
        "upper_arm_geom",
        "forearm_geom",
        "wrist_1_geom",
        "wrist_2_geom",
        "wrist_3_geom",
        "camera_geom",
        "peg_geom",
    }
    ENV_COLLISION_GEOMS = {
        "floor",
        "table_top",
        "hole_plate",
        "hole_north",
        "hole_south",
        "hole_east",
        "hole_west",
    }

    def __init__(
        self,
        model_path: str | Path | None = None,
        observation_mode: ObservationMode = "image",
        render_mode: Literal["rgb_array"] | None = None,
        image_width: int = 100,
        image_height: int = 100,
        max_steps: int = 200,
        frame_skip: int = 10,
        action_scale: float = 0.005,
        target_low: tuple[float, float, float] = (0.50, 0.00, 0.65),
        target_high: tuple[float, float, float] = (0.60, 0.10, 0.65),
        workspace_low: tuple[float, float, float] = (0.30, -0.25, 0.55),
        workspace_high: tuple[float, float, float] = (0.75, 0.25, 0.95),
        success_xy_tolerance: float = 0.02,
        success_z_tolerance: float = 0.06,
        approach_xy_tolerance: float = 0.06,
        approach_height: float = 0.08,
        staged_xy_weight: float = 2.0,
        staged_z_weight: float = 1.0,
        success_bonus: float = 50.0,
        collision_penalty: float = 150.0,
        timeout_penalty: float = 10.0,
        progress_reward_scale: float = 10.0,
        distance_reward_scale: float = 1.0,
        action_penalty_scale: float = 0.002,
        action_alignment_scale: float = 0.5,
        randomize_domain: bool = False,
        domain_randomization_level: DomainRandomizationLevel = "none",
        camera_position_jitter: tuple[float, float, float] = (0.003, 0.003, 0.003),
        camera_rotation_jitter_deg: float = 2.0,
        image_brightness_range: tuple[float, float] = (0.75, 1.25),
        image_contrast_range: tuple[float, float] = (0.75, 1.25),
        image_noise_std_range: tuple[float, float] = (0.0, 8.0),
        control_action_scale_range: tuple[float, float] = (0.8, 1.2),
        control_action_noise_std_range: tuple[float, float] = (0.0, 0.0008),
        control_action_delay_range: tuple[int, int] = (0, 2),
        control_action_filter_alpha_range: tuple[float, float] = (0.55, 1.0),
    ):
        if observation_mode not in ("image", "state"):
            raise ValueError("observation_mode must be 'image' or 'state'.")
        if domain_randomization_level not in (
            "none",
            "visual",
            "visual_camera",
            "visual_camera_control",
            "full",
        ):
            raise ValueError(
                "domain_randomization_level must be one of: "
                "none, visual, visual_camera, visual_camera_control, full."
            )

        self.observation_mode = observation_mode
        self.render_mode = render_mode
        self.image_width = int(image_width)
        self.image_height = int(image_height)
        self.max_steps = int(max_steps)
        self.frame_skip = int(frame_skip)
        self.action_scale = float(action_scale)
        self.target_low = np.asarray(target_low, dtype=np.float64)
        self.target_high = np.asarray(target_high, dtype=np.float64)
        self.workspace_low = np.asarray(workspace_low, dtype=np.float64)
        self.workspace_high = np.asarray(workspace_high, dtype=np.float64)
        self.success_xy_tolerance = float(success_xy_tolerance)
        self.success_z_tolerance = float(success_z_tolerance)
        self.approach_xy_tolerance = float(approach_xy_tolerance)
        self.approach_height = float(approach_height)
        self.staged_xy_weight = float(staged_xy_weight)
        self.staged_z_weight = float(staged_z_weight)
        self.success_bonus = float(success_bonus)
        self.collision_penalty = float(collision_penalty)
        self.timeout_penalty = float(timeout_penalty)
        self.progress_reward_scale = float(progress_reward_scale)
        self.distance_reward_scale = float(distance_reward_scale)
        self.action_penalty_scale = float(action_penalty_scale)
        self.action_alignment_scale = float(action_alignment_scale)
        if randomize_domain and domain_randomization_level == "none":
            domain_randomization_level = "visual"
        self.domain_randomization_level = domain_randomization_level
        self.randomize_domain = domain_randomization_level != "none"
        self.camera_position_jitter = np.asarray(camera_position_jitter, dtype=np.float64)
        self.camera_rotation_jitter_rad = float(np.deg2rad(camera_rotation_jitter_deg))
        self.image_brightness_range = tuple(float(v) for v in image_brightness_range)
        self.image_contrast_range = tuple(float(v) for v in image_contrast_range)
        self.image_noise_std_range = tuple(float(v) for v in image_noise_std_range)
        self.control_action_scale_range = tuple(float(v) for v in control_action_scale_range)
        self.control_action_noise_std_range = tuple(
            float(v) for v in control_action_noise_std_range
        )
        self.control_action_delay_range = tuple(int(v) for v in control_action_delay_range)
        self.control_action_filter_alpha_range = tuple(
            float(v) for v in control_action_filter_alpha_range
        )
        self._validate_randomization_ranges()
        self.current_image_brightness = 1.0
        self.current_image_contrast = 1.0
        self.current_image_noise_std = 0.0
        self.current_action_scale_multiplier = 1.0
        self.current_action_noise_std = 0.0
        self.current_action_delay = 0
        self.current_action_filter_alpha = 1.0
        self.action_delay_buffer: list[np.ndarray] = []
        self.previous_filtered_action = np.zeros(3, dtype=np.float64)
        self.last_commanded_action = np.zeros(3, dtype=np.float64)
        self.last_applied_action = np.zeros(3, dtype=np.float64)

        asset_path = (
            Path(model_path)
            if model_path is not None
            else Path(__file__).resolve().parents[2] / "assets" / "ur5_peg_in_hole.xml"
        )
        self.model = mujoco.MjModel.from_xml_path(str(asset_path))
        self.data = mujoco.MjData(self.model)
        self.ik_data = mujoco.MjData(self.model)

        self.arm_joint_ids = np.asarray(
            [self._joint_id(name) for name in self.ARM_JOINT_NAMES], dtype=np.int32
        )
        self.arm_qpos_ids = np.asarray(
            [self.model.jnt_qposadr[joint_id] for joint_id in self.arm_joint_ids],
            dtype=np.int32,
        )
        self.arm_dof_ids = np.asarray(
            [self.model.jnt_dofadr[joint_id] for joint_id in self.arm_joint_ids],
            dtype=np.int32,
        )
        self.arm_actuator_ids = np.asarray(
            [self._actuator_id(f"{name}_ctrl") for name in self.ARM_JOINT_NAMES],
            dtype=np.int32,
        )
        self.joint_ranges = self.model.jnt_range[self.arm_joint_ids].copy()
        self.rest_qpos = np.asarray([0.08, -1.2, 1.8, -0.6, 0.0, 0.0], dtype=np.float64)

        self.peg_tip_site_id = self._site_id("peg_tip")
        self.eef_site_id = self._site_id("eef_site")
        self.hole_site_id = self._site_id("hole_site")
        self.wrist_camera_id = self._camera_id("wrist_cam")
        self.hole_body_id = self._body_id("hole_body")
        self.hole_mocap_id = int(self.model.body_mocapid[self.hole_body_id])
        if self.hole_mocap_id < 0:
            raise RuntimeError("hole_body must be a mocap body.")

        self.base_geom_rgba = self.model.geom_rgba.copy()
        self.base_light_diffuse = self.model.light_diffuse.copy()
        self.base_cam_pos = self.model.cam_pos.copy()
        self.base_cam_quat = self.model.cam_quat.copy()

        self.renderer: mujoco.Renderer | None = None
        self.step_count = 0
        self.target_pos = self.target_low.copy()
        self.previous_shaped_distance = 0.0

        self.action_space = spaces.Box(
            low=-self.action_scale,
            high=self.action_scale,
            shape=(3,),
            dtype=np.float32,
        )
        if self.observation_mode == "image":
            self.observation_space = spaces.Dict(
                {
                    "cam_image": spaces.Box(
                        low=0,
                        high=255,
                        shape=(self.image_height, self.image_width, 1),
                        dtype=np.uint8,
                    )
                }
            )
        else:
            self.observation_space = spaces.Box(
                low=-np.inf,
                high=np.inf,
                shape=(21,),
                dtype=np.float32,
            )

    def reset(
        self,
        *,
        seed: int | None = None,
        options: dict[str, Any] | None = None,
    ) -> tuple[np.ndarray | dict[str, np.ndarray], dict[str, Any]]:
        super().reset(seed=seed)
        del options

        mujoco.mj_resetData(self.model, self.data)
        self.step_count = 0

        self._sample_target()
        self._maybe_randomize_domain()
        self._set_arm_qpos(self.data, self.rest_qpos)
        self._set_arm_control(self.rest_qpos)
        self.data.qvel[:] = 0.0

        mujoco.mj_forward(self.model, self.data)
        for _ in range(80):
            mujoco.mj_step(self.model, self.data)

        self.previous_shaped_distance, _ = self._staged_distance()
        obs = self._get_obs()
        return obs, self._get_info()

    def step(
        self, action: np.ndarray
    ) -> tuple[np.ndarray | dict[str, np.ndarray], float, bool, bool, dict[str, Any]]:
        self.step_count += 1
        action = np.asarray(action, dtype=np.float64)
        action = np.clip(action, self.action_space.low, self.action_space.high)
        applied_action = self._apply_control_randomization(action)

        current_tip_pos = self._site_xpos(self.data, self.peg_tip_site_id)
        target_tip_pos = np.clip(
            current_tip_pos + applied_action,
            self.workspace_low,
            self.workspace_high,
        )
        q_target = self._solve_position_ik(target_tip_pos)
        self._set_arm_control(q_target)

        for _ in range(self.frame_skip):
            mujoco.mj_step(self.model, self.data)

        collision = self._check_collision()
        terms = self._compute_reward(collision, applied_action)
        self.previous_shaped_distance = terms.shaped_distance
        terminated = bool(terms.inserted or collision)
        truncated = bool(self.step_count >= self.max_steps)
        reward = terms.reward
        if truncated and not terms.inserted:
            reward -= self.timeout_penalty

        obs = self._get_obs()
        info = self._get_info(terms)
        return obs, reward, terminated, truncated, info

    def render(self) -> np.ndarray:
        return self._render_camera("overview")

    def close(self) -> None:
        if self.renderer is not None:
            self.renderer.close()
            self.renderer = None

    def _validate_randomization_ranges(self) -> None:
        ranges: tuple[tuple[str, tuple[float, float]], ...] = (
            ("image_brightness_range", self.image_brightness_range),
            ("image_contrast_range", self.image_contrast_range),
            ("image_noise_std_range", self.image_noise_std_range),
            ("control_action_scale_range", self.control_action_scale_range),
            ("control_action_noise_std_range", self.control_action_noise_std_range),
            ("control_action_filter_alpha_range", self.control_action_filter_alpha_range),
        )
        for name, value_range in ranges:
            if len(value_range) != 2 or value_range[0] > value_range[1]:
                raise ValueError(f"{name} must be a two-value increasing range.")

        if len(self.control_action_delay_range) != 2:
            raise ValueError("control_action_delay_range must contain two integer values.")
        if self.control_action_delay_range[0] > self.control_action_delay_range[1]:
            raise ValueError("control_action_delay_range must be increasing.")
        if self.control_action_delay_range[0] < 0:
            raise ValueError("control_action_delay_range cannot be negative.")
        if self.control_action_scale_range[0] <= 0.0:
            raise ValueError("control_action_scale_range must stay positive.")
        if self.control_action_noise_std_range[0] < 0.0:
            raise ValueError("control_action_noise_std_range cannot be negative.")
        if self.control_action_filter_alpha_range[0] <= 0.0:
            raise ValueError("control_action_filter_alpha_range must be positive.")
        if self.control_action_filter_alpha_range[1] > 1.0:
            raise ValueError("control_action_filter_alpha_range cannot exceed 1.0.")

    def _joint_id(self, name: str) -> int:
        return self._named_id(mujoco.mjtObj.mjOBJ_JOINT, name)

    def _actuator_id(self, name: str) -> int:
        return self._named_id(mujoco.mjtObj.mjOBJ_ACTUATOR, name)

    def _site_id(self, name: str) -> int:
        return self._named_id(mujoco.mjtObj.mjOBJ_SITE, name)

    def _body_id(self, name: str) -> int:
        return self._named_id(mujoco.mjtObj.mjOBJ_BODY, name)

    def _camera_id(self, name: str) -> int:
        return self._named_id(mujoco.mjtObj.mjOBJ_CAMERA, name)

    def _named_id(self, obj_type: mujoco.mjtObj, name: str) -> int:
        obj_id = mujoco.mj_name2id(self.model, obj_type, name)
        if obj_id < 0:
            raise RuntimeError(f"MuJoCo object not found: {name}")
        return int(obj_id)

    def _set_arm_qpos(self, data: mujoco.MjData, qpos: np.ndarray) -> None:
        data.qpos[self.arm_qpos_ids] = qpos

    def _set_arm_control(self, qpos: np.ndarray) -> None:
        ctrlrange = self.model.actuator_ctrlrange[self.arm_actuator_ids]
        qpos = np.clip(qpos, ctrlrange[:, 0], ctrlrange[:, 1])
        self.data.ctrl[self.arm_actuator_ids] = qpos

    def _sample_target(self) -> None:
        self.target_pos = self.np_random.uniform(self.target_low, self.target_high)
        self.data.mocap_pos[self.hole_mocap_id] = self.target_pos
        self.data.mocap_quat[self.hole_mocap_id] = np.asarray([1.0, 0.0, 0.0, 0.0])

    def _maybe_randomize_domain(self) -> None:
        self._restore_domain()
        if not self.randomize_domain:
            return

        hole_color = self.np_random.uniform(0.25, 0.85, size=3)
        table_color = self.np_random.uniform(0.15, 0.55, size=3)
        peg_color = self.np_random.uniform(0.1, 0.9, size=3)
        for name in ("hole_plate", "hole_north", "hole_south", "hole_east", "hole_west"):
            self.model.geom_rgba[self._geom_id(name), :3] = hole_color
        self.model.geom_rgba[self._geom_id("table_top"), :3] = table_color
        self.model.geom_rgba[self._geom_id("peg_geom"), :3] = peg_color
        self.model.light_diffuse[:, :3] = self.np_random.uniform(0.45, 1.05, size=(self.model.nlight, 3))

        if self.domain_randomization_level in ("visual_camera", "visual_camera_control", "full"):
            self._randomize_wrist_camera()
            self.current_image_brightness = float(
                self.np_random.uniform(*self.image_brightness_range)
            )
            self.current_image_contrast = float(
                self.np_random.uniform(*self.image_contrast_range)
            )
            self.current_image_noise_std = float(
                self.np_random.uniform(*self.image_noise_std_range)
            )

        if self.domain_randomization_level in ("visual_camera_control", "full"):
            self._randomize_control_channel()

    def _restore_domain(self) -> None:
        self.model.geom_rgba[:] = self.base_geom_rgba
        self.model.light_diffuse[:] = self.base_light_diffuse
        self.model.cam_pos[:] = self.base_cam_pos
        self.model.cam_quat[:] = self.base_cam_quat
        self.current_image_brightness = 1.0
        self.current_image_contrast = 1.0
        self.current_image_noise_std = 0.0
        self.current_action_scale_multiplier = 1.0
        self.current_action_noise_std = 0.0
        self.current_action_delay = 0
        self.current_action_filter_alpha = 1.0
        self.action_delay_buffer = []
        self.previous_filtered_action = np.zeros(3, dtype=np.float64)
        self.last_commanded_action = np.zeros(3, dtype=np.float64)
        self.last_applied_action = np.zeros(3, dtype=np.float64)

    def _randomize_control_channel(self) -> None:
        self.current_action_scale_multiplier = float(
            self.np_random.uniform(*self.control_action_scale_range)
        )
        self.current_action_noise_std = float(
            self.np_random.uniform(*self.control_action_noise_std_range)
        )
        delay_low, delay_high = self.control_action_delay_range
        self.current_action_delay = int(
            self.np_random.integers(delay_low, delay_high + 1)
        )
        self.current_action_filter_alpha = float(
            self.np_random.uniform(*self.control_action_filter_alpha_range)
        )
        self.action_delay_buffer = [
            np.zeros(3, dtype=np.float64) for _ in range(self.current_action_delay)
        ]
        self.previous_filtered_action = np.zeros(3, dtype=np.float64)

    def _apply_control_randomization(self, action: np.ndarray) -> np.ndarray:
        self.last_commanded_action = action.copy()
        if self.domain_randomization_level not in ("visual_camera_control", "full"):
            self.last_applied_action = action.copy()
            return action

        scaled_action = action * self.current_action_scale_multiplier
        if self.current_action_delay > 0:
            self.action_delay_buffer.append(scaled_action.copy())
            delayed_action = self.action_delay_buffer.pop(0)
        else:
            delayed_action = scaled_action

        noisy_action = delayed_action.copy()
        if self.current_action_noise_std > 0.0:
            noisy_action += self.np_random.normal(
                0.0,
                self.current_action_noise_std,
                size=noisy_action.shape,
            )

        alpha = self.current_action_filter_alpha
        filtered_action = (
            alpha * noisy_action + (1.0 - alpha) * self.previous_filtered_action
        )
        applied_action = np.clip(
            filtered_action,
            self.action_space.low,
            self.action_space.high,
        )
        self.previous_filtered_action = applied_action.copy()
        self.last_applied_action = applied_action.copy()
        return applied_action

    def _randomize_wrist_camera(self) -> None:
        pos_jitter = self.np_random.uniform(
            -self.camera_position_jitter,
            self.camera_position_jitter,
        )
        self.model.cam_pos[self.wrist_camera_id] = (
            self.base_cam_pos[self.wrist_camera_id] + pos_jitter
        )

        euler = self.np_random.uniform(
            -self.camera_rotation_jitter_rad,
            self.camera_rotation_jitter_rad,
            size=3,
        )
        delta_quat = self._euler_xyz_to_quat(euler)
        camera_quat = self._quat_multiply(self.base_cam_quat[self.wrist_camera_id], delta_quat)
        self.model.cam_quat[self.wrist_camera_id] = camera_quat / np.linalg.norm(camera_quat)

    def _euler_xyz_to_quat(self, euler: np.ndarray) -> np.ndarray:
        roll, pitch, yaw = euler
        cr, sr = np.cos(roll * 0.5), np.sin(roll * 0.5)
        cp, sp = np.cos(pitch * 0.5), np.sin(pitch * 0.5)
        cy, sy = np.cos(yaw * 0.5), np.sin(yaw * 0.5)
        return np.asarray(
            [
                cr * cp * cy + sr * sp * sy,
                sr * cp * cy - cr * sp * sy,
                cr * sp * cy + sr * cp * sy,
                cr * cp * sy - sr * sp * cy,
            ],
            dtype=np.float64,
        )

    def _quat_multiply(self, q1: np.ndarray, q2: np.ndarray) -> np.ndarray:
        w1, x1, y1, z1 = q1
        w2, x2, y2, z2 = q2
        return np.asarray(
            [
                w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2,
                w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2,
                w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2,
                w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2,
            ],
            dtype=np.float64,
        )

    def _geom_id(self, name: str) -> int:
        return self._named_id(mujoco.mjtObj.mjOBJ_GEOM, name)

    def _site_xpos(self, data: mujoco.MjData, site_id: int) -> np.ndarray:
        return data.site_xpos[site_id].copy()

    def _solve_position_ik(self, target_pos: np.ndarray) -> np.ndarray:
        data = self.ik_data
        data.qpos[:] = self.data.qpos
        data.qvel[:] = 0.0
        data.mocap_pos[:] = self.data.mocap_pos
        data.mocap_quat[:] = self.data.mocap_quat

        q = data.qpos[self.arm_qpos_ids].copy()
        q[self.IK_JOINT_COUNT :] = self.rest_qpos[self.IK_JOINT_COUNT :]

        ik_dof_ids = self.arm_dof_ids[: self.IK_JOINT_COUNT]
        ik_qpos_ids = self.arm_qpos_ids[: self.IK_JOINT_COUNT]
        lower = self.joint_ranges[: self.IK_JOINT_COUNT, 0]
        upper = self.joint_ranges[: self.IK_JOINT_COUNT, 1]

        jacp = np.zeros((3, self.model.nv), dtype=np.float64)
        jacr = np.zeros((3, self.model.nv), dtype=np.float64)
        damping = 1e-3

        for _ in range(18):
            data.qpos[self.arm_qpos_ids] = q
            mujoco.mj_forward(self.model, data)

            error = target_pos - data.site_xpos[self.peg_tip_site_id]
            if np.linalg.norm(error) < 1e-4:
                break

            mujoco.mj_jacSite(self.model, data, jacp, jacr, self.peg_tip_site_id)
            jpos = jacp[:, ik_dof_ids]
            lhs = jpos @ jpos.T + damping * np.eye(3)
            dq = jpos.T @ np.linalg.solve(lhs, error)
            dq = np.clip(dq, -0.06, 0.06)

            q[: self.IK_JOINT_COUNT] = np.clip(
                q[: self.IK_JOINT_COUNT] + dq,
                lower,
                upper,
            )

        q[self.IK_JOINT_COUNT :] = self.rest_qpos[self.IK_JOINT_COUNT :]
        return q

    def _staged_distance(self) -> tuple[float, float]:
        tip_pos = self._site_xpos(self.data, self.peg_tip_site_id)
        dist_xy = float(np.linalg.norm(tip_pos[:2] - self.target_pos[:2]))
        descent_fraction = min(1.0, dist_xy / self.approach_xy_tolerance)
        desired_z = float(self.target_pos[2] + self.approach_height * descent_fraction)
        z_error = float(abs(tip_pos[2] - desired_z))
        shaped_distance = float(
            self.staged_xy_weight * dist_xy + self.staged_z_weight * z_error
        )
        return shaped_distance, desired_z

    def _compute_reward(self, collision: bool, action: np.ndarray | None = None) -> RewardTerms:
        tip_pos = self._site_xpos(self.data, self.peg_tip_site_id)
        shaped_distance, desired_z = self._staged_distance()
        progress = self.previous_shaped_distance - shaped_distance

        dist_xy = float(np.linalg.norm(tip_pos[:2] - self.target_pos[:2]))
        dist_z = float(abs(tip_pos[2] - self.target_pos[2]))
        desired_tip_pos = np.asarray(
            [self.target_pos[0], self.target_pos[1], desired_z],
            dtype=np.float64,
        )
        desired_delta = desired_tip_pos - tip_pos
        desired_delta_norm = float(np.linalg.norm(desired_delta))
        inserted = bool(
            dist_xy < self.success_xy_tolerance
            and dist_z < self.success_z_tolerance
        )

        action_norm = 0.0 if action is None else float(np.linalg.norm(action / self.action_scale))
        action_alignment = 0.0
        if action is not None and desired_delta_norm > 1e-6:
            action_alignment = float(
                np.dot(action / self.action_scale, desired_delta / desired_delta_norm)
            )
        reward = (
            self.progress_reward_scale * progress
            - self.distance_reward_scale * shaped_distance
            + self.action_alignment_scale * action_alignment
            - self.action_penalty_scale * action_norm
            - 0.01
        )
        if inserted:
            reward += self.success_bonus
        if collision and not inserted:
            reward -= self.collision_penalty

        return RewardTerms(
            reward=float(reward),
            dist_xy=dist_xy,
            dist_z=dist_z,
            shaped_distance=shaped_distance,
            desired_z=desired_z,
            inserted=inserted,
            collision=bool(collision),
        )

    def _check_collision(self) -> bool:
        tip_pos = self._site_xpos(self.data, self.peg_tip_site_id)
        dist_xy = np.linalg.norm(tip_pos[:2] - self.target_pos[:2])
        close_to_hole = dist_xy < 0.02 and abs(tip_pos[2] - self.target_pos[2]) < 0.15
        if close_to_hole:
            return False

        for contact_index in range(self.data.ncon):
            contact = self.data.contact[contact_index]
            geom1 = self._geom_name(contact.geom1)
            geom2 = self._geom_name(contact.geom2)
            robot_env_contact = (
                geom1 in self.ROBOT_GEOMS
                and geom2 in self.ENV_COLLISION_GEOMS
            ) or (
                geom2 in self.ROBOT_GEOMS
                and geom1 in self.ENV_COLLISION_GEOMS
            )
            if robot_env_contact:
                return True
        return False

    def _geom_name(self, geom_id: int) -> str:
        return mujoco.mj_id2name(self.model, mujoco.mjtObj.mjOBJ_GEOM, geom_id) or ""

    def _get_obs(self) -> np.ndarray | dict[str, np.ndarray]:
        if self.observation_mode == "state":
            return self._get_state_obs()
        image = self._render_camera("wrist_cam")
        gray = (
            0.299 * image[:, :, 0]
            + 0.587 * image[:, :, 1]
            + 0.114 * image[:, :, 2]
        )
        gray = self._augment_gray_image(gray).astype(np.uint8)
        return {"cam_image": gray[:, :, None]}

    def _augment_gray_image(self, gray: np.ndarray) -> np.ndarray:
        if (
            self.current_image_brightness == 1.0
            and self.current_image_contrast == 1.0
            and self.current_image_noise_std == 0.0
        ):
            return np.clip(gray, 0, 255)

        image = gray.astype(np.float32)
        image = (image - 127.5) * self.current_image_contrast + 127.5
        image *= self.current_image_brightness
        if self.current_image_noise_std > 0.0:
            image += self.np_random.normal(
                0.0,
                self.current_image_noise_std,
                size=image.shape,
            )
        return np.clip(image, 0, 255)

    def _get_state_obs(self) -> np.ndarray:
        tip_pos = self._site_xpos(self.data, self.peg_tip_site_id)
        qpos = self.data.qpos[self.arm_qpos_ids]
        _, desired_z = self._staged_distance()
        desired_tip_pos = np.asarray(
            [self.target_pos[0], self.target_pos[1], desired_z],
            dtype=np.float64,
        )
        obs = np.concatenate(
            [
                tip_pos,
                self.target_pos,
                self.target_pos - tip_pos,
                desired_tip_pos,
                desired_tip_pos - tip_pos,
                qpos,
            ]
        )
        return obs.astype(np.float32)

    def _render_camera(self, camera_name: str) -> np.ndarray:
        if self.renderer is None:
            self.renderer = mujoco.Renderer(
                self.model,
                height=self.image_height,
                width=self.image_width,
            )
        self.renderer.update_scene(self.data, camera=camera_name)
        return self.renderer.render()

    def _get_info(self, terms: RewardTerms | None = None) -> dict[str, Any]:
        if terms is None:
            terms = self._compute_reward(collision=False, action=None)
        tip_pos = self._site_xpos(self.data, self.peg_tip_site_id)
        return {
            "insertion_success": terms.inserted,
            "dist_xy": terms.dist_xy,
            "dist_z": terms.dist_z,
            "shaped_distance": terms.shaped_distance,
            "desired_z": terms.desired_z,
            "collision": terms.collision,
            "target_pos": self.target_pos.astype(np.float32),
            "peg_tip_pos": tip_pos.astype(np.float32),
            "step_count": self.step_count,
            "commanded_action": self.last_commanded_action.astype(np.float32),
            "applied_action": self.last_applied_action.astype(np.float32),
            "control_action_scale_multiplier": self.current_action_scale_multiplier,
            "control_action_noise_std": self.current_action_noise_std,
            "control_action_delay": self.current_action_delay,
            "control_action_filter_alpha": self.current_action_filter_alpha,
        }
