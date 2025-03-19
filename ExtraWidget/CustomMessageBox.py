from Qt import QtCore, QtWidgets, QtGui

class CustomMessageBox(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(CustomMessageBox, self).__init__(parent)
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint | QtCore.Qt.WindowStaysOnTopHint)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.setStyleSheet("""
            QWidget {
                background-color: rgba(0, 0, 0, 180);
                color: white;
                border-radius: 10px;
                padding-top: 20px;    /* 增加上间距 */
                padding-bottom: 20px; /* 增加下间距 */
                padding-left: 10px;   /* 左间距 */
                padding-right: 10px;  /* 右间距 */
            }
        """)

        self.label = QtWidgets.QLabel(self)
        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.label)
        self.setLayout(layout)

        self.move_animation = QtCore.QPropertyAnimation(self, b"pos")
        self.move_animation.setDuration(1000)

        self.animation_group = QtCore.QSequentialAnimationGroup()
        self.animation_group.addAnimation(self.move_animation)

    def show_message(self, message, parent_widget):
        self.label.setText(message)
        self.adjustSize()
        parent_geometry = parent_widget.geometry()
        start_pos = QtCore.QPoint(parent_geometry.right() - self.width() - 10, parent_geometry.bottom())
        end_pos = QtCore.QPoint(parent_geometry.right() - self.width() - 10, parent_geometry.bottom() - self.height() - 10)
        self.move(start_pos)
        self.show()

        self.move_animation.setStartValue(start_pos)
        self.move_animation.setEndValue(end_pos)
        self.move_animation.setEasingCurve(QtCore.QEasingCurve.OutBounce)

        self.animation_group.start()
        QtCore.QTimer.singleShot(5000, self.hide)  # 增加定时器时间到5000毫秒（5秒）

    def fade_out(self):
        self.hide()  # 直接隐藏消息框

