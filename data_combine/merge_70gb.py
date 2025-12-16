# -*- coding: utf-8 -*-
"""
专门针对70个1GB文件的合并脚本
支持格式：Excel (.xlsx, .xls), CSV (.csv), Stata (.dta)
直接运行即可，已优化性能参数
"""

from large_file_merge import merge_large_files, quick_merge_stata_only, quick_merge_csv_only
import sys

def main():
    print("="*70)
    print("  大文件合并工具 - 针对70GB数据优化")
    print("="*70)
    print()
    print("📊 预期场景：70个文件，每个约1GB")
    print("📁 支持格式：Excel (.xlsx, .xls), CSV (.csv), Stata (.dta)")
    print("⏱️  预计时间：2-3小时")
    print("💾 内存需求：建议8GB以上")
    print()
    
    # 配置参数 - 根据您的实际情况修改
    INPUT_DIR = "test_data"           # ← 改成您的文件夹路径
    OUTPUT_FILE = "merged_70gb.csv"   # ← 输出文件名（必须是.csv）
    CHUNKSIZE = 30000                 # ← 根据内存调整：4GB用10000，8GB用30000，16GB用50000
    
    print(f"📁 输入目录：{INPUT_DIR}")
    print(f"📄 输出文件：{OUTPUT_FILE}")
    print(f"🔧 分块大小：{CHUNKSIZE} 行/批")
    print()
    
    # 确认
    response = input("确认开始处理？(yes/no): ").strip().lower()
    if response != 'yes':
        print("已取消")
        sys.exit(0)
    
    print()
    print("="*70)
    print("开始处理...")
    print("="*70)
    print()
    
    try:
        # 方式1：标准方式（支持Excel、CSV、Stata混合）
        merge_large_files(
            input_dir=INPUT_DIR,
            output_file=OUTPUT_FILE,
            chunksize=CHUNKSIZE
        )
        
        # 方式2：如果全是Stata文件，取消下面的注释使用快速版本
        # quick_merge_stata_only(
        #     input_dir=INPUT_DIR,
        #     output_file=OUTPUT_FILE,
        #     chunksize=50000
        # )
        
        # 方式3：如果全是CSV文件，取消下面的注释使用极速版本
        # quick_merge_csv_only(
        #     input_dir=INPUT_DIR,
        #     output_file=OUTPUT_FILE,
        #     chunksize=50000
        # )
        
    except Exception as e:
        print(f"\n❌ 处理出错: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    print()
    print("="*70)
    print("🎉 全部完成！")
    print("="*70)

if __name__ == "__main__":
    main()

