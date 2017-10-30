# -*- coding: utf-8 -*-
from qgis.core import QgsVectorLayer,QgsMapLayerRegistry,QgsPoint
from PyQt4.QtCore import QObject,SIGNAL
from qgis.gui import *
from qgis.core import *
import numpy as np

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


def dentrodeColombia(punto,polColombia):
    # Esta función comprueba que el punto se encuentra dentro de Colombia
    enCol=False
    for feature in polColombia.getFeatures():
        if QgsGeometry.fromPoint(punto).within(feature.geometry()):
            enCol=True

    return enCol
