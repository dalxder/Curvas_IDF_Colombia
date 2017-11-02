# -*- coding: utf-8 -*-
from qgis.core import QgsVectorLayer,QgsMapLayerRegistry,QgsPoint
from PyQt4.QtCore import QObject,SIGNAL
from qgis.gui import *
from qgis.core import *
import numpy as np
import matplotlib.pyplot as plt
import os
import shutil
class crearLayer:
    def __init__(self):
        """Constructor."""
        #self.have_layer = False

    def crearCapa(self):
        #[2,3,5,10,25,50,100]
        defLayer="""Point?crs=EPSG:4326&
        &field=id:integer&
        &field=Punto:string(120)&
        &field=tr2:string(120)&
        &field=tr3:string(120)&
        &field=tr5:string(120)&
        &field=tr10:string(120)&
        &field=tr25:string(120)&
        &field=tr50:string(120)&
        &field=tr100:string(120)&
        &index=yes"""

        # Creación de capa de puntos en la memoria
        self.pinLayer =  QgsVectorLayer(defLayer,"Puntos de consulta","memory")

        self.provider = self.pinLayer.dataProvider()
        self.pinLayer.setDisplayField("description")
        QgsMapLayerRegistry.instance().addMapLayer(self.pinLayer)#.setCrs(QgsCoordinateReferenceSystem(3116))

        QObject.connect(self.pinLayer, SIGNAL("layerDeleted()"), self.layer_deleted)
        self.have_layer = True
        self.datosCalculo=[]


        for root, dirs, files in os.walk(os.path.dirname(__file__)+'\\static\\'):
            for f in files:
                os.unlink(os.path.join(os.path.dirname(__file__)+'\\static\\', f))
    def layer_deleted(self):
      self.have_layer = False
      self.datosCalculo=None

def obtenerDistancias(geojson,punto):
    valores=[]
    d=objectDistance()
    distancias=[]

    # itera para cada estación
    for i, feat in enumerate(geojson["features"]):
        #nomEstacion=feat["properties"]["name"]
        px,py=feat["geometry"]["coordinates"]
        # Calcular las distancias del punto de interes a cada estación del IDEAM
        dist=d.measureLine(punto,QgsPoint(px,py))
        distancias.append(dist)
    return np.array(distancias)

def update():
    # descarga de geojson
    download_url="https://raw.githubusercontent.com/dalxder/pruebasIDF/master/estaciones.geojson"
    response = urllib2.urlopen(download_url)
    with open("estaciones2.geojson", 'wb') as createGeojson:
        createGeojson.write(response.read())

def objectDistance():
    distance = QgsDistanceArea()
    crs = QgsCoordinateReferenceSystem()
    crs.createFromSrsId(4326) # EPSG:4326
    distance.setSourceCrs(crs)
    distance.setEllipsoidalMode(True)
    distance.setEllipsoid('WGS84')
    return distance
def graficas(ident,valores):

    def peval(coeficientes,D):
        C1,X0,C2=coeficientes
        return np.array(C1/((D+X0)**C2))
    def residuals(coeficientes, y, D):
        err=y-peval(coeficientes,D)
        return err

    fig = plt.figure()
    ax = plt.subplot(111)
    ax.grid(True)
    ax.minorticks_on()

    box = ax.get_position()
    ax.set_position([box.x0, box.y0, box.width * 0.85, box.height])

    x = np.linspace(15, 360)

    # Plot the lines y=x**n for n=1..4.
    tr=[2,3,5,10,25,50,100]
    for i, val in enumerate(valores):
        C1,X0,C2=val.split(",")
        ax.plot(x, peval([float(C1),float(X0),float(C2)],x), label="{0}".format(tr[i])+" años".decode("utf-8"))
    ax.legend(loc="center left", bbox_to_anchor=[1, 0.5],
               title="TR", fontsize=10)
    ax.text(0.8, 0.9,r'$I=\frac{C1}{(D+X0)^{C2}}$', ha='center', va='center', transform=ax.transAxes, fontsize=18)
    fig.savefig(os.path.dirname(__file__)+'\\static\\%s.png'%("curva"+str(ident-1)),fmt='png',dpi=200)
    fig=None
def addFeatureLayer(provider,layer,point,desc,valores):
    """
    Esta función agrega items a la capa de almacenamiento.
    """
    # Crear item
    feature = QgsFeature()
    feature.setGeometry(QgsGeometry.fromPoint(point))
    if QGis.QGIS_VERSION_INT > 10800:
        feature.setAttributes([int(provider.featureCount())+1, desc]+valores)
        layer.startEditing()
        layer.addFeature(feature, True)
        layer.commitChanges()

    layer.setCacheImage(None)
    layer.triggerRepaint()

    graficas(int(provider.featureCount()),valores)


def dentrodeColombia(punto,polColombia):
    # Esta función comprueba que el punto se encuentra dentro de Colombia
    enCol=False
    for feature in polColombia.getFeatures():
        if QgsGeometry.fromPoint(punto).within(feature.geometry()):
            enCol=True

    return enCol
        #funciones requeridas en la regresión
