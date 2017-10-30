# -*- coding: utf-8 -*-
"""
/***************************************************************************
 coeficientesIDF
                                 A QGIS plugin
 Permite conocer los coeficientes para el cálculo de las curvas IDF
                             -------------------
        begin                : 2015-02-10
        copyright            : (C) 2015 by Dany Alexander Manrique López
        email                : dalxder
        git sha              : $Format:%H$
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 This script initializes the plugin, making it known to QGIS.
"""



def classFactory(iface):
    """Load coeficientesIDF class from file coeficientesIDF.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .punto_idf import coeficientesIDF
    return coeficientesIDF(iface)
