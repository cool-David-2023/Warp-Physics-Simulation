"""
從 TetGen 線框初始化 - 使用已生成的四面體數據
"""

import bpy
import numpy as np
from .. import config
from ..core.warp_engine import WarpEngine
from ..core.coordinate_utils import blender_to_warp
from ..blender_integration.scene_setup import setup_scene
from ..blender_integration.mesh_builder import create_wireframe_mesh


class WARP_OT_InitFromTet(bpy.types.Operator):
    """從 TetGen 線框初始化 Warp 模擬"""
    
    bl_idname = "warp.init_from_tet"
    bl_label = "Initialize from TetGen"
    bl_description = "Initialize Warp simulation from generated tetrahedral mesh"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        """執行初始化"""
        print("\n" + "=" * 60)
        print("🔧 從 TetGen 初始化 Warp 模型")
        print("=" * 60)
        
        # 檢查是否有 TetGen 數據
        if not hasattr(config, 'tet_data') or config.tet_data is None:
            self.report({'ERROR'}, "請先執行 Generate Tetrahedra")
            return {'CANCELLED'}
        
        tet_data = config.tet_data
        
        try:
            # 1. 清除場景
            #self._clear_scene()

            # 清除舊的 Warp 物件
            self._clear_warp_objects()
            
            # 2. 座標轉換 Blender → Warp
            print("\n🔄 座標系轉換...")
            vertices_blender = tet_data['vertices']
            elements = tet_data['elements']
            
            vertices_warp = self._convert_to_warp_coords(vertices_blender)
            
            print(f"   Blender 座標範圍: X={np.min(vertices_blender[:,0]):.3f}~{np.max(vertices_blender[:,0]):.3f}")
            print(f"   Warp 座標範圍:    X={np.min(vertices_warp[:,0]):.3f}~{np.max(vertices_warp[:,0]):.3f}")
            
            # 3. 檢查體積並修正
            vertices_warp, elements = self._ensure_positive_volumes(vertices_warp, elements)
            
            # 4. 讀取材質參數
            density = config.get_density()
            k_mu = config.get_k_mu()
            k_lambda = config.get_k_lambda()
            k_damp = config.get_k_damp()
            
            print(f"\n⚙️ 材質參數:")
            print(f"   密度: {density} kg/m³")
            print(f"   剪切模量: {k_mu}")
            print(f"   體積模量: {k_lambda}")
            print(f"   阻尼: {k_damp}")
            
            # 5. 初始化 Warp 引擎
            engine = WarpEngine()
            success = engine.initialize_from_mesh(
                vertices_warp=vertices_warp,
                tet_indices=elements,
                density=density,
                k_mu=k_mu,
                k_lambda=k_lambda,
                k_damp=k_damp
            )
            
            if not success:
                self.report({'ERROR'}, "Warp 引擎初始化失敗")
                return {'CANCELLED'}
            
            # 儲存到全域配置
            config.model = engine.model
            config.state_0 = engine.state_0
            config.state_1 = engine.state_1
            config.integrator = engine.integrator
            
            print(f"✅ 粒子數: {engine.model.particle_count}")
            print(f"✅ 四面體數: {engine.model.tet_count}")
            
            # 6. 創建 Blender 線框網格
            wireframe_obj = create_wireframe_mesh(
                positions_warp=engine.state_0.particle_q.numpy(),
                tet_indices=engine.model.tet_indices.numpy()
            )
            config.wireframe_object = wireframe_obj
            
            print(f"✅ 線框物件已創建: {wireframe_obj.name}")
            
            # 7. 設置場景
            setup_scene()
            
            # 8. 更新快取資訊
            config.cache_info['particle_count'] = engine.model.particle_count
            config.cache_info['fps'] = context.scene.render.fps
            config.cache_info['baked'] = False
            
            # 9. 設置時間軸到起始幀
            context.scene.frame_set(context.scene.frame_start)
            
            print("=" * 60)
            print("✅ 初始化完成！")
            print("=" * 60 + "\n")
            
            self.report({'INFO'}, f"模型初始化成功 ({engine.model.particle_count} 粒子)")
            return {'FINISHED'}
            
        except Exception as e:
            print(f"❌ 初始化失敗: {e}")
            import traceback
            traceback.print_exc()
            self.report({'ERROR'}, f"初始化失敗: {str(e)}")
            return {'CANCELLED'}

    def _clear_warp_objects(self):
        """只刪除 Warp 生成的物件"""
        warp_patterns = ['WarpWireframe', 'GmshWire']
        
        for obj in list(bpy.data.objects):
            if any(pattern in obj.name for pattern in warp_patterns):
                print(f"🗑️ 刪除: {obj.name}")
                bpy.data.objects.remove(obj, do_unlink=True)
        
        print("✅ Warp 物件已清除")

    def _clear_scene(self):
        """清除場景中的所有物件"""
        bpy.ops.object.select_all(action='DESELECT')
        
        for obj in bpy.data.objects:
            obj.select_set(True)
        
        bpy.ops.object.delete()
        
        print("✅ 場景已清除")
    
    def _convert_to_warp_coords(self, vertices_blender):
        """Blender 座標 → Warp 座標"""
        vertices_warp = np.column_stack([
            vertices_blender[:, 0],  # X 不變
            vertices_blender[:, 2],  # Z → Y
            vertices_blender[:, 1]   # Y → Z
        ]).astype(np.float32)
        
        return vertices_warp
    
    def _ensure_positive_volumes(self, vertices_warp, elements):
        """確保所有四面體體積為正"""
        from ..core.mesh_validator import MeshValidator
        
        validator = MeshValidator()
        volumes = validator.compute_tet_volumes(vertices_warp, elements)
        
        invalid_count = np.sum(volumes <= 0)
        
        if invalid_count > 0:
            print(f"⚠️ 檢測到 {invalid_count} 個反轉四面體，正在修正...")
            
            # 如果全部反轉，交換索引
            if np.all(volumes <= 0):
                print("   → 全部反轉，交換索引 0-1")
                elements = elements[:, [1, 0, 2, 3]]
                volumes = validator.compute_tet_volumes(vertices_warp, elements)
                invalid_count = np.sum(volumes <= 0)
                print(f"   → 修正後反轉數: {invalid_count}")
            
            # 如果仍有反轉，個別修正
            if invalid_count > 0:
                print(f"   ⚠️ 仍有 {invalid_count} 個反轉四面體")
                print("   ⚠️ 建議調整 TetGen 參數或檢查原始網格")
        
        return vertices_warp, elements