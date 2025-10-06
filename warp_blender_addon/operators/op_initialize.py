"""
初始化操作器 - 創建 Warp 模擬模型
改進：不刪除其他網格物件，只清除舊的 Warp 線框
"""

import bpy
from .. import config
from ..core.warp_engine import WarpEngine
from ..blender_integration.scene_setup import setup_scene
from ..blender_integration.mesh_builder import create_wireframe_mesh


class WARP_OT_InitModel(bpy.types.Operator):
    """初始化 Warp 物理模擬模型"""
    
    bl_idname = "warp.init_model"
    bl_label = "Initialize Warp Model"
    bl_description = "Create a new soft body simulation model with current parameters"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        """執行初始化"""
        print("\n" + "=" * 60)
        print("🔧 初始化 Warp 模型")
        print("=" * 60)
        
        try:
            # 1. 清除舊的 Warp 線框（保留其他物件）
            #self._clear_old_warp_objects()

            # 清除舊的 Warp 物件
            self._clear_warp_objects()
            
            # 2. 從場景屬性讀取參數
            cell_dim = config.get_cell_dim()
            cell_size = config.get_cell_size()
            start_height = config.get_start_height()
            density = config.get_density()
            k_mu = config.get_k_mu()
            k_lambda = config.get_k_lambda()
            k_damp = config.get_k_damp()
            
            print(f"使用參數:")
            print(f"  網格: {cell_dim}x{cell_dim}x{cell_dim}")
            print(f"  單元格: {cell_size}m")
            print(f"  高度: {start_height}m")
            print(f"  密度: {density} kg/m³")
            print(f"  剪切模量: {k_mu}")
            print(f"  體積模量: {k_lambda}")
            print(f"  阻尼: {k_damp}")
            
            # 3. 初始化 Warp 引擎（傳入自訂參數）
            engine = WarpEngine()
            success = engine.initialize(
                cell_dim=cell_dim,
                cell_size=cell_size,
                start_height=start_height,
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
            
            # 4. 創建 Blender 線框網格
            wireframe_obj = create_wireframe_mesh(
                positions_warp=engine.state_0.particle_q.numpy(),
                tet_indices=engine.model.tet_indices.numpy()
            )
            config.wireframe_object = wireframe_obj
            
            print(f"✅ 線框物件已創建: {wireframe_obj.name}")
            
            # 5. 設置場景（只創建缺少的元素）
            self._setup_scene_elements()
            
            # 6. 更新快取資訊
            config.cache_info['particle_count'] = engine.model.particle_count
            config.cache_info['fps'] = context.scene.render.fps
            config.cache_info['baked'] = False
            
            # 7. 設置時間軸到起始幀
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


    def _clear_old_warp_objects(self):
        """清除舊的 Warp 線框物件（保留其他物件）"""
        objects_to_remove = []
        
        for obj in bpy.data.objects:
            # 只刪除 Warp 生成的線框物件
            if obj.name.startswith("WarpWireframe") or \
               obj.name.startswith("Warp_Result") or \
               (hasattr(config, 'wireframe_object') and obj == config.wireframe_object):
                objects_to_remove.append(obj)
        
        for obj in objects_to_remove:
            bpy.data.objects.remove(obj, do_unlink=True)
        
        if objects_to_remove:
            print(f"✅ 已清除 {len(objects_to_remove)} 個舊 Warp 線框物件")
        
        # 重置全域引用
        config.wireframe_object = None
    
    def _setup_scene_elements(self):
        """設置場景元素（只創建缺少的）"""
        # 檢查是否已有相機
        has_camera = any(obj.type == 'CAMERA' for obj in bpy.data.objects)
        
        # 檢查是否已有燈光
        has_light = any(obj.type == 'LIGHT' for obj in bpy.data.objects)
        
        # 檢查是否已有地面
        has_ground = any(obj.name == "Ground" for obj in bpy.data.objects)
        
        # 只創建缺少的元素
        if not has_ground:
            from ..blender_integration.scene_setup import create_ground_plane
            create_ground_plane()
        
        if not has_camera:
            from ..blender_integration.scene_setup import create_camera
            create_camera()
        
        if not has_light:
            from ..blender_integration.scene_setup import create_light
            create_light()
        
        print(f"✅ 場景檢查完成（相機:{has_camera}, 燈光:{has_light}, 地面:{has_ground}）")