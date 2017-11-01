# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      dalxder
#
# Created:     29/10/2017
# Copyright:   (c) dalxder 2017
# Licence:     <your licence>
#-------------------------------------------------------------------------------

import matplotlib.pyplot as plt
import numpy as np
#plt.clf()
fig = plt.figure()
ax = plt.subplot(111)
ax.grid(True)
#ax.grid(b=True, which='major')
#ax.grid(b=True, which='minor')
ax.minorticks_on()

box = ax.get_position()
ax.set_position([box.x0, box.y0, box.width * 0.9, box.height])

x = np.linspace(0, 400)

# Plot the lines y=x**n for n=1..4.

for n in range(1, 5):
    ax.plot(x, x**n, label="{0}".format(n)+" años".decode("utf-8"))
ax.legend(loc="center left", bbox_to_anchor=[1, 0.5],
           title="TR", fontsize=10)
ax.text(0.8, 0.9,r'$I=\frac{C1}{(D+X0)^{C2}}$', ha='center', va='center', transform=ax.transAxes, fontsize=18)
savefig('F:\\semivariogram_model2.png',fmt='png',dpi=200)