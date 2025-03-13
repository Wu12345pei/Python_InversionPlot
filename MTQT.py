from Qt import QtCore, QtWidgets, QtGui
from plotly.offline import plot
from PySide6.QtWebEngineWidgets import QWebEngineView
from NodeGraphQt import BaseNode, NodeBaseWidget, NodeGraph
from MTP2Node import *
from Menu import *
from CustomMessageBox import CustomMessageBox
from functools import partial

############################################################################################################
## 创建Nodegraph子类，添加connectionmgr和workflowengine
class NodeGraphMT(NodeGraph):
    def __init__(self):
        super(NodeGraphMT, self).__init__()
        self.connectionmgr = ConnectionManager()

    def add_connection(self, start_node, start_port, end_node, end_port):
        successful = self.connectionmgr.add_connection(start_node, start_port, end_node, end_port)
        return successful

    def remove_connection(self, start_node, start_port, end_node, end_port):
        successful = self.connectionmgr.remove_connection(start_node, start_port, end_node, end_port)
        return successful
    
    def remove_nodes(self, nodes):
        for node in nodes:
            self.delete_node(node)

    def run_workflow(self):
        nodes = self.connectionmgr.nodes
        workflow = WorkflowEngine(self.connectionmgr)
        order = workflow.prepare_execution()
        print(order)
        workflow.execute()

############################################################################################################
##所有节点列表
input_nodes = ['InputFileNode.InputFileNodeUI']
compute_nodes = ['PhaseTensorNode.PhaseTensorNodeUI', 'ApparentResistivityNode.ApparentResistivityNodeUI', 'UnpackDataNode.UnpackDataNodeUI']
output_nodes = ['OutputNode.OutputNodeUI']

## 1.输入节点，仅有输出端口
## 1.1 文件输入节点
class InputfileNodeWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(InputfileNodeWidget, self).__init__(parent)
        # 设置path
        self.label_path = QtWidgets.QLabel('Path')
        self.label_path.setStyleSheet("color: white;")  # 设置字体颜色为白色
        self.edit_path = QtWidgets.QLineEdit()
        self.btn_path = QtWidgets.QPushButton('...')
    
        # 设置file_type 
        self.combo_filetype = QtWidgets.QComboBox()
        self.label_filetype = QtWidgets.QLabel('File Type')
        self.label_filetype.setStyleSheet("color: white;")  # 设置字体颜色为白色
        self.combo_filetype.addItems(['Z_ALL_3D', 'Z_offdiag_3D'])

        # 设置read_start_line
        self.label_readline = QtWidgets.QLabel('Read Start Line')
        self.label_readline.setStyleSheet("color: white;")  # 设置字体颜色为白色
        self.spin_readline = QtWidgets.QSpinBox()
        self.spin_readline.setValue(0)

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.label_path)
        layout.addWidget(self.edit_path)
        layout.addWidget(self.btn_path)
        layout.addWidget(self.label_filetype)
        layout.addWidget(self.combo_filetype)
        layout.addWidget(self.label_readline)
        layout.addWidget(self.spin_readline)
        layout.addStretch()
class InputfileNodeWrapper(NodeBaseWidget):
    def __init__(self, parent=None, MTinputnode=None):
        super(InputfileNodeWrapper, self).__init__(parent)
        self.set_name('inputfile')
        self.set_label('InputFile')
        self.MTinputnode = MTinputnode
        self.set_custom_widget(InputfileNodeWidget())
        self.wire_signals()

    def wire_signals(self):
        widget = self.get_custom_widget()
        widget.btn_path.clicked.connect(self.on_btn_path_clicked)
        
        # 实时更新参数
        widget.edit_path.textChanged.connect(lambda: self.MTinputnode.set_param('path', widget.edit_path.text()))
        widget.combo_filetype.currentTextChanged.connect(lambda: self.MTinputnode.set_param('file_type', widget.combo_filetype.currentText()))
        widget.spin_readline.valueChanged.connect(lambda: self.MTinputnode.set_param('read_start_line', widget.spin_readline.value()))

        # 打印参数
        widget.edit_path.textChanged.connect(self.print_params)
        widget.combo_filetype.currentTextChanged.connect(self.print_params)
        widget.spin_readline.valueChanged.connect(self.print_params)

    def on_btn_path_clicked(self):
        path = QtWidgets.QFileDialog.getOpenFileName(None,'Open File', '')[0]
        if path:
            self.get_custom_widget().edit_path.setText(path)

    def print_params(self):
        print(self.MTinputnode.params)

    def get_value(self):
        widget = self.get_custom_widget()
        return {
            'path': widget.edit_path.text(),
            'file_type': widget.combo_filetype.currentText(),
            'read_start_line': widget.spin_readline.value()
        }
    
    def set_value(self, value):
        widget = self.get_custom_widget()
        widget.edit_path.setText(value['path'])
        widget.combo_filetype.setCurrentText(value['file_type'])
        widget.spin_readline.setValue(value['read_start_line'])
        ## 设定初始节点参数
        self.MTinputnode.set_param('path', value['path'])
        self.MTinputnode.set_param('file_type', value['file_type'])
        self.MTinputnode.set_param('read_start_line', value['read_start_line'])
