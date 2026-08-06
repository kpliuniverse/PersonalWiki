from dataclasses import dataclass
import logging
import os
import pathlib
from typing import List


@dataclass(frozen=True)
class MoveInfo:
    paths_deleted: List[pathlib.Path]
    paths_created: List[pathlib.Path]
    src_items: List[pathlib.Path]
    dest: pathlib.Path

    @staticmethod
    def gen_move_info(src: list[pathlib.Path], dst: pathlib.Path) -> MoveInfo:
        paths_created: List[pathlib.Path] = []
        paths_removed: List[pathlib.Path] = []
        
        for item in src:
            if (p := item.parent) == dst:
                logging.warning("File %s is already contained in directory %s, skipping...", p, dst)
                continue
            
            if item.is_dir():
                for (root,_,files) in os.walk(item, topdown=False):
                    pl_root = pathlib.Path(root)
                    paths_removed.extend((pl_root / f for f in files))
                    paths_removed.append(pl_root)

                for (root,_,files) in os.walk(item, topdown=True):       
                    pl_root = pathlib.Path(root)       
                    paths_created.append(dst / pl_root.relative_to(item.parent))
                    paths_created.extend((dst / pl_root.relative_to(item.parent) / f for f in files ))
            if item.is_file():
                paths_removed.append(item)
                paths_created.append(dst / item.name)

        
        return MoveInfo(
            paths_created=paths_created,
            paths_deleted=paths_removed,
            src_items=src,
            dest=dst
        )