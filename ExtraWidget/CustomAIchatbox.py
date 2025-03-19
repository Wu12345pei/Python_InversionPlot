from Qt import QtCore, QtWidgets, QtGui

class CustomAIchatbox(QtWidgets.QWidget):
    text_submit = QtCore.Signal(str)
    node_selected = QtCore.Signal(str)  # 新增信号，用于节点选择

    def __init__(self, parent=None):
        super(CustomAIchatbox, self).__init__(parent)
        self.setupUi()
        self.animation = QtCore.QPropertyAnimation(self, b"geometry")  # 动画对象
        self.animation.setDuration(300)  # 动画持续时间（毫秒）

    def setupUi(self):
        self.setObjectName("CustomAIchatbox")
        self.resize(400, 400)  # 调整窗口高度
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)  # 去掉默认标题栏
        self.setStyleSheet("background-color: #1e1e1e; color: #ffffff;")  # 黑色背景，白色文字

        self.verticalLayout = QtWidgets.QVBoxLayout(self)
        self.verticalLayout.setObjectName("verticalLayout")

        # 自定义标题栏
        self.titleBar = QtWidgets.QWidget(self)
        self.titleBar.setObjectName("titleBar")
        self.titleBar.setStyleSheet("background-color: #1e1e1e; color: #ffffff;")
        self.titleBarLayout = QtWidgets.QHBoxLayout(self.titleBar)
        self.titleBarLayout.setContentsMargins(0, 0, 0, 0)

        # 标题文字
        self.titleLabel = QtWidgets.QLabel("AI Chatbox", self.titleBar)
        self.titleLabel.setStyleSheet("color: #ffffff; padding: 5px;")
        self.titleBarLayout.addWidget(self.titleLabel)

        # 关闭按钮
        self.closeButton = QtWidgets.QPushButton("X", self.titleBar)
        self.closeButton.setFixedSize(20, 20)
        self.closeButton.setStyleSheet("background-color: #d3d3d3; color: #ffffff; border: none;")
        self.closeButton.clicked.connect(self.on_close_button_clicked)
        self.titleBarLayout.addWidget(self.closeButton)

        self.verticalLayout.addWidget(self.titleBar)  # 将标题栏添加到主布局

        # 节点按钮区域
        self.nodeButtonArea = QtWidgets.QWidget(self)
        self.nodeButtonArea.setObjectName("nodeButtonArea")
        self.nodeButtonArea.setStyleSheet("background-color: #2d2d2d; border: 1px solid #3c3c3c;")
        self.nodeButtonLayout = QtWidgets.QVBoxLayout(self.nodeButtonArea)
        self.nodeButtonLayout.setObjectName("nodeButtonLayout")
        self.verticalLayout.addWidget(self.nodeButtonArea, stretch=1)  # 节点按钮区域占据上方所有空间

        # 底部输入区域
        self.inputLayout = QtWidgets.QHBoxLayout()
        self.inputLayout.setObjectName("inputLayout")

        # 用户输入框
        self.textEdit = QtWidgets.QLineEdit(self)
        self.textEdit.setObjectName("textEdit")
        self.textEdit.setStyleSheet("background-color: #2d2d2d; color: #ffffff; border: 1px solid #3c3c3c;")
        self.textEdit.setFixedHeight(20)  # 固定高度为 20
        self.inputLayout.addWidget(self.textEdit, stretch=1)

        # 提交按钮
        self.pushButton = QtWidgets.QPushButton(self)
        self.pushButton.setObjectName("pushButton")
        self.pushButton.setStyleSheet("background-color: #3c3c3c; border: none; padding: 5px;")
        self.pushButton.setFixedHeight(20)  # 高度与输入框一致
        self.pushButton.setFixedWidth(60)  # 固定宽度

        # 设置提交按钮图标
        send_icon = QtGui.QIcon("icons/send.svg")  # 确保 icons/send.svg 文件存在
        self.pushButton.setIcon(send_icon)
        self.pushButton.setIconSize(QtCore.QSize(16, 16))  # 设置图标大小
        self.inputLayout.addWidget(self.pushButton)

        # 将输入区域添加到主布局
        self.verticalLayout.addLayout(self.inputLayout)

        self.retranslateUi()
        QtCore.QMetaObject.connectSlotsByName(self)

        self.pushButton.clicked.connect(self.on_pushButton_clicked)

    def retranslateUi(self):
        _translate = QtCore.QCoreApplication.translate
        self.setWindowTitle(_translate("CustomAIchatbox", "AI Chatbox"))

    def on_pushButton_clicked(self):
        text = self.textEdit.text()
        self.text_submit.emit(text)
        self.start_loading()  # 点击提交按钮时启动加载图标

    def add_node_buttons(self, nodes):
        """
        动态添加节点按钮
        :param nodes: 节点名称列表
        """
        # 清空之前的按钮
        for i in reversed(range(self.nodeButtonLayout.count())):
            widget = self.nodeButtonLayout.itemAt(i).widget()
            if widget is not None:
                widget.deleteLater()

        # 添加新的按钮
        for node in nodes:
            button = QtWidgets.QPushButton(node, self)
            button.setObjectName(f"nodeButton_{node}")
            button.setStyleSheet("background-color: #3c3c3c; color: #ffffff; border: none; padding: 5px;")
            self.nodeButtonLayout.addWidget(button)
            button.clicked.connect(lambda checked, n=node: self.on_node_button_clicked(n))

    def on_node_button_clicked(self, node):
        """
        节点按钮点击事件
        :param node: 被点击的节点名称
        """
        self.node_selected.emit(node)

    def start_loading(self):
        """
        启动加载，将按钮替换为加载图标
        """
        load_icon = QtGui.QIcon("icons/wait.svg")  
        self.pushButton.setIcon(load_icon)
        self.pushButton.setIconSize(QtCore.QSize(16, 16))  # 设置图标大小

    def stop_loading(self):
        """
        停止加载，将按钮恢复为原始状态
        """
        # 恢复按钮图标
        send_icon = QtGui.QIcon("icons/send.svg")
        self.pushButton.setIcon(send_icon)
        self.pushButton.setIconSize(QtCore.QSize(16, 16))

    def show_chatbox(self, parent_geometry):
        print(parent_geometry)
        """
        从右侧弹出整个 chatbox 窗口
        :param parent_geometry: 父窗口的几何信息，用于计算弹出位置
        """
        self.animation.stop()
        start_geometry = QtCore.QRect(parent_geometry.right(), parent_geometry.top(), 400, parent_geometry.height())
        end_geometry = QtCore.QRect(parent_geometry.right() - 400, parent_geometry.top(), 400, parent_geometry.height())
        self.animation.setStartValue(start_geometry)
        self.animation.setEndValue(end_geometry)
        self.animation.start()

    def hide_chatbox(self, parent_geometry):
        print(parent_geometry)
        """
        从左侧收回整个 chatbox 窗口
        :param parent_geometry: 父窗口的几何信息，用于计算收回位置
        """
        self.animation.stop()
        start_geometry = QtCore.QRect(parent_geometry.right() - 400, parent_geometry.top(), 400, parent_geometry.height())
        end_geometry = QtCore.QRect(parent_geometry.right(), parent_geometry.top(), 400, parent_geometry.height())
        self.animation.setStartValue(start_geometry)
        self.animation.setEndValue(end_geometry)
        self.animation.finished.connect(self.close)
        self.animation.start()


    def on_close_button_clicked(self):
        """
        关闭按钮点击事件，触发 hide_chatbox 动画
        """
        parent_geometry = self.parent().geometry() if self.parent() else self.geometry()
        self.hide_chatbox(parent_geometry)