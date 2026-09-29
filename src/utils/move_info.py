import logging
import os
import pathlib
from typing import List

from attrs import define

from src.itemmodels.project_item import ItemInfo
from src.wiki.wiki_items import ItemType

@define(frozen=True)
class MoveInfo:
    paths_deleted: List[pathlib.Path]
    items_created: List[ItemInfo]
    src_items: List[pathlib.Path]
    dest: pathlib.Path

    @staticmethod
    def gen_move_info(src: list[pathlib.Path], dst: pathlib.Path) -> MoveInfo:
        items_created: List[ItemInfo] = []
        paths_removed: List[pathlib.Path] = []
        
        for item in src:
            if (p := item.parent) == dst:
                logging.warning("File %s is already contained in directory %s, skipping...", p, dst)
                continue
            
            if item.is_dir():
                for (root, _, files) in os.walk(item, topdown=False):
                    pl_root = pathlib.Path(root)
                    paths_removed.extend((pl_root / f for f in files))
                    paths_removed.append(pl_root)

                for (root, _, files) in os.walk(item, topdown=True):
                    pl_root = pathlib.Path(root)
                    items_created.append(ItemInfo(path=dst / pl_root.relative_to(item.parent), item_type=ItemType.FOLDER))
                    items_created.extend((ItemInfo(path=dst / pl_root.relative_to(item.parent) / f, item_type=ItemType.FILE) for f in files ))
            
            if item.is_file():
                paths_removed.append(item)
                items_created.append(ItemInfo(path=dst / item.name, item_type=ItemType.FILE))

        
        return MoveInfo(
            items_created=items_created,
            paths_deleted=paths_removed,
            src_items=src,
            dest=dst
        )

    def relative_to(self, path: pathlib.Path):
        return MoveInfo(
            paths_deleted=[p.relative_to(path) for p in self.paths_deleted],
            items_created=[ItemInfo(path=i.path.relative_to(path), item_type=i.item_type) for i in self.items_created],
            src_items=[p.relative_to(path) for p in self.src_items],
            dest = self.dest.relative_to(path)
        )