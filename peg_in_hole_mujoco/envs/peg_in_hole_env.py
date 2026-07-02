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

from peg_in_hole_mujoco.paths import resolve_model_path


ObservationMode = Literal["image", "state"]
InitializationMode = Literal["fixed", "target_relative_high_start"]
IkControlMode = Literal["position", "pose", "pose_tip_priority"]
GeometryFixtureMode = Literal["box_wall", "true_mesh"]
GeometryTrueFixtureVariant = Literal["nominal", "tight_yaw"]
GeometryProfile = Literal[
    "single",
    "round_round",
    "round_square",
    "square_square",
    "hex_hex",
    "triangle_triangle",
    "slot_slot",
    "rectangular_key",
    "mixed_basic",
    "mixed_same_shape",
]
DomainRandomizationLevel = Literal[
    "none",
    "visual",
    "visual_camera",
    "visual_camera_control",
    "full_light_geometry",
    "full_contact_light",
    "full",
]

DOMAIN_RANDOMIZATION_LEVELS = (
    "none",
    "visual",
    "visual_camera",
    "visual_camera_control",
    "full_light_geometry",
    "full_contact_light",
    "full",
)

INITIALIZATION_MODES = (
    "fixed",
    "target_relative_high_start",
)
GEOMETRY_FIXTURE_MODES = (
    "box_wall",
    "true_mesh",
)
GEOMETRY_TRUE_FIXTURE_VARIANTS = (
    "nominal",
    "tight_yaw",
)

GEOMETRY_PROFILES = (
    "single",
    "round_round",
    "round_square",
    "square_square",
    "hex_hex",
    "triangle_triangle",
    "slot_slot",
    "rectangular_key",
    "mixed_basic",
    "mixed_same_shape",
)

PRIMARY_HOLE_WALL_NAMES = ("hole_north", "hole_south", "hole_east", "hole_west")
OPTIONAL_HOLE_WALL_NAMES = tuple(f"hole_aux_{index}" for index in range(8))
ALL_HOLE_WALL_NAMES = PRIMARY_HOLE_WALL_NAMES + OPTIONAL_HOLE_WALL_NAMES
POLYGON_HOLE_VISUAL_WALL_NAMES = tuple(f"hole_polygon_visual_{index}" for index in range(6))
TRUE_FIXTURE_WALL_NAMES = tuple(f"true_fixture_wall_{index}" for index in range(12))
POLYGONAL_PEG_MESH_NAMES = {
    "hex": "peg_hex_mesh",
    "triangle": "peg_triangle_mesh",
    "slot": "peg_slot_mesh",
    "rectangular_key": "peg_keyhole_mesh",
}
POLYGONAL_PEG_TIP_CAP_VISUAL_MESH_NAMES = {
    "hex": "peg_hex_tip_cap_visual_mesh",
    "triangle": "peg_triangle_tip_cap_visual_mesh",
    "rectangular_key": "peg_keyhole_tip_cap_visual_mesh",
}
POLYGONAL_PEG_TIP_OUTLINE_VISUAL_MESH_NAMES = {
    "hex": "peg_hex_tip_outline_visual_mesh",
    "triangle": "peg_triangle_tip_outline_visual_mesh",
    "rectangular_key": "peg_keyhole_tip_outline_visual_mesh",
}
POLYGONAL_PEG_SIDE_EDGE_VISUAL_MESH_NAMES = {
    "hex": "peg_hex_side_edge_visual_mesh",
    "triangle": "peg_triangle_side_edge_visual_mesh",
}
POLYGONAL_PEG_TIP_CAP_VISUAL_RGBA = np.asarray([0.82, 0.92, 1.0, 0.55], dtype=np.float64)
POLYGONAL_PEG_TIP_OUTLINE_VISUAL_RGBA = np.asarray([0.015, 0.018, 0.025, 0.92], dtype=np.float64)
POLYGONAL_PEG_SIDE_EDGE_VISUAL_RGBA = np.asarray([0.015, 0.018, 0.025, 0.42], dtype=np.float64)
SHAPE_YAW_PERIOD_DEG = {
    "square_square": 90.0,
    "triangle_triangle": 120.0,
    "hex_hex": 60.0,
    "slot_slot": 180.0,
    "rectangular_key": 360.0,
}
YAW_SENSITIVE_GEOMETRY_PROFILES = tuple(SHAPE_YAW_PERIOD_DEG.keys())
TRUE_FIXTURE_WALL_MESH_NAMES = {
    "hex": "true_hex_wall_mesh",
    "triangle": "true_triangle_wall_mesh",
    "slot_side": "true_slot_side_wall_mesh",
    "slot_arc": "true_slot_arc_wall_mesh",
    "keyhole_tab_side": "true_keyhole_tab_side_wall_mesh",
    "keyhole_tab_front": "true_keyhole_tab_front_wall_mesh",
    "keyhole_arc": "true_keyhole_arc_wall_mesh",
    "hex_tight_yaw": "true_hex_wall_tight_yaw_mesh",
    "triangle_tight_yaw": "true_triangle_wall_tight_yaw_mesh",
    "keyhole_tab_side_tight_yaw": "true_keyhole_tab_side_tight_yaw_mesh",
    "keyhole_tab_front_tight_yaw": "true_keyhole_tab_front_tight_yaw_mesh",
    "keyhole_arc_tight_yaw": "true_keyhole_arc_tight_yaw_mesh",
}
TRUE_FIXTURE_VISUAL_MESH_NAMES = {
    "hex": "true_hex_fixture_visual_mesh",
    "triangle": "true_triangle_fixture_visual_mesh",
    "slot": "true_slot_fixture_visual_mesh",
    "rectangular_key": "true_keyhole_fixture_visual_mesh",
    "hex_tight_yaw": "true_hex_fixture_visual_tight_yaw_mesh",
    "triangle_tight_yaw": "true_triangle_fixture_visual_tight_yaw_mesh",
    "rectangular_key_tight_yaw": "true_keyhole_fixture_visual_tight_yaw_mesh",
}
TRIANGLE_SCAFFOLD_HOLE_HALF_SIZE_FLOOR_MULTIPLIER = 2.2
TRIANGLE_TRUE_FIXTURE_MAX_HOLE_DIAMETER_MULTIPLIER = 2.0
SLOT_TRUE_FIXTURE_ARC_SEGMENTS_PER_END = 3
KEYHOLE_HOLE_TAB_HALF_WIDTH_RATIO = 0.50
KEYHOLE_HOLE_TAB_LENGTH_RATIO = 0.5625
KEYHOLE_PEG_TAB_HALF_WIDTH_RATIO = 5.0 / 12.0
KEYHOLE_PEG_TAB_LENGTH_RATIO = 6.5 / 12.0
KEYHOLE_TRUE_FIXTURE_ARC_SEGMENTS = 8
TIGHT_YAW_SQUARE_CLEARANCE = 0.00075
TIGHT_YAW_HEX_CLEARANCE = 0.00050
TIGHT_YAW_TRIANGLE_CLEARANCE = 0.00075
TIGHT_YAW_KEYHOLE_CLEARANCE = 0.00100
TIGHT_YAW_BASE_PEG_RADIUS = 0.012
TIGHT_YAW_KEYHOLE_PEG_TAB_HALF_WIDTH = 0.005
TIGHT_YAW_KEYHOLE_PEG_TAB_LENGTH = 0.0065


@dataclass(frozen=True)
class GeometrySpec:
    name: str
    peg_shape: str
    hole_shape: str
    hole_half_size: float
    peg_radius: float
    peg_half_extents: tuple[float, float, float] | None = None
    hole_half_extents: tuple[float, float] | None = None
    hole_polygon_sides: int | None = None
    peg_mesh_name: str | None = None

    @property
    def hole_clearance(self) -> float:
        return self.hole_half_size - self.peg_radius


