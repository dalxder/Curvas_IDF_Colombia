# -*- coding: utf-8 -*-
"""
/***************************************************************************
 Curvas IDF Colombia
                                 A QGIS plugin
 Permite conocer los coeficientes para el cálculo de las curvas IDF
                              -------------------
        begin                : 2017-10-01
        git sha              : $Format:%H$
        copyright            : (C) 2017 by Dany Alexander Manrique López
        email                : dalxder@gmail.com

 ***************************************************************************/

/***************************************************************************
    Licencia LGPL v3
 ***************************************************************************/
"""
from PyQt4.QtCore import * #QSettings, QTranslator, qVersion, QCoreApplication
from PyQt4.QtGui import * #QAction, QIcon
from PyQt4.QtSql import *
from PyQt4.QtWebKit import *

from qgis.core import *
from qgis.gui import  *

from punto_idf_dialog import listaCoordenadas,busquedaPuntual
from nuevaCapa import crearLayer,obtenerDistancias,addFeatureLayer,dentrodeColombia

import datetime as dt
import os.path,json
import numpy as np
from scipy.optimize import leastsq

class coeficientesIDF:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Referencia a la interfaz de QGOS
        self.iface = iface
        #Referencia al canvas
        self.canvas = self.iface.mapCanvas()


        # Visulaizador de datos en formato html
        self.editor = QWebView()

        # Herramineta para la captura de datos (coordenadas) del canvas
        self.captureCoor = QgsMapToolEmitPoint(self.canvas)


        # Creacion de un shapefile para el almacenamiento de datso
        self.layer=crearLayer()
        #g boolean for memory layer state
        self.layer.have_layer =False

        # Ubicación de la carpeta que contiene complemplento
        self.plugin_dir = os.path.dirname(__file__)
        self.obtenerDatos()

        # Ventana con la lista de coordenadas
        self.dlg1 =busquedaPuntual()
        self.dlg2 = listaCoordenadas()

        # Declaración de atributos
        self.actions = []
        # Menu
        self.menu = self.tr(u'&Curvas IDF Colombia')
        #
        self.toolbar = self.iface.addToolBar(self.tr(u'&Curvas IDF Colombia'))
        self.toolbar.setObjectName(self.tr(u'&Curvas IDF Colombia'))

    # Traducción
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('coeficientesIDF', message)

    # Agregar acciones
    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.toolbar.addAction(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):

        """Create the menu entries and toolbar icons inside the QGIS GUI."""
        result = QObject.connect(self.captureCoor, SIGNAL("canvasClicked(const QgsPoint &, Qt::MouseButton)"), self.consultaPuntual)
        iconPunto = self.plugin_dir+r'/icon/iconPunto.png'
        iconLC=self.plugin_dir+'/icon/iconLC.png'
        iconPrint = self.plugin_dir+'/icon/print.png'
        iconPDF= self.plugin_dir+'/icon/pdf.png'

        self.add_action(iconPunto,text=self.tr(u'Seleccionar punto en el mapa'),callback=self.run,parent=self.iface.mainWindow())
        self.add_action(iconLC,text=self.tr(u'Ingresar lista de Puntos'),callback=self.consultaLista,parent=self.iface.mainWindow())
        self.add_action(iconPrint,text=self.tr(u'Imprimir resultados'),callback=self.printResultado,parent=self.iface.mainWindow())
        self.add_action(iconPDF,text=self.tr(u'Crear Archivo PDF'),callback=self.crearPDF,parent=self.iface.mainWindow())

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(self.tr(u'&Curvas IDF Colombia'),action)
            self.iface.removeToolBarIcon(action)
        del self.toolbar



    def run(self):
        newCRS = QgsCoordinateReferenceSystem(4326)

        try:
            self.canvas.mapSettings().setDestinationCrs(newCRS)
            self.canvas.mapSettings().setProjectionsEnabled(True)
            self.canvas.mapSettings().setCrsTransformEnabled(True)
        except:
            self.canvas.mapRenderer().setDestinationCrs(newCRS,refreshCoordinateTransformInfo=True,transformExtent=True)
            self.canvas.mapRenderer().setProjectionsEnabled(True)
            self.canvas.mapSettings().setCrsTransformEnabled(True)
            #crsSrc = qgis.utils.iface.mapCanvas().mapRenderer().destinationCrs() # WGS 84

        # Comprobar la existencia de la capa
        if self.layer.have_layer == False:
            self.layer.crearCapa()
            #QMessageBox.information(self.iface.mainWindow(),"Memory Provider", "No provider yet")

        self.canvas.setMapTool(self.captureCoor)


    def crearHTML(self):

        layer=self.layer.pinLayer
        fields = layer.pendingFields()


        tempCoef="""
        <table>
    		<thead>
    		    <tr>
    		      <th>Tr (años)</th>
    		      <th>C1</th>
    		      <th>X0</th>
    		      <th>C2</th>
    		    </tr>
    		</thead>
    		<tbody>
			%s
		 </tbody>
	   </table>""".decode("utf-8")
        tempTecnicos="""
        	<h2>Datos técnicos</h2>
        	<p>Número máximo de estaciones: %s</p>
            <p>Distancia máxima: %s km</p>
            <p>Potencia de la ponderación: %s</p>
        	<table>
        		<thead>
        		    <tr>
        		      <th>Nombre</th>
        		      <th>Distancia (m)</th>
        		    </tr>
        		</thead>
        		<tbody>
    			     %s
	            </tbody>
             </table>

        """.decode("utf-8")

        datos=""
        tret=[2,3,5,10,25,50,100]
        for i,feature in enumerate(layer.getFeatures()):
            tablaCoef=""
            datos+='<img src="%s/curva%i.png" alt="Smiley face" width="800">'%(self.plugin_dir+r'/static',i)
            for j, att in enumerate(feature.attributes()[2:]):
                tablaCoef+='<tr>'+('<td>%s</td>'*4)%tuple([str(tret[j])]+att.split(","))+'</tr>'
            datosCalculo,cantEsta,distMax,potencia=self.layer.datosCalculo[i]
            dataDist=''
            for d in datosCalculo:
                dataDist+='<tr>'+('<td>%s</td><td>%.f</td>')%tuple(d)+'</tr>'
            if distMax!=None:
                distMax=distMax/1000

            datos+=tempCoef%tablaCoef
            datos+=tempTecnicos%(str(cantEsta),str(distMax),str(potencia),dataDist)




        style="""table {border-collapse: collapse;}
                    table, td, th {border: 2px solid black;}
                  div {display: block;page-break-after:auto;}
                  body {margin-left: 80;margin-top: 100;margin-right: 80;margin-bottom: 100;}
                td {font-family: Arial, Helvetica, sans-serif;font-size: 11px; text-align: center;}
                th {font-family: Arial, Helvetica, sans-serif;font-size: 12px;}"""
        tempHtml="""<!DOCTYPE html>
            <html>
            <head>
            	<title>Curvas intensidad, duración y frecuencia Colombia</title>
            	<meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
                <style>%s</style>
            </head>
            <body>
                <h1>Reporte curvas IDF</h1>
                %s
            </body>
            </html>""".decode('utf-8')%(style,datos)




            #<div class="footer">paginas: <span class="pagenum"></span></div>stile,str(dt.datetime.now().date()),tabla,type(attrs)

        #baseUrl = QUrl.fromLocalFile(os.path.join(self.plugin_dir+"/static", "css"))
        with open(self.plugin_dir+"/static/reporte.html","w")as fileHtml:
            fileHtml.write(tempHtml.encode("utf-8"))
        self.editor.setHtml(tempHtml)
        """

        """
    def printResultado(self):
        if self.layer.have_layer!= False and int(self.layer.provider.featureCount())>0:
            self.crearHTML()
            dialog = QPrintPreviewDialog()
            dialog.paintRequested.connect(self.editor.print_)#
            dialog.paintRequested.connect(self.editor.print_)
            dialog.exec_()
        else:
            QMessageBox.information(None,"Atención".decode("utf-8"), "No ha seleccionado ningún punto".decode("utf-8"))#self.iface.mainWindow()
    def obtenerDatos(self):

        self.polColombia = QgsVectorLayer(self.plugin_dir+r"/data/Colombia/Colombia_wgs84.shp", "Colombia", "ogr")
        with open(self.plugin_dir+r'/data/estaciones.geojson') as data_file:
            self.geojson = json.load(data_file)

    def crearPDF(self):
        if self.layer.have_layer!= False and int(self.layer.provider.featureCount())>0:
            ePath = QFileDialog.getSaveFileName (None,"Guardar PDF",r"D:/","PDF (*.pdf)")
            if ePath:
                self.crearHTML()
                printer = QPrinter()
                #setting format
                printer.setPageSize(QPrinter.Letter)
                printer.setOrientation(QPrinter.Portrait)
                printer.setOutputFormat(QPrinter.PdfFormat)

                printer.setOutputFileName(r"%s"%ePath)
                self.editor.print_(printer)
        else:
            QMessageBox.information(None,"Atención".decode("utf-8"), "No ha seleccionado ningún punto")

    def calCoeficientes(self,punto,cantEsta,distMax,potencia):
        datosCalculo=[]
            # Consultar distancias
        distancias=obtenerDistancias(self.geojson,punto)
        # Indices del orden de
        idOrden=np.argsort(distancias)
        if cantEsta==None:
            cantEsta=len(distancias)

        if distMax!=None:
            idOrden=idOrden[distancias[idOrden]<distMax][:cantEsta]
        else:
            idOrden=idOrden[:cantEsta]
        factores=(distancias[idOrden]**potencia)/sum((distancias[idOrden]**potencia))
        #suma distancia

        # Para cada periodo de retorno
        tr=[2,3,5,10,25,50,100]
        D=np.array([15,30,60,120,360])
        #funciones requeridas en la regresión
        def peval(coeficientes,D):
            C1,X0,C2=coeficientes
            return np.array(C1/((D+X0)**C2))
        def residuals(coeficientes, y, D):
            err=y-peval(coeficientes,D)
            return err
        p0 =[1000,1,1]
        valores=[]
        for i in tr:
            intesidad=np.zeros(len(D))
            # Coeficientes de un periodo de retorno y estaciones seleccionada
            for j,numEst in enumerate(idOrden):
                intesidad+=peval(self.geojson["features"][numEst]['properties'] [u'coeficientes']["tr%i"%i],D)*factores[j]
                #print(self.geojson["features"][numEst]["properties"]["name"])

            plsq = leastsq(residuals, p0, args=(intesidad,D))
            #print(sum(residuals(plsq[0], intesidad, D)))
            valores.append("%.3f,%.3f,%.3f"%tuple(plsq[0]))
        for numEst in idOrden:
            nombre=self.geojson["features"][numEst]["properties"]["name"]
            datosCalculo.append([nombre,distancias[numEst]])
        return valores,datosCalculo



    def consultaPuntual(self, punto,boton):
        # por definir
        # Comprobar la existencia de la capa
        if self.layer.have_layer == False:
                self.layer.crearCapa()
        if dentrodeColombia(punto,self.polColombia):
            cantEsta=None
            distMax=None

            px=float(punto.x())
            py=float(punto.y())
            ok = True
            desc="%f,%f".decode('utf-8')%(px,py)
            self.dlg1.hide()
            self.dlg1.labDesc.setText("Longitud: %f, Latitud: %f"%(px,py))
            result = self.dlg1.exec_()

            if result:
                if self.dlg1.ent_Estaciones.isEnabled():
                    try:
                        cantEsta=int(self.dlg1.ent_Estaciones.text())
                    except:
                        ok = False
                        QMessageBox.information(self.iface.mainWindow(),"Alerta", "La cantidad de estaciones no es valida".decode("utf-8"))

                if self.dlg1.ent_Distancia.isEnabled():
                    try:
                        distMax=float(str(self.dlg1.ent_Distancia.text()).replace(",","."))*1000

                    except:
                        ok = False
                        QMessageBox.information(self.iface.mainWindow(),"Alerta", "La distancia especificada no es valida".decode("utf-8"))

                try:
                    potencia=float(str(self.dlg1.ent_Pot.text()).replace(",","."))

                except:
                    ok = False
                    QMessageBox.information(self.iface.mainWindow(),"Alerta", "Valor de potencia no es valido".decode("utf-8"))

                if ok:
                    valores,datosCalculo=self.calCoeficientes(punto,cantEsta,distMax,potencia)
                    if len(valores)>0:
                        self.layer.datosCalculo.append([datosCalculo,cantEsta,distMax,potencia])
                        addFeatureLayer(self.layer.provider,self.layer.pinLayer,punto,desc,valores)

        else:
            QMessageBox.information(self.iface.mainWindow(),"Fuera del territorio Colombiano", """Lo sentimos esta aplicacion solamente es valida
            dentro del territorio colombiano""")
            print("fuera de col")
            #self.canvas.refresh()

    def consultaLista(self):
        cantEsta=None
        distMax=None

        ok = True
        self.dlg2.hide() # bloque la ventana principal
        # self.dlg2.show() no bloque la ventana principal

        result = self.dlg2.exec_()

        if result:
            if self.dlg2.defSCR:
                if self.layer.have_layer == False:
                    self.layer.crearCapa()

                self.dlg2.transfCoordenadas()
                if self.dlg2.ent_Estaciones.isEnabled():
                    try:
                        cantEsta=int(self.dlg2.ent_Estaciones.text())

                    except:
                        ok = False
                        QMessageBox.information(self.iface.mainWindow(),"Alerta", "La cantidad de estaciones no es valido".decode("utf-8"))
                        self.consultaLista()
                if self.dlg2.ent_Distancia.isEnabled():
                    try:
                        distMax=float(str(self.dlg2.ent_Distancia.text()).replace(",","."))*1000

                    except:
                        ok = False
                        QMessageBox.information(self.iface.mainWindow(),"Alerta", "La cantidad de estaciones no es valido".decode("utf-8"))
                        self.consultaLista()

                try:
                    potencia=float(str(self.dlg2.ent_Pot.text()).replace(",","."))

                except:
                    ok = False
                    QMessageBox.information(self.iface.mainWindow(),"Alerta", "Valor de potencia no es valido".decode("utf-8"))
                    self.consultaLista()


                if len(self.dlg2.puntos)>0:
                    noHallados=""
                    for i,punto in enumerate(self.dlg2.puntos):
                            px=float(punto.x())
                            py=float(punto.y())
                            desc="%f,%f".decode('utf-8')%(px,py)

                            if dentrodeColombia(punto,self.polColombia):
                                if ok:
                                    valores,datosCalculo=self.calCoeficientes(punto,cantEsta,distMax,potencia)
                                    if len(valores)>0:
                                        self.layer.datosCalculo.append([datosCalculo,cantEsta,distMax,potencia])
                                        addFeatureLayer(self.layer.provider,self.layer.pinLayer,punto,desc,valores)
                            else:
                                noHallados+="%f,%f\n"%(px,py)
                    if noHallados!="":
                        QMessageBox.information(self.iface.mainWindow(),"Puntos por fuera de Colombia:",noHallados)

                else:
                    QMessageBox.information(self.iface.mainWindow(),"Puntos".decode("utf-8"), "No hay puntos que transformar".decode("utf-8"))

            else:
                QMessageBox.information(self.iface.mainWindow(),"Definición SRC".decode("utf-8"), "Debe seleccionar un sistema de referencia de coordenadas valido".decode("utf-8"))
                self.consultaLista()


        else:
            QMessageBox.information(self.iface.mainWindow(),"Lista de puntos", "Se ha cancelado la operación".decode("utf-8"))

