from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from collections import defaultdict, deque
from PySide6.QtCore import QThread, Signal

class MTBaseNode(QThread):
    finished = Signal()

    def __init__(self, node_id: str, label: str):
        super().__init__()
        self.id = node_id          # 唯一标识符
        self.label = label        # 显示名称
        self.position = (0, 0)    # 坐标 (x,y)

        # 端口系统
        self.input_ports: Dict[str, type] = {}   # {端口名: 数据类型}
        self.output_ports: Dict[str, type] = {}  # {端口名: 数据类型}

        #参数
        self.params = {}  # 节点参数

        # 执行状态
        self._result_cache = None

    def add_input_port(self, name: str, data_type: type):
        """动态添加输入端口"""
        self.input_ports[name] = data_type
        
    def add_output_port(self, name: str, data_type: type):
        """动态添加输出端口"""
        self.output_ports[name] = data_type
    
    def set_param(self, name: str, value: any):
        """设置节点参数"""
        self.params[name] = value

    def execute(self, inputs: Dict[str, any]) -> Dict[str, any]:
        """节点核心逻辑"""
        pass

    def validate_connections(self, target: 'MTBaseNode', source_port: str, target_port: str) -> bool:
        """验证端口连接是否合法"""
        src_type = self.output_ports.get(source_port)
        dst_type = target.input_ports.get(target_port)
        return src_type == dst_type or dst_type == any

    def __repr__(self):
        return f"<{self.__class__.__name__} {self.id}>"

from dataclasses import dataclass

@dataclass
class Connection:
    source_node_id: str
    source_port: str
    target_node_id: str
    target_port: str
    data_type: type  # 保存连接时的数据类型

    def __repr__(self):
        return f"{self.source_node_id}.{self.source_port} -> {self.target_node_id}.{self.target_port}"

class ConnectionManager:
    def __init__(self):
        self.connections: List[Connection] = []
        self.nodes = {}  # {node_id: node}
        self._lookup_cache = {}  # 用于快速查询

    def add_connection(self, source_node: MTBaseNode, source_port: str,
                       target_node: MTBaseNode, target_port: str) -> bool:
        # 验证端口是否存在
        if not self._validate_ports(source_node, source_port, target_node, target_port):
            return False

        # 验证类型兼容性
        src_type = source_node.output_ports[source_port]
        dst_type = target_node.input_ports[target_port]
        if src_type != dst_type and dst_type != any:
            print(f"类型不匹配: {src_type} -> {dst_type}")
            return False

        # 创建新连接
        new_conn = Connection(
            source_node_id=source_node.id,
            source_port=source_port,
            target_node_id=target_node.id,
            target_port=target_port,
            data_type=src_type
        )
        print(f"创建连接: {new_conn}")

        # 检查是否已存在相同连接
        if not any(self._is_same_connection(new_conn, c) for c in self.connections):
            self.connections.append(new_conn)
            self.add_node(source_node)
            self.add_node(target_node)
            print(f"节点数量: {len(self.nodes)}")
            self._update_cache()
            return True
        return False

    def add_node(self, node: MTBaseNode):
        """添加节点到管理器"""
        #{node.id: node for node in nodes}
        if node.id not in self.nodes:
            self.nodes[node.id] = node
            print(f"添加节点: {node}")

    def remove_connection(self, source_node: MTBaseNode, source_port: str,
                          target_node: MTBaseNode, target_port: str) -> bool:
        src_type = source_node.output_ports[source_port]
        conn = Connection(
            source_node_id=source_node.id,
            source_port=source_port,
            target_node_id=target_node.id,
            target_port=target_port,
            data_type=src_type
        )
        # 
        if conn in self.connections:
            print(f"移除连接: {conn}")
            self.connections.remove(conn)
            self.check_and_remove_node(source_node.id)
            self.check_and_remove_node(target_node.id)
            self._update_cache()
            print(f"节点数量: {len(self.nodes)}")
            return True
        print(f"连接不存在: {conn}")
        return False
    

    def check_and_remove_node(self, node_id: str):
        """检查节点是否需要被移除"""
        if not self.get_connections_from(node_id) and not self.get_connections_to(node_id):
            print(f"移除节点: {node_id}")
            self.nodes.pop(node_id)
            return True
        return False

    def _validate_ports(self, source, src_port, target, tgt_port):
        valid = True
        if src_port not in source.output_ports:
            print(f"源节点 {source.id} 无输出端口 {src_port}")
            valid = False
        if tgt_port not in target.input_ports:
            print(f"目标节点 {target.id} 无输入端口 {tgt_port}")
            valid = False
        return valid

    def _is_same_connection(self, c1: Connection, c2: Connection) -> bool:
        return (c1.source_node_id == c2.source_node_id and
                c1.source_port == c2.source_port and
                c1.target_node_id == c2.target_node_id and
                c1.target_port == c2.target_port)

    def get_connections_to(self, node_id: str) -> List[Connection]:
        """获取连接到指定节点的所有输入连接"""
        return [c for c in self.connections if c.target_node_id == node_id]

    def get_connections_from(self, node_id: str) -> List[Connection]:
        """获取从指定节点出发的所有输出连接"""
        return [c for c in self.connections if c.source_node_id == node_id]

    def _update_cache(self):
        """更新快速查询缓存"""
        self._lookup_cache = {}
        for conn in self.connections:
            key = (conn.target_node_id, conn.target_port)
            if key not in self._lookup_cache:
                self._lookup_cache[key] = []
            self._lookup_cache[key].append(conn)

    def get_inputs_for(self, node_id: str, port: str) -> List[Connection]:
        """获取连接到指定节点端口的输入"""
        return self._lookup_cache.get((node_id, port), [])


