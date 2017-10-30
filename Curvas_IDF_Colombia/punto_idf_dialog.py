# -*- coding: utf-8 -*-
"""
/***************************************************************************
 coeficientesIDFDialog
                                 A QGIS plugin
 Permite conocer los coeficientes para el cálculo de las curvas IDF
                             -------------------
        begin                : 2015-02-10
        git sha              : $Format:%H$
        copyright            : (C) 2015 by Dany Alexander Manrique López / Maestría en ingeniería - Recursos Hidráulicos / UNAL-EAB
        email                : damanriquel@unal.edu.co
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

import os

from PyQt4 import QtGui, uic, QtCore
from PyQt4.QtWebKit import *
from qgis.gui import *
from qgis.core import *

FORM_Puntual, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), 'busquedaPuntual.ui'))
FORM_Lista, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), 'listaCoordenadas.ui'))


class busquedaPuntual(QtGui.QDialog, FORM_Puntual):
    def __init__(self, parent=None):
        """Constructor."""
        super(busquedaPuntual, self).__init__(parent)
        self.setupUi(self)
        self.checkEst.stateChanged.connect(self.estaciones)
        self.checkDist.stateChanged.connect(self.distancias)
    def distancias(self):
        self.ent_Distancia.setEnabled(self.checkDist.isChecked())
    def estaciones(self):
        self.ent_Estaciones.setEnabled(self.checkEst.isChecked())

class listaCoordenadas(QtGui.QDialog, FORM_Lista):
    def __init__(self, parent=None):
        """Constructor."""
        super(listaCoordenadas, self).__init__(parent)
        self.setupUi(self)
        self.buttonSRC.clicked.connect(self.defineSRC)
        self.checkEst.stateChanged.connect(self.estaciones)
        self.checkDist.stateChanged.connect(self.distancias)
        self.defSCR=False
    def defineSRC(self):
        projSelector = QgsGenericProjectionSelector()
        if projSelector.exec_() and projSelector:
            self.selectSRC=projSelector.selectedAuthId().split(":")
            if self.selectSRC[0]=="USER":
                self.typeSRC=QgsCoordinateReferenceSystem.InternalCrsId
                self.defSCR=True
            elif self.selectSRC[0]=="EPSG":
                self.typeSRC=QgsCoordinateReferenceSystem.EpsgCrsId
                self.defSCR=True
        if self.defSCR==True:

            crsOrigen = QgsCoordinateReferenceSystem(int(self.selectSRC[1]),self.typeSRC)
            crsDest = QgsCoordinateReferenceSystem(4326)
            self.xform = QgsCoordinateTransform(crsOrigen, crsDest)
            self.lineEdit.setText(crsOrigen.authid()+" "+crsOrigen.description())
        else:
            self.lineEdit.setText("El sistema de referencia de coordenadas no es valido")


    def transfCoordenadas(self):
        self.puntos=[]
        errores=""
        coordenadas=self.textCoordenadas.toPlainText().replace(";","\n").split("\n")
        if len(coordenadas)>0:
            for i,point in enumerate(coordenadas):
                pi=point.split(",")[0:2]
                try:
                    pt1 = self.xform.transform(QgsPoint(float(pi[0]),float(pi[1])))
                    self.puntos.append(pt1)
                except:
                    errores+=point+"\n"
        if errores!="":
            QtGui.QMessageBox.information(self,"Errores de formato:",errores)

    def distancias(self):
        self.ent_Distancia.setEnabled(self.checkDist.isChecked())
    def estaciones(self):
        self.ent_Estaciones.setEnabled(self.checkEst.isChecked())
