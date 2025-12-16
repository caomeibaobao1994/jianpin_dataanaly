# -*- coding: utf-8 -*-
"""
大文件合并工具 - 支持GB级文件，内存友好
适用于：每个文件1GB，共70个文件（总计70GB）
支持格式：Excel (.xlsx, .xls), CSV (.csv), Stata (.dta)
"""

import pandas as pd
import os
import glob

# 尝试导入pyreadstat（更好的Stata支持）
try:
    import pyreadstat
    HAS_PYREADSTAT = True
except ImportError:
    HAS_PYREADSTAT = False
    print("⚠️  提示: 安装 pyreadstat 可以获得更好的Stata文件支持")
    print("   安装命令: pip install pyreadstat")

def merge_large_files(input_dir="test_data", output_file="merged.csv", chunksize=10000):
    """
    使用分块处理合并大文件，内存友好
    
    参数:
        input_dir: 输入目录
        output_file: 输出文件（建议使用.csv格式，更快）
        chunksize: 每次处理的行数（根据内存调整，默认10000行）
    
    注意：
        - 大文件建议输出为CSV格式（比Excel快很多）
        - 如果必须用Excel，文件不能超过1,048,576行
    """
    
    # 查找所有文件
    files = glob.glob(os.path.join(input_dir, "*.xlsx")) + \
            glob.glob(os.path.join(input_dir, "*.xls")) + \
            glob.glob(os.path.join(input_dir, "*.csv")) + \
            glob.glob(os.path.join(input_dir, "*.dta"))
    
    files.sort()
    
    if len(files) == 0:
        print(f"❌ 在 {input_dir} 中没有找到文件")
        return
    
    # 统计文件类型
    file_types = {'Excel': 0, 'CSV': 0, 'Stata': 0}
    for f in files:
        if f.endswith('.dta'):
            file_types['Stata'] += 1
        elif f.endswith('.csv'):
            file_types['CSV'] += 1
        else:
            file_types['Excel'] += 1
    
    print(f"找到 {len(files)} 个文件")
    if file_types['Stata'] > 0:
        print(f"  - Stata文件: {file_types['Stata']} 个")
    if file_types['Excel'] > 0:
        print(f"  - Excel文件: {file_types['Excel']} 个")
    if file_types['CSV'] > 0:
        print(f"  - CSV文件: {file_types['CSV']} 个")
    print(f"使用分块处理，每批 {chunksize} 行")
    print(f"输出文件: {output_file}\n")
    
    total_rows = 0
    first_chunk = True
    
    # 逐个文件处理
    for idx, file in enumerate(files, 1):
        print(f"[{idx}/{len(files)}] 处理: {os.path.basename(file)}")
        
        try:
            # Stata文件：分块读取
            if file.endswith('.dta'):
                print(f"    正在读取Stata文件...")
                
                # 读取Stata文件
                if HAS_PYREADSTAT:
                    # 使用pyreadstat（更快，支持更多特性）
                    df, meta = pyreadstat.read_dta(file)
                else:
                    # 使用pandas（基础支持）
                    df = pd.read_stata(file)
                
                file_rows = len(df)
                print(f"    文件包含 {file_rows:,} 行，开始分块写入...")
                
                # 分块处理
                for start in range(0, file_rows, chunksize):
                    end = min(start + chunksize, file_rows)
                    chunk = df.iloc[start:end]
                    
                    mode = 'w' if first_chunk else 'a'
                    header = first_chunk
                    
                    if output_file.endswith('.csv'):
                        chunk.to_csv(output_file, mode=mode, header=header, 
                                   index=False, encoding='utf-8-sig')
                    else:
                        if first_chunk:
                            chunk.to_excel(output_file, index=False)
                        else:
                            with pd.ExcelWriter(output_file, mode='a', engine='openpyxl', 
                                              if_sheet_exists='overlay') as writer:
                                chunk.to_excel(writer, index=False, header=False, 
                                             startrow=total_rows)
                    
                    first_chunk = False
                    total_rows += len(chunk)
                    
                    if (end - start) > 0 and end % (chunksize * 10) == 0:
                        print(f"    已处理 {end:,}/{file_rows:,} 行")
            
            # CSV文件：分块读取
            elif file.endswith('.csv'):
                reader = pd.read_csv(file, chunksize=chunksize, encoding='utf-8-sig', 
                                    on_bad_lines='skip', low_memory=False)
                
                for chunk_num, chunk in enumerate(reader, 1):
                    # 第一次写入时创建文件（包含表头）
                    # 后续追加时不写表头
                    mode = 'w' if first_chunk else 'a'
                    header = first_chunk
                    
                    if output_file.endswith('.csv'):
                        chunk.to_csv(output_file, mode=mode, header=header, 
                                   index=False, encoding='utf-8-sig')
                    else:
                        # Excel格式需要特殊处理（不推荐大文件用Excel）
                        if first_chunk:
                            chunk.to_excel(output_file, index=False)
                        else:
                            with pd.ExcelWriter(output_file, mode='a', engine='openpyxl') as writer:
                                chunk.to_excel(writer, index=False, header=False)
                    
                    first_chunk = False
                    total_rows += len(chunk)
                    
                    if chunk_num % 10 == 0:
                        print(f"    已处理 {chunk_num} 批，累计 {total_rows:,} 行")
            
            # Excel文件：分块读取（需要先转换）
            else:
                # Excel不支持原生分块读取，需要分批处理
                print(f"    正在读取Excel文件...")
                
                # 对于超大Excel文件，使用 iter_rows 或分批读取
                df = pd.read_excel(file, engine='openpyxl')
                file_rows = len(df)
                print(f"    文件包含 {file_rows:,} 行，开始分块写入...")
                
                # 分块处理
                for start in range(0, file_rows, chunksize):
                    end = min(start + chunksize, file_rows)
                    chunk = df.iloc[start:end]
                    
                    mode = 'w' if first_chunk else 'a'
                    header = first_chunk
                    
                    if output_file.endswith('.csv'):
                        chunk.to_csv(output_file, mode=mode, header=header, 
                                   index=False, encoding='utf-8-sig')
                    else:
                        if first_chunk:
                            chunk.to_excel(output_file, index=False)
                        else:
                            # Excel追加写入（有行数限制）
                            with pd.ExcelWriter(output_file, mode='a', engine='openpyxl', 
                                              if_sheet_exists='overlay') as writer:
                                chunk.to_excel(writer, index=False, header=False, 
                                             startrow=total_rows)
                    
                    first_chunk = False
                    total_rows += len(chunk)
                    
                    if (end - start) > 0 and end % (chunksize * 10) == 0:
                        print(f"    已处理 {end:,}/{file_rows:,} 行")
                
            print(f"  ✓ 完成，累计总行数: {total_rows:,}\n")
            
        except Exception as e:
            print(f"  ❌ 处理失败: {str(e)}\n")
            continue
    
    print(f"{'='*60}")
    print(f"✅ 合并完成！")
    print(f"{'='*60}")
    print(f"输出文件: {os.path.abspath(output_file)}")
    print(f"总文件数: {len(files)}")
    print(f"总行数: {total_rows:,}")
    print(f"文件大小: {os.path.getsize(output_file) / (1024**2):.2f} MB")

