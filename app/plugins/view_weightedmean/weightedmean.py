from app.widgets.ViewWidget import ARViewWidget
from app.widgets.ControlWidget import PlotControlWidget
from app.widgets.ColumnComboBox import ColumnComboBox
from app.widgets.QCPItemRichText import QCPItemRichText
from QCustomPlot_PySide import *

from PySide2.QtWidgets import QComboBox
from PySide2.QtGui import QPen
from PySide2.QtCore import Qt

from app.data import datasets
from app.preferences import applyStyleToPlot
from app.math import formatResult, weightedMean, formatResult
from app.datatypes import Columns

import pickle

class WeightedMean(ARViewWidget):

    def __init__(self, parent=None):
        super().__init__(QCustomPlot(), parent)
        self.plot = self.widget()        
        self.plot.axisRect().setupFullAxesBox(True)
        applyStyleToPlot(self.plot)

        self.column = None
        self.dsname = None

    def setColumn(self, columnName):
        self.column = columnName
        self.updatePlot()

    def addDataset(self, datasetName):
        if not self.column:
            self.column = datasets[datasetName].columns[0]

        self.dsname = datasetName
        self.updatePlot()

    def updatePlot(self):
        if not self.dsname or not self.column:
            return

        y = datasets[self.dsname][self.column].values

        try:
            yerr = datasets[self.dsname][Columns.value_error_pairs[self.column]].values
        except:
            print('Could not find error data for %s. Assuming 5 percent.'%(self.column))
            yerr = 0.05*y

        res = weightedMean(y, yerr)
        print(res)
        x = range(len(y))

        self.plot.clearGraphs()
        self.plot.clearPlottables()
        self.plot.clearItems()

        self.graph = self.plot.addGraph()
        self.graph.setData(x, y)
        self.graph.setLineStyle(QCPGraph.lsNone)
        self.graph.setScatterStyle(QCPScatterStyle(QCPScatterStyle.ssDisc))

        self.eb = QCPErrorBars(self.plot.xAxis, self.plot.yAxis)
        self.eb.setDataPlottable(self.graph)
        self.eb.setData(yerr)
        self.eb.removeFromLegend()
        self.plot.incref(self.eb)

        self.line = QCPItemStraightLine(self.plot)
        self.line.position('point1').setType(QCPItemPosition.ptPlotCoords)
        self.line.position('point2').setType(QCPItemPosition.ptPlotCoords)
        self.line.position('point1').setCoords(x[0], res['internal'][0])
        self.line.position('point2').setCoords(x[-1], res['internal'][0])
        self.plot.incref(self.line)

        self.caption = QCPItemRichText(self.plot)
        self.caption.setText(f'<p style="background-color:white;color:black;">{formatResult(res["internal"][0], res["internal"][1])[0]}</p>')
        self.plot.incref(self.caption)
        self.caption.position('position').setType(QCPItemPosition.ptAxisRectRatio)
        self.caption.position('position').setCoords(0.98, 0.02)
        self.caption.setPen(QPen(Qt.black))
        self.caption.setPositionAlignment(Qt.AlignTop | Qt.AlignRight)      

        if isinstance(self.column, str):
            self.plot.yAxis.setLabel(self.column)

        self.plot.rescaleAxes()
        self.plot.xAxis.scaleRange(1.1)
        self.plot.yAxis.scaleRange(1.1)
        self.plot.xAxis.setTickLabels(False)
        self.plot.replot()

    def createControlWidget(self):
        return WMControlWidget(self)

    def saveState(self):
        s = {
            'column': self.column,
            'datasetName': self.dsname,
            'plotSettings': self.plot.saveState()
        }
        return pickle.dumps(s)

    def restoreState(self, state):
        s = pickle.loads(state)
        print(s)
        self.setColumn(s['column'])
        self.addDataset(s['datasetName'])
        self.plot.restoreState(s['plotSettings'])

class WMControlWidget(PlotControlWidget):

    def __init__(self, widget, parent=None):
        super().__init__(widget, parent)

        self.columnComboBox = ColumnComboBox(self)
        self.columnComboBox.columnChanged.connect(widget.setColumn)        
        self.layout().insertRow(1, 'Column', self.columnComboBox)
