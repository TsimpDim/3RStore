from typing import List
from anytree import NodeMixin

class BaseResource():

    def __init__(self, title:str, link:str, tags:List):
        self.title = title
        self.link = link
        self.tags = tags

class MixinResource(BaseResource, NodeMixin):
    def __init__(self, title:str, link:str, tags:List, name:str, length:int, width:int, parent=None):
        super().__init__(title, link, tags)
        self.name = name
        self.length = length
        self.width = width
        self.parent = parent