def quick_merge_stata_only(input_dir="test_data", output_file="merged.csv", chunksize=50000):
    """
    仅合并Stata文件的快速版本（推荐用于Stata数据）
    
    特点：
    1. 只处理Stata (.dta) 文件
    2. 使用更大的chunk size
    3. 自动处理Stata格式特性
    """
    files = glob.glob(os.path.join(input_dir, "*.dta"))
    files.sort()
    
    if len(files) == 0:
        print(f"❌ 在 {input_dir} 中没有找到Stata文件")
        return
    
    print(f"找到 {len(files)} 个Stata文件")
    print(f"快速合并模式 (chunk size: {chunksize})\n")
    
    total_rows = 0
    first_file = True
    
    for idx, file in enumerate(files, 1):
        print(f"[{idx}/{len(files)}] {os.path.basename(file)}", end=" ... ")
        
        try:
            # 读取Stata文件
            if HAS_PYREADSTAT:
                df, meta = pyreadstat.read_dta(file)
            else:
                df = pd.read_stata(file)
            
            file_rows = len(df)
            
            # 分块处理
            for start in range(0, file_rows, chunksize):
                end = min(start + chunksize, file_rows)
                chunk = df.iloc[start:end]
                
                if output_file.endswith('.csv'):
                    chunk.to_csv(output_file, mode='w' if first_file else 'a', 
                                header=first_file, index=False, encoding='utf-8-sig')
                else:
                    if first_file:
                        chunk.to_excel(output_file, index=False)
                    else:
                        with pd.ExcelWriter(output_file, mode='a', engine='openpyxl', 
                                          if_sheet_exists='overlay') as writer:
                            chunk.to_excel(writer, index=False, header=False, 
                                         startrow=total_rows)
                
                first_file = False
                total_rows += len(chunk)
            
            print(f"✓ 累计 {total_rows:,} 行")
        except Exception as e:
            print(f"❌ 处理失败: {str(e)}")
            continue
    
    print(f"\n✅ 完成！共 {total_rows:,} 行，保存到: {output_file}")

def quick_merge_csv_only(input_dir="test_data", output_file="merged.csv", chunksize=50000):
    """
    仅合并CSV文件的极速版本（推荐用于超大数据）
    
    这是最快的方式：
    1. 只处理CSV文件
    2. 使用更大的chunk size
    3. 直接追加，不做任何转换
    """
    files = glob.glob(os.path.join(input_dir, "*.csv"))
    files.sort()
    
    print(f"找到 {len(files)} 个CSV文件")
    print(f"快速合并模式 (chunk size: {chunksize})\n")
    
    total_rows = 0
    first_file = True
    
    for idx, file in enumerate(files, 1):
        print(f"[{idx}/{len(files)}] {os.path.basename(file)}", end=" ... ")
        
        # 分块读取并追加
        for chunk in pd.read_csv(file, chunksize=chunksize, encoding='utf-8-sig', 
                                low_memory=False):
            chunk.to_csv(output_file, mode='w' if first_file else 'a', 
                        header=first_file, index=False, encoding='utf-8-sig')
            first_file = False
            total_rows += len(chunk)
        
        print(f"✓ 累计 {total_rows:,} 行")
    
    print(f"\n✅ 完成！共 {total_rows:,} 行，保存到: {output_file}")

if __name__ == "__main__":
    # 方式1：标准方式（支持Excel和CSV混合）
    merge_large_files(
        input_dir="test_data",
        output_file="merged_large.csv",  # 大文件强烈建议用CSV
        chunksize=10000  # 根据内存调整：内存大可设置50000-100000
    )
    
    # 方式2：仅CSV文件的极速版本（最快）
    # quick_merge_csv_only(
    #     input_dir="test_data",
    #     output_file="merged_fast.csv",
    #     chunksize=50000
    # )

