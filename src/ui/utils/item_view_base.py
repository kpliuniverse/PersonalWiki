from PyQt6.QtWidgets import QWidget


class BaseItemView(QWidget):
    def on_leave(self) -> None:
        """
            Triggered when the view leaves for another one that is of different type.
        """

    def on_enter(self) -> None:
        """
            Triggered when another view of different type leaves for this type.
        """

