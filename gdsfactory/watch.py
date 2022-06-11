import logging
import pathlib
import sys
import time
import traceback
from functools import partial
from typing import Optional

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from gdsfactory.config import cwd
from gdsfactory.pdk import get_active_pdk
from gdsfactory.read.from_yaml import from_yaml


class YamlEventHandler(FileSystemEventHandler):
    """Captures pic.yml events."""

    def __init__(self, logger=None, path: Optional[str] = None):
        super().__init__()

        self.logger = logger or logging.root
        pdk = get_active_pdk()
        pdk.register_cells_yaml(dirpath=path)

    def update_cell(self, src_path, update: bool = False) -> None:
        """Register new YAML file into active pdk.

        pdk.cells[filename] = partial(from_yaml, filepath)
        """
        pdk = get_active_pdk()
        filepath = pathlib.Path(src_path)
        cell_name = filepath.stem.split(".")[0]
        function = partial(from_yaml, filepath)
        try:
            pdk.register_cells_yaml(**{cell_name: function}, update=update)
        except ValueError as e:
            print(e)

    def on_moved(self, event):
        super().on_moved(event)

        what = "directory" if event.is_directory else "file"
        self.logger.info(
            "Moved %s: from %s to %s", what, event.src_path, event.dest_path
        )
        if what == "file" and event.dest_path.endswith(".pic.yml"):
            self.logger.info("Created %s: %s", what, event.src_path)
            self.update_cell(event.dest_path)
            self.get_component(event.src_path)

    def on_created(self, event):
        super().on_created(event)

        what = "directory" if event.is_directory else "file"
        if what == "file" and event.src_path.endswith(".pic.yml"):
            self.logger.info("Created %s: %s", what, event.src_path)
            self.update_cell(event.src_path)
            self.get_component(event.src_path)

    def on_deleted(self, event):
        super().on_deleted(event)

        what = "directory" if event.is_directory else "file"
        self.logger.info("Deleted %s: %s", what, event.src_path)

        if what == "file" and event.src_path.endswith(".pic.yml"):
            pdk = get_active_pdk()
            filepath = pathlib.Path(event.src_path)
            cell_name = filepath.stem.split(".")[0]
            pdk.remove_cell(cell_name)

    def on_modified(self, event):
        super().on_modified(event)

        what = "directory" if event.is_directory else "file"
        if what == "file" and event.src_path.endswith(".pic.yml"):
            self.logger.info("Modified %s: %s", what, event.src_path)
            self.get_component(event.src_path)

    def get_component(self, filepath):
        try:
            filepath = pathlib.Path(filepath)
            if filepath.exists():
                c = from_yaml(filepath)
                self.update_cell(filepath, update=True)
                c.show()
                # on_yaml_cell_modified.fire(c)
                return c
        except Exception as e:
            traceback.print_exc(file=sys.stdout)
            print(e)


def watch(path=str(cwd)) -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    event_handler = YamlEventHandler(path=path)
    observer = Observer()
    observer.schedule(event_handler, path, recursive=True)
    observer.start()
    logging.info(f"Observing {path!r}")
    try:
        while True:
            time.sleep(1)
    finally:
        observer.stop()
        observer.join()


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "."
    watch(path)