class InputFileNodeUI(BaseNode):
    NODE_NAME = 'InputDAT'
    NODE_CATEGORY = 'Input'
    __identifier__ = 'InputFileNode'
    
    def __init__(self):
        super(InputFileNodeUI, self).__init__()

        # create input and output port.
        self.add_output('Processor')
        self.MTnode = InputFileNode('input', 'Input')
        # add custom widget to node with "node.view" as the parent.
        node_widget = InputfileNodeWrapper(self.view, self.MTnode)
        self.add_custom_widget(node_widget, tab='Custom')

############################################################################################################
## 2.计算节点，有输入和输出端口
## 2.1 相位张量计算节点
class PhaseTensorNodeUI(BaseNode):
    NODE_NAME = 'PhaseTensor'
    NODE_CATEGORY = 'Compute'
    __identifier__ = 'PhaseTensorNode'
    
    def __init__(self):
        super(PhaseTensorNodeUI, self).__init__()
        # create input and output port.
        self.add_input('Processor')
        self.add_output('Processor')
        self.MTnode = PhaseTensorNode('PhaseTensor', 'PhaseTensor')
## 2.2 视电阻率计算节点
class ApparentResistivityNodeUI(BaseNode):
    NODE_NAME = 'ApparentResistivity'
    NODE_CATEGORY = 'Compute'
    __identifier__ = 'ApparentResistivityNode'

    def __init__(self):
        super(ApparentResistivityNodeUI, self).__init__()
        # create input and output port.
        self.add_input('Processor')
        self.add_output('Processor')
        self.MTnode = ApparentResistivityNode('ApparentResistivity', 'ApparentResistivity')
## 2.3 数据拆包节点
class UnpackDataNodeUI(BaseNode):
    NODE_NAME = 'UnpackData'
    NODE_CATEGORY = 'Compute'
    __identifier__ = 'UnpackDataNode'
    def __init__(self):
        super(UnpackDataNodeUI,self).__init__()
        self.add_input('Processor')
        self.add_output('Periods')
        self.add_output('Sitenames')
        self.add_output('XYZ_in_dat')
        self.add_output('Z_matrix')
        self.add_output('Zerr_matrix')
        self.add_output('Orientation')
        self.add_output('Period_num')
        self.add_output('Site_num')
        self.add_output('Distance_by_Dat')
        self.add_output('Skew')
        self.add_output('Phi2')
        self.add_output('Phase_tensor')
        self.add_output('Apparent_resistivity')
        self.add_output('Phi')
        self.MTnode = UnpackDataNode('UnpackData','UnpackData')
############################################################################################################
## 3.输出节点, 仅有输入端口
## 3.1 数据字典的key输出节点
class OutputNodeUI(BaseNode):
    NODE_NAME = 'Output'
    NODE_CATEGORY = 'Output'
    __identifier__ = 'OutputNode'
    
    def __init__(self):
        super(OutputNodeUI, self).__init__()

        # create input and output port.
        self.add_input('Processor')
        self.MTnode = OutputMTPNode('output', 'output')

## 3.2 视电阻率画图输出节点
class OutputResistivityPlotNodeWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(OutputResistivityPlotNodeWidget, self).__init__(parent)
        ## 设置图片说明
        self.label_title = QtWidgets.QLabel('Apparent Resistivity Plot')
        self.label_title.setStyleSheet("color: white;")  # 设置字体颜色为白色
        ## 准备图片需要嵌入的widget
        self.plotbrowser = QWebEngineView()
        html = ""
        self.plotbrowser.setHtml(html)
        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.label_title)
        layout.addWidget(self.plotbrowser)
        layout.addStretch()

class OutputResistivityPlotNodeWrapper(NodeBaseWidget):
    def __init__(self, parent=None, MTnode=None):
        super(OutputResistivityPlotNodeWrapper, self).__init__(parent)
        self.set_name('outputplot')
        self.set_label('OutputPlot')
        self.MTnode = MTnode
        self.set_custom_widget(OutputResistivityPlotNodeWidget())
        self.wire_signals()

    def wire_signals(self):
        self.MTnode.finished.connect(self.update_plot)

    def get_value(self):
        pass
    
    def set_value(self, value):
        pass

    def update_plot(self):
        fig = self.MTnode.restorefigure
        print('fig generated')
        html = plot(fig, output_type='div', include_plotlyjs='cdn', config={'displayModeBar': False}, image_width=1200, image_height=800)
        print('html generated')
        self.get_custom_widget().plotbrowser.setHtml(html)
        print('html set')