class WorkflowEngine:
    def __init__(self, conn_mgr: ConnectionManager):
        #self.nodes = {node.id: node for node in nodes}
        if not conn_mgr.connections:
            raise ValueError("连接管理器中没有连接")
        self.conn_mgr = conn_mgr
        self.nodes = conn_mgr.nodes
        self.execution_order = []
    
    def prepare_execution(self):
        """生成拓扑排序的执行顺序"""
        dependencies = self._build_dependency_graph()
        self.execution_order = self._topological_sort(dependencies)
        return self.execution_order
    
    def execute(self):
        """执行整个工作流"""
        context = {}
        for node_id in self.execution_order:
            node = self.nodes[node_id]
            inputs = self._gather_inputs(node, context)
            try:
                output = node.execute(inputs)
                node.finished.emit()
                context[node_id] = output
            except Exception as e:
                print(f"节点 {node_id} 执行失败: {str(e)}")
                break
        return context

    def _build_dependency_graph(self) -> Dict[str, List[str]]:
        """构建节点依赖关系图"""
        graph = {node_id: [] for node_id in self.nodes}
        for conn in self.conn_mgr.connections:
            source = conn.source_node_id
            target = conn.target_node_id
            if source in self.nodes and target in self.nodes:
                graph[source].append(target)
        return graph

    def _gather_inputs(self, node: MTBaseNode, context: dict) -> dict:
        """收集节点的输入数据"""
        inputs = {}
        for conn in self.conn_mgr.get_connections_to(node.id):
            source_data = context.get(conn.source_node_id, {})
            if conn.source_port in source_data:
                inputs[conn.target_port] = source_data[conn.source_port]
            else:
                raise ValueError(f"缺失输入数据: {conn.source_node_id}.{conn.source_port}")
        return inputs

    def _topological_sort(self, graph: Dict[str, List[str]]) -> List[str]:
        in_degree = {u: 0 for u in graph}
        for u in graph:
            for v in graph[u]:
                in_degree[v] += 1

        queue = deque([u for u in in_degree if in_degree[u] == 0])
        result = []
        
        while queue:
            u = queue.popleft()
            result.append(u)
            for v in graph[u]:
                in_degree[v] -= 1
                if in_degree[v] == 0:
                    queue.append(v)
        
        if len(result) != len(graph):
            raise RuntimeError("工作流存在循环依赖")
        return result

    def visualize(self, filename="workflow"):
        """使用 Graphviz 可视化工作流，直接在代码中渲染"""
        try:
            from graphviz import Digraph
        except ImportError:
            print("请先安装 graphviz 库: pip install graphviz")
            return

        dot = Digraph(comment='Workflow', format='png')  # 指定输出格式为 PNG

        # 添加节点
        for node_id, node in self.nodes.items():
            dot.node(node_id, f"{node.label}\n({node.id})")

        # 添加连接
        for conn in self.conn_mgr.connections:
            dot.edge(conn.source_node_id, conn.target_node_id,
                     label=f"{conn.source_port} -> {conn.target_port}")

        # 保存到文件并渲染
        try:
            dot.render(filename, view=True, cleanup=True)  # 渲染并显示图像，删除临时文件
            print(f"工作流可视化已保存到 {filename}.png 并显示")
        except Exception as e:
            print(f"渲染失败: {e}")

