class shp:
    def create_pin_layer(self):

        defLayer="""Point?crs=EPSG:3116&
        &field=id:integer&
        &field=Punto:string(120)&
        &field=C1_TR_3:double&
        &field=X0_TR_3:double&
        &field=C2_TR_3:double&
        &field=C1_TR_5:double&
        &field=X0_TR_5:double&
        &field=C2_TR_5:double&
        &field=C1_TR_10:double&
        &field=X0_TR_10:double&
        &field=C2_TR_10:double&
        &field=C1_TR_25:double&
        &field=X0_TR_25:double&
        &field=C2_TR_25:double&
        &field=C1_TR_50:double&
        &field=X0_TR_50:double&
        &field=C2_TR_50:double&
        &field=C1_TR_100:double&
        &field=X0_TR_100:double&
        &field=C2_TR_100:double&
        &index=yes"""

        self.pinLayer =  QgsVectorLayer(defLayer,"Puntos IDF","memory")
        self.provider = self.pinLayer.dataProvider()
        self.pinLayer.setDisplayField("description")
        QgsMapLayerRegistry.instance().addMapLayer(self.pinLayer)#.setCrs(QgsCoordinateReferenceSystem(3116))
        result = QObject.connect(self.pinLayer, SIGNAL("layerDeleted()"), self.layer_deleted)
        self.have_layer = True

    def layer_deleted(self):
      self.have_layer = False