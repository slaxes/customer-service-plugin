# -*- coding: utf-8 -*-

from typing import Union, List, Tuple

import sqlite3


class RecallData:
    '''
    召回数据维护

    被召回的数据将统一存放到 `dbfile` 指明的 SQLite 数据库文件中，其中
    -   `recall` 表存放待打标数据；
    -   `labeled` 表存放已打标，待加回训练集中的数据。
    _（数据表定义见 `RecallData.__init__()`）_

    对已打标的数据可能至少有以下几种情况：
    -   该问题为新的主问题，答案也为新答案；
    -   训练集中已有该问题的主问题，为新的问法，答案在原训练集中；
    -   该问题为新的主问题，答案也为新答案，但 `recall` 表或 `labeled` 表中有
        类似问题。

    为了避免数据集中冗余存放主问题/答案，可能需要在合并的时候进行相似度匹配。而
    且，若该服务后期需要正规化，现有的 Excel 表格肯定不是理想的存放训练数据的解
    决方案。故这里暂不提供自动化增量式合并数据集的方法，仍需要手工进行合并操作。

    该类支持通过 `with` 块来实现对数据库文件的持久连接，也可以单独使用（但每次方法
    调用都会隐式连接数据库文件）。

    TODO: Lazy-commit。
    '''

    def __init__(self, dbfile: str):
        self.dbfile = dbfile
        with sqlite3.connect(self.dbfile) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS recall (
                    id      INTEGER PRIMARY KEY     AUTOINCREMENT,
                    ques    TEXT                    NOT NULL
                )''')
            conn.execute('''
                CREATE TABLE IF NOT EXISTS labeled (
                    ques    TEXT                    NOT NULL,
                    ans     TEXT                    NOT NULL
                )''')
        self.conn = None    # 持久链接

    def __enter__(self):
        self.conn = sqlite3.connect(self.dbfile)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # NOTE: only commit writes to file on error-free
        if exc_type is not None:
            print('RecallData: Something went wrong! Discarding changes!')
        else:
            self.conn.commit()
        self.conn.close()
        self.conn = None

    def commit(self):
        '''
        显式应用更改（仅持久连接模式时有效）。
        '''
        if self.conn:
            self.conn.commit()
        else:
            print('RecallData.commit(): No context available!')

    def print_all(self) -> None:
        '''
        [调试] 列出数据库中所有数据。
        '''
        with self.conn or sqlite3.connect(self.dbfile) as conn:
            print('Listing `recall`...')
            cur = conn.execute('SELECT * FROM recall')
            rows = cur.fetchall()
            for row in rows:
                print('  ', row)
            print('Listing `labeled`...')
            cur = conn.execute('SELECT * FROM labeled')
            rows = cur.fetchall()
            for row in rows:
                print('  ', row)

    def recall(self, ques: str) -> None:
        '''
        将该问法加入 `recall` 表中。

        Args:
        -   ques 有问题的问法
        '''
        with self.conn or sqlite3.connect(self.dbfile) as conn:
            conn.execute('INSERT INTO recall (ques) VALUES (?)', (ques,))

    def sample_from_recall(self) -> Tuple[int, str]:
        '''
        从 `recall` 表中取一条出来打标。

        NOTE: 这里 naiively 取 `recall` 中第一条。

        Return:
        `( id_in_recall , ques )`
        其中，`id_in_recall` 用以传给 `RecallData.label()` 方法，以移除该
        条记录。
        '''
        with self.conn or sqlite3.connect(self.dbfile) as conn:
            cur = conn.execute('SELECT id, ques FROM recall LIMIT 1')
            return cur.fetchone()

    def _label_id(self, id_: int, ans: str, no_commit: bool) -> bool:
        with self.conn or sqlite3.connect(self.dbfile) as conn:
            cur = conn.execute('SELECT ques FROM recall WHERE id = ? LIMIT 1', (id_,))
            ques = cur.fetchone()
            if ques is None:
                return False
            ques = ques[0]
            conn.execute('DELETE FROM recall WHERE id = ?', (id_,))
            conn.execute('INSERT INTO labeled (ques, ans) VALUES (?,?)', (ques, ans))
            # if not no_commit:
            #     conn.commit()
        return True

    def _label_ques(self, ques: str, ans: str, no_commit: bool) -> None:
        with self.conn or sqlite3.connect(self.dbfile) as conn:
            conn.execute('INSERT INTO labeled (ques, ans) VALUES (?,?)', (ques, ans))
            # if not no_commit:
            #     conn.commit()

    def label(self, id_ques: Union[int, str], ans: str, no_commit: bool=False) -> bool:
        '''
        `id_ques` 为
        -   `int`，将该条打标后的数据从 `recall` 表中移出，并加
            入到 `labeled` 表中。
        -   `str`，将该问法与答案直接加入到 `labeled` 表中。

        Args:
        -   id_ques `recall` 表中问题的 `id` | 新问法
        -   ans 正确答案
        -   no_commit [暂未使用] 不显式调用 `Connection.commit()` 方
            法，可在后期某一时间点集中调用 `RecallData.commit()`，减少
            I/O 次数（默认为 `False`）

        Return:
        当 `id_ques` 为 `int` 且在 `recall` 表中找不到该记录时
        返回 `False`，其余时候返回 `True`。
        '''
        if isinstance(id_ques, int):
            return self._label_id(id_ques, ans, no_commit)
        elif isinstance(id_ques, str):
            self._label_ques(id_ques, ans, no_commit)
            return True
        raise TypeError('id_ques')


'''Unit Test'''

if __name__ == '__main__':
    dbfile = './test_some-salty-string-you-dont-have-in-this-directory.db'

    with RecallData(dbfile=dbfile) as recall:
        # insert 2 records for test
        recall.recall('在？刷猛汉王吗？')
        recall.recall('在？喜之郎了解一下？')
        recall.print_all()
        print('')

        # get sample and label it
        sample = recall.sample_from_recall()
        print('recall.sample_from_recall() ->', sample)

        # label the sample (via the internal id)
        recall.label(sample[0], 'lei了老弟！')
        recall.print_all()
        print('')

        # direct label no recall stage (via question string)
        recall.label('五月是天！', '三玖天外飞仙！')
        recall.print_all()
        print('')

    # tear-down test env
    import os
    os.remove(dbfile)
