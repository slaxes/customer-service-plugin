# -*- coding: utf-8 -*-

from typing import Union
from dataloader import Dataloader

class ModelInterface:
    '''
    模型接口 - 方便后台调用修改

    Note: 所有后续模型开发都应该以此接口类为父类。
    '''

    def __init__(self, dataloader: Dataloader):
        raise NotImplementedError()

    def train(self, **kwargs) -> None:
        '''
        训练过程

        Args:
        - kwargs: 训练控制参数
        '''
        raise NotImplementedError()

    def __call__(self, input_: str) -> Union[str, None]:
        '''
        Args:
        - input_: 来自用户的输入问题

        Return:
        模型应答 或 None
        '''
        raise NotImplementedError()


from .RegexModel import RegexModel
