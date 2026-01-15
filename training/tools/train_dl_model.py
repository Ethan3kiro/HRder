#!/usr/bin/env python3
"""
深度学习模型训练脚本
使用 CNN 训练数字识别模型，支持 MPS 加速
"""

import json
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
from pathlib import Path
import cv2
import numpy as np
from tqdm import tqdm
import matplotlib.pyplot as plt


class DigitDataset(Dataset):
    """数字图像数据集"""
    
    def __init__(self, data_dir, transform=None):
        self.data_dir = Path(data_dir)
        self.transform = transform
        
        # 加载所有图像文件
        self.samples = []
        for img_path in self.data_dir.glob("*.png"):
            # 从文件名提取标签
            # 格式: 00000_45_0_AZ_orig.png
            parts = img_path.stem.split('_')
            if len(parts) >= 2:
                label_str = parts[1].replace('_', '.')
                try:
                    label = float(label_str)
                    self.samples.append((img_path, label))
                except ValueError:
                    continue
        
        print(f"  加载了 {len(self.samples)} 个样本")
    
    def __len__(self):
        return len(self.samples)
    
    def __getitem__(self, idx):
        img_path, label = self.samples[idx]
        
        # 加载图像
        img = cv2.imread(str(img_path), cv2.IMREAD_GRAYSCALE)
        
        # 归一化到 [0, 1]
        img = img.astype(np.float32) / 255.0
        
        # 转换为 tensor (C, H, W)
        img = torch.from_numpy(img).unsqueeze(0)
        
        # 标签转换为 tensor
        label = torch.tensor(label, dtype=torch.float32)
        
        return img, label


class DigitCNN(nn.Module):
    """数字识别 CNN 模型"""
    
    def __init__(self):
        super(DigitCNN, self).__init__()
        
        # 卷积层
        self.conv1 = nn.Conv2d(1, 32, kernel_size=3, padding=1)
        self.conv2 = nn.Conv2d(32, 64, kernel_size=3, padding=1)
        self.conv3 = nn.Conv2d(64, 128, kernel_size=3, padding=1)
        
        # 池化层
        self.pool = nn.MaxPool2d(2, 2)
        
        # Dropout
        self.dropout = nn.Dropout(0.5)
        
        # 全连接层
        # 28x28 -> 14x14 -> 7x7 -> 3x3
        self.fc1 = nn.Linear(128 * 3 * 3, 256)
        self.fc2 = nn.Linear(256, 128)
        self.fc3 = nn.Linear(128, 1)  # 回归任务，输出一个数值
        
        # 激活函数
        self.relu = nn.ReLU()
    
    def forward(self, x):
        # 卷积块 1
        x = self.relu(self.conv1(x))
        x = self.pool(x)  # 28x28 -> 14x14
        
        # 卷积块 2
        x = self.relu(self.conv2(x))
        x = self.pool(x)  # 14x14 -> 7x7
        
        # 卷积块 3
        x = self.relu(self.conv3(x))
        x = self.pool(x)  # 7x7 -> 3x3
        
        # 展平
        x = x.view(-1, 128 * 3 * 3)
        
        # 全连接层
        x = self.relu(self.fc1(x))
        x = self.dropout(x)
        x = self.relu(self.fc2(x))
        x = self.dropout(x)
        x = self.fc3(x)
        
        return x


