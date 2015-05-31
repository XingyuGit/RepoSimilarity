import numpy as np
import matplotlib
# matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import matplotlib.colors as colors
import matplotlib.cm as cm

fig = plt.figure()

method_list = ["mmmmmmmmmmmmm1", "mmmmmmmmmmmmm2", "mmmmmmmmmmmmm3", "mmmmmmmmmmmmm4", "mmmmmmmmmmmmm5", "mmmmmmmmmmmmm6"]
f1score_max_list = [0.5, 0.1, 0.3, 0.6, 0.3, 0.4]

bar_width = 0.7
index = np.arange(len(method_list))
xlist = ["m1","m2","m3","m4", "m5", "m6"]

color = cm.rainbow(np.linspace(0,1,len(xlist)))
barlist = plt.bar(index + bar_width, f1score_max_list, width=bar_width, color=color)


plt.xticks(index + 1.5*bar_width, xlist)
plt.xlabel('Methods')
plt.ylabel('Best F1Scores')
plt.title('Comparison of different methods')

fontP = fm.FontProperties()
fontP.set_size('small')
lgd = plt.legend(barlist, [": ".join(t) for t in zip(xlist, method_list)],
           loc='upper center', bbox_to_anchor=(0.5, 1.25),
            ncol=2, fancybox=True, shadow=True, prop = fontP)

plt.show()

fig.savefig('image_output.png', dpi=300, format='png', bbox_extra_artists=(lgd,), bbox_inches='tight')