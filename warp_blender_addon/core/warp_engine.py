"""
Warp 模擬引擎 - 封裝 Warp 物理模擬核心邏輯
"""

import warp as wp
import warp.sim
import numpy as np
from .. import config
from .coordinate_utils import get_rotation_quaternion


class WarpEngine:
    """Warp 物理模擬引擎"""
    
    def __init__(self):
        """初始化引擎"""
        self.model = None
        self.state_0 = None
        self.state_1 = None
        self.integrator = None
        
        wp.init()
        wp.config.mode = "release"
    
    def initialize(self, cell_dim=None, cell_size=None, start_height=None,
                   density=None, k_mu=None, k_lambda=None, k_damp=None):
        """
        初始化軟體體模型（使用規則網格）
        
        Args:
            cell_dim: 網格維度
            cell_size: 單元格大小
            start_height: 初始高度
            density: 密度
            k_mu: 剪切模量
            k_lambda: 體積模量
            k_damp: 阻尼係數
        
        Returns:
            bool: 初始化是否成功
        """
        try:
            # 使用傳入值或從 config 讀取
            cell_dim = cell_dim or config.get_cell_dim()
            cell_size = cell_size or config.get_cell_size()
            start_height = start_height or config.get_start_height()
            density = density or config.get_density()
            k_mu = k_mu or config.get_k_mu()
            k_lambda = k_lambda or config.get_k_lambda()
            k_damp = k_damp or config.get_k_damp()
            
            print(f"創建軟體體網格: {cell_dim}x{cell_dim}x{cell_dim}")
            
            builder = wp.sim.ModelBuilder()
            rot_quat = get_rotation_quaternion()
            
            # 使用 add_soft_grid
            builder.add_soft_grid(
                pos=wp.vec3(0.0, start_height, 0.0),
                rot=rot_quat,
                vel=wp.vec3(0.0, 0.0, 0.0),
                dim_x=cell_dim,
                dim_y=cell_dim,
                dim_z=cell_dim,
                cell_x=cell_size,
                cell_y=cell_size,
                cell_z=cell_size,
                density=density,
                k_mu=k_mu,
                k_lambda=k_lambda,
                k_damp=k_damp
            )
            
            builder.add_shape_plane(plane=(0.0, 1.0, 0.0, 0.0))
            
            self.model = builder.finalize(device="cuda:0")
            self.state_0 = self.model.state()
            self.state_1 = self.model.state()
            self.integrator = wp.sim.SemiImplicitIntegrator()
            
            print(f"✅ Warp 引擎初始化成功 (add_soft_grid)")
            print(f"   - 粒子數: {self.model.particle_count}")
            print(f"   - 四面體數: {self.model.tet_count}")
            
            return True
            
        except Exception as e:
            print(f"❌ Warp 引擎初始化失敗: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def initialize_from_mesh(self, vertices_warp, tet_indices,
                            density=None, k_mu=None, k_lambda=None, k_damp=None):
        """
        從自訂網格初始化軟體體模型（使用 add_soft_mesh）
        
        Args:
            vertices_warp: Warp 座標系的頂點 (N, 3) numpy array
            tet_indices: 四面體索引 (M, 4) numpy array
            density: 密度
            k_mu: 剪切模量
            k_lambda: 體積模量
            k_damp: 阻尼係數
        
        Returns:
            bool: 初始化是否成功
        """
        try:
            # 使用預設值
            density = density or config.get_density()
            k_mu = k_mu or config.get_k_mu()
            k_lambda = k_lambda or config.get_k_lambda()
            k_damp = k_damp or config.get_k_damp()
            
            print(f"創建自訂軟體體網格")
            print(f"   - 頂點數: {len(vertices_warp)}")
            print(f"   - 四面體數: {len(tet_indices)}")
            
            # 確保是 numpy array
            if not isinstance(vertices_warp, np.ndarray):
                vertices_warp = np.array(vertices_warp, dtype=np.float32)
            if not isinstance(tet_indices, np.ndarray):
                tet_indices = np.array(tet_indices, dtype=np.int32)
            
            vertices_warp = vertices_warp.reshape(-1, 3)
            
            # ✅ 關鍵修復：Warp 期望 List[List[float]]，不是 flat list！
            # 轉換為嵌套 list
            vertices_list = vertices_warp.tolist()  # 這會產生 [[x,y,z], [x,y,z], ...]
            
            # 索引仍然是 flat list
            indices_list = tet_indices.flatten().tolist()
            
            print(f"   - 頂點 list 長度: {len(vertices_list)} (每個頂點是 list[3])")
            print(f"   - 索引 list 長度: {len(indices_list)}")
            print(f"   - 頂點[0]: {vertices_list[0]}")
            print(f"   - 頂點[0] 類型: {type(vertices_list[0])}")
            print(f"   - 頂點[0][0] 類型: {type(vertices_list[0][0])}")
            
            builder = wp.sim.ModelBuilder()
            
            # 使用 add_soft_mesh
            print(f"   - 呼叫 add_soft_mesh...")
            builder.add_soft_mesh(
                pos=(0.0, 0.0, 0.0),
                rot=(0.0, 0.0, 0.0, 1.0),
                vel=(0.0, 0.0, 0.0),
                vertices=vertices_list,  # List[List[float]]
                indices=indices_list,     # List[int] (flat)
                density=density,
                k_mu=k_mu,
                k_lambda=k_lambda,
                k_damp=k_damp,
                scale=1.0,
                tri_ke=0.0,
                tri_ka=1e-8,
                tri_kd=0.0,
                tri_drag=0.0,
                tri_lift=0.0
            )
            
            print(f"   - add_soft_mesh 完成")
            
            builder.add_shape_plane(plane=(0.0, 1.0, 0.0, 0.0))
            
            print(f"   - 正在 finalize...")
            self.model = builder.finalize(device="cuda:0")
            
            # 接觸參數（使用配置或預設值）
            self.model.soft_contact_ke = config.get_contact_ke()
            self.model.soft_contact_kd = config.get_contact_kd()
            self.model.soft_contact_kf = config.get_contact_kf()
            self.model.soft_contact_mu = config.get_contact_mu()
            self.model.ground = True
            
            self.state_0 = self.model.state()
            self.state_1 = self.model.state()
            self.integrator = wp.sim.SemiImplicitIntegrator()
            
            print(f"✅ Warp 引擎初始化成功 (add_soft_mesh)")
            print(f"   - 粒子數: {self.model.particle_count}")
            print(f"   - 四面體數: {self.model.tet_count}")
            print(f"   - 三角形數: {self.model.tri_count}")
            
            return True
            
        except Exception as e:
            print(f"❌ Warp 引擎初始化失敗: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def simulate_step(self, dt):
        """執行單個模擬步驟"""
        if self.model is None:
            raise RuntimeError("模型尚未初始化")
        
        self.state_0.clear_forces()
        self.state_1.clear_forces()
        
        self.integrator.simulate(
            self.model,
            self.state_0,
            self.state_1,
            dt
        )
        
        self.state_0, self.state_1 = self.state_1, self.state_0
    
    def simulate_substeps(self, frame_dt, num_substeps):
        """執行多個子步驟模擬"""
        substep_dt = frame_dt / num_substeps
        
        for _ in range(num_substeps):
            self.simulate_step(substep_dt)
        
        wp.synchronize()
    
    def get_particle_positions(self):
        """獲取當前粒子位置"""
        if self.state_0 is None:
            raise RuntimeError("狀態尚未初始化")
        
        return self.state_0.particle_q.numpy()
    
    def get_particle_velocities(self):
        """獲取當前粒子速度"""
        if self.state_0 is None:
            raise RuntimeError("狀態尚未初始化")
        
        return self.state_0.particle_qd.numpy()
    
    def reset_simulation(self):
        """重置模擬狀態"""
        if self.model is None:
            raise RuntimeError("模型尚未初始化")
        
        self.state_0 = self.model.state()
        self.state_1 = self.model.state()
        
        print("✅ 模擬狀態已重置")
    
    def get_model_info(self):
        """獲取模型資訊"""
        if self.model is None:
            return None
        
        return {
            'particle_count': self.model.particle_count,
            'tet_count': self.model.tet_count,
            'edge_count': self.model.edge_count,
            'tri_count': self.model.tri_count,
        }