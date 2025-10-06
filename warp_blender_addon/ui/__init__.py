"""
UI 模組 - 使用者介面
五個獨立面板 + Material Library 彈出式視窗
"""

from .panel_main import (
    WARP_OT_OpenMaterialLibrary,
    WARP_OT_ApplyPreset,
    WARP_OT_SavePreset,
    WARP_OT_ResetParameters,
    WARP_PT_SimulationPanel,
    WARP_PT_GmshPanel,
    WARP_PT_GridPanel,
    WARP_PT_BakePanel,
    WARP_PT_StatusPanel,
)

__all__ = [
    # Operators
    'WARP_OT_OpenMaterialLibrary',
    'WARP_OT_ApplyPreset',
    'WARP_OT_SavePreset',
    'WARP_OT_ResetParameters',
    
    # Panels
    'WARP_PT_SimulationPanel',
    'WARP_PT_GmshPanel',
    'WARP_PT_GridPanel',
    'WARP_PT_BakePanel',
    'WARP_PT_StatusPanel',
]