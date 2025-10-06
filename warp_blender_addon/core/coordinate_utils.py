"""
座標系轉換工具 - Warp ↔ Blender
Warp: Y-up (X, Y, Z)
Blender: Z-up (X, Z, Y)
"""

import numpy as np
import warp as wp


def warp_to_blender(pos_warp):
    """
    Warp 座標系 → Blender 座標系
    
    Args:
        pos_warp: Warp 座標 [X, Y, Z] 或 numpy array
    
    Returns:
        Blender 座標 [X, Z, Y]
    """
    if isinstance(pos_warp, (list, tuple)):
        return [pos_warp[0], pos_warp[2], pos_warp[1]]
    elif isinstance(pos_warp, np.ndarray):
        # 支援批量轉換
        if pos_warp.ndim == 1:
            return np.array([pos_warp[0], pos_warp[2], pos_warp[1]])
        elif pos_warp.ndim == 2:
            # 批量轉換 (N, 3) -> (N, 3)
            return np.column_stack([
                pos_warp[:, 0],
                pos_warp[:, 2],
                pos_warp[:, 1]
            ])
    else:
        raise TypeError(f"不支援的座標類型: {type(pos_warp)}")


def blender_to_warp(pos_blender):
    """
    Blender 座標系 → Warp 座標系
    
    Args:
        pos_blender: Blender 座標 [X, Z, Y] 或 numpy array
    
    Returns:
        Warp 座標 [X, Y, Z]
    """
    if isinstance(pos_blender, (list, tuple)):
        return [pos_blender[0], pos_blender[2], pos_blender[1]]
    elif isinstance(pos_blender, np.ndarray):
        # 支援批量轉換
        if pos_blender.ndim == 1:
            return np.array([pos_blender[0], pos_blender[2], pos_blender[1]])
        elif pos_blender.ndim == 2:
            # 批量轉換 (N, 3) -> (N, 3)
            return np.column_stack([
                pos_blender[:, 0],
                pos_blender[:, 2],
                pos_blender[:, 1]
            ])
    else:
        raise TypeError(f"不支援的座標類型: {type(pos_blender)}")


def get_rotation_quaternion():
    """
    獲取 Warp 軟體體初始化時需要的旋轉四元數
    將 Warp Y-up 旋轉到 Blender Z-up（繞 X 軸旋轉 90 度）
    
    Returns:
        warp.quat: 旋轉四元數
    """
    return wp.quat_from_axis_angle(wp.vec3(1.0, 0.0, 0.0), wp.pi / 2.0)


def transform_vector_warp_to_blender(vec_warp):
    """
    轉換向量從 Warp 到 Blender（用於速度、力等）
    
    Args:
        vec_warp: Warp 向量 wp.vec3 或 numpy array
    
    Returns:
        Blender 向量 [X, Z, Y]
    """
    if isinstance(vec_warp, wp.vec3):
        return [vec_warp[0], vec_warp[2], vec_warp[1]]
    else:
        return warp_to_blender(vec_warp)


def transform_vector_blender_to_warp(vec_blender):
    """
    轉換向量從 Blender 到 Warp（用於施加外力等）
    
    Args:
        vec_blender: Blender 向量 [X, Z, Y]
    
    Returns:
        Warp 向量 wp.vec3
    """
    converted = blender_to_warp(vec_blender)
    return wp.vec3(converted[0], converted[1], converted[2])