import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.table import Table
import numpy as np

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# ========== 表1: 应用场景技术需求对比表 ==========
fig1, ax1 = plt.subplots(figsize=(14, 8))
ax1.axis('tight')
ax1.axis('off')

data1 = [
    ['应用场景', '核心芯片类型', '主要技术需求', '典型芯片示例', '算力要求'],
    ['智能机器人', 'MCU/ASIC', '实时控制、多传感器融合', 'STM32系列、专用ASIC', '10-100 GOPS'],
    ['自动驾驶', 'AI加速器/SoC', '高性能计算、低延迟', '英伟达Orin、地平线征程', '200+ TOPS'],
    ['可穿戴设备', '低功耗MCU/SoC', '超低功耗、小型化', 'Arm Cortex-M系列', '<100 mW'],
    ['工业自动化', '工业MCU/FPGA', '高可靠性、实时性', 'TI C2000、Xilinx FPGA', '50-200 GOPS']
]

table1 = ax1.table(cellText=data1[1:], colLabels=data1[0], 
                   cellLoc='center', loc='center',
                   colWidths=[0.2, 0.2, 0.25, 0.2, 0.15])

table1.auto_set_font_size(False)
table1.set_fontsize(10)
table1.scale(1, 2.5)

# 设置表头样式
for i in range(len(data1[0])):
    table1[(0, i)].set_facecolor('#2E86AB')
    table1[(0, i)].set_text_props(weight='bold', color='white')

# 设置数据行样式
for i in range(1, len(data1)):
    for j in range(len(data1[0])):
        if i % 2 == 0:
            table1[(i, j)].set_facecolor('#F0F8FF')
        else:
            table1[(i, j)].set_facecolor('#FFFFFF')

plt.title('表1：集成电路在具身智能领域典型应用场景技术需求对比', 
          fontsize=14, fontweight='bold', pad=20)
plt.tight_layout()
plt.savefig('table1_应用场景对比.png', dpi=300, bbox_inches='tight')
plt.savefig('table1_应用场景对比.pdf', bbox_inches='tight')
print("✅ 表1已保存: table1_应用场景对比.png")

# ========== 表2: 技术需求详细指标表 ==========
fig2, ax2 = plt.subplots(figsize=(14, 8))
ax2.axis('tight')
ax2.axis('off')

data2 = [
    ['技术需求', '关键指标', '当前水平', '目标水平', '技术难点'],
    ['高性能计算', '算力密度', '100 GOPS/mm²', '500 GOPS/mm²', '散热、功耗控制'],
    ['高性能计算', '内存带宽', '100 GB/s', '500 GB/s', 'HBM集成、互连技术'],
    ['低功耗设计', '待机功耗', '10-50 mW', '<5 mW', '近阈值设计、DVFS'],
    ['低功耗设计', '能效比', '50 GOPS/W', '200 GOPS/W', '工艺优化、架构创新'],
    ['高集成度', '晶体管密度', '100M/mm²', '500M/mm²', '先进封装、3D集成'],
    ['高集成度', '功能集成度', '5-10个模块', '15-20个模块', '异构集成、Chiplet'],
    ['实时性', '响应延迟', '10-50 ms', '<5 ms', '硬件加速、流水线设计'],
    ['实时性', '确定性', '90%', '99.9%', '实时调度、优先级管理']
]

table2 = ax2.table(cellText=data2[1:], colLabels=data2[0], 
                   cellLoc='center', loc='center',
                   colWidths=[0.15, 0.2, 0.2, 0.2, 0.25])

table2.auto_set_font_size(False)
table2.set_fontsize(9)
table2.scale(1, 2.2)

# 设置表头样式
for i in range(len(data2[0])):
    table2[(0, i)].set_facecolor('#06A77D')
    table2[(0, i)].set_text_props(weight='bold', color='white')

# 设置数据行样式
for i in range(1, len(data2)):
    for j in range(len(data2[0])):
        if i % 2 == 0:
            table2[(i, j)].set_facecolor('#F0FFF0')
        else:
            table2[(i, j)].set_facecolor('#FFFFFF')

plt.title('表2：集成电路在具身智能领域核心技术需求详细指标', 
          fontsize=14, fontweight='bold', pad=20)
plt.tight_layout()
plt.savefig('table2_技术需求指标.png', dpi=300, bbox_inches='tight')
plt.savefig('table2_技术需求指标.pdf', bbox_inches='tight')
print("✅ 表2已保存: table2_技术需求指标.png")

# ========== 表3: 挑战分析表 ==========
fig3, ax3 = plt.subplots(figsize=(14, 8))
ax3.axis('tight')
ax3.axis('off')

data3 = [
    ['挑战类型', '具体表现', '影响程度', '解决难度', '应对策略'],
    ['制程工艺限制', '5nm以下量子效应显著', '极高', '极高', '新材料、新结构（GAA）'],
    ['制程工艺限制', '研发成本>10亿美元', '高', '高', 'Chiplet技术、成熟工艺复用'],
    ['异构集成复杂性', '多工艺节点协调困难', '高', '高', '标准化接口（UCIe）'],
    ['异构集成复杂性', '测试成本占30%+', '中', '中', '分层测试、自动化测试'],
    ['安全性与可靠性', '物理攻击防护需求', '极高', '中', '硬件安全模块、加密引擎'],
    ['安全性与可靠性', '极端环境适应性', '高', '中', '宽温设计、防护封装'],
    ['成本控制', '设计成本数千万美元', '高', '中', 'IP复用、开源工具'],
    ['成本控制', '先进制程制造费用高', '高', '高', '成熟工艺优化、Chiplet']
]

