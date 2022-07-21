import sys 
from PySide6.QtCore import QCoreApplication, QAbstractTableModel, Qt, QModelIndex
from PySide6.QtGui import QColor, QAction, QIcon
from PySide6.QtWidgets import QLabel, QHeaderView, QStyle, QStyledItemDelegate, QFileDialog
from PySide6.QtWidgets import QApplication, QWidget, QPushButton, QMainWindow, QTableView, QVBoxLayout
from checklist.flow import Checklist, ChecklistLoadingError, LevelInfo, ProgressInfo, Step 

from checklist import resources

def gui_setup():
    QCoreApplication.setApplicationName("Lista Zadań")
    QCoreApplication.setOrganizationName("corvus_etiam.project.org")

class FlowModel(QAbstractTableModel):   
    def __init__(self, items = None) -> None:
        super(FlowModel, self).__init__()
        self._data = items or []
        
    def headerData(self, section: int, orientation, role):
        if role != Qt.DisplayRole:
            return None
        if orientation != Qt.Horizontal:
            return str(section + 1)
        if section == 0:
            return "Imp."
        elif section == 1:
            return "Opis"
        elif section == 2:
            return "Status"

    def loadData(self, data):
        self.beginRemoveRows(QModelIndex(), 0, len(self._data))
        self._data = []
        self.endRemoveRows()
        self.beginInsertRows(QModelIndex(), 0, len(data) - 1)
        self._data = data 
        self.endInsertRows()
        self.dataChanged.emit(self.index(0, 0), self.index(len(data), self.columnCount()))

    def clearUp(self):
        for row in self._data:
            row[2] = ProgressInfo.Waiting
        self._data[0][2] = ProgressInfo.Active

    def data(self, index, role):
        if role == Qt.DisplayRole and index.column() == 1:
            return self._data[index.row()][1]
        elif role == Qt.DecorationRole:
            # | importance | label | status |
            if index.column() == 2:
                kind = self._data[index.row()][index.column()]
                if kind == ProgressInfo.Active:
                    return QColor("cyan")
                elif kind == ProgressInfo.Waiting:
                    return QColor("red")
                elif kind == ProgressInfo.Finished:
                    return QColor("green")
            
            elif index.column() == 0:
                level = self._data[index.row()][0]
                if level == LevelInfo.Required:
                    return QIcon(":/icons/required")
                elif level == LevelInfo.Optional:
                    return QIcon(":/icons/optional")
                
    def rowCount(self, index = QModelIndex()) -> int:
        _ = index
        return len(self._data)
    
    def columnCount(self, parent = ...) -> int:
        _ = parent
        if len(self._data) == 0:
            return 3
        return len(self._data[0])

    def setData(self, index, value, role = Qt.DisplayRole) -> bool:
        self._data[index.row()] = value 
        left = self.index(index.row(), 0)
        right = self.index(index.row(), 3)
        self.dataChanged.emit(left, right)

    def stepForward(self):
        last_item = None
        for idx, row in enumerate(self._data):
            if row[2] == ProgressInfo.Active:
                last_item = idx
                break 
        if last_item == None:
            return False
        row = self._data[last_item]
        if last_item == self.rowCount() - 1:
            self.setData(self.index(last_item, 0), [ row[0], row[1], ProgressInfo.Finished ])
            return False
        else:
            self.setData(self.index(last_item, 0), [ row[0], row[1], ProgressInfo.Finished ])
            next_row = self._data[last_item + 1]
            self.setData(self.index(last_item + 1, 0), [ next_row[0], next_row[1], ProgressInfo.Active ])
            return True


# FIXME: Center colored block with QStyledDelegateItem


class App(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setGeometry(300, 300, 640, 480)
        self.setWindowTitle("Lista Zadań")
        self.setup_menu()
        self.setup_ui()

        self._current_flow = None 
        self._finished = False

    def _load_action(self):
        # load saved flow
        pass
     
    def _open_action(self):
        path, filter = QFileDialog.getOpenFileName(self, "Open Flow File", ".", "Txt Files (*.txt)")
        if path is None:
            return
        # path = "./tests/flow.txt" # for testing 
        try: 
            flow = Checklist.from_file(path)
            self._current_flow = flow 
            self._title_label.setText(flow.title)
            self._title_label.setAlignment(Qt.AlignCenter | Qt.AlignBaseline)
            data  = [ [ step.level, step.label, step.state ] for step in flow.steps ]
            self.flow_model.loadData(data)    
        except ChecklistLoadingError as cle:
            print(f"Error while loading checklist from file: {path}: {cle.message}")
        
    def _save_action(self):
        pass

    def setup_menu(self):
        menu = self.menuBar()
        file_menu = menu.addMenu("File")
        
        open_action = QAction("Open", self)
        open_action.setShortcut("Ctrl-O")
        open_action.triggered.connect(self._open_action)
        
        load_action = QAction("Load", self)
        load_action.setShortcut("Ctrl-L")
        load_action.triggered.connect(self._load_action)

        save_action = QAction("Save", self)
        save_action.setShortcut("Ctrl-S")
        save_action.triggered.connect(self._save_action)
        

        exit_action = QAction("Exit", self)
        exit_action.setShortcut("Ctrl-Q")
        exit_action.triggered.connect(lambda: self.close())


        file_menu.addAction(open_action)
        file_menu.addAction(load_action)
        file_menu.addAction(save_action)
        file_menu.addSeparator()
        file_menu.addAction(exit_action)

    def setup_ui(self):
        self.flow_model = FlowModel()
        self._title_label = QLabel()
        self._title_label.setText("")
        self._tbl_view = QTableView()
        self._tbl_view.setModel(self.flow_model)
        self._tbl_view.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        # self._tbl_view.setItemDelegateForColumn(0, FlagDelegate())
        # self._tbl_view.setItemDelegateForColumn(2, FlagDelegate())
        # fnt = self._tbl_view.font()
        # fnt.setPointSize(fnt.pointSize() * 1.25)
        # self._list_view.setFont(fnt)

        self._push_btn = QPushButton("Load")
        self._push_btn.setCheckable(True)
        self._push_btn.clicked.connect(self._push_btn_clicked_signal)
        
        self.vbox = QVBoxLayout()
        self.vbox.addWidget(self._title_label)
        self.vbox.addWidget(self._tbl_view)
        self.vbox.addWidget(self._push_btn)
        
        container = QWidget()
        container.setLayout(self.vbox)
        
        self.setCentralWidget(container)

    def _push_btn_clicked_signal(self):
        if self._current_flow == None:
            self._open_action() 
            self._push_btn.setText("Next Step")
        
        if self._finished:
            self.flow_model.clearUp()
            self.flow_model.layoutChanged.emit()
            self._finished = False
            self._push_btn.setText("Next")
            return 

        if not self.flow_model.stepForward():
            self._push_btn.setText("Finished. Again?")
            self._finished = True
            

def gui_start():
    gui_setup()
    app = QApplication(sys.argv)
    window = App()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    gui_start()