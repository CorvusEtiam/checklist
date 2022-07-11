import sys 

from PySide6.QtCore import QCoreApplication, QAbstractListModel, Qt
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import QStyledItemDelegate
from PySide6.QtWidgets import QApplication, QWidget, QPushButton, QMainWindow, QListView, QVBoxLayout

def gui_setup():
    QCoreApplication.setApplicationName("Checklist")
    QCoreApplication.setOrganizationName("corvus_etiam.project.org")

class FlowModel(QAbstractListModel):
    def __init__(self, *args, flow_items = None, **kwargs) -> None:
        super(FlowModel, self).__init__(*args, **kwargs)
        self.items = flow_items or []
    
    def data(self, index, role):
        if role == Qt.DisplayRole:
            status, text = self.items[index.row()]
            return text  

    def rowCount(self, parent) -> int:
        return len(self.items)

class FlowItemDelegate(QStyledItemDelegate):
    def __init__(self):
        super().__init__()

    def paint(self, painter: QPainter, option, index) -> None:
        return super().paint(painter, option, index)

class App(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setGeometry(300, 300, 640, 480)
        self.setWindowTitle("Checklist")

        self.setup_ui()

    def setup_ui(self):
        self.model = FlowModel(flow_items=[(True, "one"), (True, "two"), (False, "three")])
        self._list_view = QListView()
        self._list_view.setModel(self.model)
        self._push_btn = QPushButton("Push it!")
        self._push_btn.setCheckable(True)
        self._push_btn.clicked.connect(self._push_btn_clicked_signal)
        
        self.vbox = QVBoxLayout()

        self.vbox.addWidget(self._list_view)
        self.vbox.addWidget(self._push_btn)
        
        container = QWidget()
        container.setLayout(self.vbox)
        
        self.setCentralWidget(container)

    def _push_btn_clicked_signal(self):
        print("Push it! Push it!")

def gui_start():
    gui_setup()
    app = QApplication(sys.argv)
    window = App()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    gui_start()