class Trainer:
    """模型训练器"""
    
    def __init__(self, model, device, train_loader, val_loader, learning_rate=0.001):
        self.model = model.to(device)
        self.device = device
        self.train_loader = train_loader
        self.val_loader = val_loader
        
        # 损失函数和优化器
        self.criterion = nn.MSELoss()
        self.optimizer = optim.Adam(model.parameters(), lr=learning_rate)
        
        # 学习率调度器
        self.scheduler = optim.lr_scheduler.ReduceLROnPlateau(
            self.optimizer, mode='min', factor=0.5, patience=5
        )
        
        # 训练历史
        self.history = {
            'train_loss': [],
            'val_loss': [],
            'train_mae': [],
            'val_mae': []
        }
    
    def train_epoch(self):
        """训练一个 epoch"""
        self.model.train()
        total_loss = 0
        total_mae = 0
        
        for images, labels in tqdm(self.train_loader, desc="训练", leave=False):
            images = images.to(self.device)
            labels = labels.to(self.device).unsqueeze(1)
            
            # 前向传播
            outputs = self.model(images)
            loss = self.criterion(outputs, labels)
            
            # 反向传播
            self.optimizer.zero_grad()
            loss.backward()
            self.optimizer.step()
            
            # 统计
            total_loss += loss.item()
            total_mae += torch.abs(outputs - labels).mean().item()
        
        avg_loss = total_loss / len(self.train_loader)
        avg_mae = total_mae / len(self.train_loader)
        
        return avg_loss, avg_mae
    
    def validate(self):
        """验证模型"""
        self.model.eval()
        total_loss = 0
        total_mae = 0
        
        with torch.no_grad():
            for images, labels in tqdm(self.val_loader, desc="验证", leave=False):
                images = images.to(self.device)
                labels = labels.to(self.device).unsqueeze(1)
                
                # 前向传播
                outputs = self.model(images)
                loss = self.criterion(outputs, labels)
                
                # 统计
                total_loss += loss.item()
                total_mae += torch.abs(outputs - labels).mean().item()
        
        avg_loss = total_loss / len(self.val_loader)
        avg_mae = total_mae / len(self.val_loader)
        
        return avg_loss, avg_mae
    
    def train(self, num_epochs, save_path):
        """训练模型"""
        print("\n" + "=" * 60)
        print("开始训练")
        print("=" * 60)
        
        best_val_loss = float('inf')
        patience_counter = 0
        max_patience = 15
        
        for epoch in range(num_epochs):
            print(f"\nEpoch {epoch + 1}/{num_epochs}")
            
            # 训练
            train_loss, train_mae = self.train_epoch()
            
            # 验证
            val_loss, val_mae = self.validate()
            
            # 更新学习率
            old_lr = self.optimizer.param_groups[0]['lr']
            self.scheduler.step(val_loss)
            new_lr = self.optimizer.param_groups[0]['lr']
            
            # 如果学习率改变，打印信息
            if new_lr != old_lr:
                print(f"  ⚠️  学习率降低: {old_lr:.6f} → {new_lr:.6f}")
            
            # 记录历史
            self.history['train_loss'].append(train_loss)
            self.history['val_loss'].append(val_loss)
            self.history['train_mae'].append(train_mae)
            self.history['val_mae'].append(val_mae)
            
            # 打印结果
            print(f"  训练损失: {train_loss:.4f}, MAE: {train_mae:.2f}")
            print(f"  验证损失: {val_loss:.4f}, MAE: {val_mae:.2f}")
            
            # 保存最佳模型
            if val_loss < best_val_loss:
                best_val_loss = val_loss
                patience_counter = 0
                torch.save({
                    'epoch': epoch,
                    'model_state_dict': self.model.state_dict(),
                    'optimizer_state_dict': self.optimizer.state_dict(),
                    'val_loss': val_loss,
                    'val_mae': val_mae,
                }, save_path)
                print(f"  ✓ 保存最佳模型 (验证损失: {val_loss:.4f})")
            else:
                patience_counter += 1
                if patience_counter >= max_patience:
                    print(f"\n⚠️  早停：验证损失 {max_patience} 个 epoch 未改善")
                    break
        
        print("\n" + "=" * 60)
        print("✅ 训练完成！")
        print("=" * 60)
        print(f"\n最佳验证损失: {best_val_loss:.4f}")
        print(f"最佳验证 MAE: {min(self.history['val_mae']):.2f}")
        
        return self.history
    
    def plot_history(self, save_path):
        """绘制训练历史"""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))
        
        # 损失曲线
        ax1.plot(self.history['train_loss'], label='训练损失')
        ax1.plot(self.history['val_loss'], label='验证损失')
        ax1.set_xlabel('Epoch')
        ax1.set_ylabel('Loss (MSE)')
        ax1.set_title('训练和验证损失')
        ax1.legend()
        ax1.grid(True)
        
        # MAE 曲线
        ax2.plot(self.history['train_mae'], label='训练 MAE')
        ax2.plot(self.history['val_mae'], label='验证 MAE')
        ax2.set_xlabel('Epoch')
        ax2.set_ylabel('MAE')
        ax2.set_title('平均绝对误差')
        ax2.legend()
        ax2.grid(True)
        
        plt.tight_layout()
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"\n📊 训练曲线已保存: {save_path}")


def main():
    """主函数"""
    print("=" * 60)
    print("深度学习 OCR 模型训练")
    print("=" * 60)
    
    # 检查数据集
    data_dir = Path("training_data/dl_dataset")
    train_dir = data_dir / "train"
    val_dir = data_dir / "val"
    
    if not train_dir.exists() or not val_dir.exists():
        print("\n❌ 数据集不存在！")
        print("   请先运行: python3 tools/prepare_dl_data.py")
        return 1
    
    # 检查设备
    if torch.backends.mps.is_available():
        device = torch.device("mps")
        print("\n✓ 使用 MPS (Metal) 加速")
    elif torch.cuda.is_available():
        device = torch.device("cuda")
        print("\n✓ 使用 CUDA 加速")
    else:
        device = torch.device("cpu")
        print("\n⚠️  使用 CPU（训练会较慢）")
    
    print(f"  设备: {device}")
    
    # 加载数据集
    print("\n📦 加载数据集...")
    print("  训练集:")
    train_dataset = DigitDataset(train_dir)
    print("  验证集:")
    val_dataset = DigitDataset(val_dir)
    
    # 创建数据加载器
    batch_size = 32
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True, num_workers=0)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False, num_workers=0)
    
    print(f"\n  批次大小: {batch_size}")
    print(f"  训练批次: {len(train_loader)}")
    print(f"  验证批次: {len(val_loader)}")
    
    # 创建模型
    print("\n🔧 创建模型...")
    model = DigitCNN()
    
    # 计算参数数量
    total_params = sum(p.numel() for p in model.parameters())
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"  总参数: {total_params:,}")
    print(f"  可训练参数: {trainable_params:,}")
    
    # 创建训练器
    trainer = Trainer(model, device, train_loader, val_loader, learning_rate=0.001)
    
    # 训练模型
    num_epochs = 50
    model_path = Path("models/digit_ocr_model.pth")
    model_path.parent.mkdir(exist_ok=True)
    
    history = trainer.train(num_epochs, model_path)
    
    # 绘制训练曲线
    plot_path = Path("models/training_history.png")
    trainer.plot_history(plot_path)
    
    # 保存训练历史
    history_path = Path("models/training_history.json")
    with open(history_path, 'w') as f:
        json.dump(history, f, indent=2)
    print(f"📝 训练历史已保存: {history_path}")
    
    print("\n" + "=" * 60)
    print("✅ 全部完成！")
    print("=" * 60)
    print(f"\n生成的文件:")
    print(f"  1. {model_path} - 训练好的模型")
    print(f"  2. {plot_path} - 训练曲线图")
    print(f"  3. {history_path} - 训练历史数据")
    print(f"\n下一步:")
    print(f"  运行测试: python3 tools/test_dl_model.py")
    
    return 0


if __name__ == "__main__":
    exit(main())
