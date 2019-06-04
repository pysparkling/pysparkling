from pyspark.sql import Row

from pysparkling.sql.dataframe import DataFrame
from pysparkling.sql.functions import count, mean, parse, avg, max, min, sum


class GroupedData(object):
    def __init__(self, jgd, df):
        self._jgd = jgd
        self._df = df
        self.sql_ctx = df.sql_ctx

    def agg(self, *exprs):
        """
        >>> from pysparkling import Context
        >>> from pysparkling.sql.session import SparkSession
        >>> spark = SparkSession(Context())
        >>> df = spark.createDataFrame(
        ...   [Row(age=2, name='Alice'), Row(age=5, name='Bob')]
        ... )
        >>> gdf = df.groupBy(df.name)
        >>> sorted(gdf.agg({"*": "count"}).collect())
        [Row(name=u'Alice', count(1)=1), Row(name=u'Bob', count(1)=1)]

        >>> from pyspark.sql import functions as F
        >>> sorted(gdf.agg(min(df.age)).collect())
        [Row(name=u'Alice', min(age)=2), Row(name=u'Bob', min(age)=5)]

        >>> from pyspark.sql.functions import pandas_udf, PandasUDFType
        >>> @pandas_udf('int', PandasUDFType.GROUPED_AGG)  # doctest: +SKIP
        ... def min_udf(v):
        ...     return v.min()
        >>> sorted(gdf.agg(min_udf(df.age)).collect())  # doctest: +SKIP
        [Row(name=u'Alice', min_udf(age)=2), Row(name=u'Bob', min_udf(age)=5)]
        """
        if not exprs:
            raise ValueError("exprs should not be empty")

        if len(exprs) == 1 and isinstance(exprs[0], dict):
            jdf = self._jgd.agg(exprs[0])
        else:
            # Columns
            if not all(isinstance(c, Column) for c in exprs):
                raise ValueError("all exprs should be Column")

            # noinspection PyProtectedMember
            jdf = self._jgd.agg(
                exprs[0]._jc,
                self.sql_ctx._sc,
                [c._jc for c in exprs[1:]]
            )

        return DataFrame(jdf, self.sql_ctx)

    def count(self):
        return self.agg(count(1))

    def mean(self, *cols):
        return self.agg(*(mean(parse(col)) for col in cols))

    def avg(self, *cols):
        return self.agg(*(avg(parse(col)) for col in cols))

    def max(self, *cols):
        return self.agg(*(max(parse(col)) for col in cols))

    def min(self, *cols):
        return self.agg(*(min(parse(col)) for col in cols))

    def sum(self, *cols):
        return self.agg(*(sum(parse(col)) for col in cols))

    # todo: implement apply()
    # def pivot(self, pivot_col, values=None):
    #     if values is None:
    #         jgd = self._jgd.pivot(pivot_col)
    #     else:
    #         jgd = self._jgd.pivot(pivot_col, values)
    #     return GroupedData(jgd, self._df)

    # todo: implement apply()
    # def apply(self, udf):
    #     # Columns are special because hasattr always return True
    #     if isinstance(udf, Column) or not hasattr(udf, 'func') \
    #             or udf.evalType != PythonEvalType.SQL_GROUPED_MAP_PANDAS_UDF:
    #         raise ValueError("Invalid udf: the udf argument must be a pandas_udf of type "
    #                          "GROUPED_MAP.")
    #     df = self._df
    #     udf_column = udf(*[df[col] for col in df.columns])
    #     jdf = self._jgd.flatMapGroupsInPandas(udf_column._jc.expr())
    #     return DataFrame(jdf, self.sql_ctx)
