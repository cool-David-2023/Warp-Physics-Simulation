"""
Bake 操作器 - 執行物理模擬並儲存快取
改進：支援 ESC 中斷、Bake 前檢查初始化
"""

import bpy
import warp as wp
from .. import config
from ..core.cache_manager import CacheManager
from ..blender_integration.mesh_builder import update_wireframe_mesh
from ..blender_integration.frame_handler import register_frame_handler


class WARP_OT_Bake(bpy.types.Operator):
    """Bake Warp 物理模擬到磁碟快取"""
    
    bl_idname = "warp.bake_simulation"
    bl_label = "Bake Simulation"
    bl_description = "Simulate and save animation cache to disk (ESC to cancel)"
    bl_options = {'REGISTER'}
    
    # 添加計時器屬性
    _timer = None
    _is_running = False
    
    def execute(self, context):
        """執行 Bake（使用 modal 模式以支援中斷）"""
        # 檢查模型是否已初始化
        if config.model is None:
            self.report({'ERROR'}, "請先初始化模型 (Init Grid 或 Init from Gmsh)")
            return {'CANCELLED'}
        
        # 檢查 .blend 檔案是否已儲存
        if not bpy.data.filepath:
            self.report({'WARNING'}, "建議先儲存 .blend 檔案以使用永久快取目錄")
        
        try:
            # 準備 Bake
            self._prepare_bake(context)
            
            # 啟動 modal 模式
            wm = context.window_manager
            self._timer = wm.event_timer_add(0.001, window=context.window)
            wm.modal_handler_add(self)
            
            self._is_running = True
            self._current_frame_idx = 0
            
            return {'RUNNING_MODAL'}
            
        except Exception as e:
            print(f"❌ Bake 初始化失敗: {e}")
            import traceback
            traceback.print_exc()
            self.report({'ERROR'}, f"Bake 失敗: {str(e)}")
            return {'CANCELLED'}
    
    def modal(self, context, event):
        """Modal 事件處理（支援 ESC 中斷）"""
        
        # 檢查 ESC 鍵中斷
        if event.type == 'ESC':
            self._finish_bake(context, cancelled=True)
            self.report({'WARNING'}, "Bake 已被用戶中斷")
            return {'CANCELLED'}
        
        # 計時器事件 - 模擬一幀
        if event.type == 'TIMER' and self._is_running:
            if self._current_frame_idx < self._total_frames:
                # 執行一幀模擬
                self._simulate_frame(context)
                self._current_frame_idx += 1
                
                # 更新進度
                progress = (self._current_frame_idx) / self._total_frames * 100
                
                # 強制重繪視窗
                for area in context.screen.areas:
                    if area.type == 'VIEW_3D':
                        area.tag_redraw()
                
                return {'RUNNING_MODAL'}
            else:
                # Bake 完成
                self._finish_bake(context, cancelled=False)
                self.report({'INFO'}, f"Bake 完成！({self._total_frames} 幀)")
                return {'FINISHED'}
        
        return {'PASS_THROUGH'}
    
    def _prepare_bake(self, context):
        """準備 Bake"""
        import time
        
        # 快取管理器
        self.cache_mgr = CacheManager()
        
        # 無條件清除快取
        print("🗑️ 清除舊快取...")
        self.cache_mgr.clear_cache()
        #wp.synchronize()  # 確保 GPU 同步
        
        print(f"📁 快取目錄: {self.cache_mgr.cache_dir}")
        
        # 時間軸參數
        scene = context.scene
        self._frame_start = scene.frame_start
        self._frame_end = scene.frame_end
        self._fps = scene.render.fps
        self._sim_substeps = config.get_sim_substeps()
        
        # 更新快取資訊
        config.cache_info['frame_start'] = self._frame_start
        config.cache_info['frame_end'] = self._frame_end
        config.cache_info['fps'] = self._fps
        
        print("\n" + "=" * 60)
        print("🔥 開始 Bake 模擬")
        print("=" * 60)
        print(f"幀範圍: {self._frame_start} - {self._frame_end}")
        print(f"FPS: {self._fps}")
        print(f"子步驟數: {self._sim_substeps}")
        print(f"快取目錄: {self.cache_mgr.cache_dir}")
        print("提示: 按 ESC 可中斷")
        print("=" * 60 + "\n")
        
        # 計算時間步長
        self._frame_dt = 1.0 / self._fps
        self._sim_dt = self._frame_dt / self._sim_substeps
        
        print(f"時間步長: {self._sim_dt:.6f} 秒 (每幀 {self._sim_substeps} 子步驟)")
        
        # 重置模擬狀態（移除 wp.synchronize()）
        print("🔄 重置模擬狀態...")
        t_start = time.perf_counter()
        
        config.state_0 = config.model.state()
        config.state_1 = config.model.state()
        config.integrator = wp.sim.SemiImplicitIntegrator()
        
        t_end = time.perf_counter()
        print(f"✅ 狀態已重置（耗時 {(t_end - t_start)*1000:.2f} ms）")
        
        self._total_frames = self._frame_end - self._frame_start + 1
        
        # 設置到起始幀
        context.scene.frame_set(self._frame_start)
    
    def _simulate_frame(self, context):
        """模擬單幀"""
        import time

        frame = self._frame_start + self._current_frame_idx

        t_start = time.perf_counter()
        
        # 執行子步驟模擬
        for _ in range(self._sim_substeps):
            config.state_0.clear_forces()
            config.state_1.clear_forces()
            
            config.integrator.simulate(
                config.model,
                config.state_0,
                config.state_1,
                self._sim_dt
            )
            
            # 交換狀態
            config.state_0, config.state_1 = config.state_1, config.state_0
        
        t_sim = time.perf_counter()

        # 同步 GPU
        wp.synchronize()

        t_sync = time.perf_counter()
        
        # 儲存當前幀位置
        positions_warp = config.state_0.particle_q.numpy()
        self.cache_mgr.save_frame(frame, positions_warp)

        t_save = time.perf_counter()
        
        # 即時更新視窗（每 3 幀）
        if config.wireframe_object and self._current_frame_idx % 3 == 0:
            context.scene.frame_set(frame)
            update_wireframe_mesh(
                config.wireframe_object,
                positions_warp
            )
        
        # 進度顯示（每 10 幀）
        if self._current_frame_idx % 10 == 0:
            progress = (self._current_frame_idx + 1) / self._total_frames * 100
            sim_time = (t_sim - t_start) * 1000
            sync_time = (t_sync - t_sim) * 1000
            save_time = (t_save - t_sync) * 1000
            total_time = (t_save - t_start) * 1000
            
            print(f"進度: {progress:.1f}% (幀 {frame}/{self._frame_end})")
            print(f"  模擬: {sim_time:.2f}ms | 同步: {sync_time:.2f}ms | 儲存: {save_time:.2f}ms | 總計: {total_time:.2f}ms")
    
    def _finish_bake(self, context, cancelled=False):
        """完成 Bake"""
        # 移除計時器
        if self._timer:
            wm = context.window_manager
            wm.event_timer_remove(self._timer)
            self._timer = None
        
        self._is_running = False
        
        if not cancelled:
            # 儲存快取元資訊
            config.cache_info['baked'] = True
            self.cache_mgr.save_cache_info(config.cache_info)
            
            print("\n✅ Bake 完成！")
            print(f"總幀數: {self._total_frames}")
            
            cache_size = self.cache_mgr.get_cache_size()
            print(f"快取大小: {cache_size:.2f} MB")
            print(f"快取位置: {self.cache_mgr.cache_dir}")
            print("=" * 60 + "\n")
            
            # 註冊時間軸更新處理器
            register_frame_handler()
            
            # 設置回起始幀
            context.scene.frame_set(self._frame_start)
        else:
            print("\n⚠️ Bake 已中斷")
            print(f"已完成: {self._current_frame_idx}/{self._total_frames} 幀")
            print("=" * 60 + "\n")