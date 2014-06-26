"""
Provide a way to work with panda data frames in Spark
"""
#
# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

from pandaspark.utils import add_pyspark_path, run_tests
add_pyspark_path()
from pyspark.join import python_join, python_left_outer_join, \
    python_right_outer_join, python_cogroup
from pyspark.rdd import RDD
from pandaspark.col_stat_counters import ColumnStatCounters
import pandas

class PRDD:
    """
    A Panda Resilient Distributed Dataset (PRDD), is an extension of the RDD.
    It is an RDD containg Panda dataframes and provides special methods that
    are aware of this. You can access the underlying RDD at _rdd, but be careful
    doing so. Note: RDDs are lazy, so you operations are not performed until required.
    """

    def __init__(self, rdd):
        self._rdd = rdd

    @classmethod
    def fromRDD(cls, rdd):
        """Construct a PRDD from an RDD. No checking or validation occurs"""
        return PRDD(rdd)

    def applymap(self, f, **kwargs):
        """
        Return a new PRDD by applying a function to each element of each
        Panda DataFrame

        >>> input = [("tea", "happy"), ("water", "sad"), ("coffee", "happiest")]
        >>> prdd = psc.DataFrame(input, columns=['magic', 'thing'])
        >>> addpandasfunc = (lambda x: "panda" + x)
        >>> result = prdd.applymap(addpandasfunc).collect()
        >>> str(result.sort(['magic'])).replace(' ','').replace('\\n','')
        'magicthing0pandacoffeepandahappiest0pandateapandahappy0pandawaterpandasad...'
        """
        return self.fromRDD(self._rdd.map(lambda data: data.applymap(f), **kwargs))

    def __getitem__(self, key):
        """
        Returns a new PRDD of elements from that key

        >>> input = [("tea", "happy"), ("water", "sad"), ("coffee", "happiest")]
        >>> prdd = psc.DataFrame(input, columns=['magic', 'thing'])
        >>> str(prdd['thing'].collect()).replace(' ','').replace('\\n','')
        '0happy0sad0happiestName:thing,dtype:object'
        """
        return self.fromRDD(self._rdd.map(lambda x: x[key]))

    def collect(self):
        """
        Collect the elements in an PRDD and concatenate the partition

        >>> input = [("tea", "happy"), ("water", "sad"), ("coffee", "happiest")]
        >>> prdd = psc.DataFrame(input, columns=['magic', 'thing'])
        >>> elements = prdd.collect()
        >>> str(elements.sort(['magic']))
        '    magic     thing\\n0  coffee  happiest\\n0     tea     happy\\n0   water       sad...'
        """
        def appendFrames(frame_a, frame_b):
            return frame_a.append(frame_b)
        return self._rdd.reduce(appendFrames)

    def stats(self, columns = []):
        """
        Compute the stats for each column provided in columns.
        Parameters
        ----------
        columns : list of str, contains all comuns for which to compute stats on
        >>> input = [("magic", 10), ("ninja", 20), ("coffee", 30)]
        >>> prdd = psc.DataFrame(input, columns=['a', 'b'])
        >>> stats = prdd.stats(columns=['b'])
        >>> str(stats)
        '(field: b,  counters: (count: 3, mean: 20.0, stdev: 8.16496580928, max: 30, min: 10))'
        """
        def reduceFunc(sc1, sc2):
            print sc1
            return sc1.merge_stats(sc2)

        return self._rdd.mapPartitions(lambda i: [ColumnStatCounters(dataframes = i, columns = columns)]).reduce(reduceFunc)

if __name__ == "__main__":
    run_tests()
