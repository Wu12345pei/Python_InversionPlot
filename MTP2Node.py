from MTBaseNodeManager.BaseNodeManager import MTBaseNode, ConnectionManager, WorkflowEngine
from typing import Dict, List
from MTProcessorClass.MTProcessor import MyDataProcessor as MTProcessor

# 将MTProcessor中的功能封装到Node中
## 1.输入节点
## 1.1 文件输入节点
class InputFileNode(MTBaseNode):
    def __init__(self, node_id: str, label: str):
        super().__init__(node_id, label)
        self.add_output_port('Processor', MTProcessor)
        self.set_param('path', '')
        self.set_param('file_type', '')
        self.set_param('read_start_line', 0)

    def execute(self, inputs: Dict[str, any]) -> Dict[str, any]:
        MTP = MTProcessor()
        MTP.read_file(self.params['path'], self.params['file_type'], self.params['read_start_line'])
        MTP.get_distance()
        return {'Processor': MTP} 


## 2.计算节点
## 2.1 相位张量计算节点
class PhaseTensorNode(MTBaseNode):
    def __init__(self, node_id: str, label: str):
        super().__init__(node_id, label)
        self.add_input_port('Processor', MTProcessor)
        self.add_output_port('Processor', MTProcessor)
    def execute(self, inputs: Dict[str, any]) -> Dict[str, any]:
        MTP = inputs['Processor']
        MTP.compute_phase_Tensor()
        return {'Processor': MTP}

## 2.2 视电阻率计算节点
class ApparentResistivityNode(MTBaseNode):
    def __init__(self, node_id: str, label: str):
        super().__init__(node_id, label)
        self.add_input_port('Processor', MTProcessor)
        self.add_output_port('Processor', MTProcessor)
    def execute(self, inputs: Dict[str, any]) -> Dict[str, any]:
        MTP = inputs['Processor']
        MTP.compute_apparent_resistivity()
        return {'Processor': MTP}
    
## 2.3 文件数据拆包节点
class UnpackDataNode(MTBaseNode):
    def __init__(self, node_id: str, label: str):
        super().__init__(node_id, label)
        self.add_input_port('Processor', MTProcessor)
        self.add_output_port('Periods', List)
        self.add_output_port('Sitenames', List)
        self.add_output_port('XYZ_in_dat', List)
        self.add_output_port('Z_matrix', List)
        self.add_output_port('Zerr_matrix', List)
        self.add_output_port('Orientation', List)
        self.add_output_port('Period_num', List)
        self.add_output_port('Site_num', List)
        self.add_output_port('Distance_by_Dat', List)
        self.add_output_port('Skew', List)
        self.add_output_port('Phi2', List)
        self.add_output_port('Phase_tensor', List)
        self.add_output_port('Apparent_resistivity', List)
        self.add_output_port('Phi',list)
    def execute(self, inputs: Dict[str, any]) -> Dict[str, any]:
        MTP = inputs['Processor']
        data = MTP.DataFromDat
        if MTP is None:
            raise ValueError('No data input')
        if data is None:
            raise ValueError('No data input')
        return {'Periods': data['T'],'Sitenames': data['Sitenames'],
                'XYZ_in_dat': data['XYZ'],'Z_matrix': data['Z_matrix'],
                'Zerr_matrix': data['Zerr_matrix'],'Orientation': data['orientation'],
                'Period_num': data['nTx'],'Site_num': data['nSites'],
                'Distance_by_Dat': data['distancebyDat'],'Skew': data['skew'],
                'Phi2': data['Phi2'],'Phase_Tensor': data['Phase_Tensor'],
                'Apparent_resistivity': data['Apparent_resistivity'],'Phi': data['Phi']}
        
        
        
        



## 3.输出节点
## 3.1 数据字典的key输出节点
class OutputMTPNode(MTBaseNode):
    def __init__(self, node_id: str, label: str):
        super().__init__(node_id, label)
        self.add_input_port('Processor', MTProcessor)
    def execute(self, inputs: Dict[str, any]) -> Dict[str, any]:
        print(inputs['Processor'])
        return inputs

## 3.2 数据格式输出节点
class OutputFormatNode(MTBaseNode):
    def __init__(self, node_id: str, label: str):
        super().__init__(node_id, label)
        self.add_input_port('Data', any)
    def execute(self, inputs: Dict[str, any]) -> Dict[str, any]:
        Data = inputs['Data']
        print(type(Data))
        print(Data)
        return {'Data': Data}
    
## 3.3 视电阻率数据可视化输出节点
class OutputApparentResistivityNode(MTBaseNode):
    def __init__(self, node_id: str, label: str):
        super().__init__(node_id, label)
        self.add_input_port('Processor', MTProcessor)
    def execute(self, inputs: Dict[str, any]) -> Dict[str, any]:
        MTP = inputs['Processor']
        MTP.plot_resistivity_of_one_site(2)
        self.restorefigure = MTP.fig
        print('fig success')
        return {'Processor': MTP}


## 4.测试
## 输入节点
if __name__ == '__main__':
    ## 输入节点
    input_node = InputFileNode('input1', 'Input')
    input_node.set_param('path', 'D:/Desktop/研究生/博士二年级/Python_InversionPlot/BYKLData.dat')
    input_node.set_param('file_type', 'Z_ALL_3D')
    input_node.set_param('read_start_line', 2)

    ## 计算节点
    phase_node = PhaseTensorNode('phase', 'Phase')
    apparent_node = ApparentResistivityNode('apparent', 'Apparent')

    unpack_node = UnpackDataNode('unpack', 'Unpack')  

    ## 输出节点
    output_node = OutputApparentResistivityNode('output', 'Output')

    connectionmgr = ConnectionManager()
    connectionmgr.add_connection(input_node, 'Processor', phase_node, 'Processor')
    connectionmgr.add_connection(phase_node, 'Processor', apparent_node, 'Processor')
    connectionmgr.add_connection(apparent_node, 'Processor', unpack_node, 'Processor')
    connectionmgr.add_connection(apparent_node, 'Processor', output_node, 'Processor')
    workflow = WorkflowEngine(connectionmgr)
    order = workflow.prepare_execution()
    print(order)

    workflow.execute()
    workflow.visualize()