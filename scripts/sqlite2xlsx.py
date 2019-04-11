# -*- coding: utf-8 -*-

import sqlite3
import openpyxl as xl
from openpyxl.styles import Font as xlfont

import sys
import os


if not len(sys.argv) == 3:
    print('Usage: python sqlite2xlsx.py input_db output_xlsx')
    exit(-1)

input_db_path, output_xlsx_path = sys.argv[1:]

if not os.path.exists(input_db_path):
    print('"{}" not found!'.format(input_db_path))
    exit(-1)
if os.path.exists(output_xlsx_path):
    op = input('File "{}" already exists! Overwrite? [Y/n] '.format(output_xlsx_path))
    if op.lower() in 'y' or op.lower() == 'yes':
        pass
    else:
        exit(-1)


workbook = xl.Workbook()
worksheet = workbook.active
worksheet.title = 'xxxxxxx'
worksheet.cell(1, 1, value='主问题')
worksheet.cell(1, 2, value='标准答案')
worksheet.cell(1, 3, value='问法')
for cell in worksheet[1]:
    cell.font = xl.styles.Font(bold=True)

def get_first_empty_cell(ws, row: int):
    '''
    Note: 1-indexed.
    '''
    for idx, cell in enumerate(ws[row]):
        if cell.value is None:
            return idx + 1
    return len(ws[row]) + 1

with sqlite3.connect(input_db_path) as conn:
    # iter over main_ques
    cur = conn.execute('SELECT `id`, `ques`, `ans` FROM `main_ques`')
    main_ques = cur.fetchall()
    # row id in excel = id_ + 2
    for id_, ques, ans in main_ques:
        worksheet.cell(id_ + 2, 1, value=ques)
        worksheet.cell(id_ + 2, 2, value=ans)
    del main_ques
    # iter over sub_ques
    cur = conn.execute('SELECT `ques`, `main_ques_id` FROM `sub_ques`')
    sub_ques = cur.fetchall()
    for ques, main_ques_id in sub_ques:
        col_idx = get_first_empty_cell(worksheet, main_ques_id + 2)
        worksheet.cell(
            main_ques_id + 2,
            col_idx,
            value=ques
        )

workbook.save(output_xlsx_path)