table3 = ax3.table(cellText=data3[1:], colLabels=data3[0], 
                   cellLoc='center', loc='center',
                   colWidths=[0.18, 0.25, 0.12, 0.12, 0.33])

table3.auto_set_font_size(False)
table3.set_fontsize(9)
table3.scale(1, 2.2)

# 设置表头样式
for i in range(len(data3[0])):
    table3[(0, i)].set_facecolor('#E63946')
    table3[(0, i)].set_text_props(weight='bold', color='white')

# 设置数据行样式
for i in range(1, len(data3)):
    for j in range(len(data3[0])):
        if i % 2 == 0:
            table3[(i, j)].set_facecolor('#FFF0F0')
        else:
            table3[(i, j)].set_facecolor('#FFFFFF')

plt.title('表3：集成电路在具身智能领域面临的主要挑战分析', 
          fontsize=14, fontweight='bold', pad=20)
plt.tight_layout()
plt.savefig('table3_挑战分析.png', dpi=300, bbox_inches='tight')
plt.savefig('table3_挑战分析.pdf', bbox_inches='tight')
print("✅ 表3已保存: table3_挑战分析.png")

# ========== 表4: 未来发展趋势对比表 ==========
fig4, ax4 = plt.subplots(figsize=(14, 8))
ax4.axis('tight')
ax4.axis('off')

data4 = [
    ['技术方向', '核心优势', '技术成熟度', '市场前景', '应用场景'],
    ['Chiplet技术', '模块化、成本低、灵活', '中等', '高（160亿美元/2025）', '高性能计算、AI加速'],
    ['存算一体架构', '能耗降低90%+', '较低', '中（45亿美元/2025）', '边缘AI、低功耗应用'],
    ['先进封装技术', '集成度高、性能提升', '较高', '高（120亿美元/2025）', '小型化、高性能'],
    ['神经形态计算', '超低功耗、事件驱动', '低', '低（15亿美元/2025）', '长期运行、感知任务'],
    ['AI硬件加速器', '计算效率高、专用优化', '高', '高（85亿美元/2025）', '深度学习、实时推理']
]

table4 = ax4.table(cellText=data4[1:], colLabels=data4[0], 
                   cellLoc='center', loc='center',
                   colWidths=[0.18, 0.25, 0.15, 0.22, 0.2])

table4.auto_set_font_size(False)
table4.set_fontsize(9)
table4.scale(1, 2.5)

# 设置表头样式
for i in range(len(data4[0])):
    table4[(0, i)].set_facecolor('#A23B72')
    table4[(0, i)].set_text_props(weight='bold', color='white')

# 设置数据行样式
for i in range(1, len(data4)):
    for j in range(len(data4[0])):
        if i % 2 == 0:
            table4[(i, j)].set_facecolor('#FFF0FF')
        else:
            table4[(i, j)].set_facecolor('#FFFFFF')

plt.title('表4：集成电路在具身智能领域未来发展趋势对比', 
          fontsize=14, fontweight='bold', pad=20)
plt.tight_layout()
plt.savefig('table4_发展趋势对比.png', dpi=300, bbox_inches='tight')
plt.savefig('table4_发展趋势对比.pdf', bbox_inches='tight')
print("✅ 表4已保存: table4_发展趋势对比.png")

# ========== 表5: 典型芯片参数对比表 ==========
fig5, ax5 = plt.subplots(figsize=(16, 8))
ax5.axis('tight')
ax5.axis('off')

data5 = [
    ['芯片型号', '应用领域', '算力', '功耗', '制程', '封装形式'],
    ['英伟达Orin', '自动驾驶', '254 TOPS', '60W', '8nm', 'FCBGA'],
    ['地平线征程5', '自动驾驶', '128 TOPS', '30W', '16nm', 'FCBGA'],
    ['Arm Cortex-M4', '可穿戴设备', '1.25 DMIPS/MHz', '<10mW', '28nm', 'QFN'],
    ['STM32H7', '工业控制', '480 DMIPS', '250mW', '40nm', 'LQFP'],
    ['Apple M2', '移动计算', '15.8 TOPS', '20W', '5nm', 'FCBGA'],
    ['华为昇腾310', 'AI推理', '16 TOPS', '8W', '12nm', 'FCBGA']
]

table5 = ax5.table(cellText=data5[1:], colLabels=data5[0], 
                   cellLoc='center', loc='center',
                   colWidths=[0.15, 0.15, 0.15, 0.15, 0.15, 0.25])

table5.auto_set_font_size(False)
table5.set_fontsize(9)
table5.scale(1, 2.5)

# 设置表头样式
for i in range(len(data5[0])):
    table5[(0, i)].set_facecolor('#F18F01')
    table5[(0, i)].set_text_props(weight='bold', color='white')

# 设置数据行样式
for i in range(1, len(data5)):
    for j in range(len(data5[0])):
        if i % 2 == 0:
            table5[(i, j)].set_facecolor('#FFF8F0')
        else:
            table5[(i, j)].set_facecolor('#FFFFFF')

plt.title('表5：具身智能领域典型集成电路芯片参数对比', 
          fontsize=14, fontweight='bold', pad=20)
plt.tight_layout()
plt.savefig('table5_芯片参数对比.png', dpi=300, bbox_inches='tight')
plt.savefig('table5_芯片参数对比.pdf', bbox_inches='tight')
print("✅ 表5已保存: table5_芯片参数对比.png")

print("\n✅ 所有表格已生成完成！")

