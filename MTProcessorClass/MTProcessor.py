import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import copy
import os
import plotly.graph_objects as go

class MyDataProcessor:
    # MyDataProcessor 类用于读取文件、进行计算并绘制结果
    
    def __init__(self):
        self.data = None  # 存储读取的数据
        self.DataFromDat = None  # 存储计算后的数据

    def __repr__(self):
        return f"<{self.__class__.__name__}>("f"DataFromDat: {self.DataFromDat.keys()})"
    ##################################################################################################################
    # read_file 以下方法用于读取文件
    def __read_Zimp_3D(self, cfile, read_start=0):
        """
        Reads the header and data from a Z3D data file and returns them in a formatted way.
        
        Parameters:
        cfile (str): File path to the Z3D data file.
        
        Returns:
        header (list): List of header lines.
        data_df (pandas.DataFrame): DataFrame containing the formatted data.
        """
        if read_start < 0:
            raise ValueError("read_start must be greater than or equal to 0.")
        if not isinstance(read_start, int):
            raise ValueError("read_start must be an integer.")
        if not os.path.exists(cfile):
            raise ValueError("File does not exist.")
        header = []
        data_lines = []
        
        # open the file and set the number of header lines
        with open(cfile, 'r') as f:
            nheader = 6;
            header_alreadyread = 0;
            blockinfo = []
        # read the header lines
            while header_alreadyread < nheader+read_start:
                # Read the header info
                line = f.readline().strip()
                if line.startswith('>') and header_alreadyread + 1 >= read_start:
                    header.append(line)
                    blockinfo.append(line.strip('> '))
                header_alreadyread += 1

        # Extract the block information
            dataType = blockinfo[0]
            signstr = blockinfo[1]
            typeUnits = blockinfo[2].strip()
            orientation = blockinfo[3]
            origin = blockinfo[4]
            nTx, nSites = map(int, blockinfo[5].split())

        # Read the data lines
            while True:
                line = f.readline().strip()
                if line.startswith('>') or not line:
                    break
                data_lines.append(line)
        
        # Convert the data to a pandas DataFrame
        data_columns = ['period', 'site_code', 'lat', 'lon', 'x', 'y', 'z', 'comp', 'real', 'imag', 'err','Amuth']
        data_df = pd.DataFrame([line.split() for line in data_lines], columns=data_columns)
        
        return header, data_df, dataType, signstr, typeUnits, orientation, origin, nTx, nSites
    
    ##################################################################################################################
    # 以下方法用于数据转化和存储
    def read_file(self, file_path, file_type='Z_ALL_3D', read_start=0):
        if file_type == 'Z_ALL_3D':
            header, data_df, dataType, signstr, typeUnits, orientation, origin, nTx, nSites = self.__read_Zimp_3D(file_path, read_start)
            # get T, Sitenames and XYZ from data_df
            T_val = data_df['period'].values
            # remove duplicate values
            T = list(dict.fromkeys(T_val))

            Sitenames_val = data_df['site_code'].values
            # remove duplicate values
            Sitenames = list(dict.fromkeys(Sitenames_val))

            XYZ = data_df[['x', 'y', 'z']].values
            # remove duplicate values
            XYZ = list(dict.fromkeys(tuple(x) for x in XYZ))
            

            # get Z-matrix and Z-error-matrix from data_df,format: [nTx, nSites, nComp, 2]
            Z_val = data_df[['real', 'imag']].values
            Zerr = data_df['err'].values
            Comp_val = data_df['comp'].values

            Z_matrix = np.zeros([nTx, nSites, 2, 2], dtype=complex)
            Zerr_matrix = np.zeros([nTx, nSites, 2, 2])
            for i in range(len(Z_val)):
                Tn = T.index(T_val[i])
                Sn = Sitenames.index(Sitenames_val[i])
                Cn = ['ZXX', 'ZXY', 'ZYX', 'ZYY'].index(Comp_val[i])
                row , col = divmod(Cn, 2)
                Z_matrix[Tn, Sn, row, col] = float(Z_val[i][0]) + 1j * float(Z_val[i][1])
                Zerr_matrix[Tn, Sn, row, col] = Zerr[i]
            
            self.DataFromDat = {'header': header, 'T': T, 'Sitenames': Sitenames, 'XYZ': XYZ, 'Z_matrix': Z_matrix, 'Zerr_matrix': Zerr_matrix, 'dataType': dataType, 'signstr': signstr, 'typeUnits': typeUnits, 'orientation': orientation, 'origin': origin, 'nTx': nTx, 'nSites': nSites}

    def get_distance(self):
        if self.DataFromDat is None:
            raise ValueError("Data is not available.")
        XYZ = self.DataFromDat.get('XYZ')
        XY = np.array(XYZ)[:, :2]
        XY = [list(map(float, sublist)) for sublist in XY]
        origin = copy.deepcopy(XY[0])
        end_site = copy.deepcopy(XY[-1])
        angle = np.arctan2(end_site[1] - origin[1], end_site[0] - origin[0])
        distance = []
        rotation_matrix = np.array([[np.cos(angle), -np.sin(angle)], [np.sin(angle), np.cos(angle)]])
        for sublist in XY:
            sublist[0] = sublist[0] - origin[0]
            sublist[1] = sublist[1] - origin[1]
            sublist = np.dot(rotation_matrix.T, np.array(sublist).T).T
            distance.append(sublist[0])
        self.DataFromDat.update({'distancebyDat': distance})
        # rotate the coordinate
    ##################################################################################################################
    # 进行计算的方法
    def compute_phase_Tensor(self):
        if self.DataFromDat is None:
            raise ValueError("Data is not available.")
        Phase_Tensor = np.zeros([self.DataFromDat.get('nTx'), self.DataFromDat.get('nSites'), 2, 2])
        skew = np.zeros([self.DataFromDat.get('nTx'), self.DataFromDat.get('nSites')])
        Phi2 = np.zeros([self.DataFromDat.get('nTx'), self.DataFromDat.get('nSites')])
        for i in range(self.DataFromDat.get('nTx')):
            for j in range(self.DataFromDat.get('nSites')):
                Z_tensor = self.DataFromDat.get('Z_matrix')[i, j]
                # Phase_Tensor = inv(real(Z_tensor))*imag(Z_tensor)
                Phase_Tensor[i, j] = np.linalg.inv(np.real(Z_tensor)).dot(np.imag(Z_tensor))

                Pxx = Phase_Tensor[i, j, 0, 0]
                Pxy = Phase_Tensor[i, j, 0, 1]
                Pyx = Phase_Tensor[i, j, 1, 0]
                Pyy = Phase_Tensor[i, j, 1, 1]
                phi = np.array([[Pxx, Pxy], [Pyx, Pyy]])
                rot_angle = 1/4 * np.arctan2(2 * (Pxx - Pyy) * (Pxy + Pyx),(Pxx - Pyy)**2 - (Pxy + Pyx)**2)
                rot_M = np.array([[np.cos(rot_angle), -np.sin(rot_angle)], [np.sin(rot_angle), np.cos(rot_angle)]])
                phi = np.dot(np.dot(rot_M, phi), rot_M.T)

                phi2_ij = np.degrees(np.arctan(np.sqrt(np.abs(phi[0, 0] * phi[1, 1] - phi[0, 1] * phi[1, 0]))))
                skew_ij = np.degrees(1/2 * np.arctan(np.abs((phi[0, 1] - phi[1, 0]) / (phi[0, 0] + phi[1, 1]))))
                skew[i, j] = skew_ij
                Phi2[i, j] = phi2_ij
        self.DataFromDat.update({'skew': skew})
        self.DataFromDat.update({'Phi2': Phi2})
        self.DataFromDat.update({'Phase_Tensor': Phase_Tensor})
    

    def compute_apparent_resistivity(self):
        if self.DataFromDat is None:
            raise ValueError("Data is not available.")
        Apparent_resistivity = np.zeros([self.DataFromDat.get('nTx'), self.DataFromDat.get('nSites'),2,2])
        Phi = np.zeros([self.DataFromDat.get('nTx'), self.DataFromDat.get('nSites'),2,2])
        for i in range(self.DataFromDat.get('nTx')):
            for j in range(self.DataFromDat.get('nSites')):
                period = self.DataFromDat.get('T')[i]
                period = float(period)
                
                Z_tensor = self.DataFromDat.get('Z_matrix')[i, j]
                Rhoxx = 0.2 * period * np.abs(Z_tensor[0, 0])**2
                Rhoxy = 0.2 * period * np.abs(Z_tensor[0, 1])**2
                Rhoyx = 0.2 * period * np.abs(Z_tensor[1, 0])**2
                Rhoyy = 0.2 * period * np.abs(Z_tensor[1, 1])**2
                Phixx = np.angle(Z_tensor[0, 0])
                Phixy = np.angle(Z_tensor[0, 1])
                Phiyx = np.angle(Z_tensor[1, 0])
                Phiyy = np.angle(Z_tensor[1, 1])
                Apparent_resistivity[i, j] = np.array([[Rhoxx, Rhoxy], [Rhoyx, Rhoyy]])
                Phi[i, j] = np.array([[Phixx, Phixy], [Phiyx, Phiyy]])
        self.DataFromDat.update({'Apparent_resistivity': Apparent_resistivity})
        self.DataFromDat.update({'Phi': Phi})
    ##################################################################################################################
    # 检验绘制结果的简易方法
    def plot_para_xdistance_yperiod_colorpara(self, parameter='skew'):
        if self.DataFromDat.get(parameter) is None:
            raise ValueError("Parameter is not available.")
        para= self.DataFromDat.get(parameter)
        fig, ax = plt.subplots()
        cax = ax.matshow(para, cmap='jet')
        fig.colorbar(cax)
        plt.show()

    def plot_resistivity_of_one_site(self, site_index):
        if self.DataFromDat.get('Apparent_resistivity') is None:
            raise ValueError("Apparent_resistivity is not available.")
        Apparent_resistivity = self.DataFromDat.get('Apparent_resistivity')
        T = np.array(self.DataFromDat.get('T')).astype(float)
        min_T = min(T)
        max_T = max(T)
        
        fig = go.Figure()

        # 添加第一个数据点并显示图例标签
        fig.add_trace(go.Scattergl(
            x=[T[0]], y=[Apparent_resistivity[0, site_index, 0, 0]],
            mode='markers', name='Rhoxx', marker=dict(color='green')
        ))
        fig.add_trace(go.Scattergl(
            x=[T[0]], y=[Apparent_resistivity[0, site_index, 0, 1]],
            mode='markers', name='Rhoxy', marker=dict(color='red')
        ))
        fig.add_trace(go.Scattergl(
            x=[T[0]], y=[Apparent_resistivity[0, site_index, 1, 0]],
            mode='markers', name='Rhoyx', marker=dict(color='blue')
        ))
        fig.add_trace(go.Scattergl(
            x=[T[0]], y=[Apparent_resistivity[0, site_index, 1, 1]],
            mode='markers', name='Rhoyy', marker=dict(color='yellow')
        ))

        # 添加后续数据点并隐藏图例标签
        for i in range(1, Apparent_resistivity.shape[0]):
            fig.add_trace(go.Scattergl(
                x=[T[i]], y=[Apparent_resistivity[i, site_index, 0, 0]],
                mode='markers', marker=dict(color='green'), showlegend=False
            ))
            fig.add_trace(go.Scattergl(
                x=[T[i]], y=[Apparent_resistivity[i, site_index, 0, 1]],
                mode='markers', marker=dict(color='red'), showlegend=False
            ))
            fig.add_trace(go.Scattergl(
                x=[T[i]], y=[Apparent_resistivity[i, site_index, 1, 0]],
                mode='markers', marker=dict(color='blue'), showlegend=False
            ))
            fig.add_trace(go.Scattergl(
                x=[T[i]], y=[Apparent_resistivity[i, site_index, 1, 1]],
                mode='markers', marker=dict(color='yellow'), showlegend=False
            ))

        fig.update_layout(
            xaxis=dict(
                type='log',
                range=[np.log10(0.001), np.log10(10000)],
                title='Period (s)',
                tickvals=[0.001, 0.01, 0.1, 1, 10, 100, 1000, 10000],
                ticktext=['0.001', '0.01', '0.1', '1', '10', '100', '1000', '10000']
            ),
            yaxis=dict(
                type='log',
                range=[np.log10(0.1), np.log10(10000)],
                title='Apparent Resistivity (Ohm.m)',
                tickvals=[0.1, 1, 10, 100, 1000, 10000],
                ticktext=['0.1', '1', '10', '100', '1000', '10000']
            ),
            # 台站名称
            title=self.DataFromDat.get('Sitenames')[site_index],
            showlegend=True
        )

        self.fig = fig

if __name__ == '__main__':
    processor = MyDataProcessor()
    processor.read_file('BYKLData.dat', read_start=2, file_type='Z_ALL_3D')
    processor.get_distance()
    processor.compute_phase_Tensor()
    processor.compute_apparent_resistivity()
    processor.plot_resistivity_of_one_site(0)
    processor.plot_para_xdistance_yperiod_colorpara(parameter='skew')
    processor.plot_para_xdistance_yperiod_colorpara(parameter='Phi2')