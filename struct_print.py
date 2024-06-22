# Date    : 2024/6/22 16:23
# File    : struct_print.py
# Desc    : 
# Author  : Damon
# E-mail  : bingzhenli@hotmail.com


import os
import os.path


def validate_directory(directory):
    """
    验证目录的安全性。
    """
    if not os.path.isdir(directory):
        raise ValueError(f"{directory} is not a valid directory.")
    if '..' in directory.split(os.path.sep):
        raise ValueError(f"{directory} contains invalid path components.")


def dfs_showdir(directory, level):
    """
    递归显示目录结构。 
    """
    try:
        items = os.listdir(directory)
    except PermissionError:
        print(f"Permission denied: {directory}")
        return
    except OSError as e:
        print(f"Error occurred while listing directory {directory}: {e}")
        return

    if level == 0:
        print(f"root:[{directory}]")

    # 将items分为文件夹和文件两部分，并分别排序
    dirs = sorted([item for item in items if os.path.isdir(os.path.join(directory, item))])
    files = sorted([item for item in items if os.path.isfile(os.path.join(directory, item))])

    # 先打印文件夹
    for item in dirs:
        if '.git' not in item and '.idea' not in item:
            new_item = os.path.join(directory, item)
            print("|      " * level + "+--" + item)
            if os.path.isdir(new_item):
                dfs_showdir(new_item, level + 1)

    # 再打印文件
    for item in files:
        if '.git' not in item and '.idea' not in item:
            print("|      " * level + "+--" + item)


if __name__ == '__main__':
    project_dir = '.'
    lvl = 0
    validate_directory(project_dir)
    dfs_showdir(project_dir, lvl)