@dataclass(frozen=True)
class RewardTerms:
    reward: float
    dist_xy: float
    dist_z: float
    shaped_distance: float
    desired_z: float
    inserted: bool
    collision: bool
    success_shape_yaw_required: bool
    success_shape_yaw_ok: bool
    success_shape_yaw_error_deg: float
    success_shape_yaw_tolerance_deg: float


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
        "upper_arm_shoulder_geom",
        "upper_arm_geom",
        "forearm_elbow_geom",
        "forearm_geom",
        "wrist_1_geom",
        "wrist_2_base_geom",
        "wrist_2_geom",
        "wrist_3_geom",
        "camera_geom",
        "peg_geom",
    }
    ENV_COLLISION_GEOMS = {
        "floor",
        "table_top",
        "hole_plate",
        *ALL_HOLE_WALL_NAMES,
    }
    CONTROL_STATE_DIM = 10

    def __init__(
        self,
        model_path: str | Path | None = None,
        observation_mode: ObservationMode = "image",
        render_mode: Literal["rgb_array"] | None = None,
        image_width: int = 100,
        image_height: int = 100,
        include_near_hole_crop: bool = False,
        near_hole_crop_size: int = 64,
        near_hole_crop_source_size: int | None = None,
        near_hole_crop_source_size_range: tuple[int, int] | None = None,
        near_hole_crop_offset: tuple[int, int] = (0, 0),
        include_control_state: bool = False,
        image_frame_stack: int = 1,
        max_steps: int = 200,
        frame_skip: int = 10,
        action_scale: float = 0.005,
        target_low: tuple[float, float, float] = (0.50, 0.00, 0.65),
        target_high: tuple[float, float, float] = (0.60, 0.10, 0.65),
        workspace_low: tuple[float, float, float] = (0.30, -0.25, 0.55),
        workspace_high: tuple[float, float, float] = (0.75, 0.25, 0.95),
        success_xy_tolerance: float = 0.02,
        success_z_tolerance: float = 0.06,
        success_shape_yaw_tolerance_deg: float | None = None,
        success_shape_yaw_profiles: tuple[str, ...] | None = None,
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
        wrist_camera_pos_offset: tuple[float, float, float] = (0.0, 0.0, 0.0),
        wrist_camera_rot_offset_deg: tuple[float, float, float] = (0.0, 0.0, 0.0),
        wrist_camera_fovy: float | None = None,
        camera_position_jitter: tuple[float, float, float] = (0.003, 0.003, 0.003),
        camera_rotation_jitter_deg: float = 2.0,
        image_brightness_range: tuple[float, float] = (0.75, 1.25),
        image_contrast_range: tuple[float, float] = (0.75, 1.25),
        image_noise_std_range: tuple[float, float] = (0.0, 8.0),
        control_action_scale_range: tuple[float, float] = (0.8, 1.2),
        control_action_noise_std_range: tuple[float, float] = (0.0, 0.0008),
        control_action_delay_range: tuple[int, int] = (0, 2),
        control_action_filter_alpha_range: tuple[float, float] = (0.55, 1.0),
        geometry_hole_center_xy_jitter: tuple[float, float] = (0.002, 0.002),
        geometry_fixture_height_jitter: float = 0.001,
        geometry_table_height_jitter: float = 0.001,
        geometry_hole_half_size_range: tuple[float, float] = (0.017, 0.021),
        geometry_peg_radius_range: tuple[float, float] = (0.0115, 0.0125),
        geometry_profile: GeometryProfile = "single",
        geometry_fixture_mode: GeometryFixtureMode = "box_wall",
        geometry_true_fixture_variant: GeometryTrueFixtureVariant = "nominal",
        enable_peg_tip_visual_helpers: bool = True,
        geometry_square_peg_half_size_range: tuple[float, float] = (0.0105, 0.0125),
        geometry_mixed_square_probability: float = 0.5,
        contact_friction_multiplier_range: tuple[float, float] = (0.7, 1.3),
        contact_solref_time_multiplier_range: tuple[float, float] = (0.8, 1.25),
        contact_solref_damping_multiplier_range: tuple[float, float] = (0.8, 1.2),
        contact_solimp_width_multiplier_range: tuple[float, float] = (0.8, 1.2),
        dynamics_joint_damping_multiplier_range: tuple[float, float] = (0.8, 1.2),
        dynamics_actuator_kp_multiplier_range: tuple[float, float] = (0.8, 1.2),
        nominal_joint_damping_multiplier: float = 1.0,
        nominal_actuator_kp_multiplier: float = 1.0,
        ik_joint_count: int | None = None,
        ik_control_mode: IkControlMode = "position",
        ik_orientation_weight: float = 0.12,
        ik_posture_weight: float = 0.01,
        ik_wrist_posture_weight: float = 0.0,
        ik_wrist_anchor_weight: float = 0.0,
        ik_continuity_weight: float = 0.0,
        ik_wrist_continuity_weight: float = 0.0,
        ik_max_wrist_target_delta_deg: float | None = None,
        ik_nearest_wrist_target_equivalent: bool = False,
        ik_step_limit: float = 0.06,
        ik_max_iterations: int = 24,
        initialization_mode: InitializationMode = "fixed",
        initial_tip_z_above_range: tuple[float, float] = (0.15, 0.25),
        initial_tip_xy_offset_range: tuple[float, float] = (0.08, 0.16),
        initial_tip_xy_angle_range_deg: tuple[float, float] = (0.0, 360.0),
        initial_shape_yaw_error_range_deg: tuple[float, float] | None = None,
        initial_shape_yaw_ik_orientation_weight: float = 0.45,
        initial_shape_yaw_ik_max_iterations: int = 96,
        initial_shape_yaw_max_wrist_rest_delta_deg: float | None = None,
        initial_ik_max_attempts: int = 20,
    ):
        if observation_mode not in ("image", "state"):
            raise ValueError("observation_mode must be 'image' or 'state'.")
        if initialization_mode not in INITIALIZATION_MODES:
            raise ValueError(
                "initialization_mode must be one of: "
                + ", ".join(INITIALIZATION_MODES)
                + "."
            )
        if ik_control_mode not in ("position", "pose", "pose_tip_priority"):
            raise ValueError(
                "ik_control_mode must be 'position', 'pose', or 'pose_tip_priority'."
            )
        if domain_randomization_level not in DOMAIN_RANDOMIZATION_LEVELS:
            raise ValueError(
                "domain_randomization_level must be one of: "
                + ", ".join(DOMAIN_RANDOMIZATION_LEVELS)
                + "."
            )
        if geometry_profile not in GEOMETRY_PROFILES:
            raise ValueError(
                "geometry_profile must be one of: "
                + ", ".join(GEOMETRY_PROFILES)
                + "."
            )
        if geometry_fixture_mode not in GEOMETRY_FIXTURE_MODES:
            raise ValueError(
                "geometry_fixture_mode must be one of: "
                + ", ".join(GEOMETRY_FIXTURE_MODES)
                + "."
            )
        if geometry_true_fixture_variant not in GEOMETRY_TRUE_FIXTURE_VARIANTS:
            raise ValueError(
                "geometry_true_fixture_variant must be one of: "
                + ", ".join(GEOMETRY_TRUE_FIXTURE_VARIANTS)
                + "."
            )
        if (
            success_shape_yaw_tolerance_deg is not None
            and float(success_shape_yaw_tolerance_deg) < 0.0
        ):
            raise ValueError("success_shape_yaw_tolerance_deg cannot be negative.")
        if success_shape_yaw_profiles is not None:
            invalid_yaw_profiles = sorted(
                set(str(profile) for profile in success_shape_yaw_profiles)
                - set(YAW_SENSITIVE_GEOMETRY_PROFILES)
            )
            if invalid_yaw_profiles:
                raise ValueError(
                    "success_shape_yaw_profiles must use yaw-sensitive concrete profiles: "
                    + ", ".join(YAW_SENSITIVE_GEOMETRY_PROFILES)
                    + f". Invalid: {', '.join(invalid_yaw_profiles)}."
                )

        self.observation_mode = observation_mode
        self.render_mode = render_mode
        self.image_width = int(image_width)
        self.image_height = int(image_height)
        self.include_near_hole_crop = bool(include_near_hole_crop)
        self.near_hole_crop_size = int(near_hole_crop_size)
        self.near_hole_crop_source_size = (
            int(near_hole_crop_source_size)
            if near_hole_crop_source_size is not None
            else int(near_hole_crop_size)
        )
        self.near_hole_crop_source_size_range = (
            tuple(int(value) for value in near_hole_crop_source_size_range)
            if near_hole_crop_source_size_range is not None
            else None
        )
        self.current_near_hole_crop_source_size = self.near_hole_crop_source_size
        self.near_hole_crop_offset = tuple(int(value) for value in near_hole_crop_offset)
        self.include_control_state = bool(include_control_state)
        self.image_frame_stack = int(image_frame_stack)
        self.max_steps = int(max_steps)
        self.frame_skip = int(frame_skip)
        self.action_scale = float(action_scale)
        self.target_low = np.asarray(target_low, dtype=np.float64)
        self.target_high = np.asarray(target_high, dtype=np.float64)
        self.workspace_low = np.asarray(workspace_low, dtype=np.float64)
        self.workspace_high = np.asarray(workspace_high, dtype=np.float64)
        self.success_xy_tolerance = float(success_xy_tolerance)
        self.success_z_tolerance = float(success_z_tolerance)
        self.success_shape_yaw_tolerance_deg = (
            None
            if success_shape_yaw_tolerance_deg is None
            or float(success_shape_yaw_tolerance_deg) <= 0.0
            else float(success_shape_yaw_tolerance_deg)
        )
        yaw_profiles = (
            YAW_SENSITIVE_GEOMETRY_PROFILES
            if success_shape_yaw_profiles is None
            else tuple(str(profile) for profile in success_shape_yaw_profiles)
        )
        self.success_shape_yaw_profiles = yaw_profiles
        self.success_shape_yaw_profile_set = set(yaw_profiles)
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
        self.requested_ik_joint_count = ik_joint_count
        self.ik_control_mode = ik_control_mode
        self.ik_orientation_weight = float(ik_orientation_weight)
        self.ik_posture_weight = float(ik_posture_weight)
        self.ik_wrist_posture_weight = float(ik_wrist_posture_weight)
        self.ik_wrist_anchor_weight = float(ik_wrist_anchor_weight)
        self.ik_continuity_weight = float(ik_continuity_weight)
        self.ik_wrist_continuity_weight = float(ik_wrist_continuity_weight)
        self.ik_max_wrist_target_delta_rad = (
            None
            if ik_max_wrist_target_delta_deg is None
            or float(ik_max_wrist_target_delta_deg) <= 0.0
            else float(np.deg2rad(ik_max_wrist_target_delta_deg))
        )
        self.ik_nearest_wrist_target_equivalent = bool(
            ik_nearest_wrist_target_equivalent
        )
        self.ik_step_limit = float(ik_step_limit)
        self.ik_max_iterations = int(ik_max_iterations)
        if randomize_domain and domain_randomization_level == "none":
            domain_randomization_level = "visual"
        self.domain_randomization_level = domain_randomization_level
        self.randomize_domain = domain_randomization_level != "none"
        self.wrist_camera_pos_offset = np.asarray(wrist_camera_pos_offset, dtype=np.float64)
        self.wrist_camera_rot_offset_rad = np.deg2rad(
            np.asarray(wrist_camera_rot_offset_deg, dtype=np.float64)
        )
        self.wrist_camera_fovy = None if wrist_camera_fovy is None else float(wrist_camera_fovy)
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
        self.geometry_hole_center_xy_jitter = np.asarray(
            geometry_hole_center_xy_jitter,
            dtype=np.float64,
        )
        self.geometry_fixture_height_jitter = float(geometry_fixture_height_jitter)
        self.geometry_table_height_jitter = float(geometry_table_height_jitter)
        self.geometry_hole_half_size_range = tuple(
            float(v) for v in geometry_hole_half_size_range
        )
        self.geometry_peg_radius_range = tuple(float(v) for v in geometry_peg_radius_range)
        self.geometry_profile = geometry_profile
        self.geometry_fixture_mode = geometry_fixture_mode
        self.geometry_true_fixture_variant = geometry_true_fixture_variant
        self.enable_peg_tip_visual_helpers = bool(enable_peg_tip_visual_helpers)
        self.geometry_square_peg_half_size_range = tuple(
            float(v) for v in geometry_square_peg_half_size_range
        )
        self.geometry_mixed_square_probability = float(geometry_mixed_square_probability)
        self.contact_friction_multiplier_range = tuple(
            float(v) for v in contact_friction_multiplier_range
        )
        self.contact_solref_time_multiplier_range = tuple(
            float(v) for v in contact_solref_time_multiplier_range
        )
        self.contact_solref_damping_multiplier_range = tuple(
            float(v) for v in contact_solref_damping_multiplier_range
        )
        self.contact_solimp_width_multiplier_range = tuple(
            float(v) for v in contact_solimp_width_multiplier_range
        )
        self.dynamics_joint_damping_multiplier_range = tuple(
            float(v) for v in dynamics_joint_damping_multiplier_range
        )
        self.dynamics_actuator_kp_multiplier_range = tuple(
            float(v) for v in dynamics_actuator_kp_multiplier_range
        )
        self.nominal_joint_damping_multiplier = float(nominal_joint_damping_multiplier)
        self.nominal_actuator_kp_multiplier = float(nominal_actuator_kp_multiplier)
        self.initialization_mode = initialization_mode
        self.initial_tip_z_above_range = tuple(float(v) for v in initial_tip_z_above_range)
        self.initial_tip_xy_offset_range = tuple(float(v) for v in initial_tip_xy_offset_range)
        self.initial_tip_xy_angle_range_deg = tuple(float(v) for v in initial_tip_xy_angle_range_deg)
        self.initial_shape_yaw_error_range_deg = (
            tuple(float(v) for v in initial_shape_yaw_error_range_deg)
            if initial_shape_yaw_error_range_deg is not None
            else None
        )
        self.initial_shape_yaw_ik_orientation_weight = float(
            initial_shape_yaw_ik_orientation_weight
        )
        self.initial_shape_yaw_ik_max_iterations = int(
            initial_shape_yaw_ik_max_iterations
        )
        self.initial_shape_yaw_max_wrist_rest_delta_rad = (
            None
            if initial_shape_yaw_max_wrist_rest_delta_deg is None
            else float(np.deg2rad(initial_shape_yaw_max_wrist_rest_delta_deg))
        )
        self.initial_ik_max_attempts = int(initial_ik_max_attempts)
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
        self.current_hole_center_offset = np.zeros(2, dtype=np.float64)
        self.current_fixture_height_offset = 0.0
        self.current_table_height_offset = 0.0
        self.current_initial_tip_target = np.zeros(3, dtype=np.float64)
        self.current_initial_ik_error = 0.0
        self.current_initial_ik_attempts = 0
        self.current_initial_shape_yaw_error_deg = np.nan
        self.current_hole_half_size = 0.027
        self.current_peg_radius = 0.012
        self.current_geometry_spec = GeometrySpec(
            name="single",
            peg_shape="round",
            hole_shape="square",
            hole_half_size=self.current_hole_half_size,
            peg_radius=self.current_peg_radius,
        )
        self.current_contact_friction_multiplier = 1.0
        self.current_contact_solref_time_multiplier = 1.0
        self.current_contact_solref_damping_multiplier = 1.0
        self.current_contact_solimp_width_multiplier = 1.0
        self.current_joint_damping_multiplier = self.nominal_joint_damping_multiplier
        self.current_actuator_kp_multiplier = self.nominal_actuator_kp_multiplier
        self.gray_frame_buffer: list[np.ndarray] = []
        self.near_hole_crop_buffer: list[np.ndarray] = []
        self.control_state_buffer: list[np.ndarray] = []

        asset_path = resolve_model_path(model_path)
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
        self.ik_joint_count = self._resolve_ik_joint_count(
            self.requested_ik_joint_count
        )
        if self.ik_control_mode in ("pose", "pose_tip_priority"):
            self.ik_joint_count = len(self.ARM_JOINT_NAMES)
        self.arm_actuator_ids = np.asarray(
            [self._actuator_id(f"{name}_ctrl") for name in self.ARM_JOINT_NAMES],
            dtype=np.int32,
        )
        self.joint_ranges = self.model.jnt_range[self.arm_joint_ids].copy()
        self.rest_qpos = np.asarray([0.08, -1.2, 1.8, -0.6, 0.0, 0.0], dtype=np.float64)
        self.last_tip_pos_before_action = np.zeros(3, dtype=np.float64)
        self.last_target_tip_pos = np.zeros(3, dtype=np.float64)
        self.last_target_tip_delta = np.zeros(3, dtype=np.float64)
        self.last_ik_tip_pos = np.zeros(3, dtype=np.float64)
        self.last_ik_target_error = 0.0
        self.last_ik_orientation_error = 0.0
        self.last_ik_iterations = 0
        self.last_joint_qpos_before_action = self.rest_qpos.copy()
        self.last_joint_target_qpos = self.rest_qpos.copy()
        self.last_joint_qpos_after_action = self.rest_qpos.copy()
        self.last_joint_target_error = 0.0
        self.last_ik_wrist_target_clipped = False
        self.ik_wrist_anchor_qpos: np.ndarray | None = None
        self.last_actual_tip_delta = np.zeros(3, dtype=np.float64)
        self.last_tip_delta_error = np.zeros(3, dtype=np.float64)
        self.last_action_tracking_error = 0.0
        self.last_peg_axis_world = np.asarray([0.0, 0.0, -1.0], dtype=np.float64)
        self.last_peg_tilt_angle_deg = 0.0

        self.peg_tip_site_id = self._site_id("peg_tip")
        self.eef_site_id = self._site_id("eef_site")
        self.hole_site_id = self._site_id("hole_site")
        self.wrist_camera_id = self._camera_id("wrist_cam")
        self.base_body_id = self._body_id("base")
        self.tool0_body_id = self._body_id("tool0")
        self.hole_body_id = self._body_id("hole_body")
        self.hole_mocap_id = int(self.model.body_mocapid[self.hole_body_id])
        if self.hole_mocap_id < 0:
            raise RuntimeError("hole_body must be a mocap body.")
        self.table_geom_id = self._geom_id("table_top")
        self.peg_geom_id = self._geom_id("peg_geom")
        self.hole_cavity_visual_geom_id = self._maybe_named_id(
            mujoco.mjtObj.mjOBJ_GEOM,
            "hole_cavity_visual",
        )
        self.hole_key_tab_cavity_visual_geom_id = self._maybe_named_id(
            mujoco.mjtObj.mjOBJ_GEOM,
            "hole_key_tab_cavity_visual",
        )
        self.hole_wall_geom_ids = {}
        for name in ALL_HOLE_WALL_NAMES:
            geom_id = self._maybe_named_id(mujoco.mjtObj.mjOBJ_GEOM, name)
            if geom_id is not None:
                self.hole_wall_geom_ids[name] = geom_id
        self.hole_polygon_visual_geom_ids = {}
        for name in POLYGON_HOLE_VISUAL_WALL_NAMES:
            geom_id = self._maybe_named_id(mujoco.mjtObj.mjOBJ_GEOM, name)
            if geom_id is not None:
                self.hole_polygon_visual_geom_ids[name] = geom_id
        self.true_fixture_wall_geom_ids = {}
        for name in TRUE_FIXTURE_WALL_NAMES:
            geom_id = self._maybe_named_id(mujoco.mjtObj.mjOBJ_GEOM, name)
            if geom_id is not None:
                self.true_fixture_wall_geom_ids[name] = geom_id
        self.true_fixture_visual_geom_id = self._maybe_named_id(
            mujoco.mjtObj.mjOBJ_GEOM,
            "true_fixture_visual",
        )
        missing_primary_walls = [
            name for name in PRIMARY_HOLE_WALL_NAMES if name not in self.hole_wall_geom_ids
        ]
        if missing_primary_walls:
            raise RuntimeError(
                "MuJoCo model is missing required hole wall geoms: "
                + ", ".join(missing_primary_walls)
            )
        self.peg_mesh_ids = {}
        for shape, mesh_name in POLYGONAL_PEG_MESH_NAMES.items():
            mesh_id = self._maybe_named_id(mujoco.mjtObj.mjOBJ_MESH, mesh_name)
            if mesh_id is not None:
                self.peg_mesh_ids[shape] = mesh_id
        self.peg_tip_cap_visual_geom_id = self._maybe_named_id(
            mujoco.mjtObj.mjOBJ_GEOM,
            "peg_tip_cap_visual",
        )
        self.peg_tip_outline_visual_geom_id = self._maybe_named_id(
            mujoco.mjtObj.mjOBJ_GEOM,
            "peg_tip_outline_visual",
        )
        self.peg_side_edge_visual_geom_id = self._maybe_named_id(
            mujoco.mjtObj.mjOBJ_GEOM,
            "peg_side_edge_visual",
        )
        self.peg_tip_cap_visual_mesh_ids = {}
        for shape, mesh_name in POLYGONAL_PEG_TIP_CAP_VISUAL_MESH_NAMES.items():
            mesh_id = self._maybe_named_id(mujoco.mjtObj.mjOBJ_MESH, mesh_name)
            if mesh_id is not None:
                self.peg_tip_cap_visual_mesh_ids[shape] = mesh_id
        self.peg_tip_outline_visual_mesh_ids = {}
        for shape, mesh_name in POLYGONAL_PEG_TIP_OUTLINE_VISUAL_MESH_NAMES.items():
            mesh_id = self._maybe_named_id(mujoco.mjtObj.mjOBJ_MESH, mesh_name)
            if mesh_id is not None:
                self.peg_tip_outline_visual_mesh_ids[shape] = mesh_id
        self.peg_side_edge_visual_mesh_ids = {}
        for shape, mesh_name in POLYGONAL_PEG_SIDE_EDGE_VISUAL_MESH_NAMES.items():
            mesh_id = self._maybe_named_id(mujoco.mjtObj.mjOBJ_MESH, mesh_name)
            if mesh_id is not None:
                self.peg_side_edge_visual_mesh_ids[shape] = mesh_id
        self.true_fixture_wall_mesh_ids = {}
        for shape, mesh_name in TRUE_FIXTURE_WALL_MESH_NAMES.items():
            mesh_id = self._maybe_named_id(mujoco.mjtObj.mjOBJ_MESH, mesh_name)
            if mesh_id is not None:
                self.true_fixture_wall_mesh_ids[shape] = mesh_id
        self.true_fixture_visual_mesh_ids = {}
        for shape, mesh_name in TRUE_FIXTURE_VISUAL_MESH_NAMES.items():
            mesh_id = self._maybe_named_id(mujoco.mjtObj.mjOBJ_MESH, mesh_name)
            if mesh_id is not None:
                self.true_fixture_visual_mesh_ids[shape] = mesh_id
        self.contact_geom_ids = np.asarray(
            [
                self.table_geom_id,
                self.peg_geom_id,
                self._geom_id("hole_plate"),
                *self.hole_wall_geom_ids.values(),
                *self.true_fixture_wall_geom_ids.values(),
            ],
            dtype=np.int32,
        )
        self.default_pose_ik_target_xmat = self._compute_rest_site_xmat(
            self.peg_tip_site_id
        )
        self.pose_ik_target_xmat = self.default_pose_ik_target_xmat.copy()

        self.base_geom_rgba = self.model.geom_rgba.copy()
        self.base_geom_pos = self.model.geom_pos.copy()
        self.base_geom_size = self.model.geom_size.copy()
        self.base_geom_type = self.model.geom_type.copy()
        self.base_geom_dataid = self.model.geom_dataid.copy()
        self.base_geom_quat = self.model.geom_quat.copy()
        self.base_geom_rbound = self.model.geom_rbound.copy()
        self.base_geom_contype = self.model.geom_contype.copy()
        self.base_geom_conaffinity = self.model.geom_conaffinity.copy()
        self.base_geom_friction = self.model.geom_friction.copy()
        self.base_geom_solref = self.model.geom_solref.copy()
        self.base_geom_solimp = self.model.geom_solimp.copy()
        self.base_site_pos = self.model.site_pos.copy()
        reference_wall_id = self.hole_wall_geom_ids["hole_north"]
        self.active_hole_wall_contype = int(self.base_geom_contype[reference_wall_id])
        self.active_hole_wall_conaffinity = int(
            self.base_geom_conaffinity[reference_wall_id]
        )
        self.active_hole_wall_rgba = self.base_geom_rgba[reference_wall_id].copy()
        self.base_hole_half_size = self._infer_base_hole_half_size()
        self.base_peg_radius = float(self.base_geom_size[self.peg_geom_id, 0])
        self.base_peg_half_length = self._infer_base_peg_half_length()
        self.current_hole_half_size = self.base_hole_half_size
        self.current_peg_radius = self.base_peg_radius
        self.current_geometry_spec = self._make_geometry_spec(
            name="single",
            peg_shape="round",
            hole_shape="square",
            hole_half_size=self.current_hole_half_size,
            peg_radius=self.current_peg_radius,
        )
        self.base_light_diffuse = self.model.light_diffuse.copy()
        self._apply_nominal_wrist_camera_pose()
        self.base_cam_pos = self.model.cam_pos.copy()
        self.base_cam_quat = self.model.cam_quat.copy()
        self.base_cam_fovy = self.model.cam_fovy.copy()
        self.base_dof_damping = self.model.dof_damping.copy()
        self.base_actuator_gainprm = self.model.actuator_gainprm.copy()
        self.base_actuator_biasprm = self.model.actuator_biasprm.copy()

        self.renderer: mujoco.Renderer | None = None
        self.step_count = 0
        self.fixture_pos = self.target_low.copy()
        self.target_pos = self.target_low.copy()
        self.previous_shaped_distance = 0.0

        self.action_space = spaces.Box(
            low=-self.action_scale,
            high=self.action_scale,
            shape=(3,),
            dtype=np.float32,
        )
        if self.observation_mode == "image":
            image_spaces: dict[str, spaces.Box] = {
                "cam_image": spaces.Box(
                    low=0,
                    high=255,
                    shape=(self.image_height, self.image_width, self.image_frame_stack),
                    dtype=np.uint8,
                )
            }
            if self.include_near_hole_crop:
                image_spaces["near_hole_crop"] = spaces.Box(
                    low=0,
                    high=255,
                    shape=(
                        self.near_hole_crop_size,
                        self.near_hole_crop_size,
                        self.image_frame_stack,
                    ),
                    dtype=np.uint8,
                )
            if self.include_control_state:
                image_spaces["control_state"] = spaces.Box(
                    low=-np.inf,
                    high=np.inf,
                    shape=(self.CONTROL_STATE_DIM * self.image_frame_stack,),
                    dtype=np.float32,
                )
            self.observation_space = spaces.Dict(image_spaces)
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

        self._sample_near_hole_crop_source_size()
        self._sample_target()
        self._maybe_randomize_domain()
        self._initialize_arm_pose()
        self._reset_ik_wrist_anchor()
        self.reset_pose_ik_target_xmat()
        self.data.qvel[:] = 0.0

        mujoco.mj_forward(self.model, self.data)
        for _ in range(80):
            mujoco.mj_step(self.model, self.data)
        self._reset_action_tracking_diagnostics()
        self._clear_observation_history()

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
        joint_qpos_before = self.data.qpos[self.arm_qpos_ids].copy()
        q_target, ik_tip_pos, ik_error, ik_iterations = self._solve_ik_with_diagnostics(
            target_tip_pos
        )
        q_target = self._nearest_wrist_target_equivalent(q_target, joint_qpos_before)
        q_target = self._clip_wrist_target_delta(q_target, joint_qpos_before)
        if self.last_ik_wrist_target_clipped:
            ik_tip_pos = self._arm_qpos_tip_pos(q_target)
            ik_error = float(np.linalg.norm(target_tip_pos - ik_tip_pos))
        self._set_arm_control(q_target)
        joint_target_qpos = self.data.ctrl[self.arm_actuator_ids].copy()

        for _ in range(self.frame_skip):
            mujoco.mj_step(self.model, self.data)
        next_tip_pos = self._site_xpos(self.data, self.peg_tip_site_id)
        joint_qpos_after = self.data.qpos[self.arm_qpos_ids].copy()
        actual_tip_delta = next_tip_pos - current_tip_pos
        target_tip_delta = target_tip_pos - current_tip_pos
        tip_delta_error = target_tip_delta - actual_tip_delta
        self.last_tip_pos_before_action = current_tip_pos.copy()
        self.last_target_tip_pos = target_tip_pos.copy()
        self.last_target_tip_delta = target_tip_delta.copy()
        self.last_ik_tip_pos = ik_tip_pos.copy()
        self.last_ik_target_error = float(ik_error)
        self.last_ik_orientation_error = self._current_pose_ik_orientation_error(self.data)
        self.last_ik_iterations = int(ik_iterations)
        self.last_joint_qpos_before_action = joint_qpos_before.copy()
        self.last_joint_target_qpos = joint_target_qpos.copy()
        self.last_joint_qpos_after_action = joint_qpos_after.copy()
        self.last_joint_target_error = float(np.linalg.norm(joint_target_qpos - joint_qpos_after))
        self.last_actual_tip_delta = actual_tip_delta.copy()
        self.last_tip_delta_error = tip_delta_error.copy()
        self.last_action_tracking_error = float(np.linalg.norm(tip_delta_error))
        self.last_peg_axis_world, self.last_peg_tilt_angle_deg = self._peg_axis_and_tilt(self.data)

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
        if self.image_width <= 0 or self.image_height <= 0:
            raise ValueError("image_width and image_height must be positive.")
        if self.near_hole_crop_size <= 0:
            raise ValueError("near_hole_crop_size must be positive.")
        if self.near_hole_crop_source_size <= 0:
            raise ValueError("near_hole_crop_source_size must be positive.")
        if self.near_hole_crop_source_size_range is not None:
            if len(self.near_hole_crop_source_size_range) != 2:
                raise ValueError("near_hole_crop_source_size_range must contain two integer values.")
            if self.near_hole_crop_source_size_range[0] <= 0:
                raise ValueError("near_hole_crop_source_size_range must stay positive.")
            if self.near_hole_crop_source_size_range[0] > self.near_hole_crop_source_size_range[1]:
                raise ValueError("near_hole_crop_source_size_range must be increasing.")
        if len(self.near_hole_crop_offset) != 2:
            raise ValueError("near_hole_crop_offset must contain two integer values.")
        if self.image_frame_stack <= 0:
            raise ValueError("image_frame_stack must be positive.")
        if self.wrist_camera_pos_offset.shape != (3,):
            raise ValueError("wrist_camera_pos_offset must contain three values.")
        if self.wrist_camera_rot_offset_rad.shape != (3,):
            raise ValueError("wrist_camera_rot_offset_deg must contain three values.")
        if self.wrist_camera_fovy is not None and self.wrist_camera_fovy <= 0.0:
            raise ValueError("wrist_camera_fovy must be positive when set.")

        ranges: tuple[tuple[str, tuple[float, float]], ...] = (
            ("image_brightness_range", self.image_brightness_range),
            ("image_contrast_range", self.image_contrast_range),
            ("image_noise_std_range", self.image_noise_std_range),
            ("control_action_scale_range", self.control_action_scale_range),
            ("control_action_noise_std_range", self.control_action_noise_std_range),
            ("control_action_filter_alpha_range", self.control_action_filter_alpha_range),
            ("geometry_hole_half_size_range", self.geometry_hole_half_size_range),
            ("geometry_peg_radius_range", self.geometry_peg_radius_range),
            ("geometry_square_peg_half_size_range", self.geometry_square_peg_half_size_range),
            ("contact_friction_multiplier_range", self.contact_friction_multiplier_range),
            ("contact_solref_time_multiplier_range", self.contact_solref_time_multiplier_range),
            ("contact_solref_damping_multiplier_range", self.contact_solref_damping_multiplier_range),
            ("contact_solimp_width_multiplier_range", self.contact_solimp_width_multiplier_range),
            ("dynamics_joint_damping_multiplier_range", self.dynamics_joint_damping_multiplier_range),
            ("dynamics_actuator_kp_multiplier_range", self.dynamics_actuator_kp_multiplier_range),
            ("initial_tip_z_above_range", self.initial_tip_z_above_range),
            ("initial_tip_xy_offset_range", self.initial_tip_xy_offset_range),
            ("initial_tip_xy_angle_range_deg", self.initial_tip_xy_angle_range_deg),
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
        if self.geometry_hole_center_xy_jitter.shape != (2,):
            raise ValueError("geometry_hole_center_xy_jitter must contain two values.")
        if np.any(self.geometry_hole_center_xy_jitter < 0.0):
            raise ValueError("geometry_hole_center_xy_jitter cannot be negative.")
        if self.geometry_fixture_height_jitter < 0.0:
            raise ValueError("geometry_fixture_height_jitter cannot be negative.")
        if self.geometry_table_height_jitter < 0.0:
            raise ValueError("geometry_table_height_jitter cannot be negative.")
        if self.geometry_hole_half_size_range[0] <= 0.0:
            raise ValueError("geometry_hole_half_size_range must stay positive.")
        if self.geometry_peg_radius_range[0] <= 0.0:
            raise ValueError("geometry_peg_radius_range must stay positive.")
        if self.geometry_square_peg_half_size_range[0] <= 0.0:
            raise ValueError("geometry_square_peg_half_size_range must stay positive.")
        if not 0.0 <= self.geometry_mixed_square_probability <= 1.0:
            raise ValueError("geometry_mixed_square_probability must be in [0, 1].")
        positive_multiplier_ranges = (
            ("contact_friction_multiplier_range", self.contact_friction_multiplier_range),
            ("contact_solref_time_multiplier_range", self.contact_solref_time_multiplier_range),
            ("contact_solref_damping_multiplier_range", self.contact_solref_damping_multiplier_range),
            ("contact_solimp_width_multiplier_range", self.contact_solimp_width_multiplier_range),
            ("dynamics_joint_damping_multiplier_range", self.dynamics_joint_damping_multiplier_range),
            ("dynamics_actuator_kp_multiplier_range", self.dynamics_actuator_kp_multiplier_range),
        )
        for name, value_range in positive_multiplier_ranges:
            if value_range[0] <= 0.0:
                raise ValueError(f"{name} must stay positive.")
        if self.nominal_joint_damping_multiplier <= 0.0:
            raise ValueError("nominal_joint_damping_multiplier must stay positive.")
        if self.nominal_actuator_kp_multiplier <= 0.0:
            raise ValueError("nominal_actuator_kp_multiplier must stay positive.")
        if self.initial_tip_z_above_range[0] < 0.0:
            raise ValueError("initial_tip_z_above_range cannot be negative.")
        if self.initial_tip_xy_offset_range[0] < 0.0:
            raise ValueError("initial_tip_xy_offset_range cannot be negative.")
        if self.initial_shape_yaw_error_range_deg is not None:
            value_range = self.initial_shape_yaw_error_range_deg
            if len(value_range) != 2 or value_range[0] > value_range[1]:
                raise ValueError(
                    "initial_shape_yaw_error_range_deg must be a two-value increasing range."
                )
            if value_range[0] < 0.0:
                raise ValueError("initial_shape_yaw_error_range_deg cannot be negative.")
        if self.initial_shape_yaw_ik_orientation_weight < 0.0:
            raise ValueError("initial_shape_yaw_ik_orientation_weight cannot be negative.")
        if self.initial_shape_yaw_ik_max_iterations < 1:
            raise ValueError("initial_shape_yaw_ik_max_iterations must be positive.")
        if (
            self.initial_shape_yaw_max_wrist_rest_delta_rad is not None
            and self.initial_shape_yaw_max_wrist_rest_delta_rad <= 0.0
        ):
            raise ValueError(
                "initial_shape_yaw_max_wrist_rest_delta_deg must be positive when set."
            )
        if self.initial_ik_max_attempts < 1:
            raise ValueError("initial_ik_max_attempts must be positive.")
        if self.ik_orientation_weight < 0.0:
            raise ValueError("ik_orientation_weight cannot be negative.")
        if self.ik_posture_weight < 0.0:
            raise ValueError("ik_posture_weight cannot be negative.")
        if self.ik_wrist_posture_weight < 0.0:
            raise ValueError("ik_wrist_posture_weight cannot be negative.")
        if self.ik_wrist_anchor_weight < 0.0:
            raise ValueError("ik_wrist_anchor_weight cannot be negative.")
        if self.ik_continuity_weight < 0.0:
            raise ValueError("ik_continuity_weight cannot be negative.")
        if self.ik_wrist_continuity_weight < 0.0:
            raise ValueError("ik_wrist_continuity_weight cannot be negative.")
        if self.ik_step_limit <= 0.0:
            raise ValueError("ik_step_limit must be positive.")
        if self.ik_max_iterations < 1:
            raise ValueError("ik_max_iterations must be positive.")

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

    def _maybe_named_id(self, obj_type: mujoco.mjtObj, name: str) -> int | None:
        obj_id = mujoco.mj_name2id(self.model, obj_type, name)
        if obj_id < 0:
            return None
        return int(obj_id)

    def _infer_base_hole_half_size(self) -> float:
        north_id = self.hole_wall_geom_ids["hole_north"]
        east_id = self.hole_wall_geom_ids["hole_east"]
        site_pos = self.base_site_pos[self.hole_site_id]
        y_half_size = (
            self.base_geom_pos[north_id, 1]
            - self.base_geom_size[north_id, 1]
            - site_pos[1]
        )
        x_half_size = (
            self.base_geom_pos[east_id, 0]
            - self.base_geom_size[east_id, 0]
            - site_pos[0]
        )
        return float(0.5 * (abs(x_half_size) + abs(y_half_size)))

    def _infer_base_peg_half_length(self) -> float:
        half_length = float(abs(self.base_geom_size[self.peg_geom_id, 1]))
        if half_length > 0.0:
            return half_length
        tip_offset = self.base_site_pos[self.peg_tip_site_id] - self.base_site_pos[self.eef_site_id]
        return float(max(np.linalg.norm(tip_offset) * 0.5, self.base_peg_radius))

    def _make_geometry_spec(
        self,
        *,
        name: str,
        peg_shape: str,
        hole_shape: str,
        hole_half_size: float,
        peg_radius: float,
        peg_half_extents: tuple[float, float, float] | None = None,
        hole_half_extents: tuple[float, float] | None = None,
        hole_polygon_sides: int | None = None,
        peg_mesh_name: str | None = None,
    ) -> GeometrySpec:
        if peg_shape in ("square", "slot", "rectangular_key") and peg_half_extents is None:
            peg_half_extents = (
                float(peg_radius),
                float(peg_radius),
                float(self.base_peg_half_length),
            )
        if hole_half_extents is None and hole_shape in ("square", "slot", "rectangular_key"):
            hole_half_extents = (float(hole_half_size), float(hole_half_size))
        return GeometrySpec(
            name=name,
            peg_shape=peg_shape,
            hole_shape=hole_shape,
            hole_half_size=float(hole_half_size),
            peg_radius=float(peg_radius),
            peg_half_extents=peg_half_extents,
            hole_half_extents=hole_half_extents,
            hole_polygon_sides=hole_polygon_sides,
            peg_mesh_name=peg_mesh_name,
        )

    def _true_fixture_mesh_profile_key(self, hole_shape: str) -> str:
        if self.geometry_true_fixture_variant != "tight_yaw":
            return hole_shape
        if hole_shape == "hex":
            return "hex_tight_yaw"
        if hole_shape == "triangle":
            return "triangle_tight_yaw"
        if hole_shape == "rectangular_key":
            return "rectangular_key_tight_yaw"
        return hole_shape

    def _true_fixture_keyhole_dimensions(
        self,
        hole_radius: float | None = None,
    ) -> tuple[float, float, float]:
        if self.geometry_true_fixture_variant == "tight_yaw":
            clearance = TIGHT_YAW_KEYHOLE_CLEARANCE
            radius = TIGHT_YAW_BASE_PEG_RADIUS + clearance
            tab_half_width = TIGHT_YAW_KEYHOLE_PEG_TAB_HALF_WIDTH + clearance
            tab_length = TIGHT_YAW_KEYHOLE_PEG_TAB_LENGTH + clearance
            return radius, tab_half_width, tab_length
        radius = 0.016 if hole_radius is None else float(hole_radius)
        tab_half_width = radius * KEYHOLE_HOLE_TAB_HALF_WIDTH_RATIO
        tab_length = radius * KEYHOLE_HOLE_TAB_LENGTH_RATIO
        return radius, tab_half_width, tab_length

    def _true_fixture_polygon_apothem(self, hole_shape: str) -> float | None:
        if hole_shape == "hex":
            if self.geometry_true_fixture_variant == "tight_yaw":
                return float(self.base_peg_radius * np.cos(np.pi / 6.0) + TIGHT_YAW_HEX_CLEARANCE)
            return float(self.current_hole_half_size)
        if hole_shape == "triangle":
            if self.geometry_true_fixture_variant == "tight_yaw":
                return float(self.base_peg_radius * np.cos(np.pi / 3.0) + TIGHT_YAW_TRIANGLE_CLEARANCE)
            return float(self.current_hole_half_size)
        return None

    def _sample_geometry_spec(self, *, randomize_sizes: bool) -> GeometrySpec:
        profile = self.geometry_profile
        if profile == "mixed_basic":
            profile = (
                "square_square"
                if self.np_random.random() < self.geometry_mixed_square_probability
                else "round_square"
            )
        elif profile == "mixed_same_shape":
            profile = str(
                self.np_random.choice(
                    [
                        "round_round",
                        "square_square",
                        "hex_hex",
                        "triangle_triangle",
                        "slot_slot",
                        "rectangular_key",
                    ]
                )
            )

        hole_half_size = (
            float(self.np_random.uniform(*self.geometry_hole_half_size_range))
            if randomize_sizes
            else self.base_hole_half_size
        )
        round_peg_radius = (
            float(self.np_random.uniform(*self.geometry_peg_radius_range))
            if randomize_sizes
            else self.base_peg_radius
        )
        square_peg_half_size = (
            float(self.np_random.uniform(*self.geometry_square_peg_half_size_range))
            if randomize_sizes
            else min(self.base_peg_radius, self.base_hole_half_size * 0.8)
        )
        slot_peg_half_short = square_peg_half_size
        slot_peg_half_long = slot_peg_half_short * 2.2
        key_peg_half_short = square_peg_half_size
        key_peg_half_long = key_peg_half_short * 1.55
        slot_hole_half_extents = (hole_half_size * 2.2, hole_half_size)
        key_hole_half_extents = (hole_half_size * 1.55, hole_half_size)
        if self.geometry_fixture_mode == "true_mesh":
            key_peg_tab_length = key_peg_half_short * KEYHOLE_PEG_TAB_LENGTH_RATIO
            key_peg_half_long = key_peg_half_short + key_peg_tab_length
            key_hole_tab_length = hole_half_size * KEYHOLE_HOLE_TAB_LENGTH_RATIO
            key_hole_half_extents = (hole_half_size + key_hole_tab_length, hole_half_size)

        if self.geometry_true_fixture_variant == "tight_yaw":
            if profile == "square_square":
                square_peg_half_size = float(self.base_peg_radius)
                hole_half_size = square_peg_half_size + TIGHT_YAW_SQUARE_CLEARANCE
            elif profile == "hex_hex":
                hole_half_size = (
                    float(self.base_peg_radius) * float(np.cos(np.pi / 6.0))
                    + TIGHT_YAW_HEX_CLEARANCE
                )
            elif profile == "triangle_triangle":
                hole_half_size = (
                    float(self.base_peg_radius) * float(np.cos(np.pi / 3.0))
                    + TIGHT_YAW_TRIANGLE_CLEARANCE
                )
            elif profile == "rectangular_key":
                key_peg_half_short = TIGHT_YAW_BASE_PEG_RADIUS
                key_peg_half_long = (
                    TIGHT_YAW_BASE_PEG_RADIUS + TIGHT_YAW_KEYHOLE_PEG_TAB_LENGTH
                )
                radius, _, tab_length = self._true_fixture_keyhole_dimensions()
                hole_half_size = radius
                key_hole_half_extents = (radius + tab_length, radius)

        if profile in ("single", "round_square"):
            return self._make_geometry_spec(
                name=profile,
                peg_shape="round",
                hole_shape="square",
                hole_half_size=hole_half_size,
                peg_radius=round_peg_radius,
            )
        if profile == "round_round":
            return self._make_geometry_spec(
                name="round_round",
                peg_shape="round",
                hole_shape="round",
                hole_half_size=hole_half_size,
                peg_radius=round_peg_radius,
                hole_polygon_sides=12,
            )
        if profile == "square_square":
            return self._make_geometry_spec(
                name="square_square",
                peg_shape="square",
                hole_shape="square",
                hole_half_size=hole_half_size,
                peg_radius=square_peg_half_size,
            )
        if profile == "hex_hex":
            return self._make_geometry_spec(
                name="hex_hex",
                peg_shape="hex",
                hole_shape="hex",
                hole_half_size=hole_half_size,
                peg_radius=self.base_peg_radius,
                hole_polygon_sides=6,
                peg_mesh_name=POLYGONAL_PEG_MESH_NAMES["hex"],
            )
        if profile == "triangle_triangle":
            if self.geometry_fixture_mode == "true_mesh":
                # For an equilateral triangle, circumdiameter = 4 * apothem.
                # Limit that to 2x peg diameter, so apothem <= peg_radius.
                max_triangle_apothem = (
                    0.5
                    * TRIANGLE_TRUE_FIXTURE_MAX_HOLE_DIAMETER_MULTIPLIER
                    * self.base_peg_radius
                )
                triangle_hole_half_size = min(hole_half_size, max_triangle_apothem)
            else:
                triangle_hole_half_size = max(
                    hole_half_size,
                    self.base_peg_radius * TRIANGLE_SCAFFOLD_HOLE_HALF_SIZE_FLOOR_MULTIPLIER,
                )
            return self._make_geometry_spec(
                name="triangle_triangle",
                peg_shape="triangle",
                hole_shape="triangle",
                hole_half_size=triangle_hole_half_size,
                peg_radius=self.base_peg_radius,
                hole_polygon_sides=3,
                peg_mesh_name=POLYGONAL_PEG_MESH_NAMES["triangle"],
            )
        if profile == "slot_slot":
            return self._make_geometry_spec(
                name="slot_slot",
                peg_shape="slot",
                hole_shape="slot",
                hole_half_size=hole_half_size,
                peg_radius=slot_peg_half_short,
                peg_half_extents=(
                    slot_peg_half_long,
                    slot_peg_half_short,
                    float(self.base_peg_half_length),
                ),
                hole_half_extents=slot_hole_half_extents,
            )
        if profile == "rectangular_key":
            return self._make_geometry_spec(
                name="rectangular_key",
                peg_shape="rectangular_key",
                hole_shape="rectangular_key",
                hole_half_size=hole_half_size,
                peg_radius=key_peg_half_short,
                peg_half_extents=(
                    key_peg_half_long,
                    key_peg_half_short,
                    float(self.base_peg_half_length),
                ),
                hole_half_extents=key_hole_half_extents,
                peg_mesh_name=(
                    POLYGONAL_PEG_MESH_NAMES["rectangular_key"]
                    if self.geometry_fixture_mode == "true_mesh"
                    else None
                ),
        )
        raise ValueError(f"unsupported geometry profile: {profile}")

    def _deactivate_polygon_peg_tip_visuals(self) -> None:
        for geom_id in (
            self.peg_tip_cap_visual_geom_id,
            self.peg_tip_outline_visual_geom_id,
            self.peg_side_edge_visual_geom_id,
        ):
            if geom_id is None:
                continue
            self.model.geom_type[geom_id] = self.base_geom_type[geom_id]
            self.model.geom_dataid[geom_id] = self.base_geom_dataid[geom_id]
            self.model.geom_pos[geom_id] = self.base_geom_pos[geom_id]
            self.model.geom_quat[geom_id] = self.base_geom_quat[geom_id]
            self.model.geom_size[geom_id] = self.base_geom_size[geom_id]
            self.model.geom_rbound[geom_id] = max(float(self.base_geom_rbound[geom_id]), 0.002)
            self.model.geom_contype[geom_id] = 0
            self.model.geom_conaffinity[geom_id] = 0
            rgba = self.base_geom_rgba[geom_id].copy()
            rgba[3] = 0.0
            self.model.geom_rgba[geom_id] = rgba

    def _set_polygon_peg_tip_visual_geometry(self, peg_shape: str) -> bool:
        cap_geom_id = self.peg_tip_cap_visual_geom_id
        outline_geom_id = self.peg_tip_outline_visual_geom_id
        side_edge_geom_id = self.peg_side_edge_visual_geom_id
        cap_mesh_id = self.peg_tip_cap_visual_mesh_ids.get(peg_shape)
        outline_mesh_id = self.peg_tip_outline_visual_mesh_ids.get(peg_shape)
        side_edge_mesh_id = self.peg_side_edge_visual_mesh_ids.get(peg_shape)
        if (
            cap_geom_id is None
            or outline_geom_id is None
            or cap_mesh_id is None
            or outline_mesh_id is None
        ):
            return False

        visual_specs = (
            (cap_geom_id, cap_mesh_id, POLYGONAL_PEG_TIP_CAP_VISUAL_RGBA),
            (outline_geom_id, outline_mesh_id, POLYGONAL_PEG_TIP_OUTLINE_VISUAL_RGBA),
        )
        if side_edge_geom_id is not None and side_edge_mesh_id is not None:
            visual_specs = (
                *visual_specs,
                (side_edge_geom_id, side_edge_mesh_id, POLYGONAL_PEG_SIDE_EDGE_VISUAL_RGBA),
            )
        for geom_id, mesh_id, rgba in visual_specs:
            self.model.geom_type[geom_id] = int(mujoco.mjtGeom.mjGEOM_MESH)
            self.model.geom_dataid[geom_id] = mesh_id
            self.model.geom_pos[geom_id] = self.base_geom_pos[geom_id]
            self.model.geom_quat[geom_id] = self.base_geom_quat[geom_id]
            self.model.geom_size[geom_id] = self.base_geom_size[geom_id]
            self.model.geom_rbound[geom_id] = max(float(self.base_geom_rbound[geom_id]), 0.02)
            self.model.geom_contype[geom_id] = 0
            self.model.geom_conaffinity[geom_id] = 0
            self.model.geom_rgba[geom_id] = rgba
        return True

    def _apply_peg_geometry(self, spec: GeometrySpec) -> None:
        self._deactivate_polygon_peg_tip_visuals()
        self.model.geom_pos[self.peg_geom_id] = self.base_geom_pos[self.peg_geom_id]
        self.model.geom_quat[self.peg_geom_id] = self.base_geom_quat[self.peg_geom_id]

        if spec.peg_shape == "round":
            self.model.geom_type[self.peg_geom_id] = self.base_geom_type[self.peg_geom_id]
            self.model.geom_dataid[self.peg_geom_id] = self.base_geom_dataid[self.peg_geom_id]
            self.model.geom_size[self.peg_geom_id] = self.base_geom_size[self.peg_geom_id]
            self.model.geom_size[self.peg_geom_id, 0] = spec.peg_radius
            self.model.geom_rbound[self.peg_geom_id] = max(
                self.base_geom_rbound[self.peg_geom_id],
                float(np.hypot(spec.peg_radius, self.base_peg_half_length)),
            )
            return

        if spec.peg_shape == "square" or (
            spec.peg_shape == "rectangular_key" and self.geometry_fixture_mode != "true_mesh"
        ) or (
            spec.peg_shape == "slot" and self.geometry_fixture_mode != "true_mesh"
        ):
            if spec.peg_half_extents is None:
                raise ValueError(f"{spec.peg_shape} peg geometry requires peg_half_extents.")
            self.model.geom_type[self.peg_geom_id] = int(mujoco.mjtGeom.mjGEOM_BOX)
            self.model.geom_dataid[self.peg_geom_id] = -1
            self.model.geom_size[self.peg_geom_id] = np.asarray(
                spec.peg_half_extents,
                dtype=np.float64,
            )
            hx, hy, hz = (float(v) for v in spec.peg_half_extents)
            self.model.geom_rbound[self.peg_geom_id] = max(
                self.base_geom_rbound[self.peg_geom_id],
                float(np.sqrt(hx * hx + hy * hy + hz * hz)),
            )
            return

        if spec.peg_shape in POLYGONAL_PEG_MESH_NAMES:
            mesh_id = self.peg_mesh_ids.get(spec.peg_shape)
            if mesh_id is None:
                raise RuntimeError(
                    f"MuJoCo model is missing mesh asset for {spec.peg_shape} peg: "
                    f"{POLYGONAL_PEG_MESH_NAMES[spec.peg_shape]}"
                )
            self.model.geom_type[self.peg_geom_id] = int(mujoco.mjtGeom.mjGEOM_MESH)
            self.model.geom_dataid[self.peg_geom_id] = mesh_id
            self.model.geom_size[self.peg_geom_id] = self.base_geom_size[self.peg_geom_id]
            self.model.geom_rbound[self.peg_geom_id] = max(
                self.base_geom_rbound[self.peg_geom_id],
                float(np.hypot(0.026, self.base_peg_half_length)),
            )
            if (
                self.enable_peg_tip_visual_helpers
                and spec.peg_shape in POLYGONAL_PEG_TIP_CAP_VISUAL_MESH_NAMES
            ):
                self._set_polygon_peg_tip_visual_geometry(spec.peg_shape)
            return

        raise ValueError(f"unsupported peg shape: {spec.peg_shape}")

    def _apply_geometry_spec(
        self,
        spec: GeometrySpec,
        *,
        center_xy: np.ndarray,
        fixture_height_offset: float,
        table_height_offset: float,
    ) -> None:
        self.current_geometry_spec = spec
        self.current_hole_half_size = spec.hole_half_size
        self.current_peg_radius = spec.peg_radius
        self.current_hole_center_offset = np.asarray(center_xy, dtype=np.float64)
        self.current_fixture_height_offset = float(fixture_height_offset)
        self.current_table_height_offset = float(table_height_offset)

        fixture_pos = self.fixture_pos.copy()
        fixture_pos[2] += self.current_fixture_height_offset
        self.data.mocap_pos[self.hole_mocap_id] = fixture_pos
        self.data.mocap_quat[self.hole_mocap_id] = np.asarray([1.0, 0.0, 0.0, 0.0])

        table_pos = self.base_geom_pos[self.table_geom_id].copy()
        table_pos[2] += self.current_table_height_offset
        self.model.geom_pos[self.table_geom_id] = table_pos

        self._apply_peg_geometry(spec)
        self._set_hole_opening_geometry(spec, self.current_hole_center_offset)

        target_offset = np.asarray(
            [
                self.current_hole_center_offset[0],
                self.current_hole_center_offset[1],
                0.0,
            ],
            dtype=np.float64,
        )
        self.target_pos = fixture_pos + target_offset

    def _reset_action_tracking_diagnostics(self) -> None:
        tip_pos = self._site_xpos(self.data, self.peg_tip_site_id)
        qpos = self.data.qpos[self.arm_qpos_ids].copy()
        self.last_tip_pos_before_action = tip_pos.copy()
        self.last_target_tip_pos = tip_pos.copy()
        self.last_target_tip_delta = np.zeros(3, dtype=np.float64)
        self.last_ik_tip_pos = tip_pos.copy()
        self.last_ik_target_error = 0.0
        self.last_ik_orientation_error = self._current_pose_ik_orientation_error(self.data)
        self.last_ik_iterations = 0
        self.last_joint_qpos_before_action = qpos.copy()
        self.last_joint_target_qpos = qpos.copy()
        self.last_joint_qpos_after_action = qpos.copy()
        self.last_joint_target_error = 0.0
        self.last_ik_wrist_target_clipped = False
        self.last_actual_tip_delta = np.zeros(3, dtype=np.float64)
        self.last_tip_delta_error = np.zeros(3, dtype=np.float64)
        self.last_action_tracking_error = 0.0
        self.last_peg_axis_world, self.last_peg_tilt_angle_deg = self._peg_axis_and_tilt(self.data)

    def _resolve_ik_joint_count(self, requested_count: int | None) -> int:
        if requested_count is None:
            numeric_id = mujoco.mj_name2id(
                self.model,
                mujoco.mjtObj.mjOBJ_NUMERIC,
                "ik_joint_count",
            )
            if numeric_id >= 0:
                adr = int(self.model.numeric_adr[numeric_id])
                requested_count = int(round(float(self.model.numeric_data[adr])))
            else:
                requested_count = self.IK_JOINT_COUNT

        count = int(requested_count)
        if count < 1 or count > len(self.ARM_JOINT_NAMES):
            raise ValueError(
                f"ik_joint_count must be between 1 and {len(self.ARM_JOINT_NAMES)}, got {count}."
            )
        return count

    def set_ik_control_mode(self, ik_control_mode: IkControlMode) -> None:
        if ik_control_mode not in ("position", "pose", "pose_tip_priority"):
            raise ValueError(
                "ik_control_mode must be 'position', 'pose', or 'pose_tip_priority'."
            )
        self.ik_control_mode = ik_control_mode
        if ik_control_mode in ("pose", "pose_tip_priority"):
            self.ik_joint_count = len(self.ARM_JOINT_NAMES)
        else:
            self.ik_joint_count = self._resolve_ik_joint_count(
                self.requested_ik_joint_count
            )

    def _set_arm_qpos(self, data: mujoco.MjData, qpos: np.ndarray) -> None:
        data.qpos[self.arm_qpos_ids] = qpos

    def _set_arm_control(self, qpos: np.ndarray) -> None:
        ctrlrange = self.model.actuator_ctrlrange[self.arm_actuator_ids]
        qpos = np.clip(qpos, ctrlrange[:, 0], ctrlrange[:, 1])
        self.data.ctrl[self.arm_actuator_ids] = qpos

    def _arm_qpos_tip_pos(self, qpos: np.ndarray) -> np.ndarray:
        data = self.ik_data
        data.qpos[:] = self.data.qpos
        data.qvel[:] = 0.0
        data.mocap_pos[:] = self.data.mocap_pos
        data.mocap_quat[:] = self.data.mocap_quat
        data.qpos[self.arm_qpos_ids] = np.asarray(qpos, dtype=np.float64)
        mujoco.mj_forward(self.model, data)
        return data.site_xpos[self.peg_tip_site_id].copy()

    def _ik_continuity_weights(self) -> np.ndarray:
        weights = np.full(
            len(self.ARM_JOINT_NAMES),
            self.ik_continuity_weight,
            dtype=np.float64,
        )
        if self.ik_wrist_continuity_weight > 0.0:
            weights[3:] += self.ik_wrist_continuity_weight
        return weights

    def _ik_wrist_posture_weights(self) -> np.ndarray:
        weights = np.zeros(len(self.ARM_JOINT_NAMES), dtype=np.float64)
        if self.ik_wrist_posture_weight > 0.0:
            weights[3:] = self.ik_wrist_posture_weight
        return weights

    def _reset_ik_wrist_anchor(self) -> None:
        if self.ik_wrist_anchor_weight <= 0.0:
            self.ik_wrist_anchor_qpos = None
            return
        self.ik_wrist_anchor_qpos = self.data.qpos[self.arm_qpos_ids][3:].copy()

    def set_ik_wrist_anchor_to_current(self) -> None:
        self.ik_wrist_anchor_qpos = self.data.qpos[self.arm_qpos_ids][3:].copy()

    def clear_ik_wrist_anchor(self) -> None:
        self.ik_wrist_anchor_qpos = None

    def _ik_wrist_anchor_full_qpos(self) -> np.ndarray | None:
        if self.ik_wrist_anchor_weight <= 0.0 or self.ik_wrist_anchor_qpos is None:
            return None
        anchor = self.rest_qpos.copy()
        anchor[3:] = self.ik_wrist_anchor_qpos
        return anchor

    def _clip_wrist_target_delta(
        self,
        q_target: np.ndarray,
        q_reference: np.ndarray,
    ) -> np.ndarray:
        if self.ik_max_wrist_target_delta_rad is None:
            self.last_ik_wrist_target_clipped = False
            return q_target

        clipped = np.asarray(q_target, dtype=np.float64).copy()
        reference = np.asarray(q_reference, dtype=np.float64)
        before = clipped[3:].copy()
        delta = np.clip(
            clipped[3:] - reference[3:],
            -self.ik_max_wrist_target_delta_rad,
            self.ik_max_wrist_target_delta_rad,
        )
        clipped[3:] = reference[3:] + delta
        self.last_ik_wrist_target_clipped = bool(
            np.max(np.abs(clipped[3:] - before)) > 1e-12
        )
        return clipped

    def _nearest_wrist_target_equivalent(
        self,
        q_target: np.ndarray,
        q_reference: np.ndarray,
    ) -> np.ndarray:
        adjusted = np.asarray(q_target, dtype=np.float64).copy()
        if not self.ik_nearest_wrist_target_equivalent:
            return adjusted

        reference = np.asarray(q_reference, dtype=np.float64)
        ctrlrange = self.model.actuator_ctrlrange[self.arm_actuator_ids]
        lower = np.maximum(self.joint_ranges[:, 0], ctrlrange[:, 0])
        upper = np.minimum(self.joint_ranges[:, 1], ctrlrange[:, 1])
        period = 2.0 * np.pi
        for index in range(3, min(len(adjusted), 6)):
            value = float(adjusted[index])
            ref = float(reference[index])
            candidates = [
                value + period * offset
                for offset in range(-2, 3)
                if lower[index] <= value + period * offset <= upper[index]
            ]
            if candidates:
                adjusted[index] = min(candidates, key=lambda candidate: abs(candidate - ref))
        return adjusted

    def _initialize_arm_pose(self) -> None:
        if self.initialization_mode == "fixed":
            self._set_arm_qpos(self.data, self.rest_qpos)
            self._set_arm_control(self.rest_qpos)
            mujoco.mj_forward(self.model, self.data)
            tip_pos = self._site_xpos(self.data, self.peg_tip_site_id)
            self.current_initial_tip_target = tip_pos
            self.current_initial_ik_error = 0.0
            self.current_initial_ik_attempts = 1
            self.current_initial_shape_yaw_error_deg = float(
                self._shape_yaw_metrics(self.data).get("shape_yaw_error_deg", np.nan)
            )
            return

        q_target, tip_target, ik_error, attempts = self._sample_high_start_qpos()
        self._set_arm_qpos(self.data, q_target)
        self._set_arm_control(q_target)
        mujoco.mj_forward(self.model, self.data)
        self.current_initial_tip_target = tip_target
        self.current_initial_ik_error = ik_error
        self.current_initial_ik_attempts = attempts
        self.current_initial_shape_yaw_error_deg = float(
            self._shape_yaw_metrics(self.data).get("shape_yaw_error_deg", np.nan)
        )

    def _sample_high_start_qpos(self) -> tuple[np.ndarray, np.ndarray, float, int]:
        best_qpos = self.rest_qpos.copy()
        best_target = self._target_relative_tip_position(
            xy_offset=self.initial_tip_xy_offset_range[0],
            angle_rad=np.deg2rad(self.initial_tip_xy_angle_range_deg[0]),
            z_above=self.initial_tip_z_above_range[0],
        )
        best_error = float("inf")
        best_yaw_miss = float("inf")
        best_wrist_rest_delta = float("inf")
        best_wrist_rest_ok = self.initial_shape_yaw_max_wrist_rest_delta_rad is None
        attempts = 0

        for attempts in range(1, self.initial_ik_max_attempts + 1):
            candidate_target = self._sample_high_start_tip_target()
            if candidate_target is None:
                continue

            self._set_arm_qpos(self.data, self.rest_qpos)
            self._set_arm_control(self.rest_qpos)
            mujoco.mj_forward(self.model, self.data)
            if self.initial_shape_yaw_error_range_deg is None:
                qpos = self._solve_position_ik(candidate_target)
            else:
                target_xmat = self._sample_initial_shape_yaw_target_xmat()
                previous_xmat = self.get_pose_ik_target_xmat()
                previous_orientation_weight = self.ik_orientation_weight
                previous_max_iterations = self.ik_max_iterations
                self.set_pose_ik_target_xmat(target_xmat)
                self.ik_orientation_weight = self.initial_shape_yaw_ik_orientation_weight
                self.ik_max_iterations = self.initial_shape_yaw_ik_max_iterations
                try:
                    qpos, _, _, _ = self._solve_tip_priority_pose_ik_with_diagnostics(
                        candidate_target
                    )
                finally:
                    self.ik_orientation_weight = previous_orientation_weight
                    self.ik_max_iterations = previous_max_iterations
                    self.set_pose_ik_target_xmat(previous_xmat)
            qpos = self._nearest_wrist_target_equivalent(qpos, self.rest_qpos)
            wrist_rest_delta = (
                float(np.max(np.abs(qpos[3:] - self.rest_qpos[3:])))
                if qpos[3:].size
                else 0.0
            )
            wrist_rest_ok = bool(
                self.initial_shape_yaw_max_wrist_rest_delta_rad is None
                or wrist_rest_delta <= self.initial_shape_yaw_max_wrist_rest_delta_rad
            )
            self._set_arm_qpos(self.data, qpos)
            mujoco.mj_forward(self.model, self.data)

            achieved_tip = self._site_xpos(self.data, self.peg_tip_site_id)
            error = float(np.linalg.norm(achieved_tip - candidate_target))
            yaw_error = float(self._shape_yaw_metrics(self.data).get("shape_yaw_error_deg", np.nan))
            yaw_ok, yaw_miss = self._initial_shape_yaw_error_ok(yaw_error)
            candidate_better = False
            if yaw_ok and not np.isfinite(best_yaw_miss):
                candidate_better = True
            elif yaw_ok and best_yaw_miss <= 0.0:
                if self.initial_shape_yaw_max_wrist_rest_delta_rad is None:
                    candidate_better = error < best_error
                elif wrist_rest_ok and not best_wrist_rest_ok:
                    candidate_better = True
                elif wrist_rest_ok == best_wrist_rest_ok:
                    wrist_margin = float(np.deg2rad(5.0))
                    if wrist_rest_delta + wrist_margin < best_wrist_rest_delta:
                        candidate_better = True
                    elif (
                        np.isclose(
                            wrist_rest_delta,
                            best_wrist_rest_delta,
                            atol=wrist_margin,
                        )
                        and error < best_error
                    ):
                        candidate_better = True
            elif yaw_miss < best_yaw_miss:
                candidate_better = True
            elif np.isclose(yaw_miss, best_yaw_miss) and error < best_error:
                candidate_better = True

            if candidate_better:
                best_qpos = qpos.copy()
                best_target = candidate_target.copy()
                best_error = error
                best_yaw_miss = yaw_miss
                best_wrist_rest_delta = wrist_rest_delta
                best_wrist_rest_ok = wrist_rest_ok
            if error < 0.005 and yaw_ok and wrist_rest_ok:
                return best_qpos, best_target, best_error, attempts

        return best_qpos, best_target, best_error, max(attempts, 1)

    def _initial_shape_yaw_error_ok(self, yaw_error_deg: float) -> tuple[bool, float]:
        value_range = self.initial_shape_yaw_error_range_deg
        if value_range is None:
            return True, 0.0
        if not np.isfinite(yaw_error_deg):
            return False, float("inf")
        low, high = value_range
        if low <= yaw_error_deg <= high:
            return True, 0.0
        return False, float(min(abs(yaw_error_deg - low), abs(yaw_error_deg - high)))

    def _sample_initial_shape_yaw_target_xmat(self) -> np.ndarray:
        value_range = self.initial_shape_yaw_error_range_deg
        if value_range is None:
            return self.default_pose_ik_target_xmat.copy()
        period_deg = self._shape_yaw_period_deg()
        if not np.isfinite(period_deg) or period_deg <= 0.0:
            return self.default_pose_ik_target_xmat.copy()

        max_error_deg = 0.5 * float(period_deg)
        low = min(float(value_range[0]), max_error_deg)
        high = min(float(value_range[1]), max_error_deg)
        if high < low:
            high = low
        abs_yaw_deg = float(self.np_random.uniform(low, high))
        sign = -1.0 if self.np_random.random() < 0.5 else 1.0
        yaw_deg = sign * abs_yaw_deg

        hole_xmat = self._body_xmat(self.data, self.hole_body_id)
        hole_x_axis = hole_xmat @ np.asarray([1.0, 0.0, 0.0], dtype=np.float64)
        hole_x_xy = self._project_unit_xy(hole_x_axis)
        if hole_x_xy is None:
            hole_x_xy = np.asarray([1.0, 0.0, 0.0], dtype=np.float64)
        yaw_rad = float(np.deg2rad(yaw_deg))
        c, s = float(np.cos(yaw_rad)), float(np.sin(yaw_rad))
        target_x_axis = np.asarray(
            [
                c * hole_x_xy[0] - s * hole_x_xy[1],
                s * hole_x_xy[0] + c * hole_x_xy[1],
                0.0,
            ],
            dtype=np.float64,
        )
        target_z_axis = self.default_pose_ik_target_xmat[:, 2].copy()
        target_z_axis = target_z_axis / max(float(np.linalg.norm(target_z_axis)), 1e-9)
        target_x_axis = target_x_axis - target_z_axis * float(
            np.dot(target_x_axis, target_z_axis)
        )
        target_x_axis = target_x_axis / max(float(np.linalg.norm(target_x_axis)), 1e-9)
        target_y_axis = np.cross(target_z_axis, target_x_axis)
        target_y_axis = target_y_axis / max(float(np.linalg.norm(target_y_axis)), 1e-9)
        return np.column_stack((target_x_axis, target_y_axis, target_z_axis))

    def _sample_high_start_tip_target(self) -> np.ndarray | None:
        xy_offset = float(self.np_random.uniform(*self.initial_tip_xy_offset_range))
        angle_rad = float(
            np.deg2rad(self.np_random.uniform(*self.initial_tip_xy_angle_range_deg))
        )
        z_above = float(self.np_random.uniform(*self.initial_tip_z_above_range))
        candidate = self._target_relative_tip_position(
            xy_offset=xy_offset,
            angle_rad=angle_rad,
            z_above=z_above,
        )
        if np.any(candidate < self.workspace_low) or np.any(candidate > self.workspace_high):
            return None
        return candidate

    def _target_relative_tip_position(
        self,
        *,
        xy_offset: float,
        angle_rad: float,
        z_above: float,
    ) -> np.ndarray:
        return np.asarray(
            [
                self.target_pos[0] + xy_offset * np.cos(angle_rad),
                self.target_pos[1] + xy_offset * np.sin(angle_rad),
                self.target_pos[2] + z_above,
            ],
            dtype=np.float64,
        )

    def _sample_near_hole_crop_source_size(self) -> None:
        if self.near_hole_crop_source_size_range is None:
            self.current_near_hole_crop_source_size = self.near_hole_crop_source_size
            return
        low, high = self.near_hole_crop_source_size_range
        self.current_near_hole_crop_source_size = int(
            self.np_random.integers(low, high + 1)
        )

    def _sample_target(self) -> None:
        self.fixture_pos = self.np_random.uniform(self.target_low, self.target_high)
        self.target_pos = self.fixture_pos.copy()
        self.data.mocap_pos[self.hole_mocap_id] = self.fixture_pos
        self.data.mocap_quat[self.hole_mocap_id] = np.asarray([1.0, 0.0, 0.0, 0.0])

    def _uses_visual_camera_randomization(self) -> bool:
        return self.domain_randomization_level in (
            "visual_camera",
            "visual_camera_control",
            "full_light_geometry",
            "full_contact_light",
            "full",
        )

    def _uses_control_randomization(self) -> bool:
        return self.domain_randomization_level in (
            "visual_camera_control",
            "full_light_geometry",
            "full_contact_light",
            "full",
        )

    def _uses_light_geometry_randomization(self) -> bool:
        return self.domain_randomization_level in (
            "full_light_geometry",
            "full_contact_light",
            "full",
        )

    def _uses_contact_light_randomization(self) -> bool:
        return self.domain_randomization_level in ("full_contact_light", "full")

    def _maybe_randomize_domain(self) -> None:
        self._restore_domain()
        if self.geometry_profile != "single" and not self._uses_light_geometry_randomization():
            spec = self._sample_geometry_spec(randomize_sizes=False)
            self._apply_geometry_spec(
                spec,
                center_xy=np.zeros(2, dtype=np.float64),
                fixture_height_offset=0.0,
                table_height_offset=0.0,
            )
        if not self.randomize_domain:
            return

        hole_color = self.np_random.uniform(0.25, 0.85, size=3)
        table_color = self.np_random.uniform(0.15, 0.55, size=3)
        peg_color = self.np_random.uniform(0.1, 0.9, size=3)
        self.model.geom_rgba[self._geom_id("hole_plate"), :3] = hole_color
        for geom_id in self.hole_wall_geom_ids.values():
            self.model.geom_rgba[geom_id, :3] = hole_color
        self.model.geom_rgba[self._geom_id("table_top"), :3] = table_color
        self.model.geom_rgba[self._geom_id("peg_geom"), :3] = peg_color
        self.model.light_diffuse[:, :3] = self.np_random.uniform(0.45, 1.05, size=(self.model.nlight, 3))

        if self._uses_visual_camera_randomization():
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

        if self._uses_control_randomization():
            self._randomize_control_channel()

        if self._uses_light_geometry_randomization():
            self._randomize_light_geometry()

        if self._uses_contact_light_randomization():
            self._randomize_contact_dynamics()

    def _restore_domain(self) -> None:
        self.model.geom_rgba[:] = self.base_geom_rgba
        self.model.geom_pos[:] = self.base_geom_pos
        self.model.geom_size[:] = self.base_geom_size
        self.model.geom_type[:] = self.base_geom_type
        self.model.geom_dataid[:] = self.base_geom_dataid
        self.model.geom_quat[:] = self.base_geom_quat
        self.model.geom_rbound[:] = self.base_geom_rbound
        self.model.geom_contype[:] = self.base_geom_contype
        self.model.geom_conaffinity[:] = self.base_geom_conaffinity
        self.model.geom_friction[:] = self.base_geom_friction
        self.model.geom_solref[:] = self.base_geom_solref
        self.model.geom_solimp[:] = self.base_geom_solimp
        self.model.site_pos[:] = self.base_site_pos
        self.model.light_diffuse[:] = self.base_light_diffuse
        self.model.cam_pos[:] = self.base_cam_pos
        self.model.cam_quat[:] = self.base_cam_quat
        self.model.cam_fovy[:] = self.base_cam_fovy
        self.model.dof_damping[:] = self.base_dof_damping
        self.model.actuator_gainprm[:] = self.base_actuator_gainprm
        self.model.actuator_biasprm[:] = self.base_actuator_biasprm
        self._apply_arm_dynamics_multipliers(
            self.nominal_joint_damping_multiplier,
            self.nominal_actuator_kp_multiplier,
        )
        self.data.mocap_pos[self.hole_mocap_id] = self.fixture_pos
        self.data.mocap_quat[self.hole_mocap_id] = np.asarray([1.0, 0.0, 0.0, 0.0])
        self.target_pos = self.fixture_pos.copy()
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
        self.current_hole_center_offset = np.zeros(2, dtype=np.float64)
        self.current_fixture_height_offset = 0.0
        self.current_table_height_offset = 0.0
        self.current_hole_half_size = self.base_hole_half_size
        self.current_peg_radius = self.base_peg_radius
        self.current_geometry_spec = self._make_geometry_spec(
            name="single",
            peg_shape="round",
            hole_shape="square",
            hole_half_size=self.current_hole_half_size,
            peg_radius=self.current_peg_radius,
        )
        self.current_contact_friction_multiplier = 1.0
        self.current_contact_solref_time_multiplier = 1.0
        self.current_contact_solref_damping_multiplier = 1.0
        self.current_contact_solimp_width_multiplier = 1.0
        self.current_joint_damping_multiplier = self.nominal_joint_damping_multiplier
        self.current_actuator_kp_multiplier = self.nominal_actuator_kp_multiplier
        if self.near_hole_crop_source_size_range is None:
            self.current_near_hole_crop_source_size = self.near_hole_crop_source_size

    def _apply_arm_dynamics_multipliers(
        self,
        joint_damping_multiplier: float,
        actuator_kp_multiplier: float,
    ) -> None:
        self.model.dof_damping[self.arm_dof_ids] = (
            self.base_dof_damping[self.arm_dof_ids]
            * joint_damping_multiplier
        )
        self.model.actuator_gainprm[self.arm_actuator_ids, 0] = (
            self.base_actuator_gainprm[self.arm_actuator_ids, 0]
            * actuator_kp_multiplier
        )
        self.model.actuator_biasprm[self.arm_actuator_ids, 1] = (
            self.base_actuator_biasprm[self.arm_actuator_ids, 1]
            * actuator_kp_multiplier
        )

    def set_arm_actuator_kp_multiplier(self, actuator_kp_multiplier: float) -> None:
        if actuator_kp_multiplier <= 0.0:
            raise ValueError("actuator_kp_multiplier must be positive.")
        self.current_actuator_kp_multiplier = float(actuator_kp_multiplier)
        self._apply_arm_dynamics_multipliers(
            self.current_joint_damping_multiplier,
            self.current_actuator_kp_multiplier,
        )

    def set_ik_orientation_weight(self, ik_orientation_weight: float) -> None:
        if ik_orientation_weight < 0.0:
            raise ValueError("ik_orientation_weight cannot be negative.")
        self.ik_orientation_weight = float(ik_orientation_weight)

    def reset_pose_ik_target_xmat(self) -> None:
        self.pose_ik_target_xmat = self.default_pose_ik_target_xmat.copy()

    def set_pose_ik_target_xmat(self, target_xmat: np.ndarray) -> None:
        target_xmat = np.asarray(target_xmat, dtype=np.float64)
        if target_xmat.shape != (3, 3):
            raise ValueError("target_xmat must have shape (3, 3).")
        if not np.all(np.isfinite(target_xmat)):
            raise ValueError("target_xmat must be finite.")
        self.pose_ik_target_xmat = target_xmat.copy()

    def get_pose_ik_target_xmat(self) -> np.ndarray:
        return self.pose_ik_target_xmat.copy()

    def get_peg_tip_xmat(self) -> np.ndarray:
        return self._site_xmat(self.data, self.peg_tip_site_id)

    def set_pose_ik_target_by_planar_yaw_correction(
        self,
        yaw_correction_deg: float,
    ) -> dict[str, float]:
        if not np.isfinite(float(yaw_correction_deg)):
            self.reset_pose_ik_target_xmat()
            return {
                "pose_ik_target_yaw_correction_deg": float("nan"),
                "pose_ik_target_shape_raw_yaw_deg": float("nan"),
                "pose_ik_target_shape_yaw_error_deg": float("nan"),
            }

        current_xmat = self._site_xmat(self.data, self.peg_tip_site_id)
        current_x_axis = current_xmat @ np.asarray([1.0, 0.0, 0.0], dtype=np.float64)
        current_x_xy = self._project_unit_xy(current_x_axis)
        if current_x_xy is None:
            self.reset_pose_ik_target_xmat()
            return {
                "pose_ik_target_yaw_correction_deg": float("nan"),
                "pose_ik_target_shape_raw_yaw_deg": float("nan"),
                "pose_ik_target_shape_yaw_error_deg": float("nan"),
            }

        yaw_rad = float(np.deg2rad(yaw_correction_deg))
        c, s = float(np.cos(yaw_rad)), float(np.sin(yaw_rad))
        target_x_axis = np.asarray(
            [
                c * current_x_xy[0] - s * current_x_xy[1],
                s * current_x_xy[0] + c * current_x_xy[1],
                0.0,
            ],
            dtype=np.float64,
        )

        target_z_axis = self.default_pose_ik_target_xmat[:, 2].copy()
        target_z_norm = float(np.linalg.norm(target_z_axis))
        if target_z_norm <= 1e-9:
            target_z_axis = np.asarray([0.0, 0.0, 1.0], dtype=np.float64)
        else:
            target_z_axis = target_z_axis / target_z_norm

        target_x_axis = target_x_axis - target_z_axis * float(
            np.dot(target_x_axis, target_z_axis)
        )
        target_x_norm = float(np.linalg.norm(target_x_axis))
        if target_x_norm <= 1e-9:
            self.reset_pose_ik_target_xmat()
            return {
                "pose_ik_target_yaw_correction_deg": float("nan"),
                "pose_ik_target_shape_raw_yaw_deg": float("nan"),
                "pose_ik_target_shape_yaw_error_deg": float("nan"),
            }
        target_x_axis = target_x_axis / target_x_norm
        target_y_axis = np.cross(target_z_axis, target_x_axis)
        target_y_axis = target_y_axis / max(float(np.linalg.norm(target_y_axis)), 1e-9)
        target_xmat = np.column_stack((target_x_axis, target_y_axis, target_z_axis))
        self.set_pose_ik_target_xmat(target_xmat)

        raw_yaw_deg, yaw_error_deg = self._shape_yaw_metrics_for_xmat(target_xmat)
        return {
            "pose_ik_target_yaw_correction_deg": float(yaw_correction_deg),
            "pose_ik_target_shape_raw_yaw_deg": float(raw_yaw_deg),
            "pose_ik_target_shape_yaw_error_deg": float(yaw_error_deg),
        }

    def set_pose_ik_target_by_shortest_equivalent_planar_yaw_correction(
        self,
        yaw_correction_deg: float,
    ) -> dict[str, float]:
        period_deg = self._shape_yaw_period_deg()
        if not np.isfinite(period_deg) or period_deg <= 0.0 or period_deg >= 360.0:
            return self.set_pose_ik_target_by_planar_yaw_correction(yaw_correction_deg)

        base_correction = float(yaw_correction_deg)
        if not np.isfinite(base_correction):
            return self.set_pose_ik_target_by_planar_yaw_correction(base_correction)

        candidate_offsets = np.arange(
            -int(np.floor(180.0 / period_deg)),
            int(np.floor(180.0 / period_deg)) + 1,
            dtype=np.int32,
        )
        original_xmat = self.get_pose_ik_target_xmat()
        current_qpos = self.data.qpos[self.arm_qpos_ids].copy()
        target_tip_pos = self.last_target_tip_pos.copy()
        if not np.all(np.isfinite(target_tip_pos)):
            target_tip_pos = self._site_xpos(self.data, self.peg_tip_site_id)

        candidates: list[tuple[float, dict[str, float], np.ndarray]] = []
        for offset in candidate_offsets:
            candidate_correction = float(base_correction + float(offset) * period_deg)
            result = self.set_pose_ik_target_by_planar_yaw_correction(
                candidate_correction
            )
            candidate_xmat = self.get_pose_ik_target_xmat()
            q_target, _, ik_error, _ = self._solve_ik_with_diagnostics(
                target_tip_pos
            )
            wrist_delta = q_target[3:] - current_qpos[3:]
            wrist_norm = float(np.linalg.norm(wrist_delta))
            wrist_max = float(np.max(np.abs(wrist_delta))) if wrist_delta.size else 0.0
            joint_margin, joint_normalized_margin = self._joint_limit_metrics(q_target)
            yaw_error = float(
                result.get("pose_ik_target_shape_yaw_error_deg", float("nan"))
            )
            yaw_penalty = 0.0 if np.isfinite(yaw_error) else 1.0
            score = (
                wrist_norm
                + 0.25 * wrist_max
                + 10.0 * float(max(ik_error, 0.0))
                + yaw_penalty
            )
            candidates.append(
                (
                    score,
                    {
                        **result,
                        "pose_ik_target_equivalent_yaw_correction_deg": candidate_correction,
                        "pose_ik_target_equivalent_offset": float(offset),
                        "pose_ik_target_equivalent_wrist_norm_deg": float(
                            np.rad2deg(wrist_norm)
                        ),
                        "pose_ik_target_equivalent_wrist_max_deg": float(
                            np.rad2deg(wrist_max)
                        ),
                        "pose_ik_target_equivalent_ik_error": float(ik_error),
                        "pose_ik_target_equivalent_joint_margin": float(joint_margin),
                        "pose_ik_target_equivalent_joint_normalized_margin": float(
                            joint_normalized_margin
                        ),
                    },
                    candidate_xmat.copy(),
                )
            )

        if not candidates:
            self.set_pose_ik_target_xmat(original_xmat)
            return self.set_pose_ik_target_by_planar_yaw_correction(base_correction)

        baseline_items = [
            item for item in candidates if abs(item[1]["pose_ik_target_equivalent_offset"]) < 0.5
        ]
        baseline_score, baseline, baseline_xmat = (
            baseline_items[0] if baseline_items else min(candidates, key=lambda item: item[0])
        )
        baseline_wrist_norm = float(
            np.deg2rad(baseline["pose_ik_target_equivalent_wrist_norm_deg"])
        )
        baseline_ik_error = float(baseline["pose_ik_target_equivalent_ik_error"])
        baseline_margin = float(
            baseline["pose_ik_target_equivalent_joint_normalized_margin"]
        )

        gated_candidates: list[tuple[float, dict[str, float], np.ndarray]] = []
        for score, result, candidate_xmat in candidates:
            candidate_correction = float(
                result["pose_ik_target_equivalent_yaw_correction_deg"]
            )
            wrist_norm = float(
                np.deg2rad(result["pose_ik_target_equivalent_wrist_norm_deg"])
            )
            wrist_max = float(
                np.deg2rad(result["pose_ik_target_equivalent_wrist_max_deg"])
            )
            ik_error = float(result["pose_ik_target_equivalent_ik_error"])
            normalized_margin = float(
                result["pose_ik_target_equivalent_joint_normalized_margin"]
            )
            correction_ok = abs(candidate_correction) <= max(
                120.0,
                abs(base_correction) + 0.5 * period_deg,
            )
            ik_ok = ik_error <= max(0.008, baseline_ik_error + 0.002)
            margin_ok = normalized_margin >= max(0.01, baseline_margin - 0.03)
            wrist_ok = wrist_max <= np.deg2rad(140.0)
            improves_wrist = wrist_norm <= max(
                np.deg2rad(5.0),
                baseline_wrist_norm - np.deg2rad(8.0),
            )
            if correction_ok and ik_ok and margin_ok and wrist_ok and improves_wrist:
                gated_candidates.append((score, result, candidate_xmat))

        if gated_candidates:
            best_score, best, best_xmat = min(
                gated_candidates,
                key=lambda item: item[0],
            )
        else:
            best_score, best, best_xmat = baseline_score, baseline, baseline_xmat
            best = {**best, "pose_ik_target_equivalent_fallback_to_baseline": 1.0}

        self.set_pose_ik_target_xmat(best_xmat)
        return {**best, "pose_ik_target_equivalent_score": float(best_score)}

    def set_pose_ik_target_by_wrist_limited_equivalent_planar_yaw_correction(
        self,
        yaw_correction_deg: float,
        *,
        max_wrist_target_abs_deg: float,
        max_wrist_delta_deg: float | None = None,
        max_wrist_target_jump_deg: float | None = None,
        min_wrist_improvement_deg: float = 0.0,
        max_equivalent_correction_abs_deg: float | None = None,
        ik_error_slack: float = 0.004,
        joint_margin_slack: float = 0.04,
    ) -> dict[str, float]:
        period_deg = self._shape_yaw_period_deg()
        if not np.isfinite(period_deg) or period_deg <= 0.0 or period_deg >= 360.0:
            return self.set_pose_ik_target_by_planar_yaw_correction(yaw_correction_deg)

        base_correction = float(yaw_correction_deg)
        if not np.isfinite(base_correction):
            return self.set_pose_ik_target_by_planar_yaw_correction(base_correction)

        max_wrist_target_abs_rad = float(np.deg2rad(max_wrist_target_abs_deg))
        if not np.isfinite(max_wrist_target_abs_rad) or max_wrist_target_abs_rad <= 0.0:
            return self.set_pose_ik_target_by_planar_yaw_correction(base_correction)
        max_wrist_delta_rad = (
            None
            if max_wrist_delta_deg is None
            else float(np.deg2rad(max_wrist_delta_deg))
        )
        max_wrist_target_jump_rad = (
            None
            if max_wrist_target_jump_deg is None
            else float(np.deg2rad(max_wrist_target_jump_deg))
        )
        min_wrist_improvement_rad = max(
            0.0,
            float(np.deg2rad(min_wrist_improvement_deg)),
        )
        max_equivalent_correction_abs = (
            None
            if max_equivalent_correction_abs_deg is None
            else float(max_equivalent_correction_abs_deg)
        )

        candidate_offsets = np.arange(
            -int(np.floor(180.0 / period_deg)),
            int(np.floor(180.0 / period_deg)) + 1,
            dtype=np.int32,
        )
        original_xmat = self.get_pose_ik_target_xmat()
        current_qpos = self.data.qpos[self.arm_qpos_ids].copy()
        previous_target_qpos = self.last_joint_target_qpos.copy()
        if not np.all(np.isfinite(previous_target_qpos)):
            previous_target_qpos = current_qpos.copy()
        target_tip_pos = self.last_target_tip_pos.copy()
        if not np.all(np.isfinite(target_tip_pos)):
            target_tip_pos = self._site_xpos(self.data, self.peg_tip_site_id)

        candidates: list[tuple[float, dict[str, float], np.ndarray]] = []
        baseline: tuple[float, dict[str, float], np.ndarray] | None = None
        for offset in candidate_offsets:
            candidate_correction = float(base_correction + float(offset) * period_deg)
            result = self.set_pose_ik_target_by_planar_yaw_correction(
                candidate_correction
            )
            candidate_xmat = self.get_pose_ik_target_xmat()
            q_target, _, ik_error, _ = self._solve_ik_with_diagnostics(
                target_tip_pos
            )
            wrist_delta = q_target[3:] - current_qpos[3:]
            wrist_norm = float(np.linalg.norm(wrist_delta))
            wrist_delta_max = (
                float(np.max(np.abs(wrist_delta))) if wrist_delta.size else 0.0
            )
            wrist_abs_max = (
                float(np.max(np.abs(q_target[3:]))) if q_target[3:].size else 0.0
            )
            wrist_target_jump_max = (
                float(np.max(np.abs(q_target[3:] - previous_target_qpos[3:])))
                if q_target[3:].size
                else 0.0
            )
            joint_margin, joint_normalized_margin = self._joint_limit_metrics(q_target)
            yaw_error = float(
                result.get("pose_ik_target_shape_yaw_error_deg", float("nan"))
            )
            score = (
                wrist_abs_max
                + 0.25 * wrist_delta_max
                + 0.05 * wrist_norm
                + 20.0 * float(max(ik_error, 0.0))
                + (0.0 if np.isfinite(yaw_error) else 10.0)
            )
            item = (
                score,
                {
                    **result,
                    "pose_ik_target_equivalent_yaw_correction_deg": candidate_correction,
                    "pose_ik_target_equivalent_offset": float(offset),
                    "pose_ik_target_equivalent_wrist_norm_deg": float(
                        np.rad2deg(wrist_norm)
                    ),
                    "pose_ik_target_equivalent_wrist_max_deg": float(
                        np.rad2deg(wrist_delta_max)
                    ),
                    "pose_ik_target_equivalent_wrist_abs_max_deg": float(
                        np.rad2deg(wrist_abs_max)
                    ),
                    "pose_ik_target_equivalent_wrist_target_jump_deg": float(
                        np.rad2deg(wrist_target_jump_max)
                    ),
                    "pose_ik_target_equivalent_ik_error": float(ik_error),
                    "pose_ik_target_equivalent_joint_margin": float(joint_margin),
                    "pose_ik_target_equivalent_joint_normalized_margin": float(
                        joint_normalized_margin
                    ),
                },
                candidate_xmat.copy(),
            )
            candidates.append(item)
            if abs(float(offset)) < 0.5:
                baseline = item

        if not candidates:
            self.set_pose_ik_target_xmat(original_xmat)
            return self.set_pose_ik_target_by_planar_yaw_correction(base_correction)

        if baseline is None:
            baseline = min(candidates, key=lambda item: item[0])
        _, baseline_result, baseline_xmat = baseline
        baseline_ik_error = float(baseline_result["pose_ik_target_equivalent_ik_error"])
        baseline_margin = float(
            baseline_result["pose_ik_target_equivalent_joint_normalized_margin"]
        )
        baseline_wrist_norm = float(
            np.deg2rad(baseline_result["pose_ik_target_equivalent_wrist_norm_deg"])
        )
        baseline_wrist_abs_max = float(
            np.deg2rad(baseline_result["pose_ik_target_equivalent_wrist_abs_max_deg"])
        )

        gated: list[tuple[float, dict[str, float], np.ndarray]] = []
        for item in candidates:
            _, result, _ = item
            candidate_correction = float(
                result["pose_ik_target_equivalent_yaw_correction_deg"]
            )
            wrist_norm = float(
                np.deg2rad(result["pose_ik_target_equivalent_wrist_norm_deg"])
            )
            wrist_delta_max = float(
                np.deg2rad(result["pose_ik_target_equivalent_wrist_max_deg"])
            )
            ik_error = float(result["pose_ik_target_equivalent_ik_error"])
            normalized_margin = float(
                result["pose_ik_target_equivalent_joint_normalized_margin"]
            )
            wrist_abs_max = float(
                np.deg2rad(result["pose_ik_target_equivalent_wrist_abs_max_deg"])
            )
            wrist_target_jump_max = float(
                np.deg2rad(
                    result["pose_ik_target_equivalent_wrist_target_jump_deg"]
                )
            )
            offset = float(result["pose_ik_target_equivalent_offset"])
            ik_ok = ik_error <= max(0.008, baseline_ik_error + ik_error_slack)
            margin_ok = normalized_margin >= max(0.01, baseline_margin - joint_margin_slack)
            wrist_ok = wrist_abs_max <= max_wrist_target_abs_rad
            delta_ok = bool(
                max_wrist_delta_rad is None
                or wrist_delta_max <= max_wrist_delta_rad
            )
            target_jump_ok = bool(
                max_wrist_target_jump_rad is None
                or wrist_target_jump_max <= max_wrist_target_jump_rad
            )
            correction_ok = bool(
                max_equivalent_correction_abs is None
                or abs(candidate_correction) <= max_equivalent_correction_abs
            )
            improvement_ok = bool(
                abs(offset) < 0.5
                or min_wrist_improvement_rad <= 0.0
                or wrist_norm
                <= max(np.deg2rad(2.0), baseline_wrist_norm - min_wrist_improvement_rad)
                or wrist_abs_max
                <= max(
                    np.deg2rad(2.0),
                    baseline_wrist_abs_max - min_wrist_improvement_rad,
                )
            )
            if (
                ik_ok
                and margin_ok
                and wrist_ok
                and delta_ok
                and target_jump_ok
                and correction_ok
                and improvement_ok
            ):
                gated.append(item)

        if gated:
            best_score, best, best_xmat = min(gated, key=lambda item: item[0])
        else:
            best_score, best, best_xmat = baseline
            best = {
                **best,
                "pose_ik_target_equivalent_fallback_to_baseline": 1.0,
                "pose_ik_target_equivalent_wrist_limit_rejected": 1.0,
            }

        self.set_pose_ik_target_xmat(best_xmat)
        return {**best, "pose_ik_target_equivalent_score": float(best_score)}

    def _pose_ik_target_xmat_from_planar_x_axis(
        self,
        target_x_axis: np.ndarray,
    ) -> np.ndarray | None:
        target_x_axis = np.asarray(target_x_axis, dtype=np.float64).reshape(3)
        target_z_axis = self.default_pose_ik_target_xmat[:, 2].copy()
        target_z_norm = float(np.linalg.norm(target_z_axis))
        if target_z_norm <= 1e-9:
            target_z_axis = np.asarray([0.0, 0.0, 1.0], dtype=np.float64)
        else:
            target_z_axis = target_z_axis / target_z_norm

        target_x_axis = target_x_axis - target_z_axis * float(
            np.dot(target_x_axis, target_z_axis)
        )
        target_x_norm = float(np.linalg.norm(target_x_axis))
        if target_x_norm <= 1e-9:
            return None
        target_x_axis = target_x_axis / target_x_norm
        target_y_axis = np.cross(target_z_axis, target_x_axis)
        target_y_norm = float(np.linalg.norm(target_y_axis))
        if target_y_norm <= 1e-9:
            return None
        target_y_axis = target_y_axis / target_y_norm
        return np.column_stack((target_x_axis, target_y_axis, target_z_axis))

    def set_pose_ik_target_to_nearest_shape_hole_yaw(
        self,
        *,
        max_wrist_target_abs_deg: float | None = None,
        max_wrist_delta_deg: float | None = None,
        max_wrist_target_jump_deg: float | None = None,
        max_wrist_target_delta_from_rest_deg: float | None = None,
        ik_error_slack: float = 0.004,
        joint_margin_slack: float = 0.04,
    ) -> dict[str, float]:
        period_deg = self._shape_yaw_period_deg()
        if not np.isfinite(period_deg) or period_deg <= 0.0:
            self.reset_pose_ik_target_xmat()
            return {
                "pose_ik_target_raw_yaw_deg": float("nan"),
                "pose_ik_target_shape_yaw_error_deg": float("nan"),
            }

        symmetry_order = max(1, int(round(360.0 / period_deg)))
        if not np.isclose(symmetry_order * period_deg, 360.0, atol=1e-4):
            symmetry_order = max(1, int(np.floor(360.0 / period_deg)))

        hole_xmat = self._body_xmat(self.data, self.hole_body_id)
        current_xmat = self._site_xmat(self.data, self.peg_tip_site_id)
        hole_x_xy = self._project_unit_xy(
            hole_xmat @ np.asarray([1.0, 0.0, 0.0], dtype=np.float64)
        )
        current_x_xy = self._project_unit_xy(
            current_xmat @ np.asarray([1.0, 0.0, 0.0], dtype=np.float64)
        )
        if hole_x_xy is None or current_x_xy is None:
            self.reset_pose_ik_target_xmat()
            return {
                "pose_ik_target_raw_yaw_deg": float("nan"),
                "pose_ik_target_shape_yaw_error_deg": float("nan"),
            }

        original_xmat = self.get_pose_ik_target_xmat()
        current_qpos = self.data.qpos[self.arm_qpos_ids].copy()
        previous_target_qpos = self.last_joint_target_qpos.copy()
        if not np.all(np.isfinite(previous_target_qpos)):
            previous_target_qpos = current_qpos.copy()
        target_tip_pos = self.last_target_tip_pos.copy()
        if not np.all(np.isfinite(target_tip_pos)):
            target_tip_pos = self._site_xpos(self.data, self.peg_tip_site_id)

        max_wrist_target_abs_rad = (
            None
            if max_wrist_target_abs_deg is None
            else float(np.deg2rad(max_wrist_target_abs_deg))
        )
        max_wrist_delta_rad = (
            None
            if max_wrist_delta_deg is None
            else float(np.deg2rad(max_wrist_delta_deg))
        )
        max_wrist_target_jump_rad = (
            None
            if max_wrist_target_jump_deg is None
            else float(np.deg2rad(max_wrist_target_jump_deg))
        )
        max_wrist_target_delta_from_rest_rad = (
            None
            if max_wrist_target_delta_from_rest_deg is None
            else float(np.deg2rad(max_wrist_target_delta_from_rest_deg))
        )

        candidates: list[tuple[float, dict[str, float], np.ndarray]] = []
        baseline: tuple[float, dict[str, float], np.ndarray] | None = None
        best_current_alignment = -float("inf")
        for offset in range(symmetry_order):
            yaw_deg = float(offset) * float(period_deg)
            yaw_rad = float(np.deg2rad(yaw_deg))
            c, s = float(np.cos(yaw_rad)), float(np.sin(yaw_rad))
            candidate_x_xy = np.asarray(
                [
                    c * hole_x_xy[0] - s * hole_x_xy[1],
                    s * hole_x_xy[0] + c * hole_x_xy[1],
                    0.0,
                ],
                dtype=np.float64,
            )
            target_xmat = self._pose_ik_target_xmat_from_planar_x_axis(
                candidate_x_xy
            )
            if target_xmat is None:
                continue

            self.set_pose_ik_target_xmat(target_xmat)
            q_target, _, ik_error, _ = self._solve_ik_with_diagnostics(
                target_tip_pos
            )
            q_target = self._nearest_wrist_target_equivalent(q_target, current_qpos)
            wrist_delta = q_target[3:] - current_qpos[3:]
            wrist_norm = float(np.linalg.norm(wrist_delta))
            wrist_delta_max = (
                float(np.max(np.abs(wrist_delta))) if wrist_delta.size else 0.0
            )
            wrist_abs_max = (
                float(np.max(np.abs(q_target[3:]))) if q_target[3:].size else 0.0
            )
            wrist_target_jump_max = (
                float(np.max(np.abs(q_target[3:] - previous_target_qpos[3:])))
                if q_target[3:].size
                else 0.0
            )
            wrist_rest_delta_max = (
                float(np.max(np.abs(q_target[3:] - self.rest_qpos[3:])))
                if q_target[3:].size
                else 0.0
            )
            joint_margin, joint_normalized_margin = self._joint_limit_metrics(q_target)
            raw_yaw_deg, yaw_error_deg = self._shape_yaw_metrics_for_xmat(target_xmat)
            current_alignment = float(np.dot(current_x_xy, candidate_x_xy))
            target_delta_deg = self._signed_planar_angle_deg(
                current_x_xy,
                candidate_x_xy,
            )
            score = (
                0.20 * wrist_abs_max
                + 0.80 * wrist_delta_max
                + 0.20 * wrist_norm
                + 0.90 * wrist_target_jump_max
                + 0.45 * wrist_rest_delta_max
                + 0.04 * abs(float(np.deg2rad(target_delta_deg)))
                + 20.0 * float(max(ik_error, 0.0))
                - 0.05 * float(joint_normalized_margin)
            )
            result = {
                "pose_ik_target_raw_yaw_deg": float(raw_yaw_deg),
                "pose_ik_target_shape_yaw_error_deg": float(yaw_error_deg),
                "pose_ik_target_yaw_correction_deg": float(target_delta_deg),
                "pose_ik_target_equivalent_yaw_correction_deg": float(
                    target_delta_deg
                ),
                "pose_ik_target_equivalent_offset": float(offset),
                "pose_ik_target_equivalent_wrist_norm_deg": float(
                    np.rad2deg(wrist_norm)
                ),
                "pose_ik_target_equivalent_wrist_max_deg": float(
                    np.rad2deg(wrist_delta_max)
                ),
                "pose_ik_target_equivalent_wrist_abs_max_deg": float(
                    np.rad2deg(wrist_abs_max)
                ),
                "pose_ik_target_equivalent_wrist_target_jump_deg": float(
                    np.rad2deg(wrist_target_jump_max)
                ),
                "pose_ik_target_equivalent_wrist_rest_delta_deg": float(
                    np.rad2deg(wrist_rest_delta_max)
                ),
                "pose_ik_target_equivalent_ik_error": float(ik_error),
                "pose_ik_target_equivalent_joint_margin": float(joint_margin),
                "pose_ik_target_equivalent_joint_normalized_margin": float(
                    joint_normalized_margin
                ),
                "pose_ik_target_absolute_shape_target": 1.0,
            }
            item = (float(score), result, target_xmat.copy())
            candidates.append(item)
            if current_alignment > best_current_alignment:
                best_current_alignment = current_alignment
                baseline = item

        if not candidates:
            self.set_pose_ik_target_xmat(original_xmat)
            return {
                "pose_ik_target_raw_yaw_deg": float("nan"),
                "pose_ik_target_shape_yaw_error_deg": float("nan"),
                "pose_ik_target_equivalent_fallback_to_baseline": 1.0,
            }

        if baseline is None:
            baseline = min(candidates, key=lambda item: item[0])
        _, baseline_result, _ = baseline
        baseline_ik_error = float(baseline_result["pose_ik_target_equivalent_ik_error"])
        baseline_margin = float(
            baseline_result["pose_ik_target_equivalent_joint_normalized_margin"]
        )

        gated: list[tuple[float, dict[str, float], np.ndarray]] = []
        for item in candidates:
            _, result, _ = item
            ik_error = float(result["pose_ik_target_equivalent_ik_error"])
            normalized_margin = float(
                result["pose_ik_target_equivalent_joint_normalized_margin"]
            )
            wrist_abs_max = float(
                np.deg2rad(result["pose_ik_target_equivalent_wrist_abs_max_deg"])
            )
            wrist_delta_max = float(
                np.deg2rad(result["pose_ik_target_equivalent_wrist_max_deg"])
            )
            wrist_target_jump_max = float(
                np.deg2rad(
                    result["pose_ik_target_equivalent_wrist_target_jump_deg"]
                )
            )
            wrist_rest_delta_max = float(
                np.deg2rad(result["pose_ik_target_equivalent_wrist_rest_delta_deg"])
            )
            ik_ok = ik_error <= max(0.008, baseline_ik_error + ik_error_slack)
            margin_ok = normalized_margin >= max(0.01, baseline_margin - joint_margin_slack)
            wrist_abs_ok = bool(
                max_wrist_target_abs_rad is None
                or wrist_abs_max <= max_wrist_target_abs_rad
            )
            wrist_delta_ok = bool(
                max_wrist_delta_rad is None
                or wrist_delta_max <= max_wrist_delta_rad
            )
            target_jump_ok = bool(
                max_wrist_target_jump_rad is None
                or wrist_target_jump_max <= max_wrist_target_jump_rad
            )
            rest_delta_ok = bool(
                max_wrist_target_delta_from_rest_rad is None
                or wrist_rest_delta_max <= max_wrist_target_delta_from_rest_rad
            )
            if (
                ik_ok
                and margin_ok
                and wrist_abs_ok
                and wrist_delta_ok
                and target_jump_ok
                and rest_delta_ok
            ):
                gated.append(item)

        if gated:
            best_score, best, best_xmat = min(gated, key=lambda item: item[0])
            self.set_pose_ik_target_xmat(best_xmat)
            return {**best, "pose_ik_target_equivalent_score": float(best_score)}

        baseline_score, best, _ = baseline
        self.set_pose_ik_target_xmat(original_xmat)
        return {
            **best,
            "pose_ik_target_equivalent_score": float(baseline_score),
            "pose_ik_target_equivalent_fallback_to_baseline": 1.0,
            "pose_ik_target_equivalent_wrist_limit_rejected": 1.0,
            "pose_ik_target_absolute_shape_target_rejected": 1.0,
        }

    def set_pose_ik_target_to_nearest_square_hole_yaw(self) -> dict[str, float]:
        spec = self.current_geometry_spec
        if spec.peg_shape != "square" or spec.hole_shape != "square":
            self.reset_pose_ik_target_xmat()
            return {
                "pose_ik_target_raw_yaw_deg": float("nan"),
                "pose_ik_target_square_yaw_error_deg": float("nan"),
            }

        hole_xmat = self._body_xmat(self.data, self.hole_body_id)
        current_xmat = self._site_xmat(self.data, self.peg_tip_site_id)
        current_x_xy = self._project_unit_xy(
            current_xmat @ np.asarray([1.0, 0.0, 0.0], dtype=np.float64)
        )
        hole_x_axis = hole_xmat @ np.asarray([1.0, 0.0, 0.0], dtype=np.float64)
        hole_y_axis = hole_xmat @ np.asarray([0.0, 1.0, 0.0], dtype=np.float64)
        candidate_axes = (
            hole_x_axis,
            hole_y_axis,
            -hole_x_axis,
            -hole_y_axis,
        )
        candidate_xy_axes: list[tuple[np.ndarray, np.ndarray]] = []
        for candidate_axis in candidate_axes:
            candidate_xy = self._project_unit_xy(candidate_axis)
            if candidate_xy is not None:
                candidate_xy_axes.append((candidate_axis, candidate_xy))
        if current_x_xy is None or not candidate_xy_axes:
            self.reset_pose_ik_target_xmat()
            return {
                "pose_ik_target_raw_yaw_deg": float("nan"),
                "pose_ik_target_square_yaw_error_deg": float("nan"),
            }

        target_x_axis = max(
            candidate_xy_axes,
            key=lambda item: float(np.dot(current_x_xy, item[1])),
        )[0]
        target_z_axis = self.default_pose_ik_target_xmat[:, 2].copy()
        target_z_norm = float(np.linalg.norm(target_z_axis))
        if target_z_norm <= 1e-9:
            target_z_axis = np.asarray([0.0, 0.0, 1.0], dtype=np.float64)
        else:
            target_z_axis = target_z_axis / target_z_norm

        target_x_axis = target_x_axis - target_z_axis * float(
            np.dot(target_x_axis, target_z_axis)
        )
        target_x_norm = float(np.linalg.norm(target_x_axis))
        if target_x_norm <= 1e-9:
            self.reset_pose_ik_target_xmat()
            return {
                "pose_ik_target_raw_yaw_deg": float("nan"),
                "pose_ik_target_square_yaw_error_deg": float("nan"),
            }
        target_x_axis = target_x_axis / target_x_norm
        target_y_axis = np.cross(target_z_axis, target_x_axis)
        target_y_axis = target_y_axis / max(float(np.linalg.norm(target_y_axis)), 1e-9)
        target_xmat = np.column_stack((target_x_axis, target_y_axis, target_z_axis))
        self.set_pose_ik_target_xmat(target_xmat)
        raw_yaw_deg, yaw_error_deg = self._square_symmetry_yaw_metrics(target_xmat)
        return {
            "pose_ik_target_raw_yaw_deg": raw_yaw_deg,
            "pose_ik_target_square_yaw_error_deg": yaw_error_deg,
        }

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

    def flush_control_randomization_history(self, action: np.ndarray) -> None:
        action = np.asarray(action, dtype=np.float64)
        action = np.clip(action, self.action_space.low, self.action_space.high)
        scaled_action = action * self.current_action_scale_multiplier
        safe_action = np.clip(
            scaled_action,
            self.action_space.low,
            self.action_space.high,
        )
        self.action_delay_buffer = [
            safe_action.copy() for _ in range(self.current_action_delay)
        ]
        self.previous_filtered_action = safe_action.copy()

    def _apply_control_randomization(self, action: np.ndarray) -> np.ndarray:
        self.last_commanded_action = action.copy()
        if not self._uses_control_randomization():
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

    def _randomize_light_geometry(self) -> None:
        hole_center_offset = self.np_random.uniform(
            -self.geometry_hole_center_xy_jitter,
            self.geometry_hole_center_xy_jitter,
        )
        fixture_height_offset = float(
            self.np_random.uniform(
                -self.geometry_fixture_height_jitter,
                self.geometry_fixture_height_jitter,
            )
        )
        table_height_offset = float(
            self.np_random.uniform(
                -self.geometry_table_height_jitter,
                self.geometry_table_height_jitter,
            )
        )
        spec = self._sample_geometry_spec(randomize_sizes=True)
        self._apply_geometry_spec(
            spec,
            center_xy=hole_center_offset,
            fixture_height_offset=fixture_height_offset,
            table_height_offset=table_height_offset,
        )

    @staticmethod
    def _yaw_quat(yaw: float) -> np.ndarray:
        half_yaw = 0.5 * float(yaw)
        return np.asarray([np.cos(half_yaw), 0.0, 0.0, np.sin(half_yaw)], dtype=np.float64)

    def _set_hole_wall_active(self, geom_id: int, active: bool) -> None:
        if active:
            self.model.geom_contype[geom_id] = self.active_hole_wall_contype
            self.model.geom_conaffinity[geom_id] = self.active_hole_wall_conaffinity
            self.model.geom_rgba[geom_id] = self.active_hole_wall_rgba
        else:
            self.model.geom_contype[geom_id] = 0
            self.model.geom_conaffinity[geom_id] = 0
            self.model.geom_rgba[geom_id, 3] = 0.0

    def _deactivate_hole_wall(self, name: str) -> None:
        geom_id = self.hole_wall_geom_ids[name]
        self._set_hole_wall_active(geom_id, False)
        self.model.geom_pos[geom_id] = np.asarray([0.0, 0.0, -1.0], dtype=np.float64)
        self.model.geom_quat[geom_id] = np.asarray([1.0, 0.0, 0.0, 0.0], dtype=np.float64)
        self.model.geom_size[geom_id] = np.asarray([0.001, 0.001, 0.001], dtype=np.float64)
        self.model.geom_rbound[geom_id] = 0.002

    def _set_hole_collision_wall_visibility(self, used: set[str], visible: bool) -> None:
        alpha = 1.0 if visible else 0.0
        for name in used:
            geom_id = self.hole_wall_geom_ids[name]
            rgba = self.active_hole_wall_rgba.copy()
            rgba[3] = alpha
            self.model.geom_rgba[geom_id] = rgba

    def _set_hole_wall_box(
        self,
        name: str,
        center_xy: np.ndarray,
        *,
        yaw: float,
        half_length: float,
    ) -> None:
        geom_id = self.hole_wall_geom_ids[name]
        reference_id = self.hole_wall_geom_ids["hole_north"]
        half_thickness = float(self.base_geom_size[reference_id, 1])
        half_height = float(self.base_geom_size[reference_id, 2])
        z_pos = float(self.base_geom_pos[reference_id, 2])

        self.model.geom_type[geom_id] = int(mujoco.mjtGeom.mjGEOM_BOX)
        self.model.geom_dataid[geom_id] = -1
        self.model.geom_pos[geom_id] = np.asarray(
            [float(center_xy[0]), float(center_xy[1]), z_pos],
            dtype=np.float64,
        )
        self.model.geom_quat[geom_id] = self._yaw_quat(yaw)
        self.model.geom_size[geom_id] = np.asarray(
            [max(float(half_length), 0.001), half_thickness, half_height],
            dtype=np.float64,
        )
        self.model.geom_rbound[geom_id] = max(
            self.base_geom_rbound[geom_id],
            float(np.sqrt((max(float(half_length), 0.001) ** 2) + half_thickness**2 + half_height**2)),
        )
        self._set_hole_wall_active(geom_id, True)

    def _deactivate_hole_polygon_visual_walls(self) -> None:
        for geom_id in self.hole_polygon_visual_geom_ids.values():
            self.model.geom_type[geom_id] = int(mujoco.mjtGeom.mjGEOM_BOX)
            self.model.geom_dataid[geom_id] = -1
            self.model.geom_pos[geom_id] = np.asarray([0.0, 0.0, -1.0], dtype=np.float64)
            self.model.geom_quat[geom_id] = np.asarray([1.0, 0.0, 0.0, 0.0], dtype=np.float64)
            self.model.geom_size[geom_id] = np.asarray([0.001, 0.001, 0.001], dtype=np.float64)
            self.model.geom_rbound[geom_id] = 0.002
            self.model.geom_contype[geom_id] = 0
            self.model.geom_conaffinity[geom_id] = 0
            rgba = self.base_geom_rgba[geom_id].copy()
            rgba[3] = 0.0
            self.model.geom_rgba[geom_id] = rgba

    def _deactivate_true_fixture_walls(self) -> None:
        for geom_id in self.true_fixture_wall_geom_ids.values():
            self.model.geom_type[geom_id] = self.base_geom_type[geom_id]
            self.model.geom_dataid[geom_id] = self.base_geom_dataid[geom_id]
            self.model.geom_pos[geom_id] = np.asarray([0.0, 0.0, -1.0], dtype=np.float64)
            self.model.geom_quat[geom_id] = np.asarray([1.0, 0.0, 0.0, 0.0], dtype=np.float64)
            self.model.geom_size[geom_id] = self.base_geom_size[geom_id]
            self.model.geom_rbound[geom_id] = max(float(self.base_geom_rbound[geom_id]), 0.002)
            self.model.geom_contype[geom_id] = 0
            self.model.geom_conaffinity[geom_id] = 0
            rgba = self.base_geom_rgba[geom_id].copy()
            rgba[3] = 0.0
            self.model.geom_rgba[geom_id] = rgba

    def _deactivate_true_fixture_visual(self) -> None:
        geom_id = self.true_fixture_visual_geom_id
        if geom_id is None:
            return
        self.model.geom_type[geom_id] = self.base_geom_type[geom_id]
        self.model.geom_dataid[geom_id] = self.base_geom_dataid[geom_id]
        self.model.geom_pos[geom_id] = np.asarray([0.0, 0.0, -1.0], dtype=np.float64)
        self.model.geom_quat[geom_id] = np.asarray([1.0, 0.0, 0.0, 0.0], dtype=np.float64)
        self.model.geom_size[geom_id] = self.base_geom_size[geom_id]
        self.model.geom_rbound[geom_id] = max(float(self.base_geom_rbound[geom_id]), 0.002)
        self.model.geom_contype[geom_id] = 0
        self.model.geom_conaffinity[geom_id] = 0
        rgba = self.base_geom_rgba[geom_id].copy()
        rgba[3] = 0.0
        self.model.geom_rgba[geom_id] = rgba

    def _has_true_fixture_visual_mesh(self, hole_shape: str) -> bool:
        mesh_key = self._true_fixture_mesh_profile_key(hole_shape)
        return (
            self.true_fixture_visual_geom_id is not None
            and mesh_key in self.true_fixture_visual_mesh_ids
        )

    def _set_true_fixture_visual_geometry(
        self,
        spec: GeometrySpec,
        center_xy: np.ndarray,
    ) -> bool:
        geom_id = self.true_fixture_visual_geom_id
        mesh_key = self._true_fixture_mesh_profile_key(spec.hole_shape)
        mesh_id = self.true_fixture_visual_mesh_ids.get(mesh_key)
        if geom_id is None or mesh_id is None:
            return False

        reference_id = self.hole_wall_geom_ids["hole_north"]
        mesh_pos = self.model.mesh_pos[mesh_id]
        mesh_quat = self.model.mesh_quat[mesh_id]
        self.model.geom_type[geom_id] = int(mujoco.mjtGeom.mjGEOM_MESH)
        self.model.geom_dataid[geom_id] = mesh_id
        self.model.geom_pos[geom_id] = np.asarray(
            [
                float(center_xy[0]) + float(mesh_pos[0]),
                float(center_xy[1]) + float(mesh_pos[1]),
                float(self.base_geom_pos[reference_id, 2]) + float(mesh_pos[2]),
            ],
            dtype=np.float64,
        )
        fixture_quat = self._quat_multiply(self._yaw_quat(0.0), mesh_quat)
        self.model.geom_quat[geom_id] = fixture_quat / np.linalg.norm(fixture_quat)
        self.model.geom_size[geom_id] = np.asarray([1.0, 1.0, 1.0], dtype=np.float64)
        self.model.geom_rbound[geom_id] = max(
            float(self.base_geom_rbound[reference_id]),
            float(spec.hole_half_size) + 0.05,
        )
        self.model.geom_contype[geom_id] = 0
        self.model.geom_conaffinity[geom_id] = 0
        rgba = self.active_hole_wall_rgba.copy()
        rgba[3] = 1.0
        self.model.geom_rgba[geom_id] = rgba
        return True

    def _activate_true_fixture_mesh_wall(
        self,
        *,
        geom_id: int,
        mesh_id: int,
        center_xy: np.ndarray,
        yaw: float,
        reference_id: int,
        active_rgba: np.ndarray,
        rbound: float,
    ) -> None:
        desired_quat = self._yaw_quat(yaw)
        mesh_pos = self.model.mesh_pos[mesh_id]
        mesh_quat = self.model.mesh_quat[mesh_id]
        cos_yaw = float(np.cos(yaw))
        sin_yaw = float(np.sin(yaw))
        mesh_pos_world = np.asarray(
            [
                cos_yaw * float(mesh_pos[0]) - sin_yaw * float(mesh_pos[1]),
                sin_yaw * float(mesh_pos[0]) + cos_yaw * float(mesh_pos[1]),
                float(mesh_pos[2]),
            ],
            dtype=np.float64,
        )
        self.model.geom_type[geom_id] = int(mujoco.mjtGeom.mjGEOM_MESH)
        self.model.geom_dataid[geom_id] = mesh_id
        self.model.geom_pos[geom_id] = np.asarray(
            [
                float(center_xy[0]) + mesh_pos_world[0],
                float(center_xy[1]) + mesh_pos_world[1],
                float(self.base_geom_pos[reference_id, 2]) + mesh_pos_world[2],
            ],
            dtype=np.float64,
        )
        fixture_quat = self._quat_multiply(desired_quat, mesh_quat)
        self.model.geom_quat[geom_id] = fixture_quat / np.linalg.norm(fixture_quat)
        self.model.geom_size[geom_id] = np.asarray([1.0, 1.0, 1.0], dtype=np.float64)
        self.model.geom_rbound[geom_id] = max(float(self.base_geom_rbound[reference_id]), rbound)
        self.model.geom_contype[geom_id] = self.active_hole_wall_contype
        self.model.geom_conaffinity[geom_id] = self.active_hole_wall_conaffinity
        self.model.geom_rgba[geom_id] = active_rgba
        self.model.geom_friction[geom_id] = self.model.geom_friction[reference_id]
        self.model.geom_solref[geom_id] = self.model.geom_solref[reference_id]
        self.model.geom_solimp[geom_id] = self.model.geom_solimp[reference_id]

    def _set_true_keyhole_fixture_mesh_geometry(
        self,
        spec: GeometrySpec,
        center_xy: np.ndarray,
    ) -> bool:
        if spec.hole_shape != "rectangular_key":
            return False

        required_segments = KEYHOLE_TRUE_FIXTURE_ARC_SEGMENTS + 3
        if len(self.true_fixture_wall_geom_ids) < required_segments:
            return False
        suffix = "_tight_yaw" if self.geometry_true_fixture_variant == "tight_yaw" else ""
        side_mesh_id = self.true_fixture_wall_mesh_ids.get(f"keyhole_tab_side{suffix}")
        front_mesh_id = self.true_fixture_wall_mesh_ids.get(f"keyhole_tab_front{suffix}")
        arc_mesh_id = self.true_fixture_wall_mesh_ids.get(f"keyhole_arc{suffix}")
        if side_mesh_id is None or front_mesh_id is None or arc_mesh_id is None:
            return False

        radius, tab_half_width, tab_length = self._true_fixture_keyhole_dimensions(
            spec.hole_half_size
        )
        if radius <= 1e-6 or tab_half_width <= 1e-6 or tab_half_width >= radius:
            return False

        theta = float(np.arcsin(np.clip(tab_half_width / radius, -0.98, 0.98)))
        x_join = float(np.sqrt(max(radius * radius - tab_half_width * tab_half_width, 0.0)))
        front_x = radius + tab_length
        center = np.asarray(center_xy, dtype=np.float64)

        top_join = center + np.asarray([x_join, tab_half_width], dtype=np.float64)
        front_top = center + np.asarray([front_x, tab_half_width], dtype=np.float64)
        bottom_join = center + np.asarray([x_join, -tab_half_width], dtype=np.float64)
        front_bottom = center + np.asarray([front_x, -tab_half_width], dtype=np.float64)

        segments: list[tuple[np.ndarray, np.ndarray, int]] = [
            (front_top, top_join, side_mesh_id),
        ]
        arc_angles = np.linspace(
            theta,
            2.0 * np.pi - theta,
            KEYHOLE_TRUE_FIXTURE_ARC_SEGMENTS + 1,
        )
        arc_points = [
            center
            + radius
            * np.asarray([float(np.cos(angle)), float(np.sin(angle))], dtype=np.float64)
            for angle in arc_angles
        ]
        for index in range(KEYHOLE_TRUE_FIXTURE_ARC_SEGMENTS):
            segments.append((arc_points[index], arc_points[index + 1], arc_mesh_id))
        segments.extend(
            [
                (bottom_join, front_bottom, side_mesh_id),
                (front_bottom, front_top, front_mesh_id),
            ]
        )

        reference_id = self.hole_wall_geom_ids["hole_north"]
        active_rgba = self.active_hole_wall_rgba.copy()
        active_rgba[3] = 0.0 if self._has_true_fixture_visual_mesh(spec.hole_shape) else 1.0
        for index, (start, end, mesh_id) in enumerate(segments):
            geom_id = self.true_fixture_wall_geom_ids[TRUE_FIXTURE_WALL_NAMES[index]]
            edge = end - start
            edge_length = float(np.linalg.norm(edge))
            if edge_length <= 1e-9:
                continue
            segment_center = 0.5 * (start + end)
            yaw = float(np.arctan2(edge[1], edge[0]) + np.pi)
            self._activate_true_fixture_mesh_wall(
                geom_id=geom_id,
                mesh_id=mesh_id,
                center_xy=segment_center,
                yaw=yaw,
                reference_id=reference_id,
                active_rgba=active_rgba,
                rbound=max(edge_length, radius + tab_length + 0.02),
            )
        return True

    def _set_true_slot_fixture_mesh_geometry(
        self,
        spec: GeometrySpec,
        center_xy: np.ndarray,
    ) -> bool:
        if spec.hole_shape != "slot" or spec.hole_half_extents is None:
            return False

        required_segments = 2 + 2 * SLOT_TRUE_FIXTURE_ARC_SEGMENTS_PER_END
        if len(self.true_fixture_wall_geom_ids) < required_segments:
            return False
        side_mesh_id = self.true_fixture_wall_mesh_ids.get("slot_side")
        arc_mesh_id = self.true_fixture_wall_mesh_ids.get("slot_arc")
        if side_mesh_id is None or arc_mesh_id is None:
            return False

        half_x, half_y = (float(value) for value in spec.hole_half_extents)
        radius = half_y
        straight_half = half_x - radius
        if radius <= 1e-6 or straight_half <= 1e-6:
            return False

        center = np.asarray(center_xy, dtype=np.float64)
        left_center = center + np.asarray([-straight_half, 0.0], dtype=np.float64)
        right_center = center + np.asarray([straight_half, 0.0], dtype=np.float64)

        def arc_points(arc_center: np.ndarray, start: float, stop: float) -> list[np.ndarray]:
            angles = np.linspace(start, stop, SLOT_TRUE_FIXTURE_ARC_SEGMENTS_PER_END + 1)
            return [
                arc_center
                + radius
                * np.asarray([float(np.cos(angle)), float(np.sin(angle))], dtype=np.float64)
                for angle in angles
            ]

        segments: list[tuple[np.ndarray, np.ndarray, int]] = []
        segments.append(
            (
                center + np.asarray([straight_half, radius], dtype=np.float64),
                center + np.asarray([-straight_half, radius], dtype=np.float64),
                side_mesh_id,
            )
        )
        left_arc = arc_points(left_center, 0.5 * np.pi, 1.5 * np.pi)
        for index in range(SLOT_TRUE_FIXTURE_ARC_SEGMENTS_PER_END):
            segments.append((left_arc[index], left_arc[index + 1], arc_mesh_id))
        segments.append(
            (
                center + np.asarray([-straight_half, -radius], dtype=np.float64),
                center + np.asarray([straight_half, -radius], dtype=np.float64),
                side_mesh_id,
            )
        )
        right_arc = arc_points(right_center, 1.5 * np.pi, 2.5 * np.pi)
        for index in range(SLOT_TRUE_FIXTURE_ARC_SEGMENTS_PER_END):
            segments.append((right_arc[index], right_arc[index + 1], arc_mesh_id))

        reference_id = self.hole_wall_geom_ids["hole_north"]
        active_rgba = self.active_hole_wall_rgba.copy()
        active_rgba[3] = 0.0 if self._has_true_fixture_visual_mesh(spec.hole_shape) else 1.0
        for index, (start, end, mesh_id) in enumerate(segments):
            geom_id = self.true_fixture_wall_geom_ids[TRUE_FIXTURE_WALL_NAMES[index]]
            edge = end - start
            edge_length = float(np.linalg.norm(edge))
            if edge_length <= 1e-9:
                continue
            segment_center = 0.5 * (start + end)
            yaw = float(np.arctan2(edge[1], edge[0]) + np.pi)
            self._activate_true_fixture_mesh_wall(
                geom_id=geom_id,
                mesh_id=mesh_id,
                center_xy=segment_center,
                yaw=yaw,
                reference_id=reference_id,
                active_rgba=active_rgba,
                rbound=edge_length,
            )
        return True

    def _set_true_fixture_mesh_geometry(
        self,
        spec: GeometrySpec,
        center_xy: np.ndarray,
    ) -> bool:
        if spec.hole_shape == "slot":
            return self._set_true_slot_fixture_mesh_geometry(spec, center_xy)
        if spec.hole_shape == "rectangular_key":
            return self._set_true_keyhole_fixture_mesh_geometry(spec, center_xy)
        if spec.hole_shape not in ("hex", "triangle"):
            return False
        sides = spec.hole_polygon_sides
        if sides is None:
            return False
        if len(self.true_fixture_wall_geom_ids) < sides:
            return False
        mesh_key = self._true_fixture_mesh_profile_key(spec.hole_shape)
        mesh_id = self.true_fixture_wall_mesh_ids.get(mesh_key)
        if mesh_id is None:
            return False

        radius = float(spec.hole_half_size) / np.cos(np.pi / float(sides))
        vertices = []
        for index in range(sides):
            angle = 0.5 * np.pi + np.pi / float(sides) + 2.0 * np.pi * index / float(sides)
            vertices.append(
                np.asarray(
                    [
                        float(center_xy[0]) + radius * np.cos(angle),
                        float(center_xy[1]) + radius * np.sin(angle),
                    ],
                    dtype=np.float64,
                )
            )

        reference_id = self.hole_wall_geom_ids["hole_north"]
        active_rgba = self.active_hole_wall_rgba.copy()
        active_rgba[3] = 0.0 if self._has_true_fixture_visual_mesh(spec.hole_shape) else 1.0
        for index in range(sides):
            geom_id = self.true_fixture_wall_geom_ids[TRUE_FIXTURE_WALL_NAMES[index]]
            start = vertices[index]
            end = vertices[(index + 1) % sides]
            edge = end - start
            edge_length = float(np.linalg.norm(edge))
            if edge_length <= 1e-9:
                continue
            center = 0.5 * (start + end)
            yaw = float(np.arctan2(edge[1], edge[0]) + np.pi)
            self._activate_true_fixture_mesh_wall(
                geom_id=geom_id,
                mesh_id=mesh_id,
                center_xy=center,
                yaw=yaw,
                reference_id=reference_id,
                active_rgba=active_rgba,
                rbound=edge_length,
            )
        return True

    def _set_hole_polygon_visual_geometry(
        self,
        center_xy: np.ndarray,
        *,
        apothem: float,
        sides: int,
    ) -> None:
        if sides not in (3, 6) or len(self.hole_polygon_visual_geom_ids) < sides:
            return

        available_names = list(POLYGON_HOLE_VISUAL_WALL_NAMES[:sides])
        reference_id = self.hole_wall_geom_ids["hole_north"]
        wall_thickness = float(self.base_geom_size[reference_id, 1])
        half_height = float(self.base_geom_size[reference_id, 2])
        z_pos = float(self.base_geom_pos[reference_id, 2]) + 0.0008
        radius = float(apothem) / np.cos(np.pi / float(sides))
        wall_end_overlap = wall_thickness / max(float(np.tan(np.pi / float(sides))), 1e-6)
        visible_rgba = self.active_hole_wall_rgba.copy()
        visible_rgba[3] = 1.0

        vertices = []
        for index in range(sides):
            angle = 0.5 * np.pi + np.pi / float(sides) + 2.0 * np.pi * index / float(sides)
            vertices.append(
                np.asarray(
                    [
                        float(center_xy[0]) + radius * np.cos(angle),
                        float(center_xy[1]) + radius * np.sin(angle),
                    ],
                    dtype=np.float64,
                )
            )

        for index in range(sides):
            geom_id = self.hole_polygon_visual_geom_ids[available_names[index]]
            start = vertices[index]
            end = vertices[(index + 1) % sides]
            edge = end - start
            edge_length = float(np.linalg.norm(edge))
            if edge_length <= 1e-9:
                continue
            outward = np.asarray([edge[1], -edge[0]], dtype=np.float64) / edge_length
            center = 0.5 * (start + end) + outward * wall_thickness
            yaw = float(np.arctan2(edge[1], edge[0]))
            size = np.asarray(
                [0.5 * edge_length + wall_end_overlap, wall_thickness, half_height],
                dtype=np.float64,
            )
            self.model.geom_type[geom_id] = int(mujoco.mjtGeom.mjGEOM_BOX)
            self.model.geom_dataid[geom_id] = -1
            self.model.geom_pos[geom_id] = np.asarray(
                [float(center[0]), float(center[1]), z_pos],
                dtype=np.float64,
            )
            self.model.geom_quat[geom_id] = self._yaw_quat(yaw)
            self.model.geom_size[geom_id] = size
            self.model.geom_rbound[geom_id] = float(np.linalg.norm(size))
            self.model.geom_contype[geom_id] = 0
            self.model.geom_conaffinity[geom_id] = 0
            self.model.geom_rgba[geom_id] = visible_rgba

    def _set_hole_cavity_visual_geometry(
        self,
        spec: GeometrySpec,
        center_xy: np.ndarray,
    ) -> None:
        if self.hole_key_tab_cavity_visual_geom_id is not None:
            tab_geom_id = self.hole_key_tab_cavity_visual_geom_id
            self.model.geom_type[tab_geom_id] = self.base_geom_type[tab_geom_id]
            self.model.geom_dataid[tab_geom_id] = self.base_geom_dataid[tab_geom_id]
            self.model.geom_pos[tab_geom_id] = self.base_geom_pos[tab_geom_id]
            self.model.geom_quat[tab_geom_id] = self.base_geom_quat[tab_geom_id]
            self.model.geom_size[tab_geom_id] = self.base_geom_size[tab_geom_id]
            self.model.geom_rbound[tab_geom_id] = max(
                float(self.base_geom_rbound[tab_geom_id]),
                0.002,
            )
            self.model.geom_contype[tab_geom_id] = 0
            self.model.geom_conaffinity[tab_geom_id] = 0
            hidden_rgba = self.base_geom_rgba[tab_geom_id].copy()
            hidden_rgba[3] = 0.0
            self.model.geom_rgba[tab_geom_id] = hidden_rgba

        if self.hole_cavity_visual_geom_id is None:
            return

        geom_id = self.hole_cavity_visual_geom_id
        half_height = max(float(self.base_geom_size[geom_id, 2]), 0.0005)
        pos = self.base_geom_pos[geom_id].copy()
        pos[:2] = center_xy
        self.model.geom_pos[geom_id] = pos
        self.model.geom_quat[geom_id] = np.asarray([1.0, 0.0, 0.0, 0.0], dtype=np.float64)
        self.model.geom_dataid[geom_id] = -1
        self.model.geom_contype[geom_id] = 0
        self.model.geom_conaffinity[geom_id] = 0
        self.model.geom_rgba[geom_id] = self.base_geom_rgba[geom_id]

        if spec.hole_shape == "rectangular_key" and self.geometry_fixture_mode == "true_mesh":
            plate_id = self._geom_id("hole_plate")
            visual_z = (
                float(self.base_geom_pos[plate_id, 2])
                + float(self.base_geom_size[plate_id, 2])
                + half_height
            )
            scale = 0.88
            radius, tab_half_width, tab_length = self._true_fixture_keyhole_dimensions(
                spec.hole_half_size
            )
            radius *= scale
            tab_half_width *= scale
            tab_length *= scale
            x_join = float(np.sqrt(max(radius * radius - tab_half_width * tab_half_width, 0.0)))
            front_x = radius + tab_length

            self.model.geom_type[geom_id] = int(mujoco.mjtGeom.mjGEOM_CYLINDER)
            self.model.geom_dataid[geom_id] = -1
            self.model.geom_pos[geom_id] = np.asarray(
                [
                    float(center_xy[0]),
                    float(center_xy[1]),
                    visual_z,
                ],
                dtype=np.float64,
            )
            self.model.geom_quat[geom_id] = np.asarray([1.0, 0.0, 0.0, 0.0], dtype=np.float64)
            self.model.geom_size[geom_id] = np.asarray(
                [radius, half_height, 0.0],
                dtype=np.float64,
            )
            self.model.geom_rbound[geom_id] = float(np.hypot(radius, half_height))
            self.model.geom_rgba[geom_id] = self.base_geom_rgba[geom_id]

            tab_geom_id = self.hole_key_tab_cavity_visual_geom_id
            if tab_geom_id is not None:
                tab_half_x = max(0.0005, 0.5 * (front_x - x_join))
                tab_center_x = 0.5 * (front_x + x_join)
                self.model.geom_type[tab_geom_id] = int(mujoco.mjtGeom.mjGEOM_BOX)
                self.model.geom_dataid[tab_geom_id] = -1
                self.model.geom_pos[tab_geom_id] = np.asarray(
                    [
                        float(center_xy[0]) + tab_center_x,
                        float(center_xy[1]),
                        visual_z,
                    ],
                    dtype=np.float64,
                )
                self.model.geom_quat[tab_geom_id] = np.asarray(
                    [1.0, 0.0, 0.0, 0.0],
                    dtype=np.float64,
                )
                self.model.geom_size[tab_geom_id] = np.asarray(
                    [tab_half_x, tab_half_width, half_height],
                    dtype=np.float64,
                )
                self.model.geom_rbound[tab_geom_id] = float(
                    np.linalg.norm(self.model.geom_size[tab_geom_id])
                )
                self.model.geom_contype[tab_geom_id] = 0
                self.model.geom_conaffinity[tab_geom_id] = 0
                self.model.geom_rgba[tab_geom_id] = self.base_geom_rgba[geom_id]
            return

        if spec.hole_shape in ("square", "slot", "rectangular_key"):
            if spec.hole_half_extents is None:
                half_x = half_y = float(spec.hole_half_size)
            else:
                half_x, half_y = (float(v) for v in spec.hole_half_extents)
            size = np.asarray(
                [
                    max(0.001, half_x * 0.88),
                    max(0.001, half_y * 0.88),
                    half_height,
                ],
                dtype=np.float64,
            )
            self.model.geom_type[geom_id] = int(mujoco.mjtGeom.mjGEOM_BOX)
            self.model.geom_size[geom_id] = size
            self.model.geom_rbound[geom_id] = float(np.linalg.norm(size))
            return

        if spec.hole_shape == "round":
            radius = max(0.001, float(spec.hole_half_size) * 0.82)
            self.model.geom_type[geom_id] = int(mujoco.mjtGeom.mjGEOM_CYLINDER)
            self.model.geom_size[geom_id] = np.asarray(
                [radius, half_height, 0.0],
                dtype=np.float64,
            )
            self.model.geom_rbound[geom_id] = float(np.hypot(radius, half_height))
            return

        if spec.hole_shape in ("hex", "triangle") or (
            spec.hole_shape == "slot" and self.geometry_fixture_mode == "true_mesh"
        ):
            hidden_rgba = self.base_geom_rgba[geom_id].copy()
            hidden_rgba[3] = 0.0
            self.model.geom_type[geom_id] = int(mujoco.mjtGeom.mjGEOM_BOX)
            self.model.geom_size[geom_id] = np.asarray(
                [0.001, 0.001, half_height],
                dtype=np.float64,
            )
            self.model.geom_rgba[geom_id] = hidden_rgba
            self.model.geom_rbound[geom_id] = float(np.linalg.norm(self.model.geom_size[geom_id]))
            return

    def _set_rectangular_hole_geometry(
        self,
        center_xy: np.ndarray,
        half_extents: tuple[float, float],
    ) -> set[str]:
        center_x, center_y = (float(center_xy[0]), float(center_xy[1]))
        half_x, half_y = (float(half_extents[0]), float(half_extents[1]))
        reference_id = self.hole_wall_geom_ids["hole_north"]
        wall_thickness = float(self.base_geom_size[reference_id, 1])
        used = {"hole_north", "hole_south", "hole_east", "hole_west"}

        self._set_hole_wall_box(
            "hole_north",
            np.asarray([center_x, center_y + half_y + wall_thickness], dtype=np.float64),
            yaw=0.0,
            half_length=half_x + wall_thickness,
        )
        self._set_hole_wall_box(
            "hole_south",
            np.asarray([center_x, center_y - half_y - wall_thickness], dtype=np.float64),
            yaw=0.0,
            half_length=half_x + wall_thickness,
        )
        self._set_hole_wall_box(
            "hole_east",
            np.asarray([center_x + half_x + wall_thickness, center_y], dtype=np.float64),
            yaw=0.5 * np.pi,
            half_length=half_y + wall_thickness,
        )
        self._set_hole_wall_box(
            "hole_west",
            np.asarray([center_x - half_x - wall_thickness, center_y], dtype=np.float64),
            yaw=0.5 * np.pi,
            half_length=half_y + wall_thickness,
        )
        return used

    def _set_polygon_hole_geometry(
        self,
        center_xy: np.ndarray,
        *,
        apothem: float,
        sides: int,
    ) -> set[str]:
        available_names = list(self.hole_wall_geom_ids)
        if sides > len(available_names):
            raise RuntimeError(
                f"{sides}-sided hole requires at least {sides} wall geoms; "
                f"model only provides {len(available_names)}."
            )
        reference_id = self.hole_wall_geom_ids["hole_north"]
        wall_thickness = float(self.base_geom_size[reference_id, 1])
        radius = float(apothem) / np.cos(np.pi / float(sides))
        vertices = []
        for index in range(sides):
            angle = 0.5 * np.pi + np.pi / float(sides) + 2.0 * np.pi * index / float(sides)
            vertices.append(
                np.asarray(
                    [
                        float(center_xy[0]) + radius * np.cos(angle),
                        float(center_xy[1]) + radius * np.sin(angle),
                    ],
                    dtype=np.float64,
                )
            )

        used: set[str] = set()
        for index in range(sides):
            wall_name = available_names[index]
            start = vertices[index]
            end = vertices[(index + 1) % sides]
            edge = end - start
            edge_length = float(np.linalg.norm(edge))
            if edge_length <= 1e-9:
                continue
            outward = np.asarray([edge[1], -edge[0]], dtype=np.float64) / edge_length
            center = 0.5 * (start + end) + outward * wall_thickness
            yaw = float(np.arctan2(edge[1], edge[0]))
            self._set_hole_wall_box(
                wall_name,
                center,
                yaw=yaw,
                half_length=0.5 * edge_length,
            )
            used.add(wall_name)
        return used

    def _set_hole_opening_geometry(
        self,
        spec: GeometrySpec,
        center_xy: np.ndarray,
    ) -> None:
        self._deactivate_hole_polygon_visual_walls()
        self._deactivate_true_fixture_walls()
        self._deactivate_true_fixture_visual()
        self._set_hole_cavity_visual_geometry(spec, center_xy)

        if spec.hole_shape == "square":
            used = self._set_rectangular_hole_geometry(
                center_xy,
                spec.hole_half_extents or (spec.hole_half_size, spec.hole_half_size),
            )
        elif spec.hole_shape == "slot":
            if spec.hole_half_extents is None:
                raise ValueError(f"{spec.hole_shape} hole requires hole_half_extents.")
            if self.geometry_fixture_mode == "true_mesh" and self._set_true_fixture_mesh_geometry(
                spec,
                center_xy,
            ):
                self._set_true_fixture_visual_geometry(spec, center_xy)
                used = set()
            else:
                used = self._set_rectangular_hole_geometry(center_xy, spec.hole_half_extents)
        elif spec.hole_shape == "rectangular_key":
            if spec.hole_half_extents is None:
                raise ValueError(f"{spec.hole_shape} hole requires hole_half_extents.")
            if self.geometry_fixture_mode == "true_mesh" and self._set_true_fixture_mesh_geometry(
                spec,
                center_xy,
            ):
                self._set_true_fixture_visual_geometry(spec, center_xy)
                used = set()
            else:
                used = self._set_rectangular_hole_geometry(center_xy, spec.hole_half_extents)
        elif spec.hole_shape in ("round", "hex", "triangle"):
            sides = spec.hole_polygon_sides
            if sides is None:
                raise ValueError(f"{spec.hole_shape} hole requires hole_polygon_sides.")
            if self.geometry_fixture_mode == "true_mesh" and self._set_true_fixture_mesh_geometry(
                spec,
                center_xy,
            ):
                self._set_true_fixture_visual_geometry(spec, center_xy)
                used = set()
            else:
                used = self._set_polygon_hole_geometry(
                    center_xy,
                    apothem=spec.hole_half_size,
                    sides=sides,
                )
            if spec.hole_shape in ("hex", "triangle") and self.geometry_fixture_mode != "true_mesh":
                self._set_hole_collision_wall_visibility(used, visible=False)
                self._set_hole_polygon_visual_geometry(
                    center_xy,
                    apothem=spec.hole_half_size,
                    sides=sides,
                )
        else:
            raise ValueError(f"unsupported hole shape: {spec.hole_shape}")

        for name in self.hole_wall_geom_ids:
            if name not in used:
                self._deactivate_hole_wall(name)

        site_pos = self.base_site_pos[self.hole_site_id].copy()
        site_pos[:2] = center_xy
        self.model.site_pos[self.hole_site_id] = site_pos

    def _randomize_contact_dynamics(self) -> None:
        self.current_contact_friction_multiplier = float(
            self.np_random.uniform(*self.contact_friction_multiplier_range)
        )
        self.current_contact_solref_time_multiplier = float(
            self.np_random.uniform(*self.contact_solref_time_multiplier_range)
        )
        self.current_contact_solref_damping_multiplier = float(
            self.np_random.uniform(*self.contact_solref_damping_multiplier_range)
        )
        self.current_contact_solimp_width_multiplier = float(
            self.np_random.uniform(*self.contact_solimp_width_multiplier_range)
        )
        sampled_joint_damping_multiplier = float(
            self.np_random.uniform(*self.dynamics_joint_damping_multiplier_range)
        )
        sampled_actuator_kp_multiplier = float(
            self.np_random.uniform(*self.dynamics_actuator_kp_multiplier_range)
        )
        self.current_joint_damping_multiplier = (
            self.nominal_joint_damping_multiplier * sampled_joint_damping_multiplier
        )
        self.current_actuator_kp_multiplier = (
            self.nominal_actuator_kp_multiplier * sampled_actuator_kp_multiplier
        )

        self.model.geom_friction[self.contact_geom_ids] = (
            self.base_geom_friction[self.contact_geom_ids]
            * self.current_contact_friction_multiplier
        )
        self.model.geom_solref[self.contact_geom_ids, 0] = np.clip(
            self.base_geom_solref[self.contact_geom_ids, 0]
            * self.current_contact_solref_time_multiplier,
            0.002,
            0.05,
        )
        self.model.geom_solref[self.contact_geom_ids, 1] = np.clip(
            self.base_geom_solref[self.contact_geom_ids, 1]
            * self.current_contact_solref_damping_multiplier,
            0.2,
            3.0,
        )
        self.model.geom_solimp[self.contact_geom_ids, 2] = np.clip(
            self.base_geom_solimp[self.contact_geom_ids, 2]
            * self.current_contact_solimp_width_multiplier,
            1e-5,
            0.02,
        )
        self._apply_arm_dynamics_multipliers(
            self.current_joint_damping_multiplier,
            self.current_actuator_kp_multiplier,
        )

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

    def _apply_nominal_wrist_camera_pose(self) -> None:
        self.model.cam_pos[self.wrist_camera_id] = (
            self.model.cam_pos[self.wrist_camera_id] + self.wrist_camera_pos_offset
        )
        if np.any(np.abs(self.wrist_camera_rot_offset_rad) > 0.0):
            base_quat = self.model.cam_quat[self.wrist_camera_id].copy()
            delta_quat = self._euler_xyz_to_quat(self.wrist_camera_rot_offset_rad)
            camera_quat = self._quat_multiply(base_quat, delta_quat)
            self.model.cam_quat[self.wrist_camera_id] = camera_quat / np.linalg.norm(camera_quat)
        if self.wrist_camera_fovy is not None:
            self.model.cam_fovy[self.wrist_camera_id] = self.wrist_camera_fovy

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

    def _site_xmat(self, data: mujoco.MjData, site_id: int) -> np.ndarray:
        return data.site_xmat[site_id].reshape(3, 3).copy()

    def _body_xmat(self, data: mujoco.MjData, body_id: int) -> np.ndarray:
        return data.xmat[body_id].reshape(3, 3).copy()

    def _compute_rest_site_xmat(self, site_id: int) -> np.ndarray:
        data = self.ik_data
        data.qpos[:] = self.data.qpos
        data.qvel[:] = 0.0
        data.mocap_pos[:] = self.data.mocap_pos
        data.mocap_quat[:] = self.data.mocap_quat
        data.qpos[self.arm_qpos_ids] = self.rest_qpos
        mujoco.mj_forward(self.model, data)
        return self._site_xmat(data, site_id)

    def _rotation_error(self, current_xmat: np.ndarray, target_xmat: np.ndarray) -> np.ndarray:
        return 0.5 * (
            np.cross(current_xmat[:, 0], target_xmat[:, 0])
            + np.cross(current_xmat[:, 1], target_xmat[:, 1])
            + np.cross(current_xmat[:, 2], target_xmat[:, 2])
        )

    def _current_pose_ik_orientation_error(self, data: mujoco.MjData) -> float:
        current_xmat = self._site_xmat(data, self.peg_tip_site_id)
        return float(np.linalg.norm(self._rotation_error(current_xmat, self.pose_ik_target_xmat)))

    def _peg_axis_and_tilt(self, data: mujoco.MjData) -> tuple[np.ndarray, float]:
        xmat = self._site_xmat(data, self.peg_tip_site_id)
        axis = xmat @ np.asarray([0.0, 0.0, -1.0], dtype=np.float64)
        axis_norm = float(np.linalg.norm(axis))
        if axis_norm > 1e-9:
            axis = axis / axis_norm
        vertical_down = np.asarray([0.0, 0.0, -1.0], dtype=np.float64)
        cosine = float(np.clip(np.dot(axis, vertical_down), -1.0, 1.0))
        tilt_deg = float(np.rad2deg(np.arccos(cosine)))
        return axis.astype(np.float64), tilt_deg

    @staticmethod
    def _project_unit_xy(vector: np.ndarray) -> np.ndarray | None:
        projected = np.asarray([vector[0], vector[1], 0.0], dtype=np.float64)
        norm = float(np.linalg.norm(projected))
        if norm <= 1e-9:
            return None
        return projected / norm

    @staticmethod
    def _signed_planar_angle_deg(reference: np.ndarray, vector: np.ndarray) -> float:
        cross_z = float(reference[0] * vector[1] - reference[1] * vector[0])
        dot = float(np.clip(np.dot(reference, vector), -1.0, 1.0))
        return float(np.rad2deg(np.arctan2(cross_z, dot)))

    @staticmethod
    def _square_symmetry_yaw_error_deg(raw_yaw_deg: float) -> float:
        return float(abs(((raw_yaw_deg + 45.0) % 90.0) - 45.0))

    @staticmethod
    def _fold_shape_yaw_signed_error_deg(raw_yaw_deg: float, period_deg: float) -> float:
        return float(((raw_yaw_deg + 0.5 * period_deg) % period_deg) - 0.5 * period_deg)

    def _shape_yaw_period_deg(self) -> float:
        period = SHAPE_YAW_PERIOD_DEG.get(self.current_geometry_spec.name)
        return float(period) if period is not None else float("nan")

    def _square_symmetry_yaw_metrics(self, xmat: np.ndarray) -> tuple[float, float]:
        spec = self.current_geometry_spec
        if spec.peg_shape != "square" or spec.hole_shape != "square":
            return float("nan"), float("nan")
        x_axis = np.asarray(xmat, dtype=np.float64).reshape(3, 3) @ np.asarray(
            [1.0, 0.0, 0.0],
            dtype=np.float64,
        )
        hole_xmat = self._body_xmat(self.data, self.hole_body_id)
        hole_x_axis = hole_xmat @ np.asarray([1.0, 0.0, 0.0], dtype=np.float64)
        x_xy = self._project_unit_xy(x_axis)
        hole_x_xy = self._project_unit_xy(hole_x_axis)
        if x_xy is None or hole_x_xy is None:
            return float("nan"), float("nan")
        raw_yaw_deg = self._signed_planar_angle_deg(hole_x_xy, x_xy)
        return raw_yaw_deg, self._square_symmetry_yaw_error_deg(raw_yaw_deg)

    def _shape_yaw_metrics_for_xmat(self, xmat: np.ndarray) -> tuple[float, float]:
        period_deg = self._shape_yaw_period_deg()
        if not np.isfinite(period_deg) or period_deg <= 0.0:
            return float("nan"), float("nan")
        x_axis = np.asarray(xmat, dtype=np.float64).reshape(3, 3) @ np.asarray(
            [1.0, 0.0, 0.0],
            dtype=np.float64,
        )
        hole_xmat = self._body_xmat(self.data, self.hole_body_id)
        hole_x_axis = hole_xmat @ np.asarray([1.0, 0.0, 0.0], dtype=np.float64)
        x_xy = self._project_unit_xy(x_axis)
        hole_x_xy = self._project_unit_xy(hole_x_axis)
        if x_xy is None or hole_x_xy is None:
            return float("nan"), float("nan")
        raw_yaw_deg = self._signed_planar_angle_deg(hole_x_xy, x_xy)
        signed_error_deg = self._fold_shape_yaw_signed_error_deg(
            raw_yaw_deg,
            period_deg,
        )
        return raw_yaw_deg, abs(signed_error_deg)

    def _shape_yaw_metrics(self, data: mujoco.MjData) -> dict[str, float]:
        period_deg = self._shape_yaw_period_deg()
        if not np.isfinite(period_deg) or period_deg <= 0.0:
            return {
                "shape_yaw_period_deg": np.nan,
                "shape_yaw_symmetry_order": np.nan,
                "shape_yaw_raw_deg": np.nan,
                "shape_yaw_signed_error_deg": np.nan,
                "shape_yaw_error_deg": np.nan,
                "shape_yaw_label_sin": np.nan,
                "shape_yaw_label_cos": np.nan,
            }

        peg_xmat = self._site_xmat(data, self.peg_tip_site_id)
        hole_xmat = self._body_xmat(data, self.hole_body_id)
        peg_x_axis = peg_xmat @ np.asarray([1.0, 0.0, 0.0], dtype=np.float64)
        hole_x_axis = hole_xmat @ np.asarray([1.0, 0.0, 0.0], dtype=np.float64)
        peg_x_xy = self._project_unit_xy(peg_x_axis)
        hole_x_xy = self._project_unit_xy(hole_x_axis)
        if peg_x_xy is None or hole_x_xy is None:
            raw_yaw_deg = np.nan
            signed_error_deg = np.nan
            phase = np.nan
        else:
            raw_yaw_deg = self._signed_planar_angle_deg(hole_x_xy, peg_x_xy)
            signed_error_deg = self._fold_shape_yaw_signed_error_deg(
                raw_yaw_deg,
                period_deg,
            )
            phase = float(2.0 * np.pi * signed_error_deg / period_deg)

        return {
            "shape_yaw_period_deg": float(period_deg),
            "shape_yaw_symmetry_order": float(360.0 / period_deg),
            "shape_yaw_raw_deg": float(raw_yaw_deg),
            "shape_yaw_signed_error_deg": float(signed_error_deg),
            "shape_yaw_error_deg": float(abs(signed_error_deg)),
            "shape_yaw_label_sin": float(np.sin(phase)) if np.isfinite(phase) else np.nan,
            "shape_yaw_label_cos": float(np.cos(phase)) if np.isfinite(phase) else np.nan,
        }

    def _shape_yaw_clearance(self) -> float:
        spec = self.current_geometry_spec
        if spec.name == "hex_hex":
            peg_apothem = float(self.base_peg_radius) * float(np.cos(np.pi / 6.0))
            return float(spec.hole_half_size - peg_apothem)
        if spec.name == "triangle_triangle":
            peg_apothem = float(self.base_peg_radius) * float(np.cos(np.pi / 3.0))
            return float(spec.hole_half_size - peg_apothem)
        if spec.name == "square_square" and spec.peg_half_extents is not None:
            peg_half_width = max(float(spec.peg_half_extents[0]), float(spec.peg_half_extents[1]))
            return float(spec.hole_half_size - peg_half_width)
        if spec.name == "rectangular_key":
            radius, tab_half_width, tab_length = self._true_fixture_keyhole_dimensions(
                spec.hole_half_size
            )
            radial_clearance = radius - float(spec.peg_radius)
            tab_width_clearance = tab_half_width - TIGHT_YAW_KEYHOLE_PEG_TAB_HALF_WIDTH
            tab_length_clearance = tab_length - TIGHT_YAW_KEYHOLE_PEG_TAB_LENGTH
            return float(min(radial_clearance, tab_width_clearance, tab_length_clearance))
        return float(spec.hole_clearance)

    def _square_peg_orientation_metrics(self, data: mujoco.MjData) -> dict[str, float]:
        spec = self.current_geometry_spec
        if spec.peg_shape not in ("square", "slot", "rectangular_key") or spec.peg_half_extents is None:
            return {
                "square_peg_raw_yaw_deg": np.nan,
                "square_peg_yaw_error_deg": np.nan,
                "square_peg_topdown_half_width_x": np.nan,
                "square_peg_topdown_half_width_y": np.nan,
                "square_peg_topdown_max_half_width": np.nan,
                "square_peg_topdown_clearance_margin": np.nan,
                "square_peg_tilt_lateral_extent_x": np.nan,
                "square_peg_tilt_lateral_extent_y": np.nan,
                "square_peg_tilt_lateral_extent_max": np.nan,
                "square_peg_tilted_half_width_x": np.nan,
                "square_peg_tilted_half_width_y": np.nan,
                "square_peg_tilted_max_half_width": np.nan,
                "square_peg_tilted_clearance_margin": np.nan,
            }

        peg_xmat = self._site_xmat(data, self.peg_tip_site_id)
        hole_xmat = self._body_xmat(data, self.hole_body_id)

        peg_x_axis = peg_xmat @ np.asarray([1.0, 0.0, 0.0], dtype=np.float64)
        peg_y_axis = peg_xmat @ np.asarray([0.0, 1.0, 0.0], dtype=np.float64)
        peg_down_axis = peg_xmat @ np.asarray([0.0, 0.0, -1.0], dtype=np.float64)
        hole_x_axis = hole_xmat @ np.asarray([1.0, 0.0, 0.0], dtype=np.float64)
        hole_y_axis = hole_xmat @ np.asarray([0.0, 1.0, 0.0], dtype=np.float64)

        peg_x_xy = self._project_unit_xy(peg_x_axis)
        hole_x_xy = self._project_unit_xy(hole_x_axis)
        if peg_x_xy is None or hole_x_xy is None:
            raw_yaw_deg = np.nan
            yaw_error_deg = np.nan
        else:
            raw_yaw_deg = self._signed_planar_angle_deg(hole_x_xy, peg_x_xy)
            yaw_error_deg = self._square_symmetry_yaw_error_deg(raw_yaw_deg)

        hx, hy, hz = (float(v) for v in spec.peg_half_extents)
        topdown_half_width_x = hx * abs(float(np.dot(peg_x_axis, hole_x_axis))) + hy * abs(
            float(np.dot(peg_y_axis, hole_x_axis))
        )
        topdown_half_width_y = hx * abs(float(np.dot(peg_x_axis, hole_y_axis))) + hy * abs(
            float(np.dot(peg_y_axis, hole_y_axis))
        )
        topdown_max_half_width = max(topdown_half_width_x, topdown_half_width_y)

        tilt_lateral_extent_x = hz * abs(float(np.dot(peg_down_axis, hole_x_axis)))
        tilt_lateral_extent_y = hz * abs(float(np.dot(peg_down_axis, hole_y_axis)))
        tilt_lateral_extent_max = max(tilt_lateral_extent_x, tilt_lateral_extent_y)

        tilted_half_width_x = topdown_half_width_x + tilt_lateral_extent_x
        tilted_half_width_y = topdown_half_width_y + tilt_lateral_extent_y
        tilted_max_half_width = max(tilted_half_width_x, tilted_half_width_y)

        return {
            "square_peg_raw_yaw_deg": float(raw_yaw_deg),
            "square_peg_yaw_error_deg": float(yaw_error_deg),
            "square_peg_topdown_half_width_x": float(topdown_half_width_x),
            "square_peg_topdown_half_width_y": float(topdown_half_width_y),
            "square_peg_topdown_max_half_width": float(topdown_max_half_width),
            "square_peg_topdown_clearance_margin": float(
                spec.hole_half_size - topdown_max_half_width
            ),
            "square_peg_tilt_lateral_extent_x": float(tilt_lateral_extent_x),
            "square_peg_tilt_lateral_extent_y": float(tilt_lateral_extent_y),
            "square_peg_tilt_lateral_extent_max": float(tilt_lateral_extent_max),
            "square_peg_tilted_half_width_x": float(tilted_half_width_x),
            "square_peg_tilted_half_width_y": float(tilted_half_width_y),
            "square_peg_tilted_max_half_width": float(tilted_max_half_width),
            "square_peg_tilted_clearance_margin": float(
                spec.hole_half_size - tilted_max_half_width
            ),
        }

    def _joint_limit_metrics(self, qpos: np.ndarray) -> tuple[float, float]:
        lower = self.joint_ranges[:, 0]
        upper = self.joint_ranges[:, 1]
        span = np.maximum(upper - lower, 1e-9)
        margin = np.minimum(qpos - lower, upper - qpos)
        normalized_margin = margin / span
        return float(np.min(margin)), float(np.min(normalized_margin))

    def _solve_ik_with_diagnostics(
        self,
        target_pos: np.ndarray,
    ) -> tuple[np.ndarray, np.ndarray, float, int]:
        if self.ik_control_mode == "pose":
            return self._solve_pose_ik_with_diagnostics(target_pos)
        if self.ik_control_mode == "pose_tip_priority":
            return self._solve_tip_priority_pose_ik_with_diagnostics(target_pos)
        return self._solve_position_ik_with_diagnostics(target_pos)

    def _solve_position_ik(self, target_pos: np.ndarray) -> np.ndarray:
        q, _, _, _ = self._solve_ik_with_diagnostics(target_pos)
        return q

    def _solve_position_ik_with_diagnostics(
        self,
        target_pos: np.ndarray,
    ) -> tuple[np.ndarray, np.ndarray, float, int]:
        data = self.ik_data
        data.qpos[:] = self.data.qpos
        data.qvel[:] = 0.0
        data.mocap_pos[:] = self.data.mocap_pos
        data.mocap_quat[:] = self.data.mocap_quat

        q = data.qpos[self.arm_qpos_ids].copy()
        q[self.ik_joint_count :] = self.rest_qpos[self.ik_joint_count :]

        ik_dof_ids = self.arm_dof_ids[: self.ik_joint_count]
        lower = self.joint_ranges[: self.ik_joint_count, 0]
        upper = self.joint_ranges[: self.ik_joint_count, 1]

        jacp = np.zeros((3, self.model.nv), dtype=np.float64)
        jacr = np.zeros((3, self.model.nv), dtype=np.float64)
        damping = 1e-3
        iterations = 0

        for iteration in range(18):
            iterations = iteration + 1
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

            q[: self.ik_joint_count] = np.clip(
                q[: self.ik_joint_count] + dq,
                lower,
                upper,
            )

        q[self.ik_joint_count :] = self.rest_qpos[self.ik_joint_count :]
        data.qpos[self.arm_qpos_ids] = q
        mujoco.mj_forward(self.model, data)
        achieved_tip = data.site_xpos[self.peg_tip_site_id].copy()
        target_pos = np.asarray(target_pos, dtype=np.float64).reshape(3)
        error = float(np.linalg.norm(target_pos - achieved_tip))
        return q, achieved_tip, error, iterations

    def _solve_pose_ik_with_diagnostics(
        self,
        target_pos: np.ndarray,
    ) -> tuple[np.ndarray, np.ndarray, float, int]:
        data = self.ik_data
        data.qpos[:] = self.data.qpos
        data.qvel[:] = 0.0
        data.mocap_pos[:] = self.data.mocap_pos
        data.mocap_quat[:] = self.data.mocap_quat

        q = data.qpos[self.arm_qpos_ids].copy()
        q_reference = q.copy()
        continuity_weights = self._ik_continuity_weights()
        wrist_posture_weights = self._ik_wrist_posture_weights()
        wrist_anchor_qpos = self._ik_wrist_anchor_full_qpos()
        ik_dof_ids = self.arm_dof_ids
        lower = self.joint_ranges[:, 0]
        upper = self.joint_ranges[:, 1]
        target_pos = np.asarray(target_pos, dtype=np.float64).reshape(3)

        jacp = np.zeros((3, self.model.nv), dtype=np.float64)
        jacr = np.zeros((3, self.model.nv), dtype=np.float64)
        damping = 1e-4
        iterations = 0

        for iteration in range(self.ik_max_iterations):
            iterations = iteration + 1
            data.qpos[self.arm_qpos_ids] = q
            mujoco.mj_forward(self.model, data)

            pos_error = target_pos - data.site_xpos[self.peg_tip_site_id]
            current_xmat = self._site_xmat(data, self.peg_tip_site_id)
            rot_error = self._rotation_error(current_xmat, self.pose_ik_target_xmat)
            if np.linalg.norm(pos_error) < 1e-4 and np.linalg.norm(rot_error) < 2e-3:
                break

            mujoco.mj_jacSite(self.model, data, jacp, jacr, self.peg_tip_site_id)
            jpos = jacp[:, ik_dof_ids]
            jrot = jacr[:, ik_dof_ids]
            jtask = np.vstack(
                [
                    jpos,
                    self.ik_orientation_weight * jrot,
                ]
            )
            task_error = np.concatenate(
                [
                    pos_error,
                    self.ik_orientation_weight * rot_error,
                ]
            )

            lhs = jtask.T @ jtask + damping * np.eye(len(ik_dof_ids), dtype=np.float64)
            rhs = jtask.T @ task_error
            if self.ik_posture_weight > 0.0:
                lhs += self.ik_posture_weight * np.eye(len(ik_dof_ids), dtype=np.float64)
                rhs += self.ik_posture_weight * (self.rest_qpos - q)
            if np.any(wrist_posture_weights > 0.0):
                lhs += np.diag(wrist_posture_weights)
                rhs += wrist_posture_weights * (self.rest_qpos - q)
            if wrist_anchor_qpos is not None:
                wrist_anchor_weights = np.zeros_like(q)
                wrist_anchor_weights[3:] = self.ik_wrist_anchor_weight
                lhs += np.diag(wrist_anchor_weights)
                rhs += wrist_anchor_weights * (wrist_anchor_qpos - q)
            if np.any(continuity_weights > 0.0):
                lhs += np.diag(continuity_weights)
                rhs += continuity_weights * (q_reference - q)

            try:
                dq = np.linalg.solve(lhs, rhs)
            except np.linalg.LinAlgError:
                dq = np.linalg.lstsq(lhs, rhs, rcond=None)[0]
            dq = np.clip(dq, -self.ik_step_limit, self.ik_step_limit)
            q = np.clip(q + dq, lower, upper)

        data.qpos[self.arm_qpos_ids] = q
        mujoco.mj_forward(self.model, data)
        achieved_tip = data.site_xpos[self.peg_tip_site_id].copy()
        error = float(np.linalg.norm(target_pos - achieved_tip))
        return q, achieved_tip, error, iterations

    def _solve_tip_priority_pose_ik_with_diagnostics(
        self,
        target_pos: np.ndarray,
    ) -> tuple[np.ndarray, np.ndarray, float, int]:
        data = self.ik_data
        data.qpos[:] = self.data.qpos
        data.qvel[:] = 0.0
        data.mocap_pos[:] = self.data.mocap_pos
        data.mocap_quat[:] = self.data.mocap_quat

        q = data.qpos[self.arm_qpos_ids].copy()
        q_reference = q.copy()
        continuity_weights = self._ik_continuity_weights()
        wrist_posture_weights = self._ik_wrist_posture_weights()
        wrist_anchor_qpos = self._ik_wrist_anchor_full_qpos()
        ik_dof_ids = self.arm_dof_ids
        lower = self.joint_ranges[:, 0]
        upper = self.joint_ranges[:, 1]
        target_pos = np.asarray(target_pos, dtype=np.float64).reshape(3)

        jacp = np.zeros((3, self.model.nv), dtype=np.float64)
        jacr = np.zeros((3, self.model.nv), dtype=np.float64)
        pos_damping = 1e-5
        rot_damping = 1e-4
        iterations = 0

        for iteration in range(self.ik_max_iterations):
            iterations = iteration + 1
            data.qpos[self.arm_qpos_ids] = q
            mujoco.mj_forward(self.model, data)

            pos_error = target_pos - data.site_xpos[self.peg_tip_site_id]
            current_xmat = self._site_xmat(data, self.peg_tip_site_id)
            rot_error = self._rotation_error(current_xmat, self.pose_ik_target_xmat)
            if np.linalg.norm(pos_error) < 1e-4 and np.linalg.norm(rot_error) < 2e-3:
                break

            mujoco.mj_jacSite(self.model, data, jacp, jacr, self.peg_tip_site_id)
            jpos = jacp[:, ik_dof_ids]
            jrot = jacr[:, ik_dof_ids]

            pos_lhs = jpos @ jpos.T + pos_damping * np.eye(3, dtype=np.float64)
            try:
                jpos_pinv = jpos.T @ np.linalg.inv(pos_lhs)
                dq_pos = jpos_pinv @ pos_error
            except np.linalg.LinAlgError:
                jpos_pinv = np.linalg.pinv(jpos)
                dq_pos = jpos_pinv @ pos_error

            identity = np.eye(len(ik_dof_ids), dtype=np.float64)
            nullspace = identity - jpos_pinv @ jpos
            dq_rot = np.zeros_like(q)
            if self.ik_orientation_weight > 0.0:
                jrot_null = jrot @ nullspace
                rot_lhs = jrot_null @ jrot_null.T + rot_damping * np.eye(
                    3,
                    dtype=np.float64,
                )
                try:
                    rot_step = jrot_null.T @ np.linalg.solve(rot_lhs, rot_error)
                except np.linalg.LinAlgError:
                    rot_step = np.linalg.lstsq(jrot_null, rot_error, rcond=None)[0]
                dq_rot = (
                    self.ik_orientation_weight
                    * nullspace
                    @ np.asarray(rot_step, dtype=np.float64)
                )

            dq_posture = np.zeros_like(q)
            if self.ik_posture_weight > 0.0:
                dq_posture = (
                    self.ik_posture_weight
                    * nullspace
                    @ (self.rest_qpos - q)
                )
            if np.any(wrist_posture_weights > 0.0):
                dq_posture += nullspace @ (wrist_posture_weights * (self.rest_qpos - q))
            if wrist_anchor_qpos is not None:
                wrist_anchor_weights = np.zeros_like(q)
                wrist_anchor_weights[3:] = self.ik_wrist_anchor_weight
                dq_posture += nullspace @ (wrist_anchor_weights * (wrist_anchor_qpos - q))

            dq_continuity = np.zeros_like(q)
            if np.any(continuity_weights > 0.0):
                dq_continuity = nullspace @ (continuity_weights * (q_reference - q))

            dq = dq_pos + dq_rot + dq_posture + dq_continuity
            dq = np.clip(dq, -self.ik_step_limit, self.ik_step_limit)
            q = np.clip(q + dq, lower, upper)

        data.qpos[self.arm_qpos_ids] = q
        mujoco.mj_forward(self.model, data)
        achieved_tip = data.site_xpos[self.peg_tip_site_id].copy()
        error = float(np.linalg.norm(target_pos - achieved_tip))
        return q, achieved_tip, error, iterations

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

    def _success_shape_yaw_terms(self) -> tuple[bool, bool, float, float]:
        tolerance = self.success_shape_yaw_tolerance_deg
        required = bool(
            tolerance is not None
            and self.current_geometry_spec.name in self.success_shape_yaw_profile_set
        )
        if not required:
            return False, True, float("nan"), float("nan")

        yaw_metrics = self._shape_yaw_metrics(self.data)
        yaw_error_deg = float(yaw_metrics.get("shape_yaw_error_deg", np.nan))
        yaw_ok = bool(np.isfinite(yaw_error_deg) and yaw_error_deg <= float(tolerance))
        return True, yaw_ok, yaw_error_deg, float(tolerance)

    def _compute_reward(self, collision: bool, action: np.ndarray | None = None) -> RewardTerms:
        tip_pos = self._site_xpos(self.data, self.peg_tip_site_id)
        shaped_distance, desired_z = self._staged_distance()
        progress = self.previous_shaped_distance - shaped_distance

        dist_xy = float(np.linalg.norm(tip_pos[:2] - self.target_pos[:2]))
        dist_z = float(abs(tip_pos[2] - self.target_pos[2]))
        (
            success_shape_yaw_required,
            success_shape_yaw_ok,
            success_shape_yaw_error_deg,
            success_shape_yaw_tolerance_deg,
        ) = self._success_shape_yaw_terms()
        desired_tip_pos = np.asarray(
            [self.target_pos[0], self.target_pos[1], desired_z],
            dtype=np.float64,
        )
        desired_delta = desired_tip_pos - tip_pos
        desired_delta_norm = float(np.linalg.norm(desired_delta))
        inserted = bool(
            dist_xy < self.success_xy_tolerance
            and dist_z < self.success_z_tolerance
            and success_shape_yaw_ok
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
            success_shape_yaw_required=success_shape_yaw_required,
            success_shape_yaw_ok=success_shape_yaw_ok,
            success_shape_yaw_error_deg=success_shape_yaw_error_deg,
            success_shape_yaw_tolerance_deg=success_shape_yaw_tolerance_deg,
        )

    def _check_collision(self) -> bool:
        return bool(self._collision_contact_pairs())

    def _collision_contact_pairs(self) -> list[str]:
        tip_pos = self._site_xpos(self.data, self.peg_tip_site_id)
        dist_xy = np.linalg.norm(tip_pos[:2] - self.target_pos[:2])
        insertion_clearance_xy = max(
            0.02,
            self.current_hole_half_size - self.current_peg_radius + 0.005,
        )
        close_to_hole = (
            dist_xy < insertion_clearance_xy
            and abs(tip_pos[2] - self.target_pos[2]) < 0.15
        )
        if close_to_hole:
            return []

        pairs: list[str] = []
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
                pairs.append(f"{geom1}:{geom2}")
        return pairs

    def _peg_hole_contact_metrics(self) -> dict[str, Any]:
        wall_names = tuple(self.hole_wall_geom_ids)
        contact_names = ("hole_plate", *wall_names)
        counts = {name: 0 for name in contact_names}
        pairs: list[str] = []
        dists: list[float] = []

        for contact_index in range(self.data.ncon):
            contact = self.data.contact[contact_index]
            geom1 = self._geom_name(contact.geom1)
            geom2 = self._geom_name(contact.geom2)
            if geom1 == "peg_geom":
                other = geom2
            elif geom2 == "peg_geom":
                other = geom1
            else:
                continue

            if other not in counts:
                continue
            counts[other] += 1
            pairs.append(f"peg_geom:{other}")
            dists.append(float(contact.dist))

        wall_count = sum(counts[name] for name in wall_names)
        plate_count = counts["hole_plate"]
        contact_count = wall_count + plate_count
        metrics = {
            "peg_hole_contact_count": contact_count,
            "peg_hole_contact_pairs": ";".join(pairs[:8]),
            "peg_hole_contact_wall_count": wall_count,
            "peg_hole_contact_plate_count": plate_count,
            "peg_hole_contact_has_wall": wall_count > 0,
            "peg_hole_contact_has_plate": plate_count > 0,
            "peg_hole_contact_hole_plate": plate_count,
            "peg_hole_contact_hole_north": counts["hole_north"],
            "peg_hole_contact_hole_south": counts["hole_south"],
            "peg_hole_contact_hole_east": counts["hole_east"],
            "peg_hole_contact_hole_west": counts["hole_west"],
            "peg_hole_contact_hole_aux_total": sum(
                counts[name] for name in wall_names if name.startswith("hole_aux_")
            ),
            "peg_hole_contact_min_dist": min(dists) if dists else np.nan,
            "peg_hole_contact_max_dist": max(dists) if dists else np.nan,
        }
        return metrics

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
        obs = {"cam_image": self._stack_observation_value(self.gray_frame_buffer, gray)}
        if self.include_near_hole_crop:
            crop = self._center_crop_gray(gray)
            obs["near_hole_crop"] = self._stack_observation_value(
                self.near_hole_crop_buffer,
                crop,
            )
        if self.include_control_state:
            control_state = self._get_control_state_obs()
            obs["control_state"] = self._stack_control_state(control_state)
        return obs

    def _clear_observation_history(self) -> None:
        self.gray_frame_buffer = []
        self.near_hole_crop_buffer = []
        self.control_state_buffer = []

    def _stack_observation_value(
        self,
        buffer: list[np.ndarray],
        value: np.ndarray,
    ) -> np.ndarray:
        value = value.astype(np.uint8, copy=True)
        if not buffer:
            buffer.extend(value.copy() for _ in range(self.image_frame_stack))
        else:
            buffer.append(value.copy())
            del buffer[: max(0, len(buffer) - self.image_frame_stack)]
        return np.stack(buffer, axis=-1).astype(np.uint8, copy=False)

    def _stack_control_state(self, control_state: np.ndarray) -> np.ndarray:
        value = control_state.astype(np.float32, copy=True)
        if not self.control_state_buffer:
            self.control_state_buffer.extend(value.copy() for _ in range(self.image_frame_stack))
        else:
            self.control_state_buffer.append(value.copy())
            del self.control_state_buffer[: max(0, len(self.control_state_buffer) - self.image_frame_stack)]
        return np.concatenate(self.control_state_buffer, axis=0).astype(np.float32, copy=False)

    def _get_control_state_obs(self) -> np.ndarray:
        scale = max(self.action_scale, 1e-9)
        commanded = self.last_commanded_action / scale
        actual_delta = self.last_actual_tip_delta / scale
        tracking_error = (self.last_commanded_action - self.last_actual_tip_delta) / scale
        step_fraction = np.asarray(
            [self.step_count / max(float(self.max_steps), 1.0)],
            dtype=np.float64,
        )
        return np.concatenate(
            [commanded, actual_delta, tracking_error, step_fraction],
        ).astype(np.float32)

    def _center_crop_gray(self, gray: np.ndarray) -> np.ndarray:
        if self.near_hole_crop_size <= 0:
            raise ValueError("near_hole_crop_size must be positive.")
        if self.current_near_hole_crop_source_size <= 0:
            raise ValueError("near_hole_crop_source_size must be positive.")
        height, width = gray.shape[:2]
        crop_source_size = min(self.current_near_hole_crop_source_size, height, width)
        crop_output_size = self.near_hole_crop_size
        offset_x, offset_y = self.near_hole_crop_offset
        x0 = int(
            np.clip(
                (width - crop_source_size) // 2 + offset_x,
                0,
                width - crop_source_size,
            )
        )
        y0 = int(
            np.clip(
                (height - crop_source_size) // 2 + offset_y,
                0,
                height - crop_source_size,
            )
        )
        crop = gray[y0 : y0 + crop_source_size, x0 : x0 + crop_source_size]
        if crop.shape == (crop_output_size, crop_output_size):
            return crop

        y_idx = np.linspace(0, crop.shape[0] - 1, crop_output_size).round().astype(np.int64)
        x_idx = np.linspace(0, crop.shape[1] - 1, crop_output_size).round().astype(np.int64)
        return crop[y_idx][:, x_idx]

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
        eef_pos = self._site_xpos(self.data, self.eef_site_id)
        tool0_pos = self.data.xpos[self.tool0_body_id].copy()
        base_pos = self.data.xpos[self.base_body_id].copy()
        collision_contact_pairs = self._collision_contact_pairs()
        peg_hole_contact_metrics = self._peg_hole_contact_metrics()
        joint_qpos = self.data.qpos[self.arm_qpos_ids].copy()
        joint_limit_margin, joint_limit_normalized_margin = self._joint_limit_metrics(joint_qpos)
        peg_axis_world, peg_tilt_angle_deg = self._peg_axis_and_tilt(self.data)
        square_peg_metrics = self._square_peg_orientation_metrics(self.data)
        shape_yaw_metrics = self._shape_yaw_metrics(self.data)
        (
            pose_ik_target_raw_yaw_deg,
            pose_ik_target_square_yaw_error_deg,
        ) = self._square_symmetry_yaw_metrics(self.pose_ik_target_xmat)
        return {
            "insertion_success": terms.inserted,
            "dist_xy": terms.dist_xy,
            "dist_z": terms.dist_z,
            "success_shape_yaw_required": terms.success_shape_yaw_required,
            "success_shape_yaw_ok": terms.success_shape_yaw_ok,
            "success_shape_yaw_error_deg": terms.success_shape_yaw_error_deg,
            "success_shape_yaw_tolerance_deg": terms.success_shape_yaw_tolerance_deg,
            "shaped_distance": terms.shaped_distance,
            "desired_z": terms.desired_z,
            "collision": terms.collision,
            "collision_contact_count": len(collision_contact_pairs),
            "collision_contact_pairs": ";".join(collision_contact_pairs[:8]),
            **peg_hole_contact_metrics,
            "target_pos": self.target_pos.astype(np.float32),
            "peg_tip_pos": tip_pos.astype(np.float32),
            "eef_pos": eef_pos.astype(np.float32),
            "tool0_pos": tool0_pos.astype(np.float32),
            "base_pos": base_pos.astype(np.float32),
            "peg_tip_to_eef": (tip_pos - eef_pos).astype(np.float32),
            "peg_tip_to_tool0": (tip_pos - tool0_pos).astype(np.float32),
            "step_count": self.step_count,
            "commanded_action": self.last_commanded_action.astype(np.float32),
            "applied_action": self.last_applied_action.astype(np.float32),
            "action_tip_pos_before": self.last_tip_pos_before_action.astype(np.float32),
            "action_target_tip_pos": self.last_target_tip_pos.astype(np.float32),
            "action_target_tip_delta": self.last_target_tip_delta.astype(np.float32),
            "action_actual_tip_delta": self.last_actual_tip_delta.astype(np.float32),
            "action_tip_delta_error": self.last_tip_delta_error.astype(np.float32),
            "action_tracking_error": self.last_action_tracking_error,
            "ik_tip_pos": self.last_ik_tip_pos.astype(np.float32),
            "ik_target_error": self.last_ik_target_error,
            "ik_orientation_error": self.last_ik_orientation_error,
            "pose_ik_target_raw_yaw_deg": pose_ik_target_raw_yaw_deg,
            "pose_ik_target_square_yaw_error_deg": pose_ik_target_square_yaw_error_deg,
            "ik_iterations": self.last_ik_iterations,
            "ik_control_mode": self.ik_control_mode,
            "ik_orientation_weight": self.ik_orientation_weight,
            "ik_posture_weight": self.ik_posture_weight,
            "ik_wrist_posture_weight": self.ik_wrist_posture_weight,
            "ik_wrist_anchor_weight": self.ik_wrist_anchor_weight,
            "ik_wrist_anchor_active": bool(self.ik_wrist_anchor_qpos is not None),
            "ik_continuity_weight": self.ik_continuity_weight,
            "ik_wrist_continuity_weight": self.ik_wrist_continuity_weight,
            "ik_max_wrist_target_delta_deg": (
                np.nan
                if self.ik_max_wrist_target_delta_rad is None
                else float(np.rad2deg(self.ik_max_wrist_target_delta_rad))
            ),
            "ik_nearest_wrist_target_equivalent": bool(
                self.ik_nearest_wrist_target_equivalent
            ),
            "ik_wrist_target_clipped": self.last_ik_wrist_target_clipped,
            "ik_joint_count": self.ik_joint_count,
            "peg_axis_world": peg_axis_world.astype(np.float32),
            "peg_tilt_angle_deg": peg_tilt_angle_deg,
            "joint_limit_min_margin": joint_limit_margin,
            "joint_limit_min_normalized_margin": joint_limit_normalized_margin,
            "joint_qpos_before_action": self.last_joint_qpos_before_action.astype(np.float32),
            "joint_target_qpos": self.last_joint_target_qpos.astype(np.float32),
            "joint_qpos_after_action": self.last_joint_qpos_after_action.astype(np.float32),
            "joint_target_error": self.last_joint_target_error,
            "control_action_scale_multiplier": self.current_action_scale_multiplier,
            "control_action_noise_std": self.current_action_noise_std,
            "control_action_delay": self.current_action_delay,
            "control_action_filter_alpha": self.current_action_filter_alpha,
            "hole_center_offset": self.current_hole_center_offset.astype(np.float32),
            "fixture_height_offset": self.current_fixture_height_offset,
            "table_height_offset": self.current_table_height_offset,
            "geometry_profile": self.geometry_profile,
            "geometry_fixture_mode": self.geometry_fixture_mode,
            "geometry_true_fixture_variant": self.geometry_true_fixture_variant,
            "geometry_name": self.current_geometry_spec.name,
            "peg_shape": self.current_geometry_spec.peg_shape,
            "hole_shape": self.current_geometry_spec.hole_shape,
            "hole_half_size": self.current_hole_half_size,
            "peg_radius": self.current_peg_radius,
            "hole_clearance": self.current_geometry_spec.hole_clearance,
            "peg_half_extents": (
                np.asarray(self.current_geometry_spec.peg_half_extents, dtype=np.float32)
                if self.current_geometry_spec.peg_half_extents is not None
                else np.zeros(3, dtype=np.float32)
            ),
            "hole_half_extents": (
                np.asarray(self.current_geometry_spec.hole_half_extents, dtype=np.float32)
                if self.current_geometry_spec.hole_half_extents is not None
                else np.zeros(2, dtype=np.float32)
            ),
            "hole_polygon_sides": (
                int(self.current_geometry_spec.hole_polygon_sides)
                if self.current_geometry_spec.hole_polygon_sides is not None
                else 0
            ),
            "shape_yaw_clearance": self._shape_yaw_clearance(),
            **shape_yaw_metrics,
            **square_peg_metrics,
            "contact_friction_multiplier": self.current_contact_friction_multiplier,
            "contact_solref_time_multiplier": self.current_contact_solref_time_multiplier,
            "contact_solref_damping_multiplier": self.current_contact_solref_damping_multiplier,
            "contact_solimp_width_multiplier": self.current_contact_solimp_width_multiplier,
            "joint_damping_multiplier": self.current_joint_damping_multiplier,
            "actuator_kp_multiplier": self.current_actuator_kp_multiplier,
            "initialization_mode": self.initialization_mode,
            "initial_tip_target": self.current_initial_tip_target.astype(np.float32),
            "initial_ik_error": self.current_initial_ik_error,
            "initial_ik_attempts": self.current_initial_ik_attempts,
            "initial_shape_yaw_error_deg": self.current_initial_shape_yaw_error_deg,
            "near_hole_crop_size": self.near_hole_crop_size,
            "near_hole_crop_source_size": self.current_near_hole_crop_source_size,
            "near_hole_crop_source_size_range": (
                np.asarray(self.near_hole_crop_source_size_range, dtype=np.int32)
                if self.near_hole_crop_source_size_range is not None
                else np.asarray(
                    [
                        self.near_hole_crop_source_size,
                        self.near_hole_crop_source_size,
                    ],
                    dtype=np.int32,
                )
            ),
            "near_hole_crop_offset": np.asarray(self.near_hole_crop_offset, dtype=np.int32),
            "wrist_camera_pos_offset": self.wrist_camera_pos_offset.astype(np.float32),
            "wrist_camera_rot_offset_deg": np.rad2deg(
                self.wrist_camera_rot_offset_rad
            ).astype(np.float32),
            "wrist_camera_fovy": float(self.model.cam_fovy[self.wrist_camera_id]),
        }
