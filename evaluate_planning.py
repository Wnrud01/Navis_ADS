"""
DX Challenge Motion Planning Evaluation Script for Navis_ADS
============================================================
Evaluates motion planning models using official RideFlux Score and Prediction Error metrics:
  - RideFlux Score = (7 * progress_ratio + 3 * comfort) / 10 * (1 - overlap) * (1 - offroad)
  - minADE_1, minADE_6, minFDE_1, minFDE_6
  - T_infer_ms & Error Score
"""

import os
import argparse
import time
import numpy as np
import torch

class MotionPlanningEvaluator:
    def __init__(self, comfort_accel_lim: float = 2.0, comfort_jerk_lim: float = 2.5):
        self.comfort_accel_lim = comfort_accel_lim
        self.comfort_jerk_lim = comfort_jerk_lim

    def compute_progress_ratio(self, trajectory: np.ndarray, goal_xy: np.ndarray) -> float:
        if len(trajectory) < 2:
            return 0.0
        start_xy = trajectory[0]
        final_xy = trajectory[-1]

        total_dist = float(np.linalg.norm(goal_xy - start_xy))
        if total_dist < 1e-3:
            return 1.0

        rem_dist = float(np.linalg.norm(goal_xy - final_xy))
        progress = (total_dist - rem_dist) / total_dist
        return float(np.clip(progress, 0.0, 1.0))

    def compute_comfort(self, trajectory: np.ndarray, dt: float = 0.1) -> float:
        if len(trajectory) < 4:
            return 1.0

        vel = np.diff(trajectory, axis=0) / dt
        speed = np.linalg.norm(vel, axis=1)
        accel = np.diff(speed) / dt
        jerk = np.diff(accel) / dt

        accel_ratio = float(np.mean(np.abs(accel) <= self.comfort_accel_lim)) if len(accel) > 0 else 1.0
        jerk_ratio = float(np.mean(np.abs(jerk) <= self.comfort_jerk_lim)) if len(jerk) > 0 else 1.0

        if np.isnan(accel_ratio): accel_ratio = 1.0
        if np.isnan(jerk_ratio): jerk_ratio = 1.0

        return float(0.5 * accel_ratio + 0.5 * jerk_ratio)

    def evaluate_episode(self, planned_trajectory: np.ndarray, goal_xy: np.ndarray, collided: bool = False, offroad: bool = False, gt_future: np.ndarray | None = None) -> dict[str, float]:
        progress_ratio = self.compute_progress_ratio(planned_trajectory, goal_xy)
        comfort = self.compute_comfort(planned_trajectory)
        overlap = 1.0 if collided else 0.0
        offroad_in_box = 1.0 if offroad else 0.0

        raw_score = (7.0 * progress_ratio + 3.0 * comfort) / 10.0
        rideflux_score = raw_score * (1.0 - overlap) * (1.0 - offroad_in_box)

        metrics = {
            "rideflux_score": float(rideflux_score),
            "progress_ratio": float(progress_ratio),
            "comfort": float(comfort),
            "overlap": float(overlap),
            "offroad_in_box": float(offroad_in_box),
        }
        if gt_future is not None and len(gt_future) == len(planned_trajectory):
            disp = np.linalg.norm(planned_trajectory - gt_future, axis=-1)
            metrics["ade"] = float(np.mean(disp))
            metrics["fde"] = float(disp[-1])
        return metrics

    def compute_error_score(self, min_ade_1: float, min_ade_6: float, t_infer_ms: float) -> float:
        accuracy_term = 0.5 * (min_ade_1 + min_ade_6)
        speed_penalty = 1.0 + max(0.0, t_infer_ms - 100.0) / 200.0
        return float(accuracy_term * speed_penalty)


def run_evaluation():
    print("==========================================================================")
    print(" DX Challenge Motion Planning Evaluation System (RideFlux Score Metric)")
    print("==========================================================================")
    evaluator = MotionPlanningEvaluator()
    print(" [Status] Evaluator initialized successfully.")

if __name__ == "__main__":
    run_evaluation()
