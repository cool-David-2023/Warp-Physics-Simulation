"""
Blender Integration 模組 - Blender 整合層
負責將核心邏輯連接到 Blender API
"""

from .mesh_builder import create_wireframe_mesh, update_wireframe_mesh, extract_edges_from_tets
from .scene_setup import setup_scene, create_ground_plane, create_camera, create_light
from .frame_handler import register_frame_handler, unregister_frame_handler, update_from_cache

__all__ = [
    # Mesh operations
    'create_wireframe_mesh',
    'update_wireframe_mesh',
    'extract_edges_from_tets',
    
    # Scene setup
    'setup_scene',
    'create_ground_plane',
    'create_camera',
    'create_light',
    
    # Frame handler
    'register_frame_handler',
    'unregister_frame_handler',
    'update_from_cache',
]