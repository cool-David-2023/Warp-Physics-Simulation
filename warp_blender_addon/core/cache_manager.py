"""
快取管理器 - 負責模擬數據的讀寫
支援 .npy 格式儲存粒子位置，JSON 格式儲存元資訊
"""

import json
import numpy as np
from pathlib import Path
from .. import config


class CacheManager:
    """Warp 模擬快取管理器"""
    
    def __init__(self):
        """初始化快取管理器"""
        # ✅ 動態獲取快取目錄（而非在初始化時固定）
        self._ensure_cache_dir()
    
    def _ensure_cache_dir(self):
        """確保快取目錄存在並更新 config"""
        # 重新獲取快取目錄（以防檔案儲存狀態改變）
        config.cache_dir = config.get_cache_directory()
        
        if config.cache_dir:
            config.cache_dir.mkdir(exist_ok=True)
    
    @property
    def cache_dir(self):
        """動態獲取快取目錄"""
        self._ensure_cache_dir()
        return config.cache_dir
    
    def save_frame(self, frame, obj_name, positions_warp):
        """
        儲存單幀的物件粒子位置數據
        
        Args:
            frame: 幀編號
            obj_name: 物件名稱
            positions_warp: Warp 座標系的粒子位置 (N, 3) numpy array
        """
        if self.cache_dir is None:
            raise RuntimeError("快取目錄未設置，請先儲存 .blend 檔案")
        
        # 創建物件子目錄
        obj_cache_dir = self.cache_dir / obj_name
        obj_cache_dir.mkdir(exist_ok=True)
        
        frame_path = obj_cache_dir / f"frame_{frame:04d}.npy"
        np.save(frame_path, positions_warp)
    
    def load_frame(self, frame, obj_name):
        """
        載入單幀的物件粒子位置數據
        
        Args:
            frame: 幀編號
            obj_name: 物件名稱
        
        Returns:
            positions_warp: Warp 座標系的粒子位置 (N, 3) numpy array，
                           若檔案不存在則返回 None
        """
        if self.cache_dir is None:
            return None
        
        obj_cache_dir = self.cache_dir / obj_name
        frame_path = obj_cache_dir / f"frame_{frame:04d}.npy"
        
        if frame_path.exists():
            return np.load(frame_path)
        else:
            return None
    
    def save_cache_info(self, cache_info_dict):
        """
        儲存快取元資訊（幀範圍、粒子數、FPS 等）
        
        Args:
            cache_info_dict: 快取資訊字典
        """
        if self.cache_dir is None:
            raise RuntimeError("快取目錄未設置，請先儲存 .blend 檔案")
        
        info_path = self.cache_dir / "cache_info.json"
        
        with open(info_path, 'w', encoding='utf-8') as f:
            json.dump(cache_info_dict, f, indent=2, ensure_ascii=False)
        
        print(f"✅ 快取資訊已儲存: {info_path}")
    
    def load_cache_info(self):
        """
        載入快取元資訊
        
        Returns:
            dict: 快取資訊字典，若檔案不存在則返回 None
        """
        if self.cache_dir is None:
            return None
        
        info_path = self.cache_dir / "cache_info.json"
        
        if info_path.exists():
            with open(info_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            return None
    
    def clear_cache(self):
        """清除所有快取檔案（.npy 和 .json）"""
        if self.cache_dir is None or not self.cache_dir.exists():
            print("⚠️ 無快取目錄可清除")
            return
        
        # 刪除所有 .npy 檔案
        npy_files = list(self.cache_dir.glob("frame_*.npy"))
        for file in npy_files:
            try:
                file.unlink()
            except Exception as e:
                print(f"⚠️ 刪除失敗: {file.name} - {e}")
        
        # 刪除元資訊
        info_path = self.cache_dir / "cache_info.json"
        if info_path.exists():
            try:
                info_path.unlink()
            except Exception as e:
                print(f"⚠️ 刪除 cache_info.json 失敗: {e}")
        
        # ✅ 強制垃圾回收
        import gc
        gc.collect()
        
        print(f"✅ 快取已清除: {self.cache_dir}")
        print(f"   - 刪除了 {len(npy_files)} 個 .npy 檔案")
    
    def get_cache_size(self):
        """
        計算快取目錄的總大小
        
        Returns:
            float: 快取大小（MB）
        """
        if self.cache_dir is None or not self.cache_dir.exists():
            return 0.0
        
        total_bytes = sum(
            f.stat().st_size for f in self.cache_dir.glob('*')
        )
        
        return total_bytes / 1024 / 1024
    
    def get_frame_count(self):
        """
        獲取已快取的幀數
        
        Returns:
            int: 快取的幀數
        """
        if self.cache_dir is None or not self.cache_dir.exists():
            return 0
        
        return len(list(self.cache_dir.glob("frame_*.npy")))
    
    def validate_cache(self, expected_frame_start, expected_frame_end):
        """
        驗證快取完整性（檢查所有幀是否存在）
        
        Args:
            expected_frame_start: 期望的起始幀
            expected_frame_end: 期望的結束幀
        
        Returns:
            bool: 快取是否完整
        """
        if self.cache_dir is None:
            return False
        
        for frame in range(expected_frame_start, expected_frame_end + 1):
            frame_path = self.cache_dir / f"frame_{frame:04d}.npy"
            if not frame_path.exists():
                print(f"❌ 缺少幀: {frame}")
                return False
        
        return True
    
    def has_cache(self):
        """
        檢查是否存在快取數據
        
        Returns:
            bool: 是否有快取
        """
        return self.get_frame_count() > 0