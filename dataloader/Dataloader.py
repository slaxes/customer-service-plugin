# -*- coding: utf-8 -*-

from typing import List, Union, Tuple

import pandas as pd
# import xlrd
import random


class Dataloader:
    '''
    基础 Excel dataloader

    Excel 表各列定义如下：
    | 主问题 | 标准答案 | 问法 1 | 问法 2 | 问法 3 | ...

    Note: 这里特地使用 `.xlsx` 格式数据而不选用 `.csv` 格式，因为数据中本身就可能
    带有英文逗号 `,`。

    Note: 这里没有分 batch，因为数据量本身比较小。
    '''

    @staticmethod
    def flatten_data(df: pd.DataFrame) -> List[Tuple[str, str, int]]:
        '''
        [内部方法] 将原始数据表中数据项压平

        Return:
            `[ ( 具体问法, 主问题, 答案编号 ) ]`

        Note: 主问题也算一种具体问法，加入数据中。
        '''
        retlist = []
        for row in df.itertuples():
            for ques_form in row[3:]:
                if pd.isnull(ques_form):
                    continue
                retlist.append((ques_form, row[1], row[0]))
            retlist.append((row[1], row[1], row[0]))        # 主问题也算作一种问法，加入数据中
        return retlist

    def __init__(self, filename: str, sheet_name: str):
        '''
        [构造函数]

        Args:
        - filename: Excel 数据文件路径
        - sheet_name: 数据表名称（'知识库'）
        '''
        df = pd.read_excel(filename, sheet_name=sheet_name)
        self._orig_df = df
        self._data_pool = Dataloader.flatten_data(df)
        self._answer_list = df['答案']

    def __len__(self) -> int:
        '''
        获取数据集大小
        '''
        return len(self._data_pool)

    @property
    def original_dataframe(self):
        '''
        [调试用] 获取未压平前的原始 `pd.DataFrame`
        '''
        return self._orig_df

    @property
    def flat_data(self):
        '''
        获取压平后的数据，格式如下：
        `[ ( 具体问法, 主问题, 答案编号 ) ]`
        '''
        return self._data_pool

    def sample(self, count: int=1) -> List[Tuple[str, str, str]]:
        '''
        随机获取数据

        Args:
        - count: batch 大小，默认为 1

        Return:
            `[ ( 具体问法, 主问题, 答案编号 ) ]`
        '''
        return random.sample(self._data_pool, count)

    def get_answer(self, main_ques_idx: int) -> str:
        '''
        根据 `答案编号` 获取对应答案内容
        '''
        return self._answer_list[main_ques_idx]

    def to_sqlite(self, path: str):
        '''
        Args:
        - path: 导出数据库地址

        数据库中将有以下几张表：
        1. `main_ques` - id : int : 主问题 ID | ques : str : 主问题 |
                         ans : str : 标准答案
        2. `sub_ques` - id : int : 问法 ID | ques : str : 问法 |
                        main_ques_id : str : 主问题 ID
        '''
        import os
        if os.path.exists(path):
            raise AssertionError("Database file at '{}' already exists!".format(path))
        import sqlite3
        with sqlite3.connect(path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS main_ques (
                    id      INTEGER     PRIMARY KEY,
                    ques    TEXT                        NOT NULL,
                    ans     TEXT                        NOT NULL
                )''')
            conn.execute('''
                CREATE TABLE IF NOT EXISTS sub_ques (
                    id              INTEGER     PRIMARY KEY     AUTOINCREMENT,
                    ques            TEXT                        NOT NULL,
                    main_ques_id    INTEGER                     NOT NULL
                )''')
            df = self.original_dataframe
            for row in df.itertuples():
                row_id, main_ques, ans = row[:3]
                conn.execute(
                    'INSERT INTO main_ques (id, ques, ans) VALUES (?,?,?)',
                    (row_id, main_ques, ans)
                )
                for sub_ques in row[3:]:
                    if pd.isnull(sub_ques):
                        continue
                    conn.execute(
                        'INSERT INTO sub_ques (ques, main_ques_id) VALUES (?,?)',
                        (sub_ques, row_id)
                    )
                conn.execute(
                    'INSERT INTO sub_ques (ques, main_ques_id) VALUES (?,?)',
                    (main_ques, row_id)
                )


'''Testing and Example'''

if __name__ == '__main__':
    loader = Dataloader('xxxxxxxxxxxxxxxxxxxxxxx', 'xxxxxxxxxxxx')
    print('数据集中一共有 {:d} 种问法。'.format(len(loader)))
    samp = loader.sample(3)
    print('从数据中共选取了 3 行：')
    for row in samp:
        print('问    法：  ' + row[0])
        print('主 问 题：  ' + row[1])
        print('对应标答：  ' + loader.get_answer(row[2]))
        print('')
    print('============================')
    loader.to_sqlite('xxxxxxxxxxxxxxxxxxxx')
