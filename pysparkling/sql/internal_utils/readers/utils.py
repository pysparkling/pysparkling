from pysparkling.fileio import File, TextFile
from pysparkling.sql.casts import get_caster
from pysparkling.utils import row_from_keyed_values
from pysparkling.sql.utils import AnalysisException
from pysparkling.sql.types import *


def resolve_partitions(patterns):
    """
    Given a list of patterns, returns all the files matching or in folders matching
    one of them.

    The file are returned in a list of tuple of 2 elements:
    - The first tuple is the file path
    - The second being the partition keys and values if any were encountered else None

    In addition to this list, return, if the data was partitioned, a schema for the
    partition keys, else None

    :type patterns: list of str
    :rtype: Tuple[List[str], List[Optional[Row]], Optional[StructType]]
    """
    file_paths = File.get_content(patterns)
    if not file_paths:
        raise AnalysisException('Path does not exist:'.format(patterns))
    partitions = {}
    for file_path in file_paths:
        if "=" in file_path:
            row = row_from_keyed_values(
                folder.split("=")
                for folder in file_path.split("/")[:-1]
                if folder.count("=") == 1
            )
            partitions[file_path] = row
        else:
            partitions[file_path] = None

    if any(value is None for value in partitions.values()):
        raise AnalysisException(
            "Unable to parse those malformed folders: {1}".format(
                file_paths,
                [path for path, value in partitions.items() if value is None]
            )
        )

    partitioning_field_sets = set(p.__fields__ for p in partitions.values())
    if len(partitioning_field_sets) > 1:
        raise Exception(
            "Conflicting directory structures detected while reading {0}. "
            "All partitions must have the same partitioning fields, found fields {1}".format(
                ",".join(patterns),
                " and also ".join(
                    str(fields) for fields in partitioning_field_sets
                )
            )
        )

    if partitioning_field_sets:
        partitioning_fields = partitioning_field_sets.pop()
        partition_schema = guess_schema_from_strings(partitioning_fields, partitions.values())
    else:
        partition_schema = None

    return partitions, partition_schema


def guess_schema_from_strings(schema_fields, data):
    field_values = {
        field: [row[field] for row in data]
        for field in schema_fields
    }

    field_types_and_values = {
        field: guess_type_from_values_as_string(values)
        for field, values in field_values.items()
    }

    schema = StructType(fields=[
        StructField(field, field_type)
        for field, field_type in field_types_and_values.items()
    ])

    return schema


def guess_type_from_values_as_string(values):
    # Reproduces inferences available in Spark
    # PartitioningUtils.inferPartitionColumnValue()
    # located in org.apache.spark.sql.execution.datasources
    tested_types = (
        IntegerType(),
        LongType(),
        DecimalType(),
        DoubleType(),
        TimestampType(),
        DateType(),
        StringType()
    )
    for tested_type in tested_types:
        string_type = StringType()
        type_caster = get_caster(from_type=string_type, to_type=tested_type)
        try:
            for value in values:
                casted_value = type_caster(value)
                if casted_value is None and value != "null":
                    raise ValueError
            return tested_type
        except ValueError:
            pass
    # Should never happen
    raise AnalysisException("Unable to find a matching type for some partition, even StringType did not work")


def get_records(f_name, linesep, encoding):
    f_content = TextFile(f_name).load(encoding=encoding).read()
    records = f_content.split(linesep) if linesep is not None else f_content.splitlines()
    return records