class OutputResistivityPlotNodeUI(BaseNode):
    NODE_NAME = 'Outputplot'
    NODE_CATEGORY = 'Output'
    __identifier__ = 'OutputResistivityPlotNode'

    def __init__(self):
        super(OutputResistivityPlotNodeUI, self).__init__()

        # create input and output port.
        self.add_input('Processor')
        self.MTnode = OutputApparentResistivityNode('outputplot', 'outputplot')
        # add custom widget to node with "node.view" as the parent.
        node_widget = OutputResistivityPlotNodeWrapper(self.view, self.MTnode)
        self.add_custom_widget(node_widget, tab='Custom')



## 4.测试
if __name__ == '__main__':
    app = QtWidgets.QApplication([])
    node_graph = NodeGraphMT()
    node_graph.register_node(InputFileNodeUI)
    node_graph.register_node(PhaseTensorNodeUI)
    node_graph.register_node(ApparentResistivityNodeUI)
    node_graph.register_node(OutputNodeUI)
    node_graph.register_node(UnpackDataNodeUI)
    node_graph.register_node(OutputResistivityPlotNodeUI)

    # get the main context menu.
    context_menu = node_graph.get_context_menu('graph')

    # 添加图菜单
    Run_menu = context_menu.add_menu('Run')
    Run_menu.add_command('Run work flow', node_graph.run_workflow, 'Shift+R')
 
    Node_menu = context_menu.add_menu('Node')
    Input_menu = Node_menu.add_menu('Input')
    Compute_menu = Node_menu.add_menu('Compute')
    Output_menu = Node_menu.add_menu('Output')

    Input_menu.add_command('InputFileNode', lambda: node_graph.create_node('InputFileNode.InputFileNodeUI', name='Default_Input'))
    Compute_menu.add_command('PhaseTensorNode', lambda: node_graph.create_node('PhaseTensorNode.PhaseTensorNodeUI', name='Default_Phase'))
    Compute_menu.add_command('ApparentResistivityNode', lambda: node_graph.create_node('ApparentResistivityNode.ApparentResistivityNodeUI', name='Default_Apparent'))
    Compute_menu.add_command('UnpackDataNode', lambda: node_graph.create_node('UnpackDataNode.UnpackDataNodeUI', name='Default_Unpack'))
    Output_menu.add_command('OutputNode', lambda: node_graph.create_node('OutputNode.OutputNodeUI', name='Default_Output'))
    Output_menu.add_command('OutputResistivityPlotNode', lambda: node_graph.create_node('OutputResistivityPlotNode.OutputResistivityPlotNodeUI', name='Default_OutputPlot'))

    # 添加节点右键菜单
    nodes_menu = node_graph.get_context_menu('nodes')
    nodes_menu.add_command('Delete', 
                           lambda: node_graph.remove_nodes(node_graph.selected_nodes()),
                           node_class=BaseNode)

    # 添加连接和断开连接的信号
    message_box = CustomMessageBox()

    def show_message(title, message):
        message_box.show_message(message, node_graph.widget)

    def on_nodes_connected(end_port, start_port):
        start_node = start_port.node()
        end_node = end_port.node() 
        suc = node_graph.add_connection(start_node.MTnode, start_port.name(), end_node.MTnode, end_port.name())
        if not suc:
            start_port.disconnect_from(end_port)
            show_message("Error", "Connection failed")
        else:
            show_message("Node Connected", f"Connected: {start_node.name()} ({start_port.name()}) -> {end_node.name()} ({end_port.name()})")

    node_graph.port_connected.connect(on_nodes_connected)

    def on_nodes_disconnected(end_port, start_port):
        start_node = start_port.node()
        end_node = end_port.node()
        suc = node_graph.remove_connection(start_node.MTnode, start_port.name(), end_node.MTnode, end_port.name())
        if not suc:
            show_message("Error", "Disconnection failed")
        else:
            show_message("Node Disconnected", f"Disconnected: {start_node.name()} ({start_port.name()}) -> {end_node.name()} ({end_port.name()})")

    node_graph.port_disconnected.connect(on_nodes_disconnected)

    def on_node_deleted(node):
        show_message("Node Deleted", f"Node {node.name()} deleted")


    node_graph.widget.show()
    node_input = node_graph.create_node('InputFileNode.InputFileNodeUI', name='Node_InputDAT_MT')
    node_phase = node_graph.create_node('PhaseTensorNode.PhaseTensorNodeUI', name='Node_Phase_MT')
    node_apparent = node_graph.create_node('ApparentResistivityNode.ApparentResistivityNodeUI', name='Node_Apparent_MTDAT')
    node_output = node_graph.create_node('OutputResistivityPlotNode.OutputResistivityPlotNodeUI', name='Node_Output_MTDAT')

    app.exec()