[Geohash wiki](https://en.wikipedia.org/wiki/Geohash)

[How do I get indices of N maximum values in a NumPy array?](https://stackoverflow.com/questions/6910641/how-do-i-get-indices-of-n-maximum-values-in-a-numpy-array)

```python
# 不易讀版本
import numpy as np
arr = np.array([1, 3, 2, 4, 5])
arr.argsort()[-3:][::-1]
array([4, 3, 1])

# 正常邏輯
a = np.array([9, 4, 4, 3, 3, 9, 0, 4, 6, 0])
ind = np.argpartition(a, -4)[-4:]  # use introselect algorithm.
a[ind]

# sorted np.argsort
ind[np.argsort(a[ind])] #argsort args have kind : {‘quicksort’, ‘mergesort’, ‘heapsort’, ‘stable’}
```

[Python: speeding up geographic comparison](https://stackoverflow.com/questions/6656475/python-speeding-up-geographic-comparison)  
This is the kind of calculation that numpy is really good at. Rather than looping over the entire large set of coordinates, you can compute the distance between a single point and the entire dataset in a single calculation. With my tests below, you can get an order of magnitude speed increase.

```python
from math import radians, sin, cos, asin, sqrt, pi, atan2
import numpy as np
import itertools

earth_radius_miles = 3956.0

def haversine(point1, point2):
    """Gives the distance between two points on earth.
    """
    lat1, lon1 = (radians(coord) for coord in point1)
    lat2, lon2 = (radians(coord) for coord in point2)
    dlat, dlon = (lat2 - lat1, lon2 - lon1)
    a = sin(dlat/2.0)**2 + cos(lat1) * cos(lat2) * sin(dlon/2.0)**2
    great_circle_distance = 2 * asin(min(1,sqrt(a)))
    d = earth_radius_miles * great_circle_distance
    return d

def get_shortest_in(needle, haystack):
    """needle is a single (lat,long) tuple.
        haystack is a numpy array to find the point in
        that has the shortest distance to needle
    """
    dlat = np.radians(haystack[:,0]) - radians(needle[0])
    dlon = np.radians(haystack[:,1]) - radians(needle[1])
    a = np.square(np.sin(dlat/2.0)) + cos(radians(needle[0])) * np.cos(np.radians(haystack[:,0])) * np.square(np.sin(dlon/2.0))
    great_circle_distance = 2 * np.arcsin(np.minimum(np.sqrt(a), np.repeat(1, len(a))))
    d = earth_radius_miles * great_circle_distance
    return np.min(d)


x = (37.160316546736745, -78.75)
y = (39.095962936305476, -121.2890625)

def dohaversine():
    for i in xrange(100000):
        haversine(x,y)

ots = np.array(list(itertools.repeat(y, 100000)))
def donumpy():
    get_shortest_in(x, lots)

from timeit import Timer
print 'haversine distance =', haversine(x,y), 'time =',
print Timer("dohaversine()", "from __main__ import dohaversine").timeit(100)
print 'numpy distance =', get_shortest_in(x, lots), 'time =',
print Timer("donumpy()", "from __main__ import donumpy").timeit(100)
```
And here's what it prints:
```
haversine distance = 2293.13242188 time = 44.2363960743
dumb distance = 40.6034161104 time = 5.58199882507
numpy distance = 2293.13242188 time = 1.54996609688
```
[测量小代码片段的执行时间](https://docs.python.org/zh-cn/3/library/timeit.html)  
[haversine wiki](https://zh.wikipedia.org/wiki/%E5%8D%8A%E6%AD%A3%E7%9F%A2%E5%85%AC%E5%BC%8F)  
[Locality-Sensitive Hashing](https://blog.csdn.net/icvpr/article/details/12342159)  
[R樹 wiki 多維資料建立索引](https://zh.wikipedia.org/wiki/R%E6%A0%91)  
[geohash, polygon](https://ithelp.ithome.com.tw/articles/10203720)  
[web lat lon convert geohash,google map](https://www.movable-type.co.uk/scripts/geohash.html)

