#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查预训练模型质量"""
import torch
import os
import numpy as np

pkl_path = 'enhanced_dqn_checkpoint_v9.pkl'

print("=" * 60)
print("预训练模型诊断")
print("=" * 60)

if not os.path.exists(pkl_path):
    print(f"❌ 模型文件不存在: {pkl_path}")
    exit(1)

print(f"✅ 模型文件存在")
print(f"📦 文件大小: {os.path.getsize(pkl_path)/1024:.1f} KB\n")

try:
    # PyTorch 2.6需要显式设置weights_only=False来加载包含numpy对象的checkpoint
    checkpoint = torch.load(pkl_path, map_location='cpu', weights_only=False)
    
    print(f"✅ 模型加载成功")
    print(f"📋 包含的键: {list(checkpoint.keys())}\n")
    
    # 检查训练统计（新格式）
    if 'training_stats' in checkpoint:
        stats = checkpoint['training_stats']
        print("=" * 60)
        print("训练统计（新格式）")
        print("=" * 60)
        
        episode_rewards = stats.get('episode_rewards', [])
        episode_losses = stats.get('episode_losses', [])
        
        print(f"训练Episode数: {len(episode_rewards)}")
        
        if episode_rewards:
            print(f"平均奖励: {np.mean(episode_rewards):.4f}")
            print(f"奖励标准差: {np.std(episode_rewards):.4f}")
            print(f"奖励范围: [{min(episode_rewards):.4f}, {max(episode_rewards):.4f}]")
            print(f"最后10个episode平均奖励: {np.mean(episode_rewards[-10:]):.4f}")
        
        if episode_losses:
            print(f"平均损失: {np.mean(episode_losses):.6f}")
            print(f"最后10个episode平均损失: {np.mean(episode_losses[-10:]):.6f}")
        
        print(f"Meta-learning事件: {len(stats.get('meta_learning_events', []))}")
        print(f"Bayesian优化事件: {len(stats.get('bayesian_optimization_events', []))}")
        print(f"Fallback事件: {len(stats.get('fallback_events', []))}")
    
    # 检查旧格式的训练信息
    elif 'loss_history' in checkpoint or 'performance_history' in checkpoint:
        print("=" * 60)
        print("训练信息（旧格式）")
        print("=" * 60)
        
        train_count = checkpoint.get('train_count', 0)
        epsilon = checkpoint.get('epsilon', 1.0)
        fallback_count = checkpoint.get('fallback_count', 0)
        
        print(f"训练步数: {train_count}")
        print(f"当前Epsilon: {epsilon}")
        print(f"Fallback次数: {fallback_count}")
        
        # 检查损失历史
        loss_history = checkpoint.get('loss_history', [])
        if loss_history:
            print(f"\n损失历史:")
            print(f"  记录数: {len(loss_history)}")
            print(f"  平均损失: {np.mean(loss_history):.6f}")
            if len(loss_history) >= 10:
                print(f"  最后10次平均损失: {np.mean(loss_history[-10:]):.6f}")
                print(f"  前10次平均损失: {np.mean(loss_history[:10]):.6f}")
        
        # 检查性能历史
        performance_history = checkpoint.get('performance_history', [])
        if performance_history:
            print(f"\n性能历史:")
            print(f"  记录数: {len(performance_history)}")
            try:
                # 如果是字典列表
                if isinstance(performance_history[0], dict):
                    qps_values = [p.get('qps', 0) for p in performance_history if 'qps' in p]
                    if qps_values:
                        print(f"  平均QPS: {np.mean(qps_values):.2f}")
                        if len(qps_values) >= 10:
                            print(f"  最后10次平均QPS: {np.mean(qps_values[-10:]):.2f}")
                else:
                    print(f"  平均性能: {np.mean(performance_history):.4f}")
            except:
                print(f"  无法解析性能数据")
        
        # 检查其他历史
        bayesian_history = checkpoint.get('bayesian_history', [])
        meta_history = checkpoint.get('meta_history', [])
        
        if bayesian_history:
            print(f"\nBayesian优化历史: {len(bayesian_history)}次")
        if meta_history:
            print(f"Meta-learning历史: {len(meta_history)}次")
    
    else:
        print("⚠️ 没有训练统计信息")
    
    # 检查超参数
    if 'hyperparams' in checkpoint:
        print("\n" + "=" * 60)
        print("超参数")
        print("=" * 60)
        for k, v in checkpoint['hyperparams'].items():
            print(f"{k:20s}: {v}")
    else:
        print("\n⚠️ 没有超参数信息")
    
    # 检查增强功能状态
    if 'enhancement_status' in checkpoint:
        print("\n" + "=" * 60)
        print("增强功能状态")
        print("=" * 60)
        for k, v in checkpoint['enhancement_status'].items():
            print(f"{k:20s}: {v}")
    else:
        print("\n⚠️ 没有增强功能状态信息")
    
    # 检查网络参数
    if 'q_network_state_dict' in checkpoint:
        q_net = checkpoint['q_network_state_dict']
        print("\n" + "=" * 60)
        print("网络结构")
        print("=" * 60)
        print(f"网络层数: {len(q_net)}")
        total_params = sum(p.numel() for p in q_net.values())
        print(f"总参数量: {total_params:,}")
    
    # 质量评估
    print("\n" + "=" * 60)
    print("质量评估")
    print("=" * 60)
    
    issues = []
    
    if 'training_stats' in checkpoint:
        stats = checkpoint['training_stats']
        rewards = stats.get('episode_rewards', [])
        
        if len(rewards) < 100:
            issues.append(f"❌ 训练Episode太少 ({len(rewards)} < 100)")
        elif len(rewards) < 500:
            issues.append(f"⚠️ 训练Episode偏少 ({len(rewards)} < 500)")
        else:
            print(f"✅ 训练Episode充足 ({len(rewards)})")
        
        if rewards:
            recent_rewards = rewards[-50:] if len(rewards) >= 50 else rewards
            if np.mean(recent_rewards) < 0:
                issues.append(f"❌ 近期平均奖励为负 ({np.mean(recent_rewards):.4f})")
            elif np.mean(recent_rewards) < 0.5:
                issues.append(f"⚠️ 近期平均奖励偏低 ({np.mean(recent_rewards):.4f})")
            else:
                print(f"✅ 近期平均奖励正常 ({np.mean(recent_rewards):.4f})")
            
            # 检查收敛性
            if len(rewards) >= 100:
                early_rewards = np.mean(rewards[:50])
                late_rewards = np.mean(rewards[-50:])
                improvement = late_rewards - early_rewards
                
                if improvement < 0:
                    issues.append(f"❌ 训练过程性能下降 ({improvement:.4f})")
                elif improvement < 0.1:
                    issues.append(f"⚠️ 训练改进不明显 ({improvement:.4f})")
                else:
                    print(f"✅ 训练有明显改进 (+{improvement:.4f})")
    
    if issues:
        print("\n⚠️ 发现的问题:")
        for issue in issues:
            print(f"  {issue}")
    else:
        print("\n✅ 模型质量看起来正常")
    
    print("\n" + "=" * 60)
    
except Exception as e:
    print(f"❌ 模型检查失败: {e}")
    import traceback
    traceback.print_exc()

